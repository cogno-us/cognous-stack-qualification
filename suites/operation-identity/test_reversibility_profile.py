"""N4 composed scenarios: opt-in reversibility/0.1 across control plane and runtime (addendum 101726_B, L4).

SPDX-License-Identifier: Apache-2.0

Route: control plane BoundedAuthorizationWorkflow -> runtime PinnedControlPlaneExecutor -> the runtime's SQLite destination.
Synthetic fixtures only; the purpose store outage is a resolver that raises; no network effects.

What these prove: under the opt-in profile an action class carries one of ``irreversible | reversible_until | reversible_at_cost``;
during a purpose-store outage a cached "open" purpose snapshot (with its epoch and age) is accepted only for a reversible class,
only inside its age bound (``max_status_age_seconds`` or a recorded N3 extension), never for a class that reads protected data,
never once a ``reversible_until`` deadline has passed (it is then treated as irreversible), and never against a purpose closure this
control plane already recorded. Every accepted use appends a row naming the snapshot's epoch and age. What they do not prove: that
the cached snapshot is true (it is the source's own assertion, ``age_basis: source_asserted``), that a closure this control plane did
not itself read is honoured, or anything about the data the class reads (a class declaration is trusted host configuration).

Provenance of "expected today" values (leg e). ``test_purpose_outage_refuses_a_reversible_class_today`` was RUN against pristine
control plane main 3f6a766 and runtime main 6bfb77ee (default path: a purpose outage refuses for every class, nothing is cached). The
profile tests describe new opt-in behaviour: there is no expected-today value and they FAIL on those mains by design. Each profile
test's code-reading label names the implementing files.
"""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import timedelta

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import _refusal_template as T  # noqa: E402
from _oi_flow import Flow  # noqa: E402

PRINCIPAL = "urn:cognous:principal:refund-service"
PROVENANCE_PROFILE = T.Provenance("code-reading", "control plane reversibility.py (judge_cached_purpose, effective_reversibility) and "
                                  "bounded.py (_cached_purpose, validate_extensions purpose_cache): opt-in reversibility/0.1 (new), no "
                                  "expected-today value; fails on the pinned mains by design")
PROVENANCE_TODAY = T.Provenance("run", "control plane main 3f6a766 and runtime main 6bfb77ee, pristine checkouts, "
                                "test_purpose_outage_refuses_a_reversible_class_today")


# ----------------------------------------------------------------------------------------------------------- the flow
def action_class(value="reversible_at_cost", **members):
    from agent_control_plane.runtime_authority import ActionClass
    base = dict(reversibility=value, class_id="synthetic-" + value, max_status_age_seconds=60)
    if value == "reversible_until":
        base["reversible_until"] = (T_NOW() + timedelta(minutes=10)).isoformat()
    if value == "reversible_at_cost":
        base["reversal_cost"] = "refund can be clawed back at a fee"
    if value != "irreversible":
        base["on_unreadable"] = "bounded_tolerance"
    base.update(members)
    return ActionClass(**base)


def T_NOW():
    import tests.test_bounded_authorization as tba
    return tba.NOW


def build(work, mp, value="reversible_at_cost", **members):
    def update(flow):
        from agent_control_plane.reversibility import ReversibilityProfile
        return {"actions": {flow.p.action_id: action_class(value, **members)}, "reversibility": ReversibilityProfile()}

    def cache(flow):
        flow.r.cached = flow.r.purpose.model_copy()
        flow.r.cached_purpose_status = lambda ref: flow.r.cached.model_dump()
    return Flow(work, mp, identity=False, purpose=True, cfg_update=update, setup=cache)


def outage(flow):
    def broken(ref):
        raise TimeoutError("purpose store unavailable")
    flow.r.purpose_status = broken


def at(flow, seconds):
    """Move the evaluation clock without refreshing inputs: the purpose snapshot keeps its original observation time."""
    flow.NOW = T_NOW() + timedelta(seconds=seconds)
    flow.mp.setattr(flow.cp, "_now", lambda: flow.NOW)


