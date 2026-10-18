"""N1 composed scenarios: opt-in operation-identity/0.1 across control plane and runtime (addendum 101726_B, N1).

SPDX-License-Identifier: Apache-2.0

Every scenario follows the N4 refusal-test template (suites/_refusal_template.py, legs a-e) or, where the scenario is a join
integrity check rather than a refusal, the same five legs written out in the test (marked "legs" in the docstring).

Route: control plane BoundedAuthorizationWorkflow -> runtime PinnedControlPlaneExecutor -> OperationIdentityDestination.
Synthetic fixtures only; no network effects.

What these prove: with the opt-in profile, one operation id is shared by every attempt (renewals included), the destination
refuses a second effect for it, attempts join their licensing check by id, a renewal is accepted only from the grant issuer, and
absent is not "never executed". What they do not prove: tamper evidence (a holder of the record-store key can rewrite rows),
cross-host fencing, or anything about a destination that cannot store our id (it is refused, never silently accepted).

Provenance of "expected today" values (leg e), per test:
  * *_legacy_* tests: ``run`` on pristine control plane main 5f5ae03f and runtime main 10a11d03 (the default path).
  * the profile tests describe new opt-in behaviour: there is no "expected today" value; they FAIL on those mains by design
    (the profile is absent there). ``absent_is_not_never_executed`` is identical today and with the profile (``run`` on both).
  * the one N3-owned assertion (``check_expired_before_dispatch``) was a strict xfail in N1 and is a plain test now that stream N3
    landed the opt-in freshness/0.1 profile (control plane) and the delayed-commit mode (runtime).
"""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import _refusal_template as T  # noqa: E402
from _oi_flow import EXPECTED_TODAY_RUN, OPERATION, RESOLVER_ID, RESOLVER_VERSION, Flow  # noqa: E402

PRINCIPAL = "urn:cognous:principal:refund-service"
NEW_BEHAVIOUR = "opt-in operation-identity/0.1 (new): no expected-today value; fails on the pinned mains by design"
PROVENANCE_PROFILE = T.Provenance("code-reading", "control plane operation_identity.py + bounded.py (_operation_gate, record_renewal, "
                                  "_join_attempt, LocalRefundDestination.apply) and runtime engine/operation_identity_destination.py; " + NEW_BEHAVIOUR)
PROVENANCE_LEGACY = T.Provenance(*EXPECTED_TODAY_RUN)


