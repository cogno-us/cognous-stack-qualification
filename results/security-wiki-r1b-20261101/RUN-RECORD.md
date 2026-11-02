# R1B targeted qualification - run record (developer observation)

Status: developer observation on a GitHub-hosted runner. NOT Q7, NOT independent qualification, NOT certification. No claim promotion (CA16). Success of any Replay case is a CALLER-TRUSTED CONFIGURATION MATCH only, never REGISTRY_AUTHENTICATED.

- Workflow run: https://github.com/cogno-us/cognous-stack-qualification/actions/runs/41259860519 (event pull_request, attempt 1, job 124710711881, conclusion success, about 1 minute). Run started 2026-11-01T01:09:19Z.
- Workflow/runner commit under test (PR #261 head): `bd56d2855415e412ba7c19562486856a124fa46b`; base main `5409d4776a9daff204fc97b71958b4dee12687b0`.
- Components (exact SHA, HEAD and tree verified by the runner): Replay `2d8b00664572e1adeb899c6722a71befbff141ba` tree `b2932497304ad589b1085d8b586ddc1fc1a2c583`; Exchange `4184c1e3fe8500503bc11aae38088963e942c000` tree `c73d2d5b43c6864dda99746c1978aa6f244ea788`. Frozen S3 baselines recorded for context only, not run.
- Artifact `security-r1b-targeted-41259860519-1` (id 13064991778, 52753 bytes), GitHub digest `sha256:1985cd0357ce8a9517eb9113dc01e40816c557b0c1e2eeca3a4e63c3d0e5e6e0`. The builder cannot download it; the readable per-case surface is the check-run annotation set saved here as `check-run-annotations-job-124710711881.txt` (sha256 in SHA256SUMS). The job summary text was not retrievable by REST and is not reproduced.

## Observed verdicts (read from the check-run annotations)
| leg | PASS | FAIL | BLOCKED |
|---|---|---|---|
| Replay PR #82, 71 tests R1-P01..R1-N09 (+2 auxiliary) | 71 | 0 | 0 |
| Exchange PR #64, 35 replace-ref tests | 35 | 0 | 0 |

Replay expected-digest provenance (annotation `prov=`): 39 INDEPENDENT-HARDCODED-VECTOR, 1 NON-INDEPENDENT-COPIED-FROM-RECORD (R1-N03, accepted by design), 31 N/A (no digest comparison reached or no digest supplied). Independence of the PINNED vector is asserted by the test author and not verifiable here.

## Mutation results (each required test failed on the mutant and passed on the restored fixed tree)
| mutant | weakness | required failing tests | verdict |
|---|---|---|---|
| replay-M1 | expected-digest comparison bypassed | R1-N02, R1-N04 (4 further tests also failed: N02b, N02c, N07, P01c) | MUTATION_DETECTED |
| replay-M2 | explicit None expected digest accepted | R1-N05, R1-N09 | MUTATION_DETECTED |
| exchange-E1 | `--no-replace-objects` removed | not-interpreted (3), manifest-checkout (3); the before-execution test also failed | MUTATION_DETECTED |
| exchange-E2 | refs/replace refusal removed | test_checkout_with_a_replace_ref_is_reported | MUTATION_DETECTED |
Survivors: 0. Patch prefixes (sha256): M1 94d513d5fb71, M2 87ffd0642e37, E1 4b42f81a7b22, E2 3940857ba498.

## Other checks on the PR head
r1b-targeted success; CodeQL and Analyze (actions, rust, javascript-typescript, python) success; validate / validate-and-build were still in progress when this record was written (see the PR for their final state).

## Limits
Raw artifacts not downloadable by the builder; digests above are GitHub-reported, not independently recomputed. Four hand-chosen single-line mutants only. Replay run with PYTHONPATH=src (no editable install). Exchange verifier residuals (GIT_DIR, alternates, shallow/graft, config/filter/hook injection) not tested. Change-impact: none of the frozen S3 41 cases exercises the Registry-governed Replay profile; the Exchange-driven subset is affected only through the source-verifier path covered by the 35 tests. Recommendation: no rerun of the 41 or 244 cases.
