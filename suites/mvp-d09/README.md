# mvp-d09: D09 supplement for the MVP tuple

Local builder evidence. Qualification owns the oracles and verdicts; nothing here declares acceptance or qualification.

- Content: `test_mvp_d09_exact_runtime.py` (12 cases). A widened static inventory of effect entry points (adds `workflow.execute(`, which finds the Control Plane `acp run` ingress, `cli_run.py`) and of the files that write the `effects` table (exactly two). It also runs negative controls on route B with operation identity: direct commit bypass (5 variants), legacy write refusal through the atomic marker (3), AgentEngine no-effect, and a supported-path control.
- Not covered: route C (the governed-exchange ingress), the OpenShell route, raw SQL by the database holder, forged claims via `provision_claim` / `execute_claim_atomic`, the `simulate` parameter and the authority writers. Route C is still exercised only by the original `suites/v1-scenarios/test_scn_d09.py`.
- No workflow runs this suite. There is no CI wiring; results are local runs only.
- It lives outside `suites/v1-scenarios` and has no `test_scn_d09` in its name so that the frozen V1 row SCN-D09 (selector `test_scn_d09`, min 32) matches only the original cases. `test_scn_d09.py` and all retained evidence are unchanged.
- Tuple: the runtime must be `ec728da6dc301a664b331ac8986afd6e850a1273`. The Control Plane may be `0a41faa9...` or `7a4bcd40...`. Admitting 7a4bcd40 here is only a harness allowance and does not qualify it. At 7a4bcd40 the original D09 suite shows 5 route C failures (`candidate source identity mismatch: agent_control_plane.bounded`).
- Run: `SCN_COMPONENTS_DIR=DIR python -m pytest -q -p no:cacheprovider suites/mvp-d09`, with DIR holding pristine checkouts named control_plane, runtime, replay, evidence_pack, odes, exchange and manifest, and pydantic >= 2.12 and jsonschema importable.
