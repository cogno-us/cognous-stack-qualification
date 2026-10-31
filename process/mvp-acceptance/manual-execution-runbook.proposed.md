# Manual exact-manifest execution runbook (PROPOSED, builder-prepared)

Purpose: run the SAME battery as the `mvp-acceptance` workflow by hand when the single authorized hosted run (QGATE-05: push to `qgate-05/run-1`, GitHub-hosted ubuntu-24.04, `run_attempt == 1`, no re-run path, evidence mirrored to the append-only branch `qgate-05/evidence-run-1`) cannot be used or no hosted/qualifying host exists. A manual run is NOT the authorized execution and its output is supplementary. In the workflow the three pytest groups below run concurrently in one job; by hand they may run one after another (the results are disjoint per group). Non-authorizing; UNQUALIFIED; release and production HOLD. Output label while no authorized independent owner exists: **Candidate testing complete or partially complete; independent adjudication pending.**

## Inputs to fix before running (write them into the run record)
1. Qualification commit (40-hex) and `candidate-commitment.proposed.v5.json` sha256, supplied from outside the checkout. In the hosted run both come from the hub custody record `docs/mvp-recovery/qgate-05/custody/freeze-commitment.json` (hub default branch); the workflow asserts `GITHUB_SHA == qualification_revision` and `sha256sum process/mvp-acceptance/candidate-commitment.proposed.v5.json == candidate_commitment_sha256` (`tools/qgate05_custody_check.py`) before any test runs, then hands the value to the gate as `--expect-commitment-sha256`. By hand, perform the same two comparisons yourself.
2. `process/mvp-acceptance/candidate-identity.inputs.json` (tuple and `composite` block) and its sha256.
3. Expectation hashes: `unchanged_files_sha256` in the battery file in force for commitment v5 (the amended battery and the oracle file named there; `process/mvp-chain/expectations.proposed.v7.json` stays byte-identical).
4. Python 3.13 with `pip install --require-hashes -r .github/locks/cryptography-pydantic-pytest-a9a750.txt`; record `python -VV` and `pip freeze`.

## Steps
0. Prerequisites: at least 2 GB free disk (the tracked `results/` tree alone is about 928 MB); Python 3.13 as above; `git`, `sudo`. `git clean -fdx` at the Qualification root is forbidden (it deletes `results/` and `components/`).
1. Clone each component at exactly its tuple sha into `components/<dir>` (`git clone <repository> components/<dir>`, `git -C components/<dir> checkout <sha>`), then `git -C components/<dir> clean -fdx`; verify `git rev-parse HEAD` and `git status --porcelain --ignored` empty. Directory and repository per component: `control_plane` (cogno-us/cognous-control-plane), `runtime` (cogno-us/cognous-execution-runtime), `replay` (cogno-us/cognous-replay-bundle), `evidence_pack` (cogno-us/cognous-governance-evidence-pack), `odes` (cogno-us/open-decision-evidence-standard), `verifier` (cogno-us/cognous-open-control-stack-verifier), `manifest` (cogno-us/cognous-action-manifest), `hub` (cogno-us/cognous-open-control-stack). Record the heads and, for the hub, the tree ids of `tools/mvp_ingress` and `tools/mvp_env_record` (`git rev-parse HEAD:<path>`). Then mark the checkouts safe, as the workflow does:

```bash
git config --global --add safe.directory '*'
sudo git config --global --add safe.directory '*'
```

2. Resolve, preflight the hub capture script and verify (the same commands as the workflow, in the same order; `resolve` writes the run-scoped variables, including `MVP_RUN_ID`, to the file named by `--github-env`, which you MUST then source). `verify-checkouts` writes `tuple-resolved.json` including `composite_verified`:

