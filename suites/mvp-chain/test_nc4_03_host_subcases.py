"""NC4-03 host-dependent subcases (NC4-03a..d): structure, status vocabulary, isolation from the deterministic verdict.

SPDX-License-Identifier: Apache-2.0

These tests pass on ANY host: they assert that each subcase reports a well-formed PASS / FAIL / BLOCKED status with its reason and that no host result can change the
deterministic verdict. They do NOT assert that the ratified 2751 profile is available: that is the oracle rows NC4-03a..d (v8 fragment), which are BLOCKED (acceptance
INCOMPLETE) on a host without the profile and are never converted. Nothing here is evidence of the profile on a developer machine. PROPOSED.
"""
import json
import os
import pathlib

import pytest

import _nc4_03_host as H
import _nc4_03_mutations as M
import verdict

HERE = pathlib.Path(__file__).resolve().parent
HOST = json.loads((HERE / "nc4_03_host_subcases.v1.json").read_text())
STATUSES = {verdict.PASS, verdict.FAIL, verdict.BLOCKED}


@pytest.fixture(autouse=True)
def _components_present():
    """Overrides the suite's component-wiring autouse fixture: the host probes read only the hub tools tree (copied)."""


def test_every_host_subcase_is_fully_specified_with_the_six_fields_and_is_separate():
    assert [s["id"] for s in HOST["subcases"]] == list(H.SUBCASE_IDS) and HOST["host_dependent"] is True and HOST["affects_deterministic_verdict"] is False
    for s in HOST["subcases"]:
        for f in M.ITEM_FIELDS:
            assert s[f], (s["id"], f)
        assert s["environment"]["not_production"] is True and "2751" in s["environment"]["profile"]
        assert s["predicate"] == [{"obs": f"nc4_03_host.{s['id']}.status", "op": "eq", "value": "PASS"}]
    assert "BLOCKED" in HOST["separation_rule"] and "never" in HOST["separation_rule"]


def test_host_record_is_well_formed_on_any_host():
    rec = H.run_host_subcases(os.environ.get("MVP_HUB_DIR"))
    assert rec["host_dependent"] is True and rec["affects_deterministic_verdict"] is False
    assert [s["id"] for s in rec["subcases"]] == list(H.SUBCASE_IDS)
    for s in rec["subcases"]:
        assert s["status"] in STATUSES and s["reason"] and isinstance(s["observed"], dict), s


def test_developer_optout_can_never_be_pass(monkeypatch):
    monkeypatch.setenv("MVP_INGRESS_PROFILE", "developer-optout")
    rec = H.run_host_subcases(os.environ.get("MVP_HUB_DIR"))
    assert all(s["status"] != verdict.PASS for s in rec["subcases"]), rec


def test_unknown_profile_blocks_identity_subcases_only(monkeypatch):
    monkeypatch.setenv("MVP_INGRESS_PROFILE", "bogus")
    rec = H.run_host_subcases(None)
    by = {s["id"]: s for s in rec["subcases"]}
    assert all(by[i]["status"] == verdict.BLOCKED for i in ("NC4-03b", "NC4-03c", "NC4-03d"))
    assert by["NC4-03a"]["status"] in STATUSES  # Yama is judged on its own


def test_a_probe_exception_blocks_that_subcase_only(monkeypatch):
    def boom(ctx):
        raise RuntimeError("probe exploded")
    monkeypatch.setenv("MVP_INGRESS_PROFILE", "developer-optout")  # identities resolve, so the probe itself is reached
    monkeypatch.setitem(H.PROBES, "NC4-03c", ("ipc_2751_socket_profile", boom))
    rec = H.run_host_subcases(None)
    by = {s["id"]: s for s in rec["subcases"]}
    assert by["NC4-03c"]["status"] == verdict.BLOCKED and "probe error" in by["NC4-03c"]["reason"]
    assert [s["id"] for s in rec["subcases"]] == list(H.SUBCASE_IDS)


def test_scenario_observation_never_marks_the_whole_scenario_blocked(monkeypatch):
    monkeypatch.setenv("MVP_INGRESS_PROFILE", "approved")
    obs = H.scenario_observation(None)
    assert obs["status"] == "ran" and set(H.SUBCASE_IDS) <= set(obs)
    for sid in H.SUBCASE_IDS:
        assert obs[sid]["status"] in STATUSES


def test_real_host_record_cannot_change_a_deterministic_record():
    det = {"verdict": verdict.PASS, "reasons": ["x"], "record_sha256": "1" * 64}
    host = H.run_host_subcases(os.environ.get("MVP_HUB_DIR"))
    out = M.compose(det, host)
    assert out["nc4_03_row_verdict"] == verdict.PASS and out["nc4_03_deterministic"] == det


def test_host_module_does_not_import_the_mutation_runner():
    import ast
    tree = ast.parse((HERE / "_nc4_03_host.py").read_text())
    names = {n.names[0].name for n in ast.walk(tree) if isinstance(n, ast.Import)} | {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert "_nc4_03_mutations" not in names
