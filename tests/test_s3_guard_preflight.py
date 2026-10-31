"""Regression tests for the MANDATORY S3 tuple-guard preflight (OCS-254-S3 closeout D5). Non-authorizing; hermetic.

All configuration edits are made on scratch COPIES of the committed profile / freeze-manifest / tuple (never the committed files).
Checkout identity is exercised with scratch directories and a patched `git` helper, so no component checkout is needed; one test
(skipped when the pristine pinned checkouts are absent) runs the guard against the real frozen config and real checkouts.
Every refusal test asserts the SPECIFIC refusal reason (and, where relevant, the check id), not merely 'an error'.

Run:  python -m unittest tests.test_s3_guard_preflight   (also picked up by `python -m unittest discover -s tests`)
"""
import contextlib
import copy
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
for _p in (REPO / 'tools', REPO / 's3'):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import s3_tuple_guard as guard  # noqa: E402
import run_wiki_s3 as runner  # noqa: E402

VID = guard.VALIDATION_ID
TUPLE_REL = f'process/v1-validation/{VID}/runner-tuple.json'
PROFILE_REL = 'process/security-runtime-current-stack-S3-20261031.json'
MAN_REL = f'process/v1-validation/{VID}/freeze-manifest.json'
REAL_COMPONENTS = Path(os.environ.get('S3_COMPONENTS_DIR', '/home/claude/cs-components-s3run'))
NAMES = list(guard.EXPECTED)
# historical P2 generation values (must be refused even when set consistently everywhere)
P2 = {'control_plane': '7a4bcd40b3b49e61ff3c294dcca53b52f460b22c', 'runtime': 'c5e97e87dd239c821b1b4a406a55dcd03c5bc61f',
      'replay': '40012b8c174c6f25685bd5d9bc93ff46cc9a5842', 'evidence_pack': '7b9511f2c6d56d424f17b078826594abd29f6c96',
      'odes': '1a5e1d300250d832e611633f0bf8f762e398c0ec'}
BOGUS = 'deadbeef' * 5


def load(rel):
    return json.loads((REPO / rel).read_text())


class Scratch:
    """A scratch ROOT holding copies of the three config files, a scratch tuple and fake component checkouts."""

    def __init__(self, test):
        self.tmp = Path(tempfile.mkdtemp(prefix='s3guard-'))
        test.addCleanup(__import__('shutil').rmtree, self.tmp, True)
        self.root = self.tmp / 'root'
        self.tuple = load(TUPLE_REL)
        self.profile = load(PROFILE_REL)
        self.man = load(MAN_REL)
        self.comps = self.tmp / 'comps'
        for n in NAMES:
            (self.comps / n).mkdir(parents=True)
        self.heads = {n: guard.EXPECTED[n][0] for n in NAMES}
        self.trees = {n: guard.EXPECTED[n][1] for n in NAMES}
        self.dirty = set()
        self.consts = {c: guard.EXPECTED[k][0] for c, k in guard.EXCHANGE_CONSTANTS.items()}
        self.profile_block = guard.EXCHANGE_PROFILE
        self.write()

    def write(self):
        """(Re)write config copies and the fake Exchange source; the committed files are never touched."""
        for rel, obj in ((TUPLE_REL, self.tuple), (PROFILE_REL, self.profile), (MAN_REL, self.man)):
            f = self.root / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(obj, indent=1))
        src = self.comps / 'exchange' / 'experiments' / 'odex_gax_imx_reference' / 'gax_ref_runtime.py'
        src.parent.mkdir(parents=True, exist_ok=True)
        body = ''.join(f'    {c} = "{v}"\n' for c, v in self.consts.items())
        src.write_text(f'if RUNTIME_COMPATIBILITY_PROFILE == "{self.profile_block}":\n{body}else:\n    pass\n')

    def fake_git(self, path, *args):
        n = Path(path).name
        if args == ('rev-parse', 'HEAD'):
            return self.heads[n]
        if args == ('rev-parse', 'HEAD^{tree}'):
            return self.trees[n]
        if args[0] == 'status':
            return '?? stray.py' if n in self.dirty else ''
        raise AssertionError(args)

    @property
    def tuple_path(self):
        return self.root / TUPLE_REL

    def guard(self):
        self.write()
        with mock.patch.object(guard, 'git', self.fake_git):
            return guard.run_guard(self.tuple_path, self.comps, root=self.root)

    def set_all(self, key, value):
        """Set a component SHA consistently in tuple, profile and freeze-manifest (a 'consistently wrong' configuration)."""
        pk, mk = guard.CFG[key]
        self.tuple[key] = value
        self.profile['components'][pk]['revision'] = value
        self.man['components_subject'][mk]['sha'] = value


