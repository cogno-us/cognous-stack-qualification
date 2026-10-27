"""CI gate for the V07 assessment: fails on harness FAIL/SKIP, on INCONCLUSIVE, and on any BREACH not listed (by case id and severity) in
the committed accepted-findings file. A listed finding is preserved, not hidden: the file is part of the retained evidence."""
import json
import sys

import os


def annotate(msg):
    """Emit a workflow annotation so a failure's cause is readable without downloading job logs."""
    print("::error title=V07 gate::" + msg.replace("%", "%25").replace("\r", "").replace("\n", "%0A")[:1500])


if not os.path.exists(sys.argv[1]):
    annotate(f"no results file at {sys.argv[1]}: the harness did not reach session finish")
    sys.exit(1)
results = json.load(open(sys.argv[1]))
accepted = {f["case"]: f for f in json.load(open(sys.argv[2]))["findings"]}
c = results["counts"]
bad = []
if c["executed"] == 0 or c["FAILED"] or c["SKIP"]:
    bad.append(f"harness counts: {c}")
for case in results["cases"]:
    short = case["case"].split("::")[-1].split("_")[1].upper()
    v = case.get("verdict")
    if case.get("outcome") not in ("PASSED", None):
        annotate(f"{short}: {case.get('outcome')}: {case.get('failure', '')[-900:]}")
    if v == "INCONCLUSIVE":
        bad.append(f"{short}: INCONCLUSIVE")
    if v == "BREACH":
        f = accepted.get(short)
        if f is None or f["severity"] in ("CRITICAL", "HIGH"):
            bad.append(f"{short}: BREACH not accepted ({f})")
for b in bad:
    annotate(b)
print(json.dumps({"counts": c, "verdicts": results["verdicts"], "accepted": sorted(accepted)}, indent=1))
sys.exit(1 if bad else 0)
