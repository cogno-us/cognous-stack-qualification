"""Offline tests of tools/rc_env.py: recipe reading, exact-commit checkout from local repositories, env output and check."""
from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import rc_env  # noqa: E402

REAL_ROOT = Path(__file__).resolve().parents[1]
GIT = ['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid']


def git(path, *args):
    return subprocess.check_output([*GIT, '-C', str(path), *args], text=True).strip()


def make_repo(base, repository, files):
    """A repository the tools can fetch from: returns (first commit, second commit); the tip differs from the first."""
    path = Path(base) / (repository + '.git')
    path.mkdir(parents=True)
    git(path, 'init', '-q')
    git(path, 'config', 'uploadpack.allowAnySHA1InWant', 'true')
    for name, text in files.items():
        (path / name).parent.mkdir(parents=True, exist_ok=True)
        (path / name).write_text(text)
    git(path, 'add', '.')
    git(path, 'commit', '-qm', 'one')
    first = git(path, 'rev-parse', 'HEAD')
    (path / 'later.txt').write_text('later\n')
    git(path, 'add', '.')
    git(path, 'commit', '-qm', 'two')
    return first, git(path, 'rev-parse', 'HEAD')


def write_workflow(root, name, text):
    path = Path(root) / '.github' / 'workflows' / (name + '.yml')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text))
    return path


SHA_A = 'a' * 40
SHA_B = 'b' * 40


class ReadingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def read(self, text, name='w', **kw):
        write_workflow(self.root, name, text)
        return rc_env.read_recipe(name, root=self.root, **kw)

    def test_roles_pins_stage_environment_and_unmodelled_steps(self):
        recipe = self.read(f"""
            name: demo
            on: {{workflow_dispatch: {{}}}}
            jobs:
              test:
                strategy: {{matrix: {{python-version: ['3.11', '3.12']}}}}
                env: {{KEEP: '1'}}
                steps:
                - uses: actions/checkout@v4
                  with:
                    repository: cogno-us/owner
                    ref: ${{{{ inputs.source_revision || '{SHA_A}' }}}}
                - uses: actions/checkout@v4
                  with:
                    repository: cogno-us/cognous-stack-qualification
                    ref: ${{{{ inputs.qualification_revision || github.sha }}}}
                    path: _qualification
                - uses: actions/checkout@v4
                  with: {{repository: cogno-us/dep, ref: {SHA_B}, path: upstream/dep}}
                - name: Verify
                  run: |
                    test "$(git -C upstream/dep rev-parse HEAD)" = "{SHA_B}"
                - uses: actions/setup-python@v5
                  with: {{python-version: '${{{{ matrix.python-version }}}}'}}
                - name: Install
                  run: |
                    pip install --upgrade pip
                    pip install -e upstream/dep
                    python -m pip install -e ".[dev]"
                - name: Only on 3.11
                  if: matrix.python-version == '3.11'
                  run: pytest -q never
                - name: Tests
                  env:
                    DEP_ROOT: ${{{{ github.workspace }}}}/upstream/dep
                    REL: upstream/dep/file.json
                    TOKEN: ${{{{ secrets.THING }}}}
                  run: |
                    set -e
                    pytest -q tests
                    agep check-examples
            """)
        self.assertEqual(recipe['python_version'], '3.12')
        self.assertEqual([(c['role'], c['sha'], c['path']) for c in recipe['checkouts']],
                         [('source', SHA_A, '.'), ('qualification', None, '_qualification'), ('upstream', SHA_B, 'upstream/dep')])
        self.assertEqual(recipe['verify'], [{'path': 'upstream/dep', 'sha': SHA_B}])
        self.assertEqual([e['kind'] for e in recipe['events']], ['install', 'install', 'test'])
        (stage,) = recipe['stages']
        self.assertEqual(stage['env']['KEEP'], '1')
        self.assertEqual(stage['env']['REL'], 'upstream/dep/file.json')
        self.assertTrue(stage['env']['DEP_ROOT'].endswith('/upstream/dep'))
        self.assertNotIn('TOKEN', stage['env'])
        self.assertTrue(any('secret' in s['if'] for s in recipe['skipped_steps']))
        self.assertTrue(any(s['step'] == 'Only on 3.11' for s in recipe['skipped_steps']))
        self.assertEqual([u['line'] for u in recipe['unmodelled']], ['agep check-examples'])

    def test_source_revision_override(self):
        text = f"""
            jobs:
              t:
                steps:
                - uses: actions/checkout@v4
                  with: {{repository: cogno-us/owner, ref: "${{{{ inputs.source_revision || '{SHA_A}' }}}}"}}
                - run: pytest -q
            """
        self.assertEqual(self.read(text, source_rev=SHA_B)['checkouts'][0]['sha'], SHA_B)
        self.assertTrue(self.read(text, source_rev=SHA_B)['source_override'])

    def test_unpinned_or_unknown_inputs_are_refused(self):
        with self.assertRaisesRegex(rc_env.RecipeError, 'not a full commit id'):
            self.read("""
                jobs:
                  t:
                    steps:
                    - uses: actions/checkout@v4
                      with: {repository: cogno-us/owner, ref: main}
                    - run: pytest -q
                """)
        with self.assertRaisesRegex(rc_env.RecipeError, 'expression not modelled'):
            self.read(f"""
                jobs:
                  t:
                    steps:
                    - uses: actions/checkout@v4
                      with: {{repository: cogno-us/owner, ref: "${{{{ github.event.pull_request.head.sha }}}}"}}
                    - run: pytest -q
                """)
        with self.assertRaisesRegex(rc_env.RecipeError, 'pip option not modelled'):
            self.read("""
                jobs:
                  t:
                    steps:
                    - uses: actions/checkout@v4
                    - run: pip install --index-url https://example.invalid/simple pkg
                    - run: pytest -q
                """)

    def test_pip_forms(self):
        self.assertIsNone(rc_env.parse_pip('python -m pip install --upgrade pip'))
        self.assertEqual(rc_env.parse_pip('pip install --require-hashes --only-binary :all: -r tools/x.lock'),
                         [('--require-hashes', None), ('--only-binary', ':all:'), ('-r', 'tools/x.lock')])
        self.assertEqual(rc_env.parse_pip('pip install pytest==8.3.5 pydantic==2.11.9'),
                         [('', 'pytest==8.3.5'), ('', 'pydantic==2.11.9')])
        command = rc_env._pip_command(Path('/v'), [('-e', '.[dev]'), ('-e', 'up/dep'), ('', 'pytest==8')], Path('/ws/pkg'))
        self.assertEqual([str(c) for c in command[4:]], ['-e', '/ws/pkg[dev]', '-e', '/ws/pkg/up/dep', 'pytest==8'])

    def test_overlay_step_is_recognised(self):
        recipe = self.read(f"""
            jobs:
              t:
                steps:
                - uses: actions/checkout@v4
                  with: {{repository: cogno-us/owner, ref: "${{{{ inputs.source_revision || '{SHA_A}' }}}}", path: src}}
                - run: python3 _qualification/tools/install_suite.py --suite some-suite --source-root "src" --evidence "ev/t.json"
                - run: pytest -q
            """)
        overlay = recipe['events'][0]
        self.assertEqual((overlay['kind'], overlay['suite'], overlay['source_root']), ('overlay', 'some-suite', 'src'))


class RepositoryWorkflowTests(unittest.TestCase):
    def test_every_default_recipe_reads_with_exact_pins(self):
        for name in rc_env.DEFAULT_RECIPES:
            with self.subTest(recipe=name):
                recipe = rc_env.read_recipe(name, root=REAL_ROOT)
                self.assertTrue(recipe['stages'])
                for checkout in recipe['checkouts']:
                    if checkout['role'] in ('source', 'upstream'):
                        self.assertRegex(checkout['sha'], r'^[0-9a-f]{40}$')

    def test_the_workflows_own_verification_lines_agree_with_their_checkouts(self):
        for name in rc_env.DEFAULT_RECIPES:
            with self.subTest(recipe=name):
                recipe = rc_env.read_recipe(name, root=REAL_ROOT)
                pins = {c['path'].rstrip('/'): c['sha'] for c in recipe['checkouts'] if c['sha']}
                for item in recipe['verify']:
                    if item['path'].rstrip('/') in pins:
                        self.assertEqual(item['sha'], pins[item['path'].rstrip('/')], item['path'])

    def test_native_hub_root_comes_from_the_pilot_workflow(self):
        recipe = rc_env.read_recipe('claude-agent-pilot:offline-controls', root=REAL_ROOT)
        stage = next(s for s in recipe['stages'] if 'NATIVE_HUB_ROOT' in s['env'])
        self.assertTrue(stage['env']['NATIVE_HUB_ROOT'].endswith('/_native-hub'))
        self.assertIn('tests/native', stage['command'])

    def test_no_pin_value_is_written_in_the_tool(self):
        text = (REAL_ROOT / 'tools' / 'rc_env.py').read_text()
        import re
        self.assertEqual(re.findall(r'\b[0-9a-f]{40}\b', text), [])


