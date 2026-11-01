"""NC4-03 frozen deterministic mutation set (v1): execution against the pinned hub source, negative controls, host-independence and oracle v8 fragment checks.

SPDX-License-Identifier: Apache-2.0

Every test here is deterministic and host-independent (no uid, /proc, sysctl, socket or network). The pinned hub checkout comes from MVP_HUB_DIR and is only COPIED.
A missing MVP_HUB_DIR FAILS (nothing skips). Tests that depend on the ast_digest pins skip on a non-3.13 interpreter with an explicit reason (the suite convention of
test_kwflow.py): a skipped instance in the authoritative 3.13 run is INCOMPLETE at the gate. PROPOSED; Qualification owns the set and the oracle.
"""
import copy
import json
import os
import pathlib
import subprocess
import sys

import pytest

import _kwflow
import _nc4_03_mutations as M
import verdict

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DOC = M.load_set()
requires_313 = pytest.mark.skipif(not M.interpreter_ok(), reason="the NC4-03 ast_digest pins are honoured on CPython 3.13 only; this interpreter is supplementary")


@pytest.fixture(autouse=True)
def _components_present():
    """Pure source analysis: overrides the suite's component-wiring autouse fixture (only the hub tools/mvp_ingress tree is read, as a copy)."""


@pytest.fixture(scope="module")
def hub():
    raw = os.environ.get("MVP_HUB_DIR")
    if not raw or not (pathlib.Path(raw) / "tools" / "mvp_ingress").is_dir():
        pytest.fail("MVP_HUB_DIR must name the pinned hub checkout (tools/mvp_ingress): the deterministic NC4-03 mutation set has no input without it")
    return pathlib.Path(raw)


@pytest.fixture(scope="module")
def base_obs(hub):
    return M.observe_tree(hub, "pinned")


@pytest.fixture(scope="module")
def det_record(hub):
    return M.run_deterministic(hub)


MUT_IDS = [m["id"] for m in DOC["mutations"]]
CTL_IDS = [c["id"] for c in DOC["controls"]]
FAM_IDS = [f["id"] for f in DOC["families"]]
BY_ID = {i["id"]: i for i in DOC["mutations"] + DOC["controls"]}


# ---- structure ---------------------------------------------------------------------------------------------------------------------------------
def test_every_mutation_and_control_is_fully_specified_with_the_six_fields():
    assert M.validate_set(DOC) == []
    for it in DOC["mutations"] + DOC["controls"]:
        for f in M.ITEM_FIELDS:
            assert it[f], (it["id"], f)
    assert len(DOC["mutations"]) == 69 and len(DOC["controls"]) == 13 and len(DOC["families"]) == 7


def test_every_family_has_a_negative_control_pair_or_a_noop():
    for fam in DOC["families"]:
        kinds = {c["title"].split(" ")[0] for c in DOC["controls"] if c["family"] == fam["id"]}
        assert any(c["id"].endswith("NOOP") for c in DOC["controls"] if c["family"] == fam["id"]), fam["id"]
        assert kinds, fam["id"]


def test_every_rule_the_predicate_can_emit_is_the_expected_rejection_of_at_least_one_mutation():
    """F-05: the frozen set must cover every rule id of _kwflow (UNRESOLVED is the callee-resolution sentinel of names_of, not a rule id: its code paths are driven by the GENERIC-FORWARD
    mutations that expect OPAQUE_POSITIONAL_UNPACK / ORIGIN_VIOLATION on an unresolved callee)."""
    import ast
    import re
    tree = ast.parse((HERE / "_kwflow.py").read_text())
    emitted = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and re.fullmatch(r"[A-Z]+(_[A-Z]+)+", n.value)}
    emitted.discard("UNRESOLVED")
    assert {"SIMULATE_NOT_CONSTANT_NONE", "NONLITERAL_KWARGS", "MODEL_COPY_KWARGS_FORBIDDEN", "MODEL_COPY_UPDATE_NOT_FIXED", "COMPREHENSION_NOT_FIXED", "OPAQUE_POSITIONAL_UNPACK"} <= emitted
    covered = {r for m in DOC["mutations"] for r in m["expected"]["rules_all_of"]}
    assert emitted - covered == set(), f"rule ids with no frozen mutation: {sorted(emitted - covered)}"
    gen = [m for m in DOC["mutations"] if m["family"] == "GENERIC-FORWARD"]
    assert len(gen) == 12 and {"SIMULATE_NOT_CONSTANT_NONE", "NONLITERAL_KWARGS", "MODEL_COPY_KWARGS_FORBIDDEN", "MODEL_COPY_UPDATE_NOT_FIXED", "COMPREHENSION_NOT_FIXED",
                                "OPAQUE_POSITIONAL_UNPACK"} <= {r for m in gen for r in m["expected"]["rules_all_of"]}
    assert sum("UNRESOLVED-callee path" in m["provenance"]["supplementary_source"] for m in gen) == 3
    assert [c["id"] for c in DOC["controls"] if c["family"] == "GENERIC-FORWARD"] == ["C-GENERIC-FORWARD-NOOP", "C-GENERIC-FORWARD-BENIGN"]


