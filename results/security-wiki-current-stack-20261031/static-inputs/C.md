# Worker C (delivery id C): runtime and host security, OCS-SECURITY-COVERAGE-01

Read-only static-source plus existing-evidence assessment. Nothing was run, written to a checkout, or modified. Not a certification, not Q7/Tier 1, not release or production readiness. No CVSS.
Heads read: execution-runtime f7a55e2a, control-plane b19c47dd, stack-orchestrator 721f4406, hub dd522c50 (tools/mvp_ingress, read for IPC/peer-cred), wiki-derived suite at wt-wiki 86f78ea3.
MVP pins differ: CP 7a4bcd40 (head b19c47dd), Runtime c5e97e87 (head f7a55e2a). Shallow clones: I could not diff head against the MVP pins. The only comparable reference is the frozen ec728da6 runtime. Against it, safe_executor.py, local_authority_effect_recovery.py and both operation_identity_* files are byte-identical to head. local_authority_effect.py and atomic_local_control_plane_executor.py differ (F-A1 pin step, selection guard, successor profile, approval-revocation table). Some of those differences may already be in c5e97e87 (NC1-04 needs approval-revocation), so I do not attribute them to head versus MVP.
Hub ingress: all 7 files in tools/mvp_ingress at dd522c50 are byte-identical to the baseline fixture in wt-wiki/suites/mvp-chain/kwflow_fixtures/baseline (diff run). I did not compare against hub c897266b directly.

## 1. Evidence classification

VIEW A, DIRECTLY-EXECUTED (run 41169692260, host-evidence + mvp-chain), bounded 2751/0660 synthetic profile (ruling D3), hosted Azure runner, kernel 7.0.0-1017-azure, ext4:
- Ids and groups (environment-record.json): ingress 999:987, client 997:986 (groups 985,986), outsider 65533. All unprivileged, CapEff 0 for ingress, client and outsider.
- IPC (ipc / NC4-03c): IPC dir 2751 owner 999 group 985, outside the state tree. Socket 0660 owner 999 group 985. Outsider: connect EACCES, listdir EACCES, stat of the known name OK (accepted residual, a limit). Group member client connects.
- Peer credentials (NC4-03d, ipc.peer_credentials): SO_PEERCRED from a real connection matches the ingress pid/uid/gid. Allowlist enforced by the pinned server.serve against a STUB CORE (not the live core). A non-allowlisted group member gets PEER_NOT_ALLOWED. An empty allowlist is refused.
- Yama (NC4-03a, yama-record.json): ptrace_scope 1 as found, action none. The row records only the number; "facts" is empty.
- State tree (filesystem.*): 17 entries, dirs 0700, files 0600, one owner, no ACLs on 25 paths, ancestors not group/other-writable.
- Client probes (qualification.client_denied_*): kill(0) on the ingress, open of /proc/<pid>/environ and /proc/<pid>/mem, listdir/open/stat/unlink in the state dir all denied. NC4-02: 232 adversarial inputs refused, no table changed. The baseline control (same actions without the boundary) succeeded, which shows the boundary is OS permissions, not the destination DB.
- Crash (NC2-07, nc_process_kill): real SIGKILL at 3 seams (after_begin, after_effect_insert_before_commit, after_commit). A fresh process reopens the on-disk store. Pre-commit: 0 effect/attempt/receipt/operation rows, claim still "issued", reconcile hold/no_durable_effect_for_claim, retry_eligible false, re-presented claim executes exactly once, third presentation denied. Post-commit: 1 effect, claim consumed, reconcile applied, re-presentation denied and not attempted.
- Lost ack: NC2-01..05 executor-level (simulate='lost_ack'); NC2-06 ingress-level via an owner-side hook.
- Duplicate: NC3-01..03.
- Pruning (NC3-04): documented limit, row records "not judged". With operations rows removed, the CP no longer holds. Destination refuses operation_already_committed. One effect remains.
- Custody failure: NC6-02/03.
- Source-level (STATIC): NC4-03 AST, KL-01.
- Not isolated by the evidence: NC4-04 is launcher argv only.

VIEW A caveats:
- The ingress under test was launched through a harness wrapper (`python -I -B -c ...` pre-exec plus an observation-only sitecustomize probe, MVP_FAULT_* env), not the plain launcher command. The environment-record process_identity.cmdline shows this.
- The capture harness ran as root with full caps.
- NC2-07 killed an executor child, not the ingress process and not the CP process.
- The harness's own docstring (suites/mvp-chain/_killharness.py:36-38) states what is not exercised: power loss / OS crash, kills during Replay/Pack/Verifier, kill of the Control Plane process, filesystem corruption, kill during claim provisioning.

