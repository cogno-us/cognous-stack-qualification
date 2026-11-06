#!/usr/bin/env python3
"""Self-test harness + kill-matrix runner for the Internal Milestone A evaluator. STUBS ONLY.

Library (imported by tests/test_*.py) and script:
    python3 -I -B tests/selftest_matrix.py [<outdir>]      (default: internal_a/results/selftest/)
Writes kill_matrix.json, est_results.json, summary.json, SHA256SUMS. Exit code is non-zero if any
observation survives its wrong-value variants, any attack is not defended, or any selected RI oracle
variant / engine mutant survives. Nothing here imports or executes a subject component; the only
code under test is ia_eval, driven through observation bundles synthesised from the oracle.
"""
from __future__ import annotations

import contextlib
import copy
import hashlib
import inspect
import json
import re
import sys
import tempfile
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
for _p in (str(PKG), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
sys.dont_write_bytecode = True

from stubs import Stub, load_oracle, set_pointer  # noqa: E402
from ia_eval import engine, guard, oracle as O, predicates as P, verdicts as V  # noqa: E402
from ia_eval.pointer import BLOCKED, MISSING, is_missing, resolve  # noqa: E402

ORC, ORC_BYTES, ORC_SHA = load_oracle()
PASS, FAIL, INCONC, NOT_RUN, NA = V.PASS, V.FAIL, V.INCONCLUSIVE, V.NOT_RUN, V.NOT_APPLICABLE
MAND = [c["id"] for c in ORC["cases"] if c["mandatory"]]
CASES = {c["id"]: c for c in ORC["cases"]}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def ser(o) -> bytes:
    return (json.dumps(o, sort_keys=True, indent=1) + "\n").encode()


# --------------------------------------------------------------------------- bundle model
class Bundle:
    """In-memory observation bundle with every tamper knob needed by the attacks."""

    def __init__(self, stub: Stub):
        self.raw = copy.deepcopy(stub.raw)
        self.cases = copy.deepcopy(stub.cases)
        self.driver_events = copy.deepcopy(stub.driver_events)
        self.orch = copy.deepcopy(stub.orchestrator_status)
        self.index_over, self.index_drop = {}, set()
        self.drop_files, self.raw_bytes, self.extra = set(), {}, {}
        self.edit, self.bundle_bytes = [], None

    def clone(self) -> "Bundle":
        return copy.deepcopy(self)

    def render(self):
        files, index = {}, {}
        for rel, obj in self.raw.items():
            data = self.raw_bytes[rel] if rel in self.raw_bytes else ser(obj)
            index[rel] = sha(data)
            if rel not in self.drop_files:
                files[rel] = data
        index.update(self.index_over)
        for rel in self.index_drop:
            index.pop(rel, None)
        files.update(self.extra)
        d = {"schema": engine.BUNDLE_SCHEMA, "raw_index": index, "cases": self.cases,
             "driver_events": self.driver_events, "orchestrator_status": self.orch}
        for fn in self.edit:
            fn(d)
        return files, (self.bundle_bytes if self.bundle_bytes is not None else ser(d))


_GOLD = None


def gold() -> Bundle:
    global _GOLD
    if _GOLD is None:
        _GOLD = Bundle(Stub(copy.deepcopy(ORC)))
    return _GOLD


def G() -> Bundle:
    return gold().clone()


class Runner:
    """Writes only the files that changed since the previous run, then calls engine.run."""

    def __init__(self, base):
        self.base = Path(base)
        self.base.mkdir(parents=True, exist_ok=True)
        self.state, self._n = {}, 0

    def fresh(self) -> "Runner":
        self._n += 1
        return Runner(self.base / f"fresh{self._n}")

    def stage(self, b: Bundle) -> bytes:
        files, bb = b.render()
        files = dict(files)
        files["bundle.json"] = bb
        for rel in set(self.state) - set(files):
            (self.base / rel).unlink(missing_ok=True)
        for rel, data in files.items():
            if self.state.get(rel) != data:
                p = self.base / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(data)
        self.state = files
        return bb

    def run(self, b: Bundle, *, oracle_bytes=None, oracle_sha=None, extra_block=None, bundle_sha=None):
        bb = self.stage(b)
        return engine.run(ORC_BYTES if oracle_bytes is None else oracle_bytes, self.base,
                          ORC_SHA if oracle_sha is None else oracle_sha,
                          sha(bb) if bundle_sha is None else bundle_sha, extra_block)


# --------------------------------------------------------------------------- report helpers
def case_of(r, cid):
    return next((c for c in r["cases"] if c["id"] == cid), None)


def vmap(r):
    return {c["id"]: c["verdict"] for c in r["cases"]}


def obs_of(r, cid, oid):
    c = case_of(r, cid)
    return next((o for o in (c or {}).get("observations", []) if o["id"] == oid), None)


def sig(r):
    cases = tuple((c["id"], c["verdict"], c.get("claim_gated"), c.get("security_property_validated"), c.get("observation_result"),
                   tuple((o["id"], o["status"]) for o in c.get("observations", []))) for c in r["cases"])
    return (r.get("overall"), r.get("claim_basis"), (r.get("blocked_reason") or "")[:24], tuple(r.get("violations") or ()), cases,
            tuple(sorted((r.get("counts") or {}).items())), tuple(sorted((r.get("obs_summary") or {}).items())))


def not_pass(r):
    return r["overall"] != PASS and r["claim_basis"] != PASS


# --------------------------------------------------------------------------- bundle edit helpers
def rawrel(b, cid, bd):
    br = b.cases[cid]["boundaries"][bd]
    return br.get("raw") or br["exception_raw"]


def setv(b, cid, bd, ptr, val):
    rel = rawrel(b, cid, bd)
    b.raw[rel] = set_pointer(b.raw[rel], ptr, val)


def getv(b, cid, bd, ptr):
    return resolve(b.raw[rawrel(b, cid, bd)], ptr)


def edit_dict(b, cid, bd, ptr, fn):
    """Mutate the dict at `ptr` through fn(dict). (stubs.set_pointer would treat digit-only keys as list indexes.)"""
    d = copy.deepcopy(getv(b, cid, bd, ptr))
    fn(d)
    setv(b, cid, bd, ptr, d)


def delv(b, cid, bd, ptr):
    cur = b.raw[rawrel(b, cid, bd)]
    segs = [s.replace("~1", "/").replace("~0", "~") for s in ptr[1:].split("/")]
    for s in segs[:-1]:
        cur = cur[int(s)] if isinstance(cur, list) else cur[s]
    if isinstance(cur, list):
        del cur[int(segs[-1])]
    else:
        del cur[segs[-1]]


def to_raised(b, cid, bd, exc_type="builtins.RuntimeError", msg="boom"):
    br = b.cases[cid]["boundaries"][bd]
    new = br["raw"].replace(".raw.", ".exc.")
    b.raw[new] = {"type": exc_type, "message": msg}
    del br["raw"]
    br.update(outcome="raised", exception_raw=new)


def to_returned(b, cid, bd):
    br = b.cases[cid]["boundaries"][bd]
    new = br["exception_raw"].replace(".exc.", ".raw.")
    b.raw[new] = {}
    del br["exception_raw"]
    br.update(outcome="returned", raw=new)


def rename_raw(b, old, new):
    b.raw[new] = b.raw.pop(old)
    for c in b.cases.values():
        for br in c["boundaries"].values():
            for k in ("raw", "exception_raw"):
                if br.get(k) == old:
                    br[k] = new
            for k, v in list(br.get("inputs", {}).items()):
                if v == old:
                    br["inputs"][k] = new


def flip(s):
    return (s[:-1] + ("#" if s[-1] != "#" else "$")) if s else "#"


def wrong(v):
    if v is None:
        return "x"
    if isinstance(v, bool):
        return not v
    if isinstance(v, int):
        return v + 1
    if isinstance(v, float):
        return v + 1.0
    if isinstance(v, str):
        return v + "x"
    if isinstance(v, list):
        return v + ["x"]
    if isinstance(v, dict):
        return {**v, "zz_extra": 1}
    raise TypeError(type(v))


def leaf_mut(v):
    if isinstance(v, dict) and v:
        out = copy.deepcopy(v)
        k = next(iter(out))
        out[k] = leaf_mut(out[k])
        return out
    if isinstance(v, list) and v:
        out = copy.deepcopy(v)
        out[0] = leaf_mut(out[0])
        return out
    return wrong(v)


def exc_boundary(cid):
    return next(o["boundary"] for o in CASES[cid]["observations"] if o["op"].startswith("raised_"))


# --------------------------------------------------------------------------- (a) per-observation variants
def obs_variants(g: Bundle, case, ob):
    """[(variant_name, Bundle, wanted_obs_status)] -- each a wrong-value variant of the golden bundle for ONE observation."""
    cid, bd, op = case["id"], ob["boundary"], ob["op"]
    ptr, exp = ob.get("pointer"), ob.get("expected")
    out = []

    def mk(name, fn, want="violated"):
        b = g.clone()
        fn(b)
        out.append((name, b, want))

    def tv(name, val, want="violated"):
        mk(name, lambda b: setv(b, cid, bd, ptr, copy.deepcopy(val)), want)

    br = g.cases[cid]["boundaries"][bd]
    if op.startswith("raised_"):
        rel = br["exception_raw"]
        def field(f, fn):
            def run(b):
                b.raw[rel][f] = fn(b.raw[rel][f])
            return run
        if op == "raised_type":
            mk("type_suffix", field("type", lambda t: t + "x"))
            mk("type_other", field("type", lambda t: "builtins.RuntimeError"))
        else:
            mk("msg_onechar", field("message", flip))
            mk("msg_truncated", field("message", lambda m: m[:-1]))
            if op == "raised_message_equals":
                mk("msg_suffix", field("message", lambda m: m + "x"))
                mk("msg_prefix", field("message", lambda m: "x" + m))
        mk("returns_instead_of_raising", lambda b: to_returned(b, cid, bd))
        return out
    mk("raises_instead_of_returning", lambda b: to_raised(b, cid, bd))
    if op == "returned":
        return out
    cur = resolve(g.raw[br["raw"]], ptr) if op not in P.RELATION_OPS or not ptr.startswith("#") else None
    if op in P.COMMIT_OPS:
        tv("commitment_changed", wrong(cur))
        tv("commitment_onechar", flip(cur))
        tv("driver_lies_zero_commitment", "sha256:" + "0" * 64)
        tv("commitment_non_str", 5)
        src = resolve(g.raw[br["raw"]], exp)
        mk("source_changed", lambda b: setv(b, cid, bd, exp, leaf_mut(src)))
        mk("source_nulled", lambda b: setv(b, cid, bd, exp, None))
        mk("source_removed", lambda b: delv(b, cid, bd, exp), "unevaluable")
        return out
    if op in P.RELATION_OPS:
        if ptr.startswith("#input:"):
            name = ptr[len("#input:"):]
            cur_ref = br["inputs"][name]
            other = br["raw"] if br["raw"] != cur_ref else next(r for r in g.raw if r != cur_ref)
            if op == "eq_ref":
                mk("input_redirected", lambda b: b.cases[cid]["boundaries"][bd]["inputs"].__setitem__(name, other))
            else:
                tgt = g.cases[cid]["boundaries"][exp["boundary"]]["raw"]
                mk("input_equalised", lambda b: b.cases[cid]["boundaries"][bd]["inputs"].__setitem__(name, tgt))
            mk("input_not_recorded", lambda b: b.cases[cid]["boundaries"][bd]["inputs"].pop(name), "unevaluable")
            mk("input_unindexed", lambda b: b.cases[cid]["boundaries"][bd]["inputs"].__setitem__(name, "raw/not-in-index.json"), "unevaluable")
            return out
        tb = g.cases[cid]["boundaries"][exp["boundary"]]
        right = resolve(g.raw[tb["raw"]], exp["pointer"])
        if op == "eq_ref":
            tv("left_changed", wrong(cur))
            if isinstance(cur, str):
                tv("left_onechar", flip(cur))
            if ptr != "":
                mk("left_removed", lambda b: delv(b, cid, bd, ptr), "unevaluable")
            mk("right_changed", lambda b: setv(b, cid, exp["boundary"], exp["pointer"], wrong(right)))
        else:
            tv("left_equalised", right)
        return out
    if op == "eq":
        tv("wrong_value", wrong(cur))
        if isinstance(cur, bool):
            tv("bool_as_int", int(cur))
            tv("bool_as_null", None)
        elif isinstance(cur, int):
            tv("int_as_float", float(cur))
        elif isinstance(cur, str):
            tv("onechar", flip(cur))
        elif isinstance(cur, dict) and cur:
            tv("key_dropped", dict(list(cur.items())[1:]))
            tv("leaf_changed", leaf_mut(cur))
        elif isinstance(cur, list) and cur:
            tv("item_dropped", cur[:-1])
    elif op == "ne":
        tv("equalised", exp)
    elif op == "int_eq":
        tv("plus1", cur + 1)
        tv("float", float(cur))
        tv("str", str(cur))
        tv("null", None)
        if cur in (0, 1):
            tv("bool", bool(cur))
    elif op == "is_null":
        tv("non_null", "x")
        tv("empty_str", "")
    elif op == "not_null":
        tv("null", None)
    elif op == "set_eq":
        tv("extra", cur + ["zz"])
        if cur:
            tv("missing", cur[:-1])
            tv("duplicate", cur + [cur[0]])
    elif op == "seq_eq":
        tv("extra", cur + ["x"])
        if cur:
            tv("dropped", cur[:-1])
        if len(cur) > 1 and cur[::-1] != cur:
            tv("reordered", cur[::-1])
    elif op == "len_eq":
        tv("plus1", cur + ["x"])
        if cur:
            tv("minus1", cur[:-1])
        tv("scalar", len(cur))
    elif op == "in":
        tv("not_member", wrong(cur))
    elif op == "sha256_format":
        tv("short", "sha256:" + "a" * 63)
        tv("upper", "sha256:" + "A" * 64)
        tv("no_prefix", "a" * 64)
        tv("non_str", 12345)
    elif op == "contains_substr":
        tv("missing", flip(exp))
        tv("non_str", 1)
    elif op == "list_contains":
        tv("removed", [])
        tv("wrong_item", [wrong(exp)])
        tv("not_list", "x")
    elif op == "any_item_matches":
        rest = [x for x in cur if not P.subset(exp, x)] or [{"code": "OTHER"}]
        tv("matching_item_removed", rest)
        tv("partial_item", rest + [leaf_mut(exp)])
        tv("not_list", {})
    elif op == "none_item_matches":
        tv("forbidden_added", list(cur) + [copy.deepcopy(exp)])
        tv("not_list", "x")
    elif op == "present":
        mk("removed", lambda b: delv(b, cid, bd, ptr))
    elif op == "absent":
        tv("added", "x")
    else:
        raise AssertionError(f"no wrong-value variant defined for op {op}")
    return out


def boundary_variants(g: Bundle, cid, bd):
    """[(name, Bundle, wanted_case_verdicts)] evidence-level attacks on one boundary's raw file."""
    rel = rawrel(g, cid, bd)
    out = []

    def mk(name, fn, want):
        b = g.clone()
        fn(b)
        out.append((name, b, want))
    mk("raw_file_missing", lambda b: b.drop_files.add(rel), (INCONC,))
    mk("raw_hash_lie", lambda b: b.index_over.__setitem__(rel, sha(b"lie")), (FAIL,))
    mk("raw_not_json", lambda b: b.raw_bytes.__setitem__(rel, b"<html>not json"), (INCONC,))
    mk("raw_empty", lambda b: b.raw_bytes.__setitem__(rel, b""), (INCONC,))
    mk("raw_duplicate_key", lambda b: b.raw_bytes.__setitem__(rel, b'{"a":1,"a":2}'), (INCONC,))
    mk("raw_index_entry_removed", lambda b: b.index_drop.add(rel), (INCONC,))
    mk("raw_index_entry_not_str", lambda b: b.index_over.__setitem__(rel, 7), (INCONC,))
    mk("boundary_not_observed", lambda b: b.cases[cid]["boundaries"].pop(bd), (INCONC,))
    return out


def case_variants(g: Bundle, cid):
    out = []

    def mk(name, fn, want):
        b = g.clone()
        fn(b)
        out.append((name, b, want))
    mk("executed_false", lambda b: b.cases[cid].__setitem__("executed", False), (NOT_RUN,))
    mk("executed_truthy_int", lambda b: b.cases[cid].__setitem__("executed", 1), (NOT_RUN,))
    mk("executed_string", lambda b: b.cases[cid].__setitem__("executed", "true"), (NOT_RUN,))
    mk("executed_missing", lambda b: b.cases[cid].pop("executed"), (NOT_RUN,))
    mk("case_dropped", lambda b: b.cases.pop(cid), (NOT_RUN,))
    mk("case_is_list", lambda b: b.cases.__setitem__(cid, []), (NOT_RUN,))
    mk("boundaries_not_dict", lambda b: b.cases[cid].__setitem__("boundaries", []), (INCONC,))
    return out


def run_case_matrix(R: Runner, cid):
    """{obs_id: {killed, verdict, variants}, '__boundaries__': ..., '__case__': ...} for one mandatory case."""
    g, case = gold(), CASES[cid]
    res = {}
    for ob in case["observations"]:
        vs = {}
        for name, b, want in obs_variants(g, case, ob):
            r = R.run(b)
            c, o = case_of(r, cid), obs_of(r, cid, ob["id"])
            cv = c["verdict"] if c else None
            ostat = o["status"] if o else None
            ok_case = cv == FAIL if want == "violated" else cv in (INCONC, FAIL)
            ok = bool(ok_case and ostat == want and r["overall"] != PASS)
            vs[name] = {"killed": ok, "case_verdict": cv, "obs_status": ostat, "overall": r["overall"], "wanted": want}
        res[ob["id"]] = {"killed": all(v["killed"] for v in vs.values()) and bool(vs),
                         "verdict": FAIL if all(v["case_verdict"] == FAIL for v in vs.values() if v["wanted"] == "violated") else "MIXED",
                         "variants": vs}
    bnd = {}
    for bd in g.cases[cid]["boundaries"]:
        vs = {}
        for name, b, want in boundary_variants(g, cid, bd):
            r = R.run(b)
            cv = (case_of(r, cid) or {}).get("verdict")
            vs[name] = {"killed": cv in want and r["overall"] != PASS, "case_verdict": cv, "wanted": list(want), "overall": r["overall"]}
        bnd[bd] = {"killed": all(v["killed"] for v in vs.values()), "variants": vs}
    cs = {}
    for name, b, want in case_variants(g, cid):
        r = R.run(b)
        cv = (case_of(r, cid) or {}).get("verdict")
        cs[name] = {"killed": cv in want and r["overall"] != PASS, "case_verdict": cv, "wanted": list(want), "overall": r["overall"]}
    return {"observations": res, "boundaries": bnd, "case_level": cs}


def kill_matrix(base=None):
    with contextlib.ExitStack() as st:
        base = Path(base) if base else Path(st.enter_context(tempfile.TemporaryDirectory()))
        R = Runner(base / "km")
        return {cid: run_case_matrix(R, cid) for cid in MAND}


def matrix_counts(km):
    n = k = vn = vk = 0
    for cid, m in km.items():
        for oid, o in m["observations"].items():
            n += 1
            k += bool(o["killed"])
            for v in o["variants"].values():
                vn += 1
                vk += bool(v["killed"])
        for grp in ("boundaries", "case_level"):
            for o in m[grp].values():
                for v in (o["variants"].values() if grp == "boundaries" else [o]):
                    vn += 1
                    vk += bool(v["killed"])
    return {"observations_total": n, "observations_killed": k, "variants_total": vn, "variants_killed": vk}


# --------------------------------------------------------------------------- (b) weakened oracle variants (RI cases)
def _structural(name):
    return "raises" in name or "returns" in name


def _wrong_for(g, case, ob):
    for name, b, want in obs_variants(g, case, ob):
        if want == "violated" and not _structural(name):
            return name, b
    return None, None


def _loosen(ob):
    ob = copy.deepcopy(ob)
    if ob["op"] in ("raised_message_equals", "raised_message_contains"):
        ob["op"], ob["expected"] = "raised_message_contains", ob["expected"][:1]
    elif ob["op"].startswith("raised_"):
        return None
    else:
        ob["op"] = "present"
        ob.pop("expected", None)
    return ob


def weakened_oracle_variants():
    """Yield dicts describing (variant oracle, wrong-value bundle)."""
    g = gold()
    for case in ORC["cases"]:
        if case["class"] != "RI":
            continue
        cid, obs = case["id"], case["observations"]
        plans = []
        for i, ob in enumerate(obs):
            wname, wb = _wrong_for(g, case, ob)
            if wb is None:
                continue
            if len(obs) > 1:
                plans.append((f"drop:{ob['id']}", [o for j, o in enumerate(obs) if j != i], wname, wb))
            lo = _loosen(ob)
            if lo is not None:
                plans.append((f"loosen:{ob['id']}", [lo if j == i else o for j, o in enumerate(obs)], wname, wb))
        if len(obs) > 1:
            wname, wb = _wrong_for(g, case, obs[-1])
            plans.append(("keep_only_first", [obs[0]], wname, wb))
        for name, new_obs, wname, wb in plans:
            v = copy.deepcopy(ORC)
            next(c for c in v["cases"] if c["id"] == cid)["observations"] = new_obs
            yield {"case": cid, "variant": name, "oracle": v, "wrong_variant": wname, "wrong_bundle": wb}


def run_weakened(R: Runner, spec):
    vbytes = (json.dumps(spec["oracle"], sort_keys=True, indent=1) + "\n").encode()
    assert not O.validate(spec["oracle"]), O.validate(spec["oracle"])
    cid = spec["case"]
    real = R.run(spec["wrong_bundle"])
    var = R.run(spec["wrong_bundle"], oracle_bytes=vbytes, oracle_sha=sha(vbytes))
    pinned = R.run(spec["wrong_bundle"], oracle_bytes=vbytes)
    rv, vv = case_of(real, cid)["verdict"], case_of(var, cid)["verdict"]
    rejected = (pinned["overall"] == NOT_RUN and (pinned.get("blocked_reason") or "").startswith("ORACLE_DRIFT")
                and all(c["verdict"] == NOT_RUN for c in pinned["cases"] if c["mandatory"]))
    distinguishable = rv == FAIL and vv != FAIL
    return {"case": cid, "variant": spec["variant"], "wrong_value_variant": spec["wrong_variant"], "real_oracle_verdict": rv,
            "weakened_oracle_verdict": vv, "weakened_overall": var["overall"], "rejected_by_pinned_hash": rejected,
            "distinguishable": distinguishable, "killed": bool(rejected and distinguishable)}


# --------------------------------------------------------------------------- attacks (EST library)
ATTACKS = {}


def attack(name, est, expect, claim_may_pass=False):
    """claim_may_pass: OBS-only deviations FAIL `overall` but, by design, never touch the claim basis (claim_gated False)."""
    def deco(fn):
        ATTACKS[name] = {"est": est, "expect": tuple(expect), "fn": fn, "claim_may_pass": claim_may_pass}
        return fn
    return deco


def _run(R, mutate, **kw):
    b = G()
    mutate(b)
    return R.run(b, **kw)


attack("golden", "BASE", (PASS,))(lambda R: R.run(G()))


def _est01(b):
    setv(b, "QA-01", "cp_record", "/decisions/0/result", "denied")
    setv(b, "QA-01", "pack", "/metadata/traceable_import/derived_counts/destination_effect_count", 1)
    b.orch.update({"all_ok": True, "chain_verdict": "ACCEPTED"})


attack("est01_false_success_summary", "EST-01", (FAIL,))(lambda R: _run(R, _est01))
attack("est02_hold_to_authorized", "EST-02", (FAIL,))(
    lambda R: _run(R, lambda b: setv(b, "QA-02", "cp_record", "/decisions/0/result", "authorized")))
_CNT = "/metadata/traceable_import/derived_counts/"
PACK_COUNTS = ["control_plane_attempt_count", "executor_attempt_count", "attempt_transition_record_count",
               "destination_effect_count", "effect_observation_count", "reconciliation_count"]
for _lbl, _val in (("bool", False), ("str", "0"), ("float", 0.0), ("null", None)):
    attack(f"est03_counter_{_lbl}", "EST-03", (FAIL,))(
        lambda R, v=_val: _run(R, lambda b: setv(b, "QA-01", "pack", _CNT + "control_plane_attempt_count", v)))


def _est04(b):
    setv(b, "QA-02", "replay_bundle", "/records", [{"record_type": "note", "data": {}}])
    setv(b, "QA-02", "replay_bundle", "/retains_upstream_refusal", True)
    b.cases["QA-02"]["retains_upstream_refusal"] = True
    b.orch["retains_upstream_refusal"] = True


attack("est04_downstream_refusal_dropped", "EST-04", (FAIL,))(lambda R: _run(R, _est04))
for _cid in ("QA-03", "QA-05", "QA-12", "QA-25"):
    attack(f"est05_message_onechar_{_cid}", "EST-05", (FAIL,))(
        lambda R, c=_cid: _run(R, lambda b: b.raw[rawrel(b, c, exc_boundary(c))].__setitem__(
            "message", flip(b.raw[rawrel(b, c, exc_boundary(c))]["message"]))))
attack("est05_equals_message_suffix_QA-05", "EST-05", (FAIL,))(
    lambda R: _run(R, lambda b: b.raw[rawrel(b, "QA-05", "pack_import")].__setitem__(
        "message", b.raw[rawrel(b, "QA-05", "pack_import")]["message"] + " (extra)")))
attack("est05_type_changed_QA-19", "EST-05", (FAIL,))(
    lambda R: _run(R, lambda b: b.raw[rawrel(b, "QA-19", "am_load")].__setitem__("type", "builtins.FileNotFoundError")))


def _swap_cases(b):
    b.cases["QA-03"], b.cases["QA-05"] = b.cases["QA-05"], b.cases["QA-03"]


def _dup_key_bundle(b):
    bb = b.render()[1].decode().rstrip()
    b.bundle_bytes = (bb[:-1] + ', "schema": "ia-observation-bundle/1"}\n').encode()


attack("est06_case_swap", "EST-06", (FAIL,))(lambda R: _run(R, _swap_cases))
attack("est06_dropped_case", "EST-06", (NOT_RUN,))(lambda R: _run(R, lambda b: b.cases.pop("QA-12")))
attack("est06_zero_cases", "EST-06", (NOT_RUN,))(lambda R: _run(R, lambda b: b.cases.clear()))
attack("est06_unknown_case_id", "EST-06", (FAIL,))(
    lambda R: _run(R, lambda b: b.cases.__setitem__("QA-99", copy.deepcopy(b.cases["QA-S1"]))))
attack("est06_duplicate_json_key_bundle", "EST-06", (NOT_RUN,))(lambda R: _run(R, _dup_key_bundle))

_A, _B = "raw/QA-01.cp_record.raw.json", "raw/QA-01.pack.raw.json"
attack("est07_raw_hash_lie", "EST-07", (FAIL,))(lambda R: _run(R, lambda b: b.index_over.__setitem__(_A, "0" * 64)))
attack("est07_cross_artifact_hash", "EST-07", (FAIL,))(
    lambda R: _run(R, lambda b: b.index_over.__setitem__(_A, sha(ser(b.raw[_B])))))
attack("est07_missing_raw_file", "EST-07", (INCONC,))(lambda R: _run(R, lambda b: b.drop_files.add(_A)))
attack("est07_non_json_raw", "EST-07", (INCONC,))(lambda R: _run(R, lambda b: b.raw_bytes.__setitem__(_A, b"<html>nope")))


def _flip_oracle_byte():
    i = ORC_BYTES.index(b"draft")
    return ORC_BYTES[:i] + b"dra_t" + ORC_BYTES[i + 5:]


attack("est08_oracle_one_byte", "EST-08", (NOT_RUN,))(lambda R: R.run(G(), oracle_bytes=_flip_oracle_byte()))
attack("est08_oracle_not_json", "EST-08", (NOT_RUN,))(
    lambda R: R.run(G(), oracle_bytes=b"not json", oracle_sha=sha(b"not json")))
attack("est08_freeze_drift", "EST-08", (NOT_RUN,))(lambda R: R.run(G(), extra_block="FREEZE_DRIFT: changed file ia_eval/engine.py"))
attack("est08_bundle_hash_mismatch", "EST-08", (NOT_RUN,))(lambda R: R.run(G(), bundle_sha="0" * 64))
attack("est11_obs_deviation", "EST-11", (FAIL,), True)(
    lambda R: _run(R, lambda b: setv(b, "QA-11", "replay_bundle", "/status", "reconstruction_complete")))
for _cid in ("QA-03", "QA-05", "QA-10", "QA-12", "QA-18", "QA-19", "QA-22", "QA-25"):
    attack(f"est12_returns_instead_of_refusing_{_cid}", "EST-12", (FAIL,))(
        lambda R, c=_cid: _run(R, lambda b: to_returned(b, c, exc_boundary(c))))
attack("est12_raises_where_return_required_QA-11", "EST-12", (FAIL,), True)(
    lambda R: _run(R, lambda b: to_raised(b, "QA-11", "replay_import")))
attack("est12_raises_cp_record_QA-01", "EST-12", (FAIL,))(lambda R: _run(R, lambda b: to_raised(b, "QA-01", "cp_record")))
attack("arch_binding_removed", "ARCH", (INCONC,))(lambda R: _run(R, lambda b: delv(b, "QA-01", "cp_record", "/decisions/0/binding")))
attack("arch_binding_null", "ARCH", (FAIL,))(lambda R: _run(R, lambda b: setv(b, "QA-01", "cp_record", "/decisions/0/binding", None)))
for _n in PACK_COUNTS:
    attack(f"arch_pack_count_nonzero_{_n}", "ARCH", (FAIL,))(lambda R, n=_n: _run(R, lambda b: setv(b, "QA-01", "pack", _CNT + n, 1)))
for _n in ("attempts", "observations", "reconciliations"):
    attack(f"arch_cp_{_n}_nonzero", "ARCH", (FAIL,))(lambda R, n=_n: _run(R, lambda b: setv(b, "QA-01", "cp_record", "/" + n, [{"x": 1}])))
attack("arch_skipped_case", "ARCH", (NOT_RUN,))(lambda R: _run(R, lambda b: b.cases["QA-08"].__setitem__("executed", False)))
attack("arch_executed_truthy", "ARCH", (NOT_RUN,))(lambda R: _run(R, lambda b: b.cases["QA-08"].__setitem__("executed", 1)))
attack("arch_source_commit_altered_QA-S1", "ARCH", (FAIL,))(
    lambda R: _run(R, lambda b: setv(b, "QA-S1", "source_identity", "/commits/action_manifest",
                                     flip(getv(b, "QA-S1", "source_identity", "/commits/action_manifest")))))
_FIX = "am:examples/refund_integration_v1_1.manifest.json"
attack("arch_fixture_hash_altered_QA-S2", "ARCH", (FAIL,))(
    lambda R: _run(R, lambda b: edit_dict(b, "QA-S2", "file_identity", "/sha256", lambda d: d.__setitem__(_FIX, flip(d[_FIX])))))
attack("arch_raw_index_not_dict", "ARCH", (NOT_RUN,))(lambda R: _run(R, lambda b: b.edit.append(lambda d: d.__setitem__("raw_index", []))))
attack("arch_raw_index_entry_removed", "ARCH", (INCONC,))(lambda R: _run(R, lambda b: b.index_drop.add(_A)))
attack("arch_raw_index_entry_int", "ARCH", (INCONC,))(lambda R: _run(R, lambda b: b.index_over.__setitem__(_A, 7)))
attack("arch_h1_h2_confusion", "ARCH", (FAIL,))(
    lambda R: _run(R, lambda b: b.cases["QA-01"]["boundaries"]["pack"]["inputs"].__setitem__("replay_bundle", rawrel(b, "QA-01", "pack"))))
attack("arch_h1_h2_swapped_inputs", "ARCH", (FAIL,))(
    lambda R: _run(R, lambda b: (b.cases["QA-01"]["boundaries"]["pack"]["inputs"].__setitem__("replay_bundle", rawrel(b, "QA-01", "cp_record")),
                                 b.cases["QA-01"]["boundaries"]["replay_bundle"]["inputs"].__setitem__("cp_record", rawrel(b, "QA-01", "replay_bundle")))))
attack("arch_pair_swapped_cp_records", "ARCH", (FAIL,))(
    lambda R: _run(R, lambda b: (lambda a, c: (b.raw.__setitem__(a, b.raw[c]), b.raw.__setitem__(c, copy.deepcopy(gold().raw[a]))))(
        "raw/QA-01.cp_record.raw.json", "raw/QA-02.cp_record.raw.json")))
attack("label_lie_returned_but_raised", "OUTCOME", (INCONC,))(
    lambda R: _run(R, lambda b: b.cases["QA-03"]["boundaries"]["pack_import"].__setitem__("outcome", "returned")))
attack("label_lie_raised_with_both", "OUTCOME", (INCONC,))(
    lambda R: _run(R, lambda b: b.cases["QA-03"]["boundaries"]["pack_import"].__setitem__("raw", rawrel(b, "QA-S1", "source_identity"))))
attack("bool_as_int_valid", "EST-03", (FAIL,))(lambda R: _run(R, lambda b: setv(b, "QA-01", "am_validate", "/valid", 1)))
attack("false_as_zero_semantics", "EST-03", (FAIL,))(
    lambda R: _run(R, lambda b: setv(b, "QA-01", "replay_bundle", "/semantics/external_effect_execution", 0)))
attack("weak_sha_format", "EST-03", (FAIL,))(lambda R: _run(R, lambda b: setv(b, "QA-01", "cp_record", "/decisions/0/effect_id", "abc")))
attack("missing_pointer_is_not_null", "EST-03", (INCONC,))(lambda R: _run(R, lambda b: delv(b, "QA-02", "cp_record", "/decisions/0/binding")))
attack("break_QA-01_control", "PAIRED", (FAIL,))(lambda R: _run(R, lambda b: setv(b, "QA-01", "cp_record", "/decisions/0/result", "hold")))

_EVT = "agent_control_plane.bounded.BoundedAuthorizationWorkflow"
for _lbl, _ev in (
    ("effect_named_execute", {"kind": "native_call", "callable": _EVT + ".execute"}),
    ("effect_named_reconcile", {"kind": "native_call", "callable": _EVT + ".reconcile"}),
    ("unlisted_benign_name", {"kind": "native_call", "callable": _EVT + ".decide_again"}),
    ("kind_network", {"kind": "network", "host": "example.invalid"}),
    ("kind_subprocess", {"kind": "subprocess", "argv": ["true"]}),
    ("scratch_traversal", {"kind": "scratch_write", "path": "scratch/../../x"}),
    ("scratch_absolute", {"kind": "scratch_write", "path": "/etc/x"}),
    ("scratch_backslash", {"kind": "scratch_write", "path": "scratch\\x"}),
    ("scratch_nul", {"kind": "scratch_write", "path": "scratch/a\0b"}),
    ("event_not_dict", "native_call"),
):
    attack(f"guard_{_lbl}", "GUARD", (FAIL,))(lambda R, e=_ev: _run(R, lambda b: b.driver_events.append(e)))
attack("guard_events_key_absent", "GUARD", (FAIL,))(lambda R: _run(R, lambda b: b.edit.append(lambda d: d.pop("driver_events"))))
attack("guard_events_null", "GUARD", (FAIL,))(lambda R: _run(R, lambda b: setattr(b, "driver_events", None)))


def _oracle_invalid(R):
    v = copy.deepcopy(ORC)
    del v["cases"][0]["observations"][0]["pointer"]
    vb = (json.dumps(v, sort_keys=True, indent=1) + "\n").encode()
    return R.run(G(), oracle_bytes=vb, oracle_sha=sha(vb))


attack("oracle_invalid_pinned", "EST-08", (NOT_RUN,))(_oracle_invalid)


def _symlink_dir(R):
    import os
    R2 = R.fresh()
    r0 = R2.run(G())
    assert r0["overall"] == PASS
    ext = R2.base.parent / (R2.base.name + "_ext")
    (R2.base / "raw").rename(ext)
    os.symlink(ext, R2.base / "raw")
    return engine.run(ORC_BYTES, R2.base, ORC_SHA, sha((R2.base / "bundle.json").read_bytes()))


def _symlink_file(R):
    import os
    R2 = R.fresh()
    R2.run(G())
    f = R2.base / _A
    (R2.base / "copy.json").write_bytes(f.read_bytes())
    f.unlink()
    os.symlink(R2.base / "copy.json", f)
    return engine.run(ORC_BYTES, R2.base, ORC_SHA, sha((R2.base / "bundle.json").read_bytes()))


def _backslash_name(R):
    b = G()
    rename_raw(b, _A, "raw\\QA-01.cp_record.json")
    return R.run(b)


def _absolute_name(R):
    b = G()
    rename_raw(b, _A, str(R.base.resolve() / "abs_cp_record.json"))
    return R.run(b)


attack("path_symlinked_directory", "SEC", (INCONC,))(_symlink_dir)
attack("path_symlinked_file", "SEC", (INCONC,))(_symlink_file)
attack("path_backslash_name", "SEC", (INCONC,))(_backslash_name)
attack("path_absolute_name", "SEC", (INCONC,))(_absolute_name)


def _qa26_alias(b):
    br = b.cases["QA-26"]["boundaries"]
    br["pack_second"]["raw"] = br["pack_first"]["raw"]


attack("qa26_two_boundaries_alias_one_raw_file", "ALIAS", (INCONC,), True)(lambda R: _run(R, _qa26_alias))
attack("qa09_driver_lies_about_raw_commitment", "COMMIT", (FAIL,), True)(
    lambda R: _run(R, lambda b: setv(b, "QA-09", "digest_full", "/raw_commitment", "sha256:" + "0" * 64)))
attack("qa09_manifest_changed_commitment_stale", "COMMIT", (FAIL,), True)(
    lambda R: _run(R, lambda b: setv(b, "QA-09", "digest_reduced", "/manifest", {"changed": True})))
attack("qa09_manifest_null_blocks_pointer", "COMMIT", (FAIL,), True)(
    lambda R: _run(R, lambda b: setv(b, "QA-09", "digest_full", "/manifest", None)))


def scenarios():
    """[(name, fn(R)->report)] used for engine-mutant kill detection: attacks first, then per-op wrong-value sweeps."""
    out = [(n, a["fn"]) for n, a in ATTACKS.items()]
    out += [(n, (lambda R, b=b: R.run(b))) for n, b in sweep_bundles()]
    return out


_SWEEP = None


def sweep_bundles():
    global _SWEEP
    if _SWEEP is None:
        seen, out = {}, []
        for c in ORC["cases"]:
            if not c["mandatory"]:
                continue
            for ob in c["observations"]:
                if seen.get(ob["op"], 0) >= 2:
                    continue
                seen[ob["op"]] = seen.get(ob["op"], 0) + 1
                for vn, b, _want in obs_variants(gold(), c, ob):
                    out.append((f"sweep:{ob['id']}:{vn}", b))
        _SWEEP = out
    return _SWEEP


def est_results(R: Runner):
    rows = []
    for name, a in ATTACKS.items():
        if name == "golden":
            continue
        r = a["fn"](R)
        rows.append({"attack": name, "est": a["est"], "expected_overall": list(a["expect"]), "overall": r["overall"],
                     "claim_basis": r["claim_basis"], "blocked_reason": (r.get("blocked_reason") or "")[:80],
                     "defended": r["overall"] != PASS and (a["claim_may_pass"] or r["claim_basis"] != PASS),
                     "as_expected": r["overall"] in a["expect"] and (a["claim_may_pass"] or not_pass(r))})
    return rows


# --------------------------------------------------------------------------- engine mutants
def src_patch(owner, name, old, new):
    fn = getattr(owner, name)
    mod = sys.modules[fn.__module__]
    src = textwrap.dedent(inspect.getsource(fn))
    if src.count(old) != 1:
        raise AssertionError(f"mutation anchor not unique in {name}: {old!r} x{src.count(old)}")
    ns = {}
    exec(compile(src.replace(old, new), f"<mutant:{name}>", "exec"), mod.__dict__, ns)   # noqa: S102 - test-only source mutation
    return ("attr", owner, name, ns[name])


@contextlib.contextmanager
def patched(patches):
    saved = []
    try:
        for kind, owner, name, val in patches:
            old = getattr(owner, name) if kind == "attr" else owner[name]
            saved.append((kind, owner, name, old))
            if kind == "attr":
                setattr(owner, name, val)
            else:
                owner[name] = val
        yield
    finally:
        for kind, owner, name, old in reversed(saved):
            if kind == "attr":
                setattr(owner, name, old)
            else:
                owner[name] = old


def _combine_variant(drop=(), empty=NOT_RUN, order=(FAIL, INCONC, NOT_RUN)):
    def combine(verdicts):
        vs = list(verdicts)
        if not vs:
            return empty
        for bad in order:
            if bad in vs and bad not in drop:
                return bad
        return PASS if all(v == PASS or v in drop for v in vs) else INCONC
    return combine


def _resolve_none(doc, ptr):
    r = resolve(doc, ptr)
    return None if is_missing(r) else r


def _always_true(*_a, **_k):
    return True, "mutant: always holds"


def _deq_type_loose(a, b):
    return a == b


def _deq_extra_keys(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return all(k in a and _deq_extra_keys(a[k], v) for k, v in b.items())
    if isinstance(a, list):
        return len(a) >= len(b) and all(_deq_extra_keys(x, y) for x, y in zip(a, b))
    return a == b


def _as_item(op, patch):
    """VALUE_OPS captured the original function objects, so an op mutant must replace the dict entry."""
    return ("item", P.VALUE_OPS, op, patch[3])


def _mutants():
    E, Rw = engine, engine._Raw
    sp = src_patch
    used_ops = sorted({ob["op"] for c in ORC["cases"] if c["mandatory"] for ob in c.get("observations", [])} & set(P.VALUE_OPS))
    L = []

    def m(mid, desc, patches, equivalent=None):
        L.append({"id": mid, "desc": desc, "patches": patches, "equivalent": equivalent})
    m("M01_oracle_validation_skipped", "oracle shape errors ignored", lambda: [sp(E, "_run", "if errs:", "if False:")])
    m("M02_oracle_pin_ignored", "ORACLE_DRIFT check removed", lambda: [sp(
        E, "_run", "if not isinstance(expect_oracle_sha256, str) or O.sha256_bytes(oracle_bytes) != expect_oracle_sha256:", "if False:")])
    m("M03_extra_block_ignored", "freeze drift block ignored", lambda: [sp(E, "_run", "if extra_block:", "if False:")])
    m("M04_bundle_pin_ignored", "BUNDLE_DRIFT check removed", lambda: [sp(
        E, "_run", "if not isinstance(expect_bundle_sha256, str) or O.sha256_bytes(bdata) != expect_bundle_sha256:", "if False:")])
    m("M05_unknown_case_ids_ignored", "extra case ids not a violation", lambda: [sp(E, "_run", "if unknown:", "if False:")])
    m("M06_violations_ignored", "guard violations not applied", lambda: [sp(E, "_run", "if violations:", "if False:")])
    m("M07_claim_basis_ignores_violations", "violations only downgrade overall", lambda: [sp(
        E, "_run", "overall, gated = V.FAIL, V.FAIL", "overall = V.FAIL")])
    m("M08_paired_control_downgrade_removed", "refusal case may PASS with a broken control", lambda: [sp(
        E, "_run", 'if pc and x["verdict"] == V.PASS and by_id[pc]["verdict"] != V.PASS:', "if False:")])
    m("M09_zero_executed_rule_removed", "zero-executed PASS rescue removed", lambda: [sp(
        E, "_run", "if not executed_mand and overall == V.PASS:", "if False:")],
      equivalent="unreachable on its own: combine() already maps all-NOT_RUN to NOT RUN (see M09b for the compound)")
    m("M09b_notrun_ignored_and_zero_rule_removed", "combine ignores NOT RUN and the zero-executed rule is gone", lambda: [
        sp(E, "_run", "if not executed_mand and overall == V.PASS:", "if False:"), ("attr", V, "combine", _combine_variant(drop=(NOT_RUN,)))])
    m("M10_executed_flag_not_checked", "executed:false still evaluated", lambda: [
        sp(E, "evaluate_case", 'cobs.get("executed") is not True', "False")])
    m("M11_executed_truthy_accepted", "executed:1 / 'true' accepted", lambda: [sp(
        E, "evaluate_case", 'cobs.get("executed") is not True', 'not cobs.get("executed")')])
    m("M12_unevaluable_ignored", "unevaluable observations count as PASS", lambda: [sp(
        E, "evaluate_case", 'V.INCONCLUSIVE if state["unevaluable"] else V.PASS', "V.PASS")])
    m("M13_violated_ignored", "violated observations do not FAIL", lambda: [sp(
        E, "evaluate_case", 'verdict = V.FAIL if state["violated"] else', "verdict = V.FAIL if False else")])
    m("M14_info_case_passes", "INFO cases report PASS", lambda: [sp(
        E, "evaluate_case", '"verdict": V.NOT_RUN, "executed": False, "blocked_reason": "informational', '"verdict": V.PASS, "executed": False, "blocked_reason": "informational')])
    m("M15_obs_deviation_ignored", "OBS deviations cannot fail", lambda: [sp(
        E, "evaluate_case", "if st in state:", 'if st in state and c["class"] != "OBS":')])
    m("M16_obs_marked_validated", "OBS claims security_property_validated", lambda: [sp(
        E, "evaluate_case", 'out["security_property_validated"] = False', 'out["security_property_validated"] = True')])
    m("M17_obs_claim_gated", "OBS cases claim-gated", lambda: [sp(
        E, "evaluate_case", 'out["claim_gated"] = False', 'out["claim_gated"] = True')])
    m("M18_hash_verification_disabled", "raw sha256 never compared", lambda: [sp(Rw, "_load", "if got != want:", "if False:")])
    m("M19_containment_removed", "symlinked directories / escapes readable", lambda: [sp(Rw, "_load", "real.relative_to(self.root)", "None")])
    m("M20_file_symlink_allowed", "symlinked raw files accepted", lambda: [sp(
        Rw, "_load", "if p.is_symlink() or not real.is_file():", "if not real.is_file():")])
    m("M21_backslash_path_allowed", "backslash raw paths accepted", lambda: [sp(Rw, "_load", r'or "\\" in rel or', "or")])
    m("M22_size_cap_removed_in_load", "raw size cap removed in _Raw only", lambda: [sp(
        Rw, "_load", "if len(data) > O.MAX_JSON_BYTES:", "if False:")],
      equivalent="load_json_strict enforces the same 8 MiB cap (defence in depth)")
    m("M23_tampered_is_unevaluable", "hash lie yields INCONCLUSIVE instead of FAIL", lambda: [sp(
        E, "_eval_obs", 'if kind == "tampered":\n        return "violated", val, None', 'if kind == "tampered":\n        return "unevaluable", val, None')])
    m("M24_outcome_label_trusted", "boundary outcome taken from the bundle label", lambda: [(
        "attr", E, "_outcome", lambda bres, raw: (bres.get("outcome") if bres.get("outcome") in ("returned", "raised") else None, None))])
    m("M25_outcome_consistency_removed", "label/evidence disagreement tolerated", lambda: [sp(E, "_outcome", "if label != want:", "if False:")])
    m("M26_message_equals_is_contains", "raised_message_equals degraded to contains", lambda: [sp(
        E, "_eval_obs", 'ok = exc["message"] == ob["expected"]', 'ok = ob["expected"] in exc["message"]')])
    m("M27_exception_type_substring", "exception type compared by substring", lambda: [sp(
        E, "_eval_obs", 'ok = exc["type"] == ob["expected"]', 'ok = ob["expected"] in exc["type"]')])
    m("M28_message_contains_always_ok", "raised_message_contains always holds", lambda: [sp(
        E, "_eval_obs", 'ok = ob["expected"] in exc["message"]', "ok = True")])
    m("M29_return_where_refusal_required_ok", "a returned call satisfies a refusal predicate", lambda: [sp(
        E, "_eval_obs", 'return "violated", "expected a native refusal but the call returned", None', 'return "ok", "mutant", None')])
    m("M30_raise_where_return_required_ok", "a raised call satisfies `returned`", lambda: [sp(
        E, "_eval_obs", 'return "violated", "native raised where a return was required", None', 'return "ok", "mutant", None')])
    m("M31_value_predicate_on_raise_ok", "a raised call satisfies value predicates", lambda: [sp(
        E, "_eval_obs", 'return "violated", "native raised; a value predicate cannot be satisfied", None', 'return "ok", "mutant", None')])
    m("M32_missing_pointer_defaults_none", "MISSING pointer resolves to None", lambda: [("attr", E, "resolve", _resolve_none)])
    m("M33_missing_pointer_ok", "MISSING pointer accepted", lambda: [sp(
        E, "_eval_obs", 'return "unevaluable", f"pointer {ob.get(\'pointer\')} missing (no default is assumed)", None', 'return "ok", "mutant", None')])
    m("M34_relation_target_unavailable_ok", "unavailable relation target ignored", lambda: [sp(
        E, "_eval_obs", 'if k2 != "ok" or is_missing(v2):', "if False:")])
    m("M35_relation_always_holds", "eq_ref/ne_ref always satisfied", lambda: [sp(
        E, "_eval_obs", "same = P.deq(val, v2)", 'same = (op == "eq_ref")')])
    m("M36_combine_ignores_inconclusive", "combine drops INCONCLUSIVE", lambda: [("attr", V, "combine", _combine_variant(drop=(INCONC,)))])
    m("M37_combine_empty_is_pass", "empty mandatory set is PASS", lambda: [("attr", V, "combine", _combine_variant(empty=PASS))],
      equivalent="the engine never calls combine() with an empty list (the oracle always has mandatory cases); verdicts.combine is unit-tested directly")
    m("M38_combine_ignores_not_run", "NOT RUN mandatory cases ignored", lambda: [("attr", V, "combine", _combine_variant(drop=(NOT_RUN,)))])
    m("M39_combine_inconclusive_over_fail", "INCONCLUSIVE outranks FAIL", lambda: [("attr", V, "combine", _combine_variant(order=(INCONC, FAIL, NOT_RUN)))])
    m("M40_deq_type_loose", "True == 1, 1 == 1.0", lambda: [("attr", P, "deq", _deq_type_loose)])
    m("M41_deq_extra_keys_ok", "extra dict keys / list items tolerated", lambda: [("attr", P, "deq", _deq_extra_keys)])
    m("M42_int_eq_accepts_bool_float", "int_eq accepts True/0.0", lambda: [_as_item("int_eq", sp(P, "op_int_eq", "type(obs) is not int", "not isinstance(obs, (int, float))"))])
    m("M43_sha256_format_any", "sha256_format regex matches anything", lambda: [("attr", P, "_SHA", re.compile(r".*"))])
    m("M44_subset_any_key", "dict subset requires only one key", lambda: [sp(
        P, "subset", "all(k in obs and subset(v, obs[k]) for k, v in exp.items())", "any(k in obs and subset(v, obs[k]) for k, v in exp.items())")])
    m("M45_len_eq_unchecked_type", "len_eq accepts any container length by truthiness", lambda: [_as_item("len_eq", sp(
        P, "op_len_eq", "return len(obs) == exp,", "return len(obs) >= exp,"))])
    m("N1_blocked_is_missing", "null/scalar traversal reported as missing (INCONCLUSIVE)", lambda: [sp(E, "_eval_obs", "if val is BLOCKED:", "if False:")])
    m("N2_blocked_is_ok", "null/scalar traversal satisfies value predicates", lambda: [sp(
        E, "_eval_obs", 'return "violated", f"pointer {ob.get(\'pointer\')} crosses a null or scalar: observed structure contradicts the expected one", None', 'return "ok", "mutant", None')])
    m("N3_blocked_counts_as_present", "`absent` fails / `present` passes on a BLOCKED path", lambda: [sp(
        E, "_eval_obs", "present = not is_missing(val)", "present = val is not MISSING")])
    m("N4_commitment_of_always_ok", "commitment_of always holds", lambda: [sp(
        E, "_eval_obs", "ok = isinstance(val, str) and val == commitment(other)", "ok = True")])
    m("N5_commitment_trusts_driver", "commitment compared with the observed value itself (not recomputed)", lambda: [sp(
        E, "_eval_obs", "val == commitment(other)", "val == val")])
    m("N6_commitment_source_missing_ok", "missing commitment source ignored", lambda: [sp(
        E, "_eval_obs", "if is_missing(other):", "if False:")])
    m("N7_relation_alias_rule_removed", "self-comparison via aliased raw file accepted", lambda: [sp(
        E, "_eval_obs", 'if bres.get("raw") == cb.get("raw") and ob.get("pointer") == ref2["pointer"]:', "if False:")])
    for op in used_ops:
        m(f"M46_op_always_true:{op}", f"predicate {op} always holds", (lambda op=op: [("item", P.VALUE_OPS, op, _always_true)]))
    m("G1_check_events_empty", "guard returns no violations", lambda: [("attr", guard, "check_events", lambda e, a: [])])
    m("G2_all_kinds_allowed", "network/subprocess kinds allowed", lambda: [(
        "attr", guard, "ALLOWED_KINDS", frozenset({"git_read", "file_read", "native_call", "scratch_write", "network", "subprocess"}))])
    m("G3_allow_list_not_enforced", "native_call allow-list ignored", lambda: [sp(
        guard, "check_events", "if not isinstance(name, str) or name not in allowed:", "if not isinstance(name, str):")])
    m("G4_scratch_path_unchecked", "scratch_write path never validated", lambda: [sp(
        guard, "check_events", 'if kind == "scratch_write" and not _in_scratch(e.get("path")):', "if False:")])
    m("G5_absent_events_ok", "missing driver_events treated as clean", lambda: [sp(
        guard, "check_events", "if not isinstance(events, list):", "if events is None:\n        events = []\n    if not isinstance(events, list):")])
    m("G6_scratch_traversal_allowed", "scratch/.. accepted", lambda: [(
        "attr", guard, "_in_scratch", lambda p: isinstance(p, str) and p.startswith("scratch/"))])
    m("G7_effect_regex_removed", "effect-name regex never matches", lambda: [("attr", guard, "_EFFECT_NAME", re.compile(r"(?!x)x"))],
      equivalent="the allow-list already refuses every effect-named callable the current oracle does not list (regex is defence in depth; unit-tested directly)")
    return L


MUTANTS = _mutants()


def run_mutant(mut, R: Runner, base_sigs):
    """Run scenarios under the mutant; killed = some scenario's signature differs from the correct engine's."""
    with patched(mut["patches"]()):
        for name, fn in scenarios():
            try:
                s = sig(fn(R))
            except Exception as e:   # a crash is also an observable difference
                s = ("CRASH", type(e).__name__)
            if s != base_sigs[name]:
                return {"id": mut["id"], "description": mut["desc"], "killed": True, "killed_by": name, "equivalent": mut["equivalent"]}
    return {"id": mut["id"], "description": mut["desc"], "killed": False, "killed_by": None, "equivalent": mut["equivalent"]}


def baseline_sigs(R: Runner):
    return {name: sig(fn(R)) for name, fn in scenarios()}


def engine_mutants(R: Runner, base_sigs=None):
    base_sigs = base_sigs or baseline_sigs(R)
    return [run_mutant(m, R, base_sigs) for m in MUTANTS]


# --------------------------------------------------------------------------- memoised expensive results (shared by test modules)
_MEMO = {}
_TMP = []


def memo(key, fn):
    if key not in _MEMO:
        _MEMO[key] = fn()
    return _MEMO[key]


def memo_runner():
    def mk():
        import atexit
        import shutil
        d = tempfile.mkdtemp(prefix="ia-selftest-")
        atexit.register(shutil.rmtree, d, True)
        return Runner(Path(d) / "w")
    return memo("runner", mk)


def memo_variants():
    return memo("variants", lambda: [run_weakened(memo_runner(), s) for s in weakened_oracle_variants()])


def memo_base_sigs():
    return memo("base_sigs", lambda: baseline_sigs(memo_runner()))


def memo_mutants():
    return memo("mutants", lambda: engine_mutants(memo_runner(), memo_base_sigs()))


# --------------------------------------------------------------------------- script
def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    outdir = Path(argv[0]) if argv else PKG / "results" / "selftest"
    outdir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        R = Runner(Path(td) / "w")
        km = kill_matrix(Path(td))
        est = est_results(R)
        variants = [run_weakened(R, s) for s in weakened_oracle_variants()]
        base = baseline_sigs(R)
        muts = engine_mutants(R, base)
    cnt = matrix_counts(km)
    surv_obs = [(c, o) for c, m in km.items() for o, d in m["observations"].items() if not d["killed"]]
    surv_var = [v for v in variants if not v["killed"]]
    surv_mut = [x for x in muts if not x["killed"] and not x["equivalent"]]
    bad_att = [e for e in est if not e["as_expected"]]
    summary = {**cnt, "attacks_total": len(est), "attacks_as_expected": len(est) - len(bad_att),
               "attacks_not_as_expected": [e["attack"] for e in bad_att],
               "ri_oracle_variants_total": len(variants), "ri_oracle_variants_killed": len(variants) - len(surv_var),
               "ri_oracle_variants_surviving": [f"{v['case']}/{v['variant']}" for v in surv_var],
               "engine_mutants_total": len(muts), "engine_mutants_killed": sum(1 for x in muts if x["killed"]),
               "engine_mutants_equivalent": [x["id"] for x in muts if x["equivalent"]],
               "engine_mutants_surviving": [x["id"] for x in surv_mut],
               "observations_surviving": [f"{c}/{o}" for c, o in surv_obs]}
    files = {"kill_matrix.json": {"cases": km, "ri_oracle_variants": variants, "engine_mutants": muts},
             "est_results.json": est, "summary.json": summary}
    sums = []
    for name, obj in files.items():
        data = (json.dumps(obj, indent=1, sort_keys=True) + "\n").encode()
        (outdir / name).write_bytes(data)
        sums.append(f"{sha(data)}  {name}")
    (outdir / "SHA256SUMS").write_text("\n".join(sorted(sums, key=lambda s: s.split()[1])) + "\n")
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 1 if (surv_obs or surv_var or surv_mut or bad_att) else 0


if __name__ == "__main__":
    sys.exit(main())
