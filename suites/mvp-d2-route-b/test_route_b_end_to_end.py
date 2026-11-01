"""Route B (Control Plane workflow -> AtomicLocalControlPlaneExecutor(operation_identity=True) -> operation-identity atomic
SQLite destination) end-to-end observations at the MVP tuple. Real claim provisioning (executor.provision_claim ->
provision_local_execution_claim), real persisted decision, operation id derived from the decision (never the caller).

SPDX-License-Identifier: Apache-2.0
Scope: synthetic $10-class refund fixtures of the Control Plane test package; builder tests, no Qualification verdict.
Local builder evidence, not wired to CI; not a Qualification verdict. test_REACHABLE_* tests (other file) PASS when a hole exists.
test_approval_revocation_is_terminal_like_grant_revocation asserts the terminal expectation. It failed at Runtime ec728da6 and
passes at Runtime c5e97e87 (F3); it is not marked xfail.
"""
from __future__ import annotations

import sqlite3

import pytest

from _oi_flow import Flow

OPERATION = "op-order-100/refund-1"


def _build(tmp_path, *, dest_cls=None, wide=False):
    from engine.atomic_local_control_plane_executor import AtomicLocalControlPlaneExecutor
    if dest_cls is None:
        from engine.operation_identity_atomic_destination import OperationIdentityAtomicAuthorityEffectDestination as dest_cls
    mp = pytest.MonkeyPatch()
    flow = Flow(tmp_path, mp, identity=True, wide=wide)
    flow.OPERATION_ID = OPERATION
    dest = dest_cls(tmp_path / "atomic", clock=lambda: flow.NOW)
    ex = AtomicLocalControlPlaneExecutor(workflow=flow.f, destination=dest, policy=flow.policy, operation_identity=True)
    claim = ex.provision_claim(proposal=flow.p, decision=flow.d1, now=flow.NOW)
    return mp, flow, dest, ex, claim


def _effects(dest):
    c = sqlite3.connect(dest.path)
    try:
        return [r[0] for r in c.execute("SELECT effect_id FROM effects ORDER BY effect_id")]
    finally:
        c.close()


def _op_rows(dest):
    c = sqlite3.connect(dest.path)
    try:
        return c.execute("SELECT principal_id,authority_domain,operation_id,effect_id FROM operation_effects_v1").fetchall()
    finally:
        c.close()


def _attempt_rows(dest):
    c = sqlite3.connect(dest.path)
    try:
        return c.execute("SELECT attempt_id,status FROM attempt_events ORDER BY rowid").fetchall()
    finally:
        c.close()


def _run(flow, ex, claim, **kw):
    return ex.execute(envelope=flow.envelope(flow.d1), claim_id=claim.claim_id, **kw)


# 1. duplicate dispatch after commit ---------------------------------------------------------------------------------

def test_duplicate_dispatch_of_same_claim_after_commit_is_refused_one_effect(tmp_path):
    mp, flow, dest, ex, claim = _build(tmp_path)
    try:
        r1 = _run(flow, ex, claim, attempt_id="attempt-1")
        assert (r1.status, r1.acknowledged, r1.newly_executed) == ("executed", True, True)
        r2 = _run(flow, ex, claim, attempt_id="attempt-2")
        print("DUP-SAME-CLAIM r2:", r2.status, r2.error, r2.attempted, r2.newly_executed, r2.observed_state)
        assert r2.status == "denied" and r2.attempted is False and r2.newly_executed is False
        assert _effects(dest) == [flow.d1.effect_id]
        assert len(_op_rows(dest)) == 1
        assert dest.claim_state(claim.claim_id) == "consumed"
        assert dest.budget_state(f"grant:{flow.d1.binding.grant_id}")["used_effects"] == 1
    finally:
        mp.undo()


def test_second_claim_for_the_same_decision_cannot_produce_a_second_effect(tmp_path):
    """Re-provisioning a fresh claim for the already-executed decision (same effect_id, new claim_id) and executing it."""
    mp, flow, dest, ex, claim = _build(tmp_path, wide=True)  # cap 2: only identity/effect-id uniqueness can stop it
    try:
        assert _run(flow, ex, claim).status == "executed"
        try:
            claim2 = ex.provision_claim(proposal=flow.p, decision=flow.d1, now=flow.NOW, claim_id="claim-second")
        except Exception as exc:  # refusal at provisioning is an acceptable stop; record the exact text
            print("DUP-REPROVISION refused at provisioning:", type(exc).__name__, exc)
            assert _effects(dest) == [flow.d1.effect_id]
            return
        r2 = ex.execute(envelope=flow.envelope(flow.d1), claim_id=claim2.claim_id)
        print("DUP-REPROVISION r2:", r2.status, r2.error, r2.observed_state)
        # Observed at the tuple: the operation guard admits the same effect_id; the effects PRIMARY KEY (effect_id) rolls the
        # transaction back (IntegrityError) and the executor reports status unknown (conservative), claim-second stays issued.
        assert r2.status == "unknown" and r2.newly_executed is False and r2.observation["retry_eligible"] is False
        assert _effects(dest) == [flow.d1.effect_id]
        assert dest.claim_state(claim2.claim_id) == "issued" and dest.claim_state(claim.claim_id) == "consumed"
        assert dest.budget_state(claim2.budget_id)["used_effects"] == 1
    finally:
        mp.undo()