VIEW B (heads): STATIC-SOURCE only. Repo test files exist (runtime tests/test_crashed_holder.py, test_atomic_post_commit_*.py, host_pin/test_installer_crash_recovery.py, host_pin/test_installer_os_isolation.py; orchestrator tests/integration/workflow_store/test_workflow_store_crash.py). I did not run them. I found no CI results for them in the files I read, so their execution status at these heads is UNAVAILABLE. No MVP qualification transfers.

ORCHESTRATOR: UNTESTED at VIEW A (not in the tuple). Static only.

Wiki run: /home/claude/wiki-run/junit-wiki-derived.xml was absent when I looked; results UNAVAILABLE.

## 2. Findings

None CRITICAL or HIGH found. No unauthorized-filesystem-access path was found past the documented trusted-host assumption.
Column order: id | severity | status | repo@sha file:line | boundary | consequence | existing mitigation | confidence | code change? | blocks?

| C-01 | MEDIUM | VERIFIED (test asserts it) | wt-wiki@86f78ea3 suites/wiki-derived/test_wp_c_budget_stop_recovery.py (`test_wiki_l15_019_restore_of_an_older_backup_readmits_later_effects_known_limit`) | backup/restore of local SQLite, no external anchor | restoring an OLDER consistent backup returns claims/budgets to the earlier state and re-admits effects: the same effect_id was committed twice over the system's life (witness shows 4 commits, budget cap 2) | none in code; limit stated in applicability not_claimed (TC-L15-019); optional CP witness-digest/0.1 (witness.py) is opt-in and unused in MVP | HIGH on the mechanism, STATIC+frozen-ref (not run by me) | design (external anchor), not a bug fix | no for bounded publication; already within HOLD; any production claim needs an anchor |
| C-02 | LOW | VERIFIED | runtime@f7a55e2a engine/c8_source_evidence.py:49-50 | stop journal integrity | docstring says "Append-only" but the table has no UPDATE/DELETE triggers (the pin store, recovery ledger and registry tables do); requester/reason are unauthenticated (acknowledged in the TC-L06-022 not_claimed). Rewrite of stop history by anyone with file write | owner-only file permissions of the deployment | HIGH | docstring or trigger | no |
| C-03 | LOW | VERIFIED (source), HYPOTHETICAL (runtime impact) | hub@dd522c50 tools/mvp_ingress/core.py:35-49 and server.py:219 | ingress crash/restart | a request id reserved 'inflight' stays burned after kill -9 or SIGTERM (SystemExit mid-request). No startup scan. REPLAY returns no stored outcome, so a client that lost the ack cannot learn it via the ingress; the operator must reconcile out of band. No double execution (fail-safe) | documented operator procedure in BOUNDARY.md; reviewer-observed kill -9 runs (HISTORICAL, in BOUNDARY.md only) | MEDIUM | optional status/reconcile op | no |
| C-04 | LOW | HYPOTHETICAL | hub@dd522c50 server.py:28,54,160 | IPC availability | single-threaded serial accept: an allowlisted client can hold the server up to READ_TIMEOUT 5 s per connection, a non-allowlisted socket-group member ~0.5 s drain per connection. Availability only, inside the group trust boundary | READ_TIMEOUT total deadline, drain cap, backlog 8 | MEDIUM | no | no |
| C-05 | LOW | VERIFIED (record), HYPOTHETICAL (impact) | evidence run 41169692260 environment-record.json process_identity.ingress_process, isolation_limits | process hardening | ingress has CapBnd 000001ffffffffff, no_new_privs 0, seccomp 0, no LSM profile recorded; unprivileged userns enabled (unprivileged_userns_clone 1, max 58121); /proc without hidepid (cmdline visible). A local setuid binary or kernel bug would be outside the evidence. core_pattern/ulimit -c not recorded | uid separation, CapEff/CapPrm 0, denied /proc/mem and environ, Yama 1 | HIGH that it is unrecorded or unset | host profile (NoNewPrivs, bounding set drop, seccomp/AppArmor) | no, for the bounded D3 profile |
| C-06 | LOW | VERIFIED | runtime@f7a55e2a engine/openshell_environment.py:188 | CLI digest check then exec | sha256 of the CLI binary is read and compared, then the path is executed later (check/use gap); needs write access to the binary path | pinned digest, fixed argv, killpg cleanup (:158-163 region), 1 MiB output cap | MEDIUM | open fd or fexecve | no (OpenShell deferred, live behaviour unverified) |
| C-07 | LOW | VERIFIED | runtime@f7a55e2a engine/safe_executor.py:466-479 | destination DB path | self-documented residual TOCTOU (no dirfd/openat); `exists() and is_symlink()` skips a dangling link, but the later escape check (:477-479) still refuses an outside target. sqlite3.connect creates DB with umask-derived mode (no chmod in engine/): 0644 under umask 022 unless the host sets umask 077 (the ingress does) | symlink-component rejection, escape check, ingress umask 077 plus verify_state_permissions | HIGH | host umask or chmod | no |
| C-08 | LOW | VERIFIED | cp@b19c47dd src/agent_control_plane/bounded.py:558 (also :1169) | record store dir | BoundedRecordStore mkdir uses umask default, not make_private_dir 0700. File itself is mkstemp 0600 (:1020). Leaves directory listing exposed under a permissive umask; SIGKILL leaves stale *.tmp (0600) copies | atomic write plus dir fsync; ingress umask 077 | HIGH | use make_private_dir | no |
| C-09 | INFO | VERIFIED | runtime@f7a55e2a safe_executor.py:817,835; local_authority_effect.py:1049 | test hook in prod path | `simulate` ('lost_ack','crash_after_commit','partial') is a public parameter of commit/execute and writes state 'partial' or raises after commit. Not client reachable in the ingress (NC4-03 AST, core.py hard-codes None). Other integrators must keep it out | NC4-03 source check; check is best-effort (does not see getattr or ** forwarding, BOUNDARY.md) | HIGH | consider removing from non-test builds | no |
| C-10 | INFO | VERIFIED | runtime@f7a55e2a engine/recovery_resolution.py (checks block in `append`) | reconciliation evidence | synthetic recovery ledger admits observations with source_authentication/independent_verification "not_established"; non-authorizing, no retry authority | explicit synthetic=True, append-only triggers on events | HIGH | no | no |
| C-11 | INFO | VERIFIED | runtime@f7a55e2a SECURITY.md:13,42 vs :7 | doc consistency | In-scope list includes "escape the sandbox", "access unauthorized files" while the same file says isolation is application-level, not OS confinement. The roadmap item "test suite for sandbox escape attempts" is not done | the :7 statement is accurate | HIGH | doc edit | no |
| C-12 | INFO | VERIFIED | orchestrator@721f4406 orchestration/adapters/attestation/verifier.py:203 | subprocess | verifier runs `python -I` in a temp-dir copy with minimal env, timeout, but no rlimits/seccomp/network block; capture_output unbounded within the timeout. Workflow-store lock owner tokens are forgeable by anyone who can read the directory (README:77); lock is cooperative | timeout, -I, exclusive hard-link events, sequence_conflict | MEDIUM | rlimits/output cap | no |

