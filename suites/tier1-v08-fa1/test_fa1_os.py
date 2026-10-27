"""F-A1 qualification, real-OS and crash cases (plan docs/f-a1-authorization-pin/qualification-plan.md). 7 of the 30 counted executions.

FA1-05 and FA1-06(a) use TWO REAL NON-ROOT OS IDENTITIES (throwaway users created with useradd, processes started with setpriv): the installer identity writes the pin
store, anchor, fence and log; the executor identity can read them through the Runtime guard's own reader but cannot write, replace, rename, unlink or re-permission any of them,
and cannot create a journal or a sibling file. They need root with useradd/userdel/setpriv; where those are absent the case is SKIPPED, which the gate counts as INCONCLUSIVE,
never PASS. These cases show what OS permissions do for a deployment that uses separate identities; they do NOT show that the Python API is an isolation boundary.

FA1-19 to FA1-22 kill a REAL installer process (SIGKILL) at the stages of the Amendment 4 crash table, then restart it.
"""
from __future__ import annotations

import contextlib
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

import _fa1 as f
from _fa1 import Rig, judge, w
from engine import authorization_pin_format as fmt
from engine.authorization_pin import PinReader
from host.authorization_pin import TrustedAuthorizationInstaller

HERE = Path(__file__).resolve().parent
CHILD = Path(os.environ.get("V08_FA1_CHILD") or (HERE / "fa1_child.py"))   # CI stages it where the throwaway OS users can traverse
RUNTIME = Path(os.environ.get("V08_COMPONENTS_DIR", "")).resolve() / "runtime"
CP_SRC = Path(os.environ.get("V08_COMPONENTS_DIR", "")).resolve() / "control_plane" / "src"
ZERO = {"effects": 0, "attempts": 0, "authority_effect_receipts_v1": 0, "budget_used": 0}
CAN_OS = hasattr(os, "geteuid") and os.geteuid() == 0 and all(shutil.which(x) for x in ("useradd", "userdel", "setpriv"))


@pytest.fixture(autouse=True)
def _cp_clock():
    with w.cp_clock():
        yield


def finish(ev, verdict, note=None, **observed):
    ev["observed"].update(observed)
    ev["verdict"] = verdict
    if note:
        ev["note"] = note
    assert verdict in ("HELD", "CHARACTERIZED"), (verdict, {k: observed[k] for k in list(observed)[:6]})


def child_env():
    return {**os.environ, "PYTHONPATH": f"{RUNTIME}:{RUNTIME / 'src'}:{CP_SRC}", "PYTHONDONTWRITEBYTECODE": "1"}


def spec_of(rig, **extra):
    return {"store": str(rig.icfg.pin_store_path), "fences": str(rig.icfg.fence_dir), "anchor": str(rig.icfg.anchor_path), "log": str(rig.icfg.log_path),
            "store_id": f.STORE_ID, **extra}


def kill_child(rig, assessment, stage, hot_journal=False):
    p = subprocess.run([sys.executable, str(CHILD), "kill", json.dumps(spec_of(rig, assessment=assessment, stage=stage, hot_journal=hot_journal))], capture_output=True, text=True,
                       timeout=90, env=child_env(), cwd=RUNTIME)
    return p.returncode, p.stderr[-400:]


def restart(rig):
    return TrustedAuthorizationInstaller(rig.icfg)                      # a fresh process-equivalent: no in-memory state survives the kill


def admission(rig, decision_id):
    rd = PinReader(rig.gcfg)
    return fmt.anchor_admission(rd.read_anchor(), rd.read_head(), decision_id).verdict


