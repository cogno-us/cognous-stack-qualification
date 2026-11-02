"""N3: mode and configuration. Mode mismatch in both directions (no fallback), omitted/invalid expected mode, operational placeholders / fixed_instant / missing owner digest
(operational ALWAYS ends authority_config_unprovisioned in G1), secret-shaped material, unknown / missing members, digest mismatch, malformed or unsupported input.
Loading is read-only: on every refusal the directory holding the configuration and snapshot is byte-identical."""
import copy
import json

import pytest

import harness as H
from harness import AP, SYNTH, build, dump, expect_refusal, make_kit, material, refused_build, snapshot_files, spy  # noqa: F401


def operational_cfg(kit, **edit):
    """An otherwise COMPLETE operational configuration: system clock, real-looking (non-placeholder) state and identity references."""
    cfg = copy.deepcopy(kit.config)
    cfg["mode"] = "operational"
    cfg["clock"] = {"kind": "system_utc"}
    cfg["state"] = {"backend": "postgres-ledger", "namespace": "prod-refunds-anti-rollback", "reference": "ledger-7731", "anchor_reference": "anchor-7731"}
    cfg["identities"] = {"snapshot_publisher_ref": "registry-publisher-A", "enforcing_operator_ref": "operator-team-B", "state_admin_ref": "dba-team-C"}
    for k, v in edit.items():
        cfg[k] = v
    return cfg


def read_only_load(kit, code, **kw):
    before = snapshot_files(kit.dir)
    err = expect_refusal(code, AP.load_authority_profile, kit.config_path, **kw)
    assert snapshot_files(kit.dir) == before
    return err


# ---------------------------------------------------------------------------------------------------------------------------------------------- mode
@pytest.mark.row("N3.a", "synthetic configuration, owner expects operational: authority_config_mode_mismatch (no upgrade, no fallback)")
def test_synthetic_config_with_operational_expectation_is_refused(tmp_path):
    kit = make_kit(tmp_path)
    read_only_load(kit, "authority_config_mode_mismatch", expected_mode="operational", expected_config_digest=kit.digest)


@pytest.mark.parametrize("digest", ["with_digest", "without_digest"])
@pytest.mark.row("N3.b", "operational configuration, owner expects synthetic: authority_config_mode_mismatch (no downgrade to synthetic, no fallback), with and without a digest")
def test_operational_config_with_synthetic_expectation_is_refused(tmp_path, digest):
    kit = make_kit(tmp_path)
    kit.rewrite_config(operational_cfg(kit))
    read_only_load(kit, "authority_config_mode_mismatch", expected_mode="synthetic", expected_config_digest=kit.digest if digest == "with_digest" else None)


@pytest.mark.parametrize("bad", [None, "", "Synthetic", "SYNTHETIC", "production", "operational ", 1, True, ["synthetic"], b"synthetic"])
@pytest.mark.row("N3.c", "owner-supplied expected_mode is None / empty / wrong case / unknown / not a string: authority_config_mode_mismatch (the mode is never inferred from the file)")
def test_invalid_expected_mode_is_refused(tmp_path, bad):
    kit = make_kit(tmp_path)
    read_only_load(kit, "authority_config_mode_mismatch", expected_mode=bad)


@pytest.mark.row("N3.d", "expected_mode OMITTED entirely: never a profile (typed mode_mismatch refusal or a TypeError for the missing process argument)")
def test_omitted_expected_mode_never_yields_a_profile(tmp_path):
    kit = make_kit(tmp_path)
    got = None
    with pytest.raises((AP.AuthorityProfileRefusal, TypeError)) as exc:
        got = AP.load_authority_profile(kit.config_path)
    assert got is None
    if isinstance(exc.value, AP.AuthorityProfileRefusal):
        assert exc.value.code == "authority_config_mode_mismatch"


@pytest.mark.row("N3.e", "factory called WITHOUT expected_mode: no workflow (TypeError or a typed refusal)")
def test_factory_without_expected_mode_builds_nothing(tmp_path):
    kit = make_kit(tmp_path)
    profile = kit.load()
    p, kw = H.flow_kwargs(tmp_path)
    got = None
    with pytest.raises((AP.AuthorityProfileRefusal, TypeError)):
        got = AP.governed_age_workflow(profile, host_source=H.Source(material()), scope=H.SCOPE, **kw)
    assert got is None


