"""E-11: the aggregate binds job and freeze records to the plan and the run: validation_id, workflow_run and pinned/actual sha."""
import unittest

from agg_util import GOOD_FREEZE, VID, aggregate, job, plan_entry, selector_row

ROW = [selector_row('R-1', 'alpha', 'test_selected')]
OK = [('t', 'test_selected', 'passed')]
SHA = '1' * 40
PLAN = [plan_entry('alpha', repository='o/alpha', sha=SHA)]


def comp(**extra):
    base = {'workflow_run': '5', 'repository': 'o/alpha', 'pinned_sha': SHA, 'actual_sha': SHA}
    base.update(extra)
    return job('alpha', 'PASS', OK, extra=base)


def freeze(**kw):
    return dict(dict(GOOD_FREEZE, workflow_run='5', components={'alpha': {'commit': SHA}}), **kw)


def run(jobs=None, fz=None):
    return aggregate(jobs or [comp()], ROW, freeze=fz or freeze(), plan=PLAN)


class Binding(unittest.TestCase):
    def test_consistent_records_pass(self):
        s = run()
        self.assertEqual(s['selected_v1_verdict'], 'PASS')
        self.assertEqual(s['record_binding_problems'], [])

    def test_a_freeze_record_for_another_validation_id_is_a_freeze_problem(self):
        s = run(fz=freeze(validation_id='v1-1999-01-01-x'))
        self.assertEqual(s['freeze_status'], 'FAIL')
        self.assertEqual(s['selected_v1_verdict'], 'INCOMPLETE')
        self.assertIn(VID, s['verdict_note'])

    def test_a_freeze_record_without_validation_id_is_a_freeze_problem(self):
        fz = freeze()
        del fz['validation_id']
        self.assertEqual(run(fz=fz)['freeze_status'], 'FAIL')

    def test_a_job_record_of_another_workflow_run_is_not_accepted(self):
        s = run([comp(workflow_run='1')])
        self.assertEqual(s['selected_v1_verdict'], 'INCOMPLETE')
        self.assertIn('workflow_run', s['verdict_note'])

    def test_a_job_record_without_a_workflow_run_is_not_accepted_when_the_run_is_known(self):
        r = comp()
        del r['result']['workflow_run']
        self.assertEqual(run([r])['selected_v1_verdict'], 'INCOMPLETE')

    def test_a_job_record_at_another_sha_than_the_plan_is_not_accepted(self):
        for extra in ({'pinned_sha': '0' * 40}, {'actual_sha': '0' * 40}, {'pinned_sha': '0' * 40, 'actual_sha': '0' * 40}, {'repository': 'o/other'}):
            s = run([comp(**extra)])
            self.assertEqual(s['selected_v1_verdict'], 'INCOMPLETE', extra)
            self.assertTrue(s['record_binding_problems'], extra)

    def test_a_job_record_that_differs_from_the_commit_the_freeze_fetched_is_not_accepted(self):
        s = run(fz=freeze(components={'alpha': {'commit': '9' * 40}}))
        self.assertEqual(s['selected_v1_verdict'], 'INCOMPLETE')

    def test_the_aggregate_run_id_from_the_environment_wins(self):
        s = aggregate([comp()], ROW, freeze=freeze(), plan=PLAN, env={'GITHUB_RUN_ID': '77'})
        self.assertEqual(s['selected_v1_verdict'], 'INCOMPLETE')  # records say run 5


if __name__ == '__main__':
    unittest.main()