def uses(flow):
    return json.loads(flow.f.records.path.read_text(encoding="utf-8")).get("snapshot_uses", [])


def record(record_property, name, result=None, report=None, text=None):
    record_property("principal", PRINCIPAL)
    record_property(name, T.report_json(result, report) if result is not None else text)


# ------------------------------------------------------------------------------------------------ refusal adapter
class PurposeAdapter(T.Adapter):
    """Outage (optionally with a recorded closure) is the change; executing the decided effect at ``seconds`` is the call.
    The ``purpose`` entry of ``changed_inputs`` is a projection of the real snapshot-use row (its versions are built from real
    values; nothing is invented)."""

    def __init__(self, value="reversible_at_cost", seconds=0, closure=False, **members):
        self.value, self.seconds, self.closure, self.members = value, seconds, closure, members

    def build(self, work, mp):
        return build(work, mp, self.value, **self.members)

    def apply_change(self, flow):
        if self.closure:
            flow.r.purpose.state = "closed"             # read live and recorded by the control plane ...
            assert flow.f.decide(flow.p, now=flow.NOW).result == "hold"
        outage(flow)                                     # ... then the purpose store goes down; the cache still says open

    def execute(self, flow):
        at(flow, self.seconds)
        try:
            return flow.run(flow.d1)
        except PermissionError as refused:
            return refused

    def effect_id(self, flow):
        return flow.d1.effect_id

    def ledger_effect_ids(self, flow):
        return flow.ledger_effect_ids()

    def refusal_rows(self, flow):
        rows = []
        for r in flow.record().refusals:
            row = r.model_dump(mode="json")
            row = {k: row[k] for k in ("refusal_id", "effect_id", "stage", "reasons")}
            (use,) = [u for u in uses(flow) if not u["accepted"]][-1:]
            row["changed_inputs"] = [{
                "input_type": "purpose", "input_id": use["purpose_ref"],
                "expected_version": f"state=open;epoch={use['epoch']}",
                "observed_version": f"basis={use['basis']};effective={use['effective_status']};accepted={use['accepted']};"
                                    f"reversibility={use['reversibility']};age={use['age_seconds']}"}]
            rows.append(row)
        return rows

    def disable_refusal_writer(self, flow):
        flow.f.records.append_refusal = lambda value: None  # only the evidence row is lost; the gate still refuses

    def policy_versions_observed_at_enforcement(self, flow, stage):
        return {}


def run_template(adapter, spec, tmp_path, record_property):
    result = T.run_refusal_scenario(adapter, spec, tmp_path, pytest.MonkeyPatch)
    assert result.legs_passed == T.LEGS
    holders = [{"holder_id": "urn:cognous:issuance:1", "kind": "mandate"}]
    report = T.classify_holders(holders, [result.refusal_row])
    record(record_property, "n4_" + spec.name, result, report)
    return result, report


def run_spec(adapter, name, reasons, tmp_path, record_property):
    # the purpose input id is the commitment of the grant's purpose binding, which the adapter reads from the real row
    probe = adapter.build(tmp_path / "probe", pytest.MonkeyPatch())
    adapter.apply_change(probe)
    adapter.execute(probe)
    (use,) = [u for u in uses(probe) if not u["accepted"]][-1:]
    s = T.RefusalSpec(name=name, reasons=tuple(reasons), changed_inputs=(T.ChangedInput("purpose", use["purpose_ref"]),),
                      provenance=PROVENANCE_PROFILE)
    return run_template(adapter, s, tmp_path / "template", record_property)


