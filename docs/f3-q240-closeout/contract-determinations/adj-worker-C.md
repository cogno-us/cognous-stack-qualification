# WORKER C: A25(e) effective_profile_digest (same-lineage review, not independent)

## 1. Scope
Member: ECB `effective_profile_digest` only. Host digest is out of scope except where it separates fixtures.
Read-only. Nothing was run. I read:
- Registry records 02, 03, 12 and the CP 739efe7 source.
- The bounded package (FXE-JOINT main plus C0-C3), its raw run1 and run2 JSONL, and the junit files.
- D-1 verdict and protocol, and the original F3-A tarball (A19 harness and rows).
- The static worker-C document `q252-worker-c-effective-profile-2026-10-30.md`.

I re-derived the key source facts myself and note below where I rely on that document instead.

Counts I verified from the raw files:
- FXE-JOINT is 5 pytest tests (main, C0, C1, C2, C3), 127 evidence rows per run.
- 102 of those rows are PASS: 37 PRECONDITION, 33 CONTROL, 32 ASSERTION (A01-A32).
- The other 25 rows are OBSERVATION/SNAPSHOT/EXCEPTION with result n/a.
- Run1 and run2 agree on every expected/observed/result value, except the `journal_after` SNAPSHOT rows of main, C1 and C3.
- The package's pytest total is 14 tests, 0 failures, 0 skipped, in each run.
- "102" is rows, not tests, and not 102 assertions. Assertions proper number 32 in main plus 8+8+7+10 in the controls.
- Protocol sha256 prefix `ff25219245f3` matches the frozen file.

## 2. Is strict isolated live-side variation logically incompatible with valid state?

**Target state.** A decision R and a live evaluation L in which ECB `eff_L != eff_R` while `catalogue_digest` (cat) and `approval_commitment` (app) are equal.

**Proof, contract layer.**
- Premise C1: `02` §4 line 48 says `effective_profile_digest` equals `catalogue_digest` for profile-bearing workflows, else null.
- Premise C2: every valid persisted member was minted by the lifecycle, so R satisfies `eff_R = cat_R`.
- Premise C3: every valid live evaluation satisfies `eff_L = cat_L`.
- Then `eff_L != eff_R` implies `cat_L != cat_R`.
- This contradicts "cat equal". The target state is not in the value space of valid states.
- For null/null workflows (F4-dedicated, or composed with no profile) the member is a constant, so no live variation exists.

**Proof, code layer (739efe7).**
- I1 (live co-derivation).
  - Live eff is `profile_digest(held)` = `commitment(held.model_dump("json"))`, at `registry_f5_class_age_governance.py:130-132, 260` and `registry_governed_policy.py:482-486`.
  - cat is `commitment(profile.model_dump("json"))` at `runtime_authority.py:475`.
  - It is called with `self.runtime_authority_profile` at `bounded.py:2560-2563`.
  - Both are computed inside one `GovernedLifecycle._resolve` (`registry_governed_lifecycle.py:263-274`).
  - That function runs `super()._resolve` first, then `_gl_configuration_members()`.
  - Both read the same attribute.
- I2 (mint). The decision is minted on that same path (`:269-270`), so `eff_R = cat_R`.
- I3 (approval). The `approval_commitment` preimage contains `profile.model_dump` (`runtime_authority.py:236-242`), and the binding stores the live-computed expected value. So any H(P) change moves app.
- I4 (order). Base reasons, including `runtime_authority_approval_mismatch`, precede ECB stamping, which precedes `current != persisted.binding` (`bounded.py:1685-1711`).

**Premises it rests on.**
- A1: `commitment` is deterministic and collision-free.
- A2: persisted records come only from the lifecycle's own mint. The store is unsigned, so this is a trust assumption, not enforced.
- A3: the profile object is not mutated between the two reads (single writer).
- A4: no host subclass overrides `_gl_configuration_members` to derive eff differently. That hook is an abstract extension point.
- A5: `profile_digest` and `validate_extensions` stay unchanged.

**Where it could fail.**
- (i) A store write that reseals a persisted member. This is the A19/G1/G2/P5 route, a forged state outside valid construction and outside the documented threat model.
- (ii) An in-call mutation of the held profile (an unsupported race).
- (iii) A regression or host subclass that breaks I1 or I2.
  - Nothing at runtime asserts `eff == cat`. The equality holds by construction only.
  - The proof therefore shows the isolation state does not exist today, not that it can never be created by a future defect.
