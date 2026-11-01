"""Unit tests of the Wiki OPA application on synthetic inputs of this file's own.

No registered corner, baseline or Wiki scenario is executed here. Each test
builds its own requests and asserts the rule it names, so the rule logic is shown
active and the tests do not encode how any other configuration behaves.
"""
import json
import pytest


def ex(app, effect='e1', grant='grant', target='sink', payload='synthetic', claims=None, fault=None, **more):
    changes = dict(grant=grant, effect=effect, target=target, payload=payload, issuer_claims=claims or {})
    changes.update(more)
    out = app.apply(app.request(changes, fault))
    out['all'] = app.snapshot()['events'][-1]['reasons']   # every reason the policy returned
    return out


def ok(r): assert r['status'] == 'accepted', r
def no(r, reason):
    """Denied, and the named rule is among the reasons returned (several rules may fire on one request)."""
    assert r['status'] == 'denied' and reason in r['all'], r


def effects(app): return len(app.snapshot()['effects'])


# ---- base lifecycle ---------------------------------------------------------
def test_default_accept_and_duplicate_is_one_effect(make):
    a = make(); ok(ex(a)); r = ex(a); ok(r); assert r['result']['duplicate'] and effects(a) == 1


def test_conflicting_redelivery(make):
    a = make(); ok(ex(a)); no(ex(a, payload='other'), 'EFFECT_ID_CONFLICT'); assert effects(a) == 1


def test_revoke_budget_expiry_fence_rotate(make):
    a = make(); a.revoke(); no(ex(a), 'CREDENTIAL_BINDING_CLOSED')
    a = make(); ok(ex(a)); no(ex(a, effect='e2'), 'CREDENTIAL_BINDING_CLOSED')
    a = make(); a.now = 200; no(ex(a), 'CREDENTIAL_EXPIRED')
    a = make(); a.fence(); no(ex(a), 'BINDING_DENIED')
    a = make(); a.rotate(); no(ex(a), 'CREDENTIAL_PIN_CHANGED')
    a = make(); no(ex(a, policy='other'), 'BINDING_DENIED'); no(ex(a, grant='missing', effect='x'), 'BINDING_DENIED')


def test_verifier_and_auth_faults(make):
    a = make(); no(ex(a, fault='missing_verifier'), 'VERIFIER_INVALID')
    a = make(); no(ex(a, fault='stale_verifier'), 'VERIFIER_INVALID')
    a = make(); no(ex(a, fault='forged_signature'), 'AUTHENTICATION_DENIED')
    a = make(); no(ex(a, fault='wrong_actor'), 'AUTHENTICATION_DENIED')
    assert effects(a) == 0
    ev = a.snapshot()['events'][-1]; assert ev['command_authenticated'] is False and ev['reason']


def test_unknown_fault_and_unknown_controls_raise(make):
    a = make()
    with pytest.raises(ValueError): a.request({}, 'no_such_fault')
    with pytest.raises(AttributeError): getattr(a, 'no_such_verb:x')()
    with pytest.raises(AttributeError): getattr(a, 'plainmissing')
    with pytest.raises(KeyError): a.__getattr__('stop:nobody')()
    with pytest.raises(ValueError): make('not_a_family')


def test_clock_regression_denied(make):
    a = make(); a.now = 150; ok(ex(a, grant='grant-agent'))
    a.now = 120; no(ex(a, effect='e2', grant='grant-agent'), 'CLOCK_REGRESSION')


def test_audit_outage_aborts_whole_transaction(make):
    import sqlite3
    a = make(); a.break_audit()
    with pytest.raises(sqlite3.IntegrityError, match='synthetic audit outage'): ex(a)
    assert effects(a) == 0
    ok_state = json.loads(sqlite3.connect(a.path).execute('SELECT body FROM state').fetchone()[0])
    assert ok_state['grants']['grant']['consumed'] == 0


