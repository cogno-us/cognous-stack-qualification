# OCS-257 W2 - R1C-final-source / r3-candidate targeted observation - run record (developer observation)

Not Q7, not independent qualification, not certification; no release or production hold changes (CA16: no claim promotion). Static plan: Issue #257 (W2/G2), #254, #256 in cogno-us/cognous-open-control-stack.
Governing: Engineering Constitution cogno-us/cognous-engineering-constitution@1c2e920f4e58e07a52e8e2408a506cf7dbc1292b (TESTING_POLICY: a test must fail when the weakness is restored; BLOCKED, not PASS, when a prerequisite is missing; CA06 preserve evidence).
Replay trusted match = CALLER-TRUSTED CONFIGURATION MATCH only, never Registry authentication. Structural-only mode remains UNQUALIFIED (leg G asserts the marker).

## Two separately identified observations (and one NOT yet produced)
| observation | label | where | Replay | ODES | Evidence Pack | Exchange |
|---|---|---|---|---|---|---|
| 1 | candidate observation (R1C-candidate) | results/security-wiki-r1c-20261102/ (preserved byte-for-byte; run 41390031155) | 6f45e288 (merge) | fe3c1416 = PR #143 CANDIDATE head | c461ae8c = PR #66 CANDIDATE head (final PR head was 143441ac, docs-only follow-up) | 8fa8d3e7 (main, #64) |
| 2 | R1C-final-source / r3-candidate (THIS record) | results/security-wiki-r1c-r3-20261102/ | 6f45e288 (merge) | d461f0ba (merge) | 39fecb00 (merge) | c1975014 = Exchange r3 CANDIDATE head, not merged identity (PR #65 UNMERGED) plus 8fa8d3e7 for the historical r2 leg |
| 3 | R1C-final (merged Exchange) | NOT PRODUCED | - | - | - | requires the operator merge of PR #65 |

**FINAL merged-head Exchange evidence is NOT yet produced: it requires operator merge of PR #65; then edit the Exchange tuple to the actual merge commit and rerun only legs C, D, E, H.**
Procedure (the Exchange component is ONE line of r1c/tuple-final.json, key "exchange"):
1. `gh api repos/cogno-us/cognous-governed-exchange/commits/<E> --jq '.sha,.commit.tree.sha,(.parents|length)'`; confirm PR #65 merged with merge_commit_sha == E.
2. Edit the single `"exchange": {...}` line: `sha` = E, `tree` = its tree, `role` = "Exchange main merge commit (Exchange #65)". Nothing else changes (r3 profile constants are re-checked by leg C2; if the merge changed them C2 fails).
3. Push to the PR branch (triggers a full run) or, once the workflow file is on the default branch, dispatch only the Exchange legs: `gh workflow run security-r1c-r3-targeted.yml --repo cogno-us/cognous-stack-qualification --ref <branch> -f legs=C1,C2,C3,D1,E1,E2,H` (mutants attached to those legs run with them: M5, M7, M8, M9). Record the new run in a new results directory; do not overwrite this one.

## Run
- Qualification PR (draft): https://github.com/cogno-us/cognous-stack-qualification/pull/262 ; code head ecee392e9cdf785320954ea3eb3b464e05cfbd35 (tree 2dafffd46738f39b7fae59bfbf75c331cbaf9308; parent 8bf224918c01a54e7198ebcdf725d6068c2e0745, tree 4966d41a83031cfab8f10f1d368f0f55ce12b987; base main 7fc2fe602f460d0d4e01d6c3839d61e448a9010b). This evidence commit adds only files under results/security-wiki-r1c-r3-20261102/.
- Run: https://github.com/cogno-us/cognous-stack-qualification/actions/runs/41410531383 (attempt 1, event pull_request, conclusion success), job https://github.com/cogno-us/cognous-stack-qualification/actions/runs/41410531383/job/125162297010
- Artifact security-r1c-r3-targeted-41410531383-1 (id 13124974323), GitHub-reported digest sha256:99c3a6417c36430f95ba6d259175fb31d5244dbad327925d3c39c20d43ec204c (367190 bytes). **The builder cannot download artifacts**: the raw JUnit XML, runner logs, components-identity.tsv, per-test verdict CSVs, mutation outputs, environment files and the artifact's own SHA256SUMS were NOT inspected by the builder. Nothing here is inferred from the artifact; the readable surface is the check-run annotations (check-run-annotations-job-125162297010.txt, 43 annotations) and the green job. Raw verification needs someone who can download the artifact and compare it with the digest above.
- r1c/tuple-final.json sha256 c2c11d3a4ab727f21a3b85b12fec95b9ccd2c7ba1dc0694d7877425643d76bba (the runner prints and copies it into the artifact). r1c/run_r1c.py sha256 6ec59175ef601b68d61d3291b1ecf3ede701758935b79b386ba5b9115623f638; it was 83929f9cccba575e5e16cafa4cb3f0f1a645e0e911ba8c72f1ca0cdcc13ebb46 when observation 1 ran (run 41390031155). Edit: default behaviour unchanged; adds --tuple, --legs, a "realsource" leg type, report text and annotation tag taken from the tuple, bytecode caches excluded from mutant copies. Workflow security-r1c-targeted.yml and r1c/tuple.json are unchanged (the candidate workflow re-ran on this push, run 41410531234, success; that re-run is not part of either record).
- Hash-locked dependencies as observation 1 (pytest 8.3.5, pydantic 2.13.5, cryptography 50.0.0, jsonschema 4.23.0; Python 3.13; ubuntu-24.04). Component fetches are anonymous exact-SHA fetches (persist-credentials false); Control Plane, Runtime and Action Manifest fetched successfully, so no BLOCKED leg on repository access.

## Tuple (exact SHAs; the runner verifies HEAD and tree of every fetch, a mismatch is BLOCKED)
| component | commit | tree | label |
|---|---|---|---|
| Replay | 6f45e288ae37ec7e7712f9296760927d2d843bba | b2932497304ad589b1085d8b586ddc1fc1a2c583 | MERGED main commit (Replay #82) |
| ODES | d461f0ba3feccef3593ab6efdbf930569d669767 | e6ed482de7e9a1eabc3f17641180764803bcbe0b | MERGED main commit (PR #143 merge; parents 77fd7a1c, fe3c1416) |
| Evidence Pack | 39fecb004f3d4c4e87673d79d8d9399314f551e4 | e7b591a5c85d5476cbffa69cf8bd17cac76fb318 | MERGED main commit (PR #66 merge; parents 96f5f2e1, 143441ac) |
| Control Plane | b19c47ddd020409d24e52e70b11359c46265edbb | 039219b5aba7a157fff79781c716067fad7ed985 | main |
| Runtime | f7a55e2a8494801e49193f9f46935f0a971c248d | 97da8323368bb5a573fd157b11a9c1dda1178a10 | real-source check only |
| Action Manifest | fa170815ef96a54c233d0dd9da821b60debabf8b | 3b0e3772e944aa668c8f4b879588c7cc3e2c32be | real-source check only |
| Exchange r3 | c1975014ad1c28e05383d0655c8c93503c0600c7 | c2bc951ef1738f1ff548e11e236191286e74f803 | **Exchange r3 CANDIDATE head, not merged identity** (PR https://github.com/cogno-us/cognous-governed-exchange/pull/65, UNMERGED) |
| Exchange main | 8fa8d3e77c4b24fefddb333795f9b6d3457dc556 | c73d2d5b43c6864dda99746c1978aa6f244ea788 | historical r2 leg (Exchange #64 merge) |
| Replay r2 | d395e37c443fedf1bf6b9a4651338b7b7de4a553 | 0bdee3eacd650ecb0e99781635a972e68cbe2853 | SUPERSEDED (genuine r2 tuple; negative control) |
| ODES r2 | 77fd7a1cb1dd7a2dbc9ac3c02538a617056688ae | d8b33261de975fc504ff8f0ac30a8f47e8ebd43f | r2 tuple; negative control |
| ODES near | fe3c1416bca0c1ea1091f08ba570ecfc68e3bb2f | e6ed482de7e9a1eabc3f17641180764803bcbe0b | PR #143 head: SAME TREE as the merge, one commit different (identity is the commit, not the tree) |
| Pack r2 | 96f5f2e126a9c27a75716658d4d2e85baf94b40b | 2fc26d4c86e65b22bdffedf1090a15e7167440d3 | r2 tuple; negative control |
| Replay P2 | 40012b8c174c6f25685bd5d9bc93ff46cc9a5842 | b68151a2f957a468d398a4bcb4b3936217eb449d | prerequisite of the Pack full suite only |

## Verdicts (from the job annotations; counts are rows in the verdict CSVs)
| leg | what | PASS | FAIL | BLOCKED | skips |
|---|---|---|---|---|---|
| A1 | merged ODES d461f0ba current-generation e2e against merged Replay 6f45e288 (180 tests + pin check) | 181 | 0 | 0 | 0 |
| A2 | merged Pack 39fecb00 current-generation e2e against merged Replay 6f45e288 (148 + pin check) | 149 | 0 | 0 | 0 |
| A3 | ODES full suite (CI configuration) | 3266 | 0 | 0 | 8 SKIP_DOCUMENTED |
| A4 | Pack full suite minus test_cli (P2 Replay on path) | 427 | 0 | 0 | 82 SKIP_COVERED (by A2) |
| B1 | identity: ODES CUR_REPLAY_REVISION and Pack CUR_REPLAY_PIN equal the Replay MERGE SHA 6f45e288 | 2 | 0 | 0 | 0 |
| B2 | ODES d395e37c negatives by node id (superseded refused; pin is one literal) | 2 | 0 | 0 | 0 |
| B3 | Pack negative by node id (pinned gate refuses [d395e37c]) | 1 | 0 | 0 | 0 |
| C1 | Exchange r3 candidate head: FULL tests/test_exchange_input_and_source_repairs.py (474 collected) | 464 | 0 | 0 | 10 SKIP_DOCUMENTED |
| C2 | Exchange r3 profile block constants (6) equal the bound CP/Runtime/Manifest/Replay/ODES/Pack SHAs | 6 | 0 | 0 | 0 |
| C3 | REAL-SOURCE: r3 ACCEPTED against real CP, Runtime, Manifest, Replay 6f45e288, ODES d461f0ba, Pack 39fecb00 (verifier `_verify_refusal_profile_sources` and public `load_executor_runtime`) | 2 | 0 | 0 | 0 |
| D1 | historical r2: r2 ACCEPTED against the genuine r2 tuple (Replay d395e37c, ODES 77fd7a1c, Pack 96f5f2e1, same CP/Runtime/Manifest) on Exchange main 8fa8d3e7 (verifier and public entry) and on the r3 candidate head; main refuses the r3 sources under r2; main has no r3 profile and refuses the name | 5 | 0 | 0 | 0 |
| E1 | REAL-SOURCE refusals on the r3 candidate head (10): r2 Replay with r3 ODES/Pack; one-commit-different ODES fe3c1416 (same tree); r2 ODES; r2 Pack; complete r2 source tuple; r2 profile against r3 sources (mixed); dirty tracked entry file in Replay; dirty tracked non-entry file in ODES; git-replaced Replay (refs/replace); git-replaced ODES | 10 | 0 | 0 | 0 |
| E2 | Exchange modelled mixed-generation node tests (-k, 6 functions, 59 collected) | 55 | 0 | 0 | 4 SKIP_DOCUMENTED |
| F | Replay caller-trusted expected-digest tests at 6f45e288 (71) | 71 | 0 | 0 | 0 |
| G | Replay structural-only default mode: UNQUALIFIED marker, no authenticated label | 1 | 0 | 0 | 0 |
| H | Exchange replace-object hardening on the r3 candidate head (42 = 39 + 3 r3-specific) | 42 | 0 | 0 | 0 |
| I | CP b19c47dd vs Replay 6f45e288 FAMILY_TABLE parity | 3 | 0 | 0 | 0 |
Lettering follows the OCS-257 W2 task (A e2e, B identity, C Exchange r3, D historical r2, E mixed refusal, F digest, G structural-only, H replace hardening, I parity); it differs from observation 1's letters.

## Real-source check (closes the open item that r3 negatives were modelled with fake checkouts)
Each case runs in a fresh interpreter (r1c/legC/child_verify.py) with GAX_RUNTIME_COMPATIBILITY_PROFILE set, calls Exchange's own `_verify_refusal_profile_sources(cp_root, molt_root)` (C3 also the public `load_executor_runtime()`) against REAL fetched checkouts that are fresh bytecode-free copies verified clean with `git status --porcelain --untracked-files=all --ignored`. A refusal counts only if the message names the expected module ("candidate source identity mismatch: <module>"); an acceptance counts only if the imported modules come from the verified checkouts. Results are the C3, D1 and E1 rows above (17 of 17 as expected). Case logs are in the artifact (not inspected by the builder).
Not attributable from the message alone: the refs/replace refusal and the dirty non-entry file refusal both surface as the generic module mismatch; their attribution rests on mutants M8 (refs/replace refusal removed) and, for the generic path, M9.

## Mutation controls (9/9 MUTATION_DETECTED; each required test passed on the fixed tree and failed on the mutant; none SURVIVED)
| mutant | leg | weakness restored | other failing tests |
|---|---|---|---|
| M1 | A1 | ODES CUR Replay pin reverted to d395e37c | 0 |
| M2 | A2 | Pack CUR Replay pin reverted to d395e37c | 12 |
| M3 | F | Replay expected-digest comparison bypassed (resealed substitution accepted under trusted match) | 10 |
| M4 | G | Replay default-mode structural marker replaced by an authenticated-sounding label | 0 |
| M5 | H | Exchange `--no-replace-objects` removed from every source-reading git call | 11 |
| M6 | I | Replay FAMILY_TABLE class_age contract version altered (r08-v2 -> r08-v3) | 0 |
| M7 | C3 | Exchange r3 profile Replay pin reverted to d395e37c | 0 |
| M8 | E1 | Exchange refs/replace refusal removed from the checkout source check | 0 |
| M9 | E1 | Exchange source identity comparison disabled | 3 |
M1-M6 reuse observation 1's patches (C-M1, C-M2, D-M1, E-M1, F-M1, P-M1; r1c/mutations/, unchanged) re-validated here against the merged sources and the Exchange r3 candidate head; M7-M9 are new (r1c/mutations/M7-M9-*.patch).

## Findings and limitations (disclosed, not waived)
- Exchange is a CANDIDATE head (PR #65 unmerged): every Exchange row (C, D, E, H, M5, M7-M9) binds to c1975014, not to a merged identity. D1 binds the r2 historical rows to Exchange main 8fa8d3e7 as well. Observation 3 is pending the operator merge.
- Evidence Pack: observation 1 used PR head c461ae8c (tree 65181250); the merge 39fecb00 has tree e7b591a5 (docs-only follow-up 143441ac, 3 files x 1 line). Observation 2 is the first observation bound to the merge tree and re-ran A2/A4/B1/B3 on it.
- Skips are not PASS. C1: 10 SKIP_DOCUMENTED = 5 "all r2 pins are resolved" (the r2 unresolved-placeholder tests have nothing to exercise), 4 "same commit in both generations: not a substitution" (CP and Runtime are identical in r2 and r3), 1 "PR #62 head object not present in this checkout (shallow clone)" (that byte-identity test of the original profile block did NOT execute). E2 carries the same 4 "same commit" skips. A3: 8 SKIP_DOCUMENTED as in observation 1 (1 needs rfc8785, not in the hash lock; 7 need the accepted Replay installed; ODES example-package semantic tests therefore have no executed CI coverage). A4: 82 SKIP_COVERED by A2; Pack tests/test_cli.py is excluded and not executed.
- Replace-ref coverage count: the 35 tests of observation 1 become 39 on the r3 head because the r3 profile joins the parametrized strict-profile set (+3 substitution modes, +1 unrelated-branches test); with the 3 r3-specific tests, H = 42. The earlier "35" figure is not comparable.
- Finding: Exchange's verifier refuses ANY untracked or ignored importable file in a verified checkout, including `__pycache__/*.pyc` left by earlier test runs (seen in a pre-run on the builder's machine: ODES src/odes/__pycache__ made r3 acceptance fail). A consumer that runs tests from a checkout and then verifies the same checkout will be refused; this leg therefore verifies clean copies. This is stricter-than-needed behaviour, not a weakness.
- Known Exchange residuals stay as the r2 profile comment states: GIT_DIR / GIT_OBJECT_DIRECTORY / GIT_ALTERNATE_OBJECT_DIRECTORIES, alternates, shallow and graft files, git config / filter / hook injection are not inspected; the manifest checkout is protected by `--no-replace-objects` only (no refs/replace refusal); this is not a complete source-integrity proof and nothing here tests those residuals.
- The real-source check exercises one Manifest example file and clean copies of the fetched checkouts; it is not a run of the full Exchange workflow with the Registry (the migrated OCS Registry is not consumed or verified by the Exchange).
- Replay trusted match remains caller-trusted configuration matching only; structural-only remains UNQUALIFIED; F relies on Replay's own pinned vectors whose independence is asserted by their author.
- The job passed on the first run (no dashboard cancellation, no rerun needed); the 5-minute timeout concern for the dashboard check did not occur on this head.
- Annotation noise: on a green job, legs with skips also carry ::error annotations listing SKIP_* rows (not failures); the gate step passed. Annotations list every row only for legs of 100 rows or fewer (others: summary plus non-PASS rows); per-test CSVs are artifact-only.
- Untouched: PR #260 (branch security-wiki/s3-current-tuple-20261031), results/security-wiki-s3-20261031, results/security-wiki-r1b-20261101, r1b/, results/security-wiki-r1c-20261102/ (observation 1), security-r1c-targeted.yml, r1c/tuple.json.
