# Lane D: rule-family source analysis

Pins: Control Plane `%s`, Runtime `%s`, qualification `998d39c5`. Earlier R07 read: Runtime `ec728da6`, CP `0a41faa9` (not locally available). Cite prefixes: RT, CP = component heads; REG = registry-main docs; Q = qualification repo; OCS = open-control-stack. Every claim carries a label: SOURCE FACT, REASONED INFERENCE, CUSTOMER HYPOTHESIS, UNVERIFIED. Nothing here is a ruling on D1, D5, D6, D12 or any S02 UNRESOLVED row.

## Complexity scale

Ordinal implementation-complexity score for migrating the family's configurable fields to registry-managed typed records. Rule-based so it can be audited; it measures engineering/decision burden, NOT security value or customer value. Label: REASONED INFERENCE (lane D's own scale; not an R07 construct).

- **1**: At most 3 fields; one component; composition definable (set/min) and bounded differential evidence already exists (S05 for F1a).
- **2**: At most 5 fields; one component; composition definable without any open decision; no differential evidence yet.
- **3**: Typed non-set payload, scattered literals, or a must-agree pair across two components; composition definable per scalar below a code floor; no open critical decision (only low-priority classification).
- **4**: Composition conditional on an unruled decision (D4/D5/D6/D12, or a critical D1 row) OR cross-component binding is required OR a Tier 1 UNRESOLVED S02 row sits on the family.
- **5**: Composition not definable under current evidence (new semantics or a security-weakening mode) OR two or more independent level-4 triggers across components.

## Summary table

| Family | Title | Evaluator location | Fields | Cross-component binding (G3) | Score | S02 UNRESOLVED rows | Open decisions |
|---|---|---|---|---|---|---|---|
| F1a | LocalExecutionPolicy allow-sets: units, adapters, actions | Runtime | 3 | No | 1 | none mapped | D2, D3, D7, D13, D11 (sequencing; F1b preferred next) |
| F1b | LocalExecutionPolicy allow-sets: institutions, authority domains | Runtime (operands from CP) | 2 | Partial: values must equal CP-issued institution/domain | 2 | none mapped | D11 (F1b recommended first extension; not authorized), D2, D3, D7, D13 |
| F1c | LocalExecutionPolicy ceilings: max_amount, max_effects | Runtime ceiling + CP operand and CP-side limits | 2 | Yes | 4 | W8-091 | D6, D4, D1 (W8-091), D2, D3, D7, D13 |
| F1d | LocalExecutionPolicy target scope: allowed_target_prefixes, target_match | Runtime | 2 | No (blocked by semantics, D9) | 5 | W1-029 | D9, D4, D1 (W1-029), D2, D3, D7, D13 |
| F3 | Size, depth, timeout budgets | Both (independent literals) | 11 | No (independent guards) | 3 | W2-082 (linked by R07 not S02) | D1 (W2-082), D4, D2, D3, D7, D13 |
| F4 | Observation, status and approval freshness bounds | CP primary + Runtime recovery window literal | 14 | Yes | 5 | W6-042, (adjacent, not mapped by R07: W6-004 EVIDENCE_KINDS and W6-005 UNKNOWN_BEHAVIORS govern obligations whose max_age_seconds is read at bounded.py:2545-2556) | D1 (W6-042; 60-versus-300 relationship), D4, D2, D3, D7, D13 |
| F5 | Per-action-class authority declarations | CP only | 10 | No cross-component; needs CP as consumer | 4 | W8-014 | D1 (W8-014), D4, D2, D3, D7, D13 |
| F6 | Agent permission allow-list | Runtime only (legacy path) | 2 | No | 4 | none mapped | D5, D4 (n/a numeric), D2, D3, D7, D13 |
| F7 | Dedupe and replay-window defaults | Both | 4 | Yes | 5 | W3-063, W9-027 | D12, D4, D1 (W3-063, W9-027), D2, D3, D7, D13 |
| F8 | Demo policy tool lists | CP only (demo) | 4 | No | 1 | W4-022, W4-023, (adjacent: W4-004 read rule, W4-014/015 PolicyConfig.default_action, W4-018, W9-007 PolicyGate() default) | D1 (W4-022, W4-023) |
| F9 | Tenant id length bound | Both (6 copies) | 1 | Yes (must agree) | 3 | none mapped | D4 (minor), D2, D3, D7, D13 |
| F10 | Diagnostic trend thresholds | CP only | 2 | No | 1 | none mapped | D2, D3, D7, D13 (low relevance) |
| F11 | Redaction defaults | CP only | 6 | No | 3 | none mapped | D1 (tier classification; W9-002 is a candidate row, not UNRESOLVED), D2, D3, D7, D13 |

## Per-family sections

### F1a: LocalExecutionPolicy allow-sets: units, adapters, actions

**Definition** (family source)

- [SOURCE FACT] R07 02 defines F1a as allowed_units, allowed_adapters, allowed_actions; S02 section 6 narrowed the first increment to exactly these three. (`REG:docs/registry-schema-analysis/02-rule-family-taxonomy.md:42`, `REG:docs/s02-inventory.md:76`)

**Configurable fields**

- [SOURCE FACT] `allowed_units`: frozenset[str] of non-empty str (empty frozenset is accepted by the constructor) (`RT:engine/safe_executor.py:365`)
- [SOURCE FACT] `allowed_adapters`: frozenset[str] (`RT:engine/safe_executor.py:362`)
- [SOURCE FACT] `allowed_actions`: frozenset[str] (`RT:engine/safe_executor.py:363`)

**Current evaluator** (component: Runtime)

- [SOURCE FACT] LocalExecutionPolicy.check: adapter membership at 417-418, action at 419-420, unit at 423-424 (class 359-372, __post_init__ 374-395, check 410-430). (`RT:engine/safe_executor.py:359`, `RT:engine/safe_executor.py:374`, `RT:engine/safe_executor.py:410`, `RT:engine/safe_executor.py:417`, `RT:engine/safe_executor.py:419`, `RT:engine/safe_executor.py:423`)
- [SOURCE FACT] Call sites of check: Route A observe (control_plane_adapter.py:101), LocalDestinationExecutor.execute_snapshot (safe_executor.py:890), Route B AtomicLocalControlPlaneExecutor.execute (atomic_local_control_plane_executor.py:69). (`RT:engine/control_plane_adapter.py:101`, `RT:engine/safe_executor.py:890`, `RT:engine/atomic_local_control_plane_executor.py:69`)
- [REASONED INFERENCE] Control Plane involvement: None. No Control Plane source references LocalExecutionPolicy or safe_executor (grep).

**Source revision**: read at Runtime c5e97e87dd239c821b1b4a406a55dcd03c5bc61f (safe_executor.py git blob 2fc880dae37eac76e5074533435740ce0684209d, equal to the blob R07/R08 state for the S01/S03 pin); R07 read at Runtime ec728da6dc301a664b331ac8986afd6e850a1273.

- [SOURCE FACT] File content matches R07 03/06 claims: fields 358-372, __post_init__ 374-395, check 410-430 all verified at the head; blob hash equals the value stated in r08-preparation/10 and r10-feasibility. (`RT:engine/safe_executor.py:358`, `REG:docs/r08-preparation/10-source-revision-reconciliation-and-review-closure.md:25`)
- [UNVERIFIED] Cannot diff against ec728da6: the local clone has no history for that object. Equality of safe_executor.py rests on the matching blob hash (SOURCE FACT) and on doc 10's statement that only local_authority_effect.py differs (REPORTED). 

**Existing configuration mechanism**

- [SOURCE FACT] Host code constructs a frozen LocalExecutionPolicy with Python literals and passes it to the executor; no file, environment or registry mechanism exists. Examples: Runtime README demo (README.md:82-86) and the OCS synthetic ingress host (OCS repo tools/mvp_ingress/synthetic_host.py:126-130, read at OCS head 51c579a; note the brief lists this repo as not cloned, but it is present locally). (`RT:README.md:82`, `OCS:tools/mvp_ingress/synthetic_host.py:126`, `RT:engine/control_plane_adapter.py:56`, `RT:engine/atomic_local_control_plane_executor.py:14`)
- [UNVERIFIED] How a production operator or customer constructs the policy is not established: no production caller exists in the sources read (destination is synthetic SQLite). 

**Mandatory code-owned invariants**

- [SOURCE FACT] Fixed check order institution, authority-domain, adapter, action, target, unit, amount, one-effect, effect-count and the exact reason texts. (`RT:engine/safe_executor.py:410`)
- [SOURCE FACT] __post_init__ fail-closed construction: sets must be exact frozenset of non-empty str; prefixes non-empty; mode in vocabulary. (`RT:engine/safe_executor.py:374`)
- [SOURCE FACT] Strict number validators (bool/subclass excluded, finite, non-negative, ints <= 2**53) and exact-one-effect rule on the operation. (`RT:engine/safe_executor.py:252`, `RT:engine/safe_executor.py:267`, `RT:engine/safe_executor.py:316`)
- [SOURCE FACT] Target well-formedness and match-mode vocabulary (M1/F2; out of scope for F1a). (`RT:engine/safe_executor.py:343`, `RT:engine/safe_executor.py:347`)

**Typed composition requirements (R07 D4)**

| Field | Units | Order | Floor/ceiling | Direction | Unsupported-case outcome | Status | Label |
|---|---|---|---|---|---|---|---|
| allowed_units / allowed_adapters / allowed_actions | set of opaque exact strings (no wildcards, 1-128 chars per S03) | none (unordered set) | No numeric floor. Empty effective set = deny-all for that dimension. | Intersection: effective = caller INTERSECT registry; a registry value never widens the caller. | Optional-overlay refusal leaves caller policy unchanged (S04, T7); mandatory profile must DENY/HOLD (D7, not authorized). | Established for the bounded trusted-host, inactive profile by S05 differential evidence (builder-authored oracle, T10); NOT a proof; does not transfer to a successor contract. | SOURCE FACT |
| deny-all representation | n/a | n/a | n/a | n/a | Frozen S03 refuses empty lists, so deny-all cannot be authored in a record (successor contract, R08 E-03/V4). The Runtime constructor itself accepts an empty frozenset (verified by constructing the dataclass locally); this contradicts a statement in r10-feasibility that __post_init__ refuses empty sets (true only for allowed_target_prefixes). | MISMATCH recorded (see limitations) | SOURCE FACT |

**Cross-family dependencies**

- [SOURCE FACT] F1a/F1b/F1c/F1d are one dataclass and one check(); a registry record for F1a only leaves the other six dimensions caller-owned. The five set fields and the numeric/target fields are evaluated in one fixed order, so partial registry coverage does not change order. (`RT:engine/safe_executor.py:410`)
- [REASONED INFERENCE] F1a values must be coherent with Control Plane manifest action ids and adapter ids (op fields come from the validated CP binding); no code binds the two sets, the host integrator does (C-01 unnamed). (`REG:docs/r08-preparation/08-decisions-and-dependencies.md:29`)

**Unresolved classification decisions** (listed, not resolved): decisions D2, D3, D7, D13, D11 (sequencing; F1b preferred next); S02 UNRESOLVED rows none mapped. R08 05 states F1a/F1b were not found to depend on an unresolved S02 row beyond the shared S06 deny-all/refusal questions; the dependence was not adjudicated (do not treat as cleared).
Other open items: V1-V6 (selection fields, effective-policy binding, lifecycle vocabulary, deny-all, participation granularity, MSOP); R10 F1 effect-time gap UNQUALIFIED (policy.check runs outside the atomic transaction)

**Existing tests** (ids verbatim; run state not assessed)

- `suites/v1-scenarios/test_scn_c11.py::test_scn_c11_route_a_stricter_local_policy_overrides_institutional_authorization[adapter|action|unit]` -- Replaces allowed_adapters/actions/units with disjoint values on the real Route A flow; asserts refusal, no destination mutation, no attempt. (`Q:suites/v1-scenarios/test_scn_c11.py:176`)
- `suites/v1-scenarios/test_scn_c11.py::test_scn_c11_route_b_stricter_local_policy_overrides_claimed_authority[adapter|action|unit]` -- Same on Route B (atomic claim). (`Q:suites/v1-scenarios/test_scn_c11.py:202`)
- `suites/v1-probes/test_runtime_probes.py::test_probe_policy_bypass_out_of_scope_operation_denied_with_no_effect[adapter_id|action_id|unit]` -- Direct evaluator probe with positive control. (`Q:suites/v1-probes/test_runtime_probes.py:115`)
- `suites/wiki-derived/test_wp_d_manifest_change_control.py (assert 'local action restriction' in res.error, line 740)` -- Asserts the exact action-restriction reason text. (`Q:suites/wiki-derived/test_wp_d_manifest_change_control.py:740`)
- `suites/cognous-execution-runtime/tests/test_openshell_environment.py::test_local_restriction_prevents_sandbox_dispatch` -- Local restriction prevents sandbox dispatch. (`Q:suites/cognous-execution-runtime/tests/test_openshell_environment.py:244`)

Run state of these tests (PASS/FAIL/NOT RUN) was not assessed in this lane; coverage-map.json marks scenario_verdict NOT RUN for C11 and mapping_status PARTIAL (UNVERIFIED beyond that). S05 differential evidence lives in the registry repo (not read here). Component-local tests that also exercise the check (Runtime tests/test_route_a_local_policy_reason.py, tests/test_exact_target_matching.py) are NOT relocated into the qualification repo.

**Authenticated selection / activation (R08/R09)**: Pin-only S04 overlay exists for F1a, inactive, called by nothing; authenticated selection/activation not designed or approved (R08/R09 not passed).

- [SOURCE FACT] Architect-recommended MSOP Option 1 is F1a with all fourteen lifecycle elements, but the operator has NOT adopted any MSOP. (`REG:docs/r08-preparation/05-minimum-operational-profile.md:80`)

**Complexity**: score 1 of 5 [REASONED INFERENCE]. Fields: 3. Cross-component binding: no. Composition: Yes (intersection), established only for the bounded inactive profile. Three fields, one component, set intersection, bounded differential evidence exists. Score excludes the shared R08-R10 infrastructure, which dominates real cost.

**Qualification requirements**

- [REASONED INFERENCE] Successor-contract differential battery against an independent oracle (S05 does not transfer; oracle was builder-authored). (`REG:docs/r08-preparation/09-implementation-readiness.md:35`)
- [REASONED INFERENCE] Mandatory-participation negatives: missing/expired/revoked/forged selection must HOLD/DENY, never fall back to the broader caller policy (D7). (`REG:docs/registry-schema-analysis/08-open-architectural-decisions.md:67`)
- [REASONED INFERENCE] Effect-time evidence for the R10 gap: the F1 check runs before the atomic transaction; guarantee is UNQUALIFIED until an integration design exists. (`REG:docs/r10-feasibility/r10-effect-boundary-feasibility.md:17`)
- [REASONED INFERENCE] Empty-intersection / deny-all case, order-of-check preservation and reason-text equality tests. (`RT:engine/safe_executor.py:410`)
- [REASONED INFERENCE] Independent qualifier + oracle author designated first (D13/F-01). (`REG:docs/registry-schema-analysis/08-open-architectural-decisions.md:72`)

### F1b: LocalExecutionPolicy allow-sets: institutions, authority domains

**Definition** (family source)

