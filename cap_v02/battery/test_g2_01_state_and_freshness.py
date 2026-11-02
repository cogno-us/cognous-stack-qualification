"""G2.1-G2.5: a valid selection is persisted; a legitimate renewal advances; a lower epoch, an older snapshot, an expired or a revoked selection are refused WITHOUT any write.

Real components throughout: the Registry core (11 layers, exact Ed25519Verifier, PyNaCl), the unchanged Registry conformance kit, a REAL state file. Refusal tests compare the entire
authorization directory (configuration, snapshot, store, ledger) byte-for-byte before and after; the spy proves WHICH layer refused (Registry verdict vs. state)."""
import json
import os
import stat

import pytest

import harness as H
from harness import (AP, ST, EFFECTIVE_LONG, SELECTION_ID, SELECTION_ID_B, Source, admit, build, evidence, independent_authority_digest, later, make_kit, refused_admit, sel,
                     snapshot_doc, spy, tree, wspy)  # noqa: F401


def verify_envelope(kit, env):
    """Independent integrity checks of a persisted envelope (contract section 5)."""
    assert list(sorted(env)) == sorted(["schema", "namespace", "authority_digest", "generation", "parent_digest", "bootstrap", "state", "state_digest"])
    assert env["schema"] == "ocs-cap-freshness-state/1"
    assert env["namespace"] == kit.config["state"]["namespace"]
    assert env["authority_digest"] == independent_authority_digest(kit.config)
    assert env["state_digest"] == H.c.digest({k: v for k, v in env.items() if k != "state_digest"})
    assert env["state"]["schema"] == "ocs-conformance-state/1"
    assert H.kitmod.verify_state(env["state"]) is None


def row_of(env):
    rows = env["state"]["rows"]
    assert len(rows) == 1, list(rows)
    return next(iter(rows.values()))


# =========================================================================================================================== G2.1 valid selection with persisted state
@pytest.mark.row("G2.1.a", "bootstrap creates generation 0 with an EMPTY kit state; the envelope is the closed ocs-cap-freshness-state/1 schema; authority_digest equals the independent recomputation")
def test_bootstrap_store_is_generation_zero_empty_and_closed(tmp_path):
    kit = make_kit(tmp_path)
    env = kit.store()
    verify_envelope(kit, env)
    assert env["generation"] == 0 and env["parent_digest"] is None
    assert env["state"] == H.kitmod.empty_state()
    assert env["state"]["rows"] == {} and env["state"]["floors"]["high_water"] == {}
    assert env["bootstrap"]["bootstrap_id"] == "bootstrap-0001"
    assert stat.S_IMODE(os.stat(kit.state_path).st_mode) == 0o600
    assert kit.lock_path.exists() and kit.lock_path.name == "freshness-state.json.lock"


@pytest.mark.row("G2.1.b", "a valid selection through the FACTORY authorizes and executes, and the persisted state records it: generation 1, active row epoch 1 with the selection digest, snapshot version+fingerprint of the pin, parent chain")
def test_valid_selection_is_persisted_after_a_real_authorization(tmp_path, spy, wspy):
    kit = make_kit(tmp_path)
    before = kit.store()
    n0 = wspy.n
    assert n0 == 2      # bootstrap wrote the consumed ledger and the store
    s1 = sel(1)
    flow, p, host, profile = build(tmp_path, kit, s1)
    d = flow.decide(p, now=H.NOW)
    assert d.result == "authorized", d.reasons
    ex = flow.execute(p, flow.records.decision(d.decision_id), adapter_id=p.adapter_id, now=H.NOW)
    assert json.loads((tmp_path / "destination.json").read_text()), "the real destination wrote the refund effect"
    after = kit.store()
    verify_envelope(kit, after)
    assert after["generation"] == 1 and after["parent_digest"] == before["state_digest"]
    row = row_of(after)
    assert row["activation_state"] == "active" and row["epoch"] == 1 and row["selection_digest"] == s1.digest
    assert row["participation"] == "required" and row["issuer_id"] == H.ISSUER_ID and row["issuer_key_id"] == H.KEY_ID
    assert row["record"]["record_id"] == "f4-age-record" and row["record"]["record_digest"] == json.loads(s1.record_text)["record_digest"]
    assert after["state"]["snapshot"]["version"] == kit.doc["version"] and after["state"]["snapshot"]["fingerprint"] == kit.config["snapshot"]["expected"]["fingerprint"]
    assert after["state"]["floors"]["high_water"][next(iter(after["state"]["rows"]))] == 1
    # exactly ONE write for construction + decide + execute (4 source reads): the repeats used the guard
    assert flow.cap_selection_source.reads == 4 and wspy.n - n0 == 1
    assert spy.n == 4 and all(vd.admitted is True and vd.epoch_floor_applied is True for vd in spy.verdicts)
    evidence("g2-1-valid-selection-persisted", {"before": before, "after": after, "source_reads": flow.cap_selection_source.reads, "writes_after_bootstrap": wspy.n - n0})


