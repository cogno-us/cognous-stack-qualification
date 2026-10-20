#!/usr/bin/env python3
"""Contract self-check of the comparison runner (comparator plan section 2: the scoring interface; amendments 76 and 79 for the declarations).

It uses no real configuration to produce a verdict. It checks that

  1. each configuration class of the Wiki subset provides every member that the registered runner drives (constructor, clock, keys,
     request, apply, zero-argument controls, snapshot) and refuses an unknown fault;
  2. three stubs (always accept, always deny, byte-echo of a correct fixture) receive the documented verdict from the registered `evaluate`
     on every executable scenario of the plan file, so every scenario is scorable and the durable denial term is satisfiable;
  3. the declarations of the protected-destination column cover the plan file, agree with the rules and cite sources that exist;
  4. the report generator carries the blocks that the pre-registration requires, including the block of RP-6 when no case qualifies;
  5. the cell aggregation labels the documented situations as documented.

Usage: SCN_HUB_DIR=<hub> python3 comparators/runner/contract_check.py [--plan P] [--declarations D]   (exit status 0 only when every check passes)
"""
import argparse
import inspect
import json
from pathlib import Path
import shutil
import sys
import tempfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO))
from comparators.runner import cells, ocs_column, report, run_core, stubs  # noqa: E402

PLAN = REPO / 'comparators/wiki/plans/wiki-subset-plan.json'
DECL = HERE / 'ocs-column-declarations.json'
REQUEST_FIELDS = set(ocs_column.REQUEST_FIELDS)
KEYS = {'admin', 'broker', 'verifier', 'agent'}
ZERO_ARG = ('revoke', 'fence', 'rotate', 'reopen', 'break_audit')


def members(cls, name, tmp, errors):
    sig = list(inspect.signature(cls.__init__).parameters)[1:]
    if sig[:3] != ['root', 'opa', 'mutation']:
        errors.append('%s: constructor must be (root, opa, mutation), found %s' % (name, sig))
    obj = cls(tmp / (name + '-members'), '/nonexistent-opa', None)
    for attr in ('now', 'serial'):
        if type(getattr(obj, attr, None)) is not int:
            errors.append('%s: public integer %s is missing' % (name, attr))
    if not KEYS <= set(getattr(obj, 'keys', {})):
        errors.append('%s: keys must hold %s' % (name, sorted(KEYS)))
    if not isinstance(getattr(obj, 'registry', None), dict):
        errors.append('%s: registry is missing' % name)
    for m in ('request', 'apply', 'snapshot') + ZERO_ARG:
        if not callable(getattr(obj, m, None)):
            errors.append('%s: member %s is missing' % (name, m))
    request = obj.request()
    arguments = request['body']['arguments']
    if set(arguments) != REQUEST_FIELDS:
        errors.append('%s: request arguments must be exactly the eight fields, found %s' % (name, sorted(arguments)))
    try:
        obj.request(None, 'no-such-fault')
        errors.append('%s: an unknown fault must raise' % name)
    except ValueError:
        pass
    snap = obj.snapshot()
    if set(snap) != {'effects', 'events'} or snap['effects'] != []:
        errors.append('%s: snapshot must hold effects and events, with no effect before any call' % name)
    try:
        getattr(obj, 'no_such_verb:x')()
        errors.append('%s: an unknown control verb must raise' % name)
    except (AttributeError, KeyError, ValueError):
        pass


def predicted(case, kind):
    """The verdict that a stub is documented to receive, derived from the case alone (no scoring code is repeated: only the plain consequence of
    what the stub does)."""
    calls = [s for s in case['steps'] if s['action'] == 'execute']
    ids = [s['args']['effect'] for s in calls]
    if kind == 'echo':
        return True
    if kind == 'deny':
        return all(x == 'denied' for x in case['expected_statuses']) and case['expected_effects'] == 0
    payloads_ok = all(s['args'].get('payload', 'synthetic') == case['expected_payload'] for s in calls)
    return (all(x == 'accepted' for x in case['expected_statuses']) and case['expected_effects'] == len(set(ids))
            and set(ids) <= set(case['allowed_effect_ids']) and payloads_ok)


def stub_checks(plan, tmp, errors):
    runner = run_core.load_runner()
    built = stubs.build_stubs()
    n = 0
    for case in plan['cases']:
        for kind in ('accept', 'deny', 'echo'):
            cls = built['echo_for'](case) if kind == 'echo' else built[kind]
            runner.ADAPTERS = {'stub-' + kind: cls}
            n += 1
            try:
                verdict = runner.run_case(cls, case, tmp / ('stub-%s-%s' % (kind, case['id'])), '/nonexistent-opa')
            except Exception as exc:  # noqa: BLE001
                errors.append('%s: the %s stub raised %s: %s' % (case['id'], kind, type(exc).__name__, str(exc)[:200]))
                continue
            want = predicted(case, kind)
            if verdict['pass_case'] != want:
                errors.append('%s: the %s stub received pass=%s, documented %s' % (case['id'], kind, verdict['pass_case'], want))
            if kind == 'deny' and verdict['denied_calls'] != verdict['durably_recorded_denials']:
                errors.append('%s: the deny stub left a denial without a durable record' % case['id'])
            if kind == 'accept' and verdict['denied_calls']:
                errors.append('%s: the accept stub denied a call' % case['id'])
    return n


