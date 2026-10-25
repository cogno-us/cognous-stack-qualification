# 05 Minimum necessary new test infrastructure

**Status: documentation-only analysis. Non-authorizing. Draft for Architect review. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.**

Nothing here authorizes a migration, approves a pin, selects or activates a record, or changes a qualification verdict. Implementation is not authorized. This section proposes what would be built, not that it be built now. Under CA02 the test is "smallest complete authorized capability".

## 1. Three new things, one optional

| # | New item | Why nothing existing carries it | Size (estimate) |
|---|---|---|---|
| N1 | **Gate-binding table** and its validator | `QG-nn` is not representable in this repository (gap G-M). Without it, "QG-02 INACTIVE", "no new status" and "no gate counted as PASS by analogy" cannot be checked here | One JSON data file of 14 rows; one validator of roughly 60 to 100 lines; one unit test |
| N2 | **One registry-subject profile workflow** | No workflow checks out `cognous-ocs-registry` or runs a registry-bearing tuple (gap list: nothing automatically gates a registry change) | One workflow, modelled on the 86-line `operation-identity-profile.yml` |
| N3 | **One native suite directory** `suites/ocs-registry-v1/` containing only the independent author's test files, a `conftest.py` and an import map | The cases in doc 04 (G-A to G-L) have nowhere to live | Test content is the independent author's work, not infrastructure; the infrastructure part is the `conftest.py` and import map, roughly 50 to 120 lines |
| N4 (optional) | Allowlist and capture-workflow option for `cognous-ocs-registry` | Only needed if runs of workflows that live **in the registry repository** must be captured as workflow telemetry | Two small edits; expected not needed |

## 2. N1 Gate-binding table

