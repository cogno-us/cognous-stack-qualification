# Traceable Agent Governance Evidence Pack

| Field | Value |
|---|---|
| Pack ID | agep-0bc27c59f65ee607 |
| Version | 0.2.0 |
| Generated At | 2026-10-16T19:27:53.045581+00:00 |
| Review Status (asserted, unverified) | draft |
| Agent | Synthetic Refund Agent |
| Environment | other |
| Owner | cognous-integration-pilot |
| Business Unit | — |

## 1. Executive Summary

**Synthetic Refund Agent** is represented in this evidence pack for the **other** environment. Business purpose: Imported from Manifest and Reconstruction Bundle; business purpose unavailable.

The pack records **1** tool(s), **2** action(s), **2** privileged/review-sensitive action(s), and **1** replay/reconstruction bundle reference(s).

Validation summary (asserted, unverified): 1 valid bundle(s), 0 invalid bundle(s), 0 error(s), 2 warning(s).
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
| c3d9c6d6-f375-4868-b73c-b0bd1d5c6a5c | run-1 | validated_complete | 2026-10-16T19:27:53.045581+00:00 | No | No | semantically_valid | metadata.traceable_import.source_record_refs |

## 11. Validation Summary

_These values are caller assertions recorded in the pack. They are not verified by this renderer: no reviewer identity, signature, redaction or validation result is checked._

**Valid Bundles:** 1 | **Invalid Bundles:** 0 | **Errors:** 0 | **Warnings:** 2

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
| reconstruction_bundle | c3d9c6d6-f375-4868-b73c-b0bd1d5c6a5c | 0.2.0 | sha256:3569e9b19d6ef8abb40365b83b14f2ace03c8eee97d78cdebadd7179f7a0d89f | 79ba16d48b9be1e059b3045989c7df960c3df1c2 | validated_complete |

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
| control_plane_attempt_count | 1 |
| executor_attempt_count | 1 |
| attempt_transition_record_count | 4 |
| authorization_granted_count | 1 |
| authorization_held_count | 0 |
| authorization_denied_count | 0 |
| destination_observation.absent | 1 |
| destination_observation.applied | 1 |
| acknowledgement.control_plane_unknown | 1 |
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
| execution_attempted | yes |
| acknowledgement | unknown |
| destination_observed | applied |
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
| REPLAY_M002 | warning | attempt_correlation | Control Plane and executor attempt namespaces are preserved separately; no equivalence is inferred. |
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
| M002 | unsupported_semantic | warning | attempt_correlation | unknown | Control Plane and executor attempt namespaces are preserved separately; no equivalence is inferred. |
| M003 | conversion_warning | info | moltbot.execution_envelope.operation.institution_id | — | Institution/domain provenance is the trusted Moltbot integration context, not Control Plane AuthorizationBinding. |
| M004 | conversion_warning | info | moltbot.execution_envelope.operation.authority_context_id | — | At the pinned adapter this field carries the proposal profile reference; it is distinct from the Control Plane binding context-instance ID. |

### Supporting source-record references

| Record ID | Type | Producer Profile | Evidence Class (source assertion) | Producer Revision | Revision Check | Source Path |
|---|---|---|---|---|---|---|
| control-plane-security-runtime@a34c3dc2:runtime_proposal:0 | runtime_proposal | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | proposal |
| control-plane-security-runtime@a34c3dc2:runtime_decision:1 | runtime_decision | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | decisions&#91;0&#93; |
| control-plane-security-runtime@a34c3dc2:control_plane_attempt_transition:2 | control_plane_attempt_transition | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | attempts&#91;0&#93; |
| control-plane-security-runtime@a34c3dc2:control_plane_attempt_transition:3 | control_plane_attempt_transition | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | attempts&#91;1&#93; |
| control-plane-security-runtime@a34c3dc2:effect_observation:4 | effect_observation | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | observations&#91;0&#93; |
| control-plane-security-runtime@a34c3dc2:effect_observation:5 | effect_observation | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | observations&#91;1&#93; |
| control-plane-security-runtime@a34c3dc2:reconciliation:6 | reconciliation | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | reconciliations&#91;0&#93; |
| control-plane-security-runtime@a34c3dc2:reconciliation:7 | reconciliation | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | reconciliations&#91;1&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check:8 | resolution_check | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | resolution_checks&#91;0&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check:9 | resolution_check | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | resolution_checks&#91;1&#93; |
| control-plane-security-runtime@a34c3dc2:attempt_closeout:10 | attempt_closeout | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | closeouts&#91;0&#93; |
| control-plane-security-runtime@a34c3dc2:input_time_floors:11 | input_time_floors | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | input_time_floors |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:12 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;0&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:13 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;1&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:14 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;2&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:15 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;3&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:16 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;4&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:17 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;5&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:18 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;6&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:19 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;7&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:20 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;8&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:21 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;9&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:22 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;10&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:23 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;11&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:24 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;12&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:25 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;13&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:26 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;14&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:27 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;15&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:28 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;16&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:29 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;17&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:30 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;18&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:31 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;19&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:32 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;20&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:33 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;21&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:34 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;22&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:35 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;23&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:36 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;24&#93; |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:37 | resolution_check_event | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | check_events&#91;25&#93; |
| moltbot-safe-executor-producer-2.0.0@e20f92e1:execution_envelope:38 | execution_envelope | moltbot-safe-executor-producer-2.0.0@e20f92e1 | producer_reported | e20f92e104aba2ba6ad06120d8549c6170eaf63f | declared_revision_matches_accepted_pin | moltbot.execution_envelope |
| moltbot-safe-executor-producer-2.0.0@e20f92e1:executor_control_plane_evidence:39 | executor_control_plane_evidence | moltbot-safe-executor-producer-2.0.0@e20f92e1 | producer_reported | e20f92e104aba2ba6ad06120d8549c6170eaf63f | declared_revision_matches_accepted_pin | moltbot.control_plane_evidence |
| moltbot-safe-executor-producer-2.0.0@e20f92e1:execution_result:40 | execution_result | moltbot-safe-executor-producer-2.0.0@e20f92e1 | producer_reported | e20f92e104aba2ba6ad06120d8549c6170eaf63f | declared_revision_matches_accepted_pin | moltbot.execution_result |
| moltbot-safe-executor-producer-2.0.0@e20f92e1:destination_attempt:41 | destination_attempt | moltbot-safe-executor-producer-2.0.0@e20f92e1 | producer_reported | e20f92e104aba2ba6ad06120d8549c6170eaf63f | declared_revision_matches_accepted_pin | moltbot.attempts&#91;0&#93; |
| moltbot-safe-executor-producer-2.0.0@e20f92e1:destination_attempt_event:42 | destination_attempt_event | moltbot-safe-executor-producer-2.0.0@e20f92e1 | producer_reported | e20f92e104aba2ba6ad06120d8549c6170eaf63f | declared_revision_matches_accepted_pin | moltbot.attempt_events&#91;0&#93; |
| moltbot-safe-executor-producer-2.0.0@e20f92e1:destination_attempt_event:43 | destination_attempt_event | moltbot-safe-executor-producer-2.0.0@e20f92e1 | producer_reported | e20f92e104aba2ba6ad06120d8549c6170eaf63f | declared_revision_matches_accepted_pin | moltbot.attempt_events&#91;1&#93; |
| control-plane-security-runtime@a34c3dc2:moltbot_attributed_control_plane_attempt:44 | moltbot_attributed_control_plane_attempt | control-plane-security-runtime@a34c3dc2 | producer_reported | a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5 | declared_revision_matches_accepted_pin | moltbot.control_plane_attempts&#91;0&#93; |
| moltbot-safe-executor-producer-2.0.0@e20f92e1:destination_effect:45 | destination_effect | moltbot-safe-executor-producer-2.0.0@e20f92e1 | producer_reported | e20f92e104aba2ba6ad06120d8549c6170eaf63f | declared_revision_matches_accepted_pin | moltbot.effects&#91;0&#93; |
| moltbot-safe-executor-producer-2.0.0@e20f92e1:executor_observation:46 | executor_observation | moltbot-safe-executor-producer-2.0.0@e20f92e1 | producer_reported | e20f92e104aba2ba6ad06120d8549c6170eaf63f | declared_revision_matches_accepted_pin | moltbot.observations&#91;0&#93; |

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
| moltbot-safe-executor-producer-2.0.0@e20f92e1:execution_envelope:38 | payload_commitment | sha256:6b782ebbcc034edeca4069b31aa4d8cbc9d3eeaf3b2034ab989bb430de962c0e | SHA-256 | json-sort-keys-compact-utf8-no-nan | checked_match | moltbot.execution_envelope.operation.payload_commitment |
| moltbot-safe-executor-producer-2.0.0@e20f92e1:destination_effect:45 | operation_digest | sha256:ffcad4c587ea3a81df49e9b2c5d3ee817a929d07356d8704db82c1b9c70af175 | SHA-256 | json-sort-keys-compact-utf8-no-nan | checked_match | moltbot.effects&#91;0&#93;.operation_digest |

### Locally computed record commitments

