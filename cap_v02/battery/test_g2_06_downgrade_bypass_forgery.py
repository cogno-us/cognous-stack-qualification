"""G2.10 downgrade / alternate-path bypass; G2.11 untrusted evidence cannot advance state; G2.12 review-fix behaviours (no stateless fallback, committed verdicts must be genuine and admitted,
signing key recorded, lock identity, clock read after the lock); G2.13 documented limits pinned as limits.

`none-g1` is the explicit stateless G1 choice and is NEVER a fallback."""
import collections
import copy
import dataclasses
import fcntl
import json
import os

import pytest

import harness as H
from harness import AP, ST, EFFECTIVE_LONG, SELECTION_ID, admit, base_config, build, dump, evidence, make_kit, refused_admit, sel, snapshot_doc, tree


# ------------------------------------------------------------------------------------------------------------------------------- G2.10 unknown / replaced backend
@pytest.mark.parametrize("bad", ["file-g3", "none", "", "FILE-G2", " file-g2", "file-g2 ", "memory", "sqlite", "file", "g2", None, 1, True, ["file-g2"], {"x": 1}])
@pytest.mark.row("G2.10.a", "an unknown or malformed state.backend in the CONFIGURATION is refused by the loader (authority_config_malformed): there is no default, no coercion and no stateless fallback")
def test_loader_rejects_unknown_backends(tmp_path, bad):
    kit = make_kit(tmp_path, bootstrap=False)
    cfg = copy.deepcopy(kit.config)
    cfg["state"]["backend"] = bad
    kit.rewrite_config(cfg)
    H.expect_refusal("authority_config_malformed", kit.load)


@pytest.mark.parametrize("bad", ["none-g1", "memory", "FILE-G2", "", None, "file-g3"])
@pytest.mark.row("G2.10.b", "a hand-REPLACED profile.state_backend (a file-g2 profile object with another backend) is refused authority_config_unprovisioned by EVERY entry point: wrapper, factory, open_transaction, read_state, bootstrap_state; never run stateless; store byte-identical")
def test_replaced_backend_is_refused_by_every_entry_point(tmp_path, spy, bad):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    admit(kit, s1)
    pre = kit.store_bytes()
    prof = dataclasses.replace(kit.load(), state_backend=bad)
    spy.reset()
    host = H.Source(s1, H.pinned_trust(kit))
    # wrapper: construction or call refuses, the host source is never read, the Registry never reached
    with pytest.raises(AP.AuthorityProfileRefusal) as exc:
        w = AP.PinnedSelectionSource(prof, host, H.ev.Ed25519Verifier(), expected_mode="synthetic", expected_config_digest=kit.digest)
        w()
    assert exc.value.code == "authority_config_unprovisioned" and host.calls == 0 and spy.reached is False
    with pytest.raises(AP.AuthorityProfileRefusal) as exc:
        build(tmp_path, kit, s1, profile=prof)
    assert exc.value.code == "authority_config_unprovisioned"
    H.expect_refusal("authority_config_unprovisioned", ST.open_transaction, prof, AP._now(kit.load()))
    H.expect_refusal("authority_config_unprovisioned", ST.read_state, prof)
    path = kit.write_bootstrap(kit.bootstrap_doc(bootstrap_id="bootstrap-0002"))
    H.expect_refusal("authority_config_unprovisioned", ST.bootstrap_state, prof, path, AP._now(kit.load()))
    assert kit.store_bytes() == pre and not (kit.dir / "freshness-state.json.consumed.bootstrap-0002").exists()
    assert host.calls == 0 and spy.reached is False


@pytest.mark.row("G2.10.c", "a profile whose state_path is blanked or whose config declaration is swapped (config says none-g1, field says file-g2 or vice versa) is refused; no stateless fallback")
def test_inconsistent_profile_declarations_are_refused(tmp_path, spy):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    admit(kit, s1)
    prof = kit.load()
    swapped_cfg = copy.deepcopy(dict(prof.config))
    swapped_cfg["state"] = dict(swapped_cfg["state"], backend="none-g1")
    for variant in (dataclasses.replace(prof, config=swapped_cfg), dataclasses.replace(prof, state_path="")):
        spy.reset()
        with pytest.raises(AP.AuthorityProfileRefusal) as exc:
            admit(kit, s1, profile=variant)
        assert exc.value.code == "authority_config_unprovisioned" and spy.reached is False


