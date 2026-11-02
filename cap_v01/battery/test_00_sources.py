"""S: the battery runs against exactly the pinned sources (HEAD verified, nothing substituted), the unit under test is imported from the pinned checkout, PyNaCl is the hash-locked one."""
import re
from pathlib import Path

import pytest

import harness as H
from harness import AP


@pytest.mark.parametrize("name", ["control_plane", "registry", "replay"])
@pytest.mark.row("S", "source provenance: git rev-parse HEAD equals sources.json for every pinned repository")
def test_pinned_source_head_is_exactly_the_declared_commit(name):
    assert H.git(name, "rev-parse", "HEAD") == H.SOURCES[name]["sha"]


@pytest.mark.row("S", "the unit under test and the Registry verifier are imported FROM the pinned checkouts, not from an installed or stale copy")
def test_modules_under_test_come_from_the_pinned_checkouts():
    import registry_successor.v2_verified_selection as vsel
    import registry_adapters.ed25519_verifier as ed
    import agent_replay_bundle.importers as imp
    for mod, name in ((AP, "control_plane"), (vsel, "registry"), (ed, "registry"), (imp, "replay")):
        assert Path(mod.__file__).resolve().is_relative_to(H.src(name).resolve()), (mod.__name__, mod.__file__)


@pytest.mark.row("S", "dependency provenance: real Ed25519 backend is the PyNaCl of the Registry hash-locked requirements-ed25519.lock.txt, and it signs and rejects for real")
def test_pynacl_is_the_locked_version_and_signs_and_verifies_for_real():
    import nacl
    import nacl.bindings as nb
    lock = (H.src("registry") / "requirements-ed25519.lock.txt").read_text()
    locked = re.search(r"(?mi)^pynacl==([0-9.]+)", lock).group(1)
    assert nacl.__version__ == locked
    pk, sk = nb.crypto_sign_seed_keypair(bytes(range(32)))
    sig = nb.crypto_sign(b"m", sk)[:64]
    assert nb.crypto_sign_open(sig + b"m", pk) == b"m"
    with pytest.raises(Exception):
        nb.crypto_sign_open(bytes([sig[0] ^ 1]) + sig[1:] + b"m", pk)


@pytest.mark.row("S", "the unit's module labels itself: no durable anti-rollback (G2), claim A only, not independently qualified (G1 labels the evidence; it keeps no state)")
def test_module_carries_the_g2_and_claim_scope_labels():
    doc = AP.__doc__ or ""
    assert re.search(r"NO durable anti-rollback \(G2\)", doc)
    assert "NOT independently qualified" in doc
    assert "claim A only" in doc
