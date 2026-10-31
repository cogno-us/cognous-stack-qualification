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
    def test_single_notice_escaped_and_bounded(self):
        rows = [{'test_id': f'a/b.py::t{i}', 'verdict_prelim': 'FAIL', 'first_failure_boundary': 'x' * 400 + '\nmore'} for i in range(41)]
        a = h.build_annotation(rows, {'PASS': 0, 'FAIL': 41, 'BLOCKED': 0}, 41, 41, {'python': '3.13', 'pytest': '9', 'jsonschema': '4'})
        self.assertTrue(a.startswith('::notice '))
        self.assertNotIn('\n', a)
        self.assertEqual(a.count('%0A'), 2 + 41 - 1)
        self.assertIn('collected 41', a)
        self.assertLess(len(a), 60100)
        for i in range(41):
            self.assertIn(f't{i} | FAIL', a)


if __name__ == '__main__':
    unittest.main()
