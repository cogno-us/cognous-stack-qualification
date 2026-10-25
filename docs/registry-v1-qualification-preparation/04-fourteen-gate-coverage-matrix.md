# 04 Fourteen-gate coverage matrix (gate definitions)

**Status: test-design and evidence PREPARATION. This is not independent Tier 1 qualification. No V1 implementation exists, nothing here was run, and no gate is met.** RELEASE, PUBLICATION and PRODUCTION: HOLD. Every statement below is a prepared expectation or frozen-intent, state NOT_RUN; any outcome today is NOT_QUALIFIED.

Gate meaning is preserved from the P1 plan (`07-independent-qualification-matrix.md`, `data/qualification-gate-matrix.json`, registry main `d2c472e4`). Machine-readable twin: [`data/gate-definitions.json`](data/gate-definitions.json) (14 records). V1 scope: eight fields (Runtime: allowed_actions, allowed_adapters, allowed_units, allowed_institutions, allowed_authority_domains; Control Plane: status_max_age_seconds, approval_max_age_seconds, ActionClass.max_status_age_seconds), atomic Route B only. `max_amount` is deferred; QG-02 is retained and INACTIVE. QG-01 and QG-07 bear on the five Runtime fields; QG-03 and QG-04 bear on the Control Plane ages only.

Source note: the Architect final rulings file (`claude/ocs-p1-architect-final-rulings-2026-10-25.md`) could not be read by this lane (no project-read tool available). Ruling content is taken from P1 docs 10 and 11 and 07 only; any gate expectation that depends on a ruling detail not visible there is marked in `block_criteria` and must be confirmed against the rulings file before freeze.

## Summary table

| Gate | Name | V1 status | Evidence status of source scenarios today | Depends on unfinished V1 | Blocking contracts to confirm |
|---|---|---|---|---|---|
| QG-01 | Differential old/new evaluator, five DIRECT Runtime fields | ACTIVE | KNOWN_LIMIT_ASSERTED 1, NOT_RUN 3, PASS_RECORDED 3 | yes | OPEN-Q3, OPEN-Q6 |
| QG-02 | max_amount differential (INACTIVE: max_amount deferred, not in V1) | INACTIVE_MAX_AMOUNT_DEFERRED | KNOWN_LIMIT_ASSERTED 1, NOT_RUN 3, PASS_RECORDED 2 | no (deferred) | D6 (deferred) |
| QG-03 | F4 status_max_age_seconds and approval_max_age_seconds differential (Control Plane) | ACTIVE | NOT_RUN 4, PASS_RECORDED 4 | yes | R6 mechanics (O-1), floor/int rules |
| QG-04 | F5 ActionClass.max_status_age_seconds differential (Control Plane) | ACTIVE | NOT_RUN 2, PASS_RECORDED 1 | yes | R5/R6, revival disclosure |
| QG-05 | Configuration change: selection, supersession, rollback, epoch | ACTIVE | NO_TEST 3 | yes | A1-A4, OPEN-Q12, QS13 |
| QG-06 | Required-policy refusal | ACTIVE | NOT_RUN 1 | yes | OPEN-Q3/Q6/Q12, outcome map |
| QG-07 | Scope narrowing, never widening (five Runtime fields) | ACTIVE | KNOWN_LIMIT_ASSERTED 1, PASS_RECORDED 1 | yes | scope binding, unsupported-value class |
| QG-08 | Revocation and expiry | ACTIVE | KNOWN_LIMIT_ASSERTED 1, PASS_RECORDED 2 | yes | claim-expiry clamp, race disclosure |
| QG-09 | Atomic Route B effect-boundary tests | ACTIVE | KNOWN_LIMIT_ASSERTED 2, PASS_RECORDED 1 | yes | R10 option, O-3, O-5 |
| QG-10 | Cross-component policy consistency | ACTIVE | PASS_RECORDED 1 | yes | profile hash definition |
| QG-11 | Evidence and replay verification | ACTIVE | PASS_RECORDED 6 | yes | evidence field set |
| QG-12 | Independent negative tests | ACTIVE | PASS_RECORDED 3 | yes | negative classification |
| QG-13 | Regression and disclosure | ACTIVE | KNOWN_LIMIT_ASSERTED 4, PASS_RECORDED 5 | yes | GAP-G4-07/09 owner actions |
| QG-14 | Process: exact-head independent run by designated owner | ACTIVE | none (process gate) | yes | lead designation (GAP-G4-13) |

## Status vocabulary

- `NOT_RUN`: nothing in this package has been executed. All prepared expectations are NOT_RUN.
- `BLOCKED`: a contract or ruling is unresolved or a mapping is not representable. Never waived. A mismatch against a resolved expectation is FAIL; an unresolved mapping is BLOCKED.
- `BLOCKED_ON_CONTRACT`: row-level marker naming the open decision.
- `NOT_QUALIFIED`: default state of every gate.
- `PASS_RECORDED` (crosswalk evidence status): a named historical case passed at the g8-r10 controller pins (Control Plane `0a41faa9`, Runtime `ec728da6`), not at current heads or any candidate. The scenario row stays INCONCLUSIVE; there is no scenario-level PASS. It is context, never a V1 result.
- `KNOWN_LIMIT_ASSERTED` (C11, C07, C10, D07): a test asserting a limit; never a PASS or protection.
- `NO_TEST` and `NOT_RUN` (crosswalk): no test exists / not executed. Collection is not execution. D01, D03, D04 stay INCONCLUSIVE.
- `BUILDER_TESTED`: registry-repo tests written by the builder; excluded as a basis for any expectation here.
- `INACTIVE_MAX_AMOUNT_DEFERRED`: QG-02 only; reported as inactive, never counted as PASS.

## Shared independence rules (apply to every gate)

- Expectations written by the blind oracle author from contracts, rulings and source characterization before any implementation result is shown for the gate; each names its basis and basis_type (CONTRACT, RULING, SOURCE_CHARACTERIZATION, INVENTORY).
- Registry builder tests and oracles are not read to derive an expectation; accidental reads are recorded as contamination.
- Expectations, candidate pins and a spec digest are frozen in a dated qualification-repo commit before execution; amendments are dated and never made to obtain a pass.
- Roles stay separate: oracle author (blind), builder (never edits expectations), runner (retains raw output), evidence reviewer (separate from all three, else recorded not performed), final adjudicator (operator).
- Only a designated independent lead writes a Tier 1 verdict. The builder, Architect, Copilot or any dependent worker may not be the lead. Copilot review is technical review, not qualification. Builder-side inspection never counts toward independence.
- Synthetic data only; no network, paid, credentialed or production execution; no real key material.
- A mutation leg applies to every refusal family: disable exactly one refusal check and the case must fail.
- Race and clock gates (QG-03, QG-08, QG-09 at minimum) require repeated runs with every raw log retained; one run is not evidence.
- The verdict transfers only to the exact candidate and profile; pins listed below are filled at freeze. Analysed baselines (Runtime `c5e97e87`, Control Plane `7a4bcd40`, registry `d2c472e4`, qualification `be1994a9`, evaluator blob `2fc880da`) are analysed baseline only, not the candidate.
- Route A is out of V1: Route A results are characterization context and earn no credit (negative class route_a_not_credited).

## Negative-control class slugs used by gates

