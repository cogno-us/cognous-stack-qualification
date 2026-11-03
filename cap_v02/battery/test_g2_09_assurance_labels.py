"""G2.17 (H1): explicit assurance labels. The lane derives machine-readable labels from the profile the battery actually LOADS and writes them to the evidence directory
(`g2-evidence/assurance-labels.json`, included in the SHA-256 manifest, written on pass and on failure). The labels never claim authentication, operational trust or production use.
There is no provider concept and no structural/keyless mode; `derived_inputs` only reports what the loaded profile declares."""
import json

import pytest

import harness as H
from harness import make_kit


@pytest.mark.row("G2.17.a", "assurance labels are derived from the loaded profile and state NON-PRODUCTION, synthetic-verified, no authentication, no operational trust")
def test_labels_derive_from_the_loaded_profile_and_do_not_overclaim(tmp_path):
    kit = make_kit(tmp_path)
    profile = kit.load()                                   # loaded WITH the owner digest, as the battery does
    lab = H.assurance_labels(profile, digest_supplied=True, battery_result="passed")
    assert lab["label"] == "NON-PRODUCTION" and lab["mode"] == "synthetic-verified" and lab["claim"] == "A mechanism, synthetic keys"
    assert lab["authenticated_authority"] is False and lab["operational_trust"] is False
    d = lab["derived_inputs"]
    assert d == {"profile_mode": "synthetic", "state_backend": "file-g2", "clock_kind": "fixed_instant", "snapshot_source_kind": "file", "expected_config_digest_supplied": True}
    assert set(lab["sources"]) == {"qualification", "control_plane", "registry", "replay"} and lab["sources"]["control_plane"] == H.SOURCES["control_plane"]["sha"]
    text = json.dumps(lab).lower()
    assert "provider" not in text and "anti-rollback" not in text.replace("independently anchored anti-rollback (g3)", "")
    assert any("B:" in x for x in lab["not_claimed"]) and any("operational trust" in x for x in lab["not_claimed"])
    H.LABELS_DRAFT.clear()
    H.LABELS_DRAFT.update(lab)                              # conftest completes battery_result and writes the evidence file


@pytest.mark.row("G2.17.b", "labels follow the loaded profile: a stateless profile and an undigested load are reported as such, not as constants")
def test_labels_report_a_stateless_profile_and_an_undigested_load_as_such(tmp_path):
    kit = make_kit(tmp_path / "k", backend="none-g1", bootstrap=False)
    profile = kit.load(digest=None)
    d = H.assurance_labels(profile, digest_supplied=False, battery_result="failed")["derived_inputs"]
    assert d["state_backend"] == "none-g1" and d["expected_config_digest_supplied"] is False


@pytest.mark.row("G2.17.c", "an operational profile can never be labelled synthetic-verified")
def test_an_operational_profile_cannot_be_labelled_synthetic_verified(tmp_path):
    class Fake:  # the loader never returns an operational profile (it always refuses); a hand-built one must still not be labelled
        mode = "operational"
    with pytest.raises(ValueError):
        H.assurance_labels(Fake(), digest_supplied=True, battery_result="passed")
