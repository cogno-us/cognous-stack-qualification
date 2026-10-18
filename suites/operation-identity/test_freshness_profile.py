"""N3 composed scenarios: opt-in freshness/0.1 across control plane and runtime (addendum 101726_B, N3).

SPDX-License-Identifier: Apache-2.0

Every scenario follows the N4 refusal-test template (suites/_refusal_template.py, legs a-e) or, where the scenario is a report or
a timestamp property rather than a refusal, the same five legs written out in the test (marked "legs" in the docstring).

Route: control plane BoundedAuthorizationWorkflow -> runtime PinnedControlPlaneExecutor -> the runtime's opt-in delayed-commit
destination. Synthetic fixtures only; no network effects.

What these prove: with the opt-in profile, journal events are stamped at write by the service clock (evaluation time kept as its
own field), a check past its class age bound is refused immediately before dispatch, a live check past its deadline is reported
overdue without being closed, a replayed status response is rejected where the resolver echoes the reader's nonce, and an
outage extension of an age bound counts only with a recorded signer from the rule-revision signer set. What they do not prove:
tamper evidence (a holder of the record-store key can rewrite rows), cross-host fencing (flock is same-host), that a deadline
check closes the window between check and commit (it narrows it), or anything about a resolver that cannot echo a nonce (its
ages are labelled source-asserted, never nonce-bound).

Provenance of "expected today" values (leg e), per test. All are ``run`` unless marked: the ``*_today`` tests and the default-path
legs were RUN against pristine control plane main 83b49b5 and runtime main 63a7c0fe, with only the new
``engine/delayed_commit_destination.py`` added to the runtime (the mode changes no existing path; the suite needs a destination
that can stall). The profile tests describe new opt-in behaviour: there is no "expected today" value, and they FAIL on those mains
by design (the profile is absent). ``superseded_owner_journal_write_refused`` is a regression guard whose default-path half
passes today (run) and whose profile half guards the new ``expired`` phase against opening a hole.
"""
from __future__ import annotations

import json
import pathlib
import sys
import threading
from datetime import timedelta

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import _refusal_template as T  # noqa: E402
from _oi_flow import Flow  # noqa: E402

PRINCIPAL = "urn:cognous:principal:refund-service"
REQUESTER, EXT_SIGNER, POLICY_SIGNER = ("urn:cognous:principal:outage-requester", "urn:cognous:principal:outage-signer",
                                        "urn:cognous:principal:policy-signer")
NEW_BEHAVIOUR = "opt-in freshness/0.1 (new): no expected-today value; fails on the pinned mains by design"
PROVENANCE_PROFILE = T.Provenance("code-reading", "control plane freshness.py + bounded.py (_resolve_journal, _expired_before_dispatch, "
                                  "recovery_pass, _read_via_resolver, _class_age_bound) and runtime engine/delayed_commit_destination.py; "
                                  + NEW_BEHAVIOUR)
PROVENANCE_TODAY = T.Provenance("run", "control plane main 83b49b5 and runtime main 63a7c0fe (plus engine/delayed_commit_destination.py "
                                "only), pristine checkouts, this suite's default-path legs and *_today tests")


def record(record_property, name, adapter_result=None, report=None, text=None):
    record_property("principal", PRINCIPAL)
    record_property(name, T.report_json(adapter_result, report) if adapter_result is not None else text)


def run_template(adapter, spec, tmp_path, record_property, holder):
    result = T.run_refusal_scenario(adapter, spec, tmp_path, pytest.MonkeyPatch)
    assert result.legs_passed == T.LEGS
    holders = [{"holder_id": holder, "kind": "grant"}, {"holder_id": "urn:cognous:issuance:1", "kind": "mandate"}]
    report = T.classify_holders(holders, [result.refusal_row])
    record(record_property, "n3_" + spec.name, result, report)
    return result, report


# ---------------------------------------------------------------------------------------------------------- adapter
GRANT = "urn:cognous:grant:routine-1"