forged_selection, substituted_digest, mismatched_claim_identity, expired_selection, revoked_selection, required_absence, epoch_downgrade, concurrent_revocation, stale_approval_revival, restore_rollback, durable_state_missing_or_corrupt, registry_denyall_vs_evaluator_denial, invalid_freshness_input, outage_extension_widening, confused_deputy, string_based_decision, route_a_not_credited.

## Gate definitions

### QG-01 Differential old/new evaluator, five DIRECT Runtime fields

**V1 status:** ACTIVE

**Statement.** For the five Runtime fields only (allowed_actions, allowed_adapters, allowed_units, allowed_institutions, allowed_authority_domains), a registry-backed LocalExecutionPolicy yields the same first-failing-check disposition and reason text as the historical policy built from the effective sets, per field, when every effective set is non-empty. When any effective set is empty the adapter denies before constructing a policy (registry deny-all): denial, zero effect rows, claim not consumed, budget unchanged, and it is NOT reason-text equality. Atomic Route B is the only V1 execution boundary; Route A behaviour is characterization context and earns no credit.

**Source scenarios (crosswalk evidence_status; PASS_RECORDED = named historical case at g8-r10 pins, not current heads):** C11 (KNOWN_LIMIT_ASSERTED), C02 (PASS_RECORDED), D02 (PASS_RECORDED), C18 (PASS_RECORDED), TC-L06-009 (NOT_RUN), TC-L06-011 (NOT_RUN), TC-L06-013 (NOT_RUN)

**Required assertions:**
- per field x {empty, subset, superset, disjoint, equal} grid of caller set versus registry set: effective set equals exact-string intersection and disposition matches the historical policy built from that set
- first-failing-check order and reason text identical old vs new for multi-violation inputs (non-empty effective sets only)
- empty effective set (any of the five): refusal before LocalExecutionPolicy construction, zero effects, claim unconsumed, budget unchanged; the cause is distinguishable from an evaluator denial
- omitted deployed value in the registry set refuses all (fail closed); absent field is a refusal, empty array is explicit deny-all
- exact-string membership: wildcard, case, whitespace, unicode, substring, bare str all behave as exact string comparison with no normalization
- caller policy object not mutated; trusted-context (institution/domain) check still refuses a substituted value independently of the registry
- engine/safe_executor.py blob unchanged from the candidate pin (no evaluator edit)
- denial and deny-all asserted on the Route B atomic path; Route A results recorded as out of V1 and not credited

**Expected negative controls (class slugs):**
- registry_denyall_vs_evaluator_denial
- string_based_decision
- mismatched_claim_identity
- route_a_not_credited

**Evidence artifacts:**
- raw per-case logs for the full run (stdout/stderr)
- junit xml per suite
- collected-test list AND executed-test list (collection is not execution)
- SHA256SUMS over all run artifacts
- environment record (interpreter, OS, dependency lock hashes, clock source)
- expectations digest (hash of the frozen oracle/control/case files)
- candidate pin record (the five head SHAs, evaluator blob, trust snapshot id)
- skip/xfail/error list preserved verbatim (a skip is not evidence)
- mutation-leg log (one refusal check disabled per case; case must fail)
- old-vs-new differential table (per case: historical-policy outcome, registry-backed outcome, equality verdict)
- evaluator blob hash record

**Existing test gaps:**
- C11 is KNOWN_LIMIT_ASSERTED: it asserts a limit and is not protection
- C02, D02, C18 are PASS_RECORDED for named historical cases at g8-r10 pins only; their scenario rows stay INCONCLUSIVE; no run at current heads
- TC-L06-009/011/013 are NOT_RUN
- Runtime-side tests isolate only unit, amount and action; institution, domain and adapter coverage exists only in the qualification repo (inventory erratum 7)
- no existing test covers a registry-supplied value; no empty-set deny-all-before-construction test exists
- registry builder tests exist but are not a basis for any expectation (independence)

**Missing oracle coverage candidates:**
- per-field x route-B grid oracles for all five fields
- check-order/reason-text differential cases with multi-violation pairs
- deny-all-before-construction controls for each field and for all-five-empty
- exact-string membership edge oracles
- mutation controls: collapse deny-all into evaluator denial; normalize case; widen on omitted value

**Pass criteria.** Every frozen QG-01 oracle, differential case and negative control executes at the exact pins and matches its frozen expectation; mutation leg fails the disabled-check case for each refusal family; no skipped or unexecuted case; verdict written by the designated independent lead.

**Fail criteria.** Any mismatch against a resolved expectation (disposition, reason text, effect/claim/budget state), any widening of an effective set, evaluator blob changed, or a deny-all reported with a reason text taken from the evaluator.

**Block criteria.** BLOCKED (never waived) if the deny-all vs evaluator-denial distinction (OPEN-Q6) or exact-string/type rules (OPEN-Q3) are not recorded in a readable contract or ruling, if the registry-to-Runtime adapter mapping is not representable at the candidate, or if the five-field wiring (EXT-S1-3, EXT-S2-2) is absent.

**Depends on unfinished V1:** yes: EXT-S1-2, EXT-S1-3 (r08-v2 five-set family), EXT-S2-1, EXT-S2-2 (Runtime narrowing adapter), EXT-S1-5 (outcome map); no V1 implementation exists

**Reviewer requirements:** shared independence rules above apply without gate-specific additions.

### QG-02 max_amount differential (INACTIVE: max_amount deferred, not in V1)

**V1 status:** INACTIVE_MAX_AMOUNT_DEFERRED

**Statement.** Retained from the P1 gate set: effective ceiling = min(caller, registry) under a code cap, with exactly-one-effect and finite-number validators unchanged. In V1 max_amount is deferred and out of scope, so this gate is INACTIVE, is reported as inactive, and is never counted as met or PASS. No oracle, control or differential case is authored for it.

**Source scenarios (crosswalk evidence_status; PASS_RECORDED = named historical case at g8-r10 pins, not current heads):** C11 (KNOWN_LIMIT_ASSERTED), C16 (PASS_RECORDED), C18 (PASS_RECORDED), TC-L06-014 (NOT_RUN), TC-L06-016 (NOT_RUN), TC-L06-024 (NOT_RUN)

**Required assertions:**
- none in V1; the gate is reported as INACTIVE_MAX_AMOUNT_DEFERRED in the execution record
- if separately authorized later: expectations cannot be authored until D6 and the amount encoding are ruled

**Expected negative controls (class slugs):**
- none

**Evidence artifacts:**
- status line in the execution record: QG-02 INACTIVE_MAX_AMOUNT_DEFERRED, not PASS, not counted

**Existing test gaps:**
- C11[max_amount] is KNOWN_LIMIT_ASSERTED; C16/C18 PASS_RECORDED named historical cases; TC-L06-014/016/024 NOT_RUN; none is V1 evidence
- registry-side: none (pass-through only)

**Missing oracle coverage candidates:**
- none for V1 (excluded); one explicit 'excluded' note is the only permitted artifact

**Pass criteria.** Not applicable. An inactive gate has no pass condition and is never counted as PASS.

**Fail criteria.** Reporting QG-02 as PASS, met, or counted in an ACTIVE-gate total; or presenting a max_amount check as V1 evidence.

**Block criteria.** Any future activation is BLOCKED until D6 and the encoding are ruled and the operator re-authorizes scope.

**Depends on unfinished V1:** no: Deferred by operator; not an unfinished V1 item

**Reviewer requirements:** shared independence rules above apply without gate-specific additions.

### QG-03 F4 status_max_age_seconds and approval_max_age_seconds differential (Control Plane)

**V1 status:** ACTIVE

