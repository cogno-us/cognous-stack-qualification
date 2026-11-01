# Traceable Agent Governance Evidence Pack

| Field | Value |
|---|---|
| Pack ID | agep-14d9636144e3934a |
| Version | 0.2.0 |
| Generated At | 2026-10-16T19:39:28.164674+00:00 |
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
| 6ec9c989-f663-4c45-b059-5d73af665e28 | run-1 | validated_complete | 2026-10-16T19:39:28.164674+00:00 | No | No | semantically_valid | metadata.traceable_import.source_record_refs |

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
| manifest | refund-integration-pilot-v1 | 1.1 | sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac | 2c36bcd0b620dbfe7ad924bc7196a3f0c04c5c5e | digest_and_cross_artifact_binding_checked_when_runtime_proposal_present |
| reconstruction_bundle | 6ec9c989-f663-4c45-b059-5d73af665e28 | 0.2.0 | sha256:2dead267292191946d3aa7536cc47b39800cb89792e5ded2fe0971e3a9749078 | 79ba16d48b9be1e059b3045989c7df960c3df1c2 | validated_complete |

### Transformation

| Field | Value |
|---|---|
| Transformation Version | agep-manifest-reconstruction-import/0.3.6-security-runtime-f5b-candidate |
| Canonicalization Profile | json-sort-keys-compact-utf8-no-nan |

### Selected producer revisions

| Component | Selected Revision |
|---|---|
| manifest | 2c36bcd0b620dbfe7ad924bc7196a3f0c04c5c5e |
| replay | 79ba16d48b9be1e059b3045989c7df960c3df1c2 |
| control_plane | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 |
| moltbot_safe | e20f92e104aba2ba6ad06120d8549c6170eaf63f |

### Supported producer revision sets

| Component | Supported Revisions |
|---|---|
| manifest | 2c36bcd0b620dbfe7ad924bc7196a3f0c04c5c5e |
| replay | 79ba16d48b9be1e059b3045989c7df960c3df1c2 |
| control_plane | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 |
| moltbot_safe | e20f92e104aba2ba6ad06120d8549c6170eaf63f |

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
| control-plane-security-runtime@a34c3dc2 | cogno-us/cognous-agent-control-plane | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | — | declared_revision_matches_accepted_pin | not_performed |
| moltbot-safe-executor-producer-2.0.0@e20f92e1 | cogno-us/moltbot-safe | e20f92e104aba2ba6ad06120d8549c6170eaf63f | 2.0.0 | declared_revision_matches_accepted_pin | not_performed |

### Executor producer contract

| Field | Value |
|---|---|
| interface_profile_id | urn:cognous:profiles:moltbot-safe-executor-producer |
| interface_profile_version | 2.0.0 |
| repository_revision | e20f92e104aba2ba6ad06120d8549c6170eaf63f |
| legacy | False |
| source_asserted_repository_revision | e20f92e104aba2ba6ad06120d8549c6170eaf63f |
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
| control-plane-security-runtime@a34c3dc2:runtime_proposal:0 | runtime_proposal | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | proposal |
| control-plane-security-runtime@a34c3dc2:runtime_decision:1 | runtime_decision | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | decisions&#91;0&#93; |
| control-plane-security-runtime@a34c3dc2:effect_time_refusal:2 | effect_time_refusal | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | refusals&#91;0&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check:3 | resolution_check | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | resolution_checks&#91;0&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check:4 | resolution_check | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | resolution_checks&#91;1&#93; |
| control-plane-security-runtime@a34c3dc2:input_time_floors:5 | input_time_floors | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | input_time_floors |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:6 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;0&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:7 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;1&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:8 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;2&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:9 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;3&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:10 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;4&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:11 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;5&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:12 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;6&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:13 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;7&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:14 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;8&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:15 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;9&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:16 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;10&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:17 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;11&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:18 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;12&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:19 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;13&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:20 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;14&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:21 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;15&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:22 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;16&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:23 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;17&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:24 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;18&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:25 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;19&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:26 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;20&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:27 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;21&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:28 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;22&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:29 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;23&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:30 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;24&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:31 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;25&#93; |
| moltbot-safe-executor-producer-2.0.0@e20f92e1:execution_envelope:32 | execution_envelope | moltbot-safe-executor-producer-2.0.0@e20f92e1 | producer_reported | e20f92e104aba2ba6ad06120d8549c6170eaf63f | declared_revision_matches_accepted_pin | moltbot.execution_envelope |
| moltbot-safe-executor-producer-2.0.0@e20f92e1:executor_control_plane_evidence:33 | executor_control_plane_evidence | moltbot-safe-executor-producer-2.0.0@e20f92e1 | producer_reported | e20f92e104aba2ba6ad06120d8549c6170eaf63f | declared_revision_matches_accepted_pin | moltbot.control_plane_evidence |
| moltbot-safe-executor-producer-2.0.0@e20f92e1:execution_result:34 | execution_result | moltbot-safe-executor-producer-2.0.0@e20f92e1 | producer_reported | e20f92e104aba2ba6ad06120d8549c6170eaf63f | declared_revision_matches_accepted_pin | moltbot.execution_result |

### Source-supplied commitments

| Record ID | Label | Commitment | Algorithm | Canonicalization | Source Verification Status | Source Path |
|---|---|---|---|---|---|---|
| control-plane-security-runtime@a34c3dc2:runtime_proposal:0 | payload_commitment | sha256:6b782ebbcc034edeca4069b31aa4d8cbc9d3eeaf3b2034ab989bb430de962c0e | SHA-256 | json-sort-keys-compact-utf8-no-nan | checked_match | proposal.payload_commitment |
| control-plane-security-runtime@a34c3dc2:runtime_decision:1 | effect_id | sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829 | SHA-256 | json-sort-keys-compact-utf8-no-nan | checked_match | decisions&#91;0&#93;.effect_id |
| control-plane-security-runtime@a34c3dc2:runtime_decision:1 | proposal_commitment | sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b | SHA-256 | json-sort-keys-compact-utf8-no-nan | attributed_claim | decisions&#91;0&#93;.binding.proposal_commitment |
| control-plane-security-runtime@a34c3dc2:runtime_decision:1 | manifest_digest | sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac | SHA-256 | json-sort-keys-compact-utf8-no-nan | attributed_claim | decisions&#91;0&#93;.binding.manifest_digest |
| control-plane-security-runtime@a34c3dc2:runtime_decision:1 | payload_commitment | sha256:6b782ebbcc034edeca4069b31aa4d8cbc9d3eeaf3b2034ab989bb430de962c0e | SHA-256 | json-sort-keys-compact-utf8-no-nan | attributed_claim | decisions&#91;0&#93;.binding.payload_commitment |
| control-plane-security-runtime@a34c3dc2:runtime_decision:1 | requirement_commitment | sha256:6590406e701b51e637c87953860d1ceb72d8da0af87311048f152e0ee2b8ccb6 | SHA-256 | json-sort-keys-compact-utf8-no-nan | attributed_claim | decisions&#91;0&#93;.binding.requirement_commitment |
| control-plane-security-runtime@a34c3dc2:runtime_decision:1 | role_mapping_digest | sha256:f8a8db156df7087ddf34be1ed77fc86fa20ba7668deb87a9b3a5bd0a6ace496d | SHA-256 | json-sort-keys-compact-utf8-no-nan | attributed_claim | decisions&#91;0&#93;.binding.role_mapping_digest |
| moltbot-safe-executor-producer-2.0.0@e20f92e1:execution_envelope:32 | payload_commitment | sha256:6b782ebbcc034edeca4069b31aa4d8cbc9d3eeaf3b2034ab989bb430de962c0e | SHA-256 | json-sort-keys-compact-utf8-no-nan | checked_match | moltbot.execution_envelope.operation.payload_commitment |

