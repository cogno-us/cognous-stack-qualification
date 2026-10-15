"""Actual token and rigor comparison of fixed effort and PRP routing. No retries."""
from collections import defaultdict
from datetime import datetime,timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import time
import uuid
from openai_agent_pilot import OpenAIHTTP,OpenAILedger,MODEL
from claude_agent_pilot import PilotError
from trajectory_contract import ROOT,digest
CONFIG=ROOT/'qualification/serial/prp-proportional-repair-20261015.json'
CASES=ROOT/'qualification/serial/prp-proportional-repair-cases-20261015.json'
FILES=['SKILL.md','references/reasoning-effort.md','references/runtime-control.md']
ARMS=['fixed_low','fixed_medium','fixed_high','prp_routed']
COMMON='Complete the supplied task accurately using only its supplied facts and policies. Submit the requested factual result through the tool. Do not provide private chain of thought.'
ROUTER='Apply PRP Auto to the supplied task. Choose the lowest adequate effective semantic level 0 to 4, honoring mandatory rigor floors and the actual consequence, not just keywords. Return that level with a brief public rationale of at most 35 words. Do not solve the task or expose private chain of thought. The host maps levels 0/1 to low provider effort, level 2 to medium, and levels 3/4 to high. This host mapping is experimental, not part of PRP itself.'
MAP={0:'low',1:'low',2:'medium',3:'high',4:'high'}
ROUTE_TOOL={'type':'function','name':'choose_reasoning_level','description':'Select the lowest adequate PRP effective level.','strict':True,'parameters':{'type':'object','properties':{'effective_level':{'type':'integer','enum':[0,1,2,3,4]},'brief_basis':{'type':'string'}},'required':['effective_level','brief_basis'],'additionalProperties':False}}
class Budget(OpenAILedger):
    def reserve(self,amount):
        if amount not in (45120,60480):raise PilotError('Unexpected reservation')
        with self.connect() as d:
            d.execute('BEGIN IMMEDIATE')
            if d.execute('SELECT halted FROM campaign WHERE id=1').fetchone()[0]:raise PilotError('Campaign halted')
            if d.execute('SELECT count(*) FROM calls').fetchone()[0]>=100:raise PilotError('Campaign call cap')
            if d.execute('SELECT coalesce(sum(charged),0) FROM calls').fetchone()[0]+amount>self.cap:raise PilotError('Campaign budget exhausted')
            i=uuid.uuid4().hex;d.execute('INSERT INTO calls VALUES(?,?,?,?)',(i,amount,amount,'RESERVED'));return i

def config():
    c=json.loads(CONFIG.read_text())
    expected={'campaign_id':'prp-proportional-repair-20261015','model':MODEL,'max_trial_spend_usd':'7.27','repetitions':2,'max_answer_calls':80,'max_router_calls':20,'max_paid_calls':100,'answer_output_cap':2048,'router_output_cap':512,'counted_input_limit':15000,'reserved_input_ceiling':16000,'automatic_retries':0,'seed':20261015,'prp_commit':'b3ffa8559db05188f3471c5b0bfe5d936a4bcb29'}
    if any(c.get(k)!=v for k,v in expected.items()):raise ValueError('Frozen campaign bound mismatch')
    if c['pricing']!=json.loads((ROOT/'qualification/serial/openai-gpt-6.1-sol.json').read_text())['pricing']:raise ValueError('Pricing changed')
    return c

def plan(cases):
    rng=random.Random(20261015);out=[]
    for rep in (1,2):
        identities=[c['id'] for c in cases];rng.shuffle(identities)
        for n,i in enumerate(identities):
            arms=ARMS[(n+rep)%4:]+ARMS[:(n+rep)%4]
            out.extend({'case_id':i,'repetition':rep,'arm':a} for a in arms)
    return out

def public_input(case):return {'task':case['task']}
def protocol(prp):return '\n\n'.join('FILE '+f+'\n'+(prp/f).read_text() for f in FILES)
def tool(case):return {'type':'function','name':'submit_result','description':'Submit the factual result requested by the task.','strict':True,'parameters':case['answer_schema']}

