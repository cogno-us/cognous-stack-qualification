"""Tests of the extensions of the declared world (DECISIONS.md C-11 to C-17), on synthetic inputs of this file's own.

Each extension is shown on both comparator applications alike (the OPA application and the graph application over it).
No registered corner, baseline or Wiki scenario is executed here and no expected outcome of the plan is consulted: every
test builds its own requests and asserts the rule it names, including the cases in which the extension must NOT change
the answer.
"""
import json
import sqlite3
import pytest
from test_wiki_opa_app import ex, ok, no, effects

PAY = {'path': '/lab/data/a'}
SE = {'recipient': 'a@example.test'}
ADMIN = {'user': 'user-admin'}
STD = {'user': 'user-standard'}


@pytest.fixture(params=['opa', 'graph'])
def build(request, tmp_path, opa):
    from comparators.wiki.apps.wiki_opa_app import WikiOpaApp
    from comparators.wiki.apps.wiki_langgraph_app import WikiLangGraphOPA
    cls = {'opa': WikiOpaApp, 'graph': WikiLangGraphOPA}[request.param]
    count = [0]

    def make(mutation=None):
        count[0] += 1
        return cls(tmp_path / ('a%d' % count[0]), opa, mutation)
    return make


def ctl(app, name): app.__getattr__(name)()


def state(app): return json.loads(sqlite3.connect(app.path).execute('SELECT body FROM state').fetchone()[0])


# ---- C-11: a delegation that cannot expire before the check ---------------------------------------------------
DELEG_PAYLOAD = dict(PAY, data_class='public')


def deleg(a, name, **kw):
    return ex(a, effect=kw.pop('effect', 'd1'), grant='grant-agent', target='read_file', payload=DELEG_PAYLOAD,
              claims={'user': 'user-a', 'delegation_id': name}, **kw)


def test_second_delegation_is_live_long_after_the_first_one_expired(build):
    a = build(); a.now = 700
    no(deleg(a, 'deleg-1'), 'DELEGATION_INVALID')              # deleg-1 expired at 200
    ok(deleg(a, 'deleg-2', effect='d2'))                        # deleg-2 is valid to 10000


def test_revoking_the_second_delegation_denies_it_and_leaves_the_first_alone(build):
    a = build(); a.now = 150; ctl(a, 'revoke_delegation:deleg-2')
    ok(deleg(a, 'deleg-1', effect='d1'))
    no(deleg(a, 'deleg-2', effect='d2'), 'DELEGATION_INVALID')
    b = build(); ctl(b, 'revoke_delegation:deleg-2'); b.now = 700
    r = deleg(b, 'deleg-2'); no(r, 'DELEGATION_INVALID')
    assert state(b)['delegations']['deleg-2']['revoked'] is True and effects(b) == 0


def test_second_delegation_has_the_scope_of_the_first(build):
    a = build(); a.now = 400
    no(ex(a, effect='x1', grant='grant-agent', target='send_email', payload=SE, claims={'user': 'user-a', 'delegation_id': 'deleg-2'}), 'DELEGATION_INVALID')
    no(ex(a, effect='x2', grant='grant-agent', target='read_file', payload=dict(PAY, data_class='secret'),
          claims={'user': 'user-a', 'delegation_id': 'deleg-2'}), 'DELEGATION_INVALID')
    no(ex(a, effect='x3', grant='grant-agent', target='read_file', payload=DELEG_PAYLOAD, claims={'user': 'user-b', 'delegation_id': 'deleg-2'}), 'DELEGATION_INVALID')


# ---- C-12: a budget owner changes a cap -----------------------------------------------------------------------
def key(a, i, k='key-1'): return ex(a, effect='b%d' % i, grant='grant-agent', claims={'hierarchy': {'key': k}})


def test_raised_budget_admits_up_to_the_new_cap_and_keeps_the_usage(build):
    a = build()
    for i in range(1, 4): ok(key(a, i))
    no(key(a, 4), 'BUDGET_LEVEL_EXHAUSTED')
    ctl(a, 'set_budget:key:key-1:5'); a.now = 460
    ok(key(a, 5)); ok(key(a, 6))
    no(key(a, 7), 'BUDGET_LEVEL_EXHAUSTED')
    assert state(a)['budgets']['key']['key-1'] == {'cap': 5, 'used': 5}
    assert state(a)['budgets']['key']['key-2'] == {'cap': 3, 'used': 0}     # other records untouched


