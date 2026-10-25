#!/usr/bin/env python3
"""Merges the per-owner configuration-extraction rows into one validated planning manifest.

SPDX-License-Identifier: Apache-2.0
Usage: build_extraction_manifest.py <DATA_DIR> <ROWS.jsonl> [<ROWS.jsonl> ...]   (stdlib only)

Writes data/configuration-extraction-manifest.{jsonl,csv} and adds the table keys T_MANIFEST, T_MANIFEST_COUNTS and
T_MANIFEST_FAMILY to data/tables.json (rendered into 09-configuration-extraction-handoff.md by fill_docs.py).
Validation (exit non-zero on failure): all required keys; dispositions and verification in the closed vocabularies;
field_id unique; every scenario_id is NONE, a canonical crosswalk ID or a suite-local claim ID; no row marked
SOURCE_VERIFIED lacks a source_pin. It is a planning manifest; it authorizes nothing.
"""
import csv, json, re, sys, collections as C

D = sys.argv[1].rstrip('/') + '/'
SRC = sys.argv[2:]
KEYS = ['field_id', 'scenario_id', 'enforcement_component', 'evaluator', 'configurable_field', 'current_value_source',
        'existing_guardrail', 'registry_family', 'configuration_value', 'central_governance_benefit', 'extraction_complexity',
        'cross_field_dependency', 'cross_component_dependency', 'required_qualification', 'exclusion_impact',
        'recommended_disposition', 'disposition_basis', 'verification', 'source_pin']
DISP = ['DIRECT_EXTRACTION', 'CONDITIONAL_EXTRACTION', 'CODE_OWNED_GUARDRAIL', 'UNRESOLVED', 'NOT_RELEVANT_TO_V1']
VERIF = {'SOURCE_VERIFIED', 'UNVERIFIED'}

canon = {r['scenario_id'] for r in csv.DictReader(open(D + 'canonical-scenario-crosswalk.csv'))}
supp = {r['scenario_id'] for r in csv.DictReader(open(D + 'suite-local-claims-supplement.csv'))}
rows, errs = [], []
for p in SRC:
    for n, line in enumerate(open(p), 1):
        if not line.strip():
            continue
        try:
            o = json.loads(line)
        except Exception as e:
            errs.append(f'{p}:{n} not JSON: {e}'); continue
        miss = [k for k in KEYS if k not in o]
        if miss:
            errs.append(f"{p}:{n} {o.get('field_id')} missing {miss}"); continue
        rows.append(o)
seen = set()
for o in rows:
    f = o['field_id']
    if f in seen: errs.append(f'duplicate field_id {f}')
    seen.add(f)
    if o['recommended_disposition'] not in DISP: errs.append(f'{f} bad disposition {o["recommended_disposition"]}')
    if o['verification'] not in VERIF: errs.append(f'{f} bad verification {o["verification"]}')
    if o['verification'] == 'SOURCE_VERIFIED' and not o['source_pin']: errs.append(f'{f} verified without pin')
    for s in [x.strip() for x in o['scenario_id'].split(';') if x.strip()]:
        if s != 'NONE' and s not in canon and s not in supp:
            errs.append(f'{f} unknown scenario id {s}')

for o in rows:
    t = ' '.join([o['disposition_basis']])
    o['decisions_named'] = ','.join(sorted(set(re.findall(r'\b(D(?:1|4|5|6|9|12)|W\d-\d{3})\b', t)))) if o['recommended_disposition'] in ('CONDITIONAL_EXTRACTION', 'UNRESOLVED') else ''
    o['governance_benefit_level'] = o['central_governance_benefit'].split(' ')[0].strip('-:').upper()
    o['complexity_level'] = o['extraction_complexity'].split(' ')[0].strip('-:').upper()
    o.setdefault('shared_underlying_field', ''); o.setdefault('duplicate_of', '')
cols = KEYS + ['decisions_named', 'governance_benefit_level', 'complexity_level', 'shared_underlying_field', 'duplicate_of']
order = {'DIRECT_EXTRACTION': 0, 'CONDITIONAL_EXTRACTION': 1, 'UNRESOLVED': 2, 'CODE_OWNED_GUARDRAIL': 3, 'NOT_RELEVANT_TO_V1': 4}
rows.sort(key=lambda o: (o['field_id'].split('-')[0], order[o['recommended_disposition']], o['field_id']))

# duplicate-field accounting: rows naming the same underlying field must have exactly one governing row (duplicate_of empty),
# every duplicate_of must reference a governing row, and all rows of a group must share one disposition.
_grp = C.defaultdict(list)
for o in rows:
    if o['shared_underlying_field']: _grp[o['shared_underlying_field']].append(o)
