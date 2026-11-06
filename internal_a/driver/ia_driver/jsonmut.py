"""Deterministic JSON-pointer mutations on a PARSED document, with before/after evidence. Pure functions.
Used to build mutated INPUTS from frozen corpus files; every mutation is described and hashed by the caller."""
from __future__ import annotations

import copy
import hashlib
import json


class MutationError(Exception):
    pass


def canonical_bytes(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def commitment(obj) -> str:
    """'sha256:'+hex of the canonical JSON (same canonicalisation CP bounded.py:84-97, AM binding.py:17-28, PK importer.py:324-329)."""
    return "sha256:" + hashlib.sha256(canonical_bytes(obj)).hexdigest()


def _segs(ptr):
    if not isinstance(ptr, str) or not ptr.startswith("/"):
        raise MutationError(f"bad pointer {ptr!r}")
    return [s.replace("~1", "/").replace("~0", "~") for s in ptr[1:].split("/")]


def _walk(doc, segs):
    cur = doc
    for s in segs:
        if isinstance(cur, list):
            if not (s.isascii() and s.isdigit()) or int(s) >= len(cur):
                raise MutationError(f"index {s!r} not present")
            cur = cur[int(s)]
        elif isinstance(cur, dict):
            if s not in cur:
                raise MutationError(f"key {s!r} not present")
            cur = cur[s]
        else:
            raise MutationError(f"cannot descend into {type(cur).__name__}")
    return cur


def replace(doc, ptr, new, *, expect=None):
    """Return (new_doc, evidence). If expect is given the current value must equal it (no silent retargeting)."""
    d = copy.deepcopy(doc)
    segs = _segs(ptr)
    parent, last = _walk(d, segs[:-1]), segs[-1]
    old = parent[int(last)] if isinstance(parent, list) else parent[last]
    if expect is not None and old != expect:
        raise MutationError(f"{ptr}: expected {expect!r} found {old!r}")
    if isinstance(parent, list):
        parent[int(last)] = new
    else:
        parent[last] = new
    return d, {"op": "replace", "pointer": ptr, "before": old, "after": new}


def remove(doc, ptr):
    d = copy.deepcopy(doc)
    segs = _segs(ptr)
    parent, last = _walk(d, segs[:-1]), segs[-1]
    if isinstance(parent, list):
        old = parent.pop(int(last))
    else:
        old = parent.pop(last)
    return d, {"op": "remove", "pointer": ptr, "before": old}


def append(doc, ptr, value):
    d = copy.deepcopy(doc)
    target = _walk(d, _segs(ptr))
    if not isinstance(target, list):
        raise MutationError(f"{ptr} is not a list")
    target.append(copy.deepcopy(value))
    return d, {"op": "append", "pointer": ptr, "after": value}


def find_index(items, predicate):
    """Index of the unique item matching predicate; zero or several matches are errors (no guessing)."""
    hits = [i for i, x in enumerate(items) if predicate(x)]
    if len(hits) != 1:
        raise MutationError(f"expected exactly one match, found {len(hits)}")
    return hits[0]


def flip_one_hex(digest: str) -> str:
    """Change exactly one hex character of the 64-hex tail of 'sha256:<hex>' (deterministic: first char 0<->1... never equal)."""
    if not (isinstance(digest, str) and digest.startswith("sha256:") and len(digest) == 71):
        raise MutationError("not a sha256:<64 hex> digest")
    tail = digest[7:]
    c = "1" if tail[-1] == "0" else "0"
    return "sha256:" + tail[:-1] + c
