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
# Requalification: the historical A08 BREACH (Runtime 4199a6c7) must now be HELD with the typed refusal and nothing committed.
# The patched result is judged on its own evidence; the historical breach is kept in historical_findings.json and is never an allowance.
a08 = [c for c in results["cases"] if c["case"].endswith("test_a08_claim_effective_policy_digest_replaced_by_a_wider_policys_digest")]
if len(a08) != 1:
    bad.append("A08: not present exactly once")
else:
    obs = a08[0].get("observed") or {}
    counts = obs.get("counts_effects_attempts_receipts_budget")
    if (a08[0].get("verdict") != "HELD" or (obs.get("selection_refusal") or {}).get("code") != "policy_identity_mismatch"
            or not counts or any(counts[:3])):
        bad.append(f"A08: patched result is not HELD/policy_identity_mismatch/zero-evidence: {a08[0].get('verdict')} {obs}")
required = {"A12", "A13", "A14", "A15", "A16", "A17", "A18"}
present = {c["case"].split("::")[-1].split("_")[1].upper() for c in results["cases"]}
if not required <= present:
    bad.append(f"requalification cases missing: {sorted(required - present)}")
for b in bad:
    annotate(b)
print(json.dumps({"counts": c, "verdicts": results["verdicts"], "accepted": sorted(accepted)}, indent=1))
sys.exit(1 if bad else 0)
