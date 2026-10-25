# Lane A: AI Security Wiki cases - OCS Registry V1 scope notes

Analysis only. Nothing implemented, nothing in any repo modified. Labels: SOURCE FACT / REASONED INFERENCE / UNVERIFIED (as in the brief).
Companion file: `A-wiki-rows.jsonl` (656 rows, one per upstream case).

## 1. Method

1. Row universe = `scenarios/ai-security-wiki/applicability.json` (`cases`, 656 entries, wiki commit `1a0c72de4752a1c6932172e5e7dbf14f755799c8`, qualification HEAD `998d39c5`). Title, layer, classification, close_call are copied verbatim; `source_refs[0]` is the line of the case in that file. SOURCE FACT.
2. 591 NOT_APPLICABLE rows are generated mechanically: `test_ids=[]`, `existing_protection=NOT_APPLICABLE`, `registry_family=[NONE]`, `evidence_status=NO_TEST`, `exclusion_impact` = recorded reason. `registry_dependency=UNNECESSARY` for the 572 plain ones; `UNKNOWN` for the 19 close-call NOT_APPLICABLE ones (their registry relevance was not assessed; the close_call_note is in `known_limitations`; verdicts not reclassified).
3. 65 in-scope rows are hand-analysed (`lanea/entries.py` in my scratchpad, not a deliverable). Test mapping is mechanical and AST based: `@wiki_case("TC-...")` decorators (all string literals, no module-level `pytestmark` case ids, no test carries two case ids) over `suites/wiki-derived/test_*.py`; parametrization expanded by reading the parameter lists. Source `path:line` references are produced by needle search in the cloned files, so each line number is real at the revision read.
4. Pytest is not installed in the environment; counts are by reading/AST, not `--collect-only`.
5. Enforcing code was read only where cloned. Where the enforcing component is not cloned, the row says so, uses label UNVERIFIED, and cites only the relocated test or the test-side helper that names the function.

### Revisions
| Item | Read | Pin used by the tests (r13 profile) |
|---|---|---|
| Control Plane | `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` (shallow clone, 1 commit) | `0a41faa9...` |
| Execution Runtime | `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f` (shallow clone) | `ec728da6...` (the R07 S02 pin) |
| Qualification repo | `998d39c5...` | |
All `path:line` citations are at the HEAD revisions, not at the pins. The pinned objects are not in the shallow clones, so I could not diff. Line numbers may differ at the pin; behaviour was cross-checked against test docstrings that name the pin (e.g. `test_wp_d_manifest_change_control.py:523` is "Revised for control plane 0a41faa9"). SOURCE FACT for the revisions; the drift consequence is UNVERIFIED.
Also: `/home/claude/cogno-us/cognous-open-control-stack` (HEAD `51c579a3`) exists locally although the brief says it is not cloned. It holds contracts/profiles/docs, not the component sources for exchange, replay, pack, ODES, verifier or manifest, so those enforcing implementations remain unreadable.

## 2. Count reconciliation

