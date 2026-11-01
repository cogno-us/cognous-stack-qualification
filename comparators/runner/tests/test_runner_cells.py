"""Cell aggregation: states of scenarios, outcomes, case cells, counts and the lists of RP-6."""
import copy

import pytest

from comparators.runner import cells as C

OCS = 'cognous-protected-destination'
OPA = 'opa-transactional-application'
GRAPH = 'langgraph-opa-transactional-application'
PROFILES = [OCS, OPA, GRAPH]
A, NE, NC, U = C.ASKED, C.NE, C.NC, C.UNASKED


def st(status, **kw):
    d = dict(status=status, run=status == A or kw.pop('run', False), scored=status == A, reason='r', reason_code='c', citations=[], origin='x', void=False)
    d.update(kw)
    return d


def row(sid, ok=True, profile='p', mode='scored', outputs=None, **kw):
    r = dict(case_id=sid, profile=profile, mode=mode, repetition=0, seed=1701, pass_case=ok, outputs=outputs or [],
             unexpected_effect_count=0, missing_effect_count=0, false_allows=0, false_blocks=0, denied_calls=0, durably_recorded_denials=0)
    r.update(kw)
    return r


def mini_plan():
    return dict(profiles=[OPA, GRAPH],
                cases=[dict(id='C-S1', wiki_case_id='C', per_configuration=None), dict(id='C-S2', wiki_case_id='C', per_configuration={OCS: 'NOT-CLAIMED (amendment 39)'})],
                non_executed=[dict(id='C-S3', wiki_case_id='C', state='NOT-EXPRESSIBLE', origin='plan', reason='limit of the shared fixture', reason_code='N5'),
                              dict(id='C-S4', wiki_case_id='C', state='UNASKED', origin='plan', reason='rule missing', reason_code='R3')])


def decl_for(statuses):
    return dict(records=[dict(scenario=sid, status=s, run_anyway=s == NC, reason='declared', reason_code='X', citations=[dict(kind='x')])
                         for sid, s in statuses.items()])


# ---------------------------------------------------------------- scenario states
def test_states_of_every_scenario_for_every_configuration():
    states = C.scenario_states(mini_plan(), OCS, decl_for({'C-S1': A, 'C-S2': NC}))
    assert sorted(states) == sorted(PROFILES)
    assert states[OCS]['C-S1']['status'] == A and states[OCS]['C-S1']['scored']
    assert states[OCS]['C-S2']['status'] == NC and states[OCS]['C-S2']['run'] and not states[OCS]['C-S2']['scored']
    for p in (OPA, GRAPH):
        assert states[p]['C-S1']['status'] == A and states[p]['C-S2']['status'] == A
    for p in PROFILES:
        assert states[p]['C-S3']['status'] == NE and states[p]['C-S3'].get('plan_level') and not states[p]['C-S3']['run']
        assert states[p]['C-S4']['status'] == U and not states[p]['C-S4']['run']


def test_a_scenario_without_a_declaration_for_the_destination_stops_the_run():
    with pytest.raises(C.DeclarationConflict):
        C.scenario_states(mini_plan(), OCS, decl_for({'C-S1': A}))


def test_a_plan_entry_that_says_not_claimed_must_agree_with_the_declaration():
    with pytest.raises(C.DeclarationConflict):
        C.scenario_states(mini_plan(), OCS, decl_for({'C-S1': A, 'C-S2': A}))


def test_a_declaration_for_a_comparator_without_a_citation_is_void_and_the_scenario_is_asked():
    plan = mini_plan()
    plan['cases'][0]['per_configuration'] = {OPA: dict(status=NE, reason='no field')}
    states = C.scenario_states(plan, OCS, decl_for({'C-S1': A, 'C-S2': NC}))
    assert states[OPA]['C-S1']['status'] == A and states[OPA]['C-S1']['void'] is True
    plan['cases'][0]['per_configuration'] = {OPA: dict(status=NE, reason='no field', citations=[dict(kind='interface', item='x')])}
    states = C.scenario_states(plan, OCS, decl_for({'C-S1': A, 'C-S2': NC}))
    assert states[OPA]['C-S1']['status'] == NE and not states[OPA]['C-S1']['run'] and states[GRAPH]['C-S1']['status'] == A


