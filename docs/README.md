# Documentation index

Every page under `docs/`, grouped by what a reader wants to do. Each row says what the page is and its state. States used here:
**current** (describes the repository as it is), **known limit** (states limits and keeps them visible), **proposed** (a draft or
plan, not a supported interface), **historical** (a dated record; kept as written, not updated), **generated** (written by a tool;
do not edit by hand).

Scope of everything in this repository: a bounded synthetic profile. Comparators are configured by Cognous. This is not independent
certification and not production readiness; operational trust stays on HOLD. Linux only.

Back to the [repository README](../README.md).

## Understand what is tested and how

| Page | What it is | State |
|---|---|---|
| [Release test inventory](test-inventory.md) | Every suite of the release test gate: command, count, environment, state, known limits, blockers. Twin: [`process/release-gate/inventory.json`](../process/release-gate/inventory.json) | current (an inventory, not a result) |
| [Execution and evidence contract](execution-contract.md) | What a run must pin and record; gates and metrics | proposed |
| [Source provenance](sources.md) | Where the catalog came from and what its scope is | current |
| [Serial qualification packet](serial-qualification.md) | The T0 program of named deterministic variants; human oversight is NOT EVALUATED | current |
| [Refusal-test template](refusal-test-template.md) | The one shape every effect-time refusal scenario uses | current |
| [Contract-version matrix](contract-matrix.md) | How the compatibility gate uses contract versions; labels stay `0.1.0-draft` | current (alpha) |

## Run tests and read results

| Page | What it is | State |
|---|---|---|
| [Suites index](../suites/README.md) | Every suite directory, with command and inventory row | current |
| [Qualification dashboard](qualification-dashboard.md) | Scenario mappings, workflow outcomes and gaps | generated (by `tools/build_dashboard.py`) |
| [Dashboard operations](qualification-dashboard-guide.md) | How the dashboard is captured and built | current |
| [Results and retention rules](../results/README.md) | Layout of `results/`, append-only rules | current |
| [Result commentary index](../results/readme-commentary/index.md) | Relocated component reporting with source references | current |
| [Testing process](../process/testing/README.md) | Configuration checkpoint, D01/D03 comparison and D04 recovery | current |

## Known limits and residuals

| Page | What it is | State |
|---|---|---|
| [V1 known limits](v1-known-limits.md) | The narrowed V1 claim and the limits kept visible | known limit |
| [Security repairs and residual limits (16 October)](security-residuals-20261016.md) | Repairs to qualification tooling, with an update of 2026-10-18, and the residual limits | known limit |
| [Security coverage corrections (15 October)](security-coverage-addendum.md) | Bounded coverage work for hub issues 138 to 140; grants no clearance | historical |
| [Security remediation compatibility (16 October)](security-remediation-compatibility-20261016.md) | Compatibility corrections after the remediation PRs | historical |
| [Authority probe re-baseline](authority-probe-rebaseline.md) | Re-baseline of the authority probes at the r4 pin | historical |
| [Runtime authority implementation dashboard](runtime-authority-2026-10-15.md) | A nonselected candidate for addendum items K1 to K6 | historical |
| [Adversarial test plan](adversarial-test-plan.md) | Hypothesis backlog mapped to existing tests; batch 1 (T01 to T20) is implemented, results in [`process/adversarial/README.md`](../process/adversarial/README.md) | proposed (plan), batch 1 implemented |

## Extend or maintain

| Page | What it is | State |
|---|---|---|
| [Upstream refresh through GitHub](upstream-sync.md) | How the weekly refresh imports Wiki specifications and opens a PR for maintainer review; it never merges | current |
| [Claude agent pilot](claude-agent-pilot.md) | The bounded Anthropic pilot: scope, accounting, how the key is held (environment secret) | current (campaign record) |
| [OpenAI agent pilot](openai-agent-pilot.md) | The bounded OpenAI pilot: scope, accounting, how the key is held (environment secret) | current (campaign record) |
| [Scenario catalog](../scenarios/README.md) | The 40 Cognous cases; regenerate from `scenarios/catalog.json`, never hand-edit | generated |
| [AI Security Wiki scenarios](../scenarios/ai-security-wiki/README.md) | Imported reference cases and attribution (CC BY-SA 4.0) | generated (imported) |
| [Applicability of the Wiki cases](../scenarios/ai-security-wiki/APPLICABILITY.md) | How each of the 656 cases was classified (20 / 45 / 591) | current |
| [License and attribution](../THIRD_PARTY_NOTICES.md) | Third-party notices | current |

## Other places with their own READMEs

[`suites/wiki-derived/`](../suites/wiki-derived/README.md), [`suites/fix2-probes/`](../suites/fix2-probes/README.md),
[`suites/operation-identity/`](../suites/operation-identity/README.md), [`suites/outside-holder/`](../suites/outside-holder/README.md),
[`suites/verifier-mutation/`](../suites/verifier-mutation/README.md), [`process/adversarial/`](../process/adversarial/README.md),
[`process/testing/`](../process/testing/README.md).
