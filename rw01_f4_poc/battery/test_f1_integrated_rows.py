"""F-1 INTEGRATED rows F1-A .. F1-G (evidence kind REAL; BUILDER_TESTED developer test code, NOT independent qualification).

Chain: REAL Registry signing (PyNaCl Ed25519, synthetic keys) -> REAL Control Plane `GovernedAgeWorkflow(carry_selection_evidence=True)` -> persisted and RETRIEVED through the
CP's own `BoundedRecordStore` -> REAL Replay `import_bounded_workflow(control_plane_profile=REGISTRY_AUTHENTICATED_SELECTION_F4_PROFILE, registry_evidence_trust=...)` with
operator-supplied trust built from the REAL `RegistryEvidenceVerifierV2` and synthetic trust inputs. Nothing from the record is used as trust. NO bridging, grafting, re-sealing
or edit of a retrieved record: the only edits are explicit TAMPERED / SWAPPED deep copies (original untouched, asserted), always paired with the control positive in the SAME test.

Claim made: A only (Registry selection signature admitted by an operator-supplied verifier at the operator's time). Not claimed: claim B (CP decision authenticated), Registry origin,
operational trust, production adoption. Replay cannot tell the real adapter from an injected stub (NF-2); here the verifier is the real adapter (wrapped only by the observing Spy).
"""
import copy
import json

import pytest

import harness as H
import real_cp_record as R

REAL = pytest.mark.evidence("REAL")
F4 = R.F4_SELECTOR
SEL_MISSING = "selection_evidence_missing"
UNV = "registry_evidence_unverified:"


def rowmark(letter, text):
    return pytest.mark.row("F1-" + letter, text)


@pytest.fixture
def rr():
    return R.produce_real()


def jdump(x):
    return json.dumps(x, sort_keys=True)


def go(rec, op, proposal, **kw):
    """Import through the REAL Replay F4 path; returns (bundle, replay_trust_object)."""
    return R.import_through_replay_f4_with_trust(rec, op, proposal=proposal, **kw)


def control(r):
    """CONTROL POSITIVE: the genuine retrieved record + its operator inputs imports through the F4 selector, all 11 layers pass, claim-A markers exact. Returns (bundle, trust_obj)."""
    bundle, t = go(r.record, r.operator, r.proposal)
    H.assert_exact_claim_a_markers(bundle, profile=F4)
    assert t.verifier.calls == 1 and t.verifier.last["ok"] is True and set(t.verifier.last["layers"].values()) == {"pass"}
    return bundle, t


def refuse(rec, op, proposal, code, *, verifier_calls, layers=None, **kw):
    """The import raises ImportContractError with EXACTLY `code`; no bundle came back; `verifier_calls` times the real adapter was reached; `layers` {layer: value} of its last verdict."""
    out = None
    pass_trust = kw.pop("pass_trust", True)
    spy = H.Spy() if pass_trust else None
    with pytest.raises(H.ImportContractError) as exc:
        out = R.import_through_replay_f4(rec, op, proposal=proposal, verifier=spy, pass_trust=pass_trust, **kw)
    assert out is None
    t = type("T", (), {"verifier": spy})() if pass_trust else None
    assert exc.value.code == code, (exc.value.code, str(exc.value))
    if t is not None:
        assert t.verifier.calls == verifier_calls, t.verifier.calls
        for layer, value in (layers or {}).items():
            assert t.verifier.last["layers"][layer] == value, t.verifier.last["layers"]
    assert "SNAPSHOT" not in str(exc.value)
    return exc.value


