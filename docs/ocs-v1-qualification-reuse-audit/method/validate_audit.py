#!/usr/bin/env python3
"""Checks the data files of docs/ocs-v1-qualification-reuse-audit for closed vocabularies and internal consistency.

Not repository tooling and not wired to any workflow. Standard library only; reads the data directory, writes nothing.
Usage: python3 -I validate_audit.py <path to docs/ocs-v1-qualification-reuse-audit>

SPDX-License-Identifier: Apache-2.0
"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

CLASSES = {
    "REUSE UNCHANGED", "EXTEND EXISTING", "MISSING — BUILD ONLY IF NECESSARY",
    "DOMAIN-SPECIFIC — KEEP SEPARATE", "DUPLICATE — CONSOLIDATION CANDIDATE",
}
LABELS = {"SOURCE FACT", "REASONED INFERENCE", "UNVERIFIED"}
COVERAGE = {"PARTIAL", "NONE", "INACTIVE"}   # coverage by existing tests; never a result status
FORBIDDEN_WORDS = ("independently qualified", "qualified by", "certified")  # must not appear as a claim in the data


def load(root):
    d = root / "data"
    cj = json.loads((d / "capability-matrix.json").read_text(encoding="utf-8"))
    gj = json.loads((d / "gate-coverage.json").read_text(encoding="utf-8"))
    with open(d / "capability-matrix.csv", newline="", encoding="utf-8") as f:
        cc = list(csv.DictReader(f))
    with open(d / "gate-coverage.csv", newline="", encoding="utf-8") as f:
        gc = list(csv.DictReader(f))
    return cj, gj, cc, gc


def main(root):
    cj, gj, cc, gc = load(root)
    problems = []

    def need(cond, msg):
        if not cond:
            problems.append(msg)

    need(len(cj) == len(cc), "capability JSON and CSV row counts differ")
    for a, b in zip(cj, cc):
        need(all(str(a[k]) == b[k] for k in b), f"capability {a['id']}: JSON and CSV differ")
    ids = [r["id"] for r in cj]
    need(len(ids) == len(set(ids)), "duplicate capability id")
    for r in cj:
        need(r["classification"] in CLASSES, f"{r['id']}: class outside the five")
        need(r["label"] in LABELS, f"{r['id']}: label outside the three")
        need(r["repo"] in {"QUAL", "ISS"}, f"{r['id']}: repo")
    counts = Counter(r["classification"] for r in cj)
    need(len(cj) == 44, f"expected 44 capabilities, found {len(cj)}")
    expect = {"REUSE UNCHANGED": 14, "EXTEND EXISTING": 3, "MISSING — BUILD ONLY IF NECESSARY": 9,
              "DOMAIN-SPECIFIC — KEEP SEPARATE": 11, "DUPLICATE — CONSOLIDATION CANDIDATE": 7}
    need(dict(counts) == expect, f"class totals differ from the documents: {dict(counts)}")

    need(len(gj) == 14 and len(gc) == 14, "expected 14 gate rows")
    need([g["gate_id"] for g in gj] == [f"QG-{i:02d}" for i in range(1, 15)], "gate ids not QG-01..QG-14 in order")
    for a, b in zip(gj, gc):
        need(all(str(a[k]) == b[k] for k in b), f"{a['gate_id']}: JSON and CSV differ")
    for g in gj:
        need(g["qualification_side_coverage"] in COVERAGE, f"{g['gate_id']}: coverage word")
        need(g["qualified"] is False, f"{g['gate_id']}: must not be marked qualified")
        need(g["existing_references_total"] == g["existing_references_registry_builder"] + g["existing_references_qualification"],
             f"{g['gate_id']}: reference split")
    inactive = [g["gate_id"] for g in gj if g["qualification_side_coverage"] == "INACTIVE"]
    need(inactive == ["QG-02"], f"only QG-02 may be INACTIVE, found {inactive}")
    need(next(g for g in gj if g["gate_id"] == "QG-02")["plan_v1_status"] == "INACTIVE_MAX_AMOUNT_DEFERRED", "QG-02 plan status")
    active = [g for g in gj if g["gate_id"] != "QG-02"]
    need(sum(g["predeclared_new_test_items"] for g in gj) == 121, "new-item total != 121")
    need(sum(g["predeclared_new_test_items"] for g in active) == 114, "active new-item total != 114")
    need(sum(g["existing_references_total"] for g in gj) == 74, "existing-reference total != 74")
    cov = Counter(g["qualification_side_coverage"] for g in gj)
    need(dict(cov) == {"PARTIAL": 10, "NONE": 3, "INACTIVE": 1}, f"coverage totals differ from the documents: {dict(cov)}")

    blob = json.dumps([cj, gj]).lower()
    for w in FORBIDDEN_WORDS:
        need(w not in blob, f"data contains the phrase {w!r}")

    if problems:
        print("FAILED")
        for p in problems:
            print(" -", p)
        return 1
    print(f"OK: {len(cj)} capabilities in five closed classes {dict(counts)}; 14 gates, coverage {dict(cov)}; "
          f"QG-02 inactive; references 74 (26 registry builder / 48 qualification); new items 121 (114 active). No result status stored.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(Path(sys.argv[1])))
