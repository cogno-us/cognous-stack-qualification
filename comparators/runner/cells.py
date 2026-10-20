"""Cell aggregation for the comparison tables (pre-registration RP-4, RP-5; amendments 74 and 76).

Pure functions on plain data: no adapter is imported or run here.

Vocabulary of a cell: pass, fail, not expressible, not claimed, could not check, not asked (and masked, for plumbing runs whose
verdicts are discarded). Rules:

  * a scenario is asked of a configuration, not expressible, not claimed, or not asked; the state comes from the plan file and, for
    the protected destination, from the declarations file; a declaration without a citation is void and the scenario is asked;
  * an asked scenario passes when every trial passes; it is could-not-check when a trial raised or when fewer trials than expected
    were recorded (never a pass); otherwise it fails;
  * a case cell is fail if any asked scenario failed, could not check if none failed and any could not be checked, pass if at least
    one scenario was asked and all asked passed (the cell carries `asked k of n`), and, when none was asked, not claimed if every
    scenario that was declared at all is not claimed, not asked if every scenario is not asked, and not expressible otherwise
    (the cell carries the counts so that a mixed cell is visible);
  * a scenario declared not claimed that was run keeps its observation apart: it is listed in `unscored_observations` and is
    never part of a pass fraction.
"""
from collections import Counter

ASKED, NE, NC, UNASKED = 'ASKED', 'NOT-EXPRESSIBLE', 'NOT-CLAIMED', 'UNASKED'
PASS, FAIL, NOT_EXPRESSIBLE, NOT_CLAIMED, COULD_NOT_CHECK, NOT_ASKED, MASKED = (
    'pass', 'fail', 'not expressible', 'not claimed', 'could not check', 'not asked', 'masked')
LABEL = {NE: NOT_EXPRESSIBLE, NC: NOT_CLAIMED, UNASKED: NOT_ASKED}


class DeclarationConflict(Exception):
    pass


def _cited(entry):
    return isinstance(entry, dict) and bool(entry.get('citations'))


def scenario_states(plan, ocs_profile, declarations):
    """State of every scenario of the plan for every configuration.

    Returns {profile: {scenario_id: record}}; a record has status, run (bool), scored (bool), reason, citations, origin, void.
    The profiles are those of the plan plus the protected destination."""
    profiles = list(plan['profiles'])
    if ocs_profile not in profiles:
        profiles = [ocs_profile] + profiles
    decl_by_id = {r['scenario']: r for r in (declarations or {}).get('records', [])}
    states = {p: {} for p in profiles}
    for case in plan['cases']:
        per = case.get('per_configuration') or {}
        for p in profiles:
            if p == ocs_profile:
                d = decl_by_id.get(case['id'])
                if d is None:
                    raise DeclarationConflict('no declaration for scenario %s' % case['id'])
                entry = per.get(p)
                if isinstance(entry, str) and entry.upper().startswith(NC) and d['status'] != NC:
                    raise DeclarationConflict('%s: the plan file says not claimed for the destination, the declaration says %s' % (case['id'], d['status']))
                states[p][case['id']] = dict(status=d['status'], run=d['status'] == ASKED or bool(d.get('run_anyway')), scored=d['status'] == ASKED,
                                             reason=d['reason'], reason_code=d['reason_code'], citations=d['citations'], origin='declarations file', void=False)
                continue
            entry = per.get(p)
            if isinstance(entry, dict) and entry.get('status') in (NE, NC):
                if _cited(entry):
                    states[p][case['id']] = dict(status=entry['status'], run=entry['status'] == NC, scored=False, reason=entry.get('reason', ''),
                                                 reason_code=entry.get('reason_code'), citations=entry['citations'], origin='plan file', void=False)
                    continue
                states[p][case['id']] = dict(status=ASKED, run=True, scored=True, reason='declaration without a citation is void; asked', reason_code=None,
                                             citations=[], origin='plan file', void=True)
                continue
            states[p][case['id']] = dict(status=ASKED, run=True, scored=True, reason='', reason_code=None, citations=[], origin='plan file', void=False)
    for item in plan['non_executed']:
        status = item['state'] if item['state'] in (NE, NC, UNASKED) else UNASKED
        for p in profiles:
            states[p][item['id']] = dict(status=status, run=False, scored=False, reason=item.get('reason', ''), reason_code=item.get('reason_code'),
                                         citations=item.get('citations', []), origin='plan file (no executable steps)', void=False, plan_level=True)
    return states


