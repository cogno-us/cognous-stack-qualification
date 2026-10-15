"""Qualification with the merged Replay API and its pinned Runtime fixtures."""
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys

import pytest
from agent_governance_evidence_pack import recovery_inspection as ep
from agent_replay_bundle import recovery_inspection as ri

REPLAY = Path(os.environ["COGNOUS_REPLAY_SOURCE"]).resolve()
assert Path(ri.__file__).resolve() == REPLAY / "src/agent_replay_bundle/recovery_inspection.py"
content = Path(ri.__file__).read_bytes().rstrip(b"\n") + b"\n"
assert hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest() == "00fb16918f55d9799cd693b300a41d2a44e80379"
if os.environ.get("EXPECTED_EVIDENCE_ROOT"):
    assert Path(ep.__file__).resolve().is_relative_to(Path(os.environ["EXPECTED_EVIDENCE_ROOT"]))
# Reuse the pinned owning-repository fixture helpers. They import and blob-check
# actual Runtime modules, then create temporary SQLite state through Runtime APIs.
fixtures = runpy.run_path(str(REPLAY / "tests/recovery_inspection_checks.py"))


@pytest.fixture
def pair(tmp_path):
    return fixtures["ledger"].__wrapped__(tmp_path)


def native(pair):
    return fixtures["inspect"](fixtures["export"](pair))


def build(inspection):
    return ep.build_recovery_inspection_evidence(inspection, replay_revision=ep.REPLAY_REVISION,
                                                expected_identity=inspection["expected_identity"])


@pytest.mark.parametrize("scenario", ["empty", "unknown", "absent", "partial", "applied", "collision", "legacy"])
def test_actual_chain_retains_evidence_without_authority(pair, scenario):
    if scenario == "legacy":
        pair[0].close_original_attempt(attempt_id="attempt", observation_state="applied",
            observation=fixtures["OrderingEvidence"](3, "synthetic:legacy"), observation_ref="synthetic:legacy")
    elif scenario != "empty":
        state = "unknown" if scenario == "collision" else scenario
        fixtures["append"](pair, state=state, final=state == "applied", complete_coverage=state == "applied")
        if scenario == "collision":
            fixtures["append"](pair, state="partial", order=4)
    source = native(pair)
    before = deepcopy(source)
    output = build(source)
    assert source == before == native(pair)
    assert output == build(source)
    assert output["replay_inspection"] == source
    assert output["loss_report"] == source["loss_report"]
    assert output["assurance"]["independent_verification"] == "not_established"
    assert output["assurance"]["settlement_verified"] is False
    assert output["assurance"]["retry_eligible"] is False
    assert output["review_status"] == "unreviewed"
    assert output["summary"]["original_disposition"] == "in_doubt"
    if scenario == "applied":
        assert output["summary"]["producer_work_state"] == "resolved"
        assert output["summary"]["producer_finality"] == "synthetic_profile_only"
    if scenario == "collision":
        assert output["summary"]["commitment_only_event_count"] == 1
        assert output["summary"]["producer_work_state"] == "conflict_review"
    if scenario == "legacy":
        assert output["summary"]["legacy_record_present"] is True
        assert output["summary"]["producer_work_state"] == "awaiting_observation"
    ep.validate_recovery_inspection_evidence(output)
    output["loss_report"]["dropped_fields"].append("changed")
    assert source == before


@pytest.mark.parametrize("key,value", [("inspection_format", "unknown"), ("runtime_revision", "main"),
    ("loss_report", {}), ("event_checks", []), ("assurance", {"settlement_verified": True})])
def test_invalid_replay_inputs_rejected(pair, key, value):
    fixtures["append"](pair)
    source = native(pair)
    source[key] = value
    with pytest.raises(ep.RecoveryEvidenceError):
        build(source)


def test_unknown_replay_revision_and_wrong_selected_identity(pair):
    source = native(pair)
    with pytest.raises(ep.RecoveryEvidenceError):
        ep.build_recovery_inspection_evidence(source, replay_revision="main", expected_identity=source["expected_identity"])
    selected = dict(source["expected_identity"], grant_id="other")
    with pytest.raises(ep.RecoveryEvidenceError):
        ep.build_recovery_inspection_evidence(source, replay_revision=ep.REPLAY_REVISION, expected_identity=selected)


def test_replay_validator_rejects_dropped_event(pair):
    fixtures["append"](pair, state="applied", complete_coverage=True, final=True)
    source = native(pair)
    source["source"]["events"] = []
    with pytest.raises(ep.RecoveryEvidenceError):
        build(source)


def test_loss_mapping_preserves_collision_gap(pair):
    fixtures["append"](pair)
    fixtures["append"](pair, state="partial", order=4)
    source = native(pair)
    output = build(source)
    assert output["loss_report"] == source["loss_report"]
    assert output["loss_report"]["unavailable_evidence"]


@pytest.mark.parametrize("section,key,value", [
    (None, "review_status", "accepted"), (None, "transformation", "unknown"),
    (None, "loss_report", {}), (None, "original_identity", {}),
    ("provenance", "input_sha256", "a"*64), ("provenance", "replay_revision", "main"),
    ("summary", "retained_event_count", 0), ("summary", "producer_work_state", "resolved"),
    ("assurance", "settlement_verified", True), ("assurance", "retry_eligible", True),
    ("assurance", "independent_verification", "verified"),
])
def test_derived_evidence_changes_rejected(pair, section, key, value):
    fixtures["append"](pair)
    output = build(native(pair))
    target = output if section is None else output[section]
    target[key] = value
    with pytest.raises(ep.RecoveryEvidenceError):
        ep.validate_recovery_inspection_evidence(output)


@pytest.mark.parametrize("mutation", ["validator", "loss"])
def test_disposable_mutation_controls(tmp_path, mutation):
    root = tmp_path / "isolated"
    shutil.copytree(Path(ep.__file__).parent, root / "agent_governance_evidence_pack",
                    ignore=shutil.ignore_patterns("__pycache__"))
    test = root / "checks.py"
    shutil.copyfile(__file__, test)
    path = root / "agent_governance_evidence_pack/recovery_inspection.py"
    code = path.read_text()
    if mutation == "validator":
        changed = code.replace("        validate_recovery_inspection(retained)", "        pass  # removed in disposable mutant", 1)
        case = "test_replay_validator_rejects_dropped_event"
    else:
        changed = code.replace('"loss_report": deepcopy(retained["loss_report"])', '"loss_report": {}', 1)
        case = "test_loss_mapping_preserves_collision_gap"
    assert changed != code
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(root), str(REPLAY / "src")]),
               EXPECTED_EVIDENCE_ROOT=str(root))
    command = [sys.executable, "-m", "pytest", "-q", str(test) + "::" + case]
    before = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True, timeout=30)
    assert before.returncode == 0, before.stdout + before.stderr
    path.write_text(changed)
    for cache in root.rglob("__pycache__"):
        shutil.rmtree(cache)
    after = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True, timeout=30)
    assert after.returncode == 1, after.stdout + after.stderr
    assert "1 failed" in after.stdout and case in after.stdout
