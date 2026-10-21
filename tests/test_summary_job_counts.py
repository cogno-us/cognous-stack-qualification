"""Unit tests for the per-job test counts in the validation summary (synthetic JUnit and job records only).

Counts reporting only: no status, row or verdict is derived from these values.
"""
import argparse
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import v1_validation as v  # noqa: E402

JUNIT = ('<?xml version="1.0" encoding="utf-8"?><testsuites><testsuite name="pytest">'
         '<testcase classname="s.a" name="t_pass"/>'
         '<testcase classname="s.a" name="t_fail"><failure message="x"/></testcase>'
         '<testcase classname="s.a" name="t_err"><error message="x"/></testcase>'
         '<testcase classname="s.a" name="t_skip"><skipped/></testcase>'
         '</testsuite></testsuites>')
EXPECTED = {'testcases': 4, 'failures': 1, 'errors': 1, 'skipped': 1}


def summarise(jobs):
    """jobs: {artifact dir: (result record, junit file name or None)}; returns {job dir: counts} from the written summary."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        inp = td / 'in'
        (inp / 'v1v-freeze').mkdir(parents=True)
        (inp / 'v1v-freeze' / 'freeze-verification.json').write_text(json.dumps({'status': 'PASS', 'validation_id': 'v1-2026-10-16-t', 'components': {'x': {}}, 'components_expected': ['x']}))
        for name, (record, junit_name) in jobs.items():
            (inp / name).mkdir()
            (inp / name / 'result.json').write_text(json.dumps(record))
            if junit_name:
                (inp / name / junit_name).write_text(JUNIT)
        out = td / 'out'
        ns = argparse.Namespace(inputs=str(inp), out=str(out), validation_id='v1-2026-10-16-t', requirements=None,
                                declared_twin=None, declared_set=None, require_committed_twin=False)
        with contextlib.redirect_stdout(io.StringIO()):
            v.cmd_aggregate(ns)
        summary = json.loads((out / 'summary.json').read_text())
        md = (out / 'summary.md').read_text()
        return {j['job']: j['counts'] for j in summary['jobs']}, md


def record(component, **extra):
    return {'schema': 'cognous.v1-validation-job/1', 'component': component, 'status': 'FAIL', 'os': 'ubuntu-latest', 'python': '3.12', **extra}


class SummaryJobCounts(unittest.TestCase):
    def test_single_instance_job_counts_come_from_its_record(self):
        counts, md = summarise({'v1v-scenarios': (record('scenarios', kind='scenario-suite', counts=EXPECTED), 'junit.xml')})
        self.assertEqual(counts['v1v-scenarios'], EXPECTED)
        self.assertIn('| FAIL | 4/1/1/1 |', md)

    def test_counts_come_from_the_job_junit_when_the_record_has_none(self):
        counts, _ = summarise({'v1v-scenarios': (record('scenarios'), 'junit.xml')})
        self.assertEqual(counts['v1v-scenarios'], EXPECTED)

    def test_no_counts_anywhere_stays_null(self):
        counts, _ = summarise({'v1v-scenarios': (record('scenarios'), None)})
        self.assertIsNone(counts['v1v-scenarios'])

    def test_attempt_counts_are_unchanged_and_take_precedence(self):
        attempt = {'testcases': 9, 'failures': 0, 'errors': 0, 'skipped': 2}
        counts, _ = summarise({'v1v-comp-odes': (record('odes', attempts=[{'outcome': 'PASS', 'counts': attempt}]), 'junit-attempt1.xml')})
        self.assertEqual(counts['v1v-comp-odes'], attempt)


if __name__ == '__main__':
    unittest.main()
