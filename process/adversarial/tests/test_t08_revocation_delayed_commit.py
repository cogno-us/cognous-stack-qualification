"""T08. Revocation against the delayed-commit destination: prevented or detected only (ideas B09, B10, B16, tier 3).

SPDX-License-Identifier: Apache-2.0

Attacker: a revoker acting at a chosen point of the commit sequence (or, symmetrically, a worker racing a revocation).
Deterministic barriers: the runtime's delayed-commit pause points ('observe' = after the control plane's effect-time check and
before dispatch; 'commit' = inside the destination call, before its transaction), its deferred landing, and the atomic
destination's transaction-stage hook. Event order is recorded; destination rows are read independently.
Invariant (plan): per route, the outcome matches the documented checkpoint level: the default route A (C0) is a known window
in which a revocation after the check does not stop the commit; the effective-grant destination and the atomic route refuse a
revocation that is visible to their own transaction.

Does not prove: revocations that are not written through the destination's own authority writer (the effective-grant row or
the atomic grant row); real provider latency; cross-host timing.
"""
from __future__ import annotations

import pytest

from _adv import atomic, effect_ids, flow
from conftest import observe

T = "T08"
DNP = "only revocations written to the destination's own authority store are visible to it; no real provider timing"


def _revoke(fl, events, label):
    def go():
        fl.r.statuses[fl.d1.binding.grant_id].status = "revoked"
        if fl.digest is not None:
            g = fl.r.contexts[fl.PROFILE]["grant"]
            fl.dest.set_effective_grant(principal=fl.p.principal, grant_id=g["grant_id"], revision=g["revision"],
                                        permissions=fl.p.requested_permissions, status="revoked")
        events.append("revoked@" + label)
    return go


def _run(fl, events):
    events.append("execute")
    r = fl.run(fl.d1)
    events.append("result:" + r.status)
    return r


@pytest.mark.parametrize("effective_grant", [False, True], ids=["route_a_default", "route_a_effective_grant"])
@pytest.mark.parametrize("point", ["before", "observe", "commit", "deferred_landing", "after"])
def test_revocation_point(cprt, tmp_path, monkeypatch, effective_grant, point):
    fl = flow(tmp_path, monkeypatch, effective_grant=effective_grant)
    events: list[str] = []
    if point == "before":
        _revoke(fl, events, point)()
        _run(fl, events)
    elif point in ("observe", "commit"):
        if point == "observe":  # the first observe_bound is the control plane's pre-dispatch read
            fl.dest.pause_at("observe", _revoke(fl, events, point))
        else:
            fl.dest.pause_at("commit", _revoke(fl, events, point))
        _run(fl, events)
    elif point == "deferred_landing":
        fl.dest.defer_next_commit()
        _run(fl, events)
        _revoke(fl, events, point)()
        try:
            fl.dest.land()
            events.append("landed")
        except PermissionError as exc:
            events.append("landing_refused:" + str(exc))
    else:
        _run(fl, events)
        _revoke(fl, events, point)()
    landed = bool(effect_ids(fl.dest.path))
    documented = {  # (effective_grant, point) -> effect lands?
        (False, "before"): False, (True, "before"): False,
        (False, "observe"): True, (True, "observe"): False,
        (False, "commit"): True, (True, "commit"): False,
        (False, "deferred_landing"): True, (True, "deferred_landing"): False,
        (False, "after"): True, (True, "after"): True,
    }[(effective_grant, point)]
    if point == "after":
        result = "not applicable"
    elif landed:
        result = "reproduced failure"  # the documented C0 window on the default route (known, by design)
    else:
        result = "prevented"
    observe(T, f"{'effective-grant' if effective_grant else 'default'} route A, revoke {point}", result, does_not_prove=DNP,
            detail={"events": events, "landed": landed, "documented_lands": documented})
    assert landed == documented, events


@pytest.mark.parametrize("stage", ["before_begin", "before_execute"])
def test_route_b_revocation_visible_to_the_transaction_is_refused(cprt, tmp_path, monkeypatch, stage):
    fl = flow(tmp_path, monkeypatch)
    dest, ex = atomic(fl, tmp_path)
    claim = ex.provision_claim(proposal=fl.p, decision=fl.d1, now=fl.NOW)
    events = []
    grant_id = fl.d1.binding.grant_id
    if stage == "before_execute":
        dest.set_grant_status(grant_id, status="revoked")
        events.append("revoked")
    else:
        original = dest._transaction_stage

        def hook(name):
            if name == "before_begin":
                dest.set_grant_status(grant_id, status="revoked")
                events.append("revoked@before_begin")
            return original(name)
        dest._transaction_stage = hook
    r = ex.execute(envelope=fl.envelope(fl.d1), claim_id=claim.claim_id)
    events.append("result:" + r.status)
    assert r.status == "denied" and effect_ids(dest.path) == [] and dest.claim_state(claim.claim_id) == "issued", events
    observe(T, f"route B, revoke {stage}", "prevented", does_not_prove=DNP, detail=events)


def test_route_b_revocation_after_commit_is_linearised_after_the_effect(cprt, tmp_path, monkeypatch):
    fl = flow(tmp_path, monkeypatch)
    dest, ex = atomic(fl, tmp_path)
    claim = ex.provision_claim(proposal=fl.p, decision=fl.d1, now=fl.NOW)
    events = []
    original = dest._transaction_stage

    def hook(name):
        if name == "after_commit":
            dest.set_grant_status(fl.d1.binding.grant_id, status="revoked")
            events.append("revoked@after_commit")
        return original(name)
    dest._transaction_stage = hook
    r = ex.execute(envelope=fl.envelope(fl.d1), claim_id=claim.claim_id)
    receipt = r.control_plane_evidence["authority_receipt"]
    assert r.status == "executed" and receipt["grant_status"] == "active" and effect_ids(dest.path) == [fl.d1.effect_id]
    observe(T, "route B, revoke after commit", "not applicable", does_not_prove=DNP,
            detail={"events": events, "receipt_status": receipt["grant_status"]})


def test_positive_control_no_revocation_one_effect(cprt, tmp_path, monkeypatch):
    for eg in (False, True):
        fl = flow(tmp_path / str(eg), monkeypatch, effective_grant=eg)
        assert fl.run(fl.d1).status == "executed"
        assert effect_ids(fl.dest.path) == [fl.d1.effect_id]
