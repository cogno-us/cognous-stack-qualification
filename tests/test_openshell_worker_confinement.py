# SPDX-License-Identifier: Apache-2.0
"""The packaged-worker qualification runs the worker under restricted container options.

No container daemon is needed: subprocess.run is replaced and the generated
argv is inspected. The tool imports runtime modules that live in the component
checkout, so minimal stand-ins are registered while the tool is loaded.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "suites/cognous-execution-runtime/tools/openshell_image_qualification.py"
IMAGE = "example/worker:test"


@pytest.fixture()
def tool(monkeypatch):
    engine = types.ModuleType("engine")
    env = types.ModuleType("engine.openshell_environment")
    env.OpenShellRefundDestination = type("OpenShellRefundDestination", (), {})
    safe = types.ModuleType("engine.safe_executor")
    safe.EXECUTION_ENVELOPE_VERSION = "0.1.0"
    for name in ("ExecutionEnvelope", "ExecutionOperation", "commitment", "snapshot_envelope"):
        setattr(safe, name, object)
    for name, mod in (("engine", engine), ("engine.openshell_environment", env), ("engine.safe_executor", safe)):
        monkeypatch.setitem(sys.modules, name, mod)
    spec = importlib.util.spec_from_file_location("r3b_openshell_image_qualification", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _capture(monkeypatch, tool, *, stdout="", returncode=0):
    calls: list[list[str]] = []

    def fake_run(argv, **kwargs):
        calls.append(list(argv))
        return subprocess.CompletedProcess(argv, returncode, stdout=stdout, stderr="")

    monkeypatch.setattr(tool.subprocess, "run", fake_run)
    return calls


def _before_image(argv):
    return argv[: argv.index(IMAGE)]


def _pairs(argv):
    return list(zip(argv, argv[1:]))


def test_run_command_drops_capabilities_and_privilege_escalation(tool, monkeypatch, tmp_path):
    calls = _capture(monkeypatch, tool)
    tool._docker(IMAGE, tmp_path, ["/bin/true"])
    opts = _before_image(calls[0])
    assert ("--cap-drop", "ALL") in _pairs(opts)
    assert ("--security-opt", "no-new-privileges") in _pairs(opts)


def test_run_command_has_read_only_root_with_writable_state_and_scratch(tool, monkeypatch, tmp_path):
    calls = _capture(monkeypatch, tool)
    tool._docker(IMAGE, tmp_path, ["/bin/true"])
    opts = _before_image(calls[0])
    assert "--read-only" in opts
    mounts = [value for flag, value in _pairs(opts) if flag == "--mount"]
    assert mounts == [f"type=bind,src={tmp_path},dst=/var/lib/cognous"]
    assert "readonly" not in mounts[0] and "ro" not in mounts[0].split(",")
    assert any(flag == "--tmpfs" and value.split(":")[0] == "/tmp" for flag, value in _pairs(opts))


def test_run_command_limits_memory_processes_and_network(tool, monkeypatch, tmp_path):
    calls = _capture(monkeypatch, tool)
    tool._docker(IMAGE, tmp_path, ["/bin/true"])
    pairs = dict(_pairs(_before_image(calls[0])))
    assert pairs["--network"] == "none"
    assert pairs["--memory"].rstrip("mMgG").isdigit() and int(pairs["--memory"].rstrip("mMgG")) > 0
    assert 0 < int(pairs["--pids-limit"]) <= 1024


def test_stdin_and_user_options_still_present_when_restricted(tool, monkeypatch, tmp_path):
    calls = _capture(monkeypatch, tool)
    tool._docker(IMAGE, tmp_path, ["/bin/true"], stdin="{}", user="1000:1000")
    opts = _before_image(calls[0])
    assert "-i" in opts
    assert ("--user", "1000:1000") in _pairs(opts)
    assert ("--cap-drop", "ALL") in _pairs(opts)
    assert calls[0][calls[0].index(IMAGE):] == [IMAGE, "/bin/true"]


def test_worker_invocation_is_restricted(tool, monkeypatch, tmp_path):
    calls = _capture(monkeypatch, tool)
    tool._worker(IMAGE, tmp_path, {"version": "0.1.0"})
    opts = _before_image(calls[0])
    for needed in ("--read-only",):
        assert needed in opts
    assert ("--network", "none") in _pairs(opts)
    assert calls[0][calls[0].index(IMAGE):][:3] == [IMAGE, "/usr/local/bin/python3", "-I"]


def test_packaging_checks_keep_code_path_check_meaningful(tool, monkeypatch, tmp_path):
    """Only the code-path write check may run without --read-only; it must still be
    able to fail for the right reason (file permissions), not an empty root mount."""
    seen: list[list[str]] = []

    def fake_run(argv, **kwargs):
        seen.append(list(argv))
        cmd = argv[argv.index(IMAGE) + 1:]
        if cmd[:2] == ["/usr/bin/id", "-u"] or cmd[:2] == ["/usr/bin/id", "-g"]:
            return subprocess.CompletedProcess(argv, 0, stdout="1000\n", stderr="")
        if any("should-not-write" in part for part in cmd):
            return subprocess.CompletedProcess(argv, 1, stdout="", stderr="denied")
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr(tool.subprocess, "run", fake_run)
    tool._packaging_checks(IMAGE, tmp_path)
    unrestricted = [a for a in seen if "--read-only" not in a]
    assert len(unrestricted) == 1 and any("should-not-write" in p for p in unrestricted[0])
    for argv in seen:
        opts = _before_image(argv)
        assert ("--cap-drop", "ALL") in _pairs(opts)
        assert ("--security-opt", "no-new-privileges") in _pairs(opts)
        assert ("--network", "none") in _pairs(opts)
        assert "--memory" in opts and "--pids-limit" in opts
