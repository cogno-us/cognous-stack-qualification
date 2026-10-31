# S3 merged-current-tuple 41-case run (developer / local-offline; NOT independent qualification)
Run on freeze commit b48675b7bb3638a938fd3f5f3d80bec36a17a2bf (branch security-wiki/s3-current-tuple-20261031), Issue #254, Constitution 1c2e920f.
* `run-41-merged-tuple/`: the single primary execution (runner tools/run_wiki_s3.py): raw/{junit.xml,log.txt,obs.json,run.json,collect-only.txt,nodeids-41.txt,tuple.json}; raw/native.tar.gz = pytest basetemp (4955 files, tarred to keep the repo small); `SHA256SUMS.runner-listing-incl-native` is the runner's own checksum list of every file including the native tree (digests of the untarred files).
* `run-41-merged-tuple-supplementary-enospc3/`: re-execution (once) of ONLY the 3 cases that the primary run could not complete because the host disk was full (ENOSPC). Labelled supplementary; the primary classification is kept.
* `run-41-merged-tuple-controls/`: refusal-control outputs (scratch).
* `diagnostics-vacuity/`: vacuity diagnostic (post-run, observer only) and the CSV builder.
* `per-test-41.csv`: 41 rows with the 7 required fields (test_id; expected_behaviour; actual_observed_behaviour; first_failure_refusal_boundary; executing_component_revisions; verdict_primary_run; raw_evidence_reference) plus extra columns. For PASS rows the actual-behaviour text summarises the assertion set of the test source (pytest PASS = every assertion held); it is not an independent re-measurement.
* `REPORT.md`: results and scope.
