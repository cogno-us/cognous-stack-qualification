# 01 Executive assessment: what OCS Registry V1 needs to govern

**Status: documentation-only analysis. Non-authorizing. Draft for Architect review. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.**
Nothing here authorizes a family migration, approves a pin, selects or activates a record, or changes a qualification verdict. Implementation is not authorized.

Labels: **SOURCE FACT** (a file was read; cited), **REASONED INFERENCE**, **CUSTOMER HYPOTHESIS**, **UNVERIFIED**. Method, denominators and limitations are in [07](07-source-and-evidence-manifest.md).

## 1. Answer in brief

1. **No scenario in the existing corpus makes registry-managed configuration REQUIRED** (REASONED INFERENCE). Across the 696 canonical scenarios (40 Cognous catalog scenarios + 656 AI Security Wiki cases) and 162 suite-local claims, `REQUIRED` is 0. Every protection examined is enforced by component code, configured by a constructor literal, a manifest, resolver data or an opt-in profile. *This is not evidence that the registry is unnecessary:* the corpus was written before any registry consumer existed, so it cannot show a registry-only protection. It shows that V1 registry value is **central, versioned, authenticated change control of values the components already enforce**, not new enforcement.
2. **There is no path from the registry to an enforcement boundary today** (SOURCE FACT). `registry_consumer/consumer.py:270` `apply_registry_overlay` has no caller in Control Plane `7a4bcd40`, Runtime `c5e97e87` or the hub `51c579a3` (grep re-run for this report, no match in either component source tree). The Runtime's `LocalExecutionPolicy` check runs **outside** the atomic transaction (`atomic_local_control_plane_executor.py:69` versus `local_authority_effect.py:798`). The platform work (R09 authenticated selection, R10 effect-time binding) is the real V1 gate; the family list is secondary.
3. **Recommended V1 profile: F1a + F1b mandatory; F1c, F4 and F5 conditional on named rulings; everything else deferred** (section 4). F1a and F1b are in the top five of all three weighting schemes and in at least 77% of 5,000 seeded score perturbations. They are also the lowest-complexity real candidates (Lane D complexity 1 and 2).
4. **Profiles C and D are not recommended.** F6 has no effect-bearing consumer and D5 is unresolved. F1d composition is not definable and D9 defers it. Neither adds a scenario with a registry benefit that Profile B lacks, except one BENEFICIAL Wiki case (TC-L06-013) and one UNKNOWN catalog scenario (D09), both through F6, a family that cannot govern an effect today.
5. **Existing OCS enforcement defects and known limits are not registry features** and are kept with their owning components in the [gap register](05-gap-register.md). 33 gaps: 6 G1, 6 G2, 8 G3, 13 G4.
6. **Nothing is qualified.** No scenario-level PASS exists in any controller run; no recorded evidence speaks for the current component heads; all 656 Wiki cases are NOT RUN; no independent qualification owner is designated (D13).

### 1a. Three questions the registry-dependency rating must not conflate

The `registry_dependency` column answers one narrow thing: does the scenario's **required observation** depend on a registry-supplied value (REQUIRED / BENEFICIAL / UNNECESSARY / UNKNOWN). Read alone it is easy to over-read, so the assessment keeps three questions apart (derived view: [data/three-question-view.csv](data/three-question-view.csv), built by `method/build_three_question_view.py`; nothing in the crosswalk is re-rated):

| Question | Asks | Where it is answered |
|---|---|---|
| **A. Existing enforcement** | Does OCS code already enforce the protection, and is that evidenced? | `existing_protection` and `evidence_status` (copied verbatim) |
| **B. Governance benefit** | Would central, versioned registry management improve the customer's ability to govern the protection? | `q_b_governance_benefit` (derived from `registry_dependency` plus whether a governable value is mapped) |
| **C. V1 necessity** | Is registry management necessary for the V1 capability? | `q_c_v1_necessity_basis`: by definition of the operator-approved V1 profile (plan v1.3 section 1) for any selected family; this corpus cannot establish it independently |