def test_set_is_declared_deterministic_and_host_independent_and_is_not_the_host_file():
    assert DOC["deterministic"] is True and DOC["host_dependent"] is False
    for it in DOC["mutations"] + DOC["controls"]:
        assert it["environment"]["host_dependent"] is False
    host = json.loads((HERE / "nc4_03_host_subcases.v1.json").read_text())
    assert host["host_dependent"] is True and host["affects_deterministic_verdict"] is False
    assert not ({i["id"] for i in DOC["mutations"] + DOC["controls"]} & {s["id"] for s in host["subcases"]})


@requires_313
def test_set_target_equals_the_predicate_constants_and_the_pinned_hub(hub, base_obs):
    t = DOC["target"]
    assert t["pin_sha"] == _kwflow.HUB_REVISION
    assert t["ingress_py_tree_sha256"] == _kwflow.INGRESS_PY_TREE_SHA256 == base_obs["ingress_tree_sha256"]
    assert t["recursive_tree_sha256"] == _kwflow.EXPECTED_TREE_SHA256 == base_obs["recursive_tree_sha256"]
    ing = hub / "tools" / "mvp_ingress"
    assert t["file_sha256"] == {p.name: M.sha256_bytes(p.read_bytes()) for p in sorted(ing.iterdir()) if p.is_file()}
    for it in DOC["mutations"] + DOC["controls"]:
        for fname, digest in it["input"]["files"].items():
            assert t["file_sha256"][fname] == digest, (it["id"], fname)


def test_malformed_sets_are_rejected_by_the_structure_check():
    bad = copy.deepcopy(DOC)
    del bad["mutations"][0]["predicate"]
    assert any("predicate" in p for p in M.validate_set(bad))
    bad = copy.deepcopy(DOC)
    bad["controls"] = [c for c in bad["controls"] if c["family"] != "OR-FIELD"]
    assert any("OR-FIELD" in p for p in M.validate_set(bad))
    bad = copy.deepcopy(DOC)
    bad["mutations"][0]["predicate"] = [p for p in bad["mutations"][0]["predicate"] if p["obs"] != "violation_rules"]
    assert any("not enforced" in p for p in M.validate_set(bad))


# ---- execution against the pinned hub source ---------------------------------------------------------------------------------------------------
@requires_313
@pytest.mark.parametrize("mid", MUT_IDS)
def test_mutation_is_rejected_as_expected(mid, hub, base_obs):
    r = M.run_item(hub, BY_ID[mid], base_obs)
    assert r["observed"]["mutation_applied"], (mid, r["observed"]["apply_error"])
    assert r["predicate_holds"], (mid, BY_ID[mid]["title"], r["failed_predicates"], r["observed"])


@requires_313
@pytest.mark.parametrize("cid", CTL_IDS)
def test_control_is_accepted_so_the_predicate_cannot_false_pass(cid, hub, base_obs):
    r = M.run_item(hub, BY_ID[cid], base_obs)
    assert r["predicate_holds"], (cid, r["failed_predicates"], r["observed"])
    assert r["observed"]["violation_count"] == 0


@requires_313
@pytest.mark.parametrize("fam", FAM_IDS)
def test_control_does_not_satisfy_any_rejection_predicate_of_its_family(fam, hub, base_obs):
    for c in [c for c in DOC["controls"] if c["family"] == fam]:
        r = M.run_item(hub, c, base_obs)
        for m in [m for m in DOC["mutations"] if m["family"] == fam]:
            assert not M.holds(m["predicate"], r["observed"])[0], f"{c['id']} would satisfy the rejection predicate of {m['id']}"


