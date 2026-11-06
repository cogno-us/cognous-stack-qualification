"""Oracle loading and structural validation. Strict: unknown keys, duplicate ids, unsourced
required-invariant observations and orchestrator-label pointers all invalidate the oracle."""
from __future__ import annotations

import hashlib
import json

from . import predicates as P

ORACLE_SCHEMA = "ia-oracle/1"
CLASSES = ("PRE", "CTL", "RI", "OBS", "INFO")
GATED = ("PRE", "CTL", "RI")          # contribute to the Q-A claim gate
# Orchestrator/harness labels (L25): never evidence. A pointer segment equal to one of these is refused.
ORCHESTRATOR_NAMES = frozenset({
    "chain_verdict", "retains_upstream_refusal", "carried_authorization_state", "harness_run_ref",
    "all_ok", "ok", "passed", "boundary_verdicts", "REFUSED_NATIVE", "ACCEPTED", "NOT_ATTEMPTED",
    "check_count", "oracle_checks", "expected", "expected_results",
})
_TOP = {"schema", "oracle_version", "profile", "subject", "allowed_native_calls", "cases", "exclusions", "claim", "notes"}
_CASE = {"id", "title", "class", "mandatory", "mutation", "entrypoint", "observations", "failure_condition", "reason", "limit_ids"}
_OBS = {"id", "boundary", "pointer", "op", "expected", "source", "note"}
_SRC = {"kind", "component", "commit", "path", "line", "confidence", "limit_id", "text"}


class OracleError(Exception):
    pass


def _no_dup_pairs(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise OracleError(f"duplicate JSON key {k!r}")
        d[k] = v
    return d


def load_json_strict(data: bytes):
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_no_dup_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise OracleError(f"not valid UTF-8 JSON: {e}") from e


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def validate(o: dict) -> list:
    errs = []
    if not isinstance(o, dict) or o.get("schema") != ORACLE_SCHEMA:
        return [f"schema must be {ORACLE_SCHEMA}"]
    errs += [f"unknown top-level key {k}" for k in o if k not in _TOP]
    for k in ("oracle_version", "profile", "subject", "allowed_native_calls", "cases", "exclusions", "claim"):
        if k not in o:
            errs.append(f"missing top-level key {k}")
    seen = set()
    for c in o.get("cases", []):
        cid = c.get("id")
        if not isinstance(cid, str) or cid in seen:
            errs.append(f"bad or duplicate case id {cid!r}")
        seen.add(cid)
        errs += [f"{cid}: unknown key {k}" for k in c if k not in _CASE]
        if c.get("class") not in CLASSES:
            errs.append(f"{cid}: class must be one of {CLASSES}")
        if not isinstance(c.get("mandatory"), bool):
            errs.append(f"{cid}: mandatory must be boolean")
        if c.get("class") == "INFO" and c.get("mandatory"):
            errs.append(f"{cid}: INFO cases cannot be mandatory")
        if c.get("class") in GATED + ("OBS",) and not c.get("mandatory"):
            errs.append(f"{cid}: {c.get('class')} cases are mandatory (demote to INFO with a reason instead)")
        if not c.get("failure_condition"):
            errs.append(f"{cid}: failure_condition required")
        if c.get("class") in ("OBS", "INFO") and not c.get("reason"):
            errs.append(f"{cid}: reason required for OBS/INFO")
        obs = c.get("observations", [])
        if c.get("class") != "INFO" and not obs:
            errs.append(f"{cid}: zero observations (a case that cannot fail is vacuous)")
        oseen = set()
        for ob in obs:
            oid = ob.get("id")
            if oid in oseen:
                errs.append(f"{cid}: duplicate observation id {oid}")
            oseen.add(oid)
            errs += [f"{cid}/{oid}: unknown key {k}" for k in ob if k not in _OBS]
            if ob.get("op") not in P.ALL_OPS:
                errs.append(f"{cid}/{oid}: unknown op {ob.get('op')!r}")
            ptr = ob.get("pointer")
            if ptr is not None:
                segs = [s for s in str(ptr).lstrip("#").split("/") if s]
                bad = [s for s in segs if s in ORCHESTRATOR_NAMES]
                if bad:
                    errs.append(f"{cid}/{oid}: pointer uses orchestrator-label segment {bad} (L25)")
            src = ob.get("source")
            if c.get("class") in GATED and not src:
                errs.append(f"{cid}/{oid}: required-invariant observation needs a source")
            if src:
                errs += [f"{cid}/{oid}: unknown source key {k}" for k in src if k not in _SRC]
                if src.get("kind") == "native_source" and not (isinstance(src.get("line"), int) and src["line"] > 0 and src.get("path") and src.get("commit")):
                    errs.append(f"{cid}/{oid}: native_source needs commit, path and positive line")
                if src.get("kind") not in ("native_source", "frozen_limit", "evaluator_relation", "frozen_literal"):
                    errs.append(f"{cid}/{oid}: bad source kind {src.get('kind')!r}")
    return errs
