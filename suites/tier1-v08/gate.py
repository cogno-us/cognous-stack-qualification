"""V08 gate (lead-owned). Usage: gate.py <results-root> <manifest.json>

Fails on: a missing area; any FAILED or SKIP case; any BREACH, INCONCLUSIVE or BLOCKED verdict; a mandatory scenario (manifest) with no HELD case.
There is no allowlist: a finding is preserved in the results and in the PR, and the run stays red until the owner remediates and V08 is rerun."""
import json
import sys
from pathlib import Path

root, manifest = Path(sys.argv[1]), json.load(open(sys.argv[2]))
areas = ("authority", "atomicity", "trust")
bad, cases, totals = [], [], {"executed": 0, "PASSED": 0, "FAILED": 0, "SKIP": 0, "BLOCKED": 0}
verdicts: dict = {}
pins = None


def annotate(msg):
    print("::error title=V08 gate::" + msg.replace("%", "%25").replace("\r", "").replace("\n", "%0A")[:1500])


for a in areas:
    f = root / a / "results.json"
    if not f.exists():
        bad.append(f"{a}: no results.json")
        continue
    doc = json.load(open(f))
    pins = pins or doc["exact_pins"]
    if doc["exact_pins"] != pins:
        bad.append(f"{a}: pins differ from the other areas")
    for k in totals:
        totals[k] += doc["counts"].get(k, 0)
    for c in doc["cases"]:
        cases.append(c)
        v = c.get("verdict") or "NONE"
        verdicts[v] = verdicts.get(v, 0) + 1
        short = c["case"].split("::")[-1]
        if c.get("outcome") != "PASSED":
            bad.append(f"{short}: {c.get('outcome')}: {c.get('failure', '')[-600:]}")
        if v in ("BREACH", "INCONCLUSIVE", "BLOCKED", "NONE"):
            bad.append(f"{short}: verdict {v}: {c.get('note')}")
for area, items in manifest["mandatory_scenarios"].items():
    for s in items:
        if s.get("mandatory"):
            mine = [c for c in cases if c.get("scenario") == s["id"]]
            if not any(c.get("verdict") == "HELD" and c.get("outcome") == "PASSED" for c in mine):
                bad.append(f"mandatory scenario {s['id']} has no HELD case ({len(mine)} case(s) tagged)")
for b in bad:
    annotate(b)
print("::notice title=V08 gate::" + json.dumps({"counts": totals, "verdicts": verdicts, "pins": pins}, sort_keys=True))
sys.exit(1 if bad else 0)