# ---- stop, allow-lists, definitions, names ------------------------------------
def test_stop_one_agent_only_and_persists(make):
    a = make(); ok(ex(a, grant='grant-support', target='read_file', payload={'path': '/lab/data/a'}))
    a.__getattr__('stop:support')()
    no(ex(a, effect='e2', grant='grant-support', target='read_file', payload={'path': '/lab/data/a'}), 'AGENT_STOPPED')
    ok(ex(a, effect='e3', grant='grant-finance', target='read_file', payload={'path': '/lab/data/a'}))
    a.reopen(); no(ex(a, effect='e4', grant='grant-support', target='read_file', payload={'path': '/lab/data/a'}), 'AGENT_STOPPED')


def test_allow_list_per_agent(make):
    a = make(); user = {'user': 'user-admin'}
    no(ex(a, grant='grant-support', target='transfer_test_funds', payload={'amount': 5}, claims=user), 'TOOL_NOT_ALLOWED')
    ok(ex(a, effect='e2', grant='grant-finance', target='transfer_test_funds', payload={'amount': 5}, claims=user))
    no(ex(a, effect='e3', grant='grant-finance', target='unregistered_tool', payload='x'), 'TOOL_NOT_REGISTERED')


def test_rug_pull_blocks_until_reapproved(make):
    for field in ('description', 'new_parameter', 'rename', 'scope'):
        a = make(); a.__getattr__(f'mutate_tool:sink:{field}')()
        no(ex(a), 'TOOL_DEFINITION_CHANGED')
        a.__getattr__('reapprove_tool:sink')(); ok(ex(a, effect='e2', grant='grant-agent'))
    a = make(); a.__getattr__('add_tool:server-2:brand_new')(); a.__getattr__('allow_tool:agent:brand_new')()
    a.__getattr__('pend_tool:brand_new')(); no(ex(a, target='brand_new'), 'TOOL_DEFINITION_CHANGED')


def test_name_collisions(make):
    a = make()
    from comparators.wiki.apps import wiki_config as W
    assert W.normalise_name('sеnd_email') == W.normalise_name('send_email') == W.normalise_name('ns/SEND_EMAIL')
    for key, name in (('server-2/send_email', 'send_email'), ('Send_Email', 'Send_Email')):
        a.__getattr__(f'add_tool:server-2:{name}')()
        a.__getattr__(f'allow_tool:agent:{key}')()
    for i, key in enumerate(('server-2/send_email', 'Send_Email')):
        no(ex(a, effect=f'c{i}', grant='grant-agent', target=key, payload={'recipient': 'a@example.test'}), 'TOOL_NAME_COLLISION')
    ok(ex(a, effect='t', grant='grant-agent', target='send_email', payload={'recipient': 'a@example.test'}))


def test_qualified_name_requirement_when_configured(make):
    a = make(); a.cfg['require_qualified_names'] = True
    no(ex(a, grant='grant-agent'), 'TOOL_NAME_COLLISION')


def test_exception_and_elevation_expire(make):
    a = make(); no(ex(a, grant='grant-agent', target='elevated_task'), 'PRIVILEGE_ELEVATION_REQUIRED')
    a.__getattr__('grant_exception:agent:elevated_task:15')()
    ok(ex(a, effect='e2', grant='grant-agent', target='elevated_task'))
    a.now = 115; no(ex(a, effect='e3', grant='grant-agent', target='elevated_task'), 'PRIVILEGE_ELEVATION_REQUIRED')
    # an exception also opens a tool outside the allow-list, only until it expires
    b = make(); no(ex(b, grant='grant-research', target='update_records', payload={'records': 1}, claims={'user': 'user-admin'}), 'TOOL_NOT_ALLOWED')
    b.__getattr__('grant_exception:research:update_records:50')()
    no(ex(b, effect='e2', grant='grant-research', target='update_records', payload={'records': 1, 'operation': 'write'}, claims={'user': 'user-admin'}), 'OPERATION_NOT_PERMITTED')


def test_never_via_agent(make):
    a = make()
    for t in ('edit_roles', 'read_credentials', 'create_agent'):
        no(ex(a, effect=t, grant='grant-agent', target=t, claims={'user': 'user-admin'}), 'ESCALATION_BLOCKED')
    a.__getattr__('grant_exception:agent:edit_roles:50')()
    no(ex(a, effect='x', grant='grant-agent', target='edit_roles', claims={'user': 'user-admin'}), 'ESCALATION_BLOCKED')


