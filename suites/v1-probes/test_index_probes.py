"""V1 validation probes for The Index (docx recommendation 02, acceptance items).

Each probe states its expected secure behaviour. A failing probe is a recorded
finding about the pinned component, not a harness error. Detectors are
calibrated against accept-all / reject-all stubs so a pass cannot be vacuous.
"""
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

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


def forged_link_accepted(client):
    """True when the service stores a link whose attestor identity is unverifiable."""
    c = client.post("/api/v1/claims/", json=CLAIM).json()
    e = client.post("/api/v1/evidence/", json=evidence(0)).json()
    r = client.post("/api/v1/evidence/links", json=link_payload(c["id"], e["id"], FORGED))
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


def test_er02_forged_attestation_rejected_at_link_route(index_client):
    """ER-02-2: forged attestations are rejected (unsigned link with an unregistered attestor)."""
    assert not forged_link_accepted(index_client), "link accepted with unverifiable attested_by"


def test_er02_accepted_claim_cannot_be_updated_or_deleted(index_client):
    """ER-02-1: public API cannot bypass accepted-object invariants."""
    c = index_client.post("/api/v1/claims/", json=CLAIM).json()
    put = index_client.put(f"/api/v1/claims/{c['id']}", json={"canonical_text": "tampered"})
    delete = index_client.delete(f"/api/v1/claims/{c['id']}")
    assert put.status_code == 409 and delete.status_code == 409
    assert index_client.get(f"/api/v1/claims/{c['id']}").json()["canonical_text"] == CLAIM["canonical_text"]


def test_er02_duplicated_evidence_is_not_independent_corroboration(index_client):
    """ER-02-4: five copies of one source must not read as five independent sources."""
    c = index_client.post("/api/v1/claims/", json=CLAIM).json()
    for i in range(5):
        e = index_client.post("/api/v1/evidence/", json=evidence(i)).json()
        index_client.post("/api/v1/evidence/links", json=link_payload(c["id"], e["id"], "probe_attestor"))
    s = index_client.get(f"/api/v1/evidence/epistemic-status/{c['id']}").json()
    assert s["independence_score"] <= 0.2, f"independence_score={s['independence_score']} for 1 distinct source"


def test_er02_status_reproducible_from_identical_inputs(index_client):
    """ER-02-4: status is reproducible from pinned inputs."""
    c = index_client.post("/api/v1/claims/", json=CLAIM).json()
    e = index_client.post("/api/v1/evidence/", json=evidence(0)).json()
    index_client.post("/api/v1/evidence/links", json=link_payload(c["id"], e["id"], "probe_attestor"))
    a = index_client.get(f"/api/v1/evidence/epistemic-status/{c['id']}").json()
    b = index_client.get(f"/api/v1/evidence/epistemic-status/{c['id']}").json()
    for k in ("status", "supporting_weight", "contradicting_weight", "independence_score", "robustness_score"):
        assert a[k] == b[k]