def test_lowered_budget_below_the_usage_denies(build):
    a = build(); ok(key(a, 1)); ok(key(a, 2))
    ctl(a, 'set_budget:key:key-1:1')
    no(key(a, 3), 'BUDGET_LEVEL_EXHAUSTED')


def test_budget_control_rejects_unknown_records_and_bad_caps(build):
    a = build()
    for bad in ('set_budget:nolevel:x:5', 'set_budget:key:key-99:5'):
        with pytest.raises(KeyError): ctl(a, bad)
    for bad in ('set_budget:key:key-1:-1', 'set_budget:key:key-1:2.5', 'set_budget:key:key-1:x', 'set_budget:key:key-1:'):
        with pytest.raises(ValueError): ctl(a, bad)
    with pytest.raises(AttributeError): ctl(a, 'set_budget')
    assert state(a)['budgets']['key']['key-1']['cap'] == 3


# ---- C-13: a tool leaves an allow-list ------------------------------------------------------------------------
def test_removed_tool_is_denied_at_once_and_only_for_that_agent_and_tool(build):
    a = build(); ok(ex(a, effect='r0', grant='grant-support', target='send_email', payload=SE))
    ctl(a, 'disallow_tool:support:send_email'); a.now = 101
    no(ex(a, effect='r1', grant='grant-support', target='send_email', payload=SE), 'TOOL_NOT_ALLOWED')
    ok(ex(a, effect='r2', grant='grant-support', target='read_file', payload=PAY))                    # another tool of the same agent
    ok(ex(a, effect='r3', grant='grant-agent', target='send_email', payload=SE))                      # the same tool for another agent
    assert 'send_email' not in state(a)['agents']['support']['allowed_targets']


def test_removed_tool_can_be_added_again_and_leaves_the_read_class(build):
    a = build(); ctl(a, 'disallow_tool:support:read_file')
    assert 'read_file' not in state(a)['agents']['support']['read_targets']
    no(ex(a, effect='r1', grant='grant-support', target='read_file', payload=PAY), 'TOOL_NOT_ALLOWED')
    ctl(a, 'allow_tool:support:read_file'); ok(ex(a, effect='r2', grant='grant-support', target='read_file', payload=PAY))


def test_removal_of_a_tool_that_is_not_listed_or_of_an_unknown_agent_raises(build):
    a = build()
    with pytest.raises(KeyError): ctl(a, 'disallow_tool:support:transfer_test_funds')
    with pytest.raises(KeyError): ctl(a, 'disallow_tool:nobody:read_file')
    ctl(a, 'disallow_tool:support:send_email')
    with pytest.raises(KeyError): ctl(a, 'disallow_tool:support:send_email')      # not a silent second no-op


def test_a_live_exception_is_not_removed_by_the_removal_and_still_applies(build):
    a = build(); ctl(a, 'disallow_tool:support:send_email'); ctl(a, 'grant_exception:support:send_email:300')
    ok(ex(a, effect='r1', grant='grant-support', target='send_email', payload=SE))


# ---- C-14: a token with the read scope only -------------------------------------------------------------------
def test_read_only_token_reads_but_cannot_write(build):
    a = build()
    ok(ex(a, effect='t1', grant='grant-agent-ro', target='list_tickets', payload={'scope': 'read:tickets', 'resource': 'tickets'}))
    no(ex(a, effect='t2', grant='grant-agent-ro', target='list_tickets', payload={'scope': 'write:tickets', 'resource': 'tickets'}), 'SCOPE_NOT_GRANTED')
    ok(ex(a, effect='t3', grant='grant-agent', target='list_tickets', payload={'scope': 'write:tickets', 'resource': 'tickets'}))   # the ordinary grant is unchanged
    assert effects(a) == 2
    assert state(a)['grants']['grant-agent-ro']['scopes'] == ['read:tickets'] and state(a)['grants']['grant-agent-ro']['agent'] == 'agent'


