"""Run the repaired-source migration cases at exact clean component revisions.

SPDX-License-Identifier: Apache-2.0
Candidate execution never selects or authorizes a release.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT/'process/security-runtime-candidate-20261016.json'


def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True, timeout=120).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--components', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--prepare-work', action='store_true')
    args = parser.parse_args()
    profile = json.loads(PROFILE.read_text())
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
    env['PYTHONPATH'] = os.pathsep.join(map(str, [paths['control_plane'], paths['control_plane']/'src',
        paths['runtime'], paths['replay']/'src', paths['evidence_pack']/'src',
        *([paths['odes']/'src'] if 'odes' in paths else [])]))
    command = [sys.executable,'-m','pytest','-q',str(ROOT/'suites/security-runtime'),
        '--junitxml='+str(args.out.resolve()/'junit.xml'),'--basetemp='+str(args.out.resolve()/'native')]
    if phase == 'replay':
        command += ['-k','not evidence_pack and not odes and not exchange']
    with (args.out/'stdout.log').open('w') as stream:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=240)
    for name, spec in profile['components'].items():
        if git(paths[name],'rev-parse','HEAD') != spec['revision'] or git(paths[name],'status','--porcelain','--untracked-files=all'):
            raise ValueError('Source changed during execution: '+name)
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    report = {'profile':profile,'source_revisions':pins,'command':command,'returncode':result.returncode,
        'qualification_head':git(ROOT,'rev-parse','HEAD'),
        'qualification_worktree_dirty':bool(git(ROOT,'status','--porcelain','--untracked-files=all')),
        'source_hashes':{str(p.relative_to(ROOT)):digest(p) for p in [PROFILE,Path(__file__),*sorted((ROOT/'suites/security-runtime').glob('*.py'))]},
        'python':sys.version,'evidence':{p.relative_to(args.out).as_posix():digest(p) for p in sorted(args.out.rglob('*')) if p.is_file()},
        'selected':False,'reference_release_authorized':False,'production_deployment_authorized':False,
        'qualification_scope':'Actual components; synthetic fixtures; PR heads remain diagnostic until merged-source rerun'}
    (args.out/'run.json').write_text(json.dumps(report,indent=2)+'\n')
    print((args.out/'stdout.log').read_text())
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
