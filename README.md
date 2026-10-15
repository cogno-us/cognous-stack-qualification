# Cognous Stack Qualification

Cross-component test scenarios and qualification evidence for [Cognous Open Control Stack](https://github.com/cogno-us/cognous-open-control-stack). This repository records what an assembled, pinned system must demonstrate and, when execution is implemented, what actually happened.

**Current status:** versioned scenario specifications plus [relocated executable integration suites](suites/README.md). The initial 15 October 2026 snapshot contains **696 NOT RUN specifications**: 40 Cognous cases (9 deterministic, 6 agent-behavior, 2 human-oversight and 23 supplemental) plus 656 AI Security Wiki reference cases. See the generated Wiki index for the current upstream case count after refreshes. Wiki applicability is unassessed until mapped to a supported profile. Relocation validation is distinct from complete stack qualification, actual-agent evaluation or human studies. Catalog validation is not system qualification.

## Start here

- [Executable cross-component suites and source maps](suites/README.md)
- [Browse the scenario catalog](scenarios/README.md)
- [Machine-readable Cognous scenarios](scenarios/catalog.json)
- [AI Security Wiki scenarios and original procedures](scenarios/ai-security-wiki/README.md)
- [License and attribution boundaries](THIRD_PARTY_NOTICES.md)
- [Upstream refresh through GitHub](docs/upstream-sync.md)
- [Execution and evidence contract](docs/execution-contract.md)
- [Source provenance and scope](docs/sources.md)
- [Results and retention rules](results/README.md)

## Responsibilities

| Location | Responsibility |
|---|---|
| Component repositories | Implementations, component contracts and local regression tests |
| Open Control Stack hub | Canonical architecture, selected component pins, release decisions and evidence links |
| This repository | Cross-component scenario definitions, relocated executable test suites/harnesses, reusable CI and configuration-specific qualification records |

This repository does not select component revisions, grant authority, clear publication gates or authorize production. Existing selection and HOLD decisions remain with their owners. A future run must distinguish selected and nonselected candidate profiles.

## GitHub workflow

Read and change scenarios through GitHub files and pull requests. The Catalog validation workflow checks catalog consistency and provenance/license records on pushes and pull requests. The Upstream Wiki refresh workflow runs weekly on Mondays at 14:17 UTC and automatically merges generated update PRs after provenance, license and importer checks pass, subject to GitHub rules; manual dispatch also remains available. It does not execute D, A, H or C scenarios. No offline file collection is required to browse or maintain the catalog.

Future execution workflows should capture exact source identities, perform containment and reset checks, run supported scenarios, and retain result manifests plus evidence through GitHub. Migrated reusable workflows execute their original test commands against pinned components. A unified dashboard and automatic result publication are not implemented. Workflow artifacts expire; accepted release evidence needs durable retained references and hashes before it can support a release decision.

## Qualification rules

Every run must pin the harness and component commits, profile, fixtures and evaluator configuration. Cases may be PASS, FAIL, INCONCLUSIVE, NOT RUN or NOT APPLICABLE with reasons. Missing authoritative observations cannot support a passing completion claim. Unsupported capabilities are explicitly out of scope rather than simulated and counted as coverage.

Keep deterministic, actual-agent, human-review and operational evidence separate. A separate repository does not establish reviewer independence. Historical passes do not qualify changed configurations. No model or fleet capability is required merely because it appears in the catalog.

Implement the deterministic bounded workflow first; add agent and human pilots only with actual supported configurations and reviewers. Preserve all failures, missing trials and residual limits. See the execution contract for gates and metrics.

## License

The existing [Apache License 2.0](LICENSE) covers original repository code and Cognous scenario adaptations. Relocated suites preserve their original per-file Apache-2.0/MIT scope and source NOTICE files; see [the migration manifest](migrations/cross-component-2026-10-15.json). **AI Security Wiki content and adaptations under `scenarios/ai-security-wiki/` remain CC BY-SA 4.0**, with a nested license and author attribution. Source-document terms and reuse basis are explicit in [the source register](sources/documents.json). See [third-party notices](THIRD_PARTY_NOTICES.md); cited external works are not automatically licensed by their citation.
