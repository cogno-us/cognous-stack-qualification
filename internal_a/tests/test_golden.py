"""Golden synthetic bundle: the evaluator must PASS exactly what the oracle freezes, deterministically."""
from __future__ import annotations

import json

import pytest

import selftest_matrix as M
from ia_eval import oracle as O, verdicts as V


@pytest.fixture
def R(tmp_path):
    return M.Runner(tmp_path / "b")


@pytest.fixture
def golden(R):
    return R.run(M.G())


def test_oracle_is_structurally_valid_and_pinned_shape():
    assert O.validate(M.ORC) == []
    assert M.ORC["profile"] == "Q-A-internal-nonproduction"
    assert all(c["class"] in ("PRE", "CTL", "RI", "OBS") for c in M.ORC["cases"] if c["mandatory"])
    assert all(not c["mandatory"] for c in M.ORC["cases"] if c["class"] in ("INFO", "NA"))


def test_golden_overall_and_claim_basis_pass(golden):
    assert golden["overall"] == V.PASS
    assert golden["claim_basis"] == V.PASS
    assert golden["violations"] == []
    assert "blocked_reason" not in golden or not golden.get("blocked_reason")


def test_golden_every_mandatory_case_passes_with_every_observation_ok(golden):
    mand = [c for c in golden["cases"] if c["mandatory"]]
    assert len(mand) == 22
    for c in mand:
        assert c["verdict"] == V.PASS, c["id"]
        assert c["executed"] is True
        assert c["observations"], f"{c['id']} PASS with zero observations"
        assert all(o["status"] == "ok" for o in c["observations"]), c["id"]


def test_golden_info_not_run_and_na_not_applicable(golden):
    info = [c for c in golden["cases"] if c["class"] == "INFO"]
    na = [c for c in golden["cases"] if c["class"] == "NA"]
    assert [c["id"] for c in info] == ["QA-I1", "QA-I2"]
    assert all(c["verdict"] == V.NOT_RUN and c["executed"] is False and not c["mandatory"] for c in info)
    assert all("informational" in c["blocked_reason"] for c in info)
    assert [c["id"] for c in na] == ["QA-14"]
    assert na[0]["verdict"] == V.NOT_APPLICABLE and na[0]["not_applicable_reason"]
    assert not any(c["claim_gated"] for c in info + na)


def test_golden_counts_as_expected(golden):
    assert golden["counts"] == {V.PASS: 22, V.FAIL: 0, V.INCONCLUSIVE: 0, V.NOT_RUN: 2, V.NOT_APPLICABLE: 1}
    assert golden["mandatory_cases"] == 22 and golden["executed_mandatory_cases"] == 22
    assert sum(golden["counts"].values()) == len(M.ORC["cases"]) == 25


def test_mandatory_case_set_equals_oracle_mandatory_set(golden):
    assert [c["id"] for c in golden["cases"]] == [c["id"] for c in M.ORC["cases"]]
    assert {c["id"] for c in golden["cases"] if c["mandatory"]} == set(M.MAND)
    assert len(M.MAND) == len(set(M.MAND))


def test_claim_gating_flags_follow_class(golden):
    for c in golden["cases"]:
        assert c["claim_gated"] == (c["class"] in ("PRE", "CTL", "RI")), c["id"]


def test_golden_obs_cases_observed_as_frozen_and_validate_nothing(golden):
    assert golden["obs_summary"] == {k: "OBSERVED_AS_FROZEN" for k in ("QA-09", "QA-11", "QA-17", "QA-26", "QA-OBS-EXACT")}
    for c in golden["cases"]:
        if c["class"] == "OBS":
            assert c["security_property_validated"] is False and c["claim_gated"] is False


def test_golden_report_pins_and_limit(golden):
    assert golden["oracle_sha256"] == M.ORC_SHA
    assert golden["ignored_orchestrator_status_keys"] == []
    assert "Not independent qualification" in golden["claim_limit"]
    assert "OBS results validate no security property" in golden["claim_limit"]


def test_determinism_two_runs_byte_identical(R, tmp_path):
    a = json.dumps(R.run(M.G()), sort_keys=True).encode()
    b = json.dumps(R.run(M.G()), sort_keys=True).encode()
    other = M.Runner(tmp_path / "elsewhere" / "deep")
    c = json.dumps(other.run(M.G()), sort_keys=True).encode()
    assert a == b == c


def test_report_does_not_leak_paths(golden, tmp_path):
    assert str(tmp_path) not in json.dumps(golden)


def test_info_and_na_cases_stay_inert_even_if_the_bundle_supplies_evidence(R):
    """A bundle that 'executes' INFO/NA cases cannot turn them into verdicts (D9) nor upset the claim."""
    b = M.G()
    for cid in ("QA-I1", "QA-I2", "QA-14"):
        b.cases[cid] = copy_case(b.cases["QA-S1"])
    r = R.run(b)
    assert r["overall"] == V.PASS and r["violations"] == []
    assert M.vmap(r)["QA-I1"] == M.vmap(r)["QA-I2"] == V.NOT_RUN and M.vmap(r)["QA-14"] == V.NOT_APPLICABLE
    assert r["counts"] == {V.PASS: 22, V.FAIL: 0, V.INCONCLUSIVE: 0, V.NOT_RUN: 2, V.NOT_APPLICABLE: 1}


def copy_case(c):
    return json.loads(json.dumps(c))