@pytest.mark.row("G2.10.d", "OPERATIONAL profiles cannot open a transaction or bootstrap: a complete operational configuration (file-g2, system clock, real-looking identities, digest supplied) still refuses authority_config_unprovisioned at the loader; a replaced mode refuses at every state entry point")
def test_operational_cannot_use_state(tmp_path):
    kit = make_kit(tmp_path, bootstrap=False)
    cfg = copy.deepcopy(kit.config)
    cfg.update(mode="operational")
    cfg["clock"] = {"kind": "system_utc"}
    cfg["state"] = {"backend": "file-g2", "namespace": "prod-ns", "reference": "prod-state.json", "anchor_reference": "anchor://prod-anchor-1"}
    cfg["identities"] = {"snapshot_publisher_ref": "id://publisher-1", "enforcing_operator_ref": "id://operator-1", "state_admin_ref": "id://state-admin-1"}
    digest = kit.rewrite_config(cfg)
    H.expect_refusal("authority_config_unprovisioned", AP.load_authority_profile, kit.config_path, expected_mode="operational", expected_config_digest=digest)
    H.expect_refusal("authority_config_unprovisioned", AP.load_authority_profile, kit.config_path, expected_mode="operational", expected_config_digest=None)
    H.expect_refusal("authority_config_mode_mismatch", AP.load_authority_profile, kit.config_path, expected_mode="synthetic", expected_config_digest=digest)
    kit.config["mode"] = "synthetic"; kit.config["clock"] = base_config()["clock"]; kit.config["state"] = base_config()["state"]; kit.config["identities"] = base_config()["identities"]
    kit.rewrite_config()
    kit.bootstrap()
    admit(kit, sel(1))
    prof = dataclasses.replace(kit.load(), mode="operational")
    now = AP._now(kit.load())
    H.expect_refusal("authority_config_unprovisioned", ST.open_transaction, prof, now)
    H.expect_refusal("authority_config_unprovisioned", ST.bootstrap_state, prof, kit.write_bootstrap(kit.bootstrap_doc(bootstrap_id="bootstrap-0002")), now)
    H.expect_refusal("authority_config_unprovisioned", admit, kit, sel(1), profile=prof)
    H.expect_refusal("authority_config_unprovisioned", build, tmp_path, kit, sel(1), profile=prof)
    assert not state_files_for(kit, "prod-state.json")


def state_files_for(kit, name):
    return [p for p in kit.dir.iterdir() if p.name.startswith(name)]


@pytest.mark.row("G2.10.e", "none-g1 is an EXPLICIT stateless choice: loads with no state path, creates no state/lock/ledger, never reads an existing file at state.reference, cannot open a transaction or bootstrap, G1 behaviour (older epoch not detected statelessly) is unchanged")
def test_none_g1_is_explicit_and_stateless(tmp_path, spy):
    kit = make_kit(tmp_path, bootstrap=False, backend="none-g1")
    prof = kit.load()
    assert prof.state_backend == "none-g1" and prof.state_path == ""
    # a decoy at state.reference must never be read or touched
    decoy = kit.dir / "freshness-state.json"
    decoy.write_bytes(b"decoy-not-a-store")
    s1 = sel(1)
    s2 = sel(2, prev=s1, effective=EFFECTIVE_LONG)
    admit(kit, s1); admit(kit, s2); admit(kit, s1)       # G1: stateless, an older epoch is NOT detected (that is the point of G2)
    assert decoy.read_bytes() == b"decoy-not-a-store"
    assert sorted(p.name for p in kit.dir.iterdir()) == ["authority.json", "freshness-state.json", "snapshot.json"]
    H.expect_refusal("authority_config_unprovisioned", ST.open_transaction, prof, AP._now(prof))
    H.expect_refusal("authority_config_unprovisioned", ST.bootstrap_state, prof, kit.write_bootstrap(kit.bootstrap_doc()), AP._now(prof))
    H.expect_refusal("authority_config_unprovisioned", ST.read_state, prof)
    # the real factory flow works exactly as in G1
    flow, p, host, _ = build(tmp_path, kit, s1)
    assert flow.decide(p, now=H.NOW).result == "authorized"


