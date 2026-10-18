"""Static guard for the batch-1 adversarial tests (process/adversarial). Needs no component checkout; nothing is executed here."""
import ast
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
ADV = ROOT / 'process/adversarial'
VOCAB = ['prevented', 'detected only', 'reproduced failure', 'inconclusive', 'not applicable', 'not tested']


class AdversarialBatch1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch = json.loads((ADV / 'batch-1.json').read_text(encoding='utf-8'))
        cls.plan = json.loads((ADV / 'ideas.json').read_text(encoding='utf-8'))
        cls.readme = (ADV / 'README.md').read_text(encoding='utf-8')
        cls.components = json.loads((ADV / 'components.json').read_text(encoding='utf-8'))['components']

    def test_batch_matches_the_plan_and_never_feeds_the_verdict(self):
        self.assertIs(self.batch['feeds_v1_validation'], False)
        self.assertIs(self.batch['catalogue_scenarios'], False)
        self.assertEqual(self.batch['result_vocabulary'], VOCAB)
        self.assertEqual([t['id'] for t in self.batch['tests']], [b['id'] for b in self.plan['batch_1']])
        self.assertEqual([t['id'] for t in self.batch['tests']], ['T%02d' % n for n in range(1, 21)])

    def test_readme_table_agrees_with_batch(self):
        rows = {}
        for line in self.readme.splitlines():
            m = re.match(r'\| (T\d\d) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|', line)
            if m:
                rows[m.group(1)] = (m.group(2).strip(), m.group(4).strip())
        titles = {b['id']: b['title'] for b in self.plan['batch_1']}
        self.assertEqual(sorted(rows), ['T%02d' % n for n in range(1, 21)])
        for t in self.batch['tests']:
            self.assertIn(t['status'], VOCAB, t['id'])
            self.assertEqual(rows[t['id']][1], t['status'], t['id'])
            self.assertTrue(titles[t['id']].startswith(rows[t['id']][0].split(':')[0][:30]), t['id'])
        cases = self.batch['run']['cases']
        self.assertIn('**%d passed, %d xfailed, 0 failed, 0 skipped**' % (cases['passed'], cases['xfailed']), self.readme)

    def test_every_module_states_what_it_does_not_prove_and_never_skips(self):
        for t in self.batch['tests']:
            path = ADV / t['file']
            self.assertTrue(path.is_file(), t['file'])
            source = path.read_text(encoding='utf-8')
            tree = ast.parse(source)
            doc = ast.get_docstring(tree) or ''
            self.assertTrue(doc.startswith(t['id'] + '. '), t['id'])
            self.assertIn('Does not prove', doc, t['id'])
            self.assertNotRegex(source, r'pytest\.skip\(|mark\.skip\b|mark\.skipif|importorskip', t['id'])
            for m in re.finditer(r'mark\.xfail\(([^)]*)\)', source):
                self.assertIn('strict=True', m.group(1), t['id'])
                self.assertIn('raises=AssertionError', m.group(1), t['id'])

    def test_xfail_count_matches_the_recorded_run(self):
        xfail_tests = [t['id'] for t in self.batch['tests'] if 'xfail' in t['summary'] or t['status'] == 'reproduced failure']
        for tid in xfail_tests:
            src = (ADV / next(t['file'] for t in self.batch['tests'] if t['id'] == tid)).read_text(encoding='utf-8')
            self.assertIn('mark.xfail(', src, tid)

    def test_components_are_full_revisions(self):
        expected = {'control_plane': '3cd17ead', 'runtime': '11de097c', 'verifier': 'bb34c961', 'replay': '253c3a61',
                    'evidence_pack': '20cb11ea', 'odes': '0663d5a2', 'hub': 'afca5bbd'}
        for key, prefix in expected.items():
            rev = self.components[key]['revision']
            self.assertRegex(rev, r'^[0-9a-f]{40}$', key)
            self.assertTrue(rev.startswith(prefix), key)

    def test_public_text_carries_no_exploit_detail(self):
        """Suspected defects are named neutrally in public text (README and batch-1.json); the detail goes to the private channel."""
        public = self.readme + json.dumps(self.batch)
        self.assertIn('private channel', public)
        for word in ('exploit', 'recipe', 'proof of concept', 'PoC'):
            self.assertNotIn(word, public)


if __name__ == '__main__':
    unittest.main()
