# S4-CLOSEOUT: Security Wiki S3 closeout (Issue #254)

Governing: Engineering Constitution cogno-us/cognous-engineering-constitution@1c2e920f4e58e07a52e8e2408a506cf7dbc1292b (CA06 preserve original evidence, CA16 no silent claim promotion); Issue cogno-us/cognous-open-control-stack#254; plan OCS-INTEGRATION-COMPAT-20261031/1.0. Author: Worker D, from Worker A (read-only verification of head 2978679f) and Worker C (residual register). Non-authorizing; `claims_made = []`.
Scope: developer / local-offline and GitHub-hosted developer evidence by AI workers. NOT independent qualification (Q7 NOT ESTABLISHED), NOT adoption, NOT a release or certification claim. This is the one S4 report; CROSSWALK-S4.md section 14, REPORT.md, README-S3-run.md and REVIEW-CORRECTIONS.md point here. Raw evidence, per-test-41.csv, junit, logs, observer files, run.json, registry-probe/ and all earlier SHA256SUMS* files are unchanged.
Evidence head chain: run 41 executed on b48675b7 (C1); reviewed implementation head 99fd257e; verified head 2978679f; the final head is the commit after this one (see PR #260).

## 1. Three layers, never one battery
| Layer | Result | PASS | FAIL | BLOCKED | Where |
|---|---|---|---|---|---|
| A | Original current-stack assessment (290 tests) | 244 | 5 | 41 | `results/security-wiki-current-stack-20261031/` |
| B | Exchange-only diagnostic on the 41 (unmerged Exchange 05ba99ba; mixed Replay/ODES/Pack) | 0 valid | 0 valid | 41 | `results/security-wiki-exchange-compat-20261031/` |
| C1 | Merged tuple, single strict execution of the 41 (PRIMARY) | 38 | 0 | 3 | `run-41-merged-tuple/` |
| C2 | Supplementary single re-execution of the 3 blocked ids | 3 of 3 PASS (41/0/0 if combined) | 0 | 0 | `run-41-merged-tuple-supplementary-enospc3/` |
| C3 | GitHub-hosted observation of the same 41 | 41 (runs 2-6) | 0 | 0 | `c3-hosted-run/` |

* **C1 is the primary figure: 38 PASS / 0 FAIL / 3 BLOCKED.** The 3 BLOCKED are TC-L06-020 x3 with `OSError: [Errno 28] No space left on device` (host disk full): infrastructure, not a component refusal.
* **C2 provenance limits:** chosen after seeing C1; there is no run.json, command record, tuple record, pristine-after record or disk reading. "Same tuple and environment" is asserted, not evidenced. It does not replace C1 unless the Architect accepts it.
* **C3 is a separate hosted observation**, python 3.13.17, pytest 8.3.5, jsonschema 4.26.0 versus C1 python 3.13.18, pytest 9.1.1. It does not alter C1 or C2.

### C3 runs (Worker A verified via REST: event pull_request, workflow "Security Wiki S3 current tuple (C3 hosted observation)" `.github/workflows/security-wiki-s3-current-tuple.yml`, attempt 1, run and job conclusion success for all six)
| Run id | Head | Created (UTC) | Annotation | Ids visible | GitHub artifact (id, size, zip sha256) |
|---|---|---|---|---|---|
| 41229883384 (SUPERSEDED) | 93d5807e | 18:32:06 | "39 FAIL, 0 BLOCKED", job not failed: harness defect (missing `jsonschema`; none reached a security assertion) | n/a | 13053526017, 4321562 B, e9f0e0ab482a22c340c6cc33a96fc789a558da6296b0f10e4add8b26be551a26 |
| 41231370965 | ca541b9e | 18:50:45 | 41/0/0 | 29 of 41 (4096-char truncation) | 13053927620, 19812425 B, 1120704d49add54ccb3cddaec5b0568808d063d6a7bde1f2254e31e95a568e70 |
| 41231979036 | 60cdb929 | 18:58:42 | 41/0/0 | 29 of 41 | 13053834164, 19811720 B, 4c0bb74d9b9cea9020f8afa941a1e2cd2b63d7c88194b6daba68c99df45db52e |
| 41232844591 | 6c5d89a4 | 19:09:11 | 41/0/0, chunks 1/2 and 2/2 | 41 of 41, all PASS | 13054876090, 19811273 B, bde19ecb1e7db0e8533eb3a4a479f6d5cfc351a2362623415ba63d95a7716b1f |
| 41233326892 | 99fd257e | 19:15:12 | 41/0/0 | 41 of 41, all PASS (live check; not committed) | 13055180510, 19812067 B, 293d26bfbc4c90421a252b9c3281e3b135078a1f4f22638813f619fad6b71991 |
| 41234082886 | 2978679f | 19:24:37 | 41/0/0 | 41 of 41, all PASS (live check; not committed) | 13054478118, 19811782 B, 669977f4ba5f58b9d6c448a6d68295aa2a1c63cf2077e4203d95168f5a1fd8ca |
All six artifacts were not expired at verification. The digests are GitHub-provided zip digests and appear nowhere else in the repo evidence. **Raw hosted per-case evidence (junit, per-test CSV, SHA256SUMS-all) was NOT downloaded or independently reconstructed**; C3 verdicts rest on header counts and per-test annotations, which are not raw verification. Annotations for runs 2-4 are byte-equal to the committed `run{2,3,4}-annotations.json`. Classifier caveat: the helper substring-matches block markers, so an assertion FAIL containing e.g. "No module named" could show as BLOCKED (the job still fails on dependency strings). A trailing hosted run will follow the commit that adds this file; it is reported in the PR and is not captured.

## 2. Distinction matrix (what each kind of result does and does not mean)
| Category | Status in this evidence |
|---|---|
| Compatibility acceptance (components load and the Exchange r2 identity gate accepts the tuple) | Developer observation: Exchange identity check evidenced in 39 of 41 C1 rows (2 setup-error rows carry stale counters), accepted, raised 0; all 41 C3 ids PASS |
| Security-control effectiveness | Only the 17 negative-path PASS rows can evidence a refusal, relative to the frozen assertions and synthetic data; 2 of those are PARTIAL and 1 exception-based |
| Documented-limit tests | 9 rows: PASS means the limitation was asserted to exist; NOT control-proven |
| Partial coverage | TC-L06-039 plain / urgent_administrator (sub-case exception-only); TC-L06-003 exception-based; TC-L06-040 twelve-invalid PASS-as-written (5 of 12 rejected) |
| Source-authentic evidence | NOT established: no source authenticity, signature or trust (Registry probe non-claims) |
| Caller-asserted metadata | `cur` generation labels (patch ea8bddcd, PROVISIONAL DEVELOPMENT PIN), `source_asserted_not_independently_verified` |
| Developer observations | C1, C2, C3, the Registry probe, Worker A/C/E AI inspections |
| Independent qualification | NONE; Q7 NOT ESTABLISHED (AI-only reviewers give no organisational independence) |
| Canonical adoption | NOT ADOPTED; the canonical component lock is unchanged by this evidence (candidate manifest is draft PR #255, see PR #255 for its current head) |
| Release readiness | HOLD; no release, production, certification or hold removal is claimed |

## 3. Residual security register (Worker C; nothing here is remediated in S4; no issues were created)
Tracker discovery caveat: `gh api` returned 403 for control-plane, execution-runtime and ocs-registry, so "NONE FOUND" for those repos means none found by org search or direct fetch, not an exhaustive listing.
| ID | Residual | Owner | Next action (NOT implemented) | Tracker |
|---|---|---|---|---|
| F1 | **Replay accepts a substituted effective configuration when the digest is recomputed consistently. Digest consistency is not source authorization.** Probe verdict NON_DETECTION_RECORDED; CP-side `authorization_binding_changed` refusal works, Replay only retains the refusal record. The probe's "overall PASS" must not be cited as Replay or Registry control PASS. **Not remediated in S4.** | Replay (`effective_configuration.py` importer, importers.py); Registry/CP for the digest and selection contract | One Replay tracker: decide whether import must verify against an authorization source (Registry revision, selection, signature) or the profile is documented internal-consistency-only; add the negative resealed-substitution test only after that decision | NONE FOUND (related only: Exchange #30 closed, Replay #81 closed, #254 open) |
| F2 | Caller-asserted provenance labels; Replay revision gates compare caller-supplied strings and cannot detect a relabelled historical record | Replay, ODES, Evidence Pack, qualification repo | One cross-component tracker: who may assert generation labels, plus a verifier or explicit non-claim | NONE FOUND |
| F3 | Registry probe does not establish source revision, signature or trust; bytes exercised a40fe755 (code-equal outside docs/ and README.md, 62 doc paths differ) not tuple 6b96a9a6; Pack/ODES NOT_RUN; revoked/withdrawn/expired and forged signature refused CP-side only | ocs-registry with Replay; qualification repo | Record as unsupported scope; later probe on exact 6b96a9a6 plus a source-lineage decision | Partial only (Registry #58/#59 holds, #52); no tracker for "Replay carries no Registry lineage" |
| F4 | Runtime governed export BLOCKED: `PinnedControlPlaneExecutor.execute` rebuilds the workflow via `workflow.__class__(...)` and cannot construct `GovernedPolicyWorkflow`; no production interface; not repaired, not fabricated | execution-runtime; control-plane | Runtime owner scopes an export interface, or Architect records permanent unsupported scope | NONE FOUND (closest closed Runtime #95/#100, CP #91/#96) |
| F5 | Exchange `refs/replace` unhardened: the source-identity check does not neutralise git replace refs; the S3 guard origin check is HEAD/tree only; the Exchange check does not cover the Action Manifest | governed-exchange (`gax_ref_runtime.py`); qualification s3 guard | Harden against replace refs with a negative test; same in the guard | NONE FOUND (#254 S0: separate hardening item) |
| F6 | Nine documented-limit rows inside every PASS tally (C1, C2, C3): see section 4 | Exchange / Control Plane behaviours; Wiki expectations in the qualification repo | Architect decision per row: permanent documented limit or remediation item; list the nine ids in any PASS summary | NONE FOUND |
| F7 | Partial / exception-based coverage: TC-L06-039 plain and urgent_administrator (rows 31, 32), TC-L06-003 (row 41), TC-L06-040 twelve-invalid (row 28, PASS-as-written, 5 of 12 rejected, criterion >=11 unmet) | qualification repo wiki-derived suites; Exchange/Manifest | Architect decision on expectation amendments (separate scope); correct figures by addendum, not silent relabel | NONE FOUND |
| F8 | Five historical FAILs, untouched and not rerun: TC-L06-018, TC-L06-022, TC-L06-040 (schema check does not reject extra members/content types/size), TC-L09-004, TC-L15-019 | Exchange/CP (L06), Runtime triage (L09-004, L15-019) | Own scope per owner; not rolled into #254 | NONE FOUND |
| F9 | Four unimplemented Wiki cases (NOT TESTED): TC-D09-004, TC-D13-003, TC-L02-002, TC-L08-033 | qualification repo with control owners | Architect: implement, defer or mark out of scope | NONE FOUND |
Additional: G1 Exchange identity check evidenced in 39 of 41 C1 rows (setup-error rows 3 and 4: TC-L06-020 `each_hop_is_assessed_...` and `forwarded_message_with_a_changed_requested_action_...`; the observer resets counters only in the call phase; CSV columns and REPORT.md still show 2/0, governed by REVIEW-CORRECTIONS M1). G2 C2 provenance limits and unverifiable pre-run real-config guard (M4). G3 C3 raw evidence not reconstructed. G4 tenant substitution not exercised; the probe ran concurrently on the same disk; the six LOW inspection items; Pack/ODES e2e tests skip in CI without their Replay source. G5 related open trackers: ODES #131 and #140 (open), #254, #255 (draft), #260, qualification #240 and #235.
Standing holds (status as Worker C found them, unchanged): Registry #58 open, unmerged, held; Registry #59 open, unmerged; Control Plane #87 open, unmerged (work re-implemented in merged #88); **Ed25519 #26 and #34 are MERGED Registry PRs whose security-review status is BLOCKED (no independent crypto reviewer): the hold is a review status, not an open PR**; V09, DEF-OBS-TOL-OVERFLOW-1, R1 and constructor tolerance are carried in #254/#240 text without dedicated open trackers; Q7 NOT ESTABLISHED; Final Tier 1 DEFERRED (qualification #235 open); publication, release and production HOLD.

## 4. The nine documented-limit rows (C1 rows 6, 10, 25, 26, 29, 34, 35, 37, 38)
TC-L06-020 `known_limit_the_hop_where_content_was_stopped_is_not_recorded`; TC-L06-038 `known_limit_a_registry_holds_one_recipient_and_refusals_are_not_stored`; TC-L06-018 `a_forged_message_claiming_a_registered_agent_is_accepted_when_consistent_known_limit`; TC-L06-018 `refusals_before_acceptance_are_returned_and_not_stored_known_limit`; TC-L06-040 `extra_members_content_types_and_size_are_accepted_as_data_while_mistyped_members_are_refused_known_limit`; TC-L06-039 `the_sender_label_is_not_bound_to_the_actor_...`; TC-L06-039 `a_held_request_is_retained_with_the_proposal_of_the_actor_and_the_user_...`; TC-L06-045 `the_hop_names_the_actor_the_user_the_payload_commitment_and_the_decision_but_not_the_caller_...`; TC-L06-045 `the_correlation_identifier_is_not_a_member_of_the_message_known_limit`.
Composition of the 38 C1 PASS: 12 positive-path, 9 known-limit, 17 negative (2 PARTIAL, 1 exception-based).

## 5. Errata (CA06: originals kept; nothing deleted)
| # | Where | Original statement | Correction |
|---|---|---|---|
| E1 | per-test-41.csv row 28 (`test_wiki_l06_040_each_of_twelve_invalid_messages_ends_without_any_effect_beyond_the_bounded_operation`), CROSSWALK-S4 section 3 | vacuity "none"; section 3 counts "27 marked none" as control-proven | The test asserts `(rejected, accepted) == (5, 7)`: PASS-as-written, **NOT control-proven**, Wiki criterion (>=11 of 12) unmet. Arithmetic checked against the CSV: exactly 27 rows have vacuity "none" (14 others), row 28 is one of them, so rows marked none and not excluded are **26, not 27**. The CSV is unchanged. The 26 include positive-path rows (e.g. the smoke route and TC-L07-013) and "control-proven" is relative to the frozen assertions |
| E2 | REPORT.md, CSV columns `exchange_identity_check_calls/raised` | identity check exercised in every one of the 41 | 39 of 41 (REVIEW-CORRECTIONS M1) |
| E3 | REPORT.md | C2 "same tuple, same environment" | asserted, not evidenced (M2) |
| E4 | REPORT.md | guard OK on the real config before the run | unverifiable; guard not claimed for C1 (M4) |
| E5 | CROSSWALK-S4 section 14 | trailing run 41233326892 "reported by coordinator"; run 41234082886 absent | both recorded in section 1 above with verified metadata |

## 6. Issue #254 completion definition (seven criteria)
| # | Checkbox text (exact) | Status | Evidence |
|---|---|---|---|
| 1 | One source-authentic, versioned compatible current-stack manifest includes the migrated Registry. | PARTIALLY SATISFIED | Candidate manifest published as DRAFT hub PR #255 (see PR #255 for the current head), not adopted, HOLD; canonical component lock unchanged and stale; "source-authentic" is not established (F2, F3) |
| 2 | Replay, ODES, Pack contracts accept the selected CP/Runtime pair only when genuine compatible inputs are provided and reject substitutions. | PARTIALLY SATISFIED | Replay #81, ODES #142, Pack #65 merged with tests; BUT F1 (resealed substitution accepted by Replay) and caller-asserted labels (F2); probe typed refusals for missing/plain member, tampered digest, catalogue tie |
| 3 | Exchange exact profile matches accepted downstream component SHAs and refuses bad identities. | SATISFIED for the tested scope | Exchange #63 (r2 profile, tuple tests), mandatory s3 guard refusals in `run-41-merged-tuple-controls/`; residual F5 (refs/replace, Manifest not covered) |
| 4 | All 41 previously blocked tests rerun without weakening assertions, with actual per-test verdicts and immutable evidence. | SATISFIED as developer evidence with disclosed caveats | per-test-41.csv, C1 38/0/3 primary (3 infra BLOCKED), C2 supplementary, C3 hosted; nine limit rows, partials, 39 of 41, Architect acceptance per D2; no test assertion changed (only the 4-line label-only `cur` branch in the chain test) |
| 5 | Minimal real Registry-governed CP → Replay probe executed or honestly BLOCKED; Registry-wide Wiki qualification is not implied. | SATISFIED (narrow) | `registry-probe/VERDICTS.md`: CP-to-Replay PASS_IMPORT; Runtime governed export BLOCKED; NON_DETECTION_RECORDED for F1; no enforcement qualification |
| 6 | Consolidated security crosswalk published; unresolved 5 failures and 4 untested cases remain explicit. | SATISFIED once PR #260 merges | CROSSWALK-S4.md, REVIEW-CORRECTIONS.md and this file on the PR #260 branch (unmerged); F8 and F9 list the 5 and 4 |
| 7 | Formal certification and release holds unchanged. | SATISFIED | No hold changed; `tools/` and `process/mvp-acceptance` byte-identical to main; v6 candidate sha256 42b482eec25b9d9c1455b5eefc63fb726d7a8041698831cc3c168ea5809a1846, no v7 |
Because criteria 1 and 2 are only PARTIALLY SATISFIED, #254 is not fully closed by evidence alone.

## 7. Smallest remaining actions
1. Operator merges PR #260 (evidence only; CI green at verified head 2978679f; see PR for the final head).
2. Operator merges PR #255 (candidate manifest only; this is NOT adoption).
3. Separate adoption decision for the canonical component lock.
4. Architect decision on closure of #254, because criteria 1 and 2 are PARTIAL (F1 owner decision at Replay is the main blocker for 2).

## 8. Checksums
`SHA256SUMS.s4` covers CROSSWALK-S4.md, S4-CLOSEOUT.md, REPORT.md, README-S3-run.md and REVIEW-CORRECTIONS.md. Earlier files are untouched: `SHA256SUMS`, `SHA256SUMS.crosswalk`, `-v2`, `-v3`, `c3-hosted-run/SHA256SUMS`, `registry-probe/SHA256SUMS`. As Worker A documented, `SHA256SUMS.crosswalk` and `-v2` fail for CROSSWALK-S4.md (superseded). Because this commit prepends errata blocks to REPORT.md and README-S3-run.md and appends to CROSSWALK-S4.md, the entries for those files in `SHA256SUMS` and `SHA256SUMS.crosswalk-v3` also no longer match; both are superseded by `SHA256SUMS.s4` for those files. `SHA256SUMS.runner-listing-incl-native` verifies only after untarring native.tar.gz.
