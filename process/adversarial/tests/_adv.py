"""Shared helpers for the batch-1 adversarial tests (synthetic fixtures, no network effects).

SPDX-License-Identifier: Apache-2.0

Composed flow: the qualification repo's existing operation-identity harness (suites/operation-identity/_oi_flow.Flow), which
builds the real control plane BoundedAuthorizationWorkflow from the component's own synthetic fixtures and the runtime
PinnedControlPlaneExecutor. Nothing here carries destination or authority code of its own. Every destination read is an
independent read-only SQLite connection, never the executor's return value.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sqlite3

import pytest


def flow(work, mp, **kw):
    from _oi_flow import Flow
    kw.setdefault("identity", False)
    kw.setdefault("wide", False)
    return Flow(pathlib.Path(work), mp, **kw)


def ro(path) -> sqlite3.Connection:
    uri = pathlib.Path(path).resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def tables(path) -> list[str]:
    conn = ro(path)
    try:
        return [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    finally:
        conn.close()


def rows(path, table: str, order: str = "rowid") -> list[dict]:
    if not pathlib.Path(path).exists() or table not in tables(path):
        return []
    conn = ro(path)
    try:
        return [dict(r) for r in conn.execute(f'SELECT * FROM "{table}" ORDER BY {order}')]  # noqa: S608 - fixed names
    finally:
        conn.close()


def effect_ids(path) -> list[str]:
    return sorted(r["effect_id"] for r in rows(path, "effects"))


def table_digest(path, names=None) -> dict[str, str]:
    """sha256 of every row of every (or the named) table, read independently."""
    out = {}
    for name in names or tables(path):
        out[name] = hashlib.sha256(json.dumps(rows(path, name), sort_keys=True, default=str).encode()).hexdigest()
    return out


def snapshot(envelope):
    from engine.safe_executor import snapshot_envelope
    return snapshot_envelope(envelope)


def atomic(fl, work, *, identity_key=False, clock=None):
    """Route B: runtime AtomicLocalControlPlaneExecutor + atomic authority/effect destination on the flow's workflow."""
    from engine.atomic_local_control_plane_executor import AtomicLocalControlPlaneExecutor
    if identity_key:
        from engine.operation_identity_atomic_destination import OperationIdentityAtomicAuthorityEffectDestination as Dest
    else:
        from engine.local_authority_effect import AtomicAuthorityEffectDestination as Dest
    dest = Dest(pathlib.Path(work) / "atomic", clock=clock or (lambda: fl.NOW))
    ex = AtomicLocalControlPlaneExecutor(workflow=fl.f, destination=dest, policy=fl.policy,
                                         **({"operation_identity": True} if identity_key else {}))
    return dest, ex


def bundle(fl, out) -> pathlib.Path:
    """The flow's control-plane run record, proposal export and manifest, as the verifier and Replay read them."""
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "run-record.json").write_text(fl.f.records.path.read_text(encoding="utf-8"), encoding="utf-8")
    (out / "proposal.json").write_text(json.dumps(fl.p.model_dump(mode="json", exclude_none=False)), encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps(fl.f.manifest), encoding="utf-8")
    return out


def ledger_projection(db_path) -> dict:
    """Field-for-field projection of the runtime SQLite effects table into the verifier's ledger shape.

    The verifier documents the control plane's local destination state as its ledger; this projection of the runtime route's
    rows is the same one the orchestrator overlay uses, and it is labelled as a projection wherever it is used.
    """
    effects, counts = {}, {}
    for row in rows(db_path, "effects"):
        effects[row["effect_id"]] = {"effect_id": row["effect_id"], "grant_id": row["grant_id"], "target": row["target"],
                                     "amount": row["amount"], "unit": row["unit"], "payload": json.loads(row["payload_json"]),
                                     "state": row["state"]}
        counts[row["grant_id"]] = counts.get(row["grant_id"], 0) + 1
    return {"effects": effects, "grant_effect_counts": counts}


GENERATED_AT = "2026-10-18T12:00:00+00:00"


