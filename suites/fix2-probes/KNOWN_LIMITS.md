# Known limits kept as strict expected failures

These 22 probes state a property that the component at its current head does not hold. They stay `xfail(strict=True)`: a run is
green while they fail in the asserted way, and the run fails if one starts to pass (the signal to remove its mark and list it as a
control). No assertion, fixture or expected value was changed to reach this state. Each mark carries a reason that starts
`known limit:`. Ids are relative to `suites/fix2-probes/`.

Measured at the main heads of the nine components on 2026-10-19 (Python 3.13): 191 passed, 22 expected failures, 0 reported failures.

| Probe id | Component | Property the probe states | Limit at the current head |
|---|---|---|---|
| `test_journal_rules_probes.py::test_probe_every_contradictory_combination_for_a_status_is_refused[odes-failed]` | ODES, execution-attempt-lifecycle reference validator | every status, flag and state combination the producer refuses is refused (status `failed`) | accepts a result of this status that claims an attempt and names no attempt row |
| `test_journal_rules_probes.py::test_probe_every_contradictory_combination_for_a_status_is_refused[odes-partial]` | ODES, execution-attempt-lifecycle reference validator | every status, flag and state combination the producer refuses is refused (status `partial`) | accepts a result of this status that claims an attempt and names no attempt row |
| `test_journal_rules_probes.py::test_probe_every_contradictory_combination_for_a_status_is_refused[odes-unknown]` | ODES, execution-attempt-lifecycle reference validator | every status, flag and state combination the producer refuses is refused (status `unknown`) | accepts a result of this status that claims an attempt and names no attempt row |
| `test_journal_rules_probes.py::test_probe_every_contradictory_combination_for_a_status_is_refused[odes-executed]` | ODES, execution-attempt-lifecycle reference validator | every status, flag and state combination the producer refuses is refused (status `executed`) | accepts a result of this status that claims an attempt and names no attempt row |
| `test_journal_rules_probes.py::test_probe_every_contradictory_combination_for_a_status_is_refused[odes-reconciled]` | ODES, execution-attempt-lifecycle reference validator | every status, flag and state combination the producer refuses is refused (status `reconciled`) | accepts a result of this status that claims an attempt and names no attempt row |
| `test_journal_rules_probes.py::test_probe_a_null_attempt_id_on_an_attempt_claiming_status_is_refused[failed-odes]` | ODES, execution-attempt-lifecycle reference validator | a null attempt id on an attempt-claiming result (`failed`) is refused | accepts an attempt-claiming result that names no registered attempt row |
| `test_journal_rules_probes.py::test_probe_a_null_attempt_id_on_an_attempt_claiming_status_is_refused[partial-odes]` | ODES, execution-attempt-lifecycle reference validator | a null attempt id on an attempt-claiming result (`partial`) is refused | accepts an attempt-claiming result that names no registered attempt row |
| `test_journal_rules_probes.py::test_probe_a_null_attempt_id_on_an_attempt_claiming_status_is_refused[unknown-odes]` | ODES, execution-attempt-lifecycle reference validator | a null attempt id on an attempt-claiming result (`unknown`) is refused | accepts an attempt-claiming result that names no registered attempt row |
| `test_journal_rules_probes.py::test_probe_a_null_attempt_id_on_an_attempt_claiming_status_is_refused[executed-odes]` | ODES, execution-attempt-lifecycle reference validator | a null attempt id on an attempt-claiming result (`executed`) is refused | accepts an attempt-claiming result that names no registered attempt row |
| `test_journal_rules_probes.py::test_probe_a_null_attempt_id_on_an_attempt_claiming_status_is_refused[reconciled-odes]` | ODES, execution-attempt-lifecycle reference validator | a null attempt id on an attempt-claiming result (`reconciled`) is refused | accepts an attempt-claiming result that names no registered attempt row |
| `test_journal_rules_probes.py::test_probe_a_result_naming_no_attempt_row_is_refused[failed-odes]` | ODES, execution-attempt-lifecycle reference validator | a result (`failed`) naming an unregistered attempt id is refused | accepts an attempt-claiming result that names no registered attempt row |
| `test_journal_rules_probes.py::test_probe_a_result_naming_no_attempt_row_is_refused[partial-odes]` | ODES, execution-attempt-lifecycle reference validator | a result (`partial`) naming an unregistered attempt id is refused | accepts an attempt-claiming result that names no registered attempt row |
| `test_journal_rules_probes.py::test_probe_a_result_naming_no_attempt_row_is_refused[unknown-odes]` | ODES, execution-attempt-lifecycle reference validator | a result (`unknown`) naming an unregistered attempt id is refused | accepts an attempt-claiming result that names no registered attempt row |
| `test_journal_rules_probes.py::test_probe_a_result_naming_no_attempt_row_is_refused[executed-odes]` | ODES, execution-attempt-lifecycle reference validator | a result (`executed`) naming an unregistered attempt id is refused | accepts an attempt-claiming result that names no registered attempt row |
| `test_journal_rules_probes.py::test_probe_a_result_naming_no_attempt_row_is_refused[reconciled-odes]` | ODES, execution-attempt-lifecycle reference validator | a result (`reconciled`) naming an unregistered attempt id is refused | accepts an attempt-claiming result that names no registered attempt row |
| `test_journal_rules_probes.py::test_probe_a_reconciliation_dated_before_its_attempt_is_refused[verifier]` | Verifier, control-plane journal rules | a reconciliation dated before the attempt it rests on is refused | does not compare a reconciliation stamp with the start of the attempt it rests on |
| `test_journal_rules_probes.py::test_probe_a_reconciliation_dated_before_its_attempt_is_refused[odes]` | ODES, control-plane-journal reference validator | a reconciliation dated before the attempt it rests on is refused | orders stamps within one clock domain only; a service stamp is not compared with the attempt start (evaluation time) |
| `test_journal_rules_probes.py::test_probe_a_closeout_dated_before_its_attempt_is_refused[odes]` | ODES, control-plane-journal reference validator | a closeout dated before the attempt it closes is refused | orders stamps within one clock domain only; a service stamp is not compared with the attempt start (evaluation time) |
| `test_runtime_probes.py::test_failure_after_commit_reports_unknown[runtime-error]` | Execution runtime, atomic executor | a failure after the effect commit reports status unknown with observed_state unknown and no retry | reports status unknown, retry not eligible, with observed_state applied (recovery observation); the probe expects observed_state unknown |
| `test_runtime_probes.py::test_failure_after_commit_reports_unknown[os-error]` | Execution runtime, atomic executor | a failure after the effect commit reports status unknown with observed_state unknown and no retry | reports status unknown, retry not eligible, with observed_state applied (recovery observation); the probe expects observed_state unknown |
| `test_verifier_probes.py::test_probe_a_binding_member_changed_alone_is_refused_against_the_captured_inputs[journal-applied-effective_max_effects]` | Verifier, decision binding | a change to binding member `effective_max_effects` alone is refused against the captured inputs, in a record verified without proposal and ledger | this member is checked against the proposal export and destination ledger only, not against the captured inputs |
| `test_verifier_probes.py::test_probe_a_binding_member_changed_alone_is_refused_against_the_captured_inputs[journal-applied-requirement_id]` | Verifier, decision binding | a change to binding member `requirement_id` alone is refused against the captured inputs, in a record verified without proposal and ledger | this member is checked against the proposal export and destination ledger only, not against the captured inputs |

