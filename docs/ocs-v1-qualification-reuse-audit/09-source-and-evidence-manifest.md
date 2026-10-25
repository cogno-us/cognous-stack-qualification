# 09 Source and evidence manifest

**Status: documentation-only analysis. Non-authorizing. Draft for Architect review. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.**

Nothing here authorizes a migration, approves a pin, selects or activates a record, or changes a qualification verdict. Implementation is not authorized. Labels as in [01](01-existing-ocs-capabilities.md). This is **builder-side inspection**: it is not independent qualification, evidence review or certification, and Tier 1 is NOT QUALIFIED.

## 1. Pins

| Repository | Revision | Note |
|---|---|---|
| `cogno-us/cognous-stack-qualification` (primary, read and write) | `be1994a961e4e40612d999972ede6547a3729887` | `main`, the PR #227 merge; the clone is a single squashed commit |
| `cogno-us/cognous-issbench-v2` (read-only reference) | `5e05ecf71894731d2816ecabc764d8962652b5b9` | shallow clone of default branch; nothing written to it |
| `cogno-us/cognous-ocs-registry` (read-only, plan only) | `d2c472e4a09543228bad62235e07a0dedfd7f48b` | `main`, the PR #22 merge (final head `b34fa6613f225f944ca839d521a4f8a972b89cec`); read only `docs/p1-extraction-plan/`; the registry source tree was not audited |
| `data/qualification-gate-matrix.json` in the registry plan | sha-256 `e81b5fad1dfcc9bcb002111a17e7bd79117efa53cfc81b3198fbcb75b2dd04bd` | the source of the 14 gate rows in `data/gate-coverage.*` |
| `cogno-us/cognous-engineering-constitution` | `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` | read at this revision (`ENGINEERING_CONSTITUTION.md`, `ADOPTION.md`). A different revision, `6f7f2731`, is called provisional guidance in the project status record. Whether either is formally adopted for this program is **UNVERIFIED**; `ADOPTION.md` says publication and possession do not establish adoption |
| Control Plane / Runtime candidate | `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` / `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f` | named by the plan and the prior assessment; **not cloned or read here**. All statements about their code come from this repository's tests and docs |
| Historical controller pins | Control Plane `0a41faa9`, Runtime `ec728da6` (g8-r10) | what `PASS_RECORDED` refers to; historical evidence does not speak for the current heads |

## 2. How this was produced

Eleven read-only reviewers (Claude workers) each took a disjoint slice: the inventory and gates; workflows and locks; evidence, custody and reporting; OCS suites against the allowlist, freshness, Route B and identity items; OCS suites against selection, revocation, rollback and negative evidence; the ISSBench runtime package; ISSBench fixtures and results; ISSBench workflows, scripts and cross-repository references; cross-repository duplication; documentation conventions and governing references; and the ISSBench registry-related documents. They were instructed not to modify either repository. The lead then re-checked the claims this package leans on most, against the files:

| Re-checked directly | Result |
|---|---|
| `REPOSITORIES` allowlist excludes `cognous-ocs-registry` | Confirmed (`tools/qualification_results.py:14-20`) |
| No `issbench` or `cognous-ocs-registry` reference in workflows, tools, tests or suites | Confirmed by `grep` (results excluded) |
| `QG-[0-9]` appears nowhere in this repository | Confirmed |
| `approval_max_age_seconds` occurrences | One: `process/adversarial/tests/test_t15_profile_forwarding.py:52`, a forwarding check. One reviewer had reported zero in `suites/`; that is true of `suites/` and incomplete overall, and is corrected in doc 01 |
| `suites/v1-probes/_index_signing.py` equals `suites/v1-scenarios/_index_signing.py` | Byte-identical (same sha-256) |
| 696-row crosswalk status counts | NO_TEST 602, NOT_RUN 67, PASS_RECORDED 23, KNOWN_LIMIT_ASSERTED 4; 162 suite-local rows |
| `POLICY_DIMS` in `test_scn_c11.py` | Seven dimensions, including the five in scope |
| Native suites absent from the migration manifest | `suites/mvp-chain`, `operation-identity`, `v1-scenarios`, `outside-holder` have no `migrations/` entry |
| Gate catalogue | Read directly from the plan's matrix: 14 rows, QG-02 `INACTIVE_MAX_AMOUNT_DEFERRED`, all `qualified: false` |

