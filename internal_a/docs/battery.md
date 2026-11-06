# Internal-A reduced case battery (generated from `oracle/oracle.v1.json`)

Draft for Architect review. **Internal nonproduction Q-A only.** Generated from the oracle so the two cannot diverge; the oracle JSON is authoritative. Classes: **PRE** precondition, **CTL** control, **RI** required invariant, **OBS** known-limit observation (never a validated security property), **INFO** informational/NOT RUN, **NA** not applicable.

## Mandatory cases (22)

| Case | Class | Maps to | Mutation | Native entrypoint | Observations | Paired control | Failure condition |
|---|---|---|---|---|---|---|---|
| QA-S1 | PRE | - | none | git rev-parse HEAD / HEAD^{tree} per component checkout (driver raw capture 'source_identity') | 2 | - | any commit or tree differs from the D4-approved pin, is missing, or the capture is absent |
| QA-S2 | PRE | - | none | evaluator ia_eval.identity.hash_files over the pinned checkouts (driver raw capture 'file_identity') | 2 | - | any listed file is missing, extra, or has a different sha256 or git blob id (module/fixture hash tampering) |
| QA-S3 | PRE | - | none | evaluator ia_eval.identity.hash_files over internal_a/freeze/snapshots (driver raw capture 'snapshot_identity') | 1 | - | any snapshot file differs from its frozen sha256, or is missing |
| QA-E1 | PRE | - | none | evaluator hash of the retained ZIPs and their members (driver raw capture 'artifact_identity'); read-only, nothing is re-executed | 2 | - | any ZIP or C4 member hash differs from the frozen value, or the retained bytes are unavailable (unavailable => INCONCLUSIVE, never PASS) |
| QA-01 | CTL | - | none | AM load_manifest_json/validate_manifest/manifest_digest/proposal_digest/proposal_mismatches; CP BoundedAuthorizationWorkflow.decide; RB import_bounded_workflow; PK import_manifest_reconstruction | 44 | - | any observation differs, is missing, or a native call raised |
| QA-02 | CTL | - | none | as QA-01 with the subject-owned grant-status input revoked (L26) | 43 | - | any observation differs, is missing, a native call raised, or an 'authorized' decision appears downstream |
| QA-03 | RI | QA-03 | /records/<i>/data/result where records[i].record_type=='runtime_decision': replace 'hold' -> 'authorized' | PK import_manifest_reconstruction(manifest: dict, reconstruction_bundle: dict) | 2 | QA-02 | import returns a pack, or raises a different type or message |
| QA-05 | RI | QA-05 | /records/<i> where record_type=='runtime_decision': remove | PK import_manifest_reconstruction | 2 | QA-02 | import succeeds, or a different type or message |
| QA-08 | RI | QA-08 | /manifest_digest: change one hex character of the 64-hex tail | AM binding.proposal_mismatches(manifest, proposal); CP BoundedAuthorizationWorkflow.decide(proposal) | 4 | QA-01 | AM list lacks the code or has extras; CP result is not hold, a binding is present, or the code is absent |
| QA-10 | RI | QA-10 | /tenant_id: replace 'tenant-alpha' -> 'tenant-beta' | RB import_bounded_workflow(cp_record, proposal=<mutated>, control_plane_revision=<CP pin>) | 2 | QA-01 | import returns a bundle, or a different type or message |
| QA-12 | RI | QA-12 | control_plane_revision: replace with an unsupported 40-hex string | RB import_bounded_workflow(..., control_plane_revision=<unknown 40-hex>) | 2 | QA-01 | import returns a bundle, or a different type or message |
| QA-16 | RI | QA-16 | /metadata/traceable_import/derived_counts/destination_effect_count: replace 0 -> 1 | PK load_evidence_pack(path) then validate_evidence_pack(pack) on the persisted, mutated Pack | 2 | QA-01 | report.valid is True, or no E_TRACE_SEMANTICS error issue at metadata.traceable_import |
| QA-27 | RI | QA-27 | /metadata/traceable_import/derived_counts/authorization_held_count: 1 -> 0; /metadata/traceable_import/derived_counts/authorization_granted_count: 0 -> 1 | PK load_evidence_pack(path) then validate_evidence_pack(pack) on the persisted, mutated Pack | 2 | QA-02 | report.valid is True, or no E_TRACE_SEMANTICS error issue at metadata.traceable_import |
| QA-18 | RI | QA-18 | /status: replace 'reconstruction_partial' -> 'reconstruction_complete' | PK import_manifest_reconstruction | 2 | QA-01 | import succeeds, or a different type or message |
| QA-19 | RI | QA-19 | file: delete | AM load_manifest(path) | 2 | QA-01 | a manifest is returned, or a different type or message |
| QA-22 | RI | QA-22 | any tracked *.py: change one byte | PK import_manifest_reconstruction with a scratch git checkout of Replay carrying a one-byte change | 2 | QA-01 | import succeeds with the modified Replay file, or a different type or message |
| QA-25 | RI | QA-25 | /decisions: append a deep copy of /decisions/0 | RB import_bounded_workflow(cp_record, proposal=proposal, control_plane_revision=<CP pin>) | 2 | QA-01 | import returns a bundle, or a different type or message |
| QA-09 | OBS | QA-09 | /metadata: omit | AM binding.manifest_digest(manifest) vs evaluator canonical sha256 of the raw dict (CP bounded.py:84-97 basis) | 2 | - | full-manifest digests differ, or reduced-manifest digests are equal (the limitation changed: new oracle version required) |
| QA-11 | OBS | QA-11 | /tenant_id: replace 'tenant-alpha' -> 'tenant-beta'; keep run_id unchanged (a differing run_id raises, importers.py~1005) | RB import_bounded_workflow(hold_record, proposal=<tenant swapped>, control_plane_revision=<CP pin>) | 3 | - | Replay refuses the swapped proposal on a HOLD record (the limitation changed: new oracle version required) |
| QA-17 | OBS | QA-17 | /bundle_id: replace with the fixed value 00000000-0000-4000-8000-0000000000a1 | PK import_manifest_reconstruction on the bundle with bundle_id replaced; validate_evidence_pack | 4 | - | the Pack refuses the re-identified bundle (the limitation changed: new oracle version required) |
| QA-26 | OBS | QA-26 | -: deliver twice | PK import_manifest_reconstruction called twice on identical inputs | 3 | - | the second import is refused or yields different stable counts (the limitation changed: new oracle version required) |
| QA-OBS-EXACT | OBS | O-CP3/O-RB2/O-RB3/O-PK2c/O-PK5 | none | projections of the QA-01/QA-02 native outputs | 8 | - | any exact form differs (record as drift; never re-baseline silently) |

