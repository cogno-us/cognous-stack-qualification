# Evidence applicability crosswalk (read-only inspection; no verdict authority)

Evidence root: `/tmp/claude-0/ev`. Row numbers below are **1-based line numbers** of `runs/A-main4/f3a_evidence.jsonl` (901 rows; row 1 = PREFLIGHT). Nothing in `/tmp/claude-0/ev` was modified; scratch copies are in `/tmp/claude-0/work/agents/tmp`.

## 0. Integrity and identity checks (executed, not assumed)

| Check | Result |
|---|---|
| `sha256sum -c MANIFEST-final.txt` | 168 listed, **168 OK, 0 mismatches**. Coverage: every file on disk (excluding the git-ignored `runs/*/*/tree/`, `B-mutants/*/{src,cp,tests,schemas}`) is listed except `MANIFEST-final.txt` itself; no listed file is missing. |
| `sha256sum -c MANIFEST-freeze.txt` | 40 listed, **0 mismatches**. `PROTOCOL-F3-v1.md` = `e799b108...` as quoted in VERDICTS. |
| `candidate-tree-before.txt` | content `1e7a7555eb3a956fcd2db21d3eb944169d0f7783` |
| `git -C /home/claude/cogno-us/cognous-control-plane rev-parse 739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69^{tree}` | `1e7a7555eb3a956fcd2db21d3eb944169d0f7783` -> **equal** to the recorded id. |
| C-compat probe vs git | `probe-main.json` `all_modules_sha256` (47 modules) and `schema_files_sha256` (20 files) all equal `sha256(git show 739efe7:<path>)`; git has 47 `.py` under `src/agent_control_plane` at 739efe7 (full coverage). `probe-base.json` (45 modules, 20 files) all equal `b7eb11a` blobs. So the code tree that was executed for the probe is byte-identical to 739efe7 / b7eb11a `src/` and `schemas/`+`conformance/`. |
| Harness provenance (AMEND chain) | `pre-AMEND-1` + `A-AMEND-1.diff` = `pre-AMEND-2` (hash equal); + `A-AMEND-2.diff` = `pre-AMEND-3` (equal); + `A-AMEND-3-4.diff` = `harness-final/test_f3a_independent.post-AMEND4.py` (`a5147412...`, equal, reproduced with `patch`). So the final harness text is reconstructable and matches the manifest. |
| Run-to-run consistency | A-main3 and A-main4 fail the identical 23 cases; the 22 `pin_raw_outcome` details are identical across the two runs; A-main4 adds only A25, the A16 d0 sub-case and the A15/A16 strip change (AMEND-3/4). |

### Gaps/provenance observations on the run itself
1. **The CP tree id is not recorded inside any A-main4 artifact.** Row 1 (PREFLIGHT) records only `acp` = `.../scratchpad/run/cp/src/agent_control_plane/__init__.py`, python `3.11.18`, pin `{head: a40fe755e2384a99c37016fa9ad59396f1835900, pin_dir: .../run/reg-v8, require: "1"}`. The tree id exists only in `candidate-tree-before.txt` ("before") and in VERDICTS prose ("identical before and after all runs"). **There is no "after" artifact** in the extracted set (`find` for `*tree*` outside `tree/` dirs returns only `candidate-tree-before.txt`). The executed `src/` is independently tied to 739efe7 only by the C-compat module hashes (above), not by anything captured in the A-main4 run; `tests/` and `docs/` used by A-main4 (A24 reads `docs/*.md`; harness imports `tests.test_bounded_authorization`, `tests.test_runtime_authority`, `tests.v02_support` from `run/cp`) are not hash-captured at run time. Tree equality therefore is an inference from "before" file + VERDICTS statement.
2. **Environment not captured in the run artifacts.** `stdout.txt` is `pytest -q` output with no header (no platform/plugins/rootdir/pydantic). pydantic 2.14.2, PyNaCl 1.6.2, pytest 9.2.0, pytest-asyncio 1.4.1 appear only in `crosswalks/D/source-identity.md` §7 (Worker D inspection of `run/venv311`) and VERDICTS §1, i.e. post-hoc, not run-time capture. Not recorded for A-main4: `F3_EVIDENCE_DIR`, `F3_OLD_SRC` (only inferable from A06 row 195 `acp` = `.../run/old-b7eb11a/src/...`), `F3_PIN_DURABLE_REFUSAL_REQUIRED` (not recorded; inferable as default `1` because the durable check is emitted as `CHECK_FAIL`, the `=0` mode would emit `OBSERVATION ...(evidence_only)`), `PYTHONDONTWRITEBYTECODE`, `OCS_REQUIRE_REGISTRY_PIN` is recorded (`"1"`). stderr only has the pytest-asyncio `asyncio_default_fixture_loop_scope` deprecation warning and the venv path `.../945ef3c2-.../scratchpad/run/venv311/...`.
3. The registry pin `head` is `git rev-parse HEAD` in the pin dir (no worktree-clean check recorded at run time; Worker D asserts clean at inspection time).
4. Executed harness file path in stdout is `../../../work/A/test_f3a_independent.py`; no hash of that live file was captured at run time (no copy in `runs/A-main4/`); equivalence to `harness-final` is established only by the reconstruction above and the mtime ordering (diff 18:36, run 18:36:33-18:37:47 per row `t`).
5. Mutation results `A-mutants/D06-M01..M05,M09,M10,M12,M13` have only `ev/` (pre-AMEND-3 harness, 96 tests; e.g. M03 stdout "25 failed, 71 passed"); only M06/M07/M08/M11 have `ev4/`. Mutation adequacy for the pin-export/claim checks is against the earlier harness text.

