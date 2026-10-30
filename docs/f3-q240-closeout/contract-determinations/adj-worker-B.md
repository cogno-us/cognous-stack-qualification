# Worker B: A25(e) host_profile_digest, record 12 item 2 (same-lineage review, not independent)

## 1. Scope
Member: `host_profile_digest` (host half of record 12 item 2). Read-only. I ran no test and edited nothing. I read the harness, the frozen host spec, the merged bounded JSONL (run1/run2), D-1 Q3-H1 and its mutant diff, the original F3-A harness and raw rows, CP 739efe7 source, and registry records 03 and 12. Hub paths are relative to `results/third-party/cp-739efe7-f3-q2q3-bounded-20261030` unless stated. `effective_profile_digest`, `authority_domain` and the claim-joint cases are out of scope.

Counts, checked against the raw JSONL. Host tests are 4 of the 14 pytest tests (`test_FC_H1`, `H2`, `H3a`, `H3b`). Host assertion rows:

| Case | Rows | Preconditions | Gating checks |
|---|---|---|---|
| FC-H1 | 34 | 13 | 21 (7 C, 14 A) |
| FC-H2 | 27 | 14 | 13 (5 C, 8 A) |
| FC-H3a | 14 | 7 | 7 |
| FC-H3b | 17 | 8 | 9 |

- That is 92 rows in total. Plus 10 evidence-only rows (5 + 3 + 1 + 1) and 2 CLASSIFICATION rows.
- 0 CHECK_FAIL and 0 BLOCKED. junit shows 14/14 in both runs.
- Run1 versus run2 host rows are identical except the run-minted decision UUID in FC-H1-C04.

## 2. Distinctness analysis (the core question)

| Dimension | FC-H1 (claim, class-age) | FC-H2 (execute, class-unreadable) | Distinct? |
|---|---|---|---|
| Workflow family / Registry contract | `GovernedClassAgeWorkflow`, r08-v2 | `GovernedClassUnreadableWorkflow`, r08-v5 | YES |
| Host edit leaf | `max_status_age_seconds` 60 to 61, masked by Registry 10 (`compose_profile`, class_age.py:117) | `on_unreadable` bounded_tolerance to refuse, masked by Registry refuse (`compose_unreadable`, unreadable.py:146) | YES |
| Entry point and comparison site | `materialize_local_execution_claim`, `current != decision.binding` (local_authority_effect.py:455) | `execute`, `current != persisted.binding` (bounded.py:1690) | YES, two textual sites. Each is a one-line inequality on the same object. |
| Member hook line | class_age.py:260, `profile_digest(self._f5_host)` | unreadable.py:336, `profile_digest(self._fu_host)` | YES, two one-line sites |
| `_resolve`, ECB equality (`classify`) | `GovernedLifecycle._resolve` (lifecycle.py:263), `ecb.classify` BOUND iff `record == live` (ecb.py:209) | same | NO, shared |
| Member builder | `_gl_build_members` (lifecycle.py:208) to `ecb.build_members` | same | NO, shared |
| Digest function | `profile_digest` (class_age.py:130) | the same function, imported at unreadable.py:68 | NO, literally shared |
| Fixture library | `d1_lib.f5_world/f5_flow/f5_mint/host_profile` unchanged | new local `unr_*` and `host_unr` helpers, but built on `d1_lib.prepare_runtime_authority`, `f5_base_kwargs`, `live_binding`, `split_diff`, `binding_of`, `leaf_diff`, `H.Src`, `H.tba` | Partly. H2's world builder is new code, but it sits on the same library and instrument. |
| Instrument | `Cx`, `live_diff`, `own_commit`, `classification` | same | NO |
| Author, spec, freeze, reviewer | Worker B draft, lead-frozen, review-E | same | NO, one session lineage |

**Different workflow families.** Yes: class-age versus class-unreadable. The developer's own host exemplar, `test_c06` in CP `tests/test_effective_configuration_binding.py:247-253`, is a third family, the composed policy workflow. It is developer evidence and is not independent.

