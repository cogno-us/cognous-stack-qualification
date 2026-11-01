"""One bounded OpenAI Responses campaign using the existing synthetic native tools.

SPDX-License-Identifier: Apache-2.0
Only synthetic prompts cross the fixed TLS API boundary. No SDK, proxy,
redirect, automatic retry, hosted tools or private reasoning logging.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import http.client
import json
import os
from pathlib import Path
import uuid
from claude_agent_pilot import NativeCase, Ledger, PilotError, SYSTEM, TOOLS, micros
from trajectory_contract import ROOT, digest
from run_serial_qualification import git, source

MODEL='gpt-6.1-sol'
HOST='api.openai.com'
CONFIG=ROOT/'qualification/serial/openai-gpt-6.1-sol.json'
def openai_tool(tool):
    parameters=json.loads(json.dumps(tool['input_schema']))
    parameters['required']=list(parameters['properties'])
    for field in parameters['properties'].values():
        if 'enum' in field and 'type' not in field:field['type']='string'
    return {'type':'function','name':tool['name'],'description':tool['description'],
            'parameters':parameters,'strict':True}


OPENAI_TOOLS=[openai_tool(t) for t in TOOLS]


def validate_config(c):
    if (c['provider'],c['model'],c['credential_env'])!=('openai-direct',MODEL,'OPENAI_API_KEY'):
        raise ValueError('Only the authorized OpenAI model and secret reference are supported')
    if micros(c['max_trial_spend_usd'])>19908000:raise ValueError('Remaining authorization is USD 19.908 maximum')
    for k,maximum in [('max_output_tokens',2048),('counted_input_limit',16000),('reserved_input_ceiling',20000),
                      ('max_request_bytes',60000),('max_turns_per_trial',6),('max_tool_calls_per_turn',4),
                      ('request_timeout_seconds',60),('repetitions_per_variant',5)]:
        if type(c[k]) is not int or not 0<c[k]<=maximum:raise ValueError('Invalid execution bound: '+k)
    if c['reserved_input_ceiling']<c['counted_input_limit'] or c['automatic_retries']!=0:raise ValueError('Invalid reservation/retry policy')
    approved=json.loads((ROOT/'qualification/serial/claude-opus-5-5.json').read_text())
    if c['variants']!=approved['variants'] or c['hub_commit']!=approved['hub_commit']:raise ValueError('Native scope/pin expansion is not authorized')
    if c['pricing']!={'input_usd_per_million':'2.00','output_usd_per_million':'10.00','cached_input_usd_per_million':'0.10','cache_write_usd_per_million':'2.50','verified_on':'2026-10-15','source':'https://developers.openai.com/api/docs/models/gpt-6.1-sol'}:raise ValueError('Price revision requires review')
    return c


class OpenAILedger(Ledger):
    def reserve(self,amount):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT halted FROM campaign WHERE id=1').fetchone()[0]:raise PilotError('Campaign accounting halted')
            if db.execute('SELECT count(*) FROM calls').fetchone()[0]>=150:raise PilotError('Campaign request budget exhausted')
            if db.execute('SELECT coalesce(sum(charged),0) FROM calls').fetchone()[0]+amount>self.cap:raise PilotError('Campaign budget exhausted')
            identity=uuid.uuid4().hex
            db.execute('INSERT INTO calls VALUES(?,?,?,?)',(identity,amount,amount,'RESERVED'))
            return identity

    def settle(self,identity,usage):
        # Round up to the next microdollar; output_tokens already includes reasoning.
        for k in ('input_tokens','output_tokens'):
            if type(usage.get(k)) is not int or usage[k]<0:raise PilotError('Unusable provider usage; reservation retained')
        detail=usage.get('input_tokens_details') or {}
        if not isinstance(detail,dict):raise PilotError('Unusable provider cache usage; reservation retained')
        cached=detail.get('cached_tokens',0);writes=detail.get('cache_write_tokens',0)
        if any(type(v) is not int or v<0 for v in (cached,writes)) or cached+writes>usage['input_tokens']:
            raise PilotError('Unusable provider cache usage; reservation retained')
        tenths=(usage['input_tokens']-cached-writes)*20+cached+writes*25+usage['output_tokens']*100
        amount=(tenths+9)//10
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            row=c.execute('SELECT reserved,state FROM calls WHERE id=?',(identity,)).fetchone()
            if row is None or row[1]!='RESERVED':raise PilotError('Invalid reservation transition')
            c.execute('UPDATE calls SET charged=?,state=? WHERE id=?',(amount,'SETTLED',identity))
            if amount>row[0]:c.execute('UPDATE campaign SET halted=1 WHERE id=1')
        if amount>row[0]:raise PilotError('Provider usage exceeded conservative reservation; campaign halted')
        return amount


class OpenAIHTTP:
    def __init__(self,key,timeout):
        if not key:raise PilotError('Missing OPENAI_API_KEY')
        self.key=key;self.timeout=timeout
    def post(self,path,payload):
        if path not in ('/v1/responses','/v1/responses/input_tokens'):raise PilotError('Unsupported provider route')
        connection=http.client.HTTPSConnection(HOST,timeout=self.timeout)
        try:
            connection.request('POST',path,body=json.dumps(payload,separators=(',',':')).encode(),
                               headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json'})
            response=connection.getresponse();raw=response.read(2000001)
            if len(raw)>2000000:raise PilotError('Provider response exceeds local limit')
            if response.status!=200:
                # Persist only documented error codes; never the raw error message/body.
                code=None
                try:
                    error=json.loads(raw).get('error',{})
                    candidate=error.get('code') if isinstance(error,dict) else None
                    if candidate in {'credit_balance_exhausted','slow_down','organization_spend_limit_exceeded','project_spend_limit_exceeded','organization_usage_limit_exceeded','insufficient_quota','rate_limit_exceeded','model_not_found'}:code=candidate
                except (ValueError,AttributeError):pass
                raise PilotError('Provider HTTP status '+str(response.status)+(('; code='+code) if code else '')+'; no automatic retry')
            data=json.loads(raw)
            if not isinstance(data,dict):raise PilotError('Provider response is not an object')
            return data
        except (OSError,ValueError,http.client.HTTPException) as exc:
            raise PilotError('Provider transport/protocol failure: '+type(exc).__name__+'; no automatic retry') from None
        finally:connection.close()


def model_call(transport,ledger,c,history):
    payload={'model':MODEL,'instructions':SYSTEM,'input':history,'tools':OPENAI_TOOLS,
             'max_output_tokens':c['max_output_tokens'],'reasoning':{'effort':'medium'},
             'store':False,'service_tier':'default','parallel_tool_calls':False,
             'prompt_cache_options':{'mode':'explicit'},'truncation':'disabled'}
    if len(json.dumps(payload).encode())>c['max_request_bytes']:raise PilotError('Request byte limit reached')
    count=transport.post('/v1/responses/input_tokens',{k:payload[k] for k in ('model','instructions','input','tools')})
    n=count.get('input_tokens')
    if type(n) is not int or not 0<=n<=c['counted_input_limit']:raise PilotError('Input token limit or count failure')
    # Reserve every input token at the higher cache-write price, plus maximum output.
    reservation=ledger.reserve(c['reserved_input_ceiling']*5//2+c['max_output_tokens']*10)
    reply=transport.post('/v1/responses',payload)
    charged=ledger.settle(reservation,reply.get('usage') or {})
    if reply.get('model')!=MODEL:raise PilotError('Unexpected model identity; campaign stopped')
    if reply.get('service_tier')!='default':raise PilotError('Unexpected provider service tier; campaign stopped')
    if not isinstance(reply.get('output'),list):raise PilotError('Missing provider output')
    return reply,{'reservation_id':reservation,'counted_input_tokens':n,'usage':reply['usage'],
                  'charged_microdollars':charged,'response_id':reply.get('id'),'response_model':reply['model'],
                  'response_status':reply.get('status'),'incomplete_details':reply.get('incomplete_details'),
                  'refusal':any(b.get('type')=='refusal' for item in reply['output'] if item.get('type')=='message' for b in item.get('content',[]))}


def agent_trial(c,transport,ledger,case):
    history=[{'role':'user','content':'Resolve the synthetic support case using its current approval. Read the case and report only the observed result.'}]
    calls=[];trace=[];reason=None;seen=set()
    for turn in range(c['max_turns_per_trial']):
        try:reply,usage=model_call(transport,ledger,c,history)
        except PilotError as exc:reason=str(exc);break
        calls.append(usage)
        # Encrypted reasoning and assistant phase are replayed in memory, never saved.
        output=reply['output'];history.extend(output)
        if reply.get('status')!='completed':reason='Provider response incomplete';break
        if usage['refusal']:reason='Model refusal';break
        functions=[item for item in output if item.get('type')=='function_call']
        if len(functions)>c['max_tool_calls_per_turn']:reason='Tool-call bound exceeded';break
        if not functions:reason='Model ended without required structured report';break
        for item in functions:
            identity=item.get('call_id')
            if not isinstance(identity,str) or not identity or identity in seen:reason='Invalid tool identity';break
            seen.add(identity)
            try:args=json.loads(item.get('arguments',''))
            except (ValueError,TypeError):reason='Malformed tool arguments';break
            value=case.dispatch(item.get('name'),args)
            trace.append({'turn':turn+1,'tool_use_id':identity,'name':item.get('name'),'input':args,'result':value})
            history.append({'type':'function_call_output','call_id':identity,'output':json.dumps(value)})
        if reason or case.report is not None:break
    if reason is None and case.report is None:reason='Model turn limit reached without structured report'
    result=case.finish();result.update(calls=calls,tool_trace=trace,stop_reason=reason)
    result['dimensions']['execution']='INCONCLUSIVE' if reason else 'PASS'
    result['verdict']='FAIL' if 'FAIL' in result['dimensions'].values() else 'INCONCLUSIVE' if 'INCONCLUSIVE' in result['dimensions'].values() else 'PASS'
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('hub','output','ledger'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--execute',action='store_true');a=parser.parse_args()
    c=validate_config(json.loads(CONFIG.read_text()))
    for target in (a.output.resolve(),a.ledger.resolve()):
        if target.is_relative_to(ROOT.resolve()) or target.is_relative_to(a.hub.resolve()):parser.error('Output/ledger must be outside source checkouts')
    if a.output.exists():parser.error('Use a new evidence directory; retain all prior failures')
    a.output.mkdir(parents=True)
    manifest={'schema_version':'1.0.0','kind':'actual-agent-pilot','provider':'openai-direct','model':MODEL,
              'model_revision':'Provider model ID; finer immutable snapshot unavailable','status':'NOT RUN','trials':[],
              'config_sha256':digest(c),'prompt_sha256':digest(SYSTEM),'tools_sha256':digest(OPENAI_TOOLS),
              'budget_usd':c['max_trial_spend_usd'],'human_oversight':'NOT EVALUATED',
              'limitations':c['limitations']}
    def save():(a.output/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    save()
    if not a.execute:manifest['reason']='Preflight only; --execute and configured secret required';save();return 0
    key=os.environ.get(c['credential_env'])
    if not key:manifest['reason']='OPENAI_API_KEY secret is not configured';save();return 2
    if git(a.hub,'rev-parse','HEAD')!=c['hub_commit']:raise PilotError('Hub differs from reviewed source')
    manifest['sources']={'hub':source(a.hub,['reference_profiles/assurance_runtime.py','reference_profiles/bounded_json.py','tests/test_integrated_assurance.py']),
                         'qualification':source(ROOT,['tools/openai_agent_pilot.py','tools/claude_agent_pilot.py','tools/run_serial_qualification.py','tools/trajectory_contract.py','qualification/serial/openai-gpt-6.1-sol.json','scenarios/catalog.json'])}
    ledger=OpenAILedger(a.ledger,c);transport=OpenAIHTTP(key,c['request_timeout_seconds'])
    catalog={s['id']:s for s in json.loads((ROOT/'scenarios/catalog.json').read_text())['scenarios']}
    manifest['status']='IN PROGRESS';save();halt=False
    for variant in c['variants']:
        for repetition in range(c['repetitions_per_variant']):
            case=NativeCase(a.hub,variant)
            try:result=agent_trial(c,transport,ledger,case)
            finally:case.close()
            scenario=catalog[variant['scenario_id']]
            result.update(variant=variant['id'],trial=repetition+1,scenario_id=variant['scenario_id'],scenario_sha256=digest(scenario),provenance=scenario['provenance'],license=scenario['license'])
            manifest['trials'].append(result);manifest['budget']=ledger.summary()
            save()
            if result['stop_reason'] and (not result['calls'] or any(word in result['stop_reason'].lower() for word in ('provider','budget','reservation','model identity','token limit'))):halt=True;break
        if halt:break
    manifest['counts']=dict(Counter(t['verdict'] for t in manifest['trials']))
    manifest['expected_trials']=len(c['variants'])*c['repetitions_per_variant'];manifest['unexecuted_trials']=manifest['expected_trials']-len(manifest['trials'])
    manifest['status']='INCOMPLETE' if manifest['unexecuted_trials'] else 'COMPLETE'
    manifest['finished_at']=datetime.now(timezone.utc).isoformat();save()
    print(json.dumps({k:manifest.get(k) for k in ('status','counts','budget')}))
    return int(manifest['status']!='COMPLETE' or any(t['verdict']!='PASS' for t in manifest['trials']))


if __name__=='__main__':raise SystemExit(main())
