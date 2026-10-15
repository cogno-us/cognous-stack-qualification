<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->
# AI Security Wiki scenarios

**656 upstream specifications; all NOT RUN.** These are not implemented or executed Cognous tests.

Imported from [AI Security Wiki](https://github.com/nachi065/AI-Security-Wiki/tree/1a0c72de4752a1c6932172e5e7dbf14f755799c8), commit `1a0c72de4752a1c6932172e5e7dbf14f755799c8`.

Original author: **Nachiket Sathaye**. Contributor credited by the upstream README: **Ankush Jain**. Each page and catalog entry retains its page-specific authors/coauthors. No upstream endorsement is implied.

Content and adaptations in this directory are **[CC BY-SA 4.0](LICENSE)** ([license link](https://creativecommons.org/licenses/by-sa/4.0/)). Changes: extracted machine-readable metadata, added status/provenance and attribution notices, and resolved relative Markdown links to the pinned source commit. Original procedures, safety notes, framework references and suggested thresholds are retained in the pages.

Upstream numeric thresholds and framework mappings are reference material, not adopted Cognous gates or verified current standards. Check applicability, profile limits, actual interfaces and current mappings before execution. All activity must use synthetic data and authorized isolated targets. Importing browser, training, regional compliance or fleet cases does not imply those capabilities exist in Cognous.

Use the [execution contract](../../docs/execution-contract.md), [source lock](../../sources/ai-security-wiki.lock.json), [machine-readable catalog](catalog.json), and [update instructions](../../docs/upstream-sync.md).

| Source layer/domain | Cases | Page credit |
|---|---:|---|
| [D08 AI Red Teaming and Continuous Testing](pages/D08-ai-red-teaming-and-continuous-testing.md) | 25 | Nachiket Sathaye |
| [D09 Agent and Non-Human Identity Governance](pages/D09-agent-and-non-human-identity-governance.md) | 20 | Nachiket Sathaye |
| [D10 Browser and Computer-Use Agents](pages/D10-browser-and-computer-use-agents.md) | 23 | Nachiket Sathaye |
| [D11 Multimodal and Voice Input Security](pages/D11-multimodal-and-voice-input-security.md) | 22 | Nachiket Sathaye |
| [D12 AI Incident Response and Forensics](pages/D12-ai-incident-response-and-forensics.md) | 22 | Nachiket Sathaye |
| [D13 AI Cost and Abuse Controls](pages/D13-ai-cost-and-abuse-controls.md) | 21 | Nachiket Sathaye |
| [L01 Business & Use Cases](pages/L01-business-and-use-cases.md) | 20 | Nachiket Sathaye |
| [L02 Governance & Risk Mgmt](pages/L02-governance-and-risk-mgmt.md) | 25 | Nachiket Sathaye |
| [L03 Legal, Privacy & Compliance](pages/L03-legal-privacy-and-compliance.md) | 42 | Nachiket Sathaye |
| [L04 Human Interaction Layer](pages/L04-human-interaction-layer.md) | 32 | Nachiket Sathaye |
| [L05 AI Applications](pages/L05-ai-applications.md) | 35 | Nachiket Sathaye |
| [L06 Agent Orchestration Layer](pages/L06-agent-orchestration-layer.md) | 46 | Nachiket Sathaye |
| [L07 Prompt & Context Layer](pages/L07-prompt-and-context-layer.md) | 41 | Nachiket Sathaye |
| [L08 AI Gateway & Security Controls](pages/L08-ai-gateway-and-security-controls.md) | 42 | Nachiket Sathaye |
| [L09 Identity & Access Mgmt](pages/L09-identity-and-access-mgmt.md) | 26 | Nachiket Sathaye |
| [L10 Data Layer](pages/L10-data-layer.md) | 33 | Nachiket Sathaye |
| [L11 Knowledge & Retrieval Layer](pages/L11-knowledge-and-retrieval-layer.md) | 25 | Nachiket Sathaye |
| [L12 Model Layer](pages/L12-model-layer.md) | 31 | Nachiket Sathaye |
| [L13 Training & Fine-Tuning Layer](pages/L13-training-and-fine-tuning-layer.md) | 26 | Nachiket Sathaye |
| [L14 MLOps / LLMOps Layer](pages/L14-mlops-llmops-layer.md) | 22 | Nachiket Sathaye |
| [L15 Infrastructure Layer](pages/L15-infrastructure-layer.md) | 20 | Nachiket Sathaye |
| [L16 Supply Chain & Third Party](pages/L16-supply-chain-and-third-party.md) | 26 | Nachiket Sathaye |
| [L17 Monitoring, Detection & Response](pages/L17-monitoring-detection-and-response.md) | 31 | Nachiket Sathaye |

## Case index

| ID | Scenario | Status |
|---|---|---|
| [TC-D08-001](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-001) | Seeded Vulnerable Target: Ground-Truth Benchmark for Findings | NOT RUN |
| [TC-D08-002](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-002) | Attack Library Coverage Across Risk Classes | NOT RUN |
| [TC-D08-003](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-003) | Attack Library Freshness and Update Cadence | NOT RUN |
| [TC-D08-004](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-004) | Single-Turn Attack Generation: Diversity and Mutation Quality | NOT RUN |
| [TC-D08-005](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-005) | Multi-Turn Adaptive Attack Campaigns | NOT RUN |
| [TC-D08-006](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-006) | Agentic Attack Scenarios Against Tool-Using Agents | NOT RUN |
| [TC-D08-007](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-007) | Retrieval and RAG Attack Coverage | NOT RUN |
| [TC-D08-008](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-008) | Indirect Injection Through Web, Email and File Content (Automated) | NOT RUN |
| [TC-D08-009](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-009) | Multimodal Attack Coverage (Images, Audio, Documents) | NOT RUN |
| [TC-D08-010](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-010) | Multilingual Attack Coverage (Arabic, Hindi, Urdu, French and Mixed) | NOT RUN |
| [TC-D08-011](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-011) | Custom Attack Authoring for Domain-Specific Scenarios | NOT RUN |
| [TC-D08-012](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-012) | Target Connectivity and Authentication Modes | NOT RUN |
| [TC-D08-013](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-013) | Attack Success Judging: Accuracy of Automated Verdicts | NOT RUN |
| [TC-D08-014](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-014) | Judge Robustness: Formatting, Persuasion and Cross-Judge Consistency | NOT RUN |
| [TC-D08-015](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-015) | Severity Scoring and Prioritisation of Findings | NOT RUN |
| [TC-D08-016](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-016) | Reproducibility and Run-to-Run Variance | NOT RUN |
| [TC-D08-017](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-017) | Finding Evidence Quality and Redaction | NOT RUN |
| [TC-D08-018](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-018) | Remediation Guidance Quality and Verified Retest | NOT RUN |
| [TC-D08-019](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-019) | Regression Testing After Model, Prompt or Guardrail Changes | NOT RUN |
| [TC-D08-020](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-020) | CI/CD Integration and Release Gates | NOT RUN |
| [TC-D08-021](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-021) | Continuous and Scheduled Testing with Change-Triggered Runs | NOT RUN |
| [TC-D08-022](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-022) | Safe Execution Against Production-Like Targets | NOT RUN |
| [TC-D08-023](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-023) | Handling of Adversarial Payloads, Responses and Test Data | NOT RUN |
| [TC-D08-024](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-024) | Test Cost, Runtime and Scalability | NOT RUN |
| [TC-D08-025](pages/D08-ai-red-teaming-and-continuous-testing.md#tc-d08-025) | Transparency of Benchmarks and Published Results | NOT RUN |
| [TC-D09-001](pages/D09-agent-and-non-human-identity-governance.md#tc-d09-001) | Agent Identity Registry as System of Record | NOT RUN |
| [TC-D09-002](pages/D09-agent-and-non-human-identity-governance.md#tc-d09-002) | Human Sponsor Accountability for Every Agent Identity | NOT RUN |
| [TC-D09-003](pages/D09-agent-and-non-human-identity-governance.md#tc-d09-003) | Agent Identity Provisioning Workflow and Approval | NOT RUN |
| [TC-D09-004](pages/D09-agent-and-non-human-identity-governance.md#tc-d09-004) | Agent Identity Risk Tiering and Privilege Classes | NOT RUN |
| [TC-D09-005](pages/D09-agent-and-non-human-identity-governance.md#tc-d09-005) | Entitlement Governance: Agent Access Requests and Least-Privilege Catalogue | NOT RUN |
| [TC-D09-006](pages/D09-agent-and-non-human-identity-governance.md#tc-d09-006) | Periodic Access Recertification for Agent Entitlements | NOT RUN |
| [TC-D09-007](pages/D09-agent-and-non-human-identity-governance.md#tc-d09-007) | Privilege Drift Detection Against an Approved Baseline | NOT RUN |
| [TC-D09-008](pages/D09-agent-and-non-human-identity-governance.md#tc-d09-008) | Dormant and Orphaned Agent Identity Clean-Up | NOT RUN |
| [TC-D09-009](pages/D09-agent-and-non-human-identity-governance.md#tc-d09-009) | Time-Bound and Just-in-Time Elevation for Agents | NOT RUN |
| [TC-D09-010](pages/D09-agent-and-non-human-identity-governance.md#tc-d09-010) | Separation of Duties for Agents | NOT RUN |
| [TC-D09-011](pages/D09-agent-and-non-human-identity-governance.md#tc-d09-011) | Delegation Records and Consent Evidence | NOT RUN |
| [TC-D09-012](pages/D09-agent-and-non-human-identity-governance.md#tc-d09-012) | Acting as the User versus Acting as Itself: Attribution Policy and Evidence | NOT RUN |
| [TC-D09-013](pages/D09-agent-and-non-human-identity-governance.md#tc-d09-013) | Cross-Platform Agent Identity Federation and Consistency | NOT RUN |
| [TC-D09-014](pages/D09-agent-and-non-human-identity-governance.md#tc-d09-014) | Agent Credential Lifecycle Governance and Compliance Reporting | NOT RUN |
| [TC-D09-015](pages/D09-agent-and-non-human-identity-governance.md#tc-d09-015) | Machine Identity Certificate and Key Lifecycle for AI Workloads | NOT RUN |
| [TC-D09-016](pages/D09-agent-and-non-human-identity-governance.md#tc-d09-016) | Revocation Propagation Time Across Systems | NOT RUN |
| [TC-D09-017](pages/D09-agent-and-non-human-identity-governance.md#tc-d09-017) | Agent Identity Misuse Case Handling Process | NOT RUN |
| [TC-D09-018](pages/D09-agent-and-non-human-identity-governance.md#tc-d09-018) | Third-Party and Vendor-Operated Agent Identities | NOT RUN |
| [TC-D09-019](pages/D09-agent-and-non-human-identity-governance.md#tc-d09-019) | Non-Human Identity Governance Metrics and Audit Evidence | NOT RUN |
| [TC-D09-020](pages/D09-agent-and-non-human-identity-governance.md#tc-d09-020) | Agent Identity Offboarding and Decommission Evidence | NOT RUN |
| [TC-D10-001](pages/D10-browser-and-computer-use-agents.md#tc-d10-001) | Browser and Computer-Use Agent Inventory and Classification | NOT RUN |
| [TC-D10-002](pages/D10-browser-and-computer-use-agents.md#tc-d10-002) | Execution Environment Isolation (Profile, Container or Virtual Machine) | NOT RUN |
| [TC-D10-003](pages/D10-browser-and-computer-use-agents.md#tc-d10-003) | Credential and Session Isolation for Agents | NOT RUN |
| [TC-D10-004](pages/D10-browser-and-computer-use-agents.md#tc-d10-004) | Domain and URL Policy with Redirect and Subdomain Handling | NOT RUN |
| [TC-D10-005](pages/D10-browser-and-computer-use-agents.md#tc-d10-005) | Action-Level Policy: Click, Type, Submit, Download, Upload, Purchase, Delete | NOT RUN |
| [TC-D10-006](pages/D10-browser-and-computer-use-agents.md#tc-d10-006) | Purchase and Payment Guard | NOT RUN |
| [TC-D10-007](pages/D10-browser-and-computer-use-agents.md#tc-d10-007) | Form Submission and Sensitive Data Entry Guard | NOT RUN |
| [TC-D10-008](pages/D10-browser-and-computer-use-agents.md#tc-d10-008) | File Download Controls and Malicious File Handling | NOT RUN |
| [TC-D10-009](pages/D10-browser-and-computer-use-agents.md#tc-d10-009) | File Upload and Clipboard Access Controls | NOT RUN |
| [TC-D10-010](pages/D10-browser-and-computer-use-agents.md#tc-d10-010) | Indirect Injection via Web Content: Visible, Hidden and Layout-Based | NOT RUN |
| [TC-D10-011](pages/D10-browser-and-computer-use-agents.md#tc-d10-011) | Fake Authority Cues: Banners, System Messages, Security Checks and Support Chats | NOT RUN |
| [TC-D10-012](pages/D10-browser-and-computer-use-agents.md#tc-d10-012) | Intent Verification: Agent Actions Compared with the User's Task | NOT RUN |
| [TC-D10-013](pages/D10-browser-and-computer-use-agents.md#tc-d10-013) | Step-Level Approval and Human Handoff | NOT RUN |
| [TC-D10-014](pages/D10-browser-and-computer-use-agents.md#tc-d10-014) | CAPTCHA and Bot-Detection Compliance | NOT RUN |
| [TC-D10-015](pages/D10-browser-and-computer-use-agents.md#tc-d10-015) | Authentication Flows: SSO, MFA and Session Handling | NOT RUN |
| [TC-D10-016](pages/D10-browser-and-computer-use-agents.md#tc-d10-016) | Cross-Tab and Cross-Site Data Leakage | NOT RUN |
| [TC-D10-017](pages/D10-browser-and-computer-use-agents.md#tc-d10-017) | Screenshot and Screen-Content Handling | NOT RUN |
| [TC-D10-018](pages/D10-browser-and-computer-use-agents.md#tc-d10-018) | Session Recording, Action Audit Trail and Replay | NOT RUN |
| [TC-D10-019](pages/D10-browser-and-computer-use-agents.md#tc-d10-019) | Rate and Scope Limits on Agent Actions | NOT RUN |
| [TC-D10-020](pages/D10-browser-and-computer-use-agents.md#tc-d10-020) | Kill Switch and Session Termination for Browser Agents | NOT RUN |
| [TC-D10-021](pages/D10-browser-and-computer-use-agents.md#tc-d10-021) | Desktop Computer-Use Agents: File System and Application Access Controls | NOT RUN |
| [TC-D10-022](pages/D10-browser-and-computer-use-agents.md#tc-d10-022) | Managed Browser Policy and Agent Extension Permission Governance | NOT RUN |
| [TC-D10-023](pages/D10-browser-and-computer-use-agents.md#tc-d10-023) | Detecting Agent-Driven Traffic on Internal Applications (Application-Side Signals) | NOT RUN |
| [TC-D11-001](pages/D11-multimodal-and-voice-input-security.md#tc-d11-001) | Multimodal Input Channel Inventory and Exposure Map | NOT RUN |
| [TC-D11-002](pages/D11-multimodal-and-voice-input-security.md#tc-d11-002) | Image Text Injection: Visible, Small and Low-Contrast Text | NOT RUN |
| [TC-D11-003](pages/D11-multimodal-and-voice-input-security.md#tc-d11-003) | Image Injection: Rotated, Distorted, Layout-Based and Screenshot Content | NOT RUN |
| [TC-D11-004](pages/D11-multimodal-and-voice-input-security.md#tc-d11-004) | Adversarial Image Perturbation Against Vision Components | NOT RUN |
| [TC-D11-005](pages/D11-multimodal-and-voice-input-security.md#tc-d11-005) | Image Metadata and Embedded Data: Injection and Leakage | NOT RUN |
| [TC-D11-006](pages/D11-multimodal-and-voice-input-security.md#tc-d11-006) | Sensitive Data in Images: OCR and Visual DLP Accuracy | NOT RUN |
| [TC-D11-007](pages/D11-multimodal-and-voice-input-security.md#tc-d11-007) | Faces, Biometric Images and Personal Identifiers in Images | NOT RUN |
| [TC-D11-008](pages/D11-multimodal-and-voice-input-security.md#tc-d11-008) | Document Parser Attack Surface: Malformed and Spoofed Files | NOT RUN |
| [TC-D11-009](pages/D11-multimodal-and-voice-input-security.md#tc-d11-009) | Active Content in Documents: Macros, Formulas, Links and Embedded Objects | NOT RUN |
| [TC-D11-010](pages/D11-multimodal-and-voice-input-security.md#tc-d11-010) | Hidden Layers in Documents: White Text, Comments, Tracked Changes, Annotations and Notes | NOT RUN |
| [TC-D11-011](pages/D11-multimodal-and-voice-input-security.md#tc-d11-011) | Document and Media Bombs: Resource Exhaustion in Ingestion | NOT RUN |
| [TC-D11-012](pages/D11-multimodal-and-voice-input-security.md#tc-d11-012) | Cross-Modal Consistency Attacks | NOT RUN |
| [TC-D11-013](pages/D11-multimodal-and-voice-input-security.md#tc-d11-013) | Audio Injection: Spoken Instructions in Synthetic Voice | NOT RUN |
| [TC-D11-014](pages/D11-multimodal-and-voice-input-security.md#tc-d11-014) | Audio Injection in Background and Noisy Conditions (Audible Range) | NOT RUN |
| [TC-D11-015](pages/D11-multimodal-and-voice-input-security.md#tc-d11-015) | Transcription Errors as Policy Bypass (Accents, Dialects, Homophones and Code-Switching) | NOT RUN |
| [TC-D11-016](pages/D11-multimodal-and-voice-input-security.md#tc-d11-016) | Real-Time Voice DLP and Redaction Under Latency Limits | NOT RUN |
| [TC-D11-017](pages/D11-multimodal-and-voice-input-security.md#tc-d11-017) | Voice Authentication and Synthetic Voice Resistance | NOT RUN |
| [TC-D11-018](pages/D11-multimodal-and-voice-input-security.md#tc-d11-018) | Speaker Identification, Voiceprints and Biometric Data Handling | NOT RUN |
| [TC-D11-019](pages/D11-multimodal-and-voice-input-security.md#tc-d11-019) | Meeting and Call Recording: Consent, Notice and Transcript Governance | NOT RUN |
| [TC-D11-020](pages/D11-multimodal-and-voice-input-security.md#tc-d11-020) | Video and Live Camera Input: Frame-Based Injection and Bystander Privacy | NOT RUN |
| [TC-D11-021](pages/D11-multimodal-and-voice-input-security.md#tc-d11-021) | Multimodal Output Leakage: Generated Images, Spoken Output and Documents | NOT RUN |
| [TC-D11-022](pages/D11-multimodal-and-voice-input-security.md#tc-d11-022) | Storage, Retention and Access Controls for Media Inputs and Outputs | NOT RUN |
| [TC-D12-001](pages/D12-ai-incident-response-and-forensics.md#tc-d12-001) | AI Incident Taxonomy and Severity Classification | NOT RUN |
| [TC-D12-002](pages/D12-ai-incident-response-and-forensics.md#tc-d12-002) | AI Incident Intake: Detection Alerts, User Reports and Third-Party Notices | NOT RUN |
| [TC-D12-003](pages/D12-ai-incident-response-and-forensics.md#tc-d12-003) | Triage Runbooks by AI Incident Type | NOT RUN |
| [TC-D12-004](pages/D12-ai-incident-response-and-forensics.md#tc-d12-004) | Preserving AI System State at Incident Time: Model, Prompt, Configuration, Tools and Policy | NOT RUN |
| [TC-D12-005](pages/D12-ai-incident-response-and-forensics.md#tc-d12-005) | Retrieval Index and Knowledge Snapshots for Forensics | NOT RUN |
| [TC-D12-006](pages/D12-ai-incident-response-and-forensics.md#tc-d12-006) | Reconstructing What the Model Saw: Context, Memory and Retrieved Content | NOT RUN |
| [TC-D12-007](pages/D12-ai-incident-response-and-forensics.md#tc-d12-007) | Deterministic Replay: Reproducing an Incident with Pinned Versions and Recorded Inputs | NOT RUN |
| [TC-D12-008](pages/D12-ai-incident-response-and-forensics.md#tc-d12-008) | Attribution Analysis: Attacker, Insider, Misconfiguration or Model Fault | NOT RUN |
| [TC-D12-009](pages/D12-ai-incident-response-and-forensics.md#tc-d12-009) | Scoping and Blast Radius: Users, Data, Systems and Outputs Affected | NOT RUN |
| [TC-D12-010](pages/D12-ai-incident-response-and-forensics.md#tc-d12-010) | Downstream Propagation of Harmful or False Outputs | NOT RUN |
| [TC-D12-011](pages/D12-ai-incident-response-and-forensics.md#tc-d12-011) | Containment Option Catalogue and Selection Guidance | NOT RUN |
| [TC-D12-012](pages/D12-ai-incident-response-and-forensics.md#tc-d12-012) | Eradication and Recovery Validation | NOT RUN |
| [TC-D12-013](pages/D12-ai-incident-response-and-forensics.md#tc-d12-013) | Poisoning and Training-Data Incident Forensics | NOT RUN |
| [TC-D12-014](pages/D12-ai-incident-response-and-forensics.md#tc-d12-014) | Model Behaviour Regression Incident | NOT RUN |
| [TC-D12-015](pages/D12-ai-incident-response-and-forensics.md#tc-d12-015) | Harm Assessment and Affected-Person Identification | NOT RUN |
| [TC-D12-016](pages/D12-ai-incident-response-and-forensics.md#tc-d12-016) | Notification Decision and Communications (Framework-Neutral) | NOT RUN |
| [TC-D12-017](pages/D12-ai-incident-response-and-forensics.md#tc-d12-017) | Third-Party and Model-Provider Incident Coordination | NOT RUN |
| [TC-D12-018](pages/D12-ai-incident-response-and-forensics.md#tc-d12-018) | Evidence Handling for AI Artefacts and Chain of Custody | NOT RUN |
| [TC-D12-019](pages/D12-ai-incident-response-and-forensics.md#tc-d12-019) | Forensic Tooling Access, Separation of Duties and Audit | NOT RUN |
| [TC-D12-020](pages/D12-ai-incident-response-and-forensics.md#tc-d12-020) | AI Root-Cause Analysis Method and Recurrence Tracking | NOT RUN |
| [TC-D12-021](pages/D12-ai-incident-response-and-forensics.md#tc-d12-021) | Near-Miss and Blocked-Attack Learning | NOT RUN |
| [TC-D12-022](pages/D12-ai-incident-response-and-forensics.md#tc-d12-022) | AI Incident Register, Metrics and Trend Analysis | NOT RUN |
| [TC-D13-001](pages/D13-ai-cost-and-abuse-controls.md#tc-d13-001) | Cost Attribution: Tagging Spend to Team, Application, User and Key | NOT RUN |
| [TC-D13-002](pages/D13-ai-cost-and-abuse-controls.md#tc-d13-002) | Token Accounting Accuracy Against Provider Invoices | NOT RUN |
| [TC-D13-003](pages/D13-ai-cost-and-abuse-controls.md#tc-d13-003) | Budget Hierarchy and Enforcement: Organisation, Team, Application, User and Key | NOT RUN |
| [TC-D13-004](pages/D13-ai-cost-and-abuse-controls.md#tc-d13-004) | Real-Time Spend Anomaly Detection | NOT RUN |
| [TC-D13-005](pages/D13-ai-cost-and-abuse-controls.md#tc-d13-005) | Leaked or Stolen API Key: Cost-Spike Detection and Automatic Containment | NOT RUN |
| [TC-D13-006](pages/D13-ai-cost-and-abuse-controls.md#tc-d13-006) | Denial of Wallet via Public Chatbot Endpoints: Anonymous Traffic Abuse | NOT RUN |
| [TC-D13-007](pages/D13-ai-cost-and-abuse-controls.md#tc-d13-007) | Quota and Credit Abuse: Multi-Account, Free-Tier and Trial Exploitation | NOT RUN |
| [TC-D13-008](pages/D13-ai-cost-and-abuse-controls.md#tc-d13-008) | Prompt and Output Expansion Abuse: Length and Amplification Limits | NOT RUN |
| [TC-D13-009](pages/D13-ai-cost-and-abuse-controls.md#tc-d13-009) | Tool Fan-Out and Recursive Agent Cost Explosion | NOT RUN |
| [TC-D13-010](pages/D13-ai-cost-and-abuse-controls.md#tc-d13-010) | Retry Storms, Timeouts and the Cost of Failure Handling | NOT RUN |
| [TC-D13-011](pages/D13-ai-cost-and-abuse-controls.md#tc-d13-011) | Caching and Prefix Reuse: Cost Effects and Cache Abuse | NOT RUN |
| [TC-D13-012](pages/D13-ai-cost-and-abuse-controls.md#tc-d13-012) | Model Routing Cost Controls: Premium Model Misuse and Downgrade Policy | NOT RUN |
| [TC-D13-013](pages/D13-ai-cost-and-abuse-controls.md#tc-d13-013) | Rate and Concurrency Limits per Identity, Key and Network | NOT RUN |
| [TC-D13-014](pages/D13-ai-cost-and-abuse-controls.md#tc-d13-014) | Circuit Breakers and Automatic Actions on Budget Breach | NOT RUN |
| [TC-D13-015](pages/D13-ai-cost-and-abuse-controls.md#tc-d13-015) | Batch Jobs, Scheduled Runs and Long-Running Tasks: Timeouts and Spend Ceilings | NOT RUN |
| [TC-D13-016](pages/D13-ai-cost-and-abuse-controls.md#tc-d13-016) | GPU and Self-Hosted Inference Cost Abuse | NOT RUN |
| [TC-D13-017](pages/D13-ai-cost-and-abuse-controls.md#tc-d13-017) | Shadow Spend Discovery: Unapproved AI Subscriptions and Direct Provider Accounts | NOT RUN |
| [TC-D13-018](pages/D13-ai-cost-and-abuse-controls.md#tc-d13-018) | Spend Approval Workflow for Expensive Models, Features and Contracts | NOT RUN |
| [TC-D13-019](pages/D13-ai-cost-and-abuse-controls.md#tc-d13-019) | Cost Controls for Third-Party and Embedded AI Features | NOT RUN |
| [TC-D13-020](pages/D13-ai-cost-and-abuse-controls.md#tc-d13-020) | Cost Reporting, Chargeback Evidence and Dispute Handling | NOT RUN |
| [TC-D13-021](pages/D13-ai-cost-and-abuse-controls.md#tc-d13-021) | Abuse Enforcement Ladder: Warn, Throttle, Suspend and Appeal for Authenticated Users | NOT RUN |
| [TC-L01-001](pages/L01-business-and-use-cases.md#tc-l01-001) | AI Use-Case Registry: Creation, Mandatory Fields and Uniqueness | NOT RUN |
| [TC-L01-002](pages/L01-business-and-use-cases.md#tc-l01-002) | Use-Case Intake and Approval Workflow Before Deployment | NOT RUN |
| [TC-L01-003](pages/L01-business-and-use-cases.md#tc-l01-003) | Business Owner and Accountable Executive Attribution | NOT RUN |
| [TC-L01-004](pages/L01-business-and-use-cases.md#tc-l01-004) | Use-Case to System, Model and Data Traceability | NOT RUN |
| [TC-L01-005](pages/L01-business-and-use-cases.md#tc-l01-005) | Risk Tiering of Use Cases: Criteria and Consistency | NOT RUN |
| [TC-L01-006](pages/L01-business-and-use-cases.md#tc-l01-006) | Screening for Prohibited or Restricted Use Cases | NOT RUN |
| [TC-L01-007](pages/L01-business-and-use-cases.md#tc-l01-007) | Intended Purpose Documentation and Purpose-Drift Detection | NOT RUN |
| [TC-L01-008](pages/L01-business-and-use-cases.md#tc-l01-008) | Reconciliation of Discovered AI Use Against the Registry | NOT RUN |
| [TC-L01-009](pages/L01-business-and-use-cases.md#tc-l01-009) | Business Impact and Criticality Classification | NOT RUN |
| [TC-L01-010](pages/L01-business-and-use-cases.md#tc-l01-010) | Impacted Persons and Stakeholder Identification | NOT RUN |
| [TC-L01-011](pages/L01-business-and-use-cases.md#tc-l01-011) | Identification of Automated Decisions and Profiling | NOT RUN |
| [TC-L01-012](pages/L01-business-and-use-cases.md#tc-l01-012) | Human Oversight Design Recorded and Tested | NOT RUN |
| [TC-L01-013](pages/L01-business-and-use-cases.md#tc-l01-013) | Use-Case Lifecycle States and Required Controls per State | NOT RUN |
| [TC-L01-014](pages/L01-business-and-use-cases.md#tc-l01-014) | Pilot and Proof-of-Concept Guardrails | NOT RUN |
| [TC-L01-015](pages/L01-business-and-use-cases.md#tc-l01-015) | Material Change Triggers Re-Assessment | NOT RUN |
| [TC-L01-016](pages/L01-business-and-use-cases.md#tc-l01-016) | Benefit, Risk and KPI Tracking per Use Case | NOT RUN |
| [TC-L01-017](pages/L01-business-and-use-cases.md#tc-l01-017) | Third-Party AI Dependency Recording per Use Case | NOT RUN |
| [TC-L01-018](pages/L01-business-and-use-cases.md#tc-l01-018) | Fallback and Continuity Plans for AI-Dependent Processes | NOT RUN |
| [TC-L01-019](pages/L01-business-and-use-cases.md#tc-l01-019) | Use-Case Retirement and Decommission Evidence | NOT RUN |
| [TC-L01-020](pages/L01-business-and-use-cases.md#tc-l01-020) | Portfolio View and Executive Reporting on Use Cases | NOT RUN |
| [TC-L02-001](pages/L02-governance-and-risk-mgmt.md#tc-l02-001) | AI Policy Framework: Scope, Ownership, Approval and Review Cycle | NOT RUN |
| [TC-L02-002](pages/L02-governance-and-risk-mgmt.md#tc-l02-002) | Policy-to-Control Mapping | NOT RUN |
| [TC-L02-003](pages/L02-governance-and-risk-mgmt.md#tc-l02-003) | Control Library and Multi-Framework Crosswalk Capability | NOT RUN |
| [TC-L02-004](pages/L02-governance-and-risk-mgmt.md#tc-l02-004) | Roles and Responsibilities (RACI) Recorded and Enforced | NOT RUN |
| [TC-L02-005](pages/L02-governance-and-risk-mgmt.md#tc-l02-005) | AI Governance Committee Workflow and Decision Record | NOT RUN |
| [TC-L02-006](pages/L02-governance-and-risk-mgmt.md#tc-l02-006) | AI Risk Register: Creation, Scoring and Ownership | NOT RUN |
| [TC-L02-007](pages/L02-governance-and-risk-mgmt.md#tc-l02-007) | Risk Assessment Consistency Between Assessors | NOT RUN |
| [TC-L02-008](pages/L02-governance-and-risk-mgmt.md#tc-l02-008) | Risk Treatment Tracking | NOT RUN |
| [TC-L02-009](pages/L02-governance-and-risk-mgmt.md#tc-l02-009) | Residual Risk Acceptance with Authority Limits | NOT RUN |
| [TC-L02-010](pages/L02-governance-and-risk-mgmt.md#tc-l02-010) | Exception and Waiver Workflow: Request, Approval, Expiry and Review | NOT RUN |
| [TC-L02-011](pages/L02-governance-and-risk-mgmt.md#tc-l02-011) | Exception Expiry Enforced in Technical Controls | NOT RUN |
| [TC-L02-012](pages/L02-governance-and-risk-mgmt.md#tc-l02-012) | Exception Reporting, Ageing and Concentration | NOT RUN |
| [TC-L02-013](pages/L02-governance-and-risk-mgmt.md#tc-l02-013) | Control Effectiveness Measurement and Evidence Freshness | NOT RUN |
| [TC-L02-014](pages/L02-governance-and-risk-mgmt.md#tc-l02-014) | Control Owner Attestation | NOT RUN |
| [TC-L02-015](pages/L02-governance-and-risk-mgmt.md#tc-l02-015) | Automated Evidence Collection and Freshness | NOT RUN |
| [TC-L02-016](pages/L02-governance-and-risk-mgmt.md#tc-l02-016) | Audit Readiness: Evidence Pack on Demand | NOT RUN |
| [TC-L02-017](pages/L02-governance-and-risk-mgmt.md#tc-l02-017) | Internal and External Audit Support: Read-Only Access and Sampling | NOT RUN |
| [TC-L02-018](pages/L02-governance-and-risk-mgmt.md#tc-l02-018) | Finding, Nonconformity and Corrective Action Management | NOT RUN |
| [TC-L02-019](pages/L02-governance-and-risk-mgmt.md#tc-l02-019) | Governance Metrics and KPI Reporting | NOT RUN |
| [TC-L02-020](pages/L02-governance-and-risk-mgmt.md#tc-l02-020) | Regulatory and Framework Change Management | NOT RUN |
| [TC-L02-021](pages/L02-governance-and-risk-mgmt.md#tc-l02-021) | Third-Party Governance Integration | NOT RUN |
| [TC-L02-022](pages/L02-governance-and-risk-mgmt.md#tc-l02-022) | Training and Awareness Tracking for AI Policies | NOT RUN |
| [TC-L02-023](pages/L02-governance-and-risk-mgmt.md#tc-l02-023) | Acceptable Use Acknowledgement and Re-Acknowledgement | NOT RUN |
| [TC-L02-024](pages/L02-governance-and-risk-mgmt.md#tc-l02-024) | Management Review Inputs and Outputs | NOT RUN |
| [TC-L02-025](pages/L02-governance-and-risk-mgmt.md#tc-l02-025) | Governance Record Integrity: Change History and Tamper Evidence | NOT RUN |
| [TC-L03-001](pages/L03-legal-privacy-and-compliance.md#tc-l03-001) | Register of AI Processing Activities | NOT RUN |
| [TC-L03-002](pages/L03-legal-privacy-and-compliance.md#tc-l03-002) | Lawful Basis or Legal Ground Recording per Processing Activity | NOT RUN |
| [TC-L03-003](pages/L03-legal-privacy-and-compliance.md#tc-l03-003) | Notice and Transparency: Disclosing AI Interaction and Processing | NOT RUN |
| [TC-L03-004](pages/L03-legal-privacy-and-compliance.md#tc-l03-004) | Consent Capture, Evidence and Withdrawal | NOT RUN |
| [TC-L03-005](pages/L03-legal-privacy-and-compliance.md#tc-l03-005) | Data Subject Rights: Access Request Workflow | NOT RUN |
| [TC-L03-006](pages/L03-legal-privacy-and-compliance.md#tc-l03-006) | Data Subject Rights: Correction Request Handling | NOT RUN |
| [TC-L03-007](pages/L03-legal-privacy-and-compliance.md#tc-l03-007) | Data Subject Rights: Erasure Across AI Stores | NOT RUN |
| [TC-L03-008](pages/L03-legal-privacy-and-compliance.md#tc-l03-008) | Rights to Object, Restrict and Request Human Review | NOT RUN |
| [TC-L03-009](pages/L03-legal-privacy-and-compliance.md#tc-l03-009) | Rights Request Timeline Tracking and Evidence | NOT RUN |
| [TC-L03-010](pages/L03-legal-privacy-and-compliance.md#tc-l03-010) | Impact Assessment Support (Privacy, Data Protection and AI Impact Assessments) | NOT RUN |
| [TC-L03-011](pages/L03-legal-privacy-and-compliance.md#tc-l03-011) | Impact Assessment Triggers | NOT RUN |
| [TC-L03-012](pages/L03-legal-privacy-and-compliance.md#tc-l03-012) | Cross-Border Transfer Register and Assessment | NOT RUN |
| [TC-L03-013](pages/L03-legal-privacy-and-compliance.md#tc-l03-013) | Cross-Border Transfer Enforcement | NOT RUN |
| [TC-L03-014](pages/L03-legal-privacy-and-compliance.md#tc-l03-014) | Residency Evidence Export for a Regulator | NOT RUN |
| [TC-L03-015](pages/L03-legal-privacy-and-compliance.md#tc-l03-015) | Data Minimisation and Purpose Limitation Enforcement | NOT RUN |
| [TC-L03-016](pages/L03-legal-privacy-and-compliance.md#tc-l03-016) | Retention Schedule Enforcement for AI Data | NOT RUN |
| [TC-L03-017](pages/L03-legal-privacy-and-compliance.md#tc-l03-017) | Children's and Vulnerable Persons' Data Handling | NOT RUN |
| [TC-L03-018](pages/L03-legal-privacy-and-compliance.md#tc-l03-018) | Special and Sensitive Categories of Data: Identification and Heightened Controls | NOT RUN |
| [TC-L03-019](pages/L03-legal-privacy-and-compliance.md#tc-l03-019) | Breach and Incident Notification Workflow | NOT RUN |
| [TC-L03-020](pages/L03-legal-privacy-and-compliance.md#tc-l03-020) | Controller, Processor and Joint Role Mapping with Agreements | NOT RUN |
| [TC-L03-021](pages/L03-legal-privacy-and-compliance.md#tc-l03-021) | AI Provider Compliance Due-Diligence Evidence | NOT RUN |
| [TC-L03-022](pages/L03-legal-privacy-and-compliance.md#tc-l03-022) | Compliance Evidence Export: Formats, Signing and Integrity | NOT RUN |
| [TC-L03-023](pages/L03-legal-privacy-and-compliance.md#tc-l03-023) | Multi-Framework Compliance Dashboard: Coverage and Gaps | NOT RUN |
| [TC-L03-024](pages/L03-legal-privacy-and-compliance.md#tc-l03-024) | Adopting a New Framework: Custom Framework Onboarding | NOT RUN |
| [TC-L03-025](pages/L03-legal-privacy-and-compliance.md#tc-l03-025) | Evidence Reuse Across Frameworks | NOT RUN |
| [TC-L03-026](pages/L03-legal-privacy-and-compliance.md#tc-l03-026) | Regulator Inspection Simulation: Rapid Evidence Request | NOT RUN |
| [TC-L03-027](pages/L03-legal-privacy-and-compliance.md#tc-l03-027) | Litigation Hold and Regulatory Preservation Notice | NOT RUN |
| [TC-L03-028](pages/L03-legal-privacy-and-compliance.md#tc-l03-028) | Intellectual Property and Copyright Controls for AI Inputs and Outputs | NOT RUN |
| [TC-L03-029](pages/L03-legal-privacy-and-compliance.md#tc-l03-029) | Automated Decision Explanation Records | NOT RUN |
| [TC-L03-030](pages/L03-legal-privacy-and-compliance.md#tc-l03-030) | Language and Jurisdiction Configuration (Arabic, English and Regional Rule Sets) | NOT RUN |
| [TC-L03-031](pages/L03-legal-privacy-and-compliance.md#tc-l03-031) | Bias Testing Before Release and on Material Change | NOT RUN |
| [TC-L03-032](pages/L03-legal-privacy-and-compliance.md#tc-l03-032) | Adverse-Impact Analysis for Employment, Credit and Other Consequential Decisions | NOT RUN |
| [TC-L03-033](pages/L03-legal-privacy-and-compliance.md#tc-l03-033) | Language Parity: Output Quality and Safety Controls Across Languages | NOT RUN |
| [TC-L03-034](pages/L03-legal-privacy-and-compliance.md#tc-l03-034) | Fundamental Rights Impact Assessment Before Deployment | NOT RUN |
| [TC-L03-035](pages/L03-legal-privacy-and-compliance.md#tc-l03-035) | AI-Generated Content Marking, Labels and Provenance | NOT RUN |
| [TC-L03-036](pages/L03-legal-privacy-and-compliance.md#tc-l03-036) | Automated Decision Register and Published Transparency Statement | NOT RUN |
| [TC-L03-037](pages/L03-legal-privacy-and-compliance.md#tc-l03-037) | Statutory Role and Risk-Class Determination per AI System | NOT RUN |
| [TC-L03-038](pages/L03-legal-privacy-and-compliance.md#tc-l03-038) | AI Literacy Programme and Role-Based Training Records | NOT RUN |
| [TC-L03-039](pages/L03-legal-privacy-and-compliance.md#tc-l03-039) | Authority Register, Filings and Local Representative Records | NOT RUN |
| [TC-L03-040](pages/L03-legal-privacy-and-compliance.md#tc-l03-040) | Human Oversight Effectiveness: Seeded-Error Detection and Review Metrics | NOT RUN |
| [TC-L03-041](pages/L03-legal-privacy-and-compliance.md#tc-l03-041) | Overseer Evidence, Override Authority and Review Workload | NOT RUN |
| [TC-L03-042](pages/L03-legal-privacy-and-compliance.md#tc-l03-042) | AI Vendor Terms: Output Ownership, Infringement Indemnity and Training Use | NOT RUN |
| [TC-L04-001](pages/L04-human-interaction-layer.md#tc-l04-001) | Unsanctioned Public AI Web Tool Discovery | NOT RUN |
| [TC-L04-002](pages/L04-human-interaction-layer.md#tc-l04-002) | AI Browser Extension Discovery | NOT RUN |
| [TC-L04-003](pages/L04-human-interaction-layer.md#tc-l04-003) | AI Usage Attribution by Department | NOT RUN |
| [TC-L04-004](pages/L04-human-interaction-layer.md#tc-l04-004) | AI Usage Attribution by User Group | NOT RUN |
| [TC-L04-005](pages/L04-human-interaction-layer.md#tc-l04-005) | AI Usage by Device Type and Management Status | NOT RUN |
| [TC-L04-006](pages/L04-human-interaction-layer.md#tc-l04-006) | AI Usage by Network Path | NOT RUN |
| [TC-L04-007](pages/L04-human-interaction-layer.md#tc-l04-007) | Discovery from Existing Proxy/SWG Logs | NOT RUN |
| [TC-L04-008](pages/L04-human-interaction-layer.md#tc-l04-008) | Off-Network Endpoint Usage Reporting | NOT RUN |
| [TC-L04-009](pages/L04-human-interaction-layer.md#tc-l04-009) | Personal vs Corporate Account Detection on the Same AI Service | NOT RUN |
| [TC-L04-010](pages/L04-human-interaction-layer.md#tc-l04-010) | Native Browser-Embedded AI Assistant Detection | NOT RUN |
| [TC-L04-011](pages/L04-human-interaction-layer.md#tc-l04-011) | Real-Time Coaching Banner on Unsanctioned Tool | NOT RUN |
| [TC-L04-012](pages/L04-human-interaction-layer.md#tc-l04-012) | Content-Aware Warning on Sensitive Paste | NOT RUN |
| [TC-L04-013](pages/L04-human-interaction-layer.md#tc-l04-013) | Business Justification Workflow (Justify and Proceed) | NOT RUN |
| [TC-L04-014](pages/L04-human-interaction-layer.md#tc-l04-014) | Approval Workflow for AI Access Exceptions | NOT RUN |
| [TC-L04-015](pages/L04-human-interaction-layer.md#tc-l04-015) | Time-Bound Exception Expiry Enforcement | NOT RUN |
| [TC-L04-016](pages/L04-human-interaction-layer.md#tc-l04-016) | Block with Redirect to Sanctioned Alternative | NOT RUN |
| [TC-L04-017](pages/L04-human-interaction-layer.md#tc-l04-017) | Sensitive Text Paste into Web AI Prompt: Monitor vs Block | NOT RUN |
| [TC-L04-018](pages/L04-human-interaction-layer.md#tc-l04-018) | File Upload to AI Web Tool: Classified File Detection | NOT RUN |
| [TC-L04-019](pages/L04-human-interaction-layer.md#tc-l04-019) | Source Code Snippet Paste or Drag-and-Drop | NOT RUN |
| [TC-L04-020](pages/L04-human-interaction-layer.md#tc-l04-020) | Screenshot and Image Upload with Sensitive Content | NOT RUN |
| [TC-L04-021](pages/L04-human-interaction-layer.md#tc-l04-021) | Voice and Audio Input to AI Tools | NOT RUN |
| [TC-L04-022](pages/L04-human-interaction-layer.md#tc-l04-022) | Hidden Text and Metadata in Uploaded Documents | NOT RUN |
| [TC-L04-023](pages/L04-human-interaction-layer.md#tc-l04-023) | Browser-Based AI Agent (Computer-Use) Activity Detection | NOT RUN |
| [TC-L04-024](pages/L04-human-interaction-layer.md#tc-l04-024) | Mobile and BYOD AI App Visibility | NOT RUN |
| [TC-L04-025](pages/L04-human-interaction-layer.md#tc-l04-025) | Unmanaged Device Access to Sanctioned AI Tools | NOT RUN |
| [TC-L04-026](pages/L04-human-interaction-layer.md#tc-l04-026) | User Risk Scoring from Repeated AI Policy Violations | NOT RUN |
| [TC-L04-027](pages/L04-human-interaction-layer.md#tc-l04-027) | Privacy Controls on User-Level AI Activity Data | NOT RUN |
| [TC-L04-028](pages/L04-human-interaction-layer.md#tc-l04-028) | Arabic and Mixed-Language Prompt Handling | NOT RUN |
| [TC-L04-029](pages/L04-human-interaction-layer.md#tc-l04-029) | Differential Policy Enforcement by Group | NOT RUN |
| [TC-L04-030](pages/L04-human-interaction-layer.md#tc-l04-030) | Shared or Generic Account Use of AI Tools | NOT RUN |
| [TC-L04-031](pages/L04-human-interaction-layer.md#tc-l04-031) | IDE Chat Prompt Containing Proprietary Source Code: Monitor vs Block | NOT RUN |
| [TC-L04-032](pages/L04-human-interaction-layer.md#tc-l04-032) | Developer Coaching and Justification Inside the IDE | NOT RUN |
| [TC-L05-001](pages/L05-ai-applications.md#tc-l05-001) | Sanctioned AI Application Discovery | NOT RUN |
| [TC-L05-002](pages/L05-ai-applications.md#tc-l05-002) | AI Plugin and Connector Discovery in Sanctioned SaaS | NOT RUN |
| [TC-L05-003](pages/L05-ai-applications.md#tc-l05-003) | AI API Usage Discovery | NOT RUN |
| [TC-L05-004](pages/L05-ai-applications.md#tc-l05-004) | IDE-Based AI Coding Assistant Discovery | NOT RUN |
| [TC-L05-005](pages/L05-ai-applications.md#tc-l05-005) | Embedded AI Features in Sanctioned SaaS | NOT RUN |
| [TC-L05-006](pages/L05-ai-applications.md#tc-l05-006) | Internally Built AI Application Discovery | NOT RUN |
| [TC-L05-007](pages/L05-ai-applications.md#tc-l05-007) | AI Application Risk Classification | NOT RUN |
| [TC-L05-008](pages/L05-ai-applications.md#tc-l05-008) | Application Inventory Enrichment (Owner, Data, Model) | NOT RUN |
| [TC-L05-009](pages/L05-ai-applications.md#tc-l05-009) | New AI Application Detection Latency | NOT RUN |
| [TC-L05-010](pages/L05-ai-applications.md#tc-l05-010) | Model API Key Exposure in Application Configuration | NOT RUN |
| [TC-L05-011](pages/L05-ai-applications.md#tc-l05-011) | Inventory Export to CMDB or Asset Management | NOT RUN |
| [TC-L05-012](pages/L05-ai-applications.md#tc-l05-012) | Runtime Protection Coverage Verification | NOT RUN |
| [TC-L05-013](pages/L05-ai-applications.md#tc-l05-013) | Runtime Protection Fail-Open vs Fail-Closed Behaviour | NOT RUN |
| [TC-L05-014](pages/L05-ai-applications.md#tc-l05-014) | Output Handling: Script Injection in Rendered Responses | NOT RUN |
| [TC-L05-015](pages/L05-ai-applications.md#tc-l05-015) | Output Handling: Injection into Downstream Systems | NOT RUN |
| [TC-L05-016](pages/L05-ai-applications.md#tc-l05-016) | Output Handling: PII in Model Responses | NOT RUN |
| [TC-L05-017](pages/L05-ai-applications.md#tc-l05-017) | Output Handling: Secrets and Credentials in Responses | NOT RUN |
| [TC-L05-018](pages/L05-ai-applications.md#tc-l05-018) | Output Handling: Harmful or Policy-Violating Content | NOT RUN |
| [TC-L05-019](pages/L05-ai-applications.md#tc-l05-019) | Output Handling: Fabricated Package and URL Detection | NOT RUN |
| [TC-L05-020](pages/L05-ai-applications.md#tc-l05-020) | Output Handling: Markdown Image and Link Exfiltration | NOT RUN |
| [TC-L05-021](pages/L05-ai-applications.md#tc-l05-021) | Response Grounding and Citation Verification | NOT RUN |
| [TC-L05-022](pages/L05-ai-applications.md#tc-l05-022) | Structured Output and Function-Call Argument Validation | NOT RUN |
| [TC-L05-023](pages/L05-ai-applications.md#tc-l05-023) | Tenant Data Isolation in Multi-Tenant AI Applications | NOT RUN |
| [TC-L05-024](pages/L05-ai-applications.md#tc-l05-024) | Streaming Response Inspection | NOT RUN |
| [TC-L05-025](pages/L05-ai-applications.md#tc-l05-025) | Application Logging Completeness | NOT RUN |
| [TC-L05-026](pages/L05-ai-applications.md#tc-l05-026) | Multi-Turn Conversation Protection | NOT RUN |
| [TC-L05-027](pages/L05-ai-applications.md#tc-l05-027) | Pre-Production Automated Red-Team Scan | NOT RUN |
| [TC-L05-028](pages/L05-ai-applications.md#tc-l05-028) | Per-Application Policy as Code | NOT RUN |
| [TC-L05-029](pages/L05-ai-applications.md#tc-l05-029) | Orphaned and Decommissioned AI Application Detection | NOT RUN |
| [TC-L05-030](pages/L05-ai-applications.md#tc-l05-030) | Protection Overhead Under Load | NOT RUN |
| [TC-L05-031](pages/L05-ai-applications.md#tc-l05-031) | AI Coding Assistant Extension Inventory and Version Risk | NOT RUN |
| [TC-L05-032](pages/L05-ai-applications.md#tc-l05-032) | Personal vs Corporate Account in AI Coding Assistants | NOT RUN |
| [TC-L05-033](pages/L05-ai-applications.md#tc-l05-033) | Coding Assistant Workspace Context Scope and File Exclusion | NOT RUN |
| [TC-L05-034](pages/L05-ai-applications.md#tc-l05-034) | Insecure Code Suggestion Detection | NOT RUN |
| [TC-L05-035](pages/L05-ai-applications.md#tc-l05-035) | AI-Generated Code: Licence and Public-Code Match Detection | NOT RUN |
| [TC-L06-001](pages/L06-agent-orchestration-layer.md#tc-l06-001) | Agent Discovery Across Platforms and Custom Builds | NOT RUN |
| [TC-L06-002](pages/L06-agent-orchestration-layer.md#tc-l06-002) | Agent Inventory Enrichment: Owner, Tools, Data and Model | NOT RUN |
| [TC-L06-003](pages/L06-agent-orchestration-layer.md#tc-l06-003) | Shadow Agent Detection (Unregistered and Local Agents) | NOT RUN |
| [TC-L06-004](pages/L06-agent-orchestration-layer.md#tc-l06-004) | Low-Code and No-Code Agent Builder Discovery | NOT RUN |
| [TC-L06-005](pages/L06-agent-orchestration-layer.md#tc-l06-005) | MCP Server Discovery (Local and Remote) | NOT RUN |
| [TC-L06-006](pages/L06-agent-orchestration-layer.md#tc-l06-006) | MCP Server Trust: Registry and Allow-List Enforcement | NOT RUN |
| [TC-L06-007](pages/L06-agent-orchestration-layer.md#tc-l06-007) | MCP Tool Description Poisoning | NOT RUN |
| [TC-L06-008](pages/L06-agent-orchestration-layer.md#tc-l06-008) | MCP Rug-Pull: Tool Definition Change After Approval | NOT RUN |
| [TC-L06-009](pages/L06-agent-orchestration-layer.md#tc-l06-009) | MCP Tool Shadowing and Name Collision | NOT RUN |
| [TC-L06-010](pages/L06-agent-orchestration-layer.md#tc-l06-010) | MCP Authentication and Transport Security | NOT RUN |
| [TC-L06-011](pages/L06-agent-orchestration-layer.md#tc-l06-011) | MCP Gateway Policy: Per-Tool Allow and Deny | NOT RUN |
| [TC-L06-012](pages/L06-agent-orchestration-layer.md#tc-l06-012) | Tool Inventory and Permission Scope Mapping | NOT RUN |
| [TC-L06-013](pages/L06-agent-orchestration-layer.md#tc-l06-013) | Least-Privilege Tool Allow-Listing Per Agent | NOT RUN |
| [TC-L06-014](pages/L06-agent-orchestration-layer.md#tc-l06-014) | Tool Call Argument Validation and Parameter-Level Policy | NOT RUN |
| [TC-L06-015](pages/L06-agent-orchestration-layer.md#tc-l06-015) | High-Risk Action Approval (Human in the Loop) | NOT RUN |
| [TC-L06-016](pages/L06-agent-orchestration-layer.md#tc-l06-016) | Approval Fatigue and Approval Bypass Resistance | NOT RUN |
| [TC-L06-017](pages/L06-agent-orchestration-layer.md#tc-l06-017) | Delegation Chains: Sub-Agent Authority Attenuation | NOT RUN |
| [TC-L06-018](pages/L06-agent-orchestration-layer.md#tc-l06-018) | Agent-to-Agent Message Authenticity | NOT RUN |
| [TC-L06-019](pages/L06-agent-orchestration-layer.md#tc-l06-019) | Confused Deputy: Agent Acting Beyond the User's Intent | NOT RUN |
| [TC-L06-020](pages/L06-agent-orchestration-layer.md#tc-l06-020) | Cross-Agent Prompt Injection Propagation | NOT RUN |
| [TC-L06-021](pages/L06-agent-orchestration-layer.md#tc-l06-021) | Runaway Loop and Recursion Detection | NOT RUN |
| [TC-L06-022](pages/L06-agent-orchestration-layer.md#tc-l06-022) | Kill Switch: Stopping a Single Agent | NOT RUN |
| [TC-L06-023](pages/L06-agent-orchestration-layer.md#tc-l06-023) | Kill Switch: Global Credential Revocation and Action Rollback | NOT RUN |
| [TC-L06-024](pages/L06-agent-orchestration-layer.md#tc-l06-024) | Action Rate Limits and Blast-Radius Caps | NOT RUN |
| [TC-L06-025](pages/L06-agent-orchestration-layer.md#tc-l06-025) | Agent Sandboxing for Code Execution | NOT RUN |
| [TC-L06-026](pages/L06-agent-orchestration-layer.md#tc-l06-026) | Agent Runtime File and Network Egress Restrictions | NOT RUN |
| [TC-L06-027](pages/L06-agent-orchestration-layer.md#tc-l06-027) | Goal Hijacking Mid-Task | NOT RUN |
| [TC-L06-028](pages/L06-agent-orchestration-layer.md#tc-l06-028) | Agent Action Logging and Replayable Traces | NOT RUN |
| [TC-L06-029](pages/L06-agent-orchestration-layer.md#tc-l06-029) | Agent Behaviour Baselining and Anomaly Detection | NOT RUN |
| [TC-L06-030](pages/L06-agent-orchestration-layer.md#tc-l06-030) | Tool Output DLP and Sanitisation | NOT RUN |
| [TC-L06-031](pages/L06-agent-orchestration-layer.md#tc-l06-031) | Browser and Computer-Use Agent Controls | NOT RUN |
| [TC-L06-032](pages/L06-agent-orchestration-layer.md#tc-l06-032) | Third-Party Agent and Plugin Vetting | NOT RUN |
| [TC-L06-033](pages/L06-agent-orchestration-layer.md#tc-l06-033) | Orchestration Graph Policy as Code | NOT RUN |
| [TC-L06-034](pages/L06-agent-orchestration-layer.md#tc-l06-034) | Agent Change Control and Re-Approval | NOT RUN |
| [TC-L06-035](pages/L06-agent-orchestration-layer.md#tc-l06-035) | Agent Decommissioning and Orphan Agent Handling | NOT RUN |
| [TC-L06-036](pages/L06-agent-orchestration-layer.md#tc-l06-036) | Coding Agent Terminal Command and File-System Guardrails | NOT RUN |
| [TC-L06-037](pages/L06-agent-orchestration-layer.md#tc-l06-037) | IDE and Coding Agent MCP Server Configuration Discovery | NOT RUN |
| [TC-L06-038](pages/L06-agent-orchestration-layer.md#tc-l06-038) | Agent Trust Map: Permitted Agent-to-Agent Relationships | NOT RUN |
| [TC-L06-039](pages/L06-agent-orchestration-layer.md#tc-l06-039) | Inter-Agent Request Authorisation: Low-Trust Agent Instructing a High-Trust Agent | NOT RUN |
| [TC-L06-040](pages/L06-agent-orchestration-layer.md#tc-l06-040) | Inter-Agent Message Schema and Content Validation | NOT RUN |
| [TC-L06-041](pages/L06-agent-orchestration-layer.md#tc-l06-041) | Agent Discovery and Agent Card Spoofing | NOT RUN |
| [TC-L06-042](pages/L06-agent-orchestration-layer.md#tc-l06-042) | Inter-Agent Channel Encryption and Protocol Downgrade | NOT RUN |
| [TC-L06-043](pages/L06-agent-orchestration-layer.md#tc-l06-043) | Cross-Organisation Agent Federation: Third-Party Agent Trust | NOT RUN |
| [TC-L06-044](pages/L06-agent-orchestration-layer.md#tc-l06-044) | Hand-Off Data Scope: Context Over-Sharing Between Agents | NOT RUN |
| [TC-L06-045](pages/L06-agent-orchestration-layer.md#tc-l06-045) | Inter-Agent Request Logging and Cross-Agent Trace Correlation | NOT RUN |
| [TC-L06-046](pages/L06-agent-orchestration-layer.md#tc-l06-046) | Compromised Agent Containment in a Multi-Agent System | NOT RUN |
| [TC-L07-001](pages/L07-prompt-and-context-layer.md#tc-l07-001) | Direct Injection: Instruction Override Baseline | NOT RUN |
| [TC-L07-002](pages/L07-prompt-and-context-layer.md#tc-l07-002) | Direct Injection: Delimiter and Format Confusion | NOT RUN |
| [TC-L07-003](pages/L07-prompt-and-context-layer.md#tc-l07-003) | Direct Injection: Authority and Role Impersonation | NOT RUN |
| [TC-L07-004](pages/L07-prompt-and-context-layer.md#tc-l07-004) | Direct Injection: Payload Splitting Across Turns | NOT RUN |
| [TC-L07-005](pages/L07-prompt-and-context-layer.md#tc-l07-005) | Direct Injection: Encoded and Obfuscated Payloads | NOT RUN |
| [TC-L07-006](pages/L07-prompt-and-context-layer.md#tc-l07-006) | Direct Injection: Multilingual Payloads (Arabic, Hindi, Urdu, French) | NOT RUN |
| [TC-L07-007](pages/L07-prompt-and-context-layer.md#tc-l07-007) | Direct Injection: Long-Context Burying and Many-Shot Patterns | NOT RUN |
| [TC-L07-008](pages/L07-prompt-and-context-layer.md#tc-l07-008) | Direct Injection Leading to Unauthorised Tool Action | NOT RUN |
| [TC-L07-009](pages/L07-prompt-and-context-layer.md#tc-l07-009) | Indirect Injection: Web Page Content | NOT RUN |
| [TC-L07-010](pages/L07-prompt-and-context-layer.md#tc-l07-010) | Indirect Injection: Email and Document Content | NOT RUN |
| [TC-L07-011](pages/L07-prompt-and-context-layer.md#tc-l07-011) | Indirect Injection: Hidden Text and File Metadata | NOT RUN |
| [TC-L07-012](pages/L07-prompt-and-context-layer.md#tc-l07-012) | Indirect Injection: Retrieved Knowledge Base Documents | NOT RUN |
| [TC-L07-013](pages/L07-prompt-and-context-layer.md#tc-l07-013) | Indirect Injection: Tool and API Responses | NOT RUN |
| [TC-L07-014](pages/L07-prompt-and-context-layer.md#tc-l07-014) | Indirect Injection: Images with Embedded Text | NOT RUN |
| [TC-L07-015](pages/L07-prompt-and-context-layer.md#tc-l07-015) | Indirect Injection: Collaboration Data (Chat, Tickets, Calendar) | NOT RUN |
| [TC-L07-016](pages/L07-prompt-and-context-layer.md#tc-l07-016) | Indirect Injection Driving Data Exfiltration via URL | NOT RUN |
| [TC-L07-017](pages/L07-prompt-and-context-layer.md#tc-l07-017) | Jailbreak: Persona and Role-Play | NOT RUN |
| [TC-L07-018](pages/L07-prompt-and-context-layer.md#tc-l07-018) | Jailbreak: Hypothetical and Fictional Framing | NOT RUN |
| [TC-L07-019](pages/L07-prompt-and-context-layer.md#tc-l07-019) | Jailbreak: Gradual Multi-Turn Escalation | NOT RUN |
| [TC-L07-020](pages/L07-prompt-and-context-layer.md#tc-l07-020) | Jailbreak: Refusal Suppression and Prefix Injection | NOT RUN |
| [TC-L07-021](pages/L07-prompt-and-context-layer.md#tc-l07-021) | Jailbreak: Automated Adversarial Suffixes and Fuzzing | NOT RUN |
| [TC-L07-022](pages/L07-prompt-and-context-layer.md#tc-l07-022) | Jailbreak: Cross-Lingual and Low-Resource Languages | NOT RUN |
| [TC-L07-023](pages/L07-prompt-and-context-layer.md#tc-l07-023) | Jailbreak: Instructions Embedded in Images (Multimodal) | NOT RUN |
| [TC-L07-024](pages/L07-prompt-and-context-layer.md#tc-l07-024) | Jailbreak Regression After Model or Policy Update | NOT RUN |
| [TC-L07-025](pages/L07-prompt-and-context-layer.md#tc-l07-025) | System Prompt Extraction Under Probing | NOT RUN |
| [TC-L07-026](pages/L07-prompt-and-context-layer.md#tc-l07-026) | Instruction Hierarchy Enforcement | NOT RUN |
| [TC-L07-027](pages/L07-prompt-and-context-layer.md#tc-l07-027) | Context Window Poisoning Within a Session | NOT RUN |
| [TC-L07-028](pages/L07-prompt-and-context-layer.md#tc-l07-028) | Long-Term Memory Poisoning | NOT RUN |
| [TC-L07-029](pages/L07-prompt-and-context-layer.md#tc-l07-029) | Memory Isolation Between Users | NOT RUN |
| [TC-L07-030](pages/L07-prompt-and-context-layer.md#tc-l07-030) | Memory Deletion and Retention Verification | NOT RUN |
| [TC-L07-031](pages/L07-prompt-and-context-layer.md#tc-l07-031) | Conversation History Tampering via API | NOT RUN |
| [TC-L07-032](pages/L07-prompt-and-context-layer.md#tc-l07-032) | Context Stuffing and Token Flooding | NOT RUN |
| [TC-L07-033](pages/L07-prompt-and-context-layer.md#tc-l07-033) | Prompt Template Injection (Variable Interpolation) | NOT RUN |
| [TC-L07-034](pages/L07-prompt-and-context-layer.md#tc-l07-034) | Prompt Library and Shared Prompt Store Integrity | NOT RUN |
| [TC-L07-035](pages/L07-prompt-and-context-layer.md#tc-l07-035) | Context Provenance and Trust Labelling | NOT RUN |
| [TC-L07-036](pages/L07-prompt-and-context-layer.md#tc-l07-036) | Canary Token and Leak Detection | NOT RUN |
| [TC-L07-037](pages/L07-prompt-and-context-layer.md#tc-l07-037) | Injection Detection Explainability and Alert Triage | NOT RUN |
| [TC-L07-038](pages/L07-prompt-and-context-layer.md#tc-l07-038) | Human Approval for Suspected Injection in Tool Flows | NOT RUN |
| [TC-L07-039](pages/L07-prompt-and-context-layer.md#tc-l07-039) | Secrets and Personal Data in System Prompts and Few-Shot Examples | NOT RUN |
| [TC-L07-040](pages/L07-prompt-and-context-layer.md#tc-l07-040) | Detection Update Cadence and Benchmark Coverage | NOT RUN |
| [TC-L07-041](pages/L07-prompt-and-context-layer.md#tc-l07-041) | Indirect Injection: Repository Files, Comments and Assistant Rule Files | NOT RUN |
| [TC-L08-001](pages/L08-ai-gateway-and-security-controls.md#tc-l08-001) | Deployment Mode and Traffic Coverage Verification | NOT RUN |
| [TC-L08-002](pages/L08-ai-gateway-and-security-controls.md#tc-l08-002) | Allow and Deny by AI Application and Category | NOT RUN |
| [TC-L08-003](pages/L08-ai-gateway-and-security-controls.md#tc-l08-003) | Policy by User, Group and Context | NOT RUN |
| [TC-L08-004](pages/L08-ai-gateway-and-security-controls.md#tc-l08-004) | DLP: Personal Data in Prompts | NOT RUN |
| [TC-L08-005](pages/L08-ai-gateway-and-security-controls.md#tc-l08-005) | DLP: Payment Card and Financial Data | NOT RUN |
| [TC-L08-006](pages/L08-ai-gateway-and-security-controls.md#tc-l08-006) | DLP: UAE and GCC Identifiers | NOT RUN |
| [TC-L08-007](pages/L08-ai-gateway-and-security-controls.md#tc-l08-007) | DLP: Source Code and Secrets | NOT RUN |
| [TC-L08-008](pages/L08-ai-gateway-and-security-controls.md#tc-l08-008) | DLP: Custom Dictionary and Document Fingerprinting | NOT RUN |
| [TC-L08-009](pages/L08-ai-gateway-and-security-controls.md#tc-l08-009) | DLP: Action Modes (Block, Mask, Warn, Log) | NOT RUN |
| [TC-L08-010](pages/L08-ai-gateway-and-security-controls.md#tc-l08-010) | DLP: Reversible Pseudonymisation Round Trip | NOT RUN |
| [TC-L08-011](pages/L08-ai-gateway-and-security-controls.md#tc-l08-011) | DLP: Encoded and Fragmented Data | NOT RUN |
| [TC-L08-012](pages/L08-ai-gateway-and-security-controls.md#tc-l08-012) | DLP: File Types and Nested Archives | NOT RUN |
| [TC-L08-013](pages/L08-ai-gateway-and-security-controls.md#tc-l08-013) | DLP: Sensitive Text Inside Images | NOT RUN |
| [TC-L08-014](pages/L08-ai-gateway-and-security-controls.md#tc-l08-014) | DLP: Arabic and Mixed-Script Content | NOT RUN |
| [TC-L08-015](pages/L08-ai-gateway-and-security-controls.md#tc-l08-015) | Guardrail Detection Accuracy Baseline | NOT RUN |
| [TC-L08-016](pages/L08-ai-gateway-and-security-controls.md#tc-l08-016) | Guardrail: Jailbreak Policy | NOT RUN |
| [TC-L08-017](pages/L08-ai-gateway-and-security-controls.md#tc-l08-017) | Guardrail: Topic and Off-Policy Restriction | NOT RUN |
| [TC-L08-018](pages/L08-ai-gateway-and-security-controls.md#tc-l08-018) | Guardrail: Toxic and Harmful Output | NOT RUN |
| [TC-L08-019](pages/L08-ai-gateway-and-security-controls.md#tc-l08-019) | Guardrail: System Prompt Leakage | NOT RUN |
| [TC-L08-020](pages/L08-ai-gateway-and-security-controls.md#tc-l08-020) | Guardrail: Response-Side DLP | NOT RUN |
| [TC-L08-021](pages/L08-ai-gateway-and-security-controls.md#tc-l08-021) | Bypass Resistance: Unicode, Homoglyph and Obfuscation | NOT RUN |
| [TC-L08-022](pages/L08-ai-gateway-and-security-controls.md#tc-l08-022) | Bypass Resistance: Protocol Variants | NOT RUN |
| [TC-L08-023](pages/L08-ai-gateway-and-security-controls.md#tc-l08-023) | Bypass Resistance: Alternate Endpoints, VPN and DoH | NOT RUN |
| [TC-L08-024](pages/L08-ai-gateway-and-security-controls.md#tc-l08-024) | Bypass Resistance: Certificate Pinning and TLS Inspection Exceptions | NOT RUN |
| [TC-L08-025](pages/L08-ai-gateway-and-security-controls.md#tc-l08-025) | Bypass Resistance: Agent Tampering and Uninstall | NOT RUN |
| [TC-L08-026](pages/L08-ai-gateway-and-security-controls.md#tc-l08-026) | Bypass Resistance: Native Apps, CLI and SDK Traffic | NOT RUN |
| [TC-L08-027](pages/L08-ai-gateway-and-security-controls.md#tc-l08-027) | Bypass Resistance: Translation and Paraphrase Evasion | NOT RUN |
| [TC-L08-028](pages/L08-ai-gateway-and-security-controls.md#tc-l08-028) | Model Provider and Model Allow-List Enforcement | NOT RUN |
| [TC-L08-029](pages/L08-ai-gateway-and-security-controls.md#tc-l08-029) | Central API Key Management at the Gateway | NOT RUN |
| [TC-L08-030](pages/L08-ai-gateway-and-security-controls.md#tc-l08-030) | Rate Limiting and Token Quotas | NOT RUN |
| [TC-L08-031](pages/L08-ai-gateway-and-security-controls.md#tc-l08-031) | Cost Controls and Budget Alerts | NOT RUN |
| [TC-L08-032](pages/L08-ai-gateway-and-security-controls.md#tc-l08-032) | Latency Overhead Under Normal Load | NOT RUN |
| [TC-L08-033](pages/L08-ai-gateway-and-security-controls.md#tc-l08-033) | Throughput and Behaviour at Peak Load | NOT RUN |
| [TC-L08-034](pages/L08-ai-gateway-and-security-controls.md#tc-l08-034) | High Availability and Failover | NOT RUN |
| [TC-L08-035](pages/L08-ai-gateway-and-security-controls.md#tc-l08-035) | Streaming Inspection Without Breaking User Experience | NOT RUN |
| [TC-L08-036](pages/L08-ai-gateway-and-security-controls.md#tc-l08-036) | Policy Change Propagation and Rollback | NOT RUN |
| [TC-L08-037](pages/L08-ai-gateway-and-security-controls.md#tc-l08-037) | Monitor-Only Mode and False-Positive Review | NOT RUN |
| [TC-L08-038](pages/L08-ai-gateway-and-security-controls.md#tc-l08-038) | Block Page Customisation and Arabic Localisation | NOT RUN |
| [TC-L08-039](pages/L08-ai-gateway-and-security-controls.md#tc-l08-039) | Administrator RBAC and Policy Change Audit | NOT RUN |
| [TC-L08-040](pages/L08-ai-gateway-and-security-controls.md#tc-l08-040) | Log Content, Masking and Retention Controls | NOT RUN |
| [TC-L08-041](pages/L08-ai-gateway-and-security-controls.md#tc-l08-041) | Repository-Aware Policy for AI Assistance (Restricted Repositories and File Types) | NOT RUN |
| [TC-L08-042](pages/L08-ai-gateway-and-security-controls.md#tc-l08-042) | Coding Assistant Model, Provider and Local-Model Allow-List | NOT RUN |
| [TC-L09-001](pages/L09-identity-and-access-mgmt.md#tc-l09-001) | Non-Human Identity Inventory for AI Workloads | NOT RUN |
| [TC-L09-002](pages/L09-identity-and-access-mgmt.md#tc-l09-002) | Unique Identity Per Agent (No Shared Credentials) | NOT RUN |
| [TC-L09-003](pages/L09-identity-and-access-mgmt.md#tc-l09-003) | Short-Lived Scoped Credentials for Agents | NOT RUN |
| [TC-L09-004](pages/L09-identity-and-access-mgmt.md#tc-l09-004) | Token Scope Enforcement Per Tool and Resource | NOT RUN |
| [TC-L09-005](pages/L09-identity-and-access-mgmt.md#tc-l09-005) | OAuth Consent and Grant Control for AI Applications | NOT RUN |
| [TC-L09-006](pages/L09-identity-and-access-mgmt.md#tc-l09-006) | Delegated User Identity Propagation (On-Behalf-Of) | NOT RUN |
| [TC-L09-007](pages/L09-identity-and-access-mgmt.md#tc-l09-007) | Privilege Escalation via Agent | NOT RUN |
| [TC-L09-008](pages/L09-identity-and-access-mgmt.md#tc-l09-008) | Role-Based Access to AI Applications and Models | NOT RUN |
| [TC-L09-009](pages/L09-identity-and-access-mgmt.md#tc-l09-009) | Attribute and Context-Based Access Conditions | NOT RUN |
| [TC-L09-010](pages/L09-identity-and-access-mgmt.md#tc-l09-010) | SSO and SCIM Integration for the AI Platform | NOT RUN |
| [TC-L09-011](pages/L09-identity-and-access-mgmt.md#tc-l09-011) | Leaver and Mover Access Removal for AI Access | NOT RUN |
| [TC-L09-012](pages/L09-identity-and-access-mgmt.md#tc-l09-012) | Step-Up Authentication for Sensitive AI Actions | NOT RUN |
| [TC-L09-013](pages/L09-identity-and-access-mgmt.md#tc-l09-013) | Privileged Access to the AI Platform (Just-in-Time and Separation) | NOT RUN |
| [TC-L09-014](pages/L09-identity-and-access-mgmt.md#tc-l09-014) | Model API Key Lifecycle: Issue, Rotate, Expire, Revoke | NOT RUN |
| [TC-L09-015](pages/L09-identity-and-access-mgmt.md#tc-l09-015) | Credentials Passing Through Prompts and Tool Arguments | NOT RUN |
| [TC-L09-016](pages/L09-identity-and-access-mgmt.md#tc-l09-016) | Vault Integration: Agents Retrieve Secrets Without Exposure | NOT RUN |
| [TC-L09-017](pages/L09-identity-and-access-mgmt.md#tc-l09-017) | Anomalous Use of Agent and Service Identities | NOT RUN |
| [TC-L09-018](pages/L09-identity-and-access-mgmt.md#tc-l09-018) | Impersonation Resistance: Agent or User Claims Another Identity | NOT RUN |
| [TC-L09-019](pages/L09-identity-and-access-mgmt.md#tc-l09-019) | Environment and Tenant Identity Boundaries (Prod vs Non-Prod) | NOT RUN |
| [TC-L09-020](pages/L09-identity-and-access-mgmt.md#tc-l09-020) | Session Management for AI Chat Sessions | NOT RUN |
| [TC-L09-021](pages/L09-identity-and-access-mgmt.md#tc-l09-021) | Access Reviews and Recertification for AI Access | NOT RUN |
| [TC-L09-022](pages/L09-identity-and-access-mgmt.md#tc-l09-022) | Effective Permissions Visibility for Users and Agents | NOT RUN |
| [TC-L09-023](pages/L09-identity-and-access-mgmt.md#tc-l09-023) | Emergency (Break-Glass) Access Controls | NOT RUN |
| [TC-L09-024](pages/L09-identity-and-access-mgmt.md#tc-l09-024) | Mutual Authentication Between AI Components | NOT RUN |
| [TC-L09-025](pages/L09-identity-and-access-mgmt.md#tc-l09-025) | Identity Audit Trail: Who, What and On Whose Behalf | NOT RUN |
| [TC-L09-026](pages/L09-identity-and-access-mgmt.md#tc-l09-026) | Coding Agent Repository and Cloud Credentials: Scope and Lifetime | NOT RUN |
| [TC-L10-001](pages/L10-data-layer.md#tc-l10-001) | Sensitive Data Discovery in AI Data Stores | NOT RUN |
| [TC-L10-002](pages/L10-data-layer.md#tc-l10-002) | Classification Accuracy on Structured Data | NOT RUN |
| [TC-L10-003](pages/L10-data-layer.md#tc-l10-003) | Classification Accuracy on Unstructured Documents | NOT RUN |
| [TC-L10-004](pages/L10-data-layer.md#tc-l10-004) | Classification of Arabic and Regional-Language Documents | NOT RUN |
| [TC-L10-005](pages/L10-data-layer.md#tc-l10-005) | Label Inheritance to AI Outputs and Derived Data | NOT RUN |
| [TC-L10-006](pages/L10-data-layer.md#tc-l10-006) | Label-Aware Access: AI Cannot Read Beyond User Entitlement | NOT RUN |
| [TC-L10-007](pages/L10-data-layer.md#tc-l10-007) | Field-Level Masking and Data Minimisation Before the Model | NOT RUN |
| [TC-L10-008](pages/L10-data-layer.md#tc-l10-008) | Data Lineage: Source to Prompt to Output | NOT RUN |
| [TC-L10-009](pages/L10-data-layer.md#tc-l10-009) | Lineage for Knowledge Base and Dataset Versions | NOT RUN |
| [TC-L10-010](pages/L10-data-layer.md#tc-l10-010) | Tenant Isolation in Shared AI Data Stores | NOT RUN |
| [TC-L10-011](pages/L10-data-layer.md#tc-l10-011) | Tenant Isolation Under Adversarial Probing | NOT RUN |
| [TC-L10-012](pages/L10-data-layer.md#tc-l10-012) | Data Residency: Processing Region Enforcement | NOT RUN |
| [TC-L10-013](pages/L10-data-layer.md#tc-l10-013) | Data Residency: Logs, Telemetry, Backups and Support Access | NOT RUN |
| [TC-L10-014](pages/L10-data-layer.md#tc-l10-014) | Cross-Border Transfer Detection to Non-Approved Providers | NOT RUN |
| [TC-L10-015](pages/L10-data-layer.md#tc-l10-015) | Encryption and Key Ownership (BYOK and HYOK) | NOT RUN |
| [TC-L10-016](pages/L10-data-layer.md#tc-l10-016) | Key Rotation and Crypto-Shredding | NOT RUN |
| [TC-L10-017](pages/L10-data-layer.md#tc-l10-017) | Dataset Access Control for AI Service Identities | NOT RUN |
| [TC-L10-018](pages/L10-data-layer.md#tc-l10-018) | Oversharing Discovery: Data Reachable by AI Assistants Beyond Need | NOT RUN |
| [TC-L10-019](pages/L10-data-layer.md#tc-l10-019) | Bulk Data Extraction Through AI Queries | NOT RUN |
| [TC-L10-020](pages/L10-data-layer.md#tc-l10-020) | Retention and Deletion Across the AI Pipeline | NOT RUN |
| [TC-L10-021](pages/L10-data-layer.md#tc-l10-021) | Erasure Propagation to Vector Stores and Derived Data | NOT RUN |
| [TC-L10-022](pages/L10-data-layer.md#tc-l10-022) | Data Subject Access Request Support | NOT RUN |
| [TC-L10-023](pages/L10-data-layer.md#tc-l10-023) | Production Data in Development and Test AI Environments | NOT RUN |
| [TC-L10-024](pages/L10-data-layer.md#tc-l10-024) | Ingestion Validation for Untrusted Data Sources | NOT RUN |
| [TC-L10-025](pages/L10-data-layer.md#tc-l10-025) | Provider Data-Use Terms: Zero Retention and No Training Verification | NOT RUN |
| [TC-L10-026](pages/L10-data-layer.md#tc-l10-026) | Data Access Forensics: Who Accessed What via AI | NOT RUN |
| [TC-L10-027](pages/L10-data-layer.md#tc-l10-027) | Insider Investigation Workflow and Case Management | NOT RUN |
| [TC-L10-028](pages/L10-data-layer.md#tc-l10-028) | Legal Hold and eDiscovery for AI Conversations | NOT RUN |
| [TC-L10-029](pages/L10-data-layer.md#tc-l10-029) | Classification and Label Synchronisation with Enterprise Tools | NOT RUN |
| [TC-L10-030](pages/L10-data-layer.md#tc-l10-030) | Leakage Metrics and Regulatory Reporting Evidence | NOT RUN |
| [TC-L10-031](pages/L10-data-layer.md#tc-l10-031) | Dataset Quality Thresholds Before Training or Fine-Tuning | NOT RUN |
| [TC-L10-032](pages/L10-data-layer.md#tc-l10-032) | Retrieval Corpus Currentness and Source Credibility | NOT RUN |
| [TC-L10-033](pages/L10-data-layer.md#tc-l10-033) | Data Quality Profile and Evidence for Audit | NOT RUN |
| [TC-L11-001](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-001) | Knowledge Source and Connector Inventory | NOT RUN |
| [TC-L11-002](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-002) | Vector Store Discovery and Exposure | NOT RUN |
| [TC-L11-003](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-003) | Vector Store Authentication and Hardening Checks | NOT RUN |
| [TC-L11-004](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-004) | Document-Level Access Control at Retrieval | NOT RUN |
| [TC-L11-005](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-005) | Permission Change Propagation to the Index | NOT RUN |
| [TC-L11-006](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-006) | Retrieval Leakage via Semantic Neighbours | NOT RUN |
| [TC-L11-007](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-007) | Namespace and Tenant Isolation in the Vector Store | NOT RUN |
| [TC-L11-008](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-008) | RAG Poisoning: False Facts in Indexed Documents | NOT RUN |
| [TC-L11-009](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-009) | RAG Poisoning: Trigger-Phrase Retrieval Hijack | NOT RUN |
| [TC-L11-010](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-010) | Ingestion Provenance and Approval Workflow | NOT RUN |
| [TC-L11-011](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-011) | Indexed Content Integrity and Tamper Detection | NOT RUN |
| [TC-L11-012](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-012) | Embedding Inversion and Text Recovery Risk | NOT RUN |
| [TC-L11-013](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-013) | Embedding Model Version Change and Re-Indexing Integrity | NOT RUN |
| [TC-L11-014](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-014) | Chunk Metadata Injection | NOT RUN |
| [TC-L11-015](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-015) | Sensitive Data Scan Before Indexing | NOT RUN |
| [TC-L11-016](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-016) | Retrieval-Time Filtering by User Clearance | NOT RUN |
| [TC-L11-017](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-017) | Citation and Source Attribution Integrity | NOT RUN |
| [TC-L11-018](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-018) | Stale, Withdrawn and Expired Content Handling | NOT RUN |
| [TC-L11-019](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-019) | Knowledge Base Extraction and Crawling Detection | NOT RUN |
| [TC-L11-020](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-020) | Query Rewriting and Expansion Safety | NOT RUN |
| [TC-L11-021](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-021) | Reranker and Hybrid Search Manipulation | NOT RUN |
| [TC-L11-022](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-022) | Connector Credentials and Scope Security | NOT RUN |
| [TC-L11-023](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-023) | Knowledge Base Backup and Export Controls | NOT RUN |
| [TC-L11-024](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-024) | Retrieval Logging and Audit Completeness | NOT RUN |
| [TC-L11-025](pages/L11-knowledge-and-retrieval-layer.md#tc-l11-025) | Security Control Impact on Answer Quality | NOT RUN |
| [TC-L12-001](pages/L12-model-layer.md#tc-l12-001) | Model Inventory and Registry Discovery | NOT RUN |
| [TC-L12-002](pages/L12-model-layer.md#tc-l12-002) | Model Artefact Scanning: Unsafe Serialisation | NOT RUN |
| [TC-L12-003](pages/L12-model-layer.md#tc-l12-003) | Model Scanning: Backdoor and Trojan Indicators | NOT RUN |
| [TC-L12-004](pages/L12-model-layer.md#tc-l12-004) | Model File Format Policy Enforcement | NOT RUN |
| [TC-L12-005](pages/L12-model-layer.md#tc-l12-005) | Model Provenance and Signature Verification | NOT RUN |
| [TC-L12-006](pages/L12-model-layer.md#tc-l12-006) | Model Licence and Usage Terms Check | NOT RUN |
| [TC-L12-007](pages/L12-model-layer.md#tc-l12-007) | Model Extraction Attack Detection | NOT RUN |
| [TC-L12-008](pages/L12-model-layer.md#tc-l12-008) | Training Data Extraction and Memorisation Probes | NOT RUN |
| [TC-L12-009](pages/L12-model-layer.md#tc-l12-009) | Model Weights Exfiltration Protection | NOT RUN |
| [TC-L12-010](pages/L12-model-layer.md#tc-l12-010) | Adversarial Image Robustness for Vision Models | NOT RUN |
| [TC-L12-011](pages/L12-model-layer.md#tc-l12-011) | Adversarial Text Perturbation Robustness for Classifiers | NOT RUN |
| [TC-L12-012](pages/L12-model-layer.md#tc-l12-012) | Inference-Time Input Anomaly Detection | NOT RUN |
| [TC-L12-013](pages/L12-model-layer.md#tc-l12-013) | Inference Endpoint Authentication, Authorisation and Rate Limiting | NOT RUN |
| [TC-L12-014](pages/L12-model-layer.md#tc-l12-014) | Model-Level Access Control by User, Role and Version | NOT RUN |
| [TC-L12-015](pages/L12-model-layer.md#tc-l12-015) | Model Fingerprinting and Unauthorised Copy Identification | NOT RUN |
| [TC-L12-016](pages/L12-model-layer.md#tc-l12-016) | Safety Evaluation Baseline for Deployed Models | NOT RUN |
| [TC-L12-017](pages/L12-model-layer.md#tc-l12-017) | Hallucination and Factuality Evaluation Baseline | NOT RUN |
| [TC-L12-018](pages/L12-model-layer.md#tc-l12-018) | Model Version Pinning and Behaviour Drift Detection | NOT RUN |
| [TC-L12-019](pages/L12-model-layer.md#tc-l12-019) | Model Cards and AI-BOM Completeness | NOT RUN |
| [TC-L12-020](pages/L12-model-layer.md#tc-l12-020) | Model Deployment Configuration Hardening | NOT RUN |
| [TC-L12-021](pages/L12-model-layer.md#tc-l12-021) | Multi-Model Routing and Fallback Security | NOT RUN |
| [TC-L12-022](pages/L12-model-layer.md#tc-l12-022) | Model Resource Exhaustion and Long-Sequence Abuse | NOT RUN |
| [TC-L12-023](pages/L12-model-layer.md#tc-l12-023) | Quantised and Converted Model Integrity | NOT RUN |
| [TC-L12-024](pages/L12-model-layer.md#tc-l12-024) | Model Retirement and Weight Disposal | NOT RUN |
| [TC-L12-025](pages/L12-model-layer.md#tc-l12-025) | Model Risk Tiering and Assessment Workflow | NOT RUN |
| [TC-L12-026](pages/L12-model-layer.md#tc-l12-026) | Model Serving Workload Identity and Scoped Access to Weights | NOT RUN |
| [TC-L12-027](pages/L12-model-layer.md#tc-l12-027) | Calling Workload Attribution at Inference Endpoints: No Shared Application Keys | NOT RUN |
| [TC-L12-028](pages/L12-model-layer.md#tc-l12-028) | Privileged Access to Model Weights and the Registry: Just-in-Time and Dual Approval | NOT RUN |
| [TC-L12-029](pages/L12-model-layer.md#tc-l12-029) | Tenant and Owner Isolation for Fine-Tuned Models | NOT RUN |
| [TC-L12-030](pages/L12-model-layer.md#tc-l12-030) | Access Recertification for Model Registry and Serving Entitlements | NOT RUN |
| [TC-L12-031](pages/L12-model-layer.md#tc-l12-031) | Identity Audit Trail for Model Access: Download, Load and Promotion Events | NOT RUN |
| [TC-L13-001](pages/L13-training-and-fine-tuning-layer.md#tc-l13-001) | Training Dataset Inventory and Ownership | NOT RUN |
| [TC-L13-002](pages/L13-training-and-fine-tuning-layer.md#tc-l13-002) | Dataset Provenance, Licence and Consent Verification | NOT RUN |
| [TC-L13-003](pages/L13-training-and-fine-tuning-layer.md#tc-l13-003) | Data Poisoning: Label Flipping Detection | NOT RUN |
| [TC-L13-004](pages/L13-training-and-fine-tuning-layer.md#tc-l13-004) | Data Poisoning: Backdoor Trigger Insertion in Fine-Tuning Data | NOT RUN |
| [TC-L13-005](pages/L13-training-and-fine-tuning-layer.md#tc-l13-005) | Outlier and Anomaly Screening at Ingestion | NOT RUN |
| [TC-L13-006](pages/L13-training-and-fine-tuning-layer.md#tc-l13-006) | Personal Data and Secrets in Training Data | NOT RUN |
| [TC-L13-007](pages/L13-training-and-fine-tuning-layer.md#tc-l13-007) | Copyright, Opt-Out and Terms Compliance for Training Data | NOT RUN |
| [TC-L13-008](pages/L13-training-and-fine-tuning-layer.md#tc-l13-008) | Fine-Tuning Job Access Control and Approval | NOT RUN |
| [TC-L13-009](pages/L13-training-and-fine-tuning-layer.md#tc-l13-009) | Data Exfiltration via Provider Fine-Tuning Interfaces | NOT RUN |
| [TC-L13-010](pages/L13-training-and-fine-tuning-layer.md#tc-l13-010) | Safety Regression After Fine-Tuning | NOT RUN |
| [TC-L13-011](pages/L13-training-and-fine-tuning-layer.md#tc-l13-011) | Training Environment Isolation and Egress Control | NOT RUN |
| [TC-L13-012](pages/L13-training-and-fine-tuning-layer.md#tc-l13-012) | Checkpoint and Artefact Integrity | NOT RUN |
| [TC-L13-013](pages/L13-training-and-fine-tuning-layer.md#tc-l13-013) | Training Run Reproducibility and Audit Record | NOT RUN |
| [TC-L13-014](pages/L13-training-and-fine-tuning-layer.md#tc-l13-014) | Third-Party Dataset and Base Model Ingestion Vetting | NOT RUN |
| [TC-L13-015](pages/L13-training-and-fine-tuning-layer.md#tc-l13-015) | Synthetic Data Generation Controls | NOT RUN |
| [TC-L13-016](pages/L13-training-and-fine-tuning-layer.md#tc-l13-016) | Distributed and Federated Training Participant Trust | NOT RUN |
| [TC-L13-017](pages/L13-training-and-fine-tuning-layer.md#tc-l13-017) | Memorisation Testing of Fine-Tuned Models | NOT RUN |
| [TC-L13-018](pages/L13-training-and-fine-tuning-layer.md#tc-l13-018) | Feedback Loop and Preference Data Poisoning | NOT RUN |
| [TC-L13-019](pages/L13-training-and-fine-tuning-layer.md#tc-l13-019) | Data Deletion and Unlearning Request Handling | NOT RUN |
| [TC-L13-020](pages/L13-training-and-fine-tuning-layer.md#tc-l13-020) | Unauthorised Training Compute and Resource Abuse | NOT RUN |
| [TC-L13-021](pages/L13-training-and-fine-tuning-layer.md#tc-l13-021) | Training Job Workload Identity: Unique Identity Per Job, No Static Keys | NOT RUN |
| [TC-L13-022](pages/L13-training-and-fine-tuning-layer.md#tc-l13-022) | Least-Privilege Dataset Access Scoped to the Approved Training Run | NOT RUN |
| [TC-L13-023](pages/L13-training-and-fine-tuning-layer.md#tc-l13-023) | Training Credential Lifetime and Revocation at Job End | NOT RUN |
| [TC-L13-024](pages/L13-training-and-fine-tuning-layer.md#tc-l13-024) | Human Access to Training Environments: Roles, Just-in-Time Access and Separation of Duties | NOT RUN |
| [TC-L13-025](pages/L13-training-and-fine-tuning-layer.md#tc-l13-025) | Identity Attribution in Training Run Records | NOT RUN |
| [TC-L13-026](pages/L13-training-and-fine-tuning-layer.md#tc-l13-026) | Dormant and Orphaned Training Identities | NOT RUN |
| [TC-L14-001](pages/L14-mlops-llmops-layer.md#tc-l14-001) | AI Pipeline and LLMOps Tool Inventory | NOT RUN |
| [TC-L14-002](pages/L14-mlops-llmops-layer.md#tc-l14-002) | CI/CD Security Gates for AI Releases | NOT RUN |
| [TC-L14-003](pages/L14-mlops-llmops-layer.md#tc-l14-003) | Artefact Signing and Verification (Models, Containers, Prompts) | NOT RUN |
| [TC-L14-004](pages/L14-mlops-llmops-layer.md#tc-l14-004) | Model Registry Access Control and Immutability | NOT RUN |
| [TC-L14-005](pages/L14-mlops-llmops-layer.md#tc-l14-005) | Prompts and Configuration as Code: Review and Version Control | NOT RUN |
| [TC-L14-006](pages/L14-mlops-llmops-layer.md#tc-l14-006) | Secrets in Pipelines, Notebooks and Experiment Logs | NOT RUN |
| [TC-L14-007](pages/L14-mlops-llmops-layer.md#tc-l14-007) | Notebook Server Security | NOT RUN |
| [TC-L14-008](pages/L14-mlops-llmops-layer.md#tc-l14-008) | Pipeline Runner Least Privilege | NOT RUN |
| [TC-L14-009](pages/L14-mlops-llmops-layer.md#tc-l14-009) | Dependency Scanning for ML Libraries and Serving Images | NOT RUN |
| [TC-L14-010](pages/L14-mlops-llmops-layer.md#tc-l14-010) | Container Image and Runtime Configuration Scanning for Model Serving | NOT RUN |
| [TC-L14-011](pages/L14-mlops-llmops-layer.md#tc-l14-011) | Infrastructure-as-Code Scanning for AI Infrastructure | NOT RUN |
| [TC-L14-012](pages/L14-mlops-llmops-layer.md#tc-l14-012) | Promotion Workflow Across Environments | NOT RUN |
| [TC-L14-013](pages/L14-mlops-llmops-layer.md#tc-l14-013) | Rollback and Emergency Model Disable | NOT RUN |
| [TC-L14-014](pages/L14-mlops-llmops-layer.md#tc-l14-014) | Feature Store and Data Pipeline Integrity | NOT RUN |
| [TC-L14-015](pages/L14-mlops-llmops-layer.md#tc-l14-015) | Experiment Tracking Data Leakage | NOT RUN |
| [TC-L14-016](pages/L14-mlops-llmops-layer.md#tc-l14-016) | Post-Deployment Monitoring Coverage and Drift Signals | NOT RUN |
| [TC-L14-017](pages/L14-mlops-llmops-layer.md#tc-l14-017) | Evaluation Harness and Test Set Integrity | NOT RUN |
| [TC-L14-018](pages/L14-mlops-llmops-layer.md#tc-l14-018) | Shadow Deployments and Unregistered Model Endpoints | NOT RUN |
| [TC-L14-019](pages/L14-mlops-llmops-layer.md#tc-l14-019) | Pipeline Audit Trail and Change Attribution | NOT RUN |
| [TC-L14-020](pages/L14-mlops-llmops-layer.md#tc-l14-020) | Policy-as-Code Admission Control for AI Workloads | NOT RUN |
| [TC-L14-021](pages/L14-mlops-llmops-layer.md#tc-l14-021) | AI-Assisted Commit and Pull Request Identification | NOT RUN |
| [TC-L14-022](pages/L14-mlops-llmops-layer.md#tc-l14-022) | AI Code Review and Fix Bot Permissions in the Pipeline | NOT RUN |
| [TC-L15-001](pages/L15-infrastructure-layer.md#tc-l15-001) | AI Infrastructure Asset Discovery | NOT RUN |
| [TC-L15-002](pages/L15-infrastructure-layer.md#tc-l15-002) | GPU Cluster Configuration Hardening | NOT RUN |
| [TC-L15-003](pages/L15-infrastructure-layer.md#tc-l15-003) | GPU Multi-Tenancy Isolation and Memory Residue | NOT RUN |
| [TC-L15-004](pages/L15-infrastructure-layer.md#tc-l15-004) | Kubernetes Hardening for AI Workloads | NOT RUN |
| [TC-L15-005](pages/L15-infrastructure-layer.md#tc-l15-005) | Inference Server Hardening and Exposure | NOT RUN |
| [TC-L15-006](pages/L15-infrastructure-layer.md#tc-l15-006) | Network Segmentation Between AI Zones | NOT RUN |
| [TC-L15-007](pages/L15-infrastructure-layer.md#tc-l15-007) | Egress Control for AI Workloads | NOT RUN |
| [TC-L15-008](pages/L15-infrastructure-layer.md#tc-l15-008) | Lateral Movement Containment from a Compromised Inference Pod | NOT RUN |
| [TC-L15-009](pages/L15-infrastructure-layer.md#tc-l15-009) | Secrets Management for AI Infrastructure | NOT RUN |
| [TC-L15-010](pages/L15-infrastructure-layer.md#tc-l15-010) | Cloud IAM Roles for AI Services and Metadata Service Protection | NOT RUN |
| [TC-L15-011](pages/L15-infrastructure-layer.md#tc-l15-011) | Model and Dataset Storage Security | NOT RUN |
| [TC-L15-012](pages/L15-infrastructure-layer.md#tc-l15-012) | Encryption and Confidential Computing Evidence | NOT RUN |
| [TC-L15-013](pages/L15-infrastructure-layer.md#tc-l15-013) | Control Plane and Data Plane Location Proof (Sovereignty) | NOT RUN |
| [TC-L15-014](pages/L15-infrastructure-layer.md#tc-l15-014) | Air-Gapped and On-Premise Operation | NOT RUN |
| [TC-L15-015](pages/L15-infrastructure-layer.md#tc-l15-015) | Single-Tenant and Dedicated Deployment Evidence | NOT RUN |
| [TC-L15-016](pages/L15-infrastructure-layer.md#tc-l15-016) | Hardening of the Evaluated Platform's Own Components | NOT RUN |
| [TC-L15-017](pages/L15-infrastructure-layer.md#tc-l15-017) | Resource Quotas and Noisy-Neighbour Protection on Shared GPU Capacity | NOT RUN |
| [TC-L15-018](pages/L15-infrastructure-layer.md#tc-l15-018) | Infrastructure Logging and Telemetry Coverage | NOT RUN |
| [TC-L15-019](pages/L15-infrastructure-layer.md#tc-l15-019) | Backup, Disaster Recovery and Restoration of AI Services | NOT RUN |
| [TC-L15-020](pages/L15-infrastructure-layer.md#tc-l15-020) | Hosting Location and Data Centre Assurance | NOT RUN |
| [TC-L16-001](pages/L16-supply-chain-and-third-party.md#tc-l16-001) | AI Bill of Materials Generation | NOT RUN |
| [TC-L16-002](pages/L16-supply-chain-and-third-party.md#tc-l16-002) | AI Bill of Materials Format, Export and Vulnerability Linkage | NOT RUN |
| [TC-L16-003](pages/L16-supply-chain-and-third-party.md#tc-l16-003) | Model Provenance Verification for Hub-Sourced Models | NOT RUN |
| [TC-L16-004](pages/L16-supply-chain-and-third-party.md#tc-l16-004) | Malicious or Typosquatted Model and Package Detection | NOT RUN |
| [TC-L16-005](pages/L16-supply-chain-and-third-party.md#tc-l16-005) | Third-Party Model Repository Scanning at Download | NOT RUN |
| [TC-L16-006](pages/L16-supply-chain-and-third-party.md#tc-l16-006) | Known Vulnerabilities in AI Frameworks and Serving Components | NOT RUN |
| [TC-L16-007](pages/L16-supply-chain-and-third-party.md#tc-l16-007) | Dependency Confusion and Build-Time Substitution in AI SDKs | NOT RUN |
| [TC-L16-008](pages/L16-supply-chain-and-third-party.md#tc-l16-008) | Third-Party SaaS AI Feature and Vendor Risk Assessment | NOT RUN |
| [TC-L16-009](pages/L16-supply-chain-and-third-party.md#tc-l16-009) | Third-Party Assurance Evidence (SOC 2, ISO 27001, ISO/IEC 42001) | NOT RUN |
| [TC-L16-010](pages/L16-supply-chain-and-third-party.md#tc-l16-010) | Sub-Processor and Model-Provider Chain Visibility | NOT RUN |
| [TC-L16-011](pages/L16-supply-chain-and-third-party.md#tc-l16-011) | Contractual Data Use, Training Opt-Out and Breach Notification Terms | NOT RUN |
| [TC-L16-012](pages/L16-supply-chain-and-third-party.md#tc-l16-012) | Provider Outage, API Change and Exit Resilience | NOT RUN |
| [TC-L16-013](pages/L16-supply-chain-and-third-party.md#tc-l16-013) | Provider Model Deprecation and Behaviour Change Monitoring | NOT RUN |
| [TC-L16-014](pages/L16-supply-chain-and-third-party.md#tc-l16-014) | Open-Source Licence Compliance for Models, Datasets and Code | NOT RUN |
| [TC-L16-015](pages/L16-supply-chain-and-third-party.md#tc-l16-015) | Agent Framework and SDK Supply Chain Integrity | NOT RUN |
| [TC-L16-016](pages/L16-supply-chain-and-third-party.md#tc-l16-016) | Third-Party Prompt and Template Pack Vetting | NOT RUN |
| [TC-L16-017](pages/L16-supply-chain-and-third-party.md#tc-l16-017) | Container Base Image and GPU Driver Supply Chain | NOT RUN |
| [TC-L16-018](pages/L16-supply-chain-and-third-party.md#tc-l16-018) | Evaluated Vendor's Own Software Supply Chain and Security Programme | NOT RUN |
| [TC-L16-019](pages/L16-supply-chain-and-third-party.md#tc-l16-019) | Vendor Handling of Customer Telemetry and Support Access | NOT RUN |
| [TC-L16-020](pages/L16-supply-chain-and-third-party.md#tc-l16-020) | Vendor Continuity, Escrow and Data Return | NOT RUN |
| [TC-L16-021](pages/L16-supply-chain-and-third-party.md#tc-l16-021) | Vendor Incident Response and Breach Notification | NOT RUN |
| [TC-L16-022](pages/L16-supply-chain-and-third-party.md#tc-l16-022) | Vendor Patch Cadence and Vulnerability Handling | NOT RUN |
| [TC-L16-023](pages/L16-supply-chain-and-third-party.md#tc-l16-023) | Fourth-Party and Concentration Risk Across AI Controls | NOT RUN |
| [TC-L16-024](pages/L16-supply-chain-and-third-party.md#tc-l16-024) | Supply Chain Incident Response Exercise | NOT RUN |
| [TC-L16-025](pages/L16-supply-chain-and-third-party.md#tc-l16-025) | Right to Audit and Independent Security Testing of the Vendor Platform | NOT RUN |
| [TC-L16-026](pages/L16-supply-chain-and-third-party.md#tc-l16-026) | IDE Extension and AI Plugin Marketplace Vetting | NOT RUN |
| [TC-L17-001](pages/L17-monitoring-detection-and-response.md#tc-l17-001) | Telemetry Coverage Map Across the 17 Layers | NOT RUN |
| [TC-L17-002](pages/L17-monitoring-detection-and-response.md#tc-l17-002) | Event Schema and Field Completeness | NOT RUN |
| [TC-L17-003](pages/L17-monitoring-detection-and-response.md#tc-l17-003) | Log Delivery to SIEM: Formats, Reliability and Backfill | NOT RUN |
| [TC-L17-004](pages/L17-monitoring-detection-and-response.md#tc-l17-004) | Log Integrity and Tamper Evidence | NOT RUN |
| [TC-L17-005](pages/L17-monitoring-detection-and-response.md#tc-l17-005) | Log Retention, Immutability and Storage Location | NOT RUN |
| [TC-L17-006](pages/L17-monitoring-detection-and-response.md#tc-l17-006) | Prebuilt AI Detection Content and SIEM Rules | NOT RUN |
| [TC-L17-007](pages/L17-monitoring-detection-and-response.md#tc-l17-007) | Alert Quality: Severity, Deduplication and Noise | NOT RUN |
| [TC-L17-008](pages/L17-monitoring-detection-and-response.md#tc-l17-008) | Alert Enrichment with User, Device, Asset and Risk Context | NOT RUN |
| [TC-L17-009](pages/L17-monitoring-detection-and-response.md#tc-l17-009) | Correlation of AI Events with Endpoint, Identity and Network Events | NOT RUN |
| [TC-L17-010](pages/L17-monitoring-detection-and-response.md#tc-l17-010) | Detection of Data Exfiltration Through AI Services | NOT RUN |
| [TC-L17-011](pages/L17-monitoring-detection-and-response.md#tc-l17-011) | Detection of Account Takeover on AI Tools | NOT RUN |
| [TC-L17-012](pages/L17-monitoring-detection-and-response.md#tc-l17-012) | Detection of Agent Compromise Indicators | NOT RUN |
| [TC-L17-013](pages/L17-monitoring-detection-and-response.md#tc-l17-013) | Detection of Insider Misuse and Policy Evasion | NOT RUN |
| [TC-L17-014](pages/L17-monitoring-detection-and-response.md#tc-l17-014) | Mapping of Detections to MITRE ATLAS and ATT&CK | NOT RUN |
| [TC-L17-015](pages/L17-monitoring-detection-and-response.md#tc-l17-015) | SOAR Playbooks for Automated Containment | NOT RUN |
| [TC-L17-016](pages/L17-monitoring-detection-and-response.md#tc-l17-016) | SOAR and Ticketing Integration: Bidirectional Flow | NOT RUN |
| [TC-L17-017](pages/L17-monitoring-detection-and-response.md#tc-l17-017) | Case Management and Evidence Attachment | NOT RUN |
| [TC-L17-018](pages/L17-monitoring-detection-and-response.md#tc-l17-018) | AI Incident Response Runbook and Tabletop Exercise | NOT RUN |
| [TC-L17-019](pages/L17-monitoring-detection-and-response.md#tc-l17-019) | Containment Time Measurement | NOT RUN |
| [TC-L17-020](pages/L17-monitoring-detection-and-response.md#tc-l17-020) | Forensics: Conversation and Tool Call Reconstruction | NOT RUN |
| [TC-L17-021](pages/L17-monitoring-detection-and-response.md#tc-l17-021) | Forensics: Evidence Preservation, Legal Hold and Integrity | NOT RUN |
| [TC-L17-022](pages/L17-monitoring-detection-and-response.md#tc-l17-022) | Forensics: Cross-User, Agent and Tool Timeline | NOT RUN |
| [TC-L17-023](pages/L17-monitoring-detection-and-response.md#tc-l17-023) | Post-Incident Feedback into Policy and Detection | NOT RUN |
| [TC-L17-024](pages/L17-monitoring-detection-and-response.md#tc-l17-024) | AI Threat Intelligence Ingestion | NOT RUN |
| [TC-L17-025](pages/L17-monitoring-detection-and-response.md#tc-l17-025) | Dashboards and Executive Metrics (Detection and Response Times) | NOT RUN |
| [TC-L17-026](pages/L17-monitoring-detection-and-response.md#tc-l17-026) | Regulatory Incident Reporting Evidence (UAE and GCC) | NOT RUN |
| [TC-L17-027](pages/L17-monitoring-detection-and-response.md#tc-l17-027) | 24x7 Monitoring, MDR Support and Escalation Model | NOT RUN |
| [TC-L17-028](pages/L17-monitoring-detection-and-response.md#tc-l17-028) | Platform Health and Silent Failure Detection | NOT RUN |
| [TC-L17-029](pages/L17-monitoring-detection-and-response.md#tc-l17-029) | Purple-Team Detection Validation: Replay of Earlier Attacks | NOT RUN |
| [TC-L17-030](pages/L17-monitoring-detection-and-response.md#tc-l17-030) | SOC Analyst Access to Raw Prompts: Masking, Role Separation and Unmask Audit | NOT RUN |
| [TC-L17-031](pages/L17-monitoring-detection-and-response.md#tc-l17-031) | Developer AI Activity Telemetry and Investigation Timeline | NOT RUN |