**Different entry points.** Yes (claim versus execute). However FC-H1 differs from the earlier D-1 Q3-H1 in this dimension only. FC-H1's world is the D-1 H1 world unchanged: `f5_world(t1=60, reg=10)`, host 61, approval not re-bound. It adds one `materialize_local_execution_claim` call. FC-H1 is therefore a second leg on the same fixture, not a second fixture. FC-H2 is the only genuinely second fixture. It differs from D-1 H1 in family, hook, Registry contract, composer and edited leaf, and it shares the execute entry point.

**Different underlying implementations.** Only at the thin edges (the hook line, the composer, the final inequality). The load-bearing logic is shared: `_resolve`, `ecb.classify`, `_gl_build_members` and the digest function. My inference, not shown by any mutant in the bounded package:
- A defect in `ecb.classify`, `_gl_build_members` or `profile_digest` would fail both fixtures at once.
- A defect confined to one hook line or one inequality would be caught only by the fixture that exercises it.
- D-1 mutant D1-M14 changed only class_age.py:260 and killed only D-1 H1. The bounded package ran no mutants (limitations item 10), so FC-H2's sensitivity to a defect at unreadable.py:336, and FC-H1's to a deleted claim inequality, are inferred and not killed.

**Independent fixture construction.** No. Same lineage, same helper library, same diff instrument, same frozen decision rule. `orig_harness.py` is a byte-copy of the original qualifier harness (Protocol notes; I did not re-verify its authorship or independence). Expected values are hard-coded literals, which is good. FC-H1-C04 is the one identity-linked expected, a freshly minted decision id.

**Organizational reviewer independence.** None. Producers and review-E are one lineage (limitations 1). Placement under `third-party/` asserts nothing.

**Conclusion on distinctness.** FC-H1 and FC-H2 are distinct pathways: distinct family, entry, hook line and composer. They are not independent fixtures. Their non-overlap is also confounded. FC-H1 versus FC-H2 differ on five axes at once, so a pair of passes cannot say which axis any one pass depends on. Two passes establish "the member is bound and refused on two pathways", not "two independent fixtures".

## 3. What else was asked

**Original F5 masked-host evidence.** Nothing called "original F5 masked-host" exists in F3-A. Three items bear on it, and I could not tell which the brief meant:
- (a) Original F3-A `A02_masked_host_change_observation` (orig_harness.py:640). This is the F4 family, not F5, and a scalar, not a profile. Host status 60 to 45 under Registry 30 was EXECUTED: `acknowledged`, `dest_calls` 1, `binding_status` bound (raw: `cp-739efe7-f3-q4q5q6-20261030/raw/R03|R04-orig-31x-739efe7/helper/f3a_evidence.jsonl` row 54). This is the real "masked-host limit", an observation with no pass criterion.
- (b) Original `A19[...][host_profile_digest]` (orig_harness.py:1190). It forges the persisted member on the "pin" fixture (profile-bearing F4-only composed workflow). Execute is refused with `authorization_binding_changed` (PASS). Pin-export returns state `unknown` with no payload. The two durable-refusal and reason-names-code rows are CHECK_FAIL, which is part of the 23 original FAILs, and the successor interpretation removes that obligation. This is persisted-side, not live-side. It shows the classifier compares the member but not that the live derivation reads the host profile.
- (c) D-1 Q3-H0/H1/H2 in `cp-739efe7-f3-q2q3-isolation-20261030/verdict.md:8,18-23` (F5 class-age, masked, execute). Base diff `[]`, ECB diff exactly `{digest, host_profile_digest}`. D1-M14 is killed and Q3-H1 then acknowledges.

What the original evidence adds to item 2: (a) supplies the limit text and shows it is real, but only for non-profile scalars. (b) adds persisted-side pin-export coverage, the only pin-export touch of this member anywhere. (c) is the first fixture, and the only one with a mutant kill.

