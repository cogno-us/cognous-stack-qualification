# Historical test-result commentary: cognous-open-control-stack

Public source: [`README.md`](https://github.com/cogno-us/cognous-open-control-stack/blob/c25b30ccb529d086275b882204859267f1ffe891/README.md) at commit `c25b30ccb529d086275b882204859267f1ffe891`, Git blob `a3ded26a7db080b7daf731de7738e07fae3a2c5f`.

Only test-result excerpts or bounded summaries are relocated here. Unrelated evaluator, security, license, release and implementation material stays at its source. These are historical statements, not a new test run, validation, current selection claim or deployment approval. Review the exact source for full context and applicable license/notice terms.

Remove duplicated qualification commentary, stale snapshot reporting and result totals; retain operational instructions, interfaces and limitations.

## Recorded test commentary


| Accepted evidence | What was demonstrated | Scope that remains outside the claim |
|---|---|---|
| [Historical persistence-generation qualification](https://github.com/cogno-us/cognous-open-control-stack/blob/c25b30ccb529d086275b882204859267f1ffe891/README.md) | Two repetitions of 915 Python tests, 35 matrix entries satisfying their gates, repeatable representative outcomes and 120 separate mocked OpenShell tests | Production authentication, independent real-world verification and live OpenShell |
| [Shared-store persistence](https://github.com/cogno-us/cognous-control-plane/blob/248d899634d9db3518e831bc7ab568a48733f825/docs/record-store-persistence.md) | Cooperating same-host record transactions preserve supported concurrent writes and process-interruption behavior on documented local Linux filesystems | Whole-workflow atomicity, cross-host persistence and remote exactly-once delivery |
| [Recovery qualification](https://github.com/cogno-us/cognous-open-control-stack/blob/c25b30ccb529d086275b882204859267f1ffe891/README.md) | Same-effect continuity, original-effect reconciliation, accepted/rejected observations and changed-authority denial separated from historical execution | Retry permission from absence, rollback, cancellation or remote finality |
| [Protected-worker campaign](https://github.com/cogno-us/cognous-open-control-stack/blob/c25b30ccb529d086275b882204859267f1ffe891/README.md) | Twelve isolated cases and 17 verifier tests passed on the recorded Ubuntu 22.04/bubblewrap environment | OpenShell, arbitrary agents, production credentials or general production non-bypassability |

### Protected-worker qualification

The historical qualified profile uses a fixed synthetic worker under separate mount, PID and network namespaces. A trusted host owns authority, execution and the destination; direct destination reads, canary hashes and a controlled host-loopback sink check the worker's claims and attempted alternate paths. One authorized control must produce exactly one expected effect; payload, target and adapter substitutions, missing authority and forged success produce none.

Qualification applies to **Ubuntu 22.04.5, Linux 6.8.0-1064-azure, bubblewrap 0.6.1 and Python 3.11.16**, six scenarios repeated twice. It does not demonstrate model prompt-injection resistance or arbitrary-program confinement. The earlier Ubuntu 24.04 campaign remains blocked, with its evidence preserved. See the [profile and prerequisites](https://github.com/cogno-us/cognous-open-control-stack/blob/c25b30ccb529d086275b882204859267f1ffe891/README.md), [actual campaign](https://github.com/cogno-us/cognous-open-control-stack/blob/c25b30ccb529d086275b882204859267f1ffe891/README.md) and [source/CI provenance](https://github.com/cogno-us/cognous-open-control-stack/blob/c25b30ccb529d086275b882204859267f1ffe891/README.md).


The optional same-host authority/effect profile has merged through [Control Plane PR #12](https://github.com/cogno-us/cognous-control-plane/pull/12), [Execution Runtime PR #25](https://github.com/cogno-us/cognous-execution-runtime/pull/25) and [hub PR #16](https://github.com/cogno-us/cognous-open-control-stack/pull/16). [Qualification run 37682165860](https://github.com/cogno-us/cognous-open-control-stack/actions/runs/37682165860) passed 73 tests against its exact reviewed source revisions. It orders cooperating authority mutations, claim and budget consumption, and the protected synthetic effect through the declared trusted handoff and authoritative SQLite transaction.
