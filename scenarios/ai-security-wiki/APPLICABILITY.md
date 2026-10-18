<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->
# Scenario applicability classification

Classification of all 656 imported AI Security Wiki specifications against the declared scope of the Open Control Stack. Machine-readable: [applicability.json](applicability.json). Case IDs and titles come from the AI Security Wiki by **Nachiket Sathaye** (contributor credited upstream: Ankush Jain), commit `1a0c72de4752a1c6932172e5e7dbf14f755799c8`, licensed CC BY-SA 4.0 ([license](LICENSE)). This file adds classification only; `catalog.json` and the case pages are unchanged. No upstream endorsement is implied.

**Basis.** Applicability follows only from the declared scope and interfaces: the supported claim (trusted-host synthetic local SQLite refund, bounded tenant/grant/approval/policy checks, durable typed refusal and lost acknowledgement, local stop journal and reconciliation, non-authorizing Replay/Evidence lineage) and the explicit exclusions in the hub. It was fixed before any result was consulted. It is not a verdict, a score or a coverage claim; every case stays NOT RUN.

## Classes

| Class | Meaning |
|---|---|
| APPLICABLE | tests a declared OCS capability; may be a subset (scope_extent) |
| PARTLY_COVERED | only a subset is in scope and an existing test covers it (paths named) |
| NOT_APPLICABLE | tests a layer or capability OCS does not claim |

## Counts by class

| Class | Cases |
|---|---:|
| APPLICABLE | 20 |
| PARTLY_COVERED | 45 |
| NOT_APPLICABLE | 591 |
| Total | 656 |

## Counts by layer

| Layer | Cases | APPLICABLE | PARTLY_COVERED | NOT_APPLICABLE |
|---|---:|---:|---:|---:|
| D08 | 25 | 0 | 0 | 25 |
| D09 | 20 | 0 | 4 | 16 |
| D10 | 23 | 0 | 0 | 23 |
| D11 | 22 | 0 | 0 | 22 |
| D12 | 22 | 2 | 2 | 18 |
| D13 | 21 | 0 | 1 | 20 |
| L01 | 20 | 0 | 0 | 20 |
| L02 | 25 | 2 | 2 | 21 |
| L03 | 42 | 1 | 0 | 41 |
| L04 | 32 | 0 | 0 | 32 |
| L05 | 35 | 2 | 2 | 31 |
| L06 | 46 | 8 | 16 | 22 |
| L07 | 41 | 0 | 4 | 37 |
| L08 | 42 | 0 | 2 | 40 |
| L09 | 26 | 2 | 6 | 18 |
| L10 | 33 | 0 | 0 | 33 |
| L11 | 25 | 0 | 0 | 25 |
| L12 | 31 | 0 | 0 | 31 |
| L13 | 26 | 0 | 0 | 26 |
| L14 | 22 | 0 | 0 | 22 |
| L15 | 20 | 0 | 1 | 19 |
| L16 | 26 | 0 | 2 | 24 |
| L17 | 31 | 3 | 3 | 25 |

## Individual-component vs cross-component split

Applies to APPLICABLE and PARTLY_COVERED cases. A case is cross-component when it needs two or more OCS components working together. Testing-hub inventory: synthetic individual-component tests, synthetic cross-component tests, and Wiki-derived tests (this split).

| Class | Individual-component | Cross-component | Total |
|---|---:|---:|---:|
| APPLICABLE | 2 | 18 | 20 |
| PARTLY_COVERED | 15 | 30 | 45 |
| Both | 17 | 48 | 65 |

Cases touching each component:

| Component | Cases |
|---|---:|
| action-manifest | 8 |
| control-plane | 47 |
| evidence-pack | 6 |
| execution-runtime | 35 |
| governed-exchange | 11 |
| odes | 2 |
| replay-bundle | 14 |
| verifier | 6 |

