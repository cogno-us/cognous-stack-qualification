# Final repaired-source preflight — 16 October 2026

**BLOCKED: source admission. Integrated scenarios NOT RUN.**

The seven actual merged component commits in `candidate.json` were inspected in
clean checkouts using `tools/final_source_preflight.py`. All nine admission
mapping checks failed: six Exchange source pins and three consumer Control Plane
revision admissions. These are nine prerequisite checks, not nine executed
effect scenarios or a general failure of the implementations.

Two real API probes corroborate the boundary:

- Exchange `load_executor_runtime()` refuses with `candidate source identity
  mismatch: agent_control_plane.bounded`.
- Replay `import_bounded_workflow({}, control_plane_revision=<current CP>)`
  refuses with `unsupported Control Plane revision` before inspecting the empty
  record. The empty record is only an admission probe, not execution evidence.

The command exited **1**, as a failing admission gate must. No compatibility
constants or production implementations were patched. No paid model calls,
effects, authority grants, release selection or publication occurred.

## Retained records

- `candidate.json`: seven nonselected exact source commits.
- `preflight.json`: actual pins/trees, loaded source hashes, mapping checks and
  API exceptions. Historical required revisions are retained alongside observed
  revisions; none is substituted for another.
- `environment.json`: both starting repository commits, exact runner/profile
  hashes, hash-locked dependency input and installed versions. The runner/profile
  were working-tree bytes at execution, identified by hashes; the containing PR
  supplies their later publication commit.
- `SHA256SUMS.json`: hashes of these three original evidence records.

## Reproduction and next gate

Check out this qualification revision, install the hub's recorded
`tools/requirements-release.lock` using `pip install --require-hashes`, and clone
each `candidate.json` component into `<work>/<component-key>` at its exact SHA.
Keep all checkouts clean, including untracked files. Then run once into a fresh
output path:

```sh
PYTHONDONTWRITEBYTECODE=1 python tools/final_source_preflight.py \
  --profile results/final-source-preflight-20261016/candidate.json \
  --work <work> --out <fresh-output>/preflight.json
```

Until compatibility mappings are migrated, expect exit 1 and retain the evidence.
Do not disable source checks or label new producers as older accepted revisions.
The next sequence is: Replay exact producer contract; ODES/Evidence Pack using the
actual merged Replay; Exchange using all actual merged dependencies; then the
bounded scenario suite and affected complete-reference regressions.

[The single finalization control plane](https://github.com/cogno-us/cognous-open-control-stack/issues/68)
owns sequencing. This preflight does not select the candidate, qualify any
scenario, confer independent review, or change publication/production HOLD.