## 1. A19 pin-export mismatch cases (22 members)

Test: `test_A19_pin_export_refuses_per_perturbed_member[<member>-pin-export]` (harness lines 1188-1211; judge `judge_pin_refusal` 477-489). Fixture `new_case(tmp_path,"pin")` (profile-bearing, F4-only; R8). Perturbation is **persisted-side only**: the stored `effective_configuration` member is replaced by a self-consistent (digest recomputed by `my_digest`) copy differing in exactly one member; live configuration unchanged. Call: `assess_authorization_pin(flow, fx.p, persisted, now=NOW, host_policy_binding=fx.binding)`.

Each pin-export case has 7 rows: (+0) `control_status_bound_before_perturbation` PASS; (+1) `perturbation_changed_digest_and_is_self_consistent` PASS; (+2) `pin_raw_outcome` OBSERVATION; (+3) `<m>:export_not_active_no_payload` PASS; (+4) `<m>:reason_names_code` **CHECK_FAIL**; (+5) `<m>:durable_effect_time_refusal` **CHECK_FAIL**; (+6) `<m>:destination_apply_never_called` PASS.

| # | member | pin-export rows (raw obs row) | execute rows |
|---|---|---|---|
| 1 | `scope.consumer_id` | 526-532 (raw 528; fails 530,531) | 520-525 |
| 2 | `scope.tenant_id` | 539-545 (raw 541; fails 543,544) | 533-538 |
| 3 | `scope.action_id` | 552-558 (raw 554; fails 556,557) | 546-551 |
| 4 | `scope.institution_id` | 565-571 (raw 567; fails 569,570) | 559-564 |
| 5 | `scope.authority_domain` | 578-584 (raw 580; fails 582,583) | 572-577 |
| 6 | `host_profile_digest` | 591-597 (raw 593; fails 595,596) | 585-590 |
| 7 | `effective_profile_digest` | 604-610 (raw 606; fails 608,609) | 598-603 |
| 8 | `f4_scalars.status_max_age_seconds` | 617-623 (raw 619; fails 621,622) | 611-616 |
| 9 | `f4_scalars.approval_max_age_seconds` | 630-636 (raw 632; fails 634,635) | 624-629 |
| 10 | `other_scalars.clock_tolerance_seconds` | 643-649 (raw 645; fails 647,648) | 637-642 |
| 11 | `other_scalars.identity_max_age_seconds` | 656-662 (raw 658; fails 660,661) | 650-655 |
| 12 | `other_scalars.mandate_max_age_seconds` | 669-675 (raw 671; fails 673,674) | 663-668 |
| 13 | `observation_policy.max_age_seconds` | 682-688 (raw 684; fails 686,687) | 676-681 |
| 14 | `observation_policy.clock_tolerance_seconds` | 695-701 (raw 697; fails 699,700) | 689-694 |
| 15 | `observation_policy=null` | 708-714 (raw 710; fails 712,713) | 702-707 |
| 16 | `families.0.slot` | 721-727 (raw 723; fails 725,726) | 715-720 |
| 17 | `families.0.family_id` | 734-740 (raw 736; fails 738,739) | 728-733 |
| 18 | `families.0.contract_version` | 747-753 (raw 749; fails 751,752) | 741-746 |
| 19 | `families.0.family_schema_revision` | 760-766 (raw 762; fails 764,765) | 754-759 |
| 20 | `families.0.effective_policy_digest` | 773-779 (raw 775; fails 777,778) | 767-772 |
| 21 | `families=none_declared` | 786-792 (raw 788; fails 790,791) | 780-785 |
| 22 | `families=extra_class_age_declared` | 799-805 (raw 801; fails 803,804) | 793-798 |

