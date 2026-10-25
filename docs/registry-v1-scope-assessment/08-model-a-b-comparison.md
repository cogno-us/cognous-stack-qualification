# 08 Model A versus Model B: where to draw the V1 extraction boundary

**Status: documentation-only analysis. Non-authorizing. Draft for Architect review. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.** Nothing here selects a scope, authorizes a migration or approves P1 extraction. The recommendation below is an **analytical recommendation, not an adopted scope**; scope is frozen only by the operator (plan v1.3 section 8).

Labels as in [01](01-executive-assessment.md): SOURCE FACT, REASONED INFERENCE, CUSTOMER HYPOTHESIS, UNVERIFIED. Counts come from the [extraction manifest](09-configuration-extraction-handoff.md) (96 rows: 24 Runtime at `c5e97e87`, 72 Control Plane at `7a4bcd40`) joined to the [three-question view](data/three-question-view.csv). A "field" is one manifest row with disposition `DIRECT_EXTRACTION` or `CONDITIONAL_EXTRACTION`. **A count of fields is not a count of safe migratable values**: every `CONDITIONAL_EXTRACTION` row waits on a named ruling or prerequisite, and no row is approved, qualified or scheduled.

## 1. The two models

- **Model A (scenario-driven).** Externalize only the fields that a selected scenario's required observation varies. "Selected" here means a canonical scenario with an identified governance benefit (question B: `BENEFIT_IDENTIFIED`, 17 in-scope canonical rows). The field-to-scenario link is the manifest's `scenario_id` column.
- **Model B (owner-wide).** Externalize every safe, useful field of the selected owners through their existing evaluators and typed adapters, whether or not a selected scenario varies it. "Safe" means the P0 extractability test passes or is conditional on a named decision; relaxing toggles, guards and unresolved rows are never in either model.

Neither model is preferred by default. Both are bounded by the same constraints: registry holds typed parameter data only, evaluators and guardrails stay code, the registry never grants or activates, and effect-time binding (R10) is a precondition for relying on any registry value at the effect boundary (GAP-G3-01, GAP-G3-02, GAP-G3-07).

## 2. Field counts

Fields with disposition DIRECT or CONDITIONAL, by family (manifest, joined to question B):

| Family | Owner | DIRECT | CONDITIONAL | Fields in Model A (varied by a BENEFICIAL scenario) | Fields only in Model B | Of Model B-only: tied to an UNKNOWN scenario | Of Model B-only: no mapped canonical benefit |
|---|---|---|---|---|---|---|---|
| F1a | Runtime | 3 | 0 | 3 | 0 | 0 | 0 |
| F1b | Runtime | 2 | 0 | 2 | 0 | 0 | 0 |
| F1c | Runtime | 0 | 1 | 1 | 0 | 0 | 0 |
| F4 | Control Plane | 0 | 7 | 2 | 5 | 0 | 5 |
| F5 | Control Plane | 0 | 3 | 2 | 1 | 1 | 0 |
| **Candidate families (F1a, F1b, F1c, F4, F5)** | | **5** | **11** | **10** | **6** | **1** | **5** |
| F6 | Runtime | 0 | 1 | 0 | 1 | 1 | 0 |
| F3 | Runtime, Control Plane | 0 | 2 | 0 | 2 | 1 | 1 |
| F7 | Control Plane | 0 | 1 | 0 | 1 | 0 | 1 |
| F11 | Control Plane | 0 | 4 | 0 | 4 | 4 | 0 |
| F8, F9, F10 | | 0 | 0 | 0 | 0 | 0 | 0 |
| **All families** | | **5** | **19** | **10** | **14** | **7** | **7** |

Reading the table:

