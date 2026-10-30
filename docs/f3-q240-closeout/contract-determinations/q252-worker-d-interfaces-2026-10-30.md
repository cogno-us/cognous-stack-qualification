# WORKER D (static, read-only) - OCS-F3-Q252-FEASIBILITY: interface applicability of three ECB members

Same session lineage as the lead builder: NOT independent. Nothing executed; no product code run. Method: `git show`/`git grep` at CP `739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69` (abbrev `739`) and Registry `origin/main` `6b96a9a658923954433dc1a4c13626fa5145b9c7` records 02, 03, 06, 11, 12, 13, 14; hub evidence read from the checkout at `/home/claude/cogno-us/cognous-stack-qualification` (current branch `f3a-readjudication-20261030`, plus unmerged remote branches `evidence/f3-q2q3-isolation-20261030` = D-1, `evidence/f3-q4q5q6-20261030` = D-2). Scratch copies of sources live in the session scratchpad only. Line numbers are 739 unless prefixed. File aliases: `B` = bounded.py, `L` = registry_governed_lifecycle.py, `E` = effective_configuration_binding.py, `P` = authorization_pin_export.py, `C` = local_authority_effect.py, `G` = registry_governed_policy.py.

Evidence labels: FACT = read in source/record. INFERENCE = my reading, not executed. UNVERIFIED = not shown by any evidence I read.

---------------------------------------------------------------------------------------------------------------------------------
## 1. Where the ECB comparison lives (common to all three interfaces)

FACT. The comparison is not a separate gate. `GovernedLifecycle._resolve` (L:263-285) calls `super()._resolve` (B:2055 -> `_resolve_journal` B:2069-2144 -> `_resolve_inputs` B:2239-2606). If the base returned ANY reason or no binding, it returns them unchanged (L:267-268) and the ECB is never computed. Otherwise it mints the live member (L:271-272; `BindingInvalid` -> raises `_gl_refuse("configuration_binding_invalid")` L:276-277), classifies the persisted member against it (L:275, `E.classify` E:193-209), stamps the live member into the rebuilt binding (L:281, 291) and, only for a non-accepted status whose persisted dict happens to compare Python-equal, adds the reason `authorization_binding_changed` (L:283-284). The refusal itself is the pre-existing equality `current != persisted.binding`: B:1690 (execute), P:181 (pin-export), C:455 (claim). Consequence (FACT, confirmed by D-1 guard table): a refusal carrying `authorization_binding_changed` is emitted for ANY difference in the rebuilt binding (B:1692-1693), so the code alone never attributes the refusal to one ECB member.

`_gl_revalidate`/`_gl_reverify` (L:297-316: proposal scope, held-state, `manifest_authority_changed`, `selection_changed`) run ONLY inside `GovernedLifecycle.execute` (L:330-338), before `super().execute`. They are NOT run by pin-export (P has no call) or by claim (C has no call). (FACT, grep of both files.)

---------------------------------------------------------------------------------------------------------------------------------
## 2. Interface A - effecting execute (B:1662-1833, wrapper L:330-338)

### 2.1 Workflow families that reach an ECB comparison
FACT (all `GovernedLifecycle` subclasses; `git grep` finds exactly four, no others):
| Family / class | File:line | Profile? | host/effective digest members | Notes |
|---|---|---|---|---|
| F4 dedicated `GovernedAgeWorkflow` | registry_f4_age_governance.py:100 | refuses any profile (`runtime_authority_profile_unsupported`, :110-111) | both constant `null` (:158) | `r08-v2` `f4-control-plane-age-bounds` |
| F5 class-age `GovernedClassAgeWorkflow` | registry_f5_class_age_governance.py:188 | profile required, `policy_binding` refused (:206-207) | digest(host snapshot), digest(held) (:260) | `r08-v2` `f5-action-class-age-bounds`; outage-extension limit composed in `compose_profile` (:117-126) = the "freshness-extension" case, not a separate family |
| class-unreadable `GovernedClassUnreadableWorkflow` (alone or joined with class age) | registry_f5_class_unreadable_governance.py:236 | profile required, `policy_binding` refused (:263-264) | :336 | `r08-v5` |
| policy-composition `GovernedPolicyWorkflow` | G:298 | optional; required if any of class_age/unreadable/assurance/terminal/irreversible/anchor declared (G:323-327); `policy_binding` refused iff one of those six is declared (G:333-334) | G:476-486 (`hd`,`ed` null iff no profile) | slots in order `FAMILY_NAMES` G:64-65: f4_ages r08-v2, class_age r08-v2, class_unreadable r08-v5, class_revocation_assurance r08-v6, class_irreversible r08-v7, anchor_deadline r08-v8, observation_max_age r08-v8, observation_clock_tolerance r08-v8, terminal_revocation r08-v6 (registry_effective_policy.py:25-35) |
| plain `BoundedAuthorizationWorkflow` | B | any | NO ECB minted or checked (record 02 D-06.4; no `GovernedLifecycle`) | out of scope |

