# Worker D reconciliation review (read-only; same lineage as author, NOT independent)
Subject: docs/f3-q240-closeout/07-f3-architectural-technical-disposition-2026-10-30.md (working tree, branch docs/f3-architectural-technical-disposition-20261030, 147 lines). Controlling source: Registry record 12 (origin/main, 27 lines).

## Overall verdict: PUBLISHABLE WITH LISTED FIXES (no blocking defect; fixes are wording/annotation)

## (1) Q2/Q3 OPEN in every authoritative status statement: PASS (with annotation fixes)
Operative statements, all OPEN: L6 (section 0 "SUPERSEDED for operative acceptance purposes"), L10-11 (table, exact "OPEN — REQUIRED ISOLATION NOT FULLY DEMONSTRATED"), L31, L98 (7.3), L119-120 (Q-table), L147 closing.
Remaining SATISFIED / Met occurrences (all in sections 5-6, each under a heading or label that says SUPERSEDED; operative OPEN):
- L66 / L82 section headings: "SUPERSEDED for operative purposes; operative status is OPEN" - clearly marked.
- L67, L83, L85, L87: "SATISFIED — SCOPED" each prefixed "Analytical label (SUPERSEDED; operative status OPEN)" - clearly marked.
- L71-76 criteria table (A-F "Met"), L89 "Criteria A, C, D, E, F are met for both members": NOT individually marked; covered only by the section heading. Adverse: L75 (E, "No material obligation waived: Met", resting on "contain no wording requiring natural or isolated live-side ... proof") is exactly the reasoning record 12 / Architect rejected, and 03 L23 ("every member perturbed independently ... execute AND pin-export refuse") arguably is such wording. L72 (B "Met").
- L110 section 9 "Conditional scoped technical PASS": qualified ("without full Class A acceptance ... not overall F3-A technical acceptance ... Not formal acceptance") but not marked analytical; a bare "PASS" in a status section.
- L113 "F3-B Scoped technical PASS" - consistent with records 13/14; fine.
- L41 "may satisfy a scoped technical qualification": inside section 1, marked SUPERSEDED in heading L37.
- L118/121-123 "CLOSED" are Q1/Q4/Q5/Q6, not Q2/Q3; fine.
- Uncommitted/committed worker files still carry unmarked SATISFIED: contract-determinations/q2-adjudication-worker-b (L5 "LABEL: SATISFIED - SCOPED", L74), q3-adjudication-worker-c (L10-12), q2q3-adversarial-review (L16, 24, 198-199 "defensible only with listed edits", "OPEN fallback correct if 12 controlling"). L13 of 07 covers "a worker analysis it cites" generically, but the files themselves have no banner.

## (2) Record 12 controlling; crosswalk accuracy: PASS
Verified against record 12 text: classes legend (L16 vs rec12 L3) exact; "No UNVERIFIED outcome is converted to PASS" exact; item 1 quote (rec12 L8) exact, class A, UNVERIFIED; item 2 quote "Two independent fixtures needed; state the masked-host limit alongside." exact, A, UNVERIFIED; item 3 class "C (becomes B only if it maps to a required oracle member)" - paraphrased correctly, disposition "Record both outcomes side by side ... No new campaign" correct; item 4 "C for members unreachable...; F4-reachable members remain in A (items 1, 2)" correct. L25: rec13 decision 3 and rec14 section 6 ("none waived") correctly characterised. Gap (minor): crosswalk covers items 1-4 only; items 5 (Py3.12, B), 6, 7 (claim provision, B), 8 omitted although Q5/Q6 are marked CLOSED. Rec12 item 5 says record "independently qualified on 3.11 only" and defers; 07 Q6 "CLOSED ... scoped corrective qualification" by same lineage is not reconciled to that wording.

## (3) No refusal pathway described as qualified without evidence: PASS
Pin-export/claim live-side: L20 (not demonstrated), L21, L80 (no evidence), L93, L97 (7.2), L100 (inference labelled, "not counted as evidence"), L72 persisted-side only and labelled. effective_profile_digest "No isolated end-to-end ... claimed" L85. Residual: L72 B-row "Met" reads strongly though superseded.

## (4) Successor vs original oracle: PASS
L47-48 separate bullets; L67 and L107 state literal oracle FAIL / pin-export met only under successor interpretation, adoption pending (rec 11 section 7). L110 and L138 retain "pending". No place conflates 03 with 06/11.

