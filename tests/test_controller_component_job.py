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
        for comp in ('bitrep', 'control_plane', 'gax_imx_transport', 'action_manifest', 'the_index'):
            self.assertEqual(v.provision_siblings(comp, '/x', MANIFEST, LOG, fetch=self.fetch(calls)), [])
        self.assertEqual(calls, [])

    def test_the_evidence_pack_gets_the_pinned_replay_then_control_plane_and_replay_gets_the_pinned_pack(self):
        pins = pins_in_force()
        for component, siblings in (('governance_evidence_pack', ['replay_bundle', 'control_plane']), ('replay_bundle', ['governance_evidence_pack'])):
            calls = []
            recs = v.provision_siblings(component, '/nonexistent/sib', MANIFEST, LOG, fetch=self.fetch(calls))
            self.assertEqual([r['component'] for r in recs], siblings)
            self.assertEqual(calls, [(key, *pins[key]) for key in siblings])
            self.assertTrue(all(r['pinned_sha'] == r['actual_sha'] for r in recs))
            self.assertNotIn(component, siblings)

    def test_provisioned_siblings_are_installed_the_way_the_suites_were_measured(self):
        # evidence pack suite: Replay editable (its importer names the installed Replay commit), Control Plane plain with the extra
        # Replay suite: the pack plain
        recs = {c: {r['component']: r for r in v.provision_siblings(c, '/s', MANIFEST, LOG, fetch=self.fetch([]))} for c in ('governance_evidence_pack', 'replay_bundle')}
        pack_cmds = {k: v.sibling_install_command('py', {**r, 'dir': '/s/' + k}, r['targets'][0]) for k, r in recs['governance_evidence_pack'].items()}
        self.assertEqual(pack_cmds['replay_bundle'], ['py', '-m', 'pip', 'install', '-q', '-e', '/s/replay_bundle'])
        self.assertEqual(pack_cmds['control_plane'], ['py', '-m', 'pip', 'install', '-q', '/s/control_plane[runtime-authority]'])
        pack = recs['replay_bundle']['governance_evidence_pack']
        self.assertEqual(v.sibling_install_command('py', {**pack, 'dir': '/s/p'}, '.'), ['py', '-m', 'pip', 'install', '-q', '/s/p'])
        self.assertEqual(recs['governance_evidence_pack']['control_plane']['targets'], ['.[runtime-authority]', '.'])

    def test_the_sibling_graph_has_no_component_that_is_its_own_sibling(self):
        for comp, wanted in v.SIBLING_PROVISIONING.items():
            self.assertNotIn(comp, [key for key, _ in wanted])

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


BACKEND = """\
import base64, hashlib, os, zipfile
NAME, VERSION, PKG = "agent_replay_bundle", "0.0.0", "src/agent_replay_bundle"


def _wheel(directory, files):
    tag = f"{NAME}-{VERSION}"
    files = dict(files)
    files[f"{tag}.dist-info/METADATA"] = f"Metadata-Version: 2.1\\nName: {NAME}\\nVersion: {VERSION}\\n"
    files[f"{tag}.dist-info/WHEEL"] = "Wheel-Version: 1.0\\nGenerator: tiny\\nRoot-Is-Purelib: true\\nTag: py3-none-any\\n"
    record = "".join(f"{n},sha256=" + base64.urlsafe_b64encode(hashlib.sha256(c.encode()).digest()).rstrip(b"=").decode() + f",{len(c.encode())}\\n" for n, c in files.items())
    files[f"{tag}.dist-info/RECORD"] = record + f"{tag}.dist-info/RECORD,,\\n"
    name = f"{tag}-py3-none-any.whl"
    with zipfile.ZipFile(os.path.join(directory, name), "w") as z:
        for n, c in files.items():
            z.writestr(n, c)
    return name


def get_requires_for_build_wheel(config_settings=None):
    return []


get_requires_for_build_editable = get_requires_for_build_wheel


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    return _wheel(wheel_directory, {f"{NAME}/__init__.py": open(PKG + "/__init__.py").read()})


def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    return _wheel(wheel_directory, {f"__editable__.{NAME}.pth": os.path.abspath("src") + "\\n"})
"""


def _git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', *args], capture_output=True, text=True, check=True).stdout.strip()


def make_replay_fixture(path):
    """A tiny git checkout shaped like the Replay sibling (src layout, one commit) with a dependency-free build backend, so no network is needed."""
    (path / 'src/agent_replay_bundle').mkdir(parents=True)
    (path / 'src/agent_replay_bundle/__init__.py').write_text('VALUE = 1\n')
    (path / 'tinybackend.py').write_text(BACKEND)
    (path / 'pyproject.toml').write_text('[build-system]\nrequires = []\nbuild-backend = "tinybackend"\nbackend-path = ["."]\n')
    subprocess.run(['git', 'init', '-q', str(path)], check=True)
    _git(path, 'add', '.')
    _git(path, 'commit', '-q', '-m', 'one')
    (path / 'src/agent_replay_bundle/__init__.py').write_text('VALUE = 2\n')
    _git(path, 'commit', '-q', '-am', 'two')
    return _git(path, 'rev-parse', 'HEAD')


