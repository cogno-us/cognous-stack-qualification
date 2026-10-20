"""Integration: the LangGraph application over the REAL Wiki OPA application, driven through the pinned
runner's `run_case` / `evaluate`.

Only SYNTHETIC cases defined in this file are driven (ids prefixed `synthetic-`; the test below shows none
is a registered corner or baseline id). No registered scenario, no OCS output, no controller. The pinned runner
file is imported by path and its module global ADAPTERS is replaced; no scoring function is copied or edited.
Decision D1 holds: destination only, one profile per run, no mixed scoring.
"""
import hashlib
import json
import pytest
from comparators.wiki.harness import _base
from comparators.wiki.harness.registered_sets import registered_adapters, wiki_adapters_langgraph, wiki_adapters_opa_only
from comparators.wiki.apps.wiki_opa_app import WikiOpaApp, REASON_ORDER
from comparators.wiki.apps import wiki_langgraph_app as G
from comparators.wiki.apps.wiki_langgraph_app import WikiLangGraphOPA

GRAPH_PROFILE = 'langgraph-opa-transactional-application'


@pytest.fixture(scope='module')
def runner():
    r = _base.pinned_runner()
    r.ADAPTERS = wiki_adapters_langgraph()
    return r


def case(**kw):
    base = dict(id='synthetic-accept', steps=[{'action': 'execute'}], expected_statuses=['accepted'],
                expected_effects=1, allowed_effect_ids=['effect'], expected_payload='synthetic')
    base.update(kw)
    return base


def run(runner, tmp_path, opa, c, name='r', mutation=None):
    return runner.run_case(WikiLangGraphOPA, c, tmp_path / name, opa, mutation)


def test_synthetic_ids_are_not_registered():
    g = _base.suite_dir() / 'benchmarks/governance'
    registered = {c['id'] for n in ('corner-plan.json', 'plan.json') for c in json.loads((g / n).read_text())['cases']}
    synthetic = {'synthetic-' + s for s in ('accept', 'deny', 'reject', 'approve', 'timeout', 'outage', 'crash-before',
                                                 'crash-after', 'parallel', 'ablation', 'wrong', 'native-approval')}
    assert not registered & synthetic


# ---- wiring and D1 ------------------------------------------------------------------------
def test_graph_class_subclasses_the_real_application():
    assert issubclass(WikiLangGraphOPA, WikiOpaApp) and WikiLangGraphOPA._base_cls is WikiOpaApp
    assert WikiLangGraphOPA.apply is not WikiOpaApp.apply
    assert WikiLangGraphOPA.request is WikiOpaApp.request          # request construction untouched
    assert WikiLangGraphOPA.profile_id == GRAPH_PROFILE


def test_d1_destination_only_one_profile_per_mapping():
    assert list(wiki_adapters_langgraph()) == [GRAPH_PROFILE]
    assert list(wiki_adapters_opa_only()) == ['opa-transactional-application']
    assert 'cognous-protected-destination' not in wiki_adapters_langgraph()
    assert set(registered_adapters()) == {'cognous-protected-destination', 'opa-transactional-application', GRAPH_PROFILE}


def test_scoring_interface_members_and_signature():
    import inspect
    for m in ('request', 'apply', 'snapshot', 'revoke', 'fence', 'rotate', 'reopen', 'break_audit',
              'require_approval', 'release_approval', 'approve', 'reject', 'timeout', 'record_denial'):
        assert callable(getattr(WikiLangGraphOPA, m)), m
    assert list(inspect.signature(WikiLangGraphOPA.__init__).parameters)[:4] == ['self', 'root', 'opa', 'mutation']


def test_pinned_scoring_code_untouched(runner):
    _base.check_pins()
    assert runner.evaluate.__module__ == 'pinned_run_comparative_governance'
    assert hashlib.sha256((_base.suite_dir() / 'tools/run_comparative_governance.py').read_bytes()).hexdigest().startswith('b0a396b8')


def test_reason_vocabulary_is_shared():
    for reason in list(G.REASON_BY_DECISION.values()) + [G.REASON_PENDING]:
        assert reason in REASON_ORDER, reason


