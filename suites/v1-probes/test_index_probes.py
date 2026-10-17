"""V1 validation probes for The Index (docx recommendation 02, acceptance items).

Each probe states its expected secure behaviour. A failing probe is a recorded
finding about the pinned component, not a harness error. Detectors are
calibrated against accept-all / reject-all stubs so a pass cannot be vacuous.

Links are built through ``_index_signing.LinkSigner``: against a service that requires a BitRep v1 attestation (the fixed
Index) every stored link is validly signed with a throwaway test-time issuer key provisioned in a trust-registry snapshot, and
the forged / unsigned / unknown-issuer / revoked / expired / replayed cases are rejection assertions; against a service that
predates the requirement (the old pin) the same probes send unsigned links, as before, and keep failing there.
"""
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from _index_signing import FORGERY_KINDS, LinkSigner, reason

CLAIM = {"canonical_text": "Probe claim alpha", "semantic_representation": {"subject": "a", "predicate": "b"},
         "domains": ["probe"], "created_by": "probe_user"}
FORGED = "forged-attestor-absent-from-every-registry"


def evidence(i, source="doi:10.1234/same-source"):
    return {"type": "experiment", "source_identifier": source,
            "metadata": {"methodology": "double-blind RCT", "sample_size": 1000, "uncertainty": 0.05, "copy": i},
            "submitted_by": "probe_user"}


def link_payload(claim_id, evidence_id, attested_by):
    return {"claim_id": claim_id, "evidence_id": evidence_id, "relation_type": "supports", "strength": 1.0,
            "attested_by": attested_by}


def require_links_stored(status):
    """Non-vacuity guard: a probe about stored links proves nothing if no link was stored. Links are now signed when the
    service requires it, so a missing link is a FAILURE of the probe setup (never a skip, never a pass)."""
    assert status.get("supporting_weight"), "no link was stored: the probe was not exercised (a rejected link is a failure here, not a pass)"


@pytest.fixture
def signer(index_client, tmp_path, monkeypatch):
    return LinkSigner(index_client, tmp_path, monkeypatch.setenv)


def forged_link_accepted(client, signer=None, kind="unsigned_forged_identity"):
    """True when the service stores a link whose attestor identity is unverifiable (kind: see _index_signing.FORGERY_KINDS)."""
    signer = signer or LinkSigner(client, ".", lambda *a: None, requires=False)
    c = client.post("/api/v1/claims/", json=CLAIM).json()
    e = client.post("/api/v1/evidence/", json=evidence(0)).json()
    r = client.post("/api/v1/evidence/links", json=signer.forged_body(kind, c["id"], e["id"]))
    return 200 <= r.status_code < 300


def stub(accept):
    app = FastAPI()
    n = {"c": 0}

    @app.post("/api/v1/claims/")
    def claim():
        return {"id": "c1"}

    @app.post("/api/v1/evidence/")
    def ev():
        return {"id": "e1"}

    @app.post("/api/v1/evidence/links", status_code=201)
    def link():
        if not accept:
            raise HTTPException(status_code=403, detail="unverified attestation")
        return {"id": "l1"}
    return TestClient(app)


def test_control_detector_flags_accept_all_stub():
    assert forged_link_accepted(stub(True)) is True


def test_control_detector_clears_reject_all_stub():
    assert forged_link_accepted(stub(False)) is False


@pytest.mark.parametrize("kind", sorted(FORGERY_KINDS))
def test_control_signed_forgery_detector_flags_accept_all_and_clears_reject_all(kind, tmp_path, monkeypatch, index_client):
    """Calibration of the signed-forgery detector: every forgery kind is flagged by an accept-all stub and cleared by a
    reject-all stub (so the rejection assertions below cannot pass vacuously). Needs the verifier to build signed forgeries."""
    try:
        import app.bitrep_verify  # noqa: F401
    except ImportError:
        pytest.skip("this Index version has no attestation verifier: signed forgeries cannot be built (unsigned detector is calibrated above)")
    for accept, expected in ((True, True), (False, False)):
        s = LinkSigner(stub(accept), tmp_path, monkeypatch.setenv, requires=True)
        assert forged_link_accepted(stub(accept), s, kind) is expected


def test_er02_forged_attestation_rejected_at_link_route(index_client, signer):
    """ER-02-2: forged attestations are rejected (unsigned link with an unregistered attestor)."""
    assert not forged_link_accepted(index_client, signer), "link accepted with unverifiable attested_by"


@pytest.mark.parametrize("kind", sorted(FORGERY_KINDS))
def test_er02_forged_attestation_variants_rejected_and_never_stored(kind, index_client, signer):
    """ER-02-2: unsigned / unknown-issuer / wrong-key / revoked / expired / wrong-audience / tampered / mis-bound attestations are
    rejected with the documented status and reason, nothing is stored, and a valid signed link IS accepted (positive control)."""
    if not signer.requires:
        pytest.skip("service does not verify attestations (old behaviour): covered by test_er02_forged_attestation_rejected_at_link_route")
    c = index_client.post("/api/v1/claims/", json=CLAIM).json()
    e = index_client.post("/api/v1/evidence/", json=evidence(0)).json()
    r = index_client.post("/api/v1/evidence/links", json=signer.forged_body(kind, c["id"], e["id"]))
    want_status, want_reason = FORGERY_KINDS[kind]
    assert (r.status_code, reason(r)) == (want_status, want_reason), f"{kind}: HTTP {r.status_code} {r.text[:200]}"
    assert signer.stored_links(c["id"]) == []
    assert index_client.get(f"/api/v1/evidence/epistemic-status/{c['id']}").json()["supporting_weight"] == 0
    assert signer.post_link(c["id"], e["id"]).status_code == 201, "positive control: a validly signed link must be accepted"


