"""The Architect's explicit list: missing bindings, nonzero effect counters, skipped cases, zero-case success,
altered source/fixture hashes, corrupted evidence index, H1/H2 confusion, wrong refusal messages, paired controls."""
from __future__ import annotations

import pytest

import selftest_matrix as M
from ia_eval import verdicts as V

PASS, FAIL, INC, NR = V.PASS, V.FAIL, V.INCONCLUSIVE, V.NOT_RUN
CNT = M._CNT


@pytest.fixture
def R(tmp_path):
    return M.Runner(tmp_path / "b")


def verdicts(r):
    return M.vmap(r)


# ---------------------------------------------------------------- missing native binding
def test_missing_native_binding_in_pos_is_inconclusive(R):
    """POS binding removed (evidence missing) => the binding observations are unevaluable => INCONCLUSIVE, never PASS."""
    r = M.ATTACKS["arch_binding_removed"]["fn"](R)
    assert M.case_of(r, "QA-01")["verdict"] == INC
    assert {o["id"] for o in M.case_of(r, "QA-01")["observations"] if o["status"] == "unevaluable"} == {"QA-01.13", "QA-01.14", "QA-01.15", "QA-01.16"}
    assert r["overall"] == INC and r["claim_basis"] == INC


def test_native_binding_set_null_in_pos_is_fail(R):
    """POS binding explicitly null (a present, wrong value) must be FAIL, not 'missing evidence'.
    D1 (FIXED): a null parent yields the BLOCKED sentinel => violated."""
    r = M.ATTACKS["arch_binding_null"]["fn"](R)
    assert M.case_of(r, "QA-01")["verdict"] == FAIL, verdicts(r)["QA-01"]
    assert r["overall"] == FAIL


def test_binding_present_on_hold_is_fail(R):
    """QA-02 (hold) carrying a binding object is a violation (binding must be null)."""
    r = M._run(R, lambda b: M.setv(b, "QA-02", "cp_record", "/decisions/0/binding", {"tenant_id": "tenant-alpha"}))
    assert M.obs_of(r, "QA-02", "QA-02.12")["status"] == "violated" and r["overall"] == FAIL


def test_binding_commitment_conflicts_fail(R):
    """Binding proposal/manifest commitment different from AM digests => FAIL (relations)."""
    for ptr, oid in (("/decisions/0/binding/proposal_commitment", "QA-01.13"), ("/decisions/0/binding/manifest_digest", "QA-01.14")):
        r = M._run(R, lambda b, p=ptr: M.setv(b, "QA-01", "cp_record", p, "sha256:" + "9" * 64))
        assert M.obs_of(r, "QA-01", oid)["status"] == "violated" and r["overall"] == FAIL


# ---------------------------------------------------------------- nonzero attempt/effect counters
@pytest.mark.parametrize("name", M.PACK_COUNTS)
def test_nonzero_pack_effect_or_attempt_counter_fails(R, name):
    """Each of the six Pack counts nonzero => QA-01 FAIL (and overall/claim basis FAIL)."""
    r = M.ATTACKS[f"arch_pack_count_nonzero_{name}"]["fn"](R)
    assert M.case_of(r, "QA-01")["verdict"] == FAIL and r["overall"] == FAIL and r["claim_basis"] == FAIL


@pytest.mark.parametrize("name", M.PACK_COUNTS)
def test_nonzero_pack_counter_in_hold_case_fails(R, name):
    """The same six counters in the HOLD (QA-02) Pack."""
    r = M._run(R, lambda b: M.setv(b, "QA-02", "pack", CNT + name, 1))
    assert M.case_of(r, "QA-02")["verdict"] == FAIL and r["overall"] == FAIL


@pytest.mark.parametrize("name", ["attempts", "observations", "reconciliations"])
def test_nonzero_cp_attempts_observations_reconciliations_fail(R, name):
    """CP attempts/observations/reconciliations nonzero => FAIL."""
    r = M.ATTACKS[f"arch_cp_{name}_nonzero"]["fn"](R)
    assert M.case_of(r, "QA-01")["verdict"] == FAIL and r["overall"] == FAIL
    assert M.obs_of(r, "QA-01", {"attempts": "QA-01.6", "observations": "QA-01.7", "reconciliations": "QA-01.8"}[name])["status"] == "violated"


