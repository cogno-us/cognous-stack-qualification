"""N4 composed scenarios: opt-in dedupe-ttl/0.1 across control plane and runtime (addendum 101726_B, M4).

SPDX-License-Identifier: Apache-2.0

Route: control plane BoundedAuthorizationWorkflow -> runtime PinnedControlPlaneExecutor -> the runtime's opt-in
``DedupeTtlOperationDestination`` (``engine/dedupe_destination.py``: a destination that stores our operation key for a TTL, forgets it
afterwards, and answers ``in_progress`` for a key it is still processing). Synthetic fixtures only; the destination clock is injected,
nothing sleeps, no network effects, no real provider.

What these prove: a destination that forgets the operation key at its TTL cannot, under the profile, turn a second effect for an
operation that already has an applied effect into a fresh one: the control plane refuses it from its own ledger before dispatch
(``dedupe_operation_effect_applied``); an ``in_progress`` answer leaves the attempt ``unknown`` and no new key is minted
(``dedupe_unresolved_attempt_blocks_new_key``); an unresolved attempt escalates at a deadline inside the key TTL and the row says
whether the destination still remembered the key. What they do not prove: anything about a real provider's TTL (the capability is
declared by the destination, never inferred, and here it is a CI/local aid), that an escalation is ever read by a person, or
cross-host behaviour. Effect-id dedupe never expires: only the operation key has a TTL.

Provenance of "expected today" values (leg e). The ``*_today`` tests were RUN with the TTL destination and the profile absent: the
default path has no dedupe profile, so an expired key lets the second effect land and an ``in_progress`` answer is an ordinary
unknown outcome under which a renewal dispatches a second key. The profile tests describe new opt-in behaviour: there is no
"expected today" value and they FAIL on the pinned mains by design (the profile and the destination are absent there).
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import _refusal_template as T  # noqa: E402
from _oi_flow import OPERATION, Flow  # noqa: E402

PRINCIPAL = "urn:cognous:principal:refund-service"
TTL, HORIZON, DEADLINE = 600, 120, 300
NEW_BEHAVIOUR = "opt-in dedupe-ttl/0.1 (new): no expected-today value; fails on the pinned mains by design"
PROVENANCE_PROFILE = T.Provenance("code-reading", "control plane dedupe.py (applied_under_other_effect, blocks_new_key) and bounded.py "
                                  "(_effect_gate_n4); runtime engine/dedupe_destination.py; " + NEW_BEHAVIOUR)
PROVENANCE_TODAY = T.Provenance("run", "this suite's *_today tests: TTL destination, dedupe profile absent")


class Clock:
    """The destination's own clock (seconds). Independent of the evaluation time so the key can expire without staling inputs."""

    def __init__(self):
        self.now = 1_000_000.0

    def __call__(self):
        return self.now


def dedupe_profile():
    from agent_control_plane.dedupe import DedupeProfile
    return DedupeProfile(dedupe_ttl_seconds=TTL, provider_horizon_seconds=HORIZON, escalation_deadline_seconds=DEADLINE)


def build(work, mp, *, profile=True):
    clock = Clock()

    def factory(path, flow):
        from engine.dedupe_destination import DedupeTtlOperationDestination
        return DedupeTtlOperationDestination(path, dedupe_ttl_seconds=TTL, clock=clock)

    flow = Flow(work, mp, identity=True, dest_factory=factory,
                cfg_update=(lambda f: {"dedupe": dedupe_profile()}) if profile else None)
    flow.clock = clock
    return flow


def enable_profile(flow):
    """Switch the dedupe profile on after the fact (host configuration; the approval commitment is rebound)."""
    cfg = flow.f.runtime_authority_profile.model_copy(update={"dedupe": dedupe_profile()})
    flow.tra.bind_approval(flow.r, cfg)
    flow.f.runtime_authority_profile = cfg.snapshot()


def document(flow):
    return json.loads(flow.f.records.path.read_text(encoding="utf-8"))


def record(record_property, name, adapter_result=None, report=None, text=None):
    record_property("principal", PRINCIPAL)
    record_property(name, T.report_json(adapter_result, report) if adapter_result is not None else text)


