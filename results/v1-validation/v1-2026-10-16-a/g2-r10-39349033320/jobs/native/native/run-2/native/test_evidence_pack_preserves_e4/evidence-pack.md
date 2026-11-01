# Traceable Agent Governance Evidence Pack

| Field | Value |
|---|---|
| Pack ID | agep-4bb57d4423a93740 |
| Version | 0.2.0 |
| Generated At | 2026-10-20T00:42:32.919178+00:00 |
| Review Status (asserted, unverified) | draft |
| Agent | Synthetic Refund Agent |
| Environment | other |
| Owner | cognous-integration-pilot |
| Business Unit | — |

## 1. Executive Summary

**Synthetic Refund Agent** is represented in this evidence pack for the **other** environment. Business purpose: Imported from Manifest and Reconstruction Bundle; business purpose unavailable.

The pack records **1** tool(s), **2** action(s), **2** privileged/review-sensitive action(s), and **1** replay/reconstruction bundle reference(s).

Validation summary (asserted, unverified): 1 valid bundle(s), 0 invalid bundle(s), 0 error(s), 1 warning(s).
Source artifacts were evaluated by supported semantic import checks; inspect the actual findings. This does not establish deployment approval, compliance, operational effectiveness, or independent audit.

No open risks recorded. Absence of incident records does not prove absence of incidents.

## 2. Agent Overview

**Agent Name:** Synthetic Refund Agent

**Description:** Synthetic bounded integration fixture; not deployed and not an institutional grant.

**Business Purpose:** Imported from Manifest and Reconstruction Bundle; business purpose unavailable.

**Owner:** cognous-integration-pilot

**Business Unit:** —

**User Population:** —

**Lifecycle Stage:** —


## 3. Deployment Context

**Environment:** other

**Deployment Name:** synthetic

**Deployment Date:** —

**Systems Touched:** synthetic-refund-ledger

**Data Domains:** —

**Geographic Scope:** —

**Notes:** Generated from retained producer artifacts; does not establish deployment approval or operational effectiveness.


## 4. Tool Inventory

| Tool Name | Description | External System | Data Classification | Access Mode | Control Status |
|---|---|---|---|---|---|
| refund_adapter | Synthetic refund destination adapter. | synthetic-refund-ledger | synthetic | — | planned |

## 5. Action Inventory

| Action Name | Tool | Type | Authority Required | Review Required | Reliance Required | Default Posture | Control Status |
|---|---|---|---|---|---|---|---|
| refund_issue_routine | refund_adapter | write | Yes | Yes | Yes | escalate | planned |
| refund_issue_high_consequence | refund_adapter | write | Yes | Yes | Yes | escalate | planned |

## 6. Authority Model

**Summary:** Authority evidence imported from retained runtime records. This is not a grant or approval.

**Authority Scopes:** —

**Privileged Action Types:** write

**Expiration Required:** Yes

**Human Approval Required:** Yes

**Notes:** Authority Context profile references remain distinct from context-instance identifiers.


## 7. Policy Controls

| Control Name | Description | Status | Evidence Reference |
|---|---|---|---|
| Manifest declaration | Actions and requirements imported from Manifest v1.1. Declaration alone does not establish implementation. | planned | metadata.traceable_import.input_artifacts&#91;manifest&#93; |
| Review and approval declaration | Manifest review_requirement and approval-related declarations are preserved for review support; declaration alone does not create human approval. | planned | manifest.actions&#91;*&#93;.review_requirement |
| Replay semantic import validation | The importer executed the accepted Replay semantic validator over retained producer records. This is import-time evidence checking, not evidence that runtime controls were operationally effective. | implemented | metadata.traceable_import.replay_semantic_validation |
| Independent operational verification | No independent real-world effect verification supplied. | planned | metadata.traceable_import.lifecycle_summary.independent_verification |

## 8. Blocked-Action Summary

No blocked actions recorded.

## 9. Reliance Summary

No reliance records recorded.

## 10. Replay Bundle Inventory

_These values are caller assertions recorded in the pack. They are not verified by this renderer: no reviewer identity, signature, redaction or validation result is checked._

| Bundle ID | Run ID | Status | Generated At | Signed (asserted, unverified) | Redacted (asserted, unverified) | Validation Status (asserted, unverified) | Evidence Reference |
|---|---|---|---|---|---|---|---|
| 09f74557-30dd-416e-801a-fc77b23b97cb | run-1 | validated_complete | 2026-10-20T00:42:32.919178+00:00 | No | No | semantically_valid | metadata.traceable_import.source_record_refs |

## 11. Validation Summary

_These values are caller assertions recorded in the pack. They are not verified by this renderer: no reviewer identity, signature, redaction or validation result is checked._

**Valid Bundles:** 1 | **Invalid Bundles:** 0 | **Errors:** 0 | **Warnings:** 1

Source artifacts were evaluated by supported semantic import checks; inspect the actual findings. This does not establish deployment approval, compliance, operational effectiveness, or independent audit.


## 12. Redaction and Export Summary

No redaction or export records recorded.

## 13. Risk Register

No risks recorded. Missing incident records do not prove that no incidents occurred.

## 14. Review Records

No review records recorded. Default review status remains unreviewed/draft unless supplied by an attributable human reviewer.

## 15. Known Limitations

This evidence pack summarizes available runtime and governance records. It does not prove that model outputs are correct, policy controls are sufficient, compliance obligations are satisfied, deployment is approved, controls are operationally effective, or independent audit has occurred. Schema validity and successful reconstruction are review aids only.

## 16. Traceability and Import Provenance

This section is generated from `metadata.traceable_import`. It is review support only. It does not certify deployment approval, compliance, operational effectiveness, or independent audit.

### Input artifacts

| Role | Artifact ID | Version | Hash | Trusted Revision | Verification Status |
|---|---|---|---|---|---|
| manifest | refund-integration-pilot-v1 | 1.1 | sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac | ff5490828b2bf7f6a976da209f3f533701855687 | digest_and_cross_artifact_binding_checked_when_runtime_proposal_present |
| reconstruction_bundle | 09f74557-30dd-416e-801a-fc77b23b97cb | 0.2.0 | sha256:5d29d0f22df99dd84bf505cd97fcc959b3ca5af73e53c65e50748b69202c9f6f | 6a6a477495ac24e813f12bb0fe314acfe8bac9cf | validated_complete |

### Transformation

| Field | Value |
|---|---|
| Transformation Version | agep-manifest-reconstruction-import/0.3.8-programme2-profiles-candidate |
| Canonicalization Profile | json-sort-keys-compact-utf8-no-nan |

### Selected producer revisions

| Component | Selected Revision |
|---|---|
| manifest | ff5490828b2bf7f6a976da209f3f533701855687 |
| replay | 6a6a477495ac24e813f12bb0fe314acfe8bac9cf |
| control_plane | 2bac7875391cad0a431fa0d75208b7ade39743e3 |
| moltbot_safe | 6b16962db140590b808f02b5c2cb11a217aec46f |

### Supported producer revision sets

| Component | Supported Revisions |
|---|---|
| manifest | ff5490828b2bf7f6a976da209f3f533701855687 |
| replay | 6a6a477495ac24e813f12bb0fe314acfe8bac9cf |
| control_plane | 2bac7875391cad0a431fa0d75208b7ade39743e3 |
| moltbot_safe | 6b16962db140590b808f02b5c2cb11a217aec46f |

### Derived counts

| Count | Value |
|---|---|
| proposal_count | 1 |
| decision_count | 1 |
| distinct_effect_count | 1 |
| control_plane_attempt_count | 0 |
| executor_attempt_count | 0 |
| attempt_transition_record_count | 0 |
| authorization_granted_count | 1 |
| authorization_held_count | 0 |
| authorization_denied_count | 0 |
| acknowledgement.execution_result_unknown | 1 |

Counting rules:
- Repeated lifecycle records do not inflate attempt counts.
- Duplicate submissions do not inflate distinct effect counts when effect_id is unchanged.
- Control Plane and executor attempt IDs are separate namespaces unless explicit correlation exists.
- Destination effects, effect observations and reconciliations are counted separately.
- Missing observations are unavailable, not success or failure.
- Latest supported state uses Replay producer sequence and exact effect lineage; earlier rejection remains visible. Independent clocks do not establish ordering.

### Lifecycle and effect status

| Dimension | Value |
|---|---|
| authorization | authorized |
| current_permission | not_evaluated_from_historical_records |
| execution_attempted | no |
| acknowledgement | not_applicable |
| destination_observed | unknown |
| destination_observation_scope | latest supplied Control Plane reconciliation per exact effect; not a fresh query |
| reconstruction_status | reconstruction_complete |
| retry_permission | not_established |
| independent_verification | unavailable |

- Historical authorization is retained evidence and does not establish current permission.
- Control Plane transition status is preserved separately from acknowledgement receipt.
- Executor acknowledgement is distinct from independently verified delivery.
- A lost or unknown acknowledgement followed by an applied observation retains both facts.
- Observed local destination state does not establish independently verified institutional outcome.
- Reconstruction completeness does not mean effect completion.
- HMAC/shared-secret integrity is not public issuer identity or independent review.
- A software-generated pack cannot create human approval.

### Control evidence levels

| Level | Status | Evidence | Meaning |
|---|---|---|---|
| semantic_validation_performed_during_import | validated_complete | metadata.traceable_import.replay_semantic_validation | the importer executed the accepted Replay semantic validator; this is not a test-run or runtime-control-effectiveness claim |
| source_asserted_runtime_evidence | unavailable | — | no source runtime or fixture provenance was supplied |
| attributable_test_run_evidence | unavailable | — | no complete attributable test-run provenance was supplied |
| declared | present | manifest | control or requirement is declared only |
| implemented | not_established_by_import | — | implementation requires producer-specific evidence; manifest declarations and import success do not suffice |
| tested | unavailable | — | semantic import validation and source runtime records do not by themselves establish that a test occurred |
| tested_in_this_repository | not_evaluated_during_import | — | this import does not execute or imply execution of the Evidence Pack repository test suite |
| operationally_observed | unavailable | — | no production operational observation supplied |
| independently_audited | unavailable | — | no independent audit or certification supplied |

### Import findings and unresolved limitations

| Code | Severity | Path/Source | Message |
|---|---|---|---|
| REPLAY_M003 | info | moltbot.execution_envelope.operation.institution_id | Institution/domain provenance is the trusted Moltbot integration context, not Control Plane AuthorizationBinding. |
| REPLAY_M004 | info | moltbot.execution_envelope.operation.authority_context_id | At the pinned adapter this field carries the proposal profile reference; it is distinct from the Control Plane binding context-instance ID. |
| REPLAY_SEMANTIC_LIMITATION | info | semantics.notes | Replay reconstructs recorded events only; import never renews permission or creates an effect. |
| R_REDACTION_UNVERIFIED | warning | — | Source declarations do not verify removal of sensitive content; export safety is unverified. |

### Unresolved issues

| Code | Severity | Message |
|---|---|---|
| U_INDEPENDENT_VERIFICATION_UNAVAILABLE | warning | Destination observation is producer-retained unless independent verifier evidence is supplied. |
| U_OPERATIONAL_EFFECTIVENESS_NOT_MEASURED | warning | Synthetic import success cannot support operational effectiveness or deployment approval. |
| U_HISTORICAL_AUTHORIZATION_NOT_CURRENT_PERMISSION | info | Retained authorization is historical evidence only; current permission must be re-evaluated by the runtime authority/control boundary. |
| U_EXCHANGE_METADATA_SUPPLEMENTARY | info | Accepted GAX/IMX exchange metadata remains supplementary unless represented by a supported Replay mapping; the Evidence Pack does not invent exchange fields. |

### Producer profiles

| Profile | Repository | Revision | Format Version | Revision Check | Independent Provenance Verification |
|---|---|---|---|---|---|
| control-plane-programme2-profiles@2bac7875 | cogno-us/cognous-agent-control-plane | 2bac7875391cad0a431fa0d75208b7ade39743e3 | — | declared_revision_matches_accepted_pin | not_performed |
| moltbot-safe-executor-producer-2.0.0@6b16962d | cogno-us/moltbot-safe | 6b16962db140590b808f02b5c2cb11a217aec46f | 2.0.0 | declared_revision_matches_accepted_pin | not_performed |

### Executor producer contract

| Field | Value |
|---|---|
| interface_profile_id | urn:cognous:profiles:moltbot-safe-executor-producer |
| interface_profile_version | 2.0.0 |
| repository_revision | 6b16962db140590b808f02b5c2cb11a217aec46f |
| legacy | False |
| source_asserted_repository_revision | 6b16962db140590b808f02b5c2cb11a217aec46f |
| source_asserted_profile_id | urn:cognous:profiles:moltbot-safe-executor-producer |
| source_asserted_profile_version | 2.0.0 |
| independently_established_count | 0 |

Executor producer metadata and repository revision are source assertions unless separately established. A locally computed commitment or successful semantic import does not authenticate the producer or independently verify the outcome.

### Conversion losses and source findings

| Code | Category | Severity | Path | Value State | Message |
|---|---|---|---|---|---|
| M003 | conversion_warning | info | moltbot.execution_envelope.operation.institution_id | — | Institution/domain provenance is the trusted Moltbot integration context, not Control Plane AuthorizationBinding. |
| M004 | conversion_warning | info | moltbot.execution_envelope.operation.authority_context_id | — | At the pinned adapter this field carries the proposal profile reference; it is distinct from the Control Plane binding context-instance ID. |

### Supporting source-record references

| Record ID | Type | Producer Profile | Evidence Class (source assertion) | Producer Revision | Revision Check | Source Path |
|---|---|---|---|---|---|---|
| control-plane-programme2-profiles@2bac7875:runtime_proposal:0 | runtime_proposal | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | proposal |
| control-plane-programme2-profiles@2bac7875:runtime_decision:1 | runtime_decision | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | decisions&#91;0&#93; |
| control-plane-programme2-profiles@2bac7875:effect_time_refusal:2 | effect_time_refusal | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | refusals&#91;0&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check:3 | resolution_check | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | resolution_checks&#91;0&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check:4 | resolution_check | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | resolution_checks&#91;1&#93; |
| control-plane-programme2-profiles@2bac7875:input_time_floors:5 | input_time_floors | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | input_time_floors |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:6 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;0&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:7 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;1&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:8 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;2&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:9 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;3&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:10 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;4&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:11 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;5&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:12 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;6&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:13 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;7&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:14 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;8&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:15 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;9&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:16 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;10&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:17 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;11&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:18 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;12&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:19 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;13&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:20 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;14&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:21 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;15&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:22 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;16&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:23 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;17&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:24 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;18&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:25 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;19&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:26 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;20&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:27 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;21&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:28 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;22&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:29 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;23&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:30 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;24&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:31 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;25&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:32 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;26&#93; |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:33 | resolution_check_event | control-plane-programme2-profiles@2bac7875 | producer_reported | 2bac7875391cad0a431fa0d75208b7ade39743e3 | declared_revision_matches_accepted_pin | check_events&#91;27&#93; |
| moltbot-safe-executor-producer-2.0.0@6b16962d:execution_envelope:34 | execution_envelope | moltbot-safe-executor-producer-2.0.0@6b16962d | producer_reported | 6b16962db140590b808f02b5c2cb11a217aec46f | declared_revision_matches_accepted_pin | moltbot.execution_envelope |
| moltbot-safe-executor-producer-2.0.0@6b16962d:executor_control_plane_evidence:35 | executor_control_plane_evidence | moltbot-safe-executor-producer-2.0.0@6b16962d | producer_reported | 6b16962db140590b808f02b5c2cb11a217aec46f | declared_revision_matches_accepted_pin | moltbot.control_plane_evidence |
| moltbot-safe-executor-producer-2.0.0@6b16962d:execution_result:36 | execution_result | moltbot-safe-executor-producer-2.0.0@6b16962d | producer_reported | 6b16962db140590b808f02b5c2cb11a217aec46f | declared_revision_matches_accepted_pin | moltbot.execution_result |

### Source-supplied commitments

| Record ID | Label | Commitment | Algorithm | Canonicalization | Source Verification Status | Source Path |
|---|---|---|---|---|---|---|
| control-plane-programme2-profiles@2bac7875:runtime_proposal:0 | payload_commitment | sha256:6b782ebbcc034edeca4069b31aa4d8cbc9d3eeaf3b2034ab989bb430de962c0e | SHA-256 | json-sort-keys-compact-utf8-no-nan | checked_match | proposal.payload_commitment |
| control-plane-programme2-profiles@2bac7875:runtime_decision:1 | effect_id | sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829 | SHA-256 | json-sort-keys-compact-utf8-no-nan | checked_match | decisions&#91;0&#93;.effect_id |
| control-plane-programme2-profiles@2bac7875:runtime_decision:1 | proposal_commitment | sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b | SHA-256 | json-sort-keys-compact-utf8-no-nan | attributed_claim | decisions&#91;0&#93;.binding.proposal_commitment |
| control-plane-programme2-profiles@2bac7875:runtime_decision:1 | manifest_digest | sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac | SHA-256 | json-sort-keys-compact-utf8-no-nan | attributed_claim | decisions&#91;0&#93;.binding.manifest_digest |
| control-plane-programme2-profiles@2bac7875:runtime_decision:1 | payload_commitment | sha256:6b782ebbcc034edeca4069b31aa4d8cbc9d3eeaf3b2034ab989bb430de962c0e | SHA-256 | json-sort-keys-compact-utf8-no-nan | attributed_claim | decisions&#91;0&#93;.binding.payload_commitment |
| control-plane-programme2-profiles@2bac7875:runtime_decision:1 | requirement_commitment | sha256:6590406e701b51e637c87953860d1ceb72d8da0af87311048f152e0ee2b8ccb6 | SHA-256 | json-sort-keys-compact-utf8-no-nan | attributed_claim | decisions&#91;0&#93;.binding.requirement_commitment |
| control-plane-programme2-profiles@2bac7875:runtime_decision:1 | role_mapping_digest | sha256:f8a8db156df7087ddf34be1ed77fc86fa20ba7668deb87a9b3a5bd0a6ace496d | SHA-256 | json-sort-keys-compact-utf8-no-nan | attributed_claim | decisions&#91;0&#93;.binding.role_mapping_digest |
| moltbot-safe-executor-producer-2.0.0@6b16962d:execution_envelope:34 | payload_commitment | sha256:6b782ebbcc034edeca4069b31aa4d8cbc9d3eeaf3b2034ab989bb430de962c0e | SHA-256 | json-sort-keys-compact-utf8-no-nan | checked_match | moltbot.execution_envelope.operation.payload_commitment |

### Locally computed record commitments