def report_checks(errors):
    profiles = [ocs_column.OCS_PROFILE, run_core.OPA_PROFILE, run_core.GRAPH_PROFILE]
    states = {p: {'S1': dict(status=cells.ASKED, run=True, scored=True, reason='', reason_code=None, citations=[], origin='x', void=False)} for p in profiles}
    rows = [dict(case_id='S1', profile=p, mode='scored', repetition=0, seed=1701, pass_case=True, outputs=[], unexpected_effect_count=0,
                 missing_effect_count=0, false_allows=0, false_blocks=0, denied_calls=0, durably_recorded_denials=0) for p in profiles]
    table = cells.build_set('corner', [dict(id='S1', title='S1', scenarios=['S1'])], profiles, states, rows, 1, ocs_column.OCS_PROFILE)
    text = report.render([table], None)
    for needle in (report.SCOPE_TEXT, report.RP8_CAVEATS, 'Cases where a comparator passes and OCS does not (RP-6)', 'None.', 'Comparison table (RP-4)',
                   'Counts of the oracle (RP-5)', 'Run identity (RP-9)', 'Comparative statements (RP-7)', report.NE_NC_MEANING):
        if needle not in text:
            errors.append('report: missing text: ' + needle[:60])
    # a set on which a configuration has no scored result carries no comparative statement
    one = cells.build_set('corner', [dict(id='S1', title='S1', scenarios=['S1'])], profiles, states, rows[:2], 1, ocs_column.OCS_PROFILE)
    if 'Not evaluated' not in report.render([one], None):
        errors.append('report: a set without a scored result for every configuration must not carry a comparison')


def cell_checks(errors):
    A, NE, NC, U = cells.ASKED, cells.NE, cells.NC, cells.UNASKED

    def st(status):
        return dict(status=status, run=status == A, scored=status == A, reason='r', reason_code='c', citations=[], origin='x', void=False)

    def row(sid, ok=True, err=None):
        r = dict(case_id=sid, profile='p', mode='scored', repetition=0, seed=1701, pass_case=ok, outputs=[])
        if err:
            r['error'] = err
        return r
    cases = {
        'pass': ({'a': st(A), 'b': st(NE)}, [row('a')], cells.PASS), 'fail': ({'a': st(A), 'b': st(A)}, [row('a'), row('b', False)], cells.FAIL),
        'cnc-error': ({'a': st(A)}, [row('a', True, 'RuntimeError: x')], cells.COULD_NOT_CHECK), 'cnc-missing': ({'a': st(A)}, [], cells.COULD_NOT_CHECK),
        'ne': ({'a': st(NE), 'b': st(U)}, [], cells.NOT_EXPRESSIBLE), 'nc': ({'a': st(NC), 'b': st(U)}, [], cells.NOT_CLAIMED),
        'mixed': ({'a': st(NC), 'b': st(NE)}, [], cells.NOT_EXPRESSIBLE), 'unasked': ({'a': st(U)}, [], cells.NOT_ASKED)}
    for name, (states, rows, want) in cases.items():
        outcomes = {s: cells.scenario_outcome(states[s], [r for r in rows if r['case_id'] == s], 1) for s in states}
        got = cells.case_cell(sorted(states), states, outcomes)['outcome']
        if got != want:
            errors.append('cells: %s gave %s, documented %s' % (name, got, want))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--plan', type=Path, default=PLAN)
    ap.add_argument('--declarations', type=Path, default=DECL)
    args = ap.parse_args(argv)
    errors = []
    plan = json.loads(args.plan.read_text())
    decl = json.loads(args.declarations.read_text())
    tmp = Path(tempfile.mkdtemp(prefix='contract-'))
    try:
        from comparators.runner.run_wiki_subset import adapter_map
        run_core.load_runner()
        for name, cls in adapter_map().items():
            members(cls, name, tmp, errors)
        n = stub_checks(plan, tmp, errors)
        errors += ocs_column.check_declarations(plan, decl)
        report_checks(errors)
        cell_checks(errors)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for e in errors:
        print('FAIL ' + e)
    print('contract check: %d executable scenarios x 3 stubs = %d stub runs; %d problem(s)' % (len(plan['cases']), n, len(errors)))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
