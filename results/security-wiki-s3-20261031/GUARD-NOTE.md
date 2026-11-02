# GUARD-NOTE: mandatory S3 tuple-guard preflight and the guard-result schema

Governing: Engineering Constitution @1c2e920f4e58e07a52e8e2408a506cf7dbc1292b; Issue cogno-us/cognous-open-control-stack#254; architect decision D5. Non-authorizing.

## C1 guard status (no retroactive claim)
C1 (`run-41-merged-tuple/`, freeze `b48675b7`, 38 PASS / 0 FAIL / 3 BLOCKED) and the supplementary C2 run PRE-DATE mandatory guard integration. Their guard status is **"not a gate, scratch-copy controls only"**: the tuple guard existed as a stand-alone read-only tool, was run by hand, and its refusal controls were exercised on scratch copies (`run-41-merged-tuple-controls/`); the C1 runner did not call it and C1 retained no guard-result record. Nothing in this change re-labels, re-executes or re-hashes C1; its `raw/run.json` has no `preflight_guard` field and must not be read as `passed`. Only runs produced by a runner revision that contains this integration carry the field.

## What changed (S3 tooling only; `tools/`, `process/mvp-acceptance`, the gate and its workflow are untouched)
* `s3/s3_tuple_guard.py`: the checks are unchanged in substance; they now run through `run_guard(tuple, components, root)`, which returns a record instead of printing, and adds an explicit placeholder/TEMPLATE check, a 40-hex SHA-format check per component and a per-check result list. The CLI still prints `REFUSED:` / exit 2 and writes nothing.
* `s3/run_wiki_s3.py`: `guard.run_guard(...)` is the FIRST statement of `main()`, before any other check, for `--dry-check` and real runs alike. There is no option or environment variable that skips it (asserted by test).
* Test: `tests/test_s3_guard_preflight.py` (hermetic: scratch copies of config/tuple, scratch checkout dirs with a patched `git`; one test against the real pinned checkouts is skipped when they are absent). `tests/` is outside the MVP byte inventory (the gate commits only `.`, `suites`, `suites/operation-identity`, `tools` direct files, `process/mvp-chain`, `process/mvp-acceptance`).

## Retained evidence
| situation | record | `preflight_guard` |
|---|---|---|
| real run, guard passed | `<out>/raw/guard-result.json`; `raw/run.json` has `preflight_guard`, `guard_result_sha256`, and `config_hashes['s3/s3_tuple_guard.py']`; the file is listed in `<out>/SHA256SUMS` | `passed` |
| real run, guard refused | `<out>-REFUSED/guard-result.json` (`-REFUSED-1`, ... if it exists); `--out` itself is NOT created, so the one-shot directory stays unused | `refused` |
| `--dry-check`, guard refused | record printed on stdout, reason on stderr; nothing written (dry-check writes nothing, as before) | `refused` |
| `--dry-check`, passed | stdout JSON contains `"preflight_guard": "passed"`; nothing written | `passed` |

## guard-result schema `cognous.wiki-s3-guard-result/1`
`schema`; `label`; `preflight_guard` (`passed|refused`); `refusal_reason` (null when passed); `validation_id`; `exchange_profile_required`; `guard_file {path, sha256}` (sha256 of the guard executed); `tuple_sha256` (sha256 of the tuple file bytes); `inputs {tuple_path, components_dir, root, profile_path, profile_sha256, freeze_manifest_path, freeze_manifest_sha256}` (profile/manifest entries present once they were read); `checks [{check, result: pass|fail, reason?}]` (executed checks in order; the first failure ends the list, later checks are not run); `expected {component: {commit, tree}}`; `utc_time` (UTC, ISO 8601).

## Refusals covered (each by a regression test asserting the specific reason)
Wrong Exchange profile (original `security-runtime-current-20261031`, `-r3` typo, P2, other; also profile-file-only and manifest-only); mixed generations (Replay 40012b8c, ODES 1a5e1d30, Pack 7b9511f2, CP 7a4bcd40, Runtime c5e97e87), including when set consistently in tuple, profile, manifest and checkouts; unknown/substituted SHA for each of the 8 components, in the tuple, profile or manifest; malformed SHA (branch, prefix, empty, uppercase, null); unresolved PLACEHOLDER/TEMPLATE in tuple, profile or manifest; wrong validation id; checkout HEAD, tree, pristine state or presence wrong; Exchange profile constants (CP/Runtime/Manifest/Replay/ODES/Pack) differing from the tuple or the profile block absent.
