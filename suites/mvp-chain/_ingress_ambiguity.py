"""Supported-ingress ambiguity evidence (Architect ruling 5, PROPOSED; Qualification owns the verdict).

SPDX-License-Identifier: Apache-2.0

EVIDENCE LEVEL: SUPPORTED INGRESS. This is NOT the executor-level evidence of ruling 4 (``test_ruling4_lost_ack.py``, NC2-01..05), which
drive the executor directly with ``simulate='lost_ack'``. Here the unprivileged client (uid 65534, no groups) sends one ordinary, valid
proposal over the real hub ingress socket; the request schema is unchanged and the client chooses nothing about faults; the ingress
keeps ``simulate=None``. The fault is injected owner-side only (see _ingress_fault_wrapper.py): the Runtime's own post-commit transaction
seam raises once after the destination commit. Observations recorded:

  boundary   the live ``execute_claim_atomic`` call received simulate=None; owner-side read-only SQLite readback shows the committed effect
  ack        the hook fired; the client received outcome 'unknown' (never 'executed', never a refusal); executor result acknowledged False
  unknown    the ingress ledger settled the request as 'unknown'; the executor observation says retry_eligible False; the claim is consumed
  reuse      the same request bytes again -> REPLAY refusal; a fresh request id with the same business content -> not executed; effects unchanged
  reconcile  after the ingress is stopped, the owner runs reconcile_claim over the real destination file with the captured claim/envelope
Raw observations only; no verdict is computed here.
"""
from __future__ import annotations

import json
import os
import pathlib
import pickle
import shutil
import sqlite3
import subprocess
import sys
import tempfile

import _ingress
import _state

UNPRIV = _ingress.UNPRIV_UID


def _ro(path):
    return sqlite3.connect(pathlib.Path(path).resolve().as_uri() + "?mode=ro", uri=True, timeout=10)


def _effects(dest):
    conn = _ro(dest)
    try:
        return [list(r) for r in conn.execute("SELECT effect_id,state,amount FROM effects ORDER BY effect_id")]
    finally:
        conn.close()


def _claims(dest):
    conn = _ro(dest)
    try:
        return dict(conn.execute("SELECT claim_id,state FROM execution_claims_v1").fetchall())
    finally:
        conn.close()


def _load(path):
    p = pathlib.Path(path)
    return json.loads(p.read_text()) if p.exists() else None


