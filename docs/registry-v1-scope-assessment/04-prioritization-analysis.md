# 04 Prioritization analysis

Non-authorizing. This ranks **outcomes and families**, not test functions. Raw test counts are not used as a proxy for business value: a single scenario showing an uncontrolled irreversible effect can outweigh many schema-validation tests (D04 and C09, severity 5, versus dozens of format checks). No customer demand, revenue or adoption data exists in the corpus and none is used.

Every cell below is a **REASONED INFERENCE** unless marked otherwise. Scores are ordinal 1-5 and are not additive in any physical sense; the weighted composites exist only to test whether the order is stable.

## 1. Dimensions and scale definitions

| Dim | Name | 5 means | 1 means | How derived |
|---|---|---|---|---|
| A | Security consequence | An in-scope mapped scenario whose failure is an uncontrolled irreversible external effect or a boundary bypass with durable harm | Failure is a cosmetic or false-block outcome | **Computed**: maximum Lane E severity over the family's in-scope canonical scenarios. Lane E rates the harm if the protection fails (1-5), per scenario, on its text. |
| B | Breadth of enterprise applicability | Maps to 6 or more distinct primary outcome categories | One category | **Computed**: distinct primary outcomes of mapped in-scope canonical scenarios (1 → 1, 2 → 2, 3 → 3, 4-5 → 4, 6+ → 5). Structural proxy; no customer data. |
| C | Dependence on centralized governance | Registry-managed configuration REQUIRED | All mapped rows UNNECESSARY | **Computed**: 4 if at least 3 BENEFICIAL rows (canonical + suite-local) including one of severity ≥ 4; 3 if at least 1 BENEFICIAL; 2 if only UNKNOWN; 1 otherwise. 5 (REQUIRED) is never reached. |
| D | Existing OCS enforcement maturity | Enforced at the effect boundary with negative evidence | No effect-bearing consumer | **Manual** (rationale in section 3). A registry can only govern what code enforces. |
| E | Incremental customer capability from registry control | Large new capability (central, versioned, authenticated, auditable control of a value customers cannot otherwise govern) | None (value is internal or a code constant) | **Manual** (section 3). |
| F | Engineering and integration complexity | (ease) 5 = complexity 1 | (ease) 1 = complexity 5 | **Lane D** complexity score, inverted: ease = 6 − complexity. |
| G | Qualification maturity | A mapped scenario has a controller-recorded named-case PASS (historical pins; capped at 3 because nothing speaks for the current heads) | No test, or known-limit tests only | **Computed**: 3 if any mapped canonical row has `PASS_RECORDED`; 2 if tests exist; 1 otherwise. |
| H | Cross-family dependencies | (ease) 5 = none | (ease) 1 = four or more | **Computed** from Lane D's cross-family dependency list: 5 − min(4, number of dependencies). |

## 2. Scores

| Family | A | B | C | D | E | F (ease) | G | H (ease) |
|---|---|---|---|---|---|---|---|---|
| F1a | 4 | 2 | 4 | 3 | 3 | 5 | 3 | 3 |
| F1b | 4 | 3 | 4 | 3 | 3 | 4 | 3 | 3 |
| F1c | 4 | 4 | 4 | 3 | 4 | 2 | 3 | 2 |
| F1d | 4 | 2 | 3 | 2 | 3 | 1 | 2 | 3 |
| F3 | 4 | 2 | 3 | 3 | 2 | 3 | 3 | 3 |
| F4 | 5 | 5 | 4 | 3 | 4 | 1 | 3 | 2 |
| F5 | 4 | 5 | 4 | 3 | 3 | 2 | 3 | 2 |
| F6 | 4 | 2 | 3 | 1 | 2 | 2 | 3 | 4 |
| F7 | 5 | 2 | 4 | 2 | 3 | 1 | 3 | 2 |
| F8 | 1 | 1 | 1 | 1 | 1 | 5 | 1 | 4 |
| F9 | 4 | 1 | 1 | 3 | 1 | 3 | 2 | 4 |
| F10 | 1 | 1 | 2 | 2 | 1 | 5 | 1 | 4 |
| F11 | 3 | 1 | 2 | 3 | 2 | 3 | 2 | 4 |

The 36 in-scope rows mapped to `NONE` (mandatory gate or evidence logic, or grant data) and the 64 rated UNNECESSARY do not raise any family's score.

## 3. Rationale for the manually assigned scores (D, E)