**Statement.** Freshness bounds only tighten: the effective status_max_age_seconds and approval_max_age_seconds are the validated per-scalar min(caller, registry) of strict integer seconds; stale, future and missing observations are refused or held; tolerance never extends the window. This gate bears on the three Control Plane ages as scoped to the two F4 ages here (ActionClass.max_status_age_seconds belongs to QG-04). There is no universal five-second floor and no cross-bound between the distinct F4 ages (the 60-vs-300 relationship is neither assumed nor resolved).

**Source scenarios (crosswalk evidence_status; PASS_RECORDED = named historical case at g8-r10 pins, not current heads):** C01 (PASS_RECORDED), C17 (PASS_RECORDED), C06 (PASS_RECORDED), D03 (PASS_RECORDED), H01 (NOT_RUN), TC-L06-015 (NOT_RUN), TC-D09-009 (NOT_RUN), TC-D09-016 (NOT_RUN)

**Required assertions:**
- per age: observation at bound-1 accepted, at bound per characterized rule, at bound+1 refused, evidenced against real bounded.py _fresh at the candidate Control Plane
- future observation at 0, at clock tolerance, and at tolerance+1
- registry < caller => effective = registry (e.g. caller 60, registry 30 => 30); registry = caller => caller; registry > caller => caller (registry value recorded as not narrowing)
- registry value 0, negative, bool, float, string, huge: refused (code floor >= 1, strict int) before _fresh, with a typed cause
- stable refusal codes for grant/conflict/policy/approval status stale or future
- lock-time clock domain used for the comparison, not the check-time clock
- mandatory profile: unavailable or invalid registry value does not fall back to the caller value
- clock_tolerance_seconds is not weakened by registry values
- a validly signed outage extension never lifts the effective ceiling above min(caller, registry); an extension computed from the caller value instead of the narrowed value is refused
- extension beyond the code-owned bound, unsigned, forged, expired, replayed, other-scope or on a different field is refused with a typed extension-invalid cause and zero effects
- approval_max_age and status_max_age are independent; neither is derived from the other

**Expected negative controls (class slugs):**
- invalid_freshness_input
- outage_extension_widening
- stale_approval_revival
- required_absence
- string_based_decision
- expired_selection

**Evidence artifacts:**
- raw per-case logs for the full run (stdout/stderr)
- junit xml per suite
- collected-test list AND executed-test list (collection is not execution)
- SHA256SUMS over all run artifacts
- environment record (interpreter, OS, dependency lock hashes, clock source)
- expectations digest (hash of the frozen oracle/control/case files)
- candidate pin record (the five head SHAs, evaluator blob, trust snapshot id)
- skip/xfail/error list preserved verbatim (a skip is not evidence)
- mutation-leg log (one refusal check disabled per case; case must fail)
- repeated-run logs (minimum run count predeclared at freeze; every run retained, single runs do not qualify) with per-run seeds/orderings
- clock-source record and injected-clock transcript for boundary cases
- old-vs-new differential table at real _fresh

**Existing test gaps:**
- C01, C17, C06, D03 are PASS_RECORDED for named historical cases at g8-r10 pins; D03 row INCONCLUSIVE; H01 and TC-L06-015, TC-D09-009/016 are NOT_RUN
- no Control Plane test passes the four age kwargs (inventory erratum 4); Control Plane tests exist at the default 60 only
- no test pins registry-narrowed ages or the extension-vs-narrowed-value relation
- probe clock-uncertainty tests are limits/probes, not V1 protection

**Missing oracle coverage candidates:**
- boundary grids for both ages (bound-1/bound/bound+1, future/tolerance)
- per-scalar min direction table
- invalid-value refusal family (0, negative, bool, float, str, huge)
- outage-extension cap controls incl. extension-base mutation
- mandatory-profile no-fallback control

**Pass criteria.** All frozen QG-03 oracles, differential cases and controls execute at the exact pins and match; boundary and clock cases pass in every repeated run; mutation legs (use check-time clock; compute extension on the caller value; drop the floor) fail their cases; designated independent lead verdict.

**Fail criteria.** Any age exceeds min(caller, registry), tolerance extends the window, an invalid freshness value is accepted or coerced, an extension widens past the narrowed value, or a boundary result differs between repeated runs.

**Block criteria.** BLOCKED (not waived) if the R6 outage-extension mechanics are not resolved (P1 doc 11 open item O-1: whether profile narrowing alone suffices) or the strict-integer and floor rules lack a readable ruling; if EXT-S3-3/S3-4 are not present the extension controls are not representable.

**Depends on unfinished V1:** yes: EXT-S1-4 (age slots, per-scalar min), EXT-S3-1 (characterization), EXT-S3-2 (age_bounds helper), EXT-S3-3 (host factory), EXT-S3-4 (extension limit); R6 mechanics O-1

**Reviewer requirements:** shared independence rules above apply without gate-specific additions.

### QG-04 F5 ActionClass.max_status_age_seconds differential (Control Plane)

**V1 status:** ACTIVE

**Statement.** The per-class ActionClass.max_status_age_seconds can only be lowered by the registry (per-class min, strict integer, floor >= 1); the approval binds to the effective narrowed profile, so the profile commitment reflects the effective profile; relaxing toggles (on_unreadable, allow_synthetic_resolver, bounded_tolerance) are unreachable from the registry. This gate bears on the Control Plane class age only.

**Source scenarios (crosswalk evidence_status; PASS_RECORDED = named historical case at g8-r10 pins, not current heads):** C01 (PASS_RECORDED), TC-L05-012 (NOT_RUN), TC-L05-013 (NOT_RUN)

**Required assertions:**
- per-class effective bound = min(caller class bound, registry class bound); class bounds 5 and 120 characterized old vs new
- unknown action class refused (action_class_unknown), not defaulted
- existing zero-bound behaviour at the pin characterized (_fresh accepts an observation at now and a future one within tolerance when the bound is 0); the new helper floor >= 1 refuses values below 1 before _fresh
- irreversible class never raised by an extension
- effective profile equals the profile hashed into approval_commitment
- approval bound to narrowed profile P1 passes while P1 is in force (positive control); after narrowing is withdrawn it fails by commitment mismatch (P1 to P0); an approval hashing the caller profile is refused against the narrowed profile; an older P0 approval stays invalid after the narrowing is withdrawn (no automatic revival; Architect final ruling; fresh approval or authorized new issuance required; no generalized approval-history migration), asserted by QO-065, NC-073 and DF-103, while the baseline commitment re-match (DF-086) is recorded as a characterization only
- relaxing toggles cannot be set or influenced from any registry payload
- a detector exists that fails if the bounded_tolerance toggle is opted in

**Expected negative controls (class slugs):**
- stale_approval_revival
- outage_extension_widening
- invalid_freshness_input
- mismatched_claim_identity
- required_absence

**Evidence artifacts:**
- raw per-case logs for the full run (stdout/stderr)
- junit xml per suite
- collected-test list AND executed-test list (collection is not execution)
- SHA256SUMS over all run artifacts
- environment record (interpreter, OS, dependency lock hashes, clock source)
- expectations digest (hash of the frozen oracle/control/case files)
- candidate pin record (the five head SHAs, evaluator blob, trust snapshot id)
- skip/xfail/error list preserved verbatim (a skip is not evidence)
- mutation-leg log (one refusal check disabled per case; case must fail)
- profile-commitment comparison record (effective profile vs hashed profile)
- toggle-reachability check record