Implementation: 4 APPLICABLE cases have no existing test and need new implementation; the other APPLICABLE cases have an existing test covering part of them (listed per case), with the remainder still new.

## Applicable and partly covered cases

| ID | Class | Split | Components | Destination | Existing tests | Note |
|---|---|---|---|---|---|---|
| TC-D09-004 Agent Identity Risk Tiering and Privilege Classes | PARTLY_COVERED | individual-component | control-plane | no destination (synthetic record, bundle or manifest files only) | `suites/v1-probes/test_authority_probes.py` | authority tiers T0-T4 exist; agent population tiering does not **Close call.** |
| TC-D09-009 Time-Bound and Just-in-Time Elevation for Agents | PARTLY_COVERED | cross-component | control-plane, execution-runtime | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_asw_i.py`, `suites/v1-probes/test_authority_ra_probes.py` | grant expiry at use time only; no elevation workflow |
| TC-D09-011 Delegation Records and Consent Evidence | PARTLY_COVERED | individual-component | control-plane | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_scn_c18.py` | bounded delegation only; consent evidence export not claimed |
| TC-D09-016 Revocation Propagation Time Across Systems | PARTLY_COVERED | cross-component | control-plane, execution-runtime | route-A (effective-grant synthetic SQLite refund destination) ; route-B (atomic-claim synthetic SQLite refund destination) | `suites/v1-scenarios/test_scn_c07.py`, `suites/v1-scenarios/test_scn_d09.py`, `suites/v1-scenarios/test_asw_i.py` | local grant revocation before dispatch/commit; cross-system propagation excluded **Close call.** |
| TC-D12-004 Preserving AI System State at Incident Time: Model, Prompt, Configuration, Tools and Policy | APPLICABLE | cross-component | control-plane, replay-bundle, evidence-pack | no destination (synthetic record, bundle or manifest files only) | none (new) | policy, grant, manifest and decision inputs at decision time only **Close call.** |
| TC-D12-007 Deterministic Replay: Reproducing an Incident with Pinned Versions and Recorded Inputs | PARTLY_COVERED | cross-component | replay-bundle, control-plane | no destination (synthetic record, bundle or manifest files only) | `suites/v1-probes/test_replay_probes.py`, `suites/v1-scenarios/test_scn_c12.py` | replay reconstructs the record and does not re-execute or re-evaluate **Close call.** |
| TC-D12-018 Evidence Handling for AI Artefacts and Chain of Custody | APPLICABLE | cross-component | replay-bundle, evidence-pack, verifier | no destination (synthetic record, bundle or manifest files only) | `suites/v1-scenarios/test_asw_s.py`, `suites/v1-scenarios/test_scn_c13.py` | hashing and altered-item detection in scope; access logging and custody workflow not |
| TC-D12-021 Near-Miss and Blocked-Attack Learning | PARTLY_COVERED | cross-component | control-plane, replay-bundle, execution-runtime | route-A (effective-grant synthetic SQLite refund destination) | `suites/cognous-execution-runtime/tests/test_w2_refusal_history.py`, `suites/cognous-replay-bundle/tests/test_refusal_evidence.py` | refusal evidence retention only; clustering and improvement loop out of scope **Close call.** |
| TC-D13-003 Budget Hierarchy and Enforcement: Organisation, Team, Application, User and Key | PARTLY_COVERED | cross-component | execution-runtime, control-plane | route-A (effective-grant synthetic SQLite refund destination) ; route-B (atomic-claim synthetic SQLite refund destination) | `suites/v1-probes/test_runtime_probes.py`, `suites/v1-scenarios/test_scn_c16.py` | effect budgets, not model spend budgets **Close call.** |
| TC-L02-002 Policy-to-Control Mapping | PARTLY_COVERED | individual-component | control-plane | no destination (synthetic record, bundle or manifest files only) | `suites/v1-probes/test_authority_probes.py` | ER031 provision-to-control mapping rows **Close call.** |
| TC-L02-011 Exception Expiry Enforced in Technical Controls | PARTLY_COVERED | cross-component | control-plane, execution-runtime | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_asw_i.py`, `suites/v1-probes/test_authority_ra_probes.py` | grant expiry is the only exception-like control **Close call.** |
| TC-L02-016 Audit Readiness: Evidence Pack on Demand | APPLICABLE | cross-component | evidence-pack, replay-bundle | no destination (synthetic record, bundle or manifest files only) | none (new) | generate and verify a pack for a sampled period **Close call.** |
| TC-L02-025 Governance Record Integrity: Change History and Tamper Evidence | APPLICABLE | cross-component | control-plane, verifier | no destination (synthetic record, bundle or manifest files only) | `suites/v1-scenarios/test_scn_d08.py`, `suites/verifier-mutation` | no role model; tamper detection by verifier only; single-row deletion limit documented |
| TC-L03-022 Compliance Evidence Export: Formats, Signing and Integrity | APPLICABLE | cross-component | replay-bundle, evidence-pack, odes | no destination (synthetic record, bundle or manifest files only) | `suites/v1-scenarios/test_scn_c13.py`, `suites/v1-scenarios/test_scn_c14.py`, `suites/v1-scenarios/test_scn_c12.py` | only formats OCS offers: replay, pack, ODES |
| TC-L05-012 Runtime Protection Coverage Verification | PARTLY_COVERED | individual-component | execution-runtime | route-A (effective-grant synthetic SQLite refund destination) ; route-B (atomic-claim synthetic SQLite refund destination) | `suites/v1-scenarios/test_scn_d09.py` | static discovery of destination-mutating routes **Close call.** |
| TC-L05-013 Runtime Protection Fail-Open vs Fail-Closed Behaviour | APPLICABLE | cross-component | control-plane, execution-runtime | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_scn_c06.py`, `suites/v1-probes/test_authority_ra_probes.py` | fail-closed branch only **Close call.** |
| TC-L05-022 Structured Output and Function-Call Argument Validation | APPLICABLE | cross-component | action-manifest, control-plane | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_asw_a.py`, `suites/fix2-probes/test_manifest_probes.py` |  |
| TC-L05-028 Per-Application Policy as Code | PARTLY_COVERED | individual-component | control-plane | no destination (synthetic record, bundle or manifest files only) | `suites/v1-probes/test_rule_revision_probes.py` | policy revision signing and digest checks **Close call.** |
| TC-L06-003 Shadow Agent Detection (Unregistered and Local Agents) | PARTLY_COVERED | cross-component | governed-exchange, execution-runtime | route-C (local durable exchange transport with synthetic refund destination) | `suites/v1-scenarios/test_asw_a.py` | unregistered agent refused; discovery sensor not claimed |
| TC-L06-007 MCP Tool Description Poisoning | PARTLY_COVERED | cross-component | action-manifest, control-plane | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_asw_a.py` | descriptions stay data; no MCP server in scope |
| TC-L06-008 MCP Rug-Pull: Tool Definition Change After Approval | PARTLY_COVERED | cross-component | action-manifest, control-plane | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_scn_c02.py`, `suites/v1-scenarios/test_scn_d02.py`, `suites/v1-scenarios/test_asw_a.py` | manifest version/digest change refused; MCP rug-pull itself not modelled |
| TC-L06-009 MCP Tool Shadowing and Name Collision | PARTLY_COVERED | cross-component | action-manifest, execution-runtime | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_asw_a.py` | adapter binding must match; no MCP registry |
| TC-L06-011 MCP Gateway Policy: Per-Tool Allow and Deny | PARTLY_COVERED | cross-component | action-manifest, execution-runtime | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-probes/test_runtime_probes.py`, `suites/v1-scenarios/test_asw_a.py` | manifest and executor allow-list, not an MCP gateway **Close call.** |
| TC-L06-013 Least-Privilege Tool Allow-Listing Per Agent | APPLICABLE | cross-component | action-manifest, control-plane, execution-runtime | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_asw_a.py`, `suites/v1-probes/test_runtime_probes.py` |  |
| TC-L06-014 Tool Call Argument Validation and Parameter-Level Policy | APPLICABLE | cross-component | action-manifest, control-plane, execution-runtime | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_asw_a.py`, `suites/fix2-probes/test_manifest_probes.py` |  |
| TC-L06-015 High-Risk Action Approval (Human in the Loop) | APPLICABLE | cross-component | control-plane, execution-runtime | route-A (effective-grant synthetic SQLite refund destination) ; route-C (local durable exchange transport with synthetic refund destination) | `suites/v1-scenarios/test_asw_p.py`, `suites/v1-scenarios/test_asw_i.py` | approver display and human review excluded; hold, rejection and expiry checks in scope |
| TC-L06-016 Approval Fatigue and Approval Bypass Resistance | PARTLY_COVERED | cross-component | execution-runtime, control-plane | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-probes/test_runtime_probes.py`, `suites/v1-scenarios/test_asw_p.py` | aggregate effect budget and missing-approval refusal; fatigue is human and excluded **Close call.** |
| TC-L06-017 Delegation Chains: Sub-Agent Authority Attenuation | PARTLY_COVERED | individual-component | control-plane | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_scn_c18.py` | delegated grant naming a parent is refused; no ancestor walk |
| TC-L06-018 Agent-to-Agent Message Authenticity | APPLICABLE | individual-component | governed-exchange | route-C (local durable exchange transport with synthetic refund destination) | `suites/v1-scenarios/test_asw_s.py`, `suites/cognous-governed-exchange/tests/test_gax_imx_redelivery.py` | forged, modified and replayed message variants beyond the existing tamper cases need adding |
| TC-L06-019 Confused Deputy: Agent Acting Beyond the User's Intent | PARTLY_COVERED | cross-component | control-plane, execution-runtime | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_scn_d02.py`, `suites/v1-scenarios/test_asw_i.py`, `suites/v1-scenarios/test_asw_a.py` | authority from trusted resolver, not from the request |
| TC-L06-020 Cross-Agent Prompt Injection Propagation | PARTLY_COVERED | cross-component | governed-exchange, control-plane, execution-runtime | route-C (local durable exchange transport with synthetic refund destination) | `suites/v1-scenarios/test_asw_p.py` | hostile message content cannot authorize an effect; propagation between agents not modelled **Close call.** |
| TC-L06-022 Kill Switch: Stopping a Single Agent | PARTLY_COVERED | individual-component | execution-runtime | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_scn_d09.py`, `suites/cognous-execution-runtime/tests/test_w2_stop_recovery.py`, `suites/cognous-execution-runtime/tests/test_w3_c8_actual_stop.py` | local stop journal only; generalized all-path stop excluded **Close call.** |
| TC-L06-023 Kill Switch: Global Credential Revocation and Action Rollback | PARTLY_COVERED | cross-component | control-plane, execution-runtime | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_scn_c07.py`, `suites/v1-scenarios/test_asw_i.py` | local grant revocation only; rollback excluded **Close call.** |
| TC-L06-024 Action Rate Limits and Blast-Radius Caps | PARTLY_COVERED | individual-component | execution-runtime | route-A (effective-grant synthetic SQLite refund destination) ; route-B (atomic-claim synthetic SQLite refund destination) | `suites/v1-probes/test_runtime_probes.py`, `suites/v1-scenarios/test_scn_c16.py` | cumulative effect budget; no alert at 80 percent **Close call.** |
| TC-L06-026 Agent Runtime File and Network Egress Restrictions | PARTLY_COVERED | individual-component | execution-runtime | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_scn_c10.py`, `suites/v1-probes/test_runtime_probes.py` | database-path confinement; egress assurance excluded **Close call.** |
| TC-L06-028 Agent Action Logging and Replayable Traces | APPLICABLE | cross-component | control-plane, replay-bundle, verifier | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_scn_c12.py`, `suites/v1-scenarios/test_scn_d08.py` | no LLM turns; effect lineage only |
| TC-L06-034 Agent Change Control and Re-Approval | PARTLY_COVERED | cross-component | action-manifest, control-plane | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_scn_c02.py`, `suites/v1-probes/test_rule_revision_probes.py` | manifest/policy revision refused until signed; agent component change control not claimed |
| TC-L06-038 Agent Trust Map: Permitted Agent-to-Agent Relationships | PARTLY_COVERED | individual-component | governed-exchange | route-C (local durable exchange transport with synthetic refund destination) | `suites/v1-scenarios/test_asw_a.py` | recipient/registry binding in the local registry **Close call.** |
| TC-L06-039 Inter-Agent Request Authorisation: Low-Trust Agent Instructing a High-Trust Agent | APPLICABLE | cross-component | governed-exchange, control-plane, execution-runtime | route-C (local durable exchange transport with synthetic refund destination) | none (new) | caller and originating-user evaluation through trusted resolver; low/high-trust agent roles are fixture identities |
| TC-L06-040 Inter-Agent Message Schema and Content Validation | APPLICABLE | individual-component | governed-exchange | route-C (local durable exchange transport with synthetic refund destination) | `suites/v1-scenarios/test_asw_s.py` | invalid-message set (schema, version mismatch) needs adding |
| TC-L06-041 Agent Discovery and Agent Card Spoofing | PARTLY_COVERED | individual-component | governed-exchange | route-C (local durable exchange transport with synthetic refund destination) | `suites/v1-scenarios/test_asw_a.py` | rogue sender/recipient refused by local registry; directory discovery not claimed **Close call.** |
| TC-L06-045 Inter-Agent Request Logging and Cross-Agent Trace Correlation | APPLICABLE | cross-component | governed-exchange, control-plane, replay-bundle | route-C (local durable exchange transport with synthetic refund destination) | none (new) | one correlation identifier across exchange, decision, effect and replay **Close call.** |
| TC-L07-008 Direct Injection Leading to Unauthorised Tool Action | PARTLY_COVERED | cross-component | control-plane, execution-runtime | route-A (effective-grant synthetic SQLite refund destination) ; route-C (local durable exchange transport with synthetic refund destination) | `suites/v1-scenarios/test_asw_p.py`, `suites/v1-scenarios/test_asw_a.py` | only the part where injected instructions cannot authorize an effect; content neutralisation and detection are not claimed **Close call.** |
| TC-L07-009 Indirect Injection: Web Page Content | PARTLY_COVERED | cross-component | governed-exchange, control-plane, execution-runtime | route-A (effective-grant synthetic SQLite refund destination) ; route-C (local durable exchange transport with synthetic refund destination) | `suites/v1-scenarios/test_asw_p.py`, `suites/v1-scenarios/test_asw_a.py` | only the part where injected instructions cannot authorize an effect; content neutralisation and detection are not claimed **Close call.** |
| TC-L07-012 Indirect Injection: Retrieved Knowledge Base Documents | PARTLY_COVERED | cross-component | governed-exchange, control-plane, execution-runtime | route-A (effective-grant synthetic SQLite refund destination) ; route-C (local durable exchange transport with synthetic refund destination) | `suites/v1-scenarios/test_asw_p.py`, `suites/v1-scenarios/test_asw_a.py` | only the part where injected instructions cannot authorize an effect; content neutralisation and detection are not claimed **Close call.** |
| TC-L07-013 Indirect Injection: Tool and API Responses | PARTLY_COVERED | cross-component | governed-exchange, control-plane, execution-runtime | route-A (effective-grant synthetic SQLite refund destination) ; route-C (local durable exchange transport with synthetic refund destination) | `suites/v1-scenarios/test_asw_p.py`, `suites/v1-scenarios/test_asw_a.py` | only the part where injected instructions cannot authorize an effect; content neutralisation and detection are not claimed **Close call.** |
| TC-L08-033 Throughput and Behaviour at Peak Load | PARTLY_COVERED | individual-component | execution-runtime | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_scn_d06.py` | ingress pressure on OCS surfaces, not gateway throughput **Close call.** |
| TC-L08-036 Policy Change Propagation and Rollback | PARTLY_COVERED | individual-component | control-plane | no destination (synthetic record, bundle or manifest files only) | `suites/v1-probes/test_rule_revision_probes.py`, `suites/v1-scenarios/test_asw_i.py` | policy revision effect and unsigned-revision refusal; cross-component propagation timing not claimed **Close call.** |
| TC-L09-003 Short-Lived Scoped Credentials for Agents | PARTLY_COVERED | cross-component | control-plane, execution-runtime | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_asw_i.py` | grant validity window, not credential issuance |
| TC-L09-004 Token Scope Enforcement Per Tool and Resource | APPLICABLE | cross-component | control-plane, execution-runtime | route-A (effective-grant synthetic SQLite refund destination) ; route-B (atomic-claim synthetic SQLite refund destination) | `suites/v1-probes/test_runtime_probes.py`, `suites/v1-scenarios/test_scn_c11.py` |  |
| TC-L09-006 Delegated User Identity Propagation (On-Behalf-Of) | PARTLY_COVERED | cross-component | control-plane, execution-runtime | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_scn_d02.py` | actor/principal binding on the proposal **Close call.** |
| TC-L09-007 Privilege Escalation via Agent | PARTLY_COVERED | cross-component | control-plane, execution-runtime | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_asw_a.py`, `suites/v1-scenarios/test_scn_d02.py` | permission widening in request refused |
| TC-L09-014 Model API Key Lifecycle: Issue, Rotate, Expire, Revoke | PARTLY_COVERED | cross-component | control-plane, execution-runtime | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_asw_i.py` | grant expiry and revocation as analogue of key lifecycle **Close call.** |
| TC-L09-018 Impersonation Resistance: Agent or User Claims Another Identity | PARTLY_COVERED | cross-component | control-plane, execution-runtime | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_scn_d02.py`, `suites/v1-scenarios/test_asw_i.py` | identity taken from the resolver binding |
| TC-L09-019 Environment and Tenant Identity Boundaries (Prod vs Non-Prod) | PARTLY_COVERED | cross-component | control-plane, execution-runtime | route-A (effective-grant synthetic SQLite refund destination) ; route-B (atomic-claim synthetic SQLite refund destination) | `suites/v1-scenarios/test_asw_i.py` | tenant boundary only; prod/non-prod environments not modelled |
| TC-L09-025 Identity Audit Trail: Who, What and On Whose Behalf | APPLICABLE | cross-component | control-plane, replay-bundle | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_scn_c12.py`, `suites/v1-scenarios/test_scn_d08.py` | who/what/on-whose-behalf fields as recorded in decision, binding and replay |
| TC-L15-019 Backup, Disaster Recovery and Restoration of AI Services | PARTLY_COVERED | cross-component | execution-runtime, control-plane | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_scn_d07.py` | restore of authority state and destination state; external anchor not claimed |
| TC-L16-007 Dependency Confusion and Build-Time Substitution in AI SDKs | PARTLY_COVERED | individual-component | replay-bundle | no destination (synthetic record, bundle or manifest files only) | `suites/v1-scenarios/test_asw_s.py` | pin drift and unaccepted revisions refused; package index not modelled **Close call.** |
| TC-L16-015 Agent Framework and SDK Supply Chain Integrity | PARTLY_COVERED | individual-component | replay-bundle | no destination (synthetic record, bundle or manifest files only) | `suites/v1-scenarios/test_asw_s.py` | digest mismatch and revision refusal; SDK supply chain not modelled **Close call.** |
| TC-L17-002 Event Schema and Field Completeness | APPLICABLE | cross-component | odes, control-plane | no destination (synthetic record, bundle or manifest files only) | `suites/fix2-probes/test_time_grammar_probes.py`, `suites/v1-probes/test_odes_probes.py` | ODES and journal schema only; SIEM sources not claimed |
| TC-L17-004 Log Integrity and Tamper Evidence | APPLICABLE | cross-component | control-plane, verifier, replay-bundle, evidence-pack | no destination (synthetic record, bundle or manifest files only) | `suites/v1-scenarios/test_scn_d08.py`, `suites/v1-scenarios/test_scn_c13.py`, `suites/verifier-mutation`, `suites/v1-scenarios/test_asw_s.py` |  **Close call.** |
| TC-L17-020 Forensics: Conversation and Tool Call Reconstruction | PARTLY_COVERED | cross-component | replay-bundle, control-plane | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_scn_c12.py` | tool-call/effect reconstruction only; conversation turns not recorded **Close call.** |
| TC-L17-021 Forensics: Evidence Preservation, Legal Hold and Integrity | APPLICABLE | cross-component | replay-bundle, evidence-pack, verifier | no destination (synthetic record, bundle or manifest files only) | `suites/v1-scenarios/test_asw_s.py`, `suites/v1-scenarios/test_scn_c13.py` | hash verification and altered-copy failure only; legal hold and access log not claimed |
| TC-L17-022 Forensics: Cross-User, Agent and Tool Timeline | PARTLY_COVERED | cross-component | control-plane, verifier | no destination (synthetic record, bundle or manifest files only) | `suites/v1-scenarios/test_scn_d08.py` | ordering and duplicate detection of recorded events **Close call.** |
| TC-L17-028 Platform Health and Silent Failure Detection | PARTLY_COVERED | cross-component | execution-runtime, control-plane | route-A (effective-grant synthetic SQLite refund destination) | `suites/v1-scenarios/test_scn_c06.py`, `suites/v1-scenarios/test_asw_r.py` | failures surface as typed refusal or unknown; no alerting **Close call.** |

