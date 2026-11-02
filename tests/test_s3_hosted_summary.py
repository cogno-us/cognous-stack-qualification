"""Classification regression for the hosted S3 summary helper (s3/ci/summarize_hosted_run.py). Non-authorizing; hermetic.

A missing runner dependency (ModuleNotFoundError) must be BLOCKED and a harness defect, never a security FAIL; a real assertion failure stays FAIL;
ENOSPC stays BLOCKED. Also checks the single ::notice annotation shape.   Run: python -m unittest tests.test_s3_hosted_summary
"""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 's3' / 'ci'))
import summarize_hosted_run as h  # noqa: E402


def case(tag=None, msg='', text=''):
    c = ET.Element('testcase', classname='suites.x.test_a', name='test_one', time='0.1')
    if tag:
        e = ET.SubElement(c, tag, message=msg)
        e.text = text
    return c


class Classify(unittest.TestCase):
    def test_module_not_found_is_blocked_and_dependency_error(self):
        c = case('error', "ModuleNotFoundError: No module named 'jsonschema'")
        self.assertEqual(h.classify(c)[0], 'BLOCKED')
        self.assertTrue(h.dependency_error(c))

    def test_wrapped_assertion_text_with_missing_module_is_blocked(self):
        c = case('failure', 'AssertionError', "assert 'x' in \"ModuleNotFoundError: No module named 'jsonschema'\"")
        self.assertEqual(h.classify(c)[0], 'BLOCKED')

    def test_assertion_failure_is_fail(self):
        c = case('failure', 'AssertionError: expected refusal, got acceptance', 'assert False')
        self.assertEqual(h.classify(c)[0], 'FAIL')
        self.assertFalse(h.dependency_error(c))

    def test_enospc_is_blocked_not_dependency(self):
        c = case('error', 'OSError: [Errno 28] No space left on device')
        self.assertEqual(h.classify(c)[0], 'BLOCKED')
        self.assertFalse(h.dependency_error(c))

    def test_pass_and_skip(self):
        self.assertEqual(h.classify(case())[0], 'PASS')
        c = case()
        ET.SubElement(c, 'skipped', message='s')
        self.assertEqual(h.classify(c)[0], 'BLOCKED')


class Annotation(unittest.TestCase):
    def test_chunked_notices_cover_all_41_ids_and_stay_under_4096(self):
        rows = [{'test_id': f'a/b.py::test_case_{i:02d}_' + 'n' * 80, 'verdict_prelim': 'FAIL' if i % 2 else 'PASS',
                 'first_failure_boundary': 'x' * 400 + '\nmore'} for i in range(41)]
        notes = h.build_annotations(rows, {'PASS': 21, 'FAIL': 20, 'BLOCKED': 0}, 41, 41, {'python': '3.13', 'pytest': '9', 'jsonschema': '4'})
        self.assertGreater(len(notes), 1)
        n = len(notes)
        for k, a in enumerate(notes, 1):
            self.assertTrue(a.startswith(f'::notice title=S3 C3 per-test verdicts ({k}/{n})::'))
            self.assertNotIn('\n', a)
            self.assertLess(len(a.split('::', 2)[2]), 4096)
            self.assertIn(f'chunk {k}/{n}', a)
        joined = '\n'.join(notes)
        self.assertIn('collected 41', notes[0])
        self.assertIn('jsonschema 4', notes[0])
        for i in range(41):
            self.assertIn(f'test_case_{i:02d}_', joined)
            self.assertEqual(joined.count(f'test_case_{i:02d}_'), 1)

    def test_escaping(self):
        self.assertEqual(h.gh_escape('a%b\nc\r'), 'a%25b%0Ac%0D')


if __name__ == '__main__':
    unittest.main()