| Record ID | Local Commitment | Compatibility Hash Alias | Canonicalization | Verification Status |
|---|---|---|---|---|
| control-plane-programme2-profiles@2bac7875:runtime_proposal:0 | sha256:1afd891df02fda64ffd73bbaaf9eb2ba7ce3b0863c9d71598ab90602d6fa52f2 | sha256:1afd891df02fda64ffd73bbaaf9eb2ba7ce3b0863c9d71598ab90602d6fa52f2 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:runtime_decision:1 | sha256:a31643345102cbeb19d034efadfeff1a10725af6e0423e12a75c24f56622ca03 | sha256:a31643345102cbeb19d034efadfeff1a10725af6e0423e12a75c24f56622ca03 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:effect_time_refusal:2 | sha256:e23611378e80c4a08078bd12a8ce414c09d8563b4f6bdf2c1466938f2f8861b0 | sha256:e23611378e80c4a08078bd12a8ce414c09d8563b4f6bdf2c1466938f2f8861b0 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check:3 | sha256:e3cc5e3fe2783b1ad8e53a962c01df7379122aff8823961cb227d7689221983a | sha256:e3cc5e3fe2783b1ad8e53a962c01df7379122aff8823961cb227d7689221983a | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check:4 | sha256:095066fdde514b4c9fdec1ba37ac83b5d05c2d5b12c699f1f68122cfbcc13e85 | sha256:095066fdde514b4c9fdec1ba37ac83b5d05c2d5b12c699f1f68122cfbcc13e85 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:input_time_floors:5 | sha256:5bb5dad4cee13b6759a24d21e8188907c3e660c5b24b3209791cec62ea796d3d | sha256:5bb5dad4cee13b6759a24d21e8188907c3e660c5b24b3209791cec62ea796d3d | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:6 | sha256:54d708ff1f56d0c5eb1d6e09f1516b79c8f013ce42af8717f9ce506e7bc59d8d | sha256:54d708ff1f56d0c5eb1d6e09f1516b79c8f013ce42af8717f9ce506e7bc59d8d | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:7 | sha256:bc5023f4571a2b36dfa2d9a5521686a69c0b6f92b344fe717a699a043f8f14eb | sha256:bc5023f4571a2b36dfa2d9a5521686a69c0b6f92b344fe717a699a043f8f14eb | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:8 | sha256:a89e5a0c1e35defe5f4c9dc081b21ef540b2cecb29294058c74629ed24e92aaa | sha256:a89e5a0c1e35defe5f4c9dc081b21ef540b2cecb29294058c74629ed24e92aaa | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:9 | sha256:dafc1ea21477e6e9c00e9ceb673eaab1d16b2f6d7429d83c3a6b0b1862f6e6bd | sha256:dafc1ea21477e6e9c00e9ceb673eaab1d16b2f6d7429d83c3a6b0b1862f6e6bd | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:10 | sha256:31d5c485efa797c1108a28b14f24532814188c264865f952ad6c5d2f85a4fd0e | sha256:31d5c485efa797c1108a28b14f24532814188c264865f952ad6c5d2f85a4fd0e | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:11 | sha256:691476bb9e6c29660a6c508131fb51c1660e8f553ad1f4cda29dd150b7e32e33 | sha256:691476bb9e6c29660a6c508131fb51c1660e8f553ad1f4cda29dd150b7e32e33 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:12 | sha256:20f89c9c501c46334e5c076df100708ef94365790af6d1520be422e9aa411311 | sha256:20f89c9c501c46334e5c076df100708ef94365790af6d1520be422e9aa411311 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:13 | sha256:2407f49ec8b7ed7c8d2d57a1bb9d7499dbc8b73561d4a2cd63fa743a006033a4 | sha256:2407f49ec8b7ed7c8d2d57a1bb9d7499dbc8b73561d4a2cd63fa743a006033a4 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:14 | sha256:f480c14a15fff1b04ebc7d1ee47e670547a544aa6b449439e6bd78d594350572 | sha256:f480c14a15fff1b04ebc7d1ee47e670547a544aa6b449439e6bd78d594350572 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:15 | sha256:e0d6e409f084b4e98393b1916b7b58c8fc0052937988652ee63841260882f62a | sha256:e0d6e409f084b4e98393b1916b7b58c8fc0052937988652ee63841260882f62a | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:16 | sha256:45188949f064a2b56aa6d6937e79674cdbb1f9439c550404e07837e9f6281f03 | sha256:45188949f064a2b56aa6d6937e79674cdbb1f9439c550404e07837e9f6281f03 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:17 | sha256:31e6fda981695637e8f53b42cf81f504ad55a9d5cf9673502b8d838d59cbc26f | sha256:31e6fda981695637e8f53b42cf81f504ad55a9d5cf9673502b8d838d59cbc26f | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:18 | sha256:430e7f3ff67fa018acb6bb78c2bd64467ea70c45e2dba5d6db6d025d24926358 | sha256:430e7f3ff67fa018acb6bb78c2bd64467ea70c45e2dba5d6db6d025d24926358 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:19 | sha256:ddba867cb7c5f1e07dc4a317c4e002169b0d6d7174af5e223bef91e8731947ce | sha256:ddba867cb7c5f1e07dc4a317c4e002169b0d6d7174af5e223bef91e8731947ce | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:20 | sha256:9b9c28fc62cfe4affca60ee987b24debadb4de4331b8cb0ec9f6800f9adab917 | sha256:9b9c28fc62cfe4affca60ee987b24debadb4de4331b8cb0ec9f6800f9adab917 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:21 | sha256:db0ee14d96bb66899d7d4d3c60ce1db43edc7fd1c80055bd3d67f61533bcee59 | sha256:db0ee14d96bb66899d7d4d3c60ce1db43edc7fd1c80055bd3d67f61533bcee59 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:22 | sha256:31be8a3fbaac1adddeeac4be797882bdaf1091ec2894196e998ef30c7fd454d8 | sha256:31be8a3fbaac1adddeeac4be797882bdaf1091ec2894196e998ef30c7fd454d8 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:23 | sha256:3de22de6150b83966d4261784e57d6082b6679c4c2c1081dee4788db20b05783 | sha256:3de22de6150b83966d4261784e57d6082b6679c4c2c1081dee4788db20b05783 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:24 | sha256:dc2060ed680e2f2a2bc01eba03516fe944210d85f54af7513fe0657ee40cb676 | sha256:dc2060ed680e2f2a2bc01eba03516fe944210d85f54af7513fe0657ee40cb676 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:25 | sha256:e886346e925753f1773e01da1eb67a1a45d60fcd0bdb2241c37452cd6d054e7f | sha256:e886346e925753f1773e01da1eb67a1a45d60fcd0bdb2241c37452cd6d054e7f | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:26 | sha256:9927fe30675644db82780432b649365149ef9ed93eb74a34a21da155238f742c | sha256:9927fe30675644db82780432b649365149ef9ed93eb74a34a21da155238f742c | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:27 | sha256:655857f355a33f793714944c04c58a25846a2369dea39d7cd3b0285e4a8775c0 | sha256:655857f355a33f793714944c04c58a25846a2369dea39d7cd3b0285e4a8775c0 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:28 | sha256:082f9f66d24bcdda426a963089e9c6a3957d37572328fb25e2cfc71a4582fa94 | sha256:082f9f66d24bcdda426a963089e9c6a3957d37572328fb25e2cfc71a4582fa94 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:29 | sha256:6de35016d46305c9955fcd4aac1a5f0d873140dd922c1c860ab24f046bb40149 | sha256:6de35016d46305c9955fcd4aac1a5f0d873140dd922c1c860ab24f046bb40149 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:30 | sha256:588db970b764266fd72dac9dab14121b79e1f8885a32c2feea6dd1ee14791eda | sha256:588db970b764266fd72dac9dab14121b79e1f8885a32c2feea6dd1ee14791eda | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:31 | sha256:97e6ca2896b37fdd73e534377a009f4e06a175f95e2f4ee63404b63115fa9abc | sha256:97e6ca2896b37fdd73e534377a009f4e06a175f95e2f4ee63404b63115fa9abc | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:32 | sha256:08d4182f9a69643b8d30d333aac4019b62bdecaf10c18f7d77997fdb95c5e19e | sha256:08d4182f9a69643b8d30d333aac4019b62bdecaf10c18f7d77997fdb95c5e19e | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-programme2-profiles@2bac7875:resolution_check_event:33 | sha256:0f796835c36b2ef38e595ec8df0dc9e0317f261fc091b5b70069d6429934c359 | sha256:0f796835c36b2ef38e595ec8df0dc9e0317f261fc091b5b70069d6429934c359 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| moltbot-safe-executor-producer-2.0.0@6b16962d:execution_envelope:34 | sha256:aec272751a6bbecb1d0066758eac85696f3e81c0b55193a48cfb11385c5bafd3 | sha256:aec272751a6bbecb1d0066758eac85696f3e81c0b55193a48cfb11385c5bafd3 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| moltbot-safe-executor-producer-2.0.0@6b16962d:executor_control_plane_evidence:35 | sha256:17a53f7c1abf97c01999083d4ad097a6743097a4d32e443ff0c37b3022d0ac06 | sha256:17a53f7c1abf97c01999083d4ad097a6743097a4d32e443ff0c37b3022d0ac06 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| moltbot-safe-executor-producer-2.0.0@6b16962d:execution_result:36 | sha256:371e76cd0bb060ca286c3e3ddf8c29d82361ec3308b3cadc88c2e35f9f7d1dd0 | sha256:371e76cd0bb060ca286c3e3ddf8c29d82361ec3308b3cadc88c2e35f9f7d1dd0 | json-sort-keys-compact-utf8-no-nan | computed_during_import |

Source evidence classes and source verification statuses are retained as producer/source assertions. They are not the importer’s independent assurance or verification.

### Complete material trace (escaped JSON)

The following is the complete trace metadata without truncation. Null observations, rejected content, historical states, policy/evaluation metadata and original sources remain distinct. Rejected evidence is not accepted lineage. No retry or current authority is established.

