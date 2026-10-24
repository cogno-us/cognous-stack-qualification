# Mandatory battery: note on the supported-ingress ambiguity row NC2-06 (PROPOSED)

Status: the entries below are now APPLIED in `mandatory-battery.proposed.v1.json` by this proposal (the file name keeps its earlier "placeholder" name so that no reference breaks). They remain a builder proposal: Qualification decides whether, and in which battery version, they become mandatory. Nothing here is an acceptance or a release decision; release stays HOLD.

## Resolution of the earlier contradictory instructions

An earlier version of this note named `suites/mvp-chain/test_ingress_ambiguity.py::test_ingress_ambiguous_acknowledgement_supported_path` as the NC2-06 battery entry, while the PR change list named `suites/mvp-chain/test_mvp_chain.py::test_row[NC2-06]`. The gate judges an `oracle_row` entry by the oracle verdict of its row, and G-03 requires one `oracle_row` per mandatory row of the expectations in force; only `test_row[NC2-06]` carries that verdict. The single, applied rule is:

| id | kind | invocation | file | test | oracle row | evidence level |
|---|---|---|---|---|---|---|
| NC2-06 | oracle_row | mvp-chain | `suites/mvp-chain/test_mvp_chain.py` | `test_row[NC2-06]` | `NC2-06` in `process/mvp-chain/expectations.proposed.v6.json` | SUPPORTED INGRESS |

The six tests of `suites/mvp-chain/test_ingress_ambiguity.py` (the supported-path test `test_ingress_ambiguous_acknowledgement_supported_path` and five negative controls, each of which must FAIL the NC2-06 predicate) are listed as supplementary entries `AMB-01` to `AMB-06` (kind `supplementary_nc2_06_negative_control`). They are mandatory in the zero-unexplained-skips sense, they are not oracle rows, and they do not stand in for `test_row[NC2-06]`. Every test of `suites/mvp-chain/test_kwflow.py` (143 collected tests, the self-tests of the NC4-03 data-flow predicate) is listed as `KW-001` to `KW-143` (kind `supplementary_nc4_03_predicate`).

## What the battery now names

- `expectations_in_force` is `expectations.proposed.v6.json` (the builder's composition of the v3 rows with the NC4-03 row of PR #222 and the NC2-06 row of PR #224; a rows-from-two-branches merge, not a Qualification-composed or frozen oracle); it has its own `unchanged_files_sha256` entry; v1-v3 stay listed and unchanged.
- The invocation `paths` of `mvp-chain` (battery, collection step and run step of the workflow, which must stay identical) include `test_kwflow.py` and `test_ingress_ambiguity.py`, so G-13 (a collected test that is not committed is INCOMPLETE) holds.
- NC2-01..05 and `test_ruling4_lost_ack.py` remain EXECUTOR-LEVEL evidence (`simulate='lost_ack'`) and must not be cited as supported-ingress evidence. Preserve the UNKNOWN / no-blind-retry criterion.

The fault is injected owner-side only (`suites/mvp-chain/_ingress_fault_wrapper.py`: one Runtime post-commit seam, one use); no general fault-injection subsystem.

Evidence limit for the reuse part of NC2-06: the same-bytes REPLAY refusal is ingress-ledger evidence only. A fresh request id is HELD by approval binding unless the owner-side harness builds it with the approval-bound correlation id (`bind_fresh`); only then does a second request reach the executor, where it is denied (in the pinned tuple by the authoritative effect budget, not by the operation-identity guard). The row must not be cited as destination duplicate prevention beyond that observation.