@pytest.mark.parametrize("path_kind", ["direct", "factory", "fresh_process"])
@pytest.mark.parametrize("damage", ["missing", "corrupt", "foreign"])
@pytest.mark.row("G2.10.f", "ALTERNATE PATHS cannot bypass: direct PinnedSelectionSource, the factory and a fresh process each refuse a missing / corrupt / foreign store; none returns material; the host source is not read")
def test_every_path_enforces_the_store(tmp_path, spy, path_kind, damage):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    admit(kit, s1)
    if damage == "missing":
        kit.state_path.unlink(); code = "state_missing"
    elif damage == "corrupt":
        kit.state_path.write_bytes(b"{broken"); code = "state_corrupt"
    else:
        env = kit.store(); env["namespace"] = "other"
        body = {k: v for k, v in env.items() if k != "state_digest"}
        kit.state_path.write_bytes(json.dumps(dict(body, state_digest=H.c.digest(body))).encode()); code = "state_authority_mismatch"
    pre = kit.state_path.read_bytes() if kit.state_path.exists() else None
    spy.reset()
    if path_kind == "direct":
        H.expect_refusal(code, admit, kit, s1)
    elif path_kind == "factory":
        H.expect_refusal(code, build, tmp_path, kit, s1)
    else:
        r = H.child_admit(kit, s1)
        assert r["out"]["ok"] is False and r["out"]["code"] == code
    assert spy.reached is False and (kit.state_path.read_bytes() if kit.state_path.exists() else None) == pre


@pytest.mark.row("G2.10.g", "the factory still forbids a caller-supplied selection_source/verifier for a file-g2 profile; unknown workflow kwargs cannot carry state; a host-supplied snapshot object (older, or with raised floors) is refused snapshot_pin_mismatch and writes nothing")
def test_factory_and_host_snapshot_bypasses(tmp_path, spy):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    admit(kit, s1)
    pre = kit.store_bytes()
    for kw in ({"selection_source": lambda: None}, {"verifier": object()}):
        H.expect_refusal("authority_factory_argument_refused", build, tmp_path, kit, s1, **kw)
    for kw in ({"last_accepted_snapshot": (9, "x")}, {"state": {}}, {"state_path": "elsewhere"}):
        with pytest.raises(TypeError):
            build(tmp_path, kit, s1, **kw)
    assert kit.store_bytes() == pre or kit.store()["generation"] == 1
    # host-supplied trust objects: raised floors / lower version / extra issuer
    spy.reset()
    other = snapshot_doc(min_epochs=[[SELECTION_ID, 50], [H.SELECTION_ID_B, 1]])
    trust = H.v.TrustSnapshot(other["snapshot_id"], other["version"], other["valid_until"], H.pinned_trust(kit).issuers, frozenset(), frozenset(), tuple((p[0], p[1]) for p in other["min_epochs"]))
    refused_admit(kit, s1, "snapshot_pin_mismatch", spy, reached=False, trust=trust)
    assert kit.store_bytes() == pre or kit.store()["generation"] == 1


# ------------------------------------------------------------------------------------------------------------------------------- G2.11 untrusted evidence
def _tamper_epoch(base, to=99):
    return dataclasses.replace(base, selection_text=base.selection_text.replace('"epoch": 1', f'"epoch": {to}'))


