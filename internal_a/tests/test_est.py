"""EST-01 .. EST-12: the evaluator-subversion threats. Every test is an attack that must NOT yield PASS."""
from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

import pytest

import selftest_matrix as M
from ia_eval import oracle as O, verdicts as V

PASS, FAIL, INC, NR = V.PASS, V.FAIL, V.INCONCLUSIVE, V.NOT_RUN
CNT = M._CNT


@pytest.fixture
def R(tmp_path):
    return M.Runner(tmp_path / "b")


def atk(R, name):
    return M.ATTACKS[name]["fn"](R)


def own_oracle(mut):
    o = copy.deepcopy(M.ORC)
    mut(o)
    b = (json.dumps(o, sort_keys=True, indent=1) + "\n").encode()
    return b, M.sha(b)


# ------------------------------------------------------------------ EST-01
def test_est01_false_success_summary_is_ignored(R):
    """EST-01: an orchestrator `all_ok`/`chain_verdict` summary cannot rescue wrong raw values."""
    r = atk(R, "est01_false_success_summary")
    assert r["overall"] == FAIL and r["claim_basis"] == FAIL
    assert M.case_of(r, "QA-01")["verdict"] == FAIL
    assert M.obs_of(r, "QA-01", "QA-01.11")["status"] == "violated"
    assert M.obs_of(r, "QA-01", "QA-01.31")["status"] == "violated"
    assert r["ignored_orchestrator_status_keys"] == ["all_ok", "chain_verdict"]


def test_est01_orchestrator_labels_do_not_change_any_verdict(R):
    """EST-01: identical raw evidence => identical verdicts whatever the orchestrator says, in both directions."""
    wrong = M.G()
    M._est01(wrong)
    wrong2 = wrong.clone()
    wrong2.orch.clear()
    a, b = R.run(wrong), R.run(wrong2)
    assert M.vmap(a) == M.vmap(b) and a["overall"] == b["overall"] == FAIL
    good = M.G()
    good.orch.update({"all_ok": False, "chain_verdict": "REFUSED_NATIVE", "ok": False})
    good.cases["QA-01"]["chain_verdict"] = "REFUSED_NATIVE"
    g = R.run(good)
    assert g["overall"] == PASS and g["ignored_orchestrator_status_keys"] == ["all_ok", "chain_verdict", "ok"]


def test_est01_orchestrator_label_pointers_are_refused_by_the_oracle():
    """EST-01: an oracle that tried to read an orchestrator label as evidence is invalid (L25)."""
    for seg in ("chain_verdict", "all_ok", "retains_upstream_refusal", "ACCEPTED"):
        def mut(o, seg=seg):
            o["cases"][0]["observations"][0]["pointer"] = "/" + seg
        errs = O.validate(json.loads(own_oracle(mut)[0]))
        assert any("orchestrator-label" in e for e in errs), seg


# ------------------------------------------------------------------ EST-02
def test_est02_hold_changed_to_authorized_fails_qa02(R):
    """EST-02: HOLD silently reported as authorized => QA-02 FAIL and the refusals it controls lose their control."""
    r = atk(R, "est02_hold_to_authorized")
    assert M.case_of(r, "QA-02")["verdict"] == FAIL
    assert M.obs_of(r, "QA-02", "QA-02.11")["status"] == "violated"
    assert r["overall"] == FAIL and r["claim_basis"] == FAIL
    for dep in ("QA-03", "QA-05", "QA-27"):
        assert M.case_of(r, dep)["verdict"] == INC, dep