@pytest.mark.parametrize("expected", ["operational", None, "", "other"])
@pytest.mark.row("N3.f", "factory expected_mode differs from the loaded profile's mode: authority_config_mode_mismatch at construction, host source read at most once, verifier not reached, no file changed")
def test_factory_expected_mode_must_match_the_profile(tmp_path, spy, expected):
    kit = make_kit(tmp_path)
    profile = kit.load()
    prepared = H.flow_kwargs(tmp_path)
    p, kw = prepared
    before = snapshot_files(tmp_path)
    got = None
    with pytest.raises(AP.AuthorityProfileRefusal) as exc:
        got = AP.governed_age_workflow(profile, host_source=H.Source(material()), scope=H.SCOPE, expected_mode=expected, expected_config_digest=kit.digest, **kw)
    assert got is None and exc.value.code == "authority_config_mode_mismatch"
    assert snapshot_files(tmp_path) == before and not spy.reached and spy.crypto == 0


@pytest.mark.row("N3.g", "configured mode is neither synthetic nor operational: authority_config_malformed")
def test_unknown_configured_mode_is_refused(tmp_path):
    kit = make_kit(tmp_path)
    cfg = copy.deepcopy(kit.config)
    cfg["mode"] = "staging"
    kit.rewrite_config(cfg)
    read_only_load(kit, "authority_config_malformed", expected_mode="synthetic", expected_config_digest=kit.digest)


# ---------------------------------------------------------------------------------------------------------------------------------------------- operational fails closed
OPERATIONAL_VARIANTS = {
    "complete_and_valid": lambda kit: operational_cfg(kit),
    "placeholder_state_reference": lambda kit: operational_cfg(kit, state={"backend": "postgres-ledger", "namespace": "prod-x", "reference": "PLACEHOLDER", "anchor_reference": "anchor-1"}),
    "unselected_identity": lambda kit: operational_cfg(kit, identities={"snapshot_publisher_ref": "UNSELECTED", "enforcing_operator_ref": "op-1", "state_admin_ref": "dba-1"}),
    "synthetic_identities_in_operational": lambda kit: operational_cfg(kit, identities={"snapshot_publisher_ref": SYNTH, "enforcing_operator_ref": SYNTH, "state_admin_ref": SYNTH}),
    "todo_namespace": lambda kit: operational_cfg(kit, state={"backend": "postgres-ledger", "namespace": "TODO", "reference": "ledger-1", "anchor_reference": "anchor-1"}),
    "changeme_backend": lambda kit: operational_cfg(kit, state={"backend": "changeme", "namespace": "ns-1", "reference": "ledger-1", "anchor_reference": "anchor-1"}),
    "example_identity": lambda kit: operational_cfg(kit, identities={"snapshot_publisher_ref": "example", "enforcing_operator_ref": "op-1", "state_admin_ref": "dba-1"}),
    "fixed_instant_clock": lambda kit: operational_cfg(kit, clock={"kind": "fixed_instant", "as_of": H.AS_OF}),
    "blank_state_reference": lambda kit: operational_cfg(kit, state={"backend": "postgres-ledger", "namespace": "ns-1", "reference": "  ", "anchor_reference": "anchor-1"}),
    "blank_identity": lambda kit: operational_cfg(kit, identities={"snapshot_publisher_ref": " ", "enforcing_operator_ref": "op-1", "state_admin_ref": "dba-1"}),
}


@pytest.mark.parametrize("variant", sorted(OPERATIONAL_VARIANTS))
@pytest.mark.row("N3.h", "operational configuration with placeholders / UNSELECTED / blanks / fixed_instant / or fully complete: authority_config_unprovisioned in G1 (durable state is G2); no profile, no fallback to synthetic")
def test_operational_always_ends_unprovisioned(tmp_path, variant):
    kit = make_kit(tmp_path)
    kit.rewrite_config(OPERATIONAL_VARIANTS[variant](kit))
    read_only_load(kit, "authority_config_unprovisioned", expected_mode="operational", expected_config_digest=kit.digest)


