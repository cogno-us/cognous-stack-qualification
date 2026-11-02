# Refusal controls for the S3 freeze (Issue #254; Constitution 1c2e920f)
Run in a scratch copy of this repo (never the real frozen config) with `python3 -I -B refusal_controls.py` (paths are the scratch layout of the freezing worker).
* `refusal-runner-only-output.txt`: tools/run_wiki_s3.py --dry-check per scenario (first run, before the guard existed).
* `refusal-runner-and-guard-output.txt`: same scenarios, runner --dry-check AND tools/s3_tuple_guard.py (rc pairs in the SUMMARY line: [runner, guard]).
* `runtime-boundary-single-case-controls.txt`: where wrong-but-consistent configurations are refused at run time.
Findings: the runner refuses missing/short/branch revisions, placeholders/TEMPLATE, inconsistent profile names, tuple/config/checkout mismatches, dirty or wrong-HEAD or missing checkouts, absent cur patch.
The runner does NOT refuse a CONSISTENTLY wrong Exchange profile name (3a original, 3b typo -r3, 3d p2) or a CONSISTENTLY mixed-generation set (4a Replay 40012b8c, 4b ODES 1a5e1d30): dry_check OK, collected 41.
tools/s3_tuple_guard.py (new, stdlib, read-only; runner unchanged) pins the intended tuple/trees/profile and the r2 block of the Exchange source and refuses all of those (guard rc=2).