# ----------------------------------------------------------------------------------------------------- refusal adapter
class OperationAdapter(T.Adapter):
    """scenario: 'commit_stall' (r1 inside the destination), 'check_stall' (r1 between its check and dispatch) or 'self_renewal'.

    The refusal rows are projections of real ledger rows (attempt, decision and renewal rows); the input-version strings are
    built from real values (the operation's committing effect id, the renewal row's outcome and code). Nothing is invented.
    """

    def __init__(self, scenario, stall_seconds=0, freshness=None):
        self.scenario, self.stall_seconds, self.freshness = scenario, stall_seconds, freshness

    def build(self, work, mp):
        return Flow(work, mp, identity=True, freshness=self.freshness)

    def apply_change(self, flow):
        if self.scenario == "self_renewal":
            flow.renewal_writer = flow.p.actor  # the worker, not the issuer, writes the renewal
            return
        hook = {"commit_stall": "commit", "check_stall": "observe"}[self.scenario]

        def while_r1_is_stalled():
            if self.stall_seconds:
                flow.advance_clock(self.stall_seconds)  # r1's check is now older than its class bound
            flow.renew_and_commit_r2()
        flow.dest.pause_at(hook, while_r1_is_stalled)  # the renewal and r2 happen while r1 is stalled

    def execute(self, flow):
        if self.scenario != "self_renewal":
            return flow.run(flow.d1)
        flow.publish_revision("2")
        writer = getattr(flow, "renewal_writer", flow.ISSUER)
        try:
            flow.f.record_renewal(OPERATION, to_revision="2", written_by=writer, now=flow.NOW)
        except PermissionError:
            pass
        d2 = flow.f.decide(flow.p, now=flow.NOW)
        flow.r2 = (d2, flow.run(d2) if d2.result == "authorized" else None)
        return flow.r2

    def effect_id(self, flow):
        return flow.renewed_effect_id("2") if self.scenario == "self_renewal" else flow.d1.effect_id

    def ledger_effect_ids(self, flow):
        return flow.ledger_effect_ids()

    def refusal_rows(self, flow):
        record = flow.record()
        if self.scenario == "self_renewal":
            refused = [x for x in record.operation_renewals if x.outcome == "refused"]
            rows = []
            for d in (x for x in record.decisions if x.result == "hold"):
                codes = list(d.reasons) + [x.refusal_code for x in refused]
                rows.append({"refusal_id": d.decision_id, "effect_id": d.effect_id, "stage": "decision", "reasons": codes,
                             "changed_inputs": [{"input_type": "grant", "input_id": flow.d1.binding.grant_id,
                                                 "expected_version": "revision=2;renewal=accepted_from_grant_issuer",
                                                 "observed_version": ";".join(f"revision={x.to_revision};renewal={x.outcome}:{x.refusal_code}"
                                                                              f";written_by={x.written_by}" for x in refused) or "renewal=none"}]})
            return rows
        committed = flow.dest.operation_effect(
            (flow.d1.binding.principal, "customer-refunds", OPERATION)) if hasattr(flow.dest, "operation_effect") else None
        recorded = [x.model_dump(mode="json") for x in record.refusals]  # effect-time refusal rows, if the control plane wrote any
        return recorded + [{"refusal_id": a.attempt_id, "effect_id": a.effect_id, "stage": "destination_commit", "reasons": [a.error],
                 "changed_inputs": [{"input_type": "operation", "input_id": OPERATION, "expected_version": f"effect_id={a.effect_id}",
                                     "observed_version": f"committed_by_effect_id={committed}"}]}
                for a in flow.latest_attempts() if a.status == "failed" and a.error]

    def disable_refusal_writer(self, flow):
        if self.scenario == "self_renewal":
            # Still refuses (raises), but the refused row is never persisted: only the evidence row is lost.
            from agent_control_plane.operation_identity import CODE_NOT_BY_ISSUER, OperationRenewalRow

            def refuse_without_row(**kw):
                return OperationRenewalRow(renewal_id="unrecorded", operation_id=kw["operation_id"], to_revision=kw["to_revision"],
                                           written_by=kw["written_by"], outcome="refused", refusal_code=CODE_NOT_BY_ISSUER,
                                           recorded_at=kw["recorded_at"])
            flow.f.records.record_renewal = refuse_without_row
        else:
            original = flow.f.records.append_attempt  # the failed-attempt row is the destination-refusal evidence
            flow.f.records.append_attempt = lambda value: None if value.status == "failed" else original(value)
            flow.f.records.append_refusal = lambda value: None  # and any effect-time refusal row
            records = flow.f.records

            def gate_without_evidence(attempt, refusal, event):  # control plane >= F1: the gate refusal is one atomic write
                records.append_check_event(event)  # the failed-attempt and refusal evidence rows are lost
            records.record_gate_refusal = gate_without_evidence

    def policy_versions_observed_at_enforcement(self, flow, stage):
        return {}