class BuildTests(unittest.TestCase):
    """prepare, env and check against repositories on local disk (no network, no package index)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.remotes = base / 'remotes'
        self.work = base / 'work'
        self.root = base / 'qualification'
        self.first_src, self.tip_src = make_repo(self.remotes, 'cogno-us/owner', {'pkg/a.py': 'A = 1\n', 'README': 'x\n'})
        self.first_dep, self.tip_dep = make_repo(self.remotes, 'cogno-us/dep', {'examples/m.json': '{}\n'})
        self.root.mkdir()
        git(self.root, 'init', '-q')
        (self.root / 'f').write_text('f')
        write_workflow(self.root, 'demo', f"""
            jobs:
              test:
                env: {{PYTHONDONTWRITEBYTECODE: '1'}}
                steps:
                - uses: actions/checkout@v4
                  with:
                    repository: cogno-us/owner
                    ref: ${{{{ inputs.source_revision || '{self.first_src}' }}}}
                    path: src
                - uses: actions/checkout@v4
                  with:
                    repository: cogno-us/cognous-stack-qualification
                    ref: ${{{{ inputs.qualification_revision || github.sha }}}}
                    path: _qualification
                - uses: actions/checkout@v4
                  with: {{repository: cogno-us/dep, ref: {self.first_dep}, path: pinned/dep}}
                - name: Verify
                  run: |
                    test "$(git -C pinned/dep rev-parse HEAD)" = "{self.first_dep}"
                - name: Tests
                  working-directory: src
                  env:
                    DEP_ROOT: ${{{{ github.workspace }}}}/pinned/dep
                    FIXTURE: ../pinned/dep/examples/m.json
                    PYTHONPATH: .:../pinned/dep
                    PLAIN: value with spaces
                  run: pytest -q tests
            """)
        git(self.root, 'add', '.')
        git(self.root, 'commit', '-qm', 'qualification')
        self.patches = [mock.patch.object(rc_env, 'ROOT', self.root),
                        mock.patch.dict(os.environ, {rc_env.GIT_BASE_ENV: 'file://' + str(self.remotes) + '/'})]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = rc_env.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def prepare(self, *extra):
        code, out, err = self.cli('prepare', '--work', str(self.work), '--recipe', 'demo', '--python', sys.executable, *extra)
        self.assertEqual(code, 0, err + out)
        return Path(self.work) / 'demo'

    def test_prepare_checks_out_the_exact_pins_not_the_tips(self):
        base = self.prepare()
        self.assertEqual(git(base / 'ws/src', 'rev-parse', 'HEAD'), self.first_src)
        self.assertEqual(git(base / 'ws/pinned/dep', 'rev-parse', 'HEAD'), self.first_dep)
        self.assertNotEqual(self.first_src, self.tip_src)
        self.assertFalse((base / 'ws/src/later.txt').exists())
        self.assertTrue((base / 'ws/_qualification').is_symlink())
        manifest = json.loads((base / rc_env.MANIFEST).read_text())
        self.assertEqual([c['role'] for c in manifest['checkouts']], ['source', 'qualification', 'upstream'])
        self.assertEqual(len(manifest['venvs']), 1)
        self.assertEqual(manifest['claim'], 'NONE: preparing an environment is not execution or acceptance')

    def test_env_prints_resolved_variables_for_the_stage(self):
        base = self.prepare()
        code, out, err = self.cli('env', '--work', str(self.work), '--recipe', 'demo')
        self.assertEqual(code, 0, err)
        exports = {}
        for line in out.splitlines():
            if line.startswith('export '):
                key, _, value = line[len('export '):].partition('=')
                exports[key] = shlex.split(value)[0] if key != 'PATH' else value
        self.assertEqual(exports['DEP_ROOT'], str(base / 'ws/pinned/dep'))
        self.assertEqual(exports['FIXTURE'], str(base / 'ws/pinned/dep/examples/m.json'))
        self.assertEqual(exports['PYTHONPATH'], f'{base}/ws/src:{base}/ws/pinned/dep')
        self.assertEqual(exports['PLAIN'], 'value with spaces')
        self.assertEqual(exports['PYTHONDONTWRITEBYTECODE'], '1')
        self.assertTrue(exports['PATH'].endswith(':"$PATH"'))
        self.assertTrue(Path(exports['VIRTUAL_ENV']).is_dir())
        code, out, _ = self.cli('env', '--work', str(self.work), '--recipe', 'demo', '--json')
        data = json.loads(out)
        self.assertEqual(data['cwd'], str(base / 'ws/src'))
        self.assertEqual(data['command'], 'pytest -q tests')
        code, _, err = self.cli('env', '--work', str(self.work), '--recipe', 'demo', '--stage', 'nope')
        self.assertEqual(code, 2)
        self.assertIn('no stage', err)

    def test_check_passes_then_reports_each_kind_of_mismatch(self):
        base = self.prepare()
        code, out, _ = self.cli('check', '--work', str(self.work))
        self.assertEqual(code, 0, out)
        self.assertIn('all pins and hashes match', out)
        # a tracked file edited by hand
        (base / 'ws/src/README').write_text('edited\n')
        code, out, _ = self.cli('check', '--work', str(self.work))
        self.assertEqual(code, 1)
        self.assertIn('tracked files changed after prepare: README', out)
        git(base / 'ws/src', 'checkout', '-q', '--', 'README')
        # a checkout moved to another commit
        git(base / 'ws/pinned/dep', 'fetch', '-q', 'origin', self.tip_dep)
        git(base / 'ws/pinned/dep', 'checkout', '-q', '--detach', self.tip_dep)
        code, out, _ = self.cli('check', '--work', str(self.work))
        self.assertEqual(code, 1)
        self.assertIn(f'head {self.tip_dep}, pinned {self.first_dep}', out)
        git(base / 'ws/pinned/dep', 'checkout', '-q', '--detach', self.first_dep)
        # a pin changed in the workflow after prepare
        workflow = self.root / '.github/workflows/demo.yml'
        workflow.write_text(workflow.read_text().replace(self.first_dep, self.tip_dep))
        code, out, _ = self.cli('check', '--work', str(self.work))
        self.assertEqual(code, 1)
        self.assertIn('file changed since prepare', out)
        self.assertIn('workflow says %s, prepared %s' % (self.tip_dep, self.first_dep), out)

    def test_check_reports_a_package_installed_after_prepare(self):
        base = self.prepare()
        manifest = json.loads((base / rc_env.MANIFEST).read_text())
        manifest['venvs'][0]['freeze'].append('ghost==1.0')
        (base / rc_env.MANIFEST).write_text(json.dumps(manifest))
        code, out, _ = self.cli('check', '--work', str(self.work))
        self.assertEqual(code, 1)
        self.assertIn('installed packages differ from prepare: ghost==1.0', out)

    def test_prepare_refuses_an_existing_directory_unless_forced(self):
        self.prepare()
        code, _, err = self.cli('prepare', '--work', str(self.work), '--recipe', 'demo', '--python', sys.executable)
        self.assertEqual(code, 2)
        self.assertIn('--force', err)
        self.prepare('--force')
        stray = Path(self.work) / 'other'
        stray.mkdir()
        (stray / 'keep').write_text('x')
        write_workflow(self.root, 'other', (self.root / '.github/workflows/demo.yml').read_text())
        code, _, err = self.cli('prepare', '--work', str(self.work), '--recipe', 'other', '--python', sys.executable, '--force')
        self.assertEqual(code, 2)
        self.assertIn('not a directory made by prepare', err)
        self.assertTrue((stray / 'keep').exists())

    def test_source_revision_override_moves_only_the_source(self):
        base = self.prepare('--source-rev', f'demo={self.tip_src}')
        self.assertEqual(git(base / 'ws/src', 'rev-parse', 'HEAD'), self.tip_src)
        self.assertEqual(git(base / 'ws/pinned/dep', 'rev-parse', 'HEAD'), self.first_dep)
        code, out, _ = self.cli('check', '--work', str(self.work))
        self.assertEqual(code, 0, out)

    def test_plan_is_offline_json(self):
        code, out, _ = self.cli('plan', '--recipe', 'demo')
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)['stages'][0]['command'], 'pytest -q tests')


if __name__ == '__main__':
    unittest.main()