- [SOURCE FACT] R07 02 defines F1b as allowed_institutions and allowed_authority_domains; R07 04 fit code B (same type/check, new contract version because S03 `supplies` is fixed). (`REG:docs/registry-schema-analysis/02-rule-family-taxonomy.md:42`, `REG:docs/registry-schema-analysis/04-schema-fitness-matrix.md:21`)

**Configurable fields**

- [SOURCE FACT] `allowed_institutions`: frozenset[str] (`RT:engine/safe_executor.py:360`)
- [SOURCE FACT] `allowed_authority_domains`: frozenset[str] (`RT:engine/safe_executor.py:361`)

**Current evaluator** (component: Runtime)

- [SOURCE FACT] LocalExecutionPolicy.check: institution at 413-414, authority-domain at 415-416. The same check also pins institution/domain via the trusted-context check in the Route A adapter (control_plane_adapter.py ~85-92). (`RT:engine/safe_executor.py:413`, `RT:engine/safe_executor.py:415`, `RT:engine/control_plane_adapter.py:90`)
- [REASONED INFERENCE] Control Plane involvement: Indirect: op.institution_id and op.authority_domain are copied from the CP-validated binding; the allow-set itself is Runtime-only.

**Source revision**: read at Runtime c5e97e87dd239c821b1b4a406a55dcd03c5bc61f; R07 read at Runtime ec728da6dc301a664b331ac8986afd6e850a1273.

- [SOURCE FACT] Same evaluator file/blob as F1a; check lines match R07. (`RT:engine/safe_executor.py:410`)
- [UNVERIFIED] No history for ec728da6 locally. 

**Existing configuration mechanism**

- [SOURCE FACT] Same as F1a: host-constructed LocalExecutionPolicy literals; additionally the Route A adapter takes trusted_institution_id / trusted_authority_domain as separate constructor values and compares them to the operation (a second, independent institution/domain check). (`RT:engine/control_plane_adapter.py:56`, `RT:engine/control_plane_adapter.py:90`)

**Mandatory code-owned invariants**

- [SOURCE FACT] Check order and reason texts; trusted-context binding in the adapter; __post_init__ validation. (`RT:engine/safe_executor.py:410`, `RT:engine/safe_executor.py:374`)

**Typed composition requirements (R07 D4)**

| Field | Units | Order | Floor/ceiling | Direction | Unsupported-case outcome | Status | Label |
|---|---|---|---|---|---|---|---|
| allowed_institutions / allowed_authority_domains | opaque exact strings | none | none numeric | Intersection with caller value (proposed in R07; same operator as F1a). | As F1a. Needs a new contract version because S03 refuses unknown fields. | Definable; no differential evidence for these two fields (S05 covers F1a only). | SOURCE FACT |

**Cross-family dependencies**

- [REASONED INFERENCE] Scope binding: a selection's tenant/institution scope (v1.2 section 3.1) and the policy's allowed_institutions are different layers; R08 05 notes F1b adds the scope-binding dimension but no new registry function. (`REG:docs/r08-preparation/05-minimum-operational-profile.md:73`)
- [SOURCE FACT] op.institution_id/op.authority_domain are produced by CP; Runtime adapter compares them to separately supplied trusted values. Registry set must contain the deployed values or all operations are refused. (`RT:engine/control_plane_adapter.py:90`)

**Unresolved classification decisions** (listed, not resolved): decisions D11 (F1b recommended first extension; not authorized), D2, D3, D7, D13; S02 UNRESOLVED rows none mapped. No UNRESOLVED S02 row maps to F1b (R07 02 lists W-rows only for F1c/F1d).
Other open items: E-10 whether F1b joins as an additive second increment; V1-V6

**Existing tests** (ids verbatim; run state not assessed)

- `suites/v1-scenarios/test_scn_c11.py::test_scn_c11_route_a_stricter_local_policy_overrides_institutional_authorization[institution|authority_domain]` -- Disjoint institution/domain sets refuse an authorized decision. (`Q:suites/v1-scenarios/test_scn_c11.py:176`)
- `suites/v1-scenarios/test_scn_c11.py::test_scn_c11_route_b_stricter_local_policy_overrides_claimed_authority[institution|authority_domain]` -- Route B same. (`Q:suites/v1-scenarios/test_scn_c11.py:202`)
- `suites/v1-probes/test_runtime_probes.py::test_probe_policy_bypass_out_of_scope_operation_denied_with_no_effect[institution_id|authority_domain]` -- Direct evaluator probe. (`Q:suites/v1-probes/test_runtime_probes.py:115`)
- `suites/cognous-open-control-stack/tests/test_paired_request_enforcement.py::test_actor_principal_institution_domain_substitution` -- Identity substitution; supporting only per coverage-map gap text. (`Q:suites/cognous-open-control-stack/tests/test_paired_request_enforcement.py`)

Run state not assessed. C11 mapping_status PARTIAL, scenario_verdict NOT RUN in coverage-map.json.

**Authenticated selection / activation (R08/R09)**: Same as F1a; additionally a contract version change is required; D11 ruling names F1b the preferred first extension but authorizes nothing.


**Complexity**: score 2 of 5 [REASONED INFERENCE]. Fields: 2. Cross-component binding: no. Composition: Yes (intersection); no evidence yet. Two fields, same evaluator and type as F1a; needs successor contract and a new battery.

**Qualification requirements**

- [REASONED INFERENCE] New differential battery (S05 machinery reusable only if the qualifier re-approves expectations). (`REG:docs/r08-preparation/09-implementation-readiness.md:35`)
- [REASONED INFERENCE] Test that a registry set that omits the deployed institution refuses everything (fail-closed, not fail-open) and that the adapter trusted-context check still applies independently. (`RT:engine/control_plane_adapter.py:90`)

### F1c: LocalExecutionPolicy ceilings: max_amount, max_effects

**Definition** (family source)

- [SOURCE FACT] R07 02 defines F1c as max_amount and max_effects; R07 04 fit code C (numeric payload; W1-015 binary64 handling; W8-091 origin). (`REG:docs/registry-schema-analysis/02-rule-family-taxonomy.md:42`, `REG:docs/registry-schema-analysis/04-schema-fitness-matrix.md:22`)

**Configurable fields**

- [SOURCE FACT] `max_amount`: int or float, exact builtin types only, finite, non-negative, ints <= 2**53 (bool excluded); one unit-less number compared against float(op.amount) regardless of op.unit (`RT:engine/safe_executor.py:366`)
- [SOURCE FACT] `max_effects`: exact int >= 1; compared against op.effective_max_effects (the grant-derived cap), NOT against op.effects (which must equal exactly 1) (`RT:engine/safe_executor.py:367`)

**Current evaluator** (component: Runtime (policy ceiling) with operand origin in Control Plane)

- [SOURCE FACT] LocalExecutionPolicy.check: amount ceiling 425-426 (`float(op.amount) > max_amount`); one-effect rule 427-428; effect-count ceiling 429-430. (`RT:engine/safe_executor.py:425`, `RT:engine/safe_executor.py:427`, `RT:engine/safe_executor.py:429`)
- [SOURCE FACT] Operand effective_max_effects is minimum of requirement permission max_effects, grant permission max_effects, and action effect_limits.max_effects (default proposal effects) in BoundedAuthorizationWorkflow._resolve_inputs. (`CP:src/agent_control_plane/bounded.py:2570`)
- [SOURCE FACT] CP carries it into the claim (local_authority_effect.py:449; R07 03 cites :443, which is the pre-head coordinate - see limitations) and the dispatch (bounded.py:1797). (`CP:src/agent_control_plane/local_authority_effect.py:449`, `CP:src/agent_control_plane/bounded.py:1797`)
- [SOURCE FACT] Two further, independent effect-count enforcements exist: cumulative per-grant count in DurableRefundDestination (`local cumulative max_effects exhausted`) and the atomic budget row in the Route B destination. (`RT:engine/safe_executor.py:811`, `RT:engine/local_authority_effect.py:848`)
- [SOURCE FACT] CP has its own amount ceilings from manifest/action limits and grant permission: _manifest_mismatches (missing_amount_limit, amount > limit) and the permission max_amount compare. (`CP:src/agent_control_plane/bounded.py:2682`, `CP:src/agent_control_plane/bounded.py:2735`)
- [REASONED INFERENCE] Control Plane involvement: Operand origin and separate CP-side amount/effect ceilings; the Runtime ceiling is a local second layer (C11 'institutional authorization cannot override stricter local permissions').

**Source revision**: read at Runtime c5e97e87dd239c821b1b4a406a55dcd03c5bc61f; Control Plane 7a4bcd40b3b49e61ff3c294dcca53b52f460b22c; R07 read at Runtime ec728da6dc301a664b331ac8986afd6e850a1273; CP 0a41faa972699f7ec3063967a14cd9bdd3e67d27.

- [SOURCE FACT] bounded.py:2570-2574 min() matches R07 03 (W8-091). local_authority_effect.py coordinate is 449 at head vs :443 in R07/S02: CP local_authority_effect.py is one of the two CP files that differ between pin and head (+8/-2 per doc 10), so the shift is consistent with that diff; not independently verified. (`CP:src/agent_control_plane/bounded.py:2570`, `CP:src/agent_control_plane/local_authority_effect.py:449`)
- [UNVERIFIED] No history for pins locally. 

**Existing configuration mechanism**

- [SOURCE FACT] Host-constructed LocalExecutionPolicy literals (OCS synthetic host passes max_amount=1000, max_effects=1). The CP-side limits come from the signed/validated manifest action `effect_limits`/limits and grant permissions, not from a host profile. (`OCS:tools/mvp_ingress/synthetic_host.py:130`, `CP:src/agent_control_plane/bounded.py:2682`)

**Mandatory code-owned invariants**

- [SOURCE FACT] Exact-one-effect rule (op.effects must equal 1; check re-asserts) so a ceiling above 1 never admits a multi-effect operation. (`RT:engine/safe_executor.py:316`, `RT:engine/safe_executor.py:427`)
- [SOURCE FACT] Strict binary64 handling (W1-015: ints beyond 2**53 refused so no silent rounding before compare). (`RT:engine/safe_executor.py:262`, `RT:engine/safe_executor.py:267`)
- [SOURCE FACT] Strict `>` comparison: amount equal to ceiling is allowed; non-negative floor of 0. (`RT:engine/safe_executor.py:425`)
- [SOURCE FACT] Cumulative per-grant and atomic-budget enforcement stay in the destination and are independent of the policy ceiling. (`RT:engine/safe_executor.py:811`, `RT:engine/local_authority_effect.py:848`)

**Typed composition requirements (R07 D4)**

| Field | Units | Order | Floor/ceiling | Direction | Unsupported-case outcome | Status | Label |
|---|---|---|---|---|---|---|---|
| max_amount | unit-less number (the policy does not tie the ceiling to op.unit; multi-unit allow-sets share one ceiling) - composition across currencies undefined | total order on reals within [0, 2**53] for ints; floats finite | Floor 0 by code; a code hard cap would need to be defined (R07 04 says 'needs a code hard cap and a floor') | Minimum (registry may only lower) - R07 PROPOSAL, pending D4/D6 | NaN/inf/bool/str/negative/over-2**53 int refused whole (record_invalid class); optional-overlay refusal leaves caller ceiling | Not ruled: D6 (invariant / caller data / registry-eligible / layered) and W1-015 representation concern open | SOURCE FACT |
| max_effects | count (exact int >=1) of grant-derived cap | integers | Floor 1 by code (_strict_positive_int); effects==1 rule makes ceiling >1 only relevant to the grant-derived operand | Minimum - R07 PROPOSAL, pending D6 | Non-int/bool/<1 refused whole | Not ruled; origin of operand is a 3-way CP minimum (W8-091 UNRESOLVED classification) | SOURCE FACT |

**Cross-family dependencies**

- [SOURCE FACT] F1c depends on the effect-cap origin (W8-091): operand computed in CP bounded.py, ceiling in Runtime. Registry value can only affect the Runtime side. (`REG:docs/registry-schema-analysis/02-rule-family-taxonomy.md:55`, `CP:src/agent_control_plane/bounded.py:2570`)
- [REASONED INFERENCE] Three distinct 'max effects' notions interact: policy.max_effects vs effective_max_effects (safe_executor.py:429), cumulative count (safe_executor.py:811), atomic budget (local_authority_effect.py:848). A registry ceiling lowering only the first does not change the other two. (`RT:engine/safe_executor.py:429`, `RT:engine/safe_executor.py:811`, `RT:engine/local_authority_effect.py:848`)
- [REASONED INFERENCE] Interacts with F5 evidence/limits only through the grant (permission max_amount/max_effects live in authority data, not in F1c). (`CP:src/agent_control_plane/bounded.py:2735`)

**Unresolved classification decisions** (listed, not resolved): decisions D6, D4, D1 (W8-091), D2, D3, D7, D13; S02 UNRESOLVED rows W8-091. W1-015 (2**53) is classified MANDATORY-INVARIANT (not UNRESOLVED) but is a stated representation prerequisite for F1c in R07 04.
Other open items: R10 effect-time gap (F1 ceilings are checked outside the atomic transaction); V1-V6

**Existing tests** (ids verbatim; run state not assessed)

- `suites/v1-scenarios/test_scn_c11.py::test_scn_c11_route_a_stricter_local_policy_overrides_institutional_authorization[max_amount]` -- max_amount=1 against an authorized larger amount: refused. max_effects is NOT in POLICY_DIMS. (`Q:suites/v1-scenarios/test_scn_c11.py:92`)
- `suites/v1-probes/test_runtime_probes.py::test_probe_policy_bypass_out_of_scope_operation_denied_with_no_effect[amount-1000.01]` -- Amount just over ceiling refused. (`Q:suites/v1-probes/test_runtime_probes.py:115`)
- `suites/v1-probes/test_runtime_probes.py::test_probe_policy_bypass_cumulative_effect_budget_enforced_across_effect_ids` -- Cumulative per-grant count (a different mechanism from policy.max_effects). (`Q:suites/v1-probes/test_runtime_probes.py:151`)
- `suites/v1-scenarios/test_add_c2c_bi.py (dataclasses.replace(policy, max_effects=budget), lines 107,160,245) and test_scn_c16.py:332` -- Budget exhaustion with policy.max_effects set; asserts 'local cumulative max_effects exhausted'. (`Q:suites/v1-scenarios/test_add_c2c_bi.py:107`)
- `suites/mvp-chain/kwflow_fixtures/negative/n52_client_effective_max_effects.py` -- Client-supplied effective_max_effects negative fixture. (`Q:suites/mvp-chain/kwflow_fixtures/negative/n52_client_effective_max_effects.py`)

No qualification test isolates the policy.max_effects effect-count ceiling (`local effect-count restriction`) as a refusal; the Runtime repo's own test names for it (S02 W1-043) are not in suites/ and the S02-named test (test_effective_max_effects_equal_to_policy_max_is_allowed) was not found in the Runtime head tests/ directory (UNVERIFIED which repo holds it).

**Authenticated selection / activation (R08/R09)**: Blocked first by classification (D6) and typed numeric payload; then same R08-R10 chain.


**Complexity**: score 4 of 5 [REASONED INFERENCE]. Fields: 2. Cross-component binding: yes. Composition: Conditionally (minimum under a code cap/floor) once D6 is ruled. Level-4 triggers: Tier 1 UNRESOLVED row (W8-091), unruled D6, operand originates in CP; unit-less amount ceiling.

**Qualification requirements**

