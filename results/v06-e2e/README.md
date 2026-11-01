# V06 end-to-end governed-effect qualification — retained evidence

Bounded synthetic local qualification. Not independent attestation; not a production security qualification. RELEASE / PUBLICATION / PRODUCTION: HOLD.

## Exact components exercised
| Component | Commit |
|---|---|
| Registry V01a | `943ab1831e39fadac1eb2a414ae322ccfa09bc6a` |
| Control Plane V02 | `1bee3696ee6cd8037d142cdbcdb6020e052b0480` |
| Runtime V05 | `4199a6c793cd9ec37a5fd451f7d99265dcf634fd` |
| Control Plane (intentionally older fixture, no successor profile) | `e66e5f163c5d5c112ff345a2f332b4c3893ee183` |

Environment: Python 3.13.17 locally (CI: 3.12), pydantic 2.14.1, PyNaCl 1.6.2, pytest 9.1.1 (hash lock `.github/locks/pydantic212-pynacl-pytest-v06.txt`).

## Local development executions (budget: 50 targeted case executions)
| Run | Cases | Result |
|---|---|---|
| 1 | d01 (pass), d02 (fail: harness defect, `python -I` ignored PYTHONPATH) | stopped by `-x`; its results file was overwritten by run 2 |
| 2 | 32 (all except d01) | 30 PASS, 2 FAIL (r01, r02: harness defect — racing connection was opened inside the held-lock stage hook) — `local-dev-runs/run-2-full-minus-d01/results.json` |
| 3 | r01, r02 | 2 PASS — `local-dev-runs/run-3-race-rerun/results.json`; contains the authority-transition ordering |
| **Total local executions** | | **36** (2 + 32 + 2) |

No single local run covered all 33 cases after the harness repairs: a clean full local run would have exceeded the 50-execution budget. The clean full run of all 33 cases is the GitHub Actions run of `e2e-governed-effect-v06.yml` (artifact `v06-e2e-evidence-<sha>`); its counts are reported separately in the PR and are not local executions.
No skipped case was counted as passed; the CI step fails on any SKIP.

## Known limits / unqualified boundaries
- Claims are built from the Control Plane's own models and `commitment`, and verified by them at provisioning. Issuance through the Control Plane workflow (`provision_local_execution_claim`) is NOT exercised: its fixtures use a different tenant, institution and domain than the Runtime's Registry fixtures. Control Plane V02's own suite covers issuance.
- The race is exercised with in-process stage hooks and a second SQLite connection, not an OS-level adversary; it shows the transition waits for the `BEGIN IMMEDIATE` lock and lands only after `after_commit`.
- Synthetic SQLite destination only; no real effect, network, credential, or external dispatch.
- The Runtime wrapper `worker21-authority-effect.yml` still calls the reusable workflow at its older pinned SHA; moving that pin is a Runtime-repository change outside this sprint.
- Python 3.12 only in CI for this workflow.
- Legacy compatibility on the older pin lives in its own reusable workflow (`cognous-execution-runtime--worker21-legacy-pin-compat.yml`) because the repo tooling (`tools/rc_env.py`) requires one checkout job per default recipe.