# ======================================================================================================================================================== F1-A
@rowmark("A", "REAL CP -> Replay positive: the genuine persisted+retrieved F4 record imports through the explicit F4 selector with the real adapter, 11 layers pass, claim-A markers only, retained decision byte-identical")
@REAL
def test_f1_a_genuine_record_imports_with_exact_claim_a_markers_and_all_11_layers(rr):
    persisted_before = rr.path.read_bytes()
    record_before = jdump(rr.record)
    bundle, t = control(rr)
    # the verifier is the REAL adapter (observed through the pure Spy wrapper), not a stub
    assert type(t.verifier) is H.Spy and type(t.verifier.inner) is H.RegistryEvidenceVerifierV2
    v = t.verifier.last
    assert v["verifier_implementation"]["name"] != "caller-injected-stub" and v["authenticated"] is True and v["code"] is None
    assert set(v["layers"]) == set(H.v.LAYERS_V2) and len(v["layers"]) == 11 and set(v["layers"].values()) == {"pass"}
    # markers (conservative): claim A only
    m = bundle.metadata
    assert m["registry_authenticated"] is False and m["registry_origin"] == "registry_origin_unverified" and m["control_plane_decision_authenticated"] is False
    assert m["registry_authentication_claim"] == "A_selection_signature_per_injected_verifier"
    assert m["control_plane_profile"] == F4 == "registry-authenticated-selection-f4-governed/0.1"
    # the operator's inputs were not read from the record, and the importer did not touch the persisted/retrieved record
    assert rr.path.read_bytes() == persisted_before == rr.retrieved_bytes and jdump(rr.record) == record_before
    # retained decision (incl. selection_evidence) is byte-identical to the persisted one: nothing grafted, re-sealed or inferred
    (rec,) = [x for x in bundle.records if x.record_type == "runtime_decision"]
    persisted_decision = json.loads(persisted_before)["decisions"][0]
    assert jdump(rec.data) == jdump(persisted_decision) == jdump(rr.decision)
    assert rec.data["selection_evidence"] == persisted_decision["selection_evidence"] == rr.evidence
    for absent in ("reason_vocabulary_version", "rule_identity", "reopen_conditions", "evaluated_at", "recorded_at", "check_events"):
        assert absent not in rec.data and absent not in rr.record
    assert set(rec.data["binding"]["runtime_authority"]) == {"effective_configuration"}
    # effective-policy digest: operator-computed (Registry's own function over the operator's host ages and the signed bound) == verdict == the record's f4_ages row == marker
    (ev0,) = m["registry_evidence"]
    row = H.row(rr.record)
    assert ev0["effective_policy_digest"] == v["effective_policy_digest"] == row["effective_policy_digest"] == rr.operator.expected_effective_policy_digest
    assert v["effective_values"] == rr.operator.expected_effective_values() == {"status_max_age_seconds": 60, "approval_max_age_seconds": 60}
    # admission_binding_digest: recomputed independently (Replay's public function over the record, the verdict and the validated operator trust) and sensitive to the evidence
    tr = H.RE.validate_trust(rr.operator.as_replay_trust(verifier=H.Spy()))
    ec = rr.decision["binding"]["runtime_authority"]["effective_configuration"]
    recomputed = H.RE.binding_digest(decision_id=rr.decision["decision_id"], ec=ec, ev=rr.evidence, verdict=v, tr=tr)
    assert ev0["admission_binding_digest"] == recomputed
    other_ev = {**rr.evidence, "record_text": R.produce_real(mat=H.material(40, 30)).evidence["record_text"]}
    assert H.RE.binding_digest(decision_id=rr.decision["decision_id"], ec=ec, ev=other_ev, verdict=v, tr=tr) != recomputed


@rowmark("A", "REAL: the F4 selector admits the record because of the operator's trust, never because of the record: the same record with a stub-free, wrong-snapshot operator is refused by the real adapter")
@REAL
def test_f1_a_trust_comes_from_the_operator_not_the_record(rr):
    control(rr)
    other_snapshot = H.trust(issuers=(R.vs_issuer(H.KEY_ID, H.OTHER_PK),))       # operator admits a DIFFERENT key only
    op = rr.operator.with_(trust_snapshot=other_snapshot, snapshot_ref=(other_snapshot.snapshot_id, other_snapshot.version))
    refuse(rr.record, op, rr.proposal, UNV + "signature_invalid", verifier_calls=1, layers={"authenticity": "refuse"})
    assert not any(k in json.dumps(rr.record) for k in ("trust_snapshot", "expected_host_ages", "verification_time"))


