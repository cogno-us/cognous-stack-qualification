"""Security-runtime profiles stay nonauthorizing and the historical F3 run stays reproducible."""
import json
from pathlib import Path
import re
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = ROOT/'process/security-runtime-candidate-20261016.json'
F5B = ROOT/'process/security-runtime-f5b-20261016.json'
WORKFLOWS = ROOT/'.github/workflows'


class SecurityRuntimeProfiles(unittest.TestCase):
    def test_profiles_are_nonauthorizing_full_merged_only(self):
        for path in (HISTORICAL, F5B):
            profile = json.loads(path.read_text())
            with self.subTest(profile=path.name):
                for key in ('selected', 'reference_release_authorized', 'production_deployment_authorized'):
                    self.assertIs(profile[key], False)
                self.assertEqual((profile['phase'], profile['qualification_input_status']), ('full', 'merged_only'))
                for spec in profile['components'].values():
                    self.assertRegex(spec['revision'], r'^[0-9a-f]{40}$')

    def test_historical_profile_uses_runner_defaults(self):
        profile = json.loads(HISTORICAL.read_text())
        for key in ('suite_generation', 'exchange_compatibility_profile', 'additional_source_hashes'):
            self.assertNotIn(key, profile)
        runner = (ROOT/'tools/run_security_runtime.py').read_text()
        self.assertIn("DEFAULT_EXCHANGE_PROFILE = 'security-runtime-candidate-20261016'", runner)
        self.assertIn("DEFAULT_SUITE_GENERATION = 'security'", runner)
        self.assertIn("PROFILE = ROOT/'process/security-runtime-candidate-20261016.json'", runner)

    def test_f5b_profile_selects_separate_generation(self):
        profile = json.loads(F5B.read_text())
        self.assertEqual(profile['suite_generation'], 'f5b')
        self.assertEqual(profile['exchange_compatibility_profile'], 'security-runtime-f5b-20261016')
        historical = json.loads(HISTORICAL.read_text())['components']
        self.assertEqual(set(profile['components']), set(historical))
        for name, spec in profile['components'].items():
            self.assertEqual(spec['repository'], historical[name]['repository'])
            self.assertNotEqual(spec['revision'], historical[name]['revision'])
        for name in profile['additional_source_hashes']:
            self.assertTrue((ROOT/name).is_file(), name)

    def test_workflows_pin_actions_and_drop_credentials(self):
        for name in ('security-runtime-qualification.yml', 'security-runtime-f5b-qualification.yml'):
            doc = yaml.safe_load((WORKFLOWS/name).read_text())
            for step in doc['jobs']['actual-components']['steps']:
                uses = step.get('uses')
                if uses:
                    with self.subTest(workflow=name, uses=uses):
                        self.assertRegex(uses, r'@[0-9a-f]{40}$')
                if uses and uses.startswith('actions/checkout@'):
                    self.assertIs(step['with']['persist-credentials'], False)
                for line in step.get('run', '').splitlines():
                    if 'pip install' in line:
                        self.assertIn('--require-hashes', line)
        f5b = (WORKFLOWS/'security-runtime-f5b-qualification.yml').read_text()
        self.assertEqual(len(re.findall(r'--profile process/security-runtime-f5b-20261016\.json', f5b)), 2)


    def test_native_audit_open_leaves_wal_database_untouched(self):
        import sqlite3, sys, tempfile
        sys.path.insert(0, str(ROOT/'tools'))
        from summarize_security_runtime import rows
        with tempfile.TemporaryDirectory() as temp:
            db = Path(temp)/'refunds.sqlite3'
            con = sqlite3.connect(db); con.execute('pragma journal_mode=wal')
            con.execute('create table effects (effect_id text)'); con.execute("insert into effects values ('e')")
            con.commit(); con.close()
            before = sorted(p.name for p in Path(temp).iterdir()); digest = db.read_bytes()
            self.assertEqual(rows(db, 'select effect_id from effects'), [{'effect_id': 'e'}])
            self.assertEqual(sorted(p.name for p in Path(temp).iterdir()), before)
            self.assertEqual(db.read_bytes(), digest)


if __name__ == '__main__':
    unittest.main()
