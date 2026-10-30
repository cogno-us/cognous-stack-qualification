# WORKER E: adversarial review of combined A/B/C/D findings (same-lineage review, not independent)

## 1. Scope and method
Read-only. I ran no test, harness or qualification. I read COMMON.md and worker-A/B/C/D, then re-checked the load-bearing citations in source (CP 739efe7 pristine tree), Registry origin/main (records 02, 03, 12 byte-compared to r12.txt; 06/11/13 via the D copies), the merged bounded package JSONL (python parse), junit, SHA256SUMS, and the original A-main4 rows. Members: authority_domain (AD), host_profile_digest (HPD), effective_profile_digest (EPD). Authority order as in COMMON.md.

## 2. Citation spot-check (22 checked; all hold unless noted)
- bounded.py:1690 `if reasons or current is None or current != persisted.binding` OK. :2584 (binding copies `proposal.manifest_digest`), :2618-2619 (`manifest_digest_mismatch`), :2297-2298 (`authority_domain_mismatch`) OK.
- local_authority_effect.py:455 (comparison) and :458 (generic PermissionError) OK.
- authorization_pin_export.py: :144 binding_digest test, :146 `commitment(profile) != persisted_catalogue`, :147 its raise, :145 raise for the digest. The workers cite these as :145/:146/:147, which is inconsistent but harmless. The pin-export comparator at :181 compares against `current_binding`, not `persisted.binding`. :117-122 pin needs `policy_binding` OK.
- registry_governed_lifecycle.py: :137-140 `require_authority` reads `workflow_kwargs["manifest"]` before the base `__init__` deep-copy (bounded.py:1291). :175 is the only `_gl_authority` assignment (grep confirms; 4 constructors all call `require_authority`). :267-268 base-reason short-circuit. :307-309 `manifest_authority_changed`. `_gl_reverify` is reached only via `_gl_revalidate` at :327 (decision) and :332 (effect) and the commit gate :321. It is NOT reached by claim or pin-export (Worker A's stateful-manifest observation is correct).
- registry_governed_policy.py:333-334 `policy_binding_unsupported` and :482-483 OK. class_age:206-207, unreadable:263-264, f4:110-111 and :158 OK.
- Record 02 L48 (EPD "equals catalogue_digest for profile-bearing workflows, else null") OK; L52 rule 2 "Execute and pin-export claim recompute" OK. Record 03 L23 (expectation 1) names "execute AND pin-export" only; it does not name claim issuance. Record 03 L30 (expectation 8) prescribes a replayed-member negative control. Record 12 = r12.txt exactly. Item 1 has the fallback sentence; item 2 has none; item 4 is Class C with F4-reachable members kept in A.
- Counts: junit 14/14, 0 fail/skip, run1 and run2. PASS rows: FC-H1 34, FC-H2 27, FC-H3a 14, FC-H3b 17, FXE-JOINT 102 (bq file; the same 102 are mirrored in d1_evidence, so do not double count), N-CLAIM-JOINT 82. FC-H1-A07 = 0 refusals and N-CLAIM-JOINT-A04 = 0 refusals (observed). N-CLAIM-A10/A11/A13 as Worker A states. Run1/run2 differ only in 5 gating rows with run-minted UUID expecteds (matches README and review-E).
- SHA256SUMS: 510 lines, 510 OK. PROTOCOL.md sha256 ff25219245f39b85...a18b0d2 equals protocol.sha256 and source-identity.json. CP 739efe7d, src_tree d248bde4, pin a40fe755, hub main 01c1da1c = merge of PR #254: all match.
- Original oracle: A-main4 rows 574-577 (execute AD PASS), 580-584 (pin-export `unknown`, two CHECK_FAIL), 883 (A25(a) UNREACHABLE-ISOLATED) OK. README states "Original F3-A remains FAIL (23 assertions)" and no worker rescores it.

## 3. Numbered findings

**F1 (must-disclose, worker error) Claim-branch mislabel.** Workers A and D say N-CLAIM-JOINT exercised the claim "journal branch" and that the non-journal branch is unexercised. Source and spec say the opposite for AD. N-CLAIM-JOINT uses `GovernedAgeWorkflow` (d1_lib.py:222), which refuses any runtime-authority profile (f4:110-111), so `runtime_authority_profile` is None and `journal=False` (local_authority_effect.py:443). `_resolve` then takes the MINT branch (lifecycle :270-272; spec/cases-domain.md:20-23 says so). The claim comparison is plain model equality with no classification or legacy handling. FC-H1 (class-age, profile present) takes the journal branch with stage="claim". So claim evidence for AD and for HPD is on different code branches, and AD claim says nothing about a profile-bearing or pin-capable shape. Fix: state per member which branch was exercised.

**F2 (must-disclose) Claim attribution is instrument-inferred.** The claim's own `current` binding is not observable. The base/ECB diff comes from a scratch `decide`/`live_diff` world (spec/cases-domain.md:112; FC-H1 `live_diff`). The claim itself only gives a generic `PermissionError` and a ResolutionCheck row identical to an issued one (limitations 3). "Isolated on the claim leg" for HPD therefore means "scratch-measured diff plus a claim that did not issue", not an observed member-specific claim refusal. Fix wording: "diff-isolated by instrument, claim refusal generic".

**F3 (must-disclose) "STRUCTURALLY UNREACHABLE" is over-stated if read as unconditional.** It holds only as: "not reachable through supported interfaces at CP 739efe7 under premises P". The premises that can fail:
- (a) Same-code mint and read. Persisted-by-version-N then live-by-version-N+1 (restart across an upgrade that changes `profile_digest` or `scope_identity` preimage but not `catalogue_digest` or `approval_commitment`) is a valid operational state in which eff or the leaf differs with the base equal. Workers C (A5) and A (P3/P4) assume this away. Nothing at runtime asserts eff == cat (Worker C concedes).
- (b) Unsigned store (persisted records only from the lifecycle). Trust assumption, not enforcement.
- (c) AD only: stateful `Mapping` manifest. The leaf is the construction-time read of `workflow_kwargs["manifest"]`, while `manifest_digest` is `commitment(self.manifest)` of the deep copy. Execute is protected by `_gl_reverify`; claim and pin-export are not. Worker A flagged but did not trace this. It is adversarial-host, so outside "valid authority" in my reading, but it is not excluded by source.
- (d) EPD: only class-age was exercised; unreadable, composed and pin-shape are source-argued.
- (e) Pin-export for all three members is static reading only (no case executed anywhere).
Recommended verdict wording: STRUCTURALLY UNREACHABLE (supported interfaces, 739efe7, premises P1-Pn listed; not proved in general; pin-export legs source-only).

**F4 (must-disclose) EPD "by definition" conflates two arguments.** limitations 4 and contract-coverage say "by definition and construction (min(host, Registry); co-derived)". `min(host, Registry)` is the F5 masking rule, not the 02 L48 definition. L48 literally says "else null" and does not describe the pin-capable shape (profile present, no profile-bearing family, EPD non-null: registry_governed_policy.py:482-483). The definitional argument covers profile-bearing workflows only; elsewhere the claim rests on code co-derivation (Worker D's observation, which I confirm from the lines). Fix wording accordingly.

**F5 (must-disclose, misquote) contract-coverage.md attributes a fallback to record 12 item 2.** Its EPD row quotes the requirement as "Isolation, else not independently demonstrated". That is item 1's text. Item 2 reads "Two independent fixtures needed; state the masked-host limit alongside" and has no fallback (Workers C and D right; Worker A right that item 1 has one). Correct by addendum. Consequence: item 2 for EPD is unsatisfiable as written, not "not independently demonstrated".

**F6 (must-disclose) Which reading of item 2 the text supports.** The item's own basis cell says `test_c06` (host only) and `test_c07` (effective only) "isolate each", then asks for "two independent fixtures". The most natural reading (R1) is one fixture per named member. Worker B's R2 (two for host) is a weaker reading. Neither is determinative, and 13 decision 3 leaves the force of items 1 and 2 open. Under R1 the host fixture exists and the effective fixture is the impossible one. Under R2 the host half needs two. I verified Worker B's point that FC-H1 is not a second fixture: FC-H1 builds `f5_world(t1=60, reg=10)` with host 61 (the D-1 Q3-H1 world, test_d1.py:98) and adds only a claim call. The honest "two" under R2 is D-1 Q3-H1 plus FC-H2 (both execute). README and contract-coverage name FC-H1 and FC-H2 as the pair; that overstates fixture count. Also record 12 says a masked host change "is not refused (documented limit)"; evidence shows masked host-profile edits ARE refused (HPD member). Record 12's limit text is true for F4 scalars and ObservationPolicy only (original A02 masked status 60 to 45 executed once), and the CP doc sentence is absent at 739efe7 (docs grep: no hit). The limit statement must be carried with that scope.

**F7 (must-disclose) The "frozen-literal 03 L23 durable refusal on claim" annotation is not supported by the text.** Worker D's reading is better supported than A/B/limitations 2. 03 L23 names execute and pin-export only. 06 L19-22 reads "pin export claim path refuses" (the annex wording) as the pin-export path, and introduces claim issuance as successor scope C (06 L31, L43; 11 L15). So no frozen text unambiguously demands a durable refusal on claim. Observed facts stay: 0 refusal rows (FC-H1-A07, N-CLAIM-JOINT-A04), PermissionError, no claim. Fix wording: "claim issuance is addressed only by 06/11 scope C (adoption pending); 03 L23 does not name it; 02 L52 is ambiguous". The claim legs also fall outside record 12 items 1 and 2 wording, so they count toward scope C, not toward Class A discharge.

**F8 (must-disclose, cross-package transfer) AD execute evidence is not in the bounded package.** contract-coverage says AD "execute and claim JOINT-ONLY, pin-export GUARD-FIRST". N-CLAIM-JOINT has no execute leg (Worker A, confirmed: claim only, routes materialize and provision). Execute joint evidence is D-1 Q2-A2(ii) (different package, different protocol). "GUARD-FIRST" for pin-export is a source reading, not an observation. Host evidence (FC-H1/H2/H3, D-1 H1) must not be reused for AD or EPD, and claim evidence must not be reused for pin-export. No pin-export case exists for any member in bounded or D-1; the only pin-export touches are original A19 persisted-side rows and readjudication G1.

**F9 (must-disclose) Graft is not valid authority and not item 1's construction.** D-1 Q2-A3 writes a genuine donor member into the persisted decision by unsigned-store write (execute only, one fixture, F4 workflow). It is the same capability class as the A19 reseal and the "documented rollback/forge limit" (D-1 verdict L30). Record 03 expectation 8 sanctions replay as a negative control, not as an isolation of "decision under X, live side rebuilt under Y". "MET ONLY BY GRAFT" in the D-1 verdict must not be quoted as discharge. The M06 kill (graft executes under the mutant) shows the leaf is comparison-sensitive on that one route; it says nothing about claim or pin-export. Worker A's dissent (store owner might be "valid authority") would make execute DEMONSTRATED; I reject it as unsupported by 11/12/D-1's own wording, but it is an Architect call.

**F10 (blocking for any acceptance claim) AD item 1 is unsatisfied.** The fallback "not independently demonstrated for this member" is a reportable negative status, not a discharge. Item 1 is inside the Class A boundary, and 13 decision 3 leaves open whether acceptance can proceed with that status. I confirm A's disposition and hold that no wording may imply AD isolation or discharge.

**F11 (blocking for any acceptance claim) EPD item 2 is unsatisfiable as written, and Option B is not ready.** Worker D's Proposal B requires an impossibility argument "reviewed by the designated independent owner" and decomposed elements (a)-(e). None are met: the proof is lineage-internal (premises A1-A5, F3 above); live-derivation and comparator-ignores-eff mutants never run; derivation exercised on one class-age workflow only; the persisted-side leg (A19 [eff]) uses the composed F4-only fixture where eff = host digest = cat, so it cannot separate an eff slot from a host-swap wiring error (Worker C); and component (b) "refused on every in-scope interface" is met on pin-export only under the unadopted 06/11 reading (A19 pin-export [eff] has two CHECK_FAIL under the literal oracle). The member could be called "decomposed-qualified" only after Architect-signed adoption plus independent verification. It must never be called "isolated".

**F12 (must-disclose) Mutation and sensitivity gaps.** The bounded package ran no mutants (limitations 10). Only D1-M14 (class_age.py:260) kills an HPD defect, and only D-1 H1; FC-H2's hook (unreadable.py:336) and the claim inequality (local_authority_effect.py:455) have no kill. "Outcome-equivalent mutant" wording in cases-eff.md section 0 holds for the refusal outcome only (Worker C), while A04/A10 value assertions would very likely catch a live-eff := host mutant (source reasoning, not run). A joint refusal is also outcome-equivalent with a deleted or constant leaf (Worker A observed this under M06 for Q2-A2(ii)).

**F13 (minor) Counting.** 14 tests; rows are not assertions. N-CLAIM-JOINT 82 PASS = 59 ASSERTION + 22 PRECONDITION + 1 CONTROL (bq_kind). FXE 102 = 37 precondition + 33 control + 32 assertion (Worker C). Host rows are likewise preconditions plus gating checks (Worker B). Anything saying "N-CLAIM 82 assertions" or "102 assertions" is wrong. FXE rows are mirrored in two files; do not double count. README's "Assertion/precondition PASS rows" wording is acceptable.

**F14 (minor) Original oracle preserved.** All four reports and README keep original F3-A as 74 pass / 23 FAIL (22 pin-export members + A06) with no rescoring. Successor PASS statements are all labelled conditional on 06/11 adoption. Add one explicit sentence in any adjudication: "no successor or bounded result rescoring original F3-A".

**F15 (minor) Unverified or unexercised branches that should be listed.** Legacy decisions on the non-journal claim branch (plain equality, no cutoff logic, source-only); `docs/effective-configuration-binding.md:127` vs `BindingInvalid` becoming a `PermissionError` at pin-export (Worker D item 6, not exercised); pin-shape claim "host == held == cat" (Worker D's reading; I confirmed only that the policy hooks compute `hd` from `_gp_host` and `ed` from `held`, not that they are equal).

## 4. Disagreements between workers: which reading the evidence supports
- A vs C on item-level fallbacks: both right. Item 1 has the fallback; item 2 has none (r12 verified). Not a conflict about facts. It means AD has a sanctioned negative status, while EPD has none.
- D vs bounded package on claim: D is better supported (F7).
- A and D vs source on the claim branch: A and D are wrong for N-CLAIM-JOINT (F1).
- B's R1/R2: R1 is the more natural reading of item 2 and shifts the problem to the effective fixture (F6). B's verdict "host half PARTIALLY DEMONSTRATED" stands, and "two independent fixtures: NOT DEMONSTRATED" stands.
- C (EPD unreachable at high confidence) vs F3: unreachable under stated premises only; I keep C's verdict with the condition.
- D (AD not Option B) vs A: agree. AD has no frozen equation and has its own fallback. A's structural proof for AD is sound but depends on P6 (value-stable manifest) for claim and pin-export.
- C says persisted-side evidence "cited, not re-verified"; I re-read A19 execute/pin-export AD rows (574-584) and confirm them; I did not re-read the [eff] or [host] A19 rows.

## 5. Acceptance-test verdicts per member (items 1-9 condensed, with best option)

**AD.** Invariant: persisted under X, live under Y: execute durable refusal; pin-export non-active; claim no claim. Strongest evidence: D-1 Q2-A2 natural routes (execute, joint or guard-first), Q2-A3 graft with M06 kill, N-CLAIM-JOINT (claim, non-journal branch, joint), A19 persisted-side.
- Isolation under valid authority: STRUCTURALLY UNREACHABLE (conditions F3).
- Refusal property: PARTIALLY DEMONSTRATED (execute strongest; claim joint and successor-conditional; pin-export persisted-side only, static for live).
- Whether the contract requires the impossible construction: CONTRACTUALLY UNRESOLVED (item 1 names it but carries its own fallback; 03 requires the refusal property).
- Item 1 status: "not independently demonstrated for this member". Decomposition could establish the refusal obligation but not "the leaf, not manifest_digest, caused it" (Q7). Unqualified (Q8): live pin-export, claim in profile-bearing shape, comparison-side/live-only mutants, P6, independence.
- Best option: **A (retain unchanged)**. B not needed (no frozen equation, own fallback). C unsupported (reachable on all three interfaces).

**HPD.** Invariant: masked-host edit with base and effective equal and ECB diff exactly {digest, host_profile_digest} must be refused. Isolation reachable under valid authority on execute (D-1 H1, FC-H2) and via claim (instrument-measured, F2); not live on pin-export (profile-bearing families cannot carry `policy_binding`).
- Verdicts: execute PARTIALLY DEMONSTRATED (n=2 fixtures but shared library, one mutant kill); claim PARTIALLY DEMONSTRATED, successor-conditional, instrument-attributed; pin-export live STRUCTURALLY UNREACHABLE (source), persisted-side only; item 2 sufficiency CONTRACTUALLY UNRESOLVED (R1/R2).
- Option: **A**. C is only a confirmation of item 4 for profile-bearing families; it must not remove the pin-shape or persisted-side legs.
- Required wording: "two" = D-1 Q3-H1 + FC-H2, same lineage, shared d1_lib/ECB engine/digest function, five-axis confounded, one mutant; FC-H1 is a claim leg on the first fixture.

**EPD.** Invariant: live eff differing from persisted with a resolved base must refuse; eff == catalogue_digest for profile-bearing workflows.
- Isolation: STRUCTURALLY UNREACHABLE (premises A1-A5; F3, F4).
- Refusal property: PARTIALLY DEMONSTRATED (joint end-to-end FXE A24-A31, derivation A04/A05/A10/A11, guard order C1, controls C0-C3; persisted-side comparison cited from A19 on a different fixture).
- Member-specific live sensitivity: NOT DEMONSTRATED.
- Item 2 for EPD: CONTRACTUALLY UNRESOLVED; as written unsatisfiable (F5, F6).
- Best option: **A now; B only prospectively** and only after Architect signature plus independent verification of the proof, the mutants, the other workflow types and the interface legs (F11). C does not apply.

## 6. Test of the Architect's starting position
- Retain record 12: supported. All three members need it as written; item 1 gives AD a negative status, item 2 gives EPD none.
- No waiver: supported. Option B for EPD would not be a waiver only if its decomposed obligations are kept and verified; it must not be presented as closure.
- Accept host-path results only to verified scope: supported with these limits: execute on two masked-host fixtures; claim conditional on 06/11 and instrument-attributed; no pin-export; no independence; mutant coverage limited to D-1 H1; the masked-host limit carried with its correct scope.
- Keep AD and EPD independently unproven: supported, but state the distinction. AD has a sanctioned fallback status. EPD has no fallback, which makes its status "unsatisfied as written" rather than "unproven".
- Use Option B only where a rigorous impossibility proof makes the methodology incompatible with valid runtime invariants: EPD is the only candidate. The proof is not yet rigorous in the required sense (lineage-internal, premises not independently checked, cross-version and other-family gaps). AD should not use B.
- Preserve Q7/Q8: supported. Decomposition (Q7) cannot establish member-specific sensitivity; unqualified lists (Q8) must stay attached.

## 7. Recommended wording fixes (for adjudication text)
1. "STRUCTURALLY UNREACHABLE" becomes "not reachable through supported interfaces at CP 739efe7 under premises P; pin-export legs source-only".
2. "Isolated" for FC-H1 becomes "diff-isolated by scratch-world instrument; claim refusal generic PermissionError, 0 refusals; successor semantics".
3. "Two independent fixtures" for HPD becomes "D-1 Q3-H1 and FC-H2 (distinct families, shared library, same lineage, not organizationally independent)".
4. Correct the contract-coverage EPD row: item 2 has no fallback; do not attribute item 1's fallback.
5. Replace "frozen-literal 03 L23 durable refusal on claim" with "claim issuance is addressed only by 06/11 scope C (adoption pending); 03 L23 names execute and pin-export".
6. Name the claim branch per member (AD: non-journal MINT branch; HPD: journal branch).
7. State that AD execute joint evidence is D-1, not the bounded package, and that no pin-export case was executed for any member.
8. Add "original F3-A: 74 pass / 23 FAIL, unchanged, not rescored; Q2 and Q3 remain OPEN; no independent certification" as a fixed sentence.

## 8. Dissent and what could be wrong with my conclusions
- I did not execute anything, so every "source-only" statement (non-journal MINT branch behavior, pin-export guard-first, mutant predictions) remains inference. The claim-branch correction in F1 rests on source plus the package's own spec text, not on a run.
- My rejection of "graft as valid authority" is an interpretation. If the Architect treats the store writer as inside valid authority, AD execute isolation would be DEMONSTRATED by Q2-A3 on one fixture; claim and pin-export would remain unrun.
- F3(a) cross-version drift is a theoretical valid state I did not build. It may be excluded by ECB versioning (the member carries a version string) that I did not trace.
- R1 as "most natural" is a textual judgment; a reader could prefer R2.
- Worker D's HPD/EPD pin-shape co-movement (host = held) was not independently verified by me.
- All producers and reviewers share one lineage, including me. Nothing here adds independence.

## 9. Confidence and limits
High on the citation checks, counts, hashes and protocol/source identity listed in section 2. High on F1, F5, F7, F13. Medium on F3, F6, F9, F11 (interpretive). Not verified: A19 [eff] and [host] rows; G1/G2/P5; readjudication raw rows; D-1 mutant outputs beyond the verdict text; records 13/14 beyond decision 3 (13 L19) and keyword greps; Python 3.12; CP 8616d5f and main; whether the Architect has acted on records 11/13 after the 2026-10-30 snapshots; the stateful-manifest construction; merge state beyond `git log` showing PR #254 merged at 01c1da1c.

Files: /tmp/claude-0/work/adj/worker-E.md