def test_agent_change_control(make):
    a = make(); a.__getattr__('change_agent:agent-c:owner')()
    ok(ex(a, grant='grant-agent-c', target='update_records', payload={'records': 1}, claims={'user': 'user-admin'}))
    for i, comp in enumerate(('model', 'prompt', 'tool', 'data_scope')):
        b = make(); b.__getattr__(f'change_agent:agent-c:{comp}')()
        no(ex(b, grant='grant-agent-c', target='update_records', payload={'records': 1}, claims={'user': 'user-admin'}), 'AGENT_PENDING_REAPPROVAL')
        ok(ex(b, effect='r', grant='grant-agent-c', target='read_file', payload={'path': '/lab/data/x'}))
        b.__getattr__('reapprove_agent:agent-c')()
        ok(ex(b, effect='u', grant='grant-agent-c', target='update_records', payload={'records': 1}, claims={'user': 'user-admin'}))


# ---- environment, scope, users, delegation --------------------------------------
def test_environment_boundary(make):
    a = make(); no(ex(a, claims={'environment': 'nonprod'}), 'ENVIRONMENT_MISMATCH')
    ok(ex(a, effect='e2', claims={'environment': 'prod'}))
    b = make(); b.mutate(lambda s: s['grants']['grant'].update(environment='nonprod')); no(ex(b), 'ENVIRONMENT_MISMATCH')


def test_scope_and_resource(make):
    a = make()
    ok(ex(a, grant='grant-agent', payload={'scope': 'read:tickets', 'resource': 'tickets'}))
    no(ex(a, effect='2', grant='grant-agent', payload={'scope': 'read:tickets', 'resource': 'payroll'}), 'SCOPE_NOT_GRANTED')
    no(ex(a, effect='3', grant='grant-agent', payload={'scope': 'read:*', 'resource': 'tickets'}), 'SCOPE_NOT_GRANTED')
    no(ex(a, effect='4', grant='grant-agent', payload={'scope': 'read:tickets', 'resource': 'tickets2'}), 'SCOPE_NOT_GRANTED')
    no(ex(a, effect='5', grant='grant-agent', payload={'resource': 'tickets'}), 'SCOPE_NOT_GRANTED')


def test_users_and_identity(make):
    a = make(); std = {'user': 'user-standard'}
    no(ex(a, grant='grant-agent', target='delete_record', claims=std, payload='x'), 'USER_NOT_ENTITLED')
    no(ex(a, effect='2', grant='grant-agent', target='delete_record', payload='x'), 'USER_REQUIRED')
    ok(ex(a, effect='3', grant='grant-agent', target='delete_record', claims={'user': 'user-admin'}, payload='x'))
    no(ex(a, effect='4', grant='grant-agent', claims={'user': 'ghost'}), 'USER_NOT_ENTITLED')
    no(ex(a, effect='5', grant='grant-agent', claims=std, payload={'user': 'user-admin'}), 'IDENTITY_SUBSTITUTION')
    no(ex(a, effect='6', grant='grant-agent', claims={'user': 'user-a', 'agent': 'finance'}), 'IDENTITY_SUBSTITUTION')
    no(ex(a, effect='7', grant='grant-agent', claims=std, payload={'data_owner': 'user-b'}), 'CROSS_USER_DATA')
    no(ex(a, effect='8', grant='grant-agent', claims={'task_expires_at': 100}), 'TASK_EXPIRED')
    no(ex(a, effect='9', grant='grant-agent', claims='not-a-dict'), 'CLAIMS_INVALID')


