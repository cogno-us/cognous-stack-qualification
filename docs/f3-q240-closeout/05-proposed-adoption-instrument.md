# 05 PROPOSED constitutional adoption instrument (documentary draft; requires Architect approval; activates nothing)

Disposition of Q8 (coordinator's reading, for the Architect to decide):
- Revisions: `1c2e920` (OCS technical baseline), `230c0af` (revision used by the final-three work package), `dcdbe3b` (prospective orchestration convention; adds licence, orchestrator addendum, packet schema). ADOPTION.md is the same blob at all three. All 23 CA rows are byte-identical. The review-tier label inverts (Tier 1 critical at `1c2e920`; Tier 3 critical at `230c0af` and `dcdbe3b`); `TESTING_POLICY.md` adds an independent T0-T4 scale and still contains a residual "independent Tier 1" phrase. 230c0af/dcdbe3b add the compliance addendum, testing policy and typed-packet convention that exist at no earlier revision.
- No ADOPTION.md-form instrument exists for any of the three. The standing baseline rests on pins in operator-approved plans and a scoped record that calls `1c2e920` "still binding".
- NOT required for the engineering closeout document to be accurate (it claims no adoption). REQUIRED before: any claim that OCS has adopted a revision; treating the compliance addendum, testing policy or packet convention as governing OCS packets; and, practically, before a competent certification rests on the constitution as the adopted text.
- This draft preserves `1c2e920` as binding, records `dcdbe3b` as a prospective convention without activating it, and leaves every approval field blank. It selects no revision for the Architect and names no approver.

Draft text follows (from the Q8 analysis; placeholders in brackets).

```
=============================================================================
PROPOSED ADOPTION RECORD (ADOPTION.md form)  --  STATUS: PROPOSED.
REQUIRES ARCHITECT APPROVAL. NOT ADOPTED. NOT EFFECTIVE. NON-AUTHORIZING.
=============================================================================
Prepared as a documentary draft only. It names no approver and records no
approval. Nothing in it is a decision until the competent adopting authority
(identified in section 11) completes section 12. If not approved, it has no effect.

1. Adopting context
   Program: OCS Registry V1 program and closeout records of work package [OCS-F3-*].
   Repositories in scope: cogno-us/cognous-ocs-registry; cogno-us/cognous-control-plane;
   cogno-us/cognous-stack-qualification. Other repositories/programs: NOT in scope.

2. Exact revision(s) and content identity
   2.1 Binding technical baseline (UNCHANGED, PRESERVED):
       cogno-us/cognous-engineering-constitution @ 1c2e920f4e58e07a52e8e2408a506cf7dbc1292b
       ADOPTION.md blob a9394cdb2b0c1432f2b2f10e82d94d3a8b0dd3f0;
       ENGINEERING_CONSTITUTION.md blob 3bb01a02b824cfad96839e131a39578714b5d6eb;
       ORCHESTRATION.md blob 1d3b924d5952bf40c3b54a3e7adb2c5dee54083c (verified from git)
   2.2 Prospective prompt-engineering convention, REFERENCED, NOT ACTIVATED:
       same repository @ dcdbe3b76843d672ca3cfb1f000124ecd78ed03c
       (ORCHESTRATOR_PROMPT_ENGINEERING_ADDENDUM.md blob e1b73f74cc8dd48ce73f0e649b25ef454b318829;
        ENGINEERING_COMPLIANCE_ADDENDUM.md blob 1d8a31a9867e045882c64ed0f3a68a14481f83e5;
        TESTING_POLICY.md blob f9d6ebbd6d7d8ffbf8a642c4e666691f79ac6ccc;
        ENGINEERING_CONSTITUTION.md blob bed8f0639fa0b403acce87dd496c985be474455e;
        schemas/orchestrator-assignment-v1.schema.json blob 9b65bfd606b22410cdad9c750d78583ef4fb475c; all verified from git)
       Intermediate revision cited by work package OCS-REG-FINAL3: 230c0aff1c2d1e054652cfc1be175147260b8aae
       (identical to 2.2 for the constitution, orchestration, compliance addendum and testing policy).
   2.3 Previously adopted, scoped (UNCHANGED): addenda/RISK_BASED_TESTING.md (blob 58b333d479361cf4ededdca275bac16fb5e35575;
       recorded revision a4dd11115e47e27e8f0731a622fe950f7fbf2fc2) for the OCS Registry V1 program only, per prior ruling D3
       dated 2026-10-25 (cited from hub doc 10; primary ruling text [LOCATION UNVERIFIED]).

3. Classification (ADOPTION.md "Semantic versioning")
   Local adoption record, not an amendment to the constitution. It changes no duties of A. For
   2.2, a prospective process convention; no change to CA01-CA23 (byte-identical at A, B, C).

4. Scope
   4.1 A (2.1) remains the technical baseline for all OCS program work, including CA01-CA23
       clause text used in F3 assignment packets (Archetype C and D cells are word-for-word
       A's CA table cells, per registry 09 section C/D).
   4.2 The convention in 2.2 (archetype routing, verbatim-slice packets, eight-field packet
       compilation) applies ONLY to assignments issued AFTER the effective point in section 5
       and only where an assignment states it. It is not retroactive.
   4.3 TESTING_POLICY.md T0-T4 (2.2): [ALTERNATIVE FOR ARCHITECT -- choose and record one]
       (a) not adopted; used only as a labelled vocabulary in packets that cite it; or
       (b) adopted as additional interpretive policy for [SCOPE], effective [POINT].
       DEFAULT in this draft if neither is chosen: (a). 
   4.4 Tier vocabulary rule for all OCS records: state tier meaning by label
       ("critical"/"routine") or by T0-T4 ID; where a bare "Tier 1"/"Tier 3" appears in a
       historical OCS record, it keeps the meaning of the revision in effect when written
       (A: Tier 1 = critical). New records must not use bare "Tier 1"/"Tier 3".

5. Effective point
   [DATE/EVENT -- to be set by the adopting authority; draft proposes: the date this record is
   merged AND approved, whichever is later; no retroactive effect on earlier packets or evidence].

6. Applicable controlling rules
   Law, security controls, contractual duties, branch protection and required checks retain
   precedence (ADOPTION.md "Standing"). The stricter rule governs on conflict (per prior D3
   record). Frozen contracts and oracles are not amended by this record.

7. Reserved powers (unchanged; none transferred by this record)
   Reserved to the competent authority as already recorded: architectural, security, budget,
   external-effect, deployment, release, upstream and material acceptance-rule decisions;
   independent-owner designation; competent certification; final Tier 1 qualification;
   Registry #58/#59, Control Plane #87, Ed25519 #26/#34, constructor tolerance, V09,
   publication/release/production holds, DEF-OBS-TOL-OVERFLOW-1, R1 refactoring (as in
   closeout 14 s8). [Update list to the holds in force at approval.]

8. Exceptions and transition provisions
   8.1 Historical evidence and records keep the revision identity they cite (ADOPTION.md
       "Older revision identities and historical evidence remain valid"; "not retroactively
       recertified").
   8.2 Records that cite B or C for process (e.g., final-three 02/03, hub PROTOCOL-F3 R14)
       remain valid as citations of what they cited; no re-labelling.
   8.3 The F3 original FAIL and the successor interpretation OCS-F3A-DEV-PE-1-INTERPRETATION/1.0
       are not altered by this record.
   8.4 Any packet that sets projectAdoption.status = CONFLICT or UNVERIFIED may be updated to
       VERIFIED only by citing this record's id and its approval entry, after section 12.
   8.5 Exceptions: [NONE PROPOSED | LIST].
   8.6 Transition for open items: AD-15 (pin confirmation) -- closed by this record only upon
       approval; D7 (post-migration/04) -- answered by section 4.2 only upon approval;
       adoption of 6f7f273 -- remains NOT ADOPTED (UNVERIFIED history).

9. Non-effects (explicit)
   Does not activate any new requirement of B or C for work already issued; does not select C
   as the OCS governing revision; does not adopt the Orchestrator Prompt Engineering Addendum
   (its own text: NOT ADOPTED by publication or merge); does not authorize spending, personnel
   delegation, credential access, production release, external effect, legal certification, or
   any transfer of independent qualification authority; does not designate an independent owner
   or certifier; does not constitute qualification, certification, integration, or release.

10. Lineage and retention
    Predecessor: no ADOPTION.md-form instrument located (see registry 09 section A4).
    Supersedes: nothing. Preserved: all pin citations and non-adoption statements.
    Decision record and any objections retained under ADOPTION.md "Evidence, retention".

11. Adopting authority (to be identified; none presumed)
    Competent identified individual or body: [IDENTITY]
    Source of that authority: [CITATION]
    Adequate context basis ("Human approval alone is insufficient without valid authority and
    adequate context"): [STATEMENT]

12. Decision entry -- BLANK; to be completed only by the adopting authority
    Decision: [ACCEPT / REJECT / DEFER]    Text and scope decided: [..]
    Effective point fixed: [..]            Exceptions approved: [..]
    Attestation / mechanism: [..]          Date: [..]
    Status of this record before section 12 is completed: PROPOSED -- REQUIRES ARCHITECT APPROVAL.

13. Verification before approval (checklist for the preparer)
    [ ] full blob ids and commit ids re-read from git on approval date
    [ ] clause equality A vs B vs C re-run
    [ ] list of holds updated
    [ ] D3 primary ruling text located or marked UNVERIFIED
=============================================================================
```

Open questions a draft cannot answer (flag, do not guess):
1. Who the competent adopting authority is (section 11).
2. Whether the Architect's stated rule "existing OCS constitutional adoption is preserved" (D6, builder-transcribed) is the decision this record should cite or restate; primary text not located.
3. Whether to adopt TESTING_POLICY.md T0-T4 (4.3) and whether D3's older addendum is superseded by it (D3 stated scope is the older file only).
4. Whether the draft should reference C at all; including 2.2 as "referenced, not activated" is a drafting choice.