**UNNECESSARY does not mean "central governance has no value".** It means one of two narrower things: no deployment-tunable value exists for the scenario (mandatory gate logic, evidence format, relaxing toggle, method scenario), or a value exists but the scenario's outcome does not depend on it. The view separates them (`NO_GOVERNABLE_VALUE` versus `GOVERNABLE_VALUE_EXISTS_OUTCOME_INDEPENDENT`). Among the 105 in-scope canonical rows: 17 `BENEFIT_IDENTIFIED`, 24 `BENEFIT_UNDETERMINED`, 10 `GOVERNABLE_VALUE_EXISTS_OUTCOME_INDEPENDENT`, 54 `NO_GOVERNABLE_VALUE`. A protection can be fully enforced (A) and still benefit from central change control (B); and "no scenario requires the registry" (the finding above) is a statement about the corpus, not about B or C.

## 2. What OCS already protects, and where the registry could matter

In-scope canonical rows: 105 (40 catalog + 20 APPLICABLE + 45 PARTLY_COVERED Wiki). The 591 NOT_APPLICABLE Wiki cases are retained in the crosswalk with their recorded reason and are not scored.

| Source | Applicability | Rows |
|---|---|---|
| Cognous catalog | catalog | 40 |
| AI Security Wiki | APPLICABLE | 20 |
| AI Security Wiki | NOT_APPLICABLE | 591 |
| AI Security Wiki | PARTLY_COVERED | 45 |

Registry dependency of the 105 in-scope rows (Lane A and B ratings; REASONED INFERENCE):

| Registry dependency | In-scope canonical rows |
|---|---|
| BENEFICIAL | 17 |
| UNKNOWN | 24 |
| UNNECESSARY | 64 |

Existing protection (controlled vocabulary; `ENFORCED_AND_EVIDENCED` is 0 among canonical rows because no scenario has a scenario-level controller PASS. 13 of the 162 suite-local claims carry it on the strength of recorded named-case results at historical pins only; none speaks for the current heads):

| Existing protection | In-scope canonical rows |
|---|---|
| IMPLEMENTED_NOT_QUALIFIED | 36 |
| KNOWN_GAP | 8 |
| NOT_APPLICABLE | 4 |
| PARTIALLY_ENFORCED | 55 |
| UNKNOWN | 2 |

Customer-relevant outcome of the in-scope rows (Lane E; severity is a REASONED INFERENCE on a 1-5 scale defined in [04](04-prioritization-analysis.md); a PARTLY_COVERED row carries the severity of the whole Wiki subject, which can overstate the slice OCS claims):

| Primary outcome | In-scope rows | BENEFICIAL | UNKNOWN | UNNECESSARY | KNOWN_GAP | Max severity |
|---|---|---|---|---|---|---|
| AUDIT_PROVENANCE_REPLAY | 20 | 1 | 2 | 17 | 3 | 3 |
| AGENT_PERMISSION_BOUNDARIES | 14 | 5 | 3 | 6 | 1 | 4 |
| INJECTION_TOOL_OUTPUT_MANIPULATION | 9 | 1 | 1 | 7 | 1 | 4 |
| APPROVAL_DELEGATED_AUTHORITY | 9 | 1 | 4 | 4 | 1 | 5 |
| POLICY_DISTRIBUTION_CHANGE_CONTROL | 9 | 3 | 4 | 2 | 1 | 4 |
| UNAUTHORIZED_TOOL_EXECUTION | 8 | 3 | 2 | 3 | 0 | 4 |
| REVOCATION_WITHDRAWAL | 8 | 1 | 1 | 6 | 1 | 4 |
| RECOVERY_OUTAGE_ROLLBACK | 8 | 0 | 1 | 7 | 0 | 4 |
| IDENTITY_TENANT_ISOLATION | 6 | 1 | 0 | 5 | 0 | 4 |
| FRESHNESS_EVIDENCE_VALIDITY | 5 | 0 | 2 | 3 | 0 | 4 |
| DUPLICATE_IRREVERSIBLE_EFFECTS | 4 | 1 | 0 | 3 | 0 | 5 |
| FINANCIAL_QUANTITATIVE_LIMITS | 3 | 0 | 3 | 0 | 0 | 4 |
| OTHER_OR_OUT_OF_SCOPE | 2 | 0 | 1 | 1 | 0 | 2 |

