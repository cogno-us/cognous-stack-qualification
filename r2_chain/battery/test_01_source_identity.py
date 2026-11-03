"""T01: adversarial SOURCE-substitution negatives. Every case runs the SAME check functions as test_00 (source_identity.py) against a TEMP COPY of a real pinned
source (the pinned checkouts are never touched) and must be refused: REFUSED_AS_EXPECTED rows with the typed refusal code."""
import copy
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

import harness as H
import source_identity as SI

SI_DIR = Path(SI.__file__).resolve().parent


def _copy_source(tmp_path, name="replay"):
    dst = tmp_path / "copy" / H.SOURCES[name]["dir"]
    shutil.copytree(H.src(name), dst, symlinks=True)
    return dst


def _git(path, *a):
    return subprocess.run(["git", "-C", str(path), *a], capture_output=True, text=True, check=True).stdout


def _assert_baseline_clean(copy_path, name="replay"):
    spec = H.SOURCES[name]
    assert SI.check_pin(copy_path, spec)["problems"] == [] and SI.check_clean(copy_path) == [], "the temp copy must pass before it is tampered"


def _first_tracked_py(path):
    return next(l for l in _git(path, "ls-files").splitlines() if l.endswith(".py") and "/" in l)


@pytest.mark.row("S1", "SRC-a wrong-SHA tuple entry: a tuple that pins another SHA/tree than the checkout is refused", kind="negative")
def test_a_wrong_sha_tuple_entry_is_refused(tmp_path):
    path = _copy_source(tmp_path)
    spec = copy.deepcopy(H.SOURCES["replay"])
    _assert_baseline_clean(path)
    spec["sha"] = H.SOURCES["registry"]["sha"]        # tuple says: a different (real) commit
    with H.expect_refusal("SOURCE_PIN_MISMATCH", SI.SourceIdentityRefusal) as box:
        SI.require("SOURCE_PIN_MISMATCH", SI.check_pin(path, spec)["problems"])
    H.check("refused with the HEAD mismatch named", "HEAD" in str(box.exception))
    bad_tree = copy.deepcopy(H.SOURCES["replay"]); bad_tree["tree"] = "0" * 40
    with H.expect_refusal("SOURCE_PIN_MISMATCH", SI.SourceIdentityRefusal):
        SI.require("SOURCE_PIN_MISMATCH", SI.check_pin(path, bad_tree)["problems"])
    # a manifest that drops/changes one of the three SHAs is refused too
    m = copy.deepcopy(SI.load_sources()); m["sources"]["control_plane"]["sha"] = m["sources"]["control_plane"]["sha"][:-1] + "0"
    with H.expect_refusal("SOURCE_MANIFEST_MISMATCH", SI.SourceIdentityRefusal):
        SI.require("SOURCE_MANIFEST_MISMATCH", SI.check_manifest(m))
    m2 = copy.deepcopy(SI.load_sources()); m2["label"] = "CANONICAL TUPLE"
    with H.expect_refusal("SOURCE_MANIFEST_MISMATCH", SI.SourceIdentityRefusal):
        SI.require("SOURCE_MANIFEST_MISMATCH", SI.check_manifest(m2))


@pytest.mark.row("S1", "SRC-a2 a checkout at a different commit (HEAD moved) is refused even though its files are clean", kind="negative")
def test_a2_checkout_at_another_commit_is_refused(tmp_path):
    path = _copy_source(tmp_path)
    _git(path, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "--allow-empty", "-m", "synthetic extra commit")
    assert _git(path, "status", "--porcelain").strip() == ""
    with H.expect_refusal("SOURCE_PIN_MISMATCH", SI.SourceIdentityRefusal) as box:
        SI.require("SOURCE_PIN_MISMATCH", SI.check_pin(path, H.SOURCES["replay"])["problems"])
    H.check("HEAD != pin named", "HEAD" in str(box.exception))


