#!/usr/bin/env python3
"""Fail-closed gate over the pytest junit XML of the CAP v0.1 G1 battery: nonzero on any failure/error/skip/xfail, or fewer than --min-tests tests.
usage: junit_gate.py <junit.xml> --min-tests N"""
import argparse
import sys
import xml.etree.ElementTree as ET

ap = argparse.ArgumentParser()
ap.add_argument("junit")
ap.add_argument("--min-tests", type=int, required=True)
a = ap.parse_args()
root = ET.parse(a.junit).getroot()
suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
tests = sum(int(s.get("tests", 0)) for s in suites)
bad = {k: sum(int(s.get(k, 0)) for s in suites) for k in ("failures", "errors", "skipped")}
print(f"tests={tests} (min {a.min_tests}) failures={bad['failures']} errors={bad['errors']} skipped={bad['skipped']}")
if tests < a.min_tests or any(bad.values()):
    print("::error::CAP v0.1 G1 gate FAILED (fewer tests than expected, or a failure/error/skip/xfail)")
    sys.exit(1)
print("CAP v0.1 G1 gate: PASS")
