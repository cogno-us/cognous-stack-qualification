"""Security regressions: type confusion, path handling, pointer quirks, effect guard, oracle shape, hostile JSON,
freeze verification and CLI behaviour. Stubs only; the CLI is run as `python -I -B` against a throw-away copy of the package."""
from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys

import pytest

import selftest_matrix as M
from ia_eval import engine, freeze, guard, oracle as O, predicates as P, verdicts as V
from ia_eval.pointer import BLOCKED, MISSING, is_missing, resolve

PASS, FAIL, INC, NR = V.PASS, V.FAIL, V.INCONCLUSIVE, V.NOT_RUN


@pytest.fixture
def R(tmp_path):
    return M.Runner(tmp_path / "b")


def own_oracle(mut):
    o = copy.deepcopy(M.ORC)
    mut(o)
    b = (json.dumps(o, sort_keys=True, indent=1) + "\n").encode()
    return b, M.sha(b)


def obs(o, cid, oid):
    return next(x for c in o["cases"] if c["id"] == cid for x in c["observations"] if x["id"] == oid)


# ================================================================== type confusion
def test_deq_nested_bool_int_confusion():
    assert P.deq({"a": {"x": True}}, {"a": {"x": 1}}) is False
    assert P.deq([[True]], [[1]]) is False
    assert P.deq([[1]], [[1.0]]) is False
    assert P.deq({"a": [{"b": 0}]}, {"a": [{"b": False}]}) is False
    assert P.deq({"a": {"x": 1}}, {"a": {"x": 1}}) is True
    assert P.deq([[True]], [[True]]) is True
    assert P.deq({"a": 1}, {"a": 1, "b": 2}) is False and P.deq({"a": 1, "b": 2}, {"a": 1}) is False
    assert P.deq([1, 2], [1, 2, 3]) is False
    assert P.deq("1", 1) is False and P.deq(None, 0) is False and P.deq(None, False) is False


def _nested(expected, observed, op="eq"):
    def mut(o):
        ob = obs(o, "QA-01", "QA-01.1")
        ob.update(pointer="/nested", op=op, expected=expected)
    ob, osha = own_oracle(mut)
    b = M.G()
    M.setv(b, "QA-01", "am_validate", "/nested", observed)
    return b, ob, osha


@pytest.mark.parametrize("expected,observed,verdict", [
    ({"x": 1}, {"x": True}, FAIL), ({"x": 1}, {"x": 1.0}, FAIL), ({"x": 1}, {"x": 1}, PASS),
    ([[1]], [[True]], FAIL), ([[1]], [[1]], PASS), ([[True]], [[1]], FAIL), ({"a": {"x": 0}}, {"a": {"x": False}}, FAIL),
    ({"a": {"x": 0}}, {"a": {"x": 0}}, PASS), ({"a": {"x": None}}, {"a": {"x": 0}}, FAIL), ({"a": "1"}, {"a": 1}, FAIL),
])
def test_engine_nested_bool_int_confusion(R, expected, observed, verdict):
    b, ob, osha = _nested(expected, observed)
    r = R.run(b, oracle_bytes=ob, oracle_sha=osha)
    assert M.case_of(r, "QA-01")["verdict"] == verdict
    assert (r["overall"] == PASS) == (verdict == PASS)


def test_set_and_membership_ops_are_type_strict():
    assert P.op_in(True, [1])[0] is False and P.op_in(1, [True])[0] is False
    assert P.op_list_contains([1], True)[0] is False and P.op_list_contains([True], 1)[0] is False
    assert P.op_seq_eq([True], [1])[0] is False
    assert P.op_set_eq([1], [1])[0] is False          # sets are for strings only
    assert P.op_set_eq(["a", "a"], ["a"])[0] is False  # duplicates refused
    assert P.op_int_eq(True, 1)[0] is False and P.op_int_eq(1.0, 1)[0] is False and P.op_int_eq(1, 1)[0] is True
    assert P.op_any_item_matches([{"a": True}], {"a": 1})[0] is False
    assert P.op_none_item_matches([{"a": True}], {"a": 1})[0] is True
    assert P.op_len_eq(True, 1)[0] is False and P.op_len_eq([1], True)[0] is False and P.op_len_eq("a", 1)[0] is False
    assert P.op_sha256_format("sha256:" + "a" * 64)[0]
    assert not P.op_sha256_format("sha256:" + "A" * 64)[0] and not P.op_sha256_format(None)[0] and not P.op_sha256_format("sha256:" + "a" * 63)[0]


@pytest.mark.parametrize("suffix", ["\n", "\r\n", " ", "\x00"])
def test_sha256_format_rejects_trailing_characters(suffix):
    """D5 (FIXED): the pattern ends in `$`, which also matches before a trailing newline, so 'sha256:<64 hex>\n' is accepted."""
    assert P.op_sha256_format("sha256:" + "a" * 64 + suffix)[0] is False


def test_empty_expected_object_cannot_make_item_match_vacuous():
    assert P.op_any_item_matches([{"a": 1}], {})[0] is False
    assert P.op_none_item_matches([{"a": 1}], {})[0] is False


def test_nan_and_infinity_in_raw_never_satisfy_int_or_eq(R):
    b = M.G()
    rel = M.rawrel(b, "QA-01", "am_validate")
    txt = M.ser(b.raw[rel]).decode().replace('"valid": true', '"valid": NaN')
    assert "NaN" in txt
    b.raw_bytes[rel] = txt.encode()
    r = R.run(b)
    assert M.obs_of(r, "QA-01", "QA-01.1")["status"] == "violated" and r["overall"] == FAIL
    for lit in ("Infinity", "-Infinity"):
        b = M.G()
        b.raw_bytes[M.rawrel(b, "QA-01", "pack")] = M.ser(b.raw[M.rawrel(b, "QA-01", "pack")]).decode().replace(
            '"decision_count": 1', f'"decision_count": {lit}').encode()
        r = R.run(b)
        assert M.obs_of(r, "QA-01", "QA-01.35")["status"] == "violated"


