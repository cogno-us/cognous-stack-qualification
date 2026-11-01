# Independent inspection: constitutional-adoption crosswalk (09 / 09a)
Read-only. No verdict. Registry HEAD verified = 517062529f0507be81a8ac5e457a009db98f8d90. Constitution repo main = dcdbe3b (42 commits, all 3 revs exist as commits).
Note: the crosswalk 09 header says "HEAD 6d005ab"; real HEAD at this inspection is 5170625 (merge of the PR carrying 09 itself). Minor staleness, not substantive.

## (1) CA04/06/07/08/23 byte-equality (recomputed, sha256 of whole table row, first 16 hex)
Revisions 1c2e920f, 230c0aff, dcdbe3b all exist (git cat-file = commit). Constitution CA table is lines 88-110 at all three.
| Row | sha256 (identical at 1c2e920, 230c0af, dcdbe3b) |
| CA04 | 49567c10816cc859 |
| CA06 | a09776e40c6646d6 |
| CA07 | a72d126b5a902fa1 |
| CA08 | 5d8781145789e221 |
| CA23 | 99062daeb1a750fb |
Compliance Addendum Archetype D table (lines 61-65), at 230c0af AND dcdbe3b: article label, Required cell and Prohibited cell each string-equal to the Constitution CA-table cells (True for all 5 x 3 fields, both revisions). Addendum file blob 1d8a31a9 is the same at both; absent at 1c2e920.
Verbatim at dcdbe3b (Required | Prohibited):
- CA04 — Qualification Designed Before Acceptance | "Distinguish implementation inspection, independent qualification, competent certification and final integration; preserve independence wherever required." | "Fit an oracle to implementation or substitute developer tests."
- CA06 — Preserve Original Evidence | "Retain consequential decision ancestry, rejected alternatives, objections, adverse findings and supersession where legitimately relevant, subject to privacy and retention limits." | "Delete, relabel, overwrite or silently rescore failures."
- CA07 — Exact-Source Reproducibility | "Bind claims to exact source, configuration, governing context and transition evidence; reconstruct authoritative pathways when deterministic execution replay is impossible." | "Transfer a pass across revisions."
- CA08 — Independently Qualified Delivery | "Optimize authorization-to-independently-qualified outcome; distinguish lifecycle evidence." | "Treat PR counts, green CI or documents as delivery or qualification."
- CA23 — Accountable Certification | "Separate contribution, inspection, qualification, certification and integration according to risk and governing independence requirements." | "Self-certify generated work or treat nominal human involvement as sufficient authority."
(The Constitution table row also has a 4th Validation cell, e.g. CA04 "Independent pre-acceptance source/pin record."; CA23 "Competence, identity, independence and accountability review."; also identical.)

## (2) All 23 CA rows across revisions
CONFIRMED: 23 rows at each revision; full-row string equality for all 23 across 1c2e920 / 230c0af / dcdbe3b (zero differing rows). Crosswalk claim (C) holds.

## (3) Tier vocabulary (ENGINEERING_CONSTITUTION.md lines 150-156)
1c2e920: "**Tier 1 is highest criticality; Tier 3 is lowest.**" ... table "| Tier 1 — critical |", "| Tier 2 — substantive |", "| Tier 3 — routine |". Also has sentence "Do not automatically fix Tier 3 items first simply because they are numbered third."
230c0af = dcdbe3b (identical blob bed8f063): "**Tier 1 is routine; Tier 3 is critical.**" table "| Tier 1 — routine |", "| Tier 2 — substantive |", "| Tier 3 — critical |".
ORCHESTRATION.md: 1c2e920 line 76 "...evidence rule are Tier 1 (critical)." line 105 "Apply Tier 3 routine self-validation ...; Tier 1 retains those requirements and adds focused independent assurance for the critical boundary." dcdbe3b line 90 "...are Tier 3 (critical)." line 119 "Apply Tier 1 routine ...; Tier 3 retains ...".
TESTING_POLICY.md (230c0af, dcdbe3b) uses a separate scale: T0 Editorial, T1 Isolated low consequence, T2 Interface or composition, T3 Governance or safety critical, T4 Acceptance milestone (lines 17-21). It defines no "Tier N" review labels, BUT line 67 says: "Risk-tiered developer CI is **not** independent Tier 1 qualification or certification." That "Tier 1" is the OLD (1c2e920) meaning (critical/independent) and contradicts dcdbe3b's own Constitution (Tier 1 = routine). Crosswalk 09 did not flag this internal inconsistency inside TESTING_POLICY at B/C. Practical consequence: in dcdbe3b-era texts, bare "Tier 1" is ambiguous; T-vocabulary (T0-T4) vs review Tier 1-3 are different axes (T3 "governance critical" ~ review Tier 3 critical in B/C, but ~ Tier 1 critical in A).
Crosswalk claim of "label inversion, same class" CONFIRMED.