def test_replay_semantics_effect_flags_flipped_fail(R):
    """external_effect_execution true / destination_observation performed => FAIL."""
    for ptr, val, oid in (("/semantics/external_effect_execution", True, "QA-01.21"), ("/semantics/destination_observation", "performed", "QA-01.22"),
                          ("/semantics/policy_reevaluation", True, "QA-01.23")):
        r = M._run(R, lambda b, p=ptr, v=val: M.setv(b, "QA-01", "replay_bundle", p, v))
        assert M.obs_of(r, "QA-01", oid)["status"] == "violated" and r["overall"] == FAIL


# ---------------------------------------------------------------- skipped case / zero case
def test_skipped_case_is_not_run_and_overall_not_run(R):
    """executed false => NOT RUN for the case and for overall; never PASS even though all its data is present and correct."""
    r = M.ATTACKS["arch_skipped_case"]["fn"](R)
    c = M.case_of(r, "QA-08")
    assert c["verdict"] == NR and c["executed"] is False and c["observations"] == []
    assert r["overall"] == NR and r["claim_basis"] == NR
    assert r["executed_mandatory_cases"] == 21
    assert [k for k, v in verdicts(r).items() if v == PASS and k != "QA-08"] and verdicts(r)["QA-01"] == PASS


@pytest.mark.parametrize("val", [1, "true", "yes", 1.0, [], {}, None])
def test_non_boolean_executed_flag_is_not_execution(R, val):
    """Only the JSON literal true counts as executed."""
    r = M._run(R, lambda b: b.cases["QA-08"].__setitem__("executed", val))
    assert M.case_of(r, "QA-08")["verdict"] == NR and r["overall"] == NR


def test_zero_case_success_is_not_pass(R):
    """A bundle with zero cases (and empty everything) can never succeed."""
    r = M.ATTACKS["est06_zero_cases"]["fn"](R)
    assert r["overall"] == NR and r["claim_basis"] == NR
    b = M.G()
    b.cases.clear()
    b.raw.clear()
    b.driver_events = []
    r2 = R.run(b)
    assert r2["overall"] == NR and r2["claim_basis"] == NR and r2["executed_mandatory_cases"] == 0


def test_all_cases_present_but_not_executed(R):
    """Every case present with data but executed=false => NOT RUN overall."""
    b = M.G()
    for c in b.cases.values():
        c["executed"] = False
    r = R.run(b)
    assert r["overall"] == NR and r["claim_basis"] == NR and r["executed_mandatory_cases"] == 0


def test_empty_case_dicts_are_not_run(R):
    """Cases present as {} (no executed flag, no boundaries)."""
    b = M.G()
    for k in list(b.cases):
        b.cases[k] = {}
    assert R.run(b)["overall"] == NR


# ---------------------------------------------------------------- altered source / fixture hash
def test_altered_source_commit_qa_s1_fails(R):
    r = M.ATTACKS["arch_source_commit_altered_QA-S1"]["fn"](R)
    assert M.case_of(r, "QA-S1")["verdict"] == FAIL and M.obs_of(r, "QA-S1", "QA-S1.1")["status"] == "violated"
    assert r["overall"] == FAIL and r["claim_basis"] == FAIL


def test_altered_tree_qa_s1_fails(R):
    r = M._run(R, lambda b: M.setv(b, "QA-S1", "source_identity", "/trees/control_plane", "0" * 40))
    assert M.obs_of(r, "QA-S1", "QA-S1.2")["status"] == "violated" and r["claim_basis"] == FAIL


def test_altered_fixture_hash_qa_s2_fails(R):
    r = M.ATTACKS["arch_fixture_hash_altered_QA-S2"]["fn"](R)
    assert M.case_of(r, "QA-S2")["verdict"] == FAIL and r["overall"] == FAIL and r["claim_basis"] == FAIL


def test_altered_git_blob_qa_s2_fails(R):
    k = "am:examples/refund_integration_v1_1.manifest.json"
    r = M._run(R, lambda b: M.edit_dict(b, "QA-S2", "file_identity", "/git_blob", lambda d: d.__setitem__(k, M.flip(d[k]))))
    assert M.obs_of(r, "QA-S2", "QA-S2.2")["status"] == "violated" and M.obs_of(r, "QA-S2", "QA-S2.1")["status"] == "ok"


