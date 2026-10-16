import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import prp_openai_evaluation as p

class Fake:
    def __init__(self,steps):self.steps=iter(steps);self.paid=0
    def post(self,path,payload):
        if path.endswith('input_tokens'):return {'input_tokens':100}
        self.paid+=1
        name,args=next(self.steps)
        return {'id':'resp_'+str(self.paid),'model':p.MODEL,'service_tier':'default','status':'completed','usage':{'input_tokens':100,'output_tokens':20},'output':[{'type':'reasoning','summary':[],'encrypted_content':'never persist this'},{'type':'function_call','call_id':str(self.paid),'name':name,'arguments':json.dumps(args)}]}

class Controls(unittest.TestCase):
    def setUp(self):
        self.c=p.validate(json.loads(p.CONFIG.read_text()))
        self.case={'hypotheses':['H0','H1'],'prior':[.5,.5],'actions':{'gather':{}},'stop_expected_loss':1.2,'likelihoods':{'null':[.5,.5]}}
    def run_trial(self,steps):
        with tempfile.TemporaryDirectory() as d:
            ledger=p.OpenAILedger(Path(d)/'ledger.sqlite',self.c)
            fake=Fake(steps);r=p.trial(self.c,fake,ledger,p.SYSTEM,self.case,'null')
            return r,fake,ledger.summary()
    def test_read_then_report_and_no_reasoning_log(self):
        report={'posterior':[.5,.5],'action':'gather','rationale':'The evidence is neutral.'}
        r,f,b=self.run_trial([('get_case',{}),('report_decision',report)])
        self.assertEqual(r['decision'],report);self.assertIsNone(r['stop_reason']);self.assertEqual(f.paid,2)
        self.assertNotIn('encrypted_content',json.dumps(r));self.assertEqual(b['calls'][0]['count'],2)
        self.assertNotIn('null',json.dumps(r['tool_trace'][0]['result']))
    def test_report_without_read_fails_without_retry(self):
        r,f,_=self.run_trial([('report_decision',{'posterior':[.5,.5],'action':'gather','rationale':'x'})])
        self.assertIsNone(r['decision']);self.assertEqual(f.paid,1);self.assertEqual(r['stop_reason'],'Tool contract violation')
    def test_unknown_tool_and_bad_probabilities(self):
        r,f,_=self.run_trial([('shell',{})]);self.assertEqual(f.paid,1);self.assertIsNone(r['decision'])
        self.assertFalse(p.valid_report({'posterior':[True,0],'action':'gather','rationale':'x'},self.case))
    def test_design_and_bounds(self):
        design=p.schedule();self.assertEqual(len(design),18);self.assertEqual(len(set(design)),18)
        self.assertEqual(sum(c=='prp' for _,_,c in design),9)
        with self.assertRaises(ValueError):p.validate(self.c|{'max_trial_spend_usd':'3.01'})
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(p.instructions(Path(d),'baseline'),p.SYSTEM)
    def test_ambiguous_usage_keeps_reservation(self):
        with tempfile.TemporaryDirectory() as d:
            ledger=p.OpenAILedger(Path(d)/'ledger.sqlite',self.c);i=ledger.reserve(55360)
            with self.assertRaises(p.PilotError):ledger.settle(i,{})
            self.assertEqual(ledger.summary()['calls'][0]['state'],'RESERVED')

if __name__=='__main__':unittest.main()
