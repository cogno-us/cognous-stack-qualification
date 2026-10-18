# Refusal-test template (N4)

Every effect-time refusal scenario uses one shape, implemented in [`suites/_refusal_template.py`](../suites/_refusal_template.py). A worked example against the pinned reference is [`suites/v1-scenarios/test_n4_refusal_template.py`](../suites/v1-scenarios/test_n4_refusal_template.py); the template's own logic is covered without pinned components by [`tests/test_refusal_template.py`](../tests/test_refusal_template.py).

This is test harness only. It changes no component, pin, profile or default, maps to no requirement row, and changes no verdict.

## The five legs

A scenario fails with the letter of the first leg that broke (`RefusalTemplateFailure.leg`).

| Leg | Assertion |
|---|---|
| (a) negative | The destination ledger has no row for the refused effect id. Read through an independent read-only connection, not through the executor's result. |
| (b) refusal row | A refusal row names the effect id, the failed check (every expected reason code) and, for each input the scenario declares as changed, both its expected and observed version. The stage can be pinned too. |
| (c) positive control | A fresh, identical flow with the grant unchanged, through the same call, produces the same effect id, exactly one ledger row, and no refusal row. A revocation probe (`revocation=True`) also requires that the permitted control ran at the same enforcement point as the refusal and that the policy version it observed there equals the policy version the refusal row observed. A control bound to a different policy version does not count. |
| (d) mutation | With the refusal writer disabled on a disposable flow, the same scenario must fail leg (b). A mutant that survives is itself a failure (leg d). The effect must still be blocked in the mutant (the refusal blocks, only the evidence row is lost), which the template also asserts. |
| (e) provenance | The scenario declares `Provenance(kind, source)`: `code-reading` (cite file and symbol) or `run` (cite the pinned commit and the run or test). Anything else, or an empty source, is refused before any leg runs. The label travels in the evidence JSON. |

## Holder classification

`classify_holders(holders, refusal_rows)` returns exactly two lists.

- `witnessed_refusals`: holders named by a refusal row (as a changed input, or by effect id).
- `unenumerated_authority_needing_containment`: every other holder, classified `coverage_unknown`.

A holder that produced no refusal is `coverage_unknown`. It is never reported as expired, revoked or inactive: no refusal means nothing is known about whether its authority still stands. Containment or a probe is needed before any claim.

## Writing a scenario

1. Pick or write an `Adapter` (`RouteAAdapter` covers control plane revalidation, the runtime executor and the effective-grant destination, using the objects from `_d02_d05_d09_helpers`). Another route needs `build`, `apply_change`, `execute`, `effect_id`, `ledger_effect_ids`, `refusal_rows`, `disable_refusal_writer` and `policy_versions_observed_at_enforcement`.
2. Declare a `RefusalSpec` (reasons, changed inputs, provenance, revocation flag, optional stage).
3. Call `run_refusal_scenario(adapter, spec, tmp_path, pytest.MonkeyPatch)`, then `classify_holders` over the holders you enumerated, and record `report_json(...)` with `record_property`.

Record the principal the scenario acts for with `record_property('principal', <id>)`; `tools/scenario_report.py` reports per principal only from that property and counts every case without it as `unrecorded`.

Test the template's sensitivity the way the example does: a wrong expected reason must fail leg (b); a change that does not refuse must fail leg (a); a bad provenance label must fail leg (e).

## Code facts the template relies on (code wins over the addenda)

- The refusal outcome of `decide()` and of effect-time revalidation is `hold`; `deny` is never produced. Refusal rows are typed (`EffectTimeRefusal`, reason codes from `runtime-authority-reasons/0.1`).
- `effect_id` is the commitment of proposal, grant id and grant revision, so renewing a grant changes it. The control in leg (c) therefore must not renew the grant.
- The refusal writer is `BoundedRecordStore.append_refusal`. Leg (d) replaces it on the instance of the disposable flow only.
- The effect-time check is recorded on the control side as a resolution check at stage `effect`; the refusal row's stage is `effect_time_revalidation`. The route A adapter maps one to the other.
