#!/usr/bin/env python3
"""Validates data/canonical-scenario-crosswalk.json against the repository's own scenario IDs, test markers and coverage map.

SPDX-License-Identifier: Apache-2.0
Usage: validate_crosswalk.py <QUAL_REPO_ROOT> <DATA_DIR>   (stdlib only, read-only). Exits non-zero on any failure."""
import ast, csv, json, os, re, sys, collections as C
R, D = sys.argv[1].rstrip('/') + '/', sys.argv[2].rstrip('/') + '/'
cw = json.load(open(D + 'canonical-scenario-crosswalk.json')); sl = json.load(open(D + 'suite-local-claims-supplement.json'))
csvrows = list(csv.DictReader(open(D + 'canonical-scenario-crosswalk.csv')))
cat = json.load(open(R + 'scenarios/catalog.json'))['scenarios']
cov = json.load(open(R + 'scenarios/coverage-map.json'))['mappings']
app = json.load(open(R + 'scenarios/ai-security-wiki/applicability.json'))
wcat = json.load(open(R + 'scenarios/ai-security-wiki/catalog.json'))['scenarios']
res, fails = {}, []
def chk(name, ok, detail=''):
    res[name] = {'ok': bool(ok), 'detail': detail}
    if not ok: fails.append(name)
ids = [r['scenario_id'] for r in cw]
chk('row_count_696', len(cw) == 696 and len(set(ids)) == 696, f'{len(cw)} rows, {len(set(ids))} distinct')
def _norm(x):
    return '' if x is None else (';'.join(map(str, x)) if isinstance(x, list) else str(x))
_diff = [(c['scenario_id'], k) for c, j in zip(csvrows, cw) for k in c if _norm(j.get(k)) != c[k]]
chk('csv_matches_json', [r['scenario_id'] for r in csvrows] == ids and not _diff and all(set(c) == set(j) for c, j in zip(csvrows, cw)), f'{len(csvrows)} csv rows; all columns compared; differences: {_diff[:5]}')
catids = [s['id'] for s in cat]; wids = [c['id'] for c in app['cases']]
chk('catalog_ids_exact', [r['scenario_id'] for r in cw[:40]] == catids and set(catids) <= set(ids), f'{len(catids)} catalog ids, source order preserved')
chk('wiki_ids_exact', set(wids) == set(ids[40:]) and len(wids) == 656, f'{len(wids)} wiki ids from applicability.json')
chk('wiki_catalog_agrees', {s['id'] for s in wcat} == set(wids), f'{len(wcat)} ids in ai-security-wiki/catalog.json')
cls = C.Counter(r['applicability'] for r in cw[40:]); want = C.Counter(c['classification'] for c in app['cases'])
chk('wiki_classification_preserved', cls == want, dict(cls))
wapp = {c['id']: c['classification'] for c in app['cases']}
chk('wiki_row_classification_per_id', all(r['applicability'] == wapp[r['scenario_id']] for r in cw[40:]))
VOC_DEP = {'REQUIRED', 'BENEFICIAL', 'UNNECESSARY', 'UNKNOWN'}; VOC_PROT = {'ENFORCED_AND_EVIDENCED', 'IMPLEMENTED_NOT_QUALIFIED', 'PARTIALLY_ENFORCED', 'KNOWN_GAP', 'NOT_APPLICABLE', 'UNKNOWN'}
VOC_EV = {'PASS_RECORDED', 'FAIL_RECORDED', 'BLOCKED', 'NOT_RUN', 'KNOWN_LIMIT_ASSERTED', 'COLLECTED_ONLY', 'NO_TEST', 'UNKNOWN'}
FAM = {'F1a','F1b','F1c','F1d','F3','F4','F5','F6','F7','F8','F9','F10','F11','NONE','UNMAPPED'}
chk('vocab_dependency', all(r['registry_dependency'] in VOC_DEP for r in cw + sl))
chk('vocab_protection', all(r['existing_protection'] in VOC_PROT for r in cw + sl))
chk('vocab_evidence', all(r['evidence_status'] in VOC_EV for r in cw + sl))
chk('vocab_family', all(set(r['registry_family'].split(',')) <= FAM for r in cw + sl))
chk('f8_never_assigned_as_candidate', not any('F8' in r['registry_family'].split(',') for r in cw + sl))
chk('no_canonical_enforced_and_evidenced', not any(r['existing_protection'] == 'ENFORCED_AND_EVIDENCED' for r in cw), 'canonical rows: 0 (no scenario has a scenario-level PASS)')
chk('suite_local_enforced_and_evidenced_only_with_recorded_pass', all(r['evidence_status'] == 'PASS_RECORDED' for r in sl if r['existing_protection'] == 'ENFORCED_AND_EVIDENCED'), str(sum(r['existing_protection'] == 'ENFORCED_AND_EVIDENCED' for r in sl)) + ' suite-local claims')
chk('known_limit_not_counted_as_protection', all(r['existing_protection'] != 'ENFORCED_AND_EVIDENCED' for r in cw if r['evidence_status'] == 'KNOWN_LIMIT_ASSERTED'))
chk('no_not_run_as_pass', not any(r['evidence_status'] == 'PASS_RECORDED' and 'NOT RUN' in r['qualification_status'] and not r['qualification_status'].startswith('scenario verdict NOT RUN; named') and r['scenario_id'] in ids[40:] for r in cw))
chk('wiki_all_not_run', all(r['qualification_status'].startswith('NOT RUN') for r in cw[40:]))
chk('required_columns', all(len(r) == 21 for r in cw), '21 specified columns per row')
# test markers
def defs(path):
    try: t = ast.parse(open(path).read())
    except Exception: return set()
    out = set()
    for n in ast.walk(t):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)): out.add(n.name)
    return out