1. **On the Runtime, Model B adds nothing to Model A.** All five DIRECT fields (`allowed_actions`, `allowed_adapters`, `allowed_units`, `allowed_institutions`, `allowed_authority_domains`) and `max_amount` are varied by a BENEFICIAL scenario (C11 varies every policy dimension including `unit`; TC-L06-009/011/013 vary action and adapter). The handoff's earlier working note that B-over-A on the Runtime was "3 DIRECT fields" is superseded by this join. The Runtime increment of B over A is decision-gated fields only (F6 permissions mapping, OpenShell timeout).
2. **On the Control Plane, the whole B-over-A increment is conditional and mostly unsupported by a benefit scenario.** Of the 6 additional candidate-family fields, 5 have no canonical benefit mapping at all (observation, identity and mandate age bounds; the anchor-to-inputs flag and the age-extension limit) and 1 (`requires_revocation_assurance`) is tied only to an UNKNOWN scenario. Benefit and complexity are REASONED INFERENCE.
3. **Model A as counted includes one field that should not be extracted in any model:** `ActionClass.on_unreadable` (CP-F5-02) is a relaxing toggle (`refuse` | `bounded_tolerance`) and R07 keeps such toggles in code. Its row is conditional only on whether a tightening-only reading is ruled (W8-014); effective Model A is therefore 9 fields, 5 of them direct.

## 3. Comparison by family

Effort and complexity use the manifest's `extraction_complexity` (LOW / MEDIUM / HIGH) and Lane D's 1-5 scale; they are relative judgements, not estimates in person-days. "Added qualification burden" is the qualification the manifest rows list as NEW, beyond reuse of existing tests (which are NOT RUN or historical and speak for no current head).

### F1a and F1b: Runtime allow-lists (5 DIRECT fields)

| Dimension | Model A | Model B |
|---|---|---|
| Incremental governance capability | Central, versioned, authenticated change control of the five sets (C11, TC-L06-009/011/013) | Identical: A and B select the same five fields |
| Values externalized | 5 | 5 |
| Engineering effort | LOW (one frozenset per field on one evaluator; shared R08 to R10 infrastructure dominates). F1a path exists as an implemented-but-unwired reference; F1b needs a contract version change | Same |
| Architectural complexity | Low: set intersection is definable and non-widening | Same |
| Cross-component dependencies | Action ids and adapter ids must coincide with Control Plane manifest ids (nothing in code binds them); institution and domain operands are derived from Control Plane authority context | Same |
| New security exposure | A registry set omitting the deployed value refuses everything (fail-closed). Two further risks: the check runs before the atomic transaction on Route B (GAP-G3-02), and selection is unauthenticated today (GAP-G3-07) | Same |
| Added qualification burden | New differential battery for F1b with an independent oracle; fail-closed negatives; effect-time revalidation; F1a's S05 oracle is builder-written, not independent (D13 undesignated) | Same |
| Consequence of deferral | Allow-lists stay host constructor literals changed by redeploy; no registry-pinned policy identity appears in evidence; no enforcement lost | Same |

Model choice is moot for these families. Whether to include them at all is the real question, and it depends on R09 and R10 (section 5).

### F1c: ceilings (Runtime `max_amount` conditional; `max_effects` unresolved)

| Dimension | Model A | Model B |
|---|---|---|
| Incremental governance capability | Central lowering of the local per-effect monetary ceiling (C11); fleet-wide tightening without per-host redeploy | Same field; `max_effects` is UNRESOLVED (W8-091, D6) and `exact-one-effect` and the binary64 validators are code-owned guardrails in both models |
| Values externalized | 1 | 1 |
| Engineering effort | HIGH: D6 unruled; a code hard cap and floor must be defined; numeric encoding open (registry JCS and loader refuse floats, P0 G3) | Same |
| Architectural complexity | One unit-less ceiling is compared regardless of unit, so unit narrowing interacts with it (multi-unit semantics unspecified) | Same |
| Cross-component dependencies | Control Plane keeps independent manifest and grant ceilings; the registry value can only affect the Runtime second layer | Same |
| New security exposure | Mis-specified minimum semantics could raise a ceiling; the numeric encoding is a new parsing surface | Same |
| Added qualification burden | Numeric boundary battery on Routes A and B (equality, 0, 2**53, 2**53+1, NaN, inf, bool, negative), independent `min(caller, registry)` oracle, registry-cannot-raise test | Same |
| Consequence of deferral | Ceilings remain host literals; Control Plane limits unaffected | Same |

