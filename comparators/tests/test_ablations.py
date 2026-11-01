"""Control-removal probes of the Wiki OPA application, on synthetic inputs of this file's own.

For every rule family: the violation is denied with the family's reason; with that family (and,
where another family independently covers the same violation, that one too) switched off, the same
request is accepted. This shows each pass is not vacuous. A probe for a family never permits a
violation of an unrelated family.
"""
import pytest
from test_wiki_opa_app import ex, ok, no, effects
from comparators.wiki.apps.wiki_opa_app import FAMILIES

A = 'grant-agent'
ADMIN = {'user': 'user-admin'}


def v_revocation(a): a.revoke(); return ex(a)
def v_budget(a): ok(ex(a)); return ex(a, effect='e2')
def v_expiry(a): a.now = 200; return ex(a)
def v_verifier(a): return ex(a, fault='missing_verifier')
def v_credential_pin(a): a.rotate(); return ex(a)
def v_clock(a): a.now = 150; ok(ex(a, grant=A)); a.now = 120; return ex(a, effect='e2', grant=A)
def v_stop(a): a.__getattr__('stop:agent-b')(); return ex(a, grant='grant-agent-b')
def v_tool_registry(a): return ex(a, grant=A, target='unregistered')
def v_tool_definition(a): a.__getattr__('mutate_tool:sink:description')(); return ex(a, grant=A)
def v_name_collision(a):
    a.__getattr__('add_tool:server-2:send_email')(); a.__getattr__('allow_tool:agent:server-2/send_email')()
    return ex(a, grant=A, target='server-2/send_email', payload={'recipient': 'a@example.test'})
def v_allow_list(a): return ex(a, grant='grant-support', target='transfer_test_funds', payload={'amount': 5}, claims=ADMIN)
def v_elevation(a): return ex(a, grant=A, target='elevated_task')
def v_escalation(a): return ex(a, grant=A, target='edit_roles', claims=ADMIN)
def v_agent_change(a): a.__getattr__('change_agent:agent-c:model')(); return ex(a, grant='grant-agent-c', target='update_records', payload={'records': 1}, claims=ADMIN)
def v_operation(a): return ex(a, grant='grant-research', target='read_file', payload={'path': '/lab/data/a', 'operation': 'write'})
def v_environment(a): return ex(a, grant=A, claims={'environment': 'nonprod'})
def v_scope(a): return ex(a, grant=A, payload={'scope': 'read:tickets', 'resource': 'payroll'})
def v_user_entitlement(a): return ex(a, grant=A, target='delete_record', claims={'user': 'user-standard'}, payload='x')
def v_claims_consistency(a): return ex(a, grant=A, claims={'user': 'user-admin'}, payload={'user': 'user-standard'})
def v_task_expiry(a): return ex(a, grant=A, claims={'task_expires_at': 100})
def v_task_scope(a): return ex(a, grant=A, target='read_file', payload={'path': '/lab/data/a'}, claims={'task_tools': []})
def v_delegation_record(a): a.__getattr__('revoke_delegation:deleg-1')(); return ex(a, grant=A, target='read_file', claims={'user': 'user-a', 'delegation_id': 'deleg-1'}, payload={'path': '/lab/data/a'})
def v_delegation_chain(a): return ex(a, grant='grant-agent-b', target='read_file', payload={'path': '/lab/data/a'}, claims={'chain': ['parent', 'child-1', 'child-3', 'agent-b']})
def v_schema(a): return ex(a, grant='grant-helpdesk', target='update_records', payload={'records': 1, 'extra': 1}, claims=ADMIN)
def v_parameter(a): return ex(a, grant='grant-support', target='send_email', payload={'recipient': 'a@evil.test'})
def v_window(a):
    ok(ex(a, grant=A, target='delete_record', claims=ADMIN, payload='r1'))
    return ex(a, effect='e2', grant=A, target='delete_record', claims=ADMIN, payload='r2')
def v_aggregate(a):
    for i in range(3): ok(ex(a, effect=f'f{i}', grant='grant-finance', target='transfer_test_funds', payload={'amount': 100}, claims=ADMIN))
    return ex(a, effect='f3', grant='grant-finance', target='transfer_test_funds', payload={'amount': 1}, claims=ADMIN)