- (iv) A legacy member-less decision. The member is omitted from comparison, so this is not a counterexample.
- (v) A hash collision.

**Freshness-extension route.**
- `compose_profile` (`registry_f5_class_age_governance.py:117-127`) reads the raw Registry class map to set `freshness.max_age_extension_seconds = min(host_limit, registry - effective)`.
- The family digest preimage is `{family, contract_version, effective}` only, so it ignores the raw map.
- So Registry `{T1:70}` to `{T1:90}` with host age 60 leaves effective age 60 and the families leaf unchanged, but moves the extension limit (10 to 30).
- Observed (run1 `OBS-complementary_diff`, A14-A17, A22):
  - Base diff is exactly `{approval_commitment, catalogue_digest}`.
  - ECB diff is exactly `{digest, members.effective_profile_digest}`.
  - Families and host leaves are equal.
  - `claim_for` returns "joint".
- Answer to "moves the families leaf only": no, the opposite.
  - The route removes the `families.0` confound that D-1 Q3-E2 had.
  - C3 (`{T1:50}`) shows the leaf reappears when the effective age changes.
  - It cannot remove the base pair, because the profile dump enters cat and app.
  - It narrows the joint set but does not isolate.

**Verdict on isolation: STRUCTURALLY UNREACHABLE** (valid authority, live side, execute or claim).

## 3. Per-member answers (effective_profile_digest)

1. **Exact invariant.**
   - Safety: for any authorized decision carrying the member, if the live evaluation's member differs from the persisted one (digest or any member leaf), execute, claim and pin-export do not proceed. Execute writes a durable `authorization_binding_changed` refusal, with no attempt and the destination untouched.
   - Derivation: live eff equals `commitment(held.dump)` and equals `catalogue_digest` (or null).
   - These are two separable properties.

2. **Strongest existing evidence.**
   - (a) Derivation at two or three points. A04 and A10 show persisted and live eff equal an independent harness commitment of a literal-built dump (SA, SB). A05 and A11 show eff equals cat. C0-A07/A08 repeat it. The host is a separate constant (A06, A13).
   - (b) Joint diff attribution (A14-A22).
   - (c) End-to-end joint refusal after approval re-issue: A24-A31 (`PermissionError`, one durable `[authorization_binding_changed]`, no attempt, destination untouched, binding unchanged).
   - (d) Guard order: C1 gives only `[runtime_authority_approval_mismatch]` and the ECB code is absent (C1-A03/A04). D-1 Q3-E1 gives the same.
   - (e) Controls: C0 (unchanged executes once), C2 (re-signed selection executes, so no selection-identity artefact), C3 (families leaf appears with a third point).
   - Persisted-side comparison sensitivity is only cited: original A19 execute `[effective_profile_digest]` (resealed, self-consistent, PASS: `[authorization_binding_changed]`, no attempt, destination untouched), plus G1/G2/P5. I read the A19 rows in the tarball (`runs/A-main2/f3a_evidence.jsonl`). Neither D-1 nor the bounded run re-verified them.

3. **Valid runtime counterexample that would disprove the property.**
   - A valid decision whose live eff differs from the persisted eff, at the same profile-bearing workflow, that executes or claims.
   - Equivalently, an effective-profile change (freshness route or effective-map route) that executes with the approval re-issued.
   - Also a live eff that is constant, equals the host digest, or is not `commitment(held.dump)`. FXE A04/A10 would expose these at SA/SB. I have not executed that.

4. **Is the missing independent-isolation construction reachable under valid authority?** No (section 2).

5. **Why not.**
   - The frozen definition (line 48) plus single-call co-derivation makes `eff` a function of the same object as cat and app.
   - The impossibility is a derivation consequence, not a failed attempt.
   - The only routes that vary eff alone are an unsigned-store write or an unsupported attribute mutation.