def assert_joined_by_id(flow, *, attempts):
    """Every attempt has exactly one join row; operation, attempt and licensing check agree by id (never by time order)."""
    record = flow.record()
    rows = flow.latest_attempts()
    joins = {j.attempt_id: j for j in record.attempt_joins}
    assert len(record.attempt_joins) == len(joins) == len(rows) == attempts
    assert set(joins) == {a.attempt_id for a in rows}
    assert {j.operation_id for j in joins.values()} == {OPERATION}
    opened = {e.check_id: e for e in record.check_events if e.phase == "opened" and e.stage == "effect"}
    checks = {c.check_id: c for c in record.resolution_checks if c.stage == "effect"}
    for j in joins.values():
        assert j.check_id in opened and j.check_id in checks, "join names a check the journal or the resolution rows do not have"
        assert opened[j.check_id].effect_id == j.effect_id
        assert (j.resolver_id, j.resolver_version, j.class_max_age) == (RESOLVER_ID, RESOLVER_VERSION, 60)
        assert j.merged_into is None
    assert len({j.check_id for j in joins.values()}) == attempts, "two attempts share one licensing check"
    return joins, opened


def run_template(scenario, spec, tmp_path, record_property):
    result = T.run_refusal_scenario(OperationAdapter(scenario), spec, tmp_path, pytest.MonkeyPatch)
    assert result.legs_passed == T.LEGS
    record_property("principal", PRINCIPAL)
    holders = [{"holder_id": OPERATION, "kind": "operation"}, {"holder_id": "urn:cognous:issuance:1", "kind": "mandate"}]
    report = T.classify_holders(holders, [result.refusal_row])
    record_property("n1_refusal_template", T.report_json(result, report))
    return result, report


def replay(scenario, tmp_path):
    """A fresh flow driven the same way, for the N1-specific assertions beyond the template legs."""
    adapter = OperationAdapter(scenario)
    mp = pytest.MonkeyPatch()
    try:
        flow = adapter.build(tmp_path, mp)
        adapter.apply_change(flow)
        outcome = adapter.execute(flow)
        return flow, outcome
    finally:
        mp.undo()


# ------------------------------------------------------------------------------------------ delayed_r1_after_renewal_single_effect
DELAYED = T.RefusalSpec(
    name="delayed_r1_after_renewal_single_effect",
    reasons=("operation_already_committed",),
    changed_inputs=(T.ChangedInput("operation", OPERATION),),
    provenance=PROVENANCE_PROFILE)


def test_delayed_r1_after_renewal_single_effect(tmp_path, record_property):
    """Legs a-e via the template. r1 passed its check and is inside the destination; the grant is renewed; r2 commits; r1 lands late."""
    result, report = run_template("commit_stall", DELAYED, tmp_path / "template", record_property)
    # the operation produced the refusal; the mandate was never probed and stays coverage_unknown, never "expired"
    assert [h["holder_id"] for h in report["witnessed_refusals"]] == [OPERATION]
    assert [h["classification"] for h in report["unenumerated_authority_needing_containment"]] == [T.CLASSIFICATION_UNKNOWN]
    flow, outcome = replay("commit_stall", tmp_path / "extra")
    d2, r2 = flow.r2
    assert d2.effect_id != flow.d1.effect_id, "legacy effect_id still changes per grant revision"
    assert flow.ledger_effect_ids() == [d2.effect_id], "one effect at the destination, committed by r2"
    assert r2.status == "executed" and outcome.status == "failed" and outcome.error == "operation_already_committed"
    joins, opened = assert_joined_by_id(flow, attempts=2)
    assert {j.grant_revision for j in joins.values()} == {"1", "2"}
    # The operation id is stable: both attempts, both checks, one operation.
    assert {opened[j.check_id].effect_id for j in joins.values()} == {flow.d1.effect_id, d2.effect_id}


def test_delayed_r1_after_renewal_legacy_two_effects_today(tmp_path):
    """Expected today (ran, default path): a renewed grant changes effect_id and the delayed r1 commits a second effect."""
    PROVENANCE_LEGACY.validate()
    mp = pytest.MonkeyPatch()
    try:
        flow = Flow(tmp_path, mp, identity=False)
        flow.dest.pause_at("commit", flow.renew_and_commit_r2)
        r1 = flow.run(flow.d1)
        d2, r2 = flow.r2
        assert d2.effect_id != flow.d1.effect_id and r1.status == "executed" and r2.status == "executed"
        assert sorted(flow.ledger_effect_ids()) == sorted([flow.d1.effect_id, d2.effect_id]), "two effects for one operation"
        document = flow.f.records.path.read_text()
        assert "attempt_joins" not in document and "operations" not in document, "the default path writes no identity rows"
    finally:
        mp.undo()


