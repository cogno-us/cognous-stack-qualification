"""Worker C (area `trust`) shared helpers. Fixture MECHANICS only are reused from the Runtime's existing test modules
(`test_registry_selection_effect_guard` -> class `Gov`, `make_claim`, `binding_of`, `effect_policy`; `test_registry_selection_authority` -> `Env`,
statement/record/trust builders). Every oracle and attack in this area is written here, not copied.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import test_registry_selection_effect_guard as g  # fixture mechanics (Gov, make_claim, binding_of, effect_policy)

v4 = g.v4
sa = g.sa
REPO = Path(__file__).resolve().parents[3]
PAIR = frozenset({("sel-test-1", 1)})


def newgov(tmp_path: Path, name: str, **kw):
    (tmp_path / name).mkdir(parents=True, exist_ok=True)
    return g.Gov(tmp_path / name, **kw)


def typed_of(res) -> dict | None:
    return (res.control_plane_evidence or {}).get("selection_refusal")


def claim_state(gov, cid: str):
    conn = sqlite3.connect(gov.dest.path)
    try:
        row = conn.execute("SELECT state FROM execution_claims_v1 WHERE claim_id=?", (cid,)).fetchone()
    finally:
        conn.close()
    return row[0] if row else None


def attempt(gov, env, cid, policy=None):
    res = gov.executor(policy).execute(envelope=env, claim_id=cid)
    return res, {"status": res.status, "attempted": res.attempted, "error": (res.error or "")[:240], "typed": typed_of(res),
                 "failure_class": (res.control_plane_evidence or {}).get("failure_class")}


def zero(gov, cid) -> bool:
    return gov.counts() == (0, 0, 0, 0) and claim_state(gov, cid) == "issued"


def refused_as(res, gov, cid, codes, cls=None) -> bool:
    t = typed_of(res)
    return bool(res.status == "denied" and res.attempted is False and t and t["code"] in codes and (cls is None or t["refusal_class"] == cls)
                and zero(gov, cid))


def save(gov, path: Path) -> None:
    src, dst = sqlite3.connect(gov.dest.path), sqlite3.connect(path)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()


def restore(gov, path: Path) -> None:
    src, dst = sqlite3.connect(path), sqlite3.connect(gov.dest.path, isolation_level=None)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()


def sync_try(gov, trust_obj, **kw) -> dict | None:
    """Deliver a snapshot to the Runtime writer. None = accepted; else the typed refusal as data."""
    try:
        gov.dest.sync_selection("snapshot", trust=trust_obj, **kw)
        return None
    except sa.SelectionRefusal as exc:
        return {"code": exc.code, "refusal_class": exc.refusal_class, "cause": exc.cause}


def fingerprint_state(gov) -> dict:
    """Everything an unaccepted transition must leave byte-identical."""
    return {"dump": gov.e.dump(), "anchor": gov.e.anchor.read_text(), "head": gov.e.head()}


def sub(ev, name: str, fn) -> dict:
    """Run one sub-probe; a harness exception becomes INCONCLUSIVE evidence, never a crash and never a pass."""
    try:
        out = fn()
    except Exception as exc:  # noqa: BLE001 - recorded, not swallowed
        out = {"harness_error": f"{type(exc).__name__}: {exc}"[:600]}
    ev["observed"].setdefault("probes", {})[name] = out
    return out


def verdict(ev, *, allow=("HELD",), note: str = "") -> None:
    probes = ev["observed"].get("probes", {})
    breach = [k for k, v in probes.items() if v.get("breach")]
    harness = [k for k, v in probes.items() if "harness_error" in v and not v.get("informational")]
    untyped = [k for k, v in probes.items() if v.get("untyped_failclosed")]
    notok = [k for k, v in probes.items() if not v.get("ok") and not v.get("breach") and "harness_error" not in v and not v.get("informational")
             and not v.get("untyped_failclosed")]
    if breach:
        ev["verdict"], ev["note"] = "BREACH", f"unauthorized effect or bypass in probes {breach}. {note}"
    elif harness:
        ev["verdict"], ev["note"] = "INCONCLUSIVE", f"harness error in probes {harness}; the intended path was not exercised. {note}"
    elif notok:
        ev["verdict"], ev["note"] = "INCONCLUSIVE", f"probes {notok} did not meet the stated oracle although no unauthorized effect was seen. {note}"
    elif untyped:
        ev["verdict"] = "CHARACTERIZED" if "CHARACTERIZED" in allow else "INCONCLUSIVE"
        ev["note"] = (f"fail-closed (no effect, claim unconsumed) but NOT as a typed store_unknown/HOLD refusal in probes {untyped}: an exception other than "
                      f"SelectionRefusal escaped the store verifier. {note}")
    else:
        ev["verdict"], ev["note"] = allow[0], note
    assert ev["verdict"] in allow, (ev["verdict"], ev["note"])


def log_entry(gov, seq: int) -> dict:
    return json.loads(gov.e.sql("SELECT entry_json FROM selection_log_v1 WHERE activation_sequence=?", (seq,))[0][0])


def put_entry(gov, seq: int, entry: dict, *, rehash: bool) -> str:
    raw = sa.canonical_bytes(entry).decode("ascii")
    h = sa.entry_hash_of(entry)
    if rehash:
        gov.e.sql("UPDATE selection_log_v1 SET entry_json=?, entry_hash=? WHERE activation_sequence=?", (raw, h, seq))
    else:
        gov.e.sql("UPDATE selection_log_v1 SET entry_json=? WHERE activation_sequence=?", (raw, seq))
    return h


def tamper_probe(gov, env, cid, pristine: Path, mutate, *, anchor_text: str | None = None) -> dict:
    """Restore the pristine database (and anchor text if given), prove the store is `known`, apply `mutate` (an adversary with file-write access),
    then execute the claim at the effect boundary. HELD-grade evidence: tamper delivered (verify != known or raises), effect refused with typed
    store_unknown/HOLD, zero effects/attempts/receipts/budget, claim still issued."""
    restore(gov, pristine)
    if anchor_text is not None:
        gov.e.anchor.write_text(anchor_text)
    pre = gov.e.verify()
    out: dict = {"pre_state": pre.state}
    gov.e.drop_guards()
    try:
        mutate()
    except Exception as exc:  # noqa: BLE001
        out["mutation_error"] = f"{type(exc).__name__}: {exc}"[:300]
        out["ok"] = False
        return out
    try:
        st = gov.e.verify()
        out.update(verify_state=st.state, verify_cause=st.cause)
    except Exception as exc:  # noqa: BLE001
        out.update(verify_state="raised", verify_cause=f"{type(exc).__name__}: {exc}"[:200])
    res, info = attempt(gov, env, cid)
    out.update(info, counts=list(gov.counts()), claim_state=claim_state(gov, cid))
    out["breach"] = gov.counts()[0] > 0
    typed_hold = refused_as(res, gov, cid, {"store_unknown"}, "HOLD")
    out["typed_hold"] = typed_hold
    out["untyped_failclosed"] = bool(res.status != "executed" and not out["breach"] and not typed_hold and zero(gov, cid))
    out["ok"] = bool(pre.state == "known" and out.get("verify_state") != "known" and typed_hold and not out["breach"])
    return out
