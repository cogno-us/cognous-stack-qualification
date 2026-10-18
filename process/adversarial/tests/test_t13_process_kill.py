"""T13. Real process kill at every persistence boundary (ideas C18, C19, tier 4).

SPDX-License-Identifier: Apache-2.0

Attacker: an operator or fault that kills the process (os._exit in a forked child: no finally blocks, no atexit, no flush
beyond what was already written) at one write point of the route-A sequence, then restarts.
Boundaries: after the decision is persisted; after the 'attempted' row; inside the destination call before its transaction;
after the destination transaction committed but before the acknowledgement returns; after the acknowledged row. With the
operation-identity profile on, the attempt join row and the destination operation key are inside the same points.
Restart: a fresh process view over the same record store and destination (new workflow, new decision with the same effect id),
recovery of interrupted checks, then one execution attempt.
Invariant: after restart the destination holds at most one effect, and no state claims success without the effect: an
'acknowledged' attempt implies a row; a row left by the killed process is reconciled, never duplicated.

Does not prove: machine crash or fsync loss (the kill is a process exit on a live kernel); route C (exchange) and the witness
write point; kills inside SQLite or inside the JSON store's own write (between temp file and rename).
"""
from __future__ import annotations

import multiprocessing
import os

import pytest

from _adv import effect_ids, flow
from conftest import observe

T = "T13"
DNP = "process exit only (no power loss or fsync loss); route C and the witness write point not run"
KILL = 71
BOUNDARIES = ("after_decision", "after_attempted_row", "inside_destination_before_commit", "after_commit_before_ack",
              "after_acknowledged_row")


def _child(work, boundary, identity):
    mp = pytest.MonkeyPatch()
    fl = flow(work, mp, identity=identity, wide=True)
    if boundary == "after_decision":
        os._exit(KILL)
    rec = fl.f.records
    original_append = rec.append_attempt
    count = {"n": 0}

    def append(value):
        original_append(value)
        count["n"] += 1
        if boundary == "after_attempted_row" and value.status == "attempted":
            os._exit(KILL)
        if boundary == "after_acknowledged_row" and value.status == "acknowledged":
            os._exit(KILL)
    rec.append_attempt = append
    if boundary == "inside_destination_before_commit":
        fl.dest.pause_at("commit", lambda: os._exit(KILL))
    if boundary == "after_commit_before_ack":
        original_commit = fl.dest.commit

        def commit(snapshot, **kw):
            original_commit(snapshot, **kw)
            os._exit(KILL)
        fl.dest.commit = commit
    fl.run(fl.d1)
    os._exit(0)


def _restart(work, mp, identity):
    fl = flow(work, mp, identity=identity, wide=True)  # same directories: the record store and destination persist
    recovered = fl.f.records.recover_interrupted_checks()
    r = fl.run(fl.d1)
    attempts = fl.f.records.load().attempts
    return fl, r, recovered, attempts


@pytest.mark.parametrize("identity", [False, True], ids=["default", "operation_identity"])
@pytest.mark.parametrize("boundary", BOUNDARIES)
def test_kill_then_restart(cprt, tmp_path, monkeypatch, boundary, identity):
    proc = multiprocessing.get_context("fork").Process(target=_child, args=(tmp_path, boundary, identity))
    proc.start()
    proc.join(120)
    assert proc.exitcode == KILL, f"the kill point {boundary} was not reached (exit {proc.exitcode})"
    fl0_effects = effect_ids(tmp_path / "sqlite" / "refunds.sqlite3") if (tmp_path / "sqlite" / "refunds.sqlite3").exists() else []
    fl, r, recovered, attempts = _restart(tmp_path, monkeypatch, identity)
    effects = effect_ids(fl.dest.path)
    acknowledged = [a for a in attempts if a.status == "acknowledged"]
    over_claim = bool(acknowledged) and not effects
    detail = {"effects_after_kill": len(fl0_effects), "effects_after_restart": len(effects), "restart_status": r.status,
              "recovered_checks": recovered, "acknowledged_rows": len(acknowledged)}
    ok = len(effects) <= 1 and not over_claim
    observe(T, f"kill {boundary} ({'identity' if identity else 'default'})", "prevented" if ok else "reproduced failure",
            does_not_prove=DNP, detail=detail)
    assert len(effects) <= 1, detail
    assert not over_claim, detail
    if fl0_effects:  # the killed process left a row: the restart reconciles it, never re-dispatches
        assert r.status in ("reconciled", "executed") and r.newly_executed is False, detail


def test_positive_control_no_kill_one_effect(cprt, tmp_path, monkeypatch):
    fl = flow(tmp_path, monkeypatch, wide=True)
    assert fl.run(fl.d1).status == "executed" and effect_ids(fl.dest.path) == [fl.d1.effect_id]
