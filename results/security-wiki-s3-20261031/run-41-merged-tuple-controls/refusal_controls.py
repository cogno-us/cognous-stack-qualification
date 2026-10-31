import json,subprocess,shutil,os,sys,copy
S='/home/claude/scratch-refuse'; R=S+'/root'; N='current-stack-S3-20261031'; REAL='/home/claude/wt-s3'
W='/home/claude/cs-components-s3run'
P=f'{R}/process/security-runtime-{N}.json'; D=f'{R}/process/v1-validation/{N}/'
files=[P,D+'runner-tuple.json',D+'freeze-manifest.json',D+'tuple.json']
orig={f:open(f).read() for f in files}
def reset():
    for f,c in orig.items(): open(f,'w').write(c)
def J(f): return json.load(open(f))
def W_(f,o): open(f,'w').write(json.dumps(o,indent=1))
def comps(over={}):
    d=S+'/comps_run'; shutil.rmtree(d,ignore_errors=True); os.makedirs(d)
    for n in 'control_plane runtime replay evidence_pack odes exchange manifest registry'.split():
        os.symlink(over.get(n,f'{W}/{n}'),f'{d}/{n}')
    return d
def run(name,mut,over={},extra=[]):
    reset(); mut()
    cmd=['python3','-I','-B',f'{R}/tools/run_wiki_s3.py','--tuple',D+'runner-tuple.json','--components',comps(over),'--out',R+'/results/refuse-out','--dry-check']
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
    r=subprocess.run(cmd,env=env,capture_output=True,text=True,cwd=R)
    out=(r.stdout+r.stderr).strip().replace('\n',' ')[:600]
    g=subprocess.run(['python3','-I','-B',f'{R}/tools/s3_tuple_guard.py','--tuple',D+'runner-tuple.json','--components',S+'/comps_run'],env=env,capture_output=True,text=True,cwd=R)
    gout=(g.stdout+g.stderr).strip().replace('\n',' ')[:260]
    print(f'## {name}\nrunner --dry-check rc={r.returncode}: {out[:230]}\nguard rc={g.returncode}: {gout}\n',flush=True)
    return (r.returncode,g.returncode)
def tup(f):
    t=J(D+'runner-tuple.json'); f(t); W_(D+'runner-tuple.json',t)
def prof(f):
    t=J(P); f(t); W_(P,t)
def man(f):
    t=J(D+'freeze-manifest.json'); f(t); W_(D+'freeze-manifest.json',t)
def allthree(pk,mk,tk,val):
    def m():
        tup(lambda t:t.__setitem__(tk,val)); prof(lambda t:t['components'][pk].__setitem__('revision',val)); man(lambda t:t['components_subject'][mk].__setitem__('sha',val))
    return m
def xprof(val):
    def m():
        tup(lambda t:t.__setitem__('exchange_compatibility_profile',val)); prof(lambda t:t.__setitem__('exchange_compatibility_profile',val)); man(lambda t:t['profile'].__setitem__('exchange_compatibility_profile',val))
    return m
res={}
res['0 control: unmodified scratch copy']=run('0 control: unmodified scratch copy (must pass)',lambda:None)
res['1a']=run('1a MISSING component revision: tuple lacks "odes"',lambda:tup(lambda t:t.pop('odes')))
res['1b']=run('1b MISSING component revision: profile exchange.revision removed',lambda:prof(lambda t:t['components']['exchange'].pop('revision')))
res['1c']=run('1c MISSING component revision: tuple.exchange empty string',lambda:tup(lambda t:t.__setitem__('exchange','')))
res['1d']=run('1d component given by branch name not SHA: tuple.replay="main"',lambda:tup(lambda t:t.__setitem__('replay','main')))
res['1e']=run('1e component given by short prefix: tuple.odes="77fd7a1c"',lambda:tup(lambda t:t.__setitem__('odes','77fd7a1c')))
res['2a']=run('2a UNRESOLVED placeholder in tuple.exchange',lambda:tup(lambda t:t.__setitem__('exchange','PLACEHOLDER:PENDING exchange merge SHA')))
res['2b']=run('2b UNRESOLVED placeholder in profile exchange_compatibility_profile',lambda:prof(lambda t:t.__setitem__('exchange_compatibility_profile','PLACEHOLDER:name')))
res['2c']=run('2c UNRESOLVED placeholder in freeze-manifest hub head',lambda:man(lambda t:t['identities']['hub'].__setitem__('head','PLACEHOLDER:hub head SHA at freeze')))
res['2d']=run('2d TEMPLATE marker left in tuple validation_id',lambda:tup(lambda t:t.__setitem__('validation_id','current-stack-S3-TEMPLATE')))
res['3a']=run('3a WRONG Exchange profile: original security-runtime-current-20261031 (consistent in tuple/profile/manifest)',xprof('security-runtime-current-20261031'))
res['3b']=run('3b WRONG Exchange profile: typo security-runtime-current-20261031-r3 (consistent in all three)',xprof('security-runtime-current-20261031-r3'))
res['3c']=run('3c WRONG Exchange profile: tuple says r2, profile file says original (inconsistent)',lambda:prof(lambda t:t.__setitem__('exchange_compatibility_profile','security-runtime-current-20261031')))
res['3d']=run('3d WRONG Exchange profile: p2 profile security-runtime-p2-20261018 (consistent in all three)',xprof('security-runtime-p2-20261018'))
res['4a']=run('4a MIXED generation: Replay = P2 40012b8c (tuple+profile+manifest consistent, checkout at 40012b8c)',allthree('replay','replay_bundle','replay','40012b8c174c6f25685bd5d9bc93ff46cc9a5842'),{'replay':S+'/alt/replay_p2'})
res['4b']=run('4b MIXED generation: ODES = previous 1a5e1d30 (all consistent, checkout at 1a5e1d30)',allthree('odes','odes','odes','1a5e1d300250d832e611633f0bf8f762e398c0ec'),{'odes':S+'/alt/odes_old'})
res['4c']=run('4c MIXED generation: tuple Replay=P2 40012b8c but config files still d395e37c',lambda:tup(lambda t:t.__setitem__('replay','40012b8c174c6f25685bd5d9bc93ff46cc9a5842')),{'replay':S+'/alt/replay_p2'})
res['4d']=run('4d MIXED generation: checkouts Replay at P2 40012b8c while tuple/config say d395e37c',lambda:None,{'replay':S+'/alt/replay_p2'})
res['5a']=run('5a UNVERIFIED/DIRTY source: manifest checkout has a modified tracked file',lambda:None,{'manifest':S+'/alt/manifest_dirty'})
res['5b']=run('5b UNVERIFIED source identity: ODES checkout HEAD (1a5e1d30) != tuple SHA 77fd7a1c',lambda:None,{'odes':S+'/alt/odes_old'})
res['5c']=run('5c UNVERIFIED source: component directory missing (registry)',lambda:None,{'registry':S+'/nonexistent'})
res['5d']=run('5d UNVERIFIED source: freeze-manifest exchange sha differs from tuple (config vs tuple)',lambda:man(lambda t:t['components_subject']['gax_imx_transport'].__setitem__('sha','0'*40)))
res['6']=run('6 cur patch absent: SUITE_GENERATIONS without cur',lambda:open(R+'/tools/run_security_runtime.py','w').write(open(REAL+'/tools/run_security_runtime.py').read().replace(", 'cur'}","}")))
reset()
shutil.copy(REAL+'/tools/run_security_runtime.py',R+'/tools/run_security_runtime.py')
print('SUMMARY',json.dumps(res))
