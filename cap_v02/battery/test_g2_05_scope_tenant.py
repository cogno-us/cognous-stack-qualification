"""G2.9: wrong tenant / scope. A store belongs to ONE (namespace, authority configuration). Another configuration (another tenant, consumer, operation, institution, domain, issuer,
key, clock, namespace, profile id or state binding) pointed at the same store is refused state_authority_mismatch BEFORE the host source or the Registry is touched; the store stays
byte-identical. Snapshot rotation (new pin, same anchor/grants) is NOT such a change."""
import copy

import pytest

import harness as H
from harness import AP, GRANT_ROW, ST, Kit, admit, base_config, dump, evidence, independent_authority_digest, issuer_entry, make_kit, refused_admit, sel, snapshot_doc, tree


def variant(kit, name, *, grant_row=None, namespace=None, cfg_edit=None, key=None, issuer_id=None, snapshot_doc_over=None, profile_id=None):
    """A second configuration in the SAME directory, same state reference (so the same store file), differing as requested; its snapshot is consistent with its own declarations."""
    row = grant_row or GRANT_ROW
    pub = key[0] if key else H.PK
    doc = snapshot_doc(issuers=[issuer_entry(pub=pub, grants=[row], issuer_id=issuer_id or H.ISSUER_ID)], **(snapshot_doc_over or {}))
    cfg = base_config(doc, snapshot_ref=f"snapshot-{name}.json", namespace=namespace or kit.config["state"]["namespace"], grant_row=row, profile_id=profile_id or "cap-profile-g2")
    if cfg_edit:
        cfg_edit(cfg)
    (kit.dir / f"snapshot-{name}.json").write_bytes(dump(doc))
    k2 = Kit(kit.dir, kit.dir / f"authority-{name}.json", kit.dir / f"snapshot-{name}.json", doc, cfg, "", kit.boot_dir)
    k2.rewrite_config()
    return k2


def sel_for(row, **kw):
    consumer, tenant, inst, dom, op = row
    return sel(1, stmt_over={"consumer_id": consumer, "scope": {"tenant": tenant, "institution": inst, "authority_domain": dom}, "operation": op}, **kw)


VARIANTS = {
    "other_tenant": dict(grant_row=[H.CONSUMER, "tenant-beta", H.INSTITUTION, H.DOMAIN, H.OPERATION]),
    "other_consumer": dict(grant_row=["consumer-other", H.TENANT_ID, H.INSTITUTION, H.DOMAIN, H.OPERATION]),
    "other_operation": dict(grant_row=[H.CONSUMER, H.TENANT_ID, H.INSTITUTION, H.DOMAIN, "refund-issue-other"]),
    "other_institution": dict(grant_row=[H.CONSUMER, H.TENANT_ID, "urn:other:institution", H.DOMAIN, H.OPERATION]),
    "other_domain": dict(grant_row=[H.CONSUMER, H.TENANT_ID, H.INSTITUTION, "other-domain", H.OPERATION]),
    "other_namespace": dict(namespace="cap-qual-g2-other"),
    "other_profile_id": dict(profile_id="cap-profile-other"),
    "other_issuer_id": dict(issuer_id="issuer-test-other"),
    "other_trust_anchor_key": dict(key=(H.ATT_PK, H.ATT_SK)),
    "other_clock": dict(cfg_edit=lambda c: c["clock"].update(as_of="2026-10-05T19:00:01Z")),
    "other_anchor_reference": dict(cfg_edit=lambda c: c["state"].update(anchor_reference="anchor-ref-OTHER")),
}


@pytest.mark.parametrize("name", list(VARIANTS))
@pytest.mark.row("G2.9.a", "another configuration (tenant, consumer, operation, institution, domain, namespace, profile id, issuer, trust-anchor key, clock, anchor reference) over the SAME store is refused state_authority_mismatch; store identical; host not read; Registry not reached")
def test_other_configuration_over_the_same_store_is_refused(tmp_path, spy, name):
    kit = make_kit(tmp_path)
    admit(kit, sel(1))
    spec = dict(VARIANTS[name])
    k2 = variant(kit, name, **spec)
    assert k2.state_path == kit.state_path
    row = spec.get("grant_row") or GRANT_ROW
    pre = kit.store_bytes()
    spy.reset()
    # a perfectly valid, correctly signed selection for THAT configuration
    s_other = sel_for(row, sk=(H.ATT_SK if name == "other_trust_anchor_key" else None), pub=(H.ATT_PK if name == "other_trust_anchor_key" else H.PK))
    host_before = tree(kit.dir)
    err = H.expect_refusal("state_authority_mismatch", admit, k2, s_other)
    assert spy.reached is False and spy.crypto == 0
    assert kit.store_bytes() == pre
    after = tree(kit.dir)
    assert {k: v for k, v in after.items() if not k.endswith(".lock")} == {k: v for k, v in host_before.items() if not k.endswith(".lock")}
    # factory path and a fresh process agree
    with pytest.raises(AP.AuthorityProfileRefusal) as exc:
        H.build(tmp_path, k2, s_other, scope=H.GovernedScope(row[0], row[1], H.ACTION_ID, row[4]))
    assert exc.value.code == "state_authority_mismatch"
    r = H.run_child("admit", config=str(k2.config_path), digest=k2.digest, record=s_other.record_text, selection=s_other.selection_text)
    assert r["out"]["code"] == "state_authority_mismatch" and kit.store_bytes() == pre
    # the ORIGINAL configuration is unaffected
    admit(kit, sel(1))


