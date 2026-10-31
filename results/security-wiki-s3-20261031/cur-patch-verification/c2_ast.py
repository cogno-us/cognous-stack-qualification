#!/usr/bin/env python3
"""Conditions B,C,F,I (AST): compare the two patched files BEFORE vs AFTER. Prints a report; exit 1 on any failure."""
import ast,copy,json,os,re,subprocess,sys
from pathlib import Path
BEFORE_ROOT,AFTER_ROOT,OUT=Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]); PATCH=Path(sys.argv[4])
FILES=['suites/security-runtime/test_security_runtime_chain.py','tools/run_security_runtime.py']
fails=[]; rep=[]
def P(*a):
    s=' '.join(map(str,a)); rep.append(s); print(s)
def chk(name,ok,detail=''):
    P(('PASS ' if ok else 'FAIL ')+name+(' '+detail if detail else ''))
    if not ok: fails.append(name)
def is_cur_cmp(t):
    return isinstance(t,ast.Compare) and isinstance(t.left,ast.Name) and t.left.id=='GENERATION' and len(t.comparators)==1 and isinstance(t.comparators[0],ast.Constant) and t.comparators[0].value=='cur' and isinstance(t.ops[0],ast.Eq)
class Strip(ast.NodeTransformer):
    """Remove ONLY the added cur clauses: (1) an If whose test is GENERATION=='cur' (replaced by its else-body), (2) the Constant 'cur' inside a set/frozenset literal."""
    n=0
    def visit_If(self,node):
        self.generic_visit(node)
        if is_cur_cmp(node.test):
            Strip.n+=1; return node.orelse
        return node
    def visit_Constant(self,node):
        return node
    def visit_Call(self,node):
        self.generic_visit(node)
        if isinstance(node.func,ast.Name) and node.func.id=='frozenset' and node.args and isinstance(node.args[0],ast.Set):
            before=len(node.args[0].elts)
            node.args[0].elts=[e for e in node.args[0].elts if not(isinstance(e,ast.Constant) and e.value=='cur')]
            Strip.n+=before-len(node.args[0].elts)
        return node