def run(work):
    hub = _state.ENV["dirs"].get("hub")
    if not hub:
        return {"status": "blocked", "blocked_reason": "hub checkout not provided (MVP_HUB_DIR)", "ingress": {"probe_ran": False}}
    if os.geteuid() != 0:
        return {"status": "blocked", "blocked_reason": "environment cannot run the client as a distinct unprivileged uid (needs root to drop to uid 65534)",
                "ingress": {"probe_ran": False}}
    hub = pathlib.Path(hub)
    dump = subprocess.run([sys.executable, str(pathlib.Path(__file__).with_name("_dump_d1_cases.py")), str(hub)], cwd=hub,
                          env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True, timeout=120)
    if dump.returncode != 0:
        return {"status": "blocked", "blocked_reason": "cannot load D1 cases: " + dump.stderr[-300:], "ingress": {"probe_ran": False}}
    good = json.loads(dump.stdout)["good"]
    base = pathlib.Path(tempfile.mkdtemp(prefix="mvp-ingress-amb-"))
    os.chmod(base, 0o755)
    state, sock = base / "state", str(base / "ingress.sock")
    capture = base / "capture"  # owner-only, OUTSIDE the state tree and the client's reach
    capture.mkdir(mode=0o700)
    wrapper = pathlib.Path(__file__).with_name("_ingress_fault_wrapper.py")
    cmd = [sys.executable, str(wrapper), "--state-dir", str(state), "--socket", sock, "--control-plane", _state.ENV["dirs"]["control_plane"],
           "--runtime", _state.ENV["dirs"]["runtime"], "--socket-mode", "666"]
    penv = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", MVP_FAULT_CAPTURE_DIR=str(capture),
                PYTHONPATH=os.pathsep.join([str(hub)] + ([os.environ["PYTHONPATH"]] if os.environ.get("PYTHONPATH") else [])))
    proc = subprocess.Popen(cmd, cwd=hub, env=penv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    obs = {"evidence_level": "supported-ingress", "executor_level_evidence": "NC2-01..05 and test_ruling4_lost_ack.py (simulate='lost_ack', direct executor, NOT this row)",
           "fault_injection": {"where": "trusted qualification harness only: owner-started wrapper of the pinned hub server; Runtime seam _transaction_stage('after_commit') raises once",
                               "wrapper": "suites/mvp-chain/_ingress_fault_wrapper.py", "wrapper_sha256": _ingress.sha(wrapper.read_bytes()),
                               "request_schema_changed": False, "client_chooses_simulate": False}}
    try:
        line = proc.stdout.readline()
        if line.strip() != "READY":
            proc.kill()
            return {**obs, "status": "blocked", "ingress": {"probe_ran": False}, "blocked_reason": "fault-wrapped ingress did not start: " + proc.stderr.read()[-500:]}
        shutil.copy(hub / "tools" / "mvp_ingress" / "client.py", base / "client.py")
        (base / "probe.py").write_text(_ingress.PROBE)
        for f in ("client.py", "probe.py"):
            os.chmod(base / f, 0o644)
        dest = state / "atomic" / "refunds.sqlite3"

        def client(phase, bodies):
            plan = base / f"plan-{phase}.json"
            plan.write_text(json.dumps({"direct": False, "bodies_hex": [json.dumps(b).encode().hex() for b in bodies]}))
            os.chmod(plan, 0o644)

            def drop():
                os.setgroups([])
                os.setgid(UNPRIV)
                os.setuid(UNPRIV)
            p = subprocess.run(["/usr/bin/python3", "-I", str(base / "probe.py"), str(state), str(base / "client.py"), sock, str(proc.pid), str(plan)],
                               preexec_fn=drop, env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent"}, capture_output=True, text=True, timeout=600)
            return {"error": p.stderr[-500:]} if p.returncode != 0 else json.loads(p.stdout)

        def dest_tables():
            return _ingress.tables_digest(dest)

        before = {"effects": _effects(dest), "claims": _claims(dest)}
        first = client("first", [good])
        if "error" in first:
            return {**obs, "status": "blocked", "ingress": {"probe_ran": False}, "blocked_reason": "unprivileged client failed to run: " + first["error"]}
        after_first = {"effects": _effects(dest), "claims": _claims(dest), "tables": dest_tables(), "ledger": _ingress.ledger_rows(state / "ingress.db")}
        hook, atomic_call, exec_res = _load(capture / "hook.json"), _load(capture / "atomic_call.json"), _load(capture / "executor_result.json")
        # reuse 1: the very same request bytes; reuse 2: a fresh request id with the same business content (no new authority)
        replay = client("replay", [good])
        fresh = client("fresh", [{**good, "request_id": good["request_id"] + "-fresh"}])
        after_reuse = {"effects": _effects(dest), "claims": _claims(dest), "tables": dest_tables(), "ledger": _ingress.ledger_rows(state / "ingress.db")}
        alive_before_stop = proc.poll() is None
        # owner-side reconciliation over the real destination, after the ingress is stopped (no second writer)
        proc.terminate()
        proc.wait(15)
        recon_obs = {"ran": False}
        saved = None
        pk = capture / "envelope.pickle"
        if pk.exists():
            from engine.operation_identity_atomic_destination import OperationIdentityAtomicAuthorityEffectDestination as Dest
            from engine.safe_executor import snapshot_envelope
            import tests.test_bounded_authorization as tba
            with open(pk, "rb") as fh:
                saved = pickle.load(fh)
            d2 = Dest(state / "atomic", clock=lambda: tba.NOW)
            try:
                value = d2.reconcile_claim(saved["claim_id"], snapshot_envelope(saved["envelope"]))
                recon_obs = {"ran": True, "ok": True, "value": _strip(value)}
            except Exception as exc:  # noqa: BLE001
                recon_obs = {"ran": True, "ok": False, "error": {"type": type(exc).__name__, "message": str(exc)[:300]}}
        after_recon = {"effects": _effects(dest), "claims": _claims(dest)}
        v = recon_obs.get("value") or {}
        one = after_first["effects"]
        obs.update({
            "ingress": {"probe_ran": True, "hub_head": _state.ENV["heads"].get("hub"), "ingress_uid": os.geteuid(), "client_uid": first["uid"],
                        "client_euid": first["euid"], "client_groups": first["groups"],
                        "client_is_distinct_unprivileged": first["uid"] == first["euid"] == UNPRIV and os.geteuid() != UNPRIV and first["groups"] == [],
                        "server_alive_after_fault": alive_before_stop},
            "boundary": {"execute_claim_atomic_called": atomic_call is not None, "simulate_received_by_destination": None if atomic_call is None else atomic_call["simulate"],
                         "simulate_received_by_executor": None if exec_res is None else exec_res["simulate_received"],
                         "effects_before": before["effects"], "effects_after_first": one, "effect_count_after_first": len(one)},
            "ack": {"hook_fired": bool(hook and hook.get("fired")), "client_response": first["responses"][0],
                    "executor_status": None if exec_res is None else exec_res["status"],
                    "executor_acknowledged": None if exec_res is None else exec_res["acknowledged"],
                    "executor_attempted": None if exec_res is None else exec_res["attempted"],
                    "executor_error": None if exec_res is None else exec_res["error"]},
            "unknown": {"ledger_rows": [list(r) for r in after_first["ledger"]],
                        "ledger_state": next((r[2] for r in after_first["ledger"] if r[0] == good["request_id"]), None),
                        "ledger_outcome": next((r[3] for r in after_first["ledger"] if r[0] == good["request_id"]), None),
                        "claim_consumed_after_first": bool(after_first["claims"]) and set(after_first["claims"].values()) == {"consumed"},
                        "executor_observation": None if exec_res is None else exec_res["observation"],
                        "executor_retry_eligible": None if exec_res is None else (exec_res["observation"] or {}).get("retry_eligible"),
                        "claim_states_after_first": after_first["claims"]},
            "reuse": {"replay_response": replay.get("responses", [None])[0], "fresh_request_id_response": fresh.get("responses", [None])[0],
                      "effects_after_reuse": after_reuse["effects"], "effect_count_after_reuse": len(after_reuse["effects"]),
                      "effects_unchanged": after_reuse["effects"] == after_first["effects"],
                      "destination_effect_tables_unchanged": all(after_reuse["tables"].get(t) == after_first["tables"].get(t)
                                                                 for t in ("effects", "attempts", "authority_effect_receipts_v1", "operation_effects_v1")),
                      "claims_unchanged": after_reuse["claims"] == after_first["claims"]},
            "reconcile": {"ran": recon_obs.get("ran"), "ok": recon_obs.get("ok"), "error": recon_obs.get("error"), "value": recon_obs.get("value"),
                          "state_or_status": v.get("state") or v.get("status"), "effect_id": v.get("effect_id"), "retry_eligible": v.get("retry_eligible"),
                          "effect_id_matches_owner_readback": bool(one) and v.get("effect_id") == one[0][0],
                          "effects_after_reconcile": after_recon["effects"], "effect_count_after_reconcile": len(after_recon["effects"]),
                          "claims_after_reconcile": after_recon["claims"]},
            "status": "ran",
        })
        return obs
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(10)
            except subprocess.TimeoutExpired:
                proc.kill()
        shutil.rmtree(base, ignore_errors=True)


def _strip(value):
    return json.loads(json.dumps(value, default=str)) if isinstance(value, dict) else value
