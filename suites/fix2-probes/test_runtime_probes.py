"""Execution runtime probes (PROBE2_RUNTIME_DIR with PROBE2_CONTROL_PLANE_DIR): result consistency after the effect is committed.

A failure raised after the effect transaction has committed leaves a committed effect and a consumed claim. The executor result
for it must not claim that nothing was attempted (status ``denied``, attempted false): the outcome is not known to the caller, so
it is reported as ``unknown`` with an unknown observed state and no retry. A failure raised before the commit leaves no effect and
an issued claim, and stays ``denied``. The statement of the producer result matrix used by the other probes is checked here
against the runtime function it restates.
"""
import dataclasses
import importlib.util
import pathlib
import sqlite3
import sys

import pytest

from _matrix import STATUSES, cells, producer_allows
from _support import pending
from conftest import checkout


@pytest.fixture(autouse=True)
def _pin():
    checkout("PROBE2_RUNTIME_DIR")
    checkout("PROBE2_CONTROL_PLANE_DIR")


def _flow():
    """The valid-flow helpers of the runtime's own atomic route tests (loaded by path, nothing written into the checkout)."""
    sys.dont_write_bytecode = True
    path = pathlib.Path(checkout("PROBE2_RUNTIME_DIR")) / "tests" / "test_atomic_route_valid_flow_identity.py"
    name = "probe2_runtime_flow"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run(tmp_path, stage=None, error=None):
    from engine.atomic_local_control_plane_executor import AtomicLocalControlPlaneExecutor
    from engine.local_authority_effect import AtomicAuthorityEffectDestination
    flow = _flow()

    class Destination(AtomicAuthorityEffectDestination):
        def _transaction_stage(self, name):
            if error is not None and name == stage:
                raise error

    env = flow.envelope()
    destination = Destination(tmp_path / "authority.sqlite", clock=lambda: flow.BASE)
    claim = flow.make_claim(env)
    destination.provision_claim(claim)
    executor = AtomicLocalControlPlaneExecutor(workflow=None, destination=destination, policy=flow.policy(env.operation))
    result = executor.execute(envelope=env, claim_id=claim.claim_id)
    with sqlite3.connect(destination.path) as db:
        effects = db.execute("select count(*) from effects").fetchone()[0]
        state = db.execute("select state from execution_claims_v1").fetchone()[0]
    return result, effects, state


def test_valid_flow_is_executed(tmp_path):
    result, effects, state = run(tmp_path)
    assert (result.status, result.attempted, result.acknowledged, result.observed_state) == ("executed", True, True, "applied")
    assert (effects, state) == (1, "consumed")


def test_failure_before_commit_stays_denied(tmp_path):
    result, effects, state = run(tmp_path, "after_effect_insert_before_commit", RuntimeError("before commit"))
    assert (result.status, result.attempted, result.observed_state) == ("denied", False, "unknown")
    assert (effects, state) == (0, "issued")


@pending()
@pytest.mark.parametrize("error", [RuntimeError("after commit"), OSError("after commit")], ids=["runtime-error", "os-error"])
def test_failure_after_commit_reports_unknown(tmp_path, error):
    result, effects, state = run(tmp_path, "after_commit", error)
    assert (effects, state) == (1, "consumed")
    assert result.status == "unknown"
    assert result.observed_state == "unknown"
    assert (result.observation or {}).get("retry_eligible") is False


def test_timeout_after_commit_reports_unknown_and_not_retryable(tmp_path):
    result, effects, state = run(tmp_path, "after_commit", TimeoutError("slow"))
    assert (effects, state) == (1, "consumed")
    assert result.status == "unknown"
    assert (result.observation or {}).get("retry_eligible") is False


@pytest.mark.parametrize("status", STATUSES)
def test_probe_matrix_statement_agrees_with_runtime(status):
    from engine.safe_executor import ExecutionResult
    from engine.producer_contract import _validate_result_state
    for cell in cells(status):
        _, attempted, acknowledged, newly, state, has_id = cell
        if attempted and status not in {"denied", "observed"} and not has_id:
            continue  # checked by the retained-binding rule, not by the state function
        result = ExecutionResult(status, "d", "e", "a" if has_id else None, attempted, acknowledged, state, newly,
                                 {"effect_id": "e"})
        try:
            _validate_result_state(result)
            allowed = True
        except ValueError:
            allowed = False
        assert allowed == producer_allows(*cell), cell
