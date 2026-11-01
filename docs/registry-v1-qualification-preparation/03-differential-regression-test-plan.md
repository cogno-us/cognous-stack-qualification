# 03 Differential regression test plan (frozen evaluator vs proposed configuration adapters)

Status: **PREPARATION ONLY. This is not qualification. Nothing was run.** No V1 candidate exists. No test in this plan was collected or executed; no result, pass, fail or count of passing tests is claimed. Expected results are fixed from the FROZEN baseline (source read at the pins) and from approved contracts and rulings, never from candidate behaviour. Independent Tier 1 qualification is not claimed (no designated independent lead; Copilot review is technical review, not qualification). RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.

Lane C of the registry V1 qualification preparation. Companion data: [`data/differential-cases.jsonl`](data/differential-cases.jsonl) (103 cases, `DF-001` to `DF-103`).

## 1. Scope and pins

| Item | Value |
|---|---|
| V1 fields | Runtime: `allowed_actions`, `allowed_adapters`, `allowed_units`, `allowed_institutions`, `allowed_authority_domains`. Control Plane: `status_max_age_seconds`, `approval_max_age_seconds`, `ActionClass.max_status_age_seconds` |
| Execution boundary | Atomic Route B only. Route A existing behaviour is characterized as OUT OF V1 and earns no credit |
| Excluded | `max_amount` (QG-02 INACTIVE: retained, never counted PASS; no oracle or control is written for it; it appears only as an opaque caller field that must pass through unchanged) |
| Runtime pin | `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f`; `engine/safe_executor.py` blob `2fc880dae37eac76e5074533435740ce0684209d` (re-computed from the pin in this lane) |
| Control Plane pin | `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` |
| Registry | main `d2c472e4a09543228bad62235e07a0dedfd7f48b` (r08-v1 regression rows only) |
| Historical test pins | `PASS_RECORDED` means a named historical case at the g8-r10 controller pins (Control Plane `0a41faa9`, Runtime `ec728da6`), not at the pins above |

Other frozen-file blob ids computed from the pins (read-only `git fetch --depth=1`, `git show`, `git hash-object`): Runtime `engine/control_plane_adapter.py` `c3d1940d8ad676f5623ebda59167d3ce9d9fc44f`; Runtime `engine/atomic_local_control_plane_executor.py` `d5ff31359f2d510a2e1573d2bc322ec0a75b6956` (expected to change under EXT-S4-2; therefore no UNCHANGED_FILE row); Control Plane `bounded.py` `2cc8d998ff0a8fec3112a8b0634111fcf8fbef17`; `runtime_authority.py` `fffc7d3b7be8752dfbb4797b100c848140205310`; `local_authority_effect.py` `8203d652401d14e444933b6355472843ee844a40` (expected to change under EXT-S4-4; no UNCHANGED_FILE row).

## 2. Method

1. **Baseline first.** For every case the frozen evaluator behaviour is characterized from source at the pin (file:line recorded in `baseline_source`), including the existing test that bears on it and that test's true historical status. Source reading is not execution.
2. **Expected result source is always `frozen baseline`.** Where a comparison needs concrete expected values, the independent oracle builds a *reference* object by calling the frozen evaluator directly (for example `dataclasses.replace(caller_policy, **effective_sets)` and `LocalExecutionPolicy.check`, or a `BoundedAuthorizationWorkflow` constructed with the literal narrowed integer) and records its output *before* any candidate exists. The adapter output is only ever compared with that recorded value.
3. **Mismatch is FAIL of the candidate.** A mismatch is never resolved by editing the expectation. An expectation is amended only by a dated, recorded amendment made for a stated contract reason, never to obtain a pass. A mapping the contract cannot represent is **BLOCKED** (`BLOCKED_ON_CONTRACT`), not waived and not guessed.
4. **Comparison types.** BYTE_IDENTICAL, REASON_EQUIVALENT, NARROWER_ONLY, UNCHANGED_FILE, KNOWN_LIMIT_PRESERVED, CHECK_ORDER_PRESERVED (table in section 4). NARROWER_ONLY is used where the adapter has no equivalent evaluator reason: it asserts denial and absence of widening, not reason-text equality (OPEN-Q6: a registry preconstruction deny-all is distinct from a `LocalExecutionPolicy.check` evaluator denial).
5. **Reason equivalence is for non-empty effective sets only.** An empty effective set is deny-all decided before a policy object is built (the Runtime accepts empty frozensets; refusing them is an adapter convention). Those cases assert denial, zero effects, claim not consumed and budget unchanged.
6. **No string-based security decisions** (OPEN-Q3): reason strings are compared by the oracle as recorded evidence; no case permits a production decision to depend on parsing a reason string.
7. **Independence.** Nothing here was derived from registry builder tests or oracles (see section 9).