# ---------------------------------------------------------------- scenario outcomes
def test_asked_scenario_outcomes():
    s = st(A)
    assert C.scenario_outcome(s, [row('x'), row('x')], 2)['outcome'] == C.PASS
    assert C.scenario_outcome(s, [row('x'), row('x', False)], 2)['outcome'] == C.FAIL
    assert C.scenario_outcome(s, [row('x'), row('x', error='RuntimeError: boom')], 2)['outcome'] == C.COULD_NOT_CHECK
    assert C.scenario_outcome(s, [row('x')], 2)['outcome'] == C.COULD_NOT_CHECK     # fewer trials than expected is never a pass
    assert C.scenario_outcome(s, [], 2)['outcome'] == C.COULD_NOT_CHECK
    assert C.scenario_outcome(s, [dict(case_id='x', profile='p', mode='masked', executed=True)], 1)['outcome'] == C.MASKED


def test_refusal_reasons_are_kept_per_outcome():
    outputs = [dict(status='denied', reason='R1'), dict(status='accepted', reason=None), dict(status='denied', reason=None)]
    o = C.scenario_outcome(st(A), [row('x', outputs=outputs), row('x', outputs=outputs)], 2)
    assert o['reasons'] == {'denied: (no reason)': 2, 'denied: R1': 2}


def test_not_expressible_not_claimed_and_not_asked_scenarios_are_never_a_pass_or_fail():
    assert C.scenario_outcome(st(NE), [], 5)['outcome'] == C.NOT_EXPRESSIBLE
    assert C.scenario_outcome(st(U), [], 5)['outcome'] == C.NOT_ASKED
    nc = C.scenario_outcome(st(NC, run=True), [row('x', mode='observation'), row('x', False, mode='observation')], 5)
    assert nc['outcome'] == C.NOT_CLAIMED and nc['trials'] == 0 and nc['passed'] == 0
    assert nc['observation']['trials'] == 2 and nc['observation']['observed_equal_to_expected'] == 1


# ---------------------------------------------------------------- case cells
def cell(states, rows, expected=1):
    outcomes = {s: C.scenario_outcome(states[s], [r for r in rows if r['case_id'] == s], expected) for s in states}
    return C.case_cell(sorted(states), states, outcomes)


def test_case_cell_rules():
    assert cell({'a': st(A), 'b': st(NE)}, [row('a')])['outcome'] == C.PASS
    assert cell({'a': st(A), 'b': st(A)}, [row('a'), row('b', False)])['outcome'] == C.FAIL
    assert cell({'a': st(A), 'b': st(A)}, [row('a', False), row('b', error='E: x')])['outcome'] == C.COULD_NOT_CHECK   # a scenario that could not be checked keeps the case open
    assert cell({'a': st(A), 'b': st(A)}, [row('a'), row('b', error='E: x')])['outcome'] == C.COULD_NOT_CHECK
    assert cell({'a': st(A)}, [])['outcome'] == C.COULD_NOT_CHECK
    assert cell({'a': st(NE), 'b': st(U)}, [])['outcome'] == C.NOT_EXPRESSIBLE
    assert cell({'a': st(NC), 'b': st(U)}, [])['outcome'] == C.NOT_CLAIMED
    assert cell({'a': st(NC), 'b': st(NE)}, [])['outcome'] == C.NOT_EXPRESSIBLE
    assert cell({'a': st(U), 'b': st(U)}, [])['outcome'] == C.NOT_ASKED


def test_the_cell_says_asked_k_of_n_and_counts_the_rest():
    c = cell({'a': st(A), 'b': st(NE), 'c': st(NC), 'd': st(U)}, [row('a')])
    assert (c['asked'], c['of'], c['not_expressible'], c['not_claimed'], c['not_asked']) == (1, 4, 1, 1, 1)
    assert c['trials'] == 1 and c['trials_passed'] == 1


def test_a_pass_fraction_counts_only_the_trials_of_asked_scenarios():
    states = {'a': st(A), 'b': st(NC, run=True)}
    rows = [row('a'), row('a'), row('b', mode='observation'), row('b', False, mode='observation')]
    c = cell(states, rows, 2)
    assert c['trials'] == 2 and c['trials_passed'] == 2


