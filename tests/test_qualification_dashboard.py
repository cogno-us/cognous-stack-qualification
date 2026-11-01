"""Reject stale mappings, altered provenance and unsupported acceptance claims."""
import copy
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build_dashboard import load_data,markdown,cell,render_html
from qualification_results import workflow_manifest,validate_manifest,write_immutable,outcome


def snapshot(status='completed',conclusion='success'):
    return {'run':{'id':101,'head_sha':'a'*40,'run_attempt':1,'repository':{'full_name':'cogno-us/cognous-open-control-stack','private':False},'name':'Synthetic validation fixture','status':status,'conclusion':conclusion,'referenced_workflows':[{'path':'cogno-us/cognous-stack-qualification/.github/workflows/example.yml','sha':'b'*40}]},'jobs':[], 'artifacts':[{'name':'fixture','id':5,'digest':'sha256:'+'c'*64,'expired':True,'expires_at':'2020-01-01T00:00:00Z'}]}


class RunManifestTests(unittest.TestCase):
    def make(self,**kw):return workflow_manifest(snapshot(**kw),'cogno-us/cognous-open-control-stack','2026-10-15T18:00:00Z')
    def test_workflow_pass_does_not_accept_cases_or_components(self):
        r=self.make();self.assertEqual(r['execution']['outcome'],'PASS');self.assertEqual(r['scenario_results'],[])
        self.assertEqual(r['component_set']['completeness'],'UNVERIFIED');self.assertIsNone(r['observed_state'])
        self.assertEqual(r['qualification']['commits'],['b'*40])
    def test_pending_failure_cancel_and_neutral_stay_distinct(self):
        for status,conclusion,expected in [('queued',None,'RUNNING'),('in_progress',None,'RUNNING'),('completed','failure','FAIL'),('completed','cancelled','CANCELLED'),('completed','skipped','INCONCLUSIVE'),('completed','neutral','INCONCLUSIVE')]:
            with self.subTest(status=status,conclusion=conclusion):self.assertEqual(outcome(status,conclusion),expected)
    def test_expired_artifacts_and_provider_digest_basis_survive(self):
        evidence=self.make()['evidence'][1];self.assertTrue(evidence['expired_at_observation']);self.assertEqual(evidence['retention'],'EXPIRING_ARTIFACT');self.assertIn('not independently',evidence['digest_basis'])
    def test_private_and_wrong_repository_are_rejected(self):
        for change in ['private','repository']:
            s=snapshot()
            if change=='private':s['run']['repository']['private']=True
            else:s['run']['repository']['full_name']='other/repo'
            with self.assertRaises(ValueError):workflow_manifest(s,'cogno-us/cognous-open-control-stack','2026-10-15T18:00:00Z')
    def test_fabricated_scenario_or_release_claims_are_rejected(self):
        for field in ['scenario_results','assurance','component_set','observed_state','verdict_dimensions']:
            r=self.make()
            if field=='scenario_results':r[field]=[{'scenario_id':'D01','verdict':'PASS'}]
            elif field=='assurance':r[field]['release_authorized']=True
            elif field=='component_set':r[field]['completeness']='VERIFIED'
            elif field=='observed_state':r[field]={'effects':1}
            else:r[field]['authority_acceptance']='PASS'
            with self.subTest(field=field),self.assertRaises(ValueError):validate_manifest(r)
    def test_cannot_relabel_failed_workflow_successful(self):
        r=self.make(conclusion='failure');r['execution']['outcome']='PASS'
        with self.assertRaisesRegex(ValueError,'contradicts'):validate_manifest(r)
    def test_history_is_append_only_and_content_addressed(self):
        with tempfile.TemporaryDirectory() as temp:
            failed=self.make(conclusion='failure');first=write_immutable(failed,temp)
            later=self.make();later['observed_at']='2026-10-15T19:00:00Z';second=write_immutable(later,temp)
            self.assertNotEqual(first,second);self.assertEqual(json.loads(first.read_text())['execution']['outcome'],'FAIL')
            self.assertEqual(first.stem,hashlib.sha256(first.read_bytes()).hexdigest());self.assertEqual(first,write_immutable(failed,temp))
    def test_missing_or_non_utc_observation_is_rejected(self):
        for value in ['','2026-10-15T18:00:00','2026-10-15T18:00:00+01:00']:
            r=self.make();r['observed_at']=value
            with self.subTest(value=value),self.assertRaises(ValueError):validate_manifest(r)