## Reading notes

- The 15 attempt-identity rows are one limit seen through three probes: the verifier refuses these records, the ODES reference
  validator does not.
- The three clock-domain rows state an order between a service stamp and an attempt start (evaluation time). The ODES rule
  `causal_order` compares stamps within one clock domain only, by its own wording, so these rows record a difference between the
  probe and that documented rule as well as between the two implementations.
- The two runtime rows record the observed state reported after a failure that follows the commit: the current executor reports
  `applied` (the effect is present and read back) with status `unknown` and no retry; the probe expects `unknown`.
- The two verifier binding rows hold for a record verified without its proposal export and ledger; the same changes are refused when
  those are supplied (probes `..._with_proposal_and_ledger_supplied`, which run as controls).

## Other conditions of this suite (documented, nothing edited)

- Module collection: a module whose `PROBE2_*` variables are unset is not collected (`conftest.py`), and `checkout()` skips a test
  whose variable is unset. A missing checkout therefore gives no result rather than a pass.
- Python versions: the time grammar probes (69) pass on Python 3.13 and 3.14 at the current heads; the hour-24 form no longer needs a
  version-conditional mark.
- Wall-clock bound: `test_replay_probes.py::test_probe_an_80_kb_input_of_escaped_quotes_is_scanned_in_under_a_second` asserts a scan
  time below 1.0 s in a child process (3 s timeout); a heavily loaded machine can exceed it.
- `test_exchange_probes.py` builds throw-away git repositories and needs `git` on the path; `test_pack_probes.py` builds throw-away
  site layouts and needs no network.
