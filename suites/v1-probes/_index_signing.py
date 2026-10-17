"""Signing path for the Index link validation tests (shared by the V1 probes and the C03/C04 scenarios).

SPDX-License-Identifier: Apache-2.0

The fixed Index (POST /api/v1/evidence/links requires a BitRep v1 attestation, docs/BITREP_LINK_ATTESTATION.md)
rejects unsigned links, so tests that need links to be STORED must sign them. ``LinkSigner`` does that without
changing any product code and without committing key material:

* it detects the mode from the service itself (an unsigned link answered 401 ``attestation_required`` means
  "attestation required"); a service that predates the requirement keeps receiving unsigned links, exactly as before;
* when attestation is required it generates throwaway Ed25519 keys AT TEST TIME, writes a trust-registry snapshot
  (``BITREP_TRUST_REGISTRY``, operator-controlled in the product; here a per-test file) and signs each link with the
  Index-side profile ``index.link.v1``: subject = claim_id, issuer = attested_by, content_digest = sha256 of the compact
  sorted-key ASCII JSON of {claim_id, claim_id_2, evidence_id, relation_type, strength}. The digest is computed here from the
  documented profile (not by the product helper) so a product change to the profile is detected, not mirrored;
  the statement bytes signed are the vendored BitRep verifier's own ``canonical_bytes``;
* it builds the forged / unknown-issuer / revoked / expired / replayed attestations used as rejection assertions.

This file is intentionally identical in suites/v1-probes and suites/v1-scenarios (each suite directory is self-contained).
"""
from __future__ import annotations

import base64
import hashlib
import itertools
import json
import time
from pathlib import Path

AUDIENCE = "index:v1-validation"
LINK_STATEMENT_TYPE = "index.link.v1"
TRUST_ENV = "BITREP_TRUST_REGISTRY"
FORGED = "forged-attestor-absent-from-every-registry"
_counter = itertools.count(1)

# kind -> (expected HTTP status, expected detail.reason) at a service that verifies attestations
FORGERY_KINDS = {
    "unsigned_forged_identity": (401, "attestation_required"),
    "unregistered_issuer_own_key": (422, "unknown_key"),
    "registered_issuer_attacker_key": (422, "invalid_signature"),
    "unknown_key_id": (422, "unknown_key"),
    "revoked_key": (422, "key_revoked"),
    "expired_attestation": (422, "attestation_expired"),
    "wrong_audience": (422, "audience_mismatch"),
    "tampered_signature": (422, "invalid_signature"),
    "issuer_not_matching_attested_by": (422, "attestation_binding_mismatch"),
    "wrong_statement_type": (422, "attestation_binding_mismatch"),
}
# what the same kinds look like against a service with no attestation support: a bare unverifiable attested_by string
LEGACY_IDENTITY = {"unsigned_forged_identity": FORGED, "unregistered_issuer_own_key": "issuer:mallory",
                   "unknown_key_id": "issuer:alice#key:unknown", "revoked_key": "issuer:alice#key:1(revoked)"}


def reason(response):
    try:
        detail = response.json().get("detail")
    except Exception:
        return None
    return detail.get("reason") if isinstance(detail, dict) else None


def link_content_digest(fields):
    body = {"claim_id": fields["claim_id"], "claim_id_2": fields.get("claim_id_2"), "evidence_id": fields.get("evidence_id"),
            "relation_type": fields["relation_type"], "strength": float(fields["strength"])}
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _requires_attestation(client):
    c = client.post("/api/v1/claims/", json={"canonical_text": "attestation mode detection", "domains": ["probe"],
                                              "semantic_representation": {"subject": "a", "predicate": "b"}, "created_by": "probe_user"}).json()
    e = client.post("/api/v1/evidence/", json={"type": "experiment", "source_identifier": "doi:10.0/mode-detection", "submitted_by": "probe_user",
                                                "metadata": {"methodology": "double-blind RCT", "sample_size": 10, "uncertainty": 0.05}}).json()
    r = client.post("/api/v1/evidence/links", json={"claim_id": c["id"], "evidence_id": e["id"], "relation_type": "supports",
                                                     "strength": 1.0, "attested_by": "probe_attestor"})
    return r.status_code == 401 and reason(r) == "attestation_required"


