# Comparison results, candidate g2-r10 (2026-10-20)

**Scope.** Bounded synthetic profile only. The comparator applications (the OPA application and the LangGraph plus OPA application) are configured by Cognous, not vendor implementations. This is not independent certification and not production readiness; operational trust stays on HOLD. Linux only. Nothing here authorizes a release or production use.

Caveats that stay with every report (RP-8, unchanged): the corner plan was authored after inspection of the baseline code and is not blinded, and both plans had no independent review; the shared Cognous wire and signature helpers feed all three configurations.

## Run identity

| Item | Value |
| --- | --- |
| Candidate id | g2-r10 |
| Qualification commit | `32ed191626356642b5bd3871e1f65c405bba702c` |
| Amendments in force | 99 (1 to 99) |
| OPA binary | v1.21.2, sha256 `830ab11f61ffec760b5e19db0d7ad02bf037e13f5ef4d665faeaf17632177527` |
| Hub revision for the registered runner | `8517818fbf817897acd8d8d4b32af2a2f6a46bb6` |
| Seeds, repetitions | 1701 and 1702, five repetitions (Wiki subset) |
| Retained output | `results/comparisons/g2-r10-20261020/` (digests in `SHA256SUMS`) |

The run was started once, ran to completion and has no could-not-check cell. Nothing was edited after the run. The generated report is `results/comparisons/g2-r10-20261020/comparison-report.md`.

## Corner scenarios (19 cases, 10 trials each)

| Configuration | Trials passed | Unexpected effects | False allows | Denied calls |
| --- | ---: | ---: | ---: | ---: |
| OCS (protected destination) | 190/190 | 0 | 0 | 180 |
| OPA application | 130/190 | 50 | 60 | 120 |
| LangGraph plus OPA application | 130/190 | 50 | 60 | 120 |

Both comparator applications pass 13 cases and fail six with 0/10 trials: `unknown_argument`, `empty_effect_identifier`, `unknown_body_field`, `unknown_verifier_field`, `wrong_operation` and `exact_command_replay`. OCS passes all 19. The comparator applications are configured by Cognous with the rule set of the registered plan; a different configuration could close these six. No case is one where a comparator passes and OCS does not.

## Baseline scenarios (24 cases, 20 trials each)

| Configuration | Trials passed | Unexpected effects | False allows | Denied calls |
| --- | ---: | ---: | ---: | ---: |
| OCS (protected destination) | 480/480 | 0 | 0 | 360 |
| OPA application | 480/480 | 0 | 0 | 360 |
| LangGraph plus OPA application | 480/480 | 0 | 0 | 360 |

The three configurations tie. No case is one where a comparator passes and OCS does not.

## Wiki subset (28 cases, 121 scenarios)

| Configuration | Asked | Not expressible | Not claimed | Not asked | Could not check | Trials passed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| OCS (protected destination) | 4 | 92 | 9 | 16 | 0 | 40/40 |
| OPA application | 94 | 11 | 0 | 16 | 0 | 940/940 |
| LangGraph plus OPA application | 94 | 11 | 0 | 16 | 0 | 940/940 |

How to read this table:
- The comparison is destination-only. The protected destination can be asked only the few Wiki scenarios its request interface can express, so most of its cells are not expressible or not claimed. A cell of that kind is not a failure and is not a comparative statement.
- In 23 cases the comparator applications pass and the OCS cell is not expressible or not claimed. They are listed in the generated report with their reasons and are not scored.
- The 16 scenarios not asked of any configuration, and the 11 not expressible for every configuration, are listed with their reasons in the plan file `comparators/wiki/plans/wiki-subset-plan.json`.
- Not expressible and not claimed describe what the configured application can be asked and the claims of the stack as configured. They say nothing about what OPA or LangGraph could do in other hands.
- The cross-reference for the OCS cells that are not scored here is the run of the Wiki-derived tests against the whole stack (290 tests, 285 passing, five failing and reported as non-gating under amendments 78 and 79; none is classified as a major defect). That run uses a different harness and is not scored by this oracle. Details are in `docs/v1-known-limits.md` (entry of 2026-10-20, measured state). That entry also records the controller run at the same pins.

## What the results support

- On the corner set, OCS passes every case and each comparator application fails six, as configured here.
- On the baseline set the three configurations tie.
- On the Wiki subset the comparison asks little of the protected destination, so it neither supports nor counts against it; the comparator applications pass every scenario they were asked.
- There is no aggregate score across sets and no ranking.