# ======================================================================================================================================================== F1-B
@rowmark("B", "forged signature: the real producer re-run with a WRONG signing key; the operator's snapshot admits only the genuine key -> signature_invalid at layer authenticity, not imported")
@REAL
def test_f1_b_forged_signature_is_refused_at_authenticity(rr):
    forged = R.variant_forged_signature()
    assert forged.evidence["selection_text"] != rr.evidence["selection_text"]
    control(rr)
    bundle, _ = go(rr.record, forged.operator, forged.proposal)                      # CONTROL: the same operator inputs admit the genuine record
    assert bundle.metadata["registry_authentication_claim"] == "A_selection_signature_per_injected_verifier"
    e = refuse(forged.record, forged.operator, forged.proposal, UNV + "signature_invalid", verifier_calls=1, layers={"authenticity": "refuse", "record_binding": "pass", "scope": "pass"})
    assert "tenant" not in str(e.args[0])


# ======================================================================================================================================================== F1-C
@rowmark("C", "wrong scope: the OPERATOR's ExpectedContext/action/operation differs from the record scope -> registry_evidence_scope_mismatch (Replay pre-check, verifier never reached)")
@REAL
@pytest.mark.parametrize("kind", ["tenant", "institution", "domain", "consumer", "operation", "action"])
def test_f1_c_operator_scope_mismatch_is_refused_before_the_verifier(rr, kind):
    control(rr)                                                                       # CONTROL positive with the unmodified operator inputs
    bad = R.variant_wrong_context(kind)
    assert bad.operator != rr.operator and bad.record["decisions"][0]["binding"]["tenant_id"] == rr.decision["binding"]["tenant_id"]   # same genuine scope; only the OPERATOR differs
    refuse(bad.record, bad.operator, bad.proposal, "registry_evidence_scope_mismatch", verifier_calls=0)


@rowmark("C", "wrong scope: a genuine record produced end to end for ANOTHER tenant is refused against the default operator context")
@REAL
def test_f1_c_genuine_record_of_another_tenant_is_refused(rr):
    control(rr)
    other = R.variant_wrong_tenant_record()
    assert other.decision["binding"]["tenant_id"] != rr.decision["binding"]["tenant_id"]
    refuse(other.record, other.operator, other.proposal, "registry_evidence_scope_mismatch", verifier_calls=0)


# ======================================================================================================================================================== F1-D
@rowmark("D", "substituted record (i): a different GENUINE Registry record text swapped into the carried evidence (TAMPERED copy; original untouched) -> real adapter refuses at record_binding")
@REAL
def test_f1_d_i_substituted_registry_record_text_is_refused_at_record_binding(rr):
    other = R.produce_real(mat=H.material(40, 30))                                    # a different GENUINE signed record
    assert other.evidence["record_text"] != rr.evidence["record_text"]
    before = jdump(rr.record)
    control(rr)
    tampered = R.tampered_copy_record_text(rr, lambda _t: other.evidence["record_text"])    # TAMPERED copy
    assert tampered != rr.record and jdump(rr.record) == before                       # genuine record untouched
    refuse(tampered, rr.operator, rr.proposal, UNV + "record_digest_mismatch", verifier_calls=1,
           layers={"record_binding": "refuse", "authenticity": "pass", "scope": "pass", "disposition": "not_evaluated"})


@rowmark("D", "substituted record (ii): the carried evidence is the evidence of a DIFFERENT genuine CP run; observed behaviour and its limits")
@REAL
def test_f1_d_ii_evidence_of_a_different_genuine_run_observed_behaviour_and_limits(rr):
    control(rr)
    before = jdump(rr.record)

    def swapped(donor):
        rec = copy.deepcopy(rr.record)                                                # SWAPPED copy: donor's selection_evidence spliced into rr's decision; originals untouched
        rec["decisions"][0]["selection_evidence"] = copy.deepcopy(donor.evidence)
        return rec

    # (1) other run signed a DIFFERENT bound (40/30): a genuine, valid selection -> the REAL adapter admits it on all 11 layers; Replay then REFUSES because the verdict's effective
    #     policy digest/values (operator host ages + the donor's signed bound) differ from the f4_ages row of THIS record's effective_configuration.
    donor_bound = R.produce_real(mat=H.material(40, 30))
    e = refuse(swapped(donor_bound), rr.operator, rr.proposal, "registry_evidence_effective_digest_mismatch", verifier_calls=1)
    # (2) other run for ANOTHER tenant: refused by the real adapter itself (authority/scope layers), code issuer_not_authorized
    donor_tenant = R.variant_wrong_tenant_record()
    refuse(swapped(donor_tenant), rr.operator, rr.proposal, UNV + "issuer_not_authorized", verifier_calls=1, layers={"authority": "refuse", "scope": "refuse"})
    # (3) LIMIT, asserted not hidden: a SECOND genuine run with the identical signed material carries byte-identical evidence (the signature binds no run id/decision id), so swapping it in
    #     is indistinguishable and is ADMITTED. Replay's protections here are scope + operator context + effective-policy digest + record binding, not run identity.
    donor_same = R.produce_real()
    assert donor_same.evidence == rr.evidence and donor_same.decision_id != rr.decision_id
    bundle, _ = go(swapped(donor_same), rr.operator, rr.proposal)
    assert bundle.metadata["registry_authentication_claim"] == "A_selection_signature_per_injected_verifier"
    assert jdump(rr.record) == before