class LinkSigner:
    """Build (and post) links for an Index client, signed when the service requires attestation."""

    def __init__(self, client, workdir, setenv, requires=None):
        self.client = client
        self.setenv = setenv
        self.path = Path(workdir) / f"trust-{next(_counter)}.json"
        self.requires = _requires_attestation(client) if requires is None else requires
        self._issuers = {}  # issuer -> (private key, key_id, registry-record overrides)
        if self.requires:
            try:
                from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey  # noqa: F401
                from app.bitrep_verify.models import SignedStatement  # noqa: F401
                from app.bitrep_verify.verification import canonical_bytes  # noqa: F401
            except ImportError as exc:  # a service that demands signatures but cannot be signed for is a harness defect, never a pass
                raise AssertionError(f"service requires attestation but the signing path is unavailable: {exc}")
            self._write()

    # ---- trust registry (test-time keys; never committed)
    def _write(self):
        now = int(time.time())
        keys = []
        for issuer, (priv, key_id, over) in self._issuers.items():
            rec = {"issuer": issuer, "key_id": key_id, "public_key": self._pub(priv), "valid_from": now - 10_000,
                   "valid_until": now + 100_000, "revoked_at": None}
            rec.update(over)
            keys.append(rec)
        doc = {"registry_version": "bitrep-trust/1", "audience": AUDIENCE, "published_at": now - 10_000, "valid_until": now + 100_000, "keys": keys}
        self.path.write_text(json.dumps(doc))
        self.setenv(TRUST_ENV, str(self.path))

    @staticmethod
    def _pub(priv):
        from cryptography.hazmat.primitives import serialization as s
        return base64.b64encode(priv.public_key().public_bytes(s.Encoding.Raw, s.PublicFormat.Raw)).decode()

    def enroll(self, issuer, key_id="key:1", **record_overrides):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        self._issuers[issuer] = (Ed25519PrivateKey.generate(), key_id, record_overrides)
        self._write()
        return self._issuers[issuer][0]

    def unavailable_registry(self):
        """Point the service at a missing snapshot (it must fail closed with 503, not accept)."""
        self.setenv(TRUST_ENV, str(self.path) + ".missing")

    # ---- signing
    def sign(self, fields, issuer, *, priv=None, key_id=None, attestation_id=None, audience=AUDIENCE, ttl=3600, issued_offset=-60,
             now=None, statement_type=LINK_STATEMENT_TYPE, attested_by=None):
        from app.bitrep_verify.models import SignedStatement
        from app.bitrep_verify.verification import canonical_bytes
        if priv is None:
            if issuer not in self._issuers:
                self.enroll(issuer)
            priv = self._issuers[issuer][0]
        key_id = key_id or (self._issuers[issuer][1] if issuer in self._issuers else "key:1")
        now = int(time.time()) if now is None else now
        st = {"protocol_version": "bitrep-attestation/1", "algorithm": "Ed25519", "attestation_id": attestation_id or f"att-{next(_counter)}",
              "issuer": issuer, "key_id": key_id, "subject": fields["claim_id"], "statement_type": statement_type, "audience": audience,
              "content_digest": link_content_digest(fields), "issued_at": now + issued_offset, "not_before": now + issued_offset, "expires_at": now + ttl}
        sig = base64.b64encode(priv.sign(canonical_bytes(SignedStatement(**st)))).decode()
        body = dict(fields)
        body["attested_by"] = attested_by or issuer
        body["attestation"] = {"statement": st, "signature": sig}
        return body

    @staticmethod
    def fields(claim_id, evidence_id, relation="supports", strength=1.0):
        return {"claim_id": claim_id, "evidence_id": evidence_id, "relation_type": relation, "strength": strength}

    def valid_body(self, claim_id, evidence_id, attested_by="probe_attestor", relation="supports", strength=1.0, attestation_id=None):
        """A link body the service must accept: signed when attestation is required, unsigned otherwise."""
        f = self.fields(claim_id, evidence_id, relation, strength)
        if not self.requires:
            return {**f, "attested_by": attested_by}
        return self.sign(f, attested_by, attestation_id=attestation_id)

    def post_link(self, claim_id, evidence_id, attested_by="probe_attestor", relation="supports", strength=1.0, attestation_id=None):
        return self.client.post("/api/v1/evidence/links", json=self.valid_body(claim_id, evidence_id, attested_by, relation, strength, attestation_id))

    def store_link(self, claim_id, evidence_id, attested_by="probe_attestor", relation="supports", strength=1.0, attestation_id=None):
        """post_link that FAILS (never skips) when the link was not stored: a probe about stored links proves nothing otherwise."""
        r = self.post_link(claim_id, evidence_id, attested_by, relation, strength, attestation_id)
        assert r.status_code in (200, 201), f"link was not stored (HTTP {r.status_code}, reason={reason(r)}): {r.text[:300]}"
        return r

    # ---- forgeries (rejection assertions)
    def forged_body(self, kind, claim_id, evidence_id):
        """A body for forgery ``kind``. Without attestation support the forgery is the bare unverifiable attested_by string."""
        f = self.fields(claim_id, evidence_id)
        if not self.requires:
            return {**f, "attested_by": LEGACY_IDENTITY.get(kind, FORGED)}
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        if kind == "unsigned_forged_identity":
            return {**f, "attested_by": FORGED}
        if kind == "unregistered_issuer_own_key":
            return self.sign(f, "issuer:mallory", priv=Ed25519PrivateKey.generate())
        if kind == "registered_issuer_attacker_key":
            self.enroll("issuer:alice")
            return self.sign(f, "issuer:alice", priv=Ed25519PrivateKey.generate())
        if kind == "unknown_key_id":
            self.enroll("issuer:alice")
            return self.sign(f, "issuer:alice", key_id="key:unknown")
        if kind == "revoked_key":
            self.enroll("issuer:revoked", revoked_at=int(time.time()) - 5)
            return self.sign(f, "issuer:revoked")
        if kind == "expired_attestation":
            return self.sign(f, "issuer:alice", now=int(time.time()) - 7200, ttl=60)
        if kind == "wrong_audience":
            return self.sign(f, "issuer:alice", audience="index:other-deployment")
        if kind == "tampered_signature":
            body = self.sign(f, "issuer:alice")
            sig = body["attestation"]["signature"]
            body["attestation"]["signature"] = ("A" if sig[0] != "A" else "B") + sig[1:]
            return body
        if kind == "issuer_not_matching_attested_by":
            return self.sign(f, "issuer:alice", attested_by="issuer:bob")
        if kind == "wrong_statement_type":
            return self.sign(f, "issuer:alice", statement_type="asserts")
        raise KeyError(kind)

    def stored_links(self, claim_id):
        return self.client.get(f"/api/v1/evidence/links/claim/{claim_id}").json()


