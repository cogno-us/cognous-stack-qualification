"""Synthetic, oracle-shaped observation bundles for evaluator self-tests. STUBS ONLY:
nothing here imports or calls a subject component. A golden stub is synthesised from the oracle's
own expected values, so it proves evaluator logic (not native behaviour). Mutations then break it."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORACLE_PATH = HERE.parent / "oracle" / "oracle.v1.json"


def _sha(b): return hashlib.sha256(b).hexdigest()


def set_pointer(doc, ptr, value):
    """Create/overwrite value at an RFC6901 pointer, creating dicts/lists as needed."""
    if ptr == "":
        return value
    segs = [s.replace("~1", "/").replace("~0", "~") for s in ptr[1:].split("/")]
    cur, parent, key = doc, None, None
    for i, seg in enumerate(segs):
        last = i == len(segs) - 1
        nxt_is_idx = (not last) and segs[i + 1].isdigit()
        if seg.isdigit():
            idx = int(seg)
            if not isinstance(cur, list):
                cur = []
                _assign(parent, key, cur)
            while len(cur) <= idx:
                cur.append(None)
            if last:
                cur[idx] = value
            else:
                if not isinstance(cur[idx], (dict, list)):
                    cur[idx] = [] if nxt_is_idx else {}
                parent, key, cur = cur, idx, cur[idx]
        else:
            if not isinstance(cur, dict):
                cur = {}
                _assign(parent, key, cur)
            if last:
                cur[seg] = value
            else:
                if not isinstance(cur.get(seg), (dict, list)):
                    cur[seg] = [] if nxt_is_idx else {}
                parent, key, cur = cur, seg, cur[seg]
    return doc


def _assign(parent, key, val):
    if parent is None:
        raise ValueError("cannot reshape the document root")
    parent[key] = val


def _get(doc, ptr):
    cur = doc
    if ptr == "":
        return cur
    for seg in ptr[1:].split("/"):
        cur = cur[int(seg)] if isinstance(cur, list) else cur[seg]
    return cur


class Stub:
    """In-memory observation bundle. .raw: relpath -> JSON object; .cases: id -> case dict."""

    def __init__(self, oracle: dict):
        self.oracle = oracle
        self.raw, self.cases = {}, {}
        self.driver_events = [{"kind": "file_read", "path": "oracle/oracle.v1.json"}]
        self.driver_events += [{"kind": "native_call", "callable": c} for c in oracle["allowed_native_calls"][:3]]
        self.orchestrator_status = {}
        self._build()

    # ---- golden construction -------------------------------------------------
    def _path(self, cid, boundary, kind="raw"):
        return f"raw/{cid}.{boundary}.{kind}.json"

    def _build(self):
        for c in self.oracle["cases"]:
            if c["class"] in ("INFO", "NA"):
                continue
            case = {"executed": True, "boundaries": {}, "adverse_notes": []}
            self.cases[c["id"]] = case
            per_boundary = {}
            for ob in c["observations"]:
                per_boundary.setdefault(ob["boundary"], []).append(ob)
            for b, obs in per_boundary.items():
                if any(o["op"].startswith("raised_") for o in obs):
                    exc = {"type": "", "message": ""}
                    for o in obs:
                        if o["op"] == "raised_type":
                            exc["type"] = o["expected"]
                        else:
                            exc["message"] = o["expected"]
                    p = self._path(c["id"], b, "exc")
                    self.raw[p] = exc
                    case["boundaries"][b] = {"outcome": "raised", "exception_raw": p, "entrypoint": c["entrypoint"]}
                else:
                    p = self._path(c["id"], b)
                    self.raw[p] = {}
                    case["boundaries"][b] = {"outcome": "returned", "raw": p, "entrypoint": c["entrypoint"]}
            # direct value synthesis first, relations second
            direct = [o for o in c["observations"] if o["op"] not in ("eq_ref", "ne_ref", "returned") and not o["op"].startswith("raised_")]
            for ob in sorted(direct, key=lambda o: o["op"] == "commitment_of"):   # commitments last
                self._synth(case, ob)
            for ob in c["observations"]:
                if ob["op"] in ("eq_ref", "ne_ref"):
                    self._synth_rel(case, ob)

    def _doc(self, case, b):
        return self.raw[case["boundaries"][b]["raw"]]

    def _synth(self, case, ob):
        b, ptr, op, exp = ob["boundary"], ob.get("pointer"), ob["op"], ob.get("expected")
        p = case["boundaries"][b]["raw"]
        d = self.raw[p]
        def put(v):
            self.raw[p] = set_pointer(d if ptr != "" else {}, ptr, v)
        if op in ("eq", "int_eq", "seq_eq", "set_eq"):
            put(copy.deepcopy(exp))
        elif op == "is_null":
            put(None)
        elif op == "not_null":
            put("x")
        elif op == "len_eq":
            put(["x"] * exp if True else None)
        elif op == "sha256_format":
            put("sha256:" + "a" * 64)
        elif op == "contains_substr":
            put(exp)
        elif op == "in":
            put(copy.deepcopy(exp[0]))
        elif op == "list_contains":
            put([copy.deepcopy(exp)])
        elif op == "present":
            put("x")
        elif op == "any_item_matches":
            try:
                lst = _get(d, ptr)
            except (KeyError, IndexError, TypeError):
                lst = None
            lst = lst if isinstance(lst, list) else []
            lst = [x for x in lst if x != "x"]
            lst.append(copy.deepcopy(exp))
            put(lst)
        elif op == "none_item_matches":
            try:
                lst = _get(d, ptr)
            except (KeyError, IndexError, TypeError):
                lst = None
            put([x for x in (lst if isinstance(lst, list) else [])] or [{"code": "OTHER"}])
        elif op == "absent":
            pass
        elif op == "commitment_of":
            from ia_eval.identity import commitment
            try:
                src = _get(d, exp)
            except (KeyError, IndexError, TypeError):
                src = {"k": "v"}
                d = set_pointer(d, exp, src)
            put(commitment(src))
        else:
            raise ValueError(f"stub cannot synthesise op {op}")

    def _synth_rel(self, case, ob):
        b, ptr, ref = ob["boundary"], ob["pointer"], ob["expected"]
        bres = case["boundaries"][b]
        tgt = case["boundaries"][ref["boundary"]]
        if ptr.startswith("#input:"):
            bres.setdefault("inputs", {})[ptr[len("#input:"):]] = tgt["raw"]
            return
        if ref["pointer"] == "#raw_sha256":
            raise ValueError("unsupported relation shape in stub")
        if ref["pointer"] == "":
            self.raw[bres["raw"]] = copy.deepcopy(self.raw[tgt["raw"]])
            return
        try:
            tv = _get(self.raw[tgt["raw"]], ref["pointer"])
        except (KeyError, IndexError, TypeError):
            tv = "sha256:" + "c" * 64
            self.raw[tgt["raw"]] = set_pointer(self.raw[tgt["raw"]], ref["pointer"], tv)
        if ob["op"] == "eq_ref":
            self.raw[bres["raw"]] = set_pointer(self.raw[bres["raw"]], ptr, copy.deepcopy(tv))
        else:
            self.raw[bres["raw"]] = set_pointer(self.raw[bres["raw"]], ptr, "DIFFERENT-" + str(tv))

    # ---- serialisation -------------------------------------------------------
    def write(self, dest, *, hash_overrides=None, skip_files=(), extra_files=None):
        dest = Path(dest)
        (dest / "raw").mkdir(parents=True, exist_ok=True)
        index = {}
        for rel, obj in self.raw.items():
            data = (json.dumps(obj, sort_keys=True, indent=1) + "\n").encode()
            index[rel] = _sha(data)
            if rel not in skip_files:
                (dest / rel).write_bytes(data)
        index.update(hash_overrides or {})
        for rel, data in (extra_files or {}).items():
            (dest / rel).write_bytes(data)
        bundle = {"schema": "ia-observation-bundle/1", "raw_index": index, "cases": self.cases, "driver_events": self.driver_events,
                  "orchestrator_status": self.orchestrator_status}
        bdata = (json.dumps(bundle, sort_keys=True, indent=1) + "\n").encode()
        (dest / "bundle.json").write_bytes(bdata)
        return _sha(bdata)


def load_oracle():
    b = ORACLE_PATH.read_bytes()
    return json.loads(b), b, _sha(b)
