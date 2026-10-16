# Boundary map (correction vs. commitment)

Source files examined under the frozen F5b pins:

- Suite driver: `suites/security-runtime/test_security_runtime_chain.py`
- Workflow + decision: `agent_control_plane.bounded` (control plane @ `a34c3dc2`)
- Effect-time check: `engine.control_plane_adapter.PinnedControlPlaneExecutor.execute`
- Durable commit: `engine.effective_grant.EffectiveGrantDestination.commit` (local SQLite)
- Replay import: `agent_replay_bundle.importers.import_bounded_workflow`

Per the bounded-comparison process doc the two boundaries are named separately:

> The correction boundary is the latest point where an effective intervention can still
> change or prevent this action. The commitment boundary is the destination
> operation/transaction after which that consequence cannot be prevented by that
> intervention.

| Scenario | Case in produce() | Correction boundary | Commitment boundary | Residual-race limit |
|---|---|---|---|---|
| D01 | `valid` | N/A (no revocation) — baseline permits exactly one effect | SQLite destination commit of the effect row for `(grant_id, effect_id)` | No race injected. |
| D03 | `revoked` | Mutation of grant status to `revoked` **before** the executor's effect-time `resolution_check_event` for the grant input | SQLite destination commit | Prevention is contingent on revocation becoming effective **before** the executor's effect-time check; D03 as implemented places revocation at that correction window. |
| C07 | `race` | Grant mutation injected inside the destination `commit` call-site, after the effect-time check and before the row insert | SQLite destination commit (same insert) | The frozen F5b pins retain the published C0 residual race: an effective-grant change at commit time surfaces `effective_grant_changed_at_commit` and the row is not committed. The passing characterization test confirms **this specific** residual-race limit; it is not qualified distributed atomicity. |

## Notes

1. `NOW` is fixed by `monkeypatch` on `agent_control_plane.bounded._now`; clock
   uncertainty is removed by construction. Clock domain is simulated.
2. The destination source of truth is a local SQLite under `tmp_path/'sqlite'`; the
   observer `dest.observe(effect_id)` is a method call on the same in-process object as
   the writer — this is a local synthetic oracle, not an independently operated observer.
   See `observer-spec.md`.
3. `D03` here is the "grant revoked" variant. "Approval withdrawal", "policy-version
   change" and "evidence invalidation" are additional D03 variants listed in the
   bounded-comparison process and are **not** executed in this run; they are explicitly
   out of scope for this comparison. Capability flags for approval-withdrawal exist in
   the `produce()` fixture (`purpose_closed`, `tampered_evidence`, `input_dropped`) and
   can be enumerated separately if the owner requests.
4. The task's "stale-authority refusal from D03" calibration control maps to the
   `revoked` case already covered by `test_denial_preserves_actual_journal_refusal_and_destination[revoked-grant_revoked]`.