```bash
export WS="$PWD" GITHUB_OUTPUT="$PWD/results/gh-output.txt" GITHUB_ENV="$PWD/results/gh-env.txt"
mkdir -p results/mvp-acceptance/mvp-chain
python3 tools/mvp_acceptance_gate.py resolve --identity process/mvp-acceptance/candidate-identity.inputs.json --out-pin results/mvp-acceptance/tuple-pin.resolved.json --out-resolved results/mvp-acceptance/tuple-resolved.json --github-output "$GITHUB_OUTPUT" --github-env "$GITHUB_ENV" --qualification-sha "$(git rev-parse HEAD)"
set -a; . "$GITHUB_ENV"; set +a
python3 tools/mvp_acceptance_gate.py preflight-hub --components-dir "$WS/components"
python tools/mvp_acceptance_gate.py verify-checkouts --resolved results/mvp-acceptance/tuple-resolved.json --base "$WS"
```

3. Profile. On a qualifying host provision the approved profile exactly as the workflow does, with the helper (needs passwordless sudo; it creates only throwaway accounts and `/var/lib/qgate05-ocs`, makes the workspace readable for the ingress uid, and changes NO sysctl, Yama or ACL setting; it records the host under `results/mvp-acceptance/host-evidence/`):

```bash
bash tools/qgate05_host_setup.sh provision "$WS" "$WS/results/mvp-acceptance/host-evidence"
cat /proc/sys/kernel/yama/ptrace_scope || true
export MVP_INGRESS_PROFILE=approved MVP_INGRESS_USER=mvp-ingress MVP_CLIENT_USER=mvp-client MVP_IPC_GROUP=mvp-ipc
export MVP_QUALIFICATION_SHA="$(git rev-parse HEAD)" QG5_BASE=/var/lib/qgate05-ocs QG5_TMP=/var/lib/qgate05-ocs/tmp QG5_DURABLE_DIR=/var/lib/qgate05-ocs/durable
```

The helper refuses if uid 65533 (the outsider probe uid) is allocated or `/var/lib/qgate05-ocs` exists. `kernel.yama.ptrace_scope` is recorded as found: below 1 (or absent) the boundary test is BLOCKED and the verdict INCOMPLETE; nothing weaker is substituted. The IPC directory (setgid, group `mvp-ipc`, **mode 2751**) is created by `suites/mvp-chain/_ingress.py`; 2751 is the **bounded synthetic test profile** ratified by Architect D3 (socket 0660, peer-UID allowlist), not a production setting; the accepted residual is that an outsider can stat a known socket name. Where no distinct identities exist, skip provisioning and export `MVP_INGRESS_PROFILE=developer-optout` instead (the run is then supplementary and the host layer stays INCOMPLETE).

4. Anchor, collect and run, mirroring the workflow steps exactly (the commands below are compared with `.github/workflows/mvp-acceptance.yml` by a test; `WS` is the checkout root, `CP` the Control Plane tuple sha, `MVP_RUN_ID` the `run_id` in `tuple-resolved.json`, `PYTHONDONTWRITEBYTECODE=1`, no `__pycache__` anywhere under the suites). The anchor needs `GH_TOKEN`; without it `anchor.json` is missing and G-02c is INCOMPLETE. The exchange exclusion plugin (`-p exchange_exclusion_plugin`, `MVP_EXCLUSION_TAG`) writes the `exchange-exclusion-*.json` files G-08 requires; the chain results must land under `results/mvp-acceptance/mvp-chain/` (`MVP_RESULTS_DIR`). The chain battery runs as root on a qualifying host (NC4 starts the ingress and the client as different dedicated uids). `MVP_ACCEPTANCE_DIR` is exported as in the workflow so the exclusion plugin's `exchange-exclusion-*.json` land directly under `results/mvp-acceptance/` (G-08). The environment exports below are compared with the workflow job `env:` by a test. The d2 run needs `D2_CONTROL_PLANE_DIR` and `D2_RUNTIME_DIR`. Between runs `git clean -fdx` only INSIDE each `components/<dir>` checkout, NEVER at the Qualification root: that would delete `results/` and `components/` (and `results/` is tracked, about 928 MB).