def adopt_fixture_policy(flow, signers):
    """Configure the N2 rule-revision signer set (the age extension reuses it) and adopt the fixture policy so decisions pass."""
    from agent_control_plane.rule_revision import RuleRevision, RuleRevisionProfile, append_rule_revision
    from tests.test_bounded_authorization import POLICY_REF
    digest = flow.cp.commitment({"policy": "v1"})
    flow.r.policies[POLICY_REF].digest = digest
    flow.f.rule_revision_profile = RuleRevisionProfile(signers=list(signers))
    append_rule_revision(flow.f.records, flow.f.rule_revision_profile, RuleRevision(
        revision_id="adopt-1", rule_kind="policy", rule_ref=POLICY_REF, from_digest=None, to_digest=digest, reviser=REQUESTER,
        signer=POLICY_SIGNER, authority_ref="synthetic-authority:1", reason="synthetic", recorded_at=flow.NOW.isoformat()))


def request_extension(flow, **override):
    values = dict(class_id="synthetic-irreversible", to_max_age_seconds=200, not_before=flow.NOW.isoformat(),
                  expires_at=(flow.NOW + timedelta(hours=1)).isoformat(), outage_ref="outage-1", requested_by=REQUESTER,
                  signer=EXT_SIGNER, authority_ref="urn:cognous:authority:outage-1", now=flow.NOW)
    values.update(override)
    return flow.f.record_age_extension(**values)


def setup_extension(flow):
    adopt_fixture_policy(flow, (EXT_SIGNER, POLICY_SIGNER))
    next(iter(flow.r.statuses.values())).observed_at = (flow.NOW - timedelta(seconds=70)).isoformat()  # older than the 60 s bound
    flow.extension = request_extension(flow)


def setup_tape(flow):
    """Record every echoed read, so a response (with its nonce) can be replayed into a later check."""
    flow.tape, original = {}, flow.r.nonce_read
    flow.nonce_read_original = original

    def taping(nonce, method, *args):
        out = original(nonce, method, *args)
        flow.tape[method] = out
        return out
    flow.r.nonce_read = taping


class FreshnessAdapter(T.Adapter):
    """scenario: 'stall' (r1 stalls between check and dispatch past the class bound), 'replay' (the grant status response is a
    replay of an earlier one, nonce included) or 'extension_withdrawn' (the recorded extension's signer loses authority).

    The refusal rows are projections of real ledger rows (EffectTimeRefusal, the age extension row); the input-version strings are
    built from real values. Nothing is invented.
    """

    def __init__(self, scenario):
        self.scenario = scenario

    def build(self, work, mp):
        if self.scenario == "stall":
            return Flow(work, mp, identity=False, freshness={})
        if self.scenario == "replay":
            return Flow(work, mp, identity=False, freshness={}, echo_nonce=True, setup=setup_tape)
        return Flow(work, mp, identity=False, freshness={"max_age_extension_seconds": 300}, setup=setup_extension)

    def apply_change(self, flow):
        if self.scenario == "stall":
            flow.dest.pause_at("observe", lambda: flow.advance_clock(61))  # r1's check is now older than its class bound
        elif self.scenario == "replay":
            def replaying(nonce, method, *args):
                if method == "grant_status":
                    return flow.tape["grant_status"]  # the old record and its old echoed nonce
                return flow.nonce_read_original(nonce, method, *args)
            flow.r.nonce_read = replaying
        else:
            from agent_control_plane.rule_revision import RuleRevisionProfile
            flow.f.rule_revision_profile = RuleRevisionProfile(signers=[POLICY_SIGNER])  # the extension signer is withdrawn

    def execute(self, flow):
        return flow.run(flow.d1)

    def effect_id(self, flow):
        return flow.d1.effect_id

    def ledger_effect_ids(self, flow):
        return flow.ledger_effect_ids()

    def refusal_rows(self, flow):
        record = flow.record()
        rows = []
        for r in record.refusals:
            row = r.model_dump(mode="json")
            row = {k: row[k] for k in ("refusal_id", "effect_id", "stage", "reasons", "changed_inputs")}
            if self.scenario == "stall" and r.deadline:
                row["changed_inputs"] = [{"input_type": "clock", "input_id": "service_clock",
                                          "expected_version": f"deadline={r.deadline}",
                                          "observed_version": f"service_time={r.recorded_at}"}]
            if self.scenario == "extension_withdrawn" and record.age_extensions:
                ext = record.age_extensions[0]
                grant = next(x for x in r.resolution_inputs if x.input_type == "grant")
                defects = [x for x in r.reasons if x.startswith("age_extension_")]
                row["changed_inputs"] = [{
                    "input_type": "grant", "input_id": grant.input_id,
                    "expected_version": f"max_age_seconds={ext.to_max_age_seconds};extension_id={ext.extension_id};signer={ext.signer}",
                    "observed_version": f"observed_at={grant.observed['observed_at']};extension_counts=false;defects={','.join(defects)}"}]
            rows.append(row)
        return rows

    def disable_refusal_writer(self, flow):
        flow.f.records.append_refusal = lambda value: None  # only the evidence row is lost; the refusal still raises
        records = flow.f.records

        def gate_without_refusal_row(attempt, refusal, event):  # control plane >= F1: the gate refusal is one atomic write
            records.append_attempt(attempt)
            records.append_check_event(event)
        records.record_gate_refusal = gate_without_refusal_row

    def policy_versions_observed_at_enforcement(self, flow, stage):
        return {}


