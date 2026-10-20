"""Declared world and rule configuration of the Wiki OPA application.

One application configured once, from the text of the registered Wiki cases
(tools, limits, test data named there). Scenario authors express each case with
existing request fields only: grant effect generation policy target payload
verifier_status issuer_claims. Nothing here is derived from how any other
configuration behaves.
"""
import copy
import unicodedata

PROFILE_ID = 'opa-transactional-application'  # same profile id as the registered comparator

# Ten tools of one gateway server for the per-tool allow and deny case (4 read, 3 write, 2 delete, 1 execute) and the
# three agents that case names; the rule is carried by the agents' allow-lists (reads for all three, writes for the
# first agent only, deletes and execute for none), the same per-agent allow-list mechanism as every other agent.
GW_TOOLS = {'read': ['gw_read_%d' % i for i in range(1, 5)], 'write': ['gw_write_%d' % i for i in range(1, 4)],
            'delete': ['gw_delete_%d' % i for i in range(1, 3)], 'execute': ['gw_exec_1']}
GW_AGENTS = ['gw-a1', 'gw-a2', 'gw-a3']
READ_TOOLS = ('read_file', 'list_tickets', 'sink') + tuple(GW_TOOLS['read'])

TOOLS = ['sink', 'send_email', 'send_external_email', 'transfer_test_funds', 'transfer_large_funds',
         'read_file', 'update_records', 'delete_record', 'purge_record', 'elevated_task',
         'list_tickets', 'edit_roles', 'read_credentials', 'create_agent'] + [t for ts in GW_TOOLS.values() for t in ts]
AGENT_IDS = ['agent', 'support', 'finance', 'helpdesk', 'research', 'operations', 'parent',
             'child-1', 'child-2', 'child-3', 'agent-b', 'agent-c'] + GW_AGENTS
RESTRICTED = {  # allow-lists below 'everything' (L06-013, L06-039, L06-017)
    'support': ['send_email', 'read_file'], 'finance': ['transfer_test_funds', 'read_file'],
    'helpdesk': ['read_file', 'update_records'], 'research': ['read_file'],
    'operations': ['read_file', 'update_records'], 'parent': ['read_file', 'update_records'],
    'child-1': ['read_file'], 'child-2': ['update_records'], 'child-3': ['read_file'],
    'gw-a1': GW_TOOLS['read'] + GW_TOOLS['write'], 'gw-a2': list(GW_TOOLS['read']), 'gw-a3': list(GW_TOOLS['read'])}
READ_ONLY_AGENTS = {'research'}

# Parameter envelope shared by the four mock tools of the parameter-policy case (send_email, transfer_test_funds,
# read_file, update_records). Each tool requires its own parameter; the others are optional keys of the same envelope,
# validated by type and by the parameter rules when present. A key outside the envelope is still an unknown argument.
ENVELOPE_PARAMS = {'recipient': 'string', 'body': 'string', 'amount': 'number', 'account': 'string', 'path': 'string',
                   'records': 'number'}


def tool_schema(required):
    return {'required': {k: ENVELOPE_PARAMS[k] for k in required},
            'optional': {k: t for k, t in ENVELOPE_PARAMS.items() if k not in required}}


CONFIG = {
    'allowed_domains': ['example.test', 'corp.test'],
    'allowed_path_prefixes': ['/lab/data/', '/lab/public/'],
    'amount_limit': 100,
    'max_records': 10,
    'approval_ttl': 900,
    'approval_required_targets': ['purge_record', 'send_external_email', 'transfer_large_funds'],
    'privileged_targets': ['elevated_task'],
    'never_via_agent': ['edit_roles', 'read_credentials', 'create_agent'],
    'user_required_targets': ['update_records', 'delete_record', 'purge_record', 'transfer_test_funds',
                              'transfer_large_funds', 'edit_roles', 'read_credentials', 'create_agent'],
    'identity_payload_keys': ['user', 'claimed_user', 'on_behalf_of'],
    'max_delegation_depth': 3,
    'require_qualified_names': False,
    'windows': {'update_records': {'cap': 20, 'seconds': 3600}, 'send_email': {'cap': 5, 'seconds': 3600},
                'delete_record': {'cap': 1, 'seconds': 3600}},
    'aggregate_amount': {'transfer_test_funds': {'cap': 300, 'seconds': 3600}},
    'alert_fraction': 0.8,
    'schemas': {'send_email': tool_schema(['recipient']), 'transfer_test_funds': tool_schema(['amount']),
                'read_file': tool_schema(['path']), 'update_records': tool_schema(['records'])},
}

