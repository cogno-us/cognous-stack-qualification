"""End-to-end rows N01..N22, N27, N28 and the integration finding F-1.

Chain under test:  Registry (real Ed25519, synthetic seeds) -> real CP F4 workflow with carry_selection_evidence=True -> carried exact signed bytes -> real Replay
`import_bounded_workflow` under registry-authenticated-selection/0.1 with operator-supplied INDEPENDENT trust inputs and the real `RegistryEvidenceVerifierV2`.
Every negative asserts the SPECIFIC typed code, the layer that refused (Replay pre-check vs the real Registry adapter and which Registry layer), and that no bundle came back.
"""
import copy
import json

import pytest

import harness as H
from harness import (CP_PR_HEAD, F4, Spy, admitted, bridge, do_import, make_trust, material, produce, real_decision, refused, reseal, row, trust, withdrawal_text)

BRIDGED = pytest.mark.evidence("BRIDGED")
REAL = pytest.mark.evidence("REAL")


@pytest.fixture
def pr(tmp_path):
    return produce(tmp_path, material())


def wire_unbridged(pr):
    return copy.deepcopy(pr.run), pr.proposal


# =============================================================================================================== F-1 (finding)
# NOTE (F-1 recovery): the former intentional-FAIL row `test_f1_a_real_cp_f4_run_record_is_importable_by_replay_authenticated_profile` is REPLACED by the real passing integration
# row F1-A in test_f1_integrated_rows.py (F4 selector, Replay 6651abef, tree identical to former head ca94d6a8). The tests below stay: they pin that the OLD selectors/legacy profiles still refuse a real F4 record.


@pytest.mark.row("F-1", "the same refusal happens WITHOUT the PoC: flag off, plain CUR import and the pre-existing Registry-governed profile (so the gap is pre-existing, not caused by carriage)")
@REAL
@pytest.mark.parametrize("selector", [None, H.OLD_SELECTOR])
def test_f1_the_gap_is_independent_of_carriage_real_f4_records_never_import_at_current_generation(tmp_path, selector):
    pr0 = produce(tmp_path, material(), carry=False)
    assert "selection_evidence" not in real_decision(pr0)
    with pytest.raises(H.ImportContractError) as exc:
        H.I.import_bounded_workflow(copy.deepcopy(pr0.run), proposal=pr0.proposal, control_plane_revision=H.CUR_CP, control_plane_profile=selector)
    assert "resolution journal missing" in str(exc.value)


@pytest.mark.row("F-1", "root cause: the real F4 decision has no check_events journal and no runtime-authority/0.1 binding members (F4 refuses runtime_authority_profile)")
@REAL
def test_f1_root_cause_is_the_absence_of_the_runtime_authority_journal_and_binding(pr):
    d = real_decision(pr)
    assert "check_events" not in pr.run
    assert set(d["binding"]["runtime_authority"]) == {"effective_configuration"}
    assert "reason_vocabulary_version" not in d
    with pytest.raises(PermissionError):
        H.GovernedAgeWorkflow(scope=H.SCOPE, selection_source=H.Source(material()), verifier=H.ev.Ed25519Verifier(), allow_test_time=True, construction_time=H.NOW,
                              manifest=H.manifest(), runtime_authority_profile=object(), destination=H.LocalRefundDestination(pr.tmp / "x.json"),
                              records=H.BoundedRecordStore(pr.tmp / "x2.json", "run-x"), resolver=H.tenant_resolver_for(H.tenant_proposal()))


@pytest.mark.row("F-1", "cross-check that makes the bridge honest: Replay's own digest function reproduces the REAL CP effective_configuration digest, and the bridged record carries the real bytes verbatim")
@REAL
def test_f1_bridge_uses_the_real_effective_configuration_and_the_real_carried_bytes_verbatim(pr):
    real = real_decision(pr)
    ec = real["binding"]["runtime_authority"]["effective_configuration"]
    assert H.EC.digest_of(ec["version"], ec["members"]) == ec["digest"]
    cp, _ = bridge(pr)
    assert cp["decisions"][0]["binding"]["runtime_authority"]["effective_configuration"] == ec
    assert cp["decisions"][0]["selection_evidence"] == real["selection_evidence"]
    assert real["selection_evidence"]["record_text"] == pr.material.record_text and real["selection_evidence"]["selection_text"] == pr.material.selection_text


