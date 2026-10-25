# 5. Synthetic fixture definitions

Status: **PREPARATION.** These are definitions and deterministic input grids. No key, record, claim, approval, database image or run has been created, and nothing here executes against any component. Synthetic data only; no network, paid, credentialed or production use. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.

## What is ready and what is not

Fixtures fall into two groups.

1. **Ready now (no V1 code needed).** `method/fixture_grids.py` generates `data/fixture-grids.json` deterministically with the standard library. It holds inputs plus the expected effective value derived from the contract formula alone: allow-lists use `effective = caller INTERSECT registry`, ages use a validated per-scalar `min` on strict integer seconds. It is not the output of any implementation. Contents: a 64-row caller-by-registry set grid over a three-member synthetic universe (applies to each of the five Runtime fields), 5 near-miss exact-string members (case, whitespace, prefix, wildcard, confusable character), 36 valid age pairs, 20 invalid age inputs (refused, never clamped), 28 boundary offsets against the frozen freshness rule, 5 half-open validity-interval points and 6 strict-greater epoch points. The upper bound on age values (`AGE_MAX`, open decision O-4) is deliberately not assumed.
2. **Definition only (waits for V1 formats).** Keys, trust snapshots, records, selection statements, claims, approvals, durable-state images, race barriers and evidence rows cannot be produced honestly until the V1 serialization is fixed by `EXT-S1-1`, `EXT-S1-5` and `EXT-S4-0`. They are defined here by purpose and variants. Building them against builder behaviour would defeat independence, so the lead builds them from the frozen contract at freeze time.

**Readiness summary.** All 139 per-control fixtures (`FX-B-nnn`, one per negative control) are `DEFINITION_ONLY_NEEDS_V1_FORMAT` because each composes at least one base fixture that needs a V1 format. The grids above are the reusable, ready part and are consumed by the oracles and differential cases, not by a per-control fixture.

## Base fixture library (`data/fixtures.json`)

| Id | Name | Definition | Readiness |
|---|---|---|---|
| `FXB-CLOCK` | Controllable clock | A clock schedule the runner sets (lock-time clock, check-time clock, rollback jump). Reusable now. | Ready now (no V1 code) |
| `FXB-SETS` | Caller and registry set grids | The five-set relation grid in data/fixture-grids.json. Reusable now. | Ready now (no V1 code) |
| `FXB-AGES` | Age value, boundary and invalid-input grids | Valid pairs, invalid inputs, boundary offsets in data/fixture-grids.json. Reusable now. | Ready now (no V1 code) |
| `FXB-KEYS` | Synthetic signing keys | Throw-away key pairs generated at run time and discarded: signer A, signer B, a revoked key, an unknown key. Never an operational root. Verifier adapter format is not final. | Definition only: waits for V1 formats |
| `FXB-TRUST` | Trust snapshot | Snapshot with version, expiry, per-scope min_epochs and issuer/key revocations; stale, expired and downgraded variants. | Definition only: waits for V1 formats |
| `FXB-RECORD` | Typed registry records | Records for the five-set family and the F4/F5 age families: valid, widened, dropped field, unknown family, re-digested, wrong participation. | Definition only: waits for V1 formats |
| `FXB-SELECT` | Selection statements | Select and withdraw statements with epochs, supersession, validity interval and scope key. | Definition only: waits for V1 formats |
| `FXB-CALLER` | Caller policies and profiles | Caller LocalExecutionPolicy sets; Control Plane caller age values and ActionClass profile. | Definition only: waits for V1 formats |
| `FXB-CLAIM` | Authorization claims | Claim with and without the claim-carried effective-policy binding; substituted, swapped and missing variants. | Definition only: waits for V1 formats |
| `FXB-APPROVAL` | Approvals | Approval bound to profile P0 and to narrowed profile P1, with approval generation; the narrow-then-withdraw sequence. | Definition only: waits for V1 formats |
| `FXB-STATE` | Durable-state images | SQLite images of selection state, revoked set and activation log: healthy, truncated, missing table, corrupted rows, restored-older, never seeded from a claim. | Definition only: waits for V1 formats |
| `FXB-RACE` | Transaction-stage barriers | Hooks at named transaction stages (such as the destination _transaction_stage) to order revocation against the commit lock; repetition and seed recorded. | Definition only: waits for V1 formats |
| `FXB-ROUTE` | Route hosts | A Route B atomic host (V1) and a Route A host (characterization only, never credited). | Definition only: waits for V1 formats |
| `FXB-EVIDENCE` | Receipts, failure rows and replay inputs | Committed receipts and failure rows carrying identity and exact causes; substituted and omitted identity variants. | Definition only: waits for V1 formats |

## Per-control fixtures

`data/fixtures.json` maps each negative control to its own fixture id (`FX-B-nnn`, the description written by the control's author) and to the base fixtures it composes. Usage of base fixtures across the 138 controls:

| Base fixture | Controls using it |
|---|---|
| `FXB-AGES` | 24 |
| `FXB-APPROVAL` | 6 |
| `FXB-CALLER` | 50 |
| `FXB-CLAIM` | 29 |
| `FXB-CLOCK` | 27 |
| `FXB-EVIDENCE` | 18 |
| `FXB-KEYS` | 16 |
| `FXB-RACE` | 6 |
| `FXB-RECORD` | 44 |
| `FXB-ROUTE` | 55 |
| `FXB-SELECT` | 80 |
| `FXB-SETS` | 7 |
| `FXB-STATE` | 71 |
| `FXB-TRUST` | 48 |

## Rules

- Keys are generated at run time, used once and discarded. They are never operational roots, and no key ceremony or trust root is implied (operator-gated).
- Fixtures never seed durable state from a claim; a control that does so is itself a negative control.
- Expected values are fixed from the contract before any implementation result is shown; a fixture is never edited to obtain a pass.
- A grid or fixture that touches `max_amount` is out of scope (QG-02 inactive).
- Fixtures for Route A exist only to show it is not credited.
