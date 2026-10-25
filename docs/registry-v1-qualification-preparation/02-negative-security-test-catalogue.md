# 02. Negative security test catalogue (Lane B)

**Status: PREPARATION ONLY. This is not qualification.** Nothing here has been run. No V1 implementation exists (no `EXT-S1-2` successor, no `EXT-S4-2` Runtime guard, no `EXT-S4-4` claim binding), so every control is `NOT_RUN` and several have nothing to execute yet. No control in this document records a result, and no control is credited as protection of any current or future build. The independent Tier 1 qualification lead is not designated; Copilot review is technical review, not qualification. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.

**Synthetic fixtures are defined separately by the lead.** Each control names a placeholder `FX-B-nnn` and an abstract description of the synthetic input. The ids are per control; the lead may merge fixtures that turn out to be identical. All keys, signatures, ids and digests must be synthetic, never reused real material, with no network, paid or credentialed execution.

Machine-readable rows: [`data/negative-controls.jsonl`](data/negative-controls.jsonl) (138 rows, one JSON object per line). This page is the human catalogue; the JSONL is authoritative for field values.

## 1. Scope and boundaries

- V1 scope (operator-approved, not reopened): eight configurable fields (Runtime: `allowed_actions`, `allowed_adapters`, `allowed_units`, `allowed_institutions`, `allowed_authority_domains`; Control Plane: `status_max_age_seconds`, `approval_max_age_seconds`, `ActionClass.max_status_age_seconds`). Execution boundary is **atomic Route B only**.
- `max_amount` is excluded and QG-02 stays INACTIVE: **no control targets `max_amount`, and no row is tagged QG-02.** (Existing evaluator behaviour for `max_amount` is untouched and not characterised here.)
- Route A is out of V1. The Route A controls assert that Route A is **not** credited as protected; they are labelling and disclosure controls, not protection claims.
- Gates QG-01, QG-03..QG-13 are tagged where they bear; QG-14 appears only on the custody control that must be recorded as `not performed`.
- Paths prefixed `p1/` below mean `cognous-ocs-registry/docs/p1-extraction-plan/`. Source references `file:line @c5e97e87` / `@7a4bcd40` are the Runtime and Control Plane pins, used for characterisation only.

## 2. Summary counts

| Measure | Count |
|---|---|
| Controls | 138 |
| `PREPARED` (expectation derivable from a contract, ruling or pinned source) | 118 |
| `BLOCKED_ON_CONTRACT` (named open decision) | 20 |
| Scope RUNTIME / REGISTRY / CONTROL_PLANE / CROSS | 67 / 29 / 26 / 16 |
| Basis type CONTRACT / RULING / SOURCE_CHARACTERIZATION / INVENTORY | 121 / 3 / 14 / 0 |
| Race or repeat controls | 12 |
| Distinct existing registry codes asserted (of 48 mapped: 46 `r08-v1` plus 2 v2-only) | 29 |
| Distinct `NEW_CODE_PROPOSED` names | 35 |

The count is above the 80-130 planning range because several classes (freshness grids, deny-all, boundary pairs) are kept as separate rows where the cause or the field differs. Rows that would merely re-word another were removed.

Gate coverage (a row may carry several gates): QG-01 6; QG-03 20; QG-04 20; QG-05 34; QG-06 32; QG-07 8; QG-08 47; QG-09 44; QG-10 20; QG-11 7; QG-12 50; QG-13 20; QG-14 1.

## 3. Exact-cause preservation rule

Every control names **one** expected cause, in `expected_exact_cause`. The rule binds the lead, the oracle author and the runner:

1. **Cause is a structured value, never message text.** The assertion compares `detail.registry_code` (registry codes), the Control Plane `reasons` entry, or the Runtime `reason_code`/`failure_class`. It never parses `PermissionError` or `registry_detail_text` (OPEN-Q3). A control whose assertion needs text parsing is mis-written. (Exact evaluator reason texts such as 'local unit restriction' appear only as retained evidence for the evaluator-denial controls, per QG-01; they never select an outcome.)
2. **Right disposition with the wrong or missing cause is an unmet expectation.** `REFUSE`, `HOLD` or `DENY` with no effect is necessary but not sufficient. The outcome map's rule applies: a path that cannot carry the cause is `BLOCKED`, not mapped.
3. **Distinct causes are never collapsed.** Several registry codes share one Runtime `reason_code` (`registry_policy_unavailable`, `registry_input_rejected`, `registry_binding_rejected`, `registry_contract_unsupported`) and the commit path shares `current_authority_rejected` with grant and approval failures. A matching `reason_code` is therefore **not** cause equality; `detail.registry_code` is the carrier.
4. **Commit-time registry causes** are asserted only if a structured `registry_code` reaches the persisted failure row. If the candidate carries only the shared `current_authority_rejected` text, the expected evidence is `UNMAPPED_CAUSE_LOSS` with the loss disclosed, never credit as the registry code (outcome map `cause_requirement`, OPEN-Q3). NC rows for commit-time causes carry that clause in `expected_runtime_mapping`.
5. **Registry preconstruction deny-all is not an evaluator denial** (OPEN-Q6): `registry_deny_all` (decision kind `applied_deny_all`, no policy constructed) versus `local_policy_rejected` with the evaluator's own text. Both paths have their own controls and neither may be relabelled as the other.
6. **Stale epoch is a specific REFUSE** (`selection_epoch_stale`); **HOLD** is reserved for authority state that is genuinely indeterminate with effects prohibited (`authority_state_*`, restore-unbaselined). Neither is a retryable success. Equal-epoch activation cause is unresolved and blocked (section 6).
7. **Optional-participation failures keep their own code** with `applied=false` (`overlay_not_applied`), are never recorded as `selection_withdrawn`, and are never reported as enforcement.
8. **`NEW_CODE_PROPOSED` names are placeholders** for causes the plan describes without a literal code. If the ADR chooses different names the control is updated, but two causes that are distinct here must stay distinct. A renaming that merges two proposals is a contract change to be recorded, not a drift to absorb.

### Outcome vocabulary used in `expected_outcome`