| Quantity | Brief / inventory | Verified | Basis |
|---|---:|---:|---|
| Distinct Wiki cases | 656 | **656** (656 in catalog.json too, identical id set, titles identical) | applicability.json |
| NOT_APPLICABLE / PARTLY_COVERED / APPLICABLE | 591 / 45 / 20 | **591 / 45 / 20** | applicability.json |
| In scope | 65 | **65** (W-I 17 = 2 A + 15 P; W-X 48 = 18 A + 30 P) | `split` member |
| In-scope close calls | n/a | **36** of 65; plus 19 NOT_APPLICABLE close calls (55 total) | `close_call` |
| `existing_implementation.status` of in-scope | 16 A partial + 4 A needs-new + 45 P partial | **61 partial_existing, 4 needs_new_implementation** (TC-D12-004, TC-L02-016, TC-L06-039, TC-L06-045); `new_implementation_needed=true` is set on all 20 APPLICABLE | applicability.json |
| Test functions in `suites/wiki-derived` | n/a | **262** (`def test_` at module level) | AST |
| Collected items (after parametrization) | 290 | **290** = 262 functions + 28 extra items | see below |
| Tests without a case id (skeleton) | 9 | **9** (5 registry/count checks + 4 route smoke tests) | `test_wiki_skeleton.py` |
| Case-carrying functions / items | 281 items | **253 functions = 281 items** | AST |
| W-I / W-X items | 64 / 217 | **64 / 217** (55 / 198 functions) | by case `split` |
| Cases with >= 1 wiki-derived test | W-I 14 + W-X 47 = 61 | **61** (41 PARTLY_COVERED + all 20 APPLICABLE) | AST |
| Cases with no wiki-derived test | 4 (`in_scope_without_wiki_derived_test`) | **4**: TC-D09-004, TC-D13-003, TC-L02-002, TC-L08-033 (all PARTLY_COVERED) | AST + inventory.json |
| Known-limit tests named | 35 | **35** (inventory.json list) covering 27 cases; function names containing `known_limit` number 36 because the withdrawn TC-L06-040 test is still in the file | name match vs inventory |

Parametrization expansion (28 extra items): `FAILURES` has 6 labels (TC-L17-028, 3 tests, +15); `floating_forms` 8 (TC-L16-007, +7); artifact list of 3 (TC-L16-015, +2); `G.FOUR` 4 (TC-L17-004, +3); two phrasings (TC-L06-039, +1). 15+7+2+3+1 = 28.
Items per in-scope case with tests: min 2 (TC-L06-041), max 19 (TC-L17-028); distribution of items per case: 2:1, 3:12, 4:27, 5:13, 6:4, 8:1, 9:1, 10:1, 19:1 (61 cases).

**Inconsistency inside `docs/test-inventory.md` (SOURCE FACT).** The package table (lines 124-136) and `inventory.json` list tests for APPLICABLE cases (WP-G1..G6), but the "Current state" bullets (lines 159-162) still say "39 of the 65 in-scope cases have tests ... all 39 are PARTLY_COVERED" and "None of the 20 APPLICABLE cases has a test", and list 26 cases without a test. The AST scan supports the table and inventory.json (61 with tests, 4 without). The bullets are stale; the line 160 "largest open item" no longer describes the repository. Line 161 also says six PARTLY_COVERED cases rely only on existing tests (adding TC-L06-003 and TC-L06-026), but WP-G6 now tests both; inventory.json's `in_scope_without_wiki_derived_test` has the four.

### Evidence state (what is and is not recorded)
- No Wiki case has a controller result: every case is NOT RUN (inventory.json, test-inventory.md section 5). `evidence_status` is therefore `NOT_RUN` for the 61 cases with tests and `NO_TEST` for the 4 without. I did not convert any local-run claim into PASS. SOURCE FACT.
- `docs/v1-known-limits.md:248` reports a direct local run (19-20 Oct, r10 pins): 290 collected, 285 passed, 5 failed (W-I 1, W-X 4), "expectations lag an intended change of their component"; one of the five is the withdrawn TC-L06-040 test. The other four failing test ids are not named anywhere I could find, so I cannot attach them to cases. That run is not a recorded verdict and predates the r13 pins.
- Four of the 20 APPLICABLE cases and some PARTLY_COVERED ones also appear in the comparison run `results/comparisons/g2-r10-20261020/` (wiki subset, 28 cases, OCS column: only 4 scenarios asked and all passed, 40/40 trials: TC-L06-008, TC-L06-023, TC-L06-034, TC-L09-014; most other OCS cells are "not expressible"; TC-D13-003 "not claimed"). That is a different harness and subset; I cite it in `known_limitations` only.
- Existing (pre-wiki) tests named in applicability.json have recorded PASS in controller run g8-r10-39690459403 (e.g. probes-authority `test_authority_probes` 23, probes-moltbot-safe `test_runtime_probes` 22, scenarios `test_scn_c16` 18, `test_scn_d06` 8) but at r10 pins; `results/README.md` says historical evidence does not qualify changed configurations. I used this only to describe the 4 no-test cases.
- Rule I applied to `existing_protection`: `ENFORCED_AND_EVIDENCED` is assigned to **no** case, because there is no recorded result at the r13 pins / HEAD for any Wiki case. `IMPLEMENTED_NOT_QUALIFIED` = the in-scope behaviour is enforced in code I read (or asserted by a test whose enforcing code I read) but not qualified. `PARTIALLY_ENFORCED` = even the declared-scope subset has an asserted limit. `KNOWN_GAP` = the core of the case is an asserted limit. REASONED INFERENCE (my rule, stated so the lead can re-map).

