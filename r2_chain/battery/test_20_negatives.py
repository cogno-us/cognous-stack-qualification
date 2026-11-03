"""R2 NEGATIVE joined-chain rows A..S (evidence kind REAL; BUILDER_TESTED developer test code, NOT independent qualification). Worker B.

PRIVATE PREVIEW QUALIFICATION TUPLE (preview-only, NOT canonical). Synthetic, single synthetic tenant, claim A only; claim B never asserted.

Chain per row: genuine record produced by the REAL Control Plane F4 workflow (carry_selection_evidence=True), persisted and retrieved through BoundedRecordStore, then the
REAL Replay `import_bounded_workflow` under the explicit F4 profile with independent operator trust inputs and the REAL RegistryEvidenceVerifierV2 (observed by a pure Spy).
Each test first runs the CONTROL POSITIVE (the genuine record is admitted), then the negative sub-cases; every refusal asserts the exact typed code, the verifier call count and
(where the adapter was reached) the refusing layer, and that no bundle came back. Edited records are explicit TAMPERED/SWAPPED deep copies; the genuine record is asserted untouched.

Row ids are the sprint letters A..S (run_chain.py requires every row of that id to be REFUSED_AS_EXPECTED). Where the current contracts do NOT refuse something, the observed behavior
is asserted and recorded as a separate DOCUMENTED-LIMIT row (id "<letter>-limit", label NOT_APPLICABLE via skip) - never folded into the letter row.
"""
import base64
import copy
import dataclasses
import json
from datetime import datetime, timezone

import pytest

import harness as H
import real_cp_record as R
from negatives_support import ALL_PASS, UNV, Cases, control, trust_with

UTC = timezone.utc
F4S = H.SELECTOR_F4


@pytest.fixture
def rr(tmp_path):
    return R.produce_real(tmp_path / "cp")


def _pop(d, k):
    d.pop(k)          # returns None on purpose: the tamper helpers replace the target with a non-None return value


def _limit(reason):
    pytest.skip("NOT_APPLICABLE (documented limit, behavior asserted above): " + reason)


# ======================================================================================================================================================== A
@pytest.mark.row("A", "forged Registry selection signature -> signature_invalid at layer authenticity (flipped byte; re-signed by another key under the trusted key id; whole record produced under a wrong key)")
def test_a_forged_selection_signature(rr):
    control(rr)
    c = Cases(rr)

    def flip(t):
        env = json.loads(t)
        raw = bytearray(base64.b64decode(env["signatures"][0]["signature"]))
        raw[0] ^= 1
        env["signatures"][0]["signature"] = base64.b64encode(bytes(raw)).decode()
        return json.dumps(env, sort_keys=True)

    lay = {"authenticity": "refuse", "record_binding": "pass", "scope": "not_evaluated"}
    c.refuse("one signature byte flipped (TAMPERED copy)", H.tampered_copy_selection_text(rr, flip), UNV + "signature_invalid", calls=1, layers={"authenticity": "refuse"})
    c.refuse("re-signed by another key under the trusted key id (TAMPERED copy)", H.tampered_copy_selection_text(rr, lambda _t: H.envelope_text(rr.material.stmt, sk=H.OTHER_SK)),
             UNV + "signature_invalid", calls=1, layers={"authenticity": "refuse"})
    forged = R.variant_forged_signature()
    H.check("forged record is a different selection than the genuine one", forged.evidence["selection_text"] != rr.evidence["selection_text"])
    H.import_f4(rr.record, forged.operator, proposal=forged.proposal, verifier=H.Spy())      # same operator inputs admit the genuine record
    c.refuse("record produced end to end under a WRONG signing key; operator snapshot admits only the genuine key", forged.record, UNV + "signature_invalid", operator=forged.operator,
             calls=1, layers={"authenticity": "refuse", "record_binding": "pass"})
    H.note("proves", "a signature not made by a key the OPERATOR's snapshot admits is refused by the real Registry verifier at the authenticity layer; admission never comes from the record")
    c.done()


# ======================================================================================================================================================== B
@pytest.mark.row("B", "wrong tenant / context mismatch -> registry_evidence_scope_mismatch (operator context differs; verifier never reached) and issuer_not_authorized (genuine evidence of another tenant swapped in)")
def test_b_wrong_tenant_or_context(rr):
    control(rr)
    c = Cases(rr)
    for kind in ("tenant", "institution", "domain", "consumer"):
        bad = R.variant_wrong_context(kind)
        H.check("only the OPERATOR context differs (%s)" % kind, bad.operator != rr.operator and bad.decision["binding"]["tenant_id"] == rr.decision["binding"]["tenant_id"])
        c.refuse("operator expects another %s" % kind, bad.record, "registry_evidence_scope_mismatch", operator=bad.operator, calls=0)
    other = R.variant_wrong_tenant_record()
    H.check("genuine record of another tenant exists", other.decision["binding"]["tenant_id"] != rr.decision["binding"]["tenant_id"])
    c.refuse("genuine record produced for ANOTHER tenant vs default operator context", other.record, "registry_evidence_scope_mismatch", operator=other.operator, proposal=other.proposal, calls=0)
    c.refuse("other tenant's genuine evidence swapped into this record (SWAPPED copy)", H.swap_evidence(rr.record, other.evidence), UNV + "issuer_not_authorized", calls=1,
             layers={"authority": "refuse", "scope": "refuse"})
    H.note("proves", "tenant/institution/domain/consumer are bound twice: Replay's own pre-check of the operator context against the record scope, and the Registry authority/scope layers")
    c.done()


