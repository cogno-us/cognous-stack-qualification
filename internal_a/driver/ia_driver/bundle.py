"""Raw-evidence packaging into the merged evaluator's observation bundle (ia-observation-bundle/1).
The driver never computes a verdict. Raw files are copied BYTE-FOR-BYTE from the case scratch (written by the
native-calling child) and indexed by sha256 before anything is interpreted."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from . import BUNDLE_SCHEMA, DRIVER_VERSION


def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class BundleBuilder:
    def __init__(self, out_dir):
        self.out = Path(out_dir)
        if self.out.exists():
            raise FileExistsError(f"bundle output directory already exists: {self.out}")      # create-only, never overwrite
        (self.out / "raw").mkdir(parents=True)
        self.raw_index = {}
        self.cases = {}
        self.driver_events = []
        self.driver_meta = {"driver_version": DRIVER_VERSION}

    # ---- raw evidence ----
    def add_raw(self, case_id, boundary, kind, data: bytes) -> str:
        """kind: 'raw' (returned native value) | 'exc' (exception record) | 'input' (preserved input). Returns the bundle-relative path."""
        if kind not in ("raw", "exc", "input"):
            raise ValueError("bad raw kind")
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("raw evidence must be bytes copied from the child scratch")
        rel = f"raw/{case_id}.{boundary}.{kind}.json"
        if rel in self.raw_index:
            raise ValueError(f"duplicate raw evidence path {rel}")
        p = self.out / rel
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as fh:
            fh.write(bytes(data))
        self.raw_index[rel] = sha256_hex(bytes(data))
        return rel

    def add_case(self, case_id, *, executed, boundaries, adverse_notes=()):
        if case_id in self.cases:
            raise ValueError(f"duplicate case {case_id}")                # duplicate cases are refused, never merged
        self.cases[case_id] = {"executed": bool(executed), "boundaries": boundaries, "adverse_notes": list(adverse_notes)}

    def set_events(self, events):
        self.driver_events = list(events)

    def finish(self) -> str:
        """Write bundle.json (create-only). Returns the sha256 of its bytes (record it OUTSIDE the driver before evaluation)."""
        bundle = {"schema": BUNDLE_SCHEMA, "raw_index": self.raw_index, "cases": self.cases, "driver_events": self.driver_events,
                  "driver_meta": self.driver_meta}
        data = (json.dumps(bundle, sort_keys=True, indent=1) + "\n").encode()
        fd = os.open(self.out / "bundle.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        return sha256_hex(data)


def boundary_record(*, outcome, entrypoint, raw=None, exception_raw=None, inputs=None):
    """Exactly one of raw (returned) / exception_raw (raised) - the evaluator derives the outcome from the evidence kind."""
    if (raw is None) == (exception_raw is None):
        raise ValueError("a boundary needs exactly one of raw / exception_raw")
    if outcome != ("returned" if raw is not None else "raised"):
        raise ValueError("outcome label disagrees with the evidence kind")
    rec = {"outcome": outcome, "entrypoint": entrypoint}
    if raw is not None:
        rec["raw"] = raw
    else:
        rec["exception_raw"] = exception_raw
    if inputs:
        rec["inputs"] = dict(inputs)
    return rec