- [REASONED INFERENCE] Numeric-boundary battery: equality, 0, 2**53, 2**53+1, NaN/inf, bool, negative, float-vs-int; both Route A and B. (`RT:engine/safe_executor.py:267`)
- [REASONED INFERENCE] Test the isolated `local effect-count restriction` and `local amount restriction` refusals (currently only amount is isolated by C11). (`RT:engine/safe_executor.py:425`)
- [REASONED INFERENCE] Multi-unit semantics (one ceiling shared across allowed units) must be specified and tested before any registry value is accepted. (`RT:engine/safe_executor.py:423`)
- [REASONED INFERENCE] Independent oracle for min(caller, registry) with code cap; no registry value may raise the ceiling. (`REG:docs/registry-schema-analysis/04-schema-fitness-matrix.md:22`)

### F1d: LocalExecutionPolicy target scope: allowed_target_prefixes, target_match

**Definition** (family source)

- [SOURCE FACT] R07 02 defines F1d as allowed_target_prefixes and target_match; R07 04 fit code D (prefix semantics, not set membership); R07 08 D9 ruling: stays deferred until containment and matching-mode semantics are shown non-widening. (`REG:docs/registry-schema-analysis/02-rule-family-taxonomy.md:42`, `REG:docs/registry-schema-analysis/04-schema-fitness-matrix.md:23`, `REG:docs/registry-schema-analysis/08-open-architectural-decisions.md:69`)

**Configurable fields**

- [SOURCE FACT] `allowed_target_prefixes`: non-empty tuple of non-empty str (entries may end in a separator) (`RT:engine/safe_executor.py:364`)
- [SOURCE FACT] `target_match`: one of 'segment' (default), 'exact', 'legacy-prefix' (`RT:engine/safe_executor.py:372`)

**Current evaluator** (component: Runtime)

- [SOURCE FACT] LocalExecutionPolicy._target_allowed (396-408) consuming _TARGET_MATCH_MODES (343), _TARGET_SEPARATORS (344, '/' and ':') and _target_is_well_formed (347-355); check calls it at 421-422. (`RT:engine/safe_executor.py:396`, `RT:engine/safe_executor.py:343`, `RT:engine/safe_executor.py:347`, `RT:engine/safe_executor.py:421`)
- [REASONED INFERENCE] Control Plane involvement: None (op.target comes from the CP-validated proposal).

**Source revision**: read at Runtime c5e97e87dd239c821b1b4a406a55dcd03c5bc61f; R07 read at Runtime ec728da6dc301a664b331ac8986afd6e850a1273.

- [SOURCE FACT] R07 03 W1-029 claims (target_match default segment :372; __post_init__ rejection :393-394; _target_allowed :396-408; legacy-prefix goes straight to startswith) verified. (`RT:engine/safe_executor.py:372`, `RT:engine/safe_executor.py:393`, `RT:engine/safe_executor.py:405`)
- [UNVERIFIED] No pin history locally. 

**Existing configuration mechanism**

- [SOURCE FACT] Host-constructed LocalExecutionPolicy literals; the mode set itself has no override path (module constant). (`RT:engine/safe_executor.py:343`, `OCS:tools/mvp_ingress/synthetic_host.py:129`)

**Mandatory code-owned invariants**

- [SOURCE FACT] Match-mode vocabulary and separators (M1/F2; W1-029 UNRESOLVED; W1-030). (`RT:engine/safe_executor.py:343`)
- [SOURCE FACT] Target well-formedness refusals in every mode: NUL/control/format/surrogate/line-separator characters and dot-segments. (`RT:engine/safe_executor.py:347`)
- [SOURCE FACT] Non-empty prefix tuple and non-empty entries (an empty prefix would match everything via startswith). (`RT:engine/safe_executor.py:389`)

**Typed composition requirements (R07 D4)**

| Field | Units | Order | Floor/ceiling | Direction | Unsupported-case outcome | Status | Label |
|---|---|---|---|---|---|---|---|
| allowed_target_prefixes | strings interpreted by a mode-dependent prefix relation | NO defined order: containment between prefixes depends on mode and separators | none defined | NOT DEFINED. List intersection of prefix strings is not the intersection of the target sets they admit. | composition_unsupported (R07 06 class) - refuse whole | Deferred by D9 ruling | SOURCE FACT |
| target_match | enum of 3 | For a FIXED entry list the admitted sets nest: exact subset of segment subset of legacy-prefix (derived from the code at 400-407); no stated tightening order in R07 | legacy-prefix is security-weakening (explicit opt-in per CHANGELOG) | Candidate 'toward exact' is REASONED INFERENCE only; not ruled | composition_unsupported / relaxation_unsupported | Not ruled | REASONED INFERENCE |

**Cross-family dependencies**

- [SOURCE FACT] Mode vocabulary is M1/F2 (code-owned); F1d cannot be migrated without deciding whether the vocabulary stays in code (W1-029). (`REG:docs/registry-schema-analysis/02-rule-family-taxonomy.md:105`)
- [REASONED INFERENCE] Target well-formedness is applied before prefix matching in every mode, so a registry prefix cannot admit malformed targets. (`RT:engine/safe_executor.py:397`)

**Unresolved classification decisions** (listed, not resolved): decisions D9, D4, D1 (W1-029), D2, D3, D7, D13; S02 UNRESOLVED rows W1-029. W1-030 (separators) is CONFIGURABLE-CANDIDATE, Tier 1, kept in code per R07.

**Existing tests** (ids verbatim; run state not assessed)

- `suites/v1-scenarios/test_scn_c11.py::test_scn_c11_route_a_stricter_local_policy_overrides_institutional_authorization[target_prefix]` -- Replaces allowed_target_prefixes wholesale with a disjoint prefix; refusal. Tests the evaluator, not any composition. (`Q:suites/v1-scenarios/test_scn_c11.py:85`)
- `suites/v1-probes/test_runtime_probes.py::test_probe_policy_bypass_out_of_scope_operation_denied_with_no_effect[target-prod-account]` -- Out-of-prefix target refused. (`Q:suites/v1-probes/test_runtime_probes.py:115`)

No qualification test varies target_match or tests segment/exact/legacy-prefix; the Runtime repo's tests/test_exact_target_matching.py does (not relocated to the qualification repo). Search of suites/ for target_match found no hit.

**Authenticated selection / activation (R08/R09)**: Blocked before any selection question: composition semantics undefined and deferred by ruling (D9).


**Complexity**: score 5 of 5 [REASONED INFERENCE]. Fields: 2. Cross-component binding: no. Composition: No. Composition not definable; includes a security-weakening mode; new containment semantics required.

**Qualification requirements**

- [REASONED INFERENCE] Before any use: a written containment relation per mode proved non-widening by an independent oracle with property tests over targets (including separator and well-formedness edge cases). (`RT:engine/safe_executor.py:396`)
- [REASONED INFERENCE] Mode-ordering test showing a registry value can never move the effective mode toward legacy-prefix. (`RT:engine/safe_executor.py:405`)

### F3: Size, depth, timeout budgets

**Definition** (family source)

- [SOURCE FACT] R07 02 section 3 F3: admission and I/O guards; mostly literals; W1-007/008 are Tier 1 admission guards, others Tier 2 minimum; composition: minimum below a code hard cap with a floor; admission guards not eligible. (`REG:docs/registry-schema-analysis/02-rule-family-taxonomy.md:58`, `REG:docs/registry-schema-analysis/04-schema-fitness-matrix.md:25`)

**Configurable fields**

- [SOURCE FACT] `_admit_plain_data structural budget: depth 32, nodes 10000`: int literals (`RT:engine/safe_executor.py:155`)
- [SOURCE FACT] `_admit_plain_data max_bytes=1048576 (keyword never passed by snapshot_envelope or validate_snapshot), per-container 10000, int bit_length 256`: int literals (`RT:engine/safe_executor.py:147`)
- [SOURCE FACT] `OpenShell JSON byte budget 1048576; CLI output max_bytes 1048576; CLI stdin 64 KiB; synthetic request 64 KiB`: int literals (`RT:engine/openshell_environment.py:36`)
- [SOURCE FACT] `OpenShellConfig.timeout_seconds default 15, range 1-30; runtime/cpu/memory pinned to docker/1/256Mi (W2-082 UNRESOLVED)`: int / str (`RT:engine/openshell_environment.py:74`)
- [SOURCE FACT] `strict_json MAX_TEXT=200 (safe_text limit); CP cli_run MAX_INPUT_BYTES = 1 MiB`: int literals (`CP:src/agent_control_plane/strict_json.py:21`)

**Current evaluator** (component: Runtime and Control Plane (both))

- [SOURCE FACT] Runtime _admit_plain_data (147-184), called from snapshot_envelope (200) and validate_snapshot (289). (`RT:engine/safe_executor.py:147`, `RT:engine/safe_executor.py:200`, `RT:engine/safe_executor.py:289`)
- [SOURCE FACT] Runtime OpenShell: _bounded_json (35), _bounded_cli_output (115-118), OpenShellConfig.__post_init__ (75-95), invoke (210). (`RT:engine/openshell_environment.py:35`, `RT:engine/openshell_environment.py:115`, `RT:engine/openshell_environment.py:90`, `RT:engine/openshell_environment.py:210`)
- [SOURCE FACT] CP strict_json.safe_text (24) and cli_run input size check (169-170). (`CP:src/agent_control_plane/strict_json.py:24`, `CP:src/agent_control_plane/cli_run.py:169`)
- [REASONED INFERENCE] Control Plane involvement: Independent CP copies of different guards; no shared constant.

**Source revision**: read at Runtime c5e97e87dd239c821b1b4a406a55dcd03c5bc61f; Control Plane 7a4bcd40b3b49e61ff3c294dcca53b52f460b22c; R07 read at Runtime ec728da6dc301a664b331ac8986afd6e850a1273; CP 0a41faa972699f7ec3063967a14cd9bdd3e67d27.

- [SOURCE FACT] R07 line cites 147-184, strict_json.py:21,24-33, cli_run.py:61 (MAX_INPUT_BYTES) verified; openshell lines 74-77/89-90 verified (89-90 is the qualified-profile check at 89-90; timeout range at 93-94). (`RT:engine/safe_executor.py:147`, `CP:src/agent_control_plane/cli_run.py:61`, `RT:engine/openshell_environment.py:89`)
- [UNVERIFIED] No pin history locally. 

**Existing configuration mechanism**

- [SOURCE FACT] Literals; one keyword default (`max_bytes`) that no caller overrides; OpenShellConfig fields set by the host when building the config, with values outside the qualified profile rejected. (`RT:engine/safe_executor.py:147`, `RT:engine/openshell_environment.py:89`)

**Mandatory code-owned invariants**

- [SOURCE FACT] Admission guards W1-007/008 (hostile-input DoS bound) must keep a fixed upper bound; floors so a value cannot disable a limit; exact-type rules (plain builtin values only). (`RT:engine/safe_executor.py:153`, `REG:docs/registry-schema-analysis/04-schema-fitness-matrix.md:25`)

**Typed composition requirements (R07 D4)**

| Field | Units | Order | Floor/ceiling | Direction | Unsupported-case outcome | Status | Label |
|---|---|---|---|---|---|---|---|
| each scalar budget (bytes, depth, nodes, seconds) | bytes / count / seconds - per field | integers | Floor required so a registry value cannot disable the limit; code hard cap above | Minimum below a hard cap (R07 PROPOSAL, pending D4); admission guards not eligible | refuse whole; no coercion | Not ruled (D4) | SOURCE FACT |

**Cross-family dependencies**

- [REASONED INFERENCE] OpenShell qualified-profile values (W2-082) are qualified externally; changing them is a qualification decision, linked to F3 by R07 not by S02. (`REG:docs/registry-schema-analysis/02-rule-family-taxonomy.md:60`)
- [REASONED INFERENCE] F9 (tenant length) and F3 both are shape/size admission bounds with independent copies in each component. (`RT:engine/safe_executor.py:319`)

**Unresolved classification decisions** (listed, not resolved): decisions D1 (W2-082), D4, D2, D3, D7, D13; S02 UNRESOLVED rows W2-082 (linked by R07 not S02). W1-007/W1-008 are CONFIGURABLE-CANDIDATE but Tier 1 admission guards.

**Existing tests** (ids verbatim; run state not assessed)

- `suites/v1-scenarios/test_scn_d06.py::test_scn_d06_malformed_runtime_admission_flood (cases string_over_1MiB, nesting_over_32, object/array_over_10000, integer_over_256_bits defined in _d06_d07_d08_helpers.py:882-889)` -- Exercises the _admit_plain_data budgets with the exact refusal texts. (`Q:suites/v1-scenarios/_d06_d07_d08_helpers.py:882`)
- `suites/cognous-execution-runtime/tests/test_openshell_environment.py::test_environment_substitution_holds[timeout_seconds-16], ::test_unsupported_profile_rejected` -- OpenShell timeout/profile substitution rejected. (`Q:suites/cognous-execution-runtime/tests/test_openshell_environment.py:123`)

No qualification test targets strict_json MAX_TEXT or the CP 1 MiB input check by name (grep). Run state not assessed.

**Authenticated selection / activation (R08/R09)**: Same chain; plus per-guard tier split would be needed (Tier 1 guards excluded).


**Complexity**: score 3 of 5 [REASONED INFERENCE]. Fields: 11. Cross-component binding: no. Composition: Per scalar below a code floor/cap once D4 rules direction. Many scattered literals across two components, mixed tier, floor design needed; no critical decision except W2-082 sub-part.

**Qualification requirements**

- [REASONED INFERENCE] Per-guard boundary tests (limit, limit+1, registry-lowered limit, attempt to raise above hard cap or to 0). (`RT:engine/safe_executor.py:155`)
- [REASONED INFERENCE] Tier split verified: Tier 1 admission guards unreachable by registry data. (`REG:docs/registry-schema-analysis/04-schema-fitness-matrix.md:25`)

### F4: Observation, status and approval freshness bounds

**Definition** (family source)

- [SOURCE FACT] R07 02 F4: admission freshness gates in bounded.py plus Runtime recovery_resolution window; `ActionClass.max_status_age_seconds` is owned by F5, not F4. (`REG:docs/registry-schema-analysis/02-rule-family-taxonomy.md:62`, `REG:docs/registry-schema-analysis/06-family-schema-proposals.md:114`)

**Configurable fields**

- [SOURCE FACT] `ObservationPolicy.max_age_seconds (required, >0, no default) and clock_tolerance_seconds (default 5, >=0)`: int seconds (`CP:src/agent_control_plane/bounded.py:413`)
- [SOURCE FACT] `BoundedAuthorizationWorkflow constructor: status_max_age_seconds, identity_max_age_seconds, mandate_max_age_seconds, approval_max_age_seconds (each default 60), clock_tolerance_seconds (5)`: int seconds (`CP:src/agent_control_plane/bounded.py:1271`)
- [SOURCE FACT] `cli_run literal ObservationPolicy(max_age_seconds=300, clock_tolerance_seconds=5)`: literal (`CP:src/agent_control_plane/cli_run.py:510`)
- [SOURCE FACT] `FreshnessProfile: lease_acquire_timeout_seconds 5.0, reaper_interval_seconds 30, nonce True, max_age_extension_seconds 0, anchor_deadline_to_inputs False`: float/int/bool (`CP:src/agent_control_plane/freshness.py:62`)
- [SOURCE FACT] `Runtime recovery_resolution observation window 0 <= age <= 86400 s (inline literal)`: int literal (`RT:engine/recovery_resolution.py:266`)
- [SOURCE FACT] `Evidence-obligation max_age_seconds read from authority-context data (not a host field)`: int from data (`CP:src/agent_control_plane/bounded.py:2545`)

