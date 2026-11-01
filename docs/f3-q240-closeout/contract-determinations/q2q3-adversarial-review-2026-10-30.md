> **SUPERSEDED FOR OPERATIVE PURPOSES (OCS-F3-Q240-CONTRACT-RECONCILIATION):** its verdicts on the earlier draft are preserved; operative Q2/Q3 status is OPEN under Registry record 12 (Class A); see 07 section 0. Original text otherwise preserved.

# Worker D adversarial contract review: OCS-F3-Q240-ARCHITECTURAL-DISPOSITION (draft 07)

Reviewer: Worker D, a read-only subordinate of the same session lineage as the producer. **Not independent.** This review is developer-grade evidence and is not certification. Nothing was run except `sha256sum -c` on four hub packages and read-only parsing of raw JSONL. Nothing was modified. Date 2026-10-30.

Draft under review: `/tmp/claude-0/work/disp/07-f3-architectural-technical-disposition-2026-10-30.md`.
Inputs read: Registry `origin/main` `6b96a9a658923954433dc1a4c13626fa5145b9c7`, records 02, 03, 06, 11, 12, 13, 14 (and 09 for the tier-label claim). Hub clone at `592d0584`: D-1, D-2, readjudication and original packages, hub records 06 and 07, the contract-determinations analysis. Control Plane `739efe7` and `8616d5f` docs. The original bundle was extracted into `/tmp/claude-0/work/disp/rd/orig` for reading.

Naming note: the draft uses "record 06" for two different documents. In s1 and s4 it means hub `docs/f3-q240-closeout/06-final-custody...`. In s2 and s5 it means Registry `06` (the successor interpretation). See F13.

## 0. Bottom line

| Item | Verdict |
|---|---|
| Q2 (scope.authority_domain) | **Defensible only with listed edits.** Blocking: F1, F2, F3. |
| Q3 (host and effective digest) | **Defensible only with listed edits.** Same blockers. The effective-digest half is the weakest and only survives if the wording stops implying member-specific live sensitivity (F7, F8). |
| Neither | Not "not defensible - should be OPEN/BLOCKED" on the stated Architect rule. The OPEN fallback is correct if the Architect treats record 12 items 1-2 as controlling (F2). The draft already says so in s7.3 but does not carry that dependency into its Q-table, headline or closing sentence. |

The numeric and identifier claims I checked are almost all correct (section 4). The problems are conditionality, completeness, wording and overclaim. I found no fabricated identifier.

## 1. Findings

### F1 [BLOCKING] Pin-export durable-refusal leg of frozen expectation 1 is satisfied only through an unadopted, builder-authored successor, and the Q-table drops that dependency

Quote (s11): "Q2 | **SATISFIED — SCOPED** | Section 5. Technical sufficiency under the Architect interpretation only." Same for Q3. Quote (s5 B): "Met for the legs the governing text defines."

Evidence:
- Frozen `03` line 23 requires, for each perturbed member, "execute AND pin-export refuse with `authorization_binding_changed` and a durable `EffectTimeRefusal`". The raw original rows for `scope.authority_domain` pin-export are `runs/A-main4/f3a_evidence.jsonl` lines 582 and 583. `reason_names_code` is CHECK_FAIL and `durable_effect_time_refusal` is CHECK_FAIL with `rows: []`. The same two CHECK_FAILs occur for `host_profile_digest` and `effective_profile_digest` (I counted 4 PASS, 1 OBSERVATION, 2 FAIL for each of the three members). The readjudication re-scored this as 0/22 (`readjudication/verdict.md` line 9). So under the frozen literal oracle the pin-export leg for all three members is a FAIL, and it stays one.
- The only route to "met" is `06` s3.B/s5 (token and durable refusal are "an obligation of the effecting path (A) only"). That is a builder-written document. Its own s9 requires "the Architect's recorded post-review confirmation identifying this exact document revision". Record `11` says it is "prepared by the Lead Builder", records "no Architect signature", and in s7 leaves human adoption PENDING. The readjudication (verdict s2 C and O4) found the confirmation "NOT established from bound sources" and called the outcome CONDITIONAL. `06` s10 item 3 still asks for "a new Registry decision record" to "reconcile or retire the sentence in `03` line 23". No such record exists, so `03` L23 is unreconciled.
- The frozen subject's own docs contradict the successor. At `739efe7`, `docs/effective-configuration-binding.md` line 101 says "REFUSE, durable `EffectTimeRefusal`; execute and pin-export both". The readjudication's S-DOC group fails three checks at `739efe7`: `D2_masked_host_change_limitation_stated`, `D4b_doc_states_no_effect_time_refusal_on_pin_export_claim` and `D4c_no_line_attributes_durable_refusal_to_pin_export`. Only `8616d5f` carries the correction (line 50, "Correction 2026-10-29"). The draft mentions only the D2 half.

