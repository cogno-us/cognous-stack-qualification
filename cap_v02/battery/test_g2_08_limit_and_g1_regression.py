"""G2.15: the HONEST LIMIT (whole-store replacement by an older valid copy is NOT detected locally; G3) is pinned as not detected. G2.16: the G1 REGRESSION (the unmodified G1 battery's
behavioural tests N1-N4, P1, run as a separate pytest process against this G2 head) and the unchanged `none-g1` flows."""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import harness as H
from harness import AP, EFFECTIVE_LONG, admit, evidence, make_kit, sel


@pytest.mark.row("G2.15.a", "HONEST LIMIT (pinned as NOT detected): a privileged actor replacing the WHOLE store with an OLDER valid copy (generation 1, epoch 1) after the store reached epoch 2 is not detected locally: the stale epoch 1 is admitted again and the older store is accepted as authoritative. Closed by the independently anchored store of G3, not by G2.")
def test_limit_whole_store_rollback_to_an_older_valid_copy_is_not_detected(tmp_path):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    s2 = sel(2, prev=s1, effective=EFFECTIVE_LONG)
    admit(kit, s1)
    old_copy = kit.state_path.read_bytes()                       # a valid, digest-consistent copy at generation 1
    admit(kit, s2)
    newer = kit.store()
    assert newer["generation"] == 2
    # the privileged actor swaps the file (same directory, same permissions) with the older copy
    tmp = kit.dir / "swap.tmp"
    tmp.write_bytes(old_copy)
    os.replace(tmp, kit.state_path)
    assert kit.store()["generation"] == 1
    # NOT DETECTED: epoch 1 is accepted again (guard), the store is not flagged, no refusal of any kind
    m, _ = admit(kit, s1)
    assert m.selection_text == s1.selection_text
    assert kit.store()["generation"] == 1 and next(iter(kit.store()["state"]["rows"].values()))["epoch"] == 1
    evidence("g2-limit-whole-store-rollback", {"detected_locally": False, "newer_generation": newer["generation"], "restored_generation": 1,
                                                "note": "NOT detected locally; independently anchored monotonic store is G3 (anchor_reference)"})


@pytest.mark.row("G2.15.b", "the same limit by a stale directory restore (copy of store + lock + ledger from a backup) is likewise not detected")
def test_limit_directory_restore_is_not_detected(tmp_path):
    kit = make_kit(tmp_path)
    s1 = sel(1)
    admit(kit, s1)
    backup = tmp_path / "backup"
    shutil.copytree(kit.dir, backup)
    admit(kit, sel(2, prev=s1, effective=EFFECTIVE_LONG))
    shutil.rmtree(kit.dir)
    shutil.copytree(backup, kit.dir)
    admit(kit, s1)                                    # epoch 1 admitted again


# ------------------------------------------------------------------------------------------------------------------------------- G1 regression
G1_FILES = ["battery/test_n1_forged_authority.py", "battery/test_n2_scope_authority.py", "battery/test_n3_mode_config.py", "battery/test_n4_verifier_epoch.py", "battery/test_p1_positive.py"]
G1_LABEL_TEST = "battery/test_p1_positive.py::test_a_new_wrapper_has_no_memory_of_earlier_acceptance"


@pytest.mark.row("G2.16.a", "G1 REGRESSION: the UNMODIFIED G1 battery (cap_v01 N1-N4, P1 behavioural tests; its source/tripwire pin tests are excluded because they are pinned to the G1 PR head) passes against the G2 head in a separate pytest process (CAP_SRC_DIR points at the G2 checkouts). The one test that pins the old G1 docstring wording is run separately (G2.16.b)")
def test_g1_battery_behavioural_tests_pass_on_the_g2_head(tmp_path):
    g1 = H.KIT.parent / "cap_v01"
    assert (g1 / "battery" / "test_n1_forged_authority.py").is_file()
    junit = (H.EVIDENCE_DIR / "g1-regression-junit.xml") if H.EVIDENCE_DIR else tmp_path / "g1.xml"
    junit.parent.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "pytest", "-q", "-rA", "-p", "no:cacheprovider", f"--junitxml={junit}", f"--deselect={G1_LABEL_TEST}", *G1_FILES]
    env = dict(H.child_env()); env["CAP_SRC_DIR"] = str(H.SRC_DIR)
    p = subprocess.run(cmd, cwd=g1, capture_output=True, text=True, env=env, timeout=900)
    out = p.stdout + p.stderr
    if H.EVIDENCE_DIR:
        (H.EVIDENCE_DIR / "g1-regression-pytest-rA.txt").write_text(out)
    m = re.search(r"(\d+) passed", out)
    assert p.returncode == 0, out[-3000:]
    assert m and int(m.group(1)) >= 240 and "failed" not in out.splitlines()[-1] and "error" not in out.splitlines()[-1]
    print("\nG1 regression:", out.strip().splitlines()[-1])
    evidence("g1-regression-summary", {"command": " ".join(cmd[1:]), "last_line": out.strip().splitlines()[-1], "passed": int(m.group(1))})


@pytest.mark.row("G2.16.b", "FINDING (pinned): the single G1 test pinning the old docstring wording fails on the G2 head ONLY for that wording; its behavioural assertions (a new wrapper has no memory under none-g1) before the label line pass")
def test_g1_label_test_fails_only_on_the_wording(tmp_path):
    g1 = H.KIT.parent / "cap_v01"
    env = dict(H.child_env())
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", G1_LABEL_TEST], cwd=g1, capture_output=True, text=True, env=env, timeout=300)
    out = p.stdout + p.stderr
    assert p.returncode == 1 and "1 failed" in out
    assert re.search(r">\s+assert \"NO durable anti-rollback \(G2\)\" in AP.__doc__", out), out[-1500:]    # the failing line is the docstring-wording assertion, the last line of the test


@pytest.mark.row("G2.16.c", "G1 profile flows unchanged under G2: none-g1 factory flow authorizes and executes with 4 reads, writes no state, lock or ledger, and its config/snapshot stay byte-identical")
def test_none_g1_flow_is_unchanged(tmp_path, spy):
    kit = make_kit(tmp_path, bootstrap=False, backend="none-g1")
    before = H.tree(kit.dir)
    s1 = sel(1)
    flow, p, host, profile = H.build(tmp_path, kit, s1)
    d = flow.decide(p, now=H.NOW)
    assert d.result == "authorized"
    flow.execute(p, flow.records.decision(d.decision_id), adapter_id=p.adapter_id, now=H.NOW)
    assert flow.cap_selection_source.reads == 4 and spy.n == 4 and all(v.admitted for v in spy.verdicts)
    assert H.tree(kit.dir) == before
    assert json.loads((tmp_path / "destination.json").read_text())
