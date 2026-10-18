"""T02. Non-dispatching entry points leave destinations unchanged (ideas D25, H65, G54, tier 1).

SPDX-License-Identifier: Apache-2.0

Attacker: any caller of the reconcile, recovery, reaper, observation, replay-import, evidence-pack, ODES-export, verifier and
witness entry points, including with a flood of malformed inputs.
Fixture: route A (control plane + runtime adapter + delayed-commit SQLite destination, freshness/0.1 on so the recovery pass and
reaper exist) with one landed effect and one unresolved attempt (its commit held in flight), and route B (atomic destination)
with one consumed and one issued claim.
Invariant: these paths never create, change or delete an effect row, a claim, a budget or an authority row. Every such table of
every destination (and the control plane's own JSON destination) is hashed before and after each entry point, through an
independent read. Audit-table rows (attempt events, failure records) written by an entry point are reported, not counted as
destination change.
Positive control: a dispatching entry (landing the held commit) changes the hash, so the observer can see change.

Does not prove: entry points added after the attacked revisions; the ocs CLI and acp subcommands other than validate-run and
witness; a reaper death that is not raised through its own failure path (the fail-closed check is exercised, not every way a
thread can die).
"""
from __future__ import annotations

import io
import json
from contextlib import redirect_stderr, redirect_stdout

import pytest

from _adv import atomic, bundle, downstream, flow, table_digest, tables, verify
from conftest import observe, require

T = "T02"
DNP = "entry points added after the attacked revisions, the ocs CLI and other acp subcommands are not covered"
PROTECTED = ("effects", "execution_claims_v1", "effect_budgets_v1", "authority_grants_v1", "authority_approvals_v1",
             "authority_policies_v1", "authority_evidence_v1", "effective_grants_v1", "operation_effects_v1")


def _protected(path):
    return table_digest(path, [t for t in tables(path) if t in PROTECTED])


def _audit(path):
    return table_digest(path, [t for t in tables(path) if t not in PROTECTED])


def _second(fl):
    p2 = fl.p.model_copy(deep=True)
    p2.correlation_id = "case-2"
    ref = fl.r.contexts[fl.PROFILE]["grant"]["approval_refs"][0]
    fl.r.approvals[ref].proposal_commitment = fl.cp.commitment(p2.model_dump(mode="json", exclude_none=False))
    fl.tra.bind_approval(fl.r, fl.f.runtime_authority_profile or fl.cfg)
    d2 = fl.f.decide(p2, now=fl.NOW)
    assert d2.result == "authorized", d2.reasons
    return p2, d2


@pytest.fixture
def world(cprt, tmp_path, monkeypatch):
    fl = flow(tmp_path / "a", monkeypatch, wide=True, freshness={}, live_observation_clock=True)
    assert fl.run(fl.d1).status == "executed"
    p2, d2 = _second(fl)
    fl.dest.defer_next_commit()
    r2 = fl.run(d2, p2)
    assert r2.status == "unknown" and len(fl.dest.in_flight) == 1  # the unresolved attempt
    fb = flow(tmp_path / "b", monkeypatch)
    dest_b, ex_b = atomic(fb, tmp_path / "b")
    c1 = ex_b.provision_claim(proposal=fb.p, decision=fb.d1, now=fb.NOW)
    assert ex_b.execute(envelope=fb.envelope(fb.d1), claim_id=c1.claim_id).status == "executed"
    return {"fl": fl, "p2": p2, "d2": d2, "fb": fb, "dest_b": dest_b, "ex_b": ex_b, "c1": c1, "tmp": tmp_path}


def _state(w):
    fl = w["fl"]
    return {"route_a": _protected(fl.dest.path), "route_b": _protected(w["dest_b"].path),
            "cp_json_destination": json.dumps(fl.f.destination.snapshot(), sort_keys=True)}