# ------------------------------------------------------------------------------- stalled_check_past_class_age_refused_at_dispatch
STALLED = T.RefusalSpec(
    name="stalled_check_past_class_age_refused_at_dispatch",
    reasons=("check_expired_before_dispatch",),
    changed_inputs=(T.ChangedInput("clock", "service_clock"),),
    provenance=PROVENANCE_PROFILE)


def test_stalled_check_past_class_age_refused_at_dispatch(tmp_path, record_property):
    """Legs a-e via the template. r1 passes its effect check, then stalls 61 s (class bound 60 s) before dispatch; the service
    clock re-read immediately before ``destination.apply`` is past the deadline fixed at opening, so r1 is refused, its check is
    closed (``expired``) and nothing reaches the destination. The destination observation is stamped by the checked party and
    stays at r1's check time, so the observation-time rules cannot interfere (see the live-clock test below)."""
    run_template(FreshnessAdapter("stall"), STALLED, tmp_path / "template", record_property, GRANT)
    mp = pytest.MonkeyPatch()
    try:
        flow = FreshnessAdapter("stall").build(tmp_path / "extra", mp)
        FreshnessAdapter("stall").apply_change(flow)
        result = flow.run(flow.d1)
        assert result.status == "denied"
        record_ = flow.record()
        events = [e for e in record_.check_events if e.stage == "effect"]
        assert [e.phase for e in events][-2:] == ["completed", "expired"], "the check is closed, not left licensed"
        assert events[-1].reasons == ["check_expired_before_dispatch"] and events[0].deadline and events[0].age_bound_seconds == 60
        assert flow.ledger_effect_ids() == [] and "check_expired_before_dispatch" in result.error
        (last,) = [a for a in flow.latest_attempts()]
        assert (last.status, last.error) == ("failed", "check_expired_before_dispatch")
        # the refusal does not poison a retry: a fresh check opens a fresh deadline
        flow.dest._pauses.clear()
        flow.advance_clock(0)
        retry = flow.run(flow.d1)
        assert retry.status == "executed" and flow.ledger_effect_ids() == [flow.d1.effect_id]
    finally:
        mp.undo()


def test_stalled_check_past_class_age_is_dispatched_today(tmp_path):
    """Expected today (ran, default path): a r1 stalled 61 s past its 60 s class bound, with the destination observation stamped
    by the checked party, still reaches the destination: nothing re-reads the clock after validation."""
    PROVENANCE_TODAY.validate()
    mp = pytest.MonkeyPatch()
    try:
        flow = Flow(tmp_path, mp, identity=False)
        flow.dest.pause_at("observe", lambda: flow.advance_clock(61))
        result = flow.run(flow.d1)
        assert result.status == "executed" and flow.ledger_effect_ids() == [flow.d1.effect_id]
        assert not flow.record().refusals
    finally:
        mp.undo()


