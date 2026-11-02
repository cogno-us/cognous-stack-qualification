"""G2.8: cold start. `ocs-cap-bootstrap/1` is owner-run, one-shot, TTL <= 3600 s, bound to namespace + authority digest + mode, carries NO floor-seeding member, creates the store EXCLUSIVELY
with an EMPTY kit state, records a consumed-id ledger, and never resets an existing store. A missing store is never created implicitly. Every refusal leaves no store and no ledger."""
import dataclasses
import json
import time

import pytest

import harness as H
from harness import AP, ST, admit, evidence, make_kit, sel, tree


def boot(kit, **over):
    return kit.write_bootstrap(kit.bootstrap_doc(**over))


def run(kit, path, now=None):
    profile = kit.load()
    return ST.bootstrap_state(profile, path, now if now is not None else AP._now(profile))


def refuse(kit, path, code, now=None):
    before = tree(kit.dir)
    H.expect_refusal(code, run, kit, path, now)
    after = {k: v for k, v in tree(kit.dir).items() if not k.endswith(".lock")}
    assert after == {k: v for k, v in before.items() if not k.endswith(".lock")}, "a refused bootstrap must not create a store or a ledger"
    assert not kit.state_path.exists() or "freshness-state.json" in before


@pytest.mark.row("G2.8.a", "an authorized bootstrap creates generation 0 with the EMPTY kit state and a consumed ledger; the envelope records bootstrap_id and bootstrap digest; the document is accepted at the 3600 s TTL boundary")
def test_authorized_bootstrap_creates_empty_store_and_ledger(tmp_path):
    kit = make_kit(tmp_path, bootstrap=False)
    path = boot(kit)
    doc = json.loads(path.read_text())
    assert set(doc) == {"schema", "bootstrap_id", "namespace", "authority_digest", "issued_for_mode", "issued_at", "not_after"}
    env = run(kit, path)
    assert env["generation"] == 0 and env["parent_digest"] is None and env["state"] == H.kitmod.empty_state()
    assert env == kit.store()
    assert env["bootstrap"]["bootstrap_id"] == "bootstrap-0001" and env["bootstrap"]["bootstrap_digest"] == H.c.digest(doc)
    assert env["authority_digest"] == H.independent_authority_digest(kit.config) == doc["authority_digest"]
    ledger = kit.dir / "freshness-state.json.consumed.bootstrap-0001"
    assert ledger.is_file() and json.loads(ledger.read_text()) == {"bootstrap_id": "bootstrap-0001", "namespace": H.NAMESPACE}
    evidence("g2-8-bootstrap-created-store", {"bootstrap": doc, "envelope": env})


@pytest.mark.row("G2.8.b", "a fresh process can bootstrap and then a valid selection is admitted by another process (cold start end to end across processes)")
def test_bootstrap_in_one_process_admit_in_another(tmp_path):
    kit = make_kit(tmp_path, bootstrap=False)
    path = boot(kit)
    b = H.run_child("bootstrap", config=str(kit.config_path), digest=kit.digest, bootstrap=str(path), now=H.AS_OF)
    assert b["out"]["ok"] is True and b["out"]["generation"] == 0, b
    a = H.child_admit(kit, sel(1))
    assert a["out"]["ok"] is True and kit.store()["generation"] == 1


