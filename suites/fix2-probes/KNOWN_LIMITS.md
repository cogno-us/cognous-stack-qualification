# Known limits kept as strict expected failures

These 6 probes state a property that the component at its current head does not hold. They stay `xfail(strict=True)`: a run is
green while they fail in the asserted way, and the run fails if one starts to pass (the signal to remove its mark and list it as a
control). No assertion, fixture or expected value was changed to reach this state. Each mark carries a reason that starts
`known limit:`. Ids are relative to `suites/fix2-probes/`.

Measured at the main heads of the nine components on 2026-10-19 (Python 3.13 and 3.14, same result on both): 207 passed, 6 expected failures, 0 reported failures. With `--runxfail` the 6 are the only failures (207 passed, 6 failed).

| Probe id | Component | Property the probe states | Limit at the current head |
|---|---|---|---|
| `test_journal_rules_probes.py::test_probe_a_reconciliation_dated_before_its_attempt_is_refused[verifier]` | Verifier, control-plane journal rules | a reconciliation dated before the attempt it rests on is refused | does not compare a reconciliation stamp with the start of the attempt it rests on |
| `test_journal_rules_probes.py::test_probe_a_reconciliation_dated_before_its_attempt_is_refused[odes]` | ODES, control-plane-journal reference validator | a reconciliation dated before the attempt it rests on is refused | orders stamps within one clock domain only; a service stamp is not compared with the attempt start (evaluation time) |
| `test_journal_rules_probes.py::test_probe_a_closeout_dated_before_its_attempt_is_refused[odes]` | ODES, control-plane-journal reference validator | a closeout dated before the attempt it closes is refused | orders stamps within one clock domain only; a service stamp is not compared with the attempt start (evaluation time) |
| `test_runtime_probes.py::test_failure_after_commit_reports_unknown[runtime-error]` | Execution runtime, atomic executor | a failure after the effect commit reports status unknown with observed_state unknown and no retry | reports status unknown, retry not eligible, with observed_state applied (recovery observation); the probe expects observed_state unknown |
| `test_runtime_probes.py::test_failure_after_commit_reports_unknown[os-error]` | Execution runtime, atomic executor | a failure after the effect commit reports status unknown with observed_state unknown and no retry | reports status unknown, retry not eligible, with observed_state applied (recovery observation); the probe expects observed_state unknown |
| `test_verifier_probes.py::test_probe_a_binding_member_changed_alone_is_refused_against_the_captured_inputs[journal-applied-effective_max_effects]` | Verifier, decision binding | a change to binding member `effective_max_effects` alone is refused against the captured inputs, in a record verified without proposal and ledger | this member is checked against the proposal export and destination ledger only, not against the captured inputs |

## Reading notes

- Removed at the pinned heads of this measurement (their marks were deleted, the assertions are unchanged, and they run as controls):
  the 15 ODES attempt-identity rows (the ODES reference validator of the execution-attempt-lifecycle contract now refuses a result
  that claims an attempt and names no registered attempt row, for all five statuses) and the verifier binding row for
  `requirement_id` (a change to that member alone is now refused against the captured inputs). Before the removal each of the 16
  ran as a strict unexpected pass.
- The three clock-domain rows state an order between a service stamp and an attempt start (evaluation time). The ODES rule
  `causal_order` compares stamps within one clock domain only, by its own wording, so these rows record a difference between the
  probe and that documented rule as well as between the two implementations.
- The two runtime rows record the observed state reported after a failure that follows the commit: the current executor reports
  `applied` (the effect is present and read back) with status `unknown` and no retry; the probe expects `unknown`.
- The verifier binding row for `effective_max_effects` holds for a record verified without its proposal export and ledger; the same
  change is refused when those are supplied (probe `..._with_proposal_and_ledger_supplied`, which runs as a control).

## Other conditions of this suite (documented, nothing edited)

- Module collection: a module whose `PROBE2_*` variables are unset is not collected (`conftest.py`), and `checkout()` skips a test
  whose variable is unset. A missing checkout therefore gives no result rather than a pass.
- Python versions: the time grammar probes (69) pass on Python 3.13 and 3.14 at the current heads; the hour-24 form no longer needs a
  version-conditional mark.
- Wall-clock bound: `test_replay_probes.py::test_probe_an_80_kb_input_of_escaped_quotes_is_scanned_in_under_a_second` asserts a scan
  time below 1.0 s in a child process (3 s timeout); a heavily loaded machine can exceed it.
- `test_exchange_probes.py` builds throw-away git repositories and needs `git` on the path; `test_pack_probes.py` builds throw-away
  site layouts and needs no network.
