import hashlib
import json
import os
import shutil
from pathlib import Path

import pytest

from ia_driver import source
from ia_driver.events import EventLog
from ia_driver.source import build_identity_records, oracle_identity_keys, verify_checkout
from test_gitsafe import g, make_repo

FILES = ["src/a.py", "src/b.py"]


def verify(root, commit, tree, files=FILES, **kw):
    ev = EventLog()
    res = verify_checkout("orch", str(root), expected_commit=kw.get("ec", commit),
                          expected_tree=kw.get("et", tree), files={f: None for f in files}, events=ev)
    return res, ev


def failed(res):
    return {c["name"] for c in res["checks"] if not c["ok"]}


def test_happy_path(tmp_path):
    root, commit, tree = make_repo(tmp_path)
    res, ev = verify(root, commit, tree)
    assert res["ok"] and res["refusals"] == [] and failed(res) == set()
    assert res["observed"]["commit"] == commit and res["observed"]["tree"] == tree
    a = res["observed"]["files"]["src/a.py"]
    data = b"A = 1\n"
    assert a["sha256"] == hashlib.sha256(data).hexdigest()
    assert a["git_blob"] == a["tree_blob"] == g(root, "rev-parse", "HEAD:src/a.py")
    assert a["size"] == len(data)
    kinds = {e["kind"] for e in ev.snapshot()}
    assert kinds == {"git_read", "file_read"}
    names = {c["name"] for c in res["checks"]}
    assert {"root_real_directory", "git_dir_is_directory", "no_alternates", "git_config_safe",
            "head_matches_expected", "tree_matches_expected", "worktree_clean", "index_flags_plain",
            "no_gitlinks", "file:src/a.py", "file:src/b.py"} <= names


def test_wrong_head_and_wrong_tree(tmp_path):
    root, commit, tree = make_repo(tmp_path)
    res, _ = verify(root, commit, tree, ec="1" * 40)
    assert not res["ok"] and failed(res) == {"head_matches_expected"}
    assert res["observed"]["commit"] == commit  # observed, not copied from expected
    res, _ = verify(root, commit, tree, et="2" * 40)
    assert failed(res) == {"tree_matches_expected"} and res["observed"]["tree"] == tree


def test_malformed_expected_ids_refused_without_running_git(tmp_path):
    root, commit, tree = make_repo(tmp_path)
    res, ev = verify(root, commit, tree, ec="HEAD")
    assert failed(res) == {"expected_ids_wellformed"} and len(ev) == 0


def test_dirty_tracked_file(tmp_path):
    root, commit, tree = make_repo(tmp_path)
    (root / "README").write_text("changed\n")
    res, _ = verify(root, commit, tree)
    assert "worktree_clean" in failed(res) and not res["ok"]


def test_untracked_file(tmp_path):
    root, commit, tree = make_repo(tmp_path)
    (root / "extra.py").write_text("x\n")
    res, _ = verify(root, commit, tree)
    assert failed(res) == {"worktree_clean"}


def test_ignored_and_bytecode_file(tmp_path):
    root, commit, tree = make_repo(tmp_path, ignore="__pycache__/\n*.pyc\n")
    res, _ = verify(root, commit, tree)
    assert res["ok"]
    (root / "src" / "__pycache__").mkdir()
    (root / "src" / "__pycache__" / "a.cpython-311.pyc").write_bytes(b"\0")
    # premise: plain `git status` hides it, ours does not
    assert g(root, "status", "--porcelain") == ""
    res, _ = verify(root, commit, tree)
    assert failed(res) == {"worktree_clean"}


@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
def test_index_flags_and_hidden_substitution(tmp_path, flag):
    root, commit, tree = make_repo(tmp_path)
    g(root, "update-index", flag, "src/a.py")
    (root / "src" / "a.py").write_text("A = 9\n")
    assert g(root, "status", "--porcelain") == ""  # premise: status is fooled
    res, _ = verify(root, commit, tree)
    # flag check AND the independent blob comparison both catch it
    assert {"index_flags_plain", "file:src/a.py"} <= failed(res)
    rec = res["observed"]["files"]["src/a.py"]
    assert rec["git_blob"] != rec["tree_blob"]
    assert any("worktree blob" in c["detail"] for c in res["checks"] if c["name"] == "file:src/a.py")


def test_index_tampered_blob_detected(tmp_path):
    """Index points at a different blob than HEAD for a listed file, worktree matches the index."""
    root, commit, tree = make_repo(tmp_path)
    (root / "src" / "a.py").write_text("A = 9\n")
    g(root, "add", "src/a.py")  # staged change: index != HEAD
    res, _ = verify(root, commit, tree)
    assert "file:src/a.py" in failed(res) and "worktree_clean" in failed(res)


