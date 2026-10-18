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
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "suites/cognous-execution-runtime/tools/openshell_image_qualification.py"
IMAGE = "example/worker:test"


def _load_tool():
    engine = types.ModuleType("engine")
    env = types.ModuleType("engine.openshell_environment")
    env.OpenShellRefundDestination = type("OpenShellRefundDestination", (), {})
    safe = types.ModuleType("engine.safe_executor")
    safe.EXECUTION_ENVELOPE_VERSION = "0.1.0"
    for name in ("ExecutionEnvelope", "ExecutionOperation", "commitment", "snapshot_envelope"):
        setattr(safe, name, object)
    stubs = {"engine": engine, "engine.openshell_environment": env, "engine.safe_executor": safe}
    with mock.patch.dict(sys.modules, stubs):
        spec = importlib.util.spec_from_file_location("r3b_openshell_image_qualification", TOOL)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


def _before_image(argv):
    return argv[: argv.index(IMAGE)]


def _pairs(argv):
    return list(zip(argv, argv[1:]))


class WorkerConfinementTests(unittest.TestCase):
    def setUp(self):
        self.tool = _load_tool()
        self.state = Path("/state/under/test")
        self.calls: list[list[str]] = []

        def fake_run(argv, **kwargs):
            self.calls.append(list(argv))
            return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

        patcher = mock.patch.object(self.tool.subprocess, "run", fake_run)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_run_command_drops_capabilities_and_privilege_escalation(self):
        self.tool._docker(IMAGE, self.state, ["/bin/true"])
        opts = _before_image(self.calls[0])
        self.assertIn(("--cap-drop", "ALL"), _pairs(opts))
        self.assertIn(("--security-opt", "no-new-privileges"), _pairs(opts))

    def test_run_command_has_read_only_root_with_writable_state_and_scratch(self):
        self.tool._docker(IMAGE, self.state, ["/bin/true"])
        opts = _before_image(self.calls[0])
        self.assertIn("--read-only", opts)
        mounts = [value for flag, value in _pairs(opts) if flag == "--mount"]
        self.assertEqual(mounts, [f"type=bind,src={self.state},dst=/var/lib/cognous"])
        self.assertNotIn("readonly", mounts[0])
        self.assertNotIn("ro", mounts[0].split(","))
        self.assertTrue(any(flag == "--tmpfs" and value.split(":")[0] == "/tmp" for flag, value in _pairs(opts)))

    def test_run_command_limits_memory_processes_and_network(self):
        self.tool._docker(IMAGE, self.state, ["/bin/true"])
        pairs = dict(_pairs(_before_image(self.calls[0])))
        self.assertEqual(pairs["--network"], "none")
        memory = pairs["--memory"].rstrip("mMgG")
        self.assertTrue(memory.isdigit() and int(memory) > 0)
        self.assertTrue(0 < int(pairs["--pids-limit"]) <= 1024)

    def test_stdin_and_user_options_still_present_when_restricted(self):
        self.tool._docker(IMAGE, self.state, ["/bin/true"], stdin="{}", user="1000:1000")
        argv = self.calls[0]
        opts = _before_image(argv)
        self.assertIn("-i", opts)
        self.assertIn(("--user", "1000:1000"), _pairs(opts))
        self.assertIn(("--cap-drop", "ALL"), _pairs(opts))
        self.assertEqual(argv[argv.index(IMAGE):], [IMAGE, "/bin/true"])

    def test_worker_invocation_is_restricted(self):
        self.tool._worker(IMAGE, self.state, {"version": "0.1.0"})
        argv = self.calls[0]
        opts = _before_image(argv)
        self.assertIn("--read-only", opts)
        self.assertIn(("--network", "none"), _pairs(opts))
        self.assertEqual(argv[argv.index(IMAGE):][:3], [IMAGE, "/usr/local/bin/python3", "-I"])

    def test_packaging_checks_keep_code_path_check_meaningful(self):
        """Only the code-path write check may run without --read-only; it must still be
        able to fail for the right reason (file permissions), not an empty root mount."""
        seen: list[list[str]] = []

        def fake_run(argv, **kwargs):
            seen.append(list(argv))
            cmd = argv[argv.index(IMAGE) + 1:]
            if cmd[:2] in (["/usr/bin/id", "-u"], ["/usr/bin/id", "-g"]):
                return subprocess.CompletedProcess(argv, 0, stdout="1000\n", stderr="")
            if any("should-not-write" in part for part in cmd):
                return subprocess.CompletedProcess(argv, 1, stdout="", stderr="denied")
            return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

        with mock.patch.object(self.tool.subprocess, "run", fake_run):
            self.tool._packaging_checks(IMAGE, self.state)
        unrestricted = [a for a in seen if "--read-only" not in a]
        self.assertEqual(len(unrestricted), 1)
        self.assertTrue(any("should-not-write" in p for p in unrestricted[0]))
        for argv in seen:
            opts = _before_image(argv)
            self.assertIn(("--cap-drop", "ALL"), _pairs(opts))
            self.assertIn(("--security-opt", "no-new-privileges"), _pairs(opts))
            self.assertIn(("--network", "none"), _pairs(opts))
            self.assertIn("--memory", opts)
            self.assertIn("--pids-limit", opts)


if __name__ == "__main__":
    unittest.main()
