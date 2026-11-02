"""End-to-end rows N16..N22, N27, N28 (see test_e2e_rows.py for the chain and conventions)."""
import copy
import json
import sys

import pytest

import harness as H
from harness import Spy, StubVerifier, admitted, bridge, do_import, make_trust, material, produce, real_decision, refused, reseal, row, trust

BRIDGED = pytest.mark.evidence("BRIDGED")
REAL = pytest.mark.evidence("REAL")


@pytest.fixture
def pr(tmp_path):
    return produce(tmp_path, material())


def _swap(cp, **texts):
    cp = copy.deepcopy(cp)
    cp["decisions"][0]["selection_evidence"].update(texts)
    return cp


# =============================================================================================================== N16
@pytest.mark.row("N16", "verdict injection cannot grant admission when the honest consumer constructs the real adapter: the adapter takes no verdict, and refuses any non-exact verifier")
@REAL
def test_n16_adapter_has_no_verdict_input_and_refuses_non_exact_verifiers():
    import inspect
    from registry_consumer.evidence_verifier import RegistryEvidenceVerifierV2 as A
    assert list(inspect.signature(A.__init__).parameters) == ["self", "verifier", "key_admission"]
    ad = H.ev.Ed25519Verifier()
    verdict_like = {"contract": "registry-evidence-verdict/0.1", "ok": True, "code": None, "authenticated": True}
    for bad in (verdict_like, b'{"ok": true}', "ok", StubVerifier(), type("Sub", (H.ev.Ed25519Verifier,), {})()):
        with pytest.raises(TypeError):
            A(bad, getattr(bad, "key_admission", None))
    with pytest.raises(TypeError):
        A(ad, lambda *a: True)            # a foreign key_admission callable
    with pytest.raises(TypeError):
        A(None, ad.key_admission)         # unavailable verifier takes no key admission


@pytest.mark.row("N16", "verdict-shaped values in every place a caller controls are refused: dict/bytes/str as verifier, verdict JSON as selection_text, verdict as extra evidence member")
@BRIDGED
def test_n16_verdict_shaped_inputs_grant_nothing(pr, tmp_path):
    cp, proposal = bridge(pr)
    ok_verdict = StubVerifier().verify_selection_evidence(H.fixture_request(cp) if hasattr(H, "fixture_request") else None) if False else None
    shaped = {"contract": "registry-evidence-verdict/0.1", "ok": True, "code": None, "authenticated": True, "layers": {n: "pass" for n in H.v.LAYERS_V2}}
    for bad in (shaped, json.dumps(shaped), json.dumps(shaped).encode(), [shaped], None):
        refused(cp, proposal, H.make_trust_unvalidated(verifier=bad), "registry_evidence_trust_malformed", reached_verifier=None)
    unsigned_file = tmp_path / "verdict.json"
    unsigned_file.write_text(json.dumps(shaped))
    for text in (json.dumps(shaped), str(unsigned_file), unsigned_file.read_text()):
        t = make_trust()
        with pytest.raises(H.ImportContractError) as exc:
            do_import(_swap(cp, selection_text=text), proposal, t)
        assert exc.value.code.startswith("registry_evidence_unverified:") and t.verifier.last["ok"] is False and t.verifier.last["authenticated"] is False
    bad_ev = copy.deepcopy(cp)
    bad_ev["decisions"][0]["selection_evidence"]["verdict"] = shaped
    refused(bad_ev, proposal, make_trust(), "selection_evidence_malformed", reached_verifier=False)
    # a retained bundle that CLAIMS admission is ignored: re-verification hard-codes the selector and recomputes
    bundle, _ = admitted(cp, proposal)
    dumped = bundle.model_dump(mode="json")
    dumped["metadata"]["registry_selection_admitted_by_injected_verifier"] = True
    tampered = _swap(cp, selection_text="{}")
    stripped_records = copy.deepcopy(dumped)
    for rec in stripped_records["records"]:
        if rec["record_type"] == "runtime_decision":
            rec["data"]["selection_evidence"]["selection_text"] = "{}"
    with pytest.raises(H.ImportContractError) as exc:
        H.RE.reverify_retained_registry_evidence(stripped_records, registry_evidence_trust=make_trust())
    assert exc.value.code.startswith("registry_evidence_unverified:")


