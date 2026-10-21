"""Shared run logic of the comparison: preflight, the seeded schedule, one trial, one row.

The scoring code is the registered runner file (run_comparative_governance.py), loaded by path after its digests are checked; its
`run_case` runs each trial and its `evaluate` scores it. Nothing is copied from it. This module only decides which trials of a set
are run, in which order, and keeps every row (RO-8); a trial that raises is kept as could not check, never retried and never a pass.
"""
import ast
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import random
import shutil
import sqlite3
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO))
from comparators.wiki.harness import _base  # noqa: E402

SUITE_REL = 'suites/cognous-open-control-stack'
OCS_PROFILE = 'cognous-protected-destination'
OPA_PROFILE = 'opa-transactional-application'
GRAPH_PROFILE = 'langgraph-opa-transactional-application'
PROFILES = (OCS_PROFILE, OPA_PROFILE, GRAPH_PROFILE)


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def evaluate_source_sha256(runner_path):
    """sha256 of the source text of the function `evaluate` in the registered runner file (the registered oracle digest)."""
    source = Path(runner_path).read_text()
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'evaluate')
    return hashlib.sha256(ast.get_source_segment(source, node).encode()).hexdigest()


def load_runner():
    """A fresh copy of the registered runner module (its module globals are not shared between sets)."""
    runner = _base.pinned_runner()  # checks the digests of the pinned files and loads the runner file by path
    source = (_base.suite_dir() / 'tools/run_comparative_governance.py')
    if evaluate_source_sha256(source) != _base.EVALUATE_SOURCE_SHA256:
        raise RuntimeError('the scoring function differs from the registered function')
    return runner


def preflight(opa):
    """The checks that the registered runner makes before it runs (pinned OPA binary and direct dependencies) and the identities that a
    report records. Raises on any difference."""
    suite = _base.suite_dir()
    lock = json.loads((suite / 'benchmarks/governance/dependencies.json').read_text())
    opa = str(Path(opa).resolve())
    if sha256_file(opa) != lock['opa']['sha256']:
        raise ValueError('OPA binary differs from pinned dependency')
    for package, version in lock['python_direct'].items():
        if importlib.metadata.version(package) != version:
            raise ValueError('dependency drift: ' + package)
    _base.check_pins()
    if evaluate_source_sha256(suite / 'tools/run_comparative_governance.py') != _base.EVALUATE_SOURCE_SHA256:
        raise RuntimeError('the scoring function differs from the registered function')
    return dict(opa_sha256=lock['opa']['sha256'], opa_version=subprocess.check_output([opa, 'version'], text=True).strip(),
                python=platform.python_version(), platform=platform.platform(), sqlite=sqlite3.sqlite_version,
                runner_file_sha256=_base.PINNED_SHA256['tools/run_comparative_governance.py'],
                evaluate_function_source_sha256=_base.EVALUATE_SOURCE_SHA256,
                adapters_file_sha256=_base.PINNED_SHA256['benchmarks/governance/adapters.py'],
                dependencies=lock['python_direct'])


def schedule(cases, profiles, repetitions, seed):
    """The schedule of the registered runner: every (repetition, case, configuration), shuffled by the seed."""
    items = [(rep, case, profile) for rep in range(repetitions) for case in cases for profile in profiles]
    random.Random(seed).shuffle(items)
    return items


def run_trial(runner, adapter_class, case, root, opa, masked):
    try:
        verdict = runner.run_case(adapter_class, case, root, opa)
    except Exception as exc:  # noqa: BLE001  a trial that raises is could not check, retained with its text
        return dict(error='%s: %s' % (type(exc).__name__, str(exc)[:400]))
    if masked:
        del verdict  # the verdict is discarded on purpose; only that the trial executed is kept
        return dict(executed=True)
    return verdict


def run_rows(runner, adapter_map, cases, states, seed, repetitions, opa, out_root, masked=False, progress=None):
    """Run the trials of one set for one seed. adapter_map: {profile: class} (installed as the runner's ADAPTERS); cases: scenario dicts with an
    id; states: {profile: {scenario id: state record}} where a record says whether the scenario is run and whether it is scored."""
    runner.ADAPTERS = dict(adapter_map)
    profiles = list(adapter_map)
    work = Path(tempfile.mkdtemp(prefix='cmp-')) if masked else Path(out_root)
    rows = []
    try:
        for rep, case, profile in schedule(cases, profiles, repetitions, seed):
            state = states[profile][case['id']]
            if not state['run']:
                continue
            root = work / ('%s-%d-%s-%s' % (seed, rep, profile, case['id']))
            result = run_trial(runner, adapter_map[profile], case, root, opa, masked)
            mode = 'masked' if masked else ('scored' if state['scored'] else 'observation')
            row = dict(result)
            row.update(case_id=case['id'], profile=profile, repetition=rep, seed=seed, mode=mode)
            if masked:
                row = {k: row[k] for k in ('case_id', 'profile', 'repetition', 'seed', 'mode', 'executed', 'error') if k in row}
            rows.append(row)
            if progress:
                progress(row)
    finally:
        if masked:
            shutil.rmtree(work, ignore_errors=True)
    return rows


