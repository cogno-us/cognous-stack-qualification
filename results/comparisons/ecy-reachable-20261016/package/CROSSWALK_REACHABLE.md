# Crosswalk — Evelyne-Claudia's five receipt categories to Cognous artifact fields

Scope: this crosswalk preserves the original Cognous enums (`authorized`,
`denied`, `unknown`, `hold`, refusal reason vocabulary, `source_asserted_not_independently_verified`,
etc.) and keeps the three evidence dimensions **separate**: (a) test execution,
(b) authority authenticity, (c) field-loss / transformation. Correspondence
permits comparison; it does not transfer proof.

## Profile files (both exist; different roles)

| Role | Repository | Path | SHA-256 |
|---|---|---|---|
| Hub-recorded candidate marker | cogno-us/cognous-open-control-stack | `profiles/security-runtime-f5b-candidate-20261016.json` | `f159158c…` (prefix as recorded by coordinator) |
| Qualification-runner profile (authoritative driver in this package) | cogno-us/cognous-stack-qualification | `process/security-runtime-f5b-20261016.json` | `a710b8c0eb4a6dba1f0770a957212b32a34fb8042e1d3726ef24a2b1db249ddd` |

Both files reference the same seven component pins. The hub profile is a
candidate marker; the qualification profile drives `tools/run_security_runtime.py`
and the trial driver used for this comparison.

## 1. Test and authority records

| 1.x sub-item | Artifact → field | Status |
|---|---|---|
| Scenario ID, run ID, action ID, timestamps, test configuration, software versions | `manifest.json#trials[].scenario_id`, `.trial_id`, `.nodeid`, `.pins`; per-trial `fixture.json#proposed_action.action_id` | native, retained |
| Original authority grant: issuer, principal, scope, validity period, grant revision | `native/reconstruction.json#metadata.execution_envelope.operation.{grant_id,grant_revision,principal,authority_domain}`; `fixture.json#authority_assumptions` | native with limit — issuer field is a synthetic constant; **no signed issuer attestation** (declared) |
| Revocation receipt: grant ID, issuing authority, effective time, new revision, provenance | `native/reconstruction.json` refusal records; `transport.json#current_authority_check_at_effect_time`; refusal reason `grant_revoked` | **absent as signed receipt** — see `fixture.json#authority_assumptions.issuer_signature_present=false`. Not fabricated. |

## 2. Decision and intervention receipts

| 2.x sub-item | Artifact → field |
|---|---|
| Action proposal + initial policy decision | `native/proposal.json`; `native/executor.json#decision_id`; `native/cp/run.json` |
| Evidence of which authority revision was evaluated | `native/reconstruction.json` → `resolution_check_event[]` with `phase=input`, `source_revision`; `native/executor.json#execution_envelope.operation.grant_revision` |
| Revocation or correction event | For D03: in-memory status mutation + resulting refusal record; see `fixture.json#authority_assumptions.authority_mutation_method`. No separate revocation-event JSON (declared). |
| Effect-time authority revalidation | `native/reconstruction.json#records[type=effect_time_refusal]`; `native/executor.json#control_plane_evidence.refusal` |
| Enforcement result (allowed/blocked/escalated) | `native/executor.json#execution_result.status` ∈ {`authorized`,`denied`,`failed`,`unknown`}; **original Cognous enums preserved**. "escalated" is not a Cognous enum. |
| Was the execution adapter actually invoked? | `native/executor.json#execution_result.attempted` (bool); `transport.json#writer_entry.attempted` |

## 3. Consumption and state-change evidence

| 3.x sub-item | Artifact → field |
|---|---|
| Receiving component accepted/consumed intervention | `native/reconstruction.json` → `resolution_check_event[]` with `phase=input`, `consumed`, `read_time` |
| Governing-state snapshots before/after correction | `native/destination-observation.json#destination_state`; `destination/destination-snapshot.sqlite3` (post-run isolated snapshot) |
| Was the action committed/prevented/delayed/unresolved? | `observation.json#effect_occurrence_count` (0 or 1); `destination/destination-readback.json#readback` |
| Authoritative destination observation with coverage and limitations | `observation.json#observer_route`, `access_separation`, `trust_boundary_label`, `blind_spots` |

## 4. Consequence evidence

| 4.x sub-item | Artifact → field |
|---|---|
| Independently inspectable observation | `destination/destination-snapshot.sqlite3` (standalone SQLite; recipient reads via read-only connection); `destination/destination-readback.json#integrity_check` |
| Correlation between proposal, intervention, and effect | Stable `effect_id` threads through `proposal.json`, `executor.json`, `reconstruction.json`, `destination-observation.json`; `transport.json#decision_id`, `.attempt_id`, `.effect_id` |
| Preservation of missing / contradictory / inconclusive evidence | `native/reconstruction.json#metadata.executor_failure_reference_verification = "source_asserted_not_independently_verified"`; `transport.json#writer_entry.ack_classification`; `README_FOR_EVELYNE_CLAUDIA.md#limitations` |

## 5. Evidence integrity and review

| 5.x sub-item | Artifact → field |
|---|---|
| Stable event IDs and links | `decision_id`, `effect_id`, `attempt_id`, `grant_id` propagate across all per-trial files |
| Source provenance, artifact hashes, schema versions | `manifest.json#trials[].files[].sha256`; `native/consumers/odes-package.json#provenance.pinned_revisions`, `.profile.implementation_profile_version` |
| Replay bundle, validation results, Evidence Pack | `native/reconstruction.json`; `native/consumers/evidence-pack.json`, `.md`, `-validation.json`; `native/consumers/odes-package.json`, `odes-replay-semantics.json`, `odes-recipient-decision.json` |
| **F5b vs security-generation pairing enforcement** | `native/consumers/f5b-enforcement.json` — for every trial, pass against F5b constants AND fail against security-generation substituted control-plane revision; demonstrates the pairing is enforced by the consumer, not just asserted |
| REACHABLE™ DEMONSTRATED / CONTRADICTED / UNRESOLVED verdict | **intentionally absent on Cognous's side.** Correspondence permits comparison; it does not transfer proof. REACHABLE assigns these labels. |

## Field-loss / transformation / unavailability (separate finding)

| Field in your category | Loss type | Reason |
|---|---|---|
| Issuer signature on revocation (1.c) | **unavailable** | F5b profile declares missing signature verification remains missing |
| REACHABLE verdict (5.d) | **unavailable by design** | Not Cognous's to produce |
| "Escalated" enforcement enum (2.e) | **not applicable** | Cognous enums are `authorized/denied/failed/unknown`; no silent remapping |
| Wall-clock skew (fixture.clocks.wall_time_source) | **transformed** | NOW monkeypatched to simulated timestamp — same for all trials |
| ODES recipient decision (5.c) | **by design: fail** | ODES recipient validator intentionally fails for a bare replay package without issuer/status/use evidence; this is a feature of the recipient contract, not a defect |

## Dimensional separation (do not merge)

- **Execution finding**: did the test exit cleanly and produce the expected native enums?
- **Authority-authenticity finding**: is the authority chain cryptographically grounded?
- **Field-loss finding**: what did the recipient-side cross-walk fail to carry?

These are kept separate here. REACHABLE's assessment may re-combine them under REACHABLE's own standard.
