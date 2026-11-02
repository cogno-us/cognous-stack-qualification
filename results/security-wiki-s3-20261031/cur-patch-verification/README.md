# Verification of the Qualification `cur` suite-generation patch (Worker V-cur-verify)

Governing: Engineering Constitution cogno-us/cognous-engineering-constitution @ 1c2e920f4e58e07a52e8e2408a506cf7dbc1292b; Issue #254 (cogno-us/cognous-open-control-stack).
Architect decision: patch CONDITIONALLY APPROVED; apply only if conditions A-J all pass. All were re-derived mechanically by the scripts in this directory
(NOT taken from the earlier worker's justification, kept here as `EARLIER-WORKER-justification-NOT-TRUSTED.md` for comparison only). Non-authorizing; nothing was executed (collect-only / import-only).

* Patch file: `cur-generation.patch`, sha256 `cb0fc4d2943db0bfc3055c0c25b573c8c84349828fe631beae2b2deb268e8d0d`, 35 lines, 2 files, +5/-1.
* Base (prep branch head): `373942212cd9173363aa8205e046a2268e8380a9` (pushed as prep/NOT-FOR-MERGE-s3-wiki41-20261031). Patch commit = parent of the evidence commit on this branch.
* Blocked-41 list: `raw/blocked41-nodeids.txt` sha256 bd43f8891e4db51ca6a5d279328a58a0ac73e7b6e27da209c56d2313a836fc3c (identical to process/v1-validation/current-stack-S3-TEMPLATE/wiki41-nodeids.txt).

| ID | Condition | Verdict | Evidence |
|---|---|---|---|
| A (C1) | Collected test IDs identical before/after; all 41 present | PASS | `raw/c1-summary.json`, `raw/c1-blocked41.json`, `raw/collect-*-{before,after}.{ids,raw.txt}`: runner invocation `pytest -q -p no:cacheprovider -p wiki_exchange_observer --collect-only suites/wiki-derived suites/security-runtime`, runner env; unset/security/f5b/p4/p2: 326 ids (290 wiki-derived + 36 security-runtime) byte-identical before/after, 0 of the 41 missing. |
| B (C2a) | Security assertions identical | PASS | `raw/c2-stdout.txt`: ast.dump(after minus only the added cur clauses) == ast.dump(before) for both files; 35 asserts, 15 test ids, 5 markers, imports (only extra = the cur import inside the cur clause) identical. |
| C (C2b) | Expected values identical | PASS | `raw/c2-stdout.txt`: literal multiset diff = only `'cur'` x2 (chain) / x1 (tool), nothing removed; only def changed = `odes_generation`; `raw/c3-g-h-j.json.report.txt`: only these 2 files differ under suites/ and tools/ (876 tracked files compared byte-wise). |
| D (C3) | Classification logic untouched | PASS | `raw/c3-g-h-j.json.report.txt`: inventory of verdict/classification-like files; none is in the patch; no PASS/FAIL/BLOCKED/vacuous/verdict/classif token on any added/removed line (3 pre-existing `status=='pass'/'fail'` asserts in the chain file untouched). |
| E (C4) | Historical-generation behaviour identical; cur fails loudly | PASS | `raw/c4-generation-resolution.json`: unset/security/f5b/p4/p2 resolve to identical CP/Runtime constants and ODES tuple/profile version before/after (p2 = 7a4bcd40/c5e97e87, 0.2.6); unsupported value -> identical `RuntimeError: unsupported security runtime generation`; `cur` on current Replay 40012b8c (no CUR names) -> `ImportError ... CONTROL_PLANE_CUR_REVISION` at import (no p2 fallback); before patch `cur` -> RuntimeError unsupported. |
| F | No weakened refusal requirement | PASS | `raw/c2-stdout.txt`: 7 pytest.raises, 3 match=, 2 raise stmts, 1 refuse-call, 0 `is None` asserts and all 9 refusal/reject/negative helper defs identical. |
| G | No removed/masked adversarial fixture | PASS | `raw/c3-g-h-j.json`: 17 .py files in suites/wiki-derived + suites/security-runtime: 18 fixtures, 12 parametrize decorators, 212 negative-reference identifiers identical; non-.py data identical; collect ids identical (A). |
| H | No changed PASS/FAIL/BLOCKED semantics | PASS | conftest.py (17 incl. wiki-derived no_network), pytest.ini, tools/wiki_exchange_observer.py, tools/run_wiki_s3.py byte-identical; patch touches no verdict code. |
| I | No new skip/xfail; ImportError stays loud | PASS | patch text has no skip/skipif/xfail/importorskip/try/except/getattr; skips count 0 before/after; `cur` on old Replay is a collection ERROR (`raw/collect-cur-after.raw.txt`), not a skip. |
| J | No unreviewed oracle change | PASS | `git diff --stat 373942212 <patch commit>` = exactly the 2 patch files (+5/-1); this evidence commit adds only files under this directory. No process/, expectations, applicability or catalogue file touched. |
| C5 | Minimal; runner guard accepts | PASS | no hex/SHA literal in added lines; `tools/run_wiki_s3.py require_cur_patch()` REFUSES the unpatched tree and ACCEPTS the patched tree (c3 report). |

## What could and could not be collected for `cur`
Replay main bb5fe6f3 (has CONTROL_PLANE_CUR_REVISION / MOLTBOT_CUR_REVISION) and ODES PR #142 (CUR_REVISIONS / CUR_PROFILE_VERSION) are NOT in /home/claude/cs-components (Replay is 40012b8c, ODES 1a5e1d30), and no new clones were allowed.
So: `cur` against the real components collects 290 ids + 1 loud ImportError (expected until the merged Replay is used). To prove the id set for `cur` anyway, `stub/sitecustomize.py` (verification-only, NOT part of the patch)
injects the four CUR names at import time; with it `cur` collects the same 326 ids as p2 (`raw/collect-cur+curstub-after.ids`, cmp-identical). Stub values are the current CP/Runtime pins; ODES values are placeholders and `odes_generation()` is not called during collection.
Test ids do not depend on the generation value at all (they are identical for all of unset/security/f5b/p4/p2), so non-cur ids are unaffected. The real `cur` run still needs the merged Replay/ODES names verified (comment in the patch says so).

## Reproduce
Scripts take a BEFORE tree (prep commit 373942212 checked out), an AFTER tree (BEFORE + `git apply cur-generation.patch`), an output dir and, for c1, the stub dir and the blocked-41 list:
`c1_collect.py BEFORE AFTER OUT stub blocked41-nodeids.txt`, `c3_g_h_j.py BEFORE AFTER OUT cur-generation.patch`, `c4_gen.py BEFORE AFTER OUT stub`,
`BASE_REF=373942212cd9173363aa8205e046a2268e8380a9 c2_ast.py BEFORE AFTER OUT cur-generation.patch` (c2 was last run with AFTER = the committed branch). Needs /home/claude/cs-components. c1/c3/c4 raw output was produced against a scratch copy of the patched files, byte-identical (cmp) to the committed ones.

## Discrepancies vs the earlier justification
None material; all its numbers reproduced (22 defs, 15 tests, 35 asserts, 5 markers, 290/36/326 ids, generation constants, loud ImportError on 40012b8c). Differences: (1) it says the prep branch is unpushed, now pushed; (2) its combined-id sha (d287e03e) differs from ours (f96438040e1ce2f6 over a differently formatted list) - same 326 ids, wiki-derived subset cmp-identical to its ids_wiki_before.txt; (3) it did not show `cur` ids at all (impossible on the real Replay) - we add the stub proof; (4) it did not cover F-J, which are added here; (5) its note that the wiki-derived collect reports a security-runtime error without CP/Runtime on sys.path is confirmed (needs runner PYTHONPATH).
