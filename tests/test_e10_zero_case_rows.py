"""E-10: a `tests` requirement row with no selectors, or with selector min 0, evaluated PASS with zero executed cases.
Zero executed cases is INCONCLUSIVE whatever min/selectors say, and malformed rows are refused by requirements validation."""
import json
import sys
import unittest
from pathlib import Path

from agg_util import aggregate, job, selector_row, v

ROOT = Path(__file__).resolve().parents[1]
REQS = ROOT / 'process/v1-validation/v1-2026-10-16-a/requirements.json'
INDEX = {'alpha': [('t', 'test_a', 'passed', {'kind': 'passed', 'unexpected_pass': False})]}


def status(row, index=INDEX):
    return v.evaluate_requirements({'requirements': [row]}, index, {})[0]


class ZeroExecutedCases(unittest.TestCase):
    def test_no_selectors_is_inconclusive(self):
        for row in ({'id': 'X-1', 'kind': 'tests', 'selectors': []}, {'id': 'X-3', 'kind': 'tests'}):
            r = status(row)
            self.assertEqual((r['status'], r['executed_cases']), ('INCONCLUSIVE', 0), row)
            self.assertIn('zero executed cases', r['reason'])

    def test_min_zero_with_no_match_is_inconclusive(self):
        r = status({'id': 'X-2', 'kind': 'tests', 'selectors': [{'component': 'alpha', 're': 'never_matches', 'min': 0}]})
        self.assertEqual(r['status'], 'INCONCLUSIVE')

    def test_a_matching_row_still_passes(self):
        self.assertEqual(status({'id': 'X-4', 'kind': 'tests', 'selectors': [{'component': 'alpha', 're': 'test_a'}]})['status'], 'PASS')

    def test_a_real_failure_stays_fail(self):
        idx = {'alpha': [('t', 'test_a', 'failed', {'kind': 'failed', 'unexpected_pass': False})]}
        self.assertEqual(status({'id': 'X-5', 'kind': 'tests', 'selectors': [{'component': 'alpha', 're': 'test_a', 'min': 0}]}, idx)['status'], 'FAIL')


class MalformedRowsAreRefused(unittest.TestCase):
    def bad(self, row):
        with self.assertRaises(ValueError) as cm:
            v.validate_requirements({'requirements': [row]})
        return str(cm.exception)

    def test_rows_without_selectors_or_with_min_below_one_or_without_fields_are_refused(self):
        self.assertIn('X-1', self.bad({'id': 'X-1', 'kind': 'tests', 'selectors': []}))
        self.bad({'id': 'X-2', 'kind': 'tests'})
        self.bad({'id': 'X-3', 'kind': 'tests', 'selectors': [{'component': 'alpha', 're': 'x', 'min': 0}]})
        self.bad({'id': 'X-4', 'kind': 'tests', 'selectors': [{'component': 'alpha', 're': 'x', 'min': True}]})
        self.bad({'id': 'X-5', 'kind': 'tests', 'selectors': [{'component': 'alpha', 're': ''}]})
        self.bad({'id': 'X-6', 'kind': 'tests', 'selectors': [{'re': 'x'}]})
        self.bad({'id': 'X-7', 'kind': 'tests', 'selectors': [{'component': 'alpha', 're': '('}]})

    def test_the_repository_requirements_are_well_formed(self):
        v.validate_requirements(json.loads(REQS.read_text()))

    def test_duplicate_ids_are_refused(self):
        row = selector_row('X-1', 'alpha', 'test_a')
        with self.assertRaises(ValueError):
            v.validate_requirements({'requirements': [row, dict(row)]})

    def test_the_aggregate_refuses_a_malformed_matrix(self):
        with self.assertRaises(SystemExit):
            aggregate([job('alpha')], [{'id': 'X-1', 'kind': 'tests', 'selectors': []}])


if __name__ == '__main__':
    unittest.main()
