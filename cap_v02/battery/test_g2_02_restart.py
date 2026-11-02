"""G2.6: fresh-process restart retains the floors. Every step runs in a REAL separate `python` process (child_worker.py) that loads the profile and the persisted store from disk;
nothing is carried in memory between steps. The transcript (pids, outcomes, state digests) is recorded as evidence."""
import os

import pytest

import harness as H
from harness import EFFECTIVE_LONG, SELECTION_ID, admit, child_admit, child_read, evidence, make_kit, refused_admit, sel, snapshot_doc


def step(log, name, res, kit):
    log.append({"step": name, "pid": res["out"].get("pid") if res["out"] else None, "returncode": res["returncode"], "outcome": {k: v for k, v in (res["out"] or {}).items() if k not in ("envelope",)},
                "store_sha256": H.sha256_hex(kit.store_bytes())})


@pytest.mark.row("G2.6.a", "restart demonstration: process A admits epoch 1, B admits renewal epoch 2, C is refused epoch 1, D re-presents epoch 2 (no write), E reads the store; five different PIDs, none the test process")
def test_floors_survive_fresh_processes(tmp_path):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    s2 = sel(2, prev=s1, effective=EFFECTIVE_LONG)
    log = []
    a = child_admit(kit, s1); step(log, "A admit epoch1", a, kit)
    assert a["returncode"] == 0 and a["out"]["ok"] is True, a
    after_a = kit.store_bytes()
    b = child_admit(kit, s2); step(log, "B admit epoch2 (renewal)", b, kit)
    assert b["out"]["ok"] is True, b
    after_b = kit.store_bytes()
    assert after_b != after_a
    c_ = child_admit(kit, s1); step(log, "C re-present epoch1 (stale)", c_, kit)
    assert c_["out"]["ok"] is False and c_["out"]["code"] == "freshness_refused" and c_["out"]["registry_code"] == "selection_epoch_stale", c_
    assert kit.store_bytes() == after_b
    d = child_admit(kit, s2); step(log, "D re-present epoch2 (guard, no write)", d, kit)
    assert d["out"]["ok"] is True and kit.store_bytes() == after_b
    e = child_read(kit); step(log, "E read_state", e, kit)
    env = e["out"]["envelope"]
    assert env["generation"] == 2 and next(iter(env["state"]["rows"].values()))["epoch"] == 2 and env == kit.store()
    pids = {x["pid"] for x in log}
    assert len(pids) == 5 and os.getpid() not in pids
    evidence("g2-6-restart-demonstration", {"profile_dir": "<tmp>", "transcript": log, "persisted_after_A": {"sha256": H.sha256_hex(after_a)}, "persisted_after_B": {"sha256": H.sha256_hex(after_b)},
                                            "final_envelope": env})


@pytest.mark.row("G2.6.b", "the test process itself never held state: after children advanced the store to epoch 3, a NEW in-process wrapper (fresh objects) refuses epoch 1 and 2 and re-admits epoch 3")
def test_parent_wrapper_sees_only_the_file(tmp_path):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    s2 = sel(2, prev=s1, effective=EFFECTIVE_LONG)
    s3 = sel(3, prev=s2, effective=EFFECTIVE_LONG)
    for s_ in (s1, s2, s3):
        assert child_admit(kit, s_)["out"]["ok"] is True
    refused_admit(kit, s1, "freshness_refused", registry_code="selection_epoch_stale")
    refused_admit(kit, s2, "freshness_refused", registry_code="selection_epoch_stale")
    admit(kit, s3)
    assert kit.store()["generation"] == 3


@pytest.mark.row("G2.6.c", "the stored snapshot floor and the persisted revocation survive restart: a child on the newer snapshot advances the store, then a fresh in-process wrapper and a fresh child both refuse the older snapshot")
def test_snapshot_floor_survives_restart(tmp_path):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    kit.rotate(snapshot_doc(version=4))
    assert child_admit(kit, s1)["out"]["ok"] is True
    assert kit.store()["state"]["snapshot"]["version"] == 4
    kit.rotate(snapshot_doc(version=2))
    refused_admit(kit, s1, "registry_not_applied", registry_code="trust_snapshot_version_stale")
    r = child_admit(kit, s1)
    assert r["out"]["code"] == "registry_not_applied" and r["out"]["registry_code"] == "trust_snapshot_version_stale"


@pytest.mark.row("G2.6.d", "child exit status and stderr are clean on success and on a typed refusal (no traceback): refusals are typed results, not crashes")
def test_children_exit_cleanly_with_typed_results(tmp_path):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    ok = child_admit(kit, s1)
    assert ok["returncode"] == 0 and ok["stderr"] == "" and ok["out"]["ok"] is True
    kit.state_path.unlink()
    miss = child_admit(kit, s1)
    assert miss["returncode"] == 0 and miss["stderr"] == "" and miss["out"]["code"] == "state_missing"
