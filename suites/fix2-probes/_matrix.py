"""The result status x flags x observation matrix of the runtime producer, restated as a pure function.

Source of the statement: ``engine/producer_contract.py`` (``_validate_result_state`` and the attempt-identity rule in
``_validate_retained_bindings``) of the runtime. ``test_runtime_probes.py`` checks, when a runtime checkout is given, that
this statement agrees with the runtime function for every cell, so the statement cannot drift from its source unnoticed.
"""
import itertools

STATUSES = ("denied", "failed", "partial", "unknown", "executed", "observed", "reconciled")
OBSERVED_STATES = ("applied", "partial", "absent", "unknown")
ATTEMPT_REQUIRED = {"failed", "partial", "unknown", "executed", "reconciled"}


def producer_allows(status, attempted, acknowledged, newly_executed, observed_state, has_attempt_id):
    if status in ATTEMPT_REQUIRED and not attempted:
        return False
    if status == "observed" and (attempted or acknowledged or newly_executed or has_attempt_id):
        return False
    if acknowledged and not attempted:
        return False
    if newly_executed and not (acknowledged and status in {"executed", "partial", "unknown"}):
        return False
    if status in {"denied", "failed"} and (acknowledged or newly_executed or observed_state != "unknown"):
        return False
    if status == "executed" and not (acknowledged and newly_executed and observed_state == "applied"):
        return False
    if status == "reconciled" and (newly_executed or observed_state != "applied"):
        return False
    if status == "partial" and observed_state != "partial":
        return False
    # an attempted result (other than denied or observed) names its attempt
    if attempted and status not in {"denied", "observed"} and not has_attempt_id:
        return False
    return True


def cells(status):
    """Every flag and state combination for one status, each with the observation that is coherent with it: a validated
    observation (member ``state``) where the status carries one, a route-B recovery report for the effect-free ``observed``
    result, none where the observed state is unknown for a denied or failed result. Combinations whose observation would
    itself be incoherent (an unknown result carrying a positive validated state; an observed result with a non-positive
    report) are left out: they are not what this matrix is about."""
    for attempted, acknowledged, newly in itertools.product((False, True), repeat=3):
        for state in OBSERVED_STATES:
            for has_id in (True, False):
                if status == "observed" and state not in ("applied", "partial"):
                    continue
                if status == "unknown" and state not in ("absent", "unknown"):
                    continue
                yield (status, attempted, acknowledged, newly, state, has_id)


def build_result(cell, base):
    """``base`` is a valid executed lifecycle document; return a copy carrying ``cell`` as its execution result."""
    import copy
    status, attempted, acknowledged, newly, state, has_id = cell
    doc = copy.deepcopy(base)
    terminal = {"observed": "executed"}.get(status, status)
    sequence = ["attempted"] + (["executed", "reconciled"] if terminal == "reconciled" else [terminal])
    doc["attempt_events"] = [
        {"event_id": i + 1, "attempt_id": "syn-attempt-1", "status": s, "error": "x" if s == "failed" else None,
         "created_at": 1000.0 + i}
        for i, s in enumerate(sequence)]
    result = doc["execution_result"]
    result.update(status=status, attempted=attempted, acknowledged=acknowledged, newly_executed=newly,
                  observed_state=state, attempt_id="syn-attempt-1" if has_id else None, error=None)
    if status == "observed":
        result["observation"] = {"status": state, "claim_state": "consumed", "retry_eligible": False,
                                 "effect_id": "syn-effect-1", "operation_digest": "sha256:" + "d" * 64}
    elif status in ("denied", "failed") and state == "unknown":
        result["observation"] = None
    else:
        result["observation"] = {"effect_id": "syn-effect-1", "state": state, "observed_at": "2026-01-01T00:00:05Z"}
    return doc
