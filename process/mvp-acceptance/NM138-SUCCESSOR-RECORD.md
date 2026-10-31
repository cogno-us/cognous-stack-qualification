# NM-138 successor candidate record (OCS-MVP-NM138-REPAIR)

PROPOSED, non-authorizing. Release, publication and production stay HOLD. Not independence, Q7, certification or Tier 1.

## Parent and historical result (unchanged, not superseded in place)
- Parent Qualification candidate: `fa12c699939880149ed3997cbc2b11b264b23acd` (merged `b6142518df02d30229df668ccc90f75c74e30609`), commitment v5 sha256 `814430869c63ab57cae091624c512bb119a3291e39e043827ae180ad59d3ca49`.
- Historical run: https://github.com/cogno-us/cognous-stack-qualification/actions/runs/41165743705, evidence branch `qgate-05/evidence-run-1` @ `ef407ca3c47de22af7cf901147baa5bad226e057`. Verdict REJECT stands: 47/47 oracle rows PASS, battery 434/435, NM-138 FAIL, G-06 FAIL.

## Defect and repair
- NM-138 (`suites/mvp-chain/test_nc4_03_host_subcases.py::test_developer_optout_can_never_be_pass`, mandatory, unchanged): `_nc4_03_host.sub_a_yama` returned PASS under `MVP_INGRESS_PROFILE=developer-optout` on a host with Yama ptrace_scope >= 1; the other three subcases pass through `_cap`. The module's own spec (docstring, `nc4_03_host_subcases.v1.json`) caps every optout status at BLOCKED.
- Repair (one function): `sub_a_yama` now returns `_cap(PASS, ctx.get("ratified", False), NOT_RATIFIED)` (fail closed: PASS only when the ratified approved profile was resolved). Approved profile: status, reason text and observed keys byte-for-byte as before (oracle row NC4-03a unchanged). An unresolved profile (unknown MVP_INGRESS_PROFILE or missing identities) is never ratified, so NC4-03a is BLOCKED there too (adversarial review finding MED, fixed before the freeze; the existing test only requires a valid status).
- Regression tests (outside the mandatory battery and the commitment scope, run by the repository CI): `tests/test_nm138_yama_cap_regression.py`, 17 cases with mocked Yama (absent, 0, 1, 2, 3; approved supported/unsupported; unknown-profile fail-closed). Result on the frozen source: 7 FAIL (the Yama >= 1 optout cases and the source guard); on the repaired source: 17 PASS. No kernel setting is read or changed.

## Successor plumbing (names only; no logic change)
One-shot branch names retargeted so the spent QGATE-05 names cannot be reused: run branch `nm138/run-1`, evidence branch `nm138/evidence-run-1`, hub custody branch `nm138/custody-1` (path `docs/mvp-recovery/nm138/custody/freeze-commitment.json`), concurrency group `nm138-run-1`, commitment file `candidate-commitment.proposed.v6.json` (gate `COMMITMENT_FILE`), `tools/qgate05_custody_check.py` CUSTODY_BRANCH, `tools/qgate05_evidence_commit.sh` branch guard, gate tests. The environment profile v2 still carries QGATE-05 trigger prose; it is a historical, unchanged, committed file and is not behaviour.

## Unchanged by construction
- Component tuple (`candidate-identity.inputs.json` sha256 `f806d42ddd814df1c6efe7d2c9989a0c60dda82332e5ace5a67d9acb091ae897`).
- Oracle v8 `498efc12fc1f608fb6fb53738ef61776cb576a70573f0644eb42a0f3e35f359c` (48 rows, 47 mandatory).
- Mandatory battery v2 `61228fad3d28aa9188e528ec8dbea3952308bdc8ad750d7d1628755f46e4d262` (435 mandatory entries; NM-138 retained mandatory; 7 non-mandatory tests; pending_rows empty).
- Commitment v5 file `814430869c63ab57cae091624c512bb119a3291e39e043827ae180ad59d3ca49` (never edited).
- No Control Plane, Runtime, Replay, Evidence Pack, ODES, Action Manifest, Verifier or pin change.