def forged_cases(s1):
    legit_hi = lambda **kw: sel(99, supersedes=s1.supersedes_ref(), effective=EFFECTIVE_LONG, **kw)
    return {
        "attacker_signed_real_key_id": (legit_hi(sk=H.ATT_SK), "registry_not_applied", True),
        "attacker_key_unknown_key_id": (legit_hi(sk=H.ATT_SK, key_id="key-attacker", pub=H.ATT_PK), "registry_not_applied", False),
        "signed_epoch1_then_patched_to_99": (_tamper_epoch(sel(1, effective=EFFECTIVE_LONG), 99), "registry_not_applied", False),
        "unsigned": (dataclasses.replace(legit_hi(), selection_text=json.dumps({**json.loads(legit_hi().selection_text), "signatures": []})), "registry_not_applied", False),
        "wrong_signing_domain": (_resign_v1(legit_hi()), "registry_not_applied", True),
        "real_key_other_tenant_scope": (legit_hi(stmt_over={"scope": {"tenant": "tenant-beta", "institution": H.INSTITUTION, "authority_domain": H.DOMAIN}}), "registry_not_applied", False),
        "real_key_other_operation": (legit_hi(stmt_over={"operation": "refund-issue-other"}), "registry_not_applied", False),
        "real_key_epoch99_no_supersedes": (sel(99, supersedes=None, effective=EFFECTIVE_LONG), "freshness_refused", False),
        "real_key_epoch99_wrong_digest": (sel(99, supersedes=dict(s1.supersedes_ref(), statement_digest="sha256:" + "9" * 64), effective=EFFECTIVE_LONG), "freshness_refused", False),
    }


def _resign_v1(selection):
    stmt = selection.stmt
    sig = H.base64.b64encode(H.nb.crypto_sign(H.s.V1_DOMAIN + H.c.canonical_bytes(stmt), H.SK)[:64]).decode()
    env = H.s.envelope(stmt, signature=sig, pub=H.PK, key_id=H.KEY_ID)
    return dataclasses.replace(selection, selection_text=json.dumps(env, sort_keys=True, ensure_ascii=True))


_NAMES = list(forged_cases(sel(1)))


@pytest.mark.parametrize("name", _NAMES)
@pytest.mark.row("G2.11.a", "UNTRUSTED EVIDENCE claiming epoch 99 (attacker-signed, unknown key, patched after signing, unsigned, wrong domain, other scope, no/incorrect supersedes) is refused; state bytes IDENTICAL; no write call; the Registry spy shows the verifier was reached and (for signature/scope cases) refused it")
def test_forged_epoch_99_cannot_advance_state(tmp_path, spy, wspy, name):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    admit(kit, s1)
    pre, n0 = kit.store_bytes(), wspy.n
    forged, code, crypto = forged_cases(s1)[name]
    spy.reset()
    err = refused_admit(kit, forged, code, spy, reached=True)
    assert kit.store_bytes() == pre and wspy.n == n0
    if code == "registry_not_applied":
        assert spy.verdicts[-1].admitted is False, "the REGISTRY refused the untrusted evidence"
    else:
        assert spy.verdicts[-1].admitted is True and err.refusal.registry_code in ("selection_supersession_invalid",)   # a trusted signer without a legitimate supersession: refused by the state
    if crypto:
        assert spy.crypto >= 1
    # the floor was NOT poisoned: the legitimate renewal still advances to epoch 2
    s2 = sel(2, prev=s1, effective=EFFECTIVE_LONG)
    admit(kit, s2)
    assert next(iter(kit.store()["state"]["rows"].values()))["epoch"] == 2
    evidence("g2-11-forged-" + name, {"code": err.code, "registry_code": err.refusal.registry_code, "registry_verdict": spy.verdicts[0].code if spy.verdicts else None})


@pytest.mark.row("G2.11.b", "a HOST-supplied snapshot that trusts the attacker key (so the epoch-99 signature would verify against it) is ignored: snapshot_pin_mismatch before the Registry is reached, state identical")
def test_host_snapshot_trusting_attacker_key_is_refused(tmp_path, spy, wspy):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    admit(kit, s1)
    pre = kit.store_bytes()
    atk_doc = snapshot_doc(issuers=[H.issuer_entry(pub=H.ATT_PK)])
    trust = H.v.TrustSnapshot(atk_doc["snapshot_id"], atk_doc["version"], atk_doc["valid_until"],
                              (H.v.IssuerEntry(H.KEY_ID, H.ISSUER_ID, "ed25519", H.ATT_PK, (H.v.AuthorityGrant(*H.GRANT_ROW),)),), frozenset(), frozenset(), tuple((p[0], p[1]) for p in atk_doc["min_epochs"]))
    forged = sel(99, supersedes=s1.supersedes_ref(), effective=EFFECTIVE_LONG, sk=H.ATT_SK)
    spy.reset()
    n0 = wspy.n
    refused_admit(kit, forged, "snapshot_pin_mismatch", spy, reached=False, trust=trust)
    assert kit.store_bytes() == pre and wspy.n == n0


