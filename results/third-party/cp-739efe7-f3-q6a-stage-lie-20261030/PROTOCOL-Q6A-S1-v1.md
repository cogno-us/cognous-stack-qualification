# PROTOCOL-Q6A-S1-v1 (work package OCS-F3-Q240-FINAL-CLOSURE, case Q6-A-S1-stage-lie-plain-journal)

Author/executor: execution worker, a SUBORDINATE agent of the lead builder session, which also produced the F3-A readjudication, D-1, D-2 and the Q6 evidence. NOT independent of the lead builder (CA23). Rules: CA04 (this protocol and its expectation are frozen before candidate execution and never revised after), CA06 (all raw output and first attempts retained; amendments append-only), CA07 (exact source/dependency/interpreter binding), CA08 (not certification). No production edit; no edit to any original test file; no paid calls; no broad suites; nothing committed; no PR.

## 1. Scope
One successor case, separately named `Q6-A-S1-stage-lie-plain-journal`. It executes ONLY the STAGE-LIE half of the original `tests/test_claim_journal_stage.py::test_negative_incorrect_journal_linkage_is_detected`, which was skipped on the plain `journal` parameter in the Q6 successor evidence (13 passed / 1 skipped) and was never executed on that route anywhere. It does NOT test, assert or evaluate check-id linkage (contract analysis `q6a-contract.md`: linkage is an operation-identity feature, not required on a plain journal).

## 2. Subject and environment (CA07)
* CP `739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69` via `git archive | tar -x` into NEW dir `/tmp/claude-0/work/q6a/src/cp-739efe7`; tree id recomputed from files before: `1e7a7555eb3a956fcd2db21d3eb944169d0f7783` (src `d248bde478ae3f2ce050db4637f0c1203066e906`) (`env/cp-tree-before.txt`); recomputed again after all runs. Equals the expected id.
* Verifier: FRESH clone of `cogno-us/cognous-open-control-stack-verifier` detached at `39d46b494558e271439966bec98b26dc4d040cc4` (tree `22bb9a848e59ad56f2a737003071135818fffd89`, clean); `src/cognous_verify/engine.py` sha256 `633defffdf3ee3ee82c98dfe0d78cbb02dbbbb6a4f946394660a3ddfb3adf954`; per-file hashes `env/verifier-src-files.sha256`. Stdlib only; used via PYTHONPATH; never mocked. UNPINNED lead choice (CP records no Verifier pin).
* Interpreters: Python 3.11.18 `/tmp/claude-0/work/venv311`; Python 3.12.3 `/tmp/claude-0/work/d2/venv312`. `pip freeze` of each byte-identical to the Q6 successor freezes (`env/freeze-py311.txt`, `env/freeze-py312.txt`; also identical to each other). No package installed or changed.
* Env: `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`; `OCS_REGISTRY_PIN_DIR`/`OCS_REQUIRE_REGISTRY_PIN` unset (no Registry pin: confirmed by a collection-only smoke on both interpreters that imports the module and CP helpers without it, `raw/prefreeze-collect-311.txt`, `-312.txt`).
* Network: used only for the Verifier clone, before freeze; none during execution.

## 3. Harness (reuse by import, no copy)
`harness/test_successor_q6a_stage_lie.py` imports the ORIGINAL module's `flow` fixture, `_claim`, `_verify`, `_refutations` via `from tests.test_claim_journal_stage import ...` from the pristine CP copy. No helper is copied; nothing is changed in the original. The fixture supplies exactly two parameters: `journal` (plain; no opt-ins; synthetic resolver test flag as in `tests/test_runtime_authority.py::setup_flow`) and `journal+operation-identity` (LABELLED CONTROL; same stage-lie assertion). Tests (each x2 params = 4 test ids):
* `test_stage_lie_is_refuted[journal]`, `[journal+operation-identity]`: build record with `_claim(flow)`; `copy.deepcopy`; rewrite EVERY `check_events` entry with `stage == "claim"` to `"decision"` (precondition: at least one rewritten); then assert `any(c.verdict == "refuted" for c in _verify(bad2).checks)` (original half-2 assertion verbatim). The refutation set and overall are recorded as junit properties (diagnostic only, not asserted).
* `test_unmutated_record_has_no_stage_binding_refutation[journal]`, `[journal+operation-identity]` (NEGATIVE control): unmutated `_claim` record; asserts not crashed and no refuted finding with code `journal_stage_binding` in `_refutations(_verify(rec))`.
No check_id linkage assertion exists anywhere in the harness.
Runner `harness/run_q6a_s1.sh <311|312> <label>`; gate `harness/assert_noskip.py` (D-2 final gate, copied unchanged from the Q6 evidence) with `--min 4`. Command per run: `python -m pytest -p no:cacheprovider -q -rA --junitxml=<raw>/junit.xml harness/test_successor_q6a_stage_lie.py`, cwd = CP copy.

## 4. EXPECTATION (frozen, stated in advance)
On BOTH 3.11.18 and 3.12.3: 4 passed, 0 skipped, 0 failed, 0 errors; gate NO_SKIP_PASS (min 4). I.e.: the stage-lie case is refuted for `[journal]` and for the `[journal+operation-identity]` control; the unmutated negative control has no `journal_stage_binding` refutation on either param. Per-test outcomes identical across interpreters. (Basis: lead probe `q6a-contract.md` reproduced refutation `v2.journal.references / journal_stage_binding`, overall reject, on plain journal; that probe was not a run of this harness.)

## 5. Acceptance criteria and stop conditions
Accept (case resolved) iff the expectation is met on both interpreters, no skip counted as pass, all raw retained, SHA256SUMS verifies. If an outcome differs: preserve raw verbatim, report adverse, DO NOT change the expectation or the harness test bodies; harness defects (runner/gate/path only) only via dated append-only amendments in `amendments/`, first attempt remains. Stop (no run) if CP tree id, Verifier HEAD or engine.py sha256 mismatch the recorded values at run time (a pre-run check is in the runner session and recorded in `raw/pre-run-integrity.txt`); stop on need for network or write outside the evidence/scratch dirs.

## 6. What this does NOT establish
* Nothing about check-id linkage on a plain journal (not tested; contract says not required there; a zeroed resolution check id is not refuted by the Verifier at this sha per the lead probe, but this package does not run or assert it).
* Not an assertion that Verifier 39d46b4 is the intended/pinned Verifier (CP pins none); holds for that sha only; no transfer to other Verifier revisions or later HEAD; Verifier's own correctness/test suite not run.
* The plain-journal baseline fixture uses the synthetic resolver test flag (`allow_synthetic_resolver=True`, test clock); it shows the Verifier refutes the mutation on that fixture's record, not production behaviour.
* The refutation need only be by ANY check (original semantics); which check/code refutes is recorded diagnostically, not asserted.
* A successor/modified-scope case, not the original test, which remains skipped on `[journal]` (unchanged). No other Q6 case re-run. Python 3.11.18/3.12.3 only.
* Independence: subordinate of lead builder session; technical result only.