## 3. Per-layer summary
(INQ = IMPLEMENTED_NOT_QUALIFIED, PART = PARTIALLY_ENFORCED, GAP = KNOWN_GAP, NA = NOT_APPLICABLE; dependency UNN/BEN/UNK = UNNECESSARY/BENEFICIAL/UNKNOWN. The 12 layers with no in-scope case are all NOT_APPLICABLE and omitted from the in-scope columns.)

| Layer | Wiki cases | NOT_APPL | APPL | PARTLY | with wiki-derived test | collected items | protection INQ/PART/GAP/NA | dependency UNN/BEN/UNK |
|---|---:|---:|---:|---:|---:|---:|---|---|
| D08 | 25 | 25 | 0 | 0 | 0 | 0 | - | - |
| D09 | 20 | 16 | 0 | 4 | 3 | 12 | 3/1/0/0 | 2/2/0 |
| D10 | 23 | 23 | 0 | 0 | 0 | 0 | - | - |
| D11 | 22 | 22 | 0 | 0 | 0 | 0 | - | - |
| D12 | 22 | 18 | 2 | 2 | 4 | 20 | 1/3/0/0 | 3/0/1 |
| D13 | 21 | 20 | 0 | 1 | 0 | 0 | 0/1/0/0 | 0/0/1 |
| L01 | 20 | 20 | 0 | 0 | 0 | 0 | - | - |
| L02 | 25 | 21 | 2 | 2 | 3 | 14 | 1/2/0/1 | 3/1/0 |
| L03 | 42 | 41 | 1 | 0 | 1 | 4 | 0/1/0/0 | 1/0/0 |
| L04 | 32 | 32 | 0 | 0 | 0 | 0 | - | - |
| L05 | 35 | 31 | 2 | 2 | 4 | 13 | 1/3/0/0 | 2/1/1 |
| L06 | 46 | 22 | 8 | 16 | 24 | 104 | 10/12/2/0 | 10/9/5 |
| L07 | 41 | 37 | 0 | 4 | 4 | 14 | 4/0/0/0 | 3/0/1 |
| L08 | 42 | 40 | 0 | 2 | 1 | 4 | 1/1/0/0 | 1/1/0 |
| L09 | 26 | 18 | 2 | 6 | 8 | 34 | 5/3/0/0 | 7/0/1 |
| L10-L14 | 33+25+31+26+22 | all | 0 | 0 | 0 | 0 | - | - |
| L15 | 20 | 19 | 0 | 1 | 1 | 4 | 0/1/0/0 | 1/0/0 |
| L16 | 26 | 24 | 0 | 2 | 2 | 15 | 0/2/0/0 | 0/0/2 |
| L17 | 31 | 25 | 3 | 3 | 6 | 43 | 1/3/2/0 | 6/0/0 |
| **Total** | **656** | **591** | **20** | **45** | **61** | **281** | 27/33/4/1 | 39/14/12 |

L06 (agent runtime/authority) carries 24 of the 65 in-scope cases and 104 of the 281 items.