The reviewers' other findings (for example the per-workflow family counts, the ISSBench property taxonomy, the canonical-JSON variant differences, the T07 to T10 characterization) are as reported by them and were not re-derived line by line. They are labelled SOURCE FACT where the reviewer cited a file and line, and the lead did not find a contradiction.

## 3. Not read, not run, not available

- **No qualification suite, workflow or ISSBench script or test was executed.** All qualification pass or fail status is as recorded in the repository; several suites hard-fail without checkout variables, so a run here would not have been informative. The only things run were this repository's own checks on the final tree, once: `tools/validate_catalog.py` (valid), `tools/validate_migrations.py` (valid) and `python3 -m unittest discover -s tests` (780 tests, OK, 3 skipped, Python 3.13). That is a repository self-check, not qualification evidence.
- Control Plane, Runtime and registry source trees were not read. Enforcement lines for Exchange, Replay, Evidence Pack, ODES, Verifier, BitRep, Index and Action Manifest were not available; scenarios whose enforcement lives there carry no extraction row in the prior assessment.
- Not read in depth: `process/mvp-acceptance` internals, `suites/mvp-applicability`, `suites/verifier-mutation` internals, `governance-evidence-pack/tests`, `test_gax_imx_redelivery.py`, the `comparators/runner/cells.py` vocabulary, `test_paired_request_enforcement.py` policy usage, and the 131 requirement rows individually.
- GitHub branch protection, required status checks and rulesets for either repository (no CODEOWNERS, PR template, CONTRIBUTING, CLAUDE.md or AGENTS.md exists here).
- Whether `validate_requirements` runs without the V1 freeze for component names; how the planned host driver reaches the registry without importing it; whether the workflow pin-literal tests extend to a new workflow.
- Whether `SHA256SUMS*` files outside `results/workflows` are checked by any job.
- Whether the repository's unit-test suite passes at `be1994a9`. The clone is single-commit, so history and pin diffs are not available; the three PR #227 commit messages were read through the REST API only.

## 4. Corrections and stale statements found, not edited

Listed in [01](01-existing-ocs-capabilities.md) section 6 and not repeated: suite-directory count, wiki-derived test count 290 versus 281, the README quick start's "Ran 413 tests" versus 780 observed here, `catalog.json` all-NOT RUN versus the crosswalk's INCONCLUSIVE rows, and the overloaded word "gate". Additionally, the plan's prose says QG derives from "the existing 13-gate acceptance matrix", whereas the brief for this audit calls the gates "existing fourteen"; both are consistent once it is clear the 14 are defined in the plan (13 proposed-not-adopted V1-M/R/C gates became 14 QG gates).

## 5. Status of the underlying facts this package relies on

- 696 canonical scenarios: preserved, none re-scored; 65 in scope; no scenario makes registry-managed configuration REQUIRED (prior assessment, REASONED INFERENCE).
- Nothing is qualified. No scenario-level PASS exists; nothing is recorded at the current heads; controller g8-r10 gives 0 PASS, 27 INCONCLUSIVE, 13 NOT RUN on the 40 catalog rows and all 656 Wiki cases NOT RUN.
- The registry has no consumer path: `apply_registry_overlay` has no caller; the local policy check runs outside the atomic transaction; selection is unauthenticated (R09). These are the prior assessment's findings and the plan's gaps (GAP-G3-01, G3-02, G3-07), not re-established here.
- Independent Tier 1 qualification lead: none designated (GAP-G4-13). Trust root and key ceremony are operator-gated. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.

## 6. Provenance of the sandbox paths

Absolute paths such as `/home/claude/...` that appear in the plan's `existing_test_ids` for registry builder tests are sandbox paths from the plan's authoring session, not repository paths. In `data/gate-coverage.*` a reference is counted as registry-builder when its string contains `cognous-ocs-registry`.
