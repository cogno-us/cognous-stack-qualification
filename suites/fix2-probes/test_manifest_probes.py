"""Action manifest probes (PROBE2_MANIFEST_DIR): a runtime proposal checked against an action that is blocked or has no limits.

A declaration mismatch is reported for a proposal that the manifest does not permit. An action whose posture is ``block`` permits
no proposal at all, and an action without effect limits (or without a ceiling on the amount) cannot bound the amount and effect
count of one: a proposal of 1e12 USD and 1000 effects against either is a mismatch. The valid example manifest and a proposal
inside its limits are the controls.
"""
import copy

import pytest

from conftest import checkout

HUGE = {"amount": 1e12, "effects": 1000}


@pytest.fixture(autouse=True)
def _pin():
    checkout("PROBE2_MANIFEST_DIR")


def manifest():
    from agent_action_manifest.loader import load_manifest
    from pathlib import Path
    return load_manifest(Path(checkout("PROBE2_MANIFEST_DIR")) / "examples" / "refund_integration_v1_1.manifest.json")


def proposal(m, **override):
    from agent_action_manifest.binding import manifest_digest, payload_digest
    from agent_action_manifest.models import RuntimeActionProposal
    payload = {"customer_id": "customer-001", "refund_reason": "duplicate charge"}
    fields = dict(
        manifest_id=m.manifest_id, manifest_version=m.manifest_version, manifest_digest=manifest_digest(m),
        actor="urn:cognous:actor:synthetic-refund-agent", principal="urn:cognous:principal:synthetic-customer-service",
        action_id="urn:cognous:action:refund-issue-routine-v1", adapter_id="urn:cognous:adapter:synthetic-refund-v1",
        target="urn:cognous:synthetic-account:customer-001", payload=payload, payload_commitment=payload_digest(payload),
        requested_permissions=["refund.issue.routine"], amount=50, unit="USD", effects=1,
        authority_context_ref="urn:cognous:alvorada:public-stack-profile:0.1.0",
        requirement_id="urn:cognous:authority-requirement:refund-routine-v1", risk_metadata={"consequence_tier": "T1"},
        not_before="2026-10-05T00:00:00Z", expires_at="2026-10-06T00:00:00Z", correlation_id="corr-001", run_id="run-001",
        expected_side_effects=["synthetic_refund_record_created"], evidence_refs=["urn:cognous:evidence:refund-entitlement"])
    fields.update(override)
    return RuntimeActionProposal(**fields)


def mismatches(m, **override):
    from agent_action_manifest.binding import proposal_mismatches
    return proposal_mismatches(m, proposal(m, **override))


def with_action(change):
    m = copy.deepcopy(manifest())
    change(m.actions[0])
    return m


def blocked_at_action(action):
    action.default_action = "block"


def blocked_by_manifest_default(m):
    m.default_action = "block"
    m.actions[0].default_action = None
    return m


def read_without_limits(action):
    action.action_type = "read"
    action.effect_limits = None
    action.authority_required = []


# ---------------------------------------------------------------------------------------------------------- controls
def test_control_a_proposal_inside_the_declared_limits_has_no_mismatch():
    assert mismatches(manifest()) == []


def test_control_a_proposal_above_the_declared_limits_is_a_mismatch():
    found = mismatches(manifest(), **HUGE)
    assert {"amount_exceeded", "effect_count_exceeded"} <= set(found)


def test_control_an_action_that_escalates_by_default_still_binds_a_proposal_inside_its_limits():
    m = with_action(lambda a: setattr(a, "default_action", "escalate"))
    assert mismatches(m) == []


def test_control_an_action_without_limits_is_already_an_invalid_manifest_when_it_writes():
    m = with_action(lambda a: setattr(a, "effect_limits", None))
    assert "invalid_manifest" in mismatches(m, **HUGE)


# ---------------------------------------------------------------------------------------------------------- probes
def test_control_a_huge_proposal_against_a_blocked_action_is_a_mismatch_through_its_limits():
    m = with_action(blocked_at_action)
    assert mismatches(m, **HUGE) != []


def test_probe_a_proposal_inside_the_limits_against_a_blocked_action_is_a_mismatch():
    m = with_action(blocked_at_action)
    assert mismatches(m) != []


def test_probe_a_proposal_inside_the_limits_against_an_action_blocked_by_the_manifest_default_is_a_mismatch():
    m = copy.deepcopy(manifest())
    blocked_by_manifest_default(m)
    assert mismatches(m) != []


def test_probe_a_huge_proposal_is_not_judged_by_the_limits_alone_when_the_action_is_blocked():
    """The mismatch list for a blocked action names more than the limit codes a permitted action would give."""
    m = with_action(blocked_at_action)
    limited_only = set(mismatches(with_action(lambda a: setattr(a, "default_action", "escalate")), **HUGE))
    assert set(mismatches(m, **HUGE)) - limited_only != set()


def test_probe_a_huge_proposal_against_an_action_with_no_effect_limits_is_a_mismatch():
    m = with_action(read_without_limits)
    from agent_action_manifest.validator import validate_manifest
    assert validate_manifest(m).valid, "the manifest is otherwise valid: a read action may declare no limits"
    assert mismatches(m, **HUGE) != []