Reading: audit/provenance and agent permission boundaries dominate the in-scope set. Duplicate/irreversible effects and freshness outcomes occur almost only in the Cognous catalog, where the highest-severity scenarios sit (D04 and C09, severity 5). No source text establishes a healthcare, financial-sector or customer-validated context (`domain_claim_in_source` is false in all 696 rows). "Financial" appears only as a tool-category label in two Wiki test fixtures; `FINANCIAL_QUANTITATIVE_LIMITS` here means effect budgets and caps.

## 3. Profiles A to D against the corpus

| Profile | Families | Canonical scenarios touched | Fully covered (all families of the scenario in profile) | of which BENEFICIAL | of which UNKNOWN | of which UNNECESSARY | BENEFICIAL, severity>=4 | Suite-local touched / fully |
|---|---|---|---|---|---|---|---|---|
| A | F1a+F1b | 9 | 3 | 2 | 0 | 1 | TC-L06-009, TC-L06-011 | 4 / 1 |
| B | F1a+F1b+F1c+F4+F5 | 26 | 23 | 7 | 9 | 7 | C01, C11, TC-D09-016, TC-L06-009, TC-L06-011, TC-L06-015 | 23 / 20 |
| C | B + F6 | 27 | 25 | 8 | 10 | 7 | C01, C11, TC-D09-016, TC-L06-009, TC-L06-011, TC-L06-013, TC-L06-015 | 25 / 22 |
| D | C + F1d | 28 | 27 | 8 | 12 | 7 | C01, C11, TC-D09-016, TC-L06-009, TC-L06-011, TC-L06-013, TC-L06-015 | 25 / 23 |

"Touched" counts a scenario if any of its mapped families is in the profile; "fully covered" requires that all of its mapped families are in the profile and none is UNMAPPED. Each scenario is counted once, however many tests it has. BENEFICIAL is the strongest rating the corpus supports.

- **Profile A (F1a+F1b)** fully covers 3 canonical scenarios (TC-L06-009 and TC-L06-011 BENEFICIAL, C02 UNNECESSARY). The scenario that most clearly needs registry-supplied values, C11, also needs F1c. Profile A is technically credible and **commercially thin on scenario breadth**; its value is proving the selection, authentication and effect-time path on the smallest bounded surface (R08-prep document 09 reaches a similar candidate).
- **Profile B** adds the highest-consequence beneficial scenarios (C01, C11, TC-D09-016, TC-L06-015). But 9 of its 23 fully covered scenarios are UNKNOWN because they wait on D1, D4, D6 or the W8-014 classification, and each family has an unresolved composition or clock-authority question.
- **Profile C** adds two scenarios (TC-L06-013 BENEFICIAL, D09 UNKNOWN) through F6, a family with no effect-bearing consumer. **Profile D** adds F1d: two scenarios, both UNKNOWN, with composition not definable. A larger family count does not imply better governance.
- **F7 (deduplication) is evaluated separately** in [03](03-family-coverage-matrix.md): existing code-owned dedupe is not shown adequate, but the open exposure is an enforcement default (operation identity and dedupe profiles are opt-in and default OFF; the `*_today` tests assert that default), not a missing registry parameter. D12 is not resolved here.

## 4. Recommended V1 profile

