"""ODES reference validator probes for typed constants (PROBE2_ODES_DIR).

A schema ``const`` of a boolean must not accept the number that compares equal to it (``1`` for ``true``, ``0`` for
``false``). Three schemas state such a constant and no fixture mutated it: the bounded-deferral refusal notice, the
effect-reversibility lost-acknowledgement row and the verification-report context and report markers. Each probe replaces
the member with the equal number in a valid fixture; the valid fixture itself is the control.
"""
import copy
import json

import pytest

import _support
from _support import pending, root

CASES = [  # contract, valid fixture, member name, the equal number
    ("bounded-deferral", "expired-deferral-refused-with-notice", "effect_withheld", 1),
    ("bounded-deferral", "expired-deferral-refused-with-notice", "effect_did_not_occur", 1),
    ("effect-reversibility", "lost-ack-stage-discard", "retry_eligible", 0),
    ("verification-report", "mutation-report-full", "context_only", 1),
    ("verification-report", "mutation-report-full", "report_only", 1),
]


def _paths(doc, key, path=()):
    if isinstance(doc, dict):
        for k, v in doc.items():
            if k == key:
                yield path + (k,)
            yield from _paths(v, key, path + (k,))
    elif isinstance(doc, list):
        for i, v in enumerate(doc):
            yield from _paths(v, key, path + (i,))


def _set(doc, path, value):
    node = doc
    for step in path[:-1]:
        node = node[step]
    node[path[-1]] = value


@pytest.mark.parametrize("contract,fixture,member,_number", CASES, ids=[c[2] for c in CASES])
def test_control_valid_fixture_with_the_boolean_is_accepted(contract, fixture, member, _number):
    doc = _support.odes_fixture(contract, fixture)
    assert list(_paths(doc, member)), "the fixture carries the member"
    assert _support.odes_contract(contract).validate(doc) == []


@pytest.mark.parametrize("contract,fixture,member,number", CASES, ids=[c[2] for c in CASES])
@pending()
def test_probe_a_number_equal_to_the_boolean_constant_is_refused(contract, fixture, member, number):
    doc = _support.odes_fixture(contract, fixture)
    path = next(_paths(doc, member))
    damaged = copy.deepcopy(doc)
    _set(damaged, path, number)
    assert json.dumps(damaged) != json.dumps(doc)
    assert _support.odes_contract(contract).validate(damaged) != []