@pytest.mark.row("S1", "SRC-b dirty file: a modified tracked file in the pinned source is detected", kind="negative")
def test_b_dirty_tracked_file_is_detected(tmp_path):
    path = _copy_source(tmp_path)
    _assert_baseline_clean(path)
    f = path / _first_tracked_py(path)
    f.write_text(f.read_text() + "\n# synthetic local edit\n")
    H.check("git status itself shows the edit", _git(path, "status", "--porcelain", "--untracked-files=no").strip() != "")
    with H.expect_refusal("SOURCE_DIRTY", SI.SourceIdentityRefusal) as box:
        SI.require("SOURCE_DIRTY", SI.check_clean(path))
    H.check("the modified file is named", f.name in str(box.exception) or "not clean" in str(box.exception))


@pytest.mark.row("S1", "SRC-c untracked shadow module placed in a source dir (package root, src dir and sitecustomize/.pth at the root) is detected", kind="negative")
@pytest.mark.parametrize("rel", ["src/agent_replay_bundle_shadow_untracked.py", "src/agent_replay_bundle/zz_shadow.py", "sitecustomize.py", "evil.pth"])
def test_c_untracked_shadow_module_is_detected(tmp_path, rel):
    path = _copy_source(tmp_path)
    _assert_baseline_clean(path)
    target = path / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# synthetic shadow\n")
    with H.expect_refusal("SOURCE_UNTRACKED_FILE", SI.SourceIdentityRefusal) as box:
        SI.require("SOURCE_UNTRACKED_FILE", SI.check_clean(path))
    H.check("the untracked file is named", Path(rel).name in str(box.exception) or "not clean" in str(box.exception))


@pytest.mark.row("S1", "SRC-c2 a git-ignored shadow file (hidden from plain `git status`) is detected", kind="negative")
def test_c2_ignored_shadow_file_is_detected(tmp_path):
    path = _copy_source(tmp_path)
    _assert_baseline_clean(path)
    (path / ".git" / "info" / "exclude").write_text("zz_ignored_shadow.py\n")
    (path / "src").mkdir(exist_ok=True)
    (path / "src" / "zz_ignored_shadow.py").write_text("# ignored shadow\n")
    H.check("plain git status --porcelain does NOT show it", _git(path, "status", "--porcelain").strip() == "")
    with H.expect_refusal("SOURCE_UNTRACKED_FILE", SI.SourceIdentityRefusal):
        SI.require("SOURCE_UNTRACKED_FILE", SI.check_clean(path))


@pytest.mark.row("S1", "SRC-d assume-unchanged / skip-worktree edit that git status hides is detected", kind="negative")
@pytest.mark.parametrize("flag,tag", [("--assume-unchanged", "h"), ("--skip-worktree", "S")])
def test_d_hidden_edit_is_detected(tmp_path, flag, tag):
    path = _copy_source(tmp_path)
    _assert_baseline_clean(path)
    rel = _first_tracked_py(path)
    _git(path, "update-index", flag, rel)
    (path / rel).write_text((path / rel).read_text() + "\n# hidden synthetic edit\n")
    H.check("precondition: plain git status does NOT show the edit", _git(path, "status", "--porcelain", "--untracked-files=no").strip() == "")
    flags = [l for l in _git(path, "ls-files", "-v").splitlines() if l[0] != "H"]
    H.check("precondition: ls-files -v carries the %r tag" % tag, any(l.startswith(tag + " ") for l in flags), flags)
    with H.expect_refusal("SOURCE_HIDDEN_EDIT", SI.SourceIdentityRefusal) as box:
        SI.require("SOURCE_HIDDEN_EDIT", SI.check_clean(path))
    H.check("flag and content difference both reported", "index flag" in str(box.exception) or "differs" in str(box.exception))
    # the content hash alone (without trusting the flags) also exposes the edit
    probs = SI.check_clean(path)
    H.check("content-hash comparison independently reports the edit", any("differs from HEAD tree blob" in x for x in probs), probs)


