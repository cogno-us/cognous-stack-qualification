# R2 joined-chain evidence index

PRIVATE PREVIEW QUALIFICATION TUPLE (preview-only, NOT canonical; `component-lock.json` untouched). Synthetic only; single synthetic tenant; claim A only.

Committed run: [`run-2026-11-03-ecee20fb/`](run-2026-11-03-ecee20fb/) - clean-checkout participant run at tested code head `ecee20fbb8d47341bada66009fd6fff2d864db78` (disposition PASS: 10 PASS, 35 REFUSED_AS_EXPECTED, 4 NOT_APPLICABLE documented limits, 0 FAIL). Later commits on the PR branch add evidence and documentation only, no code. Negative matrix: `run-2026-11-03-ecee20fb/negative-matrix.md`. The four NOT_APPLICABLE rows are documented limits (ADMITTED behavior), see `../README.md`.

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
