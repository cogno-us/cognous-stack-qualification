#!/usr/bin/env python3
"""MVP acceptance gate (proposed): tuple resolution, checkout verification and the gate verdict. Standard library only.

SPDX-License-Identifier: Apache-2.0

Qualification owns the oracle and every verdict; this tool only reads recorded artifacts and applies the proposed, separately
versioned inputs (process/mvp-acceptance/*). It never edits an expectation, never runs a component and authorizes nothing:
every verdict document says ``authorizes: false`` and ``release: HOLD``.

Subcommands
  resolve           candidate identity inputs + validated per-component overrides -> resolved tuple pin file + tuple-resolved.json
  verify-checkouts  every component checkout is at exactly its resolved 40-hex sha and pristine -> tuple-resolved.json updated
  commit            write the versioned candidate commitment (sha256 of the proposed inputs, gate, workflow and mandatory test sources)
  anchor            record main-branch blob ids of the frozen historical files
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
def resolve(identity_path: Path, overrides: dict[str, str], out_pin: Path, out_resolved: Path, github_output: Path | None = None,
            qualification_sha: str | None = None, github_env: Path | None = None, run_id: str | None = None) -> dict:
    identity = load(identity_path)
    components = identity["components"]
    problems = []
    if qualification_sha is None or not SHA40.fullmatch(qualification_sha):
        problems.append(f"the Qualification commit actually run must be a 40-hex sha: {qualification_sha!r}")
    run_id = run_id or hashlib.sha256(os.urandom(32)).hexdigest()[:32]
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
           "identity_sha256": sha256_file(identity_path), "qualification_sha": qualification_sha, "run_id": run_id, "overrides": {n: c["sha"] for n, c in resolved.items() if c["source"] == "input-override"},
           "components": resolved}
    Path(out_resolved).write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    if github_output:
        with open(github_output, "a") as fh:
            for name, comp in resolved.items():
                fh.write(f"{name}={comp['sha']}\n")
            fh.write(f"qualification={qualification_sha}\n")
    if github_env:
        with open(github_env, "a") as fh:
            fh.write(f"MVP_RUN_ID={run_id}\n")
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
            dirty = _git(path, "status", "--porcelain", "--untracked-files=all", "--ignored")
            kind = _git(path, "cat-file", "-t", comp["sha"])
        except Exception as exc:  # noqa: BLE001
            comp.update(verified_head=None, pristine=False)
            problems.append(f"{name}: not a readable git checkout ({type(exc).__name__})")
            continue
        comp.update(verified_head=head, pristine=not dirty, object_type=kind)
        if head != comp["sha"]:
            problems.append(f"{name}: HEAD {head} != pinned {comp['sha']}")
        if dirty:
            problems.append(f"{name}: checkout is not pristine (modified, untracked or ignored files present)")
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


def valid_declaration(battery: dict, entry: dict) -> bool:
    rows = {t["row"] for t in battery["tests"] if t["kind"] == "oracle_row"}
    just = entry.get("justification")
    return entry.get("id") in rows and isinstance(just, str) and bool(just.strip())


def check_declared_not_applicable(gate: Gate, battery: dict):
    bad = [d for d in battery.get("declared_not_applicable", []) if not (isinstance(d, dict) and valid_declaration(battery, d))]
    gate.add("G-03b", INCOMPLETE if bad else PASS, "every declared NOT APPLICABLE names a battery row and has a non-empty justification" if not bad
             else f"invalid declared_not_applicable entries (id must be a battery row, justification non-empty): {bad}")


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
    declared = {d["id"]: d for d in battery.get("declared_not_applicable", []) if isinstance(d, dict) and valid_declaration(battery, d)}
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
            if verdict == "PASS":
                pass
            elif verdict == "NOT APPLICABLE":
                if t["row"] not in declared:
                    buckets["undeclared_not_applicable"].append(t["id"])
                    per_test[t["id"]] = "NOT APPLICABLE (undeclared)"
            elif verdict == "FAIL":
                buckets["oracle_fail"].append(t["id"])
                per_test[t["id"]] = "ORACLE FAIL"
            else:  # BLOCKED, NOT RUN, missing, or any string this gate does not know (KNOWN LIMITATION, XFAIL, ...): never a pass
                buckets["blocked_or_not_run"].append(t["id"])
                per_test[t["id"]] = f"ORACLE {verdict if verdict else 'MISSING'}"
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
        try:
            report = json.loads(raw)
            checks = report["checks"]
            if not isinstance(checks, list) or not all(isinstance(c, dict) and {"check_id", "tier", "verdict"} <= set(c) for c in checks):
                raise ValueError("checks malformed")
            if not isinstance(report.get("summary"), dict):
                raise ValueError("summary missing")
        except (ValueError, KeyError, TypeError) as exc:
            problems_incomplete.append(f"{label}: retained report is malformed ({type(exc).__name__}: {exc})")
            continue
        tally = {"checks": len(checks)}
        for verdict in ("confirmed", "could_not_check", "refuted"):
            tally[verdict] = sum(1 for c in checks if c["verdict"] == verdict)
        na = report.get("extensions", {}).get("x-not-applicable", [])
        v4 = {v: sorted(c["check_id"] for c in checks if c["tier"] == "V4" and c["verdict"] == v) for v in ("confirmed", "could_not_check", "refuted")}
        v4_na = sorted(n["check_id"] for n in na if n.get("tier") == "V4")
        derived_overall = "reject" if tally["refuted"] else ("abstain" if (tally["checks"] == 0 or tally["could_not_check"]) else "accept")
        derived_exit = {"reject": 1, "abstain": 3, "accept": 0}[derived_overall]
        if obs.get("exit_code") != derived_exit or obs.get("overall") not in (None, derived_overall):
            problems_fail.append(f"{label}: recorded exit {obs.get('exit_code')!r}/overall {obs.get('overall')!r} disagree with the retained report (derived {derived_exit}/{derived_overall})")
        captured[run] = {"exit_code": derived_exit, "recorded_exit_code": obs.get("exit_code"), "overall": derived_overall, "crashed": obs.get("crashed"), "summary": tally,
                         "report_sha256": obs.get("report_sha256"), "module_path": obs.get("module_path"),
                         "refuted_check_ids": sorted(c["check_id"] for c in checks if c["verdict"] == "refuted"),
                         "could_not_check_ids": sorted(c["check_id"] for c in checks if c["verdict"] == "could_not_check"),
                         "v4": {"confirmed": len(v4["confirmed"]), "could_not_check": len(v4["could_not_check"]), "refuted": len(v4["refuted"]),
                                "could_not_check_ids": v4["could_not_check"], "not_applicable": len(v4_na), "not_applicable_ids": v4_na},
                         "not_applicable_total": len(na)}
        for key, want in (("exit_code", exp["exit_code"]), ("overall", exp["overall"]), ("crashed", exp["crashed"])):
            got = captured[run][key]
            if got != want:
                problems_fail.append(f"{label}: {key} {got!r} != expected {want!r}")
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


def blob_id(path: Path) -> str:
    data = Path(path).read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()  # noqa: S324  (git object id, not a security hash)


def frozen_files(repo_root: Path) -> list[str]:
    battery = load(repo_root / "process/mvp-acceptance/mandatory-battery.proposed.v1.json")
    mapping = load(repo_root / "process/mvp-acceptance/mvp-applicability.proposed.v1.json")
    return sorted(set(battery["oracle"]["unchanged_files_sha256"]) | set(mapping["historical_files_unchanged"]["files"]))


def anchor(repo: str, ref: str, out: Path, repo_root: Path) -> dict:
    """Record the blob ids the frozen files have on ``ref`` of the repository, read through the GitHub REST API (not from this checkout)."""
    files = {}
    for rel in frozen_files(repo_root):
        proc = subprocess.run(["gh", "api", f"repos/{repo}/contents/{rel}?ref={ref}", "--jq", ".sha"], capture_output=True, text=True, timeout=120)
        files[rel] = {"main_blob": proc.stdout.strip() if proc.returncode == 0 else None, "error": None if proc.returncode == 0 else proc.stderr.strip()[-200:]}
    doc = {"schema": "cognous.mvp-anchor/1", "repo": repo, "ref": ref, "files": files}
    Path(out).write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    return doc


def check_anchor(gate: Gate, run_dir: Path, repo_root: Path):
    """Frozen files must be byte-identical (git blob id) to what the main branch holds, read independently of this checkout.

    Limit: this proves identity with main's current content; it is not an owner approval. Protecting main (CODEOWNERS or branch rules)
    is what makes that content frozen."""
    doc = _read_json(gate, "G-02c", run_dir / "anchor.json", "main-branch anchor")
    if doc is None:
        return
    problems = []
    for rel in frozen_files(repo_root):
        entry = doc.get("files", {}).get(rel)
        main_blob = entry.get("main_blob") if isinstance(entry, dict) else None
        local = blob_id(repo_root / rel) if (repo_root / rel).is_file() else None
        if not main_blob:
            problems.append(f"{rel}: no main-branch blob recorded")
        elif local != main_blob:
            problems.append(f"{rel}: blob {local} != main {main_blob}")
    gate.add("G-02c", INCOMPLETE if any("no main-branch" in x for x in problems) else (FAIL if problems else PASS),
             f"frozen files match the main-branch blobs on {doc.get('ref')}" if not problems else "; ".join(problems))


def check_run_binding(gate: Gate, run_dir: Path, battery: dict, results: dict | None, observations: dict | None, expect_qualification: str | None):
    resolved = _read_json(gate, "G-10", run_dir / "tuple-resolved.json", "resolved tuple")
    if resolved is None:
        return
    run_id, problems = resolved.get("run_id"), []
    if not isinstance(run_id, str) or not run_id:
        problems.append("tuple-resolved.json has no run_id")
    q = resolved.get("qualification_sha")
    if not isinstance(q, str) or not SHA40.fullmatch(q):
        problems.append("tuple-resolved.json has no 40-hex qualification_sha")
    elif expect_qualification is not None and q != expect_qualification:
        problems.append(f"qualification sha recorded {q} != checkout {expect_qualification}")
    if results is not None and results.get("run_id") != run_id:
        problems.append("results.json carries a different run_id")
    if observations is not None and (observations.get("run") or {}).get("run_id") != run_id:
        problems.append("observations.json carries a different run_id")
    for tag, inv in battery["invocations"].items():
        try:
            if json.loads((run_dir / inv["exclusion_observation"]).read_text()).get("run_id") != run_id:
                problems.append(f"{inv['exclusion_observation']} carries a different run_id")
        except (OSError, ValueError):
            pass  # reported by G-08
        try:
            name = ET.parse(run_dir / inv["junit"]).getroot().find("testsuite").get("name") or ""
            if run_id not in name:
                problems.append(f"{inv['junit']} testsuite name does not carry the run_id")
        except (OSError, ET.ParseError, AttributeError):
            pass  # reported by G-05
    try:
        d = json.loads((run_dir / "mvp-chain" / "artifacts" / "ingress-modules.json").read_text())
        if d.get("run_id") != run_id:
            problems.append("ingress-modules.json carries a different run_id")
    except (OSError, ValueError):
        pass
    gate.add("G-10", INCOMPLETE if problems else PASS, "artifacts, junit reports and the recorded Qualification commit belong to this run" if not problems else "; ".join(problems),
             run_id=run_id, qualification_sha=q)
    return resolved


# ------------------------------------------------------------------------------------------------ commitment and environment
COMMITMENT_FILE = "process/mvp-acceptance/candidate-commitment.proposed.v1.json"
ENV_PROFILE_FILE = "process/mvp-acceptance/environment-profile.proposed.v1.json"
SUITE_DIRS = ("suites/mvp-chain", "suites/mvp-applicability")
ABSENT_CANDIDATES = ("conftest.py", "suites/conftest.py", "tox.ini", "setup.cfg", "pyproject.toml")
CONFIG_FILES = ("pytest.ini",)
ENV_RECORDS_DIR = "process/mvp-acceptance/environment-records"


def _entries(root: Path, rel: str) -> list[str]:
    """Every entry (file, symlink to a file, symlink to a directory) under ``rel`` without following links."""
    out = []
    for dirpath, dirnames, filenames in os.walk(Path(root) / rel, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
        for name in sorted(filenames) + [d for d in dirnames if (Path(dirpath) / d).is_symlink()]:
            if name.endswith(".pyc"):
                continue
            out.append(str((Path(dirpath) / name).relative_to(root)))
    return out


def _local_imports(root: Path, rel: str) -> set[str]:
    """Local modules a Python file imports (nested imports included), resolved against the directories the suites put on sys.path."""
    import ast
    root = Path(root)
    path = root / rel
    try:
        tree = ast.parse(path.read_text())
    except (SyntaxError, OSError, UnicodeDecodeError):
        return set()
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [(a.name, 0) for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            names.append((base, node.level))
            names += [((base + "." + a.name).strip("."), node.level) for a in node.names]
    search = [path.parent, root / "suites", root / "suites/operation-identity", root / "tools"]
    found = set()
    for name, level in names:
        dirs = [path.parent.parents[level - 1] if level > 1 else path.parent] if level else search
        parts = name.split(".") if name else []
        for i in range(len(parts), 0, -1):
            for d in dirs:
                for cand in (d.joinpath(*parts[:i]).with_suffix(".py"), d.joinpath(*parts[:i], "__init__.py")):
                    if cand.is_file():
                        found.add(str(cand.relative_to(root)))
        if level and not parts:
            found.add(str((path.parent / "__init__.py").relative_to(root))) if (path.parent / "__init__.py").is_file() else None
    return found


def commit_files(repo_root: Path) -> list[str]:
    """Every file whose bytes the qualification candidate commits to: ALL files under the two mandatory suites, the transitive closure of the
    local modules they import (including other suites and tools), the gate, the workflow and the lock files it references, pytest.ini, the
    proposed inputs and every process/mvp-chain and process/mvp-acceptance file (except the commitment itself and the environment records,
    which are evidence checked by an independent hash)."""
    root = Path(repo_root)
    files = {"tools/mvp_acceptance_gate.py", ".github/workflows/mvp-acceptance.yml"}
    for sub in SUITE_DIRS:
        files.update(_entries(root, sub))
    for sub in ("process/mvp-chain", "process/mvp-acceptance"):
        files.update(f for f in _entries(root, sub) if f != COMMITMENT_FILE and not f.startswith(ENV_RECORDS_DIR + "/"))
    files.update(f for f in CONFIG_FILES if (root / f).exists() or (root / f).is_symlink())
    wf = (root / ".github/workflows/mvp-acceptance.yml").read_text()
    for lock in sorted(set(re.findall(r"\.github/locks/[A-Za-z0-9._-]+", wf))):
        for cand in (lock, re.sub(r"\.txt$", ".in", lock)):
            if (root / cand).exists() or (root / cand).is_symlink():
                files.add(cand)
    frontier = {f for f in files if f.endswith(".py")}
    while frontier:
        nxt = set()
        for rel in frontier:
            for dep in _local_imports(root, rel):
                if dep not in files:
                    files.add(dep)
                    nxt.add(dep)
        frontier = nxt
    return sorted(files)


def absent_files(repo_root: Path) -> list[str]:
    return sorted(c for c in ABSENT_CANDIDATES if not (Path(repo_root) / c).exists() and not (Path(repo_root) / c).is_symlink())


def symlinks_in(repo_root: Path, rels) -> list[str]:
    """Committed paths that are, or sit below, a symbolic link."""
    root, bad = Path(repo_root), set()
    for rel in rels:
        cur = root
        for part in Path(rel).parts:
            cur = cur / part
            if cur.is_symlink():
                bad.add(str(cur.relative_to(root)))
    return sorted(bad)


def build_commitment(repo_root: Path, out: Path) -> dict:
    root = Path(repo_root)
    files = commit_files(root)
    links = symlinks_in(root, files)
    if links:
        raise SystemExit(f"commit refused: symbolic links in the committed set: {links}")
    doc = {"schema": "cognous.mvp-qualification-candidate-commitment/1", "candidate_version": "mvp-qualification-candidate-v1",
           "status": "PROPOSED; pending independent Qualification acceptance and freeze (target 2026-10-27). Not frozen, not an acceptance; release HOLD.",
           "supersession": "A change to any listed file is a NEW candidate: write candidate-commitment.proposed.v2.json (and new versions of the changed inputs) and re-run. "
                           "This file is never edited in place once frozen, and the gate compares the committed list to the files present, so an added, removed or changed "
                           "mandatory test, imported module, input, lock file, pytest.ini, gate or workflow is refused, as is any symbolic link in the set.",
           "independence": "The sha256 of THIS file must be supplied to the gate from outside this checkout (workflow input candidate_commitment_sha256, recorded by Qualification). "
                           "Without it the verdict is INCOMPLETE.",
           "inherent_limit": "The gate and the workflow that evaluate this commitment come from the same checkout, so a changed gate could report PASS. An independent reviewer must pin "
                             "this commitment hash AND the gate code (tools/mvp_acceptance_gate.py is itself listed here, but its listing is only meaningful against a hash held outside the checkout).",
           "scope": "all files under suites/mvp-chain and suites/mvp-applicability; the transitive closure of local modules they import (static import analysis); pytest.ini; the lock files "
                    "the workflow references; process/mvp-chain and process/mvp-acceptance (except this file and environment-records/, which are evidence checked by an independent hash).",
           "must_remain_absent": absent_files(root),
           "files": {rel: sha256_file(root / rel) for rel in files}}
    Path(out).write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    return doc


def check_commitment(gate: Gate, repo_root: Path, expect_sha: str | None, commitment_rel: str = COMMITMENT_FILE):
    path = Path(repo_root) / commitment_rel
    if not path.is_file():
        gate.add("G-12", INCOMPLETE, f"candidate commitment {commitment_rel} is missing")
        return None
    actual = sha256_file(path)
    if not expect_sha or not re.fullmatch(r"[0-9a-f]{64}", expect_sha):
        gate.add("G-12", INCOMPLETE, "no independently supplied sha256 of the candidate commitment file (candidate_commitment_sha256): the candidate is not anchored outside this checkout",
                 commitment_sha256=actual)
        return actual
    if actual != expect_sha:
        gate.add("G-12", FAIL, f"candidate commitment file sha256 {actual} != the independently supplied {expect_sha}: a changed candidate must be a new versioned candidate", commitment_sha256=actual)
        return actual
    doc = load(path)
    committed, present = doc.get("files", {}), commit_files(repo_root)
    problems = []
    uncommitted = sorted(set(present) - set(committed))
    removed = sorted(set(committed) - set(present))
    if uncommitted:
        problems.append(f"files present but not committed (tests, imported modules, inputs, locks, config, gate or workflow added): {uncommitted}")
    if removed:
        problems.append(f"committed files absent: {removed}")
    links = symlinks_in(repo_root, set(present) | set(committed))
    if links:
        problems.append(f"symbolic links in or above the committed set: {links}")
    planted = sorted(c for c in doc.get("must_remain_absent", []) if (Path(repo_root) / c).exists() or (Path(repo_root) / c).is_symlink())
    if planted:
        problems.append(f"files that must remain absent now exist (they would change collection or configuration): {planted}")
    for rel in sorted(set(committed) & set(present)):
        if (Path(repo_root) / rel).is_file() and sha256_file(Path(repo_root) / rel) != committed[rel]:
            problems.append(f"{rel}: bytes differ from the commitment")
    gate.add("G-12", FAIL if problems else PASS,
             f"{doc.get('candidate_version')}: {len(committed)} files (suite sources, imported modules, inputs, lock files, pytest.ini, gate, workflow) match the commitment, "
             "whose sha256 equals the independently supplied value; no symlinks" if not problems else "; ".join(problems),
             commitment_sha256=actual, candidate_version=doc.get("candidate_version"))
    return actual


def check_uncommitted_tests(gate: Gate, run_dir: Path, battery: dict):
    """Any test collected from a battery invocation that is neither mandatory nor listed as non-mandatory is an uncommitted test."""
    known = {f"{t['file']}::{t['test']}" for t in battery["tests"]} | {f"{t['file']}::{t['test']}" for t in battery.get("non_mandatory_tests", [])}
    extra = {}
    for tag, inv in battery["invocations"].items():
        try:
            names = parse_collected(run_dir / inv["collected"])
        except OSError:
            continue  # reported by G-05
        extra[tag] = sorted(names - known)
    flat = [x for v in extra.values() for x in v]
    gate.add("G-13", INCOMPLETE if flat else PASS, "every collected test is a committed mandatory test or a committed non-mandatory test" if not flat
             else f"collected tests that are not in the committed battery: {flat[:10]}")


def check_pending_rows(gate: Gate, battery: dict):
    bad = [p for p in battery.get("pending_rows", []) if not isinstance(p, dict) or p.get("rows") != [] or not p.get("placeholder")]
    gate.add("G-14", INCOMPLETE if bad else PASS, "pending row placeholders hold no rows (none invented before Qualification freezes the predicate)" if not bad
             else f"a pending placeholder carries rows before its predicate is frozen: {bad}")


def check_interpreter(gate: Gate, require: str | None):
    if not require:
        gate.add("G-04b", INCOMPLETE, "--require-python not given: the gate did not assert its interpreter")
        return
    ok = f"{sys.version_info[0]}.{sys.version_info[1]}" == require and sys.implementation.name == "cpython"
    gate.add("G-04b", PASS if ok else INCOMPLETE, f"the gate runs on CPython {require}" if ok else
             f"the gate runs on {sys.implementation.name} {sys.version.split()[0]}, not CPython {require}; a result from any other interpreter (for example 3.12) is supplementary and cannot qualify the profile")


def _record_digest(rec: dict) -> str:
    body = {k: v for k, v in rec.items() if k != "record_sha256"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def check_environment_record(gate: Gate, run_dir: Path, repo_root: Path, components_dir: Path | None = None, expect_record_sha: str | None = None,
                             observations: dict | None = None):
    """The hub environment record (mvp-ingress-env-record/1) must be PASS on the selected profile; BLOCKED (Yama absent, not root, ...) is INCOMPLETE."""
    profile = load(Path(repo_root) / ENV_PROFILE_FILE)["hub_record"]
    rec = _read_json(gate, "G-11", run_dir / "environment-record.json", "hub environment record (none supplied)")
    if rec is None:
        return
    record_path = run_dir / "environment-record.json"
    resolved = load(run_dir / "tuple-resolved.json") if (run_dir / "tuple-resolved.json").is_file() else {"components": {}}
    tuple_shas = {c.get("sha") for c in resolved.get("components", {}).values()}
    incomplete, fail = [], []
    if record_path.is_symlink():
        fail.append("the staged environment record is a symbolic link")
    if not expect_record_sha or not re.fullmatch(r"[0-9a-f]{64}", expect_record_sha):
        incomplete.append("no independently supplied sha256 of the environment record file (environment_record_sha256)")
    elif sha256_file(record_path) != expect_record_sha:
        fail.append("environment record file sha256 differs from the independently supplied value")
    if rec.get("schema") != profile["schema"]:
        fail.append(f"schema {rec.get('schema')!r} != {profile['schema']!r}")
    if rec.get("record_sha256") != _record_digest(rec):
        fail.append("record_sha256 does not match the record body (altered or hand-edited)")
    checks = {c.get("id"): c for c in rec.get("checks", []) if isinstance(c, dict)}
    derived = "FAIL" if any(c.get("status") == "FAIL" for c in checks.values()) else ("BLOCKED" if any(c.get("status") == "BLOCKED" for c in checks.values()) else "PASS")
    if rec.get("overall") != derived:
        fail.append(f"recorded overall {rec.get('overall')!r} disagrees with its checks ({derived})")
    if derived == "FAIL":
        fail.append("record has FAIL checks: " + ", ".join(sorted(i for i, c in checks.items() if c.get("status") == "FAIL")))
    if derived == "BLOCKED":
        incomplete.append("record has BLOCKED checks (a precondition could not be verified): " + ", ".join(sorted(i for i, c in checks.items() if c.get("status") == "BLOCKED")))
    for cid in profile["required_pass_check_ids"]:
        st = (checks.get(cid) or {}).get("status")
        if st is None:
            incomplete.append(f"required check {cid} absent from the record")
        elif st != "PASS" and st not in ("FAIL", "BLOCKED"):
            fail.append(f"required check {cid} has status {st!r}")
        elif st != "PASS" and cid == "isolation.ptrace_scope" and st == "BLOCKED":
            incomplete.append("Yama absent or unreadable: the exact profile is unsupported, the boundary test is BLOCKED")
    py = rec.get("python") or {}
    if not str(py.get("version", "")).startswith(profile["python_version_prefix"] + ".") or py.get("implementation") != "CPython":
        fail.append(f"python {py.get('implementation')} {py.get('version')} is not CPython {profile['python_version_prefix']}")
    scope = (rec.get("isolation_limits") or {}).get("yama_ptrace_scope")
    if scope not in ("1", "2", "3"):
        (incomplete if scope is None else fail).append(f"kernel.yama.ptrace_scope {scope!r} (profile requires >= 1; absent is unsupported)")
    if any((c.get("data") or {}).get("relaxed") for c in checks.values()):
        fail.append("a requirement was relaxed (for example a root ingress): not a qualifying configuration")
    # run binding
    for key, want in (("run_id", resolved.get("run_id")), ("qualification_sha", resolved.get("qualification_sha"))):
        if key not in rec:
            incomplete.append(f"record carries no {key}: it cannot be bound to this run")
        elif rec.get(key) != want:
            fail.append(f"record {key} {rec.get(key)!r} != this run's {want!r}")
    # interpreter version equals the one the suite ran on
    seen = str((observations or {}).get("env", {}).get("python", "")).split(" ")[0]
    if not seen:
        incomplete.append("the suite's interpreter version was not observed")
    elif py.get("version") != seen:
        fail.append(f"record python {py.get('version')!r} != the suite's interpreter {seen!r}")
    # ingress sources at the tuple sha
    recorded_src = (rec.get("configuration") or {}).get("ingress_source_sha256")
    hub = Path(components_dir) / COMPONENT_DIRS["hub"] / "tools" / "mvp_ingress" if components_dir else None
    if not isinstance(recorded_src, dict) or not recorded_src:
        incomplete.append("record has no configuration.ingress_source_sha256")
    elif hub is None or not hub.is_dir():
        incomplete.append("no hub checkout available to compare ingress_source_sha256")
    else:
        actual_src = {"tools/mvp_ingress/" + f.name: sha256_file(f) for f in sorted(hub.glob("*.py"))}
        if recorded_src != actual_src:
            fail.append("record ingress_source_sha256 differs from the hub files at the tuple sha: " + ", ".join(sorted(set(recorded_src) ^ set(actual_src) | {k for k in recorded_src if k in actual_src and recorded_src[k] != actual_src[k]})))
    # ipc, group policy, separate IPC directory, non-root ingress
    ipc = rec.get("ipc") or {}
    policy = (ipc.get("connection_policy") or {}).get("socket_group_policy")
    if policy is None:
        incomplete.append("record has no ipc.connection_policy.socket_group_policy")
    elif policy != profile["ipc"]["socket_group_policy"]:
        fail.append(f"socket_group_policy {policy!r} != {profile['ipc']['socket_group_policy']!r}")
    st = ipc.get("stat") if isinstance(ipc.get("stat"), dict) else None
    if st is None or "mode" not in st:
        incomplete.append("record has no ipc.stat (socket mode and type)")
    else:
        if st.get("mode") != profile["ipc"]["socket_mode"] or st.get("type") != profile["ipc"]["socket_type"]:
            fail.append(f"socket mode/type {st.get('mode')}/{st.get('type')} != {profile['ipc']['socket_mode']}/{profile['ipc']['socket_type']}")
        state_dir = (rec.get("filesystem") or {}).get("state_dir")
        sock = st.get("path")
        if not state_dir or not sock:
            incomplete.append("record lacks the socket path or state dir needed to show a separate IPC directory")
        else:
            sd = os.path.normpath(state_dir)
            sdir = os.path.normpath(os.path.dirname(sock))
            if sdir == sd or sdir.startswith(sd + os.sep):
                fail.append(f"the socket directory {sdir} is the ingress state directory or inside it")
    ident = rec.get("process_identity") or {}
    ing = ident.get("ingress_uid")
    ing_proc = ident.get("ingress_process") if isinstance(ident.get("ingress_process"), dict) else {}
    if ing is None:
        incomplete.append("record has no process_identity.ingress_uid")
    elif ing == 0 or ing_proc.get("uid") == 0:
        fail.append("the ingress runs as uid 0 (a non-root dedicated uid is mandatory)")
    pins = [v for v in ((rec.get("configuration") or {}).get("source_pins") or {}).values() if isinstance(v, str) and SHA40.fullmatch(v)]
    if not pins:
        incomplete.append("the record pins no component sha: it cannot be tied to the selected tuple")
    elif not set(pins) <= tuple_shas:
        fail.append(f"record pins {sorted(set(pins) - tuple_shas)} are not members of the selected tuple")
    status = INCOMPLETE if incomplete else (FAIL if fail else PASS)
    if fail and not incomplete:
        status = FAIL
    gate.add("G-11", status, "hub environment record is PASS on the selected profile (CPython 3.13, Yama ptrace_scope >= 1, non-root ingress, actual identities, tuple pins)"
             if status == PASS else "; ".join(fail + incomplete), record_sha256=rec.get("record_sha256"), overall=rec.get("overall"))


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
    roots = tuple(mapping["banned_exchange_module_roots"])
    path_pattern = re.compile(mapping["banned_exchange_path_pattern"])
    dump = None
    try:
        dump = json.loads((run_dir / "mvp-chain" / "artifacts" / "ingress-modules.json").read_text())
    except (OSError, ValueError):
        problems_incomplete.append("mvp-chain/artifacts/ingress-modules.json missing or unreadable (the ingress process's loaded modules were not recorded)")
    if dump is not None:
        mods = dump.get("modules", {})
        loaded = sorted(m for m in mods if m.split(".")[0] in roots)
        by_file = sorted(m for m, f in mods.items() if isinstance(f, str) and path_pattern.search(f))
        paths = [x for x in dump.get("sys_path", []) if isinstance(x, str) and path_pattern.search(x)]
        if not mods:
            problems_incomplete.append("ingress module dump is empty")
        if loaded or by_file or paths:
            problems_fail.append(f"ingress process: modules {loaded}, from exchange paths {by_file}, sys.path {paths}")
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
        gate.add("G-08", PASS, "no Exchange module loaded or Exchange path on sys.path in any battery pytest process or in the ingress server process, and no Exchange test collected (AP-06)")


def run_gate(run_dir: Path, repo_root: Path = ROOT, expect_qualification: str | None = None, expect_commitment: str | None = None,
             require_python: str | None = None, components_dir: Path | None = None, expect_record_sha: str | None = None) -> dict:
    run_dir, repo_root = Path(run_dir), Path(repo_root)
    gate = Gate()
    battery = load(repo_root / "process/mvp-acceptance/mandatory-battery.proposed.v1.json")
    gate_exp = load(repo_root / "process/mvp-acceptance/gate-expectations.proposed.v1.json")
    mapping = load(repo_root / "process/mvp-acceptance/mvp-applicability.proposed.v1.json")
    results = _read_json(gate, "G-00", run_dir / "mvp-chain" / "results.json", "mvp-chain results.json")
    observations = _read_json(gate, "G-00b", run_dir / "mvp-chain" / "observations.json", "mvp-chain observations.json")
    chain_dir = run_dir / "mvp-chain"
    accounting, resolved = {}, None

    def guarded(check_id, fn, *args):
        """A malformed or unexpected artifact is an incomplete verdict, never a crash and never a missing verdict document."""
        try:
            return fn(*args)
        except Exception as exc:  # noqa: BLE001
            gate.add(check_id, INCOMPLETE, f"{check_id} could not be evaluated ({type(exc).__name__}: {str(exc)[:200]})")
            return None

    guarded("G-01", check_tuple, gate, run_dir, repo_root, results)
    guarded("G-02", check_oracle, gate, repo_root, battery, results)
    guarded("G-02c", check_anchor, gate, run_dir, repo_root)
    guarded("G-03", check_battery_covers_oracle, gate, repo_root, battery)
    guarded("G-03b", check_declared_not_applicable, gate, battery)
    guarded("G-04", check_environment, gate, gate_exp, observations)
    guarded("G-04b", check_interpreter, gate, require_python)
    guarded("G-11", check_environment_record, gate, run_dir, repo_root, components_dir, expect_record_sha, observations)
    commitment_sha = guarded("G-12", check_commitment, gate, repo_root, expect_commitment)
    guarded("G-13", check_uncommitted_tests, gate, run_dir, battery)
    guarded("G-14", check_pending_rows, gate, battery)
    accounting = guarded("G-05", check_battery_execution, gate, run_dir, battery, results) or {}
    guarded("G-07", check_verifier, gate, chain_dir, gate_exp, observations)
    guarded("G-09", check_pytest_exits, gate, run_dir, battery)
    guarded("G-08", check_exchange_exclusion, gate, run_dir, battery, mapping)
    resolved = guarded("G-10", check_run_binding, gate, run_dir, battery, results, observations, expect_qualification)
    doc = {"schema": "cognous.mvp-acceptance-gate-verdict/1", "verdict": gate.verdict(), "authorizes": False, "release": "HOLD",
           "candidate_commitment_sha256": commitment_sha, "gate_python": sys.version.split()[0], "run_id": (resolved or {}).get("run_id"), "qualification_sha": (resolved or {}).get("qualification_sha"),
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
    r.add_argument("--github-env")
    r.add_argument("--qualification-sha", required=True)
    a_ = sub.add_parser("anchor")
    a_.add_argument("--repo", required=True)
    a_.add_argument("--ref", default="main")
    a_.add_argument("--out", required=True)
    a_.add_argument("--repo-root", default=str(ROOT))
    v = sub.add_parser("verify-checkouts")
    v.add_argument("--resolved", required=True)
    v.add_argument("--base", default=".")
    g = sub.add_parser("gate")
    g.add_argument("--run-dir", required=True)
    g.add_argument("--out")
    g.add_argument("--repo-root", default=str(ROOT))
    g.add_argument("--expect-qualification-sha")
    g.add_argument("--expect-commitment-sha256")
    g.add_argument("--require-python")
    g.add_argument("--components-dir")
    g.add_argument("--expect-environment-record-sha256")
    c_ = sub.add_parser("commit")
    c_.add_argument("--repo-root", default=str(ROOT))
    c_.add_argument("--out", default=COMMITMENT_FILE)
    args = parser.parse_args(argv)
    if args.cmd == "resolve":
        overrides = {n: os.environ[OVERRIDE_ENV + n.upper()] for n in EXPECTED_COMPONENTS if os.environ.get(OVERRIDE_ENV + n.upper())}
        resolve(Path(args.identity), overrides, Path(args.out_pin), Path(args.out_resolved), Path(args.github_output) if args.github_output else None,
                qualification_sha=args.qualification_sha, github_env=Path(args.github_env) if args.github_env else None)
        return 0
    if args.cmd == "commit":
        build_commitment(Path(args.repo_root), Path(args.repo_root) / args.out)
        return 0
    if args.cmd == "anchor":
        anchor(args.repo, args.ref, Path(args.out), Path(args.repo_root))
        return 0
    if args.cmd == "verify-checkouts":
        verify_checkouts(Path(args.resolved), Path(args.base))
        return 0
    doc = run_gate(Path(args.run_dir), Path(args.repo_root), args.expect_qualification_sha, args.expect_commitment_sha256, args.require_python,
                   Path(args.components_dir) if args.components_dir else None, args.expect_environment_record_sha256)
    out = Path(args.out) if args.out else Path(args.run_dir) / "gate-verdict.json"
    out.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    for c in doc["checks"]:
        print(f"{c['status']:10} {c['id']:6} {c['detail'][:300]}")
    print(f"gate verdict: {doc['verdict']} (authorizes: false; release: HOLD)")
    return {ACCEPT: 0, REJECT: 1, INCOMPLETE: 2}[doc["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
