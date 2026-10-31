# ISOLATION-NOTE: S3 tooling relocated out of the frozen MVP byte inventory (post-run, behaviour-preserving)

Governing: Engineering Constitution @1c2e920f4e58e07a52e8e2408a506cf7dbc1292b; Issue cogno-us/cognous-open-control-stack#254; architect decisions D3 (no MVP candidate v7) and D4 (isolate S3 tooling, do not weaken integrity checks, do not hide executable source).

## Status of the C1 run
C1 (`run-41-merged-tuple/`, 38 PASS / 0 FAIL / 3 BLOCKED) was produced at freeze `b48675b7` with the ORIGINAL layout (`tools/run_wiki_s3.py`, `tools/wiki_exchange_observer.py`, ...). Its `raw/run.json` `config_hashes` keys and hashes (`tools/run_wiki_s3.py`, `tools/wiki_exchange_observer.py`) describe that layout and are NOT changed. This move happens AFTER the run, is not part of what C1 executed, and does not retroactively re-label C1. The historical records in this directory (README-S3-run.md, FREEZE-STEPS.md, REPORT.md, CROSSWALK-S4.md, REVIEW-CORRECTIONS.md, sub-READMEs) deliberately keep the old `tools/...` paths; read them with the mapping below.

## Cause of the four failing GitHub checks
`validate` (catalog-validation) x2, `validate-and-build` and `integrity` all run `python -m unittest discover -s tests`; two tests in `tests/test_mvp_acceptance_gate.py::RulingsTwoTests` failed:
`test_committed_candidate_matches_the_files_in_this_repository` and `test_every_file_directly_in_a_sys_path_directory_is_committed`.
`tools/mvp_acceptance_gate.py commit_files()` commits EVERY file directly in a sys.path directory (`SYSPATH_DIRS = (".", "suites", "suites/operation-identity", "tools")`) by bytes into `process/mvp-acceptance/candidate-commitment.proposed.v6.json`. Exact responsible paths (set difference against the v6 commitment):
* not in commitment (new files in tools/): `tools/run_wiki_s3.py`, `tools/s3_tuple_guard.py`, `tools/registry_integration_probe.py`, `tools/wiki_exchange_observer.py`
* committed but changed: `tools/run_security_runtime.py` (the approved cur patch added `'cur'` to `SUITE_GENERATIONS`)
`suites/security-runtime/` and `results/` are NOT in the inventory (only `suites/mvp-chain`, `suites/mvp-applicability`, `suites/mvp-d2-route-b`, direct files of `suites/` and `suites/operation-identity`, `process/mvp-chain`, `process/mvp-acceptance`, tools/ direct files and import closure); the suites/ label edit and the results/ additions did not trip anything.

## Isolation
* The four S3 files moved with `git mv` to `s3/` (own commit `2824a5d5`, 100% rename, 0 insertions/0 deletions). `s3/` is not in `SYSPATH_DIRS` and not on any workflow PYTHONPATH of `mvp-acceptance.yml`, so it is outside the MVP byte inventory; it IS committed, inspectable source, hashed into every S3 run record (`config_hashes`) and covered by the same CI and review gates as any other committed file.
* `tools/run_security_runtime.py` is back to its main bytes (sha256 b417d447f323c237c26f759ac3a4fc580ad4fd7550d06df4c2bafa37bdf3dbc1 = the value committed in v6). The `'cur'` member of `SUITE_GENERATIONS` is NOT needed for S3: `s3/run_wiki_s3.py` never invokes `tools/run_security_runtime.py` (it runs pytest directly on the 41 node ids) and the generation reaches the harness through the profile's `suite_generation` read by the suite helpers. The runner's `require_cur_patch()` previously used that member as one of its presence checks; it now requires only the harness-side symbols (`GENERATION=='cur'`, `CONTROL_PLANE_CUR_REVISION`, `MOLTBOT_CUR_REVISION`, `CUR_REVISIONS`) in `suites/security-runtime/test_security_runtime_chain.py` and still refuses the unpatched harness (verified). Side effect, intended: the `cur` profile stays refused by `run_security_runtime.py` (`Unsupported suite generation`), so the historical runner cannot be used to produce a `cur` run.
* Frozen MVP files, commitment (v6 sha256 42b482eec25b9d9c1455b5eefc63fb726d7a8041698831cc3c168ea5809a1846), acceptance predicates, security expectations and `mvp-acceptance.yml` are untouched. No candidate v7.
* Edits after the pure rename (second commit): path references (usage docstrings; `OBSERVER` = `s3/wiki_exchange_observer.py`; child `PYTHONPATH` = `tools` then `s3`, so the `-p wiki_exchange_observer` plugin resolves), `require_cur_patch()` as above. No change to node ids, expectations, observer logic, guard checks or probe logic.

## Rename evidence (`git diff -M --stat 80bb2ffc..2824a5d5`, all four 100% renames)
| file | sha256 before (tools/) | sha256 after pure rename (s3/) | after second commit |
|---|---|---|---|
| run_wiki_s3.py | ff4ecc5e74d5394373db31b7c72b85824be72f91fc41bbe119bacddddb579530 | same | e2092d42404af044b9c9fcedcf81e33d7cdd1f34f09794dd0fe5e716de578b1d |
| s3_tuple_guard.py | 191799e5d65ba408c154cb0ce29cbb83506414e94aced4c4f0902d2d520c9377 | same | 6e83cd03946f20bba14c99c509eb2c5309aef5186e4ff72967c3583f9781046e (docstring paths only) |
| registry_integration_probe.py | dd9a08256195116a923a0eef303bd5bdfafc6ffd070d305f5823e9202ac6fbdd | same | 38f76a83179a7718a5c5183f112c50afffd7adb3fefedfd135040ba7ca814e6e (docstring path only) |
| wiki_exchange_observer.py | 0b503becb206fa05ade97ae9eb03b75a49a90c0065602ff6399282e16960a343 | same | unchanged |

Cross-check: C1's retained `raw/run.json` `config_hashes` records `tools/run_wiki_s3.py` = ff4ecc5e... and `tools/wiki_exchange_observer.py` = 0b503bec..., equal to the 'before' column (and `git show b48675b7:tools/run_wiki_s3.py | sha256sum` = ff4ecc5e...). The pure-rename commit therefore moved exactly the bytes C1 executed. To audit what C1 executed, use freeze `b48675b7` / those recorded hashes, not the second-commit versions of the relocated files.

## New invocation paths
`python3 s3/s3_tuple_guard.py --tuple ... --components DIR`, `python3 s3/run_wiki_s3.py ... [--dry-check]`, `python3 s3/registry_integration_probe.py ...` (old `tools/...` paths no longer exist).
