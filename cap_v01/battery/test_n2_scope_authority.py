"""N2: wrong scope / wrong authority. Consumer, tenant, operation mismatch; an issuer that holds no grant for the scope; wildcard grants; a withdrawn key. The scope guard of
the factory refuses before anything is read; authority defects of the signed material reach the REAL verifier, which refuses (registry_not_applied); no file changes."""
import copy

import pytest

import harness as H
from harness import (AP, ATT_PK, ATT_SK, KEY_ID, SCOPE, GovernedScope, Source, build, dump, expect_refusal, issuer_entry, make_kit, material, refused_build,  # noqa: F401
                     snapshot_doc, snapshot_files, spy)


@pytest.mark.parametrize("label,scope", [
    ("consumer", GovernedScope("consumer-other", H.TENANT_ID, H.ACTION_ID, H.OPERATION)),
    ("tenant", GovernedScope(H.CONSUMER, "tenant-other", H.ACTION_ID, H.OPERATION)),
    ("operation", GovernedScope(H.CONSUMER, H.TENANT_ID, H.ACTION_ID, "refund-issue-other")),
    ("all_three", GovernedScope("consumer-other", "tenant-other", H.ACTION_ID, "refund-issue-other")),
])
@pytest.mark.row("N2.a", "scope handed to the factory differs from the configured expected_context (consumer / tenant / operation): authority_config_scope_mismatch, the host source is never read, verifier not reached, no file changed")
def test_scope_differing_from_expected_context_is_refused_before_anything_is_read(tmp_path, spy, label, scope):
    kit = make_kit(tmp_path)
    host = Source(material())
    refused_build(tmp_path, kit, None, "authority_config_scope_mismatch", spy, reached=False, scope=scope, host_source=host)
    assert host.calls == 0


@pytest.mark.parametrize("label,stmt_over", [
    ("consumer", {"consumer_id": "consumer-other"}),
    ("tenant", {"scope": dict(H.STMT_SCOPE, tenant="tenant-other")}),
    ("institution", {"scope": dict(H.STMT_SCOPE, institution="urn:cognous:institution:other")}),
    ("authority_domain", {"scope": dict(H.STMT_SCOPE, authority_domain="domain-other")}),
    ("operation", {"operation": "refund-issue-other"}),
])
@pytest.mark.row("N2.b", "the SIGNED selection is for another consumer / tenant / institution / domain / operation (validly signed by the granted key): the real verifier is reached and refuses, registry_not_applied, no workflow, no file changed")
def test_validly_signed_selection_for_a_different_context_is_refused_by_the_verifier(tmp_path, spy, label, stmt_over):
    kit = make_kit(tmp_path)
    refused_build(tmp_path, kit, material(stmt_over=stmt_over), "registry_not_applied", spy, reached=True)
    (verdict,) = spy.verdicts
    assert verdict.admitted is False and verdict.code is not None
    assert {k for k, x in verdict.layers if x == "refuse"} & {"authority", "scope"}, verdict.layers


@pytest.mark.row("N2.c", "UNGRANTED issuer: the pinned snapshot (and the declarations, consistently) grant the signing issuer a DIFFERENT operation than the expected context: the verifier is reached and its authority layer refuses")
def test_issuer_without_a_grant_for_the_expected_context_is_refused(tmp_path, spy):
    other = [H.CONSUMER, H.TENANT_ID, H.INSTITUTION, H.DOMAIN, "refund-issue-other"]
    doc = snapshot_doc(issuers=[issuer_entry(grants=[other])])
    kit = make_kit(tmp_path, doc=doc)
    kit.load()  # the profile itself is well-formed: the defect is only visible to the verifier
    refused_build(tmp_path, kit, material(host_trust=H.trust_object(doc)), "registry_not_applied", spy, reached=True)
    assert H.layers_of(spy.verdicts[0])["authority"] == "refuse"


@pytest.mark.parametrize("field,idx,value", [("consumer", 0, "consumer-other"), ("tenant", 1, "tenant-other"), ("institution", 2, "urn:cognous:institution:other"),
                                              ("domain", 3, "domain-other")])
@pytest.mark.row("N2.d", "UNGRANTED issuer for each context member separately (grant differs in consumer / tenant / institution / domain): authority layer refuses")
def test_grant_that_differs_in_one_member_does_not_authorize(tmp_path, spy, field, idx, value):
    grant = list(H.GRANT_ROW)
    grant[idx] = value
    doc = snapshot_doc(issuers=[issuer_entry(grants=[grant])])
    kit = make_kit(tmp_path, doc=doc)
    refused_build(tmp_path, kit, material(host_trust=H.trust_object(doc)), "registry_not_applied", spy, reached=True)
    assert H.layers_of(spy.verdicts[0])["authority"] == "refuse"