Why blocking: Architect rule says SATISFIED — SCOPED only when all applicable obligations are demonstrably supported, and substantive refusal obligations must not be weakened. The successor does not weaken authorization (fail closed, payload suppressed). It does remove the durable refusal evidence from a path the frozen oracle named. That is defensible only as a conditional. The draft states the condition in s2, s9 and s14.3, but not where readers act on it: the Q-table, the s5/s6 headings and the closing sentence.

Fix (exact):
1. Q-table rows Q2 and Q3 scope cell: "Technical sufficiency under the Architect interpretation only. Execute leg: SATISFIED — SCOPED. Pin-export and claim legs: SATISFIED — SCOPED **only conditionally** on OCS-F3A-DEV-PE-1-INTERPRETATION/1.0 (Registry `06`/`11`; human adoption pending; `03` L23 not reconciled by a Registry record). Under frozen `03` L23 read literally the pin-export leg of these members is FAIL (original rows 582-583 for scope.authority_domain, and the same two checks for the host and effective digests) and remains FAIL."
2. s5 and s6 criterion B: replace "Met for the legs the governing text defines" with "Met for the execute leg under the frozen text; met for the pin-export and claim legs only under the successor interpretation (conditional)." The current phrase is circular, because the frozen text defines the pin-export leg with a durable refusal.
3. Add one sentence to s9 and s7: "At 739efe7 the Control Plane docs state the opposite for pin-export (line 101; readjudication S-DOC D4b and D4c fail); the correction exists only at 8616d5f."
4. s9: change "47 pass / 1 documented-input failure" to "47 pass / 1 failed test (G4_S_DOC: three failed doc checks D2, D4b, D4c)". Source: `readjudication/raw/739efe7/stdout.txt:49,56`, 3 CHECK_FAIL rows in `readj_evidence.jsonl`.

### F2 [BLOCKING until stated] Record 12 items 1-2, 13 decision 3 and 14 "none waived": the treatment is defensible, but the draft contradicts itself and omits the missing-evidence list it promises

Reading them myself:
- `12` item 1 (class A, "Stays inside the acceptance boundary", outcome UNVERIFIED): "Needs one independent isolation (decision under domain X, live side rebuilt under domain Y, all else equal, run execute and pin-export). If not isolable, status is 'not independently demonstrated for this member'."
- `12` item 2 (class A): "Two independent fixtures needed; state the masked-host limit alongside." Item 2 has no fallback status.
- `12` header says its basis is the Architect directive "as reported". The directive text is not in any repository. `12` is builder-authored. The risk statement says only items 1-2 map to an explicit oracle requirement.
- `13` decision 3 lists "Whether items 1 and 2 of `12` ... must be independently demonstrated before acceptance" among decisions that "remain with the Architect or the certification authority".
- `14` s6: "Outstanding obligations ... none waived" and "Formal independent acceptance NOT ESTABLISHED". It is a status list and contains no accepted-limits section.

Are they "existing contract expressly requiring stronger proof"? My reading: no. They are a builder-authored coverage classification, with a stated non-isolable fallback for item 1. The class-A label is not traceable to Architect wording. `13` and hub `06` both say the question is still the Architect's. "None waived" is consistent with discharge by adjudicated evidence, as opposed to waiver. The frozen `02`/`03`/`06` contain none of the words isolated, natural, reachable or end-to-end (`contract-determinations/q2q3-contract-mandatoriness-analysis.md` s1, which I re-checked against `03` L23, L30). `03` L30 itself prescribes a replay or graft for the scope member. So treating `12` as non-governing is defensible under the Architect's rule.