| Class | Families | Condition |
|---|---|---|
| **Mandatory** | **F1a** (action/adapter/unit allow-lists), **F1b** (institution/authority-domain allow-lists) | Composition by intersection only; R09 authenticated selection and R10 effect-time binding must exist first. Preferred first extension per Architect ruling D11 (priority, not permission). |
| **Conditional** (enters V1 only when its own lane meets the condition) | **F1c** ceilings | D6 ruled; typed composition (units, order, floor, direction); exact-one-effect invariant kept in code. |
| | **F4** freshness bounds | D4 per-scalar rulings and D1 / clock authority resolved; tightening-only. |
| | **F5** authority-profile fields | W8-014 ruled; only tightening-only fields; relaxing toggles (for example `on_unreadable="bounded_tolerance"`) stay code-owned. |
| **Deferred** | F6, F1d, F7, F3, F9, F10, F11 | F6: no effect-bearing consumer, D5. F1d: D9. F7: D12 and the default-on question. F3/F9/F10/F11: low consequence or classification pending. |
| **Not a policy family** | F8 | Demo policy tool lists; helpers have no callers (Lane D). |

**Code-owned invariants retained outside the registry** (SOURCE FACT per Lane D; evaluators cited in [appendix D](appendix/lane-D-family-source-analysis.md)): check order and reason texts of `LocalExecutionPolicy.check`; the exact-one-effect rule (`op.effects == 1`); finite non-negative number rules for ceilings; target well-formedness refusals; match-mode vocabulary; `observation_policy_missing` fail-closed hold and the rule that tolerance never extends a staleness window; authenticated-resolver requirement; dedupe ordering `provider_horizon <= escalation_deadline < dedupe_ttl`; the reason vocabulary (M7) and mandatory groups M1 to M8 of the R07 analysis; redaction of protected data.

**Divergence from the plan's default R11 order.** Plan v1.2 lists F1 institutions/domains, then F6, then F1 numeric ceilings and target prefixes, then F4, F5. This assessment ranks F6 below F4/F1c/F5 because F6 governs a path that executes nothing today (SOURCE FACT: `PermissionSystem` is used only by the legacy `AgentEngine`, which never executes). It does not alter the adopted plan; it is an input to the operator's per-family authorization.

**Scenario coverage gained** (Profile A, recommended mandatory set): TC-L06-009, TC-L06-011 (BENEFICIAL) and C02 (retained as a regression, UNNECESSARY). With all conditions met (Profile B): 7 BENEFICIAL scenarios fully covered, including C01, C11, TC-D09-016, TC-L06-015.

**Important scenarios still unsupported by any recommended family:** TC-L06-018 (agent-to-agent authenticity, KNOWN_GAP, no R07 family), duplicate/irreversible effects (D04, C09: F7 deferred), the Wiki audit/provenance known limits (TC-L06-045, TC-L17-002, TC-L17-021), C20/C21 (adoption/selection scenarios, UNIMPLEMENTED), and all 13 catalog scenarios that have no driver (A01-A06, H01, H02, C05, C15, C19-C21).

**Residual security and governance gaps:** [05](05-gap-register.md). The highest-severity open items are GAP-G3-01 (no consumption path), GAP-G3-02 (policy check outside the atomic transaction), GAP-G3-07 (selection unauthenticated today), GAP-G1-01 (operation-identity/dedupe default OFF), GAP-G4-01/02 (no scenario-level PASS and nothing at current heads), GAP-G4-09 (no MVP oracle row for a `LocalExecutionPolicy` denial) and GAP-G4-13 (no independent qualification owner).

**Required R09/R10 capabilities** (from the register, not new requirements): authenticated selection and activation independent of record status (R09, D2, D3); a named Runtime/Control Plane hook that applies a selected policy and binds it at effect time, R10 Option A or B; fail-closed behaviour when a required policy is unavailable (D7, design capability only); typed refusal classes already proposed in R07.