# ------------------------------------------------------------------------------------------------ refusal adapter
class ExpiredKeyAdapter(T.Adapter):
    """r1 applied; the destination's key TTL passed; the grant is renewed. The change is turning the profile on; the call is the
    renewed (second-effect) execution. Control: the same call without the change lands the second effect (the value today)."""

    def build(self, work, mp):
        flow = build(work, mp, profile=False)
        assert flow.run(flow.d1).status == "executed"
        flow.clock.now += TTL  # the key is valid while age < TTL, so at exactly the TTL the destination has forgotten it
        flow.publish_revision("2")
        flow.f.record_renewal(OPERATION, to_revision="2", written_by=flow.ISSUER, now=flow.NOW)
        return flow

    def apply_change(self, flow):
        enable_profile(flow)

    def execute(self, flow):
        flow.d2 = flow.f.decide(flow.p, now=flow.NOW)
        assert flow.d2.result == "authorized", flow.d2.reasons
        return flow.run(flow.d2)

    def effect_id(self, flow):
        return flow.renewed_effect_id("2")

    def ledger_effect_ids(self, flow):
        return flow.ledger_effect_ids()

    def refusal_rows(self, flow):
        rows = []
        for r in flow.record().refusals:
            row = r.model_dump(mode="json")
            row = {k: row[k] for k in ("refusal_id", "effect_id", "stage", "reasons")}
            applied = [a.effect_id for a in flow.latest_attempts() if a.status == "acknowledged"]
            row["changed_inputs"] = [{"input_type": "operation", "input_id": OPERATION, "expected_version": "applied_effects=none",
                                      "observed_version": "applied_effects=" + ",".join(sorted(applied))}]
            rows.append(row)
        return rows

    def disable_refusal_writer(self, flow):
        flow.f.records.append_refusal = lambda value: None  # only the evidence row is lost; the gate still refuses
        records = flow.f.records

        def gate_without_refusal_row(attempt, refusal, event):
            records.append_attempt(attempt)
            records.append_check_event(event)
        records.record_gate_refusal = gate_without_refusal_row

    def policy_versions_observed_at_enforcement(self, flow, stage):
        return {}


EXPIRED_KEY = T.RefusalSpec(
    name="expired_destination_key_does_not_make_a_duplicate_fresh",
    reasons=("dedupe_operation_effect_applied",),
    changed_inputs=(T.ChangedInput("operation", OPERATION),),
    provenance=PROVENANCE_PROFILE)


def test_expired_destination_key_does_not_make_a_duplicate_fresh(tmp_path, record_property):
    """Legs a-e via the template. r1 applied; the destination forgot the key at its TTL; the renewed r2 would be a second effect for
    the same operation. With the profile it is refused before dispatch and the ledger keeps one effect."""
    result = T.run_refusal_scenario(ExpiredKeyAdapter(), EXPIRED_KEY, tmp_path / "template", pytest.MonkeyPatch)
    assert result.legs_passed == T.LEGS
    holders = [{"holder_id": OPERATION, "kind": "operation"}, {"holder_id": "urn:cognous:issuance:1", "kind": "mandate"}]
    report = T.classify_holders(holders, [result.refusal_row])
    record(record_property, "n4_" + EXPIRED_KEY.name, result, report)
    assert [h["holder_id"] for h in report["witnessed_refusals"]] == [OPERATION]
    mp = pytest.MonkeyPatch()
    try:
        adapter = ExpiredKeyAdapter()
        flow = adapter.build(tmp_path / "extra", mp)
        adapter.apply_change(flow)
        first = flow.d1.effect_id
        assert adapter.execute(flow).status == "denied"
        assert flow.ledger_effect_ids() == [first], "one effect at the destination: the first"
        assert {x.effect_id for x in flow.latest_attempts()} == {first}, "no attempt was made under the second key"
    finally:
        mp.undo()


def test_a_second_effect_lands_when_the_destination_key_expires_today(tmp_path):
    """Expected today (ran, profile absent): the destination forgot the key, so the renewed effect is accepted as new."""
    PROVENANCE_TODAY.validate()
    mp = pytest.MonkeyPatch()
    try:
        adapter = ExpiredKeyAdapter()
        flow = adapter.build(tmp_path, mp)
        assert adapter.execute(flow).status == "executed"
        assert len(flow.ledger_effect_ids()) == 2 and {x.effect_id for x in flow.latest_attempts()} == {flow.d1.effect_id, flow.d2.effect_id}
        assert "dedupe_escalations" not in document(flow)
    finally:
        mp.undo()


def test_inside_the_ttl_the_destination_itself_dedupes_the_second_effect(tmp_path):
    """Control for the TTL: one second before it expires the destination refuses the renewed effect (definitively, a failed attempt),
    with or without the profile; the control plane's own refusal is what covers the time after."""
    mp = pytest.MonkeyPatch()
    try:
        flow = build(tmp_path, mp, profile=False)
        assert flow.run(flow.d1).status == "executed"
        flow.clock.now += TTL - 1
        flow.publish_revision("2")
        flow.f.record_renewal(OPERATION, to_revision="2", written_by=flow.ISSUER, now=flow.NOW)
        d2 = flow.f.decide(flow.p, now=flow.NOW)
        assert flow.run(d2).status == "failed"
        failed = [a for a in flow.latest_attempts() if a.status == "failed"]
        assert [a.error for a in failed] == ["operation_already_committed"] and len(flow.ledger_effect_ids()) == 1
    finally:
        mp.undo()


# ----------------------------------------------------------------------------- in progress never mints a second key
def lose_first_ack(flow):
    flow.dest.defer_next_commit()  # the destination accepts the request and is still processing it; the acknowledgement is lost
    first = flow.run(flow.d1)
    return first


