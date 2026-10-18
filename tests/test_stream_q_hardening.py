"""Input-validation, fixed-location aggregation, export path safety and workflow static checks."""
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import v1_validation as v  # noqa: E402
from safe_paths import assert_plain_tree, resolve_regular_file, safe_relative_name  # noqa: E402

VID = 'v1-2026-10-16-t'


def run_aggregate(layout, vid=VID):
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        inp = td / 'in'
        inp.mkdir()
        for rel, value in layout.items():
            f = inp / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(value))
        with contextlib.redirect_stdout(io.StringIO()):
            v.cmd_aggregate(argparse.Namespace(inputs=str(inp), out=str(td / 'out'), validation_id=vid, requirements=None))
        return json.loads((td / 'out/summary.json').read_text())


def res(component, st='PASS', os_='ubuntu-latest', py='3.12'):
    return {'component': component, 'status': st, 'os': os_, 'python': py}


class AggregateLocations(unittest.TestCase):
    base = {'v1v-freeze/freeze-verification.json': {'status': 'PASS'},
            'v1v-plan/plan.json': {'include': [{'component': 'a', 'os': 'ubuntu-latest', 'python': '3.12'}]},
            'v1v-comp-a/result.json': res('a')}

    def test_fixed_locations_accepted(self):
        self.assertEqual(run_aggregate(self.base)['missing_jobs'], 0)

    def test_bad_validation_id_refused(self):
        for bad in ('x; echo', 'v1-2026-10-16-A', 'v1-2026-10-16-', '../v1-2026-10-16-a'):
            with self.assertRaises(SystemExit):
                run_aggregate(self.base, bad)

    def test_nested_plan_cannot_shrink_expected_jobs(self):
        layout = dict(self.base)
        layout['v1v-comp-a/sub/plan.json'] = {'include': []}
        with self.assertRaises(SystemExit):
            run_aggregate(layout)

    def test_nested_result_and_foreign_freeze_refused(self):
        for rel in ('v1v-comp-a/x/result.json', 'v1v-comp-a/freeze-verification.json', 'v1v-plan/result.json'):
            layout = dict(self.base)
            layout[rel] = res('a') if rel.endswith('result.json') else {'status': 'PASS'}
            with self.assertRaises(SystemExit):
                run_aggregate(layout)

    def test_duplicate_component_os_python_refused(self):
        layout = dict(self.base)
        layout['v1v-comp-a-dup/result.json'] = res('a', 'FAIL')
        with self.assertRaises(SystemExit):
            run_aggregate(layout)

    def test_symlinked_control_record_refused(self):
        with tempfile.TemporaryDirectory() as td:
            inp = Path(td) / 'in'
            (inp / 'v1v-comp-a').mkdir(parents=True)
            target = Path(td) / 'real.json'
            target.write_text(json.dumps(res('a')))
            os.symlink(target, inp / 'v1v-comp-a/result.json')
            with self.assertRaises(SystemExit):
                v.collect_control_records(inp)


class ExportPathSafety(unittest.TestCase):
    def test_unsafe_names_refused(self):
        for bad in ('../x', '/etc/passwd', 'a/../b', 'a\\b', '', 'a//b', './a', 'a\x00b'):
            with self.assertRaises(ValueError):
                safe_relative_name(bad)

    def test_symlink_and_non_regular_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / 'r'
            root.mkdir()
            (root / 'ok.txt').write_text('x')
            (root / 'd').mkdir()
            outside = Path(td) / 'outside.txt'
            outside.write_text('secret')
            os.symlink(outside, root / 'link.txt')
            os.symlink(Path(td), root / 'dirlink')
            self.assertEqual(resolve_regular_file(root, 'ok.txt'), root / 'ok.txt')
            for bad in ('link.txt', 'dirlink/outside.txt', 'd', 'missing'):
                with self.assertRaises((ValueError, OSError)):
                    resolve_regular_file(root, bad)
            with self.assertRaises(ValueError):
                assert_plain_tree(root)


class WorkflowStatic(unittest.TestCase):
    def workflows(self):
        return sorted((ROOT / '.github/workflows').glob('*.yml'))

    def run_blocks(self, text):
        blocks, lines, i = [], text.split('\n'), 0
        while i < len(lines):
            m = re.match(r'^(\s*)(?:- )?run:\s*(.*)$', lines[i])
            if m:
                indent, rest = len(m.group(1)), m.group(2)
                if rest in ('|', '>', '|-', '>-', '|+'):
                    j, body = i + 1, []
                    while j < len(lines) and (not lines[j].strip() or len(lines[j]) - len(lines[j].lstrip()) > indent):
                        body.append(lines[j]); j += 1
                    blocks.append('\n'.join(body)); i = j; continue
                blocks.append(rest)
            i += 1
        return blocks

    def test_no_inputs_or_env_expressions_in_run_blocks(self):
        for wf in self.workflows():
            for block in self.run_blocks(wf.read_text()):
                self.assertNotIn('${{ inputs.', block, wf.name)
                self.assertNotIn('${{inputs.', block, wf.name)
                self.assertNotRegex(block, r'\$\{\{\s*(inputs|github\.event|env)\.', wf.name)

    def test_actions_are_pinned_by_full_sha(self):
        for wf in self.workflows():
            for m in re.finditer(r'uses:\s*([^\s#]+)', wf.read_text()):
                ref = m.group(1)
                if ref.startswith('./'):
                    continue
                self.assertRegex(ref, r'@[0-9a-f]{40}$', f'{wf.name}: {ref}')

    def test_every_job_has_timeout_and_workflows_declare_permissions(self):
        for wf in self.workflows():
            text = wf.read_text()
            self.assertRegex(text, r'(?m)^permissions:', wf.name)
            self.assertEqual(len(re.findall(r'(?m)^    runs-on:', text)), len(re.findall(r'(?m)^    timeout-minutes:', text)), wf.name)

    def test_results_job_requires_plan_success(self):
        text = (ROOT / '.github/workflows/v1-validation.yml').read_text()
        self.assertIn("needs.plan.result == 'success'", text)

    def test_prp_openai_evaluation_workflow_absent(self):
        self.assertFalse((ROOT / '.github/workflows/prp-openai-evaluation.yml').exists())


if __name__ == '__main__':
    unittest.main()
