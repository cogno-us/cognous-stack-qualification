# Security repairs and residual limits — 16 October 2026

This note records the F5b repairs to qualification tooling and the residual limits left open. It grants no security clearance, release selection or production authorization. Operational HOLD remains in force.

## Repaired

- **Privileged workflow dependencies.** Capture qualification run, Upstream Wiki refresh and Publish qualification dashboard install PyYAML, jsonschema and their transitive dependencies only from `tools/requirements-ci.lock` with `--require-hashes` and binary wheels for CPython 3.12. Pages publication does not persist checkout credentials. Capture and Wiki refresh keep them because their final steps push a branch with the checkout token; those jobs still hold write authority while their own tests run. Hashes bind the downloaded bytes, not the packages' upstream provenance.
- **Local runner source checks.** `tools/prp_openai_evaluation.py`, `tools/run_runtime_authority.py` and `tools/final_source_preflight.py` now call `tools/pristine_checkout.py` before loading external code. A checkout must match the pinned HEAD, show no modified, staged, untracked or ignored files (bytecode included), and have no assume-unchanged or skip-worktree index entries. **Local runners require fresh runner-owned clones.** Do not reuse a working checkout or one another party can write to. These checks do not authenticate a compromised host, exclude concurrent writers or compare every file with a reviewed digest. `tools/run_security_runtime.py` is unchanged because retained F3 evidence binds its hash.

## Residual limits (deferred)

- **Mutable references in read-only reusable workflows.** Nineteen migrated reusable workflows (`workflow_dispatch`/`workflow_call`, `contents: read`) reference 99 Actions by major tag (`@v4`, `@v5`). The OpenShell image qualification workflow pulls `python:3.12-slim` by tag and records the resolved digest afterwards; it does not enforce a reviewed digest. A moved or compromised upstream tag could therefore alter the code that produces their evidence. Treat their outputs as qualified only for the identities they recorded.
- **Public link checker DNS rebinding.** `tools/check_public_links.py` validates one DNS answer as public and then connects by hostname, so a host that resolves again to a private address can receive the anonymous, bounded HEAD/Range request. This is a local CLI only; run it on hosts with no sensitive internal services in reach.
- **Wiki import has no size budget.** `tools/sync_ai_security_wiki.py` reads and parses upstream Markdown fully in memory without size or count limits. The scheduled refresh is bounded only by its 15-minute job timeout and runner resources; oversized upstream content can make the refresh fail but does not execute upstream code.

## F3 evidence disclosure

The retained F3 source-run summaries (`results/security-runtime-merged-20261016/run-*/source-run-summary.json`) record `qualification_worktree_dirty: true`. This is because the hosted run wrote its untracked outputs inside the qualification checkout before computing that field: `--out results/security-runtime/run-N` and the `--components _components` clones. It does not show that tracked qualification sources changed; `source_hashes` bind the runner, suite and profile bytes.
