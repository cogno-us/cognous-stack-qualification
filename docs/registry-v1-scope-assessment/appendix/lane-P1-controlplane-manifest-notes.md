# Control Plane manifest notes

Merged from two source-reading passes (part A: F4, F5, F7, F8; part B: F3, F9, F10, F11). Pin: cognous-control-plane 7a4bcd40b3b49e61ff3c294dcca53b52f460b22c.

## Part A (F4, F5, F7, F8)
### Control Plane manifest notes, part A (families F4, F5, F7, F8)

Pin: cognous-control-plane 7a4bcd40b3b49e61ff3c294dcca53b52f460b22c (HEAD of the read-only checkout confirmed by `git rev-parse`); Runtime c5e97e87dd239c821b1b4a406a55dcd03c5bc61f used for cross-component facts only. 49 rows in `lane-P1-controlplane-manifest-a.jsonl`: F4 15, F5 12, F7 11, F8 11. By disposition: CONDITIONAL_EXTRACTION 11, UNRESOLVED 10, CODE_OWNED_GUARDRAIL 22, NOT_RELEVANT_TO_V1 6, DIRECT_EXTRACTION 0. No DIRECT row: every Control Plane value sits behind at least one of D4 (per-field direction unruled), W6-042, W8-014, D12 or D1, and none has been served by a registry consumer in the Control Plane (D2). Planning proposals only. No test was run; no result is restated as current.

Two rows (CP-F4-15, CP-F7-07) carry the Runtime pin because I read Runtime code for them (cross-component facts lane D lists under F4/F7 that no Runtime row covers). CP-F7-07 is in the Runtime component; the lead should assign both to a Runtime row set or accept them here.

## Verified directly at the Control Plane pin
- bounded.py: ObservationPolicy (410-415); BoundedAuthorizationWorkflow constructor (1263-1300, no validation of the five age/tolerance arguments); _fresh (2017-2024); _reconcile_observation (1890-1926); observe-failure path (1844-1873); _class_age_bound (1358-1372); record_age_extension (1376); _expired_before_dispatch (1410-1432); _resolve and _resolve_journal (2055-2125); _read_grant (2175-2200); _resolve_inputs freshness sites (2352-2557); _manifest_mismatches (2608-2711); dedupe/merge wiring (1489-1581); AttemptJoin write (1613-1626); record_resolution_check tolerance use (627-660).
- runtime_authority.py in full (ActionClass, EvidenceCriterion, RuntimeAuthorityProfile, approval_commitment, validate_evidence, validate_extensions).
- freshness.py (FreshnessProfile, Reaper, effective_age_bound, extension_defects), dedupe.py in full, operation_identity.py, merge.py (MergeProfile, funded check), holder_inventory.py, rule_revision.py (RuleRevisionProfile), reversibility.py check_class_members, manifest_validation.py in full, policy_gate.py, policy_config.py, demo_policies.py, replay.py (head), records.py start_run, cli_run.py (381-392, 505-512).
- Grep over src/, tests/, docs/, examples/, tools/ for callers of demo_policies, PolicyGate, PolicyConfig, default_action, catalogue_version.
- Runtime (cross-component, read only for these facts): control_plane_adapter.py 78-90 and 318-360; recovery_resolution.py 255-275; dedupe_destination.py 36-112; local_authority_effect.py 760-780; operation_admission.py 115-116.

## Taken from lane D or the crosswalk, not re-read
- All S02/R07 row text (W6-042, W6-004, W6-005, W8-014, W8-041, W8-042, W8-068, W3-062, W3-063, W9-027, W4-004, W4-014/015, W4-018, W4-022, W4-023, W9-007) and the D-ruling text. I used the ids only as lane D states them.
- Test ids and their NOT RUN / historical states; no test file under suites/ or the Control Plane tests/ was opened.
- AttemptCloseout.observed_state typing (bounded.py:449) and close_uncertain_attempts reachability (D12 special analysis).
- Runtime EvidenceProjection/commit-time behaviour beyond the lines listed above; Route B destination non-TTL guard.
- Scenarios whose enforcement is in components not cloned (cognous-governed-exchange).