# ====================================================================================================================== real two-identity OS cases
@contextlib.contextmanager
def os_world(tmp_path, assessment):
    if not CAN_OS:
        pytest.skip("needs root with useradd/userdel/setpriv: two real OS identities cannot be created here (INCONCLUSIVE, not a pass)")
    suffix = secrets.token_hex(3)
    inst, exe = f"fa1i{suffix}", f"fa1e{suffix}"
    base = Path(tempfile.mkdtemp(prefix="fa1-os-", dir="/tmp"))
    created = []
    try:
        for name in (inst, exe):
            subprocess.run(["useradd", "-M", "-s", "/usr/sbin/nologin", "-U", name], check=True)
            created.append(name)
        os.chmod(base, 0o755)
        for d in ("pin", "anchor"):
            (base / d).mkdir(mode=0o755)
            shutil.chown(base / d, user=inst, group=inst)
            os.chmod(base / d, 0o755)

        def run_as(user, *argv):
            return subprocess.run(["setpriv", f"--reuid={user}", f"--regid={user}", "--clear-groups", *argv], capture_output=True, text=True, timeout=90,
                                  env=child_env(), cwd=RUNTIME)
        world = {"inst": inst, "exec": exe, "store": base / "pin/pins.sqlite3", "fences": base / "pin/fences", "anchor": base / "anchor/pins.anchor.json",
                 "log": base / "pin/installer.log", "decision_id": assessment["decision_id"], "run_as": run_as}
        spec = {"store": str(world["store"]), "fences": str(world["fences"]), "anchor": str(world["anchor"]), "log": str(world["log"]), "store_id": f.STORE_ID,
                "assessments": [assessment]}
        done = run_as(inst, sys.executable, str(CHILD), "run", json.dumps(spec))
        world["installer_stdout"], world["installer_stderr"] = done.stdout.split(), done.stderr[-400:]
        world["spec"] = {k: str(v) for k, v in world.items() if k in ("store", "fences", "anchor", "log")}
        world["fence"] = f.fmt.fence_path(world["fences"], assessment["decision_id"])
        world["inst_uid"] = int(subprocess.check_output(["id", "-u", inst]))
        world["exec_uid"] = int(subprocess.check_output(["id", "-u", exe]))
        yield world
    finally:
        for name in created:
            subprocess.run(["userdel", "-f", name], capture_output=True)
            subprocess.run(["groupdel", name], capture_output=True)
        shutil.rmtree(base, ignore_errors=True)


def probe(world, kind):
    spec = {**world["spec"], "store_id": f.STORE_ID, "fence": str(world["fence"]), "decision_id": world["decision_id"], "kind": kind}
    return world["run_as"](world["exec"], sys.executable, str(CHILD), "probe", json.dumps(spec))


def test_fa1_05_supplier_identity_cannot_install_or_replace_a_pin(tmp_path, ev):
    ev["scenario"] = "FA1-05"
    ev["expected"] = ("REAL two identities: the installer user installs the real Control Plane export; the executor user (the claim supplier's side) tries to open the store read-write, "
                      "insert a row, create a table, create a journal or a sibling store, create a fence, create or rename over the anchor: every attempt denied by the OS, "
                      "store/anchor/log bytes unchanged; the same identity CAN read the pin through the guard's reader and take a shared flock")
    rig = Rig(tmp_path)
    assessment = rig.assessment()
    with os_world(tmp_path, assessment) as wd:
        files = (wd["store"], wd["anchor"], wd["log"])
        installed_ok = wd["installer_stdout"][:1] == ["installed"] and "custody-ok" in wd["installer_stdout"]
        owners = {str(p.name): p.stat().st_uid for p in (*files, wd["fence"])}
        before = {p: p.read_bytes() for p in files}
        done = probe(wd, "install")
        result = json.loads(done.stdout) if done.returncode == 0 and done.stdout.strip() else {}
        attempts = result.get("denied_attempts", {})
        unchanged = {p: p.read_bytes() for p in files} == before
        no_journal = not Path(str(wd["store"]) + "-journal").exists()
        siblings = sorted(os.listdir(wd["store"].parent))
        ok = (installed_ok and attempts and all(v.startswith("denied") for v in attempts.values()) and unchanged and no_journal
              and all(uid == wd["inst_uid"] for uid in owners.values()) and result.get("euid") == wd["exec_uid"] != wd["inst_uid"] and result.get("reader_rows") == [[1, "active"]]
              and result.get("shared_flock_on_ro_fd") == "ok")
        finish(ev, "HELD" if ok else ("BREACH" if any(v == "ALLOWED" for v in attempts.values()) else "INCONCLUSIVE"), installer_identity_uid=wd["inst_uid"],
               executor_identity_uid=wd["exec_uid"], file_owner_uids=owners, installer_output=wd["installer_stdout"], attempts=attempts, bytes_unchanged=unchanged,
               no_journal_created=no_journal, store_dir_listing=siblings, executor_may_read=result.get("reader_rows"), shared_flock=result.get("shared_flock_on_ro_fd"),
               probe_stderr=done.stderr[-400:], installer_stderr=wd["installer_stderr"])


