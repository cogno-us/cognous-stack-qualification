# V07 findings and disposition

Bounded adversarial assessment of the V06 baseline at the frozen pins (Registry `943ab183`, Control Plane V02 `1bee3696`, Runtime V05 `4199a6c7`, Qualification V06 `ae122218`; older Control Plane fixture `e66e5f16`). Synthetic local SQLite only. **Assessor = the builder identity that wrote the Runtime V05 guard and the V06 harness; this is not an independent-party review.** Ed25519 is SECURITY-HELD and not assessed. Threat model and the predeclared inventory: `THREAT_MODEL.md`, `INVENTORY.md` (committed at `b1c6644e`, before any attack was run; Addendum A was added after the first wave and before its two cases ran).

## Execution record (local; budget 50)
| Run | Cases | Result |
|---|---|---|
| 1 (commit `591ee470`) | 37 | 37 harness PASS: 32 HELD, 1 BREACH, 4 CHARACTERIZED (`local-runs/run1-first-wave`) |
| 2 | A11, I05 | A11 HELD; I05 recorded HELD but its stderr showed a missing test dependency (`cryptography`), i.e. an environment error, not a security result — **I05 run 2 is withdrawn** (`local-runs/run2-addendum`, kept) |
| 3 | I05 | HELD with a real outcome (`local-runs/run3-i05-rerun`) |
| **Total** | **40 executions** | no case skipped; no failed attack discarded |

Effective result per case: 39 distinct cases — HELD 34, BREACH 1 (A08), CHARACTERIZED 4 (A09, D01, D08, I01), INCONCLUSIVE 0. The CI run re-executes all 39 at the frozen pins (not counted against the local budget).

## Findings
### F-01 MEDIUM — Registry policy narrowing is not verified by the Runtime at effect time (case A08, D08)
- **Component/commit:** Runtime V05 `4199a6c7`, `engine/registry_selection_authority.py::check_effect`; contract r08-v2 §7.4 item 3.
- **Invariant:** "The Registry policy can reduce caller permissions but cannot expand them" (V06 acceptance 5; mission P0 "unauthorized policy expansion").
- **Preconditions:** a claim supplier that can call the trusted-host `provision_claim` with a claim the Control Plane would not issue: all identity members correct (record triple, activation_ref, epoch, snapshot), `effective_policy_digest` set to the digest of a WIDER policy, commitment recomputed; the executor is then given that wider policy.
- **Reproduction:** `suites/security-v07/test_adversarial.py::test_a08_...` (Registry payload allows only `act-list`; claim and executor policy carry `act-list, act-extra`; envelope action `act-extra`).
- **Expected vs observed:** expected refusal; observed `executed`, one effect committed (`local-runs/run1-first-wave/results.json`, case A08). The guard compares the claim-carried digest only with the digest of the executor's own policy; it never compares the executor policy with the activated record's payload, which it holds (`selection_activation_v1.record_json`).
- **Why MEDIUM, not HIGH:** contract §7.4 item 3 states in terms that `effective_policy_digest` "is not compared to durable state ... narrowing itself is enforced by the evaluator on the policy the executor was given", so the behaviour conforms to the frozen contract; the Control Plane refuses an unapproved binding at issuance (case I04, HELD); and an honest flow cannot widen (executor policy digest must equal the issuer-composed `min(record, caller)` digest, so its five sets are within the record). Exploitation needs a claim supplier outside the honest Control Plane.
- **Escalation condition:** if the Architect treats the Runtime as an enforcement point for Registry narrowing independent of the claim supplier (the V06 acceptance wording could be read that way), this is HIGH and the disposition becomes BLOCK.
- **Consequence:** an effect outside the active Registry policy can commit when claim issuance is compromised or mis-composed; the Registry restriction is only as strong as the issuer.
- **Owner / remediation:** Runtime (guard) with a Registry contract amendment to §7.4 item 3: refuse when any of the five executor policy sets is not a subset of the activated record's payload sets (local rows only; no new authority source).

## Characterized behaviour (not findings)
- **A09 (LOW / hardening):** `max_amount` and target prefixes are outside the F1AB payload and remain caller-owned; with the five Registry sets unchanged, an amount above the default cap executed. Contractual, but a "narrowed" selection does not bound them.
- **D08 (LOW / QUALIFICATION GAP):** `execution_claims_v1.claim_json` is not authenticated at lock time; editing it in place (no commitment recompute) changed the effective digest and an effect committed. Requires write access to the database file, which also permits direct effect rows; the selection tables, by contrast, are hash-chained and anchored. Same condition as F-01 but via storage.
- **D01 (disclosed limit):** a consistent rollback of the database AND the host-held anchor resurrected a withdrawn selection (effect committed). ADR 3.6 discloses this as undetectable; the anchor custodian is operator-gated. Not a new vulnerability; stays an unqualified boundary.
- **I01 (coverage gap C):** the Runtime wrapper `worker21-authority-effect.yml` still calls the reusable workflow at `1c1755ff…`, older than the V06-qualified revision. A change belongs to the Runtime repository.

## Coverage gaps / unqualified boundaries
- Coverage gap A: only one Control Plane issuance probe (I04) exists; no claim issued by the Control Plane workflow was carried through the Runtime guard (fixtures use different scopes).
- Coverage gap B: the in-process stage-hook race of V06 was supplemented by one OS-process race (C01: 50 effects then 110 refusals, every effect's guard head below the withdrawal sequence) and a two-process double-claim (C02); one timing-dependent run each, not exhaustive.
- Coverage gap D: I03 refused because its hand-built binding was invalid, so it does not isolate pydantic 2.11 behaviour (weak evidence). I05 shows Control Plane V02 *issuance* works and still refuses a tampered binding under pydantic 2.11.9; Runtime-side verification of successor claims under 2.11.9 remains untested.
- Not assessed: Ed25519 soundness, anchor custody, Registry→Control Plane publication, production deployment, independent human review.

## Case results (HELD = attack failed)
A01 A02 A03 A04 A05 A06 A07 A10 A11 HELD; **A08 BREACH (F-01)**; A09 CHARACTERIZED; C01–C07 HELD (C01 overlapped the race: executed 50 / denied 110); D02–D07 HELD; D01, D08 CHARACTERIZED; T01–T08 HELD; I02 I03 I04 I05 HELD; I01 CHARACTERIZED.

## Disposition
No CRITICAL or HIGH finding was demonstrated under the stated classification. **PASS with one MEDIUM finding (F-01); BLOCK if the Architect escalates F-01 to HIGH.** Standing holds unchanged: V08–V09 not authorized; Ed25519 SECURITY-HELD; Tier 1 not started; Release / Publication / Production HOLD.