@pytest.mark.row("S1", "SRC-e a module whose __file__ lies outside the pinned dir is detected (stray module and a shadowing package earlier on sys.path)", kind="negative")
def test_e_module_file_outside_the_pin_is_detected(tmp_path):
    pins = SI.pinned_dirs(H.SRC_DIR)
    stray = tmp_path / "stray"
    stray.mkdir()
    (stray / "r2_stray_mod.py").write_text("X = 1\n")
    sys.path.insert(0, str(stray))
    try:
        with H.expect_refusal("SOURCE_MODULE_OUTSIDE_PIN", SI.SourceIdentityRefusal) as box:
            SI.require("SOURCE_MODULE_OUTSIDE_PIN", SI.check_module_files(SI.pinned_sys_path_entries(H.SRC_DIR), modules={"r2_stray_mod": "replay"}, pins=pins))
        H.check("the stray file is named", "r2_stray_mod" in str(box.exception))
    finally:
        sys.path.remove(str(stray))
        sys.modules.pop("r2_stray_mod", None)


@pytest.mark.row("S1", "SRC-e2 a same-named shadow package that precedes the pinned entries on sys.path wins the import and is detected (fresh interpreter)", kind="negative")
def test_e2_shadowing_package_before_the_pins_is_detected(tmp_path):
    shadow = tmp_path / "shadow"
    (shadow / "agent_replay_bundle").mkdir(parents=True)
    (shadow / "agent_replay_bundle" / "__init__.py").write_text("# synthetic shadow of the pinned Replay package\n")
    prog = textwrap.dedent("""
        import json, sys
        from pathlib import Path
        sys.path.insert(0, %r)
        import source_identity as SI
        src = Path(%r)
        entries = SI.pinned_sys_path_entries(src)
        sys.path[:0] = [%r] + [str(e) for e in entries]
        pins = SI.pinned_dirs(src)
        order = SI.check_sys_path_order(entries)
        mods = SI.check_module_files(entries, modules={"agent_replay_bundle": "replay"}, pins=pins)
        print(json.dumps({"order": order, "mods": mods, "file": sys.modules["agent_replay_bundle"].__file__}))
    """) % (str(SI_DIR), str(H.SRC_DIR), str(shadow))
    r = subprocess.run([sys.executable, "-I", "-c", prog], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    import json
    out = json.loads(r.stdout.strip().splitlines()[-1])
    H.check("the shadow package really won the import", out["file"].startswith(str(shadow)), out["file"])
    with H.expect_refusal("SOURCE_MODULE_OUTSIDE_PIN", SI.SourceIdentityRefusal):
        SI.require("SOURCE_MODULE_OUTSIDE_PIN", out["mods"])
    with H.expect_refusal("SOURCE_SYS_PATH_SHADOWED", SI.SourceIdentityRefusal):
        SI.require("SOURCE_SYS_PATH_SHADOWED", out["order"])


@pytest.mark.row("S1", "SRC-f a canonical component-lock.json reference or modification is detected", kind="negative")
def test_f_component_lock_reference_or_edit_is_detected(tmp_path, monkeypatch):
    repo = tmp_path / "qrepo"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / "component-lock.json").write_text('{"locked": true}\n')
    _git(repo, "add", "component-lock.json")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "x")
    H.check("untouched lock passes", SI.check_component_lock(repo) == [])
    (repo / "component-lock.json").write_text('{"locked": false}\n')
    with H.expect_refusal("SOURCE_COMPONENT_LOCK_TOUCHED", SI.SourceIdentityRefusal):
        SI.require("SOURCE_COMPONENT_LOCK_TOUCHED", SI.check_component_lock(repo))
    bad = copy.deepcopy(SI.load_sources()); bad["sources"]["replay"]["dir"] = "component-lock.json"
    monkeypatch.setattr(SI, "load_sources", lambda path=None: bad)
    with H.expect_refusal("SOURCE_COMPONENT_LOCK_TOUCHED", SI.SourceIdentityRefusal):
        SI.require("SOURCE_COMPONENT_LOCK_TOUCHED", SI.check_component_lock(repo))