| Value | Meaning |
|---|---|
| REFUSE / HOLD / DENY / RETRY | Registry outcome vocabulary of `ld02-outcome-map.json`; for an existing registry code the value is copied from `conceptual_outcome_required`. Required participation: no policy returned, no dispatch. |
| OVERLAY_NOT_APPLIED | Optional participation only: caller policy returned unchanged, `applied=false`, `registry_code` retained; not a denial and not protection. |
| NOT_PROTECTED_ASSERTED / KNOWN_LIMIT_NOT_PROTECTED_ASSERTED | The control passes only when the run is labelled as unprotected or a known limit. Never counted as PASS or as protection. |
| ALLOW_PAIR_CONTROL | Paired positive at a boundary, proving the refusing check does not over-refuse. Not a security claim. |
| NO_EFFECT_COMMITTED, NO_ROLLBACK_AND_LATER_REFUSED, EFFECT_COMMITTED_THEN_REVOKED, EXACTLY_ONE_ORDERING_PER_RUN, UNRESOLVED_NOT_RETRY_ELIGIBLE, NO_EXTENSION, NARROW_ONLY, DERIVATION_EXACT, ABSENT_CAPABILITY_ASSERTED | Control-specific invariants stated in `expected_exact_cause`. |
| UNSPECIFIED, HOLD_OR_REFUSE_PER_ADR | Only on `BLOCKED_ON_CONTRACT` rows where the contract has not fixed the outcome. |

## 4. Class-by-class catalogue

Columns: id, title, expected outcome, expected exact cause (existing code shown as `registry_code=`; new names flagged), status. Full attack steps, fixtures, `must_not`, evidence and basis are in the JSONL.

| Class | Controls | PREPARED | BLOCKED |
|---|---|---|---|
| Forged selection | 12 | 11 | 1 |
| Hostile input | 3 | 3 | 0 |
| Substituted policy digest and identity | 3 | 1 | 2 |
| Mismatched claim identity | 12 | 10 | 2 |
| Expired selection | 9 | 7 | 2 |
| Revoked selection, issuer and key | 7 | 5 | 2 |
| Concurrent revocation | 4 | 4 | 0 |
| Required-policy absence | 6 | 6 | 0 |
| scope_required ratchet | 4 | 4 | 0 |
| Epoch downgrade | 6 | 5 | 1 |
| Stale trust-snapshot version | 4 | 4 | 0 |
| Stale approval revival and approval/profile mismatch | 6 | 4 | 2 |
| Restore and rollback | 5 | 4 | 1 |
| Missing or corrupted durable state | 8 | 7 | 1 |
| Registry deny-all versus evaluator denial (OPEN-Q6) | 7 | 6 | 1 |
| Confused deputy between families | 3 | 3 | 0 |
| String-based decision attacks (OPEN-Q3) | 4 | 3 | 1 |
| Sync manufacturing authorization or reversing revocation (A2) | 5 | 5 | 0 |
| Invalid optional selection masquerading as withdrawal | 5 | 4 | 1 |
| Outage-extension widening (R6) | 4 | 3 | 1 |
| Invalid freshness inputs | 11 | 10 | 1 |
| Narrowed freshness boundary | 3 | 3 | 0 |
| Route A bypass (out of V1) | 3 | 2 | 1 |
| Evidence and reachability | 2 | 2 | 0 |
| Transaction integrity | 2 | 2 | 0 |
| **Total** | **138** | **118** | **20** |

### 4.1 Forged selection (12)

Bad signature, wrong key (untrusted and unauthorised), re-digested statement and record, unknown family, dropped and smuggled fields, wrong participation, conflict, v1/v2 replay. Attack-class slug: `forged_selection`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-001 | Selection statement with one flipped signature bit | HOLD | registry_code=signature_invalid | PREPARED |
| NC-002 | Statement altered and statement digest recomputed, signature stale | HOLD | registry_code=signature_invalid | PREPARED |
| NC-003 | Valid signature by a trusted key that holds no authority for this consumer, scope and operation | HOLD | registry_code=issuer_not_authorized | PREPARED |
| NC-004 | Valid self-signature by a key absent from the trust snapshot | HOLD | registry_code=issuer_untrusted | PREPARED |
| NC-005 | Record altered and record digest recomputed; selection pins the original record digest | REFUSE | registry_code=record_digest_mismatch | PREPARED |
| NC-006 | Record of an unknown family | REFUSE | registry_code=family_unsupported | PREPARED |
| NC-007 | Record with a required field dropped (allowed_units absent) | REFUSE | registry_code=field_missing | PREPARED |
| NC-008 | Record smuggling an out-of-profile field (target prefixes wildcard) | REFUSE | registry_code=field_unknown | PREPARED |
| NC-009 | Optional-participation selection presented for a required operation | HOLD | registry_code=participation_mismatch | PREPARED |
| NC-010 | Two effective selections for one scope at the same epoch without supersession | HOLD | registry_code=selection_conflict | PREPARED |
| NC-011 | Higher epoch without an explicit supersession link | HOLD | registry_code=selection_conflict | PREPARED |
| NC-012 | v1-signed statement replayed as an r08-v2 statement | HOLD_OR_REFUSE_PER_ADR | NEW_CODE_PROPOSED: v2_domain_separation_refusal (name open; candidates signature_invalid, contract_unsupported) | BLOCKED |

### 4.2 Hostile input (3)

Duplicate key, float/non-finite number, oversize document. Attack-class slug: `hostile_input`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-013 | Duplicate JSON key smuggles last-wins value | REFUSE | registry_code=json_duplicate_key | PREPARED |
| NC-014 | Float or non-finite number in a signed document | REFUSE | registry_code=json_number_unsupported | PREPARED |
| NC-015 | Oversize input beyond MAX_DOCUMENT_BYTES | REFUSE | registry_code=input_too_large | PREPARED |

### 4.3 Substituted policy digest and identity (3)

Policy digest swapped under the lock; substituted or omitted identity in evidence. Attack-class slug: `policy_digest_substitution`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-016 | Policy digest in the claim substituted with a broader profile's digest, same selection id | REFUSE | registry_code=digest_mismatch | PREPARED |
| NC-017 | Evidence pack substitutes the governing policy identity | REFUSE | NEW_CODE_PROPOSED: evidence_policy_identity_substituted | BLOCKED |
| NC-018 | Evidence pack omits the policy identity entirely | REFUSE | NEW_CODE_PROPOSED: evidence_policy_identity_missing | BLOCKED |

### 4.4 Mismatched claim identity (12)

