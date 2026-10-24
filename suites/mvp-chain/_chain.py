"""Scenario drivers for the mvp-chain suite. They record raw observations; they never compute a verdict.

SPDX-License-Identifier: Apache-2.0

Real path exercised (synthetic, Linux single-host, no network/payment/subprocess effect except the pinned Verifier CLI run):
  Control Plane BoundedAuthorizationWorkflow.decide (operation identity profile on, operation admitted at decide)
  -> AtomicLocalControlPlaneExecutor.provision_claim  (= agent_control_plane.local_authority_effect.provision_local_execution_claim)
  -> AtomicLocalControlPlaneExecutor.execute(operation_identity=True) on OperationIdentityAtomicAuthorityEffectDestination (SQLite)
  -> engine.producer_contract.export_execution_artifacts
  -> Replay import_bounded_workflow -> Evidence Pack import_manifest_reconstruction + validate_evidence_pack
  and, over the raw CP run record with proposal and manifest, the pinned Verifier CLI (exit code and report retained).
Fixtures are the Control Plane component's own tests package (as suites/operation-identity and suites/runtime-authority do), with
the proposal amount set to 10.0 so the action is the $10 synthetic refund. The destination ledger is the atomic destination's
`effects` table; no account-balance adapter is attached (limitation recorded in the README).
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import pathlib
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import traceback

import pytest

import _state

SCENARIOS = {}
NOW_ISO = "2026-10-05T19:00:00+00:00"


def scenario(name):
    def deco(fn):
        SCENARIOS[name] = fn
        return fn
    return deco


def run_scenario(name):
    """Run a scenario once per session; record its observation. A harness exception is recorded as BLOCKED with the traceback."""
    if name in _state.OBS and name != "env":
        return _state.OBS[name]
    work = pathlib.Path(tempfile.mkdtemp(prefix=f"mvp-{name}-"))
    try:
        obs = SCENARIOS[name](work)
        obs.setdefault("status", "ran")
    except Exception as exc:  # noqa: BLE001
        obs = {"status": "blocked", "blocked_reason": f"harness error ({type(exc).__name__}): {exc}", "traceback": traceback.format_exc()}
    obs["work_dir_removed"] = True
    _state.OBS[name] = obs
    shutil.rmtree(work, ignore_errors=True)
    return obs


# ---------------------------------------------------------------------------------------------------------------- helpers
def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(value) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode())


def attempt(fn, expected=None):
    """Run fn and record the outcome. ``expected`` is the tuple of exception types that are a GENUINE refusal for this call: an exception of any other type is
    not refusal evidence (a TypeError from a harness or component bug must never turn a negative control into a pass), so it propagates to run_scenario(), which
    records the scenario as BLOCKED (INCOMPLETE verdict). ``expected=None`` (informational and success-path calls only) records any exception."""
    try:
        return {"ok": True, "value": fn()}
    except Exception as exc:  # noqa: BLE001
        if expected is not None and not isinstance(exc, tuple(expected)):
            raise
        return {"ok": False, "error": {"type": type(exc).__name__, "code": getattr(exc, "code", None), "message": str(exc)[:400]}}


# Genuine refusal types of the candidate components: the Control Plane / executor refuse authority with PermissionError; the Replay, Pack and executor export
# refuse malformed or contradicted evidence with ValueError subclasses (ImportContractError, validation errors); the destination store reports outages as sqlite3.Error / OSError.
REFUSALS_AUTHORITY = (PermissionError,)
REFUSALS_VALUE = (ValueError,)
REFUSALS_STORE = (sqlite3.Error, OSError)
NO_EXCEPTION = ()  # the component reports this refusal as a returned denied result; any raised exception is a harness or component error


def err_of(step):
    return None if step["ok"] else step["error"]


class Ctx:
    """One disposable flow: Control Plane workflow + atomic operation-identity destination + route B executor."""

    def __init__(self, work, *, wide=False):
        import tests.test_runtime_authority as tra
        from _oi_flow import Flow
        from engine.atomic_local_control_plane_executor import AtomicLocalControlPlaneExecutor
        from engine.operation_identity_atomic_destination import OperationIdentityAtomicAuthorityEffectDestination as Dest
        self.mp = pytest.MonkeyPatch()
        original = tra.proposal
        self.mp.setattr(tra, "proposal", lambda *a, **k: original(*a, **k).model_copy(update={"amount": 10.0}))
        self.work = pathlib.Path(work)
        self.flow = Flow(self.work, self.mp, identity=True, wide=wide,
                         dest_factory=lambda path, fl: Dest(path, clock=lambda: fl.NOW))
        self.dest = self.flow.dest
        self.executor = AtomicLocalControlPlaneExecutor(workflow=self.flow.f, destination=self.dest, policy=self.flow.policy, operation_identity=True)
        self.Dest = Dest

    def close(self):
        self.mp.undo()

    def provision(self, decision=None):
        return self.executor.provision_claim(proposal=self.flow.p, decision=decision or self.flow.d1, now=self.flow.NOW)

    def execute(self, claim_id, decision=None, **kwargs):
        return self.executor.execute(envelope=self.flow.envelope(decision or self.flow.d1), claim_id=claim_id, **kwargs)

    def effect_ids(self):
        path = pathlib.Path(self.dest.path)
        if not path.exists():
            return None
        conn = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=10)
        try:
            return [r[0] for r in conn.execute("SELECT effect_id FROM effects ORDER BY effect_id")]
        finally:
            conn.close()

    def count(self):
        ids = self.effect_ids()
        return None if ids is None else len(ids)

    def raw_record(self):
        return self.flow.f.records.load().model_dump(mode="json")

    def run_json_bytes(self):
        return (self.work / "cp" / "run.json").read_bytes()

    def proposal_json(self):
        return self.flow.p.model_dump(mode="json")

    def export(self, result, decision=None):
        from engine.producer_contract import export_execution_artifacts
        return export_execution_artifacts(self.flow.envelope(decision or self.flow.d1), result, self.dest,
                                          repository_revision=_state.ENV["heads"]["runtime"])

    def derived_ledger(self):
        """Harness-derived Verifier ledger input from the real SQLite effects table (not a component artifact)."""
        conn = sqlite3.connect(pathlib.Path(self.dest.path).resolve().as_uri() + "?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            rows = [dict(r) for r in conn.execute("SELECT * FROM effects ORDER BY effect_id")]
        finally:
            conn.close()
        effects, counts = {}, {}
        for r in rows:
            effects[r["effect_id"]] = {"effect_id": r["effect_id"], "grant_id": r["grant_id"], "target": r["target"], "amount": r["amount"],
                                       "unit": r["unit"], "payload": json.loads(r["payload_json"]), "state": r["state"]}
            counts[r["grant_id"]] = counts.get(r["grant_id"], 0) + 1
        return {"effects": effects, "grant_effect_counts": counts}


def result_obs(result):
    return {"status": result.status, "observed_state": result.observed_state, "acknowledged": result.acknowledged,
            "attempted": result.attempted, "newly_executed": getattr(result, "newly_executed", None), "error": result.error,
            "has_observation": bool(result.observation)}


def replay_import(raw, proposal, export):
    from agent_replay_bundle.importers import CONTROL_PLANE_P2_REVISION, import_bounded_workflow
    def go():
        bundle = import_bounded_workflow(copy.deepcopy(raw), proposal=copy.deepcopy(proposal), moltbot_export=copy.deepcopy(export),
                                         control_plane_revision=CONTROL_PLANE_P2_REVISION)
        return bundle
    step = attempt(go, expected=REFUSALS_VALUE)
    out = {"ok": step["ok"], "error": err_of(step)}
    if step["ok"]:
        bundle = step["value"]
        out["all_reports_complete"] = all(x.complete for x in bundle.import_reports)
        out["n_reports"] = len(bundle.import_reports)
        out["n_records"] = len(bundle.records)
        out["bundle_sha256"] = sha256_json(bundle.model_dump(mode="json"))
        out["_bundle"] = bundle
    return out


def pack_import(manifest, bundle):
    from agent_governance_evidence_pack import validate_evidence_pack
    from agent_governance_evidence_pack.importer import import_manifest_reconstruction
    def go():
        pack = import_manifest_reconstruction(manifest, bundle.model_dump(mode="json"))
        return pack, validate_evidence_pack(pack).valid
    step = attempt(go, expected=REFUSALS_VALUE)
    out = {"ok": step["ok"], "error": err_of(step), "valid": None}
    if step["ok"]:
        pack, valid = step["value"]
        out.update(valid=bool(valid), sha256=sha256_json(pack.model_dump(mode="json")), _pack=pack)
    return out


def strip_private(d):
    if isinstance(d, dict):
        return {k: strip_private(v) for k, v in d.items() if not k.startswith("_")}
    if isinstance(d, list):
        return [strip_private(v) for v in d]
    return d


# ------------------------------------------------------------------------------------------------------------- verifier
VERIFIER_CODE = ("import sys,cognous_verify;sys.stderr.write('MODULE '+cognous_verify.__file__+'\\n');"
                 "from cognous_verify.cli import main;sys.exit(main(sys.argv[1:]))")


def run_verifier(label, outdir, *, record_bytes, proposal, manifest, ledger=None):
    outdir = pathlib.Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    files = {"record": (f"{label}-run-record.json", record_bytes),
             "proposal": (f"{label}-proposal.json", json.dumps(proposal, indent=1, sort_keys=True).encode()),
             "manifest": (f"{label}-manifest.json", json.dumps(manifest, indent=1, sort_keys=True).encode())}
    if ledger is not None:
        files["ledger"] = (f"{label}-ledger.json", json.dumps(ledger, indent=1, sort_keys=True).encode())
    for name, data in files.values():
        (outdir / name).write_bytes(data)
    report = outdir / f"{label}-report.json"
    argv = [sys.executable, "-c", VERIFIER_CODE, files["record"][0], "--proposal", files["proposal"][0], "--manifest", files["manifest"][0]]
    if ledger is not None:
        argv += ["--ledger", files["ledger"][0]]
    argv += ["--out", str(report), "--generated-at", NOW_ISO]
    env = {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": _state.ENV["verifier_src"], "PYTHONDONTWRITEBYTECODE": "1"}
    proc = subprocess.run(argv, cwd=outdir, env=env, capture_output=True, text=True, timeout=120)
    module = next((l[7:].strip() for l in proc.stderr.splitlines() if l.startswith("MODULE ")), None)
    out = {"exit_code": proc.returncode, "crashed": proc.returncode == 4, "module_path": module,
           "module_path_under_pin": bool(module) and pathlib.Path(_state.ENV["verifier_src"]) in pathlib.Path(module).resolve().parents,
           "stdout_tail": proc.stdout[-1500:], "stderr_tail": [l for l in proc.stderr.splitlines() if not l.startswith("MODULE ")][-5:],
           "inputs": {k: sha256_bytes(v[1]) for k, v in files.items()}, "report_sha256": "", "overall": None,
           "refuted_check_ids": [], "could_not_check_check_ids": [], "finding_codes": [], "n_checks": None}
    if report.exists():
        data = report.read_bytes()
        out["report_sha256"] = sha256_bytes(data)
        rep = json.loads(data)
        out["n_checks"] = len(rep["checks"])
        out["summary"] = rep["summary"]
        out["refuted_check_ids"] = [c["check_id"] for c in rep["checks"] if c["verdict"] == "refuted"]
        out["could_not_check_check_ids"] = [c["check_id"] for c in rep["checks"] if c["verdict"] == "could_not_check"]
        out["could_not_check_reasons"] = {c["check_id"]: c.get("could_not_check_reason") for c in rep["checks"] if c["verdict"] == "could_not_check"}
        out["finding_codes"] = sorted({f["code"] for c in rep["checks"] for f in c.get("findings", [])})
        out["findings_by_check"] = {c["check_id"]: sorted({f["code"] for f in c["findings"]}) for c in rep["checks"] if c.get("findings")}
        for line in proc.stdout.splitlines():
            if line.startswith("overall:"):
                out["overall"] = line.split()[1]
        retain(f"verifier/{label}-report.json", data)
    return out


def retain(relative, data):
    path = _state.results_dir() / "artifacts" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else json.dumps(data, indent=1, sort_keys=True, default=str).encode())


def journal_summary(raw):
    events = raw.get("check_events", [])
    completed = [e for e in events if e["phase"] == "completed"]
    return {"events": [{"phase": e["phase"], "stage": e["stage"], "check_id": e["check_id"], "has_decision_id": e.get("decision_id") is not None}
                       for e in events if e["phase"] != "input"],
            "n_events": len(events), "completed_check_ids": [e["check_id"] for e in completed],
            "completed_stages": [e["stage"] for e in completed],
            "distinct_completed_check_ids": len({e["check_id"] for e in completed}),
            "completed_events_labelled_decision": sum(1 for e in completed if e["stage"] == "decision"),
            "resolution_check_stages": [c["stage"] for c in raw.get("resolution_checks", [])]}


# ------------------------------------------------------------------------------------------------------------ scenarios
@scenario("chain")
def chain(work):
    ctx = Ctx(work)
    try:
        flow, dest = ctx.flow, ctx.dest
        d = flow.d1
        binding = d.binding
        extension = binding.runtime_authority or {}
        domain = flow.f._authority_domain(binding)
        op_status = flow.f.records.operation_status(operation_id=extension.get("operation_id"), principal_id=binding.principal, authority_domain=domain,
                                                    issuer=extension.get("operation_issuer"), grant_id=binding.grant_id, grant_revision=binding.grant_revision)
        obs = {"decision": {"result": d.result, "reasons": list(d.reasons), "decision_id": d.decision_id, "effect_id": d.effect_id},
               "proposal": {"amount": flow.p.amount, "unit": flow.p.unit, "action_id": flow.p.action_id, "target": flow.p.target},
               "operation": {"operation_id": extension.get("operation_id"), "status": op_status,
                             "identity_profile_on": getattr(flow.f.runtime_authority_profile, "operation_identity", None) is not None}}
        claim_step = attempt(ctx.provision)
        claim = claim_step["value"] if claim_step["ok"] else None
        obs["claim"] = {"ok": claim_step["ok"], "error": err_of(claim_step), "claim_id": getattr(claim, "claim_id", None),
                        "state_after_provision": dest.claim_state(claim.claim_id) if claim else None}
        result = None
        if claim:
            ex_step = attempt(lambda: ctx.execute(claim.claim_id))
            if ex_step["ok"]:
                result = ex_step["value"]
                obs["execute"] = {**result_obs(result), "ok": True}
            else:
                obs["execute"] = {"ok": False, "error": err_of(ex_step), "status": None, "observed_state": None}
        else:
            obs["execute"] = {"ok": False, "error": "no claim", "status": None, "observed_state": None}
        obs["destination"] = {"effect_ids": ctx.effect_ids(), "effect_count": ctx.count(), "claim_state_after": dest.claim_state(claim.claim_id) if claim else None,
                              "operation_identity_destination": isinstance(dest, ctx.Dest) and ctx.executor.operation_identity is True,
                              "expected_effect_id": d.effect_id}
        raw = ctx.raw_record()
        obs["journal"] = journal_summary(raw)
        retain("chain/cp-run-record.json", ctx.run_json_bytes())
        retain("chain/proposal.json", ctx.proposal_json())
        (_state.results_dir() / "artifacts").mkdir(parents=True, exist_ok=True)
        shutil.copy(dest.path, _state.results_dir() / "artifacts" / "chain-destination.sqlite")
        export_obs = {"ok": False, "error": "no execution result", "sha256": None}
        export = None
        if result is not None:
            step = attempt(lambda: ctx.export(result))
            export_obs = {"ok": step["ok"], "error": err_of(step), "sha256": sha256_json(step["value"]) if step["ok"] else None}
            export = step["value"] if step["ok"] else None
            if export:
                retain("chain/executor-export.json", export)
        obs["export"] = export_obs
        replay = {"ok": False, "error": "no export", "all_reports_complete": False}
        pack = {"ok": False, "valid": False, "error": "no bundle"}
        if export is not None:
            replay = replay_import(raw, ctx.proposal_json(), export)
            bundle = replay.pop("_bundle", None)
            if bundle is not None:
                retain("chain/replay-bundle.json", bundle.model_dump(mode="json"))
                pack = pack_import(flow.f.manifest, bundle)
                pk = pack.pop("_pack", None)
                if pk is not None:
                    retain("chain/evidence-pack.json", pk.model_dump(mode="json"))
        obs["replay"], obs["pack"] = replay, pack
        out = _state.results_dir() / "artifacts" / "verifier"
        obs["verifier"] = {
            "A": run_verifier("A", out, record_bytes=ctx.run_json_bytes(), proposal=ctx.proposal_json(), manifest=flow.f.manifest),
            "B": run_verifier("B", out, record_bytes=ctx.run_json_bytes(), proposal=ctx.proposal_json(), manifest=flow.f.manifest,
                              ledger=ctx.derived_ledger()),
            "note": "A = record + proposal + manifest (the gated run). B = A plus a harness-derived ledger from the SQLite effects table (informational).",
        }
        return obs
    finally:
        ctx.close()


@scenario("nc_revocation")
def nc_revocation(work):
    obs = {}
    # (a) grant revoked in the authority store after claim issuance, before effect
    ctx = Ctx(work / "a")
    try:
        claim = ctx.provision()
        ctx.dest.set_grant_status(ctx.flow.d1.binding.grant_id, status="revoked")
        r = ctx.execute(claim.claim_id)
        obs["grant_revoked"] = {**result_obs(r), "effect_count": ctx.count(), "claim_state_after": ctx.dest.claim_state(claim.claim_id)}
    finally:
        ctx.close()
    # (b) approval withdrawal before effect
    ctx = Ctx(work / "b")
    try:
        claim = ctx.provision()
        approval_ref = ctx.flow.r.contexts[ctx.flow.PROFILE]["grant"]["approval_refs"][0]
        ctx.dest.set_approval_status(approval_ref, status="revoked")
        r = ctx.execute(claim.claim_id)
        obs["approval_withdrawn"] = {**result_obs(r), "approval_ref": approval_ref, "effect_count": ctx.count(), "claim_state_after": ctx.dest.claim_state(claim.claim_id)}
    finally:
        ctx.close()
    # (c) revocation visible to the Control Plane resolver before claim issuance
    ctx = Ctx(work / "c")
    try:
        next(iter(ctx.flow.r.statuses.values())).status = "revoked"
        step = attempt(ctx.provision, REFUSALS_AUTHORITY)
        obs["resolver_revoked"] = {"claim_ok": step["ok"], "error": err_of(step), "effect_count": ctx.count()}
    finally:
        ctx.close()
    # terminality (information for NC1-04/05): revoke, then reactivate, then execute the claim issued before the revocation
    ctx = Ctx(work / "d")
    try:
        claim = ctx.provision()
        approval_ref = ctx.flow.r.contexts[ctx.flow.PROFILE]["grant"]["approval_refs"][0]
        ctx.dest.set_approval_status(approval_ref, status="revoked")
        step = attempt(lambda: ctx.dest.set_approval_status(approval_ref, status="active"), REFUSALS_AUTHORITY)
        r = attempt(lambda: ctx.execute(claim.claim_id), NO_EXCEPTION)
        obs["approval_terminality"] = {"reactivation_accepted": step["ok"], "reactivation_error": err_of(step),
                                       **(result_obs(r["value"]) if r["ok"] else {"status": None, "raised": err_of(r)}), "effect_count": ctx.count()}
    finally:
        ctx.close()
    ctx = Ctx(work / "e")
    try:
        claim = ctx.provision()
        gid = ctx.flow.d1.binding.grant_id
        ctx.dest.set_grant_status(gid, status="revoked")
        step = attempt(lambda: ctx.dest.set_grant_status(gid, status="active"), REFUSALS_AUTHORITY)
        r = attempt(lambda: ctx.execute(claim.claim_id), NO_EXCEPTION)
        obs["grant_terminality"] = {"reactivation_accepted": step["ok"], "reactivation_error": err_of(step),
                                    **(result_obs(r["value"]) if r["ok"] else {"status": None, "raised": err_of(r)}), "effect_count": ctx.count()}
    finally:
        ctx.close()
    return obs


@scenario("nc_ambiguous")
def nc_ambiguous(work):
    obs = {}
    ctx = Ctx(work / "a")
    try:
        claim = ctx.provision()
        # fault injection by the harness (a trusted test driver, not the ingress): lost acknowledgement after a durable commit
        first = ctx.execute(claim.claim_id, simulate="lost_ack")
        obs["first"] = result_obs(first)
        obs["first"]["observation"] = strip_private(copy.deepcopy(first.observation)) if first.observation else None
        obs["destination"] = {"effect_count": ctx.count(), "claim_state_after_first": ctx.dest.claim_state(claim.claim_id)}
        rec = first.observation if isinstance(first.observation, dict) else {}
        obs["recovery"] = {"retry_eligible": rec.get("retry_eligible"), "status": rec.get("status"), "state": rec.get("state"),
                           "reason": rec.get("reason"), "status_or_state": rec.get("status") if rec.get("status") not in (None, "unknown") else rec.get("state")}
        retry = attempt(lambda: ctx.execute(claim.claim_id), NO_EXCEPTION)
        obs["retry"] = {**result_obs(retry["value"]), "raised": False} if retry["ok"] else {"status": None, "raised": True, "error": err_of(retry)}
        obs["destination"]["effect_count"] = ctx.count()
        recon = attempt(lambda: ctx.dest.reconcile_claim(claim.claim_id, __import__("engine.safe_executor", fromlist=["x"]).snapshot_envelope(ctx.flow.envelope(ctx.flow.d1))))
        obs["reconcile"] = {"ok": recon["ok"], "error": err_of(recon), "value": strip_private(recon["value"]) if recon["ok"] else None}
        if recon["ok"] and isinstance(recon["value"], dict):
            v = recon["value"]
            obs["recovery"]["status_or_state"] = v.get("state") or v.get("status") if (v.get("state") or v.get("status")) != "unknown" else obs["recovery"]["status_or_state"]
            obs["recovery"]["reconcile_retry_eligible"] = v.get("retry_eligible")
        obs["destination"]["effect_count_after_reconcile"] = ctx.count()
        exp = attempt(lambda: ctx.export(first))
        obs["export"] = {"ok": exp["ok"], "error": err_of(exp)}
        if exp["ok"]:
            rp = replay_import(ctx.raw_record(), ctx.proposal_json(), exp["value"])
            rp.pop("_bundle", None)
            obs["replay"] = rp
        else:
            obs["replay"] = {"ok": False, "error": "export failed"}
    finally:
        ctx.close()
    # reconciliation route unavailable after the ambiguous commit
    ctx = Ctx(work / "b")
    try:
        claim = ctx.provision()
        def unavailable(*a, **k):
            raise TimeoutError("injected: reconciliation route unavailable")
        ctx.dest.reconcile_claim = unavailable
        r = ctx.execute(claim.claim_id, simulate="lost_ack")
        o = r.observation if isinstance(r.observation, dict) else {}
        obs["reconcile_unavailable"] = {**result_obs(r), "retry_eligible": o.get("retry_eligible"), "reason": o.get("reason"), "effect_count": ctx.count()}
    finally:
        ctx.close()
    return obs


@scenario("nc_duplicate")
def nc_duplicate(work):
    obs = {}
    ctx = Ctx(work / "a")
    try:
        claim = ctx.provision()
        first = ctx.execute(claim.claim_id)
        obs["first"] = result_obs(first)
        again = ctx.execute(claim.claim_id)
        obs["same_claim"] = {**result_obs(again), "effect_count": ctx.count()}
        step = attempt(ctx.provision, REFUSALS_AUTHORITY)
        if step["ok"]:
            second = attempt(lambda: ctx.execute(step["value"].claim_id), NO_EXCEPTION)
            if second["ok"]:
                obs["second_claim"] = {**result_obs(second["value"]), "provisioned": True, "executed": second["value"].status == "executed", "effect_count": ctx.count()}
            else:
                obs["second_claim"] = {"provisioned": True, "executed": False, "raised": err_of(second), "effect_count": ctx.count()}
        else:
            obs["second_claim"] = {"provisioned": False, "executed": False, "provision_error": err_of(step), "effect_count": ctx.count()}
    finally:
        ctx.close()
    # renewal with a new approval, cap 2, same operation id (source: suites/operation-identity/test_atomic_route_operation_identity.py::_renew)
    ctx = Ctx(work / "b", wide=True)
    try:
        flow, dest = ctx.flow, ctx.dest
        flow.OPERATION_ID = "op-order-100/refund-1"
        claim1 = ctx.provision()
        r1 = ctx.execute(claim1.claim_id)
        flow.publish_revision("2")
        c = flow.r.contexts[flow.tba.PROFILE]
        grant = c["grant"]
        old = grant["approval_refs"][0]
        new = old.rsplit("-", 1)[0] + "-2"
        approval = flow.r.approvals[old].model_copy(deep=True)
        approval.approval_ref = new
        flow.r.approvals[new] = approval
        grant["approval_refs"] = [new]
        ra = c["runtime_authority"]
        for item in ra["required_inputs"]:
            if item["input_id"] == old:
                item["input_id"] = new
        ra["required_inputs"] = sorted(ra["required_inputs"], key=lambda x: (x["input_type"], x["input_id"]))
        ra["required_inputs_digest"] = flow.cp.commitment(ra["required_inputs"])
        flow.tra.bind_approval(flow.r, flow.f.runtime_authority_profile or flow.cfg)
        flow.f.record_renewal(flow.OPERATION_ID, to_revision="2", written_by=flow.ISSUER, now=flow.NOW)
        dest.set_grant_status(flow.d1.binding.grant_id, status="active", revision="2")
        d2 = flow.f.decide(flow.p, now=flow.NOW)
        claim2 = ctx.provision(d2)
        r2 = ctx.execute(claim2.claim_id, d2)
        obs["renewal_cap2"] = {"r1": result_obs(r1), "r2": result_obs(r2), "renewed_decision": d2.result, "error": r2.error, "effect_count": ctx.count()}
    finally:
        ctx.close()
    return obs


@scenario("nc_authority_gates")
def nc_authority_gates(work):
    """Three required negative controls on route B (Architect ruling Q2), executor level on the exact candidate tuple: (1) unauthorized execution
    commits no effect; (2) stale or mismatched authority prevents an unauthorized effect; (3) missing, invalid or expired required evidence does not
    permit execution. Every case records raw observations only (status, attempted, error text, an independent read-only effect count, claim state);
    rows NC7-01..03 judge them. A control case that refuses proves nothing if the harness could never commit, so the authorized control case must
    commit exactly one effect through the same Ctx. Evidence rows are changed in the destination store the way the existing NC1 cases change grant
    and approval rows (owner-side, raw SQLite), which is the authority-store writer role, not a client capability.
    """
    from datetime import timedelta
    obs = {}

    def refused(ctx, claim_id, envelope=None):
        step = attempt(lambda: ctx.executor.execute(envelope=envelope or ctx.flow.envelope(ctx.flow.d1), claim_id=claim_id), NO_EXCEPTION)
        base = result_obs(step["value"]) if step["ok"] else {"status": None, "raised": err_of(step)}
        return {**base, "effect_count": ctx.count(), "claim_state_after": ctx.dest.claim_state(claim_id)}

    def evidence_case(name, mutate):
        ctx = Ctx(work / name)
        try:
            claim = ctx.provision()
            conn = sqlite3.connect(ctx.dest.path)
            try:
                mutate(conn)
                conn.commit()
            finally:
                conn.close()
            obs.setdefault("evidence", {})[name] = refused(ctx, claim.claim_id)
        finally:
            ctx.close()

    ctx = Ctx(work / "control")
    try:
        claim = ctx.provision()
        obs["control"] = {**result_obs(ctx.execute(claim.claim_id)), "effect_count": ctx.count()}
    finally:
        ctx.close()

    # (1) unauthorized execution
    ctx = Ctx(work / "forged")
    try:
        obs.setdefault("unauthorized", {})["forged_claim_id"] = refused(ctx, "claim-never-issued")
    finally:
        ctx.close()
    ctx = Ctx(work / "denied")
    try:
        over = ctx.flow.p.model_copy(update={"amount": 100000.0})
        decision = ctx.flow.f.decide(over, now=ctx.flow.NOW)
        step = attempt(lambda: ctx.executor.provision_claim(proposal=over, decision=decision, now=ctx.flow.NOW), REFUSALS_AUTHORITY)
        obs["unauthorized"]["not_authorized_decision"] = {"decision_result": decision.result, "claim_ok": step["ok"], "error": err_of(step), "effect_count": ctx.count()}
    finally:
        ctx.close()

    # (2) stale or mismatched authority
    stale = obs.setdefault("stale_or_mismatched", {})
    ctx = Ctx(work / "expired")
    try:
        now = ctx.flow.NOW
        claim = ctx.executor.provision_claim(proposal=ctx.flow.p, decision=ctx.flow.d1, now=now, expires_at=(now + timedelta(seconds=60)).isoformat())
        ctx.flow.advance_clock(120)
        stale["claim_expired"] = refused(ctx, claim.claim_id)
    finally:
        ctx.close()
    ctx = Ctx(work / "advanced")
    try:
        claim = ctx.provision()
        ctx.dest.set_grant_status(ctx.flow.d1.binding.grant_id, status="active", revision="2")
        stale["authority_advanced_after_claim"] = refused(ctx, claim.claim_id)
    finally:
        ctx.close()
    ctx = Ctx(work / "resolver")
    try:
        ctx.flow.publish_revision("2")
        step = attempt(ctx.provision, REFUSALS_AUTHORITY)
        stale["resolver_revision_changed_before_claim"] = {"claim_ok": step["ok"], "error": err_of(step), "effect_count": ctx.count()}
    finally:
        ctx.close()
    ctx = Ctx(work / "amount")
    try:
        claim = ctx.provision()
        changed = ctx.flow.p.model_copy(update={"amount": 11.0})
        stale["envelope_amount_mismatch"] = refused(ctx, claim.claim_id, ctx.flow.envelope(ctx.flow.d1, changed))
    finally:
        ctx.close()
    ctx = Ctx(work / "binding")
    try:
        claim = ctx.provision()
        d1 = ctx.flow.d1
        other = d1.model_copy(update={"binding": d1.binding.model_copy(update={"grant_revision": "2"})})
        stale["envelope_grant_revision_mismatch"] = refused(ctx, claim.claim_id, ctx.flow.envelope(other))
    finally:
        ctx.close()

    # (3) missing, invalid or expired required evidence
    evidence_case("missing", lambda c: c.execute("DELETE FROM authority_evidence_v1"))
    evidence_case("invalid_state", lambda c: c.execute("UPDATE authority_evidence_v1 SET state='stale'"))
    evidence_case("expired", lambda c: c.execute("UPDATE authority_evidence_v1 SET observed_at='2020-01-01T00:00:00+00:00'"))
    ctx = Ctx(work / "resolver_evidence")
    try:
        ctx.flow.r.evidence.clear()
        step = attempt(ctx.provision, REFUSALS_AUTHORITY)
        obs["evidence"]["missing_at_claim_issuance"] = {"claim_ok": step["ok"], "error": err_of(step), "effect_count": ctx.count()}
    finally:
        ctx.close()
    return obs


@scenario("nc_unmediated")
def nc_unmediated(work):
    """The declared ingress boundary: the real hub ingress (Unix socket) attacked as an unprivileged uid; see _ingress.py.

    Reachability is computed from independent owner-side observations, never from ingress self-report. BLOCKED (never PASS) when the
    environment cannot run the client as a distinct unprivileged uid or the hub checkout is absent.
    """
    import _ingress
    obs = _ingress.run(work / "ingress")
    obs["baseline_direct_surfaces"] = direct_surface_baseline(work / "direct")
    return obs



@scenario("nc_ingress_ambiguity")
def nc_ingress_ambiguity(work):
    """SUPPORTED-INGRESS evidence (ruling 5, proposed): see _ingress_ambiguity.py. Executor-level evidence stays in nc_ambiguous / ruling 4."""
    import _ingress_ambiguity
    return _ingress_ambiguity.run(work / "ingress-ambiguity")


@scenario("nc_ingress_ambiguity_nohook")
def nc_ingress_ambiguity_nohook(work):
    """NEGATIVE CONTROL for NC2-06: the owner-side fault hook is disabled (no after_commit raise)."""
    import _ingress_ambiguity
    return _ingress_ambiguity.run(work / "ingress-ambiguity-nohook", fault_mode="none,bind_fresh")


@scenario("nc_ingress_ambiguity_forced_simulate")
def nc_ingress_ambiguity_forced_simulate(work):
    """NEGATIVE CONTROL for NC2-06: mutated wrapper forces simulate='lost_ack' into the executor call (a caller-controlled simulate)."""
    import _ingress_ambiguity
    return _ingress_ambiguity.run(work / "ingress-ambiguity-forced", fault_mode="after_commit,bind_fresh,forced_simulate")


@scenario("nc_ingress_ambiguity_before_commit")
def nc_ingress_ambiguity_before_commit(work):
    """NEGATIVE CONTROL for NC2-06: the failure is raised BEFORE the commit (no durable effect), so the row's effect-exists predicates must fail."""
    import _ingress_ambiguity
    return _ingress_ambiguity.run(work / "ingress-ambiguity-before", fault_mode="before_commit,bind_fresh")