# ================================================================== paths
def test_symlinked_directory_inside_bundle_is_refused(R):
    r = M.ATTACKS["path_symlinked_directory"]["fn"](R)
    assert r["overall"] == INC and r["claim_basis"] == INC
    c = M.case_of(r, "QA-01")
    assert c["verdict"] == INC and all("outside the bundle" in o["detail"] for o in c["observations"] if o["status"] == "unevaluable")
    assert all(M.case_of(r, k)["verdict"] == INC for k in ("QA-S1", "QA-S2", "QA-S3", "QA-E1"))


def test_symlinked_directory_control_the_external_copy_is_byte_identical(R):
    """Control: the same bytes read through the symlink would have produced PASS; only the refusal prevents it."""
    R2 = R.fresh()
    assert R2.run(M.G())["overall"] == PASS
    ext = R2.base.parent / (R2.base.name + "_ext")
    shutil.copytree(R2.base / "raw", ext)
    shutil.rmtree(R2.base / "raw")
    os.symlink(ext, R2.base / "raw")
    r = engine.run(M.ORC_BYTES, R2.base, M.ORC_SHA, M.sha((R2.base / "bundle.json").read_bytes()))
    assert r["overall"] == INC
    assert all((ext / p.name).read_bytes() == M.ser(M.gold().raw[f"raw/{p.name}"]) for p in ext.iterdir())


def test_symlinked_file_and_bundle_json_symlink_refused(R):
    assert M.ATTACKS["path_symlinked_file"]["fn"](R)["overall"] == INC
    R2 = R.fresh()
    R2.run(M.G())
    real = R2.base / "bundle.real.json"
    (R2.base / "bundle.json").rename(real)
    os.symlink(real, R2.base / "bundle.json")
    r = engine.run(M.ORC_BYTES, R2.base, M.ORC_SHA, M.sha(real.read_bytes()))
    assert r["overall"] == NR and r["blocked_reason"].startswith("BUNDLE_MISSING")


def test_missing_bundle_json_and_directory_in_place_of_it(R):
    r = engine.run(M.ORC_BYTES, R.base, M.ORC_SHA, "0" * 64)
    assert r["overall"] == NR and r["blocked_reason"].startswith("BUNDLE_MISSING")
    (R.base / "bundle.json").mkdir()
    assert engine.run(M.ORC_BYTES, R.base, M.ORC_SHA, "0" * 64)["blocked_reason"].startswith("BUNDLE_MISSING")


@pytest.mark.parametrize("label", ["dotdot", "absolute", "backslash", "nul", "empty", "nonstring"])
def test_unsafe_raw_paths_are_missing_evidence(R, label):
    b = M.G()
    if label == "dotdot":
        M.rename_raw(b, M._A, "../outside_cp_record.json")
    elif label == "absolute":
        M.rename_raw(b, M._A, str(R.base.resolve() / "abs_cp_record.json"))
    elif label == "backslash":
        M.rename_raw(b, M._A, "raw\\cp_record.json")
    elif label == "nul":
        b.raw.pop(M._A)
        for c in b.cases.values():
            for br in c["boundaries"].values():
                if br.get("raw") == M._A:
                    br["raw"] = "raw/cp\0record.json"
    elif label == "empty":
        b.raw.pop(M._A)
        b.cases["QA-01"]["boundaries"]["cp_record"]["raw"] = ""
        b.cases["QA-01"]["boundaries"]["cp_record"]["outcome"] = "returned"
    else:
        b.raw.pop(M._A)
        b.cases["QA-01"]["boundaries"]["cp_record"]["raw"] = ["raw/x.json"]
    r = R.run(b)
    assert M.case_of(r, "QA-01")["verdict"] == INC and r["overall"] == INC
    if label in ("dotdot", "absolute", "backslash", "nul"):
        assert any("bad raw path" in o["detail"] for o in M.case_of(r, "QA-01")["observations"] if o["status"] == "unevaluable")


def test_dotdot_file_exists_outside_and_is_not_read(R):
    """Control: the '../' target really exists with a matching hash; refusal comes from the evaluator, not from a missing file."""
    b = M.G()
    M.rename_raw(b, M._A, "../outside_cp_record.json")
    r = R.run(b)
    assert (R.base.parent / "outside_cp_record.json").is_file()
    assert M.case_of(r, "QA-01")["verdict"] == INC


def test_raw_pointing_at_a_directory_or_fifo_like_non_file(R):
    b = M.G()
    R.stage(b)
    p = R.base / M._A
    p.unlink()
    p.mkdir()
    R.state.pop(M._A)
    r = engine.run(M.ORC_BYTES, R.base, M.ORC_SHA, M.sha((R.base / "bundle.json").read_bytes()))
    assert M.case_of(r, "QA-01")["verdict"] == INC


# ================================================================== pointer quirks
@pytest.mark.parametrize("ptr", ["/a/01", "/a/00", "/a/-1", "/a/+1", "/a/1.0", "/a/ 1", "/a/1 ", "/a/٣", "/a/١", "/a/9", "/a/", "/a/x",
                                 "/a/1e0", "/a/0x1", "/a/１", "/b/0", "/a/0/x", "/a/1/0"])
def test_pointer_quirks_resolve_to_missing(ptr):
    doc = {"a": [10, 20, 30], "b": 5}
    assert is_missing(resolve(doc, ptr))
    assert resolve(doc, ptr) is (BLOCKED if ptr in ("/b/0", "/a/0/x", "/a/1/0") else MISSING)


def test_pointer_good_cases_and_escapes():
    doc = {"a": [10, 20, 30], "x/y": 1, "t~k": 2, "": 3, "n": None}
    assert resolve(doc, "/a/0") == 10 and resolve(doc, "/a/2") == 30 and resolve(doc, "/x~1y") == 1 and resolve(doc, "/t~0k") == 2
    assert resolve(doc, "/") == 3 and resolve(doc, "") is doc and resolve(doc, "/n") is None
    assert resolve(doc, "/n/x") is BLOCKED and resolve(doc, "/a/0/x") is BLOCKED and resolve(doc, "/a/9") is MISSING
    assert is_missing(MISSING) and is_missing(BLOCKED) and not is_missing(None) and not is_missing(0) and not is_missing("")
    assert not MISSING and not BLOCKED and repr(MISSING) == "MISSING" and repr(BLOCKED) == "BLOCKED" and BLOCKED is not MISSING
    for bad in ("a", "a/b", None, 5):
        with pytest.raises(ValueError):
            resolve(doc, bad)


