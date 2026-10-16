# Phase 0 configuration checkpoint — Evelyne-Claudia bounded comparison

Comparison id: `evelyne-claudia-reachable-20261016`
Scope: Cognous Open Control Stack V1 frozen reference examined independently against
the discipline Evelyne-Claudia Yantony proposed in her LinkedIn exchange:

> Freeze independently. Execute independently. Observe independently. Find independently. Compare afterward.
> Correspondence permits comparison; it does not transfer proof.

This checkpoint is Cognous's independent examination at the configuration level. It is
**not** REACHABLE™'s assessment, does **not** advance any Cognous scenario verdict for
her, and does **not** import REACHABLE labels (DEMONSTRATED / CONTRADICTED / UNRESOLVED
are REACHABLE's to assign; Cognous does not produce them).

## Reference pins (frozen)

| Component | Repository | Revision |
|---|---|---|
| Hub | cogno-us/cognous-open-control-stack | 8517818f |
| Qualification | cogno-us/cognous-stack-qualification | af9f5843 |
| Runtime | cogno-us/cognous-execution-runtime | e20f92e1 |
| Control plane | cogno-us/cognous-control-plane | a34c3dc2 |
| Replay | cogno-us/cognous-replay-bundle | 79ba16d4 |
| Evidence Pack | cogno-us/cognous-governance-evidence-pack | 893aca8d |
| ODES | cogno-us/open-decision-evidence-standard | eb83220c |
| Governed Exchange | cogno-us/cognous-governed-exchange | 8be6c6b8 |
| Manifest | cogno-us/cognous-action-manifest | 2c36bcd0 |

Candidate profile in-tree: `process/security-runtime-f5b-20261016.json`
Strict exchange profile: `security-runtime-f5b-20261016`.
Profile asserts `selected=false`, `reference_release_authorized=false`,
`production_deployment_authorized=false`.

The coordinator's task text named `profiles/security-runtime-f5b-candidate-20261016.json`
(digest `f159158c…`). No file at that path exists in this repository; the actual
candidate profile is the committed `process/security-runtime-f5b-20261016.json` with
digest `a710b8c0eb4a6dba1f0770a957212b32a34fb8042e1d3726ef24a2b1db249ddd`. Treat the
in-tree path as authoritative; the manifest records both the task-provided digest and
the real file digest explicitly rather than hiding the discrepancy.

## Scenario coverage selection

Scenarios named by Evelyne-Claudia: **D01** (baseline), **D03** (primary, authority changes),
**C07** (variant, concurrent authority change). D09 and C06 remain out of scope for this
run; they would require additional capability declarations that are not covered by the
F5b candidate profile without separate qualification.

## Discipline

Phase 0 only; no execution, no instrumentation changes, no package yet. The purpose of
this checkpoint is to make visible: which of the five receipt categories in her 11:10 AM
message are produced natively by the frozen reference, and which require an added
observer or adapter.

## Files

- `README.md` (this file)
- `loaded-profile.json` — the loaded candidate profile verbatim plus digests
- `boundary-map.md` — correction vs. commitment boundaries per scenario
- `observer-spec.md` — observer route, access separation, declared blind spots
- `native-receipt-inventory.md` — per-category inventory, mapping Evelyne-Claudia's
  five categories to native producer records and the one gap we can fairly add
  (Phase 1 writer-entry telemetry; already contemplated by the bounded process)
- `findings-and-gaps.md` — Phase 0 findings and open questions for the owner's go/no-go
