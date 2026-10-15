"""Run a relocated suite command in a fresh owning-source checkout.

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations
import argparse
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import tempfile
from install_suite import install


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', required=True)
    parser.add_argument('--source-root', required=True, type=Path)
    parser.add_argument('--source-revision', default='HEAD')
    parser.add_argument('--results-dir', required=True, type=Path)
    parser.add_argument('--timeout', type=int, default=300)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('Supply an explicit command after --; no default qualification is inferred')
    out = args.results_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix='cognous-suite-') as temp:
        source = Path(temp) / 'source'
        subprocess.run(['git','clone','--quiet','--no-hardlinks','--no-checkout',str(args.source_root.resolve()),str(source)],check=True)
        subprocess.run(['git','-C',str(source),'checkout','--quiet','--detach',args.source_revision],check=True)
        report = install(args.suite,source,evidence=out/'source-identity.json')
        env = os.environ.copy()
        env['PYTHONDONTWRITEBYTECODE']='1'
        env['PYTHONPATH']=os.pathsep.join([str(source),str(source/'src'),env.get('PYTHONPATH','')])
        timed_out=False
        with (out/'execution.log').open('w') as stream:
            try:
                process=subprocess.Popen(command,cwd=source,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=(os.name=='posix'))
                code=process.wait(timeout=args.timeout)
            except subprocess.TimeoutExpired:
                timed_out=True;code=124
                if os.name=='posix':os.killpg(process.pid,signal.SIGKILL)
                else:process.kill()
                process.wait()
        (out/'command-result.json').write_text(json.dumps({'command':command,'exit_code':code,'timed_out':timed_out,'owning_source_commit':report['owning_source_commit'],'qualification_commit':report['qualification_commit'],'scope':'Command outcome only; inspect original suite gates, skips and assertions before any qualification claim.'},indent=2)+'\n')
        print((out/'execution.log').read_text())
        return code


if __name__ == '__main__':
    raise SystemExit(main())