# ---- deterministic verdict ---------------------------------------------------------------------------------------------------------------------
@requires_313
def test_deterministic_record_passes_and_is_stable_across_runs(hub, det_record):
    assert det_record["verdict"] == verdict.PASS, det_record["reasons"]
    assert (det_record["mutations_total"], det_record["mutations_rejected"], det_record["controls_total"], det_record["controls_accepted"]) == (69, 69, 13, 13)
    assert det_record["mutations_not_rejected"] == [] and det_record["controls_falsely_rejected"] == [] and det_record["control_satisfies_rejection_predicate"] == []
    assert det_record["pinned_input"]["matches_set_target"] is True and det_record["host_dependent"] is False
    again = M.run_deterministic(hub)
    assert again == det_record and again["record_sha256"] == det_record["record_sha256"]


@requires_313
def test_deterministic_record_is_identical_under_a_different_host_environment(hub, det_record):
    """A subprocess with a scrambled process environment, cwd, umask, hash seed and a junk ingress profile must produce a byte-identical record: no host input is read."""
    code = ("import sys,json; sys.path.insert(0,%r); import _nc4_03_mutations as M; r=M.run_deterministic(sys.argv[1]); print(r['record_sha256'], r['verdict'])" % str(HERE))
    env = {"PATH": "/nonexistent", "HOME": "/nonexistent", "LANG": "C", "TZ": "Pacific/Kiritimati", "MVP_INGRESS_PROFILE": "bogus", "MVP_INGRESS_USER": "nobody", "PYTHONHASHSEED": "12345",
           "PYTHONDONTWRITEBYTECODE": "1", "MVP_RESULTS_DIR": "/nonexistent"}
    p = subprocess.run([sys.executable, "-c", code, str(hub)], cwd="/", env=env, capture_output=True, text=True, timeout=300)
    assert p.returncode == 0, p.stderr[-500:]
    assert p.stdout.split() == [det_record["record_sha256"], "PASS"]


def test_mutation_runner_never_touches_host_apis_or_the_host_module():
    import ast
    tree = ast.parse((HERE / "_nc4_03_mutations.py").read_text())
    module_level = {n.names[0].name for n in tree.body if isinstance(n, ast.Import)} | {n.module for n in tree.body if isinstance(n, ast.ImportFrom)}
    assert "_nc4_03_host" not in module_level and "_ingress" not in module_level  # _ingress is imported lazily, only inside scenario_observation (a v3 AST helper)
    assert not [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) and "_nc4_03_host" in ast.dump(n)]
    docstrings = {id(n.body[0].value) for n in ast.walk(tree) if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body and isinstance(n.body[0], ast.Expr)
                  and isinstance(getattr(n.body[0], "value", None), ast.Constant) and isinstance(n.body[0].value.value, str)}
    seen = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Attribute):
            seen.add(n.attr)
        elif isinstance(n, ast.Name):
            seen.add(n.id)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docstrings:
            seen.add(n.value)
    for token in ("geteuid", "getuid", "setuid", "setresuid", "getpwnam", "getgrnam", "uname", "getpid", "time", "datetime", "socket", "yama", "ptrace", "MVP_INGRESS_PROFILE"):
        assert token not in seen, f"deterministic module references host/clock API {token!r}"
    assert not [v for v in seen if isinstance(v, str) and v.startswith("/proc")]


@requires_313
def test_a_scanner_that_accepts_everything_cannot_pass_the_set(hub, monkeypatch):
    """False-pass guard: if the predicate stopped rejecting, every mutation would be reported as not rejected and the verdict would be FAIL."""
    real = _kwflow.scan_dir

    def lenient(root, rev=None):
        out = real(root, rev)
        out["violations"], out["pins_unmatched"], out["required_sites_missing"] = [], [], []
        return out
    monkeypatch.setattr(_kwflow, "scan_dir", lenient)
    rec = M.run_deterministic(hub)
    assert rec["verdict"] == verdict.FAIL and len(rec["mutations_not_rejected"]) >= 50


@requires_313
def test_a_scanner_that_rejects_everything_cannot_pass_the_set(hub, monkeypatch):
    real = _kwflow.scan_dir

    def strict(root, rev=None):
        out = real(root, rev)
        out["violations"] = out["violations"] + [{"rule": "ORIGIN_VIOLATION", "site": "forced"}]
        return out
    monkeypatch.setattr(_kwflow, "scan_dir", strict)
    rec = M.run_deterministic(hub)
    assert rec["verdict"] == verdict.FAIL and rec["controls_falsely_rejected"]