@pytest.mark.row("N3.i", "operational configuration WITHOUT the owner-supplied digest: authority_config_unprovisioned (a complete profile is still refused with the digest; both ends the same)")
def test_operational_without_owner_digest_is_unprovisioned(tmp_path):
    kit = make_kit(tmp_path)
    kit.rewrite_config(operational_cfg(kit))
    read_only_load(kit, "authority_config_unprovisioned", expected_mode="operational", expected_config_digest=None)


@pytest.mark.row("N3.j", "operational with a WRONG owner digest: authority_config_digest_mismatch (the digest is checked before provisioning)")
def test_operational_with_wrong_owner_digest_is_a_digest_mismatch(tmp_path):
    kit = make_kit(tmp_path)
    kit.rewrite_config(operational_cfg(kit))
    read_only_load(kit, "authority_config_digest_mismatch", expected_mode="operational", expected_config_digest="sha256:" + "0" * 64)


@pytest.mark.row("N3.k", "a refused operational load leaves NO way to a workflow: nothing was read from the host source, the verifier was never reached, no Control Plane file was written")
def test_refused_operational_load_reaches_nothing(tmp_path, spy):
    kit = make_kit(tmp_path)
    kit.rewrite_config(operational_cfg(kit))
    host = H.Source(material())
    before = snapshot_files(tmp_path)
    with pytest.raises(AP.AuthorityProfileRefusal) as exc:
        build(tmp_path, kit, None, mode="operational", host_source=host)
    assert exc.value.code == "authority_config_unprovisioned"
    assert host.calls == 0 and not spy.reached and spy.crypto == 0
    assert set(snapshot_files(tmp_path)) - set(before) <= {"destination.json", "destination.json.lock", "run.json", "run.json.lock"}  # only the harness's own empty stores
    assert not json.loads((tmp_path / "run.json").read_text()).get("decisions") if (tmp_path / "run.json").exists() else True


@pytest.mark.row("N3.l", "an AuthorityProfile built DIRECTLY (dataclasses.replace(profile, mode='operational')) bypasses load_authority_profile; operational must still never activate: factory, wrapper and replay_trust_kwargs refuse authority_config_unprovisioned (found at ed8e3e7a as F-1, fixed at ce3c229a)")
def test_handbuilt_operational_profile_cannot_activate(tmp_path, spy):
    import dataclasses
    kit = make_kit(tmp_path)
    profile = dataclasses.replace(kit.load(), mode="operational")
    p, kw = H.flow_kwargs(tmp_path)
    before = snapshot_files(tmp_path)
    host = H.Source(material())
    with pytest.raises(AP.AuthorityProfileRefusal) as exc:
        AP.governed_age_workflow(profile, host_source=host, scope=H.SCOPE, expected_mode="operational", **kw)
    assert exc.value.code == "authority_config_unprovisioned"
    with pytest.raises(AP.AuthorityProfileRefusal) as exc:
        AP.PinnedSelectionSource(profile, host, H.ev.Ed25519Verifier(), expected_mode="operational")()
    assert exc.value.code == "authority_config_unprovisioned"
    with pytest.raises(AP.AuthorityProfileRefusal) as exc:
        AP.replay_trust_kwargs(profile)
    assert exc.value.code == "authority_config_unprovisioned"
    assert host.calls == 0 and not spy.reached and spy.crypto == 0 and snapshot_files(tmp_path) == before


# ---------------------------------------------------------------------------------------------------------------------------------------------- secret material
SECRET_EDITS = {
    "member_private_key": lambda c: c.update(private_key="x"),
    "member_secret": lambda c: c["trust_anchor"].update(secret="x"),
    "member_seed": lambda c: c["trust_anchor"]["keys"][0].update(seed="x"),
    "member_password": lambda c: c["state"].update(password="x"),
    "member_signing_key": lambda c: c["issuers"][0].update(signing_key="x"),
    "member_credentials": lambda c: c["identities"].update(credentials="x"),
    "member_in_grant": lambda c: c["issuers"][0]["grants"][0].update(secret_grant="x"),
    "value_pem_private_key": lambda c: c["state"].update(reference="-----BEGIN PRIVATE KEY-----\nAAAA\n-----END PRIVATE KEY-----"),
    "value_pem_openssh": lambda c: c["state"].update(namespace="-----BEGIN OPENSSH PRIVATE KEY-----"),
    "value_bare_hex_32_bytes": lambda c: c["state"].update(reference="a" * 64),
    "value_bare_hex_64_bytes": lambda c: c["state"].update(reference="0123456789abcdef" * 8),
    "value_base64_32_bytes": lambda c: c["state"].update(anchor_reference="A" * 43 + "="),
    "value_base64_64_bytes": lambda c: c["identities"].update(state_admin_ref="B" * 86 + "=="),
    "value_in_list_element": lambda c: c["trust_anchor"]["keys"].append({"key_id": "k2", "public_key_sha256": "c" * 64}),
}


