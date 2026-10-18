"""Governed exchange probes (PROBE2_EXCHANGE_DIR): the strict source check of the executor runtime loader.

The loader verifies the named entry modules of the pinned dependency checkouts against their revision before importing them. A
module those entries import is also code that runs, so a tracked sibling module whose content differs from the revision must be
refused as well, including when the working-tree flag that hides modifications from ``git status`` is set on it. The dependency
checkouts here are throw-away repositories, as in the exchange's own component-local tests; the clean checkout is the control.
"""
import subprocess
import sys
from pathlib import Path

import pytest

from _support import pending
from conftest import checkout

MODULES = {
    "control_plane": ("src/agent_control_plane", "bounded"),
    "runtime": ("engine", "producer_contract"),
    "replay": ("src/agent_replay_bundle", "importers"),
    "odes": ("src/odes", "exporter"),
    "pack": ("src/agent_governance_evidence_pack", "importer"),
}
TOP_LEVEL = ("agent_control_plane", "engine", "agent_replay_bundle", "odes", "agent_governance_evidence_pack")
SIBLING = "src/agent_replay_bundle/helper_module.py"


@pytest.fixture(autouse=True)
def _pin():
    checkout("PROBE2_EXCHANGE_DIR")


def git(path, *args):
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def repo(path, files):
    for name, text in files.items():
        target = path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    git(path.parent, "init", "-q", str(path))
    git(path, "add", "-A")
    git(path, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "fixture")
    return git(path, "rev-parse", "HEAD")


def modified_source(marker):
    return f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran')\nVALUE = 2\n"


def runtime_module():
    from experiments.odex_gax_imx_reference import gax_ref_runtime
    return gax_ref_runtime


@pytest.fixture(params=["typed-refusal-candidate-20261015"])
def checkouts(request, tmp_path, monkeypatch):
    runtime = runtime_module()
    marker = tmp_path / "modified-code-executed"
    roots, revisions = {}, {}
    for key, (package, module) in MODULES.items():
        body = "import colorsys\nVALUE = 1\n"
        files = {f"{package}/__init__.py": "", f"{package}/{module}.py": body}
        if key == "replay":
            files[f"{package}/{module}.py"] = "from . import helper_module\n" + body
            files[SIBLING] = "VALUE = 1\n"
        if key == "runtime":
            body += ("EXECUTOR_PRODUCER_PROFILE_ID = 'urn:cognous:profiles:moltbot-safe-executor-producer'\n"
                     "EXECUTOR_PRODUCER_PROFILE_VERSION = '2.0.0'\n"
                     "PinnedControlPlaneExecutor = DurableRefundDestination = ExecutionEnvelope = None\n"
                     "ExecutionOperation = LocalExecutionPolicy = commitment = export_execution_artifacts = None\n")
            files[f"{package}/{module}.py"] = body
        roots[key] = tmp_path / key
        revisions[key] = repo(roots[key], files)
    manifest_root = tmp_path / "manifest"
    revisions["manifest"] = repo(manifest_root, {"examples/m.json": "{}"})
    for key in ("replay", "odes", "pack"):
        monkeypatch.syspath_prepend(str(roots[key] / "src"))
    monkeypatch.setattr(sys, "path", list(sys.path))
    for name in [m for m in sys.modules if m.split(".")[0] in TOP_LEVEL]:
        monkeypatch.delitem(sys.modules, name)
    monkeypatch.setattr(runtime, "RUNTIME_COMPATIBILITY_PROFILE", request.param)
    for attr, key in (("CP_REVISION", "control_plane"), ("MOLTBOT_REVISION", "runtime"), ("REPLAY_REVISION", "replay"),
                      ("ODES_REVISION", "odes"), ("EVIDENCE_PACK_REVISION", "pack"), ("MANIFEST_REVISION", "manifest")):
        monkeypatch.setattr(runtime, attr, revisions[key])
    monkeypatch.setenv("MOLTBOT_SAFE_CONTROL_PLANE_ROOT", str(roots["control_plane"]))
    monkeypatch.setenv("MOLTBOT_SAFE_ROOT", str(roots["runtime"]))
    monkeypatch.setenv("UPSTREAM_MANIFEST_EXAMPLE", str(manifest_root / "examples/m.json"))
    yield runtime, roots, marker
    for name in [m for m in sys.modules if m.split(".")[0] in TOP_LEVEL]:
        sys.modules.pop(name, None)


def test_clean_checkouts_with_a_sibling_module_load(checkouts):
    runtime, roots, marker = checkouts
    loaded = runtime.load_executor_runtime()
    assert Path(loaded["producer"].__file__).resolve() == (roots["runtime"] / "engine/producer_contract.py").resolve()
    assert not marker.exists()


def test_modified_entry_module_with_hidden_flag_is_refused(checkouts):
    runtime, roots, marker = checkouts
    target = "src/agent_replay_bundle/importers.py"
    git(roots["replay"], "update-index", "--assume-unchanged", target)
    (roots["replay"] / target).write_text(modified_source(marker))
    with pytest.raises(RuntimeError, match="candidate source identity mismatch"):
        runtime.load_executor_runtime()
    assert not marker.exists()


def test_modified_sibling_module_without_hidden_flag_is_refused(checkouts):
    runtime, roots, marker = checkouts
    (roots["replay"] / SIBLING).write_text(modified_source(marker))
    with pytest.raises(RuntimeError, match="candidate source identity mismatch"):
        runtime.load_executor_runtime()
    assert not marker.exists()


@pending()
def test_modified_sibling_module_with_hidden_flag_is_refused_before_it_runs(checkouts):
    runtime, roots, marker = checkouts
    git(roots["replay"], "update-index", "--assume-unchanged", SIBLING)
    (roots["replay"] / SIBLING).write_text(modified_source(marker))
    assert git(roots["replay"], "status", "--porcelain", "--untracked-files=no") == ""
    with pytest.raises(RuntimeError, match="candidate source identity mismatch"):
        runtime.load_executor_runtime()
    assert not marker.exists()
