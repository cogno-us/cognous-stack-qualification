"""E-7: a failed pinned-sibling install must stay visible (setup_ok was overwritten by the pyproject install result).
E-7b: a first attempt that failed and a retry that passed must be reported by the job row and the aggregate, not look like a clean PASS."""
import argparse
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agg_util import aggregate, job, plan_entry, selector_row, v


def make_repo(td):
    repo = Path(td) / 'c'
    repo.mkdir()
    (repo / 'pyproject.toml').write_text("[project]\nname='x'\nversion='0'\n")
    (repo / 'test_a.py').write_text('def test_a(): pass\n')
    for c in (['init', '-q'], ['add', '-A'], ['-c', 'user.name=a', '-c', 'user.email=a@a', 'commit', '-qm', 'x']):
        subprocess.run(['git', '-C', str(repo), *c], check=True, capture_output=True)
    return repo, subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()


def run_suite(sibling_ok=True, attempts_fail=(True, False), component='moltbot_safe'):
    """attempts_fail[i]: attempt i+1 has a failing test case. The sibling install fails (rc 1) unless sibling_ok."""
    with tempfile.TemporaryDirectory() as td:
        repo, sha = make_repo(td)
        sib = {'component': 'control_plane', 'repository': 'o/cp', 'pinned_sha': '1' * 40, 'actual_sha': '1' * 40, 'dir': str(Path(td) / 'sib'), 'targets': ['.']}
        state = {'pytest': 0}

        def fake_run(cmd, cwd, timeout, log):
            s = ' '.join(map(str, cmd))
            if '--junitxml' in s:
                bad = attempts_fail[min(state['pytest'], len(attempts_fail) - 1)]
                state['pytest'] += 1
                j = [a for a in cmd if str(a).startswith('--junitxml=')][0].split('=', 1)[1]
                Path(j).write_text('<testsuite><testcase classname="t" name="a">' + ('<failure message="x"/>' if bad else '') + '</testcase></testsuite>')
                return (1 if bad else 0), '', 0.1, False
            if 'pip' in s and str(Path(td) / 'sib') in s:
                return (0 if sibling_ok else 1), '', 0, False
            return 0, '', 0, False
        args = argparse.Namespace(repo_dir=str(repo), fetch=False, repository='o/c', sha=sha, out=str(Path(td) / 'out'), component=component,
                                  os_name='ubuntu-latest', timeout=60, pins_manifest=None, refreeze_log=None, no_siblings=False)
        with mock.patch.object(v, 'provision_siblings', lambda *a, **k: [sib]), mock.patch.object(v, 'run', fake_run), \
                mock.patch.object(v, '_resolve_pin_file', lambda *a: None), contextlib.redirect_stdout(io.StringIO()):
            try:
                v.cmd_component_suite(args)
            except SystemExit:
                pass
        return json.loads((Path(td) / 'out/result.json').read_text())


class SiblingSetupVisible(unittest.TestCase):
    def test_a_failed_sibling_install_is_not_hidden_by_a_successful_project_install(self):
        r = run_suite(sibling_ok=False, attempts_fail=(False,))
        self.assertFalse(r['attempts'][0]['setup_ok'])
        self.assertFalse(r['attempts'][0]['sibling_install_ok'])
        self.assertEqual(len(r['attempts']), 2)  # a setup failure is retried once

    def test_a_good_sibling_install_keeps_setup_ok(self):
        r = run_suite(sibling_ok=True, attempts_fail=(False,))
        self.assertTrue(r['attempts'][0]['setup_ok'])
        self.assertEqual(len(r['attempts']), 1)


class RetryIsReported(unittest.TestCase):
    def test_first_attempt_fail_then_retry_pass_is_flagged_with_the_first_outcome(self):
        r = run_suite(sibling_ok=False, attempts_fail=(True, False))
        self.assertEqual(r['status'], 'PASS')
        self.assertTrue(r['flaky_or_setup'])
        self.assertEqual(r['attempt_outcomes'], ['FAIL', 'PASS'])

    def test_a_clean_first_attempt_is_not_flagged(self):
        r = run_suite(sibling_ok=True, attempts_fail=(False,))
        self.assertFalse(r.get('flaky_or_setup', False))

    def test_the_aggregate_reports_a_retried_pass_in_the_row_the_summary_and_the_markdown(self):
        ROW = [selector_row('R-1', 'alpha', 'test_selected')]
        cases = [('t', 'test_selected', 'passed')]
        extra = {'flaky_or_setup': True, 'attempt_outcomes': ['FAIL', 'PASS'], 'attempts': [{'outcome': 'FAIL'}, {'outcome': 'PASS'}]}
        s = aggregate([job('alpha', 'PASS', cases, extra=extra)], ROW, plan=[plan_entry('alpha')])
        self.assertEqual(s['selected_v1_verdict'], 'PASS')  # decision: reported, not blocking
        self.assertTrue(s['jobs'][0]['flaky_or_setup'])
        self.assertEqual(s['jobs'][0]['attempt_outcomes'], ['FAIL', 'PASS'])
        self.assertEqual([j['component'] for j in s['flaky_or_setup_jobs']], ['alpha'])


if __name__ == '__main__':
    unittest.main()
