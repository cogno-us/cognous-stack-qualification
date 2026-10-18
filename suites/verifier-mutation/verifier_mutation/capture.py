"""Capture the clean corpus from the real control plane (opt-in development tool; the harness never imports the stack).

Runs the stack to produce the clean traces: the control plane's own test helpers (synthetic proposals, resolver and
destination, a fixed clock, as its lifecycle conformance suite does) and the public ``acp run`` command on the declared examples
and on seeded variants of them. No qualification controller and no ``tools/v1_validation.py`` mode is run, and no component is
modified. The output is a frozen snapshot committed under ``corpus/clean``; capture is not repeatable byte for byte (identifiers
and one reconciliation time come from the stack), so the corpus digest, not this script, identifies the corpus.

    <venv with agent-control-plane and cryptography>/bin/python -m verifier_mutation capture \
        --control-plane <checkout of cogno-us/cognous-control-plane> --out corpus/clean
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import contextlib
import copy
import json
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .jsonio import PROFILE, digest, dump_file_bytes
from .trace import FILENAMES

CAPTURE_SEED = 20261018
ACP_NOW = "2026-10-05T19:00:00Z"


def _write(path: Path, doc: Any) -> None:
    path.write_bytes(dump_file_bytes(doc))


def capture(control_plane: Path, out: Path) -> dict[str, Any]:
    cp = control_plane.resolve()
    sys.path.insert(0, str(cp))
    sys.path.insert(0, str(cp / "src"))
    import agent_control_plane.bounded as bounded  # noqa: PLC0415
    from tests.test_bounded_authorization import NOW, manifest, proposal, resolver_for, workflow  # noqa: PLC0415
    from tests.test_runtime_authority import setup_flow  # noqa: PLC0415

    bounded._now = lambda: NOW  # fixed synthetic clock, as the control plane's own suite does
    revision = subprocess.run(["git", "-C", str(cp), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    registry = cp / "schemas" / "runtime_authority_reasons_0_1.json"
    work = Path(tempfile.mkdtemp(prefix="vm-capture-"))
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    entries: list[dict[str, Any]] = []

    def keep(name: str, description: str, producer: str, files: dict[str, bytes | Path | Any]) -> None:
        d = out / name
        d.mkdir()
        recorded: dict[str, str] = {}
        for role, content in files.items():
            data = content.read_bytes() if isinstance(content, Path) else content if isinstance(content, bytes) else dump_file_bytes(content)
            (d / FILENAMES[role]).write_bytes(data)
            recorded[role] = digest(data)
        _write(d / "scenario.json", {"scenario": name, "description": description, "producer": producer, "control_plane_revision": revision, "synthetic": True})
        entries.append({"trace_id": name, "scenario": name, "description": description, "files": recorded})

    def keep_flow(name: str, description: str, flow: Any, prop: Any) -> None:
        keep(name, description, "agent-control-plane bounded workflow (test helpers, fixed clock)", {
            "run_record": Path(flow.records.path),
            "proposal_export": prop.model_dump(mode="json", exclude_none=False),
            "manifest": manifest(),
            "destination_ledger": flow.destination.snapshot()})

    def reopen(flow: Any, r: Any, cfg: Any) -> Any:
        return bounded.BoundedAuthorizationWorkflow(
            allow_test_time=True, manifest=manifest(), resolver=r, destination=bounded.LocalRefundDestination(flow.destination.path),
            records=bounded.BoundedRecordStore(flow.records.path, "run-1"),
            observation_policy=bounded.ObservationPolicy(max_age_seconds=300, clock_tolerance_seconds=5), runtime_authority_profile=cfg)

    p = proposal(); f = workflow(work / "default-applied", p); d = f.decide(p, now=NOW); f.execute(p, d, adapter_id=p.adapter_id, now=NOW)
    keep_flow("default-applied", "default path, authorized then acknowledged and applied", f, p)

    p = proposal(); r = resolver_for(p); r.statuses = {}; f = workflow(work / "default-held", p, resolver=r); f.decide(p, now=NOW)
    keep_flow("default-held", "default path, decision held (grant unreadable), nothing dispatched", f, p)

    p, r, f, cfg = setup_flow(work / "journal-applied"); d = f.decide(p, now=NOW); f.execute(p, d, adapter_id=p.adapter_id, now=NOW)
    keep_flow("journal-applied", "journal mode, authorized then applied (two checks)", f, p)

    p, r, f, cfg = setup_flow(work / "journal-partial"); d = f.decide(p, now=NOW); f.execute(p, d, adapter_id=p.adapter_id, now=NOW, partial=True)
    keep_flow("journal-partial", "journal mode, partial dispatch and partial observation", f, p)

    p, r, f, cfg = setup_flow(work / "journal-lost-ack"); d = f.decide(p, now=NOW); f.execute(p, d, adapter_id=p.adapter_id, now=NOW, lose_ack=True)
    keep_flow("journal-lost-ack", "journal mode, acknowledgement lost, attempt unknown", f, p)

    p, r, f, cfg = setup_flow(work / "journal-lost-ack-closeout"); d = f.decide(p, now=NOW); f.execute(p, d, adapter_id=p.adapter_id, now=NOW, lose_ack=True)
    reopen(f, r, cfg).reconcile(d.effect_id, now=NOW)
    keep_flow("journal-lost-ack-closeout", "lost acknowledgement, then reconcile appends a closeout", f, p)

    p, r, f, cfg = setup_flow(work / "journal-reconciled-existing"); d = f.decide(p, now=NOW); f.execute(p, d, adapter_id=p.adapter_id, now=NOW, lose_ack=True)
    again = reopen(f, r, cfg); again.execute(p, d, adapter_id=p.adapter_id, now=NOW)
    keep_flow("journal-reconciled-existing", "retry after a lost acknowledgement finds the effect (reconciled_existing)", again, p)

    p, r, f, cfg = setup_flow(work / "journal-failed"); d = f.decide(p, now=NOW)

    def reject(**kwargs: Any) -> None:
        raise bounded.DefinitiveDestinationRejection("synthetic_definitive_rejection")

    f.destination.apply = reject  # type: ignore[method-assign]
    f.execute(p, d, adapter_id=p.adapter_id, now=NOW)
    keep_flow("journal-failed", "journal mode, destination definitively rejected the effect", f, p)

    p, r, f, cfg = setup_flow(work / "journal-effect-time-refusal"); d = f.decide(p, now=NOW); r.grant_status = lambda ref: None
    with contextlib.suppress(PermissionError):
        f.execute(p, d, adapter_id=p.adapter_id, now=NOW)
    keep_flow("journal-effect-time-refusal", "journal mode, grant unreadable at effect time: refusal", f, p)

    p, r, f, cfg = setup_flow(work / "journal-held"); r.grant_status = lambda ref: None; f.decide(p, now=NOW)
    keep_flow("journal-held", "journal mode, decision held (status unreadable)", f, p)

    # `acp run` (the public command) on the declared examples and on seeded variants of the authorized example.
    acp = Path(sys.executable).parent / "acp"
    examples = cp / "examples" / "acp_run"
    rng = random.Random(CAPTURE_SEED)
    base_state = json.loads((examples / "authorized" / "resolver-state.json").read_text(encoding="utf-8"))
    base_proposal = json.loads((examples / "authorized" / "proposal.json").read_text(encoding="utf-8"))
    base_context = (examples / "authorized" / "authority-context.json")
    cases: list[tuple[str, str, Path, Path, Path]] = []
    for case in ("authorized", "held"):
        cases.append((f"acp-run-{case}", f"`acp run` on the control plane example `{case}`",
                      examples / case / "proposal.json", examples / case / "authority-context.json", examples / case / "resolver-state.json"))
    variants = [("applied", "authorized variant"), ("applied", "authorized variant"), ("applied", "authorized variant"), ("applied", "authorized variant"),
                ("revoked", "grant revoked in the resolver state (held)"), ("approval-mismatch", "approval bound to another proposal (held)")]
    for i, (kind, label) in enumerate(variants, start=1):
        prop = copy.deepcopy(base_proposal)
        # the grant's scope fixes the target and customer; amount, reason and identifiers vary
        prop["payload"] = {"customer_id": base_proposal["payload"]["customer_id"], "refund_reason": rng.choice(("duplicate", "late", "damaged"))}
        prop["amount"] = float(rng.choice((10, 25, 40, 75)))
        prop["correlation_id"] = f"case-v{i}"
        prop["run_id"] = f"run-v{i}"
        prop["payload_commitment"] = bounded.commitment(prop["payload"])
        model = bounded.RuntimeProposal.model_validate(prop)
        pc = bounded.commitment(model.model_dump(mode="json", exclude_none=False))
        state = copy.deepcopy(base_state)
        for approval in state["approvals"].values():
            approval["proposal_commitment"] = pc if kind != "approval-mismatch" else bounded.commitment({"other": i})
        if kind == "revoked":
            for status in state["statuses"].values():
                status["status"] = "revoked"
        vdir = work / f"variant-{i}"
        vdir.mkdir()
        _write(vdir / "proposal.json", prop)
        _write(vdir / "resolver-state.json", state)
        cases.append((f"acp-run-v{i}-{kind}", f"`acp run` on a seeded variant: {label}", vdir / "proposal.json", base_context, vdir / "resolver-state.json"))
    for name, description, proposal_path, context_path, state_path in cases:
        run_dir = work / name
        run_dir.mkdir()
        subprocess.run([str(acp), "run", "--manifest", str(examples / "manifest.json"), "--proposal", str(proposal_path), "--authority-context", str(context_path),
                        "--resolver-state", str(state_path), "--store-dir", str(run_dir / "store"), "--out-dir", str(run_dir / "out"), "--now", ACP_NOW,
                        "--format", "json"], capture_output=True, check=False)
        model = bounded.RuntimeProposal.model_validate(json.loads(proposal_path.read_text(encoding="utf-8")))
        keep(name, description, "acp run (public command)", {
            "run_record": run_dir / "out" / "bounded-run-record.json",
            "proposal_export": model.model_dump(mode="json", exclude_none=False),
            "manifest": examples / "manifest.json",
            "destination_ledger": run_dir / "store" / "destination.json"})

    entries.sort(key=lambda e: e["trace_id"])
    manifest_doc = {
        "kind": "verifier-mutation-clean-corpus", "canonicalization_profile": PROFILE, "capture_seed": CAPTURE_SEED,
        "control_plane_repository": "cogno-us/cognous-control-plane", "control_plane_revision": revision,
        "reason_registry_digest": digest(registry.read_bytes()),
        "contract_versions": {"control-plane-journal": "0.1.0-draft", "execution-attempt-lifecycle": "0.1.0-draft"},
        "synthetic": True, "traces": entries,
    }
    (out / "manifest.json").write_bytes(dump_file_bytes(manifest_doc))
    shutil.rmtree(work)
    return manifest_doc


UNOBSERVED = "journal-lost-ack-unobserved"


def capture_unobserved(control_plane: Path, out: Path) -> dict[str, Any]:
    """Add one trace to an existing clean corpus (post-run-1 addition, V3b): a lost acknowledgement whose post-dispatch observation failed.

    The control plane's own code path is used: the destination commits and times out (``lose_ack``), the attempt is ``unknown``, and the
    follow-up ``observe`` raises, so the record holds the pre-dispatch ``absent`` observation and a ``hold`` reconciliation but no accepted
    applied observation, while the destination ledger holds the row. Nothing in the record corroborates that row, which is what a category R6
    expected-accept mutant needs. The existing traces are left untouched; the manifest gains one entry.
    """
    cp = control_plane.resolve()
    sys.path.insert(0, str(cp))
    sys.path.insert(0, str(cp / "src"))
    import agent_control_plane.bounded as bounded  # noqa: PLC0415
    from tests.test_bounded_authorization import NOW, manifest  # noqa: PLC0415
    from tests.test_runtime_authority import setup_flow  # noqa: PLC0415

    bounded._now = lambda: NOW
    manifest_path = out / "manifest.json"
    doc = json.loads(manifest_path.read_text(encoding="utf-8"))
    revision = subprocess.run(["git", "-C", str(cp), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    if revision != doc["control_plane_revision"]:
        raise ValueError(f"control plane {revision} is not the corpus's {doc['control_plane_revision']}")
    work = Path(tempfile.mkdtemp(prefix="vm-capture-extra-"))
    p, r, f, cfg = setup_flow(work / UNOBSERVED)
    d = f.decide(p, now=NOW)
    real_observe, calls = f.destination.observe, []

    def observe(effect_id: str) -> Any:
        calls.append(effect_id)
        if len(calls) > 1:  # the first read is the pre-dispatch existence check; every later read fails
            raise ConnectionError("synthetic: destination unreachable after the commit")
        return real_observe(effect_id)

    f.destination.observe = observe  # type: ignore[method-assign]
    f.execute(p, d, adapter_id=p.adapter_id, now=NOW, lose_ack=True)
    dest = out / UNOBSERVED
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir()
    files = {"run_record": Path(f.records.path), "proposal_export": p.model_dump(mode="json", exclude_none=False), "manifest": manifest(),
             "destination_ledger": f.destination.snapshot()}
    recorded: dict[str, str] = {}
    for role, content in files.items():
        data = content.read_bytes() if isinstance(content, Path) else dump_file_bytes(content)
        (dest / FILENAMES[role]).write_bytes(data)
        recorded[role] = digest(data)
    description = "journal mode, acknowledgement lost and the follow-up observation failed: unknown attempt, no accepted applied observation, ledger row present"
    _write(dest / "scenario.json", {"scenario": UNOBSERVED, "description": description, "producer": "agent-control-plane bounded workflow (test helpers, fixed clock)",
                                    "control_plane_revision": revision, "synthetic": True,
                                    "note": "added after run 1 of the mutation harness (V3b); see the suite README"})
    doc["traces"] = sorted([t for t in doc["traces"] if t["trace_id"] != UNOBSERVED] + [{"trace_id": UNOBSERVED, "scenario": UNOBSERVED, "description": description, "files": recorded}],
                           key=lambda e: e["trace_id"])
    manifest_path.write_bytes(dump_file_bytes(doc))
    shutil.rmtree(work)
    return doc