def test_stalled_check_with_a_live_observation_clock_is_refused_at_dispatch_not_for_observation_time(tmp_path):
    """The observation clock is decoupled from the evaluation pass. Without the profile (the N1 test
    ``stalled_check_with_a_live_observation_clock_is_held_for_observation_time_today``, ran) a live observation clock makes the
    stalled r1 a hold for ``observation_time_future``; with the profile the same stall reaches the deadline gate and is refused as
    ``check_expired_before_dispatch``. Nothing reaches the destination."""
    PROVENANCE_PROFILE.validate()
    mp = pytest.MonkeyPatch()
    try:
        flow = Flow(tmp_path, mp, identity=False, live_observation_clock=True, freshness={})
        flow.dest.pause_at("observe", lambda: flow.advance_clock(61))
        result = flow.run(flow.d1)
        record_ = flow.record()
        assert result.status == "denied" and "check_expired_before_dispatch" in result.error and flow.ledger_effect_ids() == []
        assert any("check_expired_before_dispatch" in x.reasons for x in record_.refusals)
        assert not any("observation_time_future" in x.reasons for x in record_.reconciliations)
    finally:
        mp.undo()


# --------------------------------------------------------------------------------------- journal_timestamps_reflect_wall_time
SLOW_READ_SECONDS = 4  # inside the 5 s clock tolerance, so the later reads stay valid


def decide_with_a_slow_read(work, mp, *, freshness, restamp=False):
    """A decision whose first resolver read takes SLOW_READ_SECONDS of service-clock time. Returns (flow, decision, t0)."""
    flow = Flow(work, mp, identity=False, freshness=freshness)
    t0, clock = flow.NOW, {"now": flow.NOW}
    mp.setattr(flow.cp, "_now", lambda: clock["now"])
    original = flow.r.identity_status

    def slow(*args):
        out = original(*args)
        clock["now"] = clock["now"] + timedelta(seconds=SLOW_READ_SECONDS)
        return out
    flow.r.identity_status = slow
    if restamp:  # mutation: the journal writer stamps the evaluation time again (the legacy behaviour)
        append = flow.f.records.append_check_event
        flow.f.records.append_check_event = lambda event: append(event.model_copy(update={"recorded_at": t0.isoformat()}))
    return flow, flow.f.decide(flow.p, now=t0), t0


def journal(flow):
    return [e for e in flow.record().check_events if e.stage == "decision"]


def test_journal_timestamps_reflect_wall_time(tmp_path, record_property):
    """Legs written out. (a) default path: every journal event of a check whose reads took 4 s reuses the evaluation time
    (identical timestamps, ran); (b) profile: recorded_at follows the service clock write by write, evaluated_at stays the one
    evaluation pass, and the completed event is stamped 4 s after the opening; (c) control: with no wall time elapsing recorded_at
    equals evaluated_at (identical is then correct); (d) mutation: a journal writer that stamps the evaluation time fails (b);
    (e) provenance labels."""
    PROVENANCE_TODAY.validate(), PROVENANCE_PROFILE.validate()
    mp = pytest.MonkeyPatch()
    try:
        flow, d, t0 = decide_with_a_slow_read(tmp_path / "default", mp, freshness=None)
        assert d.result == "authorized", d.reasons
        stamps = {e.recorded_at for e in journal(flow)}
        assert stamps == {t0.isoformat()}, "(a) today: one timestamp for every event despite 4 s of wall time"  # (a)

        def assert_wall_time(flow, t0):
            events = journal(flow)
            recorded = [e.recorded_at for e in events]
            assert recorded == sorted(recorded) and len(set(recorded)) > 1, f"recorded_at did not follow the clock: {recorded}"
            assert events[0].phase == "opened" and events[0].recorded_at == t0.isoformat()
            assert events[-1].phase == "completed" and events[-1].recorded_at == (t0 + timedelta(seconds=SLOW_READ_SECONDS)).isoformat()
            assert {e.evaluated_at for e in events} == {t0.isoformat()}

        flow, d, t0 = decide_with_a_slow_read(tmp_path / "profile", mp, freshness={})
        assert d.result == "authorized", d.reasons
        assert_wall_time(flow, t0)  # (b)
        assert d.evaluated_at == t0.isoformat() and d.recorded_at >= journal(flow)[-1].recorded_at

        control = Flow(tmp_path / "control", mp, identity=False, freshness={})  # (c) no slow read, no clock movement
        control.f.decide(control.p, now=control.NOW)
        assert {e.recorded_at for e in journal(control)} == {e.evaluated_at for e in journal(control)} == {control.NOW.isoformat()}

        flow, d, t0 = decide_with_a_slow_read(tmp_path / "mutant", mp, freshness={}, restamp=True)  # (d)
        with pytest.raises(AssertionError):
            assert_wall_time(flow, t0)
        record(record_property, "n3_journal_timestamps_reflect_wall_time",
               text="legs a-e passed; (a) ran on pristine mains, (b-d) opt-in profile")
    finally:
        mp.undo()