| Record ID | Local Commitment | Compatibility Hash Alias | Canonicalization | Verification Status |
|---|---|---|---|---|
| control-plane-security-runtime@a34c3dc2:runtime_proposal:0 | sha256:f571d7c4baf2f994443a25dc6c621514836d71e655a80c63f0a86445b518b6c8 | sha256:f571d7c4baf2f994443a25dc6c621514836d71e655a80c63f0a86445b518b6c8 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:runtime_decision:1 | sha256:0b94b7a8786be5dfc024412183a7072c1c133b80870f2e5d86f6a3a34c26655f | sha256:0b94b7a8786be5dfc024412183a7072c1c133b80870f2e5d86f6a3a34c26655f | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:control_plane_attempt_transition:2 | sha256:aea0f3bbda98a1a6ac7dc07c0f366c226f31901d16e900dbe7ff19714c5151b6 | sha256:aea0f3bbda98a1a6ac7dc07c0f366c226f31901d16e900dbe7ff19714c5151b6 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:control_plane_attempt_transition:3 | sha256:50b47cfd2bdcabd411d7bfde9dd55aa05f5a9e4b620be72e09b29945eaa612ee | sha256:50b47cfd2bdcabd411d7bfde9dd55aa05f5a9e4b620be72e09b29945eaa612ee | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:effect_observation:4 | sha256:ad8f3ee4f96a3a6659b5b9f47780f9069825b8b1ef9133177ea0bf4ca40c2892 | sha256:ad8f3ee4f96a3a6659b5b9f47780f9069825b8b1ef9133177ea0bf4ca40c2892 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:effect_observation:5 | sha256:4c6abb07c0694cc64ed6425a621ee1a50e2124fca0148133abf65da556b4e4f2 | sha256:4c6abb07c0694cc64ed6425a621ee1a50e2124fca0148133abf65da556b4e4f2 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:reconciliation:6 | sha256:b19bbf1f16287405a55d98b864290fa837dc76019a3d4d62083b783e3710e772 | sha256:b19bbf1f16287405a55d98b864290fa837dc76019a3d4d62083b783e3710e772 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:reconciliation:7 | sha256:421ac9e34746de614fab63abd46cbef56a5900bf4d38a7f91eb8e56472737b91 | sha256:421ac9e34746de614fab63abd46cbef56a5900bf4d38a7f91eb8e56472737b91 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check:8 | sha256:de9910c0d5e0988c1ddc478f889b4524df546f87fb0707fc6beb46afd6f879d2 | sha256:de9910c0d5e0988c1ddc478f889b4524df546f87fb0707fc6beb46afd6f879d2 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check:9 | sha256:89c9e5aeade439182ce60a8a87af4a78fbd8b458611b39250ca89e4db09c84b6 | sha256:89c9e5aeade439182ce60a8a87af4a78fbd8b458611b39250ca89e4db09c84b6 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:attempt_closeout:10 | sha256:bc3c12f99615f3ee17990bd3de9bb02e4726b2a219ea9a56529e5ed971b47a45 | sha256:bc3c12f99615f3ee17990bd3de9bb02e4726b2a219ea9a56529e5ed971b47a45 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:input_time_floors:11 | sha256:1232f87aa0bfa7ba03d77eaaba2ef2f3f2e2e15e1b0c94da3b2c6f54d711cd6f | sha256:1232f87aa0bfa7ba03d77eaaba2ef2f3f2e2e15e1b0c94da3b2c6f54d711cd6f | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:12 | sha256:4a7f745b884dff8753f6b5851b92afe15f9200d47b6f851f127a757f75c29273 | sha256:4a7f745b884dff8753f6b5851b92afe15f9200d47b6f851f127a757f75c29273 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:13 | sha256:ad82b7a70dd1f5da591b1d75813503c49dff4bce80ec74e38cf5d4cd709e6b99 | sha256:ad82b7a70dd1f5da591b1d75813503c49dff4bce80ec74e38cf5d4cd709e6b99 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:14 | sha256:4b428697a551bdf0f62a7cf3bf6541512ff46abaf4b5b999ce5d99fa1581e9e1 | sha256:4b428697a551bdf0f62a7cf3bf6541512ff46abaf4b5b999ce5d99fa1581e9e1 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:15 | sha256:beaa4a8f881e22779f117ca301b26463d11049f91603bb92ebfa5c11fec628d8 | sha256:beaa4a8f881e22779f117ca301b26463d11049f91603bb92ebfa5c11fec628d8 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:16 | sha256:7bc7c85611d4c253b836544ad9b723e39b74179656453e4058738f3ff9ae37bf | sha256:7bc7c85611d4c253b836544ad9b723e39b74179656453e4058738f3ff9ae37bf | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:17 | sha256:37c12c50aca0659e4ad03f2594a3faa062a4357adefbf9f4d58580ab756020ed | sha256:37c12c50aca0659e4ad03f2594a3faa062a4357adefbf9f4d58580ab756020ed | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:18 | sha256:a4feb11cc072ceacc4e906475a547a797967e2ba0a69dbae1b7e1df6379cc2e8 | sha256:a4feb11cc072ceacc4e906475a547a797967e2ba0a69dbae1b7e1df6379cc2e8 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:19 | sha256:ff50dde1246805dcd621cd8dfc6a3f33c2ffb4f830780e16098236efcd8c658d | sha256:ff50dde1246805dcd621cd8dfc6a3f33c2ffb4f830780e16098236efcd8c658d | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:20 | sha256:448d9a0ac9f94466540c85bc11dedb698511eb16f5b631ec21b5526062c9c6d7 | sha256:448d9a0ac9f94466540c85bc11dedb698511eb16f5b631ec21b5526062c9c6d7 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:21 | sha256:b654560737856c675e304c965af13d64af9dc48b40141f1cea1461a9006a9986 | sha256:b654560737856c675e304c965af13d64af9dc48b40141f1cea1461a9006a9986 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:22 | sha256:d6d5a5e90e48bcc2f72fb794f538ad558e10a65018bff54d5134d28e2a39a410 | sha256:d6d5a5e90e48bcc2f72fb794f538ad558e10a65018bff54d5134d28e2a39a410 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:23 | sha256:e27b63401874c432d6f8766664d5927e1d3c82662bb89c998f9287557a1e6f27 | sha256:e27b63401874c432d6f8766664d5927e1d3c82662bb89c998f9287557a1e6f27 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:24 | sha256:6b6d538968e21e66fb625bde9a94446d665d14f6817e69f5a596bad03da71177 | sha256:6b6d538968e21e66fb625bde9a94446d665d14f6817e69f5a596bad03da71177 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:25 | sha256:a6ca6474137907762d67bfb2d7a0aeb6d45bd6334549b783dbb148eeaf3248fd | sha256:a6ca6474137907762d67bfb2d7a0aeb6d45bd6334549b783dbb148eeaf3248fd | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:26 | sha256:66728f9b30093ea8289c3c1c0dbd61dc400e9e0e2e2d4550b50dad1262c6c013 | sha256:66728f9b30093ea8289c3c1c0dbd61dc400e9e0e2e2d4550b50dad1262c6c013 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:27 | sha256:1b9b47484fe865863be615efde719b9ee644a241573dd64e29b99fcc1e12e0c8 | sha256:1b9b47484fe865863be615efde719b9ee644a241573dd64e29b99fcc1e12e0c8 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:28 | sha256:524b167d80992abf2efaededbfcefe857a8703b2e030c7f16a7610ebb2118ea9 | sha256:524b167d80992abf2efaededbfcefe857a8703b2e030c7f16a7610ebb2118ea9 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:29 | sha256:8d46721f1b02ebc7c1fc9bd6a4d26588c7a2e4cae54d8a21d6fd60f982029fae | sha256:8d46721f1b02ebc7c1fc9bd6a4d26588c7a2e4cae54d8a21d6fd60f982029fae | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:30 | sha256:3dbba0235508fe22580158cc6ea6c1096fc2d951f74572f67553ec9d869c54e2 | sha256:3dbba0235508fe22580158cc6ea6c1096fc2d951f74572f67553ec9d869c54e2 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:31 | sha256:91d6ec2891e083514082619f6e240a4378c088567bed75bdcb7be6e8faa6afb9 | sha256:91d6ec2891e083514082619f6e240a4378c088567bed75bdcb7be6e8faa6afb9 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:32 | sha256:101a89a13768826ac7b79c6b30839c369001ba87136edb3929f19e03e8ca59a7 | sha256:101a89a13768826ac7b79c6b30839c369001ba87136edb3929f19e03e8ca59a7 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:33 | sha256:04fb70fae9e806c7ac3df0f8d78ced10c8273d192b95c6ed372e002fd5b0e4ab | sha256:04fb70fae9e806c7ac3df0f8d78ced10c8273d192b95c6ed372e002fd5b0e4ab | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:34 | sha256:57c4cd322a2c678fd72ee05abef310d781493e7d92a8255b977c5013c858feca | sha256:57c4cd322a2c678fd72ee05abef310d781493e7d92a8255b977c5013c858feca | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:35 | sha256:4de316f1bb662ebfc32d1e9912c61e3d1b8c540f2078b5cacaa4b0f2f0b879aa | sha256:4de316f1bb662ebfc32d1e9912c61e3d1b8c540f2078b5cacaa4b0f2f0b879aa | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:36 | sha256:2d42f022e933da80401356b08cb48d113f69553fd846e945f369f930d8cb6dda | sha256:2d42f022e933da80401356b08cb48d113f69553fd846e945f369f930d8cb6dda | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:resolution_check_event:37 | sha256:9c7f308132de2b09921ae8a8f03b8eeb7b5e2da85457c6caab25ec244f86d779 | sha256:9c7f308132de2b09921ae8a8f03b8eeb7b5e2da85457c6caab25ec244f86d779 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| moltbot-safe-executor-producer-2.0.0@e20f92e1:execution_envelope:38 | sha256:31e141b14ba8d7fbc14ebc3bea6f5e8942571c6cf9bf27dfe68f53cf8db953fd | sha256:31e141b14ba8d7fbc14ebc3bea6f5e8942571c6cf9bf27dfe68f53cf8db953fd | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| moltbot-safe-executor-producer-2.0.0@e20f92e1:executor_control_plane_evidence:39 | sha256:3a071336105f364fe0861cb2b39b94f07b1671dbeb0cd46423214bb750009337 | sha256:3a071336105f364fe0861cb2b39b94f07b1671dbeb0cd46423214bb750009337 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| moltbot-safe-executor-producer-2.0.0@e20f92e1:execution_result:40 | sha256:d7534c570c9535a0f2fc481f492f863eff48e08991a2a7dc1fec2df9b34dd0e5 | sha256:d7534c570c9535a0f2fc481f492f863eff48e08991a2a7dc1fec2df9b34dd0e5 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| moltbot-safe-executor-producer-2.0.0@e20f92e1:destination_attempt:41 | sha256:74315cb0bacdf3fb29f0acff4debf0a90d7b1db6a7a2453780b94ab71be2bebe | sha256:74315cb0bacdf3fb29f0acff4debf0a90d7b1db6a7a2453780b94ab71be2bebe | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| moltbot-safe-executor-producer-2.0.0@e20f92e1:destination_attempt_event:42 | sha256:8102304c16a5dd36753e8f5e6fda2bb3a90c41066508b55c7bf5cd49bf069626 | sha256:8102304c16a5dd36753e8f5e6fda2bb3a90c41066508b55c7bf5cd49bf069626 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| moltbot-safe-executor-producer-2.0.0@e20f92e1:destination_attempt_event:43 | sha256:1585adfab369cebeffdbda349891137e6f89530ccf593eef3bca6f12c59ec5fc | sha256:1585adfab369cebeffdbda349891137e6f89530ccf593eef3bca6f12c59ec5fc | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| control-plane-security-runtime@a34c3dc2:moltbot_attributed_control_plane_attempt:44 | sha256:e8aa6dadbed5bc5fb26fa695585dfc62db81c27ac136bc7bb393513292dd98d7 | sha256:e8aa6dadbed5bc5fb26fa695585dfc62db81c27ac136bc7bb393513292dd98d7 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| moltbot-safe-executor-producer-2.0.0@e20f92e1:destination_effect:45 | sha256:4dda202a1477299e8b40bb4149eade1d1dd717354321378893560adc9e54f8b6 | sha256:4dda202a1477299e8b40bb4149eade1d1dd717354321378893560adc9e54f8b6 | json-sort-keys-compact-utf8-no-nan | computed_during_import |
| moltbot-safe-executor-producer-2.0.0@e20f92e1:executor_observation:46 | sha256:793b830939f000a3688a95e82de1760521a1eac9e429dcc9826f034af3ef6322 | sha256:793b830939f000a3688a95e82de1760521a1eac9e429dcc9826f034af3ef6322 | json-sort-keys-compact-utf8-no-nan | computed_during_import |

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
          "code": "M002",
          "category": "unsupported_semantic",
          "severity": "warning",
          "path": "attempt_correlation",
          "message": "Control Plane and executor attempt namespaces are preserved separately; no equivalence is inferred.",
          "value_state": "unknown"
        },
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
      "artifact_id": "c3d9c6d6-f375-4868-b73c-b0bd1d5c6a5c",
      "version": "0.2.0",
      "hash": "sha256:3569e9b19d6ef8abb40365b83b14f2ace03c8eee97d78cdebadd7179f7a0d89f",
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
      "local_content_commitment": "sha256:0b94b7a8786be5dfc024412183a7072c1c133b80870f2e5d86f6a3a34c26655f",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:0b94b7a8786be5dfc024412183a7072c1c133b80870f2e5d86f6a3a34c26655f"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:control_plane_attempt_transition:2",
      "record_type": "control_plane_attempt_transition",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "attempts[0]",
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
      "local_content_commitment": "sha256:aea0f3bbda98a1a6ac7dc07c0f366c226f31901d16e900dbe7ff19714c5151b6",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:aea0f3bbda98a1a6ac7dc07c0f366c226f31901d16e900dbe7ff19714c5151b6"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:control_plane_attempt_transition:3",
      "record_type": "control_plane_attempt_transition",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "attempts[1]",
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
      "local_content_commitment": "sha256:50b47cfd2bdcabd411d7bfde9dd55aa05f5a9e4b620be72e09b29945eaa612ee",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:50b47cfd2bdcabd411d7bfde9dd55aa05f5a9e4b620be72e09b29945eaa612ee"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:effect_observation:4",
      "record_type": "effect_observation",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "observations[0]",
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
      "local_content_commitment": "sha256:ad8f3ee4f96a3a6659b5b9f47780f9069825b8b1ef9133177ea0bf4ca40c2892",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:ad8f3ee4f96a3a6659b5b9f47780f9069825b8b1ef9133177ea0bf4ca40c2892"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:effect_observation:5",
      "record_type": "effect_observation",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "observations[1]",
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
      "local_content_commitment": "sha256:4c6abb07c0694cc64ed6425a621ee1a50e2124fca0148133abf65da556b4e4f2",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:4c6abb07c0694cc64ed6425a621ee1a50e2124fca0148133abf65da556b4e4f2"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:reconciliation:6",
      "record_type": "reconciliation",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "reconciliations[0]",
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
      "local_content_commitment": "sha256:b19bbf1f16287405a55d98b864290fa837dc76019a3d4d62083b783e3710e772",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:b19bbf1f16287405a55d98b864290fa837dc76019a3d4d62083b783e3710e772"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:reconciliation:7",
      "record_type": "reconciliation",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "reconciliations[1]",
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
      "local_content_commitment": "sha256:421ac9e34746de614fab63abd46cbef56a5900bf4d38a7f91eb8e56472737b91",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:421ac9e34746de614fab63abd46cbef56a5900bf4d38a7f91eb8e56472737b91"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check:8",
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
      "local_content_commitment": "sha256:de9910c0d5e0988c1ddc478f889b4524df546f87fb0707fc6beb46afd6f879d2",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:de9910c0d5e0988c1ddc478f889b4524df546f87fb0707fc6beb46afd6f879d2"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check:9",
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
      "local_content_commitment": "sha256:89c9e5aeade439182ce60a8a87af4a78fbd8b458611b39250ca89e4db09c84b6",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:89c9e5aeade439182ce60a8a87af4a78fbd8b458611b39250ca89e4db09c84b6"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:attempt_closeout:10",
      "record_type": "attempt_closeout",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "closeouts[0]",
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
      "local_content_commitment": "sha256:bc3c12f99615f3ee17990bd3de9bb02e4726b2a219ea9a56529e5ed971b47a45",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:bc3c12f99615f3ee17990bd3de9bb02e4726b2a219ea9a56529e5ed971b47a45"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:input_time_floors:11",
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
      "local_content_commitment": "sha256:1232f87aa0bfa7ba03d77eaaba2ef2f3f2e2e15e1b0c94da3b2c6f54d711cd6f",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:1232f87aa0bfa7ba03d77eaaba2ef2f3f2e2e15e1b0c94da3b2c6f54d711cd6f"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:12",
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
      "local_content_commitment": "sha256:4a7f745b884dff8753f6b5851b92afe15f9200d47b6f851f127a757f75c29273",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:4a7f745b884dff8753f6b5851b92afe15f9200d47b6f851f127a757f75c29273"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:13",
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
      "local_content_commitment": "sha256:ad82b7a70dd1f5da591b1d75813503c49dff4bce80ec74e38cf5d4cd709e6b99",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:ad82b7a70dd1f5da591b1d75813503c49dff4bce80ec74e38cf5d4cd709e6b99"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:14",
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
      "local_content_commitment": "sha256:4b428697a551bdf0f62a7cf3bf6541512ff46abaf4b5b999ce5d99fa1581e9e1",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:4b428697a551bdf0f62a7cf3bf6541512ff46abaf4b5b999ce5d99fa1581e9e1"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:15",
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
      "local_content_commitment": "sha256:beaa4a8f881e22779f117ca301b26463d11049f91603bb92ebfa5c11fec628d8",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:beaa4a8f881e22779f117ca301b26463d11049f91603bb92ebfa5c11fec628d8"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:16",
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
      "local_content_commitment": "sha256:7bc7c85611d4c253b836544ad9b723e39b74179656453e4058738f3ff9ae37bf",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:7bc7c85611d4c253b836544ad9b723e39b74179656453e4058738f3ff9ae37bf"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:17",
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
      "local_content_commitment": "sha256:37c12c50aca0659e4ad03f2594a3faa062a4357adefbf9f4d58580ab756020ed",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:37c12c50aca0659e4ad03f2594a3faa062a4357adefbf9f4d58580ab756020ed"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:18",
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
      "local_content_commitment": "sha256:a4feb11cc072ceacc4e906475a547a797967e2ba0a69dbae1b7e1df6379cc2e8",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:a4feb11cc072ceacc4e906475a547a797967e2ba0a69dbae1b7e1df6379cc2e8"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:19",
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
      "local_content_commitment": "sha256:ff50dde1246805dcd621cd8dfc6a3f33c2ffb4f830780e16098236efcd8c658d",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:ff50dde1246805dcd621cd8dfc6a3f33c2ffb4f830780e16098236efcd8c658d"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:20",
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
      "local_content_commitment": "sha256:448d9a0ac9f94466540c85bc11dedb698511eb16f5b631ec21b5526062c9c6d7",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:448d9a0ac9f94466540c85bc11dedb698511eb16f5b631ec21b5526062c9c6d7"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:21",
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
      "local_content_commitment": "sha256:b654560737856c675e304c965af13d64af9dc48b40141f1cea1461a9006a9986",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:b654560737856c675e304c965af13d64af9dc48b40141f1cea1461a9006a9986"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:22",
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
      "local_content_commitment": "sha256:d6d5a5e90e48bcc2f72fb794f538ad558e10a65018bff54d5134d28e2a39a410",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:d6d5a5e90e48bcc2f72fb794f538ad558e10a65018bff54d5134d28e2a39a410"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:23",
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
      "local_content_commitment": "sha256:e27b63401874c432d6f8766664d5927e1d3c82662bb89c998f9287557a1e6f27",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:e27b63401874c432d6f8766664d5927e1d3c82662bb89c998f9287557a1e6f27"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:24",
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
      "local_content_commitment": "sha256:6b6d538968e21e66fb625bde9a94446d665d14f6817e69f5a596bad03da71177",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:6b6d538968e21e66fb625bde9a94446d665d14f6817e69f5a596bad03da71177"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:25",
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
      "local_content_commitment": "sha256:a6ca6474137907762d67bfb2d7a0aeb6d45bd6334549b783dbb148eeaf3248fd",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:a6ca6474137907762d67bfb2d7a0aeb6d45bd6334549b783dbb148eeaf3248fd"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:26",
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
      "local_content_commitment": "sha256:66728f9b30093ea8289c3c1c0dbd61dc400e9e0e2e2d4550b50dad1262c6c013",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:66728f9b30093ea8289c3c1c0dbd61dc400e9e0e2e2d4550b50dad1262c6c013"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:27",
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
      "local_content_commitment": "sha256:1b9b47484fe865863be615efde719b9ee644a241573dd64e29b99fcc1e12e0c8",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:1b9b47484fe865863be615efde719b9ee644a241573dd64e29b99fcc1e12e0c8"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:28",
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
      "local_content_commitment": "sha256:524b167d80992abf2efaededbfcefe857a8703b2e030c7f16a7610ebb2118ea9",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:524b167d80992abf2efaededbfcefe857a8703b2e030c7f16a7610ebb2118ea9"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:29",
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
      "local_content_commitment": "sha256:8d46721f1b02ebc7c1fc9bd6a4d26588c7a2e4cae54d8a21d6fd60f982029fae",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:8d46721f1b02ebc7c1fc9bd6a4d26588c7a2e4cae54d8a21d6fd60f982029fae"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:30",
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
      "local_content_commitment": "sha256:3dbba0235508fe22580158cc6ea6c1096fc2d951f74572f67553ec9d869c54e2",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:3dbba0235508fe22580158cc6ea6c1096fc2d951f74572f67553ec9d869c54e2"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:31",
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
      "local_content_commitment": "sha256:91d6ec2891e083514082619f6e240a4378c088567bed75bdcb7be6e8faa6afb9",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:91d6ec2891e083514082619f6e240a4378c088567bed75bdcb7be6e8faa6afb9"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:32",
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
      "local_content_commitment": "sha256:101a89a13768826ac7b79c6b30839c369001ba87136edb3929f19e03e8ca59a7",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:101a89a13768826ac7b79c6b30839c369001ba87136edb3929f19e03e8ca59a7"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:33",
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
      "local_content_commitment": "sha256:04fb70fae9e806c7ac3df0f8d78ced10c8273d192b95c6ed372e002fd5b0e4ab",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:04fb70fae9e806c7ac3df0f8d78ced10c8273d192b95c6ed372e002fd5b0e4ab"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:34",
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
      "local_content_commitment": "sha256:57c4cd322a2c678fd72ee05abef310d781493e7d92a8255b977c5013c858feca",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:57c4cd322a2c678fd72ee05abef310d781493e7d92a8255b977c5013c858feca"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:35",
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
      "local_content_commitment": "sha256:4de316f1bb662ebfc32d1e9912c61e3d1b8c540f2078b5cacaa4b0f2f0b879aa",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:4de316f1bb662ebfc32d1e9912c61e3d1b8c540f2078b5cacaa4b0f2f0b879aa"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:36",
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
      "local_content_commitment": "sha256:2d42f022e933da80401356b08cb48d113f69553fd846e945f369f930d8cb6dda",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:2d42f022e933da80401356b08cb48d113f69553fd846e945f369f930d8cb6dda"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:37",
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
      "local_content_commitment": "sha256:9c7f308132de2b09921ae8a8f03b8eeb7b5e2da85457c6caab25ec244f86d779",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:9c7f308132de2b09921ae8a8f03b8eeb7b5e2da85457c6caab25ec244f86d779"
    },
    {
      "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:execution_envelope:38",
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
      "local_content_commitment": "sha256:31e141b14ba8d7fbc14ebc3bea6f5e8942571c6cf9bf27dfe68f53cf8db953fd",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:31e141b14ba8d7fbc14ebc3bea6f5e8942571c6cf9bf27dfe68f53cf8db953fd"
    },
    {
      "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:executor_control_plane_evidence:39",
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
      "local_content_commitment": "sha256:3a071336105f364fe0861cb2b39b94f07b1671dbeb0cd46423214bb750009337",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:3a071336105f364fe0861cb2b39b94f07b1671dbeb0cd46423214bb750009337"
    },
    {
      "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:execution_result:40",
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
      "local_content_commitment": "sha256:d7534c570c9535a0f2fc481f492f863eff48e08991a2a7dc1fec2df9b34dd0e5",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:d7534c570c9535a0f2fc481f492f863eff48e08991a2a7dc1fec2df9b34dd0e5"
    },
    {
      "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:destination_attempt:41",
      "record_type": "destination_attempt",
      "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1",
      "source_path": "moltbot.attempts[0]",
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
      "local_content_commitment": "sha256:74315cb0bacdf3fb29f0acff4debf0a90d7b1db6a7a2453780b94ab71be2bebe",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:74315cb0bacdf3fb29f0acff4debf0a90d7b1db6a7a2453780b94ab71be2bebe"
    },
    {
      "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:destination_attempt_event:42",
      "record_type": "destination_attempt_event",
      "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1",
      "source_path": "moltbot.attempt_events[0]",
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
      "local_content_commitment": "sha256:8102304c16a5dd36753e8f5e6fda2bb3a90c41066508b55c7bf5cd49bf069626",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:8102304c16a5dd36753e8f5e6fda2bb3a90c41066508b55c7bf5cd49bf069626"
    },
    {
      "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:destination_attempt_event:43",
      "record_type": "destination_attempt_event",
      "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1",
      "source_path": "moltbot.attempt_events[1]",
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
      "local_content_commitment": "sha256:1585adfab369cebeffdbda349891137e6f89530ccf593eef3bca6f12c59ec5fc",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:1585adfab369cebeffdbda349891137e6f89530ccf593eef3bca6f12c59ec5fc"
    },
    {
      "record_id": "control-plane-security-runtime@a34c3dc2:moltbot_attributed_control_plane_attempt:44",
      "record_type": "moltbot_attributed_control_plane_attempt",
      "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
      "source_path": "moltbot.control_plane_attempts[0]",
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
      "local_content_commitment": "sha256:e8aa6dadbed5bc5fb26fa695585dfc62db81c27ac136bc7bb393513292dd98d7",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:e8aa6dadbed5bc5fb26fa695585dfc62db81c27ac136bc7bb393513292dd98d7"
    },
    {
      "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:destination_effect:45",
      "record_type": "destination_effect",
      "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1",
      "source_path": "moltbot.effects[0]",
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
          "label": "operation_digest",
          "value": "sha256:ffcad4c587ea3a81df49e9b2c5d3ee817a929d07356d8704db82c1b9c70af175",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "verification_status": "checked_match",
          "source_path": "moltbot.effects[0].operation_digest",
          "notes": "Checked against the exact retained Execution Envelope operation under the pinned canonicalization profile."
        }
      ],
      "source_content_commitment": "sha256:ffcad4c587ea3a81df49e9b2c5d3ee817a929d07356d8704db82c1b9c70af175",
      "source_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "source_commitment_verification_status": "checked_match",
      "local_content_commitment": "sha256:4dda202a1477299e8b40bb4149eade1d1dd717354321378893560adc9e54f8b6",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:4dda202a1477299e8b40bb4149eade1d1dd717354321378893560adc9e54f8b6"
    },
    {
      "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:executor_observation:46",
      "record_type": "executor_observation",
      "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1",
      "source_path": "moltbot.observations[0]",
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
      "local_content_commitment": "sha256:793b830939f000a3688a95e82de1760521a1eac9e429dcc9826f034af3ef6322",
      "local_canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
      "local_commitment_verification_status": "computed_during_import",
      "hash": "sha256:793b830939f000a3688a95e82de1760521a1eac9e429dcc9826f034af3ef6322"
    }
  ],
  "conversion_losses": [
    {
      "source": "replay_import_report",
      "report_index": 0,
      "finding_index": 0,
      "adapter_profile": "control-plane-security-runtime@a34c3dc2",
      "code": "M002",
      "category": "unsupported_semantic",
      "severity": "warning",
      "path": "attempt_correlation",
      "value_state": "unknown",
      "message": "Control Plane and executor attempt namespaces are preserved separately; no equivalence is inferred."
    },
    {
      "source": "replay_import_report",
      "report_index": 0,
      "finding_index": 1,
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
      "finding_index": 2,
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
    "control_plane_attempt_count": 1,
    "executor_attempt_count": 1,
    "attempt_transition_record_count": 4,
    "destination_effect_count": 1,
    "effect_observation_count": 2,
    "reconciliation_count": 2,
    "destination_observation_counts": {
      "absent": 1,
      "applied": 1
    },
    "destination_effect_state_counts": {
      "applied": 1
    },
    "effect_observation_state_counts": {
      "absent": 1,
      "applied": 1
    },
    "reconciliation_state_counts": {
      "applied": 1,
      "observed_absent": 1
    },
    "execution_result_state_counts": {
      "unknown": 1
    },
    "acknowledgement_counts": {
      "control_plane_unknown": 1,
      "execution_result_unknown": 1
    },
    "acknowledgement_sources": [
      {
        "record_id": "control-plane-security-runtime@a34c3dc2:control_plane_attempt_transition:3",
        "source": "control_plane_transition",
        "state": "unknown",
        "status": "unknown",
        "attempt_id": "d5c548ea-1b55-4755-8dbf-db5ec36e5742"
      },
      {
        "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:execution_result:40",
        "source": "execution_result",
        "state": "unknown",
        "status": "unknown",
        "attempt_id": "a9f08460-cc12-44fe-b6a0-6123f53f398a"
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
    "execution_attempted": "yes",
    "acknowledgement": "unknown",
    "acknowledgement_sources": [
      {
        "record_id": "control-plane-security-runtime@a34c3dc2:control_plane_attempt_transition:3",
        "source": "control_plane_transition",
        "state": "unknown",
        "status": "unknown",
        "attempt_id": "d5c548ea-1b55-4755-8dbf-db5ec36e5742"
      },
      {
        "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:execution_result:40",
        "source": "execution_result",
        "state": "unknown",
        "status": "unknown",
        "attempt_id": "a9f08460-cc12-44fe-b6a0-6123f53f398a"
      }
    ],
    "control_plane_transition_statuses": {
      "attempted": 1,
      "unknown": 1
    },
    "destination_observed": "applied",
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
        "latest_reconciliation": {
          "source_index": 1,
          "result": "applied",
          "observation_accepted": true
        },
        "latest_accepted_observation": {
          "source_index": 1,
          "observation": {
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "observed_at": "2026-10-05T19:00:00+00:00",
            "state": "applied",
            "destination_state": {
              "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
              "state": "applied",
              "grant_id": "urn:cognous:grant:routine-1",
              "target": "urn:cognous:synthetic-account:customer-001",
              "amount": 50.0,
              "unit": "USD",
              "payload": {
                "customer_id": "customer-001",
                "refund_reason": "duplicate"
              },
              "operation_digest": "sha256:ffcad4c587ea3a81df49e9b2c5d3ee817a929d07356d8704db82c1b9c70af175"
            }
          }
        },
        "latest_supported_destination_state": "applied",
        "retry_eligible": false,
        "acknowledgement_history": [
          {
            "source_index": 0,
            "attempt_id": "d5c548ea-1b55-4755-8dbf-db5ec36e5742",
            "status": "attempted",
            "acknowledgement": {}
          },
          {
            "source_index": 1,
            "attempt_id": "d5c548ea-1b55-4755-8dbf-db5ec36e5742",
            "status": "unknown",
            "acknowledgement": {}
          }
        ],
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
      "code": "REPLAY_M002",
      "severity": "warning",
      "path": "attempt_correlation",
      "message": "Control Plane and executor attempt namespaces are preserved separately; no equivalence is inferred.",
      "category": "unsupported_semantic",
      "value_state": "unknown"
    },
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
      "bundle_id": "c3d9c6d6-f375-4868-b73c-b0bd1d5c6a5c",
      "bundle_version": "0.2.0",
      "run_id": "run-1",
      "status": "reconstruction_complete",
      "generated_at": "2026-10-16T19:27:53.045581+00:00",
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
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
          "record_id": "control-plane-security-runtime@a34c3dc2:control_plane_attempt_transition:2",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "control_plane_attempt_transition",
          "source_sequence": 2,
          "source_path": "attempts[0]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "attempt_id": "d5c548ea-1b55-4755-8dbf-db5ec36e5742",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202"
          },
          "evidence_class": "producer_reported",
          "data": {
            "attempt_id": "d5c548ea-1b55-4755-8dbf-db5ec36e5742",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
            "started_at": "2026-10-05T19:00:00+00:00",
            "time_source": "test_override",
            "status": "attempted",
            "acknowledgement": {},
            "error": null
          }
        },
        {
          "record_id": "control-plane-security-runtime@a34c3dc2:control_plane_attempt_transition:3",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "control_plane_attempt_transition",
          "source_sequence": 3,
          "source_path": "attempts[1]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "attempt_id": "d5c548ea-1b55-4755-8dbf-db5ec36e5742",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202"
          },
          "evidence_class": "producer_reported",
          "data": {
            "attempt_id": "d5c548ea-1b55-4755-8dbf-db5ec36e5742",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
            "started_at": "2026-10-05T19:00:00+00:00",
            "time_source": "test_override",
            "status": "unknown",
            "acknowledgement": {},
            "error": "destination_outcome_unknown:TimeoutError"
          }
        },
        {
          "record_id": "control-plane-security-runtime@a34c3dc2:effect_observation:4",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "effect_observation",
          "source_sequence": 4,
          "source_path": "observations[0]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829"
          },
          "evidence_class": "producer_reported",
          "data": {
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "observed_at": "2026-10-05T19:00:00+00:00",
            "state": "absent",
            "destination_state": {}
          }
        },
        {
          "record_id": "control-plane-security-runtime@a34c3dc2:effect_observation:5",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "effect_observation",
          "source_sequence": 5,
          "source_path": "observations[1]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829"
          },
          "evidence_class": "producer_reported",
          "data": {
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "observed_at": "2026-10-05T19:00:00+00:00",
            "state": "applied",
            "destination_state": {
              "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
              "state": "applied",
              "grant_id": "urn:cognous:grant:routine-1",
              "target": "urn:cognous:synthetic-account:customer-001",
              "amount": 50.0,
              "unit": "USD",
              "payload": {
                "customer_id": "customer-001",
                "refund_reason": "duplicate"
              },
              "operation_digest": "sha256:ffcad4c587ea3a81df49e9b2c5d3ee817a929d07356d8704db82c1b9c70af175"
            }
          }
        },
        {
          "record_id": "control-plane-security-runtime@a34c3dc2:reconciliation:6",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "reconciliation",
          "source_sequence": 6,
          "source_path": "reconciliations[0]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829"
          },
          "evidence_class": "producer_reported",
          "data": {
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "reconciled_at": "2026-10-05T19:00:00+00:00",
            "result": "observed_absent",
            "observation": {
              "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
              "observed_at": "2026-10-05T19:00:00+00:00",
              "state": "absent",
              "destination_state": {}
            },
            "observation_accepted": true,
            "retry_eligible": false,
            "reasons": [],
            "evaluation_time": "2026-10-05T19:00:00+00:00",
            "observation_max_age_seconds": 300,
            "observation_clock_tolerance_seconds": 5
          }
        },
        {
          "record_id": "control-plane-security-runtime@a34c3dc2:reconciliation:7",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "reconciliation",
          "source_sequence": 7,
          "source_path": "reconciliations[1]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829"
          },
          "evidence_class": "producer_reported",
          "data": {
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "reconciled_at": "2026-10-05T19:00:00+00:00",
            "result": "applied",
            "observation": {
              "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
              "observed_at": "2026-10-05T19:00:00+00:00",
              "state": "applied",
              "destination_state": {
                "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
                "state": "applied",
                "grant_id": "urn:cognous:grant:routine-1",
                "target": "urn:cognous:synthetic-account:customer-001",
                "amount": 50.0,
                "unit": "USD",
                "payload": {
                  "customer_id": "customer-001",
                  "refund_reason": "duplicate"
                },
                "operation_digest": "sha256:ffcad4c587ea3a81df49e9b2c5d3ee817a929d07356d8704db82c1b9c70af175"
              }
            },
            "observation_accepted": true,
            "retry_eligible": false,
            "reasons": [],
            "evaluation_time": "2026-10-05T19:00:00+00:00",
            "observation_max_age_seconds": 300,
            "observation_clock_tolerance_seconds": 5
          }
        },
        {
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check:8",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check",
          "source_sequence": 8,
          "source_path": "resolution_checks[0]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "6006ee62-ad58-44e3-849c-56a08afd7799"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "6006ee62-ad58-44e3-849c-56a08afd7799",
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check:9",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check",
          "source_sequence": 9,
          "source_path": "resolution_checks[1]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "807bb7e4-0cbc-4a0a-8c22-d1c010db5821"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "807bb7e4-0cbc-4a0a-8c22-d1c010db5821",
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
            "reasons": []
          }
        },
        {
          "record_id": "control-plane-security-runtime@a34c3dc2:attempt_closeout:10",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "attempt_closeout",
          "source_sequence": 10,
          "source_path": "closeouts[0]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "attempt_id": "d5c548ea-1b55-4755-8dbf-db5ec36e5742"
          },
          "evidence_class": "producer_reported",
          "data": {
            "attempt_id": "d5c548ea-1b55-4755-8dbf-db5ec36e5742",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "original_status": "unknown",
            "observed_state": "applied",
            "observed_at": "2026-10-05T19:00:00+00:00",
            "reconciled_at": "2026-10-05T19:00:00+00:00"
          }
        },
        {
          "record_id": "control-plane-security-runtime@a34c3dc2:input_time_floors:11",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "input_time_floors",
          "source_sequence": 11,
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:12",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 12,
          "source_path": "check_events[0]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
            "phase": "opened",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:13",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 13,
          "source_path": "check_events[1]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:14",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 14,
          "source_path": "check_events[2]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:15",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 15,
          "source_path": "check_events[3]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:16",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 16,
          "source_path": "check_events[4]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:17",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 17,
          "source_path": "check_events[5]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:18",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 18,
          "source_path": "check_events[6]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:19",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 19,
          "source_path": "check_events[7]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:20",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 20,
          "source_path": "check_events[8]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:21",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 21,
          "source_path": "check_events[9]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:22",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 22,
          "source_path": "check_events[10]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:23",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 23,
          "source_path": "check_events[11]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
            "phase": "input",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:24",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 24,
          "source_path": "check_events[12]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
            "phase": "completed",
            "stage": "decision",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:25",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 25,
          "source_path": "check_events[13]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
            "phase": "opened",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:26",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 26,
          "source_path": "check_events[14]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:27",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 27,
          "source_path": "check_events[15]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:28",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 28,
          "source_path": "check_events[16]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:29",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 29,
          "source_path": "check_events[17]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:30",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 30,
          "source_path": "check_events[18]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:31",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 31,
          "source_path": "check_events[19]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:32",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 32,
          "source_path": "check_events[20]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:33",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 33,
          "source_path": "check_events[21]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:34",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 34,
          "source_path": "check_events[22]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:35",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 35,
          "source_path": "check_events[23]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:36",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 36,
          "source_path": "check_events[24]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
            "phase": "input",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
          "record_id": "control-plane-security-runtime@a34c3dc2:resolution_check_event:37",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "resolution_check_event",
          "source_sequence": 37,
          "source_path": "check_events[25]",
          "recorded_at": "2026-10-05T19:00:00+00:00",
          "identifiers": {
            "run_id": "run-1",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841"
          },
          "evidence_class": "producer_reported",
          "data": {
            "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
            "phase": "completed",
            "stage": "effect",
            "recorded_at": "2026-10-05T19:00:00+00:00",
            "owner": {
              "pid": "2738",
              "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
            },
            "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
          "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:execution_envelope:38",
          "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1",
          "record_type": "execution_envelope",
          "source_sequence": 38,
          "source_path": "moltbot.execution_envelope",
          "recorded_at": null,
          "identifiers": {
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
          "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:executor_control_plane_evidence:39",
          "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1",
          "record_type": "executor_control_plane_evidence",
          "source_sequence": 39,
          "source_path": "moltbot.control_plane_evidence",
          "recorded_at": null,
          "identifiers": {},
          "evidence_class": "producer_reported",
          "data": {
            "attempt": {
              "attempt_id": "d5c548ea-1b55-4755-8dbf-db5ec36e5742",
              "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
              "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
              "started_at": "2026-10-05T19:00:00+00:00",
              "time_source": "test_override",
              "status": "unknown",
              "acknowledgement": {},
              "error": "destination_outcome_unknown:TimeoutError"
            },
            "reconciliation": {
              "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
              "reconciled_at": "2026-10-05T19:00:00+00:00",
              "result": "applied",
              "observation": {
                "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
                "observed_at": "2026-10-05T19:00:00+00:00",
                "state": "applied",
                "destination_state": {
                  "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
                  "state": "applied",
                  "grant_id": "urn:cognous:grant:routine-1",
                  "target": "urn:cognous:synthetic-account:customer-001",
                  "amount": 50.0,
                  "unit": "USD",
                  "payload": {
                    "customer_id": "customer-001",
                    "refund_reason": "duplicate"
                  },
                  "operation_digest": "sha256:ffcad4c587ea3a81df49e9b2c5d3ee817a929d07356d8704db82c1b9c70af175"
                }
              },
              "observation_accepted": true,
              "retry_eligible": false,
              "reasons": [],
              "evaluation_time": "2026-10-05T19:00:00+00:00",
              "observation_max_age_seconds": 300,
              "observation_clock_tolerance_seconds": 5
            }
          }
        },
        {
          "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:execution_result:40",
          "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1",
          "record_type": "execution_result",
          "source_sequence": 40,
          "source_path": "moltbot.execution_result",
          "recorded_at": null,
          "identifiers": {
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "attempt_id": "a9f08460-cc12-44fe-b6a0-6123f53f398a"
          },
          "evidence_class": "producer_reported",
          "data": {
            "status": "unknown",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "attempt_id": "a9f08460-cc12-44fe-b6a0-6123f53f398a",
            "attempted": true,
            "acknowledged": false,
            "observed_state": "applied",
            "newly_executed": false,
            "observation": {
              "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
              "observed_at": "2026-10-05T19:00:00+00:00",
              "state": "applied",
              "destination_state": {
                "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
                "state": "applied",
                "grant_id": "urn:cognous:grant:routine-1",
                "target": "urn:cognous:synthetic-account:customer-001",
                "amount": 50.0,
                "unit": "USD",
                "payload": {
                  "customer_id": "customer-001",
                  "refund_reason": "duplicate"
                },
                "operation_digest": "sha256:ffcad4c587ea3a81df49e9b2c5d3ee817a929d07356d8704db82c1b9c70af175"
              }
            },
            "error": "destination_outcome_unknown:TimeoutError",
            "control_plane_evidence": {
              "attempt": {
                "attempt_id": "d5c548ea-1b55-4755-8dbf-db5ec36e5742",
                "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
                "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
                "started_at": "2026-10-05T19:00:00+00:00",
                "time_source": "test_override",
                "status": "unknown",
                "acknowledgement": {},
                "error": "destination_outcome_unknown:TimeoutError"
              },
              "reconciliation": {
                "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
                "reconciled_at": "2026-10-05T19:00:00+00:00",
                "result": "applied",
                "observation": {
                  "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
                  "observed_at": "2026-10-05T19:00:00+00:00",
                  "state": "applied",
                  "destination_state": {
                    "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
                    "state": "applied",
                    "grant_id": "urn:cognous:grant:routine-1",
                    "target": "urn:cognous:synthetic-account:customer-001",
                    "amount": 50.0,
                    "unit": "USD",
                    "payload": {
                      "customer_id": "customer-001",
                      "refund_reason": "duplicate"
                    },
                    "operation_digest": "sha256:ffcad4c587ea3a81df49e9b2c5d3ee817a929d07356d8704db82c1b9c70af175"
                  }
                },
                "observation_accepted": true,
                "retry_eligible": false,
                "reasons": [],
                "evaluation_time": "2026-10-05T19:00:00+00:00",
                "observation_max_age_seconds": 300,
                "observation_clock_tolerance_seconds": 5
              }
            }
          }
        },
        {
          "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:destination_attempt:41",
          "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1",
          "record_type": "destination_attempt",
          "source_sequence": 41,
          "source_path": "moltbot.attempts[0]",
          "recorded_at": null,
          "identifiers": {
            "attempt_id": "a9f08460-cc12-44fe-b6a0-6123f53f398a",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202"
          },
          "evidence_class": "producer_reported",
          "data": {
            "attempt_id": "a9f08460-cc12-44fe-b6a0-6123f53f398a",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
            "operation_digest": "sha256:ffcad4c587ea3a81df49e9b2c5d3ee817a929d07356d8704db82c1b9c70af175",
            "created_at": 1792178873.0264566
          }
        },
        {
          "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:destination_attempt_event:42",
          "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1",
          "record_type": "destination_attempt_event",
          "source_sequence": 42,
          "source_path": "moltbot.attempt_events[0]",
          "recorded_at": null,
          "identifiers": {
            "attempt_id": "a9f08460-cc12-44fe-b6a0-6123f53f398a",
            "event_id": "1",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202"
          },
          "evidence_class": "producer_reported",
          "data": {
            "event_id": 1,
            "attempt_id": "a9f08460-cc12-44fe-b6a0-6123f53f398a",
            "status": "attempted",
            "error": null,
            "created_at": 1792178873.027308
          }
        },
        {
          "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:destination_attempt_event:43",
          "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1",
          "record_type": "destination_attempt_event",
          "source_sequence": 43,
          "source_path": "moltbot.attempt_events[1]",
          "recorded_at": null,
          "identifiers": {
            "attempt_id": "a9f08460-cc12-44fe-b6a0-6123f53f398a",
            "event_id": "2",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202"
          },
          "evidence_class": "producer_reported",
          "data": {
            "event_id": 2,
            "attempt_id": "a9f08460-cc12-44fe-b6a0-6123f53f398a",
            "status": "unknown",
            "error": "synthetic acknowledgement unavailable after durable commit",
            "created_at": 1792178873.0288382
          }
        },
        {
          "record_id": "control-plane-security-runtime@a34c3dc2:moltbot_attributed_control_plane_attempt:44",
          "producer_profile_id": "control-plane-security-runtime@a34c3dc2",
          "record_type": "moltbot_attributed_control_plane_attempt",
          "source_sequence": 44,
          "source_path": "moltbot.control_plane_attempts[0]",
          "recorded_at": null,
          "identifiers": {
            "run_id": "run-1",
            "attempt_id": "d5c548ea-1b55-4755-8dbf-db5ec36e5742",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829"
          },
          "evidence_class": "producer_reported",
          "data": {
            "attempt_id": "d5c548ea-1b55-4755-8dbf-db5ec36e5742",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
            "started_at": "2026-10-05T19:00:00+00:00",
            "time_source": "test_override",
            "status": "unknown",
            "acknowledgement": {},
            "error": "destination_outcome_unknown:TimeoutError"
          }
        },
        {
          "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:destination_effect:45",
          "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1",
          "record_type": "destination_effect",
          "source_sequence": 45,
          "source_path": "moltbot.effects[0]",
          "recorded_at": null,
          "identifiers": {
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "grant_id": "urn:cognous:grant:routine-1"
          },
          "evidence_class": "producer_reported",
          "data": {
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "operation_digest": "sha256:ffcad4c587ea3a81df49e9b2c5d3ee817a929d07356d8704db82c1b9c70af175",
            "grant_id": "urn:cognous:grant:routine-1",
            "target": "urn:cognous:synthetic-account:customer-001",
            "amount": 50.0,
            "unit": "USD",
            "payload_json": "{\"customer_id\":\"customer-001\",\"refund_reason\":\"duplicate\"}",
            "state": "applied"
          }
        },
        {
          "record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:executor_observation:46",
          "producer_profile_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1",
          "record_type": "executor_observation",
          "source_sequence": 46,
          "source_path": "moltbot.observations[0]",
          "recorded_at": null,
          "identifiers": {
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829"
          },
          "evidence_class": "producer_reported",
          "data": {
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "observed_at": "2026-10-05T19:00:00+00:00",
            "state": "applied",
            "destination_state": {
              "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
              "state": "applied",
              "grant_id": "urn:cognous:grant:routine-1",
              "target": "urn:cognous:synthetic-account:customer-001",
              "amount": 50.0,
              "unit": "USD",
              "payload": {
                "customer_id": "customer-001",
                "refund_reason": "duplicate"
              },
              "operation_digest": "sha256:ffcad4c587ea3a81df49e9b2c5d3ee817a929d07356d8704db82c1b9c70af175"
            }
          }
        }
      ],
      "links": [
        {
          "link_type": "explicit",
          "from_record_id": "control-plane-security-runtime@a34c3dc2:moltbot_attributed_control_plane_attempt:44",
          "to_record_id": "control-plane-security-runtime@a34c3dc2:control_plane_attempt_transition:3",
          "basis": "Producer-supplied Control Plane attempt evidence exactly matches the retained Control Plane run record.",
          "establishes_identity_equivalence": true
        }
      ],
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
          "source_record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:execution_envelope:38",
          "source_path": "moltbot.execution_envelope.operation.payload_commitment",
          "verification_status": "checked_match",
          "notes": null
        },
        {
          "label": "operation_digest",
          "value": "sha256:ffcad4c587ea3a81df49e9b2c5d3ee817a929d07356d8704db82c1b9c70af175",
          "algorithm": "SHA-256",
          "canonicalization_profile": "json-sort-keys-compact-utf8-no-nan",
          "source_record_id": "moltbot-safe-executor-producer-2.0.0@e20f92e1:destination_effect:45",
          "source_path": "moltbot.effects[0].operation_digest",
          "verification_status": "checked_match",
          "notes": "Checked against the exact retained Execution Envelope operation under the pinned canonicalization profile."
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
              "code": "M002",
              "category": "unsupported_semantic",
              "severity": "warning",
              "path": "attempt_correlation",
              "message": "Control Plane and executor attempt namespaces are preserved separately; no equivalence is inferred.",
              "value_state": "unknown"
            },
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
            "latest_reconciliation": {
              "source_index": 1,
              "result": "applied",
              "observation_accepted": true
            },
            "latest_accepted_observation": {
              "source_index": 1,
              "observation": {
                "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
                "observed_at": "2026-10-05T19:00:00+00:00",
                "state": "applied",
                "destination_state": {
                  "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
                  "state": "applied",
                  "grant_id": "urn:cognous:grant:routine-1",
                  "target": "urn:cognous:synthetic-account:customer-001",
                  "amount": 50.0,
                  "unit": "USD",
                  "payload": {
                    "customer_id": "customer-001",
                    "refund_reason": "duplicate"
                  },
                  "operation_digest": "sha256:ffcad4c587ea3a81df49e9b2c5d3ee817a929d07356d8704db82c1b9c70af175"
                }
              }
            },
            "latest_supported_destination_state": "applied",
            "retry_eligible": false,
            "acknowledgement_history": [
              {
                "source_index": 0,
                "attempt_id": "d5c548ea-1b55-4755-8dbf-db5ec36e5742",
                "status": "attempted",
                "acknowledgement": {}
              },
              {
                "source_index": 1,
                "attempt_id": "d5c548ea-1b55-4755-8dbf-db5ec36e5742",
                "status": "unknown",
                "acknowledgement": {}
              }
            ],
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
        "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
    "control_plane_attempt_transition": [
      {
        "attempt_id": "d5c548ea-1b55-4755-8dbf-db5ec36e5742",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
        "started_at": "2026-10-05T19:00:00+00:00",
        "time_source": "test_override",
        "status": "attempted",
        "acknowledgement": {},
        "error": null
      },
      {
        "attempt_id": "d5c548ea-1b55-4755-8dbf-db5ec36e5742",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
        "started_at": "2026-10-05T19:00:00+00:00",
        "time_source": "test_override",
        "status": "unknown",
        "acknowledgement": {},
        "error": "destination_outcome_unknown:TimeoutError"
      }
    ],
    "effect_observation": [
      {
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "observed_at": "2026-10-05T19:00:00+00:00",
        "state": "absent",
        "destination_state": {}
      },
      {
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "observed_at": "2026-10-05T19:00:00+00:00",
        "state": "applied",
        "destination_state": {
          "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
          "state": "applied",
          "grant_id": "urn:cognous:grant:routine-1",
          "target": "urn:cognous:synthetic-account:customer-001",
          "amount": 50.0,
          "unit": "USD",
          "payload": {
            "customer_id": "customer-001",
            "refund_reason": "duplicate"
          },
          "operation_digest": "sha256:ffcad4c587ea3a81df49e9b2c5d3ee817a929d07356d8704db82c1b9c70af175"
        }
      }
    ],
    "reconciliation": [
      {
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "reconciled_at": "2026-10-05T19:00:00+00:00",
        "result": "observed_absent",
        "observation": {
          "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
          "observed_at": "2026-10-05T19:00:00+00:00",
          "state": "absent",
          "destination_state": {}
        },
        "observation_accepted": true,
        "retry_eligible": false,
        "reasons": [],
        "evaluation_time": "2026-10-05T19:00:00+00:00",
        "observation_max_age_seconds": 300,
        "observation_clock_tolerance_seconds": 5
      },
      {
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "reconciled_at": "2026-10-05T19:00:00+00:00",
        "result": "applied",
        "observation": {
          "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
          "observed_at": "2026-10-05T19:00:00+00:00",
          "state": "applied",
          "destination_state": {
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "state": "applied",
            "grant_id": "urn:cognous:grant:routine-1",
            "target": "urn:cognous:synthetic-account:customer-001",
            "amount": 50.0,
            "unit": "USD",
            "payload": {
              "customer_id": "customer-001",
              "refund_reason": "duplicate"
            },
            "operation_digest": "sha256:ffcad4c587ea3a81df49e9b2c5d3ee817a929d07356d8704db82c1b9c70af175"
          }
        },
        "observation_accepted": true,
        "retry_eligible": false,
        "reasons": [],
        "evaluation_time": "2026-10-05T19:00:00+00:00",
        "observation_max_age_seconds": 300,
        "observation_clock_tolerance_seconds": 5
      }
    ],
    "resolution_check": [
      {
        "check_id": "6006ee62-ad58-44e3-849c-56a08afd7799",
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
        "check_id": "807bb7e4-0cbc-4a0a-8c22-d1c010db5821",
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
        "reasons": []
      }
    ],
    "attempt_closeout": [
      {
        "attempt_id": "d5c548ea-1b55-4755-8dbf-db5ec36e5742",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "original_status": "unknown",
        "observed_state": "applied",
        "observed_at": "2026-10-05T19:00:00+00:00",
        "reconciled_at": "2026-10-05T19:00:00+00:00"
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
        "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
        "phase": "opened",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
        "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
        "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
        "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
        "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
        "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
        "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
        "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
        "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
        "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
        "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
        "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
        "phase": "input",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
        "check_id": "808e45fd-111e-4eb0-9787-55352a6f6100",
        "phase": "completed",
        "stage": "decision",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "f11e1266-6c11-4a76-8ecf-18a0eefa953a"
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
        "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
        "phase": "opened",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
        "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
        "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
        "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
        "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
        "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
        "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
        "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
        "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
        "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
        "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
        "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
        "phase": "input",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
        "check_id": "7b0fbd70-13c2-4f0f-a341-58f5da536841",
        "phase": "completed",
        "stage": "effect",
        "recorded_at": "2026-10-05T19:00:00+00:00",
        "owner": {
          "pid": "2738",
          "token": "70cfc4f9-f6ff-4be8-ae48-fe4b331069e5"
        },
        "proposal_commitment": "sha256:133c4baa21d85e41ae7f75af45a96810aa1a175ee3e693913585568630aea96b",
        "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
    ],
    "execution_envelope": [
      {
        "version": "0.2.0",
        "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
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
        "attempt": {
          "attempt_id": "d5c548ea-1b55-4755-8dbf-db5ec36e5742",
          "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
          "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
          "started_at": "2026-10-05T19:00:00+00:00",
          "time_source": "test_override",
          "status": "unknown",
          "acknowledgement": {},
          "error": "destination_outcome_unknown:TimeoutError"
        },
        "reconciliation": {
          "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
          "reconciled_at": "2026-10-05T19:00:00+00:00",
          "result": "applied",
          "observation": {
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "observed_at": "2026-10-05T19:00:00+00:00",
            "state": "applied",
            "destination_state": {
              "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
              "state": "applied",
              "grant_id": "urn:cognous:grant:routine-1",
              "target": "urn:cognous:synthetic-account:customer-001",
              "amount": 50.0,
              "unit": "USD",
              "payload": {
                "customer_id": "customer-001",
                "refund_reason": "duplicate"
              },
              "operation_digest": "sha256:ffcad4c587ea3a81df49e9b2c5d3ee817a929d07356d8704db82c1b9c70af175"
            }
          },
          "observation_accepted": true,
          "retry_eligible": false,
          "reasons": [],
          "evaluation_time": "2026-10-05T19:00:00+00:00",
          "observation_max_age_seconds": 300,
          "observation_clock_tolerance_seconds": 5
        }
      }
    ],
    "execution_result": [
      {
        "status": "unknown",
        "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "attempt_id": "a9f08460-cc12-44fe-b6a0-6123f53f398a",
        "attempted": true,
        "acknowledged": false,
        "observed_state": "applied",
        "newly_executed": false,
        "observation": {
          "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
          "observed_at": "2026-10-05T19:00:00+00:00",
          "state": "applied",
          "destination_state": {
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "state": "applied",
            "grant_id": "urn:cognous:grant:routine-1",
            "target": "urn:cognous:synthetic-account:customer-001",
            "amount": 50.0,
            "unit": "USD",
            "payload": {
              "customer_id": "customer-001",
              "refund_reason": "duplicate"
            },
            "operation_digest": "sha256:ffcad4c587ea3a81df49e9b2c5d3ee817a929d07356d8704db82c1b9c70af175"
          }
        },
        "error": "destination_outcome_unknown:TimeoutError",
        "control_plane_evidence": {
          "attempt": {
            "attempt_id": "d5c548ea-1b55-4755-8dbf-db5ec36e5742",
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
            "started_at": "2026-10-05T19:00:00+00:00",
            "time_source": "test_override",
            "status": "unknown",
            "acknowledgement": {},
            "error": "destination_outcome_unknown:TimeoutError"
          },
          "reconciliation": {
            "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
            "reconciled_at": "2026-10-05T19:00:00+00:00",
            "result": "applied",
            "observation": {
              "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
              "observed_at": "2026-10-05T19:00:00+00:00",
              "state": "applied",
              "destination_state": {
                "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
                "state": "applied",
                "grant_id": "urn:cognous:grant:routine-1",
                "target": "urn:cognous:synthetic-account:customer-001",
                "amount": 50.0,
                "unit": "USD",
                "payload": {
                  "customer_id": "customer-001",
                  "refund_reason": "duplicate"
                },
                "operation_digest": "sha256:ffcad4c587ea3a81df49e9b2c5d3ee817a929d07356d8704db82c1b9c70af175"
              }
            },
            "observation_accepted": true,
            "retry_eligible": false,
            "reasons": [],
            "evaluation_time": "2026-10-05T19:00:00+00:00",
            "observation_max_age_seconds": 300,
            "observation_clock_tolerance_seconds": 5
          }
        }
      }
    ],
    "destination_attempt": [
      {
        "attempt_id": "a9f08460-cc12-44fe-b6a0-6123f53f398a",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
        "operation_digest": "sha256:ffcad4c587ea3a81df49e9b2c5d3ee817a929d07356d8704db82c1b9c70af175",
        "created_at": 1792178873.0264566
      }
    ],
    "destination_attempt_event": [
      {
        "event_id": 1,
        "attempt_id": "a9f08460-cc12-44fe-b6a0-6123f53f398a",
        "status": "attempted",
        "error": null,
        "created_at": 1792178873.027308
      },
      {
        "event_id": 2,
        "attempt_id": "a9f08460-cc12-44fe-b6a0-6123f53f398a",
        "status": "unknown",
        "error": "synthetic acknowledgement unavailable after durable commit",
        "created_at": 1792178873.0288382
      }
    ],
    "moltbot_attributed_control_plane_attempt": [
      {
        "attempt_id": "d5c548ea-1b55-4755-8dbf-db5ec36e5742",
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "decision_id": "2340e937-5e8d-43d2-8a1c-33c1c543a202",
        "started_at": "2026-10-05T19:00:00+00:00",
        "time_source": "test_override",
        "status": "unknown",
        "acknowledgement": {},
        "error": "destination_outcome_unknown:TimeoutError"
      }
    ],
    "destination_effect": [
      {
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "operation_digest": "sha256:ffcad4c587ea3a81df49e9b2c5d3ee817a929d07356d8704db82c1b9c70af175",
        "grant_id": "urn:cognous:grant:routine-1",
        "target": "urn:cognous:synthetic-account:customer-001",
        "amount": 50.0,
        "unit": "USD",
        "payload_json": "{\"customer_id\":\"customer-001\",\"refund_reason\":\"duplicate\"}",
        "state": "applied"
      }
    ],
    "executor_observation": [
      {
        "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
        "observed_at": "2026-10-05T19:00:00+00:00",
        "state": "applied",
        "destination_state": {
          "effect_id": "sha256:d19d83b15e0ec164f3da356fe7a1ecef64734724d7fd65265e91e95f2ffe2829",
          "state": "applied",
          "grant_id": "urn:cognous:grant:routine-1",
          "target": "urn:cognous:synthetic-account:customer-001",
          "amount": 50.0,
          "unit": "USD",
          "payload": {
            "customer_id": "customer-001",
            "refund_reason": "duplicate"
          },
          "operation_digest": "sha256:ffcad4c587ea3a81df49e9b2c5d3ee817a929d07356d8704db82c1b9c70af175"
        }
      }
    ]
  },
  "explicit_links": [
    {
      "link_type": "explicit",
      "from_record_id": "control-plane-security-runtime@a34c3dc2:moltbot_attributed_control_plane_attempt:44",
      "to_record_id": "control-plane-security-runtime@a34c3dc2:control_plane_attempt_transition:3",
      "basis": "Producer-supplied Control Plane attempt evidence exactly matches the retained Control Plane run record.",
      "establishes_identity_equivalence": true
    }
  ],
  "reconstruction_completeness": "reconstruction_complete",
  "refusal_vocabulary_summary": {
    "total_refusals": 0,
    "series": [],
    "prior_window": "unavailable",
    "disappearance_assessed": false,
    "limitation": "source-record counts; exposure and collection completeness not independently established"
  }
}</pre>