**Observed fields (identical in all 22 `pin_raw_outcome` rows):** `state: "unknown"`, `payload: null`, `terminal_status: null`, `raised: null`, `reason: "authority not supported but not positively terminal: binding changed"`, `new_refusal_reasons: []` (no EffectTimeRefusal row), `new_attempts: 0`, `dest_calls: 0`, `dest_unchanged: true`. `check` rows: `export_not_active_no_payload` carries `raised: null, state: "unknown"` (e.g. rows 542, 555, ...). `reason_names_code` rows carry `reason` verbatim (e.g. row 543); `durable_effect_time_refusal` rows carry `rows: []` (e.g. row 544).

**ResolutionCheck rows on pin-export: NOT recorded.** `snap_state()` (harness line 419-422) snapshots only `refusals` and `attempts` (filtered by decision), destination `calls` and `snapshot()`. It never reads `resolution_checks`, `check_events`, `input_time_floors`, `decisions`, `holds`, `closeouts` or the raw store text. `grep -i resolutioncheck` over the harness: no match.

**Source facts bearing on that gap (git 739efe7):** `authorization_pin_export.py` line 14 docstring: "Bookkeeping: the existing resolution step journals a resolution check in the Control Plane record store, exactly as claim issuance does. No decision, grant, approval or policy record is created or changed."; line 175 calls `workflow._record_check(...)` *before* the `current != current_binding` comparison; `bounded.py` `record_resolution_check` appends a `ResolutionCheck` to `resolution_checks` and advances `input_time_floors`; `_resolve_journal` appends `CheckEvent`s when a runtime-authority profile exists (the pin fixture has one). `docs/authorization-pin-export.md` line 5: "read-only with respect to authorization state ... (The existing resolution step journals a resolution check in the Control Plane record store, as claim issuance does.)". Therefore the statement in VERDICTS ("pin-export ... never writes a row") / crosswalk A open-question Q2 ("writes no refusal row") is true **only for `EffectTimeRefusal`**; a ResolutionCheck (stage `claim`, reasons `[]` by the "binding changed" fallback) is by design written on this path and the original run neither observed nor ruled it out. Cause attribution is nonetheless supported: the reason text "binding changed" is the fallback at PE line 187 (`shown = ",".join(sorted(set(reasons))[:8]) or "binding changed"`), meaning `reasons` was empty and the refusal came from `current != current_binding` alone.

**Does any original check assert the documented non-authorizing outcome?** Partially. `export_not_active_no_payload` (PASS x22) asserts `raised == PermissionError` **or** (`state not in (None,"active")` **and** `payload is None`). It does **not** assert `state == "unknown"`, `terminal_status is None`, or any specific reason text; those exist only as OBSERVATION content in `pin_raw_outcome`. It would also accept `state: "terminal"` or a PermissionError. The check is discriminating (mutant D06-M03 "pin-export-compare-deleted": `export_not_active_no_payload` fails 22/22, `A20 pin_child_not_active_on_perturbed_member` fails; evidence `runs/A-mutants/D06-M03/ev/f3a_evidence.jsonl`). The reason-text and durable-row criteria are the strict CONTRACT-LITERAL ones that fail. **Important for re-scoring under the read-only reading:** crosswalk A open-questions Q2 states that even with `F3_PIN_DURABLE_REFUSAL_REQUIRED=0` the `reason_names_code` criterion "remains strict and will also fail"; so the raw rows must be re-judged, the recorded verdict flags cannot simply be reused.

**Failing check names (verbatim, from rows and stdout.txt):** `<member>:reason_names_code` and `<member>:durable_effect_time_refusal` for each of the 22 members; pytest assertion (stdout lines 117-1020): `AssertionError: A19_pin_export_refuses_per_perturbed_member[pin-export][<member>]: failed criteria ['<member>:reason_names_code', '<member>:durable_effect_time_refusal']`.

## 2. A06 legacy pin-export subcase `pin:cutoff0_idx0`

