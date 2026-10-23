# Executable cross component suites

These suites were relocated from seven public Cognous repositories. Original source hashes, dependency pins, assertions and per-file licenses are retained; execution-location and provenance adaptations are explicitly marked in the manifest. This is a refactor of ownership, not fresh production qualification. The first table lists the seven relocated suites; a second table lists the suites written in this repository, and the [release test inventory](../docs/test-inventory.md) states command, count, environment and state for every suite. The 696 scenario-catalog entries retain their own NOT RUN statuses until explicitly mapped to executed evidence.

| Owning repository | Moved tests and harness files | Delegated workflows | Source commit |
|---|---:|---:|---|
| [cognous-open-control-stack](cognous-open-control-stack/README.md) | 55 | 21 | `0e6ab2435438dd1edcdc5a00789afa6f0f5f4ccf` |
| [cognous-execution-runtime](cognous-execution-runtime/README.md) | 46 | 11 | `309e194c1b0a3de23e11e20133e6eaf88875e48a` |
| [cognous-replay-bundle](cognous-replay-bundle/README.md) | 8 | 4 | `83fbaf2a0f6f071aca1ea0af859eb8fc6385c26a` |
| [cognous-governance-evidence-pack](cognous-governance-evidence-pack/README.md) | 14 | 7 | `1e789c7d67a897097445faef1813fb0cd22d55e5` |
| [cognous-governed-exchange](cognous-governed-exchange/README.md) | 12 | 3 | `9de2d438ed03531bb960c896f541a6a2da1b2315` |
| [open-decision-evidence-standard](open-decision-evidence-standard/README.md) | 8 | 3 | `25c7ad608c2e6fd9f450e075db6bbf3ee4091a49` |
| [cognous-evidence-registry](cognous-evidence-registry/README.md) | 2 | 1 | `650903fd6db1d68810dd377ba09e801a76682935` |

## Suites written in this repository

The directories below were written here, not relocated. They have no source commit column because they have no source repository. The [release test inventory](../docs/test-inventory.md) is the page that states, per suite, the command, the case count, the environment, the state and the known limits; its machine-readable twin is [`process/release-gate/inventory.json`](../process/release-gate/inventory.json). Counts below are collected counts at the time of the inventory; the inventory is the source for them. A suite that needs component checkouts is skipped or fails without them, as its own README says; nothing here is a verdict.

| Directory | Purpose | Inventory row | Command (needs the named checkouts) |
|---|---|---|---|
| [`v1-scenarios/`](v1-scenarios/) | Catalog scenarios executed twice from fresh stores against the pinned synthetic reference, with normalised observations compared; includes the ASW core families (`test_asw_*.py`) | X-05 | `SCN_COMPONENTS_DIR=... SCN_HUB_DIR=... python -m pytest -q -p no:cacheprovider suites/v1-scenarios` (more `SCN_*` variables are listed in the inventory row) |
| [`v1-probes/`](v1-probes/) | Per-component probes recorded against frozen pins; known limits kept as strict expected failures in [`KNOWN_LIMITS.md`](v1-probes/KNOWN_LIMITS.md) | X-01 | `PROBE_<X>_DIR=<checkout> python -m pytest -q suites/v1-probes/<module>`; a module whose variable is unset is not collected |
| [`fix2-probes/`](fix2-probes/README.md) | Evidence-check hardening probes: controls plus strict expected failures; the 6 known limits are listed in [`KNOWN_LIMITS.md`](fix2-probes/KNOWN_LIMITS.md) | X-02 | `PROBE2_*_DIR=... python -m pytest -q -p no:cacheprovider suites/fix2-probes` |
| [`wiki-derived/`](wiki-derived/README.md) | Tests derived from the AI Security Wiki cases classified APPLICABLE or PARTLY_COVERED | W-I, W-X | `SCN_COMPONENTS_DIR=DIR python -m pytest -q -p no:cacheprovider suites/wiki-derived` |
| [`operation-identity/`](operation-identity/README.md) | Opt-in operation identity, freshness and related profiles (addendum items N1 to N3) with the control plane and runtime | X-06 | `OI_CONTROL_PLANE_DIR=... OI_RUNTIME_DIR=... python -m pytest -q suites/operation-identity` |
| [`mvp-chain/`](mvp-chain/README.md) | Proposed exact-candidate MVP chain: Control Plane decision, operation identity, real claim provisioning, route B atomic executor, Replay, Evidence Pack and the pinned Verifier, the six negative controls (NC4 attacks the real hub ingress as an unprivileged uid); statuses from a proposed expectations file owned by Qualification; ODES is pin-checked, not exercised | none yet (proposed) | `MVP_*_DIR=... python -m pytest -q suites/mvp-chain` (see its README; workflow `mvp-chain.yml`) |
| [`outside-holder/`](outside-holder/README.md) | Witness digest and holder probe scenarios (addendum items M3 and L5); not part of the V1 validation controller | X-07 | `OH_CONTROL_PLANE_DIR=... OH_RUNTIME_DIR=... python -m pytest -q suites/outside-holder` |
| [`verifier-mutation/`](verifier-mutation/README.md) | Report-only measurement of the independent verifier against damaged traces; includes a vendored copy of the verification-report contract in `contract/` (do not edit) | X-08 | `python -m unittest tests.test_verifier_mutation_harness` for the harness proof; the report command is in its README |
| [`security-runtime/`](security-runtime/) | Merged-source chain cases, each run twice from fresh stores; no README, driven by the runner | X-03 | `python tools/run_security_runtime.py --profile <profile> --prepare-work --components DIR --out OUT` (see the inventory row) |
| [`runtime-authority/`](runtime-authority/) | Runtime-authority candidate chain (control plane, runtime, Replay, Evidence Pack); a candidate, never selected; no README | X-04 | `python tools/run_runtime_authority.py --components components --out results/runtime-authority` |