class GuardCase(unittest.TestCase):
    def refused(self, res, reason_part, check=None):
        self.assertEqual(res['preflight_guard'], 'refused', res.get('refusal_reason'))
        self.assertIn(reason_part, res['refusal_reason'])
        if check:
            self.assertEqual(res['checks'][-1]['check'], check)
            self.assertEqual(res['checks'][-1]['result'], 'fail')


class TestGuardRefusals(GuardCase):
    def test_unmodified_scratch_copy_of_frozen_config_passes_with_full_record(self):
        s = Scratch(self)
        r = s.guard()
        self.assertEqual(r['preflight_guard'], 'passed', r['refusal_reason'])
        self.assertIsNone(r['refusal_reason'])
        self.assertEqual(r['schema'], guard.RESULT_SCHEMA)
        self.assertEqual(r['guard_file']['sha256'], guard.sha256_file(guard.__file__))
        self.assertEqual(r['tuple_sha256'], guard.sha256_file(s.tuple_path))
        self.assertTrue(r['utc_time'].endswith('+00:00'))
        ids = {c['check'] for c in r['checks']}
        for must in ('tuple_no_placeholder', 'tuple_exchange_profile', 'tuple_pin.replay', 'profile_pin.odes', 'manifest_pin.exchange',
                     'checkout_head.registry', 'checkout_tree.exchange', 'checkout_pristine.manifest', 'exchange_constant.REPLAY_REVISION'):
            self.assertIn(must, ids)
        self.assertTrue(all(c['result'] == 'pass' for c in r['checks']))
        self.assertEqual(r['inputs']['profile_sha256'], guard.sha256_file(s.root / PROFILE_REL))

    def test_wrong_exchange_profile_original_typo_and_p2_even_when_consistent(self):
        for bad in ('security-runtime-current-20261031', 'security-runtime-current-20261031-r3', 'security-runtime-p2-20261018', 'other'):
            with self.subTest(profile=bad):
                s = Scratch(self)
                s.tuple['exchange_compatibility_profile'] = bad
                s.profile['exchange_compatibility_profile'] = bad
                s.man['profile']['exchange_compatibility_profile'] = bad
                s.profile_block = bad
                self.refused(s.guard(), f'wrong Exchange profile in tuple: {bad!r}', 'tuple_exchange_profile')

    def test_wrong_exchange_profile_in_profile_file_or_manifest_only(self):
        s = Scratch(self)
        s.profile['exchange_compatibility_profile'] = 'security-runtime-current-20261031'
        self.refused(s.guard(), 'profile file: wrong Exchange profile', 'profile_exchange_profile')
        s = Scratch(self)
        s.man['profile']['exchange_compatibility_profile'] = 'security-runtime-current-20261031-r3'
        self.refused(s.guard(), 'freeze-manifest: wrong Exchange profile', 'manifest_exchange_profile')

    def test_mixed_generation_consistent_in_tuple_config_profile_and_checkouts(self):
        s = Scratch(self)
        for k, v in P2.items():
            s.set_all(k, v)
            s.heads[k] = v  # the checkouts are at the mixed generation as well
        r = s.guard()
        self.refused(r, 'tuple.control_plane', 'tuple_pin.control_plane')
        self.assertIn('mixed-generation or substituted component', r['refusal_reason'])
        # Replay 40012b8c / ODES 1a5e1d30 / Pack 7b9511f2 alone (CP/Runtime current) is refused as well
        for k in ('replay', 'odes', 'evidence_pack'):
            with self.subTest(only=k):
                s = Scratch(self)
                s.set_all(k, P2[k])
                s.heads[k] = P2[k]
                self.refused(s.guard(), f'tuple.{k} {P2[k]!r} != intended', f'tuple_pin.{k}')

    def test_unknown_or_substituted_sha_for_every_component(self):
        for k in NAMES:
            with self.subTest(component=k):
                s = Scratch(self)
                s.tuple[k] = BOGUS
                self.refused(s.guard(), f'tuple.{k} {BOGUS!r} != intended {guard.EXPECTED[k][0]}', f'tuple_pin.{k}')

    def test_profile_or_manifest_substitution_with_correct_tuple(self):
        cases = [('profile', 'profile.replay revision != intended', 'profile_pin.replay', lambda s: s.profile['components']['replay'].__setitem__('revision', BOGUS)),
                 ('manifest', 'freeze-manifest.moltbot_safe sha != intended', 'manifest_pin.runtime', lambda s: s.man['components_subject']['moltbot_safe'].__setitem__('sha', BOGUS)),
                 ('registry', 'profile registry != intended', 'config_pin.registry', lambda s: s.profile['ocs_registry'].__setitem__('revision', BOGUS)),
                 ('exchange tree', 'freeze-manifest exchange tree != intended', 'manifest_tree.exchange', lambda s: s.man['verified_trees']['trees'].__setitem__('exchange', BOGUS)),
                 ('p2 generation', 'profile suite_generation != cur', 'profile_suite_generation', lambda s: s.profile.__setitem__('suite_generation', 'p2'))]
        for name, reason, cid, mut in cases:
            with self.subTest(name):
                s = Scratch(self)
                mut(s)
                self.refused(s.guard(), reason, cid)

    def test_malformed_sha_branch_prefix_empty(self):
        for bad in ('main', '77fd7a1c', '', 'A' * 40, None):
            with self.subTest(value=bad):
                s = Scratch(self)
                s.tuple['odes'] = bad
                self.refused(s.guard(), f'tuple.odes is not a 40-hex SHA: {bad!r}', 'tuple_sha_format.odes')

    def test_unresolved_placeholder_in_tuple_profile_manifest(self):
        s = Scratch(self)
        s.tuple['exchange'] = 'PLACEHOLDER:PENDING exchange merge SHA'
        self.refused(s.guard(), 'unresolved placeholder/template marker in tuple', 'tuple_no_placeholder')
        s = Scratch(self)
        s.tuple['validation_id'] = 'current-stack-S3-TEMPLATE'
        self.refused(s.guard(), 'unresolved placeholder/template marker in tuple', 'tuple_no_placeholder')
        s = Scratch(self)
        s.profile['note_x'] = 'PLACEHOLDER:name'
        self.refused(s.guard(), 'unresolved placeholder/template marker in profile/freeze-manifest', 'config_no_placeholder')
        s = Scratch(self)
        s.man['identities']['hub']['head'] = 'PLACEHOLDER:hub head SHA at freeze'
        self.refused(s.guard(), 'unresolved placeholder/template marker in profile/freeze-manifest', 'config_no_placeholder')

    def test_tuple_that_is_not_a_json_object(self):
        s = Scratch(self)
        s.write()
        s.tuple_path.write_text('["not", "an", "object"]')
        with mock.patch.object(guard, 'git', s.fake_git):
            self.refused(guard.run_guard(s.tuple_path, s.comps, root=s.root), 'tuple is not a JSON object', 'tuple_is_object')

    def test_wrong_validation_id(self):
        s = Scratch(self)
        s.tuple['validation_id'] = 'current-stack-20261031'
        self.refused(s.guard(), f'validation_id != {guard.VALIDATION_ID}', 'tuple_validation_id')

    def test_invalid_source_identity_checkout_head_tree_pristine_missing(self):
        s = Scratch(self)
        s.heads['replay'] = P2['replay']
        self.refused(s.guard(), f'replay: checkout HEAD != intended {guard.EXPECTED["replay"][0]}', 'checkout_head.replay')
        s = Scratch(self)
        s.trees['odes'] = BOGUS
        self.refused(s.guard(), f'odes: checkout tree != intended {guard.EXPECTED["odes"][1]}', 'checkout_tree.odes')
        s = Scratch(self)
        s.dirty.add('manifest')
        self.refused(s.guard(), 'manifest: checkout is not pristine', 'checkout_pristine.manifest')
        s = Scratch(self)
        __import__('shutil').rmtree(s.comps / 'registry')
        self.refused(s.guard(), 'missing checkout', 'checkout_present.registry')

    def test_real_git_checkout_at_wrong_head_is_refused(self):
        import subprocess
        s = Scratch(self)
        d = s.comps / 'control_plane'
        env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t', GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')
        subprocess.check_call(['git', 'init', '-q', str(d)], env=env)
        subprocess.check_call(['git', '-C', str(d), 'commit', '-q', '--allow-empty', '-m', 'x'], env=env)
        s.write()
        r = guard.run_guard(s.tuple_path, s.comps, root=s.root)  # real git for this one
        self.refused(r, f'control_plane: checkout HEAD != intended {guard.EXPECTED["control_plane"][0]}', 'checkout_head.control_plane')

    def test_exchange_profile_constants_must_equal_tuple(self):
        for c in guard.EXCHANGE_CONSTANTS:
            with self.subTest(constant=c):
                s = Scratch(self)
                s.consts[c] = P2['replay']
                self.refused(s.guard(), f'Exchange profile {guard.EXCHANGE_PROFILE} constant {c}=', f'exchange_constant.{c}')

    def test_exchange_source_without_the_required_profile_block(self):
        s = Scratch(self)
        s.profile_block = 'security-runtime-current-20261031'  # only the original profile is defined in this (fake) Exchange source
        self.refused(s.guard(), f'Exchange source does not define profile {guard.EXCHANGE_PROFILE!r}')

    def test_unreadable_tuple_is_a_refusal_record_not_a_crash(self):
        s = Scratch(self)
        s.write()
        s.tuple_path.write_text('{not json')
        with mock.patch.object(guard, 'git', s.fake_git):
            r = guard.run_guard(s.tuple_path, s.comps, root=s.root)
        self.assertEqual(r['preflight_guard'], 'refused')
        self.assertTrue(r['refusal_reason'].startswith('ValueError') or r['refusal_reason'].startswith('JSONDecodeError'), r['refusal_reason'])


