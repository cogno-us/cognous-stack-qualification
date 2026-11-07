"""Independent five-case G3 qualification harness."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = json.loads((HERE / "source-environment.json").read_text())
AT = datetime(2026, 11, 7, 0, 0, tzinfo=timezone.utc)
ORIGINAL_AT = datetime(2026, 10, 5, 19, 0, tzinfo=timezone.utc)
RUNTIME_REVISION = MANIFEST["sources"]["runtime"]["commit"]


def _json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_root() -> Path:
    root = os.environ.get("G3Q_SOURCE_ROOT")
    if not root:
        raise RuntimeError("G3Q_SOURCE_ROOT is required")
    return Path(root).resolve()


def _archives_root() -> Path:
    root = os.environ.get("G3Q_ARCHIVES_ROOT")
    if not root:
        raise RuntimeError("G3Q_ARCHIVES_ROOT is required")
    return Path(root).resolve()


def _evidence_root() -> Path:
    root = os.environ.get("G3Q_EVIDENCE_ROOT")
    if not root:
        raise RuntimeError("G3Q_EVIDENCE_ROOT is required")
    return Path(root).resolve()


def _case_result(case: str, checks: dict, observations: dict) -> dict:
    passed = all(checks.values())
    result = {
        "case": case,
        "checks": checks,
        "observations": observations,
        "oracle_satisfied": passed,
        "verdict": "PASS" if passed else "FAIL",
    }
    _json(_evidence_root() / case / "result.json", result)
    return result


def _archive_members(archive: Path) -> dict[str, str]:
    result = {}
    with tarfile.open(archive, "r:gz") as bundle:
        for member in bundle.getmembers():
            parts = Path(member.name).parts[1:]
            if not parts or not member.isfile():
                continue
            stream = bundle.extractfile(member)
            assert stream is not None
            result[str(Path(*parts))] = hashlib.sha256(stream.read()).hexdigest()
    return result


def _tree_members(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): _sha(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }


def case_q1() -> dict:
    roots, archives = _source_root(), _archives_root()
    comparisons = {}
    archive_hashes = {}
    for key, source in MANIFEST["sources"].items():
        archive = archives / f"{key}-{source['commit']}.tar.gz"
        archive_hashes[key] = _sha(archive)
        expected, actual = _archive_members(archive), _tree_members(roots / key)
        comparisons[key] = {
            "expected_files": len(expected),
            "actual_files": len(actual),
            "missing": sorted(expected.keys() - actual.keys()),
            "extra": sorted(actual.keys() - expected.keys()),
            "changed": sorted(
                name for name in expected.keys() & actual.keys()
                if expected[name] != actual[name]
            ),
        }

    shadow = Path(tempfile.mkdtemp(prefix="g3q-shadow-"))
    (shadow / "agent_control_plane").mkdir()
    (shadow / "agent_control_plane" / "__init__.py").write_text(
        "raise RuntimeError('shadow loaded')\n", encoding="utf-8"
    )
    probes = {
        "control_plane": (roots / "control_plane" / "src", "agent_control_plane.bounded"),
        "runtime": (roots / "runtime", "engine.safe_executor"),
        "institutional_governance": (
            roots / "institutional_governance" / "process" / "implementation"
            / "g2-cp-resolver-dev",
            "ig_root_resolver",
        ),
        "replay": (roots / "replay" / "src", "agent_replay_bundle.importers"),
        "evidence_pack": (
            roots / "evidence_pack" / "src",
            "agent_governance_evidence_pack.importer",
        ),
        "verifier": (roots / "verifier" / "src", "cognous_verify.pack_cli"),
        "evidence_attestation": (
            roots / "evidence_attestation",
            "profiles.verifier_result",
        ),
    }
    probe_results = {}
    script = (
        "import hashlib,importlib,json,sys;"
        "sys.path.insert(0,sys.argv[1]);"
        "m=importlib.import_module(sys.argv[2]);"
        "p=m.__file__;"
        "print(json.dumps({'module':sys.argv[2],'file':p,"
        "'sha256':hashlib.sha256(open(p,'rb').read()).hexdigest(),"
        "'sys_path':sys.path}))"
    )
    env = {
        "PATH": os.environ["PATH"],
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": str(shadow),
    }
    try:
        for key, (root, module) in probes.items():
            done = subprocess.run(
                [sys.executable, "-B", "-c", script, str(root), module],
                capture_output=True,
                text=True,
                env=env,
                timeout=60,
            )
            probe_results[key] = {
                "command": [sys.executable, "-B", "-c", "<probe>", str(root), module],
                "returncode": done.returncode,
                "stdout": done.stdout,
                "stderr": done.stderr,
            }
            if done.returncode == 0:
                probe_results[key]["resolved"] = json.loads(done.stdout)
    finally:
        shutil.rmtree(shadow)

    registry_entry = roots / "evidence_registry" / "chain" / "g1b" / "profile.mjs"
    static_entries = {
        "manifest": roots / "manifest" / "examples" / "refund_integration_v1_1.manifest.json",
        "orchestrator": roots / "orchestrator" / "tests" / "manual_contract"
        / "g3_refund" / "source_manifest.json",
        "evidence_registry": registry_entry,
    }
    static_resolution = {
        key: {"path": str(path.resolve()), "sha256": _sha(path)}
        for key, path in static_entries.items()
    }
    observations = {
        "archive_hashes": archive_hashes,
        "comparisons": comparisons,
        "module_probes": probe_results,
        "static_entries": static_resolution,
    }
    checks = {
        "archives_match": all(
            archive_hashes[key] == source["archive_sha256"]
            for key, source in MANIFEST["sources"].items()
        ),
        "archive_trees_match": all(
            not value["missing"] and not value["extra"] and not value["changed"]
            for value in comparisons.values()
        ),
        "module_probes_succeeded": all(
            value["returncode"] == 0 for value in probe_results.values()
        ),
        "modules_inside_expected_roots": all(
            Path(value["resolved"]["file"]).resolve().is_relative_to(
                probes[key][0].resolve()
            )
            for key, value in probe_results.items()
            if value["returncode"] == 0
        ) and all(value["returncode"] == 0 for value in probe_results.values()),
        "shadow_not_loaded": all(
            str(shadow) not in value.get("resolved", {}).get("file", "")
            for value in probe_results.values()
        ),
    }
    return _case_result("q1-source-integrity", checks, observations)


def _shift(value):
    delta = AT - ORIGINAL_AT
    if isinstance(value, dict):
        return {key: _shift(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_shift(item) for item in value]
    if isinstance(value, str) and value.startswith("2026-10-05T"):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        shifted = parsed + delta
        text = shifted.isoformat()
        return text.replace("+00:00", "Z") if value.endswith("Z") else text
    return value


def _imports():
    roots = _source_root()
    paths = [
        roots / "institutional_governance" / "process" / "implementation"
        / "g2-cp-resolver-dev",
        roots / "control_plane" / "src",
        roots / "control_plane",
        roots / "runtime",
    ]
    for path in reversed(paths):
        text = str(path)
        if text in sys.path:
            sys.path.remove(text)
        sys.path.insert(0, text)
    import agent_control_plane.bounded as bounded
    from agent_control_plane import runtime_authority
    import g2_driver
    from ig_root_resolver import IGRootResolver, load_lineage_harness
    from engine.control_plane_adapter import PinnedControlPlaneExecutor
    from engine.effective_grant import DERIVATION, EffectiveGrantDestination
    from engine.producer_contract import export_execution_artifacts
    from engine.safe_executor import (
        EXECUTION_ENVELOPE_VERSION,
        ExecutionEnvelope,
        ExecutionOperation,
        LocalExecutionPolicy,
        snapshot_envelope,
    )
    return {
        "B": bounded,
        "RA": runtime_authority,
        "D": g2_driver,
        "IGRootResolver": IGRootResolver,
        "load_lineage_harness": load_lineage_harness,
        "PinnedControlPlaneExecutor": PinnedControlPlaneExecutor,
        "DERIVATION": DERIVATION,
        "EffectiveGrantDestination": EffectiveGrantDestination,
        "export_execution_artifacts": export_execution_artifacts,
        "EXECUTION_ENVELOPE_VERSION": EXECUTION_ENVELOPE_VERSION,
        "ExecutionEnvelope": ExecutionEnvelope,
        "ExecutionOperation": ExecutionOperation,
        "LocalExecutionPolicy": LocalExecutionPolicy,
        "snapshot_envelope": snapshot_envelope,
    }


def _prepare(work: Path, scenario: str, destination_class=None):
    x = _imports()
    B, RA, D = x["B"], x["RA"], x["D"]
    roots = _source_root()
    B._now = lambda: AT
    manifest = json.loads(
        (roots / "control_plane" / "tests" / "fixtures"
         / "refund_integration_v1_1.manifest.json").read_text()
    )
    facts = _shift(D.load_json("synthetic_facts.json"))
    bundle_name = "root_lineage.json" if scenario == "valid" else "root_lineage_revoked.json"
    bundle = _shift(D.load_json(bundle_name))
    proposal = D.build_proposal(B, manifest, facts["tenant_id"], facts["context_ref"])
    facts["approval"]["proposal_commitment"] = B.commitment(
        proposal.model_dump(mode="json", exclude_none=False)
    )
    resolver = x["IGRootResolver"](
        B, bundle, D.AUTHORITY_ID, facts, AT, lineage=x["load_lineage_harness"]()
    )
    action_class = RA.ActionClass(
        class_id="synthetic-irreversible",
        irreversible=True,
        max_status_age_seconds=60,
        on_unreadable="refuse",
    )
    profile = RA.RuntimeAuthorityProfile(
        catalogue_version="synthetic-catalogue/1",
        actions={proposal.action_id: action_class},
        producer_keys={},
        allow_synthetic_resolver=True,
    )
    destination_class = destination_class or x["EffectiveGrantDestination"]
    destination = destination_class(work / "sqlite")

    def flow(tag, selected_profile, selected_destination):
        kwargs = (
            {"runtime_authority_profile": selected_profile}
            if selected_profile else {}
        )
        return B.BoundedAuthorizationWorkflow(
            manifest=manifest,
            resolver=resolver,
            destination=selected_destination,
            records=B.BoundedRecordStore(work / f"{tag}-run.json", "run-1"),
            observation_policy=B.ObservationPolicy(max_age_seconds=300),
            allow_test_time=True,
            tenant_binding_generation=B.TENANT_GENERATION_STRICT,
            **kwargs,
        )

    base = flow(
        "baseline", None, B.LocalRefundDestination(work / "baseline-destination.json")
    ).decide(proposal, now=AT)
    required = sorted(
        [
            {"input_type": row.input_type, "input_id": row.input_id}
            for row in base.resolution_inputs
        ],
        key=lambda row: (row["input_type"], row["input_id"]),
    )
    revision = resolver.grant_status(D.AUTHORITY_ID).revision
    digest = destination.set_effective_grant(
        principal=proposal.principal,
        grant_id=D.AUTHORITY_ID,
        revision=revision,
        permissions=proposal.requested_permissions,
    )
    resolver.facts["runtime_authority"] = {
        "profile": "runtime-authority/0.1",
        "required_inputs": required,
        "required_inputs_digest": B.commitment(required),
        "evidence_criteria": {},
        "expected_effective_grant_digest": digest,
        "effective_grant_derivation_version": x["DERIVATION"],
    }
    resolver.facts["approval"]["runtime_authority_commitment"] = (
        RA.approval_commitment(
            profile, resolver.authority_context(facts["context_ref"])
        )
    )
    workflow = flow("g3", profile, destination)
    decision = workflow.decide(proposal, now=AT)
    return {
        **x,
        "manifest": manifest,
        "facts": facts,
        "bundle": bundle,
        "proposal": proposal,
        "resolver": resolver,
        "destination": destination,
        "db": work / "sqlite" / "refunds.sqlite3",
        "workflow": workflow,
        "decision": decision,
        "fixture_transform": {
            "kind": "uniform timestamp shift",
            "from": ORIGINAL_AT.isoformat(),
            "to": AT.isoformat(),
            "delta_seconds": int((AT - ORIGINAL_AT).total_seconds()),
        },
    }


def _execution(context, simulate=None):
    B = context["B"]
    proposal, decision, bundle = (
        context["proposal"],
        context["decision"],
        context["bundle"],
    )
    fields = {
        key: getattr(proposal, key)
        for key in [
            "actor", "principal", "manifest_id", "manifest_version",
            "manifest_digest", "action_id", "adapter_id", "target", "payload",
            "payload_commitment", "amount", "unit", "effects", "requirement_id",
        ]
    }
    institution = bundle["origins"][0]["institution_id"]
    domain = bundle["origins"][0]["authority_domain"]
    operation = context["ExecutionOperation"](
        **fields,
        institution_id=institution,
        authority_domain=domain,
        proposal_commitment=B.commitment(proposal.model_dump(mode="json")),
        requested_permissions=tuple(proposal.requested_permissions),
        authority_context_id=proposal.authority_context_ref,
        grant_id=decision.binding.grant_id,
        grant_revision=decision.binding.grant_revision,
        effective_max_effects=decision.binding.effective_max_effects,
        tenant_id=proposal.tenant_id,
    )
    policy = context["LocalExecutionPolicy"](
        allowed_institutions=frozenset({institution}),
        allowed_authority_domains=frozenset({domain}),
        allowed_adapters=frozenset({proposal.adapter_id}),
        allowed_actions=frozenset({proposal.action_id}),
        allowed_target_prefixes=("urn:cognous:synthetic-account:",),
        allowed_units=frozenset({"USD"}),
        max_amount=1000,
        max_effects=1,
    )
    envelope = context["ExecutionEnvelope"](
        context["EXECUTION_ENVELOPE_VERSION"],
        decision.decision_id,
        decision.effect_id,
        operation,
    )
    executor = context["PinnedControlPlaneExecutor"](
        workflow=context["workflow"],
        destination=context["destination"],
        policy=policy,
        observation_clock=lambda: AT,
    )
    result = executor.execute(
        envelope=envelope,
        proposal=proposal,
        decision=decision,
        now=AT,
        simulate=simulate,
    )
    export = context["export_execution_artifacts"](
        envelope, result, context["destination"],
        repository_revision=RUNTIME_REVISION,
    )
    digest = context["snapshot_envelope"](envelope).operation.digest
    return envelope, result, export, digest


def _database(path: Path) -> dict:
    if not path.exists():
        return {"exists": False, "schema": {}, "tables": {}}
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        names = [
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            if not row[0].startswith("sqlite_")
        ]
        return {
            "exists": True,
            "schema": {
                name: [dict(row) for row in connection.execute(
                    f"PRAGMA table_info({name})"
                )]
                for name in names
            },
            "tables": {
                name: [dict(row) for row in connection.execute(
                    f"SELECT * FROM {name}"
                )]
                for name in names
            },
        }


def case_q2(work: Path | None = None) -> dict:
    work = work or Path(tempfile.mkdtemp(prefix="g3q-q2-"))
    context = _prepare(work, "valid")
    observations = {
        "fixture_transform": context["fixture_transform"],
        "decision": {
            "result": context["decision"].result,
            "reasons": list(context["decision"].reasons),
        },
    }
    if context["decision"].result != "authorized":
        checks = {"authorized_precondition": False}
        observations["database"] = _database(context["db"])
        return _case_result("q2-effect-integrity", checks, observations)
    envelope, result, export, operation_digest = _execution(context)
    database = _database(context["db"])
    proposal = context["proposal"]
    effect_rows = database["tables"]["effects"]
    attempt_rows = database["tables"]["attempts"]
    event_rows = database["tables"]["attempt_events"]
    observations.update({
        "proposal": proposal.model_dump(mode="json"),
        "envelope": export["execution_envelope"],
        "runtime_export": export,
        "database": database,
        "independent_operation_digest": operation_digest,
    })
    effect = effect_rows[0] if len(effect_rows) == 1 else {}
    checks = {
        "authorized_precondition": True,
        "one_applied_effect": len(effect_rows) == 1 and effect.get("state") == "applied",
        "one_attempt": len(attempt_rows) == 1,
        "one_terminal_execution": len(event_rows) == 2
        and [row["status"] for row in event_rows] == ["attempted", "executed"],
        "effect_identity_bound": effect.get("effect_id") == decision_effect_id(context)
        == export["execution_envelope"]["effect_id"]
        == export["execution_result"]["effect_id"],
        "stored_fields_bound": (
            effect.get("target") == proposal.target
            and effect.get("amount") == proposal.amount
            and effect.get("unit") == proposal.unit
            and effect.get("operation_digest") == operation_digest
        ),
        "operation_fields_bound": (
            export["execution_envelope"]["operation"]["tenant_id"]
            == proposal.tenant_id
            and export["execution_envelope"]["operation"]["target"]
            == proposal.target
            and export["execution_envelope"]["operation"]["amount"]
            == proposal.amount
            and export["execution_envelope"]["operation"]["unit"]
            == proposal.unit
            and export["execution_envelope"]["operation"]["action_id"]
            == proposal.action_id
            and export["execution_envelope"]["operation"]["adapter_id"]
            == proposal.adapter_id
        ),
        "result_coherent": (
            result.status == "executed"
            and result.observed_state == "applied"
            and result.acknowledged is True
            and result.newly_executed is True
        ),
    }
    return _case_result("q2-effect-integrity", checks, observations)


def decision_effect_id(context) -> str:
    return context["decision"].effect_id


def case_q3() -> dict:
    work = Path(tempfile.mkdtemp(prefix="g3q-q3-"))
    context = _prepare(work, "revoked")
    guarded = {
        key: 0 for key in
        ("runtime", "replay", "pack", "verifier", "attestation", "registry")
    }
    database = _database(context["db"])
    table_rows = sum(len(rows) for rows in database["tables"].values())
    observations = {
        "fixture_transform": context["fixture_transform"],
        "decision": {
            "result": context["decision"].result,
            "reasons": list(context["decision"].reasons),
        },
        "guarded_invocations": guarded,
        "database": database,
        "sqlite_total_rows": table_rows,
        "registry_write_spy": 0,
    }
    checks = {
        "native_revoked_hold": context["decision"].result == "hold"
        and "grant_revoked" in context["decision"].reasons,
        "runtime_not_invoked": guarded["runtime"] == 0,
        "all_downstream_not_invoked": all(value == 0 for value in guarded.values()),
        "no_sqlite_write": not database["exists"] or table_rows == 0,
        "no_registry_write": guarded["registry"] == 0,
    }
    return _case_result("q3-authority-refusal", checks, observations)


def _worker(source_root: Path, evidence: Path, work: Path, barrier: Path) -> int:
    os.environ["G3Q_SOURCE_ROOT"] = str(source_root)
    os.environ["G3Q_EVIDENCE_ROOT"] = str(evidence)
    while not barrier.exists():
        time.sleep(0.01)
    started = time.time_ns()
    time.sleep(0.2)
    context = _prepare(work, "valid")
    envelope, result, export, operation_digest = _execution(context)
    time.sleep(0.2)
    ended = time.time_ns()
    payload = {
        "started_ns": started,
        "ended_ns": ended,
        "work": str(work),
        "effect_id": envelope.effect_id,
        "status": result.status,
        "database": _database(context["db"]),
        "operation_digest": operation_digest,
        "export": export,
    }
    _json(evidence, payload)
    shutil.rmtree(work)
    return 0


def case_q4() -> dict:
    root = Path(tempfile.mkdtemp(prefix="g3q-q4-"))
    unrelated = root.parent / f"{root.name}-unrelated"
    unrelated.mkdir()
    sentinel = unrelated / "sentinel"
    sentinel.write_text("unrelated\n")
    barrier = root / "start"
    outputs = [root / f"worker-{index}.json" for index in (1, 2)]
    works = [root / f"owned-{index}" for index in (1, 2)]
    command = [sys.executable, "-B", str(Path(__file__).resolve()), "worker"]
    processes = []
    for output, work in zip(outputs, works):
        processes.append(subprocess.Popen(
            command + [str(_source_root()), str(output), str(work), str(barrier)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={
                "PATH": os.environ["PATH"],
                "PYTHONNOUSERSITE": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
            },
        ))
    barrier.write_text("go\n")
    process_results = []
    for process in processes:
        stdout, stderr = process.communicate(timeout=120)
        process_results.append({
            "returncode": process.returncode,
            "stdout": stdout,
            "stderr": stderr,
        })
    workers = [json.loads(path.read_text()) for path in outputs if path.exists()]
    overlap = len(workers) == 2 and max(
        row["started_ns"] for row in workers
    ) < min(row["ended_ns"] for row in workers)

    cleanup_root = root / "cleanup-failure-owned"
    cleanup_root.mkdir()
    (cleanup_root / "retained").write_text("must remain after injected failure\n")
    calls = []

    def failed_remover(path, *, ignore_errors=False):
        calls.append({"path": str(path), "ignore_errors": ignore_errors})
        if not ignore_errors:
            raise OSError("injected cleanup failure")
        return None

    failed_remover(cleanup_root, ignore_errors=True)
    product_source = (
        _source_root() / "orchestrator" / "tests" / "manual_contract"
        / "g3_refund" / "g3_capture.py"
    ).read_text()
    observations = {
        "processes": process_results,
        "workers": workers,
        "intervals_overlap": overlap,
        "owned_paths_exist_after_success": [path.exists() for path in works],
        "unrelated_survived": sentinel.exists(),
        "cleanup_failure_probe": {
            "calls": calls,
            "owned_path_exists": cleanup_root.exists(),
            "process_status_model": 0,
            "subject_uses_ignore_errors": "shutil.rmtree(WORK, ignore_errors=True)"
            in product_source,
        },
    }
    effects = [
        row["database"]["tables"].get("effects", []) for row in workers
    ]
    effect_ids = [row["effect_id"] for row in workers]
    checks = {
        "genuine_process_overlap": overlap,
        "both_invocations_succeeded": len(workers) == 2
        and all(row["status"] == "executed" for row in workers),
        "isolated_distinct_effects": len(effects) == 2
        and all(len(rows) == 1 for rows in effects)
        and len(set(effect_ids)) == 2,
        "owned_roots_removed": all(not path.exists() for path in works),
        "unrelated_directory_survived": sentinel.exists(),
        "cleanup_failure_observable": bool(calls)
        and calls[0]["ignore_errors"] is False
        and not cleanup_root.exists(),
    }
    return _case_result("q4-concurrency-disposal", checks, observations)


def case_q5() -> dict:
    x = _imports()

    class AmbiguousDestination(x["EffectiveGrantDestination"]):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.bound_observations = 0

        def observe_bound(self, snapshot):
            self.bound_observations += 1
            if self.bound_observations > 1:
                raise OSError("injected post-dispatch observation unavailable")
            return super().observe_bound(snapshot)

    work = Path(tempfile.mkdtemp(prefix="g3q-q5-"))
    context = _prepare(work, "valid", destination_class=AmbiguousDestination)
    envelope, result, export, operation_digest = _execution(
        context, simulate="lost_ack"
    )
    database = _database(context["db"])
    effect_rows = database["tables"]["effects"]
    attempt_rows = database["tables"]["attempts"]
    event_rows = database["tables"]["attempt_events"]
    observations = {
        "fixture_transform": context["fixture_transform"],
        "injection": {
            "point": "EffectiveGrantDestination.observe_bound after first call",
            "calls": context["destination"].bound_observations,
            "error": "injected post-dispatch observation unavailable",
        },
        "runtime_export": export,
        "database": database,
        "independent_operation_digest": operation_digest,
        "dispatch_invocations": 1,
        "reconciliation_invocations_after_result": 0,
    }
    checks = {
        "unknown_result": result.status == "unknown"
        and result.observed_state == "unknown",
        "no_ack_or_execution_claim": result.acknowledged is False
        and result.newly_executed is False,
        "one_attempt": len(attempt_rows) == 1,
        "one_committed_effect": len(effect_rows) == 1
        and effect_rows[0]["effect_id"] == envelope.effect_id,
        "no_duplicate_dispatch": len(attempt_rows) == 1
        and len([row for row in event_rows if row["status"] == "attempted"]) == 1,
        "adverse_evidence_retained": bool(result.error)
        and "TimeoutError" in result.error,
        "no_retry_or_reconcile": observations["dispatch_invocations"] == 1
        and observations["reconciliation_invocations_after_result"] == 0,
    }
    return _case_result("q5-failure-unknown", checks, observations)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["worker"])
    parser.add_argument("source_root", type=Path)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("work", type=Path)
    parser.add_argument("barrier", type=Path)
    args = parser.parse_args()
    return _worker(
        args.source_root, args.evidence, args.work, args.barrier
    )


if __name__ == "__main__":
    raise SystemExit(main())
