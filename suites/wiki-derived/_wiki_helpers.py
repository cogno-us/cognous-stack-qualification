"""Shared helpers for the scenario-derived suite.

SPDX-License-Identifier: Apache-2.0

Three parts:

* the case-id marker ``wiki_case`` and the registry (static scan of this suite's test files against
  scenarios/ai-security-wiki/applicability.json);
* thin wrappers over the synthetic destination helpers of suites/v1-scenarios, loaded lazily so that the registry part works
  without any pinned reference;
* ``run_twice``: the same trial from two fresh work directories.

Synthetic destination routes (no network, no payment, no model call, no production effect):

* route A: effective-grant SQLite destination behind the pinned control-plane executor (``route_a``, ``execute_a``)
* route B: atomic-claim SQLite destination (``route_b``, ``execute_b``)
* route C: local durable exchange with a synthetic refund destination (``route_c``, ``exchange_run``, ``exchange_resume``)
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
APPLICABILITY = ROOT / 'scenarios/ai-security-wiki/applicability.json'
CATALOG = ROOT / 'scenarios/ai-security-wiki/catalog.json'
IN_SCOPE = ('APPLICABLE', 'PARTLY_COVERED')
MARKER = 'wiki_case'


# ------------------------------------------------------------------------------------------------ marker
def wiki_case(case_id):
    """Mark a test (or a module, through ``pytestmark``) with the case id it checks. The id must be a string literal so that the
    registry can read it without importing the module. conftest.py records it as the ``wiki_case`` property of the test."""
    return getattr(pytest.mark, MARKER)(case_id)


# ------------------------------------------------------------------------------------------------ applicability and catalog
_APPLICABILITY = None
_CATALOG_IDS = None


def load_applicability():
    global _APPLICABILITY
    if _APPLICABILITY is None:
        _APPLICABILITY = json.loads(APPLICABILITY.read_text(encoding='utf-8'))
    return _APPLICABILITY


def catalog_ids():
    global _CATALOG_IDS
    if _CATALOG_IDS is None:
        _CATALOG_IDS = {s['id'] for s in json.loads(CATALOG.read_text(encoding='utf-8'))['scenarios']}
    return _CATALOG_IDS


def ids_by_classification(*classes):
    return {c['id'] for c in load_applicability()['cases'] if c['classification'] in classes}


def in_scope_ids():
    return ids_by_classification(*IN_SCOPE)


# ------------------------------------------------------------------------------------------------ registry
def scan_source(source, filename):
    """(filename, line, case id or None) for every ``wiki_case(...)`` or ``<x>.wiki_case(...)`` call in ``source``.
    None stands for an argument that is not a string literal."""
    found = []
    for node in ast.walk(ast.parse(source, filename)):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else None
        if name != MARKER:
            continue
        arg = node.args[0] if node.args else None
        literal = isinstance(arg, ast.Constant) and isinstance(arg.value, str)
        found.append((filename, node.lineno, arg.value if literal else None))
    return found


def scan_suite():
    """The case ids carried by the test modules of this suite (the helper modules themselves are not scanned)."""
    found = []
    for path in sorted(HERE.glob('test_*.py')):
        found.extend(scan_source(path.read_text(encoding='utf-8'), path.name))
    return found


def registry_problems(found):
    problems = []
    in_scope, catalog = in_scope_ids(), catalog_ids()
    classes = {c['id']: c['classification'] for c in load_applicability()['cases']}
    for filename, line, case_id in found:
        where = f'{filename}:{line}'
        if case_id is None:
            problems.append(f'{where}: the case id must be a string literal')
        elif case_id not in catalog:
            problems.append(f'{where}: {case_id} is not a case of the catalog')
        elif case_id not in in_scope:
            problems.append(f'{where}: {case_id} is classified {classes.get(case_id, "unclassified")}, not APPLICABLE or PARTLY_COVERED')
    return problems


def cases_without_a_test(found):
    carried = {case_id for _, _, case_id in found if case_id}
    return sorted(in_scope_ids() - carried)


# ------------------------------------------------------------------------------------------------ synthetic destinations
def _h():
    """The route helpers of suites/v1-scenarios (imported on first use; verifies the pinned components before importing them)."""
    here = str(ROOT / 'suites/v1-scenarios')
    if here not in sys.path:
        sys.path.append(here)
    import _d02_d05_d09_helpers as H
    return H


def route_a(work, monkeypatch, *, tenant=None):
    return _h().flow_a(work, monkeypatch, tenant=tenant)


def execute_a(flow, **kwargs):
    return _h().execute_a(flow, **kwargs)


def route_b(work, **kwargs):
    return _h().flow_b(work, **kwargs)


def execute_b(flow, part, **kwargs):
    return _h().execute_b(flow, part, **kwargs)


def route_c(work, monkeypatch):
    return _h().flow_c(work, monkeypatch)


def exchange_run(flow, **extra):
    return _h().exchange_run(flow, **extra)


def exchange_resume(flow):
    return _h().exchange_resume(flow)


def exchange_view(res):
    return _h().exchange_view(res)


def destination_summary(flow):
    """Read-only, timestamp-free view of the destination (separate read-only SQLite connection)."""
    return _h().db_summary(flow.dest.path)


def destination_effects(flow):
    return destination_summary(flow)['effects']


def run_twice(tmp_path, trial):
    """Run ``trial(work_dir, monkeypatch)`` from two fresh work directories and return both observations in order."""
    out = []
    for n in (1, 2):
        work = tmp_path / f'run-{n}'
        work.mkdir()
        mp = pytest.MonkeyPatch()
        try:
            out.append(trial(work, mp))
        finally:
            mp.undo()
    return out
