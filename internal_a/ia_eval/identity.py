"""Pure-Python content identity (no subprocess, no git binary): git blob ids and sha256 of files."""
from __future__ import annotations

import hashlib
from pathlib import Path


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()  # nosec - git object id, not a security hash


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_files(root, relpaths):
    """Read-only: {relpath: {"sha256":..., "git_blob":..., "size":...}} for files under root.
    A missing file is recorded as {"missing": True}; it is never skipped."""
    root = Path(root)
    out = {}
    for rel in relpaths:
        p = (root / rel)
        if ".." in Path(rel).parts or Path(rel).is_absolute():
            raise ValueError(f"refusing path outside root: {rel}")
        if p.is_symlink() or not p.is_file():
            out[rel] = {"missing": True}
            continue
        data = p.read_bytes()
        out[rel] = {"sha256": sha256_hex(data), "git_blob": git_blob_sha1(data), "size": len(data)}
    return out
