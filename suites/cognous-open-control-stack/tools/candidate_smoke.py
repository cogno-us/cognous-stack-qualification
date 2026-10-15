#!/usr/bin/env python3
"""Run bounded synthetic tests from an extracted candidate, without Git or network."""
import argparse
from pathlib import Path
import sys
import unittest

parser = argparse.ArgumentParser()
parser.add_argument("--source-root", type=Path, required=True)
ROOT = parser.parse_args().source_root.resolve()
sys.path.insert(0, str(ROOT))
from tools.check_contract_surfaces import check


def main():
    check()
    suite = unittest.TestSuite()
    for name in ('test_semantic_handoff_contract.py', 'test_resolver_assurance.py',
                 'test_protected_destination.py'):
        selected = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern=name)
        if selected.countTestCases() == 0:
            raise ValueError('missing required smoke suite: ' + name)
        suite.addTests(selected)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() and result.testsRun > 0 and not result.skipped else 1


if __name__ == '__main__':
    raise SystemExit(main())