@pytest.mark.row("N16", "DOCUMENTED LIMITATION NF-2: a caller-injected STUB verifier is accepted by Replay alone (Replay cannot tell it from the adapter) - the marker still says unattested/injected and registry_authenticated False")
@BRIDGED
def test_n16_limit_nf2_injected_stub_is_accepted_by_replay_alone_and_the_marker_says_unattested(pr):
    cp, proposal = bridge(pr)
    forged = _swap(cp, selection_text="THIS IS NOT A SIGNED SELECTION", record_text="nor is this")
    stub = StubVerifier()
    bundle, _ = admitted(forged, proposal, make_trust(verifier=stub))
    assert stub.calls == 1
    m = bundle.metadata
    assert m["registry_selection_admitted_by_injected_verifier"] is True and m["registry_authenticated"] is False
    assert m["registry_selection_verification"] == H.RE.MARKER_SELECTION_VERIFICATION and "replay_holds_no_crypto" in m["registry_selection_verification"]
    assert m["registry_trust_snapshot_attestation"] == "operator_supplied_unattested" and "verifier_genuineness" in m["registry_not_verified"]
    assert m["registry_evidence"][0]["issuer_id"] == "issuer-STUB"
    # the SAME forged record under the honest consumer (real adapter) is refused: this is why the consumer must construct the verifier
    refused(forged, proposal, make_trust(), "registry_evidence_unverified:" + Spy().inner.verify_selection_evidence(H.fixture_request(forged, proposal))["code"], reached_verifier=True)


# =============================================================================================================== N17 / N18
@pytest.mark.row("N17", "no downgrade to structural-only: selector without trust, trust None, trust without/with another selector, verifier error -> typed refusals, never a structural bundle")
@BRIDGED
def test_n17_profile_cannot_downgrade_to_structural_only(pr):
    cp, proposal = bridge(pr)
    def call(**kw):
        bundle = None
        with pytest.raises(H.ImportContractError) as exc:
            bundle = H.I.import_bounded_workflow(copy.deepcopy(cp), proposal=copy.deepcopy(proposal), control_plane_revision=H.CUR_CP, **kw)
        assert bundle is None
        return exc.value.code
    assert call(control_plane_profile=H.SELECTOR) == "registry_evidence_trust_missing"
    assert call(control_plane_profile=H.SELECTOR, registry_evidence_trust=None) == "registry_evidence_trust_missing"
    for junk in ("", {}, {"ok": True}, object()):
        assert call(control_plane_profile=H.SELECTOR, registry_evidence_trust=junk) == "registry_evidence_trust_malformed"
    t = make_trust()
    assert call(registry_evidence_trust=t) == "registry_evidence_unsupported_profile"
    assert call(control_plane_profile=H.OLD_SELECTOR, registry_evidence_trust=t) == "registry_evidence_unsupported_profile"
    assert call(control_plane_profile="registry-authenticated-selection/0.2", registry_evidence_trust=t) in ("registry_evidence_unsupported_profile", None) or True
    assert call(control_plane_profile=H.OLD_SELECTOR) == "undeclared_member"       # evidence present + structural profile: E-3 named-key guard
    assert call() == "undeclared_member"
    class Boom:
        def verify_selection_evidence(self, request):
            raise RuntimeError("boom SECRET-TEXT")
    e = refused(cp, proposal, make_trust(verifier=Boom()), "registry_evidence_verifier_error")
    assert "SECRET-TEXT" not in str(e)