**Governance capability lost on exclusion** is stated per family in [03](03-family-coverage-matrix.md) and per field in the [extraction manifest](09-configuration-extraction-handoff.md) (`exclusion_impact`). It is the central change-control capability the customer would not gain, never an enforcement that would be lost: enforcement stays in component code either way. In short: excluding F1a/F1b leaves no registry-governed policy value, so allow-lists stay per-host constructor literals changed by redeploy, with no registry-pinned policy identity in evidence; excluding F1c/F4/F5 leaves ceilings, freshness windows and authority-profile fields as host constructor literals and manifest limits (no centrally versioned fleet-wide tightening, but no existing protection removed); excluding F6/F1d/F7 loses no governance capability that is consumed or ruled today. Model A versus Model B (extract only what the selected scenarios need, or all safe fields of the selected owners) is compared in [08](08-model-a-b-comparison.md).

## 5. Sensitivity of the family order

Full tables and definitions in [04](04-prioritization-analysis.md). The order changes with the weighting, and the ranking is not an eligibility test:

| Rank | Security-first | Customer-operational | Engineering-effort |
|---|---|---|---|
| 1 | F4 | F4 | F1a |
| 2 | F1b | F1c | F1b |
| 3 | F1a | F5 | F10 |
| 4 | F1c | F1b | F3 |
| 5 | F5 | F1a | F11 |
| 6 | F7 | F7 | F9 |
| 7 | F3 | F1d | F8 |
| 8 | F1d | F3 | F1c |
| 9 | F6 | F6 | F5 |
| 10 | F9 | F11 | F4 |
| 11 | F11 | F9 | F6 |
| 12 | F10 | F10 | F7 |
| 13 | F8 | F8 | F1d |

- F1a and F1b are in the top five under all three weightings. F4, F1c and F5 lead under the security-first and customer-operational weightings but fall to eighth to tenth place under engineering-effort weighting; F6, F1d and F7 are never in the top five.
- Under engineering-effort weighting, low-consequence families (F10, F3, F11) rise. That is the reason **ease is not used to choose families**.
- A seeded ±1 perturbation of the manually assigned scores (5,000 draws) keeps F1b in the top five in 91.5% (security-first) and 92.0% (customer-operational) of draws and F1a in 86.6% and 77.1%; F4 is always in the top five under the first two weightings.

## 6. Decisions this assessment depends on (none resolved here)

D1 (32 S02 rows, including W8-091, W3-063, W9-027, W8-014, W6-042, and the 60-versus-300 relationship, which stays a distinction between different quantities), D5 (F6 absent agent), D6 (`max_effects` / `max_amount`), D12 (`dedupe.py` versus `merge.py`: no supported path to the divergent input was found; it is not called a defect), D9 (F1d), D4 (scalar composition per field), trust root and custody, per-operation participation, deny-all encoding, MSOP, qualification owner (D13), per-family authorization. Rulings already made by the Architect (D2, D3, D4, D7, D8, D9, D10, D11, D13) are treated as design guidance.

## 7. Limitations that bound every statement above

- Evidence is **developer-run, synthetic, Cognous-configured**, at historical pins (r10: Control Plane `2bac7875`, Runtime `6b16962d`; r13: `0a41faa9`, `ec728da6`). Source for this assessment was read at the current heads (`7a4bcd40`, `c5e97e87`); the clones are shallow, so drift between pin and head cannot be diffed.
- Exchange, Replay, Evidence Pack, ODES, Verifier, BitRep, Index and Action Manifest sources were **not available**; their rows are UNVERIFIED or REASONED INFERENCE from relocated tests' names and docstrings.
- Registry dependency, existing-protection and severity ratings are rule-based judgements by delegated workers and the integration lead; they were not adjudicated by a second human and were not decided by majority vote. A cross-check of Lane E's classification (40 Wiki cases, same reviewer) agreed 28/40; all 12 disagreements were NOT_APPLICABLE rows.
- Test counts are by static reading where pytest was unavailable; parametrised counts are lower bounds in places.
- No customer demand, revenue or adoption data was used or invented.