# ======================================================================================================================================================== F1-E
@rowmark("E", "effective-policy digest mismatch: operator host-age expectation differs from the record's f4_ages row -> registry_evidence_effective_digest_mismatch (verifier passes, Replay cross-check refuses)")
@REAL
@pytest.mark.parametrize("ages", [(30, 30), (600, 600)])
def test_f1_e_operator_expected_effective_policy_differs_from_the_record(rr, ages):
    control(rr)
    host = {"status_max_age_seconds": ages[0], "approval_max_age_seconds": ages[1]}
    bad = R.variant_mutated_effective_policy(host_ages=host)
    assert bad.operator.expected_effective_policy_digest != H.row(rr.record)["effective_policy_digest"]       # the operator's independently computed digest differs from the record's row
    assert bad.operator.expected_effective_policy_digest != rr.operator.expected_effective_policy_digest
    refuse(bad.record, bad.operator, bad.proposal, "registry_evidence_effective_digest_mismatch", verifier_calls=1, layers={"disposition": "pass", "record_binding": "pass"})


# ======================================================================================================================================================== F1-F
@rowmark("F", "missing evidence: real CP run WITHOUT carry_selection_evidence -> selection_evidence_missing (verifier never reached)")
@REAL
def test_f1_f_run_without_carry_selection_evidence_is_refused_as_missing(rr):
    control(rr)
    nc = R.variant_no_carry()
    assert nc.decision["result"] == "authorized" and "selection_evidence" not in nc.decision
    refuse(nc.record, nc.operator, nc.proposal, SEL_MISSING, verifier_calls=0)
    # also: removing the member from the genuine record (TAMPERED copy) gives the same refusal
    stripped = copy.deepcopy(rr.record)
    del stripped["decisions"][0]["selection_evidence"]
    refuse(stripped, rr.operator, rr.proposal, SEL_MISSING, verifier_calls=0)


# ======================================================================================================================================================== F1-G
@rowmark("G", "authenticated-profile downgrade (a): the F4 selector WITHOUT operator trust is refused registry_evidence_trust_missing (never structural-only)")
@REAL
def test_f1_g_a_f4_selector_without_trust_is_refused(rr):
    control(rr)
    refuse(rr.record, rr.operator, rr.proposal, "registry_evidence_trust_missing", verifier_calls=0, pass_trust=False)


@rowmark("G", "authenticated-profile downgrade (b): plain/legacy governed profiles and no selector never import the real record (resolution journal), never structural-only or caller-trusted")
@REAL
@pytest.mark.parametrize("selector", [None, H.OLD_SELECTOR])
def test_f1_g_b_legacy_profiles_and_no_selector_refuse_the_real_record(rr, selector):
    control(rr)
    e = refuse(rr.record, rr.operator, rr.proposal, None, verifier_calls=0, pass_trust=False, selector=selector)
    assert "resolution journal missing" in str(e)
    # caller-trusted match mode (expected digest, no trust) does not rescue it either
    ec = rr.decision["binding"]["runtime_authority"]["effective_configuration"]
    e2 = refuse(rr.record, rr.operator, rr.proposal, None, verifier_calls=0, pass_trust=False, selector=H.OLD_SELECTOR, expected_effective_configuration_digest=ec["digest"])
    assert "resolution journal missing" in str(e2)


