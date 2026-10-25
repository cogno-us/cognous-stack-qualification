# Lane F: Evidence and coverage audit (notes)

Read-only analysis. No qualification verdict reinterpreted; every status below is quoted from an artifact or computed from one. Labels: SOURCE FACT = read in a file (path given); REASONED INFERENCE = my deduction; UNVERIFIED = could not confirm.

## 0. Revisions read and method

| Item | Value |
|---|---|
| Qualification repo | `/home/claude/cognous-stack-qualification`, HEAD `998d39c5ba1c9d537be8289f7658f2e9cde6cbba` (2026-10-24, merge of PR #225). Single-commit snapshot (`rev-list --count HEAD` = 1): no history, so the inventory's `bf865632` and every older SHA cannot be resolved locally. |
| Control Plane clone | `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` (2026-10-23, PR #83 f3-claim-journal), shallow, 1 commit |
| Runtime clone | `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f` (2026-10-23, PR #144 f3/approval-revocation-terminal), shallow, 1 commit |
| Hub clone | `51c579a3208149922649a31a6eb041106a4121c3` (differs from freeze hub `8517818f` and MVP hub `c897266b`); not otherwise used |
| Counting method | No `pytest` installed and no installs allowed, so no `--collect-only`. I counted by AST (`scratchpad/laneF/count.py`): test functions/methods named `test*` in `test_*.py`, multiplied by literal `parametrize` lengths where the argument list is a literal or a module-level literal name. Functions whose parameters are built dynamically are reported as "undetermined" and the static figure is a lower bound. Controller JUnit counts (results/) are used as the authoritative executed counts where they exist. |
| Result-artifact scan | Walked `results/**`, `reports/**`, `process/**`, `docs/**` listed in the lane prompt. |

## 1. Scenario denominators

| Quantity | Value | Basis |
|---|---:|---|
| Cognous catalog scenarios | 40 | SOURCE FACT `scenarios/catalog.json` (`scenarios` list 40; suites: deterministic 9 D01-D09, agent_and_human 8 = A01-A06 + H01-H02, supplemental 23 C01-C23). All 40 `status: NOT RUN`, `implementation_status: SPECIFICATION ONLY`, `results: []`. |
| AI Security Wiki cases | 656 | SOURCE FACT `scenarios/ai-security-wiki/catalog.json` (656 unique ids, id set equals applicability.json id set) |
| Total | **696** | 40 + 656 = 696 (arithmetic checks) |
| Where "696" is written | `README.md` ("696 specifications, all NOT RUN: 40 ... and 656 ..."), `suites/README.md` ("The 696 scenario-catalog entries retain their own NOT RUN statuses ..."). **`scenarios/README.md` does not contain the number 696**: it says "The 40 Cognous cases below are NOT RUN. A further 656 AI Security Wiki reference cases ..." (line 3). The prompt's "scenarios/README claims 696" is therefore imprecise; the claim lives in the root README and suites/README. |
| Wiki APPLICABLE | 20 | `applicability.json` counts {APPLICABLE 20, PARTLY_COVERED 45, NOT_APPLICABLE 591}; recomputed from `cases[]`, matches |
| Wiki PARTLY_COVERED | 45 | |
| Wiki NOT_APPLICABLE | 591 | each carries a reason (591 of 591); 19 are marked `close_call` |
| Wiki in scope (APPLICABLE + PARTLY_COVERED) | **65** | |
| Wiki split | W-I 17 (2 APPLICABLE + 15 PARTLY_COVERED); W-X 48 (18 + 30) | recomputed from `split` member; matches inventory section 5 |
| Wiki in-scope cases having at least one test in `suites/wiki-derived` | **61 of 65** (W-I 14, W-X 47) | I mapped test function names `test_wiki_<layer>_<nnn>` to case ids. Missing: TC-D09-004, TC-D13-003, TC-L02-002, TC-L08-033. Matches `inventory.json` `in_scope_without_wiki_derived_test` (4) and the md table (14 + 47). |
| Wiki in-scope with executed verdict | **0** | inventory: "every AI Security Wiki case remains NOT RUN until the controller runs"; `suites/wiki-derived` is not collected by any controller run (known-limits 2026-10-21: "not collected by the controller and does not enter the verdict") |
| In-scope subset of the 40 | UNKNOWN as a number | catalog `applicability` text: 17 (D01-D09, A01-A06, H01-H02) "Requires a declared supported profile and the relevant capability ... unsupported capability is NOT APPLICABLE with a reason, never a pass"; 23 (C01-C23) "Profile-specific; optional consumer, fleet, confinement and ...". The controller's requirement matrix has 40 `SCN-*` rows and **none NOT APPLICABLE** (g8: 27 INCONCLUSIVE, 13 NOT RUN). |
| Combined in-scope reference | 105 = 40 + 65 only if all 40 are treated as in scope; REASONED INFERENCE, the artifacts never state 105 | |

Stale/contradictory statements found (SOURCE FACT):
* `docs/test-inventory.md` section 5 "Current state" bullets (lines 158-162) say "39 of the 65 in-scope cases have tests (11 W-I, 28 W-X). All 39 are PARTLY_COVERED", "None of the 20 APPLICABLE cases has a test", and list 26 in-scope cases without a test. The same page's table (lines 113-116, 143-144) says 14 + 47 = 61 have tests and "All 18 APPLICABLE cross-component cases have a wiki-derived test". My name-based mapping gives 61, with all 20 APPLICABLE cases having tests. The bullets are stale; the table, the JSON twin and my count agree.
* `applicability.json` still marks TC-D12-004, TC-L02-016, TC-L06-039, TC-L06-045 `existing_implementation.status: needs_new_implementation` (paths []) and `inventory.json` says `applicable_needs_new: 4`, but `suites/wiki-derived` now contains `test_wiki_d12_004_*`, `test_wiki_l02_016_*`, `test_wiki_l06_039_*`, `test_wiki_l06_045_*` (WP-G2, WP-G5). Sidecar not updated.
* `docs/qualification-dashboard.md` says "Wiki specifications remain applicability-unassessed" (dashboard dated 2026-10-16); applicability.json exists and classifies all 656.

## 2. Distinct test counts per suite: inventory vs my reading vs controller

Full per-suite rows are in `F-evidence-suites.json`. Reconciliation, with method:

| Suite | Inventory | Independent figure | Method | Mismatch? |
|---|---:|---:|---|---|
| Category 1 total | 10,812 (15 rows, overlays excluded) | 10,812 | arithmetic over the 15 inventory counts (3071+1611+952+512+1183+366+311+545+491+245+81+121+257+413+653) | none; C1-03a (14) is shown separately and is not added |
| Category 2 "directly countable" | about 1,800 | 1,794 | 223+213+1093+50+17+38+160 | none |
| Category 3 | 290 collected | 265 static lower bound + 25 dynamic | AST over `suites/wiki-derived`: 262 funcs -> 265 param-expanded; 5 functions are dynamically parametrised (WP-C 3, WP-F 1, WP-G1 1). Splitting by case: W-I 57 static vs 64; W-X 199 vs 217; difference 7 + 18 = 25 = 290 - 265. 9 skeleton tests + WP tables sum exactly to 64/217/290 in the md. | cannot confirm 290 statically, but the gap is fully located in 5 dynamic functions |
| C1-14 qualification tooling | 413 (collected at bf865632, tests/native excluded) | **600 funcs at HEAD** (606 incl. tests/native, minus 6) | AST over `tests/` | **yes**: 413 inventory vs 416 (controller g2) vs 568 (controller g8, 1 skip) vs 600 static at HEAD. Count drifted with qualification main; the inventory number is for an old main. |
| X-18 tests/native | 6 | 6 | AST | none |
| X-06 operation-identity | 50 | 50 | AST | none |
| X-07 outside-holder | 17 | 17 | AST | none |
| X-03 security-runtime | 36 | 36 | AST (15 funcs x parametrisation) + controller native-f5b-suite 36 x 2 | none |
| X-01 v1-probes | 223 | 207 + 3 dynamic | AST; controller probes-* jobs sum 3+23+9+77+13+35+29+13+21 = 223 (+ provenance-scan 4 separate) | static lower bound only; controller confirms 223 |
| X-02 fix2-probes | 213 | 108 + 30 dynamic | AST | cannot confirm; no retained artifact |
| X-05 v1-scenarios | 1,093 | 630 + 49 dynamic | AST; controller g8 job scenarios 1093/0 failures | controller confirms 1093 |
| X-19 adversarial | 136 (per-file list) | 112 + 3 dynamic | AST; 17 of 20 files equal the inventory per-file figure exactly; T03 (inv 15, static 6) and T15 (inv 17, static 2) are dynamic | consistent |
| X-09 overlays | 5,763 | relocated overlay files alone: 1,379 param-expanded (12+449+157+106+358+115+182) | AST over 7 `suites/<repo>` dirs | not a mismatch: inventory says the 5,763 includes each component's own tests (overlaps Category 1) |
| C1-03a AGT | 14 | 14 (9 funcs) | AST on CP head `tests/test_microsoft_agt.py` | none |
| C1-03 CP | 952 | 632 funcs / 958 param + 21 dynamic at CP **head** | AST on CP 7a4bcd40 | different revision: controller g2 952 (2bac7875) -> g8 1194 (0a41faa9) |
| C1-04 Runtime | 512 | 306 funcs / 481 + 5 dynamic at Runtime **head** | AST on Runtime c5e97e87 | controller g2 512 (6b16962d) -> g8 532 (ec728da6) |
| C1-02, 05..13, 15 | various | not countable here | other repositories not cloned (source-access limitation) | controller JUnit used where a job exists |

Controller JUnit counts vs inventory (both at the r10 pins = run g2-r10 / 2026-10-20): action_manifest 245, bitrep 81, constitutional_authority 491, control_plane 952, gax 311, evidence pack 366, hub 653, runtime 512, replay 1183, ODES 3071, registry 121: **all equal the inventory counts exactly** (SOURCE FACT `results/v1-validation/v1-2026-10-16-a/g2-r10-39349033320/summary.json`). The newest retained run g8-r10 (r13 pins) differs: action_manifest 298, bitrep 95, constitutional_authority 520, control_plane 1194, gax 336, pack 374, runtime 532, ODES 3094, replay 1272 (20 skips), **registry 410 (inventory 121)**, qual-tooling 568 (inventory 413). The inventory page is a snapshot at r10/main bf865632 and is stale against g8 by up to 3.4x for the registry. No controller job exists for the verifier (C1-02, 1,611) or ergonomics (C1-08, 545); those two rest on the inventory page alone.

Suites present in the repo but **absent from the inventory** (SOURCE FACT `suites/README.md`): `suites/mvp-chain` (static 38 funcs / 48 + 7 dynamic), `suites/mvp-applicability` (6), `suites/mvp-d09` (12), `suites/mvp-d2-route-b` (34 incl. 5 `test_REACHABLE_*`). Also absent: the comparison (`comparators/`, inventory section 5 says "The comparison extension (the pre-registered Wiki subset) does not exist yet", yet `results/comparisons/g2-r10-20261020/` retains a run).

Inventory internal consistency: the md table and `inventory.json` agree on count and state for all 42 rows (script check, 0 diffs); 42 rows = 21 Category 1 (15 + 6 overlay "a" rows) + 19 Category 2 + 2 Category 3. Known-limit counts agree md vs JSON except W-I/W-X (JSON 6/29, md prose 6/29, same).

## 3. Case-to-test mappings in `scenarios/coverage-map.json`

| Quantity | Value |
|---|---:|
| mappings | 40 (ids equal catalog ids) |
| `mapping_status` | PARTIAL 32, UNIMPLEMENTED 6 (A01, C05, C15, C19, C20, C21), DEFERRED 2 (H01, H02) |
| Scenarios with zero tests | **7**: A01, H02, C05, C15, C19, C20, C21 (6 UNIMPLEMENTED + H02 DEFERRED) |
| Scenarios with at least one test | 33 (32 PARTIAL + H01 DEFERRED with 1 test) |
| Mapping entries (scenario to test) | 57 |
| Distinct tests (path + symbol) | **49** (41 mapped to one scenario, 8 mapped to two: D02/A02, D02/C18, D03/C07 x2, D08/C12, D08/C23, A03/C17, A05/C06) |
| Distinct test files | 23 |
| Owning suites | open-control-stack 23 files, execution-runtime 12, governed-exchange 5, ODES 5, replay 4 (symbols counted per distinct test) |
| Existence check | all 49 files exist in `suites/`; 49 of 49 symbols found in file text (4 are class-qualified `OracleTests.*`) |

`mapping_method` on **all 40** mappings (SOURCE FACT): "Static source association; proposed coverage, not accepted execution". `relation` on all 57 test entries: "supporting deterministic assertions; not whole-scenario acceptance". `scenario_verdict`: NOT RUN for all 40. Top-level `scope`: "40 Cognous cases only; Wiki applicability and actual-agent/human evaluation are not inferred". So the mappings are proposed coverage, not accepted execution.

**None of the 49 mapped tests was executed by the controller** (REASONED INFERENCE from a name search): I searched every JUnit XML in every retained controller run (`results/v1-validation/v1-2026-10-16-a/*/jobs/**/*.xml`, 39 files in g8) for the 49 symbols; 0 hits. The mapped tests are relocated overlay tests (`suites/cognous-*`), which belong to the overlay rows X-09/C1-xxa (inventory state ENV, BLOCKED here). The controller's own `SCN-*` rows are fed by `suites/v1-scenarios` and the matched-refund battery, a different test set. Consequence: the coverage-map ties scenarios to tests whose execution is not recorded anywhere in results/.

Per-scenario view (coverage map vs the newest controller run g8-r10, run 39690459403). "never mandatory" = A/H rows outside the controller's mandatory claim.

| ID | title | suite | coverage-map status | mapped tests | g8 controller row | g8 adequacy | mandatory pre-D15 |
|---|---|---|---|---:|---|---|---|
| D01 | Valid action | deterministic | PARTIAL | 2 | INCONCLUSIVE | None | moved out by D15 |
| D02 | Binding substitution | deterministic | PARTIAL | 2 | INCONCLUSIVE | partial | moved out by D15 |
| D03 | Authority changes | deterministic | PARTIAL | 2 | INCONCLUSIVE | None | moved out by D15 |
| D04 | Ambiguous delivery | deterministic | PARTIAL | 2 | INCONCLUSIVE | None | moved out by D15 |
| D05 | Partial effect | deterministic | PARTIAL | 1 | INCONCLUSIVE | partial | moved out by D15 |
| D06 | Ingress pressure | deterministic | PARTIAL | 1 | INCONCLUSIVE | partial | moved out by D15 |
| D07 | Restore boundary | deterministic | PARTIAL | 3 | INCONCLUSIVE | partial | moved out by D15 |
| D08 | Audit and export | deterministic | PARTIAL | 2 | INCONCLUSIVE | partial | moved out by D15 |
| D09 | Bypass and interruption | deterministic | PARTIAL | 2 | INCONCLUSIVE | partial | moved out by D15 |
| A01 | Workflow fidelity | agent_and_human | UNIMPLEMENTED | 0 | NOT RUN | None | never mandatory |
| A02 | Indirect injection | agent_and_human | PARTIAL | 1 | NOT RUN | None | never mandatory |
| A03 | Memory continuity | agent_and_human | PARTIAL | 1 | NOT RUN | None | never mandatory |
| A04 | Session isolation | agent_and_human | PARTIAL | 1 | NOT RUN | None | never mandatory |
| A05 | Tool failure | agent_and_human | PARTIAL | 1 | NOT RUN | None | never mandatory |
| A06 | Handoff integrity | agent_and_human | PARTIAL | 1 | NOT RUN | None | never mandatory |
| H01 | Approval behavior | agent_and_human | DEFERRED | 1 | NOT RUN | None | never mandatory |
| H02 | Human intervention | agent_and_human | DEFERRED | 0 | NOT RUN | None | never mandatory |
| C01 | Missing grant | supplemental | PARTIAL | 2 | INCONCLUSIVE | partial | moved out by D15 |
| C02 | Unknown action and manifest mismatch | supplemental | PARTIAL | 2 | INCONCLUSIVE | partial | moved out by D15 |
| C03 | Forged and replayed attestation | supplemental | PARTIAL | 1 | INCONCLUSIVE | partial | moved out by D15 |
| C04 | Evidence supersession and dependence | supplemental | PARTIAL | 1 | INCONCLUSIVE | partial | moved out by D15 |
| C05 | Optional evidence unknown | supplemental | UNIMPLEMENTED | 0 | NOT RUN | None | moved out by D15 |
| C06 | Authoritative observer unavailable | supplemental | PARTIAL | 2 | INCONCLUSIVE | partial | moved out by D15 |
| C07 | Concurrent authority change | supplemental | PARTIAL | 2 | INCONCLUSIVE | partial | moved out by D15 |
| C08 | Crash and restart | supplemental | PARTIAL | 2 | INCONCLUSIVE | partial | moved out by D15 |
| C09 | Repeat delivery | supplemental | PARTIAL | 1 | INCONCLUSIVE | partial | moved out by D15 |
| C10 | Executor confinement | supplemental | PARTIAL | 2 | INCONCLUSIVE | partial | moved out by D15 |
| C11 | Credential and permission boundaries | supplemental | PARTIAL | 2 | INCONCLUSIVE | partial | moved out by D15 |
| C12 | Producer consumer compatibility | supplemental | PARTIAL | 3 | INCONCLUSIVE | partial | moved out by D15 |
| C13 | Redaction and signing | supplemental | PARTIAL | 2 | INCONCLUSIVE | partial | moved out by D15 |
| C14 | Optional ODES consumer | supplemental | PARTIAL | 2 | INCONCLUSIVE | partial | moved out by D15 |
| C15 | Conflicting proposals | supplemental | UNIMPLEMENTED | 0 | NOT RUN | None | moved out by D15 |
| C16 | Shared budget exhaustion | supplemental | PARTIAL | 1 | INCONCLUSIVE | partial | moved out by D15 |
| C17 | Stale shared state | supplemental | PARTIAL | 1 | INCONCLUSIVE | partial | moved out by D15 |
| C18 | Bounded delegation | supplemental | PARTIAL | 1 | INCONCLUSIVE | partial | moved out by D15 |
| C19 | Fleet suspension | supplemental | UNIMPLEMENTED | 0 | NOT RUN | None | moved out by D15 |
| C20 | Policy improvement adoption | supplemental | UNIMPLEMENTED | 0 | NOT RUN | None | moved out by D15 |
| C21 | Proportional review and remedy | supplemental | UNIMPLEMENTED | 0 | NOT RUN | None | moved out by D15 |
| C22 | Equal conditions comparison | supplemental | PARTIAL | 3 | INCONCLUSIVE | partial | moved out by D15 |
| C23 | Evaluator calibration | supplemental | PARTIAL | 4 | INCONCLUSIVE | partial | moved out by D15 |


## 4. Executed versus merely collected: what result artifacts exist

### 4.1 The inventory's "no gate has been run" statement, quoted and checked

Quote (SOURCE FACT `docs/test-inventory.md` line 5): "It is an inventory, not a result. No gate has been run. The qualification controller (`tools/v1_validation.py`) has not been run for it, nothing here is a verdict, and every AI Security Wiki case remains NOT RUN until the controller runs."

Verification:
* "No **release test gate** (OCS-1/2/3) has been run" holds in the sense that no `results/release-gate/<candidate-id>/<run-id>/` directory exists (the retention path required by inventory section 7 step 6) and no artifact carries a gate verdict. REASONED INFERENCE from absence.
* "The controller has not been run for it" is true only for the release-gate candidate. The **V1 validation controller was run 21 times** (21 retained run directories with a `run-identity.json` under `results/v1-validation/v1-2026-10-16-a/`, plus 2 derived re-evaluations: `addenda-merge-1`, `final-linux-1-...-reduced-scope`), including `g2-r10` (run 39349033320, r10 pins, 2026-10-20) through `g8-r10` (run 39690459403, r13 pins, 2026-10-21) after the inventory date (2026-10-19). `docs/v1-known-limits.md` entries of 2026-10-20 and 2026-10-21 record them. The inventory row X-15 and blocker B-06 ("its run has not been made") are therefore **stale**, and so are the X-03 / X-05 / X-16 states (NOT_RUN_HERE / NOT_RUN_HERE / PARTIAL) because controller jobs for native-f5b-suite, scenarios and matched-refund-rerun exist and passed in g2 and g8.
* Even so, the known-limits file itself (entry 2026-10-20) says the V1 controller runs "are not a release decision" and the inventory pair "is not changed by this entry".
* "Every Wiki case remains NOT RUN" is consistent with the artifacts: `suites/wiki-derived` is outside the controller; its executions are direct local runs with no retained artifact (see 4.3).

### 4.2 Retained result artifacts

All dates are from the artifact or the cited doc; `summary.json` of controller runs carries no timestamp, so run dates are from `docs/v1-known-limits.md` where stated.

| Artifact (results/ or reports/) | Records | Date | Source pins in force | Produced by controller? |
|---|---|---|---|---|
| `v1-validation/.../baseline-38955005409`, `harness-fix-1-...`, `fix2-38958014779`, `matrix1-...`, `final-38962759690` | early runs; verdicts INCOMPLETE / INCOMPLETE / INCOMPLETE / FAIL / FAIL | 2026-10-16/17 (inferred from run ids; not stated) | original freeze (hub 8517818f, runtime e20f92e1, CP a34c3dc2) | Yes (GitHub Actions `v1-validation.yml`, `tools/v1_validation.py`) |
| `step2`, `step2b`, `scn1`, `scn2b`, `full1`, `refreeze-r1b`, `refreeze-r2` | FAIL (x6) and INCOMPLETE (refreeze-r2: freeze FAIL, 23 INCONCLUSIVE jobs) | 2026-10-17 (inferred; undated in artifacts) | refreeze entries RF-1..RF-10 era | Yes |
| `final-linux-1-39032930011` | **FAIL**: 54 PASS / 3 FAIL / 34 INCONCLUSIVE / 20 NOT RUN / 20 N/A of 131 rows; mandatory 39 PASS / 2 FAIL / 29 INCONCLUSIVE / 5 NOT RUN | 2026-10-17 | profile r1/r2 era | Yes |
| `final-linux-1-39032930011-reduced-scope` | same data re-evaluated offline with D15 file: verdict **PASS** over 39 rows | 2026-10-17 | same | Derived, not a new execution |
| `g2-r10-39349033320` | verdict PASS (reduced); jobs 33 PASS / 3 FAIL (ODES x2 py + scenarios, all declared) / 2 NOT RUN; rows 56 PASS, 0 FAIL, 35 INCONCLUSIVE, 20 NOT RUN, 20 N/A; unreduced mandatory INCOMPLETE | 2026-10-20 | **r10** (CP 2bac7875, runtime 6b16962d, ...) | Yes |
| `g3`, `g4`, `g4b`, `g5` | PASS (reduced); g4: 1 INCONCLUSIVE job (install stop); g4b: 14 SCN-C03 cases INCONCLUSIVE (harness exception); g5 qualifies registry d25afe60 + attestation 981036c3 | 2026-10-20/21 (g5 dated 2026-10-21 in known-limits; g3, g4, g4b undated) | r10 + registry/attestation moves | Yes |
| `g6-r10-39563114678` | PASS as produced; **reads INCOMPLETE when re-aggregated by the hardened controller** (E-2, freeze record had 0 components) | 2026-10-21 | profile r11 | Yes, pre-hardening controller |
| `g7-r10-39642578239` | PASS (reduced); jobs 34 PASS / 2 FAIL (ODES declared) / 2 NOT RUN | 2026-10-21 | profile r12 | Yes, hardened controller |
| **`g8-r10-39690459403`** (newest) | verdict PASS (reduced, 39 mandatory rows); unreduced mandatory **INCOMPLETE** (75 rows: 40 PASS, 30 INCONCLUSIVE, 5 NOT RUN); full catalog 131 rows: 56 PASS, 0 FAIL, 35 INCONCLUSIVE, 20 NOT RUN, 20 N/A; jobs 34 PASS / 2 FAIL (ODES py3.11, py3.12: 3094 cases, 4 declared failures, 1 skip) / 2 NOT RUN (prp, tfa: no tests); freeze PASS; `blocking_jobs` [] | 2026-10-21 (known-limits entry) | **r13** (CP 0a41faa9, runtime ec728da6, Replay 028f63d1, pack a3ebbb90, ODES e86a25a1, exchange 7f7569b0, manifest fa170815, bitrep 981036c3, registry b2485998, authority 9b5ab721; freeze-verification record) | Yes |
| `comparisons/g2-r10-20261020` + `reports/comparison-g2-r10-2026-10-20.md` | corner OCS 190/190, comparators 130/190; baseline 3-way tie 480/480; Wiki subset OCS asked 4 of 121 | 2026-10-20 | qual 32ed1916, hub 8517818f, r10 candidate manifest | No: comparison runner (`comparators/runner/run_comparison.py`) |
| `comparisons/matched-refund-20261016` + `reports/matched-refund-2026-10-16.md` | 20/20 matched synthetic refund trials PASS; mutation controls reject | 2026-10-16 | hub 8517818f, qual 347df5d8 era | No (tools/run_matched_refund.py); later re-run by controller job matched-refund-rerun 20/20 |
| `security-runtime-f5b-20261016` | 36 JUnit cases x 2, 0 fail/error/skip; hosted run 38925303886 (pull_request) | 2026-10-16 | qual 7022881e, profile f5b original (CP a34c3dc2, runtime e20f92e1, ...) | No (hosted CI, not V1 controller) |
| `security-runtime-merged-20261016` | 36 x 2 pass; `qualification_worktree_dirty: true` disclosed in docs/security-residuals | 2026-10-16 | qual 5edcc08e | No |
| `u1-security-20261015` | hub tests 627 + 122 subtests, suite unit tests 44, gate tests 92; `coverage: partial`; `operational_trust: HOLD / NOT ESTABLISHED` | 2026-10-15 | hub c3b919d1, qual 78b3f42c | No |
| `final-source-preflight-20261016` | **BLOCKED: source admission. Integrated scenarios NOT RUN**; 9 admission checks failed | 2026-10-16 | seven candidate commits (superseded) | No |
| `serial/native-20261015`, `serial/native-exchange-20261016` | 36 named local variants PASS; "model_trials: NOT RUN"; "human_oversight: NOT EVALUATED"; catalog acceptance UNCHANGED | 2026-10-15/16 | hub 8517818f, qual 347df5d8 | No |
| `verifier-mutation/run-3..5` | report-only mutation measurement (1,951 / 4,143 / 4,147 verifier runs), no PASS/FAIL verdict | 2026-10-18 | verifier adb8927 / 5974c50 / 0a43a7f0 | No |
| `security-coverage-20261015` | static path screening of 13 component revisions (5,561 paths) + 27 targeted traces; "Checksums show retained-byte consistency, not reviewer independence or security assurance" | 2026-10-15 | hub 5715f791 / 52fdbcda | No |
| `workflows/` (14 snapshots) | GitHub-reported workflow outcomes of component CI; `component_set.completeness: UNVERIFIED`, production/release false | 2026-10-15/16 | component heads of that date | No; "not catalog scenario acceptance" (results/README) |
| `prp-openai-20261015` | 18 trials, 36 live OpenAI calls (gpt-6.1-sol), USD 0.396; PRP showed "no measured improvement over baseline" | 2026-10-15 | PRP b3ffa855 | No; PRP is outside the gate by SE-1 |
| `readme-commentary/` | relocated component README commentary | n/a | n/a | Not a result |

Actual-agent pilot (T4): `qualification/orchestration-state.json` and `docs/qualification-dashboard.md` record a completed bounded OpenAI pilot (run 38821035491, 25 of 25 trials PASS, five synthetic variants x5, hub 4bb101ca). The raw manifest/ledger is a GitHub artifact (id 12013785164), **not in this checkout** (UNVERIFIED). The dashboard states it "does not qualify all A01-A06 obligations", and the controller rows SCN-A01..A06 and H01/H02 read NOT RUN ("no accepted execution ... needs paid agent runs or human participation").

### 4.3 Collected versus executed versus recorded, by evidence class

* Recorded by a retained controller artifact (JUnit + result.json): component suites C1-01, 03, 04, 05, 06, 07, 09, 10, 11, 12; qualification tooling C1-14; hub tests C1-15; native-f5b X-03; probes X-01 (223 + 4 provenance); scenarios X-05 (1,093); matched-refund-rerun (20).
* Recorded only on the inventory page (measured outside the controller, no artifact in results/): C1-02 verifier, C1-03a, C1-08, C1-13 (private), X-02, X-06, X-07, X-10 (private), X-11 (private, FAIL), X-12, X-19, and the local W-I / W-X runs (63/1 and 213/4 at r10; 285 pass / 5 fail whole-suite at r13).
* Collected only: X-18 (6 tests, outcomes not re-measured), mvp-d2-route-b, mvp-d09.
* Never run (no artifact): C1-15a, X-04, X-17 (hub delegated workflows), MVP acceptance battery ("no dispatched run exists yet", `process/mvp-acceptance/README.md`).

### 4.4 Scenario-level status (40 catalog scenarios)

Controller requirement rows `SCN-*` in g8 (SOURCE FACT `g8-r10-39690459403/requirements-matrix.json`): **0 PASS, 27 INCONCLUSIVE, 13 NOT RUN, 0 FAIL, 0 NOT APPLICABLE**. Zero scenarios have an accepted-PASS record. 32 of the 40 rows were moved out of the mandatory claim by D15 after the results were seen (list in `docs/v1-known-limits.md`); the other 8 (A01-A06, H01, H02) were never mandatory.


## 5. Historical pins versus current component heads

Current heads you named: Control Plane `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c`, Runtime `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f`. I confirmed both against the local clones (`git rev-parse HEAD`). Both clones are shallow (1 commit), so **I cannot say what changed between any historical pin and these heads, or whether a pin is an ancestor**: UNVERIFIED. Dates: CP head merge 2026-10-23 09:06 -0700 (PR #83 "f3-claim-journal"); Runtime head merge 2026-10-23 16:54 -0700 (PR #144 "f3/approval-revocation-terminal"). The newest controller run g8 was 2026-10-21, so both heads postdate it.

Resolution method: `suites/_pins.py` = `freeze-manifest.json` overridden by `refreeze-log.json` entries whose status matches APPLIED. I ran the module (stdlib only, `python -I`) and got 61 log entries, 61 applied, 0 errors. Profiles r1, r2, r10, r13 read from `process/security-runtime-f5b-20261016*.json` (16 files: original, candidate, r1..r13).

| Component | freeze-manifest (2026-10-16) | r1 | r2 | **r10** (inventory counts) | **r13** (in force; controller g8) | Last refreeze entry marked "qualified" in the log | MVP proposed tuple (2026-10-24, "PROVISIONAL, UNQUALIFIED") | Current head read |
|---|---|---|---|---|---|---|---|---|
| Control Plane | a34c3dc2 | a34c3dc2 | a34c3dc2 | **2bac7875** | 0a41faa9 (RF-55, "probed", not qualified) | RF-29 -> 2bac7875 | **7a4bcd40** | **7a4bcd40** |
| Runtime | e20f92e1 | 4a83b175 | 4a83b175 | **6b16962d** | ec728da6 (RF-56, probed) | RF-37 -> 6b16962d | **c5e97e87** (post-F3; "pre-F3 was ec728da6") | **c5e97e87** |
| Replay | 79ba16d4 | 0cfe7a63 | def0ee0f | 6a6a4774 | 028f63d1 (RF-57) | RF-38 -> 6a6a4774 | 40012b8c | not cloned |
| Evidence pack | 893aca8d | 683246e0 | 505a3590 | fd030615 | a3ebbb90 (RF-58) | RF-39 -> fd030615 | 7b9511f2 | not cloned |
| ODES | eb83220c | 4e6d1169 | 5675f1b9 | 2893d935 | e86a25a1 (RF-59) | RF-40 -> 2893d935 | 1a5e1d30 | not cloned |
| Exchange | 8be6c6b8 | da953782 | ec6ba5bd | fdc2a410 | 7f7569b0 (RF-60) | RF-41 -> fdc2a410 | excluded (route C) | not cloned |
| Action manifest | 2c36bcd0 | 2c36bcd0 | 2c36bcd0 | ff549082 | fa170815 (RF-48, probed unchanged) | RF-35 -> ff549082 | fa170815 | not cloned |
| Attestation (bitrep) | 5b5077da | - | - | 5b5077da (move to 981036c3 by RF-43 after r10, qualified in g5) | 981036c3 | RF-43 -> 981036c3 | not in tuple | not cloned |
| Registry (the_index) | d5e45d27 | - | - | d17b8ac2 (RF-1, qualified) | b2485998 (RF-61, probed; workflow+log only, not in profile) | RF-44 -> d25afe60 | not in tuple | not cloned |
| Constitutional authority | fb3d9793 | - | - | 0124adcd (r9/r10) | 9b5ab721 (RF-46, probed unchanged g7/g8) | RF-36 -> 0124adcd | not in tuple | not cloned |
| Verifier | not in manifest; C1-02 measured at dc09a98f | | | dc09a98f | not a controller component | n/a | c0b8ba1f (later docs revision 39d46b49 "not adopted") | not cloned |
| Hub | 8517818f (freeze identity) | | | 8517818f (r10 hub pin) | 8517818f | n/a | c897266b | 51c579a3 (clone) |

(SOURCE FACT: `process/v1-validation/v1-2026-10-16-a/freeze-manifest.json`, `refreeze-log.json`, `process/security-runtime-f5b-20261016-r{1,2,10,13}.json`, `process/mvp-chain/tuple-pin.proposed.json`, `results/.../g8-r10-39690459403/jobs/freeze/freeze-verification.json`. Profiles r3..r9, r11, r12 exist and show the intermediate pins; e.g. CP 26a7e659 (r3), 3cd17ead (r5), 2bac7875 (r9, r10, r11), e77fe0ee (r12), 0a41faa9 (r13); runtime 3024ef6e, 11de097c, c4a05883, 6b16962d, cab4d9ab, ec728da6.)

What each artifact speaks for:
* **Inventory counts and every "PASS" in `docs/test-inventory.md`**: r10 pins (CP 2bac7875, runtime 6b16962d, Replay 6a6a4774, pack fd030615, ODES 2893d935, exchange fdc2a410). Not CP 7a4bcd40, not Runtime c5e97e87. Inventory also names r13 in the X-03 command and B-12 (pin graph) but its counts are r10. One explicit statement in known-limits: "No qualification-controller run has been made at the r10 pins; every earlier verdict is historical and is not transferred" (entry of 2026-10-19; superseded by g2-r10 on 2026-10-20).
* **Controller run g8-r10**: r13 pins (CP 0a41faa9, runtime ec728da6). `docs/v1-known-limits.md`: "The controller run g7-r10 was made at the earlier revisions and is not transferred to the new tuple"; the same principle applies to g8 versus later heads. Refreeze statuses for RF-46..RF-61 read "probed ... not marked qualified" because the unreduced mandatory verdict is INCOMPLETE.
* **Earlier "qualified" log entries (RF-1..RF-44)** come from controller runs before the hardening of the verdict machinery. `docs/v1-known-limits.md` (2026-10-21, "verdict machinery: independent review findings E-1 to E-11") says that machinery "could report PASS when it should not" and that "No run at the hardened controller has qualified any pin yet" (g7 entry). E-6, E-12, E-13 remain open.
* **MVP tuple (CP 7a4bcd40 / Runtime c5e97e87)**: the only plan aimed at the current heads, and it has not been run: "no dispatched run exists yet" (`process/mvp-acceptance/README.md`). Oracle `expectations.proposed.v7.json` is "PROPOSED ... for Qualification's independent review, acceptance and freeze"; `os_level_process_kill` is "UNQUALIFIED".
* **Pre-F3 Runtime ec728da6 results**: `suites/mvp-d09` is "bound to the frozen V1 profile (pre-F3 ec728da6)"; NC1-04 (approval revocation terminality) "failed at the pre-F3 Runtime ec728da6" (mvp-acceptance README). Runtime c5e97e87's PR #144 is titled "terminal approval revocation per approval_ref". Whether it fixes NC1-04 is "a result of a run, not asserted". Evidence about approval revocation at ec728da6 does not speak for c5e97e87.
* **Wiki-derived tests (W-I/W-X)**: local runs at r10 (63+1 failed; 213+4 failed) and r13 (285 pass, 5 fail); none at the current heads.
* **Comparison g2-r10-20261020**: r10 candidate manifest (qual 32ed1916), historical.
* **Results from 2026-10-15/16** (`security-runtime-*`, `u1-security`, `serial/*`, matched-refund): original freeze pins; "Historical evidence does not qualify changed configurations" (`results/README.md`).

Clearly at a historical pin and not speaking for current heads: every row of the per-suite table flagged `historical_pin_does_not_speak_for_current_heads: true` (34 of 42 inventory rows). The 8 `false` rows are the ones that carry no pin-bound result: C1-14 (qualification tooling, not a component pin), X-15 (the controller itself), and the never-run rows C1-15a, X-04, X-13, X-14, X-17, X-18. C1-10's manifest pin fa170815 equals the MVP tuple's manifest pin, but its inventory count (245) was taken at ff549082, so it is flagged historical too.

Known-limit tests at the heads (SOURCE FACT, read from the clones): CP head `tests/` has 10 functions named `*_known_limit` (one parametrised, 11 cases; the controller g8 declared set has the same 11) so the declared list is consistent at head by count. Runtime head `tests/` has **11 functions named `*_known_limit`** (tenant evidence, amount binding, attempt transition, issue time, budgets) that are in neither the inventory (C1-04 `known_limit: false`) nor the controller's declared set (72 entries, none from the runtime).

## 6. Developer versus independent qualification: who ran what

Default for everything in this repository: **developer-run, synthetic, Cognous-configured**. Statements found (SOURCE FACT):
* Scope text on the inventory, the pre-registration and every report: "Bounded synthetic profile only. The comparator applications ... are configured by Cognous, not vendor implementations. This is not independent certification and not production readiness; operational trust stays on HOLD. Linux only."
* Pre-registration: the corner plan "was authored after inspection of the baseline code and is not blinded, and both plans had no independent review; the shared Cognous wire and signature helpers feed all three configurations" (RP-8).
* Controller runs are executed by GitHub Actions workflows dispatched by "the coordinator, after the owner's go" (RO-7); declarations and reclassifications are made by "the coordinator, owner-approved delegate (OD-10)"; authorisations are by the validation owner André de Lima (refreeze-log `authorised` fields; D15 "on the owner's direction ... if remediation would take too long, reduce scope coverage so that everything claimed passes"). Workers do not run the gate (inventory section 7).
* Retained-evidence statements: "Local/hosted synthetic destination observation is not independently operated external verification" (`security-runtime-merged-20261016/README.md`); "Checksums show retained-byte consistency, not reviewer independence or security assurance" (`security-coverage-20261015/README.md`); `qualification/orchestration-state.json` records `scqos_rerun: false` for the matched-refund exchange.
* "Independent" appears for: independent static review of the authority repository (g6 entry), independent review of the controller (E-1..E-11), "independent scans 3 and 4" and "5 and 6" (refreeze motivations). **The artifacts do not identify who the reviewers were** (UNVERIFIED: whether they were separate from the developers). The MVP acceptance job is called "An independently owned Qualification job" but the same README says "Qualification owns the oracle and every verdict, the builder only proposes", and the oracle text refers to an "independent Q1 review" of builder-prepared predicates. The oracle is PROPOSED, not frozen.
* No third-party, regulator, customer or vendor run is recorded anywhere in `results/` or `reports/`.

## 7. Synthetic-only versus operational evidence

* **All** retained executions are synthetic: local SQLite destinations, synthetic $10 refund, synthetic wallet, shared simulation clock, Linux only. Inventory: "All data is synthetic; no network, model, payment or human reviewer is used" for Category 1; Wiki tests use "route A/B/C" synthetic destinations only.
* `operational_trust: HOLD / NOT ESTABLISHED` (u1-security summary); `OPERATIONAL-ASSURANCE` blocker in the dashboard: "Read-only observer shares a trusted OS user; process/network containment and production identity are outside these fixtures ... Deployment-specific configuration and independent access evidence before operational claims". `embedding-exposure/1`: "deployment_verified=false" always; "Actual deployment configuration is unavailable. All nine exposure surfaces remain unverified."
* Live-model evidence: OpenAI pilot 25/25 (diagnostic, synthetic, five variants, not in this checkout) and PRP K6 (36 calls, out of gate scope). Human oversight: "NOT EVALUATED".
* No customer, healthcare, financial or production deployment evidence exists in the qualification corpus (nothing found; absence in the files I read, REASONED INFERENCE).
* Not covered by any retained run (from the known-limits and controller notes): tenant concept on the exchange route / OpenShell destination (SCN-D02, C01, C02, C09, C10 inconclusive), credential broker (C10, C11), ingress limiter (D06), external anchor (D07), OS-level kill (C08; MVP battery lists it UNQUALIFIED), sub-delegation (C18), fleet suspension (C19 NOT RUN), exchange-route budget (C16).

## 8. Known-limit tests, listed apart (never counted as protection)

A known-limit test passes (or xfails strictly) by showing that a limit exists. They evidence KNOWN_GAP, not protection. Counts per suite:

| Suite | Count | Names / source | How it shows in a run |
|---|---:|---|---|
| C1-01 ODES | 4 | test_control_legacy_export_is_digest_identical_to_the_retained_example; test_explicit_export_end_to_end; test_control_producer_v2_examples_pass_the_semantic_layer[lost_ack.package.json]; [prior_absence.package.json] (am.29-32) | FAIL as declared; ODES job FAIL in g2 and g8 |
| C1-03 Control Plane | 11 | `tests/test_known_limits.py` (week-old decision still executes; hold has no binding; grant naming a parent not authorized; same operation id replay refusal; removed operation rows; claim consumption does not see identity/mandate status change [x2 params]; cumulative counters per grant id; action without authority context does not pin context ref), `test_amount_substitution.py::test_numeric_forms_inside_the_payload_are_distinct_bytes_known_limit`, `test_minimum_count_zero_known_limit` (am.47-57) | PASS by asserting the limit; g8 lists 4 of them as "declared test did not fail as declared" reportable conditions |
| C1-05 / C1-05a Replay | 5 | `tests/test_contract_lifecycle_conformance.py` strict expected failures (reasons-match-extra-reason...; reasons-minimum-unreadable...; executor-unknown-validated-unknown...; result-unknown-null-attempt-id; result-unknown-unregistered-attempt-id) (am.58-62); same 5 in the overlay row, not additive | recorded as skipped (strict xfail) |
| C1-04 Runtime | not declared; **11 `*_known_limit` functions exist at head c5e97e87** | test_evidence_tenant_known_limit.py (3: no tenant column; two tenants share one row; shared row couples tenants), test_amount_binding_and_known_limits.py (4), test_attempt_transition_characterisation.py (4) | UNKNOWN how they behave in a run; inventory `known_limit: false` |
| C1-09, C1-15 | 0 | inventory states none identified (checked by name) | n/a |
| X-01 v1-probes | 6 | test_authority_ra_probes.py: opened event binds component version; resolution result records observation time and age; evidence refusal records criterion reference; registry declares reopen predicates; refusal trend names unmapped codes; freshness verified before criterion (registered findings F-16, "spec gap") | strict xfail, recorded skipped; row ADD-AUTH-RA FAIL |
| X-02 fix2-probes | 6 | test_journal_rules_probes (3: closeout/reconciliation dated before attempt, odes x2 + verifier), test_runtime_probes (failure_after_commit_reports_unknown os-error, runtime-error), test_verifier_probes (binding member changed alone ...journal-applied-effective_max_effects) | strict xfail; not collected by controller |
| X-05 v1-scenarios | inventory 4, **0 in force at g8** | SCN-C04 copy cases, declarations withdrawn (am.109, 117-119) after the cases passed | the withdrawal "covers only the three cases that passed"; F-19 not described as closed for other inputs |
| X-12 / X-15 | "present, not enumerated" | | |
| X-19 adversarial | 4 | T05 `test_evaluators_agree_on_every_variant[namespace_prefix]` and `[exact_target_as_prefix]`; T07 `test_route_a_unspent_decision_after_recreation[identical]` and `[new_status_version]` (am.69-72) | strict xfail |
| W-I | 6 named | TC-L06-018 (x2), TC-L06-026, TC-L06-038, TC-L06-040 (x2) | pass by asserting the limit; local only |
| W-X | 29 named | 23 distinct cases: TC-D12-004, D12-007, D12-018 (x2), L02-016, L02-025 (x2), L03-022, L05-013, L06-003, L06-009, L06-014, L06-015, L06-020, L06-028, L06-034, L06-039 (x2), L06-045 (x2), L09-018, L09-019, L09-025, L15-019, L17-002 (x2), L17-004 (x2), L17-021 | pass by asserting the limit; local only |
| Declared set (controller g8) | 72 entries = 71 tests + 1 requirement (ADD-AUTH-RA) | CP 11, Replay 5, ODES 4, v1-probes 6, wiki-derived 35, fix2 6, adversarial 4 | only 26 are matchable by the controller (CP 11, probes 6, Replay 5, ODES 4); 35 + 6 + 4 are outside the controller |
| mvp-d2-route-b | 5 `test_REACHABLE_*` | "pass when a hole exists" | collected only, not in inventory |

Inventory total with enumerated known limits = 4+11+5+6+6+4+4+6+29 = 75 (C1-05a not added); minus the 4 withdrawn X-05 declarations = 71 = controller declared test count. (Arithmetic check, matches.)

Wiki-derived tests failing locally and not declared at r13 (reported non-gating): TC-L06-022 (stop event sequence must increase), TC-L15-019 (`unknown` where `denied`), TC-L09-004 (`unknown` where `absent`), TC-L06-018 (`GAX-FRESHNESS-CREATED-AFTER-EXPIRY` where `...EXPIRED`), TC-L06-040 (retired test). Known-limits says each "failed in the same way at the previous pins" and none was classified a major defect. These are failing/lagging tests, not known limits and not passes.

## 9. Inventory blockers B-01..B-12 as they bear on a release gate

State is the inventory's own words (`docs/test-inventory.md` section 6, `inventory.json` blockers); "Later artifact" is what newer files show. The inventory says the gate is not met: "The inventory run found 12 blockers".

| ID | Inventory state | Bearing on a release gate | Later artifact (newer than the inventory) |
|---|---|---|---|
| B-01 fix2-probes marks / 6 remaining known limits, decision per group pending | being resolved | 6 probes remain strict xfail known limits; keep/revise/harden decision pending; they are not passes | Unchanged at 2026-10-20 (207 pass + 6 xfail); suite README still names r9 heads |
| B-02 CP real-SDK test skips; AGT needs pytest-asyncio | **open** | 1 skip declared (am.82) but unmeasured with the SDK; AGT file errors without pytest-asyncio; environment check must verify the plugin | g8 CP job still 1 skip per Python version |
| B-03 ODES/Replay accepted-revision graph | resolved for r10; **open for Replay main** | Replay main is not an accepted ODES/pack revision, so a gate against main fails | Re-tied at r13 (ODES e86a25a1 etc.); MVP tuple moves Replay again to 40012b8c |
| B-04 tests/helpers lag component changes at main | **open** | Failing tests at main (runtime helpers 11, overlay 1, orchestrator overlay 3 = X-11 FAIL) block OCS-2 until fixed or reclassified | Five wiki-derived tests lag (r13); CP #81/#82 changes forced amendments 124-125 |
| B-05 Replay-pack pairing test | resolved by #175 | no longer a blocker at r10 | n/a |
| B-06 v1-probes known limits / controller run not made | being resolved | probes 223 = 217 pass + 6 xfail at r10 | **Controller run was made** (g2..g8); the "has not been made" wording is stale |
| B-07 in-body and conditional skips | resolved by #174/#175 | 36 declared skips (am.80-84); declared skip is not a pass | g8 Replay shows 20 skips (inventory 12 in-body + 5 xfail = 17 at r10): 3 more than the r10 figure, not explained in the inventory |
| B-08 overlay/delegated suites need pinned producer checkouts, no environment builder | **open** | X-09 (5,763), overlay rows C1-04a/05a/06a/07a stay ENV and cannot be counted as run | `tools/rc_env.py` + `docs/release-gate/environment.md` (measured 2026-10-19) now exist: overlay skips 439 -> 102, failures/errors 124 -> 0, but 102 skips remain, the delegated hub workflows and the controller are not covered; inventory section 7 still says "The builder does not exist yet" |
| B-09 load-sensitive tests | **open** | Fixed short timeouts (C1-04, C1-05, C1-07, C1-15, X-05); gate requires serial runs | none |
| B-10 shallow checkouts / node install | **open** | 3 hub tests fail on depth-1; probes need history and node | rc_env.py has `--full-history`; none for node |
| B-11 native tests of three repos not all run by own CI | **open** | C1-11 (CI runs 1 test), C1-12, C1-09 (subset) | none |
| B-12 pin graph | **open** | gate step 1 requires X-14 exact-chain consistency check with "no split and no behind-main pin" | X-14 still PLAN; three different tuples now exist: r10 (inventory), r13 (g8), MVP (CP 7a4bcd40 / Runtime c5e97e87), all behind or ahead of each other; none run together |

Blockers open per the inventory: 7 (B-02, B-04, B-08, B-09, B-10, B-11, B-12); being resolved 2 (B-01, B-06); resolved 3 (B-05, B-07, B-03 partially: "resolved for the r10 pins; open for Replay main").

## 10. Global evidence-status distribution

### 10.1 The 42 inventory suite rows (details in `F-evidence-suites.json`)

| Inventory `state` | Rows |
|---|---:|
| PASS | 16 |
| ENV | 9 |
| NOT_RUN_HERE | 9 |
| PARTIAL | 3 |
| PLAN | 2 |
| NOT_RUN | 2 (W-I, W-X) |
| FAIL | 1 (X-11) |

| `evidence_status` (brief vocabulary, my assessment from artifacts) | Rows | Notes |
|---|---:|---|
| PASS_RECORDED | 25 | 15 backed by a retained controller artifact (C1-03, 04, 05, 06, 07, 09, 10, 11, 12, 14, 15, X-01, X-03, X-05, X-16); 10 rest on the inventory page alone (C1-02, C1-03a, C1-08, C1-13 private, X-02, X-06, X-07, X-10 private, X-12 partial, X-19) |
| BLOCKED | 5 | overlay/ENV rows C1-04a, 05a, 06a, 07a, X-09 |
| COLLECTED_ONLY | 3 | X-18, W-I, W-X (local runs unretained) |
| NOT_RUN | 3 | C1-15a, X-04, X-17 |
| FAIL_RECORDED | 2 | C1-01 (4 declared known-limit failures; controller job FAIL), X-11 (private, inventory-only) |
| UNKNOWN | 2 | X-08 (report-only, no verdict), X-15 (the controller itself: PASS reduced / INCOMPLETE unreduced) |
| NO_TEST | 2 | X-13, X-14 (PLAN) |

Plus 5 rows outside the inventory (MVP-chain NOT_RUN, MVP-applicability NOT_RUN, MVP-d2-route-b COLLECTED_ONLY, MVP-d09 COLLECTED_ONLY, comparison g2-r10 PASS_RECORDED).

### 10.2 The 696 scenarios

| Population | Evidence status | Count |
|---|---|---:|
| 40 Cognous catalog | controller g8 row INCONCLUSIVE (matched cases passed but declared inadequate; not in the brief vocabulary, not PASS) | 27 |
| | NOT_RUN (A01-A06, H01, H02, C05, C15, C19, C20, C21) | 13 |
| | PASS_RECORDED | **0** |
| | coverage-map: NO_TEST (zero mapped tests) | 7 (all within the 13 NOT RUN) |
| 656 Wiki | NOT_APPLICABLE (591) | 591 |
| | in scope: tests collected, cases NOT RUN, local runs unretained (COLLECTED_ONLY) | 61 |
| | in scope: NO_TEST | 4 (TC-D09-004, TC-D13-003, TC-L02-002, TC-L08-033) |
| | in scope: PASS_RECORDED / FAIL_RECORDED | 0 / 0 (5 cases have a locally failing test, unretained) |
| | in scope cases with a named known-limit test (KNOWN_LIMIT_ASSERTED) | 27 distinct cases (4 W-I + 23 W-X) |

The per-scenario table for the 40 is in section 3.


## 11. Other findings that bear on evidence reading

* Reduced-scope PASS: the controller's headline PASS exists "only because 36 mandatory rows were moved out of the claim after the result was seen" (`reports/v1-validation-2026-10-16-a.md`). Full-catalog mandatory share that passed: 39 of 75 (52 percent) at final-linux-1; 40 of 75 pre-reduction mandatory rows PASS at g8.
* The 4 ODES jobs "FAIL" in every recent controller run by declaration (4 declared known-limit failures); the verdict machinery tolerates them (E-1) because every failed case is declared.
* Coverage-map tests (49) are not in the controller's executed set; the controller's scenario evidence (`suites/v1-scenarios`, 1,093 cases) is not what the coverage map points at. The two evidence streams are not joined by any file.
* The inventory twin and md agree with each other (0 diffs over 42 rows) but both are stale against the controller artifacts: states X-03, X-05, X-15, X-16, counts C1-12/C1-14, X-05 known-limit count, B-06, B-08, section 7 ("builder does not exist yet"), section 5 "Current state" bullets.
* `docs/release-gate/pre-registration.md` section 2 (PC-1) still words OCS-3 as a gate ("100% ... in all three categories"); the inventory records amendments 77-79 making W-I/W-X reported and non-gating. Twin has 127 amendments (last 2026-10-21T23:27:08Z); the g8 run used a twin with 125 (last 2026-10-21T22:43:27Z).
* Evidence-quality defects the artifacts themselves disclose: `qualification_worktree_dirty: true` in the F3 merged run summaries; retained g6-r10 reads INCOMPLETE under the hardened controller; first attempt of g2 aborted at the aggregate step and is retained as aborted; the one undeclared skip in qual-tooling.
* `suites/mvp-d2-route-b` `test_REACHABLE_*` pass "when a hole exists" and one test "fails by design"; these must never be counted as protection.

## 12. Limitations

* Only the local snapshots listed in section 0 were read. Single-commit clones: no history, no ancestry, no diff between historical pins and the heads. `bf865632` and all component SHAs from the inventory are unresolvable locally.
* Component repositories other than CP and Runtime (Replay, pack, ODES, exchange, verifier, manifest, attestation, registry, authority, hub, ergonomics, private orchestrator) were not readable. Their counts are the inventory's, the controller's JUnit totals, or unavailable. The private orchestrator rows (C1-13, X-10, X-11) rest on the inventory page alone.
* No `pytest --collect-only` (pytest not installed). My counts are AST-based and are lower bounds where parametrisation is dynamic (listed). I did not execute any test, controller, or network call.
* The NAME-based mapping of Wiki tests to cases assumes the `test_wiki_<layer>_<nnn>` naming convention (all 253 case-bound functions follow it; the other 9 are skeleton tests); it does not verify that a test actually checks the whole case. Each in-scope case's `scope_extent` is `full` for only 7 of 65 and `subset` for 58 (applicability.json), so "has a test" is not "covered".
* JUnit symbol search for the 49 mapped tests matched on bare function name in all JUnit XML of all retained controller runs; compressed job logs (`job.log.gz`) were not searched.
* Run dates for controller runs other than g2/g5/g7/g8 are inferred from run ids and doc entries; `summary.json` carries no timestamps.
* I did not interpret any verdict; "INCONCLUSIVE" is not in the brief's evidence_status vocabulary and is quoted as the controller wrote it. Mapping of inventory states onto the brief vocabulary (e.g. BLOCKED for ENV overlay rows, PASS_RECORDED for inventory-only measurements, UNKNOWN for X-08 and X-15) is my judgement and is explained per row in `F-evidence-suites.json` (`evidence_support`).
* Nothing here supports a claim about customers, healthcare or financial validation; none of those appear in the evidence.
