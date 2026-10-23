"""Worker D2 route-B end-to-end tests: wiring only (new file; reuses suites/operation-identity/_oi_flow.py unmodified).

D2_CONTROL_PLANE_DIR  Control Plane checkout (its tests/ package supplies the synthetic fixtures)
D2_RUNTIME_DIR        Runtime checkout
D2_CONTROL_PLANE_PIN  expected Control Plane HEAD; must be one of the two accepted tuples below (default 0a41faa9...)
Every test FAILS (never skips) unless: both variables are set; Runtime HEAD == ec728da6...; Control Plane HEAD == D2_CONTROL_PLANE_PIN;
both checkouts are git checkouts with a clean working tree (untracked, non-ignored files count as dirty); pydantic >= 2.12.
Local builder evidence, not wired to CI. Not a Qualification verdict.
SPDX-License-Identifier: Apache-2.0
"""
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RUNTIME_PIN = "ec728da6dc301a664b331ac8986afd6e850a1273"
CP_PINS = {"0a41faa972699f7ec3063967a14cd9bdd3e67d27", "7a4bcd40b3b49e61ff3c294dcca53b52f460b22c"}
_MISSING = [v for v in ("D2_CONTROL_PLANE_DIR", "D2_RUNTIME_DIR") if not os.environ.get(v)]


def _git(path, *args):
    return subprocess.run(["git", "-C", path, *args], check=True, capture_output=True, text=True, timeout=30).stdout.strip()


def _pin_problems():
    problems = []
    cp_pin = os.environ.get("D2_CONTROL_PLANE_PIN", "0a41faa972699f7ec3063967a14cd9bdd3e67d27")
    if cp_pin not in CP_PINS:
        problems.append(f"D2_CONTROL_PLANE_PIN {cp_pin} is not an accepted Control Plane pin")
    for label, var, pin in (("Control Plane", "D2_CONTROL_PLANE_DIR", cp_pin), ("Runtime", "D2_RUNTIME_DIR", RUNTIME_PIN)):
        path = os.environ[var]
        try:
            head, dirty = _git(path, "rev-parse", "HEAD"), _git(path, "status", "--porcelain")
        except Exception as exc:
            problems.append(f"{label}: not a readable git checkout ({type(exc).__name__})")
            continue
        if head != pin:
            problems.append(f"{label} HEAD {head} != pin {pin}")
        if dirty:
            problems.append(f"{label} checkout is not pristine")
    try:
        import pydantic
        major_minor = tuple(int(x) for x in pydantic.VERSION.split(".")[:2])
        if major_minor < (2, 12):
            problems.append(f"pydantic {pydantic.VERSION} < 2.12")
    except Exception as exc:
        problems.append(f"pydantic unavailable ({type(exc).__name__})")
    return problems


_PIN_PROBLEMS = [] if _MISSING else _pin_problems()
if not _MISSING:
    cp, rt = os.environ["D2_CONTROL_PLANE_DIR"], os.environ["D2_RUNTIME_DIR"]
    for path in (rt, os.path.join(cp, "src"), cp, os.path.join(ROOT, "suites", "operation-identity"), HERE):
        if path not in sys.path:
            sys.path.insert(0, path)


@pytest.fixture(autouse=True)
def _components_present():
    if _MISSING:
        pytest.fail(f"{', '.join(_MISSING)} not set")
    if _PIN_PROBLEMS:
        pytest.fail("pin refusal: " + "; ".join(_PIN_PROBLEMS))
