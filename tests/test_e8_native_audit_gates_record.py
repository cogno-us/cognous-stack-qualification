"""E-8: the native-f5b job record must be FAIL when the audit step (tools/summarize_security_runtime.py) or the repetition step fails;
it used to be built from JUnit counts only. The record script is extracted from the workflow and run here; the aggregate row follows it."""
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from agg_util import aggregate, job

ROOT = Path(__file__).resolve().parents[1]
TEXT = (ROOT / '.github/workflows/v1-validation.yml').read_text()


def record_script():
    job_text = TEXT[TEXT.index('\n  native-f5b:'):TEXT.index('\n  harness-and-hub-tests:')]
    step = job_text[job_text.index('- name: Collect result record'):]
    m = re.search(r"python - <<'EOF'\n(.*?)\n\s*EOF\n", step, re.S)
    return textwrap.dedent(m.group(1))


def junit(n, failed=0, skipped=0):
    cases = ''.join('<testcase classname="c" name="t%d"/>' % i for i in range(n))
    cases += ''.join('<testcase classname="c" name="f%d"><failure message="x"/></testcase>' % i for i in range(failed))
    cases += ''.join('<testcase classname="c" name="s%d"><skipped/></testcase>' % i for i in range(skipped))
    return f'<testsuites><testsuite>{cases}</testsuite></testsuites>'


def run_record(audit='success', repeat='success', failed=0, skipped=0, n=3):
    with tempfile.TemporaryDirectory() as td:
        for r in ('run-1', 'run-2'):
            d = Path(td, 'out/native', r)
            d.mkdir(parents=True)
            (d / 'junit.xml').write_text(junit(n, failed, skipped))
        env = dict(os.environ, GITHUB_RUN_ID='7')
        for k, val in (('AUDIT_OUTCOME', audit), ('REPEAT_OUTCOME', repeat)):
            if val is not None:
                env[k] = val
            else:
                env.pop(k, None)
        subprocess.run([sys.executable, '-c', record_script()], cwd=td, env=env, check=True, capture_output=True)
        return json.loads(Path(td, 'out/result.json').read_text())


class NativeRecord(unittest.TestCase):
    def test_clean_run_with_a_successful_audit_is_pass(self):
        rec = run_record()
        self.assertEqual((rec['status'], rec['audit_outcome']), ('PASS', 'success'))

    def test_a_failed_audit_makes_the_record_fail_even_with_clean_junit(self):
        rec = run_record(audit='failure')
        self.assertEqual(rec['status'], 'FAIL')
        self.assertEqual(rec['attempts'][0]['outcome'], 'FAIL')
        self.assertIn('audit', rec['reason'])

    def test_a_skipped_or_missing_audit_is_not_pass(self):
        self.assertEqual(run_record(audit='skipped')['status'], 'FAIL')
        self.assertEqual(run_record(audit=None)['status'], 'FAIL')

    def test_a_failed_repetition_step_is_fail(self):
        self.assertEqual(run_record(repeat='failure')['status'], 'FAIL')

    def test_junit_failures_and_skips_still_fail(self):
        self.assertEqual(run_record(failed=1)['status'], 'FAIL')
        self.assertEqual(run_record(skipped=1)['status'], 'FAIL')
        self.assertEqual(run_record(n=0)['status'], 'FAIL')

    def test_the_workflow_wires_the_step_outcomes_into_the_record_step(self):
        job_text = TEXT[TEXT.index('\n  native-f5b:'):TEXT.index('\n  harness-and-hub-tests:')]
        self.assertRegex(job_text, r'(?s)id: audit\n.*AUDIT_OUTCOME: \$\{\{ steps\.audit\.outcome \}\}')
        self.assertIn('REPEAT_OUTCOME: ${{ steps.repeat.outcome }}', job_text)


class AggregateRow(unittest.TestCase):
    ROWS = [{'id': 'SC-NATIVE-F5B', 'kind': 'job', 'component': 'native-f5b-suite', 'mandatory': True}]

    def agg(self, extra):
        return aggregate([job('native-f5b-suite', 'PASS', dirname='v1v-native-f5b', extra=extra)], self.ROWS)

    def test_a_pass_record_with_a_successful_audit_is_pass(self):
        self.assertEqual(self.agg({'audit_outcome': 'success'})['selected_v1_verdict'], 'PASS')

    def test_a_pass_record_without_a_successful_audit_is_not_pass(self):
        for extra in ({}, {'audit_outcome': 'failure'}, {'audit_outcome': 'skipped'}):
            s = self.agg(extra)
            self.assertEqual(s['requirement_status_counts']['PASS'], 0, extra)
            self.assertNotEqual(s['selected_v1_verdict'], 'PASS', extra)


if __name__ == '__main__':
    unittest.main()
