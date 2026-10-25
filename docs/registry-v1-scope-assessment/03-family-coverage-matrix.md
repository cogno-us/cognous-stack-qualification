# 03 Family coverage matrix

Non-authorizing. Labels as in [01](01-executive-assessment.md). Counts are **distinct scenario IDs** from the [canonical crosswalk](data/canonical-scenario-crosswalk.csv) (in-scope rows only: 40 catalog + 65 Wiki); suite-local claims are counted separately and never added to the canonical denominator. A scenario mapped to several families appears under each, so family rows must not be summed.

## 1. Summary

| Family | In-scope canonical scenarios touched | REQUIRED | BENEFICIAL | UNKNOWN | UNNECESSARY | Max consequence severity (1-5) | Suite-local claims touched | Complexity (1-5, Lane D) |
|---|---|---|---|---|---|---|---|---|
| F1a | 7 | 0 | 5 | 1 | 1 | 4 | 4 | 1 |
| F1b | 3 | 0 | 1 | 1 | 1 | 4 | 2 | 2 |
| F1c | 9 | 0 | 1 | 7 | 1 | 4 | 6 | 4 |
| F1d | 2 | 0 | 0 | 2 | 0 | 4 | 3 | 5 |
| F3 | 2 | 0 | 0 | 1 | 1 | 4 | 3 | 3 |
| F4 | 9 | 0 | 4 | 1 | 4 | 5 | 12 | 5 |
| F5 | 7 | 0 | 2 | 3 | 2 | 4 | 6 | 4 |
| F6 | 2 | 0 | 1 | 1 | 0 | 4 | 2 | 4 |
| F7 | 3 | 0 | 1 | 0 | 2 | 5 | 8 | 5 |
| F8 | 0 | 0 | 0 | 0 | 0 | - | 0 | 1 |
| F9 | 1 | 0 | 0 | 0 | 1 | 4 | 1 | 3 |
| F10 | 0 | 0 | 0 | 0 | 0 | - | 1 | 1 |
| F11 | 1 | 0 | 0 | 1 | 0 | 3 | 1 | 3 |

`REQUIRED` is 0 for every family (REASONED INFERENCE; see [01](01-executive-assessment.md) section 1 for why this does not show the registry is unnecessary). "Complexity" is Lane D's rule-based 1-5 scale (fields, cross-component binding, composition definability, unresolved decisions); 5 is hardest. Family definitions are the R07 definitions (`docs/registry-schema-analysis/02-rule-family-taxonomy.md` on registry main `783ff59f`); F8 is not an R07 policy family (Lane D found a definition only as the demo policy tool lists).

## 2. Per-family detail

Evaluator citations are `RT:` Runtime `c5e97e87` and `CP:` Control Plane `7a4bcd40` (SOURCE FACT, Lane D, 285 citations checked for file and line range at those heads; about 30 spot-read). Pre-pin differences cannot be diffed (shallow clones). Full per-family source analysis: [appendix D](appendix/lane-D-family-source-analysis.md) and [JSON](appendix/lane-D-families.json).

### F1a Action / adapter / unit allow-lists (complexity 1)
- **Scenarios.** BENEFICIAL: C11, TC-L06-003, TC-L06-009, TC-L06-011, TC-L06-013. UNKNOWN: TC-L06-014. UNNECESSARY: C02.
- **Evaluator.** `RT:engine/safe_executor.py` `LocalExecutionPolicy` (`:359`), `check` (`:410`); constructor-only, no loader (no environment variable is read in Runtime `engine/` or Control Plane `src/`).
- **Protected without migration.** Yes: the refusal is in code and tested (C02, D02). A registry copy of an allow-list would duplicate a comparison the code already makes (D02, C02: the refusing control is binding to proposal/decision/grant and manifest membership, `control_plane_adapter.py:270-316`, `bounded.py:2608-2689`).
- **What the registry adds.** Central, versioned, authenticated change control of the allow-lists; the "next call" change behaviour is tested only in NOT RUN Wiki-derived tests (TC-L06-011, TC-L06-013).
- **Decisions.** D2, D3, D7, D13; D11 (sequencing). No UNRESOLVED S02 row maps to F1a (Lane D).
- **Qualification needed.** An MVP-tuple oracle row for a `LocalExecutionPolicy` denial (none exists; GAP-G4-09); effect-time binding tests (GAP-G3-02); independent run at exact heads.
- **Exclusion consequence.** Allow-lists stay host constructor literals. No enforced capability is lost.

### F1b Institution / authority-domain allow-lists (complexity 2)
- **Scenarios.** BENEFICIAL: C11. UNKNOWN: C18. UNNECESSARY: D02.
- **Evaluator.** Same dataclass and `check` as F1a (`RT:engine/safe_executor.py:360-361`); operands come from the Control Plane context; the Route A adapter also takes `trusted_institution_id` / `trusted_authority_domain` as separate constructor values.
- **Decisions.** D11 (preferred first extension; an architectural priority, not permission), D2, D3, D7, D13. No UNRESOLVED S02 row maps to F1b.
- **Exclusion consequence.** As F1a. Excluding F1b while including F1a leaves C11 and C18 partly covered.