def test_pointer_to_wrong_container_kind_is_missing_not_error():
    assert resolve({"a": {"0": "d"}}, "/a/0") == "d"          # dict key "0" (documented dict semantics)
    assert resolve({"a": "str"}, "/a/0") is BLOCKED and resolve({"a": 5}, "/a/x") is BLOCKED and resolve([1], "/x") is MISSING


@pytest.mark.parametrize("ptr", ["valid", "a/b", "x", " /a", "#raw", "#input", "#/a", "##raw_sha256", "#raw_sha256x", "#input", 5, ["/a"]])
def test_malformed_oracle_pointer_is_oracle_invalid(R, ptr):
    """D6 (NEW, '#raw_sha256x' case): oracle.py:121 uses startswith("#raw_sha256"), so a suffixed token is accepted and later raises in resolve.
    validate() rejects pointers that are not '' / '/...' / '#raw_sha256' / '#input:...'; engine reports ORACLE_INVALID NOT RUN."""
    ob, osha = own_oracle(lambda o: obs(o, "QA-01", "QA-01.1").__setitem__("pointer", ptr))
    assert O.validate(json.loads(ob))
    r = R.run(M.G(), oracle_bytes=ob, oracle_sha=osha)
    assert r["overall"] == NR and r["blocked_reason"].startswith("ORACLE_INVALID")


@pytest.mark.parametrize("ptr", ["", "/a", "/a/0", "#raw_sha256", "#input:cp_record"])
def test_wellformed_pointer_shapes_are_accepted_by_validate(ptr):
    o = copy.deepcopy(M.ORC)
    obs(o, "QA-01", "QA-01.1")["pointer"] = ptr
    assert not [e for e in O.validate(o) if "pointer" in e and "QA-01.1" in e]


def test_blocked_pointer_semantics_per_op(R):
    """BLOCKED (path crosses null/scalar): value ops violated; `absent` ok; `present` violated; plain absent key stays unevaluable."""
    r = M._run(R, lambda b: M.setv(b, "QA-01", "cp_record", "/decisions/0/binding", None))
    assert M.obs_of(r, "QA-01", "QA-01.15")["status"] == "violated" and M.case_of(r, "QA-01")["verdict"] == FAIL
    r = M._run(R, lambda b: M.delv(b, "QA-01", "cp_record", "/decisions/0/binding"))
    assert M.obs_of(r, "QA-01", "QA-01.15")["status"] == "unevaluable" and M.case_of(r, "QA-01")["verdict"] == INC
    r = M._run(R, lambda b: M.setv(b, "QA-09", "digest_reduced", "/manifest", None))
    assert M.obs_of(r, "QA-09", "QA-09.4")["status"] == "ok"            # absent holds on a BLOCKED path
    r = M._run(R, lambda b: M.setv(b, "QA-09", "digest_full", "/manifest", 5))
    assert M.obs_of(r, "QA-09", "QA-09.1")["status"] == "violated"      # present fails on a BLOCKED path
    r = M._run(R, lambda b: M.delv(b, "QA-09", "digest_full", "/manifest/metadata"))
    assert M.obs_of(r, "QA-09", "QA-09.1")["status"] == "violated"      # plain missing: present violated too
    r = M._run(R, lambda b: M.setv(b, "QA-09", "digest_reduced", "/manifest/metadata", "x"))
    assert M.obs_of(r, "QA-09", "QA-09.4")["status"] == "violated"


def test_commitment_of_is_recomputed_by_the_evaluator(R):
    """commitment_of: observed raw_commitment must equal identity.commitment() of the manifest; a lying driver or a changed manifest fails."""
    from ia_eval.identity import commitment
    g = M.gold()
    for bd in ("digest_full", "digest_reduced"):
        d = g.raw[M.rawrel(g, "QA-09", bd)]
        assert d["raw_commitment"] == commitment(d["manifest"])
    for name in ("qa09_driver_lies_about_raw_commitment", "qa09_manifest_changed_commitment_stale", "qa09_manifest_null_blocks_pointer"):
        r = M.ATTACKS[name]["fn"](R)
        assert M.case_of(r, "QA-09")["verdict"] == FAIL and r["overall"] == FAIL, name
    # consistent re-derivation by a hostile driver is accepted for the commitment but is caught by the pinned am_digest relation
    b = M.G()
    M.setv(b, "QA-09", "digest_full", "/manifest", {"metadata": "x", "extra": 1})
    M.setv(b, "QA-09", "digest_full", "/raw_commitment", commitment({"metadata": "x", "extra": 1}))
    r = R.run(b)
    assert M.obs_of(r, "QA-09", "QA-09.2")["status"] == "ok" and M.obs_of(r, "QA-09", "QA-09.3")["status"] == "violated"


def test_commitment_of_oracle_expected_must_be_a_pointer():
    for bad in ("manifest", "", 5, None, {"a": 1}):
        o = copy.deepcopy(M.ORC)
        obs(o, "QA-09", "QA-09.2")["expected"] = bad
        assert any("commitment_of" in e for e in O.validate(o)), bad


def test_relation_aliasing_two_boundaries_to_one_raw_file_is_inconclusive(R):
    """QA-26 determinism: both calls recorded in one raw file proves nothing => INCONCLUSIVE, never PASS."""
    r = M.ATTACKS["qa26_two_boundaries_alias_one_raw_file"]["fn"](R)
    o = M.obs_of(r, "QA-26", "QA-26.3")
    assert o["status"] == "unevaluable" and "itself" in o["detail"]
    assert M.case_of(r, "QA-26")["verdict"] == INC and r["overall"] == INC and M.case_of(r, "QA-26")["observation_result"] == "UNEVALUABLE"
    # distinct raw files with identical content are still fine
    assert R.run(M.G())["overall"] == PASS


def test_len_eq_is_list_only_and_sha256_fullmatch():
    assert P.op_len_eq("", 0)[0] is False and P.op_len_eq({}, 0)[0] is False and P.op_len_eq("abc", 3)[0] is False
    assert P.op_len_eq([], 0)[0] is True and P.op_len_eq([1], 0)[0] is False
    assert P.op_sha256_format("sha256:" + "a" * 64 + "\n")[0] is False