In-scope registry family tally (a case may list several; REASONED INFERENCE except where the row says SOURCE FACT):
- F1a 5 (TC-L06-003, -009, -011, -013, -014); F1c 5 (TC-D13-003, TC-L06-014, -016, -024, TC-L09-014); F1d 2 (TC-L06-014, TC-L07-012); F4 3 (TC-D09-009, TC-D09-016, TC-L06-015); F5 3 (TC-D09-016, TC-L05-012, TC-L05-013); F6 1 (TC-L06-013, adjacent, not exercised); F11 1 (TC-L06-028).
- F1b, F3, F7, F9, F10: no case's tests exercise a configurable value of these families. F3 admission guards (TC-L08-033) are literals classified mandatory by R07; F9 (tenant id length) and F10 (trend thresholds) are present in source but not on any tested path. F8 is not defined as a policy family in R07 (`02-rule-family-taxonomy.md` section 4: "F8 (demo policy lists) is not a policy family"); no row uses it.
- `UNMAPPED` (14 cases): behaviour relevant to a registry but not an R07 parameter family: policy revision and change control (TC-L05-028, TC-L06-034, TC-L08-036, TC-L02-025, TC-D12-004), the exchange sender/recipient sets (TC-L06-003, -018, -020, -038, -039, -041), manifest content (TC-L05-022), component pins (TC-L16-007, -015).
- `NONE` (36 cases): protection is mandatory gate/lifecycle/evidence logic (R07 M1-M8) or authority data (grants) that a registry must not create.
- Dependency: **REQUIRED = 0**; BENEFICIAL 14; UNNECESSARY 39; UNKNOWN 12. No tested protection exists only because of registry-managed configuration. TC-L05-028 / TC-L08-036 / TC-L06-034 are the nearest to "registry would be needed to claim more" (cross-component policy propagation is explicitly not claimed today), still BENEFICIAL, not REQUIRED. UNKNOWN rows depend on D1/D6/D9/F11-tier questions, which I did not resolve.

## 4. Findings the lead should not miss
1. **The only configuration surface in the tested path is constructor/profile data, never env vars or files.** `grep os.environ|getenv` over Control Plane `src/` and Runtime `engine/` returns nothing (SOURCE FACT). Policy values enter as: `LocalExecutionPolicy` frozen-dataclass fields (`engine/safe_executor.py:359-372`; tests replace them with `dataclasses.replace`), `BoundedAuthorizationWorkflow.__init__` integers (`bounded.py:1264-1280`, ages default 60, clock tolerance 5), pydantic host profiles (`RuntimeAuthorityProfile`/`ActionClass`, `runtime_authority.py:82-170`), `RuleRevisionProfile.signers`, `PolicyConfig` JSON (`policy_config.py:16-40`, the only file loaded, serving the older PolicyGate), and in the exchange `LocalRegistry(senders, recipients, recipient)` (named in test code; exchange source not cloned).
2. **The Wiki cases mostly test mandatory logic, not parameters.** 36 of 65 map to `NONE`; of the families R07 calls candidates, only F1a, F1c/F1d, F4, F5, F6 (adjacent) and F11 appear on a tested path. F1a (executor allow-list, TC-L06-011/-013) is the clearest case where central policy adds value without changing a protection.
3. **TC-L05-013 test claims more than the source supports.** `test_wiki_l05_013_there_is_no_configurable_fail_open_mode_known_limit` asserts no fail-open mode exists, but `ActionClass.on_unreadable` accepts `"bounded_tolerance"` (`runtime_authority.py:88`) and `_read_grant` then serves a cached positive grant status for reversible classes (`bounded.py:2186-2200`; irreversible classes with a non-refuse value are rejected, `bounded.py:2111-2112`). The test introspects `bounded.BoundedWorkflow`, a name that does not exist in `bounded.py` (the class is `BoundedAuthorizationWorkflow`), behind a `hasattr` guard, so its parameter check is vacuous. Consequence for the registry: `on_unreadable` is a relaxing toggle; R07 04 says such toggles must never be registry-configurable. SOURCE FACT (code), REASONED INFERENCE (test weakness).
4. **A "known_limit"-named test is no longer a limit.** `test_wiki_l06_009_a_decision_alone_does_not_refuse_two_tools_of_one_name_known_limit` is in the inventory's declared 35, but its docstring (amendment 124, CP `0a41faa9`) says the limit was fixed (CP now refuses with `adapter_mismatch`/`invalid_manifest`; code at `bounded.py:2630-2634`, `ambiguous_tool`). It asserts a refusal, so it is not KNOWN_LIMIT_ASSERTED evidence; my row for TC-L06-009 treats it that way. Conversely `test_wiki_l06_028_..._known_cross_ledger_limit` is limit-shaped but not in the declared 35.
5. **Known-limit evidence is dense where evidence/records are concerned**: 27 of the 61 tested cases carry at least one declared known-limit test (35 tests). Four rows are `KNOWN_GAP` (TC-L06-018 no signature on exchange messages; TC-L06-045 correlation id not in message; TC-L17-002 4 of 14 fields not carried; TC-L17-021 no hold/retention/access log). None of these gaps is closed by any R07 parameter family: they are G1 (design/implementation) or G4 (evidence) classes, not G2.
6. **Most registry-relevant behaviour is policy distribution and change control, which R07's F-families do not cover.** Signed rule revisions already exist in the Control Plane (`rule_revision.py:113-188`, adoption check in the policy loop `bounded.py:2472`), and tests TC-L05-028, TC-L08-036, TC-L06-034, TC-L02-025 pin their behaviour (including known limits: policy content read as digest and row, backdated revision row accepted, in-place grant edit read as current). A registry that becomes the policy source must keep these properties (G3 binding) - this belongs to R08/R09/R10 (v1.2 V1-V2), not to the family list.
7. **Tenant, identity, injection and evidence cases are registry-neutral.** TC-L09-006/-007/-018/-019, TC-L07-008/-009/-013, TC-L17-*, TC-D12-007/-018/-021 are enforced in code that no family parameterises.

