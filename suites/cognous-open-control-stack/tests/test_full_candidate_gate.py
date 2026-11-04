import copy
import pytest
from tools.aggregate_full_candidate import validate_reports
from tools.reference_release import BATCHES


def reports():
    result=[]
    for batch,names in BATCHES.items():
        r={'batch':batch,'profile_sha256':'exact','passed':True,'suite_runs':[{'suite':n,'repetition':rep,'returncode':0} for n in names for rep in (1,2)],'extra':[]}
        if batch=='exchange':r.update(representative_repeatable=True,representative_runs=[{'returncode':0},{'returncode':0}])
        if batch=='authority':r['extra']=[{'returncode':0}]
        if batch=='registry':
            # Current OCS scope: TFA is the only optional static check (PRP and
            # Research Intelligence are retired and not evaluated).
            r['extra']=[{'returncode':0,'scope':'static JSON only'}]
            r['suite_runs'] += [{'suite':'index_local_chain','repetition':rep,'returncode':0} for rep in (1,2)]
        result.append(r)
    return result


def test_complete_reports_pass():validate_reports(reports(),'exact')


@pytest.mark.parametrize('mutation',['missing','duplicate','digest','failed','repetition','transport','mock','registry'])
def test_incomplete_batch_cannot_pass(mutation):
    data=reports()
    if mutation=='missing':data.pop()
    elif mutation=='duplicate':data[-1]=copy.deepcopy(data[0])
    elif mutation=='digest':data[0]['profile_sha256']='different'
    elif mutation=='failed':data[0]['passed']=False
    elif mutation=='repetition':data[0]['suite_runs'].pop()
    elif mutation=='transport':next(r for r in data if r['batch']=='exchange')['representative_repeatable']=False
    elif mutation=='mock':next(r for r in data if r['batch']=='authority')['extra']=[]
    elif mutation=='registry':next(r for r in data if r['batch']=='registry')['suite_runs'].pop()
    with pytest.raises(ValueError, match='Index chain evidence missing' if mutation=='registry' else None):validate_reports(data,'exact')


def test_historical_green_reports_do_not_qualify_refusal_candidate():
    with pytest.raises(ValueError, match="missing suite repetition"):
        validate_reports(reports(), 'exact', {'runtime_profile':'typed-refusal-candidate-20261015'})


@pytest.mark.parametrize('missing', ['executor_refusal','gax_refusal','gax_historical_artifacts','replay_refusal','odes_refusal','evidence_pack_refusal'])
def test_each_current_generation_suite_is_mandatory(missing):
    from tools.reference_release import CANDIDATE_SUITES
    data=reports()
    for report in data:
        report['suite_runs'] += [{'suite':name,'repetition':rep,'returncode':0}
            for name in CANDIDATE_SUITES[report['batch']] for rep in (1,2)]
    profile={'runtime_profile':'typed-refusal-candidate-20261015'}
    validate_reports(data, 'exact', profile)
    for report in data:
        report['suite_runs']=[run for run in report['suite_runs']
            if (run['suite'],run['repetition']) != (missing,2)]
    with pytest.raises(ValueError, match="missing suite repetition"):
        validate_reports(data, 'exact', profile)


def _registry(data):
    return next(r for r in data if r['batch']=='registry')


def test_registry_fixture_carries_exactly_current_tfa_static_evidence():
    assert _registry(reports())['extra']==[{'returncode':0,'scope':'static JSON only'}]


def test_missing_current_tfa_static_evidence_is_rejected():
    data=reports()
    _registry(data)['extra']=[]
    with pytest.raises(ValueError, match='current OCS optional static evidence'):validate_reports(data,'exact')


def test_failed_current_tfa_static_evidence_is_rejected():
    data=reports()
    _registry(data)['extra'][0]['returncode']=1
    with pytest.raises(ValueError, match='current OCS optional static evidence'):validate_reports(data,'exact')


def test_historical_three_entry_static_shape_is_not_current_evidence():
    # The pre-scope-change shape (TFA + retired PRP + Research Intelligence)
    # must not be silently accepted as if it were current evidence.
    data=reports()
    _registry(data)['extra']=[{'returncode':0} for _ in range(3)]
    with pytest.raises(ValueError, match='current OCS optional static evidence'):validate_reports(data,'exact')


@pytest.mark.parametrize('retired_state',['absent','present_passing','present_failing'])
def test_retired_prp_research_intelligence_evidence_is_not_required_or_decisive(retired_state):
    # Retired components are historical provenance only: their metadata, if a
    # report carries it, never becomes a requirement and cannot flip the verdict.
    data=reports()
    if retired_state!='absent':
        code=0 if retired_state=='present_passing' else 1
        _registry(data)['historical_non_ocs_static']={name:{'returncode':code} for name in ('prp','research_intelligence')}
    validate_reports(data,'exact')


