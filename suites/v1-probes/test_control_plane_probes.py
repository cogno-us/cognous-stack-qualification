"""SR-1 probes for the Control Plane: clock uncertainty, observation time and freshness are explicit and enforced.

Drives the real BoundedAuthorizationWorkflow reconciliation path and BoundedRecordStore time floors at exact boundaries.
Run against the checkout named by PROBE_CONTROL_PLANE_DIR (Linux only: the record store requires flock).
"""
from datetime import datetime, timedelta, timezone

import pytest

from conftest import pin_dir

NOW = datetime(2026, 10, 5, 19, 0, tzinfo=timezone.utc)
EFFECT = "effect-1"


@pytest.fixture(autouse=True)
def _pin():
    pin_dir("PROBE_CONTROL_PLANE_DIR")


class Observer:
    def __init__(self, observation):
        self.observation = observation

    def observe(self, effect_id):
        return self.observation.model_copy(deep=True)


def flow(tmp_path, observed_at, *, tolerance=5, max_age=300, test_time=True, state="absent", policy=True):
    import agent_control_plane.bounded as b
    obs = b.EffectObservation(effect_id=EFFECT, observed_at=observed_at, state=state, destination_state={})
    records = b.BoundedRecordStore(tmp_path / "run.json", "probe-run")
    wf = b.BoundedAuthorizationWorkflow(
        allow_test_time=test_time, manifest={}, resolver=None, destination=Observer(obs), records=records,
        observation_policy=b.ObservationPolicy(max_age_seconds=max_age, clock_tolerance_seconds=tolerance) if policy else None)
    return wf, records


def iso(delta):
    return (NOW + timedelta(seconds=delta)).isoformat()


# ----------------------------------------------------- explicit tolerance boundary
@pytest.mark.parametrize("tolerance", [0, 5, 30])
def test_probe_clock_uncertainty_future_observation_accepted_exactly_up_to_declared_tolerance(tmp_path, tolerance):
    ok, _ = flow(tmp_path / "ok", iso(tolerance), tolerance=tolerance)
    r = ok.reconcile(EFFECT, now=NOW)
    assert r.observation_accepted is True and r.result == "observed_absent", r.reasons
    bad, records = flow(tmp_path / "bad", iso(tolerance + 1), tolerance=tolerance)
    r = bad.reconcile(EFFECT, now=NOW)
    assert r.observation_accepted is False and r.result == "hold" and "observation_time_future" in r.reasons
    assert records.load().observations == []  # an observation from the future is retained as a rejection, never as state


def test_probe_clock_uncertainty_tolerance_never_extends_the_staleness_window(tmp_path):
    fresh, _ = flow(tmp_path / "a", iso(-300), tolerance=30, max_age=300)
    assert fresh.reconcile(EFFECT, now=NOW).observation_accepted is True  # age == max_age is the last fresh instant
    stale, _ = flow(tmp_path / "b", iso(-301), tolerance=30, max_age=300)
    r = stale.reconcile(EFFECT, now=NOW)
    assert r.observation_accepted is False and "observation_stale" in r.reasons and "observation_time_future" not in r.reasons


def test_probe_clock_uncertainty_policy_values_are_recorded_with_the_decision(tmp_path):
    wf, records = flow(tmp_path, iso(0), tolerance=7, max_age=123)
    r = wf.reconcile(EFFECT, now=NOW)
    assert (r.observation_clock_tolerance_seconds, r.observation_max_age_seconds) == (7, 123)
    assert r.evaluation_time == NOW.isoformat()
    kept = records.load().reconciliations[-1]
    assert (kept.observation_clock_tolerance_seconds, kept.observation_max_age_seconds, kept.evaluation_time) == (7, 123, NOW.isoformat())


def test_probe_clock_uncertainty_must_be_declared_non_negative_and_age_positive():
    import agent_control_plane.bounded as b
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        b.ObservationPolicy(max_age_seconds=300, clock_tolerance_seconds=-1)
    with pytest.raises(ValidationError):
        b.ObservationPolicy(max_age_seconds=0)
    assert b.ObservationPolicy(max_age_seconds=1).clock_tolerance_seconds == 5  # documented default, not unbounded


def test_probe_clock_uncertainty_missing_observation_policy_holds_rather_than_assuming_a_tolerance(tmp_path):
    wf, records = flow(tmp_path, iso(0), policy=False)
    r = wf.reconcile(EFFECT, now=NOW)
    assert r.result == "hold" and "observation_policy_missing" in r.reasons and records.load().observations == []


