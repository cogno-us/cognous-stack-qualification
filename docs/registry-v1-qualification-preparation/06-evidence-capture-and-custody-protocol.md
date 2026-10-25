# 6. Evidence capture and custody protocol

Status: **PREPARATION. Nothing here has been executed.** This is a protocol for a future exact-head run by a designated independent lead. It authorizes no run, qualifies nothing, and creates no verdict. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.

## Roles (kept separate; no role may be held by the builder, the Architect, Copilot or a dependent worker for Tier 1)

| Role | Holds | Must not |
|---|---|---|
| Oracle author | Writes expectations from approved contracts, rulings and frozen-baseline source before any implementation result for that gate is shown | Read builder tests or oracles to set an expectation; edit an expectation after freeze to obtain a pass |
| Builder | Produces the candidate; remediates | Edit expectations; run or supervise the gates it will be judged by |
| Runner (independent lead or supervised operator) | Executes at the frozen candidate pins and retains raw output | Alter fixtures, expectations or pins during a run |
| Evidence reviewer | Reads raw evidence separately from the oracle author and runner | Be the same person or model instance as the oracle author, builder or runner |
| Final adjudicator | The operator | Delegate a Tier 1 verdict to a role above |
| Independent qualification lead | Designated in writing by the independent qualification owner (GAP-G4-13 is OPEN); the only role that may write a Tier 1 verdict | Be the builder, the Architect, Copilot, or a worker dependent on the builder |

This preparation worker does **not** become the independent qualification lead by authoring this package. Until a lead is designated, any execution is PREPARE-mode, labelled "builder-side inspection; Tier 1 not qualified", and never counts toward independence.

## Pre-execution freeze (all required before any gate runs)

1. **Candidate freeze.** A written candidate record: exact commit SHA of each repository (registry, Runtime, Control Plane, qualification) plus the Runtime `engine/safe_executor.py` blob id, the dependency lock hash for each, and the trust-snapshot identity used by the fixtures. The analysed baselines in this package (Runtime `c5e97e87`, Control Plane `7a4bcd40`, registry `d2c472e4`, qualification `be1994a9`, blob `2fc880da`) are **not** the candidate.
2. **Expectation freeze.** A dated qualification-repo commit containing `data/oracles.jsonl`, `data/negative-controls.jsonl`, `data/differential-cases.jsonl`, `data/gate-definitions.json` and `data/fixtures.json`, with a `SHA256SUMS` file covering them. The hash is computed at freeze time, not in this package.
3. **Independence record.** Who authored which expectation, what each author read (the `read_contamination` fields), what the runner and reviewer are, and the lead's written designation and independence statement.
4. **Amendment log.** Any change after freeze is dated, recorded and separately justified. An amendment is never made to obtain a pass. The existing QS13 amendment in the registry repository is developer evidence only and must be re-adjudicated and re-frozen by the lead before it is executed.
5. **Synthetic-only statement.** No network, paid, credentialed or production calls. Synthetic keys are generated for the run and discarded; they are never operational roots.

## Run environment

- A pristine qualification checkout (including ignored files) and a separate pristine checkout of each component at its frozen SHA. Output goes to a new directory outside every checkout.
- Python 3.13 for acceptance, 3.12 supplementary (Round 5 ruling in force); dependencies installed with `--require-hashes --only-binary=:all:` from the committed locks. A missing lock source is restored only where source-backed and reproducible; lock provenance is never fabricated (EXT-S1-0).
- A recorded environment file: OS, kernel, Python and package versions, UID/GID of the runner, filesystem and SQLite version, clock source and any clock-control mechanism, free disk at start and end.
- Disk is checked before and after each run; a full disk invalidates the run.

## Capture requirements (every gate, every run)

| Artifact | Content | Notes |
|---|---|---|
| Raw logs | Full stdout and stderr of each test process, unfiltered | Never summarized in place of raw output |
| JUnit XML | Per-test results with IDs | Collection is not execution: a collected-but-unrun test is NOT_RUN |
| Collected-test list | Every ID collected, run, skipped, xfailed, deselected | Skips, XFAIL and NOT RUN are preserved and reported, not removed |
| Candidate pin record | The freeze record from step 1, copied into the result | |
| Expectation digest | `SHA256SUMS` of the frozen expectation files and a recomputation at run time | A mismatch invalidates the run |
| Durable-state snapshots | SQLite backups (standalone, DELETE-journal) before, after and at each injected fault | Retained for restore and rollback controls |
| Evidence rows | Failure rows, receipts and negative evidence with exact causes, as written by the candidate | Compared to the frozen exact cause; a collapsed cause is a mismatch |
| Repeated-run logs | For race and clock controls: the repetition count, seed, clock schedule and every outcome | One run is not evidence; the required count is in each control |
| `SHA256SUMS` | Hash of every file in the result directory, produced last | |
| Run manifest | Command lines, start and end times, exit codes, operator identity | |

## Custody

- The result directory is copied to write-once or independently held storage by the runner immediately after `SHA256SUMS` is written; the reviewer verifies hashes against that copy.
- Raw evidence is retained as produced. A redaction, if unavoidable, is recorded with the reason, the original hash and the redactor; unredacted original is retained under the same custody.
- No evidence file is edited after hashing. A re-run produces a new result directory; both are retained, including failures.
- Results transfer only to the exact candidate and profile they were run against. Any head change reopens the affected gates.
- Historical results do not qualify current heads. Known-limit assertions are not PASS.

## Verdict vocabulary (per control, per gate)

| Verdict | Meaning |
|---|---|
| PASS | The control ran at the frozen candidate and produced the frozen expected outcome with the frozen exact cause, and the mutation leg failed as required |
| FAIL | A resolved expectation was contradicted, including a collapsed or substituted cause, a committed effect where none is allowed, or a mutation that did not fail the control |
| BLOCKED | The mapping is not representable, a contract or ruling is unresolved, or a prerequisite artifact is missing. BLOCKED is never waived and never reported as PASS |
| NOT_RUN | Not executed (the constitutional addendum's NOT EXECUTED). Preserved as NOT_RUN |
| INACTIVE | The gate does not apply to the V1 profile (QG-02, `max_amount` deferred); the addendum's N/A. Reported as inactive, never as PASS |

### Result kind and aggregation

Every oracle, control and case row carries `result_kind`:

| result_kind | Meaning | Aggregation |
|---|---|---|
| PROTECTION | The row asserts a protection: the frozen outcome and exact cause must hold (and, for controls, the mutation leg must flip it) | Counts toward the gate. PASS requires the expected outcome, exact cause and, for controls, a failing mutation leg |
| PAIR_CONTROL | A positive or over-refusal companion of a protection row (for example the accept leg at a boundary) | Must match its own expected accept or refuse outcome; counts toward the gate together with its partner; the partner's mutation direction applies |
| DISCLOSURE_ONLY | A characterization of an unprotected limit or absent capability (known limits, `NOT_PROTECTED_ASSERTED`, `ABSENT_CAPABILITY_ASSERTED`) | Recorded as CHARACTERIZED with its raw evidence. Never PASS, never counted as protection, never able to close a gate. It does not block a gate on its own and must still be listed in the gate's disclosure section |

A gate is PASS only if every ACTIVE PROTECTION and PAIR_CONTROL row it owns is PASS, every DISCLOSURE_ONLY row it owns is recorded as CHARACTERIZED with evidence, and its reviewer requirements are met. No gate may be reported PASS "by analogy" to builder tests. Only a designated lead may write a Tier 1 verdict; otherwise the candidate reads "NOT INDEPENDENTLY QUALIFIED".