# ---- verdicts through the pinned oracle ---------------------------------------------------
def test_accept_through_graph(runner, tmp_path, opa):
    row = run(runner, tmp_path, opa, case())
    assert row['pass_case'] and row['actual_effects'] == 1


def test_base_denial_through_graph_is_durably_recorded(runner, tmp_path, opa):
    c = case(id='synthetic-deny', steps=[{'action': 'revoke'}, {'action': 'execute'}],
             expected_statuses=['denied'], expected_effects=0)
    row = run(runner, tmp_path, opa, c)
    assert row['pass_case'] and (row['denied_calls'], row['durably_recorded_denials']) == (1, 1)


def test_wrong_expectation_fails(runner, tmp_path, opa):
    c = case(id='synthetic-wrong', steps=[{'action': 'revoke'}, {'action': 'execute'}])
    row = run(runner, tmp_path, opa, c)
    assert not row['pass_case'] and row['false_blocks'] == 1


def test_hold_reject_is_recorded_denial(runner, tmp_path, opa):
    c = case(id='synthetic-reject', steps=[{'action': 'require_approval'}, {'action': 'execute'}, {'action': 'reject'}],
             expected_statuses=['denied'], expected_effects=0)
    row = run(runner, tmp_path, opa, c)
    assert row['pass_case'] and (row['denied_calls'], row['durably_recorded_denials']) == (1, 1)
    reasons = [e['reason'] for e in row['destination']['events']]
    assert reasons == ['APPROVAL_PENDING', 'APPROVAL_REJECTED']


def test_hold_approve_executes_through_real_app(runner, tmp_path, opa):
    c = case(id='synthetic-approve', steps=[{'action': 'require_approval'}, {'action': 'execute'}, {'action': 'approve'}],
             expected_statuses=['denied'], expected_effects=1)
    row = run(runner, tmp_path, opa, c)
    assert row['pass_case'], row
    last = row['destination']['events'][-1]
    assert last['status'] == 'accepted' and last['command_authenticated'] is True   # real app event after resume


def test_hold_timeout_reason_is_the_applications_name(runner, tmp_path, opa):
    c = case(id='synthetic-timeout', steps=[{'action': 'require_approval'}, {'action': 'execute'}, {'action': 'timeout'}],
             expected_statuses=['denied'], expected_effects=0)
    row = run(runner, tmp_path, opa, c)
    assert row['pass_case'] and row['destination']['events'][-1]['reason'] == 'APPROVAL_TIMED_OUT'


def test_audit_outage_is_unavailable(runner, tmp_path, opa):
    c = case(id='synthetic-outage', steps=[{'action': 'break_audit'}, {'action': 'execute'}],
             expected_statuses=['unavailable'], expected_effects=0)
    assert run(runner, tmp_path, opa, c)['pass_case']


def test_crash_before_and_after_commit(runner, tmp_path, opa):
    c = case(id='synthetic-crash-before', steps=[{'action': 'crash_before_commit', 'expected_effects_after': 0},
                                                    {'action': 'execute'}], expected_statuses=['accepted'])
    assert run(runner, tmp_path, opa, c, 'cb')['pass_case']
    c = case(id='synthetic-crash-after', steps=[{'action': 'crash_after_commit', 'expected_effects_after': 1},
                                                   {'action': 'execute'}], expected_statuses=['accepted'], expected_effects=1,
             allowed_effect_ids=['effect'])
    assert run(runner, tmp_path, opa, c, 'ca')['pass_case']


def test_parallel_callers_one_budget(runner, tmp_path, opa):
    c = case(id='synthetic-parallel', steps=[{'action': 'parallel'}], expected_statuses=['accepted', 'denied'],
             expected_effects=1, allowed_effect_ids=['parallel-0', 'parallel-1'])
    row = run(runner, tmp_path, opa, c)
    assert sorted(o['status'] for o in row['outputs']) == ['accepted', 'denied'] and row['actual_effects'] == 1
    assert row['durably_recorded_denials'] == 1 and row['destination_conformance']


