#!/usr/bin/env python3
"""Condition E (C4): import-time generation resolution + odes_generation(), BEFORE vs AFTER tree, per GENERATION value (module imported, NO test executed)."""
import os,subprocess,sys,json
from pathlib import Path
BEFORE,AFTER,OUT,STUB=map(Path,sys.argv[1:5]); C=Path('/home/claude/cs-components')
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
    for stub in ([False,True] if gen=='cur' else [False]):
        b=run(BEFORE,gen,stub);a=run(AFTER,gen,stub);k=f"{gen}{'+curstub' if stub else ''}"
        res[k]={'before':b,'after':a}
        same=(a==b)
        expect_diff=(gen=='cur')   # cur is the ONLY value allowed to differ
        ok = (not same) if expect_diff else same
        print(('PASS' if ok else 'FAIL'),k,'identical' if same else 'DIFFERENT'); print('   before:',json.dumps(b)[:420]); print('   after: ',json.dumps(a)[:420])
        if not ok:bad.append(k)
# explicit negative-property checks for cur
cu=res['cur']['after']; cs=res['cur+curstub']['after']; p2=res['p2']['after']
chk=[('cur on older Replay (real 40012b8) fails loudly at import, with ImportError naming CONTROL_PLANE_CUR_REVISION', cu['import'].startswith('ERROR ImportError') and 'CONTROL_PLANE_CUR_REVISION' in cu['import']),
 ('cur on older Replay does NOT resolve to p2 labels', cu.get('CP') is None and cu.get('CP')!=p2['CP']),
 ('cur BEFORE patch fails loudly as unsupported generation', res['cur']['before']['import'].endswith('unsupported security runtime generation')),
 ('cur with CUR names present resolves to the CUR constants, not p2 labels', cs.get('CP')=='b19c47ddd020409d24e52e70b11359c46265edbb' and cs.get('MB')=='f7a55e2a8494801e49193f9f46935f0a971c248d' and cs['CP']!=p2['CP'] and cs['MB']!=p2['MB']),
 ('unsupported value still raises RuntimeError(unsupported security runtime generation) after patch', res['bogus']['after']['import']=='ERROR RuntimeError: unsupported security runtime generation')]
for n,ok in chk:
    print(('PASS' if ok else 'FAIL'),n)
    if not ok:bad.append(n)
OUT.write_text(json.dumps(res,indent=1)); print('FAILS:',bad); sys.exit(1 if bad else 0)