# ================================================================== effect guard
@pytest.mark.parametrize("name", [n for n in M.ATTACKS if n.startswith("guard_")])
def test_guard_violations_fail_overall_and_claim_basis(R, name):
    r = M.ATTACKS[name]["fn"](R)
    assert r["violations"], name
    assert r["overall"] == FAIL and r["claim_basis"] == FAIL
    assert all(M.case_of(r, c)["verdict"] == PASS for c in M.MAND), "cases themselves pass: the guard alone must flip the outcome"


def test_guard_effect_named_native_call_is_flagged_even_when_allow_listed():
    allowed = ["a.b.execute", "a.reconcile", "x.apply", "svc.send", "svc.post", "svc.deliver", "svc.charge", "svc.submit", "a.delete", "a.put", "a.run_effect"]
    v = guard.check_events([{"kind": "native_call", "callable": n} for n in allowed], allowed)
    assert len(v) == len(allowed) and all("effect path" in x for x in v)
    benign = ["agent_control_plane.bounded.BoundedAuthorizationWorkflow.decide", "m.validate_evidence_pack", "m.dump_evidence_pack", "m.applicable_rules"]
    assert guard.check_events([{"kind": "native_call", "callable": n} for n in benign], benign) == []


def test_guard_unit_kinds_and_shapes():
    ok = [{"kind": "git_read"}, {"kind": "file_read", "path": "/x"}, {"kind": "native_call", "callable": "a.b"}, {"kind": "scratch_write", "path": "scratch/x/y.json"}]
    assert guard.check_events(ok, ["a.b"]) == []
    assert guard.check_events([], []) == []
    for bad_events in (None, {}, "events", 5, ({"kind": "git_read"},)):
        assert guard.check_events(bad_events, []) and "driver_events" in guard.check_events(bad_events, [])[0]
    for e in (None, 5, "native_call", {}, {"kind": 5}, {"kind": None}, {"kind": "Git_Read"}, {"kind": "network"}, {"kind": "subprocess"},
              {"kind": "http"}, {"kind": "exec"}, {"kind": "git_push"}, {"kind": "native_call"}, {"kind": "native_call", "callable": 5}):
        assert len(guard.check_events([e], ["a.b"])) == 1, e


@pytest.mark.parametrize("path", ["scratch/../../x", "scratch/..", "/scratch/x", "/etc/passwd", "scratch\\x", "scratch/a\0b", "scratch", "scratch/",
                                  "scratch//x", "scratch/./x", "Scratch/x", "", None, 5, "x/scratch/y", "../scratch/x", "scratch/x/../../y"])
def test_guard_scratch_write_paths_outside_scratch(path):
    assert len(guard.check_events([{"kind": "scratch_write", "path": path}], [])) == 1, path


@pytest.mark.parametrize("path", ["scratch/a", "scratch/a/b.json", "scratch/.hidden", "scratch/a..b"])
def test_guard_scratch_write_paths_inside_scratch(path):
    assert guard.check_events([{"kind": "scratch_write", "path": path}], []) == []


def test_absent_driver_events_fail_overall_and_claim_basis(R):
    for n in ("guard_events_key_absent", "guard_events_null"):
        r = M.ATTACKS[n]["fn"](R)
        assert r["overall"] == FAIL and r["claim_basis"] == FAIL and "driver_events" in r["violations"][0]


def test_unlisted_native_call_names_are_exact_not_prefix(R):
    allowed = M.ORC["allowed_native_calls"][0]
    for name in (allowed + "x", allowed.upper(), allowed.rsplit(".", 1)[0], " " + allowed, allowed + "\n"):
        b = M.G()
        b.driver_events.append({"kind": "native_call", "callable": name})
        r = R.run(b)
        assert r["overall"] == FAIL and r["claim_basis"] == FAIL, name


def test_allow_listed_calls_and_reads_do_not_trip_the_guard(R):
    b = M.G()
    b.driver_events += [{"kind": "native_call", "callable": c} for c in M.ORC["allowed_native_calls"]]
    b.driver_events += [{"kind": "git_read"}, {"kind": "file_read", "path": "../../anything"}, {"kind": "scratch_write", "path": "scratch/a.json"}]
    r = R.run(b)
    assert r["overall"] == PASS and r["violations"] == []
    assert [c for c in M.ORC["allowed_native_calls"] if guard._EFFECT_NAME.search(c)] == []


# ================================================================== oracle shape
def _delp(o):
    del obs(o, "QA-01", "QA-01.1")["pointer"]


def _substr_int(o):
    ob = obs(o, "QA-01", "QA-01.1")
    ob.update(op="contains_substr", expected=5)


def _substr_empty(o):
    obs(o, "QA-01", "QA-01.1").update(op="contains_substr", expected="")


def _rel_label(o):
    obs(o, "QA-01", "QA-01.10")["expected"]["pointer"] = "/chain_verdict"


def _rel_label_hash(o):
    obs(o, "QA-01", "QA-01.10")["expected"]["pointer"] = "#/ok"


def _ptr_label(o):
    obs(o, "QA-01", "QA-01.1")["pointer"] = "/all_ok"


def _ptr_label_deep(o):
    obs(o, "QA-01", "QA-01.1")["pointer"] = "/a/b/retains_upstream_refusal/c"


def _case(cid):
    return lambda o: next(c for c in o["cases"] if c["id"] == cid)