# ---------------------------------------------------------------- sets
def build(states_by_profile, rows, cases, expected=1):
    return C.build_set('wiki', cases, PROFILES, states_by_profile, rows, expected, OCS)


def test_counts_per_configuration_and_oracle_counts_use_only_scored_rows():
    plan = mini_plan()
    states = C.scenario_states(plan, OCS, decl_for({'C-S1': A, 'C-S2': NC}))
    rows = []
    for p in PROFILES:
        rows.append(row('C-S1', profile=p, false_allows=1, denied_calls=2, durably_recorded_denials=2))
        if p != OCS:
            rows.append(row('C-S2', profile=p))
    rows.append(row('C-S2', profile=OCS, mode='observation', false_allows=7))
    ids = ['C-S1', 'C-S2', 'C-S3', 'C-S4']
    t = build(states, rows, [dict(id='C', title='case C', scenarios=ids)])
    assert t['counts'][OCS] == dict(scenarios=4, asked=1, not_expressible=1, not_expressible_plan_level=1, not_claimed=1, not_asked=1, could_not_check=0)
    assert t['counts'][OPA]['asked'] == 2 and t['counts'][OPA]['not_claimed'] == 0
    assert t['oracle_counts'][OCS]['false_allows'] == 1          # the observation of the not-claimed scenario is not in the counts
    assert t['oracle_counts'][OCS]['case_trials'] == 1
    assert [o['scenario'] for o in t['unscored_observations']] == ['C-S2'] and t['unscored_observations'][0]['profile'] == OCS


def test_counts_come_from_the_plan_and_not_from_a_constant():
    plan = mini_plan()
    for n in range(3):
        plan['cases'].append(dict(id='C-X%d' % n, wiki_case_id='C', per_configuration=None))
    statuses = {c['id']: A for c in plan['cases']}
    statuses['C-S2'] = NC
    states = C.scenario_states(plan, OCS, decl_for(statuses))
    ids = [c['id'] for c in plan['cases']] + [c['id'] for c in plan['non_executed']]
    t = build(states, [], [dict(id='C', title='C', scenarios=ids)])
    assert t['counts'][OPA]['scenarios'] == len(ids) == 7 and t['counts'][OPA]['asked'] == 5


def test_could_not_check_is_counted_per_scenario():
    states = C.scenario_states(mini_plan(), OCS, decl_for({'C-S1': A, 'C-S2': NC}))
    rows = [row('C-S1', profile=OCS, error='X: y')]
    t = build(states, rows, [dict(id='C', title='C', scenarios=['C-S1'])])
    assert t['counts'][OCS]['could_not_check'] == 1 and t['cases'][0]['cells'][OCS]['outcome'] == C.COULD_NOT_CHECK
    assert t['counts'][OPA]['could_not_check'] == 1      # the comparators have no rows at all: nothing recorded is never a pass


# ---------------------------------------------------------------- RP-6 lists
def table_with(cells_by_case):
    return dict(profiles=PROFILES, cases=[dict(id=cid, cells={p: dict(outcome=o) for p, o in zip(PROFILES, outs)}) for cid, outs in cells_by_case.items()])


def test_lists_of_cases_where_a_comparator_passes_and_the_destination_does_not():
    P, F, X, N, K = C.PASS, C.FAIL, C.NOT_EXPRESSIBLE, C.NOT_CLAIMED, C.COULD_NOT_CHECK
    t = table_with({'c1': (F, P, F), 'c2': (X, P, P), 'c3': (N, F, F), 'c4': (P, P, P), 'c5': (K, F, P), 'c6': (F, F, F), 'c7': (N, P, F)})
    a, b = C.comparator_passes_and_ocs_does_not(t, OCS)
    assert [(x['case'], x['comparators']) for x in a] == [('c1', [OPA]), ('c5', [GRAPH])]
    assert [(x['case'], x['comparators']) for x in b] == [('c2', [OPA, GRAPH]), ('c7', [OPA])]
    assert C.comparator_passes_and_ocs_does_not(table_with({'c4': (P, P, P)}), OCS) == ([], [])
