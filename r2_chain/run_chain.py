#!/usr/bin/env python3
"""R2 joined-chain runner (PRIVATE PREVIEW QUALIFICATION TUPLE; preview-only, NOT canonical; synthetic, single synthetic tenant, claim A only).

Runs the lane's pytest battery (junit XML), then writes machine-readable evidence to --out:
  summary.json            result counts per label, per-row verdicts, required-row check, source-identity result, overall disposition
  rows.jsonl              one result row per marked test (written by the conftest recorder): row id, case id, label, expected/observed typed code, checks, node id
  positive-case.json      the positive chain case (record/selection digests, verdict, markers, binding, operator inputs, labelled assertions P01..P15)
  source-identity.json    Worker C's source-identity report (HEAD + tree + clean work tree of each pinned subject source, qualification revision)
  environment.json        interpreter, platform, package versions, exact command, tuple SHAs
  tuple.json              copy of r2_chain/sources.json (the PRIVATE PREVIEW QUALIFICATION TUPLE)
  junit.xml, pytest.log   raw pytest output
  SHA256SUMS              sha256 of every other file in --out
Exit status is nonzero on any pytest failure, any FAIL / NOT_RUN row, any required row missing or not in its allowed label set, or a source-identity problem.

usage (after `r2_chain/fetch_sources.sh <srcdir>`; the venv needs PyNaCl, pydantic, pytest, jsonschema; network is needed ONLY for fetching/installing):
    python r2_chain/run_chain.py --src-dir <srcdir> --out <outdir> [--required full|positive] [-- <extra pytest args>]
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as md
import json
import os
import platform
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "battery"))

LABELS = ("PASS", "FAIL", "REFUSED_AS_EXPECTED", "NOT_RUN", "NOT_APPLICABLE")
NEG_LETTERS = "ABCDEFGHIJKLMNOPQRS"           # the 19 required negatives A..S (row id = the letter)
# required row id -> labels allowed for EVERY row carrying that id. Negatives must be REFUSED_AS_EXPECTED; G (epoch/floor regression "where applicable") may be NOT_APPLICABLE.
REQUIRED_POSITIVE = {"P1": {"PASS"}, "S0": {"PASS"}}
REQUIRED_NEGATIVE = {**{k: {"REFUSED_AS_EXPECTED"} for k in NEG_LETTERS}, "G2": {"REFUSED_AS_EXPECTED"}, "S1": {"PASS", "REFUSED_AS_EXPECTED"}}
REQUIRED_NEGATIVE["G"] = {"REFUSED_AS_EXPECTED", "NOT_APPLICABLE"}
BAD_LABELS = {"FAIL", "NOT_RUN"}
PACKAGES = ("PyNaCl", "pydantic", "pytest", "jsonschema")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pkg_versions() -> dict:
    out = {}
    for n in PACKAGES:
        try:
            out[n] = md.version(n)
        except md.PackageNotFoundError:
            out[n] = None
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src-dir", default=os.environ.get("SRC_DIR"), help="directory populated by fetch_sources.sh (default: $SRC_DIR)")
    ap.add_argument("--out", required=True, help="evidence output directory (created; existing evidence files of the same names are overwritten, nothing else is touched)")
    ap.add_argument("--required", choices=("full", "positive"), default="full", help="required rows: full = positive + 19 negatives A-S + G2 + source rows (default); positive = P1 + S0 only (development)")
    ap.add_argument("pytest_args", nargs="*", help="extra pytest args (put after --)")
    a = ap.parse_args(argv)
    if not a.src_dir:
        ap.error("--src-dir (or SRC_DIR) is required")
    src_dir, out = Path(a.src_dir).resolve(), Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    for stale in ("rows.jsonl", "positive-case.json", "junit.xml", "pytest.log", "summary.json", "SHA256SUMS", "environment.json", "source-identity.json", "tuple.json"):
        (out / stale).unlink(missing_ok=True)

    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONSTARTUP", "PYTHONHOME")}
    env.update(SRC_DIR=str(src_dir), R2_SRC_DIR=str(src_dir), R2_ROWS_JSONL=str(out / "rows.jsonl"), R2_OUT_DIR=str(out),
               PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="0")     # bytecode must never be written into the pinned source trees (they are checked clean)
    env.pop("R2_SOURCES_JSON", None)

    import source_identity as SI  # noqa: E402  (battery/source_identity.py; imports no subject module)
    os.environ["SRC_DIR"] = str(src_dir)
    ident = SI.source_identity_report(src_dir, check_modules=False)
    (out / "source-identity.json").write_text(json.dumps(ident, indent=1, sort_keys=True) + "\n")
    shutil.copyfile(HERE / "sources.json", out / "tuple.json")
    tuple_ = json.loads((HERE / "sources.json").read_text())

    cmd = [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--junitxml", str(out / "junit.xml"), *a.pytest_args]
    with open(out / "pytest.log", "w") as log:
        proc = subprocess.run(cmd, cwd=HERE, env=env, stdout=log, stderr=subprocess.STDOUT)
    tail = (out / "pytest.log").read_text().splitlines()[-25:]
    print("\n".join(tail))

    # ------------------------------------------------------------------ rows
    rows = []
    rp = out / "rows.jsonl"
    if rp.exists():
        rows = [json.loads(x) for x in rp.read_text().splitlines() if x.strip()]
    counts = Counter(r["label"] for r in rows)
    by_row: dict = {}
    for r in rows:
        by_row.setdefault(r["row_id"], []).append(r)
    required = dict(REQUIRED_POSITIVE) if a.required == "positive" else {**REQUIRED_POSITIVE, **REQUIRED_NEGATIVE}
    problems = []
    row_verdicts = {}
    for rid, allowed in required.items():
        got = by_row.get(rid, [])
        labels = sorted({r["label"] for r in got})
        ok = bool(got) and all(r["label"] in allowed for r in got)
        row_verdicts[rid] = {"required_labels": sorted(allowed), "observed_labels": labels, "count": len(got), "ok": ok}
        if not ok:
            problems.append("required row %s: %s" % (rid, "missing" if not got else "labels %s not within %s" % (labels, sorted(allowed))))
    for r in rows:
        if r["label"] in BAD_LABELS:
            problems.append("row %s (%s) is %s" % (r["row_id"], r["nodeid"], r["label"]))
    if proc.returncode != 0:
        problems.append("pytest exited %d" % proc.returncode)

    # junit totals (independent of the recorder)
    jt = {}
    try:
        suite = ET.parse(out / "junit.xml").getroot()
        suite = suite if suite.tag == "testsuite" else suite.find("testsuite")
        jt = {k: int(suite.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")}
    except Exception as e:  # noqa: BLE001
        problems.append("junit.xml unreadable: %s" % e)
    marked = len(rows)
    if jt and (jt["failures"] or jt["errors"]):
        problems.append("junit failures=%d errors=%d" % (jt["failures"], jt["errors"]))

    # source identity: before the run (report) and after it (the run must not have dirtied any pinned tree)
    ident_after = SI.source_identity_report(src_dir, check_modules=False)
    if not ident["ok"]:
        problems.append("source identity (before run): %s" % ident["problems"][:5])
    if not ident_after["ok"]:
        problems.append("source identity (after run): %s" % ident_after["problems"][:5])

    pos = out / "positive-case.json"
    if not pos.exists():
        problems.append("positive-case.json was not produced")

    env_json = {
        "label": "PRIVATE PREVIEW QUALIFICATION TUPLE (preview-only, NOT canonical)", "python": sys.version, "executable": sys.executable, "platform": platform.platform(),
        "packages": pkg_versions(), "command": cmd, "cwd": str(HERE), "src_dir": str(src_dir), "github_sha": os.environ.get("GITHUB_SHA"),
        "qualification": ident["qualification"], "tuple": {k: {"repo": v["repo"], "sha": v["sha"], "tree": v["tree"]} for k, v in tuple_["sources"].items()},
        "env_set": {k: env[k] for k in ("PYTHONDONTWRITEBYTECODE", "PYTHONHASHSEED")}, "network_used_by_tests": False,
        "scope": "synthetic only; single synthetic tenant; claim A only; claim B not asserted"}
    (out / "environment.json").write_text(json.dumps(env_json, indent=1, sort_keys=True) + "\n")

    disposition = "PASS" if not problems else "FAIL"
    summary = {
        "schema": "r2-joined-chain-run-summary/1", "label": "PRIVATE PREVIEW QUALIFICATION TUPLE (preview-only, NOT canonical)", "disposition": disposition,
        "required_mode": a.required, "tuple": env_json["tuple"], "qualification": ident["qualification"],
        "pytest": {"returncode": proc.returncode, **jt, "marked_result_rows": marked}, "label_counts": {k: counts.get(k, 0) for k in LABELS},
        "required_rows": row_verdicts, "rows": [{k: r.get(k) for k in ("row_id", "case_id", "label", "expected_code", "observed_code", "nodeid")} for r in rows],
        "source_identity_ok_before": ident["ok"], "source_identity_ok_after": ident_after["ok"], "problems": problems,
        "positive_case": "positive-case.json" if pos.exists() else None,
        "claims_not_made": ["claim B", "Registry origin/authority", "production readiness", "multi-tenant isolation", "operational trust", "canonical adoption"]}
    (out / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")

    sums = [(sha256_file(p), p.relative_to(out).as_posix()) for p in sorted(out.rglob("*")) if p.is_file() and p.name != "SHA256SUMS"]
    (out / "SHA256SUMS").write_text("".join("%s  %s\n" % s for s in sums))
    print("R2 joined chain: %s  labels=%s  problems=%d  evidence=%s" % (disposition, dict(counts), len(problems), out))
    for p in problems:
        print("  PROBLEM:", p)
    return 0 if disposition == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