**Current evaluator** (component: Control Plane (primary) and Runtime (recovery window): both)

- [SOURCE FACT] _reconcile_observation: missing policy -> observation_policy_missing (1901); future limit = reference + clock_tolerance (1922); stale when age > max_age (1925). (`CP:src/agent_control_plane/bounded.py:1890`, `CP:src/agent_control_plane/bounded.py:1901`, `CP:src/agent_control_plane/bounded.py:1922`, `CP:src/agent_control_plane/bounded.py:1925`)
- [SOURCE FACT] _observe_and_reconcile missing policy on observe failure (1858). (`CP:src/agent_control_plane/bounded.py:1844`, `CP:src/agent_control_plane/bounded.py:1858`)
- [SOURCE FACT] _fresh (2017-2024) used for identity (2352), mandate (2366), grant status (2398-2399), conflicts (2445), current (2469), approval (2505), evidence obligations (2547, 2556). (`CP:src/agent_control_plane/bounded.py:2017`, `CP:src/agent_control_plane/bounded.py:2352`, `CP:src/agent_control_plane/bounded.py:2366`, `CP:src/agent_control_plane/bounded.py:2398`, `CP:src/agent_control_plane/bounded.py:2505`)
- [SOURCE FACT] Runtime recovery_resolution append: freshness assessed inside the lock; 'HOLD: synthetic observation outside 24-hour window'. (`RT:engine/recovery_resolution.py:266`)
- [REASONED INFERENCE] Control Plane involvement: Control Plane owns the gates; Runtime has an independent window literal.

**Source revision**: read at Control Plane 7a4bcd40b3b49e61ff3c294dcca53b52f460b22c; Runtime c5e97e87dd239c821b1b4a406a55dcd03c5bc61f; R07 read at CP 0a41faa972699f7ec3063967a14cd9bdd3e67d27; Runtime ec728da6dc301a664b331ac8986afd6e850a1273.

- [SOURCE FACT] R07 03 claims verified: observation_policy_missing at ~1856/1899 (actual 1858, 1901); ObservationPolicy at 409-415; cli_run.py:510; recovery_resolution.py:266-269. bounded.py reported identical at pin and head by doc 10 (blob 2cc8d998 in r10). (`CP:src/agent_control_plane/bounded.py:1858`, `CP:src/agent_control_plane/cli_run.py:510`, `RT:engine/recovery_resolution.py:266`)
- [UNVERIFIED] No pin history locally; bounded.py equality rests on doc 10/r10 statements. 

**Existing configuration mechanism**

- [SOURCE FACT] Host constructor keyword arguments and an ObservationPolicy model passed to BoundedAuthorizationWorkflow; opt-in FreshnessProfile inside the host RuntimeAuthorityProfile; the CLI hard-codes 300/5. (`CP:src/agent_control_plane/bounded.py:1263`, `CP:src/agent_control_plane/cli_run.py:510`, `CP:src/agent_control_plane/runtime_authority.py:162`)

**Mandatory code-owned invariants**

- [SOURCE FACT] Missing observation policy fails closed to a hold (observation_policy_missing); tolerance never extends the staleness window; future observations beyond tolerance rejected; trusted-clock handling; precedence rules (W7-042). (`CP:src/agent_control_plane/bounded.py:1901`, `CP:src/agent_control_plane/bounded.py:1922`)
- [SOURCE FACT] Lower bound age >= 0 in the Runtime window. (`RT:engine/recovery_resolution.py:267`)

**Typed composition requirements (R07 D4)**

| Field | Units | Order | Floor/ceiling | Direction | Unsupported-case outcome | Status | Label |
|---|---|---|---|---|---|---|---|
| each age bound (status/identity/mandate/approval/observation) | integer seconds | totally ordered scalars; no ruled relation between 60 (status, per class) and 300 (destination observation) | Code floor needed (>0); ceiling = code default | Minimum under a ruled direction (R07 PROPOSAL); D4 ruled that no universal direction exists | refuse whole / effective_value_invalid | Not ruled | SOURCE FACT |
| clock_tolerance_seconds, max_age_extension_seconds, anchor_deadline_to_inputs, nonce | seconds / booleans | no single direction | n/a | NOT DEFINABLE as one rule (R07 04 section 4 item 3) | composition_unsupported | Not definable | SOURCE FACT |

**Cross-family dependencies**

- [SOURCE FACT] F4/F5 overlap on the same decision: grant-status age is judged at bounded.py:2398-2399 using ActionClass.max_status_age_seconds when a runtime-authority profile exists, else the constructor's status_max_age_seconds (both default 60). R07 assigns the class field solely to F5 but the constructor argument is in F4's source range; two host-set fields feed one check selected by `if self.runtime_authority_profile`. (`CP:src/agent_control_plane/bounded.py:2398`, `CP:src/agent_control_plane/runtime_authority.py:87`, `CP:src/agent_control_plane/bounded.py:1271`)
- [SOURCE FACT] Same age bound also drives _class_age_bound with freshness extensions (an extension never raises an irreversible class). (`CP:src/agent_control_plane/bounded.py:1358`, `CP:src/agent_control_plane/bounded.py:1370`)
- [SOURCE FACT] Depends on a trusted clock source and observation authority (not provided by a registry record). (`REG:docs/registry-schema-analysis/04-schema-fitness-matrix.md:38`)

**Unresolved classification decisions** (listed, not resolved): decisions D1 (W6-042; 60-versus-300 relationship), D4, D2, D3, D7, D13; S02 UNRESOLVED rows W6-042, (adjacent, not mapped by R07: W6-004 EVIDENCE_KINDS and W6-005 UNKNOWN_BEHAVIORS govern obligations whose max_age_seconds is read at bounded.py:2545-2556). 60-versus-300 is an explicit UNRESOLVED relationship, not an S02 row.
Other open items: W8-041 reaper_interval, W8-042 nonce are F4-adjacent candidates (Tier 2 / Tier 1 until reviewed)

**Existing tests** (ids verbatim; run state not assessed)

- `suites/v1-probes/test_control_plane_probes.py::test_probe_clock_uncertainty_future_observation_accepted_exactly_up_to_declared_tolerance[0|5|30]` -- Tolerance boundary. (`Q:suites/v1-probes/test_control_plane_probes.py:44`)
- `suites/v1-probes/test_control_plane_probes.py::test_probe_clock_uncertainty_tolerance_never_extends_the_staleness_window` -- Staleness boundary (age == max_age is last fresh instant). (`Q:suites/v1-probes/test_control_plane_probes.py:55`)
- `suites/v1-probes/test_control_plane_probes.py::test_probe_clock_uncertainty_missing_observation_policy_holds_rather_than_assuming_a_tolerance` -- observation_policy_missing hold. (`Q:suites/v1-probes/test_control_plane_probes.py:82`)
- `suites/v1-probes/test_control_plane_probes.py::test_probe_clock_uncertainty_must_be_declared_non_negative_and_age_positive` -- Model validation of ObservationPolicy fields and default tolerance 5. (`Q:suites/v1-probes/test_control_plane_probes.py:72`)
- `suites/v1-scenarios/test_add_molt_verify.py::test_add_molt_verify_e3_grant_status_freshness_is_not_per_item` -- Default 60 s bound and class-level bounds 5/120 s on grant status. (`Q:suites/v1-scenarios/test_add_molt_verify.py:47`)
- `suites/operation-identity/test_freshness_profile.py::test_stalled_check_past_class_age_refused_at_dispatch (and ::test_outage_extension_recorded_with_authority)` -- Opt-in freshness/0.1 deadline and age extension. (`Q:suites/operation-identity/test_freshness_profile.py:190`)
- `suites/cognous-execution-runtime/tests/test_observation_compatibility.py (stale -> observation_stale; missing policy)` -- Observation reasons through the Runtime/CP seam. (`Q:suites/cognous-execution-runtime/tests/test_observation_compatibility.py:16`)

The Runtime 86400 s window has no test in suites/ (grep for 86400/24-hour finds only an unrelated ten-year-skew test). Run state not assessed.

**Authenticated selection / activation (R08/R09)**: Needs the Control Plane to become a registry consumer (E-04); blocked by W6-042 and 60-vs-300.

- [SOURCE FACT] R08 05 notes F4/F5 are the families whose evaluators live in the Control Plane; an F1-only profile does not make the Control Plane a consumer. (`REG:docs/r08-preparation/05-minimum-operational-profile.md:15`)

**Complexity**: score 5 of 5 [REASONED INFERENCE]. Fields: 14. Cross-component binding: yes. Composition: Per scalar only, after each direction is ruled; not definable across bounds/clocks. Composition not definable as one rule; two components; open critical rows (W6-042, 60-vs-300); wide blast radius; clock authority dependency.

**Qualification requirements**

- [REASONED INFERENCE] Per-scalar boundary and changed-condition tests with a controllable trusted clock; negative tests that a registry value cannot raise any bound above the code/host value or lower the tolerance to disable future-rejection. (`CP:src/agent_control_plane/bounded.py:1922`)
- [REASONED INFERENCE] Separate test for the F4/F5 selection at bounded.py:2398 (profile vs constructor). (`CP:src/agent_control_plane/bounded.py:2398`)
- [REASONED INFERENCE] Cross-component: Runtime window literal and CP gates must be shown not to contradict. (`RT:engine/recovery_resolution.py:266`)

### F5: Per-action-class authority declarations

**Definition** (family source)

- [SOURCE FACT] R07 02 F5: ActionClass and RuntimeAuthorityProfile host profile; sole owner of max_status_age_seconds; relaxing toggles (allow_synthetic_resolver) never registry-configurable; tightening subset only. (`REG:docs/registry-schema-analysis/02-rule-family-taxonomy.md:66`, `REG:docs/registry-schema-analysis/04-schema-fitness-matrix.md:28`, `REG:docs/registry-schema-analysis/06-family-schema-proposals.md:129`)

**Configurable fields**

- [SOURCE FACT] `ActionClass: class_id, irreversible (default True), max_status_age_seconds (default 60, >=0), on_unreadable (refuse|bounded_tolerance), requires_revocation_assurance, reversibility, reversible_until, reversal_cost, reads_protected_data, counterparty_observable`: pydantic fields (`CP:src/agent_control_plane/runtime_authority.py:85`)
- [SOURCE FACT] `RuntimeAuthorityProfile: catalogue_version, actions, producer_keys, allow_synthetic_resolver (default False; relaxing, excluded), and opt-in sub-profiles operation_identity, freshness, holder_inventory, merge, reversibility, dedupe, terminal_revocation`: pydantic fields (`CP:src/agent_control_plane/runtime_authority.py:154`)
- [SOURCE FACT] `R07 tightening subset (illustrative only): max_status_age_seconds lowered, on_unreadable bounded_tolerance->refuse, requires_revocation_assurance false->true`: R07 proposal (`REG:docs/registry-schema-analysis/04-schema-fitness-matrix.md:61`)

**Current evaluator** (component: Control Plane only)

- [SOURCE FACT] Model validation: ActionClass (82-110, validator calls reversibility.check_class_members), RuntimeAuthorityProfile (150-179, merge/dedupe need operation_identity), validate_extensions (251; holder_inventory_missing at 358-359). (`CP:src/agent_control_plane/runtime_authority.py:82`, `CP:src/agent_control_plane/runtime_authority.py:150`, `CP:src/agent_control_plane/runtime_authority.py:251`, `CP:src/agent_control_plane/runtime_authority.py:358`)
- [SOURCE FACT] Gates in BoundedAuthorizationWorkflow: _resolve_journal class checks (action_class_unknown 2110; irreversible with non-refuse on_unreadable -> action_class_invalid 2111; unauthenticated resolver unless allow_synthetic_resolver 2113); _read_grant bounded_tolerance branch (2189); _class_age_bound (1358); status freshness (2398-2399). (`CP:src/agent_control_plane/bounded.py:2069`, `CP:src/agent_control_plane/bounded.py:2110`, `CP:src/agent_control_plane/bounded.py:2113`, `CP:src/agent_control_plane/bounded.py:2189`, `CP:src/agent_control_plane/bounded.py:1358`, `CP:src/agent_control_plane/bounded.py:2398`)
- [SOURCE FACT] reversibility.check_class_members derives `irreversible` from `reversibility` and rejects conflicts (irreversible_flag_mismatch, protected_read_not_irreversible, unobservable_not_strict). (`CP:src/agent_control_plane/reversibility.py:125`, `CP:src/agent_control_plane/reversibility.py:143`, `CP:src/agent_control_plane/reversibility.py:157`)
- [REASONED INFERENCE] Control Plane involvement: Entirely Control Plane.

**Source revision**: read at Control Plane 7a4bcd40b3b49e61ff3c294dcca53b52f460b22c; R07 read at CP 0a41faa972699f7ec3063967a14cd9bdd3e67d27.

- [SOURCE FACT] R07 03/04 claims verified for allow_synthetic_resolver (bounded.py:1288, 2113), profile fields 153-170, reversibility.py:125-143 and 129-160. Minor: R07 02 cites runtime_authority.py:87-121 for ActionClass; ActionClass is declared at 82-110 and 87-121 spans ActionClass fields plus EvidenceCriterion (cosmetic). (`CP:src/agent_control_plane/bounded.py:1288`, `CP:src/agent_control_plane/bounded.py:2113`, `CP:src/agent_control_plane/runtime_authority.py:82`, `CP:src/agent_control_plane/reversibility.py:125`)
- [UNVERIFIED] runtime_authority.py/reversibility.py equality with the pin rests on doc 10 (identical per whole-tree diff stat). 

**Existing configuration mechanism**

- [SOURCE FACT] Trusted host configuration: a dict/model passed as runtime_authority_profile to BoundedAuthorizationWorkflow, validated and snapshotted at construction; the profile is committed into approvals (approval_commitment). (`CP:src/agent_control_plane/bounded.py:1263`, `CP:src/agent_control_plane/runtime_authority.py:186`)

**Mandatory code-owned invariants**

- [SOURCE FACT] Authenticated-resolver requirement; allow_synthetic_resolver requires an explicit test clock. (`CP:src/agent_control_plane/bounded.py:1288`, `CP:src/agent_control_plane/bounded.py:2113`)
- [SOURCE FACT] Derived `irreversible` cannot be changed alone; irreversible class must have on_unreadable=refuse; extension never raises an irreversible class's bound. (`CP:src/agent_control_plane/reversibility.py:143`, `CP:src/agent_control_plane/bounded.py:2111`, `CP:src/agent_control_plane/bounded.py:1370`)
- [SOURCE FACT] A class must be declared by the host; a payload may not add one (action_class_unknown / relaxation_unsupported). (`CP:src/agent_control_plane/bounded.py:2110`, `REG:docs/registry-schema-analysis/06-family-schema-proposals.md:129`)

**Typed composition requirements (R07 D4)**

