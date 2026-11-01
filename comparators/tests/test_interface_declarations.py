"""Every source reference of the declared interfaces points at a line that contains its marker, and every interface item
that the plan cites exists."""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CMP = REPO / 'comparators'
IFACE = CMP / 'wiki/interface'


def walk(o, path=''):
    if isinstance(o, dict):
        if 'source' in o and 'marker' in o:
            yield path, o['source'], o['marker']
        for k, v in o.items():
            yield from walk(v, path + '/' + k)


def declared():
    return {p.name: json.loads(p.read_text()) for p in sorted(IFACE.glob('*.json'))}


def test_each_source_reference_contains_its_marker():
    checked = 0
    for name, d in declared().items():
        for path, source, marker in walk(d):
            file, _, line = source.rpartition(':')
            lines = (REPO / file).read_text().splitlines()
            assert 1 <= int(line) <= len(lines), (name, path, source)
            assert marker in lines[int(line) - 1], (name, path, source, marker)
            checked += 1
    assert checked >= 25


def test_every_declared_interface_names_a_configuration_and_a_status():
    for name, d in declared().items():
        assert d['configuration'] and 'Declared interface' in d['status'], name


def test_declared_controls_match_the_application_grammar():
    from comparators.wiki.apps import wiki_opa_app as app
    d = declared()['declared-interface-opa-app.json']
    verbs = {v.split(':')[0] for v in d['zero_argument_controls']['verbs (grammar verb:arg:arg through __getattr__)']}
    for v in verbs:
        assert hasattr(app.WikiOpaApp, '_verb_' + v), v
    assert sorted(d['faults']) == sorted(f for f in app.KNOWN_FAULTS if f)


def resolve(d, pointer):
    node = d
    for part in pointer.strip('/').split('/'):
        node = node[part]
    return node


def test_every_interface_item_cited_by_the_plan_exists():
    d = declared()['declared-interface-opa-app.json']
    plan = json.loads((CMP / 'wiki/plans/wiki-subset-plan.json').read_text())
    cited = [(x['id'], i) for x in plan['non_executed'] for i in x.get('interface_items', [])]
    cited += [(c['id'], i) for c in plan['cases'] for i in c.get('world_extension', {}).get('interface_items', [])]
    assert cited
    for sid, item in cited:
        resolve(d, item)


def test_gateway_world_is_ten_tools_and_three_agents():
    from comparators.wiki.apps import wiki_config as W
    sizes = {k: len(v) for k, v in W.GW_TOOLS.items()}
    assert sizes == {'read': 4, 'write': 3, 'delete': 2, 'execute': 1}
    assert W.GW_AGENTS == ['gw-a1', 'gw-a2', 'gw-a3']
    allowed = {a: set(W.RESTRICTED[a]) for a in W.GW_AGENTS}
    reads, writes = set(W.GW_TOOLS['read']), set(W.GW_TOOLS['write'])
    assert allowed['gw-a1'] == reads | writes and allowed['gw-a2'] == reads and allowed['gw-a3'] == reads
    for tools in allowed.values():
        assert not tools & (set(W.GW_TOOLS['delete']) | set(W.GW_TOOLS['execute']))
    assert all(t in W.TOOLS for ts in W.GW_TOOLS.values() for t in ts)


def test_world_extensions_are_declared_and_exist_in_the_world():
    from comparators.wiki.apps import wiki_config as W
    from comparators.wiki.apps import wiki_opa_app as app
    d = declared()['declared-interface-opa-app.json']
    ext = {k for k in d['world_extensions'] if not k.startswith('_')}
    assert ext == {'second_delegation_record', 'budget_cap_control', 'allow_list_removal_control', 'read_only_token_grant',
                   'destination_environment_control', 'task_tool_claim', 'shared_parameter_envelope'}
    verbs = d['zero_argument_controls']['verbs (grammar verb:arg:arg through __getattr__)']
    assert {'disallow_tool:<agent>:<tool>', 'set_budget:<level>:<id>:<cap>', 'set_environment:<prod|non-prod>'} <= set(verbs)
    assert 'task_tools' in d['issuer_claims_keys_read'] and 'task_scope' in app.FAMILIES and 'TASK_TOOL_NOT_WARRANTED' in app.REASON_ORDER
    state = W.initial_state()
    assert {'deleg-1', 'deleg-2'} == set(state['delegations']) and state['grants']['grant-agent-ro']['scopes'] == ['read:tickets']
    assert state['environment'] == 'prod'
    cfg = W.config()['schemas']
    envelope = set(W.ENVELOPE_PARAMS)
    for tool in ('send_email', 'transfer_test_funds', 'read_file', 'update_records'):
        assert set(cfg[tool]['required']) | set(cfg[tool]['optional']) == envelope and len(cfg[tool]['required']) == 1