But the draft is not safe as written, for four reasons:
(a) It asserts criterion E "Met" using only `02`, `03` and `06`, and never addresses `12`, `13` or `14` in the E row. E is only "met" on the premise that `12` is not governing. E should say so.
(b) s7.3 says that if `12` controls, Q2 and Q3 "revert to OPEN with the missing evidence stated in section 15". Section 15 states nothing; it is a pointer to a review "appended below" that does not yet exist in the file. The missing evidence appears nowhere in the draft.
(c) s14.4 asks the Architect to confirm that `12` items 1-2 are superseded. That means the label is contingent on an open decision, yet the Q-table is unconditional.
(d) `12` item 1's fallback ("not independently demonstrated for this member") applies "if not isolable". The pin-export leg of authority_domain is isolable. The same graft construct was simply never run on pin-export (D-1 verdict s7: "pin-export and claim paths ... not covered"). So the fallback label does not excuse the pin-export gap. It is an unrun test, not an unreachable one.

Fix (exact):
- Add to the E row of s5 and s6: "E is met on the premise that Registry `12` items 1-2 (builder-authored class A coverage dispositions, directive 'as reported', not in repository) are not governing contract text. `12` item 1 asks for 'one independent isolation ... run execute and pin-export'. The delivered evidence is graft-only, execute-only and non-independent, and `12` item 2 asks for 'two independent fixtures', which the delivered evidence also does not meet as worded. If the Architect treats `12` as controlling, E is not met."
- Replace s15 so that, before the appended review, it carries a "Missing evidence if 12 controls" list:
  1. authority_domain: one pin-export graft (d1 member over d2 pin-fixture decision, expect state not active, payload None, base diff empty, d2 control active) and a claim parity run. Neither was executed.
  2. host_profile_digest: live-side masked-host case on pin-export and claim, an unmasked-edit control, and policy-composition and class-unreadable workflows.
  3. effective_profile_digest: no isolating live-side construction was executed. D-1 REVIEW-ADDENDUM item 2 says the stated reason for not grafting was wrong and that the graft "was not run". Whether the case is unsatisfiable by construction is unproven.
  4. A designated independent owner (Q7).
- In the Q-table, mark Q2 and Q3 "contingent on Architect confirmation that Registry `12` items 1-2 do not control (s14.4)".
- Optional cheap closure (not for this record): the one pin-export graft in item 1 removes the sharpest point.

### F3 [BLOCKING] Closing sentence, header and "closes" claims overclaim

Quotes:
- s16: "F3 technical qualification is closed within the demonstrated and explicitly bounded scope."
- Header: "Authoritative, append-only record".
- s1: "This closes the single 'narrow Architect decision' left open in record `06`."

