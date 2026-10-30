"""V08 Tier 1 qualification: shared environment gate, budget ledger and raw-evidence capture (lead-builder owned).

The suite FAILS (never skips) when a component checkout is missing or not at its frozen pin. Workers add tests under their own area directory
(authority / atomicity / trust) and must not edit this file. Each area writes `results.json` and appends to `ledger.jsonl` in its own results
directory, so no two workers ever write the same evidence file.

Independence statement: tests are designed from the frozen contracts by qualification workers; the lead and the workers are all AI sessions of the
same engineering organization. This is independent test design within the same organization, NOT independent external qualification, and it does
not satisfy the plan's "independent lead and oracle" requirement for Tier 1.
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
    "registry": "a1169a05afb917862f4a0f5865e278f4168ed171",
    "control_plane": "1bee3696ee6cd8037d142cdbcdb6020e052b0480",
    "runtime": "ac247dafbce3aacde37695575d457cf958b22560",
    "control_plane_legacy": "e66e5f163c5d5c112ff345a2f332b4c3893ee183",  # intentionally older fixture: no successor profile
}
V07_QUALIFICATION = "90e0e56e69448eadb43ea3df2017be189e09e3bb"
AREAS = ("authority", "atomicity", "trust")
AREA_BUDGET = {"authority": 15, "atomicity": 15, "trust": 15}  # global budget 50 = 45 + 5 integration reserve held by the lead
REPO = Path(__file__).resolve().parents[2]
COMPONENTS = Path(os.environ["V08_COMPONENTS_DIR"]).resolve() if os.environ.get("V08_COMPONENTS_DIR") else None
RESULTS_ROOT = Path(os.environ.get("V08_RESULTS_DIR", str(REPO / "results" / "v08-tier1"))).resolve()
ENFORCE_BUDGET = os.environ.get("V08_BUDGET_ENFORCE") == "1"  # local runs; CI is a separate gate and is not counted against the local budget
WORKER = os.environ.get("V08_WORKER", "ci" if os.environ.get("CI") else "unknown")
_CASES: dict = {}


def head_of(path: Path) -> str:
    return subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()


def area_of(nodeid: str):
    parts = nodeid.replace("\\", "/").split("/")
    for a in AREAS:
        if a in parts:
            return a
    return None


def pytest_configure(config):
    problems = []
    if COMPONENTS is None or not COMPONENTS.is_dir():
        problems.append("V08_COMPONENTS_DIR is not set to a directory of pinned component checkouts")
    else:
        for name, pin in PINS.items():
            try:
                got = head_of(COMPONENTS / name)
            except Exception as exc:  # noqa: BLE001 - any failure to identify the checkout is a hard error
                problems.append(f"{name}: cannot read checkout at {COMPONENTS / name}: {exc}")
                continue
            if got != pin:
                problems.append(f"{name}: checkout is {got}, expected pin {pin}")
    anc = subprocess.run(["git", "-C", str(REPO), "merge-base", "--is-ancestor", V07_QUALIFICATION, "HEAD"], capture_output=True)
    if anc.returncode != 0:
        problems.append(f"qualification V07 {V07_QUALIFICATION} is not an ancestor of this checkout")
    if problems:
        raise pytest.UsageError("V08 component pins not satisfied (this suite never skips): " + "; ".join(problems))
    os.environ["OCS_REGISTRY_PIN_DIR"] = str(COMPONENTS / "registry")
    for p in (COMPONENTS / "runtime" / "tests", COMPONENTS / "runtime", COMPONENTS / "control_plane" / "src"):
        sys.path.insert(0, str(p))


def pytest_collection_modifyitems(session, config, items):
    """Local budget gate: prior ledger entries plus the selected items (parametrized cases individually) must fit the area budget."""
    if not ENFORCE_BUDGET:
        return
    by_area: dict = {}
    for it in items:
        by_area.setdefault(area_of(it.nodeid), []).append(it)
    for area, its in by_area.items():
        if area is None:
            raise pytest.UsageError("a V08 test outside authority/atomicity/trust cannot be counted against the budget")
        ledger = RESULTS_ROOT / area / "ledger.jsonl"
        prior = sum(1 for _ in open(ledger)) if ledger.exists() else 0
        if prior + len(its) > AREA_BUDGET[area]:
            raise pytest.UsageError(f"V08 budget for {area}: {prior} already executed + {len(its)} selected > {AREA_BUDGET[area]}; nothing was run")


@pytest.fixture
def ev(request):
    """Per-case evidence: expected oracle, observed facts, verdict in {HELD, BREACH, CHARACTERIZED, INCONCLUSIVE, BLOCKED}, `mandatory` flag."""
    record = {"case": request.node.nodeid, "expected": None, "observed": {}, "verdict": None, "mandatory": True, "note": None}
    request.node._v08_record = record
    return record


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    rec = getattr(item, "_v08_record", None)
    if rep.when == "call" or (rep.when == "setup" and rep.outcome != "passed"):
        entry = rec or {"case": item.nodeid, "expected": None, "observed": {}, "mandatory": True}
        entry["outcome"] = "SKIP" if rep.outcome == "skipped" else rep.outcome.upper()
        if rep.failed:
            entry["failure"] = str(rep.longrepr)[-2500:]
        _CASES[item.nodeid] = entry


def pytest_sessionfinish(session, exitstatus):
    if COMPONENTS is None or not _CASES:
        return
    import pydantic
    by_area: dict = {}
    for c in _CASES.values():
        by_area.setdefault(area_of(c["case"]), []).append(c)
    for area, cases in by_area.items():
        if area is None:
            continue
        out = RESULTS_ROOT / area
        out.mkdir(parents=True, exist_ok=True)
        counts = {k: sum(1 for c in cases if c["outcome"] == k) for k in ("PASSED", "FAILED", "SKIP")}
        verdicts: dict = {}
        for c in cases:
            verdicts[c.get("verdict") or "NONE"] = verdicts.get(c.get("verdict") or "NONE", 0) + 1
        doc = {
            "schema": "v08-tier1-results/1", "area": area, "worker": WORKER,
            "claim": "Independent TEST DESIGN by an AI qualification worker of the same engineering organization; not independent external qualification.",
            "exact_pins": {k: head_of(COMPONENTS / k) for k in PINS},
            "harness_commit": os.environ.get("GITHUB_SHA") or subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
            "environment": {"python": sys.version.split()[0], "platform": platform.platform(), "pydantic": pydantic.VERSION, "pytest": pytest.__version__},
            "counts": {"executed": len(cases), **counts, "BLOCKED": sum(1 for c in cases if c.get("verdict") == "BLOCKED")},
            "verdicts": verdicts, "qualification_v07_pin": V07_QUALIFICATION, "cases": cases,
        }
        (out / "runs").mkdir(exist_ok=True)
        n = len(list((out / "runs").glob("run-*.json"))) + 1
        doc["run_number"] = n
        text = json.dumps(doc, indent=1, sort_keys=True, default=str)
        (out / "runs" / f"run-{n:03d}.json").write_text(text)  # every local run is retained; nothing is overwritten
        (out / "results.json").write_text(text)  # latest session of this area (CI starts from an empty directory)
        if ENFORCE_BUDGET:
            with open(out / "ledger.jsonl", "a") as fh:
                for c in cases:
                    fh.write(json.dumps({"case": c["case"], "outcome": c["outcome"], "verdict": c.get("verdict"), "worker": WORKER}) + "\n")