@pytest.mark.row("G2.1.c", "the directory holds exactly the configuration, snapshot, store, lock and consumed ledger: no stray temp file after success")
def test_no_stray_files_after_success(tmp_path):
    kit = make_kit(tmp_path)
    admit(kit, sel(1))
    assert sorted(p.name for p in kit.dir.iterdir()) == sorted(["authority.json", "snapshot.json", "freshness-state.json", "freshness-state.json.lock", "freshness-state.json.consumed.bootstrap-0001"])


@pytest.mark.row("G2.1.d", "a repeat of the SAME admitted selection uses the kit guard: no write, store byte-identical, generation unchanged, still admitted")
def test_repeat_of_same_selection_does_not_write(tmp_path, wspy):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    admit(kit, s1)
    b1, n1 = kit.store_bytes(), wspy.n
    for _ in range(5):
        m, _h = admit(kit, s1)
        assert m.selection_text == s1.selection_text
    assert kit.store_bytes() == b1 and wspy.n == n1 and kit.store()["generation"] == 1


@pytest.mark.row("G2.1.e", "the Registry verifier is given the STORED snapshot as last_accepted: None on the first admission, (version, fingerprint) afterwards; min_trust_snapshot_version is the pin")
def test_registry_receives_the_stored_snapshot_as_last_accepted(tmp_path, spy):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    admit(kit, s1)
    admit(kit, s1)
    assert spy.calls[0][5]["last_accepted_snapshot"] is None
    fp = kit.config["snapshot"]["expected"]["fingerprint"]
    assert tuple(spy.calls[1][5]["last_accepted_snapshot"]) == (1, fp)
    assert all(c_[5]["min_trust_snapshot_version"] == 1 for c_ in spy.calls)
    assert spy.crypto == 2 and all(set(dict(vd.layers).values()) == {"pass"} and len(vd.layers) == 11 for vd in spy.verdicts)


@pytest.mark.row("G2.1.f", "the persisted state is written only AFTER a fully admitted verdict: the same bytes are on disk for any reader as soon as the call returns (fsync + replace), and a second wrapper over the file sees it")
def test_second_wrapper_over_the_file_sees_the_persisted_row(tmp_path):
    kit = make_kit(tmp_path)
    s1, s2 = sel(1), None
    admit(kit, s1)
    other_profile = kit.load()                   # a different object, same files
    env = ST.read_state(other_profile)
    assert row_of(env)["epoch"] == 1 and env["generation"] == 1
    s2 = sel(2, prev=s1, effective=EFFECTIVE_LONG)
    admit(kit, s2, profile=other_profile)
    assert row_of(ST.read_state(kit.load()))["epoch"] == 2


# =========================================================================================================================== G2.2 legitimate epoch advancement
@pytest.mark.row("G2.2.a", "legitimate renewal: epoch 2 signed with supersedes {selection_id, epoch, statement_digest, decision_ref} naming epoch 1 is ADMITTED and persisted (generation+1, row epoch 2, parent chain)")
def test_renewal_with_signed_supersedes_advances_the_floor(tmp_path, spy):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    admit(kit, s1)
    g1 = kit.store()
    s2 = sel(2, prev=s1, effective=EFFECTIVE_LONG)
    assert set(s2.stmt["supersedes"]) == {"selection_id", "epoch", "statement_digest", "decision_ref"}
    admit(kit, s2)
    g2 = kit.store()
    verify_envelope(kit, g2)
    assert g2["generation"] == 2 and g2["parent_digest"] == g1["state_digest"]
    row = row_of(g2)
    assert row["epoch"] == 2 and row["selection_digest"] == s2.digest and row["activation_state"] == "active"
    assert g2["state"]["floors"]["high_water"][next(iter(g2["state"]["rows"]))] == 2
    assert spy.verdicts[-1].admitted is True and spy.verdicts[-1].epoch == 2
    evidence("g2-2-renewal-epoch-advance", {"before_epoch1": g1, "after_epoch2": g2, "supersedes": s2.stmt["supersedes"]})