Claim-carried binding for another tenant, record version or epoch; valid binding swapped for another valid one; missing binding (required vs optional); evaluator build and trust-snapshot fingerprint substituted; executor-supplied identity; seeding hazard; expiry clamp. Attack-class slug: `claim_identity_mismatch`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-019 | Claim carries a binding for another tenant | HOLD | registry_code=selection_scope_mismatch | PREPARED |
| NC-020 | Claim carries a binding pinning another record version | REFUSE | registry_code=record_identity_mismatch | PREPARED |
| NC-021 | Claim carries a newer epoch than the trusted row | REFUSE | NEW_CODE_PROPOSED: claim_epoch_ahead_of_row | BLOCKED |
| NC-022 | Valid binding swapped for another valid binding, commitment not recomputed | REFUSE | NEW_CODE_PROPOSED: claim_commitment_mismatch | PREPARED |
| NC-023 | Valid binding swapped for another valid binding, commitment recomputed by the claim holder | REFUSE | NEW_CODE_PROPOSED: activation_row_identity_mismatch | PREPARED |
| NC-024 | Required scope, claim carries no binding | REFUSE | NEW_CODE_PROPOSED: claim_policy_binding_missing | PREPARED |
| NC-025 | Optional scope, claim carries no binding: not protected, must be labelled | NOT_PROTECTED_ASSERTED | decision_kind=overlay_not_applied with registry_code and applied=false; evidence must not claim enforcement (label proposed: overlay_not_applied_no... | PREPARED |
| NC-026 | Evaluator build identity substituted | REFUSE | registry_code=evaluator_mismatch | PREPARED |
| NC-027 | Trust-snapshot fingerprint substituted | REFUSE | NEW_CODE_PROPOSED: trust_snapshot_fingerprint_mismatch | PREPARED |
| NC-028 | Executor-supplied identity string with no claim-carried binding | REFUSE | NEW_CODE_PROPOSED: executor_supplied_identity_not_authority | PREPARED |
| NC-029 | Self-asserted claim cannot create the activation row | REFUSE | NEW_CODE_PROPOSED: activation_unavailable | PREPARED |
| NC-030 | Claim expiry extended beyond the selection validity (clamp cannot extend) | NO_EXTENSION | NEW_CODE_PROPOSED: claim_expiry_clamp_rule | BLOCKED |

### 4.5 Expired selection (9)

Before check, between check and commit, lock-time boundary [valid_from, valid_until), check-time versus lock-time clock, time source loss, snapshot expiry. Attack-class slug: `expiry`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-031 | Selection already expired at the gate | HOLD | registry_code=selection_expired | PREPARED |
| NC-032 | Selection expires between check and commit | HOLD | registry_code=selection_expired | PREPARED |
| NC-033 | Lock-time clock equals valid_until exactly (half-open interval) | HOLD | registry_code=selection_expired | PREPARED |
| NC-034 | Lock-time clock one tick before valid_until: expiry must not fire (pair control) | ALLOW_PAIR_CONTROL | no expiry refusal; effect and claim and budget commit together | PREPARED |
| NC-035 | Check-time clock used instead of lock-time clock | HOLD | registry_code=selection_expired | PREPARED |
| NC-036 | No trusted current time at the lock | HOLD | registry_code=time_unavailable | PREPARED |
| NC-037 | Wall clock set backwards to un-expire a selection | HOLD_OR_REFUSE_PER_ADR | NEW_CODE_PROPOSED: clock_rollback_cause_unspecified | BLOCKED |
| NC-038 | Trust snapshot past valid_until | HOLD | registry_code=trust_snapshot_expired | PREPARED |
| NC-039 | Trust snapshot expires between check and commit | UNSPECIFIED | NEW_CODE_PROPOSED: snapshot_expiry_at_commit_unspecified | BLOCKED |

### 4.6 Revoked selection, issuer and key (7)

Revocation before the check, between check and lock, after commit; issuer and key revocation; revocation visible only in Runtime state. Attack-class slug: `revocation`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-040 | Selection revoked before the check | HOLD | registry_code=selection_revoked | PREPARED |
| NC-041 | Issuer signing key revoked in the trust snapshot | HOLD | registry_code=issuer_key_revoked | PREPARED |
| NC-042 | Selection revoked between check and lock | HOLD | registry_code=selection_revoked | PREPARED |
| NC-043 | Revocation visible only in Runtime state while the binding still verifies | HOLD | registry_code=selection_revoked | PREPARED |
| NC-044 | Issuer key revoked between check and commit | HOLD | registry_code=issuer_key_revoked | BLOCKED |
| NC-045 | Issuer revoked between check and commit | HOLD | registry_code=issuer_untrusted | BLOCKED |
| NC-046 | Revocation after the effect committed: no rollback of the committed effect | NO_ROLLBACK_AND_LATER_REFUSED | registry_code=selection_revoked | PREPARED |

### 4.7 Concurrent revocation (4)

Both lock orders by barrier, free race with repetitions, lost acknowledgement then revocation. Attack-class slug: `concurrent_revocation`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-047 | Order A: revocation transaction commits before the effect transaction takes the lock | HOLD | registry_code=selection_revoked | PREPARED |
| NC-048 | Order B: effect transaction holds the lock first, revocation waits | EFFECT_COMMITTED_THEN_REVOKED | effect committed once with receipt checked_at < revocation row time; subsequent attempts refuse with selection_revoked | PREPARED |
| NC-049 | Unsynchronised race between revoker and effect transaction | EXACTLY_ONE_ORDERING_PER_RUN | each run is either (refused, detail.registry_code=selection_revoked, no effect) or (effect committed strictly before revocation, receipt ordering p... | PREPARED |
| NC-050 | Lost acknowledgement then revocation: unresolved and not retry-eligible | UNRESOLVED_NOT_RETRY_ELIGIBLE | existing Runtime reason_code dispatch_outcome_unresolved / acknowledgement_unavailable; no registry code substitutes for it | PREPARED |

### 4.8 Required-policy absence (6)

Unavailable, unselected, no trust root, no verifier, withdrawn, selected-not-activated, restart before first sync. Attack-class slug: `required_policy_absence`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-051 | Registry unreachable: host supplies no selection | HOLD | registry_code=selection_missing | PREPARED |
| NC-052 | No trust root supplied | HOLD | registry_code=trust_snapshot_missing | PREPARED |
| NC-053 | No signature verifier available (digest match is not authentication) | HOLD | registry_code=verifier_unavailable | PREPARED |
| NC-054 | Required scope whose selection was withdrawn | HOLD | registry_code=selection_withdrawn | PREPARED |
| NC-055 | Selected but never activated by the consumer | REFUSE | NEW_CODE_PROPOSED: activation_unavailable | PREPARED |
| NC-056 | Restart before the first sync: required scope refuses | REFUSE | NEW_CODE_PROPOSED: activation_unavailable | PREPARED |

### 4.9 scope_required ratchet (4)

Not downgradable by call, by optional selection, by management request; survives restart. Attack-class slug: `scope_required_ratchet`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-057 | Per-call 'optional' presented for a ratcheted scope | HOLD | registry_code=participation_mismatch | PREPARED |
| NC-058 | Optional selection statement delivered for a ratcheted scope | HOLD | registry_code=participation_mismatch | PREPARED |
| NC-059 | Management request to clear scope_required has no writer | REFUSE | NEW_CODE_PROPOSED: scope_required_clear_unsupported | PREPARED |
| NC-060 | Ratchet survives restart | HOLD | registry_code=participation_mismatch | PREPARED |

### 4.10 Epoch downgrade (6)

Older and equal epoch at activation, bump and swap between check and commit, immediate retry, indeterminate state as the only HOLD. Attack-class slug: `epoch_downgrade`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-061 | Activation at an older epoch than the high-water | REFUSE | registry_code=selection_epoch_stale | PREPARED |
| NC-062 | Activation at an equal epoch with different content | REFUSE | NEW_CODE_PROPOSED: activation_epoch_not_greater | BLOCKED |
| NC-063 | Epoch bumped between check and commit | REFUSE | registry_code=selection_epoch_stale | PREPARED |
| NC-064 | Epoch swap: a different selection becomes the head between check and commit | REFUSE | registry_code=selection_epoch_stale | PREPARED |
| NC-065 | Immediate retry of a stale-epoch refusal without a new authority artifact | REFUSE | registry_code=selection_epoch_stale | PREPARED |
| NC-066 | Authority state genuinely indeterminate: HOLD, not stale and not success | HOLD | NEW_CODE_PROPOSED: authority_state_indeterminate | PREPARED |

### 4.11 Stale trust-snapshot version (4)

Below floor, revocation rollback, equal version with different fingerprint, invalid floor. Attack-class slug: `trust_snapshot_version`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-067 | Trust snapshot version below the enforcer-supplied floor | HOLD | registry_code=trust_snapshot_version_stale | PREPARED |
| NC-068 | Older snapshot that omits a prior revocation (revocation rollback) | HOLD | registry_code=trust_snapshot_version_stale | PREPARED |
| NC-069 | Equal snapshot version with a different fingerprint | REFUSE | NEW_CODE_PROPOSED: trust_snapshot_fingerprint_conflict | PREPARED |
| NC-070 | Invalid floor input (non-int, bool, zero, negative) | REFUSE | NEW_CODE_PROPOSED: trust_snapshot_floor_invalid | PREPARED |

### 4.12 Stale approval revival and approval/profile mismatch (6)

Caller-profile approval against narrowed profile, P1 approval after withdrawal, P0 revival, no approval-history migration, cross-component disagreement. Attack-class slug: `stale_approval_revival`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-071 | Approval issued under the caller profile, evaluated against the narrowed profile | HOLD | reason runtime_authority_approval_mismatch (existing Control Plane reason; decision result=hold) | PREPARED |
| NC-072 | Approval bound to narrowed P1 fails after the narrowing is withdrawn | HOLD | reason runtime_authority_approval_mismatch (commitment P1 vs P0) | PREPARED |
| NC-073 | Older P0 approval after narrowing (P1) was applied and then withdrawn: must not be revived | UNSPECIFIED | NEW_CODE_PROPOSED: approval_revival_unspecified | BLOCKED |
| NC-074 | No generalized approval-history migration capability exists | ABSENT_CAPABILITY_ASSERTED | no migration path; A0 stays runtime_authority_approval_mismatch under P1; only a newly issued approval validates | PREPARED |
| NC-075 | Approval valid but the grant derives from another profile | HOLD_OR_REFUSE_PER_ADR | NEW_CODE_PROPOSED: grant_profile_disagreement | BLOCKED |
| NC-076 | Control Plane and Runtime profile disagreement never takes the broader side | REFUSE | NEW_CODE_PROPOSED: cross_component_policy_disagreement | PREPARED |

### 4.13 Restore and rollback (5)

Restored high-water store, consistent rollback (known limit), restore must not reverse revocation or downgrade scope_required, re-baseline. Attack-class slug: `restore_rollback`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-077 | Restored older high-water store with an external floor: fail closed until re-baselined | HOLD | NEW_CODE_PROPOSED: authority_state_restore_unbaselined | PREPARED |
| NC-078 | Revoked set and high-water roll back together with no external anchor: undetected, disclosed limit | KNOWN_LIMIT_NOT_PROTECTED_ASSERTED | no detection expected; evidence must carry the known-limit label; never counted PASS or protection | PREPARED |
| NC-079 | Restore must not reverse a revocation | HOLD | registry_code=selection_revoked | PREPARED |
| NC-080 | Restore must not downgrade scope_required | HOLD | NEW_CODE_PROPOSED: authority_state_restore_unbaselined | PREPARED |
| NC-081 | Re-baseline attempted by an unauthenticated local call or from a claim | REFUSE | NEW_CODE_PROPOSED: rebaseline_unauthenticated | BLOCKED |

### 4.14 Missing or corrupted durable state (8)

Missing, truncated and corrupted selection-state, revoked-set and activation-log tables; trust-snapshot file truncation and custody. Attack-class slug: `durable_state_loss`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-082 | selection-state table missing | HOLD | NEW_CODE_PROPOSED: authority_state_unavailable | PREPARED |
| NC-083 | revoked-set table missing | HOLD | NEW_CODE_PROPOSED: authority_state_unavailable | PREPARED |
| NC-084 | activation-log table missing | HOLD | NEW_CODE_PROPOSED: authority_state_unavailable | PREPARED |
| NC-085 | revoked-set row deleted while the log shows the revoke entry | HOLD | NEW_CODE_PROPOSED: authority_state_inconsistent | PREPARED |
| NC-086 | Activation log tail truncated | HOLD | NEW_CODE_PROPOSED: authority_state_corrupt | PREPARED |
| NC-087 | Epoch lowered directly in the state row | HOLD | NEW_CODE_PROPOSED: authority_state_corrupt | PREPARED |
| NC-088 | Trust snapshot file truncated | HOLD | registry_code=trust_snapshot_invalid | PREPARED |
| NC-089 | Trust snapshot file is a symlink, FIFO or foreign-owner file | HOLD | NEW_CODE_PROPOSED: snapshot_custody_rejected | BLOCKED |

### 4.15 Registry deny-all versus evaluator denial (OPEN-Q6) (7)

Preconstruction deny-all for three of the five Runtime fields, evaluator denial with exact reason text, direct empty-set policy, Control Plane side blocked. Attack-class slug: `deny_all_vs_evaluator`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-090 | Registry preconstruction deny-all: empty effective allowed_actions | DENY | Runtime denied/attempted=false/policy_denial/reason_code=registry_deny_all/pre_dispatch; detail: decision_kind=applied_deny_all, registry_code=null... | PREPARED |
| NC-091 | Registry preconstruction deny-all: empty effective allowed_units | DENY | Runtime denied/attempted=false/policy_denial/reason_code=registry_deny_all/pre_dispatch; detail: decision_kind=applied_deny_all, registry_code=null... | PREPARED |
| NC-092 | Registry preconstruction deny-all: empty effective allowed_institutions | DENY | Runtime denied/attempted=false/policy_denial/reason_code=registry_deny_all/pre_dispatch; detail: decision_kind=applied_deny_all, registry_code=null... | PREPARED |
| NC-093 | Evaluator denial with non-empty effective sets: first-failing check and reason text preserved (institution) | DENY | Runtime denied/policy_denial/reason_code=local_policy_rejected, detail text 'local institution restriction' (existing evaluator denial; NOT registr... | PREPARED |
| NC-094 | Evaluator denial on the last-listed V1 dimension (unit) | DENY | Runtime denied/policy_denial/reason_code=local_policy_rejected, detail text 'local unit restriction' | PREPARED |
| NC-095 | Policy built directly with an empty frozenset bypasses the adapter: evaluator path, not deny-all | DENY | Runtime reason_code=local_policy_rejected, text 'local action restriction'; no registry_code | PREPARED |
| NC-096 | Control Plane side deny-all for F4/F5 values is undecided | UNSPECIFIED | NEW_CODE_PROPOSED: control_plane_deny_all_cause_unspecified | BLOCKED |

### 4.16 Confused deputy between families (3)

Family presented to the wrong consumer; a selection is never a grant. Attack-class slug: `confused_deputy`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-097 | Runtime F1a selection presented to a Control Plane age consumer | REFUSE | registry_code=family_unsupported | PREPARED |
| NC-098 | Age-family record presented to the Runtime F1a consumer | REFUSE | registry_code=family_unsupported | PREPARED |
| NC-099 | Valid selection with no grant or claim: a selection is never a grant | DENY | existing grant/claim-path refusal (cause unchanged by the registry); decision.operationally_authorized stays false | PREPARED |

### 4.17 String-based decision attacks (OPEN-Q3) (4)

Message text must not drive causes or classification; structured carrier; map completeness. Attack-class slug: `string_decision`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-100 | Non-registry PermissionError whose text equals a registry code name | DENY | Runtime authority_hold/current_authority_rejected recorded as UNMAPPED_CAUSE_LOSS; registry_code absent; never selection_revoked | PREPARED |
| NC-101 | ValueError from check() with text identical to a policy-denial reason is not a policy denial | DENY | Runtime failure_class=evaluation_error, reason_code=local_policy_evaluation_error (existing); not local_policy_rejected | PREPARED |
| NC-102 | Commit-time structured carrier of registry_code | REFUSE | NEW_CODE_PROPOSED: structured_registry_code_carrier | BLOCKED |
| NC-103 | Outcome-map completeness: deleting a CODES entry must fail | REFUSE | completeness test fails naming the missing code | PREPARED |

### 4.18 Sync manufacturing authorization or reversing revocation (A2) (5)

Unauthenticated, reactivating, replaying and un-revoking sync; direct activation_state write. Attack-class slug: `sync_manufacture`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-104 | Sync carrying an unauthenticated statement cannot manufacture an activation | HOLD | registry_code=signature_invalid | PREPARED |
| NC-105 | Sync tries to reactivate a revoked epoch | REFUSE | NEW_CODE_PROPOSED: activation_refused_revoked_epoch | PREPARED |
| NC-106 | Replayed older sync (selection epoch below the row) | REFUSE | registry_code=selection_epoch_stale | PREPARED |
| NC-107 | A newer snapshot that no longer lists a revocation does not un-revoke | HOLD | registry_code=selection_revoked | PREPARED |
| NC-108 | Direct local write of activation_state (no authenticated statement) | REFUSE | NEW_CODE_PROPOSED: activation_write_unauthenticated | PREPARED |

### 4.19 Invalid optional selection masquerading as withdrawal (5)

Optional-scope failures keep their own registry_code; forged and malformed withdraw statements. Attack-class slug: `invalid_optional_as_withdrawal`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-109 | Optional scope, bad signature: not applied, not 'withdrawn' | OVERLAY_NOT_APPLIED | registry_code=signature_invalid | PREPARED |
| NC-110 | Optional scope, expired selection: not applied, code selection_expired | OVERLAY_NOT_APPLIED | registry_code=selection_expired | PREPARED |
| NC-111 | Forged withdraw statement leaves the prior selection in force | HOLD | registry_code=signature_invalid | PREPARED |
| NC-112 | Withdraw statement without a supersedes reference | REFUSE | registry_code=selection_supersession_invalid | PREPARED |
| NC-113 | Withdraw statement carrying a record pin | REFUSE | NEW_CODE_PROPOSED: withdraw_shape_invalid | BLOCKED |

### 4.20 Outage-extension widening (R6) (4)

Extension cannot widen a registry-narrowed bound; existing extension defects characterised. Attack-class slug: `outage_extension`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-114 | Valid signed outage extension lifting a registry-narrowed class above the registry limit | HOLD | NEW_CODE_PROPOSED: extension_exceeds_registry_limit | BLOCKED |
| NC-115 | Rewritten extension row with a lowered recorded base cannot launder an oversized extension | HOLD | defect age_extension_invalid (existing, src/agent_control_plane/freshness.py:155-175 @7a4bcd40); grant_status_stale_or_future when the age exceeds ... | PREPARED |
| NC-116 | Extension larger than the profile's max_age_extension_seconds | HOLD | defect age_extension_exceeds_limit (existing, freshness.py:51, 155-175 @7a4bcd40) | PREPARED |
| NC-117 | Extension for an irreversible class never raises the bound | HOLD | bound stays at the class base; existing behaviour (bounded.py:1370-1373 @7a4bcd40, reversibility/0.1 opt-in) | PREPARED |

### 4.21 Invalid freshness inputs (11)

bool/float/NaN/inf/str/None/negative/zero/huge for the three age fields; refused, never clamped. Attack-class slug: `freshness_invalid_input`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-118 | Invalid age input: huge integers 10**30 and 2**53 and above-ceiling values (status_max_age_seconds) | REFUSE | NEW_CODE_PROPOSED: age_bound_invalid with detail.specific.reason=above_ceiling (sub-causes stay distinct) | BLOCKED |
| NC-119 | Invalid caller age refused even when the registry value is valid | REFUSE | NEW_CODE_PROPOSED: age_bound_invalid with detail.specific.source=caller | PREPARED |
| NC-120 | Required registry age policy that is invalid returns HOLD, never the caller value | HOLD | NEW_CODE_PROPOSED: age_bound_invalid | PREPARED |
| NC-121 | Unvalidated constructor accepts infinity: existing known limit, not protection | KNOWN_LIMIT_NOT_PROTECTED_ASSERTED | existing behaviour: stale observation is not refused; evidence labels it a known limit; closed only on the helper path | PREPARED |
| NC-122 | Invalid age input class: boolean and bool-like integers (status_max_age_seconds) | REFUSE | NEW_CODE_PROPOSED: age_bound_invalid with detail.specific.reason one of ['bool_true', 'bool_false'] (per-variant sub-cause retained, never merged) | PREPARED |
| NC-123 | Invalid age input class: floats (status_max_age_seconds) | REFUSE | NEW_CODE_PROPOSED: age_bound_invalid with detail.specific.reason one of ['float_integral', 'float_fractional', 'float_exp'] (per-variant sub-cause ... | PREPARED |
| NC-124 | Invalid age input class: non-finite numbers (status_max_age_seconds) | REFUSE | NEW_CODE_PROPOSED: age_bound_invalid with detail.specific.reason one of ['nan', 'inf', 'neg_inf'] (per-variant sub-cause retained, never merged) | PREPARED |
| NC-125 | Invalid age input class: non-numeric types (status_max_age_seconds) | REFUSE | NEW_CODE_PROPOSED: age_bound_invalid with detail.specific.reason one of ['str', 'none', 'decimal', 'int_subclass'] (per-variant sub-cause retained,... | PREPARED |
| NC-126 | Invalid age input class: below the floor (status_max_age_seconds) | REFUSE | NEW_CODE_PROPOSED: age_bound_invalid with detail.specific.reason one of ['negative', 'zero'] (per-variant sub-cause retained, never merged) | PREPARED |
| NC-127 | Invalid age input class: full grid replay for the approval age (approval_max_age_seconds) | REFUSE | NEW_CODE_PROPOSED: age_bound_invalid with detail.specific.reason one of ['all variants above'] (per-variant sub-cause retained, never merged) | PREPARED |
| NC-128 | Invalid age input class: full grid replay for the per-class age (ActionClass.max_status_age_seconds) | REFUSE | NEW_CODE_PROPOSED: age_bound_invalid with detail.specific.reason one of ['all variants above'] (per-variant sub-cause retained, never merged) | PREPARED |

### 4.22 Narrowed freshness boundary (3)

Bound plus one second for status, approval and class ages. Attack-class slug: `freshness_boundary`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-129 | Status observation at registry-narrowed bound plus one second | HOLD | reason grant_status_stale_or_future (existing; decision result=hold) | PREPARED |
| NC-130 | Approval observation at registry-narrowed bound plus one second | HOLD | reason approval_status_stale_or_future (existing; decision result=hold) | PREPARED |
| NC-131 | Per-class status age at narrowed bound plus one second | HOLD | reason grant_status_stale_or_future (existing; decision result=hold) | PREPARED |

### 4.23 Route A bypass (out of V1) (3)

Route A is not credited as protected. Attack-class slug: `route_a_bypass`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-132 | Route A execute_snapshot ignores a revoked registry selection: asserted unprotected | NOT_PROTECTED_ASSERTED | route_a_out_of_v1: no commit-time registry recheck; known limit; never PASS | PREPARED |
| NC-133 | Any test or evidence named as Route A protection is rejected | REFUSE | catalogue/result classification check fails naming the offending test | PREPARED |
| NC-134 | Required-scope operation routed over Route A to skip the commit guard | UNSPECIFIED | NEW_CODE_PROPOSED: route_a_required_scope_handling | BLOCKED |

### 4.24 Evidence and reachability (2)

No leakage into evidence; no network inside a transaction. Attack-class slug: `evidence_integrity`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-135 | Evidence never records raw input, signature bytes, caller policy values or trust-snapshot content | REFUSE | scan finds zero canaries | PREPARED |
| NC-136 | No registry call, socket or network I/O inside a transaction; an unreachable registry behaves identically | REFUSE | sentinel records zero attempts; outcome identical with registry reachable and unreachable | PREPARED |

### 4.25 Transaction integrity (2)

Crash between guard and commit; effect, claim and budget atomicity. Attack-class slug: `transaction_integrity`.

| ID | Title | Outcome | Exact cause | Status |
|---|---|---|---|---|
| NC-137 | Crash between guard and commit: recovery re-evaluates, never trusts the earlier guard pass | HOLD | registry_code=selection_revoked | PREPARED |
| NC-138 | Effect, claim and budget commit together under the guard (fault between writes) | NO_EFFECT_COMMITTED | whole transaction rolls back; no partial state; existing atomic fault-injection behaviour preserved | PREPARED |

## 5. Mutation-leg approach

Each row names `mutation_leg`: the **single** check which, if disabled, must make that control fail. This is the Common independence rule (vii) applied per refusal family.

1. **Two legs per control.** Leg 1 runs the control against the unmodified candidate and records the observed outcome and cause. Leg 2 runs the same frozen fixture against a scratch copy of the candidate in which exactly the named check is disabled. The control is credited only if leg 2 flips (the refusal disappears, the cause changes, or an effect commits). A control whose mutant still passes proves nothing and is reported as a non-discriminating control.
2. **One mutation, one control.** The mutation must be the narrowest edit that removes that check. Where one check guards several controls (for example the signature-verify call) the same mutant is reused, and every control it guards must flip.
3. **Mutants live outside every source repository** (scratch copy, patch file kept in the evidence bundle). `engine/safe_executor.py` blob `2fc880da` is never edited; evaluator-denial controls (NC rows in 4.15) mutate only the registry adapter, not the evaluator.
4. **Pair controls run the mutation in the over-refusal direction** (for example tightening `<` to `<=` at the boundary); the paired positive must flip to a refusal.
5. **Known-limit and capability-absence rows** (`NOT_PROTECTED_ASSERTED`, `ABSENT_CAPABILITY_ASSERTED`) use a labelling or surface mutation instead: remove the label, or add the forbidden capability. `tools/adversarial_mutations.py` in the Control Plane was named by `EXT-S4-4` but its contents are unverified and were not read.
6. Mutation legs for commit-time controls cannot be exercised until `EXT-S4-2` exists; until then they are design text only.

### Race and repeat protocol

12 controls carry `race_or_repeat=true` and a `repeat_requirement`. Barrier-driven controls (via the Runtime `_transaction_stage` hook named in `EXT-S4-2`) require at least 5 consecutive identical results; unsynchronised races require at least 200 runs per ordering. **These minima are proposed by this lane, not taken from a contract**; the lead may raise them. Raw logs, per-run timestamps (gate, lock, revocation write, receipt `checked_at`) and the count of each ordering are retained. One run is not evidence (p1/08 risk 22).

## 6. `BLOCKED_ON_CONTRACT` controls

These controls are prepared as test intent only. Their expectation cannot be fixed from approved contracts without guessing, so none may be executed or frozen until the named decision is made.

| ID | Control | Open decision |
|---|---|---|
| NC-012 | v1-signed statement replayed as an r08-v2 statement | EXT-S1-1 ADR must name the v2 domain-separation refusal code (signature_invalid vs contract_unsupported); the ADR does not exist yet. |
| NC-017 | Evidence pack substitutes the governing policy identity | Replay/Verifier refusal vocabulary for a substituted policy identity is not defined (EXT-S1-9/S4-0 ADR). |
| NC-018 | Evidence pack omits the policy identity entirely | Same open vocabulary as the substituted-identity evidence control. |
| NC-021 | Claim carries a newer epoch than the trusted row | EXT-S4-0 ADR: cause code for claim epoch greater than the activated row epoch is not defined (selection_epoch_stale means below floor). |
| NC-030 | Claim expiry extended beyond the selection validity (clamp cannot extend) | EXT-S4-0 ADR: Option C claim-expiry clamp rule (DT-05/LD-09 'defense in depth') is not yet specified; only the intent (clamp cannot extend the grant) is recorded. |
| NC-037 | Wall clock set backwards to un-expire a selection | No contract says how a backwards trusted clock is detected or what code results; EXT-S4-0 ADR to decide. |
| NC-039 | Trust snapshot expires between check and commit | Whether snapshot expiry (distinct from selection expiry) is re-evaluated under the lock is not specified (map says gate_only). |
| NC-044 | Issuer key revoked between check and commit | Does sync translate a key revocation into revocation rows for every selection that key signed, or is key revocation gate-only? EXT-S4-0 ADR open; the lead brief expects before/after-lock coverage. |
| NC-045 | Issuer revoked between check and commit | Same open decision as key revocation: issuer-removal propagation to activation rows at commit. |
| NC-062 | Activation at an equal epoch with different content | EXT-S4-0 ADR: equal-epoch activation is refused (A2) but whether its cause is selection_epoch_stale, selection_conflict or a new code is unspecified; the cause must not be collapsed. |
| NC-073 | Older P0 approval after narrowing (P1) was applied and then withdrawn: must not be revived | Lead brief (Architect final ruling on approval revival): old approval stays invalid. P1 plan 07 and 11 EXT-S3-4: revival of an older P0 approval 'is not guaranteed by V1 (no generation or revocation mechanism is authorized) and is disclosed'. A P0 approval's commitment matches P0 again, so 'stays invalid' needs a mechanism no document authorizes. The final-rulings document was not readable; reconcile before freeze. |
| NC-075 | Approval valid but the grant derives from another profile | No document names the reason for 'approval bound to narrowed profile but grant from another profile' (reverse of the mismatch case). |
| NC-081 | Re-baseline attempted by an unauthenticated local call or from a claim | EXT-S4-0 ADR: who may re-baseline, with what authenticated artifact, is not specified anywhere read. |
| NC-089 | Trust snapshot file is a symlink, FIFO or foreign-owner file | Custody design (who loads the snapshot, ownership/permission rules, resulting code) is operator-gated and unspecified; V1 has no operational trust root. |
| NC-096 | Control Plane side deny-all for F4/F5 values is undecided | OPEN-Q6: no Control Plane outcome for deny-all is asserted anywhere; the registry-versus-evaluator distinction at the Control Plane is undefined. |
| NC-102 | Commit-time structured carrier of registry_code | OPEN-Q3: no decision yet on a structured carrier for registry_code through the destination PermissionError channel (EXT-S4-0 ADR). Until decided, commit-time causes are UNMAPPED_CAUSE_LOSS by contract. |
| NC-113 | Withdraw statement carrying a record pin | EXT-S1-1 ADR: A1 says a withdraw 'carries no record pin' but the refusal code for a pin on a withdraw (field_unknown vs field_invalid vs new) is not specified. |
| NC-114 | Valid signed outage extension lifting a registry-narrowed class above the registry limit | O-1: whether R6 can be met by profile narrowing alone is open (extension rows are measured from the trusted base, so an extension may lift a narrowed class above the registry limit); the S1-1/S3-4 ADR step decides; S3-4 stops if an existing Control Plane source edit is needed. |
| NC-118 | Invalid age input: huge integers 10**30 and 2**53 and above-ceiling values (status_max_age_seconds) | O-4: the numeric ceiling / bound constants are recorded only by the EXT-S1-1 ADR; no placeholder bound may be assumed. The refuse-never-clamp rule is fixed; the threshold is not. |
| NC-134 | Required-scope operation routed over Route A to skip the commit guard | Open decision: must the V1 host refuse Route A for a scope that has a required registry selection, or only disclose that Route A is unprotected? No document read decides. |

### Tensions between sources (recorded, not resolved)

- **Stale epoch outcome (OPEN-Q12).** The outcome map keeps `selection_epoch_stale` as HOLD pending the Architect; the lead brief instructs REFUSE with a specific cause and HOLD only for indeterminate state. The controls follow the brief (REFUSE) and say so in `contract_note`. Both are denied-with-no-effect, so the effect-side assertions are unaffected.
- **Approval revival (NC for P0 revival).** The brief states an old approval "stays invalid" after narrowing is withdrawn. p1/07 and p1/11 `EXT-S3-4` say revival of an older P0 approval "is not guaranteed by V1 (no generation or revocation mechanism is authorized) and is disclosed". A P0 approval's commitment matches P0 again, so "stays invalid" needs a mechanism no document authorizes. Held as BLOCKED; the P1-approval-after-withdrawal control (commitment mismatch P1 to P0) is prepared.
- **Un-revocation by a newer snapshot.** The control that a newer snapshot omitting a revocation does not un-revoke rests on revocation being terminal for `(selection_id, epoch)` (p1/04 lifecycle table). If the Architect intends snapshot-driven un-revocation, that control must be revisited; its `contract_note` says so.

## 7. Proposed new code names

Descriptive names for causes the plan describes without a literal code. All are `NEW_CODE_PROPOSED`; none exists in `registry_successor/common.py` `CODES`.

| Proposed name | Controls |
|---|---|
| `v2_domain_separation_refusal` | NC-012 |
| `evidence_policy_identity_substituted` | NC-017 |
| `evidence_policy_identity_missing` | NC-018 |
| `claim_epoch_ahead_of_row` | NC-021 |
| `claim_commitment_mismatch` | NC-022 |
| `activation_row_identity_mismatch` | NC-023 |
| `claim_policy_binding_missing` | NC-024 |
| `trust_snapshot_fingerprint_mismatch` | NC-027 |
| `executor_supplied_identity_not_authority` | NC-028 |
| `activation_unavailable` | NC-029, NC-055, NC-056 |
| `claim_expiry_clamp_rule` | NC-030 |
| `clock_rollback_cause_unspecified` | NC-037 |
| `snapshot_expiry_at_commit_unspecified` | NC-039 |
| `scope_required_clear_unsupported` | NC-059 |
| `activation_epoch_not_greater` | NC-062 |
| `authority_state_indeterminate` | NC-066 |
| `trust_snapshot_fingerprint_conflict` | NC-069 |
| `trust_snapshot_floor_invalid` | NC-070 |
| `approval_revival_unspecified` | NC-073 |
| `grant_profile_disagreement` | NC-075 |
| `cross_component_policy_disagreement` | NC-076 |
| `authority_state_restore_unbaselined` | NC-077, NC-080 |
| `rebaseline_unauthenticated` | NC-081 |
| `authority_state_unavailable` | NC-082, NC-083, NC-084 |
| `authority_state_inconsistent` | NC-085 |
| `authority_state_corrupt` | NC-086, NC-087 |
| `snapshot_custody_rejected` | NC-089 |
| `control_plane_deny_all_cause_unspecified` | NC-096 |
| `structured_registry_code_carrier` | NC-102 |
| `activation_refused_revoked_epoch` | NC-105 |
| `activation_write_unauthenticated` | NC-108 |
| `withdraw_shape_invalid` | NC-113 |
| `extension_exceeds_registry_limit` | NC-114 |
| `age_bound_invalid` | NC-118, NC-119, NC-120, NC-122, NC-123, NC-124, NC-125, NC-126, NC-127, NC-128 |
| `route_a_required_scope_handling` | NC-134 |

## 8. Sources, independence and what was not read

**Read (contracts, rulings as transcribed in the plan, pinned source):** p1 README/02-11, `ld02-outcome-map.json`, `qualification-gate-matrix.json`; ADR-REG-TR01; the Runtime source at `c5e97e87` (`engine/safe_executor.py`, `engine/atomic_local_control_plane_executor.py`) and the Control Plane source at `7a4bcd40` (`bounded.py`, `runtime_authority.py`, `freshness.py`), read-only from scratch fetches.

**Not read / could not read:** the Architect final-rulings document (`claude/ocs-p1-architect-final-rulings-2026-10-25.md`) was **not** readable by this worker (no project reading tool was available). A1 to A4 are taken from the transcription in p1/04, rulings 1 to 16 from p1/10, and OPEN-Q3/Q5/Q6/Q12, R6 and O-1 to O-5 from the outcome map and p1/11. Approval-revival and "no generalized approval-history migration" are taken from the lead brief (`basis_type` RULING). `laneH.md` (outcome map open-question reference) was not found. Existing qualification-repo suites and `docs/v1-known-limits.md` were consulted for provenance only.

**Contamination:** registry builder tests and oracles (`tests/test_r08_*`, `tests/test_s05_*`, `tests/s05_oracle.py`, `r08_support.py`, `docs/r08-s01/qualification-spec.md`) were **not** opened. `read_contamination` is `none` on every row.

**Disclosed limits that these controls do not close:** consistent rollback of every selection table with no external anchor is undetectable (NC row in 4.13, asserted as a known limit); optional-scope failure falls back to the caller policy and is disclosed, not prevented (p1/08 risk 25); loaded-code replacement, raw SQL by the database holder and non-SQLite destinations are outside every gate (risk 23); key and snapshot custody is operator-gated and recorded as `not performed`.

## 9. Field coverage note

Fields carried by the rows: `NONE` (103), `status_max_age_seconds` (13), `ActionClass.max_status_age_seconds` (11), `allowed_actions` (4), `allowed_units` (3), `allowed_institutions` (2), `approval_max_age_seconds` (2). Selection, identity, state and sync attacks are field-agnostic and carry `NONE`. The registry deny-all rows exercise three of the five Runtime fields (`allowed_actions`, `allowed_units`, `allowed_institutions`); the same fixture template extends to `allowed_adapters` and `allowed_authority_domains` (only `deny_all_fields` differs) if the lead wants one row per field.

## 10. Handoff to the lead

- Define the `FX-B-nnn` fixtures (shared fixtures can serve many rows: one signed selection, one trust snapshot, one activated store, one claim, one age grid).
- Decide the `BLOCKED_ON_CONTRACT` items in section 6 and the proposed code names in section 7 before freeze; no expectation may be edited after a result is seen.
- Confirm the proposed race minima in section 5.
- This catalogue is builder-independent preparation. It confers no qualification, and no row may be read as a PASS, a protection claim or a verdict.
