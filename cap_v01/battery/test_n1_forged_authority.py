"""N1: forged or self-supplied authority. An attacker snapshot via host material, an altered pinned file, an extra issuer or grant: all refused `snapshot_pin_mismatch`
BEFORE the Registry verifier is reached (spy). A forged signature under the legitimate pin reaches the verifier and is refused by it. On every refusal no file changed."""
import copy

import pytest

import harness as H
from harness import (AP, ATT_PK, ATT_SK, KEY_ID, Source, build, dump, issuer_entry, make_kit, material, refused_build, snapshot_doc, snapshot_files, spy,  # noqa: F401
                     trust_object)


def attacker_doc(**over):
    """A complete, self-consistent snapshot the attacker controls: own key, own issuer, grants for exactly the victim scope."""
    return snapshot_doc(snapshot_id=H.SNAP_ID, issuers=[issuer_entry("key-attacker", "issuer-attacker", ATT_PK)], **over)


@pytest.mark.row("N1.a", "host supplies an ATTACKER snapshot and a statement signed by the attacker key: snapshot_pin_mismatch, verifier NOT reached, no crypto, no file changed")
def test_attacker_snapshot_via_host_material_with_attacker_signature(tmp_path, spy):
    kit = make_kit(tmp_path)
    mat = material(host_trust=trust_object(attacker_doc()), sk=ATT_SK, key_id="key-attacker", pub=ATT_PK)
    src = Source(mat)
    refused_build(tmp_path, kit, mat, "snapshot_pin_mismatch", spy, reached=False, host_source=src)
    assert src.calls == 1  # the host source was read once and its snapshot compared to the pin; nothing else


@pytest.mark.row("N1.b", "host supplies an attacker snapshot but LEGITIMATELY signed material: still snapshot_pin_mismatch, verifier not reached (host-supplied snapshot must equal the pin)")
def test_host_snapshot_must_equal_the_pin_even_with_a_valid_signature(tmp_path, spy):
    kit = make_kit(tmp_path)
    refused_build(tmp_path, kit, material(host_trust=trust_object(attacker_doc())), "snapshot_pin_mismatch", spy, reached=False)


@pytest.mark.parametrize("label,edit", [
    ("version_bumped", lambda d: d.update(version=2)),
    ("valid_until_extended", lambda d: d.update(valid_until="2099-01-01T00:00:00Z")),
    ("epoch_floor_added", lambda d: d.update(min_epochs=d["min_epochs"] + [["sel-other", 5]])),
    ("a_key_revoked", lambda d: d.update(revoked_key_ids=["key-unrelated"])),
    ("a_selection_revoked", lambda d: d.update(revoked_selections=[["sel-unrelated", 9]])),
    ("snapshot_id_changed", lambda d: d.update(snapshot_id="snap-cap-evil")),
])
@pytest.mark.row("N1.c", "host snapshot differs from the pin in ANY fingerprinted member (each parametrized): snapshot_pin_mismatch, verifier not reached")
def test_any_difference_of_the_host_snapshot_from_the_pin_is_refused(tmp_path, spy, label, edit):
    kit = make_kit(tmp_path)
    doc = copy.deepcopy(kit.doc)
    edit(doc)
    refused_build(tmp_path, kit, material(host_trust=trust_object(doc)), "snapshot_pin_mismatch", spy, reached=False)


@pytest.mark.parametrize("host", [None, {"snapshot_id": "x"}, "trust"])
@pytest.mark.row("N1.d", "host supplies no snapshot or a non-snapshot object: refused, verifier not reached (no fallback to host trust, no crash)")
def test_host_snapshot_that_is_not_a_snapshot_is_refused(tmp_path, spy, host):
    kit = make_kit(tmp_path)
    mat = H.SelectionMaterial(material().record_text, material().selection_text, host)
    refused_build(tmp_path, kit, mat, "snapshot_pin_mismatch", spy, reached=False)


