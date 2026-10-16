"""Rescore retained frozen battery evidence offline; makes no provider calls."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
import prp_quality_evaluation as b

def verify(path,prp):
    m=json.loads((path/'manifest.json').read_text());cases=json.loads((path/'cases.json').read_text());index={c['id']:c for c in cases}
    assert cases==json.loads(b.CASES.read_text())['cases']
    assert m['campaign']==json.loads(b.CONFIG.read_text())
    for group,root in [('qualification',b.ROOT),('prp',prp)]:
        for name,expected in m['source_hashes'][group].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==expected,(group,name)
    for arm in ('baseline','prp'):
        assert b.digest((path/(arm+'-instructions.txt')).read_text())==m['prompt_hashes'][arm]
        assert (path/(arm+'-instructions.txt')).read_text()==b.instructions(prp,arm)
    assert json.loads((path/'tools.json').read_text())=={c['id']:b.case_tools(c) for c in cases}
    assert m['schedule']==b.schedule(cases,m['campaign']['seed'])
    trials=m['trials'];keys=[(t['case_id'],t['repetition'],t['condition']) for t in trials]
    assert len(set(keys))==len(keys)
    calls=[];failures=[]
    for t in trials:
        case=index[t['case_id']]
        assert t['score']==b.score(case,t['decision'],t['stop_reason'])
        for item in t['tool_trace']:
            if item['name']=='get_case' and item['accepted']:assert item['result']==case['input']
        if not t['stop_reason']:
            assert [x['name'] for x in t['tool_trace']]==['get_case','submit_decision']
            assert len(t['calls'])==2
        for call in t['calls']:
            assert call['model']==b.MODEL and call['service_tier']=='default'
            assert call['counted_input_tokens']<=13500
            assert call['usage']['input_tokens']<=14000 and call['usage']['output_tokens']<=1536
            calls.append(call)
        if not t['score']['passed']:failures.append({'case_id':t['case_id'],'repetition':t['repetition'],'condition':t['condition'],'decision':t['decision'],'score':t['score'],'stop_reason':t['stop_reason']})
    assert len({c['response_id'] for c in calls})==len(calls) and all(c['response_id'] for c in calls)
    assert m['summary']==b.summarize(cases,trials)
    with sqlite3.connect('file:'+str(path/'ledger.sqlite')+'?mode=ro',uri=True) as db:
        accounting={row[0]:{'reserved':row[1],'charged':row[2],'state':row[3]} for row in db.execute('SELECT id,reserved,charged,state FROM calls')}
    for c in calls:
        a=accounting[c['reservation_id']]
        assert a['state']=='SETTLED' and a['charged']==c['charged_microdollars'] and a['reserved']==50360
        u=c['usage'];detail=u.get('input_tokens_details') or {};cached=detail.get('cached_tokens',0);writes=detail.get('cache_write_tokens',0)
        amount=((u['input_tokens']-cached-writes)*20+cached+writes*25+u['output_tokens']*100+9)//10
        assert amount==a['charged']
    assert len(accounting)<=192 and sum(a['charged'] for a in accounting.values())<=16700000
    assert int(round(float(m['budget']['charged_or_reserved_usd'])*1e6))==sum(a['charged'] for a in accounting.values())
    return {'status':m['status'],'trials':len(trials),'unique_response_ids':len(calls),'accounting_states':dict(Counter(a['state'] for a in accounting.values())),'ledger_microdollars':sum(a['charged'] for a in accounting.values()),'summary':m['summary'],'failed_trials':failures,'verification':'Frozen source hashes, prompts, tools, case inputs, response identities, usage, ledger, full scores and primary summary recomputed locally without model calls.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);p.add_argument('--prp',type=Path,required=True);a=p.parse_args();r=verify(a.evidence,a.prp)
    (a.evidence/'verified-summary.json').write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k not in ('summary','failed_trials')},indent=2));print(json.dumps(r['summary']['arms'],indent=2));print('Failures:',len(r['failed_trials']))
