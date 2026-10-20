"""Shared fixtures of the tests of the comparison runner.

Run (no network): SCN_HUB_DIR=<hub checkout with reference_profiles/> SCN_OPA=<opa 1.21.2 binary> \
    python3 -I -m pytest comparators/runner/tests -q -p no:cacheprovider
The tests run no scenario of any registered set on a configuration for a result: the plumbing tests drive renamed twins whose verdicts
are discarded inside the run.
"""
import json
import os
from pathlib import Path
import sys
import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
OPA = os.environ.get('SCN_OPA', str(REPO / 'comparators/deps/bin/opa'))
PLAN_PATH = REPO / 'comparators/wiki/plans/wiki-subset-plan.json'
DECL_PATH = REPO / 'comparators/runner/ocs-column-declarations.json'


def pytest_sessionstart(session):
    missing = []
    if not os.environ.get('SCN_HUB_DIR'):
        missing.append('SCN_HUB_DIR (hub checkout with reference_profiles/)')
    if not Path(OPA).is_file():
        missing.append('SCN_OPA (opa binary)')
    if missing:
        pytest.exit('the runner tests need: ' + ', '.join(missing), returncode=3)


@pytest.fixture(scope='session')
def opa():
    return OPA


@pytest.fixture(scope='session')
def plan():
    return json.loads(PLAN_PATH.read_text())


@pytest.fixture(scope='session')
def decl():
    return json.loads(DECL_PATH.read_text())
