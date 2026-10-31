# CROSSWALK-S4: consolidated Security Wiki results (A / B / C) and closeout status

**Corrections after independent review: see REVIEW-CORRECTIONS.md (governs where it differs). Key changes: identity check evidenced in 39 of 41 rows, not 41; supplementary re-run is under-evidenced; TC-L06-040 twelve-invalid row is PASS-as-written (5 of 12 rejected, criterion unmet), not control-proven; real-config guard run unverifiable; Replay resealed-substitution non-detection is a named residual.**

Governing: Engineering Constitution cogno-us/cognous-engineering-constitution@1c2e920f4e58e07a52e8e2408a506cf7dbc1292b; static plan Issue #254 (cogno-us/cognous-open-control-stack), OCS-INTEGRATION-COMPAT-20261031/1.0; sprint OCS-254-S3/S4, Tasks 7-8. Author: Worker D (evidence and crosswalk). Non-authorizing. `claims_made = []`.
Scope: developer / local-offline results. This is NOT independent qualification, NOT a release, production or certification claim. Historical reports and raw files are not edited; this file is new and REPORT.md is unchanged.

## 1. Headline (three results, never merged into one number)
| | Result | PASS | FAIL | BLOCKED | Where |
|---|---|---|---|---|---|
| A | Original current-stack assessment (290 tests) | 244 | 5 | 41 | `results/security-wiki-current-stack-20261031/` |
| B | Exchange-only diagnostic on the 41 (unmerged Exchange 05ba99ba, mixed Replay/ODES/Pack) | 0 valid | 0 valid | 41 | `results/security-wiki-exchange-compat-20261031/` (on main via #259) |
| C1 | Merged tuple, strict single execution of the 41 (PRIMARY) | 38 | 0 | 3 | `run-41-merged-tuple/` |
| C2 | C1 plus the labelled supplementary re-execution of exactly the 3 blocked ids | 41 | 0 | 0 | `run-41-merged-tuple-supplementary-enospc3/` |

**Primary figure: C1, 38 PASS / 0 FAIL / 3 BLOCKED.** Reason: the sprint rule is a single execution with no retries; C1 is the only execution of the full 41 under the frozen invocation, and its 3 BLOCKED are TC-L06-020 x3 failing with `OSError: [Errno 28] No space left on device` (shared host disk full; junit failure and two setup errors "could not create numbered dir"). That is an infrastructure cause, not a component refusal and not evidence about the control. C2 is a second execution done after space was freed (no run.json, command, tuple, pristine-after or disk record exists for it, so same tuple/environment is asserted, not evidenced), of exactly those 3 ids, same tuple and environment, once, in a separate directory; all 3 PASS (observer calls 9/4/3, raised 0). C2 is reported because it is informative, but it is a re-run chosen after seeing the result, so it does not replace C1 unless the architect accepts it. Neither figure is extrapolated to the 244 cases not rerun, to the 5 failures or to the 4 unimplemented cases.

## 2. Exact tuple executed (commit -> tree; pristine fresh checkouts, HEAD and tree verified equal to ls-remote main)
| component | commit | tree |
|---|---|---|
| Control Plane | b19c47ddd020409d24e52e70b11359c46265edbb | 039219b5aba7a157fff79781c716067fad7ed985 |
| Runtime | f7a55e2a8494801e49193f9f46935f0a971c248d | 97da8323368bb5a573fd157b11a9c1dda1178a10 |
| Replay (#81) | d395e37c443fedf1bf6b9a4651338b7b7de4a553 | 0bdee3eacd650ecb0e99781635a972e68cbe2853 |
| ODES (#142) | 77fd7a1cb1dd7a2dbc9ac3c02538a617056688ae | d8b33261de975fc504ff8f0ac30a8f47e8ebd43f |
| Evidence Pack (#65) | 96f5f2e126a9c27a75716658d4d2e85baf94b40b | 2fc26d4c86e65b22bdffedf1090a15e7167440d3 |
| Governed Exchange (#63 squash; profile `security-runtime-current-20261031-r2`) | 746378d74bff59314bdcf8f0b50b19ab94679ba9 | dcbe909f96d7c83e6281c5679283bd65cf19dbdb |
| Action Manifest | fa170815ef96a54c233d0dd9da821b60debabf8b | 3b0e3772e944aa668c8f4b879588c7cc3e2c32be |
| Migrated Registry (recorded, not exercised by the Wiki harness) | 6b96a9a658923954433dc1a4c13626fa5145b9c7 | 38d50602ae725e208f010baba05bbf7b908e76ac |
| Qualification main merged into run branch (#259) | 5409d4776a9daff204fc97b71958b4dee12687b0 | 43f171ee47eb7fb8b861f444d386f1d137192f75 |

Run configuration: Qualification run commit b48675b7bb3638a938fd3f5f3d80bec36a17a2bf (tree ec8c57f250adcf38ce8727967618aba3ec1e7c08, worktree clean after), suite generation label `cur` (patch ea8bddcd, sha256 cb0fc4d2943db0bfc3055c0c25b573c8c84349828fe631beae2b2deb268e8d0d; caller-asserted PROVISIONAL DEVELOPMENT PIN labels, +5/-1, labels only), validation id `current-stack-S3-20261031`. All 41 rows in the CSV carry the identical executing-revision string; it equals the tuple above and `raw/run.json` checkouts and `raw/tuple.json` (re-read by Worker D). Registry is recorded only (the Wiki battery does not import it). Registry bytes exercised in the probe are a40fe755 (code-equal to 6b96a9a6 outside docs/ and README.md, 62 doc paths differ), see section 4.

Command (from `raw/run.json`, abridged): `python3 -m pytest -q -p no:cacheprovider -p wiki_exchange_observer -o junit_family=xunit1 -rA --junitxml=.../run-41-merged-tuple/raw/junit.xml --basetemp=.../raw/native <41 explicit node ids>` via `tools/run_wiki_s3.py` (one process, workers 1, retries 0, attempts 1, no `-x`). Started 2026-10-31T17:20:32Z, finished 17:27:55Z, pytest return code 1 (1 failure, 2 errors, 0 skipped, 41 testcase elements). Environment: Linux 6.18.44 x86_64, Python 3.13.18, pytest 9.1.1, git 2.43.0, 2 CPUs; pip freeze in `raw/run.json`. Supplementary: `nodeids-3.txt` sha256 90e47512..., run once.

## 3. Independent validation by Worker D (recomputed from raw evidence, not from the CSV)
* Verdicts: for each of the 41 ids the verdict was recomputed from `raw/junit.xml` (unique testcase match by name, element type failure/error/skipped) and `raw/obs.json` (identity-check `calls >= 1`, `raised == 0`). Result 38 PASS / 3 BLOCKED, junit 0 skipped. A junit failure or error was BLOCKED only if its message is ENOSPC or "could not create numbered dir": exactly the 3 TC-L06-020 ids. **Disagreements with `per-test-41.csv` verdict_primary_run: 0.** The supplementary junit gives 3 PASS for those ids.
* Identity set: 41 unique ids; `raw/nodeids-41.txt` sha256 `bd43f8891e4db51ca6a5d279328a58a0ac73e7b6e27da209c56d2313a836fc3c` (matches the expected wiki41-nodeids digest and equals `blocked41-nodeids.txt` of the Exchange diagnostic by sorted-set comparison); the CSV id set equals it.
* Exchange identity check: 39 of 41 rows have observer calls >= 1 and raised = 0 evidenced; the 2 setup-ERROR rows (TC-L06-020 each_hop, forwarded_message) carry a stale value from the preceding test because the observer resets counters only in the call phase (correction M1). Note: observer-calls shows the check ran and accepted; it is not an assertion about the controls.
* Checksums recomputed: S3 `SHA256SUMS` (25 entries) all OK before and after the probe merge; `registry-probe/SHA256SUMS` (74 entries, digest bb6a73e0767ddfaf6661ac0c5f0d52b2e4603b9eaaa11d8c9d0dc810f766e59c) all OK; runner listing `SHA256SUMS.runner-listing-incl-native` non-native entries OK (the 4955 native files were not re-extracted for disk reasons; the tarball is covered by the S3 SHA256SUMS); historical A and B SHA256SUMS all OK.
* Probe merge: adds 75 files, all under `results/security-wiki-s3-20261031/registry-probe/`, 0 modified, 0 other paths.
* Not independently re-measured: PASS rows' "actual observed behaviour" text in the CSV summarises the test source's assertion set (pytest PASS = every assertion held); it is not a separate measurement.

### Vacuity notes (honest classification)
PASS means the documented assertion held. It does not always mean a hostile input was refused.
* **PASS-as-documented-limit (9 known_limit / limit-assertion rows; the test asserts that a limitation exists; NOT control-proven):** TC-L06-020 known_limit (hop where content was stopped is not recorded); TC-L06-038 known_limit (registry holds one recipient, refusals not stored); TC-L06-018 x2 (forged message accepted when consistent / refusals before acceptance not stored); TC-L06-040 (extra members/content types/size accepted as data); TC-L06-039 sender label not bound to the actor; TC-L06-039 held request retained; TC-L06-045 x2 (hop record, correlation id not a member). These are the documented limits, not security properties established.
* **PASS with PARTIAL vacuity:** TC-L06-039 `[plain]` and `[urgent_administrator]`: sub-case `tool_not_in_the_manifest` asserts only that an exception occurred (the text identifies the Manifest-declaration boundary); 5 of 6 sub-cases reach the Control Plane decision and hold with reasons. Not control-proven for that sub-case.
* **PASS, exception-based but boundary identified:** TC-L06-003 undeclared action (`pytest.raises`, message 'declared Manifest action' asserted; boundary = Manifest-declaration check at bundle export).
* **Other flagged rows:** TC-L07-008 (run_decision accepts an exception as refusal only for the high-value variant; legitimate-request positive path), TC-L07-012 (route A legs verified non-vacuous by diagnostic).
* **TC-L06-040 twelve-invalid row (correction M3): PASS-as-written; the test asserts (rejected, accepted) == (5, 7), so the Wiki criterion of at least 11 of 12 is unmet; NOT control-proven (its vacuity entry 'none' in the CSV is superseded).**
* **Control-proven (typed refusal or no-effect observed at the intended boundary):** the remaining rows (27 marked none, plus smoke positive path). Residual: "control-proven" is relative to the frozen test's assertions, with synthetic data and caller-asserted labels.
* Note on B: the two TC-L06-039 junit PASSes in B were rejected as vacuous there (exception-only). In C they are accepted with the PARTIAL note only because the same exception-only sub-case is 1 of 6 and the other 5 are substantive; this is a judgement carried over from Worker A and Worker D agrees but flags it for the architect.

## 4. Mapping of the 41 to original blocked classification
Original A: 39 identity-blocked (`Exchange gax_ref_runtime._verify_refusal_profile_sources: candidate source identity mismatch`) and 2 originally junit-PASS tests (TC-L06-039 plain/urgent_administrator) reclassified BLOCKED as vacuous (identity check raised 6 times). B (Exchange-only diagnostic): all 41 BLOCKED at the Replay revision gate (`ImportContractError: unsupported Control Plane revision`; 2 more expected `exc is None`, 1 TC-L06-003 case n/a; 2 junit PASS rejected as vacuous), Exchange identity refusals 0. C: see column. (C2 column = supplementary re-execution result.)

| # | case | test (shortened) | A original | B intermediate | C1 primary | C2 supp. |
|---|---|---|---|---|---|---|
| 1 | smoke | `smoke_route_c_exchange_destination_executes_once` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 2 | TC-L06-020 | `l06_020_three_sequential_exchanges_instruction_bearing_narrative_at_the_third_` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | BLOCKED | PASS |
| 3 | TC-L06-020 | `l06_020_each_hop_is_assessed_against_its_own_sender_recipient_and_authority` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | BLOCKED | PASS |
| 4 | TC-L06-020 | `l06_020_forwarded_message_with_a_changed_requested_action_is_refused_by_commit` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | BLOCKED | PASS |
| 5 | TC-L06-020 | `l06_020_normal_three_hop_chain_with_current_authority_executes_once` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 6 | TC-L06-020 | `l06_020_known_limit_the_hop_where_content_was_stopped_is_not_recorded` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 7 | TC-L06-038 | `l06_038_six_permitted_links_expressed_as_per_recipient_registries_are_accepted` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 8 | TC-L06-038 | `l06_038_undeclared_new_peer_and_reverse_direction_are_refused_with_typed_codes` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 9 | TC-L06-038 | `l06_038_relayed_request_is_assessed_on_its_own_sender_and_authority` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 10 | TC-L06-038 | `l06_038_known_limit_a_registry_holds_one_recipient_and_refusals_are_not_stored` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 11 | TC-L06-041 | `l06_041_look_alike_sender_copied_capability_text_and_changed_recipient_are_eac` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 12 | TC-L06-041 | `l06_041_new_recipient_is_not_trusted_until_declared_to_the_registry` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 13 | TC-L07-008 | `l07_008_thirty_instruction_bearing_exchange_narratives_for_three_unlisted_acti` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 14 | TC-L07-008 | `l07_008_legitimate_request_for_each_registered_action_executes_once` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 15 | TC-L07-009 | `l07_009_seven_hidden_text_forms_in_an_exchange_narrative_do_not_change_the_aut` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 16 | TC-L07-009 | `l07_009_benign_page_content_executes_the_bounded_operation_once` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 17 | TC-L07-009 | `l07_009_retained_bundle_instructing_a_different_operation_is_refused` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 18 | TC-L07-012 | `l07_012_five_instruction_forms_in_retrieved_text_do_not_change_the_authorized_` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 19 | TC-L07-012 | `l07_012_redirect_link_in_a_payload_target_is_refused_by_exact_target_binding` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 20 | TC-L07-012 | `l07_012_clean_documents_execute_the_bounded_operation_unchanged` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 21 | TC-L07-013 | `l07_013_twelve_instruction_bearing_destination_observations_are_recorded_as_da` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 22 | TC-L06-018 | `l06_018_three_normal_exchanges_between_the_registered_agents_each_execute_once` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 23 | TC-L06-018 | `l06_018_a_replayed_message_adds_no_second_effect_and_a_reused_identifier_with_` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 24 | TC-L06-018 | `l06_018_a_retired_a_unregistered_and_a_misaddressed_sender_are_refused` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 25 | TC-L06-018 | `l06_018_a_forged_message_claiming_a_registered_agent_is_accepted_when_consiste` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 26 | TC-L06-018 | `l06_018_refusals_before_acceptance_are_returned_and_not_stored_known_limit` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 27 | TC-L06-040 | `l06_040_eight_valid_messages_are_accepted_and_each_executes_the_bounded_operat` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 28 | TC-L06-040 | `l06_040_each_of_twelve_invalid_messages_ends_without_any_effect_beyond_the_bou` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 29 | TC-L06-040 | `l06_040_extra_members_content_types_and_size_are_accepted_as_data_while_mistyp` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 30 | TC-L06-039 | `l06_039_six_in_scope_requests_are_allowed_and_each_executes_once` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 31 | TC-L06-039 | `l06_039_six_out_of_scope_requests_are_denied_in_both_phrasings_with_no_effect[` | identity-blocked; originally vacuous PASS reclassified (observer: identity check raised) | Replay-blocked; junit PASS not accepted (exception-only) | PASS | - |
| 32 | TC-L06-039 | `l06_039_six_out_of_scope_requests_are_denied_in_both_phrasings_with_no_effect[` | identity-blocked; originally vacuous PASS reclassified (observer: identity check raised) | Replay-blocked; junit PASS not accepted (exception-only) | PASS | - |
| 33 | TC-L06-039 | `l06_039_the_decision_names_the_scope_of_the_actor_and_the_user_of_the_request_` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 34 | TC-L06-039 | `l06_039_the_sender_label_is_not_bound_to_the_actor_so_a_listed_low_trust_sende` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 35 | TC-L06-039 | `l06_039_a_held_request_is_retained_with_the_proposal_of_the_actor_and_the_user` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 36 | TC-L06-045 | `l06_045_five_requests_are_each_reconstructed_across_the_exchange_decision_effe` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 37 | TC-L06-045 | `l06_045_the_hop_names_the_actor_the_user_the_payload_commitment_and_the_decisi` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 38 | TC-L06-045 | `l06_045_the_correlation_identifier_is_not_a_member_of_the_message_known_limit` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 39 | TC-L06-045 | `l06_045_a_retried_request_keeps_the_identifiers_and_a_missing_current_bundle_i` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 40 | TC-L06-003 | `l06_003_a_sender_a_recipient_and_an_actor_that_are_not_declared_are_refused_wi` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |
| 41 | TC-L06-003 | `l06_003_an_undeclared_action_is_refused_with_no_effect` | identity-blocked (Exchange source identity) | Replay-blocked (revision gate) | PASS | - |

## 5. Registry import probe (narrow; NOT Registry enforcement qualification)
Evidence: `registry-probe/` (75 files; branch `security-wiki/s3-registry-probe-20261031` head 7399a045a6983108e289cf9fd7a941a4441d0531; SHA256SUMS digest bb6a73e0...e59c; probe commit 877bc005, probe file unedited; synthetic keys, patched clock, one scenario). Verdicts in `registry-probe/VERDICTS.md`:
* Source identity: PASS (modules loaded from pristine checkouts; Registry bytes exercised = a40fe755, not 6b96a9a6).
* CP Registry-governed decision and execute: PASS. Replay E1 import of the real CP record: PASS_IMPORT (retains digest, family rows, CUR label; import report complete=False, finding B004; Replay marker `internal_consistency_only_registry_source_revision_unverified`).
* Missing member, plain-profile member, tampered digest, catalogue tie: REFUSED_AS_EXPECTED (Replay typed refusals).
* Substituted configuration (age 61, family dropped): refused CP-side at execute (`authorization_binding_changed`); Replay only RETAINS the refusal record. **Resealed substitution at Replay: ACCEPTED (NON_DETECTION_RECORDED).**
* Revoked / withdrawn / expired selection: refused CP-side only; NOT_APPLICABLE at Replay (no selection state). Forged signature: refused CP-builder-side with synthetic keys; NOT_APPLICABLE at Replay.
* Decision lineage (ids, action, tenant): PASS. Source lineage (Registry SHA, selection, signature, trust): NOT_APPLICABLE / UNAVAILABLE. Pack/ODES: NOT_RUN.
* **Governed Runtime export: BLOCKED** (see section 6).
* Non-claims: source authenticity; signature or trust; live configuration selection; runtime enforcement; decision/execution configuration consistency; independent verifier acceptance; Registry enforcement qualification; qualification of any kind.

## 6. Runtime governed-export limitation (outside this sprint, not repaired, not fabricated)
`PinnedControlPlaneExecutor.execute` rebuilds the workflow via `workflow.__class__(...)` and cannot construct `GovernedPolicyWorkflow`; no production interface exists to export a Registry-governed Runtime record. The probe reports BLOCKED with this interface gap. No production API was added.

## 7. Existing and unimplemented items (untouched)
* Five existing security failures in A, not amended, not rerun: TC-L06-018, TC-L06-022, TC-L06-040, TC-L09-004, TC-L15-019. They remain FAIL. (TC-L06-018/-040 also have separate known-limit PASS rows in C that document limits; those do not offset the failures.)
* Four unimplemented Wiki cases (NOT TESTED): TC-D09-004, TC-D13-003, TC-L02-002, TC-L08-033.
* 244 A PASS cases were not rerun (no documented change-impact reason); they are not restated as qualified against the new tuple.

## 8. Unqualified provenance and trust surfaces
* Provenance labels (`cur` generation, PROVISIONAL DEVELOPMENT PINs) are caller-asserted and inherited; no component verifies who asserted them.
* NAMED RESIDUAL: Replay accepts a resealed substituted configuration (probe: NON_DETECTION_RECORDED; probe overall PASS despite BLOCKED Runtime export; bytes exercised a40fe755 not 6b96a9a6); Replay carries no Registry source revision, selection state or signature.
* No Registry source trust: authenticity, signature trust and live selection are not established at Replay (or anywhere in this evidence).
* Governed Exchange: git `replace` refs in a candidate checkout are not neutralised by the source-identity check; the unhardened refs/replace residual stands.

## 9. Independent qualification status
**NONE.** All work was done by AI workers directed by the lead builder (builder Worker A, probe Worker B, evidence Worker D, reviewer Worker E). Worker E's review is a read-only AI review; AI-only reviewers give no organisational independence. Constitution question Q7 (independence) is **NOT ESTABLISHED**. Nothing in this document is an independently qualified behaviour.

## 10. Remaining release and production holds (all standing holds unchanged)
No release, production deployment, formal security certification or hold removal is authorized or claimed. The tuple is a tested developer tuple, not a release; the hub manifest (Worker C) is a reviewable candidate and does not replace the canonical component lock. The five failures, the four unimplemented cases, the Runtime governed-export gap, the provenance/trust gaps and the absence of independent qualification each independently prevent a release claim. Issue #254 criteria that need independent qualification or the export limitation remain open.

## 11. Runner-guard gap found by Worker A, and the mitigation (stated without overstatement)
* Finding: `tools/run_wiki_s3.py --dry-check` refuses missing/short/branch revisions, placeholders and TEMPLATE markers, inconsistent profile names, tuple/config/checkout mismatches, dirty/wrong-HEAD/missing checkouts and a missing cur patch, but does NOT refuse a consistently wrong Exchange profile (original -20261031, typo -r3, p2) or a consistently mixed-generation set (Replay 40012b8c, ODES 1a5e1d30): dry_check OK, collected 41. (`run-41-merged-tuple-controls/`.)
* Mitigation: new read-only `tools/s3_tuple_guard.py` (stdlib; pins tuple, trees, profile and the r2 block of the Exchange source); refused all those scenarios in the scratch-copy controls. At run time the Exchange itself refuses the original profile and Replay 40012b8c fails to import CUR names (`runtime-boundary-single-case-controls.txt`).
* **Timing, from commits and file times:** the guard was added in freeze commit 877bc005 (2026-10-31T17:19:49Z); the controls outputs were written 17:19:40Z, i.e. BEFORE the primary run (started 17:20:32Z on run commit b48675b7). So the guard existed and was exercised on scratch scenarios before the run. REPORT.md states that the guard was also run OK against the real frozen config before the run; **no committed output for that real-config guard run exists** (the committed guard outputs are scratch-copy controls, and `raw/run.json` does not record a guard invocation; the pytest command was launched through the runner, which does not call the guard), so that statement is not verifiable from the committed artifacts (correction M4); the run is supported post hoc only by run.json tuple/trees matching the guard's pins. The guard was not a gate in the runner. The runner's own pre-run checks (`--dry-check`, tuple/tree/HEAD checks recorded in run.json, `checkout_problems` empty) did run. The guard is unqualified tooling written by the same worker/lead.
* Also disclosed: the first real invocation (freeze 877bc005) was refused at the runner's collect-only step (observer wrote into a not-yet-created raw/), 2-line fix b48675b7 (the freeze used); no test body ran. One id (the first of the 41) was run once in a scratch copy as a control rehearsal (PASSED), not used as a verdict.

## 12. CI status and root cause (head ac3dfccf58e526f94e46d6fc81ab640bb9098da4; PR #260 into main)
Failing: `validate` (x2), `validate-and-build`, `integrity`. Passing: CodeQL, Analyze (actions, python, javascript-typescript, rust), `actual-components` (x2). Main is green.
Root cause per Worker A (Worker D confirmed the changed file set, not the CI log): `tests/test_mvp_acceptance_gate.py` `RulingsTwoTests` fails because the committed candidate `process/mvp-acceptance/candidate-commitment.proposed.v6.json` commits every file in `tools/` by bytes; the approved cur patch (`tools/run_security_runtime.py` modified) and the new tools files (`registry_integration_probe.py`, `run_wiki_s3.py`, `s3_tuple_guard.py`, `wiki_exchange_observer.py`) change that set. The new head after the probe merge adds only evidence files, so it does not change this.
Smallest options (architect decision; NEITHER applied, the MVP gate was not touched): (1) a new versioned candidate v7 produced through the gate that includes the new tools set; (2) exclude these tools from the gate's commitment (move them out of `tools/` or amend the commitment rules via the gate process). Either needs the architect.

## 13. Evidence index (all under `results/security-wiki-s3-20261031/` unless noted)
`per-test-41.csv` (7 required fields plus extras); `run-41-merged-tuple/raw/{junit.xml,log.txt,obs.json,run.json,tuple.json,nodeids-41.txt,collect-only.txt,native.tar.gz}`; `run-41-merged-tuple-supplementary-enospc3/raw/`; `run-41-merged-tuple-controls/`; `diagnostics-vacuity/`; `registry-probe/`; `merged-components-verification/`; `cur-patch-verification/`; `REPORT.md`; `SHA256SUMS`. Historical (unchanged): `results/security-wiki-current-stack-20261031/`, `results/security-wiki-exchange-compat-20261031/`.