@pytest.mark.parametrize("mode", ["synthetic", "operational"])
@pytest.mark.parametrize("variant", sorted(SECRET_EDITS))
@pytest.mark.row("N3.m", "secret-shaped member names (private/secret/seed/password/signing/credential) and key-shaped VALUES (PEM, bare hex, base64 key) in either mode: authority_config_secret_material, nothing activates")
def test_secret_shaped_material_is_refused_in_both_modes(tmp_path, mode, variant):
    kit = make_kit(tmp_path)
    cfg = operational_cfg(kit) if mode == "operational" else copy.deepcopy(kit.config)
    SECRET_EDITS[variant](cfg)
    kit.rewrite_config(cfg)
    read_only_load(kit, "authority_config_secret_material", expected_mode=mode, expected_config_digest=kit.digest)


@pytest.mark.row("N3.n", "the public key itself (hex) written into the configuration instead of its sha256: refused (secret_material or malformed) - the configuration holds only key ids and sha256 of public key bytes")
def test_raw_public_key_in_the_configuration_is_refused(tmp_path):
    kit = make_kit(tmp_path)
    cfg = copy.deepcopy(kit.config)
    cfg["trust_anchor"]["keys"][0] = {"key_id": H.KEY_ID, "public_key": H.PK.hex()}
    kit.rewrite_config(cfg)
    err = None
    with pytest.raises(AP.AuthorityProfileRefusal) as exc:
        kit.load(digest=kit.digest)
    assert exc.value.code in ("authority_config_secret_material", "authority_config_malformed")


@pytest.mark.row("N3.o", "the public key hash in the configuration does not match the key in the pinned snapshot: snapshot_pin_mismatch, verifier not reached (declared key digest must EQUAL the snapshot key)")
def test_declared_public_key_digest_must_equal_the_snapshot_key(tmp_path, spy):
    kit = make_kit(tmp_path)
    cfg = copy.deepcopy(kit.config)
    cfg["trust_anchor"]["keys"][0]["public_key_sha256"] = H.sha_tag(H.ATT_PK)
    kit.rewrite_config(cfg)
    refused_build(tmp_path, kit, material(), "snapshot_pin_mismatch", spy, reached=False)


# ---------------------------------------------------------------------------------------------------------------------------------------------- closed schema
def add(path, value):
    def edit(c):
        node = c
        for step in path[:-1]:
            node = node[step]
        node[path[-1]] = value
    return edit


def drop(path):
    def edit(c):
        node = c
        for step in path[:-1]:
            node = node[step]
        del node[path[-1]]
    return edit


