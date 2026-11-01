"""T17. Last-unit budget race and grant multiplication (ideas G47, G48, tier 7).

SPDX-License-Identifier: Apache-2.0

Attacker: several workers racing for the last unit of a grant's effect budget, or one actor holding several grants.
Barriers: route A, the delayed-commit 'commit' pause point (worker A has passed the control plane's effect-time check and is
inside the destination call; worker B runs a different operation on the same grant to completion; A resumes). Route B, the
atomic destination's 'before_begin' transaction stage (worker B executes the same claim in another thread before A's
transaction begins). Destination rows are read independently.
Invariant: the last unit is spent once. Grant multiplication (N grants of cap 1, one notional total) is measured and reported as
characterised: no cross-grant ceiling exists (SCN-C16 independent budgets).

Does not prove: route C (exchange budget semantics are unmapped in the plan); two different claims on one atomic budget (the
synthetic approval binds one proposal per approval reference); the multiplication leg is measured at the effective-grant
destination with valid grant rows, not through N full control plane flows.
"""
from __future__ import annotations

import threading

from _adv import atomic, effect_ids, flow, rows, snapshot
from conftest import observe

T = "T17"
DNP = "route C not run; one atomic claim raced (not two claims on one budget); multiplication measured at the destination"


def _second_operation(fl):
    p2 = fl.p.model_copy(deep=True)
    p2.correlation_id = "case-2"
    ref = fl.r.contexts[fl.PROFILE]["grant"]["approval_refs"][0]
    fl.r.approvals[ref].proposal_commitment = fl.cp.commitment(p2.model_dump(mode="json", exclude_none=False))
    fl.tra.bind_approval(fl.r, fl.f.runtime_authority_profile or fl.cfg)
    d2 = fl.f.decide(p2, now=fl.NOW)
    assert d2.result == "authorized" and d2.effect_id != fl.d1.effect_id, d2.reasons
    return p2, d2


def test_route_a_last_unit_spent_once_under_barrier(cprt, tmp_path, monkeypatch):
    fl = flow(tmp_path, monkeypatch)  # per-grant cap 1: one unit
    events, out = [], {}

    def worker_b():
        p2, d2 = _second_operation(fl)
        out["B"] = fl.run(d2, p2).status
        events.append("B:" + out["B"])
    errors = {}

    fl.dest.pause_at("commit", worker_b)
    events.append("A:start")
    rA = fl.run(fl.d1)
    out["A"] = rA.status
    errors["A"] = [r["error"] for r in rows(fl.dest.path, "attempt_events") if r["status"] == "failed"]
    events.append("A:" + out["A"])
    n = len(effect_ids(fl.dest.path))
    observe(T, "route A last unit, two operations, barrier inside the destination", "prevented" if n == 1 else
            "reproduced failure", does_not_prove=DNP, detail={"events": events, "effects": n, "errors": errors})
    assert n == 1 and out == {"B": "executed", "A": "failed"} and any("max_effects" in (x or "") for x in errors["A"]), (events, errors)


def test_route_b_same_claim_raced_spent_once(cprt, tmp_path, monkeypatch):
    fl = flow(tmp_path, monkeypatch)
    dest, ex = atomic(fl, tmp_path)
    claim = ex.provision_claim(proposal=fl.p, decision=fl.d1, now=fl.NOW)
    events, out = [], {}
    original = dest._transaction_stage
    fired = {"done": False}

    def hook(name):
        if name == "before_begin" and not fired["done"]:
            fired["done"] = True
            t = threading.Thread(target=lambda: out.__setitem__("B", ex.execute(envelope=fl.envelope(fl.d1),
                                                                                  claim_id=claim.claim_id).status))
            t.start()
            t.join(60)
            events.append("B:" + str(out.get("B")))
        return original(name)
    dest._transaction_stage = hook
    out["A"] = ex.execute(envelope=fl.envelope(fl.d1), claim_id=claim.claim_id).status
    events.append("A:" + out["A"])
    n = len(effect_ids(dest.path))
    assert dest.budget_state(f"grant:{fl.d1.binding.grant_id}")["used_effects"] == 1
    observe(T, "route B same claim raced at before_begin", "prevented" if n == 1 else "reproduced failure", does_not_prove=DNP,
            detail={"events": events, "effects": n})
    assert n == 1 and sorted(out.values()) == ["denied", "executed"], events


def test_grant_multiplication_is_characterised(cprt, tmp_path, monkeypatch):
    """N grants of cap 1, each valid at the effective-grant destination: N effects; nothing aggregates across grants (known)."""
    import dataclasses
    from engine.effective_grant import DERIVATION, EffectiveGrantDestination
    fl = flow(tmp_path / "f", monkeypatch)
    dest = EffectiveGrantDestination(tmp_path / "dest")
    base = snapshot(fl.envelope(fl.d1))
    N = 5
    for i in range(N):
        grant = f"urn:cognous:grant:split-{i}"
        op = dataclasses.replace(base.operation, grant_id=grant, effective_max_effects=1)
        snap = dataclasses.replace(base, effect_id=f"sha256:{i:064x}", operation=op)
        digest = dest.set_effective_grant(principal=op.principal, grant_id=grant, revision=op.grant_revision,
                                          permissions=list(op.requested_permissions))
        dest.commit(snap, expected_effective_grant_digest=digest, effective_grant_derivation_version=DERIVATION)
    n = len(effect_ids(dest.path))
    observe(T, f"grant multiplication over {N} grants of cap 1", "reproduced failure", does_not_prove=DNP,
            detail={"effects": n, "aggregate_amount": n * fl.p.amount, "known": "no cross-grant ceiling (SCN-C16)"})
    assert n == N  # characterised known limitation


def test_positive_control_single_worker_spends_last_unit_once(cprt, tmp_path, monkeypatch):
    fl = flow(tmp_path, monkeypatch)
    assert fl.run(fl.d1).status == "executed"
    p2, d2 = _second_operation(fl)
    assert fl.run(d2, p2).status != "executed"
    assert effect_ids(fl.dest.path) == [fl.d1.effect_id]
