# Observer specification

## Route

The executor and the observer both access the destination through
`engine.effective_grant.EffectiveGrantDestination`, which is a thin wrapper around a
single local SQLite file (`tmp_path/'sqlite'`).

- Writer entry: `EffectiveGrantDestination.commit(snapshot, ...)` opens the SQLite
  file in the executor process and inserts the committed effect row.
- Reader entry: `EffectiveGrantDestination.observe(effect_id)` opens the **same**
  SQLite file in the **same** process and returns `{state, version, …}`. It also
  exposes `effect_count(grant_id)`.
- Access separation: **none** at the operating-system level. Both reader and writer
  run under the same OS user, same working directory, same Python process, and
  share the destination Python object.

## Trust boundary (declared explicitly, not papered over)

A direct SQLite readback via the same in-process destination object is a **local
synthetic oracle**. It is useful as:

- a check that the executor **did** or **did not** reach the commit code path;
- a check that effect multiplicity is zero, one, or more;
- a check that durable row state matches the executor's acknowledgement.

It is **not** an independent operational witness. It cannot distinguish between
"the writer committed and the state is honest" and "the writer committed and the
reader is colluding with the writer in the same process". That distinction
requires a separate reader principal, credential and access path, which this
frozen reference does not implement.

The bounded-comparison process already states this explicitly:

> A separate query in the same trusted process does not establish independent
> operational observation.

This spec adopts that limit without softening it.

## Horizon

Observations occur immediately after the executor returns and once more at the end
of the test. No delayed-commit window is observed; a commitment that arrives after
the test teardown cannot be detected by this observer, and the manifest will mark
the horizon explicitly.

## What the observer cannot exclude

- An out-of-process writer that bypassed the executor path entirely.
- A delayed commit that lands after the horizon.
- A corrupt SQLite WAL or storage layer failure (no `PRAGMA integrity_check` is run
  against the live database during execution; it is only invoked on the exported
  snapshot in Phase 4).
- Any effect visible only to an external principal (there is no external principal).

## Writer-entry telemetry (Phase 1 addition, allowed by process)

The bounded-comparison process explicitly contemplates adding only the missing
`writer-entry`, `intervention-consumption` and `observer` telemetry. The frozen
reference already records:

- Writer entry: `result.attempted` on the `ExecutionResult`, plus the
  `effect_count(grant_id)` observation.
- Intervention consumption: `resolution_check_event` entries (phase = `input` on the
  grant source) plus the resolver call that is paused and resumed around the
  injection point in `produce()`.
- Observer: `dest.observe(effect_id)` and `destination-observation.json` artifact.

No new telemetry is required to execute D01, D03 (revoked variant) or C07 (race).
If approved to proceed, Phase 1 will **re-use** these records and only add a run-level
`observer.json` that re-serializes the already-produced data behind an explicit
"local-synthetic-oracle" label, so the package honours Evelyne-Claudia's five
categories without inventing new facts.
