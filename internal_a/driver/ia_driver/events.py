"""Append-only driver event log. Kinds are the evaluator guard's allow-list: git_read, file_read,
native_call, scratch_write. Anything else is recorded as-is and makes the evaluator fail closed."""
from __future__ import annotations

import copy


class EventLog:
    def __init__(self):
        self._events = []

    def add(self, kind: str, **fields):
        if not isinstance(kind, str) or not kind:
            raise ValueError("event kind must be a non-empty string")
        ev = {"seq": len(self._events), "kind": kind, **fields}
        self._events.append(ev)
        return ev

    def extend(self, events):
        """Merge child-process events (re-sequenced; child origin recorded)."""
        for e in events:
            if not isinstance(e, dict) or not isinstance(e.get("kind"), str):
                self.add("malformed_child_event", raw=repr(e)[:200])
                continue
            fields = {k: v for k, v in e.items() if k not in ("seq", "kind")}
            self.add(e["kind"], **fields)

    def snapshot(self):
        return copy.deepcopy(self._events)

    def __len__(self):
        return len(self._events)