def test_native_policy_approval_still_the_applications(runner, tmp_path, opa):
    steps = [{'action': 'execute', 'args': dict(grant='grant-agent', target='purge_record', payload='rec',
                                                issuer_claims={'user': 'user-admin'})}]
    c = case(id='synthetic-native-approval', steps=steps, expected_statuses=['denied'], expected_effects=0)
    row = run(runner, tmp_path, opa, c)
    assert row['pass_case'] and row['outputs'][0]['reason'] == 'APPROVAL_PENDING'
    assert row['destination']['events'][-1]['hold'] is True


# ---- denial-row schema --------------------------------------------------------------------
def test_graph_denial_rows_share_the_applications_event_schema(runner, tmp_path, opa):
    c = case(id='synthetic-reject', steps=[{'action': 'revoke'}, {'action': 'execute'}, {'action': 'require_approval'},
                                               {'action': 'execute', 'args': {'effect': 'e2'}}, {'action': 'reject'}],
             expected_statuses=['denied', 'denied'], expected_effects=0)
    ev = run(runner, tmp_path, opa, c)['destination']['events']
    app_event, pending, rejected = ev[0], ev[1], ev[2]
    # revoke was applied before the hold, so the first execute is the application's own denial row
    assert set(app_event) == set(pending) == set(rejected) == {
        'operation', 'command', 'request_digest', 'status', 'reason', 'at', 'command_authenticated',
        'threshold_alert', 'hold', 'policy_skipped', 'reasons'}
    assert list(app_event) == list(pending) == list(rejected)
    assert (pending['hold'], rejected['hold']) == (True, False)
    assert pending['reasons'] == ['APPROVAL_PENDING'] and rejected['reasons'] == ['APPROVAL_REJECTED']
    assert pending['threshold_alert'] is False and pending['policy_skipped'] is False


def test_record_denial_marks_unauthenticated_and_leaves_state_alone(make):
    a = make()
    r = a.request(); r['signature'] = '00' * 64
    before = a.snapshot()['effects']
    a.record_denial(r, 'APPROVAL_PENDING')
    ev = a.snapshot()['events'][-1]
    assert ev['command_authenticated'] is False and ev['status'] == 'denied' and a.snapshot()['effects'] == before


def test_synthetic_fallback_row_matches_real_app_row(make, tmp_path):
    """The layer's fallback (base without record_denial) writes the same keys as the real record_denial."""
    real = make(); r = real.request(); real.record_denial(r, 'APPROVAL_REJECTED')
    ev = real.snapshot()['events'][-1]
    assert list(G.denial_event(ev['command'], ev['request_digest'], ev['reason'], ev['at'], True)) == list(ev)
    assert G.denial_event(ev['command'], ev['request_digest'], ev['reason'], ev['at'], True) == ev


# ---- ablations ----------------------------------------------------------------------------
def test_graph_ablation_changes_verdict_on_real_app(runner, tmp_path, opa):
    steps = [{'action': 'require_approval'}, {'action': 'execute'}, {'action': 'reject'}]
    c = case(id='synthetic-ablation', steps=steps, expected_statuses=['denied'], expected_effects=0)
    assert not run(runner, tmp_path, opa, c, 'x', 'graph_reject_as_approve')['pass_case']
    assert run(runner, tmp_path, opa, c, 'y')['pass_case']


def test_combined_graph_and_base_mutation_pass_through(tmp_path, opa):
    a = WikiLangGraphOPA(tmp_path / 'm', opa, 'graph_skip_hold+revocation')
    assert a._graph_mutation == 'graph_skip_hold' and a.disabled == ['revocation']
    with pytest.raises(ValueError):
        WikiLangGraphOPA(tmp_path / 'm2', opa, 'graph_skip_hold+graph_bypass_graph')
    with pytest.raises(ValueError):
        WikiLangGraphOPA(tmp_path / 'm3', opa, 'graph_skip_hold+no_such_family')


def test_base_family_removal_visible_through_graph(runner, tmp_path, opa):
    c = case(id='synthetic-deny', steps=[{'action': 'revoke'}, {'action': 'execute'}],
             expected_statuses=['denied'], expected_effects=0)
    assert not run(runner, tmp_path, opa, c, 'z', 'revocation')['pass_case']   # revocation removed => accepted