# ======================================================================================================================================================== C
@pytest.mark.row("C", "wrong operation id -> registry_evidence_scope_mismatch (operator operation differs) and selection_operation_mismatch / issuer_not_authorized at the Registry layers (selection for another operation)")
def test_c_wrong_operation_id(rr):
    control(rr)
    c = Cases(rr)
    bad = R.variant_wrong_context("operation")
    c.refuse("operator expects another operation id (context.operation and expected_operation_id)", bad.record, "registry_evidence_scope_mismatch", operator=bad.operator, calls=0)
    # a genuinely signed selection for ANOTHER operation, with an operator snapshot that grants that operation, swapped into the carried evidence
    snap = H.trust(issuers=(H.v.IssuerEntry(H.KEY_ID, "issuer-test-1", "ed25519", H.PK, (H.grant(operation="other-operation"),)),))
    other = H.material(stmt_over={"operation": "other-operation"}, host_trust=snap)
    op = rr.operator.with_(trust_snapshot=snap, snapshot_ref=(snap.snapshot_id, snap.version))
    c.refuse("selection signed for another operation, snapshot granting only that operation (TAMPERED copy)", H.tampered_copy_selection_text(rr, lambda _t: other.selection_text),
             UNV + "selection_operation_mismatch", operator=op, calls=1, layers={"scope": "refuse"})
    # the genuine selection, but the operator snapshot grants only another operation
    snap2 = H.trust(issuers=(H.v.IssuerEntry(H.KEY_ID, "issuer-test-1", "ed25519", H.PK, (H.grant(operation="other-operation"),)),))
    c.refuse("operator snapshot grants the issuer only another operation", rr.record, UNV + "issuer_not_authorized",
             operator=rr.operator.with_(trust_snapshot=snap2, snapshot_ref=(snap2.snapshot_id, snap2.version)), calls=1, layers={"authority": "refuse"})
    H.note("proves", "the operation id is operator-supplied and checked against the carried evidence, the signed statement and the issuer grant")
    c.done()


# ======================================================================================================================================================== D
@pytest.mark.row("D", "wrong action id -> registry_evidence_scope_mismatch (the operator's expected action id differs from the decision's bound action; verifier never reached)")
def test_d_wrong_action_id(rr):
    control(rr)
    c = Cases(rr)
    bad = R.variant_wrong_context("action")
    H.check("operator action id differs, record unchanged", bad.operator.expected_action_id != rr.operator.expected_action_id and bad.decision["binding"] == rr.decision["binding"])
    c.refuse("operator expects another action id", bad.record, "registry_evidence_scope_mismatch", operator=bad.operator, calls=0)
    c.refuse("record decision/binding action id edited (TAMPERED copy)", H.tamper_decision(rr, lambda d: d["binding"].update(action_id=d["binding"]["action_id"] + "-x")), "schema_violation", calls=0)
    H.note("proves", "the action id is not read from the record as trust: it is the operator's independent expectation and must equal the decision's bound action and effective-configuration scope")
    c.done()


# ======================================================================================================================================================== E
@pytest.mark.row("E", "stale selection / expired time window -> selection_expired, selection_not_yet_effective, trust_snapshot_expired at layer time/trust_snapshot (operator verification time)")
def test_e_stale_or_expired_selection(rr):
    control(rr)
    c = Cases(rr)
    long_snap = H.trust(valid_until="2026-10-10T00:00:00Z")
    c.refuse("verification time == valid_until of the signed window (snapshot still valid)", rr.record, UNV + "selection_expired",
             operator=rr.operator.with_(verification_time=datetime(2026, 10, 6, 0, 0, 0, tzinfo=UTC), trust_snapshot=long_snap), calls=1, layers={"time": "refuse"})
    c.refuse("verification time one second before valid_from", rr.record, UNV + "selection_not_yet_effective",
             operator=rr.operator.with_(verification_time=datetime(2026, 9, 30, 23, 59, 59, tzinfo=UTC)), calls=1, layers={"time": "refuse"})
    c.refuse("trust snapshot expired at the verification time", rr.record, UNV + "trust_snapshot_expired",
             operator=rr.operator.with_(verification_time=datetime(2026, 10, 7, 0, 0, 0, tzinfo=UTC)), calls=1, layers={"trust_snapshot": "refuse"})
    # boundary control: valid_from is inclusive
    spy = H.Spy()
    b, _ = H.import_f4(rr.record, rr.operator.with_(verification_time=datetime(2026, 10, 1, 0, 0, 0, tzinfo=UTC)), proposal=rr.proposal, verifier=spy)
    H.check("boundary control: at valid_from (inclusive) the same record is admitted", b.metadata["registry_verified_as_of"] == "2026-10-01T00:00:00Z" and spy.calls == 1)
    H.note("proves", "admission is decided at the OPERATOR's explicit as_of time against the signed window and snapshot validity, not at the decision time carried in the record")
    c.done()


