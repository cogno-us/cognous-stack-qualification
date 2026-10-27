"""TR-5 missing / raising verifier and dependency absence fail closed (C11). Worker C.
In-process: non-admitted, None and raising verifiers, Registry import blocked (real ImportError through the Runtime's lazy import), duplicate-key and
non-canonical selection text. Separate OS processes (`_probe_effect.py`): pydantic 2.11.9 interpreter, legacy Control Plane, Registry absent,
PyNaCl blocked, Control Plane binding validator blocked.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import importlib
import json
import os
import pickle
import subprocess
import sqlite3
from pathlib import Path

import _tr
from _tr import sa, v4

COMP = Path(os.environ["V08_COMPONENTS_DIR"]).resolve()
PY_MAIN = "/home/claude/venv-cp/bin/python"
PY_OLD = os.environ.get("V08_PY211", "/home/claude/venv/bin/python")
PROBE = str(Path(__file__).resolve().parent / "_probe_effect.py")


def _paths(*, cp="control_plane", registry=True):
    parts = [str(COMP / "runtime"), str(COMP / cp / "src")]
    if registry:
        parts.append(str(COMP / "registry"))
    return os.pathsep.join(parts)


def _run_probe(python, workdir: Path, mode, root, anchor, cid, pk, claim_json, paths) -> dict:
    proc = subprocess.run([python, "-I", PROBE, mode, str(root), str(anchor), cid, str(pk), str(claim_json), paths], cwd=str(workdir),
                          capture_output=True, text=True, timeout=240, env={"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1"})
    line = next((ln for ln in proc.stdout.splitlines() if ln.startswith("RESULT:")), None)
    if proc.returncode != 0 or line is None:
        return {"harness_error": f"probe exit={proc.returncode} stdout={proc.stdout[-300:]!r} stderr={proc.stderr[-500:]!r}"}
    out = json.loads(line[len("RESULT:"):])
    out["exit"] = proc.returncode
    return out


def _count(db: Path) -> dict:
    if not db.exists():
        return {"missing": True}
    c = sqlite3.connect(db)
    try:
        return {"effects": c.execute("SELECT COUNT(*) FROM effects").fetchone()[0],
                "claims": c.execute("SELECT COUNT(*) FROM execution_claims_v1").fetchone()[0],
                "claim_states": [r[0] for r in c.execute("SELECT state FROM execution_claims_v1")]}
    except sqlite3.Error as exc:
        return {"count_error": str(exc)[:120]}
    finally:
        c.close()


def _clone(G, dst: Path) -> Path:
    dst.mkdir(parents=True, exist_ok=True)
    src, d = sqlite3.connect(G.dest.path), sqlite3.connect(dst / G.dest.path.name)
    try:
        src.backup(d)
    finally:
        d.close()
        src.close()
    anchor = dst / "anchor.json"
    anchor.write_text(G.e.anchor.read_text())
    return anchor


class _Stub:
    """Stand-in for `importlib` inside the Runtime's selection module only: the Registry packages really fail to import."""

    def __init__(self, real):
        self._real = real

    def import_module(self, name, *a, **k):
        if name.startswith(("registry_successor", "registry_adapters")):
            raise ImportError("blocked by Worker C: " + name)
        return self._real.import_module(name, *a, **k)

    def __getattr__(self, n):
        return getattr(self._real, n)


