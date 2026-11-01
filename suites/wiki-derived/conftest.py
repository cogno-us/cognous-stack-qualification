"""Fixtures for the scenario-derived suite.

SPDX-License-Identifier: Apache-2.0

* registers the ``wiki_case`` marker and records its case id as a test property (``wiki_case``);
* ``no_network`` (autouse): attempted IP network access is refused and counted, and the count must stay zero;
* ``pinned_reference``: the pinned bounded reference of suites/v1-scenarios, verified pristine before and after the module.
  Without SCN_COMPONENTS_DIR the test is skipped (never passed).
"""
import os
import socket
import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))


def pytest_configure(config):
    config.addinivalue_line('markers', 'wiki_case(case_id): the catalog case id this test checks (a string literal)')


@pytest.fixture(autouse=True)
def _record_wiki_case(request, record_property):
    for mark in request.node.iter_markers('wiki_case'):
        record_property('wiki_case', mark.args[0])
    yield


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    attempts = []
    real_connect = socket.socket.connect

    def refuse(self, address):
        if self.family in (socket.AF_INET, socket.AF_INET6):
            attempts.append(repr(address))
            raise PermissionError('network access is prohibited in the synthetic harness')
        return real_connect(self, address)

    monkeypatch.setattr(socket.socket, 'connect', refuse)
    yield attempts
    assert attempts == [], f'prohibited network access attempted: {attempts}'


@pytest.fixture(scope='module')
def pinned_reference():
    if not os.environ.get('SCN_COMPONENTS_DIR'):
        pytest.skip('SCN_COMPONENTS_DIR is not set (layout: tools/run_security_runtime.py --prepare-work)')
    import _wiki_helpers as W
    H = W._h()
    ref = H.reference()
    yield ref
    H.assert_pins_still_pristine()