def test_read_only_token_is_an_ordinary_grant_in_every_other_respect(build):
    a = build()
    ctl(a, 'revoke_grant:grant-agent-ro')
    no(ex(a, effect='t1', grant='grant-agent-ro', target='list_tickets', payload={'scope': 'read:tickets', 'resource': 'tickets'}), 'CREDENTIAL_BINDING_CLOSED')
    ok(ex(a, effect='t2', grant='grant-agent', target='sink'))                                         # revoking it does not touch the other grants
    b = build(); b.now = 900                                                                            # live late in the clock range, like the per-agent grants
    ok(ex(b, effect='t3', grant='grant-agent-ro', target='sink'))
    assert state(b)['grants']['grant-agent-ro']['expires_at'] == state(b)['grants']['grant-agent']['expires_at'] == 10000


# ---- C-15: the destination is a non-production deployment -----------------------------------------------------
def test_prod_token_is_denied_at_a_non_prod_destination_and_accepted_again_at_prod(build):
    a = build(); ok(ex(a, effect='n0', grant='grant-agent', claims={'environment': 'prod'}))
    ctl(a, 'set_environment:non-prod')
    no(ex(a, effect='n1', grant='grant-agent', claims={'environment': 'prod'}), 'ENVIRONMENT_MISMATCH')
    no(ex(a, effect='n2', grant='grant-agent'), 'ENVIRONMENT_MISMATCH')                                  # the grant itself is a prod token
    ctl(a, 'set_environment:prod')
    ok(ex(a, effect='n3', grant='grant-agent', claims={'environment': 'prod'}))
    assert effects(a) == 2


def test_non_prod_token_is_still_denied_at_prod_and_bad_environment_names_raise(build):
    a = build(); no(ex(a, effect='n1', grant='grant-agent', claims={'environment': 'non-prod'}), 'ENVIRONMENT_MISMATCH')
    for bad in ('set_environment:staging', 'set_environment:'):
        with pytest.raises(KeyError): ctl(a, bad)
    assert state(a)['environment'] == 'prod'


# ---- C-16: the tools that the user's request requires ---------------------------------------------------------
def task(a, tool, tools, effect, payload=None, **more):
    return ex(a, effect=effect, grant='grant-agent', target=tool, payload=payload or dict(SE, **PAY),
              claims=dict(ADMIN, task_tools=tools), **more)


def test_empty_task_record_warrants_no_tool(build):
    a = build()
    for i, t in enumerate(('send_email', 'delete_record', 'read_file')): no(task(a, t, [], 'k%d' % i), 'TASK_TOOL_NOT_WARRANTED')
    assert effects(a) == 0


def test_task_record_warrants_exactly_its_tools(build):
    a = build()
    for i, t in enumerate(('send_email', 'delete_record', 'read_file')): ok(task(a, t, [t], 'w%d' % i))
    assert effects(a) == 3
    no(task(a, 'read_file', ['send_email'], 'w9'), 'TASK_TOOL_NOT_WARRANTED')
    ok(task(a, 'read_file', ['send_email', 'read_file'], 'w10'))


def test_no_task_record_means_no_task_limit(build):
    a = build(); ok(ex(a, effect='n1', grant='grant-agent', target='read_file', payload=PAY, claims=ADMIN))


def test_malformed_task_record_is_a_claims_error_not_a_limit_or_a_pass(build):
    a = build()
    for i, bad in enumerate(('read_file', {'read_file': True}, [1], ['read_file', None], None)):
        r = ex(a, effect='m%d' % i, grant='grant-agent', target='read_file', payload=PAY, claims=dict(ADMIN, task_tools=bad))
        assert r['status'] == 'denied' and r['reason'] == 'CLAIMS_INVALID', (bad, r)


def test_task_record_does_not_open_anything_else(build):
    a = build()
    no(task(a, 'send_email', ['send_email'], 'o1', payload={'recipient': 'a@outside.test'}), 'PARAMETER_RULE_VIOLATION')
    no(ex(a, effect='o2', grant='grant-support', target='transfer_test_funds', payload={'amount': 5}, claims=dict(ADMIN, task_tools=['transfer_test_funds'])), 'TOOL_NOT_ALLOWED')
    no(ex(a, effect='o3', grant='grant-agent', target='delete_record', payload='x', claims={'user': 'user-standard', 'task_tools': ['delete_record']}), 'USER_NOT_ENTITLED')
    a.__getattr__('grant_exception:agent:elevated_task:300')()
    no(task(a, 'elevated_task', [], 'o4', payload='x'), 'TASK_TOOL_NOT_WARRANTED')     # an exception record does not warrant a tool


