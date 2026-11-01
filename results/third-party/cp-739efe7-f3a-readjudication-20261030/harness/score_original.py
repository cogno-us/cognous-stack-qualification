"""Re-score ORIGINAL A-main4 raw rows (read-only) under reading (i-A), (i-B) and the partial (ii) facts the original rows can support. Criteria are those frozen in the protocol."""
import json,re,collections,sys
rows=[json.loads(l) for l in open('/tmp/claude-0/ev/runs/A-main4/f3a_evidence.jsonl')]
CODE='authorization_binding_changed'
def cases(prefix):
    return [(i+1,r) for i,r in enumerate(rows) if r.get('case','').startswith(prefix)]
pin=collections.defaultdict(dict)
for i,r in enumerate(rows,1):
    c=r.get('case','')
    m=re.match(r'A19_pin_export_refuses_per_perturbed_member\[pin-export\]\[(.+)\]$',c)
    if m and r['kind']=='OBSERVATION' and r.get('check')=='pin_raw_outcome':
        pin[m.group(1)]['raw']=r['detail']; pin[m.group(1)]['row']=i
res={}
for leaf,d in pin.items():
    o=d['raw']
    a=(o.get('state') not in (None,'active') and o.get('payload') is None) or o.get('raised')=='PermissionError'
    b=CODE in (o.get('reason') or '') or CODE in (o.get('msg') or '')
    c=[CODE] in o.get('new_refusal_reasons',[])
    dd=o.get('dest_calls')==0 and o.get('dest_unchanged') is True
    res[leaf]=dict(row=d['row'],state=o.get('state'),payload_none=o.get('payload') is None,reason=o.get('reason'),new_refusals=o.get('new_refusal_reasons'),
                   a_not_active_no_payload=a,b_names_code=b,c_durable_refusal=c,d_dest_untouched=dd,
                   reading_iA=all([a,b,c,dd]),reading_iB=all([a,b]),
                   succ_partial_P2_P3_P5_P7=(o.get('state')=='unknown' and o.get('payload') is None and not o.get('new_refusal_reasons') and dd and o.get('new_attempts')==0))
print(json.dumps({'n_members':len(res),'iA_pass':sum(v['reading_iA'] for v in res.values()),'iB_pass':sum(v['reading_iB'] for v in res.values()),
  'a_pass':sum(v['a_not_active_no_payload'] for v in res.values()),'b_pass':sum(v['b_names_code'] for v in res.values()),'c_pass':sum(v['c_durable_refusal'] for v in res.values()),
  'd_pass':sum(v['d_dest_untouched'] for v in res.values()),'succ_partial':sum(v['succ_partial_P2_P3_P5_P7'] for v in res.values()),
  'reasons':sorted(set(v['reason'] for v in res.values()))},indent=1))
# execute regression
ex=collections.defaultdict(lambda: collections.defaultdict(list))
for i,r in enumerate(rows,1):
    m=re.match(r'A19_pin_export_refuses_per_perturbed_member\[execute\]\[(.+)\]$',r.get('case',''))
    if m and r['kind'] in('CHECK_PASS','CHECK_FAIL'): ex[m.group(1)][r['kind']].append(r['check'])
exsum={k:{'pass':len(v['CHECK_PASS']),'fail':len(v['CHECK_FAIL'])} for k,v in ex.items()}
print(json.dumps({'execute_members':len(exsum),'execute_all_pass':all(v['fail']==0 and v['pass']>=6 for v in exsum.values()),'execute_checks_total':sum(v['pass'] for v in exsum.values())}))
# A06 pin
a06=[(i+1,r) for i,r in enumerate(rows) if r.get('case','').startswith('A06') and 'pin:' in str(r.get('check',''))]
print(json.dumps([{'row':i,'check':r['check'],'kind':r['kind']} for i,r in a06]))
json.dump({'pin_members':res,'execute':exsum},open(sys.argv[1],'w'),indent=1,sort_keys=True)