```bash
export WS="$PWD" CP=<control-plane tuple sha>
export GITHUB_REPOSITORY=cogno-us/cognous-stack-qualification GH_TOKEN=<read-only token for the anchor>
export MVP_CP_DIR="$WS/components/control_plane" MVP_RUNTIME_DIR="$WS/components/runtime" MVP_REPLAY_DIR="$WS/components/replay" MVP_PACK_DIR="$WS/components/evidence_pack"
export MVP_ODES_DIR="$WS/components/odes" MVP_VERIFIER_DIR="$WS/components/verifier" MVP_MANIFEST_DIR="$WS/components/manifest" MVP_HUB_DIR="$WS/components/hub"
export MVP_PIN_FILE="$WS/results/mvp-acceptance/tuple-pin.resolved.json" MVP_ACCEPTANCE_DIR="$WS/results/mvp-acceptance" MVP_RESULTS_DIR="$WS/results/mvp-acceptance/mvp-chain"
export MVP_IDENTITY_FILE="$WS/process/mvp-acceptance/candidate-identity.inputs.json" D2_CONTROL_PLANE_DIR="$WS/components/control_plane" D2_RUNTIME_DIR="$WS/components/runtime"
export PYTHONDONTWRITEBYTECODE=1
# approved profile on a qualifying host (the workflow's provisioning step): dedicated users and group, then
export MVP_INGRESS_PROFILE=approved MVP_INGRESS_USER=mvp-ingress MVP_CLIENT_USER=mvp-client MVP_IPC_GROUP=mvp-ipc
d=results/mvp-acceptance
python tools/mvp_acceptance_gate.py anchor --repo "$GITHUB_REPOSITORY" --ref main --out results/mvp-acceptance/anchor.json
MVP_RESULTS_DIR="$d/collect-mvp-chain" python -m pytest --collect-only -q -p no:cacheprovider suites/mvp-chain/test_mvp_chain.py suites/mvp-chain/test_verdict_engine.py suites/mvp-chain/test_ruling4_lost_ack.py suites/mvp-chain/test_kwflow.py suites/mvp-chain/test_ingress_ambiguity.py suites/mvp-chain/test_process_kill_a1.py suites/mvp-chain/test_ledger_pruning_a2.py suites/mvp-chain/test_nc4_03_mutation_set.py suites/mvp-chain/test_nc4_03_host_subcases.py | tee "$d/collected-mvp-chain.txt"
D2_CONTROL_PLANE_PIN="$CP" MVP_RESULTS_DIR="$d/collect-d2-route-b" python -m pytest --collect-only -q -p no:cacheprovider suites/mvp-d2-route-b/test_inventory_negatives.py | tee "$d/collected-d2-route-b.txt"
MVP_RESULTS_DIR="$d/collect-applicability" python -m pytest --collect-only -q -p no:cacheprovider suites/mvp-applicability/test_route_c_exclusion.py | tee "$d/collected-applicability.txt"
MVP_EXCLUSION_TAG=mvp-chain sudo -E env "PATH=$PATH" "PYTHONPATH=$WS/suites/mvp-applicability/plugin" "TMPDIR=$QG5_TMP" "QG5_DURABLE_DIR=$QG5_DURABLE_DIR" python -m pytest -q -p no:cacheprovider -p exchange_exclusion_plugin suites/mvp-chain/test_mvp_chain.py suites/mvp-chain/test_verdict_engine.py suites/mvp-chain/test_ruling4_lost_ack.py suites/mvp-chain/test_kwflow.py suites/mvp-chain/test_ingress_ambiguity.py suites/mvp-chain/test_process_kill_a1.py suites/mvp-chain/test_ledger_pruning_a2.py suites/mvp-chain/test_nc4_03_mutation_set.py suites/mvp-chain/test_nc4_03_host_subcases.py -o junit_suite_name="mvp-acceptance-$MVP_RUN_ID-mvp-chain" --junitxml="$d/junit-mvp-chain.xml"
echo $? > "$d/pytest-exit-mvp-chain.txt"
D2_CONTROL_PLANE_PIN="$CP" MVP_EXCLUSION_TAG=d2-route-b MVP_RESULTS_DIR="$d/mvp-d2-route-b" PYTHONPATH="$WS/suites/mvp-applicability/plugin" python -m pytest -q -p no:cacheprovider -p exchange_exclusion_plugin suites/mvp-d2-route-b/test_inventory_negatives.py -o junit_suite_name="mvp-acceptance-$MVP_RUN_ID-d2-route-b" --junitxml="$d/junit-d2-route-b.xml"
echo $? > "$d/pytest-exit-d2-route-b.txt"
MVP_EXCLUSION_TAG=applicability PYTHONPATH="$WS/suites/mvp-applicability/plugin" python -m pytest -q -p no:cacheprovider -p exchange_exclusion_plugin suites/mvp-applicability/test_route_c_exclusion.py -o junit_suite_name="mvp-acceptance-$MVP_RUN_ID-applicability" --junitxml="$d/junit-applicability.xml"
echo $? > "$d/pytest-exit-applicability.txt"
```

