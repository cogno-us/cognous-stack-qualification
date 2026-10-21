"""E1: freeze-verify must fetch and record every pinned component, and the aggregate must refuse a freeze record without them."""
import argparse
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import v1_validation as v  # noqa: E402

HEAD, TAG, SHA_A, SHA_B, SHA_C = 'a' * 40, 'b' * 40, '1' * 40, '2' * 40, '3' * 40
MANIFEST = {
    'validation_id': 'v1-2026-10-16-t',
    'identities': {'hub': {'repository': 'o/hub', 'head': HEAD, 'tag_commit': TAG, 'public_reference_tag': 't', 'head_minus_tag_files': ['x']},
                   'qualification': {'repository': 'o/q', 'closeout': HEAD, 'tag_commit': HEAD, 'public_reference_tag': 't'},
                   'runtime': {'repository': 'o/rt', 'public_reference_tag': 't', 'sha': HEAD, 'quarantine_tag': 'q'}},
    'hub_file_hashes': {}, 'qualification_file_hashes': {},
    'profile': {'path': 'profile.json', 'qualification_profile': 'qprofile.json'},
    'components_subject': {'alpha': {'repository': 'o/alpha', 'sha': SHA_A}, 'beta': {'repository': 'o/beta', 'sha': SHA_B}},
    'components_lock_remainder': {}, 'components_optional': {'gamma': {'repository': 'o/gamma', 'sha': SHA_C}},
}


FULL_PROFILE = {'components': {k: {'repository': spec['repository'], 'revision': spec['sha']} for k, spec in MANIFEST['components_subject'].items()}}


def run_freeze(td, fetch, profile=FULL_PROFILE, qprofile=FULL_PROFILE):
    td = Path(td)
    (td / 'hub').mkdir(); (td / 'q').mkdir()
    (td / 'manifest.json').write_text(json.dumps(MANIFEST))
    (td / 'hub' / 'profile.json').write_text(json.dumps(profile))
    (td / 'hub' / 'component-lock.json').write_text(json.dumps({'components': {'gamma': {'sha': SHA_C}}}))
    (td / 'q' / 'qprofile.json').write_text(json.dumps(qprofile))

    def fake_git(path, *a, **k):
        return {'diff': 'x', 'merge-base': ''}.get(a[0], HEAD if a[:2] == ('rev-parse', 'HEAD') else 'tree')

    args = argparse.Namespace(manifest=str(td / 'manifest.json'), refreeze_log=None, hub_dir=str(td / 'hub'), qual_dir=str(td / 'q'),
                              work=str(td / 'work'), out=str(td / 'out' / 'f.json'), qual_profile=None)
    with mock.patch.object(v, 'git', fake_git), mock.patch.object(v, 'ls_remote_tag', lambda r, t: TAG if r == 'o/hub' else HEAD), \
            mock.patch.object(v, 'fetch_exact', fetch), mock.patch.object(v.platform, 'platform', lambda: 'test'), mock.patch.object(v.subprocess, 'run', lambda *a, **k: mock.Mock(returncode=0)), \
            contextlib.redirect_stdout(io.StringIO()):
        try:
            v.cmd_freeze_verify(args)
        except SystemExit:
            pass
    return json.loads((td / 'out' / 'f.json').read_text())


