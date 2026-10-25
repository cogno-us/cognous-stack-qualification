# 04 Genuine OCS V1 qualification gaps

**Status: documentation-only analysis. Non-authorizing. Draft for Architect review. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.**

Nothing here authorizes a migration, approves a pin, selects or activates a record, or changes a qualification verdict. Implementation is not authorized. A gap is listed only if no existing capability in [03](03-reuse-and-duplication-matrix.md) can carry it. Labels as in [01](01-existing-ocs-capabilities.md).

## 1. Where the fourteen gates are defined

`QG-01..QG-14` are defined in the merged P1 execution plan in `cognous-ocs-registry`, `docs/p1-extraction-plan/data/qualification-gate-matrix.json` (14 rows; file sha-256 `e81b5fad1dfcc9bcb002111a17e7bd79117efa53cfc81b3198fbcb75b2dd04bd`, at registry main `d2c472e4a09543228bad62235e07a0dedfd7f48b`, the PR #22 merge). They are derived there from the 13 proposed-not-adopted V1-M/R/C gates in this repository's [`06-v1-acceptance-matrix.md`](../registry-v1-scope-assessment/06-v1-acceptance-matrix.md); the plan keeps the count at 14 and rejects proposed QG-15 and QG-16. **SOURCE FACT**

None of the fourteen is defined, named or machine-readable in this repository (`grep QG-[0-9]` finds nothing outside this package). "Existing" therefore means *defined in the merged plan*, not *run*: every gate is `qualified: false` and `PREPARE_ONLY_UNTIL_INDEPENDENT_LEAD_DESIGNATED`. **SOURCE FACT**

## 2. Coverage by gate, qualification-side

Coverage counts only tests that exist in *this* repository. Builder tests in the registry repository (`BUILDER_TESTED`, using a `FakeVerifier`) are shown separately and do not count as qualification-side coverage. PARTIAL means adjacent, reusable tests exist. It never means a gate passed. Counts are references listed by the plan, not distinct tests. **REASONED INFERENCE** (reading only; no suite was run)

| Gate | Plan status | Existing refs (qual / registry builder) | New items | Qualification-side coverage | Basis |
|---|---|---|---|---|---|
| QG-01 | ACTIVE | 4 / 4 | 8 | **PARTIAL** | Refusal oracles for all five allowlists exist (Q04). No test builds a policy from a registry record; no grid; no deny-all test. |
| QG-02 | INACTIVE_MAX_AMOUNT_DEFERRED | 5 / 0 | 7 | **INACTIVE** | max_amount is deferred and not in V1. Existing C11[max_amount], C16, C18 stay as they are. Reported inactive, never PASS. |
| QG-03 | ACTIVE | 5 / 0 | 13 | **PARTIAL** | Adjacent tests exist for the boundary pattern and current bounds (Q06). No approval-age behaviour test, no registry-narrowed bound, no extension-ceiling test. |
| QG-04 | ACTIVE | 2 / 0 | 9 | **PARTIAL** | Thin: two references. TC-L05-013 is NOT_RUN and cannot detect the bounded_tolerance toggle (GAP-G4-05). |
| QG-05 | ACTIVE | 0 / 7 | 18 | **NONE** | No qualification-repository test. Builder tests in the registry repo use a FakeVerifier. |
| QG-06 | ACTIVE | 1 / 4 | 8 | **PARTIAL** | Thin: TC-L05-013 only. Builder tests are at decision-function level, none at an effect boundary. |
| QG-07 | ACTIVE | 0 / 4 | 5 | **NONE** | Builder tests only, 2 to 3 values per field. Consumer path has no caller. |
| QG-08 | ACTIVE | 5 / 3 | 11 | **PARTIAL** | Adjacent authority-level revocation and expiry tests exist (Q09). No selection-level test. |
| QG-09 | ACTIVE | 4 / 0 | 12 | **PARTIAL** | Adjacent atomic authority-boundary tests exist (Q08). Not registry policy at that boundary; policy check runs outside the transaction (GAP-G3-02). |
| QG-10 | ACTIVE | 3 / 0 | 6 | **PARTIAL** | Thin: MVP chain rows are builder proposals; no test compares Runtime-effective policy with Control Plane policy for registry values. |
| QG-11 | ACTIVE | 7 / 0 | 4 | **PARTIAL** | Refusal and evidence substitution tests exist (Q12). None carries a registry record or selection identity. |
| QG-12 | ACTIVE | 2 / 3 | 10 | **PARTIAL** | Thin: v1-probes and fix2-probes KNOWN_GAP rows are limits, not protection. No independent adversarial run. |
| QG-13 | ACTIVE | 10 / 1 | 5 | **PARTIAL** | Most existing tests are reusable for a rerun at exact pins. 11 undeclared Runtime known-limit tests and GAP-G4-09 come first. |
| QG-14 | ACTIVE | 0 / 0 | 5 | **NONE** | Process gate. No independent lead designated (GAP-G4-13). |

Totals: 74 existing references (48 qualification, 26 registry builder); 121 predeclared new-test items, of which 114 belong to the 13 active gates and 7 to inactive QG-02. Coverage: 10 PARTIAL, 3 NONE (QG-05, QG-07, QG-14), 1 INACTIVE (QG-02).

**QG-02 stays INACTIVE.** `max_amount` is deferred and not in V1. The existing C11 `[max_amount]`, C16, C18 and TC-L06-014/016/024 references are untouched. QG-02 is reported inactive and is never counted as PASS, skipped-as-pass or covered (as QG-14 requires).

## 3. Gaps by V1 scope item

Severity is the effect on whether the item can be qualified at all. "Blocked" means there is nothing to execute until a planned component exists; it is not a defect in this repository.

| # | Gap | Scope item | Gates | Blocked on | Severity |
|---|---|---|---|---|---|
| G-A | Registry-sourced values never reach enforcement: `apply_registry_overlay` has no caller. No test builds a `LocalExecutionPolicy` from a registry record, covers superset, narrowing or empty-set per allowlist, or deterministic refusal on bad registry data | five Runtime allowlists | QG-01, QG-07 | the Runtime narrowing adapter (planned) | High |
| G-B | Pre-construction deny-all is untested and not distinguished from a `LocalExecutionPolicy.check` denial (OPEN-Q6). No MVP oracle row exists for a `LocalExecutionPolicy` denial (GAP-G4-09) | five Runtime allowlists; durable negative evidence | QG-01, QG-13 | G-A | High |
| G-C | Approval-age behaviour has no test; `approval_max_age_seconds` appears only as a forwarded parameter. No test that a registry-supplied bound narrows only, honours a code floor, or composes with a signed outage extension (extension must never exceed `min(caller, registry)`) | three CP freshness bounds | QG-03, QG-04 | the Control Plane age-bound helper, host factory and per-class narrowing (planned) | High |
| G-D | Changing a per-class bound forces re-approval (E3 shows `runtime_authority_approval_mismatch`). No test that withdrawing a narrowing does not revive an older approval | three CP freshness bounds | QG-04 | G-C | Medium |
| G-E | The local policy check runs before the destination transaction (GAP-G3-02; R10 Options A/B/C unimplemented). No test races a policy or selection change against the transaction, and none can pass today | atomic Route B only | QG-09 | the Runtime selection destination and commit-time guard (planned) | High |
| G-F | No claim field or test carries an effective-policy identity (governing record and version, selected policy and epoch, scope, configuration digest, activation identity, trust snapshot). Executor-supplied identity strings with no claim-carried binding are untested | claim-carried identity | QG-09, QG-10, QG-11 | the typed identity contract and the Control Plane claim-carried binding (planned, mandatory) | High |
| G-G | No qualification-side test of authenticated selection: supersession, epoch ordering, withdrawal, required-scope ratchet, sync that never manufactures authorization. Builder tests use a `FakeVerifier`, not cryptography. One builder expectation (QS13) was amended after behaviour was seen | authenticated selection and activation | QG-05, QG-06, QG-12 | the real signature verifier and the activation state (planned) | High |
| G-H | Required-policy refusal cannot be detected at the effect boundary: TC-L05-013 is NOT_RUN and cannot detect the `bounded_tolerance` toggle (GAP-G4-05) | authenticated selection and activation | QG-06 | G-G | Medium |
| G-I | No selection-level revocation, expiry, stale or swapped epoch, or terminal-revoked test. Authority-level coverage exists but must not be reported as selection-level by analogy | revocation, expiry, rollback | QG-05, QG-08 | G-E, G-G | High |
| G-J | Rollback and restore: T10 shows rollback is undetected without an external anchor. A restored selection store older than a revocation or higher epoch must fail closed until re-baselined; that is a V1 disclosure plus a test, not a claim of rollback prevention | revocation, expiry, rollback | QG-05, QG-08, QG-13 | G-G | Medium |
| G-K | Registry codes as structured negative evidence: no test that the original code survives mapping to an existing refusal category, that every code in the map has a typed refusal, or that no decision reads message text | durable negative evidence | QG-06, QG-11, QG-12 | the outcome map (planned) | Medium |
| G-L | Evidence names no registry record or selection identity; Replay, Evidence Pack and Verifier refusal of a substituted or omitted identity is untested | durable negative evidence; claim-carried identity | QG-11 | G-F | Medium |
| G-M | The fourteen gates are not machine-readable in this repository, so "QG-02 INACTIVE" and "no new status" cannot be checked here | existing fourteen gates | QG-14 | nothing | Low |
| G-N | Process: no independent qualification lead is designated (GAP-G4-13). All S5 work is PREPARE-only and labelled "builder-side inspection; Tier 1 not qualified" | all | QG-14 | operator or Architect designation | Blocking for any verdict |
| G-O | 11 Runtime known-limit tests are undeclared (GAP-G4-07) and must be declared by the owner before the exact-pin run | existing gates | QG-13 | owner action | Medium |

## 4. What is not a gap

- **A new evidence format, record kind or status.** None is needed (rows Q02, Q24, Q25).
- **A new harness for refusal, atomicity or revocation.** Q08, Q09 and Q12 already provide the fixtures; the missing content is cases.
- **Approval-history migration.** The Architect ruled no automatic approval revival and no generalized migration in V1; the required negative case (narrowed, approval invalidated, narrowing withdrawn, old approval stays invalid) is a single new case under QG-04.
- **A capture-allowlist change.** Not needed if the registry-subject workflow lives here (doc 05).
- **Anything in ISSBench.** It offers no revocation, rollback or freshness mechanism to fill G-I, G-J or G-C (doc 02, section 5).

## 5. Execution realities that limit reuse

These do not add gaps but constrain how the existing tests can be run for V1. **SOURCE FACT**

- Many suites hard-fail when checkout variables are unset (`MVP_*_DIR`, `ADV_*_DIR`, `ARB_REFUSAL_CP_ROOT`, `ARB_REFUSAL_EXECUTOR_ROOT`, `ARB_PINNED_MANIFEST_FIXTURE`); one copy of the refusal-evidence test asserts, another skips.
- Atomic Route B tests are skipped when `agent_control_plane` is not importable. A green Runtime check is not evidence by itself.
- `mvp-d2-route-b` and `mvp-d09` need pydantic 2.12 or later. Lock `a9a750` provides 2.13.5; two other locks pin 2.11.9.
- Some `operation-identity` tests are designed to fail on specific Runtime or Control Plane pins, so reuse requires a pin check.
- Historical results are at the g8-r10 controller pins (Control Plane `0a41faa9`, Runtime `ec728da6`), not at Control Plane `7a4bcd40` or Runtime `c5e97e87`. No scenario-level PASS exists and nothing is recorded at the current heads.