def test_symlink_at_listed_path(tmp_path):
    root, commit, tree = make_repo(tmp_path)
    (root / "src" / "a.py").unlink()
    os.symlink("b.py", root / "src" / "a.py")
    g(root, "add", "-A")
    g(root, "commit", "-q", "-m", "link")
    commit, tree = g(root, "rev-parse", "HEAD"), g(root, "rev-parse", "HEAD^{tree}")
    res, _ = verify(root, commit, tree)
    assert {"no_listed_symlink_in_index", "file:src/a.py"} <= failed(res)
    assert res["observed"]["files"]["src/a.py"]["missing"] is True


def test_symlink_swapped_in_worktree_only(tmp_path):
    root, commit, tree = make_repo(tmp_path)
    (root / "src" / "a.py").unlink()
    os.symlink("b.py", root / "src" / "a.py")
    res, _ = verify(root, commit, tree)
    assert "file:src/a.py" in failed(res) and res["observed"]["files"]["src/a.py"]["missing"]


def test_symlinked_directory_component_refused(tmp_path):
    root, commit, tree = make_repo(tmp_path)
    shutil.move(str(root / "src"), str(tmp_path / "elsewhere"))
    os.symlink(str(tmp_path / "elsewhere"), root / "src")
    res, _ = verify(root, commit, tree)
    assert "file:src/a.py" in failed(res)
    assert any("symlink component" in c["detail"] for c in res["checks"])


def test_unlisted_symlink_is_adverse_note_only(tmp_path):
    root, commit, tree = make_repo(tmp_path)
    os.symlink("README", root / "lnk")
    g(root, "add", "-A")
    g(root, "commit", "-q", "-m", "l")
    commit, tree = g(root, "rev-parse", "HEAD"), g(root, "rev-parse", "HEAD^{tree}")
    res, _ = verify(root, commit, tree)
    assert res["ok"] and any("lnk" in n for n in res["notes"])


def test_gitlink_anywhere(tmp_path):
    root, commit, tree = make_repo(tmp_path)
    g(root, "update-index", "--add", "--cacheinfo", f"160000,{commit},vendor/sub")
    g(root, "commit", "-q", "-m", "gitlink")
    commit, tree = g(root, "rev-parse", "HEAD"), g(root, "rev-parse", "HEAD^{tree}")
    res, _ = verify(root, commit, tree)
    assert "no_gitlinks" in failed(res) and not res["ok"]


def test_gitfile_instead_of_git_directory(tmp_path):
    root, commit, tree = make_repo(tmp_path)
    real = tmp_path / "gitdir"
    shutil.move(str(root / ".git"), str(real))
    (root / ".git").write_text(f"gitdir: {real}\n")
    res, ev = verify(root, commit, tree)
    assert failed(res) == {"git_dir_is_directory"} and len(ev) == 0  # no git ran


def test_git_dir_symlink(tmp_path):
    root, commit, tree = make_repo(tmp_path)
    real = tmp_path / "gitdir"
    shutil.move(str(root / ".git"), str(real))
    os.symlink(str(real), root / ".git")
    res, ev = verify(root, commit, tree)
    assert failed(res) == {"git_dir_is_directory"} and len(ev) == 0


def test_alternates_present(tmp_path):
    root, commit, tree = make_repo(tmp_path)
    (root / ".git" / "objects" / "info").mkdir(exist_ok=True)
    (root / ".git" / "objects" / "info" / "alternates").write_text("/somewhere/objects\n")
    res, ev = verify(root, commit, tree)
    assert "no_alternates" in failed(res) and len(ev) == 0


def test_hostile_git_config_refused_before_any_git_runs(tmp_path):
    root, commit, tree = make_repo(tmp_path)
    with open(root / ".git" / "config", "a") as fh:
        fh.write("[alias]\n\tstatus = !touch /tmp/never\n")
    res, ev = verify(root, commit, tree)
    assert failed(res) == {"git_config_safe"} and len(ev) == 0 and res["observed"]["commit"] is None


def test_root_symlink_and_relative_and_missing(tmp_path):
    root, commit, tree = make_repo(tmp_path)
    link = tmp_path / "linkroot"
    os.symlink(str(root), link)
    res, ev = verify(link, commit, tree)
    assert failed(res) == {"root_real_directory"} and len(ev) == 0
    res, _ = verify("relative/dir", commit, tree)
    assert failed(res) == {"root_real_directory"}
    res, _ = verify(tmp_path / "nope", commit, tree)
    assert failed(res) == {"root_real_directory"}
    # a non-canonical path (symlinked parent) is refused as well
    os.symlink(str(tmp_path), tmp_path / "parentlink")
    res, _ = verify(tmp_path / "parentlink" / "repo", commit, tree)
    assert failed(res) == {"root_real_directory"}


def test_missing_listed_file_is_structured_never_skipped(tmp_path):
    root, commit, tree = make_repo(tmp_path)
    (root / "src" / "b.py").unlink()
    res, _ = verify(root, commit, tree, files=FILES + ["src/never_existed.py"])
    assert res["observed"]["files"]["src/b.py"]["missing"] is True
    assert res["observed"]["files"]["src/never_existed.py"]["missing"] is True
    assert {"file:src/b.py", "file:src/never_existed.py", "worktree_clean"} <= failed(res)
    assert "sha256" in res["observed"]["files"]["src/a.py"]
    assert set(res["observed"]["files"]) == set(FILES) | {"src/never_existed.py"}


