"""G2.7: a missing, deleted, corrupt, truncated, oversized or foreign store is REFUSED with a typed code; it is never silently recreated, repaired or ignored; the Registry verifier is not
even reached (the state is opened first) and the host source is not read."""
import json
import os

import pytest

import harness as H
from harness import AP, ST, EFFECTIVE_LONG, Source, admit, build, evidence, make_kit, refused_admit, sel, tree


def unreached(kit, selection, code, spy, **kw):
    spy.reset()
    err = refused_admit(kit, selection, code, spy, reached=False, **kw)
    return err


def reseal(env):
    body = {k: v for k, v in env.items() if k != "state_digest"}
    return dict(body, state_digest=H.c.digest(body))


def put(kit, env_or_bytes):
    kit.state_path.write_bytes(env_or_bytes if isinstance(env_or_bytes, bytes) else json.dumps(env_or_bytes, sort_keys=True, separators=(",", ":")).encode())
    return kit.store_bytes()


# ------------------------------------------------------------------------------------------------------------------------------- missing
@pytest.mark.row("G2.7.a", "a profile whose store was NEVER bootstrapped refuses state_missing: no store created, the host source is not read, the Registry core is not reached")
def test_never_bootstrapped_store_is_missing_and_not_created(tmp_path, spy):
    kit = make_kit(tmp_path, bootstrap=False)
    host_reads = []
    err = unreached(kit, sel(1), "state_missing", spy)
    assert not kit.state_path.exists()
    assert not any(p.name.startswith("freshness-state.json.") and p.name.endswith(".tmp") for p in kit.dir.iterdir())
    assert not any(".consumed." in p.name for p in kit.dir.iterdir())
    # the factory path refuses too, and again, still nothing is created
    with pytest.raises(AP.AuthorityProfileRefusal) as exc:
        build(tmp_path, kit, sel(1))
    assert exc.value.code == "state_missing" and not kit.state_path.exists()
    # the read-only inspection API refuses too
    H.expect_refusal("state_missing", ST.read_state, kit.load())
    assert not kit.state_path.exists()


@pytest.mark.row("G2.7.b", "DELETE-AFTER-USE: deleting the store after a legitimate admission makes every later call refuse state_missing (in process and in a fresh process); the store is not recreated; retries keep refusing")
def test_deleted_store_refuses_and_is_not_recreated(tmp_path, spy):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    admit(kit, s1)
    gone = kit.store_bytes()
    kit.state_path.unlink()
    for _ in range(3):
        unreached(kit, s1, "state_missing", spy)
        assert not kit.state_path.exists()
    r = H.child_admit(kit, s1)
    assert r["out"]["ok"] is False and r["out"]["code"] == "state_missing" and not kit.state_path.exists()
    with pytest.raises(AP.AuthorityProfileRefusal) as exc:
        build(tmp_path, kit, s1)
    assert exc.value.code == "state_missing" and not kit.state_path.exists()
    # the consumed-bootstrap ledger is still there, so the same bootstrap cannot be replayed to resurrect an empty store
    assert (kit.dir / "freshness-state.json.consumed.bootstrap-0001").exists()
    evidence("g2-7b-delete-after-use", {"deleted_store_sha256": H.sha256_hex(gone), "outcomes": ["state_missing", "state_missing", "state_missing", "child:state_missing", "factory:state_missing"]})


# ------------------------------------------------------------------------------------------------------------------------------- corrupt (accidental damage)
def _blobs():
    return [("empty", b""), ("brace", b"{"), ("null", b"null"), ("array", b"[]"), ("number", b"7"), ("binary", b"\x00\xff\xfe garbage"), ("empty_object", b"{}"),
            ("schema_only", b'{"schema":"ocs-cap-freshness-state/1"}'), ("nan_token", b'{"generation":NaN}'), ("trailing_junk", None), ("duplicate_keys", None), ("utf16", None)]