### Locally computed record commitments

| Record ID | Local Commitment | Compatibility Hash Alias | Canonicalization | Verification Status |
|---|---|---|---|---|
| control-plane-security-runtime@a34c3dc2:runtime_proposal:0 | sha256:f571d7c4baf2f994443a25dc6c621514836d71e655a80c63f0a86445b518b6c8 | sha256:f571d7c4baf2f994443a25dc6c621514836d71e655a80c63f0a86445b518b6c8 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:runtime_decision:1 | sha256:c2586f99d7e7fccc88439dab145d27efe2239ee78bded2835e0b8ec588835ea5 | sha256:c2586f99d7e7fccc88439dab145d27efe2239ee78bded2835e0b8ec588835ea5 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:effect_time_refusal:2 | sha256:7a05974f4d0a11e2102c06a267749eefcebec901f2b8dca98d33c2eba1755686 | sha256:7a05974f4d0a11e2102c06a267749eefcebec901f2b8dca98d33c2eba1755686 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check:3 | sha256:06e41c3dfc71243fe9b6ba3039ffa20c89e5b6505cb38ef864db28a67538eebc | sha256:06e41c3dfc71243fe9b6ba3039ffa20c89e5b6505cb38ef864db28a67538eebc | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check:4 | sha256:59da720685523d206f5cfcc0fb9b027b1dad8be66e490800af715053188536d8 | sha256:59da720685523d206f5cfcc0fb9b027b1dad8be66e490800af715053188536d8 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:input_time_floors:5 | sha256:498bdc6bee29d27b43b9a5620c612e2a7c73d21b3d654e8a4c4c84d9c7dda4b5 | sha256:498bdc6bee29d27b43b9a5620c612e2a7c73d21b3d654e8a4c4c84d9c7dda4b5 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:6 | sha256:300ce09db446cffeeb239129abc0447b2609c71c3891f4a5b7bad89f6fc84738 | sha256:300ce09db446cffeeb239129abc0447b2609c71c3891f4a5b7bad89f6fc84738 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:7 | sha256:dd88749ed90b68aa99301704c4a90abf862e59a79c19a31b67ae6ef7d8d0fa7f | sha256:dd88749ed90b68aa99301704c4a90abf862e59a79c19a31b67ae6ef7d8d0fa7f | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:8 | sha256:743b447c036350742b50c3bdfad99c2ddb2abca063559cc19476ac9d5b628e21 | sha256:743b447c036350742b50c3bdfad99c2ddb2abca063559cc19476ac9d5b628e21 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:9 | sha256:d790b8516fc6e727439c5309a77ec31bf41259e4ac55a7c48c641519404d731b | sha256:d790b8516fc6e727439c5309a77ec31bf41259e4ac55a7c48c641519404d731b | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:10 | sha256:c80b819730cf20ea6d94bb36f75df481862669904113e79fdb1a38232737adf9 | sha256:c80b819730cf20ea6d94bb36f75df481862669904113e79fdb1a38232737adf9 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:11 | sha256:c90fbd56c012aac66a6ed78b279b93f25c11c12db938a6260f3fba328d5749ce | sha256:c90fbd56c012aac66a6ed78b279b93f25c11c12db938a6260f3fba328d5749ce | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:12 | sha256:c7e87551d77df957e8f46bca9791b09f3135459f7d2854cfe1ad425aaaecf139 | sha256:c7e87551d77df957e8f46bca9791b09f3135459f7d2854cfe1ad425aaaecf139 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:13 | sha256:7f93cb772909003d42af6c9b7143b759d57e3a1eeb8e3b56d268cbe536b6bf97 | sha256:7f93cb772909003d42af6c9b7143b759d57e3a1eeb8e3b56d268cbe536b6bf97 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:14 | sha256:63a01a40cef22fd943a85c59a58eef0fadf26fbc7ef548fac1e1faf18d5f4e33 | sha256:63a01a40cef22fd943a85c59a58eef0fadf26fbc7ef548fac1e1faf18d5f4e33 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:15 | sha256:d869841e872b51e320c24d4a3ce499d704dc44e304d305f942e9a62acd41964e | sha256:d869841e872b51e320c24d4a3ce499d704dc44e304d305f942e9a62acd41964e | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:16 | sha256:609937008ec50e7dd460e2c5d140cc9ec6b45e866330dd12f2ef86984f4598b2 | sha256:609937008ec50e7dd460e2c5d140cc9ec6b45e866330dd12f2ef86984f4598b2 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:17 | sha256:293d70c1c4a5842fd69bf9c895e160b53be7d4ced3cfcf79e1184e27f3cc405e | sha256:293d70c1c4a5842fd69bf9c895e160b53be7d4ced3cfcf79e1184e27f3cc405e | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:18 | sha256:37466fdb464131d0175524e1e0492530ecafb7c82359ebe9a79274985f35b8ad | sha256:37466fdb464131d0175524e1e0492530ecafb7c82359ebe9a79274985f35b8ad | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:19 | sha256:2cf6137321a2e146353bfc8f92b7168395a4a9467aaeb77cc3b2e5c8d31b39b4 | sha256:2cf6137321a2e146353bfc8f92b7168395a4a9467aaeb77cc3b2e5c8d31b39b4 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:20 | sha256:ec780b5db1fab1e5a7b27de44cd69d7482071394cb5bbb93682bda3e714f39e0 | sha256:ec780b5db1fab1e5a7b27de44cd69d7482071394cb5bbb93682bda3e714f39e0 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:21 | sha256:52922ad9a340ff37002567e4fda064471944f53410c7c59ea9b87e8460cfb051 | sha256:52922ad9a340ff37002567e4fda064471944f53410c7c59ea9b87e8460cfb051 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:22 | sha256:30178370522de94f68c702a33fb3f309659dfbb5a5b8ab871d2f66d6e9324aa2 | sha256:30178370522de94f68c702a33fb3f309659dfbb5a5b8ab871d2f66d6e9324aa2 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:23 | sha256:fee18641a5a8a9710cee87b3301d43eb33148d40d97a7330c27be2a5520dc950 | sha256:fee18641a5a8a9710cee87b3301d43eb33148d40d97a7330c27be2a5520dc950 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:24 | sha256:05b58596354c7b37b02ace1ce382ea6b2e57d36244786a3584a4250e36bc534a | sha256:05b58596354c7b37b02ace1ce382ea6b2e57d36244786a3584a4250e36bc534a | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:25 | sha256:637b873716bc6f3aa66c477b7a0d68849ffe352ffba284326117a8ce830264c2 | sha256:637b873716bc6f3aa66c477b7a0d68849ffe352ffba284326117a8ce830264c2 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:26 | sha256:3a8f9f666037867eadaa2af544f52005a0b56fb4e2ba9bc0db06f971ff4efbef | sha256:3a8f9f666037867eadaa2af544f52005a0b56fb4e2ba9bc0db06f971ff4efbef | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:27 | sha256:0ea52806f0ec771f4de60a187800de720cc645573b8abcba4ae77a0e635ffd7e | sha256:0ea52806f0ec771f4de60a187800de720cc645573b8abcba4ae77a0e635ffd7e | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:28 | sha256:66e7d9b335d90321bac21ae50305484ae5222b4bf2871bc737791665537a3f7a | sha256:66e7d9b335d90321bac21ae50305484ae5222b4bf2871bc737791665537a3f7a | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:29 | sha256:b9b731eff7b8b4c76af5582528d759465161329f00ca8c806ff93218014cc9b0 | sha256:b9b731eff7b8b4c76af5582528d759465161329f00ca8c806ff93218014cc9b0 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:30 | sha256:ee4dd5d8c8adedb97ecaf59c1502ae0da27e6ca74df61efc1100e549444fa2c4 | sha256:ee4dd5d8c8adedb97ecaf59c1502ae0da27e6ca74df61efc1100e549444fa2c4 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:31 | sha256:3c1b94789e14d79bd0f01cc9a2865ec8ecf99b54ffb93e94fed8e530756c28d2 | sha256:3c1b94789e14d79bd0f01cc9a2865ec8ecf99b54ffb93e94fed8e530756c28d2 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| moltbot-safe-executor-producer-2.0.0@e20f92e1:execution_envelope:32 | sha256:0fb25114467cdff7eea44b45d9553a79778271210f9772cba928bcac5e711473 | sha256:0fb25114467cdff7eea44b45d9553a79778271210f9772cba928bcac5e711473 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| moltbot-safe-executor-producer-2.0.0@e20f92e1:executor_control_plane_evidence:33 | sha256:c7a741221a1c1a188cfc299dbdc93d4e8baa3f13a78b4459769adbb0d697b664 | sha256:c7a741221a1c1a188cfc299dbdc93d4e8baa3f13a78b4459769adbb0d697b664 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| moltbot-safe-executor-producer-2.0.0@e20f92e1:execution_result:34 | sha256:1f94d6a768bff213d766cddcf25a0ea892062b4fa89a2294eafea299cad9f19a | sha256:1f94d6a768bff213d766cddcf25a0ea892062b4fa89a2294eafea299cad9f19a | json-sort-keys-compact-utf8-no-nan | computed_during_import |