# ======================================================================================================================================================== F
@pytest.mark.row("F", "revoked selection -> issuer_key_revoked / selection_revoked (operator snapshot) and selection_withdrawn (signed withdrawal); the Control Plane boundary also refuses a withdrawal")
def test_f_revoked_selection(rr, tmp_path):
    control(rr)
    c = Cases(rr)
    c.refuse("signing key revoked in the operator snapshot", rr.record, UNV + "issuer_key_revoked",
             operator=rr.operator.with_(trust_snapshot=H.trust(revoked_key_ids=frozenset({H.KEY_ID}))), calls=1, layers={"authenticity": "refuse"})
    c.refuse("selection (id, epoch) revoked in the operator snapshot", rr.record, UNV + "selection_revoked",
             operator=rr.operator.with_(trust_snapshot=H.trust(revoked_selections=frozenset({("sel-test-1", 1)}))), calls=1, layers={"revocation": "refuse"})
    wd = H.withdrawal_text(rr.material)
    res = c.refuse("genuinely signed WITHDRAWAL substituted for the carried selection (TAMPERED copy)", H.tampered_copy_selection_text(rr, lambda _t: wd), UNV + "selection_withdrawn",
                   calls=1, layers={"disposition": "refuse"})
    H.check("withdrawal verdict was authenticated (signature good) but not ok", res.spy.last["authenticated"] is True and res.spy.last["ok"] is False)
    base = rr.material
    wmat = H.Material(base.record_text, wd, base.host_trust, base.rec, base.stmt)
    with H.expect_refusal("RegistrySelectionRefused", Exception) as box:
        R.produce_real(tmp_path / "wd", mat=wmat)
    H.check("Control Plane boundary refuses at construction with the withdrawal code (no decision, nothing carried)", "selection_withdrawn" in str(box.exception) and "construction" in str(box.exception))
    H.note("proves", "revocation and withdrawal are enforced from the operator's snapshot / the signed withdrawal at admission time, independent of what the Control Plane host knew at decision time")
    c.done()


# ======================================================================================================================================================== G
@pytest.mark.row("G", "epoch / floor regression -> selection_epoch_stale (epoch layer), trust_snapshot_version_stale (min version and last-accepted-snapshot floors); floors at the boundary admit")
def test_g_epoch_and_snapshot_floor_regression(rr):
    control(rr)
    c = Cases(rr)
    c.refuse("operator epoch floor (sel-test-1, 2) above the carried epoch 1", rr.record, UNV + "selection_epoch_stale",
             operator=rr.operator.with_(trust_snapshot=H.trust(min_epochs=(("sel-test-1", 2),))), calls=1, layers={"epoch": "refuse"})
    c.refuse("min_trust_snapshot_version 2 above the snapshot version 1", rr.record, UNV + "trust_snapshot_version_stale",
             operator=rr.operator.with_(min_trust_snapshot_version=2), calls=1, layers={"trust_snapshot": "refuse"})
    c.refuse("last accepted snapshot (1, other fingerprint): same version, different content", rr.record, UNV + "trust_snapshot_version_stale",
             operator=rr.operator.with_(last_accepted_snapshot=(1, "sha256:" + "0" * 64)), calls=1, layers={"trust_snapshot": "refuse"})
    c.refuse("last accepted snapshot is a NEWER version (2)", rr.record, UNV + "trust_snapshot_version_stale",
             operator=rr.operator.with_(last_accepted_snapshot=(2, "sha256:" + "0" * 64)), calls=1, layers={"trust_snapshot": "refuse"})
    spy = H.Spy()
    b, _ = H.import_f4(rr.record, rr.operator.with_(trust_snapshot=H.trust(min_epochs=(("sel-test-1", 1),))), proposal=rr.proposal, verifier=spy)
    H.check("boundary control: epoch floor equal to the carried epoch admits and the epoch floor is reported applied", b.metadata["registry_evidence"][0]["epoch_floor_applied"] is True)
    fp = H.pid.trust_snapshot_fingerprint_from_verified(H.trust())
    b2, _ = H.import_f4(rr.record, rr.operator.with_(last_accepted_snapshot=(1, fp)), proposal=rr.proposal, verifier=H.Spy())
    H.check("boundary control: last_accepted_snapshot with the equal fingerprint admits", b2.metadata["registry_floors_applied"] == {"min_trust_snapshot_version": True, "last_accepted_snapshot": True})
    H.note("proves", "the F4 path reaches the Registry epoch layer and both trust-snapshot floors through the operator snapshot; the layer is APPLICABLE (not NOT_APPLICABLE)")
    c.done()


# ======================================================================================================================================================== H
@pytest.mark.row("H", "wrong effective policy digest -> registry_evidence_effective_digest_mismatch / effective_values_mismatch (record resealed with Replay's own digest function), schema_violation when not resealed")
def test_h_wrong_effective_policy_digest(rr):
    control(rr)
    c = Cases(rr)
    bad_digest = H.reseal(rr.record, lambda m: [x.update(effective_policy_digest="sha256:" + "ab" * 32) for x in m["families"] if x["slot"] == "f4_ages"])
    H.check("RESEALED copy differs only in the f4_ages digest", H.jdump(bad_digest) != H.jdump(rr.record))
    c.refuse("f4_ages family row digest altered, effective_configuration resealed (TAMPERED copy)", bad_digest, "registry_evidence_effective_digest_mismatch", calls=1)
    c.refuse("f4_scalars altered, resealed (TAMPERED copy)", H.reseal(rr.record, lambda m: m["f4_scalars"].update(status_max_age_seconds=7)), "registry_evidence_effective_values_mismatch", calls=1)
    nr = copy.deepcopy(rr.record)
    H.row(nr)["effective_policy_digest"] = "sha256:" + "cd" * 32
    c.refuse("digest altered WITHOUT resealing: Replay's structural effective_configuration check refuses before any verifier call", nr, "schema_violation", calls=0)
    H.note("proves", "the effective policy digest of the f4_ages row is recomputed by the Registry verifier from operator host ages and the signed bound and compared by Replay; resealing cannot launder an edit")
    c.done()