# --------------------------------------------------------- observation time and clock trust
@pytest.mark.parametrize("observed_at,reason", [
    (None, "observation_time_missing"), ("", "observation_time_missing"), ("not-a-time", "observation_time_malformed"),
    ("2026-10-05T19:00:00", "observation_time_timezone_missing"),
])
def test_probe_clock_observation_time_missing_malformed_or_zoneless_is_never_accepted(tmp_path, observed_at, reason):
    wf, records = flow(tmp_path, observed_at)
    r = wf.reconcile(EFFECT, now=NOW)
    assert r.observation_accepted is False and r.result == "hold" and reason in r.reasons
    assert records.load().observations == []


def test_probe_clock_evaluation_time_missing_or_zoneless_holds_under_test_clock(tmp_path):
    wf, _ = flow(tmp_path / "m", iso(0))
    assert "evaluation_time_missing" in wf.reconcile(EFFECT).reasons
    wf2, _ = flow(tmp_path / "n", iso(0))
    r = wf2.reconcile(EFFECT, now=NOW.replace(tzinfo=None))
    assert r.result == "hold" and "evaluation_time_timezone_missing" in r.reasons


def test_probe_clock_caller_supplied_time_is_ignored_outside_the_explicit_test_clock(tmp_path, monkeypatch):
    import agent_control_plane.bounded as b
    server_now = NOW
    monkeypatch.setattr(b, "_now", lambda: server_now)
    wf, _ = flow(tmp_path, iso(-10), test_time=False)
    # a caller trying to make a stale/future observation look fresh by supplying its own clock has no effect
    lie = NOW + timedelta(days=365)
    r = wf.reconcile(EFFECT, now=lie)
    assert r.evaluation_time == server_now.isoformat()
    assert r.observation_accepted is True
    stale_wf, _ = flow(tmp_path / "s", iso(-10_000), test_time=False)
    assert "observation_stale" in stale_wf.reconcile(EFFECT, now=NOW - timedelta(days=365)).reasons


def test_probe_clock_time_source_is_labelled_in_retained_records(tmp_path):
    wf, _ = flow(tmp_path / "t", iso(0), test_time=True)
    assert wf.time_source == "test_override"
    wf2, _ = flow(tmp_path / "p", iso(0), test_time=False)
    assert wf2.time_source == "control_plane"


# ------------------------------------------------------------- freshness / observation floors
def make_input(observed_at):
    import agent_control_plane.bounded as b
    return b.ResolutionInput(input_type="grant", input_id="g1", observed={"observed_at": observed_at})


def floor_of(records):
    return next(iter(records.load().input_time_floors.values()), None)


def test_probe_clock_future_input_beyond_tolerance_cannot_poison_the_observation_floor(tmp_path):
    import agent_control_plane.bounded as b
    records = b.BoundedRecordStore(tmp_path / "run.json", "probe-run")
    args = dict(now=NOW, stage="decision", time_source="test_override", reasons=[], tolerance_seconds=5)
    records.record_resolution_check(inputs=[make_input(iso(5))], **args)
    assert floor_of(records) == iso(5)  # within tolerance: floor advances
    records.record_resolution_check(inputs=[make_input(iso(60))], **args)
    assert floor_of(records) == iso(5)  # beyond tolerance: floor does not advance
    ok = records.record_resolution_check(inputs=[make_input(iso(1))], **args)
    assert "input_observation_time_regressed" in ok  # older than the floor: regression is flagged
    fine = records.record_resolution_check(inputs=[make_input(iso(5))], **args)
    assert "input_observation_time_regressed" not in fine


def test_probe_clock_observation_floor_survives_store_reopen(tmp_path):
    import agent_control_plane.bounded as b
    args = dict(now=NOW, stage="decision", time_source="test_override", reasons=[], tolerance_seconds=5)
    b.BoundedRecordStore(tmp_path / "run.json", "probe-run").record_resolution_check(inputs=[make_input(iso(0))], **args)
    reopened = b.BoundedRecordStore(tmp_path / "run.json", "probe-run")
    reasons = reopened.record_resolution_check(inputs=[make_input(iso(-1))], **args)
    assert "input_observation_time_regressed" in reasons