# The revision detection of the ODES tests (open-decision-evidence-standard src/odes/common.py installed_replay_revision at 2893d935), run
# unchanged inside the interpreter that received the sibling install.
DETECT = r"""
import importlib.metadata as metadata, importlib.util, json, re, subprocess
from pathlib import Path
def installed_replay_revision():
    try:
        spec = importlib.util.find_spec("agent_replay_bundle")
        origin = Path(spec.origin).resolve() if spec is not None and spec.origin else None
    except Exception:
        origin = None
    if origin is not None:
        for parent in list(origin.parents)[:4]:
            if (parent / ".git").exists():
                try:
                    out = subprocess.run(["git", "-C", str(parent), "rev-parse", "HEAD"], capture_output=True, text=True, check=True, timeout=20).stdout.strip()
                except Exception:
                    break
                return out if re.fullmatch(r"[0-9a-f]{40}", out) else None
    try:
        names = metadata.packages_distributions().get("agent_replay_bundle") or []
        if len(set(names)) != 1:
            return None
        raw = metadata.distribution(names[0]).read_text("direct_url.json")
        commit = ((json.loads(raw).get("vcs_info") or {}).get("commit_id")) if raw else None
        return commit if isinstance(commit, str) else None
    except Exception:
        return None
print(json.dumps(installed_replay_revision()))
"""


class SiblingReplayRevision(unittest.TestCase):
    """The Replay sibling must be installed so that ODES can name its revision; a local non-editable install gives it neither a checkout nor a VCS commit."""

    def install_and_detect(self, component, editable_expected):
        import venv
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            head = make_replay_fixture(td / 'replay')
            venv.create(td / 'env', with_pip=True, system_site_packages=False, symlinks=True)
            py = str(td / 'env' / ('Scripts' if os.name == 'nt' else 'bin') / ('python.exe' if os.name == 'nt' else 'python'))
            sb = {'component': component, 'dir': str(td / 'replay')}
            cmd = v.sibling_install_command(py, sb, '.')
            self.assertEqual('-e' in cmd, editable_expected)
            subprocess.run(cmd, cwd=td, check=True, capture_output=True, text=True, timeout=300)
            found = subprocess.run([py, '-I', '-c', DETECT], cwd=td, check=True, capture_output=True, text=True, timeout=60).stdout
            return head, json.loads(found)

    def test_the_provisioned_replay_sibling_reports_its_checkout_head(self):
        head, found = self.install_and_detect('replay_bundle', True)
        self.assertEqual(found, head)

    def test_a_plain_local_install_reports_no_revision(self):
        # the pre-fix behaviour, kept as a control: the detection must find nothing here, or the test above proves nothing
        _, found = self.install_and_detect('some_other_sibling', False)
        self.assertIsNone(found)

    def test_install_commands_per_sibling(self):
        cp = {'component': 'control_plane', 'dir': '/s/cp'}
        self.assertEqual(v.sibling_install_command('py', cp, '.[runtime-authority]'), ['py', '-m', 'pip', 'install', '-q', '/s/cp[runtime-authority]'])
        self.assertEqual(v.sibling_install_command('py', cp, '.'), ['py', '-m', 'pip', 'install', '-q', '/s/cp'])
        rb = {'component': 'replay_bundle', 'dir': '/s/r'}
        self.assertEqual(v.sibling_install_command('py', rb, '.'), ['py', '-m', 'pip', 'install', '-q', '-e', '/s/r'])
        self.assertIn(('replay_bundle', ('.',)), v.SIBLING_PROVISIONING['odes'])


class ProbeSuiteTimeout(unittest.TestCase):
    """A probe suite that outlives --timeout leaves an INCONCLUSIVE result.json, never an unhandled exception and never a pass."""

    def run_probe(self, script_body):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            fake = td / 'fakepy'
            fake.write_text('#!/bin/sh\n' + script_body)
            fake.chmod(0o755)
            (td / 'repo').mkdir(); (td / 'suite').mkdir()
            args = argparse.Namespace(component='c', repo_dir=str(td / 'repo'), out=str(td / 'out'), os_name='linux', suite=str(td / 'suite'),
                                      repository='o/r', sha='a' * 40, refreeze_log=None, pins_manifest=None, full_history=False, timeout=1,
                                      env_var='PROBE_INDEX_DIR', npm_dir=None, extras=None, harness_requirements=False)
            with mock.patch.object(v, 'fetch_exact', return_value='a' * 40), mock.patch.object(v, 'run', return_value=(0, '', 0.0, False)), \
                    mock.patch.object(sys, 'executable', str(fake)), mock.patch('builtins.print'):
                v.cmd_probe_suite(args)
            return json.loads((td / 'out' / 'result.json').read_text())

    def test_timeout_is_inconclusive_with_the_reason(self):
        result = self.run_probe('exec sleep 30\n')
        self.assertEqual(result['status'], 'INCONCLUSIVE')
        self.assertEqual(result['reason'], 'probe suite timed out after 1 s')
        self.assertEqual(result['attempts'][0]['outcome'], 'INCONCLUSIVE')
        self.assertEqual(result['attempts'][0]['returncode'], 124)

    def test_a_partial_junit_is_kept_but_never_makes_a_timeout_a_pass(self):
        body = ('for a in "$@"; do case "$a" in --junitxml=*) f="${a#--junitxml=}";; esac; done\n'
                'printf \'<testsuite><testcase classname="a" name="b"/></testsuite>\' > "$f"\nexec sleep 30\n')
        result = self.run_probe(body)
        self.assertEqual(result['status'], 'INCONCLUSIVE')
        self.assertEqual(result['reason'], 'probe suite timed out after 1 s')
        self.assertEqual(result['attempts'][0]['counts']['testcases'], 1)

    def test_a_suite_that_finishes_in_time_still_passes(self):
        body = ('for a in "$@"; do case "$a" in --junitxml=*) f="${a#--junitxml=}";; esac; done\n'
                'printf \'<testsuite><testcase classname="a" name="b"/></testsuite>\' > "$f"\n')
        self.assertEqual(self.run_probe(body)['status'], 'PASS')


if __name__ == '__main__':
    unittest.main()