| Family | D | E | Rationale (REASONED INFERENCE; source in Lane D / B / C notes) |
|---|---|---|---|
| F1a | 3 | 3 | Enforced in Runtime `LocalExecutionPolicy.check` and tested, but the check runs outside the atomic transaction and D02/C02 show binding does the refusing (D = 3). Central change control of allow-lists is real but modest (E = 3). |
| F1b | 3 | 3 | Same evaluator; operands come from the Control Plane. |
| F1c | 3 | 4 | Ceiling enforced in Runtime, operand computed in Control Plane; central effect-budget control is the most direct governance gain (E = 4), subject to D6. |
| F1d | 2 | 3 | Enforced, but a documented weakening mode exists and no test varies it (D = 2). |
| F3 | 3 | 2 | Module-constant hostile-input bounds. |
| F4 | 3 | 4 | Enforced across two components with a fail-closed missing-policy hold; window "narrowed, not closed" (source comment). Central freshness control is valuable (E = 4). |
| F5 | 3 | 3 | Decision-time only; relaxing toggles must stay in code, which limits the governable surface. |
| F6 | 1 | 2 | No effect-bearing consumer; value is potential only. |
| F7 | 2 | 3 | Opt-in, default OFF; selected route B destination has no TTL. |
| F8 | 1 | 1 | Uncalled helpers. |
| F9 | 3 | 1 | Constants that must agree across six copies; no customer value in changing them. |
| F10 | 2 | 1 | Non-gating diagnostic. |
| F11 | 3 | 2 | Redaction defaults; tier classification pending; protected-data redaction cannot be removed by data. |

## 4. Weighting schemes

| Dim | Security-first | Customer-operational | Engineering-effort |
|---|---|---|---|
| A consequence | 0.30 | 0.10 | 0.075 |
| B breadth | 0.10 | 0.20 | 0.05 |
| C central governance | 0.15 | 0.20 | 0.05 |
| D enforcement maturity | 0.15 | 0.10 | 0.15 |
| E incremental capability | 0.10 | 0.25 | 0.075 |
| F ease | 0.075 | 0.05 | 0.30 |
| G qualification maturity | 0.05 | 0.05 | 0.10 |
| H dependency ease | 0.075 | 0.05 | 0.20 |

Weights are a documented choice, not an estimate of anything; they are written down so a reviewer can change them. `method/build_assessment.py` documents how the lane outputs were joined and weighted, but its lane input files are not committed, so the stage cannot be re-run from this checkout; the committed `data/` and `appendix/` files are the authoritative outputs. A reviewer who changes a weight must restore the lane inputs or recompute from `data/family-metrics-and-scores.json`.

## 5. Composites and order

| Family | Security-first | Customer-operational | Engineering-effort |
|---|---|---|---|
| F1a | 3.5 | 3.2 | 3.675 |
| F1b | 3.525 | 3.35 | 3.425 |
| F1c | 3.5 | 3.65 | 2.75 |
| F1d | 2.85 | 2.65 | 2.175 |
| F3 | 3.1 | 2.65 | 2.95 |
| F4 | 3.825 | 3.9 | 2.575 |
| F5 | 3.5 | 3.6 | 2.725 |
| F6 | 2.8 | 2.45 | 2.55 |
| F7 | 3.275 | 2.95 | 2.2 |
| F8 | 1.525 | 1.35 | 2.8 |
| F9 | 2.625 | 1.8 | 2.825 |
| F10 | 1.825 | 1.65 | 3.0 |
| F11 | 2.575 | 2.15 | 2.875 |

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

## 6. Does the recommended order change?

Yes, with the weighting, in a structured way:

- **Stable:** F1a and F1b are in the top five under all three weightings (F1a: positions 3 / 5 / 1 and F1b: 2 / 4 / 2 under security-first / customer-operational / engineering-effort). F6, F1d and F7 are never in the top five. F8 is last or near-last everywhere.
- **Value-driven order:** under security-first and customer-operational weighting the top five is the same set (F4, F1b, F1a, F1c, F5), with F4 first. These are the families with the highest-consequence BENEFICIAL scenarios.
- **Effort-driven order:** under engineering-effort weighting F4, F5 and F1c drop to tenth, ninth and eighth, and low-consequence families (F10, F3, F11, F9) rise. Ease is therefore reported but **not** used to choose families.
- **Ranking is not eligibility.** F4 ranks first under two schemes but has complexity 5, no definable cross-bound composition, an open clock-authority question (D1) and unruled D4 scalars. [01](01-executive-assessment.md) section 4 therefore makes F4 conditional despite its rank. A family also needs its decisions ruled and an effect-time binding before it is eligible; the ranking only orders the families that are eligible.