| Field | Units | Order | Floor/ceiling | Direction | Unsupported-case outcome | Status | Label |
|---|---|---|---|---|---|---|---|
| max_status_age_seconds | integer seconds | integers | floor 0 by model (ge=0); a floor >0 needed; ceiling = host value | lower (PROPOSAL [I]); D4 unruled | refuse whole | Not ruled | SOURCE FACT |
| on_unreadable, requires_revocation_assurance | enum / bool | refuse stricter than bounded_tolerance; true stricter than false (PROPOSAL [I]) | n/a | one-way only | relaxation_unsupported | Not ruled | SOURCE FACT |
| irreversible / reversibility members | coupled enum + derived bool | n/a | n/a | Coupled composition deferred; standalone changes excluded | relaxation_unsupported | Excluded | SOURCE FACT |

**Cross-family dependencies**

- [SOURCE FACT] Sub-profiles for F4 (freshness), F7 (dedupe, merge) sit inside the same RuntimeAuthorityProfile; merge/dedupe require operation_identity. (`CP:src/agent_control_plane/runtime_authority.py:174`, `REG:docs/registry-schema-analysis/02-rule-family-taxonomy.md:68`)
- [SOURCE FACT] max_status_age_seconds vs the F4 constructor status_max_age_seconds feed one check (see F4). (`CP:src/agent_control_plane/bounded.py:2398`)
- [SOURCE FACT] Holder inventory (W8-068) is F5-adjacent host data feeding holder_inventory_missing. (`CP:src/agent_control_plane/runtime_authority.py:358`)

**Unresolved classification decisions** (listed, not resolved): decisions D1 (W8-014), D4, D2, D3, D7, D13; S02 UNRESOLVED rows W8-014. W8-068 (HolderInventory) CONFIGURABLE-CANDIDATE, Tier 1 until reviewed.

**Existing tests** (ids verbatim; run state not assessed)

- `suites/v1-probes/test_authority_ra_probes.py::test_probe_addauthra_reversible_tolerance_needs_unexpired_grant_and_matching_revision_and_scope` -- bounded_tolerance branch. (`Q:suites/v1-probes/test_authority_ra_probes.py:252`)
- `suites/v1-probes/test_authority_ra_probes.py::test_probe_addauthra_unauthenticated_resolver_cannot_authorize_or_derive_a_revocation` -- Resolver authentication requirement; also touches allow_synthetic_resolver at 555. (`Q:suites/v1-probes/test_authority_ra_probes.py:552`)
- `suites/v1-probes/test_authority_ra_probes.py::test_probe_addauthra_reversible_class_tolerance_cannot_override_a_known_purpose_closure_or_outage` -- Tolerance limits. (`Q:suites/v1-probes/test_authority_ra_probes.py:492`)
- `suites/operation-identity/test_reversibility_profile.py::test_reversible_until_past_deadline_treated_irreversible (and ::test_purpose_outage_*)` -- Reversibility members and on_unreadable tolerance. (`Q:suites/operation-identity/test_reversibility_profile.py:167`)
- `suites/outside-holder/test_holder_probe.py::test_requires_revocation_assurance_class_holds_until_inventory_exists` -- requires_revocation_assurance + holder inventory. (`Q:suites/outside-holder/test_holder_probe.py:112`)
- `suites/v1-scenarios/test_add_molt_verify.py::test_add_molt_verify_e3_grant_status_freshness_is_not_per_item` -- Class-level max_status_age_seconds 5/120 s. (`Q:suites/v1-scenarios/test_add_molt_verify.py:47`)

No suites/ test references irreversible_flag_mismatch (the derived-field coupling). Run state not assessed.

**Authenticated selection / activation (R08/R09)**: Needs Control Plane consumer (E-04); blocked by W8-014 and D4; tightening-only subset required.


**Complexity**: score 4 of 5 [REASONED INFERENCE]. Fields: 10. Cross-component binding: no. Composition: Per field, directional; set-level (class add) not defined. Tier 1, UNRESOLVED W8-014, D4 unruled, coupled derived fields, requires class-selection semantics; single component.

**Qualification requirements**

- [REASONED INFERENCE] Negative tests that no payload can add a class, flip a relaxing toggle, or set `irreversible` alone. (`CP:src/agent_control_plane/reversibility.py:143`)
- [REASONED INFERENCE] Profile-commitment tests: registry-derived effective profile must be what approval_commitment hashes, else approvals bind a different profile. (`CP:src/agent_control_plane/runtime_authority.py:186`)
- [REASONED INFERENCE] Per-field monotonic tightening battery with independent oracle. (`REG:docs/registry-schema-analysis/04-schema-fitness-matrix.md:61`)

### F6: Agent permission allow-list

**Definition** (family source)

- [SOURCE FACT] R07 02 F6: Runtime PermissionSystem.is_allowed, JSON file {agent: [perm,...]}; per-agent intersection; absent-agent behaviour needs a ruling (D5). (`REG:docs/registry-schema-analysis/02-rule-family-taxonomy.md:70`, `REG:docs/registry-schema-analysis/04-schema-fitness-matrix.md:62`, `REG:docs/registry-schema-analysis/06-family-schema-proposals.md:79`)

**Configurable fields**

- [SOURCE FACT] `permissions mapping: agent_id -> list of permission strings (exact membership)`: JSON object of string -> list[str] (`RT:engine/permissions.py:20`)
- [SOURCE FACT] `agents_absent_from_record (UNDECIDED in R07 06: unconstrained | deny)`: undecided (`REG:docs/registry-schema-analysis/06-family-schema-proposals.md:91`)

**Current evaluator** (component: Runtime)

- [SOURCE FACT] PermissionSystem.is_allowed (15-23): non-str action -> False; absent agent/non-list entry -> False; exact string membership. _load (8-13): FileNotFoundError -> {} (deny-all); malformed JSON is not caught (raises). (`RT:engine/permissions.py:15`, `RT:engine/permissions.py:8`, `RT:engine/permissions.py:11`)
- [SOURCE FACT] Only caller: legacy AgentEngine.execute_action (engine.py:31). AgentEngine's docstring says it is not the supported execution path, performs no side effect and can never report successful execution; agent_id is caller-asserted and never authenticated. (`RT:engine/engine.py:19`, `RT:engine/engine.py:31`, `RT:engine/engine.py:10`)
- [REASONED INFERENCE] Control Plane involvement: None.

**Source revision**: read at Runtime c5e97e87dd239c821b1b4a406a55dcd03c5bc61f; R07 read at Runtime ec728da6dc301a664b331ac8986afd6e850a1273.

- [SOURCE FACT] R07 03 F6 claims verified: is_allowed 15-23, missing file -> {} -> deny-all, permissions.json 4 lines; W2-002 malformed JSON raises verified (json.load not wrapped). Note permissions.py is unchanged in kind but R07 states it is 'not in this repository's baseline' (registry baseline) - not verifiable here. (`RT:engine/permissions.py:15`, `RT:engine/permissions.json:1`)
- [UNVERIFIED] No pin history locally. 

**Existing configuration mechanism**

- [SOURCE FACT] A JSON file path passed to AgentEngine(sandbox_dir, permissions_file, audit_log_file); a sample file ships in the repo (agent1 read/write, agent2 read). (`RT:engine/engine.py:17`, `RT:engine/permissions.json:1`)

**Mandatory code-owned invariants**

- [SOURCE FACT] Exact-string membership (no substring grants), missing file -> deny-all, non-list entry -> deny, non-str action -> deny; malformed JSON raises at construction. (`RT:engine/permissions.py:15`)

**Typed composition requirements (R07 D4)**

| Field | Units | Order | Floor/ceiling | Direction | Unsupported-case outcome | Status | Label |
|---|---|---|---|---|---|---|---|
| per-agent permission list | set of exact strings per agent key | none | n/a | Per-agent intersection (definable) | refuse whole | Definable per agent | SOURCE FACT |
| agent present in caller file but absent from registry record | n/a | n/a | n/a | Two internally consistent, different policies: unconstrained (overlay: caller list stands) or deny (key-wise intersection removes the agent). NOT RESOLVED (D5). Current evaluator on an agent absent from the caller's own file returns deny; that is a different question from registry-record silence. | undecided | D5 UNRESOLVED; needs source-backed baseline and operational-profile semantics | SOURCE FACT |

**Cross-family dependencies**

- [REASONED INFERENCE] None in code. Semantically adjacent to CP manifest/grant authority (agent permission is a local file check, not tied to grants or to the F1 allow-sets). (`RT:engine/engine.py:31`)

**Unresolved classification decisions** (listed, not resolved): decisions D5, D4 (n/a numeric), D2, D3, D7, D13; S02 UNRESOLVED rows none mapped. R07 02 states none of the 32 rows concerns F6; absent-agent semantics is a new question. W2-001 is CONFIGURABLE-CANDIDATE Tier 1; W2-002 MANDATORY-INVARIANT.
Other open items: new baseline import required for permissions.py

**Existing tests** (ids verbatim; run state not assessed)

- `suites/v1-probes/test_runtime_probes.py::test_probe_permissions_legacy_engine_denies_unlisted_agent_and_never_executes` -- Unlisted agent 'intruder' -> PermissionError; unlisted action -> PermissionError; allowed action still executed=False. (`Q:suites/v1-probes/test_runtime_probes.py:161`)
- `suites/v1-scenarios/test_scn_d09.py::test_scn_d09_legacy_agent_engine_performs_no_side_effect` -- Permitted legacy action reports unsupported/no execution; unpermitted refused. (`Q:suites/v1-scenarios/test_scn_d09.py:330`)
- `suites/mvp-d09/test_mvp_d09_exact_runtime.py (legacy AgentEngine pointed at route B directory; database unchanged)` -- Legacy engine cannot affect route B state. (`Q:suites/mvp-d09/test_mvp_d09_exact_runtime.py:233`)

Runtime repo's own tests/test_permissions.py (3 tests) is not relocated into the qualification repo. No qualification test covers malformed JSON or missing file. Run state not assessed.

**Authenticated selection / activation (R08/R09)**: Needs a new baseline/evaluator registration; PLUS the evaluator sits on an unsupported legacy path with caller-asserted identity, so activation questions are moot until a supported consumer exists (REASONED INFERENCE).

- [REASONED INFERENCE] R11 default order lists F6 second after F1 set fields, but no supported execution path consumes F6 today. (`REG:docs/plans/PROJECT_PLAN-v1.2.md:110`)

**Complexity**: score 4 of 5 [REASONED INFERENCE]. Fields: 2. Cross-component binding: no. Composition: Per agent yes; absent-agent no until D5. Level-4 trigger: composition conditional on unruled D5. Otherwise small (one mapping, one component).

**Qualification requirements**

- [REASONED INFERENCE] Tests for both absent-agent semantics only after a ruling; until then none can be written as pass criteria. (`REG:docs/registry-schema-analysis/08-open-architectural-decisions.md:66`)
- [REASONED INFERENCE] Malformed JSON, missing file, non-list entry, substring-grant negatives against the registry-composed map. (`RT:engine/permissions.py:8`)
- [REASONED INFERENCE] Identity-authentication gap: agent_id is asserted, so qualification can only show allow-list mechanics, not agent authentication. (`RT:engine/engine.py:10`)

### F7: Dedupe and replay-window defaults

**Definition** (family source)

- [SOURCE FACT] R07 02 F7: Runtime dedupe_destination.py (default 600 s) and CP DedupeProfile (provider_horizon <= escalation_deadline < dedupe_ttl); Tier 2 minimum; guard itself Tier 1; composition conditional. (`REG:docs/registry-schema-analysis/02-rule-family-taxonomy.md:74`, `REG:docs/registry-schema-analysis/04-schema-fitness-matrix.md:59`, `REG:docs/registry-schema-analysis/06-family-schema-proposals.md:97`)

**Configurable fields**

- [SOURCE FACT] `DedupeTtlOperationDestination dedupe_ttl_seconds (default 600; positive int)`: int seconds (`RT:engine/dedupe_destination.py:105`)
- [SOURCE FACT] `DedupeProfile.dedupe_ttl_seconds, provider_horizon_seconds, escalation_deadline_seconds (each >0)`: int seconds (`CP:src/agent_control_plane/dedupe.py:58`)
- [SOURCE FACT] `Destination-declared dedupe_capability ('dedupe-ttl/0.1') and dedupe_ttl_seconds (a destination attribute, never inferred)`: str / int (`CP:src/agent_control_plane/dedupe.py:97`)

**Current evaluator** (component: Both Control Plane and Runtime (cross-component binding required))

- [SOURCE FACT] Runtime DedupeTtlMixin._operation_guard: different effect id inside TTL -> operation_already_committed; row deleted after TTL; in-progress hold ignored after TTL. (`RT:engine/dedupe_destination.py:76`, `RT:engine/dedupe_destination.py:82`, `RT:engine/dedupe_destination.py:86`)
- [SOURCE FACT] CP DedupeProfile ordering validator (62-67); dedupe_mode (95-100); unresolved_effects (111-135); blocks_new_key (138-141); applied_under_other_effect (144-155); classify (158-175); due_escalations (178-194). (`CP:src/agent_control_plane/dedupe.py:62`, `CP:src/agent_control_plane/dedupe.py:95`, `CP:src/agent_control_plane/dedupe.py:111`, `CP:src/agent_control_plane/dedupe.py:144`, `CP:src/agent_control_plane/dedupe.py:158`)
- [SOURCE FACT] Gate wiring: _effect_gate_n4 (1569) emits dedupe_unresolved_attempt_blocks_new_key / dedupe_operation_effect_applied; reached only via _operation_gate when a merge or dedupe profile is configured; escalation_pass / dedupe_report (1514-1538). (`CP:src/agent_control_plane/bounded.py:1569`, `CP:src/agent_control_plane/bounded.py:1578`, `CP:src/agent_control_plane/bounded.py:1580`, `CP:src/agent_control_plane/bounded.py:1527`)
- [SOURCE FACT] Related code-owned dedupe that is not F7 data: effect_id PRIMARY KEY + operation digest binding (safe_executor.py:508, 790-805); non-TTL operation guard used by the selected Route B destination (operation_identity_destination.py:43-49; operation_identity_atomic_destination.py:37-38). (`RT:engine/safe_executor.py:508`, `RT:engine/safe_executor.py:790`, `RT:engine/operation_identity_destination.py:43`, `RT:engine/operation_identity_atomic_destination.py:37`)
- [REASONED INFERENCE] Control Plane involvement: Yes: ledger gates and escalation are CP; the key-forgetting TTL is Runtime.

**Source revision**: read at Control Plane 7a4bcd40b3b49e61ff3c294dcca53b52f460b22c; Runtime c5e97e87dd239c821b1b4a406a55dcd03c5bc61f; R07 read at CP 0a41faa972699f7ec3063967a14cd9bdd3e67d27; Runtime ec728da6dc301a664b331ac8986afd6e850a1273.

- [SOURCE FACT] R07 03 W3-063/W9-027 statements verified in content: _operation_guard behaviour, TTL positive int + default 600 (line 105), DedupeProfile ordering, dedupe_mode capability rule, ledger never expires. dedupe.py/merge.py/bounded.py reported identical at pin and head by doc 10 (not diffed here). (`RT:engine/dedupe_destination.py:76`, `CP:src/agent_control_plane/dedupe.py:62`)
- [UNVERIFIED] No pin history locally. 

**Existing configuration mechanism**

