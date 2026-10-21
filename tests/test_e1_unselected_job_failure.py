"""E-1: the V1 verdict must not be PASS while an expected job is FAIL, INCONCLUSIVE or missing and no declared known limit covers it.

The requirement rows only look at the cases their selectors match; a failing case of a pinned component's own suite that no selector
matches used to leave the verdict PASS even though the job status was FAIL.
"""
import unittest

from agg_util import VID, aggregate, job, plan_entry, selector_row

ROW = [selector_row('R-1', 'alpha', 'test_selected')]
OK = [('t', 'test_selected', 'passed'), ('t', 'test_other', 'passed')]
BAD = [('t', 'test_selected', 'passed'), ('t', 'test_other', 'failed')]


class JobVerdictGate(unittest.TestCase):
    def test_baseline_all_pass_is_pass(self):
        s = aggregate([job('alpha', 'PASS', OK)], ROW, plan=[plan_entry('alpha')])
        self.assertEqual(s['selected_v1_verdict'], 'PASS')

    def test_undeclared_failure_that_no_selector_matches_is_fail_and_names_the_job(self):
        s = aggregate([job('alpha', 'FAIL', BAD)], ROW, plan=[plan_entry('alpha')])
        self.assertEqual(s['requirement_status_counts']['PASS'], 1)  # the row itself still passes: this is the gap
        self.assertEqual(s['selected_v1_verdict'], 'FAIL')
        self.assertIn('alpha', s['verdict_note'])
        self.assertIn('test_other', s['verdict_note'])

    def test_failure_declared_as_known_limit_does_not_block(self):
        odes = [('tests.test_restriction_semantics', 'test_explicit_export_end_to_end', 'failed'), ('tests.test_x', 'test_selected', 'passed')]
        s = aggregate([job('odes', 'FAIL', odes)], [selector_row('R-1', 'odes', 'test_selected')],
                      freeze={'status': 'PASS', 'validation_id': VID, 'components': {'odes': {}}, 'components_expected': ['odes']}, plan=[plan_entry('odes')])
        self.assertEqual(s['selected_v1_verdict'], 'PASS')

    def test_declared_failure_plus_an_undeclared_one_blocks(self):
        odes = [('tests.test_restriction_semantics', 'test_explicit_export_end_to_end', 'failed'), ('tests.test_x', 'test_selected', 'passed'),
                ('tests.test_x', 'test_new_defect', 'failed')]
        s = aggregate([job('odes', 'FAIL', odes)], [selector_row('R-1', 'odes', 'test_selected')],
                      freeze={'status': 'PASS', 'validation_id': VID, 'components': {'odes': {}}, 'components_expected': ['odes']}, plan=[plan_entry('odes')])
        self.assertEqual(s['selected_v1_verdict'], 'FAIL')

    def test_failed_job_without_any_failing_case_in_its_junit_blocks(self):
        s = aggregate([job('alpha', 'FAIL', OK)], ROW, plan=[plan_entry('alpha')])
        self.assertEqual(s['selected_v1_verdict'], 'FAIL')

    def test_missing_expected_job_is_incomplete(self):
        s = aggregate([job('alpha', 'PASS', OK)], ROW, plan=[plan_entry('alpha'), plan_entry('alpha', python='3.11')])
        self.assertEqual(s['selected_v1_verdict'], 'INCOMPLETE')
        self.assertIn('alpha', s['verdict_note'])

    def test_inconclusive_job_is_incomplete(self):
        s = aggregate([job('alpha', 'PASS', OK), job('alpha', 'INCONCLUSIVE', (), python='3.11', dirname='v1v-comp-alpha-311')], ROW,
                      plan=[plan_entry('alpha'), plan_entry('alpha', python='3.11')])
        self.assertEqual(s['selected_v1_verdict'], 'INCOMPLETE')

    def test_not_run_blocks_unless_the_component_is_optional(self):
        base = [job('alpha', 'PASS', OK)]
        s = aggregate(base + [job('beta', 'NOT RUN')], ROW, plan=[plan_entry('alpha'), plan_entry('beta')],
                      freeze={'status': 'PASS', 'validation_id': VID, 'components': {'alpha': {}, 'beta': {}}, 'components_expected': ['alpha', 'beta']})
        self.assertEqual(s['selected_v1_verdict'], 'INCOMPLETE')
        s = aggregate(base + [job('beta', 'NOT RUN')], ROW, plan=[plan_entry('alpha'), plan_entry('beta', group='components_optional')],
                      freeze={'status': 'PASS', 'validation_id': VID, 'components': {'alpha': {}, 'beta': {}}, 'components_expected': ['alpha', 'beta']})
        self.assertEqual(s['selected_v1_verdict'], 'PASS')

    def test_a_job_behind_a_non_mandatory_job_row_does_not_block(self):
        rows = ROW + [{'id': 'SC-TOOLING', 'kind': 'job', 'component': 'qual-tooling', 'mandatory': False}]
        s = aggregate([job('alpha', 'PASS', OK), job('qual-tooling', 'FAIL', BAD, dirname='v1v-qual-tooling')], rows, plan=[plan_entry('alpha')])
        self.assertEqual(s['selected_v1_verdict'], 'PASS')

    def test_a_failed_job_row_for_a_mandatory_job_row_is_still_fail(self):
        rows = ROW + [{'id': 'SC-HUB-TESTS', 'kind': 'job', 'component': 'hub-tests', 'mandatory': True}]
        s = aggregate([job('alpha', 'PASS', OK), job('hub-tests', 'FAIL', BAD, dirname='v1v-hub-tests')], rows, plan=[plan_entry('alpha')])
        self.assertEqual(s['selected_v1_verdict'], 'FAIL')

    def test_summary_lists_the_blocking_jobs(self):
        s = aggregate([job('alpha', 'FAIL', BAD)], ROW, plan=[plan_entry('alpha')])
        self.assertEqual([b['component'] for b in s['blocking_jobs']], ['alpha'])


if __name__ == '__main__':
    unittest.main()
