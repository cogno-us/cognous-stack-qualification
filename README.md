# Cognous Stack Qualification

Cross-component test scenarios, executable test suites and qualification evidence for the [Cognous Open Control Stack](https://github.com/cogno-us/cognous-open-control-stack). This repository records what an assembled, pinned system must demonstrate and, when execution is implemented, what actually happened.

**Scope.** Bounded synthetic profile only. The comparator applications are configured by Cognous, not vendor implementations. This is not independent certification and not production readiness; operational trust stays on HOLD. Linux only.

**Who it is for.** Reviewers who want to see what the stack is tested against, maintainers who run or extend the suites, and the hub's release process, which links evidence from here. It is not an install target for stack users.

**What it does not do.** It does not select component revisions, grant authority, clear publication gates or authorize production. Validating the catalog is not qualification. A green local run of a suite is material for the qualification controller, not a recorded verdict. The controller (`tools/v1_validation.py`, run through the dispatch-only `v1-validation.yml`) has been run at the r10 tuple: the first attempt (run 39345693648) stopped at the aggregate step and is retained as an aborted attempt, and the second run (39349033320, after the artifact split of #182) completed; its results are retained under [`results/v1-validation/v1-2026-10-16-a/g2-r10-39349033320`](results/v1-validation/v1-2026-10-16-a/g2-r10-39349033320) and summarised in [V1 known limits](docs/v1-known-limits.md). A retained result describes one tuple; it is not a release decision.

**Current status** (counts as of `main` on 20 October 2026; the [release test inventory](docs/test-inventory.md) and the generated Wiki index are the sources if they differ):

- **696 specifications, all NOT RUN:** 40 Cognous cases (9 deterministic, 6 agent-behavior, 2 human-oversight, 23 supplemental) and 656 AI Security Wiki reference cases. The catalog itself records no result: a controller result is recorded per requirement row in the retained V1 validation files, not per catalog case.
- **Wiki applicability is classified:** all 656 Wiki cases are assessed against the declared scope in [`scenarios/ai-security-wiki/applicability.json`](scenarios/ai-security-wiki/APPLICABILITY.md): 20 APPLICABLE, 45 PARTLY_COVERED and 591 NOT_APPLICABLE. 65 cases are in scope. A classification is not a verdict. A case added by a later upstream refresh has no classification until it is assessed.
- **Executable suites:** 18 suite directories under [`suites/`](suites/README.md): seven relocated from component repositories and eleven written here. [`suites/wiki-derived`](suites/wiki-derived/README.md) holds 290 collected tests for 61 of the 65 in-scope cases (20 of the 20 APPLICABLE and 41 PARTLY_COVERED).
- **Release test inventory:** [docs/test-inventory.md](docs/test-inventory.md) (machine-readable twin [process/release-gate/inventory.json](process/release-gate/inventory.json)) lists every suite of the release test gate with command, count, environment, state and known limits. It is an inventory, not a result; it states that the gate is not met today and lists the blockers.
<!-- pin-round: the counts above (suite directories, 290 tests, 61 of 65) change when suites land; refresh them with the inventory -->

## Where this repository sits in the stack

<!-- stack-map:start -->
<!-- Canonical block: identical text in every component README. Source: docs/stack-map.md in the hub. Refresh at the pin round. -->
The Open Control Stack groups its repositories by responsibility. The groups are a navigation map, not an execution sequence and not a requirement to install every component. The hub [component lock](https://github.com/cogno-us/cognous-open-control-stack/blob/main/component-lock.json) is the only source of selected revisions; [release status](https://github.com/cogno-us/cognous-open-control-stack/blob/main/docs/release-status.md) states their evidence and limits. Last checked against `component-lock.json` at hub commit `dcc9bd7533ef`.

| Group | Members |
| --- | --- |
| **01 Knowledge & Provenance** | [Evidence Registry (The Index)](https://github.com/cogno-us/cognous-evidence-registry) · [Evidence Attestation (BitRep)](https://github.com/cogno-us/cognous-evidence-attestation) |
| **02 Institutional Governance** | [Institutional Governance (Alvorada)](https://github.com/cogno-us/cognous-institutional-governance) |
| **03 Declaration & Policy Control** | [Action Manifest](https://github.com/cogno-us/cognous-action-manifest) · [Control Plane](https://github.com/cogno-us/cognous-control-plane) |
| **04 Constrained Execution** | [Execution Runtime](https://github.com/cogno-us/cognous-execution-runtime) |
| **05 Replay & Evidence** | [Replay Bundle](https://github.com/cogno-us/cognous-replay-bundle) · [Governance Evidence Pack](https://github.com/cogno-us/cognous-governance-evidence-pack) · [ODES](https://github.com/cogno-us/open-decision-evidence-standard) |
| **Cross-cutting exchange** | [Governed Exchange (GAX/IMX)](https://github.com/cogno-us/cognous-governed-exchange) |
| **Tooling and qualification** (side group) | [Ergonomics (`cognous-ocs`)](https://github.com/cogno-us/cognous-open-control-stack-ergonomics) · [Verifier](https://github.com/cogno-us/cognous-open-control-stack-verifier) · [Orchestrator](https://github.com/cogno-us/cognous-stack-orchestrator) · [Qualification](https://github.com/cogno-us/cognous-stack-qualification) |

Status labels used in this README: **merged** (reviewed and merged in the owning repository; not by itself selected), **selected** (pinned in the hub lock), **known limit** (a limitation that is stated and kept visible) and **proposed** (draft or planned work, not a supported interface). Full map, names and commands: [stack map](https://github.com/cogno-us/cognous-open-control-stack/blob/main/docs/stack-map.md), [naming](https://github.com/cogno-us/cognous-open-control-stack/blob/main/docs/naming.md), [profiles and tools](https://github.com/cogno-us/cognous-open-control-stack/blob/main/docs/profiles-and-tools.md). A signature, registry entry, message receipt or evidence summary does not grant execution authority.
<!-- stack-map:end -->

This repository is in the **Tooling and qualification** side group. It is not in the hub lock: it holds cross-component tests and results, and it is the central target of the component READMEs' test commentary ([result-commentary index](results/readme-commentary/index.md)).

## Start here

| If you want to | Read |
|---|---|
| **Understand** what is tested and why | [Release test inventory](docs/test-inventory.md) · [Execution and evidence contract](docs/execution-contract.md) · [Source provenance and scope](docs/sources.md) · [Serial qualification packet](docs/serial-qualification.md) |
| **Run** tests | [Quick start](#quick-start) below · [Suites index](suites/README.md) · [What ships](#what-ships) |
| **Read results** | [Qualification dashboard](docs/qualification-dashboard.md) (generated) · [Results and retention rules](results/README.md) · [Latest retained controller results (r10)](results/v1-validation/v1-2026-10-16-a/g2-r10-39349033320/summary.md) · [Result commentary index](results/readme-commentary/index.md) · [V1 known limits](docs/v1-known-limits.md) |
| **Review limits** | [Security repairs and residual limits](docs/security-residuals-20261016.md) · [Adversarial test plan](docs/adversarial-test-plan.md) and [batch-1 results](process/adversarial/README.md) · [Known limits of the probe suites](suites/fix2-probes/KNOWN_LIMITS.md) and [of the V1 probes](suites/v1-probes/KNOWN_LIMITS.md) |
| **Extend** the catalog or suites | [Browse the scenario catalog](scenarios/README.md) · [Machine-readable Cognous scenarios](scenarios/catalog.json) · [AI Security Wiki scenarios](scenarios/ai-security-wiki/README.md) · [Upstream refresh through GitHub](docs/upstream-sync.md) · [Refusal-test template](docs/refusal-test-template.md) · [Dashboard operating guide](docs/qualification-dashboard-guide.md) |
| **Check licensing** | [License and attribution boundaries](THIRD_PARTY_NOTICES.md) |
| **Find any page** | [Documentation index](docs/README.md) |

## Quick start

From a clean checkout, with Python 3.12 or later on Linux. These commands read the repository only: no network access to components, no model call, no workflow.

```bash
git clone https://github.com/cogno-us/cognous-stack-qualification.git
cd cognous-stack-qualification
python3 -m venv .venv && . .venv/bin/activate
python -m pip install PyYAML==6.0.2 jsonschema==4.26.0 pytest==8.3.5
```

**1. Validate the catalog** (about a second; exit 0):

```bash
python tools/validate_catalog.py
```

```text
Valid: 40 Cognous + 656 Wiki specifications; provenance/license records checked. No qualification scenarios executed.
```

**2. Run the registry checks of the Wiki-derived suite** (about two seconds; exit 0). Tests that need component checkouts are skipped, never passed:

```bash
python -m pytest -q -p no:cacheprovider suites/wiki-derived
```

```text
5 passed, 285 skipped
```

**3. Run the repository's own tests** (a few minutes, depending on the machine; this is what the catalog-validation workflow runs):

```bash
python -m unittest discover -s tests
```

```text
Ran 413 tests in 208.113s

OK (skipped=1)
```

<!-- pin-round: the test count and time in step 3 change when tests/ changes; refresh with the inventory -->

What these show: the catalog and its provenance records are consistent, and this repository's tooling and static guards pass. What they do not show: any scenario result, any component behaviour, or qualification. Suites that run against component checkouts (for example `SCN_COMPONENTS_DIR=DIR python -m pytest -q -p no:cacheprovider suites/wiki-derived`, or `python tools/run_suite.py`) need the pinned checkouts that the [suites index](suites/README.md) and the inventory name; they were not run for this quick start. With the same interpreter, `python -m pytest --ignore=tests/native -q tests` runs the same files under pytest; `tests/native` holds native tool-boundary tests that need a hub checkout (`NATIVE_HUB_ROOT`) and are left out of the quick start.

## What ships

| Area | Contents |
|---|---|
| [`scenarios/`](scenarios/README.md) | `catalog.json` (40 Cognous cases), `coverage-map.json`, and `ai-security-wiki/` (656 imported reference cases, `applicability.json`, CC BY-SA 4.0) |
| [`suites/`](suites/README.md) | 19 executable suite directories (see the [suites index](suites/README.md)) |
| `tools/` | See the table below |
| [`process/`](docs/README.md) | `testing/` (bounded comparison process), `adversarial/` (batch-1 tests T01 to T20, [README](process/adversarial/README.md)), `release-gate/` (inventory twin), `v1-validation/`, and retained runtime-authority and security-runtime profile files |
| [`results/`](results/README.md) | Retained evidence and workflow metadata: `workflows/` (append-only), `v1-validation/`, `security-runtime-*`, `serial/`, `comparisons/`, `verifier-mutation/`, `readme-commentary/` and others. Retained files are not rewritten |
| [`docs/`](docs/README.md) | Documentation index and every page |
| `reports/`, `qualification/`, `schemas/`, `sources/`, `migrations/` | Dated reports, serial orchestration state, JSON schemas, the source register and Wiki lock, and the migration manifests |
| `dashboard/` | Static assets for the generated qualification dashboard |
| `.github/workflows/` | 69 workflows; see [GitHub workflow](#github-workflow) |

Tools by function (all under `tools/`; the command-line tools print their usage with `--help`):

| Function | Tools |
|---|---|
| Catalog and sources | `validate_catalog.py` (provenance and specifications; never executes scenarios), `sync_ai_security_wiki.py` (pinned Wiki import), `check_public_links.py`, `failure_register.py`, `scenario_report.py` (reporting over recorded results) |
| Run a suite | `run_suite.py` (explicit command in a disposable source checkout, with retained telemetry), `install_suite.py` (assemble relocated tests into a component checkout), `qualification_results.py`, `pristine_checkout.py`, `omit_locks.py` |
| Controller and candidate runners | `v1_validation.py` (frozen-V1 controller helpers; dispatch-only through `v1-validation.yml`), `run_security_runtime.py`, `summarize_security_runtime.py`, `run_runtime_authority.py`, `final_source_preflight.py`, `contract_matrix.py`, `validate_migrations.py` |
| Serial and agent pilots | `run_serial_qualification.py`, `serial_orchestration.py`, `claude_agent_pilot.py`, `openai_agent_pilot.py`, `restore_openai_pilot.py`, `prp_openai_evaluation.py` (the pilots call paid provider APIs and run only through reviewer-gated workflows) |
| Matched refund and exchange evidence | `run_matched_refund.py`, `verify_matched_refund.py`, `export_exchange.py`, `verify_exchange.py`, `trajectory_contract.py`, `safe_paths.py` |
| Dashboard and coverage | `build_dashboard.py` (generates `docs/qualification-dashboard.md`; do not hand-edit), `capture_workflow_run.py`, `security_coverage.py` |
| Dependency locks | `requirements-ci.lock`, `requirements-serial.lock`, `requirements-serial.txt` |

Status labels for what ships: the catalog, tools and suites are **merged** in this repository (none is selected, because this repository is outside the hub lock). Probe suites carry **known limit** expectations as strict expected failures, listed in their `KNOWN_LIMITS.md` files. The pilots' untested scopes and the planned release-gate additions in the inventory are **proposed**.

## Responsibilities

| Location | Responsibility |
|---|---|
| Component repositories | Implementations, component contracts and local regression tests |
| Open Control Stack hub | Canonical architecture, selected component pins, release decisions and evidence links |
| This repository | Cross-component scenario definitions, relocated executable test suites/harnesses, reusable CI and configuration-specific qualification records |

This repository does not select component revisions, grant authority, clear publication gates or authorize production. Existing selection and HOLD decisions remain with their owners. A future run must distinguish selected and nonselected candidate profiles.

## GitHub workflow

Read and change scenarios through GitHub files and pull requests. The Catalog validation workflow checks catalog consistency and provenance/license records on pushes and pull requests. The Upstream Wiki refresh workflow runs weekly on Mondays at 14:17 UTC, validates the generated update (provenance, license and importer checks) and opens a pull request for maintainer review; it never merges it. Manual dispatch also remains available. It does not execute D, A, H or C scenarios. No offline file collection is required to browse or maintain the catalog.

The repository has 69 workflows (retained, not edited by documentation changes):

| Kind | Workflows |
|---|---|
| Catalog and migration checks | `catalog-validation.yml` (runs `tools/validate_catalog.py` and the unit tests), `migration-integrity.yml` |
| Upstream import | `upstream-wiki-refresh.yml` (opens a PR for review; never merges) |
| Controller | `v1-validation.yml` (dispatch only; plan, freeze check, suites, aggregate) |
| Delegated component workflows (50) | `<repository>--<name>.yml`: the original test commands of the relocated suites, run against pinned components (dispatch or `workflow_call`) |
| Profile and candidate runs | `operation-identity-profile.yml`, `mvp-chain.yml` (proposed MVP chain harness, dispatch only; see [`suites/mvp-chain/`](suites/mvp-chain/README.md); the local, CI-unwired route-B builder suite is [`suites/mvp-d2-route-b/`](suites/mvp-d2-route-b/README.md)), `outside-holder-profile.yml`, `verifier-mutation-report.yml`, `runtime-authority-candidate.yml`, `security-runtime-qualification.yml`, `security-runtime-f5b-qualification.yml`, `security-coverage.yml`, `serial-qualification.yml`, `remediation-compatibility-pr.yml` |
| Dashboard and capture | `capture-qualification-run.yml`, `qualification-dashboard.yml`, `publish-qualification-dashboard.yml` |
| Paid provider pilots | `claude-agent-pilot.yml`, `openai-agent-pilot.yml` (the paid jobs run in the reviewer-gated `provider-keys` environment; keys are environment secrets) |

Future execution workflows should capture exact source identities, perform containment and reset checks, run supported scenarios, and retain result manifests plus evidence through GitHub. Migrated reusable workflows execute their original test commands against pinned components. The generated [qualification dashboard](docs/qualification-dashboard.md) links proposed scenario mappings and append-only workflow metadata. Captures are initiated from GitHub Actions and open review PRs; merging them refreshes the dashboard. The static HTML build is available as a workflow artifact, with optional Pages publishing after administrator enablement. Workflow artifacts expire; accepted release evidence needs durable retained references and hashes before it can support a release decision.


## Qualification rules

Every run must pin the harness and component commits, profile, fixtures and evaluator configuration. Cases may be PASS, FAIL, INCONCLUSIVE, NOT RUN or NOT APPLICABLE with reasons. Missing authoritative observations cannot support a passing completion claim. Unsupported capabilities are explicitly out of scope rather than simulated and counted as coverage.

Keep deterministic, actual-agent, human-review and operational evidence separate. A separate repository does not establish reviewer independence. Historical passes do not qualify changed configurations. No model or fleet capability is required merely because it appears in the catalog.

The serial T0 program implements named deterministic variants, then gates actual-agent runs on a supported configuration. Human participation is excluded and human oversight effectiveness is NOT EVALUATED. See [the serial packet](docs/serial-qualification.md). Preserve all failures, missing trials and residual limits. See the execution contract for gates and metrics.

## License

The existing [Apache License 2.0](LICENSE) covers original repository code and Cognous scenario adaptations. Relocated suites preserve their original per-file Apache-2.0/MIT scope and source NOTICE files; see [the migration manifest](migrations/cross-component-2026-10-15.json). **AI Security Wiki content and adaptations under `scenarios/ai-security-wiki/` remain CC BY-SA 4.0**, with a nested license and author attribution. Source-document terms and reuse basis are explicit in [the source register](sources/documents.json). See [third-party notices](THIRD_PARTY_NOTICES.md); cited external works are not automatically licensed by their citation.

## Centralized component test commentary

[README result-commentary index](results/readme-commentary/index.md) preserves relocated component reporting with exact source references. Publish new test-result commentary in this repository; keep component READMEs focused on usage, contracts and limitations. Historical evidence does not qualify changed configurations.
