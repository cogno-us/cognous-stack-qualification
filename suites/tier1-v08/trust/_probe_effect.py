"""Worker C subprocess probe (separate OS process / interpreter). Run with `python -I`; sys.path is built here from argv so the parent controls
exactly which components (and which support libraries) are importable.

argv: mode root anchor claim_id pickle_path claim_json_path pathsep_joined_sys_path
modes: execute | execute_no_nacl | execute_no_binding_validator | provision
Prints exactly one line `RESULT:{json}`; any failure is captured into the JSON (never a traceback-only exit).
SPDX-License-Identifier: Apache-2.0
"""
import importlib.abc
import json
import os
import pickle
import sqlite3
import sys

mode, root, anchor, claim_id, pickle_path, claim_json, paths = sys.argv[1:8]
sys.path[:0] = [p for p in paths.split(os.pathsep) if p]
out = {"mode": mode, "python": sys.version.split()[0], "phase": "start"}


class Block(importlib.abc.MetaPathFinder):
    def __init__(self, names):
        self.names = tuple(names)

    def find_spec(self, fullname, path, target=None):
        if any(fullname == n or fullname.startswith(n + ".") for n in self.names):
            raise ImportError(f"blocked by probe: {fullname}")
        return None


def counts(db):
    try:
        c = sqlite3.connect(db)
        try:
            return {"effects": c.execute("SELECT COUNT(*) FROM effects").fetchone()[0],
                    "claims": c.execute("SELECT COUNT(*) FROM execution_claims_v1").fetchone()[0],
                    "claim_states": [r[0] for r in c.execute("SELECT state FROM execution_claims_v1")]}
        finally:
            c.close()
    except Exception as exc:  # noqa: BLE001
        return {"counts_error": f"{type(exc).__name__}: {exc}"}


try:
    import pydantic
    out["pydantic"] = pydantic.VERSION
    if mode == "execute_no_nacl":
        sys.meta_path.insert(0, Block(["nacl"]))
    if mode == "execute_no_binding_validator":
        sys.meta_path.insert(0, Block(["agent_control_plane.canonical_policy_binding"]))
    from datetime import datetime, timezone
    now = datetime(2026, 10, 25, 12, 0, 0, tzinfo=timezone.utc)
    out["phase"] = "import_engine"
    from engine.local_authority_effect import AtomicAuthorityEffectDestination as D
    out["phase"] = "open_destination"
    dest = D(root, clock=lambda: now)
    db = str(dest.path)
    if mode == "provision":
        out["phase"] = "provision"
        claim = json.load(open(claim_json))
        try:
            dest.provision_claim(claim)
            out["provisioned"] = True
        except BaseException as exc:  # noqa: BLE001
            out["provisioned"] = False
            out["exc_type"], out["exc_msg"] = type(exc).__name__, str(exc)[:400]
    else:
        out["phase"] = "configure_store"
        dest.configure_selection_authority(anchor)
        from engine.atomic_local_control_plane_executor import AtomicLocalControlPlaneExecutor as X
        env, policy = pickle.load(open(pickle_path, "rb"))
        out["phase"] = "execute"
        res = X(workflow=None, destination=dest, policy=policy).execute(envelope=env, claim_id=claim_id)
        out["status"] = res.status
        out["error"] = (res.error or "")[:300]
        out["typed"] = (res.control_plane_evidence or {}).get("selection_refusal")
        out["failure_class"] = (res.control_plane_evidence or {}).get("failure_class")
        out["nacl_loaded"] = "nacl" in sys.modules
    out["db"] = counts(db)
    out["phase"] = "done"
except BaseException as exc:  # noqa: BLE001
    out["exc_type"], out["exc_msg"] = type(exc).__name__, str(exc)[:400]
    try:
        out["db"] = counts(str(db))  # noqa: F821
    except Exception:
        pass
print("RESULT:" + json.dumps(out, default=str))