## 5. Cases whose registry relevance is non-obvious
- **TC-L06-013 (per-agent allow-list)**: delivered by grants from the resolver (authority; registry must not issue grants) plus the executor allow-list (F1a). F6 is the shape-nearest family (`engine/permissions.py:3-23`, JSON `{agent: [perms]}`) but I found no tested path using `PermissionSystem` (REASONED INFERENCE); D5 absent-agent semantics stays open.
- **TC-L05-012 (coverage verification)**: `HolderInventory` (`holder_inventory.py:43-60`) is an F5-adjacent host profile (S02 W8-068); D1/W8-014 unresolved, so dependency UNKNOWN.
- **TC-L05-013**: see finding 3; family F5 listed because the toggle sits in `ActionClass`, dependency UNNECESSARY because the registry must not be able to relax it.
- **TC-L06-014 / TC-L07-012**: touch F1c (ceilings, D6 open) and F1d (target prefixes, deferred by D9); dependency UNKNOWN. I do not resolve D6/D9.
- **TC-L06-024 / TC-L06-016 / TC-D13-003 / TC-L09-014**: effect-count caps (`max_effects`) live in three places (manifest `effect_limits`, grant permissions, `LocalExecutionPolicy.max_effects`; effective cap is the min, `bounded.py:2570`) plus the route-B budget row. Which of them a registry would own is exactly D6 and the S02 W8-091 row; not resolved.
- **TC-L06-028**: payload not masked; F11 default redaction (`models.py:420`) belongs to the older RunRecord/ReplayBundle path; I did not establish that RedactionConfig applies on the bounded export path (UNVERIFIED).
- **TC-D12-004**: "state at incident time" depends on the decision record carrying policy identity; with a registry the record would need the registry selection identity (v1.2 V2). UNMAPPED, UNKNOWN.
- **TC-L06-018/-038/-039/-041/-003 (exchange)**: the sender/recipient sets are constructor arguments of the exchange `LocalRegistry`; no R07 family; the exchange source is not cloned.
- **TC-L16-007/-015**: accepted-revision list and digest refusal sit in the Replay importer and the qualification pin tooling (`suites/_pins.py`); v1.2 selections carry exact evaluator pins; UNMAPPED, UNKNOWN.
- **TC-D09-004 / TC-L02-002**: no runtime protection to configure (consequence-tier equality `bounded.py:2300` only; mapping is a document).