_ids = {o['field_id']: o for o in rows}
for sf, g in _grp.items():
    gov = [o for o in g if not o['duplicate_of']]
    if len(gov) != 1: errs.append(f'shared field {sf}: {len(gov)} governing rows (need exactly 1)')
    if len({o['recommended_disposition'] for o in g}) != 1: errs.append(f'shared field {sf}: conflicting dispositions')
    for o in g:
        if o['duplicate_of'] and (o['duplicate_of'] not in _ids or _ids[o['duplicate_of']]['shared_underlying_field'] != sf or _ids[o['duplicate_of']]['duplicate_of']): errs.append(f"{o['field_id']}: bad duplicate_of {o['duplicate_of']}")
for o in rows:
    if o['duplicate_of'] and not o['shared_underlying_field']: errs.append(f"{o['field_id']}: duplicate_of without shared_underlying_field")
if errs:
    print('FAIL'); [print(' ', e) for e in errs]; sys.exit(1)

with open(D + 'configuration-extraction-manifest.jsonl', 'w') as f:
    for o in rows: f.write(json.dumps({k: o[k] for k in cols}, ensure_ascii=False) + '\n')
with open(D + 'configuration-extraction-manifest.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, cols); w.writeheader(); w.writerows({k: o[k] for k in cols} for o in rows)

def esc(s): return s.replace('|', '/').replace('\n', ' ')
tbl = ['| Field | Component | Family | Configurable field | Disposition | Governance benefit | Complexity | Decisions named | Verification |', '|---|---|---|---|---|---|---|---|---|']
for o in rows:
    comp = 'Runtime' if o['field_id'].startswith('RT') else ('Control Plane' if o['field_id'].startswith('CP') else o['field_id'].split('-')[0])
    tbl.append(f"| {o['field_id']} | {comp} | {esc(o['registry_family'])} | {esc(o['configurable_field'])[:90]} | {o['recommended_disposition']} | {o['governance_benefit_level']} | {o['complexity_level']} | {o['decisions_named'] or '-'} | {o['verification']} |")
cnt = C.Counter(o['recommended_disposition'] for o in rows)
byc = C.Counter(('Runtime' if o['field_id'].startswith('RT') else 'Control Plane', o['recommended_disposition']) for o in rows)
t2 = ['| Disposition | Runtime | Control Plane | Total |', '|---|---|---|---|']
for d in DISP:
    t2.append(f"| {d} | {byc[('Runtime', d)]} | {byc[('Control Plane', d)]} | {cnt[d]} |")
t2.append(f"| **All inventory rows** | {sum(v for (c, _), v in byc.items() if c == 'Runtime')} | {sum(v for (c, _), v in byc.items() if c == 'Control Plane')} | {len(rows)} |")
_dups = [o for o in rows if o['duplicate_of']]
_elig = [o for o in rows if o['recommended_disposition'] in ('DIRECT_EXTRACTION', 'CONDITIONAL_EXTRACTION') and not o['duplicate_of']]
t2.append(f"| Duplicate inventory rows (same underlying field, counted once) | {sum(1 for o in _dups if o['field_id'].startswith('RT'))} | {sum(1 for o in _dups if o['field_id'].startswith('CP'))} | {len(_dups)} |")
t2.append(f"| **Distinct underlying configurable fields** | | | {len(rows) - len(_dups)} |")
t2.append(f"| Eligible (DIRECT + CONDITIONAL) distinct fields, the Model B population | | | {len(_elig)} |")
fam = C.defaultdict(C.Counter)
for o in rows:
    for fm in re.split(r'[;,]\s*', o['registry_family']):
        fam[fm.strip()][o['recommended_disposition']] += 1
t3 = ['| Family | ' + ' | '.join(DISP) + ' | Rows |', '|---|' + '---|' * (len(DISP) + 1)]
for fm in sorted(fam):
    t3.append(f'| {fm} | ' + ' | '.join(str(fam[fm][d]) for d in DISP) + f' | {sum(fam[fm].values())} |')
T = json.load(open(D + 'tables.json'))
T['T_MANIFEST'] = '\n'.join(tbl) + '\n'; T['T_MANIFEST_COUNTS'] = '\n'.join(t2) + '\n'; T['T_MANIFEST_FAMILY'] = '\n'.join(t3) + '\n'
json.dump(T, open(D + 'tables.json', 'w'), indent=1)
print('OK', len(rows), dict(cnt))