class TestRunnerPreflight(GuardCase):
    """The runner must call the guard first, for --dry-check and real runs, and keep retained evidence."""

    def run_main(self, s, out, *extra):
        o, e = io.StringIO(), io.StringIO()
        with mock.patch.object(runner, 'ROOT', s.root), mock.patch.object(guard, 'git', s.fake_git), \
                mock.patch.object(runner, 'load_tuple', side_effect=AssertionError('runner went past the guard')), \
                mock.patch.object(runner, 'collect_only', side_effect=AssertionError('collect-only must not run')), \
                contextlib.redirect_stdout(o), contextlib.redirect_stderr(e):
            rc = runner.main(['--tuple', str(s.tuple_path), '--components', str(s.comps), '--out', str(out), *extra])
        return rc, o.getvalue(), e.getvalue()

    def test_dry_check_refused_before_anything_else_and_writes_nothing(self):
        s = Scratch(self)
        s.tuple['exchange_compatibility_profile'] = 'security-runtime-current-20261031-r3'
        s.write()
        out = s.tmp / 'out'
        rc, so, se = self.run_main(s, out, '--dry-check')
        self.assertEqual(rc, 2)
        self.assertIn("REFUSED: preflight guard: wrong Exchange profile in tuple: 'security-runtime-current-20261031-r3'", se)
        self.assertEqual(json.loads(so)['preflight_guard'], 'refused')
        self.assertEqual(sorted(p.name for p in s.tmp.iterdir()), ['comps', 'root'])  # nothing written (no out, no -REFUSED)

    def test_real_run_refusal_leaves_a_refusal_record_and_keeps_out_unused(self):
        s = Scratch(self)
        s.tuple['replay'] = P2['replay']
        s.write()
        out = s.tmp / 'out'
        rc, so, se = self.run_main(s, out)
        self.assertEqual(rc, 2)
        self.assertFalse(out.exists())
        rec = json.loads((s.tmp / 'out-REFUSED' / 'guard-result.json').read_text())
        self.assertEqual(rec['preflight_guard'], 'refused')
        self.assertIn('tuple.replay', rec['refusal_reason'])
        self.assertEqual(rec['tuple_sha256'], guard.sha256_file(s.tuple_path))
        self.assertEqual(rec['guard_file']['sha256'], guard.sha256_file(guard.__file__))
        rc, *_ = self.run_main(s, out)  # a second refusal never overwrites the first record
        self.assertTrue((s.tmp / 'out-REFUSED-1' / 'guard-result.json').exists())

    def test_every_refusal_class_stops_the_runner_in_dry_check(self):
        muts = {'placeholder': lambda s: s.tuple.__setitem__('exchange', 'PLACEHOLDER:x'),
                'substituted sha': lambda s: s.tuple.__setitem__('registry', BOGUS),
                'checkout head': lambda s: s.heads.__setitem__('exchange', BOGUS),
                'checkout tree': lambda s: s.trees.__setitem__('runtime', BOGUS)}
        for name, mut in muts.items():
            with self.subTest(name):
                s = Scratch(self)
                mut(s)
                s.write()
                rc, so, se = self.run_main(s, s.tmp / 'out', '--dry-check')
                self.assertEqual(rc, 2)
                self.assertIn('REFUSED: preflight guard:', se)

    def test_no_option_or_environment_variable_skips_the_guard(self):
        src = (REPO / 's3' / 'run_wiki_s3.py').read_text()
        opts = [l.split("'")[1] for l in src.splitlines() if 'ap.add_argument(' in l]
        self.assertEqual(sorted(opts), ['--components', '--dry-check', '--hub', '--nodeids', '--out', '--tuple'])
        s = Scratch(self)
        s.tuple['control_plane'] = BOGUS
        s.write()
        env = {k: '1' for k in ('S3_SKIP_GUARD', 'SKIP_GUARD', 'NO_GUARD', 'S3_GUARD', 'S3_NO_GUARD', 'CI')}
        with mock.patch.dict(os.environ, env):
            rc, so, se = self.run_main(s, s.tmp / 'out', '--dry-check')
        self.assertEqual(rc, 2)
        self.assertIn('tuple.control_plane', se)

    def test_passed_real_run_retains_guard_result_in_run_evidence(self):
        s = Scratch(self)
        out = s.tmp / 'out'
        real_tuple = REPO / TUPLE_REL
        ids = [f'suites/wiki-derived/t.py::T::t{i}' for i in range(41)]

        real_run = runner.subprocess.run

        def fake_run(cmd, **kw):
            if not any(str(c).startswith('--junitxml=') for c in cmd):
                return real_run(cmd, **kw)  # git rev-parse etc. stay real
            junit = [c.split('=', 1)[1] for c in cmd if str(c).startswith('--junitxml=')][0]
            cases = ''.join(f'<testcase classname="suites/wiki-derived/t.py::T" name="t{i}"/>' for i in range(41))
            Path(junit).write_text(f'<testsuites><testsuite>{cases}</testsuite></testsuites>')
            return mock.Mock(returncode=0)

        o = io.StringIO()
        with mock.patch.object(guard, 'git', s.fake_git), mock.patch.object(runner, 'collect_only', return_value=('listing\n', [])), \
                mock.patch.object(runner, 'check_configs', return_value=(REPO / PROFILE_REL, REPO / MAN_REL)), \
                mock.patch.object(runner, 'read_nodeids', return_value=ids), mock.patch.object(runner, 'qual_status', return_value=[]), \
                mock.patch.object(runner, 'check_checkouts', return_value={n: {'path': str(s.comps / n)} for n in runner.CHECKED}), mock.patch.object(runner, 'require_pristine'), \
                mock.patch.object(runner, 'tool_versions', return_value={}), mock.patch.object(runner.subprocess, 'run', fake_run), \
                mock.patch.object(runner, 'load_tuple', return_value=json.loads(real_tuple.read_text())), \
                contextlib.redirect_stdout(o):
            rc = runner.main(['--tuple', str(s.tuple_path), '--components', str(s.comps), '--out', str(out)])
        self.assertEqual(rc, 0, o.getvalue())
        g = json.loads((out / 'raw' / 'guard-result.json').read_text())
        self.assertEqual(g['preflight_guard'], 'passed')
        run = json.loads((out / 'raw' / 'run.json').read_text())
        self.assertEqual(run['preflight_guard'], 'passed')
        self.assertEqual(run['guard_result_sha256'], guard.sha256_file(out / 'raw' / 'guard-result.json'))
        self.assertIn('s3/s3_tuple_guard.py', run['config_hashes'])
        self.assertEqual(run['config_hashes']['s3/s3_tuple_guard.py'], guard.sha256_file(guard.__file__))
        self.assertIn('./raw/guard-result.json', (out / 'SHA256SUMS').read_text())


@unittest.skipUnless((REAL_COMPONENTS / 'registry').is_dir(), 'pristine pinned checkouts not available (set S3_COMPONENTS_DIR)')
class TestRealFrozenConfig(GuardCase):
    def test_real_frozen_config_and_checkouts_pass(self):
        r = guard.run_guard(REPO / TUPLE_REL, REAL_COMPONENTS)
        self.assertEqual(r['preflight_guard'], 'passed', r['refusal_reason'])


if __name__ == '__main__':
    unittest.main()