**Do the unmasked-host controls change anything?** No, they add nothing to isolation.
- FC-H3a is guard-first: `runtime_authority_approval_mismatch` fires before the ECB is consulted (runtime_authority.py:332-335).
- FC-H3b is joint: base diff `{approval_commitment, catalogue_digest}` plus a four-leaf ECB diff.
- They are correctly labelled non-isolating. Their value is explanatory only: masking is the isolating device.
- "ECB not consulted" in H3a is an inference from guard order (limitations 9).
- They must not be counted toward "two".

**Pin-export host-profile route.** None is reachable live.
- All three profile-bearing governed workflows refuse a `policy_binding` at construction: class_age.py:206-207, unreadable.py:263-264, and the composed policy workflow at registry_governed_policy.py:334.
- Pin-export requires a side `policy_binding` (authorization_pin_export.py:117-122).
- The F4-dedicated family carries `host_profile_digest=None` (registry_f4_age_governance.py:158) and refuses any profile.
- No pin-export host case was executed in the bounded package. The only pin-export touch is the persisted-side forgery in (b) above.
- I re-read the source for the three refusals and the pin demand. I did not construct anything.

## 4. Acceptance test, host_profile_digest

1. **Invariant.** A persisted authorized decision minted under host profile H1 must not be executed, and no claim may issue for it, under a live configuration that differs only in `host_profile_digest`. That means effective profile, `catalogue_digest` and base binding all equal, with the ECB diff exactly `{digest, members.host_profile_digest}`.
   - Execute (frozen 03 L23): `PermissionError`, one durable `EffectTimeRefusal` with `[authorization_binding_changed]`, no attempt, destination untouched.
   - Claim (successor C, pending adoption): `PermissionError`, no claim, no refusal write.
   - Pin-export: no active export.
2. **Strongest evidence.**
   - D-1 Q3-H1 with the kill D1-M14, execute, class-age.
   - FC-H2 (A01-A08 plus the P01-P14 masking preconditions): independent commitments of the effective dumps equal and of the host dumps differ; execute refused with `[authorization_binding_changed]`, vocabulary `runtime-authority-reasons/0.1`, 0 attempts, destination unchanged, control executes once.
   - FC-H1 (claim): A01/A02 diff isolation, A03-A05 `PermissionError` with the claim text, A07 0 refusals, E05 restoration control issues.
   - All of it is two runs, same host, same lineage, n=1 per fixture.
3. **Disproving counterexample.** Any host-only edit with equal effective and base commitments after which execute acknowledges or a claim issues. D1-M14 is the demonstrated example. Also: a host-only edit on an unexercised hook (composed workflow, freshness extension), or a different edited leaf.
4. **Isolating construction reachable?** Yes for execute and claim on masked-host routes under valid authority (supported interfaces, no guard bypass, no graft). Not reachable live for pin-export.
5. **Why pin-export is not reachable.** Profile-bearing families refuse `policy_binding` at construction, and pin-export requires one. This is implementation-level. Frozen 02/03 are silent, and record 12 item 4 is a closeout disposition, not frozen text.
6. **Does the controlling contract require the impossible construction?** Item 2 text ("two independent fixtures; state the masked-host limit alongside") does not require pin-export. 03 L23 demands execute and pin-export refusal for every perturbed member, but that is satisfied on the persisted side. What is impossible is a live pin-export host isolation. The underlying refusal property is required, not that construction. "Independent" is the contested word (see section 5).
7. **Decomposition.** Partly. Established: independent digest recomputation (D-1 Q3-H2, FC preconditions), the persisted-side forged host member refused (original A19), and the live masked-host refusal on execute. Not established by decomposition: pin-export live behavior for this member.
8. **Unqualified.**
   - Pin-export live.
   - The composed policy workflow, freshness-extension fixtures, and class-unreadable on the claim leg.
   - Edited leaves other than `max_status_age_seconds` and the scoped `on_unreadable`.
   - Mutant sensitivity of FC-H2's hook and of the claim inequality.
   - Frozen-literal claim durable refusal (0 refusals observed, FC-H1-A07).
   - Organizational independence.
   - Python 3.12, CP 8616d5f and main.
   - Rows deviating from section 16 (limitations 7).