# =============================================================================================================== N01
@pytest.mark.row("N01", "valid: real Registry signature carried by the real CP decision, admitted by Replay authenticated profile via the real adapter; exact marker set")
@BRIDGED
def test_n01_valid_selection_is_admitted_with_exactly_the_claim_a_markers(pr):
    cp, proposal = bridge(pr)
    spy = Spy()
    bundle, _ = admitted(cp, proposal, make_trust(verifier=spy))
    ev0 = H.assert_exact_claim_a_markers(bundle)
    assert spy.calls == 1 and spy.last["ok"] is True and spy.last["authenticated"] is True and set(spy.last["layers"].values()) == {"pass"}
    assert spy.last["selection_text_sha256"] == H.sha256_text(pr.material.selection_text) and spy.last["record_text_sha256"] == H.sha256_text(pr.material.record_text)
    assert ev0["effective_policy_digest"] == row(cp)["effective_policy_digest"] == spy.last["effective_policy_digest"]
    assert spy.last["effective_values"] == H.HOST_AGES
    assert not set(bundle.metadata) - H.SUCCESS_KEYS - set(do_import_structural_keys(cp, proposal))


def do_import_structural_keys(cp, proposal):
    """The metadata keys of the SAME record imported structurally (old governed selector, evidence stripped): the structural keys the success path may add to."""
    c2 = copy.deepcopy(cp)
    c2["decisions"][0].pop("selection_evidence")
    return list(do_import(c2, proposal, selector=H.OLD_SELECTOR).metadata)


@pytest.mark.row("N01", "valid: the carried bytes ARE the signed material, and Registry's own verify (independent call, not via Replay) admits exactly them with the operator's trust")
@REAL
def test_n01_carried_bytes_are_the_exact_signed_material_and_registry_admits_them_directly(pr):
    ev = real_decision(pr)["selection_evidence"]
    ad = H.ev.Ed25519Verifier()
    ctx = H.c.ExpectedContext(H.CONSUMER, H.TENANT_ID, H.INSTITUTION, H.DOMAIN, H.OPERATION)
    res = H.vs.verify_f4_selection_v2(ev["selection_text"], ev["record_text"], ctx, trust(), ad, H.NOW, min_trust_snapshot_version=1, last_accepted_snapshot=None,
                                      key_admission=ad.key_admission)
    assert res.admitted is True and res.code is None and dict(res.layers) == {n: "pass" for n in H.v.LAYERS_V2}
    assert (ev["version"], ev["contract_version"], ev["family"], ev["operation_id"]) == ("selection-evidence/0.1", "r08-v2", F4, H.OPERATION)


# =============================================================================================================== N02 forged signature
def _swap_selection(cp, text):
    cp = copy.deepcopy(cp)
    cp["decisions"][0]["selection_evidence"]["selection_text"] = text
    return cp


@pytest.mark.row("N02", "forged signature: one signature byte flipped in the carried selection -> real Registry layer authenticity refuses (signature_invalid)")
@BRIDGED
def test_n02_flipped_signature_byte_is_signature_invalid_at_the_authenticity_layer(pr):
    cp, proposal = bridge(pr)
    env = json.loads(pr.material.selection_text)
    raw = bytearray(H.base64.b64decode(env["signatures"][0]["signature"]))
    raw[0] ^= 1
    env["signatures"][0]["signature"] = H.base64.b64encode(bytes(raw)).decode()
    t = make_trust()
    e = refused(_swap_selection(cp, json.dumps(env, sort_keys=True)), proposal, t, "registry_evidence_unverified:signature_invalid", reached_verifier=True, layer="authenticity",
                adapter_code="signature_invalid")
    assert t.verifier.last["authenticated"] is False


@pytest.mark.row("N02", "forged signature: re-signed with a different key under the trusted key id -> signature_invalid at authenticity")
@BRIDGED
def test_n02_statement_resigned_by_another_key_is_signature_invalid(pr):
    cp, proposal = bridge(pr)
    forged = H.envelope_text(pr.material.stmt, sk=H.OTHER_SK)
    refused(_swap_selection(cp, forged), proposal, make_trust(), "registry_evidence_unverified:signature_invalid", reached_verifier=True, layer="authenticity",
            adapter_code="signature_invalid")