def call(transport,budget,instructions,task,tools,effort,output_cap):
    payload={'model':MODEL,'instructions':instructions,'input':[{'role':'user','content':json.dumps(task)}],'tools':tools,'reasoning':{'effort':effort},'max_output_tokens':output_cap,'store':False,'service_tier':'default','parallel_tool_calls':False,'tool_choice':'required','prompt_cache_options':{'mode':'explicit'},'truncation':'disabled'}
    record={'requested_effort':effort,'requested_output_cap':output_cap,'instructions_sha256':digest(instructions),'input_sha256':digest(task),'tools_sha256':digest(tools),'started_at':datetime.now(timezone.utc).isoformat(),'visible_messages':[],'tool_proposals':[],'stop_reason':None,'result':None}
    try:
        if len(json.dumps(payload).encode())>100000:raise PilotError('Request byte bound')
        n=transport.post('/v1/responses/input_tokens',{k:payload[k] for k in ('model','instructions','input','tools')}).get('input_tokens')
        if type(n) is not int or not 0<=n<=15000:raise PilotError('Provider token count invalid or above bound')
        i=budget.reserve(40000+output_cap*10);record['reservation_id']=i;record['counted_input_tokens']=n
        start=time.monotonic();reply=transport.post('/v1/responses',payload);record['latency_seconds']=round(time.monotonic()-start,3)
        record.update(response_id=reply.get('id'),model=reply.get('model'),service_tier=reply.get('service_tier'),status=reply.get('status'),usage=reply.get('usage'),incomplete_details=reply.get('incomplete_details'))
        record['charged_microdollars']=budget.settle(i,reply.get('usage') or {})
        usage=reply['usage'];details=usage.get('output_tokens_details') or {};r=details.get('reasoning_tokens')
        if type(r) is int and 0<=r<=usage['output_tokens']:
            record['reasoning_token_measurement']={'value':r,'status':'provider_reported','interpretation':'Reported reasoning tokens; zero does not independently establish absence of internal computation.'}
        else:record['reasoning_token_measurement']={'value':None,'status':'unavailable','estimated_bounds':[0,usage['output_tokens']],'interpretation':'Only a conservative accounting bound, not an estimate of private thought.'}
        if reply.get('model')!=MODEL or reply.get('service_tier')!='default':raise PilotError('Provider identity/tier mismatch')
        output=reply.get('output')
        if not isinstance(output,list):raise PilotError('Provider output invalid')
        record['visible_messages']=[o for o in output if o.get('type')=='message']
        functions=[o for o in output if o.get('type')=='function_call'];record['tool_proposals']=functions
        if reply.get('status')!='completed':raise PilotError('Response incomplete')
        if len(functions)!=1 or functions[0].get('name')!=tools[0]['name']:raise PilotError('Missing or invalid result tool')
        result=json.loads(functions[0].get('arguments',''))
        from jsonschema import Draft202012Validator
        Draft202012Validator(tools[0]['parameters']).validate(result)
        record['result']=result
    except Exception as exc:
        # Sanitize all exceptions to prevent accidental provider/credential disclosure.
        record['stop_reason']=str(exc) if isinstance(exc,PilotError) else type(exc).__name__
    record['finished_at']=datetime.now(timezone.utc).isoformat()
    return record

def equal(a,b):
    if isinstance(b,bool):return type(a) is bool and a==b
    if isinstance(b,(int,float)):return type(a) in (int,float) and abs(a-b)<=.0005
    if isinstance(b,dict):return isinstance(a,dict) and set(a)==set(b) and all(equal(a[k],v) for k,v in b.items())
    if isinstance(b,list):return isinstance(a,list) and a==b
    return isinstance(a,str) and a.strip()==b

