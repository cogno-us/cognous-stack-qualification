# 07 F3 architectural technical disposition (OCS-F3-Q240-ARCHITECTURAL-DISPOSITION), 2026-10-30

Final-disposition, append-only record under issue #240. It supersedes the OPEN Q2/Q3 rows of hub records `06` and `07-final-technical-closeout-record` (those remain unedited as history). The file number `07` is the directive's name; it is distinct from the existing `07-final-technical-closeout-record-2026-10-30.md`. In this document "`06`/`11`/`12`/`13`/`14`" without a prefix mean Registry records under `docs/family-migration/final-three/`; the hub custody report is called "hub `06`". Documentation only. No evidence, protocol, oracle, implementation or earlier record is rewritten or re-run. The Q2 and Q3 adjudications below are the lead builder's, prepared from read-only worker analyses and an adversarial review (section 15). **All workers, the producer of the evidence and the adjudicator are one session lineage. This is a scoped technical adjudication under the Architect's interpretation; it is not independent certification.**

Assignment packet (eight fields, Archetype A, verbatim CA01/CA03/CA04/CA18/CA21 cells with task-specific Bindings): `assignments/A-architectural-disposition-OCS-F3-Q240-ARCHITECTURAL-DISPOSITION.json`.

## 1. Architect interpretation and scope
Adopted by the Architect for this bounded technical acceptance decision (directive 2026-10-30, section 2):
- Qualification evidence must demonstrate the contractually required binding, refusal and non-widening behavior.
- Independent end-to-end isolation of every internal binding member is not automatically mandatory unless the governing contract expressly requires it.
- Mechanism-level and decomposed evidence may satisfy a scoped technical qualification where (A) the protected comparison is demonstrated, (B) applicable end-to-end refusal behavior is verified, (C) mandatory admission and authorization guards remain operative, (D) the evidence is source-bound and reproducible, (E) no material contractual obligation is waived, (F) untested behavior is explicitly excluded.
- This does not establish that all internal members can be independently manipulated through naturally reachable production workflows. Historical frozen-oracle results are not reinterpreted. Where the existing contract expressly requires stronger proof, that controls.

This answers the technical-sufficiency question left open in hub `06` ("Narrow Architect decision outstanding"). It does not decide adoption of Registry record `11`, Q7 or Q8. The A-F criteria were stated by the Architect after the D-1 evidence was produced; D-1's own labels ("MET ONLY BY GRAFT", "DECOMPOSED-ONLY") stand unchanged and are what the evidence actually shows.

## 2. Governing contract revisions
- Frozen oracle: Registry `docs/family-migration/final-three/03` (expectation 1: each perturbed member makes execute and pin-export refuse with `authorization_binding_changed` and a durable `EffectTimeRefusal`; expectation 8: replayed scope member must refuse); `02` section 4 rule 2.
- Successor interpretation OCS-F3A-DEV-PE-1-INTERPRETATION/1.0: Registry `06` and `11`. Builder-prepared; human adoption pending (`11` section 7, `13` decision 1). Execute: durable refusal. Pin-export: read-only assessment, state `unknown`, payload None, no durable refusal. Claim issuance: `PermissionError`, no claim, no refusal write.
- Coverage and readiness records `12`, `13`, `14` (builder-authored dispositions, see section 7 and 15).
- Registry main `6b96a9a658923954433dc1a4c13626fa5145b9c7`; execution pin `a40fe755e2384a99c37016fa9ad59396f1835900`.
- Constitution: adopted OCS technical baseline `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`; prospective orchestration convention `dcdbe3b76843d672ca3cfb1f000124ecd78ed03c` (CA clause text byte-identical across `1c2e920`, `230c0af`, `dcdbe3b`; the review-tier label inverts, so criticality is stated as critical/routine). No new revision is activated here (Q8).

## 3. Frozen implementation subject
Control Plane `739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69` (tree `1e7a7555eb3a956fcd2db21d3eb944169d0f7783`, src `d248bde478ae3f2ce050db4637f0c1203066e906`). Control Plane `main` `b19c47ddd020409d24e52e70b11359c46265edbb` is a later head and is not the subject. Interpreter Python 3.11.18 for D-1.