Test `test_A06_frozen_legacy_store_cutoff_semantics_and_legacy_report` (harness 764-822; pin branch 819-822: `run(0, ids[0])` then `judge_pin_refusal(chk,"pin:cutoff0_idx0",out)`). Store generated by the unchanged `b7eb11a` tree (rows 214-215 `pin:legacy_generator_ran_under_old_tree`, `acp` = `.../run/old-b7eb11a/src/...`, decisions `e06f6f0f-957e-46b4-9af6-936b2f086790`, `9f626b9e-b0ad-4fbd-a446-2812c6235550`; row 217 store has no member PASS; rows 218-219 approval_commitment/catalogue_digest recompute PASS).
- Row 220 `pin:cutoff1_idx0_active` PASS (positive control, payload recorded, state `active`).
- Row 221 `pin:cutoff0_idx0:export_not_active_no_payload` PASS, `raised: null, state: "unknown"`.
- Row 222 `pin:cutoff0_idx0:reason_names_code` **CHECK_FAIL**, `reason: "authority not supported but not positively terminal: binding changed"`.
- Row 223 `pin:cutoff0_idx0:durable_effect_time_refusal` **CHECK_FAIL**, `rows: []`.
- Row 224 `pin:cutoff0_idx0:destination_apply_never_called` PASS.
- Gaps vs A19: **no `pin_raw_outcome` OBSERVATION row** for this subcase. `payload: null` is only implied by the PASS of row 221 and the dest count only by the boolean PASS of row 224; `terminal_status`, `new_attempts`, ResolutionCheck rows not recorded. Failing pytest assertion (stdout line 75): `AssertionError: A06_frozen_legacy_store_cutoff_semantics: failed criteria ['pin:cutoff0_idx0:reason_names_code', 'pin:cutoff0_idx0:durable_effect_time_refusal']`.
- The f4 half of A06 (rows 195-213) passes: cutoff0/idx0 and cutoff1/idx1 refuse with `[["authorization_binding_changed"]]`, cutoff2/idx0 and cutoff1/idx0 execute and report `legacy`.
- No claim-route legacy test exists (crosswalk A finding F-2b: legacy below-cutoff decision possibly over-refused on the claim route when the workflow has no profile) -- not exercised.

## 3. A19 claim-issuance observations

`test_A19_claim_route_extra_path` (harness 1214-1242), `materialize_local_execution_claim` with `claim_id="harness-claim"`, `policy_binding`, `expected_consumer_id`, `expected_operation` on the pin fixture. Only **3 of the 22 members** were exercised:

| member | rows (control claimed / perturbed refused / names_code OBS) |
|---|---|
| `f4_scalars.status_max_age_seconds` | 806 (`claimed`, detail null) / 807 PASS / 808 OBS `names_code:false` |
| `scope.consumer_id` | 809 / 810 PASS / 811 OBS `names_code:false` |
| `families=none_declared` | 812 / 813 PASS / 814 OBS `names_code:false` |

Observed text in all three: `"PermissionError: authorization-critical inputs changed before claim issuance"` (source `local_authority_effect.py:458`; the alternative branch text "policy binding refused at claim issuance: ..." was not the one hit). Also A17 `A17_bad_types_claim_route_no_profile` rows 504-505 (F4 no-profile workflow; unperturbed claim -> `TenantLocalExecutionClaim`; float 30.0 member -> same PermissionError text).

Gaps/adverse points:
- 19 of 22 members never reach the claim route. `provision_local_execution_claim` (named in R3 as CONTRACT) is never called (`grep provision` in harness: no calls).
- Captured: outcome string and exception text only. **Not captured on claim routes: refusal rows, attempt rows, destination calls/snapshot, ResolutionCheck rows, check_events, floors.** The VERDICTS statement "local claim issuance and pin claim route perturbed => refuse, destination untouched (A17/A19 claim)" and "(claim) raises PermissionError ... without token or row" are therefore **not backed by any recorded check** (no `destination*` check exists in rows for these cases; verified). Source shows the claim path runs `workflow._record_check(...)` (LAE ~line 456) before raising, so a ResolutionCheck is written on the refusing claim.
- Refusal cause is not isolated: the message is generic for any `reasons`/binding inequality; there is no second *unperturbed* claim after the control claim on the same store as a negative-negative control (control claim and perturbed claim share `claim_id` and store; control claim itself journals a ResolutionCheck and may advance `input_time_floors`).
- Mutation support: D06-M04 (local-claim-issuance-compare-deleted) fails `perturbed_member_yields_no_claim` x3 and `float_equal_member_does_not_yield_claim` x1 (pre-AMEND-3 harness).

