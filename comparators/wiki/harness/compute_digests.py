#!/usr/bin/env python3
"""Computes comparators/digests.json and comparators/DIGESTS.md: the sha256 of every file that the freeze amendment names.

Usage: SCN_HUB_DIR=<hub checkout at the pinned revision> python3 compute_digests.py [--check]
  without --check  writes the two files
  with --check     exits 1 when the committed files differ from a fresh computation
Reads files only; no network access; executes no scenario.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import sys

PKG = Path(__file__).resolve().parents[1]            # comparators/wiki
CMP = PKG.parent                                      # comparators
REPO = CMP.parent
SUITE = 'suites/cognous-open-control-stack'
BASE_COMMIT = '5027aff9eaf6c78bc26e990a7b140cb8dbc5f8ca'
HUB_REPO = 'cogno-us/cognous-open-control-stack'
HUB_SHA = '8517818fbf817897aacfb6fe7898c22aea46fd95'
HUB_FILES_USED = ['assurance_runtime.py', 'bounded_json.py', 'protected_destination.py', 'trust_evidence.py']

REGISTERED = [   # files of the registered sets, relative to the repository root
    SUITE + '/tools/run_comparative_governance.py',
    SUITE + '/benchmarks/governance/adapters.py',
    SUITE + '/benchmarks/governance/policy.rego',
    SUITE + '/benchmarks/governance/corner-plan.json',
    SUITE + '/benchmarks/governance/plan.json',
    SUITE + '/benchmarks/governance/dependencies.json',
    SUITE + '/benchmarks/governance/requirements.txt',
]

GROUPS = {   # name -> (description, rule for membership: list of paths or globs relative to comparators/)
    'wiki_plan_file': ('plan file of PR-6: the Wiki-subset plan with the executable steps of every asked scenario',
                       ['wiki/plans/wiki-subset-plan.json']),
    'expected_outcomes': ('expected outcomes (statuses, effects, rulings) and the scripts that build them',
                          ['wiki/expected-outcomes/*']),
    'opa_rule_file': ('rule file of the OPA application', ['wiki/apps/wiki_policy.rego']),
    'comparator_modules': ('modules of the two comparator applications and the declared world they use',
                           ['__init__.py', 'wiki/__init__.py', 'wiki/apps/__init__.py', 'wiki/apps/wiki_config.py',
                            'wiki/apps/wiki_opa_app.py', 'wiki/apps/wiki_langgraph_app.py']),
    'runner_modules': ('oracle loader and plan tooling of the Wiki subset (the scoring code itself is the pinned runner file)',
                       ['wiki/harness/*']),
    'declared_interfaces': ('declared interface of each comparator application', ['wiki/interface/*']),
    'dependency_lock': ('hash-locked requirements and the direct pins they come from', ['deps/*']),
    'ocs_crossref': ('cross-reference listing of test names (different harness, not scored)', ['wiki/crossref/*']),
    'runner': ('comparison runner and the declarations of the protected-destination column (includes its own digests.json and its tests)',
               ['runner/*', 'runner/tests/*']),
    'package_tests': ('tests of this package (informational: not part of the frozen run)', ['tests/*', 'tests/support/*']),
}
SELF = {'digests.json', 'DIGESTS.md'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def group_files(patterns):
    out = []
    for pat in patterns:
        out += [p for p in CMP.glob(pat) if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc']
    return sorted(set(out))


def group_digest(files):
    text = ''.join('%s  %s\n' % (sha(f), f.relative_to(REPO).as_posix()) for f in sorted(files, key=lambda f: f.relative_to(REPO).as_posix()))
    return hashlib.sha256(text.encode()).hexdigest()


def evaluate_source_sha256(runner_path):
    source = Path(runner_path).read_text()
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'evaluate')
    return hashlib.sha256(ast.get_source_segment(source, node).encode()).hexdigest()


def compute(hub_dir):
    plan = json.loads((PKG / 'plans/wiki-subset-plan.json').read_text())
    outcomes = json.loads((PKG / 'expected-outcomes/outcomes-final.json').read_text())
    result = {
        'schema': 'cognous.comparators-digests/1',
        'base_commit': BASE_COMMIT,
        'note': ('sha256 of every file that the freeze amendment names, computed from the files of this package and from the registered files at the base commit. '
                 'A group digest is the sha256 of the lines "<sha256>  <path>" of its files in path order. This file and DIGESTS.md are not listed in any group.'),
        'registered_files': {rel: sha(REPO / rel) for rel in REGISTERED},
        'registered_evaluate_function_source_sha256': evaluate_source_sha256(REPO / REGISTERED[0]),
        'hub': {'repo': HUB_REPO, 'revision': HUB_SHA,
                'files_used_by_the_registered_sets_and_the_comparators': {n: sha(Path(hub_dir) / 'reference_profiles' / n) for n in HUB_FILES_USED},
                'reference_profiles_tree': {p.name: sha(p) for p in sorted((Path(hub_dir) / 'reference_profiles').glob('*.py'))}},
        'opa_binary_sha256_per_dependencies_json': json.loads((REPO / SUITE / 'benchmarks/governance/dependencies.json').read_text())['opa']['sha256'],
        'groups': {},
        'files': {},
        'wiki_plan': {
            'path': 'comparators/wiki/plans/wiki-subset-plan.json',
            'sha256': sha(PKG / 'plans/wiki-subset-plan.json'),
            'cases_in_registered_subset': 28, 'scenarios': plan['scenarios_total'],
            'executable_cases': len(plan['cases']),
            'counts_per_state_plan_file': plan['counts_per_state'],
            'counts_per_state_outcome_files': outcomes['counts_per_state'],
            'per_configuration_counts': {
                'opa-transactional-application': dict(plan['counts_per_state'], scored=len(plan['cases'])),
                'langgraph-opa-transactional-application': dict(plan['counts_per_state'], scored=len(plan['cases'])),
                'cognous-protected-destination': 'not authored: declarations of not expressible and not claimed for the protected destination need the owner (see DECISIONS.md)'},
            'seeds': plan['seeds'], 'repetitions': plan['repetitions'],
            'plan_authoring_reclassifications': sorted(x['id'] for x in plan['non_executed'] if x['origin'].startswith('plan authoring')),
        },
        'owner_held_records': json.loads((CMP / 'owner-held-records.json').read_text()),
    }
    for name, (desc, patterns) in GROUPS.items():
        files = group_files(patterns)
        result['groups'][name] = {'description': desc, 'group_sha256': group_digest(files),
                                  'files': [f.relative_to(REPO).as_posix() for f in files]}
        for f in files:
            result['files'][f.relative_to(REPO).as_posix()] = sha(f)
    listed = {Path(p).relative_to('comparators').as_posix() for p in result['files']}
    every = {p.relative_to(CMP).as_posix() for p in CMP.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    unlisted = sorted(every - listed - SELF - {'README.md', 'DECISIONS.md', 'owner-held-records.json'})
    result['unlisted_files_check'] = unlisted
    return result


def render_md(d):
    L = ['# Digests of the comparator package', '',
         'Generated by `comparators/wiki/harness/compute_digests.py`; checked by `comparators/tests/test_package_digests.py`. '
         'Base commit of the qualification repository: `%s`.' % d['base_commit'], '',
         'Scope text (unchanged): ' + json.loads((REPO / 'process/release-gate/preregistration.json').read_text())['scope_text'], '',
         '## Registered files the comparison uses (not changed by this package)', '', '| File | sha256 |', '|---|---|']
    L += ['| `%s` | `%s` |' % (k, v) for k, v in d['registered_files'].items()]
    L += ['', 'Function source sha256 of `evaluate`: `%s`.' % d['registered_evaluate_function_source_sha256'], '',
          '## Hub files at `%s`' % d['hub']['revision'], '', '| File | sha256 |', '|---|---|']
    L += ['| `reference_profiles/%s` | `%s` |' % (k, v) for k, v in d['hub']['files_used_by_the_registered_sets_and_the_comparators'].items()]
    L += ['', 'The whole `reference_profiles` tree of that revision is listed in `digests.json` under `hub.reference_profiles_tree`.', '',
          '## Wiki-subset plan file', '', '- path: `%s`' % d['wiki_plan']['path'], '- sha256: `%s`' % d['wiki_plan']['sha256'],
          '- scenarios: %d in %d cases; executable (asked) scenarios: %d' % (d['wiki_plan']['scenarios'], d['wiki_plan']['cases_in_registered_subset'], d['wiki_plan']['executable_cases']),
          '- counts per state in the plan file: ' + json.dumps(d['wiki_plan']['counts_per_state_plan_file']),
          '- counts per state in the outcome files (before plan authoring): ' + json.dumps(d['wiki_plan']['counts_per_state_outcome_files']),
          '- seeds %s, repetitions %d' % (d['wiki_plan']['seeds'], d['wiki_plan']['repetitions']), '',
          '## Groups', '', '| Group | Group sha256 | Files |', '|---|---|---|']
    L += ['| `%s` | `%s` | %d |' % (k, v['group_sha256'], len(v['files'])) for k, v in d['groups'].items()]
    L += ['', '## Every file', '', '| File | sha256 |', '|---|---|']
    L += ['| `%s` | `%s` |' % (k, v) for k, v in sorted(d['files'].items())]
    L += ['', '## Records held by the owner (not in this repository)', '']
    L += ['- %s: `%s`' % (r['role'], r['sha256']) for r in d['owner_held_records']['records']]
    L += ['', '## Dependencies', '', 'OPA binary sha256 (from `dependencies.json`): `%s`.' % d['opa_binary_sha256_per_dependencies_json'], '']
    return '\n'.join(L)


def main(argv):
    hub = os.environ.get('SCN_HUB_DIR')
    if not hub:
        raise SystemExit('SCN_HUB_DIR is required (hub checkout at %s)' % HUB_SHA)
    d = compute(hub)
    j = json.dumps(d, indent=1, sort_keys=True) + '\n'
    m = render_md(d) + '\n'
    if '--check' in argv:
        same = (CMP / 'digests.json').read_text() == j and (CMP / 'DIGESTS.md').read_text() == m
        print('digests up to date' if same else 'digests differ from a fresh computation')
        return 0 if same else 1
    (CMP / 'digests.json').write_text(j)
    (CMP / 'DIGESTS.md').write_text(m)
    print('written; plan sha256', d['wiki_plan']['sha256'])
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