### Interpretation recorded for "both effective-set grids"

The lane brief names two effective-set grids without defining them. This plan reads them as: **Grid A**, the per-field effective-set relation grid (equal, strict subset, empty, and non-subset forms that the adapter must refuse), one case per field; **Grid B**, a single cross-field operation-verdict grid over a fixed operation battery with all five sets narrowed together. The caller x registry composition (intersection) itself is registry-side (QG-07 / S05) and is not re-derived here. If the lead intends a different pair, the case rows are individually re-taggable without changing expectations.

## 3. What is preserved (the differential's invariants)

- **Existing refusal semantics:** the ten evaluator reasons and the Route B record mapping (`policy_denial` / `local_policy_rejected`; `evaluation_error` / `local_policy_evaluation_error`).
- **Evaluator ordering:** ceiling validation, institution, domain, adapter, action, target, unit, amount, exactly-one-effect, effect count; first failure wins; exact membership.
- **Construction rules:** `__post_init__` set validation; empty frozenset accepted (deny-all for that dimension); omitted constructor argument is a `TypeError`.
- **Valid-flow byte identity** (Runtime preserved list): `test_valid_flow_byte_identity`, `test_atomic_route_valid_flow_identity`, `test_route_a_local_policy_reason`, `test_security_admission`, `test_r2_atomic_operation_identity`, `test_atomic_post_commit_fault_injection`, `test_atomic_post_commit_unresolved`, `test_crashed_holder`, `test_atomic_grant_status_and_envelope_binding`, `test_atomic_approval_status_terminality`, `test_atomic_approval_terminality_flow`, `test_public_runtime_surface`; Control Plane preserved list (FS-CP). A skipped run is not evidence; no atomic test may be skipped for a missing Control Plane.
- **Control Plane age semantics:** `_fresh` inclusive `<=`, future tolerance, per-consumer reason strings, profile dump and `approval_commitment` bytes, `runtime_authority_approval_mismatch`, `AttemptJoin.class_max_age`, dispatch deadline.
- **Registry r08-v1:** goldens, 46-code vocabulary, frozen sets `registry_contract/`, `registry_consumer/`, `baseline/`, existing r08/s0x expectations unedited.
- **Frozen files:** `engine/safe_executor.py` blob `2fc880da`, plus the Control Plane and adapter files in section 1.
- **Provenance:** every baseline records repo, pin, file:line, existing test ids and their true status.

## 4. Cases by comparison type

| comparison_type | Cases | Meaning |
|---|---|---|
| BYTE_IDENTICAL | 32 | Candidate output (records, bytes, verdicts) must equal the frozen baseline exactly. |
| REASON_EQUIVALENT | 10 | Same denial and same reason text / code string as the frozen evaluator for the same effective input. |
| NARROWER_ONLY | 38 | Candidate may only refuse earlier or more; any acceptance the baseline would refuse is a FAIL (no widening). |
| UNCHANGED_FILE | 9 | A frozen file or tree has the same blob/tree id as at the pin. |
| KNOWN_LIMIT_PRESERVED | 7 | A disclosed limit is carried forward unchanged; never PASS. |
| CHECK_ORDER_PRESERVED | 7 | Evaluator first-failure ordering unchanged. |
| **Total** | **103** | 98 PREPARED, 5 BLOCKED_ON_CONTRACT |

### By scope

| scope | Cases |
|---|---|
| V1_ROUTE_B | 42 |
| CONTROL_PLANE_HOST_FACTORY | 35 |
| ALL_ROUTES_SOURCE_FILE | 9 |
| ROUTE_A_OUT_OF_V1_CHARACTERIZATION_ONLY_NOT_CREDITED | 8 |
| REGISTRY_REPO_V1_REGRESSION | 7 |
| DIRECT_CONSTRUCTION_NO_ADAPTER | 2 |

