"""Run the repaired-source migration cases at exact clean component revisions.

SPDX-License-Identifier: Apache-2.0
Candidate execution never selects or authorizes a release.
The default profile is the historical F3 candidate; later generations are
selected with --profile so earlier retained evidence stays reproducible.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT/'process/security-runtime-candidate-20261016.json'
# Defaults reproduce the historical F3 run when a profile omits these fields.
DEFAULT_EXCHANGE_PROFILE = 'security-runtime-candidate-20261016'
DEFAULT_SUITE_GENERATION = 'security'
SUITE_GENERATIONS = frozenset({'security', 'f5b', 'p4', 'p2', 'cur'})


def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True, timeout=120).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--components', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--prepare-work', action='store_true')
    parser.add_argument('--profile', type=Path, default=PROFILE,
        help='candidate profile inside this repository (default: historical F3 candidate)')
    args = parser.parse_args()
    profile_path = (args.profile if args.profile.is_absolute() else ROOT/args.profile).resolve()
    profile_path.relative_to(ROOT)  # only committed profiles in this checkout
    profile = json.loads(profile_path.read_text())
    exchange_profile = profile.get('exchange_compatibility_profile', DEFAULT_EXCHANGE_PROFILE)
    generation = profile.get('suite_generation', DEFAULT_SUITE_GENERATION)
    if generation not in SUITE_GENERATIONS:
        raise ValueError('Unsupported suite generation')
    extra_hashed = [ROOT/name for name in profile.get('additional_source_hashes', [])]
    for path in extra_hashed:
        path.resolve().relative_to(ROOT)
    if any(profile[key] is not False for key in ('selected', 'reference_release_authorized', 'production_deployment_authorized')):
        raise ValueError('Candidate must remain nonselected and nonauthorizing')
    if args.out.exists():
        raise ValueError('Evidence output must be new')
    paths = {}; pins = {}
    for name, spec in profile['components'].items():
        path = (args.components/name).resolve()
        if not path.exists() and args.prepare_work:
            path.mkdir(parents=True)
            for command in (['git','init','-q',str(path)],
                            ['git','-C',str(path),'remote','add','origin','https://github.com/'+spec['repository']+'.git'],
                            ['git','-C',str(path),'fetch','-q','--depth','1','origin',spec['revision']],
                            ['git','-C',str(path),'checkout','-q','--detach','FETCH_HEAD']):
                subprocess.run(command, check=True, timeout=180)
        if git(path,'rev-parse','HEAD') != spec['revision'] or git(path,'status','--porcelain','--untracked-files=all'):
            raise ValueError('Dirty or mismatched source: '+name)
        paths[name] = path
        pins[name] = {**spec, 'tree':git(path,'rev-parse','HEAD^{tree}')}
    phase = profile['phase']
    if phase not in {'replay','consumers','full'}:
        raise ValueError('Unsupported qualification phase')
    args.out.mkdir(parents=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    # The suite imports the revision constants of the generation this profile pins.
    env['COGNOUS_SECURITY_RUNTIME_GENERATION'] = generation
    env['PYTHONPATH'] = os.pathsep.join(map(str, [paths['control_plane'], paths['control_plane']/'src',
        paths['runtime'], paths['replay']/'src', paths['evidence_pack']/'src',
        *([paths['odes']/'src'] if 'odes' in paths else []),
        *([paths['exchange']] if 'exchange' in paths else [])]))
    if 'exchange' in paths:
        env['GAX_RUNTIME_COMPATIBILITY_PROFILE'] = exchange_profile
        env['MOLTBOT_SAFE_CONTROL_PLANE_ROOT'] = str(paths['control_plane'])
        env['MOLTBOT_SAFE_ROOT'] = str(paths['runtime'])
        env['UPSTREAM_MANIFEST_EXAMPLE'] = str(paths['manifest']/'examples/refund_integration_v1_1.manifest.json')
    command = [sys.executable,'-m','pytest','-q',str(ROOT/'suites/security-runtime'),
        '--junitxml='+str(args.out.resolve()/'junit.xml'),'--basetemp='+str(args.out.resolve()/'native')]
    if phase == 'replay':
        command += ['-k','not evidence_pack and not odes and not exchange']
    elif phase == 'consumers':
        command += ['-k','not exchange']
    with (args.out/'stdout.log').open('w') as stream:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=240)
    for name, spec in profile['components'].items():
        if git(paths[name],'rev-parse','HEAD') != spec['revision'] or git(paths[name],'status','--porcelain','--untracked-files=all'):
            raise ValueError('Source changed during execution: '+name)
    cases = list(ET.parse(args.out/'junit.xml').getroot().iter('testcase'))
    counts = {'testcase_elements': len(cases), **{kind: sum(c.find(kind) is not None for c in cases)
        for kind in ('failure', 'error', 'skipped')}}
    expected = {'replay':16, 'consumers':30, 'full':36}[phase]
    passed = result.returncode == 0 and len(cases) == expected and not any(counts[k] for k in ('failure','error','skipped'))
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    report = {'profile':profile,'profile_file':profile_path.relative_to(ROOT).as_posix(),
        'suite_generation':generation,'exchange_compatibility_profile':exchange_profile if 'exchange' in paths else None,
        'source_revisions':pins,'command':command,'returncode':result.returncode,
        'qualification_head':git(ROOT,'rev-parse','HEAD'),
        'raw_junit_counts':counts,'expected_testcase_elements':expected,
        'bounded_cases_passed':passed,
        'candidate_integration_passed':passed and phase=='full' and profile['qualification_input_status']=='merged_only',
        'qualification_worktree_dirty':bool(git(ROOT,'status','--porcelain','--untracked-files=all')),
        'source_hashes':{str(p.relative_to(ROOT)):digest(p) for p in [profile_path,Path(__file__),*sorted((ROOT/'suites/security-runtime').glob('*.py')),*extra_hashed]},
        'python':sys.version,'evidence':{p.relative_to(args.out).as_posix():digest(p) for p in sorted(args.out.rglob('*')) if p.is_file()},
        'selected':False,'reference_release_authorized':False,'production_deployment_authorized':False,
        'qualification_scope':'Actual components; synthetic fixtures; PR heads remain diagnostic until merged-source rerun'}
    (args.out/'run.json').write_text(json.dumps(report,indent=2)+'\n')
    print((args.out/'stdout.log').read_text())
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