def score(case,result,effort,level=None,error=None):
    if result is None or error:return {'quality_passed':False,'quality_score':0,'allocation_score':0,'proportionality_score':0,'predicate_matches':{},'critical_failure':False,'execution_failure':True,'level_appropriate':None}
    matches={k:equal(result.get(k),v) for k,v in case['expected'].items()}
    if case['id']=='R5' and isinstance(result.get('test_variants'),list):
        variants=set(result['test_variants']);matches['test_variants']=set(case['expected']['test_variants'])<=variants and 'format_header_only' not in variants
    # Names and identifiers carry task meaning; no optional explanatory field is scored.
    if case['group']=='cost':quality=2 if all(matches.values()) else 0
    else:
        fraction=sum(matches.values())/len(matches)
        quality=2 if fraction==1 else 1 if fraction>=.75 else 0
    critical=any(not matches[k] for k in case['critical_fields'])
    if critical:quality=0
    allocation=2 if effort==case['target_effort'] else 1 if effort=='medium' else 0
    level_ok=None if level is None else level in case['acceptable_levels']
    if level is not None and not level_ok:allocation=min(allocation,1)
    return {'quality_passed':all(matches.values()),'quality_score':quality,'allocation_score':allocation,'proportionality_score':0 if critical else quality+allocation,'predicate_matches':matches,'critical_failure':critical,'execution_failure':False,'level_appropriate':level_ok}

def metrics(calls):
    paid=[c for c in calls if 'usage' in c and c.get('usage')];reported=[c['reasoning_token_measurement'] for c in paid if 'reasoning_token_measurement' in c]
    return {'calls':len(paid),'input_tokens':sum(c['usage']['input_tokens'] for c in paid),'output_tokens':sum(c['usage']['output_tokens'] for c in paid),'reported_reasoning_tokens':sum(x['value'] for x in reported if x['value'] is not None),'reasoning_tokens_complete':len(reported)==len(paid) and all(x['value'] is not None for x in reported),'estimated_microdollars':sum(c.get('charged_microdollars',0) for c in paid),'latency_seconds':round(sum(c.get('latency_seconds',0) for c in paid),3)}

def summarize(trials):
    summary={'arms':{},'case_results':[],'routing':{},'limitations':['Allocation score evaluates a preregistered host effort mapping, not hidden thought.','Proportionality 0-4 combines allocation 0-2 and observable quality/rigor 0-2.','Total routed cost includes router and answer calls plus full public instructions.','One model, ten purposive tasks, two repetitions: descriptive, not general efficacy.','Fixed arms lack PRP; routing/prompt effects are combined in the PRP system condition.']}
    for arm in ARMS:
        ts=[t for t in trials if t['arm']==arm];summary['arms'][arm]={'groups':{}}
        for group in ['all','cost','rigor']:
            g=ts if group=='all' else [t for t in ts if t['group']==group];calls=[c for t in g for c in t['calls']]
            summary['arms'][arm]['groups'][group]={**metrics(calls),'trials':len(g),'quality_passes':sum(t['score']['quality_passed'] for t in g),'critical_failures':sum(t['score']['critical_failure'] for t in g),'execution_failures':sum(t['score']['execution_failure'] for t in g),'mean_allocation_score':sum(t['score']['allocation_score'] for t in g)/len(g) if g else None,'mean_quality_score':sum(t['score']['quality_score'] for t in g)/len(g) if g else None,'mean_proportionality_score':sum(t['score']['proportionality_score'] for t in g)/len(g) if g else None}
    for identity in sorted(set(t['case_id'] for t in trials)):
        row={'case_id':identity,'arms':{}}
        for arm in ARMS:
            ts=[t for t in trials if t['case_id']==identity and t['arm']==arm]
            if not ts:continue
            row['arms'][arm]={**metrics([c for t in ts for c in t['calls']]),'quality_passes':sum(t['score']['quality_passed'] for t in ts),'mean_proportionality_score':sum(t['score']['proportionality_score'] for t in ts)/len(ts),'levels':[t.get('selected_level') for t in ts],'efforts':[t['answer_effort'] for t in ts]}
        summary['case_results'].append(row)
    routed=[t for t in trials if t['arm']=='prp_routed'];summary['routing']={'correct_level_choices':sum(t['score']['level_appropriate'] is True for t in routed),'trials':len(routed),'router_only_metrics':metrics([t['calls'][0] for t in routed])}
    summary['comparisons']={}
    for group in ['all','cost','rigor']:
        x=summary['arms']['prp_routed']['groups'][group];comparisons={}
        for arm in ['fixed_low','fixed_medium','fixed_high']:
            y=summary['arms'][arm]['groups'][group];base=y['estimated_microdollars']
            comparisons[arm]={'cost_delta_microdollars':x['estimated_microdollars']-base,'cost_saving_percent':(1-x['estimated_microdollars']/base)*100 if base else None,'input_token_delta':x['input_tokens']-y['input_tokens'],'output_token_delta':x['output_tokens']-y['output_tokens'],'quality_pass_delta':x['quality_passes']-y['quality_passes']}
        summary['comparisons'][group]=comparisons
    return summary