@scenario("nc_ingress_ambiguity_allow_second_commit")
def nc_ingress_ambiguity_allow_second_commit(work):
    """NEGATIVE CONTROL for NC2-06: the destination operation guard and record are skipped from the second execute on (a destination that
    would allow a second commit); the reuse predicates must fail."""
    import _ingress_ambiguity
    return _ingress_ambiguity.run(work / "ingress-ambiguity-second", fault_mode="after_commit,bind_fresh,allow_second_commit")


@scenario("nc_ingress_ambiguity_unbound_fresh")
def nc_ingress_ambiguity_unbound_fresh(work):
    """NEGATIVE CONTROL for NC2-06: without bind_fresh the fresh request id is HELD by approval binding and never reaches the executor
    again; that is not destination duplicate prevention, so the row must fail on the executor-call predicates."""
    import _ingress_ambiguity
    return _ingress_ambiguity.run(work / "ingress-ambiguity-unbound", fault_mode="after_commit")


def direct_surface_baseline(work):
    """Informational (no row): the excluded surfaces ARE reachable by direct in-process use of the components, which is the
    trusted-host limitation the ingress must exclude for ordinary clients. Recorded, not judged."""
    out = {}
    ctx = Ctx(work)
    try:
        claim = ctx.provision()
        r = ctx.execute(claim.claim_id, simulate="lost_ack")
        out["simulate_accepted_by_execute"] = {"status": r.status, "effect_count": ctx.count()}
        out["authority_writer_set_grant_status"] = attempt(lambda: ctx.dest.set_grant_status(ctx.flow.d1.binding.grant_id, status="revoked") or "accepted")["ok"]
    finally:
        ctx.close()
    ctx = Ctx(work / "raw")
    try:
        conn = sqlite3.connect(ctx.dest.path)
        step = attempt(lambda: conn.execute(
            "INSERT INTO effects(effect_id,operation_digest,grant_id,target,amount,unit,payload_json,state) VALUES('raw','x','g','t',1,'USD','{}','applied')"))
        conn.commit()
        conn.close()
        out["raw_sql_insert_into_effects"] = {"accepted": step["ok"], "error": err_of(step), "effect_count": ctx.count(),
                                              "claim_issued_for_it": False}
    finally:
        ctx.close()
    return out