SHAPE = {
    "value_op_without_pointer": _delp,
    "substring_expected_not_str": _substr_int,
    "substring_expected_empty": _substr_empty,
    "relation_pointer_orchestrator_label": _rel_label,
    "relation_pointer_hash_label": _rel_label_hash,
    "pointer_orchestrator_label": _ptr_label,
    "pointer_deep_orchestrator_label": _ptr_label_deep,
    "unknown_op": lambda o: obs(o, "QA-01", "QA-01.1").__setitem__("op", "approx_eq"),
    "unknown_obs_key": lambda o: obs(o, "QA-01", "QA-01.1").__setitem__("tolerance", 1),
    "unknown_case_key": lambda o: _case("QA-01")(o).__setitem__("skip", True),
    "unknown_top_key": lambda o: o.__setitem__("defaults", {}),
    "missing_top_key": lambda o: o.pop("claim"),
    "wrong_schema": lambda o: o.__setitem__("schema", "ia-oracle/2"),
    "duplicate_case_id": lambda o: o["cases"].append(copy.deepcopy(o["cases"][0])),
    "duplicate_obs_id": lambda o: _case("QA-S1")(o)["observations"].append(copy.deepcopy(_case("QA-S1")(o)["observations"][0])),
    "gated_obs_without_source": lambda o: obs(o, "QA-01", "QA-01.1").pop("source"),
    "native_source_without_line": lambda o: obs(o, "QA-08", "QA-08.1")["source"].pop("line"),
    "bad_source_kind": lambda o: obs(o, "QA-08", "QA-08.1")["source"].__setitem__("kind", "trust_me"),
    "info_mandatory": lambda o: _case("QA-I1")(o).__setitem__("mandatory", True),
    "obs_not_mandatory": lambda o: _case("QA-09")(o).__setitem__("mandatory", False),
    "ri_not_mandatory": lambda o: _case("QA-03")(o).__setitem__("mandatory", False),
    "mandatory_not_bool": lambda o: _case("QA-03")(o).__setitem__("mandatory", "yes"),
    "ri_mutation_without_control": lambda o: _case("QA-03")(o).pop("paired_control"),
    "control_is_self": lambda o: _case("QA-03")(o).__setitem__("paired_control", "QA-03"),
    "control_unknown": lambda o: _case("QA-03")(o).__setitem__("paired_control", "QA-404"),
    "zero_observations": lambda o: _case("QA-03")(o).__setitem__("observations", []),
    "na_with_observations": lambda o: _case("QA-14")(o).__setitem__("observations", copy.deepcopy(_case("QA-S1")(o)["observations"])),
    "failure_condition_missing": lambda o: _case("QA-03")(o).__setitem__("failure_condition", ""),
    "unknown_class": lambda o: _case("QA-03")(o).__setitem__("class", "TRUSTED"),
    "obs_reason_missing": lambda o: _case("QA-09")(o).pop("reason"),
    "eq_ref_expected_not_object": lambda o: obs(o, "QA-01", "QA-01.10").__setitem__("expected", "x"),
    "set_eq_expected_not_list": lambda o: obs(o, "QA-01", "QA-01.1").update(op="set_eq", expected="a"),
    "any_item_expected_empty": lambda o: obs(o, "QA-01", "QA-01.18").__setitem__("expected", {}),
    "raised_type_expected_missing": lambda o: obs(o, "QA-03", "QA-03.1").pop("expected"),
}


@pytest.mark.parametrize("name", sorted(SHAPE))
def test_oracle_shape_errors_are_oracle_invalid_not_run(R, name):
    ob, osha = own_oracle(SHAPE[name])
    errs = O.validate(json.loads(ob))
    assert errs, f"{name}: validate() accepted a malformed oracle"
    r = R.run(M.G(), oracle_bytes=ob, oracle_sha=osha)       # pinned with its OWN sha: validity, not drift, must refuse it
    assert r["overall"] == NR and r["claim_basis"] == NR and r["blocked_reason"].startswith("ORACLE_INVALID"), r["blocked_reason"]
    assert all(c["verdict"] == NR for c in r["cases"] if c["mandatory"])
    assert "oracle_sha256" not in r


def test_unchanged_oracle_validates_and_every_gated_observation_has_a_source():
    assert O.validate(M.ORC) == []
    for c in M.ORC["cases"]:
        if c["class"] in O.GATED:
            assert all(o.get("source") for o in c["observations"]), c["id"]


@pytest.mark.parametrize("raw", [b"[]", b"5", b"null", b'"x"', b'{"schema": "ia-oracle/1", "cases": 5}', b'{"schema": "ia-oracle/1", "cases": [5]}'])
def test_non_object_or_garbage_oracle_never_passes_and_never_crashes(R, raw):
    r = R.run(M.G(), oracle_bytes=raw, oracle_sha=M.sha(raw))
    assert isinstance(r, dict) and r["overall"] in (NR, INC) and r["claim_basis"] in (NR, INC)


# ================================================================== hostile JSON
def _bundle_bytes_run(R, data, **kw):
    b = M.G()
    b.bundle_bytes = data
    return R.run(b, **kw)


@pytest.mark.parametrize("label,data", [
    ("deep_nesting", b"[" * 100000),
    ("deep_nesting_objects", b'{"a":' * 50000),
    ("huge_integer", None),
    ("bom", None), ("trailing_data", None), ("trailing_garbage", None), ("invalid_utf8", b"\xff\xfe{}"), ("utf16", None),
    ("empty", b""), ("whitespace", b"  \n"), ("nul_byte", b"{\x00}"), ("not_object", b"[]"), ("string", b'"x"'),
])
def test_hostile_bundle_json_never_passes_and_never_crashes(R, label, data):
    good = M.G().render()[1]
    if label == "huge_integer":
        data = good.replace(b'"orchestrator_status": {}', b'"orchestrator_status": {"n": ' + b"9" * 5000 + b"}")
        assert data != good
    elif label == "bom":
        data = b"\xef\xbb\xbf" + good
    elif label == "trailing_data":
        data = good + b"{}"
    elif label == "trailing_garbage":
        data = good + b"\x00garbage"
    elif label == "utf16":
        data = good.decode().encode("utf-16")
    r = _bundle_bytes_run(R, data)
    assert isinstance(r, dict) and r["overall"] in (NR, INC) and r["claim_basis"] in (NR, INC), (label, r["overall"])
    assert r["blocked_reason"].startswith(("BUNDLE_UNREADABLE", "BUNDLE_SCHEMA_INVALID", "EVALUATOR_ERROR"))
    assert all(c["verdict"] != PASS for c in r["cases"])


def test_leading_whitespace_in_bundle_is_ordinary_json(R):
    good = M.G().render()[1]
    assert _bundle_bytes_run(R, b"\n\n  " + good)["overall"] == PASS


def test_bundle_size_cap(R):
    big = b'{"pad": "' + b"a" * (O.MAX_JSON_BYTES + 1) + b'"}'
    r = _bundle_bytes_run(R, big)
    assert r["overall"] == NR and r["blocked_reason"].startswith("BUNDLE_UNREADABLE") and "8 MiB" in r["blocked_reason"]
    just_under = M.G().render()[1]
    assert len(just_under) < O.MAX_JSON_BYTES


