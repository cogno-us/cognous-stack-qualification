"""Verdict engine: oracle x observation bundle -> report. Deterministic, read-only, stdlib-only.

Trust model: the evaluator trusts (a) the committed oracle hash, (b) the committed freeze root, (c) the
externally supplied bundle hash, and (d) raw files only after sha256 verification against raw_index.
It does NOT trust bundle labels: a boundary's outcome is derived from hash-verified raw evidence
(`raw` => returned, `exception_raw` => raised). The future driver is still trusted for call fidelity
and for the completeness of driver_events (see README, residual trust).
"""
from __future__ import annotations

import json
from pathlib import Path

from . import EVALUATOR_VERSION, guard, oracle as O, predicates as P, verdicts as V
from .identity import sha256_hex
from .identity import commitment
from .pointer import BLOCKED, is_missing, resolve

BUNDLE_SCHEMA = "ia-observation-bundle/1"
CLAIM_LIMIT = ("Internal nonproduction Q-A assessment ceiling only: decision-only, synthetic, source-pinned, fully populated Manifest 1.1 fixture. "
               "Not independent qualification, certification, release or production authorization; OBS results validate no security property.")


class _Raw:
    """Lazy, hash-verified, containment-checked access to bundle raw files."""

    def __init__(self, root: Path, index: dict):
        self.root, self.index, self._c = root.resolve(), index, {}

    def get(self, rel):
        """('ok', (parsed, sha256)) | ('missing'|'tampered'|'unparsable', message)."""
        key = rel if isinstance(rel, str) else repr(rel)
        if key in self._c:
            return self._c[key]
        self._c[key] = self._load(rel)
        return self._c[key]

    def _load(self, rel):
        if not isinstance(rel, str) or not rel or "\0" in rel or "\\" in rel or ".." in Path(rel).parts or Path(rel).is_absolute():
            return ("missing", f"bad raw path {rel!r}")
        want = self.index.get(rel)
        if not isinstance(want, str):
            return ("missing", f"{rel} not in raw_index")
        p = self.root / rel
        try:
            real = p.resolve(strict=True)
            real.relative_to(self.root)           # blocks symlinked directories and escapes
        except (OSError, ValueError):
            return ("missing", f"{rel} absent or outside the bundle")
        if p.is_symlink() or not real.is_file():
            return ("missing", f"{rel} is not a regular file")
        data = real.read_bytes()
        if len(data) > O.MAX_JSON_BYTES:
            return ("unparsable", f"{rel} exceeds the evaluator size cap")
        got = sha256_hex(data)
        if got != want:
            return ("tampered", f"{rel} sha256 {got} != indexed {want}")
        try:
            return ("ok", (O.load_json_strict(data), got))
        except O.OracleError as e:
            return ("unparsable", f"{rel}: {e}")


def _report_stub(orc, overall, reason, cases=None, extra=None):
    return {"evaluator": EVALUATOR_VERSION, "oracle_version": (orc or {}).get("oracle_version"), "overall": overall, "claim_basis": overall,
            "blocked_reason": reason, "cases": cases or [], "claim_limit": CLAIM_LIMIT, **(extra or {})}


def _blocked(orc, reason):
    cases = [{"id": c["id"], "class": c["class"], "mandatory": c["mandatory"], "claim_gated": c["class"] in O.GATED, "verdict": V.NOT_RUN,
              "blocked_reason": reason, "executed": False} for c in orc.get("cases", [])]
    mand = [c["verdict"] for c in cases if c["mandatory"]]
    return _report_stub(orc, V.combine(mand) if mand else V.NOT_RUN, reason, cases)


def _ref_value(raw, ref):
    st, pl = raw.get(ref) if ref else ("missing", "no raw reference")
    return (st, pl)


def _target(raw, bres, ptr):
    """Resolve '#raw_sha256', '#input:<name>' or a JSON pointer inside a boundary's returned raw value."""
    st, pl = _ref_value(raw, bres.get("raw"))
    if ptr == "#raw_sha256":
        return ("ok", pl[1]) if st == "ok" else (st, pl)
    if isinstance(ptr, str) and ptr.startswith("#input:"):
        inputs = bres.get("inputs")
        ref = inputs.get(ptr[len("#input:"):]) if isinstance(inputs, dict) else None
        if ref is None:
            return ("unevaluable", f"input {ptr[7:]} not recorded")
        s2, p2 = raw.get(ref)
        return ("ok", p2[1]) if s2 == "ok" else (s2, p2)
    if st != "ok":
        return (st, pl)
    return ("ok", resolve(pl[0], ptr))


def _outcome(bres, raw):
    """Derive the outcome from hash-verified evidence, never from the label alone."""
    has_raw, has_exc = bres.get("raw") is not None, bres.get("exception_raw") is not None
    if has_raw == has_exc:
        return None, "boundary must carry exactly one of raw (returned) or exception_raw (raised)"
    label = bres.get("outcome")
    want = "returned" if has_raw else "raised"
    if label != want:
        return None, f"outcome label {label!r} disagrees with the evidence kind ({want})"
    return want, None


