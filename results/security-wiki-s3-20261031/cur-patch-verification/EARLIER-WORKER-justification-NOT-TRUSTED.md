# Justification for the proposed Qualification `cur` suite-generation patch (NOT APPLIED)

Governing: Engineering Constitution @ 1c2e920f4e58e07a52e8e2408a506cf7dbc1292b; Issue #254 (S3). Worker P1-cur-patch.
Patch: `/tmp/claude-0/sec/s3/cur-generation.patch` (35 lines, 2 files, +5/-1; sha256 cb0fc4d2943db0bf...), `git diff` format against cogno-us/cognous-stack-qualification origin/main 497f1319.
`git apply --check` OK in /home/claude/wt-s3 (after the revert below). Not applied there.
Raw evidence (all re-runnable, scripts included): `/tmp/claude-0/sec/s3/evidence/`.

## 0. Prep-branch state (history not rewritten)
Branch s3/prep-20261031 (unpushed): 5e32b660, f9f94825, then NEW commits 1ea2fc36 (reverts only `suites/security-runtime/test_security_runtime_chain.py` and `tools/run_security_runtime.py` to 497f1319) and 40cc37f5 (runner guard).
`git diff --stat 497f1319 HEAD -- suites tools/run_security_runtime.py` is EMPTY: the prep branch has no edit to suites/ or the existing run_security_runtime.py.
`tools/run_wiki_s3.py` now calls `require_cur_patch()` (in the config cross-check, also in `--dry-check`): it AST-reads `tools/run_security_runtime.py` for `'cur'` in `SUITE_GENERATIONS` and requires `CONTROL_PLANE_CUR_REVISION`, `MOLTBOT_CUR_REVISION`, `CUR_REVISIONS` in the chain harness; otherwise `Refuse("suite_generation 'cur' requires the approved patch /tmp/claude-0/sec/s3/cur-generation.patch ...")`. Observed on the unpatched prep tree: REFUSED. The TEMPLATE profile `note` and the runner docstring are marked "REQUIRES approved patch".
(Note: `tools/registry_integration_probe.py` shows uncommitted edits in that worktree made by another worker concurrently; not mine, untouched.)

## 1. What the patch is
```
tools/run_security_runtime.py:  SUITE_GENERATIONS = frozenset({'security','f5b','p4','p2'})  ->  + 'cur'
suites/security-runtime/test_security_runtime_chain.py:
  + elif GENERATION=='cur': from agent_replay_bundle.importers import CONTROL_PLANE_CUR_REVISION as CONTROL_PLANE_RUNTIME_AUTHORITY_REVISION, MOLTBOT_CUR_REVISION as MOLTBOT_RUNTIME_AUTHORITY_REVISION
  + (in odes_generation())  if GENERATION=='cur': return common.CUR_REVISIONS, common.CUR_PROFILE_VERSION
```
No test added/removed/edited, no assertion touched, no SHA literal in the patch.

## 2(a). AST evidence (python `ast.dump`, temp copies of ONLY the touched files; `evidence/ast_compare.out`, `strip_proof.out`)
Chain file, before vs after:
- function/class defs: 22 vs 22, same names; the only def whose `ast.dump` differs: `odes_generation` (the added `if`).
- test functions: 15 vs 15, ids identical (same order).
- `assert` statements: 35 vs 35, sequence of `ast.dump`s identical.
- decorators/markers: 5 vs 5, identical.
- constants: removed = {} ; added = {'cur': 2}. No expected-value literal changed.
- Only differing module-level statement: the `GENERATION` if/elif chain (index 15).
- STRIP PROOF: delete exactly the added `elif GENERATION=='cur'` clause and the added `if GENERATION=='cur'` line from the AFTER tree => `ast.dump(after) == ast.dump(before)` is **True**. So everything outside the added lines is identical, node for node (a stronger statement than byte equality).
run_security_runtime.py: defs identical (2 vs 2, none differ); `SUITE_GENERATIONS` constants before [f5b,p2,p4,security], after +[cur], removed []; dropping the single 'cur' element makes the module AST equal to before: **True**.
Also `diff -r` of the two full trees: exactly these two files differ (all other .py under suites/ sha256-identical).