## Discrepancies with lane D / the crosswalk
1. **F8 scope.** Lane D defines F8 as the demo helper lists only (demo_policies.py, uncalled). The Control Plane actually enforces tool allow/deny in the V1 path through the manifest `tools[]` (adapter binding, `allowed`) and `default_action` (bounded.py:2626-2634, 2663-2667), which lane D does not list under F8. They are rowed as CP-F8-08..10 (CODE_OWNED_GUARDRAIL: digest-pinned manifest artifact). Lane D also lists PolicyConfig.default_action only as an adjacent W4-014/015 note; PolicyConfig is a real JSON-file loader (policy_config.py:26-40) for tool lists, authority_required and default_action (CP-F8-04..06), and `default_action` is loaded but never read anywhere in src (CP-F8-05).
2. **PolicyGate is not on the V1 path.** `PolicyGate` has a single caller, `RunRecorder` (records.py:224). `BoundedAuthorizationWorkflow` and cli_run.py do not call it; the CLI builds a Frame after the decision (cli_run.py:380-392, CP-F8-11). So the F8 tool lists, PolicyConfig lists and PolicyGate rule chain affect only the legacy recorder path.
3. **F4 constructor bounds are unvalidated.** Lane D says a code floor is "needed". At the pin there is none and no type check: status/identity/mandate/approval age bounds and the workflow clock tolerance are plain keyword arguments stored as is (bounded.py:1271-1275, 1295-1299). Only ObservationPolicy and FreshnessProfile are pydantic-validated. So extractability clause (b) fails as-is for CP-F4-03..07 and a floor would be new code.
4. **Two tolerances and a Runtime tolerance of zero.** Lane D lists clock_tolerance_seconds once. There are two independent fields (ObservationPolicy.clock_tolerance_seconds, bounded.py:415/1922, and the workflow argument used by _fresh, input floors, the dispatch guard and claim issuance). The Runtime effect-time evidence check applies zero future tolerance (local_authority_effect.py:772-774 at the Runtime pin), so a larger CP tolerance does not reach the commit transaction.
5. **ActionClass.max_status_age_seconds has more than one consumer.** Lane D says it feeds one check (bounded.py:2398). It also drives the purpose-status age test with no tolerance (runtime_authority.py:341), the cached-purpose bound (bounded.py:2163), the dispatch deadline (2082-2088) and the Runtime AttemptJoin copy (1623). Also `ge=0` allows 0. Lane D calls the 2469 target "current"; it is the policy status read.
6. **F7 numeric fields never gate dispatch.** dedupe_ttl/provider_horizon/escalation_deadline feed dedupe_mode, classify and due_escalations (records and a mode label). The refusal gates (blocks_new_key, applied_under_other_effect) are activated by profile presence only (bounded.py:1566-1581). Lane D does not say this explicitly; it is why CP-F7-05 is a guardrail and CP-F7-01..03 are about escalation semantics (D12).
7. **F7 "replay-window defaults".** No Control Plane replay or dedup window exists beyond dedupe.py; replay.py only serialises a RunRecord (CP-F7-11, NOT_RELEVANT_TO_V1).
8. **Whole-profile approval binding.** Every RuntimeAuthorityProfile value (F4 freshness members, F5 ActionClass fields, F7 dedupe/merge) is hashed into approval_commitment (runtime_authority.py:186-194) and an approval with a different commitment fails closed (268-271). Lane D mentions the commitment under F5 only; I carry it in the cross-field cell of every profile row and as CP-F5-12.
9. **Line drift (cosmetic).** _resolve_journal class checks: unknown 2109-2110, irreversible/on_unreadable 2111-2112, resolver authenticity 2113-2114 (lane D: 2110, 2111, 2113). ObservationPolicy class spans 410-415.
10. **Evidence max_age_seconds** has two treatments of a missing key (decision gate: authority_limit_malformed, 2546; claim issuance: defaults to 0, local_authority_effect.py:306) and no sign check (`_exact_int`, bounded.py:104-106). Lane D does not record either.
11. **Crosswalk.** TC-L05-028 (PolicyConfig file) is `UNMAPPED`, yet lane D treats PolicyConfig only as F8-adjacent. C02 and D02 are mapped to F1a/F1b/F1c although the enforcement they name is the Control Plane manifest gate (as the Runtime notes also say); I attached them to the manifest rows CP-F8-08..10 as regression context only. D03 and H01 are mapped to F4/F5 but exercise fixed refusals, not a registry value.

