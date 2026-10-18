"""T07. Authority ABA (idea B15, tier 3; the one testable-uncovered idea of the plan).

SPDX-License-Identifier: Apache-2.0

Attacker: an administrator who revokes a grant and later re-creates it under the same grant id.
Invariant: an approval, decision or claim made against the first grant cannot spend authority of the re-created grant unless the
binding distinguishes them; the atomic destination's provisioning refusal on differing rows holds.
Routes: A (control plane decide/execute -> runtime PinnedControlPlaneExecutor -> SQLite destination) and B (runtime
AtomicLocalControlPlaneExecutor -> atomic authority/effect destination). Destination rows are read independently.

Tests marked xfail(strict, raises=AssertionError) assert the invariant, which does not hold at the attacked revisions; the
detail is held for the private channel in SECURITY.md, not described here. A strict xfail turns red when the behaviour changes,
so a fix is noticed; a broken precondition fails outright (pytest.fail), it is never absorbed by the xfail.

Does not prove: anything about real resolver implementations (external; the synthetic resolver serves whatever state it is
given); whether a revoked grant should be terminal is a policy question this test records but does not settle; route C.
"""
from __future__ import annotations

import pytest

from _adv import atomic, effect_ids, flow
from conftest import observe

T = "T07"
DNP = "synthetic resolver only; real resolver semantics are external; route C not run"
SUSPECTED = "suspected defect at the attacked revisions; detail held for the private channel (SECURITY.md)"


def _status(fl):
    return fl.r.statuses[fl.d1.binding.grant_id]


def test_positive_control_original_grant_executes_once(cprt, tmp_path, monkeypatch):
    fl = flow(tmp_path, monkeypatch)
    r = fl.run(fl.d1)
    assert r.status == "executed"
    assert effect_ids(fl.dest.path) == [fl.d1.effect_id]


def test_route_a_revocation_alone_is_refused(cprt, tmp_path, monkeypatch):
    fl = flow(tmp_path, monkeypatch)
    _status(fl).status = "revoked"
    r = fl.run(fl.d1)
    assert r.status == "denied" and effect_ids(fl.dest.path) == []
    assert ["grant_revoked"] in [x.reasons for x in fl.f.records.load().refusals]
    observe(T, "route A: revoked, no re-creation", "prevented", does_not_prove=DNP)


def test_route_a_recreated_as_new_revision_is_refused(cprt, tmp_path, monkeypatch):
    fl = flow(tmp_path, monkeypatch)
    _status(fl).status = "revoked"
    fl.publish_revision("2")
    _status(fl).status = "active"
    r = fl.run(fl.d1)
    assert r.status == "denied" and effect_ids(fl.dest.path) == []
    observe(T, "route A: re-created as revision 2", "prevented", does_not_prove=DNP)


def test_route_a_recreated_with_new_authority_basis_is_refused(cprt, tmp_path, monkeypatch):
    fl = flow(tmp_path, monkeypatch)
    _status(fl).status = "revoked"
    fl.run(fl.d1)
    st = _status(fl)
    st.status, st.authority_basis_ref = "active", "urn:cognous:authority-basis:reissued"
    r = fl.run(fl.d1)
    assert r.status == "denied" and effect_ids(fl.dest.path) == []
    observe(T, "route A: re-created with a new authority basis", "prevented", does_not_prove=DNP)


def test_route_a_spent_authority_is_not_spent_twice_after_recreation(cprt, tmp_path, monkeypatch):
    """d1 commits, the grant is revoked and re-created identically; a fresh decision has the same effect id and only reconciles."""
    fl = flow(tmp_path, monkeypatch)
    assert fl.run(fl.d1).status == "executed"
    _status(fl).status = "revoked"
    _status(fl).status = "active"
    d2 = fl.f.decide(fl.p, now=fl.NOW)
    assert d2.result == "authorized" and d2.effect_id == fl.d1.effect_id
    assert fl.run(d2).status == "reconciled"
    assert effect_ids(fl.dest.path) == [fl.d1.effect_id]
    observe(T, "route A: spent authority after identical re-creation", "prevented", does_not_prove=DNP)


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=SUSPECTED)
@pytest.mark.parametrize("variant", ["identical", "new_status_version"])
def test_route_a_unspent_decision_after_recreation(cprt, tmp_path, monkeypatch, variant):
    fl = flow(tmp_path, monkeypatch)
    _status(fl).status = "revoked"
    if fl.run(fl.d1).status != "denied":
        pytest.fail("precondition: the revocation itself was not refused")  # not an AssertionError: never hidden by the xfail
    st = _status(fl)
    st.status = "active"
    if variant == "new_status_version":
        st.version = "status-v2"
    r = fl.run(fl.d1)
    observe(T, f"route A: unspent decision, re-creation ({variant})",
            "reproduced failure" if effect_ids(fl.dest.path) else "prevented", does_not_prove=DNP,
            detail={"status": r.status})
    assert r.status == "denied" and effect_ids(fl.dest.path) == []


