# G3 bounded independent qualification report

**Qualification issue:** [#273](https://github.com/cogno-us/cognous-stack-qualification/issues/273)  
**OCS Hub:** [cognous-open-control-stack#273](https://github.com/cogno-us/cognous-open-control-stack/issues/273)  
**Static plan:** [cognous-open-control-stack#281](https://github.com/cogno-us/cognous-open-control-stack/issues/281)  
**Frozen subject:** `cogno-us/cognous-stack-orchestrator@0c1fb8a108f24db889ed6d06af1814cb1f9be647`  
**Qualification harness revision:** `944a0a63e76bcd0ab0cc776677d631899c9a474e`  
**Run:** 2026-11-07T20:45:46Z–20:45:50Z, exit 1 (one execution only)

## Result

| Case | Independent verdict | Summary |
|---|---|---|
| Q1 source integrity | **NOT VERIFIED** | Archive and module paths matched, but the frozen comparison misclassified a tracked archive symlink as an extra file. The raw harness verdict remains FAIL. |
| Q2 effect integrity | **PASS** | One independently queried SQLite effect and attempt matched the proposal, operation digest, envelope, export, and result across all frozen fields. |
| Q3 authority refusal | **FAIL** | Native `hold`/`grant_revoked`; no Runtime/downstream/Registry invocation and no effect/attempt, but pre-decision setup wrote one `effective_grants_v1` SQLite row. |
| Q4 concurrency/disposal | **FAIL** | Processes genuinely overlapped, effects stayed in isolated databases, owned successful roots were removed, and the unrelated directory survived. Subject cleanup uses `ignore_errors=True`, so the injected cleanup failure was silent and left its owned root. |
| Q5 failure/UNKNOWN | **NOT VERIFIED** | The result was UNKNOWN with no retry, but the frozen injection intercepted a pre-dispatch observation rather than the intended post-commit observation. No effect committed, so the ambiguity oracle was not exercised. The raw harness verdict remains FAIL. |

**Independent assessment: qualification did not pass.** Two cases failed and two
were not verified. These results do not establish independently qualified
delivery, certification, adoption, custody, production authority, P1 acceptance,
or Architect acceptance. Stop for Architect disposition; do not merge as a
qualification acceptance claim.

## Independence and environment

The appointment, process separation, conflicts, limitations, exact sources,
environment, isolation, rollback, USD 0 cap, and frozen oracles are recorded in
[`PROTOCOL.md`](PROTOCOL.md) and
[`source-environment.json`](source-environment.json). The qualifier is a fresh
operator-appointed Copilot task session with no prior G1/G1b/G2/G3
builder/reviewer role. This establishes process separation only, not formal
organizational independence or certification competence.

The nine independently resolved component commit objects matched the subject
manifest. All ten commit-addressed archive hashes matched. Constitution source
was identifiable, but project-local adoption and an immutable plan-issue
revision were not verified; constitutional adoption remains **UNVERIFIED**.

## Q1 — source integrity: NOT VERIFIED

**Frozen expected outcome.** Every archive/tree matches, every used module loads
from its expected root, and no shadow or unexplained file is present.

**Observed.**

- All ten archives matched their frozen SHA-256.
- All seven Python probes succeeded and resolved inside their expected roots.
- The deliberately lower-priority `agent_control_plane` shadow did not load.
- Nine extracted trees compared exactly.
- Runtime comparison reported `CLAUDE.md` as extra. Adjudication established
  that it is the tracked archive symlink `CLAUDE.md -> AGENTS.md`; the comparison
  included followed symlinks in the extracted tree but only regular archive
  members in its expected set.

**Adjudication.** The raw FAIL is preserved. Because the frozen comparison had a
known asymmetric symlink treatment, the all-tree condition was not validly
measured and cannot be promoted to PASS. No loaded module escaped its pinned
root, but whole-tree source integrity is **NOT VERIFIED**.

**Evidence.** `raw/q1-source-integrity/result.json`. Material limitation:
commit-addressed archives have no Git index, so ignored/untracked state is
measured against archive members rather than `git status`.

## Q2 — effect integrity: PASS

**Frozen expected outcome.** One authorized synthetic execution; one applied
row and attempt; full field and operation-digest binding, not effect ID alone.

**Observed.** The native decision authorized. Independent SQLite queries found:

- one `effects` row in state `applied`;
- one attempt with terminal events `attempted`, `executed`;
- exact agreement for effect ID, target, amount `50.0`, unit `USD`;
- stored `operation_digest` equal to an independent envelope recomputation;
- proposal/envelope agreement for tenant `tenant-alpha`, target, amount, unit,
  action, and adapter;
- Runtime status `executed`, observed state `applied`, acknowledged true, and
  newly executed true.

**Evidence.** `raw/q2-effect-integrity/result.json`, including schemas, every
queried row, proposal, envelope, export, and digest. Limitation: tenant and
action/adapter are not direct columns in `effects`; their durable binding is the
operation digest.

## Q3 — authority refusal: FAIL

**Frozen expected outcome.** `hold` with `grant_revoked`; zero Runtime/downstream
invocations and zero SQLite/Registry writes.

**Observed.** The native decision was `hold` with `grant_revoked`. Independent
guards recorded zero Runtime, Replay, Pack, Verifier, Attestation, and Registry
calls. There were zero effects, attempts, attempt events, failures, and Registry
writes. However, the setup created the SQLite schema and inserted one active
`effective_grants_v1` row before the revoked decision.

**Adjudication.** This violates the frozen zero-SQLite-write oracle even though
there was no Runtime effect. **FAIL.**

**Evidence.** `raw/q3-authority-refusal/result.json`. Limitation: the pre-decision
row is authority setup, not an effect or Registry write; the stricter frozen
oracle intentionally distinguished those concepts.

## Q4 — concurrency and disposal: FAIL

**Frozen expected outcome.** Two overlapping isolated invocations; safe owned
cleanup; unrelated survival; cleanup failure observable.

**Observed.**

- two separate processes overlapped and returned zero;
- each isolated SQLite database contained one applied effect;
- both successful owned roots were removed;
- the unrelated sentinel survived;
- identical synthetic inputs produced the same deterministic effect ID in the
  two isolated databases, failing the frozen distinct-identity check;
- the subject contains `shutil.rmtree(WORK, ignore_errors=True)`;
- the cleanup-failure probe recorded `ignore_errors=true`, a success-status
  model, and the orphaned owned path.

**Adjudication.** Silent cleanup failure independently violates the oracle.
**FAIL.** Repeated deterministic effect identity across separate databases is
also preserved as an oracle failure, but is not independently claimed as a
duplicate external effect.

**Evidence.** `raw/q4-concurrency-disposal/result.json`, including process
intervals, rows, paths, cleanup call, stdout, and stderr. Limitation: cleanup
failure was injected at the subject's deletion call rather than through an
OS-level permission failure.

## Q5 — failure / UNKNOWN: NOT VERIFIED

**Frozen expected outcome.** Native lost acknowledgement after a committed row,
then unavailable post-dispatch observation; UNKNOWN, one effect, one attempt,
no retry, and retained adverse evidence.

**Observed.** Runtime returned `unknown`/`unknown`, acknowledged false,
newly-executed false, with one attempt and no retry/reconcile call. The
injection counted three `observe_bound` calls. It intercepted a pre-dispatch
observation and produced `destination_outcome_unknown:PermissionError`; no
effect row committed. Thus the intended post-commit ambiguity never occurred,
and the expected TimeoutError evidence was absent.

**Adjudication.** The raw FAIL is preserved. This is an instrumentation miss,
not evidence that the frozen post-commit behavior is safe or unsafe.
**NOT VERIFIED.**

**Evidence.** `raw/q5-failure-unknown/result.json`. No missing acknowledgement is
treated as proof of effect absence, execution, custody, or retry permission.

## Preserved adverse and limiting evidence

- The formal run was not retried.
- `raw/pytest.stdout.txt` preserves the four raw assertion failures.
- `raw/PREFLIGHT_DISCLOSURE.txt` discloses an earlier unretained setup probe and
  its stale-time refusal; it was not used for a case verdict.
- `raw/SHA256SUMS` binds the retained raw artifacts.
- No product source, component lock, contract, or workflow was changed.