def test_fa1_06a_executor_identity_cannot_modify_pin_files_or_paths(tmp_path, ev):
    ev["scenario"] = "FA1-06"
    ev["expected"] = ("(a) REAL executor identity attempts UPDATE/DELETE/DROP through SQLite, and open-for-write, append, truncate, unlink, rename and chmod of the pin store, the "
                      "anchor, the fence and the log, and to unlink every fence: all denied, bytes unchanged, the guard's reader still sees the pin")
    rig = Rig(tmp_path)
    assessment = rig.assessment()
    with os_world(tmp_path, assessment) as wd:
        files = (wd["store"], wd["anchor"], wd["log"], wd["fence"])
        before = {p: p.read_bytes() for p in files}
        modes_before = {str(p): oct(p.stat().st_mode) for p in files}
        done = probe(wd, "tamper")
        result = json.loads(done.stdout) if done.returncode == 0 and done.stdout.strip() else {}
        attempts = result.get("denied_attempts", {})
        unchanged = {p: p.read_bytes() for p in files} == before and {str(p): oct(p.stat().st_mode) for p in files} == modes_before
        ok = (wd["installer_stdout"][:1] == ["installed"] and attempts and len(attempts) >= 20 and all(v.startswith("denied") for v in attempts.values()) and unchanged
              and all(p.exists() for p in files) and result.get("reader_rows") == [[1, "active"]])
        finish(ev, "HELD" if ok else ("BREACH" if any(v == "ALLOWED" for v in attempts.values()) else "INCONCLUSIVE"), attempts=attempts, bytes_and_modes_unchanged=unchanged,
               executor_may_read=result.get("reader_rows"), executor_uid=result.get("euid"), installer_uid=wd["inst_uid"], probe_stderr=done.stderr[-400:])


# ====================================================================================================================== crash cases (real SIGKILL of a real installer)
def revoked_assessment(rig):
    rig.revoke_in_control_plane()
    a = rig.assessment()
    assert a["state"] == "terminal" and a["terminal_status"] == "revoked"
    return a


def test_fa1_19_crash_before_the_intent_is_durable_leaves_no_barrier(tmp_path, ev):
    ev["scenario"] = "FA1-19"
    ev["expected"] = ("crash A: the installer is killed before the anchor replace: no intent, no pending, no state change, admission accepts; the restarted installer re-derives the "
                      "transition from the Control Plane export and completes it; the next attempt is REFUSED pin_status:revoked")
    rig = Rig(tmp_path)
    rig.install()
    cid = rig.claim()
    a = revoked_assessment(rig)
    before = (rig.icfg.anchor_path.read_bytes(), [r["status"] for r in rig.rows()])
    rc, err = kill_child(rig, a, "before_intent")
    state = (rig.icfg.anchor_path.read_bytes(), [r["status"] for r in rig.rows()])
    inst2 = restart(rig)
    pending = inst2.pending()
    adm = admission(rig, rig.decision_id)
    redone = inst2.apply_assessment(rig.assessment())
    res = rig.run(cid)
    v, typed = judge(res, ZERO, "policy_identity_mismatch", "REFUSE", "pin_status:revoked")
    ok = rc == -9 and state == before and pending is None and adm == "accept" and redone.outcome == "complete" and [r["status"] for r in rig.rows()] == ["active", "revoked"]
    finish(ev, v if ok else "INCONCLUSIVE", child_returncode=rc, state_unchanged=state == before, pending_after_restart=pending, admission_before_rederive=adm,
           rederive=redone.outcome, after_typed=typed, child_stderr=err)