## Non-mandatory cases

* **QA-I1** (INFO) N3-GATE (contract gate; mutated byte unspecified) — Architect D9: informational; mutation byte unspecified; largely covered by QA-08/QA-09
* **QA-I2** (INFO) QA-21 delete runtime_proposal at Pack level — Architect D9: informational; native outcome not derived (Pack importer.py:1039,1075,1084 are proposal-conditioned)
* **QA-14** (NA) Corrupted persisted bundle bytes (invalid JSON) — No native boundary on the C4 chain parses persisted bundle JSON text: Pack import_manifest_reconstruction takes parsed dicts (importer.py:1579-1581, 332-335) and the C4 harness parses with its own subject-owned parser (real_c4.py:131-149). Off-path native text parsers (Pack admission.loads; Replay ingress.load_json_bounded) are outside the C4 chain and outside Q-A.

## Source references per observation (RI, CTL, PRE, OBS)

| Observation | Boundary | Pointer | Op | Source |
|---|---|---|---|---|
| QA-S1.1 | source_identity | `/commits` | eq | frozen literal |
| QA-S1.2 | source_identity | `/trees` | eq | frozen literal |
| QA-S2.1 | file_identity | `/sha256` | eq | frozen literal |
| QA-S2.2 | file_identity | `/git_blob` | eq | frozen literal |
| QA-S3.1 | snapshot_identity | `/sha256` | eq | frozen literal |
| QA-E1.1 | artifact_identity | `/zip_sha256` | eq | frozen literal |
| QA-E1.2 | artifact_identity | `/c4_members_sha256` | eq | frozen literal |
| QA-01.1 | am_validate | `/valid` | eq | AM src/agent_action_manifest/validator.py:51 [INFERRED] |
| QA-01.2 | am_validate | `/manifest_digest` | eq | AM src/agent_action_manifest/binding.py:31 [SOURCE-READ] |
| QA-01.3 | am_validate | `/proposal_digest` | eq | AM src/agent_action_manifest/binding.py:39 [SOURCE-READ] |
| QA-01.4 | am_validate | `/proposal_mismatches` | len_eq | AM src/agent_action_manifest/binding.py:48 [SOURCE-READ] |
| QA-01.5 | cp_record | `/decisions` | len_eq | CP src/agent_control_plane/bounded.py:1679 [SOURCE-READ] |
| QA-01.6 | cp_record | `/attempts` | len_eq | CP src/agent_control_plane/bounded.py:1648 [SOURCE-READ] |
| QA-01.7 | cp_record | `/observations` | len_eq | CP src/agent_control_plane/bounded.py:1648 [SOURCE-READ] |
| QA-01.8 | cp_record | `/reconciliations` | len_eq | CP src/agent_control_plane/bounded.py:1648 [SOURCE-READ] |
| QA-01.9 | cp_record | `/decisions/0/effect_id` | sha256_format | CP src/agent_control_plane/bounded.py:2031 [SOURCE-READ] |
| QA-01.10 | cp_record | `/decisions/0/operation_horizon/proposal_commitment` | eq_ref | CP src/agent_control_plane/bounded.py:1339 [SOURCE-READ] |
| QA-01.11 | cp_record | `/decisions/0/result` | eq | CP src/agent_control_plane/bounded.py:1667 [SOURCE-READ] |
| QA-01.12 | cp_record | `/decisions/0/reasons` | len_eq | CP src/agent_control_plane/bounded.py:1667 [SOURCE-READ] |
| QA-01.13 | cp_record | `/decisions/0/binding/proposal_commitment` | eq_ref | CP src/agent_control_plane/bounded.py:2523 [SOURCE-READ] |
| QA-01.14 | cp_record | `/decisions/0/binding/manifest_digest` | eq_ref | CP src/agent_control_plane/bounded.py:2643 [SOURCE-READ] |
| QA-01.15 | cp_record | `/decisions/0/binding/tenant_id` | eq | CP src/agent_control_plane/bounded.py:2635 [SOURCE-READ] |
| QA-01.16 | cp_record | `/decisions/0/binding/generation` | eq | CP src/agent_control_plane/bounded.py:57 [SOURCE-READ] |
| QA-01.17 | replay_bundle | `/status` | eq | RB src/agent_replay_bundle/importers.py:1247 [SOURCE-READ] |
| QA-01.18 | replay_bundle | `/import_reports/0/findings` | any_item_matches | RB src/agent_replay_bundle/importers.py:1209 [SOURCE-READ] |
| QA-01.19 | replay_bundle | `/import_reports/0/findings` | none_item_matches | RB src/agent_replay_bundle/importers.py:1008 [SOURCE-READ] |
| QA-01.20 | replay_bundle | `/import_reports/0/findings` | none_item_matches | RB src/agent_replay_bundle/importers.py:1080 [SOURCE-READ] |
| QA-01.21 | replay_bundle | `/semantics/external_effect_execution` | eq | RB src/agent_replay_bundle/importers.py:1253 [SOURCE-READ] |
| QA-01.22 | replay_bundle | `/semantics/destination_observation` | eq | RB src/agent_replay_bundle/importers.py:1253 [SOURCE-READ] |
| QA-01.23 | replay_bundle | `/semantics/policy_reevaluation` | eq | RB src/agent_replay_bundle/importers.py:1253 [SOURCE-READ] |
| QA-01.24 | replay_bundle | `#input:cp_record` | eq_ref | evaluator relation |
| QA-01.25 | pack | `/metadata/traceable_import/derived_counts/authorization_granted_count` | int_eq | PK src/agent_governance_evidence_pack/importer.py:1157 [SOURCE-READ] |
| QA-01.26 | pack | `/metadata/traceable_import/derived_counts/authorization_held_count` | int_eq | PK src/agent_governance_evidence_pack/importer.py:1157 [SOURCE-READ] |
| QA-01.27 | pack | `/metadata/traceable_import/derived_counts/authorization_denied_count` | int_eq | PK src/agent_governance_evidence_pack/importer.py:1157 [SOURCE-READ] |
| QA-01.28 | pack | `/metadata/traceable_import/derived_counts/control_plane_attempt_count` | int_eq | PK src/agent_governance_evidence_pack/importer.py:1237 [INFERRED] |
| QA-01.29 | pack | `/metadata/traceable_import/derived_counts/executor_attempt_count` | int_eq | PK src/agent_governance_evidence_pack/importer.py:1237 [INFERRED] |
| QA-01.30 | pack | `/metadata/traceable_import/derived_counts/attempt_transition_record_count` | int_eq | PK src/agent_governance_evidence_pack/importer.py:1237 [INFERRED] |
| QA-01.31 | pack | `/metadata/traceable_import/derived_counts/destination_effect_count` | int_eq | PK src/agent_governance_evidence_pack/importer.py:1237 [INFERRED] |
| QA-01.32 | pack | `/metadata/traceable_import/derived_counts/effect_observation_count` | int_eq | PK src/agent_governance_evidence_pack/importer.py:1237 [INFERRED] |
| QA-01.33 | pack | `/metadata/traceable_import/derived_counts/reconciliation_count` | int_eq | PK src/agent_governance_evidence_pack/importer.py:1237 [INFERRED] |
| QA-01.34 | pack | `/metadata/traceable_import/derived_counts/distinct_effect_count` | int_eq | PK src/agent_governance_evidence_pack/importer.py:1237 [SOURCE-READ] |
| QA-01.35 | pack | `/metadata/traceable_import/derived_counts/decision_count` | int_eq | PK src/agent_governance_evidence_pack/importer.py:1237 [SOURCE-READ] |
| QA-01.36 | pack | `/metadata/traceable_import/lifecycle_summary/authorization` | eq | PK src/agent_governance_evidence_pack/importer.py:1146 [SOURCE-READ] |
| QA-01.37 | pack | `/metadata/traceable_import/lifecycle_summary/current_permission` | eq | PK src/agent_governance_evidence_pack/importer.py:1274 [SOURCE-READ] |
| QA-01.38 | pack | `/metadata/traceable_import/lifecycle_summary/execution_attempted` | eq | PK src/agent_governance_evidence_pack/importer.py:1274 [SOURCE-READ] |
| QA-01.39 | pack | `/metadata/traceable_import/lifecycle_summary/independent_verification` | eq | PK src/agent_governance_evidence_pack/importer.py:1274 [SOURCE-READ] |
| QA-01.40 | pack | `/replay_bundles/0/status` | eq | PK src/agent_governance_evidence_pack/importer.py:1031 [SOURCE-READ] |
| QA-01.41 | pack | `/replay_bundles/0/validation_status` | eq | PK src/agent_governance_evidence_pack/importer.py:1594 [SOURCE-READ] |
| QA-01.42 | pack | `/replay_bundles/0/signed` | eq | PK src/agent_governance_evidence_pack/importer.py:1594 [SOURCE-READ] |
| QA-01.43 | pack | `/review_status` | eq | PK src/agent_governance_evidence_pack/importer.py:1594 [SOURCE-READ] |
| QA-01.44 | pack | `#input:replay_bundle` | eq_ref | evaluator relation |
| QA-02.1 | am_validate | `/valid` | eq | AM src/agent_action_manifest/validator.py:51 [INFERRED] |
| QA-02.2 | am_validate | `/manifest_digest` | eq | AM src/agent_action_manifest/binding.py:31 [SOURCE-READ] |
| QA-02.3 | am_validate | `/proposal_digest` | eq | AM src/agent_action_manifest/binding.py:39 [SOURCE-READ] |
| QA-02.4 | am_validate | `/proposal_mismatches` | len_eq | AM src/agent_action_manifest/binding.py:48 [SOURCE-READ] |
| QA-02.5 | cp_record | `/decisions` | len_eq | CP src/agent_control_plane/bounded.py:1679 [SOURCE-READ] |
| QA-02.6 | cp_record | `/attempts` | len_eq | CP src/agent_control_plane/bounded.py:1648 [SOURCE-READ] |
| QA-02.7 | cp_record | `/observations` | len_eq | CP src/agent_control_plane/bounded.py:1648 [SOURCE-READ] |
| QA-02.8 | cp_record | `/reconciliations` | len_eq | CP src/agent_control_plane/bounded.py:1648 [SOURCE-READ] |
| QA-02.9 | cp_record | `/decisions/0/effect_id` | sha256_format | CP src/agent_control_plane/bounded.py:1659 [SOURCE-READ] |
| QA-02.10 | cp_record | `/decisions/0/operation_horizon/proposal_commitment` | eq_ref | CP src/agent_control_plane/bounded.py:1339 [SOURCE-READ] |
| QA-02.11 | cp_record | `/decisions/0/result` | eq | CP src/agent_control_plane/bounded.py:1667 [SOURCE-READ] |
| QA-02.12 | cp_record | `/decisions/0/binding` | is_null | CP src/agent_control_plane/bounded.py:1675 [SOURCE-READ] |
| QA-02.13 | cp_record | `/decisions/0/reasons` | list_contains | CP src/agent_control_plane/bounded.py:2432 [SOURCE-READ] |
| QA-02.14 | replay_bundle | `/status` | eq | RB src/agent_replay_bundle/importers.py:1247 [SOURCE-READ] |
| QA-02.15 | replay_bundle | `/import_reports/0/findings` | any_item_matches | RB src/agent_replay_bundle/importers.py:1209 [SOURCE-READ] |
| QA-02.16 | replay_bundle | `/import_reports/0/findings` | none_item_matches | RB src/agent_replay_bundle/importers.py:1008 [SOURCE-READ] |
| QA-02.17 | replay_bundle | `/import_reports/0/findings` | any_item_matches | RB src/agent_replay_bundle/importers.py:1080 [SOURCE-READ] |
| QA-02.18 | replay_bundle | `/records` | any_item_matches | RB src/agent_replay_bundle/importers.py:1028 [SOURCE-READ] |
| QA-02.19 | replay_bundle | `/records` | none_item_matches | RB src/agent_replay_bundle/importers.py:1028 [SOURCE-READ] |
| QA-02.20 | replay_bundle | `/semantics/external_effect_execution` | eq | RB src/agent_replay_bundle/importers.py:1253 [SOURCE-READ] |
| QA-02.21 | replay_bundle | `/semantics/destination_observation` | eq | RB src/agent_replay_bundle/importers.py:1253 [SOURCE-READ] |
| QA-02.22 | replay_bundle | `/semantics/policy_reevaluation` | eq | RB src/agent_replay_bundle/importers.py:1253 [SOURCE-READ] |
| QA-02.23 | replay_bundle | `#input:cp_record` | eq_ref | evaluator relation |
| QA-02.24 | pack | `/metadata/traceable_import/derived_counts/authorization_granted_count` | int_eq | PK src/agent_governance_evidence_pack/importer.py:1157 [SOURCE-READ] |
| QA-02.25 | pack | `/metadata/traceable_import/derived_counts/authorization_held_count` | int_eq | PK src/agent_governance_evidence_pack/importer.py:1157 [SOURCE-READ] |
| QA-02.26 | pack | `/metadata/traceable_import/derived_counts/authorization_denied_count` | int_eq | PK src/agent_governance_evidence_pack/importer.py:1157 [SOURCE-READ] |
| QA-02.27 | pack | `/metadata/traceable_import/derived_counts/control_plane_attempt_count` | int_eq | PK src/agent_governance_evidence_pack/importer.py:1237 [INFERRED] |
| QA-02.28 | pack | `/metadata/traceable_import/derived_counts/executor_attempt_count` | int_eq | PK src/agent_governance_evidence_pack/importer.py:1237 [INFERRED] |
| QA-02.29 | pack | `/metadata/traceable_import/derived_counts/attempt_transition_record_count` | int_eq | PK src/agent_governance_evidence_pack/importer.py:1237 [INFERRED] |
| QA-02.30 | pack | `/metadata/traceable_import/derived_counts/destination_effect_count` | int_eq | PK src/agent_governance_evidence_pack/importer.py:1237 [INFERRED] |
| QA-02.31 | pack | `/metadata/traceable_import/derived_counts/effect_observation_count` | int_eq | PK src/agent_governance_evidence_pack/importer.py:1237 [INFERRED] |
| QA-02.32 | pack | `/metadata/traceable_import/derived_counts/reconciliation_count` | int_eq | PK src/agent_governance_evidence_pack/importer.py:1237 [INFERRED] |
| QA-02.33 | pack | `/metadata/traceable_import/derived_counts/distinct_effect_count` | int_eq | PK src/agent_governance_evidence_pack/importer.py:1237 [SOURCE-READ] |
| QA-02.34 | pack | `/metadata/traceable_import/derived_counts/decision_count` | int_eq | PK src/agent_governance_evidence_pack/importer.py:1237 [SOURCE-READ] |
| QA-02.35 | pack | `/metadata/traceable_import/lifecycle_summary/authorization` | eq | PK src/agent_governance_evidence_pack/importer.py:1146 [SOURCE-READ] |
| QA-02.36 | pack | `/metadata/traceable_import/lifecycle_summary/current_permission` | eq | PK src/agent_governance_evidence_pack/importer.py:1274 [SOURCE-READ] |
| QA-02.37 | pack | `/metadata/traceable_import/lifecycle_summary/execution_attempted` | eq | PK src/agent_governance_evidence_pack/importer.py:1274 [SOURCE-READ] |
| QA-02.38 | pack | `/metadata/traceable_import/lifecycle_summary/independent_verification` | eq | PK src/agent_governance_evidence_pack/importer.py:1274 [SOURCE-READ] |
| QA-02.39 | pack | `/replay_bundles/0/status` | eq | PK src/agent_governance_evidence_pack/importer.py:1031 [SOURCE-READ] |
| QA-02.40 | pack | `/replay_bundles/0/validation_status` | eq | PK src/agent_governance_evidence_pack/importer.py:1594 [SOURCE-READ] |
| QA-02.41 | pack | `/replay_bundles/0/signed` | eq | PK src/agent_governance_evidence_pack/importer.py:1594 [SOURCE-READ] |
| QA-02.42 | pack | `/review_status` | eq | PK src/agent_governance_evidence_pack/importer.py:1594 [SOURCE-READ] |
| QA-02.43 | pack | `#input:replay_bundle` | eq_ref | evaluator relation |
| QA-03.1 | pack_import | `-` | raised_type | PK src/agent_governance_evidence_pack/importer.py:1061 [SOURCE-READ] |
| QA-03.2 | pack_import | `-` | raised_message_contains | PK src/agent_governance_evidence_pack/importer.py:1061 [SOURCE-READ] |
| QA-05.1 | pack_import | `-` | raised_type | PK src/agent_governance_evidence_pack/importer.py:701 [SOURCE-READ] |
| QA-05.2 | pack_import | `-` | raised_message_equals | PK src/agent_governance_evidence_pack/importer.py:701 [SOURCE-READ] |
| QA-08.1 | am_bind | `/proposal_mismatches` | seq_eq | AM src/agent_action_manifest/binding.py:62 [SOURCE-READ] |
| QA-08.2 | cp_record | `/decisions/0/result` | eq | CP src/agent_control_plane/bounded.py:2678 [SOURCE-READ] |
| QA-08.3 | cp_record | `/decisions/0/binding` | is_null | CP src/agent_control_plane/bounded.py:1675 [SOURCE-READ] |
| QA-08.4 | cp_record | `/decisions/0/reasons` | list_contains | CP src/agent_control_plane/bounded.py:2678 [SOURCE-READ] |
| QA-10.1 | replay_import | `-` | raised_type | RB src/agent_replay_bundle/importers.py:264 [SOURCE-READ] |
| QA-10.2 | replay_import | `-` | raised_message_contains | RB src/agent_replay_bundle/importers.py:264 [SOURCE-READ] |
| QA-12.1 | replay_import | `-` | raised_type | RB src/agent_replay_bundle/importers.py:847 [SOURCE-READ] |
| QA-12.2 | replay_import | `-` | raised_message_equals | RB src/agent_replay_bundle/importers.py:847 [SOURCE-READ] |
| QA-16.1 | pack_validation | `/valid` | eq | PK src/agent_governance_evidence_pack/validator.py:507 [SOURCE-READ] |
| QA-16.2 | pack_validation | `/issues` | any_item_matches | PK src/agent_governance_evidence_pack/validator.py:507 [SOURCE-READ] |
| QA-27.1 | pack_validation | `/valid` | eq | PK src/agent_governance_evidence_pack/validator.py:507 [SOURCE-READ] |
| QA-27.2 | pack_validation | `/issues` | any_item_matches | PK src/agent_governance_evidence_pack/validator.py:507 [SOURCE-READ] |
| QA-18.1 | pack_import | `-` | raised_type | PK src/agent_governance_evidence_pack/importer.py:1017 [SOURCE-READ] |
| QA-18.2 | pack_import | `-` | raised_message_contains | PK src/agent_governance_evidence_pack/importer.py:1017 [SOURCE-READ] |
| QA-19.1 | am_load | `-` | raised_type | AM src/agent_action_manifest/loader.py:46 [SOURCE-READ] |
| QA-19.2 | am_load | `-` | raised_message_contains | AM src/agent_action_manifest/loader.py:46 [SOURCE-READ] |
| QA-22.1 | pack_import | `-` | raised_type | PK src/agent_governance_evidence_pack/importer.py:974 [SOURCE-READ] |
| QA-22.2 | pack_import | `-` | raised_message_contains | PK src/agent_governance_evidence_pack/importer.py:974 [SOURCE-READ] |
| QA-25.1 | replay_import | `-` | raised_type | RB src/agent_replay_bundle/importers.py:1078 [SOURCE-READ] |
| QA-25.2 | replay_import | `-` | raised_message_equals | RB src/agent_replay_bundle/importers.py:1078 [SOURCE-READ] |
| QA-09.1 | digest_full | `/am_digest` | eq_ref | limit L15 |
| QA-09.2 | digest_reduced | `/am_digest` | ne_ref | limit L15 |
| QA-11.1 | replay_import | `-` | returned | limit L22 |
| QA-11.2 | replay_bundle | `/status` | eq | RB src/agent_replay_bundle/importers.py:1045 [SOURCE-READ] |
| QA-11.3 | replay_bundle | `/import_reports/0/findings` | any_item_matches | RB src/agent_replay_bundle/importers.py:1080 [SOURCE-READ] |
| QA-17.1 | pack_import | `-` | returned | limit L7 |
| QA-17.2 | pack | `/replay_bundles/0/bundle_id` | eq | PK src/agent_governance_evidence_pack/importer.py:1588 [SOURCE-READ] |
| QA-17.3 | pack_validation | `/valid` | eq | limit L11 |
| QA-17.4 | pack_validation | `/issues` | none_item_matches | limit L19 |
| QA-26.1 | pack_first | `-` | returned | limit L14 |
| QA-26.2 | pack_second | `-` | returned | limit L14 |
| QA-26.3 | pack_second | `` | eq_ref | PK src/agent_governance_evidence_pack/importer.py:1590 [SOURCE-READ] |
| QA-OBS-EXACT.1 | cp_pos | `/decisions/0/reasons` | seq_eq | CP src/agent_control_plane/bounded.py:1667 [INFERRED] |
| QA-OBS-EXACT.2 | cp_hold | `/decisions/0/reasons` | seq_eq | CP src/agent_control_plane/bounded.py:2432 [INFERRED] |
| QA-OBS-EXACT.3 | rb_pos | `/import_reports/0/findings` | len_eq | RB src/agent_replay_bundle/importers.py:1209 [INFERRED] |
| QA-OBS-EXACT.4 | rb_hold | `/import_reports/0/findings` | len_eq | RB src/agent_replay_bundle/importers.py:1080 [INFERRED] |
| QA-OBS-EXACT.5 | pk_val_pos | `/valid` | eq | PK src/agent_governance_evidence_pack/validator.py:58 [INFERRED] |
| QA-OBS-EXACT.6 | pk_val_pos | `/issues` | none_item_matches | PK src/agent_governance_evidence_pack/validator.py:58 [INFERRED] |
| QA-OBS-EXACT.7 | pk_val_hold | `/valid` | eq | PK src/agent_governance_evidence_pack/validator.py:58 [INFERRED] |
| QA-OBS-EXACT.8 | pk_val_hold | `/issues` | none_item_matches | PK src/agent_governance_evidence_pack/validator.py:58 [INFERRED] |

