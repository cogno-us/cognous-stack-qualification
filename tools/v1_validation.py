"""Frozen-V1 validation controller helpers.

SPDX-License-Identifier: Apache-2.0

Subcommands
  plan            emit the GitHub Actions job matrix from the freeze manifest
  freeze-verify   verify every identity recorded in the freeze manifest
  component-suite discover and run one component's own tests at its pinned commit
  aggregate       merge job results; refuse to promote missing, failed or skipped
                  mandatory coverage to PASS

This module never modifies product code, component pins or expected outcomes.
Status vocabulary: PASS, FAIL, INCONCLUSIVE, NOT RUN, NOT APPLICABLE.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUSES = ("PASS", "FAIL", "INCONCLUSIVE", "NOT RUN", "NOT APPLICABLE")
MAX_RETAINED_LOG = 5 * 1024 * 1024  # bytes of gzip retained per log


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(path, *args, check=True, timeout=300):
    proc = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, timeout=timeout)
    if check and proc.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def load_manifest(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def all_components(manifest):
    """Yield (group, key, spec) for every pinned component."""
    for group in ("components_subject", "components_lock_remainder", "components_optional"):
        for key, spec in manifest.get(group, {}).items():
            yield group, key, spec


# ----------------------------------------------------------------- plan
def cmd_plan(args):
    manifest = load_manifest(args.manifest)
    include = []
    for group, key, spec in all_components(manifest):
        oses = ["ubuntu-latest", "windows-latest", "macos-latest"] if group != "components_optional" else ["ubuntu-latest"]
        for os_name in oses:
            pys = ["3.12"] + (["3.11"] if os_name == "ubuntu-latest" and group != "components_optional" else [])
            for py in pys:
                include.append({"component": key, "group": group, "repository": spec["repository"],
                                "sha": spec["sha"], "os": os_name, "python": py,
                                "timeout": int(spec.get("test_timeout_seconds", 300))})
    out = {"include": include}
    text = json.dumps(out, separators=(",", ":"))
    if args.out_file:
        Path(args.out_file).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_file).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    if args.github_output:
        with open(args.github_output, "a", encoding="utf-8") as fh:
            fh.write(f"matrix={text}\n")
    else:
        print(text)


# --------------------------------------------------------- freeze verify
def fetch_exact(repo_dir: Path, repository: str, sha: str):
    repo_dir.mkdir(parents=True, exist_ok=True)
    if not (repo_dir / ".git").exists():
        subprocess.run(["git", "init", "-q", str(repo_dir)], check=True)
        subprocess.run(["git", "-C", str(repo_dir), "remote", "add", "origin", f"https://github.com/{repository}.git"], check=True)
    git(repo_dir, "fetch", "-q", "--depth", "1", "origin", sha, timeout=600)
    git(repo_dir, "checkout", "-q", "--detach", "FETCH_HEAD")
    return git(repo_dir, "rev-parse", "HEAD")


def ls_remote_tag(repository: str, tag: str):
    proc = subprocess.run(["git", "ls-remote", "--tags", f"https://github.com/{repository}.git",
                           f"refs/tags/{tag}", f"refs/tags/{tag}^{{}}"], capture_output=True, text=True, timeout=120)
    peeled = direct = None
    for line in proc.stdout.splitlines():
        sha, ref = line.split("\t")
        if ref.endswith("^{}"):
            peeled = sha
        else:
            direct = sha
    return peeled or direct


def cmd_freeze_verify(args):
    m = load_manifest(args.manifest)
    checks = []

    def check(name, ok, expected=None, actual=None, detail=None):
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "expected": expected, "actual": actual, "detail": detail})

    hub = Path(args.hub_dir)
    qual = Path(args.qual_dir)
    ident = m["identities"]
    hub_head = git(hub, "rev-parse", "HEAD")
    check("hub head equals frozen hub head", hub_head == ident["hub"]["head"], ident["hub"]["head"], hub_head)
    tag_commit = ident["hub"]["tag_commit"]
    check("hub public-reference tag peels to recorded commit",
          ls_remote_tag(ident["hub"]["repository"], ident["hub"]["public_reference_tag"]) == tag_commit, tag_commit)
    anc = subprocess.run(["git", "-C", str(hub), "merge-base", "--is-ancestor", tag_commit, hub_head]).returncode == 0
    check("hub tag commit is an ancestor of hub head", anc)
    changed = sorted(git(hub, "diff", "--name-only", tag_commit, hub_head).splitlines())
    check("hub head differs from tag only by the recorded tag-recording files",
          changed == sorted(ident["hub"]["head_minus_tag_files"]), sorted(ident["hub"]["head_minus_tag_files"]), changed)
    for rel, expected in m["hub_file_hashes"].items():
        p = hub / rel
        actual = sha256_file(p) if p.exists() else None
        check(f"hub file hash {rel}", actual == expected, expected, actual)
    for rel, expected in m["qualification_file_hashes"].items():
        p = qual / rel
        actual = sha256_file(p) if p.exists() else None
        check(f"qualification file hash {rel}", actual == expected, expected, actual)
    q = ident["qualification"]
    anc = subprocess.run(["git", "-C", str(qual), "merge-base", "--is-ancestor", q["closeout"], "HEAD"]).returncode == 0
    check("qualification closeout is an ancestor of the harness checkout", anc, q["closeout"])
    check("qualification public-reference tag peels to closeout",
          ls_remote_tag(q["repository"], q["public_reference_tag"]) == q["tag_commit"] == q["closeout"], q["closeout"])
    rt = ident["runtime"]
    check("runtime public-reference tag peels to recorded sha",
          ls_remote_tag(rt["repository"], rt["public_reference_tag"]) == rt["sha"], rt["sha"])
    check("runtime quarantine tag exists", ls_remote_tag(rt["repository"], rt["quarantine_tag"]) is not None)
    # profile pins agree with manifest
    prof = json.loads((hub / m["profile"]["path"]).read_text())
    byrepo = {s["repository"]: s["sha"] for _, _, s in all_components(m)}
    for name, spec in prof["components"].items():
        check(f"hub profile pin {name} equals manifest", byrepo.get(spec["repository"]) == spec["revision"], spec["revision"], byrepo.get(spec["repository"]))
    qprof = json.loads((qual / m["profile"]["qualification_profile"]).read_text())
    for name, spec in qprof["components"].items():
        check(f"qualification profile pin {name} equals manifest", byrepo.get(spec["repository"]) == spec["revision"], spec["revision"], byrepo.get(spec["repository"]))
    lock = json.loads((hub / "component-lock.json").read_text())
    for key, spec in {**m["components_lock_remainder"], **m["components_optional"]}.items():
        check(f"hub lock pin {key} equals manifest", lock["components"][key]["sha"] == spec["sha"], spec["sha"], lock["components"][key]["sha"])
    # fetch every pinned component exactly
    work = Path(args.work)
    resolved = {}
    for group, key, spec in all_components(m):
        try:
            got = fetch_exact(work / key, spec["repository"], spec["sha"])
            tree = git(work / key, "rev-parse", "HEAD^{tree}")
            resolved[key] = {"repository": spec["repository"], "commit": got, "tree": tree, "group": group}
            check(f"component {key} resolves to pinned commit", got == spec["sha"], spec["sha"], got)
        except Exception as exc:  # noqa: BLE001 - record, never hide
            check(f"component {key} resolves to pinned commit", False, spec["sha"], None, str(exc)[:500])
    out = {"schema": "cognous.v1-validation-freeze-verification/1", "validation_id": m["validation_id"],
           "harness_revision": os.environ.get("GITHUB_SHA") or git(qual, "rev-parse", "HEAD"),
           "workflow_run": os.environ.get("GITHUB_RUN_ID"), "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
           "python": sys.version, "platform": platform.platform(), "components": resolved, "checks": checks,
           "status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL"}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    for c in checks:
        print(("ok   " if c["status"] == "PASS" else "FAIL ") + c["check"])
    sys.exit(0 if out["status"] == "PASS" else 1)


# ------------------------------------------------------- component suite
def run(cmd, cwd, timeout, log):
    start = time.monotonic()
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, errors="replace")
        log.write(f"$ {' '.join(map(str, cmd))}\n{proc.stdout}\n{proc.stderr}\n[exit {proc.returncode}]\n")
        return proc.returncode, proc.stdout, time.monotonic() - start, False
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or b"")
        out = out.decode("utf-8", "replace") if isinstance(out, bytes) else out
        log.write(f"$ {' '.join(map(str, cmd))}\n{out}\n[TIMEOUT after {timeout}s]\n")
        return 124, out, time.monotonic() - start, True


def junit_counts(path: Path):
    if not path.exists():
        return None
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return None
    t = f = e = s = 0
    for tc in root.iter("testcase"):
        t += 1
        if tc.find("failure") is not None:
            f += 1
        if tc.find("error") is not None:
            e += 1
        if tc.find("skipped") is not None:
            s += 1
    return {"testcases": t, "failures": f, "errors": e, "skipped": s}


def retain_log(text: str, dest: Path):
    data = text.encode("utf-8", "replace")
    gz = gzip.compress(data, 9)
    info = {"sha256_uncompressed": hashlib.sha256(data).hexdigest(), "bytes_uncompressed": len(data), "retained": True}
    if len(gz) > MAX_RETAINED_LOG:
        info["retained"] = False
        info["limitation"] = f"gzip log {len(gz)} bytes exceeds {MAX_RETAINED_LOG}; not retained in Git"
    else:
        dest.write_bytes(gz)
        info["file"] = dest.name
    return info


def cmd_component_suite(args):
    repo = Path(args.repo_dir).resolve()
    if args.fetch:
        fetch_exact(repo, args.repository, args.sha)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    actual = git(repo, "rev-parse", "HEAD")
    result = {"schema": "cognous.v1-validation-job/1", "component": args.component, "repository": args.repository,
              "pinned_sha": args.sha, "actual_sha": actual, "os": args.os_name, "python": platform.python_version(),
              "platform": platform.platform(), "workflow_run": os.environ.get("GITHUB_RUN_ID"),
              "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"), "job": os.environ.get("GITHUB_JOB"),
              "attempts": [], "timeout_seconds": args.timeout}
    if actual != args.sha:
        result.update(status="FAIL", classification="setup/harness defect", reason="checked-out commit differs from pin")
        (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        sys.exit(1)
    # inventory (independent of whether tests can run)
    tests_dirs = [str(p.relative_to(repo)).replace("\\", "/") for p in repo.rglob("test*") if p.is_dir() and ".git" not in p.parts and "node_modules" not in p.parts][:50]
    test_files = sorted(str(p.relative_to(repo)).replace("\\", "/") for p in repo.rglob("test_*.py") if ".git" not in p.parts and "node_modules" not in p.parts)
    wfs = sorted(p.name for p in (repo / ".github" / "workflows").glob("*.y*ml")) if (repo / ".github" / "workflows").exists() else []
    runs_on = {}
    wf_dir = repo / ".github" / "workflows"
    for wf in (wf_dir.glob("*.y*ml") if wf_dir.exists() else []):
        txt = wf.read_text(encoding="utf-8", errors="replace")
        found = sorted(set(re.findall(r"runs-on:\s*([^\n#]+)", txt)) | set(re.findall(r"^\s*os:\s*\[([^\]]+)\]", txt, re.M)))
        if found:
            runs_on[wf.name] = [x.strip() for x in found]
    result["inventory"] = {"ci_runs_on": runs_on, "test_dirs": tests_dirs, "test_files": test_files, "test_file_count": len(test_files), "ci_workflows": wfs,
                           "has_pyproject": (repo / "pyproject.toml").exists(), "has_requirements": sorted(p.name for p in repo.glob("requirements*.txt"))}
    py = sys.executable
    log = out / "job.log"
    with open(log, "w", encoding="utf-8") as fh:
        for attempt in (1, 2):
            rec = {"attempt": attempt}
            setup_ok = True
            installs = []
            fh.write(f"==== attempt {attempt}\n")
            run([py, "-m", "pip", "install", "-q", "pytest"], repo, 600, fh)
            if (repo / "pyproject.toml").exists() or (repo / "setup.py").exists():
                for extra in (".[dev,test]", ".[dev]", ".[test]", "."):
                    rc, _, _, _ = run([py, "-m", "pip", "install", "-q", "-e", extra], repo, 900, fh)
                    installs.append({"target": extra, "rc": rc})
                    if rc == 0:
                        break
                setup_ok = bool(installs) and installs[-1]["rc"] == 0
            for req in sorted(repo.glob("requirements*.txt")):
                rc, _, _, _ = run([py, "-m", "pip", "install", "-q", "-r", req.name], repo, 900, fh)
                installs.append({"target": req.name, "rc": rc})
                setup_ok = setup_ok and rc == 0
            rec["installs"] = installs
            rc, freeze, _, _ = run([py, "-m", "pip", "freeze"], repo, 120, fh)
            if attempt == 1:
                (out / "pip-freeze.txt").write_text(freeze, encoding="utf-8")
            junit = out.resolve() / f"junit-attempt{attempt}.xml"
            if not test_files:
                rec.update(outcome="NOT RUN", reason="no test_*.py discovered in this component at the pinned commit")
                result["attempts"].append(rec)
                break
            rc, stdout, secs, timed_out = run([py, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={junit}"], repo, args.timeout, fh)
            counts = junit_counts(junit)
            rec.update(returncode=rc, execution_seconds=round(secs, 2), timed_out=timed_out, counts=counts, setup_ok=setup_ok)
            if timed_out:
                rec.update(outcome="INCONCLUSIVE", reason=f"timeout after {args.timeout}s")
            elif rc == 0 and counts and counts["testcases"] > 0 and counts["failures"] == counts["errors"] == 0:
                rec.update(outcome="PASS")
            elif rc == 5:
                rec.update(outcome="NOT RUN", reason="pytest collected no tests")
            elif counts and (counts["failures"] or counts["errors"]) and counts["testcases"] > 0:
                rec.update(outcome="FAIL", reason="test failures/errors")
            else:
                rec.update(outcome="INCONCLUSIVE", reason="pytest produced no usable JUnit (collection/setup error)")
            result["attempts"].append(rec)
            # at most one automatic retry, only for a plausible setup/transient cause
            retry = (not setup_ok) or (rec["outcome"] == "INCONCLUSIVE" and not timed_out)
            if attempt == 1 and retry:
                continue
            break
    final = result["attempts"][-1]
    result["status"] = final["outcome"]
    result["reason"] = final.get("reason")
    if len(result["attempts"]) > 1:
        result["retry_note"] = "one automatic retry after a plausible setup/transient cause; both attempts preserved"
        if final["outcome"] == "PASS" and result["attempts"][0]["outcome"] != "PASS":
            result["flaky_or_setup"] = True
    result["log"] = retain_log(log.read_text(encoding="utf-8", errors="replace"), out / "job.log.gz")
    log.unlink()
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("component", "os", "python", "status", "reason")}))
    sys.exit(0)  # the aggregate decides; a failing suite is evidence, not a workflow error


def cmd_probe_suite(args):
    """Run the validation probes (suites/v1-probes) against one exactly pinned component. A failing probe is a finding, not a harness error."""
    repo = Path(args.repo_dir).resolve()
    fetch_exact(repo, args.repository, args.sha)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    actual = git(repo, "rev-parse", "HEAD")
    result = {"schema": "cognous.v1-validation-job/1", "component": args.component, "repository": args.repository, "pinned_sha": args.sha,
              "actual_sha": actual, "os": args.os_name, "python": platform.python_version(), "workflow_run": os.environ.get("GITHUB_RUN_ID"),
              "kind": "probe-suite", "attempts": []}
    if actual != args.sha:
        result.update(status="FAIL", classification="setup/harness defect", reason="checked-out commit differs from pin")
        (out / "result.json").write_text(json.dumps(result, indent=2) + "\n"); sys.exit(1)
    py = sys.executable
    junit = out.resolve() / "junit.xml"
    with open(out / "job.log", "w", encoding="utf-8") as fh:
        run([py, "-m", "pip", "install", "-q", "pytest", "httpx"], repo, 600, fh)
        for req in sorted(repo.glob("requirements*.txt")):
            if "dev" in req.name:
                continue
            run([py, "-m", "pip", "install", "-q", "-r", req.name], repo, 900, fh)
        env = dict(os.environ, PROBE_INDEX_DIR=str(repo), PYTHONDONTWRITEBYTECODE="1")
        suite = Path(args.suite).resolve()
        start = time.monotonic()
        proc = subprocess.run([py, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={junit}", str(suite)], cwd=suite, env=env,
                              capture_output=True, text=True, timeout=args.timeout, errors="replace")
        fh.write(proc.stdout + proc.stderr + f"[exit {proc.returncode}]\n")
    counts = junit_counts(junit)
    ran = bool(counts and counts["testcases"] > 0)
    result["attempts"].append({"attempt": 1, "returncode": proc.returncode, "counts": counts, "execution_seconds": round(time.monotonic() - start, 2),
                               "outcome": "PASS" if ran else "INCONCLUSIVE"})
    result["status"] = "PASS" if ran else "INCONCLUSIVE"
    result["reason"] = "probe harness executed; individual probe outcomes are in junit.xml" if ran else "no probe results produced"
    result["log"] = retain_log((out / "job.log").read_text(encoding="utf-8", errors="replace"), out / "job.log.gz")
    (out / "job.log").unlink()
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("component", "status", "reason")}))


# -------------------------------------------------------------- aggregate
def verdict(requirements):
    """Selected-V1 verdict. Never promotes missing, failed or skipped mandatory coverage."""
    mandatory = [r for r in requirements if r.get("mandatory", True)]
    if any(r["status"] == "FAIL" for r in mandatory):
        return "FAIL"
    for r in mandatory:
        if r["status"] == "NOT APPLICABLE":
            if not r.get("not_applicable_reason"):
                return "INCOMPLETE"
        elif r["status"] != "PASS":
            return "INCOMPLETE"
    return "PASS" if mandatory else "INCOMPLETE"


def load_junit_index(inputs: Path, results):
    """component -> list of (classname, name, outcome). Only Linux/3.12 component runs plus single-instance jobs count as selector evidence."""
    index = {}
    for r in results:
        comp = r.get("component")
        if not comp or (r.get("os") not in (None, "ubuntu-latest")) or str(r.get("python", "3.12"))[:4] not in ("3.12", ""):
            continue
        d = inputs / r["_dir"]
        files = sorted(d.glob("junit-attempt*.xml"))[-1:] or sorted(d.rglob("junit.xml"))
        for f in files:
            try:
                root = ET.parse(f).getroot()
            except ET.ParseError:
                continue
            for tc in root.iter("testcase"):
                out = "failed" if (tc.find("failure") is not None or tc.find("error") is not None) else "skipped" if tc.find("skipped") is not None else "passed"
                index.setdefault(comp, []).append((tc.get("classname", ""), tc.get("name", ""), out))
    return index


def evaluate_requirements(doc, index, job_status):
    """Compute each requirement's status from executed evidence. A requirement is PASS only when adequate evidence executed and passed."""
    evaluated = []
    for r in doc.get("requirements", []):
        r = dict(r)
        kind = r.get("kind", "tests")
        r.setdefault("mandatory", True)
        if kind == "tests":
            hits, fails, skips, detail = 0, 0, 0, []
            for sel in r.get("selectors", []):
                rx = re.compile(sel["re"], re.I)
                m = [t for t in index.get(sel["component"], []) if rx.search(f"{t[0]}::{t[1]}")]
                f = [t for t in m if t[2] == "failed"]
                k = [t for t in m if t[2] == "skipped"]
                hits += len(m); fails += len(f); skips += len(k)
                detail.append({"component": sel["component"], "re": sel["re"], "matched": len(m), "failed": len(f), "skipped": len(k), "min": sel.get("min", 1),
                               "failed_tests": [f"{t[0]}::{t[1]}" for t in f][:10]})
            short = any(d["matched"] < d["min"] for d in detail)
            r["selector_results"] = detail
            r["executed_cases"] = hits
            if fails:
                r["status"] = "FAIL"; r.setdefault("classification", "product defect")
            elif short:
                r["status"] = "INCONCLUSIVE"; r["reason"] = "selector matched fewer executed cases than required (job missing or selector defective)"
            elif skips:
                r["status"] = "INCONCLUSIVE"; r["reason"] = "matched cases were skipped"
            elif r.get("adequacy", "adequate") == "adequate":
                r["status"] = "PASS"; r["provenance"] = r.get("provenance", "NEW EXECUTION")
            else:
                r["status"] = "INCONCLUSIVE"
                r["reason"] = "matched cases passed but are declared inadequate for the full requirement: " + r.get("adequacy_note", "partial coverage")
        elif kind == "job":
            st = job_status.get(r["component"])
            r["status"] = st if st in ("PASS", "FAIL") else "INCONCLUSIVE"
            if r["status"] != "PASS":
                r.setdefault("reason", f"job status {st}")
        elif kind == "not_applicable":
            r["status"] = "NOT APPLICABLE"
        else:  # gap / manual: status declared with reason; never promoted
            r["status"] = r.get("declared_status", "NOT RUN")
            if r["status"] == "PASS":
                r["status"] = "INCONCLUSIVE"; r["reason"] = "declared PASS without executed evidence is refused"
        evaluated.append(r)
    return evaluated


