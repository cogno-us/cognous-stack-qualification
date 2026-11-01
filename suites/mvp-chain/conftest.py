"""mvp-chain suite wiring: explicit component checkouts, each HEAD refused unless it equals the tuple pin.

SPDX-License-Identifier: Apache-2.0

Components come from explicit environment paths (MVP_CP_DIR, MVP_RUNTIME_DIR, MVP_REPLAY_DIR, MVP_PACK_DIR, MVP_ODES_DIR,
MVP_VERIFIER_DIR, MVP_MANIFEST_DIR, MVP_HUB_DIR). The expected shas come from the tuple pin file (MVP_PIN_FILE, default
process/mvp-chain/tuple-pin.proposed.json). Every component revision is a run parameter: MVP_<NAME>_REVISION (40-hex, named by rev_env in the pin file) replaces that component's pin-file
sha (a PENDING null pin requires it) and each override is recorded in the results. Any mismatch, dirty checkout, unset variable or
module imported from outside its pinned tree fails every test; nothing skips. Missing components are never papered over.
Statuses are computed from process/mvp-chain/expectations.proposed.v8.json (the builder's proposal: v7 plus the real-kill row NC2-07, the ledger-pruning row NC3-04, the rescoped deterministic NC4-03 and the host subcases NC4-03a..d; MVP_EXPECTATIONS overrides the path, for example to reproduce v3 or v7) and the recorded
observations only; see verdict.py.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _path in (str(HERE), str(ROOT / "suites"), str(ROOT / "suites" / "operation-identity"), str(ROOT / "tools")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import _state  # noqa: E402
import verdict  # noqa: E402

SHA = re.compile(r"[0-9a-f]{40}")
SRC_SUBDIR = {"control_plane": "src", "replay": "src", "evidence_pack": "src", "verifier": "src", "runtime": ".", "odes": ".", "action_manifest": "."}
# import path entries, first wins: the repo roots of the CP tests package and the runtime engine must precede everything else
_WIRE_ORDER = ("replay", "evidence_pack", "runtime", "control_plane")


def _git(path, *args):
    return subprocess.check_output(["git", "-C", str(path), *args], text=True, timeout=60).strip()


def pin_file() -> Path:
    return Path(os.environ.get("MVP_PIN_FILE") or ROOT / "process" / "mvp-chain" / "tuple-pin.proposed.json")


def expectations_file() -> Path:
    return Path(os.environ.get("MVP_EXPECTATIONS") or ROOT / "process" / "mvp-chain" / "expectations.proposed.v8.json")


def _wire():
    env = _state.ENV
    pins = json.loads(pin_file().read_text())
    env["pin_file"] = str(pin_file())
    env["pin_file_sha256"] = hashlib.sha256(pin_file().read_bytes()).hexdigest()
    comps = {k: dict(v) for k, v in pins["components"].items()}
    env["overrides"], env["pending"] = {}, []
    for name, spec in comps.items():
        override = os.environ.get(spec["rev_env"])
        if override:
            if not SHA.fullmatch(override):
                env["problems"].append(f"{spec['rev_env']} is not a 40-hex commit sha")
                continue
            env["overrides"][name] = {"pin_file_sha": spec["sha"], "run_sha": override}
            spec["sha"] = override
        elif spec["sha"] is None:
            env["pending"].append(name)
            env["problems"].append(f"{name}: pin is PENDING in the pin file; name the revision under test with {spec['rev_env']}")
    env["cp_revision_override"] = env["overrides"].get("control_plane")
    env["pins"] = {k: v["sha"] for k, v in comps.items()}
    comps = {k: v for k, v in comps.items() if v["sha"] is not None}
    pins_match, pristine = True, True
    heads = {}
    from pristine_checkout import require_pristine
    for name, spec in comps.items():
        raw = os.environ.get(spec["env"])
        if not raw:
            env["problems"].append(f"{spec['env']} not set")
            pins_match = pristine = False
            continue
        path = Path(raw).resolve()
        env["dirs"][name] = str(path)
        try:
            heads[name] = _git(path, "rev-parse", "HEAD")
        except Exception as exc:  # noqa: BLE001
            env["problems"].append(f"{name}: not a git checkout ({type(exc).__name__})")
            pins_match = pristine = False
            continue
        if heads[name] != spec["sha"]:
            env["problems"].append(f"{name}: HEAD {heads[name]} != pin {spec['sha']}")
            pins_match = False
            continue
        try:
            require_pristine(path, spec["sha"], name)
        except ValueError as exc:
            env["problems"].append(str(exc))
            pristine = False
    env["heads"] = heads
    env["pins_match"], env["pristine"] = pins_match, pristine
    import importlib.metadata
    try:
        import pydantic
        parts = pydantic.VERSION.split(".")
        env["pydantic_version"] = pydantic.VERSION
        env["pydantic_ok"] = (int(parts[0]), int(parts[1])) >= (2, 12)
        env["pydantic_file"] = pydantic.__file__
    except Exception as exc:  # noqa: BLE001
        env["pydantic_version"], env["pydantic_ok"] = f"unavailable: {type(exc).__name__}", False
    if not env["pydantic_ok"]:
        env["problems"].append(f"pydantic {env['pydantic_version']} (>=2.12 required)")
    env["python"] = sys.version
    env["platform"] = sys.platform
    env["uid"] = os.getuid() if hasattr(os, "getuid") else None
    env["modules_from_pinned_trees"] = False
    if pins_match and pristine and not env["problems"]:
        for name in _WIRE_ORDER:
            sub = SRC_SUBDIR[name]
            root = Path(env["dirs"][name])
            entries = [root / sub] + ([root] if name == "control_plane" else [])
            for entry in reversed(entries):
                sys.path.insert(0, str(entry))
        env["wired"] = True
        _declare_replay_distribution(env)
        env["modules_from_pinned_trees"] = _modules_ok(env) and env.get("replay_distribution_ok", False)
        if not env["modules_from_pinned_trees"]:
            env["problems"].append("a component module or the Replay distribution is not the pinned tree: " + json.dumps({k: env.get(k) for k in ("module_files", "replay_distribution_path", "replay_revision_seen_by_evidence_pack", "replay_code_problem", "replay_distribution_error")}))
    env["verifier_src"] = str(Path(env["dirs"]["verifier"]) / "src") if "verifier" in env["dirs"] else None
    _state.OBS["env"] = {k: env.get(k) for k in (
        "status", "pins", "heads", "dirs", "pins_match", "pristine", "pydantic_version", "pydantic_ok", "pydantic_file", "python", "platform", "uid",
        "modules_from_pinned_trees", "module_files", "replay_distribution_path", "replay_revision_seen_by_evidence_pack", "replay_code_problem", "replay_distribution_ok", "replay_distribution_error", "pin_file", "pin_file_sha256", "cp_revision_override", "overrides", "pending", "problems")}
    _state.OBS["env"]["status"] = "ran"


def _declare_replay_distribution(env) -> None:
    """The Evidence Pack trusts the Replay revision recorded by the INSTALLED ``agent-replay-bundle`` distribution (PEP 610).

    No venv is created here. A dist-info for the pinned Replay checkout is written to a temporary directory placed first on
    sys.path, with the same ``direct_url.json`` an editable local-directory install records (dir_info, file URL). The Evidence
    Pack then resolves the revision as the git HEAD of that clean checkout. A different installed distribution (for example a stale
    editable install in the interpreter) is shadowed, and the revision the Evidence Pack resolves is recorded and must equal the pin.
    """
    import importlib.metadata
    import tempfile
    root = Path(env["dirs"]["replay"])
    site = Path(tempfile.mkdtemp(prefix="mvp-replay-dist-"))
    dist = site / "agent_replay_bundle-0.0.0+mvpchain.dist-info"
    dist.mkdir()
    (dist / "METADATA").write_text("Metadata-Version: 2.1\nName: agent-replay-bundle\nVersion: 0.0.0+mvpchain\n")
    (dist / "direct_url.json").write_text(json.dumps({"url": root.as_uri(), "dir_info": {"editable": True}}))
    (dist / "RECORD").write_text("")
    sys.path.insert(0, str(site))
    env["replay_distribution_site"] = str(site)
    try:
        found = importlib.metadata.distribution("agent-replay-bundle")
        env["replay_distribution_path"] = str(found._path)
        import agent_governance_evidence_pack.importer as imp
        env["replay_revision_seen_by_evidence_pack"] = imp._installed_replay_revision()
        env["replay_code_problem"] = imp._imported_replay_code_problem()
        env["replay_distribution_ok"] = (Path(found._path) == dist and env["replay_revision_seen_by_evidence_pack"] == env["pins"]["replay"]
                                         and env["replay_code_problem"] is None)
    except Exception as exc:  # noqa: BLE001
        env["replay_distribution_ok"] = False
        env["replay_distribution_error"] = f"{type(exc).__name__}: {exc}"


def _modules_ok(env) -> bool:
    import importlib
    wanted = {"agent_control_plane": "control_plane", "tests": "control_plane", "engine": "runtime",
              "agent_replay_bundle": "replay", "agent_governance_evidence_pack": "evidence_pack"}
    files, ok = {}, True
    for module, comp in wanted.items():
        try:
            mod = importlib.import_module(module + (".test_runtime_authority" if module == "tests" else ""))
            f = Path(mod.__file__).resolve()
            files[module] = str(f)
            ok = ok and Path(env["dirs"][comp]) in f.parents
        except Exception as exc:  # noqa: BLE001
            files[module] = f"import failed: {type(exc).__name__}: {exc}"
            ok = False
    env["module_files"] = files
    return ok


try:
    _wire()
except Exception as _exc:  # noqa: BLE001  (a wiring bug is a problem for every test, never a skip)
    _state.ENV["problems"].append(f"wiring error: {type(_exc).__name__}: {_exc}")
    _state.OBS.setdefault("env", {"status": "ran", "problems": _state.ENV["problems"], "pins_match": False, "pristine": False,
                                  "modules_from_pinned_trees": False, "pydantic_ok": False})


@pytest.fixture(autouse=True)
def _components_present():
    if _state.ENV["problems"]:
        pytest.fail("mvp-chain cannot run against the components: " + "; ".join(_state.ENV["problems"]))


def pytest_sessionfinish(session, exitstatus):
    out = _state.results_dir()
    exp_path = expectations_file()
    exp_bytes = exp_path.read_bytes()
    expectations = json.loads(exp_bytes)
    _state.OBS["run"] = {"run_id": os.environ.get("MVP_RUN_ID")}
    obs_bytes = json.dumps(_state.OBS, indent=2, sort_keys=True, default=str).encode() + b"\n"
    (out / "observations.json").write_bytes(obs_bytes)
    results = verdict.evaluate_all(expectations, _state.OBS)
    document = {
        "schema": "cognous.mvp-chain-results/1",
        "acceptance_declared": False,
        "run_id": os.environ.get("MVP_RUN_ID"),
        "note": "Raw observations plus statuses computed only from the proposed expectations file. Not an acceptance, not a release decision; production HOLD unchanged.",
        "expectations_file": str(exp_path),
        "expectations_sha256": hashlib.sha256(exp_bytes).hexdigest(),
        "expectations_git_blob": subprocess.run(["git", "hash-object", str(exp_path)], capture_output=True, text=True).stdout.strip(),
        "observations_sha256": hashlib.sha256(obs_bytes).hexdigest(),
        "pytest_exit_status": int(exitstatus),
        "tuple": {"pins": _state.ENV.get("pins"), "heads": _state.ENV.get("heads"), "cp_revision_override": _state.ENV.get("cp_revision_override"), "overrides": _state.ENV.get("overrides"),
                  "pin_file_sha256": _state.ENV.get("pin_file_sha256")},
        "counts": verdict.counts(results),
        "rows": results,
    }
    (out / "results.json").write_text(json.dumps(document, indent=2, sort_keys=True, default=str) + "\n")
    print(f"\nmvp-chain results: {out / 'results.json'}  counts={document['counts']}")
