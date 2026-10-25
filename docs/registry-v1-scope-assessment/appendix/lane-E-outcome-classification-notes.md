# Lane E - Customer-outcome classification notes

Sources read (SOURCE FACT): `/home/claude/cognous-stack-qualification` HEAD 998d39c5 (main, 2026-10-24): `scenarios/catalog.json` (40 scenarios, read in full), `scenarios/ai-security-wiki/applicability.json` (656 cases), Wiki page text under `scenarios/ai-security-wiki/pages/` (all 65 in-scope pages read: Risk Addressed, Technical Scenario, Test Data). No tests, registry families, results or other lanes consulted. Output: `E-outcomes.jsonl`, 696 rows, 696 unique ids, validated (40 cognous_catalog + 656 ai_security_wiki, no gaps or duplicates). Every row is labeled REASONED INFERENCE (outcome category, severity and rationale are my judgment from scenario text). Working scripts: `E_work/build.py`.

## 1. Outcome taxonomy rules (REASONED INFERENCE)

Primary outcome = the customer-relevant governance harm that the scenario's own stimulus/required observation exists to prevent or expose. Secondary = a second harm that the same scenario would also expose if it failed. Decide by asking, in order: "what would the customer lose if the protection failed?"

| Category | Means | Decision rule |
|---|---|---|
| UNAUTHORIZED_TOOL_EXECUTION | An action/tool call runs that no current authority covers | Primary when the failure mode is "effect occurs with no/unknown/mismatched authorization" and no more specific cause (stale, revoked, tenant, budget) dominates |
| IDENTITY_TENANT_ISOLATION | Wrong actor/tenant/environment/identity is honored or data crosses a tenant boundary | Primary when the forbidden thing is a cross-identity or cross-tenant effect or exposure |
| AGENT_PERMISSION_BOUNDARIES | An agent/executor reaches beyond its own scope (resources, credentials, files, network, peers) | Primary when the boundary is the agent's or executor's own reach, not a per-action approval |
| APPROVAL_DELEGATED_AUTHORITY | Human approval, delegation or attenuation is bypassed, manufactured or widened | Primary when the control is "someone competent decided/delegated" |
| FINANCIAL_QUANTITATIVE_LIMITS | Aggregate or numeric caps (budget, rate, blast radius) exceeded | Primary when harm scales with count/amount; "financial" means quantitative effect limits, not a finance domain |
| FRESHNESS_EVIDENCE_VALIDITY | Stale, forged, copied, unknown or superseded evidence is treated as valid | Primary when the failure is promotion of bad evidence into authority or completion |
| REVOCATION_WITHDRAWAL | Authority that was withdrawn, expired or suspended is still honored | Primary when ordering of withdrawal vs commit is the point |
| DUPLICATE_IRREVERSIBLE_EFFECTS | An external effect is repeated, partially repeated or blindly retried | Primary when retry/ambiguity/partial state could duplicate a committed effect |
| INJECTION_TOOL_OUTPUT_MANIPULATION | Content (documents, tool output, peer messages, descriptions) steers or forges behavior | Primary when untrusted content is the attack carrier |
| AUDIT_PROVENANCE_REPLAY | Record, export, trace or replay is missing, altered or misleading | Primary when failure harms later explanation/evidence rather than causing an effect |
| RECOVERY_OUTAGE_ROLLBACK | Behavior under crash, overload, tool failure, restore or fail-open | Primary when the stress condition, not authority semantics, is the stimulus |
| POLICY_DISTRIBUTION_CHANGE_CONTROL | Policy/manifest/config changes are unreviewed, unsigned, undistributed or drifting | Primary when the governed object is the rule set itself |
| OTHER_OR_OUT_OF_SCOPE | Not a customer governance outcome OCS claims (measurement methodology, task quality, or a layer/capability OCS does not claim) | Used for all 591 NOT_APPLICABLE Wiki cases except nearest-analogue close calls, plus A01 and C22 |

Tie-break precedence when two fit: (1) an effect-causing harm outranks an evidence/record harm; (2) the more specific cause outranks UNAUTHORIZED_TOOL_EXECUTION; (3) stress conditions rank below the authority semantics they stress unless the scenario is purely about the stress; (4) record the loser as secondary.

