"""V06 end-to-end governed-effect qualification: environment gate and raw-evidence capture.

The suite FAILS (never skips) when a component checkout is missing or not at its accepted pin: a mandatory dependency
failure must not turn into a skipped, or silently passing, run.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from pathlib import Path

import pytest

PINS = {
    "registry": "943ab1831e39fadac1eb2a414ae322ccfa09bc6a",
    "control_plane": "1bee3696ee6cd8037d142cdbcdb6020e052b0480",
    "runtime": "4199a6c793cd9ec37a5fd451f7d99265dcf634fd",
    "control_plane_legacy": "e66e5f163c5d5c112ff345a2f332b4c3893ee183",  # intentionally older fixture: no successor profile
}
COMPONENTS = Path(os.environ.get("V06_COMPONENTS_DIR", "")).resolve() if os.environ.get("V06_COMPONENTS_DIR") else None
EVIDENCE_DIR = Path(os.environ.get("V06_EVIDENCE_DIR", "v06-evidence")).resolve()
_CASES: list = []


def head_of(path: Path) -> str:
    return subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()


def pytest_configure(config):
    problems = []
    if COMPONENTS is None or not COMPONENTS.is_dir():
        problems.append("V06_COMPONENTS_DIR is not set to a directory of pinned component checkouts")
    else:
        for name, pin in PINS.items():
            path = COMPONENTS / name
            try:
                got = head_of(path)
            except Exception as exc:  # noqa: BLE001 - any failure to identify the checkout is a hard error
                problems.append(f"{name}: cannot read checkout at {path}: {exc}")
                continue
            if got != pin:
                problems.append(f"{name}: checkout is {got}, expected pin {pin}")
    if problems:
        raise pytest.UsageError("V06 component pins not satisfied (this suite never skips): " + "; ".join(problems))
    os.environ["OCS_REGISTRY_PIN_DIR"] = str(COMPONENTS / "registry")
    for p in (COMPONENTS / "runtime" / "tests", COMPONENTS / "runtime", COMPONENTS / "control_plane" / "src"):
        sys.path.insert(0, str(p))


@pytest.fixture
def ev(request):
    """Per-case evidence dictionary: filled by the test, written with the outcome at teardown."""
    record = {"case": request.node.nodeid, "expected": None, "observed": {}}
    request.node._v06_record = record
    return record


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    rec = getattr(item, "_v06_record", None)
    if rep.when == "call" or (rep.when == "setup" and rep.outcome != "passed"):
        entry = rec or {"case": item.nodeid, "expected": None, "observed": {}}
        entry["outcome"] = rep.outcome.upper() if rep.outcome != "skipped" else "SKIP"
        if rep.failed:
            entry["failure"] = str(rep.longrepr)[-2000:]
        _CASES.append(entry)


def pytest_sessionfinish(session, exitstatus):
    if COMPONENTS is None:
        return
    import pydantic
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    counts = {k: sum(1 for c in _CASES if c["outcome"] == k) for k in ("PASSED", "FAILED", "SKIP")}
    doc = {
        "schema": "v06-e2e-results/1",
        "claim": "Bounded synthetic local qualification only. Not independent attestation, not production security qualification.",
        "exact_pins": {k: head_of(COMPONENTS / k) for k in PINS},
        "harness_commit": os.environ.get("GITHUB_SHA") or subprocess.run(
            ["git", "-C", str(Path(__file__).resolve().parent), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
        "environment": {"python": sys.version.split()[0], "platform": platform.platform(), "pydantic": pydantic.VERSION,
                        "pytest": pytest.__version__},
        "counts": {"executed": len(_CASES), **counts, "BLOCKED": 0},
        "cases": _CASES,
    }
    (EVIDENCE_DIR / "results.json").write_text(json.dumps(doc, indent=1, sort_keys=True, default=str))