## (4) ADOPTION.md at dcdbe3b (blob a9394cdb, identical at all three revisions)
Valid adoption instrument, line 7: "An adopting authority must identify an exact revision, the scope and effective point of adoption, applicable controlling rules, reserved powers, and any approved exceptions or transition provisions."
Line 5: "Publication of a revision, possession of a copy, a passing check, or a repository merge does **not** by itself establish adoption by an organization or project, authorize activity, or override law, security controls, existing contractual duties or separately reserved decisions."
Line 17: "**Adopting authority:** a competent identified individual or body determines whether, when and to what scope an amendment is adopted. Human approval alone is insufficient without valid authority and adequate context."
Line 28: "**Decide.** The competent adopting authority accepts, rejects or defers a specified text and scope. A technical merge cannot stand in for this decision."
Line 30: "**Adopt locally.** Each adopting context makes or records its own revision selection and transition; a newly published text does not silently amend existing frozen contracts."
Independence, line 15: "**Independent qualifier:** where required, assesses the amendment against independently specified obligations and records a scoped result. Independence cannot be inferred from a second automated process alone."
Line 21: "One individual may perform multiple roles where the applicable risk and governing rules allow it. Required independence may not be waived through role renaming or delegation."
Line 13: "Inspection is not certification."  Line 41: "Historical evidence is not retroactively recertified by a newer constitution."
Line 45: "Nothing here constitutes ... transfer of independent qualification authority."

## (5) TESTING_POLICY.md at dcdbe3b (blob f9d6ebbd, same at 230c0af)
- Line 3: "Effective adoption: requires an exact-revision, scope-specific adoption record. Merging this document alone is not project adoption." Also "Status: Normative engineering practice, subject to competent adoption under ADOPTION.md."
- Line 7: "Reuse existing evidence only where exact source, dependency, contract, configuration and execution-environment applicability is demonstrated."
- Line 36 (reuse across revisions): "Reuse a prior pass only when the claimant records exact tested source head, relevant dependencies/contract versions, inputs, environment, test identifier, result and why the changed system remains within that evidence's applicability. A passing test on a different revision is not automatically transferable (CA07). Re-run targeted tests when the evidence cannot cover a changed failure mode."
- Line 44: "A zero diff in evaluator and contract files is **necessary in simple cases but not sufficient**: changed data, callers, dispatch, runtime wiring, authority state or configuration may invalidate the earlier evidence."
- Docs-only: line 17 T0 = "Comments, prose, metadata, non-executable documentation, with no contract, governance, generated artifacts or CI semantics changed"; line 23: "A documentation edit changing a governing requirement, security procedure, API contract or release claim is not automatically T0. A one-line authorization change can be T3."
- T4 (line 21): "Release candidate, engineering freeze, certification, mandated independent qualification | The complete prescribed qualification campaign at exact frozen heads, with required independence and adverse evidence; cannot be replaced by T0–T3 developer results." Line 38: "T4 follows its independent acceptance plan."
- Line 67: "The independent qualifier defines and executes the required scope rather than inheriting a builder's convenience-based test selection." Also "Preserve negative evidence, original failed outputs, qualification holds, exact-head traces and the independent oracle."
- Line 32: "Never disable a needed test, adjust an oracle to match implementation, hide failure logs, loosen a check or call a workflow skip a PASS."
- Mutation: the word "mutation" does NOT appear in TESTING_POLICY.md. Regression: T3 "Broad **affected** regression, adverse/negative and boundary tests..." and "Unrelated repository-wide tests are not automatic unless risk or controlling gates require them" (line 20); T2 "affected integration/regression paths". No mutation-testing expectation is stated in this policy.
- Line 9: "If two rules apply, follow the stronger applicable obligation; record unresolved conflicts." Line 69: "It cannot silently alter the obligations or adopted revision of any engineering project."
Also addendum line 3 (Compliance): "Proposed normative orchestration addendum, subject to competent adoption under ADOPTION.md".

