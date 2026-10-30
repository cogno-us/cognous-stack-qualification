"""V08 Tier 1, Worker B: transactional integrity of the authority-to-effect boundary (AT-1 .. AT-7).

Worker B, fresh AI session, no prior implementation involvement, same organization (independent test DESIGN, not external qualification).
Cases B-01 .. B-14 are declared in results/v08-tier1/atomicity/INVENTORY.md (committed before any execution). Race and crash cases use DISTINCT OS
PROCESSES (scripts `_probe_*.py` launched with subprocess); in-process execution is used only where the case is not a concurrency claim (B-05, B-14,
and parent-side corruption/inspection) and is labelled so. Fixture mechanics (Env, make_claim, binding_of, trust) are reused from the Runtime
component tests via `_atomicity_fixture`; every oracle below is written independently from the ADR and the source.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import time
from datetime import timedelta
from pathlib import Path

import pytest

from _atomicity_fixture import (  # noqa: E402
    EFFECT_TABLES, AtomicAuthorityEffectDestination, AtomicLocalControlPlaneExecutor, Checks, Child, World, anchor_info, counts, dump_db,
    effect_dump, envelope_i, ev_time, exec_spec, g, kill_all, read_events, sa, snapshot_envelope, touch, v4, wait_event)

BARRIER_SETTLE = 1.2  # seconds a waiter is given to be inside BEGIN IMMEDIATE before the holder is released (SQLite busy timeout is 10 s)
REVOKE_PAIR = [["sel-test-1", 1]]


def revoke_spec(w: World, tmp: Path, *, versions, revoked=(), hooks=None, go=None) -> dict:
    return {"base": str(w.base), "versions": list(versions), "revoked": [list(x) for x in revoked], "events": str(tmp / "events.jsonl"),
            "go": str(go) if go else None, "hooks": hooks or {}}


def run_exec(w: World, i: int, tmp: Path, label: str, *, max_effects: int = 1):
    c = Child("_probe_exec.py", exec_spec(w.base, i, tmp, attempt_id=f"att-{label}", max_effects=max_effects), tmp, label)
    rc = c.wait()
    return c, rc


def typed_of(res) -> dict:
    return (res or {}).get("typed") or {}


def checkpoint(db: Path) -> None:
    conn = sqlite3.connect(str(db))
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchall()
    finally:
        conn.close()


def scrub(ev_obs, events: list) -> list:
    return [{"label": e["label"], "pid": e["pid"], "name": e["name"], "t_ms": round(e["t"] / 1e6, 1)} for e in events]


# ======================================================================================================================== AT-1
def test_b01_effect_holds_lock_after_guard_revocation_process_blocked(tmp_path, ev):
    """B-01: process E holds the write lock after its guard passed; process R (revocation) is proven blocked; effect linearizes before revocation."""
    ev["scenario"] = "AT-1"
    ev["expected"] = ("E (holding the lock after a passed guard) commits exactly one effect whose receipt log head is the pre-revocation head; R's revocation "
                      "commits only after E, as head+1/+2; later claim on the scope is refused selection_revoked; 1 effect/attempt/receipt, claim consumed, budget 1")
    chk, kids = Checks(), []
    w = World(tmp_path / "w", n_claims=2)
    tmp = tmp_path / "run"
    tmp.mkdir()
    events, release = tmp / "events.jsonl", tmp / "release"
    head0 = counts(w.db)["log_head"]
    E = Child("_probe_exec.py", exec_spec(w.base, 1, tmp, go=tmp / "go-E", attempt_id="att-E",
                                          hooks={"after_selection_guard": [["event", "holding"], ["wait", str(release)]]}), tmp, "E")
    R = Child("_probe_revoke.py", revoke_spec(w, tmp, versions=[2], revoked=REVOKE_PAIR, go=tmp / "go-R"), tmp, "R")
    kids = [E, R]
    try:
        ready = [wait_event(events, c.label, "ready", kids) for c in kids]
        touch(tmp / "go-E")
        holding = wait_event(events, "E", "holding", kids)
        chk.exercise("E and R ready, E parked after guard holding the write lock", all(ready) and holding is not None)
        if holding is None:
            ev["observed"].update(events=scrub(ev, read_events(events)), children=[c.summary() for c in kids])
            chk.apply(ev, "E never reached the seam")
            return
        touch(tmp / "go-R")
        wait_event(events, "R", "sync_start", kids)
        time.sleep(BARRIER_SETTLE)
        still_blocked = ev_time(read_events(events), "R", "sync_returned") is None
        t_release = touch(release)
        rcE, rcR = E.wait(), R.wait()
    finally:
        kill_all(kids)
    evs = read_events(events)
    resE, resR = E.result(), R.result()
    post = counts(w.db)
    verify = w.fresh_dest().verify_selection_store()
    c2, _ = run_exec(w, 2, tmp, "C2")
    r2 = c2.result()
    chk.exercise("R was still blocked while E held the lock", still_blocked)
    chk.exercise("R returned only after the release", (ev_time(evs, "R", "sync_returned") or 0) > t_release)
    chk.exercise("E and R probes completed with results", rcE == 0 and rcR == 0 and resE is not None and resR is not None and "exception" not in (resE or {}) and "exception" not in (resR or {}),
                 rcE=rcE, rcR=rcR, resE=resE, resR=resR)
    chk.exercise("E executed against the then-current authority", (resE or {}).get("status") == "executed")
    chk.exercise("E commit event precedes R sync return", (ev_time(evs, "E", "stage:after_commit") or 1 << 62) < (ev_time(evs, "R", "sync_returned") or 0))
    chk.safety("exactly one effect, attempt, receipt; claim-1 consumed; budget used 1",
               (post["effects"], post["attempts"], post["authority_effect_receipts_v1"], post["budget_used"]) == (1, 1, 1, 1) and post["claims"].get("claim-1") == "consumed",
               post=post)
    chk.safety("receipt log head is the pre-revocation head (effect linearized before the revocation)", (resE or {}).get("receipt_head") == head0, head0=head0,
               receipt_head=(resE or {}).get("receipt_head"))
    chk.safety("revocation entries follow the effect head (head0+1 and +2)", post["log_head"] == head0 + 2 and ((resR or {}).get("results") or [{}])[0].get("activation_sequence") == head0 + 1,
               post_head=post["log_head"])
    chk.safety("store verifies known after the race", verify.state == "known", state=verify.state, cause=verify.cause)
    chk.safety("a later claim on the scope is refused selection_revoked and writes no effect", (r2 or {}).get("status") == "denied" and typed_of(r2).get("code") == "selection_revoked"
               and typed_of(r2).get("refusal_class") == "REFUSE" and counts(w.db)["effects"] == 1, r2=r2)
    ev["observed"].update(events=scrub(ev, evs), children=[c.summary() for c in kids], pids={"E": E.pid, "R": R.pid, "post_claim": c2.pid},
                          t_release_ms=round(t_release / 1e6, 1), head_before=head0, post=post)
    chk.apply(ev)


def test_b02_revocation_holds_lock_effect_process_blocked(tmp_path, ev):
    """B-02: process R holds its revocation transaction (uncommitted); process E is proven blocked; after R commits E must be refused."""
    ev["scenario"] = "AT-1"
    ev["expected"] = ("E blocks on BEGIN IMMEDIATE until R commits; E then refused selection_revoked (REFUSE); 0 effects/attempts/receipts, claim issued, budget 0, "
                      "effect-bearing tables unchanged, store known at head 5")
    chk = Checks()
    w = World(tmp_path / "w", n_claims=1)
    tmp = tmp_path / "run"
    tmp.mkdir()
    events, release = tmp / "events.jsonl", tmp / "release"
    R = Child("_probe_revoke.py", revoke_spec(w, tmp, versions=[2], revoked=REVOKE_PAIR, go=tmp / "go-R",
                                              hooks={"before_commit": [["event", "holding"], ["wait", str(release)]]}), tmp, "R")
    E = Child("_probe_exec.py", exec_spec(w.base, 1, tmp, go=tmp / "go-E", attempt_id="att-E"), tmp, "E")
    kids = [R, E]
    try:
        ready = [wait_event(events, c.label, "ready", kids) for c in kids]
        touch(tmp / "go-R")
        holding = wait_event(events, "R", "holding", kids)
        chk.exercise("R and E ready, R parked at before_commit with its transaction open", all(ready) and holding is not None)
        if holding is None:
            ev["observed"].update(events=scrub(ev, read_events(events)), children=[c.summary() for c in kids])
            chk.apply(ev, "R never reached the seam")
            return
        pre = effect_dump(w.db)
        touch(tmp / "go-E")
        wait_event(events, "E", "stage:before_begin", kids)
        time.sleep(BARRIER_SETTLE)
        e_started = ev_time(read_events(events), "E", "stage:after_begin") is not None
        t_release = touch(release)
        rcR, rcE = R.wait(), E.wait()
    finally:
        kill_all(kids)
    evs = read_events(events)
    resE, resR = E.result(), R.result()
    post = counts(w.db)
    verify = w.fresh_dest().verify_selection_store()
    chk.exercise("E had not acquired the lock while R held it", not e_started)
    chk.exercise("E acquired the lock only after the release", (ev_time(evs, "E", "stage:after_begin") or 0) > t_release)
    chk.exercise("R committed the revocation (two entries) and E probe finished", rcR == 0 and rcE == 0 and "exception" not in (resR or {}) and (resR or {}).get("results", [{}])[0].get("n_entries") == 2
                 and resE is not None and "exception" not in (resE or {}), resR=resR, resE=resE)
    chk.safety("E did not execute; zero effects, attempts, receipts, budget; claim-1 still issued",
               (resE or {}).get("status") != "executed" and (post["effects"], post["attempts"], post["authority_effect_receipts_v1"], post["budget_used"]) == (0, 0, 0, 0)
               and post["claims"].get("claim-1") == "issued", post=post, resE=resE)
    chk.safety("effect-bearing tables identical before E and after the race", effect_dump(w.db) == pre)
    chk.safety("store known at head 5 (revocation durable)", verify.state == "known" and post["log_head"] == 5, state=verify.state, cause=verify.cause, head=post["log_head"])
    chk.exercise("E refused for the intended typed reason selection_revoked / REFUSE", typed_of(resE).get("code") == "selection_revoked" and typed_of(resE).get("refusal_class") == "REFUSE",
                 typed=typed_of(resE))
    ev["observed"].update(events=scrub(ev, evs), children=[c.summary() for c in kids], pids={"R": R.pid, "E": E.pid}, t_release_ms=round(t_release / 1e6, 1), post=post)
    chk.apply(ev)


# ======================================================================================================================== AT-2
def _race_four(tmp_path, ev, *, shared_budget: bool):
    chk = Checks()
    n, max_eff = 4, (2 if shared_budget else 1)
    w = World(tmp_path / "w", n_claims=n, max_effects=max_eff, budgets={i: "budget-shared" for i in range(1, n + 1)} if shared_budget else None)
    tmp = tmp_path / "run"
    tmp.mkdir()
    events, release = tmp / "events.jsonl", tmp / "release"
    kids = []
    for k in range(n):
        idx = (k + 1) if shared_budget else 1  # shared budget: four distinct claims; one claim: four attempts at claim-1
        hooks = {"after_begin": [["event", "holding"], ["wait", str(release)]]} if k == 0 else {}
        kids.append(Child("_probe_exec.py", exec_spec(w.base, idx, tmp, go=tmp / f"go-P{k}", attempt_id=f"att-P{k}", hooks=hooks, max_effects=max_eff), tmp, f"P{k}"))
    try:
        ready = [wait_event(events, c.label, "ready", kids) for c in kids]
        touch(tmp / "go-P0")
        holding = wait_event(events, "P0", "holding", kids)
        chk.exercise("four processes ready; P0 holds the write lock at after_begin", all(ready) and holding is not None)
        if holding is None:
            return w, chk, kids, tmp, None, None, events
        for k in range(1, n):
            touch(tmp / f"go-P{k}")
        waiting = [wait_event(events, f"P{k}", "stage:before_begin", kids) for k in range(1, n)]
        time.sleep(BARRIER_SETTLE)
        evs_mid = read_events(events)
        none_acquired = all(ev_time(evs_mid, f"P{k}", "stage:after_begin") is None for k in range(1, n))
        t_release = touch(release)
        rcs = [c.wait() for c in kids]
    finally:
        kill_all(kids)
    chk.exercise("all three waiters reached BEGIN IMMEDIATE and none acquired it while P0 held it", all(waiting) and none_acquired)
    evs = read_events(events)
    chk.exercise("waiters acquired the lock only after the release",
                 all((ev_time(evs, f"P{k}", "stage:after_begin") or 0) > t_release for k in range(1, n)))
    chk.exercise("all four probes completed", all(rc == 0 for rc in rcs) and all(c.result() and "exception" not in c.result() for c in kids), rcs=rcs)
    return w, chk, kids, tmp, t_release, evs, events


def test_b03_one_claim_four_processes_exactly_one_effect(tmp_path, ev):
    """B-03: four OS processes attempt ONE claim; only the lock holder may commit."""
    ev["scenario"] = "AT-2"
    ev["expected"] = "exactly 1 of 4 processes executes; the other 3 are denied 'execution claim is not usable'; 1 effect/attempt/receipt; claim consumed; budget used 1"
    w, chk, kids, tmp, t_release, evs, events = _race_four(tmp_path, ev, shared_budget=False)
    if evs is None:
        ev["observed"].update(children=[c.summary() for c in kids])
        chk.apply(ev, "P0 never reached the seam")
        return
    res = [c.result() or {} for c in kids]
    post = counts(w.db)
    statuses = [r.get("status") for r in res]
    chk.safety("exactly one process executed", statuses.count("executed") == 1, statuses=statuses)
    chk.safety("one effect, one attempt, one receipt, claim consumed, budget used 1",
               (post["effects"], post["attempts"], post["authority_effect_receipts_v1"], post["budget_used"]) == (1, 1, 1, 1) and post["claims"].get("claim-1") == "consumed", post=post)
    chk.exercise("the lock holder P0 is the winner and the others are denied 'not usable'",
                 statuses[0] == "executed" and all(r.get("status") == "denied" and "execution claim is not usable" in (r.get("error") or "") for r in res[1:]), res=res)
    ev["observed"].update(events=scrub(ev, evs), children=[c.summary() for c in kids], pids=[c.pid for c in kids], post=post, statuses=statuses)
    chk.apply(ev)


def test_b04_shared_budget_four_claims_never_exceeded(tmp_path, ev):
    """B-04: four DISTINCT claims share one budget (max 2); four OS processes race; the budget must never exceed 2."""
    ev["scenario"] = "AT-2"
    ev["expected"] = "exactly 2 effects; 2 denials 'authoritative effect budget exhausted'; used_effects == 2 (max 2); 2 consumed + 2 issued claims; attempts == receipts == effects == 2"
    w, chk, kids, tmp, t_release, evs, events = _race_four(tmp_path, ev, shared_budget=True)
    if evs is None:
        ev["observed"].update(children=[c.summary() for c in kids])
        chk.apply(ev, "P0 never reached the seam")
        return
    res = [c.result() or {} for c in kids]
    post = counts(w.db)
    conn = sqlite3.connect(str(w.db))
    budgets = [tuple(r) for r in conn.execute("SELECT budget_id, max_effects, used_effects FROM effect_budgets_v1")]
    conn.close()
    statuses = [r.get("status") for r in res]
    states = list(post["claims"].values())
    chk.safety("shared budget never exceeded", all(used <= mx for _, mx, used in budgets) and post["effects"] <= 2, budgets=budgets, effects=post["effects"])
    chk.safety("exactly 2 effects, attempts, receipts; budget used 2; 2 claims consumed, 2 issued",
               (post["effects"], post["attempts"], post["authority_effect_receipts_v1"], post["budget_used"]) == (2, 2, 2, 2) and states.count("consumed") == 2 and states.count("issued") == 2,
               post=post)
    chk.exercise("2 executed and 2 denied for the exhausted budget (typed message)",
                 statuses.count("executed") == 2 and sum(1 for r in res if r.get("status") == "denied" and "authoritative effect budget exhausted" in (r.get("error") or "")) == 2, res=res)
    ev["observed"].update(events=scrub(ev, evs), children=[c.summary() for c in kids], pids=[c.pid for c in kids], post=post, budgets=budgets, statuses=statuses)
    chk.apply(ev)


# ======================================================================================================================== AT-3
def test_b05_transaction_critical_evidence_write_failure_leaves_zero_effects(tmp_path, ev):
    """B-05 (in-process by design: fault injection, not a concurrency claim): receipt-evidence hook failure and commit-stage failure."""
    ev["scenario"] = "AT-3"
    ev["expected"] = ("both injected failures: no effect/attempt/event/receipt row, claim issued, budget 0, effect-bearing and selection tables identical to the pre-state; "
                      "executor result not executed; a clean retry then commits exactly one effect")
    chk = Checks()
    obs = {}
    for name in ("receipt_evidence_hook", "commit_stage_hook"):
        w = World(tmp_path / name)
        fired = {"n": 0}

        class Failing(AtomicAuthorityEffectDestination):
            def _selection_receipt_evidence(self, evidence):
                if name == "receipt_evidence_hook":
                    fired["n"] += 1
                    raise OSError("synthetic transaction-critical evidence store failure")
                return evidence

            def _transaction_stage(self, stage):
                if name == "commit_stage_hook" and stage == "after_effect_insert_before_commit":
                    fired["n"] += 1
                    raise OSError("synthetic failure after the effect, attempt and budget rows were written")

        bad = Failing(w.base / "dest", clock=lambda: w.e.now)
        bad.configure_selection_authority(w.anchor)
        pre = {k: v for k, v in dump_db(w.db).items() if k != "failure_records_v1"}
        res = AtomicLocalControlPlaneExecutor(workflow=None, destination=bad, policy=g.effect_policy()).execute(
            envelope=envelope_i(1), claim_id="claim-1", attempt_id="att-fail")
        post = counts(w.db)
        after = {k: v for k, v in dump_db(w.db).items() if k != "failure_records_v1"}
        retry = AtomicLocalControlPlaneExecutor(workflow=None, destination=w.fresh_dest(), policy=g.effect_policy()).execute(
            envelope=envelope_i(1), claim_id="claim-1", attempt_id="att-retry")
        post_retry = counts(w.db)
        chk.exercise(f"{name}: the injected failure actually fired inside the transaction", fired["n"] == 1, fired=fired["n"])
        chk.safety(f"{name}: executor did not report executed", res.status != "executed", status=res.status, error=res.error)
        chk.safety(f"{name}: zero effects, attempts, events, receipts, budget; claim issued",
                   (post["effects"], post["attempts"], post["attempt_events"], post["authority_effect_receipts_v1"], post["budget_used"]) == (0, 0, 0, 0, 0)
                   and post["claims"].get("claim-1") == "issued", post=post)
        chk.safety(f"{name}: every table (except the separate failure record) byte-identical to the pre-state", pre == after,
                   differing=[k for k in set(pre) | set(after) if pre.get(k) != after.get(k)])
        chk.exercise(f"{name}: failure surfaced as a pre-dispatch refusal (denied, attempted False)", res.status == "denied" and res.attempted is False, status=res.status)
        chk.exercise(f"{name}: clean retry commits exactly one effect (claim stayed usable)",
                     retry.status == "executed" and (post_retry["effects"], post_retry["authority_effect_receipts_v1"], post_retry["budget_used"]) == (1, 1, 1), retry=retry.status)
        obs[name] = {"status": res.status, "error": res.error, "failure_class": (res.control_plane_evidence or {}).get("failure_class"), "post": post, "post_retry": post_retry}
    ev["observed"].update(obs)
    chk.apply(ev)


# ======================================================================================================================== AT-4
def _crash_run(w: World, tmp: Path, stage: str):
    events, never = tmp / "events.jsonl", tmp / "never"
    V = Child("_probe_exec.py", exec_spec(w.base, 1, tmp, attempt_id="att-victim", hooks={stage: [["event", "parked"], ["wait", str(never)]]}), tmp, "V")
    try:
        parked = wait_event(events, "V", "parked", [V])
        rc = V.kill9() if parked else None
    finally:
        kill_all([V])
    return V, parked, rc


def test_b06_effect_process_sigkill_before_and_after_commit(tmp_path, ev):
    """B-06: a distinct OS process is SIGKILLed (kill -9) parked at (a) before commit and (b) after commit; then retry/replay semantics."""
    ev["scenario"] = "AT-4"
    ev["expected"] = ("(a) kill before commit: 0 effects/attempts/receipts, claim issued, budget 0, retry in a fresh process commits exactly 1; (b) kill after commit: exactly 1 effect, "
                      "1 receipt, claim consumed, reconcile=applied (not retry eligible), replay refused 'not usable', still 1 effect and budget 1; store known")
    chk, obs = Checks(), {}
    # ---- (a) before commit
    wa = World(tmp_path / "a")
    ta = tmp_path / "ta"
    ta.mkdir()
    V, parked, rc = _crash_run(wa, ta, "after_effect_insert_before_commit")
    mid = counts(wa.db)
    verify = wa.fresh_dest().verify_selection_store()
    R1, _ = run_exec(wa, 1, ta, "RETRY_A")
    r1 = R1.result()
    end = counts(wa.db)
    chk.exercise("(a) victim parked after the effect insert and was killed by SIGKILL", parked is not None and rc == -9, rc=rc)
    chk.safety("(a) after the kill: zero effects, attempts, events, receipts, budget; claim issued",
               (mid["effects"], mid["attempts"], mid["attempt_events"], mid["authority_effect_receipts_v1"], mid["budget_used"]) == (0, 0, 0, 0, 0) and mid["claims"].get("claim-1") == "issued", mid=mid)
    chk.safety("(a) store verifies known after the crash", verify.state == "known", state=verify.state, cause=verify.cause)
    chk.exercise("(a) fresh-process retry executes", (r1 or {}).get("status") == "executed", r1=r1)
    chk.safety("(a) after retry exactly one effect, one receipt, budget 1, claim consumed", (end["effects"], end["authority_effect_receipts_v1"], end["budget_used"]) == (1, 1, 1) and end["claims"].get("claim-1") == "consumed", end=end)
    obs["a"] = {"victim_pid": V.pid, "returncode": rc, "after_kill": mid, "retry": r1, "after_retry": end}
    # ---- (b) after commit
    wb = World(tmp_path / "b")
    tb = tmp_path / "tb"
    tb.mkdir()
    V2, parked2, rc2 = _crash_run(wb, tb, "after_commit")
    mid2 = counts(wb.db)
    verify2 = wb.fresh_dest().verify_selection_store()
    rec = AtomicLocalControlPlaneExecutor(workflow=None, destination=wb.fresh_dest(), policy=g.effect_policy()).reconcile(claim_id="claim-1", envelope=envelope_i(1))
    R2, _ = run_exec(wb, 1, tb, "REPLAY_B")
    r2 = R2.result()
    end2 = counts(wb.db)
    chk.exercise("(b) victim parked after COMMIT and was killed by SIGKILL", parked2 is not None and rc2 == -9, rc=rc2)
    chk.safety("(b) the committed effect survived the kill: 1 effect, 1 attempt, 1 receipt, claim consumed, budget 1",
               (mid2["effects"], mid2["attempts"], mid2["authority_effect_receipts_v1"], mid2["budget_used"]) == (1, 1, 1, 1) and mid2["claims"].get("claim-1") == "consumed", mid2=mid2)
    chk.safety("(b) store verifies known", verify2.state == "known", state=verify2.state, cause=verify2.cause)
    chk.safety("(b) reconcile reports applied and not retry eligible", rec.observed_state == "applied" and rec.observation.get("retry_eligible") is False, observation=rec.observation)
    chk.safety("(b) replay of the same claim is refused and creates no second effect",
               (r2 or {}).get("status") != "executed" and end2["effects"] == 1 and end2["budget_used"] == 1 and end2["authority_effect_receipts_v1"] == 1, r2=r2, end2=end2)
    chk.exercise("(b) replay refused for the intended reason 'execution claim is not usable'", "execution claim is not usable" in ((r2 or {}).get("error") or ""), r2=r2)
    obs["b"] = {"victim_pid": V2.pid, "returncode": rc2, "after_kill": mid2, "reconcile": rec.observation, "replay": r2, "after_replay": end2}
    ev["observed"].update(obs)
    chk.apply(ev)


def _part_b07(tmp_path):
    """B-07: the revocation writer is SIGKILLed after two uncommitted log inserts; authority state must be unchanged and usable.
    (Re-executed in the combined case after a harness defect in the first run: the full-table comparison was evaluated after the retry. Now the dump is taken right after the kill.)"""
    chk = Checks()
    w = World(tmp_path / "w", n_claims=1)
    tmp = tmp_path / "run"
    tmp.mkdir()
    events, never = tmp / "events.jsonl", tmp / "never"
    head0, anchor0, dump0 = counts(w.db)["log_head"], anchor_info(w.anchor), dump_db(w.db)
    Rv = Child("_probe_revoke.py", revoke_spec(w, tmp, versions=[2], revoked=REVOKE_PAIR, hooks={"after_log_insert@2": [["event", "parked"], ["wait", str(never)]]}), tmp, "R")
    try:
        parked = wait_event(events, "R", "parked", [Rv])
        rc = Rv.kill9() if parked else None
    finally:
        kill_all([Rv])
    verify = w.fresh_dest().verify_selection_store()
    state = w.fresh_dest().read_selection_state(v4.GS) if verify.state == "known" else None
    mid = counts(w.db)
    dump_mid = dump_db(w.db)  # immediately after the kill, BEFORE any retry
    anchor_mid = anchor_info(w.anchor)
    conn = sqlite3.connect(str(w.db))
    revoked_rows = conn.execute("SELECT COUNT(*) FROM selection_revoked_v1").fetchone()[0]
    conn.close()
    X, _ = run_exec(w, 1, tmp, "X")
    rx = X.result()
    end = counts(w.db)
    chk.exercise("writer parked at its second uncommitted log insert and was killed by SIGKILL", parked is not None and rc == -9, rc=rc)
    chk.safety("store known and log head unchanged after the torn transition", verify.state == "known" and mid["log_head"] == head0 == verify.head_sequence, state=verify.state, cause=verify.cause, head0=head0, mid=mid)
    chk.safety("no revoked row, anchor bytes unchanged, selection still active", revoked_rows == 0 and anchor_mid == anchor0 and state is not None and state.status == "active",
               revoked_rows=revoked_rows)
    chk.safety("every table identical to the pre-crash dump (taken right after the kill)", dump_mid == dump0,
               differing=[k for k in set(dump0) | set(dump_mid) if dump0.get(k) != dump_mid.get(k)])
    chk.exercise("claim-1 still executes once in a fresh process with receipt head = pre-crash head", (rx or {}).get("status") == "executed" and (rx or {}).get("receipt_head") == head0, rx=rx)
    chk.safety("exactly one effect after the retry", end["effects"] == 1 and end["authority_effect_receipts_v1"] == 1, end=end)
    return chk, {"events": scrub(None, read_events(events)), "writer_pid": Rv.pid, "returncode": rc, "after_kill": mid, "retry": rx, "after_retry": end}


# ======================================================================================================================== AT-5
def _corrupt_drop_table(w, tmp):
    # in-process first, on the already configured store (reaches the schema_missing path), then the physical drop remains for the fresh process
    conn = sqlite3.connect(str(w.db), isolation_level=None)
    conn.execute("DROP TABLE selection_activation_v1")
    conn.close()
    r = AtomicLocalControlPlaneExecutor(workflow=None, destination=w.dest, policy=g.effect_policy()).execute(envelope=envelope_i(1), claim_id="claim-1", attempt_id="att-inproc")
    cpe = r.control_plane_evidence or {}
    return {"inproc_status": r.status, "inproc_typed": cpe.get("selection_refusal")}


def _corrupt_damaged_row(w, tmp):
    conn = sqlite3.connect(str(w.db), isolation_level=None)
    conn.execute("UPDATE selection_activation_v1 SET valid_until='2099-01-01T00:00:00Z'")
    conn.close()
    return {}


def _corrupt_edit_log(w, tmp):
    conn = sqlite3.connect(str(w.db), isolation_level=None)
    conn.execute("DROP TRIGGER IF EXISTS selection_log_v1_no_update")
    raw = conn.execute("SELECT entry_json FROM selection_log_v1 WHERE activation_sequence=3").fetchone()[0]
    entry = json.loads(raw)
    entry["policy_generation"] = 2
    conn.execute("UPDATE selection_log_v1 SET entry_json=? WHERE activation_sequence=3", (sa.canonical_bytes(entry).decode("ascii"),))
    conn.close()
    return {}


def _corrupt_truncate(w, tmp):
    checkpoint(w.db)
    size = w.db.stat().st_size
    os.truncate(w.db, size // 2)
    return {"size_before": size, "size_after": w.db.stat().st_size}


@pytest.mark.parametrize("variant,corrupt,cause_prefix", [
    ("drop_table", _corrupt_drop_table, ("schema_missing", "table_mismatch:selection_activation_v1")),
    ("damaged_row", _corrupt_damaged_row, ("table_mismatch:selection_activation_v1",)),
    ("edit_log_entry", _corrupt_edit_log, ("log_integrity:entry_hash_mismatch",)),
    ("truncated_file", _corrupt_truncate, ()),
])
def test_b08_b11_corrupted_durable_authority_fails_closed(tmp_path, ev, variant, corrupt, cause_prefix):
    """B-08..B-11: damaged / dropped / edited / truncated durable authority; a fresh OS process then attempts the claim."""
    ev["scenario"] = "AT-5"
    ev["expected"] = ("store verifies known before; after the corruption a fresh process is refused typed store_unknown / HOLD (cause from the corruption), zero effects, claim issued, "
                      "budget 0 (truncated file: any failure that is not a committed effect; untyped error is CHARACTERIZED)")
    chk = Checks()
    w = World(tmp_path / "w", n_claims=1)
    tmp = tmp_path / "run"
    tmp.mkdir()
    pre = w.dest.verify_selection_store()
    chk.exercise("control: store known and selection active before the corruption", pre.state == "known" and w.e.state().status == "active")
    info = corrupt(w, tmp)
    X, rc = run_exec(w, 1, tmp, "X")
    rx = X.result() or {}
    post = counts(w.db)
    typed = typed_of(rx)
    ev["observed"].update(variant=variant, corruption=info, probe=X.summary(), post=post, pid=X.pid)
    if variant == "truncated_file":
        chk.exercise("the file was really truncated", info["size_after"] < info["size_before"], **info)
        chk.safety("no effect committed (probe not executed; no readable effect row)", rx.get("status") != "executed" and (post.get("effects", 0) == 0), rx=rx, post=post)
        chk.exercise("probe produced an outcome", bool(rx))
        verdict = chk.apply(ev, "truncated database file")
        if verdict == "HELD" and not (typed.get("code") == "store_unknown" and typed.get("refusal_class") == "HOLD"):
            ev["verdict"] = "CHARACTERIZED"
            ev["note"] += f" | fail-closed but NOT a typed HOLD: status={rx.get('status')} exception={rx.get('exception')} typed={typed}"
        return
    chk.safety("not executed; zero effects, attempts, receipts, budget; claim-1 issued",
               rx.get("status") != "executed" and (post["effects"], post["attempts"], post["authority_effect_receipts_v1"], post["budget_used"]) == (0, 0, 0, 0)
               and post["claims"].get("claim-1") == "issued", rx=rx, post=post)
    chk.exercise("refused typed store_unknown / HOLD", typed.get("code") == "store_unknown" and typed.get("refusal_class") == "HOLD", typed=typed, rx=rx)
    chk.exercise("cause names the corruption", any(str(typed.get("cause", "")).startswith(p) for p in cause_prefix), cause=typed.get("cause"), expected=cause_prefix)
    if variant == "drop_table":
        t0 = info.get("inproc_typed") or {}
        chk.safety("in-process (store already configured) attempt also refused, no effect", info.get("inproc_status") != "executed")
        chk.exercise("in-process path reached cause schema_missing (HOLD)", t0.get("code") == "store_unknown" and t0.get("cause") == "schema_missing", typed=t0)
    chk.apply(ev)


# ======================================================================================================================== AT-6
def _part_b12(tmp_path):
    """B-12: rollback attack (older DB file restored over a store whose anchor moved on) and anchor deletion.
    (Re-executed in the combined case after a harness defect in the first run: the older file was copied IN PLACE over a database the parent still had open.
    The restore now replaces the file atomically with os.replace after unlinking -wal/-shm.)"""
    chk, obs = Checks(), {}
    # ---- rollback attack
    w = World(tmp_path / "a", n_claims=2)
    ta = tmp_path / "ta"
    ta.mkdir()
    checkpoint(w.db)
    old = ta / "old.sqlite3"
    shutil.copy2(w.db, old)
    a_before = anchor_info(w.anchor)
    Rv = Child("_probe_revoke.py", revoke_spec(w, ta, versions=[2], revoked=REVOKE_PAIR), ta, "R")
    rcR = Rv.wait()
    a_after = anchor_info(w.anchor)
    C2, _ = run_exec(w, 2, ta, "CTRL")
    rc2 = C2.result()
    for suffix in ("-wal", "-shm"):
        p = Path(str(w.db) + suffix)
        if p.exists():
            p.unlink()
    staged = w.db.parent / "restore.tmp"
    shutil.copy2(old, staged)
    os.replace(staged, w.db)
    restored = counts(w.db)
    X, _ = run_exec(w, 1, ta, "X")
    rx = X.result() or {}
    post = counts(w.db)
    chk.exercise("revocation committed in a separate process and the anchor advanced past the old copy", rcR == 0 and a_after["head_sequence"] > a_before["head_sequence"], before=a_before, after=a_after)
    chk.exercise("control: before the rollback the revocation was effective (claim-2 selection_revoked)", typed_of(rc2).get("code") == "selection_revoked", rc2=rc2)
    chk.exercise("the older database really was restored (log head back to 3, claim-1 issued)", restored.get("log_head") == 3 and restored.get("claims", {}).get("claim-1") == "issued", restored=restored)
    chk.safety("restored older store: claim-1 not executed, zero effects", rx.get("status") != "executed" and post.get("effects") == 0 and post.get("authority_effect_receipts_v1") == 0, rx=rx, post=post)
    chk.exercise("refused typed store_unknown / HOLD with cause anchor_ahead", typed_of(rx).get("code") == "store_unknown" and typed_of(rx).get("refusal_class") == "HOLD" and typed_of(rx).get("cause") == "anchor_ahead", typed=typed_of(rx))
    obs["rollback"] = {"anchor_before": a_before, "anchor_after": a_after, "control": rc2, "restored": restored, "probe": rx, "post": post, "pids": {"revoker": Rv.pid, "ctrl": C2.pid, "victim": X.pid}}
    # ---- anchor deleted
    w2 = World(tmp_path / "b", n_claims=1)
    tb = tmp_path / "tb"
    tb.mkdir()
    pre2 = w2.dest.verify_selection_store()
    for p in (w2.anchor, Path(str(w2.anchor) + ".lock")):
        if p.exists():
            p.unlink()
    head_before = counts(w2.db)["log_head"]
    Y, _ = run_exec(w2, 1, tb, "Y")
    ry = Y.result() or {}
    post2 = counts(w2.db)
    regen = {}
    try:
        w2.fresh_dest().sync_selection("baseline", determination_ref=v4.DET2)
        regen["outcome"] = "ACCEPTED"
    except sa.SelectionRefusal as exc:
        regen.update(outcome="refused", code=exc.code, refusal_class=exc.refusal_class, cause=exc.cause)
    post3 = counts(w2.db)
    chk.exercise("control: store known before the anchor was deleted", pre2.state == "known")
    chk.safety("anchor missing: claim not executed, zero effects", ry.get("status") != "executed" and post2["effects"] == 0 and post2["authority_effect_receipts_v1"] == 0, ry=ry, post=post2)
    chk.exercise("refused typed store_unknown / HOLD with cause anchor_absent", typed_of(ry).get("code") == "store_unknown" and typed_of(ry).get("refusal_class") == "HOLD" and typed_of(ry).get("cause") == "anchor_absent", typed=typed_of(ry))
    chk.safety("a fresh genesis baseline is refused; no new log row; no anchor re-created", regen.get("outcome") == "refused" and regen.get("code") == "store_unknown" and post3["log_head"] == head_before and not w2.anchor.exists(), regen=regen, head_before=head_before, head_after=post3["log_head"])
    obs["anchor_deleted"] = {"probe": ry, "post": post2, "rebaseline": regen, "pid": Y.pid}
    return chk, obs


def test_b07_b12_rerun_combined(tmp_path, ev):
    """B-07 (AT-4, authority-writer SIGKILL) and B-12 (AT-6, restored older store / missing anchor) as ONE budgeted re-execution after the first run's
    two harness defects (see FINDINGS). Part verdicts are recorded separately; the case verdict is the worst of the two."""
    ev["scenario"] = "AT-4+AT-6"
    ev["expected"] = ("B-07: after kill -9 of the writer at its 2nd uncommitted log insert: store known, all tables identical, head/anchor unchanged, claim still executes once. "
                      "B-12: restored older DB -> store_unknown HOLD cause anchor_ahead (revocation not resurrected), anchor deleted -> HOLD anchor_absent, re-genesis refused")
    ev["mandatory"] = False
    parts = {}
    for name, fn, sub in (("B-07", _part_b07, "b07"), ("B-12", _part_b12, "b12")):
        chk, obs = fn(tmp_path / sub)
        holder = {"observed": {}}
        verdict = chk.apply(holder, name)
        parts[name] = {"verdict": verdict, "note": holder["note"], "checks": holder["observed"]["checks"], "observed": obs}
    ev["observed"].update(parts=parts, part_verdicts={k: v["verdict"] for k, v in parts.items()})
    vs = [v["verdict"] for v in parts.values()]
    ev["verdict"] = "BREACH" if "BREACH" in vs else "INCONCLUSIVE" if "INCONCLUSIVE" in vs else "HELD"
    ev["note"] = "; ".join(f"{k}: {v['verdict']} {v['note']}" for k, v in parts.items())


def test_b13_anchor_monotone_across_process_restart(tmp_path, ev):
    """B-13: process 1 advances the store, process 2 (restart) verifies, tries to move the anchor backwards / sideways, then executes."""
    ev["scenario"] = "AT-6"
    ev["expected"] = ("anchor head sequence 3 -> 5 -> 5 never decreases; restart verifies known at head 5; older advance returns 'stale' with file bytes unchanged; equal-position "
                      "different-hash raises anchor_equal_position_conflict with bytes unchanged; post-restart execution commits exactly 1 effect with receipt head 5")
    chk = Checks()
    w = World(tmp_path / "w", n_claims=1)
    tmp = tmp_path / "run"
    tmp.mkdir()
    a3 = json.loads(w.anchor.read_text())["anchor"]
    h_a = anchor_info(w.anchor)["head_sequence"]
    P1 = Child("_probe_revoke.py", revoke_spec(w, tmp, versions=[2, 3]), tmp, "P1")
    rc1 = P1.wait()
    h_b = anchor_info(w.anchor)["head_sequence"]
    P2 = Child("_probe_restart.py", {"base": str(w.base), "older_anchor": a3}, tmp, "P2")
    rc2 = P2.wait()
    r2 = P2.result() or {}
    h_c = anchor_info(w.anchor)["head_sequence"]
    post = counts(w.db)
    chk.exercise("process 1 advanced the store twice (anchor 3 -> 5)", rc1 == 0 and (h_a, h_b) == (3, 5), h_a=h_a, h_b=h_b, p1=P1.summary())
    chk.exercise("restart probe completed", rc2 == 0 and "exception" not in r2 and bool(r2), r2=r2)
    chk.safety("anchor head sequence never decreases across the restart", h_a <= h_b <= h_c and r2.get("anchor_head_before") == 5 and r2.get("anchor_head_after", 0) >= 5, seq=[h_a, h_b, h_c])
    chk.safety("restarted process verifies the store known at head 5", (r2.get("verify") or [None])[0] == "known" and (r2.get("verify") or [0, 0, 0])[2] == 5, verify=r2.get("verify"))
    chk.safety("an older anchor is not accepted: advance returns 'stale' and the file is unchanged", r2.get("advance_older") == "stale" and r2.get("bytes_same_after_older") is True, r2=r2)
    chk.safety("equal-position different-hash anchor is refused and the file is unchanged", str(r2.get("advance_conflict", "")).endswith("anchor_equal_position_conflict") and r2.get("bytes_same_after_conflict") is True, r2=r2)
    chk.exercise("legitimate path after restart executes exactly once", r2.get("status") == "executed" and r2.get("receipt_head") == 5 and post["effects"] == 1, r2=r2, post=post)
    ev["observed"].update(anchor_sequence=[h_a, h_b, h_c], pids={"P1": P1.pid, "P2": P2.pid}, p1=P1.summary(), p2=r2, post=post)
    chk.apply(ev)


# ======================================================================================================================== AT-7
def test_b14_refusals_leave_no_partial_rows(tmp_path, ev):
    """B-14 (in-process by design): full-table row hashes of every table plus the anchor file bytes, before and after each refusal."""
    ev["scenario"] = "AT-7"
    ev["expected"] = ("each executor-side and writer-side refusal raises the expected PermissionError (typed SelectionRefusal where applicable) and leaves every table of the database and the "
                      "anchor file byte-identical to before (including the late refusals: duplicate attempt id and exhausted budget after the guard passed)")
    chk, obs = Checks(), {}
    w = World(tmp_path / "w", n_claims=6, budgets={1: "budget-s", 4: "budget-s"})
    pol = g.effect_policy()
    kw = dict(policy_effective_digest=sa.policy_digest_of(pol), policy_effective_sets=sa.policy_sets_of(pol))

    def snap():
        return dump_db(w.db), w.anchor.read_bytes() if w.anchor.exists() else None

    def refuse(label, fn, exc_type, contains=None, code=None):
        before = snap()
        try:
            fn()
            outcome = {"raised": None}
        except exc_type as exc:
            outcome = {"raised": type(exc).__name__, "text": str(exc)[:160], "code": getattr(exc, "code", None), "cls": getattr(exc, "refusal_class", None)}
        except BaseException as exc:  # noqa: BLE001
            outcome = {"raised": "UNEXPECTED " + type(exc).__name__, "text": str(exc)[:160]}
        after = snap()
        expected = outcome.get("raised") not in (None,) and not str(outcome["raised"]).startswith("UNEXPECTED") and (contains is None or contains in outcome["text"]) and (code is None or outcome.get("code") == code)
        chk.exercise(f"{label}: refused as expected", expected, **outcome)
        chk.safety(f"{label}: all tables and anchor bytes unchanged", before == after,
                   differing=[k for k in set(before[0]) | set(after[0]) if before[0].get(k) != after[0].get(k)], anchor_changed=before[1] != after[1])
        obs[label] = outcome

    def run(i, attempt, env=None):
        return lambda: w.dest.execute_claim_atomic(f"claim-{i}", snapshot_envelope(env or envelope_i(i)), attempt_id=attempt, **kw)

    refuse("unknown_claim", run(99, "att-x", envelope_i(1)), PermissionError, "execution claim unavailable")
    ok = run(1, "att-1")()
    chk.exercise("control: claim-1 executes once", ok["newly_executed"] is True and counts(w.db)["effects"] == 1)
    refuse("duplicate_attempt_id_after_guard", run(2, "att-1"), PermissionError, "attempt identity already exists")
    refuse("operation_mismatch", run(3, "att-3", envelope_i(3, amount=999.0)), PermissionError, "execution claim operation mismatch")
    refuse("shared_budget_exhausted_after_guard", run(4, "att-4"), PermissionError, "authoritative effect budget exhausted")
    base_now = w.e.now
    w.e.now = base_now + timedelta(days=10)
    refuse("claim_outside_validity_interval", run(5, "att-5"), PermissionError, "outside validity interval")
    w.e.now = base_now
    refuse("writer_stale_epoch_reactivation", lambda: w.e.activate(w.stmt), sa.SelectionRefusal, code="selection_epoch_stale")
    w.e.sync(2, revoked_selections=frozenset({("sel-test-1", 1)}))
    chk.exercise("control: revocation committed (state revoked)", w.e.state().status == "revoked")
    refuse("claim_after_revocation", run(6, "att-6"), sa.SelectionRefusal, code="selection_revoked")
    refuse("writer_older_snapshot", lambda: w.e.sync(1), sa.SelectionRefusal, code="trust_snapshot_version_stale")
    refuse("writer_withdraw_of_revoked_row", lambda: w.e.withdraw(v4.withdraw_stmt(w.stmt, 2)), sa.SelectionRefusal)
    post = counts(w.db)
    chk.safety("only the single control effect exists", (post["effects"], post["attempts"], post["authority_effect_receipts_v1"], post["budget_used"]) == (1, 1, 1, 1), post=post)
    chk.safety("store known at the end", w.fresh_dest().verify_selection_store().state == "known")
    ev["observed"].update(refusals=obs, post=post)
    chk.apply(ev)
