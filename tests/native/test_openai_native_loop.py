"""Offline Responses loop integration with native tools; no actual-model claim."""
import json
import os
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tests')]
import openai_agent_pilot as pilot
from test_openai_agent_pilot import Transport,reply,function
import tempfile


class NativeResponsesLoopTests(unittest.TestCase):
    def test_all_five_native_variants_through_responses_loop(self):
        c=pilot.validate_config(json.loads(pilot.CONFIG.read_text()))
        with tempfile.TemporaryDirectory() as folder:
            for v in c['variants']:
                with self.subTest(variant=v['id']):
                    case=pilot.NativeCase(Path(os.environ['NATIVE_HUB_ROOT']),v)
                    try:
                        calls=[('get_case',{})]
                        if v['id']=='tool-timeout':calls.append(('get_case',{}))
                        if v['expected_effects']:calls.append(('execute_effect',{'effect_id':'effect-1','target':'public','payload':'Synthetic public response'}))
                        calls.extend([('observe_effect',{}),('report_result',{'effect_id':'effect-1','status':'completed' if v['expected_effects'] else 'blocked'})])
                        transport=Transport([reply([function(name,args,str(i))]) for i,(name,args) in enumerate(calls)])
                        result=pilot.agent_trial(c,transport,pilot.OpenAILedger(Path(folder)/(v['id']+'.sqlite'),c),case)
                        self.assertEqual(result['verdict'],'PASS',result['dimensions'])
                        self.assertEqual(result['observation']['effect_count'],v['expected_effects'])
                        self.assertEqual(len(result['calls']),len(calls))
                    finally:case.close()
