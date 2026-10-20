# Comparator package

**Scope.** Bounded synthetic profile only. The comparator applications (the OPA application and the LangGraph plus OPA application) are configured by Cognous, not vendor implementations. This is not independent certification and not production readiness; operational trust stays on HOLD. Linux only.

Caveats that stay with every report (RP-8, unchanged): the corner plan was authored after inspection of the baseline code and is not blinded, and both plans had no independent review; the shared Cognous wire and signature helpers feed all three configurations.

## What this directory is

The material for the pre-registered comparison ([pre-registration](../docs/release-gate/pre-registration.md), sections 5 to 7, 9 and 10): the two comparator applications for the Wiki subset, the Wiki-subset plan file (PR-6) with the expected outcomes it rests on, the declared interfaces, the dependency lock, and the list of digests that the freeze amendment names. The comparison is destination-only for the Wiki subset (amendment 76): the protected destination, the OPA application and the LangGraph plus OPA application are scored by the same oracle; the cross-reference file names test ids at other harnesses and is never scored.

Nothing here has been run as a comparison. No scenario of the registered corner, baseline or Wiki sets has been executed on any configuration for the purpose of a result, no workflow uses this directory, and nothing in it changes a registered file, a pin, a profile, the inventory or the pre-registration. The corner and baseline sets use the registered files under `suites/cognous-open-control-stack/` unchanged; their digests are listed in `DIGESTS.md`.

## Layout

| Path | Content |
|---|---|
| `wiki/apps/` | `wiki_opa_app.py` and `wiki_policy.rego` (the OPA application and its rule file), `wiki_langgraph_app.py` (the graph layer over that application), `wiki_config.py` (the declared world) |
| `wiki/harness/` | `_base.py` (locates the pinned trees, checks the pinned digests, loads the pinned runner file by path), `registered_sets.py` (profile id to class mappings), `author_plan.py` and `validate_plan.py` (build and check the plan file), `plumbing_twin.py`, `gen_crossref.py`, `compute_digests.py` |
| `wiki/interface/` | declared interface of each comparator application, with source references that a test checks |
| `wiki/plans/` | `wiki-subset-plan.json`: the plan file of PR-6 (executable steps of every asked scenario, and every scenario that is not asked, each with its reason) |
| `wiki/expected-outcomes/` | expected statuses and effects per scenario with the rulings they rest on (`outcomes-final.json`, `scenario-outcomes.json`) and the two scripts that produce them from the author's table |
| `wiki/crossref/` | case id to test names at the components that claim the case (different harness, not scored) |
| `deps/` | direct pins and the hash-locked requirements file |
| `tests/` | tests of the package |
| `DIGESTS.md`, `digests.json` | sha256 of every file that the freeze amendment names |
| `DECISIONS.md` | choices made while assembling the package, for owner review |
| `owner-held-records.json` | sha256 of two records that are held by the owner and are not in this repository |

## Rules the package follows

- The scoring function is the registered `evaluate` in `suites/cognous-open-control-stack/tools/run_comparative_governance.py`. The Wiki-subset loader imports that file by path, checks its digest, and replaces only the mapping of profile ids to classes. No scoring code is copied.
- The plan carries no expected reason codes; reason conformance then holds by construction and the durable-denial term of the oracle still applies. Every expected outcome carries the label `from case text` and none was taken from what a configuration did.
- Request fields are the eight of the registered interface only. Application controls (state changes, approval records, counters, idempotency) are application code, not guarantees of OPA or LangGraph.
- No network access at run time. Dependencies are pinned by exact version with hashes in `deps/requirements-comparator.lock` (install with `python -m pip install --require-hashes --only-binary=:all: -r comparators/deps/requirements-comparator.lock`). The OPA binary is the one named, with its digest, in `suites/cognous-open-control-stack/benchmarks/governance/dependencies.json`; it is not stored here.

## Running the tests of the package

The tests need the pinned dependencies, the OPA binary and a checkout of the hub at the revision named in `digests.json` (only `reference_profiles/` is read):

    SCN_HUB_DIR=<hub checkout> SCN_OPA=<opa binary> python3 -m pytest comparators/tests -q -p no:cacheprovider

The plan can be re-validated without running any scenario: `python3 comparators/wiki/harness/validate_plan.py`. The digests can be re-checked with `python3 comparators/wiki/harness/compute_digests.py --check` (same environment).

## Not in the package

- The cell aggregation, the report generator, the contract self-check and the stub adapters of the Wiki-subset runner (listed as open in `DECISIONS.md`).
- The declarations of not expressible and not claimed for the protected destination column (listed as open in `DECISIONS.md`).
