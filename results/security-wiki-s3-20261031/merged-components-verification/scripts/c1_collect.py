#!/usr/bin/env python3
"""C1/A: pytest --collect-only (nothing executed) with the runner's invocation, BEFORE tree vs AFTER (patched) tree, per suite-generation value."""
import os,subprocess,sys,hashlib,json
from pathlib import Path
BEFORE,AFTER,OUT,STUB=map(Path,sys.argv[1:5]); C=Path('/tmp/claude-0/sec/s3/scratch/comp')
def env(root,gen,stub=False):
    e={k:v for k,v in os.environ.items() if not k.startswith(('PYTEST_','V1_','SCN_','OBS_','GAX_','COGNOUS_','MOLTBOT_','UPSTREAM_','PYTHONPATH'))}
    paths=[C/'control_plane',C/'control_plane/src',C/'runtime',C/'replay/src',C/'evidence_pack/src',C/'odes/src',C/'exchange']
    if stub:paths.insert(0,STUB)
    e.update(PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',SCN_COMPONENTS_DIR=str(C),V1_VALIDATION_ID='current-stack-20261031',
      V1_PROFILE='process/security-runtime-current-stack-20261031.json',OBS_OUT='/tmp/obs-unused',
      GAX_RUNTIME_COMPATIBILITY_PROFILE='security-runtime-p2-20261018',MOLTBOT_SAFE_CONTROL_PLANE_ROOT=str(C/'control_plane'),MOLTBOT_SAFE_ROOT=str(C/'runtime'),
      UPSTREAM_MANIFEST_EXAMPLE=str(C/'manifest/examples/refund_integration_v1_1.manifest.json'),
      PYTHONPATH=os.pathsep.join(map(str,[root/'tools']+paths)))
    if gen:e['COGNOUS_SECURITY_RUNTIME_GENERATION']=gen
    return e
def collect(root,gen,suites,stub=False):
    cmd=[sys.executable,'-m','pytest','-q','-p','no:cacheprovider','-p','wiki_exchange_observer','--collect-only',*suites]
    r=subprocess.run(cmd,cwd=root,env=env(root,gen,stub),capture_output=True,text=True,timeout=900)
    ids=sorted(l.strip() for l in r.stdout.splitlines() if '::' in l and l.startswith('suites/'))
    return r,ids,cmd
OUT.mkdir(parents=True,exist_ok=True); summ={}
SU=['suites/wiki-derived','suites/security-runtime']
for gen in [None,'security','f5b','p4','p2','cur','bogus']:
  for label,root,stub in (('before',BEFORE,False),('after',AFTER,False),('before',BEFORE,True),('after',AFTER,True)):
    if gen not in('cur',) and stub: continue
    tag=f"{gen or 'unset'}{'+curstub' if stub else ''}"
    r,ids,cmd=collect(root,gen,SU,stub)
    (OUT/f'collect-{tag}-{label}.raw.txt').write_text(' '.join(cmd)+'\n--- rc=%d\n'%r.returncode+r.stdout+'\n--- stderr\n'+r.stderr)
    (OUT/f'collect-{tag}-{label}.ids').write_text('\n'.join(ids)+'\n')
    last=[l for l in r.stdout.splitlines() if l.strip()][-1:] 
    err=[l for l in r.stdout.splitlines() if l.startswith('E ')][:2]
    summ.setdefault(tag,{})[label]={'rc':r.returncode,'n_ids':len(ids),'sha256':hashlib.sha256('\n'.join(ids).encode()).hexdigest()[:16],'tail':last,'errors':err}
(OUT/'c1-summary.json').write_text(json.dumps(summ,indent=1))
b41=[l.strip() for l in Path(sys.argv[5]).read_text().splitlines() if l.strip()]
res={'blocked41_count':len(b41),'unique':len(set(b41))}
for tag in summ:
    for label in('before','after'):
        p=OUT/f'collect-{tag}-{label}.ids'
        if p.exists():
            got=set(p.read_text().split()); res[f'{tag}/{label}/missing_of_41']=len(set(b41)-got)
print(json.dumps(summ,indent=1)); print(json.dumps(res,indent=1))
(OUT/'c1-blocked41.json').write_text(json.dumps(res,indent=1))
