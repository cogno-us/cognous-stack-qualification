## V1 validation v1-2026-10-16-a

Freeze: **PASS** · Verdict: **PASS** (requirement matrix)

| Status | Jobs |
|---|---|
| PASS | 33 |
| FAIL | 2 |
| INCONCLUSIVE | 1 |
| NOT RUN | 2 |
| NOT APPLICABLE | 0 |

| Component | OS | Python | Status | Testcases/fail/err/skip | Reason |
|---|---|---|---|---|---|
| action_manifest | ubuntu-latest | 3.11.17 | PASS | 245/0/0/0 |  |
| action_manifest | ubuntu-latest | 3.12.15 | PASS | 245/0/0/0 |  |
| bitrep | ubuntu-latest | 3.11.17 | PASS | 95/0/0/0 |  |
| bitrep | ubuntu-latest | 3.12.15 | PASS | 95/0/0/0 |  |
| constitutional_authority | ubuntu-latest | 3.11.17 | PASS | 491/0/0/0 |  |
| constitutional_authority | ubuntu-latest | 3.12.15 | PASS | 491/0/0/0 |  |
| control_plane | ubuntu-latest | 3.11.17 | PASS | 952/0/0/1 |  |
| control_plane | ubuntu-latest | 3.12.15 | PASS | 952/0/0/1 |  |
| gax_imx_transport | ubuntu-latest | 3.11.17 | PASS | 311/0/0/0 |  |
| gax_imx_transport | ubuntu-latest | 3.12.15 | PASS | 311/0/0/0 |  |
| governance_evidence_pack | ubuntu-latest | 3.11.17 | PASS | 366/0/0/0 |  |
| governance_evidence_pack | ubuntu-latest | 3.12.15 | PASS | 366/0/0/0 |  |
| moltbot_safe | ubuntu-latest | 3.11.17 | PASS | 512/0/0/0 |  |
| moltbot_safe | ubuntu-latest | 3.12.15 | PASS | 512/0/0/0 |  |
| odes | ubuntu-latest | 3.11.17 | FAIL | 3071/4/0/1 | test failures/errors |
| odes | ubuntu-latest | 3.12.15 | FAIL | 3071/4/0/1 | test failures/errors |
| prp | ubuntu-latest | 3.12.15 | NOT RUN | -/-/-/- | no test_*.py discovered in this component at the pinned commit |
| replay_bundle | ubuntu-latest | 3.11.17 | PASS | 1183/0/0/17 |  |
| replay_bundle | ubuntu-latest | 3.12.15 | PASS | 1183/0/0/17 |  |
| research_intelligence | ubuntu-latest | 3.12.15 | PASS | 13/0/0/0 |  |
| tfa | ubuntu-latest | 3.12.15 | NOT RUN | -/-/-/- | no test_*.py discovered in this component at the pinned commit |
| the_index | ubuntu-latest | 3.11.17 | PASS | 124/0/0/0 |  |
| the_index | ubuntu-latest | 3.12.15 | PASS | 124/0/0/0 |  |
| hub-tests | ubuntu-latest | 3.12 | PASS | 653/0/0/0 |  |
| matched-refund-rerun | ubuntu-latest | 3.12 | PASS | 20/0/0/0 |  |
| native-f5b-suite | ubuntu-latest | 3.12 | PASS | 36/0/0/0 |  |
| probes-action-manifest | ubuntu-latest | 3.12.15 | PASS | 3/0/0/0 | probe harness executed; individual probe outcomes are in junit.xml |
| probes-authority | ubuntu-latest | 3.12.15 | PASS | 23/0/0/0 | probe harness executed; individual probe outcomes are in junit.xml |
| probes-bitrep | ubuntu-latest | 3.12.15 | PASS | 9/0/0/0 | probe harness executed; individual probe outcomes are in junit.xml |
| probes-control-plane | ubuntu-latest | 3.12.15 | PASS | 77/0/0/6 | probe harness executed; individual probe outcomes are in junit.xml |
| probes-evidence-pack | ubuntu-latest | 3.12.15 | PASS | 13/0/0/0 | probe harness executed; individual probe outcomes are in junit.xml |
| probes-index | ubuntu-latest | 3.12.15 | PASS | 35/0/0/0 | probe harness executed; individual probe outcomes are in junit.xml |
| probes-moltbot-safe | ubuntu-latest | 3.12.15 | PASS | 29/0/0/0 | probe harness executed; individual probe outcomes are in junit.xml |
| probes-odes | ubuntu-latest | 3.12.15 | PASS | 13/0/0/0 | probe harness executed; individual probe outcomes are in junit.xml |
| probes-replay-bundle | ubuntu-latest | 3.12.15 | PASS | 21/0/0/0 | probe harness executed; individual probe outcomes are in junit.xml |
| provenance-scan | ubuntu-latest | 3.12.15 | PASS | 4/0/0/0 | probe harness executed; individual probe outcomes are in junit.xml |
| qual-tooling | ubuntu-latest | 3.12 | PASS | 423/0/0/1 |  |
| scenarios | ubuntu-latest | 3.12 | INCONCLUSIVE | 0/0/0/0 |  |