### 2.2 Entry conditions (FACT)
Decision in store and equal to caller's (B:1674-1676); `result == authorized` with binding (B:1677-1678); `effect_id` recomputes (B:1679-1680); for governed: proposal is `TenantRuntimeProposal` of the bound tenant/action (L:299-300). Hold decisions never reach the ECB.

### 2.3 Guard order (every guard before the ECB comparison, then everything after)
Before (refusal kind in brackets):
1. L:332 `_evaluation_time`; L:297-301 `_gl_revalidate` -> `proposal_out_of_scope` [non-durable `RegistrySelectionRefused`, a `PermissionError` subclass L:65; no row].
2. L:303-316 `_gl_reverify`: `_gl_held_defect` (`scalars_modified`, `profile_modified`, `observation_policy_modified`, `activation_superseded`; G:488-509, f4:150-154, f5:249-253) -> `manifest_authority_changed` (L:307-309) -> Registry sources re-read and re-derived, `selection_changed` (L:310-313) -> held defect again (L:314-316). All non-durable, before any write.
3. L:333-335 contextvars set; B:1672 `_require_reaper_alive`; B:1673 time.
4. B:1674-1680 decision identity/authorized/effect identity [`PermissionError`, no row].
5. B:1685 `_resolve` -> L:263 -> B:2055: if a profile is set, B:2063 check lease, B:2093-2143 write `check_events` (opened, one per input, completed) [durable journaling]; `_resolve_inputs`: manifest mismatches B:2266 (`manifest_digest_mismatch` B:2618-2619, `adapter_mismatch`, `target_out_of_scope`...), authority context B:2267, tenant B:2277-2282, `authority_domain_mismatch` B:2297-2298, role mapping, identity B:2342-2353, mandate B:2355-2367, grant B:2369-2400, requirement/grant scope, conflict, policy, approvals B:2477-2514, evidence B:2516-2557, `validate_extensions` B:2560-2566 (`runtime_authority_approval_mismatch`, runtime_authority.py:332-335), `return sorted(reasons), None` B:2567-2568. ANY reason ends here; ECB not consulted (L:267).
6. L:269-285 ECB mint/classify/stamp (reachable only with zero base reasons).
7. B:1687-1688 `_operation_gate` (identity profile only); B:1689 `_record_check` (one `ResolutionCheck` row + `input_time_floors`; may add `input_observation_time_regressed`, B:647-648, which then masks the ECB code).
8. B:1690 `reasons or current is None or current != persisted.binding` -> B:1691-1693 `refusal_reasons` = base reasons, or `["authorization_binding_changed"]` iff none -> B:1694-1710 durable `EffectTimeRefusal` -> B:1711 `PermissionError("authorization-critical inputs changed before effect")`.
After: B:1712-1716 capability checks; B:1717 adapter substitution; B:1721-1730 prior attempts / `_observe_and_reconcile`; B:1731-1767 reconcile-existing branches; B:1769-1780 first attempt row; B:1782-1789 expired-before-dispatch gate; L:318-324 `_gl_commit_gate` inside `_GatedDestination.apply` (L:109-111) re-verifies Registry sources; B:1794 `destination.apply`.

