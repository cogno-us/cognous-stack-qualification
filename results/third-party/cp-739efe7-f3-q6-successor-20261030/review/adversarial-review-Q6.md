# Adversarial review: Q6 successor package (OCS-F3-Q240-FINAL) vs CP 739efe7d
Reviewer: read-only subordinate of the lead builder session (not independent). No opinion on F3-A formal acceptance.
Scratch: /tmp/claude-0/work/review/{rv (CP archive), vr (Verifier clone), rt (runtime bare clone), probe.py, rerun-A312.xml}

## Verified OK (no action)
- SHA256SUMS: `sha256sum -c` all OK. Protocol sha 25b076db... matches file and .sha256. FREEZE-HASHES harness hashes equal SHA256SUMS entries.
- Timing: freeze 04:30:17Z precedes first candidate run (Q6A-311 invocation 04:30:21Z; A0 :23, B/B0 :24, C-311 :25; 3.12 runs :33-:38). Harness files mtime 04:28, before freeze. Pre-freeze collection-only outputs (04:29) ran no test bodies.
- Pins: Verifier clone HEAD 39d46b4 and engine.py sha256 633defff... recomputed equal; public remote HEAD is still 39d46b4 today. Registry clone HEAD 943ab18. Format blob 231b5557 sha256 2fc671e6... equal.
- Format blob across runtime repo: I bare-cloned cogno-us/cognous-execution-runtime (138 heads). Exactly 9 heads contain engine/authorization_pin_format.py, ALL blob 231b5557; `git log --all` over the path = single commit 09f26efd. Matches env/format-module-variants.txt. (Also tests/test_authorization_pin_format.py exists on the same 9 heads, one blob be553a24; not run by the package, see F6.)
- Dependency freezes: py311 and py312 freeze files byte-identical to each other and to D-2's env/freeze-py311.txt (diff clean). The only environment differences are interpreter (3.11.18 vs 3.12.3 and their binary hashes), as recorded.
- Pin applicability: tests/test_claim_journal_stage.py, test_authorization_pin_export.py and the helpers they import (tests.v02_support, test_bounded_authorization, test_operation_identity, test_runtime_authority) contain no OCS_REGISTRY_* reference (grep); runs passed with the vars unset. Claim "no Registry needed for A and B" holds. For C the only env read is OCS_REGISTRY_PIN_DIR (test line 59) and PIN constant at line 45 = 943ab18; HEAD assertion at line 62-63 is what failed in D-2.
- Modified-copy diff: the only added line is FORMAT_PATH (Q6_FORMAT_MODULE_PATH). I confirmed the test function body is byte-identical to the original (python compare). 
- Reproduction (one item): Q6-A on 3.12.3 re-run in new scratch (fresh CP archive, fresh Verifier clone at 39d46b4, Registry vars unset): 13 passed, 1 skipped, same skip line 154; per-test outcomes identical to raw/Q6A-312/junit.xml (all 14 ids).
- No amendments, no changed qualification expectation found; the A-expectation miss is recorded unrevised.

## Findings

### F1 (should-fix) Skipped test: exact cause, and a genuine coverage gap exists, larger than verdict.md says
Test (lines 152-164): `if not (flow[2]._identity or flow[2]._freshness): pytest.skip(...)`. `flow[2]` is the BoundedAuthorizationWorkflow. In fixture param "journal", `enable()` is never called, so `_identity` and `_freshness` are falsy (bounded.py property; local_authority_effect.py:446 only passes check_ref when either is truthy). The skip fires before any Verifier call; independent of Verifier version, interpreter, Registry. No supported configuration of this fixture makes `[journal]` run: the parameter is by construction the "no identity, no freshness" route, and the skip condition is exactly its negation. (Only a different test, or a host config with merge/dedupe/identity/freshness, would execute that body, and that is the other param.)
I probed the body on the plain-journal route (probe.py, Verifier 39d46b4, 3.12):
 - Plain journal: resolution_checks[*].check_id are present but are NOT the journal check ids (different uuids from check_events). Replacing resolution_checks[1].check_id with the zero uuid is NOT detected (no refutation, overall "abstain"). So the first half of the test would FAIL if forced to run on plain journal; the skip is not hiding a passing test, it documents a real detection limit of the plain-journal route (consistent with the skip message "linkage only recorded with operation identity/freshness").
 - Plain journal: the second half (claim row lying about its stage -> `stage="decision"`) IS detected (`v2.journal.references/journal_stage_binding`, overall reject). That assertion is perfectly runnable on plain journal but is skipped together with the first half. So there is a real, narrow coverage gap: the stage-lie negative on the plain-journal route is never executed in any run; and the linkage-negative for plain journal is unenforced (not detectable) rather than merely unexecuted.
 verdict.md says "not covered ... only journal+operation-identity route is." Accurate, but it omits (a) that the stage-lie half is detectable and executable on plain journal and (b) that the linkage half is not detectable there. These are my own probe results, not package evidence; outside the frozen package.
