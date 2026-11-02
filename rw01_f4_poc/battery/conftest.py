"""Pytest plumbing of the RW-01-F4-PoC battery: path bootstrap, the synthetic clock of the Control Plane/Registry test harness, and the N-row mapping.

Every test carries `@pytest.mark.row("N07", "boundary text")`; the rows and boundaries go to the junit XML as properties and to the terminal summary (the
N01-N28 mapping table). Nothing here changes a result.
"""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness as H  # noqa: E402  (bootstraps sys.path from RW01_SRC_DIR)

_ROWS: dict = {}


def pytest_configure(config):
    config.addinivalue_line("markers", "row(id, boundary): the sprint row N01..N28 (or F-n finding) this test supports and the boundary it exercises")
    config.addinivalue_line("markers", "evidence(kind): REAL (unbridged real components) | BRIDGED (real F4 evidence grafted onto a Replay-valid record) | STATIC | SUBPROCESS")


@pytest.fixture(autouse=True)
def _synthetic_clock(monkeypatch):
    monkeypatch.setattr(H.cp_bounded, "_now", lambda: H.NOW)
    monkeypatch.setattr(H.cp_f4, "_now", lambda: H.NOW)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    for mark in item.iter_markers("row"):
        rid = mark.args[0]
        boundary = mark.args[1] if len(mark.args) > 1 else ""
        kinds = [m.args[0] for m in item.iter_markers("evidence") if m.args]
        if call.when == "call" or (call.when == "setup" and rep.outcome != "passed"):
            result = {"passed": "PASS", "failed": "FAIL", "skipped": "SKIP"}[rep.outcome]
            if rep.outcome == "skipped" and "BLOCKED" in str(getattr(rep, "longrepr", "")):
                result = "BLOCKED"
            _ROWS.setdefault(rid, []).append((item.nodeid, result, boundary, ",".join(kinds)))
        if call.when == "setup":
            item.user_properties.append(("row", rid))
            item.user_properties.append(("boundary", boundary))
            item.user_properties.append(("evidence", ",".join(kinds)))


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if not _ROWS:
        return
    tw = terminalreporter
    tw.section("RW-01-F4-PoC N-row mapping (row -> result -> nodeid -> boundary exercised)")
    order = sorted(_ROWS, key=lambda k: (k[0] != "N", k))
    for rid in order:
        results = [x[1] for x in _ROWS[rid]]
        agg = "FAIL" if "FAIL" in results else ("BLOCKED" if "BLOCKED" in results else ("SKIP" if "SKIP" in results else "PASS"))
        tw.write_line("%-4s %-7s (%d tests)" % (rid, agg, len(results)))
        for nodeid, result, boundary, kinds in _ROWS[rid]:
            tw.write_line("      %-7s %s  [%s]  {%s}" % (result, nodeid, kinds, boundary))
    out = os.environ.get("RW01_ROWS_JSON")
    if out:
        Path(out).write_text(json.dumps({k: [dict(nodeid=a, result=b, boundary=c_, evidence=d) for a, b, c_, d in v] for k, v in _ROWS.items()}, indent=1, sort_keys=True))
