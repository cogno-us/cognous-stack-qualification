# Comparison runner

**Scope.** Bounded synthetic profile only. The comparator applications (the OPA application and the LangGraph plus OPA application) are configured by Cognous, not vendor implementations. This is not independent certification and not production readiness; operational trust stays on HOLD. Linux only.

This directory holds the comparison-runner side of `comparators/`: the column of the protected destination for the Wiki subset, the Wiki
entry point, the cell aggregation, the report generator, the contract self-check and the top-level script of the whole comparison. It adds
files only; nothing under `comparators/wiki` or elsewhere in `comparators/` is edited. Operational trust stays on HOLD. Nothing here
authorizes a release or production use.

## Files

| File | Role |
| --- | --- |
| `ocs_column.py` | Interface of the destination (eight request fields, closed operation list), adapter for the Wiki subset, declaration rules and `check_declarations` |
| `declare_ocs_column.py` | Writes or checks `ocs-column-declarations.json` and `.md` from the plan file and the rules; reads no result |
| `ocs-column-declarations.json` / `.md` | Per scenario: asked, not expressible or not claimed, each with citations |
| `cells.py` | Pure aggregation: scenario states, outcomes, case cells, counts, lists of RP-6 |
| `run_core.py` | Loading of the registered runner, schedule, trials, masked twins, run identity (RP-9) |
| `run_wiki_subset.py` | Entry point: the plan file over the three configurations |
| `run_comparison.py` | Top-level script: corner (registered plan), baseline (registered plan), Wiki subset |
| `report.py` | Markdown report with the blocks RP-4 to RP-9 |
| `contract_check.py`, `stubs.py` | Contract self-check on three stub adapters (no real configuration produces a verdict) |
| `compute_digests.py`, `digests.json` | sha256 of every file here except `digests.json` |
| `DECISIONS.md` | Decisions and the borderline cases listed for the coordinator |
| `tests/` | Tests of this directory |

## Use

Environment: `SCN_HUB_DIR` (hub checkout holding `reference_profiles/`), the OPA binary passed as `--opa`, a Python with the pinned
`langgraph` and `cryptography`.

Self-check (no scenario is run on a real configuration):

    SCN_HUB_DIR=<hub> python3 -I comparators/runner/contract_check.py
    python3 -I comparators/runner/compute_digests.py --check
    python3 -I comparators/runner/declare_ocs_column.py --check

Plumbing run on renamed twins (verdicts are discarded inside the run, nothing about an outcome is stored or printed):

    SCN_HUB_DIR=<hub> python3 -I comparators/runner/run_comparison.py --opa <opa> --output <new dir> --plumbing \
      --twins corner=ID,ID --twins baseline=ID,ID --twins wiki=ID,ID

The comparison itself (all trials; needs the confirmation flag, a clean tree unless `--allow-dirty`, current digests and declarations):

    SCN_HUB_DIR=<hub> python3 -I comparators/runner/run_comparison.py --opa <opa> --output <new dir> \
      --confirm-real-run --candidate-id <id> [--gate-status <json>]

The Wiki subset alone: `run_wiki_subset.py --opa <opa> --output <new dir> --confirm-real-run`.
Report again from retained results: `run_comparison.py --report-only <results dir> --output <new dir>`.

If the plan file changes, regenerate and review the declarations with `declare_ocs_column.py --write`, then `compute_digests.py`.
Counts are read from the plan file; no scenario count is written into the code.