# ------------------------------------------------------------------ EST-03
@pytest.mark.parametrize("counter", M.PACK_COUNTS)
@pytest.mark.parametrize("val", [False, True, "0", 0.0, None, [], {}, "", 1])
def test_est03_pack_counters_of_wrong_type_or_value_never_pass(R, counter, val):
    """EST-03: counters as bool/'0'/0.0/None/[]/{} (or nonzero) are not the integer 0."""
    r = M._run(R, lambda b: M.setv(b, "QA-01", "pack", CNT + counter, val))
    assert M.case_of(r, "QA-01")["verdict"] in (FAIL, INC)
    assert r["overall"] != PASS and r["claim_basis"] != PASS
    assert M.obs_of(r, "QA-01", f"QA-01.{28 + M.PACK_COUNTS.index(counter)}")["status"] == "violated"


@pytest.mark.parametrize("val", [True, "1", 1.0, None])
def test_est03_int_eq_counters_with_expected_one(R, val):
    """EST-03: the granted counter (expected int 1) rejects True/'1'/1.0/null."""
    r = M._run(R, lambda b: M.setv(b, "QA-01", "pack", CNT + "authorization_granted_count", val))
    assert M.obs_of(r, "QA-01", "QA-01.25")["status"] == "violated"
    assert r["overall"] == FAIL


@pytest.mark.parametrize("name", ["attempts", "observations", "reconciliations"])
@pytest.mark.parametrize("val", ["", {}, 0, None, False, "0"])
def test_est03_cp_empty_list_counters_of_wrong_type_never_pass(R, name, val):
    """EST-03: CP attempts/observations/reconciliations must be the empty LIST, not '' / {} / 0 / null."""
    r = M._run(R, lambda b: M.setv(b, "QA-01", "cp_record", "/" + name, val))
    assert M.case_of(r, "QA-01")["verdict"] in (FAIL, INC), f"{name}={val!r} accepted as zero {name}"
    assert r["overall"] != PASS


def test_est03_bool_as_int_and_false_as_zero(R):
    """EST-03: nested True/1 and False/0 confusion at the engine level."""
    for name in ("bool_as_int_valid", "false_as_zero_semantics"):
        r = atk(R, name)
        assert M.case_of(r, "QA-01")["verdict"] == FAIL and r["overall"] == FAIL, name


# ------------------------------------------------------------------ EST-04
def test_est04_downstream_refusal_dropped_not_rescued_by_bundle_label(R):
    """EST-04: Replay runtime_decision hold removed => FAIL; bundle-supplied retains_upstream_refusal:true cannot rescue."""
    r = atk(R, "est04_downstream_refusal_dropped")
    assert M.case_of(r, "QA-02")["verdict"] == FAIL
    assert M.obs_of(r, "QA-02", "QA-02.18")["status"] == "violated"
    assert r["overall"] == FAIL and r["claim_basis"] == FAIL
    assert "retains_upstream_refusal" in r["ignored_orchestrator_status_keys"]


def test_est04_retention_label_in_raw_doc_or_case_is_inert(R):
    """EST-04: the label planted everywhere (raw doc, case dict, status) with a CORRECT hold changes nothing."""
    b = M.G()
    M.setv(b, "QA-02", "replay_bundle", "/retains_upstream_refusal", False)
    b.cases["QA-02"]["retains_upstream_refusal"] = False
    b.orch["retains_upstream_refusal"] = False
    assert R.run(b)["overall"] == PASS


# ------------------------------------------------------------------ EST-05
@pytest.mark.parametrize("cid", ["QA-03", "QA-05", "QA-12", "QA-25"])
def test_est05_one_character_change_in_expected_message_fails(R, cid):
    """EST-05: a one-character change in an expected exception message fails the case."""
    r = atk(R, f"est05_message_onechar_{cid}")
    assert M.case_of(r, cid)["verdict"] == FAIL and r["overall"] == FAIL
    assert [o["id"] for o in M.case_of(r, cid)["observations"] if o["status"] == "violated"] == [f"{cid}.2"]