def scenario_outcome(state, rows, expected_trials):
    """Outcome of one scenario for one configuration from its trial rows."""
    if state['status'] != ASKED:
        out = dict(outcome=LABEL.get(state['status'], NOT_ASKED), trials=0, passed=0)
        if rows:  # a not-claimed scenario that was run: observation only
            out['observation'] = observation(rows)
        return out
    if not rows:
        return dict(outcome=COULD_NOT_CHECK, trials=0, passed=0, detail='no trial recorded')
    errors = [r for r in rows if r.get('error')]
    if errors:
        return dict(outcome=COULD_NOT_CHECK, trials=len(rows), passed=0, detail='; '.join(sorted({r['error'][:160] for r in errors})))
    if len(rows) < expected_trials:
        return dict(outcome=COULD_NOT_CHECK, trials=len(rows), passed=0, detail='incomplete: %d of %d trials recorded' % (len(rows), expected_trials))
    if all(r.get('mode') == 'masked' for r in rows):
        return dict(outcome=MASKED, trials=len(rows), passed=None)
    passed = sum(bool(r['pass_case']) for r in rows)
    return dict(outcome=PASS if passed == len(rows) else FAIL, trials=len(rows), passed=passed, reasons=refusal_reasons(rows))


def observation(rows):
    errors = [r for r in rows if r.get('error')]
    if all(r.get('mode') == 'masked' for r in rows):
        return dict(trials=len(rows), executed=sum(1 for r in rows if not r.get('error')), errors=len(errors))
    ok = [r for r in rows if not r.get('error')]
    return dict(trials=len(rows), errors=len(errors), observed_equal_to_expected=sum(bool(r['pass_case']) for r in ok),
                reasons=refusal_reasons(ok))


def refusal_reasons(rows):
    c = Counter()
    for r in rows:
        for o in r.get('outputs', []):
            if o.get('status') != 'accepted':
                c['%s: %s' % (o.get('status'), o.get('reason') or '(no reason)')] += 1
    return dict(sorted(c.items()))


def case_cell(scenario_ids, states_for_profile, outcomes):
    """Cell of one case for one configuration. outcomes: {scenario_id: scenario_outcome}."""
    n = len(scenario_ids)
    status = Counter(states_for_profile[s]['status'] for s in scenario_ids)
    asked = [s for s in scenario_ids if states_for_profile[s]['status'] == ASKED]
    results = [outcomes[s]['outcome'] for s in asked]
    if asked:
        if COULD_NOT_CHECK in results:
            outcome = COULD_NOT_CHECK
        elif FAIL in results:
            outcome = FAIL
        elif all(x == MASKED for x in results):
            outcome = MASKED
        else:
            outcome = PASS
    else:
        declared = [s for s in scenario_ids if states_for_profile[s]['status'] in (NE, NC)]
        if not declared:
            outcome = NOT_ASKED
        elif all(states_for_profile[s]['status'] == NC for s in declared):
            outcome = NOT_CLAIMED
        else:
            outcome = NOT_EXPRESSIBLE
    trials = sum(outcomes[s]['trials'] for s in asked)
    passed = sum(outcomes[s]['passed'] or 0 for s in asked)
    reasons = Counter()
    for s in asked:
        reasons.update(outcomes[s].get('reasons', {}))
    return dict(outcome=outcome, asked=len(asked), of=n, not_expressible=status[NE], not_claimed=status[NC], not_asked=status[UNASKED],
                trials=trials, trials_passed=passed, refusal_reasons=dict(sorted(reasons.items())),
                scenarios={s: dict(state=states_for_profile[s]['status'], **outcomes[s]) for s in scenario_ids})


ORACLE_FIELDS = ('unexpected_effect_count', 'missing_effect_count', 'false_allows', 'false_blocks', 'denied_calls', 'durably_recorded_denials')