@pytest.mark.row("G2.11.c", "EVERY refusal path across the battery writes nothing: refusal outcomes of a dozen different kinds leave the store byte-identical and the atomic writer uncalled")
def test_no_refusal_ever_calls_the_writer(tmp_path, spy, wspy):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    s2 = sel(2, prev=s1, effective=EFFECTIVE_LONG)
    admit(kit, s1); admit(kit, s2)
    pre, n0 = kit.store_bytes(), wspy.n
    cases = [(s1, None), (sel(2, prev=s1, status=100, effective=EFFECTIVE_LONG), None), (sel(1, selection_id=H.SELECTION_ID_B), None), (sel(9, supersedes=None, effective=EFFECTIVE_LONG), None),
             (sel(3, prev=s2, effective=EFFECTIVE_LONG, sk=H.ATT_SK), None), (s2, later_profile(kit, "2026-10-30T00:00:00Z"))]
    for selection, prof in cases:
        with pytest.raises(AP.AuthorityProfileRefusal):
            admit(kit, selection, profile=prof)
    assert kit.store_bytes() == pre and wspy.n == n0


def later_profile(kit, as_of):
    return H.later(kit.load(), as_of)


# ------------------------------------------------------------------------------------------------------------------------------- G2.12 review-fix behaviours
V = collections.namedtuple("V", "selection_id consumer_id scope operation family epoch selection_digest participation valid_from valid_until issuer_id record_id record_version record_digest trust_snapshot_fingerprint admitted epoch_floor_applied")


def genuine_verdict(kit, selection, profile=None):
    profile = profile or kit.load()
    trust, _ = AP.load_pinned_trust(profile)
    ctx = H.c.ExpectedContext(*profile.context)
    return H.vsel.verify_f4_selection_v2(selection.selection_text, selection.record_text, ctx, trust, H.ev.Ed25519Verifier(), AP._now(profile),
                                         min_trust_snapshot_version=profile.pin_version, last_accepted_snapshot=None), trust


@pytest.mark.row("G2.12.a", "Transaction.commit refuses a FORGED (non-Registry) verdict object: freshness_refused / verdict_not_admitted; no write; state identical")
def test_commit_refuses_a_forged_verdict(tmp_path, wspy):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    profile = kit.load()
    trust, fp = AP.load_pinned_trust(profile)
    forged = V(SELECTION_ID, H.CONSUMER, (H.TENANT_ID, H.INSTITUTION, H.DOMAIN), H.OPERATION, H.F4, 1, s1.digest, "required", "2026-10-01T00:00:00Z", "2026-10-06T00:00:00Z", H.ISSUER_ID,
               "f4-age-record", 1, "sha256:" + "2" * 64, fp, True, True)
    pre, n0 = kit.store_bytes(), wspy.n
    txn = ST.open_transaction(profile, AP._now(profile))
    try:
        H.expect_refusal("freshness_refused", txn.commit, forged, s1.selection_text, trust, registry_code="verdict_not_admitted")
    finally:
        txn.close()
    assert kit.store_bytes() == pre and wspy.n == n0


@pytest.mark.parametrize("field", ["admitted", "epoch_floor_applied"])
@pytest.mark.row("G2.12.b", "a GENUINE Registry verdict that is not admitted, or without an applied epoch floor, cannot be committed (freshness_refused / verdict_not_admitted)")
def test_commit_refuses_unadmitted_genuine_verdict(tmp_path, wspy, field):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    verdict, trust = genuine_verdict(kit, s1)
    assert verdict.admitted is True
    bad = dataclasses.replace(verdict, **{field: False}) if dataclasses.is_dataclass(verdict) else None
    assert bad is not None, "VerifiedSelectionV2 is expected to be a dataclass"
    pre = kit.store_bytes()
    profile = kit.load()
    txn = ST.open_transaction(profile, AP._now(profile))
    try:
        H.expect_refusal("freshness_refused", txn.commit, bad, s1.selection_text, trust, registry_code="verdict_not_admitted")
    finally:
        txn.close()
    assert kit.store_bytes() == pre