class CoverageTests(unittest.TestCase):
    def fixture(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name)
        mapping=json.loads((ROOT/'scenarios/coverage-map.json').read_text())
        paths={'scenarios/catalog.json','scenarios/coverage-map.json','scenarios/ai-security-wiki/catalog.json','migrations/cross-component-2026-10-15.json'}
        paths.update(t['path'] for m in mapping['mappings'] for t in m['tests'])
        for relative in paths:
            p=root/relative;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/relative,p)
        return root
    def change_map(self,root,change):
        p=root/'scenarios/coverage-map.json';d=json.loads(p.read_text());change(d['mappings']);p.write_text(json.dumps(d))
    def test_catalog_is_fully_mapped_without_scenario_acceptance(self):
        d=load_data();self.assertEqual(len(d['scenarios']),40);self.assertEqual({m['scenario_verdict'] for m in d['scenarios']},{'NOT RUN'})
        self.assertEqual(sum(bool(m['tests']) for m in d['scenarios']),33)
    def test_duplicate_or_missing_case_is_rejected(self):
        for mutate in [lambda rows:rows.pop(),lambda rows:rows.append(copy.deepcopy(rows[0]))]:
            root=self.fixture();self.change_map(root,mutate)
            with self.assertRaisesRegex(ValueError,'exactly once'):load_data(root)
    def test_requirement_change_requires_explicit_remapping(self):
        root=self.fixture();p=root/'scenarios/catalog.json';c=json.loads(p.read_text());c['scenarios'][0]['required_observation']='Different contract';p.write_text(json.dumps(c))
        with self.assertRaisesRegex(ValueError,'Scenario changed'):load_data(root)
    def test_changed_test_bytes_are_not_silently_covered(self):
        root=self.fixture();row=json.loads((root/'scenarios/coverage-map.json').read_text())['mappings'][0]['tests'][0];p=root/row['path'];p.write_text(p.read_text()+'\n# changed\n')
        with self.assertRaisesRegex(ValueError,'Mapped test changed'):load_data(root)
    def test_missing_test_symbol_or_wrong_license_is_rejected(self):
        for field,value in [('symbol','test_invented'),('license','CC0-1.0')]:
            root=self.fixture();self.change_map(root,lambda rows:rows[0]['tests'][0].update({field:value}))
            with self.subTest(field=field),self.assertRaises(ValueError):load_data(root)
    def test_traversal_and_forged_case_verdict_are_rejected(self):
        for change in [lambda rows:rows[0]['tests'][0].update(path='../../escape.py'),lambda rows:rows[0].update(scenario_verdict='PASS')]:
            root=self.fixture();self.change_map(root,change)
            with self.assertRaises(ValueError):load_data(root)
    def test_markdown_treats_metadata_as_text(self):
        self.assertNotIn('](javascript:',cell('x](javascript:bad)'))
        d=load_data();r=copy.deepcopy(d['runs'][0]);r['execution']['name']='x](javascript:bad)<script>alert(1)</script>';d['runs']=[r]
        rendered=markdown(d);self.assertNotIn('<script>',rendered);self.assertNotIn('](javascript:',rendered)
    def test_metadata_cannot_escape_json_script_boundary(self):
        from html.parser import HTMLParser
        class Scripts(HTMLParser):
            def __init__(self):super().__init__();self.tags=[]
            def handle_starttag(self,tag,attrs):self.tags.append(tag)
        text=render_html('<script type="application/json">__QUALIFICATION_DATA__</script>',{'name':'</script><img src=x onerror=evil()><script>'})
        parser=Scripts();parser.feed(text);self.assertEqual(parser.tags,['script']);self.assertIn('\\u003c',text)
    def test_manifest_bytes_must_match_content_address(self):
        root=self.fixture();p=write_immutable(RunManifestTests().make(),root/'results/workflows');p.write_text(p.read_text()+' ')
        with self.assertRaisesRegex(ValueError,'commitment mismatch'):load_data(root)
    def test_multiple_snapshots_are_history_not_multiple_trials(self):
        root=self.fixture();r=RunManifestTests().make(conclusion='failure');write_immutable(r,root/'results/workflows');r=copy.deepcopy(r);r['execution'].update(conclusion='success',outcome='PASS');r['observed_at']='2026-10-15T19:00:00Z';write_immutable(r,root/'results/workflows')
        d=load_data(root);self.assertEqual(len(d['runs']),1);self.assertEqual(len(d['snapshots']),2);self.assertEqual(d['runs'][0]['execution']['outcome'],'PASS')


if __name__=='__main__':unittest.main()
