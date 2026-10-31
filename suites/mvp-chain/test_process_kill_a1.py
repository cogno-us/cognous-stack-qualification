"""A1 (Architect disposition, issue #215): REAL OS-level process kill, mandatory row NC2-07 and its negative controls (proposed).

SPDX-License-Identifier: Apache-2.0

The scenario ``nc_process_kill`` (``_killharness.py``) starts a child Python process that runs the pinned route B
``AtomicLocalControlPlaneExecutor`` on a durable on-disk store (Control Plane run record + SQLite), blocks it at a documented
``_transaction_stage`` seam, SIGKILLs it from this process, and has a FRESH process reopen the same store and observe / reconcile /
re-present the claim. ``simulate=`` is never used. The verdict predicate is the row ``NC2-07`` of ``v8_rows_b1.fragment.json``
evaluated by ``verdict.py`` over owner-side observations only.

The negative controls run the SAME pipeline with one thing changed (a different signal, no kill, or a mutated killed store) and require the
row predicate to FAIL for the intended reason, so the row cannot pass vacuously. Nothing skips; nothing is marked xfail.
"""
from __future__ import annotations

import copy
import json
import pathlib
import shutil
import signal
import tempfile

import pytest

import _chain
import _killharness as K
import _state
import verdict

FRAGMENT = json.loads((pathlib.Path(__file__).resolve().parent / "v8_rows_b1.fragment.json").read_text())
ROW = next(r for r in FRAGMENT["rows"] if r["id"] == "NC2-07")


def row_for_seam(seam):
    prefix = f"nc_process_kill.{seam}."
    row = copy.deepcopy(ROW)
    row["all"] = [p for p in row["all"] if p["obs"].startswith(prefix)]
    row["blocked_if"] = [p for p in row["blocked_if"] if p["obs"].startswith(prefix)]
    assert row["all"], seam
    return row


def judge(seam, seam_obs):
    return verdict.evaluate_row(row_for_seam(seam), {"nc_process_kill": {"status": "ran", seam: seam_obs}})


@pytest.fixture(scope="module")
def killed():
    obs = _chain.run_scenario("nc_process_kill")
    if obs.get("status") != "ran":
        pytest.fail(f"nc_process_kill did not run: {obs.get('blocked_reason')}")
    return obs


@pytest.mark.parametrize("seam", K.SEAMS)
def test_real_sigkill_was_delivered_to_a_live_blocked_process_at_the_seam(killed, seam):
    v = killed[seam]["victim"]
    assert v["seam_reached"] is True and v["ready_line"].startswith(f"READY {seam} "), v
    # alive_before_kill: the process had not exited when the signal was sent. Its /proc state (R just after the READY write, S once asleep) is recorded as evidence only: asserting it would be timing luck.
    assert v["alive_before_kill"] is True, v
    assert v["kill_signal_sent"] == int(signal.SIGKILL)
    assert v["returncode"] == -9 and v["term_signal"] == 9 and v["exit_code"] is None and v["killed_by_sigkill"] is True, v
    assert v["completed_without_kill"] is False and "COMPLETED" not in v["stdout"]
    assert v["proc_gone_after"] is True


@pytest.mark.parametrize("seam", K.PRECOMMIT)
def test_kill_inside_the_open_transaction_leaves_nothing_and_the_claim_is_still_issued(killed, seam):
    r = killed[seam]["recovered"]
    assert r["observer_is_fresh_process"] is True and r["observer_pid"] != r["victim_pid"]
    on = r["on_reopen"]
    assert (on["effect_count"], on["attempt_rows"], on["attempt_event_rows"], on["receipt_rows"], on["operation_rows"]) == (0, 0, 0, 0, 0), on
    assert on["claim_state"] == "issued" and on["budget_used"] == [0], on
    rec = r["reconcile_first"]
    assert (rec["status"], rec["reason"], rec["claim_state"], rec["retry_eligible"]) == ("hold", "no_durable_effect_for_claim", "issued", False), rec  # reconcile itself never authorizes a retry
    # the pinned code does not recover anything automatically: presenting the still-issued claim again is a NEW execute, and it delivers the effect exactly once
    assert r["execute_again"]["status"] == "executed" and r["after_execute_again"]["effect_count"] == 1
    assert r["execute_third"]["status"] == "denied" and r["execute_third"]["attempted"] is False and "claim is not usable" in r["execute_third"]["error"]
    assert r["final"]["effect_count"] == 1 and r["effect_ids_final_match_expected"] is True and r["final"]["claim_state"] == "consumed"