Checked, nothing found (VERIFIED by source):
- Atomic route: the claim state check, budget, attempt, effect insert and receipt all run inside one BEGIN IMMEDIATE (local_authority_effect.py:928-1075), with ROLLBACK on every refusal path.
- Lost ack: TimeoutError and generic exceptions after dispatch map to 'unknown', retry_eligible forced False (atomic_local_control_plane_executor.py), with reconcile_claim_exact binding decision, effect and operation digest.
- CP Route-A execute: write-ahead 'attempted' row, then absence-after-prior-attempt is never retry-eligible (bounded.py:1665-1831).
- CP record writes are tmp + fsync + os.replace + dir fsync under a sidecar flock. Pin installer uses fsync, an anchor, fences and a hot-journal recovery path. Pin reader is mode=ro and fails closed (HOLD).
- Peer credential check precedes any read; unreadable creds refuse; socket is bound under umask 0777 then chmod (no window).

## 3. Mapping to Wiki cases (execution-runtime or control-plane; crash/duplicate/lost-ack/recovery/host)

All tests below are in suites/wiki-derived at 86f78ea3. All run on SYNTHETIC SQLite routes against the frozen ec728da6 reference profile (HISTORICAL profile r13), not the MVP tuple or heads. Results UNAVAILABLE.

