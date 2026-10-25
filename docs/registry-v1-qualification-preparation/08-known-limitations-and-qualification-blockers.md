# 8. Known limitations and qualification blockers

Status: **PREPARATION.** This package contains prepared expectations only. Nothing was executed, no V1 candidate exists, no gate is met, and no verdict is given. The preparation worker does not become the independent qualification lead. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.

## Blockers to independent qualification (all open)

| # | Blocker | Effect | Owner |
|---|---|---|---|
| B1 | **No independent qualification lead is designated (GAP-G4-13).** The lead must not be the builder, the Architect, Copilot or a dependent worker | Without a lead every run is PREPARE-mode, labelled "builder-side inspection; Tier 1 not qualified", and QG-14 cannot close | Independent qualification owner / operator |
| B2 | **No V1 candidate exists.** Implementation is not authorized; EXT-S1-1 has not started | There is nothing to freeze or execute | Architect (implementation authorization) |
| B3 | **Contract and ruling items are open** (table below) | Rows tagged `BLOCKED_ON_CONTRACT` stay BLOCKED; BLOCKED is never waived | Architect, component owners |
| B4 | **V1 serialization is not fixed** (records, selection statements, claims, snapshots, durable state) | 138 per-control fixtures are definition-only; the ready part is the contract-derived grids | `EXT-S1-1`, `EXT-S1-5`, `EXT-S4-0` |
| B5 | **No real verifier or operational trust root.** The registry tests use a test double; the Ed25519 adapter (`EXT-S1-7`) is not built; trust root and key ceremony are operator-gated | Authenticity can be evidenced only with synthetic keys; GAP-G3-07 stays open | Operator |
| B6 | **Independent evidence review is not available** (the operator recorded "no second llm for now") | Evidence review must be recorded as not performed until a reviewer exists | Operator |
| B7 | **Existing coverage gaps** the package cannot close by design: 11 undeclared Runtime known-limit tests (GAP-G4-07); no MVP oracle row for a `LocalExecutionPolicy` denial (GAP-G4-09); no scenario-level PASS and nothing at current heads (GAP-G4-01, 02) | QG-13 and QG-14 depend on the owners | Component and qualification owners |
| B8 | **Historical results do not qualify current heads.** `PASS_RECORDED` is a named historical case at g8-r10 pins; D01, D03, D04 stay INCONCLUSIVE; known-limit assertions are not PASS; collection is not execution | No historical PASS is claimed or relied on | n/a |

## Open contract and ruling items behind `BLOCKED_ON_CONTRACT` rows

Counts are generated in [04a](04a-computed-coverage.md): oracles 5, negative controls 19, differential cases 5.

| Open item | Rows waiting |
|---|---|
| OPEN-Q6: Control Plane outcome and record shape for a preconstruction registry deny-all | QO-028, DF-036, NC-096 |
| O-1: R6 mechanics (how an outage extension is held under the effective narrowed limit) | QO-115, NC-114 |
| O-3: claim member list; OPEN-Q3/Q5: structured code carrier at commit time | QO-104, QO-105, NC-102 |
| O-4: upper bound (`AGE_MAX`) and refusal/HOLD code names for invalid age values | QO-052, DF-067, DF-068, NC-118 |
| Route B trusted-context independence (the atomic executor has no institution/domain check; it exists on Route A only) | DF-037 |
| No-registry-input path versus invalid caller ages the constructor accepts today (the cards say both "byte-identical" and "invalid caller refuses") | DF-066 |
| v2 domain-separation cause; Evidence/Replay refusal vocabulary | NC-012, NC-017, NC-018 |
| Cause for a claim epoch ahead of the row; equal-epoch activation cause | NC-021, NC-062 |
| Claim-expiry clamp rule (Option C); clock-rollback detection; snapshot expiry at commit | NC-030, NC-037, NC-039 |
| Key and issuer revocation propagation at commit | NC-044, NC-045 |
| Grant-versus-profile reason | NC-075 |
| Re-baseline procedure; snapshot custody | NC-081, NC-089 |
| Shape code for a withdraw statement carrying a record pin | NC-113 |
| Whether Route A must be refused for a required scope | NC-134 |

## Reconciliation with the Architect's final rulings

The lane workers could not open the rulings document, so they derived ruling-based rows from the P1 plan's restatement. The integration owner read the primary text and corrected what conflicted:

- **Approval revival (QO-065, NC-073).** The ruling is explicit: no automatic revival; a withdrawn narrowing must not reactivate an older approval; the old approval stays invalid. Both rows are now PREPARED with `REFUSE`. Only the exact cause name remains open (`NEW_CODE_PROPOSED`); the plan's earlier "not guaranteed" wording is superseded.
- **Stale or rolled-back epoch (OPEN-Q12).** Rows use REFUSE with a specific stale-epoch cause and HOLD only for genuinely indeterminate authority state. `data/ld02-outcome-map.json` in the P1 plan still shows HOLD for `selection_epoch_stale`; its owner must update it at ratification. The rows are not edited to match the map.
- **Outcome-vocabulary alignment items for the ratification** (rows differ from the vetted-but-unratified LD-02 map): `participation_mismatch` for a required scope (QO-034, QO-035: REFUSE versus map HOLD) and `selection_revoked` as terminal (QO-090, QO-092: REFUSE versus map HOLD). Rows asserting a Runtime gate DENY with the conceptual cause carried as structured detail (QO-079, QO-081, NC-100) follow the map's Route B commit entry.
- **B-lite is rejected and claim-carried identity is mandatory.** No row relies on keyword-argument carriage; identity-without-binding rows (QO-095, NC-028) assert it is not authority.
- This reconciliation is a conflict scan, not a line-by-line review. The independent oracle author or lead must still confirm every `RULING` row against the primary text before freeze.

## Testing policy

Governed by the constitutional addendum on risk-based testing and milestone qualification (constitution PR #4): continuous Level 1 and Level 2 testing by the implementers, comprehensive Level 3 qualification at a frozen milestone. Passing CI and Copilot review remain technical review, not independent qualification, and this addendum changes cadence, not the independence requirement. No conflict with a mandatory existing requirement was found.

## Limits of the package

- **Not executed.** No test, fixture or harness was run against any component. The validator checks structure and cross-references only.
- **Counts are of prepared rows,** not of behaviour covered. A gate with many rows is not closer to PASS; the gate-to-class tagging gaps in [04a](04a-computed-coverage.md) show where coverage is thin or tags need review. QG-11 has only a handful of oracles, and QG-13 relies mostly on differential cases.
- **Proposed new code names (`NEW_CODE_PROPOSED`)** in oracles and controls are placeholders for the ADR, not decisions. Renaming a cause later is an amendment, not a free edit.
- **Race minimums are proposals** (5 barrier runs and 200 free-race runs per ordering, from lane B). The lead confirms or changes them at freeze.
- **Independence is partial.** The lane authors were instructed not to read builder tests or oracles. 19 oracle rows carry a contamination note because the LD-02 outcome map was vetted against builder `decision.py`; it was used only as a contract proposal. The authors are workers of the same session that may be adjacent to the builder; a designated independent author should review or re-derive the expectations before freeze.
- **Control Plane and Runtime facts are source readings** at the analysed pins (Runtime `c5e97e87`, Control Plane `7a4bcd40`), not tested results. Any head change reopens them.
- **Route A is out of V1** and appears only to show it is not credited. **`max_amount` is deferred**; QG-02 is INACTIVE and never counted as PASS.
- **Copilot review is technical review, not qualification.**
