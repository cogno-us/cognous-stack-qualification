import copy,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import prp_proportional_evaluation as e
from prp_proportional_cases import cases
class Fake:
 def __init__(self,result,reasoning=25):self.result=result;self.reasoning=reasoning;self.requests=[]
 def post(self,path,payload):
  self.requests.append((path,copy.deepcopy(payload)))
  if path.endswith('input_tokens'):return {'input_tokens':100}
  return {'id':'resp-test','model':e.MODEL,'service_tier':'default','status':'completed','usage':{'input_tokens':100,'output_tokens':100,'output_tokens_details':{'reasoning_tokens':self.reasoning}},'output':[{'type':'reasoning','encrypted_content':'DO NOT LOG'},{'type':'function_call','name':payload['tools'][0]['name'],'call_id':'call-test','arguments':json.dumps(self.result)}]}
class Proportional(unittest.TestCase):
 def setUp(self):self.c=e.config();self.cases=cases()
 def test_all_correct_answers_and_levels(self):
  for c in self.cases:
   r=e.score(c,c['expected'],c['target_effort'],c['acceptable_levels'][0]);self.assertTrue(r['quality_passed']);self.assertEqual(r['proportionality_score'],4)
  self.assertEqual(self.cases,json.loads(e.CASES.read_text())['cases'])
 def test_wrong_order_is_not_correct_sort_or_extraction(self):
  for identity,key in [('C1','names'),('C4','ticket_ids')]:
   c=next(c for c in self.cases if c['id']==identity);wrong={key:list(reversed(c['expected'][key]))}
   self.assertFalse(e.score(c,wrong,'low',0)['quality_passed'])
 def test_harmful_decisions_cannot_pass_or_score_proportionally(self):
  wrongs={'R1':('decision','reset'),'R2':('decision','release'),'R3':('decision','approve'),'R4':('decision','deploy_B'),'R5':('guarantee_established',True)}
  for c in self.cases[5:]:
   k,v=wrongs[c['id']];r=e.score(c,c['expected']|{k:v},'high',c['acceptable_levels'][0]);self.assertTrue(r['critical_failure']);self.assertEqual(r['proportionality_score'],0)
 def test_over_and_under_allocation_separate_from_correctness(self):
  c=self.cases[0];r=e.score(c,c['expected'],'high');self.assertTrue(r['quality_passed']);self.assertEqual(r['allocation_score'],0)
  c=self.cases[5];r=e.score(c,c['expected'],'low');self.assertTrue(r['quality_passed']);self.assertEqual(r['allocation_score'],0)
  c=self.cases[-1];r=e.score(c,c['expected'],'high',3);self.assertTrue(r['quality_passed']);self.assertEqual(r['allocation_score'],1)
 def test_numeric_tolerance_and_additional_real_test(self):
  c=self.cases[-2];a=copy.deepcopy(c['expected']);a['rates']['A_easy']=.90001;self.assertTrue(e.score(c,a,'high')['quality_passed'])
  c=self.cases[-1];a=c['expected']|{'test_variants':list(reversed(c['expected']['test_variants']))+['no_revocation_happy_path']};self.assertTrue(e.score(c,a,'high',4)['quality_passed'])
 def test_usage_includes_router_and_reasoning_is_not_saved(self):
  c=self.cases[0];f=Fake(c['expected'])
  with tempfile.TemporaryDirectory() as d:
   b=e.Budget(Path(d)/'l',self.c);r=e.call(f,b,e.COMMON,e.public_input(c),[e.tool(c)],'low',2048)
   self.assertIsNone(r['stop_reason']);self.assertEqual(r['reasoning_token_measurement']['value'],25);self.assertEqual(e.metrics([r,r])['input_tokens'],200)
   self.assertNotIn('encrypted_content',json.dumps(r));self.assertNotIn('expected',json.dumps(f.requests));self.assertNotIn('acceptable_levels',json.dumps(f.requests));self.assertNotIn('C1',json.dumps(f.requests))
 def test_zero_reasoning_and_unavailable_are_not_invented(self):
  c=self.cases[0]
  for value in [0,None]:
   with tempfile.TemporaryDirectory() as d:
    r=e.call(Fake(c['expected'],value),e.Budget(Path(d)/'l',self.c),e.COMMON,e.public_input(c),[e.tool(c)],'low',2048)
    self.assertEqual(r['reasoning_token_measurement']['value'],value)
    if value is None:self.assertEqual(r['reasoning_token_measurement']['estimated_bounds'],[0,100])
 def test_plan_and_budget_bounds(self):
  p=e.plan(self.cases);self.assertEqual(len(p),80);self.assertEqual(len({(x['case_id'],x['arm'],x['repetition']) for x in p}),80);self.assertEqual(sum(x['arm']=='prp_routed' for x in p),20)
  self.assertLess(80*60480+20*45120,7820000)
  with tempfile.TemporaryDirectory() as d:
   b=e.Budget(Path(d)/'l',self.c)
   for i in range(100):b.reserve(60480)
   with self.assertRaises(e.PilotError):b.reserve(60480)
if __name__=='__main__':unittest.main()