**Existing test gaps:**
- C01 PASS_RECORDED for named historical cases only
- TC-L05-012/013 are NOT_RUN and TC-L05-013 cannot detect the bounded_tolerance toggle (GAP-G4-05)
- no test exists for registry-narrowed class bounds or commitment equality (CP-F5-12)
- the baseline has no test for revival and no generation or revocation mechanism; the candidate requirement (no automatic revival) is carried by QO-065, NC-073 and DF-103

**Missing oracle coverage candidates:**
- per-class min oracles for classes 5 and 120
- unknown-class refusal
- commitment-equality and P1/P0 approval cases (incl. positive control)
- toggle-unreachable and toggle-detector controls
- irreversible-class extension control

**Pass criteria.** All frozen QG-04 cases execute at the exact pins and match, including the P1 positive control and the P1-to-P0 commitment mismatch; mutation leg (raise instead of min; hash caller profile) fails its case; designated independent lead verdict.

**Fail criteria.** A class bound is raised, an approval bound to the caller profile passes against the narrowed one, a relaxing toggle is reachable, or an extension lifts a narrowed class.

**Block criteria.** BLOCKED if the approval-revival ruling's exact cause name or the R5/R6 mechanics are unresolved, or EXT-S3-4 (per-class min, approval binding, extension limit) is absent so the mapping is not representable.

**Depends on unfinished V1:** yes: EXT-S1-4 (F5 family), EXT-S3-3, EXT-S3-4 (per-class narrowing, approval binding R5, extension limit R6)

**Reviewer requirements:** shared independence rules above apply without gate-specific additions.

### QG-05 Configuration change: selection, supersession, rollback, epoch

**V1 status:** ACTIVE

**Statement.** A configuration change takes effect only through an authenticated, explicitly superseding selection, and never by a higher epoch alone, by rollback, or by a restore of older state. Withdrawal, activation and the scope_required ratchet follow the Architect rulings (A1-A4). Applies to selections governing the eight V1 fields.

**Source scenarios (crosswalk evidence_status; PASS_RECORDED = named historical case at g8-r10 pins, not current heads):** C19 (NO_TEST), C20 (NO_TEST), C21 (NO_TEST)

**Required assertions:**
- v1 to v2 supersession is effective for the next operation only; the in-flight operation keeps its original identity
- higher epoch without explicit supersession is a conflict, distinct from stale-epoch
- equal, older and swapped epoch (between check and commit) refused; claim epoch below the Runtime high-water refused (REFUSE with a specific cause, HOLD only if authority state is genuinely unavailable: OPEN-Q12)
- two selections in one scope conflict
- restore of a selection store older than a revocation or higher epoch fails closed until re-baselined; lost or corrupt high-water state fails closed
- half-completed activation rolls back with no partial selection effective; reactivating a restored revoked record is refused
- withdrawn, absent, revoked, expired, superseded each yield their own code for required and optional participation
- withdraw without supersedes, at equal/lower epoch, or carrying a record pin is refused; withdrawal never lowers the high-water
- no code path writes activation_state without an authenticated selection, withdrawal or revocation
- scope_required ratchet: optional presentation for a required scope refused from claim, selection, caller and restored older store; survives restart
- real Ed25519 verifier behaviour with synthetic keys (not FakeVerifier) once EXT-S1-7 exists; QS13 re-adjudicated and frozen by the independent lead, not taken from the builder amendment

**Expected negative controls (class slugs):**
- forged_selection
- epoch_downgrade
- restore_rollback
- durable_state_missing_or_corrupt
- revoked_selection
- expired_selection
- required_absence
- concurrent_revocation

**Evidence artifacts:**
- raw per-case logs for the full run (stdout/stderr)
- junit xml per suite
- collected-test list AND executed-test list (collection is not execution)
- SHA256SUMS over all run artifacts
- environment record (interpreter, OS, dependency lock hashes, clock source)
- expectations digest (hash of the frozen oracle/control/case files)
- candidate pin record (the five head SHAs, evaluator blob, trust snapshot id)
- skip/xfail/error list preserved verbatim (a skip is not evidence)
- mutation-leg log (one refusal check disabled per case; case must fail)
- synthetic trust-snapshot fixture record (lead-owned keys, no real key material)
- durable-state before/after snapshots for restore and rollback cases
- activation-log excerpts

**Existing test gaps:**
- C19, C20, C21 are NO_TEST in the crosswalk
- registry builder tests exist (FakeVerifier, not cryptography) and are excluded as a basis; QS13 was amended after behaviour was seen (developer evidence only)
- no activation, no approved pin and no runtime wiring exist; no scope_required ratchet test; no restore/rollback test at a Runtime boundary

**Missing oracle coverage candidates:**
- supersession/next-operation-only oracle
- epoch cause-distinctness oracles
- withdraw statement validity oracles
- restore, lost high-water and half-activation controls
- ratchet survive-restart control
- activation_state authenticated-writer control

**Pass criteria.** All frozen QG-05 cases execute at the exact pins with the real verifier and match; stale-epoch and conflict remain distinct causes; restore/rollback cases fail closed; mutation legs fail; designated independent lead verdict.

**Fail criteria.** A config change takes effect by epoch alone or by rollback, two causes are collapsed, activation_state is writable without an authenticated statement, or lost state does not fail closed.

**Block criteria.** BLOCKED if A1-A4 mechanics, OPEN-Q12 outcome class, or the QS13 re-adjudication are unresolved or unreadable; if the selection-state schema (EXT-S4-0) or durable selection destination (EXT-S4-2) does not exist the cases are not representable.

**Depends on unfinished V1:** yes: EXT-S1-1/S1-3/S1-6/S1-7/S1-8/S1-9, EXT-S4-0, EXT-S4-2 (selection destination, ratchet), EXT-S4-3

**Reviewer requirements:** shared independence rules above apply without gate-specific additions.

### QG-06 Required-policy refusal

**V1 status:** ACTIVE

**Statement.** A required registry policy that is unavailable, invalid, stale, revoked, expired or untrusted never falls back to a broader caller policy: the outcome is a typed refusal with zero effects. Optional participation yields overlay_not_applied with the caller policy unchanged and is not a denial. All 46 r08-v1 registry codes plus the v2 additions map to REFUSE/DENY/HOLD/RETRY, with registry_code preserved.

**Source scenarios (crosswalk evidence_status; PASS_RECORDED = named historical case at g8-r10 pins, not current heads):** TC-L05-013 (NOT_RUN)

**Required assertions:**
- at the Runtime/Control Plane boundary, each of unavailable, invalid, stale, revoked, expired, no trust root, no verifier, malformed caller policy yields a typed refusal and zero effects, claim unconsumed
- no dispatch and no fallback to the caller policy on any required-profile failure
- optional participation: caller policy unchanged, overlay_not_applied, not a denial
- a required scope that is withdrawn, revoked, expired or unavailable never returns the caller policy and never succeeds
- completeness: every entry of the ld02 outcome map (46 r08-v1 codes plus trust_snapshot_version_stale and selection_withdrawn and any ADR-listed v2 addition) maps to a typed outcome; an unmapped entry fails the test; deletion of selection_withdrawn fails
- each mapped code keeps detail.registry_code; overloaded codes keep their subcause distinguishable
- registry preconstruction deny-all is distinguishable from a LocalExecutionPolicy.check evaluator denial (OPEN-Q6)
- outcome selection is structural, never derived by matching message text (OPEN-Q3)