def oracle_counts(rows):
    """The counts the oracle already reports (RP-5) over scored rows: sums of its own fields, no scoring here."""
    scored = [r for r in rows if r.get('mode') == 'scored' and not r.get('error')]
    out = dict(case_trials=len(scored), passed=sum(bool(r['pass_case']) for r in scored))
    for f in ORACLE_FIELDS:
        out[f] = sum(r[f] for r in scored)
    return out


def scenario_counts(scenario_ids, states_for_profile, outcomes):
    """Per-configuration counts for a set: asked, not expressible, not claimed, not asked, could not check (RP-4, amendment 83)."""
    out = dict(scenarios=len(scenario_ids), asked=0, not_expressible=0, not_expressible_plan_level=0, not_claimed=0, not_asked=0, could_not_check=0)
    for s in scenario_ids:
        st = states_for_profile[s]
        if st['status'] == ASKED:
            out['asked'] += 1
            if outcomes[s]['outcome'] == COULD_NOT_CHECK:
                out['could_not_check'] += 1
        elif st['status'] == NE:
            out['not_expressible'] += 1
            if st.get('plan_level'):
                out['not_expressible_plan_level'] += 1
        elif st['status'] == NC:
            out['not_claimed'] += 1
        else:
            out['not_asked'] += 1
    return out


def build_set(name, cases, profiles, states, rows, expected_trials, ocs_profile):
    """Table of one set.

    cases: [{'id', 'title', 'scenarios': [scenario ids]}] in table order; states: scenario_states() result (all-asked for the registered sets);
    rows: trial rows ({case_id (= scenario id), profile, mode, ...}); expected_trials: trials expected per asked scenario."""
    by_key = {}
    for r in rows:
        by_key.setdefault((r['profile'], r['case_id']), []).append(r)
    table = dict(set=name, profiles=list(profiles), cases=[], counts={}, oracle_counts={}, unscored_observations=[], expected_trials=expected_trials)
    all_ids = [s for c in cases for s in c['scenarios']]
    outcomes_by_profile = {}
    for p in profiles:
        outcomes_by_profile[p] = {s: scenario_outcome(states[p][s], by_key.get((p, s), []), expected_trials) for s in all_ids}
        table['counts'][p] = scenario_counts(all_ids, states[p], outcomes_by_profile[p])
        scored_rows = [r for r in rows if r['profile'] == p and states[p].get(r['case_id'], {}).get('status') == ASKED]
        table['oracle_counts'][p] = oracle_counts(scored_rows) if not any(r.get('mode') == 'masked' for r in rows) else None
    for c in cases:
        row = dict(id=c['id'], title=c.get('title', c['id']), scenarios=c['scenarios'], cells={})
        for p in profiles:
            row['cells'][p] = case_cell(c['scenarios'], states[p], outcomes_by_profile[p])
        table['cases'].append(row)
    for p in profiles:
        for s in all_ids:
            o = outcomes_by_profile[p][s]
            if 'observation' in o:
                st = states[p][s]
                table['unscored_observations'].append(dict(profile=p, scenario=s, status=st['status'], reason=st['reason'], citations=st['citations'],
                                                          observation=o['observation']))
    return table


def comparator_passes_and_ocs_does_not(table, ocs_profile):
    """Case ids for the RP-6 block, in two lists: (a) a comparator cell is pass and the destination cell is fail or could not check;
    (b) a comparator cell is pass and the destination cell is not expressible or not claimed (neither a pass nor a fail)."""
    a, b = [], []
    comparators = [p for p in table['profiles'] if p != ocs_profile]
    for row in table['cases']:
        ocs = row['cells'][ocs_profile]['outcome']
        passing = [p for p in comparators if row['cells'][p]['outcome'] == PASS]
        if not passing:
            continue
        if ocs in (FAIL, COULD_NOT_CHECK):
            a.append(dict(case=row['id'], comparators=passing, ocs=ocs))
        elif ocs in (NOT_EXPRESSIBLE, NOT_CLAIMED):
            b.append(dict(case=row['id'], comparators=passing, ocs=ocs))
    return a, b