# ----------------------------------------------------------------------------------- live_overdue_check_reported_not_closed
def open_check_ids(flow):
    return [e.check_id for e in flow.record().check_events if e.phase == "opened" and e.stage == "decision"]


def hold_a_live_check_open(flow):
    """Start a decision whose grant read blocks: its process is alive and holds the check lease. Returns (thread, release, check_id)."""
    before = set(open_check_ids(flow))
    release, started = threading.Event(), threading.Event()
    original = flow.r.grant_status

    def blocked(ref):
        started.set()
        release.wait(30)
        return original(ref)
    flow.r.grant_status = blocked
    thread = threading.Thread(target=lambda: flow.f.decide(flow.p, now=flow.NOW), daemon=True)
    thread.start()
    assert started.wait(15), "the stalled check never started"
    (check_id,) = set(open_check_ids(flow)) - before
    return thread, release, check_id


def test_live_overdue_check_reported_not_closed(tmp_path, record_property):
    """Legs written out. (a) default path: a live check stalled past the class bound is skipped by recovery and nothing marks it
    (ran); (b) profile: the recovery pass reports ``check_overdue`` for it, writes a non-terminal ``overdue`` event once, and does
    not close it (the process is alive: it finishes its own check afterwards); (c) control: a live check within its deadline is
    not reported, and an abandoned check (dead lease) past its deadline is closed ``check_interrupted``, not reported overdue;
    (d) mutation: with the deadline writer disabled at opening the stalled check is not reported, failing (b); (e) provenance."""
    PROVENANCE_TODAY.validate(), PROVENANCE_PROFILE.validate()
    mp = pytest.MonkeyPatch()
    try:
        legacy = Flow(tmp_path / "default", mp, identity=False)
        thread, release, stalled = hold_a_live_check_open(legacy)
        try:
            legacy.advance_clock(61)
            assert legacy.f.records.recover_interrupted_checks() == 0, "(a) today: the live stalled check is skipped"  # (a)
            assert {e.phase for e in legacy.record().check_events if e.check_id == stalled} <= {"opened", "input"}
            assert not any(e.phase == "overdue" for e in legacy.record().check_events)
        finally:
            release.set(), thread.join(30)

        def overdue_flow(label, *, sabotage=False):
            flow = Flow(tmp_path / label, mp, identity=False, freshness={})
            if sabotage:
                flow.f._class_age_bound = lambda action_id, now: (None, None, [])  # the deadline is never fixed at opening
            thread, release, check_id = hold_a_live_check_open(flow)
            flow.advance_clock(61)
            return flow, thread, release, check_id

        flow, thread, release, check_id = overdue_flow("profile")
        try:
            report = flow.f.records.recovery_pass(trigger="manual")  # (b)
            assert [x["check_id"] for x in report.overdue] == [check_id] and report.overdue[0]["reasons"] == ["check_overdue"]
            assert report.interrupted == [] and report.oldest_open_age_seconds >= 61
            phases = [e.phase for e in flow.record().check_events if e.check_id == check_id]
            assert "overdue" in phases and not {"interrupted", "completed"} & set(phases), "reported, not closed"
            flow.f.records.recovery_pass()
            assert [e.phase for e in flow.record().check_events if e.check_id == check_id].count("overdue") == 1
        finally:
            release.set(), thread.join(30)
        assert [e.phase for e in flow.record().check_events if e.check_id == check_id][-1] == "completed", "the live owner finishes"

        from agent_control_plane.bounded import CheckEvent, _process_owner
        control = Flow(tmp_path / "control", mp, identity=False, freshness={})  # (c)
        deadline = (control.NOW + timedelta(seconds=60)).isoformat()
        for cid in ("live-within", "abandoned"):
            control.f.records.append_check_event(CheckEvent(
                check_id=cid, phase="opened", stage="effect", recorded_at=control.NOW.isoformat(), owner=_process_owner(),
                proposal_commitment=control.cp.commitment({}), deadline=deadline))
        with control.f.records.check_lease("live-within"):
            control.advance_clock(30)
            within = control.f.records.recovery_pass()
            assert within.overdue == [] and "live-within" in within.open_within_deadline and within.interrupted == ["abandoned"]
            control.advance_clock(1000)
            assert [x["check_id"] for x in control.f.records.recovery_pass().overdue] == ["live-within"]
        ended = [e for e in control.record().check_events if e.check_id == "abandoned"][-1]
        assert (ended.phase, ended.reasons) == ("interrupted", ["check_interrupted"])

        flow, thread, release, _ = overdue_flow("mutant", sabotage=True)  # (d)
        try:
            assert flow.f.records.recovery_pass().overdue == [], "mutant: nothing reported, so (b) would fail"
        finally:
            release.set(), thread.join(30)
        record(record_property, "n3_live_overdue_check_reported_not_closed",
               text="legs a-e passed; (a) ran on pristine mains, (b-d) opt-in profile")
    finally:
        mp.undo()


