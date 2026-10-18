"""Registry checks for the scenario-derived suite, plus one smoke test per synthetic destination route.

SPDX-License-Identifier: Apache-2.0

The registry tests need no pinned reference. The smoke tests need SCN_COMPONENTS_DIR (see README.md) and are skipped, never
passed, when it is not set.
"""
from __future__ import annotations

import pytest

import _wiki_helpers as W


# ------------------------------------------------------------------------------------------------ registry
def test_wiki_marker_ids_exist_in_the_catalog_and_are_in_scope():
    """Every case id carried by a test in this suite is a catalog case classified APPLICABLE or PARTLY_COVERED."""
    problems = W.registry_problems(W.scan_suite())
    assert problems == [], problems


def test_wiki_registry_refuses_unknown_and_out_of_scope_ids_and_accepts_in_scope_ids():
    """Negative and positive controls for the registry check itself."""
    in_scope = sorted(W.in_scope_ids())
    out_of_scope = sorted(W.ids_by_classification('NOT_APPLICABLE'))
    assert in_scope and out_of_scope
    ok = W.scan_source(f'@wiki_case("{in_scope[0]}")\ndef test_x():\n    pass\n', 'ok.py')
    assert W.registry_problems(ok) == []
    unknown = W.scan_source('@wiki_case("TC-ZZZ-999")\ndef test_x():\n    pass\n', 'unknown.py')
    assert any('TC-ZZZ-999' in p for p in W.registry_problems(unknown))
    out = W.scan_source(f'@pytest.mark.wiki_case("{out_of_scope[0]}")\ndef test_x():\n    pass\n', 'out.py')
    assert any(out_of_scope[0] in p for p in W.registry_problems(out))
    dynamic = W.scan_source('@wiki_case(CASE)\ndef test_x():\n    pass\n', 'dynamic.py')
    assert any('literal' in p for p in W.registry_problems(dynamic))


def test_wiki_cases_without_a_test_yet_are_reported_not_failed(record_property):
    """Report only: in-scope case ids that no test in this suite carries yet."""
    missing = W.cases_without_a_test(W.scan_suite())
    record_property('cases_without_test', ' '.join(missing))
    print(f'wiki-derived: {len(missing)} of {len(W.in_scope_ids())} in-scope cases have no test yet')
    assert set(missing) <= W.in_scope_ids()


def test_wiki_applicability_file_is_loaded_with_the_published_counts():
    data = W.load_applicability()
    counts = {}
    for case in data['cases']:
        counts[case['classification']] = counts.get(case['classification'], 0) + 1
    assert counts == data['counts']


# ------------------------------------------------------------------------------------------------ smoke (routes A, B, C)
def test_wiki_smoke_route_a_effective_grant_destination_executes_once(pinned_reference, tmp_path, monkeypatch):
    flow = W.route_a(tmp_path, monkeypatch)
    res, exc = W.execute_a(flow)
    assert exc is None and res.status == 'executed'
    assert len(W.destination_effects(flow)) == 1


def test_wiki_smoke_route_b_atomic_claim_destination_executes_once(pinned_reference, tmp_path):
    flow = W.route_b(tmp_path)
    res, exc = W.execute_b(flow, flow.parts[0])
    assert exc is None and res.status == 'executed'
    assert len(W.destination_effects(flow)) == 1


def test_wiki_smoke_route_c_exchange_destination_executes_once(pinned_reference, tmp_path, monkeypatch):
    flow = W.route_c(tmp_path, monkeypatch)
    res = W.exchange_run(flow)
    assert W.exchange_view(res)['attempt_status'] == 'executed'
    assert len(W.destination_effects(flow)) == 1


def test_wiki_smoke_run_twice_helper_compares_two_fresh_runs(pinned_reference, tmp_path):
    def trial(work, monkeypatch):
        flow = W.route_a(work, monkeypatch)
        res, exc = W.execute_a(flow)
        return {'status': res.status if res else exc, 'effects': len(W.destination_effects(flow))}

    first, second = W.run_twice(tmp_path, trial)
    assert first == second == {'status': 'executed', 'effects': 1}
