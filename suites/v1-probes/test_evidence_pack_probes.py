"""ER-08-3 probes for the Governance Evidence Pack: approved review status cannot follow from schema validity alone.

Every case below is a pack that LOADS (passes the pydantic schema) and is then judged by the real semantic validator,
summary and renderer. Run against the checkout named by PROBE_EVIDENCE_PACK_DIR.
"""
import copy
import json
from pathlib import Path

import pytest

from conftest import pin_dir

NOW = "2026-01-01T00:00:00Z"


def api():
    pin_dir("PROBE_EVIDENCE_PACK_DIR")
    import agent_governance_evidence_pack as agep
    return agep


def payload(**over):
    p = {"pack_id": "probe-001", "title": "Probe Pack", "generated_at": NOW,
         "agent_overview": {"agent_name": "ProbeAgent", "business_purpose": "probe"},
         "deployment_context": {"environment": "development"}}
    p.update(over)
    return p


def bundle(i=1):
    return {"bundle_id": f"b{i}", "run_id": f"r{i}", "status": "available", "generated_at": NOW, "signed": False, "redacted": False}


def record(decision="approved", reviewer="Rev Iewer", reviewed_at=NOW):
    return {"reviewer": reviewer, "reviewed_at": reviewed_at, "decision": decision}


def codes(pack):
    return {i.code for i in api().validate_evidence_pack(pack).issues if i.severity.value == "error"}


def load(p):
    return api().load_evidence_pack_json(p)  # schema-level load must succeed in every case below


def test_probe_approval_control_properly_evidenced_approved_pack_is_valid():
    pack = load(payload(review_status="approved", review_records=[record()], replay_bundles=[bundle()]))
    r = api().validate_evidence_pack(pack)
    assert r.valid, [i.message for i in r.issues if i.severity.value == "error"]
    assert api().summarize_evidence_pack(pack)["review_status"] == "approved"


@pytest.mark.parametrize("status", ["approved", "approved_with_conditions"])
def test_probe_approval_schema_valid_status_without_any_review_record_is_invalid(status):
    pack = load(payload(review_status=status, replay_bundles=[bundle()]))
    assert codes(pack)  # schema loaded; semantics refuse
    s = api().summarize_evidence_pack(pack)
    assert s["semantic_validation_passed"] is False and s["review_status"] == "invalid"
    with pytest.raises(ValueError):
        api().render_markdown(pack)


@pytest.mark.parametrize("label,records", [
    ("other_decision", [record("rejected")]),
    ("in_review_only", [record("in_review")]),
    ("conditions_for_approved", [record("approved_with_conditions")]),
    ("blank_reviewer", [record(reviewer="   ")]),
    ("missing_reviewed_at", [record(reviewed_at=None)]),
    ("blank_reviewed_at", [record(reviewed_at="  ")]),
])
def test_probe_approval_schema_valid_but_unsupporting_review_records_do_not_approve(label, records):
    pack = load(payload(review_status="approved", review_records=records, replay_bundles=[bundle()]))
    assert not api().validate_evidence_pack(pack).valid, label
    assert api().summarize_evidence_pack(pack)["review_status"] == "invalid"


def test_probe_approval_schema_valid_but_critical_open_risk_or_no_replay_evidence_blocks_approval():
    risk = {"risk_id": "R1", "title": "t", "description": "d", "severity": "critical", "status": "open"}
    crit = load(payload(review_status="approved", review_records=[record()], replay_bundles=[bundle()], risk_register=[risk]))
    assert not api().validate_evidence_pack(crit).valid
    bare = load(payload(review_status="approved", review_records=[record()]))
    assert not api().validate_evidence_pack(bare).valid


def test_probe_approval_importer_output_is_draft_and_cannot_be_promoted_by_editing_status():
    # The producer-v2 example packs are importer outputs (lost-ack, partial, restart, ...): none may carry approval.
    ex = Path(pin_dir("PROBE_EVIDENCE_PACK_DIR")) / "examples" / "producer-v2"
    packs = sorted(ex.glob("*.pack.json"))
    assert len(packs) >= 5
    for f in packs:
        pack = api().load_evidence_pack(f)
        assert pack.review_status.value == "draft" and pack.review_records == [], f.name
        forged = pack.model_copy(update={"review_status": api().ReviewStatus.approved})
        assert not api().validate_evidence_pack(forged).valid, f.name
        assert api().summarize_evidence_pack(forged)["review_status"] == "invalid", f.name


def test_probe_approval_published_example_packs_do_not_claim_approval_without_a_matching_record():
    ex = Path(pin_dir("PROBE_EVIDENCE_PACK_DIR")) / "examples"
    seen = 0
    for f in sorted(ex.glob("*.json")) + sorted((ex / "producer-v2").glob("*.pack.json")):
        pack = api().load_evidence_pack(f)
        seen += 1
        if pack.review_status.value in ("approved", "approved_with_conditions"):
            assert any(r.decision == pack.review_status and r.reviewed_at for r in pack.review_records), f.name
    assert seen >= 5
