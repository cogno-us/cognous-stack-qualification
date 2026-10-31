# C3 hosted observation (GitHub Actions) - S3 current tuple, frozen 41-case battery

Status: a separate GitHub-hosted observation (C3). Developer evidence, NOT independent qualification, not Q7, not certification; it replaces
neither C1 (38 PASS / 0 FAIL / 3 BLOCKED, primary) nor C2 (41 PASS / 0 FAIL / 0 BLOCKED, supplementary recovery). No release or production hold changes.

## Run #1 - SUPERSEDED (harness defect), kept visible
- Run 41229883384, head 93d5807e4724e52732bdf0b6eaca4d7250689ef9, job 124621702447, 2026-10-31 18:32Z. Metadata: `run1-metadata.json`, `run1-jobs.json`; annotations: `run1-annotations.json`.
- It reported "39 FAIL, 0 BLOCKED" and a green job. Those 39 were environment errors: the workflow installed only `.github/locks/cryptography-pydantic-pytest-a9a750.txt`, but the
  ODES component imports `jsonschema` at module level (`odes/schema_validation.py`). 36 cases died with `ModuleNotFoundError: jsonschema` and 3 assertions wrapped that text. None reached a
  security assertion, so run #1 says nothing about security behaviour. The helper also labelled such errors FAIL instead of BLOCKED, and the job did not fail.
- Not hidden, not deleted. Its artifact `security-wiki-s3-c3-hosted-41229883384-1` exists on GitHub.

## Runs #2, #3, #4 - the fixed workflow
- Run 41231370965, head ca541b9e0dcaabc092aaf6a3102af6812b94b014, job 124626105489, 2026-10-31 18:50:45Z-18:57:38Z, conclusion success. Metadata: `run2-metadata.json`, `run2-jobs.json`; annotations: `run2-annotations.json`.
- Fix: also installs the already-committed hash lock `.github/locks/jsonschema-pyyaml-c943d3.txt` (`--require-hashes`); imports jsonschema/cryptography/pydantic/pytest/yaml before the frozen run;
  the helper classifies ModuleNotFoundError / No module named / ImportError: cannot import name as BLOCKED AND as a harness problem that fails the job; emits a per-test `::notice`. Test: `tests/test_s3_hosted_summary.py`.
- Result (from the annotation, junit-derived, preliminary): PASS 41, FAIL 0, BLOCKED 0; collected 41, executed 41; python 3.13.17, pytest 8.3.5, jsonschema 4.26.0. Same as C2; no id differs from C2/C1 where visible.
- Run #3: 41231979036, head 60cdb9296aa6f04f8b177875797e749e5dd63985 (triggered by the evidence commit, because the PR path filter re-evaluates the whole PR diff), success; header PASS 41 / FAIL 0 / BLOCKED 0, collected 41, executed 41. Files `run3-*.json`.
- Run #4: 41232844591, head 6c5d89a49c3de29ac78cd01e6e1587010e2b0a3a (chunked-annotation helper), job 124630435286, success; header PASS 41 / FAIL 0 / BLOCKED 0, collected 41, executed 41. Files `run4-*.json`.
- Which ids are visible: in runs #2 and #3 GitHub truncated the single notice at 4096 characters, so only the first ~28-29 of 41 per-test lines are visible (all PASS); the other 12-13 are covered only by the header counts (41/0/0).
  In run #4 the helper emitted two chunked notices (1/2, 2/2) and all 41 ids are visible, every one PASS (`run4-annotations.json`).
- Compared with C2 (41 PASS) and C1 (38 PASS / 3 BLOCKED): no visible id differs from C2.
- A further hosted run is triggered by the commit that adds this directory (same PR path-filter behaviour). It is a trailing observation; its annotations are deliberately NOT captured here to avoid an endless evidence/run loop. Its result is reported in the PR/coordinator report only.

## Unverifiable here
- Artifacts `security-wiki-s3-c3-hosted-<run>-1` for runs 2-4 (run 2 is 19.8 MB; also `...-41229883384-1`, 4.3 MB) exists on GitHub but could not be downloaded from this environment (egress to the blob host denied; job logs also 403).
  Per-case hosted verdicts come from the annotation only until someone downloads and checks the artifact (junit.xml, per-test CSV, SHA256SUMS-all).

## Other
- `junit-rehearsal1-NOT-EVIDENCE.xml`: Worker H's local rehearsal (39 fail / 2 pass without jsonschema). NOT EVIDENCE of any hosted or security result; kept only to document the diagnosis.
- `SHA256SUMS` covers the files in this directory.
