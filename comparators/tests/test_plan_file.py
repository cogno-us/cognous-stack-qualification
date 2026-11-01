"""The plan file of PR-6 for the Wiki subset: structure, coverage of the registered subset, outcomes carried unchanged,
reproducibility from the scripts. No scenario is executed here."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
PKG = REPO / 'comparators/wiki'
TWIN = json.loads((REPO / 'process/release-gate/preregistration.json').read_text())
PLAN = json.loads((PKG / 'plans/wiki-subset-plan.json').read_text())
OUT = json.loads((PKG / 'expected-outcomes/outcomes-final.json').read_text())
SUB = json.loads((PKG / 'expected-outcomes/scenario-outcomes.json').read_text())
REQUIRED = {'id', 'steps', 'expected_statuses', 'expected_effects', 'allowed_effect_ids', 'expected_payload'}


def test_the_28_registered_cases_are_covered_exactly():
    registered = [c['id'] for c in TWIN['comparator_subset']['wiki']['included']]
    assert len(registered) == 28
    assert [c['id'] for c in SUB['cases']] == registered
    assert sorted({s['case'] for s in OUT['scenarios']}) == sorted(registered)
    assert sorted({c['wiki_case_id'] for c in PLAN['cases']} | {x['wiki_case_id'] for x in PLAN['non_executed']}) == sorted(registered)


def test_counts_are_as_recorded():
    assert OUT['scenarios_total'] == 121 and PLAN['scenarios_total'] == 121 and len(SUB['cases']) == 28
    assert OUT['counts_per_state'] == {'ASKED': 94, 'NOT-EXPRESSIBLE': 11, 'NOT-CLAIMED': 0, 'UNASKED': 16}
    assert PLAN['counts_per_state'] == {'ASKED': 94, 'NOT-EXPRESSIBLE': 11, 'NOT-CLAIMED': 0, 'UNASKED': 16}
    assert PLAN['counts_per_state'] == OUT['counts_per_state']        # every scenario asked in the outcome files is executable
    assert len(PLAN['cases']) + len(PLAN['non_executed']) == 121
    assert len({c['id'] for c in PLAN['cases']} | {x['id'] for x in PLAN['non_executed']}) == 121


def test_declarations_of_the_registered_rulings():
    d = PLAN['declarations']
    assert PLAN['seeds'] == [1701, 1702] and PLAN['repetitions'] == 5
    assert d['stated_time_T'].startswith('T = 0 units') and 'accepted | denied' in d['status_vocabulary']
    assert 'clock starts at 100' in d['time_unit'] or 'starts at 100' in d['time_unit']
    assert d['tools_L06_011'] == {'read': 4, 'write': 3, 'delete': 2, 'execute': 1, 'agents': 3, 'users': 2}
    assert d['evasion_set_L06_014'] == ['TC-L06-014-S3', 'TC-L06-014-S4', 'TC-L06-014-S5']


def test_executable_scenarios_have_the_runner_keys_and_no_expected_reasons():
    for c in PLAN['cases']:
        assert REQUIRED <= set(c), c['id']
        assert 'expected_reasons' not in c and c['source'] == 'from case text'
        assert len(c['allowed_effect_ids']) == c['expected_effects'] == c['expected_statuses'].count('accepted')
        clock = 100
        for st in c['steps']:
            if st['action'] == 'clock':
                assert clock <= st['now'] <= 999, c['id']
                clock = st['now']
    assert 'expected_reasons' not in json.dumps(PLAN['cases'])


def test_expected_outcomes_of_the_executable_scenarios_equal_the_outcome_file():
    by = {s['scenario']: s for s in OUT['scenarios']}
    for c in PLAN['cases']:
        o = by[c['id']]
        assert o['state'] == 'ASKED'
        assert c['expected_statuses'] == o['expected_statuses'] and c['expected_effects'] == o['expected_effects'], c['id']
    for x in PLAN['non_executed']:
        o = by[x['id']]
        assert not x['origin'].startswith('plan authoring')        # no scenario asked in the outcome files is set aside by plan authoring
        assert o['state'] == x['state'] and o['state'] != 'ASKED'


def test_the_ten_tool_case_covers_all_ten_tools_for_three_agents_and_two_users():
    from comparators.wiki.apps import wiki_config as W
    expect = {'S1': 24, 'S2': 6, 'S3': 12, 'S4': 12, 'S5': 6}
    tools_all = {t for ts in W.GW_TOOLS.values() for t in ts}
    seen = set()
    for suffix, n in expect.items():
        c = next(c for c in PLAN['cases'] if c['id'] == 'TC-L06-011-' + suffix)
        calls = [s['args'] for s in c['steps'] if s['action'] == 'execute']
        assert len(calls) == n, suffix
        assert len({(a['grant'], a['target'], a['issuer_claims']['user']) for a in calls}) == n
        seen |= {a['target'] for a in calls}
        assert {a['issuer_claims']['user'] for a in calls} == {'user-standard', 'user-admin'}
    assert seen == tools_all and len(tools_all) == 10


def test_validate_plan_passes():
    r = subprocess.run([sys.executable, str(PKG / 'harness/validate_plan.py')], capture_output=True, text=True, timeout=300)
    assert r.returncode == 0 and 'errors: 0' in r.stdout, r.stdout[-1500:]
    assert 'class introspection: both comparator applications imported' in r.stdout


def test_outcome_files_and_plan_are_reproduced_byte_for_byte_by_the_scripts(tmp_path):
    subprocess.run([sys.executable, str(PKG / 'expected-outcomes/build_outcomes.py'), str(tmp_path)], check=True, capture_output=True)
    for name in ('outcomes-final.json', 'scenario-outcomes.json'):
        assert (tmp_path / name).read_bytes() == (PKG / 'expected-outcomes' / name).read_bytes(), name
    out = tmp_path / 'plan.json'
    subprocess.run([sys.executable, str(PKG / 'harness/author_plan.py'), str(out)], check=True, capture_output=True)
    assert out.read_bytes() == (PKG / 'plans/wiki-subset-plan.json').read_bytes()


def test_no_unscored_cell_is_hidden_every_unasked_or_not_expressible_scenario_has_a_reason_and_a_citation():
    for x in PLAN['non_executed']:
        assert x['reason'] and x['citations'] and x['state'] in ('NOT-EXPRESSIBLE', 'UNASKED'), x['id']


EXTENDED = ['TC-D09-011-S4', 'TC-D13-003-S6', 'TC-L06-013-S4', 'TC-L06-014-S1', 'TC-L07-008-S1', 'TC-L07-008-S2', 'TC-L09-004-S5', 'TC-L09-019-S2']


def test_the_eight_scenarios_that_were_set_aside_are_executable_with_their_outcome_unchanged():
    by_case = {c['id']: c for c in PLAN['cases']}
    by_out = {s['scenario']: s for s in OUT['scenarios']}
    assert all(sid in by_case for sid in EXTENDED) and not {x['id'] for x in PLAN['non_executed']} & set(EXTENDED)
    for sid in EXTENDED:
        c, o = by_case[sid], by_out[sid]
        assert c['expected_statuses'] == o['expected_statuses'] and c['expected_effects'] == o['expected_effects'], sid
        assert c['world_extension']['interface_items'] and c['world_extension']['decision'].startswith('DECISIONS.md C-'), sid
    assert PLAN['status'].startswith('EXECUTABLE STEPS AUTHORED')


def test_every_interface_item_cited_by_a_scenario_exists_in_the_declared_interface():
    d = json.loads((PKG / 'interface/declared-interface-opa-app.json').read_text())
    for c in PLAN['cases']:
        for item in c.get('world_extension', {}).get('interface_items', []):
            node = d
            for part in item.strip('/').split('/'):
                node = node[part]
    cited = {i for c in PLAN['cases'] for i in c.get('world_extension', {}).get('interface_items', [])}
    assert {'/world_extensions/' + k for k in d['world_extensions'] if not k.startswith('_')} <= cited     # every extension is used by a scenario


def test_the_extended_scenarios_use_only_the_declared_request_fields_and_controls():
    from comparators.wiki.apps.wiki_opa_app import WikiOpaApp
    for c in PLAN['cases']:
        if c['id'] not in EXTENDED: continue
        for st in c['steps']:
            if st['action'] == 'execute':
                assert set(st['args']) <= {'grant', 'effect', 'generation', 'policy', 'target', 'payload', 'verifier_status', 'issuer_claims'}
            elif st['action'] != 'clock':
                assert ':' not in st['action'] or hasattr(WikiOpaApp, '_verb_' + st['action'].split(':')[0]), st