### F4: freshness windows (Control Plane, 7 conditional fields; 0 direct)

| Dimension | Model A (2 fields: `status_max_age_seconds`, `approval_max_age_seconds`) | Model B (7 fields) |
|---|---|---|
| Incremental governance capability | Central tuning of status and approval freshness (TC-D09-009/016, TC-L06-015) | A plus observation, identity and mandate age bounds, anchor and extension fields, which no BENEFICIAL scenario varies |
| Values externalized | 2 | 7 (5 more) |
| Engineering effort | HIGH. No Control Plane consumer or adapter exists (P0 G4); F4 is Lane D complexity 5 | Higher: more scalars, each needing a per-field ruling |
| Architectural complexity | Constructor age bounds and clock tolerance carry **no validation or floor** (`bounded.py:1271-1299`), so extractability clause (b) fails as the code stands; the Runtime effect-time check applies zero tolerance (SOURCE FACT: constructor parameters at `bounded.py:1271-1299` are plain `int` arguments with no check; the zero-tolerance point is from the Control Plane worker notes) | Same, multiplied |
| Cross-component dependencies | Two separate tolerance fields; Runtime evidence-row ages are a second copy | More copies |
| New security exposure | A registry value that lengthens a window widens authority; narrow-only composition per scalar (units, order, floor, direction) must be ruled first (D4, W6-042) | Larger surface; five extra scalars with no benefit scenario |
| Added qualification burden | Per-scalar composition tests, clock-domain tests | Roughly proportional to field count |
| Consequence of deferral | Windows stay constructor arguments and evidence-row values; the fail-closed missing-policy hold is a code invariant either way | Same, so deferring the five extra fields costs no mapped benefit |

### F5: per-action-class authority declarations (Control Plane, 3 conditional fields)

| Dimension | Model A (2 fields) | Model B (3 fields) |
|---|---|---|
| Incremental governance capability | `max_status_age_seconds` (C01, TC-D09-016) and `on_unreadable` (C01) | Adds `requires_revocation_assurance` (UNKNOWN scenario TC-L05-012 only) |
| Values externalized | 2, of which `on_unreadable` is a relaxing toggle that should stay code | 3 |
| Engineering effort | HIGH: `max_status_age_seconds` has at least four consumers; needs the same Control Plane adapter as F4 | Slightly higher |
| Architectural complexity | W8-014 open; the authority profile is hashed into the approval commitment (`runtime_authority.py:186,268`), so a changed profile value changes the commitment | Same |
| New security exposure | `on_unreadable=bounded_tolerance` can relax a refusal, and the Wiki known-limit test cannot detect it (GAP-G4-05) | Same |
| Added qualification burden | Toggle-cannot-relax negatives; commitment-stability tests | Plus revocation-assurance semantics |
| Consequence of deferral | Declarations stay in the authority profile; no enforcement lost | Same |

### Families outside the candidate set (Model B only, all decision-gated)

