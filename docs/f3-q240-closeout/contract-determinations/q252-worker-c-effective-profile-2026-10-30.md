# WORKER C (static, read-only) - OCS-F3-Q252-FEASIBILITY: can `effective_profile_digest` (A25(e)) be isolated on the live side?

Status: static source reading only. Same session lineage as the lead builder: NOT independent. Nothing was run (no pytest, no product import, no mutants); nothing modified except this file. Not an acceptance claim. Nothing here is adopted; section 9 is prospective wording only.

Sources read: CP frozen subject `739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69` (via `git show`; file:line refer to that tree); Registry `origin/main` docs `02,03,06,11,12,13,14` under `docs/family-migration/final-three/`; Registry pin `a40fe755` (`registry_successor/v2_policy_identity.py::effective_policy_digest`); hub `1c9b7197` `docs/f3-q240-closeout/07-f3-architectural-technical-disposition-2026-10-30.md`, `results/third-party/cp-739efe7-f3-q2q3-isolation-20261030/` (verdict.md, REVIEW-ADDENDUM.md, review/adversarial-review-D1.md), `cp-739efe7-f3a-readjudication-20261030/verdict.md`, `cp-739efe7-f3-q4q5q6-20261030/verdict.md`.

---------------------------------------------------------------------------------------------------------------------------------
## 0. Answer in five lines
1. STRICT live-side isolation (ECB `effective_profile_digest` differs, while `approval_commitment`, `catalogue_digest`, `host_profile_digest`, `families.*.effective_policy_digest`, scope, scalars, observation_policy stay equal) is IMPOSSIBLE BY CONTRACT for every profile-bearing workflow, and the F4-dedicated live value is a constant `null`. The impossibility is a derivation consequence of `02` section 4 line 48 ("`effective_profile_digest` (equals `catalogue_digest` for profile-bearing workflows, else null)") plus the code, not an inference from failed tests.
2. The equality is enforced BY CONSTRUCTION (one object, one function, one `_resolve` call), NOT by an assertion or guard. No code compares ECB `effective_profile_digest` with `catalogue_digest` at runtime (grep of `catalogue_digest` in `src/` at 739efe7: only `runtime_authority.py:475` produces it, `authorization_pin_export.py:128,147` consumes it; nothing in `effective_configuration_binding.py` or the lifecycle).
3. The narrowest live-reachable state is a JOINT one. Already observed: Q3-E2 (base diff `{approval_commitment, catalogue_digest}`, ECB diff `{digest, effective_profile_digest, families.0.effective_policy_digest}`). By source reading there is a NARROWER joint (freshness-extension route, section 6) that removes the `families.*` leaf from the ECB diff. It is NOT YET DEMONSTRATED and still joint with the base pair, so it does not meet the isolation rule.
4. Pin-export: BLOCKED BY AN EARLIER GUARD with exact lines (`authorization_pin_export.py:147` raises before `_resolve` at `:170`), and profile-bearing governed workflows cannot even be built with the `policy_binding` pin-export requires. Claim: JOINT-ONLY / GUARD-FIRST, same as execute.
5. A legitimate decomposed proof remains available (persisted-side comparison sensitivity A19/G1/G2/P5 + component derivation H2/G5a + guard order E1 + joint end-to-end E2). Whether record 12 item 2 accepts it is an Architect decision; section 9 lists the minimum prospective clarification.

---------------------------------------------------------------------------------------------------------------------------------
## 1. FACTS (each with source)

### 1.1 Contract
- F-C1. `02` section 4 line 48: Digest members include "`effective_profile_digest` (equals `catalogue_digest` for profile-bearing workflows, else null)". `02` section 4 rule 6: "`approval_commitment`, `catalogue_digest`, `RuntimeAuthorityProfile` ... unchanged." CP `docs/effective-configuration-binding.md:34`: "digest of the FINAL held profile (equals `catalogue_digest`), or null for a workflow with no profile"; table at `:57` lists F4 null/null, class age / unreadable / joint host-profile and held profile.
- F-C2. `03` line 23 (F3-A expectation 1): every member "perturbed independently (... host profile digest, effective profile digest ...) changes the digest and makes execute AND pin-export refuse ...". Interpreted for pin-export/claim by `06` section 3/5 and `11`: execute -> durable `EffectTimeRefusal` `authorization_binding_changed`; pin-export -> not `active`/`unknown`, payload None, NO refusal row, one stage-claim `ResolutionCheck` (per D2); claim -> `PermissionError("authorization-critical inputs changed before claim issuance")`, no refusal row.
- F-C3. `12` item 2: Class A. "Named in `03` expectation 1. Developer tests `test_c06` (host only) and `test_c07` (effective only) isolate each; they are developer evidence. ... Two independent fixtures needed; state the masked-host limit alongside." Hub `07` section 0: record 12 controls; Q3 OPEN; section 7(3)(c): "an independent fixture isolating it, or a documented unresolved qualification constraint if it cannot be isolated from `catalogue_digest` by construction (`02` section 4)". Note: `12` itself contains no clause for "cannot be isolated"; that fallback appears only in the hub's own missing-requirements list (`07` section 7(3)(c)) and in the Q2 wording of `12` item 1 ("If not isolable, status is 'not independently demonstrated for this member'").
- F-C4. `12` item 2's own cited developer fixture `test_c07` (CP `tests/test_effective_configuration_binding.py:255-261`) changes the final profile via a different Registry selection (`amat({T1: 30})`) and calls `T.bind_approval(res, other.runtime_authority_profile)`: i.e. it is the JOINT construction (approval follows), not an isolation.