@pytest.mark.parametrize("cid,pos", [("QA-03", 0), ("QA-03", 5), ("QA-05", 0), ("QA-05", 7), ("QA-12", 3), ("QA-25", 9), ("QA-19", 2), ("QA-18", 4), ("QA-22", 6)])
def test_est05_one_character_change_anywhere_in_the_message(R, cid, pos):
    """EST-05: for 'contains' the mutated character must lie inside the expected substring to matter; equals: anywhere."""
    exp_ob = [o for o in M.CASES[cid]["observations"] if o["op"].startswith("raised_message")][0]
    exp = exp_ob["expected"]
    i = min(pos, len(exp) - 1)
    mutated = exp[:i] + ("~" if exp[i] != "~" else "^") + exp[i + 1:]
    r = M._run(R, lambda b: b.raw[M.rawrel(b, cid, M.exc_boundary(cid))].__setitem__("message", mutated))
    assert M.case_of(r, cid)["verdict"] == FAIL


def test_est05_equals_vs_contains_semantics(R):
    """EST-05: 'equals' (QA-05/12/25) rejects surrounding text; 'contains' (QA-03/19) tolerates it but not a truncation."""
    for cid in ("QA-05", "QA-12", "QA-25"):
        assert [o["op"] for o in M.CASES[cid]["observations"]][1] == "raised_message_equals"
        exp = M.CASES[cid]["observations"][1]["expected"]
        for msg in (exp + " ", " " + exp, exp + "\n", exp.upper(), exp[:-1]):
            r = M._run(R, lambda b, m=msg: b.raw[M.rawrel(b, cid, M.exc_boundary(cid))].__setitem__("message", m))
            assert M.case_of(r, cid)["verdict"] == FAIL, (cid, msg)
    for cid in ("QA-03", "QA-19"):
        assert M.CASES[cid]["observations"][1]["op"] == "raised_message_contains"
        exp = M.CASES[cid]["observations"][1]["expected"]
        ok = M._run(R, lambda b: b.raw[M.rawrel(b, cid, M.exc_boundary(cid))].__setitem__("message", f"X: {exp} (detail)"))
        assert M.case_of(ok, cid)["verdict"] == PASS, "contains must tolerate surrounding text"
        bad = M._run(R, lambda b: b.raw[M.rawrel(b, cid, M.exc_boundary(cid))].__setitem__("message", exp[:-1]))
        assert M.case_of(bad, cid)["verdict"] == FAIL
        case_swapped = M._run(R, lambda b: b.raw[M.rawrel(b, cid, M.exc_boundary(cid))].__setitem__("message", exp.swapcase()))
        assert M.case_of(case_swapped, cid)["verdict"] == FAIL


def test_est05_exception_type_is_exact_not_substring(R):
    """EST-05: the exception TYPE is compared exactly (prefix/suffix/base-class names fail)."""
    for cid in ("QA-03", "QA-19", "QA-12"):
        t = M.CASES[cid]["observations"][0]["expected"]
        for bad in (t + "x", "x" + t, t.rsplit(".", 1)[1], "builtins.Exception", t.upper()):
            r = M._run(R, lambda b, v=bad: b.raw[M.rawrel(b, cid, M.exc_boundary(cid))].__setitem__("type", v))
            assert M.case_of(r, cid)["verdict"] == FAIL, (cid, bad)


# ------------------------------------------------------------------ EST-06
def test_est06_case_swap(R):
    """EST-06: swapping two cases' evidence cannot produce a PASS."""
    r = atk(R, "est06_case_swap")
    assert M.case_of(r, "QA-03")["verdict"] == FAIL and M.case_of(r, "QA-05")["verdict"] == FAIL
    assert r["overall"] == FAIL


def test_est06_dropped_case_is_not_run_never_pass(R):
    """EST-06: a dropped mandatory case => that case NOT RUN and overall NOT RUN."""
    r = atk(R, "est06_dropped_case")
    c = M.case_of(r, "QA-12")
    assert c["verdict"] == NR and c["executed"] is False and r["overall"] == NR
    assert r["executed_mandatory_cases"] == 21 and r["mandatory_cases"] == 22


