"""Verdict engine: oracle x observation bundle -> report. Deterministic, read-only, stdlib-only."""
from __future__ import annotations

import json
from pathlib import Path

from . import EVALUATOR_VERSION, guard, oracle as O, predicates as P, verdicts as V
from .pointer import MISSING, resolve

BUNDLE_SCHEMA = "ia-observation-bundle/1"
CLAIM_LIMIT = ("Internal nonproduction Q-A assessment ceiling only: decision-only, synthetic, source-pinned, fully populated Manifest 1.1 fixture. "
               "Not independent qualification, certification, release or production authorization; OBS results validate no security property.")


class _Raw:
    """Lazy, hash-verified access to bundle raw files."""

    def __init__(self, root: Path, index: dict):
        self.root, self.index, self._c = root, index, {}

    def get(self, rel):
        """Return (status, payload): ('ok', parsed) | ('missing', msg) | ('tampered', msg) | ('unparsable', msg)."""
        if rel in self._c:
            return self._c[rel]
        res = self._load(rel)
        self._c[rel] = res
        return res

    def _load(self, rel):
        if not isinstance(rel, str) or ".." in Path(rel).parts or Path(rel).is_absolute():
            return ("missing", f"bad raw path {rel!r}")
        want = self.index.get(rel)
        p = self.root / rel
        if want is None:
            return ("missing", f"{rel} not in raw_index")
        if p.is_symlink() or not p.is_file():
            return ("missing", f"{rel} absent")
        data = p.read_bytes()
        from .identity import sha256_hex
        got = sha256_hex(data)
        if got != want:
            return ("tampered", f"{rel} sha256 {got} != indexed {want}")
        try:
            return ("ok", (O.load_json_strict(data), got))
        except O.OracleError as e:
            return ("unparsable", f"{rel}: {e}")


def _blocked(oracle, reason, extra=None):
    cases = []
    for c in oracle.get("cases", []):
        cases.append({"id": c["id"], "class": c["class"], "mandatory": c["mandatory"], "verdict": V.NOT_RUN, "blocked_reason": reason, "executed": False})
    mand = [c["verdict"] for c in cases if c["mandatory"]]
    return {"evaluator": EVALUATOR_VERSION, "oracle_version": oracle.get("oracle_version"), "overall": V.combine(mand) if mand else V.NOT_RUN,
            "blocked_reason": reason, "cases": cases, "claim_limit": CLAIM_LIMIT, **(extra or {})}


def _target(case_obs, raw_rec, bres, ptr):
    """Resolve '#raw_sha256', '#input:<name>' or a JSON pointer inside a boundary. Returns (kind, value)."""
    if ptr == "#raw_sha256":
        st, pl = raw_rec
        return ("ok", pl[1]) if st == "ok" else (st, pl)
    if ptr is not None and ptr.startswith("#input:"):
        name = ptr[len("#input:"):]
        ref = (bres.get("inputs") or {}).get(name)
        if ref is None:
            return ("unevaluable", f"input {name} not recorded")
        st, pl = case_obs["_raw"].get(ref)
        return ("ok", pl[1]) if st == "ok" else (st, pl)
    st, pl = raw_rec
    if st != "ok":
        return (st, pl)
    v = resolve(pl[0], ptr)
    return ("ok", v)


