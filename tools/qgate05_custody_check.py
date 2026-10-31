#!/usr/bin/env python3
"""OCS-MVP-QGATE-05 / Worker C: independent commitment custody check for the single authorized mvp-acceptance run (PROPOSED, non-authorizing).

The candidate commitment (G-12) must be anchored OUTSIDE the candidate checkout. The workflow checks out the hub repository
(cogno-us/cognous-open-control-stack) at the DEDICATED custody branch `qgate-05/custody-1` (ref = that branch; NOT the hub default branch) into a separate directory and
reads ONE custody record (the record is pushed once to that branch and never force-pushed; the resolved head sha of the branch is recorded in the evidence):

    docs/mvp-recovery/qgate-05/custody/freeze-commitment.json

    {
      "schema": "cognous.qgate05-freeze-commitment/1",
      "qualification_revision": "<40-hex, the commit pushed to qgate-05/run-1>",
      "candidate_commitment_file": "process/mvp-acceptance/candidate-commitment.proposed.v5.json",      (optional, must equal --commitment-rel when present; the hub template spells it commitment_file, also accepted)
      "candidate_commitment_sha256": "<64-hex sha256 of that file>"
    }

This script asserts (exit 1 on any failure, the run stops before any test):
  1. the record parses and carries both fields in the right shape;
  2. GITHUB_SHA (the pushed commit, passed as --github-sha) equals qualification_revision, and so does `git rev-parse HEAD` of the Qualification checkout (--repo-root);
  3. the sha256 RECOMPUTED from the commitment file in the checkout equals candidate_commitment_sha256.
It writes custody-evidence.json (record bytes sha256, the hub commit resolved at checkout time, the recomputed value, every comparison) and, with --github-output,
`candidate_commitment_sha256=<value>` for the gate's independent --expect-commitment-sha256 (G-12). The workflow never embeds either value: the commitment covers the
workflow file, so embedding it would be circular. Standard library only. The record is untrusted input: only the two shapes above are accepted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

SCHEMA = "cognous.qgate05-freeze-commitment/1"
SCHEMAS = (SCHEMA, "cognous.ocs-mvp-qgate-05-freeze-commitment/1")  # the second is the string of the hub freeze package template (docs/mvp-recovery/qgate-05/freeze/freeze-commitment.template.json)
FILE_KEYS = ("candidate_commitment_file", "commitment_file")  # same meaning; the hub template names it commitment_file
CUSTODY_BRANCH = "qgate-05/custody-1"
HEX40 = re.compile(r"[0-9a-f]{40}")
HEX64 = re.compile(r"[0-9a-f]{64}")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git(path: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True, text=True, timeout=60).stdout.strip()


def check(record_path: Path, commitment_path: Path, commitment_rel: str, github_sha: str, repo_root: Path, hub_dir: Path | None) -> tuple[dict, list[str]]:
    problems: list[str] = []
    evidence: dict = {"schema": "cognous.qgate05-custody-evidence/1", "record_path": str(record_path), "commitment_file": commitment_rel, "github_sha": github_sha}
    try:
        raw = record_path.read_bytes()
    except OSError as exc:
        return evidence, [f"custody record unreadable: {type(exc).__name__}: {exc}"]
    evidence["record_file_sha256"] = sha256_bytes(raw)
    try:
        rec = json.loads(raw)
    except ValueError as exc:
        return evidence, [f"custody record is not JSON: {exc}"]
    if not isinstance(rec, dict):
        return evidence, ["custody record is not a JSON object"]
    evidence["record"] = {k: rec.get(k) for k in ("schema", "qualification_revision", "candidate_commitment_file", "commitment_file", "candidate_commitment_sha256")}
    if rec.get("schema") not in SCHEMAS:
        problems.append(f"custody record schema is {rec.get('schema')!r}, expected one of {SCHEMAS!r}")
    q, c = rec.get("qualification_revision"), rec.get("candidate_commitment_sha256")
    if not isinstance(q, str) or not HEX40.fullmatch(q):
        problems.append("qualification_revision is not a 40-hex lower-case sha")
    if not isinstance(c, str) or not HEX64.fullmatch(c):
        problems.append("candidate_commitment_sha256 is not a 64-hex lower-case sha256")
    for key in FILE_KEYS:
        if key in rec and rec[key] != commitment_rel:
            problems.append(f"{key} {rec[key]!r} != {commitment_rel!r}")
    if not HEX40.fullmatch(github_sha or ""):
        problems.append("GITHUB_SHA is not a 40-hex sha")
    if isinstance(q, str) and github_sha != q:
        problems.append(f"GITHUB_SHA {github_sha} != custody qualification_revision {q}")
    try:
        head = git(repo_root, "rev-parse", "HEAD")
        evidence["checkout_head"] = head
        if head != github_sha:
            problems.append(f"checkout HEAD {head} != GITHUB_SHA {github_sha}")
    except (subprocess.SubprocessError, OSError) as exc:
        problems.append(f"cannot read checkout HEAD: {type(exc).__name__}")
    try:
        recomputed = sha256_bytes(commitment_path.read_bytes())
        evidence["recomputed_commitment_sha256"] = recomputed
        if isinstance(c, str) and recomputed != c:
            problems.append(f"recomputed commitment sha256 {recomputed} != custody candidate_commitment_sha256 {c}")
    except OSError as exc:
        problems.append(f"commitment file unreadable: {type(exc).__name__}: {exc}")
    if hub_dir is not None:
        try:
            evidence["hub_custody_checkout_head"] = git(hub_dir, "rev-parse", "HEAD")
            evidence["hub_custody_branch"] = CUSTODY_BRANCH
            evidence["hub_custody_checkout_branch_note"] = f"checked out at the dedicated hub custody branch {CUSTODY_BRANCH} (checkout ref); hub_custody_checkout_head is the resolved head sha of that branch"
        except (subprocess.SubprocessError, OSError) as exc:
            problems.append(f"cannot resolve the hub custody checkout commit: {type(exc).__name__}")
    evidence["problems"] = problems
    evidence["result"] = "PASS" if not problems else "FAIL"
    return evidence, problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--record", required=True)
    ap.add_argument("--commitment-file", required=True, help="path of the commitment file inside the Qualification checkout")
    ap.add_argument("--commitment-rel", required=True, help="repository-relative name of that file (compared with the record when it names one)")
    ap.add_argument("--github-sha", required=True)
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--hub-dir")
    ap.add_argument("--out", required=True)
    ap.add_argument("--github-output")
    a = ap.parse_args(argv)
    evidence, problems = check(Path(a.record), Path(a.commitment_file), a.commitment_rel, a.github_sha, Path(a.repo_root), Path(a.hub_dir) if a.hub_dir else None)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    for p in problems:
        print(f"CUSTODY FAIL: {p}", file=sys.stderr)
    if problems:
        return 1
    if a.github_output:
        with open(a.github_output, "a") as fh:
            fh.write(f"candidate_commitment_sha256={evidence['record']['candidate_commitment_sha256']}\n")
    print("custody PASS: GITHUB_SHA == qualification_revision and the recomputed commitment sha256 == the custody record")
    return 0


if __name__ == "__main__":
    sys.exit(main())