@pytest.mark.row("G2.2.b", "a chain 1 -> 2 -> 3 persists generation 1,2,3 with an unbroken parent_digest chain, and an epoch may advance past a gap (1 -> 5) when it names the current row")
def test_chain_of_renewals_and_gap(tmp_path):
    kit = make_kit(tmp_path)
    s = [sel(1)]
    envs = []
    admit(kit, s[0]); envs.append(kit.store())
    for e in (2, 3):
        s.append(sel(e, prev=s[-1], effective=EFFECTIVE_LONG)); admit(kit, s[-1]); envs.append(kit.store())
    s.append(sel(5, prev=s[-1], effective=EFFECTIVE_LONG)); admit(kit, s[-1]); envs.append(kit.store())
    assert [e["generation"] for e in envs] == [1, 2, 3, 4]
    for a, b in zip(envs, envs[1:]):
        assert b["parent_digest"] == a["state_digest"]
    assert row_of(envs[-1])["epoch"] == 5
    assert len(row_of(envs[-1])) and kit.store()["state"]["log"] and len(kit.store()["state"]["log"]) >= 4   # the kit's hash-chained log grew with every activation


@pytest.mark.row("G2.2.c", "after a renewal the REAL workflow built from the renewed selection enforces the NEW signed bound (30/20 < host 60/60) and authorizes")
def test_workflow_uses_the_renewed_bound(tmp_path):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    admit(kit, s1)
    s2 = sel(2, prev=s1, status=30, approval=20, effective=EFFECTIVE_LONG)
    flow, p, host, _ = build(tmp_path, kit, s2)
    assert flow.status_max_age_seconds == 30 and flow.approval_max_age_seconds == 20
    d = flow.decide(p, now=H.NOW)
    assert d.result == "authorized", d.reasons
    assert row_of(kit.store())["epoch"] == 2


@pytest.mark.parametrize("name,make", [
    ("no_supersedes", lambda s1: sel(2, supersedes=None, effective=EFFECTIVE_LONG)),
    ("names_wrong_digest", lambda s1: sel(2, supersedes=dict(s1.supersedes_ref(), statement_digest="sha256:" + "0" * 64), effective=EFFECTIVE_LONG)),
    ("names_wrong_epoch", lambda s1: sel(2, supersedes=dict(s1.supersedes_ref(), epoch=7), effective=EFFECTIVE_LONG)),
    ("names_other_selection", lambda s1: sel(2, supersedes=dict(s1.supersedes_ref(), selection_id=SELECTION_ID_B), effective=EFFECTIVE_LONG)),
    ("missing_decision_ref", lambda s1: sel(2, supersedes={k: v for k, v in s1.supersedes_ref().items() if k != "decision_ref"}, effective=EFFECTIVE_LONG)),
])
@pytest.mark.row("G2.2.d", "a higher epoch that is NOT a legitimate supersession (absent, wrong digest, wrong epoch, other selection, no decision_ref) is refused, typed, and writes nothing")
def test_illegitimate_advancement_is_refused_without_writing(tmp_path, spy, name, make):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    admit(kit, s1)
    spy.reset()
    bad = make(s1)
    err = None
    before = tree(kit.dir)
    with pytest.raises(AP.AuthorityProfileRefusal) as exc:
        admit(kit, bad)
    assert exc.value.code in ("freshness_refused", "registry_not_applied"), exc.value.code
    assert exc.value.refusal.registry_code, "the underlying kit/Registry code is carried"
    after = tree(kit.dir)
    assert {k: v for k, v in after.items() if not k.endswith(".lock")} == {k: v for k, v in before.items() if not k.endswith(".lock")}
    assert row_of(kit.store())["epoch"] == 1 and kit.store()["generation"] == 1
    evidence("g2-2d-refusal-" + name, {"code": exc.value.code, "registry_code": exc.value.refusal.registry_code})


# =========================================================================================================================== G2.3 lower epoch refused
@pytest.mark.parametrize("epoch_kind", ["lower", "equal_conflicting", "equal_replay_of_old"])
@pytest.mark.row("G2.3.a", "after epoch 2 is persisted: epoch 1 (lower), a CONFLICTING epoch-2 statement, are refused by the STATE (Registry admitted them: verdict admitted=True) with selection_epoch_stale; store identical")
def test_lower_or_equal_conflicting_epoch_is_refused_by_the_state(tmp_path, spy, epoch_kind):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    admit(kit, s1)
    s2 = sel(2, prev=s1, effective=EFFECTIVE_LONG)
    admit(kit, s2)
    bad = {"lower": s1, "equal_conflicting": sel(2, prev=s1, status=100, effective=EFFECTIVE_LONG), "equal_replay_of_old": sel(1, status=110)}[epoch_kind]
    spy.reset()
    err = refused_admit(kit, bad, "freshness_refused", spy, reached=True, registry_code="selection_epoch_stale")
    assert spy.verdicts[-1].admitted is True, "the Registry verified the signed statement; it is the persisted FLOOR that refuses it"
    assert row_of(kit.store())["epoch"] == 2 and kit.store()["generation"] == 2