**Expected negative controls (class slugs):**
- required_absence
- forged_selection
- expired_selection
- revoked_selection
- epoch_downgrade
- durable_state_missing_or_corrupt
- registry_denyall_vs_evaluator_denial
- string_based_decision

**Evidence artifacts:**
- raw per-case logs for the full run (stdout/stderr)
- junit xml per suite
- collected-test list AND executed-test list (collection is not execution)
- SHA256SUMS over all run artifacts
- environment record (interpreter, OS, dependency lock hashes, clock source)
- expectations digest (hash of the frozen oracle/control/case files)
- candidate pin record (the five head SHAs, evaluator blob, trust snapshot id)
- skip/xfail/error list preserved verbatim (a skip is not evidence)
- mutation-leg log (one refusal check disabled per case; case must fail)
- outcome-map completeness report (map entries vs registry code set)
- per-failure-class table of outcome, effects, claim and budget state

**Existing test gaps:**
- TC-L05-013 is NOT_RUN and cannot detect the opt-in tolerance toggle
- registry builder tests are decision-function level only (BUILDER_TESTED) and excluded as a basis; none at an effect boundary
- no Runtime/Control Plane required-profile test exists

**Missing oracle coverage candidates:**
- one oracle per failure class at the boundary
- outcome-map completeness oracle
- optional-mode oracle
- registry_code preservation oracle
- mutation controls: fallback-to-caller; delete-map-entry

**Pass criteria.** Every failure class on a required profile refuses with the frozen typed outcome and zero effects; completeness holds; mutation legs (fall back to the caller; delete a code from the map) fail their cases; designated independent lead verdict.

**Fail criteria.** Any fallback to a broader caller policy, any unmapped code, any outcome derived from message text, or a required failure that dispatches.

**Block criteria.** BLOCKED if the outcome class for a code is unresolved in ld02-outcome-map or the rulings (OPEN-Q3/Q6/Q12) are unreadable, or EXT-S1-5/S4-2 mappings are not representable.

**Depends on unfinished V1:** yes: EXT-S1-5 (46-code outcome map and completeness test), EXT-S1-6, EXT-S4-2, EXT-S4-4

**Reviewer requirements:** shared independence rules above apply without gate-specific additions.

### QG-07 Scope narrowing, never widening (five Runtime fields)

**V1 status:** ACTIVE

**Statement.** For each of the five Runtime fields, effective = caller set intersect registry set (exact-string containment); a registry superset, or a selection for the wrong tenant, consumer or scope, never widens. The same never-widen direction holds for the three Control Plane ages by min, evidenced under QG-03/QG-04; this gate's field-set statement bears on the five Runtime fields.

**Source scenarios (crosswalk evidence_status; PASS_RECORDED = named historical case at g8-r10 pins, not current heads):** C11 (KNOWN_LIMIT_ASSERTED), D02 (PASS_RECORDED)

**Required assertions:**
- written containment relation per field; effective is always a subset of the caller set
- property cases over universes larger than 2-3 values per field, including registry superset, disjoint, equal, empty
- wrong tenant, wrong consumer, wrong scope selection is refused, not applied
- unsupported or unknown family/field value refused with a typed class, not ignored
- consumer-level evidence in the real Runtime path (not a function-level call only)
- registry value with extra or case/whitespace variants never matches a caller value

**Expected negative controls (class slugs):**
- mismatched_claim_identity
- confused_deputy
- registry_denyall_vs_evaluator_denial
- string_based_decision
- forged_selection

**Evidence artifacts:**
- raw per-case logs for the full run (stdout/stderr)
- junit xml per suite
- collected-test list AND executed-test list (collection is not execution)
- SHA256SUMS over all run artifacts
- environment record (interpreter, OS, dependency lock hashes, clock source)
- expectations digest (hash of the frozen oracle/control/case files)
- candidate pin record (the five head SHAs, evaluator blob, trust snapshot id)
- skip/xfail/error list preserved verbatim (a skip is not evidence)
- mutation-leg log (one refusal check disabled per case; case must fail)
- containment relation statement per field (frozen with the oracles)
- property-case generator seed and enumerated universe record

**Existing test gaps:**
- C11 KNOWN_LIMIT_ASSERTED; D02 PASS_RECORDED for named historical cases (binding substitution, not allow-list narrowing)
- registry builder property tests use 2-3 values per field, are BUILDER_TESTED and are excluded as a basis
- apply_registry_overlay had no caller in the P1 analysis; no consumer-level test exists

**Missing oracle coverage candidates:**
- large-universe containment oracles per field
- tenant/consumer/scope mismatch controls
- confused-deputy control between families
- union-instead-of-intersection mutation control

**Pass criteria.** No frozen case yields an effective value outside the caller set; wrong-scope/tenant/consumer cases refuse; mutation leg (union instead of intersection) fails; designated independent lead verdict.

**Fail criteria.** Any widening, any scope/tenant/consumer mismatch applied, any non-containment effective value.

**Block criteria.** BLOCKED if tenant/consumer/scope binding semantics or the unsupported-value outcome class are unresolved, or if there is no consumer path in Runtime to exercise (EXT-S2-2/S4-2 absent).

**Depends on unfinished V1:** yes: EXT-S1-2, EXT-S1-3, EXT-S2-2 (narrowing adapter), EXT-S4-2 (consumer path)

**Reviewer requirements:** shared independence rules above apply without gate-specific additions.

### QG-08 Revocation and expiry

**V1 status:** ACTIVE

**Statement.** A revoked or expired registry selection cannot govern an effect, in either order against the commit; revoked is terminal and is not resurrected by reactivation, lineage, a higher epoch or a restore. Commit-time revocation, expiry and epoch checks remain essential (ruling 12).

**Source scenarios (crosswalk evidence_status; PASS_RECORDED = named historical case at g8-r10 pins, not current heads):** D03 (PASS_RECORDED), C07 (KNOWN_LIMIT_ASSERTED), C17 (PASS_RECORDED)

**Required assertions:**
- selection revoked or expired after check and before commit is refused; same result when revocation lands before the lock and, if the effect transaction takes the lock first, the effect stands with its original identity and the change governs the next operation only
- interval boundaries evaluated at commit with the lock-time clock; exact-boundary instants characterized
- revoked in Runtime-held state while the claim-carried binding still verifies is refused at commit
- revocation present only in a below-floor trust snapshot is refused, not ignored
- reactivation, lineage or a higher epoch cannot resurrect a revoked selection, including after a Runtime-state restore; activation_state revoked mirrors the terminal revocation table
- queued job and retry after revocation are refused; stale cache never governs
- claim expiry clamped to the selection interval where the ADR chooses clamping (BLOCKED_ON_CONTRACT otherwise)
- revocation vs concurrent commit race results are repeatable across runs

**Expected negative controls (class slugs):**
- revoked_selection
- expired_selection
- concurrent_revocation
- restore_rollback
- epoch_downgrade
- stale_approval_revival
- durable_state_missing_or_corrupt

**Evidence artifacts:**
- raw per-case logs for the full run (stdout/stderr)
- junit xml per suite
- collected-test list AND executed-test list (collection is not execution)
- SHA256SUMS over all run artifacts
- environment record (interpreter, OS, dependency lock hashes, clock source)
- expectations digest (hash of the frozen oracle/control/case files)
- candidate pin record (the five head SHAs, evaluator blob, trust snapshot id)
- skip/xfail/error list preserved verbatim (a skip is not evidence)
- mutation-leg log (one refusal check disabled per case; case must fail)
- repeated-run logs (minimum run count predeclared at freeze; every run retained, single runs do not qualify) with per-run seeds/orderings
- injected clock transcript (check-time vs lock-time)
- revocation-table state before/after