cache = {}
def has(path, sym):
    if path not in cache: cache[path] = defs(R + path) if path.endswith('.py') and os.path.exists(R + path) else None
    if cache[path] is None: return os.path.exists(R + path) and (sym in open(R + path, errors='ignore').read() if sym else True)
    m = re.match(r'^([A-Za-z_]\w*)\[(.+)\]$', sym)
    if m and not (m.group(1) in (cache[path] or set())):  # data-driven marker such as VARIANTS[valid]: name and key must both occur in the file
        txt = open(R + path).read(); return m.group(1) in txt and m.group(2) in txt
    base = sym.split('[')[0].split('.')[-1]  # class-qualified names such as OracleTests.test_x: check the final segment
    return base in cache[path] or sym in open(R + path).read()
bad = []
for r in cw[:40]:
    for t in r['test_ids'].split(';'):
        if not t: continue
        p, _, s = t.partition('::')
        if not os.path.exists(R + p) or not has(p, s): bad.append((r['scenario_id'], t))
chk('catalog_test_ids_exist', not bad, f'{sum(len([t for t in r["test_ids"].split(";") if t]) for r in cw[:40])} test ids; missing: {bad[:5]}')
wd = set()
for f in os.listdir(R + 'suites/wiki-derived'):
    if f.endswith('.py'): wd |= defs(R + 'suites/wiki-derived/' + f)
badw = [(r['scenario_id'], t) for r in cw[40:] for t in r['test_ids'].split(';') if t and t.split('::')[-1] not in wd]
chk('wiki_test_ids_exist', not badw, f'{len({t for r in cw[40:] for t in r["test_ids"].split(";") if t})} distinct wiki-derived test functions; missing: {badw[:5]}')
# coverage-map mappings preserved
missing = []
for m in cov:
    sid = m['scenario_id']; row = next(r for r in cw if r['scenario_id'] == sid); have = row['test_ids']
    for t in m['tests']:
        if t['symbol'].split('[')[0] not in have: missing.append((sid, t['symbol']))
