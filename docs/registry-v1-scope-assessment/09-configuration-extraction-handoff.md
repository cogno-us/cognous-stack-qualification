# 09 Configuration-extraction handoff (planning manifest)

**A planning manifest, not implementation authorization.** It proposes, field by field, what could be externalized to the registry, what must stay code, and what is unresolved, so the Architect and operator can freeze a V1 scope (plan v1.3 phase P1). It does not approve a migration, select or activate a record, change an evaluator, or authorize P2 to P6 work. P1 extraction requires a separate Architect disposition and operator scope approval. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.

Machine-readable form: [data/configuration-extraction-manifest.jsonl](data/configuration-extraction-manifest.jsonl) (same rows as [csv](data/configuration-extraction-manifest.csv)). Built by [method/build_extraction_manifest.py](method/build_extraction_manifest.py), which validates required keys, closed vocabularies, unique field IDs and that every `scenario_id` is a canonical or suite-local ID. The per-owner notes (what was verified directly versus taken from the lane D inventory, and every discrepancy found) are in [appendix/lane-P1-runtime-manifest-notes.md](appendix/lane-P1-runtime-manifest-notes.md) and [appendix/lane-P1-controlplane-manifest-notes.md](appendix/lane-P1-controlplane-manifest-notes.md); the per-owner source rows are [appendix/lane-P1-runtime-manifest.jsonl](appendix/lane-P1-runtime-manifest.jsonl) and [appendix/lane-P1-controlplane-manifest.jsonl](appendix/lane-P1-controlplane-manifest.jsonl).

## Reading rules

- **One row per configurable field, not per scenario or test.** `scenario_id` lists the canonical and suite-local IDs that exercise the field (`;`-joined; `NONE` where no mapped scenario varies it). No count of rows is a count of safe migratable fields; the 32 historical S02 unresolved classifications stay unresolved unless a row's source finding decides them.
- **Columns.** The fifteen the Architect specified (`scenario_id` to `recommended_disposition`), plus `field_id`, `disposition_basis` (which of the four extractability clauses pass or fail, and the open decision), `verification` (`SOURCE_VERIFIED` = the code was read at `source_pin`; `UNVERIFIED` = taken from the lane D inventory or not confirmed), `source_pin`, and three derived columns (`decisions_named`, `governance_benefit_level`, `complexity_level`). `enforcement_component` names the owner that enforces the field today; per ADR-REG-TR01 that enforcing component also owns activation and high-water state for any registry value that reaches it, and the registry never activates.
- **Extractability test** (reused from the P0 readiness document, not invented): a value is extractable only if (a) it is already caller, constructor or profile data, (b) a code-owned hard bound or floor remains, (c) the registry value can only narrow what the caller permits, and (d) refusal is deterministic and never widens. Relaxing toggles, guards, check order, reason texts, `__post_init__` validation, vocabularies and lifecycle stay code.
- **`central_governance_benefit` and `extraction_complexity`** are REASONED INFERENCE from the mapped scenario's recorded outcome and the source; no customer demand, revenue or adoption data was used or invented. Benefit is a property of the field (question B in [01 section 1a](01-executive-assessment.md)); it is not a finding that existing code fails to enforce.
- **`exclusion_impact`** states the governance capability lost if the field is not externalized (central change control not gained), never an enforcement that would be lost.
- **Dispositions** are the five the Architect named. `DIRECT_EXTRACTION` means the four clauses are met on source reading of the inspected code (a judgement, not a test result) and no open decision (D1, D5, D6, D9, D12, W8-014) is named; it does not mean approved, qualified or scheduled. `CONDITIONAL_EXTRACTION` names the decision or prerequisite it waits on. `UNRESOLVED` means the source cannot decide it. `CODE_OWNED_GUARDRAIL` rows are listed so that nothing adjacent to a configurable field is silently left out.

## Constraints from P0 that every row respects