## 2(b). Collect-only node-id sets (nothing executed; `evidence/collect*.txt`, `allA/allB`)
- Same environment as the runner (SCN_COMPONENTS_DIR, V1_VALIDATION_ID=current-stack-20261031, plugin autoload off, observer plugin): `suites/wiki-derived`: 290 ids before and after, `cmp` identical (sha256 fca9d891...). All 41 ids of `wiki41-nodeids.txt` are in that set (0 missing).
- `suites/security-runtime` (module imports the p2 generation branch; needs CP/Runtime on sys.path as the harness does): 36 ids before and after, identical.
- Combined 326 ids: identical (sha256 d287e03e...).
- The wiki-derived collect also reports one pre-existing collection ERROR for security-runtime when run without those paths (`No module named tests.test_runtime_authority`); the collect output is identical before/after apart from the tree path in that message.

## 2(c). Behaviour for existing generation values is unchanged (`evidence/gen_probe.out`)
Executed the module's import-time selection and `odes_generation()` (no test run) with both trees, Replay/ODES from /home/claude/cs-components:
| generation | before | after |
|---|---|---|
| security | 996baeb4 / fd6b76fa / odes ...0.2.3 | identical |
| f5b | a34c3dc2 / 4a83b175 / 0.2.4 | identical |
| p4 | 26a7e659 / 3024ef6e / 0.2.5 | identical |
| p2 | 7a4bcd40 / c5e97e87 / 0.2.6 | identical |
| bogus value | RuntimeError "unsupported security runtime generation" | identical (the `else: raise` is untouched) |
| cur | RuntimeError (unsupported) | ImportError "cannot import name CONTROL_PLANE_CUR_REVISION" on the pre-CUR Replay 40012b8c = fails LOUD, no silent fallback to p2 labels |
Code path: the new clause is reached only by the comparison `GENERATION=='cur'`; for any other value, Python evaluates it as False exactly as before, and SUITE_GENERATIONS membership for the other four is unchanged; the strip proof shows no other node moved.

## 2(d). What `cur` changes, and what it does not
- The Wiki/chain tests stamp `chain.CONTROL_PLANE_RUNTIME_AUTHORITY_REVISION` / `MOLTBOT_RUNTIME_AUTHORITY_REVISION` into Replay `import_bounded_workflow(control_plane_revision=...)` and Runtime `export_execution_artifacts(repository_revision=...)` (e.g. wiki-derived/test_wp_f_records_replay_policy.py:120,253,267,657,962; test_wp_c_budget_stop_recovery.py:263,265; _wp_g_common.py:95; v1-scenarios helpers), and ODES generation tuple via `odes_generation()`.
- Under `p2` those resolve to CP 7a4bcd40 / Runtime c5e97e87 (+ manifest fa170815, ODES p2 profile 0.2.6). The current pair is CP b19c47dd / Runtime f7a55e2a. Stamping 7a4bcd40/c5e97e87 on b19c47dd/f7a55e2a evidence would assert a source identity the bytes do not have = FALSE PROVENANCE (and Replay would, correctly, treat it as a different generation).
- With `cur` the harness takes the labels from the Replay/ODES CUR constants: CP `b19c47ddd020409d24e52e70b11359c46265edbb`, Runtime `f7a55e2a8494801e49193f9f46935f0a971c248d` (Replay `CONTROL_PLANE_CUR_REVISION`/`MOLTBOT_CUR_REVISION`), and ODES `CUR_REVISIONS` (manifest fa170815, CP b19c47dd, Runtime f7a55e2a, Replay pin, plus `CUR_PROFILE_VERSION`). These constants live in the Replay/ODES repos (S1 PRs), NOT in this patch.
- Does NOT alter: any expected value, refusal expectation (`pytest.raises(ImportContractError...)` etc.), marker, or test id (2(a): 35 asserts, 5 markers, 15 test ids byte-identical in AST). Wiki-test assertions run unchanged.
- Classification logic untouched: PASS/FAIL/BLOCKED is not computed in either patched file (`grep -c "PASS\|FAIL\|BLOCKED" tools/run_security_runtime.py` = 0; the chain file only contains test functions). Verdicts come from pytest junit + the observer plugin `tools/wiki_exchange_observer.py` and the analysis; `run_wiki_s3.py` states "verdicts are assigned by the analysis, not by pytest exit code". None of those files is in the patch (patch file list = the two files above).
- Test in the chain that references the historical label stays as is: `test_security_pair_rejects_historical_cp` imports Replay's `CONTROL_PLANE_RUNTIME_AUTHORITY_REVISION` directly (unchanged; AST-identical).