Suggested wording (verdict.md Q6-A Analysis): "On the plain-journal route the linkage half cannot be asserted (resolution_checks carry non-journal check ids; a zeroed id is not refuted by Verifier 39d46b4), and the stage-lie half, which the Verifier does refute on that route (journal_stage_binding), is skipped with it. Reviewer probe only; no run in this package executes either half on plain journal."

### F2 (should-fix) Frozen A expectation contradicted by test source readable before freeze
The test's conditional skip (line 153-154) was visible in the CP tree at freeze; collection-only (14 collected) cannot show it. Protocol section 5 predicted "14 pass, 0 skipped" with basis "D-2 shows ...intended to pass", not mentioning the in-test skip. The miss is correctly recorded unrevised, and verdict.md reports it, but verdict.md Q6-A treats it as a surprise-free "by design" finding while the protocol framed it as a live possibility only for failures. Suggest adding one sentence: "The expectation was drafted without reading line 153-154; it was inconsistent with the test source at freeze time; recorded unrevised per CA04." No effect on outcome.

### F3 (note) Wording: first execution time
verdict.md says "first candidate execution 2026-10-30T04:30:2xZ". Raw invocation.txt shows 04:30:21Z (Q6A-311). Suggest "04:30:21Z (4 s after freeze)". The 04:30:25Z figure is Q6C-311, not the first run.

### F4 (note) "Unpinned Verifier" caveats are slightly stale/over-hedged
verdict says no transfer to "its later HEAD". Today the Verifier remote HEAD is 39d46b4 itself (ls-remote and clone), so the chosen sha is the current HEAD; and CP at 739efe7 truly pins none (grep: only importorskip, a docstring "pinned Verifier", README link; CI tests.yml has no verifier install). Keep the unpinned statement; add "= public HEAD at 2026-10-30" for the reader. Also the package's recon-time fetch is un-timestamped relative to HEAD; HEAD may move.

### F5 (note) "ONLY FORMAT_PATH changed" needs the qualifier already half-present
verdict says "ONLY `FORMAT_PATH` changed" while the diff is 312 lines because 27 other tests and the `refused` helper were dropped. The protocol (section 3) states this correctly; verdict.md should say "only added line is FORMAT_PATH; all other original tests and the `refused` helper omitted; retained function body byte-identical (I verified)". Not an overstatement of results, a precision issue.

### F6 (note) Gap B scope
The B result is the runtime's payload_defect/PAYLOAD_MEMBERS agreement only. A sibling test file tests/test_authorization_pin_format.py exists in the runtime repo (same 9 heads); not run here, not claimed. verdict.md already declines to claim runtime installer behavior; no change needed, optionally mention that file exists.

### F7 (note) OCS_REQUIRE_REGISTRY_PIN=1 in case C is inert for this test file
Only CI workflow YAML references it; test_v02_claim_policy_binding.py reads only OCS_REGISTRY_PIN_DIR. Harmless, but protocol/verdict imply it is part of the binding. Wording: "set for parity with CI; not read by this file".

### F8 (note) Verdict overall text: A/B/C summary is fair
"A partial, B only as modified copy, C resolved" is supported by raw gates (A NOT_RUN by skip, B NO_SKIP_PASS on modified copy, C NO_SKIP_PASS 95/95 on both). Only caveat is F1 (A "13/14" understates that the missing 1 is a detection limit, not a mere omission) and that C is conditional on the file's own pin (already stated). No blocking issue found.

Severity totals: blocking 0, should-fix 2 (F1, F2), note 6.

## Not examined
- D-2 artifacts beyond freeze-file diff (6 a01..a06 failures, PR #245, S1 results, 5 green files) - not verified.
- Registry clone content beyond HEAD sha (vector blob equality, requirements-ed25519.lock hashes, wheel hashes).
- Verifier's own test suite or correctness; whether 39d46b4 is the intended Verifier.
- Python 3.11 re-run (only 3.12 reproduced); Q6-B / Q6-C re-runs; full junit-by-id comparison of 3.11 vs 3.12 beyond reading the gates.
- CP git history/tree-id recomputation (I used git archive of the commit; did not recompute tree 1e7a7555 from files).
- Whether /home/claude/wt absence is the original builder environment; the runtime-installer worktree content.
- CP CI behaviour at 739efe7 beyond reading tests.yml (no CI run logs checked).
