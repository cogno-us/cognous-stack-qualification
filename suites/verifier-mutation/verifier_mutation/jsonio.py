"""Canonical bytes, digests and a JSON writer that can express damaged text.

The pinned profile is ``json-sort-keys-compact-utf8-no-nan-python-semantics-v0.1`` (the same recipe the ODES contract
validators and the control plane use). ``dumps`` writes ordinary JSON like ``json.dumps`` and, in addition, can emit a
duplicate object member (``Pairs``) or a verbatim token (``Raw``) so a mutation operator can damage the *text* of a record
that a Python object tree cannot express.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

PROFILE = "json-sort-keys-compact-utf8-no-nan-python-semantics-v0.1"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(data: bytes) -> str:
    return "sha256:" + sha256_hex(data)


def commitment(value: Any) -> str:
    return digest(canonical_bytes(value))


class Raw(str):
    """A token written verbatim (for example ``NaN`` or ``1e2``)."""


class Pairs(list):
    """An object written as (key, value) pairs in order; keys may repeat."""


def _scalar(value: Any, ascii_only: bool) -> str:
    return json.dumps(value, ensure_ascii=ascii_only)


def dumps(value: Any, indent: int | None = 1, ascii_only: bool = False) -> str:
    """Serialize ``value``. ``indent=None`` is compact. Key order is preserved (no sorting)."""

    def enc(v: Any, depth: int) -> str:
        if isinstance(v, Raw):
            return str(v)
        if isinstance(v, (dict, Pairs)):
            items = list(v.items()) if isinstance(v, dict) else list(v)
            if not items:
                return "{}"
            parts = [(_scalar(k, ascii_only), enc(x, depth + 1)) for k, x in items]
            if indent is None:
                return "{" + ",".join(f"{k}:{x}" for k, x in parts) + "}"
            pad, end = " " * (indent * (depth + 1)), " " * (indent * depth)
            return "{\n" + ",\n".join(f"{pad}{k}: {x}" for k, x in parts) + "\n" + end + "}"
        if isinstance(v, (list, tuple)):
            if not v:
                return "[]"
            parts = [enc(x, depth + 1) for x in v]
            if indent is None:
                return "[" + ",".join(parts) + "]"
            pad, end = " " * (indent * (depth + 1)), " " * (indent * depth)
            return "[\n" + ",\n".join(pad + p for p in parts) + "\n" + end + "]"
        return _scalar(v, ascii_only)

    return enc(value, 0)


def dump_file_bytes(value: Any, indent: int | None = 1) -> bytes:
    return (dumps(value, indent=indent) + "\n").encode("utf-8")


def parse_lenient(data: bytes) -> Any:
    """Python's own parser (last duplicate wins, NaN accepted). Used only by the harness on its own bases and for measures."""
    return json.loads(data.decode("utf-8"))