## Scenarios mapped to F4, F5, F7 or F8 in the crosswalk with NO configurable field found
- A03, C17 (F4): enforcement is `_effect_time_changed_inputs` (input version comparison), not an age bound. No row.
- SL:fix2-probes:time-grammar-strictness (F4): parser strictness, enforcement `n/a`. No row.
- C05 (F5): UNKNOWN_BEHAVIORS vocabulary is code; attached to CP-F4-08 only.
- SL:v1-probes:authority-er031-governance-mapping (F5): document checks, no enforcement function. No row.
- D04, C08 (F7): enforcement is Runtime reconcile (`reconcile_claim`, `_unresolved`), not a Control Plane field. No row.
- SL:operation-identity:atomic-route-operation-key, SL:mvp-d2-route-b:operation-never-forgotten-selected-destination (F7): Runtime operation key / non-TTL guard; attached only to CP-F5-09 (atomic-route key) or not at all.
- SL:cognous-governed-exchange:delivery-time-expiry and :recovery-separation-and-observation-repair (F4): repo not cloned; no row.
- No canonical or suite-local scenario carries F8 in `registry_family`. F8 rows use NONE except where TC-L05-028, C02, D02, TC-L06-009/011 are attached as context.
- SL:v1-probes:xfail-* (F4) are strict-xfail known limits; attached to CP-F4-04 and CP-F4-08, not protection.

## Open items
- CP-F4-15 and CP-F7-07 need an owner (Runtime row set or accept here).
- Whether the legacy PolicyGate/RunRecorder/PolicyConfig path is a supported V1 surface (decides CP-F8-04; D1 scope question, not decided).
- Whether CP-F4-04..07 should be merged into one row per the lead's reading of D4 ("typed per-field composition"): kept separate because each has its own evaluator and refusal code.
- No qualification test for the identity or mandate bound was identified by me (suites/ not searched); no test exercises `irreversible_flag_mismatch` (lane D) or the Runtime 86400 s window.
- D12 source inconsistency (dedupe.py:122 versus 152 versus docstring 147-149) re-confirmed in code; whether another observed_state can ever be stored rests on lane D.
- Benefit and complexity cells are REASONED INFERENCE; no customer, revenue or adoption data used.

## Decision dependencies used
- D1 (S02 classification): CP-F4-08 (W6-004/W6-005 adjacent), CP-F4-12/13 (W8-041 candidate tier), CP-F8-04/05 (W4-014/015 adjacent); W4-022/W4-023, W4-004, W9-007, W8-068 mentioned, not decided.
- W6-042 and the 60-versus-300 relationship: CP-F4-01..07.
- W8-014: CP-F4-09, CP-F4-11, CP-F5-01..03 (and the whole-profile approval binding).
- D12 with W3-063/W9-027/W3-062: CP-F7-01..03, 05, 07, 08.
- D4 (typed per-field direction): named in basis for every CONDITIONAL/UNRESOLVED F4/F5/F7 row.
- D5, D6, D9 not touched by a Control Plane field in this set (CP-F8-10 notes D6/D9 for the lead).
- Respected, not decided: D2 (authenticated selection needed; the Control Plane is not a consumer), D3, D7 (mandatory participation design-only), D11, D13.

## Part B (F3, F9, F10, F11)
### Control Plane manifest notes, part b (F3, F9, F10, F11)