def _eval_obs(ob, cobs, raw):
    b = ob["boundary"]
    bres = (cobs.get("boundaries") or {}).get(b)
    if not isinstance(bres, dict):
        return "unevaluable", f"boundary {b} not observed", None
    op = ob["op"]
    outcome = bres.get("outcome")
    if outcome not in ("returned", "raised"):
        return "unevaluable", f"boundary {b} has no valid outcome", None
    if op in P.EXCEPTION_OPS:
        if op == "returned":
            return ("ok", "returned", None) if outcome == "returned" else ("violated", f"native raised {bres.get('exception')!r} where a return was required", None)
        if outcome != "raised":
            return "violated", "expected a native refusal but the call returned", None
        exc = bres.get("exception")
        if not isinstance(exc, dict) or not isinstance(exc.get("type"), str) or not isinstance(exc.get("message"), str):
            return "unevaluable", "exception record missing type/message", None
        if op == "raised_type":
            ok = exc["type"] == ob["expected"]
            return ("ok" if ok else "violated"), f"exception type {exc['type']!r} expected {ob['expected']!r}", exc["type"]
        ok = ob["expected"] in exc["message"]
        return ("ok" if ok else "violated"), f"message {exc['message'][:200]!r} must contain {ob['expected']!r}", exc["message"][:200]
    # value operators need a returned boundary with a raw record
    if outcome != "returned":
        return "violated", f"native raised {bres.get('exception')!r}; value predicate cannot be satisfied", None
    ref = bres.get("raw")
    raw_rec = raw.get(ref) if ref else ("missing", "no raw reference")
    cobs_ctx = dict(cobs)
    cobs_ctx["_raw"] = raw
    if op in P.TEXT_OPS:
        if raw_rec[0] != "ok":
            return ("violated" if raw_rec[0] == "tampered" else "unevaluable"), raw_rec[1], None
        text = json.dumps(raw_rec[1][0], sort_keys=True)
        ok, d = P.op_text_lacks(text, ob["expected"])
        return ("ok" if ok else "violated"), d, None
    kind, val = _target(cobs_ctx, raw_rec, bres, ob.get("pointer"))
    if kind == "tampered":
        return "violated", val, None
    if kind in ("missing", "unparsable", "unevaluable"):
        return "unevaluable", val, None
    if op in P.PRESENCE_OPS:
        present = val is not MISSING
        return ("ok" if present == (op == "present") else "violated"), f"pointer {ob.get('pointer')} present={present}", None
    if val is MISSING:
        return "unevaluable", f"pointer {ob.get('pointer')} missing (no default is assumed)", None
    if op in P.RELATION_OPS:
        ref2 = ob["expected"]
        b2 = (cobs.get("boundaries") or {}).get(ref2.get("boundary"))
        if not isinstance(b2, dict):
            return "unevaluable", f"relation boundary {ref2.get('boundary')} not observed", None
        raw2 = raw.get(b2.get("raw")) if b2.get("raw") else ("missing", "no raw reference")
        k2, v2 = _target(cobs_ctx, raw2, b2, ref2.get("pointer"))
        if k2 == "tampered":
            return "violated", v2, None
        if k2 != "ok" or v2 is MISSING:
            return "unevaluable", f"relation target unavailable: {v2}", None
        same = type(val) is type(v2) and val == v2
        return ("ok" if same == (op == "eq_ref") else "violated"), f"relation {op}: {same}", None
    ok, d = P.VALUE_OPS[op](val, ob["expected"])
    return ("ok" if ok else "violated"), d, repr(val)[:200]


def evaluate_case(c, cobs, raw):
    base = {"id": c["id"], "title": c.get("title"), "class": c["class"], "mandatory": c["mandatory"],
            "claim_gated": c["class"] in O.GATED, "failure_condition": c["failure_condition"]}
    if c["class"] == "INFO":
        return {**base, "verdict": V.NOT_RUN, "executed": False, "blocked_reason": "informational by Architect decision D9: " + c["reason"], "observations": []}
    if not isinstance(cobs, dict) or cobs.get("executed") is not True:
        return {**base, "verdict": V.NOT_RUN, "executed": False, "blocked_reason": "case not executed (no execution evidence in bundle)", "observations": []}
    recs, state = [], {"violated": 0, "unevaluable": 0}
    for ob in c["observations"]:
        st, detail, shown = _eval_obs(ob, cobs, raw)
        if st in state:
            state[st] += 1
        recs.append({"id": ob["id"], "boundary": ob["boundary"], "pointer": ob.get("pointer"), "op": ob["op"], "expected": ob.get("expected"),
                     "status": st, "detail": detail, "observed": shown, "source": ob.get("source")})
    verdict = V.FAIL if state["violated"] else (V.INCONCLUSIVE if state["unevaluable"] else V.PASS)
    out = {**base, "verdict": verdict, "executed": True, "observations": recs, "adverse_notes": cobs.get("adverse_notes", [])}
    if verdict == V.INCONCLUSIVE:
        out["reason"] = "attempted but unevaluable: " + "; ".join(r["detail"] for r in recs if r["status"] == "unevaluable")[:600]
    if c["class"] == "OBS":
        out["observation_result"] = "OBSERVED_AS_FROZEN" if verdict == V.PASS else ("DEVIATES_FROM_FROZEN_OBSERVATION" if verdict == V.FAIL else "UNEVALUABLE")
        out["security_property_validated"] = False
        out["claim_gated"] = False
    return out


