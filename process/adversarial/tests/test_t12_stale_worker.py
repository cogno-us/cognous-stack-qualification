"""T12. Stale worker resumes after lease or deadline expiry (ideas C23, B12, tier 4; leg of chain CH2).

SPDX-License-Identifier: Apache-2.0

Attacker: a worker paused by the scheduler after the control plane's freshness gate, resumed after another worker took over.
Barrier: the delayed-commit 'commit' pause point (inside the destination call, after the freshness/0.1 dispatch gate). While
worker A is paused there, the clock moves past the check deadline (600 s) and worker B runs to completion in another thread
(same decision, or a renewed decision with a new effect id). Then A resumes. Destination rows are read independently.
Invariant (plan): no second effect; a resumed worker whose deadline has passed is refused at the destination or its effect is
detected. Expected: prevented by effect-id dedupe / prior-attempt rule / operation key; the absence of destination-enforced
fencing is recorded as a residual.

Does not prove: cross-host fencing (the check lease is a same-host flock); real scheduler pauses; that the resumed worker's
late commit is refused (it is not: there is no destination-side fencing token; this is the recorded residual).
"""
from __future__ import annotations

import threading

import pytest

from _adv import effect_ids, flow, twice
from conftest import observe

T = "T12"
DNP = "same-host only; no destination-side fencing token exists, so a resumed worker's late commit is not refused by it"


def _scenario(tmp_path, mp, *, identity, renew):
    fl = flow(tmp_path, mp, identity=identity, wide=True, freshness={}, live_observation_clock=True)
    out = {}

    def worker_b():
        fl.advance_clock(600)
        if renew:
            _, r = fl.renew_and_commit_r2()
        else:
            r = fl.run(fl.d1)
        out["B"] = (r.status, r.error)

    def pause():
        t = threading.Thread(target=worker_b)
        t.start()
        t.join(60)
        out["B_finished"] = not t.is_alive()

    fl.dest.pause_at("commit", pause)
    rA = fl.run(fl.d1)
    out["A"] = (rA.status, rA.error)
    out["effects"] = len(effect_ids(fl.dest.path))
    return out


@pytest.mark.parametrize("identity", [False, True], ids=["default", "operation_identity"])
def test_takeover_of_the_same_decision_single_effect(cprt, tmp_path, monkeypatch, identity):
    out = twice(tmp_path, lambda w, mp: _scenario(w, mp, identity=identity, renew=False))
    observe(T, f"same-decision takeover ({'identity' if identity else 'default'})", "prevented" if out["effects"] == 1
            else "reproduced failure", does_not_prove=DNP, detail={**out, "residual": "A's late commit lands; no fencing"})
    assert out["B_finished"] and out["B"][0] == "denied" and out["effects"] == 1, out


def test_takeover_by_renewal_default_duplicates_known(cprt, tmp_path, monkeypatch):
    out = twice(tmp_path, lambda w, mp: _scenario(w, mp, identity=False, renew=True))
    observe(T, "renewal takeover (default)", "reproduced failure", does_not_prove=DNP,
            detail={**out, "known": "same class as F-5 / F-18 (T11): default configuration has no operation-level control"})
    assert out["effects"] == 2, out  # characterised known limitation


def test_takeover_by_renewal_operation_identity_single_effect(cprt, tmp_path, monkeypatch):
    out = twice(tmp_path, lambda w, mp: _scenario(w, mp, identity=True, renew=True))
    observe(T, "renewal takeover (operation identity)", "prevented" if out["effects"] == 1 else "reproduced failure",
            does_not_prove=DNP, detail=out)
    assert out["B"][0] == "executed" and out["A"][0] != "executed" and out["effects"] == 1, out


def test_positive_control_without_takeover_a_commits_once(cprt, tmp_path, monkeypatch):
    fl = flow(tmp_path, monkeypatch, freshness={}, live_observation_clock=True)
    assert fl.run(fl.d1).status == "executed" and effect_ids(fl.dest.path) == [fl.d1.effect_id]