def test_kill_after_commit_leaves_one_durable_effect_consumed_claim_and_refuses_re_presentation(killed):
    r = killed["after_commit"]["recovered"]
    on = r["on_reopen"]
    assert (on["effect_count"], on["attempt_rows"], on["receipt_rows"], on["operation_rows"]) == (1, 1, 1, 1), on
    assert r["effect_ids_match_expected_on_reopen"] is True and on["claim_state"] == "consumed", on
    rec = r["reconcile_first"]
    assert (rec["status"], rec["retry_eligible"], rec["effect_id_matches_expected"]) == ("applied", False, True), rec
    again = r["execute_again"]
    assert (again["status"], again["attempted"], again["acknowledged"], again["newly_executed"]) == ("denied", False, False, False), again
    assert "claim is not usable" in again["error"]
    assert r["max_effect_count"] == 1 and r["final"]["effect_count"] == 1


@pytest.mark.parametrize("seam", K.SEAMS)
def test_raw_pre_recovery_state_and_run_record_are_retained_and_the_cp_record_was_not_touched_by_the_kill(killed, seam):
    pre = killed[seam]["pre_recovery"]
    assert "refunds.sqlite3" in pre["files"] and pre["files"]["refunds.sqlite3"]["sha256"]
    assert pre["run_json_unchanged_by_kill"] is True
    art = _state.results_dir() / "artifacts" / "nc_process_kill" / seam
    for name in ("observations.json", "post-recovery-tables.json", "pre-recovery/refunds.sqlite3", "pre-recovery/cp-run.json"):
        assert (art / name).is_file(), name


@pytest.mark.parametrize("seam", K.SEAMS)
def test_row_predicate_for_each_seam_passes_on_the_recorded_observations(killed, seam):
    result = judge(seam, killed[seam])
    assert result["status"] == verdict.PASS, result


def test_oracle_row_nc2_07_passes_on_the_recorded_observations(killed):
    result = verdict.evaluate_row(ROW, _state.OBS)
    assert result["status"] == verdict.PASS, result


# ------------------------------------------------------------------------------------------------------------- negative controls
def _control(seam, **kwargs):
    work = pathlib.Path(tempfile.mkdtemp(prefix="mvp-killctl-"))
    try:
        return K.run_seam(work, seam, **kwargs)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _must_fail(seam, obs, expected_failed_fragment):
    result = judge(seam, obs)
    assert result["status"] == verdict.FAIL, result
    failed = [f["obs"] for f in result["failed"]]
    assert any(expected_failed_fragment in f for f in failed), (expected_failed_fragment, failed)


def test_negative_control_sigterm_instead_of_sigkill_fails_the_row():
    obs = _control("after_begin", kill_signal=signal.SIGTERM)
    assert obs["victim"]["returncode"] == -15
    _must_fail("after_begin", obs, "victim.killed_by_sigkill")


def test_negative_control_no_kill_the_flow_completes_fails_the_row():
    obs = _control("after_commit", mode="run")
    assert obs["victim"]["returncode"] == 0 and obs["victim"]["completed_without_kill"] is True
    _must_fail("after_commit", obs, "victim.killed_by_sigkill")


def test_negative_control_extra_effect_in_the_killed_store_fails_the_precommit_row():
    obs = _control("after_effect_insert_before_commit", mutate=K.mutate_duplicate_effect)
    _must_fail("after_effect_insert_before_commit", obs, "recovered.on_reopen.effect_count")


def test_negative_control_claim_reset_in_the_killed_store_fails_the_postcommit_row():
    obs = _control("after_commit", mutate=K.mutate_claim_reset)
    _must_fail("after_commit", obs, "recovered.")


def test_negative_control_committed_effect_removed_from_the_killed_store_fails_the_postcommit_row():
    obs = _control("after_commit", mutate=K.mutate_rollback_committed)
    _must_fail("after_commit", obs, "recovered.on_reopen.effect_count")