@pytest.mark.row("G2.3.b", "a lower epoch is refused by the REAL workflow factory too (construction fails with the typed freshness refusal; no workflow object, no decision, store identical)")
def test_lower_epoch_refused_through_the_factory(tmp_path, spy):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    admit(kit, s1)
    s2 = sel(2, prev=s1, effective=EFFECTIVE_LONG)
    admit(kit, s2)
    prepared = H.flow_kwargs(tmp_path)
    before = tree(tmp_path)
    with pytest.raises(AP.AuthorityProfileRefusal) as exc:
        build(tmp_path, kit, s1, prepared=prepared)
    assert exc.value.code == "freshness_refused" and exc.value.refusal.registry_code == "selection_epoch_stale"
    after = tree(tmp_path)
    assert {k: v for k, v in after.items() if not k.endswith(".lock")} == {k: v for k, v in before.items() if not k.endswith(".lock")}


@pytest.mark.row("G2.3.c", "the snapshot per-selection min_epochs floor also refuses: a rotated snapshot with min_epochs 3 refuses a signed epoch-2 selection at the Registry (no state write)")
def test_snapshot_min_epochs_floor_refuses_lower_epoch(tmp_path, spy):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    s2 = sel(2, prev=s1, effective=EFFECTIVE_LONG)
    admit(kit, s1); admit(kit, s2)
    kit.rotate(snapshot_doc(version=2, min_epochs=[[SELECTION_ID, 3], [SELECTION_ID_B, 1]]))
    spy.reset()
    refused_admit(kit, s2, "registry_not_applied", spy, reached=True)
    assert spy.verdicts[-1].admitted is False and "epoch" in (spy.verdicts[-1].code or "")


# =========================================================================================================================== G2.4 older snapshot refused
@pytest.mark.row("G2.4.a", "legitimate snapshot rotation is NOT a reset: new version-2 pin with the same anchor is admitted, the store (rows, floors) is kept, generation advances, the stored snapshot becomes version 2")
def test_forward_snapshot_rotation_keeps_the_store(tmp_path):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    s2 = sel(2, prev=s1, effective=EFFECTIVE_LONG)
    admit(kit, s1); admit(kit, s2)
    g = kit.store()
    kit.rotate(snapshot_doc(version=2))
    profile = kit.load()
    assert ST.authority_digest(profile) == g["authority_digest"], "snapshot.expected/source are excluded from authority_digest"
    admit(kit, s2)
    g2 = kit.store()
    verify_envelope(kit, g2)
    assert g2["state"]["snapshot"]["version"] == 2 and g2["generation"] == g["generation"] + 1
    assert row_of(g2)["epoch"] == 2 and g2["state"]["floors"]["high_water"] == g["state"]["floors"]["high_water"]
    refused_admit(kit, s1, "freshness_refused", registry_code="selection_epoch_stale")   # the floor survived the rotation


@pytest.mark.parametrize("variant", ["older_version", "same_version_other_fingerprint"])
@pytest.mark.row("G2.4.b", "an OLDER snapshot (same trust anchor, lower version / same version other fingerprint) is refused by the Registry against the STORED last_accepted snapshot; store identical")
def test_older_snapshot_is_refused_against_the_stored_snapshot(tmp_path, spy, variant):
    kit = make_kit(tmp_path, doc=snapshot_doc(version=1))
    s1 = sel(1)
    kit.rotate(snapshot_doc(version=3))
    admit(kit, s1)
    assert kit.store()["state"]["snapshot"]["version"] == 3
    older = snapshot_doc(version=2) if variant == "older_version" else snapshot_doc(version=3, valid_until="2026-10-13T00:00:00Z")
    kit.rotate(older)
    spy.reset()
    refused_admit(kit, s1, "registry_not_applied", spy, reached=True, registry_code="trust_snapshot_version_stale")
    assert spy.verdicts[-1].admitted is False
    assert tuple(spy.calls[-1][5]["last_accepted_snapshot"])[0] == 3
    # the newest snapshot is still accepted afterwards (the refusal did not poison the store)
    kit.rotate(snapshot_doc(version=3))
    admit(kit, s1)
    assert kit.store()["state"]["snapshot"]["version"] == 3