### F1c Ceilings: `max_amount`, `max_effects` (complexity 4)
- **Scenarios.** BENEFICIAL: C11. UNKNOWN: C16, C18, TC-D13-003, TC-L06-014, TC-L06-016, TC-L06-024, TC-L09-014. UNNECESSARY: D02.
- **Evaluator.** Ceiling check in `RT:engine/safe_executor.py` (exact-one-effect re-asserted at `:316`); the effective `max_effects` operand is computed in Control Plane `bounded.py:2570`. Two ends must agree.
- **Why seven rows are UNKNOWN.** D6 (code invariant versus caller configuration versus governed parameter) and S02 row W8-091 are open. They are not resolved here and the ceilings are not migrated by this assessment.
- **Protected without migration.** The budget behaviour is tested in the catalog (C16, historical named-case PASS) and exact under load in Wiki-derived tests that are NOT RUN. The Verifier checks `effective_max_effects` only against the proposal export and ledger (GAP-G1-05).
- **Exclusion consequence.** Ceilings remain host constructor literals and manifest limits. Importantly for the Architect's question on financial/quantitative limits: no source text here establishes a finance domain; the family governs effect budgets.

### F1d Target prefixes and match mode (complexity 5)
- **Scenarios.** UNKNOWN: TC-L06-014, TC-L07-012.
- **Evaluator.** `RT:engine/safe_executor.py:343` (`target_match`: `segment`, `exact`, `legacy-prefix`; `legacy-prefix` is a documented weakening mode); `allowed_target_prefixes` must be non-empty.
- **Why deferred.** Composition is not definable (the prefix relation depends on mode and separators, so intersecting prefix strings does not intersect admitted targets). D9 defers F1d until containment is shown non-widening. No qualification test varies `target_match` (GAP-G3-06).

### F3 Size, depth and timeout budgets (complexity 3)
- **Scenarios.** UNKNOWN: D06 (unsupported by its own text: needs measured limits against a predeclared profile that does not exist). UNNECESSARY: C10.
- **Evaluator.** `RT:engine/safe_executor.py:147-155` literals (1 MiB, depth 32, 10000 nodes). They are hostile-input bounds that need a code-owned floor and ceiling if ever migrated.
- **Exclusion consequence.** None observed. Not unexpectedly critical.

### F4 Observation, status and approval freshness (complexity 5)
- **Scenarios.** BENEFICIAL: C01, TC-D09-009, TC-D09-016, TC-L06-015. UNKNOWN: H01. UNNECESSARY: D03, A03, C06, C17.
- **Evaluator.** Split across `CP:src/agent_control_plane/bounded.py:411-413` (`ObservationPolicy`), `:1858,:1901` (`observation_policy_missing` hold), `:2398-2399` (grant-status age) and Runtime evidence-row `max_age_seconds`. The CLI hard-codes 300/5. A source comment at `bounded.py:1782-1784` says the window is narrowed, not closed.
- **Decisions.** D1 (W6-042 and the 60-versus-300 relationship, which stays a distinction between different quantities), D4 per scalar.
- **Qualification needed.** Per-scalar composition tests (units, order, floor, direction); clock-domain tests. TC-L06-015 is rated severity 5 for the whole Wiki subject, but OCS claims only hold, rejection and expiry.
- **Exclusion consequence.** Freshness windows stay constructor arguments and evidence-row values; the fail-closed missing-policy hold is a code invariant and is unaffected.

### F5 Per-action-class authority declarations (complexity 4)
- **Scenarios.** BENEFICIAL: C01, TC-D09-016. UNKNOWN: H01, C05, TC-L05-012. UNNECESSARY: D03, TC-L05-013.
- **Evaluator.** `CP:src/agent_control_plane/runtime_authority.py:82-150` (`ActionClass`, `RuntimeAuthorityProfile`), consumed in `bounded.py`.
- **Relaxing toggles.** `ActionClass.on_unreadable: Literal["refuse","bounded_tolerance"]` (`runtime_authority.py:88`; `bounded.py:2186-2200`) can relax a refusal and must not become registry-configurable (R07). The Wiki-derived test `test_wiki_l05_013_..._known_limit` searches for names containing fail_open, fail_mode, on_error and similar; none matches `on_unreadable`, so it cannot detect this opt-in (GAP-G4-05; lead re-read of test lines 750-755 and the field).
- **Decisions.** D1 (W8-014 UNRESOLVED), D4.

### F6 Agent permission allow-list (complexity 4)
- **Scenarios.** BENEFICIAL: TC-L06-013. UNKNOWN: D09.
- **Evaluator.** `RT:engine/permissions.py:20`, used only by the legacy `AgentEngine` (`engine/engine.py:39`), which executes nothing; `agent_id` is caller-asserted.
- **Decisions.** D5 (absent-agent semantics) unresolved; this assessment does not choose between unconstrained and deny.
- **Why deferred.** A registry-managed F6 would govern a path that enforces no effect today (GAP-G3-05). The ordering in plan v1.2 (F6 early) assumes a consumer that the corpus does not show.

