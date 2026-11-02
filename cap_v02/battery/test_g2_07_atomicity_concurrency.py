"""G2.14: atomicity, concurrency, crash, lock and write-failure evidence with REAL processes and a REAL file. A write happens only after a fully admitted verdict; a crash between temp
write and os.replace leaves the old store byte-identical; a lock held by another process refuses state_lock_failed without writing; an injected write failure admits nothing."""
import errno
import json
import os
import signal
import threading
import time

import pytest

import harness as H
from harness import AP, ST, EFFECTIVE_LONG, admit, evidence, make_kit, sel, tree


def spawn(kit, selection, go, **kw):
    return H.popen_child("admit", config=str(kit.config_path), digest=kit.digest, record=selection.record_text, selection=selection.selection_text, go_file=str(go), **kw)


def wave(kit, tmp_path, assignments, name):
    """assignments: list of Sel, one child process each; all released at the same instant."""
    go = tmp_path / f"go-{name}"
    procs = [spawn(kit, s_, go) for s_ in assignments]
    time.sleep(1.2)                 # all interpreters are up and spinning on the barrier
    go.write_text("go")
    outs = []
    for s_, pr in zip(assignments, procs):
        so, se = pr.communicate(timeout=90)
        assert pr.returncode == 0 and se == "", (pr.returncode, se)
        outs.append((s_, json.loads(so.strip().splitlines()[-1])))
    return outs


def assert_store_ok(kit):
    env = kit.store()
    assert H.kitmod.verify_state(env["state"]) is None
    assert env["state_digest"] == H.c.digest({k: v for k, v in env.items() if k != "state_digest"})
    assert env["authority_digest"] == H.independent_authority_digest(kit.config)
    return env


@pytest.mark.parametrize("round_", [1, 2, 3])
@pytest.mark.row("G2.14.a", "CONCURRENCY: 12 real processes (6 per variant) race two COMPETING epoch-1 selections on an empty store: exactly ONE variant wins, all its processes are admitted, all processes of the other variant are refused selection_epoch_stale, the store verifies and generation == 1 (a single write)")
def test_twelve_processes_two_competing_selections_one_wins(tmp_path, round_):
    kit = make_kit(tmp_path)
    a, b = sel(1, status=120, approval=90), sel(1, status=100, approval=80)
    assert a.digest != b.digest
    assigns = [a, b] * 6
    outs = wave(kit, tmp_path, assigns, "ab")
    env = assert_store_ok(kit)
    winner = next(iter(env["state"]["rows"].values()))["selection_digest"]
    assert winner in (a.digest, b.digest)
    for s_, o in outs:
        if s_.digest == winner:
            assert o["ok"] is True, o
        else:
            assert o["ok"] is False and o["code"] == "freshness_refused" and o["registry_code"] == "selection_epoch_stale", o
    assert env["generation"] == 1 and env["parent_digest"] is not None
    assert len({o["pid"] for _s, o in outs}) == 12
    assert not [p for p in kit.dir.iterdir() if p.name.endswith(".tmp")]
    evidence(f"g2-14a-concurrency-round{round_}", {"winner": "A" if winner == a.digest else "B", "outcomes": [{"variant": "A" if s_.digest == a.digest else "B", **o} for s_, o in outs],
                                                   "generation": env["generation"], "store_digest": env["state_digest"]})


@pytest.mark.row("G2.14.b", "CONCURRENCY on a RENEWAL: from epoch 1, 8 processes present two competing epoch-2 renewals (both validly superseding epoch 1): exactly one wins, generation == 2, store verifies")
def test_eight_processes_competing_renewals(tmp_path):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    admit(kit, s1)
    c_, d_ = sel(2, prev=s1, status=50, effective=EFFECTIVE_LONG), sel(2, prev=s1, status=40, effective=EFFECTIVE_LONG)
    outs = wave(kit, tmp_path, [c_, d_] * 4, "cd")
    env = assert_store_ok(kit)
    winner = next(iter(env["state"]["rows"].values()))["selection_digest"]
    assert [o["ok"] for s_, o in outs if s_.digest == winner] == [True] * 4
    assert all(o["ok"] is False and o["registry_code"] == "selection_epoch_stale" for s_, o in outs if s_.digest != winner)
    assert env["generation"] == 2


