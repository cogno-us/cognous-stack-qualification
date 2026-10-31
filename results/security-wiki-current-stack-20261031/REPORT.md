# Security Wiki battery against the CURRENT integrated OCS (incl. migrated Registry) - consolidated report

Date 2026-10-31. Owner of tests/evidence: cogno-us/cognous-stack-qualification. Tracker: cogno-us/cognous-open-control-stack #215.
Governance: Engineering Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`; static plan in the hub. Non-authorizing. No organizational-independence claim (fresh-context AI reviewers only).
Standing limits unchanged: the bounded MVP result is not revoked; F3 engineering closed; formal independence, Tier 1, publication, release and production holds unchanged. Nothing here repaired, reclassified or excluded.

## Verdict (read first)
The current stack **cannot yet be fully qualified by the Wiki battery**. Of 290 executed tests: **244 PASS, 5 FAIL, 41 BLOCKED, 0 skipped**. The 41 BLOCKED are an INTEGRATION blocker: the Governed Exchange (7f7569b0) hard-pins the *historical* Control Plane/Runtime/Replay/ODES/Pack revisions per compatibility profile and has no profile for the current tuple, so every Exchange-route test refuses with `candidate source identity mismatch`. Clearing it needs an Exchange-owned (production) change; a Qualification-side bypass would weaken the check and was not made. **No Wiki test exercises the migrated Registry**; it is in the target tuple but is untested by this battery. No confirmed exploitable defect came out of an executed test; two Runtime behaviours (below) need owner triage. A green count here is NOT complete Wiki qualification.

## 1. Exact current tuple (option B; full SHAs; `process/v1-validation/current-stack-20261031/tuple.json`)
Option A (authoritative integration manifest) is NOT AVAILABLE: hub `component-lock.json` is stale (pins pre-MVP Control Plane `0a41faa9`, no ocs-registry entry). The tuple is an assembled option-B tuple of current default-branch heads, not an authoritative manifest.
| Component | Repo | Commit |
|---|---|---|
| Control Plane | cognous-control-plane | b19c47ddd020409d24e52e70b11359c46265edbb |
| Runtime | cognous-execution-runtime | f7a55e2a8494801e49193f9f46935f0a971c248d |
| Replay | cognous-replay-bundle | 40012b8c174c6f25685bd5d9bc93ff46cc9a5842 |
| Evidence Pack | cognous-governance-evidence-pack | 7b9511f2c6d56d424f17b078826594abd29f6c96 |
| ODES | open-decision-evidence-standard | 1a5e1d300250d832e611633f0bf8f762e398c0ec |
| Exchange | cognous-governed-exchange | 7f7569b02666b99669a9fca61117ca1f4bce5f0d |
| Action Manifest | cognous-action-manifest | fa170815ef96a54c233d0dd9da821b60debabf8b |
| **Migrated Registry** | cognous-ocs-registry | 6b96a9a658923954433dc1a4c13626fa5145b9c7 |
| Index | cognous-evidence-registry | b2485998b88256c2b322493800d1fba076814cbd |
| Attestation | cognous-evidence-attestation | 981036c315856c71207984797b0c4e48d3b3921d |
| Governance | cognous-institutional-governance | 03a90c14c4a178997df2b6e527f67452b9c6bb7a |
| Verifier / Ergonomics / Orchestrator (recorded, not in this battery) | | 39d46b494558e271439966bec98b26dc4d040cc4 / bea582b378af1b0d6854ffe3a1de40df5ad7a0ab / 721f4406701d24171b72025a5b8a06687594928b |
| Hub / Qualification base | | dd522c504d0cd2bdf463b791a729fe9029cca224 / 86f78ea3d1bd9cf230813fa0941621e38e7605e4 |

Consistency findings (OBSERVED unless stated): Registry main = r08-v8 code (`a40fe755`; only README differs after it); every Control Plane CI Registry pin v6/v7/v8 is an ancestor of Registry main; Control Plane head contains `739efe7d`. **Inconsistencies:** (i) Exchange 7f7569b0 is not re-tied to the current heads; (ii) Replay/Pack/ODES were re-tied to Runtime `c5e97e87`/Control Plane `7a4bcd40` (MVP) while the tested Runtime/CP are f7a55e2a/b19c47dd - the bundle chain is NOT shown consistent and its provenance is label-stamped (reviewer E-02); (iii) Runtime tests assert older Registry pins; (iv) hub lock and ergonomics `requirements/stack.txt` still pin pre-MVP Control Plane. The Registry is recorded in the config and checked out pristine at 6b96a9a6 out-of-band, but it is **not** among the harness component names: the harness neither verifies nor imports it.

## 2. Migrated Registry commit
`6b96a9a658923954433dc1a4c13626fa5145b9c7` (code identical to r08-v8 `a40fe755e2384a99c37016fa9ad59396f1835900`).

## 3. Historical vs current configuration
Historical (unchanged, HISTORICAL REFERENCE ONLY): `process/v1-validation/v1-2026-10-16-a/`, `process/security-runtime-f5b-20261016-r13.json` (hub 8517818f, CP 0a41faa9, Runtime ec728da6, Replay 028f63d1, Pack a3ebbb90, ODES e86a25a1). Current: `process/v1-validation/current-stack-20261031/{freeze-manifest,tuple}.json` + `process/security-runtime-current-stack-20261031.json`, selected by the existing `V1_VALIDATION_ID`/`V1_PROFILE` mechanism. `git diff 86f78ea3..HEAD` over `suites/ tools/ scenarios/` and the historical config is empty (recorded in `run.json`): **no assertion, expected outcome or test was changed**; no adapter was added. The historical-pin run started earlier was stopped with no results; the only historical-pin execution is a 15-test diagnostic (`hist-diag/`, section 12).

## 4-8. Denominators and results
| | Count |
|---|---|
| Imported Wiki cases (catalog = applicability; source 1a0c72de; lock/page hashes verified) | **656** |
| In scope (20 APPLICABLE + 45 PARTLY_COVERED) - confirms the 65 | **65** |
| Out of scope (NOT_APPLICABLE, stored reasons) | 591 |
| In-scope cases with a harness test (executable) | 61 |
| In-scope cases with no test (NOT TESTED, MISSING COVERAGE): TC-D09-004, TC-D13-003, TC-L02-002, TC-L08-033 | 4 |
| Collected / executed tests (13 modules, 1 process each) | 290 / 290 (0 skipped, 0 xfail) |
| Tests PASS / FAIL / BLOCKED | **244 / 5 / 41** |
| In-scope case verdicts (all tests of a case must pass for PASS) | **PASS 46, FAIL 5, BLOCKED 10, NOT TESTED 4** |

BLOCKED = 39 Exchange identity refusals + 2 tests (TC-L06-039 `[plain]`, `[urgent_administrator]`) that passed only because they accept *any* exception while the refused check fired (observer evidence, `raw/*.obs.json`); they are reclassified from PASS and not counted as passes. One BLOCKED test is the skeleton's Route C smoke test, which carries no case id. The run was repeated (run1 without, run2 with the observer-only plugin): statuses identical for all 290.
FAIL cases: TC-L06-018, TC-L06-022, TC-L06-040, TC-L09-004, TC-L15-019. BLOCKED cases: TC-L06-003, L06-020, L06-038, L06-039, L06-041, L06-045, L07-008, L07-009, L07-012, L07-013 (L06-020/038/039/041/045/L07-012 have no passing test at all).

## 9. Registry-specific results (`registry-coverage-map.md`)
**No executed result for the migrated Registry.** grep of `GovernedPolicyWorkflow`, `registry_governed`, `registry_selection_authority`, `effective_configuration`, `authorization_pin` over wiki-derived, v1-scenarios and v1-probes returns 0 matches; all "rule/policy" Wiki tests run the pre-MVP `rule_revision/0.1` + `bounded` path. In the 12 requested properties (authority, identity/version binding, resolution, governance enforcement, propagation, scope, integrity, provenance, fail-closed, stale/unauthorized rejection, migration compatibility, missing/conflicting rules) mapped Wiki cases exist, but each exercises the reference path, not the Registry. Where the Wiki says "registry" it usually means the Exchange `LocalRegistry` or a model/agent registry. Candidate newly-applicable cases (flagged, NOT reclassified): strongest TC-L08-039; weaker TC-D09-007, L14-005, L14-013, L08-003 (+15 name-collision candidates in the CSV). Registry's own test suites are outside this battery and not claimed.

## 10. Cross-component results
Routes A (effective-grant SQLite behind the CP executor) and B (atomic claim) run on the current CP/Runtime heads: 244 passes, including grant lifecycle, identity/scope, budget/stop, manifest change control, records/replay/policy, integrity/export, pack/decision state, traces, tool-call/approval. Route C (Exchange <-> CP/Runtime/Replay/Pack/ODES) is BLOCKED (INTEGRATION). Cross-component *rule propagation* from the Registry to Runtime/Replay/Evidence is not tested.

## 11. Genuine engineering defects
None confirmed by an executed Wiki test as a vulnerability. Needing Runtime-owner triage (reviewer: may be real, not stale):
- TC-L15-019 route B: after the authority tables are restored to an older state, the retry returns status `unknown` where the test expects `denied` (the test stops at that assertion, so it did not itself check for a second effect; owner to confirm no double effect and that `unknown` is the intended hold).
- TC-L09-004: after the destination credential loses scope, commit is refused (`failed/effective_grant_changed_at_commit`) but `observed_state` is `unknown`, expected `absent`.
Static-only (NOT executed, source inspection by workers A-D, `static-inputs/`): Exchange default profile `persistence-v1` runs with no source verification (HIGH, A-01); unauthenticated sender identity (A-02); `ODES_ALLOW_UNVERIFIED_REPLAY` bypass not recorded (B-05); Replay's typed-refusal importer accepts a fixed `runtime_authority` member set while the Registry-governed Control Plane adds `effective_configuration` - **possible Registry->Replay incompatibility, UNCONFIRMED** (needs one executed import); the Runtime durable selection authority supports only r08-v2..v4 while v5..v8 are enforced only inside the Control Plane workflow (no durable store/rollback protection).

## 12. Harness and environment defects
- 39+2 BLOCKED: Exchange source-identity pins (INTEGRATION, production-owned).
- TC-L06-022 (stop journal now raises `ValueError` before `sqlite3.IntegrityError`; stricter, stale expectation), TC-L06-018 (expiry error code `GAX-FRESHNESS-CREATED-AFTER-EXPIRY` vs `GAX-FRESHNESS-EXPIRED`), TC-L06-040 known-limit variant (created_at is now type-checked: an improvement, expectation stale): HARNESS FAILURE, pre-existing. Diagnostic at the historical pins (15 tests, `hist-diag/junit-historical-pins-DIAGNOSTIC.xml`, HISTORICAL REFERENCE ONLY, checkouts `/home/claude/scn-components`) gave the *same 5 failures* with the same messages, so none is a migration regression. Their expectations were NOT changed.
- Run evidence directory was empty (the suite writes no per-test JSON); identity is evidenced by `run.json` gates recomputed with the real `require_pristine` after the run.
- Control Plane/Runtime/Replay admitted by contract-matrix "conforms" (tested revision = HEAD, match true), others by sha-pin. Executed in an isolated Linux sandbox, not a GitHub-hosted workflow; 2 CPUs, so 2-way parallel only.

## 13. Security coverage gaps
4 in-scope cases untested; Registry not exercised (G1-G14 in `registry-coverage-map.md`: no test for F-A1 authorization pin, cross-version signing domains, legacy cutoff, narrow-only composition, key admission, rollback/high-water; Replay/Pack/ODES carry no Registry identity); no Wiki case covers SIGKILL/IPC/peer-credentials/uid separation or power-loss; Replay/Pack/ODES provenance is label-stamped, not measured; dependency-vulnerability scan and repository settings UNAVAILABLE; orchestrator and Verifier untested by this battery. Possible further vacuous passes: other `except Exception`-tolerant tests in wp_a..g4 not yet audited (observer found only the two above in executed runs).

## 14. Raw evidence and commit references
Qualification branch `security-wiki/current-stack-20261031` (config commit chain from base 86f78ea3). In this directory: `raw/` (13 junit + logs + observer JSON, official run2), `raw-first-run/`, `hist-diag/`, `per-test.csv` (290), `per-case.csv` (656), `counts.json`, `run.json`, `runner-run_mod2.sh`, `obs_plugin.py`, `registry-coverage-map.md`, `inventory-and-denominators.md`, `static-inputs/` (STATIC-SOURCE, not executed), `reviewer-E-CS.md`, `SHA256SUMS`. Component checkouts were pristine at the tuple SHAs before and after the run.

## 15. Minimal recommended remediation set (not started)
1. Exchange owner: add a compatibility profile (or equivalent re-tie) for the current CP/Runtime/Replay/ODES/Pack heads, then re-run the 41 BLOCKED tests unchanged. Highest value.
2. Add the migrated Registry to the harness component set (verified pristine) and add Wiki-mapped tests for the Registry properties and TC-L08-039/TC-L02-002; one executed Registry-governed decision -> Replay import to settle the possible `effective_configuration` incompatibility.
3. Runtime owner: triage TC-L15-019 (`unknown` vs `denied`) and TC-L09-004 (`unknown` vs `absent`).
4. Qualification owner (separate, explicit decision): refresh the stale expectations of TC-L06-018/022/040 via the existing amendment mechanism; do not edit silently.
5. Re-tie Replay/Pack/ODES to the current Runtime/CP or record the chain as unverified; refresh the hub component-lock to produce an authoritative manifest.
6. Tests for the 4 untested in-scope cases.