# ======================================================================================================================================================== I
@pytest.mark.row("I", "wrong host age values -> registry_evidence_effective_digest_mismatch (operator's independent host ages differ from those the decision used)")
@pytest.mark.parametrize("ages", [(30, 30), (600, 600), (60, 30)])
def test_i_wrong_host_age_values(rr, ages):
    control(rr)
    c = Cases(rr)
    host = {"status_max_age_seconds": ages[0], "approval_max_age_seconds": ages[1]}
    bad = R.variant_mutated_effective_policy(host_ages=host)
    H.check("the operator's independently computed expected digest differs from the record's f4_ages row",
            bad.operator.expected_effective_policy_digest != H.row(rr.record)["effective_policy_digest"])
    c.refuse("operator host ages %s (record used 60/60)" % (ages,), bad.record, "registry_evidence_effective_digest_mismatch", operator=bad.operator, calls=1, layers={"disposition": "pass", "record_binding": "pass"})
    H.note("proves", "host ages are an operator expectation, not read from the record: a mismatch is a refusal even though the verifier accepted the signature")
    c.done()


# ======================================================================================================================================================== J
@pytest.mark.row("J", "record substitution after the Control Plane decision -> record_digest_mismatch / effective_digest_mismatch / issuer_not_authorized (different genuine record or evidence swapped into the retained record)")
def test_j_record_substitution_after_decision(rr):
    control(rr)
    c = Cases(rr)
    other = R.produce_real(mat=H.material(40, 30))
    H.check("donor is a different GENUINE retained record", other.evidence["record_text"] != rr.evidence["record_text"] and other.decision_id != rr.decision_id)
    c.refuse("different genuine Registry record text swapped into the carried evidence", H.tampered_copy_record_text(rr, lambda _t: other.evidence["record_text"]), UNV + "record_digest_mismatch",
             calls=1, layers={"record_binding": "refuse", "authenticity": "pass", "scope": "pass"})
    c.refuse("whole selection_evidence of a genuine run with a different signed bound (SWAPPED copy)", H.swap_evidence(rr.record, other.evidence), "registry_evidence_effective_digest_mismatch", calls=1)
    c.refuse("whole selection_evidence of a genuine run for ANOTHER tenant (SWAPPED copy)", H.swap_evidence(rr.record, R.variant_wrong_tenant_record().evidence), UNV + "issuer_not_authorized",
             calls=1, layers={"authority": "refuse"})
    def edit(t):
        d = json.loads(t)
        d["payload"]["status_max_age_seconds"] = 9000
        return json.dumps(d, sort_keys=True)
    c.refuse("record payload edited without resealing (TAMPERED copy)", H.tampered_copy_record_text(rr, edit), UNV + "digest_mismatch", calls=1, layers={"record_binding": "refuse"})
    c.refuse("decision re-sealed attempt: f4_scalars forged to the donor's values and the configuration resealed, evidence unchanged", H.reseal(rr.record, lambda m: m["f4_scalars"].update(status_max_age_seconds=40, approval_max_age_seconds=30)),
             "registry_evidence_effective_values_mismatch", calls=1)
    H.note("proves", "post-decision substitution of the evidence or the sealed configuration is detected when it changes the signed record, the scope or the effective values")
    c.done()


@pytest.mark.row("J-limit", "DOCUMENTED LIMIT (not a letter row): substitution by identical or effective-value-equivalent genuine evidence is admitted (N08 / F1-D(ii) non-detection)", kind="negative")
def test_j_limit_equivalent_genuine_evidence_is_not_detected(rr):
    bundle0 = control(rr)
    same = R.produce_real()
    H.check("a second genuine run carries byte-identical evidence (the signature binds no run/decision id)", same.evidence == rr.evidence and same.decision_id != rr.decision_id)
    b1, _ = H.import_f4(H.swap_evidence(rr.record, same.evidence), rr.operator, proposal=rr.proposal, verifier=H.Spy())
    H.check("identical-evidence swap is ADMITTED (observed behavior, not a refusal)", b1.metadata["registry_authentication_claim"] == "A_selection_signature_per_injected_verifier")
    equiv = R.produce_real(mat=H.material(90, 100))        # looser signed bound -> same effective values 60/60
    H.check("equivalent donor has other signed texts", equiv.evidence["selection_text"] != rr.evidence["selection_text"] and equiv.evidence["record_text"] != rr.evidence["record_text"])
    b2, _ = H.import_f4(H.swap_evidence(rr.record, equiv.evidence), rr.operator, proposal=rr.proposal, verifier=H.Spy())
    H.check("effective-value-equivalent genuine pair swap is ADMITTED and the marker lists substitution_by_other_genuine_selection as NOT verified",
            "substitution_by_other_genuine_selection" in b2.metadata["registry_not_verified"])
    H.check("the swap is visible only through a changed admission_binding_digest", b2.metadata["registry_evidence"][0]["admission_binding_digest"] != bundle0.metadata["registry_evidence"][0]["admission_binding_digest"])
    H.note("limit", "pinned documented non-detection; Replay protections are scope + operator context + effective-policy digest + record binding, not run identity")
    _limit("Replay does not refuse substitution by identical/equivalent genuine Registry evidence; the marker says so")