@pytest.mark.parametrize("label", ["huge_integer", "deep", "size_cap", "bom", "trailing", "dup_nested", "invalid_utf8", "lone_surrogate"])
def test_hostile_raw_json_is_unparsable_evidence(R, label):
    b = M.G()
    rel = M._A
    good = M.ser(b.raw[rel])
    data = {"huge_integer": b'{"decisions": [{"result": ' + b"9" * 5000 + b"}]}", "deep": b"[" * 100000,
            "size_cap": b'{"pad": "' + b"a" * (O.MAX_JSON_BYTES + 1) + b'"}', "bom": b"\xef\xbb\xbf" + good, "trailing": good + b"{}",
            "dup_nested": good.replace(b'"result": "authorized"', b'"result": "authorized", "result": "hold"'),
            "invalid_utf8": b"\xff", "lone_surrogate": good.replace(b'"authorized"', b'"\\ud800"')}[label]
    b.raw_bytes[rel] = data
    r = R.run(b)
    c = M.case_of(r, "QA-01")
    if label == "lone_surrogate":
        assert c["verdict"] == FAIL           # parseable JSON, wrong value
        return
    assert c["verdict"] == INC and r["overall"] == INC, (label, c["verdict"])
    assert any(o["status"] == "unevaluable" for o in c["observations"])


def test_hostile_oracle_bytes(R):
    for data in (b"[" * 100000, b'{"a":' * 50000, b"1" * 5000, b"\xef\xbb\xbf" + M.ORC_BYTES, M.ORC_BYTES + b"{}", b"", b"\xff",
                 b'{"x": 1, "x": 2}', b"a" * (O.MAX_JSON_BYTES + 1)):
        r = R.run(M.G(), oracle_bytes=data, oracle_sha=M.sha(data))
        assert r["overall"] == NR and r["blocked_reason"].startswith("ORACLE_UNREADABLE"), data[:20]
        assert r["cases"] == []


def test_deep_but_parseable_raw_document_does_not_crash(R):
    deep = "[" * 900 + "]" * 900
    b = M.G()
    b.raw_bytes[M._A] = deep.encode()
    r = R.run(b)
    assert isinstance(r, dict) and r["overall"] != PASS


def test_object_pairs_hook_rejects_duplicates_at_every_depth():
    for txt in ('{"a":1,"a":2}', '{"x":{"a":1,"a":2}}', '[{"a":1,"a":2}]', '{"a":1,"b":{"c":[{"d":1,"d":1}]}}'):
        with pytest.raises(O.OracleError):
            O.load_json_strict(txt.encode())
    assert O.load_json_strict(b'{"a":1,"b":{"a":2}}') == {"a": 1, "b": {"a": 2}}


# ================================================================== verdict combine
def test_combine_unit():
    c = V.combine
    assert c([]) == NR and c([PASS]) == PASS and c([PASS, PASS]) == PASS
    assert c([PASS, FAIL, INC, NR]) == FAIL and c([PASS, INC, NR]) == INC and c([PASS, NR]) == NR
    assert c([V.NOT_APPLICABLE]) == INC and c([PASS, V.NOT_APPLICABLE]) == INC      # NA is not a mandatory outcome
    assert c(iter([PASS, INC])) == INC
    assert c(["PASS", "bogus"]) == INC and c(["bogus"]) == INC                     # unknown vocabulary never PASSes


# ================================================================== freeze
@pytest.fixture
def tree(tmp_path):
    base = tmp_path / "pkg"
    (base / "sub").mkdir(parents=True)
    (base / "freeze").mkdir()
    (base / "a.txt").write_text("alpha")
    (base / "sub" / "b.json").write_text('{"b": 1}')
    m = freeze.build(base, {"k": "v"})
    (base / freeze.MANIFEST_REL).write_text(json.dumps(m))
    return base, m["root_commitment"]


def test_freeze_clean_tree_verifies(tree):
    base, root = tree
    assert freeze.verify(base, root) == []
    assert sorted(freeze.build(base, {})["files"]) == ["a.txt", "sub/b.json"]


def test_freeze_detects_changed_missing_and_unlisted(tree):
    base, root = tree
    (base / "a.txt").write_text("alphA")
    assert freeze.verify(base, root) == ["changed file a.txt"]
    (base / "a.txt").write_text("alpha")
    (base / "sub" / "b.json").unlink()
    assert freeze.verify(base, root) == ["missing file sub/b.json"]
    (base / "sub" / "b.json").write_text('{"b": 1}')
    (base / "sub" / "evil.py").write_text("print(1)")
    assert freeze.verify(base, root) == ["unlisted file sub/evil.py"]
    (base / "sub" / "evil.py").unlink()
    (base / "empty_dir").mkdir()
    assert freeze.verify(base, root) == []                               # directories carry no code


def test_freeze_detects_any_pyc_even_in_pycache(tree):
    base, root = tree
    (base / "__pycache__").mkdir()
    (base / "__pycache__" / "a.cpython-313.pyc").write_bytes(b"\0")
    p = freeze.verify(base, root)
    assert len(p) == 1 and p[0].startswith("bytecode present") and "a.cpython-313.pyc" in p[0]
    (base / "__pycache__" / "a.cpython-313.pyc").unlink()
    (base / "sub" / "x.pyc").write_bytes(b"\0")
    assert freeze.verify(base, root)[0].startswith("bytecode present") and "sub/x.pyc" in freeze.verify(base, root)[0]


def test_freeze_wrong_root_and_self_inconsistent_manifest(tree):
    base, root = tree
    assert any(p.startswith("root ") and "!= committed" in p for p in freeze.verify(base, "0" * 64))
    mp = base / freeze.MANIFEST_REL
    m = json.loads(mp.read_text())
    m["files"]["a.txt"] = "0" * 64
    mp.write_text(json.dumps(m))
    probs = freeze.verify(base, root)
    assert "manifest root_commitment does not match its own contents" in probs and "changed file a.txt" in probs
    m["root_commitment"] = freeze.root_of({k: m[k] for k in ("schema", "meta", "files")})
    mp.write_text(json.dumps(m))
    probs = freeze.verify(base, root)
    assert any("!= committed" in p for p in probs) and "changed file a.txt" in probs     # re-rooted manifest still fails the external pin


