"""Freeze manifest: sha256 of every package artifact + one root commitment. Read-only verification."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

FREEZE_SCHEMA = "ia-freeze-manifest/1"
MANIFEST_REL = "freeze/freeze-manifest.json"
_SKIP_DIRS = {"__pycache__", ".pytest_cache", "results"}
_SKIP_FILES = {MANIFEST_REL}


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def list_files(base: Path):
    out = []
    for p in sorted(base.rglob("*")):
        rel = p.relative_to(base).as_posix()
        if any(part in _SKIP_DIRS for part in p.relative_to(base).parts) or rel in _SKIP_FILES:
            continue
        if p.is_symlink():
            raise ValueError(f"symlink in freeze scope: {rel}")
        if p.is_file() and not rel.endswith(".pyc"):
            out.append(rel)
    return out


def hash_scope(base: Path):
    return {rel: hashlib.sha256((base / rel).read_bytes()).hexdigest() for rel in list_files(base)}


def root_of(body: dict) -> str:
    return hashlib.sha256(canonical(body)).hexdigest()


def build(base, meta: dict) -> dict:
    base = Path(base)
    body = {"schema": FREEZE_SCHEMA, "meta": meta, "files": hash_scope(base)}
    return {**body, "root_commitment": root_of(body)}


def verify(base, expect_root: str, manifest_path=None):
    """Return list of problems; empty means the tree equals the manifest and the manifest's root equals expect_root."""
    base = Path(base)
    mp = Path(manifest_path) if manifest_path else base / MANIFEST_REL
    if not mp.is_file():
        return ["freeze manifest missing"]
    try:
        m = json.loads(mp.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"freeze manifest unreadable: {e}"]
    probs = []
    body = {k: m.get(k) for k in ("schema", "meta", "files")}
    if m.get("schema") != FREEZE_SCHEMA:
        probs.append("bad freeze schema")
    if root_of(body) != m.get("root_commitment"):
        probs.append("manifest root_commitment does not match its own contents")
    if m.get("root_commitment") != expect_root:
        probs.append(f"root {m.get('root_commitment')} != committed {expect_root}")
    have = hash_scope(base)
    want = m.get("files") or {}
    for k in sorted(set(have) | set(want)):
        if k not in want:
            probs.append(f"unlisted file {k}")
        elif k not in have:
            probs.append(f"missing file {k}")
        elif have[k] != want[k]:
            probs.append(f"changed file {k}")
    return probs