@pytest.mark.row("N02", "forged signature at the CP boundary: the real CP workflow refuses forged material at construction/decision (no decision, nothing carried)")
@REAL
def test_n02_cp_boundary_refuses_a_forged_selection_before_any_decision_is_written(tmp_path):
    forged = material(sk=H.OTHER_SK)
    with pytest.raises(PermissionError) as exc:
        produce(tmp_path, forged)
    assert exc.value.refusal.registry_code == "signature_invalid"
    assert not (tmp_path / "run.json").exists() or json.loads((tmp_path / "run.json").read_text()).get("decisions", []) == []


# =============================================================================================================== N03 / N04 / N20
@pytest.mark.row("N03", "unknown signer: the CP host trusted key 2 (genuine, authorised); the operator's INDEPENDENT snapshot does not list it -> issuer_untrusted at the authenticity-adjacent issuer check")
@BRIDGED
def test_n03_signer_unknown_to_the_operator_snapshot_is_issuer_untrusted(tmp_path):
    host = trust(issuers=(H.v.IssuerEntry(H.OTHER_KEY_ID, "issuer-test-2", "ed25519", H.OTHER_PK, (H.grant(),)),))
    pr2 = produce(tmp_path, material(host_trust=host, sk=H.OTHER_SK, key_id=H.OTHER_KEY_ID, pub=H.OTHER_PK))
    cp, proposal = bridge(pr2)
    t = make_trust()   # operator snapshot: only key 1
    refused(cp, proposal, t, "registry_evidence_unverified:issuer_untrusted", reached_verifier=True, adapter_code="issuer_untrusted")
    assert t.verifier.last["authenticated"] is False
    assert admitted(cp, proposal, make_trust(snapshot=host))[0].metadata["registry_evidence"][0]["issuer_id"] == "issuer-test-2"   # control: with the operator trusting key 2 it is admitted


@pytest.mark.row("N04", "wrong issuer grant: the signer is trusted but NOT authorised for this operation in the operator snapshot -> issuer_not_authorized (authenticated True, ok False)")
@BRIDGED
def test_n04_issuer_without_the_grant_is_issuer_not_authorized(pr):
    cp, proposal = bridge(pr)
    other = trust(issuers=(H.v.IssuerEntry(H.KEY_ID, "issuer-test-1", "ed25519", H.PK, (H.grant(operation="some-other-operation"),)),))
    t = make_trust(snapshot=other)
    refused(cp, proposal, t, "registry_evidence_unverified:issuer_not_authorized", reached_verifier=True, adapter_code="issuer_not_authorized")
    assert t.verifier.last["authenticated"] is True and t.verifier.last["layers"]["authenticity"] == "pass"   # N20 shape: authenticated is not admission


@pytest.mark.row("N20", "authenticated=True but ok=False (unauthorised scope grant) is refused: the Replay gate admits on ok AND code AND all eleven layers, never on authenticated")
@BRIDGED
def test_n20_authenticated_true_with_ok_false_is_refused(pr):
    cp, proposal = bridge(pr)
    t = make_trust(snapshot=trust(issuers=(H.v.IssuerEntry(H.KEY_ID, "issuer-test-1", "ed25519", H.PK, (H.grant(tenant="tenant-zzz"),)),)))
    refused(cp, proposal, t, "registry_evidence_unverified:issuer_not_authorized", reached_verifier=True)
    assert t.verifier.last["authenticated"] is True and t.verifier.last["ok"] is False


@pytest.mark.row("N20", "Replay's verdict gate on a REAL adapter verdict altered in flight: ok True but a layer not pass / authenticated False / code set -> registry_evidence_not_authenticated (Replay-side gate only)")
@BRIDGED
@pytest.mark.parametrize("mutation", ["layer_not_evaluated", "layer_refuse", "authenticated_false", "code_set"])
def test_n20_replay_gate_refuses_an_ok_verdict_that_is_not_fully_authenticated(pr, mutation):
    def mutate(verdict, request):
        if mutation == "layer_not_evaluated":
            verdict["layers"]["epoch"] = "not_evaluated"
        elif mutation == "layer_refuse":
            verdict["layers"]["revocation"] = "refuse"
        elif mutation == "authenticated_false":
            verdict["authenticated"] = False
        else:
            verdict["code"] = "selection_expired"
        return verdict
    cp, proposal = bridge(pr)
    refused(cp, proposal, make_trust(verifier=Spy(mutate=mutate)), "registry_evidence_not_authenticated", reached_verifier=True)


