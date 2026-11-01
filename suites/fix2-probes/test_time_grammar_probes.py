"""Strict time grammar probes across the places that read an instant: the ODES reference validators and common module,
Replay, the independent verifier and the control plane.

An instant is ``YYYY-MM-DDThh:mm:ss[.f]`` then ``Z`` or an offset: upper-case ``T``, ASCII digits, seconds mandatory, one to
six fraction digits, hour 00 to 23. The four forms below are refused by that grammar and are accepted by a bare
``datetime.fromisoformat`` (on Python 3.14 hour 24 as well; before 3.14 the interpreter itself refuses hour 24, so that
form is an expected failure only from 3.14 on). A site that already refuses them is a control and stays unmarked.
"""
import copy
import json
import re

import pytest

import _support
from _support import root

FORMS = {
    "hour-24": "2026-01-01T24:00:00Z",
    "seventh-fraction-digit": "2026-01-01T00:00:00.1234567Z",
    "space-separator": "2026-01-01 00:00:00Z",
    "week-date": "2026-W01-4T00:00:00Z",
}
VALID = "2026-01-01T00:00:00Z"


def form_params(red_forms=()):
    """One parameter per form. ``red_forms`` is kept for the call sites: no form is an expected failure any more (the hour-24
    form was one only on Python 3.14 and later, where the standard parser accepts it; the checked heads now refuse it there too)."""
    return [pytest.param(value, id=name) for name, value in FORMS.items()]


def refuses(fn, value):
    try:
        fn(value)
    except Exception:  # any refusal path: ValueError, a typed contract error, TypeError
        return True
    return False


# -------------------------------------------------------------------------------------------------------- ODES
@pytest.mark.parametrize("value", form_params(red_forms=("hour-24",)))
def test_probe_odes_common_instant_parser_refuses_the_four_forms(value):
    import odes.common as common
    assert common.parse_instant(value) is None


def test_control_odes_common_instant_parser_accepts_a_valid_instant():
    import odes.common as common
    assert common.parse_instant(VALID) is not None


TIME_CODES = re.compile(r"timestamp|time_invalid|time_naive")
CONTRACTS = ("bounded-deferral", "effect-reversibility", "freshness-clocks", "holder-inventory", "non-broadening-delegation",
             "operation-identity", "two-party-reconciliation", "verification-report")
STAMP = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?(Z|[+-]\d\d:\d\d)$")


def _stamp_paths(doc, path=()):
    if isinstance(doc, dict):
        for key, value in doc.items():
            yield from _stamp_paths(value, path + (key,))
    elif isinstance(doc, list):
        for index, value in enumerate(doc):
            yield from _stamp_paths(value, path + (index,))
    elif isinstance(doc, str) and STAMP.match(doc):
        yield path


def _with(doc, path, value):
    out = copy.deepcopy(doc)
    node = out
    for step in path[:-1]:
        node = node[step]
    node[path[-1]] = value
    return out


def _bad_form(stamp, form):
    if form == "hour-24":
        return re.sub(r"T\d\d:", "T24:", stamp, count=1)
    if form == "seventh-fraction-digit":
        return re.sub(r"(:\d\d)(Z|[+-]\d\d:\d\d)$", r"\g<1>.1234567\2", stamp)
    if form == "space-separator":
        return stamp.replace("T", " ", 1)
    return re.sub(r"^\d{4}-\d\d-\d\d", "2026-W01-4", stamp)


@pytest.mark.parametrize("form", list(FORMS))
@pytest.mark.parametrize("contract", CONTRACTS)
def test_probe_contract_validators_refuse_a_malformed_instant_in_every_time_field(contract, form):
    """Each timestamp of the first valid fixtures is replaced, one at a time, by the form; each is refused as a timestamp."""
    module = _support.odes_contract(contract)
    fixtures = sorted((root("PROBE2_ODES_DIR") / "contracts" / contract / "fixtures" / "valid").glob("*.json"))[:3]
    missed = []
    checked = 0
    for fixture in fixtures:
        doc = json.loads(fixture.read_text(encoding="utf-8"))["document"]
        for path in list(_stamp_paths(doc))[:6]:
            original = doc
            for step in path:
                original = original[step]
            damaged = _with(doc, path, _bad_form(original, form))
            checked += 1
            if not any(TIME_CODES.search(v.code) for v in module.validate(damaged)):
                missed.append((fixture.name, path))
    assert checked
    assert missed == [], f"{len(missed)} of {checked} malformed instants not refused as timestamps, for example {missed[:2]}"


# ------------------------------------------------------------------------------------------------------ Replay
def _replay_sites():
    from agent_replay_bundle import importers, programme2_profiles as p2, recovery_inspection as ri
    return {
        "importers-aware-time": importers._aware_time,
        "profiles-instant": lambda v: p2.instant(v, "probe"),
        "recovery-inspection-time": ri._time,
    }


@pytest.mark.parametrize("site", ["importers-aware-time", "profiles-instant", "recovery-inspection-time"])
@pytest.mark.parametrize("value", form_params(red_forms=()))
def test_probe_replay_refuses_a_malformed_instant(site, value):
    fn = _replay_sites()[site]
    assert refuses(fn, value)


@pytest.mark.parametrize("site", ["importers-aware-time", "profiles-instant", "recovery-inspection-time"])
def test_control_replay_accepts_a_valid_instant(site):
    assert not refuses(_replay_sites()[site], VALID)


# ----------------------------------------------------------------------------------------------------- verifier
@pytest.mark.parametrize("value", form_params(red_forms=()))
def test_control_verifier_instant_parser_refuses_the_four_forms(value):
    from cognous_verify.timeutil import aware
    assert aware(value) is None
    assert aware(VALID) is not None


# ----------------------------------------------------------------------------------------------- control plane
@pytest.mark.parametrize("value", form_params(red_forms=()))
def test_control_control_plane_strict_parser_refuses_the_four_forms(value):
    from agent_control_plane.time_instant import parse_instant
    with pytest.raises(ValueError):
        parse_instant(value)
    parse_instant(VALID)


def _arity(as_of=VALID, row_time=VALID):
    from agent_control_plane.reason_vocabulary import measured_arity
    rows = [{"recorded_at": row_time, "reasons": ["required_input_not_read"], "resolution_inputs": []}]
    return lambda: measured_arity(rows, as_of=as_of, period_seconds=3600)


@pytest.mark.parametrize("value", form_params(red_forms=tuple(FORMS)))
def test_probe_control_plane_report_period_end_refuses_a_malformed_instant(value):
    with pytest.raises(ValueError):
        _arity(as_of=value)()


@pytest.mark.parametrize("value", form_params(red_forms=tuple(FORMS)))
def test_probe_control_plane_report_row_time_refuses_a_malformed_instant(value):
    with pytest.raises(ValueError):
        _arity(row_time=value)()


def test_control_control_plane_report_with_valid_instants_is_produced():
    report = _arity()()
    assert report["as_of"] == VALID and "required_input_not_read" in report["codes"]