## Close calls for owner review

- TC-D08-001 (NOT_APPLICABLE): C23 calibrates evaluators by seeding defects, but this case benchmarks a red-team tool
- TC-D08-013 (NOT_APPLICABLE): judge accuracy; C23 calibrates the qualification evaluator, not an OCS capability
- TC-D09-004 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-D09-007 (NOT_APPLICABLE): policy digest drift checks exist (rev probes) but not privilege drift against an approved baseline
- TC-D09-010 (NOT_APPLICABLE): no role-conflict rule engine; separation rests on host key custody (guarantees section 5)
- TC-D09-012 (NOT_APPLICABLE): actor binding exists but acting-as-user vs itself mode is not declared
- TC-D09-015 (NOT_APPLICABLE): key expiry/rotation exists for attestation keys only, not AI workload certificates
- TC-D09-016 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-D10-006 (NOT_APPLICABLE): refund-style governed effect is in scope but this case tests a browser agent purchase guard
- TC-D12-004 (APPLICABLE): model, prompt and retrieval state are not recorded by OCS
- TC-D12-007 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-D12-021 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-D13-003 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-D13-013 (NOT_APPLICABLE): per-identity rate limits are not claimed; D06 covers saturation only
- TC-L02-002 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L02-011 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L02-015 (NOT_APPLICABLE): GRC evidence collection pipeline; evidence-status expiry is a different mechanism
- TC-L02-016 (APPLICABLE): pack built from one synthetic run; compliance-framework packs are not claimed
- TC-L05-012 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L05-013 (APPLICABLE): OCS has no configurable fail-open mode; only the fail-closed behaviour exists
- TC-L05-023 (NOT_APPLICABLE): retrieval canary isolation; only authority tenant binding exists (see L09-019)
- TC-L05-028 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L06-011 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L06-012 (NOT_APPLICABLE): automatic tool classification is not claimed; manifests are declared, not discovered
- TC-L06-016 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L06-020 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L06-022 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L06-023 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L06-024 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L06-025 (NOT_APPLICABLE): code-execution sandbox; live OpenShell confinement is excluded
- TC-L06-026 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L06-027 (NOT_APPLICABLE): model behaviour; deterministic effect-level checks are covered under other cases
- TC-L06-033 (NOT_APPLICABLE): graph policy for agent/tool call paths is not claimed
- TC-L06-038 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L06-041 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L06-043 (NOT_APPLICABLE): only a local registry exists; cross-organisation trust is not claimed
- TC-L06-045 (APPLICABLE): single-hop only; multi-agent chains are not modelled
- TC-L07-008 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L07-009 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L07-012 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L07-013 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L08-033 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L08-036 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L09-002 (NOT_APPLICABLE): unique-identity enforcement is not declared; holder inventory is host-declared
- TC-L09-006 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L09-011 (NOT_APPLICABLE): IdP leaver process; only local grant revocation exists
- TC-L09-014 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L09-024 (NOT_APPLICABLE): transport mutual authentication is not claimed
- TC-L16-004 (NOT_APPLICABLE): detection scanning of typosquats is not claimed; digest mismatch is under L16-007/015
- TC-L16-007 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L16-015 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L17-004 (APPLICABLE): "blocked" is not claimed; detection only
- TC-L17-020 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L17-022 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review
- TC-L17-028 (PARTLY_COVERED): nearest-mapped or partial analogue; owner review