def test_fa1_20_crash_with_intent_durable_holds_the_covered_decision_until_the_installer_restarts(tmp_path, ev):
    ev["scenario"] = "FA1-20"
    ev["expected"] = ("crash B/D/F/H: the installer is killed right after the intent is durable and stays down: the covered decision is HELD pin_transition_pending for the whole "
                      "interval, an UNRELATED decision is admitted and executes, the intent is not cleared by anything else; the restarted installer's mandatory reconcile completes "
                      "the transition through the exclusive fence and the covered decision is then REFUSED pin_status:revoked. Unrelated decision is synthetic by construction")
    rig = Rig(tmp_path)
    rig.install()
    u = f.unrelated(rig, 2)
    rig.installer.apply_assessment(u.assessment)
    rig.dest.provision_claim(u.claim)
    cid = rig.claim()
    a = revoked_assessment(rig)
    rc, err = kill_child(rig, a, "after_intent_durable")
    intent0 = rig.icfg.anchor_path.read_bytes()
    held = [judge(rig.run(cid), ZERO, "store_unknown", "HOLD", "pin_transition_pending")[0] for _ in range(3)]
    other = w.executor(rig.dest, w.policy_from(rig.sets)).execute(envelope=u.envelope, claim_id=u.claim_id)
    intent_still = rig.icfg.anchor_path.read_bytes() == intent0
    rec = restart(rig).reconcile()
    res = rig.run(cid)
    v, typed = judge(res, {**ZERO}, "policy_identity_mismatch", "REFUSE", "pin_status:revoked")
    ok = (rc == -9 and all(x == "HELD" for x in held) and other.status == "executed" and rig.counts()["effects"] == 1 and intent_still
          and any(r.outcome == "complete" for r in rec) and [r["status"] for r in rig.rows(rig.decision_id)] == ["active", "revoked"] and v == "HELD")
    finish(ev, "HELD" if ok else "INCONCLUSIVE", child_returncode=rc, covered_while_installer_down=held, unrelated_status=other.status, intent_unchanged_while_down=intent_still,
           reconcile=[r.outcome for r in rec], after_typed=typed, counts=rig.counts(), child_stderr=err)


def test_fa1_21_crash_while_holding_the_exclusive_fence_with_a_hot_journal(tmp_path, ev):
    ev["scenario"] = "FA1-21"
    ev["expected"] = ("crash C: the installer is SIGKILLed inside the terminal transaction with a hot journal left behind: the OS releases the lock; an unrelated decision is HELD "
                      "[pin_store_unreadable] while the journal is hot and the covered decision is HELD; the restarted installer rolls the uncommitted rows back and completes the "
                      "transition; no commit is fabricated; the unrelated decision executes again. Unrelated decision is synthetic by construction")
    rig = Rig(tmp_path)
    rig.install()
    u = f.unrelated(rig, 2)
    rig.installer.apply_assessment(u.assessment)
    rig.dest.provision_claim(u.claim)
    cid = rig.claim()
    a = revoked_assessment(rig)
    rc, err = kill_child(rig, a, "row_inserted_uncommitted", hot_journal=True)
    journal = Path(str(rig.icfg.pin_store_path) + "-journal")
    hot = journal.exists() and journal.stat().st_size > 0
    covered = judge(rig.run(cid), ZERO, "store_unknown", "HOLD", "pin_transition_pending")
    unrelated = w.executor(rig.dest, w.policy_from(rig.sets)).execute(envelope=u.envelope, claim_id=u.claim_id)
    vu, tu = judge(unrelated, ZERO, "store_unknown", "HOLD", "pin_store_unreadable")
    lock_released = f.fence_free(f.fence_of(rig))
    rec = restart(rig).reconcile()
    statuses = [r["status"] for r in rig.rows(rig.decision_id)]
    junk = f.sql(rig.icfg.pin_store_path, "SELECT COUNT(*) FROM authorization_pin_v1 WHERE decision_id='junk'")[0][0]
    again = w.executor(rig.dest, w.policy_from(rig.sets)).execute(envelope=u.envelope, claim_id=u.claim_id)
    ok = (rc == -9 and hot and covered[0] == "HELD" and vu == "HELD" and lock_released and any(r.outcome == "complete" for r in rec) and statuses == ["active", "revoked"]
          and junk == 0 and again.status == "executed")
    finish(ev, "HELD" if ok else "INCONCLUSIVE" if not hot else "BREACH" if unrelated.status == "executed" else "INCONCLUSIVE", child_returncode=rc, journal_hot=hot,
           covered_typed=covered[1], unrelated_while_hot=tu, lock_released_by_os=lock_released, reconcile=[r.outcome for r in rec], statuses=statuses, junk_rows_after_recovery=junk,
           unrelated_after_recovery=again.status, child_stderr=err)