## (5) Historical FAIL preserved; no overall F3-A acceptance: PASS
L13, L107 (DEV-PE-1, 23 = 22 + A06 cutoff0), L110 "this is not overall F3-A technical acceptance", L147.

## (6) No formal certification: PASS
L31 bold disclaimer, L124 Q7 NOT ESTABLISHED, L130, L133, L147.

## (7) Documentation-only: PASS
git diff origin/main --name-status: 5 additions, all docs/f3-q240-closeout (07 .md, assignments/A-*.json, three contract-determinations .md). Working tree adds uncommitted modification of 07 and untracked assignments/C-*.json. No source/schema/test/workflow/executable. C JSON parses (python -I json.load OK), top keys schemaVersion..governance; clauses = CA02, CA04, CA06, CA07 (one each). CA04/CA06/CA07 required/prohibited text byte-matches record 03 table; CA02 text not verifiable from available sources (not in 03). Note: C JSON and the 07 edits are not yet committed; PR head 2967d0bf does not contain them.

## Closing statement: PASS - exact string present once, as last paragraph (programmatic comparison True).

## Forbidden by Architect section 5
- Absence of natural-path requirement cancelling isolation: stated correctly forbidden at L27; but L75 and L89 (superseded sections) still make that argument without an inline rebuttal. Not operative, but fix below.
- Manufacturing reachability: L27 disclaims; no guard disabled (L73 says so for the earlier D-1 work); no new execution. PASS.

## Stale text / contradictions / glitches
- No occurrence of "conditional on premise that record 12 is not controlling" in 07. The word "conditional" (L67, L83, L85, L87, L110) now refers to successor-interpretation adoption only - correct, but L87 "(conditional as above)" is easy to misread.
- L144 (15.1) still says "neither should be OPEN/BLOCKED under the stated Architect rule", "OPEN is the correct fallback if record 12 is controlling", and F2 "contingency on their non-controlling status must be explicit": historical, but unresolved in place - reader may think contingency remains open. Also section 15 header is plural but has only 15.1; no 15.2 records the reconciliation review the C packet promises (C JSON CA04: "a read-only reviewer ... checks the seven acceptance points").
- L31 calls the record "append-only" though section 0/0.1 were prepended and sections rewritten pre-merge; acceptable pre-merge, but say "append-only after merge".
- L33/L35 two assignment-packet paragraphs: the A packet is described as the disposition packet, the C packet as reconciliation; fine, but L35 ordering follows C; cosmetic.
- L44 states A-F criteria post-date D-1 evidence; good.
- L121 Q4 "that rests on D-1": D-1's live-side graft is the evidence now deemed insufficient for Q2; add "(which does not discharge Q2)".
- L9 header line 2 "Corrected by" fine.

## Recommended exact fixes
1. Insert directly under L69 table heading (and before L89): "**Criteria results in this table are the SUPERSEDED analytical assessment. Row E in particular is overridden: Registry record 12 items 1-2 (Class A) are explicit independent-isolation obligations, and absence of a natural-path requirement does not cancel them (section 0.1).**"
2. L75, append: " [SUPERSEDED: record 12 Class A items 1-2 are the express requirement; E is NOT met for operative purposes.]"
3. L110: change to "Reported conditional scoped technical outcome (not an operative acceptance status): scoped technical PASS on the demonstrated behavior ...".
4. L144: append "Resolved: the Architect later ruled record 12 controlling (section 0), so the OPEN fallback is the operative disposition; the 'defensible only with listed edits' verdicts were against the superseded sufficiency rule."
5. Add "### 15.2 Reconciliation review" recording this Worker D review (same lineage, not independent) and result, or drop "Adversarial reviews" plural.
6. Add banner line at top of the three contract-determinations files: "SUPERSEDED for operative purposes by 07 section 0 (record 12 controls; Q2/Q3 OPEN). Retained unedited per CA06." (note: this changes committed files; alternatively rely on 07 L13 and state so).
7. Extend 0.1 with one line for record 12 items 5-8 (B/B/C) or state they are outside this crosswalk; reconcile Q6 "CLOSED" with rec12 item 5 "independently qualified on 3.11 only".
8. Commit the working-tree 07 edits and untracked C JSON before publication; PR head 2967d0bf lacks them.
