"""Architect ruling 5 (PROPOSED): ONE supported-ingress ambiguous-acknowledgement test. Qualification owns the verdict.

SPDX-License-Identifier: Apache-2.0

EVIDENCE LEVEL: SUPPORTED INGRESS (real hub tools/mvp_ingress over its Unix socket, unprivileged client, simulate=None, schema unchanged).
Executor-level evidence is a different thing: ruling 4 (test_ruling4_lost_ack.py) and rows NC2-01..05 use ``simulate='lost_ack'`` on the
executor directly. Fault injection lives only in the trusted harness (_ingress_fault_wrapper.py). The status is computed by verdict.evaluate_row
from the recorded observations and the proposed row NC2-06 of expectations.proposed.v5-ingress-ambiguity.json (never from v1-v3). FAIL, BLOCKED and NOT RUN
are never converted into a pass or a skip.
"""
from __future__ import annotations

import json

import _chain
import _state
import verdict
from conftest import ROOT

V5 = ROOT / "process" / "mvp-chain" / "expectations.proposed.v5-ingress-ambiguity.json"


def test_ingress_ambiguous_acknowledgement_supported_path():
    row = next(r for r in json.loads(V5.read_text())["rows"] if r["id"] == "NC2-06")
    _chain.run_scenario(row["scenario"])
    result = verdict.evaluate_row(row, _state.OBS)
    detail = json.dumps({k: result[k] for k in ("status", "reason", "failed")}, default=str)
    assert result["status"] == verdict.PASS, f"NC2-06 (supported-ingress) {result['status']}: {detail}"


def _control(name):
    row = next(r for r in json.loads(V5.read_text())["rows"] if r["id"] == "NC2-06")
    _chain.run_scenario(name)
    # the row reads the nc_ingress_ambiguity record; point it at the control's record in a private copy
    return verdict.evaluate_row(row, {"nc_ingress_ambiguity": _state.OBS[name]})


def test_negative_control_hook_disabled_nc2_06_must_fail():
    result = _control("nc_ingress_ambiguity_nohook")
    assert result["status"] == verdict.FAIL, result
    assert "nc_ingress_ambiguity.ack.hook_fired" in [f["obs"] for f in result["failed"]], result["failed"]


def test_negative_control_caller_controlled_simulate_nc2_06_must_fail():
    result = _control("nc_ingress_ambiguity_forced_simulate")
    assert result["status"] == verdict.FAIL, result
    failed = [f["obs"] for f in result["failed"]]
    assert "nc_ingress_ambiguity.boundary.simulate_received_by_destination" in failed, failed
    assert "nc_ingress_ambiguity.boundary.simulate_received_by_executor" in failed, failed
