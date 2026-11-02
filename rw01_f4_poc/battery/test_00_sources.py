"""T00: the battery runs against exactly the pinned sources (HEAD and tree verified, nothing substituted), and PyNaCl is the hash-locked one."""
import json
import re

import pytest

import harness as H


@pytest.mark.parametrize("name", sorted(H.SOURCES))
@pytest.mark.row("S", "source provenance: git rev-parse HEAD and HEAD^{tree} equal sources.json for every pinned repository")
@pytest.mark.evidence("STATIC")
def test_pinned_source_is_exactly_the_declared_commit_and_tree(name):
    spec = H.SOURCES[name]
    assert H.git(name, "rev-parse", "HEAD") == spec["sha"]
    assert H.git(name, "rev-parse", "HEAD^{tree}") == spec["tree"]
    assert H.git(name, "status", "--porcelain", "--untracked-files=no") == ""


@pytest.mark.row("S", "dependency provenance: real Ed25519 backend is PyNaCl 1.6.2 from the Registry hash-locked requirements-ed25519.lock.txt")
@pytest.mark.evidence("STATIC")
def test_pynacl_is_the_locked_version_and_signs_and_verifies_for_real():
    import nacl
    import nacl.bindings as nb
    lock = (H.src("registry") / "requirements-ed25519.lock.txt").read_text()
    locked = re.search(r"(?mi)^pynacl==([0-9.]+)", lock).group(1)
    assert nacl.__version__ == locked == "1.6.2"
    pk, sk = nb.crypto_sign_seed_keypair(bytes(range(32)))
    sig = nb.crypto_sign(b"m", sk)[:64]
    assert nb.crypto_sign_open(sig + b"m", pk) == b"m"
    with pytest.raises(Exception):
        nb.crypto_sign_open(bytes([sig[0] ^ 1]) + sig[1:] + b"m", pk)


@pytest.mark.row("S", "registry PR #86 changes NO existing production file and the CP test pin 6f600ab1 production code is byte-identical to PR #86 head (so the single-process run is faithful to the CP tests' pin)")
@pytest.mark.evidence("STATIC")
def test_registry_pr86_adds_only_new_production_files_and_pin_6f600ab1_production_code_is_identical():
    def tree_files(name):
        out = H.git(name, "ls-tree", "-r", "--full-tree", "HEAD").splitlines()
        return {line.split("\t", 1)[1]: line.split()[2] for line in out}
    head, base, pin = tree_files("registry"), tree_files("registry_base"), tree_files("registry_cp_pin")
    prod = lambda p: p.endswith(".py") and p.split("/")[0] in ("registry_successor", "registry_adapters", "registry_consumer", "registry_contract", "registry_records", "registry_conformance")
    changed = sorted(p for p in base if prod(p) and head.get(p) != base[p])
    added = sorted(p for p in head if prod(p) and p not in base)
    assert changed == [], changed
    assert added == ["registry_consumer/evidence_verifier.py", "registry_successor/v2_verified_selection.py"], added
    # every production file that the CP pin has exists at PR #86 head with the same git blob id
    diff = sorted(p for p in pin if prod(p) and head.get(p) != pin[p])
    assert diff == [], diff