- TC-L06-022 (PARTLY): test_wp_c ::test_wiki_l06_022_* (4 tests). They show grant suspension refuses the next effect, suspension persists across restart, an already-committed call stays applied after a stop, and the stop journal records caller-supplied observations. Nothing terminates a process.
- TC-L15-019 (PARTLY): 4 tests including the known-limit re-admission test (C-01).
- TC-L17-028 (PARTLY): 4 tests (typed refusal or unknown on input failure).
- TC-L05-013 (APPL): test_wp_g4 (4 tests; fail-closed only, no fail-open mode exists).
- TC-L06-024 (PARTLY): cumulative budget.
- TC-L06-023 / TC-D09-016 (PARTLY): local revocation only.
- TC-D12-021 (PARTLY): refusal retention.
- TC-L06-026 (PARTLY): test_wp_g6 DB-path traversal and symlink fragments.
- TC-L06-015, TC-L06-016, TC-L06-003: approvals and unregistered actor, not host topics.
- Not mapped: nothing in the Wiki set covers SIGKILL, IPC/peer-cred, Yama, uid separation. Those exist only as MVP NC rows.

(a) Mappings that look wrong or over-claim:
- TC-L06-026 "Agent Runtime File and Network Egress Restrictions" is PARTLY on the strength of destination DB-path confinement. That is a destination-adapter property, not an agent-runtime restriction. The test itself states the constructor accepts any root, and SECURITY.md says not OS confinement. Compare TC-L06-025 (code sandbox) and TC-D10-002, both NOT_APPLICABLE. Suggest NOT_APPLICABLE or an explicit "no assurance" note.
- TC-L06-022: the not_claimed text says OCS "keeps a local stop journal for a controlled local process". The test docstring says the journal "is not a mechanism that stops anything", and its requester field is unauthenticated. The applicability record lists only route-A as the synthetic destination while most stop tests use route B.
- TC-L05-013 and TC-L06-015 are APPLICABLE with not_claimed null although scope notes limit them (fail-closed branch only; approver display excluded).
- TC-L17-028 / TC-L05-013: tests mutate in-process objects (monkeypatched resolver reads, `_connect` replaced) and do not exercise real filesystem or host failures.
- TC-L06-022 and TC-D12-021 point at suites/cognous-execution-runtime/tests/test_w2_*; I read those paths only as listed in applicability. I did not read those files.

## 4. (b) Security-relevant gaps with NO test or evidence anywhere I could find

- Power loss / OS crash durability (SQLite synchronous is not set in safe_executor, so it relies on the build default; WAL on). SIGKILL tests do not cover it.
- Kill of the ingress process mid-request, of the CP process, and during claim provisioning (NC2-07 kills an executor child only). The ingress restart behaviour is HISTORICAL reviewer observation only.
- Client disconnect after send (lost ack at the socket layer).
- A kill at points other than the 3 hook seams (e.g. during COMMIT fsync or WAL checkpoint).
- Live-core peer-credential rejection (NC4-03d uses a stub core). SO_PEERCRED gid is ignored (uid allowlist only).
- Hardlink or /proc magic-link variants for DB-path confinement; race tests for the TOCTOU.
- core_pattern, ulimit -c, NoNewPrivs, seccomp for ingress or client.
- Same-uid code (explicitly not claimed by the environment record).
- Pin installer / fence on a real host under executor-vs-installer uids at current heads (repo test is root-only and skips otherwise: "INCONCLUSIVE, not a pass").
- Orchestrator: no host, IPC or UID tests; crash tests exist only in-repo.
- OpenShell live behaviour (docs: unverified).
- NC4-03a asserts a number only (no per-fact booleans).
- Stale-restore protection has no test of a mitigation, only of the limit.

## 5. (c) What I could not inspect

- Wiki-derived junit results (file absent).
- Runtime c5e97e87, CP 7a4bcd40 and hub c897266b source (shallow heads only), so I cannot say which head changes post-date the MVP.
- Whether CI ran the in-repo crash tests at the heads.
- The wiki-derived `_wiki_helpers`/`_wp_g_common` and the test_w2_* / test_scn_d07 sources in depth.
- Launch.py, proposal.py parsing and Verifier/Replay/Pack custody (other workers).
- The actual runner host beyond the recorded files.

## 6. Known documented limits (limits, not defects)

- Operation-ledger pruning: no retention rule; Control Plane does not detect it; the destination's operation row is the backstop (NC3-04).
- Accepted outsider stat residual on the 2751 profile (NC4-03c).
- Trusted-host assumption: no resistance to root, the ingress uid, same-privilege code, or direct DB modification by an authorized file holder (environment-record claims.not_claimed). Direct-write baseline control in the evidence confirms this.
- Local-only budgets and stop; no external anchor.
- KL-01: the trusted ingress imports the CP tests package (synthetic resolver); fixed synthetic authority "case-1".
- The 2751/0660 bounded profile is a synthetic test config (D3), not a production design.
