# 01. Frozen-intent oracle specification (Lane A: test oracle preparation)

Status: **PREPARATION ONLY. This is not independent Tier 1 qualification.** No V1 implementation exists, nothing here was executed, and no row below is a result. Every row is a prepared expectation with status `NOT_RUN`; the candidate state is `NOT_QUALIFIED`. Historical `PASS_RECORDED` cases are at the g8-r10 pins and do not carry over. Known-limit assertions are not PASS. Copilot review is technical review, not qualification. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.

Machine-readable rows: [`data/oracles.jsonl`](data/oracles.jsonl) (117 rows, `QO-001` to `QO-117`, one JSON object per line). This page explains the method and lists what is blocked. If the two disagree, the JSONL is the specification and this page is the defect.

## 1. Scope

Eight V1 fields: Runtime `allowed_actions`, `allowed_adapters`, `allowed_units`, `allowed_institutions`, `allowed_authority_domains`; Control Plane `status_max_age_seconds`, `approval_max_age_seconds`, `ActionClass.max_status_age_seconds`. Execution boundary: atomic Route B only (Route A is out of V1; one row records that disclosure). `max_amount` is excluded and gate QG-02 stays INACTIVE (retained, never counted, no oracle or control written for it; one row asserts a sixth `max_amount` key is refused, which protects the exclusion, it does not test the field). Gates QG-01 to QG-14 are preserved; QG-02 is never tagged.

## 2. Method

1. Each oracle states the **intended** outcome of an approved contract for one synthetic input, as a typed outcome (`NARROWED_EFFECTIVE_SET`, `NARROWED_BOUND`, `CALLER_BOUND_RETAINED_RECORDED`, `DENY_ALL_PRECONSTRUCTION`, `REFUSE`, `DENY`, `HOLD`, `ACCEPT_UNCHANGED`, `NOT_APPLIED_VISIBLE`) plus a symbolic cause. Causes use the existing registry `CODES` names from `data/ld02-outcome-map.json` wherever one exists; otherwise a descriptive symbolic name is used and flagged `NEW_CODE_PROPOSED` (15 rows contain that flag). A proposed name is a placeholder for the ADR, never an asserted string.
2. Each row is atomic (one input, one action, one outcome), carries a `must_not` clause (what must never happen), and a `negative_control_hint` (the mutation of a correct implementation that must make the row fail). The hints are for the later mutation legs; they are not mutations that were run.
3. Each row names its `basis` and `basis_type`: `CONTRACT` (78), `RULING` (21), `SOURCE_CHARACTERIZATION` (17), `INVENTORY` (0). `SOURCE_CHARACTERIZATION` rows describe **existing frozen evaluator behaviour** at the pins (Runtime `c5e97e87`, blob `2fc880da`; Control Plane `7a4bcd40`) and are never used to define new behaviour.
4. Where the contract is silent or open, the row is `BLOCKED_ON_CONTRACT` and names the open decision; nothing is guessed (section 5).
5. Scope split: RUNTIME 50, CONTROL_PLANE 29, REGISTRY 26, CROSS 11. Gate tags (a row may carry several): QG-01: 23; QG-03: 19; QG-04: 22; QG-05: 22; QG-06: 15; QG-07: 18; QG-08: 13; QG-09: 24; QG-10: 13; QG-11: 5; QG-12: 16; QG-13: 3; QG-14: 1.

### Basis abbreviations
`docs/p1-extraction-plan/` is the merged P1 plan (registry main `d2c472e4`). Rows cite its documents 02, 03, 04, 07, 08, 09, 10, 11, `data/ld02-outcome-map.json` (MAP) and `data/qualification-gate-matrix.json` (gate matrix); `docs/r08-s01-contract.md` and `docs/r08-preparation/` (contract text, not tests); `docs/decisions/2026-10-25-adr-tr-01-activation-and-epoch-ownership.md` (ADR-REG-TR01); and source at the pins (`engine/safe_executor.py`, `engine/control_plane_adapter.py` at Runtime `c5e97e87`; `src/agent_control_plane/bounded.py`, `runtime_authority.py`, `freshness.py` at Control Plane `7a4bcd40`). "Architect ruling A1 to A4, R6, OPEN-Q3/Q5/Q6/Q12, O-1 to O-5" are cited as they appear in the P1 plan (04, 07, 10, 11) and in the lane brief.

## 3. Independence and blind process

