"""S: the battery runs against exactly the pinned sources (HEAD verified, nothing substituted); the unit under test, the Registry core and the conformance kit are imported FROM the
pinned checkouts (in this process AND in the real child processes); PyNaCl is the hash-locked one; the module labels state the claim scope."""
import os
import re
import subprocess
from pathlib import Path

import pytest

import harness as H
from harness import AP, ST


@pytest.mark.parametrize("name", ["control_plane", "registry", "replay"])
@pytest.mark.row("S", "source provenance: git rev-parse HEAD equals sources.json for every pinned repository (exact SHA, no branch/tag substitution)")
def test_pinned_source_head_is_exactly_the_declared_commit(name):
    assert H.git(name, "rev-parse", "HEAD") == H.SOURCES[name]["sha"]
    assert re.fullmatch(r"[0-9a-f]{40}", H.SOURCES[name]["sha"])


@pytest.mark.row("S", "component SHAs are recorded as evidence (component-shas)")
def test_component_shas_are_recorded():
    shas = {n: H.git(n, "rev-parse", "HEAD") for n in ("control_plane", "registry", "replay")}
    shas["control_plane_base"] = H.SOURCES["control_plane_base"]["sha"]
    shas["qualification_base"] = H.SPEC["qualification_base"]
    print("\n" + "\n".join(f"{k} {v}" for k, v in shas.items()))
    H.evidence("component-shas", shas)
    assert shas["control_plane"] == "925f7c4a7594965e336f2c34394cc52426c48b00" or os.environ.get("CAP_CP_SHA")
    assert shas["registry"] == "7de0ec9f8471c7a2ff630eb4035fa24d60b5e2eb" and shas["replay"] == "6651abef2dfc0960b09907ed268db45e809ee814"


@pytest.mark.row("S", "the unit under test, the Registry verifier, the conformance kit and Ed25519 adapter are imported FROM the pinned checkouts, here and in a real child process")
def test_modules_under_test_come_from_the_pinned_checkouts():
    import registry_adapters.ed25519_verifier as ed
    import registry_conformance.highwater as hw
    import registry_successor.v2_verified_selection as vsel
    for mod, name in ((AP, "control_plane"), (ST, "control_plane"), (vsel, "registry"), (ed, "registry"), (hw, "registry")):
        assert Path(mod.__file__).resolve().is_relative_to(H.src(name).resolve()), (mod.__name__, mod.__file__)
    r = H.run_child("modules")
    assert r["returncode"] == 0 and r["out"]["ok"]
    for modname, f in r["out"]["files"].items():
        if modname.startswith("agent_control_plane"):
            assert Path(f).resolve().is_relative_to(H.src("control_plane").resolve()), (modname, f)
        elif modname.startswith("registry_"):
            assert Path(f).resolve().is_relative_to(H.src("registry").resolve()), (modname, f)


@pytest.mark.row("S", "dependency provenance: the Ed25519 backend is the PyNaCl of the Registry hash-locked requirements-ed25519.lock.txt in this process and in the child, and signs and rejects for real")
def test_pynacl_is_the_locked_version_and_signs_and_verifies_for_real():
    import nacl
    import nacl.bindings as nb
    lock = (H.src("registry") / "requirements-ed25519.lock.txt").read_text()
    locked = re.search(r"(?mi)^pynacl==([0-9.]+)", lock).group(1)
    assert nacl.__version__ == locked
    assert H.run_child("modules")["out"]["pynacl"] == locked
    pk, sk = nb.crypto_sign_seed_keypair(bytes(range(32)))
    sig = nb.crypto_sign(b"m", sk)[:64]
    assert nb.crypto_sign_open(sig + b"m", pk) == b"m"
    with pytest.raises(Exception):
        nb.crypto_sign_open(bytes([sig[0] ^ 1]) + sig[1:] + b"m", pk)


@pytest.mark.row("S", "claim-scope labels: the state module states synthetic restart-safe only, operational trust NOT established, local-integrity limit; the profile module scopes durable anti-rollback to file-g2")
def test_module_labels_state_the_claim_scope():
    doc = ST.__doc__ or ""
    assert "NOT independently qualified" in doc and "SYNTHETIC restart-safe only" in doc and "OPERATIONAL TRUST NOT ESTABLISHED" in doc
    assert "local file integrity" in doc and "G3" in doc
    pdoc = AP.__doc__ or ""
    assert "Durable anti-rollback exists ONLY for `state.backend = file-g2`" in pdoc and "NOT independently qualified" in pdoc and "claim A only" in pdoc


@pytest.mark.row("S", "FINDING (pinned): the G1 label 'NO durable anti-rollback (G2)' no longer appears in the profile module docstring (replaced by the file-g2 scoping); the G1 test that pins the old wording fails on the G2 head for that reason only")
def test_g1_label_wording_changed_on_the_g2_head():
    assert "NO durable anti-rollback (G2)" not in (AP.__doc__ or "")