def test_est06_zero_cases(R):
    """EST-06: a bundle with zero cases is NOT RUN, never PASS."""
    r = atk(R, "est06_zero_cases")
    assert r["overall"] == NR and r["claim_basis"] == NR and r["executed_mandatory_cases"] == 0
    assert all(c["verdict"] == NR for c in r["cases"] if c["mandatory"])


def test_est06_extra_unknown_case_id(R):
    """EST-06: an unknown extra case id is a violation => overall and claim basis FAIL."""
    r = atk(R, "est06_unknown_case_id")
    assert r["overall"] == FAIL and r["claim_basis"] == FAIL
    assert any("QA-99" in v for v in r["violations"])


def test_est06_duplicate_json_key_in_bundle(R):
    """EST-06: a duplicate JSON key in bundle.json (even with a correct external hash) => BUNDLE_UNREADABLE NOT RUN."""
    r = atk(R, "est06_duplicate_json_key_bundle")
    assert r["overall"] == NR and r["blocked_reason"].startswith("BUNDLE_UNREADABLE")
    assert "duplicate" in r["blocked_reason"]
    assert all(c["verdict"] == NR for c in r["cases"] if c["mandatory"])


def test_est06_duplicate_case_key_in_bundle(R):
    """EST-06: two entries for the same case id (last-one-wins forgery) are refused at parse time."""
    b = M.G()
    text = b.render()[1].decode()
    i = text.index('"QA-01": {')
    b.bundle_bytes = (text[:i] + '"QA-01": {"executed": false}, ' + text[i:]).encode()
    r = R.run(b)
    assert r["overall"] == NR and r["blocked_reason"].startswith("BUNDLE_UNREADABLE")


# ------------------------------------------------------------------ EST-07
def test_est07_evidence_hash_lie_fails(R):
    """EST-07: raw_index hash for a raw file does not match its bytes => FAIL (tampered), not unevaluable."""
    r = atk(R, "est07_raw_hash_lie")
    assert r["overall"] == FAIL and M.case_of(r, "QA-01")["verdict"] == FAIL
    assert "sha256" in M.obs_of(r, "QA-01", "QA-01.11")["detail"]


def test_est07_cross_artifact_hash_conflation_fails(R):
    """EST-07: index entry of file A holds the sha of file B => FAIL."""
    r = atk(R, "est07_cross_artifact_hash")
    assert r["overall"] == FAIL and M.case_of(r, "QA-01")["verdict"] == FAIL


def test_est07_files_swapped_under_consistent_hashes_do_not_pass(R):
    """EST-07: A and B contents swapped with a self-consistent index => values wrong => never PASS."""
    a, b_ = M._A, M._B
    def mut(b):
        b.raw[a], b.raw[b_] = b.raw[b_], b.raw[a]
    r = M._run(R, mut)
    assert r["overall"] != PASS and M.case_of(r, "QA-01")["verdict"] in (FAIL, INC)


def test_est07_missing_raw_file_is_inconclusive(R):
    """EST-07: a missing raw file => INCONCLUSIVE."""
    r = atk(R, "est07_missing_raw_file")
    assert r["overall"] == INC and M.case_of(r, "QA-01")["verdict"] == INC
    assert M.obs_of(r, "QA-01", "QA-01.11")["status"] == "unevaluable"


def test_est07_non_json_raw_is_inconclusive(R):
    """EST-07: non-JSON raw content (hash consistent) => INCONCLUSIVE."""
    r = atk(R, "est07_non_json_raw")
    assert r["overall"] == INC and M.case_of(r, "QA-01")["verdict"] == INC


