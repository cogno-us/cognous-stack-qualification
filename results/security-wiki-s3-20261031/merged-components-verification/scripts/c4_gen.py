#!/usr/bin/env python3
"""Condition E (C4): import-time generation resolution + odes_generation(), BEFORE vs AFTER tree, per GENERATION value (module imported, NO test executed)."""
import os,subprocess,sys,json
from pathlib import Path
BEFORE,AFTER,OUT,STUB=map(Path,sys.argv[1:5]); C=Path('/tmp/claude-0/sec/s3/scratch/comp')
CHILD='''
import importlib.util,json,sys,os
sys.path.insert(0,os.environ["ROOTDIR"]+"/suites/security-runtime")
spec=importlib.util.spec_from_file_location("chainmod",os.environ["ROOTDIR"]+"/suites/security-runtime/test_security_runtime_chain.py")
r={}
try:
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    r["import"]="OK"; r["CP"]=m.CONTROL_PLANE_RUNTIME_AUTHORITY_REVISION; r["MB"]=m.MOLTBOT_RUNTIME_AUTHORITY_REVISION
    try:
        a,b=m.odes_generation(); r["odes"]=[json.loads(json.dumps(a,default=lambda x:sorted(x) if isinstance(x,(set,frozenset)) else str(x))),str(b)]
    except BaseException as e: r["odes_error"]=type(e).__name__+": "+str(e)
except BaseException as e: r["import"]="ERROR "+type(e).__name__+": "+str(e)
print("RESULT "+json.dumps(r,sort_keys=True))
'''
def run(root,gen,stub):
    e={k:v for k,v in os.environ.items() if not k.startswith(('PYTEST_','V1_','SCN_','OBS_','GAX_','COGNOUS_','MOLTBOT_','UPSTREAM_','PYTHONPATH'))}
    paths=[C/'control_plane',C/'control_plane/src',C/'runtime',C/'replay/src',C/'evidence_pack/src',C/'odes/src',C/'exchange']
    if stub:paths.insert(0,STUB)
    e.update(PYTHONDONTWRITEBYTECODE='1',ROOTDIR=str(root),MOLTBOT_SAFE_ROOT=str(C/'runtime'),MOLTBOT_SAFE_CONTROL_PLANE_ROOT=str(C/'control_plane'),PYTHONPATH=os.pathsep.join(map(str,paths)),COGNOUS_SECURITY_RUNTIME_GENERATION=gen)
    if gen=='__unset__':del e['COGNOUS_SECURITY_RUNTIME_GENERATION']
    r=subprocess.run([sys.executable,'-c',CHILD],cwd=root,env=e,capture_output=True,text=True,timeout=300)
    line=[l for l in r.stdout.splitlines() if l.startswith('RESULT ')]
    return json.loads(line[0][7:]) if line else {'import':'NO RESULT','stderr':r.stderr[-300:]}
res={};bad=[]
for gen in ['__unset__','security','f5b','p4','p2','bogus','cur']:
    for stub in [False]:
        b=run(BEFORE,gen,stub);a=run(AFTER,gen,stub);k=f"{gen}{'+curstub' if stub else ''}"
        res[k]={'before':b,'after':a}
        same=(a==b)
        expect_diff=(gen=='cur')   # cur is the ONLY value allowed to differ
        ok = (not same) if expect_diff else same
        print(('PASS' if ok else 'FAIL'),k,'identical' if same else 'DIFFERENT'); print('   before:',json.dumps(b)[:420]); print('   after: ',json.dumps(a)[:420])
        if not ok:bad.append(k)

cu=res['cur']['after']; p2=res['p2']['after']
T=dict(manifest='fa170815ef96a54c233d0dd9da821b60debabf8b',replay='d395e37c443fedf1bf6b9a4651338b7b7de4a553',control_plane='b19c47ddd020409d24e52e70b11359c46265edbb',moltbot_safe='f7a55e2a8494801e49193f9f46935f0a971c248d')
chk=[('cur on MERGED Replay d395e37c + ODES 77fd7a1c imports OK (real components, no stub)', cu.get('import')=='OK'),
 ('cur CP/Runtime constants == tuple (b19c47dd / f7a55e2a)', cu.get('CP')==T['control_plane'] and cu.get('MB')==T['moltbot_safe']),
 ('cur != p2 labels', cu.get('CP')!=p2.get('CP') and cu.get('MB')!=p2.get('MB')),
 ('odes_generation() cur == (CUR_REVISIONS == tuple, CUR_PROFILE_VERSION 0.2.7 cur-candidate)', cu.get('odes')==[T,'odes-cognous-stack-export-0.2.7-security-runtime-cur-candidate'] or (cu.get('odes') and cu['odes'][0]==T and cu['odes'][1].endswith('0.2.7-security-runtime-cur-candidate'))),
 ('cur BEFORE patch fails loudly as unsupported generation', res['cur']['before']['import'].endswith('unsupported security runtime generation')),
 ('unsupported value still raises RuntimeError after patch', res['bogus']['after']['import']=='ERROR RuntimeError: unsupported security runtime generation')]
for n,ok in chk:
    print(('PASS' if ok else 'FAIL'),n)
    if not ok:bad.append(n)
OUT.write_text(json.dumps(res,indent=1)); print('cur after:',json.dumps(cu)[:600]); print('FAILS:',bad); sys.exit(1 if bad else 0)