# ---- scenario pin resolution (used by suites/v1-scenarios only; harmless here)
OLD_INDEX_PIN = "d5e45d275cb301d9684b543e93b05997991d1cf2"
REFROZEN_INDEX_PIN = "d17b8ac2b8445d385fbf51185a35914b2d8b835c"


def pin_sha(path):
    import subprocess
    return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()


def env_pin_sha(var="SCN_INDEX_DIR"):
    import os
    return pin_sha(os.environ[var])


def resolve_index_pin(helpers, var="SCN_INDEX_DIR"):
    """Verified-pristine Index checkout at EITHER the old pin (unsigned links, defects #23/#24 expected to FAIL) or the re-frozen
    Index (signed links required). Any other commit is a harness defect. Skips with the exact reason when the variable is unset."""
    import os
    import pytest
    value = os.environ.get(var)
    if not value:
        return helpers.external_pin(var, OLD_INDEX_PIN, "The Index"), OLD_INDEX_PIN  # skips: variable unset
    sha = pin_sha(value)
    if sha not in (OLD_INDEX_PIN, REFROZEN_INDEX_PIN):
        pytest.fail(f"{var} is at {sha}, which is neither the old Index pin ({OLD_INDEX_PIN}) nor the re-frozen Index ({REFROZEN_INDEX_PIN})")
    return helpers.external_pin(var, sha, "The Index"), sha
