"""Bounded actual-OpenAI K6 paired experiment. No automatic retries or hidden reasoning logs."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import time
from openai_agent_pilot import OpenAIHTTP, OpenAILedger, MODEL
from claude_agent_pilot import PilotError
from trajectory_contract import ROOT, digest

CONFIG=ROOT/'qualification/serial/prp-openai-20261015.json'
FILES=['SKILL.md','references/prp-core.md','references/runtime-control.md','references/source-lineage.md']
SYSTEM='''Evaluate a synthetic decision under the supplied author model. First call get_case to read the current evidence, prior, action losses, costs, and stopping rule. Update the hypothesis probabilities using the observed evidence. Choose the action with minimum expected loss among actions allowed by the stopping rule, including gather and delay costs. Submit report_decision with your posterior, selected action, and a concise evidence-based rationale. Do not reveal private chain of thought. No external tools or real-world actions are available.'''
TOOLS=[{'type':'function','name':'get_case','description':'Read the current synthetic decision case.','strict':True,'parameters':{'type':'object','properties':{},'required':[],'additionalProperties':False}},
 {'type':'function','name':'report_decision','description':'Submit the decision and concise rationale after reading the case.','strict':True,'parameters':{'type':'object','properties':{'posterior':{'type':'array','items':{'type':'number'},'minItems':2,'maxItems':2},'action':{'type':'string','enum':['act_h0','act_h1','defer','gather']},'rationale':{'type':'string'}},'required':['posterior','action','rationale'],'additionalProperties':False}}]

def validate(c):
    expected={'campaign_id':'prp-openai-20261015','model':MODEL,'max_trial_spend_usd':'3.00','repetitions':3,'max_turns':3,'max_output_tokens':1536,'counted_input_limit':15000,'reserved_input_ceiling':16000,'automatic_retries':0,'prp_commit':'b3ffa8559db05188f3471c5b0bfe5d936a4bcb29'}
    if any(c.get(k)!=v for k,v in expected.items()):raise ValueError('Campaign bounds or source changed')
    return c

def schedule():
    names=['null','discriminating','perturbed_weaker_signal']
    return [(r+1,n,c) for r in range(3) for n in names[r:]+names[:r] for c in (['baseline','prp'] if (r+names.index(n))%2==0 else ['prp','baseline'])]

def instructions(prp,condition):
    return SYSTEM if condition=='baseline' else SYSTEM+'\n\nApply the following public PRP protocol and references:\n'+ '\n\n'.join('FILE '+p+'\n'+(prp/p).read_text() for p in FILES)

def case_input(case,name):
    return {k:case[k] for k in ('hypotheses','prior','actions','stop_expected_loss')} | {'observed_evidence_likelihoods':case['likelihoods'][name]}

def valid_report(args,case):
    if not isinstance(args,dict) or set(args)!={'posterior','action','rationale'}:return False
    p=args['posterior']
    return isinstance(p,list) and len(p)==2 and all(type(x) in (int,float) and math.isfinite(x) and 0<=x<=1 for x in p) and abs(sum(p)-1)<1e-9 and args['action'] in case['actions'] and isinstance(args['rationale'],str) and len(args['rationale'])<=12000

def trial(c,transport,ledger,prompt,case,name):
    history=[{'role':'user','content':'Read the current case and submit your decision through the tools.'}]
    result={'calls':[],'tool_trace':[],'visible_messages':[],'decision':None,'stop_reason':None,'started_at':datetime.now(timezone.utc).isoformat()}
    read=False;seen=set()
    for turn in range(c['max_turns']):
        payload={'model':MODEL,'instructions':prompt,'input':history,'tools':TOOLS,'max_output_tokens':c['max_output_tokens'],'reasoning':{'effort':'medium'},'store':False,'service_tier':'default','parallel_tool_calls':False,'prompt_cache_options':{'mode':'explicit'},'truncation':'disabled'}
        try:
            if len(json.dumps(payload).encode())>100000:raise PilotError('Request byte limit')
            count=transport.post('/v1/responses/input_tokens',{k:payload[k] for k in ('model','instructions','input','tools')}).get('input_tokens')
            if type(count) is not int or not 0<=count<=c['counted_input_limit']:raise PilotError('Provider token count invalid or above bound')
            identity=ledger.reserve(c['reserved_input_ceiling']*5//2+c['max_output_tokens']*10)
            started=time.monotonic();reply=transport.post('/v1/responses',payload)
            charged=ledger.settle(identity,reply.get('usage') or {})
            result['calls'].append({'response_id':reply.get('id'),'model':reply.get('model'),'status':reply.get('status'),'service_tier':reply.get('service_tier'),'incomplete_details':reply.get('incomplete_details'),'usage':reply.get('usage'),'counted_input_tokens':count,'charged_microdollars':charged,'reservation_id':identity,'latency_seconds':round(time.monotonic()-started,3)})
            if reply.get('model')!=MODEL or reply.get('service_tier')!='default':raise PilotError('Unexpected provider identity/tier')
            output=reply.get('output')
            if not isinstance(output,list):raise PilotError('Invalid provider output')
            result['visible_messages'].extend(item for item in output if item.get('type')=='message')
            if reply.get('status')!='completed':raise PilotError('Provider response incomplete')
            history.extend(output) # Reasoning replay stays in memory only.
            calls=[x for x in output if x.get('type')=='function_call']
            if len(calls)!=1:raise PilotError('Expected one tool call per turn')
            item=calls[0];call_id=item.get('call_id')
            if not isinstance(call_id,str) or not call_id or call_id in seen:raise PilotError('Invalid tool identity')
            seen.add(call_id)
            args=json.loads(item.get('arguments',''))
            tool=item.get('name')
            if tool=='get_case' and args=={} and not read:
                value=case_input(case,name);read=True
            elif tool=='report_decision' and read and valid_report(args,case):
                value={'accepted':True};result['decision']=args
            else:raise PilotError('Tool contract violation')
            result['tool_trace'].append({'turn':turn+1,'call_id':call_id,'name':tool,'arguments':args,'result':value})
            history.append({'type':'function_call_output','call_id':call_id,'output':json.dumps(value)})
            if result['decision'] is not None:break
        except (PilotError,ValueError,TypeError) as exc:
            result['stop_reason']=str(exc) if isinstance(exc,PilotError) else 'Invalid tool arguments';break
    if result['decision'] is None and result['stop_reason'] is None:result['stop_reason']='Turn limit without decision'
    result['finished_at']=datetime.now(timezone.utc).isoformat()
    return result

def grade(case,trials,scorer):
    pairs=[];perturb=[]
    for condition in ('baseline','prp'):
        for repetition in (1,2,3):
            group={t['observation']:t for t in trials if t['condition']==condition and t['repetition']==repetition}
            twins={n:group.get(n,{}).get('decision') for n in ('null','discriminating')}
            value=scorer.score_pair(case,twins) if all(twins.values()) else {'pair_passed':False,'execution_incomplete':True}
            pairs.append({'condition':condition,'repetition':repetition,**value})
            p=group.get('perturbed_weaker_signal',{}).get('decision')
            value=scorer.score_perturbed_direction(case,'perturbed_weaker_signal',p['posterior'][0]-case['prior'][0]) if p else {'direction_correct':False,'execution_incomplete':True}
            perturb.append({'condition':condition,'repetition':repetition,**value})
    return {'pairs':pairs,'perturbations':perturb,'behavioral_efficacy_established':False}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prp',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--execute',action='store_true');a=ap.parse_args()
    c=validate(json.loads(CONFIG.read_text()));prp=a.prp.resolve();out=a.output.resolve()
    if out.exists() or out.is_relative_to(ROOT) or out.is_relative_to(prp):ap.error('Use a new output directory outside checkouts')
    if subprocess.check_output(['git','-C',str(prp),'rev-parse','HEAD'],text=True).strip()!=c['prp_commit']:ap.error('PRP pin mismatch')
    out.mkdir(parents=True)
    paths=FILES+['evaluations/paired-case.json','tools/paired_evaluation.py']
    sources={p:hashlib.sha256((prp/p).read_bytes()).hexdigest() for p in paths}
    case=json.loads((prp/'evaluations/paired-case.json').read_text())
    spec=importlib.util.spec_from_file_location('prp_scorer',prp/'tools/paired_evaluation.py');scorer=importlib.util.module_from_spec(spec);spec.loader.exec_module(scorer)
    prompts={k:instructions(prp,k) for k in ('baseline','prp')}
    for k,v in prompts.items():(out/(k+'-instructions.txt')).write_text(v)
    (out/'case.json').write_text(json.dumps(case,indent=2));(out/'tools.json').write_text(json.dumps(TOOLS,indent=2));(out/'config.json').write_text(json.dumps(c,indent=2))
    manifest={'campaign':c,'source_hashes':sources,'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'prompt_hashes':{k:digest(v) for k,v in prompts.items()},'schedule':schedule(),'status':'NOT RUN','trials':[],'model_revision':'Provider ID; finer immutable snapshot unavailable','limitations':['Three paired repetitions of one synthetic author model; no general efficacy claim.','PRP adds instruction tokens; model/tools/settings/task inputs are matched.','Temperature/seed unavailable; medium reasoning fixed, hidden reasoning not logged.','Client spend estimates at recorded rates; no invoice guarantee.','Historical fixture unexecuted field describes its offline provenance; this manifest records actual execution.']}
    def save():(out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    save()
    if not a.execute:return 0
    ledger=OpenAILedger(out/'ledger.sqlite',c);transport=OpenAIHTTP(os.environ.get('OPENAI_API_KEY'),60)
    manifest['status']='IN PROGRESS';save()
    for repetition,name,condition in schedule():
        result=trial(c,transport,ledger,prompts[condition],case,name)
        result.update(repetition=repetition,observation=name,condition=condition)
        manifest['trials'].append(result);manifest['budget']=ledger.summary();save()
        print(json.dumps({'trial':len(manifest['trials']),'condition':condition,'observation':name,'decision':result['decision'],'stop_reason':result['stop_reason'],'budget':manifest['budget']}),flush=True)
        if result['stop_reason'] and any(w in result['stop_reason'].lower() for w in ('provider','budget','reservation')):break
    manifest['status']='COMPLETE' if len(manifest['trials'])==18 else 'INCOMPLETE'
    manifest['scores']=grade(case,manifest['trials'],scorer);save()
    print(json.dumps({'status':manifest['status'],'scores':manifest['scores'],'budget':manifest['budget']}),flush=True)
    return int(manifest['status']!='COMPLETE' or any(t['stop_reason'] for t in manifest['trials']))

if __name__=='__main__':raise SystemExit(main())
