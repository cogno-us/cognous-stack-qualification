# Mandatory battery: placeholder note for the supported-ingress ambiguity test (PROPOSED)

Status: placeholder only. `mandatory-battery.proposed.v1.json` is NOT edited (its oracle block pins expectations v1-v3 by hash). Qualification decides
whether, and in which battery version, this entry becomes mandatory. Nothing here is an acceptance or a release decision; release stays HOLD.

Proposed entry for a future battery version (Architect ruling 5):

| id | kind | invocation | file | test | oracle row | evidence level |
|---|---|---|---|---|---|---|
| NC2-06 | oracle_row | mvp-chain | `suites/mvp-chain/test_ingress_ambiguity.py` | `test_ingress_ambiguous_acknowledgement_supported_path` | `NC2-06` in `process/mvp-chain/expectations.proposed.v6.json` | SUPPORTED INGRESS |

Also required of a future battery version: `expectations_in_force` would have to name `expectations.proposed.v6.json` (the composed proposal that also carries the corrected NC4-03; see the PR description for the full change list) and the new file would need its own
`unchanged_files_sha256` entry; the invocation `paths` list would need the new test file. NC2-01..05 and `test_ruling4_lost_ack.py` remain
EXECUTOR-LEVEL evidence (`simulate='lost_ack'`) and must not be cited as supported-ingress evidence. Preserve the UNKNOWN / no-blind-retry criterion.

The fault is injected owner-side only (`suites/mvp-chain/_ingress_fault_wrapper.py`: one Runtime post-commit seam, one use); no general fault-injection subsystem.

Evidence limit for the reuse part of NC2-06: the same-bytes REPLAY refusal is ingress-ledger evidence only. A fresh request id is HELD by approval binding unless the owner-side harness builds it with the approval-bound correlation id (`bind_fresh`); only then does a second request reach the executor, where it is denied (in the pinned tuple by the authoritative effect budget, not by the operation-identity guard). The row must not be cited as destination duplicate prevention beyond that observation.