def test_er02_replayed_attestations_rejected_or_idempotent(index_client, signer):
    """ER-02-2: an attestation cannot be replayed for a different link or claim; reuse of an attestation id for another
    statement conflicts; an exact resubmission is idempotent and adds no second link or weight."""
    if not signer.requires:
        pytest.skip("service does not verify attestations (old behaviour): nothing to replay against")
    c = index_client.post("/api/v1/claims/", json=CLAIM).json()
    c2 = index_client.post("/api/v1/claims/", json={**CLAIM, "canonical_text": "Probe claim beta"}).json()
    e = index_client.post("/api/v1/evidence/", json=evidence(0)).json()
    first = signer.valid_body(c["id"], e["id"], attestation_id="att-replay")
    r1 = index_client.post("/api/v1/evidence/links", json=first)
    assert r1.status_code == 201
    weight = index_client.get(f"/api/v1/evidence/epistemic-status/{c['id']}").json()["supporting_weight"]
    assert weight > 0
    for tamper in ({"strength": 0.1}, {"relation_type": "contradicts"}, {"claim_id": c2["id"]}):
        r = index_client.post("/api/v1/evidence/links", json={**first, **tamper})
        assert (r.status_code, reason(r)) == (422, "attestation_binding_mismatch"), f"replay with {tamper}: {r.status_code} {r.text[:200]}"
    assert signer.stored_links(c2["id"]) == []
    conflict = index_client.post("/api/v1/evidence/links", json=signer.valid_body(c["id"], e["id"], strength=0.5, attestation_id="att-replay"))
    assert (conflict.status_code, reason(conflict)) == (409, "attestation_id_conflict")
    again = index_client.post("/api/v1/evidence/links", json=first)
    assert again.status_code == 200 and again.json()["id"] == r1.json()["id"]
    assert len(signer.stored_links(c["id"])) == 1
    assert index_client.get(f"/api/v1/evidence/epistemic-status/{c['id']}").json()["supporting_weight"] == weight


def test_er02_no_trust_snapshot_fails_closed(index_client, signer):
    """ER-02-2: without a usable operator trust snapshot the service refuses links (503), it does not accept them."""
    if not signer.requires:
        pytest.skip("service does not verify attestations (old behaviour): no trust snapshot concept")
    c = index_client.post("/api/v1/claims/", json=CLAIM).json()
    e = index_client.post("/api/v1/evidence/", json=evidence(0)).json()
    body = signer.valid_body(c["id"], e["id"])
    signer.unavailable_registry()
    r = index_client.post("/api/v1/evidence/links", json=body)
    assert (r.status_code, reason(r)) == (503, "trust_unavailable")
    assert signer.stored_links(c["id"]) == []


def test_er02_accepted_claim_cannot_be_updated_or_deleted(index_client):
    """ER-02-1: public API cannot bypass accepted-object invariants."""
    c = index_client.post("/api/v1/claims/", json=CLAIM).json()
    put = index_client.put(f"/api/v1/claims/{c['id']}", json={"canonical_text": "tampered"})
    delete = index_client.delete(f"/api/v1/claims/{c['id']}")
    assert put.status_code == 409 and delete.status_code == 409
    assert index_client.get(f"/api/v1/claims/{c['id']}").json()["canonical_text"] == CLAIM["canonical_text"]


def test_er02_duplicated_evidence_is_not_independent_corroboration(index_client, signer):
    """ER-02-4: five copies of one source must not read as five independent sources. All five links are stored
    (validly signed where the service requires it), so independence is genuinely computed."""
    c = index_client.post("/api/v1/claims/", json=CLAIM).json()
    for i in range(5):
        e = index_client.post("/api/v1/evidence/", json=evidence(i)).json()
        signer.store_link(c["id"], e["id"], "probe_attestor")
    assert len(signer.stored_links(c["id"])) == 5, "all five links must be stored for independence to be computed"
    s = index_client.get(f"/api/v1/evidence/epistemic-status/{c['id']}").json()
    require_links_stored(s)
    assert s["independence_score"] <= 0.2, f"independence_score={s['independence_score']} for 1 distinct source"


def test_er02_independent_sources_control_raises_independence(index_client, signer):
    """Detector control for the duplicated-evidence probe: five DISTINCT sources, same signing path, score higher than one source
    (so the <= 0.2 assertion above is a real measurement, not a constant)."""
    c = index_client.post("/api/v1/claims/", json=CLAIM).json()
    for i in range(5):
        e = index_client.post("/api/v1/evidence/", json=evidence(i, source=f"doi:10.1234/distinct-{i}")).json()
        signer.store_link(c["id"], e["id"], "probe_attestor")
    s = index_client.get(f"/api/v1/evidence/epistemic-status/{c['id']}").json()
    require_links_stored(s)
    assert s["independence_score"] > 0.2, f"independence_score={s['independence_score']} for 5 distinct sources"


def test_er02_status_reproducible_from_identical_inputs(index_client, signer):
    """ER-02-4: status is reproducible from pinned inputs."""
    c = index_client.post("/api/v1/claims/", json=CLAIM).json()
    e = index_client.post("/api/v1/evidence/", json=evidence(0)).json()
    signer.store_link(c["id"], e["id"], "probe_attestor")
    a = index_client.get(f"/api/v1/evidence/epistemic-status/{c['id']}").json()
    require_links_stored(a)
    b = index_client.get(f"/api/v1/evidence/epistemic-status/{c['id']}").json()
    for k in ("status", "supporting_weight", "contradicting_weight", "independence_score", "robustness_score"):
        assert a[k] == b[k]