# ----------------------------------------------------------------------------- superseded_owner_journal_write_refused
SUPERSEDED = T.RefusalSpec(
    name="superseded_owner_journal_write_refused",
    reasons=("check_interrupted",),
    changed_inputs=(T.ChangedInput("check", "effect-check"),),
    provenance=PROVENANCE_TODAY)


class SupersededAdapter(T.Adapter):
    """r1's check is closed ``interrupted`` by a recovery pass while r1's resolver read is still in flight (a lost host: same-host
    flock cannot represent it, so the liveness probe is forced to "dead" for that one pass). r1's next journal write is the
    superseded owner's late write and must be refused: no completed event, no decision, no attempt, no effect.

    The refusal row is a projection of the real ``interrupted`` journal row (it names the effect id and the failed check); the late
    write's refusal is the raised ``ValueError``, captured as ``flow.late_write_error``. The mutation hides the interrupted row from
    the reader (the evidence); the guard itself, which reads the document, still refuses."""

    def __init__(self, freshness):
        self.freshness = freshness

    def build(self, work, mp):
        flow = Flow(work, mp, identity=False, freshness=self.freshness)
        flow.late_write_error = None
        return flow

    def apply_change(self, flow):
        original = flow.r.identity_status
        fired = []

        def supersede_then_read(*args):
            if not fired:
                fired.append(True)
                records = flow.f.records
                records._check_is_live = lambda check_id: False  # the host is gone: the lease is not visible
                try:
                    assert records.recover_interrupted_checks() == 1
                finally:
                    del records._check_is_live
            return original(*args)
        flow.r.identity_status = supersede_then_read

    def execute(self, flow):
        try:
            return flow.run(flow.d1)
        except ValueError as exc:
            flow.late_write_error = str(exc)
            return None

    def effect_id(self, flow):
        return flow.d1.effect_id

    def ledger_effect_ids(self, flow):
        return flow.ledger_effect_ids()

    def refusal_rows(self, flow):
        events = [e for e in flow.record().check_events if e.phase in {"opened", "interrupted"} and e.stage == "effect"]
        rows = []
        for ended in (e for e in events if e.phase == "interrupted"):
            opened = next(e for e in events if e.phase == "opened" and e.check_id == ended.check_id)
            rows.append({"refusal_id": ended.check_id, "effect_id": ended.effect_id, "stage": "journal_write",
                         "reasons": list(ended.reasons),
                         "changed_inputs": [{"input_type": "check", "input_id": "effect-check",
                                             "expected_version": f"owner={opened.owner['token']};phase=open",
                                             "observed_version": f"owner=recovery;phase=interrupted;recorded_at={ended.recorded_at}"}]})
        return rows

    def disable_refusal_writer(self, flow):
        load = flow.f.records.load
        flow.f.records.load = lambda: _without_interrupted(load())  # the evidence is hidden; the document (and the guard) is not

    def policy_versions_observed_at_enforcement(self, flow, stage):
        return {}