- [SOURCE FACT] Destination TTL: constructor keyword of the CI/local synthetic destination. Control-plane profile: host-governed RuntimeAuthorityProfile.dedupe (needs operation_identity). Both opt-in; with neither set nothing runs and no stored byte changes. (`RT:engine/dedupe_destination.py:105`, `CP:src/agent_control_plane/runtime_authority.py:168`, `CP:src/agent_control_plane/runtime_authority.py:174`, `CP:src/agent_control_plane/dedupe.py:3`)
- [SOURCE FACT] The module states that no real provider implements the capability. (`CP:src/agent_control_plane/dedupe.py:28`)

**Mandatory code-owned invariants**

- [SOURCE FACT] Ordering provider_horizon <= escalation_deadline < dedupe_ttl; capability never inferred; destination TTL must be >= profile TTL else mode none; in_progress never mints a new key; ledger memory never expires; effect-id dedupe never expires. (`CP:src/agent_control_plane/dedupe.py:62`, `CP:src/agent_control_plane/dedupe.py:95`, `CP:src/agent_control_plane/dedupe.py:147`)
- [SOURCE FACT] Runtime guard rolls back and refuses inside the effect transaction; positive-int TTL. (`RT:engine/dedupe_destination.py:44`, `RT:engine/dedupe_destination.py:84`)

**Typed composition requirements (R07 D4)**

| Field | Units | Order | Floor/ceiling | Direction | Unsupported-case outcome | Status | Label |
|---|---|---|---|---|---|---|---|
| dedupe_ttl_seconds / escalation_deadline_seconds / provider_horizon_seconds | integer seconds | joint: horizon <= deadline < ttl (strict < only at the deadline/ttl pair) | all >0 by model; floors/caps not defined | Candidate meet (max TTL, min deadline, min horizon) preserves the ordering [R07 inference], but the direction is an assumption: smaller TTL widens the duplicate window, earlier deadline trades availability; horizon direction not established. D4 forbids inferring direction from numeric type. | effective_value_invalid after composition; dependency_missing if destination capability absent | Conditionally definable, NOT established | SOURCE FACT |
| destination capability dependency | capability string + ttl | destination ttl >= profile ttl | n/a | Raising the effective profile TTL above the destination's declared TTL drops dedupe_mode from destination_ttl to none: a 'stricter' meet can weaken behaviour unless the capability is re-checked after composition (R07 hazard; confirmed by dedupe.py:95-100). | dependency_missing | Cross-component binding required | SOURCE FACT |

**Cross-family dependencies**

- [SOURCE FACT] F7 sits inside F5's RuntimeAuthorityProfile and requires operation_identity/0.1 (and merge/dedupe both read the same ledger). (`CP:src/agent_control_plane/runtime_authority.py:174`)
- [SOURCE FACT] F7 depends on a Runtime destination implementing dedupe-ttl/0.1; the selected Route B destination declares no dedupe_capability (dedupe_mode would be 'none'), so profile TTL semantic cannot be 'destination_ttl' on that route. (`Q:suites/mvp-d2-route-b/test_inventory_negatives.py:146`, `CP:src/agent_control_plane/dedupe.py:97`)
- [REASONED INFERENCE] Escalation-deadline ordering relates F7 to F4 only through the ledger clock; no code link to freshness bounds. (`CP:src/agent_control_plane/dedupe.py:178`)

**Unresolved classification decisions** (listed, not resolved): decisions D12, D4, D1 (W3-063, W9-027), D2, D3, D7, D13; S02 UNRESOLVED rows W3-063, W9-027. W3-062 (default 600) is CONFIGURABLE-CANDIDATE, Tier 3 in S02's own row but Tier 2 minimum in the normalised crosswalk (S02 section 3).

**Existing tests** (ids verbatim; run state not assessed)

- `suites/operation-identity/test_dedupe_profile.py::test_expired_destination_key_does_not_make_a_duplicate_fresh` -- With profile: CP ledger refuses dedupe_operation_effect_applied after destination key expiry; one effect. (`Q:suites/operation-identity/test_dedupe_profile.py:146`)
- `suites/operation-identity/test_dedupe_profile.py::test_a_second_effect_lands_when_the_destination_key_expires_today` -- KNOWN-LIMIT assertion: profile absent, a second effect lands. Passes by asserting the limit; it is not protection. (`Q:suites/operation-identity/test_dedupe_profile.py:168`)
- `suites/operation-identity/test_dedupe_profile.py::test_in_progress_never_mints_a_second_key / ::test_in_progress_then_renewal_dispatches_a_second_key_today (known-limit)` -- in_progress handling with and without profile. (`Q:suites/operation-identity/test_dedupe_profile.py:215`)
- `suites/operation-identity/test_dedupe_profile.py::test_escalation_fires_inside_the_key_ttl_and_says_whether_the_key_was_still_remembered / ::test_a_late_escalation_is_flagged_after_the_key_ttl / ::test_same_effect_id_is_deduped_after_the_ttl_because_effect_id_dedupe_never_expires` -- Deadline/horizon/TTL semantics and effect-id non-expiry. (`Q:suites/operation-identity/test_dedupe_profile.py:257`)
- `suites/mvp-d2-route-b/test_inventory_negatives.py::test_REFUSED_selected_destination_never_forgets_an_operation_after_time_passes / ::test_dedupe_ttl_destination_class_has_no_atomic_claim_path_and_is_not_the_selected_class` -- Selected Route B destination uses the non-TTL guard; the TTL-forgetting class is not the selected class. (`Q:suites/mvp-d2-route-b/test_inventory_negatives.py:129`)
- `suites/operation-identity/test_atomic_route_operation_identity.py::test_atomic_route_legacy_cap_two_renewal_commits_two_effects_today (known-limit) / ::test_atomic_route_operation_key_refuses_the_renewed_claim_at_cap_two` -- Default path allows a second effect when the cap permits; opt-in operation key refuses it. (`Q:suites/operation-identity/test_atomic_route_operation_identity.py:96`)
- `suites/mvp-d2-route-b/test_inventory_negatives.py::test_REACHABLE_direct_destination_call_with_caller_chosen_operation_id_defeats_identity` -- PASSES when a hole exists: direct destination call defeats operation identity. Documents reachability, not safety. (`Q:suites/mvp-d2-route-b/test_inventory_negatives.py:165`)
- `suites/operation-identity/test_merge_profile.py (merge_gate path; 9 tests) and suites/v1-scenarios/test_scn_c09.py (10 tests) and test_scn_d06.py::test_scn_d06_concurrent_duplicate_deliveries_at_most_one_effect` -- Repeat delivery and concurrent duplicates at most one effect (effect-id / claim consumption; not F7 data). (`Q:suites/v1-scenarios/test_scn_c09.py:68`)

Runtime repo's tests/test_n4_dedupe_destination.py (9 tests) is not relocated into suites/. No qualification test exercises dedupe.unresolved_effects or merge.attempt_outcomes with an 'absent' closeout (it cannot be stored; see special analysis 1). *_today and test_REACHABLE_* tests pass by asserting a limit or hole and are not protection evidence. Run state not assessed.

**Authenticated selection / activation (R08/R09)**: Needs both components as consumers and a destination capability; blocked by D4 direction, W3-063, W9-027/D12.

- [SOURCE FACT] The only destination that implements the TTL capability is a CI/local synthetic aid with no authority; no provider implements it. (`RT:engine/dedupe_destination.py:16`, `CP:src/agent_control_plane/dedupe.py:28`)

**Complexity**: score 5 of 5 [REASONED INFERENCE]. Fields: 4. Cross-component binding: yes. Composition: Conditional, not established. Two level-4 triggers across components (D4 direction + capability dependency + unresolved W3-063/W9-027).

**Qualification requirements**

- [REASONED INFERENCE] Joint-ordering tests on the effective triple after composition; capability re-check after composition (TTL above destination TTL must not silently weaken to mode none). (`CP:src/agent_control_plane/dedupe.py:95`)
- [REASONED INFERENCE] Time-controlled tests at TTL-1, TTL, TTL+1 for both components with an injected clock; ledger-vs-destination agreement tests. (`RT:engine/dedupe_destination.py:82`)
- [REASONED INFERENCE] Duplicate/irreversible-effect oracle independent of the builder (D13). (`REG:docs/registry-schema-analysis/08-open-architectural-decisions.md:72`)
- [REASONED INFERENCE] Do not count *_today / test_REACHABLE_* tests as protection. (`Q:suites/operation-identity/test_dedupe_profile.py:168`)

### F8: Demo policy tool lists

**Definition** (family source)

- [SOURCE FACT] F8 IS defined in R07/S02: 'Demo policy tool lists' (CP demo_policies.py:36-39, 81-84; rows W4-020/021), demo only, literals, no tests found, Tier 3 not asserted, treated as Tier 2 until reviewed. R07 02 states F8 is not a policy family and not a candidate. (`REG:docs/s02-inventory.md:46`, `REG:docs/registry-schema-analysis/02-rule-family-taxonomy.md:105`)
- [SOURCE FACT] F1c, F1d and F8 are all defined in the corpus: F1c/F1d in R07 02 F1 sub-group list; F8 in S02 section 3 and R07 02 section 4 note. (`REG:docs/registry-schema-analysis/02-rule-family-taxonomy.md:42`)

**Configurable fields**

- [SOURCE FACT] `read_only_recorder defaults: allowed_tools [crm_read, notes_search], blocked_tools [email_send, file_write]; authority record scope [read], source demo_policy_config`: list literals (`CP:src/agent_control_plane/demo_policies.py:36`)
- [SOURCE FACT] `write_enabled_recorder defaults: allowed_tools [crm_read, crm_write, notes_search], blocked_tools [email_send]; authority record scope [read, write]`: list literals (`CP:src/agent_control_plane/demo_policies.py:81`)

**Current evaluator** (component: Control Plane)

- [SOURCE FACT] PolicyGate._apply_rules reads frame.blocked_tools / frame.allowed_tools and active authority scopes (blocked_tool_policy, unknown_tool_policy, write_authority_policy ...); the demo lists only supply defaults to RunRecorder.start_run. (`CP:src/agent_control_plane/policy_gate.py:159`, `CP:src/agent_control_plane/policy_gate.py:168`, `CP:src/agent_control_plane/policy_gate.py:203`, `CP:src/agent_control_plane/records.py:92`)
- [REASONED INFERENCE] Control Plane involvement: Entirely CP; the lists are not read by the gate unless a caller uses the demo helper.

**Source revision**: read at Control Plane 7a4bcd40b3b49e61ff3c294dcca53b52f460b22c; R07 read at CP 0a41faa972699f7ec3063967a14cd9bdd3e67d27.

- [SOURCE FACT] demo_policies.py:36-39 and 81-84 verified; read_only_recorder/write_enabled_recorder have no callers in CP src/tests/docs (only docs/README.md:67 mentions the file) and none in the qualification suites. (`CP:src/agent_control_plane/demo_policies.py:36`, `CP:src/agent_control_plane/demo_policies.py:81`)
- [UNVERIFIED] No pin history locally. 

**Existing configuration mechanism**

- [SOURCE FACT] Function arguments allowed_tools / blocked_tools (None selects the demo default); the real mechanism for any run is RunRecorder.start_run(allowed_tools, blocked_tools). (`CP:src/agent_control_plane/demo_policies.py:13`, `CP:src/agent_control_plane/records.py:92`)

**Mandatory code-owned invariants**

- [SOURCE FACT] PolicyGate rule chain and order (first-match; read_allowed_tool_policy never consults scopes - W4-004 UNRESOLVED; default escalation). (`CP:src/agent_control_plane/policy_gate.py:159`, `CP:src/agent_control_plane/policy_gate.py:196`)

**Typed composition requirements (R07 D4)**

| Field | Units | Order | Floor/ceiling | Direction | Unsupported-case outcome | Status | Label |
|---|---|---|---|---|---|---|---|
| tool allow/block lists | string sets | n/a | n/a | Not defined; family is not a registry candidate | n/a | Out of scope per R07 | SOURCE FACT |

**Cross-family dependencies**

- [SOURCE FACT] Demo helper grants authority records (scope read / read+write) that unlock the write rule in PolicyGate (W4-023), so the demo lists are authority-adjacent although uncalled. (`CP:src/agent_control_plane/demo_policies.py:95`, `CP:src/agent_control_plane/policy_gate.py:203`)

**Unresolved classification decisions** (listed, not resolved): decisions D1 (W4-022, W4-023); S02 UNRESOLVED rows W4-022, W4-023, (adjacent: W4-004 read rule, W4-014/015 PolicyConfig.default_action, W4-018, W9-007 PolicyGate() default). No D-decision proposes migrating F8.

**Existing tests** (ids verbatim; run state not assessed)

- none found

No test found in suites/ or the CP clone referencing the demo recorders (grep read_only_recorder / demo_policies).

**Authenticated selection / activation (R08/R09)**: Not applicable: not a candidate.


**Complexity**: score 1 of 5 [REASONED INFERENCE]. Fields: 4. Cross-component binding: no. Composition: Not applicable. Mechanics only (literal lists, uncalled helpers). The scale's level-4 rule would fire on W4-023 (Tier 1 UNRESOLVED) if F8 were a candidate; R07 says it is not, so the score reports mechanics and NOT migration readiness.

**Qualification requirements**

- [REASONED INFERENCE] None proposed: R07 does not nominate F8. If ever reviewed, confirm the demo helpers are unused outside demos and the Tier 2 classification. (`REG:docs/s02-inventory.md:46`)

### F9: Tenant id length bound

**Definition** (family source)

- [SOURCE FACT] R07 02 F9: tenant id max length 128 in Runtime safe_executor.py:318-321 and CP bounded.py:151-154; lowering only; very low value. (`REG:docs/registry-schema-analysis/02-rule-family-taxonomy.md:78`, `REG:docs/registry-schema-analysis/04-schema-fitness-matrix.md:32`)

**Configurable fields**

- [SOURCE FACT] `tenant_id length 1..128 (max_length literal)`: int literal (`RT:engine/safe_executor.py:319`)

**Current evaluator** (component: Both (Runtime validate_snapshot; CP pydantic models))

- [SOURCE FACT] Runtime validate_snapshot tenant_id check (318-321). (`RT:engine/safe_executor.py:318`)
- [SOURCE FACT] CP model copies of max_length=128: TenantRuntimeProposal (bounded.py:154), TenantAuthorizationBinding (297), TenantApprovalProjection (local_authority_effect.py:45), TenantPolicyProjection (56), TenantLocalExecutionClaim (127). R07 lists only bounded.py:151-154; five CP copies plus one Runtime copy exist at the head. (`CP:src/agent_control_plane/bounded.py:154`, `CP:src/agent_control_plane/bounded.py:297`, `CP:src/agent_control_plane/local_authority_effect.py:45`, `CP:src/agent_control_plane/local_authority_effect.py:56`, `CP:src/agent_control_plane/local_authority_effect.py:127`)
- [REASONED INFERENCE] Control Plane involvement: Five independent copies in CP.

**Source revision**: read at Runtime c5e97e87dd239c821b1b4a406a55dcd03c5bc61f; Control Plane 7a4bcd40b3b49e61ff3c294dcca53b52f460b22c; R07 read at pins.

- [SOURCE FACT] R07 undercounts the copies (2 cited vs 6 found); Runtime copy at 318-321 matches; CP bounded.py:154 matches (R07: 151-154). (`RT:engine/safe_executor.py:318`, `CP:src/agent_control_plane/bounded.py:154`)
- [UNVERIFIED] local_authority_effect.py differs between pin and head in CP (doc 10); whether the three copies there pre-date the head is not determinable locally. 

