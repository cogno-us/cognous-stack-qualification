"""Pytest plumbing of the CAP v0.1 G2 battery: path bootstrap (via harness), the synthetic clock of the Control Plane test harness, the row mapping, and the evidence manifest.

Every test carries `@pytest.mark.row("G2.x", "boundary")`; rows and boundaries go to the junit XML as properties and to the terminal summary. Nothing here changes a result.
At session end every file under $CAP_EVIDENCE_DIR/g2-evidence gets a SHA-256 line in $CAP_EVIDENCE_DIR/evidence-manifest.sha256.
"""
import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness as H  # noqa: E402
from harness import spy, wspy  # noqa: E402,F401  (shared fixtures)

_ROWS: dict = {}


def pytest_configure(config):
    config.addinivalue_line("markers", "row(id, boundary): the gate row (G2.1..G2.12, S, T) this test supports and the boundary it exercises")


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
            _ROWS.setdefault(rid.split(".")[0] + "." + rid.split(".")[1] if rid.startswith("G2.") else rid.split(".")[0], []).append(
                (item.nodeid, {"passed": "PASS", "failed": "FAIL", "skipped": "SKIP"}[rep.outcome], boundary))
        if call.when == "setup":
            item.user_properties.append(("row", rid))
            item.user_properties.append(("boundary", boundary))


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if not _ROWS:
        return
    tw = terminalreporter
    tw.section("CAP v0.1 G2 row mapping (gate row -> result -> tests)")
    for rid in sorted(_ROWS, key=lambda x: (x[:3], int(x.split(".")[1]) if "." in x and x.split(".")[1].isdigit() else 0)):
        results = [x[1] for x in _ROWS[rid]]
        agg = "FAIL" if "FAIL" in results else ("SKIP" if "SKIP" in results else "PASS")
        tw.write_line("%-6s %-5s (%d tests)" % (rid, agg, len(results)))


def pytest_sessionfinish(session, exitstatus):
    if H.EVIDENCE_DIR is None:
        return
    ev = H.EVIDENCE_DIR / "g2-evidence"
    # assurance labels: derived from the profile the battery actually loaded; written on pass AND on failure (the upload step runs `if: always()`)
    result = "passed" if exitstatus == 0 else "failed"
    if H.LABELS_DRAFT:
        ev.mkdir(parents=True, exist_ok=True)
        H.LABELS_DRAFT["battery_result"] = result
        (ev / "assurance-labels.json").write_text(json.dumps(H.LABELS_DRAFT, sort_keys=True, indent=1) + "\n")
    elif ev.is_dir() or exitstatus != 0:
        ev.mkdir(parents=True, exist_ok=True)
        (ev / "assurance-labels.json").write_text(json.dumps({"schema": "cap-assurance-labels/1", "lane": "cap-v02-g2", "label": "NON-PRODUCTION", "mode": "synthetic-verified",
                                                              "operational_trust": False, "authenticated_authority": False, "battery_result": "failed",
                                                              "reason": "labels test did not run"}, sort_keys=True, indent=1) + "\n")
    if not ev.is_dir():
        return
    lines = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  g2-evidence/{p.name}" for p in sorted(ev.iterdir()) if p.is_file()]
    (H.EVIDENCE_DIR / "evidence-manifest.sha256").write_text("\n".join(lines) + "\n")
