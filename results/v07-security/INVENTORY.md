# V07 case inventory and secure-outcome oracles (committed before execution)

Budget: max 50 targeted case executions (parametrized and reruns counted). Planned: 37. "Secure" = the oracle. Any other observed outcome is a BREACH, classified afterwards by the contract text.

| ID | Pri | Attack | Secure oracle |
|---|---|---|---|
| A01 | P0 | successor-profile claim with explicit `policy_binding: null` | refused at provisioning or guard; zero effects |
| A02 | P0 | legacy downgrade: bound claim stripped of binding and relabeled legacy (commitment recomputed) over a required scope | REFUSE `selection_missing`; zero effects |
| A03 | P0 | `activation_ref` = hash of a real log entry that is not the active `activate` | refused; zero effects |
| A04 | P0 | unknown extra binding member (`policy_generation`) injected | refused (`field_invalid`/model); zero effects |
| A05 | P0 | claim provisioned after the selection was withdrawn | REFUSE `selection_withdrawn`; zero effects |
| A06 | P0 | optional selection, (selection, epoch) pair revoked after claim issue | REFUSE `selection_revoked`; zero effects |
| A07 | P0 | claim field altered without recomputing the commitment | refused at provisioning; zero rows |
| A08 | P0 | claim `effective_policy_digest` replaced by the digest of a WIDER policy (commitment recomputed), executor given that wider policy, narrow selection active | refused; zero effects |
| A09 | P0 | executor policy with the five Registry sets equal but caller-owned dimensions widened (`max_amount`, target prefixes) | characterization: record whether the Registry-declared sets still bound the effect; dimensions outside the F1AB payload are caller-owned (contract) |
| A10 | P0 | second activation (epoch 2) supersedes the active epoch 1 without withdrawal; epoch-1 claim presented | REFUSE_STALE; zero effects |
| C01 | P1 | OS-process withdrawal racing a stream of executions | every committed effect has guard `log_head_sequence` below the withdrawal sequence; executions after it refuse |
| C02 | P1 | two OS processes execute the SAME claim simultaneously | exactly one effect |
| C03 | P1 | two claims sharing one `budget_id` (max 1) executed concurrently | at most one effect |
| C04 | P1 | concurrent authority writers (two snapshot syncs) | store verifies afterwards; log chain intact |
| C05 | P1 | process killed between effect insert and commit | zero effects; claim still `issued`; one retry succeeds exactly once |
| C06 | P1 | process killed immediately after commit | exactly one effect; replay refused |
| C07 | P1 | long-lived destination instance A; instance B withdraws; A executes | REFUSE (no cached authority) |
| D01 | P1 | restore older DB AND rewrite the host-held anchor to match | characterization: contract 3.6 discloses this as undetectable; record only |
| D02 | P1 | anchor ahead of the store | HOLD `store_unknown` |
| D03 | P1 | anchor head hash altered | HOLD `store_unknown` |
| D04 | P1 | scope-required (ratchet) row deleted with guards dropped; binding-less claim | HOLD (not fallback) |
| D05 | P1 | durable generation counter lowered with guards dropped | HOLD |
| D06 | P1 | selection tables dropped while a store is configured | HOLD |
| D07 | P1 | database file truncated after provisioning | no effect committed; error surfaced |
| D08 | P1 | stored `claim_json` altered after provisioning (digest widened, no recompute) | characterization: claim rows are not authenticated at lock time; record only |
| T01 | P2 | replay an older trust snapshot version | refused; state unchanged |
| T02 | P2 | later snapshot that un-revokes a key (revocations grow only) | revocation persists: claim still refuses |
| T03 | P2 | re-submit the epoch-1 signed activation after epoch 2 is active | refused; epoch unchanged |
| T04 | P2 | re-submit an old activation after withdrawal to resurrect it | refused; state stays withdrawn |
| T05 | P2 | lineage substitution: activate a different `selection_id` for the scope | refused (`selection_conflict`) |
| T06 | P2 | record identity substitution: same record id/version, mutated payload, statement pins original digest | refused |
| T07 | P2 | malformed canonical serialization: duplicate-key JSON statement text | refused; state unchanged |
| T08 | P2 | missing/raising verifier on activation | refused; state unchanged |
| I01 | P3-C | Runtime wrapper workflow pin at the frozen Runtime | record the reusable-workflow SHA it uses (coverage gap if older than the qualified one) |
| I02 | P3-D | successor claim on the older Control Plane fixture | refused, never downgraded |
| I03 | P3-D | successor claim with V02 under pydantic 2.11.9 | fail closed (refused or error); never an effect |
| I04 | P3-A | Control Plane materializes a claim with a binding whose digest disagrees with the approval | Control Plane refuses |

Classification of any BREACH follows THREAT_MODEL.md. This file is not edited after execution; results are in `results.json` and `FINDINGS.md`.
