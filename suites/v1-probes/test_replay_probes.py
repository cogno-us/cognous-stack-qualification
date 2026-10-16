"""ER-07-4 probes for the Replay Bundle importer: an incomplete delivery record cannot become verified completion.

Runs the real importer at the frozen F5b generation (Control Plane a34c3dc2 / runtime e20f92e1 profile) on the pinned
repo's own synthetic fixture, then degrades the delivery evidence and asserts the importer never reports completion or
verification it cannot support. Run against the checkout named by PROBE_REPLAY_DIR.
"""
import copy
import json
from pathlib import Path

import pytest

from conftest import pin_dir


def importers():
    pin_dir("PROBE_REPLAY_DIR")
    from agent_replay_bundle import importers as I
    return I


def load():
    I = importers()
    f = Path(pin_dir("PROBE_REPLAY_DIR")) / "tests" / "fixtures" / "security_runtime_valid"
    cp = json.loads((f / "control_plane_run.json").read_text(encoding="utf-8"))
    proposal = json.loads((f / "proposal.json").read_text(encoding="utf-8"))
    ex = json.loads((f / "executor.json").read_text(encoding="utf-8"))
    ex["repository"]["revision"] = I.MOLTBOT_F5B_REVISION
    ex["provenance"]["source_asserted"]["repository_revision"] = I.MOLTBOT_F5B_REVISION
    return cp, proposal, ex


def run(cp, proposal, ex):
    I = importers()
    return I.import_bounded_workflow(cp, proposal=proposal, moltbot_export=ex,
                                     control_plane_revision=I.CONTROL_PLANE_F5B_REVISION)


def test_probe_delivery_control_complete_import_is_complete_but_never_independently_verified():
    bundle = run(*load())
    assert bundle.status == "reconstruction_complete"  # control: detector is not reject-all
    assert bundle.semantics.independent_effect_verification is False
    assert bundle.semantics.external_effect_execution is False
    assert bundle.semantics.destination_observation == "producer_reported"
    assert all(r.evidence_class != "independently_checked" for r in bundle.records)
    assert bundle.metadata["executor_failure_reference_verification"] == "source_asserted_not_independently_verified"


def test_probe_delivery_incomplete_executor_evidence_absent_is_partial_not_complete():
    cp, proposal, _ = load()
    bundle = run(cp, proposal, None)
    assert bundle.status == "reconstruction_partial"
    report = bundle.import_reports[0]
    assert report.complete is False
    assert any(f.code == "B004" and f.value_state == "absent" for f in report.findings)
    assert bundle.semantics.destination_observation == "not_performed"
    assert bundle.semantics.independent_effect_verification is False


def _cp_says_unknown_executor_says_executed(cp, proposal, ex):
    cp["attempts"][-1]["status"] = "unknown"; cp["attempts"][-1]["acknowledgement"] = {}


def _executor_unknown_cp_acknowledged(cp, proposal, ex):
    ex["execution_result"]["status"] = "unknown"; ex["execution_result"]["acknowledged"] = False


def _executor_effect_rows_missing(cp, proposal, ex):
    ex["effects"] = []


def _no_applied_observation(cp, proposal, ex):
    cp["observations"] = [o for o in cp["observations"] if o["state"] != "applied"]


def _attempt_never_acknowledged(cp, proposal, ex):
    cp["attempts"] = cp["attempts"][:1]


def _delivery_wholly_incomplete(cp, proposal, ex):
    cp["attempts"] = cp["attempts"][:1]; cp["observations"] = []; ex["effects"] = []
    ex["execution_result"]["status"] = "unknown"; ex["execution_result"]["acknowledged"] = False


@pytest.mark.parametrize("degrade", [_cp_says_unknown_executor_says_executed, _executor_unknown_cp_acknowledged,
                                     _executor_effect_rows_missing, _no_applied_observation,
                                     _attempt_never_acknowledged, _delivery_wholly_incomplete],
                         ids=lambda f: f.__name__.strip("_"))
def test_probe_delivery_incomplete_or_contradicted_record_is_refused_not_promoted_to_completion(degrade):
    I = importers()
    cp, proposal, ex = load()
    degrade(cp, proposal, ex)
    with pytest.raises(I.ImportContractError):
        run(cp, proposal, ex)


def test_probe_incomplete_unfinished_resolution_check_is_partial_and_retained():
    cp, proposal, ex = load()
    opening = copy.deepcopy(cp["check_events"][0]); assert opening["phase"] == "opened"
    opening["check_id"] = "probe-unfinished-check"
    cp["check_events"].append(opening)
    bundle = run(cp, proposal, ex)
    assert bundle.status == "reconstruction_partial"
    assert any(f.code == "B006" and "probe-unfinished-check" in f.message and f.value_state == "unknown"
               for f in bundle.import_reports[0].findings)
    assert bundle.semantics.independent_effect_verification is False
    assert [r.data for r in bundle.records if r.record_type == "resolution_check_event"] == cp["check_events"]


def test_probe_verified_completion_cannot_be_forged_through_import_report_or_record_labels():
    # Verified-completion labels are not an input channel: re-labelling retained records as independently checked
    # in the source does not change what the importer emits.
    cp, proposal, ex = load()
    cp["attempts"][-1]["evidence_class"] = "independently_checked"
    cp["attempts"][-1]["independent_effect_verification"] = True
    ex["execution_result"]["independent_effect_verification"] = True
    try:
        bundle = run(cp, proposal, ex)
    except importers().ImportContractError:
        return  # refusing the forged label is also acceptable
    assert bundle.semantics.independent_effect_verification is False
    assert all(r.evidence_class != "independently_checked" for r in bundle.records)