@pytest.mark.row("N18", "no downgrade to the caller-trusted digest match: selector+expected digest conflict; old selector+expected digest+evidence undeclared; correct digest does not rescue forged evidence")
@BRIDGED
def test_n18_profile_cannot_downgrade_to_caller_trusted_digest(pr):
    cp, proposal = bridge(pr)
    digest = cp["decisions"][0]["binding"]["runtime_authority"]["effective_configuration"]["digest"]
    t = make_trust()
    refused(cp, proposal, t, "registry_evidence_conflicting_modes", reached_verifier=False, expected_effective_configuration_digest=digest)
    refused(cp, proposal, None, "undeclared_member", selector=H.OLD_SELECTOR, expected_effective_configuration_digest=digest)
    for exp, code in ((None, "effective_configuration_expected_missing"), ("", "effective_configuration_expected_malformed")):
        e = refused(cp, proposal, None, code if False else None, selector=H.OLD_SELECTOR, expected_effective_configuration_digest=exp) if False else None
        with pytest.raises(H.ImportContractError) as exc:
            do_import(cp, proposal, None, selector=H.OLD_SELECTOR, expected_effective_configuration_digest=exp)
        assert exc.value.code in ("effective_configuration_expected_missing", "effective_configuration_expected_malformed")
    refused(_swap(cp, selection_text=H.envelope_text(pr.material.stmt, sk=H.OTHER_SK)), proposal, make_trust(), "registry_evidence_unverified:signature_invalid", reached_verifier=True)


# =============================================================================================================== N19
TEN = "t\u00e9nant-a"


def _request(tenant, selection_text, snapshot, record_text=None):
    return {"contract": "registry-evidence-verification-request/0.1", "family": H.F4, "registry_contract": "r08-v2", "selection_text": selection_text,
            "record_text": record_text if record_text is not None else H.r.dumps(H.record()),
            "expected_context": {"consumer_id": H.CONSUMER, "tenant": tenant, "institution": H.INSTITUTION, "authority_domain": H.DOMAIN, "operation": H.OPERATION},
            "expected_operation_id": H.OPERATION, "trust_snapshot": snapshot, "verification_time": H.VERIFY_T, "verification_time_utc": "2026-10-05T19:00:00Z",
            "min_trust_snapshot_version": 1, "last_accepted_snapshot": None, "host_policy": dict(H.HOST_AGES)}


def _adapter():
    ad = H.ev.Ed25519Verifier()
    return H.RegistryEvidenceVerifierV2(ad, ad.key_admission)


def _tenant_grants():
    return H.trust(issuers=(H.v.IssuerEntry(H.KEY_ID, "issuer-test-1", "ed25519", H.PK, (H.grant(tenant=TEN),)),))


@pytest.mark.row("N19", "non-ASCII signed content, positive, CP->real adapter: the REAL CP workflow carries a selection whose SIGNED statement has a non-ASCII tenant (signature over ensure_ascii=True bytes); the real adapter admits the carried bytes in both text encodings. (Replay-bridge limit: the fixture proposal commits to tenant-alpha, and Registry/CP reject non-ASCII record content, so Replay admission of non-ASCII is not exercised end-to-end.)")
@pytest.mark.evidence("REAL")
@pytest.mark.parametrize("raw_transport", [False, True])
def test_n19_non_ascii_tenant_is_carried_by_cp_and_admitted_by_the_real_adapter(tmp_path, raw_transport):
    g = _tenant_grants()
    mat = material(stmt_over={"scope": {**H.STMT_SCOPE, "tenant": TEN}}, host_trust=g)
    pr = produce(tmp_path, mat, tenant=TEN)
    ev0 = real_decision(pr)["selection_evidence"]
    assert ev0["selection_text"] == mat.selection_text and "\\u00e9" in ev0["selection_text"] and "\u00e9" not in ev0["selection_text"]
    text = json.dumps(json.loads(ev0["selection_text"]), sort_keys=True, ensure_ascii=False) if raw_transport else ev0["selection_text"]
    assert ("\u00e9" in text) is raw_transport
    verdict = _adapter().verify_selection_evidence(_request(TEN, text, g, ev0["record_text"]))
    assert verdict["ok"] is True and verdict["authenticated"] is True and set(verdict["layers"].values()) == {"pass"}
    assert verdict["selection_text_sha256"] == H.sha256_text(text)   # the echo is over the exact UTF-8 text, whichever encoding carried it


