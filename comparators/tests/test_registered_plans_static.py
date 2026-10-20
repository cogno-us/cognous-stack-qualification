"""Static checks of the registered corner and baseline plans against the OPA applications.

Reads the two plan files as inputs; executes no scenario of either plan. Confirms the destination-only
wiring covers every step action the plans use, so the registered OPA application is reused unchanged.
"""
import hashlib
import json
import inspect
from comparators.wiki.harness import _base
from comparators.wiki.harness.registered_sets import registered_adapters
from comparators.wiki.apps.wiki_opa_app import WikiOpaApp

RUNNER_ACTIONS = {'execute', 'capture', 'alter_captured', 'submit', 'clock', 'parallel',
                  'crash_before_commit', 'crash_after_commit'}


def plans():
    g = _base.suite_dir() / 'benchmarks/governance'
    return {n: json.loads((g / n).read_text()) for n in ('corner-plan.json', 'plan.json')}


def test_counts_and_profiles():
    p = plans()
    assert len(p['corner-plan.json']['cases']) == 19 and len(p['plan.json']['cases']) == 24
    assert p['corner-plan.json']['repetitions'] == 5 and p['plan.json']['repetitions'] == 10
    for plan in p.values():
        assert plan['profiles'] == list(registered_adapters())
        assert plan['seeds'] == [1701, 1702] or 'seeds' not in plan


def test_plan_digests_have_the_planned_prefixes():
    g = _base.suite_dir() / 'benchmarks/governance'
    assert hashlib.sha256((g / 'corner-plan.json').read_bytes()).hexdigest().startswith('35ca4ee5')
    assert hashlib.sha256((g / 'plan.json').read_bytes()).hexdigest().startswith('47f28898')


def test_every_step_action_is_supported_by_both_opa_applications():
    classes = [registered_adapters()['opa-transactional-application'], WikiOpaApp]
    for plan in plans().values():
        for case in plan['cases']:
            for step in case['steps']:
                a = step['action']
                if a in RUNNER_ACTIONS: continue
                for cls in classes:
                    assert callable(getattr(cls, a, None)), (case['id'], a, cls.__name__)


def test_every_fault_in_the_plans_is_known_to_the_wiki_application():
    from comparators.wiki.apps.wiki_opa_app import KNOWN_FAULTS
    for plan in plans().values():
        for case in plan['cases']:
            for step in case['steps']:
                assert step.get('fault') in KNOWN_FAULTS, (case['id'], step.get('fault'))


def test_registered_opa_application_is_not_subclass_modified():
    cls = registered_adapters()['opa-transactional-application']
    assert cls.__module__.endswith('adapters') and 'Wiki' not in cls.__name__
    assert inspect.getsource(cls).count('class Conventional') == 1
