# Addendum - assessment of review findings and closure of the development qualification attempt

**Date:** 2026-11-07 · **PR head assessed:** `27a11afa6f80830580649585c1c785371c0546f5` · **Documentation only.**
**OCS Hub:** [cognous-open-control-stack#273](https://github.com/cogno-us/cognous-open-control-stack/issues/273) · **Static plan:** [#281](https://github.com/cogno-us/cognous-open-control-stack/issues/281)

## 1. Status, authorship and what this addendum does not do
The Architect directed closure of this development qualification attempt **without further independent testing**. This addendum was written under that direction by the G1-G3 builder session acting only as a documentation maintainer; it is **not** an independent assessment and the builder does not determine any verdict. It changes **no** verdict, frozen oracle, harness, test code, `source-environment.json`, `PROTOCOL.md` or raw evidence (`raw/SHA256SUMS` still binds the unchanged artifacts). The qualifier of record (the Copilot task session named in `PROTOCOL.md`) did not write this addendum and retains the right to contest or amend it. The six findings below come from the completed Copilot pull-request review of this head (review `5815219838`, comments `4503920999`, `4503921014`, `4503921024`, `4503921032`, `4503921039`, `4503921055`). Independent qualification remains **INCOMPLETE**.

## 2. Original verdicts (preserved, unchanged)
| Case | Original verdict |
|---|---|
| Q1 source integrity | NOT VERIFIED |
| Q2 effect integrity | PASS (reported) |
| Q3 authority refusal | FAIL |
| Q4 concurrency/disposal | FAIL |
| Q5 failure/UNKNOWN | NOT VERIFIED |

## 3. The six review findings
Severities are those stated in the Architect's directive relaying the Copilot review (HIGH: F1, F2; MEDIUM: F3-F6); the individual review comments themselves do not state a severity. Review `5815219838` is the submitted `COMMENTED` review on head `27a11afa`.
| # | Sev. | Where | Finding | Consequence for the retained result |
|---|---|---|---|---|
| F1 | HIGH | `harness.py` ~439 (Q2) | The value recorded as `independent_operation_digest` comes from the Runtime's own `snapshot_envelope(...).operation.digest`, so the digest binding tenant/action/adapter to SQLite is **not independently recomputed**; a shared digest defect would pass. | Q2's digest assurance is unmeasured independently. |
| F2 | HIGH | `harness.py` ~512 (Q2) | SQLite fields are compared with the proposal but **not** with `runtime_export['effects']` or the exported observation; result flags are checked only on the result object. An export with a wrong amount or status could pass. | Q2's export-to-SQLite agreement is unmeasured. |
| F3 | MED | `harness.py` ~154 (Q1) | The path-forced provenance probes run in **separate interpreters**, not in the pytest process or the Q4 workers that executed the cases, and omit used modules (for example `g2_driver`, `engine.control_plane_adapter`); an existing `sys.modules` entry can also bypass the import-path check. | Per-execution provenance is not established; Q1 stays NOT VERIFIED. |
| F4 | MED | `harness.py` ~548 (Q3) | The non-invocation counters are initialized after setup and **never updated**; `registry_write_spy` is a literal zero. The non-invocation checks therefore cannot fail. | Q3's "zero downstream invocations" is **unmeasured** (insufficiently instrumented). |
| F5 | MED | `harness.py` ~647 (Q4) | The cleanup-failure probe calls a **harness-local stub** with `ignore_errors=True` and records a hard-coded success status; successful disposal (`harness.py` ~595) also uses harness-owned cleanup. | Q4 did not exercise the orchestrator's workspace lifecycle. |
| F6 | MED | `prepare_sources.py` ~61 | Source preparation rejects **every** symlink, including the tracked relative link `CLAUDE.md -> AGENTS.md` in the frozen Runtime archive, so a clean acquisition exits before publishing `src/runtime`; the retained run cannot be reproduced with this helper. | Reproducibility gap (related to the Q1 symlink-handling limitation). |

## 4. Effect on each case (verdicts unchanged; their meaning is qualified)
- **Q2 - the reported PASS is limited by F1 and F2.** It records only that no discrepancy was found *within the measurements actually made* (one SQLite effect/attempt agreed with the proposal and the Runtime-derived envelope). It must **not** be read as an unqualified independent assurance of effect integrity: the independent recomputation of the operation digest and the field-by-field comparison of the exports (effects, observation, result flags) with SQLite are **NOT VERIFIED**.
- **Q3 - FAIL stands.** Its non-invocation evidence is **insufficiently instrumented** (F4): the statement in this report that independent guards recorded zero Runtime/Replay/Pack/Verifier/Attestation/Registry calls reflects counters that were never wired to count, and `registry_write_spy` is a literal.
- **Q4 - FAIL stands.** The original cleanup-failure probe **did not exercise the product lifecycle** (F5). Its positive observations about owned-root removal were produced by harness-owned cleanup as well. The preserved separate oracle failure (identical deterministic effect ID in two isolated databases) is unaffected by this addendum.
- **Q1 - NOT VERIFIED stands** (F3, F6 and the original symlink asymmetry).
- **Q5 - NOT VERIFIED stands** (injection point; unrelated to F1-F6).

## 5. Source revisions - original versus remediation
All five cases evaluated the **original G3 revision** `cogno-us/cognous-stack-orchestrator@0c1fb8a108f24db889ed6d06af1814cb1f9be647` (frozen subject). The later Q4 remediation was merged separately as `67c49e27127d3be259fcb5f6823f107191d56579` (merge of orchestrator PR #154, head `559ce9a904fa766d7bf525290045ff7653c7de1d`; its diff against `0c1fb8a1` is confined to `tests/manual_contract/g3_refund/`: the `g3_capture.py` tail/imports, new `g3_cleanup.py` and `test_g3_cleanup.py`, and developer evidence). **No qualification result in this PR was obtained on `67c49e27`.** The Q4 FAIL describes `0c1fb8a1` only and is not re-adjudicated here; the developer checks that accompany the remediation (7 passed) are developer evidence, not independent qualification. No Q1-Q5 result transfers across revisions.

## 6. Unresolved assurance requirements for any future qualification
1. Per-execution source provenance measured inside the case processes themselves, covering every module actually used and detecting `sys.modules` bypass (F3), plus a symlink-symmetric frozen tree-comparison oracle (the original Q1 comparison counted followed symlinks in the extracted tree but only regular archive members in its expected set, which is why `CLAUDE.md -> AGENTS.md` was reported as extra) and source preparation that accepts safe tracked relative symlinks (F6).
2. An independent recomputation of the operation digest (F1) and a field-by-field comparison of the exported effects, observation and result flags against SQLite (F2), including tenant/action/adapter binding.
3. Real counting or fail-if-called instrumentation for Runtime, Replay, Pack, Verifier, Attestation and Registry on a HOLD, with the Registry write measured rather than assumed (F4); a decision on the pre-decision `effective_grants_v1` row that produced the Q3 FAIL.
4. A cleanup probe that executes the product's workspace lifecycle, including an injected removal failure and a disposal measured independently of harness cleanup (F5); a reasoned oracle for repeated deterministic effect identity across isolated databases.
5. A post-commit lost-acknowledgement injection that actually produces the intended ambiguity (Q5), with no inference of effect absence from a missing acknowledgement.
6. Qualification of the remediated revision `67c49e27127d3be259fcb5f6823f107191d56579` (or its successor) as a separate subject.
7. Formal organizational independence and competence of the qualifier, project-local Engineering Constitution adoption (currently **UNVERIFIED**), and everything outside this chain's scope (authenticated institutional authority, durable custody, consensus finality, Verifier acceptance, production authority, P1 acceptance).

## 7. Closure
**No further testing is authorized in this development closeout.** This attempt is closed as **incomplete**; the original results, adverse evidence and review findings are retained. Merging this documentation does not confer qualification, certification, adoption or acceptance; those remain reserved to competent authority.

**Final status (as directed by the Architect and recorded in the OCS Hub #273 closeouts; this addendum does not itself establish integration):** G1-G3 DEVELOPMENT-INTEGRATED · G3 Q4 REMEDIATION MERGED (`67c49e27`) · INDEPENDENT QUALIFICATION INCOMPLETE · VERIFIER ALPHA/HOLD · P1-EXIT BLOCKED/DEFERRED · CONSTITUTION ADOPTION UNVERIFIED.