# ------------------------------------------------------------------ EST-08
def test_est08_late_oracle_mutation_is_oracle_drift(R):
    """EST-08: a one-byte oracle edit => overall NOT RUN, ORACLE_DRIFT, every mandatory case NOT RUN."""
    mod = M._flip_oracle_byte()
    assert len(mod) == len(M.ORC_BYTES) and sum(x != y for x, y in zip(mod, M.ORC_BYTES)) == 1
    r = atk(R, "est08_oracle_one_byte")
    assert r["overall"] == NR and r["claim_basis"] == NR and r["blocked_reason"].startswith("ORACLE_DRIFT")
    mand = [c for c in r["cases"] if c["mandatory"]]
    assert len(mand) == 22 and all(c["verdict"] == NR and c["executed"] is False for c in mand)


def test_est08_oracle_change_that_alters_expectations_is_still_drift(R):
    """EST-08: an oracle edit that turns a FAIL into a PASS is refused by the pin before any evaluation."""
    wrong = M.G()
    M.setv(wrong, "QA-02", "cp_record", "/decisions/0/result", "authorized")
    ob, _ = own_oracle(lambda o: next(x for c in o["cases"] if c["id"] == "QA-02" for x in c["observations"] if x["id"] == "QA-02.11").__setitem__("expected", "authorized"))
    assert R.run(wrong, oracle_bytes=ob, oracle_sha=M.sha(ob))["overall"] != FAIL   # the weakened oracle WOULD hide it ...
    r = R.run(wrong, oracle_bytes=ob)                                               # ... the committed pin refuses it
    assert r["overall"] == NR and r["blocked_reason"].startswith("ORACLE_DRIFT")


def test_est08_freeze_drift_blocks(R):
    """EST-08: freeze drift passed as extra_block => NOT RUN with the reason verbatim."""
    r = atk(R, "est08_freeze_drift")
    assert r["overall"] == NR and r["blocked_reason"] == "FREEZE_DRIFT: changed file ia_eval/engine.py"
    assert all(c["verdict"] == NR for c in r["cases"] if c["mandatory"])


def test_est08_wrong_expected_bundle_sha_is_bundle_drift(R):
    """EST-08: wrong expect_bundle_sha256 => NOT RUN BUNDLE_DRIFT."""
    r = atk(R, "est08_bundle_hash_mismatch")
    assert r["overall"] == NR and r["blocked_reason"].startswith("BUNDLE_DRIFT")
    r2 = R.run(M.G(), bundle_sha=None)
    assert r2["overall"] == PASS


def test_est08_bundle_edited_after_pin_and_non_string_pins(R):
    """EST-08: bundle.json appended to after the pin is taken => BUNDLE_DRIFT; non-str pins never match."""
    b = M.G()
    pin = M.sha(b.render()[1])
    R.stage(b)
    (R.base / "bundle.json").write_bytes((R.base / "bundle.json").read_bytes() + b" ")
    from ia_eval import engine
    r = engine.run(M.ORC_BYTES, R.base, M.ORC_SHA, pin)
    assert r["overall"] == NR and r["blocked_reason"].startswith("BUNDLE_DRIFT")
    for bad in (None, 0, ["x"], b"x"):
        assert engine.run(M.ORC_BYTES, R.base, M.ORC_SHA, bad)["overall"] == NR
        assert engine.run(M.ORC_BYTES, R.base, bad, pin)["overall"] == NR


def test_est08_raw_file_edited_after_bundle_pin_is_hash_failure(R):
    """EST-08: the bundle pin does not cover raw bytes; the raw_index hash does. Edit a raw file => FAIL."""
    b = M.G()
    R.stage(b)
    pin = M.sha((R.base / "bundle.json").read_bytes())
    p = R.base / M._A
    d = json.loads(p.read_text())
    d["decisions"][0]["result"] = "denied"
    p.write_text(json.dumps(d))
    from ia_eval import engine
    r = engine.run(M.ORC_BYTES, R.base, M.ORC_SHA, pin)
    assert r["overall"] == FAIL and M.case_of(r, "QA-01")["verdict"] == FAIL