### Full-catalog status (all rows, real statuses; reporting only, not the verdict basis)

| Status | All rows | Pre-reduction mandatory rows |
|---|---|---|
| PASS | 52 | 40 |
| FAIL | 0 | 0 |
| INCONCLUSIVE | 39 | 30 |
| NOT RUN | 20 | 5 |
| NOT APPLICABLE | 20 | 0 |

Pre-reduction mandatory verdict (verdict rule applied to the rows that were mandatory before scope reduction): **INCOMPLETE**

### Scope reduction (36 rows moved out of the mandatory claim; statuses unchanged, none counted as PASS)

| ID | Decision | Category | Final status |
|---|---|---|---|
| ER-03-1 | D15 | fix-merged-outside-pinned-tuple | PASS |
| ER-04-4 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SR-2 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SR-3 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-D01 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-D02 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-D03 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-D04 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-D05 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-D06 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-D07 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-D08 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-D09 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-C01 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-C02 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-C03 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-C04 | D15 | design-limit | INCONCLUSIVE |
| SCN-C05 | D15 | not-run-unimplemented | NOT RUN |
| SCN-C06 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-C07 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-C08 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-C09 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-C10 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-C11 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-C12 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-C13 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-C14 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-C15 | D15 | not-run-unimplemented | NOT RUN |
| SCN-C16 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-C17 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-C18 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-C19 | D15 | not-run-unimplemented | NOT RUN |
| SCN-C20 | D15 | not-run-unimplemented | NOT RUN |
| SCN-C21 | D15 | not-run-unimplemented | NOT RUN |
| SCN-C22 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |
| SCN-C23 | D15 | inconclusive-partial-coverage | INCONCLUSIVE |

### Declared known limits (declared set sha256 `1ba741d7e71a7c3fb49c6bbc995b41503608e5232cb1cee93c0684563e19c087`; twin sha256 `a2b176d7bda17a0df35809940367d813e07367e70d6cc65b78e5faaeb966d3b3`, committed copy at git HEAD (working tree identical); 76 declarations, 30 matchable by the controller)

- **ER-05-1** (PASS, mandatory: yes; 66 undeclared case(s) counted)
  - DECLARED-LIMIT `tests.test_amount_substitution::test_numeric_forms_inside_the_payload_are_distinct_bytes_known_limit` (control_plane): passed
  - DECLARED-LIMIT `tests.test_known_limits::test_a_hold_has_no_binding_and_a_later_decision_carries_no_link_to_it_known_limit` (control_plane): passed
  - DECLARED-LIMIT `tests.test_known_limits::test_same_operation_id_with_a_different_payload_gets_the_replay_refusal_known_limit` (control_plane): passed
- **ER-05-5** (PASS, mandatory: yes; 62 undeclared case(s) counted)
  - DECLARED-LIMIT `tests.test_known_limits::test_removed_operation_rows_let_a_revision_2_decision_authorize_but_the_destination_refuses_known_limit` (control_plane): passed
