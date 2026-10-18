"""Evidence check hardening probes for the journal and lifecycle rules, run against both implementations of them: the
reference validators of the ODES contracts (PROBE2_ODES_DIR) and the independent verifier (PROBE2_VERIFIER_DIR).

Each damaged record is one valid record with one change. A probe asserts that the change is refused; it is a strict expected
failure while the pinned head accepts it. The valid controls beside them are the records the tightened rules must keep
accepting (a refusal of valid producer output would be a regression, not a hardening).
"""
import copy

import pytest

import _matrix
from _support import (IMPLS, applied_base, closeout_base, effect_checks, effect_events, impl_params, odes_fixture, pending,
                      real_run, refusal_base, refusal_codes, verifier_fixture)

JOURNAL, LIFECYCLE = "control-plane-journal", "execution-attempt-lifecycle"
ALL = impl_params("verifier", "odes")


def journal_refusals(impl, doc):
    return refusal_codes(impl, doc, JOURNAL)


def lifecycle_refusals(impl, doc):
    return refusal_codes(impl, doc, LIFECYCLE)


def _dispatch_on(doc, applied):
    """Attempts of ``applied`` re-pointed at the (refused) decision of ``doc``."""
    decision = doc["decisions"][0]
    attempts = copy.deepcopy(applied["attempts"])
    for row in attempts:
        row["decision_id"], row["effect_id"] = decision["decision_id"], decision["effect_id"]
    return attempts


# ------------------------------------------------------------------------------------------- dispatch license
@pytest.mark.parametrize("impl", IMPLS)
def test_control_refused_record_and_applied_record_are_accepted(impl):
    assert journal_refusals(impl, refusal_base(impl)) == []
    assert journal_refusals(impl, applied_base(impl)) == []


@pytest.mark.parametrize("impl", ALL)
def test_probe_a_refusal_row_cannot_be_replaced_by_an_attempt(impl):
    """The effect check carries reasons; the refusal row is removed and an attempt for the same decision is added."""
    doc = refusal_base(impl)
    assert effect_checks(doc)[0]["reasons"], "the base record's effect check carries reasons"
    doc["refusals"] = []
    doc["attempts"] = _dispatch_on(doc, applied_base(impl))
    assert journal_refusals(impl, doc) != []


@pytest.mark.parametrize("impl", ALL)
def test_probe_a_blanked_reason_list_does_not_hide_a_replaced_refusal(impl):
    """As above, and the reasons of the effect check and of its journal events are blanked as well."""
    doc = refusal_base(impl)
    doc["refusals"] = []
    doc["attempts"] = _dispatch_on(doc, applied_base(impl))
    for check in effect_checks(doc):
        check["reasons"] = []
    for event in effect_events(doc):
        event["reasons"] = []
    assert journal_refusals(impl, doc) != []


@pytest.mark.parametrize("impl", ALL)
def test_probe_blank_check_reasons_are_refused_while_the_inputs_show_a_missing_input(impl):
    """The effect check and its events carry no reasons although a required input is recorded as missing."""
    doc = refusal_base(impl)
    assert any(x["missing"] for c in effect_checks(doc) for x in c["inputs"])
    for check in effect_checks(doc):
        check["reasons"] = []
    for event in effect_events(doc):
        event["reasons"] = []
    assert journal_refusals(impl, doc) != []


@pytest.mark.parametrize("impl", ALL)
def test_probe_an_empty_completion_cannot_bind_to_a_check_with_non_gate_reasons(impl):
    doc = refusal_base(impl)
    completed = [e for e in effect_events(doc) if e["phase"] == "completed"]
    assert completed and completed[0]["reasons"], "the base completion carries the check's reasons"
    for event in completed:
        event["reasons"] = []
    assert journal_refusals(impl, doc) != []