@pytest.mark.row("G2.9.b", "another configuration's digest really differs (independent recomputation) for every variant that is refused; snapshot-only changes do NOT change the authority digest")
def test_authority_digest_semantics_independent(tmp_path):
    kit = make_kit(tmp_path)
    base = independent_authority_digest(kit.config)
    assert base == kit.store()["authority_digest"] == ST.authority_digest(kit.load())
    for name, spec in VARIANTS.items():
        k2 = variant(kit, name, **spec)
        assert independent_authority_digest(k2.config) != base, name
        assert ST.authority_digest(k2.load()) == independent_authority_digest(k2.config), name
    # excluded members: snapshot.expected, snapshot.source, identities
    k3 = variant(kit, "rot", snapshot_doc_over=dict(version=7, valid_until="2026-10-15T00:00:00Z"), cfg_edit=lambda c: c["snapshot"]["source"].update(reference="elsewhere.json"))
    assert independent_authority_digest(k3.config) == base and ST.authority_digest(k3.load()) == base


@pytest.mark.row("G2.9.c", "rotation to a NEW snapshot source file and pin (same trust anchor) is accepted over the same store (not a reset, not a mismatch)")
def test_snapshot_source_and_pin_change_is_not_a_mismatch(tmp_path):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    admit(kit, s1)
    k2 = variant(kit, "rot", snapshot_doc_over=dict(version=5))
    admit(k2, s1)
    env = kit.store()
    assert env["state"]["snapshot"]["version"] == 5 and env["authority_digest"] == independent_authority_digest(kit.config)


@pytest.mark.row("G2.9.d", "a correctly signed selection for ANOTHER tenant/consumer/operation presented under the stored configuration is refused at the Registry (scope), nothing written")
@pytest.mark.parametrize("row", [[H.CONSUMER, "tenant-beta", H.INSTITUTION, H.DOMAIN, H.OPERATION], ["consumer-other", H.TENANT_ID, H.INSTITUTION, H.DOMAIN, H.OPERATION],
                                 [H.CONSUMER, H.TENANT_ID, H.INSTITUTION, H.DOMAIN, "refund-issue-other"]], ids=["tenant", "consumer", "operation"])
def test_selection_for_another_scope_is_refused(tmp_path, spy, row):
    kit = make_kit(tmp_path)
    admit(kit, sel(1))
    spy.reset()
    err = refused_admit(kit, sel_for(row), "registry_not_applied", spy, reached=True)
    assert spy.verdicts[-1].admitted is False
    assert kit.store()["generation"] == 1


@pytest.mark.row("G2.9.e", "two tenants have two independent stores: advancing tenant A to epoch 2 does not move tenant B's floor, and B still admits its own epoch 1")
def test_two_tenants_two_stores_are_independent(tmp_path):
    ka = make_kit(tmp_path / "a")
    rowb = [H.CONSUMER, "tenant-beta", H.INSTITUTION, H.DOMAIN, H.OPERATION]
    docb = snapshot_doc(issuers=[issuer_entry(grants=[rowb])])
    kb = make_kit(tmp_path / "b", doc=docb, config_edit=lambda c: c["expected_context"].update(tenant="tenant-beta"))
    sa1 = sel(1)
    sa2 = sel(2, prev=sa1, effective=H.EFFECTIVE_LONG)
    admit(ka, sa1); admit(ka, sa2)
    sb1 = sel_for(rowb)
    pre = kb.store_bytes()
    admit(kb, sb1)
    assert kb.store()["generation"] == 1 and ka.store()["generation"] == 2
    assert next(iter(kb.store()["state"]["rows"].values()))["epoch"] == 1 and next(iter(ka.store()["state"]["rows"].values()))["epoch"] == 2
    assert kb.store()["authority_digest"] != ka.store()["authority_digest"]
    evidence("g2-9e-two-tenants", {"A": ka.store()["authority_digest"], "B": kb.store()["authority_digest"]})


@pytest.mark.row("G2.9.f", "the persisted row key is the 7-field scope (selection_id, consumer, tenant, institution, domain, operation, family): the tenant is part of the stored floor identity")
def test_persisted_scope_key_carries_the_tenant(tmp_path):
    kit = make_kit(tmp_path)
    admit(kit, sel(1))
    key = next(iter(kit.store()["state"]["rows"]))
    assert H.TENANT_ID in key and H.CONSUMER in key and H.OPERATION in key and H.SELECTION_ID in key and "f4-control-plane-age-bounds" in key
    assert key == H.kitmod.scope_key({"selection_id": H.SELECTION_ID, "consumer_id": H.CONSUMER, "tenant": H.TENANT_ID, "institution": H.INSTITUTION,
                                      "authority_domain": H.DOMAIN, "operation": H.OPERATION, "family": H.F4})