def _entry_points(w):
    fl, fb, ex_b, dest_b, c1 = w["fl"], w["fb"], w["ex_b"], w["dest_b"], w["c1"]
    tmp = w["tmp"]
    from engine.safe_executor import snapshot_envelope
    env1, env2 = fl.envelope(fl.d1), fl.envelope(w["d2"], w["p2"])
    points = {
        "cp.reconcile(landed)": lambda: fl.f.reconcile(fl.d1.effect_id, now=fl.NOW),
        "cp.reconcile(unresolved)": lambda: fl.f.reconcile(w["d2"].effect_id, now=fl.NOW),
        "records.recover_interrupted_checks": lambda: fl.f.records.recover_interrupted_checks(),
        "records.recovery_pass": lambda: fl.f.records.recovery_pass(trigger="manual", now=fl.NOW, record_run=True),
        "reaper.run_startup+run_due": lambda: (lambda r: (r.run_startup(), r.run_due()))(fl.f.reaper(clock=lambda: fl.NOW)),
        "runtime.reconcile(landed)": lambda: fl.executor.reconcile(env1, now=fl.NOW),
        "runtime.reconcile(unresolved)": lambda: fl.executor.reconcile(env2, now=fl.NOW),
        "runtime.observe_historical": lambda: fl.executor.observe_historical(env1),
        "atomic.reconcile(consumed)": lambda: ex_b.reconcile(claim_id=c1.claim_id, envelope=fb.envelope(fb.d1)),
        "atomic.reconcile_claim": lambda: dest_b.reconcile_claim(c1.claim_id, snapshot_envelope(fb.envelope(fb.d1))),
        "atomic.read_helpers": lambda: (dest_b.authority_receipt("x"), dest_b.claim_state(c1.claim_id),
                                        dest_b.budget_state("grant:x")),
    }

    def downstream_all():
        paths = require("verifier", "replay", "evidence_pack", "odes")
        b = bundle(fl, tmp / "bundle")
        verify(paths["verifier"], b)
        downstream(fl, tmp / "downstream", paths)

    def witness_and_validate():
        import agent_control_plane.witness as W
        from agent_control_plane.cli import main
        doc = json.loads(fl.f.records.path.read_text(encoding="utf-8"))
        witness = W.LocalFileWitness(tmp / "witness" / "w.jsonl")
        W.publish_head(doc, witness)
        W.verify_against_witness(doc, witness)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            main(["validate-run", str(fl.f.records.path)])
    points["replay+pack+odes+verifier"] = downstream_all
    points["witness+acp validate-run"] = witness_and_validate
    return points


def _flood(w):
    """Malformed inputs at the reconcile and observation entry points: every call must fail or observe, never write."""
    import dataclasses
    fl, ex_b, fb = w["fl"], w["ex_b"], w["fb"]
    env = fl.envelope(fl.d1)
    bad = ["", "x", "sha256:" + "0" * 64, "sha256:" + "g" * 64, "\x00", "' OR 1=1 --", "a" * 5000, fl.d1.effect_id + "\n"]
    outcomes = {"raised": 0, "returned": 0}
    calls = []
    for b in bad:
        calls.append(lambda b=b: fl.f.reconcile(b, now=fl.NOW))
        calls.append(lambda b=b: fl.executor.reconcile(dataclasses.replace(env, effect_id=b or "e"), now=fl.NOW))
        calls.append(lambda b=b: ex_b.reconcile(claim_id=b, envelope=fb.envelope(fb.d1)))
        calls.append(lambda b=b: fl.executor.observe_historical(dataclasses.replace(env, decision_id=b or "d")))
    calls.append(lambda: fl.executor.reconcile(object(), now=fl.NOW))
    calls.append(lambda: ex_b.reconcile(claim_id=None, envelope=None))
    for call in calls:
        try:
            call()
            outcomes["returned"] += 1
        except Exception:  # noqa: BLE001 - a refusal of a malformed input is the expected outcome
            outcomes["raised"] += 1
    return outcomes


def test_entry_points_leave_destinations_unchanged(world):
    changed, audit = {}, {}
    for name, call in _entry_points(world).items():
        before, audit_before = _state(world), _audit(world["fl"].dest.path)
        try:
            call()
            outcome = "returned"
        except Exception as exc:  # noqa: BLE001 - recorded; a refusal is fine, a write is not
            outcome = "raised:" + type(exc).__name__
        after = _state(world)
        if after != before:
            changed[name] = outcome
        if _audit(world["fl"].dest.path) != audit_before:
            audit[name] = "audit rows written"
    observe(T, "non-dispatching entry points (13 groups)", "prevented" if not changed else "reproduced failure",
            does_not_prove=DNP, detail={"changed": changed, "audit_only": audit})
    assert changed == {}, changed


def test_malformed_input_flood_leaves_destinations_unchanged(world):
    before = _state(world)
    outcomes = _flood(world)
    assert _state(world) == before
    observe(T, "malformed-input flood at reconcile/observe", "prevented", does_not_prove=DNP, detail=outcomes)


def test_reaper_death_fails_closed(world):
    """The background reaper thread stops on an error: decide refuses (R1 finding 6: observed, not silent)."""
    import itertools
    import time
    from datetime import timedelta
    from agent_control_plane.freshness import ReaperFailed
    fl = world["fl"]
    ticks = itertools.count()
    reaper = fl.f.reaper(clock=lambda: fl.NOW + timedelta(hours=next(ticks)))  # every pass is due
    reaper.start()
    original = fl.f.records.recovery_pass

    def boom(*a, **kw):
        raise OSError("synthetic recovery failure")
    fl.f.records.recovery_pass = boom
    deadline = time.monotonic() + 10
    while not reaper.failed and time.monotonic() < deadline:
        time.sleep(0.05)
    fl.f.records.recovery_pass = original
    assert reaper.failed, "the reaper thread did not stop on the injected error"
    with pytest.raises(ReaperFailed):
        fl.f.decide(fl.p, now=fl.NOW)
    observe(T, "reaper thread stopped on an error", "detected only", does_not_prove=DNP,
            detail="decide refuses (ReaperFailed) after the background reaper stopped; nothing restarts it")


def test_positive_control_dispatching_entry_changes_the_hash(world):
    before = _state(world)
    world["fl"].dest.land()
    assert _state(world) != before