**Existing configuration mechanism**

- [SOURCE FACT] None: bare literals in each file. (`RT:engine/safe_executor.py:319`)

**Mandatory code-owned invariants**

- [SOURCE FACT] min_length=1 (non-empty tenant is an isolation condition); exact-str type check; shape validation itself. (`RT:engine/safe_executor.py:319`, `CP:src/agent_control_plane/bounded.py:154`)

**Typed composition requirements (R07 D4)**

| Field | Units | Order | Floor/ceiling | Direction | Unsupported-case outcome | Status | Label |
|---|---|---|---|---|---|---|---|
| tenant_id max length | characters | integers | floor 1 by code; ceiling = literal 128 | Lowering only (minimum) (R07 PROPOSAL) | refuse whole | Definable but all copies must agree | SOURCE FACT |

**Cross-family dependencies**

- [REASONED INFERENCE] A lowered value applied in only one copy would make components disagree (Runtime accepts what CP refuses or the reverse): must-agree across 6 sites. (`RT:engine/safe_executor.py:319`, `CP:src/agent_control_plane/bounded.py:154`)

**Unresolved classification decisions** (listed, not resolved): decisions D4 (minor), D2, D3, D7, D13; S02 UNRESOLVED rows none mapped. W1-027 and W6-008 are CONFIGURABLE-CANDIDATE (Tier 2); W6-008 notes no test for the 128 bound.

**Existing tests** (ids verbatim; run state not assessed)

- none found

No qualification test targets the 128 bound (grep for 128/129 with tenant or length). Tenant-isolation tests exist for other tenant mechanics (e.g. suites/cognous-execution-runtime/tests/test_w3_c8_actual_tenant.py) but not this bound. Run state not assessed.

**Authenticated selection / activation (R08/R09)**: Same chain; no value case.


**Complexity**: score 3 of 5 [REASONED INFERENCE]. Fields: 1. Cross-component binding: yes. Composition: Yes (minimum). One scalar but six must-agree copies in two components, no tests; trivially definable composition.

**Qualification requirements**

- [REASONED INFERENCE] Boundary test at 128/129 in every copy and agreement test across components before any value could be registry-supplied. (`RT:engine/safe_executor.py:319`)

### F10: Diagnostic trend thresholds

**Definition** (family source)

- [SOURCE FACT] R07 02 F10: reason_vocabulary.py thresholds 5 and 1; non-gating; no authority semantics. (`REG:docs/registry-schema-analysis/02-rule-family-taxonomy.md:82`, `REG:docs/registry-schema-analysis/04-schema-fitness-matrix.md:33`)

**Configurable fields**

- [SOURCE FACT] `minimum_prior_count (default 5), minimum_current_exposure (default 1)`: int keyword defaults (`CP:src/agent_control_plane/reason_vocabulary.py:22`)

**Current evaluator** (component: Control Plane)

- [SOURCE FACT] refusal_trends: negative-value check (31), eligibility (37), _trend_report call (38). Output is an investigation signal; not a gate. (`CP:src/agent_control_plane/reason_vocabulary.py:21`, `CP:src/agent_control_plane/reason_vocabulary.py:31`, `CP:src/agent_control_plane/reason_vocabulary.py:37`)
- [REASONED INFERENCE] Control Plane involvement: Entirely CP.

**Source revision**: read at Control Plane 7a4bcd40b3b49e61ff3c294dcca53b52f460b22c; R07 read at CP 0a41faa972699f7ec3063967a14cd9bdd3e67d27.

- [SOURCE FACT] Signature at 21-25 with defaults on 22-23 (R07: 21-25, 31-32); matches. (`CP:src/agent_control_plane/reason_vocabulary.py:22`)
- [UNVERIFIED] reason-vocabulary files reported identical by doc 10. 

**Existing configuration mechanism**

- [SOURCE FACT] Keyword arguments of refusal_trends; callers pass exposures and may override thresholds. (`CP:src/agent_control_plane/reason_vocabulary.py:22`)

**Mandatory code-owned invariants**

- [SOURCE FACT] Non-negative validation; the report never infers tampering and does not gate. (`CP:src/agent_control_plane/reason_vocabulary.py:31`)

**Typed composition requirements (R07 D4)**

| Field | Units | Order | Floor/ceiling | Direction | Unsupported-case outcome | Status | Label |
|---|---|---|---|---|---|---|---|
| thresholds | counts | integers | floor 0 | None needed (no authority semantics) | n/a | No composition needed | SOURCE FACT |

**Cross-family dependencies**

- [REASONED INFERENCE] None. Reason-vocabulary versioning is M7/D8, separate from these thresholds. (`REG:docs/registry-schema-analysis/08-open-architectural-decisions.md:16`)

**Unresolved classification decisions** (listed, not resolved): decisions D2, D3, D7, D13 (low relevance); S02 UNRESOLVED rows none mapped. W5-002 CONFIGURABLE-CANDIDATE Tier 3 in its row; R07 treats as Tier 2 minimum.

**Existing tests** (ids verbatim; run state not assessed)

- `suites/v1-probes/test_rule_revision_probes.py::test_probe_n2_row_version_predates_adoption_flagged / ::test_probe_n2_pre_split_counts_tainted` -- refusal_trends is called with default thresholds; thresholds themselves not asserted. (`Q:suites/v1-probes/test_rule_revision_probes.py:219`)
- `suites/v1-probes/test_authority_ra_probes.py::test_probe_addauthra_refusal_trend_report_names_unmapped_codes` -- Trend report content. (`Q:suites/v1-probes/test_authority_ra_probes.py:679`)

Defaults 5 and 1 are not asserted by any qualification test found.

**Authenticated selection / activation (R08/R09)**: Same chain; negligible value.


**Complexity**: score 1 of 5 [REASONED INFERENCE]. Fields: 2. Cross-component binding: no. Composition: Not needed. Two non-gating kwargs, one component, no composition.

**Qualification requirements**

- [REASONED INFERENCE] Threshold boundary test; confirm non-gating (no decision reads the report). (`CP:src/agent_control_plane/reason_vocabulary.py:37`)

### F11: Redaction defaults

**Definition** (family source)

- [SOURCE FACT] R07 02 F11: RedactionConfig defaults and CLI binding; Tier 2 minimum with confidentiality controls treated as Tier 1; union composition inside a closed ordered category set. (`REG:docs/registry-schema-analysis/02-rule-family-taxonomy.md:86`, `REG:docs/registry-schema-analysis/04-schema-fitness-matrix.md:63`)

**Configurable fields**

- [SOURCE FACT] `redact_payloads (True), redact_targets (False), redact_final_output (False), redact_reasons (False)`: bool (`CP:src/agent_control_plane/models.py:424`)
- [SOURCE FACT] `replacement ('[REDACTED]'), keep_fingerprints (False)`: str / bool (`CP:src/agent_control_plane/models.py:439`)
- [SOURCE FACT] `CLI binding: redact_payloads forced True; targets/final-output/reasons/replacement from flags; keep_fingerprints never set`: CLI flags (`CP:src/agent_control_plane/cli.py:107`)

**Current evaluator** (component: Control Plane)

- [SOURCE FACT] redaction.redact_run_record / redact_replay_bundle / redact_tool_execution_result call _apply_redaction with config or RedactionConfig(); CLI builds the config in _redaction_config_from_args. (`CP:src/agent_control_plane/redaction.py:16`, `CP:src/agent_control_plane/redaction.py:27`, `CP:src/agent_control_plane/cli.py:107`)
- [REASONED INFERENCE] Control Plane involvement: Entirely CP.

**Source revision**: read at Control Plane 7a4bcd40b3b49e61ff3c294dcca53b52f460b22c; R07 read at CP 0a41faa972699f7ec3063967a14cd9bdd3e67d27.

- [SOURCE FACT] models.py:420-451 and cli.py:107-114 verified. (`CP:src/agent_control_plane/models.py:420`, `CP:src/agent_control_plane/cli.py:107`)
- [UNVERIFIED] No pin history locally. 

**Existing configuration mechanism**

- [SOURCE FACT] RedactionConfig object passed by the caller; CLI flags --targets --final-output --reasons --replacement. (`CP:src/agent_control_plane/redaction.py:16`, `CP:src/agent_control_plane/cli.py:107`)

**Mandatory code-owned invariants**

- [SOURCE FACT] Redaction of protected data cannot be removed by data (R07); CLI forces redact_payloads=True; fingerprints blanked whenever payloads/targets are redacted unless keep_fingerprints is set (unkeyed SHA-256 re-derivable for small search spaces). (`CP:src/agent_control_plane/cli.py:109`, `CP:src/agent_control_plane/models.py:443`)

**Typed composition requirements (R07 D4)**

| Field | Units | Order | Floor/ceiling | Direction | Unsupported-case outcome | Status | Label |
|---|---|---|---|---|---|---|---|
| redaction category toggles | bool set over closed categories | more redaction is stricter | protected categories not removable | Union of redaction categories (R07 PROPOSAL), only inside a closed ordered category set owned by code | composition_unsupported | Blocked by tier classification | SOURCE FACT |

**Cross-family dependencies**

- [REASONED INFERENCE] Distinct from the ODES/replay-bundle redaction that scenario C13 exercises (different component and mechanism). (`Q:suites/v1-scenarios/test_scn_c13.py:209`)

**Unresolved classification decisions** (listed, not resolved): decisions D1 (tier classification; W9-002 is a candidate row, not UNRESOLVED), D2, D3, D7, D13; S02 UNRESOLVED rows none mapped. R07: Tier 2 minimum, confidentiality controls treated Tier 1 until reviewed.

**Existing tests** (ids verbatim; run state not assessed)

- `suites/v1-probes/test_scan_fix_control_plane_probes.py::test_probe_redacted_export_does_not_keep_a_rederivable_fingerprint` -- RedactionConfig(redact_targets=True) blanks the fingerprint by default. (`Q:suites/v1-probes/test_scan_fix_control_plane_probes.py:77`)

Only one qualification test touches CP RedactionConfig. C13 tests exercise ODES/replay redaction, not this mechanism. Run state not assessed.

**Authenticated selection / activation (R08/R09)**: Same chain; confidentiality classification blocks first.


**Complexity**: score 3 of 5 [REASONED INFERENCE]. Fields: 6. Cross-component binding: no. Composition: Union within closed code-owned categories. Bool/str payload, single component, tier classification pending, CLI binding to settle.

**Qualification requirements**

- [REASONED INFERENCE] For every category: registry cannot reduce redaction below the code floor; payload redaction cannot be disabled; fingerprints blanked unless explicitly (and non-registry) kept. (`CP:src/agent_control_plane/models.py:443`)

Common authentication/selection facts (apply to every candidate family):

- [SOURCE FACT] R08 successor contract is not approved; the readiness verdict is NOT READY FOR IMPLEMENTATION; no R08/R09 implementation, family migration, activation or pin approval is authorized. (`REG:docs/r08-preparation/09-implementation-readiness.md:15`)
- [SOURCE FACT] D2 ruling: operational selection requires authenticated authority; pin-only integrity is insufficient; trust root, signing and custody are R09 work and not designed or approved. (`REG:docs/registry-schema-analysis/08-open-architectural-decisions.md:63`)
- [SOURCE FACT] No registry hook exists in either component at the pinned heads: a grep of Runtime engine/ and Control Plane src/ for the registry consumer/overlay API (apply_registry_overlay, registry_contract) finds nothing; the registry S04 consumer is called by no OCS component. (`REG:docs/r08-preparation/05-minimum-operational-profile.md:12`)
- [SOURCE FACT] Plan v1.2 sequencing: R08 (versioned contract) -> R09 (authentication, selection lifecycle, custody) -> R10 (consumer wiring, mandatory/optional participation, effect-time boundary) -> R11 (each family migrated only under separate operator authorization, oracle and independent qualifier). (`REG:docs/plans/PROJECT_PLAN-v1.2.md:93`, `REG:docs/plans/PROJECT_PLAN-v1.2.md:98`, `REG:docs/plans/PROJECT_PLAN-v1.2.md:103`, `REG:docs/plans/PROJECT_PLAN-v1.2.md:108`)
- [SOURCE FACT] Mandatory-participation profile is permitted as design capability only (D7 ruling); the independent Tier 1 qualification owner is not designated (D13). (`REG:docs/registry-schema-analysis/08-open-architectural-decisions.md:67`, `REG:docs/registry-schema-analysis/08-open-architectural-decisions.md:72`)

## Special analyses

### 1. F7 deduplication adequacy (D12 not resolved)

**Layers**

- [SOURCE FACT] Layer 1, effect_id PRIMARY KEY and operation-digest binding in the Runtime destination: the same effect id is deduped forever (no expiry). (`RT:engine/safe_executor.py:508`, `RT:engine/safe_executor.py:790`, `Q:suites/operation-identity/test_dedupe_profile.py:257`)
- [SOURCE FACT] Layer 2, operation-key guard with NO TTL, used by the selected Route B atomic destination: refuses a different effect id for an already-committed operation. Opt-in (operation-identity profile). (`RT:engine/operation_identity_destination.py:43`, `RT:engine/operation_identity_atomic_destination.py:37`, `Q:suites/mvp-d2-route-b/test_inventory_negatives.py:129`)
- [SOURCE FACT] Layer 3, TTL-forgetting guard (default 600 s) exists only in DedupeTtlOperationDestination, a CI/local aid with no atomic claim path; not the selected class. (`RT:engine/dedupe_destination.py:105`, `RT:engine/dedupe_destination.py:82`)
- [SOURCE FACT] Layer 4, CP ledger gates blocks_new_key and applied_under_other_effect (ledger never expires), reached only through _effect_gate_n4 via _operation_gate when a merge/dedupe profile is configured. (`CP:src/agent_control_plane/dedupe.py:138`, `CP:src/agent_control_plane/dedupe.py:144`, `CP:src/agent_control_plane/bounded.py:1554`, `CP:src/agent_control_plane/bounded.py:1569`)
- [SOURCE FACT] Default path (no operation-identity profile): a second effect on renewal/expiry lands when the cap allows; asserted by *_today tests that pass by asserting the limit. These are KNOWN_LIMIT_ASSERTED, not protection. (`Q:suites/operation-identity/test_atomic_route_operation_identity.py:96`, `Q:suites/operation-identity/test_dedupe_profile.py:168`)

**D12 source discrepancy**

- [SOURCE FACT] dedupe.unresolved_effects treats ANY closeout as resolving an attempt (closed set has no observed_state filter). (`CP:src/agent_control_plane/dedupe.py:122`)
- [SOURCE FACT] dedupe.applied_under_other_effect and merge.attempt_outcomes count a closeout only if observed_state is applied or partial. (`CP:src/agent_control_plane/dedupe.py:152`, `CP:src/agent_control_plane/merge.py:141`)
- [SOURCE FACT] The applied_under_other_effect docstring says 'any attempt with a closeout' while its code filters to applied/partial. (`CP:src/agent_control_plane/dedupe.py:147`, `CP:src/agent_control_plane/dedupe.py:152`)
- [SOURCE FACT] The two functions would differ ONLY for a closeout whose observed_state is neither applied nor partial (for example absent). (`CP:src/agent_control_plane/dedupe.py:122`, `CP:src/agent_control_plane/merge.py:141`)