class FreezeVerifyFetchesComponents(unittest.TestCase):
    def test_every_pinned_component_is_fetched_recorded_and_checked(self):
        calls = []

        def fetch(d, repo, sha):
            calls.append((repo, sha)); return sha
        with tempfile.TemporaryDirectory() as td:
            rec = run_freeze(td, fetch)
        self.assertEqual(sorted(calls), [('o/alpha', SHA_A), ('o/beta', SHA_B), ('o/gamma', SHA_C)])
        self.assertEqual(sorted(rec['components']), ['alpha', 'beta', 'gamma'])
        self.assertEqual(rec['components_expected'], ['alpha', 'beta', 'gamma'])
        names = [c['check'] for c in rec['checks'] if c['check'].endswith('resolves to pinned commit')]
        self.assertEqual(sorted(names), [f'component {k} resolves to pinned commit' for k in ('alpha', 'beta', 'gamma')])
        self.assertEqual([c['check'] for c in rec['checks'] if c['status'] != 'PASS'], [])
        self.assertEqual(rec['status'], 'PASS')

    def test_an_empty_or_incomplete_profile_fails_the_record(self):
        # E-3: the profile checks used to run profile -> manifest only, so these passed with zero checks
        partial = {'components': {'alpha': FULL_PROFILE['components']['alpha']}}
        for kw in ({'profile': {'components': {}}}, {'qprofile': {'components': {}}}, {'profile': partial}, {'qprofile': partial}):
            with tempfile.TemporaryDirectory() as td:
                rec = run_freeze(td, lambda d, repo, sha: sha, **kw)
            self.assertEqual(rec['status'], 'FAIL', kw)

    def test_a_component_that_resolves_to_another_commit_fails_the_record(self):
        with tempfile.TemporaryDirectory() as td:
            rec = run_freeze(td, lambda d, repo, sha: 'f' * 40 if repo == 'o/beta' else sha)
        self.assertEqual(rec['status'], 'FAIL')


def aggregate(freeze, plan_components=()):
    with tempfile.TemporaryDirectory() as td:
        td = Path(td); inp = td / 'in'
        (inp / 'v1v-freeze').mkdir(parents=True); (inp / 'v1v-plan').mkdir()
        (inp / 'v1v-freeze' / 'freeze-verification.json').write_text(json.dumps(freeze))
        (inp / 'v1v-plan' / 'plan.json').write_text(json.dumps({'include': [{'component': c, 'os': 'ubuntu-latest', 'python': '3.12'} for c in plan_components]}))
        ns = argparse.Namespace(inputs=str(inp), out=str(td / 'out'), validation_id='v1-2026-10-16-t', requirements=None,
                                declared_twin=None, declared_set=None, require_committed_twin=False)
        with contextlib.redirect_stdout(io.StringIO()):
            v.cmd_aggregate(ns)
        return json.loads((td / 'out' / 'summary.json').read_text())


class AggregateRefusesEmptyFreeze(unittest.TestCase):
    def test_zero_components_with_expected_set_is_not_pass(self):
        s = aggregate({'status': 'PASS', 'components': {}, 'components_expected': ['alpha']}, ['alpha'])
        self.assertNotEqual(s['freeze_status'], 'PASS')
        self.assertEqual(s['selected_v1_verdict'], 'INCOMPLETE')

    def test_empty_expected_set_is_not_pass(self):
        self.assertNotEqual(aggregate({'status': 'PASS', 'components': {}, 'components_expected': []})['freeze_status'], 'PASS')

    def test_components_differing_from_the_plan_are_not_pass(self):
        rec = {'status': 'PASS', 'components': {'alpha': {}}, 'components_expected': ['alpha']}
        self.assertNotEqual(aggregate(rec, ['alpha', 'beta'])['freeze_status'], 'PASS')

    def test_complete_record_passes(self):
        rec = {'status': 'PASS', 'components': {'alpha': {}}, 'components_expected': ['alpha']}
        s = aggregate(rec, ['alpha'])
        self.assertEqual((s['freeze_status'], s['freeze_components_proof']), ('PASS', 'verified'))

    def test_legacy_record_is_flagged_not_proof_and_not_pass(self):
        # E-2: this test used to expect freeze_status PASS for a record without components_expected (it encoded the bug)
        s = aggregate({'status': 'PASS', 'components': {}})
        self.assertEqual(s['freeze_status'], 'FAIL')
        self.assertIn('not proof', s['freeze_components_proof'])


if __name__ == '__main__':
    unittest.main()
