"""Unit tests for the component-job harness corrections: the default per-component timeout and the provisioning of pinned siblings.

Nothing is fetched or installed: the fetch function is replaced and the freeze manifest is the committed one.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import v1_validation as v  # noqa: E402

VAL = ROOT / 'process/v1-validation/v1-2026-10-16-a'
MANIFEST = VAL / 'freeze-manifest.json'
LOG = VAL / 'refreeze-log.json'


def pins_in_force():
    manifest, _ = v.load_resolved(MANIFEST, LOG)
    return {k: (s['repository'], s['sha']) for _, k, s in v.all_components(manifest)}


class Timeout(unittest.TestCase):
    def test_default_is_900_and_covers_the_slowest_measured_suites(self):
        self.assertEqual(v.DEFAULT_TEST_TIMEOUT_SECONDS, 900)
        self.assertGreaterEqual(v.DEFAULT_TEST_TIMEOUT_SECONDS, 5 * 167)  # gax_imx_transport, the slowest measured suite

    def test_plan_emits_the_default_for_every_component_without_its_own_value(self):
        p = subprocess.run([sys.executable, str(ROOT / 'tools/v1_validation.py'), 'plan', '--manifest', str(MANIFEST), '--refreeze-log', str(LOG), '--linux-only'],
                           capture_output=True, text=True, check=True)
        include = json.loads(p.stdout)['include']
        self.assertTrue(include)
        self.assertEqual({row['timeout'] for row in include}, {900})

    def test_a_manifest_value_still_wins(self):
        doc = json.loads(MANIFEST.read_text())
        doc['components_subject']['odes']['test_timeout_seconds'] = 1234
        with tempfile.TemporaryDirectory() as td:
            m = Path(td) / 'm.json'
            m.write_text(json.dumps(doc))
            out = Path(td) / 'plan.json'
            subprocess.run([sys.executable, str(ROOT / 'tools/v1_validation.py'), 'plan', '--manifest', str(m), '--linux-only', '--out-file', str(out)], capture_output=True, text=True, check=True)
            by = {r['component']: r['timeout'] for r in json.loads(out.read_text())['include']}
        self.assertEqual((by['odes'], by['bitrep']), (1234, 900))

    def test_component_suite_default_argument_is_the_constant(self):
        src = (ROOT / 'tools/v1_validation.py').read_text()
        self.assertIn('p.add_argument("--timeout", type=int, default=DEFAULT_TEST_TIMEOUT_SECONDS)\n    p.add_argument("--fetch"', src)


class Siblings(unittest.TestCase):
    def fetch(self, calls):
        def f(dest, repository, sha):
            calls.append((Path(dest).name, repository, sha))
            return sha
        return f

    def test_runtime_gets_the_pinned_control_plane_and_odes_the_pinned_replay(self):
        pins = pins_in_force()
        for component, sibling in (('moltbot_safe', 'control_plane'), ('odes', 'replay_bundle')):
            calls = []
            recs = v.provision_siblings(component, '/nonexistent/sib', MANIFEST, LOG, fetch=self.fetch(calls))
            self.assertEqual([r['component'] for r in recs], [sibling])
            self.assertEqual(calls, [(sibling, *pins[sibling])])
            self.assertEqual(recs[0]['pinned_sha'], recs[0]['actual_sha'])

    def test_the_pin_in_force_is_the_overlaid_pin_not_the_frozen_one(self):
        frozen = json.loads(MANIFEST.read_text())['components_subject']['replay_bundle']['sha']
        calls = []
        v.provision_siblings('odes', '/x', MANIFEST, LOG, fetch=self.fetch(calls))
        self.assertNotEqual(calls[0][2], frozen)
        self.assertEqual(calls[0][2], pins_in_force()['replay_bundle'][1])

    def test_other_components_get_no_siblings(self):
        calls = []
        for comp in ('bitrep', 'control_plane', 'replay_bundle', 'governance_evidence_pack', 'gax_imx_transport'):
            self.assertEqual(v.provision_siblings(comp, '/x', MANIFEST, LOG, fetch=self.fetch(calls)), [])
        self.assertEqual(calls, [])

    def test_a_sibling_that_resolves_to_another_commit_is_an_error(self):
        with self.assertRaises(RuntimeError):
            v.provision_siblings('odes', '/x', MANIFEST, LOG, fetch=lambda d, r, s: '0' * 40)

    def test_missing_manifest_is_an_error_not_a_silent_skip(self):
        with self.assertRaises(RuntimeError):
            v.provision_siblings('odes', '/x', None, None, fetch=self.fetch([]))

    def test_every_provisioned_sibling_exists_in_the_manifest(self):
        pins = pins_in_force()
        for comp, wanted in v.SIBLING_PROVISIONING.items():
            self.assertIn(comp, pins)
            for key, targets in wanted:
                self.assertIn(key, pins)
                self.assertTrue(targets)

    def test_pin_file_resolution_uses_the_workflow_variables_and_refuses_a_missing_file(self):
        with mock.patch.dict(os.environ, {'MANIFEST': 'process/v1-validation/v1-2026-10-16-a/freeze-manifest.json'}):
            self.assertEqual(v._resolve_pin_file(None, 'MANIFEST'), MANIFEST)
        with mock.patch.dict(os.environ, {'REFREEZE_LOG': 'process/v1-validation/none/refreeze-log.json'}):
            with self.assertRaises(RuntimeError):
                v._resolve_pin_file(None, 'REFREEZE_LOG')
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('REFREEZE_LOG', None)
            self.assertIsNone(v._resolve_pin_file(None, 'REFREEZE_LOG'))

    def test_a_failed_sibling_provisioning_is_a_setup_defect_result_and_runs_no_tests(self):
        with tempfile.TemporaryDirectory() as td:
            repo, out = Path(td) / 'c', Path(td) / 'out'
            subprocess.run(['git', 'init', '-q', str(repo)], check=True)
            subprocess.run(['git', '-C', str(repo), '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', 'commit', '-q', '--allow-empty', '-m', 'x'], check=True)
            head = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True).stdout.strip()
            ns = argparse.Namespace(repo_dir=str(repo), fetch=False, out=str(out), component='odes', repository='x/y', sha=head, os_name='ubuntu-latest',
                                    timeout=1, pins_manifest=str(Path(td) / 'missing.json'), refreeze_log=None, no_siblings=False)
            with self.assertRaises(SystemExit) as cm:
                v.cmd_component_suite(ns)
            self.assertEqual(cm.exception.code, 1)
            res = json.loads((out / 'result.json').read_text())
            self.assertEqual((res['status'], res['classification']), ('FAIL', 'setup/harness defect'))
            self.assertIn('sibling provisioning failed', res['reason'])
            self.assertEqual(res['attempts'], [])


if __name__ == '__main__':
    unittest.main()