@pytest.mark.row("N2.e", "two granted issuers, the selection is signed by the one WITHOUT the grant for the context (its key is trusted and declared): authority refused")
def test_signature_by_the_trusted_but_ungranted_issuer_is_refused(tmp_path, spy):
    other = [H.CONSUMER, H.TENANT_ID, H.INSTITUTION, H.DOMAIN, "refund-issue-other"]
    doc = snapshot_doc(issuers=[issuer_entry(), issuer_entry("key-test-2", "issuer-test-2", ATT_PK, grants=[other])])
    kit = make_kit(tmp_path, doc=doc)
    mat = material(host_trust=H.trust_object(doc), sk=ATT_SK, key_id="key-test-2", pub=ATT_PK)
    refused_build(tmp_path, kit, mat, "registry_not_applied", spy, reached=True)
    assert H.layers_of(spy.verdicts[0])["authority"] == "refuse"


@pytest.mark.parametrize("position", [0, 1, 2, 3, 4])
@pytest.mark.row("N2.f", "WILDCARD grant in the configuration (any of the five members is '*'): authority_config_malformed at load; the configuration cannot be activated")
def test_wildcard_grant_in_the_configuration_is_refused(tmp_path, position):
    kit = make_kit(tmp_path)
    cfg = copy.deepcopy(kit.config)
    key = ("consumer_id", "tenant", "institution", "authority_domain", "operation")[position]
    cfg["issuers"][0]["grants"][0][key] = "*"
    kit.rewrite_config(cfg)
    before = snapshot_files(tmp_path)
    expect_refusal("authority_config_malformed", kit.load, digest=kit.digest)
    assert snapshot_files(tmp_path) == before


@pytest.mark.parametrize("position", [0, 1, 2, 3, 4])
@pytest.mark.row("N2.g", "WILDCARD in expected_context: authority_config_malformed (the context to enforce must be exact)")
def test_wildcard_expected_context_is_refused(tmp_path, position):
    kit = make_kit(tmp_path)
    cfg = copy.deepcopy(kit.config)
    key = ("consumer_id", "tenant", "institution", "authority_domain", "operation")[position]
    cfg["expected_context"][key] = "*"
    kit.rewrite_config(cfg)
    expect_refusal("authority_config_malformed", kit.load, digest=kit.digest)


@pytest.mark.parametrize("token", ["*", "any", ""])
@pytest.mark.row("N2.h", "a pinned snapshot that grants a WILDCARD/blank scope token is not the declared authority: snapshot_pin_mismatch, verifier not reached (the declarations carry no wildcard, so the snapshot cannot equal them)")
def test_wildcard_grant_in_the_pinned_snapshot_is_refused(tmp_path, spy, token):
    wild = [H.CONSUMER, H.TENANT_ID, H.INSTITUTION, H.DOMAIN, token]
    doc = snapshot_doc(issuers=[issuer_entry(grants=[wild])])
    kit = make_kit(tmp_path)           # declarations and pin of the NON-wildcard snapshot
    kit.snapshot_path.write_bytes(dump(doc))
    refused_build(tmp_path, kit, material(), "snapshot_pin_mismatch", spy, reached=False)


@pytest.mark.row("N2.i", "a granted issuer whose key is REVOKED in the pinned snapshot (declared consistently): the verifier is reached and refuses on revocation")
def test_revoked_issuer_key_is_refused(tmp_path, spy):
    doc = snapshot_doc(revoked_key_ids=[KEY_ID])
    kit = make_kit(tmp_path, doc=doc)
    refused_build(tmp_path, kit, material(host_trust=H.trust_object(doc)), "registry_not_applied", spy, reached=True)
    assert "refuse" in dict(spy.verdicts[0].layers).values()


@pytest.mark.row("N2.j", "the SELECTION is revoked in the pinned snapshot (declared consistently): the verifier is reached and refuses")
def test_revoked_selection_is_refused(tmp_path, spy):
    doc = snapshot_doc(revoked_selections=[[H.SELECTION_ID, 1]])
    kit = make_kit(tmp_path, doc=doc)
    refused_build(tmp_path, kit, material(host_trust=H.trust_object(doc)), "registry_not_applied", spy, reached=True)
    assert H.layers_of(spy.verdicts[0])["revocation"] == "refuse"


@pytest.mark.row("N2.k", "a pinned snapshot that is EXPIRED at the profile clock: the verifier is reached and refuses on the trust_snapshot/time layer")
def test_expired_pinned_snapshot_is_refused(tmp_path, spy):
    doc = snapshot_doc(valid_until="2026-10-05T00:00:00Z")   # before AS_OF 2026-10-05T19:00:00Z
    kit = make_kit(tmp_path, doc=doc)
    refused_build(tmp_path, kit, material(host_trust=H.trust_object(doc)), "registry_not_applied", spy, reached=True)
    assert "refuse" in dict(spy.verdicts[0].layers).values()


@pytest.mark.row("N2.l", "the signed selection is outside its effective window at the profile clock: the verifier is reached and refuses on the time layer")
def test_selection_outside_its_effective_window_is_refused(tmp_path, spy):
    kit = make_kit(tmp_path)
    mat = material(stmt_over={"effective": {"valid_from": "2026-10-01T00:00:00Z", "valid_until": "2026-10-02T00:00:00Z"}})
    refused_build(tmp_path, kit, mat, "registry_not_applied", spy, reached=True)
    assert H.layers_of(spy.verdicts[0])["time"] == "refuse"