def test_c11_missing_raising_verifier_and_dependency_absence_never_activate_or_execute(tmp_path, ev, monkeypatch):
    ev["scenario"] = "TR-5"
    ev["expected"] = ("(a) A non-admitted, None, subclass-raising, genuinely-raising or always-False verifier never activates: typed refusal "
                      "(verifier_unavailable / signature_invalid) or an exception, store byte-identical, state not_activated; the genuine verifier "
                      "then activates (control). (b) With the Registry packages unimportable, writers refuse verifier_unavailable/HOLD and the effect "
                      "is refused store_unknown/HOLD with zero effects; restored, the claim executes. (c) A duplicate-key selection text is refused "
                      "with the store unchanged (non-canonical whitespace is recorded). (d) In separate processes: Registry absent -> effect not "
                      "executed, 0 effects, claim issued; binding validator blocked -> not executed, 0 effects; legacy Control Plane -> successor claim "
                      "refused at provisioning with 0 claim rows. PyNaCl-blocked execution and pydantic 2.11.9 provisioning are recorded as "
                      "informational observations.")

    # ---------------------------------------------------------------- (a) verifiers
    (tmp_path / "e").mkdir()
    E = v4.Env(tmp_path / "e").boot()
    rec_text, sel_text = v4.r.dumps(v4.REC), v4.text(v4.ST1)

    def try_activate(verifier):
        before = E.dump()
        try:
            E.dest.activate_selection(record_text=rec_text, selection_text=sel_text, context=v4.s.CTX, trust=E.trust, verifier=verifier)
            outcome = {"activated": True}
        except sa.SelectionRefusal as exc:
            outcome = {"refusal": {"code": exc.code, "refusal_class": exc.refusal_class, "cause": exc.cause}}
        except Exception as exc:  # noqa: BLE001
            outcome = {"exception": f"{type(exc).__name__}: {exc}"[:200]}
        unchanged = E.dump() == before and E.state().status == "not_activated"
        outcome.update(unchanged=unchanged, ok=bool(not outcome.get("activated") and unchanged), breach=bool(outcome.get("activated")))
        return outcome

    class Raising(v4.ev.Ed25519Verifier):
        def verify(self, *a, **k):
            raise RuntimeError("verifier down")

    _tr.sub(ev, "verifier_plain_object", lambda: try_activate(object()))
    _tr.sub(ev, "verifier_none", lambda: try_activate(None))
    _tr.sub(ev, "verifier_subclass_raising", lambda: try_activate(Raising()))

    def patched(fn):
        monkeypatch.setattr(v4.ev.Ed25519Verifier, "verify", fn)
        try:
            return try_activate(v4.ev.Ed25519Verifier())
        finally:
            monkeypatch.undo()

    _tr.sub(ev, "genuine_verifier_raising", lambda: patched(lambda self, *a, **k: (_ for _ in ()).throw(RuntimeError("crypto backend down"))))
    _tr.sub(ev, "genuine_verifier_always_false", lambda: patched(lambda self, *a, **k: False))

    def control():
        res = E.activate(v4.ST1)
        return {"status": E.state().status, "activation_ref": res.activation_ref, "ok": E.state().status == "active"}
    _tr.sub(ev, "control_genuine_verifier_activates", control)

    # ---------------------------------------------------------------- (b) Registry import blocked
    G = _tr.newgov(tmp_path, "g")
    env, cid = G.claim()

    def registry_blocked():
        monkeypatch.setattr(sa, "importlib", _Stub(importlib))
        try:
            writer_sync = _tr.sync_try(G, v4.trust(2))
            try:
                G.e.activate(v4.ST1)
                writer_act = None
            except sa.SelectionRefusal as exc:
                writer_act = {"code": exc.code, "refusal_class": exc.refusal_class, "cause": exc.cause}
            st = G.e.verify()
            res, info = _tr.attempt(G, env, cid)
            held = _tr.refused_as(res, G, cid, {"store_unknown"}, "HOLD")
            blocked = {"sync": writer_sync, "activate": writer_act, "verify": [st.state, st.cause], **info, "counts": list(G.counts())}
        finally:
            monkeypatch.undo()
        res2, info2 = _tr.attempt(G, env, cid)
        return {**blocked, "after_restore": info2, "after_restore_counts": list(G.counts()),
                "breach": blocked["counts"][0] > 0,
                "ok": bool(held and writer_sync and writer_sync["code"] == "verifier_unavailable" and writer_sync["refusal_class"] == "HOLD"
                           and writer_act and writer_act["code"] == "verifier_unavailable" and st.state == "unknown"
                           and res2.status == "executed" and G.counts() == (1, 1, 1, 1))}
    _tr.sub(ev, "registry_unimportable_in_runtime_process", registry_blocked)

    # ---------------------------------------------------------------- (c) text forms
    (tmp_path / "f").mkdir()
    F = v4.Env(tmp_path / "f").boot()
    base = F.dump()
    clean = sel_text.rstrip()

    def dup_key():
        text = clean[:-1] + ',"statement_digest":"sha256:' + "0" * 64 + '"}'  # second, conflicting value for a signed-over member
        try:
            F.dest.activate_selection(record_text=rec_text, selection_text=text, context=v4.s.CTX, trust=F.trust, verifier=v4.ev.Ed25519Verifier())
            return {"activated": True, "breach": True, "ok": False}
        except sa.SelectionRefusal as exc:
            return {"refusal": {"code": exc.code, "refusal_class": exc.refusal_class, "cause": exc.cause}, "unchanged": F.dump() == base,
                    "ok": F.dump() == base}
    _tr.sub(ev, "duplicate_key_selection_text", dup_key)

    def noncanonical():
        text = json.dumps(json.loads(sel_text), indent=2)
        try:
            F.dest.activate_selection(record_text=rec_text, selection_text=text, context=v4.s.CTX, trust=F.trust, verifier=v4.ev.Ed25519Verifier())
            return {"activated": True, "status": F.state().status, "informational": True,
                    "note": "pretty-printed (non-canonical whitespace) envelope text was accepted; the signature covers the canonical statement"}
        except sa.SelectionRefusal as exc:
            return {"refusal": {"code": exc.code, "refusal_class": exc.refusal_class, "cause": exc.cause}, "unchanged": F.dump() == base,
                    "informational": True}
    _tr.sub(ev, "noncanonical_whitespace_selection_text", noncanonical)

    # ---------------------------------------------------------------- (d) separate processes
    S = _tr.newgov(tmp_path, "s")
    senv, scid = S.claim()
    pk = tmp_path / "env.pickle"
    pk.write_bytes(pickle.dumps((senv, v4_policy())))
    succ = tmp_path / "successor_claim.json"
    succ.write_text(json.dumps(_tr.g.make_claim(senv, S.now, binding=_tr.g.binding_of(S.state()), claim_id="dep-succ-1"), default=str))
    work = tmp_path / "work"
    work.mkdir()

    def exec_probe(label, python, mode, paths):
        a = _clone(S, tmp_path / f"clone_{label}")
        r = _run_probe(python, work, mode, tmp_path / f"clone_{label}", a, scid, pk, succ, paths)
        r["parent_db"] = _count(tmp_path / f"clone_{label}" / S.dest.path.name)
        return r

    def d_no_registry():
        r = exec_probe("noreg", PY_MAIN, "execute", _paths(registry=False))
        if "harness_error" in r:
            return r
        db = r["parent_db"]
        r["ok"] = bool(r.get("status") != "executed" and db.get("effects") == 0 and db.get("claim_states") == ["issued"])
        r["breach"] = bool(r.get("status") == "executed" or db.get("effects", 0) > 0)
        return r
    _tr.sub(ev, "process_registry_absent", d_no_registry)

    def d_no_validator():
        r = exec_probe("noval", PY_MAIN, "execute_no_binding_validator", _paths())
        if "harness_error" in r:
            return r
        db = r["parent_db"]
        r["ok"] = bool(r.get("status") != "executed" and db.get("effects") == 0 and db.get("claim_states") == ["issued"])
        r["breach"] = bool(r.get("status") == "executed" or db.get("effects", 0) > 0)
        return r
    _tr.sub(ev, "process_binding_validator_blocked", d_no_validator)

    def d_legacy_cp():
        r = _run_probe(PY_MAIN, work, "provision", tmp_path / "legacy_root", tmp_path / "unused.json", "x", pk, succ, _paths(cp="control_plane_legacy",
                                                                                                                              registry=False))
        if "harness_error" in r:
            return r
        r["parent_db"] = _count(tmp_path / "legacy_root" / S.dest.path.name)
        r["ok"] = bool(r.get("provisioned") is False and r["parent_db"].get("claims") == 0)
        r["breach"] = bool(r.get("provisioned") is True)
        return r
    _tr.sub(ev, "process_legacy_control_plane_refuses_successor_claim", d_legacy_cp)

    def d_no_nacl():
        r = exec_probe("nonacl", PY_MAIN, "execute_no_nacl", _paths())
        r["informational"] = True
        return r
    _tr.sub(ev, "informational_process_pynacl_blocked_effect_time", d_no_nacl)

    def d_old_pydantic():
        r = _run_probe(PY_OLD, work, "provision", tmp_path / "old_root", tmp_path / "unused.json", "x", pk, succ, _paths(registry=False))
        r["informational"] = True
        return r
    _tr.sub(ev, "informational_process_pydantic_2_11_9_provisions_successor_claim", d_old_pydantic)
    _tr.verdict(ev)


def v4_policy():
    return _tr.g.effect_policy()