def run(oracle_bytes: bytes, bundle_dir, expect_oracle_sha256: str, extra_block=None):
    """Evaluate a bundle directory. All failures of preconditions yield NOT RUN + blocked_reason."""
    try:
        orc = O.load_json_strict(oracle_bytes)
    except O.OracleError as e:
        return {"evaluator": EVALUATOR_VERSION, "overall": V.NOT_RUN, "blocked_reason": f"ORACLE_UNREADABLE: {e}", "cases": [], "claim_limit": CLAIM_LIMIT}
    errs = O.validate(orc)
    if errs:
        return _blocked(orc, "ORACLE_INVALID: " + "; ".join(errs)[:800])
    if not isinstance(expect_oracle_sha256, str) or O.sha256_bytes(oracle_bytes) != expect_oracle_sha256:
        return _blocked(orc, f"ORACLE_DRIFT: sha256 {O.sha256_bytes(oracle_bytes)} != committed {expect_oracle_sha256}")
    if extra_block:
        return _blocked(orc, extra_block)
    root = Path(bundle_dir)
    bpath = root / "bundle.json"
    if not bpath.is_file():
        return _blocked(orc, "BUNDLE_MISSING: bundle.json not found")
    bdata = bpath.read_bytes()
    try:
        bundle = O.load_json_strict(bdata)
    except O.OracleError as e:
        return _blocked(orc, f"BUNDLE_UNREADABLE: {e}")
    if not isinstance(bundle, dict) or bundle.get("schema") != BUNDLE_SCHEMA or not isinstance(bundle.get("raw_index"), dict) or not isinstance(bundle.get("cases"), dict):
        return _blocked(orc, "BUNDLE_SCHEMA_INVALID")
    raw = _Raw(root, bundle["raw_index"])
    violations = []
    unknown = sorted(set(bundle["cases"]) - {c["id"] for c in orc["cases"]})
    if unknown:
        violations.append(f"unexpected case ids in bundle: {unknown}")
    violations += guard.check_events(bundle.get("driver_events"), orc["allowed_native_calls"])
    cases = [evaluate_case(c, bundle["cases"].get(c["id"]), raw) for c in orc["cases"]]
    mand = [x for x in cases if x["mandatory"]]
    executed_mand = [x for x in mand if x["executed"]]
    overall = V.combine(x["verdict"] for x in mand)
    if violations:
        overall = V.FAIL
    if not executed_mand and overall == V.PASS:      # zero-case success can never be PASS
        overall = V.NOT_RUN
    gated = [x["verdict"] for x in cases if x["claim_gated"]]
    return {
        "evaluator": EVALUATOR_VERSION, "oracle_version": orc["oracle_version"], "oracle_sha256": O.sha256_bytes(oracle_bytes),
        "bundle_sha256": O.sha256_bytes(bdata), "raw_index": bundle["raw_index"],
        "overall": overall, "claim_basis": V.combine(gated), "violations": violations,
        "mandatory_cases": len(mand), "executed_mandatory_cases": len(executed_mand),
        "counts": {v: sum(1 for x in cases if x["verdict"] == v) for v in V.VERDICTS},
        "obs_summary": {x["id"]: x.get("observation_result", "NOT_OBSERVED") for x in cases if x["class"] == "OBS"},
        "ignored_orchestrator_status_keys": sorted(bundle.get("orchestrator_status", {})) if isinstance(bundle.get("orchestrator_status"), dict) else [],
        "cases": cases, "claim_limit": CLAIM_LIMIT,
    }
