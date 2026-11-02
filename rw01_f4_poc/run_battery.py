#!/usr/bin/env python3
"""Runner of the RW-01-F4-PoC end-to-end battery. Local and CI use the same script.

usage: run_battery.py --src <dir with the pinned checkouts> --out <evidence dir> [--strict]

Runs, each as its own pytest process (pytest -rA, --junitxml):
  battery        this directory's end-to-end battery (rows N01..N28, findings F-n, protected-file re-verification)
  registry_pr    the Registry PR #86 new/edited tests at the pinned head
  replay_pr      the Replay PR #84 new tests and the edited Registry-governed test file at the pinned head
  replay_f4      Replay F4 structural selector (ca94d6a8) regression set: the PR #84 suites above plus the E3 named-key guard / N23-N24 golden file, effective-configuration,
                 expected-digest, refusal-journal, programme-2 suites and the new F4 selector suite (regression H)
  cp_pr          the Control Plane PR #102 new tests (against the CP-pinned Registry 6f600ab1, OCS_REQUIRE_REGISTRY_PIN=1)
  cp_repinned_*  the seven Control Plane test files whose bounded.py pin the PR changed (four against Registry 6f600ab1, three against the r08-v8 pin a40fe755)
Then writes environment.json, summary.json, SUMMARY.md, rows.json and SHA256SUMS (a SHA-256 manifest of every output file) into --out.
Exit code: NONZERO if a suite could not run to completion, if ANY test of ANY suite failed or errored, or if ANY REQUIRED row (N01..N28, F-1, F1-A..F1-G, F1-BRIDGED, PF, S)
is missing or not PASS. There is no tolerated FAIL row any more (the former intentional F-1 FAIL is replaced by the passing integration rows F1-A..F1-G). `--strict` is kept
as an accepted no-op for old invocations.
No network, no secrets, no model calls.
"""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = json.loads((HERE / "sources.json").read_text())["sources"]


def counts(xml_path: Path):
    root = ET.parse(xml_path).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    t, f, e, s = (int(suite.get(k, 0)) for k in ("tests", "failures", "errors", "skipped"))
    return {"collected": t, "passed": t - f - e - s, "failed": f, "errors": e, "skipped": s}


def suite_env(base, over):
    """Suite environment; a PYTHONPATH already set by the caller (e.g. a throwaway PyNaCl directory when PyNaCl is not installed system-wide) is kept AFTER the suite's own entries."""
    env = {**base, **over}
    if over.get("PYTHONPATH") and base.get("PYTHONPATH"):
        env["PYTHONPATH"] = over["PYTHONPATH"] + os.pathsep + base["PYTHONPATH"]
    return env


REQUIRED_ROWS = ["N%02d" % i for i in range(1, 29)] + ["F-1", "F1-A", "F1-B", "F1-C", "F1-D", "F1-E", "F1-F", "F1-G", "F1-BRIDGED", "PF", "S"]


