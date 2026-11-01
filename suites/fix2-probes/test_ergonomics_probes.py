"""Ergonomics probes (PROBE2_ERGONOMICS_DIR): the diagnostics file of the CI entry and of the composite action helper.

The output directory of a CI run holds a file named ``ci-diagnostics.json``. When that name is already a symbolic link, a run must
not write through it to the link target and must not leave the link in the directory that is uploaded afterwards. The controls run
the same commands with a regular output directory and check that the file is written as before.
"""
import contextlib
import importlib.util
import io
import json
import os
import sys
from pathlib import Path

import pytest

from conftest import checkout


@pytest.fixture(autouse=True)
def _pin():
    checkout("PROBE2_ERGONOMICS_DIR")


def _modules():
    from cognous_ocs import __version__, ci, fixtures_data, scaffold, validate
    from cognous_ocs.cli import Outcome, main
    from cognous_ocs.doctor import FAILED, OK, Check
    from cognous_ocs.envelope import Result
    return dict(version=__version__, ci=ci, fixtures=fixtures_data, scaffold=scaffold, validate=validate, Outcome=Outcome,
                main=main, FAILED=FAILED, OK=OK, Check=Check, Result=Result)


@pytest.fixture
def space(tmp_path, monkeypatch):
    m = _modules()
    sys.dont_write_bytecode = True
    work = tmp_path / "ws"
    (work / "wf").mkdir(parents=True)
    for name, content in m["scaffold"].managed_bytes().items():
        (work / "wf" / name).write_bytes(content)
    (work / "pack.json").write_bytes(m["fixtures"].read_fixture("evidence-pack.json"))
    (work / "manifest.json").write_bytes(m["fixtures"].read_fixture("manifest.json"))
    (work / "other-file.txt").write_text("KEEP\n")
    monkeypatch.chdir(work)
    return work


def scripted(monkeypatch, outcome):
    """Replace the component-backed checks with one scripted outcome (as the package's own CI tests do)."""
    m = _modules()
    codes = {"pass": 0, "invalid": 2, "fail": 1, "review": 0}
    src = {"component": "action-manifest", "contract": "action-manifest", "contract_version": "1.0.0"}

    def run_validate(path, kind, **_):
        return m["Outcome"](m["Result"]("validate", outcome, [] if outcome == "pass" else ["OCS_INPUT_INVALID"],
                                        {"kind": kind, "path": path, "exit": codes[outcome]}, verdict_source=src,
                                        does_not_prove=["x"], messages=["m"]))

    monkeypatch.setattr(m["validate"], "run_validate", run_validate)
    monkeypatch.setattr(m["ci"], "run_checks", lambda workflow, **_: [m["Check"]("OCS_PATHS", m["OK"], "msg", "act")])


def ci_run(argv):
    m = _modules()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        return m["main"](["ci", "--out", "o", "--format", "json", *argv])


def plant(work):
    (work / "o").mkdir()
    os.symlink(work / "other-file.txt", work / "o" / "ci-diagnostics.json")


def leaf_is_link(work):
    return (work / "o" / "ci-diagnostics.json").is_symlink()


# the three outcomes of the CI entry: refusal (2), strict review failure (1), success (0)
RUNS = {
    "refusal": ([], None, 2),
    "strict-review-failure": (["--workflow", "wf", "--non-assurance", "--strict"], "review", 1),
    "success": (["--workflow", "wf", "--non-assurance", "--expect-version", "@version"], "pass", 0),
}


def argv_of(spec):
    m = _modules()
    return [m["version"] if a == "@version" else a for a in spec]


@pytest.mark.parametrize("name", RUNS)
def test_regular_output_directory_gets_diagnostics_only_when_the_run_fails(space, monkeypatch, name):
    argv, outcome, expected = RUNS[name]
    if outcome:
        scripted(monkeypatch, outcome)
    assert ci_run(argv_of(argv)) == expected
    target = space / "o" / "ci-diagnostics.json"
    if expected == 0:
        assert not target.exists()
    else:
        assert not target.is_symlink()
        assert json.loads(target.read_text())["exit_code"] == expected
    assert (space / "other-file.txt").read_text() == "KEEP\n"


@pytest.mark.parametrize("name", list(RUNS))
def test_diagnostics_link_target_is_left_unchanged(space, monkeypatch, name):
    argv, outcome, expected = RUNS[name]
    if outcome:
        scripted(monkeypatch, outcome)
    plant(space)
    assert ci_run(argv_of(argv)) == expected
    assert (space / "other-file.txt").read_text() == "KEEP\n"


@pytest.mark.parametrize("name", list(RUNS))
def test_no_diagnostics_link_remains_in_the_output_directory(space, monkeypatch, name):
    argv, outcome, expected = RUNS[name]
    if outcome:
        scripted(monkeypatch, outcome)
    plant(space)
    assert ci_run(argv_of(argv)) == expected
    assert not leaf_is_link(space)


def _load_action_helper():
    path = Path(checkout("PROBE2_ERGONOMICS_DIR")) / ".github" / "actions" / "ocs" / "confine_inputs.py"
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("probe2_confine_inputs", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["probe2_confine_inputs"] = module
    spec.loader.exec_module(module)
    return module


def action_env(work):
    return {"GITHUB_WORKSPACE": str(work), "OCS_IN_OUT_DIR": "o", "OCS_IN_WORKFLOW": "wf"}  # no mode chosen: refused


def test_action_helper_writes_diagnostics_into_a_regular_directory(space):
    helper = _load_action_helper()
    with contextlib.redirect_stderr(io.StringIO()):
        assert helper.main(action_env(space)) == 2
    assert json.loads((space / "o" / "ci-diagnostics.json").read_text())["exit_code"] == 2
    assert (space / "other-file.txt").read_text() == "KEEP\n"


def test_action_helper_does_not_write_through_a_diagnostics_link(space):
    helper = _load_action_helper()
    plant(space)
    with contextlib.redirect_stderr(io.StringIO()):
        assert helper.main(action_env(space)) == 2
    assert (space / "other-file.txt").read_text() == "KEEP\n"
    assert not leaf_is_link(space)