def test_missing_or_extra_identity_entry_fails(R):
    """A fixture dropped from (or added to) the identity map is not the pinned identity."""
    k = "am:examples/refund_integration_v1_1.manifest.json"
    r = M._run(R, lambda b: M.edit_dict(b, "QA-S2", "file_identity", "/sha256", lambda d: d.pop(k)))
    assert M.case_of(r, "QA-S2")["verdict"] == FAIL
    r = M._run(R, lambda b: M.edit_dict(b, "QA-S2", "file_identity", "/sha256", lambda d: d.__setitem__("extra:file", "0" * 64)))
    assert M.case_of(r, "QA-S2")["verdict"] == FAIL


def test_snapshot_and_artifact_identity_altered_fail(R):
    r = M._run(R, lambda b: M.edit_dict(b, "QA-S3", "snapshot_identity", "/sha256", lambda d: d.__setitem__("6660913875", "0" * 64)))
    assert M.case_of(r, "QA-S3")["verdict"] == FAIL
    r = M._run(R, lambda b: M.edit_dict(b, "QA-E1", "artifact_identity", "/zip_sha256", lambda d: d.__setitem__("13433583494", "0" * 64)))
    assert M.case_of(r, "QA-E1")["verdict"] == FAIL


# ---------------------------------------------------------------- corrupted evidence index
def test_evidence_index_not_a_dict_is_schema_invalid(R):
    r = M.ATTACKS["arch_raw_index_not_dict"]["fn"](R)
    assert r["overall"] == NR and r["blocked_reason"] == "BUNDLE_SCHEMA_INVALID"


@pytest.mark.parametrize("name", ["arch_raw_index_entry_removed", "arch_raw_index_entry_int"])
def test_evidence_index_entry_missing_or_non_string_is_inconclusive(R, name):
    r = M.ATTACKS[name]["fn"](R)
    assert M.case_of(r, "QA-01")["verdict"] == INC and r["overall"] == INC


def test_evidence_index_wrong_schema_or_type(R):
    for edit in (lambda d: d.__setitem__("schema", "ia-observation-bundle/2"), lambda d: d.__setitem__("cases", []),
                 lambda d: d.__setitem__("raw_index", None), lambda d: d.pop("cases")):
        b = M.G()
        b.edit.append(edit)
        r = R.run(b)
        assert r["overall"] == NR and r["blocked_reason"] == "BUNDLE_SCHEMA_INVALID"


def test_evidence_index_hashes_with_wrong_case_or_prefix_do_not_verify(R):
    rel = M._A
    good = M.sha(M.ser(M.gold().raw[rel]))
    for bad in (good.upper(), "sha256:" + good, good[:-1], " " + good):
        r = M._run(R, lambda b, v=bad: b.index_over.__setitem__(rel, v))
        assert M.case_of(r, "QA-01")["verdict"] == FAIL, bad


# ---------------------------------------------------------------- H1 / H2 confusion
def test_h1_h2_style_hash_confusion_fails(R):
    """H1 (hash of the exact persisted bundle bytes) must not be conflated with another artifact's hash (H2-style):
    pointing the Pack's replay-bundle input at a different artifact is a relation violation."""
    r = M.ATTACKS["arch_h1_h2_confusion"]["fn"](R)
    assert M.obs_of(r, "QA-01", "QA-01.44")["status"] == "violated" and r["overall"] == FAIL
    r = M.ATTACKS["arch_h1_h2_swapped_inputs"]["fn"](R)
    assert M.obs_of(r, "QA-01", "QA-01.44")["status"] == "violated" and M.obs_of(r, "QA-01", "QA-01.24")["status"] == "violated"


def test_h1_h2_artifact_contents_swapped_between_cases_fail(R):
    r = M.ATTACKS["arch_pair_swapped_cp_records"]["fn"](R)
    assert M.case_of(r, "QA-01")["verdict"] != PASS and r["overall"] != PASS


# ---------------------------------------------------------------- wrong expected refusal message
@pytest.mark.parametrize("cid", ["QA-03", "QA-05", "QA-10", "QA-12", "QA-18", "QA-19", "QA-22", "QA-25"])
def test_wrong_refusal_message_fails_every_refusal_case(R, cid):
    r = M._run(R, lambda b: b.raw[M.rawrel(b, cid, M.exc_boundary(cid))].__setitem__("message", "refused for some other reason"))
    assert M.case_of(r, cid)["verdict"] == FAIL and r["overall"] == FAIL and r["claim_basis"] == FAIL


@pytest.mark.parametrize("cid", ["QA-03", "QA-05", "QA-10", "QA-12", "QA-18", "QA-19", "QA-22", "QA-25"])
def test_right_message_wrong_exception_type_fails(R, cid):
    r = M._run(R, lambda b: b.raw[M.rawrel(b, cid, M.exc_boundary(cid))].__setitem__("type", "builtins.ValueError"))
    assert M.case_of(r, cid)["verdict"] == FAIL