def renew(flow):
    flow.publish_revision("2")
    flow.f.record_renewal(OPERATION, to_revision="2", written_by=flow.ISSUER, now=flow.NOW)
    d2 = flow.f.decide(flow.p, now=flow.NOW)
    assert d2.result == "authorized", d2.reasons
    return d2


def test_in_progress_never_mints_a_second_key(tmp_path):
    """Legs written out: (a) no second effect at the destination while the first is in progress, (b) the refusal names the
    unresolved first attempt and no attempt carries the second effect id, (c) landing the deferred request later gives exactly one
    effect, (d) with the profile off the same renewal reaches the destination under a second key, (e) provenance below."""
    mp = pytest.MonkeyPatch()
    try:
        flow = build(tmp_path, mp)
        first = lose_first_ack(flow)
        assert first.status in ("unknown", "unresolved"), first.status
        d2 = renew(flow)
        assert flow.run(d2).status == "denied"
        refusal = flow.record().refusals[-1]
        assert refusal.reasons == ["dedupe_unresolved_attempt_blocks_new_key"] and refusal.effect_id == d2.effect_id
        assert {a.effect_id for a in flow.latest_attempts()} == {flow.d1.effect_id}, "no attempt under the second key"
        assert flow.ledger_effect_ids() == []
        assert flow.dest.land()["duplicate"] is False
        assert flow.ledger_effect_ids() == [flow.d1.effect_id], "the deferred first request is the one effect"
    finally:
        mp.undo()


def test_in_progress_then_renewal_dispatches_a_second_key_today(tmp_path):
    """Expected today (ran, profile absent): the destination's in-progress answer is an ordinary unknown outcome, and the renewed
    effect is dispatched under a second key (here the destination holds it as in progress, so it lands nothing yet)."""
    PROVENANCE_TODAY.validate()
    mp = pytest.MonkeyPatch()
    try:
        flow = build(tmp_path, mp, profile=False)
        lose_first_ack(flow)
        d2 = renew(flow)
        flow.run(d2)
        assert {a.effect_id for a in flow.latest_attempts()} == {flow.d1.effect_id, d2.effect_id}
    finally:
        mp.undo()


# ----------------------------------------------------------------------------------------------- escalation deadline
def test_escalation_fires_inside_the_key_ttl_and_says_whether_the_key_was_still_remembered(tmp_path):
    """An unresolved attempt stays unknown through the provider horizon; at the deadline it escalates once, inside the key TTL, with
    the time until which a same-key resubmission would still be deduped. Nothing retries; the attempt is still unknown."""
    from datetime import timedelta
    mp = pytest.MonkeyPatch()
    try:
        flow = build(tmp_path, mp)
        lose_first_ack(flow)
        at = lambda s: flow.NOW + timedelta(seconds=s)  # noqa: E731
        assert [x["state"] for x in flow.f.dedupe_report(now=at(HORIZON - 1), destination=flow.dest)] == ["unknown_until_horizon"]
        assert flow.f.escalation_pass(now=at(DEADLINE - 1), destination=flow.dest) == []
        (row,) = flow.f.escalation_pass(now=at(DEADLINE), destination=flow.dest)
        assert row.fired_inside_key_ttl and row.mode == "destination_ttl" and row.effect_id == flow.d1.effect_id
        assert row.same_key_safe_until == at(TTL).isoformat() and row.reasons == ["attempt_unresolved_past_horizon"]
        assert flow.f.escalation_pass(now=at(DEADLINE + 1), destination=flow.dest) == [], "once per effect"
        assert [a.status for a in flow.latest_attempts()] == ["unknown"] and flow.ledger_effect_ids() == []
    finally:
        mp.undo()


def test_a_late_escalation_is_flagged_after_the_key_ttl(tmp_path):
    from datetime import timedelta
    mp = pytest.MonkeyPatch()
    try:
        flow = build(tmp_path, mp)
        lose_first_ack(flow)
        (row,) = flow.f.escalation_pass(now=flow.NOW + timedelta(seconds=TTL), destination=flow.dest)
        assert not row.fired_inside_key_ttl and row.reasons == ["attempt_unresolved_past_horizon", "escalation_after_key_ttl"]
    finally:
        mp.undo()


def test_same_effect_id_is_deduped_after_the_ttl_because_effect_id_dedupe_never_expires(tmp_path):
    """Only the operation key has a TTL. The same decision resubmitted after the TTL is a duplicate of the same effect, not a new one."""
    mp = pytest.MonkeyPatch()
    try:
        flow = build(tmp_path, mp)
        assert flow.run(flow.d1).status == "executed"
        flow.clock.now += TTL * 10
        again = flow.run(flow.d1)
        assert again.status in ("executed", "reconciled") and flow.ledger_effect_ids() == [flow.d1.effect_id]
    finally:
        mp.undo()