- Expectations were derived from contracts, rulings and source characterization **before** any implementation exists. No implementation result was seen.
- **Not read:** registry builder tests and oracles (`tests/test_r08_*`, `tests/test_s05_*`, `tests/s05_oracle.py`, `r08_support.py`), `docs/r08-s01/qualification-spec.md` (the QS13 amendment), and any builder implementation behaviour. No file under `registry_successor/` or `tests/` was opened.
- **Indirect contamination note (19 rows carry `read_contamination`).** `data/ld02-outcome-map.json` was vetted by its author against builder `decision.py`. It is on the permitted list and is used only as a contract proposal (outcome names, `can_authorize_action`, deny-all convention). Rows that lean on it say so in `read_contamination`. A reviewer who treats the map as builder-derived should discount those rows to "contract proposal".
- **Map versus ruling conflict, resolved in favour of the ruling.** The map still reads HOLD for `selection_epoch_stale` pending OPEN-Q12. The oracles follow the Architect resolution given to this lane: a stale or rolled-back epoch is REFUSE with a specific cause (QO-083, QO-084, QO-089 cite this; QO-087 is the HOLD case), and HOLD only when authority state is indeterminate. The map cell should be updated by its owner; the oracle is not adjusted to match it.
- **Rulings document.** The lane workers could not open the Architect final-rulings project document. The integration owner read it and corrected the conflicting rows (QO-065, QO-034/035, QO-090/092); see doc 08 "Reconciliation". The independent oracle author or lead must still confirm every `RULING` row against the primary text before freeze.
- Source at the pins was fetched read-only into a scratch directory outside every repository (`git fetch --depth=1`); nothing was executed or modified.
- Roles stay separate (07): oracle author (this lane, blind), builder (never edits expectations), runner, evidence reviewer, final adjudicator (operator). No independent qualification lead is designated, so any later execution is "builder-side inspection; Tier 1 not qualified".

## 4. The ten topics

| # | Topic slug | Rows | Count | Blocked | Subject |
|---|---|---|---|---|---|
| 1 | `allowlist_narrowing` | QO-001 to QO-018 | 18 | 1 | Allowlist narrowing (five Runtime fields) |
| 2 | `empty_set_deny_all` | QO-019 to QO-028 | 10 | 1 | Empty-set deny-all (preconstruction versus evaluator denial) |
| 3 | `required_optional_participation` | QO-029 to QO-036 | 8 | 0 | Required and optional participation; scope_required ratchet (A4) |
| 4 | `freshness_limit_narrowing` | QO-037 to QO-059 | 23 | 1 | Freshness-limit narrowing (three Control Plane ages) |
| 5 | `approval_profile_commitment` | QO-060 to QO-065 | 6 | 0 | Approval and profile commitment |
| 6 | `policy_selection_withdrawal` | QO-066 to QO-074 | 9 | 0 | Policy selection and withdrawal (A1); no registry authority over grants |
| 7 | `revocation_expiry` | QO-075 to QO-082, QO-117 | 9 | 0 | Revocation and expiry (activation and commit) |
| 8 | `activation_epoch_rollback` | QO-083 to QO-093 | 11 | 0 | Activation epoch and rollback (A2) |
| 9 | `claim_carried_identity` | QO-094 to QO-105 | 12 | 2 | Claim-carried policy identity |
| 10 | `atomic_effect_time_validation` | QO-106 to QO-116 | 11 | 1 | Atomic effect-time validation (Route B) and R6 |

Notes by topic:

1. **Allowlist narrowing.** Per field: registry subset narrows, registry superset never widens (ten rows); case, substring and wildcard are not members (exact string membership); first-failing-dimension order; caller object not mutated; F1b trusted-context stays independent; an omitted deployed value refuses (availability risk 13, fail closed); a sixth amount key is refused. Grid cells empty and disjoint are in topic 2; equal is covered by the subset/superset pair at their shared values.
2. **Deny-all.** The registry preconstruction deny-all (`registry_deny_all`, stage `pre_dispatch`, no policy built) is a different event from a `LocalExecutionPolicy.check` denial (QO rows state both and forbid collapsing them). QG-01 compares disposition only for empty effective sets (denied, zero effects, claim unconsumed, budget unchanged) and exact reason text and order only for representable non-empty sets. The Runtime accepting empty frozensets is recorded as a characterization. The Control Plane side is OPEN-Q6 (blocked).
3. **Participation.** Required never falls back to the caller policy and is fail closed; optional returns the caller policy unchanged with a visible not-applied marker carrying the true cause; an invalid selection can never be reported as an intentional withdrawal; the `scope_required` ratchet (A4) refuses an optional presentation for a required scope, survives restart, and fails closed on an older restored store.
4. **Freshness.** Validated per-scalar `min` on strict integer seconds for each of the three ages; refusal, never clamping, of zero, float, boolean and invalid caller values; no universal five-second floor; no cross-bound among F4 ages; bound, bound+1 and future-tolerance boundaries on the real `_fresh` semantics; registry above caller keeps the caller value and records non-narrowing. The code floor of at least 1 is **new helper behaviour**; the existing zero-bound behaviour at the pin (an observation at `now` and a future one within tolerance are accepted at bound 0, `bounded.py:2017-2024`) is characterized, not changed, and never described as deny-all.
5. **Approval and profile.** The approval binds to the effective narrowed profile; a caller-profile approval gives `runtime_authority_approval_mismatch`; F4-only narrowing does not touch approvals; the registry never creates, re-issues or revives an approval.
6. **Selection and withdrawal.** A1 `selection_withdrawn` from an authenticated withdraw head (required refuses, optional not applied), malformed withdraw refused, authenticated supersession for the next operation only, a forged withdrawal changes nothing, withdrawal never erases evidence. Two rows cover "no registry authority over grants" (ADR-REG-TR01 decisions 5 and 9 support them).
7. **Revocation and expiry.** Interval `[valid_from, valid_until)`; revocation at activation; at commit under the destination lock with the **lock-time** clock; below-floor snapshots cannot hide a revocation.
8. **Epoch and rollback.** Strictly greater epoch per scope key `(selection_id, consumer_domain, scope)`; equal and lower epoch REFUSE with `selection_epoch_stale`; higher epoch without supersession is the distinct `selection_conflict`; HOLD only for indeterminate state; A2 states `{active, withdrawn, revoked}` and entries `{activate, withdraw, revoke, sync}`; sync cannot manufacture authorization or reverse a revocation; a revoked epoch is not resurrected.
9. **Claim-carried identity.** The binding is mandatory; each of the six members (governing record plus version, selected policy plus selection epoch, enforcing scope, effective configuration digest, activation identity, trust snapshot identity) is substituted alone and must be refused; executor-supplied strings are not authority; identity appears in receipts and failure rows; no string-based decision (OPEN-Q3).
10. **Atomic effect time (Route B only) and R6.** Identity bound and revalidated under the lock; effect, claim and budget commit together; lock-first commit keeps its original identity; lost acknowledgement then revocation stays unresolved; no registry call or socket inside the transaction; Route A disclosed as out of scope. **R6 invariant:** an outage extension never makes an observation acceptable after the effective registry-narrowed freshness deadline (four R6 rows; the ceiling stays `min(caller, registry)`).

