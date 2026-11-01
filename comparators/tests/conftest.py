"""Shared fixtures of the comparator package tests.

Run (no network): SCN_HUB_DIR=<hub checkout with reference_profiles/> SCN_OPA=<opa 1.21.2 binary> \
    python3 -I -m pytest comparators/tests -q -p no:cacheprovider
The OPA binary is the one named in suites/cognous-open-control-stack/benchmarks/governance/dependencies.json
(its sha256 is checked by test_package_digests.py); it is not stored in the repository.
"""
import os
from pathlib import Path
import sys
import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
OPA = os.environ.get('SCN_OPA', str(REPO / 'comparators/deps/bin/opa'))


def pytest_sessionstart(session):
    missing = []
    if not os.environ.get('SCN_HUB_DIR'):
        missing.append('SCN_HUB_DIR (hub checkout with reference_profiles/)')
    if not Path(OPA).is_file():
        missing.append('SCN_OPA (opa binary)')
    if missing:
        pytest.exit('comparator package tests need: ' + ', '.join(missing), returncode=3)


@pytest.fixture
def opa():
    return OPA


@pytest.fixture
def make(tmp_path, opa):
    from comparators.wiki.apps.wiki_opa_app import WikiOpaApp
    count = [0]

    def build(mutation=None):
        count[0] += 1
        return WikiOpaApp(tmp_path / f'a{count[0]}', opa, mutation)
    return build
