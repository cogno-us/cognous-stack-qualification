"""F-1 producer-side facts of the REAL CP F4 record (evidence kind REAL). Needs NO Replay change; the Replay call is `real_cp_record.import_through_replay_f4`, exercised by test_f1_integrated_rows.py (rows F1-A..F1-G).

Negatives re-run the real producer with a different cause. Where the Registry adapter cannot see the cause (action id, effective-policy expectation, substitution of a
different genuine record) the test pins that fact (adapter PASS) and asserts the discrepancy is visible in the data Replay must cross-check later; it does not claim a refusal.
"""
import hashlib
import json

import pytest

import harness as H
import real_cp_record as R

REAL = pytest.mark.evidence("REAL")
ROW = pytest.mark.row("F-1", "real CP F4 record producer: persisted+retrieved record, carried evidence, real adapter verdicts on it")


@pytest.fixture(scope="module")
def rr(tmp_path_factory):
    # module-scoped fixtures run before the autouse clock fixture is applied: pin the synthetic clock for the producer explicitly
    import agent_control_plane.bounded as b, agent_control_plane.registry_f4_age_governance as g
    old = b._now, g._now
    b._now = g._now = lambda: H.NOW
    try:
        yield R.produce_real(tmp_path_factory.mktemp("real"))
    finally:
        b._now, g._now = old


def sha(t):
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


@ROW
@REAL
def test_retrieved_record_is_byte_identical_to_what_cp_wrote(rr):
    assert rr.retrieved_bytes == rr.written_bytes                       # fresh BoundedRecordStore.load() did not change the file
    assert rr.record == json.loads(rr.written_bytes)
    assert rr.record == rr.retrieved_model                                # CP's own validated model view equals the persisted document (no hidden/dropped member)
    assert rr.decision["result"] == "authorized" and rr.decision["decision_id"] == rr.decision_id


@ROW
@REAL
def test_selection_evidence_at_documented_location_with_exact_signed_bytes(rr):
    d = rr.decision
    assert "selection_evidence" in d and "selection_evidence" not in d["binding"]          # top-level of the decision, outside `binding`
    e = rr.evidence
    assert set(e) == {"version", "contract_version", "family", "operation_id", "verified_at", "record_text", "selection_text"}
    assert (e["version"], e["contract_version"], e["family"], e["operation_id"]) == ("selection-evidence/0.1", "r08-v2", H.F4, H.OPERATION)
    assert e["record_text"] == rr.material.record_text and e["selection_text"] == rr.material.selection_text
    assert e["selection_text"].encode("utf-8") == rr.material.selection_text.encode("utf-8") and sha(e["selection_text"]) == sha(rr.material.selection_text)


@ROW
@REAL
def test_real_adapter_passes_all_11_layers_with_operator_inputs(rr):
    v = R.verify_with_real_adapter(rr.evidence, rr.operator)
    assert v["ok"] is True and v["code"] is None
    assert len(v["layers"]) == 11 and set(v["layers"].values()) == {"pass"}, v["layers"]
    assert v["effective_policy_digest"] == rr.operator.expected_effective_policy_digest
    assert v["effective_values"] == rr.operator.expected_effective_values() == {"status_max_age_seconds": 60, "approval_max_age_seconds": 60}
    assert v["selection_text_sha256"] == sha(rr.evidence["selection_text"]) and v["record_text_sha256"] == sha(rr.evidence["record_text"])


@ROW
@REAL
def test_operator_inputs_are_independent_of_the_record(rr):
    ec = rr.decision["binding"]["runtime_authority"]["effective_configuration"]["members"]
    assert ec["scope"]["action_id"] == rr.operator.expected_action_id and ec["scope"]["tenant_id"] == rr.operator.expected_context["tenant"]
    assert rr.operator.trust_snapshot is not rr.material.host_trust            # the operator's snapshot object is not the host's; same synthetic issuer by construction
    assert not any(k in json.dumps(rr.record) for k in ("trust_snapshot", "expected_host_ages", "verification_time"))


@ROW
@REAL
def test_negative_forged_signature_refused_at_authenticity():
    v = R.verify_with_real_adapter(*(lambda r: (r.evidence, r.operator))(R.variant_forged_signature()))
    assert v["ok"] is False and v["code"] == "signature_invalid" and v["layers"]["authenticity"] == "refuse"


