import csv,glob,json,collections,xml.etree.ElementTree as ET,os
R='/home/claude/cs-run/run2'; OUT='/home/claude/cs-pkg'
tuple_=json.load(open('/tmp/claude-0/sec/current-tuple.json'))['components']
HARNESS5={'l06_022_stop_journal','l15_019_destination_restored_without_authority_state','l09_004_the_destination_credential_is_narrower','l06_018_an_expired_message','l06_040_the_schema_check_does_not_reject'}
import glob as _g
OBS={}
for _f in _g.glob(R+'/*.obs.json'): OBS.update(json.load(open(_f)))
rows=[]
for f in sorted(glob.glob(R+'/test_*.junit.xml')):
    for tc in ET.parse(f).getroot().iter('testcase'):
        props={p.get('name'):p.get('value') for p in tc.iter('property')}
        st='PASS';cls='';obs='';
        for k in('failure','error','skipped'):
            e=tc.find(k)
            if e is not None:
                txt=(e.text or '')+(e.get('message') or '')
                if k=='skipped': st='SKIPPED';cls='n/a'
                elif 'candidate source identity mismatch' in txt:
                    st='BLOCKED';cls='INTEGRATION FAILURE';obs='Exchange gax_ref_runtime._verify_refusal_profile_sources: candidate source identity mismatch (Exchange hard-pins historical Control Plane/Runtime/Replay/ODES/Pack revisions per compatibility profile; no profile for the current tuple)'
                else:
                    st='FAIL';cls='HARNESS FAILURE (pre-existing: identical failure at the historical pins, see hist-diag)' if any(h in tc.get('name') for h in HARNESS5) else 'UNCLASSIFIED'
                    obs=(e.get('message') or txt)[:300].replace('\n',' ')
        _k=[v for n,v in OBS.items() if n.split('::')[-1]==tc.get('name') and n.split('/')[-1].split('.py')[0]==os.path.basename(f).replace('.junit.xml','')]
        if st=='PASS' and _k and _k[0]['raised']>0:
            st='BLOCKED';cls='INTEGRATION FAILURE (vacuous PASS reclassified: the test passed while the Exchange source-identity check refused; it accepts any exception)';obs='observer: identity check raised %d time(s) in this test'%_k[0]['raised']
        rows.append(dict(module=os.path.basename(f).replace('.junit.xml',''),test=tc.get('name'),wiki_case=props.get('wiki_case',''),status=st,failure_class=cls,observed=obs,time_s=tc.get('time')))
with open(OUT+'/per-test.csv','w',newline='') as fh:
    w=csv.DictWriter(fh,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
bycase=collections.defaultdict(list)
for r in rows:
    if r['wiki_case']: bycase[r['wiki_case']].append(r)
cases=list(csv.DictReader(open('/tmp/claude-0/sec/handoff/D-CS-classification.csv')))
out=[];cnt=collections.Counter()
for c in cases:
    ts=bycase.get(c['id'],[])
    if c['classification'].startswith('NOT_APPLICABLE'):
        v='OUT OF SCOPE';fc='';n=''
        if ts: v='ERROR-test-for-out-of-scope';
    elif not ts: v='NOT TESTED';fc='MISSING COVERAGE (in scope, no test in the harness)';n='0'
    else:
        s=collections.Counter(t['status'] for t in ts)
        n=f"{s['PASS']}P/{s['FAIL']}F/{s['BLOCKED']}B of {len(ts)}"
        if s['FAIL']: v='FAIL'
        elif s['BLOCKED']: v='BLOCKED'
        else: v='PASS'
        fc='; '.join(sorted({t['failure_class'] for t in ts if t['failure_class']}))
    cnt[v]+=1
    out.append(dict(id=c['id'],layer=c['layer'],title=c['title'],applicability=c['classification'],verdict=v,tests=n,failure_class=fc,newly_applicable_candidate=c['newly_applicable_candidate'],original_requirement_ref=f"scenarios/ai-security-wiki/pages (case {c['id']}) + applicability.json",current_stack_revision='see TUPLE: CP b19c47dd, Runtime f7a55e2a, Replay 40012b8c, Pack 7b9511f2, ODES 1a5e1d30, Exchange 7f7569b0, Manifest fa170815',registry_revision='6b96a9a658923954433dc1a4c13626fa5145b9c7 (pinned; NOT exercised by any Wiki test)',evidence='per-test.csv + raw junit/logs'))
with open(OUT+'/per-case.csv','w',newline='') as fh:
    w=csv.DictWriter(fh,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
tc=collections.Counter(r['status'] for r in rows)
print('tests',len(rows),dict(tc)); print('cases',len(out),dict(cnt))
print('inscope verdicts',collections.Counter(o['verdict'] for o in out if o['applicability'] in('APPLICABLE','PARTLY_COVERED')))
print('by applicability x verdict',collections.Counter((o['applicability'],o['verdict']) for o in out if o['applicability']!='NOT_APPLICABLE'))
json.dump(dict(tests=dict(tc),cases=dict(cnt)),open(OUT+'/counts.json','w'))
