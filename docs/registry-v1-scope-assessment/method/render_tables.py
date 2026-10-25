#!/usr/bin/env python3
"""Renders markdown table fragments from data/*.json (and appendix/lane-F-evidence-suites.json) into data/tables.json.
Usage: render_tables.py <DATA_DIR>

SPDX-License-Identifier: Apache-2.0
"""
import json, sys, csv, collections as C
D = sys.argv[1].rstrip('/') + '/'
m = json.load(open(D + 'family-metrics-and-scores.json')); met, S, rank = m['metrics'], m['scores'], m['rank']
P = json.load(open(D + 'profile-comparison.json'))
cw = list(csv.DictReader(open(D + 'canonical-scenario-crosswalk.csv')))
FAMS = list(met)
cx = {'F1a':1,'F1b':2,'F1c':4,'F1d':5,'F3':3,'F4':5,'F5':4,'F6':4,'F7':5,'F8':1,'F9':3,'F10':1,'F11':3}
def t(h, rows): return '| ' + ' | '.join(h) + ' |\n|' + '|'.join('---' for _ in h) + '|\n' + '\n'.join('| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows) + '\n'
o = {}
o['T_FAM'] = t(['Family','In-scope canonical scenarios touched','REQUIRED','BENEFICIAL','UNKNOWN','UNNECESSARY','Max consequence severity (1-5)','Suite-local claims touched','Complexity (1-5, Lane D)'],
  [[f, met[f]['canon'], met[f]['canon_dep'].get('REQUIRED',0), met[f]['canon_dep'].get('BENEFICIAL',0), met[f]['canon_dep'].get('UNKNOWN',0), met[f]['canon_dep'].get('UNNECESSARY',0), met[f]['canon_max_sev'] or '-', met[f]['sl'], cx[f]] for f in FAMS])
cols = ['A_consequence','B_breadth','C_central_governance','D_enforcement_maturity','E_incremental_capability','F_ease','G_qual_maturity','H_dependency_ease']
o['T_SCORES'] = t(['Family','A','B','C','D','E','F (ease)','G','H (ease)'], [[f] + [S[f][c] for c in cols] for f in FAMS])
o['T_COMP'] = t(['Family','Security-first','Customer-operational','Engineering-effort'], [[f] + [S[f]['composite'][k] for k in ('security_first','customer_operational_value','engineering_effort')] for f in FAMS])
o['T_RANK'] = t(['Rank','Security-first','Customer-operational','Engineering-effort'], [[i+1, rank['security_first'][i], rank['customer_operational_value'][i], rank['engineering_effort'][i]] for i in range(len(FAMS))])
rows = []
for p, fs in (('A','F1a+F1b'),('B','F1a+F1b+F1c+F4+F5'),('C','B + F6'),('D','C + F1d')):
    c, s = P[p]['canon'], P[p]['sl']
    rows.append([p, fs, c['touched'], c['fully_covered'], c['full_dep'].get('BENEFICIAL',0), c['full_dep'].get('UNKNOWN',0), c['full_dep'].get('UNNECESSARY',0), ', '.join(c['full_beneficial_sev4plus']) or '-', f"{s['touched']} / {s['fully_covered']}"])
o['T_PROF'] = t(['Profile','Families','Canonical scenarios touched','Fully covered (all families of the scenario in profile)','of which BENEFICIAL','of which UNKNOWN','of which UNNECESSARY','BENEFICIAL, severity>=4','Suite-local touched / fully'], rows)
o['T_PRI'] = t(['Priority','Rows','Meaning'], [[k, v, d] for (k, v), d in zip(sorted(C.Counter(r['priority'] for r in cw).items()), [''] * 9)])
dist = C.Counter(r['priority'] for r in cw)
o['T_PRI'] = t(['Priority','Rows','Rule'], [['P1', dist['P1'], 'BENEFICIAL (or REQUIRED) and consequence severity >= 4'], ['P2', dist['P2'], 'BENEFICIAL with severity < 4, or UNKNOWN with severity >= 3 (blocked by an open decision or an unmapped mechanism)'], ['P3', dist['P3'], 'UNKNOWN with severity < 3'], ['P4', dist['P4'], 'in-scope, protection is a code-owned invariant or adequate without migration'], ['OUT_OF_SCOPE', dist['OUT_OF_SCOPE'], 'Wiki NOT_APPLICABLE (retained, not scored)']])
ins = [r for r in cw if r['applicability'] != 'NOT_APPLICABLE']
o['T_DEP'] = t(['Registry dependency','In-scope canonical rows'], [[k, v] for k, v in sorted(C.Counter(r['registry_dependency'] for r in ins).items())])
o['T_PROT'] = t(['Existing protection','In-scope canonical rows'], [[k, v] for k, v in sorted(C.Counter(r['existing_protection'] for r in ins).items())])
o['T_EVID'] = t(['Evidence status','All 696 rows'], [[k, v] for k, v in sorted(C.Counter(r['evidence_status'] for r in cw).items())])
o['T_P1'] = t(['Scenario','Title','Families','Dependency','Protection','Evidence'], [[r['scenario_id'], r['scenario_title'][:60], r['registry_family'], r['registry_dependency'], r['existing_protection'], r['evidence_status']] for r in cw if r['priority'] == 'P1'])
o['T_APP'] = t(['Source','Applicability','Rows'], [['Cognous catalog', 'catalog', 40]] + [['AI Security Wiki', k, v] for k, v in sorted(C.Counter(r['applicability'] for r in cw if r['scenario_source'].startswith('AI Security')).items())])


# outcome table
E = {}
for l in open(D + 'lane-E-outcomes.jsonl'):
    r = json.loads(l); E[r['scenario_id']] = r
tt = C.defaultdict(C.Counter); sev = C.defaultdict(int)
for r in ins:
    oc = r['customer_security_outcome'].split('|')[0]
    tt[oc]['n'] += 1; tt[oc][r['registry_dependency']] += 1; tt[oc]['gap'] += r['existing_protection'] == 'KNOWN_GAP'; sev[oc] = max(sev[oc], E[r['scenario_id']]['consequence_severity'])
o['T_OUT'] = t(['Primary outcome','In-scope rows','BENEFICIAL','UNKNOWN','UNNECESSARY','KNOWN_GAP','Max severity'], [[k, v['n'], v['BENEFICIAL'], v['UNKNOWN'], v['UNNECESSARY'], v['gap'], sev[k]] for k, v in sorted(tt.items(), key=lambda x: -x[1]['n'])])
esc = lambda s: str(s).replace('|', '\\|').replace('\n', ' ')
g = json.load(open(D + 'gap-register.json')); gm = json.load(open(D + 'v1-acceptance-matrix.json'))
o['T_GAPS'] = t(['ID','Class','Scenarios','Component','Severity','Registry migration necessary?','Owner','Phase'], [[r['gap_id'], r['gap_class'], esc(r['scenario_ids']), esc(r['owning_component']), r['severity'], esc(r['registry_migration_necessary']), esc(r['responsible_owner']), esc(r['recommended_phase'])] for r in g])
o['T_GATES'] = t(['Gate','Scope','Required gate','Scenarios (existing test IDs)','Current evidence','New tests or decisions required'], [[r['gate_id'], esc(r['scope']), esc(r['required_gate']), (esc(r['scenario_ids']) or '-') + ' (' + str(len([x for x in r['existing_test_ids'].split(';') if x])) + ')', esc(r['current_evidence']), esc(r['new_tests_or_decisions_required'])] for r in gm])
# per-suite evidence table (Lane F)
fs = json.load(open(D + '../appendix/lane-F-evidence-suites.json'))
o['T_SUITES'] = t(['Suite','Gate','Inventory count (basis)','Inventory state','Evidence status (Lane F)','Known-limit tests','Pin named / latest controller pin','Historical pin does not speak for current heads'], [[x['suite_id'], x.get('gate') or '-', f"{x.get('count')} ({x.get('count_basis')})", x.get('inventory_state'), x.get('evidence_status'), x.get('known_limit_count'), f"{x.get('pin_named_by_inventory')} / {x.get('pin_in_latest_controller_run_g8')}", x.get('historical_pin_does_not_speak_for_current_heads')] for x in fs])
json.dump(o, open(D + 'tables.json', 'w'), indent=1); print({k: len(v) for k, v in o.items()})