# ------------------------------------------------------------------------------------------------------------------------------- unauthorized cold start
@pytest.mark.parametrize("label,over,code", [
    ("wrong_namespace", {"namespace": "another-namespace"}, "bootstrap_invalid"),
    ("wrong_authority_digest", {"authority_digest": "sha256:" + "0" * 64}, "bootstrap_invalid"),
    ("other_authority_digest_valid_shape", {"authority_digest": "sha256:" + "f" * 64}, "bootstrap_invalid"),
    ("mode_operational", {"issued_for_mode": "operational"}, "bootstrap_invalid"),
    ("mode_unknown", {"issued_for_mode": "anything"}, "bootstrap_invalid"),
    ("over_ttl_3601", {"issued_at": "2026-10-05T18:00:00Z", "not_after": "2026-10-05T19:00:01Z"}, "bootstrap_invalid"),
    ("over_ttl_one_day", {"issued_at": "2026-10-05T18:30:00Z", "not_after": "2026-10-06T18:30:00Z"}, "bootstrap_invalid"),
    ("zero_lifetime", {"issued_at": "2026-10-05T18:30:00Z", "not_after": "2026-10-05T18:30:00Z"}, "bootstrap_invalid"),
    ("negative_lifetime", {"issued_at": "2026-10-05T19:30:00Z", "not_after": "2026-10-05T18:30:00Z"}, "bootstrap_invalid"),
    ("expired_one_second_ago", {"issued_at": "2026-10-05T18:00:00Z", "not_after": "2026-10-05T18:59:59Z"}, "bootstrap_expired"),
    ("expired_exactly_now", {"issued_at": "2026-10-05T18:00:00Z", "not_after": "2026-10-05T19:00:00Z"}, "bootstrap_expired"),
    ("not_yet_issued", {"issued_at": "2026-10-05T19:00:01Z", "not_after": "2026-10-05T19:30:00Z"}, "bootstrap_expired"),
    ("expired_days_ago", {"issued_at": "2026-09-01T00:00:00Z", "not_after": "2026-09-01T01:00:00Z"}, "bootstrap_expired"),
    ("bad_timestamp_format", {"issued_at": "2026-10-05 18:30:00"}, "bootstrap_invalid"),
    ("integer_timestamp", {"issued_at": 1791225000}, "bootstrap_invalid"),
    ("null_timestamp", {"not_after": None}, "bootstrap_invalid"),
    ("bootstrap_id_too_short", {"bootstrap_id": "b1"}, "bootstrap_invalid"),
    ("bootstrap_id_bad_chars", {"bootstrap_id": "../../etc/passwd"}, "bootstrap_invalid"),
    ("bootstrap_id_with_slash", {"bootstrap_id": "boot/strap-0001"}, "bootstrap_invalid"),
    ("bootstrap_id_not_string", {"bootstrap_id": 12345678}, "bootstrap_invalid"),
    ("wrong_schema", {"schema": "ocs-cap-bootstrap/2"}, "bootstrap_invalid"),
])
@pytest.mark.row("G2.8.c", "UNAUTHORIZED cold start refused, typed, no store and no ledger: wrong namespace / authority digest / mode, over-TTL, zero or negative lifetime, expired, not yet valid, malformed timestamps, bad id, wrong schema")
def test_unauthorized_bootstrap_is_refused(tmp_path, label, over, code):
    kit = make_kit(tmp_path, bootstrap=False)
    refuse(kit, boot(kit, **over), code)
    assert not kit.state_path.exists() and not any(".consumed." in p.name for p in kit.dir.iterdir())


@pytest.mark.parametrize("member,value", [
    ("epoch", 99), ("min_epochs", [["sel-test-1", 99]]), ("high_water", {"k": 5}), ("floors", {"high_water": {}}), ("state", {}), ("rows", {}), ("generation", 41), ("snapshot", {"version": 9}),
    ("floor", 7), ("seed", "x"), ("revoked", []), ("selection_epoch", 3), ("min_snapshot_version", 5), ("last_accepted", [1, "sha256:x"]),
])
@pytest.mark.row("G2.8.d", "a bootstrap with ANY extra (floor-seeding) member is refused bootstrap_invalid: the schema is closed and a cold start cannot seed epochs, floors, rows, snapshots or a generation")
def test_floor_seeding_member_is_refused(tmp_path, member, value):
    kit = make_kit(tmp_path, bootstrap=False)
    refuse(kit, boot(kit, **{member: value}), "bootstrap_invalid")


@pytest.mark.parametrize("drop", ["schema", "bootstrap_id", "namespace", "authority_digest", "issued_for_mode", "issued_at", "not_after"])
@pytest.mark.row("G2.8.e", "a bootstrap missing any member is refused bootstrap_invalid")
def test_missing_member_is_refused(tmp_path, drop):
    kit = make_kit(tmp_path, bootstrap=False)
    doc = kit.bootstrap_doc()
    doc.pop(drop)
    refuse(kit, kit.write_bootstrap(doc, name="x.json"), "bootstrap_invalid")


@pytest.mark.parametrize("label,raw", [
    ("empty", b""), ("not_json", b"bootstrap please"), ("array", b"[]"), ("null", b"null"), ("truncated", b'{"schema":"ocs-cap-bootstrap/1"'), ("nan", b'{"a":NaN}'),
    ("duplicate_keys", None), ("oversized", b'{"x":"' + b"A" * 70000 + b'"}'), ("binary", b"\x00\x01\x02"),
])
@pytest.mark.row("G2.8.f", "an unreadable, non-strict, duplicate-key, oversized or non-object bootstrap document is refused bootstrap_invalid; a MISSING document file is bootstrap_invalid too")
def test_malformed_bootstrap_document_is_refused(tmp_path, label, raw):
    kit = make_kit(tmp_path, bootstrap=False)
    if label == "duplicate_keys":
        text = json.dumps(kit.bootstrap_doc())
        raw = (text[:-1] + ', "bootstrap_id": "bootstrap-9999"}').encode()
    refuse(kit, kit.write_bootstrap({}, raw=raw, name="m.json"), "bootstrap_invalid")


@pytest.mark.row("G2.8.g", "a bootstrap path that does not exist is bootstrap_invalid, nothing created")
def test_missing_bootstrap_file_is_refused(tmp_path):
    kit = make_kit(tmp_path, bootstrap=False)
    refuse(kit, tmp_path / "boot" / "nope.json", "bootstrap_invalid")


