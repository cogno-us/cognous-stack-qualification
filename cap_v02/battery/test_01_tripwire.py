"""TRIPWIRE: the Control Plane change under qualification is EXACTLY the declared six files on top of merged G1 main (2ebc3e66), bounded.py is untouched, the Registry and Replay
checkouts are at their pins with clean trees. Needs a FULL-HISTORY Control Plane checkout in the hosted run (CAP_REQUIRE_FULL_HISTORY=1). Records the SHA-256 manifest of the changed files."""
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


@pytest.mark.row("T", "tripwire: the base (merged G1 main 2ebc3e66) is present and is an ancestor of the G2 head; full history is enforced in the hosted run")
def test_cp_checkout_has_the_base_as_ancestor_of_head():
    if os.environ.get("CAP_REQUIRE_FULL_HISTORY") == "1":
        assert cp_git("rev-parse", "--is-shallow-repository") == "false"
    assert cp_git("cat-file", "-t", CP_BASE) == "commit"
    cp_git("merge-base", "--is-ancestor", CP_BASE, CP_HEAD)
    assert cp_git("rev-parse", "HEAD") == CP_HEAD


@pytest.mark.row("T", "tripwire: G2 head vs merged G1 main changes EXACTLY the six declared files, only added or modified")
def test_changed_file_set_is_exactly_the_declared_six():
    status = cp_git("diff", "--no-renames", "--name-status", CP_BASE, CP_HEAD).splitlines()
    rows = sorted(line.split("\t", 1)[1] for line in status)
    assert rows == EXPECTED, rows
    assert {line.split("\t", 1)[0] for line in status} <= {"A", "M"}, status
    assert len(rows) == 6


@pytest.mark.row("T", "tripwire: the Control Plane working tree is the head (nothing modified or untracked)")
def test_cp_working_tree_is_clean_at_the_head():
    assert cp_git("status", "--porcelain", "--untracked-files=all") == ""
    assert cp_git("diff", "--name-only", "HEAD") == ""


@pytest.mark.row("T", "tripwire: bounded.py unchanged (sha256 4052ff87..., git blob b5329804...), byte-identical to the base")
def test_bounded_py_is_untouched():
    path = BOUNDED["path"]
    data = (H.src("control_plane") / path).read_bytes()
    assert hashlib.sha256(data).hexdigest().startswith(BOUNDED["sha256_prefix"])
    blob_head, blob_base = cp_git("rev-parse", f"{CP_HEAD}:{path}"), cp_git("rev-parse", f"{CP_BASE}:{path}")
    assert blob_head == blob_base and blob_head.startswith(BOUNDED["git_blob_prefix"])
    assert cp_git("hash-object", path) == blob_head
    assert cp_git("diff", "--name-only", CP_BASE, CP_HEAD, "--", path) == ""


@pytest.mark.parametrize("name", ["registry", "replay"])
@pytest.mark.row("T", "tripwire: Registry and Replay at their pins with clean trees")
def test_registry_and_replay_are_at_their_pins_with_clean_trees(name):
    assert H.git(name, "rev-parse", "HEAD") == H.SOURCES[name]["sha"]
    assert H.git(name, "diff", "--name-only", "HEAD") == ""
    assert H.git(name, "diff", "--name-only", "--cached") == ""
    assert H.git(name, "status", "--porcelain", "--untracked-files=all") == ""


@pytest.mark.row("T", "SHA-256 manifest of the six changed Control Plane files at the head (printed; written to $CAP_EVIDENCE_DIR/cp-changed-files.sha256)")
def test_sha256_manifest_of_the_changed_files():
    lines = []
    for rel in EXPECTED:
        data = (H.src("control_plane") / rel).read_bytes()
        blob = cp_git("rev-parse", f"{CP_HEAD}:{rel}")
        assert cp_git("hash-object", rel) == blob
        lines.append(f"{hashlib.sha256(data).hexdigest()}  {rel}  (git blob {blob})")
    text = "\n".join(lines) + "\n"
    print("\n" + text)
    if H.EVIDENCE_DIR:
        H.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        (H.EVIDENCE_DIR / "cp-changed-files.sha256").write_text(text)
    assert len(lines) == 6