def test_est08_oracle_not_json_and_invalid_are_not_run(R):
    """EST-08: unreadable or invalid oracles (even with their own sha) never produce a verdict above NOT RUN."""
    r = atk(R, "est08_oracle_not_json")
    assert r["overall"] == NR and r["blocked_reason"].startswith("ORACLE_UNREADABLE")
    r = atk(R, "oracle_invalid_pinned")
    assert r["overall"] == NR and r["blocked_reason"].startswith("ORACLE_INVALID")


# ------------------------------------------------------------------ EST-09
IA = Path(M.PKG) / "ia_eval"
FORBIDDEN_IMPORTS = {"subprocess", "socket", "urllib", "http", "requests", "ctypes", "multiprocessing", "pickle", "yaml",
                     "importlib", "runpy", "shutil", "tempfile", "ssl", "asyncio", "threading", "ftplib", "smtplib", "xmlrpc", "webbrowser", "marshal", "imp"}
FORBIDDEN_TOKENS = ("real_c4", "c4_hosted_check", "c4_producer")
FORBIDDEN_CALLS = {"eval", "exec", "compile", "__import__"}
FORBIDDEN_OS_ATTRS = {"system", "popen", "fork", "forkpty", "kill", "startfile"}
ALLOWED_IMPORTS = {"__future__", "argparse", "hashlib", "json", "re", "sys", "pathlib"}
WRITE_ATTRS = {"write_text", "write_bytes", "mkdir", "unlink", "rmdir", "rename", "touch", "symlink_to", "write", "makedirs", "remove", "replace_file"}


def scan(src: str):
    """Return {'imports': set, 'calls': set, 'os_attrs': set, 'open_modes': list, 'write_calls': set}."""
    t = ast.parse(src)
    out = {"imports": set(), "calls": set(), "os_attrs": set(), "open_modes": [], "write_calls": set()}
    for n in ast.walk(t):
        if isinstance(n, ast.Import):
            out["imports"] |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            if n.level == 0 and n.module:
                out["imports"].add(n.module.split(".")[0])
                if n.module == "os":
                    out["os_attrs"] |= {a.name for a in n.names}
        elif isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                out["calls"].add(f.id)
                if f.id == "open":
                    mode = n.args[1] if len(n.args) > 1 else next((k.value for k in n.keywords if k.arg == "mode"), None)
                    out["open_modes"].append(mode.value if isinstance(mode, ast.Constant) else "<dynamic>" if mode else "r")
            elif isinstance(f, ast.Attribute):
                out["write_calls"].add(f.attr) if f.attr in WRITE_ATTRS | {"open"} else None
                if f.attr == "open":
                    mode = n.args[0] if n.args else next((k.value for k in n.keywords if k.arg == "mode"), None)
                    out["open_modes"].append(mode.value if isinstance(mode, ast.Constant) else "r" if mode is None else "<dynamic>")
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "os":
            out["os_attrs"].add(n.attr)
    return out


def modules():
    return sorted(IA.glob("*.py"))


def test_est09_scanner_has_teeth():
    """EST-09: the scanner flags each forbidden construct in a synthetic module (so a clean scan means something)."""
    s = scan("import subprocess\nfrom os import system\nimport os\nos.popen('x')\neval('1')\nopen('f','w')\nfrom pathlib import Path\nPath('x').write_text('y')\n")
    assert "subprocess" in s["imports"] and "system" in s["os_attrs"] and "popen" in s["os_attrs"]
    assert "eval" in s["calls"] and s["open_modes"] == ["w"] and "write_text" in s["write_calls"]
    assert scan("import urllib.request")["imports"] == {"urllib"}
    assert scan("p.open('x')")["open_modes"] == ["x"]


def test_est09_modules_found():
    names = {p.name for p in modules()}
    assert {"engine.py", "predicates.py", "oracle.py", "guard.py", "freeze.py", "cli.py", "identity.py", "pointer.py", "verdicts.py"} <= names