def test_retired_components_are_not_required_batch_suites():
    from tools.reference_release import BATCHES, NON_OCS_COMPONENTS
    assert NON_OCS_COMPONENTS=={'prp','research_intelligence'}
    assert not set().union(*BATCHES.values()) & NON_OCS_COMPONENTS


# --- Isolated-import environment for the focused Replay/ODES preflight --------------------------------------
# Replay/ODES tests spawn ``python -I`` children, which ignore PYTHONPATH. The runner used to provide those
# components through PYTHONPATH only, so every such child raised ModuleNotFoundError. The fakes below are tiny
# git checkouts with a self-contained PEP 660 backend, so these tests need no network, setuptools or wheel.
import inspect
import json
import subprocess
import sys
from pathlib import Path
from tools import reference_release as rr

_BACKEND = '''
import base64, hashlib, zipfile
from pathlib import Path
NAME, MODULE, FAIL, TARGET, DIRTY, REQUIRES = %r, %r, %r, %r, %r, %r
def get_requires_for_build_editable(config_settings=None):
    return []
def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    if FAIL:
        raise RuntimeError("simulated build failure")
    root = Path(__file__).resolve().parent
    if DIRTY:
        (root / "build-output.txt").write_text("generated inside the pinned checkout\\n")
    stem = NAME.replace("-", "_") + "-0.2.0"
    files = {
        "__editable__." + NAME.replace("-", "_") + ".pth": str(TARGET or root / "src") + "\\n",
        stem + ".dist-info/METADATA": "Metadata-Version: 2.1\\nName: %%s\\nVersion: 0.2.0\\n" %% NAME + ("Requires-Dist: %%s\\n" %% REQUIRES if REQUIRES else ""),
        stem + ".dist-info/WHEEL": "Wheel-Version: 1.0\\nGenerator: fake\\nRoot-Is-Purelib: true\\nTag: py3-none-any\\n",
    }
    record = "".join("%%s,,\\n" %% name for name in [*files, stem + ".dist-info/RECORD"])
    files[stem + ".dist-info/RECORD"] = record
    wheel = Path(wheel_directory) / (stem + "-py3-none-any.whl")
    with zipfile.ZipFile(wheel, "w") as z:
        for name, text in files.items():
            z.writestr(name, text)
    return wheel.name
'''


