"""Architect ruling 5 (PROPOSED): ONE supported-ingress ambiguous-acknowledgement test. Qualification owns the verdict.

SPDX-License-Identifier: Apache-2.0

EVIDENCE LEVEL: SUPPORTED INGRESS (real hub tools/mvp_ingress over its Unix socket, unprivileged client, simulate=None, schema unchanged).
Executor-level evidence is a different thing: ruling 4 (test_ruling4_lost_ack.py) and rows NC2-01..05 use ``simulate='lost_ack'`` on the
executor directly. Fault injection lives only in the trusted harness (_ingress_fault_wrapper.py). The status is computed by verdict.evaluate_row
from the recorded observations and the proposed row NC2-06 of expectations.proposed.v4.json (never from v1-v3). FAIL, BLOCKED and NOT RUN
are never converted into a pass or a skip.
"""
from __future__ import annotations

import json

import _chain
import _state
import verdict
from conftest import ROOT

V4 = ROOT / "process" / "mvp-chain" / "expectations.proposed.v4.json"


def test_ingress_ambiguous_acknowledgement_supported_path():
    row = next(r for r in json.loads(V4.read_text())["rows"] if r["id"] == "NC2-06")
    _chain.run_scenario(row["scenario"])
    result = verdict.evaluate_row(row, _state.OBS)
    detail = json.dumps({k: result[k] for k in ("status", "reason", "failed")}, default=str)
    assert result["status"] == verdict.PASS, f"NC2-06 (supported-ingress) {result['status']}: {detail}"