# ======================================================================================================================================================== K
@pytest.mark.row("K", "selection-text substitution -> record_digest_mismatch / selection_withdrawn / json_malformed / signature_invalid (a different selection text in the retained evidence)")
def test_k_selection_text_substitution(rr):
    control(rr)
    c = Cases(rr)
    other = R.produce_real(mat=H.material(40, 30))
    c.refuse("other genuine selection (different signed record) in place of the carried one", H.tampered_copy_selection_text(rr, lambda _t: other.evidence["selection_text"]),
             UNV + "record_digest_mismatch", calls=1, layers={"record_binding": "refuse"})
    c.refuse("genuinely signed withdrawal in place of the carried selection", H.tampered_copy_selection_text(rr, lambda _t: H.withdrawal_text(rr.material)), UNV + "selection_withdrawn", calls=1,
             layers={"disposition": "refuse"})
    c.refuse("non-JSON text in place of the carried selection", H.tampered_copy_selection_text(rr, lambda _t: "not json at all"), UNV + "json_malformed", calls=1, layers={"structural": "refuse"})
    c.refuse("same statement re-signed by another key", H.tampered_copy_selection_text(rr, lambda _t: H.envelope_text(rr.material.stmt, sk=H.OTHER_SK)), UNV + "signature_invalid", calls=1,
             layers={"authenticity": "refuse"})
    c.refuse("byte order mark prepended to the carried selection text", H.tampered_copy_selection_text(rr, lambda t: "﻿" + t), UNV + "json_malformed", calls=1)
    H.note("proves", "the exact signed selection bytes are what the verifier sees: any other selection text, even a genuine one, fails against the carried record or the operator trust")
    c.done()


# ======================================================================================================================================================== L
@pytest.mark.row("L", "wrong source revision declaration -> registry_evidence_trust_malformed (non 40-hex revision, verifier never reached); non-current Replay control-plane revision/selector refused (untyped code, message pinned)")
def test_l_malformed_source_revision_declaration(rr):
    control(rr)
    c = Cases(rr)
    # construction of the trust object itself already refuses; the import-time re-validation refuses a trust object built around the constructor
    for field_ in ("control_plane_source_revision", "registry_source_revision"):
        for bad in ("abc", "Z" * 40, "A" * 40, ""):
            with H.expect_refusal("registry_evidence_trust_malformed", H.ImportContractError):
                dataclasses.replace(rr.operator.as_replay_trust(verifier=H.Spy()), **{field_: bad})
            t = rr.operator.as_replay_trust(verifier=H.Spy())
            object.__setattr__(t, field_, bad)        # hostile construction bypassing __post_init__; Replay re-validates at import
            res = H.refuse_import(rr.record, rr.operator, rr.proposal, "registry_evidence_trust_malformed", pass_trust=False, registry_evidence_trust=t)
            H.check("verifier never reached for malformed %s=%r" % (field_, bad), t.verifier.calls == 0)
            c.rows.append(dict(case="%s=%r" % (field_, bad), expected="registry_evidence_trust_malformed", observed=res.code, verifier_calls=t.verifier.calls))
    res = c.refuse("Replay control_plane_revision is the previous generation (not current)", rr.record, None, calls=0, revision=H.I.CONTROL_PLANE_REVISION, message_has="unsupported Control Plane profile selector")
    H.check("observed code is None (Replay's generic typed refusal without a code)", res.code is None)
    c.refuse("Replay control_plane_revision is an unknown 40-hex value", rr.record, None, calls=0, revision="a" * 40, message_has="unsupported Control Plane revision")
    H.note("proves", "the declared revisions must be well-formed 40-hex; the Replay-side control-plane revision must be the current generation. A well-formed but WRONG declared revision is NOT refused: see row L-limit")
    H.check("every refusal's observed code equals expected (None expected for the untyped Replay revision refusals)", all(x["expected"] == x["observed"] for x in c.rows))
    H.note("cases", c.rows)


@pytest.mark.row("L-limit", "DOCUMENTED LIMIT (not a letter row): a well-formed but WRONG declared source revision is admitted; the marker labels it operator_declared_unattested", kind="negative")
def test_l_limit_wrong_but_wellformed_revision_is_admitted_and_marked_unattested(rr):
    control(rr)
    for field_, marker_key in (("control_plane_source_revision", "control_plane"), ("registry_source_revision", "registry")):
        wrong = "a" * 40
        tr, _spy = trust_with(rr, **{field_: wrong})
        b, _ = H.import_f4(rr.record, rr.operator, proposal=rr.proposal, pass_trust=False, registry_evidence_trust=tr)
        decl = b.metadata["registry_declared_source_revisions"]
        H.check("wrong %s admitted; marker echoes the declared value and the attestation label" % field_, decl[marker_key] == wrong and decl["attestation"] == "operator_declared_unattested")
    H.note("limit", "source revisions are operator-declared and unattested by design (marker attestation operator_declared_unattested); Replay validates format only")
    _limit("Replay cannot verify a source revision declaration; it records it as operator_declared_unattested")


# ======================================================================================================================================================== M
@pytest.mark.row("M", "wrong trust snapshot id/version -> registry_evidence_input_echo_mismatch (operator's snapshot reference differs from the snapshot the verifier checked); floors in the snapshot version refuse")
def test_m_wrong_trust_snapshot_reference(rr):
    control(rr)
    c = Cases(rr)
    for name, ref in (("reference id differs", H.RegistryTrustSnapshotRef(snapshot_id="snap-other", version=1)),
                      ("reference version differs", H.RegistryTrustSnapshotRef(snapshot_id="snap-test-1", version=2))):
        tr, spy = trust_with(rr, trust_snapshot_ref=ref)
        res = H.refuse_import(rr.record, rr.operator, rr.proposal, "registry_evidence_input_echo_mismatch", pass_trust=False, registry_evidence_trust=tr)
        H.check("%s: verifier reached once, its verdict was ok but did not echo the declared snapshot" % name, spy.calls == 1 and spy.last["ok"] is True)
        c.rows.append(dict(case=name, expected="registry_evidence_input_echo_mismatch", observed=res.code, verifier_calls=spy.calls))
    c.refuse("operator snapshot version below the operator's own minimum (version floor)", rr.record, UNV + "trust_snapshot_version_stale", operator=rr.operator.with_(min_trust_snapshot_version=2), calls=1,
             layers={"trust_snapshot": "refuse"})
    H.note("proves", "the snapshot id/version Replay records must be the one the verifier actually evaluated")
    c.done()


