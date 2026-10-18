# Scenario-derived test suite

Tests derived from the cases of the AI Security Wiki scenario catalog that
`scenarios/ai-security-wiki/applicability.json` classifies APPLICABLE or PARTLY_COVERED. Each test checks the part of one case
that falls inside the declared scope of the stack, against the synthetic bounded reference. The suite adds tests only: it
changes no component, pin, profile, result file or workflow.

## Status

The cases stay **NOT RUN** until the owner runs the qualification controller. A green local run of this suite is material for
that run, not a recorded verdict. A test that fails at the pinned reference is reported, never weakened, skipped or marked as an
expected failure.

## Attribution

The case identifiers and titles come from the AI Security Wiki, licensed CC BY-SA. Attribution, licence text and source commit
are in `scenarios/ai-security-wiki/` (see `README.md`, `LICENSE` and `applicability.json` there). This suite carries case ids
only; it does not reproduce case text.

## Convention

- A test that checks a catalog case carries `@wiki_case("TC-...")` (from `_wiki_helpers`; a module may set
  `pytestmark = wiki_case("TC-...")`). The id must be a string literal. The marker is registered in `conftest.py`, which records
  the id as the `wiki_case` property of the test in the junit output.
- Test names start with `test_wiki_` followed by the layer and case number, for example `test_wiki_d09_009_...`.
- Every test is a control that passes at the pinned head. The infrastructure tests in `test_wiki_skeleton.py` carry no case id.
- Tests use the synthetic destinations only: no network (refused and counted by the autouse `no_network` fixture), no payment,
  no model call, no production effect. Linux only.

## Synthetic destination routes

| Route | Destination | Helpers in `_wiki_helpers` |
|---|---|---|
| A | effective-grant SQLite destination behind the pinned control-plane executor | `route_a`, `execute_a` |
| B | atomic-claim SQLite destination | `route_b`, `execute_b` |
| C | local durable exchange with a synthetic refund destination | `route_c`, `exchange_run`, `exchange_resume`, `exchange_view` |

`destination_summary` and `destination_effects` read the destination through a separate read-only connection. `run_twice` runs
one trial from two fresh work directories. These are thin wrappers over `suites/v1-scenarios/_d02_d05_d09_helpers.py`, loaded on
first use.

## Registry

`test_wiki_skeleton.py` scans the test modules of this directory (without importing them) and checks that every case id refers
to a catalog case classified APPLICABLE or PARTLY_COVERED. It also lists the in-scope case ids that no test carries yet. That
list is a report, not a failure, while the work packages land.

## Running

The registry tests need nothing but the checkout. Tests that use a route need the pinned reference, built with
`tools/run_security_runtime.py --profile <profile> --prepare-work --components DIR --out OUT`; without `SCN_COMPONENTS_DIR`
they are skipped, never passed.

```bash
SCN_COMPONENTS_DIR=DIR python -m pytest -q -p no:cacheprovider suites/wiki-derived
```

## Known gaps at this commit

- The four route smoke tests (routes A, B, C and `run_twice`) are **unverified**: they were never run against the pinned
  reference. They skip, and never pass, without `SCN_COMPONENTS_DIR`.
- No workflow collects this suite. The workflows that run `python -m unittest discover -s tests` do not reach it. The step
  needed is `python -m pytest -q -p no:cacheprovider suites/wiki-derived`, with `SCN_COMPONENTS_DIR` set to the same prepared
  components directory as the `suites/v1-scenarios` step of `v1-validation.yml`. No workflow was edited here.