def twin_cases(cases, ids):
    """Renamed development twins of the selected scenarios: id twin-1, twin-2, ... in the order given. Returns (twins, states_rename) where
    states_rename maps the original id to the twin id; the original ids are not kept in any row."""
    by_id = {c['id']: c for c in cases}
    unknown = [i for i in ids if i not in by_id]
    if unknown:
        raise SystemExit('not an executable scenario of the plan: ' + ', '.join(unknown))
    twins, rename = [], {}
    for n, sid in enumerate(ids, 1):
        twin = {k: v for k, v in by_id[sid].items() if k in ('steps', 'expected_statuses', 'expected_effects', 'allowed_effect_ids',
                                                              'expected_payload', 'expected_reasons')}
        twin['id'] = 'twin-%d' % n
        twins.append(twin)
        rename[sid] = twin['id']
    return twins, rename


def git_info(repo=REPO):
    def git(*args):
        try:
            return subprocess.check_output(['git', '-C', str(repo), *args], text=True, stderr=subprocess.DEVNULL).strip()
        except Exception:  # noqa: BLE001
            return None
    added = (git('log', '--diff-filter=A', '--format=%H', '--', 'docs/release-gate/pre-registration.md') or '').splitlines()
    head = git('rev-parse', 'HEAD')
    return dict(head=head, registration_commit=added[-1] if added else None, dirty=bool(git('status', '--porcelain')) if head else None)


def candidate_manifest_digest(repo=REPO):
    """Digest of the candidate manifest as amendment 91 defines it: one line per file (profile, freeze manifest, refreeze log), each line the
    path, one space and the sha256 of the file bytes, followed by a line feed; the digest is the sha256 of that text. None when a file is absent."""
    files = ['process/security-runtime-f5b-20261016-r12.json', 'process/v1-validation/v1-2026-10-16-a/freeze-manifest.json',
             'process/v1-validation/v1-2026-10-16-a/refreeze-log.json']
    if not all((Path(repo) / f).is_file() for f in files):
        return None
    text = ''.join('%s %s\n' % (f, sha256_file(Path(repo) / f)) for f in files)
    return dict(files={f: sha256_file(Path(repo) / f) for f in files}, sha256=hashlib.sha256(text.encode()).hexdigest())


def run_identity(plan_files, candidate_id=None, repo=REPO):
    """What every report records (RP-9): candidate id, commit and sha256 of each plan file, the oracle digest, the candidate manifest digest,
    the pre-registration commit and the amendments in force. plan_files: {label: repo-relative path}."""
    repo = Path(repo)
    git = git_info(repo)

    def last_commit(rel):
        try:
            return subprocess.check_output(['git', '-C', str(repo), 'log', '-1', '--format=%H', '--', rel], text=True,
                                           stderr=subprocess.DEVNULL).strip() or None
        except Exception:  # noqa: BLE001
            return None
    twin = json.loads((repo / 'process/release-gate/preregistration.json').read_text())
    return dict(
        candidate_id=candidate_id,
        qualification_commit=git['head'], working_tree_dirty=git['dirty'],
        plan_files={label: dict(path=rel, sha256=sha256_file(repo / rel), last_commit=last_commit(rel)) for label, rel in plan_files.items()},
        oracle=dict(evaluate_function_source_sha256=_base.EVALUATE_SOURCE_SHA256,
                    runner_file_sha256=_base.PINNED_SHA256['tools/run_comparative_governance.py'],
                    runner_file='%s/tools/run_comparative_governance.py' % SUITE_REL),
        candidate_manifest=candidate_manifest_digest(repo),
        pre_registration=dict(commit=git['registration_commit'],
                              page_sha256=sha256_file(repo / 'docs/release-gate/pre-registration.md'),
                              twin_sha256=sha256_file(repo / 'process/release-gate/preregistration.json')),
        amendments_in_force=dict(count=len(twin['amendments']), numbers='1 to %d' % len(twin['amendments']),
                                 last_timestamp=twin['amendments'][-1]['timestamp']))
