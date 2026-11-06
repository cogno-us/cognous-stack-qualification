"""Command line: evaluate | freeze-build | freeze-verify | collect-identity. No network, no subprocess."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import engine, freeze, identity

PKG_BASE = Path(__file__).resolve().parent.parent   # internal_a/


def _dump(obj):
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ia_eval")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("evaluate")
    e.add_argument("--oracle", required=True)
    e.add_argument("--expect-oracle-sha256", required=True)
    e.add_argument("--bundle", required=True)
    e.add_argument("--freeze-root", required=True, help="committed root commitment (from outside this checkout)")
    e.add_argument("--out")
    b = sub.add_parser("freeze-build")
    b.add_argument("--meta-json", required=True)
    v = sub.add_parser("freeze-verify")
    v.add_argument("--freeze-root", required=True)
    c = sub.add_parser("collect-identity")
    c.add_argument("--root", required=True)
    c.add_argument("paths", nargs="+")
    a = ap.parse_args(argv)
    if a.cmd == "evaluate":
        block = None
        probs = freeze.verify(PKG_BASE, a.freeze_root)
        if probs:
            block = "FREEZE_DRIFT: " + "; ".join(probs)[:800]
        report = engine.run(Path(a.oracle).read_bytes(), a.bundle, a.expect_oracle_sha256, extra_block=block)
        text = _dump(report)
        if a.out:
            Path(a.out).write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
        return {"PASS": 0, "FAIL": 1}.get(report["overall"], 2)
    if a.cmd == "freeze-build":
        m = freeze.build(PKG_BASE, json.loads(a.meta_json))
        (PKG_BASE / freeze.MANIFEST_REL).write_text(_dump(m), encoding="utf-8")
        print(m["root_commitment"])
        return 0
    if a.cmd == "freeze-verify":
        probs = freeze.verify(PKG_BASE, a.freeze_root)
        print("\n".join(probs) if probs else "FREEZE OK")
        return 1 if probs else 0
    if a.cmd == "collect-identity":
        sys.stdout.write(_dump(identity.hash_files(a.root, a.paths)))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