@pytest.mark.parametrize("label,edit,declared_unchanged", [
    ("attacker_key_swapped_into_issuer", lambda d: d["issuers"][0].update(public_key=ATT_PK.hex()), True),
    ("extra_attacker_issuer", lambda d: d["issuers"].append(issuer_entry("key-attacker", "issuer-attacker", ATT_PK)), True),
    ("extra_grant_on_legit_issuer", lambda d: d["issuers"][0]["authority"].append([H.CONSUMER, H.TENANT_ID, H.INSTITUTION, H.DOMAIN, "another-operation"]), True),
    ("grant_removed_and_replaced", lambda d: d["issuers"][0].update(authority=[[H.CONSUMER, H.TENANT_ID, H.INSTITUTION, H.DOMAIN, "another-operation"]]), True),
    ("issuer_id_renamed", lambda d: d["issuers"][0].update(issuer_id="issuer-renamed"), True),
    ("min_epochs_stripped", lambda d: d.update(min_epochs=[]), True),
])
@pytest.mark.row("N1.e", "the PINNED snapshot file is altered on disk (key swapped, extra issuer, extra grant, renamed issuer, stripped floors): snapshot_pin_mismatch at construction, verifier not reached")
def test_altered_pinned_file_is_refused_at_construction(tmp_path, spy, label, edit, declared_unchanged):
    kit = make_kit(tmp_path)
    doc = copy.deepcopy(kit.doc)
    edit(doc)
    kit.snapshot_path.write_bytes(dump(doc))   # the host material stays the legitimate one; only the pinned file was tampered
    refused_build(tmp_path, kit, material(), "snapshot_pin_mismatch", spy, reached=False)


@pytest.mark.parametrize("label,edit", [
    ("extra_attacker_issuer", lambda d: d["issuers"].append(issuer_entry("key-attacker", "issuer-attacker", ATT_PK))),
    ("extra_grant_on_legit_issuer", lambda d: d["issuers"][0]["authority"].append([H.CONSUMER, H.TENANT_ID, H.INSTITUTION, H.DOMAIN, "another-operation"])),
    ("attacker_key_swapped_into_issuer", lambda d: d["issuers"][0].update(public_key=ATT_PK.hex())),
])
@pytest.mark.row("N1.f", "the attacker ALSO updates the pin fingerprint in the configuration to the altered file, but the declared issuers/keys/grants stay: snapshot_pin_mismatch (declarations must EQUAL the snapshot), verifier not reached")
def test_pin_updated_but_declarations_not_is_refused(tmp_path, spy, label, edit):
    kit = make_kit(tmp_path)
    doc = copy.deepcopy(kit.doc)
    edit(doc)
    kit.snapshot_path.write_bytes(dump(doc))
    cfg = copy.deepcopy(kit.config)
    cfg["snapshot"]["expected"]["fingerprint"] = H.fingerprint_of(doc)
    kit.rewrite_config(cfg)                    # owner digest recomputed here only to reach the declaration check; the digest test is N1.g
    refused_build(tmp_path, kit, material(), "snapshot_pin_mismatch", spy, reached=False)


@pytest.mark.row("N1.g", "the attacker rewrites the CONFIGURATION consistently (new issuer, grants, pin) but the owner-supplied digest is the original: authority_config_digest_mismatch at load, nothing read further")
def test_consistently_forged_configuration_is_refused_by_the_owner_digest(tmp_path, spy):
    kit = make_kit(tmp_path)
    original_digest = kit.digest
    doc = attacker_doc()
    forged = H.base_config(doc)
    kit.snapshot_path.write_bytes(dump(doc))
    kit.rewrite_config(forged)
    assert kit.digest != original_digest
    prepared = H.flow_kwargs(tmp_path)
    before = snapshot_files(tmp_path)
    with pytest.raises(AP.AuthorityProfileRefusal) as exc:
        build(tmp_path, kit, material(host_trust=trust_object(doc), sk=ATT_SK, key_id="key-attacker", pub=ATT_PK), digest=original_digest, prepared=prepared)
    assert exc.value.code == "authority_config_digest_mismatch"
    assert snapshot_files(tmp_path) == before and not spy.reached and spy.crypto == 0


@pytest.mark.row("N1.h", "snapshot reference redirected to an attacker-controlled file (absolute path) while the pin stays: snapshot_pin_mismatch, verifier not reached")
def test_redirected_snapshot_reference_is_refused(tmp_path, spy):
    kit = make_kit(tmp_path)
    evil = tmp_path / "evil" / "evil-snapshot.json"
    evil.parent.mkdir()
    evil.write_bytes(dump(attacker_doc()))
    cfg = copy.deepcopy(kit.config)
    cfg["snapshot"]["source"]["reference"] = str(evil)
    kit.rewrite_config(cfg)
    refused_build(tmp_path, kit, material(), "snapshot_pin_mismatch", spy, reached=False)