9. **Prospective change before technical acceptance.**
   - (i) An Architect ruling on R1 versus R2, and on whether "independent" means organizational or only distinct construction.
   - (ii) For "independent" in the organizational sense: re-execution by a different lineage with fixtures not built on `d1_lib`.
   - (iii) If sensitivity matters: scratch mutants for unreadable.py:336 and the claim inequality, which is authorization-gated.
   - (iv) Adoption, or a ruling, on record 11 claim semantics.
   - No product-code change is needed.

**Verdict (host half of item 2): PARTIALLY DEMONSTRATED.**
- The member is isolated end-to-end on masked-host execute across two families, and on masked-host claim under successor semantics.
- "Two independent fixtures" is NOT DEMONSTRATED in the independence sense.
- The R1/R2 reading is CONTRACTUALLY UNRESOLVED and is flagged separately.

## 5. R1/R2 and the "two" count
- **R1.** One fixture per member, matching the c06/c07 pairing. The host fixture is D-1 H1 (or FC-H2), and the effective fixture is a separate, still-contested question. Under R1 the host half is met once, with or without FC-H1/H2.
- **R2.** Two fixtures for the host member. The honest count is D-1 H1 (class-age/execute) plus FC-H2 (unreadable/execute), both frozen-literal conformant. FC-H1 is a third leg on the first fixture, and it is the successor-conditional one.
- The weakest link under R2 is therefore not FC-H1's conditionality but independence of construction.
- Text support. In 08 §0 the dossier says "UNVERIFIED which reading the Architect intends". Worker E (q252-worker-e, E-3) argues R1 is textually supported by the c06/c07 pairing; worker B (q252-worker-b §7) left it open. I add no ruling.

## 6. Masked-host limit statement (must accompany any acceptance)
> "A host change fully masked by a stricter Registry value is not refused where the host value is not itself a bound member: F4 scalars and ObservationPolicy values (original F3-A A02_masked, status 60 to 45 under Registry 30, executed once). For profile-bearing families the host profile is bound through `host_profile_digest`, and a masked host-profile edit IS refused (FC-H1, FC-H2, D-1 Q3-H1). Isolation of this member is possible only because of masking (effective = f(host, Registry) is non-injective on the edited field); unmasked edits are refused through other members first (FC-H3a, guard-first) or jointly (FC-H3b) and isolate nothing. The Control Plane documentation sentence on this limit is absent at 739efe7 and exists only at 8616d5f (docs lines 157-158)."

## 7. Narrowest acceptable wording for item 2 (host half)
> "host_profile_digest: demonstrated, same-lineage, as isolated end-to-end (base diff empty; ECB diff exactly {digest, host_profile_digest}) on two distinct masked-host fixtures: F5 class-age, execute (D-1 Q3-H1, kill-confirmed) and class-unreadable, execute (FC-H2), plus a class-age claim leg (FC-H1; successor semantics: PermissionError, no claim, no refusal write; frozen-literal durable refusal not observed). The fixtures share the ECB engine, the digest function and the fixture/diff library, and were produced and reviewed within one session lineage; they are distinct pathways, not organizationally independent fixtures. No pin-export host case was executed and none is reachable live. The masked-host limit above applies. effective_profile_digest is not covered."

- This keeps "two" as two distinct fixtures. It does not claim independence.
- If the Architect reads "independent" as organizational independence, item 2 cannot be accepted on this evidence. Changing the adjective would change the meaning, and I do not recommend it.

## 8. Contradictions and authority order
1. **Record 12 item 2 ("a host change fully masked ... is not refused") versus FC-H1/H2/D-1 H1.**
   - Record 12's limit text is general; the evidence shows masked host-profile edits ARE refused.
   - Record 12 is controlling but builder-authored. The CP doc limit (8616d5f) covers F4 scalars and ObservationPolicy only.
   - Preserve both: the limit is true for non-bound host scalars and false for the profile member. Record 12's wording is broader than the observed behavior.
