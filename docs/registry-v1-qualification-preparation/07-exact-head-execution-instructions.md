# 7. Exact-head execution instructions

Status: **PREPARATION. Instructions for a future run. Nothing here has been executed, and no V1 candidate exists.** Placeholders in angle brackets are filled at freeze time. The commands are templates, not tested procedures; the lead validates them against the frozen candidate before relying on them. This document does not designate an executor and creates no verdict. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.

**Cadence.** Per the constitutional addendum ([Risk-based testing](https://github.com/cogno-us/cognous-engineering-constitution/blob/main/addenda/RISK_BASED_TESTING.md)), this procedure is the Level 3 milestone run: execute it once per approved freeze and again only for the scope affected by a material remediation. Do not run it after every implementation PR; implementation PRs use Level 1 and Level 2 testing owned by the implementing workers. Reuse the existing qualification infrastructure for execution; introduce no new runner or dashboard.

## Preconditions (any unmet condition means STOP, status BLOCKED)

| # | Precondition | Evidence |
|---|---|---|
| E1 | A V1 candidate exists and is frozen: exact SHAs for registry, Runtime, Control Plane and the qualification repository, and the evaluator blob id | Candidate pin record ([06](06-evidence-capture-and-custody-protocol.md) step 1) |
| E2 | Expectations are frozen in a dated commit with a `SHA256SUMS` | Freeze commit SHA |
| E3 | An independent qualification lead is designated in writing, with an independence statement | Designation record. Without it, the run is PREPARE-mode and every output is labelled "builder-side inspection; Tier 1 not qualified" |
| E4 | The prerequisite contracts and rulings for every ACTIVE control are recorded (controls marked `BLOCKED_ON_CONTRACT` stay BLOCKED) | The ADR records from `EXT-S1-1` and `EXT-S4-0` |
| E5 | Applicable CI for the candidate repositories is green at the exact heads, using the observed workflow and check names (EXT-S2-G); no branch-protection requirement is invented | Check-run listing per head |
| E6 | Disk space and runner isolation verified | Environment record |

## Procedure

1. **Verify the freeze.** Check out the qualification repository at the freeze commit. Recompute `SHA256SUMS` for the frozen expectation files and compare with the recorded values. Stop on any mismatch.
2. **Prepare pristine checkouts.** For each component repository, `git init`, `git fetch --depth=1 <url> <frozen-sha>`, `git checkout FETCH_HEAD`, and confirm `git rev-parse HEAD` equals the frozen SHA and the tree is clean (including ignored files). Confirm the Runtime blob: `git rev-parse <frozen-sha>:engine/safe_executor.py` equals the recorded evaluator blob; a change is a candidate change and reopens the affected gates.
3. **Install dependencies reproducibly.** `python -m pip install --require-hashes --only-binary=:all: -r <lock-file>` for each component. Record versions. Do not fetch anything not in a lock.
4. **Record the environment.** Write the environment file ([06](06-evidence-capture-and-custody-protocol.md)). Set no credentials. Confirm no network access is needed by the run.
5. **Collect, then run, in the fixed gate order.** Collect all controls first and write the collected-test list (collection is not execution). Then execute serially in this order: QG-13 baseline regression, QG-01, QG-07, QG-03, QG-04, QG-05, QG-06, QG-08, QG-09, QG-10, QG-11, QG-12. QG-02 is INACTIVE and is not run. QG-14 is the process gate and is assessed last from the retained evidence.
6. **Differential cases.** For each case in `data/differential-cases.jsonl`, run the frozen baseline first and the candidate adapter second against the same synthetic fixture. Use each case's `comparison_type` and `candidate_comparison` to decide what must hold: `BYTE_IDENTICAL`, `REASON_EQUIVALENT`, `CHECK_ORDER_PRESERVED` and `UNCHANGED_FILE` compare to the baseline; `NARROWER_ONLY` allows only earlier or additional refusal; `KNOWN_LIMIT_PRESERVED` and other `DISCLOSURE_ONLY` rows record the characterization and are never PASS. Where `candidate_comparison` states a candidate requirement that differs from the baseline (for example DF-103), the stated requirement is the expectation and the baseline is context. Never edit an expected value to match the candidate.
7. **Negative controls.** For each control in `data/negative-controls.jsonl`, build its synthetic fixture from `data/fixtures.json`, apply the attack step, and compare the outcome and the exact cause with the frozen expectation. Then follow the row's `mutation_leg`: disable the single named check in a throw-away copy of the candidate and require the control to FAIL. A PROTECTION control whose mutation does not fail it is itself FAIL. Exceptions: PAIR_CONTROL rows run the mutation in the over-refusal direction named by the row; DISCLOSURE_ONLY rows use a labelling or surface mutation (or none) and are recorded as CHARACTERIZED; NC-093 uses a disposable evaluator mutant as stated in doc 02 section 5.
8. **Race and clock controls.** Repeat the number of times each control specifies, with the recorded seed and clock schedule. Retain every outcome. One run is not evidence.
9. **Fault injection.** For atomic-boundary controls, inject at each named transaction stage and take SQLite snapshots before and after, as in [06](06-evidence-capture-and-custody-protocol.md).
10. **Seal.** Write `SHA256SUMS` over the entire result directory last. Copy to independent custody. Hand the directory and the frozen expectations to the evidence reviewer.
11. **Report by gate.** For each gate list every control with PASS, FAIL, BLOCKED or NOT_RUN, preserving failures, skips, XFAIL and NOT RUN. Report historical known limits separately. State the candidate pins and that the verdict transfers only to them.

## Stop conditions

- A pin, hash, blob or expectation mismatch.
- A control that requires network, credentials or paid services.
- A disk-full or environment fault during a run (the run is void; retain the evidence and start a new result directory).
- A finding that challenges the approved eight-field Route B scope, the claim-carried binding or the narrowing rule. Report it to the Architect; do not adjudicate it in the run.

## What the run must not do

Run any integration test against incomplete components and call it qualification; rewrite expected results to match new code; credit Route A; credit `max_amount` or QG-02; treat Copilot review as qualification; report a gate PASS from builder tests; or write a Tier 1 verdict without a designated lead.