Route A rows (`ROUTE_A_OUT_OF_V1_CHARACTERIZATION_ONLY_NOT_CREDITED`) are retained only so that an accidental change to Route A is detected. They never count toward QG-01, QG-09 or QG-10. `DIRECT_CONSTRUCTION_NO_ADAPTER` rows characterize the unchanged evaluator when a host builds the workflow with literal values and no adapter.

### By field

| field | Cases |
|---|---|
| ActionClass.max_status_age_seconds | 16 |
| NONE | 59 |
| allowed_actions | 3 |
| allowed_adapters | 3 |
| allowed_authority_domains | 3 |
| allowed_institutions | 5 |
| allowed_units | 3 |
| approval_max_age_seconds | 4 |
| status_max_age_seconds | 6 |

`NONE` rows are cross-field, ordering, file-identity, claim-path, registry-additivity or known-limit rows.

### Case index

| Group | Case ids |
|---|---|
| Runtime per-dimension denial, one per field | DF-001 to DF-005 |
| Runtime effective-set Grid A (per field) and Grid B (cross-field) | DF-006 to DF-011 |
| Runtime check order | DF-012 to DF-018 |
| Runtime empty-set deny-all (per field and all five), omitted argument, malformed sets, exact membership, caller not mutated, subset re-check, exactly five keys, `type(caller)`, `__post_init__` re-run, non-V1 fields pass-through | DF-019 to DF-033 |
| Route B record shape and evaluation-error mapping | DF-034, DF-035 |
| Blocked Runtime mappings | DF-036, DF-037 |
| Route A characterization and route differential (out of V1, not credited) | DF-038 to DF-042 |
| Frozen file identity (`safe_executor.py` blob and three others) | DF-043 to DF-046 |
| Runtime preserved tests (valid-flow identity, atomic identity, admission, atomic boundaries, terminality, Route A reason) | DF-047 to DF-052 |
| Control Plane no-registry-input byte identity and per-call view | DF-053 to DF-056 |
| Control Plane narrowed-refuses-earlier, per consumer | DF-057 to DF-062 |
| Required-and-invalid, invalid caller; blocked age mappings | DF-063 to DF-068 |
| Boundary grids, tolerance, zero-bound and non-finite characterization | DF-069 to DF-074 |
| Class bounds: independence, unknown class, irreversible, extension limit, dispatch deadline, twice-the-bound, cached purpose, `AttemptJoin.class_max_age` | DF-075 to DF-082 |
| Profile dump, `approval_commitment`, approval mismatch, F4/F5 independence, unregistered ages, no cross-bound or floor | DF-083 to DF-089 |
| No-binding claim path; Control Plane preserved set | DF-090, DF-091 |
| Historical known limits C07, C10, C11, D07 | DF-092 to DF-095 |
| Registry r08-v1 golden and additivity; frozen sets; unedited tests; vocabulary; version separation | DF-096 to DF-102 |
| Candidate requirement: no approval revival after a narrowing is withdrawn (ruling) | DF-103 |

## 5. Baseline characterization summary (source at the pins)

**Runtime `LocalExecutionPolicy` (`safe_executor.py`).** Frozen dataclass (358-359); `__post_init__` (374-394) requires each of the five set fields to be an exact `frozenset` of non-empty `str` (no emptiness check, so empty is accepted), a non-empty prefix tuple and a valid `target_match`. `check` (410-430) runs `_strict_finite_number(max_amount)` and `_strict_positive_int(max_effects)` first (ValueError before any set test), then institution (413), authority domain (415), adapter (417), action (419), target (421), unit (423), amount (425), `effects != 1` (427), effect-count (429). Reason texts: `local institution restriction`, `local authority-domain restriction`, `local adapter restriction`, `local action restriction`, `local target restriction`, `local unit restriction`, `local amount restriction`, `local adapter supports exactly one effect`, `local effect-count restriction`. Call sites: Route B `atomic_local_control_plane_executor.py:69-83` (PermissionError becomes `policy_denial`/`local_policy_rejected`, any other exception `evaluation_error`/`local_policy_evaluation_error`, via `_denied` 180-209, no attempt, no claim consumption); Route A `control_plane_adapter.py:94-105` and `safe_executor.py:888-894` (out of V1). The independent trusted-context check (`control_plane_adapter.py:87-92`) exists on Route A only; the atomic executor has no equivalent (see blocked case).

