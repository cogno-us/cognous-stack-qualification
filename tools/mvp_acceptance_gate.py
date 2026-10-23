#!/usr/bin/env python3
"""MVP acceptance gate (proposed): tuple resolution, checkout verification and the gate verdict. Standard library only.

SPDX-License-Identifier: Apache-2.0

Qualification owns the oracle and every verdict; this tool only reads recorded artifacts and applies the proposed, separately
versioned inputs (process/mvp-acceptance/*). It never edits an expectation, never runs a component and authorizes nothing:
every verdict document says ``authorizes: false`` and ``release: HOLD``.

Subcommands
  resolve           candidate identity inputs + validated per-component overrides -> resolved tuple pin file + tuple-resolved.json
  verify-checkouts  every component checkout is at exactly its resolved 40-hex sha and pristine -> tuple-resolved.json updated
  gate              recorded run artifacts -> gate-verdict.json; exit 0 ACCEPT, 1 REJECT, 2 INCOMPLETE

Verdicts (precedence INCOMPLETE > REJECT > ACCEPT)
  INCOMPLETE  something mandatory did not run to a judgeable result: a battery test that is skipped, not discovered, not executed or
              errored; an oracle row BLOCKED or NOT RUN; an undeclared NOT APPLICABLE; a missing artifact; an environment refusal.
  REJECT      everything ran and at least one mandatory assertion failed (a FAIL row, a failed test, a Verifier disposition that is not
              the expected one, an Exchange module loaded).
  ACCEPT      every mandatory item passed on recorded observations. A proposal for the owner, not an authorization.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SHA40 = re.compile(r"[0-9a-f]{40}")
COMPONENT_DIRS = {"control_plane": "control_plane", "runtime": "runtime", "replay": "replay", "evidence_pack": "evidence_pack",
                  "odes": "odes", "verifier": "verifier", "action_manifest": "manifest", "hub": "hub"}
EXPECTED_COMPONENTS = tuple(COMPONENT_DIRS)
OVERRIDE_ENV = "MVP_OVERRIDE_"  # + component name upper-case, for example MVP_OVERRIDE_RUNTIME
ROOT = Path(__file__).resolve().parents[1]

PASS, FAIL, INCOMPLETE = "PASS", "FAIL", "INCOMPLETE"
ACCEPT, REJECT = "ACCEPT", "REJECT"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(Path(path).read_text())


# ------------------------------------------------------------------------------------------------------------------ resolve
def resolve(identity_path: Path, overrides: dict[str, str], out_pin: Path, out_resolved: Path, github_output: Path | None = None) -> dict:
    identity = load(identity_path)
    components = identity["components"]
    problems = []
    if tuple(sorted(components)) != tuple(sorted(EXPECTED_COMPONENTS)):
        problems.append(f"candidate identity components {sorted(components)} != expected {sorted(EXPECTED_COMPONENTS)}")
    if "exchange" in json.dumps(components).lower():
        problems.append("the candidate identity tuple names an Exchange component (route C is excluded)")
    unknown = sorted(set(overrides) - set(components))
    if unknown:
        problems.append(f"override for unknown component(s) {unknown}")
    resolved, pins = {}, {}
    for name, spec in components.items():
        identity_sha = spec.get("sha")
        override = overrides.get(name) or None
        sha = override or identity_sha
        if not isinstance(sha, str) or not SHA40.fullmatch(sha):
            problems.append(f"{name}: not a pinned 40-hex lower-case commit sha (branches, tags, short or blank values are refused): {sha!r}")
            continue
        if override is not None and not SHA40.fullmatch(override):
            problems.append(f"{name}: override is not a 40-hex sha")
        resolved[name] = {"repository": spec["repository"], "sha": sha, "source": "input-override" if override else "candidate-identity",
                          "identity_sha": identity_sha, "dir": f"components/{COMPONENT_DIRS[name]}"}
        pins[name] = {**spec, "sha": sha}
    if problems:
        raise SystemExit("resolve refused:\n  " + "\n  ".join(problems))
    pin_doc = {"schema": "cognous.mvp-chain-tuple-pin/1",
               "status": "RESOLVED for one mvp-acceptance run from the candidate identity inputs plus recorded overrides; not frozen, not an acceptance",
               "identity_file": str(identity_path), "components": pins,
               "python_requirements": identity.get("python_requirements", {})}
    Path(out_pin).parent.mkdir(parents=True, exist_ok=True)
    Path(out_pin).write_text(json.dumps(pin_doc, indent=2, sort_keys=True) + "\n")
    doc = {"schema": "cognous.mvp-tuple-resolved/1", "identity_file": os.path.relpath(identity_path, ROOT) if Path(identity_path).is_absolute() else str(identity_path),
           "identity_sha256": sha256_file(identity_path), "overrides": {n: c["sha"] for n, c in resolved.items() if c["source"] == "input-override"},
           "components": resolved}
    Path(out_resolved).write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    if github_output:
        with open(github_output, "a") as fh:
            for name, comp in resolved.items():
                fh.write(f"{name}={comp['sha']}\n")
    return doc


def _git(path: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True, text=True, timeout=60).stdout.strip()


def verify_checkouts(resolved_path: Path, base: Path) -> dict:
    doc = load(resolved_path)
    problems = []
    for name, comp in doc["components"].items():
        path = Path(base) / comp["dir"]
        try:
            head = _git(path, "rev-parse", "HEAD")
            dirty = _git(path, "status", "--porcelain", "--untracked-files=all")
            kind = _git(path, "cat-file", "-t", comp["sha"])
        except Exception as exc:  # noqa: BLE001
            comp.update(verified_head=None, pristine=False)
            problems.append(f"{name}: not a readable git checkout ({type(exc).__name__})")
            continue
        comp.update(verified_head=head, pristine=not dirty, object_type=kind)
        if head != comp["sha"]:
            problems.append(f"{name}: HEAD {head} != pinned {comp['sha']}")
        if dirty:
            problems.append(f"{name}: checkout is not pristine")
        if kind != "commit":
            problems.append(f"{name}: {comp['sha']} is a {kind}, not a commit")
    doc["checkout_problems"] = problems
    Path(resolved_path).write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    if problems:
        raise SystemExit("verify-checkouts refused:\n  " + "\n  ".join(problems))
    return doc


# --------------------------------------------------------------------------------------------------------------------- gate
class Gate:
    def __init__(self):
        self.checks = []

    def add(self, check_id: str, status: str, detail: str, **extra):
        self.checks.append({"id": check_id, "status": status, "detail": detail, **extra})

    def verdict(self) -> str:
        statuses = {c["status"] for c in self.checks}
        if INCOMPLETE in statuses:
            return INCOMPLETE
        if FAIL in statuses:
            return REJECT
        return ACCEPT


def _read_json(gate: Gate, check_id: str, path: Path, what: str):
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError:
        gate.add(check_id, INCOMPLETE, f"{what} is missing: {path.name}")
    except (ValueError, OSError) as exc:
        gate.add(check_id, INCOMPLETE, f"{what} is unreadable ({type(exc).__name__}): {path.name}")
    return None


def parse_junit(path: Path) -> dict[str, str]:
    """``file::test`` -> PASSED / FAILED / ERROR / SKIPPED (the worst of duplicates). Raises on a missing or malformed file."""
    order = {"PASSED": 0, "SKIPPED": 1, "FAILED": 2, "ERROR": 3}
    out: dict[str, str] = {}
    for case in ET.parse(path).getroot().iter("testcase"):
        classname, name = case.get("classname") or "", case.get("name") or ""
        key = f"{classname.replace('.', '/')}.py::{name}"
        status = "PASSED"
        for child in case:
            if child.tag == "skipped":
                status = "SKIPPED"
            elif child.tag == "failure":
                status = "FAILED"
            elif child.tag == "error":
                status = "ERROR"
        if key not in out or order[status] > order[out[key]]:
            out[key] = status
    return out


def parse_collected(path: Path) -> set[str]:
    return {line.strip() for line in Path(path).read_text().splitlines() if "::" in line and not line.startswith(("=", "-", " "))}


def check_tuple(gate: Gate, run_dir: Path, repo_root: Path, results: dict | None):
    resolved = _read_json(gate, "G-01", run_dir / "tuple-resolved.json", "resolved tuple")
    if resolved is None:
        return
    problems = []
    comps = resolved.get("components", {})
    if tuple(sorted(comps)) != tuple(sorted(EXPECTED_COMPONENTS)):
        problems.append(f"components {sorted(comps)} != {sorted(EXPECTED_COMPONENTS)}")
    identity_file = repo_root / resolved.get("identity_file", "")
    if not identity_file.is_file():
        problems.append("identity file named by tuple-resolved.json not found")
    elif sha256_file(identity_file) != resolved.get("identity_sha256"):
        problems.append("candidate identity inputs changed after the tuple was resolved")
    for name, comp in comps.items():
        sha = comp.get("sha")
        if not isinstance(sha, str) or not SHA40.fullmatch(sha):
            problems.append(f"{name}: sha is not 40-hex")
        if comp.get("verified_head") != sha:
            problems.append(f"{name}: verified HEAD {comp.get('verified_head')} != pinned {sha}")
        if comp.get("pristine") is not True:
            problems.append(f"{name}: checkout not verified pristine")
        if results is not None:
            seen = (results.get("tuple", {}).get("heads") or {}).get(name)
            if seen != sha:
                problems.append(f"{name}: the suite saw HEAD {seen}, not the pinned {sha}")
    if resolved.get("checkout_problems"):
        problems.extend(resolved["checkout_problems"])
    gate.add("G-01", INCOMPLETE if problems else PASS,
             "exact candidate tuple: every component at its pinned 40-hex sha, pristine, and the suite saw the same heads" if not problems else "; ".join(problems),
             tuple={n: {"sha": c.get("sha"), "source": c.get("source")} for n, c in comps.items()}, overrides=resolved.get("overrides", {}))


def check_oracle(gate: Gate, repo_root: Path, battery: dict, results: dict | None):
    unchanged = battery["oracle"]["unchanged_files_sha256"]
    wrong = {}
    for rel, digest in unchanged.items():
        actual = sha256_file(repo_root / rel) if (repo_root / rel).is_file() else None
        if actual != digest:
            wrong[rel] = {"recorded": digest, "actual": actual}
    gate.add("G-02", FAIL if wrong else PASS,
             "expectations v1, v2 and v3 are byte-identical to their recorded hashes" if not wrong else f"frozen expectation changed: {wrong}")
    if results is not None:
        in_force = battery["oracle"]["unchanged_files_sha256"][battery["oracle"]["expectations_in_force"]]
        used = results.get("expectations_sha256")
        gate.add("G-02b", PASS if used == in_force else FAIL, "the suite judged against expectations v3" if used == in_force
                 else f"the suite used expectations sha256 {used}, not the recorded {in_force}")


def check_battery_covers_oracle(gate: Gate, repo_root: Path, battery: dict):
    expectations = load(repo_root / battery["oracle"]["expectations_in_force"])
    mandatory = {r["id"] for r in expectations["rows"] if r.get("mandatory", True)}
    listed = {t["row"] for t in battery["tests"] if t["kind"] == "oracle_row"}
    missing, extra = sorted(mandatory - listed), sorted(listed - mandatory)
    gate.add("G-03", INCOMPLETE if (missing or extra) else PASS,
             "the battery lists exactly the mandatory rows of the oracle in force" if not (missing or extra)
             else f"battery/oracle mismatch: mandatory rows not in the battery {missing}; battery rows not mandatory {extra}")


def check_environment(gate: Gate, gate_exp: dict, observations: dict | None):
    if observations is None:
        return
    env = observations.get("env", {})
    prefix, minimum = gate_exp["environment"]["python_prefix"], gate_exp["environment"]["pydantic_min"]
    problems = []
    if not str(env.get("python", "")).startswith(prefix):
        problems.append(f"python {str(env.get('python', ''))[:40]!r} does not start with {prefix}")
    version = str(env.get("pydantic_version", ""))
    try:
        parts = tuple(int(x) for x in version.split(".")[:2])
    except ValueError:
        parts = ()
    if not parts or parts < tuple(minimum):
        problems.append(f"pydantic {version!r} < {'.'.join(map(str, minimum))}")
    gate.add("G-04", INCOMPLETE if problems else PASS, "Python 3.13 and pydantic >= 2.12 as observed by the suite" if not problems else "; ".join(problems))


def check_battery_execution(gate: Gate, run_dir: Path, battery: dict, results: dict | None):
    """Discovery, execution and skip accounting for every listed test, against the pytest collection and junit report."""
    collected, junit, absent = {}, {}, []
    for tag, inv in battery["invocations"].items():
        try:
            collected[tag] = parse_collected(run_dir / inv["collected"])
        except OSError:
            absent.append(inv["collected"])
        try:
            junit[tag] = parse_junit(run_dir / inv["junit"])
        except (OSError, ET.ParseError):
            absent.append(inv["junit"])
    if absent:
        gate.add("G-05", INCOMPLETE, f"collection or junit report missing or unreadable: {sorted(absent)}")
        return {}
    rows = results.get("rows", []) if results else []
    row_status = {r["id"]: r["status"] for r in rows}
    declared = {d["id"]: d for d in battery.get("declared_not_applicable", [])}
    per_test, buckets = {}, {"not_discovered": [], "not_executed": [], "skipped": [], "errored": [], "failed": [], "undeclared_not_applicable": [],
                             "blocked_or_not_run": [], "oracle_fail": []}
    for t in battery["tests"]:
        key, tag = f"{t['file']}::{t['test']}", t["invocation"]
        if key not in collected[tag]:
            buckets["not_discovered"].append(t["id"])
            per_test[t["id"]] = "NOT DISCOVERED"
            continue
        status = junit[tag].get(key)
        if status is None:
            buckets["not_executed"].append(t["id"])
            per_test[t["id"]] = "NOT EXECUTED"
        elif status == "SKIPPED":
            buckets["skipped"].append(t["id"])
            per_test[t["id"]] = "SKIPPED"
        elif status == "ERROR":
            buckets["errored"].append(t["id"])
            per_test[t["id"]] = "ERROR"
        elif status == "FAILED":
            buckets["failed"].append(t["id"])
            per_test[t["id"]] = "FAILED"
        else:
            per_test[t["id"]] = "PASSED"
        if t["kind"] == "oracle_row" and status in ("PASSED", "FAILED"):
            verdict = row_status.get(t["row"])
            if verdict == "NOT APPLICABLE" and t["row"] not in declared:
                buckets["undeclared_not_applicable"].append(t["id"])
                per_test[t["id"]] = "NOT APPLICABLE (undeclared)"
            elif verdict in ("BLOCKED", "NOT RUN", None):
                buckets["blocked_or_not_run"].append(t["id"])
                per_test[t["id"]] = f"ORACLE {verdict or 'MISSING'}"
            elif verdict == "FAIL" and status == "PASSED":
                buckets["oracle_fail"].append(t["id"])
    incomplete = {k: v for k, v in buckets.items() if v and k in ("not_discovered", "not_executed", "skipped", "errored",
                                                                  "undeclared_not_applicable", "blocked_or_not_run")}
    failed = {k: v for k, v in buckets.items() if v and k in ("failed", "oracle_fail")}
    if incomplete:
        gate.add("G-05", INCOMPLETE, "zero unexplained skips violated: a mandatory battery test was not judged " + json.dumps(incomplete, sort_keys=True), buckets=buckets)
    else:
        gate.add("G-05", PASS, f"all {len(battery['tests'])} mandatory battery tests were discovered, executed and not skipped; no undeclared NOT APPLICABLE", buckets=buckets)
    if failed:
        gate.add("G-06", FAIL, "mandatory assertions failed " + json.dumps(failed, sort_keys=True), buckets=buckets)
    elif not incomplete:
        gate.add("G-06", PASS, "every mandatory battery test passed")
    return {"per_test": per_test, "collected": {k: len(v) for k, v in collected.items()}}


def check_verifier(gate: Gate, run_dir: Path, gate_exp: dict, observations: dict | None):
    if observations is None:
        return
    verifier = observations.get("chain", {}).get("verifier")
    if not isinstance(verifier, dict):
        gate.add("G-07", INCOMPLETE, "no Verifier observation recorded by the chain scenario")
        return
    spec = gate_exp["verifier"]
    problems_incomplete, problems_fail, captured = [], [], {}
    for run in ("A", "B"):
        exp, obs = spec[f"run_{run}"], verifier.get(run)
        label = f"run {run}"
        if not isinstance(obs, dict):
            problems_incomplete.append(f"{label}: no observation")
            continue
        report_path = run_dir / "artifacts" / "verifier" / f"{run}-report.json"
        if not report_path.is_file():
            problems_incomplete.append(f"{label}: retained report {report_path.name} missing")
            continue
        raw = report_path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != obs.get("report_sha256"):
            problems_fail.append(f"{label}: retained report bytes do not match the recorded report_sha256")
        report = json.loads(raw)
        checks = report["checks"]
        tally = {"checks": len(checks)}
        for verdict in ("confirmed", "could_not_check", "refuted"):
            tally[verdict] = sum(1 for c in checks if c["verdict"] == verdict)
        na = report.get("extensions", {}).get("x-not-applicable", [])
        v4 = {v: sorted(c["check_id"] for c in checks if c["tier"] == "V4" and c["verdict"] == v) for v in ("confirmed", "could_not_check", "refuted")}
        v4_na = sorted(n["check_id"] for n in na if n.get("tier") == "V4")
        captured[run] = {"exit_code": obs.get("exit_code"), "overall": obs.get("overall"), "crashed": obs.get("crashed"), "summary": tally,
                         "report_sha256": obs.get("report_sha256"), "module_path": obs.get("module_path"),
                         "refuted_check_ids": sorted(c["check_id"] for c in checks if c["verdict"] == "refuted"),
                         "could_not_check_ids": sorted(c["check_id"] for c in checks if c["verdict"] == "could_not_check"),
                         "v4": {"confirmed": len(v4["confirmed"]), "could_not_check": len(v4["could_not_check"]), "refuted": len(v4["refuted"]),
                                "could_not_check_ids": v4["could_not_check"], "not_applicable": len(v4_na), "not_applicable_ids": v4_na},
                         "not_applicable_total": len(na)}
        for key, want in (("exit_code", exp["exit_code"]), ("overall", exp["overall"]), ("crashed", exp["crashed"])):
            if obs.get(key) != want:
                problems_fail.append(f"{label}: {key} {obs.get(key)!r} != expected {want!r}")
        if report["summary"] != exp["summary"] or tally != exp["summary"]:
            problems_fail.append(f"{label}: summary {report['summary']} (recomputed {tally}) != expected {exp['summary']}")
        if captured[run]["refuted_check_ids"] != sorted(exp["refuted_check_ids"]):
            problems_fail.append(f"{label}: refuted checks {captured[run]['refuted_check_ids']} != expected {exp['refuted_check_ids']}")
        if captured[run]["could_not_check_ids"] != sorted(exp["could_not_check_ids"]):
            problems_fail.append(f"{label}: abstained checks {captured[run]['could_not_check_ids']} != expected {sorted(exp['could_not_check_ids'])}")
        if "could_not_check_reason_all" in exp:
            reasons = {c["check_id"]: c.get("could_not_check_reason") for c in checks if c["verdict"] == "could_not_check"}
            if set(reasons.values()) != {exp["could_not_check_reason_all"]}:
                problems_fail.append(f"{label}: abstention reasons {sorted(set(map(str, reasons.values())))} != {exp['could_not_check_reason_all']!r}")
        for tier, want in exp.get("tiers", {}).items():
            got = captured[run][tier.lower()]
            for key, value in want.items():
                if got.get(key) != value:
                    problems_fail.append(f"{label}: {tier} {key} {got.get(key)!r} != expected {value!r}")
        if obs.get("module_path_under_pin") is not spec["module_path_under_pin"]:
            problems_fail.append(f"{label}: the Verifier module was not imported from the pinned tree")
    if problems_incomplete:
        gate.add("G-07", INCOMPLETE, "; ".join(problems_incomplete), captured=captured)
    elif problems_fail:
        gate.add("G-07", FAIL, "Verifier disposition differs from the expected exact disposition: " + "; ".join(problems_fail), captured=captured)
    else:
        gate.add("G-07", PASS, "Verifier dispositions exactly as expected: exit 3 ABSTAIN; run B 27/28 confirmed, 1 abstained; V4 4 confirmed, 1 abstained "
                 "(v4.ledger.rows-agree-with-attempts), 2 not applicable; no refutation", captured=captured)


def check_pytest_exits(gate: Gate, run_dir: Path, battery: dict):
    """The recorded pytest exit status of each invocation: 0 (all passed) and 1 (some tests failed, judged per test) are judgeable; 2 interrupted,
    3 internal error, 4 usage error and 5 no tests collected are not."""
    problems, seen = [], {}
    for tag, inv in battery["invocations"].items():
        try:
            code = int((run_dir / inv["exit_file"]).read_text().strip())
        except (OSError, ValueError):
            problems.append(f"{tag}: pytest exit status not recorded ({inv['exit_file']})")
            continue
        seen[tag] = code
        if code not in (0, 1):
            problems.append(f"{tag}: pytest exited {code} (interrupted, internal error, usage error or nothing collected)")
    gate.add("G-09", INCOMPLETE if problems else PASS,
             "each battery pytest invocation ran to completion (exit 0 or 1)" if not problems else "; ".join(problems), exits=seen)


def check_exchange_exclusion(gate: Gate, run_dir: Path, battery: dict, mapping: dict):
    problems_incomplete, problems_fail = [], []
    for tag, inv in battery["invocations"].items():
        doc = None
        try:
            doc = json.loads((run_dir / inv["exclusion_observation"]).read_text())
        except (OSError, ValueError):
            problems_incomplete.append(f"{inv['exclusion_observation']} missing or unreadable")
        if doc is not None:
            for key in ("exchange_modules_loaded", "modules_from_exchange_paths", "sys_path_exchange_entries"):
                if doc.get(key) != []:
                    problems_fail.append(f"{tag}: {key} = {doc.get(key)!r}")
    pattern = re.compile(mapping["banned_exchange_name_pattern"])
    for tag, inv in battery["invocations"].items():
        try:
            for nodeid in parse_collected(run_dir / inv["collected"]):
                if pattern.search(nodeid) or "governed-exchange" in nodeid or "governed_exchange" in nodeid:
                    problems_fail.append(f"{tag}: collected test names Exchange: {nodeid}")
        except OSError:
            pass
    if problems_incomplete:
        gate.add("G-08", INCOMPLETE, "route C exclusion not observed: " + "; ".join(problems_incomplete))
    elif problems_fail:
        gate.add("G-08", FAIL, "route C / Exchange was loaded or collected in the MVP battery: " + "; ".join(problems_fail))
    else:
        gate.add("G-08", PASS, "no Exchange module loaded, no Exchange path on sys.path and no Exchange test collected in any battery invocation (AP-06)")


def run_gate(run_dir: Path, repo_root: Path = ROOT) -> dict:
    run_dir, repo_root = Path(run_dir), Path(repo_root)
    gate = Gate()
    battery = load(repo_root / "process/mvp-acceptance/mandatory-battery.proposed.v1.json")
    gate_exp = load(repo_root / "process/mvp-acceptance/gate-expectations.proposed.v1.json")
    mapping = load(repo_root / "process/mvp-acceptance/mvp-applicability.proposed.v1.json")
    results = _read_json(gate, "G-00", run_dir / "mvp-chain" / "results.json", "mvp-chain results.json")
    observations = _read_json(gate, "G-00b", run_dir / "mvp-chain" / "observations.json", "mvp-chain observations.json")
    chain_dir = run_dir / "mvp-chain"
    check_tuple(gate, run_dir, repo_root, results)
    check_oracle(gate, repo_root, battery, results)
    check_battery_covers_oracle(gate, repo_root, battery)
    check_environment(gate, gate_exp, observations)
    accounting = check_battery_execution(gate, run_dir, battery, results)
    check_verifier(gate, chain_dir, gate_exp, observations)
    check_pytest_exits(gate, run_dir, battery)
    check_exchange_exclusion(gate, run_dir, battery, mapping)
    doc = {"schema": "cognous.mvp-acceptance-gate-verdict/1", "verdict": gate.verdict(), "authorizes": False, "release": "HOLD",
           "note": "Proposed gate over recorded artifacts. ACCEPT is a proposal for the owner, not an authorization, certification or release decision.",
           "battery_sha256": sha256_file(repo_root / "process/mvp-acceptance/mandatory-battery.proposed.v1.json"),
           "gate_expectations_sha256": sha256_file(repo_root / "process/mvp-acceptance/gate-expectations.proposed.v1.json"),
           "applicability_sha256": sha256_file(repo_root / "process/mvp-acceptance/mvp-applicability.proposed.v1.json"),
           "checks": gate.checks, "accounting": accounting,
           "oracle_row_counts": (results or {}).get("counts")}
    return doc


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("resolve")
    r.add_argument("--identity", required=True)
    r.add_argument("--out-pin", required=True)
    r.add_argument("--out-resolved", required=True)
    r.add_argument("--github-output")
    v = sub.add_parser("verify-checkouts")
    v.add_argument("--resolved", required=True)
    v.add_argument("--base", default=".")
    g = sub.add_parser("gate")
    g.add_argument("--run-dir", required=True)
    g.add_argument("--out")
    g.add_argument("--repo-root", default=str(ROOT))
    args = parser.parse_args(argv)
    if args.cmd == "resolve":
        overrides = {n: os.environ[OVERRIDE_ENV + n.upper()] for n in EXPECTED_COMPONENTS if os.environ.get(OVERRIDE_ENV + n.upper())}
        resolve(Path(args.identity), overrides, Path(args.out_pin), Path(args.out_resolved), Path(args.github_output) if args.github_output else None)
        return 0
    if args.cmd == "verify-checkouts":
        verify_checkouts(Path(args.resolved), Path(args.base))
        return 0
    doc = run_gate(Path(args.run_dir), Path(args.repo_root))
    out = Path(args.out) if args.out else Path(args.run_dir) / "gate-verdict.json"
    out.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    for c in doc["checks"]:
        print(f"{c['status']:10} {c['id']:6} {c['detail'][:300]}")
    print(f"gate verdict: {doc['verdict']} (authorizes: false; release: HOLD)")
    return {ACCEPT: 0, REJECT: 1, INCOMPLETE: 2}[doc["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