2. **Frozen 03 L23 (durable refusal on claim) versus FC-H1-A07 (0 refusals).**
   - 03 and record 02 are first in the authority order; record 11 successor semantics are second (human adoption PENDING, so unsigned).
   - FC-H1 passes only under (2). Under (1) the claim leg does not meet the durable-refusal text. State both.
3. **Item 2 has no fallback status** and the "two/independent" wording is ambiguous (R1/R2). Authority: record 12 (1), unresolved. I did not independently discard it.
4. **Spec header, brief and README** call the cases "independent isolation" or "diff-isolated". The frozen spec itself says "independent isolation: NO" for FC-H1 and FC-H2. The README's "PASS ... diff-isolated" is accurate; the word "independent" must not be carried over.

## 9. Dissent and what could be wrong with my conclusion
- I judged "shared load-bearing logic" by reading source. No mutant at `_resolve`, `classify` or `profile_digest` was run, so "one defect fails both fixtures" is my inference.
- A stricter reviewer could say the five-axis difference between FC-H1 and FC-H2 makes them more independent than I allow. My answer is that axes are not independence of construction or authorship, and the confound limits attribution.
- The attribution in FC-H1 rests on a separate scratch live-world diff plus a generic `PermissionError`, not on a claim-time reason string. Limitations 3 shows a refused claim's ResolutionCheck row is identical to an issued one.
- FC-H2's `exec_refusal_rows` and FC-H1's `claim_attempt` hard-code the expected literals, but the diff and the refusal are computed by the same instrument for both cases. A defect in `d1_lib.split_diff` would affect both.
- I accepted the lead's reading that the bounded package is merged; I did not verify merge state.

## 10. Confidence and limits
- Confidence: high on the shared-code and distinct-site findings (read from source). Medium-high on the evidence counts (recounted from JSONL). Medium on the interpretation of record 12 "independent".
- Not verified: authorship and independence of `orig_harness.py`/the original qualifier; PR merge state; Python 3.12; 8616d5f runtime; the `*-REVIEW` addenda beyond host-relevant lines; the scratch store contents (`basetemp-parent`), though review-E reports it corroborates `h1p` having 0 refusals; `dossier §7` UNVERIFIED claims about a composed masked-host fixture.
- Memory: not used.

## Evidence references
- Hub bounded package: `harness/test_bq_host.py` (FC-H1 :248-336, FC-H2 :337-397, `_h3_world` :398), `harness/d1_lib.py`, `spec/cases-host.md`, `raw/run1|run2/d1_evidence.jsonl`, `limitations.md` items 1-3, 6-7, 9-11.
- D-1 package: `cp-739efe7-f3-q2q3-isolation-20261030/verdict.md:8,18-23`, `raw/mutant-M14-tree-diff.txt`, `harness/test_d1.py:97`.
- Original F3-A: `harness/orig_harness.py:375,640,1190`; raw `cp-739efe7-f3-q4q5q6-20261030/raw/R03|R04-orig-31x-739efe7/helper/f3a_evidence.jsonl` row 54.
- Registry (cogno-us/cognous-ocs-registry, origin/main): record 12 item 2; record 03 L23.
- CP 739efe7 source (`/tmp/claude-0/work/src/cp-739efe7/src/agent_control_plane`): `registry_governed_lifecycle.py:208,252,263`; `effective_configuration_binding.py:209`; `registry_f5_class_age_governance.py:117,130,206,260`; `registry_f5_class_unreadable_governance.py:68,146,263,336`; `bounded.py:1690`; `local_authority_effect.py:455`; `authorization_pin_export.py:117`; `registry_f4_age_governance.py:158`.
- CP test: `tests/test_effective_configuration_binding.py:247-253` (`test_c06`).
