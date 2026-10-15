"""Offline OpenAI protocol/accounting controls; fake responses are not model evidence."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import openai_agent_pilot as pilot


class Transport:
    def __init__(self,replies=None):self.requests=[];self.replies=list(replies or [reply()])
    def post(self,path,payload):
        self.requests.append((path,copy.deepcopy(payload)))
        if path.endswith('input_tokens'):return {'input_tokens':100}
        value=self.replies.pop(0)
        if isinstance(value,Exception):raise value
        return copy.deepcopy(value)


def reply(output=None,**kw):
    value={'model':pilot.MODEL,'service_tier':'default','id':'response-test','status':'completed',
           'usage':{'input_tokens':100,'output_tokens':10,'input_tokens_details':{'cached_tokens':0,'cache_write_tokens':0}},
           'output':output or []}
    value.update(kw);return value


def function(name,args,identity):return {'type':'function_call','call_id':identity,'name':name,'arguments':json.dumps(args)}


class Case:
    def __init__(self):self.report=None
    def dispatch(self,name,args):self.report=args;return {'status':'recorded'}
    def finish(self):return {'dimensions':{'effect_boundary':'PASS','completion_claim':'PASS'}}


class OpenAIPilotTests(unittest.TestCase):
    def config(self):return pilot.validate_config(json.loads(pilot.CONFIG.read_text()))
    def ledger(self,c=None):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup)
        return pilot.OpenAILedger(Path(folder.name)/'ledger.sqlite',c or self.config())

    def test_remaining_budget_and_fixed_scope(self):
        for field,value in [('max_trial_spend_usd','19.909'),('model','other'),('automatic_retries',1),('max_turns_per_trial',7)]:
            c=self.config();c[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):pilot.validate_config(c)

    def test_protocol_uses_standard_stateless_client_functions(self):
        transport=Transport();pilot.model_call(transport,self.ledger(),self.config(),[])
        count=transport.requests[0][1];payload=transport.requests[1][1]
        self.assertEqual(set(count),{'model','instructions','input','tools'})
        self.assertEqual(payload['service_tier'],'default');self.assertFalse(payload['store'])
        self.assertFalse(payload['parallel_tool_calls']);self.assertEqual(payload['reasoning'],{'effort':'medium'})
        self.assertEqual(payload['prompt_cache_options'],{'mode':'explicit'})
        self.assertTrue(all(t['type']=='function' and t['strict'] for t in payload['tools']))
        self.assertNotIn('previous_response_id',payload)
        self.assertEqual(next(t for t in payload['tools'] if t['name']=='report_result')['parameters']['properties']['status']['type'],'string')

    def test_cache_and_reasoning_usage_are_priced_once(self):
        ledger=self.ledger();identity=ledger.reserve(70480)
        usage={'input_tokens':100,'output_tokens':20,'input_tokens_details':{'cached_tokens':10,'cache_write_tokens':20},'output_tokens_details':{'reasoning_tokens':15}}
        self.assertEqual(ledger.settle(identity,usage),391)
        self.assertEqual(ledger.summary()['charged_or_reserved_usd'],'0.000391')
        with self.assertRaises(pilot.PilotError):ledger.settle(identity,usage)

    def test_unknown_request_retains_reservation_without_retry(self):
        ledger=self.ledger();transport=Transport([pilot.PilotError('Provider timeout')])
        with self.assertRaises(pilot.PilotError):pilot.model_call(transport,ledger,self.config(),[])
        self.assertEqual(len(transport.requests),2)
        self.assertEqual(ledger.summary()['charged_or_reserved_usd'],'0.07048')
        reopened=pilot.OpenAILedger(ledger.path,self.config());self.assertEqual(reopened.summary(),ledger.summary())

    def test_invalid_usage_keeps_reservation_and_overrun_halts(self):
        ledger=self.ledger();identity=ledger.reserve(10)
        with self.assertRaises(pilot.PilotError):ledger.settle(identity,{'input_tokens':1})
        with self.assertRaises(pilot.PilotError):ledger.settle(identity,{'input_tokens':100,'output_tokens':100})
        with self.assertRaises(pilot.PilotError):ledger.reserve(1)

    def test_input_and_budget_limits_block_paid_dispatch(self):
        transport=Transport();ledger=self.ledger()
        with patch.object(transport,'post',return_value={'input_tokens':16001}):
            with self.assertRaises(pilot.PilotError):pilot.model_call(transport,ledger,self.config(),[])
        c=self.config();c['max_trial_spend_usd']='0.01';transport=Transport()
        with self.assertRaises(pilot.PilotError):pilot.model_call(transport,self.ledger(c),c,[])
        self.assertEqual(len(transport.requests),1)

    def test_model_and_tier_substitution_stop(self):
        for field,value in [('model','other'),('service_tier','priority')]:
            r=reply();r[field]=value
            with self.subTest(field=field),self.assertRaises(pilot.PilotError):pilot.model_call(Transport([r]),self.ledger(),self.config(),[])

    def test_reasoning_replayed_but_never_written_in_evidence(self):
        private={'type':'reasoning','id':'r1','summary':[],'encrypted_content':'PRIVATE_SENTINEL'}
        response=reply([private,function('get_case',{},'1')])
        second=reply([function('report_result',{'status':'blocked','effect_id':'effect-1'},'2')])
        case=Case()
        def dispatch(name,args):
            if name=='report_result':case.report=args
            return {'status':'ok'}
        case.dispatch=dispatch;transport=Transport([response,second])
        result=pilot.agent_trial(self.config(),transport,self.ledger(),case)
        self.assertIn(private,transport.requests[3][1]['input'])
        self.assertNotIn('PRIVATE_SENTINEL',json.dumps(result))

    def test_refusal_and_incomplete_do_not_dispatch_tools(self):
        for r in [reply([{'type':'message','content':[{'type':'refusal','refusal':'fixture'}]}]),reply([function('execute_effect',{},'1')],status='incomplete')]:
            case=Case()
            with patch.object(case,'dispatch') as dispatch:
                result=pilot.agent_trial(self.config(),Transport([r]),self.ledger(),case)
                dispatch.assert_not_called();self.assertIsNotNone(result['stop_reason'])

    def test_error_body_cannot_expose_key_and_endpoint_is_fixed(self):
        key='SYNTHETIC_SECRET'
        with patch('openai_agent_pilot.http.client.HTTPSConnection') as connection:
            r=connection.return_value.getresponse.return_value;r.status=401;r.read.return_value=key.encode()
            with self.assertRaises(pilot.PilotError) as error:pilot.OpenAIHTTP(key,1).post('/v1/responses',{})
            self.assertNotIn(key,str(error.exception));self.assertIn('401',str(error.exception))
        with self.assertRaises(pilot.PilotError):pilot.OpenAIHTTP(key,1).post('https://other.invalid',{})

    def test_missing_secret_cli_records_not_run_without_ledger(self):
        with tempfile.TemporaryDirectory() as folder:
            env=dict(os.environ);env.pop('OPENAI_API_KEY',None);env['PYTHONDONTWRITEBYTECODE']='1'
            output=Path(folder)/'out';ledger=Path(folder)/'ledger.sqlite'
            r=subprocess.run([sys.executable,str(ROOT/'tools/openai_agent_pilot.py'),'--hub',str(Path(folder)/'hub'),'--output',str(output),'--ledger',str(ledger),'--execute'],env=env,capture_output=True,text=True)
            self.assertEqual(r.returncode,2,r.stderr)
            self.assertEqual(json.loads((output/'manifest.json').read_text())['reason'],'OPENAI_API_KEY secret is not configured')
            self.assertFalse(ledger.exists())

    def test_paid_job_is_main_only_and_first_attempt_only(self):
        import yaml
        w=yaml.load((ROOT/'.github/workflows/openai-agent-pilot.yml').read_text(),Loader=yaml.BaseLoader)
        self.assertEqual(w['on']['push'],{'branches':['main'],'paths':['qualification/serial/openai-campaign-20261015.json']})
        self.assertEqual(w['jobs']['actual-agent']['if'],"github.event_name == 'push' && github.ref == 'refs/heads/main'")
        guard=next(s for s in w['jobs']['actual-agent']['steps'] if s.get('name')=='Refuse repeated campaign runs')['run']
        self.assertIn('test "$GITHUB_RUN_ATTEMPT" = 1',guard)
        script=guard.split("python - <<'PY'\n")[-1].split('\nPY')[0]
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'RUNNER_TEMP':folder,'GITHUB_RUN_ID':'123'}):
            p=Path(folder)/'openai-campaign-runs.json'
            p.write_text(json.dumps({'total_count':1,'workflow_runs':[{'id':123,'head_branch':'main','event':'push'}]}));exec(compile(script,'guard','exec'),{})
            p.write_text(json.dumps({'total_count':2,'workflow_runs':[{'id':122,'head_branch':'main','event':'push'}]}))
            with self.assertRaises(SystemExit):exec(compile(script,'guard','exec'),{})