def main():
    p=argparse.ArgumentParser();p.add_argument('--prp',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--execute',action='store_true');a=p.parse_args();c=config();prp=a.prp.resolve();out=a.output.resolve()
    if out.exists() or out.is_relative_to(ROOT) or out.is_relative_to(prp):p.error('Use a new evidence directory outside checkouts')
    if subprocess.check_output(['git','-C',str(prp),'rev-parse','HEAD'],text=True).strip()!=c['prp_commit']:p.error('PRP pin mismatch')
    cases=json.loads(CASES.read_text())['cases'];index={x['id']:x for x in cases};order=plan(cases);text=protocol(prp)
    out.mkdir(parents=True);sourcefiles=['tools/prp_proportional_evaluation.py','tools/prp_proportional_cases.py','tools/openai_agent_pilot.py','tools/claude_agent_pilot.py','tools/trajectory_contract.py','qualification/serial/prp-proportional-repair-20261015.json','qualification/serial/prp-proportional-repair-cases-20261015.json']
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    m={'schema':'prp-proportional-run/1.0','status':'NOT RUN','campaign':c,'trials':[],'schedule':order,'source_hashes':{'qualification':{f:sha(ROOT/f) for f in sourcefiles},'prp':{f:sha(prp/f) for f in FILES}},'common_instructions':COMMON,'router_instructions':ROUTER,'host_mapping':MAP,'model_snapshot':'Provider ID; finer immutable snapshot unavailable','sampling_settings':'Temperature/seed unavailable; host ordering seed frozen','scoring':'Frozen predicates plus proportionality 0-4; no free-text rationale scoring'}
    (out/'cases.json').write_text(json.dumps(cases,indent=2));(out/'protocol.txt').write_text(text);(out/'config.json').write_text(json.dumps(c,indent=2))
    def save():(out/'manifest.json').write_text(json.dumps(m,indent=2,sort_keys=True)+'\n')
    save()
    if not a.execute:return 0
    budget=Budget(out/'ledger.sqlite',c);transport=OpenAIHTTP(os.environ.get('OPENAI_API_KEY'),60);m['status']='IN PROGRESS';save()
    for item in order:
        case=index[item['case_id']];r=item|{'group':case['group'],'calls':[],'selected_level':None,'answer_effort':None,'stop_reason':None}
        if item['arm']=='prp_routed':
            route=call(transport,budget,ROUTER+'\n\n'+text,public_input(case),[ROUTE_TOOL],'low',512);r['calls'].append(route)
            if route['result'] is not None and not route['stop_reason']:
                r['selected_level']=route['result']['effective_level'];r['answer_effort']=MAP[r['selected_level']]
            else:r['stop_reason']=route['stop_reason'] or 'No router result'
        else:r['answer_effort']=item['arm'].split('_')[1]
        if not r['stop_reason']:
            inst=COMMON+('\n\nApply PRP at the selected effective level '+str(r['selected_level'])+'.\n'+text if item['arm']=='prp_routed' else '')
            answer=call(transport,budget,inst,public_input(case),[tool(case)],r['answer_effort'],2048);r['calls'].append(answer);r['stop_reason']=answer['stop_reason'];result=answer['result']
        else:result=None
        r['score']=score(case,result,r['answer_effort'],r['selected_level'],r['stop_reason']);r['answer']=result;m['trials'].append(r);m['budget']=budget.summary();save()
        # Progress only; detailed outputs/spend remain in the retained evidence artifact.
        print('Completed allocated trial '+str(len(m['trials']))+' of 80',flush=True)
        if r['stop_reason'] and any(s in r['stop_reason'].lower() for s in ['provider','budget','campaign','transport']):break
    m['status']='COMPLETE' if len(m['trials'])==80 else 'INCOMPLETE';m['summary']=summarize(m['trials']);m['finished_at']=datetime.now(timezone.utc).isoformat();save();print('Campaign '+m['status'],flush=True)
    return int(m['status']!='COMPLETE')
if __name__=='__main__':raise SystemExit(main())