Probe suites report known limits as strict expected failures; a strict expected failure is shown as skipped or xfailed by pytest, never as a pass. The suites above do not select component revisions, grant authority or authorize production.

## Inventory and boundaries

The [migration manifest](../migrations/cross-component-2026-10-15.json) inventories 19 public repositories, including those with no eligible stack integration harness. Component-local schema, importer, adapter and implementation regression tests stay with their owners. Upstream Moltbot application tests, institutional synthetic methodology experiments, protocols, site and scanner infrastructure tests are not relabeled cross-component stack evidence.

Three private repositories were inventoried separately. Private orchestrator integration suites were not copied into this public destination: their private source has no public license grant in the reviewed tree. Private methodology and doctrine remain private and retain their ownership. This refactor does not authorize private-to-public publication.

All 194 original files have source commit/path hashes and retained license notices; 145 executable/support files relocate, 49 existing workflow paths become source-side callers, and one new registry workflow delegates its previously manual chain qualification. Some mixed integration files include helper-level regression assertions; those remain with their cohesive suite to avoid changing assertions or fixture behavior. Runtime fixture helpers remain with their migrated integration suites.

## Reproduction

Run a specific command in a disposable source checkout, with both source and suite identities retained:

```bash
python tools/run_suite.py --suite cognous-open-control-stack \
  --source-root /path/to/cognous-open-control-stack \
  --results-dir /tmp/cognous-migration-run \
  -- python -m pytest -q tests/test_reference_environment.py
```

For actual component integrations, use the migrated workflow’s original dependency commits, installation commands and environment. The runner does not infer or substitute missing dependencies. Missing inputs, skips and characterization outcomes retain their original meaning.

Source-only cold assemblies use the owning Git commit plus the recorded overlay bytes. Any run evidence must retain both identities, the migration manifest hash, dirty-worktree status and the overlay hashes. A source commit alone no longer identifies the test implementation. Frozen historical workflows retain their pinned original checkouts without overlay, and explicitly record that distinction.

The new migration integrity workflow validates structure, byte commitments, licenses and the relocation tooling. It does not execute every historical suite. Existing publication, operational-trust and production HOLD decisions are unchanged.

The follow-up from hub main `9d45ab4389f9ac7b7cd0e3b8823fa2fde56d8503` also delegates the new remediation full-reference workflow and preserves its profile-aware aggregator repair. Location/provenance adaptations are explicitly marked in the manifest; original digests remain recorded.

Comparator application adapters, frozen plans, OPA policy and dependency declarations are canonical test assets here. Component-owned contract fixtures and selected acceptance/profile definitions remain with their owning source, referenced by exact source identity.