SCHEMA_EDITS = {
    "unknown_top_level_member": add(("extra",), 1),
    "unknown_verifier_member": add(("verifier", "extra"), 1),
    "unknown_anchor_member": add(("trust_anchor", "extra"), 1),
    "unknown_key_member": add(("trust_anchor", "keys", 0, "extra"), 1),
    "unknown_issuer_member": add(("issuers", 0, "extra"), 1),
    "unknown_grant_member": add(("issuers", 0, "grants", 0, "extra"), 1),
    "unknown_context_member": add(("expected_context", "extra"), "x"),
    "unknown_snapshot_member": add(("snapshot", "extra"), 1),
    "unknown_snapshot_source_member": add(("snapshot", "source", "extra"), 1),
    "unknown_expected_member": add(("snapshot", "expected", "extra"), 1),
    "unknown_clock_member": add(("clock", "extra"), 1),
    "unknown_state_member": add(("state", "extra"), "x"),
    "unknown_identity_member": add(("identities", "extra"), "x"),
    "missing_id": drop(("id",)),
    "missing_mode": drop(("mode",)),
    "missing_verifier": drop(("verifier",)),
    "missing_trust_anchor": drop(("trust_anchor",)),
    "missing_issuers": drop(("issuers",)),
    "missing_expected_context": drop(("expected_context",)),
    "missing_snapshot": drop(("snapshot",)),
    "missing_clock": drop(("clock",)),
    "missing_state": drop(("state",)),
    "missing_identities": drop(("identities",)),
    "empty_issuers": lambda c: c.update(issuers=[]),
    "empty_keys": lambda c: c["trust_anchor"].update(keys=[]),
    "empty_grants": lambda c: c["issuers"][0].update(grants=[]),
    "issuer_key_not_in_anchor": lambda c: c["issuers"][0].update(key_id="key-unknown"),
    "duplicate_grant": lambda c: c["issuers"][0]["grants"].append(copy.deepcopy(c["issuers"][0]["grants"][0])),
    "key_shared_by_two_issuers": lambda c: c["issuers"].append(dict(copy.deepcopy(c["issuers"][0]), issuer_id="issuer-two")),
    "wrong_verifier_contract": lambda c: c["verifier"].update(contract="r08-v1"),
    "wrong_verifier_family": lambda c: c["verifier"].update(family="f5"),
    "wrong_algorithm": lambda c: c["trust_anchor"].update(algorithm="rsa"),
    "key_digest_not_sha256_tag": lambda c: c["trust_anchor"]["keys"][0].update(public_key_sha256="md5:abc"),
    "pin_fingerprint_not_sha256_tag": lambda c: c["snapshot"]["expected"].update(fingerprint="abc"),
    "pin_version_zero": lambda c: c["snapshot"]["expected"].update(version=0),
    "pin_version_bool": lambda c: c["snapshot"]["expected"].update(version=True),
    "pin_version_string": lambda c: c["snapshot"]["expected"].update(version="1"),
    "snapshot_source_not_file": lambda c: c["snapshot"]["source"].update(kind="url"),
    "snapshot_source_empty": lambda c: c["snapshot"]["source"].update(reference=""),
    "clock_unknown_kind": lambda c: c["clock"].update(kind="wall"),
    "clock_fixed_without_as_of": lambda c: c.update(clock={"kind": "fixed_instant"}),
    "clock_system_with_as_of": lambda c: c.update(clock={"kind": "system_utc", "as_of": H.AS_OF}),
    "clock_as_of_not_utc": lambda c: c.update(clock={"kind": "fixed_instant", "as_of": "2026-10-05 19:00:00"}),
    "token_with_space": lambda c: c.update(id="has space"),
    "id_not_string": lambda c: c.update(id=7),
}


@pytest.mark.parametrize("variant", sorted(SCHEMA_EDITS))
@pytest.mark.row("N3.p", "closed strict schema: unknown members at every level, missing members, empty lists, wrong types/values: authority_config_malformed; the owner digest is the digest of the (malformed) file so nothing else can be the cause")
def test_closed_schema_refuses_unknown_missing_and_malformed_members(tmp_path, variant):
    kit = make_kit(tmp_path)
    cfg = copy.deepcopy(kit.config)
    SCHEMA_EDITS[variant](cfg)
    kit.rewrite_config(cfg)
    read_only_load(kit, "authority_config_malformed", expected_mode="synthetic", expected_config_digest=kit.digest)


# ---------------------------------------------------------------------------------------------------------------------------------------------- digest, version, file
@pytest.mark.parametrize("digest", ["sha256:" + "0" * 64, "sha256:" + "A" * 64, "", "garbage", 7, b"x"])
@pytest.mark.row("N3.q", "owner-supplied configuration digest differs from the file's sha256 (or is not a digest): authority_config_digest_mismatch")
def test_owner_digest_mismatch_is_refused(tmp_path, digest):
    kit = make_kit(tmp_path)
    read_only_load(kit, "authority_config_digest_mismatch", expected_mode="synthetic", expected_config_digest=digest)


@pytest.mark.row("N3.r", "the configuration file is altered AFTER the owner digest was fixed (one byte): authority_config_digest_mismatch")
def test_configuration_altered_after_digest_was_fixed_is_refused(tmp_path):
    kit = make_kit(tmp_path)
    good = kit.digest
    kit.config_path.write_bytes(kit.config_path.read_bytes().replace(b"cap-profile-1", b"cap-profile-2"))
    read_only_load(kit, "authority_config_digest_mismatch", expected_mode="synthetic", expected_config_digest=good)


