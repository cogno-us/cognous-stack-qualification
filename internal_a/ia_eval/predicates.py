"""Strict predicate operators. Each returns (ok, detail). Types are never coerced:
True != 1, 1 != 1.0, "1" != 1. MISSING is handled by the engine, not here."""
from __future__ import annotations

import re

_SHA = re.compile(r"^sha256:[0-9a-f]{64}$")


def _t(v):
    return type(v).__name__


def deq(a, b):
    """Deep, type-strict equality: True != 1, 1 != 1.0, [True] != [1], key sets must match."""
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(deq(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(deq(x, y) for x, y in zip(a, b))
    return a == b


def _diff_keys(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        ks = sorted(set(a) | set(b), key=str)
        return [k for k in ks if k not in a or k not in b or not deq(a[k], b[k])][:12]
    return None


def op_eq(obs, exp):
    if deq(obs, exp):
        return True, "equal"
    if type(obs) is not type(exp):
        return False, f"type {_t(obs)} != expected {_t(exp)}"
    dk = _diff_keys(obs, exp)
    if dk is not None:
        return False, f"differing keys: {dk}"
    return False, f"observed {obs!r} expected {exp!r}"


def op_ne(obs, exp):
    return (not deq(obs, exp)), f"observed {obs!r} must differ from {exp!r}"


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
    return deq(obs, exp), f"observed {obs!r} expected {exp!r}"


def op_len_eq(obs, exp):
    if not isinstance(obs, (list, dict, str)) or type(exp) is not int:
        return False, "len_eq needs list/dict/str and int"
    return len(obs) == exp, f"len {len(obs)} expected {exp}"


def op_in(obs, exp):
    if not isinstance(exp, list):
        return False, "oracle 'in' expects a list"
    return any(deq(obs, e) for e in exp), f"observed {obs!r} not in {exp!r}"


def op_list_contains(obs, exp):
    if not isinstance(obs, list):
        return False, "observed is not a list"
    return any(deq(x, exp) for x in obs), f"{exp!r} not in observed list {obs!r}"


def subset(exp, obs):
    """exp is a deep subset of obs: dicts recurse by key; everything else is deep-strict-equal."""
    if isinstance(exp, dict):
        return isinstance(obs, dict) and all(k in obs and subset(v, obs[k]) for k, v in exp.items())
    return deq(exp, obs)


def op_any_item_matches(obs, exp):
    """True iff some dict item has every expected key with a deep-equal value."""
    if not isinstance(obs, list) or not isinstance(exp, dict) or not exp:
        return False, "any_item_matches needs a list and a non-empty expected object"
    for it in obs:
        if isinstance(it, dict) and subset(exp, it):
            return True, "matching item found"
    return False, f"no item matches {exp!r}"


def op_none_item_matches(obs, exp):
    if not isinstance(obs, list) or not isinstance(exp, dict) or not exp:
        return False, "none_item_matches needs a list and a non-empty expected object"
    for it in obs:
        if isinstance(it, dict) and subset(exp, it):
            return False, f"forbidden item present: {exp!r}"
    return True, "no matching item"


def op_sha256_format(obs, exp=None):
    return isinstance(obs, str) and bool(_SHA.match(obs)), f"observed {obs!r} is not sha256:<64 hex>"


def op_contains_substr(obs, exp):
    return isinstance(obs, str) and exp in obs, f"{exp!r} not found in observed string"



VALUE_OPS = {
    "eq": op_eq, "int_eq": op_int_eq, "is_null": op_is_null, "not_null": op_not_null,
    "set_eq": op_set_eq, "seq_eq": op_seq_eq, "len_eq": op_len_eq, "in": op_in,
    "sha256_format": op_sha256_format, "contains_substr": op_contains_substr,
    "ne": op_ne, "list_contains": op_list_contains, "any_item_matches": op_any_item_matches,
    "none_item_matches": op_none_item_matches,
}
# Ops that are satisfied by absence rather than by a value.
PRESENCE_OPS = ("absent", "present")
EXCEPTION_OPS = ("returned", "raised_type", "raised_message_contains", "raised_message_equals")
RELATION_OPS = ("eq_ref", "ne_ref")
ALL_OPS = tuple(VALUE_OPS) + PRESENCE_OPS + EXCEPTION_OPS + RELATION_OPS