def test_delegation_records_and_leavers(make):
    a = make(); c = {'user': 'user-a', 'delegation_id': 'deleg-1'}; p = {'path': '/lab/data/a', 'data_class': 'public'}
    ok(ex(a, grant='grant-agent', target='read_file', claims=c, payload=p))
    no(ex(a, effect='2', grant='grant-agent', target='read_file', claims=c, payload=dict(p, data_class='secret')), 'DELEGATION_INVALID')
    no(ex(a, effect='3', grant='grant-agent', target='send_email', claims=c, payload={'recipient': 'a@example.test'}), 'DELEGATION_INVALID')
    no(ex(a, effect='4', grant='grant-agent', target='read_file', claims={'user': 'user-b', 'delegation_id': 'deleg-1'}, payload=p), 'DELEGATION_INVALID')
    no(ex(a, effect='5', grant='grant-agent', target='read_file', claims={'user': 'user-a', 'delegation_id': 'nope'}, payload=p), 'DELEGATION_INVALID')
    b = make(); b.__getattr__('remove_user:user-a')()
    assert ex(b, grant='grant-agent', target='read_file', claims=c, payload=p)['status'] == 'denied'
    d = make(); d.__getattr__('revoke_delegation:deleg-1')()
    no(ex(d, grant='grant-agent', target='read_file', claims=c, payload=p), 'DELEGATION_INVALID')
    d.now = 200; no(ex(d, effect='9', grant='grant-agent', target='read_file', claims=c, payload=p), 'DELEGATION_INVALID')


def test_delegation_chain(make):
    a = make(); p = {'path': '/lab/data/a'}; seq = iter(range(1000))
    def chain(*ids, target='read_file', grant=None, payload=p, effect=None):
        return ex(a, effect=effect or 'c%d' % next(seq), grant=grant or 'grant-' + ids[-1], target=target,
                  payload=payload, claims={'chain': list(ids), 'user': 'user-admin'})
    ok(chain('parent', 'child-1'))
    no(chain('parent', 'child-2', target='read_file'), 'DELEGATION_WIDENING')       # child-2 holds update_records only
    no(chain('parent', 'child-1', target='update_records', payload={'records': 1}), 'DELEGATION_WIDENING')
    no(chain('parent', 'child-1', 'child-3', 'agent-b'), 'DELEGATION_DEPTH')
    no(chain('parent', 'child-1', 'parent', 'child-1'), 'DELEGATION_DEPTH')
    no(chain('child-1', 'parent', 'child-1', effect='cyc'), 'DELEGATION_CYCLE')
    no(chain('parent', 'child-3', grant='grant-child-1', effect='tail'), 'DELEGATION_CHAIN_INVALID')
    no(chain('parent', 'ghost', grant='grant-parent', effect='unk'), 'DELEGATION_CHAIN_INVALID')
    a.__getattr__('stop:parent')()
    no(chain('parent', 'child-1', effect='mid'), 'DELEGATION_CHAIN_INVALID')


def test_inter_agent_operations(make):
    a = make(); c = {'user': 'user-a'}
    ok(ex(a, grant='grant-research', target='read_file', claims=c, payload={'path': '/lab/data/a', 'operation': 'read', 'data_owner': 'user-a'}))
    no(ex(a, effect='2', grant='grant-research', target='read_file', claims=c, payload={'path': '/lab/data/a', 'operation': 'write'}), 'OPERATION_NOT_PERMITTED')
    no(ex(a, effect='3', grant='grant-research', target='read_file', claims=c, payload={'path': '/lab/data/a', 'data_owner': 'user-b'}), 'CROSS_USER_DATA')
    no(ex(a, effect='4', grant='grant-research', target='update_records', claims=c, payload={'records': 1}), 'TOOL_NOT_ALLOWED')


# ---- arguments ------------------------------------------------------------------
@pytest.mark.parametrize('recipient,good', [('a@example.test', True), ('a@corp.test', True), ('a@evil.test', False),
    ('a@example.test.evil.test', False), ('*@example.test', False), ('a@example.test,b@evil.test', False),
    ('A@EXAMPLE.TEST', False), ('a@@example.test', False), ('', False),
    (5, False), (['a@example.test'], False), ('a@example.test ', False)])
def test_recipient_rule(make, recipient, good):
    r = ex(make(), grant='grant-support', target='send_email', payload={'recipient': recipient},
           )
    assert (r['status'] == 'accepted') is good, r


@pytest.mark.parametrize('amount,good', [(1, True), (100, True), (0, False), (-5, False),
    ('50', False), (True, False), (None, False), ([50], False)])