def _eval_obs(ob, cobs, raw):
    b, op = ob["boundary"], ob["op"]
    bres = cobs.get("boundaries")
    bres = bres.get(b) if isinstance(bres, dict) else None
    if not isinstance(bres, dict):
        return "unevaluable", f"boundary {b} not observed", None
    outcome, why = _outcome(bres, raw)
    if outcome is None:
        return "unevaluable", why, None
    if op in P.EXCEPTION_OPS:
        if op == "returned":
            if outcome == "returned":
                st, pl = _ref_value(raw, bres["raw"])
                return (("ok", "native returned (hash-verified raw present)", None) if st == "ok" else
                        ("violated" if st == "tampered" else "unevaluable", pl, None))
            return "violated", "native raised where a return was required", None
        if outcome != "raised":
            return "violated", "expected a native refusal but the call returned", None
        st, pl = _ref_value(raw, bres["exception_raw"])
        if st != "ok":
            return ("violated" if st == "tampered" else "unevaluable"), pl, None
        exc = pl[0]
        if not isinstance(exc, dict) or not isinstance(exc.get("type"), str) or not isinstance(exc.get("message"), str):
            return "unevaluable", "exception evidence lacks type/message strings", None
        if op == "raised_type":
            ok = exc["type"] == ob["expected"]
            return ("ok" if ok else "violated"), f"exception type {exc['type']!r} expected {ob['expected']!r}", exc["type"]
        if op == "raised_message_equals":
            ok = exc["message"] == ob["expected"]
        else:
            ok = ob["expected"] in exc["message"]
        return ("ok" if ok else "violated"), f"message {exc['message'][:200]!r} vs expected {ob['expected']!r} ({op})", exc["message"][:200]
    if outcome != "returned":
        return "violated", "native raised; a value predicate cannot be satisfied", None
    kind, val = _target(raw, bres, ob.get("pointer"))
    if kind == "tampered":
        return "violated", val, None
    if kind in ("missing", "unparsable", "unevaluable"):
        return "unevaluable", val, None
    if op in P.PRESENCE_OPS:
        present = not is_missing(val)
        return ("ok" if present == (op == "present") else "violated"), f"pointer {ob.get('pointer')} present={present}", None
    if val is BLOCKED:
        return "violated", f"pointer {ob.get('pointer')} crosses a null or scalar: observed structure contradicts the expected one", None
    if is_missing(val):
        return "unevaluable", f"pointer {ob.get('pointer')} missing (no default is assumed)", None
    if op in P.COMMIT_OPS:
        st2, pl2 = _ref_value(raw, bres.get("raw"))
        if st2 != "ok":
            return ("violated" if st2 == "tampered" else "unevaluable"), pl2, None
        other = resolve(pl2[0], ob["expected"])
        if is_missing(other):
            return "unevaluable", f"commitment source {ob['expected']} missing", None
        ok = isinstance(val, str) and val == commitment(other)
        return ("ok" if ok else "violated"), "observed commitment " + ("equals" if ok else "differs from") + " the evaluator-recomputed canonical commitment", repr(val)[:200]
    if op in P.RELATION_OPS:
        ref2 = ob["expected"]
        cb = cobs["boundaries"].get(ref2["boundary"])
        if not isinstance(cb, dict):
            return "unevaluable", f"relation boundary {ref2['boundary']} not observed", None
        k2, v2 = _target(raw, cb, ref2["pointer"])
        if k2 == "tampered":
            return "violated", v2, None
        if k2 != "ok" or is_missing(v2):
            return "unevaluable", f"relation target unavailable: {v2}", None
        if bres.get("raw") == cb.get("raw") and ob.get("pointer") == ref2["pointer"]:
            return "unevaluable", "relation compares a value with itself (both sides alias the same raw file and pointer)", None
        same = P.deq(val, v2)
        return ("ok" if same == (op == "eq_ref") else "violated"), f"relation {op}: equal={same}", None
    ok, d = P.VALUE_OPS[op](val, ob.get("expected"))
    return ("ok" if ok else "violated"), d, repr(val)[:200]