def verify(verifier_dir, b, *, ledger: dict | None = None, record: pathlib.Path | None = None, name="report"):
    """Run cognous-verify (the verifier checkout, stdlib only) as an isolated subprocess. Returns (exit code, report)."""
    import subprocess
    import sys
    from conftest import COMPONENTS
    b = pathlib.Path(b)
    argv = [str(record or b / "run-record.json"), "--proposal", str(b / "proposal.json"), "--manifest", str(b / "manifest.json"),
            "--out", str(b / f"{name}.json"), "--generated-at", GENERATED_AT,
            "--controller-revision", COMPONENTS["control_plane"]["revision"],
            "--source-revision", COMPONENTS["verifier"]["revision"]]
    if ledger is not None:
        (b / f"{name}-ledger.json").write_text(json.dumps(ledger), encoding="utf-8")
        argv += ["--ledger", str(b / f"{name}-ledger.json")]
    code = "import sys; sys.path.insert(0, sys.argv[1]); from cognous_verify.cli import main; sys.exit(main(sys.argv[2:]))"
    proc = subprocess.run([sys.executable, "-I", "-c", code, str(pathlib.Path(verifier_dir) / "src"), *argv],
                          capture_output=True, text=True, timeout=300, env={"PATH": "", "HOME": ""})
    out = b / f"{name}.json"
    return proc.returncode, (json.loads(out.read_text(encoding="utf-8")) if out.exists() else {"_stderr": proc.stderr[-2000:]})


def verdicts(report: dict) -> dict[str, str]:
    return {c["check_id"]: c["verdict"] for c in report.get("checks", [])}


def refuted(report: dict) -> set[str]:
    return {k for k, v in verdicts(report).items() if v == "refuted"}


def downstream(fl, out, paths) -> dict[str, pathlib.Path]:
    """Replay import, Evidence Pack build and ODES export of the flow's record (the overlay's replay-runner path, in process).

    Replay selects its profile from the revision label it is given; the label is a caller claim. The newest label Replay lists
    (CONTROL_PLANE_P4_REVISION) is used, as the orchestrator overlay does for a later control plane.
    """
    import sys
    for key in ("replay", "evidence_pack", "odes"):
        src = str(pathlib.Path(paths[key]) / "src")
        if src not in sys.path:
            sys.path.insert(0, src)
    from agent_governance_evidence_pack import importer as pack
    from agent_replay_bundle import importers as replay
    from odes.exporter import export_cognous_stack_package
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    record = json.loads(fl.f.records.path.read_text(encoding="utf-8"))
    built = replay.import_bounded_workflow(record, proposal=fl.p.model_dump(mode="json", exclude_none=False),
                                           control_plane_revision=replay.CONTROL_PLANE_P4_REVISION)
    bundle_doc = json.loads(json.dumps(built.model_dump(mode="json"), default=str))
    files = {"replay": out / "replay-bundle.json", "pack": out / "evidence-pack.json", "odes": out / "odes-package.json"}
    files["replay"].write_text(json.dumps(bundle_doc, sort_keys=True), encoding="utf-8")
    built_pack = pack.build_evidence_pack_from_artifacts(fl.f.manifest, bundle_doc)
    files["pack"].write_text(json.dumps(json.loads(built_pack.model_dump_json()), sort_keys=True), encoding="utf-8")
    files["odes"].write_text(json.dumps(export_cognous_stack_package(fl.f.manifest, bundle_doc), sort_keys=True), encoding="utf-8")
    return files


def twice(tmp_path, fn):
    """Run ``fn(work, mp)`` from two fresh stores and require equal normalised observations (harness convention D3)."""
    outs = []
    for n in (1, 2):
        mp = pytest.MonkeyPatch()
        try:
            outs.append(fn(pathlib.Path(tmp_path) / f"run{n}", mp))
        finally:
            mp.undo()
    assert outs[0] == outs[1], f"two fresh runs disagree:\n{outs[0]}\n{outs[1]}"
    return outs[0]
