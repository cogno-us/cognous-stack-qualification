"""Outside-holder suite harness: runs against two checkouts named by environment variables (never modified).

OH_CONTROL_PLANE_DIR  cogno-us/cognous-control-plane checkout (its tests/ package supplies the synthetic fixtures)
OH_RUNTIME_DIR        cogno-us/cognous-execution-runtime checkout

A missing variable FAILS every test (it never skips): a suite that did not run proves nothing.
SPDX-License-Identifier: Apache-2.0
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
# The synthetic flow harness is the operation-identity suite's (_oi_flow.py); it is imported, not copied.
for _path in (HERE, os.path.join(ROOT, "suites", "operation-identity"), os.path.join(ROOT, "suites")):
    if _path not in sys.path:
        sys.path.insert(0, _path)


def _wire():
    missing = [v for v in ("OH_CONTROL_PLANE_DIR", "OH_RUNTIME_DIR") if not os.environ.get(v)]
    if missing:
        return missing
    cp, rt = os.environ["OH_CONTROL_PLANE_DIR"], os.environ["OH_RUNTIME_DIR"]
    for path in (rt, os.path.join(cp, "src"), cp):  # control plane root last so its `tests` package wins over any runtime `tests`
        if path not in sys.path:
            sys.path.insert(0, path)
    return []


_MISSING = _wire()


@pytest.fixture(autouse=True)
def _components_present():
    if _MISSING:
        pytest.fail(f"{', '.join(_MISSING)} not set: the outside-holder suite cannot run against the components")