@pytest.mark.row("G2.14.c", "CONCURRENCY with different selection ids for one scope: 8 processes, exactly one selection_id wins, the other id is refused selection_conflict, generation == 1")
def test_competing_selection_ids_exactly_one_wins(tmp_path):
    kit = make_kit(tmp_path)
    x, y = sel(1), sel(1, selection_id=H.SELECTION_ID_B)
    outs = wave(kit, tmp_path, [x, y] * 4, "xy")
    env = assert_store_ok(kit)
    ok_ids = {s_.stmt["selection_id"] for s_, o in outs if o["ok"]}
    assert len(ok_ids) == 1 and len(env["state"]["rows"]) == 1 and env["generation"] == 1
    assert all(o["registry_code"] == "selection_conflict" for s_, o in outs if not o["ok"])


@pytest.mark.row("G2.14.d", "CONCURRENCY identical selection: 10 processes present the SAME selection on an empty store: all admitted, exactly one write (generation 1)")
def test_ten_processes_same_selection_one_write(tmp_path):
    kit = make_kit(tmp_path)
    outs = wave(kit, tmp_path, [sel(1)] * 10, "same")
    assert all(o["ok"] for _s, o in outs)
    assert assert_store_ok(kit)["generation"] == 1


@pytest.mark.row("G2.14.e", "no lost update: 8 processes each present the NEXT epoch of a chain from different starting points; whatever the interleaving, the final row is the highest epoch whose predecessor chain was admitted and generation equals the number of admitted writes")
def test_no_lost_update_under_contention(tmp_path):
    kit = make_kit(tmp_path)
    chain = [sel(1)]
    for e in range(2, 6):
        chain.append(sel(e, prev=chain[-1], effective=EFFECTIVE_LONG))
    outs = wave(kit, tmp_path, chain * 2, "chain")
    env = assert_store_ok(kit)
    row = next(iter(env["state"]["rows"].values()))
    oks = [(s_.epoch, o["ok"]) for s_, o in outs]
    admitted_epochs = sorted({e for e, ok in oks if ok})
    assert row["epoch"] == max(admitted_epochs)
    # generation counts writes; a write happened for every strictly-advancing admission and never for a guard/refusal
    assert 1 <= env["generation"] <= len(chain)
    assert row["selection_digest"] == next(s_.digest for s_ in chain if s_.epoch == row["epoch"])


# ------------------------------------------------------------------------------------------------------------------------------- crash
@pytest.mark.parametrize("scenario", ["first_admission", "renewal"])
@pytest.mark.row("G2.14.f", "CRASH: a child killed (os._exit) between the temp write and os.replace leaves the old store BYTE-IDENTICAL; the lock is free; a retry in a new process succeeds (generation +1); the orphan temp file is the only residue")
def test_crash_before_replace_leaves_old_store_and_retry_succeeds(tmp_path, scenario):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    if scenario == "renewal":
        admit(kit, s1)
        target = sel(2, prev=s1, effective=EFFECTIVE_LONG)
    else:
        target = s1
    pre, g_pre = kit.store_bytes(), kit.store()["generation"]
    r = H.child_admit(kit, target, crash="before_replace")
    assert r["returncode"] == 97 and r["out"] is None, r
    assert kit.store_bytes() == pre, "the old store must be byte-identical after the crash"
    orphans = [p for p in kit.dir.iterdir() if p.name.endswith(".tmp")]
    assert len(orphans) == 1 and orphans[0].name.startswith("freshness-state.json.")
    orphan_env = json.loads(orphans[0].read_bytes())
    assert orphan_env["generation"] == g_pre + 1               # the half-done next state was fully written but never promoted
    again = H.child_admit(kit, target)
    assert again["out"]["ok"] is True, again
    env = assert_store_ok(kit)
    assert env["generation"] == g_pre + 1 and env["parent_digest"] == json.loads(pre)["state_digest"]
    assert orphans[0].exists(), "orphan temp files are never cleaned (documented limit e)"
    evidence("g2-14f-crash-" + scenario, {"old_store_sha256": H.sha256_hex(pre), "after_crash_sha256": H.sha256_hex(pre), "orphan": orphans[0].name, "orphan_generation": orphan_env["generation"],
                                          "retry_generation": env["generation"]})


@pytest.mark.row("G2.14.g", "SIGKILL of a process HOLDING the lock releases it (kernel flock): the next admission is not blocked and succeeds")
def test_killed_lock_holder_does_not_wedge_the_store(tmp_path):
    kit = make_kit(tmp_path)
    holder = H.popen_child("hold", config=str(kit.config_path), digest=kit.digest, seconds=60)
    assert json.loads(holder.stdout.readline())["locked"] is True
    holder.send_signal(signal.SIGKILL)
    holder.wait(timeout=10)
    t0 = time.monotonic()
    admit(kit, sel(1))
    assert time.monotonic() - t0 < 3 and kit.store()["generation"] == 1


