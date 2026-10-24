# Manual exact-manifest execution runbook (PROPOSED, builder-prepared)

Purpose: run the SAME battery as the `mvp-acceptance` workflow by hand when the workflow cannot be dispatched (it is not on Qualification main) or no hosted/qualifying host exists. Non-authorizing; UNQUALIFIED; release and production HOLD. Output label while no authorized independent owner exists: **Candidate testing complete or partially complete; independent adjudication pending.**

## Inputs to fix before running (write them into the run record)
1. Qualification commit (40-hex) and `candidate-commitment.proposed.v4.json` sha256, supplied from outside the checkout.
2. `process/mvp-acceptance/candidate-identity.inputs.json` (tuple and `composite` block) and its sha256.
3. Expectation hashes: `unchanged_files_sha256` in `mandatory-battery.proposed.v1.json` (v1-v3, v6, v7 in force).
4. Python 3.13 with `pip install --require-hashes -r .github/locks/cryptography-pydantic-pytest-a9a750.txt`; record `python -VV` and `pip freeze`.

## Steps
1. Clone each component at exactly its tuple sha into its own directory (`git clone`, `git checkout <sha>`), then `git clean -fdx` each; verify `git rev-parse HEAD` and `git status --porcelain --ignored` empty. Record the heads. Hub: tree ids of `tools/mvp_ingress` and `tools/mvp_env_record` (`git rev-parse HEAD:<path>`).
2. Resolve and verify: `python tools/mvp_acceptance_gate.py resolve ...` then `verify-checkouts` (writes `tuple-resolved.json` including `composite_verified`).
3. Export the `MVP_*_DIR` / `MVP_*_REVISION` variables, `MVP_RUN_ID`, `MVP_QUALIFICATION_SHA`, `MVP_RESULTS_DIR=<empty run dir>`. Profile: `MVP_INGRESS_PROFILE` unset on a qualifying host; `developer-optout` only where no distinct identities exist (the run is then supplementary and the host layer stays INCOMPLETE).
4. Collect, then run, each invocation separately with `-p no:cacheprovider` and `PYTHONDONTWRITEBYTECODE=1`: `suites/mvp-chain` (all files), `suites/mvp-applicability`, and the `d2-route-b` invocation (needs `D2_CONTROL_PLANE_DIR`, `D2_RUNTIME_DIR`, `D2_CONTROL_PLANE_PIN`) with `--collect-only -q` output saved as `collected-<invocation>.txt`, `--junitxml=junit-<invocation>.xml`, pytest exit status saved as `pytest-exit-<invocation>.txt`; `git clean -fdx` the component checkouts between runs. The exact paths per invocation are in the battery `invocations` and in `.github/workflows/mvp-acceptance.yml`.
5. Run the gate: `python tools/mvp_acceptance_gate.py gate --run-dir <dir> --expect-commitment <sha256> --expect-qualification <sha> --require-python 3.13 ...`; keep `gate-verdict.json` unedited.

## Preserve (with a sha256 manifest `SHA256SUMS` over everything)
source identities (`tuple-resolved.json`, heads, tree ids), expectation hashes, full console logs, raw results (`results.json`, `observations.json`, junit, collected lists, exit files), environment record and envelope (or the statement that none exists), Verifier reports, ingress module dump, the gate verdict, and `python -VV` / `pip freeze`. Never edit an expectation, the battery or the gate to change a result; a failing or skipped mandatory test stays failing or INCOMPLETE.

## Report
Use `report-template.proposed.md` (four separated layers; no aggregated NC4 PASS).
