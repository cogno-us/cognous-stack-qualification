"""ER-02-3 probes for The Index: supersession preserves history (lifecycle contract on a disposable local chain).

Needs PROBE_INDEX_DIR (pinned checkout) with `npm ci` already run in chain/ and a Node runtime.
Also covers the in-memory claims service's refusal to rewrite or delete accepted claims.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import pin_dir

HERE = Path(__file__).resolve().parent


@pytest.fixture(scope="module")
def chain_obs():
    pin = Path(pin_dir("PROBE_INDEX_DIR"))
    if not shutil.which("node"):
        pytest.fail("node is required for the lifecycle probe")
    if not (pin / "chain" / "node_modules" / "ethers").is_dir():
        pytest.fail("chain dependencies missing: run `npm ci --ignore-scripts` in the pinned chain/ directory")
    p = subprocess.run(["node", str(HERE / "index_supersession_driver.mjs")], capture_output=True, text=True,
                       timeout=240, env=dict(os.environ))
    assert p.returncode == 0, p.stderr[-2000:]
    return json.loads(p.stdout)


def test_probe_supersession_only_the_author_may_supersede_with_a_related_revision(chain_obs):
    o = chain_obs
    assert o["third_party_supersede"] is False
    assert o["unrelated_successor"] is False and o["self_successor"] is False
    assert o["empty_reason"] is False
    assert o["supersede_ok"] is True


def test_probe_supersession_preserves_original_record_and_links_the_revision(chain_obs):
    o = chain_obs
    assert o["original"] == {"content_preserved": True, "lifecycle": 3, "successor_is_revision": True, "author_preserved": True}
    assert o["revision"] == {"content": True, "lifecycle": 1, "parent_is_original": True}


def test_probe_supersession_history_is_reconstructible_in_order_from_logs(chain_obs):
    o = chain_obs
    assert o["history"].index("Registered:v1") < o["history"].index("Registered:v2") < o["history"].index("LifecycleChanged:v1:3")
    assert o["reconstructed_original"] == {"content_preserved": True, "lifecycle": 3, "successor_is_revision": True}


def test_probe_supersession_is_terminal_and_does_not_erase_later_criticism(chain_obs):
    o = chain_obs
    assert o["withdraw_after_supersede"] is False and o["supersede_twice"] is False
    assert o["evidence_after_supersede"] is True  # criticism of a superseded claim is still recordable
    assert o["evidence_count_on_original"] == 2  # earlier challenge was not dropped by supersession


def test_probe_supersession_claims_service_refuses_rewrite_and_delete_of_accepted_claims():
    pin_dir("PROBE_INDEX_DIR")
    from app.core.models import ClaimCreate, ClaimUpdate
    from app.claims.service import ClaimsService
    svc = ClaimsService()
    c = svc.create_claim(ClaimCreate(canonical_text="Probe claim", semantic_representation={"subject": "a", "predicate": "b"},
                                     domains=["probe"], created_by="probe_user"))
    with pytest.raises(ValueError):
        svc.update_claim(c.id, ClaimUpdate(canonical_text="rewritten"))
    with pytest.raises(ValueError):
        svc.delete_claim(c.id)
    kept = svc.get_claim(c.id)
    assert kept is not None and kept.canonical_text == "Probe claim"


@pytest.fixture
def signer(index_client, tmp_path, monkeypatch):
    from _index_signing import LinkSigner
    return LinkSigner(index_client, tmp_path, monkeypatch.setenv)


def test_probe_supersession_api_links_survive_refused_rewrite_and_delete(index_client, signer):
    """ER-02-3 (API surface): evidence links stored for an accepted claim (validly signed where the service requires it) are still
    there, unchanged, after the refused rewrite/delete, and status keeps counting them. The API has no supersession route, so
    this is the part of 'history is preserved' that the API itself can be held to."""
    claim = {"canonical_text": "Probe claim alpha", "semantic_representation": {"subject": "a", "predicate": "b"},
             "domains": ["probe"], "created_by": "probe_user"}
    ev = {"type": "experiment", "source_identifier": "doi:10.1234/api-history",
          "metadata": {"methodology": "double-blind RCT", "sample_size": 1000, "uncertainty": 0.05}, "submitted_by": "probe_user"}
    c = index_client.post("/api/v1/claims/", json=claim).json()
    e = index_client.post("/api/v1/evidence/", json=ev).json()
    signer.store_link(c["id"], e["id"], "probe_attestor")
    before_links = index_client.get(f"/api/v1/evidence/links/claim/{c['id']}").json()
    before = index_client.get(f"/api/v1/evidence/epistemic-status/{c['id']}").json()
    assert len(before_links) == 1 and before["supporting_weight"] > 0, "the link must be stored for this probe to mean anything"
    assert index_client.put(f"/api/v1/claims/{c['id']}", json={"canonical_text": "rewritten"}).status_code == 409
    assert index_client.delete(f"/api/v1/claims/{c['id']}").status_code == 409
    assert index_client.get(f"/api/v1/evidence/links/claim/{c['id']}").json() == before_links
    after = index_client.get(f"/api/v1/evidence/epistemic-status/{c['id']}").json()
    for k in ("status", "supporting_weight", "contradicting_weight", "independence_score", "robustness_score"):
        assert after[k] == before[k]
