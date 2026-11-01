#!/usr/bin/env python3
"""Top-level script of the pre-registered comparison: corner scenarios (19), baseline scenarios (24) and the Wiki subset, in the order of RO-6.

Corner and baseline run through the registered runner file (loaded by path after its digests are checked; its ADAPTERS mapping, `run_case`
and `evaluate` are used unchanged) on the registered plan files. The Wiki subset runs through run_wiki_subset.py. Each set is aggregated into
its own table; there is no aggregate across sets and no ranking. Every attempt is kept (RO-8): each set's results are written as soon as the
set has run.

Real run (all trials; this is the comparison and is never started by a test):
  SCN_HUB_DIR=<hub> python3 comparators/runner/run_comparison.py --opa <opa> --output <new dir> --confirm-real-run --candidate-id <id>
    [--sets corner,baseline,wiki] [--seeds 1701,1702] [--gate-status <json: test name -> status text>]
Plumbing only (renamed twins, verdicts discarded inside the run, nothing printed or stored about any outcome):
  SCN_HUB_DIR=<hub> python3 comparators/runner/run_comparison.py --opa <opa> --output <new dir> --plumbing
    --twins corner=ID,ID --twins baseline=ID,ID --twins wiki=ID,ID
Report again from retained results:
  python3 comparators/runner/run_comparison.py --report-only <results dir> --output <new dir>
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO))
from comparators.runner import cells, contract_check, ocs_column, report, run_core, run_wiki_subset  # noqa: E402

SUITE = REPO / run_core.SUITE_REL
REGISTERED_PLANS = {'corner': 'benchmarks/governance/corner-plan.json', 'baseline': 'benchmarks/governance/plan.json'}
ORDER = ('corner', 'baseline', 'wiki')
DIGESTS = HERE / 'digests.json'


def verify_freeze():
    """The files of the runner are those named in digests.json; the registered files are the pinned ones; the declarations are current."""
    problems = []
    listed = json.loads(DIGESTS.read_text())['files']
    for rel, want in listed.items():
        if run_core.sha256_file(REPO / rel) != want:
            problems.append('differs from comparators/runner/digests.json: ' + rel)
    for rel, want in run_core._base.PINNED_SHA256.items():
        if run_core.sha256_file(SUITE / rel) != want:
            problems.append('registered file differs from its pinned digest: ' + rel)
    return problems


def registered_set(name, opa, seeds, output, masked, twins=None, progress=None):
    plan = json.loads((SUITE / REGISTERED_PLANS[name]).read_text())
    runner = run_core.load_runner()
    mapping = dict(runner.ADAPTERS)
    if tuple(mapping) != run_core.PROFILES:
        raise RuntimeError('the registered runner lists other configurations than the pre-registration')
    cases = plan['cases']
    asked = dict(status=cells.ASKED, run=True, scored=True, reason='', reason_code=None, citations=[], origin='registered plan', void=False)
    if masked:
        cases, rename = run_core.twin_cases(plan['cases'], twins)
        states = {p: {t['id']: dict(asked, origin='masked twin') for t in cases} for p in mapping}
        table_cases = [dict(id=t['id'], title='(masked twin)', scenarios=[t['id']]) for t in cases]
        repetitions = 1
    else:
        states = {p: {c['id']: dict(asked) for c in cases} for p in mapping}
        table_cases = [dict(id=c['id'], title=c['id'], scenarios=[c['id']]) for c in cases]
        repetitions = plan['repetitions']
    rows = []
    for seed in seeds:
        rows += run_core.run_rows(runner, mapping, cases, states, seed, repetitions, opa, Path(output) / 'destinations', masked=masked, progress=progress)
    mutations = []
    if not masked:
        # the control-removal probes of the registered plan on the OPA application, as the registered runner runs them
        for mutation, case_id in plan['mutations'].items():
            case = next(c for c in plan['cases'] if c['id'] == case_id)
            try:
                verdict = runner.run_case(mapping[run_core.OPA_PROFILE], case, Path(output) / 'mutations' / mutation, opa, mutation)
                mutations.append(dict(mutation=mutation, case=case_id, detected=not verdict['pass_case']))
            except Exception as exc:  # noqa: BLE001
                mutations.append(dict(mutation=mutation, case=case_id, detected=None, error='%s: %s' % (type(exc).__name__, str(exc)[:300])))
    table = cells.build_set(name, table_cases, list(mapping), states, rows, repetitions * len(seeds), run_core.OCS_PROFILE)
    table['not_run'] = plan['not_run']
    table['control_removal_probes'] = mutations
    return dict(schema='cognous.comparators-set-results/1', set=name, masked=masked, seeds=list(seeds), repetitions=repetitions,
                plan=dict(path='%s/%s' % (run_core.SUITE_REL, REGISTERED_PLANS[name]), sha256=run_core.sha256_file(SUITE / REGISTERED_PLANS[name]),
                          cases=len(plan['cases'])), table=table, rows=rows)


def write_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=1) + '\n')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--opa', type=Path)
    ap.add_argument('--output', type=Path, required=True, help='a new directory (it must not exist)')
    ap.add_argument('--sets', default=','.join(ORDER))
    ap.add_argument('--seeds', default='1701,1702')
    ap.add_argument('--candidate-id')
    ap.add_argument('--confirm-real-run', action='store_true')
    ap.add_argument('--allow-dirty', action='store_true', help='record and continue when the working tree has uncommitted changes')
    ap.add_argument('--plumbing', action='store_true')
    ap.add_argument('--twins', action='append', default=[], help='set=ID,ID (plumbing only; may be repeated)')
    ap.add_argument('--report-only', type=Path, help='a results directory of an earlier run; no trial is run')
    ap.add_argument('--gate-status', type=Path)
    ap.add_argument('--crossref', type=Path, default=REPO / 'comparators/wiki/crossref/wiki-ocs-crossref.json')
    args = ap.parse_args(argv)
    sets = [s for s in args.sets.split(',') if s]
    if any(s not in ORDER for s in sets):
        raise SystemExit('sets are %s' % ', '.join(ORDER))
    sets = [s for s in ORDER if s in sets]
    out = args.output.resolve()
    gate_status = json.loads(args.gate_status.read_text()) if args.gate_status else None
    crossref = json.loads(args.crossref.read_text())
    if args.report_only:
        out.mkdir(parents=True, exist_ok=False)
        tables, identity = [], None
        for s in sets:
            f = args.report_only / s / 'results.json'
            if f.exists():
                data = json.loads(f.read_text())
                tables.append(data['table'])
                identity = data.get('identity') or identity
        manifest = args.report_only / 'run-manifest.json'
        if manifest.exists():
            identity = json.loads(manifest.read_text()).get('identity', identity)
        wiki_plan = json.loads((REPO / run_wiki_subset.PLAN_REL).read_text())
        wiki_decl = json.loads((REPO / run_wiki_subset.DECL_REL).read_text())
        text = report.render(tables, identity, plan=wiki_plan, decl=wiki_decl, crossref=crossref, gate_status=gate_status)
        (out / 'comparison-report.md').write_text(text)
        print('report written')
        return 0
    if args.opa is None:
        raise SystemExit('--opa is required')
    opa = str(args.opa.resolve())
    if not args.plumbing and not args.confirm_real_run:
        raise SystemExit('refusing to run the comparison: it needs --confirm-real-run; use --plumbing for a plumbing run')
    seeds = [int(x) for x in args.seeds.split(',')]
    if any(x not in (1701, 1702) for x in seeds):
        raise SystemExit('seeds are 1701 and 1702')
    twin_ids = {}
    for t in args.twins:
        name, _, ids = t.partition('=')
        twin_ids[name] = ids.split(',')
    out.mkdir(parents=True, exist_ok=False)
    wiki_plan_path = REPO / run_wiki_subset.PLAN_REL
    wiki_plan, wiki_decl, errors = run_wiki_subset.load_inputs(wiki_plan_path, REPO / run_wiki_subset.DECL_REL)
    if errors:
        print('the declarations of the protected-destination column are not current for the plan file:')
        print('\n'.join('  ' + e for e in errors))
        return 2
    run_core.preflight(opa)
    if not args.plumbing:
        problems = verify_freeze()
        git = run_core.git_info()
        if git['dirty'] and not args.allow_dirty:
            problems.append('the working tree has uncommitted changes (pass --allow-dirty to record them and continue)')
        if problems:
            print('freeze check failed:')
            print('\n'.join('  ' + p for p in problems))
            return 2
        if contract_check.main([]) != 0:
            print('the contract self-check failed; no set is run')
            return 2
    identity = None if args.plumbing else run_core.run_identity(
        {'corner': '%s/%s' % (run_core.SUITE_REL, REGISTERED_PLANS['corner']), 'baseline': '%s/%s' % (run_core.SUITE_REL, REGISTERED_PLANS['baseline']),
         'wiki': run_wiki_subset.PLAN_REL, 'ocs_column_declarations': run_wiki_subset.DECL_REL}, args.candidate_id)
    tables, raised = [], 0
    for name in sets:
        masked = args.plumbing
        if masked and name not in twin_ids:
            raise SystemExit('a plumbing run needs --twins %s=ID,ID' % name)
        if name == 'wiki':
            result = run_wiki_subset.run(wiki_plan, wiki_decl, opa, out / name, seeds[:1] if masked else seeds, 1 if masked else wiki_plan['repetitions'],
                                         twin_ids.get(name) if masked else None, args.candidate_id)
        else:
            result = registered_set(name, opa, seeds[:1] if masked else seeds, out / name, masked, twin_ids.get(name))
        write_json(out / name / 'results.json', result)
        tables.append(result['table'])
        raised += sum(1 for r in result['rows'] if r.get('error')) if masked else 0
        if not masked:
            print('set %s done: %s' % (name, json.dumps({p: result['table']['counts'][p] for p in result['table']['counts']})))
    text = report.render(tables, identity, masked=args.plumbing, plan=wiki_plan, decl=wiki_decl, crossref=crossref, gate_status=gate_status)
    (out / ('plumbing-report.md' if args.plumbing else 'comparison-report.md')).write_text(text)
    write_json(out / 'run-manifest.json', dict(identity=identity, sets=sets, seeds=seeds, plumbing=args.plumbing,
                                               report_sha256=hashlib.sha256(text.encode()).hexdigest()))
    if args.plumbing:
        print('plumbing: %d trial(s) raised' % raised)
        return 1 if raised else 0
    return 0


if __name__ == '__main__':
    sys.exit(main())
