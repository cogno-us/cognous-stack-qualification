#!/usr/bin/env python3
"""Reproducible integration evidence runner for the Cognous Open Control Stack."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, shutil, signal, subprocess, sys, time, tempfile
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import patch


@contextmanager
def synthetic_service_clock():
    """Explicit synthetic time only; no source edit or freshness-policy change."""
    raw=os.environ.get("COGNOUS_SYNTHETIC_SERVICE_TIME")
    if raw is None:
        yield
        return
    value=datetime.fromisoformat(raw.replace("Z","+00:00"))
    if value.tzinfo is None:
        raise ValueError("Synthetic service clock must be timezone-aware")
    import agent_control_plane.bounded as bounded
    with patch.object(bounded,"_now",lambda:value.astimezone(timezone.utc)):
        yield


def pytest_configure(config):
    # Activated only by an explicit pytest -p tools.reference_release invocation.
    config._cognous_clock_context=synthetic_service_clock()
    config._cognous_clock_context.__enter__()


def pytest_unconfigure(config):
    context=getattr(config,"_cognous_clock_context",None)
    if context is not None:
        context.__exit__(None,None,None)

from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.optional_execution_profile import validate_checkout, qualification_environment
LOCK=json.loads((ROOT/"component-lock.json").read_text())
WORK=ROOT/".reference-work"
REUSE_CHECKOUTS=False
BATCHES = {
    "authority": {"control_plane", "control_plane_store", "hub_release_gate"},
    "exchange": {"gax_observation_repair", "gax_reference", "governed_transport", "governed_transport_integration", "gax_public_runtime_artifacts", "research_qualification"},
    "consumers": {"replay", "evidence_pack", "evidence_pack_v2", "evidence_pack_persistence", "odes", "replay_merged", "evidence_pack_merged", "odes_merged"},
    "registry": {"bitrep_verification", "index_bitrep_binding"},
}


CANDIDATE_PROFILE = "typed-refusal-candidate-20261015"
CANDIDATE_SUITES = {
    "authority": {"executor_refusal"},
    "exchange": {"gax_refusal", "gax_historical_artifacts"},
    "consumers": {"replay_refusal", "odes_refusal", "evidence_pack_refusal"},
    "registry": set(),
}


def required_batches(profile):
    candidate = profile.get("runtime_profile") == CANDIDATE_PROFILE
    return {name: suites | (CANDIDATE_SUITES[name] if candidate else set())
            for name, suites in BATCHES.items()}


def run(cmd, *, cwd=None, env=None, check=False):
    started=time.time()
    p=subprocess.Popen(cmd,cwd=cwd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
    try:
        output,_=p.communicate(timeout=240)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid,signal.SIGKILL)
        output,_=p.communicate()
        p.returncode=124
        output+="\nCommand process group exceeded 240-second limit.\n"
    rec={"command":cmd,"cwd":str(cwd or ROOT),"returncode":p.returncode,"seconds":round(time.time()-started,3),"output":output}
    if check and p.returncode: raise RuntimeError(output)
    return rec

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def checkout(name,spec,sha_key="sha"):
    repo=spec["repository"]; sha=spec[sha_key]
    dest=WORK/name
    if REUSE_CHECKOUTS and dest.exists():
        validate_checkout(dest, sha)
        return dest
    if dest.exists(): raise RuntimeError('Choose a fresh work directory; existing source is never deleted')
    # Reuse public object history for additional exact test generations without
    # making a moving branch or a shared dirty worktree a test dependency.
    origin = next((p for p in WORK.iterdir() if p != dest and (p/".git").exists()
                   and run(["git","remote","get-url","origin"],cwd=p)["output"].strip()
                   == f"https://github.com/{repo}.git"), None)
    run(["git","clone","-q",str(origin) if origin else f"https://github.com/{repo}.git",str(dest)],check=True)
    run(["git","checkout","-q","--detach",sha],cwd=dest,check=True)
    actual=run(["git","rev-parse","HEAD"],cwd=dest,check=True)["output"].strip()
    validate_checkout(dest, sha)
    return dest

def static_json_check(path):
    failures=[]
    for f in path.rglob("*.json"):
        if ".git" in f.parts: continue
        try: json.loads(f.read_text(encoding="utf-8"))
        except Exception as e: failures.append({"file":str(f.relative_to(path)),"error":str(e)})
    return failures

def release_passes(suite_runs, representative_runs, repeatable, matrix_passed, openshell):
    """Every component suite remains a mandatory gate independent of the matrix."""
    return bool(suite_runs and representative_runs
                and all(x["returncode"]==0 for x in suite_runs)
                and all(x["returncode"]==0 for x in representative_runs)
                and repeatable and matrix_passed and openshell["returncode"]==0)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("command",choices=["run"])
    ap.add_argument("--results-dir",default="results/reference")
    ap.add_argument("--reuse-checkouts",action="store_true",help="Reuse existing tracked-clean checkouts only at exact lock SHAs")
    ap.add_argument("--profile",help="Explicit candidate lock; default remains component-lock.json")
    ap.add_argument("--qualification-root",type=Path,help="Exact canonical suite checkout; required by the typed-refusal candidate")
    ap.add_argument("--batch",choices=sorted(BATCHES))
    args=ap.parse_args()
    global LOCK, WORK
    profile_path=Path(args.profile).resolve() if args.profile else ROOT/"component-lock.json"
    LOCK=json.loads(profile_path.read_text())
    if args.profile:
        WORK=ROOT/".full-candidate-work"
    if args.batch and not args.profile:
        raise SystemExit("Batch qualification requires an explicit candidate profile")
    out=(ROOT/args.results_dir).resolve()
    if out.exists() and any(out.iterdir()): raise SystemExit("Choose an empty results directory; retained evidence is preserved")
    out.mkdir(parents=True,exist_ok=True)
    global REUSE_CHECKOUTS
    REUSE_CHECKOUTS=args.reuse_checkouts
    if WORK.exists() and not REUSE_CHECKOUTS: shutil.rmtree(WORK)
    WORK.mkdir(exist_ok=REUSE_CHECKOUTS)

    execution_state="tested in pinned CI" if os.environ.get("GITHUB_ACTIONS")=="true" else "tested locally"
    components={}; setup=[]
    for name,spec in LOCK["components"].items():
        key="core_interop_sha" if name=="moltbot_safe" else "sha"
        components[name]=checkout(name,spec,key)
    components["moltbot_safe_accepted"]=checkout("moltbot_safe_accepted",LOCK["components"]["moltbot_safe"],"accepted_sha")

    previous_accepted={}
    for name,spec in LOCK.get("previous_accepted_test_dependencies",{}).items():
        previous_accepted[name]=checkout("previous_accepted_"+name,spec,"core_interop_sha" if name=="moltbot_safe" else "sha")
    historical={name:checkout("historical_"+name,spec) for name,spec in LOCK.get("historical_test_dependencies",{}).items()}

    dep=run([sys.executable,"-m","pip","install","-q","--require-hashes","-r",str(ROOT/"tools/requirements-release.lock")])
    setup.append({k:v for k,v in dep.items() if k!="output"})
    if dep["returncode"]: raise RuntimeError(dep["output"])

    candidate = LOCK.get("runtime_profile") == CANDIDATE_PROFILE
    qualification_root=args.qualification_root.resolve() if args.qualification_root else None
    if candidate and qualification_root is None:
        raise RuntimeError("Typed-refusal qualification requires --qualification-root with canonical test provenance")
    def canonical_test(suite,relative):
        path=qualification_root/"suites"/suite/relative
        inventory=json.loads((qualification_root/"migrations/cross-component-2026-10-15.json").read_text())
        matches=[r for r in inventory["repositories"][suite]["files"] if r["destination_path"]==str(path.relative_to(qualification_root))]
        if len(matches)!=1 or sha256(path)!=matches[0]["destination_sha256"]:
            raise RuntimeError("Unrecorded canonical test adaptation: "+str(path))
        return path
    selected_regression = {}
    if candidate:
        selected = json.loads((ROOT/"component-lock.json").read_text())
        for name in ("control_plane", "moltbot_safe", "replay_bundle", "odes", "governance_evidence_pack"):
            selected_regression[name] = checkout("selected_regression_"+name,
                selected["components"][name], "core_interop_sha" if name=="moltbot_safe" else "sha")

    cp=components["control_plane"]; replay=components["replay_bundle"]; agep=components["governance_evidence_pack"]
    odes=components["odes"]; gax=components["gax_imx_transport"]; molt=components["moltbot_safe"]
    manifest=components["action_manifest"]; bitrep=components["bitrep"]; index=components["the_index"]
    # Build package metadata outside the immutable checkout (tracked egg-info in
    # older source generations otherwise makes --reuse-checkouts reject its own run).
    with tempfile.TemporaryDirectory(prefix="cognous-evidence-build-") as directory:
        staged=Path(directory)/"evidence-pack"
        shutil.copytree(agep,staged,ignore=shutil.ignore_patterns(".git","__pycache__"))
        agep_install=run([sys.executable,"-m","pip","install","-q","--no-deps","--no-build-isolation",str(staged)])
    setup.append({k:v for k,v in agep_install.items() if k!="output"})
    if agep_install["returncode"]: raise RuntimeError(agep_install["output"])

    py=[str(ROOT),str(cp/"src"),str(replay/"src"),str(agep/"src"),str(odes/"src"),str(gax),str(molt),str(bitrep),str(index/"chain/python")]
    env=qualification_environment()
    env["PYTHONPATH"]=os.pathsep.join(py+[env.get("PYTHONPATH","")])
    env["PYTHONDONTWRITEBYTECODE"]="1"
    if LOCK.get("runtime_profile"):
        env["GAX_RUNTIME_COMPATIBILITY_PROFILE"]=LOCK["runtime_profile"]
    if candidate:
        env["COGNOUS_SYNTHETIC_SERVICE_TIME"]="2026-08-08T01:00:00Z"
    env["PATH"]=os.pathsep.join([str(Path(sys.executable).parent),env.get("PATH","")])
    env["COGNOUS_QUALIFICATION_LOCK"]=str(profile_path)
    env["COGNOUS_QUALIFICATION_WORK"]=str(WORK)
    env["BITREP_ROOT"]=str(bitrep)
    env["MOLTBOT_SAFE_CONTROL_PLANE_ROOT"]=str(cp)
    env["MOLTBOT_SAFE_ROOT"]=str(molt)
    env["MOLTBOT_SAFE_MANIFEST_FIXTURE"]=str(manifest/"examples/refund_integration_v1_1.manifest.json")
    env["UPSTREAM_MANIFEST_EXAMPLE"]=env["MOLTBOT_SAFE_MANIFEST_FIXTURE"]
    env["UPSTREAM_REPLAY_SUCCESS_EXAMPLE"]=str(replay/"examples/bounded_success_reconstruction_v0_2.json")
    env["UPSTREAM_REPLAY_LOST_ACK_EXAMPLE"]=str(replay/"examples/bounded_lost_ack_reconstruction_v0_2.json")
    env["UPSTREAM_GAX_ROOT"]=str(gax)
    env["UPSTREAM_CONTROL_PLANE_ROOT"]=str(cp)
    env["UPSTREAM_MOLTBOT_SAFE_ROOT"]=str(molt)
    env["ARB_PINNED_CONTROL_PLANE_ROOT"]=str(cp)
    env["ARB_PINNED_MOLTBOT_ROOT"]=str(molt)
    env["ARB_PINNED_MANIFEST_FIXTURE"]=env["MOLTBOT_SAFE_MANIFEST_FIXTURE"]
    env["ODES_PINNED_CONTROL_PLANE_ROOT"]=str(cp)
    env["ODES_PINNED_MOLTBOT_ROOT"]=str(molt)
    env["ODES_PINNED_REPLAY_ROOT"]=str(replay)
    env["ODES_PINNED_MANIFEST_FIXTURE"]=env["MOLTBOT_SAFE_MANIFEST_FIXTURE"]
    env["AGEP_PINNED_REPLAY_ROOT"]=str(replay)
    env["AGEP_PINNED_CONTROL_PLANE_ROOT"]=str(cp)
    env["AGEP_PINNED_MOLTBOT_ROOT"]=str(molt)
    env["AGEP_PINNED_MANIFEST_FIXTURE"]=env["MOLTBOT_SAFE_MANIFEST_FIXTURE"]

    env["ARB_V2_CONTROL_PLANE_ROOT"]=str(cp)
    env["ARB_V2_MOLTBOT_ROOT"]=str(molt)
    env["ODES_V2_REPLAY_ROOT"]=str(replay)
    # The selected persistence-generation Evidence Pack suite gets only its
    # four explicit accepted producer inputs. Previous producer-2.0.0 and
    # historical suites remain isolated below.
    agep_persistence_env=env.copy()
    agep_persistence_env["AGEP_ACCEPTED_REPLAY_ROOT"]=str(replay)
    agep_persistence_env["AGEP_PERSISTENCE_CONTROL_PLANE_ROOT"]=str(cp)
    agep_persistence_env["AGEP_ACCEPTED_EXECUTOR_ROOT"]=str(molt)
    agep_persistence_env["AGEP_MANIFEST_FIXTURE"]=env["MOLTBOT_SAFE_MANIFEST_FIXTURE"]

    historical_env=env.copy()
    historical_env["PYTHONPATH"]=os.pathsep.join([str(historical["control_plane"]/"src"),str(historical["moltbot_safe"]),env["PYTHONPATH"]])
    for prefix in ("ARB", "ODES", "AGEP"):
        historical_env[prefix+"_PINNED_CONTROL_PLANE_ROOT"]=str(historical["control_plane"])
        historical_env[prefix+"_PINNED_MOLTBOT_ROOT"]=str(historical["moltbot_safe"])
    for prefix in ("ODES", "AGEP"):
        historical_env[prefix+"_PINNED_REPLAY_ROOT"]=str(historical["replay_bundle"])
    historical_env["MOLTBOT_SAFE_CONTROL_PLANE_ROOT"]=str(historical["control_plane"])
    historical_env["MOLTBOT_SAFE_ROOT"]=str(historical["moltbot_safe"])
    previous_selected=LOCK.get("previous_selected_test_dependencies",{})
    previous_cp=checkout("previous_selected_control_plane",previous_selected["control_plane"])
    previous_replay=checkout("previous_selected_replay_bundle",previous_selected["replay_bundle"])
    previous_odes=checkout("previous_selected_odes",previous_selected["odes"])
    agep_v2_env=env.copy()
    agep_v2_env["PYTHONPATH"]=os.pathsep.join([str(previous_cp/"src"),str(previous_replay/"src"),str(previous_odes/"src"),str(molt),str(agep/"src"),str(ROOT)])
    agep_v2_env["ARB_V2_CONTROL_PLANE_ROOT"]=str(previous_cp)
    agep_v2_env["ARB_V2_MOLTBOT_ROOT"]=str(molt)
    agep_v2_env["ARB_PINNED_MANIFEST_FIXTURE"]=env["MOLTBOT_SAFE_MANIFEST_FIXTURE"]
    agep_v2_env["ODES_V2_REPLAY_ROOT"]=str(previous_replay)
    agep_v2_env["AGEP_V2_ODES_ROOT"]=str(previous_odes)

    # Replay mirrors accepted 043830b... workflow: historical producer roots,
    # ordinary v2 observation-repair root, and persistence-v2 root coexist.
    replay_env=env.copy()
    replay_env["PYTHONPATH"]=os.pathsep.join([str(replay/"src"),str(historical["control_plane"]/"src"),str(historical["moltbot_safe"]),str(ROOT)])
    replay_env["ARB_PINNED_CONTROL_PLANE_ROOT"]=str(historical["control_plane"])
    replay_env["ARB_PINNED_MOLTBOT_ROOT"]=str(historical["moltbot_safe"])
    replay_env["ARB_V2_CONTROL_PLANE_ROOT"]=str(previous_cp)
    replay_env["ARB_V2_PERSISTENCE_CONTROL_PLANE_ROOT"]=str(cp)
    replay_env["ARB_V2_MOLTBOT_ROOT"]=str(molt)
    replay_env["ARB_PINNED_MANIFEST_FIXTURE"]=env["MOLTBOT_SAFE_MANIFEST_FIXTURE"]

    # ODES mirrors accepted 0486b64... workflow: historical PINNED inputs stay
    # historical while v2 helper loading uses selected Replay + repaired CP.
    odes_env=env.copy()
    odes_env["PYTHONPATH"]=os.pathsep.join([str(odes/"src"),str(replay/"src"),str(ROOT)])
    odes_env["ODES_PINNED_CONTROL_PLANE_ROOT"]=str(historical["control_plane"])
    odes_env["ODES_PINNED_MOLTBOT_ROOT"]=str(historical["moltbot_safe"])
    odes_env["ODES_PINNED_REPLAY_ROOT"]=str(historical["replay_bundle"])
    odes_env["ODES_PINNED_MANIFEST_FIXTURE"]=env["MOLTBOT_SAFE_MANIFEST_FIXTURE"]
    odes_env["UPSTREAM_MANIFEST_EXAMPLE"]=env["MOLTBOT_SAFE_MANIFEST_FIXTURE"]
    odes_env["UPSTREAM_REPLAY_SUCCESS_EXAMPLE"]=str(historical["replay_bundle"]/"examples/bounded_success_reconstruction_v0_2.json")
    odes_env["UPSTREAM_REPLAY_LOST_ACK_EXAMPLE"]=str(historical["replay_bundle"]/"examples/bounded_lost_ack_reconstruction_v0_2.json")
    odes_env["ODES_V2_REPLAY_ROOT"]=str(replay)
    odes_env["ARB_V2_CONTROL_PLANE_ROOT"]=str(cp)
    odes_env["ARB_V2_MOLTBOT_ROOT"]=str(molt)
    odes_env["ARB_PINNED_MANIFEST_FIXTURE"]=env["MOLTBOT_SAFE_MANIFEST_FIXTURE"]

    agep_historical_env=historical_env.copy()
    agep_historical_env["PYTHONPATH"]=os.pathsep.join([str(historical["replay_bundle"]/"src"),str(historical["odes"]/"src"),str(historical["gax_imx_transport"]),historical_env["PYTHONPATH"]])
    agep_historical_env["UPSTREAM_CONTROL_PLANE_ROOT"]=str(historical["control_plane"])
    agep_historical_env["UPSTREAM_MOLTBOT_SAFE_ROOT"]=str(historical["moltbot_safe"])
    agep_historical_env["UPSTREAM_GAX_ROOT"]=str(historical["gax_imx_transport"])
    for key,filename in (("UPSTREAM_REPLAY_SUCCESS_EXAMPLE","bounded_success_reconstruction_v0_2.json"),("UPSTREAM_REPLAY_LOST_ACK_EXAMPLE","bounded_lost_ack_reconstruction_v0_2.json")):
        historical_env[key]=agep_historical_env[key]=str(historical["replay_bundle"]/"examples"/filename)

    # Preserve every historical producer pairing while evaluating the newer
    # consumer implementations. Candidate suites below exercise the new pair.
    merged_env=env.copy()
    if previous_accepted:
        old_cp=previous_accepted["control_plane"]
        old_molt=previous_accepted["moltbot_safe"]
        old_replay=previous_accepted["replay_bundle"]
        agep_v2_env["ARB_V2_MOLTBOT_ROOT"]=str(old_molt)
        agep_v2_env["PYTHONPATH"]=agep_v2_env["PYTHONPATH"].replace(str(molt),str(old_molt))
        replay_env["ARB_V2_PERSISTENCE_CONTROL_PLANE_ROOT"]=str(old_cp)
        replay_env["ARB_V2_MOLTBOT_ROOT"]=str(old_molt)
        for target in (odes_env,agep_persistence_env):
            target["PYTHONPATH"]=os.pathsep.join([str(old_cp/"src"),str(old_molt),str(old_replay/"src"),str(odes/"src"),str(agep/"src"),str(ROOT)])
            target["ARB_V2_CONTROL_PLANE_ROOT"]=str(old_cp)
            target["ARB_V2_MOLTBOT_ROOT"]=str(old_molt)
            target["ODES_V2_REPLAY_ROOT"]=str(old_replay)
        agep_persistence_env["AGEP_ACCEPTED_REPLAY_ROOT"]=str(old_replay)
        agep_persistence_env["AGEP_PERSISTENCE_CONTROL_PLANE_ROOT"]=str(old_cp)
        agep_persistence_env["AGEP_ACCEPTED_EXECUTOR_ROOT"]=str(old_molt)
        merged_env.update({"AGEP_ACCEPTED_REPLAY_ROOT":str(replay),"AGEP_PERSISTENCE_CONTROL_PLANE_ROOT":str(cp),"AGEP_ACCEPTED_EXECUTOR_ROOT":str(molt),"AGEP_MANIFEST_FIXTURE":env["MOLTBOT_SAFE_MANIFEST_FIXTURE"]})

    historical_merged_env = merged_env.copy()
    historical_gax_env = env.copy()
    if candidate:
        selected_cp=selected_regression["control_plane"]
        selected_molt=selected_regression["moltbot_safe"]
        selected_replay=selected_regression["replay_bundle"]
        selected_odes=selected_regression["odes"]
        selected_agep=selected_regression["governance_evidence_pack"]
        historical_merged_env.update({
            "ARB_V2_CONTROL_PLANE_ROOT":str(selected_cp),
            "ARB_V2_PERSISTENCE_CONTROL_PLANE_ROOT":str(selected_cp),
            "ARB_V2_MOLTBOT_ROOT":str(selected_molt),
            "ODES_V2_REPLAY_ROOT":str(selected_replay),
            "AGEP_V2_ODES_ROOT":str(selected_odes),
            "AGEP_ACCEPTED_REPLAY_ROOT":str(selected_replay),
            "AGEP_PERSISTENCE_CONTROL_PLANE_ROOT":str(selected_cp),
            "AGEP_ACCEPTED_EXECUTOR_ROOT":str(selected_molt),
        })
        historical_merged_env.pop("COGNOUS_SYNTHETIC_SERVICE_TIME",None)
        historical_gax_env.update({
            "GAX_RUNTIME_COMPATIBILITY_PROFILE":"merged-producers-v1",
            "MOLTBOT_SAFE_CONTROL_PLANE_ROOT":str(selected_cp),
            "MOLTBOT_SAFE_ROOT":str(selected_molt),
            "PYTHONPATH":os.pathsep.join([str(ROOT),str(selected_cp/"src"),
                str(selected_molt),str(selected_replay/"src"),str(selected_odes/"src"),
                str(selected_agep/"src"),str(gax)]),
        })
        historical_gax_env.pop("COGNOUS_SYNTHETIC_SERVICE_TIME",None)

    refusal_env=env.copy()
    refusal_env.update({"ARB_REFUSAL_CP_ROOT":str(cp),
                        "ARB_REFUSAL_EXECUTOR_ROOT":str(molt)})
    refusal_env.pop("COGNOUS_SYNTHETIC_SERVICE_TIME",None)

    if args.batch in (None,"registry"):
        npm=run(["npm","ci","--ignore-scripts"],cwd=index/"chain")
        setup.append({k:v for k,v in npm.items() if k!="output"})
        if npm["returncode"]: raise RuntimeError(npm["output"])

    suites=[
      ("gax_observation_repair",[sys.executable,"-m","pytest","-q",str(gax/"tests/test_observation_repair.py")],ROOT),
      ("gax_reference",[sys.executable,"-m","pytest","-q",str(gax/"tests/test_gax_imx_reference.py"),str(gax/"tests/test_gax_imx_redelivery.py")],ROOT),
      ("governed_transport",[sys.executable,"-m","pytest","-q",str(gax/"tests/test_governed_message_transport.py")],ROOT),
      ("governed_transport_integration",[sys.executable,"-m","pytest","-q",str(canonical_test("cognous-governed-exchange","tests/test_governed_message_transport_integration.py") if candidate else gax/"tests/test_governed_message_transport_integration.py")],ROOT),
      ("gax_public_runtime_artifacts",[sys.executable,"-m","pytest","-q",str(canonical_test("cognous-governed-exchange","qualification/test_merged_artifacts.py") if candidate else gax/("qualification/test_merged_artifacts.py" if previous_accepted else "tests/test_gax_public_runtime_artifacts.py"))],ROOT),
      ("control_plane",[sys.executable,"-m","pytest","-q",str(cp/"tests/test_bounded_authorization.py")],ROOT),
      ("control_plane_store",[sys.executable,"-m","pytest","-q",str(cp/"tests/test_record_store_concurrency.py")],cp),
      ("replay",[sys.executable,"-m","pytest","-q",str(replay/"tests"), *(["--ignore="+str(replay/"tests/test_refusal_evidence.py")] if candidate else [])],replay),
      ("evidence_pack",[sys.executable,"-m","pytest","-q",str(agep/"tests"),"--ignore="+str(agep/"tests/test_producer_v2.py"),"--ignore="+str(agep/"tests/test_control_plane_store_compatibility.py")],agep),
      ("evidence_pack_v2",[sys.executable,"-m","pytest","-q",str(agep/"tests/test_producer_v2.py")],agep),
      ("evidence_pack_persistence",[sys.executable,"-m","pytest","-q",str(agep/"tests/test_control_plane_store_compatibility.py")],agep),
      ("odes",[sys.executable,"-m","pytest","-q",str(odes/"tests")],odes),
      ("bitrep_verification",[sys.executable,"-m","pytest","-q",str(bitrep/"tests/test_verification.py"),str(bitrep/"tests/test_api.py")],bitrep),
      ("index_bitrep_binding",[sys.executable,"-m","pytest","-q",str(index/"chain/python/test_bitrep.py")],ROOT),
      ("research_qualification",[sys.executable,"-m","pytest","-q",str(ROOT/"tests/test_research_qualification.py")],ROOT),
      ("hub_release_gate",[sys.executable,"-m","pytest","-q",str(ROOT/"tests/test_release_gate.py")],ROOT),
    ]

    if previous_accepted:
        suites.extend([
            ("replay_merged",[sys.executable,"-m","pytest","-q",str(replay/"qualification/test_merged_producer.py")],replay),
            ("evidence_pack_merged",[sys.executable,"-m","pytest","-q",str(agep/"qualification/test_merged_producer.py")],agep),
            ("odes_merged",[sys.executable,"-m","pytest","-q",str(odes/"qualification/test_merged_producer.py")],odes),
        ])
    if candidate:
        suites.extend([
            ("gax_historical_artifacts",[sys.executable,"-m","pytest","-q",str(gax/"qualification/test_merged_artifacts.py")],gax),
            ("executor_refusal",[sys.executable,"-m","pytest","-q",str(molt/"tests/test_refusal_capture.py")],molt),
            ("replay_refusal",[sys.executable,"-m","pytest","-q",str(replay/"tests/test_refusal_evidence.py")],replay),
            ("odes_refusal",[sys.executable,"-m","pytest","-q",str(odes/"qualification/test_refusal_profile.py")],odes),
            ("evidence_pack_refusal",[sys.executable,"-m","pytest","-q",str(agep/"qualification/test_refusal_profile.py")],agep),
            ("gax_refusal",[sys.executable,"-m","pytest","-q",str(gax/"candidate_qualification/test_typed_refusal_profile.py")],gax),
        ])
    if args.batch:
        suites=[entry for entry in suites if entry[0] in required_batches(LOCK)[args.batch]]

    runs=[]; representative_runs=[]; normalized=[]

    # Focused corrected producer-generation suites run once before the two full
    # qualification repetitions. These are diagnostic preflights, not matrix
    # repetition evidence.
    preflight_dir=out/"preflight"
    preflight_dir.mkdir()
    preflight_specs=[
        ("replay", [sys.executable,"-m","pytest","-q",str(replay/"tests")], replay, replay_env),
        ("odes", [sys.executable,"-m","pytest","-q",str(odes/"tests")], odes, odes_env),
    ]
    preflight_runs=[]
    for name,cmd,cwd,suite_env in ([] if args.batch else preflight_specs):
        junit=preflight_dir/f"{name}.xml"
        rec=run(list(cmd)+["--junitxml",str(junit)],cwd=cwd,env=suite_env)
        (preflight_dir/f"{name}.log").write_text(rec["output"],encoding="utf-8")
        rec.update({"suite":name,"junit":str(junit.relative_to(out)),"log":str((preflight_dir/f"{name}.log").relative_to(out))})
        rec.pop("output")
        preflight_runs.append(rec)
    if any(x["returncode"] for x in preflight_runs):
        raise RuntimeError("focused Replay/ODES preflight failed; see preflight logs")

    for repetition in (1,2):
        rdir=out/f"run-{repetition}"
        rdir.mkdir()
        if args.batch in (None,"exchange"):
            repdir=rdir/"representative"
            rep=run([
                sys.executable,str(ROOT/"tools/transported_reference.py"),
                "--manifest",str(manifest/"examples/refund_integration_v1_1.manifest.json"),
                "--replay",str(replay/"examples/bounded_success_reconstruction_v0_2.json"),
                "--out",str(repdir),
            ],env=env)
            (rdir/"representative.log").write_text(rep["output"],encoding="utf-8")
            rep.update({"repetition":repetition,"log":str((rdir/"representative.log").relative_to(out))})
            rep.pop("output")
            representative_runs.append(rep)
            evo=repdir/"expected-vs-observed.json"
            if rep["returncode"]==0 and evo.exists():
                normalized.append(load:=json.loads(evo.read_text(encoding="utf-8"))["normalized"])
            else:
                normalized.append(None)

        env["BATCH4C_RESULTS_DIR"]=str(rdir/"research-qualification")
        env["GAX_QUALIFICATION_RESULTS"]=str(rdir/"gax-observation-results.json")
        env["STORE_CONCURRENCY_EVIDENCE"]=str(rdir/"control-plane-store-evidence")
        for name,cmd,cwd in suites:
            actual=list(cmd)
            junit=rdir/f"{name}.xml"
            actual.extend(["--junitxml",str(junit)])
            suite_env=(refusal_env if name.endswith("_refusal") else historical_gax_env if candidate and name=="gax_historical_artifacts" else historical_merged_env if name.endswith("_merged") else agep_historical_env if name=="evidence_pack" else agep_v2_env if name=="evidence_pack_v2" else agep_persistence_env if name=="evidence_pack_persistence" else replay_env if name=="replay" else odes_env if name=="odes" else env)
            suite_env={**suite_env,"BATCH4C_RESULTS_DIR":env["BATCH4C_RESULTS_DIR"],"GAX_QUALIFICATION_RESULTS":env["GAX_QUALIFICATION_RESULTS"],"STORE_CONCURRENCY_EVIDENCE":env["STORE_CONCURRENCY_EVIDENCE"]}
            if candidate and (name in {"hub_release_gate","research_qualification","gax_observation_repair","gax_reference","gax_public_runtime_artifacts","governed_transport","governed_transport_integration"}):
                actual.extend(["-p","tools.reference_release"])
            rec=run(actual,cwd=cwd,env=suite_env)
            (rdir/f"{name}.log").write_text(rec["output"],encoding="utf-8")
            rec.update({"suite":name,"repetition":repetition,"log":str((rdir/f"{name}.log").relative_to(out)),"junit":str(junit.relative_to(out))})
            rec.pop("output")
            runs.append(rec)

        if args.batch in (None,"registry"):
            node=run(["npm","test"],cwd=index/"chain",env=env)
            (rdir/"index_local_chain.log").write_text(node["output"],encoding="utf-8")
            node.update({"suite":"index_local_chain","repetition":repetition,"log":str((rdir/"index_local_chain.log").relative_to(out))})
            node.pop("output"); runs.append(node)

    representative_repeatable=bool(len(normalized)==2 and normalized[0] is not None and normalized[0]==normalized[1])
    (out/"representative-repeatability.json").write_text(json.dumps({
        "passed":representative_repeatable,
        "comparison":"normalized expected outcomes only; generated identifiers and timestamps excluded",
        "run_1":normalized[0] if normalized else None,"run_2":normalized[1] if len(normalized)>1 else None,
    },indent=2,sort_keys=True),encoding="utf-8")

    if args.batch:
        extra=[]
        if args.batch=="authority":
            mock_env=env.copy()
            if candidate:mock_env["COGNOUS_SYNTHETIC_SERVICE_TIME"]="2026-10-05T19:00:00Z"
            extra.append(run([sys.executable,"-m","pytest","-q",*(["-p","tools.reference_release"] if candidate else []),str(molt/"tests/test_openshell_environment.py"),"--junitxml",str(out/"openshell-mock.xml")],env=mock_env))
        if args.batch=="registry":
            for name in ("prp","research_intelligence","tfa"):
                extra.append({"returncode":int(bool(static_json_check(components[name]))),"scope":"static JSON only"})
        report={"release_dependency_lock_sha256":sha256(ROOT/"tools/requirements-release.lock"),"batch":args.batch,"profile_sha256":sha256(profile_path),"profile":LOCK,"selected_regression_pins":{name:run(["git","rev-parse","HEAD"],cwd=path,check=True)["output"].strip() for name,path in selected_regression.items()},"synthetic_service_clock":env.get("COGNOUS_SYNTHETIC_SERVICE_TIME"),"qualification_commit":run(["git","rev-parse","HEAD"],cwd=qualification_root,check=True)["output"].strip() if qualification_root else None,"qualification_manifest_sha256":sha256(qualification_root/"migrations/cross-component-2026-10-15.json") if qualification_root else None,"suite_runs":runs,"representative_runs":representative_runs,"representative_repeatable":representative_repeatable,"extra":extra,"passed":bool(runs) and all(r["returncode"]==0 for r in runs+extra) and (args.batch!="exchange" or representative_repeatable),"release_qualified":False}
        (out/(args.batch+"-summary.json")).write_text(json.dumps(report,indent=2)+"\n")
        print(json.dumps({"batch":args.batch,"passed":report["passed"]}))
        return 0 if report["passed"] else 1

    matrix_run=run([
        sys.executable,str(ROOT/"tools/release_gate.py"),
        "--matrix",str(ROOT/"scenarios/acceptance-matrix.json"),
        "--results",str(out),
    ],env=env)
    (out/"matrix-resolution.log").write_text(matrix_run["output"],encoding="utf-8")
    matrix_run["log"]="matrix-resolution.log"; matrix_run.pop("output")
    matrix_results={}
    matrix_path=out/"scenario-matrix-results.json"
    if matrix_path.exists():
        matrix_results=json.loads(matrix_path.read_text(encoding="utf-8"))

    acc=components["moltbot_safe_accepted"]
    open_env=env.copy()
    open_env["PYTHONPATH"]=os.pathsep.join([str(cp/"src"),str(acc),open_env.get("PYTHONPATH","")])
    open_env["MOLTBOT_SAFE_ROOT"]=str(acc)
    open_xml=out/"openshell-mock.xml"
    # The adapter test moved to the qualification package when cross-component tests were relocated
    # (absent from runtime revisions after that move); prefer the runtime copy when it still exists.
    openshell_test=acc/"tests/test_openshell_environment.py"
    if not openshell_test.exists():
        openshell_test=ROOT/"_qualification/suites/cognous-execution-runtime/tests/test_openshell_environment.py"
    openshell=run([sys.executable,"-m","pytest","-q",str(openshell_test),"--junitxml",str(open_xml)],env=open_env)
    (out/"openshell-mock.log").write_text(openshell["output"],encoding="utf-8")
    openshell.update({"scope":"mocked adapter only","evidence_state":execution_state if openshell["returncode"]==0 else "blocked","log":"openshell-mock.log","junit":"openshell-mock.xml"})
    openshell.pop("output")

    optional={}
    for name in ("prp","research_intelligence","tfa"):
        failures=static_json_check(components[name])
        optional[name]={"state":execution_state if not failures else "blocked","check":"JSON syntax/static artifact parse only; model-behavior evaluations unexecuted","failures":failures}

    actual_pins={name:run(["git","rev-parse","HEAD"],cwd=path,check=True)["output"].strip() for name,path in components.items()}
    matrix_pass=matrix_run["returncode"]==0 and matrix_results.get("gate_passed") is True

    totals={}
    for repetition in (1,2):
        counts={key:0 for key in ("tests","failures","errors","skipped")}
        for path in (out/f"run-{repetition}").glob("*.xml"):
            for suite in ET.parse(path).getroot().iter("testsuite"):
                for key in counts: counts[key]+=int(suite.get(key,0))
        counts["passed"]=counts["tests"]-counts["failures"]-counts["errors"]-counts["skipped"]
        totals[str(repetition)]=counts
    summary={
      "test_totals":totals,
      "evidence_state":execution_state,
      "dependency_status":LOCK.get("qualification_status", "accepted"),
      "dependency_lock":LOCK,
      "environment":{"python":sys.version,"platform":platform.platform()},
      "setup_commands":setup,
      "actual_pins":actual_pins,
      "historical_test_pins":{name:run(["git","rev-parse","HEAD"],cwd=path,check=True)["output"].strip() for name,path in historical.items()},
      "representative_runs":representative_runs,
      "representative_repeatability":representative_repeatable,
      "preflight_runs":preflight_runs,"suite_runs":runs,
      "scenario_gate":matrix_results,
      "openshell":openshell,
      "optional_instruction_layers":optional,
      "compatibility":{
        "core_moltbot_pin":LOCK["components"]["moltbot_safe"]["core_interop_sha"],
        "accepted_moltbot_head":LOCK["components"]["moltbot_safe"]["accepted_sha"],
        "moltbot_provenance_gap":LOCK["components"]["moltbot_safe"]["core_interop_sha"]!=LOCK["components"]["moltbot_safe"]["accepted_sha"],
        "gax_public_entrypoint":"supported runtime imports public Moltbot producer/executor modules and requires caller-supplied resolver and execution policy",
        "transport_original_artifact_retention":"versioned retained-artifact interface exposes original Replay, ODES validation/package and successor artifacts with content commitments",
        "evidence_recovery":"post-effect artifact failure is represented as recovery_required until evidence-only recovery produces an explicitly derived artifact without a replacement effect",
        "legacy_executor_evidence":"legacy unversioned Moltbot artifacts remain consumer-managed and revision-pinned; they are not relabeled as producer-profile 2.0.0 evidence",
      },
      "live_openshell":{
        "state":"unexecuted",
        "command":"MOLTBOT_SAFE_OPENSHELL_CONFIG=/path/to/qualified-config.json MOLTBOT_SAFE_OPENSHELL_BINARY=/path/to/openshell MOLTBOT_SAFE_OPENSHELL_HOME=/path/to/isolated-home python -m pytest -q .reference-work/moltbot_safe_accepted/tests/test_openshell_live.py",
        "reason":"requires pre-authorized live OpenShell gateway, worker image and isolated home; runner never provisions paid or external infrastructure"
      },
    }
    summary["release_dependency_lock_sha256"]=sha256(ROOT/"tools/requirements-release.lock")
    summary["release_gate_passed"]=release_passes(runs, representative_runs, representative_repeatable, matrix_pass, openshell)
    summary["candidate_qualification_passed"]=summary["release_gate_passed"]
    summary["gate_passed_for_selected_lock"]=summary["release_gate_passed"] and LOCK.get("qualification_status") != "candidate"
    summary["release_qualified"]=False  # Compatibility field: execution never grants release authority.
    (out/"scenario-results.json").write_text(json.dumps(summary,indent=2,sort_keys=True),encoding="utf-8")
    (out/"component-pins.json").write_text(json.dumps(actual_pins,indent=2,sort_keys=True),encoding="utf-8")
    artifacts=[]
    for f in sorted(out.rglob("*")):
        if f.is_file(): artifacts.append({"path":str(f.relative_to(out)),"sha256":sha256(f),"bytes":f.stat().st_size})
    (out/"artifact-index.json").write_text(json.dumps({"artifacts":artifacts},indent=2),encoding="utf-8")
    print(json.dumps({
        "results_dir":str(out),
        "evidence_state":execution_state,
        "release_gate_passed":summary["release_gate_passed"],
        "representative_repeatable":representative_repeatable,
        "scenario_gate_passed":matrix_pass,
        "openshell_mock":openshell["returncode"]==0,
    },indent=2))
    return 0 if summary["release_gate_passed"] else 1

if __name__=="__main__": raise SystemExit(main())
