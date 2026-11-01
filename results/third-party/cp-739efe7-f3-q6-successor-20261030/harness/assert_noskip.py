#!/usr/bin/env python3
"""D-2 junit gate. Usage: assert_noskip.py <junit.xml> <label> [--min N]
Prints per-file counts (tests/passed/failed/errors/skipped) as JSON. Verdict line:
  NO_SKIP_PASS  : skipped==0 and failures+errors==0 and tests>=min
  NO_SKIP_FAIL  : skipped==0 but failures/errors present (ran, not passing)
  NOT_RUN       : any skipped test (skips are reported as NOT RUN, never as pass), or zero tests
Exit status 0 only for NO_SKIP_PASS."""
import json
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

path, label = sys.argv[1], sys.argv[2]
mn = int(sys.argv[sys.argv.index("--min") + 1]) if "--min" in sys.argv else 1
root = ET.parse(path).getroot()
cases = list(root.iter("testcase"))
per = defaultdict(lambda: dict(tests=0, passed=0, failed=0, errors=0, skipped=0))
for tc in cases:
    cn = tc.get("classname") or ""
    f = ".".join(cn.split(".")[:2]) if cn else "(module-level:" + (tc.get("name") or "?") + ")"
    d = per[f]
    d["tests"] += 1
    if tc.find("skipped") is not None:
        d["skipped"] += 1
    elif tc.find("failure") is not None:
        d["failed"] += 1
    elif tc.find("error") is not None:
        d["errors"] += 1
    else:
        d["passed"] += 1
tot = {k: sum(v[k] for v in per.values()) for k in ("tests", "passed", "failed", "errors", "skipped")}
if tot["tests"] == 0 or tot["skipped"] > 0:
    verdict = "NOT_RUN"
elif tot["failed"] + tot["errors"] > 0:
    verdict = "NO_SKIP_FAIL"
elif tot["tests"] < mn:
    verdict = "NOT_RUN"
else:
    verdict = "NO_SKIP_PASS"
print(json.dumps({"label": label, "junit": path, "totals": tot, "per_module": per, "verdict": verdict}, indent=1, sort_keys=True))
print(f"{label}: {verdict}")
sys.exit(0 if verdict == "NO_SKIP_PASS" else 1)