def test_renewed_decision_same_operation_is_refused_by_operation_identity_with_cap_two(tmp_path):
    from test_atomic_route_operation_identity import _renew  # suites/operation-identity helper, unmodified
    mp, flow, dest, ex, claim = _build(tmp_path, wide=True)
    try:
        assert _run(flow, ex, claim).status == "executed"
        d2 = _renew(flow, dest, identity=True)
        claim2 = ex.provision_claim(proposal=flow.p, decision=d2, now=flow.NOW)
        r2 = ex.execute(envelope=flow.envelope(d2), claim_id=claim2.claim_id)
        assert r2.status == "denied" and r2.error == "operation_already_committed"
        assert _effects(dest) == [flow.d1.effect_id]
        assert dest.claim_state(claim2.claim_id) == "issued"
    finally:
        mp.undo()


# 2. lost acknowledgement / UNKNOWN: no blind retry ---------------------------------------------------------------------

def _lost_ack_dest():
    from engine.operation_identity_atomic_destination import OperationIdentityAtomicAuthorityEffectDestination as Base

    class LostAck(Base):
        def _transaction_stage(self, stage):
            if stage == "after_commit":
                raise RuntimeError("lost acknowledgement after commit")
    return LostAck


def test_lost_ack_is_unknown_then_second_execute_is_denied_one_effect(tmp_path):
    mp, flow, dest, ex, claim = _build(tmp_path, dest_cls=_lost_ack_dest(), wide=True)
    try:
        r1 = _run(flow, ex, claim, attempt_id="attempt-1")
        assert (r1.status, r1.attempted, r1.acknowledged, r1.newly_executed) == ("unknown", True, False, False)
        assert r1.observation["retry_eligible"] is False
        assert r1.observed_state == "applied"  # exact claim reconciliation sees the durable effect
        assert _effects(dest) == [flow.d1.effect_id]
        r2 = _run(flow, ex, claim, attempt_id="attempt-2")
        print("LOSTACK r2:", r2.status, r2.error, r2.attempted, r2.observed_state, r2.observation,
              r2.control_plane_evidence)
        assert r2.status == "denied" and r2.attempted is False and r2.newly_executed is False
        assert _effects(dest) == [flow.d1.effect_id]
        assert dest.budget_state(f"grant:{flow.d1.binding.grant_id}")["used_effects"] == 1
        # the first execute wrote ('attempt-1','attempted') and ('attempt-1','executed'); the denied second execute wrote none
        assert _attempt_rows(dest) == [("attempt-1", "attempted"), ("attempt-1", "executed")]
        rec = ex.reconcile(claim_id=claim.claim_id, envelope=flow.envelope(flow.d1))
        assert rec.observation["status"] == "applied" and rec.observation["retry_eligible"] is False
    finally:
        mp.undo()


def test_lost_ack_second_execute_is_denied_pre_dispatch_with_one_committed_effect(tmp_path):
    """Characterisation of the observed second result (not the 'unknown' the brief expected): status "denied", error
    "execution claim is not usable", attempted False, observed_state "unknown" (the dataclass default of a pre-dispatch denial,
    not an observation), observation None, failure_class authority_hold. NOTE: "denied / attempted False" does not mean "no
    effect": one effect IS committed. The unknown / retry_eligible False facts belong to the FIRST result and to reconcile()."""
    mp, flow, dest, ex, claim = _build(tmp_path, dest_cls=_lost_ack_dest(), wide=True)
    try:
        r1 = _run(flow, ex, claim, attempt_id="attempt-1")
        assert r1.status == "unknown" and r1.observation["retry_eligible"] is False
        r2 = _run(flow, ex, claim, attempt_id="attempt-2")
        assert r2.status == "denied"
        assert r2.error == "execution claim is not usable"
        assert r2.attempted is False and r2.acknowledged is False and r2.newly_executed is False
        assert r2.observed_state == "unknown" and r2.observation is None
        assert r2.control_plane_evidence["failure_class"] == "authority_hold"
        assert _effects(dest) == [flow.d1.effect_id]
    finally:
        mp.undo()