**Existing test gaps:**
- D03 PASS_RECORDED for named matched-refund cases, row INCONCLUSIVE; C17 PASS_RECORDED named; all historical g8-r10
- C07 KNOWN_LIMIT_ASSERTED (residual race declared), not protection
- no test exists for registry-selection revocation/expiry at commit
- worker21 grant/evidence expiry tests cover the authority boundary, not selections; MVP v7 rows are a builder proposal awaiting review

**Missing oracle coverage candidates:**
- both-order revocation/expiry commit oracles
- lock-time boundary oracles
- resurrection controls (reactivate, lineage, higher epoch, restore)
- below-floor-snapshot revocation control
- clock-source and expiry-drop mutation controls

**Pass criteria.** All frozen QG-08 cases match in every repeated run; mutation legs (check-time clock; drop expiry comparison) fail the boundary case; designated independent lead verdict.

**Fail criteria.** A revoked or expired selection governs an effect, is resurrected, or a boundary/race result is not repeatable.

**Block criteria.** BLOCKED if claim-expiry clamping (Option C) or the residual-race disclosure are unresolved in a ruling, or EXT-S4-2/S4-4 do not exist.

**Depends on unfinished V1:** yes: EXT-S4-0, EXT-S4-2 (commit-time guard), EXT-S4-4, EXT-S4-5, EXT-S1-6 (snapshot floor)

**Reviewer requirements:** shared independence rules above apply without gate-specific additions.

### QG-09 Atomic Route B effect-boundary tests

**V1 status:** ACTIVE

**Statement.** On atomic Route B, the policy enforced at effect commit is the selected policy; a change between check and commit is refused or re-evaluated under the lock; effect, claim and budget commit together; the identity is claim-carried (mandatory) and an executor-supplied string is not authority. Route A is out of V1 and is not credited.

**Source scenarios (crosswalk evidence_status; PASS_RECORDED = named historical case at g8-r10 pins, not current heads):** C07 (KNOWN_LIMIT_ASSERTED), D07 (KNOWN_LIMIT_ASSERTED), D03 (PASS_RECORDED)

**Required assertions:**
- policy or selection changed between check and commit is refused or re-evaluated under the lock
- selection identity is claim-carried and revalidated under the lock; each comparison (claim id, policy identity, record and selection id, epoch) removed in turn makes its case fail
- executor-supplied identity string with no claim-carried binding is refused at commit; zero effect rows, claim unconsumed, budget unchanged
- same selection id with a broader profile digest, swapped trust-snapshot fingerprint, or swapped record digest after verification is refused under the lock
- if the effect transaction takes the lock first, the effect stands with its original identity
- registry unreachable during the effect transaction: outcome identical to registry reachable, and a network sentinel records no socket opened inside the transaction
- lost acknowledgement then reconcile preserves original identity; lost acknowledgement then revocation stays unresolved and not retry-eligible
- crash at each transaction stage leaves effect, claim and budget consistent
- effect, claim and budget commit atomically
- at-most-once under concurrent same-claim processes
- refusals, holds and deny-all persist with exact identity in durable failure rows

**Expected negative controls (class slugs):**
- forged_selection
- substituted_digest
- mismatched_claim_identity
- concurrent_revocation
- expired_selection
- revoked_selection
- epoch_downgrade
- restore_rollback
- durable_state_missing_or_corrupt
- string_based_decision
- route_a_not_credited
- confused_deputy

**Evidence artifacts:**
- raw per-case logs for the full run (stdout/stderr)
- junit xml per suite
- collected-test list AND executed-test list (collection is not execution)
- SHA256SUMS over all run artifacts
- environment record (interpreter, OS, dependency lock hashes, clock source)
- expectations digest (hash of the frozen oracle/control/case files)
- candidate pin record (the five head SHAs, evaluator blob, trust snapshot id)
- skip/xfail/error list preserved verbatim (a skip is not evidence)
- mutation-leg log (one refusal check disabled per case; case must fail)
- repeated-run logs (minimum run count predeclared at freeze; every run retained, single runs do not qualify) with per-run seeds/orderings
- network sentinel log for in-transaction registry reachability
- fault-injection stage record (stage, outcome, post-state)
- durable failure-row dump

**Existing test gaps:**
- existing local-authority-effect and worker21 tests establish the authority boundary, not registry policy at it (historical)
- C07 and D07 are KNOWN_LIMIT_ASSERTED; D03 PASS_RECORDED named cases at g8-r10, row INCONCLUSIVE
- R10 not implemented (GAP-G3-01/02 open); LocalExecutionPolicy.check ran outside the atomic transaction at the analysed baseline
- no test for claim-carried identity, digest swap or in-transaction reachability

**Missing oracle coverage candidates:**
- check-to-commit change oracles
- claim-carried identity and executor-string controls
- digest/fingerprint swap controls
- network-sentinel control
- fault-stage and lost-ack oracles
- per-comparison removal mutation controls

**Pass criteria.** All frozen QG-09 cases match in every repeated run with raw logs retained; each under-lock comparison mutation fails its case; designated independent lead verdict.

**Fail criteria.** A changed policy governs an effect, an executor-supplied string is accepted as authority, effect/claim/budget diverge after any fault stage, a socket opens inside the transaction, or results differ across repeated runs.

**Block criteria.** BLOCKED if R10 Option choice, the claim member list (O-3), or the Runtime destination names (O-5) are unresolved, or EXT-S4-2/S4-4/S4-5 do not exist; never reported PASS by analogy to authority-boundary tests.

**Depends on unfinished V1:** yes: EXT-S4-0, EXT-S4-2 (Runtime selection destination and commit-time guard), EXT-S4-4 (Control Plane claim-carried binding), EXT-S4-5 re-pin

**Reviewer requirements:** shared independence rules above apply without gate-specific additions.

### QG-10 Cross-component policy consistency

**V1 status:** ACTIVE

**Statement.** Control Plane decision inputs and the Runtime effective policy agree at the effect commit for registry-supplied values; any disagreement refuses and never takes the broader side. The profile snapshot hash agrees on both sides.

**Source scenarios (crosswalk evidence_status; PASS_RECORDED = named historical case at g8-r10 pins, not current heads):** D01 (PASS_RECORDED)

**Required assertions:**
- Control Plane allowed vs Runtime narrowed, and the reverse: refused, never the broader side
- a registry value consumed by one component only is refused
- profile snapshot hash identical on both sides
- grant valid with approval bound to another profile or lineage refused; grant revoked or expired with approval valid refused; and the reverse
- broken trust root, altered record or evaluator, stale caches each refuse
- positive control: consistent Control Plane and Runtime inputs permit the operation

**Expected negative controls (class slugs):**
- mismatched_claim_identity
- substituted_digest
- confused_deputy
- stale_approval_revival
- revoked_selection
- route_a_not_credited

**Evidence artifacts:**
- raw per-case logs for the full run (stdout/stderr)
- junit xml per suite
- collected-test list AND executed-test list (collection is not execution)
- SHA256SUMS over all run artifacts
- environment record (interpreter, OS, dependency lock hashes, clock source)
- expectations digest (hash of the frozen oracle/control/case files)
- candidate pin record (the five head SHAs, evaluator blob, trust snapshot id)
- skip/xfail/error list preserved verbatim (a skip is not evidence)
- mutation-leg log (one refusal check disabled per case; case must fail)
- two-sided profile hash comparison record