@pytest.mark.parametrize("name", ["profile-op-worker-self-renewal-then-unrecorded-hold", "reconciled-existing-single-row"])
@pytest.mark.parametrize("impl", IMPLS)
def test_control_a_completion_that_is_a_subset_with_gate_codes_added_after_it_is_accepted(impl, name):
    """The check row carries a code the producer appends after the journal completion (operation gate codes): accepted."""
    doc = (odes_fixture(JOURNAL, name) if impl == "odes" else verifier_fixture("journal", name))
    assert journal_refusals(impl, doc) == []


@pytest.mark.parametrize("impl", IMPLS)
def test_control_a_hold_with_gate_codes_after_the_completion_keeps_its_codes(impl):
    doc = odes_fixture(JOURNAL, "profile-op-worker-self-renewal-then-unrecorded-hold") if impl == "odes" \
        else verifier_fixture("journal", "profile-op-worker-self-renewal-then-unrecorded-hold")
    held = [c for c in doc["resolution_checks"] if c["reasons"]]
    done = [e for e in doc["check_events"] if e["phase"] == "completed" and e["stage"] == "decision"]
    assert held and held[0]["reasons"] == ["operation_renewal_unrecorded"]
    assert all(e["reasons"] == [] for e in done), "the journal completion precedes the gate code"


# --------------------------------------------------------------------------------------------- result identity
@pytest.mark.parametrize("impl", IMPLS)
def test_control_observed_result_with_null_attempt_id_stays_accepted(impl):
    name = "executor-observed-effect-free-reconcile-route-b"
    doc = odes_fixture(LIFECYCLE, name) if impl == "odes" else verifier_fixture("lifecycle", name)
    assert doc["execution_result"]["status"] == "observed" and doc["execution_result"]["attempt_id"] is None
    assert lifecycle_refusals(impl, doc) == []


# -------------------------------------------------------------------------------- result status x flags x observation
def lifecycle_base(impl):
    name = "executor-normal-attempted-executed-observed"
    return copy.deepcopy(odes_fixture(LIFECYCLE, name) if impl == "odes" else verifier_fixture("lifecycle", name))


def _matrix_misses(impl, status, allowed):
    base = lifecycle_base(impl)
    missed = []
    for cell in _matrix.cells(status):
        if _matrix.producer_allows(*cell) != allowed:
            continue
        refused = lifecycle_refusals(impl, _matrix.build_result(cell, base)) != []
        if refused == allowed:  # an allowed cell refused, or a contradictory cell accepted
            missed.append(cell)
    return missed


@pytest.mark.parametrize("impl", IMPLS)
def test_control_every_combination_the_producer_allows_is_accepted(impl):
    allowed = [c for s in _matrix.STATUSES for c in _matrix.cells(s) if _matrix.producer_allows(*c)]
    assert allowed, "the matrix has allowed cells"
    missed = []
    base = lifecycle_base(impl)
    for cell in allowed:
        if lifecycle_refusals(impl, _matrix.build_result(cell, base)):
            missed.append(cell)
    assert missed == [], f"valid producer combinations refused: {missed[:5]}"


FORBIDDEN_RED = {  # statuses with a contradictory combination the pinned head accepts, per implementation
    "verifier": {"denied", "failed", "partial", "unknown", "executed", "reconciled"},
    "odes": {"denied", "failed", "partial", "unknown", "executed", "reconciled"},
}


def _status_params():
    out = []
    for status in _matrix.STATUSES:
        for impl in IMPLS:
            marks = [pending()] if status in FORBIDDEN_RED[impl] else []
            out.append(pytest.param(impl, status, id=f"{impl}-{status}", marks=marks))
    return out


@pytest.mark.parametrize("impl,status", _status_params())
def test_probe_every_contradictory_combination_for_a_status_is_refused(impl, status):
    """For one result status, every flag and state combination the producer refuses is refused by the checker."""
    missed = _matrix_misses(impl, status, allowed=False)
    assert missed == [], f"{len(missed)} contradictory combinations accepted, for example {missed[:3]}"


