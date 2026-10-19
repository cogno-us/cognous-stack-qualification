# Release test inventory

This page lists every test suite that belongs to the Open Control Stack (OCS) release test gate: what it tests, how to run it, how many cases it holds, which components and routes it touches, what environment it needs, what state it was last seen in, and which known limits it carries. The machine-readable twin is [`process/release-gate/inventory.json`](../process/release-gate/inventory.json); a consistency test (`tests/test_release_gate_inventory.py`) checks that the two agree and that the paths and Wiki counts are real.

**Status of this page.** It is an inventory, not a result. No gate has been run. The qualification controller (`tools/v1_validation.py`) has not been run for it, nothing here is a verdict, and every AI Security Wiki case remains NOT RUN until the controller runs. Counts for the component suites were measured by a read-only inventory run on 18 and 19 October 2026 (Python 3.12, Linux, a shared two-core machine, so wall times are not stated). Where a count was measured at this repository's main (`e6b20bd504c4a6aadfc3b142ab0c7b632dbd3c46`) the table says "collected at main". Where a number is not measured, estimated, or defined only by a workflow run, the table says so and the JSON carries `null`.

**Scope.** Bounded synthetic profile only. The comparator applications (the OPA application and the LangGraph plus OPA application) are configured by Cognous, not vendor implementations. This is not independent certification and not production readiness; operational trust stays on HOLD. Linux only.

## 1. Publication criteria

The release test gate, as agreed on 18 October 2026:

1. OCS passes 100% of the applicable suites in each of the three categories below: individual-component synthetic tests (gate OCS-1), cross-component synthetic tests (OCS-2) and AI Security Wiki derived tests (OCS-3, split into individual-component W-I and cross-component W-X).
2. No unexplained skip and no unexplained xfail. A skip is allowed only if the inventory lists it with a reason and the environment it needs; a skip that is not listed fails the gate.
3. Known-limit tests are listed separately from ordinary passes.
4. A failing applicable test blocks publication until it is resolved or reclassified. Reclassification (known limit, not applicable, or a test that lags its component) and its reason are recorded before the next run that could show the result, never after the result is seen. No test is dropped, renamed or loosened after it failed.
5. Applicability is decided from the declared scope, never from results. A case that is not applicable is listed with its reason and is outside the denominator; a case that is applicable stays in the denominator even if it fails.
6. Comparators run only on three declared sets: the 19 corner scenarios, the 24 baseline scenarios, and a Wiki subset registered case by case before any run. Scoring is identical for every configuration and every result is reported as observed, including any case where a comparator passes and OCS does not. A comparative statement is limited to sets where both configurations were actually run. The comparison is a separate observation and never replaces the OCS gate.

The result table of a gate run has three columns for every suite: PASSING, PASSING-AS-KNOWN-LIMIT, and SKIPPED-WITH-REASON.

### What "known limit" means

A known limit is a stated boundary of the stack: something it does not check, record, or guarantee, and which the documentation says so. A known-limit test passes by showing the limit as it is (the negative fact is the assertion), not by showing that the limit does not exist. It is therefore not a weakened test and not a skip. Each known-limit test carries the name of the limit and is listed apart from ordinary passes in the gate report, with a pointer to the sentence in the guarantees and limits documentation that states it. A strict xfail probe counts as a known limit only if the owner reclassified it before the run, with the reason written down; otherwise a strict xfail that now passes is a failure to be cleaned up, and one that still fails is an unresolved item. Where this page says a suite has known-limit tests, the number is given if it was counted; "present, not enumerated" means the inventory did not count them. A suite marked with no known-limit tests means none was identified by the inventory, not that none exist.

## 2. Overview

| Category | Gate | Suites | Count at the inventory |
|---|---|---|---|
| 1. Synthetic individual-component | OCS-1 | C1-01 to C1-15 (plus overlay rows marked "a") | 10,107 native test cases across the 15 component rows; about 710 further relocated overlay cases run inside component trees and are counted under X-09 |
| 2. Synthetic cross-component | OCS-2 | X-01 to X-17 | about 1,800 directly countable cases (X-01 223, X-02 213, X-05 1,093, X-06 50, X-07 17, X-11 38, X-10 160 live); the workflow-defined suites (X-03, X-04, X-08, X-15, X-17) take their counts from their runs |
| 3. AI Security Wiki derived | OCS-3 | W-I, W-X | 656 upstream cases classified; 65 in scope (20 APPLICABLE and 45 PARTLY_COVERED); 232 tests in `suites/wiki-derived` collected at main |

