#!/usr/bin/env python3
"""OCS-MVP-QGATE-05 / Worker C: READ-ONLY summary of one mvp-acceptance run directory (PROPOSED, non-authorizing; changes no verdict, edits no result).

Reads whatever the run left under --run-dir and writes summary.json and summary.md next to it (or under --out-dir). It never edits an input file and never turns one
category into another: oracle row statuses (PASS / FAIL / BLOCKED / ABSTAIN / NOT RUN / NOT APPLICABLE, every distinct status string found, each counted on its own),
pytest junit outcomes (passed / failed / error / skipped, per invocation), the Verifier dispositions found in the retained report bytes, the pytest exit files, the
gate verdict, the environment-record checks (when present), the tuple heads and the run identity. A missing or malformed file is reported as MISSING / UNREADABLE,
never as zero. Standard library only. Exit status is 0 unless the arguments are wrong: the verdict is the gate's, not this script's.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def load_json(p: Path):
    try:
        return json.loads(p.read_text()), None
    except FileNotFoundError:
        return None, "MISSING"
    except (OSError, ValueError) as exc:
        return None, f"UNREADABLE ({type(exc).__name__})"


def junit_counts(p: Path) -> dict:
    try:
        root = ET.parse(p).getroot()
    except FileNotFoundError:
        return {"status": "MISSING"}
    except (OSError, ET.ParseError) as exc:
        return {"status": f"UNREADABLE ({type(exc).__name__})"}
    c = collections.Counter()
    skipped_reasons = []
    for case in root.iter("testcase"):
        c["tests"] += 1
        if case.find("failure") is not None:
            c["failed"] += 1
        elif case.find("error") is not None:
            c["error"] += 1
        elif case.find("skipped") is not None:
            c["skipped"] += 1
            sk = case.find("skipped")
            skipped_reasons.append({"test": f"{case.get('classname')}::{case.get('name')}", "message": (sk.get("message") or "")[:300]})
        else:
            c["passed"] += 1
    return {"status": "READ", **{k: c.get(k, 0) for k in ("tests", "passed", "failed", "error", "skipped")}, "skipped_detail": skipped_reasons}


def read_exit(p: Path) -> str:
    try:
        return p.read_text().strip()
    except OSError:
        return "MISSING"


def summarize(run_dir: Path) -> dict:
    d = Path(run_dir)
    doc: dict = {"schema": "cognous.qgate05-run-summary/1", "read_only": True, "authorizes": False, "run_dir": str(d)}
    ident, _ = load_json(d / "run-identity.json")
    doc["run_identity"] = ident
    resolved, err = load_json(d / "tuple-resolved.json")
    doc["tuple"] = ({"run_id": resolved.get("run_id"), "qualification_sha": resolved.get("qualification_sha"),
                     "components": {k: v.get("sha") for k, v in (resolved.get("components") or {}).items()},
                     "composite_verified": resolved.get("composite_verified")} if resolved else err)
    results, err = load_json(d / "mvp-chain" / "results.json")
    if results:
        rows = results.get("rows") or []
        statuses = collections.Counter(str(r.get("status")) for r in rows)
        doc["oracle"] = {"expectations_file": results.get("expectations_file"), "expectations_sha256": results.get("expectations_sha256"), "rows_total": len(rows),
                         "status_counts_by_distinct_status": dict(sorted(statuses.items())), "suite_reported_counts": results.get("counts"),
                         "pytest_exit_status_in_results": results.get("pytest_exit_status"),
                         "non_pass_rows": [{"id": r.get("id"), "status": r.get("status"), "reason": str(r.get("reason", ""))[:400]} for r in rows if r.get("status") != "PASS"]}
    else:
        doc["oracle"] = err
    doc["junit"] = {n: junit_counts(d / f"junit-{n}.xml") for n in ("mvp-chain", "d2-route-b", "applicability")}
    doc["pytest_exit"] = {n: read_exit(d / f"pytest-exit-{n}.txt") for n in ("mvp-chain", "d2-route-b", "applicability")}
    gv, err = load_json(d / "gate-verdict.json")
    if gv:
        by = collections.Counter(c.get("status") for c in gv.get("checks", []))
        doc["gate"] = {"verdict": gv.get("verdict"), "authorizes": gv.get("authorizes"), "release": gv.get("release"), "check_status_counts": dict(sorted(by.items())),
                       "not_pass_checks": [{"id": c.get("id"), "status": c.get("status"), "detail": str(c.get("detail", c.get("message", "")))[:400]} for c in gv.get("checks", []) if c.get("status") != "PASS"],
                       "accounting": gv.get("accounting"), "candidate_commitment_sha256": gv.get("candidate_commitment_sha256")}
    else:
        doc["gate"] = err
    rec, err = load_json(d / "mvp-chain" / "artifacts" / "environment-record.json")
    if rec:
        checks = rec.get("checks") or []
        by = collections.Counter(c.get("status") for c in checks)
        doc["environment_record"] = {"overall": rec.get("overall"), "profile_supported": rec.get("profile_supported"), "check_status_counts": dict(sorted(by.items())),
                                     "not_pass_checks": [{"id": c.get("id"), "status": c.get("status")} for c in checks if c.get("status") != "PASS"],
                                     "record_sha256": rec.get("record_sha256")}
    else:
        doc["environment_record"] = err
    custody, err = load_json(d / "custody-evidence.json")
    doc["custody"] = ({k: custody.get(k) for k in ("result", "github_sha", "checkout_head", "recomputed_commitment_sha256", "hub_custody_checkout_head", "record_file_sha256", "problems")}
                      if custody else err)
    # Verifier dispositions, from the retained report bytes (never recomputed here)
    ver = {}
    for rp in sorted((d / "mvp-chain").rglob("*-report.json")) if (d / "mvp-chain").is_dir() else []:
        rj, _ = load_json(rp)
        if isinstance(rj, dict):
            ver[str(rp.relative_to(d))] = {k: rj.get(k) for k in ("overall", "summary", "exit_code") if k in rj}
    doc["verifier_reports_found"] = ver or "none matched *-report.json under mvp-chain (see the raw files in the run directory)"
    files = sorted(str(p.relative_to(d)) for p in d.rglob("*") if p.is_file()) if d.is_dir() else []
    doc["file_count"] = len(files)
    return doc


def to_markdown(doc: dict) -> str:
    L = ["## QGATE-05 run summary (read-only; not an acceptance, not a certification; release HOLD)"]
    ident = doc.get("run_identity") or {}
    if isinstance(ident, dict):
        L.append(f"- run: {ident.get('run_url')} attempt {ident.get('run_attempt')}; workflow sha {ident.get('workflow_sha')}; qualification sha {ident.get('github_sha')}")
        L.append(f"- runner: image {ident.get('ImageOS')}/{ident.get('ImageVersion')}, kernel {ident.get('kernel')}, yama.ptrace_scope {ident.get('yama_ptrace_scope')}")
    o = doc.get("oracle")
    if isinstance(o, dict):
        L.append(f"- oracle rows ({o['rows_total']}), each status counted separately: " + ", ".join(f"{k}={v}" for k, v in o["status_counts_by_distinct_status"].items()))
        for r in o["non_pass_rows"]:
            L.append(f"  - {r['id']}: {r['status']} {r['reason']}")
    else:
        L.append(f"- oracle results.json: {o}")
    for n, j in doc["junit"].items():
        if j.get("status") == "READ":
            L.append(f"- junit {n}: tests={j['tests']} passed={j['passed']} failed={j['failed']} error={j['error']} skipped={j['skipped']}; pytest exit {doc['pytest_exit'][n]}")
        else:
            L.append(f"- junit {n}: {j.get('status')}; pytest exit {doc['pytest_exit'][n]}")
    g = doc.get("gate")
    if isinstance(g, dict):
        L.append(f"- gate verdict: {g['verdict']} (authorizes={g['authorizes']}); check statuses: " + ", ".join(f"{k}={v}" for k, v in g["check_status_counts"].items()))
        for c in g["not_pass_checks"]:
            L.append(f"  - {c['id']}: {c['status']} {c['detail']}")
    else:
        L.append(f"- gate-verdict.json: {g}")
    e = doc.get("environment_record")
    if isinstance(e, dict):
        L.append(f"- hub environment record: overall={e['overall']} profile_supported={e['profile_supported']}; " + ", ".join(f"{k}={v}" for k, v in e["check_status_counts"].items()))
        for c in e["not_pass_checks"]:
            L.append(f"  - {c['id']}: {c['status']}")
    else:
        L.append(f"- environment record: {e}")
    cu = doc.get("custody")
    L.append(f"- custody: {cu.get('result') if isinstance(cu, dict) else cu}")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out-dir")
    a = ap.parse_args(argv)
    doc = summarize(Path(a.run_dir))
    out = Path(a.out_dir or a.run_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(doc, indent=2, sort_keys=True, default=str) + "\n")
    md = to_markdown(doc)
    (out / "summary.md").write_text(md)
    sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