## Exclusions (each documented)

* **QA-04** — *redundant*: coordinated flip hits the same Pack retained-field equality (importer.py:1012-1017) as QA-18; that check is a consistency re-derivation, not tamper evidence (RI-WEAK)
* **QA-06** — *redundant*: edited hold reasons: covered by L22/L25 inventory and QA-11; no native refusal
* **QA-07** — *redundant*: stripping the binding from an authorized decision is the same Pack predicate (importer.py:1059-1061) as QA-03
* **QA-13** — *deferred*: caller-asserted revision label (L10); unconfirmed native check
* **QA-15** — *deferred*: valid-JSON edit of a persisted bundle field: no native digest applied (L19); evaluator hash comparison is covered by QA-S2/QA-E1
* **QA-20** — *deferred*: Replay import without proposal only warns (B002); outside minimum claim
* **QA-23** — *deferred*: wrong tenant at decide: tenant integrity at the Replay boundary is covered by QA-10; CP-boundary variant deferred
* **QA-24** — *outside Q-A*: freshness/custody/authenticated origin are Q-C (L7-L9); no native check
* **effect_id differs by verdict (L23)** — *deferred*: literal effect_id values are observation-derived; only sha256 format and horizon-commitment continuity are asserted
* **false-PASS, zero-case and skipped-case detection** — *evaluator property*: tested by self-tests EST-06/EST-08/EST-11 and engine guards, not by a subject case
* **wrong-owner representation** — *outside Q-A*: no native semantics

