#!/usr/bin/env python3
"""Analysis script for docs/registry-v1-scope-assessment/. Not repository tooling; not wired to any workflow.

SPDX-License-Identifier: Apache-2.0
Joins the six lane outputs (A..F) into the canonical crosswalk, family metrics, scores and sensitivity tables.
Run:  python3 build_assessment.py <LANES_DIR> <OUT_DIR>      (stdlib only)
"""
import csv, json, sys, collections as C
LANES, OUT = sys.argv[1].rstrip('/') + '/', sys.argv[2].rstrip('/') + '/'
L = lambda f: [json.loads(l) for l in open(LANES + f)]
A, B, Bs, Cs, Cr, E = (L(f) for f in ('A-wiki-rows.jsonl', 'B-catalog-rows.jsonl', 'B-suitelocal-rows.jsonl',
                                       'C-suitelocal-rows.jsonl', 'C-routes.jsonl', 'E-outcomes.jsonl'))
D = json.load(open(LANES + 'D-families.json'))['families']
D = {f['family']: f for f in D}
route = {r['scenario_id']: r for r in Cr}
outc = {r['scenario_id']: r for r in E}
QUAL = 'qualification@998d39c5'; CP = 'control-plane@7a4bcd40'; RT = 'execution-runtime@c5e97e87'; WIKI = 'ai-security-wiki@1a0c72de'
COLS = ['scenario_id','scenario_source','scenario_title','applicability','customer_security_outcome','test_ids','test_suite',
        'component_route','source_commit','enforcement_component','enforcement_function','existing_protection',
        'existing_configuration_mechanism','registry_family','registry_dependency','exclusion_impact','evidence_status',
        'qualification_status','known_limitations','priority','priority_rationale']
G8 = 'controller g8-r10 (r13 pins CP 0a41faa9 / RT ec728da6), historical'
INCONC = set('D02 D05 D06 D07 D08 D09 C01 C02 C03 C04 C06 C07 C08 C09 C10 C11 C12 C13 C14 C16 C17 C18 C22 C23'.split())
MR = {'D01', 'D03', 'D04'}
def qstat_cat(i):
    if i in MR: return f'scenario row INCONCLUSIVE in {G8} (named synthetic assertion executed: matched refund battery; catalog mapping PARTIAL); no scenario-level PASS; not independently qualified; no run at current heads'
    if i in INCONC: return f'scenario row INCONCLUSIVE (named cases passed, none failed) in {G8}; no scenario-level PASS; not independently qualified; no run at current heads'
    return 'NOT RUN (no driver or deferred/unimplemented/agent-or-human arm); not independently qualified'
def commit_str(ec, kind):
    s = [QUAL] + ([WIKI] if kind == 'wiki' else [])
    t = (ec or '') 
    if 'control-plane' in t or 'Control Plane' in t: s.append(CP)
    if 'execution-runtime' in t or 'Runtime' in t: s.append(RT)
    return '; '.join(s)
def fam_list(r):
    f = r['registry_family']; return f if isinstance(f, list) else [x.strip() for x in str(f).split(',')]
def priority(r, sev):
    fams = [f for f in fam_list(r) if f not in ('NONE',)]
    dep, app = r['registry_dependency'], r['applicability']
    if app == 'NOT_APPLICABLE': return 'OUT_OF_SCOPE', 'Wiki case classified NOT_APPLICABLE from declared OCS scope; retained, not scored for registry scope'
    if dep == 'REQUIRED': return 'P1', 'registry-managed configuration is required for the protection'
    famtxt = '+'.join(fams) if fams else 'no family'
    if dep == 'BENEFICIAL' and sev >= 4: return 'P1', f'registry control beneficial ({famtxt}); consequence severity {sev}>=4'
    if dep == 'BENEFICIAL': return 'P2', f'registry control beneficial ({famtxt}); consequence severity {sev}<4'
    if dep == 'UNKNOWN' and sev >= 3: return 'P2', f'registry value undetermined ({famtxt}), blocked by an open decision or an unmapped mechanism; severity {sev}'
    if dep == 'UNKNOWN': return 'P3', f'registry value undetermined ({famtxt}); severity {sev}'
    return 'P4', f'protection is a code-owned invariant or already adequate without registry migration ({famtxt}); severity {sev}'
