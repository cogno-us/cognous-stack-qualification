"""A2 (Architect disposition, issue #215): operation-ledger PRUNING, mandatory row NC3-04 and its negative controls (proposed).

SPDX-License-Identifier: Apache-2.0

Documented limitation (Control Plane 7a4bcd40 docs/bounded_authorization_effect.md; tests/test_known_limits.py): the operation-identity
ledger has no retention rule; with its rows removed from the run record a revision-2 decision that holds as ``operation_renewal_unrecorded``
is ``authorized``; the destination still refuses the second effect (``operation_already_committed``). This test exercises that on ROUTE B
(``_pruning.py``), which the Control Plane's own test does not. It asserts the REFUSAL BY THE DESTINATION and records the Control Plane's
``authorized`` as the disclosed limit (it is not judged, and nothing here claims pruning is detected or prevented by the Control Plane).
"""
from __future__ import annotations

import copy
import json
import pathlib
import shutil
import tempfile

import pytest

import _chain
import _pruning as P
import _state
import verdict

FRAGMENT = json.loads((pathlib.Path(__file__).resolve().parent / "v8_rows_b1.fragment.json").read_text())
ROW = next(r for r in FRAGMENT["rows"] if r["id"] == "NC3-04")


def judge(obs):
    return verdict.evaluate_row(ROW, {"nc_ledger_pruning": {"status": "ran", **obs}})


@pytest.fixture(scope="module")
def pruning():
    obs = _chain.run_scenario("nc_ledger_pruning")
    if obs.get("status") != "ran":
        pytest.fail(f"nc_ledger_pruning did not run: {obs.get('blocked_reason')}")
    return obs


def test_control_arm_intact_ledger_holds_an_unrecorded_renewal(pruning):
    c = pruning["control"]
    assert c["decision_result"] == "hold" and c["decision_reasons"] == ["operation_renewal_unrecorded"], c
    assert pruning["first"]["status"] == "executed" and pruning["first"]["effect_count"] == 1


def test_pruned_arm_control_plane_no_longer_holds_documented_known_limit_recorded_not_judged(pruning):
    p = pruning["pruned"]
    assert p["rows_before"] >= 1 and p["rows_removed"] == p["rows_before"] and p["rows_after"] == 0, p
    assert p["cp_decision_result"] == "authorized" and p["cp_decision_reasons"] == [], p  # the DISCLOSED limit: no retention rule, pruning is not detected
    assert p["claim_issued"] is True and p["second_effect_id_differs_from_first"] is True


def test_pruned_arm_route_b_destination_refuses_the_second_effect(pruning):
    p = pruning["pruned"]
    s = p["second_execute"]
    assert s["raised"] is False and s["status"] == "denied" and s["error"] == "operation_already_committed", s
    assert (s["attempted"], s["acknowledged"], s["newly_executed"]) == (False, False, False), s
    assert p["effect_count"] == 1 and p["only_original_effect"] is True  # independent read-only SQLite readback, not an executor result
    assert p["destination_operation_rows_before_second"] == p["destination_operation_rows_after"] == 1


def test_pruned_record_is_rejected_by_the_pinned_verifier_informational_characterisation_of_the_documented_statement(pruning):
    v = pruning["verifier_informational"]
    assert v["module_path_under_pin"] is True
    assert v["exit_code"] == 1 and v["overall"] == "reject", v
    assert "v2.profile.operation-identity" in v["refuted_check_ids"], v


def test_oracle_row_nc3_04_passes_on_the_recorded_observations(pruning):
    result = verdict.evaluate_row(ROW, _state.OBS)
    assert result["status"] == verdict.PASS, result


def test_artifacts_retained(pruning):
    art = _state.results_dir() / "artifacts" / "nc_ledger_pruning"
    for name in ("cp-run-record.intact.json", "cp-run-record.pruned.json", "cp-run-record.after-second-decision.json", "destination.final.sqlite"):
        assert (art / name).is_file(), name


# ------------------------------------------------------------------------------------------------------------- negative controls
def _run(**kw):
    work = pathlib.Path(tempfile.mkdtemp(prefix="mvp-prunectl-"))
    try:
        return P.run(work, verifier=False, retain=False, **kw)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_negative_control_nothing_pruned_fails_the_row():
    obs = _run(prune_cp=False)
    result = judge(obs)
    assert result["status"] == verdict.FAIL, result
    assert any("pruned.prune_cp" in f["obs"] or "pruned.rows_removed" in f["obs"] for f in result["failed"]), result


def test_negative_control_destination_ledger_also_lost_allows_a_second_effect_and_fails_the_row():
    obs = _run(prune_destination=True)
    assert obs["pruned"]["effect_count"] == 2, obs["pruned"]  # the pinned code has no other barrier: the documented limit is real, and the row would catch a change
    result = judge(obs)
    assert result["status"] == verdict.FAIL, result
    assert any("second_execute" in f["obs"] or "effect_count" in f["obs"] for f in result["failed"]), result
