"""F-T2-2: the hub-side result records read exit.txt. A pytest session that ended with a non-zero exit that is not a plain "tests failed"
exit (for example a conftest calling pytest.exit(returncode=2)) with a partial JUnit used to be recorded PASS. The record script is
extracted from the workflow and run here (as E-8 does for the native record); the aggregate also refuses PASS for such a record.
Hermetic: GITHUB_RUN_ID is set explicitly for the extracted script only."""
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from agg_util import GOOD_FREEZE, aggregate as _aggregate, job, plan_entry
import v1_validation as v

ROOT = Path(__file__).resolve().parents[1]


def aggregate(jobs, rows, plan):
    """The agg_util aggregate with a freeze record whose component set equals the plan's, so that only the job record decides the verdict."""
    names = [e['component'] for e in plan]
    return _aggregate(jobs, rows, freeze=dict(GOOD_FREEZE, components={n: {} for n in names}, components_expected=names), plan=plan)


TEXT = (ROOT / '.github/workflows/v1-validation.yml').read_text()


def record_script():
    step = TEXT[TEXT.index('      - name: Result records\n'):TEXT.index('      # One artifact per record')]
    return textwrap.dedent(re.search(r"python - <<'EOF'\n(.*?)\n\s*EOF\n", step, re.S).group(1))


def junit(passed=3, failed=0):
    cases = ''.join(f'<testcase classname="c" name="t{i}"/>' for i in range(passed))
    cases += ''.join(f'<testcase classname="c" name="f{i}"><failure message="x"/></testcase>' for i in range(failed))
    return f'<testsuites><testsuite>{cases}</testsuite></testsuites>'


def run_records(exit_txt=None, passed=3, failed=0, with_junit=True, name='hub-tests'):
    with tempfile.TemporaryDirectory() as td:
        for n in ('qual-tooling', 'hub-tests'):
            d = Path(td, 'out', n)
            d.mkdir(parents=True)
            if n == name:
                if with_junit:
                    (d / 'junit.xml').write_text(junit(passed, failed))
                if exit_txt is not None:
                    (d / 'exit.txt').write_text(exit_txt)
            else:
                (d / 'junit.xml').write_text(junit())
        subprocess.run([sys.executable, '-c', record_script()], cwd=td, env=dict(os.environ, GITHUB_RUN_ID='7'), check=True, capture_output=True)
        return json.loads(Path(td, 'out', name, 'result.json').read_text())


class RecordScript(unittest.TestCase):
    def test_the_workflow_still_writes_exit_txt_for_both_pytest_jobs(self):
        for out in ('qual-tooling', 'hub-tests'):
            self.assertRegex(TEXT, r'python -m pytest [^\n]*\|\| echo "pytest exit \$\?" > \.\./out/' + out + r'/exit\.txt')

    def test_clean_session_without_exit_txt_is_pass(self):
        for name in ('hub-tests', 'qual-tooling'):
            rec = run_records(name=name)
            self.assertEqual((rec['status'], rec['pytest_exit']), ('PASS', 0), name)

    def test_aborted_session_with_a_partial_junit_is_not_pass(self):
        for name in ('hub-tests', 'qual-tooling'):
            rec = run_records('pytest exit 2\n', passed=1, name=name)
            self.assertEqual((rec['status'], rec['pytest_exit']), ('INCONCLUSIVE', 2), name)
            self.assertEqual(rec['attempts'][0]['outcome'], 'INCONCLUSIVE')
            self.assertIn('exit 2', rec['reason'])

    def test_every_non_plain_failure_exit_is_not_pass(self):
        for code in (2, 3, 4, 5, 124, 137):
            self.assertNotEqual(run_records(f'pytest exit {code}\n', passed=5)['status'], 'PASS', code)

    def test_exit_one_with_failing_cases_is_fail(self):
        rec = run_records('pytest exit 1\n', passed=2, failed=1)
        self.assertEqual((rec['status'], rec['pytest_exit']), ('FAIL', 1))

    def test_exit_one_without_a_failing_case_is_not_pass(self):
        self.assertEqual(run_records('pytest exit 1\n', passed=4)['status'], 'INCONCLUSIVE')

    def test_aborted_session_with_failing_cases_is_fail(self):
        self.assertEqual(run_records('pytest exit 2\n', passed=1, failed=1)['status'], 'FAIL')

    def test_an_unreadable_exit_file_is_not_pass(self):
        rec = run_records('garbage\n')
        self.assertEqual((rec['status'], rec['pytest_exit']), ('INCONCLUSIVE', -1))

    def test_zero_cases_is_not_pass(self):
        self.assertEqual(run_records(passed=0)['status'], 'INCONCLUSIVE')
        self.assertEqual(run_records(with_junit=False)['status'], 'INCONCLUSIVE')

    def test_the_shell_idiom_of_the_workflow_writes_the_exit_code(self):
        # the workflow line is `<pytest> || echo "pytest exit $?" > exit.txt`; $? there is the pytest exit status
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(['bash', '-c', f'{sys.executable} -c "import sys; sys.exit(2)" || echo "pytest exit $? " > exit.txt'], cwd=td, check=True)
            self.assertEqual(Path(td, 'exit.txt').read_text().strip(), 'pytest exit 2')