# ======================================================================================================================================================== N
def _setk(k, v):
    def f(vd, req):
        vd[k] = v
        return vd
    return f


_N_CASES = {
    "verdict is a string": (lambda vd, req: "ok", "not a plain dict"),
    "verdict is a list": (lambda vd, req: [vd], "not a plain dict"),
    "verdict is None": (lambda vd, req: None, "not a plain dict"),
    "ok is a string": (_setk("ok", "yes"), "ok is not a bool"),
    "extra member": (_setk("extra", "x"), "member set"),
    "missing member (epoch)": (lambda vd, req: (vd.pop("epoch"), vd)[1], "member set"),
    "layer value outside the vocabulary": (lambda vd, req: (vd["layers"].update(time="maybe"), vd)[1], "layer value"),
    "layers missing a layer": (lambda vd, req: (vd["layers"].pop("epoch"), vd)[1], "authenticated/layers"),
    "wrong verdict contract": (_setk("contract", "registry-evidence-verdict/9.9"), "contract"),
    "selection_digest not digest-like": (_setk("selection_digest", "nothex"), "digest member"),
    "effective_policy_digest malformed": (_setk("effective_policy_digest", "sha256:zz"), "digest member"),
    "epoch 0": (_setk("epoch", 0), "snapshot version / epoch"),
    "floors_applied malformed": (_setk("floors_applied", {"x": True}), "floors_applied"),
    "effective_values wrong type": (_setk("effective_values", {"status_max_age_seconds": "60", "approval_max_age_seconds": 60}), "effective_values"),
    "ok False with no code": (lambda vd, req: dict(vd, ok=False, code=None), "refusal code"),
    "ok False with malformed code": (lambda vd, req: dict(vd, ok=False, code="Bad Code!"), "refusal code"),
    "verifier_implementation malformed": (_setk("verifier_implementation", {"name": "x"}), "verifier_implementation"),
}


@pytest.mark.row("N", "malformed verifier verdict (real adapter's verdict altered in flight by the Spy mutate hook) -> registry_evidence_verdict_malformed for 17 shapes; ok-but-not-authenticated -> registry_evidence_not_authenticated")
def test_n_malformed_verifier_verdict(rr):
    control(rr)
    c = Cases(rr)
    for name, (fn, why) in _N_CASES.items():
        c.refuse(name, rr.record, "registry_evidence_verdict_malformed", spy=H.Spy(mutate=fn), calls=1, message_has=why)
    for name, fn in (("authenticated False", _setk("authenticated", False)), ("code set on an ok verdict", _setk("code", "selection_expired")),
                     ("one layer not pass", lambda vd, req: (vd["layers"].update(epoch="not_evaluated"), vd)[1])):
        c.refuse("ok verdict but " + name, rr.record, "registry_evidence_not_authenticated", spy=H.Spy(mutate=fn), calls=1)
    H.note("proves", "Replay's closed verdict gate refuses malformed, over/under-specified and not-fully-authenticated verdicts; admission never follows from a verdict's mere shape")
    c.done()


# ======================================================================================================================================================== O
@pytest.mark.row("O", "verifier verdict digest/echo mismatch -> registry_evidence_input_echo_mismatch (selection/record sha, family, time, snapshot, floors) and effective_digest/values_mismatch")
def test_o_verdict_digest_mismatch(rr):
    control(rr)
    c = Cases(rr)
    echo = {
        "selection_text_sha256 differs": _setk("selection_text_sha256", "0" * 64),
        "selection_text_sha256 carries a sha256: prefix": lambda vd, req: dict(vd, selection_text_sha256="sha256:" + vd["selection_text_sha256"]),
        "record_text_sha256 differs": _setk("record_text_sha256", "1" * 64),
        "family differs": _setk("family", "other-family"),
        "verification_time_utc differs": _setk("verification_time_utc", "2026-10-05T19:00:01Z"),
        "trust_snapshot_id differs": _setk("trust_snapshot_id", "snap-x"),
        "trust_snapshot_version differs": _setk("trust_snapshot_version", 9),
        "floors_applied differs": _setk("floors_applied", {"min_trust_snapshot_version": False, "last_accepted_snapshot": False}),
    }
    for name, fn in echo.items():
        c.refuse(name, rr.record, "registry_evidence_input_echo_mismatch", spy=H.Spy(mutate=fn), calls=1)
    c.refuse("effective_policy_digest differs from the f4_ages row", rr.record, "registry_evidence_effective_digest_mismatch", spy=H.Spy(mutate=_setk("effective_policy_digest", "sha256:" + "2" * 64)), calls=1)
    c.refuse("effective_values differ from f4_scalars", rr.record, "registry_evidence_effective_values_mismatch",
             spy=H.Spy(mutate=_setk("effective_values", {"status_max_age_seconds": 59, "approval_max_age_seconds": 60})), calls=1)
    H.note("proves", "Replay re-derives what the verifier must have checked (hashes of the exact texts, family, time, snapshot, floors, effective policy) and refuses any verdict that does not echo it")
    c.done()


