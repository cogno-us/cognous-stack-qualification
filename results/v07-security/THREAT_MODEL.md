# V07 threat model (declared before any attack was executed)

Bounded adversarial assessment of the V06 integrated baseline. Synthetic fixtures, local SQLite, no network. Builder-authored.

**Independence limit (stated up front).** The assessor is the same builder identity that wrote the Runtime V05 guard and the V06 harness. "Independent" here means: attacks and oracles were re-derived from the frozen contracts (EXT-S4-0 ADR, r08-v2 contract sections 7.4, 3.6) and the frozen source, and V06 assertions are not reused as proof. It is NOT an independent-party review. Ed25519 verification is outside scope (SECURITY-HELD; Registry fixtures use the Registry's own signing test helpers).

## Frozen pins
Registry `943ab1831e39fadac1eb2a414ae322ccfa09bc6a`; Control Plane V02 `1bee3696ee6cd8037d142cdbcdb6020e052b0480`; Runtime V05 `4199a6c793cd9ec37a5fd451f7d99265dcf634fd`; Qualification V06 `ae12221831bc39beea6dbf0ae7fda726baeecf1f`; older Control Plane fixture `e66e5f163c5d5c112ff345a2f332b4c3893ee183`.

## Assets and invariants (from the contracts)
I-1 No effect commits unless the claim's binding equals durable, anchored, unexpired, unrevoked selection state at the lock-time clock (ADR 7, contract 7.4).
I-2 No authority transition interleaves between the final guard check and the effect commit (single `BEGIN IMMEDIATE`).
I-3 A binding-less claim never bypasses a required or active governed scope (7.4 item 8); only the listed fallback bases apply.
I-4 Unknown, corrupted, regressed-ahead or unverifiable state is HOLD for every participation; never a permissive fallback (3.6, N-12).
I-5 Revocation and high-water are monotone ("grow only"); replay, rollback or lineage substitution never revives authority.
I-6 A critical evidence failure never leaves a committed effect; a crash leaves no half-effect.
I-7 One claim yields at most one effect; a budget is not exceeded under concurrency.

## Adversaries
- **Caller/holder**: can submit envelopes, claim ids, executor policy objects; cannot write the database or anchor.
- **Claim supplier**: can present claim objects to the trusted-host `provision_claim`, including ones the Control Plane would not issue (forged digests, relabeled profile). Part of the assessment because the Runtime must not rely on issuer honesty for I-1/I-3.
- **Concurrent process**: another OS process using the same database (authority writers, executors).
- **Replayer**: re-submits old signed statements/snapshots (signatures valid, content stale).
- **Storage adversary (bounded)**: can alter or roll back database rows or the host-held anchor file. The contract discloses limits here (3.6); results are classified against that text, not treated as new vulnerabilities.

## Out of scope / unqualified
Cryptographic soundness of Ed25519; real anchor custody; production deployment; the Control Plane workflow issuance path beyond one refusal probe; independent human review.

## Classification rule
A case records `HELD` (the attack failed; invariant held) or `BREACH` (the secure oracle was violated). A BREACH is classified by the contract text: violation of a mandatory contract invariant = HIGH/CRITICAL by effect; behaviour the contract explicitly permits but that weakens defence in depth = MEDIUM; disclosed limits = QUALIFICATION GAP. Missing qualification alone is never reported as a vulnerability.
