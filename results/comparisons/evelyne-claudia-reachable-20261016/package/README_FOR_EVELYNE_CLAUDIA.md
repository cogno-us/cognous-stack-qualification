# Reciprocal evidence package — Cognous Open Control Stack V1 bounded comparison

For: Evelyne-Claudia Yantony (REACHABLE™)
From: Cognous (André de Lima) — V1 frozen reference, Phase 4 export
Comparison id: `evelyne-claudia-reachable-20261016`

## Discipline (preserved verbatim)

> Freeze independently.
> Execute independently.
> Observe independently.
> Find independently.
> Compare afterward.
>
> Correspondence permits comparison; it does not transfer proof.

This package is the Cognous half of the independent examination. REACHABLE's half
is yours to run under REACHABLE's own methodology and evidentiary standards. This
package does not transfer proof, does not import REACHABLE verdicts, and does not
assert interoperability acceptance.

## Scenarios run (as you selected)

| Scenario | Role | Case in frozen suite |
|---|---|---|
| D01 | baseline — valid action | `test_effect_and_commit_boundary[valid]` |
| D03 | primary — authority changes (grant revoked between proposal and effect-time check) | `test_denial_preserves_actual_journal_refusal_and_destination[revoked-grant_revoked]` |
| C07 | variant — concurrent authority change at commit (C0 residual-race characterization) | `test_effect_and_commit_boundary[race]` |

Two diagnostic trials per scenario (six total). Trial IDs: `ec-D01-t1`, `ec-D01-t2`, `ec-D03-t1`, `ec-D03-t2`, `ec-C07-t1`, `ec-C07-t2`. No reliability estimate is claimed from two repetitions.

D09 and C06 remain out of scope for this round, as agreed.

## Frozen reference pins

| Component | Repository | Revision |
|---|---|---|
| Hub | cogno-us/cognous-open-control-stack | 8517818f (tag `public-reference-f5b-20261016` where published) |
| Qualification | cogno-us/cognous-stack-qualification | af9f5843 |
| Runtime | cogno-us/cognous-execution-runtime | e20f92e104aba2ba6ad06120d8549c6170eaf63f |
| Control plane | cogno-us/cognous-control-plane | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 |
| Replay | cogno-us/cognous-replay-bundle | 79ba16d48b9be1e059b3045989c7df960c3df1c2 |
| Evidence Pack | cogno-us/cognous-governance-evidence-pack | 893aca8dfb27ba5c5f3e833f2d29210ca7fc92e3 |
| ODES | cogno-us/open-decision-evidence-standard | eb83220c82f942e429a5e3ef5f677fdd5057ef84 |
| Governed Exchange | cogno-us/cognous-governed-exchange | 8be6c6b80da8c5038d66419f84c10cc529f78137 |
| Manifest | cogno-us/cognous-action-manifest | 2c36bcd0b620dbfe7ad924bc7196a3f0c04c5c5e |

Loaded qualification-side profile: `process/security-runtime-f5b-20261016.json`
(SHA-256 `a710b8c0eb4a6dba1f0770a957212b32a34fb8042e1d3726ef24a2b1db249ddd`). The
hub-side candidate marker is published at
`profiles/security-runtime-f5b-candidate-20261016.json` in the hub repo (digest
prefix `f159158c…`). These are two files with distinct roles — the hub profile
records the candidate marker; the qualification profile drives the runner — and
both reference the same seven pins. See `CROSSWALK_REACHABLE.md` for the mapping.

The candidate profile asserts `selected=false`, `reference_release_authorized=false`,
`production_deployment_authorized=false`. **No release or production authority
is advanced by this package.**

## Your five receipt categories — table of contents

Each scenario directory under `scenarios/<D01|D03|C07>/<trial>/` carries the data
each category needs. The crosswalk file names field locations exactly.

| # | Your category (verbatim) | Where in this package |
|---|---|---|
| 1 | Test and authority records | `manifest.json`; per-trial `fixture.json`; `native/consumers/odes-package.json` → `provenance.pinned_revisions` and `profile.implementation_profile_version` |
| 2 | Decision and intervention receipts | per-trial `native/proposal.json`, `native/executor.json`, `native/reconstruction.json`, `transport.json` |
| 3 | Consumption and state-change evidence | per-trial `observation.json`, `destination/destination-readback.json`, `destination/destination-snapshot.sqlite3` |
| 4 | Consequence evidence | per-trial `destination/destination-readback.json` (post-run read-only snapshot) + `observation.json` with blind-spot disclosure |
| 5 | Evidence integrity and review | `manifest.json` (sizes + SHA-256); `SHA256SUMS`; `verify_export.py`; per-trial `native/consumers/evidence-pack*`, `odes-*.json`, `f5b-enforcement.json`; `CROSSWALK_REACHABLE.md` |

## What Cognous established (as the executor of its own examination)

