# 06 Proposed V1 acceptance matrix

**Proposed, not adopted.** This maps **existing** test IDs to the release gates that the recommended profile ([01](01-executive-assessment.md) section 4) would need. It does not create a qualification framework, change any expectation, or reinterpret any verdict. Full test-ID lists per gate: [data/v1-acceptance-matrix.csv](data/v1-acceptance-matrix.csv) / [json](data/v1-acceptance-matrix.json). IDs are `suite-path::symbol` for catalog scenarios and test function names with the suite for Wiki cases, as recorded in the crosswalk.

Gate kinds: **MANDATORY** (the V1 profile F1a + F1b), **CONDITIONAL** (applies only if that family is added after its named ruling), **REGRESSION** (code-owned invariants must not move), **disclosure** (known limits listed apart).

| Gate | Scope | Required gate | Scenarios (existing test IDs) | Current evidence | New tests or decisions required |
|---|---|---|---|---|---|
| V1-M1 | MANDATORY (F1a) | The effect-boundary refusal behaviour for action/adapter/unit allow-lists is unchanged and passes at the exact component heads with the registry present | C11;C02;D02;TC-L06-009;TC-L06-011;TC-L06-013 (45) | No result at current heads. C02 and D02 historical PASS_RECORDED for named cases only; C11 KNOWN_LIMIT_ASSERTED; Wiki-derived NOT RUN | Add an MVP-tuple oracle row for a LocalExecutionPolicy denial (GAP-G4-09) |
| V1-M2 | MANDATORY (F1b) | Institution and authority-domain allow-lists refuse substitution at the effect boundary with the registry present | D02;C18;C11 (38) | D02/C18 historical PASS_RECORDED for named cases; no result at current heads | None for the refusal; the registry-supplied value path is new (V1-M4) |
| V1-M3 | MANDATORY | Registry values only narrow: effective = caller policy intersect registry policy; a widening or unsupported value is refused with a typed class | - (0) | Registry-repository S04/S05 evidence (outside this corpus; not re-read here) | Consumer-level test in the real Runtime/Control Plane path |
| V1-M4 | MANDATORY (G3-01/02) | A selected registry policy is the policy enforced at effect time; a policy changed between check and commit is refused or re-evaluated | - (0) | NONE exists. apply_registry_overlay has no caller; LocalExecutionPolicy check runs outside the atomic transaction | NEW: R10 Option A or B tests |
| V1-M5 | MANDATORY (R09) | Selection and activation are authenticated and independent of record publication status; a forged, replayed, expired or unselected record cannot govern an operation | - (0) | NONE exists. RuleRevisionProfile signers are unauthenticated | NEW: R09 adversarial battery |
| V1-M6 | MANDATORY if a mandatory profile is ever used (D7) | Required registry failure (unavailable, invalid, stale selection) does not fall back to a broader caller policy | TC-L05-013 (4) | TC-L05-013 test cannot detect an opt-in tolerance toggle (GAP-G4-05) | NEW fail-closed tests |
| V1-M7 | MANDATORY (disclosure) | Known limits retained outside the registry are listed separately and never counted as protection | D07;C07;C10;C11 (37) | Known-limit tests exist (35 declared in wiki-derived; 11 CP; 11 Runtime undeclared) | Declare the 11 Runtime known-limit tests (GAP-G4-07) |
| V1-M8 | MANDATORY (process) | Exact-head, independent qualification run of every gate above by a designated owner (D13) | - (0) | None; owner not designated; no run at CP 7a4bcd40 / RT c5e97e87 | Process |
| V1-R1 | REGRESSION (code-owned invariants stay in code) | Binding, ordering, idempotency, formats and reason vocabulary behave as before | D01;C02;C12;C13;C14 (51) | Historical; no result at current heads | None |
| V1-C1 | CONDITIONAL (only if F1c is added; needs D6) | Effect-count and amount ceilings are narrowed only, with exact-one-effect and finite-number invariants intact | C11;C16;C18;TC-L06-014;TC-L06-016;TC-L06-024;TC-D13-003;TC-L09-014 (61) | Wiki-derived NOT RUN; C16/C18 historical named-case PASS | D6 ruling, then typed composition tests (units, order, floor, direction) |
| V1-C2 | CONDITIONAL (only if F4 is added; needs D4 and D1 rulings and clock authority) | Freshness bounds tighten only; a stale observation, approval or status is refused or held; tolerance never extends the window | C01;TC-L06-015;TC-D09-009;TC-D09-016;D03;C07 (35) | Wiki-derived NOT RUN; C01/D03 historical named-case PASS | Per-scalar composition tests; clock-domain tests |
| V1-C3 | CONDITIONAL (only tightening-only F5 fields; relaxing toggles excluded) | Authority-profile fields cannot be relaxed by registry data | C01;TC-L05-012;TC-L05-013 (17) | See V1-M6 caveat | W8-014 ruling |
| V1-C4 | CONDITIONAL (only if F7 is added; needs D12) | Duplicate delivery adds no effect; ambiguous delivery reconciles without reopening | C09;D04;C08 (24) | D04 row INCONCLUSIVE in g8 (named matched-refund assertions executed and passed at historical pins); operation-identity *_today tests assert the legacy default exposure | D12 ruling; default-on decision (GAP-G1-01) |

## Rules for using this matrix

1. A gate is met only by a **PASS at the exact component heads, run by a designated independent qualifier** (D13). No row above has such a result; the "current evidence" column states what exists, all of it at historical pins and developer-run.
2. **Rows with no existing test (V1-M3 to V1-M6) are new qualification work.** They are not satisfied by collecting existing tests. Where an adjacent existing test is named it is context, not coverage (for example `TC-L05-013` cannot detect the opt-in `bounded_tolerance` toggle).
3. A passing known-limit test does not count toward any gate; it is listed under V1-M7 as a disclosure.
4. NOT RUN stays NOT RUN. A Wiki case counts toward a gate only after a recorded run; the pre-registration says Wiki-derived results are not gating by themselves, and only a major defect among their failures blocks (amendments 77 to 79).
5. Nothing here creates scenario IDs or alters `scenarios/catalog.json`, `coverage-map.json`, any suite, or any expectation file.

## Existing tests not mapped to any gate

The 591 NOT_APPLICABLE Wiki cases have no tests by construction. Of the 65 in-scope Wiki cases, 61 have Wiki-derived tests; only the cases mapped to a recommended or conditional family appear in a gate above. The remainder, and every scenario mapped to `NONE`, stay in their existing suites under the existing release-gate categories (OCS-1, OCS-2, OCS-3) and are unchanged by this assessment.

The number in parentheses in the gate table is the count of test IDs listed for that gate in the CSV. A test mapped to two scenarios (for example one used by both C11 and D02) is listed once per scenario, so the number is a list length, not a count of distinct tests or of scenarios.