def test_empty_message_and_non_string_exception_evidence(R):
    r = M._run(R, lambda b: b.raw[M.rawrel(b, "QA-05", "pack_import")].__setitem__("message", ""))
    assert M.case_of(r, "QA-05")["verdict"] == FAIL
    for bad in ({"type": 5, "message": "x"}, {"type": "t"}, {"message": "m"}, [], "text", None):
        r = M._run(R, lambda b, v=bad: b.raw.__setitem__(M.rawrel(b, "QA-05", "pack_import"), v))
        assert M.case_of(r, "QA-05")["verdict"] in (INC, FAIL) and r["overall"] != PASS


# ---------------------------------------------------------------- paired controls
def _dependents(ctrl):
    return sorted(c["id"] for c in M.ORC["cases"] if c.get("paired_control") == ctrl)


def test_oracle_pairing_is_as_documented():
    """Pairing is by mutated fixture: HOLD-bundle mutations (QA-03/05) and the HOLD Pack (QA-27) pair with QA-02."""
    assert _dependents("QA-01") == ["QA-08", "QA-10", "QA-12", "QA-16", "QA-18", "QA-19", "QA-22", "QA-25"]
    assert _dependents("QA-02") == ["QA-03", "QA-05", "QA-27"]
    assert all(c.get("paired_control") for c in M.ORC["cases"] if c["class"] == "RI")


def test_breaking_qa01_makes_its_refusals_inconclusive_not_pass(R):
    r = M.ATTACKS["break_QA-01_control"]["fn"](R)
    v = verdicts(r)
    assert v["QA-01"] == FAIL
    for dep in _dependents("QA-01"):
        assert v[dep] == INC, (dep, v[dep])
        assert "paired control QA-01" in M.case_of(r, dep)["reason"]
        assert all(o["status"] == "ok" for o in M.case_of(r, dep)["observations"])   # its own evidence was fine
    for dep in _dependents("QA-02"):
        assert v[dep] == PASS, dep                     # unrelated control: not affected
    assert r["overall"] == FAIL and r["claim_basis"] == FAIL


def test_breaking_qa02_is_the_control_for_qa27_and_the_hold_bundle_refusals(R):
    r = M.ATTACKS["est02_hold_to_authorized"]["fn"](R)
    v = verdicts(r)
    assert v["QA-02"] == FAIL and v["QA-27"] == INC and v["QA-03"] == INC and v["QA-05"] == INC
    assert all(v[d] == PASS for d in _dependents("QA-01"))


@pytest.mark.parametrize("ctrl", ["QA-01", "QA-02"])
def test_control_with_missing_evidence_also_downgrades_dependents(R, ctrl):
    r = M._run(R, lambda b: b.drop_files.add(M.rawrel(b, ctrl, "cp_record")))
    v = verdicts(r)
    assert v[ctrl] == INC
    for dep in _dependents(ctrl):
        assert v[dep] == INC, dep
    assert r["overall"] == INC


def test_control_not_executed_downgrades_dependents_to_inconclusive(R):
    r = M._run(R, lambda b: b.cases["QA-01"].__setitem__("executed", False))
    v = verdicts(r)
    assert v["QA-01"] == NR and all(v[d] == INC for d in _dependents("QA-01"))
    assert r["overall"] == INC and r["claim_basis"] == INC          # INCONCLUSIVE outranks NOT RUN; never PASS


def test_dependent_that_fails_on_its_own_stays_fail_when_control_is_broken(R):
    def mut(b):
        M.setv(b, "QA-01", "cp_record", "/decisions/0/result", "hold")
        b.raw[M.rawrel(b, "QA-19", "am_load")]["message"] = "other"
    r = M._run(R, mut)
    assert verdicts(r)["QA-19"] == FAIL and verdicts(r)["QA-08"] == INC


def test_control_downgrade_only_applies_to_refusal_cases_with_pass(R):
    """A PRE/OBS case is never downgraded by a broken control."""
    r = M.ATTACKS["break_QA-01_control"]["fn"](R)
    v = verdicts(r)
    assert all(v[c] == PASS for c in ("QA-S1", "QA-S2", "QA-S3", "QA-E1", "QA-09", "QA-11", "QA-17", "QA-26", "QA-OBS-EXACT"))
