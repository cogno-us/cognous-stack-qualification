import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import prp_battery_evaluation as b
from prp_battery_cases import create_cases
class Fake:
    def __init__(self,steps):self.steps=iter(steps);self.requests=[]
    def post(self,path,payload):
        self.requests.append((path,copy.deepcopy(payload)))
        if path.endswith('input_tokens'):return {'input_tokens':100}
        name,args=next(self.steps)
        return {'id':'resp-'+str(len(self.requests)),'model':b.MODEL,'service_tier':'default','status':'completed','usage':{'input_tokens':100,'output_tokens':100},'output':[{'type':'reasoning','encrypted_content':'DO NOT SAVE'},{'type':'function_call','name':name,'call_id':str(len(self.requests)),'arguments':json.dumps(args)}]}
class Battery(unittest.TestCase):
    def setUp(self):self.c=b.validate(json.loads(b.CONFIG.read_text()));self.cases=create_cases();self.case=self.cases[0]
    def response(self,case,n=0):
        return copy.deepcopy(case['oracle']['accepted'][n])|{'evidence_ids':case['oracle']['required_evidence']}
    def test_all_cases_and_allowed_alternatives_pass(self):
        for case in self.cases:
            for i in range(len(case['oracle']['accepted'])):
                with self.subTest(case=case['id'],i=i):self.assertTrue(b.score(case,self.response(case,i))['passed'])
        self.assertEqual(self.cases,json.loads(b.CASES.read_text())['cases'])
    def test_critical_false_completion_bad_grant_scope_and_conflict(self):
        for identity,change in [('01A',{'action_state':'completed'}),('02A',{'action':'refund'}),('02C',{'action':'refund'}),('03A',{'action':'allocate'}),('04A',{'action':'send'}),('04B',{'target_ids':['C1','C2']}),('04C',{'payload_id':'P2'}),('05A',{'action':'ship'}),('06A',{'answer':'H1'}),('07C',{'action':'delete'})]:
            case=next(c for c in self.cases if c['id']==identity);r=b.score(case,self.response(case)|change)
            with self.subTest(case=identity):self.assertFalse(r['passed']);self.assertTrue(r['critical_errors'])
    def test_fabricated_and_irrelevant_sources_fail(self):
        r=b.score(self.case,self.response(self.case)|{'evidence_ids':['FAKE']});self.assertFalse(r['passed']);self.assertIn('fabricated_evidence_id',r['critical_errors'])
        r=b.score(self.case,self.response(self.case)|{'evidence_ids':['TRY-17','OPS-11']});self.assertTrue(r['passed']);self.assertFalse(r['critical_errors'])
    def test_clean_hold_fails_without_critical_inflation(self):
        c=self.cases[1];r=b.score(c,self.response(c)|{'action':'hold','action_state':'not_attempted'})
        self.assertFalse(r['passed']);self.assertTrue(r['false_block']);self.assertFalse(r['critical_errors'])
    def test_tool_loop_leakage_accounting_and_no_reasoning(self):
        answer=self.response(self.case);fake=Fake([('get_case',{}),('submit_decision',answer)])
        with tempfile.TemporaryDirectory() as d:
            ledger=b.BatteryLedger(Path(d)/'ledger.sqlite',self.c)
            r=b.trial(self.c,fake,ledger,b.SYSTEM,self.case)
            self.assertTrue(r['score']['passed']);self.assertEqual(len(r['calls']),2)
            self.assertEqual(ledger.summary()['calls'][0]['count'],2)
            self.assertNotIn('encrypted_content',json.dumps(r));self.assertNotIn('DO NOT SAVE',json.dumps(r))
            paid=[p for path,p in fake.requests if path=='/v1/responses']
            self.assertNotIn('oracle',json.dumps(paid));self.assertNotIn('challenge',json.dumps(paid));self.assertNotIn('01A',json.dumps(paid))
            case_output=json.loads(paid[1]['input'][-1]['output']);self.assertEqual(case_output,self.case['input'])
    def test_no_read_no_retry(self):
        fake=Fake([('submit_decision',self.response(self.case))])
        with tempfile.TemporaryDirectory() as d:
            r=b.trial(self.c,fake,b.BatteryLedger(Path(d)/'l',self.c),b.SYSTEM,self.case)
        self.assertFalse(r['score']['passed']);self.assertEqual(len(r['calls']),1);self.assertIsNone(r['decision'])
    def test_schedule_and_budget(self):
        design=b.schedule(self.cases,self.c['seed']);self.assertEqual(len(design),96)
        self.assertEqual(len({(x['case_id'],x['repetition'],x['condition']) for x in design}),96)
        self.assertEqual(design,b.schedule(self.cases,self.c['seed']));self.assertLessEqual(192*50360,10000000)
        with self.assertRaises(ValueError):b.validate(self.c|{'max_trial_spend_usd':'10.01'})
        with tempfile.TemporaryDirectory() as d:
            l=b.BatteryLedger(Path(d)/'l',self.c)
            for _ in range(192):l.reserve(50360)
            with self.assertRaises(b.PilotError):l.reserve(50360)
    def test_summary_tie_and_correction_regression(self):
        trials=[]
        for item in b.schedule(self.cases,self.c['seed']):
            c=next(c for c in self.cases if c['id']==item['case_id']);trials.append(item|{'kind':c['kind'],'family':c['family'],'calls':[],'stop_reason':None,'score':b.score(c,self.response(c))})
        s=b.summarize(self.cases,trials);self.assertEqual(s['labels'],{'both_correct':48});self.assertEqual(s['primary_gain_percentage_points'],0);self.assertFalse(s['useful_pilot_signal']);self.assertEqual(s['case_sign_flip_two_sided_p'],1)
        for t in trials:
            if t['condition']=='baseline' and t['kind']=='challenge':t['score']['passed']=False
        s=b.summarize(self.cases,trials);self.assertTrue(s['useful_pilot_signal']);self.assertEqual(s['labels']['corrected_by_prp'],28)
if __name__=='__main__':unittest.main()