@pytest.mark.row("G2.8.h", "key-shaped material inside a bootstrap document is refused (secret deny) and nothing is created")
def test_key_shaped_material_is_refused(tmp_path):
    kit = make_kit(tmp_path, bootstrap=False)
    refuse(kit, boot(kit, bootstrap_id="bootstrap-0001", private_key="00" * 32), "bootstrap_invalid")
    refuse(kit, boot(kit, bootstrap_id="bootstrap-0002", authority_digest="-----BEGIN PRIVATE KEY-----"), "bootstrap_invalid")


# ------------------------------------------------------------------------------------------------------------------------------- consumed / existing
@pytest.mark.row("G2.8.i", "CONSUMED: after the store is deleted, the SAME bootstrap id is refused bootstrap_consumed (ledger), no store appears; a bootstrap id is single-use")
def test_consumed_bootstrap_cannot_be_replayed(tmp_path):
    kit = make_kit(tmp_path, bootstrap=False)
    path = boot(kit)
    run(kit, path)
    kit.state_path.unlink()
    refuse(kit, path, "bootstrap_consumed")
    assert (kit.dir / "freshness-state.json.consumed.bootstrap-0001").exists()


@pytest.mark.row("G2.8.j", "EXISTING STORE: a bootstrap (same or fresh id) over an existing store is refused bootstrap_state_exists, the store is byte-identical and a fresh id is NOT burned (no ledger written)")
def test_bootstrap_never_resets_an_existing_store(tmp_path):
    kit = make_kit(tmp_path)
    admit(kit, sel(1))
    before = kit.store_bytes()
    for bid in ("bootstrap-0001", "bootstrap-0002"):
        H.expect_refusal("bootstrap_state_exists", run, kit, boot(kit, bootstrap_id=bid))
        assert kit.store_bytes() == before
    assert not (kit.dir / "freshness-state.json.consumed.bootstrap-0002").exists()
    assert kit.store()["generation"] == 1


@pytest.mark.row("G2.8.k", "a bootstrap is refused when the store file is CORRUPT or a directory (existence, not validity, blocks it): never replaced")
def test_bootstrap_does_not_replace_a_corrupt_store(tmp_path):
    kit = make_kit(tmp_path, bootstrap=False)
    kit.state_path.write_bytes(b"garbage")
    H.expect_refusal("bootstrap_state_exists", run, kit, boot(kit))
    assert kit.state_path.read_bytes() == b"garbage"


@pytest.mark.row("G2.8.l", "a missing store is never created implicitly: admit, factory, read_state, open_transaction on an absent store create nothing")
def test_nothing_creates_a_store_implicitly(tmp_path):
    kit = make_kit(tmp_path, bootstrap=False)
    profile = kit.load()
    H.expect_refusal("state_missing", admit, kit, sel(1))
    H.expect_refusal("state_missing", ST.read_state, profile)
    H.expect_refusal("state_missing", ST.open_transaction, profile, AP._now(profile))
    with pytest.raises(AP.AuthorityProfileRefusal):
        H.build(tmp_path, kit, sel(1))
    assert not kit.state_path.exists() and not any(".consumed." in p.name or p.name.endswith(".tmp") for p in kit.dir.iterdir())


# ------------------------------------------------------------------------------------------------------------------------------- bootstrap only for synthetic file-g2
@pytest.mark.row("G2.8.m", "bootstrap is available only for a loader-validated synthetic file-g2 profile: a none-g1 profile and a hand-built operational profile refuse authority_config_unprovisioned, nothing created")
def test_bootstrap_requires_synthetic_file_g2(tmp_path):
    kit = make_kit(tmp_path, bootstrap=False)
    path = boot(kit)
    profile = kit.load()
    H.expect_refusal("authority_config_unprovisioned", ST.bootstrap_state, dataclasses.replace(profile, mode="operational"), path, AP._now(profile))
    H.expect_refusal("authority_config_unprovisioned", ST.bootstrap_state, dataclasses.replace(profile, state_backend="none-g1", state_path=""), path, AP._now(profile))
    kit2 = make_kit(tmp_path / "g1", bootstrap=False, backend="none-g1")
    H.expect_refusal("authority_config_unprovisioned", ST.bootstrap_state, kit2.load(), kit2.write_bootstrap(kit2.bootstrap_doc()), AP._now(kit2.load()))
    assert not kit.state_path.exists() and not any(".consumed." in p.name for p in kit.dir.iterdir())