@pytest.mark.row("O-limit", "DOCUMENTED LIMIT (not a letter row): a well-formed but altered selection_digest / bound_record_digest in the verdict is not cross-checked by Replay (NF-2: the verifier is trusted as far as the operator injects it)", kind="negative")
def test_o_limit_verdict_selection_and_record_digest_members_are_not_cross_checked(rr):
    b0 = control(rr)
    for key in ("selection_digest", "bound_record_digest"):
        altered = "sha256:" + "4" * 64
        b, _ = H.import_f4(rr.record, rr.operator, proposal=rr.proposal, verifier=H.Spy(mutate=_setk(key, altered)))
        e = b.metadata["registry_evidence"][0]
        H.check("altered %s is ADMITTED and surfaces in the marker; the admission binding digest changes" % key,
                e[key if key == "selection_digest" else "bound_record_digest"] == altered and e["admission_binding_digest"] != b0.metadata["registry_evidence"][0]["admission_binding_digest"])
    H.note("limit", "Replay trusts the injected verifier's digest members (NF-2); only an independent comparison with the earlier admission binding digest reveals it")
    _limit("verdict digest members selection_digest / bound_record_digest are verifier-asserted and not independently recomputed by Replay")


# ======================================================================================================================================================== P
@pytest.mark.row("P", "missing required F4 evidence -> selection_evidence_missing (no carry / member removed) and selection_evidence_malformed (null, empty, member removed); verifier never reached")
def test_p_missing_required_f4_evidence(rr):
    control(rr)
    c = Cases(rr)
    nc = R.variant_no_carry()
    H.check("real Control Plane run WITHOUT carry_selection_evidence is authorized but carries no evidence", nc.decision["result"] == "authorized" and "selection_evidence" not in nc.decision)
    c.refuse("Control Plane run without carry_selection_evidence", nc.record, "selection_evidence_missing", operator=nc.operator, proposal=nc.proposal, calls=0)
    c.refuse("selection_evidence member removed from the genuine record (TAMPERED copy)", H.tamper_decision(rr, lambda d: _pop(d, "selection_evidence")), "selection_evidence_missing", calls=0)
    for k in sorted(rr.evidence):
        c.refuse("evidence member %s removed" % k, H.tamper_evidence(rr, lambda e, k=k: _pop(e, k)), "selection_evidence_malformed", calls=0)
    c.refuse("selection_evidence null", H.tamper_decision(rr, lambda d: d.update(selection_evidence=None)), "selection_evidence_malformed", calls=0)
    c.refuse("selection_evidence empty object", H.tamper_decision(rr, lambda d: d.update(selection_evidence={})), "selection_evidence_malformed", calls=0)
    H.note("proves", "no fallback to a structural-only import: an authorized decision without the complete carried F4 evidence is refused before any verifier call")
    c.done()


# ======================================================================================================================================================== Q
@pytest.mark.row("Q", "attempt to select an unsupported profile -> registry_evidence_unsupported_profile / trust_missing / typed untyped-code refusals; no downgrade to structural-only or caller-trusted modes")
def test_q_unsupported_profile_selection(rr):
    control(rr)
    c = Cases(rr)
    for name, sel in (("legacy governed profile + trust", H.OLD_SELECTOR),):
        c.refuse(name, rr.record, "registry_evidence_unsupported_profile", selector=sel, calls=0)
    for sel in (F4S + " ", F4S.upper(), "registry-authenticated-selection-f4-governed/0.2", "registry-authenticated-selection-f5-governed/0.1", "registry-governed-profile/0.9"):
        c.refuse("unknown selector %r" % sel, rr.record, None, selector=sel, calls=0, message_has="unsupported Control Plane profile selector")
    c.refuse("OLD authenticated selector + trust: the F4 shape is not admitted without the F4 selector", rr.record, None, selector=H.SELECTOR, calls=0, message_has="resolution journal missing")
    c.refuse("F4 selector WITHOUT operator trust", rr.record, "registry_evidence_trust_missing", pass_trust=False, calls=0)
    ec = rr.decision["binding"]["runtime_authority"]["effective_configuration"]
    c.refuse("F4 selector + trust + caller-trusted expected digest (conflicting modes)", rr.record, "registry_evidence_conflicting_modes", calls=0, expected_effective_configuration_digest=ec["digest"])
    H.note("proves", "only the exact F4 selector string with operator trust and the current Control Plane generation admits; every other selector or mode is refused, never downgraded")
    c.done()


# ======================================================================================================================================================== R
@pytest.mark.row("R", "unsupported evidence family -> registry_evidence_family_set_mismatch (carried family/contract, required_families, f4_ages row) and family_unsupported (genuine non-F4 record at the adapter)")
def test_r_unsupported_evidence_family(rr):
    control(rr)
    c = Cases(rr)
    c.refuse("carried family names another family", H.tamper_evidence(rr, lambda e: e.update(family="f5-class-status-age-bounds")), "registry_evidence_family_set_mismatch", calls=0)
    c.refuse("carried family is nonsense", H.tamper_evidence(rr, lambda e: e.update(family="nonsense")), "registry_evidence_family_set_mismatch", calls=0)
    c.refuse("carried registry contract_version unsupported", H.tamper_evidence(rr, lambda e: e.update(contract_version="r08-v9")), "registry_evidence_family_set_mismatch", calls=0)
    c.refuse("evidence wire version unsupported", H.tamper_evidence(rr, lambda e: e.update(version="selection-evidence/9.9")), "selection_evidence_malformed", calls=0)
    c.refuse("f4_ages family row removed from the sealed configuration (RESEALED copy)", H.reseal(rr.record, lambda m: m.update(families=[x for x in m["families"] if x["slot"] != "f4_ages"])),
             "registry_evidence_family_set_mismatch", calls=0)
    for fam in (frozenset({"f5"}), frozenset({"f4", "f5"})):
        with H.expect_refusal("registry_evidence_family_set_mismatch", H.ImportContractError):
            H.make_trust(required_families=fam)
    with H.expect_refusal("registry_evidence_trust_malformed", H.ImportContractError):
        H.make_trust(required_families=frozenset())
    from registry_successor import v2_f1ab as f1ab
    rec = H.r.seal_record(dict(H.r.make_record(), contract_version="r08-v2", family=f1ab.FAMILY_F1AB, record_id="f1ab-record",
                               payload={"allowed_actions": ["a"], "allowed_adapters": ["a"], "allowed_units": ["u"], "allowed_institutions": ["i"], "allowed_authority_domains": ["d"]}))
    oth = H.Material(H.r.dumps(rec), H.envelope_text(H.statement(rec, family=f1ab.FAMILY_F1AB)), H.trust(), rec, {})
    c.refuse("genuine NON-F4 (f1ab) record and selection under the F4 carried family label", H.tamper_evidence(rr, lambda e: e.update(record_text=oth.record_text, selection_text=oth.selection_text)),
             UNV + "family_unsupported", calls=1)
    c.refuse("genuine non-F4 pair with the non-F4 family name carried", H.tamper_evidence(rr, lambda e: e.update(record_text=oth.record_text, selection_text=oth.selection_text, family=f1ab.FAMILY_F1AB)),
             "registry_evidence_family_set_mismatch", calls=0)
    H.note("proves", "the authenticated F4 profile admits exactly the F4 family: Replay's shape gate, the required-family set and the Registry adapter all refuse any other family")
    c.done()