@scenario("nc_tamper")
def nc_tamper(work):
    obs = {}
    ctx = Ctx(work)
    try:
        claim = ctx.provision()
        result = ctx.execute(claim.claim_id)
        raw, prop, export = ctx.raw_record(), ctx.proposal_json(), ctx.export(result)
        control = replay_import(raw, prop, export)
        bundle = control.pop("_bundle", None)
        ok = control["ok"]
        # record journal substitution
        bad = copy.deepcopy(raw)
        ev = next(e for e in bad["check_events"] if e["phase"] == "opened")
        ev["proposal_commitment"] = "sha256:" + "0" * 64
        t1 = replay_import(bad, prop, export)
        t1.pop("_bundle", None)
        obs["replay_record"] = {"control_accepted": ok, "control_error": control["error"], "tampered_accepted": t1["ok"], "tampered_error": t1["error"]}
        # executor export names a different effect
        badx = copy.deepcopy(export)
        badx["effects"][0]["effect_id"] = "unrelated"
        t2 = replay_import(raw, prop, badx)
        t2.pop("_bundle", None)
        obs["replay_export"] = {"control_accepted": ok, "control_error": control["error"], "tampered_accepted": t2["ok"], "tampered_error": t2["error"]}
        # Evidence Pack retained-source tamper
        if bundle is not None:
            pk = pack_import(ctx.flow.f.manifest, bundle)
            pack = pk.pop("_pack", None)
            tampered_valid = None
            tamper_note = None
            if pack is not None:
                from agent_governance_evidence_pack import validate_evidence_pack
                forged = pack.model_copy(deep=True)
                trace = forged.metadata["traceable_import"]
                trace["retained_sources"]["reconstruction_bundle"]["records"] = trace["retained_sources"]["reconstruction_bundle"]["records"][:-1]
                tamper_note = "dropped the last retained reconstruction record from the pack's retained source"
                tampered_valid = bool(validate_evidence_pack(forged).valid)
            obs["pack"] = {"control_valid": pk["valid"], "control_error": pk["error"], "tampered_valid": tampered_valid, "tamper": tamper_note}
        else:
            obs["pack"] = {"control_valid": False, "control_error": "no bundle: Replay refused the untampered chain", "tampered_valid": None}
        # Verifier: alter the decision result in the raw record
        out = _state.results_dir() / "artifacts" / "verifier"
        base_bytes = ctx.run_json_bytes()
        base = run_verifier("T0-untampered", out, record_bytes=base_bytes, proposal=prop, manifest=ctx.flow.f.manifest)
        altered = json.loads(base_bytes)
        altered["decisions"][0]["result"] = "hold"
        tv = run_verifier("T1-decision-altered", out, record_bytes=json.dumps(altered, sort_keys=True).encode(), proposal=prop, manifest=ctx.flow.f.manifest)
        obs["verifier_record"] = {"crashed": tv["crashed"], "baseline_exit_code": base["exit_code"], "tampered_exit_code": tv["exit_code"],
                                  "baseline_finding_codes": base["finding_codes"], "tampered_finding_codes": tv["finding_codes"],
                                  "new_finding_codes": sorted(set(tv["finding_codes"]) - set(base["finding_codes"])),
                                  "baseline_refuted": base["refuted_check_ids"], "tampered_refuted": tv["refuted_check_ids"],
                                  "tampered_report_sha256": tv["report_sha256"]}
        # destination row edited after the fact, then exported again
        conn = sqlite3.connect(ctx.dest.path)
        conn.execute("UPDATE effects SET amount=999.0")
        conn.commit()
        conn.close()
        ex2 = attempt(lambda: ctx.export(result), REFUSALS_VALUE)
        if ex2["ok"]:
            t3 = replay_import(raw, prop, ex2["value"])
            t3.pop("_bundle", None)
            obs["destination_row"] = {"control_accepted": ok, "control_error": control["error"], "export_raised": False, "export_changed": sha256_json(ex2["value"]) != sha256_json(export),
                                      "tampered_accepted": t3["ok"], "tampered_error": t3["error"]}
        else:
            obs["destination_row"] = {"control_accepted": ok, "control_error": control["error"], "export_raised": True, "export_error": err_of(ex2), "tampered_accepted": False,
                                      "tampered_error": err_of(ex2)}
    finally:
        ctx.close()
    return obs