@rowmark("G", "authenticated-profile downgrade (b2): the OLD authenticated selector (registry-authenticated-selection/0.1) without trust is trust_missing; with trust it still refuses the F4 shape (no F4 relaxation without the F4 selector)")
@REAL
def test_f1_g_b2_old_authenticated_selector_does_not_admit_the_f4_shape(rr):
    control(rr)
    refuse(rr.record, rr.operator, rr.proposal, "registry_evidence_trust_missing", verifier_calls=0, pass_trust=False, selector=H.SELECTOR)
    e = refuse(rr.record, rr.operator, rr.proposal, None, verifier_calls=0, selector=H.SELECTOR)
    assert "resolution journal missing" in str(e)


@rowmark("G", "authenticated-profile downgrade (c): trust passed with a non-F4 selector / conflicting modes / non-CUR revision is refused with the specific code, verifier never reached")
@REAL
def test_f1_g_c_trust_with_non_f4_selector_and_conflicting_modes_are_refused(rr):
    control(rr)
    for selector in (None, H.OLD_SELECTOR):
        refuse(rr.record, rr.operator, rr.proposal, "registry_evidence_unsupported_profile", verifier_calls=0, selector=selector)
    ec = rr.decision["binding"]["runtime_authority"]["effective_configuration"]
    refuse(rr.record, rr.operator, rr.proposal, "registry_evidence_conflicting_modes", verifier_calls=0, expected_effective_configuration_digest=ec["digest"])
    e = refuse(rr.record, rr.operator, rr.proposal, None, verifier_calls=0, revision=H.I.CONTROL_PLANE_REVISION)
    assert "unsupported Control Plane profile selector" in str(e)
    for bad_selector in (F4 + " ", F4.upper(), "registry-authenticated-selection-f4-governed/0.2"):
        e = refuse(rr.record, rr.operator, rr.proposal, None, verifier_calls=0, selector=bad_selector)
        assert "unsupported Control Plane profile selector" in str(e) or e.code == "registry_evidence_unsupported_profile"


# ======================================================================================================================================================== old BRIDGED rows
@rowmark("BRIDGED", "honest status of the old BRIDGED rows: still COMPONENT evidence only (grafted journal members, re-sealed) -- not CP-to-Replay integration; the REAL integration is F1-A..F1-G")
@REAL
def test_old_bridged_positive_row_is_still_component_evidence_only(rr, tmp_path):
    import test_e2e_rows as E
    marks = {m.args[0] for m in E.test_n01_valid_selection_is_admitted_with_exactly_the_claim_a_markers.pytestmark if m.name == "evidence"}
    assert marks == {"BRIDGED"}
    pr = H.produce(tmp_path, H.material())
    cp, proposal = H.bridge(pr)
    # the bridged record is NOT what the CP wrote: it has a journal and runtime-authority members the real record lacks, and a different set of top-level members
    assert "check_events" in cp and "check_events" not in rr.record and cp != pr.run
    assert "reason_vocabulary_version" in cp["decisions"][0] and "reason_vocabulary_version" not in rr.decision
    assert set(cp["decisions"][0]["binding"]["runtime_authority"]) != set(rr.decision["binding"]["runtime_authority"])
    # it imports only under the OLD selector (claim A markers carry the OLD profile constant), and the real record does not
    bundle, _ = H.admitted(cp, proposal)
    assert bundle.metadata["control_plane_profile"] == H.SELECTOR != F4
    refuse(rr.record, rr.operator, rr.proposal, None, verifier_calls=0, selector=H.SELECTOR)


# ======================================================================================================================================================== F1-G (d)
@rowmark("G", "closed absence under the F4 selector (Replay ca94d6a8): journal / vocabulary members added to the persisted record, even EMPTY, are refused undeclared_member (TAMPERED copies; control positive first)")
@REAL
@pytest.mark.parametrize("member", ["check_events", "vocabulary_changes"])
def test_f1_g_d_present_even_empty_journal_members_are_refused(rr, member):
    control(rr)
    tampered = copy.deepcopy(rr.record)
    tampered[member] = []
    assert tampered != rr.record
    refuse(tampered, rr.operator, rr.proposal, "undeclared_member", verifier_calls=0)