# =============================================================================================================== N05 / N06 / N07 scope
@pytest.mark.row("N05", "wrong tenant, Replay pre-check: operator expects another tenant than the record scope -> registry_evidence_scope_mismatch, verifier NOT called")
@BRIDGED
def test_n05_operator_tenant_differs_from_the_record_scope_replay_precheck(pr):
    cp, proposal = bridge(pr)
    refused(cp, proposal, make_trust(expected_context=H.context(tenant="tenant-beta")), "registry_evidence_scope_mismatch", reached_verifier=False)


@pytest.mark.row("N05", "wrong tenant, Registry layer: a genuinely signed selection for ANOTHER tenant substituted into the evidence -> selection_scope_mismatch at the scope layer")
@BRIDGED
def test_n05_genuine_selection_for_another_tenant_is_selection_scope_mismatch(pr):
    cp, proposal = bridge(pr)
    other = H.material(stmt_over={"scope": {**H.STMT_SCOPE, "tenant": "tenant-beta"}}, host_trust=trust(issuers=(H.v.IssuerEntry(H.KEY_ID, "issuer-test-1", "ed25519", H.PK, (H.grant(tenant="tenant-beta"),)),)))
    t = make_trust(snapshot=other.host_trust)
    refused(_swap_selection(cp, other.selection_text), proposal, t, "registry_evidence_unverified:selection_scope_mismatch", reached_verifier=True, layer="scope",
            adapter_code="selection_scope_mismatch")


@pytest.mark.row("N06", "wrong action/operation, Replay pre-check: operator action id / operation id differ from the record scope -> registry_evidence_scope_mismatch, verifier NOT called")
@BRIDGED
@pytest.mark.parametrize("over", [dict(expected_action_id="urn:cognous:action:other-action-v1"), dict(expected_operation_id="other-operation", expected_context=H.context(operation="other-operation"))])
def test_n06_operator_action_or_operation_differs_replay_precheck(pr, over):
    cp, proposal = bridge(pr)
    refused(cp, proposal, make_trust(**over), "registry_evidence_scope_mismatch", reached_verifier=False)


@pytest.mark.row("N06", "wrong operation, Registry layer: a genuinely signed selection for ANOTHER operation substituted -> selection_operation_mismatch at the scope layer")
@BRIDGED
def test_n06_genuine_selection_for_another_operation_is_selection_operation_mismatch(pr):
    cp, proposal = bridge(pr)
    other = H.material(stmt_over={"operation": "other-operation"}, host_trust=trust(issuers=(H.v.IssuerEntry(H.KEY_ID, "issuer-test-1", "ed25519", H.PK, (H.grant(operation="other-operation"),)),)))
    refused(_swap_selection(cp, other.selection_text), proposal, make_trust(snapshot=other.host_trust), "registry_evidence_unverified:selection_operation_mismatch", reached_verifier=True,
            layer="scope", adapter_code="selection_operation_mismatch")


@pytest.mark.row("N06", "adapter-side R9 rule: expected_context.operation != expected_operation_id is refused by Replay trust validation before anything is called")
@BRIDGED
def test_n06_context_operation_must_equal_expected_operation_id(pr):
    cp, proposal = bridge(pr)
    t = make_trust()
    object.__setattr__(t, "expected_operation_id", "different")   # hostile construction bypassing __post_init__; Replay re-validates at import
    refused(cp, proposal, t, "registry_evidence_trust_malformed", reached_verifier=False)


@pytest.mark.row("N07", "wrong scope, Replay pre-check: operator institution / authority_domain / consumer differ from the record scope -> registry_evidence_scope_mismatch, verifier NOT called")
@BRIDGED
@pytest.mark.parametrize("field", ["institution", "authority_domain", "consumer_id"])
def test_n07_operator_scope_differs_replay_precheck(pr, field):
    cp, proposal = bridge(pr)
    refused(cp, proposal, make_trust(expected_context=H.context(**{field: "urn:other:" + field})), "registry_evidence_scope_mismatch", reached_verifier=False)