# ----------------------------------------------------------------------- renewal_after_stalled_check_single_effect
STALLED = T.RefusalSpec(
    name="renewal_after_stalled_check_single_effect",
    reasons=("operation_already_committed",),
    changed_inputs=(T.ChangedInput("operation", OPERATION),),
    provenance=PROVENANCE_PROFILE)


def test_renewal_after_stalled_check_single_effect(tmp_path, record_property):
    """Legs a-e via the template. r1 stalls between its check and dispatch; the grant is renewed; r2 commits; r1 is released.

    Pass (N1 part): one effect at the destination, both attempts and both checks join to one operation id by id. The attempts
    are appended in the opposite order to the checks, so a time-order join would mispair them.
    N3 part (check_expired_before_dispatch for r1): see the strict xfail below.
    """
    run_template("check_stall", STALLED, tmp_path / "template", record_property)
    flow, outcome = replay("check_stall", tmp_path / "extra")
    d2, r2 = flow.r2
    assert flow.ledger_effect_ids() == [d2.effect_id] and outcome.status == "failed"
    joins, opened = assert_joined_by_id(flow, attempts=2)
    record = flow.record()
    check_order = [e.check_id for e in record.check_events if e.phase == "opened" and e.stage == "effect"]
    first_attempt = {}
    for item in record.attempts:
        first_attempt.setdefault(item.attempt_id, len(first_attempt))
    attempt_order = [a for a, _ in sorted(first_attempt.items(), key=lambda kv: kv[1])]
    by_effect = {j.effect_id: j for j in joins.values()}
    assert check_order == [by_effect[flow.d1.effect_id].check_id, by_effect[d2.effect_id].check_id]  # r1's check opened first
    assert attempt_order == [by_effect[d2.effect_id].attempt_id, by_effect[flow.d1.effect_id].attempt_id]  # r2's attempt first


def test_renewal_after_stalled_check_r1_refused_as_check_expired_before_dispatch(tmp_path):
    """N3 part of the composed scenario (was the N1 strict xfail): past its class bound, r1 must be refused before dispatch, not
    by the destination. Needs the opt-in freshness/0.1 profile.

    The service clock moves 61 s (class bound 60 s) while r1 is stalled; the destination observation is stamped by the checked
    party and stays at r1's check time, so nothing else interferes. Without the profile r1 is dispatched and the destination
    refuses it (operation_already_committed): leg (b) fails because no refusal row carries check_expired_before_dispatch.
    """
    spec = T.RefusalSpec("renewal_after_stalled_check_expired", ("check_expired_before_dispatch",), (), PROVENANCE_PROFILE)
    T.run_refusal_scenario(OperationAdapter("check_stall", stall_seconds=61, freshness={}), spec, tmp_path, pytest.MonkeyPatch)


def test_stalled_check_with_a_live_observation_clock_is_held_for_observation_time_today(tmp_path):
    """Expected today (ran, default path): a r1 stalled past the 5 s clock tolerance is not dispatched, but not because its check
    expired: its own destination observation is then stamped later than its single evaluation time (observation_time_future).
    That is incidental and goes away with a re-read clock; stream N3 owns the real deadline."""
    PROVENANCE_LEGACY.validate()
    mp = pytest.MonkeyPatch()
    try:
        flow = Flow(tmp_path, mp, identity=False, live_observation_clock=True)

        def stall():
            flow.advance_clock(61)
        flow.dest.pause_at("observe", stall)
        result = flow.run(flow.d1)
        assert result.status == "denied" and result.error == "destination observation is not valid for effect dispatch"
        assert flow.ledger_effect_ids() == []
        assert any("observation_time_future" in x.reasons for x in flow.record().reconciliations)
        assert not any(x.reasons and "check_expired_before_dispatch" in x.reasons for x in flow.record().reconciliations)
    finally:
        mp.undo()


