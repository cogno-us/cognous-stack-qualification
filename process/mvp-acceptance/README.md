# mvp-acceptance (proposed)

An independently owned Qualification job that runs the complete selected MVP route at the exact candidate tuple and applies a gate.
Everything here is **proposed**: Qualification owns the oracle and every verdict, the builder only proposes. Nothing is an acceptance, a
release decision or a production claim; release stays HOLD, and the gate verdict document says `authorizes: false`.

| File | Role |
|---|---|
| [`candidate-identity.inputs.json`](candidate-identity.inputs.json) | The only source of the tuple: eight components, each a full 40-hex sha. Exchange is listed only under `excluded_components`. |
| [`mandatory-battery.proposed.v1.json`](mandatory-battery.proposed.v1.json) | The frozen-candidate list of mandatory tests (50) and the skip rule. |
| [`gate-expectations.proposed.v1.json`](gate-expectations.proposed.v1.json) | Exact Verifier dispositions and environment floor. |
| [`mvp-applicability.proposed.v1.json`](mvp-applicability.proposed.v1.json) | Route C (Exchange) EXCLUDED and NOT INVOKED, with the checks that verify it. |
| [`../../.github/workflows/mvp-acceptance.yml`](../../.github/workflows/mvp-acceptance.yml) | Dispatch-only workflow (Python 3.13, pydantic 2.13.5 from the hash lock). |
| [`../../tools/mvp_acceptance_gate.py`](../../tools/mvp_acceptance_gate.py) | `resolve`, `verify-checkouts`, `gate` (standard library only); tests in `tests/test_mvp_acceptance_gate.py`. |

## What the job runs

Real claim provisioning (journal mode, operation identity), actual route B synthetic execution, grant and approval revocation negatives
(NC1), lost-acknowledgement and duplicate-operation negatives (NC2, NC3, and the ruling 4 assertions), Replay and Evidence Pack
reconstruction, the pinned Verifier, custody and tamper checks (NC5, NC6), the trusted-host ingress boundary (NC4, as uid 65534) and the
route C exclusion checks. The chain, negatives and Verifier come from `suites/mvp-chain` (its expectations v3 are the oracle and are not
changed); `suites/mvp-d2-route-b` and `suites/mvp-d09` are not in this job because they hard-code the Runtime sha and one of them fails by
design; the same behaviours are exercised here by mvp-chain.

## Tuple

`tools/mvp_acceptance_gate.py resolve` reads the identity file, applies per-component `workflow_dispatch` inputs (each validated as 40-hex lower
case; branches, tags and short shas are refused), and writes the resolved pin file the suites read plus `tuple-resolved.json`. `verify-checkouts`
requires each checkout to be at exactly its sha and pristine before any test runs, and the gate compares the heads the suite saw. To run
the post-F3 Runtime later, pass `runtime_revision` (or replace the one `runtime` value in the identity file); no other file changes.

## Gate verdicts

`INCOMPLETE` over `REJECT` over `ACCEPT`.

* **Zero unexplained skips inside the mandatory battery.** A listed test that is skipped (including xfail), not discovered (absent from
  `pytest --collect-only`), not executed (absent from the junit report), errored, or whose oracle row is `BLOCKED` or `NOT RUN` makes the
  verdict `INCOMPLETE`. `NOT APPLICABLE` counts only when the row id is listed under `declared_not_applicable` with a justification (empty
  today); any other `NOT APPLICABLE` is `INCOMPLETE`. A declared `NOT APPLICABLE` is a different thing from a skip. Tests outside the list
  (historical suites, KL-01) are not required to be skip-free.
* **Exact Verifier dispositions** (G-07), re-read from the retained report bytes (sha256 must match the run's record): run B exits 3
  (abstain), 28 checks, 27 confirmed, 1 could-not-check (`v4.ledger.rows-agree-with-attempts`), 0 refuted; V4 has 4 confirmed, 1 abstained
  and 2 not applicable (`v4.ledger.acknowledged-attempts-have-rows`, `v4.ledger.observations-agree`). Run A (no ledger) exits 3 with 29 checks,
  22 confirmed, 7 could-not-check (all `input_absent`). Nothing is asserted as "all other V4 checks pass".
* A changed expectation v1, v2 or v3 is a `REJECT` (G-02); the gate never edits one.
* A `FAIL` row is a `REJECT`; the job fails unless the gate says `ACCEPT`.

At the current tuple the oracle itself records known failures (for example NC1-04, approval revocation is reversible at the Runtime); the
gate does not soften them, so a run is expected to be non-ACCEPT until the owner's corrections land.

## Binding, anchoring and limits

* **Run binding.** `resolve` records the Qualification commit actually run (`git rev-parse HEAD` after checkout) and a fresh `run_id`
  (exported as `MVP_RUN_ID`). `results.json`, `observations.json`, each exclusion observation, the ingress module dump and each junit
  `testsuite` name must carry that run id, and the gate fails closed (INCOMPLETE) otherwise. The Verifier exit code and overall are
  re-derived from the retained report bytes; a malformed report is INCOMPLETE, never a crash. The artifact is named with the Qualification
  commit. `qualification_revision` is validated as 40-hex before it is used as a checkout ref, and the pristine check includes ignored files.
* **Frozen-file anchor.** The workflow reads the git blob ids of expectations v1-v3 and `test_scn_d09.py` on `main` through the REST API
  and the gate (G-02c) requires this checkout's blobs to be identical, in addition to the recorded sha256 values. Limit: that proves
  identity with the content `main` holds now, not an owner approval; protecting `main` (CODEOWNERS or branch rules) is what freezes it.
* **Exchange exclusion scope (AP-06).** Covered: the pytest processes that run the battery and the pinned ingress server process (its loaded
  modules are written at exit by `suites/mvp-applicability/plugin/ingress_probe/sitecustomize.py`, which `suites/mvp-chain/_ingress.py` puts on
  the server's PYTHONPATH; observation only). Not covered: other processes the battery starts, such as the Verifier CLI.
* **Out of scope observation.** `mvp-chain.yml` on main sets up Python 3.12; this job uses 3.13 as ruling 8 requires.

## Not run here

The workflow has not been dispatched from this change; the gate logic is covered by `tests/test_mvp_acceptance_gate.py` on synthetic
artifacts, and the ruling 4 and applicability tests were checked for syntax and (for the applicability tests) against the pinned hub
ingress sources.