@pytest.mark.row("N07", "wrong scope, Registry layer: genuinely signed selection for another institution / authority_domain / consumer substituted -> selection_scope_mismatch / selection_consumer_mismatch at the scope layer")
@BRIDGED
@pytest.mark.parametrize("over,grant_over,code", [
    ({"scope": {**H.STMT_SCOPE, "institution": "urn:other:institution"}}, {"institution": "urn:other:institution"}, "selection_scope_mismatch"),
    ({"scope": {**H.STMT_SCOPE, "authority_domain": "other-domain"}}, {"domain": "other-domain"}, "selection_scope_mismatch"),
    ({"consumer_id": "consumer-other"}, {"consumer": "consumer-other"}, "selection_consumer_mismatch"),
])
def test_n07_genuine_selection_for_another_scope_is_refused_at_the_scope_layer(pr, over, grant_over, code):
    cp, proposal = bridge(pr)
    other = H.material(stmt_over=over, host_trust=trust(issuers=(H.v.IssuerEntry(H.KEY_ID, "issuer-test-1", "ed25519", H.PK, (H.grant(**grant_over),)),)))
    refused(_swap_selection(cp, other.selection_text), proposal, make_trust(snapshot=other.host_trust), "registry_evidence_unverified:" + code, reached_verifier=True, layer="scope",
            adapter_code=code)


# =============================================================================================================== N08 substitution
def _swap(cp, **texts):
    cp = copy.deepcopy(cp)
    cp["decisions"][0]["selection_evidence"].update(texts)
    return cp


@pytest.mark.row("N08", "substituted record: another GENUINE sealed record with the same id/version but other payload, selection unchanged -> record_digest_mismatch at record_binding")
@BRIDGED
def test_n08_other_genuine_sealed_record_with_same_ids_is_record_digest_mismatch(pr):
    cp, proposal = bridge(pr)
    other = H.record(30, 30)
    assert other["record_id"] == pr.material.rec["record_id"] and other["record_digest"] != pr.material.rec["record_digest"]
    refused(_swap(cp, record_text=H.r.dumps(other)), proposal, make_trust(), "registry_evidence_unverified:record_digest_mismatch", reached_verifier=True, layer="record_binding",
            adapter_code="record_digest_mismatch")


@pytest.mark.row("N08", "edited record text: payload edited without resealing -> digest_mismatch at record_binding")
@BRIDGED
def test_n08_edited_record_text_is_digest_mismatch(pr):
    cp, proposal = bridge(pr)
    tampered = copy.deepcopy(pr.material.rec)
    tampered["payload"]["status_max_age_seconds"] = 9000
    refused(_swap(cp, record_text=H.r.dumps(tampered)), proposal, make_trust(), "registry_evidence_unverified:digest_mismatch", reached_verifier=True, layer="record_binding",
            adapter_code="digest_mismatch")


@pytest.mark.row("N08", "substituted selection+record: a genuine pair with a TIGHTER signed bound changes the effective policy -> registry_evidence_effective_digest_mismatch (Replay gate over operator host ages)")
@BRIDGED
def test_n08_genuine_pair_with_a_different_effective_policy_is_detected_by_the_effective_digest(pr):
    cp, proposal = bridge(pr)
    other = H.material(30, 30)
    refused(_swap(cp, record_text=other.record_text, selection_text=other.selection_text), proposal, make_trust(), "registry_evidence_effective_digest_mismatch", reached_verifier=True)


@pytest.mark.row("N08", "STATED NON-DETECTION: substitution by another genuine selection that yields the SAME effective values is admitted (marker lists substitution_by_other_genuine_selection as not verified)")
@BRIDGED
def test_n08_limit_genuine_pair_with_the_same_effective_values_is_not_detected(pr):
    cp, proposal = bridge(pr)
    other = H.material(90, 100)   # bound looser than the host 60 => effective (60,60) as in the real decision
    assert other.selection_text != pr.material.selection_text and other.record_text != pr.material.record_text
    bundle, _ = admitted(_swap(cp, record_text=other.record_text, selection_text=other.selection_text), proposal)
    assert "substitution_by_other_genuine_selection" in bundle.metadata["registry_not_verified"]
    orig, _ = admitted(cp, proposal)
    assert bundle.metadata["registry_evidence"][0]["admission_binding_digest"] != orig.metadata["registry_evidence"][0]["admission_binding_digest"]   # visible to a party holding the earlier digest