# ----------------------------------------------------------------------------------------------- worker_self_renewal_refused
SELF_RENEWAL = T.RefusalSpec(
    name="worker_self_renewal_refused",
    reasons=("renewal_not_written_by_grant_issuer", "operation_renewal_unrecorded"),
    changed_inputs=(T.ChangedInput("grant", "urn:cognous:grant:routine-1"),),
    provenance=PROVENANCE_PROFILE)


def test_worker_self_renewal_refused(tmp_path, record_property):
    """Legs a-e via the template. Revision 2 exists; the worker writes the renewal; it is refused and recorded; r2 is held."""
    run_template("self_renewal", SELF_RENEWAL, tmp_path / "template", record_property)
    flow, (d2, r2) = replay("self_renewal", tmp_path / "extra")
    assert d2.result == "hold" and r2 is None and flow.ledger_effect_ids() == []
    (refused,) = [x for x in flow.record().operation_renewals]
    assert (refused.outcome, refused.written_by, refused.to_revision) == ("refused", flow.p.actor, "2")
    assert not flow.record().attempt_joins and not flow.latest_attempts()


# ----------------------------------------------------------------------------------------------- attempt_joins_check_by_id
def test_attempt_joins_check_by_id(tmp_path, record_property):
    """Legs written out. (a) default path: the journal check, ResolutionCheck and attempt share no id (ran today);
    (b) profile: the join row names operation, attempt and check, and the check id exists in both journal and resolution rows;
    (c) control: the same ids resolve for a normal executed attempt; (d) mutation: the join writer disabled fails (b);
    (e) provenance labels."""
    PROVENANCE_LEGACY.validate(); PROVENANCE_PROFILE.validate()
    mp = pytest.MonkeyPatch()
    try:
        legacy = Flow(tmp_path / "legacy", mp, identity=False)
        legacy.run(legacy.d1)
        rec = legacy.record()
        journal = {e.check_id for e in rec.check_events}
        assert journal and not journal & {c.check_id for c in rec.resolution_checks}, "(a) today: no shared check id"  # (a)

        flow = Flow(tmp_path / "profile", mp, identity=True)
        result = flow.run(flow.d1)
        assert result.status == "executed"
        joins, opened = assert_joined_by_id(flow, attempts=1)  # (b), (c)
        (join,) = joins.values()
        assert join.attempt_id == result.control_plane_evidence["attempt"]["attempt_id"] and join.effect_id == flow.d1.effect_id
        assert join.expected_effective_grant_digest is None

        mutant = Flow(tmp_path / "mutant", mp, identity=True)
        mutant.f.records.append_attempt_join = lambda value: None  # (d) the join writer disabled
        mutant.run(mutant.d1)
        with pytest.raises(AssertionError):
            assert_joined_by_id(mutant, attempts=1)
        record_property("principal", PRINCIPAL)
        record_property("n1_attempt_joins_check_by_id", "legs a-e passed; (a) ran on pristine mains, (b-d) opt-in profile")
    finally:
        mp.undo()


def test_attempt_join_records_the_effective_grant_digest_when_bound(tmp_path):
    """The join carries expected_effective_grant_digest when the approved extension binds one (field already opt-in)."""
    mp = pytest.MonkeyPatch()
    try:
        flow = Flow(tmp_path, mp, identity=True, wide=False, effective_grant=True)
        assert flow.run(flow.d1).status == "executed"
        (join,) = flow.record().attempt_joins
        assert join.expected_effective_grant_digest == flow.digest and join.operation_id == OPERATION
    finally:
        mp.undo()


