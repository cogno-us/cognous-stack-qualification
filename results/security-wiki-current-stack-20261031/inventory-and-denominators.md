# D-CS: Security evidence inventory, denominators, crosswalks (read-only)

Worktree: /home/claude/wt-wiki @ 86f78ea3d1bd9cf230813fa0941621e38e7605e4 (matches the tuple's qualification entry; untracked lead files `process/security-runtime-current-stack-20261031.json` and `process/v1-validation/current-stack-20261031/` exist and were not touched).
Method: python3 -I stdlib only (json, ast, hashlib, re); no test run, no import of test modules, no network. Labels: OBSERVED / INFERENCE / UNAVAILABLE. Source reading is not an executed PASS.
Deliverables: this file and /tmp/claude-0/sec/handoff/D-CS-classification.csv (656 rows + header).

## (a) Denominators verified against current source

| Claim | Result | Label |
|---|---|---|
| Imported cases | 656 in catalog.json `scenarios`, 656 in applicability.json `cases`; 656 unique ids in each; 0 duplicates; 0 missing either way; same order; titles identical; layer field equals id layer for all | OBSERVED |
| Classification | APPLICABLE 20 / PARTLY_COVERED 45 / NOT_APPLICABLE 591 = 656; in scope = 65. Counted from the `cases` rows and equal to the file's own `counts` block and to process/release-gate/inventory.json `wiki` block (656/20/45/591/65) | OBSERVED |
| Commit consistency | catalog.source_commit = applicability.catalog_source_commit = lock.source_commit = 1a0c72de4752a1c6932172e5e7dbf14f755799c8 | OBSERVED |
| Lock | 23 pages, case_count 656, 656 unique case_ids equal the catalog id set; per-page case_count equals len(case_ids) and the catalog count per page; 23/23 redistributed_sha256 equal the sha256 of pages/*.md on disk; 23 pages on disk = 23 in lock; every catalog `source.page_sha256` equals the lock page `sha256`; every case id occurs in its page text; approved_license_sha256 equals sha256 of scenarios/ai-security-wiki/LICENSE (28a9529c...) | OBSERVED |
| Upstream sha256 of the source pages / upstream commit content | not checkable offline (no network) | UNAVAILABLE |

Per page (layer: total = NA / PARTLY / APPLICABLE; lock count equal to total in every row): D08 25=25/0/0; D09 20=16/4/0; D10 23=23/0/0; D11 22=22/0/0; D12 22=18/2/2; D13 21=20/1/0; L01 20=20/0/0; L02 25=21/2/2; L03 42=41/0/1; L04 32=32/0/0; L05 35=31/2/2; L06 46=22/16/8; L07 41=37/4/0; L08 42=40/2/0; L09 26=18/6/2; L10 33=33/0/0; L11 25=25/0/0; L12 31=31/0/0; L13 26=26/0/0; L14 22=22/0/0; L15 20=19/1/0; L16 26=24/2/0; L17 31=25/3/3. Sum 656. In-scope concentration: L06 24, L09 8, L17 6, L02/L05/L07/D09/D12 4 each, L08/L16 2 each, D13/L03/L15 1 each.
Split of in-scope (applicability `split`): individual-component 17 (2 APPLICABLE + 15 PARTLY), cross-component 48 (18 + 30); equals the W-I/W-X text in docs/test-inventory.md. OBSERVED.

## (b) Tests in suites/wiki-derived (static, ast)

- 13 test modules (test_wiki_skeleton.py + WP-A..F + G1..G6). 262 `test_*` functions; 253 carry a literal `@wiki_case('TC-...')` decorator (253 markers = 253 functions, one id each, 0 non-literal, 0 module-level `wiki_case`); 9 (all in test_wiki_skeleton.py) carry none.
- Parametrize expansion (literal lists evaluated by reading source): TC-L17-028 x3 functions x6 failures = +15; TC-L16-007 8 forms = +7; TC-L16-015 3 artifacts = +2; TC-L17-004 4 = +3; TC-L06-039 2 phrasings = +1. 262 + 28 = **290 collected tests**, equal to inventory.json `wiki_derived_total_tests` (290). INFERENCE (static; collection itself not run).
- 61 distinct ids are tested. **In scope with a test: 61** (20 APPLICABLE + 41 PARTLY_COVERED). **In scope WITHOUT a test: 4**, all PARTLY_COVERED: TC-D09-004 (individual), TC-D13-003 (cross), TC-L02-002 (individual), TC-L08-033 (individual). Equals inventory.json `in_scope_without_wiki_derived_test`. **Tests marked for ids NOT in scope: 0**; marked ids not in catalog: 0.
  Note: all 20 APPLICABLE cases have a test, although applicability.json/inventory still record `applicable_needs_new: 4` (TC-D12-004, TC-L02-016, TC-L06-039, TC-L06-045; flag is historical, see cross-check 2). Individual-component tested 14 of 17; cross-component 47 of 48.
- Known-limit tests: 35 named in inventory.json all exist in the suite; 1 further `known_limit`-named function is the retired test_wiki_l06_040_the_schema_check_does_not_reject_extra_members_content_types_or_size_known_limit (present, documented to fail at the exchange pin, non-gating). 36 functions contain `known_limit` in the name.

### Skip / xfail / conditional constructs (OBSERVED, grep + ast)
- `pytest.skip`: exactly one, conftest.py:50-51 inside fixture `pinned_reference` (`if not os.environ.get('SCN_COMPONENTS_DIR'): pytest.skip(...)`). No `skipif`, `xfail`, `importorskip`, `pytest.mark.skip`, `SkipTest`, `deselect`, `collect_ignore`, or `pytest_collection*` hook anywhere in suites/wiki-derived or pytest.ini (pytest.ini only sets testpaths = tests).
- **Hidden-skip exposure**: the fixture is pulled in by module `pytestmark = usefixtures('pinned_reference')` in test_wp_a:31, wp_b:35, wp_c:45, wp_d:32, wp_e:44, wp_f:50, wp_g1:48, wp_g2:49, wp_g3:51, wp_g4:52 (list form with filterwarnings), wp_g5:56, wp_g6:40, and explicitly by the four smoke tests test_wiki_skeleton.py:75, 82, 89, 96. Hence every one of the 281 case-bearing expanded tests plus the 4 smoke tests (285 of 290) is skipped, not failed, if SCN_COMPONENTS_DIR is unset; only the 5 skeleton registry/count tests run unconditionally. Nothing in the suite converts such a skip into a failure, so the lead must assert 0 skipped in the run report. Module-scope fixtures that depend on it (wp_a:570, wp_f:195/325/941/1124, wp_g1:55, wp_g2:55, wp_g3:59/66) skip transitively.
- Other conditional constructs reviewed: no `except: pass`; bare-return inside a test only at test_wp_c_budget_stop_recovery.py:1182 (a branch end after assertions in TC-L17-028 BEFORE_ATTEMPT labels; not a skip). Two tests have no assert statement of their own and rely on helper assertions: test_wp_g5_exchange_messages_and_correlation.py:163 (executed_once helper) and :453 (executed_once). Registry gap reporting (`cases_without_a_test`, test_wiki_skeleton.py) is "reported, not failed" by design, so the 4 untested in-scope ids will not fail any run.

## (c) Classification of all 656 (CSV: D-CS-classification.csv)

| Class | Count |
|---|---|
| APPLICABLE-EXECUTABLE (in scope AND has test) | 61 (20 APPLICABLE + 41 PARTLY_COVERED) |
| APPLICABLE-NOT-IMPLEMENTED (in scope, no test) | 4 (all PARTLY_COVERED; ids above) |
| NOT_APPLICABLE-OUT-OF-SCOPE (stored reason kept verbatim, close-call note appended) | 591 |
| Total | 656 (no case dropped) |

591 NA rows carry 33 distinct stored reasons (largest: 40 gateway/DLP/guardrail, 39 compliance programme, 37 prompt/context/memory injection defences, 33 data layer, 32 UI/endpoint, 31 + 31 app-protection/model layer, 26 training, 25 red-teaming, 25 retrieval/vector, 24 + 24 vendor/SOC...). 19 NA rows are flagged `close_call` upstream. In-scope CSV rows put `[class; scope_extent; split]` plus the stored scope_note in `reason`. `test_node` lists file::function (parametrized ones listed once, not expanded).

### Candidate newly-applicable (flag only; NOT reclassified)
Column `newly_applicable_candidate`: Y = stored reason or close-call note cites a capability the current stack has (migrated Registry rule records / policy-baseline, revocation families, F-A1 pin, effective policy/binding); W = keyword match only, probable name collision; N = no flag. Selection is INFERENCE from stored text plus grep of current worktrees (Registry README/docs: 19-parameter family migration, revocation families; control_plane tests carry revocation-family runs; F-A1 docs under registry/docs/f-a1-authorization-pin). I could not establish which of these existed at classification time, so "newly" is a hypothesis for the lead/architect to adjudicate.
- Y (5): TC-D09-007 Privilege Drift Detection (note: policy digest drift exists, no approved-baseline drift; versioned registry records / pin may supply a baseline), TC-L06-043 Cross-Organisation Agent Federation (note: "only a local registry exists"), TC-L09-011 Leaver/Mover Access Removal (note: local grant revocation exists; revocation families), TC-L06-033 Orchestration Graph Policy as Code (declarative registry allow-lists), TC-L06-046 Compromised Agent Containment (reason: quarantine excluded; revocation families).
- W (15): the other NA D09 rows whose reason is "enterprise agent identity governance (registry, sponsors, IAM workflows)": D09-001, 002, 003, 005, 006, 008, 010, 012, 013, 014, 015, 017, 018, 019, 020. "Registry" there means an agent-identity system of record, not the OCS rule registry; likely not applicable. The NA rows of L12 and L14 citing "model registry"/"MLOps ... registry" were deliberately not flagged (unrelated meaning).
- Checked, not flagged: TC-L09-012 step-up (step-up appears only as a "profile" caveat in odes/control_plane READMEs; no implementation found) and TC-L17-005 ledger retention (no retention rule found in the registry or other worktrees); both OBSERVED by grep absence, INFERENCE as to meaning.

## Cross-checks and cautions
1. Tuple caveat: the Wiki tests and applicability were authored against historical pins; the tests run through suites/v1-scenarios helpers pinned to SCN_COMPONENTS_DIR. Which component tuple that directory resolves to decides whether results speak for the current stack (not examined here). INFERENCE.
2. applicability.json marks 4 APPLICABLE cases `existing_implementation.status = needs_new_implementation` (TC-D12-004, TC-L02-016, TC-L06-039, TC-L06-045); all four now have wiki-derived tests (WP-G2, G5), so the 'needs new' flag is a historical status, not a missing-test count. OBSERVED.
3. No file in the repos was modified; applicability.json and tests untouched.