1. **D01 (`valid`), six-of-six trial halves on the baseline**: a single intended
   effect was committed; destination state=`applied`; effect-count=1; executor
   reached writer entry; result status=`authorized`. Observed via local
   in-process oracle plus post-run read-only SQLite snapshot.
2. **D03 (`revoked`), two trials**: with the grant mutated to `revoked`
   between the authorize decision and the executor's effect-time input check,
   the executor refused with reason `grant_revoked`, `result.status=denied`,
   `result.attempted=False`, destination state=`absent`, effect-count=0. The
   refusal reason is preserved in the Replay bundle (`EffectTimeRefusal`), the
   Evidence Pack (`refusal_vocabulary_summary.series[0].version=runtime-authority-reasons/0.1`),
   and the ODES package.
3. **C07 (`race`), two trials**: with the effective grant mutated inside the
   destination's commit path (between the effect-time check and the row
   insert), the writer attempted but the destination refused the commit; the
   executor returned `effective_grant_changed_at_commit`; destination state=`absent`;
   effect-count=0. **This confirms the published C0 residual-race limit of the
   F5b profile; it is not a demonstration of qualified distributed atomicity.**
4. **F5b pairing is enforced by the consumers.** For every trial we validated the
   ODES package against both consumer-constant sets (F5b and the earlier
   `security` generation) and recorded the result in `native/consumers/f5b-enforcement.json`.
   In all six trials, the F5b pins pass semantics and a substitution of the
   `security` generation control-plane revision causes the consumer to fail. The
   enforcement is demonstrated by construction, not by assertion.
5. **Package byte integrity.** Every distributed file is listed in
   `manifest.json` with length and SHA-256; `SHA256SUMS` is also present. The
   `verify_export.py` recipient-side verifier reproduces these checks and runs
   tamper controls (described below).
6. **Observer trust boundary** declared, not softened. The run-time observer is
   `EffectiveGrantDestination.observe()` — same OS user, same Python process,
   same destination object as the writer. A **local synthetic oracle**, not an
   independent external witness. Per-trial `observation.json` names access
   separation, consistency, horizon, and blind spots. The exported SQLite
   snapshot can be read later with an isolated read-only connection; that is a
   recipient-side check, not a run-time independent witness.
7. **Diagnostic repetitions, not reliability estimates.** Two trials per
   scenario, distinct trial IDs, no claim of distribution over trials.

## What REACHABLE™ must independently assess

Cognous does **not** produce DEMONSTRATED / CONTRADICTED / UNRESOLVED verdicts
and does not supply them in this package. The following are precisely the
assessments that are REACHABLE's to make, from this evidence or from an
independent run:

- Whether, for each scenario, authority **remained valid at the point of
  consequential commitment**, or if an earlier legitimate transition improperly
  lent evidentiary standing to a later one.
- Whether **withdrawal or correction can still prevent an effect before the
  commitment boundary** under REACHABLE's standard — for the three scenarios as
  run and for the race-case specifically (where Cognous's own position is that
  C0 does not promise prevention; the race is characterized, not prevented).
- Whether we can **independently establish what actually changed**, given the
  observer's declared trust boundary — i.e., whether the local synthetic oracle
  (plus the exported snapshot read-back) suffices for REACHABLE, or whether an
  external witness would be required to lift the finding.
- Whether evidence integrity (hashes, canonical commitments, consumer
  validation) under REACHABLE's standard reaches "DEMONSTRATED" for each
  transition — proposal → decision, intervention → consumption, consumption →
  enforcement, enforcement → consequence.
- The two explicit absences preserved in this package:
  - **Signed revocation receipt / issuing-authority attestation (your 1.c).**
    The F5b profile does not sign revocations; the native refusal reason
    `grant_revoked` carries the fact of revocation but not an issuer signature.
    REACHABLE must assess whether this absence leaves consumption-to-enforcement
    UNRESOLVED under REACHABLE's standard.
  - **REACHABLE verdict column (your 5.d).** Intentionally absent on Cognous's
    side. REACHABLE assigns these labels.

## Limitations (plain)

- SCQOS / fleet-level / human / observer-independence tests are not covered by
  this profile.
- The exchange compatibility profile is `security-runtime-f5b-20261016`; only
  the reference `run_exchange` path is exercised. Exchange transport adapters
  under other configurations are unusable under this security profile and were
  not tested here.
- Clock domain is simulated (`NOW` is monkeypatched); wall-clock skew is not
  exercised in this comparison.
- No paid trials. No external send from this examination.
- The owner HOLD on publication, selected flag, and release/production
  authorization remains in effect. "Package ready to share" is distinct from
  "sent"; the latter requires separate explicit instruction identifying the
  recipient and channel.

## Reproducing

See `verify_export.py` and `manifest.json`. The six per-trial `test-results.xml`
files link each result to its node id, command, source revision, run and trial.
