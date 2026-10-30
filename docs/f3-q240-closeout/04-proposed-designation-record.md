# 04 PROPOSED designation record (template; names no one; NOT EFFECTIVE)

Status: PROPOSED TEMPLATE. Not a designation. No person, body, session or service is named or presumed. Not effective until completed and approved by the designating authority. Non-authorizing; release, publication and production HOLD.

Findings that shape it (from source inspection; independently re-read):
- Sources give only a negative independence standard: not the builder or Lead Builder lineage; not the Architect for oracle/verdict roles; not Copilot (technical reviewer only); not a worker dependent on the builder; not a session that also acted for the implementation owner on the subject. ADOPTION.md: independence "cannot be inferred from a second automated process alone"; a title or delegation cannot waive required independence.
- No source gives a positive eligibility test, says whether an AI session may hold the role, sets a number of qualifiers or a term.
- Three sources name different designating authorities: operator (r08 contract s8, F-01), the independent qualification owner (hub 06, D-26), Architect (F3 handoff s1, s8). The Architect must rule; the template does not assume.
- No designation of an independent owner or certifier exists in any inspected repository (GAP-G4-13 open).
- Disclosure: the session that produced the successor readjudication evidence is the same session that prepared this template; it must not be designated for Q2-Q6.

Use one record per role per scope; do not combine qualification and certification roles unless each independence basis is separately established.
Intended instrument identity: one record per role per scope. A single record must not combine independent-qualification-lead and certifier roles unless the independence basis for each is separately established.