### 2.4 ECB reachable? FACT: yes at step 6/8, only with zero base reasons and zero `_record_check` additions.
### 2.5 Refusal semantics (record 06 sec.5 row EXECUTE; 11 sec.2A): durable `EffectTimeRefusal` `authorization_binding_changed`, `PermissionError`, no attempt, destination untouched. Matches B:1690-1711 (FACT). Frozen doc 03 expectation 1 literal ("execute AND pin-export ... durable EffectTimeRefusal") is satisfied for execute. Guard-first outcomes are different evidence: a durable `EffectTimeRefusal` carrying the BASE reasons (e.g. hub A-main4 line 883 `[authority_domain_mismatch, manifest_digest_mismatch...]`) or, for step 1-2 guards, no durable row at all.

---------------------------------------------------------------------------------------------------------------------------------
## 3. Interface B - read-only pin-export (P:91-235)

### 3.1 Supported families and the F4-only limit (the key question)
FACT - where pin-export refuses/declines profile-bearing families (two layers):
* Layer 1, construction (never reaches pin-export): `policy_binding_unsupported` in `GovernedPolicyWorkflow` when any of six profile-bearing slots is declared AND the host profile carries `policy_binding` (G:333-334); in `GovernedClassAgeWorkflow` (:206-207) and `GovernedClassUnreadableWorkflow` (:263-264) for any `policy_binding` profile. F4 dedicated refuses every profile (f4:110-111).
* Layer 2, inside pin-export: `PermissionError` when the workflow has no profile (P:117-119) or no valid `policy_binding/0.1` approval side (P:120-122). Every workflow of Layer 1 therefore either cannot be built with a policy-binding side or has none, and cannot be assessed. The withdrawn disposition returns a terminal status BEFORE `_resolve` (P:134-140, 159-165): ECB not evaluated on that branch.
* Net pin-export-capable set (INFERENCE from G:323-334; only the F4 subset is tested): `GovernedPolicyWorkflow` with a profile that has `policy_binding` and ONLY non-profile slots: `f4_ages`, `observation_max_age`, `observation_clock_tolerance`. The statement "Pin-export supports the F4 family declaration only" (record 12 item 4; hub verdict) is therefore narrower than the code: observation families are not in the six-slot `profile_families` list (G:323-324). UNVERIFIED by any test (`tests/d06_support.py:97` declares `T.families(f=...)` only).

Is the limit a CONTRACT exclusion? FACT, searched:
* Registry contract text that would exclude it: none found. `policy_binding_unsupported` appears in Registry only in annexes A/B/C, mutation harnesses and F3-B expectation 8 (03:44, "unchanged"); never in a contract (`r08-v*`/Amendment 4: no family restriction on the export; Amendment 4 line 94 requires re-resolution and issuance validation only). Record 02 sec.4 rule 2 says "Execute and pin-export claim recompute the live member and compare" for every governed workflow, with no family qualifier.
* Annex B sec.2 (design record, Registry): "Stated reason: a fail-closed deferral, not a technical incompatibility." Annex A line 28: "the generation binding and this binding never co-exist today" (descriptive).
* CP module docstring G:39 ("a profile carrying `policy_binding` is refused for the profile-bearing families") and `tests/d06_support.py:89` comment ("F4 is the one family that reaches the pin export") are implementation/documentation helpers. They are NOT contract text.
* Record 12 item 4 is a closeout DISPOSITION (class C for "members unreachable by pin-export", class A for "F4-reachable members"), basis "Developer test helper documents that profile-bearing families are refused". It is not a frozen contract and itself keeps F4-reachable members in class A.
Conclusion (FACT + INFERENCE): the exclusion of profile-bearing families from pin-export is an implementation limit plus a record-12 scope disposition, not a contract exclusion. It must not be used as an UNREACHABLE-BY-CONTRACT reason.

### 3.2 Entry conditions (FACT)
tz-aware `now` (P:102-103); host binding deep-copied (P:104); decision equals persisted, authorized, tenant-bound (P:107-115); profile and valid approval side (P:117-122); valid canonical host binding (P:123-124); persisted extension has `catalogue_digest`, `approval_commitment`, `policy_generation` of exact types (P:125-132); resolver handoff/snapshot callables (P:151-155).

