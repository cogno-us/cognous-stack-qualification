"""Kill matrices: (a) every observation of every mandatory case against wrong-value variants, (b) weakened RI oracles and
engine mutants. A survivor means the evaluator (or the oracle) cannot tell a wrong value from the right one."""
from __future__ import annotations

import pytest

import selftest_matrix as M
from ia_eval import engine, verdicts as V


@pytest.fixture
def R(tmp_path):
    return M.Runner(tmp_path / "b")


# ----------------------------------------------------------------- (a) per-observation kill
@pytest.mark.parametrize("cid", M.MAND)
def test_every_observation_is_killed_by_its_wrong_value_variants(R, cid):
    res = M.run_case_matrix(R, cid)
    oracle_ids = [o["id"] for o in M.CASES[cid]["observations"]]
    assert list(res["observations"]) == oracle_ids
    survivors = {oid: {n: v for n, v in d["variants"].items() if not v["killed"]} for oid, d in res["observations"].items()}
    survivors = {k: v for k, v in survivors.items() if v}
    assert survivors == {}, survivors
    for oid, d in res["observations"].items():
        value_variants = [n for n in d["variants"] if "raises" not in n and "returns" not in n]
        op = next(o["op"] for o in M.CASES[cid]["observations"] if o["id"] == oid)
        assert len(d["variants"]) >= 2 or op == "returned", (oid, "too few variants to be a meaningful kill test")
        if op != "returned":
            assert value_variants, f"{oid}: no value-level wrong variant, only structural ones"
    assert {k: v for b in res["boundaries"].values() for k, v in b["variants"].items() if not v["killed"]} == {}
    assert {k: v for k, v in res["case_level"].items() if not v["killed"]} == {}


def test_kill_matrix_covers_every_observation_of_every_mandatory_case():
    total = sum(len(c["observations"]) for c in M.ORC["cases"] if c["mandatory"])
    assert total == 142
    seen = 0
    for c in M.ORC["cases"]:
        if c["mandatory"]:
            for ob in c["observations"]:
                assert M.obs_variants(M.gold(), c, ob), ob["id"]
                seen += 1
    assert seen == total


def test_every_oracle_op_has_a_variant_generator_and_a_kill():
    ops = {ob["op"] for c in M.ORC["cases"] if c["mandatory"] for ob in c["observations"]}
    assert ops >= {"eq", "int_eq", "is_null", "seq_eq", "len_eq", "sha256_format", "list_contains", "any_item_matches", "none_item_matches",
                   "eq_ref", "ne_ref", "returned", "raised_type", "raised_message_contains", "raised_message_equals"}
    for op in ops:
        c, ob = next((c, ob) for c in M.ORC["cases"] if c["mandatory"] for ob in c["observations"] if ob["op"] == op)
        assert len(M.obs_variants(M.gold(), c, ob)) >= 1


def test_wrong_value_variants_really_differ_from_golden():
    """The variants are not no-ops: each differs from the golden bundle in raw content, cases or index."""
    g = M.gold()
    base_files, base_b = g.render()
    for c in M.ORC["cases"]:
        if not c["mandatory"]:
            continue
        for ob in c["observations"][:6]:
            for name, b, _w in M.obs_variants(g, c, ob):
                f, bb = b.render()
                assert (f, bb) != (base_files, base_b), (ob["id"], name)


def test_matrix_summary_counts():
    km = M.memo("km", lambda: M.kill_matrix(M.memo_runner().base.parent))
    n = M.matrix_counts(km)
    assert n["observations_total"] == n["observations_killed"] == 142
    assert n["variants_total"] == n["variants_killed"] >= 900


# ----------------------------------------------------------------- (b1) weakened RI oracles
def _variant_ids():
    return [f"{s['case']}/{s['variant']}" for s in M.weakened_oracle_variants()]