### Five boundary examples
1. **C06 observer unavailable** (DIE vs FEV): primary DUPLICATE_IRREVERSIBLE_EFFECTS because "no blind retry" is the harmful action; unverified completion is secondary.
2. **A05 tool failure** (ROR vs FEV vs UTE): chose RECOVERY_OUTAGE_ROLLBACK since the stimulus is a tool fault; invented success is FEV secondary; unapproved fallback is a UTE risk not elevated.
3. **D01 valid action** (UTE vs APR): the stimulus is a legitimate effect; the protection is "only authorized effects", and failure is a false block, so UTE primary with low severity 2; linkage evidence secondary.
4. **TC-L09-014 key lifecycle** vs **TC-L13-023 job credentials** (APB vs REV): chosen APB for L09-014 in the first pass (lifecycle management as a whole), but the in-scope slice (grant expiry/revocation) is REV-like; I put REV as secondary. Honest instability: this pair is where a reasonable second reviewer may differ.
5. **C03 forged/replayed attestation** (FEV vs UTE vs INJ): chosen FEV because rejected evidence minting authority is the failure; UTE is the downstream consequence and is not listed as secondary since REV (revoked key) was also in the stimulus.

## 2. Severity of consequence (1-5) (REASONED INFERENCE)

Definition: harm if the protection fails, from the scenario text only; not likelihood, not test result, not customer value.
- 5: uncontrolled, likely irreversible external effect (duplicate or unapproved irreversible action). Only 3 rows: D04, C09, TC-L06-015.
- 4: unauthorized, duplicate or cross-boundary effect or exposure that is bounded or detectable.
- 3: evidence, audit or availability degradation that corrupts downstream decisions without itself causing an effect.
- 2: incorrect or false-blocked outcome, reporting limits, schema/format loss, measurement methodology.
- 1: cosmetic or nit (assigned only mechanically to low-risk NOT_APPLICABLE cases).
NOT_APPLICABLE cases are scored mechanically (subject base +/- Wiki Risk Severity, cap 4) and mean "harm if that generic control failed", not an OCS protection gap. Do not use NOT_APPLICABLE severities for V1 scoping.

## 3. Distribution - primary outcome by classification
| primary_outcome | COGNOUS | APPLICABLE | PARTLY_COVERED | NOT_APPLICABLE | total |
|---|---|---|---|---|---|
| AGENT_PERMISSION_BOUNDARIES | 3 | 3 | 8 | 6 | 20 |
| APPROVAL_DELEGATED_AUTHORITY | 5 | 1 | 3 | 1 | 10 |
| AUDIT_PROVENANCE_REPLAY | 5 | 11 | 4 | 1 | 21 |
| DUPLICATE_IRREVERSIBLE_EFFECTS | 4 | 0 | 0 | 0 | 4 |
| FINANCIAL_QUANTITATIVE_LIMITS | 1 | 0 | 2 | 1 | 4 |
| FRESHNESS_EVIDENCE_VALIDITY | 5 | 0 | 0 | 1 | 6 |
| IDENTITY_TENANT_ISOLATION | 2 | 0 | 4 | 1 | 7 |
| INJECTION_TOOL_OUTPUT_MANIPULATION | 1 | 2 | 6 | 0 | 9 |
| OTHER_OR_OUT_OF_SCOPE | 2 | 0 | 0 | 578 | 580 |
| POLICY_DISTRIBUTION_CHANGE_CONTROL | 1 | 0 | 8 | 1 | 10 |
| RECOVERY_OUTAGE_ROLLBACK | 4 | 1 | 3 | 0 | 8 |
| REVOCATION_WITHDRAWAL | 3 | 0 | 5 | 1 | 9 |
| UNAUTHORIZED_TOOL_EXECUTION | 4 | 2 | 2 | 0 | 8 |
| TOTAL | 40 | 20 | 45 | 591 | 696 |

Cognous catalog: 38 of 40 map to a registry-relevant customer outcome; A01 and C22 are OTHER_OR_OUT_OF_SCOPE. Among in-scope Wiki cases (65), OTHER does not occur: the applicability pass already screened for claimed capability.

Subject-matter category of the 591 NOT_APPLICABLE cases (mechanical title rule, kept as secondary_outcome; noisy): OTHER 296, AGENT_PERMISSION_BOUNDARIES 85, AUDIT_PROVENANCE_REPLAY 54, INJECTION 43, POLICY_DISTRIBUTION 36, FINANCIAL 23, APPROVAL 18, RECOVERY 13, IDENTITY_TENANT 11, REVOCATION 7, FRESHNESS 5. Primary stays OTHER for all but 13 close-call cases that were given their nearest category.

