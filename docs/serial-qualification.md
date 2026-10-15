# Serial qualification packet

The T0 increment executes a frozen subset of native local assertions and maintains the [canonical qualification dashboard](qualification-dashboard.md#serial-qualification-orchestration). Its canonical orchestration state is [qualification/orchestration-state.json](../qualification/orchestration-state.json). It does not replace the scenario catalog or silently promote its 40 cases to accepted status.

## Execution order

Contracts → native deterministic harness → calibrated evaluator → actual-agent configuration gate → integrated evidence. All work is serial. Human participation is removed; human oversight effectiveness is **NOT EVALUATED**.

The [frozen plan](../qualification/serial/plan.json) implements 18 variants, each with two diagnostic repetitions. It uses the hub's real `ProtectedDestination` and `AssuranceRuntime` public admission paths via their existing synthetic fixtures. No production runtime is rewritten and no selected component pin changes.

## Reproduce

Use a pristine qualification checkout, including ignored files, and a separate pristine hub checkout at the exact SHA recorded in the result. Output must be outside both checkouts. No overlays are required for these native tests.

```bash
python -m pip install -r tools/requirements-serial.txt
PYTHONDONTWRITEBYTECODE=1 python tools/run_serial_qualification.py \
  --hub /absolute/path/to/pristine-hub \
  --output /absolute/path/to/new-result-directory
python tools/serial_orchestration.py --check --hub /absolute/path/to/pristine-hub
python tools/build_dashboard.py --check-markdown
```

`record.json` retains native admission responses, complete native audit chains, independent readbacks, effect occurrence counts, stable effect and separate attempt IDs, scenario commitments and exact loaded source identities. `plan.json` is committed by hash; summary counts are recomputed. Failed or inconclusive runs return nonzero and their native records remain available. Do not overwrite previous result directories.

## Configuration and boundary checkpoint

The profile is explicitly nonselected. Only the named native hub modules and fixture helpers are loaded. The selected lock is retained as source context; its components are not loaded or qualified by this run. Native source paths and hashes are recorded, with the qualification code SHA and dependency versions.

ProtectedDestination correction occurs at its current-authority checks inside the serialized SQLite admission transaction. Commitment occurs at transaction commit. The approval runtime binds review to its queued proposal and rechecks it before its local SQLite effect. Stop invalidates the approval; the observed refusal is `APPROVAL_UNAVAILABLE`. These are local fixture boundaries, not distributed authority claims.

The observer runs in a separate process, has no signing keys passed to it and opens SQLite with `mode=ro`; an attempted INSERT must fail. Its snapshot includes all fixture effects and a digest of relevant objects and effects after synchronous apply returns. It shares the trusted OS account and is not an independent operational principal. The observation horizon is synchronous local completion; asynchronous or delayed external writers are unsupported. The runtime has no arbitrary shell/network callback adapter and the prohibited operation is actively refused; host network/process containment is not established.

Lost acknowledgement is injected after the native synchronous apply commits. The first attempt remains UNKNOWN in the sidecar. Reopening the store and submitting a distinct attempt for the same effect demonstrates native deduplication, not writer-free reconciliation, process-crash recovery, power-loss recovery or financial settlement.

## Native mapping and losses

| Requirement | Actual native source | Qualification mapping or gap |
|---|---|---|
| Proposal and request binding | Fixture signed command body and native `request_digest` | Sidecar request digest, native audit row and effect ID; no new upstream field asserted |
| Authority and approval | Destination grant/fence and approval-runtime proposal/review objects | Native audit and initial/final object commitments; no institutional authority claim |
| Invocation | Public `apply` and dispatch wrapper | Dispatch attempt only; private writer-entry absence is not proved |
| Effect and observation | Native effects table, separate read-only process | Full effect rows, occurrence count, business-state digest, read-only negative control |
| Reconciliation | Native duplicate result after store reopen | Same effect, distinct attempt; original UNKNOWN retained |
| Replay and Evidence Pack | No verified adapter for these two native local receipt families | NOT RUN; no sidecar relabeling as native producer output |
| Agent behavior | OpenAI GPT-6.1 Sol, bounded native tool loop | 25/25 named pilot trials passed; [completed pilot evidence](#completed-bounded-openai-pilot); broader agent coverage remains unqualified |
| Human effectiveness | Participant exercise removed | NOT EVALUATED |

Schema [v2](../schemas/trajectory-evidence-v2.schema.json) is a qualification-only index into native evidence. The existing v1 workflow contract is unchanged and still requires empty scenario results. Hashes identify bytes, not authenticity, truth or independent custody.

## Coverage and remaining work

D01, D02, D03, D04, D09 and H01 have named local variants. This does not establish every required variant or obligation in those catalog scenarios. In particular, institutional policy replacement, exact payload grant binding, tenant isolation and commit races require their actual supported profiles. D05 is not applicable to the indivisible local insert. D06 numerical resource qualification and D07 restore characterization remain in existing source/migrated suites and are not accepted by this narrow record. D08 export qualification remains unexecuted for this native record family.

Evaluator calibration includes clean controls and seeded missing approval, prohibited access, duplicate effect, fabricated completion, dropped handoff constraint and corrupted lineage. Missing observation is separately required to produce INCONCLUSIVE; a known violation still takes precedence. Calibration flags are test fixtures, not captured human reasoning or model behavior.

The completed pilot below exercises five named OpenAI variants, including agent approval behavior. It does not qualify all A01–A06 obligations. The earlier [pilot proposal](../qualification/serial/agent-pilot.json) and frozen native plan retain their historical configuration/NOT RUN statements; they are not current blockers or rewritten model evidence. Memory/compaction, tenant-memory isolation and multi-agent handoff remain NOT RUN. Missing access must never trigger simulated replacement or secret collection.

Every local variant inherits immutable scenario commitments, provenance and adaptation license from the catalog. Original implementation is Apache-2.0. Native source code remains in its owning repository; no Wiki text or external methodology is copied into this increment. Weekly upstream Wiki synchronization and its CC BY-SA boundaries are unchanged.

## Deferred closeout

After current engineering/testing finishes, before final publication: inspect exact proposed package bytes for credentials, personal/customer data and proprietary Cognous/ISS content; verify owner-approved exclusions, redistribution rights and original notices; reconcile live issues/PRs against satisfied requirements and transfer genuine residual work. This increment records that work without executing it or creating an automation. Publication and production decisions remain with their owners.

## Retained command correction

An additional regression invocation from the qualification working directory failed collection because the hub module path was absent. Its log/XML are retained as `native-collection-failure` artifacts. Rerunning from the hub checkout with its native import context passed 117 tests and 16 subtests. This setup failure did not change runtime behavior or the 36 trial verdicts.

## Completed bounded OpenAI pilot

[PR #17](https://github.com/cogno-us/cognous-stack-qualification/pull/17) merged
as `4c817a5eaa53c51e91322f8204864f039ab11d1f`.
[Workflow run 38821035491](https://github.com/cogno-us/cognous-stack-qualification/actions/runs/38821035491)
completed successfully at that qualification revision with native hub
`4bb101ca6dd5ee8f821bc44a7af935b5e389562e`. The retained manifest records
**25/25 PASS**, zero unexecuted trials: five repetitions each of routine,
indirect-injection, tool-timeout, approval-denied and approval-withdrawn.
These are synthetic diagnostic assertions using actual OpenAI GPT-6.1 Sol calls,
not full catalog acceptance, broad model reliability or full selected-stack qualification.

The [retained artifact](https://github.com/cogno-us/cognous-stack-qualification/actions/runs/38821035491/artifacts/12013785164)
contains the final manifest, campaign ledger and prior failed-attempt archive.
Downloaded ZIP SHA-256 was verified against GitHub:
`4f9ce2a5f4df1431c669f67f5e25d8564682d9e0d3b70827dbb561ad5c507154`.
The manifest SHA-256 is
`187a29385ac2123bd1f4c86421712da5950f8973cfd69bd4ecb540df79deaeb8`.
Member commitments and source/accounting metadata are recorded in
[orchestration state](../qualification/orchestration-state.json).
No evidence bytes, ledger, prior attempt or historical result are overwritten or
republished by this dashboard reconciliation. Actions expiry is **2027-01-13**;
a hash/link alone does not preserve the artifact beyond expiry.

Client accounting records **USD 0.17804 charged or reserved** against the
USD 19.908 campaign cap: 95 SETTLED requests totaling USD 0.10756 and one
RESERVED request of USD 0.07048. The unresolved reservation is retained; these
figures are not a provider invoice guarantee. Prior campaign/error accounting
remains in its retained ledger/archive. **No paid rerun is authorized or needed
for this closeout.** This update only reads existing evidence.

Testing design is complete within this bounded scope. Native receipt export to
Replay/Evidence Pack remains unverified. The read-only observer still shares a
trusted OS account; operational observer independence and production containment
remain unestablished. Human oversight effectiveness is NOT EVALUATED. The
separate active PRP campaign is outside this dashboard reconciliation; no PRP
inputs, trials or results are changed. Final security/package review remains
deferred until engineering/testing finish, followed by publication acceptance.
Release and production HOLD remain unchanged.
