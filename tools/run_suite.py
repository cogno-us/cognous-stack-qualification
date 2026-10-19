"""Run an explicit command in a disposable source checkout and retain v1 telemetry.

SPDX-License-Identifier: Apache-2.0
Command success is not scenario acceptance; profiles/components are declared inputs.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
import platform
import signal
from pathlib import Path
import subprocess
import tempfile
import uuid
from install_suite import install, git
from qualification_results import ROOT, base_record, digest, validate_manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', required=True)
    parser.add_argument('--source-root', required=True, type=Path)
    parser.add_argument('--source-revision', default='HEAD')
    parser.add_argument('--results-dir', required=True, type=Path)
    parser.add_argument('--profile', type=Path, help='Declared profile; not proof of loaded dependencies')
    parser.add_argument('--timeout', type=int, default=300)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command or args.timeout <= 0:
        parser.error('Supply a command after -- and a positive timeout')
    out = args.results_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    try:
        manifest = json.loads((ROOT/'migrations/cross-component-2026-10-15.json').read_text())
        repository = manifest['repositories'][args.suite]['repository']
        revision = git(args.source_root.resolve(), 'rev-parse', args.source_revision+'^{commit}')
        qualification = git(ROOT, 'rev-parse', 'HEAD')
        record = base_record('command-'+uuid.uuid4().hex, 'command', repository, revision, [qualification])
    except (OSError, KeyError, ValueError, subprocess.SubprocessError) as exc:
        (out/'setup-error.json').write_text(json.dumps({'outcome':'INCONCLUSIVE','stage':'source identity','error_type':type(exc).__name__,'limitation':'Exact inputs unavailable; no valid run manifest can be asserted.'},indent=2)+'\n')
        return 2
    record['environment'] = {'kind':'local-command','python':platform.python_version(),'platform':platform.platform()}
    record['qualification']['worktree_dirty'] = bool(git(ROOT,'status','--porcelain','--untracked-files=all'))
    record['execution'] = {'command':command,'started_at':datetime.now(timezone.utc).isoformat(), 'timeout_seconds':args.timeout}
    code = 2
    stage = 'setup'
    timed_out = False
    try:
        if args.profile:
            profile = args.profile.resolve()
            declared = json.loads(profile.read_text())
            record['profile'] = {'label':profile.name, 'sha256':digest(profile)}
            record['component_set']['declared_components'] = declared.get('components', {})
        with tempfile.TemporaryDirectory(prefix='cognous-suite-') as temp:
            source = Path(temp)/'source'
            subprocess.run(['git','clone','--quiet','--no-hardlinks','--no-checkout',str(args.source_root.resolve()),str(source)],check=True)
            subprocess.run(['git','-C',str(source),'checkout','--quiet','--detach',revision],check=True)
            identity = install(args.suite,source,evidence=out/'source-identity.json')
            record['source']['status_before_assembly'] = identity['source_status_before_assembly']
            record['qualification']['migration_manifest_sha256'] = identity['migration_manifest_sha256']
            env = os.environ.copy()
            env['PYTHONDONTWRITEBYTECODE']='1'
            env['PYTHONPATH']=os.pathsep.join([str(source),str(source/'src'),env.get('PYTHONPATH','')])
            stage = 'execution'
            with (out/'execution.log').open('w') as stream:
                process = subprocess.Popen(command,cwd=source,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=(os.name=='posix'))
                try:
                    code = process.wait(timeout=args.timeout)
                except subprocess.TimeoutExpired:
                    timed_out=True; code=124
                    if os.name=='posix': os.killpg(process.pid,signal.SIGKILL)
                    else: process.kill()
                    process.wait()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        record['execution']['error_type'] = type(exc).__name__
        record['execution']['error'] = str(exc)
        code = 2
    record['observed_at'] = datetime.now(timezone.utc).isoformat()
    record['execution'].update(finished_at=record['observed_at'],exit_code=code,timed_out=timed_out,stage=stage,
        outcome=('INCONCLUSIVE' if code==2 and 'error_type' in record['execution'] else 'PASS' if code==0 else 'FAIL'))
    for name in ('source-identity.json','execution.log'):
        path=out/name
        if path.exists():record['evidence'].append({'kind':name,'path':name,'sha256':digest(path),'retention':'LOCAL_ONLY'})
    validate_manifest(record)
    (out/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    # Preserve the prior CLI result interface for existing consumers.
    (out/'command-result.json').write_text(json.dumps({'command':command,'exit_code':code,'timed_out':timed_out,'owning_source_commit':revision,'qualification_commit':qualification,'scope':'Command outcome only; scenario acceptance is NOT ASSESSED.'},indent=2)+'\n')
    print(json.dumps({'manifest':str(out/'manifest.json'),'execution_outcome':record['execution']['outcome'],'scenario_results':[]}))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
