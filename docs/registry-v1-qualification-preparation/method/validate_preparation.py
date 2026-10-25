#!/usr/bin/env python3
"""Validates the V1 qualification-preparation data and writes 04a-computed-coverage.md.

SPDX-License-Identifier: Apache-2.0
Usage: validate_preparation.py <PACKAGE_DIR> <CROSSWALK_CSV>   (stdlib only; reads and writes only inside PACKAGE_DIR)

Checks structure and cross-references only. It executes no test and asserts nothing about any implementation.
Exit status is non-zero on any failed check.
"""
import csv, json, re, sys, collections as C

P = sys.argv[1].rstrip('/') + '/'
XW = sys.argv[2]
GATES = ['QG-%02d' % i for i in range(1, 15)]
V1_FIELDS = {'allowed_actions', 'allowed_adapters', 'allowed_units', 'allowed_institutions', 'allowed_authority_domains',
             'status_max_age_seconds', 'approval_max_age_seconds', 'ActionClass.max_status_age_seconds', 'NONE'}
STATUS = {'PREPARED', 'BLOCKED_ON_CONTRACT'}
BASIS = {'CONTRACT', 'RULING', 'SOURCE_CHARACTERIZATION', 'INVENTORY'}
ID_RE = {'oracles': r'^QO-\d{3}$', 'negative-controls': r'^NC-\d{3}$', 'differential-cases': r'^DF-\d{3}$'}
ID_KEY = {'oracles': 'oracle_id', 'negative-controls': 'control_id', 'differential-cases': 'case_id'}
REQ = {
    'oracles': ['oracle_id', 'topic', 'title', 'gates', 'scope', 'field', 'expected_outcome', 'expected_cause', 'must_not', 'basis', 'basis_type', 'status'],
    'negative-controls': ['control_id', 'attack_class', 'title', 'gates', 'scope', 'field', 'synthetic_fixture', 'attack_step', 'expected_outcome', 'expected_exact_cause', 'must_not', 'evidence_to_retain', 'mutation_leg', 'basis', 'basis_type', 'status'],
    'differential-cases': ['case_id', 'title', 'gates', 'scope', 'field', 'baseline_pin', 'baseline_source', 'baseline_behaviour', 'candidate_comparison', 'comparison_type', 'expected_result_source', 'basis', 'basis_type', 'status'],
}
errs, notes = [], []
canon = {r['scenario_id']: r for r in csv.DictReader(open(XW))}
data = {}
for name in ID_RE:
    rows = []
    for n, line in enumerate(open(P + 'data/%s.jsonl' % name), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception as e:
            errs.append('%s:%d not JSON: %s' % (name, n, e))
    data[name] = rows
    ids = [r.get(ID_KEY[name]) for r in rows]
    if len(ids) != len(set(ids)):
        errs.append('%s: duplicate ids' % name)
    for r in rows:
        i = r.get(ID_KEY[name], '?')
        miss = [k for k in REQ[name] if k not in r or r[k] in (None, '', [])]
        miss = [k for k in miss if not (k in ('must_not', 'expected_cause') and r.get(k) == '')]
        if miss: errs.append('%s %s missing/empty %s' % (name, i, miss))
        if not re.match(ID_RE[name], str(i)): errs.append('%s bad id %s' % (name, i))
        if r.get('status') not in STATUS: errs.append('%s %s bad status %s' % (name, i, r.get('status')))
        if r.get('basis_type') not in BASIS: errs.append('%s %s bad basis_type %s' % (name, i, r.get('basis_type')))
        if r.get('status') == 'BLOCKED_ON_CONTRACT' and not r.get('blocked_on'): errs.append('%s %s blocked without blocked_on' % (name, i))
        g = r.get('gates') or []
        if 'QG-02' in g: errs.append('%s %s tags inactive QG-02' % (name, i))
        for x in g:
            if x not in GATES: errs.append('%s %s unknown gate %s' % (name, i, x))
        if r.get('field') not in V1_FIELDS: errs.append('%s %s field not a V1 field: %s' % (name, i, r.get('field')))
        txt = json.dumps(r)
        if re.search(r'max_amount', txt) and not re.search(r'(exclud|defer|inactive|not V1|out of V1|INACTIVE)', txt, re.I):
            errs.append('%s %s mentions max_amount without exclusion note' % (name, i))
        for k in ('crosswalk_scenario_ids', 'scenario_ids'):
            for s in r.get(k) or []:
                if s not in canon: errs.append('%s %s scenario id not in crosswalk: %s' % (name, i, s))
        if re.search(r'\bPASS(ED)?\b', str(r.get('status', ''))): errs.append('%s %s status claims PASS' % (name, i))

gd = json.load(open(P + 'data/gate-definitions.json'))
if [g['gate_id'] for g in gd] != GATES: errs.append('gate-definitions must list QG-01..QG-14 in order')
for g in gd:
    for s in g.get('source_scenario_ids') or []:
        sid = s if isinstance(s, str) else s.get('scenario_id')
        if sid not in canon: errs.append('%s scenario id not in crosswalk: %s' % (g['gate_id'], sid))
    if g['gate_id'] == 'QG-02' and g.get('v1_status') != 'INACTIVE_MAX_AMOUNT_DEFERRED': errs.append('QG-02 must be INACTIVE')
    if g['gate_id'] != 'QG-02' and g.get('v1_status') != 'ACTIVE': errs.append('%s must be ACTIVE' % g['gate_id'])

# computed coverage
cov = {g: C.Counter() for g in GATES}
for name, key in (('oracles', 'QO'), ('negative-controls', 'NC'), ('differential-cases', 'DF')):
    for r in data[name]:
        for g in r.get('gates') or []:
            if g in cov: cov[g][key] += 1
            if g in cov and r.get('status') == 'BLOCKED_ON_CONTRACT': cov[g][key + '_blocked'] += 1
cls = C.Counter(r['attack_class'] for r in data['negative-controls'])
out = ['# 4a. Computed coverage (generated by `method/validate_preparation.py`; do not edit)', '',
       'Counts are rows tagged with each gate. They count PREPARED expectations only. They are **not** execution results, not coverage of behaviour, and no gate is met. A row can be tagged with several gates, so column totals exceed row totals. `blocked` counts rows whose status is BLOCKED_ON_CONTRACT.', '',
       '| Gate | V1 status | Oracles (QO) | of which blocked | Negative controls (NC) | of which blocked | Differential cases (DF) | of which blocked | Gap |', '|---|---|---|---|---|---|---|---|---|']
stat = {g['gate_id']: g.get('v1_status') for g in gd}
for g in GATES:
    c = cov[g]
    gap = 'INACTIVE' if g == 'QG-02' else ('NO PREPARED ROWS' if not (c['QO'] or c['NC'] or c['DF']) else ('process gate: evidence-only' if g == 'QG-14' else ''))
    out.append('| %s | %s | %d | %d | %d | %d | %d | %d | %s |' % (g, stat.get(g, ''), c['QO'], c['QO_blocked'], c['NC'], c['NC_blocked'], c['DF'], c['DF_blocked'], gap))
out += ['', '## Totals', '', '| Item | Rows | PREPARED | BLOCKED_ON_CONTRACT |', '|---|---|---|---|']
for name, label in (('oracles', 'Oracles'), ('negative-controls', 'Negative controls'), ('differential-cases', 'Differential cases')):
    rs = data[name]; b = sum(1 for r in rs if r['status'] == 'BLOCKED_ON_CONTRACT')
    out.append('| %s | %d | %d | %d |' % (label, len(rs), len(rs) - b, b))
out += ['', '## Negative controls by attack class', '', '| Attack class | Controls |', '|---|---|']
for k, v in sorted(cls.items()): out.append('| %s | %d |' % (k, v))
if not errs:
    open(P + '04a-computed-coverage.md', 'w').write('\n'.join(out) + '\n')
print('FAIL' if errs else 'OK', {k: len(v) for k, v in data.items()}, len(gd), 'gates')
for e in errs[:60]: print(' ', e)
sys.exit(1 if errs else 0)