## 4. A19 execute durable-refusal cases (22)

`test_A19_pin_export_refuses_per_perturbed_member[<member>-execute]`: spans in the table column "execute rows" (6 rows each: control PASS, digest-change PASS, then 4 checks, all PASS: `<m>:raised_permission_error`, `<m>:one_durable_refusal_with_code`, `<m>:no_attempt_created`, `<m>:destination_apply_never_called`). 132 rows total, 0 failures. Recorded in the `raised_permission_error` row's `detail` for **every** member (verified programmatically): `raised: "PermissionError"`, `msg: "authorization-critical inputs changed before effect"`, `binding_status: "mismatch"` (candidate classifier; evidence only), `new_refusal_reasons: [["authorization_binding_changed"]]` (exactly one new `EffectTimeRefusal`), `new_refusal_vocab: ["runtime-authority-reasons/0.1"]`, `new_attempts: 0`, `dest_calls: 0`, `dest_unchanged: true`. Note: assertion semantics: "EffectTimeRefusal" = `doc.refusals` row for the decision; "no attempt row" = `len(attempts)` delta 0; "apply count 0" = `CountingDestination.calls` delta 0 plus unchanged snapshot. Not recorded for execute: ResolutionCheck rows (an execute-stage check is written by design), `reason_vocabulary_version` is recorded but not asserted. Same fixture caveat as pin-export (F4-only; family perturbations persisted-side).

## 5. A09 compatibility and `runs/C-compat`

A09 rows 235-264 (all PASS/OBS): `unchanged:{bounded,local_authority_effect,authorization_pin_export,reason_vocabulary,models}.py` (235-239) sha256 vs `F3_OLD_SRC` (`b7eb11a` src); `schemas_dir_found` (240); `schema_unchanged:*` x19 (241-259); `expected_to_differ:runtime_authority.py` and `registry_effective_policy.py` (260-261, `differs:true`, OBSERVATION only); catalogue_digest/approval_commitment recompute (262-263); `member_present_alongside_existing_keys` (264, keys list includes `effective_configuration`). I confirmed independently in git: blob ids of those five modules are identical between b7eb11a and 739efe7 (so **`authorization_pin_export.py` and `local_authority_effect.py` are unchanged from baseline: the pin-export/claim `binding changed` / `inputs changed before claim issuance` behaviours are baseline code paths; the refusal arises through the D-06 `_resolve` override in `registry_governed_lifecycle.py`**), and `schemas/` + `conformance/` have no diff b7eb11a..739efe7.