@pytest.mark.parametrize("variant", ["missing", "empty", "not_json", "wrong_shape"])
@pytest.mark.row("N1.i", "pinned snapshot file missing/empty/garbage/wrong-shaped: typed refusal from the unit's closed code set (never an untyped crash, never the host snapshot as a fallback), verifier not reached")
def test_unusable_pinned_file_is_a_typed_refusal(tmp_path, spy, variant):
    kit = make_kit(tmp_path)
    if variant == "missing":
        kit.snapshot_path.unlink()
    else:
        kit.snapshot_path.write_bytes({"empty": b"", "not_json": b"{nope", "wrong_shape": b'{"issuers": []}'}[variant])
    prepared = H.flow_kwargs(tmp_path)
    before = snapshot_files(tmp_path)
    with pytest.raises(AP.AuthorityProfileRefusal) as exc:
        build(tmp_path, kit, material(), prepared=prepared)
    assert exc.value.code in ("authority_config_missing", "snapshot_pin_mismatch"), exc.value.code
    assert exc.value.code in AP.CODES
    assert snapshot_files(tmp_path) == before and not spy.reached and spy.crypto == 0


@pytest.mark.row("N1.j", "forged SIGNATURE under the legitimate pin (attacker key signs, claims the legitimate key id): verifier IS reached, the authenticity layer refuses, registry_not_applied, no workflow, no file")
def test_forged_signature_under_the_legitimate_pin_reaches_the_verifier_and_is_refused_by_it(tmp_path, spy):
    kit = make_kit(tmp_path)
    exc = refused_build(tmp_path, kit, material(sk=ATT_SK), "registry_not_applied", spy, reached=True)
    (verdict,) = spy.verdicts
    assert verdict.admitted is False and H.layers_of(verdict)["authenticity"] == "refuse"
    assert exc.refusal.registry_code == verdict.code
    assert spy.verifier_types == [H.ev.Ed25519Verifier]


@pytest.mark.row("N1.k", "a signed selection whose bytes were altered after signing (tamper of the statement): the verifier is reached and refuses; no workflow")
def test_tampered_selection_bytes_are_refused_by_the_verifier(tmp_path, spy):
    kit = make_kit(tmp_path)
    mat = material()
    tampered = mat.selection_text.replace(f'"{H.OPERATION}"', '"refund-issue-other"', 1)
    assert tampered != mat.selection_text
    refused_build(tmp_path, kit, H.Material(mat.record_text, tampered, mat.host_trust), "registry_not_applied", spy, reached=True)
    assert spy.verdicts[0].admitted is False


@pytest.mark.row("N1.l", "DECISION-TIME tamper: a flow was built, then the pinned file gets an extra issuer; the next decide() is refused (selection_source_failed) with the typed cause snapshot_pin_mismatch on the wrapper, and no file changed")
def test_pinned_file_tampered_after_construction_refuses_the_decision(tmp_path, spy):
    kit = make_kit(tmp_path)
    flow, p, src, _prof = build(tmp_path, kit, material())
    doc = copy.deepcopy(kit.doc)
    doc["issuers"].append(issuer_entry("key-attacker", "issuer-attacker", ATT_PK))
    kit.snapshot_path.write_bytes(dump(doc))
    spy.reset()
    before = snapshot_files(tmp_path)
    with pytest.raises(Exception) as exc:
        flow.decide(p, now=H.NOW)
    assert "selection_source_failed" in str(exc.value)
    assert flow.cap_selection_source.last_refusal.code == "snapshot_pin_mismatch"
    assert snapshot_files(tmp_path) == before
    assert not spy.reached and spy.crypto == 0
    # restoring the pinned bytes restores service: the refusal is per call, not a latched or cached state
    kit.snapshot_path.write_bytes(dump(kit.doc))
    assert flow.decide(p, now=H.NOW).result == "authorized"
    assert flow.cap_selection_source.last_refusal is None


@pytest.mark.row("N1.m", "the unit does not cache the snapshot: after the pinned file is tampered, EVERY later read refuses even though an earlier read succeeded")
def test_no_cache_of_the_pinned_snapshot_between_reads(tmp_path, spy):
    kit = make_kit(tmp_path)
    flow, p, src, _prof = build(tmp_path, kit, material())
    wrapper = flow.cap_selection_source
    assert wrapper().record_text  # a successful read
    kit.snapshot_path.write_bytes(dump(dict(kit.doc, version=2)))
    for _ in range(3):
        with pytest.raises(AP.AuthorityProfileRefusal) as exc:
            wrapper()
        assert exc.value.code == "snapshot_pin_mismatch"
    assert wrapper.reads == 5  # 1 at construction + 1 success + 3 refused