<pre>{
  "transformation_version": "agep-manifest-reconstruction-import/0.3.8-programme2-profiles-candidate",
  "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
  "supported_revisions": {
    "manifest": "ff5490828b2bf7f6a976da209f3f533701855687",
    "replay": "6a6a477495ac24e813f12bb0fe314acfe8bac9cf",
    "control_plane": "2bac7875391cad0a431fa0d75208b7ade39743e3",
    "moltbot_safe": "6b16962db140590b808f02b5c2cb11a217aec46f",
    "odes": "cba83a1c06f718a8afd76178f36e5cc15896347d",
    "gax_imx_experimental_reference": "6bcde026a804c7377f5e39f57ca6dd00b3c3292d",
    "gax_imx_acceptance_status": "provisional_experimental_dependency",
    "alvorada": "fb3d97938969a89e149e8ff8db2756091d1233fc"
  },
  "replay_semantic_validation": {
    "validator": "agent_replay_bundle.importers.import_bounded_workflow",
    "required_revision": "6a6a477495ac24e813f12bb0fe314acfe8bac9cf",
    "status": "validated_complete"
  },
  "replay_import_reports": [
    {
      "adapter_profile": "control-plane-programme2-profiles@2bac7875",
      "source_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "complete": true,
      "field_mappings": {
        "decisions": "records[runtime_decision]",
        "attempts": "records[control_plane_attempt_transition]",
        "observations": "records[effect_observation]",
        "reconciliations": "records[reconciliation]",
        "refusals": "records[effect_time_refusal]",
        "resolution_checks": "records[resolution_check]",
        "closeouts": "records[attempt_closeout]",
        "input_time_floors": "records[input_time_floors]",
        "check_events": "records[resolution_check_event]",
        "vocabulary_changes": "records[reason_vocabulary_change]"
      },
      "findings": [
        {
          "code": "M003",
          "category": "conversion_warning",
          "severity": "info",
          "path": "moltbot.execution_envelope.operation.institution_id",
          "message": "Institution/domain provenance is the trusted Moltbot integration context, not Control Plane AuthorizationBinding.",
          "value_state": null
        },
        {
          "code": "M004",
          "category": "conversion_warning",
          "severity": "info",
          "path": "moltbot.execution_envelope.operation.authority_context_id",
          "message": "At the pinned adapter this field carries the proposal profile reference; it is distinct from the Control Plane binding context-instance ID.",
          "value_state": null
        }
      ]
    }
  ],
  "replay_semantics": {
    "record_reconstruction": true,
    "policy_reevaluation": false,
    "model_reexecution": false,
    "external_effect_execution": false,
    "destination_observation": "producer_reported",
    "independent_effect_verification": false,
    "notes": "Replay reconstructs recorded events only; import never renews permission or creates an effect."
  },
  "input_artifacts": [
    {
      "artifact_role": "manifest",
      "artifact_id": "refund-integration-pilot-v1",
      "version": "1.1",
      "hash": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
      "trusted_revision": "ff5490828b2bf7f6a976da209f3f533701855687",
      "verification_status": "digest_and_cross_artifact_binding_checked_when_runtime_proposal_present",
      "commitment_source": "locally_computed",
      "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan"
    },
    {
      "artifact_role": "reconstruction_bundle",
      "artifact_id": "09f74557-30dd-416e-801a-fc77b23b97cb",
      "version": "0.2.0",
      "hash": "sha256:5d29d0f22df99dd84bf505cd97fcc959b3ca5af73e53c65e50748b69202c9f6f",
      "trusted_revision": "6a6a477495ac24e813f12bb0fe314acfe8bac9cf",
      "verification_status": "validated_complete",
      "commitment_source": "locally_computed",
      "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan"
    }
  ],
  "producer_profiles": [
    {
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "producer": "Cognous Agent Control Plane",
      "repository": "cogno-us/cognous-agent-control-plane",
      "revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "format_version": null,
      "revision_check": "declared_revision_matches_accepted_pin",
      "provenance_status": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "format_name": "BoundedRunRecord",
      "schema_ref": null,
      "notes": "No embedded format version; adapter is revision-pinned."
    },
    {
      "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@6b16962d",
      "producer": "Moltbot Safe",
      "repository": "cogno-us/moltbot-safe",
      "revision": "6b16962db140590b808f02b5c2cb11a217aec46f",
      "format_version": "2.0.0",
      "revision_check": "declared_revision_matches_accepted_pin",
      "provenance_status": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "format_name": "Executor producer export",
      "schema_ref": null,
      "notes": "Versioned producer profile; repository provenance remains source-asserted unless separately established."
    }
  ],
  "executor_producer_contract": {
    "profile_id": "moltbot-safe-executor-producer-2.0.0@6b16962d",
    "control_plane_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
    "compatible_control_plane_revisions": [
      "2bac7875391cad0a431fa0d75208b7ade39743e3"
    ],
    "repository_revision": "6b16962db140590b808f02b5c2cb11a217aec46f",
    "interface_profile_id": "urn:cognous:profiles:moltbot-safe-executor-producer",
    "interface_profile_version": "2.0.0",
    "provenance": {
      "mode": "versioned_profile",
      "source_asserted": {
        "repository_revision": "6b16962db140590b808f02b5c2cb11a217aec46f",
        "producer_profile_id": "urn:cognous:profiles:moltbot-safe-executor-producer",
        "producer_profile_version": "2.0.0"
      },
      "independently_established": []
    },
    "legacy": false
  },
  "source_record_refs": [
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:runtime_proposal:0",
      "record_type": "runtime_proposal",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "proposal",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [
        {
          "label": "payload_commitment",
          "value": "sha256:6b782ebbcc034edeca4069b31aa4d8cbc9d3eeaf3b2034ab989bb430de962c0e",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "verification_status": "checked_match",
          "source_path": "proposal.payload_commitment",
          "notes": null
        }
      ],
      "source_content_commitment": "sha256:6b782ebbcc034edeca4069b31aa4d8cbc9d3eeaf3b2034ab989bb430de962c0e",
      "source_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "source_commitment_verification_status": "checked_match",
      "local_content_commitment": "sha256:1afd891df02fda64ffd73bbaaf9eb2ba7ce3b0863c9d71598ab90602d6fa52f2",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:1afd891df02fda64ffd73bbaaf9eb2ba7ce3b0863c9d71598ab90602d6fa52f2"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:runtime_decision:1",
      "record_type": "runtime_decision",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "decisions[0]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [
        {
          "label": "effect_id",
          "value": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "verification_status": "checked_match",
          "source_path": "decisions[0].effect_id",
          "notes": "Checked under pinned Control Plane effect-id contract."
        },
        {
          "label": "proposal_commitment",
          "value": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "verification_status": "attributed_claim",
          "source_path": "decisions[0].binding.proposal_commitment",
          "notes": null
        },
        {
          "label": "manifest_digest",
          "value": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "verification_status": "attributed_claim",
          "source_path": "decisions[0].binding.manifest_digest",
          "notes": null
        },
        {
          "label": "payload_commitment",
          "value": "sha256:6b782ebbcc034edeca4069b31aa4d8cbc9d3eeaf3b2034ab989bb430de962c0e",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "verification_status": "attributed_claim",
          "source_path": "decisions[0].binding.payload_commitment",
          "notes": null
        },
        {
          "label": "requirement_commitment",
          "value": "sha256:6590406e701b51e637c87953860d1ceb72d8da0af87311048f152e0ee2b8ccb6",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "verification_status": "attributed_claim",
          "source_path": "decisions[0].binding.requirement_commitment",
          "notes": null
        },
        {
          "label": "role_mapping_digest",
          "value": "sha256:f8a8db156df7087ddf34be1ed77fc86fa20ba7668deb87a9b3a5bd0a6ace496d",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "verification_status": "attributed_claim",
          "source_path": "decisions[0].binding.role_mapping_digest",
          "notes": null
        }
      ],
      "source_content_commitment": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
      "source_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "source_commitment_verification_status": "checked_match",
      "local_content_commitment": "sha256:a31643345102cbeb19d034efadfeff1a10725af6e0423e12a75c24f56622ca03",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:a31643345102cbeb19d034efadfeff1a10725af6e0423e12a75c24f56622ca03"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:effect_time_refusal:2",
      "record_type": "effect_time_refusal",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "refusals[0]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:e23611378e80c4a08078bd12a8ce414c09d8563b4f6bdf2c1466938f2f8861b0",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:e23611378e80c4a08078bd12a8ce414c09d8563b4f6bdf2c1466938f2f8861b0"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check:3",
      "record_type": "resolution_check",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "resolution_checks[0]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:e3cc5e3fe2783b1ad8e53a962c01df7379122aff8823961cb227d7689221983a",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:e3cc5e3fe2783b1ad8e53a962c01df7379122aff8823961cb227d7689221983a"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check:4",
      "record_type": "resolution_check",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "resolution_checks[1]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:095066fdde514b4c9fdec1ba37ac83b5d05c2d5b12c699f1f68122cfbcc13e85",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:095066fdde514b4c9fdec1ba37ac83b5d05c2d5b12c699f1f68122cfbcc13e85"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:input_time_floors:5",
      "record_type": "input_time_floors",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "input_time_floors",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:5bb5dad4cee13b6759a24d21e8188907c3e660c5b24b3209791cec62ea796d3d",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:5bb5dad4cee13b6759a24d21e8188907c3e660c5b24b3209791cec62ea796d3d"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:6",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[0]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:54d708ff1f56d0c5eb1d6e09f1516b79c8f013ce42af8717f9ce506e7bc59d8d",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:54d708ff1f56d0c5eb1d6e09f1516b79c8f013ce42af8717f9ce506e7bc59d8d"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:7",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[1]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:bc5023f4571a2b36dfa2d9a5521686a69c0b6f92b344fe717a699a043f8f14eb",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:bc5023f4571a2b36dfa2d9a5521686a69c0b6f92b344fe717a699a043f8f14eb"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:8",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[2]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:a89e5a0c1e35defe5f4c9dc081b21ef540b2cecb29294058c74629ed24e92aaa",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:a89e5a0c1e35defe5f4c9dc081b21ef540b2cecb29294058c74629ed24e92aaa"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:9",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[3]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:dafc1ea21477e6e9c00e9ceb673eaab1d16b2f6d7429d83c3a6b0b1862f6e6bd",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:dafc1ea21477e6e9c00e9ceb673eaab1d16b2f6d7429d83c3a6b0b1862f6e6bd"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:10",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[4]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:31d5c485efa797c1108a28b14f24532814188c264865f952ad6c5d2f85a4fd0e",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:31d5c485efa797c1108a28b14f24532814188c264865f952ad6c5d2f85a4fd0e"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:11",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[5]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:691476bb9e6c29660a6c508131fb51c1660e8f553ad1f4cda29dd150b7e32e33",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:691476bb9e6c29660a6c508131fb51c1660e8f553ad1f4cda29dd150b7e32e33"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:12",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[6]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:20f89c9c501c46334e5c076df100708ef94365790af6d1520be422e9aa411311",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:20f89c9c501c46334e5c076df100708ef94365790af6d1520be422e9aa411311"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:13",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[7]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:2407f49ec8b7ed7c8d2d57a1bb9d7499dbc8b73561d4a2cd63fa743a006033a4",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:2407f49ec8b7ed7c8d2d57a1bb9d7499dbc8b73561d4a2cd63fa743a006033a4"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:14",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[8]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:f480c14a15fff1b04ebc7d1ee47e670547a544aa6b449439e6bd78d594350572",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:f480c14a15fff1b04ebc7d1ee47e670547a544aa6b449439e6bd78d594350572"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:15",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[9]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:e0d6e409f084b4e98393b1916b7b58c8fc0052937988652ee63841260882f62a",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:e0d6e409f084b4e98393b1916b7b58c8fc0052937988652ee63841260882f62a"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:16",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[10]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:45188949f064a2b56aa6d6937e79674cdbb1f9439c550404e07837e9f6281f03",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:45188949f064a2b56aa6d6937e79674cdbb1f9439c550404e07837e9f6281f03"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:17",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[11]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:31e6fda981695637e8f53b42cf81f504ad55a9d5cf9673502b8d838d59cbc26f",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:31e6fda981695637e8f53b42cf81f504ad55a9d5cf9673502b8d838d59cbc26f"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:18",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[12]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:430e7f3ff67fa018acb6bb78c2bd64467ea70c45e2dba5d6db6d025d24926358",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:430e7f3ff67fa018acb6bb78c2bd64467ea70c45e2dba5d6db6d025d24926358"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:19",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[13]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:ddba867cb7c5f1e07dc4a317c4e002169b0d6d7174af5e223bef91e8731947ce",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:ddba867cb7c5f1e07dc4a317c4e002169b0d6d7174af5e223bef91e8731947ce"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:20",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[14]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:9b9c28fc62cfe4affca60ee987b24debadb4de4331b8cb0ec9f6800f9adab917",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:9b9c28fc62cfe4affca60ee987b24debadb4de4331b8cb0ec9f6800f9adab917"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:21",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[15]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:db0ee14d96bb66899d7d4d3c60ce1db43edc7fd1c80055bd3d67f61533bcee59",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:db0ee14d96bb66899d7d4d3c60ce1db43edc7fd1c80055bd3d67f61533bcee59"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:22",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[16]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:31be8a3fbaac1adddeeac4be797882bdaf1091ec2894196e998ef30c7fd454d8",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:31be8a3fbaac1adddeeac4be797882bdaf1091ec2894196e998ef30c7fd454d8"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:23",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[17]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:3de22de6150b83966d4261784e57d6082b6679c4c2c1081dee4788db20b05783",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:3de22de6150b83966d4261784e57d6082b6679c4c2c1081dee4788db20b05783"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:24",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[18]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:dc2060ed680e2f2a2bc01eba03516fe944210d85f54af7513fe0657ee40cb676",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:dc2060ed680e2f2a2bc01eba03516fe944210d85f54af7513fe0657ee40cb676"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:25",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[19]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:e886346e925753f1773e01da1eb67a1a45d60fcd0bdb2241c37452cd6d054e7f",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:e886346e925753f1773e01da1eb67a1a45d60fcd0bdb2241c37452cd6d054e7f"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:26",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[20]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:9927fe30675644db82780432b649365149ef9ed93eb74a34a21da155238f742c",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:9927fe30675644db82780432b649365149ef9ed93eb74a34a21da155238f742c"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:27",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[21]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:655857f355a33f793714944c04c58a25846a2369dea39d7cd3b0285e4a8775c0",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:655857f355a33f793714944c04c58a25846a2369dea39d7cd3b0285e4a8775c0"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:28",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[22]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:082f9f66d24bcdda426a963089e9c6a3957d37572328fb25e2cfc71a4582fa94",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:082f9f66d24bcdda426a963089e9c6a3957d37572328fb25e2cfc71a4582fa94"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:29",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[23]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:6de35016d46305c9955fcd4aac1a5f0d873140dd922c1c860ab24f046bb40149",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:6de35016d46305c9955fcd4aac1a5f0d873140dd922c1c860ab24f046bb40149"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:30",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[24]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:588db970b764266fd72dac9dab14121b79e1f8885a32c2feea6dd1ee14791eda",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:588db970b764266fd72dac9dab14121b79e1f8885a32c2feea6dd1ee14791eda"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:31",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[25]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:97e6ca2896b37fdd73e534377a009f4e06a175f95e2f4ee63404b63115fa9abc",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:97e6ca2896b37fdd73e534377a009f4e06a175f95e2f4ee63404b63115fa9abc"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:32",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[26]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:08d4182f9a69643b8d30d333aac4019b62bdecaf10c18f7d77997fdb95c5e19e",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:08d4182f9a69643b8d30d333aac4019b62bdecaf10c18f7d77997fdb95c5e19e"
    },
    {
      "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:33",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
      "source_path": "check_events[27]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:0f796835c36b2ef38e595ec8df0dc9e0317f261fc091b5b70069d6429934c359",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:0f796835c36b2ef38e595ec8df0dc9e0317f261fc091b5b70069d6429934c359"
    },
    {
      "record_id": "moltbot-safe-executor-producer-2.0.0@6b16962d:execution_envelope:34",
      "record_type": "execution_envelope",
      "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@6b16962d",
      "source_path": "moltbot.execution_envelope",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/moltbot-safe",
      "producer_revision": "6b16962db140590b808f02b5c2cb11a217aec46f",
      "producer_format_version": "2.0.0",
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [
        {
          "label": "payload_commitment",
          "value": "sha256:6b782ebbcc034edeca4069b31aa4d8cbc9d3eeaf3b2034ab989bb430de962c0e",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "verification_status": "checked_match",
          "source_path": "moltbot.execution_envelope.operation.payload_commitment",
          "notes": null
        }
      ],
      "source_content_commitment": "sha256:6b782ebbcc034edeca4069b31aa4d8cbc9d3eeaf3b2034ab989bb430de962c0e",
      "source_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "source_commitment_verification_status": "checked_match",
      "local_content_commitment": "sha256:aec272751a6bbecb1d0066758eac85696f3e81c0b55193a48cfb11385c5bafd3",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:aec272751a6bbecb1d0066758eac85696f3e81c0b55193a48cfb11385c5bafd3"
    },
    {
      "record_id": "moltbot-safe-executor-producer-2.0.0@6b16962d:executor_control_plane_evidence:35",
      "record_type": "executor_control_plane_evidence",
      "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@6b16962d",
      "source_path": "moltbot.control_plane_evidence",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/moltbot-safe",
      "producer_revision": "6b16962db140590b808f02b5c2cb11a217aec46f",
      "producer_format_version": "2.0.0",
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:17a53f7c1abf97c01999083d4ad097a6743097a4d32e443ff0c37b3022d0ac06",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:17a53f7c1abf97c01999083d4ad097a6743097a4d32e443ff0c37b3022d0ac06"
    },
    {
      "record_id": "moltbot-safe-executor-producer-2.0.0@6b16962d:execution_result:36",
      "record_type": "execution_result",
      "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@6b16962d",
      "source_path": "moltbot.execution_result",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/moltbot-safe",
      "producer_revision": "6b16962db140590b808f02b5c2cb11a217aec46f",
      "producer_format_version": "2.0.0",
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:371e76cd0bb060ca286c3e3ddf8c29d82361ec3308b3cadc88c2e35f9f7d1dd0",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:371e76cd0bb060ca286c3e3ddf8c29d82361ec3308b3cadc88c2e35f9f7d1dd0"
    }
  ],
  "conversion_losses": [
    {
      "source": "replay_import_report",
      "report_index": 0,
      "finding_index": 0,
      "adapter_profile": "control-plane-programme2-profiles@2bac7875",
      "code": "M003",
      "category": "conversion_warning",
      "severity": "info",
      "path": "moltbot.execution_envelope.operation.institution_id",
      "value_state": null,
      "message": "Institution/domain provenance is the trusted Moltbot integration context, not Control Plane AuthorizationBinding."
    },
    {
      "source": "replay_import_report",
      "report_index": 0,
      "finding_index": 1,
      "adapter_profile": "control-plane-programme2-profiles@2bac7875",
      "code": "M004",
      "category": "conversion_warning",
      "severity": "info",
      "path": "moltbot.execution_envelope.operation.authority_context_id",
      "value_state": null,
      "message": "At the pinned adapter this field carries the proposal profile reference; it is distinct from the Control Plane binding context-instance ID."
    }
  ],
  "derived_counts": {
    "proposal_count": 1,
    "decision_count": 1,
    "distinct_effect_count": 1,
    "control_plane_attempt_count": 0,
    "executor_attempt_count": 0,
    "attempt_transition_record_count": 0,
    "destination_effect_count": 0,
    "effect_observation_count": 0,
    "reconciliation_count": 0,
    "destination_observation_counts": {},
    "destination_effect_state_counts": {},
    "effect_observation_state_counts": {},
    "reconciliation_state_counts": {},
    "execution_result_state_counts": {
      "denied": 1
    },
    "acknowledgement_counts": {
      "execution_result_unknown": 1
    },
    "acknowledgement_sources": [
      {
        "record_id": "moltbot-safe-executor-producer-2.0.0@6b16962d:execution_result:36",
        "source": "execution_result",
        "state": "unknown",
        "status": "denied",
        "attempt_id": null
      }
    ],
    "coverage_denominators": {
      "effect_denominator": "distinct authorized effect_id values",
      "control_plane_attempt_denominator": "unique Control Plane attempt IDs",
      "executor_attempt_denominator": "unique destination_attempt IDs",
      "destination_effect_denominator": "destination_effect records",
      "effect_observation_denominator": "effect_observation records",
      "reconciliation_denominator": "reconciliation records",
      "missing_observation": "unavailable, not zero/success/failure",
      "destination_observation_denominator": "accepted Control Plane effect_observation records only; destination rows and reconciliations counted separately"
    },
    "counting_rules": [
      "Repeated lifecycle records do not inflate attempt counts.",
      "Duplicate submissions do not inflate distinct effect counts when effect_id is unchanged.",
      "Control Plane and executor attempt IDs are separate namespaces unless explicit correlation exists.",
      "Destination effects, effect observations and reconciliations are counted separately.",
      "Missing observations are unavailable, not success or failure.",
      "Latest supported state uses Replay producer sequence and exact effect lineage; earlier rejection remains visible. Independent clocks do not establish ordering."
    ],
    "authorization_granted_count": 1,
    "authorization_held_count": 0,
    "authorization_denied_count": 0
  },
  "lifecycle_summary": {
    "authorization": "authorized",
    "current_permission": "not_evaluated_from_historical_records",
    "execution_attempted": "no",
    "acknowledgement": "not_applicable",
    "acknowledgement_sources": [
      {
        "record_id": "moltbot-safe-executor-producer-2.0.0@6b16962d:execution_result:36",
        "source": "execution_result",
        "state": "unknown",
        "status": "denied",
        "attempt_id": null
      }
    ],
    "control_plane_transition_statuses": {},
    "destination_observed": "unknown",
    "independent_verification": "unavailable",
    "notes": [
      "Historical authorization is retained evidence and does not establish current permission.",
      "Control Plane transition status is preserved separately from acknowledgement receipt.",
      "Executor acknowledgement is distinct from independently verified delivery.",
      "A lost or unknown acknowledgement followed by an applied observation retains both facts.",
      "Observed local destination state does not establish independently verified institutional outcome.",
      "Reconstruction completeness does not mean effect completion.",
      "HMAC/shared-secret integrity is not public issuer identity or independent review.",
      "A software-generated pack cannot create human approval."
    ],
    "reconstruction_status": "reconstruction_complete",
    "effect_observation_history": {
      "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829": {
        "basis": "Control Plane reconciliation array order, filtered by exact effect_id",
        "rejected_reconciliation_indices": [],
        "latest_reconciliation": null,
        "latest_accepted_observation": null,
        "latest_supported_destination_state": "unknown",
        "retry_eligible": null,
        "acknowledgement_history": [],
        "cross_sequence_order": "not_established",
        "freshness_at_import": "not_evaluated"
      }
    },
    "destination_observation_scope": "latest supplied Control Plane reconciliation per exact effect; not a fresh query",
    "retry_permission": "not_established",
    "historical_local_observation": false
  },
  "control_evidence_levels": {
    "semantic_validation_performed_during_import": {
      "status": "validated_complete",
      "evidence": [
        "metadata.traceable_import.replay_semantic_validation"
      ],
      "meaning": "the importer executed the accepted Replay semantic validator; this is not a test-run or runtime-control-effectiveness claim"
    },
    "source_asserted_runtime_evidence": {
      "status": "unavailable",
      "evidence": [],
      "scope": "unavailable",
      "meaning": "no source runtime or fixture provenance was supplied"
    },
    "attributable_test_run_evidence": {
      "status": "unavailable",
      "evidence": [],
      "scope": "unavailable",
      "meaning": "no complete attributable test-run provenance was supplied"
    },
    "declared": {
      "status": "present",
      "evidence": [
        "manifest"
      ],
      "meaning": "control or requirement is declared only"
    },
    "implemented": {
      "status": "not_established_by_import",
      "evidence": [],
      "meaning": "implementation requires producer-specific evidence; manifest declarations and import success do not suffice"
    },
    "tested": {
      "status": "unavailable",
      "evidence": [],
      "scope": "unavailable",
      "meaning": "semantic import validation and source runtime records do not by themselves establish that a test occurred"
    },
    "tested_in_this_repository": {
      "status": "not_evaluated_during_import",
      "evidence": [],
      "meaning": "this import does not execute or imply execution of the Evidence Pack repository test suite"
    },
    "operationally_observed": {
      "status": "unavailable",
      "evidence": [],
      "meaning": "no production operational observation supplied"
    },
    "independently_audited": {
      "status": "unavailable",
      "evidence": [],
      "meaning": "no independent audit or certification supplied"
    }
  },
  "redaction_state": {
    "redacted": false,
    "source": "unverified_source_claim",
    "derivation": null
  },
  "import_findings": [
    {
      "code": "REPLAY_M003",
      "severity": "info",
      "path": "moltbot.execution_envelope.operation.institution_id",
      "message": "Institution/domain provenance is the trusted Moltbot integration context, not Control Plane AuthorizationBinding.",
      "category": "conversion_warning",
      "value_state": null
    },
    {
      "code": "REPLAY_M004",
      "severity": "info",
      "path": "moltbot.execution_envelope.operation.authority_context_id",
      "message": "At the pinned adapter this field carries the proposal profile reference; it is distinct from the Control Plane binding context-instance ID.",
      "category": "conversion_warning",
      "value_state": null
    },
    {
      "code": "REPLAY_SEMANTIC_LIMITATION",
      "severity": "info",
      "path": "semantics.notes",
      "message": "Replay reconstructs recorded events only; import never renews permission or creates an effect."
    },
    {
      "code": "R_REDACTION_UNVERIFIED",
      "severity": "warning",
      "message": "Source declarations do not verify removal of sensitive content; export safety is unverified."
    }
  ],
  "manual_assessments": [],
  "unresolved_issues": [
    {
      "code": "U_INDEPENDENT_VERIFICATION_UNAVAILABLE",
      "severity": "warning",
      "message": "Destination observation is producer-retained unless independent verifier evidence is supplied."
    },
    {
      "code": "U_OPERATIONAL_EFFECTIVENESS_NOT_MEASURED",
      "severity": "warning",
      "message": "Synthetic import success cannot support operational effectiveness or deployment approval."
    },
    {
      "code": "U_HISTORICAL_AUTHORIZATION_NOT_CURRENT_PERMISSION",
      "severity": "info",
      "message": "Retained authorization is historical evidence only; current permission must be re-evaluated by the runtime authority/control boundary."
    },
    {
      "code": "U_EXCHANGE_METADATA_SUPPLEMENTARY",
      "severity": "info",
      "message": "Accepted GAX/IMX exchange metadata remains supplementary unless represented by a supported Replay mapping; the Evidence Pack does not invent exchange fields."
    }
  ],
  "outcomes_and_burden": {
    "unresolved_delivery": "see lifecycle_summary.destination_observed",
    "incidents": "unavailable_not_zero",
    "remedies": "unavailable",
    "measured_latency": "not_measured",
    "human_review_effort": "not_measured",
    "error_prevention": "not_measured",
    "error_correction": "not_measured",
    "comparison_baseline_reference": "unavailable"
  },
  "supported_revision_sets": {
    "manifest": [
      "ff5490828b2bf7f6a976da209f3f533701855687"
    ],
    "replay": [
      "6a6a477495ac24e813f12bb0fe314acfe8bac9cf"
    ],
    "control_plane": [
      "2bac7875391cad0a431fa0d75208b7ade39743e3"
    ],
    "moltbot_safe": [
      "6b16962db140590b808f02b5c2cb11a217aec46f"
    ]
  },
  "selected_revisions": {
    "manifest": "ff5490828b2bf7f6a976da209f3f533701855687",
    "replay": "6a6a477495ac24e813f12bb0fe314acfe8bac9cf",
    "control_plane": "2bac7875391cad0a431fa0d75208b7ade39743e3",
    "moltbot_safe": "6b16962db140590b808f02b5c2cb11a217aec46f"
  },
  "executor_failure_reference_verification": "source_asserted_not_independently_verified",
  "retained_sources": {
    "manifest": {
      "manifest_version": "1.1",
      "manifest_id": "refund-integration-pilot-v1",
      "agent_name": "Synthetic Refund Agent",
      "agent_description": "Synthetic bounded integration fixture; not deployed and not an institutional grant.",
      "owner": "cognous-integration-pilot",
      "environment": "synthetic",
      "default_action": "escalate",
      "tools": [
        {
          "tool_name": "refund_adapter",
          "adapter_id": "urn:cognous:adapter:synthetic-refund-v1",
          "description": "Synthetic refund destination adapter.",
          "allowed": true,
          "external_system": "synthetic-refund-ledger",
          "data_classification": "synthetic"
        }
      ],
      "actions": [
        {
          "action_name": "refund_issue_routine",
          "action_id": "urn:cognous:action:refund-issue-routine-v1",
          "tool_name": "refund_adapter",
          "action_type": "write",
          "description": "Issue one bounded routine synthetic refund.",
          "default_action": "escalate",
          "authority_required": [
            {
              "scope": "refund.issue.routine",
              "description": "Declaration only; downstream resolver must establish a current institutional grant.",
              "required": true,
              "source": "alvorada-authority-context-0.1.0"
            }
          ],
          "review_requirement": {
            "mode": "human_review",
            "reviewer_role": "customer-service-supervisor",
            "reason": "Synthetic routine case retains human review for the integration pilot."
          },
          "reliance_requirement": {
            "required": true,
            "allowed_source_types": [
              "database",
              "user_input"
            ],
            "description": "Record entitlement and customer request evidence."
          },
          "payload_policy": {
            "required_fields": [
              "customer_id",
              "refund_reason"
            ],
            "optional_fields": [],
            "sensitive_fields": [
              "customer_id"
            ],
            "forbidden_fields": []
          },
          "target_policy": {
            "allowed_targets": [
              "urn:cognous:synthetic-account:customer-001"
            ],
            "allow_any_target": false
          },
          "effect_limits": {
            "max_amount": 100.0,
            "unit": "USD",
            "max_effects": 1
          },
          "authority_context": {
            "schema_version": "0.1.0",
            "profile_ref": "urn:cognous:alvorada:public-stack-profile:0.1.0",
            "requirement_id": "urn:cognous:authority-requirement:refund-routine-v1",
            "institution_id": "urn:cognous:institution:synthetic-customer-service",
            "authority_domain": "customer-refunds",
            "consequence_tier": "T1",
            "evidence_obligation_ids": [
              "urn:cognous:evidence:refund-entitlement"
            ]
          },
          "redaction_hints": [
            {
              "field_path": "customer_id",
              "reason": "Synthetic identifier is treated as sensitive in exported evidence.",
              "replacement": "[REDACTED]"
            }
          ],
          "tags": [
            "synthetic",
            "refund",
            "routine"
          ],
          "metadata": {}
        },
        {
          "action_name": "refund_issue_high_consequence",
          "action_id": "urn:cognous:action:refund-issue-high-v1",
          "tool_name": "refund_adapter",
          "action_type": "write",
          "description": "Issue one higher-consequence synthetic refund requiring explicit approval downstream.",
          "default_action": "escalate",
          "authority_required": [
            {
              "scope": "refund.issue.high",
              "description": "Declaration only; downstream resolver must establish a current institutional grant.",
              "required": true,
              "source": "alvorada-authority-context-0.1.0"
            }
          ],
          "review_requirement": {
            "mode": "approval_required",
            "reviewer_role": "refund-authorizer",
            "reason": "Higher-consequence synthetic case requires explicit approval."
          },
          "reliance_requirement": {
            "required": true,
            "allowed_source_types": [
              "database",
              "user_input"
            ],
            "description": "Record entitlement, amount basis and approval evidence."
          },
          "payload_policy": {
            "required_fields": [
              "customer_id",
              "refund_reason",
              "case_reference"
            ],
            "optional_fields": [],
            "sensitive_fields": [
              "customer_id"
            ],
            "forbidden_fields": []
          },
          "target_policy": {
            "allowed_targets": [
              "urn:cognous:synthetic-account:customer-002"
            ],
            "allow_any_target": false
          },
          "effect_limits": {
            "max_amount": 1000.0,
            "unit": "USD",
            "max_effects": 1
          },
          "authority_context": {
            "schema_version": "0.1.0",
            "profile_ref": "urn:cognous:alvorada:public-stack-profile:0.1.0",
            "requirement_id": "urn:cognous:authority-requirement:refund-high-v1",
            "institution_id": "urn:cognous:institution:synthetic-customer-service",
            "authority_domain": "customer-refunds",
            "consequence_tier": "T2",
            "evidence_obligation_ids": [
              "urn:cognous:evidence:refund-entitlement",
              "urn:cognous:evidence:refund-approval"
            ]
          },
          "redaction_hints": [
            {
              "field_path": "customer_id",
              "reason": "Synthetic identifier is treated as sensitive in exported evidence.",
              "replacement": "[REDACTED]"
            }
          ],
          "tags": [
            "synthetic",
            "refund",
            "higher-consequence"
          ],
          "metadata": {}
        }
      ],
      "metadata": {
        "upstream_alvorada_commit": "fb3d97938969a89e149e8ff8db2756091d1233fc",
        "authority_context_version": "0.1.0",
        "deployment_status": "not_deployed"
      }
    },
    "reconstruction_bundle": {
      "bundle_id": "09f74557-30dd-416e-801a-fc77b23b97cb",
      "bundle_version": "0.2.0",
      "run_id": "run-1",
      "status": "reconstruction_complete",
      "generated_at": "2026-10-20T00:42:32.919178+00:00",
      "producer_profiles": [
        {
          "profile_id": "control-plane-programme2-profiles@2bac7875",
          "producer": "Cognous Agent Control Plane",
          "repository": "cogno-us/cognous-agent-control-plane",
          "revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
          "format_name": "BoundedRunRecord",
          "format_version": null,
          "schema_ref": null,
          "notes": "No embedded format version; adapter is revision-pinned."
        },
        {
          "profile_id": "moltbot-safe-executor-producer-2.0.0@6b16962d",
          "producer": "Moltbot Safe",
          "repository": "cogno-us/moltbot-safe",
          "revision": "6b16962db140590b808f02b5c2cb11a217aec46f",
          "format_name": "Executor producer export",
          "format_version": "2.0.0",
          "schema_ref": null,
          "notes": "Versioned producer profile; repository provenance remains source-asserted unless separately established."
        }
      ],
      "records": [
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:runtime_proposal:0",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "runtime_proposal",
          "source_sequence": 0,
          "source_path": "proposal",
          "recorded_at": null,
          "identifiers": {
            "run_id": "run-1",
            "correlation_id": "case-1",
            "action_id": "urn:cognous:action:refund-issue-routine-v1",
            "manifest_id": "refund-integration-pilot-v1",
            "authority_context_profile_ref": "urn:cognous:alvorada:public-stack-profile:0.1.0",
            "requirement_id": "urn:cognous:authority-requirement:refund-routine-v1"
          },
          "evidence_class": "producer_reported",
          "data": {
            "manifest_id": "refund-integration-pilot-v1",
            "manifest_version": "1.1",
            "manifest_digest": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
            "actor": "urn:cognous:identity:refund-agent-1",
            "principal": "urn:cognous:principal:refund-service",
            "action_id": "urn:cognous:action:refund-issue-routine-v1",
            "adapter_id": "urn:cognous:adapter:synthetic-refund-v1",
            "target": "urn:cognous:synthetic-account:customer-001",
            "payload": {
              "customer_id": "customer-001",
              "refund_reason": "duplicate"
            },
            "payload_commitment": "sha256:6b782ebbcc034edeca4069b31aa4d8cbc9d3eeaf3b2034ab989bb430de962c0e",
            "requested_permissions": [
              "refund.issue.routine"
            ],
            "amount": 50.0,
            "unit": "USD",
            "effects": 1,
            "authority_context_ref": "urn:cognous:alvorada:public-stack-profile:0.1.0",
            "requirement_id": "urn:cognous:authority-requirement:refund-routine-v1",
            "risk_metadata": {},
            "not_before": null,
            "expires_at": null,
            "correlation_id": "case-1",
            "run_id": "run-1",
            "expected_side_effects": [],
            "evidence_refs": [
              "urn:cognous:evidence:refund-entitlement"
            ]
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:runtime_decision:1",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "runtime_decision",
          "source_sequence": 1,
          "source_path": "decisions[0]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "manifest_id": "refund-integration-pilot-v1",
            "action_id": "urn:cognous:action:refund-issue-routine-v1",
            "grant_id": "urn:cognous:grant:routine-1",
            "grant_revision": "1",
            "authority_context_instance_id": "urn:cognous:authority-context:pilot-1",
            "requirement_id": "urn:cognous:authority-requirement:refund-routine-v1"
          },
          "evidence_class": "producer_reported",
          "data": {
            "reason_vocabulary_version": "runtime-authority-reasons/0.1",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "result": "authorized",
            "reasons": [],
            "decided_at": "2026-10-05T19:00:00+00:00",
            "time_source": "test_override",
            "operation_horizon": {
              "source": "runtime_proposal",
              "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
              "not_before": null,
              "expires_at": null
            },
            "binding": {
              "runtime_authority": {
                "profile": "runtime-authority/0.1",
                "approval_commitment": "sha256:ebd9bfb69fb2894a63291d67fbc9fe07f58eb2f320f48286f7b6a003d2adfe86",
                "required_inputs_digest": "sha256:1c4ef694ed72bdf927f6ad39982e981634c16ad2f303b8a718b078de2aaaffaf",
                "catalogue_digest": "sha256:b39642c9ecdaf334a778fcda63576997843e5c8765758d8f6248e3e54555ed6a",
                "expected_effective_grant_digest": "sha256:4b43b997e7a5dc9b70f51ffa8917eaeb79f7df04f108f81a90e0997de3602b31",
                "effective_grant_derivation_version": "effective-grant/0.1"
              },
              "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
              "manifest_id": "refund-integration-pilot-v1",
              "manifest_version": "1.1",
              "manifest_digest": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
              "actor": "urn:cognous:identity:refund-agent-1",
              "principal": "urn:cognous:principal:refund-service",
              "action_id": "urn:cognous:action:refund-issue-routine-v1",
              "adapter_id": "urn:cognous:adapter:synthetic-refund-v1",
              "target": "urn:cognous:synthetic-account:customer-001",
              "payload_commitment": "sha256:6b782ebbcc034edeca4069b31aa4d8cbc9d3eeaf3b2034ab989bb430de962c0e",
              "requested_permissions": [
                "refund.issue.routine"
              ],
              "amount": 50.0,
              "unit": "USD",
              "effects": 1,
              "authority_context_id": "urn:cognous:authority-context:pilot-1",
              "authority_context_version": "0.1.0",
              "authority_context_status": "proposed_pending_governor_review",
              "requirement_id": "urn:cognous:authority-requirement:refund-routine-v1",
              "requirement_commitment": "sha256:6590406e701b51e637c87953860d1ceb72d8da0af87311048f152e0ee2b8ccb6",
              "grant_id": "urn:cognous:grant:routine-1",
              "grant_revision": "1",
              "policy_versions": [
                {
                  "ref": "urn:cognous:policy:refund-policy",
                  "version": "1.0"
                }
              ],
              "role_mapping_version": "roles-v1",
              "role_mapping_digest": "sha256:f8a8db156df7087ddf34be1ed77fc86fa20ba7668deb87a9b3a5bd0a6ace496d",
              "effective_max_effects": 1
            },
            "resolution_inputs": [
              {
                "input_type": "manifest",
                "input_id": "refund-integration-pilot-v1",
                "expected": {},
                "observed": {},
                "record_commitment": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "authority_context",
                "input_id": "urn:cognous:alvorada:public-stack-profile:0.1.0",
                "expected": {},
                "observed": {
                  "schema_version": "0.1.0",
                  "interface_status": "proposed_pending_governor_review"
                },
                "record_commitment": "sha256:b0727efe67e8d7c656d48a20129dea61621acf99cda8371c67ab550d4caca342",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "role_mapping",
                "input_id": "urn:cognous:institution:synthetic-customer-service",
                "expected": {},
                "observed": {
                  "version": "roles-v1",
                  "digest": "sha256:f8a8db156df7087ddf34be1ed77fc86fa20ba7668deb87a9b3a5bd0a6ace496d"
                },
                "record_commitment": "sha256:fc884333b0da586ae781c0c4289729465659c719c0e4602758ddbf7a2bdcb89e",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "identity",
                "input_id": "urn:cognous:identity:refund-agent-1",
                "expected": {},
                "observed": {
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:5eee426c0827b2b01acc16f0acf3bd13fcfc315ad851c406822dc3242a0b18d3",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "mandate",
                "input_id": "urn:cognous:issuance:1",
                "expected": {},
                "observed": {
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:d023eb722343620d7b2d4e622e0283008d72c903ef81c15d9b3dbaada7648091",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "grant",
                "input_id": "urn:cognous:grant:routine-1",
                "expected": {
                  "revision": "1",
                  "status": "active"
                },
                "observed": {
                  "revision": "1",
                  "status": "active",
                  "version": "status-v1",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:eded76117318d91618259e7ed8eced201b868bb5f714d49fbf751535a6b8a859",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "conflict",
                "input_id": "urn:cognous:authority-requirement:refund-routine-v1",
                "expected": {},
                "observed": {
                  "state": "clear",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:b469c2e823a75ebd9ba5b0f315c1a092e9ef8d257e684f03a9c00765a065e2ec",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "policy",
                "input_id": "urn:cognous:policy:refund-policy",
                "expected": {
                  "version": "1.0",
                  "status": "active"
                },
                "observed": {
                  "status": "active",
                  "version": "1.0",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:ff1302d24b132d1ccb1345ca47ecd25be2200335621ca133e01f54c384007e30",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "approval",
                "input_id": "urn:cognous:approval:t1-1",
                "expected": {
                  "grant_revision": "1",
                  "status": "active",
                  "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                  "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                  "grant_id": "urn:cognous:grant:routine-1"
                },
                "observed": {
                  "status": "active",
                  "observed_at": "2026-10-05T19:00:00+00:00",
                  "grant_revision": "1",
                  "runtime_authority_commitment": "sha256:ebd9bfb69fb2894a63291d67fbc9fe07f58eb2f320f48286f7b6a003d2adfe86",
                  "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                  "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                  "grant_id": "urn:cognous:grant:routine-1"
                },
                "record_commitment": "sha256:373729df30fd57ccf14073ac25b970c15d0303da8e39ae39474d67e72542dbad",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "evidence",
                "input_id": "urn:cognous:evidence:refund-entitlement",
                "expected": {
                  "state": "current"
                },
                "observed": {
                  "state": "current",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:41ac78e62c85e85b6ba4dd94a60a430c4cdb94cbcf1a51a42a3850b61def1d4f",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "evidence",
                "input_id": "urn:cognous:evidence:optional-context",
                "expected": {},
                "observed": {
                  "state": "unknown",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:9918ca9a4e1da9eee69322d6c0b107f215773957e569ee85e5ca1abb94c267cd",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "purpose",
                "input_id": "sha256:6408c3a34b12a6f20f3bb978552aa9412812d9e366d53a8a27bc9ea7ea28da9b",
                "expected": {},
                "observed": {
                  "state": "open",
                  "observed_at": "2026-10-05T19:00:00+00:00",
                  "epoch": "epoch-1",
                  "epoch_capability": "authoritative"
                },
                "record_commitment": "sha256:52c634d9df00e6477998ba35e96be5316ab560a689439610bc4a01c15467a8f6",
                "missing": false,
                "previous_observed_at": null
              }
            ]
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:effect_time_refusal:2",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "effect_time_refusal",
          "source_sequence": 2,
          "source_path": "refusals[0]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "refusal_id": "614005f1-545a-4b5c-b1f3-43241683e304"
          },
          "evidence_class": "producer_reported",
          "data": {
            "reason_vocabulary_version": "runtime-authority-reasons/0.1",
            "refusal_id": "614005f1-545a-4b5c-b1f3-43241683e304",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "time_source": "test_override",
            "original_operation_horizon": {
              "source": "runtime_proposal",
              "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
              "not_before": null,
              "expires_at": null
            },
            "operation_horizon": {
              "source": "runtime_proposal",
              "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
              "not_before": null,
              "expires_at": null
            },
            "stage": "effect_time_revalidation",
            "reasons": [
              "purpose_closed"
            ],
            "changed_inputs": [],
            "resolution_inputs": [
              {
                "input_type": "manifest",
                "input_id": "refund-integration-pilot-v1",
                "expected": {},
                "observed": {},
                "record_commitment": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "authority_context",
                "input_id": "urn:cognous:alvorada:public-stack-profile:0.1.0",
                "expected": {},
                "observed": {
                  "schema_version": "0.1.0",
                  "interface_status": "proposed_pending_governor_review"
                },
                "record_commitment": "sha256:b0727efe67e8d7c656d48a20129dea61621acf99cda8371c67ab550d4caca342",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "role_mapping",
                "input_id": "urn:cognous:institution:synthetic-customer-service",
                "expected": {},
                "observed": {
                  "version": "roles-v1",
                  "digest": "sha256:f8a8db156df7087ddf34be1ed77fc86fa20ba7668deb87a9b3a5bd0a6ace496d"
                },
                "record_commitment": "sha256:fc884333b0da586ae781c0c4289729465659c719c0e4602758ddbf7a2bdcb89e",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "identity",
                "input_id": "urn:cognous:identity:refund-agent-1",
                "expected": {},
                "observed": {
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:5eee426c0827b2b01acc16f0acf3bd13fcfc315ad851c406822dc3242a0b18d3",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              },
              {
                "input_type": "mandate",
                "input_id": "urn:cognous:issuance:1",
                "expected": {},
                "observed": {
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:d023eb722343620d7b2d4e622e0283008d72c903ef81c15d9b3dbaada7648091",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              },
              {
                "input_type": "grant",
                "input_id": "urn:cognous:grant:routine-1",
                "expected": {
                  "revision": "1",
                  "status": "active"
                },
                "observed": {
                  "revision": "1",
                  "status": "active",
                  "version": "status-v1",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:eded76117318d91618259e7ed8eced201b868bb5f714d49fbf751535a6b8a859",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              },
              {
                "input_type": "conflict",
                "input_id": "urn:cognous:authority-requirement:refund-routine-v1",
                "expected": {},
                "observed": {
                  "state": "clear",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:b469c2e823a75ebd9ba5b0f315c1a092e9ef8d257e684f03a9c00765a065e2ec",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              },
              {
                "input_type": "policy",
                "input_id": "urn:cognous:policy:refund-policy",
                "expected": {
                  "version": "1.0",
                  "status": "active"
                },
                "observed": {
                  "status": "active",
                  "version": "1.0",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:ff1302d24b132d1ccb1345ca47ecd25be2200335621ca133e01f54c384007e30",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              },
              {
                "input_type": "approval",
                "input_id": "urn:cognous:approval:t1-1",
                "expected": {
                  "grant_revision": "1",
                  "status": "active",
                  "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                  "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                  "grant_id": "urn:cognous:grant:routine-1"
                },
                "observed": {
                  "status": "active",
                  "observed_at": "2026-10-05T19:00:00+00:00",
                  "grant_revision": "1",
                  "runtime_authority_commitment": "sha256:ebd9bfb69fb2894a63291d67fbc9fe07f58eb2f320f48286f7b6a003d2adfe86",
                  "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                  "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                  "grant_id": "urn:cognous:grant:routine-1"
                },
                "record_commitment": "sha256:373729df30fd57ccf14073ac25b970c15d0303da8e39ae39474d67e72542dbad",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              },
              {
                "input_type": "evidence",
                "input_id": "urn:cognous:evidence:refund-entitlement",
                "expected": {
                  "state": "current"
                },
                "observed": {
                  "state": "current",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:41ac78e62c85e85b6ba4dd94a60a430c4cdb94cbcf1a51a42a3850b61def1d4f",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              },
              {
                "input_type": "evidence",
                "input_id": "urn:cognous:evidence:optional-context",
                "expected": {},
                "observed": {
                  "state": "unknown",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:9918ca9a4e1da9eee69322d6c0b107f215773957e569ee85e5ca1abb94c267cd",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              },
              {
                "input_type": "purpose",
                "input_id": "sha256:6408c3a34b12a6f20f3bb978552aa9412812d9e366d53a8a27bc9ea7ea28da9b",
                "expected": {},
                "observed": {
                  "state": "closed",
                  "observed_at": "2026-10-05T19:00:00+00:00",
                  "epoch": "epoch-1",
                  "epoch_capability": "authoritative"
                },
                "record_commitment": "sha256:0bddd392557c3bcacb9075e1559633c7cd0fd9011349a00105b842c04fbf0f8d",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              }
            ]
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check:3",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check",
          "source_sequence": 3,
          "source_path": "resolution_checks[0]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "73f13d48-dd8b-4be6-b05e-a4d3b47f01ac"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "73f13d48-dd8b-4be6-b05e-a4d3b47f01ac",
            "stage": "decision",
            "evaluated_at": "2026-10-05T19:00:00+00:00",
            "time_source": "test_override",
            "inputs": [
              {
                "input_type": "manifest",
                "input_id": "refund-integration-pilot-v1",
                "expected": {},
                "observed": {},
                "record_commitment": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "authority_context",
                "input_id": "urn:cognous:alvorada:public-stack-profile:0.1.0",
                "expected": {},
                "observed": {
                  "schema_version": "0.1.0",
                  "interface_status": "proposed_pending_governor_review"
                },
                "record_commitment": "sha256:b0727efe67e8d7c656d48a20129dea61621acf99cda8371c67ab550d4caca342",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "role_mapping",
                "input_id": "urn:cognous:institution:synthetic-customer-service",
                "expected": {},
                "observed": {
                  "version": "roles-v1",
                  "digest": "sha256:f8a8db156df7087ddf34be1ed77fc86fa20ba7668deb87a9b3a5bd0a6ace496d"
                },
                "record_commitment": "sha256:fc884333b0da586ae781c0c4289729465659c719c0e4602758ddbf7a2bdcb89e",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "identity",
                "input_id": "urn:cognous:identity:refund-agent-1",
                "expected": {},
                "observed": {
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:5eee426c0827b2b01acc16f0acf3bd13fcfc315ad851c406822dc3242a0b18d3",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "mandate",
                "input_id": "urn:cognous:issuance:1",
                "expected": {},
                "observed": {
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:d023eb722343620d7b2d4e622e0283008d72c903ef81c15d9b3dbaada7648091",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "grant",
                "input_id": "urn:cognous:grant:routine-1",
                "expected": {
                  "revision": "1",
                  "status": "active"
                },
                "observed": {
                  "revision": "1",
                  "status": "active",
                  "version": "status-v1",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:eded76117318d91618259e7ed8eced201b868bb5f714d49fbf751535a6b8a859",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "conflict",
                "input_id": "urn:cognous:authority-requirement:refund-routine-v1",
                "expected": {},
                "observed": {
                  "state": "clear",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:b469c2e823a75ebd9ba5b0f315c1a092e9ef8d257e684f03a9c00765a065e2ec",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "policy",
                "input_id": "urn:cognous:policy:refund-policy",
                "expected": {
                  "version": "1.0",
                  "status": "active"
                },
                "observed": {
                  "status": "active",
                  "version": "1.0",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:ff1302d24b132d1ccb1345ca47ecd25be2200335621ca133e01f54c384007e30",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "approval",
                "input_id": "urn:cognous:approval:t1-1",
                "expected": {
                  "grant_revision": "1",
                  "status": "active",
                  "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                  "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                  "grant_id": "urn:cognous:grant:routine-1"
                },
                "observed": {
                  "status": "active",
                  "observed_at": "2026-10-05T19:00:00+00:00",
                  "grant_revision": "1",
                  "runtime_authority_commitment": "sha256:ebd9bfb69fb2894a63291d67fbc9fe07f58eb2f320f48286f7b6a003d2adfe86",
                  "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                  "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                  "grant_id": "urn:cognous:grant:routine-1"
                },
                "record_commitment": "sha256:373729df30fd57ccf14073ac25b970c15d0303da8e39ae39474d67e72542dbad",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "evidence",
                "input_id": "urn:cognous:evidence:refund-entitlement",
                "expected": {
                  "state": "current"
                },
                "observed": {
                  "state": "current",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:41ac78e62c85e85b6ba4dd94a60a430c4cdb94cbcf1a51a42a3850b61def1d4f",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "evidence",
                "input_id": "urn:cognous:evidence:optional-context",
                "expected": {},
                "observed": {
                  "state": "unknown",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:9918ca9a4e1da9eee69322d6c0b107f215773957e569ee85e5ca1abb94c267cd",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "purpose",
                "input_id": "sha256:6408c3a34b12a6f20f3bb978552aa9412812d9e366d53a8a27bc9ea7ea28da9b",
                "expected": {},
                "observed": {
                  "state": "open",
                  "observed_at": "2026-10-05T19:00:00+00:00",
                  "epoch": "epoch-1",
                  "epoch_capability": "authoritative"
                },
                "record_commitment": "sha256:52c634d9df00e6477998ba35e96be5316ab560a689439610bc4a01c15467a8f6",
                "missing": false,
                "previous_observed_at": null
              }
            ],
            "reasons": []
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check:4",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check",
          "source_sequence": 4,
          "source_path": "resolution_checks[1]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "dc7a7987-6167-4081-a897-1925400b54db"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "dc7a7987-6167-4081-a897-1925400b54db",
            "stage": "effect",
            "evaluated_at": "2026-10-05T19:00:00+00:00",
            "time_source": "test_override",
            "inputs": [
              {
                "input_type": "manifest",
                "input_id": "refund-integration-pilot-v1",
                "expected": {},
                "observed": {},
                "record_commitment": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "authority_context",
                "input_id": "urn:cognous:alvorada:public-stack-profile:0.1.0",
                "expected": {},
                "observed": {
                  "schema_version": "0.1.0",
                  "interface_status": "proposed_pending_governor_review"
                },
                "record_commitment": "sha256:b0727efe67e8d7c656d48a20129dea61621acf99cda8371c67ab550d4caca342",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "role_mapping",
                "input_id": "urn:cognous:institution:synthetic-customer-service",
                "expected": {},
                "observed": {
                  "version": "roles-v1",
                  "digest": "sha256:f8a8db156df7087ddf34be1ed77fc86fa20ba7668deb87a9b3a5bd0a6ace496d"
                },
                "record_commitment": "sha256:fc884333b0da586ae781c0c4289729465659c719c0e4602758ddbf7a2bdcb89e",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "identity",
                "input_id": "urn:cognous:identity:refund-agent-1",
                "expected": {},
                "observed": {
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:5eee426c0827b2b01acc16f0acf3bd13fcfc315ad851c406822dc3242a0b18d3",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              },
              {
                "input_type": "mandate",
                "input_id": "urn:cognous:issuance:1",
                "expected": {},
                "observed": {
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:d023eb722343620d7b2d4e622e0283008d72c903ef81c15d9b3dbaada7648091",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              },
              {
                "input_type": "grant",
                "input_id": "urn:cognous:grant:routine-1",
                "expected": {
                  "revision": "1",
                  "status": "active"
                },
                "observed": {
                  "revision": "1",
                  "status": "active",
                  "version": "status-v1",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:eded76117318d91618259e7ed8eced201b868bb5f714d49fbf751535a6b8a859",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              },
              {
                "input_type": "conflict",
                "input_id": "urn:cognous:authority-requirement:refund-routine-v1",
                "expected": {},
                "observed": {
                  "state": "clear",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:b469c2e823a75ebd9ba5b0f315c1a092e9ef8d257e684f03a9c00765a065e2ec",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              },
              {
                "input_type": "policy",
                "input_id": "urn:cognous:policy:refund-policy",
                "expected": {
                  "version": "1.0",
                  "status": "active"
                },
                "observed": {
                  "status": "active",
                  "version": "1.0",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:ff1302d24b132d1ccb1345ca47ecd25be2200335621ca133e01f54c384007e30",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              },
              {
                "input_type": "approval",
                "input_id": "urn:cognous:approval:t1-1",
                "expected": {
                  "grant_revision": "1",
                  "status": "active",
                  "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                  "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                  "grant_id": "urn:cognous:grant:routine-1"
                },
                "observed": {
                  "status": "active",
                  "observed_at": "2026-10-05T19:00:00+00:00",
                  "grant_revision": "1",
                  "runtime_authority_commitment": "sha256:ebd9bfb69fb2894a63291d67fbc9fe07f58eb2f320f48286f7b6a003d2adfe86",
                  "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                  "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                  "grant_id": "urn:cognous:grant:routine-1"
                },
                "record_commitment": "sha256:373729df30fd57ccf14073ac25b970c15d0303da8e39ae39474d67e72542dbad",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              },
              {
                "input_type": "evidence",
                "input_id": "urn:cognous:evidence:refund-entitlement",
                "expected": {
                  "state": "current"
                },
                "observed": {
                  "state": "current",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:41ac78e62c85e85b6ba4dd94a60a430c4cdb94cbcf1a51a42a3850b61def1d4f",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              },
              {
                "input_type": "evidence",
                "input_id": "urn:cognous:evidence:optional-context",
                "expected": {},
                "observed": {
                  "state": "unknown",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:9918ca9a4e1da9eee69322d6c0b107f215773957e569ee85e5ca1abb94c267cd",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              },
              {
                "input_type": "purpose",
                "input_id": "sha256:6408c3a34b12a6f20f3bb978552aa9412812d9e366d53a8a27bc9ea7ea28da9b",
                "expected": {},
                "observed": {
                  "state": "closed",
                  "observed_at": "2026-10-05T19:00:00+00:00",
                  "epoch": "epoch-1",
                  "epoch_capability": "authoritative"
                },
                "record_commitment": "sha256:0bddd392557c3bcacb9075e1559633c7cd0fd9011349a00105b842c04fbf0f8d",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              }
            ],
            "reasons": [
              "purpose_closed"
            ]
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:input_time_floors:5",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "input_time_floors",
          "source_sequence": 5,
          "source_path": "input_time_floors",
          "recorded_at": null,
          "identifiers": {
            "run_id": "run-1"
          },
          "evidence_class": "producer_reported",
          "data": {
            "sha256:7052a5b98597102f45a2c4ab494a5e1006ff104c4b86e5222e2b59f330c30418": "2026-10-05T19:00:00+00:00",
            "sha256:4d8e3965e23d0c43249d12bd33f98502d07aa9b8675d4e94deeef9194b96eccc": "2026-10-05T19:00:00+00:00",
            "sha256:bb70894893d767f392df7aea0070fff70716cb6b934ea3664ba852518b781eda": "2026-10-05T19:00:00+00:00",
            "sha256:759e6cc704cb5cda55ed8925b417f92ff0f83b8d81ed7959ddc439d3d01ba75b": "2026-10-05T19:00:00+00:00",
            "sha256:e25ac65c4ed37739a2ab3e879dc2435ddb4df8687db4c6665e8cff3a835513cc": "2026-10-05T19:00:00+00:00",
            "sha256:7357f30a03d77811d73178b90d4e8c7d343cc0879fa341d529623ef70db9b793": "2026-10-05T19:00:00+00:00",
            "sha256:74437776fe13ee871e8efddb996b26b2deb270f19bb09854f8f09d6b76b80b5c": "2026-10-05T19:00:00+00:00",
            "sha256:6e2ad318158316fbe204f27531f5d59e0588a8e1338eb41b36917b88b7067de6": "2026-10-05T19:00:00+00:00",
            "sha256:84ef6acdaeaba04146c274ef7764315de0eb79f6449d00779611a0cfa0ef3af4": "2026-10-05T19:00:00+00:00"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:6",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 6,
          "source_path": "check_events[0]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
            "phase": "opened",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": null,
            "effect_id": null,
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": null,
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:7",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 7,
          "source_path": "check_events[1]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": null,
            "effect_id": null,
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": {
              "input_type": "manifest",
              "input_id": "refund-integration-pilot-v1",
              "expected": {},
              "observed": {},
              "record_commitment": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:8",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 8,
          "source_path": "check_events[2]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": null,
            "effect_id": null,
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": {
              "input_type": "authority_context",
              "input_id": "urn:cognous:alvorada:public-stack-profile:0.1.0",
              "expected": {},
              "observed": {
                "schema_version": "0.1.0",
                "interface_status": "proposed_pending_governor_review"
              },
              "record_commitment": "sha256:b0727efe67e8d7c656d48a20129dea61621acf99cda8371c67ab550d4caca342",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:9",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 9,
          "source_path": "check_events[3]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": null,
            "effect_id": null,
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": {
              "input_type": "role_mapping",
              "input_id": "urn:cognous:institution:synthetic-customer-service",
              "expected": {},
              "observed": {
                "version": "roles-v1",
                "digest": "sha256:f8a8db156df7087ddf34be1ed77fc86fa20ba7668deb87a9b3a5bd0a6ace496d"
              },
              "record_commitment": "sha256:fc884333b0da586ae781c0c4289729465659c719c0e4602758ddbf7a2bdcb89e",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:10",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 10,
          "source_path": "check_events[4]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": null,
            "effect_id": null,
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": {
              "input_type": "identity",
              "input_id": "urn:cognous:identity:refund-agent-1",
              "expected": {},
              "observed": {
                "observed_at": "2026-10-05T19:00:00+00:00"
              },
              "record_commitment": "sha256:5eee426c0827b2b01acc16f0acf3bd13fcfc315ad851c406822dc3242a0b18d3",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:11",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 11,
          "source_path": "check_events[5]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": null,
            "effect_id": null,
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": {
              "input_type": "mandate",
              "input_id": "urn:cognous:issuance:1",
              "expected": {},
              "observed": {
                "observed_at": "2026-10-05T19:00:00+00:00"
              },
              "record_commitment": "sha256:d023eb722343620d7b2d4e622e0283008d72c903ef81c15d9b3dbaada7648091",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:12",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 12,
          "source_path": "check_events[6]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": null,
            "effect_id": null,
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": {
              "input_type": "grant",
              "input_id": "urn:cognous:grant:routine-1",
              "expected": {
                "revision": "1",
                "status": "active"
              },
              "observed": {
                "revision": "1",
                "status": "active",
                "version": "status-v1",
                "observed_at": "2026-10-05T19:00:00+00:00"
              },
              "record_commitment": "sha256:eded76117318d91618259e7ed8eced201b868bb5f714d49fbf751535a6b8a859",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:13",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 13,
          "source_path": "check_events[7]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": null,
            "effect_id": null,
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": {
              "input_type": "conflict",
              "input_id": "urn:cognous:authority-requirement:refund-routine-v1",
              "expected": {},
              "observed": {
                "state": "clear",
                "observed_at": "2026-10-05T19:00:00+00:00"
              },
              "record_commitment": "sha256:b469c2e823a75ebd9ba5b0f315c1a092e9ef8d257e684f03a9c00765a065e2ec",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:14",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 14,
          "source_path": "check_events[8]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": null,
            "effect_id": null,
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": {
              "input_type": "policy",
              "input_id": "urn:cognous:policy:refund-policy",
              "expected": {
                "version": "1.0",
                "status": "active"
              },
              "observed": {
                "status": "active",
                "version": "1.0",
                "observed_at": "2026-10-05T19:00:00+00:00"
              },
              "record_commitment": "sha256:ff1302d24b132d1ccb1345ca47ecd25be2200335621ca133e01f54c384007e30",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:15",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 15,
          "source_path": "check_events[9]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": null,
            "effect_id": null,
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": {
              "input_type": "approval",
              "input_id": "urn:cognous:approval:t1-1",
              "expected": {
                "grant_revision": "1",
                "status": "active",
                "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                "grant_id": "urn:cognous:grant:routine-1"
              },
              "observed": {
                "status": "active",
                "observed_at": "2026-10-05T19:00:00+00:00",
                "grant_revision": "1",
                "runtime_authority_commitment": "sha256:ebd9bfb69fb2894a63291d67fbc9fe07f58eb2f320f48286f7b6a003d2adfe86",
                "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                "grant_id": "urn:cognous:grant:routine-1"
              },
              "record_commitment": "sha256:373729df30fd57ccf14073ac25b970c15d0303da8e39ae39474d67e72542dbad",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:16",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 16,
          "source_path": "check_events[10]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": null,
            "effect_id": null,
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": {
              "input_type": "evidence",
              "input_id": "urn:cognous:evidence:refund-entitlement",
              "expected": {
                "state": "current"
              },
              "observed": {
                "state": "current",
                "observed_at": "2026-10-05T19:00:00+00:00"
              },
              "record_commitment": "sha256:41ac78e62c85e85b6ba4dd94a60a430c4cdb94cbcf1a51a42a3850b61def1d4f",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:17",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 17,
          "source_path": "check_events[11]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": null,
            "effect_id": null,
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": {
              "input_type": "evidence",
              "input_id": "urn:cognous:evidence:optional-context",
              "expected": {},
              "observed": {
                "state": "unknown",
                "observed_at": "2026-10-05T19:00:00+00:00"
              },
              "record_commitment": "sha256:9918ca9a4e1da9eee69322d6c0b107f215773957e569ee85e5ca1abb94c267cd",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:18",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 18,
          "source_path": "check_events[12]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": null,
            "effect_id": null,
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": {
              "input_type": "purpose",
              "input_id": "sha256:6408c3a34b12a6f20f3bb978552aa9412812d9e366d53a8a27bc9ea7ea28da9b",
              "expected": {},
              "observed": {
                "state": "open",
                "observed_at": "2026-10-05T19:00:00+00:00",
                "epoch": "epoch-1",
                "epoch_capability": "authoritative"
              },
              "record_commitment": "sha256:52c634d9df00e6477998ba35e96be5316ab560a689439610bc4a01c15467a8f6",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:19",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 19,
          "source_path": "check_events[13]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
            "phase": "completed",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": null,
            "effect_id": null,
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": null,
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:20",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 20,
          "source_path": "check_events[14]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
            "phase": "opened",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": null,
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:21",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 21,
          "source_path": "check_events[15]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": {
              "input_type": "manifest",
              "input_id": "refund-integration-pilot-v1",
              "expected": {},
              "observed": {},
              "record_commitment": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:22",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 22,
          "source_path": "check_events[16]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": {
              "input_type": "authority_context",
              "input_id": "urn:cognous:alvorada:public-stack-profile:0.1.0",
              "expected": {},
              "observed": {
                "schema_version": "0.1.0",
                "interface_status": "proposed_pending_governor_review"
              },
              "record_commitment": "sha256:b0727efe67e8d7c656d48a20129dea61621acf99cda8371c67ab550d4caca342",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:23",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 23,
          "source_path": "check_events[17]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": {
              "input_type": "role_mapping",
              "input_id": "urn:cognous:institution:synthetic-customer-service",
              "expected": {},
              "observed": {
                "version": "roles-v1",
                "digest": "sha256:f8a8db156df7087ddf34be1ed77fc86fa20ba7668deb87a9b3a5bd0a6ace496d"
              },
              "record_commitment": "sha256:fc884333b0da586ae781c0c4289729465659c719c0e4602758ddbf7a2bdcb89e",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:24",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 24,
          "source_path": "check_events[18]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": {
              "input_type": "identity",
              "input_id": "urn:cognous:identity:refund-agent-1",
              "expected": {},
              "observed": {
                "observed_at": "2026-10-05T19:00:00+00:00"
              },
              "record_commitment": "sha256:5eee426c0827b2b01acc16f0acf3bd13fcfc315ad851c406822dc3242a0b18d3",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:25",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 25,
          "source_path": "check_events[19]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": {
              "input_type": "mandate",
              "input_id": "urn:cognous:issuance:1",
              "expected": {},
              "observed": {
                "observed_at": "2026-10-05T19:00:00+00:00"
              },
              "record_commitment": "sha256:d023eb722343620d7b2d4e622e0283008d72c903ef81c15d9b3dbaada7648091",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:26",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 26,
          "source_path": "check_events[20]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": {
              "input_type": "grant",
              "input_id": "urn:cognous:grant:routine-1",
              "expected": {
                "revision": "1",
                "status": "active"
              },
              "observed": {
                "revision": "1",
                "status": "active",
                "version": "status-v1",
                "observed_at": "2026-10-05T19:00:00+00:00"
              },
              "record_commitment": "sha256:eded76117318d91618259e7ed8eced201b868bb5f714d49fbf751535a6b8a859",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:27",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 27,
          "source_path": "check_events[21]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": {
              "input_type": "conflict",
              "input_id": "urn:cognous:authority-requirement:refund-routine-v1",
              "expected": {},
              "observed": {
                "state": "clear",
                "observed_at": "2026-10-05T19:00:00+00:00"
              },
              "record_commitment": "sha256:b469c2e823a75ebd9ba5b0f315c1a092e9ef8d257e684f03a9c00765a065e2ec",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:28",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 28,
          "source_path": "check_events[22]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": {
              "input_type": "policy",
              "input_id": "urn:cognous:policy:refund-policy",
              "expected": {
                "version": "1.0",
                "status": "active"
              },
              "observed": {
                "status": "active",
                "version": "1.0",
                "observed_at": "2026-10-05T19:00:00+00:00"
              },
              "record_commitment": "sha256:ff1302d24b132d1ccb1345ca47ecd25be2200335621ca133e01f54c384007e30",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:29",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 29,
          "source_path": "check_events[23]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": {
              "input_type": "approval",
              "input_id": "urn:cognous:approval:t1-1",
              "expected": {
                "grant_revision": "1",
                "status": "active",
                "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                "grant_id": "urn:cognous:grant:routine-1"
              },
              "observed": {
                "status": "active",
                "observed_at": "2026-10-05T19:00:00+00:00",
                "grant_revision": "1",
                "runtime_authority_commitment": "sha256:ebd9bfb69fb2894a63291d67fbc9fe07f58eb2f320f48286f7b6a003d2adfe86",
                "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                "grant_id": "urn:cognous:grant:routine-1"
              },
              "record_commitment": "sha256:373729df30fd57ccf14073ac25b970c15d0303da8e39ae39474d67e72542dbad",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:30",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 30,
          "source_path": "check_events[24]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": {
              "input_type": "evidence",
              "input_id": "urn:cognous:evidence:refund-entitlement",
              "expected": {
                "state": "current"
              },
              "observed": {
                "state": "current",
                "observed_at": "2026-10-05T19:00:00+00:00"
              },
              "record_commitment": "sha256:41ac78e62c85e85b6ba4dd94a60a430c4cdb94cbcf1a51a42a3850b61def1d4f",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:31",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 31,
          "source_path": "check_events[25]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": {
              "input_type": "evidence",
              "input_id": "urn:cognous:evidence:optional-context",
              "expected": {},
              "observed": {
                "state": "unknown",
                "observed_at": "2026-10-05T19:00:00+00:00"
              },
              "record_commitment": "sha256:9918ca9a4e1da9eee69322d6c0b107f215773957e569ee85e5ca1abb94c267cd",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:32",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 32,
          "source_path": "check_events[26]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": {
              "input_type": "purpose",
              "input_id": "sha256:6408c3a34b12a6f20f3bb978552aa9412812d9e366d53a8a27bc9ea7ea28da9b",
              "expected": {},
              "observed": {
                "state": "closed",
                "observed_at": "2026-10-05T19:00:00+00:00",
                "epoch": "epoch-1",
                "epoch_capability": "authoritative"
              },
              "record_commitment": "sha256:0bddd392557c3bcacb9075e1559633c7cd0fd9011349a00105b842c04fbf0f8d",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-programme2-profiles@2bac7875:resolution_check_event:33",
          "producer_profile_id": "control-plane-programme2-profiles@2bac7875",
          "record_type": "resolution_check_event",
          "source_sequence": 33,
          "source_path": "check_events[27]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
            "phase": "completed",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "4737",
              "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": null,
            "reasons": [
              "purpose_closed"
            ],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "moltbot-safe-executor-producer-2.0.0@6b16962d:execution_envelope:34",
          "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@6b16962d",
          "record_type": "execution_envelope",
          "source_sequence": 34,
          "source_path": "moltbot.execution_envelope",
          "recorded_at": null,
          "identifiers": {
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "manifest_id": "refund-integration-pilot-v1",
            "action_id": "urn:cognous:action:refund-issue-routine-v1",
            "grant_id": "urn:cognous:grant:routine-1",
            "grant_revision": "1",
            "authority_context_profile_ref": "urn:cognous:alvorada:public-stack-profile:0.1.0",
            "institution_id": "urn:cognous:institution:synthetic-customer-service",
            "authority_domain": "customer-refunds"
          },
          "evidence_class": "producer_reported",
          "data": {
            "version": "0.2.0",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "operation": {
              "actor": "urn:cognous:identity:refund-agent-1",
              "principal": "urn:cognous:principal:refund-service",
              "institution_id": "urn:cognous:institution:synthetic-customer-service",
              "authority_domain": "customer-refunds",
              "manifest_id": "refund-integration-pilot-v1",
              "manifest_version": "1.1",
              "manifest_digest": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
              "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
              "action_id": "urn:cognous:action:refund-issue-routine-v1",
              "adapter_id": "urn:cognous:adapter:synthetic-refund-v1",
              "target": "urn:cognous:synthetic-account:customer-001",
              "payload": {
                "customer_id": "customer-001",
                "refund_reason": "duplicate"
              },
              "payload_commitment": "sha256:6b782ebbcc034edeca4069b31aa4d8cbc9d3eeaf3b2034ab989bb430de962c0e",
              "requested_permissions": [
                "refund.issue.routine"
              ],
              "amount": 50.0,
              "unit": "USD",
              "effects": 1,
              "authority_context_id": "urn:cognous:alvorada:public-stack-profile:0.1.0",
              "requirement_id": "urn:cognous:authority-requirement:refund-routine-v1",
              "grant_id": "urn:cognous:grant:routine-1",
              "grant_revision": "1",
              "effective_max_effects": 1
            },
            "attempt_id": null
          }
        },
        {
          "record_id": "moltbot-safe-executor-producer-2.0.0@6b16962d:executor_control_plane_evidence:35",
          "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@6b16962d",
          "record_type": "executor_control_plane_evidence",
          "source_sequence": 35,
          "source_path": "moltbot.control_plane_evidence",
          "recorded_at": null,
          "identifiers": {},
          "evidence_class": "producer_reported",
          "data": {
            "failure_record_id": "e7036bc4-f794-460a-80f5-b2ed3bde14a8",
            "refusal": {
              "reason_vocabulary_version": "runtime-authority-reasons/0.1",
              "refusal_id": "614005f1-545a-4b5c-b1f3-43241683e304",
              "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
              "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
              "recorded_at": "2026-10-05T19:00:00+00:00",
              "time_source": "test_override",
              "original_operation_horizon": {
                "source": "runtime_proposal",
                "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                "not_before": null,
                "expires_at": null
              },
              "operation_horizon": {
                "source": "runtime_proposal",
                "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                "not_before": null,
                "expires_at": null
              },
              "stage": "effect_time_revalidation",
              "reasons": [
                "purpose_closed"
              ],
              "changed_inputs": [],
              "resolution_inputs": [
                {
                  "input_type": "manifest",
                  "input_id": "refund-integration-pilot-v1",
                  "expected": {},
                  "observed": {},
                  "record_commitment": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
                  "missing": false,
                  "previous_observed_at": null
                },
                {
                  "input_type": "authority_context",
                  "input_id": "urn:cognous:alvorada:public-stack-profile:0.1.0",
                  "expected": {},
                  "observed": {
                    "schema_version": "0.1.0",
                    "interface_status": "proposed_pending_governor_review"
                  },
                  "record_commitment": "sha256:b0727efe67e8d7c656d48a20129dea61621acf99cda8371c67ab550d4caca342",
                  "missing": false,
                  "previous_observed_at": null
                },
                {
                  "input_type": "role_mapping",
                  "input_id": "urn:cognous:institution:synthetic-customer-service",
                  "expected": {},
                  "observed": {
                    "version": "roles-v1",
                    "digest": "sha256:f8a8db156df7087ddf34be1ed77fc86fa20ba7668deb87a9b3a5bd0a6ace496d"
                  },
                  "record_commitment": "sha256:fc884333b0da586ae781c0c4289729465659c719c0e4602758ddbf7a2bdcb89e",
                  "missing": false,
                  "previous_observed_at": null
                },
                {
                  "input_type": "identity",
                  "input_id": "urn:cognous:identity:refund-agent-1",
                  "expected": {},
                  "observed": {
                    "observed_at": "2026-10-05T19:00:00+00:00"
                  },
                  "record_commitment": "sha256:5eee426c0827b2b01acc16f0acf3bd13fcfc315ad851c406822dc3242a0b18d3",
                  "missing": false,
                  "previous_observed_at": "2026-10-05T19:00:00+00:00"
                },
                {
                  "input_type": "mandate",
                  "input_id": "urn:cognous:issuance:1",
                  "expected": {},
                  "observed": {
                    "observed_at": "2026-10-05T19:00:00+00:00"
                  },
                  "record_commitment": "sha256:d023eb722343620d7b2d4e622e0283008d72c903ef81c15d9b3dbaada7648091",
                  "missing": false,
                  "previous_observed_at": "2026-10-05T19:00:00+00:00"
                },
                {
                  "input_type": "grant",
                  "input_id": "urn:cognous:grant:routine-1",
                  "expected": {
                    "revision": "1",
                    "status": "active"
                  },
                  "observed": {
                    "revision": "1",
                    "status": "active",
                    "version": "status-v1",
                    "observed_at": "2026-10-05T19:00:00+00:00"
                  },
                  "record_commitment": "sha256:eded76117318d91618259e7ed8eced201b868bb5f714d49fbf751535a6b8a859",
                  "missing": false,
                  "previous_observed_at": "2026-10-05T19:00:00+00:00"
                },
                {
                  "input_type": "conflict",
                  "input_id": "urn:cognous:authority-requirement:refund-routine-v1",
                  "expected": {},
                  "observed": {
                    "state": "clear",
                    "observed_at": "2026-10-05T19:00:00+00:00"
                  },
                  "record_commitment": "sha256:b469c2e823a75ebd9ba5b0f315c1a092e9ef8d257e684f03a9c00765a065e2ec",
                  "missing": false,
                  "previous_observed_at": "2026-10-05T19:00:00+00:00"
                },
                {
                  "input_type": "policy",
                  "input_id": "urn:cognous:policy:refund-policy",
                  "expected": {
                    "version": "1.0",
                    "status": "active"
                  },
                  "observed": {
                    "status": "active",
                    "version": "1.0",
                    "observed_at": "2026-10-05T19:00:00+00:00"
                  },
                  "record_commitment": "sha256:ff1302d24b132d1ccb1345ca47ecd25be2200335621ca133e01f54c384007e30",
                  "missing": false,
                  "previous_observed_at": "2026-10-05T19:00:00+00:00"
                },
                {
                  "input_type": "approval",
                  "input_id": "urn:cognous:approval:t1-1",
                  "expected": {
                    "grant_revision": "1",
                    "status": "active",
                    "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                    "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                    "grant_id": "urn:cognous:grant:routine-1"
                  },
                  "observed": {
                    "status": "active",
                    "observed_at": "2026-10-05T19:00:00+00:00",
                    "grant_revision": "1",
                    "runtime_authority_commitment": "sha256:ebd9bfb69fb2894a63291d67fbc9fe07f58eb2f320f48286f7b6a003d2adfe86",
                    "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                    "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                    "grant_id": "urn:cognous:grant:routine-1"
                  },
                  "record_commitment": "sha256:373729df30fd57ccf14073ac25b970c15d0303da8e39ae39474d67e72542dbad",
                  "missing": false,
                  "previous_observed_at": "2026-10-05T19:00:00+00:00"
                },
                {
                  "input_type": "evidence",
                  "input_id": "urn:cognous:evidence:refund-entitlement",
                  "expected": {
                    "state": "current"
                  },
                  "observed": {
                    "state": "current",
                    "observed_at": "2026-10-05T19:00:00+00:00"
                  },
                  "record_commitment": "sha256:41ac78e62c85e85b6ba4dd94a60a430c4cdb94cbcf1a51a42a3850b61def1d4f",
                  "missing": false,
                  "previous_observed_at": "2026-10-05T19:00:00+00:00"
                },
                {
                  "input_type": "evidence",
                  "input_id": "urn:cognous:evidence:optional-context",
                  "expected": {},
                  "observed": {
                    "state": "unknown",
                    "observed_at": "2026-10-05T19:00:00+00:00"
                  },
                  "record_commitment": "sha256:9918ca9a4e1da9eee69322d6c0b107f215773957e569ee85e5ca1abb94c267cd",
                  "missing": false,
                  "previous_observed_at": "2026-10-05T19:00:00+00:00"
                },
                {
                  "input_type": "purpose",
                  "input_id": "sha256:6408c3a34b12a6f20f3bb978552aa9412812d9e366d53a8a27bc9ea7ea28da9b",
                  "expected": {},
                  "observed": {
                    "state": "closed",
                    "observed_at": "2026-10-05T19:00:00+00:00",
                    "epoch": "epoch-1",
                    "epoch_capability": "authoritative"
                  },
                  "record_commitment": "sha256:0bddd392557c3bcacb9075e1559633c7cd0fd9011349a00105b842c04fbf0f8d",
                  "missing": false,
                  "previous_observed_at": "2026-10-05T19:00:00+00:00"
                }
              ]
            }
          }
        },
        {
          "record_id": "moltbot-safe-executor-producer-2.0.0@6b16962d:execution_result:36",
          "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@6b16962d",
          "record_type": "execution_result",
          "source_sequence": 36,
          "source_path": "moltbot.execution_result",
          "recorded_at": null,
          "identifiers": {
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829"
          },
          "evidence_class": "producer_reported",
          "data": {
            "status": "denied",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "attempt_id": null,
            "attempted": false,
            "acknowledged": false,
            "observed_state": "unknown",
            "newly_executed": false,
            "observation": null,
            "error": "authorization-critical inputs changed before effect",
            "control_plane_evidence": {
              "failure_record_id": "e7036bc4-f794-460a-80f5-b2ed3bde14a8",
              "refusal": {
                "reason_vocabulary_version": "runtime-authority-reasons/0.1",
                "refusal_id": "614005f1-545a-4b5c-b1f3-43241683e304",
                "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
                "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
                "recorded_at": "2026-10-05T19:00:00+00:00",
                "time_source": "test_override",
                "original_operation_horizon": {
                  "source": "runtime_proposal",
                  "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                  "not_before": null,
                  "expires_at": null
                },
                "operation_horizon": {
                  "source": "runtime_proposal",
                  "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                  "not_before": null,
                  "expires_at": null
                },
                "stage": "effect_time_revalidation",
                "reasons": [
                  "purpose_closed"
                ],
                "changed_inputs": [],
                "resolution_inputs": [
                  {
                    "input_type": "manifest",
                    "input_id": "refund-integration-pilot-v1",
                    "expected": {},
                    "observed": {},
                    "record_commitment": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
                    "missing": false,
                    "previous_observed_at": null
                  },
                  {
                    "input_type": "authority_context",
                    "input_id": "urn:cognous:alvorada:public-stack-profile:0.1.0",
                    "expected": {},
                    "observed": {
                      "schema_version": "0.1.0",
                      "interface_status": "proposed_pending_governor_review"
                    },
                    "record_commitment": "sha256:b0727efe67e8d7c656d48a20129dea61621acf99cda8371c67ab550d4caca342",
                    "missing": false,
                    "previous_observed_at": null
                  },
                  {
                    "input_type": "role_mapping",
                    "input_id": "urn:cognous:institution:synthetic-customer-service",
                    "expected": {},
                    "observed": {
                      "version": "roles-v1",
                      "digest": "sha256:f8a8db156df7087ddf34be1ed77fc86fa20ba7668deb87a9b3a5bd0a6ace496d"
                    },
                    "record_commitment": "sha256:fc884333b0da586ae781c0c4289729465659c719c0e4602758ddbf7a2bdcb89e",
                    "missing": false,
                    "previous_observed_at": null
                  },
                  {
                    "input_type": "identity",
                    "input_id": "urn:cognous:identity:refund-agent-1",
                    "expected": {},
                    "observed": {
                      "observed_at": "2026-10-05T19:00:00+00:00"
                    },
                    "record_commitment": "sha256:5eee426c0827b2b01acc16f0acf3bd13fcfc315ad851c406822dc3242a0b18d3",
                    "missing": false,
                    "previous_observed_at": "2026-10-05T19:00:00+00:00"
                  },
                  {
                    "input_type": "mandate",
                    "input_id": "urn:cognous:issuance:1",
                    "expected": {},
                    "observed": {
                      "observed_at": "2026-10-05T19:00:00+00:00"
                    },
                    "record_commitment": "sha256:d023eb722343620d7b2d4e622e0283008d72c903ef81c15d9b3dbaada7648091",
                    "missing": false,
                    "previous_observed_at": "2026-10-05T19:00:00+00:00"
                  },
                  {
                    "input_type": "grant",
                    "input_id": "urn:cognous:grant:routine-1",
                    "expected": {
                      "revision": "1",
                      "status": "active"
                    },
                    "observed": {
                      "revision": "1",
                      "status": "active",
                      "version": "status-v1",
                      "observed_at": "2026-10-05T19:00:00+00:00"
                    },
                    "record_commitment": "sha256:eded76117318d91618259e7ed8eced201b868bb5f714d49fbf751535a6b8a859",
                    "missing": false,
                    "previous_observed_at": "2026-10-05T19:00:00+00:00"
                  },
                  {
                    "input_type": "conflict",
                    "input_id": "urn:cognous:authority-requirement:refund-routine-v1",
                    "expected": {},
                    "observed": {
                      "state": "clear",
                      "observed_at": "2026-10-05T19:00:00+00:00"
                    },
                    "record_commitment": "sha256:b469c2e823a75ebd9ba5b0f315c1a092e9ef8d257e684f03a9c00765a065e2ec",
                    "missing": false,
                    "previous_observed_at": "2026-10-05T19:00:00+00:00"
                  },
                  {
                    "input_type": "policy",
                    "input_id": "urn:cognous:policy:refund-policy",
                    "expected": {
                      "version": "1.0",
                      "status": "active"
                    },
                    "observed": {
                      "status": "active",
                      "version": "1.0",
                      "observed_at": "2026-10-05T19:00:00+00:00"
                    },
                    "record_commitment": "sha256:ff1302d24b132d1ccb1345ca47ecd25be2200335621ca133e01f54c384007e30",
                    "missing": false,
                    "previous_observed_at": "2026-10-05T19:00:00+00:00"
                  },
                  {
                    "input_type": "approval",
                    "input_id": "urn:cognous:approval:t1-1",
                    "expected": {
                      "grant_revision": "1",
                      "status": "active",
                      "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                      "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                      "grant_id": "urn:cognous:grant:routine-1"
                    },
                    "observed": {
                      "status": "active",
                      "observed_at": "2026-10-05T19:00:00+00:00",
                      "grant_revision": "1",
                      "runtime_authority_commitment": "sha256:ebd9bfb69fb2894a63291d67fbc9fe07f58eb2f320f48286f7b6a003d2adfe86",
                      "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                      "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                      "grant_id": "urn:cognous:grant:routine-1"
                    },
                    "record_commitment": "sha256:373729df30fd57ccf14073ac25b970c15d0303da8e39ae39474d67e72542dbad",
                    "missing": false,
                    "previous_observed_at": "2026-10-05T19:00:00+00:00"
                  },
                  {
                    "input_type": "evidence",
                    "input_id": "urn:cognous:evidence:refund-entitlement",
                    "expected": {
                      "state": "current"
                    },
                    "observed": {
                      "state": "current",
                      "observed_at": "2026-10-05T19:00:00+00:00"
                    },
                    "record_commitment": "sha256:41ac78e62c85e85b6ba4dd94a60a430c4cdb94cbcf1a51a42a3850b61def1d4f",
                    "missing": false,
                    "previous_observed_at": "2026-10-05T19:00:00+00:00"
                  },
                  {
                    "input_type": "evidence",
                    "input_id": "urn:cognous:evidence:optional-context",
                    "expected": {},
                    "observed": {
                      "state": "unknown",
                      "observed_at": "2026-10-05T19:00:00+00:00"
                    },
                    "record_commitment": "sha256:9918ca9a4e1da9eee69322d6c0b107f215773957e569ee85e5ca1abb94c267cd",
                    "missing": false,
                    "previous_observed_at": "2026-10-05T19:00:00+00:00"
                  },
                  {
                    "input_type": "purpose",
                    "input_id": "sha256:6408c3a34b12a6f20f3bb978552aa9412812d9e366d53a8a27bc9ea7ea28da9b",
                    "expected": {},
                    "observed": {
                      "state": "closed",
                      "observed_at": "2026-10-05T19:00:00+00:00",
                      "epoch": "epoch-1",
                      "epoch_capability": "authoritative"
                    },
                    "record_commitment": "sha256:0bddd392557c3bcacb9075e1559633c7cd0fd9011349a00105b842c04fbf0f8d",
                    "missing": false,
                    "previous_observed_at": "2026-10-05T19:00:00+00:00"
                  }
                ]
              }
            }
          }
        }
      ],
      "links": [],
      "commitments": [
        {
          "label": "payload_commitment",
          "value": "sha256:6b782ebbcc034edeca4069b31aa4d8cbc9d3eeaf3b2034ab989bb430de962c0e",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "source_record_id": "control-plane-programme2-profiles@2bac7875:runtime_proposal:0",
          "source_path": "proposal.payload_commitment",
          "verification_status": "checked_match",
          "notes": null
        },
        {
          "label": "effect_id",
          "value": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "source_record_id": "control-plane-programme2-profiles@2bac7875:runtime_decision:1",
          "source_path": "decisions[0].effect_id",
          "verification_status": "checked_match",
          "notes": "Checked under pinned Control Plane effect-id contract."
        },
        {
          "label": "proposal_commitment",
          "value": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "source_record_id": "control-plane-programme2-profiles@2bac7875:runtime_decision:1",
          "source_path": "decisions[0].binding.proposal_commitment",
          "verification_status": "attributed_claim",
          "notes": null
        },
        {
          "label": "manifest_digest",
          "value": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "source_record_id": "control-plane-programme2-profiles@2bac7875:runtime_decision:1",
          "source_path": "decisions[0].binding.manifest_digest",
          "verification_status": "attributed_claim",
          "notes": null
        },
        {
          "label": "payload_commitment",
          "value": "sha256:6b782ebbcc034edeca4069b31aa4d8cbc9d3eeaf3b2034ab989bb430de962c0e",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "source_record_id": "control-plane-programme2-profiles@2bac7875:runtime_decision:1",
          "source_path": "decisions[0].binding.payload_commitment",
          "verification_status": "attributed_claim",
          "notes": null
        },
        {
          "label": "requirement_commitment",
          "value": "sha256:6590406e701b51e637c87953860d1ceb72d8da0af87311048f152e0ee2b8ccb6",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "source_record_id": "control-plane-programme2-profiles@2bac7875:runtime_decision:1",
          "source_path": "decisions[0].binding.requirement_commitment",
          "verification_status": "attributed_claim",
          "notes": null
        },
        {
          "label": "role_mapping_digest",
          "value": "sha256:f8a8db156df7087ddf34be1ed77fc86fa20ba7668deb87a9b3a5bd0a6ace496d",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "source_record_id": "control-plane-programme2-profiles@2bac7875:runtime_decision:1",
          "source_path": "decisions[0].binding.role_mapping_digest",
          "verification_status": "attributed_claim",
          "notes": null
        },
        {
          "label": "payload_commitment",
          "value": "sha256:6b782ebbcc034edeca4069b31aa4d8cbc9d3eeaf3b2034ab989bb430de962c0e",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "source_record_id": "moltbot-safe-executor-producer-2.0.0@6b16962d:execution_envelope:34",
          "source_path": "moltbot.execution_envelope.operation.payload_commitment",
          "verification_status": "checked_match",
          "notes": null
        }
      ],
      "import_reports": [
        {
          "adapter_profile": "control-plane-programme2-profiles@2bac7875",
          "source_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
          "complete": true,
          "field_mappings": {
            "decisions": "records[runtime_decision]",
            "attempts": "records[control_plane_attempt_transition]",
            "observations": "records[effect_observation]",
            "reconciliations": "records[reconciliation]",
            "refusals": "records[effect_time_refusal]",
            "resolution_checks": "records[resolution_check]",
            "closeouts": "records[attempt_closeout]",
            "input_time_floors": "records[input_time_floors]",
            "check_events": "records[resolution_check_event]",
            "vocabulary_changes": "records[reason_vocabulary_change]"
          },
          "findings": [
            {
              "code": "M003",
              "category": "conversion_warning",
              "severity": "info",
              "path": "moltbot.execution_envelope.operation.institution_id",
              "message": "Institution/domain provenance is the trusted Moltbot integration context, not Control Plane AuthorizationBinding.",
              "value_state": null
            },
            {
              "code": "M004",
              "category": "conversion_warning",
              "severity": "info",
              "path": "moltbot.execution_envelope.operation.authority_context_id",
              "message": "At the pinned adapter this field carries the proposal profile reference; it is distinct from the Control Plane binding context-instance ID.",
              "value_state": null
            }
          ]
        }
      ],
      "semantics": {
        "record_reconstruction": true,
        "policy_reevaluation": false,
        "model_reexecution": false,
        "external_effect_execution": false,
        "destination_observation": "producer_reported",
        "independent_effect_verification": false,
        "notes": "Replay reconstructs recorded events only; import never renews permission or creates an effect."
      },
      "derivation": null,
      "integrity": [],
      "metadata": {
        "effect_observation_history": {
          "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829": {
            "basis": "Control Plane reconciliation array order, filtered by exact effect_id",
            "rejected_reconciliation_indices": [],
            "latest_reconciliation": null,
            "latest_accepted_observation": null,
            "latest_supported_destination_state": "unknown",
            "retry_eligible": null,
            "acknowledgement_history": [],
            "cross_sequence_order": "not_established",
            "freshness_at_import": "not_evaluated"
          }
        },
        "control_plane_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
        "moltbot_safe_revision": "6b16962db140590b808f02b5c2cb11a217aec46f",
        "moltbot_producer_contract": {
          "profile_id": "moltbot-safe-executor-producer-2.0.0@6b16962d",
          "control_plane_revision": "2bac7875391cad0a431fa0d75208b7ade39743e3",
          "compatible_control_plane_revisions": [
            "2bac7875391cad0a431fa0d75208b7ade39743e3"
          ],
          "repository_revision": "6b16962db140590b808f02b5c2cb11a217aec46f",
          "interface_profile_id": "urn:cognous:profiles:moltbot-safe-executor-producer",
          "interface_profile_version": "2.0.0",
          "provenance": {
            "mode": "versioned_profile",
            "source_asserted": {
              "repository_revision": "6b16962db140590b808f02b5c2cb11a217aec46f",
              "producer_profile_id": "urn:cognous:profiles:moltbot-safe-executor-producer",
              "producer_profile_version": "2.0.0"
            },
            "independently_established": []
          },
          "legacy": false
        },
        "manifest_revision": "ff5490828b2bf7f6a976da209f3f533701855687",
        "executor_failure_reference_verification": "source_asserted_not_independently_verified",
        "alvorada_revision": "fb3d97938969a89e149e8ff8db2756091d1233fc"
      }
    }
  },
  "retained_source_scope": "exact supplied sources, including declared redaction/derivative lineage; no unredaction",
  "lifecycle_records": {
    "runtime_proposal": [
      {
        "manifest_id": "refund-integration-pilot-v1",
        "manifest_version": "1.1",
        "manifest_digest": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
        "actor": "urn:cognous:identity:refund-agent-1",
        "principal": "urn:cognous:principal:refund-service",
        "action_id": "urn:cognous:action:refund-issue-routine-v1",
        "adapter_id": "urn:cognous:adapter:synthetic-refund-v1",
        "target": "urn:cognous:synthetic-account:customer-001",
        "payload": {
          "customer_id": "customer-001",
          "refund_reason": "duplicate"
        },
        "payload_commitment": "sha256:6b782ebbcc034edeca4069b31aa4d8cbc9d3eeaf3b2034ab989bb430de962c0e",
        "requested_permissions": [
          "refund.issue.routine"
        ],
        "amount": 50.0,
        "unit": "USD",
        "effects": 1,
        "authority_context_ref": "urn:cognous:alvorada:public-stack-profile:0.1.0",
        "requirement_id": "urn:cognous:authority-requirement:refund-routine-v1",
        "risk_metadata": {},
        "not_before": null,
        "expires_at": null,
        "correlation_id": "case-1",
        "run_id": "run-1",
        "expected_side_effects": [],
        "evidence_refs": [
          "urn:cognous:evidence:refund-entitlement"
        ]
      }
    ],
    "runtime_decision": [
      {
        "reason_vocabulary_version": "runtime-authority-reasons/0.1",
        "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "result": "authorized",
        "reasons": [],
        "decided_at": "2026-10-05T19:00:00+00:00",
        "time_source": "test_override",
        "operation_horizon": {
          "source": "runtime_proposal",
          "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
          "not_before": null,
          "expires_at": null
        },
        "binding": {
          "runtime_authority": {
            "profile": "runtime-authority/0.1",
            "approval_commitment": "sha256:ebd9bfb69fb2894a63291d67fbc9fe07f58eb2f320f48286f7b6a003d2adfe86",
            "required_inputs_digest": "sha256:1c4ef694ed72bdf927f6ad39982e981634c16ad2f303b8a718b078de2aaaffaf",
            "catalogue_digest": "sha256:b39642c9ecdaf334a778fcda63576997843e5c8765758d8f6248e3e54555ed6a",
            "expected_effective_grant_digest": "sha256:4b43b997e7a5dc9b70f51ffa8917eaeb79f7df04f108f81a90e0997de3602b31",
            "effective_grant_derivation_version": "effective-grant/0.1"
          },
          "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
          "manifest_id": "refund-integration-pilot-v1",
          "manifest_version": "1.1",
          "manifest_digest": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
          "actor": "urn:cognous:identity:refund-agent-1",
          "principal": "urn:cognous:principal:refund-service",
          "action_id": "urn:cognous:action:refund-issue-routine-v1",
          "adapter_id": "urn:cognous:adapter:synthetic-refund-v1",
          "target": "urn:cognous:synthetic-account:customer-001",
          "payload_commitment": "sha256:6b782ebbcc034edeca4069b31aa4d8cbc9d3eeaf3b2034ab989bb430de962c0e",
          "requested_permissions": [
            "refund.issue.routine"
          ],
          "amount": 50.0,
          "unit": "USD",
          "effects": 1,
          "authority_context_id": "urn:cognous:authority-context:pilot-1",
          "authority_context_version": "0.1.0",
          "authority_context_status": "proposed_pending_governor_review",
          "requirement_id": "urn:cognous:authority-requirement:refund-routine-v1",
          "requirement_commitment": "sha256:6590406e701b51e637c87953860d1ceb72d8da0af87311048f152e0ee2b8ccb6",
          "grant_id": "urn:cognous:grant:routine-1",
          "grant_revision": "1",
          "policy_versions": [
            {
              "ref": "urn:cognous:policy:refund-policy",
              "version": "1.0"
            }
          ],
          "role_mapping_version": "roles-v1",
          "role_mapping_digest": "sha256:f8a8db156df7087ddf34be1ed77fc86fa20ba7668deb87a9b3a5bd0a6ace496d",
          "effective_max_effects": 1
        },
        "resolution_inputs": [
          {
            "input_type": "manifest",
            "input_id": "refund-integration-pilot-v1",
            "expected": {},
            "observed": {},
            "record_commitment": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "authority_context",
            "input_id": "urn:cognous:alvorada:public-stack-profile:0.1.0",
            "expected": {},
            "observed": {
              "schema_version": "0.1.0",
              "interface_status": "proposed_pending_governor_review"
            },
            "record_commitment": "sha256:b0727efe67e8d7c656d48a20129dea61621acf99cda8371c67ab550d4caca342",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "role_mapping",
            "input_id": "urn:cognous:institution:synthetic-customer-service",
            "expected": {},
            "observed": {
              "version": "roles-v1",
              "digest": "sha256:f8a8db156df7087ddf34be1ed77fc86fa20ba7668deb87a9b3a5bd0a6ace496d"
            },
            "record_commitment": "sha256:fc884333b0da586ae781c0c4289729465659c719c0e4602758ddbf7a2bdcb89e",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "identity",
            "input_id": "urn:cognous:identity:refund-agent-1",
            "expected": {},
            "observed": {
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:5eee426c0827b2b01acc16f0acf3bd13fcfc315ad851c406822dc3242a0b18d3",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "mandate",
            "input_id": "urn:cognous:issuance:1",
            "expected": {},
            "observed": {
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:d023eb722343620d7b2d4e622e0283008d72c903ef81c15d9b3dbaada7648091",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "grant",
            "input_id": "urn:cognous:grant:routine-1",
            "expected": {
              "revision": "1",
              "status": "active"
            },
            "observed": {
              "revision": "1",
              "status": "active",
              "version": "status-v1",
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:eded76117318d91618259e7ed8eced201b868bb5f714d49fbf751535a6b8a859",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "conflict",
            "input_id": "urn:cognous:authority-requirement:refund-routine-v1",
            "expected": {},
            "observed": {
              "state": "clear",
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:b469c2e823a75ebd9ba5b0f315c1a092e9ef8d257e684f03a9c00765a065e2ec",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "policy",
            "input_id": "urn:cognous:policy:refund-policy",
            "expected": {
              "version": "1.0",
              "status": "active"
            },
            "observed": {
              "status": "active",
              "version": "1.0",
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:ff1302d24b132d1ccb1345ca47ecd25be2200335621ca133e01f54c384007e30",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "approval",
            "input_id": "urn:cognous:approval:t1-1",
            "expected": {
              "grant_revision": "1",
              "status": "active",
              "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
              "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
              "grant_id": "urn:cognous:grant:routine-1"
            },
            "observed": {
              "status": "active",
              "observed_at": "2026-10-05T19:00:00+00:00",
              "grant_revision": "1",
              "runtime_authority_commitment": "sha256:ebd9bfb69fb2894a63291d67fbc9fe07f58eb2f320f48286f7b6a003d2adfe86",
              "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
              "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
              "grant_id": "urn:cognous:grant:routine-1"
            },
            "record_commitment": "sha256:373729df30fd57ccf14073ac25b970c15d0303da8e39ae39474d67e72542dbad",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "evidence",
            "input_id": "urn:cognous:evidence:refund-entitlement",
            "expected": {
              "state": "current"
            },
            "observed": {
              "state": "current",
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:41ac78e62c85e85b6ba4dd94a60a430c4cdb94cbcf1a51a42a3850b61def1d4f",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "evidence",
            "input_id": "urn:cognous:evidence:optional-context",
            "expected": {},
            "observed": {
              "state": "unknown",
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:9918ca9a4e1da9eee69322d6c0b107f215773957e569ee85e5ca1abb94c267cd",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "purpose",
            "input_id": "sha256:6408c3a34b12a6f20f3bb978552aa9412812d9e366d53a8a27bc9ea7ea28da9b",
            "expected": {},
            "observed": {
              "state": "open",
              "observed_at": "2026-10-05T19:00:00+00:00",
              "epoch": "epoch-1",
              "epoch_capability": "authoritative"
            },
            "record_commitment": "sha256:52c634d9df00e6477998ba35e96be5316ab560a689439610bc4a01c15467a8f6",
            "missing": false,
            "previous_observed_at": null
          }
        ]
      }
    ],
    "effect_time_refusal": [
      {
        "reason_vocabulary_version": "runtime-authority-reasons/0.1",
        "refusal_id": "614005f1-545a-4b5c-b1f3-43241683e304",
        "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "time_source": "test_override",
        "original_operation_horizon": {
          "source": "runtime_proposal",
          "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
          "not_before": null,
          "expires_at": null
        },
        "operation_horizon": {
          "source": "runtime_proposal",
          "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
          "not_before": null,
          "expires_at": null
        },
        "stage": "effect_time_revalidation",
        "reasons": [
          "purpose_closed"
        ],
        "changed_inputs": [],
        "resolution_inputs": [
          {
            "input_type": "manifest",
            "input_id": "refund-integration-pilot-v1",
            "expected": {},
            "observed": {},
            "record_commitment": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "authority_context",
            "input_id": "urn:cognous:alvorada:public-stack-profile:0.1.0",
            "expected": {},
            "observed": {
              "schema_version": "0.1.0",
              "interface_status": "proposed_pending_governor_review"
            },
            "record_commitment": "sha256:b0727efe67e8d7c656d48a20129dea61621acf99cda8371c67ab550d4caca342",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "role_mapping",
            "input_id": "urn:cognous:institution:synthetic-customer-service",
            "expected": {},
            "observed": {
              "version": "roles-v1",
              "digest": "sha256:f8a8db156df7087ddf34be1ed77fc86fa20ba7668deb87a9b3a5bd0a6ace496d"
            },
            "record_commitment": "sha256:fc884333b0da586ae781c0c4289729465659c719c0e4602758ddbf7a2bdcb89e",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "identity",
            "input_id": "urn:cognous:identity:refund-agent-1",
            "expected": {},
            "observed": {
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:5eee426c0827b2b01acc16f0acf3bd13fcfc315ad851c406822dc3242a0b18d3",
            "missing": false,
            "previous_observed_at": "2026-10-05T19:00:00+00:00"
          },
          {
            "input_type": "mandate",
            "input_id": "urn:cognous:issuance:1",
            "expected": {},
            "observed": {
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:d023eb722343620d7b2d4e622e0283008d72c903ef81c15d9b3dbaada7648091",
            "missing": false,
            "previous_observed_at": "2026-10-05T19:00:00+00:00"
          },
          {
            "input_type": "grant",
            "input_id": "urn:cognous:grant:routine-1",
            "expected": {
              "revision": "1",
              "status": "active"
            },
            "observed": {
              "revision": "1",
              "status": "active",
              "version": "status-v1",
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:eded76117318d91618259e7ed8eced201b868bb5f714d49fbf751535a6b8a859",
            "missing": false,
            "previous_observed_at": "2026-10-05T19:00:00+00:00"
          },
          {
            "input_type": "conflict",
            "input_id": "urn:cognous:authority-requirement:refund-routine-v1",
            "expected": {},
            "observed": {
              "state": "clear",
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:b469c2e823a75ebd9ba5b0f315c1a092e9ef8d257e684f03a9c00765a065e2ec",
            "missing": false,
            "previous_observed_at": "2026-10-05T19:00:00+00:00"
          },
          {
            "input_type": "policy",
            "input_id": "urn:cognous:policy:refund-policy",
            "expected": {
              "version": "1.0",
              "status": "active"
            },
            "observed": {
              "status": "active",
              "version": "1.0",
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:ff1302d24b132d1ccb1345ca47ecd25be2200335621ca133e01f54c384007e30",
            "missing": false,
            "previous_observed_at": "2026-10-05T19:00:00+00:00"
          },
          {
            "input_type": "approval",
            "input_id": "urn:cognous:approval:t1-1",
            "expected": {
              "grant_revision": "1",
              "status": "active",
              "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
              "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
              "grant_id": "urn:cognous:grant:routine-1"
            },
            "observed": {
              "status": "active",
              "observed_at": "2026-10-05T19:00:00+00:00",
              "grant_revision": "1",
              "runtime_authority_commitment": "sha256:ebd9bfb69fb2894a63291d67fbc9fe07f58eb2f320f48286f7b6a003d2adfe86",
              "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
              "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
              "grant_id": "urn:cognous:grant:routine-1"
            },
            "record_commitment": "sha256:373729df30fd57ccf14073ac25b970c15d0303da8e39ae39474d67e72542dbad",
            "missing": false,
            "previous_observed_at": "2026-10-05T19:00:00+00:00"
          },
          {
            "input_type": "evidence",
            "input_id": "urn:cognous:evidence:refund-entitlement",
            "expected": {
              "state": "current"
            },
            "observed": {
              "state": "current",
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:41ac78e62c85e85b6ba4dd94a60a430c4cdb94cbcf1a51a42a3850b61def1d4f",
            "missing": false,
            "previous_observed_at": "2026-10-05T19:00:00+00:00"
          },
          {
            "input_type": "evidence",
            "input_id": "urn:cognous:evidence:optional-context",
            "expected": {},
            "observed": {
              "state": "unknown",
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:9918ca9a4e1da9eee69322d6c0b107f215773957e569ee85e5ca1abb94c267cd",
            "missing": false,
            "previous_observed_at": "2026-10-05T19:00:00+00:00"
          },
          {
            "input_type": "purpose",
            "input_id": "sha256:6408c3a34b12a6f20f3bb978552aa9412812d9e366d53a8a27bc9ea7ea28da9b",
            "expected": {},
            "observed": {
              "state": "closed",
              "observed_at": "2026-10-05T19:00:00+00:00",
              "epoch": "epoch-1",
              "epoch_capability": "authoritative"
            },
            "record_commitment": "sha256:0bddd392557c3bcacb9075e1559633c7cd0fd9011349a00105b842c04fbf0f8d",
            "missing": false,
            "previous_observed_at": "2026-10-05T19:00:00+00:00"
          }
        ]
      }
    ],
    "resolution_check": [
      {
        "check_id": "73f13d48-dd8b-4be6-b05e-a4d3b47f01ac",
        "stage": "decision",
        "evaluated_at": "2026-10-05T19:00:00+00:00",
        "time_source": "test_override",
        "inputs": [
          {
            "input_type": "manifest",
            "input_id": "refund-integration-pilot-v1",
            "expected": {},
            "observed": {},
            "record_commitment": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "authority_context",
            "input_id": "urn:cognous:alvorada:public-stack-profile:0.1.0",
            "expected": {},
            "observed": {
              "schema_version": "0.1.0",
              "interface_status": "proposed_pending_governor_review"
            },
            "record_commitment": "sha256:b0727efe67e8d7c656d48a20129dea61621acf99cda8371c67ab550d4caca342",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "role_mapping",
            "input_id": "urn:cognous:institution:synthetic-customer-service",
            "expected": {},
            "observed": {
              "version": "roles-v1",
              "digest": "sha256:f8a8db156df7087ddf34be1ed77fc86fa20ba7668deb87a9b3a5bd0a6ace496d"
            },
            "record_commitment": "sha256:fc884333b0da586ae781c0c4289729465659c719c0e4602758ddbf7a2bdcb89e",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "identity",
            "input_id": "urn:cognous:identity:refund-agent-1",
            "expected": {},
            "observed": {
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:5eee426c0827b2b01acc16f0acf3bd13fcfc315ad851c406822dc3242a0b18d3",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "mandate",
            "input_id": "urn:cognous:issuance:1",
            "expected": {},
            "observed": {
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:d023eb722343620d7b2d4e622e0283008d72c903ef81c15d9b3dbaada7648091",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "grant",
            "input_id": "urn:cognous:grant:routine-1",
            "expected": {
              "revision": "1",
              "status": "active"
            },
            "observed": {
              "revision": "1",
              "status": "active",
              "version": "status-v1",
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:eded76117318d91618259e7ed8eced201b868bb5f714d49fbf751535a6b8a859",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "conflict",
            "input_id": "urn:cognous:authority-requirement:refund-routine-v1",
            "expected": {},
            "observed": {
              "state": "clear",
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:b469c2e823a75ebd9ba5b0f315c1a092e9ef8d257e684f03a9c00765a065e2ec",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "policy",
            "input_id": "urn:cognous:policy:refund-policy",
            "expected": {
              "version": "1.0",
              "status": "active"
            },
            "observed": {
              "status": "active",
              "version": "1.0",
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:ff1302d24b132d1ccb1345ca47ecd25be2200335621ca133e01f54c384007e30",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "approval",
            "input_id": "urn:cognous:approval:t1-1",
            "expected": {
              "grant_revision": "1",
              "status": "active",
              "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
              "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
              "grant_id": "urn:cognous:grant:routine-1"
            },
            "observed": {
              "status": "active",
              "observed_at": "2026-10-05T19:00:00+00:00",
              "grant_revision": "1",
              "runtime_authority_commitment": "sha256:ebd9bfb69fb2894a63291d67fbc9fe07f58eb2f320f48286f7b6a003d2adfe86",
              "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
              "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
              "grant_id": "urn:cognous:grant:routine-1"
            },
            "record_commitment": "sha256:373729df30fd57ccf14073ac25b970c15d0303da8e39ae39474d67e72542dbad",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "evidence",
            "input_id": "urn:cognous:evidence:refund-entitlement",
            "expected": {
              "state": "current"
            },
            "observed": {
              "state": "current",
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:41ac78e62c85e85b6ba4dd94a60a430c4cdb94cbcf1a51a42a3850b61def1d4f",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "evidence",
            "input_id": "urn:cognous:evidence:optional-context",
            "expected": {},
            "observed": {
              "state": "unknown",
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:9918ca9a4e1da9eee69322d6c0b107f215773957e569ee85e5ca1abb94c267cd",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "purpose",
            "input_id": "sha256:6408c3a34b12a6f20f3bb978552aa9412812d9e366d53a8a27bc9ea7ea28da9b",
            "expected": {},
            "observed": {
              "state": "open",
              "observed_at": "2026-10-05T19:00:00+00:00",
              "epoch": "epoch-1",
              "epoch_capability": "authoritative"
            },
            "record_commitment": "sha256:52c634d9df00e6477998ba35e96be5316ab560a689439610bc4a01c15467a8f6",
            "missing": false,
            "previous_observed_at": null
          }
        ],
        "reasons": []
      },
      {
        "check_id": "dc7a7987-6167-4081-a897-1925400b54db",
        "stage": "effect",
        "evaluated_at": "2026-10-05T19:00:00+00:00",
        "time_source": "test_override",
        "inputs": [
          {
            "input_type": "manifest",
            "input_id": "refund-integration-pilot-v1",
            "expected": {},
            "observed": {},
            "record_commitment": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "authority_context",
            "input_id": "urn:cognous:alvorada:public-stack-profile:0.1.0",
            "expected": {},
            "observed": {
              "schema_version": "0.1.0",
              "interface_status": "proposed_pending_governor_review"
            },
            "record_commitment": "sha256:b0727efe67e8d7c656d48a20129dea61621acf99cda8371c67ab550d4caca342",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "role_mapping",
            "input_id": "urn:cognous:institution:synthetic-customer-service",
            "expected": {},
            "observed": {
              "version": "roles-v1",
              "digest": "sha256:f8a8db156df7087ddf34be1ed77fc86fa20ba7668deb87a9b3a5bd0a6ace496d"
            },
            "record_commitment": "sha256:fc884333b0da586ae781c0c4289729465659c719c0e4602758ddbf7a2bdcb89e",
            "missing": false,
            "previous_observed_at": null
          },
          {
            "input_type": "identity",
            "input_id": "urn:cognous:identity:refund-agent-1",
            "expected": {},
            "observed": {
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:5eee426c0827b2b01acc16f0acf3bd13fcfc315ad851c406822dc3242a0b18d3",
            "missing": false,
            "previous_observed_at": "2026-10-05T19:00:00+00:00"
          },
          {
            "input_type": "mandate",
            "input_id": "urn:cognous:issuance:1",
            "expected": {},
            "observed": {
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:d023eb722343620d7b2d4e622e0283008d72c903ef81c15d9b3dbaada7648091",
            "missing": false,
            "previous_observed_at": "2026-10-05T19:00:00+00:00"
          },
          {
            "input_type": "grant",
            "input_id": "urn:cognous:grant:routine-1",
            "expected": {
              "revision": "1",
              "status": "active"
            },
            "observed": {
              "revision": "1",
              "status": "active",
              "version": "status-v1",
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:eded76117318d91618259e7ed8eced201b868bb5f714d49fbf751535a6b8a859",
            "missing": false,
            "previous_observed_at": "2026-10-05T19:00:00+00:00"
          },
          {
            "input_type": "conflict",
            "input_id": "urn:cognous:authority-requirement:refund-routine-v1",
            "expected": {},
            "observed": {
              "state": "clear",
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:b469c2e823a75ebd9ba5b0f315c1a092e9ef8d257e684f03a9c00765a065e2ec",
            "missing": false,
            "previous_observed_at": "2026-10-05T19:00:00+00:00"
          },
          {
            "input_type": "policy",
            "input_id": "urn:cognous:policy:refund-policy",
            "expected": {
              "version": "1.0",
              "status": "active"
            },
            "observed": {
              "status": "active",
              "version": "1.0",
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:ff1302d24b132d1ccb1345ca47ecd25be2200335621ca133e01f54c384007e30",
            "missing": false,
            "previous_observed_at": "2026-10-05T19:00:00+00:00"
          },
          {
            "input_type": "approval",
            "input_id": "urn:cognous:approval:t1-1",
            "expected": {
              "grant_revision": "1",
              "status": "active",
              "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
              "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
              "grant_id": "urn:cognous:grant:routine-1"
            },
            "observed": {
              "status": "active",
              "observed_at": "2026-10-05T19:00:00+00:00",
              "grant_revision": "1",
              "runtime_authority_commitment": "sha256:ebd9bfb69fb2894a63291d67fbc9fe07f58eb2f320f48286f7b6a003d2adfe86",
              "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
              "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
              "grant_id": "urn:cognous:grant:routine-1"
            },
            "record_commitment": "sha256:373729df30fd57ccf14073ac25b970c15d0303da8e39ae39474d67e72542dbad",
            "missing": false,
            "previous_observed_at": "2026-10-05T19:00:00+00:00"
          },
          {
            "input_type": "evidence",
            "input_id": "urn:cognous:evidence:refund-entitlement",
            "expected": {
              "state": "current"
            },
            "observed": {
              "state": "current",
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:41ac78e62c85e85b6ba4dd94a60a430c4cdb94cbcf1a51a42a3850b61def1d4f",
            "missing": false,
            "previous_observed_at": "2026-10-05T19:00:00+00:00"
          },
          {
            "input_type": "evidence",
            "input_id": "urn:cognous:evidence:optional-context",
            "expected": {},
            "observed": {
              "state": "unknown",
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:9918ca9a4e1da9eee69322d6c0b107f215773957e569ee85e5ca1abb94c267cd",
            "missing": false,
            "previous_observed_at": "2026-10-05T19:00:00+00:00"
          },
          {
            "input_type": "purpose",
            "input_id": "sha256:6408c3a34b12a6f20f3bb978552aa9412812d9e366d53a8a27bc9ea7ea28da9b",
            "expected": {},
            "observed": {
              "state": "closed",
              "observed_at": "2026-10-05T19:00:00+00:00",
              "epoch": "epoch-1",
              "epoch_capability": "authoritative"
            },
            "record_commitment": "sha256:0bddd392557c3bcacb9075e1559633c7cd0fd9011349a00105b842c04fbf0f8d",
            "missing": false,
            "previous_observed_at": "2026-10-05T19:00:00+00:00"
          }
        ],
        "reasons": [
          "purpose_closed"
        ]
      }
    ],
    "input_time_floors": [
      {
        "sha256:7052a5b98597102f45a2c4ab494a5e1006ff104c4b86e5222e2b59f330c30418": "2026-10-05T19:00:00+00:00",
        "sha256:4d8e3965e23d0c43249d12bd33f98502d07aa9b8675d4e94deeef9194b96eccc": "2026-10-05T19:00:00+00:00",
        "sha256:bb70894893d767f392df7aea0070fff70716cb6b934ea3664ba852518b781eda": "2026-10-05T19:00:00+00:00",
        "sha256:759e6cc704cb5cda55ed8925b417f92ff0f83b8d81ed7959ddc439d3d01ba75b": "2026-10-05T19:00:00+00:00",
        "sha256:e25ac65c4ed37739a2ab3e879dc2435ddb4df8687db4c6665e8cff3a835513cc": "2026-10-05T19:00:00+00:00",
        "sha256:7357f30a03d77811d73178b90d4e8c7d343cc0879fa341d529623ef70db9b793": "2026-10-05T19:00:00+00:00",
        "sha256:74437776fe13ee871e8efddb996b26b2deb270f19bb09854f8f09d6b76b80b5c": "2026-10-05T19:00:00+00:00",
        "sha256:6e2ad318158316fbe204f27531f5d59e0588a8e1338eb41b36917b88b7067de6": "2026-10-05T19:00:00+00:00",
        "sha256:84ef6acdaeaba04146c274ef7764315de0eb79f6449d00779611a0cfa0ef3af4": "2026-10-05T19:00:00+00:00"
      }
    ],
    "resolution_check_event": [
      {
        "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
        "phase": "opened",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": null,
        "effect_id": null,
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": null,
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": null,
        "effect_id": null,
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": {
          "input_type": "manifest",
          "input_id": "refund-integration-pilot-v1",
          "expected": {},
          "observed": {},
          "record_commitment": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": null,
        "effect_id": null,
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": {
          "input_type": "authority_context",
          "input_id": "urn:cognous:alvorada:public-stack-profile:0.1.0",
          "expected": {},
          "observed": {
            "schema_version": "0.1.0",
            "interface_status": "proposed_pending_governor_review"
          },
          "record_commitment": "sha256:b0727efe67e8d7c656d48a20129dea61621acf99cda8371c67ab550d4caca342",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": null,
        "effect_id": null,
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": {
          "input_type": "role_mapping",
          "input_id": "urn:cognous:institution:synthetic-customer-service",
          "expected": {},
          "observed": {
            "version": "roles-v1",
            "digest": "sha256:f8a8db156df7087ddf34be1ed77fc86fa20ba7668deb87a9b3a5bd0a6ace496d"
          },
          "record_commitment": "sha256:fc884333b0da586ae781c0c4289729465659c719c0e4602758ddbf7a2bdcb89e",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": null,
        "effect_id": null,
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": {
          "input_type": "identity",
          "input_id": "urn:cognous:identity:refund-agent-1",
          "expected": {},
          "observed": {
            "observed_at": "2026-10-05T19:00:00+00:00"
          },
          "record_commitment": "sha256:5eee426c0827b2b01acc16f0acf3bd13fcfc315ad851c406822dc3242a0b18d3",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": null,
        "effect_id": null,
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": {
          "input_type": "mandate",
          "input_id": "urn:cognous:issuance:1",
          "expected": {},
          "observed": {
            "observed_at": "2026-10-05T19:00:00+00:00"
          },
          "record_commitment": "sha256:d023eb722343620d7b2d4e622e0283008d72c903ef81c15d9b3dbaada7648091",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": null,
        "effect_id": null,
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": {
          "input_type": "grant",
          "input_id": "urn:cognous:grant:routine-1",
          "expected": {
            "revision": "1",
            "status": "active"
          },
          "observed": {
            "revision": "1",
            "status": "active",
            "version": "status-v1",
            "observed_at": "2026-10-05T19:00:00+00:00"
          },
          "record_commitment": "sha256:eded76117318d91618259e7ed8eced201b868bb5f714d49fbf751535a6b8a859",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": null,
        "effect_id": null,
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": {
          "input_type": "conflict",
          "input_id": "urn:cognous:authority-requirement:refund-routine-v1",
          "expected": {},
          "observed": {
            "state": "clear",
            "observed_at": "2026-10-05T19:00:00+00:00"
          },
          "record_commitment": "sha256:b469c2e823a75ebd9ba5b0f315c1a092e9ef8d257e684f03a9c00765a065e2ec",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": null,
        "effect_id": null,
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": {
          "input_type": "policy",
          "input_id": "urn:cognous:policy:refund-policy",
          "expected": {
            "version": "1.0",
            "status": "active"
          },
          "observed": {
            "status": "active",
            "version": "1.0",
            "observed_at": "2026-10-05T19:00:00+00:00"
          },
          "record_commitment": "sha256:ff1302d24b132d1ccb1345ca47ecd25be2200335621ca133e01f54c384007e30",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": null,
        "effect_id": null,
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": {
          "input_type": "approval",
          "input_id": "urn:cognous:approval:t1-1",
          "expected": {
            "grant_revision": "1",
            "status": "active",
            "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
            "grant_id": "urn:cognous:grant:routine-1"
          },
          "observed": {
            "status": "active",
            "observed_at": "2026-10-05T19:00:00+00:00",
            "grant_revision": "1",
            "runtime_authority_commitment": "sha256:ebd9bfb69fb2894a63291d67fbc9fe07f58eb2f320f48286f7b6a003d2adfe86",
            "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
            "grant_id": "urn:cognous:grant:routine-1"
          },
          "record_commitment": "sha256:373729df30fd57ccf14073ac25b970c15d0303da8e39ae39474d67e72542dbad",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": null,
        "effect_id": null,
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": {
          "input_type": "evidence",
          "input_id": "urn:cognous:evidence:refund-entitlement",
          "expected": {
            "state": "current"
          },
          "observed": {
            "state": "current",
            "observed_at": "2026-10-05T19:00:00+00:00"
          },
          "record_commitment": "sha256:41ac78e62c85e85b6ba4dd94a60a430c4cdb94cbcf1a51a42a3850b61def1d4f",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": null,
        "effect_id": null,
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": {
          "input_type": "evidence",
          "input_id": "urn:cognous:evidence:optional-context",
          "expected": {},
          "observed": {
            "state": "unknown",
            "observed_at": "2026-10-05T19:00:00+00:00"
          },
          "record_commitment": "sha256:9918ca9a4e1da9eee69322d6c0b107f215773957e569ee85e5ca1abb94c267cd",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": null,
        "effect_id": null,
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": {
          "input_type": "purpose",
          "input_id": "sha256:6408c3a34b12a6f20f3bb978552aa9412812d9e366d53a8a27bc9ea7ea28da9b",
          "expected": {},
          "observed": {
            "state": "open",
            "observed_at": "2026-10-05T19:00:00+00:00",
            "epoch": "epoch-1",
            "epoch_capability": "authoritative"
          },
          "record_commitment": "sha256:52c634d9df00e6477998ba35e96be5316ab560a689439610bc4a01c15467a8f6",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "64a54715-1361-4373-a5ee-d775cd1fce12",
        "phase": "completed",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "8be370e2-c60c-4020-9c95-884a22fa26fe"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": null,
        "effect_id": null,
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": null,
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
        "phase": "opened",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": null,
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": {
          "input_type": "manifest",
          "input_id": "refund-integration-pilot-v1",
          "expected": {},
          "observed": {},
          "record_commitment": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": {
          "input_type": "authority_context",
          "input_id": "urn:cognous:alvorada:public-stack-profile:0.1.0",
          "expected": {},
          "observed": {
            "schema_version": "0.1.0",
            "interface_status": "proposed_pending_governor_review"
          },
          "record_commitment": "sha256:b0727efe67e8d7c656d48a20129dea61621acf99cda8371c67ab550d4caca342",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": {
          "input_type": "role_mapping",
          "input_id": "urn:cognous:institution:synthetic-customer-service",
          "expected": {},
          "observed": {
            "version": "roles-v1",
            "digest": "sha256:f8a8db156df7087ddf34be1ed77fc86fa20ba7668deb87a9b3a5bd0a6ace496d"
          },
          "record_commitment": "sha256:fc884333b0da586ae781c0c4289729465659c719c0e4602758ddbf7a2bdcb89e",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": {
          "input_type": "identity",
          "input_id": "urn:cognous:identity:refund-agent-1",
          "expected": {},
          "observed": {
            "observed_at": "2026-10-05T19:00:00+00:00"
          },
          "record_commitment": "sha256:5eee426c0827b2b01acc16f0acf3bd13fcfc315ad851c406822dc3242a0b18d3",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": {
          "input_type": "mandate",
          "input_id": "urn:cognous:issuance:1",
          "expected": {},
          "observed": {
            "observed_at": "2026-10-05T19:00:00+00:00"
          },
          "record_commitment": "sha256:d023eb722343620d7b2d4e622e0283008d72c903ef81c15d9b3dbaada7648091",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": {
          "input_type": "grant",
          "input_id": "urn:cognous:grant:routine-1",
          "expected": {
            "revision": "1",
            "status": "active"
          },
          "observed": {
            "revision": "1",
            "status": "active",
            "version": "status-v1",
            "observed_at": "2026-10-05T19:00:00+00:00"
          },
          "record_commitment": "sha256:eded76117318d91618259e7ed8eced201b868bb5f714d49fbf751535a6b8a859",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": {
          "input_type": "conflict",
          "input_id": "urn:cognous:authority-requirement:refund-routine-v1",
          "expected": {},
          "observed": {
            "state": "clear",
            "observed_at": "2026-10-05T19:00:00+00:00"
          },
          "record_commitment": "sha256:b469c2e823a75ebd9ba5b0f315c1a092e9ef8d257e684f03a9c00765a065e2ec",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": {
          "input_type": "policy",
          "input_id": "urn:cognous:policy:refund-policy",
          "expected": {
            "version": "1.0",
            "status": "active"
          },
          "observed": {
            "status": "active",
            "version": "1.0",
            "observed_at": "2026-10-05T19:00:00+00:00"
          },
          "record_commitment": "sha256:ff1302d24b132d1ccb1345ca47ecd25be2200335621ca133e01f54c384007e30",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": {
          "input_type": "approval",
          "input_id": "urn:cognous:approval:t1-1",
          "expected": {
            "grant_revision": "1",
            "status": "active",
            "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
            "grant_id": "urn:cognous:grant:routine-1"
          },
          "observed": {
            "status": "active",
            "observed_at": "2026-10-05T19:00:00+00:00",
            "grant_revision": "1",
            "runtime_authority_commitment": "sha256:ebd9bfb69fb2894a63291d67fbc9fe07f58eb2f320f48286f7b6a003d2adfe86",
            "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
            "grant_id": "urn:cognous:grant:routine-1"
          },
          "record_commitment": "sha256:373729df30fd57ccf14073ac25b970c15d0303da8e39ae39474d67e72542dbad",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": {
          "input_type": "evidence",
          "input_id": "urn:cognous:evidence:refund-entitlement",
          "expected": {
            "state": "current"
          },
          "observed": {
            "state": "current",
            "observed_at": "2026-10-05T19:00:00+00:00"
          },
          "record_commitment": "sha256:41ac78e62c85e85b6ba4dd94a60a430c4cdb94cbcf1a51a42a3850b61def1d4f",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": {
          "input_type": "evidence",
          "input_id": "urn:cognous:evidence:optional-context",
          "expected": {},
          "observed": {
            "state": "unknown",
            "observed_at": "2026-10-05T19:00:00+00:00"
          },
          "record_commitment": "sha256:9918ca9a4e1da9eee69322d6c0b107f215773957e569ee85e5ca1abb94c267cd",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": {
          "input_type": "purpose",
          "input_id": "sha256:6408c3a34b12a6f20f3bb978552aa9412812d9e366d53a8a27bc9ea7ea28da9b",
          "expected": {},
          "observed": {
            "state": "closed",
            "observed_at": "2026-10-05T19:00:00+00:00",
            "epoch": "epoch-1",
            "epoch_capability": "authoritative"
          },
          "record_commitment": "sha256:0bddd392557c3bcacb9075e1559633c7cd0fd9011349a00105b842c04fbf0f8d",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "1e6cd453-45a4-4d07-87f1-68babeb40804",
        "phase": "completed",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "4737",
          "token": "1cb37772-8e36-4c09-a0ef-e1172560d88d"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": null,
        "reasons": [
          "purpose_closed"
        ],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      }
    ],
    "execution_envelope": [
      {
        "version": "0.2.0",
        "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "operation": {
          "actor": "urn:cognous:identity:refund-agent-1",
          "principal": "urn:cognous:principal:refund-service",
          "institution_id": "urn:cognous:institution:synthetic-customer-service",
          "authority_domain": "customer-refunds",
          "manifest_id": "refund-integration-pilot-v1",
          "manifest_version": "1.1",
          "manifest_digest": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
          "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
          "action_id": "urn:cognous:action:refund-issue-routine-v1",
          "adapter_id": "urn:cognous:adapter:synthetic-refund-v1",
          "target": "urn:cognous:synthetic-account:customer-001",
          "payload": {
            "customer_id": "customer-001",
            "refund_reason": "duplicate"
          },
          "payload_commitment": "sha256:6b782ebbcc034edeca4069b31aa4d8cbc9d3eeaf3b2034ab989bb430de962c0e",
          "requested_permissions": [
            "refund.issue.routine"
          ],
          "amount": 50.0,
          "unit": "USD",
          "effects": 1,
          "authority_context_id": "urn:cognous:alvorada:public-stack-profile:0.1.0",
          "requirement_id": "urn:cognous:authority-requirement:refund-routine-v1",
          "grant_id": "urn:cognous:grant:routine-1",
          "grant_revision": "1",
          "effective_max_effects": 1
        },
        "attempt_id": null
      }
    ],
    "executor_control_plane_evidence": [
      {
        "failure_record_id": "e7036bc4-f794-460a-80f5-b2ed3bde14a8",
        "refusal": {
          "reason_vocabulary_version": "runtime-authority-reasons/0.1",
          "refusal_id": "614005f1-545a-4b5c-b1f3-43241683e304",
          "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
          "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "time_source": "test_override",
          "original_operation_horizon": {
            "source": "runtime_proposal",
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "not_before": null,
            "expires_at": null
          },
          "operation_horizon": {
            "source": "runtime_proposal",
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "not_before": null,
            "expires_at": null
          },
          "stage": "effect_time_revalidation",
          "reasons": [
            "purpose_closed"
          ],
          "changed_inputs": [],
          "resolution_inputs": [
            {
              "input_type": "manifest",
              "input_id": "refund-integration-pilot-v1",
              "expected": {},
              "observed": {},
              "record_commitment": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
              "missing": false,
              "previous_observed_at": null
            },
            {
              "input_type": "authority_context",
              "input_id": "urn:cognous:alvorada:public-stack-profile:0.1.0",
              "expected": {},
              "observed": {
                "schema_version": "0.1.0",
                "interface_status": "proposed_pending_governor_review"
              },
              "record_commitment": "sha256:b0727efe67e8d7c656d48a20129dea61621acf99cda8371c67ab550d4caca342",
              "missing": false,
              "previous_observed_at": null
            },
            {
              "input_type": "role_mapping",
              "input_id": "urn:cognous:institution:synthetic-customer-service",
              "expected": {},
              "observed": {
                "version": "roles-v1",
                "digest": "sha256:f8a8db156df7087ddf34be1ed77fc86fa20ba7668deb87a9b3a5bd0a6ace496d"
              },
              "record_commitment": "sha256:fc884333b0da586ae781c0c4289729465659c719c0e4602758ddbf7a2bdcb89e",
              "missing": false,
              "previous_observed_at": null
            },
            {
              "input_type": "identity",
              "input_id": "urn:cognous:identity:refund-agent-1",
              "expected": {},
              "observed": {
                "observed_at": "2026-10-05T19:00:00+00:00"
              },
              "record_commitment": "sha256:5eee426c0827b2b01acc16f0acf3bd13fcfc315ad851c406822dc3242a0b18d3",
              "missing": false,
              "previous_observed_at": "2026-10-05T19:00:00+00:00"
            },
            {
              "input_type": "mandate",
              "input_id": "urn:cognous:issuance:1",
              "expected": {},
              "observed": {
                "observed_at": "2026-10-05T19:00:00+00:00"
              },
              "record_commitment": "sha256:d023eb722343620d7b2d4e622e0283008d72c903ef81c15d9b3dbaada7648091",
              "missing": false,
              "previous_observed_at": "2026-10-05T19:00:00+00:00"
            },
            {
              "input_type": "grant",
              "input_id": "urn:cognous:grant:routine-1",
              "expected": {
                "revision": "1",
                "status": "active"
              },
              "observed": {
                "revision": "1",
                "status": "active",
                "version": "status-v1",
                "observed_at": "2026-10-05T19:00:00+00:00"
              },
              "record_commitment": "sha256:eded76117318d91618259e7ed8eced201b868bb5f714d49fbf751535a6b8a859",
              "missing": false,
              "previous_observed_at": "2026-10-05T19:00:00+00:00"
            },
            {
              "input_type": "conflict",
              "input_id": "urn:cognous:authority-requirement:refund-routine-v1",
              "expected": {},
              "observed": {
                "state": "clear",
                "observed_at": "2026-10-05T19:00:00+00:00"
              },
              "record_commitment": "sha256:b469c2e823a75ebd9ba5b0f315c1a092e9ef8d257e684f03a9c00765a065e2ec",
              "missing": false,
              "previous_observed_at": "2026-10-05T19:00:00+00:00"
            },
            {
              "input_type": "policy",
              "input_id": "urn:cognous:policy:refund-policy",
              "expected": {
                "version": "1.0",
                "status": "active"
              },
              "observed": {
                "status": "active",
                "version": "1.0",
                "observed_at": "2026-10-05T19:00:00+00:00"
              },
              "record_commitment": "sha256:ff1302d24b132d1ccb1345ca47ecd25be2200335621ca133e01f54c384007e30",
              "missing": false,
              "previous_observed_at": "2026-10-05T19:00:00+00:00"
            },
            {
              "input_type": "approval",
              "input_id": "urn:cognous:approval:t1-1",
              "expected": {
                "grant_revision": "1",
                "status": "active",
                "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                "grant_id": "urn:cognous:grant:routine-1"
              },
              "observed": {
                "status": "active",
                "observed_at": "2026-10-05T19:00:00+00:00",
                "grant_revision": "1",
                "runtime_authority_commitment": "sha256:ebd9bfb69fb2894a63291d67fbc9fe07f58eb2f320f48286f7b6a003d2adfe86",
                "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                "grant_id": "urn:cognous:grant:routine-1"
              },
              "record_commitment": "sha256:373729df30fd57ccf14073ac25b970c15d0303da8e39ae39474d67e72542dbad",
              "missing": false,
              "previous_observed_at": "2026-10-05T19:00:00+00:00"
            },
            {
              "input_type": "evidence",
              "input_id": "urn:cognous:evidence:refund-entitlement",
              "expected": {
                "state": "current"
              },
              "observed": {
                "state": "current",
                "observed_at": "2026-10-05T19:00:00+00:00"
              },
              "record_commitment": "sha256:41ac78e62c85e85b6ba4dd94a60a430c4cdb94cbcf1a51a42a3850b61def1d4f",
              "missing": false,
              "previous_observed_at": "2026-10-05T19:00:00+00:00"
            },
            {
              "input_type": "evidence",
              "input_id": "urn:cognous:evidence:optional-context",
              "expected": {},
              "observed": {
                "state": "unknown",
                "observed_at": "2026-10-05T19:00:00+00:00"
              },
              "record_commitment": "sha256:9918ca9a4e1da9eee69322d6c0b107f215773957e569ee85e5ca1abb94c267cd",
              "missing": false,
              "previous_observed_at": "2026-10-05T19:00:00+00:00"
            },
            {
              "input_type": "purpose",
              "input_id": "sha256:6408c3a34b12a6f20f3bb978552aa9412812d9e366d53a8a27bc9ea7ea28da9b",
              "expected": {},
              "observed": {
                "state": "closed",
                "observed_at": "2026-10-05T19:00:00+00:00",
                "epoch": "epoch-1",
                "epoch_capability": "authoritative"
              },
              "record_commitment": "sha256:0bddd392557c3bcacb9075e1559633c7cd0fd9011349a00105b842c04fbf0f8d",
              "missing": false,
              "previous_observed_at": "2026-10-05T19:00:00+00:00"
            }
          ]
        }
      }
    ],
    "execution_result": [
      {
        "status": "denied",
        "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "attempt_id": null,
        "attempted": false,
        "acknowledged": false,
        "observed_state": "unknown",
        "newly_executed": false,
        "observation": null,
        "error": "authorization-critical inputs changed before effect",
        "control_plane_evidence": {
          "failure_record_id": "e7036bc4-f794-460a-80f5-b2ed3bde14a8",
          "refusal": {
            "reason_vocabulary_version": "runtime-authority-reasons/0.1",
            "refusal_id": "614005f1-545a-4b5c-b1f3-43241683e304",
            "decision_id": "e424616d-cfeb-483a-86c4-e263f92142a7",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "time_source": "test_override",
            "original_operation_horizon": {
              "source": "runtime_proposal",
              "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
              "not_before": null,
              "expires_at": null
            },
            "operation_horizon": {
              "source": "runtime_proposal",
              "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
              "not_before": null,
              "expires_at": null
            },
            "stage": "effect_time_revalidation",
            "reasons": [
              "purpose_closed"
            ],
            "changed_inputs": [],
            "resolution_inputs": [
              {
                "input_type": "manifest",
                "input_id": "refund-integration-pilot-v1",
                "expected": {},
                "observed": {},
                "record_commitment": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "authority_context",
                "input_id": "urn:cognous:alvorada:public-stack-profile:0.1.0",
                "expected": {},
                "observed": {
                  "schema_version": "0.1.0",
                  "interface_status": "proposed_pending_governor_review"
                },
                "record_commitment": "sha256:b0727efe67e8d7c656d48a20129dea61621acf99cda8371c67ab550d4caca342",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "role_mapping",
                "input_id": "urn:cognous:institution:synthetic-customer-service",
                "expected": {},
                "observed": {
                  "version": "roles-v1",
                  "digest": "sha256:f8a8db156df7087ddf34be1ed77fc86fa20ba7668deb87a9b3a5bd0a6ace496d"
                },
                "record_commitment": "sha256:fc884333b0da586ae781c0c4289729465659c719c0e4602758ddbf7a2bdcb89e",
                "missing": false,
                "previous_observed_at": null
              },
              {
                "input_type": "identity",
                "input_id": "urn:cognous:identity:refund-agent-1",
                "expected": {},
                "observed": {
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:5eee426c0827b2b01acc16f0acf3bd13fcfc315ad851c406822dc3242a0b18d3",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              },
              {
                "input_type": "mandate",
                "input_id": "urn:cognous:issuance:1",
                "expected": {},
                "observed": {
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:d023eb722343620d7b2d4e622e0283008d72c903ef81c15d9b3dbaada7648091",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              },
              {
                "input_type": "grant",
                "input_id": "urn:cognous:grant:routine-1",
                "expected": {
                  "revision": "1",
                  "status": "active"
                },
                "observed": {
                  "revision": "1",
                  "status": "active",
                  "version": "status-v1",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:eded76117318d91618259e7ed8eced201b868bb5f714d49fbf751535a6b8a859",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              },
              {
                "input_type": "conflict",
                "input_id": "urn:cognous:authority-requirement:refund-routine-v1",
                "expected": {},
                "observed": {
                  "state": "clear",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:b469c2e823a75ebd9ba5b0f315c1a092e9ef8d257e684f03a9c00765a065e2ec",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              },
              {
                "input_type": "policy",
                "input_id": "urn:cognous:policy:refund-policy",
                "expected": {
                  "version": "1.0",
                  "status": "active"
                },
                "observed": {
                  "status": "active",
                  "version": "1.0",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:ff1302d24b132d1ccb1345ca47ecd25be2200335621ca133e01f54c384007e30",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              },
              {
                "input_type": "approval",
                "input_id": "urn:cognous:approval:t1-1",
                "expected": {
                  "grant_revision": "1",
                  "status": "active",
                  "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                  "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                  "grant_id": "urn:cognous:grant:routine-1"
                },
                "observed": {
                  "status": "active",
                  "observed_at": "2026-10-05T19:00:00+00:00",
                  "grant_revision": "1",
                  "runtime_authority_commitment": "sha256:ebd9bfb69fb2894a63291d67fbc9fe07f58eb2f320f48286f7b6a003d2adfe86",
                  "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                  "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                  "grant_id": "urn:cognous:grant:routine-1"
                },
                "record_commitment": "sha256:373729df30fd57ccf14073ac25b970c15d0303da8e39ae39474d67e72542dbad",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              },
              {
                "input_type": "evidence",
                "input_id": "urn:cognous:evidence:refund-entitlement",
                "expected": {
                  "state": "current"
                },
                "observed": {
                  "state": "current",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:41ac78e62c85e85b6ba4dd94a60a430c4cdb94cbcf1a51a42a3850b61def1d4f",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              },
              {
                "input_type": "evidence",
                "input_id": "urn:cognous:evidence:optional-context",
                "expected": {},
                "observed": {
                  "state": "unknown",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:9918ca9a4e1da9eee69322d6c0b107f215773957e569ee85e5ca1abb94c267cd",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              },
              {
                "input_type": "purpose",
                "input_id": "sha256:6408c3a34b12a6f20f3bb978552aa9412812d9e366d53a8a27bc9ea7ea28da9b",
                "expected": {},
                "observed": {
                  "state": "closed",
                  "observed_at": "2026-10-05T19:00:00+00:00",
                  "epoch": "epoch-1",
                  "epoch_capability": "authoritative"
                },
                "record_commitment": "sha256:0bddd392557c3bcacb9075e1559633c7cd0fd9011349a00105b842c04fbf0f8d",
                "missing": false,
                "previous_observed_at": "2026-10-05T19:00:00+00:00"
              }
            ]
          }
        }
      }
    ]
  },
  "explicit_links": [],
  "reconstruction_completeness": "reconstruction_complete",
  "refusal_vocabulary_summary": {
    "total_refusals": 1,
    "series": [
      {
        "version": "runtime-authority-reasons/0.1",
        "code": "purpose_closed",
        "count": 1,
        "share": 1.0
      }
    ],
    "prior_window": "unavailable",
    "disappearance_assessed": false,
    "limitation": "source-record counts; exposure and collection completeness not independently established"
  }
}</pre>
