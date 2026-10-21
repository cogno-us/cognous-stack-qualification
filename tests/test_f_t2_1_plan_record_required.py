"""F-T2-1: an aggregate without a plan record (or with an empty plan) is INCOMPLETE with a record_binding_problems entry; it used to read
`expected` as [] and could return PASS with 0 expected and 0 missing jobs. The explicit escape --no-plan-record is recorded and caps the verdict.
Hermetic: agg_util removes the CI run variables; nothing here reads GITHUB_RUN_ID."""
import subprocess
import sys
import unittest
from pathlib import Path

from agg_util import aggregate, job, plan_entry

ROOT = Path(__file__).resolve().parents[1]
ROW_JOB = [{'id': 'R-A', 'kind': 'job', 'component': 'alpha', 'mandatory': True}]
SHA = '1' * 40


class PlanRecordRequired(unittest.TestCase):
    def test_control_with_a_plan_the_same_inputs_pass(self):
        s = aggregate([job('alpha')], ROW_JOB, plan=[plan_entry('alpha')])
        self.assertEqual((s['selected_v1_verdict'], s['expected_jobs'], s['record_binding_problems']), ('PASS', 1, []))

    def test_no_plan_record_is_incomplete_with_a_binding_problem(self):
        s = aggregate([job('alpha')], ROW_JOB, plan=None)
        self.assertEqual(s['selected_v1_verdict'], 'INCOMPLETE')
        self.assertEqual([p['job'] for p in s['record_binding_problems']], ['(plan)'])
        self.assertFalse(s['no_plan_record'])
        self.assertIn('plan record', s['verdict_note'])

    def test_an_empty_plan_is_incomplete(self):
        s = aggregate([job('alpha')], ROW_JOB, plan=[])
        self.assertEqual(s['selected_v1_verdict'], 'INCOMPLETE')
        self.assertEqual([p['job'] for p in s['record_binding_problems']], ['(plan)'])

    def test_missing_jobs_stay_detected_with_a_plan(self):
        s = aggregate([job('alpha')], ROW_JOB, plan=[plan_entry('alpha'), plan_entry('beta')])
        self.assertEqual((s['missing_jobs'], s['selected_v1_verdict']), (1, 'INCOMPLETE'))

    def test_job_to_plan_sha_binding_is_not_skipped_by_dropping_the_plan(self):
        # a record at the wrong commit: with the plan the binding fails; without it the verdict is INCOMPLETE too (never PASS)
        wrong = job('alpha', extra={'repository': 'o/alpha', 'pinned_sha': '0' * 40, 'actual_sha': '0' * 40})
        with_plan = aggregate([wrong], ROW_JOB, plan=[plan_entry('alpha', repository='o/alpha', sha=SHA)])
        without = aggregate([wrong], ROW_JOB, plan=None)
        self.assertEqual(with_plan['selected_v1_verdict'], 'INCOMPLETE')
        self.assertTrue(any('sha' in p['problem'] for p in with_plan['record_binding_problems']))
        self.assertEqual(without['selected_v1_verdict'], 'INCOMPLETE')

    def test_without_requirements_the_verdict_was_already_incomplete_and_the_problem_is_recorded(self):
        s = aggregate([job('alpha')], None, plan=None)
        self.assertEqual(s['selected_v1_verdict'], 'INCOMPLETE')
        self.assertTrue(s['record_binding_problems'])

    def test_a_malformed_plan_is_refused(self):
        with self.assertRaises(SystemExit):
            aggregate([job('alpha')], ROW_JOB, plan=['alpha'])


class ExplicitEscape(unittest.TestCase):
    def test_no_plan_record_flag_is_recorded_and_caps_the_verdict_at_incomplete(self):
        s = aggregate([job('alpha')], ROW_JOB, plan=None, no_plan_record=True)
        self.assertTrue(s['no_plan_record'])
        self.assertEqual(s['selected_v1_verdict'], 'INCOMPLETE')
        self.assertEqual(s['record_binding_problems'], [])
        self.assertIn('--no-plan-record', s['verdict_note'])
        self.assertIn('--no-plan-record', s['verdict_basis'])

    def test_the_flag_does_not_lift_a_fail(self):
        s = aggregate([job('alpha', 'FAIL')], ROW_JOB, plan=None, no_plan_record=True)
        self.assertEqual(s['selected_v1_verdict'], 'FAIL')

    def test_the_flag_is_irrelevant_when_a_plan_is_present(self):
        s = aggregate([job('alpha')], ROW_JOB, plan=[plan_entry('alpha')], no_plan_record=True)
        self.assertEqual(s['selected_v1_verdict'], 'PASS')

    def test_the_command_line_offers_the_flag(self):
        out = subprocess.run([sys.executable, str(ROOT / 'tools/v1_validation.py'), 'aggregate', '--help'], capture_output=True, text=True).stdout
        self.assertIn('--no-plan-record', out)


if __name__ == '__main__':
    unittest.main()