@pytest.mark.row("N3.s", "a profile loaded under one digest and handed to the factory with a different owner digest: authority_config_digest_mismatch at construction, verifier not reached, no file changed")
def test_factory_owner_digest_must_equal_the_profile_digest(tmp_path, spy):
    kit = make_kit(tmp_path)
    refused_build(tmp_path, kit, material(), "authority_config_digest_mismatch", spy, reached=False, digest="sha256:" + "1" * 64)


@pytest.mark.parametrize("version", ["ocs-authority-profile/0.2", "ocs-authority-profile/1.0", "ocs-authority-profile/0.1 ", "OCS-AUTHORITY-PROFILE/0.1", "", 1, None])
@pytest.mark.row("N3.t", "unsupported or non-exact configuration version: authority_config_version_unsupported")
def test_unsupported_version_is_refused(tmp_path, version):
    kit = make_kit(tmp_path)
    cfg = copy.deepcopy(kit.config)
    cfg["version"] = version
    kit.rewrite_config(cfg)
    read_only_load(kit, "authority_config_version_unsupported", expected_mode="synthetic", expected_config_digest=kit.digest)


@pytest.mark.row("N3.u", "configuration without a version member: refused as a typed config error (malformed or version_unsupported), never a profile")
def test_missing_version_is_refused(tmp_path):
    kit = make_kit(tmp_path)
    cfg = copy.deepcopy(kit.config)
    del cfg["version"]
    kit.rewrite_config(cfg)
    got = None
    with pytest.raises(AP.AuthorityProfileRefusal) as exc:
        got = AP.load_authority_profile(kit.config_path, expected_mode="synthetic", expected_config_digest=kit.digest)
    assert got is None and exc.value.code in ("authority_config_malformed", "authority_config_version_unsupported")


@pytest.mark.parametrize("variant", ["nonexistent", "directory", "none_path"])
@pytest.mark.row("N3.v", "configuration path missing / a directory / None: authority_config_missing")
def test_missing_configuration_is_refused(tmp_path, variant):
    path = {"nonexistent": tmp_path / "nope.json", "directory": tmp_path, "none_path": None}[variant]
    expect_refusal("authority_config_missing", AP.load_authority_profile, path, expected_mode="synthetic")


RAW = {
    "empty": b"",
    "not_json": b"{not json",
    "trailing_garbage": b'{"version": "ocs-authority-profile/0.1"} x',
    "top_level_list": b"[]",
    "top_level_string": b'"ocs-authority-profile/0.1"',
    "invalid_utf8": b"\xff\xfe{}",
    "nan_literal": b'{"version": NaN}',
    "infinity_literal": b'{"version": Infinity}',
    "duplicate_key": b'{"version": "ocs-authority-profile/0.1", "version": "ocs-authority-profile/0.1"}',
    "oversized": b'{"version": "ocs-authority-profile/0.1", "pad": "' + b"x" * 70000 + b'"}',
}


@pytest.mark.parametrize("variant", sorted(RAW))
@pytest.mark.row("N3.w", "not strict JSON (empty, trailing bytes, NaN/Infinity, invalid UTF-8, duplicate keys, non-object, oversized): authority_config_malformed")
def test_non_strict_json_is_refused(tmp_path, variant):
    kit = make_kit(tmp_path)
    kit.rewrite_config(raw=RAW[variant])
    read_only_load(kit, "authority_config_malformed", expected_mode="synthetic", expected_config_digest=kit.digest)


@pytest.mark.row("N3.x", "duplicate JSON member that would flip the mode (first operational, last synthetic): refused as malformed, never resolved last-wins")
def test_duplicate_mode_member_cannot_flip_the_mode(tmp_path):
    kit = make_kit(tmp_path)
    text = kit.config_path.read_text().replace('"mode": "synthetic"', '"mode": "operational", "mode": "synthetic"')
    assert text.count('"mode"') == 2
    kit.rewrite_config(raw=text.encode())
    read_only_load(kit, "authority_config_malformed", expected_mode="synthetic", expected_config_digest=kit.digest)