def test_freeze_manifest_missing_unreadable_wrong_shape(tree):
    base, root = tree
    mp = base / freeze.MANIFEST_REL
    good = mp.read_bytes()
    mp.write_bytes(b'{"files": {}, "files": {}}')
    assert freeze.verify(base, root)[0].startswith("freeze manifest unreadable")
    mp.write_bytes(b"[]")
    assert freeze.verify(base, root) == ["freeze manifest has the wrong shape"]
    mp.write_bytes(b'{"files": 5}')
    assert freeze.verify(base, root) == ["freeze manifest has the wrong shape"]
    mp.write_bytes(b"\xff")
    assert freeze.verify(base, root)[0].startswith("freeze manifest unreadable")
    mp.write_bytes(good.replace(b'"ia-freeze-manifest/1"', b'"ia-freeze-manifest/9"'))
    assert "bad freeze schema" in freeze.verify(base, root)
    mp.unlink()
    assert freeze.verify(base, root) == ["freeze manifest missing"]
    assert freeze.verify(base, root, manifest_path=base / "nope.json") == ["freeze manifest missing"]


def test_freeze_results_dir_is_outside_scope_by_design(tree):
    base, root = tree
    (base / "results").mkdir()
    (base / "results" / "x.json").write_text("{}")
    assert freeze.verify(base, root) == []


def test_freeze_symlink_in_scope_is_reported_not_raised(tree):
    """A planted symlink must come back as a freeze problem. D3 (FIXED): freeze.verify() lets hash_scope's ValueError escape."""
    base, root = tree
    os.symlink(base / "a.txt", base / "link.txt")
    try:
        probs = freeze.verify(base, root)
    except ValueError as e:
        pytest.fail(f"freeze.verify raised ValueError({e}) instead of returning a problem list")
    assert any("link.txt" in p for p in probs)


def test_freeze_hash_scope_canonical_root_is_deterministic(tree):
    base, _ = tree
    assert freeze.build(base, {"k": 1}) == freeze.build(base, {"k": 1})
    assert freeze.build(base, {"k": 1})["root_commitment"] != freeze.build(base, {"k": 2})["root_commitment"]


# ================================================================== CLI
CODE = "import sys; sys.path.insert(0, sys.argv[1]); from ia_eval.cli import main; sys.exit(main(sys.argv[2:]))"