# --------------------------------------------------------------------------- reversible_until_past_deadline_treated_irreversible
def test_reversible_until_past_deadline_treated_irreversible(tmp_path, record_property):
    """Legs a-e via the template. The class is ``reversible_until`` a deadline 40 s after the decision; the purpose store is down and
    the cache says open. At +40 s (the deadline) the class is treated as irreversible and the cache is refused, and no effect lands.
    The control (same call, purpose readable) reaches the destination. Inside the window (+39 s) the same cache is accepted."""
    deadline = (T_NOW() + timedelta(seconds=40)).isoformat()
    result, report = run_spec(PurposeAdapter("reversible_until", seconds=40, reversible_until=deadline), "reversible_until_past_deadline_treated_irreversible",
                              ("purpose_cache_after_reversal_window", "purpose_unreadable"), tmp_path, record_property)
    assert result.refusal_row["reasons"] == ["purpose_cache_after_reversal_window", "purpose_unreadable"]
    mp = pytest.MonkeyPatch()
    try:
        inside = PurposeAdapter("reversible_until", seconds=39, reversible_until=deadline)
        flow = inside.build(tmp_path / "inside", mp)
        inside.apply_change(flow)
        at(flow, 39)
        assert flow.run(flow.d1).status == "executed"
        (use,) = uses(flow)
        assert use["accepted"] and use["reversibility"] == "reversible_until" and use["age_seconds"] == 39
        past = PurposeAdapter("reversible_until", seconds=40, reversible_until=deadline).build(tmp_path / "past", mp)
        outage(past)
        at(past, 40)
        assert past.run(past.d1).status == "denied"
        assert uses(past)[-1]["reversibility"] == "irreversible" and not uses(past)[-1]["accepted"]
    finally:
        mp.undo()


# ------------------------------------------------------------------ purpose_outage_cached_open_reversible_proceeds_records_age
def check_accepted_use(flow, seconds, value):
    """Leg (b): the effect landed, and exactly one accepted use row names the snapshot's epoch, its age and the bound."""
    assert len(flow.ledger_effect_ids()) == 1, "the effect did not land"
    (use,) = uses(flow)
    assert use["accepted"] and use["basis"] == "cached_snapshot" and use["effective_status"] == "open"
    assert use["epoch"] == "epoch-1" and use["age_seconds"] == seconds and use["age_bound_seconds"] == 60
    assert use["reversibility"] == value and use["age_basis"] == "source_asserted"
    return use


def test_purpose_outage_cached_open_reversible_proceeds_records_age(tmp_path, record_property):
    """Legs written out. (a) negative: the same outage with no cache provider refuses and nothing lands (the cache is what lets it
    proceed); (b) with the cache the effect lands and the use row records epoch and age; (c) control: purpose readable -> the same
    effect lands and no use row is written (the cache is never touched when the store answers); (d) mutation: with the use-row writer
    disabled leg (b) fails although the effect still lands; (e) provenance. Bound edges: age 60 s accepted, 61 s refused."""
    PROVENANCE_PROFILE.validate()
    mp = pytest.MonkeyPatch()
    try:
        for value in ("reversible_at_cost", "reversible_until"):
            flow = build(tmp_path / ("real-" + value), mp, value)
            outage(flow)
            at(flow, 30)
            assert flow.run(flow.d1).status == "executed"
            use = check_accepted_use(flow, 30, value)                                        # (b)
            effect_check = [c for c in flow.record().resolution_checks if c.stage == "effect"][-1]
            item = next(i for i in effect_check.inputs if i.input_type == "purpose")
            assert item.read_state == "cached_positive" and item.observed["epoch"] == "epoch-1" and item.observed["age_seconds"] == "30.0"
        record(record_property, "n4_purpose_outage_cached_open", text=json.dumps(use, indent=2, sort_keys=True))
        nocache = build(tmp_path / "nocache", mp)                                            # (a)
        outage(nocache)
        del nocache.r.cached_purpose_status
        assert nocache.run(nocache.d1).status == "denied"
        assert nocache.ledger_effect_ids() == [] and nocache.record().refusals[-1].reasons == ["purpose_unreadable"]
        assert uses(nocache)[-1]["basis"] == "strict_default" and not uses(nocache)[-1]["accepted"]
        control = build(tmp_path / "control", mp)                                            # (c)
        assert control.run(control.d1).status == "executed" and control.ledger_effect_ids() == [control.d1.effect_id] and uses(control) == []
        mutant = build(tmp_path / "mutant", mp)                                              # (d)
        mutant.f.records.append_snapshot_use = lambda value: None
        outage(mutant)
        at(mutant, 30)
        assert mutant.run(mutant.d1).status == "executed", "the effect still lands; only the evidence is lost"
        with pytest.raises(ValueError):
            check_accepted_use(mutant, 30, "reversible_at_cost")
        edge = build(tmp_path / "edge", mp)                                                  # the bound is inclusive
        outage(edge)
        at(edge, 60)
        assert edge.run(edge.d1).status == "executed" and uses(edge)[-1]["age_seconds"] == 60
        stale = build(tmp_path / "stale", mp)
        outage(stale)
        at(stale, 61)
        assert stale.run(stale.d1).status == "denied"
        assert uses(stale)[-1]["reasons"] == ["purpose_cache_stale"] and stale.ledger_effect_ids() == []
    finally:
        mp.undo()