## Not applicable

Every NOT_APPLICABLE case carries a one-line reason in `applicability.json`. Reasons by layer:

| Layer | Reason | Cases |
|---|---|---:|
| D08 | AI red-teaming tooling (attack libraries, judges, scanners) is not an OCS capability | 25 |
| D09 | enterprise agent identity governance (registry, sponsors, IAM workflows) is excluded; OCS has no IAM completeness claim | 16 |
| D10 | browser and computer-use agents are not declared | 23 |
| D11 | multimodal and voice input handling is not declared | 22 |
| D12 | incident-response process and model forensics are not declared | 18 |
| D13 | AI spend, token and abuse controls are not declared | 20 |
| L01 | use-case governance process is not an OCS capability | 20 |
| L02 | governance programme, GRC and risk-register workflow is not an OCS capability | 21 |
| L03 | legal, privacy and regulatory compliance programme is not claimed (no compliance certification) | 41 |
| L04 | user-facing AI usage discovery, endpoint and browser controls are not declared (UI/human layer) | 32 |
| L05 | AI application discovery, output handling and runtime protection products are not declared | 31 |
| L06 | agent discovery, MCP and orchestration platform features are not declared | 22 |
| L07 | prompt, context, memory and model-level injection defences are not claimed (general prompt-injection protection is an explicit exclusion; memory out of scope) | 37 |
| L08 | AI gateway, DLP and guardrail product features are not declared | 40 |
| L09 | enterprise IAM (SSO, SCIM, vault, sessions, JIT admin) is excluded | 18 |
| L10 | data layer classification, residency and lineage are not declared | 33 |
| L11 | retrieval and vector store quality/security is not declared | 25 |
| L12 | model layer (scanning, robustness, registry) is not declared | 31 |
| L13 | model training and fine-tuning is not declared | 26 |
| L14 | MLOps pipeline and model registry controls are not declared | 22 |
| L15 | AI infrastructure hardening and GPU/cluster controls are not declared | 19 |
| L16 | AI vendor and supply-chain risk programme is not declared | 24 |
| L17 | SOC monitoring, SIEM/SOAR detection and response operations are not declared | 25 |

Importing a case does not imply the capability exists in Cognous. Per-case exceptions to the layer reason (for example human-oversight cases) are stated in the JSON.
