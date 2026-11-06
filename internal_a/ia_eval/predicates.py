"""Strict predicate operators. Each returns (ok, detail). Types are never coerced:
True != 1, 1 != 1.0, "1" != 1. MISSING is handled by the engine, not here."""
from __future__ import annotations

import re

_SHA = re.compile(r"^sha256:[0-9a-f]{64}$")


def _t(v):
    return type(v).__name__


def op_eq(obs, exp):
    if type(obs) is not type(exp):
        return False, f"type {_t(obs)} != expected {_t(exp)}"
    return (obs == exp), f"observed {obs!r} expected {exp!r}"


def op_int_eq(obs, exp):
    if type(exp) is not int:
        raise ValueError("oracle int_eq expects an int")
    if type(obs) is not int:
        return False, f"observed type {_t(obs)} is not int"
    return obs == exp, f"observed {obs} expected {exp}"


def op_is_null(obs, exp=None):
    return obs is None, f"observed {obs!r}, expected null"


def op_not_null(obs, exp=None):
    return obs is not None, f"observed {obs!r}, expected non-null"


def op_set_eq(obs, exp):
    if not isinstance(obs, list) or not all(isinstance(x, str) for x in obs):
        return False, "observed is not a list of strings"
    if len(obs) != len(set(obs)):
        return False, f"duplicates in observed {obs!r}"
    return set(obs) == set(exp), f"observed {sorted(obs)!r} expected {sorted(exp)!r}"


def op_seq_eq(obs, exp):
    if not isinstance(obs, list):
        return False, "observed is not a list"
    return obs == exp and [type(x) for x in obs] == [type(x) for x in exp], f"observed {obs!r} expected {exp!r}"


def op_len_eq(obs, exp):
    if not isinstance(obs, (list, dict, str)) or type(exp) is not int:
        return False, "len_eq needs list/dict/str and int"
    return len(obs) == exp, f"len {len(obs)} expected {exp}"


def op_in(obs, exp):
    return any(type(obs) is type(e) and obs == e for e in exp), f"observed {obs!r} not in {exp!r}"


def op_sha256_format(obs, exp=None):
    return isinstance(obs, str) and bool(_SHA.match(obs)), f"observed {obs!r} is not sha256:<64 hex>"


def op_contains_substr(obs, exp):
    return isinstance(obs, str) and exp in obs, f"{exp!r} not found in observed string"


# Operators that act on a raw text blob rather than a pointed-to value.
def op_text_lacks(text, exp):
    return exp not in text, f"forbidden text {exp!r} present"


VALUE_OPS = {
    "eq": op_eq, "int_eq": op_int_eq, "is_null": op_is_null, "not_null": op_not_null,
    "set_eq": op_set_eq, "seq_eq": op_seq_eq, "len_eq": op_len_eq, "in": op_in,
    "sha256_format": op_sha256_format, "contains_substr": op_contains_substr,
}
# Ops that are satisfied by absence rather than by a value.
PRESENCE_OPS = ("absent", "present")
EXCEPTION_OPS = ("returned", "raised_type", "raised_message_contains")
RELATION_OPS = ("eq_ref", "ne_ref")
TEXT_OPS = ("text_lacks",)
ALL_OPS = tuple(VALUE_OPS) + PRESENCE_OPS + EXCEPTION_OPS + RELATION_OPS + TEXT_OPS