```
DESIGNATION RECORD  [DRAFT / PROPOSED -- NOT EFFECTIVE]
Record id: [ID]                  Revision of this template: [TEMPLATE REV]
Exact repository / path / commit where this record will be filed: [REPO] [PATH] [COMMIT]

1. ROLE BEING DESIGNATED  (choose one per record; do not combine)
   [ ] Independent qualification owner / lead (may write the scoped independent verdict)
   [ ] Independent evidence reviewer
   [ ] Competent certification authority
   [ ] Other (state): [ROLE]
   Role does NOT include: merge authority, release, deployment, production, spending,
   credential access, adoption authority, or any authority not expressly listed in section 4.

2. DESIGNEE IDENTITY
   Designee type:  [ ] natural person  [ ] organization  [ ] AI session/service (see 2c)
   a. Legal or account identity: [IDENTITY -- to be supplied by designee/designator]
   b. Verification method for identity and control of the account: [METHOD]
   c. If AI: provider/model/version [..], session or deployment identifier [..],
      human accountable for the AI's output [IDENTITY], and how that human
      satisfies "appropriate authority, evidence, independence and accountability"
      (EP7): [STATEMENT]. [NOTE: ADOPTION.md -- independence "cannot be inferred from
      a second automated process alone"; an AI-only designee does not satisfy the
      independence requirement without a separately established basis.]
   d. Competence basis (qualifications, relevant experience, prior work on this stack): [..]

3. DESIGNATING AUTHORITY
   a. Designating authority (identified individual or body): [IDENTITY]
   b. Source of that authority (document, ruling, date): [CITATION]
      [OPEN POINT: sources differ on who designates -- operator (r08 s8/F-01),
       independent qualification owner (hub 06, D-26), Architect (F3 handoff s1/s8).
       The authority must be identified and cited here, not assumed.]
   c. Is the designating authority independent of the builder? [YES/NO + basis]
   d. Date and mode of designation: [DATE] [MODE]
   e. Who may amend or revoke, and how: [..]

4. SCOPE
   a. Work package(s): [IDs]       b. Subjects (exact full SHAs): [REPO @ SHA, ...]
   c. Contracts/oracles/protocols in scope (blob ids / sha256): [..]
   d. Verdict type permitted (e.g. bounded scoped verdict on [..]; NOT full Tier 1 unless stated): [..]
   e. Explicitly excluded: [..]
   f. Constitutional revision this role operates under, and its adoption status: [REV] [VERIFIED/UNVERIFIED/CONFLICT]
   g. Vocabulary: state tier meaning by label ("critical"/"routine" or T0-T4), not bare "Tier 1/3".

5. EFFECTIVE POINT AND TERM
   Effective from: [DATE/EVENT]   Expires / review: [DATE/EVENT]   Reopening conditions: [..]

6. INDEPENDENCE BASIS (answer every question; "unknown" is a permitted answer and must be recorded as such)
   6.1  Has the designee authored, edited, reviewed or approved any part of the implementation
        under test? [Y/N + detail]
   6.2  Has the designee authored or contributed to the oracle, contract, expectations, fixtures or
        protocol for this subject? [Y/N + detail]
   6.3  Has the designee acted for the implementation owner, Lead Builder, or Architect on this
        or an adjacent work package, in this session lineage or otherwise? [Y/N + detail]
   6.4  Has the designee previously produced an assessment or verdict on this subject? If yes,
        is this a readjudication of the designee's own prior work? [Y/N + detail]
   6.5  What did the designee read before expectations were frozen (read_contamination)? [LIST]
   6.6  Reporting lines, employment, contract, ownership, financial or other dependency
        relationships with the builder, the implementation owners, the Architect, the operator
        or the designating authority: [LIST]
   6.7  Shared infrastructure, accounts, credentials or session memory with the builder or any
        worker whose output is under review (including shared project memory): [LIST]
   6.8  Is the designee dependent on the builder for tooling, evidence, access or compensation? [Y/N]
   6.9  Is the designee the same actor as, or a delegate of, any of: builder; Architect;
        oracle author; runner; evidence reviewer; final adjudicator; Copilot? [per-role Y/N]
   6.10 For an AI or automated designee: same model family/provider as the builder or oracle
        author? [Y/N]; is there an independent human review of its output? [Y/N + identity];
        what in the above is NOT independent? [LIST]
   6.11 Residual non-independence the designating authority accepts, with the rule that permits
        accepting it, or "none accepted": [STATEMENT]
   6.12 Independence exception/waiver requested? If yes: competent authority [..], explicit
        scope [..], duration [..], rationale [..], mitigating controls [..], immutable
        evidence [..] (TESTING_POLICY s7). Otherwise "none".

7. CONFLICTS-OF-INTEREST DISCLOSURE  (to be completed by the designee)
   7.1 Financial or equity interest in the outcome of this qualification or in the product: [..]
   7.2 Role in the seed round, commercial positioning, or customer commitments that depend
       on the outcome: [..]
   7.3 Personal or professional relationships with the builder, implementation owners, the
       Architect, the operator or other participants that could reasonably appear to affect
       impartiality: [..]
   7.4 Prior or concurrent engagements with the organization: [..]
   7.5 Other disclosures: [..]
   7.6 Management of each disclosed conflict (recusal, scope limit, additional reviewer): [..]
   7.7 Duty to update promptly on any change: [ACK]

8. ACCEPTANCE OF ROLE  (to be completed by the designee; blank until then)
   "I, [DESIGNEE IDENTITY], accept the role of [ROLE] for the scope in section 4 under the
   terms of this record. I confirm: (a) the independence answers in section 6 and the
   disclosures in section 7 are complete and true to my knowledge; (b) I am not the builder,
   the Architect, Copilot, or a worker dependent on the builder, and I did not act for the
   implementation owner on this subject; (c) I will freeze expectations before candidate
   execution and will not adjust frozen expectations to obtain a pass; (d) I will report FAIL,
   BLOCKED, NOT_RUN and INACTIVE results as such and preserve raw adverse evidence; (e) I
   hold no authority to merge, release, deploy, adopt, spend or certify beyond section 4; (f)
   I will disclose any later loss of independence; (g) I understand a result transfers only to
   the exact sources and conditions evaluated."
   Signature / attestation mechanism: [MECHANISM]   Date: [DATE]   Status: [NOT ACCEPTED]

9. DESIGNATING AUTHORITY DISPOSITION  (blank until completed by the designating authority)
   Accepted / rejected / deferred: [  ]   Basis for finding the independence adequate: [..]
   Attestation: [IDENTITY] [DATE] [MECHANISM]

10. SEPARATION CHECK (filled at designation)
   Distinct holders recorded for: oracle author [..]; builder [..]; runner [..]; evidence
   reviewer [..]; independent qualification lead [..]; competent certification authority [..];
   final adjudicator [..]; integrator [..]. Any role held by the same actor: [..] with the
   governing rule permitting it [..].

11. LIMITS AND STANDING HOLDS
   Non-authorizing. Does not confer: spending, personnel delegation, credential access,
   production release, external effect, legal certification, merge authority (ADOPTION.md
   "Non-authorizing character"). Holds carried unchanged: [list as in closeout 14 s8].

12. EVIDENCE AND CUSTODY
   Where the designation and acceptance are filed (immutable): [LOCATION]; hash: [SHA256];
   related issue/tracker: [ID].
```


Notes: sections 6 and 7 are new questions built from CA23 validation (competence, identity, independence, accountability review), the hub 06 independence-record requirement and the owner-designation-request fields; keep or drop at the Architect's discretion.
