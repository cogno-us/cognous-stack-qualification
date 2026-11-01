# verdict.md: Q6 successor (OCS-F3-Q240-FINAL) at Control Plane 739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69

INDEPENDENCE FIRST (CA23): this is the result of a SUBORDINATE worker of the lead builder session, which also produced the F3-A readjudication, D-1 and D-2. It is NOT independent of the lead builder and is not organizational certification.

Binding (CA07): CP tree `1e7a7555eb3a956fcd2db21d3eb944169d0f7783` (src `d248bde4...`), Python 3.11.18 and 3.12.3 (identical freezes, equal to D-2's), Verifier `cogno-us/cognous-open-control-stack-verifier` `39d46b494558e271439966bec98b26dc4d040cc4` (UNPINNED lead choice, not recorded by CP), format module blob `231b5557922d97dbf792bab93ee6173c89ec042b`, Registry `943ab1831e39fadac1eb2a414ae322ccfa09bc6a` for case C only. Protocol `PROTOCOL-Q6-SUCCESSOR-v1.md` sha256 `25b076db6a2220926af76314ceb7415e7358e59a2a42bb5c9fb1f07ca796ea30`, frozen 2026-10-30T04:30:17Z; first candidate execution 2026-10-30T04:30:2xZ. Expectations were not revised; no amendments were needed (`amendments/` empty).

## Summary (raw counts, per interpreter; first attempts, no reruns)
| Case | Expectation (frozen) | 3.11.18 | 3.12.3 | Met? | Gate |
|---|---|---|---|---|---|
| Q6-A `tests/test_claim_journal_stage.py`, Verifier on path | 14 pass, 0 skipped | 13 passed, 1 skipped, 0 failed | 13 passed, 1 skipped, 0 failed | NO (skip clause) | NOT_RUN (skip counted as not-run) |
| Q6-A0 control, no Verifier | module skipped at import | 1 skipped (exit 5) | 1 skipped (exit 5) | yes | NOT_RUN |
| Q6-B0 control, ORIGINAL format-module test | skips | 1 skipped | 1 skipped | yes | NOT_RUN |
| Q6-B successor copy, format module blob 231b555 | 1 pass, 0 skipped | 1 passed | 1 passed | yes | NO_SKIP_PASS |
| Q6-C `tests/test_v02_claim_policy_binding.py` ORIGINAL at Registry 943ab18 ("Q6-C-successor-pin") | 95 pass, 0 skipped | 95 passed | 95 passed | yes | NO_SKIP_PASS |
Per-test outcomes by test id are identical on 3.11 and 3.12 in every case (junit comparison); timing differs only.

## Q6-A verdict: PARTIAL (13/14 executed and passed on both interpreters; 1 test NOT RUN; frozen expectation NOT MET)
* Observed (`raw/Q6A-311`, `raw/Q6A-312`): with the Verifier at 39d46b4 on `PYTHONPATH`, the module is no longer skipped as a whole. 13 tests PASS: `test_claim_stage_journal_is_distinct_and_bound`, `test_claim_record_has_no_journal_reuse_and_no_refutation_with_pinned_verifier`, `test_effect_after_claim_keeps_effect_stage_semantics`, `test_prepatch_call_pattern_is_refuted_as_journal_check_reused`, `test_negative_reused_check_ref_is_refuted`, `test_negative_missing_stage_identity_is_refused` (each for params `journal` and `journal+operation-identity`) and `test_negative_incorrect_journal_linkage_is_detected[journal+operation-identity]`.
* ADVERSE: `test_negative_incorrect_journal_linkage_is_detected[journal]` SKIPPED on both interpreters: `SKIPPED [1] tests/test_claim_journal_stage.py:154: check-id linkage is only recorded with operation identity/freshness (same as decision/effect paths)`. The frozen expectation "0 skipped" is therefore NOT MET and, per the acceptance criteria, this skip is reported as NOT RUN and not counted as a pass.
* Analysis (no fix attempted): the skip is an in-test conditional (`if not (flow[2]._identity or flow[2]._freshness): pytest.skip(...)`, test line 153-154) that fires before any Verifier call. It is independent of the Verifier version and of this environment, i.e. neither an environment mismatch nor a dependency-version issue: the plain-`journal` parameterization is deliberately not exercised by the builder's own test, so it would skip in CP CI too (if the Verifier were installed). Not an implementation counterexample: nothing failed. Consequence: incorrect check-id linkage / stage lying detection on the plain-journal route (without operation identity/freshness) is not covered by this test; only the `journal+operation-identity` route is.
* Negative control A0 (no Verifier on path): the whole module skips at line 19 ("could not import 'cognous_verify.engine'"), reproducing D-2, so the 13 passes are attributable to the Verifier being present.
* The tests that compare against the Verifier ran the REAL `engine.evaluate` / `engine.InputFile` (import origin verified on both interpreters: `raw/post-run-integrity.txt`); not mocked.
* Does NOT establish: that 39d46b4 is the Verifier the builder intended ("pinned Verifier": CP pins none; unpinned lead choice; no transfer to any other Verifier revision, including its later HEAD); anything about the Verifier's own correctness (its own test suite was not run); the plain-journal linkage-negative case; the repo-level CI (which does not install the Verifier); production behaviour.

## Q6-B verdict: RESOLVED ONLY AS A MODIFIED SUCCESSOR CASE; the ORIGINAL test remains NOT RUN
* Variants: exactly ONE (blob `231b5557922d97dbf792bab93ee6173c89ec042b`, sha256 `2fc671e6...628bb2`) across main f7a55e2a, f-a1-pin-installer dff08044 and every other branch containing the file; a single commit in all history (`env/format-module-variants.txt`). So the per-variant report is a single report; whether the builder's private worktree "runtime-installer" held exactly this content cannot be established here.
* Original test, unmodified (B0, `raw/Q6B0-311/312`): SKIPPED on both ("Runtime format module not present in this environment (INCONCLUSIVE, not a pass)"; `/home/claude/wt` still absent). It stays NOT RUN; nothing was placed at that path.
* Successor copy (B, `raw/Q6B-311/312`; file `harness/test_successor_pin_export_format_module.py` sha256 `53be2be0...f14`, diff `harness/successor-vs-original.diff` sha256 `763838f8...6dc`; ONLY `FORMAT_PATH` changed, to read `Q6_FORMAT_MODULE_PATH`): 1 passed, 0 skipped on both. I.e. with the module at blob 231b555, `fmt.payload_defect(active(...)["payload"]) is None` and `tuple(fmt.PAYLOAD_MEMBERS) == PAYLOAD_MEMBERS` (the CP 17-member payload) hold on the pristine CP.
* This is a MODIFIED SUCCESSOR CASE, not the original test, and it is only as strong as the original function body it copies byte-for-byte.
* Does NOT establish: that the original test passes anywhere; that the runtime's installer/consumer behaves correctly (only the format module's payload check was run); that blob 231b555 equals what the builder had in the runtime-installer worktree; behaviour for any other format-module revision (no other revision exists in history); the other 26 pin-export tests (green in D-2, not re-run).