Source evidence classes and source verification statuses are retained as producer/source assertions. They are not the importer’s independent assurance or verification.

### Complete material trace (escaped JSON)

The following is the complete trace metadata without truncation. Null observations, rejected content, historical states, policy/evaluation metadata and original sources remain distinct. Rejected evidence is not accepted lineage. No retry or current authority is established.

<pre>{
  "transformation_version": "agep-manifest-reconstruction-import/0.3.6-security-runtime-f5b-candidate",
  "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
  "supported_revisions": {
    "manifest": "2c36bcd0b620dbfe7ad924bc7196a3f0c04c5c5e",
    "replay": "79ba16d48b9be1e059b3045989c7df960c3df1c2",
    "control_plane": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
    "moltbot_safe": "e20f92e104aba2ba6ad06120d8549c6170eaf63f",
    "odes": "cba83a1c06f718a8afd76178f36e5cc15896347d",
    "gax_imx_experimental_reference": "6bcde026a804c7377f5e39f57ca6dd00b3c3292d",
    "gax_imx_acceptance_status": "provisional_experimental_dependency",
    "alvorada": "fb3d97938969a89e149e8ff8db2756091d1233fc"
  },
  "replay_semantic_validation": {
    "validator": "agent_replay_bundle.importers.import_bounded_workflow",
    "required_revision": "79ba16d48b9be1e059b3045989c7df960c3df1c2",
    "status": "validated_complete"
  },
  "replay_import_reports": [
    {
      "adapter_profile": "control-plane-security-runtime@a34c3dc2",
      "source_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
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
      "trusted_revision": "2c36bcd0b620dbfe7ad924bc7196a3f0c04c5c5e",
      "verification_status": "digest_and_cross_artifact_binding_checked_when_runtime_proposal_present",
      "commitment_source": "locally_computed",
      "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan"
    },
    {
      "artifact_role": "reconstruction_bundle",
      "artifact_id": "6ec9c989-f663-4c45-b059-5d73af665e28",
      "version": "0.2.0",
      "hash": "sha256:2dead267292191946d3aa7536cc47b39800cb89792e5ded2fe0971e3a9749078",
      "trusted_revision": "79ba16d48b9be1e059b3045989c7df960c3df1c2",
      "verification_status": "validated_complete",
      "commitment_source": "locally_computed",
      "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan"
    }
  ],
  "producer_profiles": [
    {
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "producer": "Cognous Agent Control Plane",
      "repository": "cogno-us/cognous-agent-control-plane",
      "revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "format_version": null,
      "revision_check": "declared_revision_matches_accepted_pin",
      "provenance_status": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "format_name": "BoundedRunRecord",
      "schema_ref": null,
      "notes": "No embedded format version; adapter is revision-pinned."
    },
    {
      "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1",
      "producer": "Moltbot Safe",
      "repository": "cogno-us/moltbot-safe",
      "revision": "e20f92e104aba2ba6ad06120d8549c6170eaf63f",
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
    "profile_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1",
    "control_plane_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
    "compatible_control_plane_revisions": [
      "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5"
    ],
    "repository_revision": "e20f92e104aba2ba6ad06120d8549c6170eaf63f",
    "interface_profile_id": "urn:cognous:profiles:moltbot-safe-executor-producer",
    "interface_profile_version": "2.0.0",
    "provenance": {
      "mode": "versioned_profile",
      "source_asserted": {
        "repository_revision": "e20f92e104aba2ba6ad06120d8549c6170eaf63f",
        "producer_profile_id": "urn:cognous:profiles:moltbot-safe-executor-producer",
        "producer_profile_version": "2.0.0"
      },
      "independently_established": []
    },
    "legacy": false
  },
  "source_record_refs": [
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:runtime_proposal:0",
      "record_type": "runtime_proposal",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "proposal",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
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
      "local_content_commitment": "sha256:f571d7c4baf2f994443a25dc6c621514836d71e655a80c63f0a86445b518b6c8",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:f571d7c4baf2f994443a25dc6c621514836d71e655a80c63f0a86445b518b6c8"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:runtime_decision:1",
      "record_type": "runtime_decision",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "decisions[0]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
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
      "local_content_commitment": "sha256:c2586f99d7e7fccc88439dab145d27efe2239ee78bded2835e0b8ec588835ea5",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:c2586f99d7e7fccc88439dab145d27efe2239ee78bded2835e0b8ec588835ea5"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:effect_time_refusal:2",
      "record_type": "effect_time_refusal",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "refusals[0]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:7a05974f4d0a11e2102c06a267749eefcebec901f2b8dca98d33c2eba1755686",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:7a05974f4d0a11e2102c06a267749eefcebec901f2b8dca98d33c2eba1755686"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check:3",
      "record_type": "resolution_check",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "resolution_checks[0]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:06e41c3dfc71243fe9b6ba3039ffa20c89e5b6505cb38ef864db28a67538eebc",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:06e41c3dfc71243fe9b6ba3039ffa20c89e5b6505cb38ef864db28a67538eebc"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check:4",
      "record_type": "resolution_check",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "resolution_checks[1]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:59da720685523d206f5cfcc0fb9b027b1dad8be66e490800af715053188536d8",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:59da720685523d206f5cfcc0fb9b027b1dad8be66e490800af715053188536d8"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:input_time_floors:5",
      "record_type": "input_time_floors",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "input_time_floors",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:498bdc6bee29d27b43b9a5620c612e2a7c73d21b3d654e8a4c4c84d9c7dda4b5",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:498bdc6bee29d27b43b9a5620c612e2a7c73d21b3d654e8a4c4c84d9c7dda4b5"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:6",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[0]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:300ce09db446cffeeb239129abc0447b2609c71c3891f4a5b7bad89f6fc84738",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:300ce09db446cffeeb239129abc0447b2609c71c3891f4a5b7bad89f6fc84738"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:7",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[1]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:dd88749ed90b68aa99301704c4a90abf862e59a79c19a31b67ae6ef7d8d0fa7f",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:dd88749ed90b68aa99301704c4a90abf862e59a79c19a31b67ae6ef7d8d0fa7f"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:8",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[2]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:743b447c036350742b50c3bdfad99c2ddb2abca063559cc19476ac9d5b628e21",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:743b447c036350742b50c3bdfad99c2ddb2abca063559cc19476ac9d5b628e21"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:9",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[3]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:d790b8516fc6e727439c5309a77ec31bf41259e4ac55a7c48c641519404d731b",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:d790b8516fc6e727439c5309a77ec31bf41259e4ac55a7c48c641519404d731b"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:10",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[4]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:c80b819730cf20ea6d94bb36f75df481862669904113e79fdb1a38232737adf9",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:c80b819730cf20ea6d94bb36f75df481862669904113e79fdb1a38232737adf9"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:11",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[5]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:c90fbd56c012aac66a6ed78b279b93f25c11c12db938a6260f3fba328d5749ce",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:c90fbd56c012aac66a6ed78b279b93f25c11c12db938a6260f3fba328d5749ce"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:12",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[6]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:c7e87551d77df957e8f46bca9791b09f3135459f7d2854cfe1ad425aaaecf139",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:c7e87551d77df957e8f46bca9791b09f3135459f7d2854cfe1ad425aaaecf139"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:13",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[7]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:7f93cb772909003d42af6c9b7143b759d57e3a1eeb8e3b56d268cbe536b6bf97",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:7f93cb772909003d42af6c9b7143b759d57e3a1eeb8e3b56d268cbe536b6bf97"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:14",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[8]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:63a01a40cef22fd943a85c59a58eef0fadf26fbc7ef548fac1e1faf18d5f4e33",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:63a01a40cef22fd943a85c59a58eef0fadf26fbc7ef548fac1e1faf18d5f4e33"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:15",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[9]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:d869841e872b51e320c24d4a3ce499d704dc44e304d305f942e9a62acd41964e",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:d869841e872b51e320c24d4a3ce499d704dc44e304d305f942e9a62acd41964e"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:16",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[10]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:609937008ec50e7dd460e2c5d140cc9ec6b45e866330dd12f2ef86984f4598b2",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:609937008ec50e7dd460e2c5d140cc9ec6b45e866330dd12f2ef86984f4598b2"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:17",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[11]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:293d70c1c4a5842fd69bf9c895e160b53be7d4ced3cfcf79e1184e27f3cc405e",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:293d70c1c4a5842fd69bf9c895e160b53be7d4ced3cfcf79e1184e27f3cc405e"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:18",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[12]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:37466fdb464131d0175524e1e0492530ecafb7c82359ebe9a79274985f35b8ad",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:37466fdb464131d0175524e1e0492530ecafb7c82359ebe9a79274985f35b8ad"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:19",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[13]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:2cf6137321a2e146353bfc8f92b7168395a4a9467aaeb77cc3b2e5c8d31b39b4",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:2cf6137321a2e146353bfc8f92b7168395a4a9467aaeb77cc3b2e5c8d31b39b4"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:20",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[14]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:ec780b5db1fab1e5a7b27de44cd69d7482071394cb5bbb93682bda3e714f39e0",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:ec780b5db1fab1e5a7b27de44cd69d7482071394cb5bbb93682bda3e714f39e0"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:21",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[15]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:52922ad9a340ff37002567e4fda064471944f53410c7c59ea9b87e8460cfb051",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:52922ad9a340ff37002567e4fda064471944f53410c7c59ea9b87e8460cfb051"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:22",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[16]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:30178370522de94f68c702a33fb3f309659dfbb5a5b8ab871d2f66d6e9324aa2",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:30178370522de94f68c702a33fb3f309659dfbb5a5b8ab871d2f66d6e9324aa2"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:23",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[17]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:fee18641a5a8a9710cee87b3301d43eb33148d40d97a7330c27be2a5520dc950",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:fee18641a5a8a9710cee87b3301d43eb33148d40d97a7330c27be2a5520dc950"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:24",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[18]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:05b58596354c7b37b02ace1ce382ea6b2e57d36244786a3584a4250e36bc534a",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:05b58596354c7b37b02ace1ce382ea6b2e57d36244786a3584a4250e36bc534a"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:25",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[19]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:637b873716bc6f3aa66c477b7a0d68849ffe352ffba284326117a8ce830264c2",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:637b873716bc6f3aa66c477b7a0d68849ffe352ffba284326117a8ce830264c2"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:26",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[20]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:3a8f9f666037867eadaa2af544f52005a0b56fb4e2ba9bc0db06f971ff4efbef",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:3a8f9f666037867eadaa2af544f52005a0b56fb4e2ba9bc0db06f971ff4efbef"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:27",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[21]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:0ea52806f0ec771f4de60a187800de720cc645573b8abcba4ae77a0e635ffd7e",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:0ea52806f0ec771f4de60a187800de720cc645573b8abcba4ae77a0e635ffd7e"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:28",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[22]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:66e7d9b335d90321bac21ae50305484ae5222b4bf2871bc737791665537a3f7a",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:66e7d9b335d90321bac21ae50305484ae5222b4bf2871bc737791665537a3f7a"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:29",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[23]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:b9b731eff7b8b4c76af5582528d759465161329f00ca8c806ff93218014cc9b0",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:b9b731eff7b8b4c76af5582528d759465161329f00ca8c806ff93218014cc9b0"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:30",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[24]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:ee4dd5d8c8adedb97ecaf59c1502ae0da27e6ca74df61efc1100e549444fa2c4",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:ee4dd5d8c8adedb97ecaf59c1502ae0da27e6ca74df61efc1100e549444fa2c4"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:31",
      "record_type": "resolution_check_event",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "check_events[25]",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/cognous-agent-control-plane",
      "producer_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
      "producer_format_version": null,
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:3c1b94789e14d79bd0f01cc9a2865ec8ecf99b54ffb93e94fed8e530756c28d2",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:3c1b94789e14d79bd0f01cc9a2865ec8ecf99b54ffb93e94fed8e530756c28d2"
    },
    {
      "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:execution_envelope:32",
      "record_type": "execution_envelope",
      "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1",
      "source_path": "moltbot.execution_envelope",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/moltbot-safe",
      "producer_revision": "e20f92e104aba2ba6ad06120d8549c6170eaf63f",
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
      "local_content_commitment": "sha256:0fb25114467cdff7eea44b45d9553a79778271210f9772cba928bcac5e711473",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:0fb25114467cdff7eea44b45d9553a79778271210f9772cba928bcac5e711473"
    },
    {
      "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:executor_control_plane_evidence:33",
      "record_type": "executor_control_plane_evidence",
      "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1",
      "source_path": "moltbot.control_plane_evidence",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/moltbot-safe",
      "producer_revision": "e20f92e104aba2ba6ad06120d8549c6170eaf63f",
      "producer_format_version": "2.0.0",
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:c7a741221a1c1a188cfc299dbdc93d4e8baa3f13a78b4459769adbb0d697b664",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:c7a741221a1c1a188cfc299dbdc93d4e8baa3f13a78b4459769adbb0d697b664"
    },
    {
      "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:execution_result:34",
      "record_type": "execution_result",
      "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1",
      "source_path": "moltbot.execution_result",
      "evidence_class": "producer_reported",
      "evidence_class_status": "source_assertion",
      "producer_repository": "cogno-us/moltbot-safe",
      "producer_revision": "e20f92e104aba2ba6ad06120d8549c6170eaf63f",
      "producer_format_version": "2.0.0",
      "producer_revision_check": "declared_revision_matches_accepted_pin",
      "source_asserted_provenance": "source_asserted_and_contract_compared",
      "independent_provenance_verification": "not_performed",
      "source_commitments": [],
      "source_content_commitment": null,
      "source_canonicalization_profile": null,
      "source_commitment_verification_status": null,
      "local_content_commitment": "sha256:1f94d6a768bff213d766cddcf25a0ea892062b4fa89a2294eafea299cad9f19a",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:1f94d6a768bff213d766cddcf25a0ea892062b4fa89a2294eafea299cad9f19a"
    }
  ],
  "conversion_losses": [
    {
      "source": "replay_import_report",
      "report_index": 0,
      "finding_index": 0,
      "adapter_profile": "control-plane-security-runtime@a34c3dc2",
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
      "adapter_profile": "control-plane-security-runtime@a34c3dc2",
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
        "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:execution_result:34",
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
        "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:execution_result:34",
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
      "2c36bcd0b620dbfe7ad924bc7196a3f0c04c5c5e"
    ],
    "replay": [
      "79ba16d48b9be1e059b3045989c7df960c3df1c2"
    ],
    "control_plane": [
      "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5"
    ],
    "moltbot_safe": [
      "e20f92e104aba2ba6ad06120d8549c6170eaf63f"
    ]
  },
  "selected_revisions": {
    "manifest": "2c36bcd0b620dbfe7ad924bc7196a3f0c04c5c5e",
    "replay": "79ba16d48b9be1e059b3045989c7df960c3df1c2",
    "control_plane": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
    "moltbot_safe": "e20f92e104aba2ba6ad06120d8549c6170eaf63f"
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
      "bundle_id": "6ec9c989-f663-4c45-b059-5d73af665e28",
      "bundle_version": "0.2.0",
      "run_id": "run-1",
      "status": "reconstruction_complete",
      "generated_at": "2026-10-16T19:39:28.164674+00:00",
      "producer_profiles": [
        {
          "profile_id": "control-plane-security-runtime@a34c3dc2",
          "producer": "Cognous Agent Control Plane",
          "repository": "cogno-us/cognous-agent-control-plane",
          "revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
          "format_name": "BoundedRunRecord",
          "format_version": null,
          "schema_ref": null,
          "notes": "No embedded format version; adapter is revision-pinned."
        },
        {
          "profile_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1",
          "producer": "Moltbot Safe",
          "repository": "cogno-us/moltbot-safe",
          "revision": "e20f92e104aba2ba6ad06120d8549c6170eaf63f",
          "format_name": "Executor producer export",
          "format_version": "2.0.0",
          "schema_ref": null,
          "notes": "Versioned producer profile; repository provenance remains source-asserted unless separately established."
        }
      ],
      "records": [
        {
          "record_id": "control-plane-security-runtime@a34c3dc2:runtime_proposal:0",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
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
          "record_id": "control-plane-security-runtime@a34c3dc2:runtime_decision:1",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "runtime_decision",
          "source_sequence": 1,
          "source_path": "decisions[0]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
                "approval_commitment": "sha256:5f1cec7438ec4ad88f4fd9f6e3021706846fd8d6705972e12f4e0f06ac8e9497",
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
                "record_commitment": "sha256:f67908364e87a9397b3b6ef66c0d4360e4c785d7a6bdb357e74e164e755f983e",
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
                  "runtime_authority_commitment": "sha256:5f1cec7438ec4ad88f4fd9f6e3021706846fd8d6705972e12f4e0f06ac8e9497",
                  "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                  "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                  "grant_id": "urn:cognous:grant:routine-1"
                },
                "record_commitment": "sha256:865eb4d1713c75d401476e51dcbc507e634b00252c8314c3d3cc98586129deaa",
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
              }
            ]
          }
        },
        {
          "record_id": "control-plane-security-runtime@a34c3dc2:effect_time_refusal:2",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "effect_time_refusal",
          "source_sequence": 2,
          "source_path": "refusals[0]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "refusal_id": "4aec4784-cf57-47d6-a4c8-8115689756ed"
          },
          "evidence_class": "producer_reported",
          "data": {
            "reason_vocabulary_version": "runtime-authority-reasons/0.1",
            "reopen_conditions": [
              {
                "kind": "successor_grant_revision",
                "input_id": "urn:cognous:grant:routine-1",
                "previous_revision": "1"
              }
            ],
            "refusal_id": "4aec4784-cf57-47d6-a4c8-8115689756ed",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
              "grant_revoked"
            ],
            "changed_inputs": [
              {
                "input_type": "grant",
                "input_id": "urn:cognous:grant:routine-1",
                "expected_version": "revision=1;status=active",
                "observed_version": "revision=1;status=revoked;version=status-v1;observed_at=2026-10-05T19:00:00+00:00"
              }
            ],
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
                "record_commitment": "sha256:f67908364e87a9397b3b6ef66c0d4360e4c785d7a6bdb357e74e164e755f983e",
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
                  "status": "revoked",
                  "version": "status-v1",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:923e78ee4d0d6b571cb9dcd080f27719bc46f513f249ea9cca34aff494ebd900",
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
                  "runtime_authority_commitment": "sha256:5f1cec7438ec4ad88f4fd9f6e3021706846fd8d6705972e12f4e0f06ac8e9497",
                  "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                  "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                  "grant_id": "urn:cognous:grant:routine-1"
                },
                "record_commitment": "sha256:865eb4d1713c75d401476e51dcbc507e634b00252c8314c3d3cc98586129deaa",
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
              }
            ]
          }
        },
        {
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check:3",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check",
          "source_sequence": 3,
          "source_path": "resolution_checks[0]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "a7d71810-8b77-448b-b8ba-4234f0ab0f70"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "a7d71810-8b77-448b-b8ba-4234f0ab0f70",
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
                "record_commitment": "sha256:f67908364e87a9397b3b6ef66c0d4360e4c785d7a6bdb357e74e164e755f983e",
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
                  "runtime_authority_commitment": "sha256:5f1cec7438ec4ad88f4fd9f6e3021706846fd8d6705972e12f4e0f06ac8e9497",
                  "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                  "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                  "grant_id": "urn:cognous:grant:routine-1"
                },
                "record_commitment": "sha256:865eb4d1713c75d401476e51dcbc507e634b00252c8314c3d3cc98586129deaa",
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
              }
            ],
            "reasons": []
          }
        },
        {
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check:4",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check",
          "source_sequence": 4,
          "source_path": "resolution_checks[1]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "a4c65521-d803-44b8-a237-68fb2e695526"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "a4c65521-d803-44b8-a237-68fb2e695526",
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
                "record_commitment": "sha256:f67908364e87a9397b3b6ef66c0d4360e4c785d7a6bdb357e74e164e755f983e",
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
                  "status": "revoked",
                  "version": "status-v1",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:923e78ee4d0d6b571cb9dcd080f27719bc46f513f249ea9cca34aff494ebd900",
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
                  "runtime_authority_commitment": "sha256:5f1cec7438ec4ad88f4fd9f6e3021706846fd8d6705972e12f4e0f06ac8e9497",
                  "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                  "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                  "grant_id": "urn:cognous:grant:routine-1"
                },
                "record_commitment": "sha256:865eb4d1713c75d401476e51dcbc507e634b00252c8314c3d3cc98586129deaa",
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
              }
            ],
            "reasons": [
              "grant_revoked"
            ]
          }
        },
        {
          "record_id": "control-plane-security-runtime@a34c3dc2:input_time_floors:5",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
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
            "sha256:6e2ad318158316fbe204f27531f5d59e0588a8e1338eb41b36917b88b7067de6": "2026-10-05T19:00:00+00:00"
          }
        },
        {
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:6",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 6,
          "source_path": "check_events[0]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
            "phase": "opened",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:7",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 7,
          "source_path": "check_events[1]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:8",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 8,
          "source_path": "check_events[2]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
              "record_commitment": "sha256:f67908364e87a9397b3b6ef66c0d4360e4c785d7a6bdb357e74e164e755f983e",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:9",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 9,
          "source_path": "check_events[3]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:10",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 10,
          "source_path": "check_events[4]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:11",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 11,
          "source_path": "check_events[5]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:12",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 12,
          "source_path": "check_events[6]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:13",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 13,
          "source_path": "check_events[7]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:14",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 14,
          "source_path": "check_events[8]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:15",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 15,
          "source_path": "check_events[9]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
                "runtime_authority_commitment": "sha256:5f1cec7438ec4ad88f4fd9f6e3021706846fd8d6705972e12f4e0f06ac8e9497",
                "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                "grant_id": "urn:cognous:grant:routine-1"
              },
              "record_commitment": "sha256:865eb4d1713c75d401476e51dcbc507e634b00252c8314c3d3cc98586129deaa",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:16",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 16,
          "source_path": "check_events[10]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:17",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 17,
          "source_path": "check_events[11]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:18",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 18,
          "source_path": "check_events[12]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
            "phase": "completed",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:19",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 19,
          "source_path": "check_events[13]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
            "phase": "opened",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:20",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 20,
          "source_path": "check_events[14]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:21",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 21,
          "source_path": "check_events[15]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
              "record_commitment": "sha256:f67908364e87a9397b3b6ef66c0d4360e4c785d7a6bdb357e74e164e755f983e",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:22",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 22,
          "source_path": "check_events[16]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:23",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 23,
          "source_path": "check_events[17]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:24",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 24,
          "source_path": "check_events[18]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:25",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 25,
          "source_path": "check_events[19]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
                "status": "revoked",
                "version": "status-v1",
                "observed_at": "2026-10-05T19:00:00+00:00"
              },
              "record_commitment": "sha256:923e78ee4d0d6b571cb9dcd080f27719bc46f513f249ea9cca34aff494ebd900",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:26",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 26,
          "source_path": "check_events[20]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:27",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 27,
          "source_path": "check_events[21]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:28",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 28,
          "source_path": "check_events[22]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
                "runtime_authority_commitment": "sha256:5f1cec7438ec4ad88f4fd9f6e3021706846fd8d6705972e12f4e0f06ac8e9497",
                "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                "grant_id": "urn:cognous:grant:routine-1"
              },
              "record_commitment": "sha256:865eb4d1713c75d401476e51dcbc507e634b00252c8314c3d3cc98586129deaa",
              "missing": false,
              "previous_observed_at": null
            },
            "reasons": [],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:29",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 29,
          "source_path": "check_events[23]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:30",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 30,
          "source_path": "check_events[24]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:31",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 31,
          "source_path": "check_events[25]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
            "phase": "completed",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "3215",
              "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "action_class": {
              "class_id": "synthetic-irreversible",
              "irreversible": true,
              "max_status_age_seconds": 60,
              "on_unreadable": "refuse"
            },
            "input": null,
            "reasons": [
              "grant_revoked"
            ],
            "reason_vocabulary_version": "runtime-authority-reasons/0.1"
          }
        },
        {
          "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:execution_envelope:32",
          "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1",
          "record_type": "execution_envelope",
          "source_sequence": 32,
          "source_path": "moltbot.execution_envelope",
          "recorded_at": null,
          "identifiers": {
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
          "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:executor_control_plane_evidence:33",
          "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1",
          "record_type": "executor_control_plane_evidence",
          "source_sequence": 33,
          "source_path": "moltbot.control_plane_evidence",
          "recorded_at": null,
          "identifiers": {},
          "evidence_class": "producer_reported",
          "data": {
            "failure_record_id": "df7d397d-a198-4309-9cf8-e75de02ebd78",
            "refusal": {
              "reason_vocabulary_version": "runtime-authority-reasons/0.1",
              "reopen_conditions": [
                {
                  "kind": "successor_grant_revision",
                  "input_id": "urn:cognous:grant:routine-1",
                  "previous_revision": "1"
                }
              ],
              "refusal_id": "4aec4784-cf57-47d6-a4c8-8115689756ed",
              "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
                "grant_revoked"
              ],
              "changed_inputs": [
                {
                  "input_type": "grant",
                  "input_id": "urn:cognous:grant:routine-1",
                  "expected_version": "revision=1;status=active",
                  "observed_version": "revision=1;status=revoked;version=status-v1;observed_at=2026-10-05T19:00:00+00:00"
                }
              ],
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
                  "record_commitment": "sha256:f67908364e87a9397b3b6ef66c0d4360e4c785d7a6bdb357e74e164e755f983e",
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
                    "status": "revoked",
                    "version": "status-v1",
                    "observed_at": "2026-10-05T19:00:00+00:00"
                  },
                  "record_commitment": "sha256:923e78ee4d0d6b571cb9dcd080f27719bc46f513f249ea9cca34aff494ebd900",
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
                    "runtime_authority_commitment": "sha256:5f1cec7438ec4ad88f4fd9f6e3021706846fd8d6705972e12f4e0f06ac8e9497",
                    "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                    "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                    "grant_id": "urn:cognous:grant:routine-1"
                  },
                  "record_commitment": "sha256:865eb4d1713c75d401476e51dcbc507e634b00252c8314c3d3cc98586129deaa",
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
                }
              ]
            }
          }
        },
        {
          "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:execution_result:34",
          "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1",
          "record_type": "execution_result",
          "source_sequence": 34,
          "source_path": "moltbot.execution_result",
          "recorded_at": null,
          "identifiers": {
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829"
          },
          "evidence_class": "producer_reported",
          "data": {
            "status": "denied",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "attempt_id": null,
            "attempted": false,
            "acknowledged": false,
            "observed_state": "unknown",
            "newly_executed": false,
            "observation": {},
            "error": "authorization-critical inputs changed before effect",
            "control_plane_evidence": {
              "failure_record_id": "df7d397d-a198-4309-9cf8-e75de02ebd78",
              "refusal": {
                "reason_vocabulary_version": "runtime-authority-reasons/0.1",
                "reopen_conditions": [
                  {
                    "kind": "successor_grant_revision",
                    "input_id": "urn:cognous:grant:routine-1",
                    "previous_revision": "1"
                  }
                ],
                "refusal_id": "4aec4784-cf57-47d6-a4c8-8115689756ed",
                "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
                  "grant_revoked"
                ],
                "changed_inputs": [
                  {
                    "input_type": "grant",
                    "input_id": "urn:cognous:grant:routine-1",
                    "expected_version": "revision=1;status=active",
                    "observed_version": "revision=1;status=revoked;version=status-v1;observed_at=2026-10-05T19:00:00+00:00"
                  }
                ],
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
                    "record_commitment": "sha256:f67908364e87a9397b3b6ef66c0d4360e4c785d7a6bdb357e74e164e755f983e",
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
                      "status": "revoked",
                      "version": "status-v1",
                      "observed_at": "2026-10-05T19:00:00+00:00"
                    },
                    "record_commitment": "sha256:923e78ee4d0d6b571cb9dcd080f27719bc46f513f249ea9cca34aff494ebd900",
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
                      "runtime_authority_commitment": "sha256:5f1cec7438ec4ad88f4fd9f6e3021706846fd8d6705972e12f4e0f06ac8e9497",
                      "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                      "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                      "grant_id": "urn:cognous:grant:routine-1"
                    },
                    "record_commitment": "sha256:865eb4d1713c75d401476e51dcbc507e634b00252c8314c3d3cc98586129deaa",
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
          "source_record_id": "control-plane-security-runtime@a34c3dc2:runtime_proposal:0",
          "source_path": "proposal.payload_commitment",
          "verification_status": "checked_match",
          "notes": null
        },
        {
          "label": "effect_id",
          "value": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "source_record_id": "control-plane-security-runtime@a34c3dc2:runtime_decision:1",
          "source_path": "decisions[0].effect_id",
          "verification_status": "checked_match",
          "notes": "Checked under pinned Control Plane effect-id contract."
        },
        {
          "label": "proposal_commitment",
          "value": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "source_record_id": "control-plane-security-runtime@a34c3dc2:runtime_decision:1",
          "source_path": "decisions[0].binding.proposal_commitment",
          "verification_status": "attributed_claim",
          "notes": null
        },
        {
          "label": "manifest_digest",
          "value": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "source_record_id": "control-plane-security-runtime@a34c3dc2:runtime_decision:1",
          "source_path": "decisions[0].binding.manifest_digest",
          "verification_status": "attributed_claim",
          "notes": null
        },
        {
          "label": "payload_commitment",
          "value": "sha256:6b782ebbcc034edeca4069b31aa4d8cbc9d3eeaf3b2034ab989bb430de962c0e",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "source_record_id": "control-plane-security-runtime@a34c3dc2:runtime_decision:1",
          "source_path": "decisions[0].binding.payload_commitment",
          "verification_status": "attributed_claim",
          "notes": null
        },
        {
          "label": "requirement_commitment",
          "value": "sha256:6590406e701b51e637c87953860d1ceb72d8da0af87311048f152e0ee2b8ccb6",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "source_record_id": "control-plane-security-runtime@a34c3dc2:runtime_decision:1",
          "source_path": "decisions[0].binding.requirement_commitment",
          "verification_status": "attributed_claim",
          "notes": null
        },
        {
          "label": "role_mapping_digest",
          "value": "sha256:f8a8db156df7087ddf34be1ed77fc86fa20ba7668deb87a9b3a5bd0a6ace496d",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "source_record_id": "control-plane-security-runtime@a34c3dc2:runtime_decision:1",
          "source_path": "decisions[0].binding.role_mapping_digest",
          "verification_status": "attributed_claim",
          "notes": null
        },
        {
          "label": "payload_commitment",
          "value": "sha256:6b782ebbcc034edeca4069b31aa4d8cbc9d3eeaf3b2034ab989bb430de962c0e",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "source_record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:execution_envelope:32",
          "source_path": "moltbot.execution_envelope.operation.payload_commitment",
          "verification_status": "checked_match",
          "notes": null
        }
      ],
      "import_reports": [
        {
          "adapter_profile": "control-plane-security-runtime@a34c3dc2",
          "source_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
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
        "control_plane_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
        "moltbot_safe_revision": "e20f92e104aba2ba6ad06120d8549c6170eaf63f",
        "moltbot_producer_contract": {
          "profile_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1",
          "control_plane_revision": "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5",
          "compatible_control_plane_revisions": [
            "a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5"
          ],
          "repository_revision": "e20f92e104aba2ba6ad06120d8549c6170eaf63f",
          "interface_profile_id": "urn:cognous:profiles:moltbot-safe-executor-producer",
          "interface_profile_version": "2.0.0",
          "provenance": {
            "mode": "versioned_profile",
            "source_asserted": {
              "repository_revision": "e20f92e104aba2ba6ad06120d8549c6170eaf63f",
              "producer_profile_id": "urn:cognous:profiles:moltbot-safe-executor-producer",
              "producer_profile_version": "2.0.0"
            },
            "independently_established": []
          },
          "legacy": false
        },
        "manifest_revision": "2c36bcd0b620dbfe7ad924bc7196a3f0c04c5c5e",
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
        "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
            "approval_commitment": "sha256:5f1cec7438ec4ad88f4fd9f6e3021706846fd8d6705972e12f4e0f06ac8e9497",
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
            "record_commitment": "sha256:f67908364e87a9397b3b6ef66c0d4360e4c785d7a6bdb357e74e164e755f983e",
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
              "runtime_authority_commitment": "sha256:5f1cec7438ec4ad88f4fd9f6e3021706846fd8d6705972e12f4e0f06ac8e9497",
              "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
              "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
              "grant_id": "urn:cognous:grant:routine-1"
            },
            "record_commitment": "sha256:865eb4d1713c75d401476e51dcbc507e634b00252c8314c3d3cc98586129deaa",
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
          }
        ]
      }
    ],
    "effect_time_refusal": [
      {
        "reason_vocabulary_version": "runtime-authority-reasons/0.1",
        "reopen_conditions": [
          {
            "kind": "successor_grant_revision",
            "input_id": "urn:cognous:grant:routine-1",
            "previous_revision": "1"
          }
        ],
        "refusal_id": "4aec4784-cf57-47d6-a4c8-8115689756ed",
        "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
          "grant_revoked"
        ],
        "changed_inputs": [
          {
            "input_type": "grant",
            "input_id": "urn:cognous:grant:routine-1",
            "expected_version": "revision=1;status=active",
            "observed_version": "revision=1;status=revoked;version=status-v1;observed_at=2026-10-05T19:00:00+00:00"
          }
        ],
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
            "record_commitment": "sha256:f67908364e87a9397b3b6ef66c0d4360e4c785d7a6bdb357e74e164e755f983e",
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
              "status": "revoked",
              "version": "status-v1",
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:923e78ee4d0d6b571cb9dcd080f27719bc46f513f249ea9cca34aff494ebd900",
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
              "runtime_authority_commitment": "sha256:5f1cec7438ec4ad88f4fd9f6e3021706846fd8d6705972e12f4e0f06ac8e9497",
              "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
              "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
              "grant_id": "urn:cognous:grant:routine-1"
            },
            "record_commitment": "sha256:865eb4d1713c75d401476e51dcbc507e634b00252c8314c3d3cc98586129deaa",
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
          }
        ]
      }
    ],
    "resolution_check": [
      {
        "check_id": "a7d71810-8b77-448b-b8ba-4234f0ab0f70",
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
            "record_commitment": "sha256:f67908364e87a9397b3b6ef66c0d4360e4c785d7a6bdb357e74e164e755f983e",
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
              "runtime_authority_commitment": "sha256:5f1cec7438ec4ad88f4fd9f6e3021706846fd8d6705972e12f4e0f06ac8e9497",
              "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
              "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
              "grant_id": "urn:cognous:grant:routine-1"
            },
            "record_commitment": "sha256:865eb4d1713c75d401476e51dcbc507e634b00252c8314c3d3cc98586129deaa",
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
          }
        ],
        "reasons": []
      },
      {
        "check_id": "a4c65521-d803-44b8-a237-68fb2e695526",
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
            "record_commitment": "sha256:f67908364e87a9397b3b6ef66c0d4360e4c785d7a6bdb357e74e164e755f983e",
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
              "status": "revoked",
              "version": "status-v1",
              "observed_at": "2026-10-05T19:00:00+00:00"
            },
            "record_commitment": "sha256:923e78ee4d0d6b571cb9dcd080f27719bc46f513f249ea9cca34aff494ebd900",
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
              "runtime_authority_commitment": "sha256:5f1cec7438ec4ad88f4fd9f6e3021706846fd8d6705972e12f4e0f06ac8e9497",
              "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
              "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
              "grant_id": "urn:cognous:grant:routine-1"
            },
            "record_commitment": "sha256:865eb4d1713c75d401476e51dcbc507e634b00252c8314c3d3cc98586129deaa",
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
          }
        ],
        "reasons": [
          "grant_revoked"
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
        "sha256:6e2ad318158316fbe204f27531f5d59e0588a8e1338eb41b36917b88b7067de6": "2026-10-05T19:00:00+00:00"
      }
    ],
    "resolution_check_event": [
      {
        "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
        "phase": "opened",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
        "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
        "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
          "record_commitment": "sha256:f67908364e87a9397b3b6ef66c0d4360e4c785d7a6bdb357e74e164e755f983e",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
        "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
        "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
        "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
        "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
        "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
        "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
            "runtime_authority_commitment": "sha256:5f1cec7438ec4ad88f4fd9f6e3021706846fd8d6705972e12f4e0f06ac8e9497",
            "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
            "grant_id": "urn:cognous:grant:routine-1"
          },
          "record_commitment": "sha256:865eb4d1713c75d401476e51dcbc507e634b00252c8314c3d3cc98586129deaa",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
        "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
        "check_id": "bafffc50-3a05-4a2d-9460-798a7343b089",
        "phase": "completed",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "e7475d82-bee1-4b1e-b672-975248912d26"
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
        "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
        "phase": "opened",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
        "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
        "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
          "record_commitment": "sha256:f67908364e87a9397b3b6ef66c0d4360e4c785d7a6bdb357e74e164e755f983e",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
        "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
        "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
        "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
            "status": "revoked",
            "version": "status-v1",
            "observed_at": "2026-10-05T19:00:00+00:00"
          },
          "record_commitment": "sha256:923e78ee4d0d6b571cb9dcd080f27719bc46f513f249ea9cca34aff494ebd900",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
        "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
        "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
            "runtime_authority_commitment": "sha256:5f1cec7438ec4ad88f4fd9f6e3021706846fd8d6705972e12f4e0f06ac8e9497",
            "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
            "grant_id": "urn:cognous:grant:routine-1"
          },
          "record_commitment": "sha256:865eb4d1713c75d401476e51dcbc507e634b00252c8314c3d3cc98586129deaa",
          "missing": false,
          "previous_observed_at": null
        },
        "reasons": [],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      },
      {
        "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
        "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
        "check_id": "3e5aa2cb-28e3-4ade-a414-f9edc8d8b7d4",
        "phase": "completed",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "3215",
          "token": "df7bbf8f-f23a-4e18-b575-13e33f3cbf2a"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "action_class": {
          "class_id": "synthetic-irreversible",
          "irreversible": true,
          "max_status_age_seconds": 60,
          "on_unreadable": "refuse"
        },
        "input": null,
        "reasons": [
          "grant_revoked"
        ],
        "reason_vocabulary_version": "runtime-authority-reasons/0.1"
      }
    ],
    "execution_envelope": [
      {
        "version": "0.2.0",
        "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
        "failure_record_id": "df7d397d-a198-4309-9cf8-e75de02ebd78",
        "refusal": {
          "reason_vocabulary_version": "runtime-authority-reasons/0.1",
          "reopen_conditions": [
            {
              "kind": "successor_grant_revision",
              "input_id": "urn:cognous:grant:routine-1",
              "previous_revision": "1"
            }
          ],
          "refusal_id": "4aec4784-cf57-47d6-a4c8-8115689756ed",
          "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
            "grant_revoked"
          ],
          "changed_inputs": [
            {
              "input_type": "grant",
              "input_id": "urn:cognous:grant:routine-1",
              "expected_version": "revision=1;status=active",
              "observed_version": "revision=1;status=revoked;version=status-v1;observed_at=2026-10-05T19:00:00+00:00"
            }
          ],
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
              "record_commitment": "sha256:f67908364e87a9397b3b6ef66c0d4360e4c785d7a6bdb357e74e164e755f983e",
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
                "status": "revoked",
                "version": "status-v1",
                "observed_at": "2026-10-05T19:00:00+00:00"
              },
              "record_commitment": "sha256:923e78ee4d0d6b571cb9dcd080f27719bc46f513f249ea9cca34aff494ebd900",
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
                "runtime_authority_commitment": "sha256:5f1cec7438ec4ad88f4fd9f6e3021706846fd8d6705972e12f4e0f06ac8e9497",
                "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                "grant_id": "urn:cognous:grant:routine-1"
              },
              "record_commitment": "sha256:865eb4d1713c75d401476e51dcbc507e634b00252c8314c3d3cc98586129deaa",
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
            }
          ]
        }
      }
    ],
    "execution_result": [
      {
        "status": "denied",
        "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "attempt_id": null,
        "attempted": false,
        "acknowledged": false,
        "observed_state": "unknown",
        "newly_executed": false,
        "observation": {},
        "error": "authorization-critical inputs changed before effect",
        "control_plane_evidence": {
          "failure_record_id": "df7d397d-a198-4309-9cf8-e75de02ebd78",
          "refusal": {
            "reason_vocabulary_version": "runtime-authority-reasons/0.1",
            "reopen_conditions": [
              {
                "kind": "successor_grant_revision",
                "input_id": "urn:cognous:grant:routine-1",
                "previous_revision": "1"
              }
            ],
            "refusal_id": "4aec4784-cf57-47d6-a4c8-8115689756ed",
            "decision_id": "747bde17-06cc-427d-a505-f6427c7869cd",
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
              "grant_revoked"
            ],
            "changed_inputs": [
              {
                "input_type": "grant",
                "input_id": "urn:cognous:grant:routine-1",
                "expected_version": "revision=1;status=active",
                "observed_version": "revision=1;status=revoked;version=status-v1;observed_at=2026-10-05T19:00:00+00:00"
              }
            ],
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
                "record_commitment": "sha256:f67908364e87a9397b3b6ef66c0d4360e4c785d7a6bdb357e74e164e755f983e",
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
                  "status": "revoked",
                  "version": "status-v1",
                  "observed_at": "2026-10-05T19:00:00+00:00"
                },
                "record_commitment": "sha256:923e78ee4d0d6b571cb9dcd080f27719bc46f513f249ea9cca34aff494ebd900",
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
                  "runtime_authority_commitment": "sha256:5f1cec7438ec4ad88f4fd9f6e3021706846fd8d6705972e12f4e0f06ac8e9497",
                  "proposal": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
                  "policies": "sha256:1cb091c265589e9d079a3c814befac072b3ad7f11f6bfbd0968825f3b816dee2",
                  "grant_id": "urn:cognous:grant:routine-1"
                },
                "record_commitment": "sha256:865eb4d1713c75d401476e51dcbc507e634b00252c8314c3d3cc98586129deaa",
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
        "code": "grant_revoked",
        "count": 1,
        "share": 1.0
      }
    ],
    "prior_window": "unavailable",
    "disappearance_assessed": false,
    "limitation": "source-record counts; exposure and collection completeness not independently established"
  }
}</pre>