def test_fa1_22_crash_after_the_row_commit_before_the_anchor_completion(tmp_path, ev):
    ev["scenario"] = "FA1-22"
    ev["expected"] = ("crash E: killed after the terminal row commits and before the anchor completes: no effect is admitted for the decision (HOLD pin_transition_pending per 6.2 "
                      "steps 0/2, or REFUSE pin_status:revoked per the section 7 table; both fail closed); the restarted installer verifies the row against the intent and completes "
                      "the anchor; a row that does NOT match the intent yields HOLD for every decision [pin_anchor_inconsistent] and the installer refuses. Unrelated decision is synthetic")
    rig = Rig(tmp_path)
    rig.install()
    u = f.unrelated(rig, 2)
    rig.installer.apply_assessment(u.assessment)
    rig.dest.provision_claim(u.claim)
    cid = rig.claim()
    a = revoked_assessment(rig)
    rc, err = kill_child(rig, a, "after_row_commit")
    anchor = fmt.anchor_decode(rig.icfg.anchor_path.read_bytes())
    rows = [r["status"] for r in rig.rows(rig.decision_id)]
    adm = admission(rig, rig.decision_id)
    res = rig.run(cid)
    v, typed = judge(res, ZERO, "store_unknown", "HOLD", "pin_transition_pending", alt=[("policy_identity_mismatch", "REFUSE", "pin_status:revoked")])
    rec = restart(rig).reconcile()
    after_anchor = fmt.anchor_decode(rig.icfg.anchor_path.read_bytes())
    # mismatching row: same crash in a second world, then the committed row is replaced by a chain-valid row with a DIFFERENT terminal status
    rig2 = Rig(tmp_path / "second")
    rig2.install()
    u2 = f.unrelated(rig2, 2)
    rig2.installer.apply_assessment(u2.assessment)
    rig2.dest.provision_claim(u2.claim)
    a2 = revoked_assessment(rig2)
    rc2, _ = kill_child(rig2, a2, "after_row_commit")
    good = rig2.rows(rig2.decision_id)[-1]
    forged = fmt.make_row(pin_epoch=good["pin_epoch"], decision_id=good["decision_id"], status="withdrawn", payload=good["payload"],
                          provenance=good["provenance"], prev_pin_digest=good["prev_pin_digest"])
    for (trigger,) in f.sql(rig2.icfg.pin_store_path, "SELECT name FROM sqlite_master WHERE type='trigger'"):
        f.sql(rig2.icfg.pin_store_path, f'DROP TRIGGER "{trigger}"')           # the store's append-only triggers; dropped by the harness acting as the store OWNER to simulate corruption
    f.sql(rig2.icfg.pin_store_path, "UPDATE authorization_pin_v1 SET status=?, row_json=?, pin_digest=? WHERE pin_epoch=?",
          (forged["status"], fmt.encode_row(forged), forged["pin_digest"], forged["pin_epoch"]))
    rec2 = restart(rig2).reconcile()
    other = w.executor(rig2.dest, w.policy_from(rig2.sets)).execute(envelope=u2.envelope, claim_id=u2.claim_id)
    vo, to = judge(other, ZERO, "store_unknown", "HOLD", "pin_anchor_inconsistent", alt=[("verifier_unavailable", "HOLD", "pin_anchor_inconsistent")])
    ok = (rc == -9 and anchor["intent"] is not None and rows == ["active", "revoked"] and v == "HELD" and any(r.outcome == "reconciled" for r in rec)
          and after_anchor["intent"] is None and after_anchor["committed_epoch"] == anchor["committed_epoch"] + 1
          and rc2 == -9 and all(r.outcome == "refused" for r in rec2) and vo == "HELD")
    finish(ev, "HELD" if ok else "INCONCLUSIVE", child_returncode=rc, intent_present_after_crash=anchor["intent"] is not None, rows_after_crash=rows, table_admission=adm,
           runtime_typed=typed, reconcile=[r.outcome for r in rec], anchor_after=after_anchor["committed_epoch"], mismatch_reconcile=[(r.outcome, r.detail) for r in rec2],
           mismatch_unrelated_typed=to,
           note="The guard HOLDs in state E (stricter than the section 7 table's 'accept; the terminal row refuses'); both fail closed with 0 effects")