def test_ri_weakened_variants_cover_every_ri_case():
    cov = {s["case"] for s in M.weakened_oracle_variants()}
    assert cov == {c["id"] for c in M.ORC["cases"] if c["class"] == "RI"}
    assert len(_variant_ids()) == len(set(_variant_ids()))


@pytest.mark.parametrize("spec", list(M.weakened_oracle_variants()), ids=lambda s: f"{s['case']}-{s['variant']}")
def test_weakened_ri_oracle_is_killable_and_rejected_by_pin(R, spec):
    res = M.run_weakened(R, spec)
    assert res["real_oracle_verdict"] == V.FAIL, res
    assert res["weakened_oracle_verdict"] != V.FAIL, f"variant is not distinguishable (the weakening hides nothing here): {res}"
    assert res["rejected_by_pinned_hash"], res
    assert res["killed"]


def test_weakened_oracle_with_its_own_sha_would_hide_the_attack(R):
    """Control for the pin: the weakened oracle, if its own hash were trusted, yields PASS on the attacked bundle."""
    spec = next(s for s in M.weakened_oracle_variants() if s["case"] == "QA-05" and s["variant"].startswith("drop:"))
    vb = (__import__("json").dumps(spec["oracle"], sort_keys=True, indent=1) + "\n").encode()
    r = R.run(spec["wrong_bundle"], oracle_bytes=vb, oracle_sha=M.sha(vb))
    assert M.case_of(r, "QA-05")["verdict"] == V.PASS and r["overall"] in (V.PASS, V.FAIL)
    assert R.run(spec["wrong_bundle"])["overall"] == V.FAIL


# ----------------------------------------------------------------- (b2) engine mutants
def test_mutant_harness_is_not_vacuous(R):
    """A no-op patch is NOT killed (signatures equal), a real mutation is: the kill signal comes from behaviour."""
    base = M.memo_base_sigs()
    noop = M.run_mutant({"id": "noop", "desc": "", "patches": lambda: [], "equivalent": None}, R, base)
    assert noop["killed"] is False
    real = M.run_mutant({"id": "x", "desc": "", "patches": lambda: [("attr", engine.guard, "check_events", lambda e, a: [])], "equivalent": None}, R, base)
    assert real["killed"] is True


def test_patches_are_restored_after_mutants():
    M.memo_mutants()
    r = M.memo_runner().run(M.G())
    assert r["overall"] == V.PASS


def test_mutant_set_is_broad_enough():
    ids = [m["id"] for m in M.MUTANTS]
    assert len(ids) == len(set(ids)) >= 62
    required = ["deq_type_loose", "combine_ignores_inconclusive", "combine_empty_is_pass", "missing_pointer_defaults_none",
                "hash_verification_disabled", "outcome_label_trusted", "paired_control_downgrade_removed", "check_events_empty",
                "claim_basis_ignores", "executed_flag_not_checked", "blocked_is_missing", "commitment_trusts_driver", "relation_alias_rule_removed"]
    for r in required:
        assert any(r in i for i in ids), r


@pytest.mark.parametrize("mut", M.MUTANTS, ids=lambda m: m["id"])
def test_engine_mutant_is_killed(mut):
    res = M.run_mutant(mut, M.memo_runner(), M.memo_base_sigs())
    if mut["equivalent"]:
        # a documented equivalent mutant must stay unobservable through the engine; if it becomes observable the note is stale
        assert res["killed"] is False, f"{mut['id']} is documented as equivalent but was killed by {res['killed_by']}"
        return
    assert res["killed"], f"SURVIVING MUTANT {mut['id']}: {mut['desc']}"
    assert res["killed_by"]


def test_equivalent_mutants_are_justified_and_unit_tested_elsewhere():
    eq = {m["id"]: m["equivalent"] for m in M.MUTANTS if m["equivalent"]}
    assert set(eq) == {"M09_zero_executed_rule_removed", "M37_combine_empty_is_pass", "G7_effect_regex_removed"}
    assert all(len(v) > 40 for v in eq.values())