def evaluate_case(c, cobs, raw):
    base = {"id": c["id"], "title": c.get("title"), "class": c["class"], "mandatory": c["mandatory"],
            "claim_gated": c["class"] in O.GATED, "failure_condition": c["failure_condition"]}
    if c["class"] == "INFO":
        return {**base, "verdict": V.NOT_RUN, "executed": False, "blocked_reason": "informational by Architect decision D9: " + c["reason"], "observations": []}
    if c["class"] == "NA":
        return {**base, "verdict": V.NOT_APPLICABLE, "executed": False, "not_applicable_reason": c["reason"], "observations": []}
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
    notes = cobs.get("adverse_notes")
    out = {**base, "verdict": verdict, "executed": True, "observations": recs, "adverse_notes": notes if isinstance(notes, list) else []}
    if verdict == V.INCONCLUSIVE:
        out["reason"] = "attempted but unevaluable: " + "; ".join(r["detail"] for r in recs if r["status"] == "unevaluable")[:600]
    if c["class"] == "OBS":
        out["observation_result"] = "OBSERVED_AS_FROZEN" if verdict == V.PASS else ("DEVIATES_FROM_FROZEN_OBSERVATION" if verdict == V.FAIL else "UNEVALUABLE")
        out["security_property_validated"] = False
        out["claim_gated"] = False
    return out


def _run(oracle_bytes, bundle_dir, expect_oracle_sha256, expect_bundle_sha256, extra_block):
    try:
        orc = O.load_json_strict(oracle_bytes)
    except O.OracleError as e:
        return _report_stub(None, V.NOT_RUN, f"ORACLE_UNREADABLE: {e}")
    errs = O.validate(orc)
    if errs:
        return _report_stub(orc, V.NOT_RUN, "ORACLE_INVALID: " + "; ".join(errs)[:800]) if not isinstance(orc.get("cases"), list) else _blocked(orc, "ORACLE_INVALID: " + "; ".join(errs)[:800])
    if not isinstance(expect_oracle_sha256, str) or O.sha256_bytes(oracle_bytes) != expect_oracle_sha256:
        return _blocked(orc, f"ORACLE_DRIFT: sha256 {O.sha256_bytes(oracle_bytes)} != committed {expect_oracle_sha256}")
    if extra_block:
        return _blocked(orc, extra_block)
    root = Path(bundle_dir)
    bpath = root / "bundle.json"
    if bpath.is_symlink() or not bpath.is_file():
        return _blocked(orc, "BUNDLE_MISSING: bundle.json not found or not a regular file")
    bdata = bpath.read_bytes()
    if not isinstance(expect_bundle_sha256, str) or O.sha256_bytes(bdata) != expect_bundle_sha256:
        return _blocked(orc, f"BUNDLE_DRIFT: bundle.json sha256 {O.sha256_bytes(bdata)} != externally recorded {expect_bundle_sha256}")
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
    by_id = {x["id"]: x for x in cases}
    for c, x in zip(orc["cases"], cases):
        pc = c.get("paired_control")
        if pc and x["verdict"] == V.PASS and by_id[pc]["verdict"] != V.PASS:
            x["verdict"] = V.INCONCLUSIVE
            x["reason"] = f"attempted but unevaluable: paired control {pc} is not PASS, so the refusal cannot be attributed to the mutation"
    mand = [x for x in cases if x["mandatory"]]
    executed_mand = [x for x in mand if x["executed"]]
    overall = V.combine(x["verdict"] for x in mand)
    gated = V.combine(x["verdict"] for x in cases if x["claim_gated"])
    if violations:
        overall, gated = V.FAIL, V.FAIL           # fail closed: no consumer may read a PASS claim basis
    if not executed_mand and overall == V.PASS:
        overall, gated = V.NOT_RUN, V.NOT_RUN
    return {
        "evaluator": EVALUATOR_VERSION, "oracle_version": orc["oracle_version"], "oracle_sha256": O.sha256_bytes(oracle_bytes),
        "bundle_sha256": O.sha256_bytes(bdata), "raw_index": bundle["raw_index"],
        "overall": overall, "claim_basis": gated, "violations": violations,
        "mandatory_cases": len(mand), "executed_mandatory_cases": len(executed_mand),
        "counts": {v: sum(1 for x in cases if x["verdict"] == v) for v in V.VERDICTS},
        "obs_summary": {x["id"]: x.get("observation_result", "NOT_OBSERVED") for x in cases if x["class"] == "OBS"},
        "ignored_orchestrator_status_keys": sorted(map(str, bundle.get("orchestrator_status", {}))) if isinstance(bundle.get("orchestrator_status"), dict) else [],
        "cases": cases, "claim_limit": CLAIM_LIMIT,
    }


def run(oracle_bytes: bytes, bundle_dir, expect_oracle_sha256: str, expect_bundle_sha256: str, extra_block=None):
    """Evaluate a bundle. Any unexpected evaluator error becomes INCONCLUSIVE with a reason, never PASS and never a silent crash."""
    try:
        return _run(oracle_bytes, bundle_dir, expect_oracle_sha256, expect_bundle_sha256, extra_block)
    except Exception as e:   # noqa: BLE001 - deliberate fail-closed catch-all
        return _report_stub(None, V.INCONCLUSIVE, f"EVALUATOR_ERROR: {type(e).__name__}: {str(e)[:200]}")