ROW = [{'id': 'SC-HUB-TESTS', 'kind': 'job', 'component': 'hub-tests', 'mandatory': True}]


def hub(status='PASS', counts=None, **extra):
    c = counts or {'testcases': 653, 'failures': 0, 'errors': 0, 'skipped': 0}
    r = job('hub-tests', status, extra=dict({'attempts': [{'outcome': status, 'counts': c}]}, **extra))
    return r


class AggregateReadsTheExit(unittest.TestCase):
    PLAN = [plan_entry('hub-tests')]

    def verdict(self, rec, rows=ROW):
        return aggregate([rec], rows, plan=self.PLAN)

    def test_retained_shape_without_the_field_still_passes(self):
        self.assertEqual(self.verdict(hub())['selected_v1_verdict'], 'PASS')

    def test_a_pass_record_with_a_non_zero_pytest_exit_is_not_pass(self):
        s = self.verdict(hub(pytest_exit=2))
        self.assertEqual(s['selected_v1_verdict'], 'INCOMPLETE')
        self.assertTrue(s['blocking_jobs'])

    def test_a_pass_record_with_a_zero_pytest_exit_passes(self):
        self.assertEqual(self.verdict(hub(pytest_exit=0))['selected_v1_verdict'], 'PASS')

    def test_the_effective_status_follows_the_exit(self):
        self.assertEqual(v.effective_job_status({'component': 'qual-tooling', 'status': 'PASS', 'pytest_exit': 5}), 'INCONCLUSIVE')
        self.assertEqual(v.effective_job_status({'component': 'qual-tooling', 'status': 'PASS', 'pytest_exit': 0}), 'PASS')
        self.assertEqual(v.effective_job_status({'component': 'qual-tooling', 'status': 'FAIL', 'pytest_exit': 1}), 'FAIL')


class MinimumCases(unittest.TestCase):
    PLAN = [plan_entry('hub-tests')]

    def test_zero_cases_are_not_pass_for_the_hub_row(self):
        s = aggregate([hub(counts={'testcases': 0, 'failures': 0, 'errors': 0, 'skipped': 0})], ROW, plan=self.PLAN)
        self.assertNotEqual(s['selected_v1_verdict'], 'PASS')

    def test_a_row_minimum_is_enforced_when_the_row_states_one(self):
        row = [dict(ROW[0], min_cases=700)]
        self.assertNotEqual(aggregate([hub()], row, plan=self.PLAN)['selected_v1_verdict'], 'PASS')
        row = [dict(ROW[0], min_cases=653)]
        self.assertEqual(aggregate([hub()], row, plan=self.PLAN)['selected_v1_verdict'], 'PASS')

    def test_the_retained_hub_count_passes_the_default_minimum(self):
        self.assertEqual(aggregate([hub()], ROW, plan=self.PLAN)['selected_v1_verdict'], 'PASS')

    def test_a_malformed_min_cases_is_refused(self):
        for bad in (0, -1, 'x', True, 1.5):
            with self.assertRaises(ValueError, msg=repr(bad)):
                v.validate_requirements({'requirements': [dict(ROW[0], min_cases=bad)]})
        v.validate_requirements({'requirements': [dict(ROW[0], min_cases=3)]})

    def test_the_qualification_tooling_row_needs_a_case_as_well(self):
        row = [{'id': 'SC-TOOLING', 'kind': 'job', 'component': 'qual-tooling', 'mandatory': True}]
        rec = job('qual-tooling', 'PASS', extra={'attempts': [{'outcome': 'PASS', 'counts': {'testcases': 0, 'failures': 0, 'errors': 0, 'skipped': 0}}]})
        s = aggregate([rec], row, plan=[plan_entry('qual-tooling')])
        self.assertNotEqual(s['selected_v1_verdict'], 'PASS')


if __name__ == '__main__':
    unittest.main()