@requires_313
def test_an_unapplied_mutation_is_never_counted_as_rejected(hub, base_obs):
    item = copy.deepcopy(BY_ID["M001"])
    item["operation"]["steps"][0]["old"] = "THIS ANCHOR DOES NOT EXIST"
    r = M.run_item(hub, item, base_obs)
    assert r["observed"]["mutation_applied"] is False and r["predicate_holds"] is False and r["observed"]["apply_error"]
    item = copy.deepcopy(BY_ID["M001"])
    item["operation"]["steps"][0]["new"] = item["operation"]["steps"][0]["old"]  # a "mutation" that changes nothing
    r = M.run_item(hub, item, base_obs)
    assert r["observed"]["mutation_applied"] is False and r["predicate_holds"] is False


def test_wrong_interpreter_or_missing_input_is_blocked_never_pass(hub, monkeypatch):
    monkeypatch.setattr(M, "interpreter_ok", lambda: False)
    assert M.run_deterministic(hub)["verdict"] == verdict.BLOCKED
    monkeypatch.undo()
    if M.interpreter_ok():
        assert M.run_deterministic(None)["verdict"] == verdict.BLOCKED
        assert M.run_deterministic("/nonexistent/hub")["verdict"] == verdict.BLOCKED


@requires_313
def test_a_different_hub_tree_is_fail_never_pass(hub, tmp_path):
    import shutil
    shutil.copytree(hub / "tools" / "mvp_ingress", tmp_path / "tools" / "mvp_ingress")
    f = tmp_path / "tools" / "mvp_ingress" / "core.py"
    f.write_text(f.read_text() + "\n# not the frozen bytes\n")
    rec = M.run_deterministic(tmp_path)
    assert rec["verdict"] == verdict.FAIL and rec["pinned_input"]["matches_set_target"] is False and rec["mutation_results"] == []


def test_the_pinned_checkout_is_not_modified_by_a_run(hub, det_record):
    if (hub / ".git").exists():
        out = subprocess.run(["git", "-C", str(hub), "status", "--porcelain", "--ignored"], capture_output=True, text=True, timeout=60).stdout
        assert out.strip() == "", out


# ---- separation of deterministic and host-dependent results ------------------------------------------------------------------------------------
HOST_VARIANTS = {
    "all_pass": ["PASS"] * 4, "all_blocked": ["BLOCKED"] * 4, "all_fail": ["FAIL"] * 4, "mixed": ["PASS", "FAIL", "BLOCKED", "PASS"],
}


@pytest.mark.parametrize("det_verdict", [verdict.PASS, verdict.FAIL])
@pytest.mark.parametrize("variant", sorted(HOST_VARIANTS))
def test_host_results_never_alter_or_obscure_the_deterministic_verdict(variant, det_verdict):
    det = {"verdict": det_verdict, "reasons": ["x"], "record_sha256": "0" * 64, "mutations_total": 69}
    host = {"subcases": [{"id": i, "status": s, "reason": "r", "observed": {}} for i, s in zip(("NC4-03a", "NC4-03b", "NC4-03c", "NC4-03d"), HOST_VARIANTS[variant])]}
    before = json.dumps(det, sort_keys=True)
    out = M.compose(det, host)
    assert out["nc4_03_row_verdict"] == det_verdict
    assert json.dumps(out["nc4_03_deterministic"], sort_keys=True) == before == json.dumps(det, sort_keys=True)
    assert out["host_subcase_statuses"] == dict(zip(("NC4-03a", "NC4-03b", "NC4-03c", "NC4-03d"), HOST_VARIANTS[variant]))


# ---- oracle v8 fragment ------------------------------------------------------------------------------------------------------------------------
FRAG = json.loads((HERE / "nc4_03_oracle_v8_fragment.proposed.json").read_text())
V7 = json.loads((ROOT / "process" / "mvp-chain" / "expectations.proposed.v7.json").read_text())
V7_NC403 = next(r for r in V7["rows"] if r["id"] == "NC4-03")
V8_NC403 = next(r for r in FRAG["rows"] if r["id"] == "NC4-03")
OLD, NEW = "nc_unmediated.source_level.", "nc4_03_det.source_level."


def _key(p):
    return json.dumps(p, sort_keys=True)


def test_v8_nc4_03_keeps_every_v7_predicate_unchanged_except_the_scenario_prefix():
    new = {_key(p) for p in V8_NC403["all"]}
    for p in V7_NC403["all"]:
        moved = dict(p, obs=p["obs"].replace(OLD, NEW, 1))
        assert _key(moved) in new, f"v7 predicate weakened or lost: {p}"
    assert V8_NC403["mandatory"] is True and V8_NC403["scenario"] == "nc4_03_det" and "blocked_if" not in V8_NC403 and "not_applicable_if" not in V8_NC403
    assert len(V8_NC403["all"]) > len(V7_NC403["all"])


