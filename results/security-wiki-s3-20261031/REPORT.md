# Security Wiki S3: merged current-tuple 41-case results

Governing: Engineering Constitution cogno-us/cognous-engineering-constitution@1c2e920f4e58e07a52e8e2408a506cf7dbc1292b; Issue #254 (cogno-us/cognous-open-control-stack).
Scope: developer / local-offline run by the lead builder's Worker A. NOT independent qualification. No release, production or certification claim. claims_made = [].
Suite generation label `cur` (patch ea8bddcd, sha256 cb0fc4d2943db0bfc3055c0c25b573c8c84349828fe631beae2b2deb268e8d0d): caller-asserted PROVISIONAL DEVELOPMENT PIN labels, inherited and unqualified.

## Tuple (commit -> tree; pristine fresh checkouts via git init + fetch --depth 1 + detach; HEAD and tree verified; all equal ls-remote main)
| component | commit | tree |
|---|---|---|
| Control Plane | b19c47ddd020409d24e52e70b11359c46265edbb | 039219b5aba7a157fff79781c716067fad7ed985 |
| Runtime | f7a55e2a8494801e49193f9f46935f0a971c248d | 97da8323368bb5a573fd157b11a9c1dda1178a10 |
| Replay | d395e37c443fedf1bf6b9a4651338b7b7de4a553 | 0bdee3eacd650ecb0e99781635a972e68cbe2853 |
| ODES | 77fd7a1cb1dd7a2dbc9ac3c02538a617056688ae | d8b33261de975fc504ff8f0ac30a8f47e8ebd43f |
| Evidence Pack | 96f5f2e126a9c27a75716658d4d2e85baf94b40b | 2fc26d4c86e65b22bdffedf1090a15e7167440d3 |
| Governed Exchange (squash of #63; profile security-runtime-current-20261031-r2 verified in gax_ref_runtime.py: Replay d395e37c, ODES 77fd7a1c, Pack 96f5f2e1, CP/Runtime/Manifest as listed) | 746378d74bff59314bdcf8f0b50b19ab94679ba9 | dcbe909f96d7c83e6281c5679283bd65cf19dbdb |
| Action Manifest | fa170815ef96a54c233d0dd9da821b60debabf8b | 3b0e3772e944aa668c8f4b879588c7cc3e2c32be |
| Migrated Registry (recorded, not exercised by the Wiki harness; code-equal a40fe755, differs only in docs/ + README.md) | 6b96a9a658923954433dc1a4c13626fa5145b9c7 | 38d50602ae725e208f010baba05bbf7b908e76ac |
| Qualification main (ancestry: merge commit of origin/main into the run branch, no history rewrite) | 5409d4776a9daff204fc97b71958b4dee12687b0 | 43f171ee47eb7fb8b861f444d386f1d137192f75 |

## Result of the primary execution (single run, no retries, no -x, one pytest process, observer plugin, junit, log)
* pytest: 38 passed, 1 failed, 2 errors in 443 s (junit 41 testcases, 0 skipped).
* Classification: **38 PASS / 0 FAIL / 3 BLOCKED**. The 3 BLOCKED are TC-L06-020: `..._three_sequential_exchanges_instruction_bearing_narrative_at_the_third_hop_has_no_effect` (junit failure), `..._each_hop_is_assessed_against_its_own_sender_recipient_and_authority` and `..._forwarded_message_with_a_changed_requested_action_is_refused_by_commitment` (junit errors at setup). Cause for all three: `OSError: [Errno 28] No space left on device` on the shared host disk (first in Control Plane bounded.py _write via tempfile.mkstemp; then pytest basetemp could not create directories). This is an environment fault of the host, not a refusal by any component, and not evidence about the control. The intended assertions were not reached/completed.
* Supplementary re-execution of exactly those 3 ids (once, same tuple, same environment, separate directory) after space was available: 3 passed. Reported separately; if the architect accepts it, the 41-case total is 41 PASS / 0 FAIL / 0 BLOCKED; if the rule "one execution" is applied strictly it is 38 / 0 / 3.
* The Exchange strict source-identity check (the original blocker, `candidate source identity mismatch`) was exercised in every one of the 41 tests (obs.json: calls >= 1, raised = 0).
* No FAIL: no component refused a case that the frozen expectations require to pass, and no frozen expectation was violated.

## Vacuity review
Every case was inspected; PASS requires the intended assertion to run. Known-limit cases (marked limit-assertion in the CSV) and positive-path cases are included: for them PASS means the documented behaviour/limit was observed, not that a hostile input was refused; marked in the CSV). Exception-based refusals: TC-L06-003 undeclared action (pytest.raises with the message 'declared Manifest action' asserted; boundary = Manifest-declaration check at bundle export) and one sub-case of TC-L06-039 out-of-scope (tool_not_in_the_manifest: exception only asserted; 5 of 6 sub-cases per phrasing reached the Control Plane decision and held with reasons). These two parametrised rows are PASS with a PARTIAL vacuity note, not BLOCKED/vacuous, because 5/6 sub-cases are substantive and the exception text is the intended boundary.

## Freeze and controls (honest findings)
1. The first real invocation (freeze 877bc005) was refused at the runner's collect-only step: the observer wrote OBS_OUT into the not-yet-created raw/ directory. No test body ran. Fixed by a 2-line change (collect-only uses a null sink) in commit b48675b7 (the freeze actually used). The `--dry-check` had masked this because it uses /dev/null.
2. `run_wiki_s3.py --dry-check` does NOT refuse a consistently wrong Exchange profile (original -20261031, typo -r3, p2) or a consistently mixed-generation set (Replay 40012b8c, ODES 1a5e1d30): dry_check OK / collected 41. It does refuse missing/short/branch revisions, placeholders and TEMPLATE markers, inconsistent profile names, tuple/config/checkout mismatches, dirty / wrong-HEAD / missing checkouts and an absent cur patch. A new read-only `tools/s3_tuple_guard.py` pins the intended tuple, trees, profile and the r2 block of the Exchange source and refused all of these (see run-41-merged-tuple-controls/). At run time the Exchange itself refuses the original profile (`candidate source identity mismatch: agent_replay_bundle.importers`) and Replay 40012b8c fails to import CUR names (no p2 fallback) - recorded in runtime-boundary-single-case-controls.txt. The guard was run against the real config before the run (OK).
3. Disclosure: during the controls, one id (the first of the 41) was run once in a scratch copy as a control rehearsal (PASSED); it is not used as a verdict.
4. Exchange known unhardened residual (from its source): git replace refs in a candidate checkout are not neutralised by the source-identity check.

## Not covered
Registry 6b96a9a6 not exercised here (separate probe). 244 passing cases not rerun; 5 historical failures and 4 unimplemented cases untouched. Fixtures and harness sources are identified by sha256 in raw/run.json (harness_source_hashes, config_hashes). Environment: raw/run.json (python, platform, pip freeze, pytest version).
