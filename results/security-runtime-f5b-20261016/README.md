# F3R requalification of the F5b-repaired chain (16 October 2026)

**Bounded technical pass: 36 raw JUnit cases per repetition, twice, with zero failures, errors or skips.** All seven sources are actual merged commits after the F5b repairs and F3R re-pins. These are two repetitions of the same 36 cases, not 72 independent scenarios.

Tested qualification source: `8205469dd73d4c15e636749a84fa789822370785`, profile `process/security-runtime-f5b-20261016.json`, Exchange strict profile `security-runtime-f5b-20261016`, suite generation `f5b`. Run: [hosted run 38923503029](https://github.com/cogno-us/cognous-stack-qualification/actions/runs/38923503029) (job 117049091675, `pull_request`, attempt 1, Python 3.12.15). `bounded_cases_passed` and `candidate_integration_passed` are true for run-1 and run-2. `qualification_worktree_dirty` is false, because components and outputs were written under `RUNNER_TEMP`.

| Component | Revision |
|---|---|
| control_plane | `a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5` |
| runtime | `e20f92e104aba2ba6ad06120d8549c6170eaf63f` |
| replay | `79ba16d48b9be1e059b3045989c7df960c3df1c2` |
| evidence_pack | `893aca8dfb27ba5c5f3e833f2d29210ca7fc92e3` |
| odes | `eb83220c82f942e429a5e3ef5f677fdd5057ef84` |
| exchange | `8be6c6b80da8c5038d66419f84c10cc529f78137` |
| manifest | `2c36bcd0b620dbfe7ad924bc7196a3f0c04c5c5e` |

In both summaries, `source_revisions` equal these profile pins. `source_hashes` equal the committed bytes of the profile, runner, suite, workflow and summarizer at the tested head.

**Artifact and how it was verified.** Workflow artifact `12054598930` (`f5b-requalification-8205469d…`) is 4,891,142 bytes as reported by GitHub. Its GitHub-reported ZIP digest is SHA-256 `16183532f5b72aece64bdc529bc98206e01934662a10ac74fb4e895040141e59`. It expires on **14 January 2027 (2027-01-14T15:23:13Z)**.

The ZIP was **not** downloaded. The REST zip redirect to Azure blob storage was refused by this session's egress proxy, so the ZIP bytes, CRC integrity and archive member count were not checked locally.

Verification was done in the job instead. `tools/summarize_security_runtime.py` re-hashed all 668 original members per repetition against `run.json`. It then emitted these as check-run annotations, which were read through the REST API:
- the counts;
- source pins and hashes;
- the native audit;
- raw `junit.xml`/`stdout.log` (gzip+base64).

The decoded `junit.xml` and `stdout.log` match their in-job SHA-256 values.

**Native audit (read-only, immutable SQLite opens, in-job).**
- Revoked authority: zero destination effects and zero attempts, with one `authority_hold`/`admission_rejected` pre-dispatch failure row.
- Valid, lost-ack, crash-checkpoint and competing-owner cases: exactly one effect and one attempt each.
- Redelivery (lost-ack `unknown`, crash `reconciled`, competing owner `hold`): preserves the original effect ID and dispatches nothing new (`attempted` and `newly_executed` both false).

Producer acknowledgements remain distinct from actual archived destination state. The missing-configuration case fails before opening Exchange state.

**Retention.** This directory keeps raw JUnit/stdout, source/run summaries, verification commitments and audited destination rows. It does not keep the full native archive or the native basetemp trees. Retaining the full native archive (download, hash and durable storage before expiry) remains a **separate F4 owner-authorized step**: artifact ID `12054598930`, expiry 2027-01-14. These summaries do not substitute for every archived native file.

**Unchanged.** The historical F3 profile (`process/security-runtime-candidate-20261016.json`), its runner defaults and `results/security-runtime-merged-20261016/` are unchanged. The historical job passed again at this head (run 38923502695).

**Limits.**
- Synthetic local/hosted destination observation is not independently operated external verification.
- Consumer failure-record references remain source-asserted.
- Exchange transport adapters remain unusable under the security profiles; only the reference `run_exchange` path is exercised.
- Historical C0 race and same-host/C2/C3/deployment limits remain.
- No paid trial, production effect, real settlement, new institutional grant or publication occurred.

These records qualify only this bounded candidate. Refreeze, re-review, broader reference profiles, final selection/package freeze, fresh security/IP review and final owner publication acceptance remain separate gates at [control plane #68](https://github.com/cogno-us/cognous-open-control-stack/issues/68). No release or production authorization.