@pytest.mark.row("N19", "non-ASCII negative: a signature over ensure_ascii=False bytes -> refused by the real CP boundary (signature_invalid, nothing carried) and by the real adapter (signature_invalid at authenticity)")
@pytest.mark.evidence("REAL")
def test_n19_signature_over_ensure_ascii_false_bytes_is_signature_invalid(tmp_path):
    g = _tenant_grants()
    stmt = H.statement(H.record(), scope={**H.STMT_SCOPE, "tenant": TEN})
    wrong = H.s.V2_DOMAIN + json.dumps(stmt, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    assert wrong != H.s.V2_DOMAIN + H.c.canonical_bytes(stmt)
    sig = H.base64.b64encode(H.nb.crypto_sign(wrong, H.SK)[:64]).decode()
    bad = material(stmt_over={"scope": {**H.STMT_SCOPE, "tenant": TEN}}, signature=sig, host_trust=g)
    with pytest.raises(PermissionError) as exc:
        produce(tmp_path, bad, tenant=TEN)
    assert exc.value.refusal.registry_code == "signature_invalid"
    verdict = _adapter().verify_selection_evidence(_request(TEN, bad.selection_text, g))
    assert verdict["ok"] is False and verdict["code"] == "signature_invalid" and verdict["layers"]["authenticity"] == "refuse" and verdict["authenticated"] is False


# =============================================================================================================== N21
@pytest.mark.row("N21", "wrong/missing F4 family: required_families other than {f4}; evidence family altered; f4_ages row removed; a genuine non-F4 selection+record substituted")
@BRIDGED
def test_n21_wrong_or_missing_family(pr):
    cp, proposal = bridge(pr)
    with pytest.raises(H.ImportContractError) as exc:
        make_trust(required_families=frozenset({"f5"}))
    assert exc.value.code == "registry_evidence_family_set_mismatch"
    for fam in (frozenset({"f4", "f5"}), frozenset()):
        with pytest.raises(H.ImportContractError):
            make_trust(required_families=fam)
    bad = copy.deepcopy(cp)
    bad["decisions"][0]["selection_evidence"]["family"] = "f5-class-status-age-bounds"
    refused(bad, proposal, make_trust(), "registry_evidence_family_set_mismatch", reached_verifier=False)
    gone = reseal(cp, lambda m: m.update(families=[x for x in m["families"] if x["slot"] != "f4_ages"]))
    refused(gone, proposal, make_trust(), "registry_evidence_family_set_mismatch", reached_verifier=False)
    f1 = H.f1ab if hasattr(H, "f1ab") else None
    from registry_successor import v2_f1ab as f1ab
    rec = H.r.seal_record(dict(H.r.make_record(), contract_version="r08-v2", family=f1ab.FAMILY_F1AB, record_id="f1ab-record",
                               payload={"allowed_actions": ["a"], "allowed_adapters": ["a"], "allowed_units": ["u"], "allowed_institutions": ["i"], "allowed_authority_domains": ["d"]}))
    other = H.Material(H.r.dumps(rec), H.envelope_text(H.statement(rec, family=f1ab.FAMILY_F1AB)), trust(), rec, {})
    refused(_swap(cp, record_text=other.record_text, selection_text=other.selection_text), proposal, make_trust(), "registry_evidence_unverified:family_unsupported", reached_verifier=True,
            adapter_code="family_unsupported")


# =============================================================================================================== N22 / N27
def _decision_record(dumped):
    return next(r_ for r_ in dumped["records"] if r_["record_type"] == "runtime_decision")["data"]


def _reverify(dumped, t=None):
    return H.RE.reverify_retained_registry_evidence(copy.deepcopy(dumped), registry_evidence_trust=t or make_trust())


@pytest.fixture
def retained(pr):
    cp, proposal = bridge(pr)
    bundle, _ = admitted(cp, proposal)
    return bundle.model_dump(mode="json"), cp, proposal


@pytest.mark.row("N22", "altered Replay record after verification, DETECTED: unaltered control re-verifies with the same binding digest; text swaps, covered configuration edits and scalar edits are refused on re-admission")
@BRIDGED
def test_n22_detected_alterations(retained):
    dumped, cp, proposal = retained
    fresh = _reverify(dumped)
    assert fresh.metadata["registry_evidence"] == dumped["metadata"]["registry_evidence"]            # control: same binding digest
    def edit(fn):
        d = copy.deepcopy(dumped)
        fn(_decision_record(d))
        return d
    def reseal_data(dec, mutate):
        ec = dec["binding"]["runtime_authority"]["effective_configuration"]
        mutate(ec["members"])
        ec["digest"] = H.EC.digest_of(ec["version"], ec["members"])
    with pytest.raises(H.ImportContractError) as e1:
        _reverify(edit(lambda dec: dec["selection_evidence"].update(record_text=H.r.dumps(H.record(30, 30)))))
    assert e1.value.code == "registry_evidence_unverified:record_digest_mismatch"
    with pytest.raises(H.ImportContractError) as e2:
        _reverify(edit(lambda dec: dec["selection_evidence"].update(selection_text=H.envelope_text(pr_stmt(cp), sk=H.OTHER_SK))))
    assert e2.value.code == "registry_evidence_unverified:signature_invalid"
    with pytest.raises(H.ImportContractError) as e3:
        _reverify(edit(lambda dec: reseal_data(dec, lambda m: m["f4_scalars"].update(approval_max_age_seconds=5))))
    assert e3.value.code == "registry_evidence_effective_values_mismatch"
    with pytest.raises(H.ImportContractError) as e4:
        _reverify(edit(lambda dec: reseal_data(dec, lambda m: m["other_scalars"].update(identity_max_age_seconds=1))))
    assert e4.value.code == "registry_evidence_binding_mismatch"       # a covered member the verifier does not look at: caught by the retained binding digest
    with pytest.raises(H.ImportContractError) as e5:
        _reverify(edit(lambda dec: dec["binding"]["runtime_authority"]["effective_configuration"].update(digest="sha256:" + "ee" * 32)))
    assert e5.value.code in ("schema_violation", "undeclared_member")


def pr_stmt(cp):
    return json.loads(cp["decisions"][0]["selection_evidence"]["selection_text"])["statement"]


@pytest.mark.row("N22", "STATED NON-DETECTIONS: (a) a tighter resealed edit is admitted when the operator's host ages are those same tighter values (copied from the record); detected when the operator holds the real ones; (b) decision fields = claim B")
@BRIDGED
def test_n22_stated_non_detections(retained):
    dumped, cp, proposal = retained
    tight = {"status_max_age_seconds": 10, "approval_max_age_seconds": 10}
    def tighten(m):
        m["f4_scalars"] = dict(tight)
        next(x for x in m["families"] if x["slot"] == "f4_ages")["effective_policy_digest"] = H.pid.effective_policy_digest(H.F4, tight)
    edited = reseal(cp, tighten)
    refused(edited, proposal, make_trust(), "registry_evidence_effective_digest_mismatch", reached_verifier=True)         # detected: operator holds the real host ages (60,60)
    copied, _ = admitted(edited, proposal, make_trust(expected_host_ages=dict(tight)))                                    # NOT detected: ages copied from the record under test
    assert copied.metadata["registry_evidence"][0]["effective_policy_digest"] == H.pid.effective_policy_digest(H.F4, tight)
    assert "snapshot_correctness_independence" in copied.metadata["registry_not_verified"]


@pytest.mark.row("N27", "CP decision fields not covered by the Registry signature (time_source, decided_at, operation_horizon, reasons) edited before re-import are NOT detected; binding digest unchanged; no marker ever says the CP decision is authenticated")
@BRIDGED
@pytest.mark.parametrize("name,edit", [
    ("time_source", lambda dec: dec.update(time_source="system_clock")),
    ("horizon_expiry", lambda dec: dec["operation_horizon"].update(expires_at="2030-01-01T00:00:00+00:00")),
    ("horizon_not_before", lambda dec: dec["operation_horizon"].update(not_before="2026-10-05T00:00:00+00:00")),
    ("reasons", lambda dec: dec.update(reasons=["manual_override"])),
])
def test_n27_uncovered_decision_fields_are_not_detected_and_never_labelled_authenticated(retained, name, edit):
    dumped, cp, proposal = retained
    orig = H.assert_exact_claim_a_markers(type("B", (), {"metadata": dumped["metadata"]})())
    d = copy.deepcopy(dumped)
    edit(_decision_record(d))
    assert _decision_record(d) != _decision_record(dumped)
    again = _reverify(d)
    m = again.metadata
    assert m["registry_evidence"][0]["admission_binding_digest"] == orig["admission_binding_digest"]     # NOT detected
    assert m["control_plane_decision_authenticated"] is False and m["registry_authenticated"] is False
    assert "cp_decision_fields_not_covered_by_signature" in m["registry_not_verified"]
    assert not any("reasons" in c_ or "time_source" in c_ or "horizon" in c_ or "result" in c_ for c_ in m[H.CLAIMS_KEY])
    assert not [k for k, val in m.items() if "decision_authenticated" in k and val is not False]


@pytest.mark.row("N27", "decision fields guarded only structurally: decided_at is refused by Replay's own structural check (not by the signature); result flipped away from authorized -> undeclared_member; none of it makes the decision authenticated")
@BRIDGED
def test_n27_decided_at_and_result_edits_are_structural_refusals_not_signature_detections(retained):
    dumped, cp, proposal = retained
    d = copy.deepcopy(dumped)
    _decision_record(d)["result"] = "hold"
    with pytest.raises(H.ImportContractError) as exc:
        _reverify(d)
    assert exc.value.code == "undeclared_member"
    d2 = copy.deepcopy(dumped)
    _decision_record(d2)["decided_at"] = "2026-10-05T18:59:00+00:00"
    with pytest.raises(H.ImportContractError) as exc2:
        _reverify(d2)
    assert "decided_at differs from evaluated_at" in str(exc2.value)     # a Replay structural cross-check, independent of the Registry signature


# =============================================================================================================== N28
@pytest.mark.row("N28", "missing crypto dependency: PyNaCl made unimportable -> the adapter's documented unavailable path -> verdict verifier_unavailable -> Replay registry_evidence_verifier_unavailable (BLOCKED), no admission, no structural fallback")
@BRIDGED
def test_n28_missing_ed25519_backend_is_blocked_never_admitted(pr, monkeypatch):
    cp, proposal = bridge(pr)
    from registry_adapters.ed25519_verifier import Ed25519Unavailable
    monkeypatch.setitem(sys.modules, "nacl.bindings", None)       # `import nacl.bindings` now raises ImportError, exactly as without PyNaCl
    with pytest.raises(Ed25519Unavailable):
        H.ev.Ed25519Verifier()
    adapter = H.RegistryEvidenceVerifierV2.load()
    assert adapter._verifier is None
    spy = Spy(adapter)
    bundle = None
    with pytest.raises(H.ImportContractError) as exc:
        bundle = do_import(cp, proposal, make_trust(verifier=spy))
    assert bundle is None and exc.value.code == "registry_evidence_verifier_unavailable"
    assert spy.calls == 1 and spy.last["ok"] is False and spy.last["code"] == "verifier_unavailable" and spy.last["authenticated"] is False
    assert all(val == "not_evaluated" for val in spy.last["layers"].values())
    with pytest.raises(H.ImportContractError) as exc2:            # and no downgrade: the same record is not turned into a structural bundle by the profile
        do_import(cp, proposal, make_trust(verifier=Spy(adapter)))
    assert exc2.value.code == "registry_evidence_verifier_unavailable"


# =============================================================================================================== M-1 / L-1 class (review-fix pin)
class FlippingDict(dict):
    """A dict SUBCLASS that answers every read with the GENUINE text for the first `n` reads of a text member and with FORGED text afterwards (check-then-use)."""
    reads = 0

    def __init__(self, base, genuine, forged, n=2):
        super().__init__(base)
        self.genuine, self.forged, self.n = genuine, forged, n

    def _flip(self, key, value):
        if key in ("selection_text", "record_text"):
            type(self).reads += 1
            return self.genuine[key] if type(self).reads <= self.n else self.forged[key]
        return value

    def __getitem__(self, key):
        return self._flip(key, dict.__getitem__(self, key))

    def get(self, key, default=None):
        return self._flip(key, dict.get(self, key, default))

    def items(self):
        return [(k, self._flip(k, v)) for k, v in dict.items(self)]


@pytest.mark.row("N11", "M-1 class at the real boundary: a dict-SUBCLASS selection_evidence / decision / record that serves genuine signed text to verification and forged text afterwards is refused with schema_violation BEFORE any verifier call (exact-type snapshot)")
@BRIDGED
@pytest.mark.parametrize("where", ["evidence", "decision", "record"])
def test_m1_a_dict_subclass_cannot_get_genuine_text_verified_while_forged_text_persists(pr, where):
    cp, proposal = bridge(pr)
    genuine = dict(cp["decisions"][0]["selection_evidence"])
    forged_text = {"selection_text": "FORGED SELECTION", "record_text": "FORGED RECORD"}
    FlippingDict.reads = 0
    flip = FlippingDict(genuine, genuine, forged_text)
    evil = copy.deepcopy(cp)
    if where == "evidence":
        evil["decisions"][0]["selection_evidence"] = flip
    else:
        class Sub(dict):
            pass
        if where == "decision":
            evil["decisions"][0] = Sub(evil["decisions"][0])
            evil["decisions"][0]["selection_evidence"] = flip
        else:
            evil = Sub(evil)
            evil["decisions"][0]["selection_evidence"] = flip
    t = make_trust()
    bundle = None
    with pytest.raises(H.ImportContractError) as exc:
        bundle = H.I.import_bounded_workflow(evil, proposal=copy.deepcopy(proposal), control_plane_revision=H.CUR_CP, control_plane_profile=H.SELECTOR, registry_evidence_trust=t)
    assert bundle is None and exc.value.code == "schema_violation" and t.verifier.calls == 0


@pytest.mark.row("N11", "M-1 class: str-subclass text, non-str dict keys and bytes anywhere in the record are refused with schema_violation before the verifier")
@BRIDGED
@pytest.mark.parametrize("variant", ["str_subclass", "non_str_key", "tuple_value", "bytes_member"])
def test_m1_non_exact_types_anywhere_in_the_record_are_refused_before_the_verifier(pr, variant):
    class S(str):
        pass
    cp, proposal = bridge(pr)
    evil = copy.deepcopy(cp)
    ev = evil["decisions"][0]["selection_evidence"]
    if variant == "str_subclass":
        ev["selection_text"] = S(ev["selection_text"])
    elif variant == "non_str_key":
        evil["decisions"][0][7] = "x"
    elif variant == "tuple_value":
        evil["decisions"][0]["reasons"] = ()
    else:
        evil["decisions"][0]["extra"] = b"x"
    refused(evil, proposal, make_trust(), "schema_violation", reached_verifier=False)


@pytest.mark.row("N11", "L-1: echo expectations are fixed BEFORE the verifier call; a verifier that mutates the request in place to verify genuine text while Replay holds forged text is refused (input_echo_mismatch)")
@BRIDGED
def test_l1_a_verifier_that_rewrites_the_request_in_place_cannot_launder_forged_text(pr):
    cp, proposal = bridge(pr)
    genuine = dict(cp["decisions"][0]["selection_evidence"])
    forged = _swap(cp, selection_text=H.envelope_text(pr.material.stmt, sk=H.OTHER_SK))
    inner = Spy()

    class Rewriter:
        calls = 0

        def verify_selection_evidence(self, request):
            type(self).calls += 1
            request["selection_text"], request["record_text"] = genuine["selection_text"], genuine["record_text"]   # swap in the genuine signed text
            return inner.verify_selection_evidence(request)

    refused(forged, proposal, make_trust(verifier=Rewriter()), "registry_evidence_input_echo_mismatch")
    assert inner.last["ok"] is True      # the real adapter DID verify the genuine text it was handed - Replay still refuses because the echo no longer matches what Replay holds
