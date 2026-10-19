# Known limits and open items of the V1 probes

Marking a probe as a known limit is additive: a strict expected failure and this list. No assertion, fixture or expected value of any
probe was changed. Ids are relative to `suites/v1-probes/`.

## Registered findings kept as strict expected failures (6)

Module `test_authority_ra_probes.py`, run against the control plane (`PROBE_CONTROL_PLANE_DIR`). Each probe states a behaviour that the
Runtime Authority addendum asks for in literal wording and the component does not record or order. They are registered as findings of
severity "spec gap" in `process/v1-validation/v1-2026-10-16-a/acceptance-map-03.json` (no safety defect recorded). They fail the same
way at the frozen pin and at the current head. Each mark is `xfail(strict=True, raises=AssertionError)` with the reason
`registered finding (spec gap): ...`; a probe that starts to pass fails the run and its mark is then removed.

| Probe id | Component | Property the probe states | Limit (registered finding) |
|---|---|---|---|
| `test_authority_ra_probes.py::test_probe_addauthra_opened_event_binds_the_component_version` | Control plane, check journal | the check-opened event names the component version | the event does not name the control plane component version |
| `test_authority_ra_probes.py::test_probe_addauthra_resolution_result_records_observation_time_and_age` | Control plane, resolution result | observation time and age are recorded with the result | no explicit age value is stored (observation and evaluation times only) |
| `test_authority_ra_probes.py::test_probe_addauthra_evidence_refusal_records_the_criterion_reference` | Control plane, evidence refusal | the refusal row records the criterion reference | the evidence refusal row carries no criterion reference |
| `test_authority_ra_probes.py::test_probe_addauthra_registry_declares_applicable_reopen_predicates` | Control plane, reason registry | each code declares its applicable reopen predicates | the registry declares no reopen predicates per code |
| `test_authority_ra_probes.py::test_probe_addauthra_refusal_trend_report_names_unmapped_codes` | Control plane, refusal trend report | the report names codes that are not mapped | the report does not name unmapped codes |
| `test_authority_ra_probes.py::test_probe_addauthra_freshness_is_verified_before_the_criterion_is_evaluated` | Control plane, evidence gate | freshness is verified strictly before the criterion is evaluated | the strict order is not observed (both reasons are reported together) |

## Open items, not marked

These are red at the current heads and are neither registered findings nor decided known limits. They are left unchanged.

- `test_odes_probes.py` (6 probes, run against ODES, `PROBE_ODES_DIR`; the other 2 probes of the module and the 5 of
  `test_odes_extension_probes.py` pass). They pass at the frozen ODES pin and fail at current main in the layer
  `package_content_integrity`: the module's helper `make_package` builds packages without the top-level members `created_by` and
  `created_at`, which the recipient validator now requires of a package envelope (decision 39-M). In a scratch copy with those two
  members added to the helper, all 8 probes of the module pass. This is a lag of the helper, not a finding about the component, so
  it is not recorded as a known limit; the choice (update the helper, or record it) is the owner's.
- `test_authority_probes.py::test_probe_er031_profile_is_labelled_proposed_and_not_adopted_and_makes_no_ratification_claim` (1 probe,
  `PROBE_AUTHORITY_DIR`). At current main it fails on `process/implementation/public-stack-v0.1/AUTHORITY_CONTEXT.md` line 99,
  where the sentence "Nothing here is ratified." is wrapped so that the line starts with `is ratified.`; the probe reads line by
  line and does not see the negation on the previous line. It asserts document wording rather than the guarantee (see
  `docs/authority-probe-rebaseline.md`).

## Conditions that depend on the environment (documented, nothing edited)

- Modules are collected only when their variable is set (`conftest.py`); a missing job gives no result, which the aggregator reports
  as inconclusive.
- `test_provenance_probes.py` needs `PROBE_PINS_DIR` (a directory of several checkouts) and is not collected without it.
- `test_index_supersession_probes.py` needs `node` and `npm ci --ignore-scripts` run in `chain/` of the Index checkout; without them
  its probes fail with a message naming the missing piece.
- `test_authority_probes.py` and `test_action_manifest_probes.py` read git history and need a full-history checkout (the authority
  module also needs the harness requirements installed); on a shallow checkout several probes fail with a message naming that.
- `test_authority_ra_probes.py` and the other control plane modules need the `runtime-authority` extra (`cryptography`) and Linux
  (the record store uses `flock`).
- `test_index_probes.py` has four in-body skips (lines 89, 105, 120, 144) that apply when the Index has no attestation verifier;
  with the current Index none of them is taken (29 passed).
