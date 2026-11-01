"""Pure verdict computation for the mvp-chain suite: statuses come ONLY from (observations, expectations).

SPDX-License-Identifier: Apache-2.0

No component import, no I/O. ``evaluate_row`` reads one expectations row and the recorded raw observations and returns a
status in PASS / FAIL / BLOCKED / NOT RUN / NOT APPLICABLE. It never reads the process environment and has no
knowledge of any component revision, so the same expectations judge an unpatched and a patched Control Plane identically.
"""
from __future__ import annotations

PASS, FAIL, BLOCKED, NOT_RUN, NOT_APPLICABLE = "PASS", "FAIL", "BLOCKED", "NOT RUN", "NOT APPLICABLE"
_MISSING = object()


def lookup(observations: dict, path: str):
    node = observations
    for part in path.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return _MISSING
    return node


def _holds(value, op: str, expected) -> bool:
    if value is _MISSING:
        return False
    if op == "eq":
        return value == expected and type(value) is type(expected) if isinstance(expected, bool) else value == expected
    if op == "ne":
        return value != expected
    if op == "in":
        return value in expected
    if op == "not_in":
        return value not in expected
    if op == "true":
        return value is True
    if op == "false":
        return value is False
    if op == "empty":
        return isinstance(value, (list, tuple, dict, str)) and len(value) == 0
    if op == "nonempty":
        return isinstance(value, (list, tuple, dict, str)) and len(value) > 0
    if op == "contains":
        return isinstance(value, (list, tuple, str, dict)) and expected in value
    if op == "contains_all":
        return isinstance(value, (list, tuple)) and all(item in value for item in expected)
    if op == "not_contains":
        return isinstance(value, (list, tuple, str, dict)) and expected not in value
    if op == "gte":
        return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= expected
    if op == "lte":
        return isinstance(value, (int, float)) and not isinstance(value, bool) and value <= expected
    if op == "is_null":
        return value is None
    raise ValueError(f"unknown operator {op!r}")


def _check(observations: dict, predicate: dict) -> bool:
    return _holds(lookup(observations, predicate["obs"]), predicate["op"], predicate.get("value"))


def evaluate_row(row: dict, observations: dict) -> dict:
    """Return ``{"id", "status", "reason", "failed": [...]}``; the reason names the first deciding fact."""
    out = {"id": row["id"], "mandatory": row.get("mandatory", True), "title": row["title"], "status": None, "reason": "", "failed": []}
    scenario = observations.get(row["scenario"], _MISSING)
    if scenario is _MISSING:
        out.update(status=NOT_RUN, reason=f"no observation record for scenario {row['scenario']!r}")
        return out
    if isinstance(scenario, dict) and scenario.get("status") == "blocked":
        out.update(status=BLOCKED, reason=str(scenario.get("blocked_reason", "scenario blocked")))
        return out
    if any(_check(observations, p) for p in row.get("not_applicable_if", [])):
        out.update(status=NOT_APPLICABLE, reason="not_applicable_if held: " + "; ".join(
            f"{p['obs']} {p['op']} {p.get('value')!r}" for p in row["not_applicable_if"] if _check(observations, p)))
        return out
    for p in row.get("blocked_if", []):
        if _check(observations, p):
            out.update(status=BLOCKED, reason=f"blocked_if held: {p['obs']} {p['op']} {p.get('value')!r}")
            return out
    for p in row["all"]:
        if not _check(observations, p):
            seen = lookup(observations, p["obs"])
            out["failed"].append({"obs": p["obs"], "op": p["op"], "expected": p.get("value"),
                                  "observed": "<missing>" if seen is _MISSING else seen})
    if out["failed"]:
        out.update(status=FAIL, reason=f"{len(out['failed'])} predicate(s) did not hold")
    else:
        out.update(status=PASS, reason="every predicate held on the recorded observations")
    return out


def evaluate_all(expectations: dict, observations: dict) -> list[dict]:
    return [evaluate_row(row, observations) for row in expectations["rows"]]


def counts(results: list[dict]) -> dict:
    tally = {PASS: 0, FAIL: 0, BLOCKED: 0, NOT_RUN: 0, NOT_APPLICABLE: 0}
    for item in results:
        tally[item["status"]] += 1
    return tally
