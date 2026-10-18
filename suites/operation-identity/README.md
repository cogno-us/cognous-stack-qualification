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
| N3 strict xfail | `check_expired_before_dispatch` for r1 (stream N3 owns it); fails today at leg (b) by design |

The delayed-commit destination in `_oi_flow.py` is a minimal in-test stand-in for the CI delayed-commit mode owned by stream N3.
The profile tests fail on control plane main 5f5ae03f and runtime main 10a11d03 by design (the profile is absent there); the legacy
and `*_today` tests pass there. This suite is not part of the V1 validation controller and changes no verdict.