### 1.2 Derivation code (all at 739efe7)
- F-D1 (live ECB value, profile-bearing): `registry_f5_class_age_governance.py:255-260` `effective_profile_digest=profile_digest(held)`, `held = self.runtime_authority_profile`; `registry_f5_class_unreadable_governance.py:330-336` same; `registry_governed_policy.py:476-486` `ed = agemod.profile_digest(held) if held is not None else None`. `profile_digest(p) = commitment(p.model_dump(mode="json"))` (`registry_f5_class_age_governance.py:130-132`).
- F-D2 (base `catalogue_digest`): `runtime_authority.py:473-475` `"catalogue_digest": commitment(profile.model_dump(mode="json"))` inside `validate_extensions`, called at `bounded.py:2560-2563` with `self.runtime_authority_profile` (the very attribute F-D1 reads).
- F-D3 (approval commitment): `runtime_authority.py:236-242` preimage includes `"profile": profile.model_dump(mode="json")`; checked live at `:332-335` (`runtime_authority_approval_mismatch` if the approval input's `runtime_authority_commitment` != expected).
- F-D4 (mint): `registry_governed_lifecycle.py:263-274` `GovernedLifecycle._resolve` runs `super()._resolve` first (which computes F-D2), then `_gl_configuration_members()` (F-D1) in the SAME call, and mints on `stage == "decision"`.
- F-D5 (no profile): F4 dedicated refuses any `runtime_authority_profile` (`registry_f4_age_governance.py:110-111`, `runtime_authority_profile_unsupported`) and hard-codes `effective_profile_digest=None` (`:158`); composed with `runtime_authority_profile=None` has `held None` -> `ed None` (`registry_governed_policy.py:483`). Base: `bounded.py:2560` `if self.runtime_authority_profile:` false -> no `catalogue_digest`.
- F-D6 (composed, no profile-bearing family): `registry_governed_policy.py:287` `pdigest = profile_digest(base) if (base is not None and (age_part or unreadable or assurance or irreversible or anchor or terminal)) else None`; with only F4 / observation families and a host profile, `base = host`, `pdigest = None`, held = host, so ECB `host_profile_digest == effective_profile_digest == catalogue_digest` (same content), and the held-state profile check is SKIPPED (`:503` `if b["effective_profile_digest"] is not None`). A host `policy_binding` is allowed only in this configuration (`:333-334`).
- F-D7 (composition inputs): every compose function is pure in (host, effective values): `compose_unreadable` (`registry_f5_class_unreadable_governance.py:146-151`), `compose_assurance` (`registry_revocation_governance.py:122-129`), `compose_terminal` (`:132-138`), `compose_irreversible` (`registry_irreversibility_governance.py:113-120`), `compose_anchor` (`registry_final3_governance.py:105-114`). EXCEPTION: `compose_profile(host, effective, registry)` (`registry_f5_class_age_governance.py:117-127`) also reads the RAW Registry class map `registry` for the outage-extension limit: `room = min(max(0, registry[cid] - effective[cid]) ...)`, `freshness["max_age_extension_seconds"] = min(host_limit, room)`.
- F-D8 (family digest content): `registry_f5_class_age_governance.py:181` `identity.effective_policy_digest(FAMILY, {FIELD: dict(effective)})`; Registry `v2_policy_identity.preimage_from_inputs` takes `{family, contract_version, effective}` only. The family digest does NOT cover the raw Registry map. `family_rows` (`effective_configuration_binding.py:128-146`) takes only `part[1]` per slot, so the age-only intermediate `age_pdigest` (`bound[2]` / `identity["class_age"]["effective_profile_digest"]`) is NOT an ECB member.
- F-D9 (acceptance of Registry value above host): CP `tests/test_f5_class_age_governance.py:643-647` (test_x02): "host 60, Registry 90: room 30 -> `freshness.max_age_extension_seconds == 30`"; `:650-655` (test_x03) rooms 10 and 30 -> 10. Developer evidence that a Registry value above the host is accepted and yields effective == host. Also `derive_effective` enforces only `effective[k] == min(host[k], registry[k])` (`:171`).

### 1.3 Guard order (execute)
Order, in code: (G-a) `GovernedLifecycle.execute` -> `_gl_revalidate` -> `_gl_reverify` (`registry_governed_lifecycle.py:297-316,330-332`): `_gl_held_defect` (dedicated: `profile_modified` vs `_gl_bound`, class age `:249-253`, unreadable `:324-328`; composed `:488-506`, profile check only when `b["effective_profile_digest"] is not None`), manifest authority, source read + `_gl_derive`, `selection_changed` if `new_bound != self._gl_bound`, held-state again; (G-b) persisted decision identity checks `bounded.py:1676-1680`; (G-c) base `_resolve` (all base reasons incl. `runtime_authority_approval_mismatch` `runtime_authority.py:332-335`; returns reasons unchanged `registry_governed_lifecycle.py:267-268`); (G-d) ECB classify/stamp `:269-285` (a non-ACCEPTED status adds `authorization_binding_changed` only through the equality `stamped.runtime_authority == persisted_ra` guard at `:283`); (G-e) `current != persisted.binding` -> `authorization_binding_changed` + durable `EffectTimeRefusal` (`bounded.py:1690-1711`).
Pin-export: `authorization_pin_export.py:122` requires `profile.policy_binding` (else PermissionError); non-withdrawn `:147` `commitment(profile.model_dump(...)) != persisted_catalogue` -> `PermissionError("configured profile differs from the profile the persisted decision committed to")`; ONLY THEN `workflow._resolve(... stage="claim", decision=persisted)` at `:170`, `current != current_binding` at `:181`. Withdrawn branch returns at `:~158` without calling `_resolve`.
Claim: `local_authority_effect.py:443-466`: `workflow._resolve(frozen, now, stage="claim", decision=decision)`; `current != decision.binding` -> `PermissionError("authorization-critical inputs changed before claim issuance")`. `GovernedLifecycle.execute`/`_gl_revalidate` is NOT on this path (no held-state or selection re-verification before `_resolve`).

### 1.4 Existing evidence rows (as reported in the hub/Registry records; I did not re-verify raw rows)
- Q3-H2 (D-1): persisted `effective_profile_digest` equals harness' own commitment of the held effective profile and equals persisted `catalogue_digest`; differs from host digest on the F5 fixture; BUT "Q3-H2 does not vary this member (both worlds share the same effective profile)" (hub `07` section 6).
- Q3-E1: approval not re-issued -> only `[runtime_authority_approval_mismatch]`; ECB code absent (guard-first).
- Q3-E2: approval re-issued -> `[authorization_binding_changed]`; base diff `{approval_commitment, catalogue_digest}`; ECB diff `{digest, effective_profile_digest, families.0.effective_policy_digest}` (joint). Q3-E2 "does not check the new live value against an independent commitment" (hub `07` section 6).
- A19 (original independent F3-A): execute persisted-side reseal row `[effective_profile_digest]` PASS; G1 (pin-export, successor semantics): 22 members x 2 revisions persisted-side: state `unknown`, payload None, no refusal row, destination untouched; G2 (claim): `PermissionError`, no claim; D-2 Q5 P5: provision/materialize persisted-side `effective_profile_digest` 15 pass on 3.11.18 and 3.12.3. G5a: minted member content on pin fixture (both digests == `catalogue_digest`) and F4 fixture (null); D06-M06 killed there (not an eff mutant).
- Developer: `docs/evidence/d06/mutation-final2/summary.json` marks `drop-effective_profile_digest-from-preimage` KILLED by `tests/test_effective_configuration_binding_unit.py::test_digest_is_the_existing_canonical_commitment_over_domain_version_and_members` (a component test) and `members-use-host-profile-for-effective` KILLED by `test_a02_the_members_are_the_live_configuration` (a component test). Developer evidence only.
- D-1 reviewer F2 (REVIEW-ADDENDUM item 2): a graft does not move the base binding; what defeats a donor-profile graft is `families.0.effective_policy_digest` also differing. The graft was not run.

---------------------------------------------------------------------------------------------------------------------------------
## 2. Does the architecture enforce `effective_profile_digest == catalogue_digest` (or null)?

Per workflow (execute/claim path; pin-export in section 5):

| Workflow (class) | Profile-bearing? | (1) Effective profile construction | (2) catalogue_digest formation | (3) approval commitment | (4) live recomputation | (5) guards in order | (6) ECB comparison position | (7) can a valid live change move ONLY eff in the ECB? |
|---|---|---|---|---|---|---|---|---|
| F4 dedicated `GovernedAgeWorkflow` (family `f4-control-plane-age-bounds` r08-v2) | NO (profile refused `registry_f4_age_governance.py:110-111`) | none | none (no profile -> no extension, `bounded.py:2560`) | none | eff hard-coded `None` (`:158`) | held-state `scalars_modified`, authority, selection | `runtime_authority == {ECB}`; base compare at `bounded.py:1690` | NO and not applicable: live eff is a constant. Only persisted-side forging can differ. |
| Class age `GovernedClassAgeWorkflow` (`f5-action-class-age-bounds` r08-v2) | YES | `compose_profile(host, effective, registry)` at construction (`:117-127,182`) | `runtime_authority.py:475` on `self.runtime_authority_profile` | `runtime_authority.py:236-242` over same profile dump | `profile_digest(held)` `:260` | G-a (`profile_modified` `:252`) -> G-c (approval) -> G-d -> G-e | after all base reasons (`:267`) | NO with base fixed (I1-I4). Joint only. Narrower joint via extension limit (section 6). |
| Class unreadable alone / joint with age (`f5-action-class-unreadable-policy` r08-v5, + class age) | YES | `compose_unreadable`(+`compose_profile`) | same | same | `profile_digest(held)` `:336` | `profile_modified` `:326` -> approval -> ECB | same | NO with base fixed. Alone: profile is a pure function of (host, effective), so any profile change co-moves `host_profile_digest` or `families.*.effective_policy_digest`. Joint: extension route as above. |
| Composed `GovernedPolicyWorkflow`, profile-bearing families (class_age, class_unreadable, class_revocation_assurance r08-v6, terminal_revocation r08-v6, class_irreversible r08-v7, anchor_deadline r08-v8) | YES | `derive_policy` pipeline (`:187-290`); `pdigest` non-None | same | same | `profile_digest(held)` `:482-486` | `profile_modified` (`:503-505`, since pdigest non-None) -> approval -> ECB | same | NO with base fixed. All composes except `compose_profile` are pure in (host, effective); `compose_profile` adds the raw-registry dependency. |
| Composed, non-profile families only (f4_ages, observation_max_age, observation_clock_tolerance) WITH host profile | YES (profile present) but not Registry-composed | `base = host` | same | same | `profile_digest(held)`; `host_profile_digest` == eff == catalogue (identical content) | held-state profile check SKIPPED (pdigest None, `:503`); approval guard then ECB | same | NO as a host-vs-eff separation: any host change moves host digest AND eff. Eff moves alone in the ECB only under an attribute edit of `workflow.runtime_authority_profile` (unsupported; still co-moves `catalogue_digest` and `approval_commitment`). |
| Composed, non-profile families only, NO profile | NO | none | none | none | eff `None` constant (`:483`) | scalars / observation guards | ECB only | NO and not applicable (constant null). |

Conclusion: the equality (or null) holds for ALL applicable workflows, BY CONSTRUCTION: (a) both digests are `commitment(P.model_dump(mode="json"))` over the object `self.runtime_authority_profile`; (b) both are read inside the same `_resolve` call (`registry_governed_lifecycle.py:266-274`); (c) there is no runtime assertion of the equality and no separate producer of either value.

---------------------------------------------------------------------------------------------------------------------------------
## 3. Formal invariant argument (strict isolation)

Notation. W is any governed workflow instance; P(W) = `W.runtime_authority_profile`; R a persisted authorized decision minted by a (possibly different) instance W0 with profile P0; L the live evaluation of R by W on the execute path (or the claim path). cat_X, app_X, eff_X denote `catalogue_digest`, `approval_commitment`, ECB `effective_profile_digest`. `H(P) = commitment(P.model_dump(mode="json"))` (deterministic, canonical JSON, collision-resistant).

- I1 (live co-derivation). In any `_resolve` that returns a non-None binding for a W with P(W) not None: cat_L = H(P(W)) [F-D2] and eff_L = H(P(W)) [F-D1]. Hence cat_L = eff_L. If P(W) is None: eff_L = None and no cat_L exists [F-D5].
- I2 (mint co-derivation). R was minted by the same `_resolve` path [F-D4], so cat_R = eff_R = H(P0) (or eff_R = None with no cat_R). Therefore every record minted through the supported lifecycle lies in the set {eff = cat} U {eff = null, cat absent}.
- I3 (approval is profile-injective). app = commitment({profile dump, runtime_authority spec, purpose_ref, grant_expires_at}) [F-D3]. Holding the context fixed, app_L = app_R iff H(P) = H(P0) (modulo collision). So any change of H(P) also changes app.
- I4 (order). Base reasons (including `runtime_authority_approval_mismatch`) precede ECB stamping, which precedes `current != persisted.binding` [F-D4, section 1.3]. The ECB term can therefore decide the outcome only after approval has matched the LIVE profile.
Derivation. Suppose L reaches the comparison and ECB eff_L != eff_R with P(W) not None and P0 not None. By I1,I2: H(P) != H(P0), hence cat_L != cat_R; by I3 app_L != app_R. So the base diff necessarily contains {catalogue_digest, approval_commitment}. If P(W) is None and P0 not None (or vice versa): eff goes null<->digest, and the whole `runtime_authority` extension (cat, app, ...) appears/disappears; again not base-equal.
Therefore: on any live pathway built from supported constructors + the lifecycle's own mint, the state "ECB eff differs, base cat and app equal" is not in the reachable value space. It is reachable only (i) by writing the persisted store (unsigned; the A19/G1/G2/P5 pathway), (ii) by an in-call mutation of P(W) between the two reads inside one `_resolve` (a race outside the supported single-writer model), or (iii) through a defect that breaks I1 or I2 (which is what a regression would be; section 8). Under assumptions A1 (deterministic `commitment`, collision resistance), A2 (no store writes by a non-lifecycle writer; the documented unsigned-store limit), A3 (no concurrent mutation of the workflow object).

Corollary (F4 and no-profile): eff_L = eff_R = null for every live pathway: a live-side eff perturbation is not a state the contract defines (`02` line 48 "else null").

Category of this result: IMPOSSIBLE BY CONTRACT (+ construction), not "failed to demonstrate". It rests on `02` section 4 line 48 (the equality is part of the frozen digest definition) and on F-D1..F-D5. It is NOT a statement that a regression could not break the equality; the contract does not make the equality self-checking.

What the argument does NOT cover (stated, not hidden): it says nothing about the independent members (host digest, families, scope, scalars, observation), nothing about `8616d5f`/main (not read), nothing about concurrency, and it relies on `profile_digest` and `validate_extensions` staying unchanged.

---------------------------------------------------------------------------------------------------------------------------------
## 4. Three categories, kept separate

IMPOSSIBLE BY CONTRACT
- Strict live-side isolation of eff with base `catalogue_digest` and `approval_commitment` fixed (section 3). Contract text: `02` section 4 line 48; `docs/effective-configuration-binding.md:34`.
- Any live-side movement of eff for F4-dedicated and no-profile composed (constant null; `02` line 48 "else null"; F-D5).

NOT YET DEMONSTRATED (reachable by source reading, never run)
- N1. Narrower joint via the outage-extension limit (section 6): ECB diff `{digest, effective_profile_digest}` only, base diff `{approval_commitment, catalogue_digest}`. Not run. Still joint.
- N2. A live-side eff-sensitivity check that is not outcome-equivalent to cat: no end-to-end mutant on eff's live derivation exists (D-1 mutants M06 and M14 are derivation mutants of other members; hub `07` section 6: "No mutant on its live derivation was run").
- N3. Q3-H2 does not vary eff (both worlds share the same effective profile); Q3-E2 does not check the live eff against an independent commitment. A component test that varies the held profile and checks eff == independent commitment was not run in the independent record (developer unit tests only).
- N4. Coverage on composed, class-unreadable (alone and joint), and revocation/irreversibility/anchor workflows: only the F5 class-age fixture and (G5a) the pin/F4 fixtures were exercised.
- N5. Live-side claim/provision with a profile-bearing governed workflow at a profile change (joint) - no row.
- N6. A workflow with the held-state profile check skipped (F-D6) combined with an approval re-issued after an attribute edit: unsupported pathway, not demonstrated and not recommended.

BLOCKED BY AN EARLIER GUARD
- Execute, approval not re-issued: `runtime_authority.py:332-335` -> `[runtime_authority_approval_mismatch]` (Q3-E1), ECB never classified (`registry_governed_lifecycle.py:267-268`).
- Execute, same-instance profile/selection drift: `profile_modified`/`selection_changed` (`registry_governed_lifecycle.py:303-316`; composed profile check only when pdigest non-None, `registry_governed_policy.py:503`).
- Pin-export, any live profile change: `authorization_pin_export.py:147` `PermissionError` before `_resolve` (`:170`).
- Pin-export for profile-bearing governed workflows: they refuse the `policy_binding` that pin-export requires (`registry_f5_class_age_governance.py:207`, `registry_f5_class_unreadable_governance.py:264`, `registry_governed_policy.py:333-334`, vs `authorization_pin_export.py:122`).
- Claim: approval mismatch (same code path `_resolve`).

I do not infer impossibility from E1/E2: E1 is "blocked by an earlier guard", E2 is "joint". The impossibility in section 4 comes from I1-I4.

---------------------------------------------------------------------------------------------------------------------------------
## 5. Classification: effective_profile_digest by leg

Common: member `members.effective_profile_digest` (and digest). Source: `registry_f5_class_age_governance.py:260`, `registry_f5_class_unreadable_governance.py:336`, `registry_governed_policy.py:482-486`, `registry_f4_age_governance.py:158`. Required authority for a live change: host config authority (new host/effective profile) plus the Registry selection authority for any family-composed part, and the approval issuer must re-issue the approval to the new profile (host duty).

### 5.1 EXECUTE
- Classification: JOINT-ONLY (strict isolation: UNREACHABLE-BY-CONTRACT; guard-first variant: GUARD-FIRST). Both E1 (GUARD-FIRST) and E2 (JOINT) observed.
- Applicable Registry family: class age (`f5-action-class-age-bounds`), class unreadable, revocation assurance, terminal revocation, irreversibility, anchor (all profile-bearing). Not applicable to f4_ages, observation_* alone (they do not compose the profile; see F-D6).
- State transition: workflow W0 (profile P0) decides and persists R; W rebuilt with P != P0 (new host profile or new Registry selection), approval re-issued; `execute(R)`.
- Changed commitments (observed, E2): base `{approval_commitment, catalogue_digest}`; ECB `{digest, effective_profile_digest, families.0.effective_policy_digest}`. (By source: with the extension route, ECB `{digest, effective_profile_digest}`.)
- Earliest refusing guard: no re-issue -> `runtime_authority_approval_mismatch` (`runtime_authority.py:332-335`); re-issued -> `authorization_binding_changed` at `bounded.py:1690-1693` (ECB stamped `registry_governed_lifecycle.py:283`).
- ECB reachability: YES after approval matches the live profile; reached in E2.
- Existing evidence: Q3-E1, Q3-E2, Q3-H2 (component), A19 `[effective_profile_digest]` (persisted-side reseal, cited by D-1, not rerun), developer `test_c07`.
- Missing evidence: N1-N4.
- Confidence: HIGH that strict isolation is impossible (I1-I4 are direct reads of 6 short code lines); MEDIUM-HIGH for the extension-route claim (source reading plus developer test x02, never run).

### 5.2 PIN-EXPORT
- Classification: GUARD-FIRST for any live profile change (BLOCKED BY AN EARLIER GUARD, exact lines); the ECB comparison is reachable only after `commitment(profile.model_dump(...)) == persisted_catalogue`, at which point eff_L == cat_L == cat_R == eff_R, so an eff-only live difference is again impossible (I1-I2). Not applicable to the profile-bearing governed workflows as constructed (they cannot hold the required `policy_binding`).
- Applicable family: none profile-bearing. The only pin-export-capable configuration is composed F4/observation-only with a host profile carrying `policy_binding` (F-D6), where host digest == eff == catalogue.
- State transition / changed commitments: rebuilt workflow with a different host profile -> `PermissionError("configured profile differs ...")` (`:147`), a Python exception, NOT state `unknown`.
- Earliest refusing guard: `authorization_pin_export.py:147` (non-withdrawn); withdrawn branch compares activation only and never calls `_resolve`.
- ECB reachability: only when profile unchanged; then eff cannot differ live-side.
- Existing evidence: G1 persisted-side (22 members x 2 revisions; eff row included), G5a content (pin fixture, host == eff == cat).
- Missing: any live-side eff pin-export row; a fixture where host != eff on pin-export (impossible: no profile-bearing family can be pin-exported).
- Per `06` section 5, a pin-export mismatch shows as `unknown`/payload None without a refusal row; that applies to a persisted-side ECB difference only.
- Confidence: HIGH (guard line read; construction refusals read).

### 5.3 CLAIM (provision / materialize)
- Classification: JOINT-ONLY / GUARD-FIRST (same logic as execute; no held-state pre-check on this path). Strict isolation UNREACHABLE-BY-CONTRACT.
- State transition: R persisted; rebuilt W with P != P0; `_resolve(stage="claim", decision=R)` (`local_authority_effect.py:~443-466`); `current != decision.binding` -> `PermissionError("authorization-critical inputs changed before claim issuance")`; no refusal row; one stage-claim `ResolutionCheck`.
- Changed commitments: as execute.
- Earliest refusing guard: approval mismatch when approval not re-issued; else the base/ECB equality.
- Existing evidence: G2 (persisted-side, 22 members), D-2 Q5 P5 (persisted-side, 15 pass, 3.11.18 and 3.12.3); no live-side row.
- Missing: live-side joint claim row (N5); record-12 item 7 `provision_local_execution_claim` is Class B (deferred).
- Confidence: MEDIUM-HIGH (claim path read; no run).

### 5.4 F4-dedicated null/null
- Classification for execute / pin-export / claim: UNREACHABLE-BY-CONTRACT on the live side. Exact contract text: `02` section 4 line 48 "`effective_profile_digest` (equals `catalogue_digest` for profile-bearing workflows, else null)"; code: refusal of any profile `registry_f4_age_governance.py:110-111`, constant `None` at `:158`. Persisted-side perturbation (non-null in a persisted F4 record) is the only route; it is not a live pathway. Pin-export for F4: the record-12 item 4 / hub scope (F4 declaration is the only pin-exportable family) but `authorization_pin_export.py:122` still requires a profile `policy_binding`, so an F4-dedicated workflow (no profile, `:118-119` "no runtime-authority profile is configured") cannot be pin-exported; the composed F4-only-with-profile fixture is the one G1/G5a used (host == eff == cat, null NOT applicable there).
- Existing evidence: G5a F4 fixture content (null); A19 persisted-side.
- Confidence: HIGH.

---------------------------------------------------------------------------------------------------------------------------------
## 6. Counterexample search (to the "eff cannot move alone" argument)

| # | Candidate | Result |
|---|---|---|
| CE1 | A family where eff != catalogue_digest | None. All profile-bearing workflows use the one function (F-D1/F-D2). The age-only `age_pdigest` (joint unreadable+age, `registry_f5_class_unreadable_governance.py:317`) is an intermediate inside the identity dict and not an ECB member (F-D8). |
| CE2 | catalogue_digest not bound by an earlier guard | TRUE on execute and claim after a rebuild (no persisted-vs-live catalogue guard before the ECB/equality). It does not defeat the argument, because eff moves with it (I1). It is bound earlier ONLY on pin-export (`:147`). |
| CE3 | Legal alternate construction giving the same dump with a different digest | None: `commitment` over `model_dump(mode="json")` is a function of the dump. Distinct profile objects with equal dumps -> equal digests. A subclass or non-`RuntimeAuthorityProfile` held object -> `BindingInvalid` -> adapter refusal `configuration_binding_invalid` (no durable row), not an eff mismatch (`registry_governed_lifecycle.py:276-277`). |
| CE4 | eff changes while `families.*.effective_policy_digest` stays equal | FOUND by source: the freshness-extension route. `compose_profile` reads the raw Registry map (F-D7); the family digest covers `effective` only (F-D8). Two Registry selections with equal `effective` but different raw values above the host (e.g. host class age 60, host `FreshnessProfile.max_age_extension_seconds` 100: Registry 70 -> effective 60, room 10 -> limit 10; Registry 90 -> effective 60, room 30 -> limit 30) yield equal family digest, equal host digest, different profile -> different catalogue, approval and eff. This defeats the D-1 reviewer's statement that a different effective profile ALWAYS also moves `families.0.effective_policy_digest`: it does so for every route except this one. It does NOT defeat I1-I4: base cat and app move. UNVERIFIED by execution. |
| CE5 | host_profile_digest unmoved while the profile moves | Only the CE4 route (and masked-host routes for the opposite direction). For all other families, profile = f(host, effective): profile moves => host digest or family digest moves. |
| CE6 | Held-state profile check absent (composed, pdigest None) | Real (F-D6), but the profile then equals the host; eff == host digest, so it is not an eff-vs-host separation, and the base pair still moves. |
| CE7 | Freshness-extension for the claim path | Same as CE4; no held-state pre-check on claim, so the first guard is approval. |
| CE8 | Distinct authorization profiles per action/class | One `RuntimeAuthorityProfile` per workflow; per-action classes are inside the one dump. No second profile object exists in the ECB or in the base. |
| CE9 | Legacy/stripped records | `classify` returns `legacy`/`unbound-after-cutoff` before eff is compared (`effective_configuration_binding.py:193-209`); eff is not isolated there. |
| CE10 | Persisted-side graft with a donor of a different profile | Moves `families.0` as well in all routes except CE4; not a live pathway; requires the unsigned-store write capability; not run. |
| CE11 | Concurrent in-call mutation | Out of the supported model; not a valid pathway. |

---------------------------------------------------------------------------------------------------------------------------------
## 7. FACTS / INFERENCES / UNVERIFIED

FACTS (read at the cited lines): F-C1..F-C4, F-D1..F-D9, guard order of section 1.3, existing evidence as reported in the records of section 1.4.

INFERENCES (from the facts, not executed):
- I-1. I1-I4 and the strict-isolation impossibility (section 3).
- I-2. CE4 freshness-extension route exists and gives a narrower joint (section 6).
- I-3. Pin-export profile-bearing workflows are not constructible with `policy_binding`, hence no live eff pin-export route for them.
- I-4. A mutant removing eff from both mint and live is outcome-equivalent end to end (the base pair still refuses); this matches D-1 verdict section 2.3 ("outcome-equivalent ... from source reading, not execution").

UNVERIFIED:
- U-1. That the pinned Registry adapter `a40fe755` returns `applied` for a record whose class value exceeds the host's (developer test x02 says so; not run here; CE4 depends on it).
- U-2. Whether the raw rows of Q3-E2 contain exactly the diff stated (taken from the hub record, not re-read from `raw/`).
- U-3. Whether G2/P5 use a fixture where host == eff (the hub says persisted-side rows are on a fixture where host profile equals held profile, so a host/effective swap would be invisible there; hub `07` section 6 exclusions).
- U-4. Behaviour at `8616d5f`/main/Python 3.12 for the D-1 rows (not read).
- U-5. Whether the joint unreadable+age workflow passes the CE4 route end to end (same `compose_profile` call; unrun).

---------------------------------------------------------------------------------------------------------------------------------
## 8. Would structurally impossible live isolation still leave a legitimate proof?

Yes, as a DECOMPOSED proof. What each row proves and does not prove:

| Evidence | Proves | Does NOT prove |
|---|---|---|
| A19 `[effective_profile_digest]` (execute, persisted-side reseal) | Comparison sensitivity: a persisted record whose eff member alone differs (digest recomputed, base unchanged) is refused on execute with `authorization_binding_changed` and a durable `EffectTimeRefusal` (the only configuration in which "eff differs, base equal" can exist) | Live derivation sensitivity; unsigned-store pathway (documented limit) |
| G1 (pin-export, 22 members x 2 revisions) | Same comparison, pin-export semantics per `06`/`11` (unknown, payload None, no refusal row, destination untouched) | Live pin-export; fixture has host == eff, so a host/eff swap is invisible |
| G2 (claim) / D-2 Q5 P5 | Claim and provision refuse on the same persisted-side perturbation (`PermissionError`, no claim, destination untouched), 3.11.18 and 3.12.3 | Live claim; same fixture caveat |
| Q3-H2 | Component: persisted eff equals independent commitment of the held effective profile and the persisted `catalogue_digest`; differs from host | Variation of eff (both worlds share the profile) |
| G5a | Minted content on the pin fixture (host == eff == cat) and F4 (null) | Live sensitivity; separation of host vs eff (equal there) |
| Q3-E1 | Guard order: approval precedes ECB | member behaviour |
| Q3-E2 | End-to-end fail-closed on a live profile change, with durable refusal; the joint diff shows live eff moves with the profile and moves the ECB digest | Attribution to eff alone (impossible) |
| D-1 reviewer F2 / this report CE4 | Structure of the joint (what else moves) | Execution |
| Developer mutants `drop-effective_profile_digest-from-preimage`, `members-use-host-profile-for-effective` (KILLED by unit/component tests) | Component sensitivity of eff (preimage membership; not host-substituted) | Independent evidence; end-to-end |

Minimum decomposition that would be NEEDED (my analysis, not adopted):
 D1. Source derivation correctness: for each applicable workflow type (class age, class unreadable alone and joint, composed profile-bearing, composed non-profile-with-profile, F4/no-profile null), the minted eff equals an independently computed `commitment(held.model_dump(mode="json"))`, on a fixture where host != eff, with at least TWO distinct profiles (variation, to defeat a constant). Existing: Q3-H2 (one profile, F5 class age only).
 D2. Component comparison sensitivity: eff alone perturbed in the persisted member (digest recomputed, base empty diff) -> refuse on execute, pin-export (assessment semantics), claim. Existing: A19, G1, G2, P5 (fixture caveat).
 D3. Guard ordering: E1 (approval first) + pin-export `:147` + `profile_modified`. Existing: E1; pin-export order only by source.
 D4. End-to-end fail-closed with durable evidence on a live change: E2 (and optionally the CE4 narrower joint).
 D5. A statement that eff is definitionally redundant with `catalogue_digest` for profile-bearing workflows (so no independent end-to-end case can exist) with the I1-I4 derivation.
 The two-fixture requirement of `12` item 2 would then be satisfied as two decomposition layers (D1+D2, D4) rather than two isolation fixtures. That substitution is the Architect's to make; I do not make it.

---------------------------------------------------------------------------------------------------------------------------------
## 9. Prospective contractual clarification (NOT ADOPTED; for the Architect only)

Needed to accept decomposed evidence for eff under record 12 item 2 (draft wording, prospective, not retroactive; record 12 is not weakened for any other member):
 P-1. State that for `effective_profile_digest`, "independently perturbed" (`03` line 23) is satisfied by (a) a persisted-side perturbation of that member alone with the base binding unchanged, refused on execute / pin-export / claim per `06`/`11`, plus (b) a live-side joint case with attributed diff, because by `02` section 4 line 48 the member equals `catalogue_digest` (profile-bearing) or is null.
 P-2. State that the class of a member whose value is defined to equal another persisted member (eff = catalogue) is "DECOMPOSED-ONLY" and that the required minimum is D1-D5 above, including at least two distinct profiles for the derivation component test.
 P-3. Say whether a live joint case counts for the "two independent fixtures" count, and whether the narrower CE4 joint is required or optional.
 P-4. Say explicitly that attribution of `authorization_binding_changed` is by complementary diff (the code is emitted for any binding difference, `bounded.py:1692-1693`).
 P-5. Keep the masked-host statement alongside (record 12 wording is broader than CP `docs/effective-configuration-binding.md` section 10 at 8616d5f; absent at 739efe7).
 P-6. Declare pin-export scope for eff: profile-bearing governed workflows cannot be pin-exported (policy_binding refusal); pin-export evidence is persisted-side on the composed F4/observation-only fixture only.
 P-7. If the Architect prefers true isolation, it would need a CODE or CONTRACT change (for example making the member independently derivable, or a separate runtime self-check `eff == cat`), which is out of scope for this member and requires a separate authorization; not recommended here.

---------------------------------------------------------------------------------------------------------------------------------
## 10. Bounded deterministic future-case spec (NOT RUN): FXE-JOINT (Execute leg, narrower joint, CE4)

This case does NOT meet the isolation rule (base pair moves). It is the only live case that I found that narrows the ECB diff to exactly two leaves, and it requires an independent owner and an explicit Architect authorization before running.

- Subject: CP `739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69` (src tree `d248bde478ae3f2ce050db4637f0c1203066e906` per D-1), Registry pin `a40fe755e2384a99c37016fa9ad59396f1835900`, Python 3.11.18 (same environment manifest as D-1: pydantic 2.14.2, PyNaCl 1.6.2, pytest 9.2.0). No guard disabled; clock patch only.
- Workflow: `GovernedClassAgeWorkflow` (dedicated; no activation ledger), F4 refund-class fixture as in D-1 `d1_lib.py`.
- Fixture: host profile with `FreshnessProfile(max_age_extension_seconds=100)`, class T1 host age 60; Registry selection SA: `class_status_max_age_seconds {T1: 70}` -> effective T1 = 60; Registry selection SB: `{T1: 90}` -> effective T1 = 60. Pre-checks (assert before any claim): effective maps equal; `families.0.effective_policy_digest` equal in SA/SB worlds; profile dumps differ exactly in `freshness.max_age_extension_seconds` (10 vs 30) and nowhere else; `host_profile_digest` equal; derived `catalogue_digest` differ.
- Changed member: held effective profile (via the Registry raw value above the host).
- Steps: (1) build W_A over SA, issue approval to its profile (`bind_approval`), `decide` -> R authorized (persist ECB). (2) Restart: build W_B over SB on the same store, re-issue approval to W_B's profile. (3) `execute(P, R)`.
- Expected: `PermissionError("authorization-critical inputs changed before effect")`; exactly one new durable `EffectTimeRefusal` with `reasons == ["authorization_binding_changed"]`, vocabulary version per `vocabulary_for`; no attempt row; destination 0 calls and unchanged; complementary diff (live mint vs persisted binding): base diff exactly `{approval_commitment, catalogue_digest}`; ECB diff exactly `{digest, members.effective_profile_digest}`; `families.0.effective_policy_digest`, `host_profile_digest`, `scope.*`, `f4_scalars`, `other_scalars`, `observation_policy` all equal (assert each); classifier `mismatch`.
- Controls: C0 same construction, unchanged SA world -> acknowledged, 1 destination call, empty diff. C1 SB-world with approval NOT re-issued -> `[runtime_authority_approval_mismatch]` only (guard-first, E1 analogue). C2 neutral rotation: re-signed SA' with the same raw values (new selection id/epoch) -> executes (selection rotation alone does not refuse). C3 widened-diff discriminator: SC changes the effective map (T1: 50) -> ECB diff contains `families.0.effective_policy_digest` (shows the leaf is observable).
- Durable evidence: per `06`/`11`, execute = durable `EffectTimeRefusal` (hash of the store before/after, row count +1). If a claim leg is added later (separate authorization): `provision_local_execution_claim`/materialize -> `PermissionError("authorization-critical inputs changed before claim issuance")`, no claim, no refusal row, one stage-claim `ResolutionCheck`, destination untouched. Pin-export: not applicable (`authorization_pin_export.py:122,147`; profile-bearing workflows refuse `policy_binding`); do not write a pin-export leg for this member.
- Acceptance criteria: all controls match prediction; run twice identical except label; harness and protocol sha256 recorded before the run; predictions frozen before running; a scratch-copy mutant ONLY if separately authorized (suggested: live eff := host digest in `registry_f5_class_age_governance.py:260`, expected to be outcome-equivalent to pristine on E2-type joint cases, so no kill is claimed).
- Stop conditions: any base diff leaf other than the two; any ECB diff leaf other than the two; profile dumps differ elsewhere than the extension; Registry refuses a value above the host (U-1) -> stop and report UNREACHABLE for CE4; construction refusal; destination touched; subject/tree/pin/environment hash mismatch; any need to disable or patch a guard; independence requirement unmet.
- Claim wording if it passes: "effective_profile_digest: JOINT with catalogue_digest and approval_commitment on the freshness-extension route (ECB leaf narrowed); strict isolation impossible by `02` section 4 line 48; decomposed evidence A19/G1/G2/P5/H2/E1/E2". NOT "isolated end-to-end".

---------------------------------------------------------------------------------------------------------------------------------
## 11. Uncertainties and caveats
- All of section 3 depends on assumptions A1-A3 and on `profile_digest`/`validate_extensions` remaining unchanged; I did not read `8616d5f` or main.
- CE4 is source-only; U-1 and U-5 are open.
- I did not re-read raw D-1 rows or the G1/G2/P5 rows; I used the verdicts and the hub disposition (which cite them).
- `12` has no explicit "cannot be isolated" status for item 2; the fallback exists only in the hub's own `07` section 7(3)(c) and the Q2 wording of item 1. Whether a "documented unresolved qualification constraint" satisfies Class A is the Architect's decision.
- This is same-lineage analysis; no independence is claimed.

## 12. Items for memory (observed in this task, for the main session to decide)
- Source: this task (static analysis): the live-isolation impossibility for `effective_profile_digest` follows from `02` section 4 line 48 plus the one-function derivation in CP 739efe7; the freshness-extension route (CE4) is the only observed way to remove the `families.*` leaf from the ECB diff.
