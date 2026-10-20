# Matched monetary refund results — 16 October 2026

20/20 matched synthetic trials passed: ten variants, two repetitions each. This executes the monetary-refund stimulus from the supplied fixture, replacing the earlier insertion-only profile for this comparison. The earlier [36-trial result](bounded-exchange-2026-10-16.md) remains separate history.

| Check | Actual result |
|---|---|
| Matched initial state | synthetic-wallet:refund-demo-001, USD 100.00, version 1 |
| Matched action | Refund USD 10.00; effect:synthetic-refund-001; expected version 1 |
| Successful transition | USD 90.00, version 2; one effect; one consumed claim |
| Shared simulation clock | 2026-10-15 12:00/12:01/12:02 UTC issue/commit/observation |
| Matched trial battery | 20 PASS; valid, revoked, approval-withdrawn, policy-changed, evidence-stale, lost-ack-reconcile, duplicate-redelivery, observer-unavailable, changed-consequence, new-consequence-no-fresh-claim |
| Native runtime regression | 40 PASS, supported suite overlay |
| Qualification tooling | 114 PASS |
| Portable verifier | PASS under optimized Python; clean ZIP extraction PASS |
| Mutation controls | Altered bytes, rehashed contradictory readback, rewritten UNKNOWN and missing payload all rejected |
| Paid model calls | None |

The native Cognous AtomicLocalControlPlaneExecutor and AtomicAuthorityEffectDestination execute the effect. A test-only SQLite account adapter changes the balance/version inside that native transaction; this is not built-in production account management. Authority comes from the trusted native test fixture. Exact [sources, loaded hashes and trial identities](../results/comparisons/matched-refund-20261016/summary.json), [fixture](../results/comparisons/matched-refund-20261016/fixture.json), [JUnit](../results/comparisons/matched-refund-20261016/test-results.xml) and [shared commitment projections](../results/comparisons/matched-refund-20261016/comparison.json) are retained.

Runtime source is e20f92e104aba2ba6ad06120d8549c6170eaf63f; control-plane source a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5; qualification harness d4474fa8f9630b45305be26e039185f721150c94. All three source checkouts were pristine, including ignored files, before and after matched execution. Wall execution time is separate from simulated time.

D04 commits before acknowledgement loss. ACK_UNKNOWN remains historical, while the native timeout handler immediately observes applied state; this differs from the supplied external trajectory. After reopening the destination, the harness explicitly creates recovery attempt:d04:002 through native journal APIs, then invokes native read-only reconciliation. Native reconcile does not automatically create that attempt. One effect and one claim consumption remain; transaction-stage instrumentation records no second native effect transaction. Journal bookkeeping does write to the database. The post-commit/pre-retry snapshot has only attempt:d04:001. The observer-unavailable negative control injects TimeoutError before recovery observation and reports INCONCLUSIVE without redispatch; later restored validation readback remains separately labeled.

The recipient ZIP preserves native producer exports, before/postcommit/final standalone SQLite snapshots, complete manifest, portable verifier, original source notices, crosswalk and raw logs. The producer's legacy cogno-us/moltbot-safe namespace is preserved with an explicit mapping to the actual runtime source. Replay/Evidence Pack consumer interoperability is NOT RUN for this receipt family. The supplied external source files are not republished. [Archive identity](matched-refund-2026-10-16.archive.json) is separate from its self-excluding manifest.

Initial direct runtime regression invocation failed because a relocated fixture was absent. Supported source-layout assembly corrected it and all 40 tests passed. Initial tooling invocation lacked PyYAML; installation of qualification's hash-locked CI dependencies corrected it and all 114 tests passed. Both initial and corrected logs/results are retained; no runtime expectation was weakened.

This is a matched business-stimulus test against previously supplied external evidence, not a fresh two-system execution. The assessed architecture was not rerun. Authority encoding/expiry and immediate native timeout readback differ. The observer shares a trusted OS account. No institutional authority, independent operational witness, financial finality, power-loss recovery, distributed atomicity, whole-catalog acceptance, selected-stack qualification or production authorization is established. Native consequence commitments are architecture-specific and are not asserted equal across implementations.

Package status: READY TO SHARE for bounded technical review. No message or package has been sent to the counterparty.