def test_malformed_listed_paths_refused(tmp_path):
    root, commit, tree = make_repo(tmp_path)
    res, _ = verify(root, commit, tree, files=["../x", "/etc/passwd", "a//b", "src\\a.py"])
    assert "listed_paths_wellformed" in failed(res)
    assert all(v.get("missing") for v in res["observed"]["files"].values())


def test_file_with_glob_chars_is_literal(tmp_path):
    root, commit, tree = make_repo(tmp_path, files={"a*.py": "x\n", "ab.py": "y\n"})
    res, _ = verify(root, commit, tree, files=["a*.py"])
    assert res["ok"] and res["observed"]["files"]["a*.py"]["git_blob"] == g(root, "rev-parse", "HEAD:a*.py")


# ---- identity records -------------------------------------------------------------------

def _two(tmp_path):
    r1 = make_repo(tmp_path, "r1")
    r2 = make_repo(tmp_path, "r2", files={"p.py": "P\n"})
    return r1, r2


def test_build_identity_records_uses_only_observed_values(tmp_path):
    (root1, c1, t1), (root2, c2, t2) = _two(tmp_path)
    res1, _ = verify(root1, c1, t1)
    res2 = verify_checkout("am", str(root2), expected_commit="3" * 40, expected_tree="4" * 40,
                           files={"p.py": None}, events=EventLog())
    rec = build_identity_records({"orchestrator": res1, "action_manifest": res2},
                                 {"orchestrator": "orch", "action_manifest": "am"})
    assert rec["source_identity"]["commits"] == {"orchestrator": c1, "action_manifest": c2}
    assert rec["source_identity"]["trees"] == {"orchestrator": t1, "action_manifest": t2}
    assert "3" * 40 not in json.dumps(rec) and "4" * 40 not in json.dumps(rec)
    sha = rec["file_identity"]["sha256"]
    assert sha["orch:src/a.py"] == hashlib.sha256(b"A = 1\n").hexdigest()
    assert sha["am:p.py"] == hashlib.sha256(b"P\n").hexdigest()
    assert rec["file_identity"]["git_blob"]["am:p.py"] == g(root2, "rev-parse", "HEAD:p.py")
    assert any("action_manifest" in f for f in rec["flags"])  # refused checkout is flagged


def test_missing_file_omitted_and_flagged(tmp_path):
    root, commit, tree = make_repo(tmp_path)
    (root / "src" / "a.py").unlink()
    res, _ = verify(root, commit, tree)
    rec = build_identity_records({"orchestrator": res}, {"orchestrator": "orch"})
    assert "orch:src/a.py" not in rec["file_identity"]["sha256"]
    assert "orch:src/a.py" not in rec["file_identity"]["git_blob"]
    assert "orch:src/b.py" in rec["file_identity"]["sha256"]
    assert any("orch:src/a.py" in f for f in rec["flags"])


def test_unobserved_commit_omitted(tmp_path):
    root, commit, tree = make_repo(tmp_path)
    (root / ".git" / "objects" / "info").mkdir(exist_ok=True)
    (root / ".git" / "objects" / "info" / "alternates").write_text("x\n")
    res, _ = verify(root, commit, tree)
    rec = build_identity_records({"orchestrator": res}, {"orchestrator": "orch"})
    assert rec["source_identity"] == {"commits": {}, "trees": {}} and rec["flags"]


def test_unknown_component_prefix_is_error():
    with pytest.raises(ValueError):
        build_identity_records({"mystery": {"observed": {}}}, {"orchestrator": "orch"})


def test_oracle_keys_are_value_blind():
    oracle = {"cases": [
        {"id": "QA-S1", "observations": [
            {"id": "QA-S1.1", "expected": {"orchestrator": "SECRETVAL", "evidence_pack": "SECRETVAL"}}]},
        {"id": "QA-S2", "observations": [
            {"id": "QA-S2.1", "expected": {"orch:a/b.py": "SECRETHASH", "pk:c.json": "SECRETHASH"}}]}]}
    keys = oracle_identity_keys(oracle)
    assert keys["paths"] == {"evidence_pack": ["c.json"], "orchestrator": ["a/b.py"]}
    assert "SECRET" not in json.dumps(keys)
    oracle["cases"][1]["observations"][0]["expected"]["zz:x"] = "v"
    with pytest.raises(ValueError):
        oracle_identity_keys(oracle)


def test_real_oracle_key_sets_cover_five_components():
    p = Path(__file__).resolve().parents[2] / "oracle" / "oracle.v1.json"
    keys = oracle_identity_keys(json.loads(p.read_text()))
    assert set(keys["components"]) == set(source.DEFAULT_PREFIXES)
    assert sum(len(v) for v in keys["paths"].values()) == 78
