"""No-effect guard: the observation bundle's driver event log must contain only read-only
kinds and only oracle-allowed native calls. Anything else fails closed (CA05)."""
from __future__ import annotations

import re

ALLOWED_KINDS = frozenset({"git_read", "file_read", "native_call", "scratch_write"})
# execute()/reconcile()/apply() style effect paths, network and payment verbs.
_EFFECT_NAME = re.compile(r"(^|[._])(execute|reconcile|apply|run_effect|send|deliver|submit|commit_effect|charge|refund_issue|post|put|delete)($|[._(])", re.I)


def check_events(events, allowed_native_calls):
    """Return a list of violation strings; empty means clean. Unknown shape is a violation."""
    v = []
    if not isinstance(events, list):
        return ["driver_events missing or not a list (cannot show absence of effects)"]
    allowed = set(allowed_native_calls)
    for i, e in enumerate(events):
        if not isinstance(e, dict) or not isinstance(e.get("kind"), str):
            v.append(f"event[{i}] malformed")
            continue
        kind = e["kind"]
        if kind not in ALLOWED_KINDS:
            v.append(f"event[{i}] out-of-scope kind {kind!r}")
            continue
        if kind == "native_call":
            name = e.get("callable")
            if not isinstance(name, str) or name not in allowed:
                v.append(f"event[{i}] native_call {name!r} is not in the oracle allow-list")
            elif _EFFECT_NAME.search(name):
                v.append(f"event[{i}] native_call {name!r} looks like an effect path")
        if kind == "scratch_write" and not str(e.get("path", "")).startswith("scratch/"):
            v.append(f"event[{i}] write outside scratch: {e.get('path')!r}")
    return v
