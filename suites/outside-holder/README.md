# Outside-holder suite (N5: M3 witness digest, L5 holder probe)

Scenarios for two opt-in additions to the control plane (engineering addendum 101726_B, items M3 and L5; N4 template). They use the
real control plane `BoundedAuthorizationWorkflow`, the runtime `PinnedControlPlaneExecutor` and its SQLite destination, with synthetic
fixtures and no network effects. The flow harness is the operation-identity suite's `_oi_flow.py` (imported, not copied).

Run against two checkouts: `OH_CONTROL_PLANE_DIR=<control plane> OH_RUNTIME_DIR=<runtime> python -m pytest suites/outside-holder`.
A missing variable fails every test; nothing skips. The workflow `outside-holder-profile.yml` is dispatch or `workflow_call` only,
selects nothing and changes no verdict. This suite is not part of the V1 validation controller.

## Witness digest (M3, `test_witness_digest.py`)

| Test | Proves | Expected today |
|---|---|---|
| `dropped_entry_accepted_today_*` (HMAC replay bundle, signature scheme, bounded record store) | a key holder who drops an entry and re-seals the record set is accepted by every check that exists | accepted, **run** (HMAC and store are shipped code; the Ed25519 seal is modelled, no shipped signature covers these record sets) |
| `dropped_entry_after_published_digest_rejected` | with a digest held outside the key holder, the same drop is rejected under all three seals, as `witness_ledger_shrunk`; honest appends after the digest are not rejected | new behaviour, fails today by design |
| `rewritten_entry_...rejected`, `dropped_then_replaced_entry_...` | a rewrite, or a drop plus an append that restores the count, is `witness_ledger_head_mismatch` | new |
| `dropped_entry_in_an_earlier_published_digest_is_still_caught` | every held digest is checked, and a latest-only witness still catches a covered drop | new |
| `publisher_refuses_to_publish_over_a_rewrite`, `no_digest_is_not_a_pass` | an honest publisher verifies first; an empty witness verifies nothing | new |
| `blind_head_comparison_lets_the_drop_through` | mutation check: with the head comparison blinded the rewrite is accepted, so the rejection depends on it | new |
| `witness_holder_can_rewrite_the_witness_limit` | the stated limit: whoever controls the witness can substitute a matching chain; an independent copy of the digest still catches it | new |

This gives visibility to a reader who holds the witness digest. It is not tamper evidence against the witness holder, and rows
appended after the latest published digest are reported as unwitnessed. The witness in these tests is a file in a temporary
directory; where a real witness is held (owner default: a signed tag in the hub repository) is a deployment step the owner must
trigger. Nothing here publishes anything.

## Holder probe (L5, `test_holder_probe.py`, `_holder_probe.py`)

| Test | Proves | Expected today |
|---|---|---|
| `probe_routed_and_self_credentialed_holders` | after a revocation, the routed holder gets one refusal (template legs a-e, control bound to the policy version at the enforcement point); the self-credentialed holder's effect lands with no record. Report: witnessed refusals vs unenumerated authority needing containment; `coverage_unknown`, never "expired" | one refusal and one unrecorded outcome, **run** |
| `probe_without_control_is_inconclusive` | no control, or a control that did not reach the destination: verdict `inconclusive`, nothing is called witnessed | **run** |
| `probe_with_refusal_writer_disabled_fails_the_probe` | mutation check on the probe | **run** |
| `requires_revocation_assurance_*` | a flagged action class holds (`holder_inventory_missing`) until a holder inventory enumerating at least one holder exists | new, fails today by design |
| `flag_unset_default_path_unchanged` | with the flag and inventory unset the profile dump and the decision are unchanged | **run** |

Probes cover enumerated holders only. A holder nobody listed stays invisible, so the inventory is the real control.
Without the control plane change the witness tests, and the two `requires_revocation_assurance_*` tests, fail by design on control
plane main fd0d5e0 (ran: 7 passed, 10 failed by design); with it all 17 pass.