def _without_interrupted(record):
    return record.model_copy(update={"check_events": [e for e in record.check_events if e.phase != "interrupted"]})


@pytest.mark.parametrize("freshness", [None, {}], ids=["default_path_today", "freshness_profile"])
def test_superseded_owner_journal_write_refused(tmp_path, record_property, freshness):
    """Legs a-e via the template (regression guard). Expected today: refused (ran, default path). With the freshness profile the
    new ``expired`` phase must not open a hole: the superseded owner is still refused."""
    adapter = SupersededAdapter(freshness)
    result, report = run_template(adapter, SUPERSEDED, tmp_path / "template", record_property, GRANT)
    mp = pytest.MonkeyPatch()
    try:
        flow = adapter.build(tmp_path / "extra", mp)
        adapter.apply_change(flow)
        assert adapter.execute(flow) is None and flow.late_write_error == "check already closed"
        record_ = flow.record()
        effect_check = [e for e in record_.check_events if e.stage == "effect"]
        phases = [e.phase for e in effect_check]
        assert phases[0] == "opened" and phases[-1] == "interrupted" and "completed" not in phases and "expired" not in phases
        assert len(record_.decisions) == 1 and not record_.attempts and flow.ledger_effect_ids() == []
        if freshness is not None:  # the new phase cannot be written by the superseded owner either
            from agent_control_plane.bounded import CheckEvent
            opening = next(e for e in effect_check if e.phase == "opened")
            with pytest.raises(ValueError, match="check already closed"):
                flow.f.records.append_check_event(CheckEvent.model_validate(
                    dict(opening.model_dump(mode="json"), phase="expired", reasons=["check_expired_before_dispatch"])))
    finally:
        mp.undo()


# ------------------------------------------------------------------------------------- status_with_replayed_nonce_rejected
REPLAY = T.RefusalSpec(
    name="status_with_replayed_nonce_rejected",
    reasons=("status_nonce_mismatch",),
    changed_inputs=(T.ChangedInput("grant", GRANT),),
    provenance=PROVENANCE_PROFILE)


def test_status_with_replayed_nonce_rejected(tmp_path, record_property):
    """Legs a-e via the template. A resolver that supports the nonce echoes the reader's nonce, so each read is bound to its check
    (``age_basis: nonce_bound``). At effect time the grant status is a replay of an earlier response, including its old echoed
    nonce: the read is rejected (``status_nonce_mismatch``), nothing is dispatched, and both nonces are retained in the refusal."""
    run_template(FreshnessAdapter("replay"), REPLAY, tmp_path / "template", record_property, GRANT)
    adapter = FreshnessAdapter("replay")
    mp = pytest.MonkeyPatch()
    try:
        flow = adapter.build(tmp_path / "extra", mp)
        decision_bases = {i.input_type: i.age_basis for c in flow.record().resolution_checks for i in c.inputs}
        assert decision_bases["grant"] == decision_bases["identity"] == "nonce_bound" and decision_bases["manifest"] is None
        adapter.apply_change(flow)
        result = adapter.execute(flow)
        assert result.status == "denied" and flow.ledger_effect_ids() == [] and not flow.latest_attempts()
        (row,) = flow.record().refusals
        grant = next(x for x in row.resolution_inputs if x.input_type == "grant")
        assert grant.read_state == "nonce_mismatch" and grant.age_basis == "source_asserted"
        assert grant.expected["nonce"] != grant.observed["nonce"]
        opened = [e for e in flow.record().check_events if e.phase == "opened" and e.stage == "effect"]
        assert opened[-1].nonce == grant.expected["nonce"], "the nonce the reader sent is the one in the journal"
    finally:
        mp.undo()