### 3.3 Guard order
Before the ECB comparison: P:134-149 non-withdrawn: activation/epoch match (P:142-143); side `selected` and `binding_digest` match (P:144-145); **`commitment(profile.model_dump) != persisted_catalogue` -> PermissionError "configured profile differs ..." (P:146-147)**; activation/generation match (P:148-149). Then P:157-158 handoff lock; P:167-175 `_resolve(stage="claim", decision=persisted)` (same steps as 2.3 item 5-6, journaling `check_events`), `_binding_issuance_reasons` (C:182-209), `_record_check` (ResolutionCheck stage `claim`). `except PermissionError: raise` (P:176-177) - note `RegistrySelectionRefused` IS a `PermissionError` (L:65), so `configuration_binding_invalid` propagates as an exception; any other exception -> `_unknown("authority source unreadable")` (P:178-179).
Comparison: P:181 `reasons or current is None or current != current_binding` -> `_classify` (P:71-88) -> terminal only if EVERY reason maps; otherwise `_unknown(... "authority not supported but not positively terminal: " + reasons or "binding changed")` (P:186-188). An ECB-only mismatch has no reasons, so the text is "binding changed" (hub G1 row 56).
After (active path only): snapshot read P:191-196; `_validate_issuance_snapshot` P:197; **host-binding scope vs persisted tenant/institution/authority_domain P:198-201 (this is NOT the ECB member; it compares the installer-owned body)**; approval commitment recomputation P:202/247-248; validity interval P:204-212; payload P:214-235.
### 3.4 ECB reachable? FACT: yes (P:181) once P:146-149 pass and the base resolves clean. Not reachable on the withdrawn branch.
### 3.5 Semantics: record 06/11 scope B: state `unknown`, payload `None`, reason text, no `EffectTimeRefusal`, no attempt, no authorization-state write; existing `check_events` + one stage-claim `ResolutionCheck` + floors are written (record 11 sec.8; hub G1 rows 52, 58, 60). Frozen doc 03 expectation 1 literal (durable `EffectTimeRefusal`, code named) is NOT met; the successor interpretation (scope B, confirmed by record 11 sec.2/3, prospective, "no human adoption step recorded", record 11 sec.7) is the applicable text. Original F3-A FAIL stands (record 06 sec.7, 11 sec.4, 14 sec.1).

---------------------------------------------------------------------------------------------------------------------------------
## 4. Interface C - claim issuance (C:404-567; `materialize_*` C:570-598; `provision_*` C:601-634)

### 4.1 Families
FACT: not family-limited. Any workflow with a handoff-capable resolver (C:432-436). Governed ones reach the ECB through the same `_resolve`; a plain workflow has no ECB. Passing `policy_binding`/`expected_*` (C:450) additionally needs a selected `policy_binding` side (C:199-202), i.e. only the pin-export-capable subset; WITHOUT those arguments the profile-bearing families (F5 class age, unreadable, composition with profile slots) can issue claims. Tested only on the F4+policy_binding "pin" fixture (hub G2, D-2 Q5).
Two ECB code paths (FACT, C:442-447):
* journal mode (profile set): `_resolve(stage="claim", decision=decision)`; classification incl. `legacy`.
* non-journal mode (no profile: F4 dedicated, F4-only composition without profile): `_resolve` with default `stage="decision"` and no decision; `_EXEC_DECISION` is None outside `execute` (L:35, 269) so L:273-274 takes the MINT branch and the comparison is plain `current != decision.binding` with NO classification (INFERENCE from source; D-2 states this branch "unexercised"). Consequences (INFERENCE): a legacy (member-less) decision below `legacy_cutoff` is refused at claim in this mode (contract rule 2 says legacy classification applies); Python-equal malformed members (60.0 vs 60) are not caught by the L:283 guard in this mode. Fail-closed in the first case; harmless for the three string/digest members.
### 4.2 Entry: decision persisted+authorized (C:426-430), handoff callables (C:432-436), `provision` callable checked first (C:625-626).
### 4.3 Guard order
Before: C:420-421 tz; C:423 binding copy; C:426-430; C:432-436; C:439 handoff lock; C:443-447 `_resolve` (journaling); C:448-453 `_binding_issuance_reasons` if any binding argument; C:454 `_record_check` stage `claim`. Comparison: C:455 `reasons or current is None or current != decision.binding`; C:456-458 raise `PermissionError("policy binding refused at claim issuance: ...")` only if the ONLY reasons are binding reasons and `current == decision.binding`, otherwise `"authorization-critical inputs changed before claim issuance"`. ECB mismatch -> the generic message (FACT, since `current != decision.binding`).
After: C:460-462 snapshot; C:464-466 `_validate_issuance_snapshot`; C:467-470 policy-binding scope (institution, authority_domain of the host body vs institution; NOT the ECB member); C:484-485 validity interval; C:506-559 claim construction/validation; C:565-566 `provision(claim)`.
### 4.4 ECB reachable? FACT: yes at C:455. ### 4.5 Semantics (record 06 scope C, 11 scope C): `PermissionError`, no claim, no `provision` call, no `EffectTimeRefusal`, existing journaling unchanged (hub G2 rows 306-311; D-2 Q5 P1-P5).