# =============================================================================================================== N09 altered effective digest
@pytest.mark.row("N09", "altered effective policy digest in the CP record (configuration resealed with Replay's own function so the structural check passes) -> registry_evidence_effective_digest_mismatch")
@BRIDGED
def test_n09_altered_f4_ages_row_digest_is_effective_digest_mismatch(pr):
    cp, proposal = bridge(pr)
    bad = reseal(cp, lambda m: [x.update(effective_policy_digest="sha256:" + "ab" * 32) for x in m["families"] if x["slot"] == "f4_ages"])
    refused(bad, proposal, make_trust(), "registry_evidence_effective_digest_mismatch", reached_verifier=True)


@pytest.mark.row("N09", "altered f4_scalars (resealed) -> the recorded row digest no longer matches the verifier's: effective_digest_mismatch or effective_values_mismatch, never admitted")
@BRIDGED
def test_n09_altered_f4_scalars_are_refused(pr):
    cp, proposal = bridge(pr)
    bad = reseal(cp, lambda m: m["f4_scalars"].update(status_max_age_seconds=7))
    refused(bad, proposal, make_trust(), "registry_evidence_effective_values_mismatch", reached_verifier=True)


@pytest.mark.row("N09", "altered digest WITHOUT resealing: refused by Replay's structural effective_configuration check before any verifier call")
@BRIDGED
def test_n09_altered_digest_without_reseal_is_a_structural_refusal(pr):
    cp, proposal = bridge(pr)
    bad = copy.deepcopy(cp)
    row(bad)["effective_policy_digest"] = "sha256:" + "cd" * 32
    t = make_trust()
    e = refused(bad, proposal, t, e_code(bad, proposal, t), reached_verifier=False)
    assert e.code in ("schema_violation", "undeclared_member")


def e_code(cp, proposal, t):
    try:
        do_import(cp, proposal, t)
    except H.ImportContractError as exc:
        return exc.code
    raise AssertionError("not refused")


# =============================================================================================================== N10 / N11 missing / malformed
@pytest.mark.row("N10", "missing evidence: the REAL CP decision with carriage OFF (flag default) -> selection_evidence_missing; no fallback to structural-only")
@BRIDGED
def test_n10_real_decision_without_carriage_is_selection_evidence_missing(tmp_path):
    pr0 = produce(tmp_path, material(), carry=False)
    cp, proposal = bridge(pr0, evidence=False)
    t = make_trust()
    refused(cp, proposal, t, "selection_evidence_missing", reached_verifier=False)
    structural = do_import(cp, proposal, selector=H.OLD_SELECTOR).metadata   # control: the same record IS importable structurally (so the refusal is the profile's, not the record's)
    assert structural["effective_configuration_verification"] == "internal_consistency_only_registry_source_revision_unverified" and not [k for k in structural if k.startswith("registry_")]


@pytest.mark.row("N10", "missing evidence: member present on a non-authorized decision / absent on the authorized one / null / empty")
@BRIDGED
@pytest.mark.parametrize("variant", ["null", "empty_dict", "empty_list"])
def test_n10_null_or_empty_evidence_is_refused(pr, variant):
    cp, proposal = bridge(pr)
    cp["decisions"][0]["selection_evidence"] = {"null": None, "empty_dict": {}, "empty_list": []}[variant]
    refused(cp, proposal, make_trust(), "selection_evidence_malformed", reached_verifier=False)


@pytest.mark.row("N11", "malformed evidence: closed key set, version, types, size, unencodable text -> selection_evidence_malformed (Replay shape gate), verifier NOT called")
@BRIDGED
@pytest.mark.parametrize("name,edit", [
    ("extra_key_verdict", lambda e: e.update(verdict={"ok": True})), ("extra_key_authenticated", lambda e: e.update(authenticated=True)),
    ("missing_key", lambda e: e.pop("record_text")), ("version", lambda e: e.update(version="selection-evidence/9.9")),
    ("text_int", lambda e: e.update(record_text=7)), ("empty_text", lambda e: e.update(selection_text="")),
    ("oversize", lambda e: e.update(selection_text="x" * 65537)),
    ("naive_verified_at", lambda e: e.update(verified_at="2026-10-05T19:00:00")), ("non_utc_verified_at", lambda e: e.update(verified_at="2026-10-05T19:00:00+02:00")),
    ("operation_empty", lambda e: e.update(operation_id="")),
])
def test_n11_malformed_evidence_is_refused(pr, name, edit):
    cp, proposal = bridge(pr)
    edit(cp["decisions"][0]["selection_evidence"])
    refused(cp, proposal, make_trust(), "selection_evidence_malformed", reached_verifier=False)