@pytest.mark.parametrize("mod", [p.name for p in modules()])
def test_est09_no_forbidden_imports_calls_or_references(mod):
    """EST-09: no network/process/serialisation/dynamic-code imports or calls, no C4 producer references."""
    src = (IA / mod).read_text()
    s = scan(src)
    assert not (s["imports"] & FORBIDDEN_IMPORTS), s["imports"] & FORBIDDEN_IMPORTS
    assert s["imports"] <= ALLOWED_IMPORTS, f"unreviewed import(s): {s['imports'] - ALLOWED_IMPORTS}"
    assert not (s["calls"] & FORBIDDEN_CALLS), s["calls"] & FORBIDDEN_CALLS
    assert not (s["os_attrs"] & FORBIDDEN_OS_ATTRS), s["os_attrs"]
    for tok in FORBIDDEN_TOKENS:
        assert tok not in src, tok


@pytest.mark.parametrize("mod", [p.name for p in modules()])
def test_est09_write_mode_open_only_in_cli(mod):
    """EST-09: only cli.py may open a file for writing or create/delete files."""
    s = scan((IA / mod).read_text())
    writes = [m for m in s["open_modes"] if m == "<dynamic>" or any(ch in m for ch in "wax+")]
    if mod == "cli.py":
        assert writes == ["x"], "cli.py must create its --out file exclusively ('x')"
    else:
        assert writes == [] and s["open_modes"] == []
        assert not (s["write_calls"] & {"write_text", "write_bytes", "mkdir", "unlink", "rmdir", "rename", "touch", "symlink_to", "makedirs", "remove"}), s["write_calls"]


def test_est09_cli_write_surface_is_exactly_known():
    s = scan((IA / "cli.py").read_text())
    assert s["write_calls"] <= {"write_text", "write"}


# ------------------------------------------------------------------ EST-10
def test_est10_weakened_variant_kill_matrix():
    """EST-10: every weakened RI oracle is distinguishable AND rejected by the pin; every non-equivalent engine mutant is killed."""
    v = M.memo_variants()
    assert len(v) >= 40
    assert [x for x in v if not x["killed"]] == []
    m = M.memo_mutants()
    assert [x["id"] for x in m if not x["killed"] and not x["equivalent"]] == []
    assert len(m) >= 62 and sum(x["killed"] for x in m) >= 58


# ------------------------------------------------------------------ EST-11
OBS_CASES = ["QA-09", "QA-11", "QA-17", "QA-26", "QA-OBS-EXACT"]


def _obs_dev(cid):
    c = M.CASES[cid]
    ob = next(o for o in c["observations"] if o["op"] not in ("returned",) and not o["op"].startswith("raised"))
    return next(v for v in M.obs_variants(M.gold(), c, ob) if v[2] == "violated" and "raises" not in v[0])[1]


@pytest.mark.parametrize("cid", OBS_CASES)
def test_est11_obs_deviation_fails_and_validates_nothing(R, cid):
    """EST-11: an OBS case with observation deviation => FAIL and overall FAIL; never a security PASS."""
    r = R.run(_obs_dev(cid))
    c = M.case_of(r, cid)
    assert c["verdict"] == FAIL and c["observation_result"] == "DEVIATES_FROM_FROZEN_OBSERVATION"
    assert c["security_property_validated"] is False and c["claim_gated"] is False
    assert r["overall"] == FAIL and r["obs_summary"][cid] == "DEVIATES_FROM_FROZEN_OBSERVATION"


@pytest.mark.parametrize("cid", OBS_CASES)
def test_est11_obs_match_is_observed_as_frozen_not_validated(R, cid):
    """EST-11: OBS match => security_property_validated False, claim_gated False, OBSERVED_AS_FROZEN."""
    r = R.run(M.G())
    c = M.case_of(r, cid)
    assert c["verdict"] == PASS and c["observation_result"] == "OBSERVED_AS_FROZEN"
    assert c["security_property_validated"] is False and c["claim_gated"] is False
    assert r["obs_summary"][cid] == "OBSERVED_AS_FROZEN"