def test_lost_ack_restart_creates_no_fresh_effect(tmp_path):
    from engine.atomic_local_control_plane_executor import AtomicLocalControlPlaneExecutor
    from engine.operation_identity_atomic_destination import OperationIdentityAtomicAuthorityEffectDestination as Plain
    mp, flow, dest, ex, claim = _build(tmp_path, dest_cls=_lost_ack_dest(), wide=True)
    try:
        assert _run(flow, ex, claim, attempt_id="attempt-1").status == "unknown"
        restarted = Plain(tmp_path / "atomic", clock=lambda: flow.NOW)
        ex2 = AtomicLocalControlPlaneExecutor(workflow=flow.f, destination=restarted, policy=flow.policy, operation_identity=True)
        r2 = ex2.execute(envelope=flow.envelope(flow.d1), claim_id=claim.claim_id, attempt_id="attempt-2")
        assert r2.status == "denied" and r2.newly_executed is False
        assert _effects(restarted) == [flow.d1.effect_id]
    finally:
        mp.undo()


def test_caller_supplied_simulate_lost_ack_is_unknown_with_one_effect_documenting_the_lever(tmp_path):
    """simulate is a caller-controlled parameter on execute(); here it only produces the lost-ack branch (inventory item)."""
    mp, flow, dest, ex, claim = _build(tmp_path)
    try:
        r1 = _run(flow, ex, claim, simulate="lost_ack", attempt_id="attempt-1")
        assert r1.status == "unknown" and r1.observation["retry_eligible"] is False
        assert _effects(dest) == [flow.d1.effect_id]
    finally:
        mp.undo()


# 3. grant revocation before effect ------------------------------------------------------------------------------------

def test_grant_revoked_before_effect_is_refused_zero_effects(tmp_path):
    mp, flow, dest, ex, claim = _build(tmp_path)
    try:
        dest.set_grant_status(flow.d1.binding.grant_id, status="revoked")
        r = _run(flow, ex, claim)
        assert r.status == "denied" and r.attempted is False and "authoritative grant state invalid" in r.error
        assert _effects(dest) == [] and _op_rows(dest) == []
        assert _attempt_rows(dest) == [], "a refused atomic execute leaves no attempt rows (rolled back with the transaction)"
        assert dest.claim_state(claim.claim_id) == "issued"
        assert dest.budget_state(f"grant:{flow.d1.binding.grant_id}")["used_effects"] == 0
        with pytest.raises(PermissionError, match="grant revision is revoked"):
            dest.set_grant_status(flow.d1.binding.grant_id, status="active")
        assert _run(flow, ex, claim).status == "denied" and _effects(dest) == []
    finally:
        mp.undo()


def test_grant_status_flip_alone_is_refused_zero_effects(tmp_path):
    """Isolates the grant status check: the row is set to revoked by SQL, so no retained-revision record exists and
    _revision_revoked is False; only the `grant["status"] != "active"` line can refuse."""
    mp, flow, dest, ex, claim = _build(tmp_path)
    try:
        c = sqlite3.connect(dest.path)
        try:
            c.execute("UPDATE authority_grants_v1 SET status='revoked' WHERE grant_id=?", (flow.d1.binding.grant_id,))
            c.commit()
            assert c.execute("SELECT name FROM sqlite_master WHERE name='authority_grant_revocations_v1'").fetchall() == []
        finally:
            c.close()
        r = _run(flow, ex, claim)
        assert r.status == "denied" and "authoritative grant state invalid" in r.error
        assert _effects(dest) == [] and dest.claim_state(claim.claim_id) == "issued"
    finally:
        mp.undo()


# 4. approval withdrawal before effect ---------------------------------------------------------------------------------

def _approval_ref(claim):
    [ref] = [a.approval_ref for a in claim.approval_state]
    return ref


def test_approval_revoked_before_effect_is_refused_zero_effects(tmp_path):
    mp, flow, dest, ex, claim = _build(tmp_path)
    try:
        dest.set_approval_status(_approval_ref(claim), status="revoked")
        r = _run(flow, ex, claim)
        assert r.status == "denied" and r.attempted is False and "authoritative approval state invalid" in r.error
        assert _effects(dest) == [] and dest.claim_state(claim.claim_id) == "issued"
    finally:
        mp.undo()


def test_approval_revocation_is_terminal_like_grant_revocation(tmp_path):
    """EXPECTATION (parity with grants: revoked is terminal per revision). Not marked xfail. Failed at Runtime ec728da6; the F3 (Runtime PR #144) targets it."""
    mp, flow, dest, ex, claim = _build(tmp_path)
    try:
        ref = _approval_ref(claim)
        dest.set_approval_status(ref, status="revoked")
        with pytest.raises(PermissionError):
            dest.set_approval_status(ref, status="active")
        assert _run(flow, ex, claim).status == "denied" and _effects(dest) == []
    finally:
        mp.undo()


def test_approval_row_removal_before_effect_is_refused_zero_effects(tmp_path):
    mp, flow, dest, ex, claim = _build(tmp_path)
    try:
        dest.remove_authoritative_state("approval", _approval_ref(claim))
        r = _run(flow, ex, claim)
        assert r.status == "denied" and "authoritative approval state unavailable" in r.error
        assert _effects(dest) == []
    finally:
        mp.undo()