### Robustness of the manual scores

5,000 seeded draws (seed 7) moved every manually assigned score (D, E) and the ease score (F) by −1, 0 or +1 (clamped to 1-5) and recorded how often each family stayed in the top five (`method/robustness.py`, `data/robustness.json`):

| Family | Security-first | Customer-operational | Engineering-effort |
|---|---|---|---|
| F1a | 86.6% | 77.1% | 100.0% |
| F1b | 91.5% | 92.0% | 97.3% |
| F1c | 88.0% | 99.9% | 31.6% |
| F4 | 100.0% | 100.0% | 13.4% |
| F5 | 87.3% | 99.6% | 25.7% |
| F7 | 39.4% | 27.3% | 0.1% |
| F6 | 0.0% | 0.0% | 11.9% |

This tests sensitivity to the author's judgement on three dimensions only. It does not test the computed dimensions (A, B, C, G, H), which depend on Lane A/B/C/E ratings that were not independently adjudicated.

## 7. Per-scenario priority (crosswalk column `priority`)

Rule-based, from Lane E severity and the Lane A/B/C dependency rating:

| Priority | Rows | Rule |
|---|---|---|
| P1 | 9 | BENEFICIAL (or REQUIRED) and consequence severity >= 4 |
| P2 | 28 | BENEFICIAL with severity < 4, or UNKNOWN with severity >= 3 (blocked by an open decision or an unmapped mechanism) |
| P3 | 4 | UNKNOWN with severity < 3 |
| P4 | 64 | in-scope, protection is a code-owned invariant or adequate without migration |
| OUT_OF_SCOPE | 591 | Wiki NOT_APPLICABLE (retained, not scored) |

P1 rows (9):

| Scenario | Title | Families | Dependency | Protection | Evidence |
|---|---|---|---|---|---|
| C01 | Missing grant | F4,F5 | BENEFICIAL | IMPLEMENTED_NOT_QUALIFIED | PASS_RECORDED |
| C09 | Repeat delivery | F7 | BENEFICIAL | IMPLEMENTED_NOT_QUALIFIED | PASS_RECORDED |
| C11 | Credential and permission boundaries | F1a,F1b,F1c | BENEFICIAL | PARTIALLY_ENFORCED | KNOWN_LIMIT_ASSERTED |
| TC-D09-016 | Revocation Propagation Time Across Systems | F4,F5 | BENEFICIAL | IMPLEMENTED_NOT_QUALIFIED | NOT_RUN |
| TC-L06-009 | MCP Tool Shadowing and Name Collision | F1a | BENEFICIAL | IMPLEMENTED_NOT_QUALIFIED | NOT_RUN |
| TC-L06-011 | MCP Gateway Policy: Per-Tool Allow and Deny | F1a | BENEFICIAL | IMPLEMENTED_NOT_QUALIFIED | NOT_RUN |
| TC-L06-013 | Least-Privilege Tool Allow-Listing Per Agent | F1a,F6 | BENEFICIAL | IMPLEMENTED_NOT_QUALIFIED | NOT_RUN |
| TC-L06-015 | High-Risk Action Approval (Human in the Loop) | F4 | BENEFICIAL | IMPLEMENTED_NOT_QUALIFIED | NOT_RUN |
| TC-L06-018 | Agent-to-Agent Message Authenticity | UNMAPPED | BENEFICIAL | KNOWN_GAP | NOT_RUN |

A P1 label means "highest registry-scope priority among rated scenarios", not "qualified", not "approved" and not "needed". Six of the nine are Wiki cases with NOT RUN evidence; TC-L06-018 is a KNOWN_GAP with no R07 family; TC-L06-015 carries the severity of a Wiki subject of which OCS claims a slice.

## 8. Fact, inference, hypothesis, unverified

| Statement | Class |
|---|---|
| Evaluator locations, constructor-only configuration, absence of a registry caller | SOURCE FACT |
| Scenario severity, registry_dependency, existing_protection, all scores | REASONED INFERENCE |
| "Customers would value central control of X" | CUSTOMER HYPOTHESIS (not tested in this corpus) |
| Any claim about Exchange, Replay, Pack, ODES, Verifier, BitRep, Index sources | UNVERIFIED unless the row says it was read |
