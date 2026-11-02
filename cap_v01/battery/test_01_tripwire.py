"""TRIPWIRE: the Control Plane change under qualification is EXACTLY the declared six files on top of the declared base, the F4 PoC bounded.py is untouched, and the Registry and
Replay checkouts are at their pins with clean trees. Needs a FULL-HISTORY Control Plane checkout (the base commit must be present). Prints the SHA-256 manifest of the changed files."""
import hashlib
import os
from pathlib import Path

import pytest

import harness as H

CP_BASE = H.SOURCES["control_plane_base"]["sha"]
CP_HEAD = H.SOURCES["control_plane"]["sha"]
EXPECTED = sorted(H.SPEC["tripwire"]["cp_changed_files_exactly"])
BOUNDED = H.SPEC["tripwire"]["bounded_py"]


def cp_git(*args):
    return H.git("control_plane", *args)


@pytest.mark.row("T", "tripwire: the base commit is present (full history) and is an ancestor of the G1 head")
def test_cp_checkout_has_full_history_and_base_is_ancestor_of_head():
    if os.environ.get("CAP_REQUIRE_FULL_HISTORY") == "1":  # set by the hosted workflow (fetch-depth: 0)
        assert cp_git("rev-parse", "--is-shallow-repository") == "false"
    assert cp_git("cat-file", "-t", CP_BASE) == "commit"
    cp_git("merge-base", "--is-ancestor", CP_BASE, CP_HEAD)  # raises (check=True) when not an ancestor
    assert cp_git("rev-parse", "HEAD") == CP_HEAD


@pytest.mark.row("T", "tripwire: CP G1 head vs base 8b97d32f changes EXACTLY six files, only added or modified (no delete, rename, copy or type change)")
def test_changed_file_set_is_exactly_the_declared_six():
    status = cp_git("diff", "--no-renames", "--name-status", CP_BASE, CP_HEAD).splitlines()
    rows = sorted(line.split("\t", 1)[1] for line in status)
    assert rows == EXPECTED, rows
    assert {line.split("\t", 1)[0] for line in status} <= {"A", "M"}, status
    assert cp_git("diff", "--no-renames", "--name-only", CP_BASE, CP_HEAD).splitlines().__len__() == 6


@pytest.mark.row("T", "tripwire: the working tree of the Control Plane checkout is the G1 head (nothing modified or untracked), so the files tested are the files fingerprinted")
def test_cp_working_tree_is_clean_at_the_head():
    assert cp_git("status", "--porcelain", "--untracked-files=all") == ""
    assert cp_git("diff", "--name-only", "HEAD") == ""


@pytest.mark.row("T", "tripwire: src/agent_control_plane/bounded.py is unchanged (sha256 4052ff87..., git blob b5329804...), byte-identical to the base")
def test_bounded_py_is_untouched():
    path = BOUNDED["path"]
    data = (H.src("control_plane") / path).read_bytes()
    assert hashlib.sha256(data).hexdigest().startswith(BOUNDED["sha256_prefix"])
    blob_head, blob_base = cp_git("rev-parse", f"{CP_HEAD}:{path}"), cp_git("rev-parse", f"{CP_BASE}:{path}")
    assert blob_head == blob_base and blob_head.startswith(BOUNDED["git_blob_prefix"])
    assert cp_git("hash-object", path) == blob_head
    assert cp_git("diff", "--name-only", CP_BASE, CP_HEAD, "--", path) == ""


@pytest.mark.parametrize("name", ["registry", "replay"])
@pytest.mark.row("T", "tripwire: Registry and Replay checkouts are at their pins and the trees are clean (0 files changed, none untracked)")
def test_registry_and_replay_are_at_their_pins_with_clean_trees(name):
    assert H.git(name, "rev-parse", "HEAD") == H.SOURCES[name]["sha"]
    assert H.git(name, "diff", "--name-only", "HEAD") == ""
    assert H.git(name, "diff", "--name-only", "--cached") == ""
    assert H.git(name, "status", "--porcelain", "--untracked-files=all") == ""


@pytest.mark.row("T", "SHA-256 manifest of the six changed Control Plane files at the head (printed; written to $CAP_EVIDENCE_DIR/cp-changed-files.sha256 when set)")
def test_sha256_manifest_of_the_changed_files():
    lines = []
    for rel in EXPECTED:
        data = (H.src("control_plane") / rel).read_bytes()
        blob = cp_git("rev-parse", f"{CP_HEAD}:{rel}")
        assert cp_git("hash-object", rel) == blob
        lines.append(f"{hashlib.sha256(data).hexdigest()}  {rel}  (git blob {blob})")
    text = "\n".join(lines) + "\n"
    print("\n" + text)
    out = os.environ.get("CAP_EVIDENCE_DIR")
    if out:
        Path(out).mkdir(parents=True, exist_ok=True)
        (Path(out) / "cp-changed-files.sha256").write_text(text)
    assert len(lines) == 6
