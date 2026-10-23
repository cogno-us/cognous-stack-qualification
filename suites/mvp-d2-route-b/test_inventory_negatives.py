"""Static-inventory companion checks at the MVP tuple (Worker D2). Builder observations, not a Qualification verdict.

Tests named test_REFUSED_* assert a refusal that holds at the tuple. Tests named test_REACHABLE_* assert that an effect (or a
bypass of identity/authority) IS reachable through the named surface at the tuple: they are characterisations of an
unmediated surface that the trusted-host ingress (Worker D1) must keep out of reach of ordinary clients. They pass when the
surface is reachable; they do not endorse it.

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import importlib.util
import os
import sqlite3
from pathlib import Path

import pytest

from _oi_flow import Flow
from test_route_b_end_to_end import OPERATION, _attempt_rows, _build, _effects, _op_rows, _run


def _runtime_helper():
    path = Path(os.environ["D2_RUNTIME_DIR"]) / "tests" / "test_atomic_route_valid_flow_identity.py"
    spec = importlib.util.spec_from_file_location("rt_flow_helper", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _tables(dest):
    c = sqlite3.connect(dest.path)
    try:
        return {r[0]: c.execute(f"SELECT COUNT(*) FROM {r[0]}").fetchone()[0]
                for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        c.close()


# --- legacy (route A) writers aimed at a route-B database ----------------------------------------------------------------

def test_REFUSED_legacy_commit_on_route_b_database(tmp_path):
    from engine.safe_executor import DurableRefundDestination, snapshot_envelope
    mp, flow, dest, ex, claim = _build(tmp_path)
    try:
        legacy = DurableRefundDestination(tmp_path / "atomic")  # same root and file as the route-B destination
        assert legacy.path == dest.path
        with pytest.raises(PermissionError, match="requires atomic claim execution"):
            legacy.commit(snapshot_envelope(flow.envelope(flow.d1)))
        assert _effects(dest) == []
        # opposite direction: the legacy marker check does not stop a route-B commit afterwards
        assert _run(flow, ex, claim).status == "executed"
    finally:
        mp.undo()


def test_REFUSED_execute_snapshot_on_route_b_database_and_leftover_attempt_rows(tmp_path):
    """LocalDestinationExecutor.execute_snapshot on the route-B database: refused, zero effects; records what it leaves."""
    from engine.safe_executor import DurableRefundDestination, LocalDestinationExecutor, snapshot_envelope
    mp, flow, dest, ex, claim = _build(tmp_path)
    try:
        before = _tables(dest)
        legacy = DurableRefundDestination(tmp_path / "atomic")
        res = LocalDestinationExecutor(legacy, flow.policy).execute_snapshot(snapshot_envelope(flow.envelope(flow.d1)))
        after = _tables(dest)
        print("EXECUTE_SNAPSHOT result:", res.status, res.error, res.attempted, res.observed_state)
        print("ATTEMPT ROWS left:", {k: (before.get(k), after[k]) for k in after if before.get(k) != after[k]})
        assert _effects(dest) == []
        assert res.status == "failed" and res.newly_executed is False
        # observed leftover: one attempts row plus attempted->failed events; no effect row, claim untouched
        leftovers = _attempt_rows(dest)
        assert [s for _, s in leftovers] == ["attempted", "failed"]
        assert dest.claim_state(claim.claim_id) == "issued"
        # route-B execution of the same decision is not blocked by the leftover rows, and they are not removed
        assert _run(flow, ex, claim, attempt_id="attempt-b").status == "executed"
        assert _effects(dest) == [flow.d1.effect_id]
        print("ATTEMPT ROWS after route-B execute:", _attempt_rows(dest))
    finally:
        mp.undo()


def test_REFUSED_pinned_control_plane_executor_on_route_b_database(tmp_path):
    from engine.operation_identity_atomic_destination import OperationIdentityAtomicAuthorityEffectDestination as Dest
    mp = pytest.MonkeyPatch()
    try:
        flow = Flow(tmp_path, mp, identity=True, wide=False,
                    dest_factory=lambda path, f: Dest(path, clock=lambda: f.NOW))
        try:
            res = flow.run(flow.d1)
            print("PINNED on route-B DB:", res.status, res.error)
            assert res.status != "executed"
        except Exception as exc:  # a raised refusal is equally a stop
            print("PINNED on route-B DB raised:", type(exc).__name__, exc)
        assert flow.ledger_effect_ids() == []
    finally:
        mp.undo()


def test_cp_workflow_execute_writes_only_the_cp_store_never_the_route_b_database(tmp_path):
    """BoundedAuthorizationWorkflow.execute (route A inside the Control Plane) is effect-capable on ITS destination."""
    mp, flow, dest, ex, claim = _build(tmp_path)
    try:
        attempt, obs = flow.f.execute(flow.p, flow.d1, adapter_id=flow.p.adapter_id, now=flow.NOW)
        assert attempt.status == "acknowledged" and obs.state == "applied"
        cp_dest = flow.f.destination
        assert Path(getattr(cp_dest, "path", "")).resolve() != Path(dest.path).resolve()
        assert _effects(dest) == []  # the route-B database holds no effect
    finally:
        mp.undo()


def test_REFUSED_acp_run_cannot_target_a_populated_route_b_directory(tmp_path):
    from agent_control_plane.cli import main
    mp, flow, dest, ex, claim = _build(tmp_path)
    try:
        ex_dir = Path(os.environ["D2_CONTROL_PLANE_DIR"]) / "examples" / "acp_run"
        out = tmp_path / "out"
        code = main(["run", "--manifest", str(ex_dir / "manifest.json"), "--proposal", str(ex_dir / "authorized" / "proposal.json"),
                     "--authority-context", str(ex_dir / "authorized" / "authority-context.json"),
                     "--resolver-state", str(ex_dir / "authorized" / "resolver-state.json"),
                     "--store-dir", str(dest.root), "--out-dir", str(out), "--now", "2026-10-05T19:00:00Z"])
        assert code == 2 and _effects(dest) == []
    finally:
        mp.undo()


# --- Dedupe TTL hazard (deleting operation_effects_v1 rows) --------------------------------------------------------------

def test_REFUSED_selected_destination_never_forgets_an_operation_after_time_passes(tmp_path, monkeypatch):
    import time
    from test_atomic_route_operation_identity import _renew
    mp, flow, dest, ex, claim = _build(tmp_path, wide=True)
    try:
        assert _run(flow, ex, claim).status == "executed"
        real = time.time
        monkeypatch.setattr(time, "time", lambda: real() + 10 * 365 * 86400)  # ten years later by the destination's clock
        d2 = _renew(flow, dest, identity=True)
        claim2 = ex.provision_claim(proposal=flow.p, decision=d2, now=flow.NOW)
        r2 = ex.execute(envelope=flow.envelope(d2), claim_id=claim2.claim_id)
        assert r2.status == "denied" and r2.error == "operation_already_committed"
        assert len(_op_rows(dest)) == 1 and _effects(dest) == [flow.d1.effect_id]
    finally:
        mp.undo()


def test_dedupe_ttl_destination_class_has_no_atomic_claim_path_and_is_not_the_selected_class():
    from engine.dedupe_destination import DedupeTtlOperationDestination
    from engine.operation_identity_atomic_destination import OperationIdentityAtomicAuthorityEffectDestination as Selected
    assert not hasattr(DedupeTtlOperationDestination, "execute_claim_atomic")
    assert not issubclass(Selected, DedupeTtlOperationDestination)
    assert getattr(Selected, "dedupe_capability", None) is None
    assert Selected._operation_guard.__qualname__.startswith("OperationIdentityDestination.")  # no TTL delete in the guard


# --- surfaces that ARE reachable through in-process / direct-destination access (ingress must close) ----------------------

def test_REACHABLE_forged_claim_without_any_control_plane_decision_commits_an_effect(tmp_path):
    """provision_claim / execute_claim_atomic: the claim commitment is an unkeyed hash and workflow=None is accepted."""
    h = _runtime_helper()
    env, dest, claim, ex = h.setup(tmp_path)  # claim built locally by test code, no workflow, no decision
    res = ex.execute(envelope=env, claim_id=claim.claim_id, attempt_id="attempt-1")
    assert res.status == "executed" and h.effects(dest) == [env.effect_id]


def test_REACHABLE_direct_destination_call_with_caller_chosen_operation_id_defeats_identity(tmp_path):
    """execute_claim_atomic(operation_id=...) is caller-controlled when the destination is called directly (no executor)."""
    from test_atomic_route_operation_identity import _renew
    from engine.safe_executor import snapshot_envelope
    mp, flow, dest, ex, claim = _build(tmp_path, wide=True)
    try:
        assert _run(flow, ex, claim).status == "executed"
        d2 = _renew(flow, dest, identity=True)
        claim2 = ex.provision_claim(proposal=flow.p, decision=d2, now=flow.NOW)
        value = dest.execute_claim_atomic(claim2.claim_id, snapshot_envelope(flow.envelope(d2)), attempt_id="attempt-direct",
                                          operation_id="a-different-operation-id")
        assert value["newly_executed"] is True and len(_effects(dest)) == 2
    finally:
        mp.undo()


def test_REACHABLE_simulate_is_caller_controlled_on_executor_execute_and_changes_the_effect_state(tmp_path):
    mp, flow, dest, ex, claim = _build(tmp_path)
    try:
        res = _run(flow, ex, claim, simulate="partial")
        assert res.status == "partial" and res.observed_state == "partial"
        c = sqlite3.connect(dest.path)
        try:
            assert c.execute("SELECT state FROM effects").fetchall() == [("partial",)]
        finally:
            c.close()
    finally:
        mp.undo()


def test_REACHABLE_authority_writers_can_reactivate_suspended_grant_and_delete_authority_rows(tmp_path):
    mp, flow, dest, ex, claim = _build(tmp_path)
    try:
        gid = flow.d1.binding.grant_id
        dest.set_grant_status(gid, status="suspended")
        assert _run(flow, ex, claim).status == "denied"
        dest.set_grant_status(gid, status="active")  # any holder of the destination object can flip it back
        dest.set_policy_state(next(iter(claim.policy_state)).ref, status="active")
        assert _run(flow, ex, claim).status == "executed"
        # removal of authority rows is also a public method
        assert hasattr(dest, "remove_authoritative_state")
    finally:
        mp.undo()


def test_REACHABLE_raw_sql_insert_into_effects_by_the_database_file_holder(tmp_path):
    """Outside the profile by declaration (file ownership/permissions): shown so the permission negative has a positive control."""
    mp, flow, dest, ex, claim = _build(tmp_path)
    try:
        c = sqlite3.connect(dest.path)
        try:
            c.execute("INSERT INTO effects(effect_id,operation_digest,grant_id,target,amount,unit,payload_json,state) "
                      "VALUES('raw','d','g','t',1.0,'USD','{}','applied')")
            c.commit()
        finally:
            c.close()
        assert "raw" in _effects(dest)
        print("DB MODE:", oct(os.stat(dest.path).st_mode & 0o777), "DIR MODE:", oct(os.stat(dest.root).st_mode & 0o777))
    finally:
        mp.undo()