@pytest.mark.row("N11", "foreign-typed text (bytes) / non-exact types in the record: refused by Replay's exact-type snapshot with schema_violation BEFORE any verifier call (review fix M-1)")
@BRIDGED
def test_n11_bytes_text_is_refused_by_the_exact_type_snapshot_before_the_verifier(pr):
    cp, proposal = bridge(pr)
    cp["decisions"][0]["selection_evidence"]["selection_text"] = b"bytes"
    refused(cp, proposal, make_trust(), "schema_violation", reached_verifier=False)


@pytest.mark.row("N11", "unencodable text (lone surrogate): refused fail-closed with a typed code BEFORE the verifier; the code is Replay's generic input-bound schema_violation, NOT the frozen contract's selection_evidence_malformed (observation F-2)")
@BRIDGED
def test_n11_lone_surrogate_text_is_refused_typed_before_the_verifier_but_with_schema_violation(pr):
    cp, proposal = bridge(pr)
    cp["decisions"][0]["selection_evidence"]["record_text"] = "\ud800"
    refused(cp, proposal, make_trust(), "schema_violation", reached_verifier=False)


@pytest.mark.row("N11", "malformed at the Registry layer: well-shaped but non-selection text (garbage / wrong contract envelope) -> the real adapter's typed refusal, never admitted")
@BRIDGED
def test_n11_well_shaped_but_unparseable_selection_text_is_refused_by_the_registry_adapter(pr):
    cp, proposal = bridge(pr)
    t = make_trust()
    with pytest.raises(H.ImportContractError) as exc:
        do_import(_swap(cp, selection_text="not json at all"), proposal, t)
    assert exc.value.code.startswith("registry_evidence_unverified:") and t.verifier.last["ok"] is False and t.verifier.last["authenticated"] is False


# =============================================================================================================== N12 / N13 / N14 / N15
@pytest.mark.row("N12", "revoked key in the operator-supplied snapshot (the CP host's older snapshot did not know) -> issuer_key_revoked; revoked selection epoch -> selection_revoked")
@BRIDGED
def test_n12_revoked_key_and_revoked_selection_in_the_supplied_snapshot(pr):
    cp, proposal = bridge(pr)
    t = make_trust(snapshot=trust(revoked_key_ids=frozenset({H.KEY_ID})))
    refused(cp, proposal, t, "registry_evidence_unverified:issuer_key_revoked", reached_verifier=True, adapter_code="issuer_key_revoked")
    t2 = make_trust(snapshot=trust(revoked_selections=frozenset({("sel-test-1", 1)})))
    refused(cp, proposal, t2, "registry_evidence_unverified:selection_revoked", reached_verifier=True, layer="revocation", adapter_code="selection_revoked")


@pytest.mark.row("N13", "withdrawn selection: a genuinely signed WITHDRAWAL of the selection substituted for the carried selection -> selection_withdrawn (authenticated True, ok False)")
@BRIDGED
def test_n13_genuinely_signed_withdrawal_is_selection_withdrawn(pr):
    cp, proposal = bridge(pr)
    t = make_trust()
    refused(_swap_selection(cp, withdrawal_text(pr.material)), proposal, t, "registry_evidence_unverified:selection_withdrawn", reached_verifier=True, adapter_code="selection_withdrawn")
    assert t.verifier.last["authenticated"] is True


@pytest.mark.row("N13", "withdrawn selection at the CP boundary: the real CP workflow refuses to decide on a withdrawal (no decision, nothing carried)")
@REAL
def test_n13_cp_boundary_refuses_a_withdrawal(tmp_path):
    base = material()
    wd = H.Material(base.record_text, withdrawal_text(base), base.host_trust, base.rec, base.stmt)
    with pytest.raises(PermissionError) as exc:
        produce(tmp_path, wd)
    assert exc.value.refusal.registry_code == "selection_withdrawn"


@pytest.mark.row("N14", "below-minimum epoch: operator snapshot floor min_epochs=(sel-test-1, 2) vs epoch 1 -> selection_epoch_stale at the epoch layer; at the floor -> admitted and epoch_floor_applied True")
@BRIDGED
def test_n14_epoch_below_the_floor_is_selection_epoch_stale_and_at_the_floor_is_admitted(pr):
    cp, proposal = bridge(pr)
    refused(cp, proposal, make_trust(snapshot=trust(min_epochs=(("sel-test-1", 2),))), "registry_evidence_unverified:selection_epoch_stale", reached_verifier=True, layer="epoch",
            adapter_code="selection_epoch_stale")
    bundle, _ = admitted(cp, proposal, make_trust(snapshot=trust(min_epochs=(("sel-test-1", 1),))))
    assert bundle.metadata["registry_evidence"][0]["epoch_floor_applied"] is True