**Control Plane (`bounded.py`, `runtime_authority.py`).** `_fresh` (bounded.py:2017-2024) returns false for an observation more than `clock_tolerance_seconds` in the future, else `(now - observed).total_seconds() <= max_age_seconds` (inclusive); under the freshness profile it also appends `observed + max_age` to the deadline collector. Constructor stores `status_max_age_seconds` (1271, 1295) and `approval_max_age_seconds` (1274, 1298) unvalidated. Consumers: grant status profile-less 2398-2400 (reason `grant_status_stale_or_future`); grant status with profile 2393-2400 via the class bound; conflict 2445 (`conflict_status_stale_or_future`); policy 2469 (`policy_status_stale_or_future`); approval 2505 (`approval_status_stale_or_future`). `ActionClass.max_status_age_seconds` is `Field(default=60, ge=0)` (runtime_authority.py:87). `AttemptJoin.class_max_age` records the profile base (bounded.py:1623). Dispatch deadline is `opened + class bound` (2088). Cached-purpose bound is `cl.max_status_age_seconds` (runtime_authority.py:341). `approval_commitment` hashes the profile dump, runtime-authority context, purpose ref and grant expiry (186-194); a mismatch yields `runtime_authority_approval_mismatch` (268-271); the F4 ages are constructor attributes outside that hash.

## 6. Historical known limits preserved (true status)

Known-limit assertions are never PASS. These rows carry the limit forward and must appear apart from any pass count in every status report. Crosswalk `evidence_status` for C07, C10, C11 and D07 is `KNOWN_LIMIT_ASSERTED`; the scenario rows stay INCONCLUSIVE; D01, D03 and D04 stay INCONCLUSIVE.

| Case | Title | existing_test_status |
|---|---|---|
| DF-074 | Non-finite and overflow caller bounds are characterized limits of the unvalidated constructor, preserved as limits (not protection) | NO_TEST |
| DF-080 | Twice-the-bound dispatch characteristic is preserved and scales with the narrowed bound (never beyond twice the caller bound) | NO_TEST |
| DF-086 | Baseline characterization only: the commitment is a function of the profile dump, so an approval re-matches the profile it was issued under; this is not the candidate requirement (DF-103) | NO_TEST |
| DF-092 | Known limit C07 (concurrent authority change): residual check-to-commit race stays disclosed; assertion is not PASS | KNOWN_LIMIT_ASSERTED |
| DF-093 | Known limit C10 (executor confinement): no OpenShell destination / container isolation in the reference; not protection | KNOWN_LIMIT_ASSERTED |
| DF-094 | Known limit C11 (credential and permission boundaries): no credential broker; local-credential holder bypass is characterised; allow-list narrowing is not a credential boundary | KNOWN_LIMIT_ASSERTED |
| DF-095 | Known limit D07 (restore boundary): no external anchor; some restores re-admit effects after history erasure; revoked-set rollback is disclosed | KNOWN_LIMIT_ASSERTED |

The first three rows of this table (DF-074, DF-080, DF-086) are Control Plane characterized limits (non-finite and overflow bounds, twice-the-bound dispatch, the commitment re-match characterization), which are source-characterized and **not** historical crosswalk limits; DF-092 to DF-095 (C07, C10, C11, D07) are the historical crosswalk limits (`docs/v1-known-limits.md` lines 47, 50, 51, 40). No existing assertion is reclassified.

### `existing_test_status` legend

`PASS_RECORDED(historical, g8-r10 pins)`: a named historical case passed at the g8-r10 pins; not at the current pins; the scenario row stays INCONCLUSIVE. `KNOWN_LIMIT_ASSERTED`: crosswalk row classed as an asserted limit (C07, C10, C11, D07); the C11-mapped tests listed against set-denial cases inherit that row status. `NO_TEST`: no crosswalk-mapped test for the case; where `existing_test_ids` lists a test that exists in a pinned component repository (for example `tests/test_freshness.py::...`), it is a source-side test that is not mapped in the crosswalk and has no recorded run in the inventory; collection is not execution. `NOT_RUN` crosswalk rows (TC-L06-009/011/013/014/015, TC-D09-009/016, H01) appear only in `crosswalk_scenario_ids` and have no recorded run.