def row(r, kind, ew):
    o = outc.get(r['scenario_id'], {}); sev = o.get('consequence_severity', 0)
    pr, why = priority(r, sev)
    oc = o.get('primary_outcome', '') + (('|' + o['secondary_outcome']) if o.get('secondary_outcome') else '')
    if kind == 'wiki':
        qs = 'NOT RUN (all 656 Wiki cases NOT RUN; wiki-derived tests are not collected by the controller); not independently qualified'
    else:
        qs = qstat_cat(r['scenario_id'])
    rt = (route.get(r['scenario_id']) or {}).get('component_route') or r.get('component_route') or ''
    return {'scenario_id': r['scenario_id'], 'scenario_source': r['scenario_source'] if kind=='wiki' else 'cognous scenarios/catalog.json v1.0.0 (qualification@998d39c5)',
            'scenario_title': r['scenario_title'], 'applicability': r['applicability'], 'customer_security_outcome': oc,
            'test_ids': ';'.join(r['test_ids']), 'test_suite': ';'.join(r['test_suite']) if isinstance(r['test_suite'], list) else (r['test_suite'] or ''),
            'component_route': rt, 'source_commit': commit_str(r.get('enforcement_component'), kind),
            'enforcement_component': r.get('enforcement_component') or '', 'enforcement_function': r.get('enforcement_function') or '',
            'existing_protection': r['existing_protection'], 'existing_configuration_mechanism': r['existing_configuration_mechanism'],
            'registry_family': ','.join(fam_list(r)), 'registry_dependency': r['registry_dependency'], 'exclusion_impact': r['exclusion_impact'],
            'evidence_status': r['evidence_status'], 'qualification_status': qs, 'known_limitations': r['known_limitations'],
            'priority': pr, 'priority_rationale': why, '_sev': sev}
canon = [row(r, 'catalog', None) for r in B] + [row(r, 'wiki', None) for r in A]
assert len(canon) == 696 and len({r['scenario_id'] for r in canon}) == 696
sl = []
for r in Bs + Cs:
    x = row({**r, 'applicability': r.get('applicability') or 'SUITE_LOCAL'}, 'suite', None)
    ev = r['evidence_status']
    x['qualification_status'] = 'suite-local claim; ' + ('NOT RUN / PROPOSED expectation (no recorded result)' if ev == 'NOT_RUN' else
        'named cases recorded PASS at historical pins only (controller artifact or inventory-page state; see lane notes); developer-run; not independently qualified; no run at current heads' if ev == 'PASS_RECORDED' else
        'passes by asserting a known limit; not protection; not independently qualified' if ev == 'KNOWN_LIMIT_ASSERTED' else
        'collected only; no recorded result; not independently qualified')
    x['priority'], x['priority_rationale'] = ('SL_INFO', 'supplementary suite-local claim; not scored (no consequence rating produced for suite-local rows)')
    x['customer_security_outcome'] = next((t for t in str(r['known_limitations']).split() if t.startswith('outcome:')), '').replace('outcome:', '')
    sl.append(x)
assert len({r['scenario_id'] for r in sl}) == len(sl)
def w(path, rows):
    keys = COLS
    with open(path, 'w', newline='') as f:
        c = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore'); c.writeheader(); c.writerows(rows)
    json.dump([{k: r[k] for k in keys} for r in rows], open(path.replace('.csv', '.json'), 'w'), indent=1, ensure_ascii=False)
w(OUT + 'canonical-scenario-crosswalk.csv', canon); w(OUT + 'suite-local-claims-supplement.csv', sl)
# ---------- family metrics ----------
FAMS = ['F1a','F1b','F1c','F1d','F3','F4','F5','F6','F7','F8','F9','F10','F11']
sev = {r['scenario_id']: r['_sev'] for r in canon}
met = {}
for f in FAMS:
    can = [r for r in canon if f in r['registry_family'].split(',') and r['applicability'] != 'NOT_APPLICABLE']
    s = [r for r in sl if f in r['registry_family'].split(',')]
    met[f] = {'canon_ids': [r['scenario_id'] for r in can], 'canon': len(can),
              'canon_dep': dict(C.Counter(r['registry_dependency'] for r in can)),
              'canon_prot': dict(C.Counter(r['existing_protection'] for r in can)),
              'canon_max_sev': max([r['_sev'] for r in can] or [0]),
              'canon_outcomes': sorted({r['customer_security_outcome'].split('|')[0] for r in can}),
              'canon_beneficial': [r['scenario_id'] for r in can if r['registry_dependency'] == 'BENEFICIAL'],
              'canon_unnecessary': [r['scenario_id'] for r in can if r['registry_dependency'] == 'UNNECESSARY'],
              'canon_unknown': [r['scenario_id'] for r in can if r['registry_dependency'] == 'UNKNOWN'],
              'canon_withtests_passrec': [r['scenario_id'] for r in can if r['evidence_status'] == 'PASS_RECORDED'],
              'canon_with_tests': [r['scenario_id'] for r in can if r['test_ids']],
              'sl': len(s), 'sl_dep': dict(C.Counter(r['registry_dependency'] for r in s))}
def scores(f):
    m = met[f]; d = D[f]
    a = m['canon_max_sev'] or 1
    nb = len(m['canon_outcomes']); b = 1 if nb <= 1 else 2 if nb == 2 else 3 if nb == 3 else 4 if nb <= 5 else 5
    ben = m['canon_dep'].get('BENEFICIAL', 0) + m['sl_dep'].get('BENEFICIAL', 0)
    benhi = any(sev[i] >= 4 for i in m['canon_beneficial'])
    c = 4 if (ben >= 3 and benhi) else 3 if ben >= 1 else 2 if (m['canon_dep'].get('UNKNOWN', 0) or m['sl_dep'].get('UNKNOWN', 0)) else 1
    g = 3 if m['canon_withtests_passrec'] else 2 if m['canon_with_tests'] else 1
    cx = d['complexity']['score']; fe = 6 - cx
    h = 5 - min(4, len(d['cross_family_dependencies']))
    return {'A_consequence': a, 'B_breadth': b, 'C_central_governance': c, 'G_qual_maturity': g, 'F_ease': fe, 'H_dependency_ease': h}
