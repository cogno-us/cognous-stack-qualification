"""Per-scenario and per-principal reporting over RECORDED test results (C13). Read-only; no pass/fail logic.

SPDX-License-Identifier: Apache-2.0

Reads the JUnit files already retained under ``results/v1-validation/<validation>/<run>/jobs/<job>/`` and reports each scenario
and each principal on its own line instead of one pooled count. It never executes a test, never calls the controller or the
aggregate, and never decides a verdict: an outcome is ``failed`` when the JUnit case has a failure or error element, ``skipped``
when it has a skipped element, otherwise ``passed`` (the same rule ``tools/v1_validation.py`` uses to index cases).

Scenario unit: ``test_scn_cNN`` / ``test_scn_dNN`` modules map to the catalog id (``C03``); ``test_asw_x`` to ``ASW-X`` and
``test_add_*`` to ``ADD-*`` (addenda, not catalog scenarios); anything else keeps its module name.

Principal unit: the principal is reported only when the case recorded it, as a JUnit property named ``principal`` (the refusal
template and new suites record it). Cases that did not record one are counted under ``unrecorded``; no principal is derived
from a test name. Separately, ``identity_dimension_hint`` lists the identity dimension a parametrised test id names
(principal, actor, tenant, agent). That column is inferred from the id text, is not an attribution, and is labelled as such.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

UNRECORDED = 'unrecorded'
HINT_TOKENS = ('principal', 'actor', 'tenant', 'agent')


def scenario_unit(classname: str) -> str:
    module = classname.split('.')[-1]
    m = re.fullmatch(r'test_scn_([cd]\d+)', module)
    if m:
        return m.group(1).upper()
    m = re.fullmatch(r'test_asw_([a-z])', module)
    if m:
        return 'ASW-' + m.group(1).upper()
    m = re.fullmatch(r'test_add_(.+)', module)
    if m:
        return 'ADD-' + m.group(1).upper().replace('_', '-')
    return module


def outcome(case) -> str:
    if case.find('failure') is not None or case.find('error') is not None:
        return 'failed'
    return 'skipped' if case.find('skipped') is not None else 'passed'


def identity_hint(name: str) -> list[str]:
    m = re.search(r'\[(.*)\]$', name)
    text = (m.group(1) if m else '').lower()
    return [t for t in HINT_TOKENS if t in text]


def read_cases(junit: Path, job: str) -> list[dict]:
    cases = []
    for tc in ET.parse(junit).getroot().iter('testcase'):
        props = {p.get('name'): p.get('value') for p in (tc.find('properties') if tc.find('properties') is not None else [])}
        principal = (props.get('principal') or '').strip() or UNRECORDED
        cases.append({'job': job, 'unit': scenario_unit(tc.get('classname', '')), 'test': tc.get('name', ''),
                      'assertion': re.sub(r'\[.*\]$', '', tc.get('name', '')), 'outcome': outcome(tc),
                      'principal': principal, 'hint': identity_hint(tc.get('name', ''))})
    return cases


def _tally(cases) -> dict:
    out = {'cases': len(cases), 'passed': 0, 'failed': 0, 'skipped': 0}
    for c in cases:
        out[c['outcome']] += 1
    return out


def build(run_dir: Path, jobs: tuple[str, ...] = ('scenarios',)) -> dict:
    """Report for the JUnit files of ``jobs`` under ``run_dir/jobs``. Rows are sorted; nothing is pooled across scenarios."""
    cases = []
    for job in jobs:
        files = sorted((run_dir/'jobs'/job).glob('junit*.xml'))[-1:]
        if not files:
            raise FileNotFoundError(f'no JUnit file for job {job} under {run_dir}')
        cases += read_cases(files[0], job)
    by_unit: dict[str, list] = {}
    for c in cases:
        by_unit.setdefault(c['unit'], []).append(c)
    scenarios = []
    for unit in sorted(by_unit):
        rows = by_unit[unit]
        assertions = {}
        for c in rows:
            assertions.setdefault(c['assertion'], []).append(c)
        principals = {}
        for c in rows:
            principals.setdefault(c['principal'], []).append(c)
        scenarios.append({'scenario': unit, **_tally(rows),
                          'failed_tests': [c['test'] for c in rows if c['outcome'] == 'failed'],
                          'assertions': [{'assertion': a, **_tally(v)} for a, v in sorted(assertions.items())],
                          'principals': {p: _tally(v) for p, v in sorted(principals.items())}})
    principal_rows = {}
    for c in cases:
        principal_rows.setdefault(c['principal'], []).append(c)
    per_principal = []
    for p in sorted(principal_rows):
        rows = principal_rows[p]
        per_principal.append({'principal': p, **_tally(rows),
                              'scenarios': {u: _tally([c for c in rows if c['unit'] == u]) for u in sorted({c['unit'] for c in rows})},
                              'failed_tests': [c['test'] for c in rows if c['outcome'] == 'failed']})
    hints = {}
    for c in cases:
        for h in c['hint'] or ['none']:
            hints.setdefault(h, []).append(c)
    return {'run_dir': run_dir.as_posix(), 'jobs': list(jobs), 'reading': 'recorded JUnit outcomes of test cases; not scenario acceptance',
            'totals': _tally(cases),
            'per_scenario': scenarios, 'per_principal': per_principal,
            'principal_attribution': {'recorded': sum(1 for c in cases if c['principal'] != UNRECORDED), 'unrecorded': sum(1 for c in cases if c['principal'] == UNRECORDED)},
            'identity_dimension_hint': {'basis': 'inferred from the parametrised test id text; not recorded by the case and not an attribution',
                                        'rows': [{'dimension': h, **_tally(v)} for h, v in sorted(hints.items())]}}


def markdown(report: dict, titles: dict | None = None) -> str:
    titles = titles or {}
    lines = ['| Scenario | Cases | Passed | Failed | Skipped | Failing cases |', '|---|---:|---:|---:|---:|---|']
    for s in report['per_scenario']:
        label = s['scenario'] + (f" {titles[s['scenario']]}" if s['scenario'] in titles else '')
        failing = '; '.join(f'`{t}`' for t in s['failed_tests'][:4]) + (f" (+{len(s['failed_tests'])-4})" if len(s['failed_tests']) > 4 else '')
        lines.append(f"| {label.replace('|', '/')} | {s['cases']} | {s['passed']} | {s['failed']} | {s['skipped']} | {failing or '-'} |")
    pa = report['principal_attribution']
    lines += ['', f"Principal attribution: {pa['recorded']} cases recorded a principal, {pa['unrecorded']} did not (`{UNRECORDED}`). No principal is derived from a test name.", '',
              '| Principal | Cases | Passed | Failed | Skipped |', '|---|---:|---:|---:|---:|']
    for p in report['per_principal']:
        lines.append(f"| {p['principal']} | {p['cases']} | {p['passed']} | {p['failed']} | {p['skipped']} |")
    lines += ['', f"Identity dimension named in the test id (inferred from the id text, not an attribution):", '',
              '| Dimension | Cases | Passed | Failed | Skipped |', '|---|---:|---:|---:|---:|']
    for h in report['identity_dimension_hint']['rows']:
        lines.append(f"| {h['dimension']} | {h['cases']} | {h['passed']} | {h['failed']} | {h['skipped']} |")
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('run_dir', type=Path, help='a retained run directory containing jobs/<job>/junit*.xml')
    ap.add_argument('--job', action='append', default=None, help='job directory name (default: scenarios); repeatable')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    report = build(args.run_dir, tuple(args.job or ['scenarios']))
    print(json.dumps(report, indent=2) if args.json else markdown(report))


if __name__ == '__main__':
    main()
