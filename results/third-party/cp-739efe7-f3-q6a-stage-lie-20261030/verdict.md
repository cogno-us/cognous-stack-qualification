# verdict.md: Q6-A-S1-stage-lie-plain-journal (OCS-F3-Q240-FINAL-CLOSURE) at Control Plane 739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69

INDEPENDENCE FIRST (CA23): SUBORDINATE worker of the lead builder session, which also produced the F3-A readjudication, D-1, D-2 and the Q6 evidence. NOT independent; not organizational certification.

Binding (CA07): CP tree `1e7a7555eb3a956fcd2db21d3eb944169d0f7783` (src `d248bde4...`), verified before and after; Python 3.11.18 and 3.12.3 (freezes byte-identical to the Q6 freezes); Verifier `cogno-us/cognous-open-control-stack-verifier` `39d46b494558e271439966bec98b26dc4d040cc4` (fresh clone, clean; engine.py sha256 `633defffdf3ee3ee82c98dfe0d78cbb02dbbbb6a4f946394660a3ddfb3adf954`; UNPINNED lead choice). Protocol `PROTOCOL-Q6A-S1-v1.md` sha256 `04ff5530c81ababce363512691ca9dc16b02dd803d069982bb8bccbb2fcc2000`, frozen 2026-10-30T06:19:50Z; no registry pin; expectation not revised; no amendments.

## Result: EXPECTATION MET on both interpreters (first attempts, no reruns)
| Test id | 3.11.18 | 3.12.3 | Refutations recorded (diagnostic; not asserted) |
|---|---|---|---|
| test_stage_lie_is_refuted[journal] | PASS | PASS | `v2.journal.references / journal_stage_binding`; overall reject; 13 claim-stage rows rewritten |
| test_stage_lie_is_refuted[journal+operation-identity] (control) | PASS | PASS | `journal_stage_binding` plus `v2.profile.operation-identity / resolution_check_not_in_journal`; overall reject; 13 rows |
| test_unmutated_record_has_no_stage_binding_refutation[journal] (negative control) | PASS | PASS | none; overall abstain |
| test_unmutated_record_has_no_stage_binding_refutation[journal+operation-identity] (negative control) | PASS | PASS | none; overall abstain |
Raw: 4 passed, 0 skipped, 0 failed, 0 errors on 3.11.18 (`raw/Q6AS1-311`) and on 3.12.3 (`raw/Q6AS1-312`); gate NO_SKIP_PASS (min 4) on both; per-test outcomes identical across interpreters.

Established: on the plain-journal fixture (no fixture change), a claim record whose claim-stage check_events rows are rewritten to stage "decision" is refuted by the real Verifier engine (not mocked) at 39d46b4, by rule `journal_stage_binding`; the unmutated record has no such refutation; the same holds for the operation-identity control. This executes, for the first time, the stage-lie half that was unreachable behind the original test's skip.

## Adverse findings / observations
1. None against the expectation. No failure, skip or error.
2. Overall for the clean (unmutated) record is "abstain" on both params (not "pass"): from not-checkable inputs (identity/ledger manifest absent), per lead probe; the negative control asserts only "no journal_stage_binding refutation" and "not crashed", not a positive pass.
3. The mutation rewrites 13 rows; the refutation arises from rows now claiming stage "decision" while carrying a decision_id (rule `journal_stage_binding`). The original half-2 assertion is satisfied by ANY refuted check; the harness asserts exactly that and records which fired.
4. Cosmetic: `record_property` emits PytestWarning under junit xunit2 (properties were nonetheless written to junit.xml and read from there); harness not altered.
5. Verifier sha is unpinned; CP CI does not install it.

## What this does NOT establish
* Any statement about check-id linkage (not tested; per contract analysis not required on plain journal; not run or asserted here). The original `test_negative_incorrect_journal_linkage_is_detected[journal]` stays SKIPPED, unchanged.
* That 39d46b4 is the intended Verifier; any other Verifier sha or later HEAD; Verifier's own suite.
* Production behaviour: the plain-journal fixture uses the synthetic resolver test flag and test clock.
* Anything beyond Python 3.11.18/3.12.3, or any other CP revision.
* This is a successor case (separately named harness), not the original test passing.