MAN = {  # D (enforcement maturity) and E (incremental customer capability): REASONED INFERENCE, rationale in 04-prioritization-analysis.md
 'F1a': (3,3),'F1b': (3,3),'F1c': (3,4),'F1d': (2,3),'F3': (3,2),'F4': (3,4),'F5': (3,3),'F6': (1,2),'F7': (2,3),'F8': (1,1),'F9': (3,1),'F10': (2,1),'F11': (3,2)}
S = {}
for f in FAMS:
    s = scores(f); s['D_enforcement_maturity'], s['E_incremental_capability'] = MAN[f]; S[f] = s
WTS = {'security_first': dict(A_consequence=.30, C_central_governance=.15, D_enforcement_maturity=.15, B_breadth=.10, E_incremental_capability=.10, G_qual_maturity=.05, F_ease=.075, H_dependency_ease=.075),
       'customer_operational_value': dict(E_incremental_capability=.25, B_breadth=.20, C_central_governance=.20, A_consequence=.10, D_enforcement_maturity=.10, G_qual_maturity=.05, F_ease=.05, H_dependency_ease=.05),
       'engineering_effort': dict(F_ease=.30, H_dependency_ease=.20, D_enforcement_maturity=.15, G_qual_maturity=.10, A_consequence=.075, E_incremental_capability=.075, B_breadth=.05, C_central_governance=.05)}
for k, v in WTS.items(): assert abs(sum(v.values()) - 1) < 1e-9, k
rank = {}
for k, v in WTS.items():
    comp = {f: round(sum(v[d] * S[f][d] for d in v), 3) for f in FAMS}
    rank[k] = sorted(FAMS, key=lambda f: (-comp[f], f)); 
    for f in FAMS: S[f].setdefault('composite', {})[k] = comp[f]
json.dump({'metrics': met, 'scores': S, 'weights': WTS, 'rank': rank}, open(OUT + 'family-metrics-and-scores.json', 'w'), indent=1)
# ---------- profiles ----------
PROF = {'A': ['F1a','F1b'], 'B': ['F1a','F1b','F1c','F4','F5'], 'C': ['F1a','F1b','F1c','F4','F5','F6'], 'D': ['F1a','F1b','F1c','F4','F5','F6','F1d']}
def prof(fs, rows, label):
    inscope = [r for r in rows if r['applicability'] != 'NOT_APPLICABLE']
    out = {}
    touched = [r for r in inscope if set(r['registry_family'].split(',')) & set(fs)]
    full = [r for r in touched if all(x in fs or x in ('NONE',) for x in r['registry_family'].split(',') if x not in ('UNMAPPED',)) and 'UNMAPPED' not in r['registry_family'].split(',')]
    out['touched'] = len(touched); out['fully_covered'] = len(full)
    out['touched_dep'] = dict(C.Counter(r['registry_dependency'] for r in touched))
    out['full_dep'] = dict(C.Counter(r['registry_dependency'] for r in full))
    out['full_beneficial_sev4plus'] = [r['scenario_id'] for r in full if r['registry_dependency'] == 'BENEFICIAL' and r.get('_sev', 0) >= 4]
    out['full_beneficial'] = [r['scenario_id'] for r in full if r['registry_dependency'] == 'BENEFICIAL']
    out['touched_ids'] = [r['scenario_id'] for r in touched]
    return out
PR = {p: {'canon': prof(fs, canon, p), 'sl': prof(fs, sl, p)} for p, fs in PROF.items()}
PR['F7_alone'] = {'canon': prof(['F7'], canon, 'F7'), 'sl': prof(['F7'], sl, 'F7')}
json.dump(PR, open(OUT + 'profile-comparison.json', 'w'), indent=1)
print('canon', len(canon), 'sl', len(sl)); print(C.Counter(r['priority'] for r in canon)); print(C.Counter(r['registry_dependency'] for r in canon if r['applicability']!='NOT_APPLICABLE'))
for k in WTS: print(k, rank[k])
for f in FAMS: print(f, S[f]['A_consequence'], S[f]['B_breadth'], S[f]['C_central_governance'], S[f]['D_enforcement_maturity'], S[f]['E_incremental_capability'], S[f]['F_ease'], S[f]['G_qual_maturity'], S[f]['H_dependency_ease'], {k: v for k, v in S[f]['composite'].items()}, met[f]['canon'], met[f]['canon_dep'], met[f]['sl'])
for p in PROF: print(p, {k: v for k, v in PR[p]['canon'].items() if k not in ('touched_ids',)}, 'SL', PR[p]['sl']['touched'], PR[p]['sl']['fully_covered'], PR[p]['sl']['full_dep'])
print('F7', PR['F7_alone']['canon']['touched_ids'], PR['F7_alone']['canon']['touched_dep'])
