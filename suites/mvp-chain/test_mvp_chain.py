"""mvp-chain: one test per expectations row. A row passes only when verdict.evaluate_row says PASS (or NOT APPLICABLE).

SPDX-License-Identifier: Apache-2.0
Every other status fails the test: FAIL, BLOCKED and NOT RUN are never converted into a pass, a skip or an xfail here.
The status is computed from the recorded raw observations and the proposed expectations only (verdict.py).
"""
from __future__ import annotations

import json

import pytest

import _chain
import _state
import verdict
from conftest import expectations_file

ROWS = json.loads(expectations_file().read_text())["rows"]


@pytest.mark.parametrize("row", ROWS, ids=[r["id"] for r in ROWS])
def test_row(row):
    if row["scenario"] != "env":
        _chain.run_scenario(row["scenario"])
    result = verdict.evaluate_row(row, _state.OBS)
    detail = json.dumps({k: result[k] for k in ("status", "reason", "failed")}, default=str)
    assert result["status"] in (verdict.PASS, verdict.NOT_APPLICABLE), f"{row['id']} {result['status']}: {row['title']} :: {detail}"