@pytest.mark.row("N14", "snapshot-version floors: min_trust_snapshot_version above the snapshot, last_accepted_snapshot of a newer/same-version-other-fingerprint snapshot -> trust_snapshot_version_stale; equal fingerprint admitted")
@BRIDGED
def test_n14_snapshot_version_floors(pr):
    cp, proposal = bridge(pr)
    refused(cp, proposal, make_trust(min_trust_snapshot_version=2), "registry_evidence_unverified:trust_snapshot_version_stale", reached_verifier=True, layer="trust_snapshot",
            adapter_code="trust_snapshot_version_stale")
    fp = H.pid.trust_snapshot_fingerprint_from_verified(trust())
    refused(cp, proposal, make_trust(last_accepted_snapshot=(1, "sha256:" + "0" * 64)), "registry_evidence_unverified:trust_snapshot_version_stale", reached_verifier=True)
    bundle, _ = admitted(cp, proposal, make_trust(last_accepted_snapshot=(1, fp)))
    assert bundle.metadata["registry_floors_applied"] == {"min_trust_snapshot_version": True, "last_accepted_snapshot": True}


@pytest.mark.row("N15", "expired snapshot at an explicit verification time (as_of): T == snapshot valid_until -> trust_snapshot_expired at trust_snapshot; selection window enforced at T")
@BRIDGED
def test_n15_expired_snapshot_and_selection_window_at_the_explicit_time(pr):
    from datetime import datetime, timezone
    cp, proposal = bridge(pr)
    utc = timezone.utc
    refused(cp, proposal, make_trust(verification_time=datetime(2026, 10, 7, 0, 0, 0, tzinfo=utc)), "registry_evidence_unverified:trust_snapshot_expired", reached_verifier=True,
            layer="trust_snapshot", adapter_code="trust_snapshot_expired")
    refused(cp, proposal, make_trust(verification_time=datetime(2026, 9, 30, 23, 59, 59, tzinfo=utc)), "registry_evidence_unverified:selection_not_yet_effective", reached_verifier=True, layer="time")
    refused(cp, proposal, make_trust(verification_time=datetime(2026, 10, 6, 0, 0, 0, tzinfo=utc), snapshot=trust(valid_until="2026-10-10T00:00:00Z")),
            "registry_evidence_unverified:selection_expired", reached_verifier=True, layer="time")
    bundle, _ = admitted(cp, proposal, make_trust(verification_time=datetime(2026, 10, 1, 0, 0, 0, tzinfo=utc)))   # valid_from inclusive
    assert bundle.metadata["registry_verified_as_of"] == "2026-10-01T00:00:00Z"


@pytest.mark.row("N15", "time inputs: naive datetime / wrong type -> registry_evidence_trust_malformed; time_mode now with a time far from the real clock -> registry_evidence_time_inconsistent (verifier never called)")
@BRIDGED
def test_n15_time_input_validation(pr):
    from datetime import datetime
    cp, proposal = bridge(pr)
    for bad in (datetime(2026, 10, 5, 19, 0, 0), "2026-10-05T19:00:00Z", 1760000000):
        refused(cp, proposal, make_trust_raw(verification_time=bad), "registry_evidence_trust_malformed", reached_verifier=False)
        with pytest.raises(H.ImportContractError) as exc:   # and already at construction
            make_trust(verification_time=bad)
        assert exc.value.code == "registry_evidence_trust_malformed"
    with pytest.raises(H.ImportContractError) as exc:       # T = 2026-10-05, real clock = today: refused at construction ...
        make_trust(time_mode="now")
    assert exc.value.code == "registry_evidence_time_inconsistent"
    refused(cp, proposal, make_trust_raw(time_mode="now"), "registry_evidence_time_inconsistent", reached_verifier=False)   # ... and again at import


def make_trust_raw(**over):
    t = make_trust()
    for k, val in over.items():
        object.__setattr__(t, k, val)
    return t