C-compat (`harness/compat_probe.py`, `--src` base/main; `diff-base-vs-main.txt`): `approval_commitment`, `commitment_selfcheck`, `model_json_schemas_sha256` (12), `schema_files_sha256` (20), `reason_vocabulary`, `profile_fixtures` (3), `effective_policy_snapshot.identity_digest` (`sha256:ed073694...`, empty `sha256:e8d63cca...`) all equal base vs main (re-verified). `protected_sha256` differs only for `runtime_authority.py` (`a4b4ac36...` -> `45a27db8...`). Expected diffs: 6 `registry_*` modules + `runtime_authority.py` changed, `effective_configuration_binding.py` and `registry_final3_governance.py` added, `FAMILY_TABLE`/`SCHEMA_REVISIONS` gained `anchor_deadline`, `observation_clock_tolerance`, `observation_max_age`. Both probes: python 3.11.18, `.err` files empty (`e3b0c442...`). Limits: the probe fixtures do not include a binding-bearing persisted decision (that is A09's pin case); `identity_digest` is of a fixed snapshot with the tables in each tree. A09/C-compat prove byte stability of listed surfaces, not behavioural equivalence of pin-export on perturbed input.

## 6. A24 (limits documented / no anti-rollback claim)

Rows 863-879. PASS: `doc_states_unsigned_store`, `doc_states_no_anti_rollback_guarantee`, `doc_states_cutoff_without_durable_provenance`, `doc_states_mixed_fleet`, `module_docstring_states_no_anti_rollback` (863-867); OBSERVATION `rollback_line` x4 (868-871: `docs/effective-configuration-binding.md:153`, `src/effective_configuration_binding.py:24`, `docs/final3-consumers.md:21`, `docs/d07-purpose-observation-anchor-correction.md:109`, all `looks_affirmative:false`); PASS `no_line_affirms_rollback_protection` `lines: []` (872); config-B refuse x4 PASS (873-876); LIMIT_CONFIRMED `rollback_to_A_revives_decision` (877, `revived:true`) + PASS 878; LIMIT_CONFIRMED forged-member accepted (879, `accepted:true`).
Limits of this evidence: the affirmative-claim detector is a regex heuristic (a line is "non-affirmative" if it contains any of `no|not|never|without|cannot|does not|do not|isn't|nor|neither|absent|held|separate held item`), scanning only 5 files (`docs/effective-configuration-binding.md`, `src/effective_configuration_binding.py`, `docs/final3-consumers.md`, `docs/d07-purpose-observation-anchor-correction.md`, `src/registry_governed_lifecycle.py`), not `docs/authorization-pin-export.md` or other docs; file hashes are not recorded in the rows (only quoted lines). A24 does not test the masked-host-change limit (that is `A02_masked_host_change_observation`, 2 rows; VERDICTS §4 itself says it is absent from the CP doc's limits section). A24 does not cover pin-export/claim limits at all.

## 7. The 23 failures (verbatim, from stdout.txt lines 1101-1124)

`FAILED ../../../work/A/test_f3a_independent.py::test_A06_frozen_legacy_store_cutoff_semantics_and_legacy_report` (assertion keys `pin:cutoff0_idx0:reason_names_code`, `pin:cutoff0_idx0:durable_effect_time_refusal`) and `FAILED ...::test_A19_pin_export_refuses_per_perturbed_member[<member>-pin-export]` for the 22 members listed in section 1, each with assertion keys `<member>:reason_names_code` and `<member>:durable_effect_time_refusal`. Summary line: `23 failed, 74 passed in 75.56s (0:01:15)`. `CHECK_FAIL` rows in jsonl: 46 = 23 x 2; no other case has a CHECK_FAIL. `CHECK_PASS` 785, `OBSERVATION` 66, `LIMIT_CONFIRMED` 4. No check named `export_not_active_no_payload` or `destination_apply_never_called` failed anywhere.

## 8. Discrepancies and evidence gaps (adversarial summary)

1. ResolutionCheck / CheckEvent / `input_time_floors` writes on pin-export and claim routes: not captured; per source they are written by design (PE docstring line 14; PE line 175; `bounded.py` `record_resolution_check`). Claims of "no write"/"read-only" by VERDICTS/crosswalk are only valid for `EffectTimeRefusal`, `attempts`, and destination in the pin-export cases. No whole-store before/after comparison (`raw_text`) was taken on pin-export or claim.
2. Authorization-state writes (decisions/holds/grants/closeouts) on pin-export/claim: not captured, not asserted; only refusals/attempts/destination.
3. Claim-issuance: 3/22 members, `materialize` only, generic message, no refusal/attempt/destination/ResolutionCheck capture. VERDICTS' "destination untouched" for claim paths has no recorded support. `provision_local_execution_claim` unexercised. Legacy-claim-route (F-2b) unexercised.
4. A06 pin subcase lacks a raw-outcome row (payload/terminal_status/attempts not recorded explicitly).
5. `export_not_active_no_payload` is permissive (any non-`active` state or any PermissionError); exact documented outcome (`state == "unknown"`) exists only as raw observation.
6. Reason text is the same for every member and does not name the code; reason-text and durable-row failures are by design of the strict criteria (R2, Q2); under a read-only/02-sec4-rule-2 reading the stored flags are not reusable without re-judging `reason_names_code` from the raw rows.
7. CP tree id: recorded only pre-run (`candidate-tree-before.txt`); equality to `739efe7^{tree}` verified now; post-run identity and `tests/`+`docs/` state at run time are asserted in VERDICTS but have no artifact. Environment versions (pydantic 2.14.2 etc.) are not in run artifacts.
8. The run covers Python 3.11.18 only (protocol §1 limitation), Registry pin `a40fe755`, F4-only on pin-export/claim.
9. Mutation evidence for D06-M01..M05, M09, M10, M12, M13 is against pre-AMEND-3 harness runs, not the final harness.
10. Execute-case `new_refusal_vocab` is `runtime-authority-reasons/0.1` on the pin fixture but `[null]` on the F4-dedicated fixture (A06 f4 rows 199/207, A24 873, A25 884+): not a defect, but the recorded refusal rows differ in `reason_vocabulary_version` by fixture.
11. No evidence inconsistency was found between `stdout.txt`, `f3a_evidence.jsonl` and VERDICTS for the headline counts (74 pass/23 fail, 22+1 failing cases, 22/22 execute pass) and MANIFEST hashes all verify.