---------------------------------------------------------------------------------------------------------------------------------
## 5. Required durable vs read-only evidence (per record 06 sec.5 as clarified by 11 sec.8)
| | Execute | Pin-export | Claim |
|---|---|---|---|
| Durable `EffectTimeRefusal` | REQUIRED (`authorization_binding_changed`, only when no other reason) | not required, not written | not required, not written |
| `check_events` + `ResolutionCheck`(stage) + floors | written before the compare (stage `effect`) | written (stage `claim`) | written (stage `claim`) |
| Attempt / observation / decision / claim row | none | none | none (no claim, no provision) |
| Machine-readable code | in refusal row | not required | not required |
| Outcome | `PermissionError` | `{"state":"unknown","payload":None,...}` | `PermissionError` |
`configuration_binding_invalid` (live config unbindable) on any path: exception raised from `_resolve` AFTER `check_events` were written but BEFORE `_record_check` (INFERENCE from L:276-277 vs B:2069-2144): no `ResolutionCheck` row, no refusal row. Record 11 sec.8 lists this branch as unverified.

---------------------------------------------------------------------------------------------------------------------------------
## 6. APPLICABILITY MATRIX
Reference subject: the pin-export-capable fixture (composition, F4 declared, host profile with `policy_binding`, `tests/d06_support.py:88-97`). "Live" = rebuild the workflow so the live member differs; "persisted" = rewrite/reseal the stored member (unsigned store; store-write capability, a documented limit). Cell text: class; then the fields.

### 6.1 scope.authority_domain
| Field | Execute | Pin-export | Claim |
|---|---|---|---|
| Class | **JOINT-ONLY** live (plain change is **GUARD-FIRST**); **REACHABLE** by persisted edit or graft | **JOINT-ONLY/GUARD-FIRST** live; **REACHABLE** persisted | same as pin-export, and not F4-limited (UNVERIFIED beyond the pin fixture) |
| Frozen source | member = `authority[1]` from the manifest (L:81-89, 199-206; E:130-132); mismatch at B:1690 | P:181 | C:455 |
| Registry family | every declared family binds the domain via `ExpectedContext(... authority_domain ...)` (f4:76); here F4 `f4-control-plane-age-bounds` r08-v2 | same | same |
| Required authority | host manifest + resolver context + a Registry selection signed for the new domain; ECB confers none (02 sec.4 rule 3) | + installer-owned host binding (P:198-201 compares its own scope field AFTER the ECB) | + sink |
| State transition | authorized decision(domain X) -> execute under workflow(domain Y) -> refusal row; no attempt | none persisted but journaling | none persisted but journaling |
| Changed commitments | ECB digest + leaf, PLUS base `manifest_digest`, `proposal_commitment` (D-1 Q2-A1 diff) | same | same |
| Earliest refusing guard | construction needs the new manifest and a re-signed selection; then `manifest_digest_mismatch` B:2618-2619 / `authority_domain_mismatch` B:2297-2298 -> ECB never consulted (L:267). Rebuilt proposal removes the first, yielding JOINT | base reasons -> `_unknown` (P:186-188), ECB not consulted | base reasons -> generic PermissionError |
| ECB reachable | only JOINT (rebuilt proposal) or persisted/graft | same | same |
| Existing evidence | original A19 execute lines 572-577 PASS (persisted reseal); A25(a) line 883 UNREACHABLE-ISOLATED; D-1 Q2-A1/A2/A3: natural isolation structurally impossible, **MET ONLY BY GRAFT** (F4 dedicated, execute), M06 killed | A19 pin lines 578-584 (state unknown, no row, FAIL under 03 literal); G1 lines 50-61 (successor scope B 8/8 checks pass) | G2 lines 304-312; D-2 Q5 P2 (persisted-side) |
| Missing evidence | none obtainable for natural isolation (impossible by construction) | graft and rebuilt-proposal (JOINT) on the pin fixture NOT run | graft/JOINT NOT run; non-pin families UNVERIFIED |
| Confidence | high (static chain + D-1) | medium-high | medium |

