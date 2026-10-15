"""Offline budget, transport and agent-loop controls; never model qualification."""
import copy
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from claude_agent_pilot import CONFIG, MODEL, Ledger, PilotError, validate_config, model_call, agent_trial, AnthropicHTTP


class FakeTransport:
    def __init__(self,reply=None,fail=False):self.requests=[];self.reply=reply;self.fail=fail
    def post(self,path,payload):
        self.requests.append((path,copy.deepcopy(payload)))
        if path.endswith('count_tokens'):return {'input_tokens':100}
        if self.fail:raise PilotError('Provider timeout; no automatic retry')
        return self.reply or {'model':MODEL,'content':[],'usage':{'input_tokens':100,'output_tokens':10}}


class FakeCase:
    report=None
    def dispatch(self,name,args):self.report=args;return {'status':'report-recorded'}
    def finish(self):return {'dimensions':{'effect_boundary':'PASS','completion_claim':'PASS'},'scope':'UNIT FIXTURE ONLY'}


class ClaudePilotTests(unittest.TestCase):
    def config(self):return validate_config(json.loads(CONFIG.read_text()))
    def ledger(self,c=None):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        return Ledger(Path(t.name)/'campaign.db',c or self.config())

    def test_only_approved_model_and_budget(self):
        for field,value in [('model','other'),('max_trial_spend_usd','20.01'),('automatic_retries',1),('max_turns_per_trial',100)]:
            c=self.config();c[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):validate_config(c)

    def test_reservations_survive_restart_and_unknown_requests(self):
        c=self.config();c['max_trial_spend_usd']='0.20';ledger=self.ledger(c)
        ledger.reserve(120960)
        reopened=Ledger(ledger.path,c)
        with self.assertRaisesRegex(PilotError,'exhausted'):reopened.reserve(120960)
        self.assertEqual(reopened.summary()['charged_or_reserved_usd'],'0.12096')

    def test_usage_releases_only_known_unused_reservation(self):
        ledger=self.ledger();identity=ledger.reserve(120960)
        ledger.settle(identity,{'input_tokens':100,'output_tokens':10})
        self.assertEqual(ledger.summary()['charged_or_reserved_usd'],'0.0006')
        with self.assertRaises(PilotError):ledger.settle(identity,{'input_tokens':0,'output_tokens':0})

    def test_malformed_usage_does_not_refund_and_overrun_halts(self):
        ledger=self.ledger();i=ledger.reserve(1000)
        with self.assertRaises(PilotError):ledger.settle(i,{'input_tokens':1})
        with self.assertRaisesRegex(PilotError,'exceeded'):ledger.settle(i,{'input_tokens':1000,'output_tokens':1000})
        with self.assertRaisesRegex(PilotError,'halted'):ledger.reserve(1)

    def test_concurrent_reservations_cannot_overdraw(self):
        from concurrent.futures import ThreadPoolExecutor
        c=self.config();c['max_trial_spend_usd']='0.20';ledger=self.ledger(c)
        def reserve(_):
            try:return ledger.reserve(120960)
            except PilotError:return None
        with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(reserve,range(4)))
        self.assertEqual(sum(x is not None for x in results),1)

    def test_no_paid_call_after_input_or_budget_limit(self):
        c=self.config();ledger=self.ledger();t=FakeTransport()
        with patch.object(t,'post',return_value={'input_tokens':16001}):
            with self.assertRaisesRegex(PilotError,'token limit'):model_call(t,ledger,c,[])
        c=self.config();c['max_trial_spend_usd']='0.01';ledger=self.ledger(c);t=FakeTransport()
        with self.assertRaisesRegex(PilotError,'budget'):model_call(t,ledger,c,[])
        self.assertEqual([x[0] for x in t.requests],['/v1/messages/count_tokens'])

    def test_unknown_transport_keeps_reservation_and_does_not_retry(self):
        c=self.config();ledger=self.ledger();t=FakeTransport(fail=True)
        with self.assertRaises(PilotError):model_call(t,ledger,c,[])
        self.assertEqual(len(t.requests),2);self.assertEqual(ledger.summary()['calls'][0]['state'],'RESERVED')

    def test_model_substitution_and_unrequested_caching_fail_closed(self):
        for change in ('model','cache'):
            reply={'model':MODEL,'content':[],'usage':{'input_tokens':1,'output_tokens':1}}
            if change=='model':reply['model']='other-model'
            else:reply['usage']['cache_creation_input_tokens']=10
            with self.subTest(change=change),self.assertRaises(PilotError):model_call(FakeTransport(reply),self.ledger(),self.config(),[])

    def test_private_thinking_is_not_persisted_in_trial_record(self):
        private='SYNTHETIC_PRIVATE_THINKING_SENTINEL'
        reply={'model':MODEL,'content':[{'type':'thinking','thinking':private,'signature':'test-signature'},
               {'type':'tool_use','id':'one','name':'report_result','input':{'status':'blocked','effect_id':'effect-1'}}],
               'usage':{'input_tokens':10,'output_tokens':20}}
        result=agent_trial(self.config(),FakeTransport(reply),self.ledger(),FakeCase())
        self.assertNotIn(private,json.dumps(result));self.assertNotIn('test-signature',json.dumps(result))
        self.assertEqual(result['verdict'],'PASS') # unit transport only, never evidence of model execution

    def test_standard_only_capacity_and_medium_effort_are_explicit(self):
        t=FakeTransport();model_call(t,self.ledger(),self.config(),[])
        count=t.requests[0][1];paid=t.requests[1][1]
        self.assertNotIn('service_tier',count);self.assertNotIn('output_config',count)
        self.assertEqual(paid['service_tier'],'standard_only')
        self.assertEqual(paid['output_config'],{'effort':'medium'})
        self.assertNotIn('temperature',paid);self.assertNotIn('tool_choice',paid)

    def test_endpoint_and_error_body_cannot_expose_key(self):
        key='synthetic-test-secret'
        with patch('claude_agent_pilot.http.client.HTTPSConnection') as conn:
            response=conn.return_value.getresponse.return_value;response.status=401;response.read.return_value=(key+' forbidden').encode()
            with self.assertRaises(PilotError) as error:AnthropicHTTP(key,1).post('/v1/messages',{})
            self.assertNotIn(key,str(error.exception));self.assertIn('401',str(error.exception))
        with self.assertRaises(PilotError):AnthropicHTTP(key,1).post('https://other-host.invalid',{})