## 4. Evidence provenance and custody
Hub `main` at start: `592d0584b2f4683574d06a13081c038ad7c013f5` (#250). Custody verified in record `06` (all packages PASS, 0 failed checksums). Evidence used for Q2/Q3:

| Evidence | Location (hub, results/third-party/) | Custody |
|---|---|---|
| Original independent F3-A (A19, A25, mutants) | `cp-739efe7-f3-independent-20261029/` (tree `a8e2ff2f5205c0d6334f90112b666de672924ed2`, unchanged) | bundle sha256 `1d07a704…74fc5` |
| Successor readjudication G1 (pin-export), G2 (claim), G5a | `cp-739efe7-f3a-readjudication-20261030/` (#242, merge `2b15604b`) | protocol `04f4f950…9ad6`; 47/47 OK |
| D-1 A25(a)/(e) | `cp-739efe7-f3-q2q3-isolation-20261030/` (#244, merge `d744ecbc`) | protocol `cb2d3ade…f6af`; 52/52 OK; run1/run2 identical (110 rows each) |
| D-2 Q4 M06, Q5 provision | `cp-739efe7-f3-q4q5q6-20261030/` (#245, merge `8de71432`) | protocol `fb314377…1e8a`; 136/136 OK |

## 5. Q2 source-backed adjudication: scope.authority_domain (A25(a))
**Disposition: SATISFIED — SCOPED (conditional: the pin-export and claim legs are satisfied only under the successor interpretation, Registry `06`/`11`, whose human adoption is pending; under the literal frozen oracle the pin-export leg is a FAIL, see section 8)**, at `739efe7` (tree `1e7a7555`), F4 refund fixture, Python 3.11.18, under the Architect interpretation and the conditional successor interpretation.

| Criterion | Result | Evidence |
|---|---|---|
| A Protected comparison | Met | Execute: original A19 `scope.authority_domain` reseal row (6/6 checks, refusal `[authorization_binding_changed]`). D-1 Q2-A3 graft: base binding diff empty, ECB diff exactly the `scope.authority_domain` leaf and digest, refused with exactly `authorization_binding_changed`; mutant D06-M06 makes the graft execute (Q2-A3 9 fails, Q2-A1 4, Q2-A2 1). Classifier level: D-2 Q4b R10 (leaf diff exactly this member, both directions). |
| B Applicable end-to-end refusal | Met for the legs the governing text defines | Execute persisted-side (A19) and live-side by graft (D-1). Pin-export persisted-side under successor semantics: readjudication G1 (state `unknown`, payload None, no `EffectTimeRefusal`, destination untouched; both `739efe7` and `8616d5f`). Claim issuance persisted-side: G2 `PermissionError`, no claim; D-2 Q5 P2 (materialize and provision, Python 3.11 and 3.12). |
| C Guards operative | Met | No guard disabled, patched or bypassed (`d1_lib.py` header; only a clock patch). Graft state validity: base diff empty, d2 control executes, neutral graft executes. Natural routes are refused first by `authority_domain_mismatch` / `manifest_digest_mismatch` / `approval_operation_binding_mismatch`. |
| D Source-bound, reproducible | Met, with caveat | Protocol hash, SHA256SUMS and tree identity verified; run1 = run2. Caveat: D-1 predictions were not blind (probes preceded the freeze) and no independent owner exists. |
| E No material obligation waived | Met | `02` rule 2, `03` L23/L30 and `06` section 3/5 contain no wording requiring natural or isolated live-side end-to-end proof for this member. The original verdict recorded the sub-case as an observation and M06 as a coverage limit; DEV-PE-1 alone drives the original FAIL. |
| F Untested behavior excluded | Met | See exclusions below. |

**Scope wording.** Execute refuses with `authorization_binding_changed` and a durable `EffectTimeRefusal` when the persisted member differs in `scope.authority_domain` alone. Pin-export and claim issuance fail closed for the same persisted-side perturbation under the successor semantics. On the execute path only, the live derivation and comparison are shown sensitive to the authority domain by graft (a genuine foreign-domain member written into a genuine decision).

**Exclusions (not claimed).** Natural end-to-end isolation (every natural live-side route is guard-first or joint). Live-side pin-export and live-side claim-issuance behavior for this member: no evidence. The graft is an unsigned-store write outside the documented threat model and produces a state production never mints; it shows member and derivation sensitivity only. The only mutant (D06-M06) alters derivation; no comparison-side or stamping-side mutant. A14 replay/graft is not authority_domain evidence (its donor differs in `consumer_id`). F4 domain-retargeted world only; not other workflows, `8616d5f`, `main`, Python 3.12 (for D-1) or the real clock.

## 6. Q3 source-backed adjudication: host_profile_digest and effective_profile_digest (A25(e))
**host_profile_digest: SATISFIED — SCOPED (same condition as section 5).** Execute: persisted-side A19 reseal (6 checks) and live-side D-1 Q3-H1 on the F5 class-age masked-host route (class age 60 to 61 overwritten by Registry-narrowed 10): base diff empty, ECB diff exactly `{digest, members.host_profile_digest}`, exactly one durable `authorization_binding_changed`, no attempt, destination unchanged; control Q3-H0 executes. Mutant D1-M14 (host digest := effective digest) killed (H1 then executes; H2 fails 5 checks). Pin-export and claim persisted-side: G1 and G2 pass under the successor semantics at both revisions; D-2 Q5 P4 15 pass on 3.11 and 3.12. Mutant M04 breaks P4 but deletes the whole claim comparison, so it is not host-specific evidence.

**effective_profile_digest: SATISFIED — SCOPED (same condition), decomposed evidence only.** Component: the digest equals an independent commitment of the held profile and equals `catalogue_digest` (Q3-H2; G5a on the pin fixture). Q3-H2 does not vary this member (both worlds share the same effective profile), and Q3-E2 does not check the new live value against an independent commitment, so the component evidence shows consistency, not member-specific live sensitivity. That no isolating case can exist is unproven: the isolating graft was not run (a graft would also move `families.0.effective_policy_digest`). Persisted-side reseal refused on execute (A19), pin-export (G1) and claim (G2; D-2 Q5 P5 15 pass on both interpreters). Live-side on execute: Q3-E1 (approval not re-issued) refuses `runtime_authority_approval_mismatch` only (guard-first); Q3-E2 (re-issued) refuses `authorization_binding_changed` jointly (base diff `{approval_commitment, catalogue_digest}`, ECB diff `{digest, effective_profile_digest, families.0.effective_policy_digest}`), not attributable to the member alone. **No isolated end-to-end effective-profile behavior is claimed.** No mutant on its live derivation was run.

**Q3 combined: SATISFIED — SCOPED (conditional as above)**, because both members are.

Criteria A, C, D, E, F are met for both members on the same basis as section 5 (no guard disabled, E1 shows the approval guard fires first, protocol and checksum verified, `02` section 4 defines the effective digest as equal to `catalogue_digest` so separate isolation is not expressly required, exclusions stated). Criterion B is met for the refusal outcome on execute and, persisted-side, on pin-export and claim.

**Masked-host limit (precise).** Documented in Control Plane `docs/effective-configuration-binding.md` section 10 at `8616d5f` (commit `95fe45f`); absent at `739efe7`, where the text still says "HOST-supplied values" (readjudication check `D2_masked_host_change_limitation_stated` fails at `739efe7`, passes at `8616d5f`). It covers only F4 scalars (`status_max_age_seconds`, `approval_max_age_seconds`) and ObservationPolicy values (`max_age_seconds`, `clock_tolerance_seconds`) narrowed by a Registry family: a host change fully masked by a stricter Registry value is not refused. It does not cover host PROFILE edits, so the F5 class-age route is a profile edit and is not a counterexample to the limit; D-1 gives no evidence about the limit's own cases (only a developer test for ObservationPolicy 300 to 299 under Registry 60; no dedicated F4-scalar test). Registry record `12` item 2 words the limit more broadly than the Control Plane text; the Control Plane text is quoted here.

**Exclusions (not claimed).** One workflow (F5 class-age), one host-edit case, one effective-edit case; Python 3.11.18; pin `a40fe755`. No unmasked-host negative control. Policy-composition, class-unreadable, F4-dedicated and freshness-extension workflows not covered. Live-side evidence is execute only; pin-export and claim have persisted-side evidence on a fixture where host profile equals held profile, so a host/effective swap regression is invisible to those rows. Both D-1 mutants alter derivation only; no comparison-side mutant. Persisted-side rows are store edits outside the documented threat model. Synthetic fixtures.

## 7. Remaining reachability and isolation limitations
1. No member is shown naturally reachable in isolation on any live-side route; authority_domain isolation is by graft only (unsigned store), host digest by one masked-host profile edit, effective digest not isolated.
2. Live-side pin-export and claim legs have no evidence for any of the three members.
3. **Premise of criterion E.** The Architect interpretation (section 1) is what makes decomposed/graft evidence sufficient. Registry record `12` items 1 and 2 (class A, builder-authored from the Architect directive "as reported") ask for "one independent isolation ... run execute and pin-export" and "two independent fixtures", with the fallback status "not independently demonstrated for this member" if not isolable; record `13` reserves the question to the Architect; record `14` section 6 lists the obligations as "none waived" (a status list). The delivered evidence does not meet record `12`'s wording, and for pin-export the graft was isolable and simply was not run, so `12`'s "if not isolable" fallback does not excuse it. This record treats `12`-`14` as coverage and status dispositions, not governing contract text (`02`, `03`, `06` contain no such wording), consistent with the Architect decision. **Both Q2 and Q3 are contingent on that premise.** If the Architect reads `12` as controlling, Q2 and Q3 are OPEN — CONTRACTUAL REQUIREMENT UNMET, with this missing evidence: (a) Q2: a pin-export live-side graft on the pin fixture (d1 member into d2 decision, `assess_authorization_pin`, expect `unknown`/payload None, d2 control active), and claim-issuance parity; (b) host_profile_digest: F5 live-side masked-host cases on pin-export and claim issuance plus an unmasked control; (c) effective_profile_digest: a live-side case isolating it from `catalogue_digest` (if impossible by construction under `02` section 4, that is BLOCKED — CONTRACT AMBIGUITY and the clarification needed is whether such a case is required); (d) a designated independent owner.
4. **Binding standing limits (apply to every persisted-side and graft row).** The store is unsigned; there is no anti-rollback; `legacy_cutoff` is host-supplied; the neutral graft is a state production never mints. Persisted-side perturbation and graft evidence therefore show comparison and derivation sensitivity, not tamper resistance.
5. **Inference, labelled.** Live-side pin-export and claim sensitivity is expected from the shared `GovernedLifecycle._resolve` used by execute, pin-export and claim (source reading at `739efe7`), but no live-side pin-export or claim case was executed. This is inference and is not counted as evidence.
6. **Pin-export is not side-effect-free.** Under record `11` section 8 it is a read-only assessment with respect to authorization and destination, but it records check events (G1 shows 1 resolution check and 13 check events) and writes no `EffectTimeRefusal`.
7. **Refusal pathways not covered by this adjudication:** live-side malformed `configuration_binding_invalid`; legacy and stripped-member acceptance; reconcile and recovery passes; provision branches beyond Q5 (non-journal F4-only, raising provision).
8. **Masked-host text.** The limit is documented only at Control Plane `8616d5f`; this record is bound to `739efe7`, whose source is stated to be code-equivalent by the readjudication and record `11` (AST identity not re-derived here). The limit text is paraphrased in section 6, not quoted.
9. Original M06 survival and the original UNREACHABLE-ISOLATED records are preserved, not rescored. The readjudication verdict describes its session as fresh and independent, whereas hub `07-final-technical-closeout-record` records the same producer lineage; the latter is followed here.
4. Original M06 survival and the original UNREACHABLE-ISOLATED records are preserved, not rescored.

## 8. Original F3-A FAIL preserved
Original F3-A under the frozen literal oracle: **FAIL, DEV-PE-1, 23 failed assertions** (22 pin-export members plus the A06 cutoff0 case). For `scope.authority_domain`, `host_profile_digest` and `effective_profile_digest`, pin-export `reason_names_code` and `durable_effect_time_refusal` are CHECK_FAIL in the original rows (`a4.jsonl` 582-583); the readjudication scored the literal oracle 0/22 on that leg. Unchanged and not re-scored. The pin-export leg of `03` expectation 1 is met only under the successor interpretation, which Registry `06` section 10 item 3 (a new Registry record reconciling `03` L23) has not yet formalized.

## 9. Successor F3-A scoped technical outcome
Conditional scoped technical PASS under OCS-F3A-DEV-PE-1-INTERPRETATION/1.0 (readjudication at `739efe7`: 47 pass / 1 failed test, the documentation-input test G4, which carries three failed doc checks D2, D4b, D4c; Control Plane docs at `739efe7` still describe a durable pin-export refusal and the masked-host limit appears only at `8616d5f`). Conditional on human adoption of record `11`, which is pending. Not formal acceptance.

## 10. F3-B
Scoped technical PASS; not reopened.

## 11. Final Q1-Q8 disposition
| Q | Disposition | Scope |
|---|---|---|
| Q1 | **CLOSED** | Successor evidence custody verified (record `06`). |
| Q2 | **SATISFIED — SCOPED (conditional)** | Section 5. Execute leg: persisted-side and graft evidence. Pin-export and claim legs: persisted-side only, and only under the successor interpretation (record `11` adoption pending); literal frozen-oracle pin-export leg FAILS (section 8). Live-side pin-export/claim: no executed evidence. |
| Q3 | **SATISFIED — SCOPED (conditional)** | Section 6 (host and effective each SATISFIED — SCOPED on the same condition; effective decomposed only, not isolated). |
| Q4 | **CLOSED** | Bounded M06 persisted-content reproduction; does not by itself establish live comparison sensitivity (that rests on D-1). |
| Q5 | **CLOSED** | Scoped governed provisioning (14/14 on 3.11.18 and 3.12.3). Untested: non-journal F4-only branch, raising provision, lock-held sink, live-side drift. |
| Q6 | **CLOSED** | Scoped corrective qualification. Retained: original skipped (1) and failed (6 at `a40fe755`) cases; format test passes only as a path-parameterized one-test copy; verifier `39d46b49` unpinned; freshness-only route not exercised. |
| Q7 | **NOT ESTABLISHED — separate reserved gate** | Formal organizational independence and competent certification. |
| Q8 | **Separate governance decision** | Baseline `1c2e920` preserved; no new revision activated; optional adoption instrument not decided. |

Q1, Q4, Q5, Q6 are not reopened: this adjudication examined them only through the custody report and cited rows and found no indication of a material error; it did not re-audit them.

## 12. Independence and certification limitations
Producer, executing workers, reviewers and adjudicator are one session lineage (producer session `session_01VFvQdn8XjieqzRUfpEtpgy`). ADOPTION.md: independence "cannot be inferred from a second automated process alone". D-1 predictions were not blind. No independent owner, reviewer or certifier has been designated and none is invented. CA06/CA07/CA08/CA23 are applied: results are bound to exact source and interpreter, lifecycle classes are not conflated, and green CI or documents are not qualification. Nothing here is formal independent acceptance of F3-A or certification of any kind.

## 13. Remaining release and production holds
Final independent Tier 1 DEFERRED, NOT WAIVED. Publication, release and production HOLD. Registry #58/#59 HELD. Control Plane #87 HELD. Constructor tolerance NOT AUTHORIZED. Ed25519 #26/#34 HELD. V09 SEPARATE. DEF-OBS-TOL-OVERFLOW-1 OPEN, SEPARATE. R1 production refactoring DEFERRED.

## 14. Outstanding governance decisions
1. Q7: designate a genuinely independent qualification owner and competent certifier (none exists).
2. Q8: decide whether to issue an ADOPTION.md-form instrument for `230c0af`/`dcdbe3b`; baseline `1c2e920` stands meanwhile.
3. Human adoption of Registry record `11` (successor interpretation), on which the pin-export and claim legs of Q2/Q3 and the successor F3-A outcome depend.
4. Confirmation that Registry record `12` items 1-2 are not controlling for this scope (section 7 item 3). Q2 and Q3 are contingent on it; without it they are OPEN as listed there.

## 15. Adversarial review
Worker D (read-only, same lineage, not independent) reviewed the draft and spot-checked about 20 identifiers (merge SHAs, tree ids, protocol hashes, checksum counts, row counts, mutant fail counts) against raw files; all matched except two wording flaws, since corrected (a "quoted here" claim that was a paraphrase, and "1 documented-input failure" hiding three failed doc checks). Verdicts on the draft: Q2 and Q3 each "defensible only with listed edits", neither "should be OPEN/BLOCKED" under the stated Architect rule; OPEN is the correct fallback if record `12` is controlling. Adverse findings preserved and incorporated: (F1) the pin-export leg of `03` expectation 1 is met only through the unadopted successor interpretation and the literal oracle FAILS; (F2) records `12`-`14` ask for isolation incl. pin-export and the contingency on their non-controlling status must be explicit; (F3) the draft's closure and "authoritative" wording overclaimed; (F4) A-F post-dates D-1 labels; (F6) standing unsigned-store limits; (F7) effective-digest component evidence overstated; (F8) M04 not host-specific; (F10) pin-export journals check events; (F11) unlisted refusal pathways; (F12) live-side pin-export/claim is inference, not evidence; (F13) record-number ambiguity and supersession of OPEN rows. Full review: `contract-determinations/q2q3-adversarial-review-2026-10-30.md`.

## 16. Closing statement
**Conditions on this closure (stated first so the sentence below is not read more broadly):** it rests on (1) the Architect interpretation of 2026-10-30, (2) the successor interpretation (record `11`), whose human adoption is pending, and (3) the premise that Registry record `12` items 1-2 are not controlling (section 7 item 3). The original F3-A FAIL stands. Live-side pin-export and claim behavior, natural reachability and isolation of effective_profile_digest are outside the demonstrated scope.

F3 technical qualification is closed within the demonstrated and explicitly bounded scope. This does not constitute formal independent certification or production authorization.
