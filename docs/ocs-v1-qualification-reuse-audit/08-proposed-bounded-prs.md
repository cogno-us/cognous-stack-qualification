# 08 Proposed bounded implementation PRs

**Status: documentation-only analysis. Non-authorizing. Draft for Architect review. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.**

Nothing here authorizes a migration, approves a pin, selects or activates a record, or changes a qualification verdict. **These PRs are proposals only. None is started, authorized or implied, and none is to be started from this document.** The Architect issues any implementation authorization separately. Per the standing rulings: no auto-merge, exact-head verification, green checks, and bounded merge authority on each.

## 1. How these fit the existing plan

The merged P1 plan already has qualification-repository cards `EXT-S5-1` to `EXT-S5-6`. The proposals below are not new sprints. They are the infrastructure those cards will need, cut as small as the reuse in [03](03-reuse-and-duplication-matrix.md) allows, with the constraint that each reuses rather than re-creates. The independent oracle author's test content (the 114 active items) belongs to `EXT-S5-2` to `EXT-S5-5` and is **not** a PR proposed here.

Every PR below shares these properties (the plan's "Std-Q"): qualification repository only; no implementation repository touched; no existing suite, known-limit test, expectation, fixture, workflow or result edited or moved; no status invented; no qualification or independent-verdict claim; rollback is a revert.

## 2. Proposed PRs

### QPR-1 Gate-binding table and validator (supports EXT-S5-1)

| Item | Detail |
|---|---|
| Purpose | Make `QG-01..QG-14` representable here, with QG-02 inactive, so "no new status" and "no gate counted as PASS by analogy" are checkable |
| Files (new only) | `process/registry-v1/gate-bindings.proposed.v1.json`; one validator module; one unit test; one short doc |
| Reuses | Requirement-row model of `requirements.json`; `validate_requirements` if usable standalone; the existing closed status sets; the pre-registration and `*.proposed.vN.json` conventions |
| Does not touch | `requirements.json`, `freeze-manifest.json`, `v1_validation.py`, `mvp_acceptance_gate.py`, release-gate files, any result |
| Checks that run | `catalog-validation`, `qualification-dashboard` (every PR); migration integrity only if a path under `suites/` or `tools/` named in its filter changes |
| Acceptance | 14 rows matching the plan digest; QG-02 inactive and excluded from every total; a test fails on any status outside the closed sets or any "qualified" word without a designation record |
| Risk | Low. First task is to settle whether `validate_requirements` runs without the V1 freeze (UNVERIFIED); if not, reimplement only the row checks |
| Estimate | 2 to 3 engineer-days |
| Blocked on | Nothing |

### QPR-2 Registry-subject profile workflow (supports EXT-S5-2, the plan's `p1-config-extraction`)

| Item | Detail |
|---|---|
| Purpose | One workflow that checks out Control Plane, Runtime and registry at input revisions, assembles the suite, and runs every active gate's tests |
| Files (new only) | One workflow under `.github/workflows/`, not matching `*--*.yml` |
| Reuses | `operation-identity-profile.yml` as the template; `install_suite.py` for the identity artifact; `.github/locks/*-a9a750.txt` for Python 3.13 and pydantic 2.13.5 |
| Does not touch | Any existing workflow or lock |
| Acceptance | Pins are inputs; every checked-out git identity is recorded; hashed installs only; SHA-pinned actions; `persist-credentials: false`; passes the existing workflow structure and dependency tests |
| Risk | Medium. Depends on the Architect's reading of the cross-repository rule ([06](06-ownership-and-integration.md) section 3) and on how the host driver reaches the registry without importing it (UNVERIFIED) |
| Estimate | 1 to 2 engineer-days |
| Blocked on | Architect confirmation of Reading A; registry CI (`EXT-S1-0`) for a stable checkout target |

### QPR-3 Suite directory skeleton and import map (supports EXT-S5-2 to EXT-S5-5; build only if the oracle author needs it)

| Item | Detail |
|---|---|
| Purpose | A place for the independent author's tests, with unavailable prerequisites failing as typed hard failures rather than silent skips |
| Files (new only) | `suites/ocs-registry-v1/conftest.py`; an import map to the helpers in doc 05 section 4 |
| Reuses | `_oi_flow.py`, `_adv.py`, `mvp-chain/verdict.py`, `_refusal_template.py`, the C11 helpers, the atomic fixtures, by import |
| Does not touch | Any existing suite; no helper copied |
| Acceptance | No test case is included; the import map resolves; a missing prerequisite surfaces as the existing computed result (INCONCLUSIVE or NOT RUN), never PASS or a new status |
| Risk | Low to medium. Tier 1 review applies once cases arrive |
| Estimate | 2 to 4 engineer-days |
| Blocked on | QPR-1; and the existence of the components under test for any case to run |

### QPR-4 Capture allowlist and workflow option (optional; expected NOT built)

| Item | Detail |
|---|---|
| Purpose | Only if runs of workflows that live in the registry repository must be recorded as workflow telemetry |
| Files | `tools/qualification_results.py` (`REPOSITORIES`) and the capture workflow's `options`; the allowlist is tested by `tests/test_qualification_dashboard.py` |
| Why probably unnecessary | If the registry-subject workflow lives here (QPR-2), runs are already of an allowlisted repository |
| Estimate | 0 to 0.5 engineer-day |
| Blocked on | A decision that registry-repo workflow runs should be captured |

## 3. Explicitly not proposed

| Not proposed | Why |
|---|---|
| Any ISSBench-derived harness, schema, status or script | Doc 02; the ISSBench documents themselves disclaim OCS infrastructure |
| Consolidation of the five status vocabularies, the byte-identical `_index_signing.py` pair, the canonical-JSON or digest helpers, the typed-refusal and tests workflow families, the vendored trees | Not V1 needs; they touch existing tests; digest flags differ |
| A new evidence record kind, status, collector, mutation harness or dashboard change | Doc 05 section 5 |
| New catalogue rows or any change to the 696-row inventory | Preserved |
| Declaring the 11 Runtime known-limit tests | Owner action, GAP-G4-07 |
| Designating an independent lead | Operator or Architect decision, GAP-G4-13 |
| Editing README, `docs/README.md` or any index | PR #227 added no index entry; precedent followed |
| Branch-protection or required-check changes | `EXT-S2-G` inventories observed names only; none invented |

## 4. Order and stop conditions

1. QPR-1 first, before any implementation result is shown to the oracle author.
2. QPR-2 after the Architect confirms Reading A and the registry has a CI target.
3. QPR-3 only when the oracle author asks for it and the components exist.
4. QPR-4 only on a separate decision.

Stop and return to the Architect if any proposal would need an edit to an existing test, expectation, fixture, workflow, result or lock; a new status; an import from outside this repository; or a change to a Control Plane enforcement file or Runtime `engine/safe_executor.py`.