def test_amount_rule(make, amount, good):
    r = ex(make(), grant='grant-finance', target='transfer_test_funds', payload={'amount': amount}, claims={'user': 'user-admin'})
    assert (r['status'] == 'accepted') is good, r


@pytest.mark.parametrize('path,good', [('/lab/data/a.txt', True), ('/lab/public/x/y', True), ('/lab/data/../secret', False),
    ('/lab/data/..', False), ('/lab/database/x', False), ('/etc/passwd', False), ('lab/data/a', False),
    ('/lab/data//a', False), ('/lab/data/./a', False), ('/lab/data/%2e%2e/a', False), ('/lab/data/\\a', False),
    ('/lab/data/a\x00', False), ('', False), (3, False)])
def test_path_rule(make, path, good):
    r = ex(make(), grant='grant-helpdesk', target='read_file', payload={'path': path})
    assert (r['status'] == 'accepted') is good, r


@pytest.mark.parametrize('n,good', [(1, True), (10, True), (11, False), (0, False), ('3', False), (True, False)])
def test_record_count_rule(make, n, good):
    r = ex(make(), grant='grant-helpdesk', target='update_records', payload={'records': n}, claims={'user': 'user-standard'})
    assert (r['status'] == 'accepted') is good, r


def test_schema_shape(make):
    a = make(); c = {'user': 'user-standard'}
    no(ex(a, grant='grant-helpdesk', target='update_records', payload={'records': 1, 'extra': 1}, claims=c), 'SCHEMA_VIOLATION')
    no(ex(a, effect='2', grant='grant-helpdesk', target='update_records', payload={}, claims=c), 'SCHEMA_VIOLATION')
    no(ex(a, effect='3', grant='grant-helpdesk', target='update_records', payload='records=1', claims=c), 'SCHEMA_VIOLATION')
    no(ex(a, effect='4', grant='grant-helpdesk', target='read_file', payload={'path': 7}, claims=c), 'SCHEMA_VIOLATION')


def test_nested_json_argument_is_not_a_bypass(make):
    a = make()
    no(ex(a, grant='grant-finance', target='transfer_test_funds', payload={'amount': {'value': 5}}, claims={'user': 'user-admin'}), 'SCHEMA_VIOLATION')
    no(ex(a, effect='2', grant='grant-helpdesk', target='read_file', payload={'path': {'p': '/lab/data/a'}}), 'SCHEMA_VIOLATION')


# ---- caps and budgets ---------------------------------------------------------------
def test_window_cap_alert_reset_and_isolation(make):
    a = make(); a.cfg['windows']['send_email']['seconds'] = 300   # scaled: the shared fixture's keys end at t=1000
    for i in range(5): ok(ex(a, effect=f'm{i}', grant='grant-support', target='send_email', payload={'recipient': 'a@example.test'}))
    no(ex(a, effect='m5', grant='grant-support', target='send_email', payload={'recipient': 'a@example.test'}), 'WINDOW_CAP_EXCEEDED')
    ok(ex(a, effect='o', grant='grant-agent', target='send_email', payload={'recipient': 'a@example.test'}))  # other agent
    a.now = 300; ok(ex(a, effect='m6', grant='grant-support', target='send_email', payload={'recipient': 'a@example.test'}))
    ev = [e for e in a.snapshot()['events'] if e['status'] == 'accepted']
    assert [e['threshold_alert'] for e in ev[:5]] == [False, False, False, True, True]


def test_delete_cap_one_per_window(make):
    a = make(); c = {'user': 'user-admin'}
    ok(ex(a, grant='grant-agent', target='delete_record', claims=c, payload='r1'))
    no(ex(a, effect='2', grant='grant-agent', target='delete_record', claims=c, payload='r2'), 'WINDOW_CAP_EXCEEDED')


def test_split_action_is_one_aggregate(make):
    a = make(); c = {'user': 'user-admin'}
    for i in range(3): ok(ex(a, effect=f's{i}', grant='grant-finance', target='transfer_test_funds', payload={'amount': 100}, claims=c))
    no(ex(a, effect='s3', grant='grant-finance', target='transfer_test_funds', payload={'amount': 1}, claims=c), 'AGGREGATE_CAP_EXCEEDED')
    ok(ex(a, effect='other', grant='grant-agent', target='transfer_test_funds', payload={'amount': 100}, claims=c))


