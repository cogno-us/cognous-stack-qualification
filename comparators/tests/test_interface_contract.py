"""Interface contract of the Wiki OPA application against the pinned scoring code.

Only cases defined in this file are driven (synthetic ids, not any registered corner, baseline or Wiki
scenario). The pinned runner file is imported by path and its module global ADAPTERS is replaced; none of
its scoring functions is copied or edited.
"""
import inspect
import pytest
from comparators.wiki.harness import _base
from comparators.wiki.harness.registered_sets import registered_adapters, wiki_adapters_opa_only
from comparators.wiki.apps.wiki_opa_app import WikiOpaApp, PROFILE_ID


@pytest.fixture(scope='module')
def runner():
    r = _base.pinned_runner()
    r.ADAPTERS = wiki_adapters_opa_only()      # the loader mechanism of the plan, section 3.3
    return r


def case(**kw):
    base = dict(id='synthetic', steps=[{'action': 'execute'}], expected_statuses=['accepted'], expected_effects=1,
                allowed_effect_ids=['effect'], expected_payload='synthetic')
    base.update(kw); return base


def run(runner, tmp_path, opa, c, name='r'):
    return runner.run_case(WikiOpaApp, c, tmp_path / name, opa)


def test_pins_are_the_planned_digests():
    _base.check_pins()


def test_registered_profile_ids_unchanged():
    assert set(registered_adapters()) == {'cognous-protected-destination', 'opa-transactional-application',
                                          'langgraph-opa-transactional-application'}
    assert PROFILE_ID == 'opa-transactional-application'


def test_required_members_exist():
    for m in ('request', 'apply', 'snapshot', 'revoke', 'fence', 'rotate', 'reopen', 'break_audit'):
        assert callable(getattr(WikiOpaApp, m)), m
    sig = inspect.signature(WikiOpaApp.__init__)
    assert list(sig.parameters)[:4] == ['self', 'root', 'opa', 'mutation']


def test_accept_and_deny_verdicts_through_the_pinned_oracle(runner, tmp_path, opa):
    assert run(runner, tmp_path, opa, case(), 'a')['pass_case']
    denied = case(id='s2', steps=[{'action': 'revoke'}, {'action': 'execute'}], expected_statuses=['denied'], expected_effects=0)
    r = run(runner, tmp_path, opa, denied, 'b'); assert r['pass_case'] and r['durably_recorded_denials'] == 1
    wrong = case(id='s3', steps=[{'action': 'revoke'}, {'action': 'execute'}])      # wrong expectation must fail
    r = run(runner, tmp_path, opa, wrong, 'c'); assert not r['pass_case'] and r['false_blocks'] == 1


def test_capture_alter_submit_path(runner, tmp_path, opa):
    c = case(id='s4', steps=[{'action': 'capture'}, {'action': 'alter_captured', 'args': {'payload': 'tampered'}, 'resign': False},
                             {'action': 'submit'}], expected_statuses=['denied'], expected_effects=0)
    assert run(runner, tmp_path, opa, c, 'd')['pass_case']


def test_audit_failure_maps_to_unavailable(runner, tmp_path, opa):
    c = case(id='s5', steps=[{'action': 'break_audit'}, {'action': 'execute'}], expected_statuses=['unavailable'], expected_effects=0)
    assert run(runner, tmp_path, opa, c, 'e')['pass_case']


def test_concurrency_through_the_runner(runner, tmp_path, opa):
    c = case(id='concurrent_last_budget', steps=[{'action': 'parallel'}], expected_statuses=['accepted', 'denied'],
             expected_effects=1, allowed_effect_ids=['parallel-0', 'parallel-1'])
    assert run(runner, tmp_path, opa, c, 'f')['pass_case']


def test_crash_before_and_after_commit(runner, tmp_path, opa):
    before = case(id='s6', steps=[{'action': 'crash_before_commit', 'expected_effects_after': 0}, {'action': 'execute'}])
    r = run(runner, tmp_path, opa, before, 'g'); assert r['pass_case'] and r['injected_faults'][0]['effects_after_crash'] == 0
    after = case(id='s7', steps=[{'action': 'crash_after_commit', 'expected_effects_after': 1}, {'action': 'execute'}])
    r = run(runner, tmp_path, opa, after, 'h'); assert r['pass_case'] and r['injected_faults'][0]['effects_after_crash'] == 1


def test_dynamic_controls_work_as_runner_steps(runner, tmp_path, opa):
    c = case(id='s8', steps=[{'action': 'stop:agent'}, {'action': 'execute'}], expected_statuses=['denied'], expected_effects=0)
    assert run(runner, tmp_path, opa, c, 'i')['pass_case']
    bad = case(id='s9', steps=[{'action': 'stop:nobody'}, {'action': 'execute'}])
    with pytest.raises(KeyError): run(runner, tmp_path, opa, bad, 'j')
    bad = case(id='s10', steps=[{'action': 'nonsense:x'}])
    with pytest.raises(AttributeError): run(runner, tmp_path, opa, bad, 'k')


def test_wiki_plan_extra_keys_are_ignored_by_the_oracle(runner, tmp_path, opa):
    c = case(wiki_case_id='x', source='from case text', config_status={'a': 'ask'}, authors=['r'])
    assert run(runner, tmp_path, opa, c, 'l')['pass_case']


def test_mutation_slot_reuses_registered_semantics(runner, tmp_path, opa):
    c = case(id='s11', steps=[{'action': 'revoke'}, {'action': 'execute'}], expected_statuses=['denied'], expected_effects=0)
    r = runner.run_case(WikiOpaApp, c, tmp_path / 'm', opa, 'revocation')
    assert not r['pass_case']            # control removed -> detected, as the registered probes are