# ---------------------------------------------------------------------------------------- absent_is_not_never_executed
def test_absent_is_not_never_executed(tmp_path, record_property):
    """Legs written out; identical with and without the profile (ran on both).

    r1's acknowledgement is lost and its commit has not landed, so an observation says absent. A retry must not be dispatched,
    the reconciliation must record observed_absent with retry_eligible False (never safe_to_retry), and when the first commit
    lands there is exactly one effect: absent was not 'never executed'.
    (a) the retry adds no ledger row while absent; (b) the retained rows name the effect id, the unknown attempt and the
    observed_absent / not-retry-eligible reconciliation; (c) control: after a normal acknowledged attempt a re-execute
    reconciles as applied with no new effect; (d) mutation: hiding the prior attempt from the retry makes it dispatch, failing (a);
    (e) provenance."""
    provenance = T.Provenance("run", "control plane main 5f5ae03f + runtime main 10a11d03 default path and this branch's profile path; this test")
    provenance.validate()
    for identity in (False, True):
        label = "profile" if identity else "default"
        mp = pytest.MonkeyPatch()
        try:
            flow = Flow(tmp_path / label / "refused", mp, identity=identity)
            flow.dest.defer_next_commit()
            first = flow.run(flow.d1)
            assert first.status == "unknown" and not first.acknowledged
            effect_id = flow.d1.effect_id
            T.check_negative(_Adapter(), flow, effect_id)
            retry = flow.run(flow.d1)  # (a) the retry must not dispatch while the first commit is outstanding
            assert retry.status == "denied" and "does not establish retry eligibility" in retry.error
            T.check_negative(_Adapter(), flow, effect_id)
            rec = flow.record()
            absent = [x for x in rec.reconciliations if x.effect_id == effect_id and x.result == "observed_absent"]
            assert absent and all(x.retry_eligible is False for x in absent), "(b) observed_absent is retained and not retry eligible"
            assert not [x for x in rec.reconciliations if x.result == "safe_to_retry"]
            unknown = [a for a in flow.latest_attempts() if a.effect_id == effect_id and a.status == "unknown"]
            assert len(unknown) == 1 and len(flow.latest_attempts()) == 1, "(b) one unknown attempt and no replacement attempt"
            flow.dest.land()  # the provider processed the first commit late
            assert flow.ledger_effect_ids() == [effect_id], "one effect: absent was not 'never executed'"
            again = flow.executor.reconcile(flow.envelope(flow.d1), now=flow.NOW)
            assert again.result == "applied" and again.retry_eligible is False

            control = Flow(tmp_path / label / "control", mp, identity=identity)  # (c)
            assert control.run(control.d1).status == "executed"
            assert control.run(control.d1).status == "reconciled" and control.ledger_effect_ids() == [control.d1.effect_id]

            mutant = Flow(tmp_path / label / "mutant", mp, identity=identity)  # (d)
            mutant.dest.defer_next_commit()
            mutant.run(mutant.d1)
            real_load = mutant.f.records.load
            mutant.f.records.load = lambda: _without_attempts(real_load())  # the prior attempt is hidden: absence read as 'never executed'
            mutant.run(mutant.d1)
            assert mutant.ledger_effect_ids() == [mutant.d1.effect_id], "mutant dispatched a retry while absent"
            with pytest.raises(T.RefusalTemplateFailure) as caught:
                T.check_negative(_Adapter(), mutant, mutant.d1.effect_id)
            assert caught.value.leg == "a"
        finally:
            mp.undo()
    record_property("principal", PRINCIPAL)
    record_property("n1_absent_is_not_never_executed", "legs a-e passed with and without the profile (ran)")


class _Adapter(T.Adapter):
    def ledger_effect_ids(self, flow):
        return flow.ledger_effect_ids()


def _without_attempts(record):
    return record.model_copy(update={"attempts": []})
