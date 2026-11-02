"""Subprocess probe for N26. NO downstream code is modified; each downstream function is called as published.

usage: probe_downstream.py make-control  <replay-src> <odes-root>                 -> prints a plain current-generation bundle (JSON) produced by that Replay
       probe_downstream.py odes          <replay-src> <odes-root> <bundle.json> <manifest.json>
       probe_downstream.py pack          <replay-src> <pack-root> <bundle.json> <manifest.json>
Prints one JSON line {"result": "accepted"|"refused", "type":..., "message":...}.
"""
import json
import sys
from pathlib import Path

mode, replay_src, root = sys.argv[1], sys.argv[2], Path(sys.argv[3])
sys.path.insert(0, replay_src)
sys.path.insert(0, str(root / "src"))


def emit(result, exc=None, **extra):
    print(json.dumps({"result": result, "type": type(exc).__name__ if exc else None, "message": str(exc)[:600] if exc else None, **extra}, sort_keys=True))


if mode == "make-control":
    from agent_replay_bundle import importers as I
    data = root / "tests" / "data" / "current_generation" / "valid"
    cp = json.loads((data / "control_plane_run.json").read_text())
    proposal = json.loads((data / "proposal.json").read_text())
    runtime = json.loads((data / "runtime_export.json").read_text())
    print(I.import_bounded_workflow(cp, proposal=proposal, moltbot_export=runtime, control_plane_revision=I.CONTROL_PLANE_CUR_REVISION).model_dump_json())
    sys.exit(0)
bundle = json.loads(Path(sys.argv[4]).read_text())
manifest = json.loads(Path(sys.argv[5]).read_text())
try:
    if mode == "odes":
        from odes.exporter import export_cognous_stack_package
        package = export_cognous_stack_package(manifest, bundle)
        emit("accepted", package_keys=sorted(package)[:5])
    else:
        from agent_governance_evidence_pack.importer import import_manifest_reconstruction
        pack = import_manifest_reconstruction(manifest, bundle)
        emit("accepted", pack_type=type(pack).__name__)
except BaseException as exc:   # the refusal TYPE and MESSAGE are the evidence
    emit("refused", exc)
