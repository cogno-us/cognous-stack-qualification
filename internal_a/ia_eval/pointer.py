"""RFC 6901-style pointer lookup with an explicit MISSING sentinel -- no defaults, ever."""
from __future__ import annotations


class _Missing:
    def __repr__(self):
        return "MISSING"

    def __bool__(self):
        return False


MISSING = _Missing()


def resolve(doc, pointer):
    if not isinstance(pointer, str) or (pointer != "" and not pointer.startswith("/")):
        raise ValueError(f"invalid pointer {pointer!r}")
    cur = doc
    if pointer == "":
        return cur
    for raw in pointer[1:].split("/"):
        seg = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(cur, dict):
            if seg not in cur:
                return MISSING
            cur = cur[seg]
        elif isinstance(cur, list):
            if not (seg.isascii() and seg.isdigit()) or (len(seg) > 1 and seg[0] == "0"):
                return MISSING
            i = int(seg)
            if i >= len(cur):
                return MISSING
            cur = cur[i]
        else:
            return MISSING
    return cur
