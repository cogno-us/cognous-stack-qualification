# Candidate report template: separated layers (four, plus the evidence-review status) (PROPOSED, builder-prepared)

Do not aggregate these layers into an NC4 PASS. Non-authorizing; release and production HOLD.

Architect-approved wording (use verbatim): **Code-level ingress provenance was demonstrated through independent source review and builder-side testing. Host process isolation was not independently qualified under the original restricted-host profile. NC4 remains INCOMPLETE.**

| Layer | What it reports | Current state (builder-side, at the last recorded run) |
|---|---|---|
| 1. Engineering | complete / incomplete | engineering work complete for the code-level parts; host environment not available |
| 2. Individual mandatory controls | each row separately, labelled builder-side until independently adjudicated: code-level provenance (NC4-03 source predicate, NC4-04 launch isolation), executor-level controls (NC7-01..03), the other rows; host isolation evidence (NC4-01/NC4-02 observations, environment record G-11) reported separately | rows PASS builder-side with the developer-optout profile; host isolation evidence INCOMPLETE (no Yama host, no qualifying distinct-identity environment) |
| 2b. Evidence review (separate from code review) | review of the raw run evidence by a reviewer other than the builder; Copilot code review is not evidence review | **not performed** (no reviewer available): independent evidence review: not performed (no reviewer available) |
| 3. Overall independent acceptance | gate verdict by an authorized independent owner | none exists; NC4 INCOMPLETE under the original profile; the whole-run verdict stays INCOMPLETE |
| 4. Release readiness | HOLD | HOLD |

Label when no authorized independent owner exists: **Candidate testing complete or partially complete; independent adjudication pending.**

Every report states: **independent evidence review: not performed (no reviewer available)**, and never claims independent qualification or evidence adjudication.