| Family | Fields | Why they add little in V1 |
|---|---|---|
| F6 | 1 conditional (permissions mapping) | Only consumer is the unsupported legacy `AgentEngine`, which executes nothing; D5 open; the enforcing path is Control Plane grants (GAP-G3-05) |
| F3 | 2 conditional (OpenShell timeout, lease-acquire timeout) | Convenience limits; D1 open; hostile-input admission bounds are code-owned guardrails in both models |
| F7 | 1 conditional (`funded_authorities`) | D12 open; dedupe numbers never gate dispatch (only the profile's presence does), and the duplicate-effect protection is an owner decision on defaults (GAP-G1-01), not a registry parameter |
| F11 | 4 conditional (redaction toggles) | `redact_tool_execution_result` ignores `redact_payloads`; a toggle that widens redaction output is a leakage risk; D1 and W9-002 open; tied only to one UNKNOWN known-limit Wiki row |
| F8, F9, F10 | 0 | No consumed policy value (F8), must-agree literals with no benefit scenario (F9), non-gating diagnostic (F10) |

## 4. Recommended V1 boundary (analytical recommendation, not an adopted scope)

On the evidence in sections 2 and 3, the V1 boundary that the evidence supports is **Model-A-shaped on fields and Model-B-shaped on architecture**:

1. **Mandatory: F1a and F1b, the five Runtime DIRECT fields.** Models A and B coincide, every field has a BENEFICIAL scenario, and these are the only rows where all four extractability clauses pass on source read at the pin with no open D1/D5/D6/D9/D12 dependency. Mandatory means these are the fields a V1 registry claim would rest on; it presupposes R09 and R10.
2. **Conditional, each on its named prerequisite:** F1c `max_amount` (D6, numeric encoding, a code hard cap and floor); F4 `status_max_age_seconds` and `approval_max_age_seconds` (W6-042, per-scalar composition, a code floor and validation that the constructor lacks today, a Control Plane adapter); F5 `max_status_age_seconds` (W8-014, same adapter). No conditional field becomes mandatory by ranking: F4 ranks first under two weightings in [04](04-prioritization-analysis.md) yet has no direct row.
3. **Not in V1 on this evidence:** the six candidate-family fields only Model B adds (five without any benefit scenario), `on_unreadable` and every other relaxing toggle, F6, F1d, F3, F7, F11, F8, F9, F10. The reason is not that they are worthless; it is that each has either no mapped benefit scenario, an open ruling, or a clause-(b) failure, and each adds qualification burden that the current evidence (nothing qualified at the current heads, no independent qualification owner) cannot absorb.
4. **Design the typed adapter and family-dispatch table (P0 G1) so Model B is additive.** Choosing a narrow V1 field set does not require a narrow architecture. A `family -> (payload validator, composer, evaluator binding, caller normalizer)` table lets later fields join without redesign.

This reverses neither the earlier family recommendation in [01](01-executive-assessment.md) section 4 (F1a + F1b mandatory; F1c, F4, F5 conditional; the rest deferred) nor any ruling: it gives that recommendation a field-level basis. It depends on decisions it cannot make: D1, D4, D6, D12, W8-014, the numeric encoding, and the R09/R10 platform work.

## 5. What would change the recommendation

- **If R09 and R10 are not delivered for V1,** neither model gives an enforced registry value: there is no consumption path today (GAP-G3-01) and the policy check precedes the atomic transaction (GAP-G3-02). The choice between A and B is second-order to that gate.
- **If D6 is ruled "invariant,"** `max_amount` leaves the conditional set and V1 is exactly the five F1a/F1b fields.
- **If a customer need for Control Plane freshness tuning is evidenced** (it is a CUSTOMER HYPOTHESIS in this corpus), Model B for F4 becomes worth reconsidering, but only after the code floor and validation exist and per-scalar composition is ruled.
- **If an independent qualification owner is designated (D13)** the qualification-burden column weakens as an argument against extra fields; it does not remove the benefit and ruling gaps.

## 6. Limits

The field-to-scenario join uses the manifest `scenario_id` column; a field with no mapped benefit scenario may still have customer value that the corpus does not show. Effort and complexity are relative. Row counts depend on how the manifest splits adjacent fields (for example, F4 has separate rows for each age and tolerance). Only the Runtime and Control Plane were inspected; fields owned by Exchange, Replay, Evidence Pack, ODES, Verifier, BitRep, Index and Action Manifest are not in either model (see [09](09-configuration-extraction-handoff.md)).