def test_budget_hierarchy_levels(make):
    a = make()
    def spend(i, **h): return ex(a, effect=f'b{i}', grant='grant-agent', claims={'hierarchy': h})
    ok(spend(1, user='user-1')); ok(spend(2, user='user-1'))
    no(spend(3, user='user-1'), 'BUDGET_LEVEL_EXHAUSTED')
    ok(spend(4, user='user-2'))                                   # other users unaffected
    for i in range(5, 8): ok(spend(i, key='key-1'))
    no(spend(8, key='key-1'), 'BUDGET_LEVEL_EXHAUSTED')
    no(spend(9, user='user-99'), 'BUDGET_LEVEL_EXHAUSTED')
    no(spend(10, nolevel='x'), 'BUDGET_LEVEL_EXHAUSTED')
    for i in range(11, 13): ok(spend(i, app='app-1', team='team-1', org='org-1', user='user-3'))
    state = json.loads(__import__('sqlite3').connect(a.path).execute('SELECT body FROM state').fetchone()[0])
    assert state['budgets']['org']['org-1']['used'] == 2 and state['budgets']['team']['team-2']['used'] == 0


def test_denied_request_consumes_nothing(make):
    a = make()
    no(ex(a, grant='grant-agent', claims={'hierarchy': {'user': 'user-1'}, 'environment': 'nonprod'}), 'ENVIRONMENT_MISMATCH')
    state = json.loads(__import__('sqlite3').connect(a.path).execute('SELECT body FROM state').fetchone()[0])
    assert state['budgets']['user']['user-1']['used'] == 0 and state['grants']['grant-agent']['consumed'] == 0


# ---- approvals ---------------------------------------------------------------------------
def held(a, effect='p1', payload='rec', user='user-admin', **kw):
    return ex(a, effect=effect, grant='grant-agent', target='purge_record', payload=payload, claims={'user': user}, **kw)


def test_hold_approve_execute(make):
    a = make(); r = held(a); no(r, 'APPROVAL_PENDING'); assert effects(a) == 0
    assert a.snapshot()['events'][-1]['hold'] is True
    a.__getattr__('approve:p1:user-standard')(); ok(held(a)); assert effects(a) == 1


def test_reject_timeout_self_approval_do_not_run(make):
    for verb, reason in (('reject:p1', 'APPROVAL_REJECTED'), ('timeout:p1', 'APPROVAL_TIMED_OUT'),
                         ('approve:p1:user-admin', 'APPROVAL_SELF_APPROVAL')):
        a = make(); no(held(a), 'APPROVAL_PENDING'); a.__getattr__(verb)()
        no(held(a), reason); assert effects(a) == 0


def test_approval_bound_to_context_and_ttl(make):
    a = make(); no(held(a), 'APPROVAL_PENDING'); a.__getattr__('approve:p1:user-standard')()
    no(held(a, payload='changed'), 'APPROVAL_PENDING')                 # context changed after approval
    b = make(); no(held(b), 'APPROVAL_PENDING'); b.__getattr__('approve:p1:user-standard')()
    b.cfg['approval_ttl'] = 50; b.now = 100 + 51; no(held(b), 'APPROVAL_TIMED_OUT')                # slow use of approval fails safe
    c = make()
    with pytest.raises(KeyError): c.__getattr__('approve:never-held:user-standard')()


def test_approval_required_tools_only(make):
    a = make(); ok(ex(a, grant='grant-agent', claims={'user': 'user-admin'}))
    no(ex(a, effect='x', grant='grant-agent', target='send_external_email', payload='m', claims={'user': 'user-admin'}), 'APPROVAL_PENDING')
    no(ex(a, effect='y', grant='grant-agent', target='transfer_large_funds', payload='m', claims={'user': 'user-admin'}), 'APPROVAL_PENDING')