## 4. Distribution - consequence severity by classification
| severity | COGNOUS | APPLICABLE | PARTLY_COVERED | NOT_APPLICABLE |
|---|---|---|---|---|
| 1 | 0 | 0 | 0 | 103 |
| 2 | 6 | 3 | 6 | 244 |
| 3 | 11 | 9 | 20 | 177 |
| 4 | 21 | 7 | 19 | 67 |
| 5 | 2 | 1 | 0 | 0 |

Highest-severity (>=4) rows concentrate in: UNAUTHORIZED_TOOL_EXECUTION, IDENTITY_TENANT_ISOLATION, DUPLICATE_IRREVERSIBLE_EFFECTS, REVOCATION_WITHDRAWAL, and INJECTION.

## 5. Independent cross-check (40 Wiki cases, seed 7)
Method (SOURCE FACT for procedure): `random.Random(7).sample(ids_in_applicability_json_order, 40)`; sample list in `E_work/sample.json`. I re-labelled each from Risk Addressed + Technical Scenario + Control(s) Tested text only, ignoring titles, the first-pass output and OCS applicability, assigning the "subject-matter" category (what the case is about regardless of OCS claim). I did this before looking at the first-pass labels for the NOT_APPLICABLE rows. Compared against the first-pass subject category (for in-scope = primary_outcome; for NOT_APPLICABLE = mechanical title-rule category).

- Sample composition: 7 in-scope, 33 NOT_APPLICABLE.
- Subject-category agreement: 28/40 = 70% (in-scope 7/7 = 100%; NOT_APPLICABLE 21/33 = 64%).
- Claimed-vs-unclaimed agreement (OTHER vs any named category): 32/40 = 80%.
- Agreement of the delivered `primary_outcome` field vs second pass is 23/40, but this is not meaningful for NOT_APPLICABLE rows because primary is OTHER by rule; report subject agreement instead.
- Disagreements (all NOT_APPLICABLE; first-pass title-rule vs second-pass text):

| id | first pass (title rule) | second pass (text) |
|---|---|---|
| TC-D10-005 | PDC | UTE |
| TC-D10-015 | OTH | APB |
| TC-L12-020 | PDC | OTH |
| TC-D10-016 | OTH | APB |
| TC-L15-012 | APR | OTH |
| TC-D10-006 | OTH | FQL |
| TC-L04-007 | APR | OTH |
| TC-D10-003 | ITI | APB |
| TC-L01-004 | APR | OTH |
| TC-L06-010 | APB | UTE |
| TC-L01-015 | OTH | ADA |
| TC-L13-023 | REV | APB |

Reading: in-scope classification (the 65 + 40 rows that matter for V1) is stable under the second pass in this small sample; the mechanical title rule for NOT_APPLICABLE cases misfires (keywords like "monitor", "evidence", "access" and missing keywords for browser-agent cases). Those secondary labels are weak and I recommend ignoring them. I did not tune the rules after the cross-check. The second pass is by the same reviewer, so it is not fully independent. Sample of 7 in-scope cases is too small to estimate in-scope reliability beyond "no disagreement observed".

## 6. Limitations
- Single classifier; the cross-check is same-reviewer and small. Boundary cases (examples above, plus the many PARTLY_COVERED cases whose scope_note narrows the claim) are judgment calls.
- Classification uses the scenario's own text and the applicability scope_extent/scope_note; it does not assert OCS actually enforces or evidences anything. No test results, registry families or component source were read.
- For PARTLY_COVERED, the category reflects the Wiki case's full subject; the in-scope slice is recorded in the severity_rationale bracket and may be narrower (e.g. TC-L06-015 severity 5 describes the Wiki harm; OCS claims hold/rejection/expiry only).
- Domain: no source text establishes healthcare, financial-sector or customer-validated context. `domain_claim_in_source` is false in all 696 rows. "financial" occurs only as a tool-category label in Test Data of TC-D09-004 and TC-L06-015 and the Wiki test uses mock tools (`transfer_test_funds`) in TC-L06-014 - these are fixtures, not claims. FINANCIAL_QUANTITATIVE_LIMITS means quantitative effect caps.
- Severity is an ordinal of described harm, not a risk rating; it ignores likelihood and compensating controls.
- NOT_APPLICABLE rows were scored mechanically and are not suitable for scoping decisions.
- Cognous catalog items C10, C15, C16, C19 are conditional on optional capabilities per the catalog's applicability text; classified on stimulus regardless of support.
