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


def test_isolated_children_leave_the_pinned_checkout_pristine(provisioned):
    # -I children ignore PYTHONDONTWRITEBYTECODE; a __pycache__ written into a pinned checkout would make the
    # later strict source-identity verification reject it (and validate_checkout would refuse a reused one).
    _root, checkouts, pins, python, _records = provisioned
    for component, _dist, module in rr.ISOLATED_IMPORT_PACKAGES:
        child = subprocess.run([python, "-I", "-c", "import %s" % module], capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"})
        assert child.returncode == 0, child.stderr
        assert _git(checkouts[component], "status", "--porcelain", "--untracked-files=all", "--ignored=matching") == ""
        rr.validate_checkout(checkouts[component], pins[component])


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


# --- Relocated tests, historical vs current evidence, and the synthetic service clock ------------------------
# Cross-component tests were relocated into the Qualification checkout. The runner must find them there, run the
# historical producer-generation suites under their historical profile, label every stage as historical or current,
# and give the deterministic developer-test stages the existing explicit synthetic clock with explicit metadata.
def _touch(path, text=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def test_relocated_path_prefers_the_component_copy_and_falls_back_to_the_canonical_suite(tmp_path):
    component, base = tmp_path / "component", tmp_path / "qualification"
    _touch(base / "suites/s/tests/t.py")
    assert rr.relocated_path("s", component, "tests/t.py", base) == base / "suites/s/tests/t.py"
    _touch(component / "tests/t.py")
    assert rr.relocated_path("s", component, "tests/t.py", base) == component / "tests/t.py"


def test_relocated_cwd_is_the_suite_directory_only_while_the_component_lacks_the_file(tmp_path):
    component, base = tmp_path / "component", tmp_path / "qualification"
    assert rr.relocated_cwd("s", component, "qualification/t.py", base) == base / "suites/s"
    _touch(component / "qualification/t.py")
    assert rr.relocated_cwd("s", component, "qualification/t.py", base) == component


def test_directory_stages_only_gain_the_files_the_component_no_longer_carries(tmp_path):
    component, base = tmp_path / "component", tmp_path / "qualification"
    _touch(component / "tests/kept.py")
    extras = rr.relocated_extras("s", component, ["tests/kept.py", "tests/moved.py"], base)
    assert extras == [base / "suites/s/tests/moved.py"]


@pytest.mark.parametrize("stage", ["research_qualification", "openshell_mock"])
def test_synthetic_clock_is_applied_to_the_declared_developer_test_stages_under_security_runtime(stage):
    assert rr.synthetic_clock_for_stage(stage, "security-runtime-p2-20261018") == rr.SYNTHETIC_CLOCK_STAGES[stage]


@pytest.mark.parametrize("stage", ["representative", "hub_release_gate", "replay", "odes", "control_plane", "gax_reference",
                                   "replay_merged", "gax_public_runtime_artifacts", "evidence_pack"])
def test_synthetic_clock_is_not_applied_to_any_other_stage(stage):
    assert rr.synthetic_clock_for_stage(stage, "security-runtime-p2-20261018") is None


@pytest.mark.parametrize("profile", ["merged-producers-v1", rr.CANDIDATE_PROFILE, None, ""])
def test_synthetic_clock_is_not_applied_outside_security_runtime_locks(profile):
    assert rr.synthetic_clock_for_stage("research_qualification", profile) is None
    assert rr.synthetic_clock_for_stage("openshell_mock", profile) is None


def test_the_synthetic_clock_values_are_the_existing_declared_fixture_times():
    assert rr.SYNTHETIC_CLOCK_STAGES == {"research_qualification": "2026-08-08T01:00:00Z", "openshell_mock": "2026-10-05T19:00:00Z"}


def test_synthetic_clock_evidence_is_labelled_and_never_claims_temporal_enforcement():
    labels = rr.evidence_labels("research_qualification", {"COGNOUS_SYNTHETIC_SERVICE_TIME": "2026-08-08T01:00:00Z",
                                                          "GAX_RUNTIME_COMPATIBILITY_PROFILE": "security-runtime-p2-20261018"})
    assert labels["synthetic_service_clock"] == "2026-08-08T01:00:00Z"
    assert "not evidence of operational temporal enforcement" in labels["synthetic_service_clock_notice"]
    assert labels["generation"] == "current" and labels["runtime_profile"] == "security-runtime-p2-20261018"
    plain = rr.evidence_labels("control_plane", {"GAX_RUNTIME_COMPATIBILITY_PROFILE": "security-runtime-p2-20261018"})
    assert plain["synthetic_service_clock"] is None and "synthetic_service_clock_notice" not in plain


@pytest.mark.parametrize("stage", ["replay_merged", "evidence_pack_merged", "odes_merged", "gax_public_runtime_artifacts", "gax_historical_artifacts"])
def test_historical_producer_stages_are_labelled_and_cannot_substitute_for_current_qualification(stage):
    labels = rr.evidence_labels(stage, {"GAX_RUNTIME_COMPATIBILITY_PROFILE": rr.HISTORICAL_GAX_PROFILE})
    assert labels["generation"] == "historical" and labels["runtime_profile"] == "merged-producers-v1"
    assert labels["historical_result_substitutes_for_current_qualification"] is False


@pytest.mark.parametrize("stage", ["replay", "odes", "evidence_pack", "research_qualification", "hub_release_gate", "index_local_chain"])
def test_current_stages_carry_no_historical_substitution_flag(stage):
    labels = rr.evidence_labels(stage, {"GAX_RUNTIME_COMPATIBILITY_PROFILE": "security-runtime-p2-20261018"})
    assert labels["generation"] == "current" and "historical_result_substitutes_for_current_qualification" not in labels


def test_runner_wiring_gives_only_the_declared_stages_the_clock_and_the_plugin():
    source = inspect.getsource(rr.main)
    assert 'stage_clock=synthetic_clock_for_stage(name,LOCK.get("runtime_profile"))' in source
    assert 'suite_env={**suite_env,"COGNOUS_SYNTHETIC_SERVICE_TIME":stage_clock}' in source
    assert 'or stage_clock:' in source                          # plugin only for the candidate set or a clocked stage
    assert 'openshell_clock=synthetic_clock_for_stage("openshell_mock",LOCK.get("runtime_profile"))' in source
    assert 'open_env["COGNOUS_SYNTHETIC_SERVICE_TIME"]=openshell_clock' in source
    # the global environment still receives the clock only for the typed-refusal candidate
    assert 'if candidate:\n        env["COGNOUS_SYNTHETIC_SERVICE_TIME"]="2026-08-08T01:00:00Z"' in source


def test_runner_wiring_runs_historical_suites_under_the_historical_profile_for_security_runtime_locks():
    source = inspect.getsource(rr.main)
    assert 'target["GAX_RUNTIME_COMPATIBILITY_PROFILE"]=HISTORICAL_GAX_PROFILE' in source
    assert "for target in (historical_merged_env, historical_gax_env)" in source
    assert 'historical_gax_env if name in historical_gax_stages else historical_merged_env' in source
    assert '{"gax_public_runtime_artifacts"} if security_runtime' in source
    assert '"stage_evidence"' in source and "historical_result_substitutes_for_current_qualification" in source


def test_runner_paths_use_the_relocated_copies_and_never_the_removed_component_paths():
    source = inspect.getsource(rr.main)
    for removed in ('gax/"tests/test_observation_repair.py"', 'gax/"tests/test_gax_imx_reference.py"',
                    'agep/"tests/test_producer_v2.py"', 'agep/"qualification/test_merged_producer.py"',
                    'odes/"qualification/test_merged_producer.py"', 'replay/"qualification/test_merged_producer.py"',
                    'index/"chain/python/test_bitrep.py"', '"npm","test"'):
        assert removed not in source.replace('"--ignore="+str(agep/"tests/test_producer_v2.py")', "")
    for expected in ('relocated("cognous-governed-exchange",gax,"tests/test_observation_repair.py")',
                     'relocated("cognous-evidence-registry",index,"chain/python/test_bitrep.py")',
                     'relocated("cognous-governance-evidence-pack",agep,"tests/test_producer_v2.py")',
                     'relocated("cognous-replay-bundle",replay,"qualification/test_merged_producer.py")',
                     'relocated_dir("open-decision-evidence-standard",odes,"qualification/test_merged_producer.py")'):
        assert expected in source


def test_directory_stages_regain_the_relocated_files_without_touching_the_candidate_flow():
    source = inspect.getsource(rr.main)
    # command lines are recorded in the JSON results, so appended paths must be plain strings
    assert "return [] if candidate else [str(path) for path in relocated_extras(" in source
    for name in ("test_producer_v2_persistence.py", "test_pinned_integration.py", "test_importer.py", "test_accepted_executor_profile.py",
                 "test_accepted_replay_profile.py", "test_odes_stack_export.py"):
        assert name in source
    assert '*replay_relocated, *(["--ignore="+str(replay/"tests/test_refusal_evidence.py")] if candidate else [])' in source
    assert '"preflight_specs=[' not in source and '("replay", [selected_python,"-m","pytest","-q",str(replay/"tests")], replay, replay_env)' in source


def test_registry_chain_uses_an_install_suite_overlay_and_the_supported_node_and_python_invocations():
    source = inspect.getsource(rr.main)
    assert '"--suite","cognous-evidence-registry"' in source and "registry-overlay-evidence.json" in source
    assert source.index("registry-overlay-evidence.json") < source.index("preflight_specs=[")      # assembled before any suite
    assert "run_index_local_chain(index/\"chain\",env)" in source


@pytest.mark.parametrize("codes,expected", [((0, 0), 0), ((1, 0), 1), ((0, 3), 3), ((2, 3), 2)])
def test_index_local_chain_fails_if_either_supported_invocation_fails(monkeypatch, tmp_path, codes, expected):
    calls = []
    def fake(cmd, *, cwd=None, env=None, check=False):
        calls.append((cmd, cwd))
        return {"command": cmd, "cwd": str(cwd), "returncode": codes[len(calls) - 1], "seconds": 1.0, "output": "out%d" % len(calls)}
    monkeypatch.setattr(rr, "run", fake)
    record = rr.run_index_local_chain(tmp_path, {})
    assert [c[0] for c in calls] == [["node", "--test", "test/protocol.test.mjs"], [sys.executable, "python/test_bitrep.py"]]
    assert all(c[1] == tmp_path for c in calls)
    assert record["returncode"] == expected and "out1" in record["output"] and "out2" in record["output"]


def test_the_frozen_matrix_and_declared_batches_are_unchanged_by_the_relocation_wiring():
    assert BATCHES["registry"] == {"bitrep_verification", "index_bitrep_binding"}
    assert "gax_public_runtime_artifacts" in BATCHES["exchange"] and "research_qualification" in BATCHES["exchange"]