**Existing test gaps:**
- D01 PASS_RECORDED for the named matched-refund 'valid' variant at g8-r10 only; row INCONCLUSIVE
- no test compares Runtime-effective to Control Plane policy for registry values
- MVP v7 chain rows are a builder proposal awaiting independent review

**Missing oracle coverage candidates:**
- two-sided disagreement oracles both directions
- single-consumer value control
- grant/approval cross-validity grid
- broader-side mutation control

**Pass criteria.** All frozen QG-10 cases match at the exact pins, including the positive control; mutation leg (take the broader side) fails; designated independent lead verdict.

**Fail criteria.** Any disagreement that permits an effect, any broader-side resolution, or a hash mismatch not refused.

**Block criteria.** BLOCKED if EXT-S4-4/S4-5 (both repos re-pin) are absent or the profile snapshot hash definition is unresolved.

**Depends on unfinished V1:** yes: EXT-S4-2, EXT-S4-4, EXT-S4-5 (both repositories re-pin), EXT-S3-3/S3-4

**Reviewer requirements:** shared independence rules above apply without gate-specific additions.

### QG-11 Evidence and replay verification

**V1 status:** ACTIVE

**Statement.** Evidence names the exact registry record and selection that governed the effect (record id, version, digest, selection id, epoch); Replay, Evidence Pack and Verifier refuse a substituted or omitted policy identity; a recomputed hash is not authentication.

**Source scenarios (crosswalk evidence_status; PASS_RECORDED = named historical case at g8-r10 pins, not current heads):** C03 (PASS_RECORDED), C04 (PASS_RECORDED), C12 (PASS_RECORDED), C13 (PASS_RECORDED), C14 (PASS_RECORDED), D08 (PASS_RECORDED)

**Required assertions:**
- evidence carries record id/version/digest and selection id/epoch
- identity in evidence equals the identity that governed the effect
- substituted identity refused (differential against an accepted control)
- omitted identity refused
- recomputed hash alone does not authenticate
- refusals, holds and deny-all persist as durable negative evidence with exact identity
- evidence of a deny-all is distinguishable from an evaluator denial

**Expected negative controls (class slugs):**
- substituted_digest
- mismatched_claim_identity
- forged_selection
- required_absence
- string_based_decision

**Evidence artifacts:**
- raw per-case logs for the full run (stdout/stderr)
- junit xml per suite
- collected-test list AND executed-test list (collection is not execution)
- SHA256SUMS over all run artifacts
- environment record (interpreter, OS, dependency lock hashes, clock source)
- expectations digest (hash of the frozen oracle/control/case files)
- candidate pin record (the five head SHAs, evaluator blob, trust snapshot id)
- skip/xfail/error list preserved verbatim (a skip is not evidence)
- mutation-leg log (one refusal check disabled per case; case must fail)
- evidence bundle per case plus verifier output
- evidence-review record or an explicit 'evidence review: not performed'

**Existing test gaps:**
- C03, C04, C12, C13, C14, D08 are PASS_RECORDED for named cases at g8-r10; rows INCONCLUSIVE
- enforcement lines for non-cloned repos UNVERIFIED; F-19, ODES producer limits, route-B export/pack limits in docs/v1-known-limits.md
- no registry-identity evidence test exists

**Missing oracle coverage candidates:**
- identity-in-evidence oracles
- substitution/omission differential cases
- hash-is-not-auth control
- durable negative evidence oracles

**Pass criteria.** All frozen QG-11 cases match; accepted control passes while substituted/omitted variants are refused; review by a party other than author, builder and runner, else recorded not performed (and no Tier 1 verdict); designated independent lead verdict.

**Fail criteria.** Evidence omits or misnames the governing identity, or a substituted/omitted identity is accepted.

**Block criteria.** BLOCKED if the evidence field set for the registry identity is not defined in a contract, or Exchange/Replay/Pack/Verifier enforcement is not readable (UNVERIFIED sources in P1).

**Depends on unfinished V1:** yes: EXT-S1-5 (EffectivePolicyIdentity), EXT-S4-2/S4-4 (identity carried to the evidence-producing path); evidence-schema carriage not assigned to a named EXT card in the sources read

**Reviewer requirements:** shared independence rules above apply without gate-specific additions.

### QG-12 Independent negative tests

**V1 status:** ACTIVE

**Statement.** Hostile and malformed inputs and substitutions are refused; each negative is classified supported / unqualified / out of scope. Includes r08-v2 additivity and signing-domain separation.

**Source scenarios (crosswalk evidence_status; PASS_RECORDED = named historical case at g8-r10 pins, not current heads):** D02 (PASS_RECORDED), C02 (PASS_RECORDED), C03 (PASS_RECORDED)

**Required assertions:**
- forged, replayed, expired, unselected and re-digested records refused
- manifest and pin substitution refused
- symlink, FIFO and oversize inputs refused
- confused deputy between families refused
- dropped-field refusals
- v2-only fields refused by v1 loaders; no silent upgrade of a v1 document
- a v1 signature never verifies a v2 statement and the reverse
- each negative classified supported/unqualified/out of scope; loaded-code replacement (LIM-1) disclosed, not claimed
- mutation leg per NX control: disabling exactly one refusal check makes its case fail

**Expected negative controls (class slugs):**
- forged_selection
- substituted_digest
- mismatched_claim_identity
- expired_selection
- revoked_selection
- required_absence
- epoch_downgrade
- concurrent_revocation
- stale_approval_revival
- restore_rollback
- durable_state_missing_or_corrupt
- registry_denyall_vs_evaluator_denial
- invalid_freshness_input
- outage_extension_widening
- confused_deputy
- string_based_decision
- route_a_not_credited

**Evidence artifacts:**
- raw per-case logs for the full run (stdout/stderr)
- junit xml per suite
- collected-test list AND executed-test list (collection is not execution)
- SHA256SUMS over all run artifacts
- environment record (interpreter, OS, dependency lock hashes, clock source)
- expectations digest (hash of the frozen oracle/control/case files)
- candidate pin record (the five head SHAs, evaluator blob, trust snapshot id)
- skip/xfail/error list preserved verbatim (a skip is not evidence)
- mutation-leg log (one refusal check disabled per case; case must fail)
- negative-class classification table
- mutation-leg coverage table (control -> disabled check -> case failed)

**Existing test gaps:**
- D02, C02, C03 PASS_RECORDED for named cases at g8-r10; rows INCONCLUSIVE
- v1-probes and fix2-probes KNOWN_GAP rows are limits, not protection
- registry builder negatives are BUILDER_TESTED and excluded as a basis
- no independent adversarial run exists

**Missing oracle coverage candidates:**
- the full predeclared negative-class set (see expected_negative_controls)
- additivity and signing-domain separation controls
- symlink/FIFO/oversize controls

**Pass criteria.** Every frozen negative control (result_kind PROTECTION) produces its own frozen expected outcome and exact cause, and every mutation leg fails its case; PAIR_CONTROL rows match their expected accept or refuse leg; DISCLOSURE_ONLY rows are characterized and never counted as protection; classification table complete; designated independent lead verdict.

**Fail criteria.** Any hostile input accepted, any control without a failing mutation leg, or a limit presented as protection.