BUDGETS = {'org': {'org-1': 100},
           'team': {f'team-{i}': 30 for i in range(1, 4)},
           'app': {f'app-{i}': 10 for i in range(1, 7)},
           'user': {f'user-{i}': 2 for i in range(1, 11)},
           'key': {f'key-{i}': 3 for i in range(1, 5)}}

MATERIAL_AGENT_COMPONENTS = ('model', 'prompt', 'tool', 'data_scope')  # owner change is not material

_CONFUSABLE = str.maketrans({'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'х': 'x', 'і': 'i',
                             'ѕ': 's', 'ԁ': 'd', 'ɡ': 'g', 'ο': 'o', 'ν': 'v', 'ι': 'i', 'ａ': 'a'})


def normalise_name(name):
    """Namespace stripped, NFKC, casefolded, small confusable fold (not UTS #39)."""
    base = name.split('/')[-1]
    return unicodedata.normalize('NFKC', base).casefold().translate(_CONFUSABLE)


def tool_record(name, server='server-1', trusted=True):
    definition = dict(name=name, description='described', params=['payload'], scope='s')
    return dict(server=server, trusted=trusted, norm=normalise_name(name), status='approved',
                approved=dict(definition, policy='policy1'), current=dict(definition, policy='policy1'))


def agent_record(agent_id):
    allowed = RESTRICTED.get(agent_id, TOOLS)
    return dict(allowed_targets=list(allowed), read_targets=[t for t in allowed if t in READ_TOOLS],
                operations=['read'] if agent_id in READ_ONLY_AGENTS else ['read', 'write'],
                stopped=False, exceptions=[], pending_reapproval=False,
                manifest_approved=dict(model='m1', prompt='p1', tool='t1', data_scope='d1', owner='o1'),
                manifest_current=dict(model='m1', prompt='p1', tool='t1', data_scope='d1', owner='o1'))


def grant_record(agent, max_effects, token_scopes=None, expires_at=200):
    return dict(agent=agent, generation=7, revoked=False, consumed=0, max_effects=max_effects, expires_at=expires_at,
                environment='prod', credential='v1', provisioned_credential='v1', dependency='d1',
                provisioned_dependency='d1', grants=['read', 'write'], provisioned_grants=['read', 'write'],
                scopes=token_scopes or ['read:tickets', 'write:tickets'])


def initial_state():
    grants = {'grant': grant_record('agent', 1)}
    for a in AGENT_IDS:
        grants['grant-' + a] = grant_record(a, 1000, expires_at=10000)
    # a token of agent "agent" that carries the read scope only (token-scope case: a write with a read-only token)
    grants['grant-agent-ro'] = grant_record('agent', 1000, token_scopes=['read:tickets'], expires_at=10000)
    non_priv = [t for t in TOOLS if t not in ('delete_record', 'purge_record', 'transfer_large_funds', 'elevated_task')]
    state = dict(
        environment='prod', generation=7, last_now=100, opa_available=True, fail_mode='closed',
        agents={a: agent_record(a) for a in AGENT_IDS}, grants=grants,
        tools={t: tool_record(t) for t in TOOLS},
        users={'user-standard': dict(active=True, allowed_targets=non_priv),
               'user-admin': dict(active=True, allowed_targets=list(TOOLS)),
               'user-a': dict(active=True, allowed_targets=['read_file']),
               'user-b': dict(active=True, allowed_targets=['read_file'])},
        delegations={'deleg-1': dict(user='user-a', targets=['read_file'], data_classes=['public'],
                                     expires_at=200, revoked=False),
                     # same scope as deleg-1 but valid beyond the latest clock reading of a scenario, so that a check
                     # long after a revocation can only be decided by the revocation
                     'deleg-2': dict(user='user-a', targets=['read_file'], data_classes=['public'],
                                     expires_at=10000, revoked=False)},
        budgets={lv: {k: dict(cap=c, used=0) for k, c in ids.items()} for lv, ids in BUDGETS.items()},
        windows={}, aggregates={}, approvals={}, pending={})
    return state


def config():
    return copy.deepcopy(CONFIG)
