"""V08 F-A1 qualification (Registry r08-v2 Amendment 4; plan docs/f-a1-authorization-pin/qualification-plan.md, 30 counted executions).

Shared environment gate, budget ledger and raw-evidence capture. The suite FAILS (never skips) when a component checkout is missing or not at its
exact pin. Verdicts: HELD / BREACH / CHARACTERIZED / INCONCLUSIVE / BLOCKED. A case that cannot run for lack of an OS facility is INCONCLUSIVE.

Independence statement: designed by the Lead Builder session of the same engineering organization from the adopted plan; NOT independent external
qualification. Historical V08 evidence (results/v08-tier1/**, PR #235) is never edited by this suite.
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
    "registry": "1a4de32605519c505142b1ba3a57fa5b259b0b2c",       # Amendment 4 adopted
    "control_plane": "d66ae07fa240510efdcc11ed4b3e1189dcefc822",   # merge commit of cognous-control-plane#86 (tree identical to PR head 0fd44d03, which is its ancestor)
    "runtime": "3873a61b5dd1ca2f8102d355888e59b5cd5a5456",         # cognous-execution-runtime#149 head: ad1805e2 code tree + the docs-only F3 record
}
HISTORICAL_V08 = "7b72de9ac7e4898c0f9bdad3e9b337775cc9c543"   # immutable reference: cognous-stack-qualification#235 head (failed historical assessment, preserved there, not on this branch)
# The one historical helper this suite reuses, vendored byte-for-byte from the blob at HISTORICAL_V08 (suites/tier1-v08/authority/_wf.py).
HISTORICAL_WF_SHA256 = "a36dc8f81f4789cc795abf43f8f510acc68eac5acfee07806c7a0e237c60d2a7"
LOCAL_BUDGET = 30
REPO = Path(__file__).resolve().parents[2]
COMPONENTS = Path(os.environ["V08_COMPONENTS_DIR"]).resolve() if os.environ.get("V08_COMPONENTS_DIR") else None
RESULTS_ROOT = Path(os.environ.get("V08_FA1_RESULTS_DIR", str(REPO / "results" / "v08-fa1"))).resolve()
ENFORCE_BUDGET = os.environ.get("V08_BUDGET_ENFORCE") == "1"      # local runs; CI is separate and is not counted against the local budget
WORKER = os.environ.get("V08_WORKER", "ci" if os.environ.get("CI") else "lead")
_CASES: dict = {}


def head_of(path: Path) -> str:
    return subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()


def pytest_configure(config):
    config.addinivalue_line("markers", "os_isolation: real OS-identity case; needs root, useradd and setpriv (otherwise SKIP = INCONCLUSIVE, never PASS)")
    problems = []
    if COMPONENTS is None or not COMPONENTS.is_dir():
        problems.append("V08_COMPONENTS_DIR is not set to a directory of pinned component checkouts")
    else:
        for name, pin in PINS.items():
            try:
                got = head_of(COMPONENTS / name)
            except Exception as exc:  # noqa: BLE001
                problems.append(f"{name}: cannot read checkout at {COMPONENTS / name}: {exc}")
                continue
            if got != pin:
                problems.append(f"{name}: checkout is {got}, expected pin {pin}")
    import hashlib
    wf = Path(__file__).resolve().parent / "_historical" / "_wf.py"
    got_wf = hashlib.sha256(wf.read_bytes()).hexdigest() if wf.is_file() else None
    if got_wf != HISTORICAL_WF_SHA256:
        problems.append(f"vendored historical helper {wf} is {got_wf}, expected the blob digest {HISTORICAL_WF_SHA256} from {HISTORICAL_V08}")
    if problems:
        raise pytest.UsageError("F-A1 component pins not satisfied (this suite never skips): " + "; ".join(problems))
    os.environ["OCS_REGISTRY_PIN_DIR"] = str(COMPONENTS / "registry")
    for p in (COMPONENTS / "runtime" / "tests", COMPONENTS / "runtime", COMPONENTS / "control_plane" / "src"):
        sys.path.insert(0, str(p))


def pytest_collection_modifyitems(session, config, items):
    if not ENFORCE_BUDGET:
        return
    ledger = RESULTS_ROOT / "ledger.jsonl"
    prior = sum(1 for _ in open(ledger)) if ledger.exists() else 0
    if prior + len(items) > LOCAL_BUDGET:
        raise pytest.UsageError(f"F-A1 local budget: {prior} already executed + {len(items)} selected > {LOCAL_BUDGET}; nothing was run")


@pytest.fixture
def ev(request):
    record = {"case": request.node.nodeid, "scenario": None, "expected": None, "observed": {}, "verdict": None, "mandatory": True, "note": None}
    request.node._fa1_record = record
    return record


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    rec = getattr(item, "_fa1_record", None)
    if rep.when == "call" or (rep.when == "setup" and rep.outcome != "passed"):
        entry = rec or {"case": item.nodeid, "scenario": None, "expected": None, "observed": {}, "mandatory": True}
        entry["outcome"] = "SKIP" if rep.outcome == "skipped" else rep.outcome.upper()
        if rep.outcome == "skipped":
            entry["verdict"] = "INCONCLUSIVE"
            entry["note"] = (entry.get("note") or "") + " skipped: " + str(rep.longrepr)[-300:]
        if rep.failed:
            entry["failure"] = str(rep.longrepr)[-2500:]
        _CASES[item.nodeid] = entry


def pytest_sessionfinish(session, exitstatus):
    if COMPONENTS is None or not _CASES:
        return
    import pydantic
    cases = list(_CASES.values())
    counts = {k: sum(1 for c in cases if c["outcome"] == k) for k in ("PASSED", "FAILED", "SKIP")}
    verdicts: dict = {}
    for c in cases:
        verdicts[c.get("verdict") or "NONE"] = verdicts.get(c.get("verdict") or "NONE", 0) + 1
    doc = {
        "schema": "v08-fa1-results/1", "worker": WORKER,
        "claim": "Test design and execution by the Lead Builder session of the same engineering organization; not independent external qualification.",
        "exact_pins": {k: head_of(COMPONENTS / k) for k in PINS},
        "harness_commit": os.environ.get("GITHUB_SHA") or subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
        "environment": {"python": sys.version.split()[0], "platform": platform.platform(), "pydantic": pydantic.VERSION, "pytest": pytest.__version__,
                        "euid": os.geteuid()},
        "counts": {"executed": len(cases), **counts}, "verdicts": verdicts, "historical_v08_assessment": HISTORICAL_V08, "cases": cases,
    }
    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
    (RESULTS_ROOT / "runs").mkdir(exist_ok=True)
    n = len(list((RESULTS_ROOT / "runs").glob("run-*.json"))) + 1
    doc["run_number"] = n
    text = json.dumps(doc, indent=1, sort_keys=True, default=str)
    (RESULTS_ROOT / "runs" / f"run-{n:03d}.json").write_text(text)      # every local run is retained; nothing is overwritten
    (RESULTS_ROOT / "results.json").write_text(text)
    if ENFORCE_BUDGET:
        with open(RESULTS_ROOT / "ledger.jsonl", "a") as fh:
            for c in cases:
                fh.write(json.dumps({"case": c["case"], "scenario": c.get("scenario"), "outcome": c["outcome"], "verdict": c.get("verdict"), "worker": WORKER}) + "\n")
