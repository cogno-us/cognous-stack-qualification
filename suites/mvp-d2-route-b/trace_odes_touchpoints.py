"""Worker D2: run the MVP chain touchpoints (route B -> export -> Replay -> Evidence Pack -> Verifier) at the exact tuple with an audit
hook that records every file open and module import, to see whether ODES exporter/examples are touched."""
import sys, os, json, pathlib, tempfile
D2 = "/tmp/wk/o31/D2"
for p in reversed([f"{D2}/cognous-stack-qualification/suites/operation-identity", f"{D2}/cognous-stack-qualification/suites/mvp-d2-route-b",
          f"{D2}/cognous-execution-runtime", f"{D2}/cognous-control-plane/src", f"{D2}/cognous-control-plane",
          f"{D2}/rp-wt/src", f"{D2}/src/pack/src", f"{D2}/src/verifier/src", f"{D2}/src/odes/src", "/tmp/wk/mvp/H/pyd"]):
    sys.path.insert(0, p)
os.environ["D2_CONTROL_PLANE_DIR"] = f"{D2}/cognous-control-plane"; os.environ["D2_RUNTIME_DIR"] = f"{D2}/cognous-execution-runtime"
OPENED, IMPORTED = [], set()
def hook(event, args):
    if event == "open" and isinstance(args[0], str): OPENED.append(args[0])
    elif event == "import": IMPORTED.add(args[0])
sys.addaudithook(hook)
import pytest
import test_route_b_end_to_end as t
from engine.safe_executor import snapshot_envelope
from engine.producer_contract import export_execution_artifacts
import agent_replay_bundle.importers as rp
from agent_governance_evidence_pack import import_manifest_reconstruction, validate_evidence_pack
from cognous_verify import engine as vengine

def chain(label, dest_cls=None):
    tmp = pathlib.Path(tempfile.mkdtemp(dir=D2))
    mp, flow, dest, ex, claim = t._build(tmp, dest_cls=dest_cls, wide=True)
    res = t._run(flow, ex, claim, attempt_id="attempt-1")
    export = export_execution_artifacts(flow.envelope(flow.d1), res, dest, repository_revision=rp.MOLTBOT_P2_REVISION)
    raw = flow.f.records.load().model_dump(mode="json"); prop = flow.p.model_dump(mode="json")
    out = {"label": label, "result": (res.status, res.observed_state)}
    try:
        b = rp.import_bounded_workflow(raw, proposal=prop, moltbot_export=export, control_plane_revision=rp.CONTROL_PLANE_P2_REVISION)
        d = b.model_dump(mode="json"); out["replay"] = (d["status"], all(r["complete"] for r in d["import_reports"]))
        try:
            pack = import_manifest_reconstruction(flow.f.manifest, d)
            out["pack"] = (pack.metadata["traceable_import"]["replay_semantic_validation"].get("status"), validate_evidence_pack(pack).valid)
        except Exception as e: out["pack"] = ("REFUSED", type(e).__name__, str(e)[:200])
    except Exception as e: out["replay"] = ("REFUSED", type(e).__name__, str(e)[:240])
    e = vengine.evaluate([vengine.InputFile("run_record", "r.json", json.dumps(raw).encode())])
    out["verifier"] = (e.overall, e.crashed, [(r.check_id, r.verdict, r.reason) for r in e.checks if r.verdict != "confirmed"][:6])
    mp.undo(); return out

def chain_control(label, dest_cls=None, lost=False):
    """Journal from the real route-A flow (no claim provisioning, so no journal_check_reused); executor export from route B
    on the same envelope (the qualification c06 construction). Isolates the ODES-touchpoint question from the claim-journal defect."""
    import importlib.util
    from _oi_flow import Flow
    from engine.atomic_local_control_plane_executor import AtomicLocalControlPlaneExecutor
    from engine.operation_identity_atomic_destination import OperationIdentityAtomicAuthorityEffectDestination as Dest
    spec = importlib.util.spec_from_file_location("rt_helper", f"{D2}/cognous-execution-runtime/tests/test_atomic_route_valid_flow_identity.py")
    h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
    tmp = pathlib.Path(tempfile.mkdtemp(dir=D2)); mp = pytest.MonkeyPatch()
    flow = Flow(tmp, mp, identity=True, wide=False)
    env = flow.envelope(flow.d1)
    a_res = flow.run(flow.d1)
    dest = (dest_cls or Dest)(tmp / "b", clock=lambda: flow.NOW)
    dest.provision_claim(h.make_claim(env, claim_id="claim-1"))
    ex = AtomicLocalControlPlaneExecutor(workflow=flow.f, destination=dest, policy=flow.policy, operation_identity=True)
    res = ex.execute(envelope=env, claim_id="claim-1", attempt_id="attempt-1")
    if label.endswith("routeA"):
        res, dest = a_res, flow.dest
    export = export_execution_artifacts(env, res, dest, repository_revision=rp.MOLTBOT_P2_REVISION)
    raw = flow.f.records.load().model_dump(mode="json"); prop = flow.p.model_dump(mode="json")
    out = {"label": label, "routeA_status": a_res.status, "routeB_result": (res.status, res.observed_state)}
    try:
        b = rp.import_bounded_workflow(raw, proposal=prop, moltbot_export=export, control_plane_revision=rp.CONTROL_PLANE_P2_REVISION)
        d = b.model_dump(mode="json"); out["replay"] = (d["status"], all(r["complete"] for r in d["import_reports"]))
        try:
            pack = import_manifest_reconstruction(flow.f.manifest, d)
            out["pack"] = (pack.metadata["traceable_import"]["replay_semantic_validation"].get("status"), validate_evidence_pack(pack).valid)
        except Exception as e: out["pack"] = ("REFUSED", type(e).__name__, str(e)[:200])
    except Exception as e: out["replay"] = ("REFUSED", type(e).__name__, str(e)[:240])
    e = vengine.evaluate([vengine.InputFile("run_record", "r.json", json.dumps(raw).encode()), vengine.InputFile("proposal_export", "p.json", json.dumps(prop).encode()), vengine.InputFile("manifest", "m.json", json.dumps(flow.f.manifest).encode())])
    out["verifier"] = (e.overall, e.crashed, [(r.check_id, r.verdict, r.reason) for r in e.checks if r.verdict != "confirmed"][:8])
    mp.undo(); return out

import test_route_b_end_to_end as T
print(json.dumps(chain_control("control-routeA"), default=str))
print(json.dumps(chain_control("control-executed"), default=str))
print(json.dumps(chain_control("control-lost-ack", T._lost_ack_dest()), default=str))
for o in (chain("executed"), chain("lost-ack", T._lost_ack_dest())):
    print(json.dumps(o, default=str))
hits = sorted({p for p in OPENED if "package.json" in p or "/odes/" in p or "producer-v2" in p})
print("OPENED paths matching package.json|/odes/|producer-v2:", hits)
print("IMPORTED modules starting with odes:", sorted(m for m in IMPORTED if m == "odes" or m.startswith("odes.")))
print("opened files total:", len(OPENED), "; any under", f"{D2}/src/odes:", [p for p in OPENED if p.startswith(f"{D2}/src/odes")])