def facts(src):
    t=ast.parse(src); f={}
    f['defs']={n.name:ast.dump(n) for n in ast.walk(t) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
    f['tests']=[n.name for n in ast.walk(t) if isinstance(n,ast.FunctionDef) and n.name.startswith('test')]
    f['asserts']=[ast.unparse(n) for n in ast.walk(t) if isinstance(n,ast.Assert)]
    f['assert_dumps']=[ast.dump(n) for n in ast.walk(t) if isinstance(n,ast.Assert)]
    f['decorators']=[(n.name,ast.unparse(d)) for n in ast.walk(t) if isinstance(n,(ast.FunctionDef,ast.ClassDef)) for d in n.decorator_list]
    f['markers']=[x for x in f['decorators'] if 'mark' in x[1] or 'parametrize' in x[1]]
    f['fixtures']=[x for x in f['decorators'] if 'fixture' in x[1]]
    f['pytestmark']=[ast.unparse(n) for n in ast.walk(t) if isinstance(n,ast.Assign) and any(getattr(x,'id','')=='pytestmark' for x in n.targets)]
    def callname(c):return ast.unparse(c.func)
    f['raises']=[ast.unparse(n) for n in ast.walk(t) if isinstance(n,ast.Call) and callname(n).endswith(('raises','warns'))]
    f['raise_stmts']=[ast.unparse(n) for n in ast.walk(t) if isinstance(n,ast.Raise)]
    f['match_kw']=[ast.unparse(k) for n in ast.walk(t) if isinstance(n,ast.Call) for k in n.keywords if k.arg=='match']
    f['refuse_calls']=[ast.unparse(n) for n in ast.walk(t) if isinstance(n,ast.Call) and re.search('refus|reject|forbid|deny',callname(n),re.I)]
    f['neg_helpers']={k:v for k,v in f['defs'].items() if re.search('refus|reject|raises|negative|forbid|deny|tamper|forg|invalid|mutat',k,re.I)}
    f['is_none']=[ast.unparse(n) for n in ast.walk(t) if isinstance(n,ast.Assert) and re.search(r'\bis None\b|== None',ast.unparse(n.test))]
    f['skips']=[ast.unparse(n) for n in ast.walk(t) if (isinstance(n,ast.Call) and re.search('skip|xfail|importorskip',callname(n))) or (isinstance(n,ast.Attribute) and n.attr in('skip','skipif','xfail'))]
    f['constants']=sorted(repr(n.value) for n in ast.walk(t) if isinstance(n,ast.Constant))
    f['imports']=[ast.unparse(n) for n in ast.walk(t) if isinstance(n,(ast.Import,ast.ImportFrom))]
    return t,f
full={}
for fn in FILES:
    bs=subprocess.check_output(['git','-C',str(BEFORE_ROOT),'show',os.environ.get('BASE_REF','HEAD')+':'+fn],text=True); as_=(AFTER_ROOT/fn).read_text()
    bt,bf=facts(bs); at,af=facts(as_)
    P('\n=====',fn,'=====')
    Strip.n=0; st=Strip().visit(copy.deepcopy(at)); ast.fix_missing_locations(st)
    chk(f'B1 ast.dump(after minus added cur clauses) == ast.dump(before) [{Strip.n} clause(s) removed]',ast.dump(st)==ast.dump(bt))
    chk('B1b exactly the expected number of cur clauses stripped',Strip.n==(2 if 'chain' in fn else 1),str(Strip.n))
    # control: stripping nothing must NOT equal (patch is non-empty)
    chk('B1c control: unstripped after != before (patch is not vacuous)',ast.dump(at)!=ast.dump(bt))
    extra=[i for i in af['imports'] if i not in bf['imports']]
    chk('imports: all before-imports kept; only extra import is the one inside the cur clause: '+str(extra),all(i in af['imports'] for i in bf['imports']) and len(extra)==(1 if 'chain' in fn else 0) and all('CUR_REVISION' in i for i in extra))
    for k in ('tests','asserts','assert_dumps','decorators','markers','fixtures','pytestmark','raises','raise_stmts','match_kw','refuse_calls','is_none','skips'):
        chk(f'{k}: identical before/after (n={len(bf[k])}/{len(af[k])})',bf[k]==af[k])
    from collections import Counter
    cb,ca=Counter(bf['constants']),Counter(af['constants']); added=ca-cb; removed=cb-ca
    chk(f'B2 literals: removed={dict(removed)} added={dict(added)} (allowed: only \'cur\' x{2 if "chain" in fn else 1})',not removed and set(added)=={"'cur'"} and added["'cur'"]==(2 if 'chain' in fn else 1))
    dd=[k for k in bf['defs'] if bf['defs'][k]!=af['defs'].get(k)]; chk(f'defs changed: {dd} (allowed: odes_generation only in chain file, none in tool)',dd==(['odes_generation'] if 'chain' in fn else []) and set(bf['defs'])==set(af['defs']))
    nh=[k for k in bf['neg_helpers'] if bf['neg_helpers'][k]!=af['defs'].get(k)]; chk(f'F negative-expectation helpers unchanged: {list(bf["neg_helpers"])}',not nh)
    full[fn]={'before':{k:v for k,v in bf.items() if k not in('defs','assert_dumps','neg_helpers')},'after_equals_before_except':'cur clauses'}
    full[fn]['before']['def_names']=sorted(bf['defs']); full[fn]['before']['neg_helper_names']=sorted(bf['neg_helpers'])
    P('  tests (%d): %s'%(len(bf['tests']),', '.join(bf['tests'])))
    P('  asserts: %d  markers: %d  raises: %d  match=: %d  skips: %d'%(len(bf['asserts']),len(bf['markers']),len(bf['raises']),len(bf['match_kw']),len(bf['skips'])))
# patch text checks (I, C5)
pt=PATCH.read_text(); added=[l[1:] for l in pt.splitlines() if l.startswith('+') and not l.startswith('+++')]; removed=[l[1:] for l in pt.splitlines() if l.startswith('-') and not l.startswith('---')]
P('\n===== patch text =====')
chk('I patch has no skip/skipif/xfail/importorskip/pytest.skip/try/except/fallback',not re.search(r'skip|xfail|importorskip|try:|except|getattr\(|\.get\(',pt,re.I))
chk('C5 no 40-hex or 7+hex SHA literal in added lines',not re.search(r'\b[0-9a-f]{7,40}\b',' '.join(re.sub(r'[A-Za-z_]+','',l) if False else l for l in added if re.search(r'["\'][0-9a-f]{7,}["\']',l))))
chk('C5 added lines contain no digits-only/hex string literal',not any(re.search(r"['\"][0-9a-f]{7,}['\"]",l) for l in added))
P('  added lines:',len(added),' removed lines:',len(removed)); P('  files in patch:',re.findall(r'^diff --git a/(\S+)',pt,re.M))
for l in added:P('  +',l)
for l in removed:P('  -',l)
chk('C5 patch = 2 files, +5/-1',re.findall(r'^diff --git a/(\S+)',pt,re.M)==FILES and len(added)==5 and len(removed)==1, f'+{len(added)}/-{len(removed)}')
chk('C5 removed line is only the SUITE_GENERATIONS frozenset line (replaced with identical + cur)',removed==["SUITE_GENERATIONS = frozenset({'security', 'f5b', 'p4', 'p2'})"])
OUT.write_text(json.dumps(full,indent=1,default=str)); Path(str(OUT)+'.report.txt').write_text('\n'.join(rep)+'\n')
print('\nFAILS:',fails); sys.exit(1 if fails else 0)
