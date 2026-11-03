"""Pytest plumbing of the R2 joined-chain lane: path bootstrap (via harness), the synthetic clock of the Control Plane test harness, and the result-row recorder.

Every test marked `@pytest.mark.row("<row id>", "<case id>", kind=...)` yields ONE result row (per parametrization) appended to the JSONL named by R2_ROWS_JSONL:
  {row_id, case_id, kind, label, expected_code, observed_code, refusals[], checks[], verifier_calls, notes, nodeid, outcome}
label: PASS | FAIL | REFUSED_AS_EXPECTED | NOT_RUN | NOT_APPLICABLE. A refusal is never collapsed into PASS: a passed test that recorded a refusal is REFUSED_AS_EXPECTED.
Nothing here changes a test result.
"""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness as H  # noqa: E402  (bootstraps sys.path from SRC_DIR)

_ROWS: list = []


def pytest_configure(config):
    config.addinivalue_line("markers", "row(row_id, case_id, kind='negative'): the result row this test produces (kind: positive | negative | persistence | structure)")
    p = os.environ.get("R2_ROWS_JSONL")
    if p:
        Path(p).parent.mkdir(parents=True, exist_ok=True)
        Path(p).write_text("")


@pytest.fixture(autouse=True)
def _synthetic_clock(monkeypatch, request):
    monkeypatch.setattr(H.cp_bounded, "_now", lambda: H.NOW)
    monkeypatch.setattr(H.cp_f4, "_now", lambda: H.NOW)
    H._CTX = H._Ctx(request.node.nodeid)
    yield
    H._CTX = None


def _label(rep, ctx):
    if rep.outcome == "passed":
        return "REFUSED_AS_EXPECTED" if ctx.refusals else "PASS"
    if rep.outcome == "skipped":
        return "NOT_APPLICABLE" if "NOT_APPLICABLE" in str(getattr(rep, "longrepr", "")) else "NOT_RUN"
    return "FAIL"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    ctx = H._CTX
    outcome = yield
    rep = outcome.get_result()
    mark = item.get_closest_marker("row")
    if mark is None or ctx is None:
        return
    if not (call.when == "call" or (call.when in ("setup", "teardown") and rep.outcome != "passed")):
        return
    if call.when == "teardown" and any(r_["nodeid"] == item.nodeid for r_ in _ROWS):
        return
    row_id = mark.args[0]
    case_id = mark.args[1] if len(mark.args) > 1 else mark.kwargs.get("case_id", row_id)
    first = ctx.refusals[0] if ctx.refusals else {}
    row = dict(row_id=row_id, case_id=case_id, kind=mark.kwargs.get("kind", "negative"), label=_label(rep, ctx), outcome=rep.outcome,
               expected_code=first.get("expected_code"), observed_code=first.get("observed_code"), refusals=ctx.refusals, checks=ctx.checks,
               verifier_calls=ctx.verifier_calls, notes=ctx.notes, nodeid=item.nodeid)
    _ROWS.append(row)
    p = os.environ.get("R2_ROWS_JSONL")
    if p:
        with open(p, "a") as f:
            f.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def pytest_sessionfinish(session, exitstatus):
    p = os.environ.get("R2_ROWS_JSONL")
    if p and H._EXTRA_ROWS:
        with open(p, "a") as f:
            for r_ in H._EXTRA_ROWS:
                f.write(json.dumps(r_, sort_keys=True, default=str) + "\n")


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if not _ROWS:
        return
    tw = terminalreporter
    tw.section("R2 joined-chain result rows (row -> label -> expected/observed typed code)")
    for r_ in _ROWS:
        tw.write_line("%-6s %-20s %s  exp=%s obs=%s  [%s]" % (r_["row_id"], r_["label"], r_["case_id"], r_["expected_code"], r_["observed_code"], r_["nodeid"]))
