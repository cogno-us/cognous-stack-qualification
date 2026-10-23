"""Worker D2 route-B end-to-end tests: wiring only (new file; reuses suites/operation-identity/_oi_flow.py unmodified).

D2_CONTROL_PLANE_DIR  Control Plane checkout (its tests/ package supplies the synthetic fixtures)
D2_RUNTIME_DIR        Runtime checkout
A missing variable FAILS every test (never skips). Builder-written observations: not a Qualification verdict.
SPDX-License-Identifier: Apache-2.0
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
_MISSING = [v for v in ("D2_CONTROL_PLANE_DIR", "D2_RUNTIME_DIR") if not os.environ.get(v)]
if not _MISSING:
    cp, rt = os.environ["D2_CONTROL_PLANE_DIR"], os.environ["D2_RUNTIME_DIR"]
    for path in (rt, os.path.join(cp, "src"), cp, os.path.join(ROOT, "suites", "operation-identity"), HERE):
        if path not in sys.path:
            sys.path.insert(0, path)


@pytest.fixture(autouse=True)
def _components_present():
    if _MISSING:
        pytest.fail(f"{', '.join(_MISSING)} not set")
