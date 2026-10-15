"""Exercise false assurance rejection and native observer access boundaries."""
import copy
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from trajectory_contract import evaluate, calibrate, digest, validate_record
from run_serial_qualification import observe


class TrajectoryTests(unittest.TestCase):
    def case(self):
        return {'responses':[{'status':'accepted'}],'events':[],
                'observation':{'effect_count':1,'payloads':['synthetic'],'read_only_verified':True},
                'attempts':[{'attempt_id':'a','effect_id':'effect'}]}

    def test_calibration_detects_all_critical_defects_and_missing_observation(self):
        c=calibrate()
        self.assertEqual(c['critical_defects_detected'],c['critical_defects_total'])
        self.assertEqual(c['false_alarms'],0)
        self.assertTrue(c['missing_observation_inconclusive'])

    def test_violation_cannot_be_downgraded_by_missing_evidence(self):
        c=self.case();c['observation']=None;c['claimed_complete']=True
        r=evaluate(c,{'effect_count':1,'response':'accepted'})
        self.assertEqual(r['verdict'],'FAIL');self.assertTrue(r['missing'])

    def test_wrong_payload_duplicate_attempt_and_rewritten_ack_are_failures(self):
        for change in ('payload','attempt','ack'):
            c=self.case();expected={'effect_count':1,'response':'accepted','payload':'synthetic','recovery':True}
            c['attempts']=[{'attempt_id':'a','effect_id':'effect','acknowledgement':'UNKNOWN'},
                           {'attempt_id':'b','effect_id':'effect','acknowledgement':'RECEIVED'}]
            if change=='payload': c['observation']['payloads']=['substituted']
            if change=='attempt': c['attempts'][1]['attempt_id']='a'
            if change=='ack': c['attempts'][0]['acknowledgement']='RECEIVED'
            self.assertEqual(evaluate(c,expected)['verdict'],'FAIL')

    def test_missing_or_unverified_observer_cannot_pass(self):
        c=self.case();c['observation']['read_only_verified']=False
        self.assertEqual(evaluate(c,{'effect_count':1,'response':'accepted'})['verdict'],'INCONCLUSIVE')

    def test_observer_write_probe_is_refused_and_reads_source_of_truth(self):
        with tempfile.TemporaryDirectory() as temp:
            db=Path(temp)/'test.db'
            with sqlite3.connect(db) as c:
                c.executescript('CREATE TABLE effects(id TEXT,payload TEXT); CREATE TABLE objects(kind TEXT,id TEXT,body TEXT);')
                c.execute("INSERT INTO effects VALUES('e','payload')")
            o=observe(db)
            self.assertEqual(o['effect_count'],1);self.assertTrue(o['read_only_verified'])
            with sqlite3.connect(db) as c:self.assertEqual(c.execute('SELECT count(*) FROM effects').fetchone()[0],1)

    def test_fixed_plan_and_schema_reject_empty_or_fabricated_result(self):
        import jsonschema
        schema=json.loads((ROOT/'schemas/trajectory-evidence-v2.schema.json').read_text())
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate({},schema)

    def test_saved_evidence_is_recomputed_not_trusted(self):
        paths=list((ROOT/'results/serial').glob('*/record.json')) if (ROOT/'results/serial').exists() else []
        for path in paths:
            record=json.loads(path.read_text());plan=json.loads((path.parent/'plan.json').read_text());catalog=json.loads((ROOT/'scenarios/catalog.json').read_text())
            validate_record(record,plan,catalog,artifact_root=path.parent)
            changed=copy.deepcopy(record);changed['cases'][0]['observation']['effect_count']=9
            with self.assertRaisesRegex(ValueError,'commitment|contradicts'):validate_record(changed,plan,catalog)
            changed=copy.deepcopy(record);changed['cases'].pop()
            with self.assertRaisesRegex(ValueError,'Missing planned'):validate_record(changed,plan,catalog)
            changed=copy.deepcopy(record);changed['cases'][0]['provenance']={}
            with self.assertRaisesRegex(ValueError,'provenance'):validate_record(changed,plan,catalog)
            changed=copy.deepcopy(record);changed['plan_sha256']='f'*64
            with self.assertRaisesRegex(ValueError,'Plan commitment'):validate_record(changed,plan,catalog)
            changed=copy.deepcopy(record);changed['sources']['hub']['dirty']=True
            with self.assertRaises(Exception):validate_record(changed,plan,catalog)


if __name__=='__main__':unittest.main()
