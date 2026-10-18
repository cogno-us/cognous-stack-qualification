# Operation identity suite (N1)

Composed scenarios for the opt-in `operation-identity/0.1` profile (engineering addendum 101726_B, item N1), written to the
[refusal-test template](../../docs/refusal-test-template.md). They run the real control plane `BoundedAuthorizationWorkflow`, the
runtime `PinnedControlPlaneExecutor` and `OperationIdentityDestination`, with synthetic fixtures and no network effects.

Run against two checkouts: `OI_CONTROL_PLANE_DIR=<control plane> OI_RUNTIME_DIR=<runtime> python -m pytest suites/operation-identity`.
A missing variable fails every test; nothing skips. The workflow `operation-identity-profile.yml` is dispatch or `workflow_call` only.

| Test | Proves |
|---|---|
| `delayed_r1_after_renewal_single_effect` | r1 inside the destination, grant renewed, r2 commits, r1 lands late: one effect, both attempts join one operation id by id |
| `renewal_after_stalled_check_single_effect` | r1 stalls between check and dispatch: one effect; attempts and checks join by id although their time order is inverted |
| `worker_self_renewal_refused` | a renewal written by the worker is refused and recorded; the renewed revision stays held |
| `attempt_joins_check_by_id` | the journal check, the ResolutionCheck and the attempt share the check id under the profile (they share none today) |
| `absent_is_not_never_executed` | an absent read after a lost acknowledgement never permits a retry and never becomes `safe_to_retry` |
| `*_legacy_*`, `*_today` | the default path today: second effect when the cap allows it, no identity rows, observation-time hold |
| `renewal_after_stalled_check_r1_refused_as_check_expired_before_dispatch` | the N1 strict xfail, now a plain test: r1 stalled past its class bound is refused before dispatch (needs freshness/0.1) |

## Freshness (N3, `test_freshness_profile.py`)

Opt-in `freshness/0.1` (control plane `RuntimeAuthorityProfile.freshness`) and the runtime's delayed-commit destination mode
(`engine/delayed_commit_destination.py`). All six write to the refusal-test template or write its five legs out.

| Test | Proves |
|---|---|
| `stalled_check_past_class_age_refused_at_dispatch` | the service clock is re-read immediately before dispatch; past the deadline fixed at opening the check is closed (`expired`) and refused as `check_expired_before_dispatch` |
| `journal_timestamps_reflect_wall_time` | each journal event is stamped at write; `evaluated_at` stays the one evaluation pass (today every event reuses it) |
| `live_overdue_check_reported_not_closed` | a live check past its deadline is reported `check_overdue` by the recovery pass and not closed; an abandoned one is still closed |
| `superseded_owner_journal_write_refused` | regression guard (refused today, ran): a closed check cannot be written by its superseded owner, with and without the profile |
| `status_with_replayed_nonce_rejected` | where the resolver echoes the reader's nonce, a replayed response is rejected (`status_nonce_mismatch`); ages are labelled `nonce_bound` / `source_asserted` |
| `outage_extension_recorded_with_authority` | an age-bound extension counts only with a recorded signer from the rule-revision signer set; withdrawing that signer withdraws the extension |
| `*_today` | the default path today: a stalled check is dispatched; a replayed response is accepted |

The delayed-r1 cases use the runtime's delayed-commit mode (`pause_at`, `defer_next_commit`, `land`); the suite carries no
destination code of its own. Without the profile or the mode the freshness tests, and every test that builds a flow, fail by
design on control plane main 83b49b5 and runtime main 63a7c0fe; with only the delayed-commit module added to that runtime the
default-path legs, the N1 tests and the `*_today` tests pass (ran: 11 passed, 9 failed by design). This suite is not part of the V1 validation controller and changes no verdict.
