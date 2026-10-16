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
