"""Persisted verdict vocabulary (docs/execution-contract.md). BLOCKED is a *reason*, never a status."""
from __future__ import annotations

PASS = "PASS"
FAIL = "FAIL"
INCONCLUSIVE = "INCONCLUSIVE"
NOT_RUN = "NOT RUN"
NOT_APPLICABLE = "NOT APPLICABLE"
VERDICTS = (PASS, FAIL, INCONCLUSIVE, NOT_RUN, NOT_APPLICABLE)

# Overall precedence: an observed violation stays FAIL even if other evidence is missing.
_PRECEDENCE = (FAIL, INCONCLUSIVE, NOT_RUN)


def combine(verdicts):
    """Overall verdict over the *mandatory* verdicts. Empty input is never PASS."""
    vs = list(verdicts)
    if not vs:
        return NOT_RUN
    for bad in _PRECEDENCE:
        if bad in vs:
            return bad
    # NOT APPLICABLE is not a mandatory outcome; everything left must be PASS.
    return PASS if all(v == PASS for v in vs) else INCONCLUSIVE