### 6.2 host_profile_digest
| Field | Execute | Pin-export | Claim |
|---|---|---|---|
| Class | **REACHABLE** (natural, isolated) in a profile-bearing family via masked-host edit; in the pin-style fixture **GUARD-FIRST/JOINT** (host == held == catalogue); persisted edit REACHABLE | live: **GUARD-FIRST** (profile-bearing families cannot carry `policy_binding`, so hd==ed==catalogue always); persisted: **REACHABLE**. NOT contract-excluded | **REACHABLE** (natural masked-host route applies because claim needs no `policy_binding`) - INFERENCE, UNVERIFIED |
| Frozen source | G:476-486 / f5:260 / unreadable:336; null in F4 dedicated (f4:158) | P:181; but any live profile change hits P:146-147 first | C:455 |
| Registry family | class-age r08-v2 (D-1 H1), unreadable r08-v5; revocation r08-v6, irreversible r08-v7, anchor r08-v8 compose over host; F4 alone: none (host unchanged) | F4 r08-v2 (+ observation r08-v8 by code, untested): no profile family | any |
| Required authority | host profile (trusted config) + Registry narrowing | host profile with `policy_binding` side | host profile |
| State transition | decision under host H1/Registry R -> rebuilt under H2 whose FINAL profile equals (masked) -> refusal | `unknown` | PermissionError |
| Changed commitments | D-1 Q3-H1: ECB diff exactly `{digest, host_profile_digest}`, base diff empty, catalogue_digest and approval_commitment equal | live change moves host, effective, catalogue_digest, approval_commitment, `binding_digest` together | as execute |
| Earliest refusing guard | none before ECB in the masked route (held-state `profile_modified` f5:249-252 not tripped); in pin-style: approval `runtime_authority_approval_mismatch` | P:146-147 (PermissionError) | none in masked route |
| ECB reachable | yes | yes (persisted); live no | yes (inferred) |
| Existing evidence | A19 execute lines 585-590 (persisted); D-1 Q3-H1 MET + mutant D1-M14 killed; test_c06 (developer) | A19 pin lines 591-597; G1 lines 62-73; G5a content (digest == catalogue in pin fixture) | G2 lines 313-321; D-2 Q5 P4 |
| Missing evidence | composition/unreadable/freshness-extension variants (D-1 declares not covered) | none obtainable for live isolation in a pin-capable workflow | masked-host route on claim not run |
| Confidence | high | high on structure; medium on "no other pin-capable live route" | medium-low |

