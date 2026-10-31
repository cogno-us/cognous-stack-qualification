# Re-verification of the `cur` suite-generation patch against the MERGED components (Worker Q3-tuple-prep, 2026-10-31)
Governing: Engineering Constitution cogno-us/cognous-engineering-constitution @ 1c2e920f4e58e07a52e8e2408a506cf7dbc1292b; Issue #254. Non-authorizing; NOTHING executed (pytest --collect-only and module import only).

Components were `git archive`d (no checkout state) into scratch at the exact merged SHAs (all `git ls-remote origin refs/heads/main` == SHA; trees verified):
Replay d395e37c (tree 0bdee3ea), ODES 77fd7a1c (tree d8b33261), Evidence Pack 96f5f2e1 (tree 2fc26d4c), CP b19c47dd, Runtime f7a55e2a, Manifest fa170815,
Exchange = LOCAL 7f7569b0 (historical; Exchange r2 merge not yet known - collection does not exercise it). No stub, no sitecustomize.
BEFORE = prep ec3e2083 (suites/ + tools/ minus probe identical to 37394221); AFTER = run branch (BEFORE + ea8bddcd patch semantics; patch sha256 cb0fc4d2943db0bfc3055c0c25b573c8c84349828fe631beae2b2deb268e8d0d re-extracted from `git diff ea8bddcd~1 ea8bddcd`: identical).

| Item | Verdict | Evidence |
|---|---|---|
| Names exist and equal the tuple | PASS | Replay `importers.CONTROL_PLANE_CUR_REVISION`=b19c47dd, `MOLTBOT_CUR_REVISION`=f7a55e2a; ODES `common.CUR_REVISIONS`={manifest fa170815, replay d395e37c, control_plane b19c47dd, moltbot_safe f7a55e2a}, `CUR_PROFILE_VERSION`=odes-cognous-stack-export-0.2.7-security-runtime-cur-candidate (`raw/c4.json`) |
| A ids identical | PASS | `raw/c1-summary.json`: unset/security/f5b/p4/p2 = 326 ids (sha16 f96438040e1ce2f6) before and after; `cur` AFTER = 326 ids, rc 0, NO ImportError, byte-identical to p2 (`collect-cur-after.ids` vs `collect-p2-after.ids`, cmp). `cur` BEFORE patch = 290 + 1 loud RuntimeError (unsupported generation). 41/41 of the blocked set present in every generation. |
| B security asserts identical | PASS | `raw/c2-stdout.txt` (ast.dump of AFTER minus the cur clauses == BEFORE; 35 asserts, 15 tests, 5 markers, 7 raises) |
| C expected outcomes identical | PASS | c2 literal diff = only 'cur'; c3: only the 2 patch files differ in suites/+tools/ (876 files) |
| D classification logic untouched | PASS | `raw/c3-g-h-j.json.report.txt` |
| E historical + P2 behaviour identical; cur loud | PASS | `raw/c4.json`: unset/security/f5b/p4/p2/bogus identical before/after (p2 = 7a4bcd40/c5e97e87); `cur` resolves to b19c47dd/f7a55e2a and odes_generation() to CUR_REVISIONS/0.2.7 cur-candidate, != p2 labels; before patch = RuntimeError |
| F refusal requirements not weakened | PASS | c2 (7 pytest.raises, 3 match=, helper defs unchanged) |
| G no removed/masked fixture | PASS | c3 (18 fixtures, 12 parametrize, 212 negative-reference identifiers identical; non-.py data identical) |
| H PASS/FAIL/BLOCKED semantics | PASS | c3 (17 conftest + observer + pytest.ini + run_wiki_s3.py byte-identical) |
| I no new skip/xfail | PASS | c2 (skips 0/0; patch text has no skip/xfail/try/except) |
| J no unreviewed oracle change | PASS | c3 J0/J1/J2: exactly the 2 patch files differ |
Residual: the chain-file comments still say "VERIFY against the MERGED ..."; verified here, comments deliberately left untouched (patch bytes are the approved ones).
Scripts (paths point at the scratch component dir used; adapt `C=`): `scripts/`. c4 was adapted for real (non-stub) components.