def test_est11_claim_basis_identical_whether_obs_pass_or_not_run(R):
    """EST-11: claim_basis does not depend on OBS; overall does (NOT RUN when OBS are skipped)."""
    a = R.run(M.G())
    b = M.G()
    for cid in OBS_CASES:
        b.cases[cid]["executed"] = False
    r = R.run(b)
    assert a["claim_basis"] == r["claim_basis"] == PASS
    assert a["overall"] == PASS and r["overall"] == NR
    assert all(M.case_of(r, c)["verdict"] == NR for c in OBS_CASES)
    assert r["obs_summary"] == {c: "NOT_OBSERVED" for c in OBS_CASES}
    dev = R.run(_obs_dev("QA-11"))
    assert dev["claim_basis"] == PASS and dev["overall"] == FAIL    # by design: OBS never validates and never gates the claim


def test_est11_obs_pass_cannot_rescue_a_gated_failure(R):
    """EST-11: all five OBS cases PASS while a gated case FAILs => claim basis FAIL."""
    r = M._run(R, lambda b: M.setv(b, "QA-S1", "source_identity", "/commits/orchestrator", "0" * 40))
    assert all(M.case_of(r, c)["verdict"] == PASS for c in OBS_CASES)
    assert r["claim_basis"] == FAIL and r["overall"] == FAIL


def test_est11_obs_unevaluable(R):
    """EST-11: OBS evidence missing => INCONCLUSIVE/UNEVALUABLE, never PASS."""
    r = M._run(R, lambda b: b.drop_files.add(M.rawrel(b, "QA-17", "pack")))
    c = M.case_of(r, "QA-17")
    assert c["verdict"] == INC and c["observation_result"] == "UNEVALUABLE" and r["overall"] == INC


# ------------------------------------------------------------------ EST-12
RI_REFUSALS = ["QA-03", "QA-05", "QA-10", "QA-12", "QA-18", "QA-19", "QA-22", "QA-25"]


@pytest.mark.parametrize("cid", RI_REFUSALS)
def test_est12_boundary_returns_where_source_says_refuse(R, cid):
    """EST-12: a stub that returns success where the native source refuses => FAIL."""
    r = atk(R, f"est12_returns_instead_of_refusing_{cid}")
    c = M.case_of(r, cid)
    assert c["verdict"] == FAIL and r["overall"] == FAIL and r["claim_basis"] == FAIL
    assert "returned" in c["observations"][0]["detail"]


def test_est12_boundary_raises_where_a_return_is_required(R):
    """EST-12: raising where the oracle requires a return => FAIL (OBS `returned`, and value predicates)."""
    r = atk(R, "est12_raises_where_return_required_QA-11")
    o = M.obs_of(r, "QA-11", "QA-11.1")
    assert o["status"] == "violated" and "raised where a return was required" in o["detail"]
    assert r["overall"] == FAIL
    r = atk(R, "est12_raises_cp_record_QA-01")
    assert M.case_of(r, "QA-01")["verdict"] == FAIL and r["overall"] == FAIL and r["claim_basis"] == FAIL
    assert "cannot be satisfied" in M.obs_of(r, "QA-01", "QA-01.5")["detail"]


def test_est12_outcome_label_lies(R):
    """EST-12: the outcome label is never trusted; label vs evidence disagreement is unevaluable."""
    for name in ("label_lie_returned_but_raised", "label_lie_raised_with_both"):
        r = atk(R, name)
        assert M.case_of(r, "QA-03")["verdict"] == INC and r["overall"] == INC, name
    b = M.G()
    b.cases["QA-03"]["boundaries"]["pack_import"]["outcome"] = "success"
    assert M.case_of(R.run(b), "QA-03")["verdict"] == INC