@pytest.mark.row("G2.4.c", "a fresh PROCESS also refuses the older snapshot (the stored snapshot, not process memory, is the floor)")
def test_older_snapshot_refused_in_a_fresh_process(tmp_path):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    kit.rotate(snapshot_doc(version=2))
    admit(kit, s1)
    before = kit.store_bytes()
    kit.rotate(snapshot_doc(version=1))
    res = H.child_admit(kit, s1)
    assert res["returncode"] == 0 and res["out"]["ok"] is False and res["out"]["code"] == "registry_not_applied" and res["out"]["registry_code"] == "trust_snapshot_version_stale"
    assert kit.store_bytes() == before


# =========================================================================================================================== G2.5 expired / revoked refused
@pytest.mark.parametrize("as_of,label", [("2026-10-06T00:00:00Z", "at_valid_until_boundary"), ("2026-10-09T12:00:00Z", "after_expiry"), ("2026-09-30T23:59:59Z", "before_valid_from")])
@pytest.mark.row("G2.5.a", "an expired (or not yet effective) selection is refused at the Registry window layer: typed refusal, store identical")
def test_expired_or_not_yet_effective_selection_is_refused(tmp_path, spy, as_of, label):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    admit(kit, s1)
    spy.reset()
    refused_admit(kit, s1, "registry_not_applied", spy, reached=True, profile=later(kit.load(), as_of))
    assert spy.verdicts[-1].admitted is False
    assert kit.store()["generation"] == 1 and row_of(kit.store())["epoch"] == 1


@pytest.mark.row("G2.5.b", "after expiry a RENEWAL (epoch 2 with a longer window) is admitted at the later time, and the expired epoch 1 stays refused")
def test_renewal_after_expiry_is_admitted(tmp_path):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    admit(kit, s1)
    t2 = later(kit.load(), "2026-10-08T00:00:00Z")
    refused_admit(kit, s1, "registry_not_applied", profile=t2)
    s2 = sel(2, prev=s1, effective=EFFECTIVE_LONG)
    admit(kit, s2, profile=t2)
    assert row_of(kit.store())["epoch"] == 2 and kit.store()["generation"] == 2
    refused_admit(kit, s1, "registry_not_applied", profile=t2)       # epoch 1 is expired at the later time


@pytest.mark.row("G2.5.c", "a REVOKED selection (snapshot revoked_selections), a revoked issuer KEY (revoked_key_ids) are refused, typed, store identical")
@pytest.mark.parametrize("variant", ["revoked_selection", "revoked_key"])
def test_revoked_selection_or_key_is_refused(tmp_path, spy, variant):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    admit(kit, s1)
    before = kit.store_bytes()
    kit.rotate(snapshot_doc(version=2, **({"revoked_selections": [[SELECTION_ID, 1]]} if variant == "revoked_selection" else {"revoked_key_ids": [H.KEY_ID]})))
    spy.reset()
    refused_admit(kit, s1, "registry_not_applied", spy, reached=True)
    assert spy.verdicts[-1].admitted is False
    assert kit.store_bytes() == before


@pytest.mark.row("G2.5.d", "a revocation carried by a newer admitted snapshot is PERSISTED (grow-only floors.revoked) and cannot be undone by presenting the older snapshot")
def test_revocation_is_persisted_and_grow_only(tmp_path):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    s2 = sel(2, prev=s1, effective=EFFECTIVE_LONG)
    s3 = sel(3, prev=s2, effective=EFFECTIVE_LONG)
    admit(kit, s1); admit(kit, s2)
    kit.rotate(snapshot_doc(version=2, revoked_selections=[[SELECTION_ID, 2]]))
    admit(kit, s3)                                          # epoch 3 is admitted under the snapshot that revokes epoch 2
    env = kit.store()
    assert [SELECTION_ID, 2] in env["state"]["floors"]["revoked"]
    assert row_of(env)["epoch"] == 3
    # rolling the pin back to the version-1 snapshot (which does not revoke epoch 2) is refused as an older snapshot, and the revocation stays
    kit.rotate(snapshot_doc(version=1))
    refused_admit(kit, s3, "registry_not_applied", registry_code="trust_snapshot_version_stale")
    assert [SELECTION_ID, 2] in kit.store()["state"]["floors"]["revoked"]
    evidence("g2-5d-persisted-revocation", {"floors": env["state"]["floors"]})


@pytest.mark.row("G2.5.e", "a selection for ANOTHER selection_id of the same scope is refused as selection_conflict by the state (one active selection per scope), store identical")
def test_second_selection_id_for_the_same_scope_conflicts(tmp_path, spy):
    kit = make_kit(tmp_path)
    admit(kit, sel(1))
    refused_admit(kit, sel(1, selection_id=SELECTION_ID_B), "freshness_refused", spy, reached=True, registry_code="selection_conflict")