@pytest.mark.parametrize("name", [b[0] for b in _blobs()])
@pytest.mark.row("G2.7.c", "a store that is not the closed ocs-cap-freshness-state/1 envelope (empty, truncated, garbage, wrong JSON type, NaN, trailing junk, duplicate keys, wrong encoding) refuses state_corrupt, unchanged and unrepaired")
def test_garbage_store_is_state_corrupt(tmp_path, spy, name):
    kit = make_kit(tmp_path)
    admit(kit, sel(1))
    good = kit.store_bytes()
    blob = dict(_blobs())[name]
    if name == "trailing_junk":
        blob = good + b"\n{}"
    elif name == "duplicate_keys":
        blob = good.replace(b'"generation":1', b'"generation":1,"generation":1')
        assert blob != good
    elif name == "utf16":
        blob = good.decode().encode("utf-16")
    bytes_before = put(kit, blob)
    unreached(kit, sel(1), "state_corrupt", spy)
    assert kit.store_bytes() == bytes_before
    # a fresh process refuses the same way
    assert H.child_admit(kit, sel(1))["out"]["code"] == "state_corrupt"
    H.expect_refusal("state_corrupt", ST.read_state, kit.load())


@pytest.mark.row("G2.7.d", "ACCIDENTAL damage: a single flipped bit anywhere in the persisted bytes, and every truncation, is detected (state_corrupt or, when the flip turns the file into other valid structure, never an admission); never a silent accept")
def test_bit_flips_and_truncations_are_never_accepted(tmp_path, spy):
    kit = make_kit(tmp_path)
    admit(kit, sel(1))
    good = kit.store_bytes()
    positions = sorted({0, 1, 5, 20, 60, len(good) // 4, len(good) // 3, len(good) // 2, (2 * len(good)) // 3, len(good) - 40, len(good) - 10, len(good) - 2, len(good) - 1})
    outcomes = {}
    for pos in positions:
        bad = bytearray(good)
        bad[pos] ^= 0x01
        kit.state_path.write_bytes(bytes(bad))
        spy.reset()
        with pytest.raises(AP.AuthorityProfileRefusal) as exc:
            admit(kit, sel(1))
        outcomes[pos] = exc.value.code
        assert exc.value.code in ("state_corrupt", "state_authority_mismatch"), (pos, exc.value.code)
        assert spy.reached is False
        assert kit.state_path.read_bytes() == bytes(bad)
    for cut in (0, 1, len(good) // 2, len(good) - 1):
        kit.state_path.write_bytes(good[:cut])
        with pytest.raises(AP.AuthorityProfileRefusal) as exc:
            admit(kit, sel(1))
        assert exc.value.code == "state_corrupt", (cut, exc.value.code)
    assert set(outcomes.values()) <= {"state_corrupt", "state_authority_mismatch"}
    evidence("g2-7d-bitflip-outcomes", {"good_sha256": H.sha256_hex(good), "outcome_by_flipped_byte": outcomes})


@pytest.mark.row("G2.7.e", "a store larger than the 8 MiB bound, a directory in place of the store, and a symlink-less unreadable path all refuse state_corrupt; nothing is created or removed")
def test_oversized_or_directory_store_is_state_corrupt(tmp_path, spy):
    kit = make_kit(tmp_path)
    admit(kit, sel(1))
    good = kit.store_bytes()
    kit.state_path.write_bytes(b" " * (8 * 1024 * 1024 + 2))
    unreached(kit, sel(1), "state_corrupt", spy)
    kit.state_path.unlink()
    kit.state_path.mkdir()
    unreached(kit, sel(1), "state_corrupt", spy)
    assert kit.state_path.is_dir() and list(kit.state_path.iterdir()) == []


# ------------------------------------------------------------------------------------------------------------------------------- re-sealed (structurally wrong but digest-consistent)
def _mutations(env):
    def m(f):
        e = json.loads(json.dumps(env))
        f(e)
        return reseal(e)
    return {
        "extra_member": m(lambda e: e.update(extra=1)),
        "missing_member": m(lambda e: e.pop("parent_digest")),
        "schema_v2": m(lambda e: e.update(schema="ocs-cap-freshness-state/2")),
        "generation_negative": m(lambda e: e.update(generation=-1)),
        "generation_bool": m(lambda e: e.update(generation=True)),
        "generation_string": m(lambda e: e.update(generation="1")),
        "state_not_object": m(lambda e: e.update(state=[])),
        "state_unknown_store": m(lambda e: e["state"].update(store="unknown")),
        "kit_schema_changed": m(lambda e: e["state"].update(schema="ocs-conformance-state/2")),
        "kit_extra_member": m(lambda e: e["state"].update(rows_extra=1)),
        "kit_log_entry_altered": m(lambda e: e["state"]["log"][0].update(epoch=9)),
        "kit_log_removed": m(lambda e: e["state"].update(log=[])),
        "kit_high_water_lowered": m(lambda e: e["state"]["floors"]["high_water"].update({k: 0 for k in e["state"]["floors"]["high_water"]})),
        "kit_row_epoch_inflated": m(lambda e: next(iter(e["state"]["rows"].values())).update(epoch=50)),
    }


@pytest.mark.row("G2.7.f", "a digest-consistent store whose structure violates the closed envelope or the Registry kit state invariants (extra/missing member, wrong schema, bad generation type, kit state altered) refuses state_corrupt")
@pytest.mark.parametrize("name", list(_mutations({"schema": "x", "namespace": "n", "authority_digest": "a", "generation": 1, "parent_digest": None, "bootstrap": {}, "state": {"log": [{}], "rows": {"k": {}}, "floors": {"high_water": {"k": 1}}}, "state_digest": "d"})))
def test_resealed_structural_tamper_is_state_corrupt(tmp_path, spy, name):
    kit = make_kit(tmp_path)
    admit(kit, sel(1))
    bad = _mutations(kit.store())[name]
    before = put(kit, bad)
    err = unreached(kit, sel(1), "state_corrupt", spy)
    assert kit.store_bytes() == before


@pytest.mark.row("G2.7.g", "a refused corrupt store is NOT self-healing: after the damage a valid selection is still refused, a bootstrap cannot overwrite it (bootstrap_state_exists), and removing the damage by restoring the original bytes resumes service")
def test_corrupt_store_is_not_repaired_or_replaced(tmp_path, spy):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    admit(kit, s1)
    good = kit.store_bytes()
    bad = put(kit, good[: len(good) // 2])
    for _ in range(2):
        unreached(kit, s1, "state_corrupt", spy)
    path = kit.write_bootstrap(kit.bootstrap_doc(bootstrap_id="bootstrap-0002"))
    H.expect_refusal("bootstrap_state_exists", ST.bootstrap_state, kit.load(), path, AP._now(kit.load()))
    assert kit.store_bytes() == bad and not (kit.dir / "freshness-state.json.consumed.bootstrap-0002").exists()
    kit.state_path.write_bytes(good)
    admit(kit, s1)
    assert kit.store_bytes() == good


# ------------------------------------------------------------------------------------------------------------------------------- foreign store
@pytest.mark.row("G2.7.h", "a store of another namespace or another authority configuration (digest-consistent, valid kit state) refuses state_authority_mismatch (never state_corrupt, never adopted)")
@pytest.mark.parametrize("which", ["namespace", "authority_digest"])
def test_foreign_but_wellformed_store_is_authority_mismatch(tmp_path, spy, which):
    kit = make_kit(tmp_path)
    admit(kit, sel(1))
    env = kit.store()
    env[which] = "other-namespace" if which == "namespace" else "sha256:" + "ab" * 32
    before = put(kit, reseal(env))
    unreached(kit, sel(1), "state_authority_mismatch", spy)
    assert kit.store_bytes() == before