## Coverage of the Architect's mandatory list

| Required coverage | Cases |
|---|---|
| Exact source and configuration identity | QA-S1, QA-S2 |
| Manifest/proposal commitment integrity | QA-01, QA-08 (and QA-09 as OBS under Hub #280) |
| Native authorized positive | QA-01 |
| Revoked-grant HOLD | QA-02 |
| Downstream preservation of HOLD evidence | QA-02 (Replay record + Pack lifecycle/counters) |
| Held-to-authorized structural mutation | QA-03 |
| Authorized-record tenant substitution | QA-10 |
| Incorrect source revision/profile | QA-12 (Replay revision), QA-22 (modified Replay checkout) |
| Malformed or missing mandatory evidence | QA-05, QA-19 (QA-14 is NOT APPLICABLE on the C4 path) |
| Replay partial-status inflation | QA-18 |
| Incorrect Pack authorization counts | QA-27 |
| Incorrect effect/attempt counts | QA-16 (+ zero counts asserted in QA-01/QA-02) |
| Module/fixture hash tampering | QA-S2 (evaluator), QA-22 (native) |
| Missing evidence files | QA-19, QA-05, QA-E1 (retained bytes); evaluator missing-raw => INCONCLUSIVE |
| False PASS, zero-case and skipped-case detection | evaluator guards, proven by self-tests EST-06/EST-08/EST-11 (not a subject case) |
| Known-limit observations kept separate | QA-09 (#280), QA-11 (L22), QA-17, QA-26, QA-OBS-EXACT |
