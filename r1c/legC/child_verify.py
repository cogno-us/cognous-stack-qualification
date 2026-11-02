"""One real-source verification in a FRESH interpreter (the verifier imports the verified modules, so cases must not share a process).
argv[1] = JSON {exchange, profile, paths[], cp, runtime, manifest_file, entry}. Prints one JSON line: {"status": "ACCEPTED"|"REFUSED", ...}.
entry = "verify" calls Exchange's _verify_refusal_profile_sources(cp_root, molt_root); entry = "load" calls the public load_executor_runtime()."""
import json, os, sys, traceback

a = json.loads(sys.argv[1])
os.environ["GAX_RUNTIME_COMPATIBILITY_PROFILE"] = a["profile"]
os.environ["MOLTBOT_SAFE_CONTROL_PLANE_ROOT"] = a["cp"]
os.environ["MOLTBOT_SAFE_ROOT"] = a["runtime"]
os.environ["UPSTREAM_MANIFEST_EXAMPLE"] = a["manifest_file"]
sys.path[:] = [p for p in sys.path if p not in ("", ".")]
sys.path = [os.path.join(a["cp"], "src"), a["runtime"], a["exchange"]] + list(a["paths"]) + sys.path  # cp/src and runtime first: exactly what load_executor_runtime() prepends
out = {"profile": a["profile"], "entry": a["entry"]}
try:
    from experiments.odex_gax_imx_reference import gax_ref_runtime as rt
    out["module_profile"] = rt.RUNTIME_COMPATIBILITY_PROFILE
    out["pins"] = {k: getattr(rt, k) for k in ("CP_REVISION", "MOLTBOT_REVISION", "MANIFEST_REVISION", "REPLAY_REVISION", "ODES_REVISION", "EVIDENCE_PACK_REVISION")}
    from pathlib import Path
    if a["entry"] == "verify":
        rt._verify_refusal_profile_sources(Path(a["cp"]).resolve(), Path(a["runtime"]).resolve())
    else:
        rt.load_executor_runtime()
    out["status"] = "ACCEPTED"
    out["modules"] = {m: str(getattr(sys.modules.get(m), "__file__", None)) for m in ("agent_control_plane.bounded", "engine.producer_contract", "agent_replay_bundle.importers", "odes.exporter", "agent_governance_evidence_pack.importer")}
except BaseException as e:  # noqa: BLE001 - every refusal is recorded with its type and message
    out["status"] = "REFUSED"
    out["error_type"] = type(e).__name__
    out["message"] = str(e)[:300]
    out["cause"] = repr(e.__cause__)[:200] if e.__cause__ else None
    out["tb_last"] = traceback.format_exc().strip().splitlines()[-3:]
print("CHILD_RESULT " + json.dumps(out))