Pin: cognous-control-plane 7a4bcd40b3b49e61ff3c294dcca53b52f460b22c (confirmed `git rev-parse HEAD`, clean tree). Runtime cross-checks at c5e97e87dd239c821b1b4a406a55dcd03c5bc61f (HEAD confirmed). 23 rows: 13 CODE_OWNED_GUARDRAIL, 5 CONDITIONAL_EXTRACTION, 5 NOT_RELEVANT_TO_V1, 0 DIRECT, 0 UNRESOLVED. Planning proposals only; no test was run and no test outcome is restated as current. Merge validator printed OK (47 rows with the Runtime half).

## Verified directly at the pin
- F3: cli_run.py:61, 91, 162-172, 225-254, 444-447, 510; strict_json.py:21-33, 87-95, 117; holder_inventory.py:35-51; runtime_authority.py:121; operation_identity.py:50-51; bounded.py:2063-2067, 2085, 1283; freshness.py:56-62, 295, 309, 312-324. Grep of all src/agent_control_plane for max_length, MAX_, read_bytes/read_text/json.loads/strict_loads, RecursionError, setrecursionlimit, seconds/timeout/window/threshold literals.
- F9: all five `max_length=128` sites opened (listed below); bounded.py:187-196 EvidenceStatus, 2275-2282 and 2527-2534 tenant comparisons; Runtime safe_executor.py:314-321.
- F10: reason_vocabulary.py:21-58, 126-155; callers searched (tests only, no src caller).
- F11: models.py:420-451, redaction.py whole file, cli.py:76-80 and 107-114 and 150-170, manifest_validation.py:147-160. CP-local test names under tests/test_redaction*.py were listed, not read or run.

## F9 site count (lane D says five: confirmed)
| # | Site | Model | Agrees with Runtime 128 (safe_executor.py:319) |
|---|---|---|---|
| 1 | bounded.py:154 | TenantRuntimeProposal | yes |
| 2 | bounded.py:297 | TenantAuthorizationBinding | yes |
| 3 | local_authority_effect.py:45 | TenantApprovalProjection | yes |
| 4 | local_authority_effect.py:56 | TenantPolicyProjection | yes |
| 5 | local_authority_effect.py:127 | TenantLocalExecutionClaim | yes |
All five are `Field(min_length=1, max_length=128)`; with the Runtime copy, six sites carry the literal. Note: the Runtime check also requires exact `type is str` and permits `tenant_id is None`; CP uses pydantic default coercion (not tested by me). Also: bounded.py:196 `EvidenceStatus.tenant_id: str | None` has NO length bound (CP-F9-06). Lane D's "all tenant-bearing CP models are bounded" reading would be wrong; the count of 128-literal sites is still five.

## Taken from lane D / crosswalk, not re-read
S02/R07/D-ruling text, W-id classifications (W1-007/008, W1-027, W6-008, W5-002, W9-002, W8-041, W2-082), crosswalk statuses (D06 INCONCLUSIVE historical; A04, TC-L06-028, TC-L08-033, TC-L09-019 NOT RUN; SL claims PASS_RECORDED only at historical pins or COLLECTED_ONLY), the contents of the qualification test files (names only), Runtime-side facts (from the Runtime half).