@pytest.mark.row("G2.12.c", "a genuine admitted verdict cannot be committed with DIFFERENT selection text (the epoch-99 text with the epoch-1 verdict): refused, state identical; and the correct pair commits (API-level positive)")
def test_commit_binds_verdict_to_the_selection_text(tmp_path, wspy):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    verdict, trust = genuine_verdict(kit, s1)
    other = sel(1, status=100)                      # a different, equally valid epoch-1 selection text
    pre = kit.store_bytes()
    profile = kit.load()
    txn = ST.open_transaction(profile, AP._now(profile))
    try:
        with pytest.raises(AP.AuthorityProfileRefusal) as exc:
            txn.commit(verdict, other.selection_text, trust)
        assert exc.value.code == "freshness_refused"
        assert kit.store_bytes() == pre
        txn.commit(verdict, s1.selection_text, trust)
    finally:
        txn.close()
    env = kit.store()
    assert env["generation"] == 1 and next(iter(env["state"]["rows"].values()))["selection_digest"] == s1.digest


@pytest.mark.row("G2.12.d", "the recorded issuer_key_id and issuer_id are those of the key that SIGNED the admitted selection (two issuers, second one signs)")
def test_recorded_issuer_key_is_the_signing_key(tmp_path):
    pk2, sk2 = H.nb.crypto_sign_seed_keypair(bytes(range(150, 182)))
    doc = snapshot_doc(issuers=[H.issuer_entry(), H.issuer_entry(key_id="key-test-2", issuer_id="issuer-test-2", pub=pk2)])
    kit = make_kit(tmp_path, doc=doc)
    admit(kit, sel(1, sk=sk2, key_id="key-test-2", pub=pk2))
    row = next(iter(kit.store()["state"]["rows"].values()))
    assert row["issuer_key_id"] == "key-test-2" and row["issuer_id"] == "issuer-test-2"
    assert kit.store()["state"]["log"][-1]["issuer_key_id"] == "key-test-2"


@pytest.mark.row("G2.12.e", "LOCK IDENTITY: a lock file replaced (unlinked and recreated) while the lock is being taken is refused state_lock_failed; nothing is read as admitted and nothing is written")
def test_lock_file_replaced_during_locking_is_refused(tmp_path, monkeypatch, spy, wspy):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    admit(kit, s1)
    pre, n0 = kit.store_bytes(), wspy.n
    real = fcntl.flock
    fired = {"n": 0}

    def flock(fd, op):
        out = real(fd, op)
        if op & fcntl.LOCK_EX and not fired["n"]:
            fired["n"] += 1
            os.unlink(kit.lock_path)
            os.close(os.open(kit.lock_path, os.O_CREAT | os.O_RDWR, 0o600))
        return out

    monkeypatch.setattr(ST.fcntl, "flock", flock)
    spy.reset()
    H.expect_refusal("state_lock_failed", admit, kit, s1)
    assert fired["n"] == 1 and spy.reached is False and kit.store_bytes() == pre and wspy.n == n0
    monkeypatch.undo()
    admit(kit, s1)                                  # a later call with an intact lock works


@pytest.mark.row("G2.12.f", "CLOCK AFTER LOCK: Transaction accepts a clock callable which is NOT evaluated at open and IS evaluated at commit while the lock is held")
def test_clock_is_read_after_the_lock(tmp_path):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    verdict, trust = genuine_verdict(kit, s1)
    profile = kit.load()
    seen = []

    def clock():
        probe = os.open(kit.lock_path, os.O_RDWR)
        try:
            try:
                fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
                held = False
                fcntl.flock(probe, fcntl.LOCK_UN)
            except OSError:
                held = True
        finally:
            os.close(probe)
        seen.append(held)
        return AP._now(profile)

    txn = ST.open_transaction(profile, clock)
    try:
        assert seen == [], "the clock must not be read before the lock/commit"
        txn.commit(verdict, s1.selection_text, trust)
    finally:
        txn.close()
    assert seen == [True]