chk('coverage_map_tests_preserved', not missing, f'{sum(len(m["tests"]) for m in cov)} mapped tests; missing: {missing[:5]}')
zero = [m['scenario_id'] for m in cov if not m['tests']]
empty = sorted(r['scenario_id'] for r in cw[:40] if not r['test_ids'])
chk('zero_test_scenarios_equal_coverage_map', sorted(zero) == empty, f'coverage-map zero-test scenarios: {sorted(zero)}; crosswalk catalog rows without test ids: {empty}')
instc = [r for r in cw[40:] if r['applicability'] != 'NOT_APPLICABLE']
notest = sorted(r['scenario_id'] for r in instc if not r['test_ids'])
chk('wiki_in_scope_without_test_matches_inventory', notest == sorted(['TC-D09-004', 'TC-D13-003', 'TC-L02-002', 'TC-L08-033']), str(notest))
chk('suite_local_ids_unique_prefixed', len({r['scenario_id'] for r in sl}) == len(sl) and all(r['scenario_id'].startswith('SL:') for r in sl), f'{len(sl)} suite-local claims')
chk('suite_local_not_in_canonical_denominator', not ({r['scenario_id'] for r in sl} & set(ids)))
chk('priority_vocab', {r['priority'] for r in cw} <= {'P1', 'P2', 'P3', 'P4', 'OUT_OF_SCOPE'})
tqv = list(csv.DictReader(open(D + 'three-question-view.csv')))
chk('three_question_view_matches_crosswalk', [r['scenario_id'] for r in tqv] == ids and all(r['q_a_existing_protection'] == c['existing_protection'] and r['q_a_evidence_status_named_cases_only'] == c['evidence_status'] and r['q_a_qualification_status'] == c['qualification_status'] for r, c in zip(tqv, csvrows)), f'{len(tqv)} rows; question A copied verbatim')
mf = [json.loads(l) for l in open(D + 'configuration-extraction-manifest.jsonl')]
slids = {r['scenario_id'] for r in sl}
_sh = C.defaultdict(list)
for m in mf:
    if m.get('shared_underlying_field'): _sh[m['shared_underlying_field']].append(m)
_dupok = all(len([m for m in g if not m['duplicate_of']]) == 1 and len({m['recommended_disposition'] for m in g}) == 1 for g in _sh.values())
chk('manifest_field_ids_unique', len({m['field_id'] for m in mf}) == len(mf) and _dupok, f'{len(mf)} rows; {len(_sh)} shared underlying field group(s), one governing row and one disposition each; eligible distinct fields {sum(1 for m in mf if m["recommended_disposition"] in ("DIRECT_EXTRACTION","CONDITIONAL_EXTRACTION") and not m["duplicate_of"])}')
chk('manifest_scenario_ids_resolve', all(x == 'NONE' or x in set(ids) or x in slids for m in mf for x in m['scenario_id'].split(';') if x), 'canonical, suite-local or NONE')
chk('manifest_verified_rows_have_pin', all(m['source_pin'] for m in mf if m['verification'] == 'SOURCE_VERIFIED'))
_BLOCK = re.compile(r'(?i)(depends on|waits on|blocked by|pending|requires)\s+(open\s+)?(D1|D4|D5|D6|D9|D12|W\d-\d{3})\b')
chk('manifest_direct_rows_name_no_open_decision', not [m['field_id'] for m in mf if m['recommended_disposition'] == 'DIRECT_EXTRACTION' and _BLOCK.search(m['disposition_basis'])], 'independent text check of disposition_basis (not the derived decisions_named column); a mention such as "D6 interaction noted" is not a dependency')
chk('manifest_no_relaxing_toggle_direct', not any(('legacy-prefix' in m['configurable_field'] or 'on_unreadable' in m['configurable_field']) and m['recommended_disposition'] == 'DIRECT_EXTRACTION' for m in mf))
json.dump(res, open(D + 'validation-report.json', 'w'), indent=1)
for k, v in res.items(): print(('PASS ' if v['ok'] else 'FAIL ') + k + ' :: ' + str(v['detail'])[:160])
sys.exit(1 if fails else 0)
