"""Pytest plumbing of the CAP v0.1 G1 battery: path bootstrap (via harness), the synthetic clock of the Control Plane test harness, and the row mapping.

Every test carries `@pytest.mark.row("N1.a", "boundary")`; rows and boundaries go to the junit XML as properties and to the terminal summary. Nothing here changes a result.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness as H  # noqa: E402

_ROWS: dict = {}


def pytest_configure(config):
    config.addinivalue_line("markers", "row(id, boundary): the gate row (N1..N4, P1, S) this test supports and the boundary it exercises")


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
        if call.when == "call" or (call.when == "setup" and rep.outcome != "passed"):
            _ROWS.setdefault(rid.split(".")[0], []).append((item.nodeid, {"passed": "PASS", "failed": "FAIL", "skipped": "SKIP"}[rep.outcome], boundary))
        if call.when == "setup":
            item.user_properties.append(("row", rid))
            item.user_properties.append(("boundary", boundary))


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if not _ROWS:
        return
    tw = terminalreporter
    tw.section("CAP v0.1 G1 row mapping (gate row -> result -> tests)")
    for rid in sorted(_ROWS):
        results = [x[1] for x in _ROWS[rid]]
        agg = "FAIL" if "FAIL" in results else ("SKIP" if "SKIP" in results else "PASS")
        tw.write_line("%-3s %-5s (%d tests)" % (rid, agg, len(results)))
