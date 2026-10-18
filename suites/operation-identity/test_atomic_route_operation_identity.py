"""R2 (F-5 close): opt-in operation key on the atomic route (AtomicLocalControlPlaneExecutor + atomic destination).

SPDX-License-Identifier: Apache-2.0

Finding (orchestrator PR #106, development/programme-2-gap-report.md F-5): on the atomic route claim 1 commits, the grant is
renewed with a new approval reference, and with a per-grant cap of 2 the renewed claim commits too: two effects for one
operation, even with the Control Plane operation-identity profile on, because the route carried no operation key.

Route: control plane BoundedAuthorizationWorkflow -> runtime AtomicLocalControlPlaneExecutor -> atomic SQLite destination.
Opt-in: executor ``operation_identity=True`` with ``OperationIdentityAtomicAuthorityEffectDestination``; the operation id is
derived from the persisted issuer-approved decision, never passed by the caller. Synthetic fixtures only; no network effects.

Provenance of "expected today" (refusal-template leg e):
  * *_legacy_* tests describe the default path and pass on runtime main d90a2cae (the orchestrator overlay recorded the same
    two effects there: kind "run", orchestrator #106 at Control Plane 128eaa5e, Runtime d90a2cae).
  * every other test describes new opt-in behaviour: no expected-today value; they FAIL on runtime main d90a2cae by design
    (the destination class and executor flag are absent there). Red at the old pin by design.
Legs written out in the tests: (a) the ledger holds no row for the refused effect, read through an independent connection;
(b) a durable failure row names the effect and the code before the refusal is returned; (c) the identical flow with the key
off reaches the destination (control). Leg (d), mutation, is not run: the refusal here is a destination guard and the evidence
row is written by the executor in a separate statement; the test asserts both rows exist rather than mutating either.
"""
from __future__ import annotations

import sqlite3

import pytest

from _oi_flow import Flow

NEW = "opt-in atomic-route operation key (new): fails on runtime main d90a2cae by design"


def _atomic(flow, work, *, identity):
    from engine.atomic_local_control_plane_executor import AtomicLocalControlPlaneExecutor
    if identity:
        from engine.operation_identity_atomic_destination import OperationIdentityAtomicAuthorityEffectDestination as Dest
    else:
        from engine.local_authority_effect import AtomicAuthorityEffectDestination as Dest
    dest = Dest(work / "atomic", clock=lambda: flow.NOW)
    kwargs = {"operation_identity": True} if identity else {}
    return dest, AtomicLocalControlPlaneExecutor(workflow=flow.f, destination=dest, policy=flow.policy, **kwargs)


def _renew(flow, dest, *, identity):
    """Authority-side renewal as the orchestrator overlay models it: revision 2 published, new approval, row moved by the destination."""
    flow.publish_revision("2")
    ctx = flow.r.contexts[flow.tba.PROFILE]
    grant = ctx["grant"]
    old = grant["approval_refs"][0]
    new = old.rsplit("-", 1)[0] + "-2"
    approval = flow.r.approvals[old].model_copy(deep=True)
    approval.approval_ref = new
    flow.r.approvals[new] = approval
    grant["approval_refs"] = [new]
    ra = ctx["runtime_authority"]
    for item in ra["required_inputs"]:
        if item["input_id"] == old:
            item["input_id"] = new
    ra["required_inputs"] = sorted(ra["required_inputs"], key=lambda x: (x["input_type"], x["input_id"]))
    ra["required_inputs_digest"] = flow.cp.commitment(ra["required_inputs"])
    flow.tra.bind_approval(flow.r, flow.f.runtime_authority_profile or flow.cfg)
    if identity:
        flow.f.record_renewal(flow.OPERATION_ID, to_revision="2", written_by=flow.ISSUER, now=flow.NOW)
    dest.set_grant_status(flow.d1.binding.grant_id, status="active", revision="2")
    d2 = flow.f.decide(flow.p, now=flow.NOW)
    assert d2.result == "authorized", d2.reasons
    return d2


def _ledger(dest):
    conn = sqlite3.connect(dest.path)
    try:
        return [r[0] for r in conn.execute("SELECT effect_id FROM effects ORDER BY effect_id")]
    finally:
        conn.close()


def _run_renewal(tmp_path, *, cap, identity, key):
    """Claim 1 commits; the grant is renewed with a new approval; claim 2 is provisioned and executed. Returns the pieces."""
    mp = pytest.MonkeyPatch()
    try:
        flow = Flow(tmp_path, mp, identity=identity, wide=(cap == 2))
        flow.OPERATION_ID = "op-order-100/refund-1"
        dest, executor = _atomic(flow, tmp_path, identity=key)
        claim1 = executor.provision_claim(proposal=flow.p, decision=flow.d1, now=flow.NOW)
        r1 = executor.execute(envelope=flow.envelope(flow.d1), claim_id=claim1.claim_id)
        d2 = _renew(flow, dest, identity=identity)
        claim2 = executor.provision_claim(proposal=flow.p, decision=d2, now=flow.NOW)
        r2 = executor.execute(envelope=flow.envelope(d2), claim_id=claim2.claim_id)
        return flow, dest, executor, (flow.d1, d2), (claim1, claim2), (r1, r2)
    finally:
        mp.undo()