## 2(e). Where FINAL Replay / ODES / Pack SHAs are needed
- In THIS PATCH: nowhere (zero SHA literals). It imports four symbols: Replay `CONTROL_PLANE_CUR_REVISION`, `MOLTBOT_CUR_REVISION`; ODES `CUR_REVISIONS`, `CUR_PROFILE_VERSION`. Pack has no constant in this harness.
- Fill-in points live in the (unapproved-for-run) TEMPLATES, not in the patch: profile `components.{replay,evidence_pack,odes,exchange}.revision`, freeze-manifest `components_subject.*`, `tuple.json`, all `PLACEHOLDER:` (see /tmp/claude-0/sec/s1/Q-prep.md). These SHAs MUST be the MERGED revisions; the runner enforces HEAD==tuple SHA via require_pristine.
- OPEN VERIFICATION: `CUR_PROFILE_VERSION` in ODES is not named in the K/O S1 PR bodies I could read (O-prbody lists `CUR_REVISIONS`, not a profile version constant). Q-prep reported it seen in an ODES scratch `common.py`. Approver must confirm the four names in the MERGED Replay/ODES (command in 2(f)); a mismatch fails at import (loud), never silently.

## 2(f). Risks and a <10 minute verification
Risks: (1) symbol-name mismatch with merged Replay/ODES (loud ImportError, would look like a harness BLOCK not a verdict, so verify before the run); (2) the `cur` branch is only exercised at run time, collect-only does not import it (shown above: no collect change); (3) provenance labels remain caller-asserted in Replay (inherited PROVISIONAL DEVELOPMENT PIN); (4) a later Replay re-tie changes `CUR_REPLAY_PIN`/ODES `CUR_REVISIONS` -> tuple must follow.
Verify (read-only, in a scratch copy, `git apply` on a copy not on the worktree):
1. `cat /tmp/claude-0/sec/s3/cur-generation.patch` (35 lines, 2 files, additive).
2. `cd /home/claude/wt-s3 && git diff 497f1319 HEAD --stat -- suites tools/run_security_runtime.py` -> empty; `git apply --check /tmp/claude-0/sec/s3/cur-generation.patch` -> OK.
3. `python3 -I /tmp/claude-0/sec/s3/evidence/strip_proof.py <treeA> <treeB> ` (trees = prep tree / prep tree + patch) -> three True lines (stored: `evidence/strip_proof.out`); `ast_compare.py` for the full table.
4. `cmp /tmp/claude-0/sec/s3/evidence/allA /tmp/claude-0/sec/s3/evidence/allB` (326 ids, identical); 41-id subset: `sort wiki41-nodeids.txt | comm -23 - evidence/idsA` empty.
5. With the FINAL Replay/ODES on sys.path: `python -I -c 'from agent_replay_bundle.importers import CONTROL_PLANE_CUR_REVISION, MOLTBOT_CUR_REVISION'` and `python -I -c 'from odes.common import CUR_REVISIONS, CUR_PROFILE_VERSION'`.