## Q6-C verdict: RESOLVED for the file at its own pin (Q6-C-successor-pin)
* The ORIGINAL unmodified `tests/test_v02_claim_policy_binding.py` against a fresh detached Registry clone at `943ab1831e39fadac1eb2a414ae322ccfa09bc6a` (HEAD verified, clean, vector blob equal to the test's `VECTOR_BLOB`), `OCS_REGISTRY_PIN_DIR` set, PyNaCl 1.6.2 / cffi 2.1.1 / pycparser 3.12 equal to that checkout's `requirements-ed25519.lock.txt`: 95 passed, 0 skipped, 0 failed on 3.11.18 and on 3.12.3 (`raw/Q6C-311`, `raw/Q6C-312`). The 6 D-2 failures (a01..a06) were the file's own pin assertion against the supplied a40fe755; with the pin it asks for, they pass. The failure outputs in PR #245 (D-2 R05/R06) remain the historical record and are not rewritten.
* Identical to D-2's supplementary S1 (95/95); this is a fresh run, not a transfer.
* Does NOT establish: anything at Registry a40fe755 or any other pin for this file; that 943ab18 is the Registry the CP release is supposed to track (the file is in no CI step at 739efe7; the pin is the file's own); wheel-hash verification of PyNaCl (versions equal the lock, wheels were not reinstalled/hash-checked here); the Registry's own suites.

## Overall: are the D-2 Q6 gaps A, B, C resolved?
* Gap A: PARTIALLY resolved. The module-level skip is gone (13/14 executed and pass on both interpreters); 1 of 14 remains NOT RUN by the test's own design (the verifier-independent conditional skip). The Verifier sha is an unpinned choice.
* Gap B: resolved only for a modified successor case (1/1 pass on both interpreters, single variant); the original test remains NOT RUN (its hard-coded path is unobservable here).
* Gap C: resolved (95/95 at the file's own pin on both interpreters), conditional on running that file against 943ab18.
* The previous D-2 Q6 statement "PARTIALLY NOT RUN" therefore becomes: A partial, B successor-only, C resolved. No implementation counterexample was found in any executed case; no test failed.

## Applicability crosswalk
| Item | Transfers from D-2 / this package | Does not transfer |
|---|---|---|
| D-2 R05/R06 (506 passed, 6 failed, 2 skipped of 514, both interpreters) | Remains the historical first-attempt record; its 5 green files (391 + 26 tests) are not re-run here and are not re-asserted here | Nothing in this package overwrites or re-scores it |
| D-2 S1 (95/95 at 943ab18) | Q6-C reproduces it independently of that run (same pin, same result) | S1 is not used as evidence for C; C stands on `raw/Q6C-*` |
| Q6-A results | Bound to CP tree 1e7a7555..., Verifier 39d46b4, 3.11.18/3.12.3 | Any other CP revision (e.g. 8616d5f, main), any other Verifier sha, any other Python |
| Q6-B result | Bound to blob 231b555 + modified successor + the CP tree | The original test; other runtime revisions |
| 3.11 vs 3.12 | Per-test outcomes identical by id for the cases run here | Full suite; CI-gated Registry suites |
| Freeze | Dependency freezes equal D-2's (so D-2's interpreter-level statements are consistent) | Nothing about Python 3.13 or other platforms |

## Adverse findings and flags
1. Q6-A frozen expectation NOT MET (1 skip, in-test conditional); reported, not revised.
2. Verifier sha is an unpinned choice; CP at 739efe7 pins no Verifier; CP CI does not install it (recon, from D-2 and CP logs), so the CP builder CI skips this module; this package is the first program evidence that the module's tests execute.
3. B is a modified copy; the original cannot be run without creating the path `/home/claude/wt/runtime-installer/...` (deliberately not created).
4. The Verifier import and the format module come from a public repository fetched during recon (before the freeze); no network was used during execution.
5. Post-run `__pycache__` appeared in the CP copy and Verifier clone from an interpreter import check run without `PYTHONDONTWRITEBYTECODE` after the tree checks; removed, tree recomputed equal (`raw/post-run-integrity.txt`). No effect on any run (all runs had `PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider`).
6. Independence: subordinate of the lead builder session; same model family; no known written designation; same harness conventions as D-2. Technical result only.