# ---- failure of the policy engine -------------------------------------------------------------
def test_fail_closed_and_fail_open(make):
    a = make(); a.opa_down(); no(ex(a), 'POLICY_ENGINE_UNAVAILABLE'); assert effects(a) == 0
    a.opa_up(); ok(ex(a, effect='e2', grant='grant-agent'))
    b = make(); b.opa_down(); b.fail_open(); ok(ex(b)); assert effects(b) == 1
    assert b.snapshot()['events'][-1]['policy_skipped'] is True
    c = make(); c.opa_down(); c.fail_open(); no(ex(c, effect='z', fault='forged_signature'), 'AUTHENTICATION_DENIED')  # app controls stay on
    d = make(); d.opa_down(); d.fail_open(); ok(ex(d)); r = ex(d, payload='different'); no(r, 'EFFECT_ID_CONFLICT')


# ---- misc ---------------------------------------------------------------------------------------
def test_concurrent_last_budget_one_effect(make):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    a = make(); reqs = [a.request({'effect': f'p{i}'}) for i in range(2)]; bar = Barrier(2)
    def go(r):
        bar.wait(timeout=10); return a.apply(r)
    with ThreadPoolExecutor(2) as pool: out = list(pool.map(go, reqs))
    assert sorted(o['status'] for o in out) == ['accepted', 'denied'] and effects(a) == 1


def test_every_denial_has_event_with_digest(make):
    from reference_profiles.assurance_runtime import digest
    a = make(); req = a.request({'target': 'unregistered'}); r = a.apply(req); assert r['status'] == 'denied'
    ev = a.snapshot()['events'][-1]
    assert ev['request_digest'] == digest(req) and ev['command'] == req['body']['id'] and ev['reason'] and type(ev['at']) is int


def test_shared_wire_format_limits_are_reported_not_worked_around(make):
    """The shared Cognous wire helper rejects non-ASCII text and floats before any configuration sees them.
    Case variants that need them (Unicode look-alikes in recipients/paths, fractional amounts, NaN) cannot be
    sent to ANY configuration; they are a shared-fixture limit to declare, not a pass for either side."""
    a = make()
    for payload in ({'recipient': 'a@exаmple.test'}, {'amount': 99.99}, {'amount': float('nan')}, {'path': '/lab/data/ａ'}):
        with pytest.raises(ValueError): a.request({'payload': payload})


# ---- exception to an approval step (rule written from the exception-expiry case text; synthetic inputs) -----------
def external(a, effect, **kw):
    return ex(a, effect=effect, grant='grant-agent', target='send_external_email', payload='m', claims={'user': 'user-admin'}, **kw)


def test_exception_waives_a_missing_approval_only_until_its_expiry_instant(make):
    a = make(); no(external(a, 'x0'), 'APPROVAL_PENDING')                     # no exception: held
    b = make(); b.__getattr__('grant_exception:agent:send_external_email:300')()
    b.now = 150; ok(external(b, 'x1')); assert effects(b) == 1                 # live exception: no approval needed
    b.now = 400; no(external(b, 'x2'), 'APPROVAL_PENDING'); assert effects(b) == 1   # the expiry instant is outside the bound


def test_exception_is_per_agent_and_per_target(make):
    a = make(); a.__getattr__('grant_exception:agent:purge_record:300')()
    no(external(a, 'x1'), 'APPROVAL_PENDING')                                  # another target
    b = make(); b.__getattr__('grant_exception:support:send_external_email:300')()
    no(external(b, 'x1'), 'APPROVAL_PENDING')                                  # another agent
    assert effects(a) == 0 and effects(b) == 0


def test_exception_never_waives_a_recorded_rejection_timeout_or_self_approval(make):
    for verb, reason in (('reject:p1', 'APPROVAL_REJECTED'), ('timeout:p1', 'APPROVAL_TIMED_OUT'),
                         ('approve:p1:user-admin', 'APPROVAL_SELF_APPROVAL')):
        a = make(); no(held(a), 'APPROVAL_PENDING'); a.__getattr__(verb)()
        a.__getattr__('grant_exception:agent:purge_record:300')()
        no(held(a), reason); assert effects(a) == 0