def requirements_markdown(reqs):
    lines = ["| ID | Source | Status | Mandatory | Provenance | Cases | Note |", "|---|---|---|---|---|---|---|"]
    for r in reqs:
        note = (r.get("reason") or r.get("not_applicable_reason") or r.get("classification") or "")[:160].replace("|", "/")
        lines.append(f"| {r['id']} | {r.get('source','')} | {r['status']} | {'yes' if r['mandatory'] else 'no'} | {r.get('provenance','')} | {r.get('executed_cases','')} | {note} |")
    return "\n".join(lines) + "\n"


def cmd_aggregate(args):
    inputs = Path(args.inputs)
    results = []
    for p in sorted(inputs.rglob("result.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        r["_dir"] = str(p.parent.relative_to(inputs)).replace("\\", "/")
        results.append(r)
    freeze = None
    for p in inputs.rglob("freeze-verification.json"):
        freeze = json.loads(p.read_text(encoding="utf-8"))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    counts = {s: 0 for s in STATUSES}
    rows = []
    for r in results:
        counts[r.get("status", "INCONCLUSIVE")] = counts.get(r.get("status", "INCONCLUSIVE"), 0) + 1
        att = r["attempts"][-1] if r.get("attempts") else {}
        rows.append({"job": r["_dir"], "component": r.get("component"), "os": r.get("os"), "python": r.get("python"),
                     "status": r.get("status"), "reason": r.get("reason"), "counts": att.get("counts"),
                     "attempts": len(r.get("attempts", []))})
    expected = []
    for p in inputs.rglob("plan.json"):
        expected = json.loads(p.read_text(encoding="utf-8")).get("include", [])
    seen = {(r.get("component"), r.get("os"), str(r.get("python"))[:4]) for r in results}
    missing = []
    for e in expected:
        if (e["component"], e["os"], e["python"][:4]) not in seen:
            missing.append({"component": e["component"], "os": e["os"], "python": e["python"], "status": "INCONCLUSIVE",
                            "reason": "expected job produced no result (setup failure, cancelled or unavailable runner)"})
            counts["INCONCLUSIVE"] += 1
    rows.extend({"job": "(missing)", **m, "counts": None, "attempts": 0} for m in missing)
    requirements = []
    if args.requirements and Path(args.requirements).exists():
        req_doc = json.loads(Path(args.requirements).read_text(encoding="utf-8"))
        job_status = {r.get("component"): r.get("status") for r in results if r.get("os") in (None, "ubuntu-latest") and str(r.get("python", "3.12"))[:4] in ("3.12", "")}
        requirements = evaluate_requirements(req_doc, load_junit_index(inputs, results), job_status)
        (out / "requirements-matrix.json").write_text(json.dumps({"schema": "cognous.v1-validation-matrix/1", "validation_id": args.validation_id, "requirements": requirements}, indent=2) + "\n", encoding="utf-8")
        (out / "requirements-matrix.md").write_text(requirements_markdown(requirements), encoding="utf-8")
    summary = {"schema": "cognous.v1-validation-summary/1", "validation_id": args.validation_id,
               "workflow_run": os.environ.get("GITHUB_RUN_ID"), "freeze_status": (freeze or {}).get("status", "NOT RUN"),
               "job_status_counts": counts, "expected_jobs": len(expected), "missing_jobs": len(missing), "jobs": rows,
               "selected_v1_verdict": "INCOMPLETE" if not requirements else verdict(requirements),
               "verdict_basis": "no requirement matrix supplied: aggregation refuses to promote" if not requirements else "requirement matrix",
               "requirement_status_counts": {st: sum(1 for r in requirements if r["status"] == st) for st in STATUSES},
               "mandatory_requirement_status_counts": {st: sum(1 for r in requirements if r["status"] == st and r["mandatory"]) for st in STATUSES}}
    if freeze is None or freeze.get("status") != "PASS":
        summary["selected_v1_verdict"] = "INCOMPLETE" if summary["selected_v1_verdict"] != "FAIL" else "FAIL"
        summary["verdict_note"] = "freeze verification did not pass; no result may be promoted"
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    lines = [f"## V1 validation {args.validation_id}", "", f"Freeze: **{summary['freeze_status']}** · Verdict: **{summary['selected_v1_verdict']}** ({summary['verdict_basis']})", "",
             "| Status | Jobs |", "|---|---|"] + [f"| {k} | {v} |" for k, v in counts.items()] + ["",
             "| Component | OS | Python | Status | Testcases/fail/err/skip | Reason |", "|---|---|---|---|---|---|"]
    for row in rows:
        c = row["counts"] or {}
        lines.append(f"| {row['component']} | {row['os']} | {row['python']} | {row['status']} | {c.get('testcases','-')}/{c.get('failures','-')}/{c.get('errors','-')}/{c.get('skipped','-')} | {row['reason'] or ''} |")
    md = "\n".join(lines) + "\n"
    (out / "summary.md").write_text(md, encoding="utf-8")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write(md)
    print(md)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("--manifest", required=True); p.add_argument("--github-output"); p.add_argument("--out-file")
    p.set_defaults(fn=cmd_plan)
    p = sub.add_parser("freeze-verify")
    for a in ("--manifest", "--hub-dir", "--qual-dir", "--work", "--out"):
        p.add_argument(a, required=True)
    p.set_defaults(fn=cmd_freeze_verify)
    p = sub.add_parser("component-suite")
    for a in ("--component", "--repository", "--sha", "--repo-dir", "--out", "--os-name"):
        p.add_argument(a, required=True)
    p.add_argument("--timeout", type=int, default=300)
    p.add_argument("--fetch", action="store_true", help="fetch the exact pinned commit into --repo-dir first")
    p.set_defaults(fn=cmd_component_suite)
    p = sub.add_parser("probe-suite")
    for a in ("--component", "--repository", "--sha", "--repo-dir", "--out", "--os-name", "--suite"):
        p.add_argument(a, required=True)
    p.add_argument("--timeout", type=int, default=300)
    p.set_defaults(fn=cmd_probe_suite)
    p = sub.add_parser("aggregate")
    p.add_argument("--inputs", required=True); p.add_argument("--out", required=True)
    p.add_argument("--validation-id", required=True); p.add_argument("--requirements")
    p.set_defaults(fn=cmd_aggregate)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
