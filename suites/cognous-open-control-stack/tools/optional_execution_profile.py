#!/usr/bin/env python3
"""Run a selected optional synthetic profile against the accepted component lock."""
from __future__ import annotations
import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ("control_plane", "moltbot_safe", "action_manifest", "gax_imx_transport", "replay_bundle")
# Importable source roots a strict-source runtime profile verifies besides the Control Plane and runtime checkouts.
STRICT_SOURCE_COMPONENTS = (("replay_bundle", "src"), ("odes", "src"), ("governance_evidence_pack", "src"))
# Adds jsonschema (and PyYAML) only; the pytest and pydantic versions a suite already installed from its own lock are untouched.
JSONSCHEMA_LOCK = "jsonschema-pyyaml-c943d3.txt"


def validate_checkout(path, sha):
    """Reject all extra files, including ignored imports; never delete caller data.

    The operator must exclude concurrent writers for the duration of execution.
    Git identity and this preflight do not authenticate a compromised host.
    """
    actual = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True, timeout=10).strip()
    dirty = subprocess.check_output(['git', '-C', str(path), 'status', '--porcelain',
                                    '--untracked-files=all', '--ignored=matching'], text=True, timeout=10)
    if actual != sha or dirty:
        raise RuntimeError(f'{path.name}: checkout must be pristine including ignored files and match {sha}; use a fresh private work directory')
    # Tracked escaping symlinks can import bytes outside the pinned tree.
    for row in subprocess.check_output(['git', '-C', str(path), 'ls-files', '--stage', '-z'], timeout=10).split(b'\0'):
        if row.startswith(b'120000 '):
            target = path / os.fsdecode(row.split(b'\t', 1)[1])
            if not target.resolve().is_relative_to(path.resolve()):
                raise RuntimeError(f'{path.name}: escaping tracked symlink')
    return actual


def strict_sources_required(lock):
    """True for the runtime profiles that verify every candidate source before import (gax_ref_runtime STRICT_SOURCE_PROFILES)."""
    profile = lock.get("runtime_profile", "")
    return profile.startswith("security-runtime-") or profile == "typed-refusal-candidate-20261015"


def ensure_jsonschema():
    """The Replay Bundle importer imports jsonschema. Install the hash-locked set when it is missing; never an unpinned one.

    The lock is looked up in this checkout and in the canonical qualification checkout placed beside it by the workflows.
    """
    try:
        import jsonschema  # noqa: F401
        return
    except ImportError:
        pass
    for base in (ROOT, ROOT / "_qualification"):
        lock = base / ".github/locks" / JSONSCHEMA_LOCK
        if lock.is_file():
            subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "--require-hashes", "-r", str(lock)],
                           check=True, timeout=300)
            return
    raise RuntimeError("jsonschema is required by the selected runtime profile; install the hash-locked set " + JSONSCHEMA_LOCK)


def strict_source_paths(lock, work, *, clone=False):
    """PYTHONPATH entries for the extra sources a strict-source runtime profile needs, each at its lock sha.

    Replay Bundle, ODES and the Governance Evidence Pack are cloned (when ``clone``) and verified pristine, including ignored
    files, exactly like the other pinned checkouts. Returns an empty list for profiles that do not verify them.
    """
    if not strict_sources_required(lock):
        return []
    ensure_jsonschema()
    paths = []
    for name, subdir in STRICT_SOURCE_COMPONENTS:
        spec = lock["components"][name]
        sha = spec.get("sha") or spec["accepted_sha"]
        dest = work / name
        if not dest.exists() and clone:
            subprocess.run(["git", "clone", "--quiet", "--no-checkout", "https://github.com/" + spec["repository"] + ".git", str(dest)],
                           check=True, timeout=180)
            subprocess.run(["git", "checkout", "--quiet", "--detach", sha], cwd=dest, check=True, timeout=60)
        validate_checkout(dest, sha)
        paths.append(str(dest / subdir))
    return paths