**Shape.** A data file such as `process/registry-v1/gate-bindings.proposed.v1.json`, following the repository convention for versioned proposed oracles (`*.proposed.vN.json`; corrections are a new version). It carries, per gate: `gate_id`, `active` (false only for QG-02), the plan source pin (registry commit and the sha-256 of the plan's gate matrix), and requirement-style rows using the existing row model from `requirements.json`: `kind`, `selectors` (`component`, `re`, `min`), `mandatory`, `adequacy`. **No result status is stored.** Status is computed the way `evaluate_requirements` already computes it, so PASS needs adequate executed evidence and an absent or short selector gives INCONCLUSIVE. **REASONED INFERENCE**

**Validator.** A function that (a) rejects any status string outside the existing closed sets, (b) requires exactly 14 gate ids, matching the pinned plan digest, (c) requires QG-02 to be inactive and never counted in any total, (d) refuses a row that cites a qualification claim without a designation record (the plan's EXT-S5-1 asks for this test), and (e) refuses a "qualified" or independent-verdict word. It can call `validate_requirements(doc)` (`tools/v1_validation.py:833`), which takes a plain document and is a pure function. Whether it works without the V1 freeze manifest for component names is **UNVERIFIED**; the first PR must settle that, and if it does not, the validator reimplements only the row checks rather than touching `v1_validation.py`.

**Why not the existing homes.** `requirements.json` is bound to the V1 freeze (`freeze-manifest.json` is never edited, so adding rows there would mean a new validation id); `mvp_acceptance_gate.py` gates an MVP tuple with different verdict words; the release gate OCS-1/2/3 is a different object. A separate file that borrows the row *shape* touches none of them. **REASONED INFERENCE**

## 3. N2 Registry-subject profile workflow

Model it on `operation-identity-profile.yml` and `outside-holder-profile.yml`: `workflow_call` plus `workflow_dispatch`, exact-revision inputs (`control_plane_revision`, `runtime_revision`, `registry_revision`, `qualification_revision`), a Python matrix, `persist-credentials: false`, SHA-pinned actions, `--require-hashes` dependency installs from `.github/locks`, and a `relocation-*`-style identity artifact that records every git identity checked out. This is the "new `p1-config-extraction` workflow" the P1 plan already expects (EXT-S5-2); the audit's contribution is that it should be an instance of an existing pattern, not a new design, and that **one** workflow can serve every active gate rather than one per gate. **REASONED INFERENCE**

Constraints it must meet, all from the existing repository:

- The plan's host driver imports no registry-host code; tests drive the registry through its own interface. How is not specified in the plan. **UNVERIFIED**
- Pins are inputs. Defaults, if any, follow the existing literal-pin convention, which `tests/test_e4_workflow_pin_literals.py` and `test_f_t3_1_workflow_pin_structure.py` check for V1 validation only; whether they extend to a new workflow is **UNVERIFIED**.
- Python and pydantic: the mvp suites need Python 3.13 with pydantic 2.12 or later (lock `a9a750`: 2.13.5). Choosing the 2.11.9 locks would break them.
- `tests/test_privileged_workflow_dependencies.py` requires every requirement to be hashed.
- A new file under `.github/workflows` that does not match `*--*.yml` does not trigger migration integrity.

## 4. N3 Suite directory and shared helpers

Native suites (for example `mvp-chain`, `operation-identity`, `v1-scenarios`) already live under `suites/` without entries in the migration manifest. `tools/validate_migrations.py` only walks manifest rows, so a new native directory does not trip it; it will trigger the migration-integrity workflow on the pull request, which runs the catalog validator and the unit tests. **SOURCE FACT**

**Reuse by import, not copy.** `process/adversarial/tests/_adv.py` already imports `suites/operation-identity/_oi_flow.py`, which is the precedent for a test directory building on another directory's helpers. The new directory should import, by path:

| Need | Existing helper |
|---|---|
| Policy-refusal oracle for each allowlist, Routes A and B | `v1-scenarios/test_scn_c11.py` (`POLICY_DIMS`, `stricter`, flow helpers); `v1-probes/test_runtime_probes.py::op_and_policy` |
| Route B atomic fixtures, clock, barrier | `cognous-execution-runtime/tests/test_local_authority_effect.py` (`MutableClock`, `BarrierDestinationMixin`, `setup_atomic`) |
| Flow, effect ids, observe/require | `operation-identity/_oi_flow.py`, `process/adversarial/tests/_adv.py`, `conftest.py` |
| Verdict computation | `suites/mvp-chain/verdict.py` (pure function) |
| Refusal, positive control, mutation, provenance legs | `suites/_refusal_template.py` |
| Freshness fixtures | `FreshnessAdapter` in `operation-identity/test_freshness_profile.py`; the E3 pattern |

Copying any of these would be new duplication (see Q29 for the existing example, `_index_signing.py`). **REASONED INFERENCE**

**Unavailable is BLOCKED, not skip.** The Constitution says a required check that is missing, disabled, unsupported or unavailable cannot become PASS or non-applicability, and that an unresolved mapping is BLOCKED or NOT ASSESSED. Existing suites already mix hard-fail and skip on unset environment (a hard-failing and a skipping copy of the same refusal test both exist). The new `conftest.py` should choose hard-fail with a typed reason for every missing prerequisite so that nothing reads as a silent pass. It must not map to a new status: the existing computed result is INCONCLUSIVE or NOT RUN. **REASONED INFERENCE**

## 5. What is deliberately not built

| Not built | Reason |
|---|---|
| A new evidence record kind or schema | `run-manifest-v1` and `trajectory-evidence-v2` already carry what a run needs; v1 forces results into the existing verdict set and refuses any other |
| A new status, verdict or claim label | Closed sets only (Q02) |
| A new collector, freeze mechanism, immutable writer or aggregate | `suites/_pins.py`, `write_immutable`, `v1_validation.py`, `install_suite.py` exist |
| A fixture library | The fixtures in section 4 exist; the missing content is cases |
| A copy of any ISSBench mechanism | Doc 02. Nothing there is both generic and absent here |
| A cross-repository shared package for hashing or canonical JSON | Would create a dependency and could change digests (Q29, I13) |
| Dashboard changes | Not needed to qualify V1; `OUTCOMES_RUN` is hard-wired to one run and can be left alone |
| A scenario catalogue entry | The 696-row inventory is preserved; new cases are tests mapped to gates, not new catalogue rows (a new row would also require a coverage-map entry and a dashboard count change) |
| A new mutation harness | Q12 leg (d) is the per-refusal-family mutation leg; Q17 stays separate |

## 6. Tier

Per the Constitution's risk tiers, this audit PR is documentation (Tier 3). The *later* suites exercise authority, atomic state, trust and negative-evidence custody, and independent acceptance logic, which are **Tier 1** and call for focused independent review. Copilot review is technical review, not qualification, and is not evidence review. **SOURCE FACT** (Constitution tier table; P1 plan doc 07)
