"""Batch-1 adversarial tests (T01-T20): wiring to component checkouts named by environment variables (never modified).

SPDX-License-Identifier: Apache-2.0

The checkouts and the revisions they must be at are listed in ../components.json (ADV_CONTROL_PLANE_DIR, ADV_RUNTIME_DIR,
ADV_VERIFIER_DIR, ADV_REPLAY_DIR, ADV_EVIDENCE_PACK_DIR, ADV_ODES_DIR, ADV_HUB_DIR). A test that needs a checkout that is not
named FAILS; nothing skips (a test that did not run proves nothing). A checkout at another HEAD fails too, unless
ADV_ALLOW_REVISION_DRIFT=1, in which case the actual heads are written into the observations.

These tests are NOT scenario-catalogue entries and NEVER feed the v1_validation verdict. Their result vocabulary is the plan's:
prevented, detected only, reproduced failure, inconclusive, not applicable, not tested. ADV_REPORT_DIR, when set, receives
observations.json (one row per scenario with its result and what it does not prove).
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
ADV = HERE.parent
ROOT = ADV.parents[1]
COMPONENTS = json.loads((ADV / "components.json").read_text(encoding="utf-8"))["components"]
OBSERVATIONS: list[dict] = []


def _paths() -> dict[str, str]:
    return {k: os.environ[v["env"]] for k, v in COMPONENTS.items() if os.environ.get(v["env"])}


PATHS = _paths()


def _wire() -> None:
    for path in (HERE, ROOT / "suites" / "operation-identity", ROOT / "suites"):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    cp, rt = PATHS.get("control_plane"), PATHS.get("runtime")
    # control plane root last so its `tests` package (the synthetic fixtures) wins over any runtime `tests`
    for path in ([rt] if rt else []) + ([os.path.join(cp, "src"), cp] if cp else []):
        if path not in sys.path:
            sys.path.insert(0, path)


_wire()


def head(path: str) -> str:
    return subprocess.check_output(["git", "-C", path, "rev-parse", "HEAD"], text=True).strip()


HEADS: dict[str, str] = {}


def require(*names: str) -> dict[str, pathlib.Path]:
    """Fail (never skip) unless every named checkout is present and at its listed revision."""
    out = {}
    for name in names:
        spec = COMPONENTS[name]
        if name not in PATHS:
            pytest.fail(f"{spec['env']} not set: this adversarial test needs {spec['repo']} at {spec['revision'][:8]}")
        if name not in HEADS:
            HEADS[name] = head(PATHS[name])
        if HEADS[name] != spec["revision"] and os.environ.get("ADV_ALLOW_REVISION_DRIFT") != "1":
            pytest.fail(f"{spec['repo']} checkout is at {HEADS[name][:8]}, the batch attacks {spec['revision'][:8]}")
        out[name] = pathlib.Path(PATHS[name])
    return out


@pytest.fixture
def cprt():
    """Control plane and runtime checkouts (most tests)."""
    return require("control_plane", "runtime")


def observe(test_id: str, scenario: str, result: str, *, does_not_prove: str, detail=None) -> None:
    """Record one scenario outcome in the plan's result vocabulary (written out at session end when ADV_REPORT_DIR is set)."""
    assert result in {"prevented", "detected only", "reproduced failure", "inconclusive", "not applicable", "not tested"}, result
    OBSERVATIONS.append({"test": test_id, "scenario": scenario, "result": result, "does_not_prove": does_not_prove,
                         "detail": detail})


@pytest.fixture(scope="session", autouse=True)
def _write_observations():
    yield
    base = os.environ.get("ADV_REPORT_DIR")
    if base and OBSERVATIONS:
        out = pathlib.Path(base)
        out.mkdir(parents=True, exist_ok=True)
        doc = {"claim": "adversarial batch 1; synthetic; not release evidence; does not feed the v1_validation verdict",
               "heads": HEADS, "observations": OBSERVATIONS}
        (out / "observations.json").write_text(json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