| existing_test_status | Cases |
|---|---|
| NO_TEST | 77 |
| KNOWN_LIMIT_ASSERTED | 24 |
| PASS_RECORDED(historical, g8-r10 pins) | 1 |

## 7. Blocked and unrepresentable mappings

A blocked case has no executable expectation until the named contract decision exists. It is never waived and never counted.

| Case | Mapping | Blocked on |
|---|---|---|
| DF-036 | Pre-construction deny-all: durable record code and shape for an empty-effective-set denial on Route B | LD-02 outcome map ratification (EXT-S1-1 / EXT-S4-0 ADR): runtime reason code and failure_class for registry_deny_all; OPEN-Q6 |
| DF-037 | Route B trusted-context independence for institution/domain: no frozen Route B baseline check exists | Route B institution/domain independent-binding contract (EXT-S4-0 integration ADR; EXT-S4-4 claim-carried binding) |
| DF-066 | No-registry-input path with a caller age value outside the helper's valid domain (0, float, bool, inf, nan): behaviour undecided | ADR (EXT-S1-1) / S3-2 ruling: whether the no-registry-input path validates the caller value (and refuses 0, bool, float, inf) or passes it through byte-identically |
| DF-067 | Upper bound / ceiling constants for the age slots (above-maximum, 2**53, 10**30 cases) | O-4 age ceiling constants (EXT-S1-1 ADR) |
| DF-068 | Stable refusal / HOLD code names for invalid age inputs and for registry_value_not_narrowing | EXT-S1-1 ADR: closed code names and outcome (HOLD/REFUSE) per invalid-age class; LD-02 ratification |

Further notes on mappings that are prepared but depend on builder-chosen values (these are not blocked, but the oracle author must fix the values before the freeze): the narrowed integer values used in boundary grids (any valid N >= 1); the closed code names used in refusals are compared as recorded, not assumed. The "required and invalid" cases assert the outcome class (HOLD-class, no workflow built, never the caller value or the code default) and not a code name.

## 8. Rows that need a candidate that does not exist yet

All rows are NOT_RUN. Rows on the Runtime adapter need EXT-S1-3 / EXT-S2-2; Control Plane rows need EXT-S3-2 to EXT-S3-4; claim-path rows need EXT-S4-4 and EXT-S4-2; registry rows need r08-v2 (EXT-S1-1/S1-3). Characterization rows on frozen files (blob checks, preserved tests) can be fixed at once, but even those are only executed by a designated independent lead at exact pins. No row is to be executed against an unfinished component.

## 9. Sources used, independence and contamination

Used: P1 plan (`docs/p1-extraction-plan/` 02, 03, 04, 06, 07, 10, 11, `data/ld02-outcome-map.json`); inventory baseline (`canonical-scenario-crosswalk.csv`, `docs/v1-known-limits.md`); frozen evaluator source at the two pins; Runtime and Control Plane test files at the pins for function names and provenance only.

Not used to set any expectation: registry `tests/test_r08_*`, `tests/test_s05_*`, `tests/s05_oracle.py`, `r08_support.py`, `docs/r08-s01/qualification-spec.md`. Only the directory listing of `tests/` (file names) was viewed in the registry repository. `read_contamination` is `none` for every row.

Not read: the Architect final-rulings document `claude/ocs-p1-architect-final-rulings-2026-10-25.md` (the Projects tool was not available to this lane). Rulings were taken only from their restatement in `10-architect-rulings-and-repin.md` (rulings 1-16), `03` and `11`. Rows whose basis is a ruling cite that restatement. A1-A4, O-2..O-5, OPEN-Q5/Q12, approval revival and optional-scope fallback details were therefore not used beyond what the P1 plan quotes; the lead should confirm no row conflicts with them.

## 10. Failure meaning and use

A FAIL on a `BYTE_IDENTICAL`, `REASON_EQUIVALENT`, `CHECK_ORDER_PRESERVED` or `UNCHANGED_FILE` row means the candidate changed existing evaluator behaviour. A FAIL on a `NARROWER_ONLY` row means a widening or fail-open path. A `KNOWN_LIMIT_PRESERVED` row can only be satisfied by carrying the limit forward; it can never be reported PASS. Mutation legs (disable one refusal; the case must fail) are required per refusal family by the common independence rule and are owned by the executing lead.

This document is preparation. It does not qualify, verify or certify any V1 behaviour.
