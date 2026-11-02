# OCS-257-FINAL W1 - R1C-final-source (merged Exchange r3) targeted observation - run record (developer observation)

Not Q7, not independent qualification, not certification; no release or production hold changes (CA16: no claim promotion). All pins are PROVISIONAL DEVELOPMENT PINS.
Static plan: Issue #257 (W2/G2), #254, #256 in cogno-us/cognous-open-control-stack. Governing: Engineering Constitution cogno-us/cognous-engineering-constitution@1c2e920f4e58e07a52e8e2408a506cf7dbc1292b (TESTING_POLICY, CA06, CA16).
Replay trusted match = CALLER-TRUSTED CONFIGURATION MATCH only, never Registry authentication. Structural-only mode remains UNQUALIFIED (leg G asserts the marker).

## Three separately identified observations (never merged into one claim)
| # | label | where | Exchange identity |
|---|---|---|---|
| 1 | R1C-candidate | results/security-wiki-r1c-20261102/ (run 41390031155) | main 8fa8d3e7; ODES/Pack PR heads |
| 2 | R1C-r3-candidate | results/security-wiki-r1c-r3-20261102/ (run 41410531383, tuple r1c/tuple-final.json) | PR #65 CANDIDATE head c1975014, not a merged identity |
| 3 | **R1C-final-source (merged Exchange r3)** - THIS record | results/security-wiki-r1c-final-20261102/ (tuple r1c-final/tuple-merged.json, workflow security-r1c-final-targeted.yml) | **merge commit 37f72b69** (PR #65 merge) |
Observations 1 and 2 are preserved byte-for-byte (r1c/tuple.json, r1c/tuple-final.json and both RUN-RECORDs unchanged; verified by git tree ids before/after the merge from main).

## Exchange identity (verified with gh api at authoring time)
Exchange merge commit 37f72b6944de279a91807221d93a7e91edf04faa, tree c2bc951ef1738f1ff548e11e236191286e74f803 (IDENTICAL to the c1975014 candidate tree), parents 8fa8d3e77c4b24fefddb333795f9b6d3457dc556 (first) and c1975014ad1c28e05383d0655c8c93503c0600c7 (second); PR #65 merged=true, merge_commit_sha 37f72b69, base main; Exchange main HEAD at verification = 37f72b69. The runner re-verifies HEAD and tree of every exact-SHA fetch in CI (mismatch = BLOCKED).
Unchanged components: Replay 6f45e288 (b2932497), ODES d461f0ba (e6ed482d), Pack 39fecb00 (e7b591a5), CP b19c47dd (039219b5), Runtime f7a55e2a (97da8323), Manifest fa170815 (3b0e3772); historical/negative-control components as in tuple-final.json. exchange_main 8fa8d3e7 is the first parent (historical r2 leg).

## Qualification PR state
PR #262 (draft). Base main moved to 660aa7a0258909336952303a5b3f05b5e958f5ac (tree 9f51833a, squash of #260); a conflict-free normal merge from main was made (merge-tree predicted tree e2428a95, actual e2428a95; result = main tree + the 27 PR additions, 0 modifications/deletions; own evidence directories byte-identical by tree id). Observation code head ff38247d62501b935f187dd645bea97e672a3db0 (tree 7b35831e6e2c1a261b50843cc9cff98f1acd887e) = merge 8b077382 + commit adding only .github/workflows/security-r1c-final-targeted.yml and r1c-final/tuple-merged.json. This evidence commit adds only files under results/security-wiki-r1c-final-20261102/.

## Run
- Run: https://github.com/cogno-us/cognous-stack-qualification/actions/runs/41415423418 (attempt 1, event pull_request, head ff38247d, conclusion success, 08:45:48Z-08:50:24Z); job https://github.com/cogno-us/cognous-stack-qualification/actions/runs/41415423418/job/125177969892
- Artifact security-r1c-final-targeted-41415423418-1 (id 13128080276), GitHub-reported digest sha256:8e245b8d80b7f9a6975387294c2f5a8948e79b44507ee364ab438469fb5d073e (367133 bytes).
- **Download outcome: NOT DOWNLOADABLE from the authoring sandbox.** `gh api repos/cogno-us/cognous-stack-qualification/actions/artifacts/13128080276/zip` redirected to the blob host (productionresultssa7.blob.core.windows.net) which answered Forbidden (403). The raw JUnit XML, runner logs, components-identity.tsv, per-test verdict CSVs, mutation outputs, environment files and the artifact's own SHA256SUMS were therefore NOT inspected and NO independent raw-evidence reconstruction is claimed. The readable surface is the check-run annotations (check-run-annotations-job-125177969892.json, 43 annotations, REST JSON as returned) and the job conclusion. Raw verification needs someone who can download the artifact and compare it with the digest above.
- r1c-final/tuple-merged.json sha256 35f2560acf886e8c466e855ac6df150e19d79b4900b2421e6df4fc50a907db17 (the runner copies it and prints its sha256 into the artifact). r1c/run_r1c.py unchanged from observation 2 (sha256 6ec59175ef601b68d61d3291b1ecf3ede701758935b79b386ba5b9115623f638). Workflow is a copy of security-r1c-r3-targeted.yml with new tuple path, tag R1C-final, artifact name and path filters; hash-locked dependencies and action pins unchanged (pytest 8.3.5, pydantic 2.13.5, cryptography 50.0.0, jsonschema 4.23.0; Python 3.13; ubuntu-24.04).
- Profile identity under test: security-runtime-current-20261031-r3 (and -r2 for the historical legs).
- All legs were run (a push triggers a full pull_request run; workflow_dispatch with `legs` is unavailable until the workflow is on the default branch). The Exchange-dependent legs are C1,C2,C3,D1,E1,E2,H; A,B,F,G,I do not depend on the Exchange revision and re-ran unchanged. The 41-case and 244-case batteries were NOT run.
- The pre-existing workflows security-r1c-targeted.yml and security-r1c-r3-targeted.yml also re-ran on this head because the PR touches r1c/** relative to main; both succeeded and are not part of this record.

## Verdicts (from the job annotations; counts are verdict-CSV rows)
| leg | what | PASS | FAIL | BLOCKED | skips |
|---|---|---|---|---|---|
| A1 | merged ODES e2e vs merged Replay (180 + pin) | 181 | 0 | 0 | 0 |
| A2 | merged Pack e2e vs merged Replay (148 + pin) | 149 | 0 | 0 | 0 |
| A3 | ODES full suite (CI configuration) | 3266 | 0 | 0 | 8 SKIP_DOCUMENTED |
| A4 | Pack full suite minus test_cli | 427 | 0 | 0 | 82 SKIP_COVERED (by A2) |
| B1-B3 | pin constants equal Replay merge SHA; d395e37c negatives | 2 / 2 / 1 | 0 | 0 | 0 |
| C1 | Exchange 37f72b69 full tests/test_exchange_input_and_source_repairs.py (474) | 464 | 0 | 0 | 10 SKIP_DOCUMENTED |
| C2 | r3 profile constants (6) equal bound tuple | 6 | 0 | 0 | 0 |
| C3 | REAL-SOURCE: r3 ACCEPTED vs real CP, Runtime, Manifest, Replay, ODES, Pack (verifier and public load_executor_runtime) | 2 | 0 | 0 | 0 |
| D1 | historical r2 ACCEPTED vs genuine r2 tuple; main refuses r3 sources under r2 and the r3 profile name | 5 | 0 | 0 | 0 |
| E1 | REAL-SOURCE refusals (mixed, near-ODES fe3c1416, r2 ODES/Pack/Replay, dirty files, git-replaced Replay/ODES) | 10 | 0 | 0 | 0 |
| E2 | modelled mixed-generation node tests (59) | 55 | 0 | 0 | 4 SKIP_DOCUMENTED |
| F | Replay caller-trusted digest tests (71) | 71 | 0 | 0 | 0 |
| G | structural-only UNQUALIFIED marker | 1 | 0 | 0 | 0 |
| H | Exchange replace-object hardening (39 + 3) | 42 | 0 | 0 | 0 |
| I | CP/Replay FAMILY_TABLE parity | 3 | 0 | 0 | 0 |

## Task T1-T12 mapping
T1 = C3; T2 = D1; T3 = E1 (+E2); T4 = E1 (r2 Replay d395e37c) and B2/B3; T5 = E1 (ODES fe3c1416, 77fd7a1c); T6 = E1 (Pack 96f5f2e1; PR head 143441ac is not fetched in this tuple, see limitations); T7 = F; T8 = F (+M3); T9 = G (+M4); T10 = H, E1 replaced-checkout cases (+M5, M8); T11 = I (+M6); T12 = A1-A4.

## Mutation controls (9/9 MUTATION_DETECTED, none SURVIVED)
M1 A1, M2 A2, M3 F, M4 G, M5 H, M6 I, M7 C3, M8 E1, M9 E1 - all fixed=PASS and failing on the mutant (other failing tests: M1 0, M2 12, M3 10, M4 0, M5 11, M6 0, M7 0, M8 0, M9 3, identical counts to observation 2). M5, M8, M9 and M7 (the Exchange-dependent mutants) were re-confirmed on 37f72b69; r3 pin mutation = M7. Patches unchanged (r1c/mutations/).

## Limitations (disclosed, not waived)
- Exchange tree 37f72b69 is byte-identical to the c1975014 candidate tree, so results are expected to equal observation 2; this record binds them to the merge commit identity, which a candidate-head observation could not.
- Skips are not PASS. C1: 10 SKIP_DOCUMENTED (5 r2 unresolved-placeholder, 4 same-commit-in-both-generations, 1 PR #62 head object absent in the shallow checkout: that byte-identity test did NOT execute). E2: the same 4 same-commit skips. A3: 8 SKIP_DOCUMENTED (rfc8785 missing from the hash lock; Replay-installed-dependent tests). A4: 82 SKIP_COVERED by A2; Pack tests/test_cli.py excluded.
- T6: the task named Pack PR heads 143441ac and 96f5f2e1; the executed Pack negative controls are the r2 Pack 96f5f2e1 (E1) and the pin test in B3. A Pack-143441ac negative control is NOT in this tuple and was not run (it was not added to preserve the existing nine-mutant, tuple-final structure).
- Annotation noise as before: legs with skips carry ::error annotations listing SKIP_* rows (not failures); the gate step passed.
- Exchange residuals stay as in observation 2 (GIT_DIR/alternates/shallow/graft/config/hook injection not inspected; manifest checkout protected by --no-replace-objects only). Not a complete source-integrity proof. The migrated OCS Registry is not consumed or verified.
- Raw artifact content was not inspected (see download outcome). F relies on Replay's own pinned vectors whose independence is asserted by their author.
