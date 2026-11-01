"""Static consistency guard for the adversarial test plan (hypotheses and plan only; nothing is executed)."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT/'docs/adversarial-test-plan.md'
DATA = ROOT/'process/adversarial/ideas.json'
CLASSES = {'COV', 'PART', 'OFFL', 'CAP', 'NA'}
LABEL_ORDER = ['COV', 'PART', 'OFFL', 'CAP', 'NA']


class AdversarialPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text(encoding='utf-8'))
        cls.doc = DOC.read_text(encoding='utf-8')

    def test_ids_are_unique_and_complete(self):
        ids = [i['id'] for i in self.data['ideas']]
        self.assertEqual(len(ids), 75)
        self.assertEqual(len(set(ids)), 75)
        expected = [g + '%02d' % n for g, lo, hi in [('A', 1, 8), ('B', 9, 16), ('C', 17, 24), ('D', 25, 32), ('E', 33, 40), ('F', 41, 46),
                                                        ('G', 47, 54), ('H', 55, 66), ('I', 67, 75)] for n in range(lo, hi + 1)]
        self.assertEqual(sorted(ids), sorted(expected))
        self.assertEqual([c['id'] for c in self.data['chains']], ['CH%d' % n for n in range(1, 9)])

    def test_vocabularies_and_hypothesis_status(self):
        for i in self.data['ideas']:
            self.assertIn(i['cls'], CLASSES, i['id'])
            self.assertEqual(i['result'], 'not tested', i['id'])
        self.assertEqual(self.data['result_vocabulary'], ['prevented', 'detected only', 'reproduced failure', 'inconclusive', 'not applicable', 'not tested'])
        self.assertIn('HYPOTHESIS', self.data['status'])
        self.assertIn('Nothing here is a finding', self.doc)
        self.assertNotRegex(self.doc.lower(), r'production[- ]ready(?! claim)')

    def test_counts_match_document(self):
        labels = self.data['classification_vocabulary']
        rows = {}
        for line in self.doc.splitlines():
            for k in LABEL_ORDER:
                if line.startswith('| ' + labels[k] + ' |'):
                    cells = [c.strip() for c in line.strip('|').split('|')]
                    rows[k] = (int(cells[1]), int(cells[2]))
        self.assertEqual(set(rows), CLASSES)
        for k in CLASSES:
            self.assertEqual(rows[k][0], sum(1 for i in self.data['ideas'] if i['cls'] == k), k)
            self.assertEqual(rows[k][1], sum(1 for c in self.data['chains'] if c['cls'] == k), k)
            self.assertEqual(self.data['counts']['ideas'].get(k, 0), rows[k][0])
        self.assertEqual(sum(r[0] for r in rows.values()), 75)
        self.assertEqual(sum(r[1] for r in rows.values()), 8)

    def test_every_idea_and_test_is_in_the_document(self):
        for i in self.data['ideas']:
            self.assertRegex(self.doc, r'\| %s \|' % i['id'])
        for b in self.data['batch_1']:
            self.assertIn('### %s. ' % b['id'], self.doc)

    def test_batch_is_bounded_and_complete(self):
        batch = self.data['batch_1']
        self.assertLessEqual(len(batch), 20)
        ids = {i['id'] for i in self.data['ideas']}
        required = ['id', 'title', 'ideas', 'cap', 'comps', 'entry', 'inv', 'fixture', 'expected', 'pos', 'resid']
        for b in batch:
            for f in required:
                self.assertTrue(b.get(f), (b['id'], f))
            self.assertTrue(set(b['ideas']) <= ids, b['id'])
        for i in self.data['ideas']:
            for t in i['batch']:
                self.assertIn(i['id'], next(b for b in batch if b['id'] == t)['ideas'])

    def test_uncovered_ideas_are_preserved_with_a_gap(self):
        for i in self.data['ideas']:
            if i['cls'] != 'COV':
                self.assertTrue(i['gap'], i['id'])
            if i['cls'] in ('OFFL', 'CAP'):
                self.assertTrue(i['gap'] and i['entry'], i['id'])

    def test_qualification_repo_citations_exist(self):
        seen = 0
        for i in self.data['ideas']:
            for e in i['existing']:
                if e['repo'] != 'QL':
                    continue
                f = ROOT/e['path']
                self.assertTrue(f.is_file(), (i['id'], e['path']))
                self.assertRegex(f.read_text(encoding='utf-8', errors='replace'), r'def %s\b' % re.escape(e['test']), (i['id'], e['test']))
                seen += 1
        self.assertGreater(seen, 100)

    def test_document_makes_no_execution_claim(self):
        for b in self.data['batch_1']:
            self.assertIn('Current result: `not tested`', self.doc)
        self.assertIn('No attack or exploit probe was run', self.doc)


if __name__ == '__main__':
    unittest.main()