### F7 Deduplication and replay-window defaults (complexity 5)
- **Scenarios.** BENEFICIAL: C09. UNNECESSARY: D04, C08. Suite-local: 7 BENEFICIAL (operation-identity and v1-probe claims), 1 UNNECESSARY.
- **Evaluator.** `RT:engine/dedupe_destination.py:105` (TTL default 600; synthetic CI/local destination); `CP:` `RuntimeAuthorityProfile.dedupe` (needs `operation_identity`). Both opt-in. The selected route B destination has no TTL (`operation_identity_destination.py:43-49`), so F7 is not engaged on the selected MVP route.
- **Does existing code-owned deduplication adequately protect the relevant outcomes?** **Undetermined, and not shown adequate.** The duplicate-effect protection that is tested comes from effect-id / operation-identity guards, not from a tunable TTL; the profiles are OFF by default and six `*_today` tests assert that the legacy default lets two effects land (they pass by asserting the limit, so they are not protection; GAP-G1-01). Five `test_REACHABLE_*` tests likewise pass by showing a hole (GAP-G1-03). A registry-managed TTL would not change either result. **Therefore V1 does not require registry-managed deduplication parameters; what it requires is an owner decision on defaults.**
- **D12 (not resolved).** `dedupe.py:122` counts any closeout as resolving an attempt, while `dedupe.py:152` and `merge.py:141` count only applied or partial closeouts. `AttemptCloseout.observed_state` is `Literal["applied","partial"]` (`bounded.py:449`) and the only writer returns early on any other state (`bounded.py:668`), validated on every read (`:598-600`). No supported path to the divergent input was found, so it is **not** characterized as a defect; intent and adequacy remain open.

### F8 Demo policy tool lists
Not a policy family and not consumed (helpers have no callers; `CP:demo_policies.py:36-39,81-84`). No scenario maps. Excluded from every profile.

### F9 Tenant-id length bound (complexity 3)
- **Scenarios.** UNNECESSARY: A04. Six must-agree copies of a length-128 literal across two components, no tests of the bound. Keep as code constants.

### F10 Diagnostic trend thresholds (complexity 1)
- **Scenarios.** None. Non-gating diagnostic keyword defaults (`CP:reason_vocabulary.py:22`).

### F11 Redaction defaults (complexity 3)
- **Scenarios.** UNKNOWN: TC-L06-028 (payload not masked in logs is a known-limit test; tier classification pending). Protected-data redaction cannot be removed by data (R07).

## 3. Deferred families: is any unexpectedly critical?

No. F3 touches D06 (unsupported by its own text) and C10 (UNNECESSARY); F9 touches A04 (UNNECESSARY); F10 touches nothing; F11 touches one UNKNOWN Wiki row that is a known limit; F8 touches nothing; F6 touches two scenarios with no effect-bearing consumer; F7 touches the highest-severity duplicate-effect scenarios but is blocked by D12 and by a component-default question, not by a missing registry family.

## 4. Profile comparison

| Profile | Families | Canonical scenarios touched | Fully covered (all families of the scenario in profile) | of which BENEFICIAL | of which UNKNOWN | of which UNNECESSARY | BENEFICIAL, severity>=4 | Suite-local touched / fully |
|---|---|---|---|---|---|---|---|---|
| A | F1a+F1b | 9 | 3 | 2 | 0 | 1 | TC-L06-009, TC-L06-011 | 4 / 1 |
| B | F1a+F1b+F1c+F4+F5 | 26 | 23 | 7 | 9 | 7 | C01, C11, TC-D09-016, TC-L06-009, TC-L06-011, TC-L06-015 | 23 / 20 |
| C | B + F6 | 27 | 25 | 8 | 10 | 7 | C01, C11, TC-D09-016, TC-L06-009, TC-L06-011, TC-L06-013, TC-L06-015 | 25 / 22 |
| D | C + F1d | 28 | 27 | 8 | 12 | 7 | C01, C11, TC-D09-016, TC-L06-009, TC-L06-011, TC-L06-013, TC-L06-015 | 25 / 23 |

Definitions and the reading are in [01](01-executive-assessment.md) section 3. Counts treat each scenario once. Suite-local claims touched/fully covered are in the last column; they are claims grouped from suites such as operation-identity and mvp-chain, not scenarios.

## 5. Important scenarios not covered by any candidate family

- **Unmapped mechanisms (no R07 family):** TC-L06-018 agent-to-agent authenticity (KNOWN_GAP), exchange sender and recipient sets, manifest content and component pins, policy revision and change control (TC-L06-034, TC-L06-041, TC-L08-036), trust anchors / producer keys, funded authorities. Eight in-scope Wiki rows are UNMAPPED and BENEFICIAL; they need an architectural decision on whether a new family exists before they can enter any profile.
- **No driver:** A01-A06, H01, H02, C05, C15, C19, C20, C21.
- **Code or evidence gaps no family can close:** [05](05-gap-register.md) G1 and G4 rows.
