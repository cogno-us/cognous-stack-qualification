"""F-T3-1: check-workflow-pins reads the workflow as YAML structure. The regular-expression version missed a bad sha when `ref:` preceded
`repository:`, with a key between them, a trailing comment, a quoted repository, CRLF, `sha:` before `repo:`, a multi-line matrix entry, an
uppercase owner or a `git clone` command, and never required a pinned repository's literal to be present."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'suites'))
import _pins  # noqa: E402
import v1_validation as v  # noqa: E402

RESOLVED = _pins.RESOLVED_MANIFEST
CP = 'cogno-us/cognous-control-plane'
GOOD = next(s['sha'] for _, _, s in v.all_components(RESOLVED) if s['repository'] == CP)
BAD = 'e' * 40


def mismatches(text, resolved=RESOLVED):
    return v.workflow_pin_mismatches(text, resolved)


def wf(step, nl='\n'):
    return nl.join(['name: t', 'jobs:', '  j:', '    steps:'] + ['      ' + line for line in step.split('\n')]) + nl


class Variants(unittest.TestCase):
    def assert_bad(self, text):
        out = mismatches(text)
        self.assertTrue(any(CP in m and BAD in m for m in out), out)

    def assert_good(self, text):
        self.assertEqual(mismatches(text), [])

    def test_the_straight_form_is_judged(self):
        self.assert_good(wf(f'- uses: actions/checkout@{"a" * 40}\n  with:\n    repository: {CP}\n    ref: {GOOD}'))
        self.assert_bad(wf(f'- uses: actions/checkout@{"a" * 40}\n  with:\n    repository: {CP}\n    ref: {BAD}'))

    def test_ref_before_repository(self):
        self.assert_bad(wf(f'- uses: x\n  with:\n    ref: {BAD}\n    repository: {CP}'))

    def test_a_key_between_repository_and_ref(self):
        self.assert_bad(wf(f'- uses: x\n  with:\n    repository: {CP}\n    path: _cp\n    fetch-depth: 0\n    ref: {BAD}'))

    def test_trailing_comment(self):
        self.assert_bad(wf(f'- uses: x\n  with:\n    repository: {CP}   # pinned\n    ref: {BAD}   # the pin'))

    def test_quoted_repository_and_ref(self):
        self.assert_bad(wf(f'- uses: x\n  with:\n    repository: "{CP}"\n    ref: \'{BAD}\''))

    def test_crlf(self):
        self.assert_bad(wf(f'- uses: x\n  with:\n    repository: {CP}\n    ref: {BAD}', nl='\r\n'))

    def test_matrix_sha_before_repo(self):
        self.assert_bad(wf(f'- run: x\n  strategy:\n    matrix:\n      include:\n        - {{sha: {BAD}, repo: {CP}}}'))

    def test_matrix_entry_in_block_style_over_several_lines(self):
        self.assert_bad(wf(f'- run: x\n  strategy:\n    matrix:\n      include:\n        - name: p\n          repo: {CP}\n          env: X\n          sha: {BAD}'))

    def test_uppercase_owner(self):
        self.assert_bad(wf(f'- uses: x\n  with:\n    repository: COGNO-US/Cognous-Control-Plane\n    ref: {BAD}'))

    def test_git_clone_command(self):
        self.assert_bad(wf(f'- run: |\n    git clone https://github.com/{CP}.git cp\n    git -C cp checkout {BAD}'))
        self.assert_good(wf(f'- run: |\n    git clone https://github.com/{CP}.git cp\n    git -C cp checkout {GOOD}'))

    def test_a_non_sha_ref(self):
        out = mismatches(wf(f'- uses: x\n  with:\n    repository: {CP}\n    ref: main'))
        self.assertTrue(any('main' in m for m in out), out)

    def test_an_all_digit_sha_is_a_string_not_an_integer(self):
        out = mismatches(wf(f'- uses: x\n  with:\n    repository: {CP}\n    ref: {"1" * 40}'))
        self.assertTrue(any('1' * 40 in m for m in out), out)

    def test_an_unpinned_repository_is_not_judged(self):
        self.assert_good(wf(f'- uses: x\n  with:\n    repository: someone/else\n    ref: {BAD}'))

    def test_a_hex_literal_in_another_key_next_to_a_pinned_repository(self):
        self.assert_bad(wf(f'- run: x\n  strategy:\n    matrix:\n      include:\n        - {{repo: {CP}, expected: {BAD}}}'))

    def test_a_duplicate_key_is_refused(self):
        with self.assertRaises(SystemExit):
            mismatches(wf(f'- uses: x\n  with:\n    repository: {CP}\n    ref: {GOOD}\n    ref: {BAD}'))

    def test_invalid_yaml_is_refused(self):
        with self.assertRaises(SystemExit):
            mismatches('jobs: [unclosed')


class Presence(unittest.TestCase):
    def test_a_named_pinned_repository_without_a_literal_is_reported(self):
        out = mismatches(wf(f'- run: echo using {CP}'))
        self.assertTrue(any(CP in m and 'no sha literal' in m for m in out), out)

    def test_a_literal_replaced_by_an_expression_is_reported(self):
        out = mismatches(wf(f'- uses: x\n  with:\n    repository: {CP}\n    ref: ${{{{ inputs.ref }}}}'))
        self.assertTrue(out)

    def test_a_repository_the_workflow_never_names_needs_no_literal(self):
        self.assertEqual(mismatches(wf('- run: echo hi')), [])


class RepositoryWorkflow(unittest.TestCase):
    TEXT = (ROOT / '.github/workflows/v1-validation.yml').read_text()

    def test_the_repository_workflow_is_valid_with_all_18_literals(self):
        self.assertEqual(mismatches(self.TEXT), [])
        pins = {s['repository'].lower() for _, _, s in v.all_components(RESOLVED)} | {RESOLVED['identities']['hub']['repository'].lower()}
        lits = v.workflow_pin_literals(self.TEXT, pins)
        self.assertGreaterEqual(len(lits), 18)

    def test_the_repository_workflow_with_a_moved_pin_is_reported(self):
        res = copy.deepcopy(RESOLVED)
        res['components_subject']['control_plane']['sha'] = BAD
        self.assertTrue(any('control-plane' in m for m in mismatches(self.TEXT, res)))

    def test_the_plan_job_installs_the_hash_locked_yaml_reader_before_the_check(self):
        i = self.TEXT.index('check-workflow-pins')
        self.assertIn('--require-hashes -r .github/locks/jsonschema-pyyaml-c943d3.txt', self.TEXT[:i])


if __name__ == '__main__':
    unittest.main()
