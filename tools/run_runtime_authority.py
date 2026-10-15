"""Execute one exact-source candidate and retain native outputs and commitments.

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    """Verify revisions before running; never select, merge, publish or dispatch remotely."""
    ap=argparse.ArgumentParser();ap.add_argument('--components',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    manifest=json.loads((ROOT/'process/runtime-authority-candidate-2026-10-15.json').read_text())
    locations={};pins={}
    for name,spec in manifest['components'].items():
        path=(args.components/name).resolve()
        head=subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()
        if head!=spec['revision']:raise SystemExit('source revision mismatch: '+name)
        changed=subprocess.check_output(['git','-C',str(path),'diff','HEAD','--name-only'],text=True).splitlines()
        # Bytecode is not a source change. Any other tracked change invalidates an exact-head claim.
        if any('__pycache__/' not in p and not p.endswith('.pyc') for p in changed):
            raise SystemExit('source checkout modified: '+name)
        locations[name]=path;pins[name]={**spec,'tree':subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD^{tree}'],text=True).strip()}
    args.out.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
    env['PYTHONPATH']=':'.join(str(p) for p in [locations['control_plane'],locations['control_plane']/'src',
        locations['runtime'],locations['replay']/'src',locations['evidence_pack']/'src'])
    command=[sys.executable,'-m','pytest','-q',str(ROOT/'suites/runtime-authority'),
        '--junitxml='+str(args.out.resolve()/'junit.xml'),'--basetemp='+str(args.out.resolve()/'native')]
    with (args.out/'stdout.log').open('w') as output:
        result=subprocess.run(command,cwd=ROOT,env=env,stdout=output,stderr=subprocess.STDOUT)
    report={'candidate':manifest,'source_revisions':pins,'command':command,'returncode':result.returncode,
        'python':sys.version,'test_mode':'actual components with original synthetic fixtures; no network effects',
        'evidence':{p.relative_to(args.out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(args.out.rglob('*')) if p.is_file() and p.name!='run.json'},
        'selected':False,'reference_release_authorized':False,'production_deployment_authorized':False}
    (args.out/'run.json').write_text(json.dumps(report,indent=2)+'\n')
    print((args.out/'stdout.log').read_text());raise SystemExit(result.returncode)

if __name__=='__main__':main()
