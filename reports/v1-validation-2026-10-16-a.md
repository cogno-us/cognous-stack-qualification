# V1 validation report — v1-2026-10-16-a

**Selected-V1 verdict: FAIL.** Two mandatory docx acceptance items fail (both in The Index). Independently of those, 45 of 75 mandatory requirements remain unresolved (13 INCONCLUSIVE, 32 NOT RUN), so the verdict would be INCOMPLETE even if the Index were repaired. This is not a release decision: no release, tag, announcement or message was made, and production remains NOT ESTABLISHED.

Authoritative run: [Actions 38962759690](https://github.com/cogno-us/cognous-stack-qualification/actions/runs/38962759690). Retained evidence: [`results/v1-validation/v1-2026-10-16-a/final-38962759690/`](../results/v1-validation/v1-2026-10-16-a/final-38962759690/) (summary, [requirements matrix](../results/v1-validation/v1-2026-10-16-a/final-38962759690/requirements-matrix.md), every job's JUnit and result). Earlier runs (baseline, fix2, matrix1) are retained unaltered beside it, with their harness defects.

## Subject

Frozen by [freeze-manifest.json](../process/v1-validation/v1-2026-10-16-a/freeze-manifest.json) before execution: hub `8517818f`, qualification closeout `af9f5843`, runtime `e20f92e1`. The subject is the owner-approved F5b-repaired seven-component bounded synthetic reference plus the remaining lock components (BitRep, The Index, constitutional authority). It is **nonselected** in the hub: `component-lock.json` still selects the W7 generation. No pins, profiles, defaults or product code changed.

## Result counts

| | PASS | FAIL | INCONCLUSIVE | NOT RUN | NOT APPLICABLE |
|---|---|---|---|---|---|
| All 92 requirements | 31 | 2 | 13 | 42 | 4 |
| Mandatory (75) | 28 | 2 | 13 | 32 | 0 |
| Jobs (48 incl. controls) | 43 | 3 | 0 | 2 | 0 |

PASS means that adequate, executed evidence matched the requirement and none of it failed or was skipped. Selectors judged only partly adequate yield INCONCLUSIVE with the reason stated.

## Failures

| Item | Finding | Class | Issue |
|---|---|---|---|
| ER-02-2 | The Index stores a link whose `attested_by` is unverifiable (forged attestation accepted). Detector calibrated against accept-all/reject-all stubs. | missing capability | [registry #23](https://github.com/cogno-us/cognous-evidence-registry/issues/23) |
| ER-02-4b | Five copies of one source give `independence_score` 1.0. | product defect | [registry #24](https://github.com/cogno-us/cognous-evidence-registry/issues/24) |
| Platform jobs | Control plane fails closed on macOS (188/320), errors on Windows; 3 runtime cases fail on Windows. | profile/compatibility (unsupported; undocumented) | [hub #157](https://github.com/cogno-us/cognous-open-control-stack/issues/157) |

The hub scopes Index attestation as an optional evidence path; the docx acceptance was applied as written, and the matrix records that scope note.

## Verification of PR #29 reference results

| Claim | Outcome | Provenance |
|---|---|---|
| 20/20 matched refund trials | **Verified.** Re-executed from pinned runtime and control-plane sources; 20 PASS, all per-trial verdicts, balances, versions and effect counts identical to the retained reference. The supplied external fixture is not republished, so the runner input was rebuilt from the retained common stimulus. | NEW EXECUTION |
| 114 qualification tooling tests | **Verified** (114 pass, 0 fail). | NEW EXECUTION |
| 40 native runtime regressions | **Not re-executed.** The retained `matched-atomic-regression-final.xml` records 40/0/0, but the overlay assembly was not reproduced. This run executed the runtime's own 174-case suite and the 36-case native F5b suite instead, all passing on Linux. | REUSED, unverified |

## Not established

- **Scenario catalog:** D01, D03 and D04 have named synthetic assertions only (not whole-catalog acceptance). The other 37 are NOT RUN; coverage mappings are PARTIAL/UNIMPLEMENTED/DEFERRED. The eight agent/human scenarios need paid agent runs or human participation, which the freeze manifest excludes; no budget was spent.
- **No adequate test or check:** schema migration notes (ER-04-4), ODES extension versioning (ER-09-3), provenance scan for proprietary logic (SR-3), conventional-control baseline measurement and latency/review burden (SR-2, C22/C23), fleet coordination (out of V1 scope per docx dependency).
- **PRP and TFA** have no tests at their pins (optional components).
- **Source gap:** the Drive addenda folder could not be read (Google sign-in required). The matrix covers only the attached recommendations document and the repository matrices.
- **Platforms:** results for Windows and macOS are retained but not claimed; V1's supported platform is Linux.
- Evelyne-Claudia's material was treated as read-only and not reconciled.

## Method

GitHub Actions controller (`.github/workflows/v1-validation.yml`): 43 component jobs (`fail-fast: false`, 5-minute shard timeout, at most one retry), native F5b suite twice with fresh stores, hub and tooling tests, Index probes, matched-refund re-execution, then an aggregator that refuses to promote missing, failed, skipped or undeclared coverage. Cost: no paid calls.
