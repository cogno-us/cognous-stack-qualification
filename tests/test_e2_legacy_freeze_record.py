"""E-2: a freeze record without components_expected is not PASS proof (it was only a text note before).

The retained legacy g6-r10 record has no components_expected and an empty components map; it re-aggregated to PASS.
"""
import json
import unittest
from pathlib import Path

from agg_util import GOOD_FREEZE, aggregate, job, plan_entry, selector_row, v

ROW = [selector_row('R-1', 'alpha', 'test_selected')]
OK = [('t', 'test_selected', 'passed')]
RETAINED = Path(__file__).resolve().parents[1] / 'results/v1-validation/v1-2026-10-16-a/g6-r10-39563114678/jobs/freeze/freeze-verification.json'


def run(freeze):
    return aggregate([job('alpha', 'PASS', OK)], ROW, freeze=freeze, plan=[plan_entry('alpha')])


class LegacyFreezeRecord(unittest.TestCase):
    def test_complete_record_gives_pass(self):
        s = run(GOOD_FREEZE)
        self.assertEqual((s['freeze_status'], s['selected_v1_verdict']), ('PASS', 'PASS'))

    def test_record_without_components_expected_is_a_freeze_problem_and_incomplete(self):
        for rec in ({'status': 'PASS'}, {'status': 'PASS', 'components': {}}, {'status': 'PASS', 'components': {'alpha': {}}}):
            s = run(rec)
            self.assertEqual(s['freeze_status'], 'FAIL', rec)
            self.assertEqual(s['selected_v1_verdict'], 'INCOMPLETE', rec)
            self.assertIn('components_expected', s['verdict_note'])

    def test_components_that_differ_from_components_expected_are_a_problem(self):
        self.assertEqual(run({'status': 'PASS', 'components': {'alpha': {}, 'beta': {}}, 'components_expected': ['alpha']})['freeze_status'], 'FAIL')
        self.assertEqual(run({'status': 'PASS', 'components': {'alpha': {}}, 'components_expected': ['alpha', 'beta']})['freeze_status'], 'FAIL')

    def test_a_failed_check_under_a_pass_status_is_a_problem(self):
        rec = dict(GOOD_FREEZE, checks=[{'check': 'x', 'status': 'FAIL'}])
        self.assertEqual(run(rec)['freeze_status'], 'FAIL')

    def test_the_retained_legacy_record_is_not_proof(self):
        rec = json.loads(RETAINED.read_text())
        self.assertNotIn('components_expected', rec)
        self.assertIsNotNone(v.freeze_record_problem(rec, []))


if __name__ == '__main__':
    unittest.main()