5. Run the gate (the same flags as the workflow): `python tools/mvp_acceptance_gate.py gate --run-dir results/mvp-acceptance --expect-qualification-sha <sha> --expect-commitment-sha256 <sha256 of candidate-commitment.proposed.v5.json from the custody record> --require-python 3.13 --components-dir "$WS/components"`; keep `gate-verdict.json` unedited. Then `python3 tools/qgate05_summarize.py --run-dir results/mvp-acceptance` (read-only; keeps PASS / FAIL / BLOCKED / ABSTAIN counts as distinct categories).

## Capture and preserve
Record the console of the whole run (for example start `script -q -f results/mvp-acceptance/console.log` before step 2 and `exit` after step 5) and the toolchain, then build the manifest last:

```bash
python -VV | tee results/mvp-acceptance/python-version.txt
python -m pip freeze > results/mvp-acceptance/pip-freeze.txt
(cd results/mvp-acceptance && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
```

## Preserve (with the sha256 manifest `SHA256SUMS` over everything)
source identities (`tuple-resolved.json`, heads, tree ids), expectation hashes, full console logs, raw results (`results.json`, `observations.json`, junit, collected lists, exit files), environment record and envelope (or the statement that none exists), Verifier reports, ingress module dump, the gate verdict, and `python -VV` / `pip freeze`. Never edit an expectation, the battery or the gate to change a result; a failing or skipped mandatory test stays failing or INCOMPLETE.

## Report
Use `report-template.proposed.md` (four separated layers; no aggregated NC4 PASS).

## Hosted run: trigger, custody and evidence channel (QGATE-05, PROPOSED)

* **Trigger.** `push` to the one-purpose branch `qgate-05/run-1` only (the Actions API is not reachable from the lead's environment). `run_attempt == 1` guard on both jobs, no `workflow_dispatch`, no re-run path; the run refuses to start if `qgate-05/evidence-run-1` already exists. The branch must never be pushed again after the first push. The runner is `ubuntu-24.04`.
* **Custody.** The workflow embeds neither the commitment sha256 nor the qualification revision (the commitment covers the workflow file). Order of operations for the lead: freeze the candidate commit X (with `candidate-commitment.proposed.v5.json`), compute its sha256, commit the custody record `{"schema":"cognous.qgate05-freeze-commitment/1","qualification_revision":"<X>","candidate_commitment_sha256":"<sha256>"}` to the hub default branch at `docs/mvp-recovery/qgate-05/custody/freeze-commitment.json`, and only then push X to `qgate-05/run-1`. The run records the resolved hub commit in `custody-evidence.json`.
* **Evidence.** (a) GitHub artifact `qgate05-run1-evidence` (whole `results/mvp-acceptance`, 90 days); (b) the evidence job appends `runs/run-<run_id>-attempt-<n>/` to the append-only branch `qgate-05/evidence-run-1` of the Qualification repository (`tools/qgate05_evidence_commit.sh`; `contents: write` in that job only; explicit refspec; never main; never force; `SHA256SUMS` over every committed file; files above 95 MB are listed in `OMITTED-LARGE-FILES.txt` and stay in the artifact). Read it with `git fetch origin qgate-05/evidence-run-1`.
* **Not a claim.** The run is non-authorizing and claims no independence, certification, Q7, Tier 1 or release/production readiness. Permitted claim (Q14): the frozen pinned classes compose end-to-end in the qualification harness, while the trusted ingress boundary is separately exercised on the real socket under the same frozen candidate. A live socket request did NOT produce the reconstructed Replay, Evidence Pack and Verifier evidence.