def row_result(entries):
    res = [x["result"] for x in entries]
    return "FAIL" if "FAIL" in res else "BLOCKED" if "BLOCKED" in res else "SKIP" if "SKIP" in res else "PASS"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    src, out = Path(a.src).resolve(), Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    d = lambda n: src / SOURCES[n]["dir"]
    base_env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", RW01_SRC_DIR=str(src), GIT_TERMINAL_PROMPT="0")
    suites = {
        "battery": dict(cwd=HERE, args=["battery"], env={"RW01_ROWS_JSON": str(out / "rows.json")}),
        "registry_pr": dict(cwd=d("registry"), args=["tests/test_rw01_f4_verified_selection.py", "tests/test_rw01_f4_evidence_verifier.py", "tests/test_ext_s1_5_identity_module.py"], env={}),
        "replay_pr": dict(cwd=d("replay"), args=["tests/test_registry_authenticated_selection.py", "tests/test_registry_governed_expected_configuration_digest.py"],
                          env={"PYTHONPATH": str(d("replay") / "src")}),
        "replay_f4": dict(cwd=d("replay"), args=["tests/test_registry_authenticated_selection.py", "tests/test_registry_governed_effective_configuration.py",
                                                "tests/test_registry_governed_expected_configuration_digest.py", "tests/test_refusal_journal.py", "tests/test_programme2_profiles.py",
                                                "tests/test_programme2_n4_and_pairing.py", "tests/test_registry_authenticated_selection_f4_governed.py"],
                          env={"PYTHONPATH": str(d("replay") / "src")}),
        "cp_pr": dict(cwd=d("control_plane"), args=["tests/test_f4_selection_evidence.py", "tests/test_rw01_f4_poc_bounded_diff.py"],
                      env={"PYTHONPATH": str(d("control_plane") / "src"), "OCS_REGISTRY_PIN_DIR": str(d("registry_cp_pin")), "OCS_REQUIRE_REGISTRY_PIN": "1"}),
        "cp_repinned_6f600ab1": dict(cwd=d("control_plane"), args=["tests/test_f4_age_governance.py", "tests/test_f5_class_age_governance.py",
                                                                  "tests/test_freshness_purpose_anchor_successor.py", "tests/test_v02_legacy_claim_vector.py"],
                                     env={"PYTHONPATH": str(d("control_plane") / "src"), "OCS_REGISTRY_PIN_DIR": str(d("registry_cp_pin")), "OCS_REQUIRE_REGISTRY_PIN": "1"}),
        "cp_repinned_v8": dict(cwd=d("control_plane"), args=["tests/test_f5_class_unreadable_governance.py", "tests/test_final3_composed_binding.py", "tests/test_governed_policy_composition.py"],
                               env={"PYTHONPATH": str(d("control_plane") / "src"), "OCS_REGISTRY_PIN_DIR": str(d("registry_v8_pin")), "OCS_REQUIRE_REGISTRY_PIN": "1"}),
    }
    summary, harness_error = {}, False
    for name, spec in suites.items():
        xml = out / (name + ".junit.xml")
        raw = out / (name + ".raw.txt")
        print("=" * 30, name, "=" * 30, flush=True)
        proc = subprocess.run([sys.executable, "-m", "pytest", "-rA", "-p", "no:cacheprovider", "--junitxml", str(xml), *spec["args"]], cwd=spec["cwd"],
                              env=suite_env(base_env, spec["env"]), capture_output=True, text=True)
        raw.write_text(proc.stdout + ("\n--- stderr ---\n" + proc.stderr if proc.stderr.strip() else ""))
        sys.stdout.write(proc.stdout)
        if proc.stderr.strip():
            sys.stdout.write("--- stderr ---\n" + proc.stderr)
        if proc.returncode not in (0, 1) or not xml.exists():
            harness_error = True
            summary[name] = {"returncode": proc.returncode, "harness_error": True}
            continue
        summary[name] = {"returncode": proc.returncode, **counts(xml), "args": spec["args"]}
    import importlib.metadata as md
    env = {"platform": platform.platform(), "python": sys.version, "pytest": md.version("pytest"), "pydantic": md.version("pydantic"), "pydantic_core": md.version("pydantic_core"),
           "PyNaCl": md.version("PyNaCl"), "cffi": md.version("cffi"), "cryptography": md.version("cryptography"), "jsonschema": md.version("jsonschema"),
           "sources": {k: {"sha": v["sha"], "tree": v["tree"]} for k, v in SOURCES.items()}}
    (out / "environment.json").write_text(json.dumps(env, indent=1, sort_keys=True))
    (out / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True))
    rows = json.loads((out / "rows.json").read_text()) if (out / "rows.json").exists() else {}
    lines = ["# RW-01-F4-PoC battery summary", "", "| suite | collected | passed | failed | errors | skipped |", "|---|---|---|---|---|---|"]
    for name, s in summary.items():
        lines.append("| %s | %s | %s | %s | %s | %s |" % (name, s.get("collected", "-"), s.get("passed", "-"), s.get("failed", "-"), s.get("errors", "-"), s.get("skipped", "-")))
    lines += ["", "| row | result | tests |", "|---|---|---|"]
    for rid in sorted(rows, key=lambda k: (k[0] != "N", k)):
        res = [x["result"] for x in rows[rid]]
        agg = "FAIL" if "FAIL" in res else "BLOCKED" if "BLOCKED" in res else "SKIP" if "SKIP" in res else "PASS"
        lines.append("| %s | %s | %d (%d pass, %d fail) |" % (rid, agg, len(res), res.count("PASS"), res.count("FAIL")))
    failed = any(s.get("failed", 0) or s.get("errors", 0) for s in summary.values())
    bad_rows = [r for r in REQUIRED_ROWS if r not in rows or row_result(rows[r]) != "PASS"]
    bad_rows += [r for r in rows if r not in REQUIRED_ROWS and row_result(rows[r]) != "PASS"]
    verdict = ["", "REQUIRED ROWS: %d required, %d not PASS/missing%s" % (len(REQUIRED_ROWS), len(bad_rows), (": " + ", ".join(bad_rows)) if bad_rows else "")]
    verdict.append("RESULT: %s" % ("FAIL" if (harness_error or failed or bad_rows) else "PASS"))
    lines += verdict
    (out / "SUMMARY.md").write_text("\n".join(lines) + "\n")
    (out / "RESULT.txt").write_text("\n".join(verdict).lstrip("\n") + "\n")
    sums = []
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name != "SHA256SUMS":
            sums.append("%s  %s" % (hashlib.sha256(p.read_bytes()).hexdigest(), p.name))
    (out / "SHA256SUMS").write_text("\n".join(sums) + "\n")
    print("\n".join(lines))
    print("\nSHA256SUMS:\n" + "\n".join(sums))
    sys.exit(1 if (harness_error or failed or bad_rows) else 0)


if __name__ == "__main__":
    main()