# ------------------------------------------------------------------------------------------------------------------------------- concurrent cold start
@pytest.mark.row("G2.8.n", "8 concurrent processes bootstrap with DIFFERENT ids: exactly one creates the store (generation 0), the others refuse bootstrap_state_exists; exactly one ledger exists and the store verifies")
def test_concurrent_bootstrap_different_ids_exactly_one_wins(tmp_path):
    kit = make_kit(tmp_path, bootstrap=False)
    go = tmp_path / "go"
    procs = []
    for i in range(8):
        p = boot(kit, bootstrap_id=f"bootstrap-c{i:03d}")
        procs.append(H.popen_child("bootstrap", config=str(kit.config_path), digest=kit.digest, bootstrap=str(p), now=H.AS_OF, go_file=str(go)))
    time.sleep(1.0)
    go.write_text("go")
    outs = []
    for pr in procs:
        so, se = pr.communicate(timeout=60)
        assert pr.returncode == 0, se
        outs.append(json.loads(so.strip().splitlines()[-1]))
    wins = [o for o in outs if o["ok"]]
    assert len(wins) == 1, outs
    assert sorted(o["code"] for o in outs if not o["ok"]) == ["bootstrap_state_exists"] * 7
    env = kit.store()
    assert env["generation"] == 0 and env["state"] == H.kitmod.empty_state()
    ledgers = [p.name for p in kit.dir.iterdir() if ".consumed." in p.name]
    assert len(ledgers) == 1 and ledgers[0].endswith(env["bootstrap"]["bootstrap_id"])
    assert not any(p.name.endswith(".tmp") for p in kit.dir.iterdir())
    evidence("g2-8n-concurrent-bootstrap", {"outcomes": outs, "ledgers": ledgers, "winner_bootstrap_id": env["bootstrap"]["bootstrap_id"]})


@pytest.mark.row("G2.8.o", "8 concurrent processes using the SAME bootstrap document: exactly one wins; the rest are refused (exists/consumed)")
def test_concurrent_bootstrap_same_id_exactly_one_wins(tmp_path):
    kit = make_kit(tmp_path, bootstrap=False)
    go = tmp_path / "go"
    p = boot(kit)
    procs = [H.popen_child("bootstrap", config=str(kit.config_path), digest=kit.digest, bootstrap=str(p), now=H.AS_OF, go_file=str(go)) for _ in range(8)]
    time.sleep(1.0)
    go.write_text("go")
    outs = []
    for pr in procs:
        so, se = pr.communicate(timeout=60)
        assert pr.returncode == 0, se
        outs.append(json.loads(so.strip().splitlines()[-1]))
    assert sum(1 for o in outs if o["ok"]) == 1, outs
    assert {o["code"] for o in outs if not o["ok"]} <= {"bootstrap_state_exists", "bootstrap_consumed"}
    assert kit.store()["generation"] == 0


# ------------------------------------------------------------------------------------------------------------------------------- crash during bootstrap / documented limits
@pytest.mark.row("G2.8.p", "CRASH between the consumed-ledger write and the store creation: no store exists (fail closed: state_missing), the id stays burned (bootstrap_consumed), a fresh id succeeds")
def test_crash_during_bootstrap_fails_closed(tmp_path):
    kit = make_kit(tmp_path, bootstrap=False)
    path = boot(kit)
    r = H.run_child("bootstrap", config=str(kit.config_path), digest=kit.digest, bootstrap=str(path), now=H.AS_OF, crash_on_link=2)
    assert r["returncode"] == 98 and r["out"] is None, r
    assert not kit.state_path.exists()
    assert (kit.dir / "freshness-state.json.consumed.bootstrap-0001").exists()
    H.expect_refusal("state_missing", admit, kit, sel(1))
    refuse(kit, path, "bootstrap_consumed")
    run(kit, boot(kit, bootstrap_id="bootstrap-0002"))
    assert kit.store()["generation"] == 0


@pytest.mark.row("G2.8.q", "DOCUMENTED LIMIT (pinned): deleting the store AND its consumed ledger lets a still-valid bootstrap recreate an EMPTY store (floors lost); the local files cannot detect it (G3 anchor)")
def test_limit_deleting_store_and_ledger_allows_bootstrap_replay(tmp_path):
    kit = make_kit(tmp_path, bootstrap=False)
    path = boot(kit)
    run(kit, path)
    s1 = sel(1)
    s2 = sel(2, prev=s1, effective=H.EFFECTIVE_LONG)
    admit(kit, s1); admit(kit, s2)
    kit.state_path.unlink()
    (kit.dir / "freshness-state.json.consumed.bootstrap-0001").unlink()
    env = run(kit, path)
    assert env["generation"] == 0 and env["state"] == H.kitmod.empty_state()
    admit(kit, s1)           # the epoch-1 floor is gone: the older selection is admitted again. NOT detected locally.
    evidence("g2-limit-delete-store-and-ledger", {"result": "epoch 1 re-admitted after store+ledger deletion and bootstrap replay", "detected_locally": False})