# ======================================================================================================================================================== S
@pytest.mark.row("S", "duplicate / malformed critical evidence -> json_duplicate_key, signature_missing, field_unknown, field_missing (Registry adapter) and selection_evidence_malformed (Replay shape gate)")
def test_s_duplicate_or_malformed_critical_evidence(rr):
    control(rr)
    c = Cases(rr)

    def dupkey(text):
        d = json.loads(text)
        k = next(iter(d))
        return text[:-1] + ', "%s": %s}' % (k, json.dumps(d[k]))

    def with_env(fn):
        def f(t):
            e = json.loads(t)
            fn(e)
            return json.dumps(e, sort_keys=True)
        return f

    c.refuse("duplicate JSON key in the carried selection text", H.tampered_copy_selection_text(rr, dupkey), UNV + "json_duplicate_key", calls=1, layers={"structural": "refuse"})
    c.refuse("duplicate JSON key in the carried record text", H.tampered_copy_record_text(rr, dupkey), UNV + "json_duplicate_key", calls=1)
    c.refuse("signatures array emptied", H.tampered_copy_selection_text(rr, with_env(lambda e: e.update(signatures=[]))), UNV + "signature_missing", calls=1)
    c.refuse("unknown member added to the selection envelope", H.tampered_copy_selection_text(rr, with_env(lambda e: e.update(extra=1))), UNV + "field_unknown", calls=1)
    c.refuse("malformed second signature entry appended", H.tampered_copy_selection_text(rr, with_env(lambda e: e["signatures"].append({"key_id": "nope", "signature": "AA=="}))), UNV + "field_missing", calls=1)
    c.refuse("extra member (a smuggled verdict) added to selection_evidence", H.tamper_evidence(rr, lambda e: e.update(verdict={"ok": True})), "selection_evidence_malformed", calls=0)
    dup = copy.deepcopy(rr.record)
    dup["decisions"].append(copy.deepcopy(dup["decisions"][0]))
    res = c.refuse("authorized decision duplicated in the record (two bindings)", dup, None, calls=2, message_has="multiple authorization bindings")
    H.note("note", "the duplicated-decision refusal is Replay's untyped (code None) single-proposal guard, reached after the verifier ran for both decisions")
    H.note("proves", "duplicate keys, missing/unknown envelope members and extra evidence members in the critical evidence are refused by the current contracts; what is NOT refused is in row S-limit")
    c.done()


@pytest.mark.row("S-limit", "DOCUMENTED LIMIT (not a letter row): a byte-identical DUPLICATE signature entry and trailing whitespace on the carried selection text are admitted by the current contracts", kind="negative")
def test_s_limit_duplicate_identical_signature_and_trailing_whitespace_are_admitted(rr):
    control(rr)
    def dupsig(t):
        e = json.loads(t)
        e["signatures"] = e["signatures"] * 2
        return json.dumps(e, sort_keys=True)
    spy = H.Spy()
    b1, _ = H.import_f4(H.tampered_copy_selection_text(rr, dupsig), rr.operator, proposal=rr.proposal, verifier=spy)
    H.check("identical signature entry duplicated: ADMITTED (observed; the signature covers the statement, the envelope may repeat it)", spy.calls == 1 and spy.last["ok"] is True)
    spy2 = H.Spy()
    b2, _ = H.import_f4(H.tampered_copy_selection_text(rr, lambda t: t + "\n"), rr.operator, proposal=rr.proposal, verifier=spy2)
    H.check("trailing newline on the selection text: ADMITTED (observed; verdict echoes the sha256 of the bytes actually sent)", spy2.calls == 1 and spy2.last["ok"] is True
            and spy2.last["selection_text_sha256"] != H.sha256_text(rr.evidence["selection_text"]))
    H.check("the changed bytes are visible in the admission binding digest", b2.metadata["registry_evidence"][0]["admission_binding_digest"]
            != H.import_f4(rr.record, rr.operator, proposal=rr.proposal, verifier=H.Spy())[0].metadata["registry_evidence"][0]["admission_binding_digest"])
    H.note("limit", "signature binds the statement, not the envelope bytes; whitespace/duplicate-identical-signature variants are admitted but change the binding digest")
    _limit("current Registry contracts admit duplicate identical signature entries and trailing whitespace of the envelope text")