class Cli:
    def __init__(self, root):
        self.root = root
        self.pkg = root / "internal_a"
        shutil.copytree(M.PKG / "ia_eval", self.pkg / "ia_eval", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (self.pkg / "oracle").mkdir()
        shutil.copy(M.PKG / "oracle" / "oracle.v1.json", self.pkg / "oracle" / "oracle.v1.json")
        (self.pkg / "freeze").mkdir()
        self.oracle = self.pkg / "oracle" / "oracle.v1.json"
        self.fr = self.call("freeze-build", "--meta-json", "{}").stdout.strip()
        self.runner = M.Runner(root / "bundle")

    def call(self, *args):
        return subprocess.run([sys.executable, "-I", "-B", "-c", CODE, str(self.pkg), *map(str, args)], capture_output=True, text=True, timeout=120, cwd=str(self.root))

    def bundle(self, mutate=None):
        b = M.G()
        if mutate:
            mutate(b)
        self.runner.stage(b)
        return self.runner.base, M.sha((self.runner.base / "bundle.json").read_bytes())

    def evaluate(self, bundle=None, *extra, root=None, bsha=None, osha=None, oracle=None):
        d, s = bundle if bundle else self.bundle()
        return self.call("evaluate", "--oracle", oracle or self.oracle, "--expect-oracle-sha256", osha or M.ORC_SHA, "--bundle", d,
                         "--expect-bundle-sha256", bsha or s, "--freeze-root", root or self.fr, *extra)


@pytest.fixture
def cli(tmp_path):
    return Cli(tmp_path / "cli")


def test_cli_freeze_root_is_a_sha256(cli):
    assert len(cli.fr) == 64 and int(cli.fr, 16) >= 0
    out = cli.call("freeze-verify", "--freeze-root", cli.fr)
    assert out.returncode == 0 and out.stdout.strip() == "FREEZE OK"


def test_cli_exit_0_only_for_pass(cli):
    r = cli.evaluate()
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["overall"] == "PASS"


def test_cli_exit_1_for_fail(cli):
    r = cli.evaluate(cli.bundle(lambda b: M.setv(b, "QA-02", "cp_record", "/decisions/0/result", "authorized")))
    assert r.returncode == 1 and json.loads(r.stdout)["overall"] == "FAIL"


@pytest.mark.parametrize("label", ["inconclusive", "not_run_skipped", "not_run_zero", "bundle_drift", "oracle_drift", "freeze_wrong_root", "bad_oracle_pin"])
def test_cli_exit_2_for_everything_else(cli, label):
    kw = {}
    if label == "inconclusive":
        bundle = cli.bundle(lambda b: b.drop_files.add(M._A))
    elif label == "not_run_skipped":
        bundle = cli.bundle(lambda b: b.cases["QA-08"].__setitem__("executed", False))
    elif label == "not_run_zero":
        bundle = cli.bundle(lambda b: b.cases.clear())
    else:
        bundle = cli.bundle()
        if label == "bundle_drift":
            kw["bsha"] = "0" * 64
        elif label == "oracle_drift":
            o = bytearray(cli.oracle.read_bytes())
            o[o.index(b"draft")] ^= 1
            cli.oracle.write_bytes(bytes(o))
            cli.fr = cli.call("freeze-build", "--meta-json", "{}").stdout.strip()   # keep the package consistent so ONLY the oracle pin fails
        elif label == "freeze_wrong_root":
            kw["root"] = "0" * 64
        else:
            kw["osha"] = "0" * 64
    r = cli.evaluate(bundle, **kw)
    assert r.returncode == 2, (label, r.returncode, r.stderr[-300:])
    rep = json.loads(r.stdout)
    assert rep["overall"] in ("NOT RUN", "INCONCLUSIVE") and rep["claim_basis"] != "PASS"


def test_cli_freeze_drift_when_package_file_changes_or_bytecode_planted(cli):
    (cli.pkg / "ia_eval" / "engine.py").write_text((cli.pkg / "ia_eval" / "engine.py").read_text() + "\n# tampered\n")
    r = cli.evaluate()
    rep = json.loads(r.stdout)
    assert r.returncode == 2 and rep["overall"] == "NOT RUN" and rep["blocked_reason"].startswith("FREEZE_DRIFT") and "changed file ia_eval/engine.py" in rep["blocked_reason"]
    v = cli.call("freeze-verify", "--freeze-root", cli.fr)
    assert v.returncode == 1 and "changed file ia_eval/engine.py" in v.stdout


def test_cli_freeze_drift_for_pyc_and_unlisted_file(cli):
    (cli.pkg / "ia_eval" / "__pycache__").mkdir()
    (cli.pkg / "ia_eval" / "__pycache__" / "engine.cpython-313.pyc").write_bytes(b"\0")
    rep = json.loads(cli.evaluate().stdout)
    assert rep["overall"] == "NOT RUN" and "bytecode present" in rep["blocked_reason"]
    shutil.rmtree(cli.pkg / "ia_eval" / "__pycache__")
    (cli.pkg / "ia_eval" / "extra.py").write_text("x = 1\n")
    rep = json.loads(cli.evaluate().stdout)
    assert rep["overall"] == "NOT RUN" and "unlisted file ia_eval/extra.py" in rep["blocked_reason"]


def test_cli_usage_errors_exit_2(cli):
    assert cli.call().returncode == 2
    assert cli.call("evaluate").returncode == 2
    assert cli.call("evaluate", "--oracle", cli.oracle, "--bogus", "1").returncode == 2
    assert cli.call("no-such-command").returncode == 2
    assert cli.call("evaluate", "--orac", cli.oracle).returncode == 2         # allow_abbrev is off


def test_cli_out_writes_new_file_and_refuses_existing(cli, tmp_path):
    out = tmp_path / "report.json"
    r = cli.evaluate(None, "--out", out)
    assert r.returncode == 0 and r.stdout == "" and json.loads(out.read_text())["overall"] == "PASS"
    before = out.read_bytes()
    r = cli.evaluate(None, "--out", out)
    assert r.returncode == 2 and "refusing" in r.stderr and out.read_bytes() == before


def test_cli_out_refuses_symlink_even_dangling(cli, tmp_path):
    victim = tmp_path / "victim.txt"
    victim.write_text("keep")
    link = tmp_path / "link.json"
    os.symlink(victim, link)
    r = cli.evaluate(None, "--out", link)
    assert r.returncode == 2 and victim.read_text() == "keep"
    dangling = tmp_path / "dangling.json"
    os.symlink(tmp_path / "does-not-exist.json", dangling)
    r = cli.evaluate(None, "--out", dangling)
    assert r.returncode == 2 and not (tmp_path / "does-not-exist.json").exists()


@pytest.mark.parametrize("rel", ["out.json", "ia_eval/out.json", "oracle/report.json", "freeze/report.json", "sub/../out2.json"])
def test_cli_out_refuses_paths_inside_the_package(cli, rel):
    (cli.pkg / "sub").mkdir(exist_ok=True)
    target = cli.pkg / rel
    r = cli.evaluate(None, "--out", target)
    assert r.returncode == 2 and "refusing" in r.stderr and not target.exists()


def test_cli_out_refuses_oracle_and_bundle_paths(cli):
    bundle = cli.bundle()
    r = cli.evaluate(bundle, "--out", bundle[0] / "bundle.json")
    assert r.returncode == 2 and "refusing" in r.stderr
    assert M.sha((bundle[0] / "bundle.json").read_bytes()) == bundle[1]
    r = cli.evaluate(bundle, "--out", cli.oracle)
    assert r.returncode == 2 and M.sha(cli.oracle.read_bytes()) == M.ORC_SHA


def test_cli_out_symlinked_parent_into_package_is_refused(cli, tmp_path):
    os.symlink(cli.pkg / "oracle", tmp_path / "alias")
    r = cli.evaluate(None, "--out", tmp_path / "alias" / "report.json")
    assert r.returncode == 2 and not (cli.pkg / "oracle" / "report.json").exists()


def test_cli_missing_oracle_file_is_exit_2_not_a_traceback(cli):
    """D4 (FIXED): Path(a.oracle).read_bytes() is outside any handler; the traceback exits 1, which is the FAIL code."""
    r = cli.evaluate(None, oracle=cli.pkg / "oracle" / "missing.json")
    assert r.returncode == 2, (r.returncode, r.stderr[-200:])
    assert "Traceback" not in r.stderr


def test_cli_out_in_missing_directory_is_exit_2_not_a_traceback(cli, tmp_path):
    """D4b (FIXED): open(out, 'x') in a non-existent directory raises after evaluation; exit code 1 would read as FAIL."""
    r = cli.evaluate(None, "--out", tmp_path / "no-such-dir" / "r.json")
    assert r.returncode == 2 and "Traceback" not in r.stderr


def test_cli_symlink_planted_in_package_is_a_freeze_block_not_a_crash(cli):
    """D3 (CLI face, FIXED): freeze.verify raises ValueError on a symlink in scope; the traceback exits 1 (= FAIL)."""
    os.symlink(cli.pkg / "oracle" / "oracle.v1.json", cli.pkg / "ia_eval" / "link.py")
    r = cli.evaluate()
    assert r.returncode == 2 and "Traceback" not in r.stderr


def test_cli_collect_identity_refuses_traversal_and_marks_missing(cli, tmp_path):
    root = tmp_path / "idroot"
    root.mkdir()
    (root / "f.txt").write_text("hi")
    os.symlink(root / "f.txt", root / "l.txt")
    out = cli.call("collect-identity", "--root", root, "f.txt", "nope.txt", "l.txt")
    assert out.returncode == 0
    d = json.loads(out.stdout)
    assert d["f.txt"]["sha256"] == M.sha(b"hi") and d["nope.txt"] == {"missing": True} and d["l.txt"] == {"missing": True}
    assert d["f.txt"]["git_blob"] == __import__("hashlib").sha1(b"blob 2\x00hi").hexdigest() == "32f95c0d1244a78b2be1bab8de17906fabb2c4a8"
    bad = cli.call("collect-identity", "--root", root, "../x")
    assert bad.returncode != 0 and bad.stdout == ""