def test_v8_fragment_rows_are_complete_mandatory_and_placeholder_free():
    assert [r["id"] for r in FRAG["rows"]] == ["NC4-03", "NC4-03a", "NC4-03b", "NC4-03c", "NC4-03d"]
    for r in FRAG["rows"]:
        assert r["mandatory"] is True and r["all"] and r["title"] and "placeholder" not in json.dumps(r).lower()
    for r in FRAG["rows"][1:]:
        assert r["scenario"] == "nc4_03_host" and r["blocked_if"] and r["all"][0]["op"] == "eq" and r["all"][0]["value"] == "PASS"
    assert FRAG["counts"] == {"v7_rows": 42, "v7_mandatory": 41, "rows_added": 4, "rows_changed": 1, "v8_rows_from_this_fragment_alone": 46, "v8_mandatory_from_this_fragment_alone": 45}
    ids7 = {r["id"] for r in V7["rows"]}
    assert "NC4-03" in ids7 and not ({"NC4-03a", "NC4-03b", "NC4-03c", "NC4-03d"} & ids7)


def test_v8_fragment_mutation_set_predicates_match_the_set_file():
    sha = M.set_file_sha256()
    preds = {p["obs"]: p for p in V8_NC403["all"]}
    assert preds["nc4_03_det.mutation_set.set_file_sha256"]["value"] == sha
    assert preds["nc4_03_det.mutation_set.mutations_total"]["value"] == preds["nc4_03_det.mutation_set.mutations_rejected"]["value"] == len(DOC["mutations"])
    assert preds["nc4_03_det.mutation_set.controls_total"]["value"] == preds["nc4_03_det.mutation_set.controls_accepted"]["value"] == len(DOC["controls"])
    assert preds["nc4_03_det.mutation_set.verdict"]["value"] == "PASS" and preds["nc4_03_det.mutation_set.set_version"]["value"] == "v1"


@requires_313
def test_v8_nc4_03_row_evaluates_pass_on_the_deterministic_observation_and_ignores_the_host_scenario(hub):
    det_obs = M.scenario_observation(hub, _kwflow.HUB_REVISION)
    assert det_obs["status"] == "ran", det_obs
    for host_state in ("BLOCKED", "FAIL", "PASS", None):
        obs = {"nc4_03_det": det_obs}
        if host_state:
            obs["nc4_03_host"] = {"status": "ran", **{i: {"status": host_state, "reason": "x"} for i in ("NC4-03a", "NC4-03b", "NC4-03c", "NC4-03d")}}
        res = verdict.evaluate_row(V8_NC403, obs)
        assert res["status"] == verdict.PASS, (host_state, res)


@requires_313
def test_v8_nc4_03_row_is_fail_when_the_deterministic_mutation_set_fails(hub):
    det_obs = M.scenario_observation(hub, _kwflow.HUB_REVISION)
    bad = copy.deepcopy(det_obs)
    bad["mutation_set"].update(verdict="FAIL", mutations_rejected=56, mutations_not_rejected=["M001"])
    res = verdict.evaluate_row(V8_NC403, {"nc4_03_det": bad, "nc4_03_host": {"status": "ran", **{i: {"status": "PASS"} for i in ("NC4-03a", "NC4-03b", "NC4-03c", "NC4-03d")}}})
    assert res["status"] == verdict.FAIL


