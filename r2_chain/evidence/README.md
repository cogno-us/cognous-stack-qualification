# R2 joined-chain evidence index (stub)

PRIVATE PREVIEW QUALIFICATION TUPLE (preview-only, NOT canonical; `component-lock.json` untouched). Synthetic only; single synthetic tenant; claim A only.

The committed run evidence is produced later by the lead from the exact candidate head and is added to this directory. Until then this file is only the index of what a run produces. It does not assert that any run has passed.

Reproduce: `bash r2_chain/participant_run.sh [out_dir]` (see `../README.md`). Evidence files written by `run_chain.py` to `out_dir`:

| File | Content |
|---|---|
| `summary.json` | disposition, result counts per label, per-row verdicts, required-row check, source-identity result before and after the run |
| `rows.jsonl` | one row per marked test: row id, case id, label (PASS / FAIL / REFUSED_AS_EXPECTED / NOT_RUN / NOT_APPLICABLE), expected and observed typed code, node id |
| `positive-case.json` | the positive chain case: record and selection digests, verifier verdict, markers, binding, operator inputs, assertions P01..P15 |
| `source-identity.json` | HEAD, tree and clean-work-tree check of each pinned source; qualification revision |
| `environment.json` | interpreter, platform, package versions, exact command, tuple SHAs |
| `tuple.json` | copy of `r2_chain/sources.json` (the PRIVATE PREVIEW QUALIFICATION TUPLE) |
| `sources-identity.tsv` | output of `fetch_sources.sh` (name, repo, HEAD, tree) |
| `junit.xml`, `pytest.log` | raw pytest output |
| `SHA256SUMS` | sha256 of every other file in the directory |

Links: register [#259](https://github.com/cogno-us/cognous-open-control-stack/issues/259); R1 Final Closeout <https://github.com/cogno-us/cognous-open-control-stack/issues/259#issuecomment-6609667524>.