def test_replayed_status_response_is_accepted_today(tmp_path):
    """Expected today (ran, default path): a replayed grant status response is indistinguishable from a fresh one: r1 executes,
    and no input carries an age basis and no check carries a nonce."""
    PROVENANCE_TODAY.validate()
    mp = pytest.MonkeyPatch()
    try:
        flow = Flow(tmp_path, mp, identity=False)
        stale_copy = next(iter(flow.r.statuses.values())).model_copy(deep=True)
        flow.r.grant_status = lambda ref: stale_copy  # an earlier recorded response served again
        assert flow.run(flow.d1).status == "executed" and flow.ledger_effect_ids() == [flow.d1.effect_id]
        assert all("age_basis" not in x.model_dump(mode="json") for c in flow.record().resolution_checks for x in c.inputs)
        assert all(e.model_dump(mode="json").get("nonce") is None for e in flow.record().check_events)
    finally:
        mp.undo()


def test_a_resolver_that_cannot_echo_a_nonce_stays_source_asserted_under_the_profile(tmp_path):
    PROVENANCE_PROFILE.validate()
    mp = pytest.MonkeyPatch()
    try:
        flow = Flow(tmp_path, mp, identity=False, freshness={})  # no echo support
        assert flow.r.nonce_capability is None
        bases = {i.input_type: i.age_basis for c in flow.record().resolution_checks for i in c.inputs}
        assert bases["grant"] == "source_asserted" and "nonce_bound" not in bases.values() and bases["manifest"] is None
        assert flow.run(flow.d1).status == "executed"
    finally:
        mp.undo()


# --------------------------------------------------------------------------------- outage_extension_recorded_with_authority
EXTENSION = T.RefusalSpec(
    name="outage_extension_recorded_with_authority",
    reasons=("grant_status_stale_or_future", "age_extension_signer_not_configured"),
    changed_inputs=(T.ChangedInput("grant", GRANT),),
    provenance=PROVENANCE_PROFILE)


def test_outage_extension_recorded_with_authority(tmp_path, record_property):
    """Legs a-e via the template. The grant status is 70 s old (class bound 60 s) because the checker is in an outage. A signer
    from the configured rule-revision signer set records an extension to 200 s with the outage reference and authority; the
    status is accepted and r1 reaches the destination (the control). When the signer loses authority before dispatch the row no
    longer counts: r1 is held as stale, the refusal names the extension defect, and nothing is dispatched."""
    run_template(FreshnessAdapter("extension_withdrawn"), EXTENSION, tmp_path / "template", record_property, GRANT)
    adapter = FreshnessAdapter("extension_withdrawn")
    mp = pytest.MonkeyPatch()
    try:
        flow = adapter.build(tmp_path / "extra", mp)
        ext = flow.extension
        assert (ext.signer, ext.requested_by, ext.outage_ref, ext.authority_ref) == (
            EXT_SIGNER, REQUESTER, "outage-1", "urn:cognous:authority:outage-1")
        assert (ext.from_max_age_seconds, ext.to_max_age_seconds) == (60, 200)
        opened = [e for e in flow.record().check_events if e.phase == "opened"]
        assert (opened[-1].age_bound_seconds, opened[-1].extension_id) == (200, ext.extension_id)
        # authority is a precondition of recording: an unconfigured signer, the requester itself and an over-limit extension
        # are refused and each refusal is retained
        from agent_control_plane.freshness import AgeExtensionRefused
        for override, code in (({"signer": "urn:cognous:principal:stranger"}, "age_extension_signer_not_configured"),
                               ({"signer": REQUESTER}, "age_extension_self_signed"),
                               ({"to_max_age_seconds": 1000}, "age_extension_exceeds_limit")):
            with pytest.raises(AgeExtensionRefused) as caught:
                request_extension(flow, **override)
            assert code in caught.value.reasons
        refusals = json.loads(flow.f.records.path.read_text())["age_extension_refusals"]
        assert len(refusals) == 3 and [len(flow.record().age_extensions)] == [1]
        adapter.apply_change(flow)
        result = adapter.execute(flow)
        assert result.status == "denied" and flow.ledger_effect_ids() == []
    finally:
        mp.undo()
