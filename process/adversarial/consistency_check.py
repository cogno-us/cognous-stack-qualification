"""Read-only consistency checker for the V1 validation status copies (batch-1 adversarial test T18).

SPDX-License-Identifier: Apache-2.0

Compares the status counts and verdicts that appear in several places and must agree:

  matrix    results/v1-validation/<id>/<run>-reduced-scope/requirements-matrix.json   (row statuses, recounted here)
  summary   the same directory's summary.json                                          (counts and verdicts as written)
  panel     hub docs/workstreams/release-closeout-control-panel.json, member v1_validation
  markdown  hub docs/workstreams/release-closeout-control-panel.md                     (the prose lines that state the counts)
  register  process/v1-validation/<id>/failure-register.json                           (status vocabulary; referenced rows exist)

It writes nothing and changes nothing; a divergence is a finding line. It is not part of the V1 validation controller and does
not feed the v1_validation verdict. The hub is frozen: any fix is a coordinator follow-up, never an edit made by this tool.

    python process/adversarial/consistency_check.py --hub <hub checkout>      exit 0 consistent, 1 divergence, 2 input error
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
VALIDATION_ID = "v1-2026-10-16-a"
RUN_DIR = ROOT / "results" / "v1-validation" / VALIDATION_ID / "final-linux-1-39032930011-reduced-scope"
REGISTER = ROOT / "process" / "v1-validation" / VALIDATION_ID / "failure-register.json"
# Register references that are not matrix rows by design (listed, not hidden).
NON_MATRIX_REFERENCES = {"platform": "cross-platform entry (D2 Linux only); there is no matrix row for it by design"}
STATUSES = ("PASS", "FAIL", "INCONCLUSIVE", "NOT RUN", "NOT APPLICABLE")


def load_sources(hub: pathlib.Path) -> dict:
    return {
        "matrix": json.loads((RUN_DIR / "requirements-matrix.json").read_text(encoding="utf-8")),
        "summary": json.loads((RUN_DIR / "summary.json").read_text(encoding="utf-8")),
        "panel": json.loads((hub / "docs/workstreams/release-closeout-control-panel.json").read_text(encoding="utf-8")),
        "markdown": (hub / "docs/workstreams/release-closeout-control-panel.md").read_text(encoding="utf-8"),
        "register": json.loads(REGISTER.read_text(encoding="utf-8")),
    }


def _counts(rows) -> dict[str, int]:
    c = collections.Counter(r["status"] for r in rows)
    return {s: c.get(s, 0) for s in STATUSES}


def _md_counts(text: str, pattern: str) -> dict[str, int] | None:
    m = re.search(pattern, text)
    if not m:
        return None
    out = {s: 0 for s in STATUSES}
    for n, s in re.findall(r"(\d+) (PASS|FAIL|INCONCLUSIVE|NOT RUN|NOT APPLICABLE)", m.group(0)):
        out[s] = int(n)
    return out


def facts(src: dict) -> dict[str, dict]:
    """Per source: all-row counts, mandatory counts, verdicts. A missing fact is None (reported as unreadable, not as agreement)."""
    rows = src["matrix"]["requirements"]
    mandatory = [r for r in rows if r.get("mandatory")]
    out = {"matrix": {"all": _counts(rows), "mandatory": _counts(mandatory),
                      "reduced_verdict": "PASS" if mandatory and all(r["status"] == "PASS" for r in mandatory) else "FAIL"}}
    s = src["summary"]
    out["summary"] = {"all": {k: s["requirement_status_counts"].get(k, 0) for k in STATUSES},
                      "mandatory": {k: s["mandatory_requirement_status_counts"].get(k, 0) for k in STATUSES},
                      "reduced_verdict": s.get("selected_v1_verdict"),
                      "full_verdict": s.get("full_catalog_status", {}).get("unreduced_mandatory_verdict"),
                      "before_d15": {k: s.get("full_catalog_status", {}).get("unreduced_mandatory_status_counts", {}).get(k, 0)
                                     for k in STATUSES}}
    v = src["panel"].get("v1_validation", {})
    out["panel"] = {"all": {k: v.get("requirements", {}).get(k, 0) for k in STATUSES},
                    "mandatory": {k: v.get("mandatory_requirements", {}).get(k, 0) for k in STATUSES},
                    "reduced_verdict": v.get("verdict_reduced_scope"), "full_verdict": v.get("verdict_full_catalog"),
                    "before_d15": {k: v.get("mandatory_requirements_before_d15", {}).get(k, 0) for k in STATUSES}}
    md = src["markdown"]
    red = re.search(r"Reduced-scope verdict \(D15\): (PASS|FAIL)", md)
    full = re.search(r"Full-catalog verdict: (PASS|FAIL)", md)
    out["markdown"] = {"all": _md_counts(md, r"All \d+ catalog rows[^\n]*"),
                       "mandatory": _md_counts(md, r"with \d+ mandatory rows \([^)]*\)"),
                       "reduced_verdict": red.group(1) if red else None, "full_verdict": full.group(1) if full else None,
                       "before_d15": _md_counts(md, r"Of the \d+ rows mandatory before D15:[^\n]*")}
    return out


def check(src: dict) -> list[str]:
    f = facts(src)
    findings = []
    for key in ("all", "mandatory", "reduced_verdict", "full_verdict", "before_d15"):
        values = {name: d.get(key) for name, d in f.items() if key in d}
        for name, value in values.items():
            if value is None:
                findings.append(f"{key}: unreadable in {name}")
        present = {n: v for n, v in values.items() if v is not None}
        if len({json.dumps(v, sort_keys=True) for v in present.values()}) > 1:
            findings.append(f"{key}: copies disagree: " + json.dumps(present, sort_keys=True))
    reg = src["register"]
    vocab = set(reg.get("statuses", []))
    ids = {r["id"] for r in src["matrix"]["requirements"]}
    for e in reg.get("entries", []):
        if e.get("status") not in vocab:
            findings.append(f"register {e.get('id')}: status {e.get('status')!r} outside the register vocabulary")
        if e.get("status") == "VERIFIED" and not e.get("verified_in"):
            findings.append(f"register {e.get('id')}: VERIFIED without verified_in")
        for rid in e.get("requirements", []):
            if rid not in ids and rid not in NON_MATRIX_REFERENCES:
                findings.append(f"register {e.get('id')}: requirement {rid} not in the matrix")
    return findings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hub", required=True, help="cogno-us/cognous-open-control-stack checkout")
    args = ap.parse_args(argv)
    try:
        src = load_sources(pathlib.Path(args.hub))
    except (OSError, ValueError, KeyError) as exc:
        print(f"consistency_check: input error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    findings = check(src)
    for line in findings:
        print(line)
    print(f"{len(findings)} divergence(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