@pytest.mark.parametrize("impl", ALL)
@pytest.mark.parametrize("status", ["failed", "partial", "unknown", "executed", "reconciled"])
def test_probe_a_null_attempt_id_on_an_attempt_claiming_status_is_refused(impl, status):
    state = {"failed": "unknown", "partial": "partial", "unknown": "unknown", "executed": "applied", "reconciled": "applied"}[status]
    flags = {"failed": (True, False, False), "partial": (True, True, False), "unknown": (True, False, False),
             "executed": (True, True, True), "reconciled": (True, True, False)}[status]
    cell = (status, *flags, state, False)
    doc = _matrix.build_result(cell, lifecycle_base(impl))
    assert doc["execution_result"]["attempt_id"] is None
    assert lifecycle_refusals(impl, doc) != []


@pytest.mark.parametrize("impl", ALL)
@pytest.mark.parametrize("status", ["failed", "partial", "unknown", "executed", "reconciled"])
def test_probe_a_result_naming_no_attempt_row_is_refused(impl, status):
    state = {"failed": "unknown", "partial": "partial", "unknown": "unknown", "executed": "applied", "reconciled": "applied"}[status]
    flags = {"failed": (True, False, False), "partial": (True, True, False), "unknown": (True, False, False),
             "executed": (True, True, True), "reconciled": (True, True, False)}[status]
    doc = _matrix.build_result((status, *flags, state, True), lifecycle_base(impl))
    doc["execution_result"]["attempt_id"] = "unregistered-attempt"
    assert lifecycle_refusals(impl, doc) != []


@pytest.mark.parametrize("impl", IMPLS)
def test_control_a_result_whose_observation_names_another_effect_is_refused(impl):
    doc = lifecycle_base(impl)
    doc["execution_result"]["observation"]["effect_id"] = "syn-effect-other"
    assert lifecycle_refusals(impl, doc) != []


@pytest.mark.parametrize("impl", IMPLS)
def test_control_a_result_naming_an_attempt_of_another_effect_is_refused(impl):
    doc = lifecycle_base(impl)
    doc["attempts"].append({"attempt_id": "syn-attempt-2", "effect_id": "syn-effect-2", "decision_id": "syn-decision-2"})
    doc["attempt_events"] += [
        {"event_id": 3, "attempt_id": "syn-attempt-2", "status": "attempted", "error": None, "created_at": 1002.0},
        {"event_id": 4, "attempt_id": "syn-attempt-2", "status": "executed", "error": None, "created_at": 1003.0}]
    doc["execution_result"]["attempt_id"] = "syn-attempt-2"
    assert lifecycle_refusals(impl, doc) != []


# ------------------------------------------------------------------------------------------------ causal order
def _shifted(stamp, hours=-1):
    from datetime import datetime, timedelta
    moment = datetime.fromisoformat(stamp.replace("Z", "+00:00")) + timedelta(hours=hours)
    return moment.isoformat()


@pytest.mark.parametrize("impl", ALL)
def test_probe_an_attempt_that_starts_before_its_decision_is_refused(impl):
    doc = applied_base(impl)
    for row in doc["attempts"]:
        row["started_at"] = _shifted(doc["decisions"][0]["decided_at"])
    assert journal_refusals(impl, doc) != []


@pytest.mark.parametrize("impl", ALL)
def test_probe_a_reconciliation_dated_before_its_attempt_is_refused(impl):
    doc = closeout_base(impl)
    earliest = min(a["started_at"] for a in doc["attempts"])
    for rec in doc["reconciliations"]:
        rec["reconciled_at"] = _shifted(earliest)
    assert journal_refusals(impl, doc) != []


@pytest.mark.parametrize("impl", ALL)
def test_probe_a_closeout_dated_before_its_attempt_is_refused(impl):
    doc = closeout_base(impl)
    assert doc["closeouts"], "the base record has a closeout"
    earliest = min(a["started_at"] for a in doc["attempts"])
    for closeout in doc["closeouts"]:
        closeout["reconciled_at"] = _shifted(earliest)
    assert journal_refusals(impl, doc) != []


@pytest.mark.parametrize("impl", IMPLS)
def test_control_forward_order_in_the_closeout_record_is_accepted(impl):
    assert journal_refusals(impl, closeout_base(impl)) == []