Code-owned constitutional guardrails stay in code. The registry holds typed parameter data only. Registered evaluators stay in code and no universal policy interpreter is introduced. The Control Plane remains the authorization authority; the registry may govern parameters but may not issue grants or replace enforcement. Record, selection and consumer activation stay distinct (selection authenticated, activation consumer-owned). Effect-time enforcement is mandatory and the existing `LocalExecutionPolicy.check` pre-claim placement is not a transaction-time guarantee (GAP-G3-02). The V0.2 contract architecture and the P0 ledger are neither reopened nor duplicated; the P0 deliverable is [cognous-ocs-registry PR #21](https://github.com/cogno-us/cognous-ocs-registry/pull/21) (open; read at head `ac54f235`, whose `05-configuration-extraction-readiness.md` and `07-p1-handoff.md` supply the extractability test, prerequisites G1 to G9 and the source-inspection obligation). ADR-REG-TR01 is relied on only for the ownership assignment, not as an implemented or qualified mechanism.

## Result

| Disposition | Runtime | Control Plane | Total |
|---|---|---|---|
| DIRECT_EXTRACTION | 5 | 0 | 5 |
| CONDITIONAL_EXTRACTION | 3 | 15 | 18 |
| CODE_OWNED_GUARDRAIL | 11 | 36 | 47 |
| UNRESOLVED | 5 | 10 | 15 |
| NOT_RELEVANT_TO_V1 | 0 | 11 | 11 |
| **All rows** | 24 | 72 | 96 |

By family (a row naming several families counts under each):

| Family | DIRECT_EXTRACTION | CONDITIONAL_EXTRACTION | CODE_OWNED_GUARDRAIL | UNRESOLVED | NOT_RELEVANT_TO_V1 | Rows |
|---|---|---|---|---|---|---|
| F10 | 0 | 0 | 0 | 0 | 2 | 2 |
| F11 | 0 | 4 | 3 | 0 | 1 | 8 |
| F1a | 3 | 0 | 1 | 0 | 0 | 4 |
| F1b | 2 | 0 | 2 | 0 | 0 | 4 |
| F1c | 0 | 1 | 4 | 1 | 0 | 6 |
| F1d | 0 | 0 | 3 | 2 | 0 | 5 |
| F3 | 0 | 2 | 7 | 1 | 1 | 11 |
| F4 | 0 | 7 | 3 | 5 | 0 | 15 |
| F5 | 0 | 2 | 10 | 0 | 0 | 12 |
| F6 | 0 | 1 | 1 | 1 | 0 | 3 |
| F7 | 0 | 1 | 4 | 4 | 2 | 11 |
| F8 | 0 | 0 | 6 | 1 | 4 | 11 |
| F9 | 0 | 0 | 6 | 0 | 1 | 7 |

## All rows

Long-form fields (current value source, existing guardrail, configuration value, cross-field and cross-component dependencies, required qualification, exclusion impact, basis) are in the JSONL/CSV; the table is the index. The `CP-` prefix means the Control Plane half of the inventory; CP-F4-15 and CP-F7-07 cite Runtime source (the enforcing code for those two is in the Runtime) and carry the Runtime pin. CP-F5-02 (`on_unreadable`) was reclassified to `CODE_OWNED_GUARDRAIL` after review because it is a relaxing toggle.

| Field | Component | Family | Configurable field | Disposition | Governance benefit | Complexity | Decisions named | Verification |
|---|---|---|---|---|---|---|---|---|
| CP-F11-01 | Control Plane | F11 | RedactionConfig.redact_payloads | CONDITIONAL_EXTRACTION | LOW | MEDIUM | D1,W9-002 | SOURCE_VERIFIED |
| CP-F11-02 | Control Plane | F11 | RedactionConfig.redact_targets | CONDITIONAL_EXTRACTION | LOW | MEDIUM | D1,W9-002 | SOURCE_VERIFIED |
| CP-F11-03 | Control Plane | F11 | RedactionConfig.redact_final_output | CONDITIONAL_EXTRACTION | LOW | MEDIUM | D1,W9-002 | SOURCE_VERIFIED |
| CP-F11-04 | Control Plane | F11 | RedactionConfig.redact_reasons | CONDITIONAL_EXTRACTION | LOW | MEDIUM | D1,W9-002 | SOURCE_VERIFIED |
| CP-F3-07 | Control Plane | F3 | FreshnessProfile.lease_acquire_timeout_seconds (seconds to wait for the per-check lease) | CONDITIONAL_EXTRACTION | LOW | MEDIUM | D1,D4,W8-041 | SOURCE_VERIFIED |
| CP-F4-01 | Control Plane | F4 | ObservationPolicy.max_age_seconds (int seconds) | CONDITIONAL_EXTRACTION | MEDIUM | HIGH | D4,W6-042 | SOURCE_VERIFIED |
| CP-F4-04 | Control Plane | F4 | status_max_age_seconds (int seconds) | CONDITIONAL_EXTRACTION | MEDIUM | HIGH | D4,W6-042 | SOURCE_VERIFIED |
| CP-F4-05 | Control Plane | F4 | identity_max_age_seconds (int seconds) | CONDITIONAL_EXTRACTION | LOW | HIGH | D4,W6-042 | SOURCE_VERIFIED |
| CP-F4-06 | Control Plane | F4 | mandate_max_age_seconds (int seconds) | CONDITIONAL_EXTRACTION | LOW | HIGH | D4,W6-042 | SOURCE_VERIFIED |
| CP-F4-07 | Control Plane | F4 | approval_max_age_seconds (int seconds) | CONDITIONAL_EXTRACTION | MEDIUM | HIGH | D4,W6-042 | SOURCE_VERIFIED |
| CP-F4-09 | Control Plane | F4 | FreshnessProfile.anchor_deadline_to_inputs (bool) | CONDITIONAL_EXTRACTION | LOW | HIGH | D4,W8-014 | SOURCE_VERIFIED |
| CP-F4-11 | Control Plane | F4 | FreshnessProfile.max_age_extension_seconds (int seconds) | CONDITIONAL_EXTRACTION | LOW | MEDIUM | D4,W8-014 | SOURCE_VERIFIED |
| CP-F5-01 | Control Plane | F5 | ActionClass.max_status_age_seconds (int seconds) | CONDITIONAL_EXTRACTION | MEDIUM | HIGH | D4,W6-042,W8-014 | SOURCE_VERIFIED |
| CP-F5-03 | Control Plane | F5 | ActionClass.requires_revocation_assurance (bool) | CONDITIONAL_EXTRACTION | LOW | MEDIUM | D4,W8-014 | SOURCE_VERIFIED |
| CP-F7-08 | Control Plane | F7 | MergeProfile.funded_authorities (list of principal names) | CONDITIONAL_EXTRACTION | LOW | MEDIUM | D12,D4 | SOURCE_VERIFIED |
| CP-F4-02 | Control Plane | F4 | ObservationPolicy.clock_tolerance_seconds (int seconds) | UNRESOLVED | LOW | HIGH | D4,W6-042 | SOURCE_VERIFIED |
| CP-F4-03 | Control Plane | F4 | BoundedAuthorizationWorkflow clock_tolerance_seconds (int seconds) | UNRESOLVED | LOW | HIGH | D4,W6-042 | SOURCE_VERIFIED |
| CP-F4-08 | Control Plane | F4 | requirement.evidence[].max_age_seconds (int seconds, authority-context data) | UNRESOLVED | LOW | HIGH | D1,W6-004,W6-005 | SOURCE_VERIFIED |
| CP-F4-12 | Control Plane | F4 | FreshnessProfile.reaper_interval_seconds (int seconds) | UNRESOLVED | LOW | MEDIUM | D1,D4,W8-041 | SOURCE_VERIFIED |
| CP-F4-13 | Control Plane | F4 | FreshnessProfile.lease_acquire_timeout_seconds (float seconds) | UNRESOLVED | NONE | MEDIUM | D1,D4 | SOURCE_VERIFIED |
| CP-F7-01 | Control Plane | F7 | DedupeProfile.dedupe_ttl_seconds (int seconds) | UNRESOLVED | LOW | HIGH | D12,D4,W3-063,W9-027 | SOURCE_VERIFIED |
| CP-F7-02 | Control Plane | F7 | DedupeProfile.provider_horizon_seconds (int seconds) | UNRESOLVED | LOW | HIGH | D12,D4,W3-063,W9-027 | SOURCE_VERIFIED |
| CP-F7-03 | Control Plane | F7 | DedupeProfile.escalation_deadline_seconds (int seconds) | UNRESOLVED | LOW | HIGH | D12,D4 | SOURCE_VERIFIED |
| CP-F7-07 | Control Plane | F7 | DedupeTtlOperationDestination dedupe_ttl_seconds | UNRESOLVED | LOW | HIGH | D12,D4,W3-062,W3-063 | SOURCE_VERIFIED |
| CP-F8-04 | Control Plane | F8 | PolicyConfig.allowed_tools / blocked_tools (JSON file) | UNRESOLVED | MEDIUM | MEDIUM | D1,W4-014 | SOURCE_VERIFIED |
| CP-F11-05 | Control Plane | F11 | RedactionConfig.replacement (default "[REDACTED]") | CODE_OWNED_GUARDRAIL | NONE | LOW | - | SOURCE_VERIFIED |
| CP-F11-06 | Control Plane | F11 | RedactionConfig.keep_fingerprints (default False) | CODE_OWNED_GUARDRAIL | NONE | LOW | - | SOURCE_VERIFIED |
| CP-F11-07 | Control Plane | F11 | none - the set of redacted fields is fixed in code | CODE_OWNED_GUARDRAIL | NONE | HIGH | - | SOURCE_VERIFIED |
| CP-F3-01 | Control Plane | F3 | MAX_INPUT_BYTES = 1024 * 1024 (input file size ceiling for acp run) | CODE_OWNED_GUARDRAIL | NONE | MEDIUM | - | SOURCE_VERIFIED |
| CP-F3-03 | Control Plane | F3 | MAX_TEXT = 200 and per-call truncation limits 40/60/80 (diagnostic text length) | CODE_OWNED_GUARDRAIL | NONE | LOW | - | SOURCE_VERIFIED |
| CP-F3-04 | Control Plane | F3 | list caps 10000 and string caps 256 on trusted host-configuration models | CODE_OWNED_GUARDRAIL | NONE | HIGH | - | SOURCE_VERIFIED |
| CP-F3-05 | Control Plane | F3 | none - implicit depth limit (interpreter recursion limit; grep found no setrecursionlimit) | CODE_OWNED_GUARDRAIL | NONE | NONE | - | SOURCE_VERIFIED |
| CP-F3-06 | Control Plane | F3 | 4096 monotonic-clock map cap; 1.0 s reaper wake cap; 5 s thread join; 0.01 s lease poll; M | CODE_OWNED_GUARDRAIL | NONE | LOW | - | SOURCE_VERIFIED |
| CP-F4-10 | Control Plane | F4 | FreshnessProfile.nonce (bool) | CODE_OWNED_GUARDRAIL | NONE | LOW | - | SOURCE_VERIFIED |
| CP-F4-14 | Control Plane | F4 | RuleRevisionProfile.signers / host_digests / host_rule_kinds | CODE_OWNED_GUARDRAIL | NONE | HIGH | - | SOURCE_VERIFIED |
| CP-F4-15 | Control Plane | F4 | Recovery synthetic-observation window (86400 s literal, lower bound 0) | CODE_OWNED_GUARDRAIL | NONE | MEDIUM | - | SOURCE_VERIFIED |
| CP-F5-02 | Control Plane | F5 | ActionClass.on_unreadable (refuse / bounded_tolerance) | CODE_OWNED_GUARDRAIL | MEDIUM | MEDIUM | - | SOURCE_VERIFIED |
| CP-F5-04 | Control Plane | F5 | ActionClass.irreversible plus reversibility, reversible_until, reversal_cost, reads_protec | CODE_OWNED_GUARDRAIL | NONE | HIGH | - | SOURCE_VERIFIED |
| CP-F5-05 | Control Plane | F5 | RuntimeAuthorityProfile.actions map (membership of action classes) and ActionClass.class_i | CODE_OWNED_GUARDRAIL | NONE | HIGH | - | SOURCE_VERIFIED |
| CP-F5-06 | Control Plane | F5 | RuntimeAuthorityProfile.allow_synthetic_resolver (bool) | CODE_OWNED_GUARDRAIL | NONE | LOW | - | SOURCE_VERIFIED |
| CP-F5-07 | Control Plane | F5 | RuntimeAuthorityProfile.producer_keys (Ed25519 hex public keys) | CODE_OWNED_GUARDRAIL | NONE | HIGH | - | SOURCE_VERIFIED |
| CP-F5-08 | Control Plane | F5 | RuntimeAuthorityProfile.catalogue_version (str) | CODE_OWNED_GUARDRAIL | NONE | LOW | - | SOURCE_VERIFIED |
| CP-F5-09 | Control Plane | F5 | Presence of the opt-in sub-profiles (operation_identity, freshness, holder_inventory, merg | CODE_OWNED_GUARDRAIL | MEDIUM | HIGH | - | SOURCE_VERIFIED |
| CP-F5-10 | Control Plane | F5 | RuntimeAuthorityProfile.holder_inventory (HolderInventory: inventory_id, recorded_by, reco | CODE_OWNED_GUARDRAIL | LOW | HIGH | - | SOURCE_VERIFIED |
| CP-F5-11 | Control Plane | F5 | EvidenceCriterion (minimum_count, members) in the runtime_authority extension (as named in | CODE_OWNED_GUARDRAIL | NONE | HIGH | - | SOURCE_VERIFIED |
| CP-F5-12 | Control Plane | F5 | Profile snapshot and approval commitment binding | CODE_OWNED_GUARDRAIL | NONE | HIGH | - | SOURCE_VERIFIED |
| CP-F7-04 | Control Plane | F7 | Ordering rule provider_horizon <= escalation_deadline < dedupe_ttl | CODE_OWNED_GUARDRAIL | NONE | LOW | - | SOURCE_VERIFIED |
| CP-F7-05 | Control Plane | F7 | Ledger gates dedupe_unresolved_attempt_blocks_new_key and dedupe_operation_effect_applied  | CODE_OWNED_GUARDRAIL | MEDIUM | HIGH | - | SOURCE_VERIFIED |
| CP-F7-06 | Control Plane | F7 | Destination-declared dedupe_capability and dedupe_ttl_seconds | CODE_OWNED_GUARDRAIL | NONE | MEDIUM | - | SOURCE_VERIFIED |
| CP-F7-10 | Control Plane | F7 | Operation id pattern and length (1..128) | CODE_OWNED_GUARDRAIL | NONE | LOW | - | SOURCE_VERIFIED |
| CP-F8-03 | Control Plane | F8 | Demo authority record scopes granted by the helpers | CODE_OWNED_GUARDRAIL | NONE | LOW | - | SOURCE_VERIFIED |
| CP-F8-06 | Control Plane | F8 | PolicyConfig.authority_required | CODE_OWNED_GUARDRAIL | NONE | LOW | - | SOURCE_VERIFIED |
| CP-F8-07 | Control Plane | F8 | PolicyGate rule chain, read-allow rule and default escalation | CODE_OWNED_GUARDRAIL | NONE | LOW | - | SOURCE_VERIFIED |
| CP-F8-08 | Control Plane | F8 | Manifest tools[] declarations (tool_name, adapter_id, allowed) | CODE_OWNED_GUARDRAIL | MEDIUM | HIGH | - | SOURCE_VERIFIED |
| CP-F8-09 | Control Plane | F8 | Manifest default_action (action level and manifest level) | CODE_OWNED_GUARDRAIL | LOW | HIGH | - | SOURCE_VERIFIED |
| CP-F8-10 | Control Plane | F8 | Manifest per-action allowed_targets, payload_policy, effect_limits, authority_required | CODE_OWNED_GUARDRAIL | LOW | HIGH | - | SOURCE_VERIFIED |
| CP-F9-01 | Control Plane | F9 | tenant_id max_length on TenantRuntimeProposal | CODE_OWNED_GUARDRAIL | NONE | HIGH | - | SOURCE_VERIFIED |
| CP-F9-02 | Control Plane | F9 | tenant_id max_length on TenantAuthorizationBinding | CODE_OWNED_GUARDRAIL | NONE | HIGH | - | SOURCE_VERIFIED |
| CP-F9-03 | Control Plane | F9 | tenant_id max_length on TenantApprovalProjection | CODE_OWNED_GUARDRAIL | NONE | HIGH | - | SOURCE_VERIFIED |
| CP-F9-04 | Control Plane | F9 | tenant_id max_length on TenantPolicyProjection | CODE_OWNED_GUARDRAIL | NONE | HIGH | - | SOURCE_VERIFIED |
| CP-F9-05 | Control Plane | F9 | tenant_id max_length on TenantLocalExecutionClaim | CODE_OWNED_GUARDRAIL | NONE | HIGH | - | SOURCE_VERIFIED |
| CP-F10-01 | Control Plane | F10 | minimum_prior_count (default 5) and minimum_current_exposure (default 1) | NOT_RELEVANT_TO_V1 | NONE | LOW | - | SOURCE_VERIFIED |
| CP-F10-02 | Control Plane | F10 | period_seconds (window length; required keyword, no default) and declared arity counts | NOT_RELEVANT_TO_V1 | NONE | LOW | - | SOURCE_VERIFIED |
| CP-F11-08 | Control Plane | F11 | manifest action sensitive_fields / redaction_hints (manifest-owned data, shape-validated o | NOT_RELEVANT_TO_V1 | NONE | NONE | - | SOURCE_VERIFIED |
| CP-F3-02 | Control Plane | F3 | none - no size bound exists on these paths | NOT_RELEVANT_TO_V1 | NONE | NONE | - | SOURCE_VERIFIED |
| CP-F7-09 | Control Plane | F7 | OperationIdentityProfile.resolver_id / resolver_version | NOT_RELEVANT_TO_V1 | NONE | LOW | - | SOURCE_VERIFIED |
| CP-F7-11 | Control Plane | F7 | F7 "replay-window defaults" (Control Plane side) | NOT_RELEVANT_TO_V1 | NONE | NONE | - | SOURCE_VERIFIED |
| CP-F8-01 | Control Plane | F8 | read_only_recorder default allowed_tools / blocked_tools | NOT_RELEVANT_TO_V1 | NONE | LOW | - | SOURCE_VERIFIED |
| CP-F8-02 | Control Plane | F8 | write_enabled_recorder default allowed_tools / blocked_tools | NOT_RELEVANT_TO_V1 | NONE | LOW | - | SOURCE_VERIFIED |
| CP-F8-05 | Control Plane | F8 | PolicyConfig.default_action | NOT_RELEVANT_TO_V1 | NONE | LOW | - | SOURCE_VERIFIED |
| CP-F8-11 | Control Plane | F8 | CLI-derived Frame tool lists | NOT_RELEVANT_TO_V1 | NONE | LOW | - | SOURCE_VERIFIED |
| CP-F9-06 | Control Plane | F9 | none - tenant_id on evidence has no length bound (the sixth tenant-bearing model; not one  | NOT_RELEVANT_TO_V1 | NONE | NONE | - | SOURCE_VERIFIED |
| RT-F1a-01 | Runtime | F1a | allowed_actions | DIRECT_EXTRACTION | HIGH | LOW | - | SOURCE_VERIFIED |
| RT-F1a-02 | Runtime | F1a | allowed_adapters | DIRECT_EXTRACTION | MEDIUM | LOW | - | SOURCE_VERIFIED |
| RT-F1a-03 | Runtime | F1a | allowed_units | DIRECT_EXTRACTION | MEDIUM | LOW | - | SOURCE_VERIFIED |
| RT-F1b-01 | Runtime | F1b | allowed_institutions | DIRECT_EXTRACTION | MEDIUM | LOW | - | SOURCE_VERIFIED |
| RT-F1b-02 | Runtime | F1b | allowed_authority_domains | DIRECT_EXTRACTION | MEDIUM | LOW | - | SOURCE_VERIFIED |
| RT-F1c-01 | Runtime | F1c | max_amount | CONDITIONAL_EXTRACTION | MEDIUM | HIGH | D4,D6 | SOURCE_VERIFIED |
| RT-F3-03 | Runtime | F3 | OpenShellConfig.timeout_seconds | CONDITIONAL_EXTRACTION | LOW | MEDIUM | D1,D4,W2-082 | SOURCE_VERIFIED |
| RT-F6-01 | Runtime | F6 | permissions mapping {agent_id: [action strings]} | CONDITIONAL_EXTRACTION | LOW | MEDIUM | D5 | SOURCE_VERIFIED |
| RT-F1c-02 | Runtime | F1c | max_effects (policy ceiling) | UNRESOLVED | LOW | HIGH | D1,D6,W8-091 | SOURCE_VERIFIED |
| RT-F1d-01 | Runtime | F1d | allowed_target_prefixes | UNRESOLVED | LOW | HIGH | D4,D9,W1-029 | SOURCE_VERIFIED |
| RT-F1d-02 | Runtime | F1d | target_match ('segment' default / 'exact' / 'legacy-prefix') | UNRESOLVED | NONE | HIGH | D1,D9,W1-029 | SOURCE_VERIFIED |
| RT-F3-04 | Runtime | F3 | OpenShellConfig cpu/memory/runtime (pinned to a named profile; not independently qualified | UNRESOLVED | NONE | HIGH. | D1,W2-082 | SOURCE_VERIFIED |
| RT-F6-02 | Runtime | F6 | agents_absent_from_record (registry-record silence for an agent present in the caller file | UNRESOLVED | NONE | HIGH | D5 | SOURCE_VERIFIED |
| RT-F1b-03 | Runtime | F1b | trusted_institution_id / trusted_authority_domain (adapter constructor args; NOT policy da | CODE_OWNED_GUARDRAIL | NONE | HIGH | - | SOURCE_VERIFIED |
| RT-F1c-03 | Runtime | F1c | exact-one-effect rule (op.effects must equal 1) - adjacent to max_effects | CODE_OWNED_GUARDRAIL | NONE | HIGH | - | SOURCE_VERIFIED |
| RT-F1c-04 | Runtime | F1c | finite-number / binary64 validators (2**53 bound, non-negative, exact builtin types, exact | CODE_OWNED_GUARDRAIL | NONE | HIGH | - | SOURCE_VERIFIED |
| RT-F1c-05 | Runtime | F1c | cumulative per-grant effect count and atomic budget row max_effects (destination-side coun | CODE_OWNED_GUARDRAIL | NONE | HIGH | - | SOURCE_VERIFIED |
| RT-F1d-03 | Runtime | F1d | target_match='legacy-prefix' (relaxing toggle) | CODE_OWNED_GUARDRAIL | NONE | HIGH | - | SOURCE_VERIFIED |
| RT-F1d-04 | Runtime | F1d | target well-formedness rules, match-mode vocabulary and separators | CODE_OWNED_GUARDRAIL | NONE | HIGH. | - | SOURCE_VERIFIED |
| RT-F1x-01 | Runtime | F1a;F1b;F1c;F1d | check order, reason texts, __post_init__ fail-closed validation of all LocalExecutionPolic | CODE_OWNED_GUARDRAIL | NONE | HIGH. | - | SOURCE_VERIFIED |
| RT-F3-01 | Runtime | F3 | structural admission budgets: depth 32 and nodes 10000 (155), per-container 10000 (171, 17 | CODE_OWNED_GUARDRAIL | NONE | MEDIUM | - | SOURCE_VERIFIED |
| RT-F3-02 | Runtime | F3 | byte budgets (1 MiB envelope/JSON/CLI output; 64 KiB CLI stdin and request) | CODE_OWNED_GUARDRAIL | NONE | MEDIUM. | - | SOURCE_VERIFIED |
| RT-F6-03 | Runtime | F6 | exact-membership, deny-all-on-missing-file, no-execution (legacy shell) guards - adjacent  | CODE_OWNED_GUARDRAIL | NONE | HIGH. | - | SOURCE_VERIFIED |
| RT-F9-01 | Runtime | F9 | tenant_id length bound (1..128) | CODE_OWNED_GUARDRAIL | NONE | MEDIUM | - | SOURCE_VERIFIED |

## What this manifest does not cover

- Only the two enforcement owners the plan names for the candidate families (Execution Runtime and Control Plane) were inspected, at `c5e97e87` and `7a4bcd40`. It is not a 15-component inventory. Exchange, Replay, Evidence Pack, ODES, Verifier, BitRep, Index and Action Manifest were not read; scenarios whose enforcement lives there carry no extraction row (they appear in the crosswalk and the gap register).
- Registry-side numeric encoding for ceilings and ages (integer-unit or decimal string; P0 prerequisite G3), the family-dispatch table (G1) and the Control Plane adapter (G4) are registry/integration work, not fields.
- Historical results and the 21 controller runs do not qualify the current heads; the `required_qualification` column lists existing test IDs for reference only, and nothing in it is a PASS. Known-limit assertions are not PASS, and collection is not execution.
