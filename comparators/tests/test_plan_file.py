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
    assert PLAN['counts_per_state'] == {'ASKED': 86, 'NOT-EXPRESSIBLE': 19, 'NOT-CLAIMED': 0, 'UNASKED': 16}
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
        if x['origin'].startswith('plan authoring'):
            assert o['state'] == 'ASKED' and x['outcome_expected_statuses'] == o['expected_statuses'] and x['expected_outcome_unchanged']
            assert x['interface_items'] and x['citations']
        else:
            assert o['state'] == x['state']


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
