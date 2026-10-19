# Evidence check hardening probes

Probes for a round of input validation, stricter binding and result consistency work across the Cognous component repositories.
They are written first: each one states a property the pinned head of a component should hold. They run locally with pytest against
read-only checkouts and are not part of any delegated workflow or qualification run.

## Convention

- A **control** is an unmarked test. It passes at the pinned head and must keep passing after the change.
- A **probe** is marked `xfail(strict=True)` with the reason `pending hardening` (see `_support.pending`). It fails at the pinned head, so
  a run is green now. When the matching change lands the probe passes, the strict mark turns that into a failure, and the mark is
  removed. Only an assertion failure counts as the expected failure; an import error or any other exception is a real failure.
- A probe whose property the component still does not hold, and that stays a documented limit, is marked `xfail(strict=True)` with a
  reason that starts `known limit:` and states the limit in neutral words (see `_support.known_limit`). Each is listed with its
  component and property in [KNOWN_LIMITS.md](KNOWN_LIMITS.md). A probe that has passed after a change carries no mark and runs as
  an ordinary control.
- Run with `--runxfail` to see the probes fail at the pinned head.
- Probes never write inside a checkout. Where a probe needs to modify a tree it builds a throw-away copy or repository.

## Running

Set one environment variable per checkout, to the repository root. A module whose variables are unset is not collected (the
two-implementation modules need at least one of theirs), so a missing checkout gives no result rather than a pass.

| Variable | Component | Pinned head | Module |
|---|---|---|---|
| `PROBE2_ODES_DIR` | open-decision-evidence-standard | `4bf12128` | journal rules, const typing, time grammar |
| `PROBE2_VERIFIER_DIR` | cognous-open-control-stack-verifier | `dc09a98f` | journal rules, ledger and binding probes, time grammar |
| `PROBE2_REPLAY_DIR` | cognous-replay-bundle | `2a7963b1` | folds, bounded scan, time grammar |
| `PROBE2_CONTROL_PLANE_DIR` | cognous-control-plane | `2bac7875` | stored copies, time grammar, runtime flow |
| `PROBE2_MANIFEST_DIR` | cognous-action-manifest | `ff549082` | proposal limits |
| `PROBE2_RUNTIME_DIR` | cognous-execution-runtime | `c4a05883` | result consistency after commit, matrix statement |
| `PROBE2_ERGONOMICS_DIR` | cognous-open-control-stack-ergonomics | `e996a53f` | diagnostics file |
| `PROBE2_PACK_DIR` | cognous-governance-evidence-pack | `80e24650` | installed distribution check |
| `PROBE2_EXCHANGE_DIR` | cognous-governed-exchange | `bf314f38` | strict source check |

```bash
export PROBE2_ODES_DIR=/path/to/open-decision-evidence-standard   # and so on
python -m pytest -q -p no:cacheprovider suites/fix2-probes
```

Install each component's own dependencies in the interpreter that runs the probes. Python 3.13 and 3.14 are both used.

## Files

- `_support.py`: the strict mark, per-implementation parameters, loaders for the reference validators and fixtures.
- `_matrix.py`: the producer result matrix (status, flags, observation) as a pure function; `test_runtime_probes.py` checks it
  against the runtime function it restates.
- `KNOWN_LIMITS.md`: the probes kept as strict expected failures, with component, property and reason.
- `test_*_probes.py`: one module per component, or per rule family where two implementations carry the same rules.