@ROW
@REAL
@pytest.mark.parametrize("kind,code", [("tenant", "selection_scope_mismatch"), ("institution", "selection_scope_mismatch"), ("domain", "selection_scope_mismatch"),
                                       ("consumer", "selection_consumer_mismatch"), ("operation", "selection_operation_mismatch")])
def test_negative_wrong_expected_context_refused_at_scope(kind, code):
    r = R.variant_wrong_context(kind)
    v = R.verify_with_real_adapter(r.evidence, r.operator)
    assert v["ok"] is False and v["code"] == code and v["layers"]["scope"] == "refuse"


@ROW
@REAL
def test_negative_other_tenant_genuine_record_refused_by_operator_snapshot():
    r = R.variant_wrong_tenant_record()
    assert r.decision["binding"]["tenant_id"] == "tenant-other"
    v = R.verify_with_real_adapter(r.evidence, r.operator)
    assert v["ok"] is False and v["code"] == "issuer_not_authorized" and v["layers"]["authority"] == "refuse"


@ROW
@REAL
def test_pin_wrong_expected_action_is_not_visible_to_adapter_but_visible_in_record():
    """OBSERVATION: the adapter request carries no action id; a wrong expected_action_id is a Replay-side cross-check against the record's binding scope."""
    r = R.variant_wrong_context("action")
    assert R.verify_with_real_adapter(r.evidence, r.operator)["ok"] is True
    assert r.decision["binding"]["runtime_authority"]["effective_configuration"]["members"]["scope"]["action_id"] != r.operator.expected_action_id



@ROW
@REAL
def test_pin_substituted_genuine_record_passes_adapter_but_digest_differs_from_original():
    """OBSERVATION: another GENUINE selection verifies PASS; only the effective-policy digest comparison (Replay-side) distinguishes it from the original record."""
    a, b = R.variant_substituted()
    va, vb = R.verify_with_real_adapter(a.evidence, a.operator), R.verify_with_real_adapter(b.evidence, a.operator)
    assert va["ok"] and vb["ok"]
    assert va["effective_policy_digest"] != vb["effective_policy_digest"]
    assert vb["effective_policy_digest"] != a.operator.expected_effective_policy_digest and va["effective_policy_digest"] == a.operator.expected_effective_policy_digest
    assert a.evidence["selection_text"] != b.evidence["selection_text"]


@ROW
@REAL
def test_pin_mutated_effective_policy_expectation_yields_different_digest():
    """OBSERVATION: adapter recomputes the effective policy with the OPERATOR's host ages; the verdict digest then differs from the record's own f4_ages row."""
    r = R.variant_mutated_effective_policy()
    v = R.verify_with_real_adapter(r.evidence, r.operator)
    assert v["ok"] is True and v["effective_values"] == {"status_max_age_seconds": 30, "approval_max_age_seconds": 30}
    assert v["effective_policy_digest"] == r.operator.expected_effective_policy_digest
    base = R.produce_real()
    assert v["effective_policy_digest"] != R.verify_with_real_adapter(base.evidence, base.operator)["effective_policy_digest"]


@ROW
@REAL
def test_negative_missing_evidence_when_carry_off():
    r = R.variant_no_carry()
    assert r.decision["result"] == "authorized" and "selection_evidence" not in r.decision
    with pytest.raises(KeyError):
        R.verify_with_real_adapter(r.decision["selection_evidence"], r.operator)


@ROW
@REAL
def test_tampered_copy_signature_over_changed_bytes_refused_genuine_untouched(rr):
    """TAMPERED copy (explicit): selection_text altered after signing -> adapter refuses; the genuine record is unchanged."""
    before = json.dumps(rr.record, sort_keys=True)
    bad = R.tampered_copy_selection_text(rr, lambda t: t.replace("consumer-test", "consumer-XXXX", 1))
    v = R.verify_with_real_adapter(bad["decisions"][0]["selection_evidence"], rr.operator)
    assert v["ok"] is False
    assert json.dumps(rr.record, sort_keys=True) == before and R.verify_with_real_adapter(rr.evidence, rr.operator)["ok"] is True