- **ER-07-2** (PASS, mandatory: yes; 194 undeclared case(s) counted)
  - DECLARED-LIMIT `tests.test_contract_lifecycle_conformance::test_vendored_fixture_through_replay[executor-unknown-validated-unknown-after-ambiguous-dispatch]` (replay_bundle): xfailed
  - DECLARED-LIMIT `tests.test_contract_lifecycle_conformance::test_vendored_fixture_through_replay[result-unknown-null-attempt-id]` (replay_bundle): xfailed
  - DECLARED-LIMIT `tests.test_contract_lifecycle_conformance::test_vendored_fixture_through_replay[result-unknown-unregistered-attempt-id]` (replay_bundle): xfailed
- **ER-09-1** (PASS, mandatory: yes; 2215 undeclared case(s) counted)
  - DECLARED-LIMIT `tests.test_restriction_semantics::test_control_legacy_export_is_digest_identical_to_the_retained_example` (odes): failed
  - DECLARED-LIMIT `tests.test_result_classification::test_control_producer_v2_examples_pass_the_semantic_layer[lost_ack.package.json]` (odes): failed
  - DECLARED-LIMIT `tests.test_result_classification::test_control_producer_v2_examples_pass_the_semantic_layer[prior_absence.package.json]` (odes): failed
- **SCN-C04** (INCONCLUSIVE, mandatory: no; 0 undeclared case(s) counted)
  - DECLARED-LIMIT `suites.v1-scenarios.test_scn_c04::test_scn_c04_index_api_copied_evidence_is_not_counted_as_independent_corroboration[five_copies_attested_by_five_attestors]` (scenarios): NOT RUN
  - DECLARED-LIMIT `suites.v1-scenarios.test_scn_c04::test_scn_c04_index_api_copied_evidence_is_not_counted_as_independent_corroboration[five_copies_of_one_source_distinct_metadata]` (scenarios): NOT RUN
  - DECLARED-LIMIT `suites.v1-scenarios.test_scn_c04::test_scn_c04_index_api_copied_evidence_is_not_counted_as_independent_corroboration[five_exact_duplicate_submissions]` (scenarios): NOT RUN
  - DECLARED-LIMIT `suites.v1-scenarios.test_scn_c04::test_scn_c04_index_api_copied_evidence_is_not_counted_as_independent_corroboration[one_evidence_record_linked_five_times]` (scenarios): NOT RUN
  - reportable condition: declared test not run: suites.v1-scenarios.test_scn_c04::test_scn_c04_index_api_copied_evidence_is_not_counted_as_independent_corroboration[five_copies_attested_by_five_attestors]
  - reportable condition: declared test not run: suites.v1-scenarios.test_scn_c04::test_scn_c04_index_api_copied_evidence_is_not_counted_as_independent_corroboration[five_copies_of_one_source_distinct_metadata]
  - reportable condition: declared test not run: suites.v1-scenarios.test_scn_c04::test_scn_c04_index_api_copied_evidence_is_not_counted_as_independent_corroboration[five_exact_duplicate_submissions]
  - reportable condition: declared test not run: suites.v1-scenarios.test_scn_c04::test_scn_c04_index_api_copied_evidence_is_not_counted_as_independent_corroboration[one_evidence_record_linked_five_times]
- **ADD-AUTH-RA** (PASS, mandatory: no; 75 undeclared case(s) counted)
  - DECLARED-LIMIT `suites.v1-probes.test_authority_ra_probes::test_probe_addauthra_evidence_refusal_records_the_criterion_reference` (probes-control-plane): xfailed
  - DECLARED-LIMIT `suites.v1-probes.test_authority_ra_probes::test_probe_addauthra_freshness_is_verified_before_the_criterion_is_evaluated` (probes-control-plane): xfailed
  - DECLARED-LIMIT `suites.v1-probes.test_authority_ra_probes::test_probe_addauthra_opened_event_binds_the_component_version` (probes-control-plane): xfailed
  - DECLARED-LIMIT `suites.v1-probes.test_authority_ra_probes::test_probe_addauthra_refusal_trend_report_names_unmapped_codes` (probes-control-plane): xfailed
  - DECLARED-LIMIT `suites.v1-probes.test_authority_ra_probes::test_probe_addauthra_registry_declares_applicable_reopen_predicates` (probes-control-plane): xfailed
  - DECLARED-LIMIT `suites.v1-probes.test_authority_ra_probes::test_probe_addauthra_resolution_result_records_observation_time_and_age` (probes-control-plane): xfailed

Reportable conditions: 4 (listed above per row).
