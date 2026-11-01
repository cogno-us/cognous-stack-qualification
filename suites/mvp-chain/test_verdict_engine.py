"""Self-checks of verdict.py (pure): each status is reachable and a missing or false observation never yields PASS.

SPDX-License-Identifier: Apache-2.0
"""
import verdict

OBS = {"s": {"status": "ran", "a": 1, "l": [1, 2], "f": False, "n": None, "e": []}}


def row(**kw):
    base = {"id": "X", "title": "t", "scenario": "s", "all": []}
    base.update(kw)
    return verdict.evaluate_row(base, OBS)["status"]


def test_pass_fail_and_missing_is_fail():
    assert row(all=[{"obs": "s.a", "op": "eq", "value": 1}, {"obs": "s.l", "op": "contains_all", "value": [1, 2]}, {"obs": "s.f", "op": "false"},
                    {"obs": "s.n", "op": "is_null"}, {"obs": "s.e", "op": "empty"}]) == verdict.PASS
    assert row(all=[{"obs": "s.a", "op": "eq", "value": 2}]) == verdict.FAIL
    assert row(all=[{"obs": "s.absent", "op": "false"}]) == verdict.FAIL
    assert row(all=[{"obs": "s.absent", "op": "empty"}]) == verdict.FAIL


def test_not_run_blocked_not_applicable():
    assert verdict.evaluate_row({"id": "X", "title": "t", "scenario": "nope", "all": []}, OBS)["status"] == verdict.NOT_RUN
    assert verdict.evaluate_row({"id": "X", "title": "t", "scenario": "b", "all": []}, {"b": {"status": "blocked", "blocked_reason": "r"}})["status"] == verdict.BLOCKED
    assert row(blocked_if=[{"obs": "s.a", "op": "eq", "value": 1}], all=[{"obs": "s.a", "op": "eq", "value": 2}]) == verdict.BLOCKED
    assert row(not_applicable_if=[{"obs": "s.a", "op": "eq", "value": 1}], all=[{"obs": "s.a", "op": "eq", "value": 2}]) == verdict.NOT_APPLICABLE
