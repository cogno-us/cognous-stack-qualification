# 07 Estimated engineering effort avoided

**Status: documentation-only analysis. Non-authorizing. Draft for Architect review. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.**

Nothing here authorizes a migration, approves a pin, selects or activates a record, or changes a qualification verdict. Implementation is not authorized.

**Every figure in this section is a REASONED INFERENCE, not a measurement.** The Constitution (CA08, CA13) says code volume, commit intervals and worker counts are not substitutes for measured effort, and active hours are unknown unless measured. Line counts below are the only measured quantity (`wc -l`, at the pinned heads). The conversion to engineer-days is an assumption and could be wrong by a wide margin.

## 1. Method and assumptions

- Measure the existing assets a duplicate system would have to re-create, by line count.
- Convert at an assumed rate for design, implementation, review and test: **100 to 150 lines per engineer-day**, by one experienced engineer, including review rounds (E1 and E2 are line-derived this way; E5 adds an allowance for the uncounted scripts). E3 and E4 are judgement estimates for convention and reporting design, not line-derived. The ranges are deliberately wide.
- Count only work that a *duplicate* system would need. Work needed either way (the independent author's expectations for the 114 active new-test items, oracle review, execution, evidence review) is excluded from both sides and is not estimated here.
- No credit is taken for ISSBench reuse. Doc 02 finds nothing to port, so any ISSBench-derived item below is avoided *duplication*, not saved reuse.

## 2. What would otherwise be re-created

| # | Duplicate that is not needed | Existing asset (measured) | Lines | Estimate (engineer-days) |
|---|---|---|---|---|
| E1 | Registry-specific collector, pin and freeze handling, suite overlay, immutable evidence writer, trajectory record, failure register, refusal template | `tools/v1_validation.py` 1,378; `suites/_pins.py` 249; `tools/qualification_results.py` 159; `tools/install_suite.py` 127; `tools/trajectory_contract.py` 166; `tools/capture_workflow_run.py` 65; `tools/failure_register.py` 101; `suites/_refusal_template.py` 330 | 2,575 | 17 to 26 |
| E2 | Route B atomic, policy-refusal, adversarial-flow and verdict test harness for the new cases | `test_scn_c11.py` 495 (harness part); `_oi_flow.py` 209; `mvp-chain/_chain.py` 819 and `verdict.py` 101; `_adv.py` 176; atomic fixtures in `test_local_authority_effect.py` (959, harness part) | about 1,500 to 2,000 reusable | 10 to 20 |
| E3 | Workflow conventions: exact-revision inputs, pins, locks, identity artifact, hashed installs, SHA-pinned actions | `operation-identity-profile.yml` 86 lines as the template; conventions across 70 workflows | 86 template | 2 to 4 |
| E4 | Reporting and dashboard for registry results | `tools/build_dashboard.py` 191; schemas | about 200 | 2 to 4 |
| E5 | An ISSBench-style harness built for OCS: evidence log, comparator, provenance checker, freeze verification, attempt scripts | `issbench/*.py` 1,433; 104 files in `scripts/` (not counted) | 1,433+ | 10 to 20 |
| | **Total avoided (sum of ranges)** | | | **41 to 74** |

Rounded: **about 41 to 74 engineer-days**. UNVERIFIED against any actual schedule.

## 3. Proposed new work, for comparison

| PR (doc 08) | Builder-side estimate (engineer-days) | Basis |
|---|---|---|
| QPR-1 gate-binding table and validator | 2 to 3 | one data file, about 100 lines, one test, one doc |
| QPR-2 registry-subject profile workflow | 1 to 2 | one workflow copying a pattern of 86 lines, plus pin checks |
| QPR-3 suite directory `conftest.py` and import map | 2 to 4 | about 50 to 120 lines plus import checks across five helper modules |
| QPR-4 allowlist and capture option (optional, expected not built) | 0 to 0.5 | two small edits |
| **Total** | **about 5 to 9.5** | |

Ratio: roughly 4 to 15 times less than the duplicate path (41 against 9.5 at the closest, 74 against 5 at the widest), with the wide error bars above. The comparison is only meaningful if the assumptions in section 1 hold. **REASONED INFERENCE**

## 4. What these numbers leave out

- **Independent oracle authoring** for the 114 active new-test items. This is required on any path, depends on the registry consumer, selection destination and claim-carried binding existing, and cannot be sized from here.
- **Review time.** Tier 1 changes call for focused independent review (Constitution tier table). No independent reviewer is available at present.
- **Environment cost.** Many suites hard-fail without checkout variables; reproducing the exact-pin environment (Python 3.13, pydantic 2.12 or later, `agent_control_plane` on the path) is real setup work not included in E1 to E5.
- **Remediation rounds.** The plan budgets three; each changes the candidate pin and re-runs the affected gates in full.
- **Risk of the reuse path.** Reusing suites that are designed to fail on specific pins, that were last run at older heads, or whose CI skips tests when a dependency is absent can hide a problem. The saving is not free of review cost.

## 5. Not claimed

No saving is claimed in calendar time, in time to an independently accepted outcome, or in risk. No independent qualification is implied. Release, publication and production stay on HOLD.
