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
        if r.get('result_kind') not in ('PROTECTION', 'PAIR_CONTROL', 'DISCLOSURE_ONLY'): errs.append('%s %s bad result_kind %s' % (name, i, r.get('result_kind')))
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
        sid = s if isinstance(s, str) else (s.get('id') or s.get('scenario_id'))
        if sid not in canon: errs.append('%s scenario id not in crosswalk: %s' % (g['gate_id'], sid))
    if g['gate_id'] == 'QG-02' and g.get('v1_status') != 'INACTIVE_MAX_AMOUNT_DEFERRED': errs.append('QG-02 must be INACTIVE')
    if g['gate_id'] != 'QG-02' and g.get('v1_status') != 'ACTIVE': errs.append('%s must be ACTIVE' % g['gate_id'])

# every control-class slug named by a gate must be covered by at least one prepared control class
SLUG_TO_CLASSES = {
    'forged_selection': ['forged_selection'], 'substituted_digest': ['policy_digest_substitution'],
    'mismatched_claim_identity': ['claim_identity_mismatch'], 'expired_selection': ['expiry'], 'revoked_selection': ['revocation'],
    'required_absence': ['required_policy_absence', 'scope_required_ratchet', 'invalid_optional_as_withdrawal'],
    'epoch_downgrade': ['epoch_downgrade', 'trust_snapshot_version'], 'concurrent_revocation': ['concurrent_revocation'],
    'stale_approval_revival': ['stale_approval_revival'], 'restore_rollback': ['restore_rollback'],
    'durable_state_missing_or_corrupt': ['durable_state_loss'], 'registry_denyall_vs_evaluator_denial': ['deny_all_vs_evaluator'],
    'invalid_freshness_input': ['freshness_invalid_input', 'freshness_boundary'], 'outage_extension_widening': ['outage_extension'],
    'confused_deputy': ['confused_deputy'], 'string_based_decision': ['string_decision'], 'route_a_not_credited': ['route_a_bypass']}
_have = {r['attack_class'] for r in data['negative-controls']}
for g in gd:
    for slug in g.get('expected_negative_controls') or []:
        if slug not in SLUG_TO_CLASSES: errs.append('%s unknown control slug %s' % (g['gate_id'], slug))
        elif not (set(SLUG_TO_CLASSES[slug]) & _have): errs.append('%s slug %s has no prepared control class' % (g['gate_id'], slug))
        else:
            ok = [r for r in data['negative-controls'] if r['attack_class'] in SLUG_TO_CLASSES[slug] and g['gate_id'] in r['gates']]
            if not ok: notes.append('%s expects %s but no control of that class is tagged to it' % (g['gate_id'], slug))

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
CLS = {'MISSING REQUIRED CONTROL', 'EXISTING CONTROL NEEDS TAGGING', 'CONTRACT-BLOCKED', 'JUSTIFIED NOT APPLICABLE'}
gc = json.load(open(P + 'data/coverage-gap-classification.json'))['gaps']
gmap = {}
for e in gc:
    k = (e['gate_id'], e['control_slug'])
    if k in gmap: errs.append('duplicate gap classification %s' % (k,))
    gmap[k] = e
    if e.get('classification') not in CLS: errs.append('bad gap classification %s' % (k,))
    if e.get('classification') == 'JUSTIFIED NOT APPLICABLE' and not e.get('justification_source'): errs.append('N/A without justification_source %s' % (k,))
    if e.get('classification') == 'CONTRACT-BLOCKED' and not e.get('blocked_on'): errs.append('contract-blocked gap without blocked_on %s' % (k,))
computed = set()
for n in notes:
    gate, rest = n.split(' expects ', 1)
    computed.add((gate, rest.split(' but no control')[0]))
for k in computed - set(gmap): errs.append('gap without classification %s' % (k,))
for k in set(gmap) - computed: errs.append('classification for a gap that no longer exists %s' % (k,))
out += ['', '## Gate-to-control-class tagging gaps', '',
        'Each line is a control class that the gate definition (`data/gate-definitions.json`, `expected_negative_controls`) expects but for which no prepared control is tagged to that gate. All gaps are preserved as genuine preparation deficiencies; a gate having rows does not make its coverage complete. Each gap is classified in [`data/coverage-gap-classification.json`](data/coverage-gap-classification.json) as one of MISSING REQUIRED CONTROL, EXISTING CONTROL NEEDS TAGGING, CONTRACT-BLOCKED or JUSTIFIED NOT APPLICABLE (a source-backed justification is required). The classification is a preparation judgment for the independent lead and the QPR-1 gate binding to confirm. No row is created to fill a count. They are not failures of any implementation.', '',
        '| Gate | Expected control class (gate slug) | Classification |', '|---|---|---|']
for (gate, slug) in sorted(computed):
    out.append('| %s | %s | %s |' % (gate, slug, gmap.get((gate, slug), {}).get('classification', '?')))
cc = C.Counter(e['classification'] for e in gc)
out += ['', 'Classification totals: ' + '; '.join('%s %d' % (k, cc[k]) for k in sorted(cc)) + '.']
out += ['', 'Total gaps: %d.' % len(notes)]
if not errs:
    open(P + '04a-computed-coverage.md', 'w').write('\n'.join(out) + '\n')
for n in notes: print('  note:', n)
print('FAIL' if errs else 'OK', {k: len(v) for k, v in data.items()}, len(gd), 'gates')
for e in errs[:60]: print(' ', e)
sys.exit(1 if errs else 0)