## 6. Close-call cases (not reclassified)
36 in-scope close calls: TC-D09-004, -016; TC-D12-004, -007, -021; TC-D13-003; TC-L02-002, -011, -016; TC-L05-012, -013, -028; TC-L06-011, -016, -020, -022, -023, -024, -026, -038, -041, -045; TC-L07-008, -009, -012, -013; TC-L08-033, -036; TC-L09-006, -014; TC-L16-007, -015; TC-L17-004, -020, -022, -028 (the list is also `close_call=true` in the jsonl; the sidecar note is in each row's `known_limitations`). 19 NOT_APPLICABLE close calls carry `registry_dependency=UNKNOWN` and the sidecar note. Verdicts untouched.

## 7. Cases with no wiki-derived test (4) and their existing coverage
| Case | Paths named in applicability.json | What they cover | Recorded result (g8-r10, pins r10) |
|---|---|---|---|
| TC-D09-004 | `suites/v1-probes/test_authority_probes.py` | ER031 profile probes: T0-T4 tier table, mapping rows; document reads | 23 pass (probes-authority) |
| TC-L02-002 | same file | mapping rows declare status and claim no enforcement; reads optional `PROBE2_*` checkout | 23 pass |
| TC-D13-003 | `suites/v1-probes/test_runtime_probes.py`, `suites/v1-scenarios/test_scn_c16.py` | cumulative effect budget across effect ids; route B shared budgets, restart, concurrency, independence | 22 + 18 pass |
| TC-L08-033 | `suites/v1-scenarios/test_scn_d06.py` | report-only ingress pressure | 8 pass |
Owner decisions recorded in `test_wp_g6_partly_covered_fragments.py` docstring: no wrapper for D09-004, D13-003 (outside by design), L02-002 and L08-033 (would overstate coverage). SOURCE FACT. These rows have `evidence_status=NO_TEST`.

## 8. Limitations
- Enforcing source not cloned (so rows are UNVERIFIED for the function): governed exchange (all route C cases), replay bundle, evidence pack, ODES exporter, independent verifier, action manifest (only the Control Plane's in-tree port was read). 14 in-scope rows are labelled UNVERIFIED for that reason.
- Citations are at the HEAD revisions (CP `7a4bcd40`, RT `c5e97e87`), two merges ahead of the r13 pins the tests target; pinned objects unavailable (shallow clones). `docs/test-inventory.md` also cites "r10 pins" for its local run; the repository profile files go up to r13.
- No test was run (no pytest, no credentials, no controller). Test behaviour is read from test source and docstrings; where a test helper hides the called function (route C), I named only what the test code names.
- `existing_protection` and `registry_dependency` for the 65 rows are my classification under the stated rules; they are REASONED INFERENCE even where the underlying code facts are SOURCE FACT. Row `label` records the weakest basis of the row.
- The mapping of rows to R07 families uses `02-rule-family-taxonomy.md` and `04-schema-fitness-matrix.md` at registry main 783ff59f. R07 line numbers there refer to the S02 pins and drift at HEAD; I re-derived all cited lines from source.
- The comparison run `results/comparisons/g2-r10-20261020` uses another harness, other pins (r10) and a Cognous-authored subset plan; used only as a note.
- 5 failing wiki-derived tests of the 19-20 Oct local run are unidentified (only the withdrawn TC-L06-040 test is named).
- D1, D5, D6, D12 and the 32 UNRESOLVED S02 rows were not resolved; where a row depends on them the dependency is UNKNOWN or the note says "open".
- Scratch files (AST scan, builder) are in my scratchpad `lanea/`; not deliverables.
