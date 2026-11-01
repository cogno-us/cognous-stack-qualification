"""F-A1 gate. Usage: gate.py <results-dir> . Fails on a missing results file, any FAILED or SKIP case, any BREACH, INCONCLUSIVE, BLOCKED or NONE verdict,
or an executed count other than the planned 30. No allowlist: a finding stays red until the owner remediates and the suite is rerun."""
import json
import sys
from pathlib import Path

doc = json.load(open(Path(sys.argv[1]) / "results.json"))
bad = []
for c in doc["cases"]:
    v = c.get("verdict") or "NONE"
    short = c["case"].split("::")[-1]
    if c.get("outcome") != "PASSED":
        bad.append(f"{short}: {c.get('outcome')}: {c.get('failure', '')[-500:]}")
    if v in ("BREACH", "INCONCLUSIVE", "BLOCKED", "NONE"):
        bad.append(f"{short}: verdict {v}: {c.get('note')}")
if doc["counts"]["executed"] != 30:
    bad.append(f"executed {doc['counts']['executed']} != 30 planned cases")
print(json.dumps({"executed": doc["counts"]["executed"], "verdicts": doc["verdicts"], "pins": doc["exact_pins"]}, indent=1))
if bad:
    for b in bad:
        print("::error title=F-A1 gate::" + b.replace("\n", "%0A")[:1200])
    sys.exit(1)
