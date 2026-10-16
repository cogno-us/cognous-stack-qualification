"""Local runners refuse checkouts whose executed bytes could differ from the pinned tree."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1]/'tools'
sys.path.insert(0, str(TOOLS))
from pristine_checkout import require_pristine
import prp_openai_evaluation as prp_eval
import run_runtime_authority as runtime
import final_source_preflight as preflight

MODES = ('unstaged', 'staged', 'untracked', 'ignored', 'assume-unchanged', 'skip-worktree')


class PristineCheckout(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name); self.repo = self.root/'component'; self.repo.mkdir()
        self.git('init', '-q')
        (self.repo/'source.py').write_text('value = 1\n')
        (self.repo/'.gitignore').write_text('ignored.py\n')
        self.git('add', '.'); self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')
        self.sha = self.git('rev-parse', 'HEAD').strip()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], text=True)

    def contaminate(self, mode):
        sentinel = "raise AssertionError('sentinel executed')\n"
        if mode == 'untracked': (self.repo/'shadow.py').write_text(sentinel)
        elif mode == 'ignored': (self.repo/'ignored.py').write_text(sentinel)
        else:
            if mode == 'assume-unchanged': self.git('update-index', '--assume-unchanged', 'source.py')
            if mode == 'skip-worktree': self.git('update-index', '--skip-worktree', 'source.py')
            (self.repo/'source.py').write_text(sentinel)
            if mode == 'staged': self.git('add', 'source.py')

    real_run = subprocess.run

    def refuse_pytest(self, command, *args, **kwargs):
        if 'pytest' in command: raise AssertionError('child launched')
        return PristineCheckout.real_run(command, *args, **kwargs)

    def restore(self):
        self.git('update-index', '--no-assume-unchanged', 'source.py')
        self.git('update-index', '--no-skip-worktree', 'source.py')
        self.git('reset', '--hard', '-q', self.sha); self.git('clean', '-fdxq')

    def test_shared_check(self):
        self.assertEqual(require_pristine(self.repo, self.sha), self.sha)
        with self.assertRaisesRegex(ValueError, 'mismatch'): require_pristine(self.repo, '0'*40)
        for mode in MODES:
            with self.subTest(mode=mode):
                self.contaminate(mode)
                with self.assertRaises(ValueError): require_pristine(self.repo, self.sha)
                self.restore()
        require_pristine(self.repo, self.sha)

    def test_prp_evaluation_refuses_before_executing_scorer(self):
        out = self.root.parent/(self.root.name+'-prp-out')
        config = prp_eval.validate(json.loads(prp_eval.CONFIG.read_text())) | {'prp_commit': self.sha}
        for mode in MODES:
            with self.subTest(mode=mode):
                self.contaminate(mode)
                argv = ['prp', '--prp', str(self.repo), '--output', str(out)]
                with patch.object(prp_eval, 'validate', return_value=config), patch.object(sys, 'argv', argv), \
                     patch('sys.stderr'), self.assertRaises(SystemExit):
                    prp_eval.main()
                self.assertFalse(out.exists())
                self.restore()

    def test_runtime_authority_refuses_before_launch(self):
        (self.root/'process').mkdir()
        (self.root/'process/runtime-authority-candidate-2026-10-15.json').write_text(
            json.dumps({'components': {'component': {'revision': self.sha}}}))
        out = self.root/'out'
        for mode in MODES:
            with self.subTest(mode=mode):
                self.contaminate(mode)
                argv = ['runtime', '--components', str(self.root), '--out', str(out)]
                with patch.object(runtime, 'ROOT', self.root), patch.object(sys, 'argv', argv), \
                     patch.object(runtime.subprocess, 'run', side_effect=self.refuse_pytest), \
                     self.assertRaises(SystemExit):
                    runtime.main()
                self.assertFalse(out.exists())
                self.restore()

    def test_final_source_preflight_refuses_before_import(self):
        profile = self.root/'profile.json'
        profile.write_text(json.dumps({'selected': False, 'reference_release_authorized': False,
                                       'production_deployment_authorized': False,
                                       'components': {'component': {'repository': 'x/component', 'sha': self.sha}}}))
        out = self.root.parent/(self.root.name+'-preflight.json')
        for mode in MODES:
            with self.subTest(mode=mode):
                self.contaminate(mode)
                argv = ['preflight', '--profile', str(profile), '--work', str(self.root), '--out', str(out)]
                with patch.object(sys, 'argv', argv), \
                     patch.object(preflight.importlib, 'import_module', side_effect=AssertionError('imported')), \
                     self.assertRaisesRegex(ValueError, 'Unclean or mismatched source'):
                    preflight.main()
                self.restore()


if __name__ == '__main__':
    unittest.main()
