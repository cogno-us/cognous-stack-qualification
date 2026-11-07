# G3 independent qualification protocol

**Frozen before execution:** 2026-11-07T20:41:52Z  
**Assignment:** [stack qualification #273](https://github.com/cogno-us/cognous-stack-qualification/issues/273)  
**Frozen subject:** `cogno-us/cognous-stack-orchestrator@0c1fb8a108f24db889ed6d06af1814cb1f9be647`  
**Qualification baseline:** `84bb4c4b6639353deb3d680cbbfa8b3dec4d0a10`  
**Protocol status:** FROZEN. Observations and verdicts must not change this file.

## Appointment and independence declaration

The operator appointed this fresh GitHub Copilot coding-agent session directly as
the Independent Qualification Owner for issue #273. The actor is the `@copilot`
task session operating branch `copilot/vnext-g3-independent-qualification`,
initial head `fd6ca3f40f5eeda4a69be1a33271f8b6067725c5`. No more specific stable session
identifier is exposed in the environment.

This session had no G1, G1b, G2, or G3 builder/reviewer role and received no
builder-controlled oracle or verdict path. Existing source, developer tests,
reports, and issue history are untrusted evidence. Read-only subagents assisted
source-location reconnaissance only; they were expressly barred from defining
oracles, executing cases, or issuing verdicts. The qualification owner alone
authored and froze the following oracles.

Limits: process separation is established, but organizational and institutional
independence, human competence, and certification authority are not established.
The operator, product author, and repository owner may share organizational
control. This work is a bounded independent technical challenge, not formal
certification.

## Gate and isolation

- `source-environment.json` records the independently resolved subject and nine
  component commits, source archive hashes, tools, and environment.
- Source is obtained only through commit-addressed read-only GitHub archives,
  extracted under `/tmp/g3qual-sources`. No component checkout or lock is changed.
- Every effect database and workspace is created under a qualification-owned
  temporary root. No real customer, refund, payment, production service,
  credential, or public chain is used.
- No Registry/Ganache process is needed: Q3 must stop before Registry and uses a
  fail-if-called Registry spy. If that boundary is crossed, the case fails before
  any network operation. All network writes and external paid calls are forbidden;
  spending cap is USD 0.
- Fixed synthetic evaluation time is `2026-11-07T00:00:00Z`. Wall-clock process
  start/end times are retained separately.
- Rollback/disposal is deletion of the qualification-owned temporary root only.
  Unrelated sentinel directories are outside each run root and must survive.
- Raw stdout, stderr, JSON, SQLite queries, process timing, source paths, and
  hashes are retained without rewriting under `raw/`.

## Frozen cases and falsifiable oracles

Exactly these five cases are authorized.

### Q1 — source integrity

Launch clean subprocess probes with user site packages disabled and explicit
source roots. For every Python module actually used by Q2–Q5, retain resolved
`__file__`, file SHA-256, `sys.path`, and process command. Resolve the other
frozen components to archive members without importing them. Compare all roots
with the commit-addressed archive member inventory; reject extra, missing, or
changed files except recorded interpreter cache files. Place a same-named shadow
module outside the roots and prove no loaded module resolves to it.

**PASS iff** all ten commit-addressed archives match the frozen hashes; every
used module resolves inside its expected root; no shadow module loads; archive
inventory comparison finds no unexplained extra/missing/changed source; and no
revision is caller-asserted without the archive/commit binding. Otherwise FAIL;
an inaccessible source or unmeasurable identity is BLOCKED/NOT VERIFIED.

### Q2 — effect integrity

Run one authorized synthetic refund through native Control Plane decision and
Runtime execution into a disposable SQLite database. Before disposal,
independently query `effects`, `attempts`, and `attempt_events`, and retain the
schema and rows. Independently compare:

- proposal, execution envelope, result/export, and SQLite `effect_id`;
- proposal/envelope tenant, target, amount, unit, action/adapter and operation
  identity;
- SQLite target, amount, unit, state, `operation_digest`, effect and attempt
  cardinality;
- exported status, observed state, acknowledgement, and newly-executed flag.

The SQLite schema does not store tenant or action/adapter directly; those fields
must remain bound through the stored operation digest recomputed from the
envelope. **PASS iff** every available field and digest agrees, exactly one
effect is `applied`, and exactly one attempt is terminally executed. Effect-ID
equality alone is insufficient.

### Q3 — authority refusal

Build the synthetic G2 root-lineage input with its root grant revoked. Call the
native Control Plane decision once. Independent fail-if-called probes guard
Runtime, Replay, Pack, Verifier, Attestation, and Registry entry points; SQLite
write count and Registry-spy count are measured independently of driver labels.

**PASS iff** the native decision is `hold` with `grant_revoked`, every guarded
downstream count is zero, no Runtime database/effect/attempt exists, and the
Registry count is zero. Any downstream invocation or write is FAIL.

### Q4 — concurrency and disposal

Start two local invocation subprocesses behind a barrier so their execution
intervals overlap. Each receives a distinct owned root and database; sentinels
are placed in the peer and an unrelated directory. Retain process start/end
times, paths, rows, and cleanup observations. Then run one cleanup-failure probe
at the subject's cleanup call by forcing deletion of its owned root to fail.

**PASS iff** intervals overlap; both successful runs have one distinct effect;
neither touches the peer; successful owned roots are removed; the unrelated
directory survives; and the forced cleanup failure produces a nonzero process
result with the owned path identified. Silent suppression or an orphan with
success status is FAIL.

### Q5 — failure / UNKNOWN

Use the native Runtime `simulate="lost_ack"` injection. The SQLite commit occurs,
then acknowledgement raises. Independently inject failure of the sole
post-dispatch `observe_bound` call, after allowing the pre-dispatch observation,
so outcome remains ambiguous. Invoke execution exactly once; do not reconcile or
retry. Retain the raw exception-derived evidence, Runtime result, attempts/events,
and SQLite row.

**PASS iff** result status and observed state are `unknown`, acknowledged and
newly-executed are false, one attempt exists, one effect row exists, there is no
second dispatch/effect, and no output claims successful execution, absence,
custody, or retry safety. Any retry, duplicate, `executed` claim, or discarded
adverse evidence is FAIL.

## Adjudication

Each case receives only `PASS`, `FAIL`, `BLOCKED`, or `NOT VERIFIED`. Incomplete
evidence cannot pass. Five successful bounded cases would not establish
whole-stack certification, constitutional adoption, production authority, P1
acceptance, independent custody, or Architect acceptance.

The public Constitution source observed at
`87ce304130061e9cee8ca855854d625dddb3b805` is identifiable, but a project-local
adoption instrument and immutable issue-body revision for plan #281 were not
verified. Constitutional adoption is therefore `UNVERIFIED`.