def _git(path, *args):
    return subprocess.check_output(["git", "-C", str(path), "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args], text=True).strip()


def _fake_checkout(root, name, dist, module, *, fail=False, marker="pinned", target=None, dirty=False, requires=None):
    path = root / name
    (path / "src" / module).mkdir(parents=True)
    (path / "src" / module / "__init__.py").write_text("MARKER = %r\n" % marker)
    (path / "_fake_backend.py").write_text(_BACKEND % (dist, module, fail, None if target is None else str(target), dirty, requires))
    (path / "pyproject.toml").write_text('[build-system]\nrequires = []\nbuild-backend = "_fake_backend"\nbackend-path = ["."]\n')
    subprocess.check_call(["git", "init", "-q", str(path)])
    _git(path, "add", "-A")
    _git(path, "commit", "-q", "-m", "fake")
    return path, _git(path, "rev-parse", "HEAD")


def _fakes(root, **kw):
    checkouts, pins = {}, {}
    for component, dist, module in rr.ISOLATED_IMPORT_PACKAGES:
        checkouts[component], pins[component] = _fake_checkout(root, component, dist, module, **kw)
    return checkouts, pins


def _isolated(python, code, **env):
    return subprocess.run([python, "-I", "-B", "-c", code], capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", **env})


@pytest.fixture(scope="module")
def provisioned(tmp_path_factory):
    root = tmp_path_factory.mktemp("isolated-import")
    checkouts, pins = _fakes(root)
    python, records = rr.provision_isolated_import_environment(root / "venv", checkouts, pins)
    return root, checkouts, pins, python, records


def test_isolated_children_import_the_pinned_replay_and_odes_sources(provisioned):
    _root, checkouts, _pins, python, _records = provisioned
    for component, dist, module in rr.ISOLATED_IMPORT_PACKAGES:
        child = _isolated(python, "import %s as m; print(m.__file__)" % module)
        assert child.returncode == 0, child.stderr
        assert Path(child.stdout.strip()).resolve().is_relative_to(checkouts[component].resolve() / "src")


def test_install_records_identify_package_and_exact_source_revision(provisioned):
    _root, checkouts, pins, _python, records = provisioned
    identities = {r["component"]: r for r in records if r.get("step") == "identity"}
    assert set(identities) == {c for c, _d, _m in rr.ISOLATED_IMPORT_PACKAGES}
    for component, dist, _module in rr.ISOLATED_IMPORT_PACKAGES:
        assert identities[component]["source_revision"] == pins[component]
        assert identities[component]["distribution"] == dist
        assert identities[component]["checkout"] == str(checkouts[component].resolve())
    installs = [r for r in records if str(r.get("step", "")).startswith("install pinned")]
    assert len(installs) == 2 and all(r["returncode"] == 0 and "-e" in r["command"] and "--no-deps" in r["command"]
                                      and "--no-build-isolation" in r["command"] for r in installs)


def test_shared_interpreter_is_not_modified_and_cannot_import_the_packages(provisioned):
    for _component, dist, module in rr.ISOLATED_IMPORT_PACKAGES:
        child = _isolated(sys.executable, "import importlib.metadata as m, importlib.util as u, sys\n"
                          "sys.exit(0 if u.find_spec(%r) is None else 3)" % module)
        assert child.returncode == 0, "shared interpreter must not see %s" % module
        meta = _isolated(sys.executable, "import importlib.metadata as m, sys\n"
                         "try:\n    m.distribution(%r)\nexcept m.PackageNotFoundError:\n    sys.exit(0)\nsys.exit(3)" % dist)
        assert meta.returncode == 0, "shared interpreter must not carry %s metadata" % dist


def test_isolated_children_are_independent_of_pythonpath_and_pythonpath_roots_still_win(provisioned, tmp_path):
    _root, checkouts, _pins, python, _records = provisioned
    decoy = tmp_path / "decoy"
    (decoy / "agent_replay_bundle").mkdir(parents=True)
    (decoy / "agent_replay_bundle" / "__init__.py").write_text("MARKER = 'decoy'\n")
    code = "import agent_replay_bundle as m; print(m.MARKER)"
    isolated = _isolated(python, code, PYTHONPATH=str(decoy))
    assert isolated.stdout.strip() == "pinned"              # -I ignores PYTHONPATH: the pinned install is used
    ordinary = subprocess.run([python, "-B", "-c", code], capture_output=True, text=True,
                              env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(decoy)})
    assert ordinary.stdout.strip() == "decoy"                # a PYTHONPATH (historical/previous) root is never shadowed


def test_wrong_checkout_revision_is_rejected_before_anything_is_created(tmp_path):
    checkouts, pins = _fakes(tmp_path)
    pins["odes"] = "0" * 40
    with pytest.raises(RuntimeError, match="not the locked"):
        rr.provision_isolated_import_environment(tmp_path / "venv", checkouts, pins)
    assert not (tmp_path / "venv").exists()


def test_dirty_checkout_is_rejected(tmp_path):
    checkouts, pins = _fakes(tmp_path)
    (checkouts["replay_bundle"] / "src" / "stray.py").write_text("x = 1\n")
    with pytest.raises(RuntimeError, match="pristine"):
        rr.provision_isolated_import_environment(tmp_path / "venv", checkouts, pins)
    assert not (tmp_path / "venv").exists()                  # rejected before any environment was created


def test_installation_that_dirties_the_pinned_checkout_is_rejected(tmp_path):
    checkouts, pins = _fakes(tmp_path)
    checkouts["odes"], pins["odes"] = _fake_checkout(tmp_path, "odes-dirtying", "open-decision-evidence-standard", "odes", dirty=True)
    with pytest.raises(RuntimeError, match="pristine"):
        rr.provision_isolated_import_environment(tmp_path / "venv", checkouts, pins)


def test_unsatisfied_requirement_of_a_pinned_package_is_rejected(tmp_path):
    checkouts, pins = _fakes(tmp_path)
    checkouts["odes"], pins["odes"] = _fake_checkout(tmp_path, "odes-needs", "open-decision-evidence-standard", "odes",
                                                    requires="surely-not-installed-distribution-xyz")
    with pytest.raises(RuntimeError, match="pip check reports problems"):
        rr.provision_isolated_import_environment(tmp_path / "venv", checkouts, pins)


def test_install_failure_stops_qualification_without_fallback(tmp_path):
    checkouts, pins = _fakes(tmp_path)
    checkouts["odes"], pins["odes"] = _fake_checkout(tmp_path, "odes-bad", "open-decision-evidence-standard", "odes", fail=True)
    with pytest.raises(RuntimeError, match="install pinned odes failed .no fallback"):
        rr.provision_isolated_import_environment(tmp_path / "venv", checkouts, pins)


def test_preinstalled_stale_copy_is_refused_not_masked(provisioned, tmp_path):
    _root, _checkouts, _pins, stale_python, _records = provisioned
    checkouts, pins = _fakes(tmp_path, marker="newer")
    # A base interpreter that already carries a (stale) agent-replay-bundle must not satisfy the isolated children.
    with pytest.raises(RuntimeError, match="already importable before installation"):
        rr.provision_isolated_import_environment(tmp_path / "venv", checkouts, pins, base_python=stale_python)


def test_stray_module_without_distribution_metadata_is_also_refused(tmp_path):
    parent = tmp_path / "parent"
    subprocess.check_call([sys.executable, "-m", "venv", str(parent)])
    purelib = subprocess.check_output([str(parent / "bin/python"), "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"], text=True).strip()
    (Path(purelib) / "odes").mkdir()
    (Path(purelib) / "odes" / "__init__.py").write_text("")
    checkouts, pins = _fakes(tmp_path)
    with pytest.raises(RuntimeError, match="already importable before installation"):
        rr.provision_isolated_import_environment(tmp_path / "venv", checkouts, pins, base_python=str(parent / "bin/python"))


def test_existing_environment_directory_is_never_reused_or_deleted(tmp_path):
    checkouts, pins = _fakes(tmp_path)
    (tmp_path / "venv").mkdir()
    (tmp_path / "venv" / "keep").write_text("x")
    with pytest.raises(RuntimeError, match="fresh isolated-import environment"):
        rr.provision_isolated_import_environment(tmp_path / "venv", checkouts, pins)
    assert (tmp_path / "venv" / "keep").exists()


def test_runner_wiring_installs_only_outside_batch_and_before_the_preflight():
    source = inspect.getsource(rr.main)
    provision = source.index("provision_isolated_import_environment(")
    guard = source.rindex("if not args.batch:", 0, provision)
    assert source[guard:provision].count("\n") <= 2          # the call sits directly under the not-batch guard
    assert provision < source.index("preflight_specs=[") < source.index("if any(x[\"returncode\"] for x in preflight_runs)")
    assert "pip\",\"install\",\"-q\",\"--no-deps\",\"--no-build-isolation\",\"-e\"" not in source  # never into the shared interpreter


def test_preflight_and_selected_suites_use_the_isolated_python_and_stay_mandatory():
    source = inspect.getsource(rr.main)
    for entry in ('("replay", [selected_python,"-m","pytest","-q",str(replay/"tests")], replay, replay_env)',
                  '("odes", [selected_python,"-m","pytest","-q",str(odes/"tests")], odes, odes_env)',
                  '("replay",[selected_python,"-m","pytest"', '("odes",[selected_python,"-m","pytest"'):
        assert entry in source
    # every other suite keeps the shared interpreter; the preflight still raises on any failure and is not skipped
    assert source.count("selected_python") == 6
    assert 'raise RuntimeError("focused Replay/ODES preflight failed; see preflight logs")' in source
    assert "[] if args.batch else preflight_specs" in source


def test_package_resolving_outside_the_pinned_checkout_is_rejected(tmp_path):
    elsewhere = tmp_path / "elsewhere"
    (elsewhere / "agent_replay_bundle").mkdir(parents=True)
    (elsewhere / "agent_replay_bundle" / "__init__.py").write_text("MARKER = 'foreign'\n")
    checkouts, pins = _fakes(tmp_path)
    checkouts["replay_bundle"], pins["replay_bundle"] = _fake_checkout(tmp_path, "replay-redirect", "agent-replay-bundle",
                                                                      "agent_replay_bundle", target=elsewhere)
    with pytest.raises(RuntimeError, match="outside the pinned checkout"):
        rr.provision_isolated_import_environment(tmp_path / "venv", checkouts, pins)


@pytest.mark.parametrize("tamper", ["not_editable", "other_url", "no_metadata"])
def test_distribution_metadata_must_name_the_pinned_checkout_as_editable_source(tmp_path, monkeypatch, tamper):
    checkouts, pins = _fakes(tmp_path)
    real = rr._probe_identity

    def probe(python, env, packages, records, label):
        seen = real(python, env, packages, records, label)
        if label.startswith("post-install"):
            direct = seen["agent-replay-bundle"]["direct_url"]
            if tamper == "not_editable":
                direct["dir_info"] = {}
            elif tamper == "other_url":
                direct["url"] = "file:///somewhere/else"
            else:
                seen["agent-replay-bundle"]["direct_url"] = None
        return seen
    monkeypatch.setattr(rr, "_probe_identity", probe)
    with pytest.raises(RuntimeError, match="does not name the pinned checkout"):
        rr.provision_isolated_import_environment(tmp_path / "venv", checkouts, pins)