### 6.3 effective_profile_digest
| Field | Execute | Pin-export | Claim |
|---|---|---|---|
| Class | **GUARD-FIRST** (approval mismatch) / **JOINT** (approvals re-issued); persisted REACHABLE | live **GUARD-FIRST**; persisted **REACHABLE** | **GUARD-FIRST/JOINT**; persisted REACHABLE |
| Frozen source | `profile_digest(held)` == persisted `catalogue_digest` by the same formula (f5:130-132; runtime_authority.py:475) | P:146-147 (catalogue) then P:247-248 (approval commitment); P:181 | C:455 |
| Registry family | profile-bearing families change it; pin-capable set: it equals host digest | same | any |
| Required authority | issuer re-binds approvals to the new profile (host duty) | same | same |
| State transition | decision(profile A) -> execute under profile B | `unknown`/PermissionError | PermissionError |
| Changed commitments | D-1 Q3-E2: base {approval_commitment, catalogue_digest} + ECB {digest, effective_profile_digest, families.0.effective_policy_digest} | all of those + host digest | as execute |
| Earliest refusing guard | `runtime_authority_approval_mismatch` (validate_extensions, runtime_authority.py:332-335) | P:146-147 raises PermissionError (NOT `unknown`) before `_resolve` | approval mismatch via `_resolve` |
| ECB reachable | JOINT only | persisted only | JOINT only |
| Existing evidence | A19 execute lines 598-603; A25(e) line 901 UNREACHABLE-ISOLATED (reasons `[runtime_authority_approval_mismatch]`); D-1 Q3-E1/E2/H2 **DECOMPOSED-ONLY** | A19 pin lines 604-610; G1 lines 74-85 | G2 lines 322-330; D-2 Q5 P5 |
| Missing evidence | a mutant dropping this member is outcome-equivalent by natural routes (D-1) - not killable end-to-end | live PermissionError at P:146-147 not exercised as a case (INFERENCE from source) | - |
| Confidence | high | high | medium |

No cell is UNREACHABLE-BY-CONTRACT. Structural non-reachability found is implementation-only: (a) F4 dedicated has constant-null host/effective members and cannot be pin-exported (f4:110-111; P:117-119); (b) profile-bearing families cannot be pin-exported (G:333-334 etc.). Neither is NOT APPLICABLE under the lead's rule (no contract reason).

---------------------------------------------------------------------------------------------------------------------------------
## 7. Other ECB leaves reachable by pin-export (only as needed to check the fixture; not an expansion)
FACT: all 22 persisted leaves were perturbed on pin-export in the original harness (A19, `MEMBER_LEAVES` post-AMEND4 line 372-387) and in G1. Live-reachable in the pin fixture without a profile family (g02 `tests/test_effective_configuration_binding.py:545`, INFERENCE for the rest): the three other scalars `identity/mandate_max_age_seconds`, `clock_tolerance_seconds`; `observation_policy` values and null; `f4_scalars` via host value (F4 declared, so Registry min applies); the single `families.0` (f4_ages) row by FAMILY_TABLE/SCHEMA_REVISIONS patch. Persisted-only on pin-export: `families=none_declared`, `families=extra_class_age_declared` (class_age cannot be declared with `policy_binding`).