6. **Does the controlling contract require the impossible construction or the underlying refusal property?**
   - `03` L23: "every member perturbed independently ... changes the digest and makes execute AND pin-export refuse". This reads as the refusal property. A persisted-side member perturbation satisfies the text.
   - Record 12 item 2 (Class A) says: "Two independent fixtures needed; state the masked-host limit alongside."
     - It has no "if not isolable" fallback. Item 1 has one.
     - It calls `test_c06` and `test_c07` "isolating". Static worker-C F-C4 shows `test_c07` re-issues the approval, so it is joint. I have not independently re-read `test_c07`.
     - Read literally for the effective member, it asks for an impossible construction. Read as "two independent fixtures overall", it is ambiguous.
   - Verdict: **CONTRACTUALLY UNRESOLVED.**

7. **Could an independently verified decomposition establish the underlying obligation?**
   - Yes in principle, as an argument. It cannot be observed as an end-to-end isolated refusal.
   - See section 5. It has not yet been independently verified.
   - Verdict: **PARTIALLY DEMONSTRATED** for the underlying refusal property.
     - Joint end-to-end plus derivation (n=1 workflow) are demonstrated.
     - Persisted-side comparison sensitivity is cited, not re-verified.
     - Independent verification and eff-specific mutant evidence are absent.
   - Verdict: **NOT DEMONSTRATED** for member-specific live isolation (and it is unreachable).

8. **What remains unqualified.**
   - Member-specific attribution of the refusal. Independence of everything (one lineage).
   - Pin-export, which is unreachable for profile-bearing families (`registry_governed_policy.py:333-334` refuses `policy_binding`, which pin-export needs at `authorization_pin_export.py:120-122`). Pin-export also has an earlier guard at `:147` before `_resolve`. No pin-export case ran.
   - Claim for eff (no claim leg in FXE).
   - Class-unreadable, joint, and composed profile-bearing workflows. Python 3.12. Revisions other than 739efe7.
   - Eff-specific mutants (none in any independent campaign).
   - Provision route: one synthetic F4 exercise only.

9. **Prospective change before technical acceptance.**
   - No CP code change is required for this member. Decoupling eff from cat would change frozen line 48 and the protected contract. I do not recommend it.
   - Required: an Architect ruling on record 12 item 2 giving an explicit fallback for `effective_profile_digest`. It should state "structurally joint; acceptance by independently verified decomposition D1-D4", and correct the "isolating" description of `test_c07`.
   - Required: independent re-verification of the cited persisted-side rows (A19, G1, G2, P5) and of the FXE rows.
   - Required: the eff-specific mutant set below, or an explicit waiver of it.

## 4. What the joint and decomposed evidence establish, and what cannot be inferred

**Strongest property actually established (bounded, same-lineage).**
- Scope: `GovernedClassAgeWorkflow`, host age 60 with extension limit 100, CP 739efe7, Registry pin a40fe755, Python 3.11.18, one SA/SB pair plus SC.
- Property: a change to the effective profile (freshness-extension route) moves exactly {cat, app, ECB digest, ECB eff}.
  - The live eff member equals the independent commitment of the effective profile and equals cat.
  - With the approval re-issued, execute fails closed with one durable `authorization_binding_changed`.
  - With the approval not re-issued, the approval guard refuses first.
  - A neutral re-signed selection does not refuse.
- It is "joint-refusal plus derivation correctness plus guard order".

**Member-specific sensitivity cannot be inferred from the joint refusal.**
- The refusal condition is `reasons or current != persisted.binding` (`bounded.py:1690`).
- The code is assigned whenever there are no other reasons (`:1691-1692`).
- The base pair `{approval_commitment, catalogue_digest}` moves in main, so the refusal would still occur if the ECB eff member were absent, constant, or ignored by the comparator.
- The code is identical whichever leaf differs.
- A32 (classifier `mismatch`) is the candidate's own read-only classifier and the harness marks it evidence-only.
  - It also reads `mismatch` in C1 (observed in the C1 `OBS-execute_outcome`), where the refusal was approval-only.
  - So it does not attribute the refusal.
- The package itself says this: limitations 4 and 9, and `spec/cases-eff.md` §0.
- Inconvenient nuance: `cases-eff.md` §0 item 4 calls a live-eff := host-digest mutant "outcome-equivalent".
  - That holds for the refusal outcome only.
  - The value assertions A04 and A10 compare to an independent commitment, so they would very likely fail under such a mutant.
  - This is source reasoning. No mutant was run.