if __name__=='__main__':unittest.main()


class AuthorizedCampaignTests(unittest.TestCase):
    def test_live_cli_accepts_no_provider_limit_and_stops_without_secret(self):
        import subprocess
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'evidence'
            env=dict(os.environ);env.pop('ANTHROPIC_API_KEY',None);env['PYTHONDONTWRITEBYTECODE']='1'
            result=subprocess.run([sys.executable,str(ROOT/'tools/claude_agent_pilot.py'),'--hub',str(Path(folder)/'hub'),
                '--output',str(output),'--ledger',str(Path(folder)/'ledger.sqlite'),'--execute'],env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,2,result.stderr)
            manifest=json.loads((output/'manifest.json').read_text())
            self.assertEqual(manifest['status'],'NOT RUN')
            self.assertEqual(manifest['reason'],'ANTHROPIC_API_KEY secret is not configured')
            self.assertFalse((Path(folder)/'ledger.sqlite').exists())

    def test_paid_workflow_trigger_is_main_marker_and_no_pr_execution(self):
        import yaml
        workflow=yaml.load((ROOT/'.github/workflows/claude-agent-pilot.yml').read_text(),Loader=yaml.BaseLoader)
        self.assertEqual(workflow['on']['push'],{'branches':['main'],'paths':['qualification/serial/claude-campaign-20261015.json']})
        gate=workflow['jobs']['actual-agent']['if']
        self.assertIn("github.ref == 'refs/heads/main'",gate)
        self.assertNotIn('pull_request',gate)
        self.assertIn('inputs.campaign_authorized',gate)

    def test_workflow_campaign_history_blocks_previous_paid_run(self):
        import yaml
        workflow=yaml.load((ROOT/'.github/workflows/claude-agent-pilot.yml').read_text(),Loader=yaml.BaseLoader)
        steps=workflow['jobs']['actual-agent']['steps']
        guard=next(s['run'] for s in steps if s.get('name')=='Refuse automatic retries and additional campaign dispatches')
        script=guard.split("python - <<'PY'\n")[-1].split('\nPY')[0]
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'RUNNER_TEMP':folder,'GITHUB_RUN_ID':'123'}):
            path=Path(folder)/'campaign-runs.json'
            for event in ('push','workflow_dispatch','pull_request'):
                path.write_text(json.dumps({'total_count':2,'workflow_runs':[{'id':123,'head_branch':'main','event':'push'},{'id':122,'head_branch':'main','event':event}]}))
                if event=='pull_request':exec(compile(script,'workflow-guard','exec'),{})
                else:
                    with self.subTest(event=event),self.assertRaises(SystemExit):exec(compile(script,'workflow-guard','exec'),{})