# ------------------------------------------------------------------------------------------------------------------------------- G2.13 documented limits (pinned AS limits)
def _seal(env):
    body = {k: v for k, v in env.items() if k != "state_digest"}
    return dict(body, state_digest=H.c.digest(body))


@pytest.mark.row("G2.13.a", "DOCUMENTED LIMIT (pinned): a config edited to none-g1 WITHOUT expected_config_digest loads and serves statelessly (older epoch admitted, store untouched); WITH the owner digest the same edit is refused authority_config_digest_mismatch")
def test_limit_config_downgrade_needs_the_owner_digest(tmp_path):
    kit = make_kit(tmp_path)
    s1 = sel(1); s2 = sel(2, prev=s1, effective=EFFECTIVE_LONG)
    admit(kit, s1); admit(kit, s2)
    pre, owner_digest = kit.store_bytes(), kit.digest
    cfg = copy.deepcopy(kit.config); cfg["state"]["backend"] = "none-g1"
    kit.rewrite_config(cfg)
    H.expect_refusal("authority_config_digest_mismatch", AP.load_authority_profile, kit.config_path, expected_mode="synthetic", expected_config_digest=owner_digest)
    prof = AP.load_authority_profile(kit.config_path, expected_mode="synthetic")          # no digest supplied by the owner
    assert prof.state_backend == "none-g1"
    w = AP.PinnedSelectionSource(prof, H.Source(s1, H.pinned_trust(kit)), H.ev.Ed25519Verifier(), expected_mode="synthetic")
    assert w().selection_text == s1.selection_text          # NOT detected: the owner must supply expected_config_digest whenever the store matters
    assert kit.store_bytes() == pre
    evidence("g2-limit-config-downgrade", {"without_digest": "older epoch admitted statelessly", "with_digest": "authority_config_digest_mismatch"})


@pytest.mark.row("G2.13.b", "DOCUMENTED LIMIT (pinned): a newer pin that only REVOKES the selection is not recorded; re-pinning the older snapshot afterwards re-admits it until a selection is admitted under the newer pin")
def test_limit_revocation_only_pin_is_not_recorded(tmp_path):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    admit(kit, s1)
    kit.rotate(snapshot_doc(version=2, revoked_selections=[[SELECTION_ID, 1]]))
    H.expect_refusal("registry_not_applied", admit, kit, s1)
    kit.rotate(snapshot_doc(version=1))
    admit(kit, s1)                                       # re-admitted: the revocation was never persisted
    evidence("g2-limit-revocation-only-pin", {"result": "re-admitted after re-pinning older snapshot"})


@pytest.mark.row("G2.13.c", "DOCUMENTED LIMIT (pinned): there is no clock high-water: after an expiry refusal, moving the (system) clock BACK re-admits the time-expired selection")
def test_limit_clock_rollback_readmits_expired_selection(tmp_path):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    admit(kit, s1)
    late = later_profile(kit, "2026-10-08T00:00:00Z")
    H.expect_refusal("registry_not_applied", admit, kit, s1, profile=late)
    admit(kit, s1, profile=later_profile(kit, "2026-10-05T19:00:00Z"))      # clock rolled back: admitted again


@pytest.mark.row("G2.13.d", "DOCUMENTED LIMIT (pinned): a hand-created EMPTY store (no bootstrap, no ledger) is accepted as a valid fresh store")
def test_limit_hand_created_empty_store_is_accepted(tmp_path):
    kit = make_kit(tmp_path, bootstrap=False)
    env = _seal({"schema": "ocs-cap-freshness-state/1", "namespace": H.NAMESPACE, "authority_digest": H.independent_authority_digest(kit.config), "generation": 0, "parent_digest": None,
                 "bootstrap": {"bootstrap_id": "hand-made", "bootstrap_digest": "sha256:" + "0" * 64}, "state": H.kitmod.empty_state()})
    kit.state_path.write_bytes(json.dumps(env, sort_keys=True, separators=(",", ":")).encode())
    admit(kit, sel(1))
    assert not any(".consumed." in p.name for p in kit.dir.iterdir())