def test_route_b_provisioning_refused_while_revoked(cprt, tmp_path, monkeypatch):
    fl = flow(tmp_path, monkeypatch)
    dest, ex = atomic(fl, tmp_path)
    ex.provision_claim(proposal=fl.p, decision=fl.d1, now=fl.NOW)
    dest.set_grant_status(fl.d1.binding.grant_id, status="revoked")
    d2 = fl.f.decide(fl.p, now=fl.NOW)  # the control-plane side has not seen the revocation yet
    with pytest.raises(PermissionError, match="existing authoritative grant state rejects claim provisioning"):
        ex.provision_claim(proposal=fl.p, decision=d2, now=fl.NOW)
    assert effect_ids(dest.path) == []
    observe(T, "route B: provisioning refusal on a differing (revoked) row", "prevented", does_not_prove=DNP)


def test_route_b_recreated_as_new_revision_refuses_old_claim(cprt, tmp_path, monkeypatch):
    fl = flow(tmp_path, monkeypatch)
    dest, ex = atomic(fl, tmp_path)
    claim = ex.provision_claim(proposal=fl.p, decision=fl.d1, now=fl.NOW)
    dest.set_grant_status(fl.d1.binding.grant_id, status="revoked")
    dest.set_grant_status(fl.d1.binding.grant_id, status="active", revision="2")
    r = ex.execute(envelope=fl.envelope(fl.d1), claim_id=claim.claim_id)
    assert r.status == "denied" and effect_ids(dest.path) == [] and dest.claim_state(claim.claim_id) == "issued"
    observe(T, "route B: re-created as revision 2", "prevented", does_not_prove=DNP)


def test_route_b_suspension_then_reinstatement_is_listed(cprt, tmp_path, monkeypatch):
    """Suspension is reversible by its meaning; the issued claim becomes usable again. Listed, not judged."""
    fl = flow(tmp_path, monkeypatch)
    dest, ex = atomic(fl, tmp_path)
    claim = ex.provision_claim(proposal=fl.p, decision=fl.d1, now=fl.NOW)
    dest.set_grant_status(fl.d1.binding.grant_id, status="suspended")
    assert ex.execute(envelope=fl.envelope(fl.d1), claim_id=claim.claim_id).status == "denied"
    dest.set_grant_status(fl.d1.binding.grant_id, status="active")
    assert ex.execute(envelope=fl.envelope(fl.d1), claim_id=claim.claim_id).status == "executed"
    assert effect_ids(dest.path) == [fl.d1.effect_id]
    observe(T, "route B: suspended then reinstated", "not applicable", does_not_prove=DNP,
            detail="suspension is reversible by design; recorded for comparison")


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=SUSPECTED)
def test_route_b_issued_claim_after_recreation(cprt, tmp_path, monkeypatch):
    fl = flow(tmp_path, monkeypatch)
    dest, ex = atomic(fl, tmp_path)
    claim = ex.provision_claim(proposal=fl.p, decision=fl.d1, now=fl.NOW)
    dest.set_grant_status(fl.d1.binding.grant_id, status="revoked")
    if ex.execute(envelope=fl.envelope(fl.d1), claim_id=claim.claim_id).status != "denied":
        pytest.fail("precondition: the revocation itself was not refused")  # not an AssertionError: never hidden by the xfail
    dest.set_grant_status(fl.d1.binding.grant_id, status="active", revision=fl.d1.binding.grant_revision)
    r = ex.execute(envelope=fl.envelope(fl.d1), claim_id=claim.claim_id)
    observe(T, "route B: issued claim, same-revision re-creation",
            "reproduced failure" if effect_ids(dest.path) else "prevented", does_not_prove=DNP, detail={"status": r.status})
    assert r.status == "denied" and effect_ids(dest.path) == []