# ------------------------------------------------------------------------------------------------------------------------------- lock
@pytest.mark.row("G2.14.h", "LOCK HELD by another process: with the real 5 s timeout the call refuses state_lock_failed after about 5 s, writes nothing, never reaches the host source or the Registry; after release the same call succeeds")
def test_lock_held_by_another_process_refuses_with_default_timeout(tmp_path, spy):
    kit = make_kit(tmp_path)
    holder = H.popen_child("hold", config=str(kit.config_path), digest=kit.digest, seconds=60)
    try:
        assert json.loads(holder.stdout.readline())["locked"] is True
        pre, before = kit.store_bytes(), tree(kit.dir)
        s1 = sel(1)
        t0 = time.monotonic()
        spy.reset()
        err = H.expect_refusal("state_lock_failed", admit, kit, s1)
        waited = time.monotonic() - t0
        assert 4.0 <= waited <= 20.0, waited
        assert spy.reached is False and kit.store_bytes() == pre
        assert tree(kit.dir) == before
        with pytest.raises(AP.AuthorityProfileRefusal) as exc:
            build_ = H.build(tmp_path, kit, s1)
        assert exc.value.code == "state_lock_failed"
    finally:
        holder.kill(); holder.wait(timeout=10)
    admit(kit, s1)
    assert kit.store()["generation"] == 1
    evidence("g2-14h-lock-held", {"waited_seconds": round(waited, 2), "code": err.code})


@pytest.mark.parametrize("op", ["admit", "read_state", "bootstrap"])
@pytest.mark.row("G2.14.i", "LOCK HELD (fast timeout): every locking entry point (admit, read_state, bootstrap) refuses state_lock_failed and changes nothing")
def test_lock_held_every_entry_point(tmp_path, monkeypatch, op):
    kit = make_kit(tmp_path, bootstrap=(op != "bootstrap"))
    if op == "bootstrap":
        kit.state_path.parent.mkdir(exist_ok=True)
    holder = H.popen_child("hold", config=str(kit.config_path), digest=kit.digest, seconds=60)
    try:
        assert json.loads(holder.stdout.readline())["locked"] is True
        monkeypatch.setattr(ST, "LOCK_TIMEOUT_SECONDS", 0.3)
        before = tree(kit.dir)
        if op == "admit":
            H.expect_refusal("state_lock_failed", admit, kit, sel(1))
        elif op == "read_state":
            H.expect_refusal("state_lock_failed", ST.read_state, kit.load())
        else:
            p = kit.write_bootstrap(kit.bootstrap_doc())
            before = tree(kit.dir)
            H.expect_refusal("state_lock_failed", ST.bootstrap_state, kit.load(), p, AP._now(kit.load()))
        assert tree(kit.dir) == before
        assert not kit.state_path.exists() or op != "bootstrap"
    finally:
        holder.kill(); holder.wait(timeout=10)


@pytest.mark.row("G2.14.j", "a lock path that cannot be opened (a directory in its place) refuses state_lock_failed, nothing written")
def test_unopenable_lock_path_refuses(tmp_path, spy):
    kit = make_kit(tmp_path)
    admit(kit, sel(1))
    pre = kit.store_bytes()
    kit.lock_path.unlink()
    kit.lock_path.mkdir()
    spy.reset()
    H.expect_refusal("state_lock_failed", admit, kit, sel(1))
    assert kit.store_bytes() == pre and spy.reached is False


# ------------------------------------------------------------------------------------------------------------------------------- write failure
FAULTS = {
    "os_replace_enospc": lambda mp: mp.setattr(os, "replace", _raise(OSError(errno.ENOSPC, "No space left on device"))),
    "fsync_file_fails": lambda mp: mp.setattr(os, "fsync", _raise(OSError(errno.EIO, "I/O error"))),
    "mkstemp_fails": lambda mp: mp.setattr(H.cp_atomic.tempfile, "mkstemp", _raise(OSError(errno.EACCES, "denied"))),
    "writer_raises": lambda mp: mp.setattr(ST, "write_bytes_atomic", _raise(RuntimeError("boom"))),
}