The gate is not met today. The inventory run found 12 blockers (section 6): environment-gated skips and failures, tests that lag component changes, load-sensitive tests, probe marks that need cleaning up, and a pin graph that is behind main. Probe states in this page are the state after the probe-state work item (T4a, #140) and its follow-ups (#141, governance #55); rows and blockers whose resolution is not complete are marked "being resolved".

Status vocabulary: PASS (ran, all green, in the documented environment), ENV (passes or runs only when a stated environment is configured; it was not configured in the inventory run), FAIL (fails at main), PARTIAL, NOT_RUN_HERE (could not or must not be run by the inventory), NOT_RUN (a Wiki case or suite that has not been run by the controller), PLAN (does not exist yet).

## 3. Category 1: synthetic individual-component suites

Each row is one repository's own tests. Rows marked "a" are the relocated integration suites that the qualification repository installs into the component's checkout (`tools/install_suite.py`); they need pinned producer checkouts and belong gate-wise to Category 2 (see X-09), but run in the component's own working tree. All data is synthetic; no network, model, payment or human reviewer is used.

| ID | Suite | Command | Count | Environment | State | Notes and known limits |
|---|---|---|---:|---|---|---|
| C1-01 | ODES: contracts, validators, recipient and exporter profiles, fixtures, time and number semantics (open-decision-evidence-standard) | `python -m pytest -q tests` | 2,882 (measured native) | needs rfc8785, an accepted Replay revision installed | ENV | 2,874 pass and 8 are conditional (1 needs rfc8785, 7 need an accepted Replay revision). With a plain dev install the 8 skip. With rfc8785 plus the Replay revision named as accepted they pass; with a second accepted Replay revision 4 fail; Replay main is not in the accepted list (B-03). |
| C1-02 | Verifier: independent verification of retained records (cognous-open-control-stack-verifier) | `make check` | 1,519 (measured native) | none | PASS | 1,497 pass and 22 skip. The skips are in-body skips inside parametrized tests with data-dependent reasons; they are explained but not declared as marks (B-07). Coverage 97.2%. |
| C1-03 | Control plane: authorization, freshness, operation identity, journal, record store, runtime authority (cognous-control-plane) | `python -m pytest && python tools/adversarial_mutations.py` | 934 (measured native) | none | PASS | 933 pass and 1 skip (real third-party SDK test; the SDK is installed only by one workflow, B-02). Mutation controls: 3 of 3 detected. Known-limit tests: 11. |
| C1-03a | Control plane: Microsoft AGT adapter tests (cognous-control-plane) | `python -m pytest -q tests/test_microsoft_agt.py` | 14 (measured native) | needs pytest-asyncio | ENV | 13 pass and 1 skip with the dev extra installed. Without pytest-asyncio 14 fail with an environment error. Counts in the gate; the gate environment must check that the plugin is importable (B-02). |
| C1-04 | Runtime: engine, atomic route, operation identity, recovery resolution, producer contract (cognous-execution-runtime) | `python -m pytest -q tests` | 487 (measured native) | none | PASS | 486 passed and 1 failed once under heavy machine load (a 30 s subprocess limit); it passes alone (B-09). |
| C1-04a | Runtime plus relocated overlay suites (cognous-execution-runtime) | `python -m pytest -q tests (after tools/install_suite.py overlay)` | 786 (measured overlay) | `MOLTBOT_SAFE_CONTROL_PLANE_ROOT`, `MOLTBOT_SAFE_MANIFEST_FIXTURE`; needs pinned control plane checkout | ENV | Unconfigured measurement: 739 pass, 46 skip, 1 fail. 44 skips need a pinned control plane checkout and a manifest fixture; 2 need a live gateway. With control plane main as the pinned checkout 11 helper tests fail and 1 overlay test fails because the tests lag the component (B-04). |
| C1-05 | Replay bundle: reconstruction, importers, redaction, signing, refusal journal, scan bounds (cognous-replay-bundle) | `python -m pytest -q` | 1,009 (measured native) | none | FAIL | 995 pass, 12 skip (data-driven in-body skips), 1 strict xfail (known limit), 1 fail: the Replay to pack pairing test skips or fails depending on which pack and Replay are installed (B-05). Contains wall-clock assertions (B-09). Known-limit tests: 1. |
| C1-05a | Replay plus relocated overlay suites (cognous-replay-bundle) | `python -m pytest -q (after overlay)` | 1,105 (measured overlay) | needs pinned producer checkouts | ENV | Unconfigured measurement: 996 pass, 107 skip (producer checkouts not configured), 1 xfail, 1 fail (the pairing test of C1-05). Known-limit tests: 1. |
| C1-06 | Governance evidence pack: importer, rendering, producer v2, freshness, Replay pairing (cognous-governance-evidence-pack) | `python -m pytest -q tests && agep check-examples` | 362 (measured native) | needs the Replay revision pinned by the importer | ENV | 362 pass with the Replay revision the importer pins; with Replay main 351 pass and 11 error by design (revision not the pinned one). The pack cannot be gated against Replay main until the pin round (B-03, B-12). |
| C1-06a | Pack plus relocated overlay suites (cognous-governance-evidence-pack) | `pytest --ignore=tests/test_producer_v2.py tests; pytest tests/test_producer_v2.py; qualify_producer_v2.py` | 483 (measured overlay) | `UPSTREAM_MANIFEST_EXAMPLE`, `UPSTREAM_REPLAY_SUCCESS_EXAMPLE`, `UPSTREAM_GAX_ROOT`, `AGEP_PINNED_CONTROL_PLANE_ROOT`, `AGEP_V2_ODES_ROOT` | ENV | Unconfigured measurement: 440 + 43 collected; 366 pass and 74 skip in the first run; the producer v2 file has 1 fail and 42 errors because dependency checkouts are not configured. |
| C1-07 | Governed exchange: generation fence, effect ownership, redelivery, recovery separation (cognous-governed-exchange) | `python -m pytest -q tests` | 234 (measured native) | none | PASS | 234 pass. Thread and fence tests use short fixed waits (B-09). |
| C1-07a | Exchange plus relocated overlay suites (cognous-governed-exchange) | `python -m pytest -q tests (after overlay)` | 312 (measured overlay) | `UPSTREAM_MANIFEST_EXAMPLE`, `UPSTREAM_REPLAY_SUCCESS_EXAMPLE` | ENV | Unconfigured measurement: 239 pass, 3 skip, 70 fail because the upstream example files and producer checkouts are not present. |
| C1-08 | Ergonomics (cognous-ocs): validate, demo, passthrough, runner, lock freshness, packaging (cognous-open-control-stack-ergonomics) | `make check` | 545 (measured native) | none | PASS | 545 pass; coverage 95.7%; all gates ok; wheel builds. |
| C1-09 | Institutional governance: authority context, lineage, tier delay limit, reviewed digest, bootstrap (cognous-institutional-governance) | `python -m unittest discover -s tests -v; python testing/harness/run_authority_lineage.py` | 469 (measured native) | none | PASS | 469 tests (165 subtests) pass. Its CI runs only a subset (B-11). Known-limit tests: 1. |
| C1-10 | Action manifest: schema, models, validator, text validation (cognous-action-manifest) | `python -m pytest; aam check-examples` | 245 (measured native) | none | PASS | 245 tests and 5 examples pass. |
| C1-11 | Evidence attestation: signatures, verification, API, custody profile (cognous-evidence-attestation) | `python -m pytest -q tests` | 95 (measured native) | none | PASS | 95 pass. Its CI runs 1 of the 95 (B-11). |
| C1-12 | Evidence registry: claims, evidence, governance, invariants, link attestation (cognous-evidence-registry) | `python -m pytest -q tests` | 124 (measured native) | none | PASS | 124 pass; deprecation warnings only. Its CI runs a delegated chain qualification instead (B-11). |
| C1-13 | Orchestrator local checks: contract schema, adapters, mappings, matrices, composed sandboxes, documentation links (private repository) | `the 14 unittest discover steps and documentation checks of the local chain script` | 257 (measured native) | none | PASS | 257 (5 + 252) pass with 0 skips when run from a private checkout; the repository is private and not part of the public hub. |
| C1-14 | Qualification repository tooling tests: catalog, migrations, install overlay, pins, dashboard, matched-refund verifier, verifier-mutation harness, wiki import, scope, contract matrix (cognous-stack-qualification) | `python -m pytest -q --ignore=tests/native tests` | 292 (collected at main) | `VERIFIER_CLONE` | PASS | At qualification main e6b20bd: 292 collected, 291 pass and 1 skip (the verifier-mutation harness test that needs VERIFIER_CLONE). The count was 286 in the earlier inventory; the difference comes from tests added by work packages since. tests/native (1 test, NATIVE_HUB_ROOT) is excluded here and runs in the pilot workflows. The inventory consistency test added with this inventory also lives here and raises the count by its own tests. |
| C1-15 | Hub (cognous-open-control-stack) tests: protected destination, ingress, budgets, integrated assurance, federated governance, research assurance, publication inventory, release preflight, negative controls (cognous-open-control-stack) | `python -m pytest -q tests (needs full git history)` | 653 (measured native) | none | PASS | 653 pass with full history (3 tests need commit history). Some multi-process tests use short fixed timeouts (B-09). Known-limit tests: 3. |
| C1-15a | Hub qualification tools (qualify twice at exact source plus mutation controls) (cognous-open-control-stack) | `python tools/destination_admission_qualification.py (and the other qualification and check tools of the hub)` | not counted (tool reported) | none | NOT_RUN_HERE | The tools report their own denominators; not counted by the inventory. The unit-level parts are inside C1-15. |

Category 1 totals as measured: 10,107 test cases across the 15 component rows (the "a" rows are overlays and are not added). The skips among them are the in-body and conditional skips named in B-07 plus 1 control plane SDK skip and 1 qualification skip (`VERIFIER_CLONE`), and there is 1 strict xfail in Replay. The count for C1-14 is as collected at this repository's main before the inventory consistency test was added.

## 4. Category 2: synthetic cross-component suites

These need two or more components (the assembled decision to effect to evidence chain), pinned producers, or both. Paths are in this repository unless the row says otherwise; X-10, X-11 and C1-13 live in a private repository and are not part of the public hub. The probe rows X-01 and X-02 show the state after T4a (#140) and its follow-ups; the decisions that remain are named in each row.

| ID | Suite | Command | Count | Environment | State | Notes and known limits |
|---|---|---|---:|---|---|---|
| X-01 | v1-probes: per-component probes recorded against frozen pins | `PROBE_<X>_DIR=<checkout> python -m pytest -q suites/v1-probes/<module>` | 223 (collected at main) | `PROBE_ACTION_MANIFEST_DIR`, `PROBE_AUTHORITY_DIR`, `PROBE_BITREP_DIR`, `PROBE_CONTROL_PLANE_DIR`, `PROBE_EVIDENCE_PACK_DIR`, `PROBE_INDEX_DIR`, `PROBE_ODES_DIR`, `PROBE_REPLAY_DIR`, `PROBE_RUNTIME_DIR`, `PROBE_PINS_DIR`; needs full git history, npm ci for the index supersession probes | PARTIAL (being resolved) | Probe-state work item (T4a, #140) and its follow-ups (#141 and governance #55), measured with full git history and the index node install: 223 collected in 17 modules (the provenance probes are collected only with PROBE_PINS_DIR). Before T4a: 210 pass, 13 fail. Now: 6 authority-ra probes are strict expected failures recorded as registered findings (known limits, listed in suites/v1-probes/KNOWN_LIMITS.md). The 6 ODES probes failed only because the probe helper lagged the package envelope; the helper was corrected in #141 and the module passes at the frozen ODES pin and at ODES main. The authority wording probe failed on one wrapped line of a governance document; the line was reflowed in governance #55 and the probe, which is unchanged, passes against governance main. A recount of the whole suite after these two changes has not been run; the other modules are as T4a measured them. A strict expected failure is reported as skipped, so a requirement that selects those 6 cases stays inconclusive until its known-limit status is declared before a run. Known limits: suites/v1-probes/KNOWN_LIMITS.md. [state at main after T4a and T4a-2; the recount of the whole suite and the controller handling of known limits remain] |
| X-02 | fix2-probes: evidence-check hardening probes (controls plus strict pending-hardening xfail probes) | `PROBE2_*_DIR=... python -m pytest -q suites/fix2-probes` | 213 (collected at main) | `PROBE2_CONTROL_PLANE_DIR`, `PROBE2_ERGONOMICS_DIR`, `PROBE2_EXCHANGE_DIR`, `PROBE2_MANIFEST_DIR`, `PROBE2_ODES_DIR`, `PROBE2_PACK_DIR`, `PROBE2_REPLAY_DIR`, `PROBE2_RUNTIME_DIR`, `PROBE2_VERIFIER_DIR` | PASS (22 known limits) | Measured twice at qualification main after T4a (#140): 191 passed, 22 xfailed, 0 failed (213 collected). The 56 marks that covered passing probes were removed, so those probes now run as controls. The 22 remaining probes are strict expected failures with a `known limit:` reason, listed with component and property in suites/fix2-probes/KNOWN_LIMITS.md (known-limit count 22). A decision per group (keep as known limit, revise the expectation, or harden the component) is pending; none of the 22 is a pass. Known limits: suites/fix2-probes/KNOWN_LIMITS.md. [state at main after T4a; the decision per known-limit group is pending] |
| X-03 | security-runtime: merged-source cases, each run twice with fresh stores | `python tools/run_security_runtime.py --profile process/security-runtime-f5b-20261016-r8.json --prepare-work --components DIR --out OUT (twice), then python -I tools/summarize_security_runtime.py OUT/run-N` | not counted (workflow defined) | needs built pinned components | NOT_RUN_HERE | Builds the pinned components; count is in the run output. Collection fails without the built components. |
| X-04 | runtime-authority candidate suite | `python tools/run_runtime_authority.py --components components --out results/runtime-authority` | not counted (workflow defined) | needs component checkouts | NOT_RUN_HERE | Count is in the run output; needs the component checkouts. |
| X-05 | v1-scenarios: catalog scenarios executed twice and compared | `SCN_COMPONENTS_DIR=... SCN_HUB_DIR=... python -m pytest -q suites/v1-scenarios` | 1,093 (collected at main) | `SCN_COMPONENTS_DIR`, `SCN_HUB_DIR`, `SCN_INDEX_DIR`, `SCN_INDEX_CHAIN_DIR`, `SCN_EVIDENCE_DIR`, `SCN_BITREP_DIR` | NOT_RUN_HERE | 1,093 tests collected at qualification main. Not run by the inventory; needs the built components, the hub, the index and attestation packages and node. Race cases join threads for 30 s (B-09). |
| X-06 | operation-identity profile: dedupe, reversibility, escalation deadline, refund flow | `OI_CONTROL_PLANE_DIR=... OI_RUNTIME_DIR=... python -m pytest -q suites/operation-identity` | 50 (collected at main) | `OI_CONTROL_PLANE_DIR`, `OI_RUNTIME_DIR` | PASS | 50 pass at main in the inventory run. |
| X-07 | outside-holder profile: witness digest rewrite and drop, holder inventory | `OH_CONTROL_PLANE_DIR=... OH_RUNTIME_DIR=... python -m pytest -q suites/outside-holder` | 17 (collected at main) | `OH_CONTROL_PLANE_DIR`, `OH_RUNTIME_DIR` | PASS | 17 pass at main in the inventory run. |
| X-08 | Verifier mutation report: every verifier rule is mutated and each mutation must be detected | `python -m unittest tests.test_verifier_mutation_harness tests.test_verifier_mutation_witnessed, then python -m verifier_mutation report --odes ... --jobs 4 --verifier-cmd ...` | not counted (workflow defined) | `VERIFIER_CLONE` | NOT_RUN_HERE | The harness tests pass (inside C1-14); the report run needs the verifier and ODES checkouts and was not run by the inventory. |
| X-09 | Relocated component integration suites (overlay) run against pinned producers | `the component workflows delegated to the qualification repository (see C1-04a, C1-05a, C1-06a, C1-07a, C1-01)` | 5,763 (collected at inventory) | `MOLTBOT_SAFE_CONTROL_PLANE_ROOT`, `MOLTBOT_SAFE_MANIFEST_FIXTURE`, `UPSTREAM_MANIFEST_EXAMPLE`, `UPSTREAM_REPLAY_SUCCESS_EXAMPLE`, `UPSTREAM_GAX_ROOT`, `AGEP_PINNED_CONTROL_PLANE_ROOT`, `AGEP_V2_ODES_ROOT` | ENV | 5,763 collected across the overlays; these include each component's own tests, so they overlap Category 1. Measured unconfigured: about 300 environment skips and 70 environment failures. Needs an environment builder that materialises the pinned producers (B-08). |
| X-10 | Orchestrator chain at its own pins: control, runtime, evidence, connected handoff and Replay, contract matrix (private repository) | `the local chain script of the private orchestrator checkout (mirrors its workflows)` | 417 (measured native) | none | PASS | 160 live cases plus the 257 local cases of C1-13: pass with 0 skips once the environment is set. This shows the chain at its own recorded revisions, not at main; the tests assert the revisions and refuse main by design until the pin round (B-12). |
| X-11 | Orchestrator candidate overlay: candidate matrix at main (baseline byte identity, pin-move delta, journal profiles, races, holder inventory, Replay and pack outcomes) (private repository) | `COGNOUS_OVERLAY_* environment, python -m pytest -q -p no:cacheprovider tests/overlay` | 38 (measured native) | none | FAIL | 35 pass and 3 fail at main in the inventory run: pack versus Replay main revision, Replay reader versus control plane main label, and a verifier test that expects exactly one could_not_check where main now reports one more (B-04). Dispatch only in CI. |
| X-12 | Vendored-contract drift and contract matrix | `python tools/contract_matrix.py check --components DIR (plus the contract tests of C1-01, C1-02, C1-03, C1-04, C1-05, C1-14)` | 261 (collected at inventory) | none | PARTIAL | Unit tests pass. Matrix check at main: 2 of 2 boundaries conform; 4 components stay on the digest-pin gate because no contract is declared for their boundaries. Recorded item: several contract copies carry more than one content under one 0.1.0-draft label (a freeze item; the matrix refuses version strings alone). Known-limit tests: present, not enumerated. |
| X-13 | Candidate matrix: old producer with new reader and new producer with old reader (not yet in a repository) | `no single command today; assembled from X-11, the Replay accepted-label tests, ODES accepted Replay revisions (C1-01), the pack importer pin check (C1-06) and X-12` | not counted (plan) | none | PLAN | Partial. Today it exposes three real incompatibilities at main (X-11, C1-06, C1-01) instead of a passing matrix; the pin round has to resolve them first. |
| X-14 | Exact-chain consistency check: every pin in every holder versus the lock and versus main (not yet in a repository) | `python -I pin_check.py --clones DIR --json OUT --md OUT (read only, stdlib)` | not counted (plan) | none | PLAN | Exists as a preparation tool that is not yet in a repository (planned for qualification tools/). At the time of the inventory no pin site for four components was at head. Must be re-run after the pin round. |
| X-15 | Controller and aggregate: plan, freeze-verify, component-suite, probe-suite, native-f5b, harness-and-hub-tests, scenarios, matched-refund, aggregate | `gh workflow run v1-validation.yml -f validation_id=<id> -f label=<label> (dispatch only)` | 131 (declared) | none | NOT_RUN_HERE | 131 declared requirements (81 tests, 26 gaps, 20 not applicable, 4 jobs). Described only: the controller is run by the coordinator after the owner's go, never by workers. It runs at frozen pins, so on its own it does not test main. docs/v1-known-limits.md records the scope reduction of the V1 claim. Known-limit tests: present, not enumerated. |
| X-16 | Supported refund-style flow end to end, including the matched refund battery | `orchestrator steps (see X-10) and python tools/run_matched_refund.py (needs the retained common stimulus)` | 84 (measured native) | none | PARTIAL | 84 orchestrator cases pass at their pins; the 20-trial matched refund battery verifier unit tests pass (C1-14); the 20-trial re-execution was not run. At main the flow runs only through the overlay (X-11, 3 failures). |
| X-17 | Hub delegated cross-component workflows (21) | `the delegated workflows cognous-open-control-stack--*.yml (dispatch or pull request)` | not counted (workflow defined) | none | NOT_RUN_HERE | Count per workflow comes from the run. Some need a Rust toolchain, node, docker or a live gateway. |

## 5. Category 3: AI Security Wiki derived tests

**Source.** 656 upstream test case specifications from the AI Security Wiki (23 libraries), imported into `scenarios/ai-security-wiki/catalog.json` pinned at upstream commit `1a0c72de4752a1c6932172e5e7dbf14f755799c8` under CC BY-SA 4.0; attribution and licence are in `scenarios/ai-security-wiki/`. Importing a case does not make it a test.

**Classification** (`scenarios/ai-security-wiki/applicability.json`, decided from the declared scope before any result was consulted; not a verdict and not a score):

| Class | Cases |
|---|---:|
| APPLICABLE | 20 |
| PARTLY_COVERED | 45 |
| NOT_APPLICABLE | 591 |
| Total | 656 |

The 65 in-scope cases (APPLICABLE plus PARTLY_COVERED) split into individual-component and cross-component cases by the `split` member of each entry:

| Subdivision | Rule | In-scope cases | APPLICABLE | PARTLY_COVERED | Cases with tests in `suites/wiki-derived` | Tests |
|---|---|---:|---:|---:|---:|---:|
| W-I (individual-component) | one component's interface alone can satisfy the procedure | 17 | 2 | 15 | 11 | 47 |
| W-X (cross-component) | the observable is the assembled chain; two or more components | 48 | 18 | 30 | 38 | 176 |

The 591 NOT_APPLICABLE cases each carry a one-line reason in `applicability.json` (capabilities the stack does not have, such as red-team tooling, training, fleet or browser features, or scope the owner excluded) and are outside the denominator but listed there.

**The suite.** `suites/wiki-derived` holds 232 tests collected at main: 9 skeleton and registry tests that carry no case id (5 registry and count checks, 4 route smoke tests that skip without the pinned reference), plus the 223 tests of work packages A to F and G1 to G3 listed below. Every package was run locally at the pinned reference and passed with none skipped or marked as expected failures; the cases still stay NOT RUN until the controller runs. Package WP-H (the published not-claimed sentences for the 45 PARTLY_COVERED cases) adds a registry test and wording in `applicability.json`, not further cases.

| Package | File | Scope | PR | Tests | W-I tests | W-X tests | Cases (W-I) | Cases (W-X) |
|---|---|---|---:|---:|---:|---:|---|---|
| WP-0 | `suites/wiki-derived/test_wiki_skeleton.py` | skeleton, registry checks, route smoke tests | #130 | 9 | - | - | - | - |
| WP-A | `suites/wiki-derived/test_wp_a_grant_lifecycle.py` | grant expiry, revocation and rotation | #132 | 23 | - | 23 | - | TC-D09-009, TC-D09-016, TC-L02-011, TC-L06-023, TC-L09-003, TC-L09-014 |
| WP-B | `suites/wiki-derived/test_wp_b_identity_scope.py` | identity, principal binding and privilege scope | #131 | 28 | 7 | 21 | TC-D09-011, TC-L05-012 | TC-L06-019, TC-L09-006, TC-L09-007, TC-L09-018, TC-L09-019 |
| WP-C | `suites/wiki-derived/test_wp_c_budget_stop_recovery.py` | budgets, stop, approval binding, restore and failure behaviour | #134 | 39 | 8 | 31 | TC-L06-022, TC-L06-024 | TC-D12-021, TC-L06-016, TC-L15-019, TC-L17-028 |
| WP-D | `suites/wiki-derived/test_wp_d_manifest_change_control.py` | manifest, tool binding, allow-list and change control | #133 | 24 | 4 | 20 | TC-L06-017 | TC-L06-007, TC-L06-008, TC-L06-009, TC-L06-011, TC-L06-034 |
| WP-E | `suites/wiki-derived/test_wp_e_exchange_injection.py` | exchange route and injected-text corpora | #136 | 25 | 6 | 19 | TC-L06-038, TC-L06-041 | TC-L06-020, TC-L07-008, TC-L07-009, TC-L07-012, TC-L07-013 |
| WP-F | `suites/wiki-derived/test_wp_f_records_replay_policy.py` | records, replay, policy revision, pin and digest refusal | #135 | 33 | 22 | 11 | TC-L05-028, TC-L08-036, TC-L16-007, TC-L16-015 | TC-D12-007, TC-L17-020, TC-L17-022 |
| WP-G1 | `suites/wiki-derived/test_wp_g1_integrity_and_export.py` | tamper evidence and export: retained records, the outside-held digest, planted-defect catalogues, signed and unsigned copies | #149 | 26 | - | 26 | - | TC-D12-018, TC-L02-025, TC-L03-022, TC-L17-004, TC-L17-021 |
| WP-G2 | `suites/wiki-derived/test_wp_g2_pack_on_demand_and_decision_state.py` | evidence pack on demand and the state at decision time | #150 | 11 | - | 11 | - | TC-D12-004, TC-L02-016 |
| WP-G3 | `suites/wiki-derived/test_wp_g3_traces_attribution_and_event_fields.py` | replayable traces, identity attribution and event fields | #151 | 14 | - | 14 | - | TC-L06-028, TC-L09-025, TC-L17-002 |
| Total | | | | 232 | 47 | 176 | | |

The two suite rows of this category (they share the files in `suites/wiki-derived`; each test is attributed to W-I or W-X by the `split` of the case it checks):

| ID | Suite | Command | Count | Environment | State | Notes and known limits |
|---|---|---|---:|---|---|---|
| W-I | AI Security Wiki derived tests, individual-component cases (one component's interface satisfies the procedure) | `SCN_COMPONENTS_DIR=DIR python -m pytest -q -p no:cacheprovider suites/wiki-derived` | 47 (collected at main) | `SCN_COMPONENTS_DIR` | NOT_RUN | 17 in-scope cases (2 APPLICABLE, 15 PARTLY_COVERED); 11 have tests in suites/wiki-derived (47 tests). The cases stay NOT RUN until the controller runs. Local runs of the packages pass at the pinned reference; these are material for the controller run, not a recorded verdict. Known-limit tests: present, not enumerated. |
| W-X | AI Security Wiki derived tests, cross-component cases (the observable is the assembled chain) | `SCN_COMPONENTS_DIR=DIR python -m pytest -q -p no:cacheprovider suites/wiki-derived` | 176 (collected at main) | `SCN_COMPONENTS_DIR` | NOT_RUN | 48 in-scope cases (18 APPLICABLE, 30 PARTLY_COVERED); 38 have tests in suites/wiki-derived (176 tests). 10 of the 18 APPLICABLE cross-component cases have a wiki-derived test; 16 of the 20 APPLICABLE cases have partial existing tests named in applicability.json and 4 need new implementation. Cases stay NOT RUN until the controller runs. Known-limit tests: present, not enumerated. |

**How to run.** The registry tests need only the checkout. Tests that use a route need the pinned reference built with `python tools/run_security_runtime.py --profile process/security-runtime-f5b-20261016-r8.json --prepare-work --components DIR --out OUT`; without `SCN_COMPONENTS_DIR` they are skipped, never passed.

```bash
SCN_COMPONENTS_DIR=DIR python -m pytest -q -p no:cacheprovider suites/wiki-derived
```

**Components and routes.** Tests use the synthetic destinations only: route A (effective-grant SQLite destination behind the control plane executor), route B (atomic-claim SQLite destination), route C (local durable exchange with a synthetic refund destination), or no destination (record, bundle or manifest files). Components per case are in the `components` member of `applicability.json` (control plane, runtime, Replay, evidence pack, governed exchange, action manifest, ODES and verifier). No network, payment, model call or production effect is used.

**Environment needs.** The built pinned reference (`SCN_COMPONENTS_DIR`). No workflow collects `suites/wiki-derived` yet; adding the collection step is a pin-round item. Timing: the whole suite takes about 7 minutes locally (the 60-effect fixture in WP-A alone takes about 250 s).

**Current state.**

- All 656 cases are NOT RUN. Nothing in this page is a Wiki result.
- 39 of the 65 in-scope cases have tests in `suites/wiki-derived` (11 W-I, 28 W-X). All 39 are PARTLY_COVERED cases.
- None of the 20 APPLICABLE cases has a test in `suites/wiki-derived` yet: 16 of them have partial existing tests named in `applicability.json` (mostly `suites/v1-scenarios`) and 4 (TC-D12-004, TC-L02-016, TC-L06-039, TC-L06-045) need new implementation. This is the largest open item for gate OCS-3.
- Six PARTLY_COVERED cases rely only on the existing tests named in `applicability.json`: TC-D09-004, TC-D13-003, TC-L02-002, TC-L06-003, TC-L06-026, TC-L08-033.
- The in-scope cases without a `suites/wiki-derived` test, in full: TC-D09-004, TC-D12-004, TC-D12-018, TC-D13-003, TC-L02-002, TC-L02-016, TC-L02-025, TC-L03-022, TC-L05-013, TC-L05-022, TC-L06-003, TC-L06-013, TC-L06-014, TC-L06-015, TC-L06-018, TC-L06-026, TC-L06-028, TC-L06-039, TC-L06-040, TC-L06-045, TC-L08-033, TC-L09-004, TC-L09-025, TC-L17-002, TC-L17-004, TC-L17-021.
- The comparison extension (the pre-registered Wiki subset) does not exist yet. Only cases that observe a destination effect can be comparative; cases that apply to one OCS component alone are not.

**Known limits.** For PARTLY_COVERED cases the published `not_claimed` sentence in `applicability.json` states what the test does not show. Seven tests are named as known-limit tests (others assert limits inside ordinary tests and are not separately enumerated):

- `test_wp_b_identity_scope.py::test_wiki_l09_018_host_asserted_authenticated_flag_is_a_known_limit`
- `test_wp_b_identity_scope.py::test_wiki_l09_019_shared_engine_database_evidence_status_is_not_tenant_scoped_known_limit`
- `test_wp_c_budget_stop_recovery.py::test_wiki_l15_019_restore_of_an_older_backup_readmits_later_effects_known_limit`
- `test_wp_d_manifest_change_control.py::test_wiki_l06_009_a_decision_alone_does_not_refuse_two_tools_of_one_name_known_limit`
- `test_wp_d_manifest_change_control.py::test_wiki_l06_034_a_grant_edited_in_place_without_a_new_revision_is_read_as_current_known_limit`
- `test_wp_e_exchange_injection.py::test_wiki_l06_020_known_limit_the_hop_where_content_was_stopped_is_not_recorded`
- `test_wp_e_exchange_injection.py::test_wiki_l06_038_known_limit_a_registry_holds_one_recipient_and_refusals_are_not_stored`

## 6. Gate blockers at the time of the inventory

| ID | Item | State |
|---|---|---|
| B-01 | fix2-probes: the 56 marks that covered passing probes were removed (T4a); 22 probes remain as recorded known limits, with a decision per group pending (keep, revise the expectation, or harden) | being resolved |
| B-02 | Control plane real-SDK test skips without the pinned third-party SDK; the AGT test file needs pytest-asyncio | open |
| B-03 | ODES and Replay accepted-revision graph does not include Replay main | open |
| B-04 | Some tests and helpers lag component changes at main (runtime helper tests, one overlay test, three orchestrator overlay tests) | open |
| B-05 | Replay to pack pairing test depends on which pack and Replay are installed | open |
| B-06 | v1-probes: 6 registered-finding probes are recorded as known limits; the 6 ODES probes and 1 wording probe were lags of a helper and of a document and are corrected; controller handling of known-limit results is pending | being resolved |
| B-07 | In-body skips (verifier 22, Replay 12) and conditional skips (ODES 8) are not declared | open |
| B-08 | Overlay and delegated suites skip or fail unless pinned producer checkouts and variables are set; no environment builder yet | open |
| B-09 | Load-sensitive tests with short fixed timeouts | open |
| B-10 | Shallow checkouts and missing node install affect several probes and hub tests | open |
| B-11 | Native tests of three repositories are not all run by their own CI | open |
| B-12 | Pin graph: component pins are behind main; orchestrator suites assert their older pins | open |

This page only records that these items exist and what each needs to be resolved or reclassified before a gate run. Items marked "being resolved" are in progress in separate work items.

## 7. How the gate is to be run

1. A single release-candidate manifest names the exact revisions of the component repositories. The exact-chain consistency check (X-14) must report no split and no behind-main pin for the gate-relevant components.
2. One environment builder creates the virtual environments, the pinned producer checkouts at full history, the node install for the index package, and exports every variable the suites need (`PROBE_*`, `PROBE2_*`, `OI_*`, `OH_*`, `SCN_*`, `MOLTBOT_SAFE_*`, `UPSTREAM_*`, `AGEP_*`, `VERIFIER_CLONE`, `NATIVE_HUB_ROOT`). The gate refuses to start if a variable is unset or a checkout does not match the manifest. The builder does not exist yet.
3. Linux, Python 3.11 and 3.12 (the verifier and ergonomics also 3.13), a runner with no other load.
4. Order: the exact-chain check, the environment self-check, Category 1, Category 2, Category 3, then the comparison suite, then the controller and aggregate (run by the coordinator only after the owner's go).
5. Load-sensitive tests run serially. A failure of a listed test is re-run alone once only if the failure is a timeout from the declared set; both results are kept.
6. Evidence is retained per run under `results/release-gate/<candidate-id>/<run-id>/` in a reviewable pull request and is never edited afterwards; corrections are new files. Failed attempts are kept next to the green run.

Workers do not run the gate. No release, tag, publication or label change is part of running it.

## 8. Keeping this page honest

`inventory.json` is the source for the counts. `tests/test_release_gate_inventory.py` checks that the JSON validates, that every suite path that is declared to be in this repository exists, that the Wiki counts equal `scenarios/ai-security-wiki/applicability.json` (656 cases; 20, 45 and 591 by class; the in-scope split; the case ids of each package equal to the ids found in its file), that every suite id appears in this page and the reverse, and that the 21 delegated hub workflows exist. It does not run any suite and does not check counts that come from other repositories or from runs. When a suite is added, renamed or recounted, change the JSON and this page together.