def test_atomic_route_legacy_cap_two_renewal_commits_two_effects_today(tmp_path):
    """Default path (key off, plain destination): the renewed claim commits a second effect for one operation, identity profile on."""
    flow, dest, _, (d1, d2), _, (r1, r2) = _run_renewal(tmp_path, cap=2, identity=True, key=False)
    assert (r1.status, r2.status) == ("executed", "executed")
    assert _ledger(dest) == sorted([d1.effect_id, d2.effect_id])
    assert "operation_effects_v1" not in {r[0] for r in dest._connect().execute("SELECT name FROM sqlite_master")}


def test_atomic_route_legacy_cap_one_is_blocked_only_by_the_budget_today(tmp_path):
    """Default path, cap 1: one effect; the barrier is the shared per-grant budget."""
    flow, dest, _, (d1, _), _, (r1, r2) = _run_renewal(tmp_path, cap=1, identity=True, key=False)
    assert r1.status == "executed" and r2.status == "denied" and "budget exhausted" in r2.error
    assert _ledger(dest) == [d1.effect_id]


def test_atomic_route_operation_key_refuses_the_renewed_claim_at_cap_two(tmp_path):
    """Legs a-c. Key on, cap 2, identity on: claim 2 is refused with operation_already_committed; one effect, durable failure row."""
    flow, dest, _, (d1, d2), (claim1, claim2), (r1, r2) = _run_renewal(tmp_path, cap=2, identity=True, key=True)
    assert r1.status == "executed"
    assert r2.status == "denied" and r2.error == "operation_already_committed" and r2.attempted is False
    assert _ledger(dest) == [d1.effect_id]                                                    # (a) negative, independent read
    assert d2.effect_id not in _ledger(dest)
    [failure] = [x for x in dest.failure_history(d2.effect_id)]                               # (b) durable before the refusal returned
    assert failure["failure_class"] == "authority_hold" and failure["stage"] == "pre_dispatch"
    assert "operation_already_committed" in failure["detail"]
    assert dest.claim_state(claim2.claim_id) == "issued", "the refused claim was not consumed"
    key = (d1.binding.principal, "customer-refunds", flow.OPERATION_ID)
    assert dest.operation_effect(key) == d1.effect_id
    assert dest.budget_state(f"grant:{d1.binding.grant_id}")["used_effects"] == 1


def test_atomic_route_operation_key_does_not_change_the_first_commit(tmp_path):
    """Control (leg c): with the key on, the first claim commits exactly as with it off; the operation row names its effect."""
    mp = pytest.MonkeyPatch()
    try:
        flow = Flow(tmp_path, mp, identity=True, wide=True)
        flow.OPERATION_ID = "op-order-100/refund-1"
        dest, executor = _atomic(flow, tmp_path, identity=True)
        claim = executor.provision_claim(proposal=flow.p, decision=flow.d1, now=flow.NOW)
        r1 = executor.execute(envelope=flow.envelope(flow.d1), claim_id=claim.claim_id)
        assert r1.status == "executed" and r1.acknowledged
        assert _ledger(dest) == [flow.d1.effect_id]
        assert dest.operation_effect((flow.d1.binding.principal, "customer-refunds", flow.OPERATION_ID)) == flow.d1.effect_id
    finally:
        mp.undo()


def test_atomic_route_operation_key_cap_one_still_one_effect(tmp_path):
    """Cap 1 with the key on: still one effect (the budget refuses first; the operation row is not written for the refused claim)."""
    flow, dest, _, (d1, _), _, (r1, r2) = _run_renewal(tmp_path, cap=1, identity=True, key=True)
    assert r1.status == "executed" and r2.status == "denied"
    assert _ledger(dest) == [d1.effect_id]


def test_atomic_route_operation_key_without_the_control_plane_profile_is_refused(tmp_path):
    """Key on but the Control Plane identity profile is off: no operation id can be derived, so nothing commits (never guessed)."""
    mp = pytest.MonkeyPatch()
    try:
        flow = Flow(tmp_path, mp, identity=False, wide=True)
        dest, executor = _atomic(flow, tmp_path, identity=True)
        claim = executor.provision_claim(proposal=flow.p, decision=flow.d1, now=flow.NOW)
        r1 = executor.execute(envelope=flow.envelope(flow.d1), claim_id=claim.claim_id)
        assert r1.status == "denied" and r1.error == "operation_identity_profile_unavailable"
        assert _ledger(dest) == [] and dest.claim_state(claim.claim_id) == "issued"
        assert dest.failure_history(flow.d1.effect_id)[0]["stage"] == "pre_dispatch"
    finally:
        mp.undo()


def test_atomic_route_operation_key_on_a_destination_without_the_capability_is_refused(tmp_path):
    """Key on with the plain atomic destination: refused (it cannot store the key), never silently dropped."""
    from engine.atomic_local_control_plane_executor import AtomicLocalControlPlaneExecutor
    from engine.local_authority_effect import AtomicAuthorityEffectDestination
    mp = pytest.MonkeyPatch()
    try:
        flow = Flow(tmp_path, mp, identity=True, wide=True)
        dest = AtomicAuthorityEffectDestination(tmp_path / "atomic", clock=lambda: flow.NOW)
        executor = AtomicLocalControlPlaneExecutor(workflow=flow.f, destination=dest, policy=flow.policy, operation_identity=True)
        claim = executor.provision_claim(proposal=flow.p, decision=flow.d1, now=flow.NOW)
        r1 = executor.execute(envelope=flow.envelope(flow.d1), claim_id=claim.claim_id)
        assert r1.status == "denied" and r1.error == "operation_identity_capability_unavailable"
        assert _ledger(dest) == []
    finally:
        mp.undo()