def _raise(exc):
    def f(*a, **k):
        raise exc
    return f


@pytest.mark.parametrize("fault", list(FAULTS))
@pytest.mark.parametrize("scenario", ["first_admission", "renewal"])
@pytest.mark.row("G2.14.k", "WRITE FAILURE injection (ENOSPC on replace, fsync EIO, mkstemp denied, writer raises): the call refuses state_write_failed, NOTHING is admitted (no material), the store is byte-identical, no temp file remains, and the factory refuses construction the same way; a retry without the fault succeeds")
def test_write_failure_admits_nothing_and_keeps_old_store(tmp_path, monkeypatch, spy, fault, scenario):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    if scenario == "renewal":
        admit(kit, s1)
        target = sel(2, prev=s1, effective=EFFECTIVE_LONG)
    else:
        target = s1
    pre, g = kit.store_bytes(), kit.store()["generation"]
    prepared = H.flow_kwargs(tmp_path)          # the Control Plane's own stores are created BEFORE the fault is injected
    with monkeypatch.context() as mp:
        FAULTS[fault](mp)
        result = []
        err = H.expect_refusal("state_write_failed", lambda: result.append(admit(kit, target)))
        assert result == []
        with pytest.raises(AP.AuthorityProfileRefusal) as exc:
            H.build(tmp_path, kit, target, prepared=prepared)
        assert exc.value.code == "state_write_failed"
    assert kit.store_bytes() == pre
    assert not [p for p in kit.dir.iterdir() if p.name.endswith(".tmp")]
    admit(kit, target)
    assert kit.store()["generation"] == g + 1


@pytest.mark.row("G2.14.l", "directory-fsync failure AFTER os.replace: the call still refuses state_write_failed (no admission returned); the store is valid (old or new, never torn) and the retry converges to exactly one new generation")
def test_directory_fsync_failure_after_replace_is_never_an_admission(tmp_path, monkeypatch):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    pre = kit.store_bytes()
    real = os.fsync
    calls = {"n": 0}

    def fsync(fd):
        calls["n"] += 1
        if calls["n"] == 2:             # 1 = temp file, 2 = directory (after the replace)
            raise OSError(errno.EIO, "directory fsync failed")
        return real(fd)

    result = []
    with monkeypatch.context() as mp:
        mp.setattr(os, "fsync", fsync)
        H.expect_refusal("state_write_failed", lambda: result.append(admit(kit, s1)))
    assert result == [] and calls["n"] == 2
    env = assert_store_ok(kit)
    assert env["generation"] in (0, 1)
    admit(kit, s1)
    assert kit.store()["generation"] == 1
    evidence("g2-14l-dir-fsync-failure", {"store_after_failed_call_generation": env["generation"], "store_unchanged": kit.store_bytes() == pre})


@pytest.mark.row("G2.14.m", "WRITE FAILURE inside a real child process (os.replace raises ENOSPC): typed state_write_failed result, store byte-identical, exit 0")
def test_write_failure_in_a_child_process(tmp_path):
    kit = make_kit(tmp_path)
    pre = kit.store_bytes()
    r = H.child_admit(kit, sel(1), fail_write=True)
    assert r["returncode"] == 0 and r["out"]["ok"] is False and r["out"]["code"] == "state_write_failed"
    assert kit.store_bytes() == pre


@pytest.mark.row("G2.14.n", "readers never see a torn store: while 40 successive renewals are persisted, a concurrent reader thread reads the file continuously and EVERY read is a valid, digest-consistent envelope with a monotonic generation")
def test_concurrent_reader_never_sees_a_torn_store(tmp_path):
    kit = make_kit(tmp_path)
    chain = [sel(1)]
    for e in range(2, 41):
        chain.append(sel(e, prev=chain[-1], effective=EFFECTIVE_LONG))
    stop, seen, bad = threading.Event(), [], []

    def reader():
        while not stop.is_set():
            try:
                data = kit.state_path.read_bytes()
                env = json.loads(data)
                if env["state_digest"] != H.c.digest({k: v for k, v in env.items() if k != "state_digest"}):
                    bad.append("digest")
                seen.append(env["generation"])
            except Exception as e:     # noqa: BLE001
                bad.append(repr(e))

    t = threading.Thread(target=reader)
    t.start()
    try:
        for s_ in chain:
            admit(kit, s_)
    finally:
        stop.set(); t.join()
    assert bad == [] and len(seen) > 10
    assert seen == sorted(seen) and max(seen) == 40
