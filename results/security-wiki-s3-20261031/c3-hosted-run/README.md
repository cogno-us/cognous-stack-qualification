# C3 hosted observation (GitHub Actions) - S3 current tuple, frozen 41-case battery

Status: a separate GitHub-hosted observation (C3). Developer evidence, NOT independent qualification, not Q7, not certification; it replaces
neither C1 (38 PASS / 0 FAIL / 3 BLOCKED, primary) nor C2 (41 PASS / 0 FAIL / 0 BLOCKED, supplementary recovery). No release or production hold changes.

## Run #1 - SUPERSEDED (harness defect), kept visible
- Run 41229883384, head 93d5807e4724e52732bdf0b6eaca4d7250689ef9, job 124621702447, 2026-10-31 18:32Z. Metadata: `run1-metadata.json`, `run1-jobs.json`; annotations: `run1-annotations.json`.
- It reported "39 FAIL, 0 BLOCKED" and a green job. Those 39 were environment errors: the workflow installed only `.github/locks/cryptography-pydantic-pytest-a9a750.txt`, but the
  ODES component imports `jsonschema` at module level (`odes/schema_validation.py`). 36 cases died with `ModuleNotFoundError: jsonschema` and 3 assertions wrapped that text. None reached a
  security assertion, so run #1 says nothing about security behaviour. The helper also labelled such errors FAIL instead of BLOCKED, and the job did not fail.
- Not hidden, not deleted. Its artifact `security-wiki-s3-c3-hosted-41229883384-1` exists on GitHub.

## Run #2 - the fixed workflow
- Run 41231370965, head ca541b9e0dcaabc092aaf6a3102af6812b94b014, job 124626105489, 2026-10-31 18:50:45Z-18:57:38Z, conclusion success. Metadata: `run2-metadata.json`, `run2-jobs.json`; annotations: `run2-annotations.json`.
- Fix: also installs the already-committed hash lock `.github/locks/jsonschema-pyyaml-c943d3.txt` (`--require-hashes`); imports jsonschema/cryptography/pydantic/pytest/yaml before the frozen run;
  the helper classifies ModuleNotFoundError / No module named / ImportError: cannot import name as BLOCKED AND as a harness problem that fails the job; emits a per-test `::notice`. Test: `tests/test_s3_hosted_summary.py`.
- Result (from the annotation, junit-derived, preliminary): PASS 41, FAIL 0, BLOCKED 0; collected 41, executed 41; python 3.13.17, pytest 8.3.5, jsonschema 4.26.0. Same as C2; no id differs from C2/C1 where visible.
- Limit of the annotation: GitHub truncates a notice message at 4096 characters, so `run2-annotations.json` lists the per-test lines for only the first 28 of 41 ids (the header counts cover all 41). The remaining
  per-id verdicts are therefore not individually visible here; fix for future runs = emit chunked notices (not applied: it would trigger a third hosted run).

## Unverifiable here
- Artifact `security-wiki-s3-c3-hosted-41231370965-1` (19.8 MB; also `...-41229883384-1`, 4.3 MB) exists on GitHub but could not be downloaded from this environment (egress to the blob host denied; job logs also 403).
  Per-case hosted verdicts come from the annotation only until someone downloads and checks the artifact (junit.xml, per-test CSV, SHA256SUMS-all).

## Other
- `junit-rehearsal1-NOT-EVIDENCE.xml`: Worker H's local rehearsal (39 fail / 2 pass without jsonschema). NOT EVIDENCE of any hosted or security result; kept only to document the diagnosis.
- `SHA256SUMS` covers the files in this directory.