@scenario("nc_custody")
def nc_custody(work):
    obs = {}
    ctx = Ctx(work / "a")
    try:
        claim = ctx.provision()
        result = ctx.execute(claim.claim_id)
        raw, prop, export = ctx.raw_record(), ctx.proposal_json(), ctx.export(result)
        control = replay_import(raw, prop, export)
        control.pop("_bundle", None)
        omitted = copy.deepcopy(raw)
        omitted["check_events"] = [e for e in omitted["check_events"] if e["phase"] != "input"]
        j = replay_import(omitted, prop, export)
        j.pop("_bundle", None)
        obs["journal_omitted"] = {"control_accepted": control["ok"], "control_error": control["error"], "tampered_accepted": j["ok"], "tampered_error": j["error"]}
        w = replay_import(raw, prop, None)
        w.pop("_bundle", None)
        obs["export_withheld"] = {"control_accepted": control["ok"], "control_error": control["error"], "import_ok": w["ok"], "import_error": w["error"],
                                  "reported_complete": bool(w["ok"] and w.get("all_reports_complete"))}
    finally:
        ctx.close()
    # destination store unavailable at effect time
    ctx = Ctx(work / "b")
    try:
        claim = ctx.provision()
        store = pathlib.Path(ctx.dest.path).parent
        gone = pathlib.Path(str(store) + ".gone")
        os.rename(store, gone)  # whole store directory (database and journal files) disappears; no stray empty database is created
        step = attempt(lambda: ctx.execute(claim.claim_id), NO_EXCEPTION + REFUSALS_STORE)
        if step["ok"]:
            obs["destination_unavailable"] = {**result_obs(step["value"]), "raised": False}
            rec = step["value"].observation if isinstance(step["value"].observation, dict) else {}
            obs["destination_unavailable"]["retry_eligible"] = rec.get("retry_eligible")
        else:
            obs["destination_unavailable"] = {"status": None, "raised": True, "error": err_of(step)}
        obs["destination_unavailable"]["store_absent_during_outage"] = not store.exists()
        os.rename(gone, store)
        obs["destination_unavailable"]["effect_count"] = ctx.count()
    finally:
        ctx.close()
    # authority store unreadable at claim issuance
    ctx = Ctx(work / "c")
    try:
        def broken(ref):
            raise TimeoutError("injected: authority store unreadable")
        ctx.flow.r.grant_status = broken
        step = attempt(ctx.provision, REFUSALS_AUTHORITY)
        obs["authority_unreadable"] = {"claim_ok": step["ok"], "error": err_of(step), "effect_count": ctx.count()}
    finally:
        ctx.close()
    return obs