Evidence:
- F3-A under the frozen oracle is FAIL (23 assertions), and the successor outcome is conditional (draft s8 and s9). The records the draft itself cites say "Formal independent acceptance NOT ESTABLISHED" (`14` s1), "Level 5 and 6 NOT ESTABLISHED" (`13`), and Tier 1 "DEFERRED, NOT WAIVED". Hub `06` s8 records the Q6-A frozen expectation as "not met (13/14)" in the custody table (hub `06` s3, row #246), and the draft's Q6 row omits that.
- The adjudications are by the lead builder lineage (draft s12). Calling the record "Authoritative" and the qualification "closed" implies finality that a non-independent, conditional, Architect-pending record cannot carry. Hub `06` s9/Narrow decision says Q2 and Q3 "stay OPEN" until the Architect rules. The draft's own s14.3 and s14.4 leave two Architect decisions outstanding.
- "Closes the narrow Architect decision": the Architect supplied an interpretation (A-F, relayed; text not in repo). Applying A-F to the evidence is the builder's act. The builder cannot close the Architect's decision.

Fix (exact):
- s16: "Technical dispositions for Q2 and Q3 are recorded above within the demonstrated and explicitly bounded scope, conditional as stated in s7 and s14. The original F3-A FAIL stands; the successor F3-A outcome is conditional; no independent acceptance, certification, Tier 1 qualification or production authorization exists or is implied."
- Header: replace "Authoritative, append-only record" with "Append-only builder-lineage record".
- s1 last line: "This supplies the interpretive rule for the decision left open in hub record 06. The application of that rule to Q2 and Q3 below is the lead builder's, is not independent, and awaits Architect review (s14)."

### F4 [MUST-FIX] The A-F interpretation is cited to a directive that is not in any repository, and it post-dates the evidence

Quote (s1): "Adopted by the Architect for this bounded technical acceptance decision (directive 2026-10-30, section 2)".

Evidence: the contract-determinations analysis s5 and s0.2 note that the Architect directive texts are not in the repository. Hub `06` s8 says of Q3 "Contract does not expressly accept decomposition; no retroactive criteria change". D-1 was designed before A-F and labelled its own results "MET ONLY BY GRAFT" and "DECOMPOSED-ONLY ... NO isolated claim".

Fix: add to s1: "The directive text is relayed to the lead builder and is not filed in any repository; criteria A-F are reproduced from that relay. They post-date the D-1 evidence, so this is a prospective application to existing evidence, not a retroactive criteria change by the evidence producers. D-1's own labels ('MET ONLY BY GRAFT', 'DECOMPOSED-ONLY', permitted wording 'isolated end-to-end by GRAFT ... not a natural-reachability claim') remain in force and are not upgraded by this record."

### F5 [MUST-FIX] s7.1 misstates the host digest result, and the natural-reachability wording is inconsistent in both directions

Quote (s7.1): "No member is shown naturally reachable in isolation on any live-side route; authority_domain isolation is by graft only (unsigned store), host digest by one masked-host profile edit, effective digest not isolated."

Evidence: D-1 verdict s1 and s2.1 say the host digest was **MET on a natural supported route** (Q3-H1: base diff empty, ECB diff exactly `{digest, members.host_profile_digest}`, one durable refusal; the harness check list is in `raw/739efe7-run1`). The draft's own s6 says so. The first clause of s7.1 contradicts s6 and understates host. Separately, the draft never says that the host route is a masked profile edit that leaves the effective profile unchanged, so a reader could infer the refusal reflects an authority change; it does not (the profile is identical).

Fix (exact s7.1): "Reachability in isolation on a live-side route: authority_domain, none (graft only; every natural route is guard-first or joint). host_profile_digest, one supported host-profile edit fully masked by Registry composition, on the F5 class-age execute path only; the effective profile is unchanged by that edit. effective_profile_digest, not isolated (guard-first or joint)."

### F6 [MUST-FIX] Standing limits of the binding are not stated, so persisted-side and graft evidence reads as tamper resistance

Evidence: `03` expectation 9 requires honest limits: unsigned store, no anti-rollback, host-supplied cutoff, mixed-fleet legacy writers. CP docs s10 (lines 153-154): "No anti-rollback guarantee ... A→B→A revives an old decision", "The `legacy_cutoff` is host configuration ... Below the cutoff a stripped member is indistinguishable from a legacy record", and an editor of the store "defeats the check". The original verdict (line 37) observed "a store writer can re-seal a member". The draft's Q2 section names the graft as unsigned-store, and Q3 s6 names persisted-side rows as store edits. The draft states none of anti-rollback, legacy-cutoff bypass, or the neutral-graft fact. The neutral-graft control shows a store writer who writes a matching member executes without refusal.

Fix: add a short s5/s6 exclusion line and an s7 item: "The binding is drift detection, not tamper protection. A writer to the unsigned store can write a matching or resealed member and the decision executes (D-1 neutral-graft control; original reseal rows). There is no anti-rollback (A→B→A revives an old decision). `legacy_cutoff` is host-supplied; below the cutoff a stripped member is accepted as legacy, so member-level refusals apply only to present members at or past the cutoff. Nothing here claims anti-rollback, tamper resistance, or enforcement against a store writer."

### F7 [MUST-FIX] Effective-profile digest: the "Component" evidence is described more strongly than it is, and the E rationale is a non sequitur

Quotes (s6): "Component: digest equals an independent commitment of the held profile and equals `catalogue_digest` (Q3-H2; G5a on the pin fixture)." and "`02` section 4 defines the effective digest as equal to `catalogue_digest` so separate isolation is not expressly required".

Evidence:
- Worker C s3 states both Q3-H2 worlds share the same effective profile (masked), so H2 does not vary this member. G5a holds one value on the pin fixture. E2 does not assert the new live digest against an independent commitment of the new profile (worker C s6 item 4).
- D-1 REVIEW-ADDENDUM item 2: the stated reason for not grafting was wrong (a graft leaves the base binding unchanged). What defeats isolation is that the ECB diff also moves `families.0.effective_policy_digest`. The graft "was not run". Worker C's claim that a live-side isolated case "cannot exist" is source reasoning, not evidence.
- `02` s4 only says the member "equals `catalogue_digest` for profile-bearing workflows, else null". It does not speak to isolation. The inference that isolation is not required is the Architect-interpretation inference, not a `02` statement.
- "No mutant on its live derivation was run" is in the draft. The "outcome-equivalent" claim (D-1 verdict s2.3) is source reading, not execution (REVIEW-ADDENDUM item 5).

Fix: (i) s6: "Component: equality at a single value in two worlds that share the same effective profile (H2 does not vary this member); E2 does not check the new live value against an independent commitment." (ii) s6 E clause: "Isolated live-side proof is not expressly required by `02`/`03`/`06`; `02` s4 defining the member as equal to `catalogue_digest` explains why no natural isolating route is expected but does not by itself establish that none exists (the isolating graft was not run)." (iii) add: "A regression that drops this member from the live derivation would, by source reading only, change no live-side outcome; it would also pass every executed test."

### F8 [MUST-FIX] Mutation evidence is cited in a way that implies member-specific comparison coverage

Quotes: s6 host: "M04 breaks P4." s5 scope wording: "the live derivation and comparison are shown sensitive to the authority domain".

Evidence: D06-M04 is the original whole-comparison mutant "local-claim-issuance-compare-deleted". In D-2 R12 it makes P1, P2, P3, P4, P5, P7, P8 and P9 each fail 5 checks (verified by counting rows), so it is not specific to the host member. Both D-1 mutants alter live derivation only (D-1 verdict s5, REVIEW-ADDENDUM item 5). Comparison sensitivity for each member rests on the persisted-side A19, G1, G2 and Q5 rows plus pristine controls, not on a per-member comparison kill.

Fix: s6: "M04 (whole claim-comparison deletion) breaks every Q5 perturbation row, host row included; it is not member-specific." s5 scope wording: "the live derivation is shown sensitive to the authority domain by the M06 kill; comparison sensitivity for this member rests on the persisted-side rows and the graft refusal. No comparison-side or stamping-side mutant was run."

### F9 [MUST-FIX] Masked-host limit: the text "is quoted here" is false, and the limit is bound to the wrong revision for a 739efe7 record

Quote (s6): "the Control Plane text is quoted here."

Evidence: s6 paraphrases the text; it does not quote it. The CP text at `8616d5f` s10 (line 158) is not reproduced. The limit text is absent at `739efe7` (which still says "HOST-supplied values", line 157). Record `12` item 2 asks to "state the masked-host limit alongside", and the draft's disposition is bound to `739efe7`. Stating the limit by reference to `8616d5f` docs is a CA07 revision transfer unless labelled. Record `12` item 2's phrasing is broader than the CP text, which the draft correctly notes.

Fix: either quote the line-158 sentence verbatim ("A change in the host configuration that is completely masked by a stricter effective Registry value may not change the effective-configuration binding and therefore may not cause refusal ... applies only where the workflow's F4 scalars ... or ObservationPolicy values ... are narrowed by a Registry family and a host change leaves every effective value and every declared family's effective-policy digest unchanged") or change "is quoted here" to "is paraphrased here". Add: "The limit is documented only at 8616d5f (code-equivalent per the readjudication AST check and record `11`); at the frozen subject 739efe7 it is undocumented, which the original verdict recorded as a documentation gap. It is stated here from the 8616d5f text and is not a 739efe7 documentation fact."

### F10 [MUST-FIX] "Read-only" description of pin-export, and the pin-export wording, omit the journaling the interpretation itself clarified

Quote (s2): "Pin-export: read-only assessment, state `unknown`, payload None, no durable refusal."

Evidence: record `11` s8 and `06` s5/s10 item 2: pin-export keeps "existing resolution-check journaling" and the successor "does not describe pin-export as 'writing nothing'". G1 shows the writes: `check_events` delta 13, `resolution_checks` delta 1 (raw G1 row, `readj_evidence.jsonl`). The readjudication G1 states P6 "no authorization-state write (only check_events, resolution_checks changed)".

Fix: "Pin-export: non-authorizing assessment, state `unknown`, payload None, no `EffectTimeRefusal` and no authorization-state write; existing `ResolutionCheck` and `check_events` journaling still occurs (G1: 1 resolution check, 13 check events on the authority_domain row)."

### F11 [MUST-FIX] Missing-refusal-pathway disclosure is thin

The draft names execute, pin-export and claim issuance. Not mentioned and not evidenced for these members:
- the live-malformed path (CP docs s8 line 127: `configuration_binding_invalid` pre-write adapter refusal, and `configuration_binding_status` raising `BindingInvalid`), which is a different refusal code from `authorization_binding_changed`;
- the legacy and missing-member path (F6);
- reconcile and recovery passes (record `11` s8 lists recovery-pass interaction as unverified; the original verdict notes `reconcile()` is not guarded against post-construction `observation_policy` mutation);
- the non-journal `provision_local_execution_claim` branch, a raising provision and a lock-held sink (the Q5 row names these);
- live-side pin-export and claim for every member (the draft does state this in s7.2).

Fix: add to s7: "Refusal pathways not evidenced here: live-malformed configuration (`configuration_binding_invalid`), legacy or stripped-member acceptance below the cutoff, reconcile and recovery passes, and the non-journal, raising and lock-held-sink provision branches."

### F12 [MUST-FIX] Live-side pin-export and claim inference: the draft says "no evidence" but omits the source-level shared-`_resolve` argument that would justify B, and does not mark it as inference

Evidence: CP docs s3 line 50 (both revisions): pin-export and claim "re-resolve through `workflow._resolve`, so the one override covers both; a test pins each." Worker C s3 lists the call sites (`bounded.py:1685`, `authorization_pin_export.py:170`, `local_authority_effect.py:443`). `02` rule 2 says pin-export "recompute[s] the live member and compare[s]". Persisted-side G1/G2 do exercise recompute-and-compare on those paths. What they cannot show is live-derivation sensitivity (the M06 gap).

Fix: s5 B and s6 B: "Live-side derivation sensitivity is demonstrated on execute only. For pin-export and claim it is inferred from the documented shared `_resolve` (CP docs s3), which is source reading, not execution. No live-side pin-export or claim run exists for any of the three members." This keeps criterion B honest and states the actual mechanism-level basis the Architect rule permits.

### F13 [MUST-FIX] Ambiguous "record 06", and unlisted supersession of earlier OPEN dispositions (CA06)

Quotes: s1 "left open in record `06` (section 'Narrow Architect decision outstanding')" is hub record 06. s2 "Registry `06` and `11`" and s5 E "`06` section 3/5" are the Registry successor interpretation. s4 "Custody verified in record `06`" is hub record 06 again.

Evidence: hub `06` s8 records Q2 and Q3 as OPEN; hub `07` (merged #248) records "OPEN, contract AMBIGUOUS". The draft changes these to SATISFIED but never says it supersedes them. CA06 (the draft invokes it) requires supersession to be retained. Hub `06` s3 custody ran at `247d46ce` and the draft's "Hub main at start `592d0584`" is a later head. I re-verified `sha256sum -c` on all four relevant packages at `592d0584` (47, 52, 136 and 4 OK, 0 failed) and an empty diff of the original-bundle path between `247d46ce` and `592d0584`.

Fix: write "hub record 06" and "Registry 06" everywhere. Add to s1: "This record supersedes, without rewriting, the Q2 and Q3 dispositions in hub records 06 (s8: OPEN) and 07 (s6: OPEN, contract AMBIGUOUS)."

### F14 [NOTE] Reproducibility criterion D understates caveats

Quote (s5 D): "Met, with caveat ... not blind ... no independent owner."

Additional caveats from D-1 and the hub: mutant trees and per-case stores not retained (diffs retained); `run_d1.sh` embeds absolute paths; the A19, G1, G2 and Q5 rows were reused by citation in D-1 and not rerun by D-1 (they were re-scored from raw rows in the readjudication, which is a different run); `compat_probe.py` is not committed in #242 (hub `06` s4, "not cosmetic for reproducibility", affects G6 and not Q2/Q3 directly); the d2 world is built by string-retargeting the synthetic resolver, approvals included (`d1_lib.py:176-211`), so "genuine d2 world" means synthetic fixture. Run1 equals run2 only after removing timestamps and labels (I confirmed: identical after dropping `t` and `label`).

### F15 [NOTE] Q1, Q4, Q5, Q6 "no evidence of material error" is outside the evidence reviewed

s11: "Q1, Q4, Q5, Q6 are not reopened (no evidence of material error)." I verified Q1 custody and the Q5 P-row counts only. I did not review Q6. Hub `06` s3 and s8 record, for Q6: Q6-A frozen expectation "not met" (13/14), Verifier `39d46b49` unpinned, a format test that passes only as a modified copy. The draft's Q6 row lists the last two but not the 13/14. Suggested wording: "not reopened by this record; not re-reviewed here".

### F16 [NOTE] Independence statement: produced-by wording conflicts with the readjudication's self-description

The readjudication verdict states it was written by a "fresh Claude Code session ... acting as independent_qualification_owner"; record `14` s5 says it came "from the fresh AI qualifier session". The draft, following hub `07` s4 ("producer = lead builder session"), says the whole chain is one lineage. The conservative reading is right and consistent with ADOPTION.md, but the draft should say "per hub record 07 s4; the readjudication verdict describes itself differently and neither is an independence designation". The draft's session identifier cannot be verified from the files cited.

### F17 [NOTE] Hub naming

The draft is numbered "07", while hub `docs/f3-q240-closeout/07-final-technical-closeout-record-2026-10-30.md` already exists. If filed in that directory, rename (for example `08-`). If filed in the Registry `final-three` directory, record `07` there is the readjudication handoff.

## 2. Challenge-by-challenge answers

1. **Weakening of frozen `03` exp. 1.** The draft does not rewrite or rescore it and preserves the FAIL (s8). The disposition nevertheless relies on the successor to treat the pin-export leg as satisfied, which is conditional on an unadopted record. This must be visible in the Q-table (F1). I found no hidden weakening of the execute leg.
2. **Record 12 / 14.** Not governing contract text on the available evidence, but the draft must say E rests on that premise, list the missing evidence, and mark the label contingent (F2). The OPEN fallback is the right outcome if the Architect reads `12` as controlling.
3. **Evidence transfer.** Persisted-side rows are used for live-side claims nowhere explicitly, but live-side pin-export and claim derivation sensitivity is implied by B without the inference being labelled (F12). `8616d5f` evidence (G1, G2, S-DOC D2) appears alongside `739efe7` evidence and the doc limit is a `8616d5f` fact (F9). Python: D-1 is 3.11.18 only and the draft says so; Q5 uses 3.12.3 additively.
4. **Missing refusal pathways.** F11, F12.
5. **Unsupported statements.** Section 4 below. The two I found: "is quoted here" (F9) and "1 documented-input failure" (F1).
6. **False natural-reachability.** F5 (host understated; masked-edit semantics unstated). Authority_domain wording is correct.
7. **Unsigned-store limits.** F6.
8. **Overclaims.** F3, plus "Authoritative", plus "closes the narrow Architect decision".
9. **Contradictions with record 06 and the preserved FAIL.** Hub `06` says Q2 and Q3 stay OPEN "until ruled" and that the contract "does not expressly accept decomposition" (F4, F13). Registry `06` s5 and s7 are consistent with the draft except that s7 says the interpretation "can support a new verdict only through independent readjudication by a fresh qualifier"; the draft's own adjudication is non-independent, which it states. The preserved original FAIL is accurately recorded (23 assertions: 22 pin-export plus A06 `pin:cutoff0_idx0`, 46 CHECK_FAILs in A-main4).

## 3. Verdicts

- **Q2: defensible only with listed edits.** Required: F1, F2, F3, plus F4, F6, F8, F10, F12, F13. Sustainable label after edits: "execute leg SATISFIED — SCOPED (persisted-side and graft); pin-export and claim legs conditional on the successor interpretation; contingent on Architect confirmation that Registry `12` item 1 does not control". If the Architect holds `12` item 1's "run execute and pin-export" as controlling, the correct label is OPEN with the missing evidence in F2.
- **Q3: defensible only with listed edits.** Same required edits, plus F5, F7, F9. host_profile_digest is the strongest member (natural supported route, kill-confirmed, one workflow, execute only). effective_profile_digest is acceptable only as "decomposed evidence, no member-specific live sensitivity shown" under the Architect's explicit allowance for decomposed evidence. Q3 combined must read as the weaker of the two. If `12` item 2 ("two independent fixtures") controls, Q3 is OPEN.

## 4. Spot-check ledger (identifiers, counts, hashes against raw files)

| # | Draft claim | Raw check | Result |
|---|---|---|---|
| 1 | Hub main `592d0584b2f4683574d06a13081c038ad7c013f5` (#250) | clone HEAD and `git log` | match |
| 2 | Merge SHAs `2b15604b` (#242), `d744ecbc` (#244), `8de71432` (#245) | `git log --merges` | match |
| 3 | Registry main `6b96a9a658923954433dc1a4c13626fa5145b9c7` | `git rev-parse origin/main` | match |
| 4 | CP tree `1e7a7555eb3a956fcd2db21d3eb944169d0f7783`, src `d248bde478ae3f2ce050db4637f0c1203066e906` | `git rev-parse 739efe7^{tree}` and `:src`; CP main `b19c47dd...` | match |
| 5 | Original bundle tree `a8e2ff2f5205c0d6334f90112b666de672924ed2` unchanged | `rev-parse HEAD:path`; empty diff `247d46ce`..`592d0584` | match |
| 6 | Protocol sha256 `04f4f950…9ad6`, `cb2d3ade…f6af`, `fb314377…1e8a` | `.sha256` files | match |
| 7 | Checksums 47/47, 52/52, 136/136 OK | `sha256sum -c` (I ran it) | match; original bundle 4/4 OK |
| 8 | D-1 run1/run2 identical, 110 rows each | `wc -l`; parsed with `t` and `label` removed | match |
| 9 | Q2-A3 9 fails, Q2-A1 4, Q2-A2 1 under D06-M06 | parsed `M06/d1_evidence.jsonl` | match |
| 10 | D1-M14: H2 fails 5; H1 then executes | parsed `M14`: Q3-H1 8 CHECK_FAIL, Q3-H2 5, Q3-E2 1 | match |
| 11 | Original A19 execute rows: 6 checks PASS for authority_domain | A-main4 lines 572-577; host and effective also 6 PASS | match |
| 12 | `D2_masked_host_change_limitation_stated` fails at 739efe7, passes at 8616d5f | `raw/739efe7/stdout.txt:49`; verdict s2 A24 row | match (but D4b and D4c also fail, F1) |
| 13 | "47 pass / 1 documented-input failure" | `stdout.txt:56` "1 failed, 47 passed"; 3 CHECK_FAIL rows | count right, characterization incomplete |
| 14 | D-2 Q5 P2/P4/P5 15 pass on 3.11 and 3.12; M04 breaks P4 | R10, R11 parsed: 15 each; Python 3.12.3 in `invocation.txt`; R12 | match; M04 breaks all P rows (F8) |
| 15 | Masked-host limit at CP `8616d5f` s10, commit `95fe45f` | doc heading `## 10` line 150, text line 158; `95fe45f` is an ancestor of `8616d5f` | match; "quoted here" false (F9) |
| 16 | Constitution CA clauses byte-identical across `1c2e920`, `230c0af`, `dcdbe3b`; tier label inverts | Registry `09` lines 5 and 94 | match |
| 17 | Original FAIL: 23 failed assertions (22 pin-export plus A06 cutoff0) | verdict line 17; A-main4: 46 CHECK_FAIL | match |
| 18 | A14 donor differs in `consumer_id` | worker B citing harness line 1020 (not independently re-read by me) | accepted from worker B |
| 19 | Q5 14/14 on 3.11.18 and 3.12.3 | hub `06` s8 | match (not re-parsed beyond P-rows) |
| 20 | Registry `12` item 2 "words the limit more broadly" | `12` item 2 versus CP line 158 | correct |

Not verified by me: criteria A-F text and the Architect directive (not in repo); the session identifier; the Q6 row; A14 line citation; D-2 Q4b R10 leaf-diff semantics beyond row counts.

## 5. Preserved adverse findings

The adverse items above are reported as found and not softened. The strongest, in order: (1) the literal frozen pin-export leg is FAIL for the three members and the draft's SATISFIED depends on a builder-prepared, unadopted interpretation (F1); (2) record 12 item 1 expressly asks for pin-export isolation and the corresponding graft was never run (F2); (3) the closing sentence and "Authoritative" header overstate what a non-independent, conditional record can claim (F3).