**Block criteria.** BLOCKED if a negative's supported/unqualified/out-of-scope class cannot be assigned from a contract or ruling.

**Depends on unfinished V1:** yes: EXT-S1-1/S1-3 (r08-v2), EXT-S1-7/S1-9 (real verifier, R09 battery), EXT-S4-2/S4-4

**Reviewer requirements:** shared independence rules above apply without gate-specific additions.

### QG-13 Regression and disclosure

**V1 status:** ACTIVE

**Statement.** Code-owned invariants are unchanged; known limits are listed separately and never counted as protection; failures, skips, XFAIL and NOT_RUN are preserved. The r08-v1 goldens, tests and frozen artefacts are byte-identical after r08-v2 lands; engine/safe_executor.py is unchanged.

**Source scenarios (crosswalk evidence_status; PASS_RECORDED = named historical case at g8-r10 pins, not current heads):** D01 (PASS_RECORDED), C02 (PASS_RECORDED), C12 (PASS_RECORDED), C13 (PASS_RECORDED), C14 (PASS_RECORDED), D07 (KNOWN_LIMIT_ASSERTED), C07 (KNOWN_LIMIT_ASSERTED), C10 (KNOWN_LIMIT_ASSERTED), C11 (KNOWN_LIMIT_ASSERTED)

**Required assertions:**
- preserved Runtime and Control Plane test sets rerun at the exact pins with statuses preserved
- engine/safe_executor.py blob equals the candidate pin and the frozen-artifact blob checks rerun
- r08-v1 goldens, codes and frozen artefacts byte-identical after r08-v2; never edited to obtain a pass
- known-limit tests (D07, C07, C10, C11) reported in a separate disclosure list, not counted as protection
- the 11 undeclared Runtime known-limit tests declared by their owner before the run (GAP-G4-07)
- an MVP oracle row for a LocalExecutionPolicy denial exists (GAP-G4-09)
- skips, XFAIL, errors and NOT_RUN preserved verbatim

**Expected negative controls (class slugs):**
- route_a_not_credited
- registry_denyall_vs_evaluator_denial
- restore_rollback

**Evidence artifacts:**
- raw per-case logs for the full run (stdout/stderr)
- junit xml per suite
- collected-test list AND executed-test list (collection is not execution)
- SHA256SUMS over all run artifacts
- environment record (interpreter, OS, dependency lock hashes, clock source)
- expectations digest (hash of the frozen oracle/control/case files)
- candidate pin record (the five head SHAs, evaluator blob, trust snapshot id)
- skip/xfail/error list preserved verbatim (a skip is not evidence)
- mutation-leg log (one refusal check disabled per case; case must fail)
- byte-identity hash table for frozen artefacts
- disclosure list of known limits

**Existing test gaps:**
- D01, C02, C12, C13, C14 PASS_RECORDED named cases at g8-r10; D07, C07, C10, C11 KNOWN_LIMIT_ASSERTED
- no run at current heads; 11 Runtime known-limit tests undeclared
- no MVP row for a LocalExecutionPolicy denial

**Missing oracle coverage candidates:**
- byte-identity oracle for r08-v1 artefacts
- evaluator-blob unchanged oracle
- limit-disclosure completeness oracle
- LocalExecutionPolicy-denial row

**Pass criteria.** Preserved sets and byte-identity checks match at the exact pins with no unexplained skip; disclosure list complete; designated independent lead verdict.

**Fail criteria.** Any code-owned invariant changed, any known limit counted as protection, any hidden skip, or any frozen artefact edited.

**Block criteria.** BLOCKED if GAP-G4-07 declaration or GAP-G4-09 row is not made before the run, or the exact candidate pins are not recorded.

**Depends on unfinished V1:** yes: EXT-S1-3 (r08-v2 landed), EXT-S6-2 full exact-pin run; owner actions GAP-G4-07/09

**Reviewer requirements:** shared independence rules above apply without gate-specific additions.

### QG-14 Process: exact-head independent run by designated owner

**V1 status:** ACTIVE

**Statement.** Every ACTIVE gate has a PASS at the exact candidate pins, run by a designated independent qualifier; INACTIVE gates (QG-02 while max_amount is deferred) are reported as inactive, never as PASS. This is the process gate; it cannot be met by tests alone.

**Source scenarios (crosswalk evidence_status; PASS_RECORDED = named historical case at g8-r10 pins, not current heads):** none (process gate)

**Required assertions:**
- written designation of an independent lead naming the lead and an independence statement from builder, Architect, oracle author, Copilot and dependent workers
- freeze commit in the qualification repo with expectations digest and candidate SHAs, dated before execution
- execution record with raw logs and SHA256SUMS
- evidence review by a separate party or recorded 'not performed'
- key and snapshot custody recorded as 'not performed' (no operational trust root in V1), never a gate or PASS
- amendments dated and recorded, never made to obtain a pass
- QG-02 reported INACTIVE_MAX_AMOUNT_DEFERRED

**Expected negative controls (class slugs):**
- none

**Evidence artifacts:**
- designation record
- freeze commit reference
- execution record
- SHA256SUMS
- evidence-review record or not-performed note
- status report with per-gate state

**Existing test gaps:**
- no independent qualification owner is designated; no run at any V1 candidate; nothing here is evidence

**Missing oracle coverage candidates:**
- process checks only (designation, freeze, execution record); no behavioural oracle belongs to this gate

**Pass criteria.** All ACTIVE gates PASS at the exact pins under a designated independent lead, QG-02 inactive, evidence retained. Not reachable until V1 is implemented.

**Fail criteria.** A verdict by a non-independent party, a gate reported met without an exact-pin run, QG-02 counted as PASS, or edits to expectations after seeing results.

**Block criteria.** BLOCKED while no independent lead is designated (GAP-G4-13): the candidate reads 'OCS-only V1: NOT INDEPENDENTLY QUALIFIED'.

**Depends on unfinished V1:** yes: All V1 implementation PRs (S1-S4), designation of the lead, EXT-S5-1/S5-6, EXT-S6-x

**Reviewer requirements (gate-specific):** Only the operator designates the lead; if none by S5 exit, escalate as a boundary change, not a technical question. Shared rules above apply.

## Future source pins (filled at freeze; identical placeholders for every gate)

| Pin | Value |
|---|---|
| control_plane_head | TO_BE_FILLED_AT_FREEZE |
| runtime_head | TO_BE_FILLED_AT_FREEZE |
| registry_head | TO_BE_FILLED_AT_FREEZE |
| qualification_head | TO_BE_FILLED_AT_FREEZE |
| evaluator_blob | TO_BE_FILLED_AT_FREEZE (analysed baseline 2fc880da) |
| trust_snapshot_id | TO_BE_FILLED_AT_FREEZE |

Analysed baselines (Runtime `c5e97e87`, Control Plane `7a4bcd40`, registry `d2c472e4`, qualification `be1994a9`, blob `2fc880da`): analysed baseline only, not the candidate.

## Coverage computed by script

Counts of oracles (QO), negative controls (NC) and differential cases (DF) per gate are generated by the integration lead from `data/oracles.jsonl`, `data/negative-controls.jsonl` and `data/differential-cases.jsonl` into `04a-computed-coverage.md`. No counts are written in this file. A gate with zero computed coverage is reported as uncovered, not as passing.

## Preparation, not qualification

This document defines what a future independent run must evidence. It is preparation only. No gate is met, no test was executed for it, and nothing here supports a Tier 1, release or publication claim.