def test_task_scope_family_can_be_switched_off_alone(build):
    a = build('task_scope'); ok(task(a, 'read_file', [], 'f1'))
    b = build('revocation'); no(task(b, 'read_file', [], 'f1'), 'TASK_TOOL_NOT_WARRANTED')


# ---- C-17: the parameter envelope shared by the four mock tools ------------------------------------------------
ENV = {'recipient': 'a@example.test', 'amount': 50, 'path': '/lab/data/a', 'records': 5}
TOOLS4 = (('send_email', None), ('transfer_test_funds', STD), ('read_file', None), ('update_records', STD))


def test_one_payload_is_accepted_by_all_four_tools_with_one_stored_effect_payload(build):
    a = build()
    for i, (t, c) in enumerate(TOOLS4): ok(ex(a, effect='v%d' % i, grant='grant-agent', target=t, payload=ENV, claims=c))
    payloads = {e['payload'] for e in a.snapshot()['effects']}
    assert effects(a) == 4 and len(payloads) == 1 and json.loads(payloads.pop()) == ENV


def test_each_tool_still_requires_its_own_parameter_and_rejects_unknown_keys(build):
    a = build(); n = iter(range(100))
    for t, c in TOOLS4:
        own = {'send_email': 'recipient', 'transfer_test_funds': 'amount', 'read_file': 'path', 'update_records': 'records'}[t]
        without = {k: v for k, v in ENV.items() if k != own}
        no(ex(a, effect='m%d' % next(n), grant='grant-agent', target=t, payload=without, claims=c), 'SCHEMA_VIOLATION')
        no(ex(a, effect='m%d' % next(n), grant='grant-agent', target=t, payload=dict(ENV, unknown=1), claims=c), 'SCHEMA_VIOLATION')
        no(ex(a, effect='m%d' % next(n), grant='grant-agent', target=t, payload='text', claims=c), 'SCHEMA_VIOLATION')
    assert effects(a) == 0


def test_envelope_keys_are_checked_by_type_and_by_parameter_rule_on_every_tool(build):
    a = build(); n = iter(range(100))
    for t, c in TOOLS4:
        no(ex(a, effect='t%d' % next(n), grant='grant-agent', target=t, payload=dict(ENV, amount='50'), claims=c), 'SCHEMA_VIOLATION')
        no(ex(a, effect='t%d' % next(n), grant='grant-agent', target=t, payload=dict(ENV, records='5'), claims=c), 'SCHEMA_VIOLATION')
        no(ex(a, effect='t%d' % next(n), grant='grant-agent', target=t, payload=dict(ENV, recipient='a@outside.test'), claims=c), 'PARAMETER_RULE_VIOLATION')
        no(ex(a, effect='t%d' % next(n), grant='grant-agent', target=t, payload=dict(ENV, path='/etc/passwd'), claims=c), 'PARAMETER_RULE_VIOLATION')
        no(ex(a, effect='t%d' % next(n), grant='grant-agent', target=t, payload=dict(ENV, amount=150), claims=c), 'PARAMETER_RULE_VIOLATION')
        no(ex(a, effect='t%d' % next(n), grant='grant-agent', target=t, payload=dict(ENV, records=11), claims=c), 'PARAMETER_RULE_VIOLATION')
    assert effects(a) == 0


def test_envelope_does_not_give_a_tool_without_a_schema_or_a_new_key_any_new_meaning(build):
    a = build()
    ok(ex(a, effect='s1', grant='grant-agent', target='delete_record', payload=dict(SE, **PAY), claims=ADMIN))     # no schema: unchanged
    no(ex(a, effect='s2', grant='grant-agent', target='delete_record', payload=dict(SE, path='/etc/x'), claims=ADMIN), 'PARAMETER_RULE_VIOLATION')
    no(ex(a, effect='s3', grant='grant-agent', target='send_email', payload=dict(SE, other='x')), 'SCHEMA_VIOLATION')
