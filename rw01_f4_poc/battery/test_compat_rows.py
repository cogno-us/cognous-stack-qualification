"""N23, N24, N25: the existing modes and the Control Plane's flag-off output are byte-identical to the BASE revisions, run as subprocesses at the base and the head checkouts."""
import json
import subprocess
import sys

import pytest

import harness as H

HERE = H.HERE


def run(script, *args):
    res = subprocess.run([sys.executable, str(HERE / script), *map(str, args)], capture_output=True, text=True, timeout=600)
    assert res.returncode == 0, res.stderr[-2000:]
    return res.stdout


# =============================================================================================================== N25
@pytest.fixture(scope="module")
def cp_runs():
    reg = H.src("registry")
    return {"base": run("probe_cp.py", H.src("control_plane_base"), reg, "omit"), "head_omit": run("probe_cp.py", H.src("control_plane"), reg, "omit"),
            "head_false": run("probe_cp.py", H.src("control_plane"), reg, "false"), "head_true": run("probe_cp.py", H.src("control_plane"), reg, "true")}


@pytest.mark.row("N25", "CP decisions without selection_evidence: flag omitted and flag False at PR head produce run.json texts BYTE-IDENTICAL to the base b19c47dd (authorized+executed store and hold store)")
@pytest.mark.evidence("SUBPROCESS")
def test_n25_flag_off_output_is_byte_identical_to_the_base_revision(cp_runs):
    assert cp_runs["head_omit"] == cp_runs["base"] == cp_runs["head_false"]
    docs = json.loads(cp_runs["base"])
    assert all(b"selection_evidence" not in docs[k].encode() for k in docs) and json.loads(docs["main"])["decisions"] and json.loads(docs["hold"])["decisions"][0]["result"] == "hold"


@pytest.mark.row("N25", "CP legacy golden: the base-produced and head-produced stores equal the golden fixture of the CP PR (tests/fixtures/rw01_f4_poc_legacy_run_b19c47dd.json) exactly")
@pytest.mark.evidence("SUBPROCESS")
def test_n25_equals_the_cp_pr_legacy_golden(cp_runs):
    golden = json.loads((H.src("control_plane") / "tests" / "fixtures" / "rw01_f4_poc_legacy_run_b19c47dd.json").read_text())
    assert json.loads(cp_runs["base"]) == golden == json.loads(cp_runs["head_omit"])


@pytest.mark.row("N25", "flag ON changes nothing except the one added member on the authorized decision; the hold store is byte-identical (nothing carried on a hold)")
@pytest.mark.evidence("SUBPROCESS")
def test_n25_flag_on_adds_only_the_member_to_authorized_decisions(cp_runs):
    base, on = json.loads(cp_runs["base"]), json.loads(cp_runs["head_true"])
    main = json.loads(on["main"])
    carried = [d.pop("selection_evidence") for d in main["decisions"] if d["result"] == "authorized"]
    assert len(carried) == 1 and carried[0]["version"] == "selection-evidence/0.1"
    assert main == json.loads(base["main"]) and on["hold"] == base["hold"]


# =============================================================================================================== N23 / N24
@pytest.fixture(scope="module")
def replay_runs(tmp_path_factory):
    import conftest  # noqa: F401
    from unittest import mock
    d = tmp_path_factory.mktemp("bridged_no_evidence")
    with mock.patch.object(H.cp_bounded, "_now", lambda: H.NOW), mock.patch.object(H.cp_f4, "_now", lambda: H.NOW):
        pr = H.produce(d / "w", H.material(), carry=False)
    cp, proposal = H.bridge(pr, evidence=False)
    rec = d / "real_f4_effective_configuration_bridged_no_evidence"
    rec.mkdir()
    (rec / "control_plane_run.json").write_text(json.dumps(cp, sort_keys=True))
    (rec / "proposal.json").write_text(json.dumps(proposal, sort_keys=True))
    dirs = sorted(p for p in (H.src("replay") / "tests" / "fixtures" / "registry_governed_effective_configuration").iterdir() if p.is_dir()) + [rec]
    return {"head": run("probe_replay.py", H.src("replay") / "src", *dirs), "base": run("probe_replay.py", H.src("replay_base") / "src", *dirs)}


@pytest.mark.row("N23", "structural-only mode unchanged: Replay PR head and base produce byte-identical results (bundles and refusals) for every captured governed record plus the REAL F4 effective_configuration record without evidence")
@pytest.mark.evidence("SUBPROCESS")
def test_n23_structural_only_is_byte_identical_to_the_base_replay(replay_runs):
    assert replay_runs["head"] == replay_runs["base"]
    rows = [x for x in json.loads(replay_runs["head"]) if x["mode"] == "structural"]
    ok = [x for x in rows if "bundle" in x]
    assert len(ok) >= 4 and any(x["record"].startswith("real_f4") for x in ok)
    for x in ok:
        m = x["bundle"]["metadata"]
        assert m["control_plane_profile"] == H.OLD_SELECTOR and m["effective_configuration_verification"] == "internal_consistency_only_registry_source_revision_unverified"
        assert not [k for k in m if k.startswith("registry_") or k == "claim_scope_note" or k == "control_plane_decision_authenticated"]


@pytest.mark.row("N24", "caller-trusted digest mode unchanged: byte-identical to the base Replay; a matching digest still succeeds (no Registry authentication), a wrong digest still refuses effective_configuration_expected_mismatch")
@pytest.mark.evidence("SUBPROCESS")
def test_n24_caller_trusted_digest_is_byte_identical_and_still_not_authentication(replay_runs):
    assert replay_runs["head"] == replay_runs["base"]
    rows = json.loads(replay_runs["head"])
    good = [x for x in rows if x["mode"] == "trusted_match_correct" and "bundle" in x]
    bad = [x for x in rows if x["mode"] == "trusted_match_wrong" and "refused" in x and "decisions" not in x["record"]]
    assert good and bad
    assert all(x["bundle"]["metadata"].get("registry_authenticated", False) is False and "registry_selection_verification" not in x["bundle"]["metadata"] for x in good)
    assert {x["refused"][1] for x in bad if x["record"] != "governed_binding_changed"} <= {"effective_configuration_expected_mismatch", "effective_configuration_record_missing"}
