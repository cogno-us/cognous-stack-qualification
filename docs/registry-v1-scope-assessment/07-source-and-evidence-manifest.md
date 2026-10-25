# 07 Source and evidence manifest

Records exactly what was read, at which revision, how the numbers were produced, what the denominators are, and what could not be done. Non-authorizing. Read-only analysis; no suite or controller was run; no code, test, expectation or workflow was changed.

## 1. Repository pins inspected

| Repository | Revision | Note |
|---|---|---|
| `cogno-us/cognous-stack-qualification` | `998d39c5ba1c9d537be8289f7658f2e9cde6cbba` (main, 2026-10-24, PR #225 merge) | Analysis base; the draft PR branches from it. |
| `cogno-us/cognous-control-plane` | `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` (head; merge 2026-10-23, PR #83 "f3-claim-journal") | Same revision as the R07 closeout `reversibility.py` pin. Shallow clone. |
| `cogno-us/cognous-execution-runtime` | `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f` (head; merge 2026-10-23, PR #144 "f3/approval-revocation-terminal") | **Not** the `ec728da6` read for the R07 analysis. Shallow clone. |
| `cogno-us/cognous-open-control-stack` (hub) | `51c579a3208149922649a31a6eb041106a4121c3` | Contracts and docs only; the MVP tuple pins hub `c897266b`, which was not checked out. |
| `cogno-us/cognous-ocs-registry` (docs) | `783ff59f07d020d06e2ea9a32a257311527d9d82` (main) | R07 analysis (PR #17 merge `e3f5bbc3`), historical recovery (PR #13 merge `e20504df`), `r08-preparation/`, `r10-feasibility/`, plan v1.2. |
| AI Security Wiki | `1a0c72de4752a1c6932172e5e7dbf14f755799c8` | Commit recorded by `applicability.json`; page text read from the copy under `scenarios/ai-security-wiki/pages/`. |
| Engineering Constitution | `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` | Not read for this assessment; no claim about formal adoption is made. |

**Not available / not read:** Exchange, Replay bundle, Evidence Pack, ODES, Verifier, BitRep, Index (`cognous-evidence-registry`) and Action Manifest sources (relocated test copies under `suites/<repo>/` were read by name and docstring only); the `COG-REG-SHARED-ADD-01` addendum text (no durable source or verified digest exists in the repositories; D10); the registry S04/S05 implementation code (S05 claims rest on the R07/R08 documents). Rows that depend on these are marked UNVERIFIED or REASONED INFERENCE.

## 2. Historical test pins versus current heads

Historical evidence does not speak for the current heads. Both clones are single-commit shallow, so whether any pin is an ancestor of the head, or what changed, **cannot be shown** (UNVERIFIED).

| Component | Freeze manifest 2026-10-16 | r10 (inventory counts) | r13 (newest controller run g8, 2026-10-21) | MVP tuple (proposed, 2026-10-24, "PROVISIONAL, UNQUALIFIED") | Read for this assessment |
|---|---|---|---|---|---|
| Control Plane | a34c3dc2 | 2bac7875 | 0a41faa9 | **7a4bcd40** | **7a4bcd40** |
| Runtime | e20f92e1 | 6b16962d | ec728da6 | **c5e97e87** | **c5e97e87** |
| Replay | 79ba16d4 | 6a6a4774 | 028f63d1 | 40012b8c | not cloned |
| Evidence Pack | 893aca8d | fd030615 | a3ebbb90 | 7b9511f2 | not cloned |
| ODES | eb83220c | 2893d935 | e86a25a1 | 1a5e1d30 | not cloned |
| Exchange | 8be6c6b8 | fdc2a410 | 7f7569b0 | excluded (route C) | not cloned |
| Action Manifest | 2c36bcd0 | ff549082 | fa170815 | fa170815 | not cloned |
| Hub | 8517818f | 8517818f | 8517818f | c897266b | 51c579a3 |

Source: `suites/_pins.py` resolution of `process/v1-validation/v1-2026-10-16-a/freeze-manifest.json` and `refreeze-log.json` (61 entries applied, 0 errors, re-run by Lane F), `process/security-runtime-f5b-20261016-r{1,2,10,13}.json`, `process/mvp-chain/tuple-pin.proposed.json` (Lane F, full table in [appendix F](appendix/lane-F-evidence-audit-notes.md) section 5).

What each artifact speaks for: the inventory page's counts and "PASS" states speak for **r10**; controller runs g2 to g8 speak for **r10 to r13**; refreeze entries RF-1 to RF-44 marked "qualified" predate the controller's verdict-machinery hardening (the known-limits page says no run at the hardened controller has qualified any pin); the only plan aimed at the current heads is the MVP acceptance candidate, for which "no dispatched run exists yet". Approval-revocation terminality (NC1-04) **failed at the pre-F3 Runtime `ec728da6`**; its outcome at `c5e97e87` is unrun.

## 3. Denominators

| Quantity | Value | Basis |
|---|---|---|
| Canonical scenarios | **696** = 40 Cognous catalog + 656 AI Security Wiki | `scenarios/catalog.json` (40), `ai-security-wiki/applicability.json` (656); the 696 appears in the root README and `suites/README.md` (not in `scenarios/README.md`) |
| Wiki classification | 20 APPLICABLE, 45 PARTLY_COVERED, 591 NOT_APPLICABLE (in scope 65: W-I 17, W-X 48) | `applicability.json`, decided from declared scope before results (basis text) |
| Wiki-derived tests | 290 items = 262 test functions + 28 from parametrization (AST count; pytest not installed); 253 functions map to case ids, 9 skeleton tests carry no case id | Lanes A and F; 25 of the 290 come from 5 dynamically parametrised functions, so counts are lower bounds in places |
| In-scope Wiki cases with a wiki-derived test | 61 of 65; none for TC-D09-004, TC-D13-003, TC-L02-002, TC-L08-033 | Lane A mapping; the inventory prose (39 of 65; none of 20 APPLICABLE) is stale against its own table |
| Coverage-map entries | 40 mappings; 57 test entries pointing at 49 distinct tests (8 shared by two scenarios); statuses 32 PARTIAL, 6 UNIMPLEMENTED, 2 DEFERRED; **7 scenarios with zero tests** (A01, H02, C05, C15, C19, C20, C21) | `coverage-map.json`; every mapping says "Static source association; proposed coverage, not accepted execution" |
| Controller scenario rows (catalog, newest run g8-r10) | **0 PASS, 27 INCONCLUSIVE, 13 NOT RUN** | `results/v1-validation/v1-2026-10-16-a/g8-r10-39690459403/requirements-matrix.md`; D01, D03, D04 are INCONCLUSIVE on named matched-refund assertions |
| Controller selected verdict | PASS over 39 rows after the D15 scope reduction (36 rows moved out after results were seen); unreduced mandatory INCOMPLETE (40 PASS, 30 INCONCLUSIVE, 5 NOT RUN of 75) | `summary.md` (Lane F) |
| Wiki cases with a recorded run | **0 of 656** (all NOT RUN); wiki-derived tests are not collected by the controller; a local run at r13 recorded 285 pass / 5 fail (4 of the 5 not tied to cases) | `docs/test-inventory.md`, `docs/v1-known-limits.md:248` |
| Suite-local claims (supplement) | 162 (Lane B 53, Lane C 109) | Grouped claims, not test functions and not scenarios; excluded from the 696 |
| Inventory suite rows | 42 (+5 rows the inventory omits: MVP chain, MVP applicability, MVP D09, MVP D2 route B, g2-r10 comparison) | Lane F |
| Known-limit tests | 75 enumerated in the inventory, 71 after withdrawals (matches the controller declared set); Runtime head has 11 further `*_known_limit` tests in neither | Lane F |

Duplicate accounting rules applied: scenarios are counted by distinct ID; a test mapped to several scenarios is listed per scenario but never increases a scenario count; parametrised tests are one function; suite-local claims are never added to the 696.

## 4. Evidence status

Crosswalk `evidence_status` over the 696 rows:

{{T_EVID}}

`NO_TEST` is dominated by the 591 NOT_APPLICABLE Wiki cases (no test by construction). `PASS_RECORDED` means **named executed cases passed** in a recorded run at a historical pin, never whole-scenario acceptance. `KNOWN_LIMIT_ASSERTED` rows pass by asserting a limit and are evidence of a KNOWN_GAP.

Per-suite evidence (Lane F, 47 rows; the evidence status vocabulary is Lane F's mapping of the inventory state and retained artifacts, a judgement call for overlay rows):

{{T_SUITES}}

Claims about who ran what: every recorded result is **developer-run, synthetic, Cognous-configured**; the "independent scans/reviews" cited in the refreeze log and known-limits page are not identified, so independence cannot be established; no independent Tier 1 qualification owner is designated (D13). The 25/25 actual-agent pilot is described in the dashboard but its raw artifact is not in the checkout. The comparator applications (OPA; LangGraph plus OPA) are configured by Cognous.

## 5. Methodology

Six lanes with disjoint file ownership ran in parallel; one integration lead joined their outputs with a stdlib-only script ([method/](method/)). Lanes A (Wiki inventory), B (V1 and security-runtime batteries), C (cross-component and MVP), D (rule-family source analysis), E (customer-outcome classification, independent of all other lanes) and F (evidence and coverage audit, independent). Lane notes are in [appendix/](appendix/). No lane resolved an R07 decision, and no classification was decided by agreement between lanes.

| Step | Output |
|---|---|
| Join A, B, C, E into 21-column rows | [data/canonical-scenario-crosswalk.csv](data/canonical-scenario-crosswalk.csv) and `.json` (696) |
| Suite-local claims | [data/suite-local-claims-supplement.csv](data/suite-local-claims-supplement.csv) and `.json` (162) |
| Family metrics, scores, weighted composites, profile comparison | `data/family-metrics-and-scores.json`, `data/profile-comparison.json` |
| Perturbation check (5,000 draws, seed 7) | `data/robustness.json` |
| Gap register, acceptance matrix | `data/gap-register.*`, `data/v1-acceptance-matrix.*` |
| Validation against repository IDs, test markers, coverage map | `data/validation-report.json` |

`priority`, `registry_dependency`, `existing_protection`, severity and all scores are REASONED INFERENCE (rules stated in [04](04-prioritization-analysis.md)). The crosswalk's `component_route` comes from Lane C for the 40 catalog scenarios (driver docstrings, not executed drivers) and from Lane A for Wiki rows.

### Validation (method/validate_crosswalk.py; 26 checks, all pass at the time of writing)

- 696 rows, 696 distinct IDs; catalog IDs and order equal `scenarios/catalog.json`; Wiki IDs equal `applicability.json` and `ai-security-wiki/catalog.json`; Wiki classification counts and each per-ID classification preserved (20/45/591).
- Controlled vocabularies hold for dependency, protection, evidence status and family; no row assigns F8 as a candidate; no canonical row is `ENFORCED_AND_EVIDENCED`; known-limit rows never count as protection; all 656 Wiki rows are NOT RUN; 21 columns per row.
- 276 catalog test IDs resolve to a file and a function or data marker in the repository; 253 distinct Wiki-derived test functions resolve in `suites/wiki-derived`; all 57 coverage-map test entries are preserved in the matching scenario row; the 4 in-scope Wiki cases without a test equal the inventory's list; the 7 zero-test catalog scenarios equal the coverage map.
- Suite-local IDs are unique, prefixed `SL:`, and disjoint from the 696.

## 6. Source-access limitations and other limitations

- Shallow clones: no diff against historical pins; Runtime moved from `ec728da6` to `c5e97e87` after the last controller run.
- Repositories not cloned (section 1): rows for Exchange, Replay, Pack, ODES, Verifier, BitRep, Index, Action Manifest enforcement are UNVERIFIED.
- Lane D validated 285 citations for file existence and line range at the pinned heads and spot-read about 30; mismatches with R07 text: the `effective_max_effects` coordinate in `local_authority_effect.py` is 449 where R07 says 443; F9 has six length-128 copies where R07 cites two; an empty allow-set is accepted by the constructor where the R10 feasibility document implies refusal (only `allowed_target_prefixes` must be non-empty).
- Lane E cross-check (40 Wiki cases, same reviewer) agreed 28/40; all 12 disagreements were NOT_APPLICABLE rows where a mechanical title rule misfired; secondary outcomes and severities on NOT_APPLICABLE rows are not for scoping. PARTLY_COVERED severity reflects the whole Wiki subject.
- The lead re-ran or re-read: the `apply_registry_overlay` caller grep (none in Control Plane `src/` or Runtime `engine/`), the D01/D03/D04 controller rows, and the `TC-L05-013` test lines 750-755 against `runtime_authority.py:88`. Everything else attributed to a lane was accepted as reported and labelled accordingly.
- Test counts are by static reading; the controller and test suites were not run. Two cited statuses conflict across sources and both are recorded: `security-runtime` is NOT_RUN_HERE in the inventory (X-03) while the controller shows native-f5b 36/0/0/0.
- Stale statements found in the repository and **not** edited: inventory prose ("No gate has been run"; B-06; 39 of 65; X-05 known-limit count of 4 withdrawn); `suites/README.md` on `mvp-d2-route-b` (retired at Runtime `c5e97e87`).
- No paid provider call, credentialed or production execution occurred. No Copilot review was requested.

## 7. Confirmation of scope

This pull request adds files only under `docs/registry-v1-scope-assessment/`. No code, test, suite, expectation file, workflow, schema, scenario catalog, coverage map, results, process or pin file was modified; no existing document was edited; the adopted registry plan was not modified. The scripts in `method/` are analysis aids, are not wired to any workflow, and are not repository tooling.
