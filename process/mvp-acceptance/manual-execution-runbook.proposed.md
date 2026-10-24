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
4. Anchor, collect and run, mirroring the workflow steps exactly (the commands below are compared with `.github/workflows/mvp-acceptance.yml` by a test; `WS` is the checkout root, `CP` the Control Plane tuple sha, `MVP_RUN_ID` the `run_id` in `tuple-resolved.json`, `PYTHONDONTWRITEBYTECODE=1`, no `__pycache__` anywhere under the suites). The anchor needs `GH_TOKEN`; without it `anchor.json` is missing and G-02c is INCOMPLETE. The exchange exclusion plugin (`-p exchange_exclusion_plugin`, `MVP_EXCLUSION_TAG`) writes the `exchange-exclusion-*.json` files G-08 requires; the chain results must land under `results/mvp-acceptance/mvp-chain/` (`MVP_RESULTS_DIR`). The chain battery runs as root on a qualifying host (NC4 starts the ingress and the client as different dedicated uids). The d2 run needs `D2_CONTROL_PLANE_DIR` and `D2_RUNTIME_DIR`. `git clean -fdx` the component checkouts between runs.

```bash
export WS="$PWD" CP=<control-plane tuple sha> D2_CONTROL_PLANE_DIR="$PWD/components/control_plane" D2_RUNTIME_DIR="$PWD/components/runtime"
export MVP_RESULTS_DIR="$WS/results/mvp-acceptance/mvp-chain" PYTHONDONTWRITEBYTECODE=1
d=results/mvp-acceptance
python tools/mvp_acceptance_gate.py anchor --repo "$GITHUB_REPOSITORY" --ref main --out results/mvp-acceptance/anchor.json
MVP_RESULTS_DIR="$d/collect-mvp-chain" python -m pytest --collect-only -q -p no:cacheprovider suites/mvp-chain/test_mvp_chain.py suites/mvp-chain/test_verdict_engine.py suites/mvp-chain/test_ruling4_lost_ack.py suites/mvp-chain/test_kwflow.py suites/mvp-chain/test_ingress_ambiguity.py | tee "$d/collected-mvp-chain.txt"
D2_CONTROL_PLANE_PIN="$CP" MVP_RESULTS_DIR="$d/collect-d2-route-b" python -m pytest --collect-only -q -p no:cacheprovider suites/mvp-d2-route-b/test_inventory_negatives.py | tee "$d/collected-d2-route-b.txt"
MVP_RESULTS_DIR="$d/collect-applicability" python -m pytest --collect-only -q -p no:cacheprovider suites/mvp-applicability/test_route_c_exclusion.py | tee "$d/collected-applicability.txt"
MVP_EXCLUSION_TAG=mvp-chain sudo -E env "PATH=$PATH" "PYTHONPATH=$WS/suites/mvp-applicability/plugin" python -m pytest -q -p no:cacheprovider -p exchange_exclusion_plugin suites/mvp-chain/test_mvp_chain.py suites/mvp-chain/test_verdict_engine.py suites/mvp-chain/test_ruling4_lost_ack.py suites/mvp-chain/test_kwflow.py suites/mvp-chain/test_ingress_ambiguity.py -o junit_suite_name="mvp-acceptance-$MVP_RUN_ID-mvp-chain" --junitxml="$d/junit-mvp-chain.xml"
echo $? > "$d/pytest-exit-mvp-chain.txt"
D2_CONTROL_PLANE_PIN="$CP" MVP_EXCLUSION_TAG=d2-route-b MVP_RESULTS_DIR="$d/mvp-d2-route-b" PYTHONPATH="$WS/suites/mvp-applicability/plugin" python -m pytest -q -p no:cacheprovider -p exchange_exclusion_plugin suites/mvp-d2-route-b/test_inventory_negatives.py -o junit_suite_name="mvp-acceptance-$MVP_RUN_ID-d2-route-b" --junitxml="$d/junit-d2-route-b.xml"
echo $? > "$d/pytest-exit-d2-route-b.txt"
MVP_EXCLUSION_TAG=applicability PYTHONPATH="$WS/suites/mvp-applicability/plugin" python -m pytest -q -p no:cacheprovider -p exchange_exclusion_plugin suites/mvp-applicability/test_route_c_exclusion.py -o junit_suite_name="mvp-acceptance-$MVP_RUN_ID-applicability" --junitxml="$d/junit-applicability.xml"
echo $? > "$d/pytest-exit-applicability.txt"
```

5. Run the gate (the same flags as the workflow): `python tools/mvp_acceptance_gate.py gate --run-dir results/mvp-acceptance --expect-qualification-sha <sha> --expect-commitment-sha256 <sha256> --require-python 3.13 --components-dir "$WS/components"`; keep `gate-verdict.json` unedited.

## Preserve (with a sha256 manifest `SHA256SUMS` over everything)
source identities (`tuple-resolved.json`, heads, tree ids), expectation hashes, full console logs, raw results (`results.json`, `observations.json`, junit, collected lists, exit files), environment record and envelope (or the statement that none exists), Verifier reports, ingress module dump, the gate verdict, and `python -VV` / `pip freeze`. Never edit an expectation, the battery or the gate to change a result; a failing or skipped mandatory test stays failing or INCOMPLETE.

## Report
Use `report-template.proposed.md` (four separated layers; no aggregated NC4 PASS).