def v_hierarchy(a):
    ok(ex(a, grant=A, claims={'hierarchy': {'user': 'user-1'}})); ok(ex(a, effect='h2', grant=A, claims={'hierarchy': {'user': 'user-1'}}))
    return ex(a, effect='h3', grant=A, claims={'hierarchy': {'user': 'user-1'}})
def v_approval(a): return ex(a, grant=A, target='purge_record', payload='rec', claims=ADMIN)

# family -> (violation, expected reason, extra families that independently deny the same request)
PROBES = {
    'revocation': (v_revocation, 'CREDENTIAL_BINDING_CLOSED', ()), 'budget': (v_budget, 'CREDENTIAL_BINDING_CLOSED', ()),
    'expiry': (v_expiry, 'CREDENTIAL_EXPIRED', ()), 'verifier': (v_verifier, 'VERIFIER_INVALID', ()),
    'credential_pin': (v_credential_pin, 'CREDENTIAL_PIN_CHANGED', ()), 'clock': (v_clock, 'CLOCK_REGRESSION', ()),
    'stop': (v_stop, 'AGENT_STOPPED', ()), 'tool_registry': (v_tool_registry, 'TOOL_NOT_REGISTERED', ('allow_list',)),
    'tool_definition': (v_tool_definition, 'TOOL_DEFINITION_CHANGED', ()),
    'name_collision': (v_name_collision, 'TOOL_NAME_COLLISION', ()), 'allow_list': (v_allow_list, 'TOOL_NOT_ALLOWED', ()),
    'elevation': (v_elevation, 'PRIVILEGE_ELEVATION_REQUIRED', ()), 'escalation': (v_escalation, 'ESCALATION_BLOCKED', ()),
    'agent_change': (v_agent_change, 'AGENT_PENDING_REAPPROVAL', ()), 'operation': (v_operation, 'OPERATION_NOT_PERMITTED', ()),
    'environment': (v_environment, 'ENVIRONMENT_MISMATCH', ()), 'scope': (v_scope, 'SCOPE_NOT_GRANTED', ()),
    'user_entitlement': (v_user_entitlement, 'USER_NOT_ENTITLED', ()),
    'claims_consistency': (v_claims_consistency, 'IDENTITY_SUBSTITUTION', ()),
    'task_expiry': (v_task_expiry, 'TASK_EXPIRED', ()), 'task_scope': (v_task_scope, 'TASK_TOOL_NOT_WARRANTED', ()),
    'delegation_record': (v_delegation_record, 'DELEGATION_INVALID', ('user_entitlement',)),
    'delegation_chain': (v_delegation_chain, 'DELEGATION_DEPTH', ('allow_list',)), 'schema': (v_schema, 'SCHEMA_VIOLATION', ()),
    'parameter': (v_parameter, 'PARAMETER_RULE_VIOLATION', ()), 'window': (v_window, 'WINDOW_CAP_EXCEEDED', ()),
    'aggregate': (v_aggregate, 'AGGREGATE_CAP_EXCEEDED', ()), 'hierarchy': (v_hierarchy, 'BUDGET_LEVEL_EXHAUSTED', ()),
    'approval': (v_approval, 'APPROVAL_PENDING', ()),
}


def test_every_family_has_a_probe():
    assert set(PROBES) == set(FAMILIES)


@pytest.mark.parametrize('family', sorted(PROBES))
def test_family_is_active_and_removable(make, family):
    violation, reason, extra = PROBES[family]
    r = violation(make()); no(r, reason)
    mutation = '+'.join((family,) + extra)
    app = make(mutation); r = violation(app)
    assert r['status'] == 'accepted' or reason not in r['all'], (family, r)
    assert r['status'] == 'accepted', (family, r)


@pytest.mark.parametrize('family', sorted(PROBES))
def test_probe_of_one_family_does_not_open_another(make, family):
    other = 'revocation' if family != 'revocation' else 'expiry'
    app = make(family); violation = PROBES[other][0]
    r = violation(app)
    if other in PROBES[family][2]: return
    assert r['status'] == 'denied', (family, other, r)
