import sys,json,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import prp_quality_evaluation as b
from copy import deepcopy

class Quality(unittest.TestCase):
 def setUp(self):self.cases=json.loads(b.CASES.read_text())['cases']
 def decision(self,c,e=None):
  e=e or c['oracle']['accepted'][0]
  return {k:(c['oracle']['required_evidence'] if k=='evidence_ids' else e[k]) for k in c['output_fields']}
 def test_all_expected_variants(self):
  for c in self.cases:
   for e in c['oracle']['accepted']:
    with self.subTest(case=c['id']):self.assertTrue(b.score(c,self.decision(c,e))['passed'])
 def test_actions_and_real_false_blocks(self):
  for c in self.cases:
   d=self.decision(c)
   if c['id'] in ('03C','08A','08B','08C','05C'):
    d['action']='none';self.assertTrue(b.score(c,d)['passed']);self.assertFalse(b.score(c,d)['false_block'])
   if c['kind'] in ('clean','routine'):
    d['action']='clarify';self.assertTrue(b.score(c,d)['false_block']);self.assertFalse(b.score(c,d)['passed'])
 def test_dangerous_effects(self):
  for c in self.cases:
   d=self.decision(c);d['action']='export'
   self.assertFalse(b.score(c,d)['passed']);self.assertIn('effect_outside_allowed_case_consequence',b.score(c,d)['critical_errors'])
 def test_decisive_evidence(self):
  for c in self.cases:
   d=self.decision(c);d['evidence_ids']=[];self.assertFalse(b.score(c,d)['passed'])
   d=self.decision(c);d['evidence_ids']+=['FABRICATED'];self.assertTrue(b.score(c,d)['execution_failure'])
 def test_old_metadata_and_prose_defects_absent(self):
  for c in self.cases:
   if c['id'] not in ('03C','06A','06B','08A','08B','08C'):self.assertNotIn('answer',c['output_fields'])
   self.assertNotIn('oracle',json.dumps(b.case_tools(c)))
  c=next(c for c in self.cases if c['id']=='06C');d=self.decision(c)
  self.assertFalse(b.score(c,d)['critical_errors']);d['warranty_status']='covered';self.assertIn('unsupported_entitlement',b.score(c,d)['critical_errors'])
 def test_order_and_substantive_facts(self):
  c=next(c for c in self.cases if c['id']=='08A');d=self.decision(c);d['answer']='Mira, Abel, Noor';self.assertFalse(b.score(c,d)['passed'])
  for identity,key,val in [('03B','units',9),('01A','action_state','completed'),('05A','history_retained',False),('06A','answer','H1'),('04B','target_ids',['C1','C2']),('04C','payload_id','P2')]:
   c=next(c for c in self.cases if c['id']==identity);d=self.decision(c);d[key]=val;self.assertFalse(b.score(c,d)['passed'])
 def test_schema_and_schedule(self):
  import jsonschema
  for c in self.cases:
   for tool in b.case_tools(c):jsonschema.Draft202012Validator.check_schema(tool['parameters'])
  config=b.validate(json.loads(b.CONFIG.read_text()));plan=b.schedule(self.cases,config['seed']);self.assertEqual(len(plan),96)
  self.assertEqual(len({tuple(x.values()) for x in plan}),96)
 def test_budget_cap(self):
  from claude_agent_pilot import PilotError
  with tempfile.TemporaryDirectory() as t:
   l=b.BatteryLedger(Path(t)/'ledger',json.loads(b.CONFIG.read_text()))
   for _ in range(192):l.reserve(50360)
   with self.assertRaises(PilotError):l.reserve(50360)
   self.assertLessEqual(192*50360+3294292,20000000)

if __name__=='__main__':unittest.main()