**Reachability through the supported path**

- [SOURCE FACT] AttemptCloseout.observed_state is typed Literal['applied','partial']. (`CP:src/agent_control_plane/bounded.py:449`)
- [SOURCE FACT] The only writer, close_uncertain_attempts, returns early unless the observation state is applied or partial, then validates the whole document before writing. (`CP:src/agent_control_plane/bounded.py:668`, `CP:src/agent_control_plane/bounded.py:670`)
- [SOURCE FACT] _read_document validates every read against BoundedRunRecord, so a hand-edited record with another observed_state would fail validation on read. (`CP:src/agent_control_plane/bounded.py:598`, `CP:src/agent_control_plane/bounded.py:600`)

**Known**

- [REASONED INFERENCE] Through the supported store path the divergent input cannot be produced, so the discrepancy has no demonstrated execution path to a wrong outcome. This is NOT a finding that it is harmless: no analysis of future writers, extension fields or other schema versions was performed. 
- [REASONED INFERENCE] Supported-path evidence supports only: for closeouts in {applied, partial} the two functions agree. 

**Unknown**

- [UNVERIFIED] Whether the maintainers intend closeouts of other states ever to exist (for example absent, to be added by D12 or later work); the intent of the unfiltered set at dedupe.py:122 versus the docstring at :147 is unstated. 
- [UNVERIFIED] Whether any supported or planned writer or schema revision can emit another observed_state. 
- [UNVERIFIED] Whether adequacy holds under a real provider: no provider implements the capability, and no qualification test covers a real destination that forgets keys. 
- [UNVERIFIED] Whether the Route B default (profile absent) is acceptable for the V1 profile: the *_today tests show a second effect lands when the cap permits. 

Per brief: no supported execution path plus exact-source evidence of a wrong outcome was found, so the discrepancy is recorded as an unresolved source inconsistency tied to D12, not as a defect (label REASONED INFERENCE).

Adequacy: UNDETERMINED for the V1 profile. Code-owned layers 1 and 2 exist and are tested; layer 2 and 4 require opt-in profiles; the default path is a known limit. Whether that is adequate is a decision, not a source fact. (REASONED INFERENCE)

### 2. F1d target prefixes (D9)

- [SOURCE FACT] LocalExecutionPolicy._target_allowed: first rejects ill-formed targets in every mode, then exact -> equality; segment -> equality or startswith(prefix + separator) or prefix already ends in a separator; legacy-prefix -> bare startswith. (`RT:engine/safe_executor.py:396`, `RT:engine/safe_executor.py:400`, `RT:engine/safe_executor.py:405`)
- [SOURCE FACT] D9 ruling: F1d stays deferred until containment and matching-mode semantics are shown non-widening. (`REG:docs/registry-schema-analysis/08-open-architectural-decisions.md:69`)
- [REASONED INFERENCE] A registry list of prefixes cannot be composed by string-list intersection: whether prefix A admits a subset of prefix B depends on the match mode and separator rule, so the intersection of strings is not the intersection of admitted targets. 
- [REASONED INFERENCE] Mode choice is itself a widening/narrowing control: for a fixed entry list the admitted sets nest exact subset of segment subset of legacy-prefix (derived from the code). A registry-supplied mode could therefore widen; a rule of 'toward exact only' would be new semantics not in R07. 
- [SOURCE FACT] legacy-prefix is documented as a security-weakening opt-in. (`RT:CHANGELOG.md:20`)
- [SOURCE FACT] Zero qualification tests vary target_match; the Runtime-local tests/test_exact_target_matching.py is not relocated. (`Q:suites/v1-probes/test_runtime_probes.py:115`)

### 3. F6 absent-agent (D5 unresolved)

- [SOURCE FACT] is_allowed returns False for an agent absent from the loaded map; _load turns a missing file into an empty map (deny-all). (`RT:engine/permissions.py:15`, `RT:engine/permissions.py:8`)
- [SOURCE FACT] D5 is UNRESOLVED: the registry-record semantics for an agent present in the caller's file but absent from the registry record is undecided (unconstrained vs deny). (`REG:docs/registry-schema-analysis/08-open-architectural-decisions.md:66`, `REG:docs/registry-schema-analysis/06-family-schema-proposals.md:91`)
- [SOURCE FACT] Both options are internally consistent under R07: overlay leaves the caller's list; key-wise intersection removes the agent. (`REG:docs/registry-schema-analysis/04-schema-fitness-matrix.md:62`)
- [SOURCE FACT] Current evaluator behaviour for an agent absent from the caller's OWN file is deny; this does not answer registry-record silence. (`RT:engine/permissions.py:20`)
- [REASONED INFERENCE] Consequence for the V1 scope: F6 cannot receive a pass criterion for absent-agent handling until D5 is ruled; additionally the only consumer is the legacy AgentEngine with caller-asserted agent_id and no side effect, which bounds F6's customer value (value judgment belongs to the lead). 

### 4. max_effects and max_amount (D6 unresolved)

- [SOURCE FACT] D6 UNRESOLVED: whether max_effects and max_amount are code invariants, caller data, registry-eligible or layered. (`REG:docs/registry-schema-analysis/08-open-architectural-decisions.md:14`)
- [SOURCE FACT] max_amount: Runtime strict > compare of float(op.amount) against a unit-less ceiling; CP has its own independent amount ceilings from manifest/action limits and grant permission. (`RT:engine/safe_executor.py:425`, `CP:src/agent_control_plane/bounded.py:2682`, `CP:src/agent_control_plane/bounded.py:2735`)
- [SOURCE FACT] max_effects: the Runtime ceiling is compared with op.effective_max_effects, which CP computes as a three-way minimum; the exact-one-effect rule (op.effects == 1) is separate; cumulative and atomic budgets are two further independent counts. (`RT:engine/safe_executor.py:429`, `CP:src/agent_control_plane/bounded.py:2570`, `RT:engine/safe_executor.py:427`, `RT:engine/safe_executor.py:811`, `RT:engine/local_authority_effect.py:848`)
- [SOURCE FACT] Three layers (caller policy, CP computed cap, destination budget) exist today; a registry value could participate only in the first. (`RT:engine/safe_executor.py:429`)
- [REASONED INFERENCE] Facts established that bear on D6 (not a ruling): all amount/effect enforcement points are code-owned today; the ceiling VALUES are caller data in both components; qualification isolates the amount refusal (C11) but not the effect-count refusal. 

### 5. Evaluator location and cross-component binding

| Family | Evaluator location | G3 cross-component binding | Note | Label |
|---|---|---|---|---|
| F1a | Runtime | No | allow-sets from one frozen dataclass in Runtime | SOURCE FACT |
| F1b | Runtime (operands from CP) | Partial: values must equal CP-issued institution/domain | adapter trusted-context check is a second Runtime check | SOURCE FACT |
| F1c | Runtime ceiling + CP operand and CP-side limits | Yes | effective_max_effects computed in CP, ceiling in Runtime | SOURCE FACT |
| F1d | Runtime | No (blocked by semantics, D9) |  | SOURCE FACT |
| F3 | Both (independent literals) | No (independent guards) |  | SOURCE FACT |
| F4 | CP primary + Runtime recovery window literal | Yes | must not contradict across components | SOURCE FACT |
| F5 | CP only | No cross-component; needs CP as consumer | profile hashed into approvals | SOURCE FACT |
| F6 | Runtime only (legacy path) | No |  | SOURCE FACT |
| F7 | Both | Yes | destination capability + CP ledger/profile | SOURCE FACT |
| F8 | CP only (demo) | No | not a candidate | SOURCE FACT |
| F9 | Both (6 copies) | Yes (must agree) |  | SOURCE FACT |
| F10 | CP only | No | non-gating | SOURCE FACT |
| F11 | CP only | No |  | SOURCE FACT |

G3 here means: the registry could express the value, but a reliable binding to the enforcement boundary needs cross-component agreement or an effect-time integration not yet designed (REASONED INFERENCE; the final G-class assignment belongs to the lead).

## Cross-family dependency table

| From | To | Dependency | Label |
|---|---|---|---|
| F1a | F1b/F1c/F1d | One dataclass, one check() with fixed order; partial registry coverage leaves the rest caller-owned | SOURCE FACT |
| F1c | F5 (grant data) | Operand effective_max_effects derives from grant/requirement permission and action limits (CP) | SOURCE FACT |
| F1c | CP amount limits | Independent CP amount ceilings; Runtime ceiling is a second layer | SOURCE FACT |
| F1d | M1/F2 vocabulary | Match-mode vocabulary is code-owned; W1-029 UNRESOLVED | SOURCE FACT |
| F4 | F5 | Grant-status age: class max_status_age_seconds when a profile exists, else constructor status_max_age_seconds (bounded.py:2398) | SOURCE FACT |
| F4 | Runtime recovery window | Independent 86400 s literal; no test in suites/ | SOURCE FACT |
| F5 | F7 | dedupe and merge sub-profiles live inside RuntimeAuthorityProfile and require operation_identity | SOURCE FACT |
| F5 | holder inventory | requires_revocation_assurance holds without inventory | SOURCE FACT |
| F7 | Runtime destination | dedupe_mode depends on destination-declared capability and TTL; Route B declares none | SOURCE FACT |
| F9 | F3 | Both are shape/size bounds with independent copies | REASONED INFERENCE |
| F8 | F1/W4 PolicyGate | Demo lists grant scopes consumed by PolicyGate write rule; helpers uncalled | SOURCE FACT |

## Unresolved decisions touching each family

Listed from R07/S02; none is resolved here. D2, D3, D7, D13 and the R08-R10 chain apply to every candidate family and are shown once in each family row only where specific.

| Family | Decisions | S02 UNRESOLVED rows | Source |
|---|---|---|---|
| F1a | D2, D3, D7, D13, D11 (sequencing; F1b preferred next) | none mapped | R08 05 states F1a/F1b were not found to depend on an unresolved S02 row beyond the shared S06 deny-all/refusal questions; the dependence was not adjudicated (do not treat as cleared). |
| F1b | D11 (F1b recommended first extension; not authorized), D2, D3, D7, D13 | none mapped | No UNRESOLVED S02 row maps to F1b (R07 02 lists W-rows only for F1c/F1d). |
| F1c | D6, D4, D1 (W8-091), D2, D3, D7, D13 | W8-091 | W1-015 (2**53) is classified MANDATORY-INVARIANT (not UNRESOLVED) but is a stated representation prerequisite for F1c in R07 04. |
| F1d | D9, D4, D1 (W1-029), D2, D3, D7, D13 | W1-029 | W1-030 (separators) is CONFIGURABLE-CANDIDATE, Tier 1, kept in code per R07. |
| F3 | D1 (W2-082), D4, D2, D3, D7, D13 | W2-082 (linked by R07 not S02) | W1-007/W1-008 are CONFIGURABLE-CANDIDATE but Tier 1 admission guards. |
| F4 | D1 (W6-042; 60-versus-300 relationship), D4, D2, D3, D7, D13 | W6-042, (adjacent, not mapped by R07: W6-004 EVIDENCE_KINDS and W6-005 UNKNOWN_BEHAVIORS govern obligations whose max_age_seconds is read at bounded.py:2545-2556) | 60-versus-300 is an explicit UNRESOLVED relationship, not an S02 row. |
| F5 | D1 (W8-014), D4, D2, D3, D7, D13 | W8-014 | W8-068 (HolderInventory) CONFIGURABLE-CANDIDATE, Tier 1 until reviewed. |
| F6 | D5, D4 (n/a numeric), D2, D3, D7, D13 | none mapped | R07 02 states none of the 32 rows concerns F6; absent-agent semantics is a new question. W2-001 is CONFIGURABLE-CANDIDATE Tier 1; W2-002 MANDATORY-INVARIANT. |
| F7 | D12, D4, D1 (W3-063, W9-027), D2, D3, D7, D13 | W3-063, W9-027 | W3-062 (default 600) is CONFIGURABLE-CANDIDATE, Tier 3 in S02's own row but Tier 2 minimum in the normalised crosswalk (S02 section 3). |
| F8 | D1 (W4-022, W4-023) | W4-022, W4-023, (adjacent: W4-004 read rule, W4-014/015 PolicyConfig.default_action, W4-018, W9-007 PolicyGate() default) | No D-decision proposes migrating F8. |
| F9 | D4 (minor), D2, D3, D7, D13 | none mapped | W1-027 and W6-008 are CONFIGURABLE-CANDIDATE (Tier 2); W6-008 notes no test for the 128 bound. |
| F10 | D2, D3, D7, D13 (low relevance) | none mapped | W5-002 CONFIGURABLE-CANDIDATE Tier 3 in its row; R07 treats as Tier 2 minimum. |
| F11 | D1 (tier classification; W9-002 is a candidate row, not UNRESOLVED), D2, D3, D7, D13 | none mapped | R07: Tier 2 minimum, confidentiality controls treated Tier 1 until reviewed. |

## Limitations

- Source pins: Control Plane HEAD 7a4bcd40 and Runtime HEAD c5e97e87 were read. Runtime ec728da6 and CP 0a41faa9 are NOT available locally (shallow clones); the pin-to-head comparison is by content versus R07 doc claims, plus blob-hash equality for safe_executor.py. File-equality claims for other files rest on r08-preparation/10 and r10 statements (REPORTED, not re-derived). (UNVERIFIED)
- Mismatches found vs R07 text: (a) CP local_authority_effect.py effective_max_effects coordinate is 449 at head vs :443 in R07/S02 (that file differs between pin and head per doc 10); (b) F9 has 6 length-128 copies, R07 cites 2; (c) r10-feasibility says LocalExecutionPolicy.__post_init__ refuses empty sets, but a local construction showed an empty allow-set is accepted (only allowed_target_prefixes must be non-empty); (d) several S02-named Runtime test names were not located in suites/; (e) R07 02 cites runtime_authority.py:87-121 for ActionClass, declared at 82-110 (cosmetic). All SOURCE FACT except where stated.
- Run state: no test was run. Test ids are cited from reading; PASS/FAIL/NOT RUN is not asserted. coverage-map.json lists scenario verdicts NOT RUN. Nothing here converts NOT RUN to PASS.
- Component-local tests in Runtime and Control Plane repos (for example tests/test_exact_target_matching.py, test_permissions.py, test_n4_dedupe_destination.py, test_route_a_local_policy_reason.py) were read as source but are not part of the qualification suites.
- The open-control-stack repo is present locally (/home/claude/cogno-us/cognous-open-control-stack, read at 51c579a) although the brief says it is not cloned; only tools/mvp_ingress/synthetic_host.py:126-130 was used. The registry repo S04/S05 code and tests were not read; claims about S05 differential evidence rest on the R07/R08 docs.
- The 1-5 complexity scale is lane D's own rule-based construct (REASONED INFERENCE). It excludes shared R08-R10 infrastructure, and scores F8 on mechanics only.
- Cross-family and unresolved-decision mappings follow R07 doc statements; I did not adjudicate any D1/D5/D6/D12 row and did not read all 32 UNRESOLVED S02 rows, only those R07 maps to a family or that sit adjacent in the same code.
- Production deployment: how a real operator constructs LocalExecutionPolicy or profiles is not shown by any source read (synthetic hosts only). Customer, regulatory or revenue relevance is not assessed and not assumed.
- Dedupe analysis covers pure-function and store-path reading only; no concurrency, crash, or provider behaviour was exercised.