## Discrepancies with lane D / crosswalk
1. Lane D files strict_json `MAX_TEXT=200` under size/depth/timeout budgets. At the pin it only truncates diagnostic text (`safe_text`, strict_json.py:24-33); it gates nothing. Rowed as a code-owned guardrail (the escaping is the security part). Also there are call-site literals 40/60/80 that lane D did not list.
2. Lane D cites only cli_run input check 169-170. The same constant is enforced at three places (169-170, 238, 241/244-245), and ONLY `acp run` has a size ceiling: cli.py:88, persistence.py:104, policy_config.py:31, witness.py:77/179 and replay.py:73 read unbounded (CP-F3-02). No CP depth constant exists; nesting relies on the interpreter recursion limit with RecursionError caught (CP-F3-05). The crosswalk SL claim "depth still limited" (fix2-probes replay-fold-and-scan-bounds) targets a component whose repo is not cloned (crosswalk text), so it is attached to CP-F3-05 only as context.
3. Lane D F9 does not mention that the sixth tenant-bearing CP field (EvidenceStatus.tenant_id, bounded.py:196) is unbounded.
4. Crosswalk A04 text "tenant length <=1" is a known typo; code is `<=128` (already noted in the Runtime half). The crosswalk records TC-L09-019 existing_configuration_mechanism as naming the 128 literal, but its registry_family is NONE; TC-L17-028 names F10 thresholds in the same column while registry_family is NONE; C13 and TC-L06-028 text reference F11 (C13 family NONE). I attached TC-L09-019 to CP-F9-06, TC-L17-028 to CP-F10-01 and C13 to CP-F11-07 as context only.
5. Lane D lists the FreshnessProfile fields (including lease_acquire_timeout_seconds, freshness.py:62) under F4. I wrote CP-F3-07 as the F3 time-bound cross-reference because the task names time bounds; the F4 owner's row governs if rows conflict.
6. Lane D says RedactionConfig keep_fingerprints is "never set" by the CLI: confirmed (cli.py:107-114). Also confirmed: `redact_tool_execution_result` (redaction.py:38-48) ignores `redact_payloads` and `.result`; only `.error` under redact_targets. Lane D does not mention this coverage gap (CP-F11-07).
7. Lane D lists `redact_payloads (True)` as a configurable field. It is, but the CLI forces True and the default is True, so a registry could only matter for programmatic callers who pass False.
8. Default replacement "[REDACTED]" exists as two copies (models.py:440 and cli.py:80).

## Scenarios mapped to these families with NO configurable CP field found
- D06 (F3): CP-owned pieces are literals/implicit; attached to CODE_OWNED/NOT_RELEVANT rows only (CP-F3-01, 02, 04, 05). Which D06 cases exercise CP bounds (malformed_proposal_model_boundary_flood, unauthenticated_control_plane_flood) was not read.
- A04, SL:cognous-execution-runtime:tenant-isolation-at-effect-time (F9): isolation is equality; only code-owned length rows.
- SL:v1-probes:xfail-refusal_trend_report_names_unmapped_code (F10), TC-L17-028 (mechanism text only): NOT_RELEVANT_TO_V1.
- C13 (F11 by text, family NONE): attached to CP-F11-07 only.
- TC-L08-033, SL:fix2-probes:replay-fold-and-scan-bounds: context only.
- Mapped but intentionally not rowed here (other owner): F4 age bounds and clock tolerance (bounded.py:1271-1275, cli_run.py:510 ObservationPolicy 300/5), FreshnessProfile.reaper_interval_seconds (W8-041).

## Open items
- No in-tree CP caller of `refusal_trends`/`measured_arity`: confirm no external host relies on them before final NOT_RELEVANT classification.
- Whether lowering a tenant bound would make stored claim/projection rows unreadable on reload (CP-F9-01..05): not verified.
- No test of MAX_INPUT_BYTES, MAX_TEXT, the 128 bound, or the F10 default thresholds was found in CP-local tests or the qualification suites (grep; may miss indirect coverage).
- F11 category set: R07 "closed ordered category set" does not exist in code; redaction is applied by whoever calls it (nothing forces a call), so a registry cannot enforce redaction on export without a mandatory call site (D7 design-only).
- Whether the lease timeout (CP-F3-07) has an S02 W-row: not identified.

## Decision dependencies used
D1 (CP-F3-07 classification; CP-F11-01..04 confidentiality tier, W9-002 candidate), D4 (typed per-field composition respected; scalar "minimum below a hard cap with floor" treated as R07 PROPOSAL, not ruling; F9 minor), D2/D3/D7/D11/D13 respected (no DIRECT rows; D7 mandatory-participation noted as design-only for F11). D5, D6, D9, D12 and W8-014 not touched by any row.