# a complete PASSING host observation for each subcase, written independently of the harness (the shape _nc4_03_host.scenario_observation records)
PASSING = {
    "NC4-03a": {"observed": {"ptrace_scope": "1"}, "facts": {}},
    "NC4-03b": {"observed": {"ratified_profile": True, "ingress_uid": 990, "client_uid": 991, "outsider_uid": 65533,
                             "client_proc": {"uid": ["991"] * 4, "gid": ["991"] * 4, "groups": [], "cap_eff": ["0000000000000000"]},
                             "outsider_proc": {"uid": ["65533"] * 4, "gid": ["65533"] * 4, "groups": [], "cap_eff": ["0000000000000000"]}},
                "facts": {k: True for k in ("ingress_not_root_or_optout", "client_nonzero_and_distinct_from_ingress", "client_and_ingress_distinct_primary_groups",
                                            "outsider_distinct_from_ingress_and_client", "client_dropped_capabilities", "outsider_dropped_capabilities",
                                            "client_effective_uid_is_declared", "outsider_effective_uid_is_declared")}},
    "NC4-03c": {"observed": {"ratified_profile": True, "dir_mode": "0o2751", "socket_mode": "0o660", "socket_is_socket": True,
                             "outsider": {"stat_known_socket": "ok", "listdir": "EACCES", "connect": "EACCES"}, "group_member_client": {"connect": "ok"}},
                "facts": {k: True for k in ("dir_mode_is_2751", "dir_group_is_ipc_group", "socket_is_a_socket", "socket_mode_is_0660", "socket_group_is_ipc_group_via_setgid",
                                            "outsider_can_stat_known_name_residual", "outsider_cannot_list_directory", "outsider_cannot_connect", "ipc_group_member_can_connect")}},
    "NC4-03d": {"observed": {"ratified_profile": True, "empty_allowlist": "refused", "allowlisted_client_response": '{"status": "stub-core-reached"}',
                             "non_allowlisted_group_member_response": '{"error": "PEER_NOT_ALLOWED"}'},
                "facts": {k: True for k in ("empty_allowlist_refused", "allowlisted_client_reaches_core", "non_allowlisted_group_member_refused")}},
}


def _host_obs(sid, status="PASS", mutate=None):
    rec = copy.deepcopy(PASSING[sid])
    if mutate:
        mutate(rec)
    return {"nc4_03_host": {"status": "ran", sid: {"status": status, "reason": "x", **rec}}}


@pytest.mark.parametrize("sid", ["NC4-03a", "NC4-03b", "NC4-03c", "NC4-03d"])
@pytest.mark.parametrize("state,expected", [("PASS", verdict.PASS), ("BLOCKED", verdict.BLOCKED), ("FAIL", verdict.FAIL)])
def test_v8_host_rows_map_each_host_status_to_the_same_oracle_status(sid, state, expected):
    row = next(r for r in FRAG["rows"] if r["id"] == sid)
    assert verdict.evaluate_row(row, _host_obs(sid, state))["status"] == expected
    assert verdict.evaluate_row(row, {})["status"] == verdict.NOT_RUN


@pytest.mark.parametrize("sid", ["NC4-03a", "NC4-03b", "NC4-03c", "NC4-03d"])
def test_v8_host_rows_do_not_pass_on_a_harness_written_status_string_alone(sid):
    """F-04: a record whose status says PASS but that carries no / contradicting observed facts is FAIL; every asserted observation is individually load-bearing."""
    row = next(r for r in FRAG["rows"] if r["id"] == sid)
    assert verdict.evaluate_row(row, {"nc4_03_host": {"status": "ran", sid: {"status": "PASS", "reason": "x"}}})["status"] == verdict.FAIL  # status string only
    assert verdict.evaluate_row(row, _host_obs(sid))["status"] == verdict.PASS
    facts = [p for p in row["all"][1:]]
    assert len(facts) >= 1
    for p in facts:
        path = p["obs"].split(f"nc4_03_host.{sid}.", 1)[1].split(".")

        def mutate(rec, path=path, p=p):
            node = rec
            for part in path[:-1]:
                node = node[part]
            node[path[-1]] = {"true": False, "eq": "<contradiction>", "in": "<contradiction>", "contains": "<contradiction>", "not_contains": "stub-core-reached"}[p["op"]]
        res = verdict.evaluate_row(row, _host_obs(sid, mutate=mutate))
        assert res["status"] == verdict.FAIL and any(f["obs"] == p["obs"] for f in res["failed"]), (p, res)


def test_the_host_scenario_records_the_observed_facts_the_rows_assert():
    """The harness side: the scenario observation exposes ``observed`` and ``facts`` per subcase (what the rows read)."""
    import _nc4_03_host as H
    obs = H.scenario_observation(None)
    for sid in H.SUBCASE_IDS:
        assert set(obs[sid]) >= {"status", "reason", "observed", "facts"} and isinstance(obs[sid]["observed"], dict) and isinstance(obs[sid]["facts"], dict)
    assert obs["NC4-03a"]["observed"].get("ptrace_scope") is not None


@requires_313
def test_frozen_set_matches_its_derivation_from_the_supplementary_tables(hub):
    """Anti-drift: the frozen data equals what the derivation script builds from test_kwflow.MUTANTS / V5_MUTANTS and the pinned bytes (the data file is the artifact)."""
    import _nc4_03_mutation_set_derive as D
    assert D.build(hub) == DOC