## 5. BLOCKED_ON_CONTRACT oracles

Each waits for an open decision. They are retained so the gap is visible; they are not waived and carry no expected value beyond the stated constraint.

| Oracle | Title | Waits for |
|---|---|---|
| QO-018 | Route B trusted-context independence: the atomic executor has no institution or domain check (the cited check is on Route A only) | Same open item as DF-037: Route B trusted-context independence is unspecified |
| QO-028 | Control Plane consumption of a registry deny-all result is undecided | OPEN-Q6: Control Plane outcome for registry deny-all (ADR EXT-S4-0) |
| QO-052 | registry bound above the ADR maximum is refused | O-4: F4/F5 upper-bound constants recorded in the EXT-S1-1 ADR (not yet written) |
| QO-104 | no string-based security decision: a message text that spells a registry code is not a cause | OPEN-Q3 / OPEN-Q5: form of the structured code carrier at commit time (ADR EXT-S4-0) |
| QO-105 | claim member list agrees between the registry identity projection and the claim | O-3: claim member list frozen in the EXT-S1-1 ADR / EXT-S4-0 ADR |
| QO-115 | R6: an extension row whose base was computed from the caller value is invalid | O-1: whether R6 is met by profile narrowing alone or needs a source change in runtime_authority.py / freshness.py / bounded.py |

Further caveats that do **not** block a row but should be read with it: (a) commit-time rows state the outcome (`DENY`, no effect row, claim unconsumed) and a structured cause; the carrier form for that cause is OPEN-Q3/Q5, so no oracle may compare an exception message string; (b) rows that name `NEW_CODE_PROPOSED` causes fix the symbolic cause, and the final string comes from the EXT-S1-1 / EXT-S4-0 ADRs; (c) QO-065 is PREPARED from the Architect final ruling on approval revival (no automatic revival); only its exact cause name is `NEW_CODE_PROPOSED`. The older P1 plan wording ("not guaranteed and is disclosed") is superseded by that ruling.

## 6. How expectations are frozen

1. This lane writes expectations only. Nothing is frozen by this document and no digest is computed or claimed here.
2. A **future freeze commit** in the qualification repository (EXT-S5-6, dated, before any execution) will hash `data/oracles.jsonl` together with the candidate pins and the evaluator blob. After that commit an expectation is never edited to obtain a pass; an amendment is a new dated commit that records the reason, and a mismatch against a resolved expectation is FAIL, an unresolved one is BLOCKED.
3. `BLOCKED_ON_CONTRACT` rows must be resolved (the open decision recorded and the row re-stated from the decision text, not from the candidate's behaviour) or explicitly carried as BLOCKED into the freeze.
4. Rows whose cause is `NEW_CODE_PROPOSED` or whose basis is a `RULING` should be re-confirmed against the primary ADR text at the freeze, and any change recorded as a dated amendment before execution.
5. Execution is out of scope here: race and clock rows need repeated runs with raw logs, effect-boundary rows have nothing to execute until EXT-S4-2 and EXT-S4-4 exist, and none may be reported PASS by analogy to builder tests.

## 7. What this does not do

It does not execute any test, does not qualify any behaviour, does not record any PASS, does not claim the P1 plan is implemented, and does not reopen the approved scope or any ruling. It adds no paid, credentialed or production step. All data in the rows is synthetic (`act-a`, `inst-a`, `dom-a`, and similar); no real credential or key appears.