def historical_fixture_workflow(workflow_class, /, **kwargs):
    """Build a Control Plane workflow whose caller-supplied evaluation time is honoured, for fixtures dated 2026-08-08.

    Since the service-time change the Control Plane evaluates every decision at its own clock unless the workflow is built with
    ``allow_test_time=True`` (records then carry ``time_source: test_override``). These fixtures were authored for caller-supplied
    time, so their evidence is evaluable only under that documented opt-in. The pinned runtime adapter forwards the flag to the
    per-call workflow view it builds at effect time only when a runtime authority profile is configured; these fixtures use none,
    so the flag is forwarded here, otherwise decide() would authorise and execute() would then refuse every effect against the
    wall clock. Nothing else changes: the caller still supplies every ``now`` and every expected decision is untouched.
    """
    if "allow_test_time" in inspect.signature(workflow_class.__init__).parameters:
        kwargs.setdefault("allow_test_time", True)
    # A Control Plane that predates the option always evaluated at the caller-supplied time, so nothing is needed there.
    try:
        from engine import control_plane_adapter as adapter
    except ImportError:
        adapter = None
    original = getattr(adapter, "workflow_view_profile_kwargs", None)
    if original is not None and not getattr(original, "forwards_test_time", False):
        def forwarding(workflow):
            out = original(workflow)
            if getattr(workflow, "allow_test_time", False):
                out["allow_test_time"] = True
            return out
        forwarding.forwards_test_time = True
        adapter.workflow_view_profile_kwargs = forwarding
    return workflow_class(**kwargs)


def qualification_environment():
    env = os.environ.copy()
    for key in tuple(env):
        if key.startswith('PYTHON'):
            del env[key]
    env.update(PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1')
    return env


def separate_output(out, work):
    if out.resolve().is_relative_to(work.resolve()):
        raise RuntimeError('Qualification output must be outside component work trees')


def prepare(work):
    lock_bytes = (ROOT / "component-lock.json").read_bytes()
    lock = json.loads(lock_bytes)
    pins = {}
    for name in COMPONENTS:
        spec = lock["components"][name]
        sha = spec.get("sha") or spec["accepted_sha"]
        dest = work / name
        if not dest.exists():
            subprocess.run(["git", "clone", "--quiet", "--no-checkout", "https://github.com/" + spec["repository"] + ".git", str(dest)], check=True, timeout=180)
            subprocess.run(["git", "checkout", "--quiet", "--detach", sha], cwd=dest, check=True, timeout=60)
        validate_checkout(dest, sha)
        pins[name] = sha
    env = qualification_environment()
    env.update(PYTHONPATH=os.pathsep.join([str(ROOT), str(work / "control_plane/src"), str(work / "moltbot_safe"), str(work / "gax_imx_transport")]),
               PYTHONDONTWRITEBYTECODE="1", MOLTBOT_SAFE_CONTROL_PLANE_ROOT=str(work / "control_plane"),
               MOLTBOT_SAFE_ROOT=str(work / "moltbot_safe"), GAX_RUNTIME_COMPATIBILITY_PROFILE="merged-producers-v1")
    return env, pins, hashlib.sha256(lock_bytes).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--profile", required=True, choices=["atomic-authority-effect", "refund-intent"])
    ap.add_argument("--work-dir", type=Path, default=ROOT / ".optional-work")
    ap.add_argument("--results-dir", type=Path, required=True)
    ap.add_argument("--scenario", choices=["allowed", "revoked", "same-intent", "distinct-intent"])
    ap.add_argument("--execute", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args()
    out, work = args.results_dir.resolve(), args.work_dir.resolve()
    separate_output(out, work)
    if args.execute:
        from tools.optional_execution import run_case
        value = run_case(args.profile, args.scenario, out, work)
        (out / "result.json").write_text(json.dumps(value, indent=2) + "\n")
        return 0 if value["qualified"] else 1
    if args.scenario:
        ap.error("scenario selection is internal; each profile runs its complete small batch")
    out.mkdir(parents=True, exist_ok=False)
    work.mkdir(parents=True, exist_ok=True)
    env, pins, digest = prepare(work)
    from tools.worker21_authority_effect_qualification import run
    scenarios = ["allowed", "revoked"]
    if args.profile == "refund-intent":
        scenarios += ["same-intent", "distinct-intent"]
    records = []
    for scenario in scenarios:
        rec = run([sys.executable, str(Path(__file__).resolve()), "--execute", "--profile", args.profile,
                   "--scenario", scenario, "--work-dir", str(work), "--results-dir", str(out / scenario)], env=env, timeout=90)
        (out / (scenario + ".log")).write_text(rec["output"])
        records.append({"scenario": scenario, "returncode": rec["returncode"]})
    summary = {"schema_version": "1.0.0", "profile": args.profile, "tested_revisions": pins,
               "component_lock_sha256": digest, "results": records,
               "qualified": all(r["returncode"] == 0 for r in records),
               "scope": "synthetic same-host SQLite only", "consumer_chain_qualified": False,
               "default_profile_changed": False, "production_ready": False}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if summary["qualified"] else 1


if __name__ == "__main__":
    # Permit direct script invocation without requiring an editable hub install.
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
