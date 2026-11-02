#!/usr/bin/env python3
"""Conditions D,G,H,J(partial),C5-guard: BEFORE tree (git HEAD of BEFORE_ROOT) vs AFTER tree (BEFORE + patch). Args: BEFORE_ROOT AFTER_ROOT OUT PATCH"""
import ast,hashlib,re,subprocess,sys,json,os
from pathlib import Path
B,A,OUT,PATCH=map(Path,sys.argv[1:5]); fails=[]; rep=[]
def P(s=''):rep.append(s);print(s)
def chk(n,ok,d=''):
    P(('PASS ' if ok else 'FAIL ')+n+(' '+d if d else ''))
    if not ok:fails.append(n)
def files(root,sub):
    return sorted(str(p.relative_to(root)) for p in (root/sub).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
def sh(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
patched=re.findall(r'^diff --git a/(\S+)',PATCH.read_text(),re.M)
# whole tracked tree comparison: git ls-files of BEFORE vs files present in AFTER (AFTER shares non-suites/tools via symlink, so compare suites+tools byte-wise, rest is the same inode tree)
tracked=subprocess.check_output(['git','-C',str(B),'ls-files','suites','tools'],text=True).split('\n'); tracked=[t for t in tracked if t]
after_files=set(files(A,'suites')+files(A,'tools'))
chk('J0 AFTER suites/+tools/ has exactly the tracked file set of BEFORE (no file added/removed)',set(tracked)==after_files,f'{len(tracked)} vs {len(after_files)}')
diffs=[t for t in tracked if (B/t).exists() and sh(B/t)!=sh(A/t)]
P('files under suites/ and tools/ whose bytes differ BEFORE vs AFTER: '+str(diffs))
chk('J1/C2 only the 2 patch files differ under suites/ and tools/',sorted(diffs)==sorted(patched))
chk('J2 untracked/ignored extras none',set(after_files)-set(tracked)==set(),str(sorted(set(after_files)-set(tracked))))
# D/H: verdict / classification code inventory
pat=re.compile(r'\b(PASS|FAIL|BLOCKED|vacuous|vacuity|verdict|classif\w*)\b',re.I)
inv={}
for sub in ('tools','tests','suites'):
    for p in (B/sub).rglob('*.py'):
        if '__pycache__' in p.parts:continue
        n=len(pat.findall(p.read_text(errors='replace')))
        if n:inv[str(p.relative_to(B))]=n
cls=[k for k in inv if re.search(r'verdict|classif|observer|analy|summar|obs_|conftest|gate|result',k,re.I)]
P('files mentioning PASS/FAIL/BLOCKED/vacuous/verdict/classif (count): '+str(len(inv))); P('classification/verdict-like files by name: '+', '.join(sorted(cls)))
chk('D/H none of the verdict/classification-like files is in the patch',not (set(cls)&set(patched)))
added=[l for l in PATCH.read_text().splitlines() if l[:1] in '+-' and l[:3] not in('+++','---')]
P('pre-existing token hits in patched files (BEFORE): '+str({f:inv.get(f,0) for f in patched}))
for f in patched:
    for ln in (B/f).read_text().splitlines():
        if pat.search(ln):P('   '+f+': '+ln.strip()[:150])
chk('D/H no PASS/FAIL/BLOCKED/vacuous/verdict/classif token in any line the patch adds or removes',not any(pat.search(l) for l in added))
plug=['tools/wiki_exchange_observer.py']+[str(p.relative_to(B)) for p in B.rglob('conftest.py') if '.git' not in p.parts and 'results' not in p.relative_to(B).parts[:1]]
bad=[p for p in plug if (B/p).exists() and sh(B/p)!=sh(A/p)]
P('conftest/plugin/observer files checked (%d): %s'%(len(plug),', '.join(plug)))
chk('H conftest.py / pytest plugins / observer byte-identical (incl. no_network fixture)',not bad)
chk('H pytest.ini unchanged',sh(B/'pytest.ini')==sh(A/'pytest.ini'))
chk('H tools/run_wiki_s3.py (junit/observer/verdict-note handling) unchanged by patch','tools/run_wiki_s3.py' not in patched)
# G: fixtures / parametrize / negative-fixture references across both suites
G={}
for sd in ('suites/wiki-derived','suites/security-runtime'):
    for rel in files(B,sd):
        if not rel.endswith('.py'):continue
        for tag,root in(('before',B),('after',A)):
            src=(root/rel).read_text(); t=ast.parse(src)
            fx=[n.name for n in ast.walk(t) if isinstance(n,ast.FunctionDef) and any('fixture' in ast.unparse(d) for d in n.decorator_list)]
            pz=[ast.unparse(d) for n in ast.walk(t) if isinstance(n,ast.FunctionDef) for d in n.decorator_list if 'parametrize' in ast.unparse(d)]
            neg=sorted(set(re.findall(r'\b\w*(?:negative|adversar|forged|tamper|refus|reject|substitut)\w*\b',src,re.I)))
            G.setdefault(rel,{})[tag]={'fixtures':fx,'parametrize':pz,'neg_refs':neg,'sha':hashlib.sha256(src.encode()).hexdigest()[:12]}
nf=sum(len(v['before']['fixtures']) for v in G.values()); npz=sum(len(v['before']['parametrize']) for v in G.values()); nn=sum(len(v['before']['neg_refs']) for v in G.values())
P(f'G inventory over {len(G)} .py files: fixtures={nf} parametrize decorators={npz} negative-reference identifiers={nn}')
chk('G fixture/parametrize/negative-ref inventory identical before/after for every file',all(v['before']['fixtures']==v['after']['fixtures'] and v['before']['parametrize']==v['after']['parametrize'] and v['before']['neg_refs']==v['after']['neg_refs'] for v in G.values()))
chg=[r for r,v in G.items() if v['before']['sha']!=v['after']['sha']]; P('G files with different bytes: '+str(chg))
chk('G only the chain test file differs among suites/wiki-derived + suites/security-runtime .py',chg==['suites/security-runtime/test_security_runtime_chain.py'])
nonpy=[r for r in files(B,'suites/wiki-derived')+files(B,'suites/security-runtime') if not r.endswith('.py') and sh(B/r)!=sh(A/r)]
chk('G non-.py data files in those suites identical',not nonpy)
# C5 runner guard
for tag,root,expect in (('BEFORE (unpatched)',B,False),('AFTER (patched)',A,True)):
    r=subprocess.run([sys.executable,'-c',"import sys;sys.path.insert(0,'tools');import run_wiki_s3 as r\ntry:\n r.require_cur_patch();print('ACCEPTED')\nexcept r.Refuse as e:print('REFUSED',str(e)[:90])"],cwd=root,capture_output=True,text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
    P(f'  require_cur_patch on {tag}: {r.stdout.strip()} {r.stderr.strip()[-200:]}')
    chk(f'C5 runner guard require_cur_patch {"accepts" if expect else "refuses"} {tag}',('ACCEPTED' in r.stdout)==expect)
OUT.write_text(json.dumps({'G':G,'classification_inventory':inv},indent=1)); Path(str(OUT)+'.report.txt').write_text('\n'.join(rep)+'\n')
print('FAILS:',fails); sys.exit(1 if fails else 0)