## (6) Adoption instruments and D1 confirmation on record
Constitution repo: no adoption instrument. git log --all --grep=adopt gives only a6e8012 and 7f82686 (early ADOPTION.md authoring commits). 11 branches, none an adoption record. dcdbe3b files (Orchestrator addendum, TESTING_POLICY) only state non-adoption.
Registry repo (HEAD 5170625): I found no ADOPTION.md-form instrument (exact revision + scope + effective point + reserved powers + exceptions) adopting 1c2e920 or dcdbe3b. Closest: 06 section 9 / D6 restatement ("existing OCS constitutional adoption is preserved and no newer revision is silently promoted"; "dcdbe3b / 230c0af / 1c2e920 remain as they were"), which is a builder transcription of an Architect directive whose own record is "UNVERIFIED here". Plans (PROJECT_PLAN v1.1 "This plan does not itself adopt the Constitution") and decisions/2026-10-24-operator-decisions-D1-D5.md :41 ("Formal Constitution adoption is not required for S01 and none is claimed") are explicit non-claims; I did not re-audit every one of the crosswalk's A1-A3 rows line by line, but my greps (docs/, git log all branches, 'dcdbe3b') surfaced nothing contradicting its conclusion. Crosswalk 09's own statement "the Architect's own adoption record is not located in any repository inspected" is consistent with what I found.
Successor interpretation 06 (blob 0d90012 at HEAD; last changed a7a2390 2026-10-30; the PR #80 merge 6bf83dd 2026-10-29 precedes edits 47ce144/a7a2390 on 2026-10-30 -- check which landed on main; I did not resolve this):
- 06 line 3: "ADOPTED IN PRINCIPLE by the Architect (decision D1, closeout directive of 2026-10-29), subject to final source review; documentation only. It governs only from the Architect's recorded post-review confirmation naming this document's exact revision (section 9)."
- 06 section 9: "This record governs only from the Architect's recorded post-review confirmation identifying this exact document revision (PR #80 final head and blob sha at confirmation). ... the Architect's own record location is UNVERIFIED here."
- 06 section 10 item 1: "(D1, decided in principle) Record the post-review confirmation naming the exact revision (section 9)." -> still an open to-do.
- 07 lines 36, 39 list "record the post-review confirmation of D1 naming the exact revision of 06" as an open item; readjudication-packet.json states "Architect decisions D1 approved in principle after final source review"; and "UNVERIFIED: no competent designation record names a fresh independent_qualification_owner".
- Git history: commit 47ce144 (2026-10-30, by the builder session) CHANGED 06's status from "PROPOSED successor clarification ... Takes effect only on recorded Architect adoption" to "ADOPTED IN PRINCIPLE ..." and added the "D1/D2/D6" lines; that is a builder edit citing a directive not present as primary text, not an Architect instrument. No commit or file in the Registry names a confirmed revision/blob of 06.
CONCLUSION: The post-review confirmation of 06 is NOT on record in either repo. Per its own section 9, 06 therefore does not yet govern; it is, at most, an adopted-in-principle proposal. The crosswalk does not claim otherwise but also does not highlight that the 06 status line was upgraded by a builder commit on 2026-10-30.

## Other observations for the qualifier
- 09's claim "no Architect decision is needed for readjudication to proceed on baseline clause text" is supported on clause equality, but all five CA cells equal A's, so using C's Archetype D slice vs A's table is substantively identical -- verified.
- What A (1c2e920) lacks: Compliance Addendum, TESTING_POLICY (T0-T4), packet schema; packet T4 vocabulary and Archetype D routing are therefore prospective convention (C) only; neither B nor C has any adoption record.
- Tier ambiguity inside TESTING_POLICY line 67 (see 3) is an unflagged hazard.
- The Architect's directives D1-D7 are not primary text anywhere in these repos; all are builder transcriptions (UNVERIFIED as primary).
