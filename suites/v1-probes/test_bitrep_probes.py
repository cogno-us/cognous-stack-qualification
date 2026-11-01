"""V1 validation probes for BitRep (docx recommendation 01): ER-01-3 temporal semantics, ER-01-4 demonstration proofs.

Run against the pinned checkout named by PROBE_BITREP_DIR. A failing probe is a recorded product finding.
"""
import base64
import copy
import hashlib
import re
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from conftest import pin_dir

NOW = 1800000000
SEED_A = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))  # public synthetic test seeds
SEED_B = Ed25519PrivateKey.from_private_bytes(bytes(range(1, 33)))


def pub(k):
    return base64.b64encode(k.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()


def trust_doc(keys, valid_until=NOW + 1000, published_at=NOW - 100):
    return {"registry_version": "bitrep-trust/1", "audience": "index:test", "published_at": published_at,
            "valid_until": valid_until, "keys": keys}


def key(key_id="key:1", seed=SEED_A, valid_from=NOW - 100, valid_until=NOW + 1000, revoked_at=None):
    return {"issuer": "issuer:alice", "key_id": key_id, "public_key": pub(seed), "valid_from": valid_from,
            "valid_until": valid_until, "revoked_at": revoked_at}


def envelope(seed=SEED_A, key_id="key:1", issued_at=NOW - 10, expires_at=NOW + 100):
    from models.verification import AttestationEnvelope, SignedStatement
    from utils.verification import canonical_bytes
    st = SignedStatement.model_validate({
        "protocol_version": "bitrep-attestation/1", "algorithm": "Ed25519", "attestation_id": "probe-1",
        "issuer": "issuer:alice", "key_id": key_id, "subject": "claim:42", "statement_type": "asserts",
        "audience": "index:test", "content_digest": "sha256:" + hashlib.sha256(b"probe").hexdigest(),
        "issued_at": issued_at, "not_before": issued_at, "expires_at": expires_at})
    sig = base64.b64encode(seed.sign(canonical_bytes(st))).decode()
    return AttestationEnvelope(statement=st, signature=sig)


def verify(env, doc, now=NOW):
    from utils.trust import TrustRegistry
    from utils.verification import verify_attestation
    return verify_attestation(env, TrustRegistry.model_validate(copy.deepcopy(doc)), now)


@pytest.fixture(autouse=True)
def _pin(tmp_path, monkeypatch):
    pin_dir("PROBE_BITREP_DIR")
    monkeypatch.chdir(tmp_path)  # BitRep creates ./bitrep.db on import; keep it out of the workspace


# ----------------------------------------------------------------- ER-01-3
def test_probe_er013_revocation_applies_from_revoked_at_and_is_not_backdatable():
    env = envelope(issued_at=NOW - 50)  # issued well before the revocation instant
    assert verify(env, trust_doc([key(revoked_at=NOW + 1)])).outcome == "verified"  # future revocation: not yet in force
    at = verify(env, trust_doc([key(revoked_at=NOW)]))
    assert (at.outcome, at.reason) == ("rejected", "key_revoked")  # boundary inclusive
    # a statement issued before revocation is still rejected after it (no attacker-selected backdating)
    late = verify(env, trust_doc([key(revoked_at=NOW - 30)]))
    assert (late.outcome, late.reason) == ("rejected", "key_revoked")
    assert late.assurance == "none"


def test_probe_er013_key_and_statement_expiry_boundaries_are_half_open():
    env = envelope(expires_at=NOW + 100)
    assert verify(env, trust_doc([key(valid_until=NOW + 1)])).outcome == "verified"
    assert verify(env, trust_doc([key(valid_until=NOW)])).reason == "key_expired"
    assert verify(env, trust_doc([key(valid_from=NOW + 1)])).reason == "key_not_yet_valid"
    assert verify(env, trust_doc([key()]), now=NOW + 99).outcome == "verified"
    assert verify(env, trust_doc([key()]), now=NOW + 100).reason == "attestation_expired"


def test_probe_er013_rotation_old_key_rejected_after_retirement_new_key_accepted():
    old_stmt = envelope(SEED_A, "key:1", issued_at=NOW - 50)
    doc = trust_doc([key("key:1", SEED_A, valid_from=NOW - 100, valid_until=NOW - 10),
                     key("key:2", SEED_B, valid_from=NOW - 20, valid_until=NOW + 1000)])
    r = verify(old_stmt, doc)
    assert (r.outcome, r.reason) == ("rejected", "key_expired")  # valid at issuance but not at evaluation
    assert verify(envelope(SEED_B, "key:2", issued_at=NOW - 10), doc).outcome == "verified"
    # new key cannot vouch for a statement issued before the new key's validity began
    pre = verify(envelope(SEED_B, "key:2", issued_at=NOW - 50), doc)
    assert pre.reason == "issuance_outside_key_validity"
    # a signature by the retired key id cannot be passed off under the new key id
    assert verify(envelope(SEED_A, "key:2", issued_at=NOW - 10), doc).reason == "invalid_signature"


def test_probe_er013_trust_snapshot_currency_is_half_open_and_fails_closed():
    from utils.trust import TrustUnavailable
    env = envelope()
    with pytest.raises(TrustUnavailable):
        verify(env, trust_doc([key()], valid_until=NOW), now=NOW)  # valid_until exclusive
    with pytest.raises(TrustUnavailable):
        verify(env, trust_doc([key()], published_at=NOW + 1))  # snapshot from the future
    assert verify(env, trust_doc([key()], published_at=NOW)).outcome == "verified"  # published_at inclusive


def test_probe_er013_temporal_semantics_are_documented_and_match_the_code():
    spec = (Path(pin_dir("PROBE_BITREP_DIR")) / "docs" / "VERIFICATION_CONTRACT_V1.md").read_text(encoding="utf-8")
    flat = re.sub(r"\s+", " ", spec)
    for phrase in ("`[valid_from, valid_until)`", "strictly before `expires_at`", "There is no clock-skew allowance",
                   "Once `now >= revoked_at`", "including statements issued before revocation",
                   "The server's current time must be in `[published_at, valid_until)`"):
        assert phrase in flat, f"contract no longer documents: {phrase}"
    # the documented no-skew rule is enforced: one second before issuance is rejected, not tolerated
    r = verify(envelope(issued_at=NOW + 1, expires_at=NOW + 100), trust_doc([key()]))
    assert r.reason == "not_yet_valid"


# ----------------------------------------------------------------- ER-01-4
def test_probe_er014_zkproof_generated_demonstration_never_verifies():
    from utils.zkproof import generate_zk_proof, verify_zk_proof
    proof, meets = generate_zk_proof(10, 5, salt="fixed")
    assert meets is True  # the proposition is true and the proof is well-formed ...
    assert verify_zk_proof(proof, 5, True) is False  # ... yet the verifier never yields an assurance result
    assert verify_zk_proof(proof, 5, False) is False
    assert verify_zk_proof(proof, 5.0, True) is False


def test_probe_er014_zkproof_selective_disclosure_demonstration_never_verifies():
    from utils.zkproof import create_selective_disclosure_proof, verify_selective_disclosure
    atts = [{"id": 1, "issuer": "alice"}, {"id": 2, "issuer": "bob"}]
    proof = create_selective_disclosure_proof(atts, [0], salt="fixed")
    assert verify_selective_disclosure(proof, proof["disclosed_attestations"]) is False
    assert verify_selective_disclosure(proof, atts) is False


def test_probe_er014_zkproof_assurance_path_refused_over_http():
    from fastapi.testclient import TestClient
    from main import app
    routes = ("/privacy/prove-threshold", "/privacy/verify-threshold", "/privacy/selective-disclosure")
    c = TestClient(app)
    for path in routes:
        r = c.post(path, json={"proof": "a" * 64, "threshold": 100, "verified": True})
        assert r.status_code == 501, path
        d = r.json()["detail"]
        assert d["assurance"] == "none" and d["reason"] == "demonstration_only", path


def test_probe_er014_zkproof_result_model_cannot_carry_assurance_for_rejections():
    # the only assurance value a verifier can attach besides 'none' is signature-only; no proof-based assurance level exists
    from models.verification import VerificationResult
    levels = VerificationResult.model_fields["assurance"].annotation.__args__
    assert set(levels) == {"issuer_signature_only", "none"}