- The members that main cannot kill are "comparator ignores the eff slot" and "eff dropped from the comparison while its value stays correct". C1 cannot either.

**Member sensitivity can be argued only compositionally, never from the joint refusal.**
- Requires D1 (live eff tracks H(P) and is not constant or host) and D2 (the comparator is sensitive to the persisted eff slot).
- Also requires the premise that the comparator is extensional (`record == live`, `ecb.classify` BOUND iff equal) with no provenance special-casing.
- Then a live eff change would be refused even with base fixed. The inference is valid under those premises, but it is an argument, not an observation.

## 5. What an independently verified decomposition would have to show, and what exists

| Element | Must show | Existing evidence | Gap |
|---|---|---|---|
| D1 derivation invariant | Live and minted eff equal H(held.dump) and cat. Not a constant, not host. Several points. Plus the by-construction proof with premises A1-A5. | A04, A05, A10, A11, C0-A07/08, C3 dumps; source facts F-D1..F-D5; proof section 2. n=1 workflow, 2-3 points, fixture separates host from effective (host 100 vs 10) | No independent re-derivation. No eff-specific mutant. Other profile-bearing workflows (unreadable, joint, composed) not exercised |
| D2 member-comparison sensitivity | Persisted-side eff perturbation (digest resealed, base untouched, live unchanged) is refused at execute, claim, pin-export and provision | Original A19 execute `[eff]` PASS; G1/G2/P5 cited. I read the A19 execute and pin-export rows. The fixture (composed F4-only with host profile) has eff content equal to the host digest equal to cat, so it cannot separate an eff slot from a host-swap wiring error. It is not the F5 class-age fixture | Cited only, never re-verified. Different workflow class (shared-code premise). Pin-export under frozen-literal wording fails 2 checks (`reason_names_code`, `durable_effect_time_refusal`). Mutant "comparator ignores eff" never run independently |
| D3 guard order | Approval guard precedes the ECB comparison. The ECB is reached only after approval matches the live profile. | C1-A03/A04 (only the approval reason); D-1 E1; source order `runtime_authority.py:332` before `registry_governed_lifecycle.py:267-285` | The ECB code's absence proves non-consultation only by inference. Not a mutant test |
| D4 end-to-end | Durable refusal, no attempt, destination untouched for a real effective-profile change | A24-A31 (main), C3-A07..A10 | Joint only. Execute only. Claim and pin-export not run. Run1 and run2 are same-host repeatability, not replication |
| Wiring | The live eff value that D1 verifies is the value D2's comparator checks | Source reading only (`_gl_with_member`, `classify`, `ecb.mint`) | No test ties D1 and D2 together; only a composition argument |

**Mutant set an independent verifier should run** (none of these exist independently):
- Drop eff from the compared record or preimage.
- Constant live eff.
- Live eff := host digest.
- Comparator ignores the eff slot.
- Persisted eff reseal on an F5 class-age fixture.

**Source-reasoned, not executed, preimage-drop mutant.**
- A19's harness reseals with its own `my_digest`, so a product mutant that drops eff from the digest preimage would still refuse (digest mismatch) and would survive A19 `[eff]`.
- FXE A08 and A12 recompute the digest independently, so they would catch it.
- The two bodies of evidence are complementary on this mutant, but this is reasoning.

## 6. Contradictions and authority order
1. **Isolating versus joint.**
   - Record 12 item 2 calls `test_c06` and `test_c07` isolating. The static worker-C analysis shows `test_c07` is joint (approval follows).
   - Authority: record 12 controls as acceptance text (1). The source and the 02 §4 line 48 definition are frozen text (1), and they refute isolation. Unresolved, needs an Architect ruling.
2. **Expectation wording versus Class A wording.**
   - `03` L23 requires refusal on member perturbation. Record 12 item 2 requires "independent fixtures".
   - Both are (1). They are compatible only if "fixture" can be decomposed or persisted-side.
3. **Frozen-literal versus successor semantics for claim and pin-export.**
   - `03` L23 literal wording requires a durable refusal. Records 06/11 (2, adoption pending) and builder prepared semantics give `PermissionError` or `unknown`, with no refusal row.
   - Authority order: (1) over (2). The record 11 adoption is PENDING, so any pin-export or claim PASS is successor-conditional.
   - The eff pin-export rows in A19 show this: 2 `CHECK_FAIL` rows under the literal wording.
