"""A1 scenario ``nc_process_kill``: a REAL OS-level SIGKILL of a child process running the pinned route B atomic executor (proposed).

SPDX-License-Identifier: Apache-2.0

Design (no ``simulate=`` fault, no in-process exception, no ``os._exit`` by the target):

  parent (pytest)                         victim (subprocess, role ``victim``)                 observer (subprocess, role ``recover``)
  ---------------                         ------------------------------------                 ---------------------------------------
  spawn victim, stdout=PIPE   ------>     wire the pinned tuple (conftest), build Ctx on a
                                          durable on-disk work dir (CP run.json + SQLite),
                                          provision the claim, write setup.json
                                          call AtomicLocalControlPlaneExecutor.execute(...)
                                          reach the pinned destination's documented
                                          ``_transaction_stage(<seam>)`` hook -> print READY
                                          on the pipe, then BLOCK (sleep loop). It performs
                                          no fault; the hook is only the synchronization point.
  block on the pipe until READY (select,
  bounded by a timeout that can only turn
  into a FAILURE, never a pass)
  record pid evidence, file hashes
  os.kill(pid, SIGKILL)  <----- real signal from another process
  waitpid -> returncode == -9; /proc/<pid> gone
  hash the on-disk store before ANY open
  (hot-journal evidence), copy it
  spawn observer ------------------------------------------------------------------>   a fresh Python process (new pid) reopens the SAME on-disk
                                                                                       store (persisted CP run record + SQLite), reads the claim and
                                                                                       effects, calls reconcile_claim, presents the claim again TWICE
                                                                                       through the pinned executor, reads back after each step.

The seam is deterministic because the victim blocks AT the seam until it is killed: there is no race and no sleep-based timing.
Seams (the pinned ``execute_claim_atomic`` hook names, Runtime c5e97e87 ``engine/local_authority_effect.py``): ``after_begin`` and
``after_effect_insert_before_commit`` (kill inside the open write transaction) and ``after_commit`` (kill after the durable COMMIT, before
the caller can receive an acknowledgement). ``before_begin`` and ``before_failure_record`` are not seams of the pinned route B executor
for this row (``before_failure_record`` belongs to the frozen F5b reference of the historical c08 scenario; the route B executor has no such stage).

What is NOT exercised, not claimed: power loss / OS crash, a kill during Replay / Evidence Pack / Verifier steps, a kill of the Control
Plane process, disk or filesystem corruption, a kill during claim provisioning. SQLite durability here relies on the kernel keeping written
pages after the writer is killed (process death, not power loss).

Recorded as raw observations; no verdict is computed in this module.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import select
import signal
import sqlite3
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
SEAMS = ("after_begin", "after_effect_insert_before_commit", "after_commit")
PRECOMMIT = ("after_begin", "after_effect_insert_before_commit")
READY_TIMEOUT = float(os.environ.get("MVP_KILL_READY_TIMEOUT", "180"))
CHILD_TIMEOUT = 240


def _sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _files(directory: pathlib.Path) -> dict:
    return {p.name: {"sha256": _sha(p), "size": p.stat().st_size} for p in sorted(directory.iterdir()) if p.is_file()}


# =============================================================================================================== child roles
def _wire_child():
    sys.path.insert(0, str(HERE))
    sys.dont_write_bytecode = True
    import conftest  # noqa: F401  (wires the pinned tuple from the MVP_*_DIR variables exactly as the suite does)
    import _state
    if _state.ENV["problems"]:
        raise SystemExit("child cannot wire the pinned tuple: " + "; ".join(_state.ENV["problems"]))


def _read_tables(db: pathlib.Path) -> dict:
    conn = sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        out = {}
        for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
            if name.startswith("sqlite_"):
                continue
            rows = [dict(r) for r in conn.execute(f'SELECT * FROM "{name}"')]
            out[name] = rows
        return out
    finally:
        conn.close()


def _victim(work: pathlib.Path, seam: str, mode: str) -> None:
    _wire_child()
    import engine.operation_identity_atomic_destination as mod
    base = mod.OperationIdentityAtomicAuthorityEffectDestination

    class SeamDestination(base):
        """The pinned destination plus a synchronization point at the documented ``_transaction_stage`` hook. It injects no fault."""

        def _transaction_stage(self, stage):
            if stage == seam:
                sys.stdout.write(f"READY {seam} {os.getpid()}\n")
                sys.stdout.flush()
                if mode == "block":
                    while True:  # blocked at the seam until the parent kills this process
                        time.sleep(3600)
            return None

    mod.OperationIdentityAtomicAuthorityEffectDestination = SeamDestination  # Ctx imports the name at construction time
    import _chain
    ctx = _chain.Ctx(work / "victim")
    flow = ctx.flow
    claim = ctx.provision()
    run_json = work / "victim" / "cp" / "run.json"
    setup = {"pid": os.getpid(), "ppid": os.getppid(), "seam": seam, "mode": mode, "claim_id": claim.claim_id,
             "claim_state_after_provision": ctx.dest.claim_state(claim.claim_id), "decision_id": flow.d1.decision_id,
             "effect_id": flow.d1.effect_id, "sqlite_path": str(ctx.dest.path), "run_json": str(run_json), "run_json_sha256": _sha(run_json),
             "effect_ids_before_execute": ctx.effect_ids(), "destination_class": type(ctx.dest).__mro__[0].__name__}
    (work / "setup.json").write_text(json.dumps(setup, indent=1, sort_keys=True))
    result = ctx.execute(claim.claim_id)  # blocked inside this call at the seam in "block" mode
    sys.stdout.write(f"COMPLETED {result.status}\n")
    sys.stdout.flush()


def _recover(work: pathlib.Path, out: pathlib.Path) -> None:
    """A fresh process: reopen the persisted store, observe, reconcile, present the claim twice, observe."""
    _wire_child()
    import _chain
    from agent_control_plane.bounded import BoundedRecordStore
    from engine.atomic_local_control_plane_executor import AtomicLocalControlPlaneExecutor
    from engine.operation_identity_atomic_destination import OperationIdentityAtomicAuthorityEffectDestination as Dest
    from engine.safe_executor import snapshot_envelope
    setup = json.loads((work / "setup.json").read_text())
    ctx = _chain.Ctx(work / "observer-scratch")  # fresh fixtures (proposal, resolver, policy); its own scratch stores are not used for the state under test
    flow = ctx.flow
    persisted = BoundedRecordStore(setup["run_json"], "run-1")  # the Control Plane record persisted by the victim
    flow.f.records = persisted
    d1 = persisted.decision(setup["decision_id"])
    dest = Dest(pathlib.Path(setup["sqlite_path"]).parent, clock=lambda: flow.NOW)  # reopens the SAME on-disk database (this open performs SQLite journal recovery)
    ctx.dest = flow.dest = dest
    ctx.executor = AtomicLocalControlPlaneExecutor(workflow=flow.f, destination=dest, policy=flow.policy, operation_identity=True)
    claim_id = setup["claim_id"]
    envelope_snapshot = snapshot_envelope(flow.envelope(d1))

    def state():
        t = _read_tables(pathlib.Path(dest.path))
        return {"effect_ids": sorted(r["effect_id"] for r in t.get("effects", [])), "effect_count": len(t.get("effects", [])),
                "claim_state": dest.claim_state(claim_id), "attempt_rows": len(t.get("attempts", [])), "attempt_event_rows": len(t.get("attempt_events", [])),
                "receipt_rows": len(t.get("authority_effect_receipts_v1", [])), "budget_used": [r["used_effects"] for r in t.get("effect_budgets_v1", [])],
                "operation_rows": len(t.get("operation_effects_v1", []))}

    def reconcile():
        step = _chain.attempt(lambda: dest.reconcile_claim(claim_id, envelope_snapshot))
        if not step["ok"]:
            return {"raised": step["error"]}
        v = step["value"]
        return {"raised": None, **{k: v.get(k) for k in ("status", "reason", "claim_state", "retry_eligible", "effect_id")}}

    def present():
        step = _chain.attempt(lambda: ctx.execute(claim_id, d1))
        if not step["ok"]:
            return {"raised": step["error"], "status": None}
        r = step["value"]
        return {"raised": None, **_chain.result_obs(r)}

    obs = {"observer_pid": os.getpid(), "observer_ppid": os.getppid(), "victim_pid": setup["pid"], "expected_effect_id": setup["effect_id"],
           "decision_found_in_persisted_record": d1 is not None and d1.result == "authorized"}
    obs["on_reopen"] = state()
    obs["reconcile_first"] = reconcile()
    obs["execute_again"] = present()
    obs["after_execute_again"] = state()
    obs["reconcile_second"] = reconcile()
    obs["execute_third"] = present()
    obs["final"] = state()
    obs["tables_final"] = _read_tables(pathlib.Path(dest.path))
    obs["run_json_sha256_observer_start"] = setup["run_json_sha256"]
    out.write_text(json.dumps(obs, indent=1, sort_keys=True, default=str))
    ctx.close()


def main(argv):
    role = argv[1]
    if role == "victim":
        _victim(pathlib.Path(argv[2]), argv[3], argv[4])
    elif role == "recover":
        _recover(pathlib.Path(argv[2]), pathlib.Path(argv[3]))
    else:
        raise SystemExit(f"unknown role {role!r}")


# ============================================================================================================ parent side
def _proc_state(pid: int):
    try:
        data = pathlib.Path(f"/proc/{pid}/stat").read_text()
        return data[data.rindex(")") + 2:].split()[0]
    except OSError:
        return None


def _read_ready(proc, deadline):
    """Block (select) until the victim prints READY on its stdout pipe, or the process ends, or the deadline passes."""
    buffer = b""
    fd = proc.stdout.fileno()
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None, buffer.decode(errors="replace"), "timeout"
        ready, _, _ = select.select([fd], [], [], min(remaining, 1.0))
        if ready:
            chunk = os.read(fd, 4096)
            if not chunk:  # EOF: the victim ended without reaching the seam
                return None, buffer.decode(errors="replace"), "eof"
            buffer += chunk
            for line in buffer.decode(errors="replace").splitlines():
                if line.startswith("READY "):
                    return line, buffer.decode(errors="replace"), "ready"


def run_seam(work, seam, *, kill_signal=signal.SIGKILL, mode="block", mutate=None, keep=None) -> dict:
    """Run one seam end to end and return its raw observations. ``kill_signal`` / ``mode`` / ``mutate`` exist ONLY for the negative controls."""
    work = pathlib.Path(work)
    work.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    stderr_path = work / "victim.stderr"
    with open(stderr_path, "wb") as err:
        proc = subprocess.Popen([sys.executable, str(HERE / "_killharness.py"), "victim", str(work), seam, mode], stdout=subprocess.PIPE, stderr=err, env=env, cwd=str(work))
    victim = {"pid": proc.pid, "seam": seam, "kill_signal_sent": None}
    line, stdout_seen, how = _read_ready(proc, time.monotonic() + READY_TIMEOUT)
    victim["seam_reached"] = how == "ready"
    victim["ready_line"] = line
    victim["ready_wait_outcome"] = how
    obs = {"victim": victim, "seam": seam}
    if how != "ready":
        if proc.poll() is None:
            proc.kill()
        proc.wait()
        victim.update(returncode=proc.returncode, killed_by_sigkill=False, stdout=stdout_seen, stderr_tail=stderr_path.read_text(errors="replace")[-1500:])
        return obs
    setup = json.loads((work / "setup.json").read_text())
    store_dir = pathlib.Path(setup["sqlite_path"]).parent
    victim.update(proc_state_before_kill=_proc_state(proc.pid), alive_before_kill=proc.poll() is None, setup=setup,
                  files_before_kill=_files(store_dir), run_json_sha256_before_kill=_sha(pathlib.Path(setup["run_json"])))
    if mode == "block":
        os.kill(proc.pid, kill_signal)
        victim["kill_signal_sent"] = int(kill_signal)
    try:
        proc.wait(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        victim["wait_timeout"] = True
    rest = proc.stdout.read().decode(errors="replace") if proc.stdout else ""
    victim.update(returncode=proc.returncode, term_signal=(-proc.returncode if proc.returncode < 0 else None), exit_code=(proc.returncode if proc.returncode >= 0 else None),
                  killed_by_sigkill=proc.returncode == -int(signal.SIGKILL), stdout=stdout_seen + rest, stderr_tail=stderr_path.read_text(errors="replace")[-1500:],
                  proc_gone_after=not pathlib.Path(f"/proc/{proc.pid}").exists(), completed_without_kill="COMPLETED" in (stdout_seen + rest))
    after = _files(store_dir)
    obs["pre_recovery"] = {"files": after, "wal_or_journal_file_present": any(n.endswith("-journal") or n.endswith("-wal") for n in after),
                           "run_json_sha256_after_kill": _sha(pathlib.Path(setup["run_json"])),
                           "run_json_unchanged_by_kill": _sha(pathlib.Path(setup["run_json"])) == setup["run_json_sha256"]}
    if keep is not None:  # raw copy of the on-disk state BEFORE any process opens it (retained artifact)
        for p in sorted(store_dir.iterdir()):
            if p.is_file():
                keep(f"{seam}/pre-recovery/{p.name}", p.read_bytes())
        keep(f"{seam}/pre-recovery/cp-run.json", pathlib.Path(setup["run_json"]).read_bytes())
    if mutate is not None:
        obs["mutation"] = mutate(setup, store_dir)
    out = work / "recover.json"
    proc2 = subprocess.run([sys.executable, str(HERE / "_killharness.py"), "recover", str(work), str(out)], capture_output=True, text=True, env=env, cwd=str(work), timeout=CHILD_TIMEOUT)
    obs["observer_process"] = {"returncode": proc2.returncode, "stderr_tail": proc2.stderr[-1500:]}
    if proc2.returncode != 0 or not out.exists():
        raise RuntimeError(f"observer process failed for seam {seam}: rc={proc2.returncode} {proc2.stderr[-800:]}")
    rec = json.loads(out.read_text())
    tables = rec.pop("tables_final")
    obs["recovered"] = rec
    rec["observer_is_fresh_process"] = rec["observer_pid"] != rec["victim_pid"] and rec["observer_pid"] != os.getpid() and rec["observer_pid"] != setup["pid"]
    rec["effect_ids_match_expected_on_reopen"] = rec["on_reopen"]["effect_ids"] == ([rec["expected_effect_id"]] if rec["on_reopen"]["effect_count"] else [])
    rec["effect_ids_final_match_expected"] = rec["final"]["effect_ids"] == [rec["expected_effect_id"]]
    for step in ("reconcile_first", "reconcile_second"):
        rec[step]["effect_id_matches_expected"] = rec[step].get("effect_id") == rec["expected_effect_id"]
    rec["max_effect_count"] = max(rec[k]["effect_count"] for k in ("on_reopen", "after_execute_again", "final"))
    if keep is not None:
        keep(f"{seam}/observations.json", json.dumps({k: v for k, v in obs.items()}, indent=1, sort_keys=True, default=str).encode())
        keep(f"{seam}/post-recovery-tables.json", json.dumps(tables, indent=1, sort_keys=True, default=str).encode())
        keep(f"{seam}/victim.stderr", stderr_path.read_bytes())
    return obs


def run_all(work, keep=None) -> dict:
    """The mandatory scenario body: three seams, real SIGKILL each."""
    work = pathlib.Path(work)
    obs = {seam: run_seam(work / seam, seam, keep=keep) for seam in SEAMS}
    obs["seams"] = list(SEAMS)
    return obs


# ------------------------------------------------------------------------------------------------ negative-control mutations
def mutate_duplicate_effect(setup, store_dir):
    """Control: insert a SECOND (fabricated) effect row into the killed store, so any 'at most one effect' predicate must fail."""
    db = pathlib.Path(setup["sqlite_path"])
    conn = sqlite3.connect(str(db), timeout=10)
    try:
        conn.execute("INSERT INTO effects(effect_id,operation_digest,grant_id,target,amount,unit,payload_json,state) VALUES(?,?,?,?,?,?,?,?)",
                     ("sha256:fabricated-duplicate", "d", "g", "t", 10.0, "USD", "{}", "applied"))
        conn.commit()
    finally:
        conn.close()
    return {"mutation": "duplicate_effect_row_inserted"}


def mutate_claim_reset(setup, store_dir):
    """Control: reset the claim to 'issued' in the killed store, so the post-commit 'claim consumed' predicates must fail."""
    conn = sqlite3.connect(str(pathlib.Path(setup["sqlite_path"])), timeout=10)
    try:
        conn.execute("UPDATE execution_claims_v1 SET state='issued' WHERE claim_id=?", (setup["claim_id"],))
        conn.commit()
    finally:
        conn.close()
    return {"mutation": "claim_state_reset_to_issued"}


def mutate_rollback_committed(setup, store_dir):
    """Control: remove the committed effect from the killed store, so the post-commit 'effect durable' predicates must fail."""
    conn = sqlite3.connect(str(pathlib.Path(setup["sqlite_path"])), timeout=10)
    try:
        conn.execute("DELETE FROM effects")
        conn.commit()
    finally:
        conn.close()
    return {"mutation": "committed_effect_row_deleted"}


def _register_scenario():
    import _chain

    @_chain.scenario("nc_process_kill")
    def nc_process_kill(work):
        """A1 mandatory scenario: a real SIGKILL at each of the three route B seams, observed by a fresh process (see the module docstring)."""
        return run_all(work, keep=lambda rel, data: _chain.retain(f"nc_process_kill/{rel}", data))


if __name__ == "__main__":
    main(sys.argv)
else:
    _register_scenario()