---------------------------------------------------------------------------------------------------------------------------------
## 8. Where this matrix could disagree with workers analysing individual members
1. host_profile_digest: a member worker citing D-1 H1 will say "REACHABLE/MET". True for execute (and inferred claim), FALSE for pin-export live (cell is GUARD-FIRST; persisted REACHABLE only).
2. authority_domain: a member worker citing A19 will say REACHABLE; D-1 says "MET ONLY BY GRAFT"; this matrix says natural = JOINT-ONLY. All consistent if the label states which perturbation side; label sets differ ("DECOMPOSED-ONLY"/"GRAFT" vs the lead's five).
3. effective_profile_digest: D-1 "DECOMPOSED-ONLY" = my GUARD-FIRST/JOINT; a worker may add "pin-export UNKNOWN"; I show the live pin-export path raises PermissionError at P:146 rather than returning `unknown`.
4. Claim vs pin-export: a worker may copy pin-export limits onto claim. Claim is not F4-limited and has a distinct non-journal path.
5. Pin-export "F4 only": a worker may treat it as a contract limit; sources say fail-closed deferral (annex B sec.2). Another may widen to observation families; untested.

---------------------------------------------------------------------------------------------------------------------------------
## 9. CONTRADICTIONS preserved (docs vs docs/code)
* C1 (code vs CP doc) `docs/effective-configuration-binding.md:127` says a malformed LIVE configuration makes "the pin export report `unknown`"; source: `RegistryGovernedPolicyRefused` (G:68-73) subclasses `PermissionError` (L:65), P:176-177 re-raises PermissionError, so it propagates as an exception, not `unknown`. INFERENCE (no test: only `test_a05c` for execute/decide at lines 132-142 and `test_d09`).
* C2 (record 12 item 1 vs structure) asks for "decision under domain X, live side rebuilt under domain Y, all else equal". The domain comes from the manifest whose digest is in the proposal and base binding (B:2618-2619, L:81-89), so "all else equal" is unsatisfiable on any live route (D-1 Q2-A2). Record 13 decision 3 repeats the open question.
* C3 (record 12 item 4 vs code) "F4 family declaration only" vs G:323-334 (observation slots allowed with `policy_binding`).
* C4 (frozen 03 expectation 1 literal vs 02 sec.4 rule 2 vs successor 06): known; 06 sec.5 resolves for pin-export/claim prospectively; confirmation is recorded only in 11, with human adoption "PENDING" (11 sec.7; 13 level 4-6).
* C5 (02 rule 2 vs code) rule 2 says claim recomputes with legacy classification; non-journal claim does plain equality (INFERENCE, L:273-274).
* C6 (record 06 sec.5 "one ResolutionCheck row" vs observed 13 `check_events`): already clarified by 11 sec.8; my reading of B:2093-2143 agrees.
* C7 (record 12 item 2) "Two independent fixtures needed" for host/effective digests, stated for the acceptance boundary without limiting to execute; the host-only fixture cannot exist in a pin-capable workflow.

---------------------------------------------------------------------------------------------------------------------------------
## 10. TOP FINDINGS
1. None of the three members is excluded by contract from any interface. All three reach the ECB comparison on execute, pin-export and claim by persisted-side perturbation in the pin fixture (A19 lines 572-610, G1 lines 50-85, G2 lines 304-330, D-2 Q5 P2/P4/P5). Do not mark any as out of scope.
2. The F4-only pin-export limit is an implementation limit (`policy_binding_unsupported` + pin-export's `policy_binding` requirement), explicitly a "fail-closed deferral" in annex B sec.2. The only text that declares it a scope limit is record 12 item 4, which keeps F4-reachable members in class A.
3. Live isolation of authority_domain is impossible without a graft on every interface (JOINT-ONLY at best); D-1 proved the graft on execute only; pin-export and claim grafts are unrun but feasible with the pin fixture (INFERENCE).
4. host_profile_digest has a natural isolated route only in profile-bearing families, therefore execute (proved) and claim (inferred), never pin-export. Pin-export coverage of this member can be at most persisted-side. This is an implementation consequence, so it should be stated as a declared route limit, not a contract exclusion and not a failure.
5. effective_profile_digest is redundant with catalogue_digest and guarded first by approval (execute/claim) or P:146-147 (pin-export); JOINT at best; D-1 DECOMPOSED-ONLY stands.
6. Documentation defects: C1 above; non-journal claim legacy behavior undocumented.

## 11. UNVERIFIED / uncertainties
* Nothing run: all behavior statements are source reading plus cited hub rows. Hub D-1/D-2 are on unmerged remote branches; custody not established (record 14 sec.5/6).
* Claim x host_profile_digest natural route; claim on F5/unreadable/composition-with-profile families; claim non-journal branch; pin-export with observation families; pin-export graft; `configuration_binding_invalid` row counts; withdrawn-branch ECB bypass relevance.
* Hub row numbers are 1-indexed lines of `A-main4/f3a_evidence.jsonl` and `raw/739efe7/readj_evidence.jsonl` as I counted them; the handoff's "rows 526-805" numbering differs from mine (A19 pin rows start at line 578 for authority_domain); treat the case/check names as authoritative.
* Whether the Architect treats record 12 item 4 as a binding scope limit for the verdict is a decision, not a source fact; `11` confirms interpretation A/B/C only.