4. **Package wording versus assertion semantics.**
   - README, `cases-eff.md` and limitations say "not isolated".
   - A22 and C3-A06 are classification rows, not proofs of isolation.
5. **Package "outcome-equivalent" claim for mutants versus value assertions.** See section 4 (authority (3) builder-authored evidence-method text; the assertions are (3) too).
6. **Package count wording.** "102" is rows, not tests (14) and not assertions.

## 7. Dissent / what could be wrong with my conclusion
- The structural proof depends on A2. The unsigned store means the premise "persisted records come only from the lifecycle" is a trust assumption. I treat forged records as outside valid construction. The Architect could consider persisted-side forging as the intended meaning of "perturbed independently". Then D2 alone (A19) would already meet `03` L23, and my "partially demonstrated" would be too strict.
- I relied on the static worker-C document for facts F-C4 (`test_c07` joint), F-D6 (composed non-profile families) and F-D7 (raw-registry dependency exception). I re-read F-D7's `compose_profile` and the F-D1/F-D2 code lines. I did not re-read `test_c07`.
- The "wiring" gap and the A19 fixture limitation (eff content equals host content equals cat) are my inferences from the fixture description and the static document. I have not executed the A19 fixture.
- The mutant predictions are source reasoning, not results. The preimage-drop and host-swap claims could be wrong if an assertion I did not trace behaves differently.
- All producers and reviewers share one lineage, including me.

## 8. Confidence and limits
- High: the structural impossibility (derivation chain plus line 48). The FXE rows say what the package says, and run1 and run2 agree.
- Medium: that the persisted-side evidence transfers to the F5 class-age workflow (shared code).
- Low or unknown: anything about independently re-verified A19/G1/G2/P5; other profile-bearing workflows; Python 3.12; 8616d5f and main.
- Not verified:
  - Records 06, 11, 13 and 14 text beyond keyword search.
  - D-2 Q5 and the readjudication evidence.
  - The mutation-final2 developer summary.
  - The basetemp stores beyond decision binding digests (I confirmed persisted eff equals persisted cat in every FXE store I read).
  - The Python harness code for FXE beyond the specification.

## 9. Evidence references
- Source (CP 739efe7):
  - `registry_f5_class_age_governance.py:117-127, 130-132, 260`
  - `registry_governed_lifecycle.py:208-215, 263-285`
  - `registry_governed_policy.py:333-334, 476-486, 503-505`
  - `runtime_authority.py:236-242, 332-335, 473-475`
  - `bounded.py:1685-1711, 2055-2070, 2560-2563`
  - `authorization_pin_export.py:120-122, 147, 170-181`
  - `local_authority_effect.py:443-466`
- Registry: `02` §4 line 48; `03` L23; `12` item 2 (all via `git show origin/main`).
- Bounded package:
  - Directory: `/home/claude/cognous-stack-qualification/results/third-party/cp-739efe7-f3-q2q3-bounded-20261030/`
  - Rows: `raw/run1/bq_evidence.jsonl`, `raw/run2/bq_evidence.jsonl` (case_id FXE-JOINT, assertion ids cited above).
  - Package text: `spec/cases-eff.md` §0-§10, `contract-coverage.md`, `limitations.md` items 4, 5, 9.
  - Stores: `raw/run1/basetemp-parent/bt/test_FXE_JOINT_*`.
- D-1: `cp-739efe7-f3-q2q3-isolation-20261030/verdict.md` lines 36-37 and `PROTOCOL-D1-v1.md` Q3-E1/E2.
- Original A19: `cp-739efe7-f3-independent-20261029/F3-qualification-evidence-ed31764.tar.gz`, `runs/A-main2/f3a_evidence.jsonl` and `harness-final/test_f3a_independent.post-AMEND4.py:372-438, 1185-1215`. I extracted it to `/tmp/claude-0/work/adj/c_orig`.
- Static analysis (same lineage): `docs/f3-q240-closeout/contract-determinations/q252-worker-c-effective-profile-2026-10-30.md`.
