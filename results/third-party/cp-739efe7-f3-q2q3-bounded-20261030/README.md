# F3 Q2/Q3 bounded qualification: OCS-F3-Q2Q3-BOUNDED-v1

Work package OCS-F3-Q240-BOUNDED-QUALIFICATION (Archetype C). Tracker #240; design plan #252; dossier PR #253 (merge `07aa90553da41305bd38fd54447b3fbc29ed6cbc`).

## NOT claims (read first)
This is a bounded, same-lineage technical record. It is **not** an independent or competent certification, **not** an acceptance or closure of Q2 or Q3, **not** a Tier 1 result, **not** a pin-export result, **not** an isolation of `scope.authority_domain` or `effective_profile_digest`, and **not** a statement about CP `8616d5f`, `main` or Python 3.12. Placement under `results/third-party/` is a directory convention and asserts no independence. Registry record 12 Class A requirements still control. Q2 and Q3 remain OPEN. Original F3-A remains FAIL (23 assertions); successor F3-A remains a conditional scoped technical PASS pending human adoption of record 11.

## Result per case (14 pytest tests, 14 passed in each of two runs; 0 skipped)
| Case | Result | Evidence class |
|---|---|---|
| FC-H1 host_profile_digest, claim issuance, masked host | PASS, successor-semantics-conditional | diff-isolated on one masked-host pathway; claim leg follows successor semantics (PermissionError, no claim, no refusal write); frozen-literal durable-refusal reading not met (0 refusals, FC-H1-A07) |
| FC-H2 second masked-host workflow, execute | PASS | diff-isolated on a second masked-host pathway (n=1); durable refusal observed |
| FC-H3a unmasked-host contrast control | PASS | bounded control; guard-first refusal (`runtime_authority_approval_mismatch`); not isolating |
| FC-H3b unmasked-host contrast control | PASS | bounded control; joint (4 ECB leaves); not isolating |
| FXE-JOINT effective_profile_digest joint transition | PASS | JOINT only; base diff `{approval_commitment, catalogue_digest}`, ECB diff `{digest, effective_profile_digest}`; no isolation |
| N-CLAIM-JOINT authority-domain natural joint refusal | PASS, successor-semantics-conditional | JOINT only; base diff `{manifest_digest, proposal_commitment}`, ECB diff `{digest, scope.authority_domain}`; claim leg yields PermissionError with generic text, no refusal write (0 refusals, N-CLAIM-JOINT-A04); no isolation |

Assertion/precondition PASS rows per run: FC-H1 34, FC-H2 27, FC-H3a 14, FC-H3b 17, FXE-JOINT 102, N-CLAIM-JOINT 82. No FAIL, BLOCKED or NOT EXECUTED row exists. Scoring dimensions (functional correctness, member sensitivity, guard order, end-to-end refusal, independent isolation, contract coverage) are separated in `contract-coverage.md`; a joint refusal does not demonstrate isolation.

## Repeatability
run1 and run2 are two processes on the same host about 6 s apart: repeatability, not replication. The (case, check, kind) sequence and all results are identical. 13 evidence rows differ in value fields; all are run-minted decision UUIDs and claim commitments binding them (5 of the 13 are gating CHECK_PASS rows whose `expected` is a freshly minted UUID). All PASS in both runs.

## Provenance (actual relationships)
Protocol, instruments, case designs, execution and this package were produced by a single AI session lineage (Claude, subagents of one session; lead plus case workers A-D). Review `review/review-E-same-lineage-adversarial.md` was produced by a subordinate worker of the same session, same model family: **same-lineage, not independent**. No human reviewer, no organizationally independent party and no external competence reviewer took part. Multiple AI agents do not constitute organizational independence. Expected results are source-derived and fixtures are shared with D-1, so a PASS confirms the source reading, not an independent oracle.

## Layout
`PROTOCOL.md` (frozen; sha256 in `protocol.sha256`; freeze time `protocol.freeze.txt`), `harness/` (instruments, hashes in `source-identity.json`), `spec/` (case specs, also reproduced in the protocol), `raw/pre|run1|run2` (preflight, evidence JSONL, junit, stdout/stderr, retained pytest basetemp stores incl. `.lock` files), `review/`, `case-results.json`, `expected-vs-observed.md` (generated from run1 rows; 378 rows), `contract-coverage.md`, `limitations.md`, `environment.json`, `source-identity.json`, `manifest.json`, `SHA256SUMS`.

## Reproduce
1. Obtain CP `739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69` pristine (`git archive`), content hash must equal `d468827e...0721e11` (command in `source-identity.json`); Registry pin `a40fe755e2384a99c37016fa9ad59396f1835900` detached and clean.
2. Python 3.11.18 venv with the packages in `environment.json`.
3. `harness/run_bq.sh <label> <cp-root> <reg-pin-dir> <python> <outdir>` (harness files must be unmodified; compare to hashes in `source-identity.json`).
Not reproducible from committed files alone: the CP and Registry checkouts and the venv are not committed; `run_bq.sh` and the evidence rows reference scratch paths under `/tmp/claude-0/work/`; run-minted UUIDs differ per run; the stores under `raw/*/basetemp-parent` were retained here (the D-1 convention did not retain them).

## Verify
`sha256sum -c SHA256SUMS` from this directory (SHA256SUMS is written last and excludes itself).