# -------------------------------------------------------------------------------------- purpose_outage_protected_read_refuses
def test_purpose_outage_protected_read_refuses(tmp_path, record_property):
    """Legs a-e via the template. The class reads protected data (so it is irreversible by the contract): an outage with the same
    cache that a reversible class accepts is refused, and no effect lands. Control: purpose readable -> the effect lands."""
    run_spec(PurposeAdapter("irreversible", reads_protected_data=True), "purpose_outage_protected_read_refuses",
             ("purpose_cache_irreversible_class", "purpose_unreadable"), tmp_path, record_property)
    mp = pytest.MonkeyPatch()
    try:
        # the same cache and age for a reversible class is accepted: the class, not the cache, is what refuses
        ok = build(tmp_path / "reversible", mp)
        outage(ok)
        assert ok.run(ok.d1).status == "executed"
        # a protected read can never be declared reversible
        with pytest.raises(ValueError, match="protected_read_not_irreversible"):
            action_class("reversible_at_cost", reads_protected_data=True)
    finally:
        mp.undo()


# --------------------------------------------------------------------------------------- recorded_closure_overrides_cached_open
def test_recorded_closure_overrides_cached_open(tmp_path, record_property):
    """Legs a-e via the template. The control plane reads the purpose closed (a recorded closure, a hold); later the store is down
    and the cache still says open. The recorded closure wins: refused, no effect. Control: no closure and no outage -> the effect
    lands. A cache that itself says closed never supports open."""
    run_spec(PurposeAdapter("reversible_at_cost", seconds=1, closure=True), "recorded_closure_overrides_cached_open",
             ("purpose_closure_recorded", "purpose_unreadable"), tmp_path, record_property)
    mp = pytest.MonkeyPatch()
    try:
        flow = build(tmp_path / "closed-cache", mp)
        outage(flow)
        flow.r.cached.state = "closed"
        assert flow.run(flow.d1).status == "denied"
        assert "purpose_closed" in flow.record().refusals[-1].reasons and flow.ledger_effect_ids() == []
    finally:
        mp.undo()


# ----------------------------------------------------------------------------------------------------- default path today
def test_purpose_outage_refuses_a_reversible_class_today(tmp_path, record_property):
    """Expected today (ran, default path): without the profile a purpose outage refuses even for a reversible legacy class with a
    cache available; nothing is cached and no use row exists."""
    PROVENANCE_TODAY.validate()
    mp = pytest.MonkeyPatch()
    try:
        flow = Flow(tmp_path, mp, identity=False, purpose=True, reversible=True)
        flow.r.cached = flow.r.purpose.model_copy()
        flow.r.cached_purpose_status = lambda ref: flow.r.cached.model_dump()
        outage(flow)
        assert flow.run(flow.d1).status == "denied"
        assert flow.record().refusals[-1].reasons == ["purpose_unreadable"] and flow.ledger_effect_ids() == []
        assert "snapshot_uses" not in json.loads(flow.f.records.path.read_text(encoding="utf-8"))
        record(record_property, "n4_purpose_outage_today", text="purpose_unreadable")
    finally:
        mp.undo()
