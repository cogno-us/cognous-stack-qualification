#!/usr/bin/env python3
"""Entry point of the Wiki subset: runs the executable scenarios of the plan file (PR-6) on the three configurations and aggregates the cells.

Configurations: the protected destination (column adapter of ocs_column.py, destination-only comparison of amendment 76), the OPA
application and the LangGraph plus OPA application of the Wiki comparator. The scoring code is the registered runner file, loaded by path
after its digests are checked. Scenario counts, states and trial numbers are read from the plan file and the declarations file; nothing
here depends on how many scenarios the plan holds.

A scenario is run on a configuration only when its state says so: asked scenarios are run and scored; a scenario declared not claimed
that can technically be run is run and kept apart as an unscored observation (amendment 74); a scenario that is not expressible or not
asked is not run.

Real run (all trials of the plan; needs the pinned dependencies, the pinned OPA binary and SCN_HUB_DIR):
  SCN_HUB_DIR=<hub> python3 comparators/runner/run_wiki_subset.py --opa <opa> --output <new dir> --confirm-real-run [--seed 1701 --seed 1702]
Plumbing only (renamed twins of the named scenarios; verdicts are discarded inside the run and never printed or stored):
  SCN_HUB_DIR=<hub> python3 comparators/runner/run_wiki_subset.py --opa <opa> --output <new dir> --twins ID,ID,...
"""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO))
from comparators.runner import cells, ocs_column, run_core  # noqa: E402

PLAN_REL = 'comparators/wiki/plans/wiki-subset-plan.json'
DECL_REL = 'comparators/runner/ocs-column-declarations.json'
RESULT_SCHEMA = 'cognous.comparators-wiki-results/1'


def load_inputs(plan_path, decl_path, check_sources=True):
    plan = json.loads(Path(plan_path).read_text())
    decl = json.loads(Path(decl_path).read_text())
    errors = ocs_column.check_declarations(plan, decl, require_sources=check_sources)
    return plan, decl, errors


def case_table_rows(plan):
    """The cases of the plan in table order, each with every scenario of the case (executable or not)."""
    by_case = {}
    titles = {}
    for item in list(plan['cases']) + list(plan['non_executed']):
        by_case.setdefault(item['wiki_case_id'], []).append(item['id'])
        titles[item['wiki_case_id']] = item['case_title']
    return [dict(id=cid, title=titles[cid], scenarios=sorted(ids)) for cid, ids in sorted(by_case.items())]


def adapter_map():
    from comparators.wiki.harness.registered_sets import wiki_adapters_opa_only, wiki_adapters_langgraph
    (opa_id, opa_cls), = wiki_adapters_opa_only().items()
    (graph_id, graph_cls), = wiki_adapters_langgraph().items()
    if (opa_id, graph_id) != (run_core.OPA_PROFILE, run_core.GRAPH_PROFILE):
        raise RuntimeError('unexpected profile ids of the comparator applications')
    return {run_core.OCS_PROFILE: ocs_column.build_adapter_class(), opa_id: opa_cls, graph_id: graph_cls}


def run(plan, decl, opa, output, seeds, repetitions, twins=None, candidate_id=None, progress=None):
    """Run the set; returns the results dictionary (also written by main)."""
    masked = twins is not None
    runner = run_core.load_runner()
    states = cells.scenario_states(plan, run_core.OCS_PROFILE, decl)
    mapping = adapter_map()
    if sorted(states) != sorted(mapping):
        raise RuntimeError('configurations of the plan and of the adapters differ')
    cases = plan['cases']
    table_cases = case_table_rows(plan)
    if masked:
        cases, rename = run_core.twin_cases(plan['cases'], twins)
        scrub = lambda st: dict(st, reason='(masked)', citations=[], origin='masked twin')  # noqa: E731
        states = {p: {rename[s]: scrub(states[p][s]) for s in rename} for p in states}
        table_cases = [dict(id=t['id'], title='(masked twin)', scenarios=[t['id']]) for t in cases]
    preflight = run_core.preflight(opa)
    rows = []
    for seed in seeds:
        rows += run_core.run_rows(runner, mapping, cases, states, seed, repetitions, opa, Path(output) / 'destinations', masked=masked,
                                  progress=progress)
    expected = repetitions * len(seeds)
    table = cells.build_set('wiki', table_cases, list(mapping), states, rows, expected, run_core.OCS_PROFILE)
    result = dict(schema=RESULT_SCHEMA, set='wiki', masked=masked, seeds=list(seeds), repetitions=repetitions,
                  identity=run_core.run_identity({'wiki': PLAN_REL, 'ocs_column_declarations': DECL_REL}, candidate_id) if not masked else None,
                  preflight=preflight, plan_counts=plan['counts_per_state'], plan_scenarios_total=plan['scenarios_total'],
                  plan_scope_text=plan['scope_text'], plan_declarations=plan['declarations'], plan_not_run=plan['not_run'],
                  ocs_declarations_plan_sha256=decl['plan']['sha256'], table=table, rows=rows)
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--opa', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True, help='a new directory (it must not exist)')
    ap.add_argument('--plan', type=Path, default=REPO / PLAN_REL)
    ap.add_argument('--declarations', type=Path, default=REPO / DECL_REL)
    ap.add_argument('--seed', type=int, action='append', choices=[1701, 1702], help='default: the seeds of the plan file')
    ap.add_argument('--repetitions', type=int, help='default: the repetitions of the plan file (plumbing runs default to 1)')
    ap.add_argument('--twins', help='comma-separated scenario ids to drive as renamed twins with verdicts discarded (plumbing only)')
    ap.add_argument('--confirm-real-run', action='store_true', help='required for any run that is not a plumbing run')
    ap.add_argument('--candidate-id')
    args = ap.parse_args(argv)
    if args.twins is None and not args.confirm_real_run:
        raise SystemExit('refusing to run the plan: a real run needs --confirm-real-run; use --twins for a plumbing run')
    plan, decl, errors = load_inputs(args.plan, args.declarations)
    if errors:
        print('declarations are not current for the plan file:')
        for e in errors:
            print('  ' + e)
        return 2
    masked = args.twins is not None
    seeds = args.seed or (plan['seeds'][:1] if masked else plan['seeds'])
    repetitions = args.repetitions or (1 if masked else plan['repetitions'])
    twins = args.twins.split(',') if masked else None
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    result = run(plan, decl, str(args.opa.resolve()), output, seeds, repetitions, twins, args.candidate_id)
    (output / 'results.json').write_text(json.dumps(result, indent=1) + '\n')
    from comparators.runner import report
    (output / 'summary.md').write_text(report.render([result['table']], result.get('identity'), masked=masked, plan=plan, decl=decl, extra=result))
    if masked:
        errors = [r for r in result['rows'] if r.get('error')]
        executed = len(result['rows']) - len(errors)
        print('twins driven: %d scenarios; trials executed: %d; raised: %d' % (len(args.twins.split(',')), executed, len(errors)))
        for r in errors:
            print('  RAISED', r['case_id'], r['profile'], r['error'][:200])
        return 1 if errors else 0
    print(json.dumps({p: result['table']['counts'][p] for p in result['table']['counts']}, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
