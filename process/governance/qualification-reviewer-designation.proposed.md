# Qualification reviewer designation record (DRAFT for operator approval)

Status: DRAFT prepared by the builder for the Cognous operator. Not approved, not effective until the operator fills the disposition below. Non-authorizing; release and production HOLD. This file does not concern issue #218 and nothing is posted there.

## Responsibilities (operator decisions of 2026-10-24; three separate roles)
1. **Code review**: GitHub Copilot code review. Observed identity: `copilot-pull-request-reviewer[bot]`, review state COMMENTED (comment-only; NOT a GitHub approval). Commits it reviewed: #226 `94fc06bd`, #223 `b3123aee`, #225 `e931f18c`. The operator decided this review is sufficient for the code-review function.
2. **Evidence review**: a separate LLM instance, independent of the builder and of the code reviewer, to be run AFTER the battery runs, inspecting the oracle, the candidate manifest, execution logs, checksums and environment records. Not yet performed.
3. **Final adjudication**: the Cognous operator.

**Merge actor**: the operator explicitly delegated the Qualification-repo merges to the coordinator Claude session acting under operator authority (decision 2026-10-24). The builder does not merge. Comment-only reviews are not repository approvals; independence of the evidence review remains with the separate LLM; final adjudication stays with the operator.

## Designation (proposed by the operator's decision of 2026-10-24)
| Field | Value |
|---|---|
| Reviewer (code review) | GitHub Copilot code review (a separate LLM, independent of the builder); observed as copilot-pull-request-reviewer[bot], COMMENTED |
| Model / session identity | as exposed by GitHub per review; may be "not disclosed" |
| Scope | Qualification PRs #226, #223 and #225; expectations v6 and v7; exact-candidate evidence; assessment of the trusted-host successor profile |
| Independence | the reviewer makes no implementation changes and no retroactive alteration of mandatory criteria; it is not the builder |
| Authority | technical review and recommendation ONLY. Final acceptance is retained by the Cognous operator. An authorized GitHub actor performs merges |

## Limits that matter for this designation (stated honestly)
- GitHub Copilot code review is comment-only: it cannot approve, block or merge.
- It cannot execute the battery and cannot read evidence that is not in the repository or the PR.
- Its review is technical review. It is NOT independent test execution and NOT qualification. Test execution evidence remains a separate artifact, and a human or authorized actor must adjudicate.
- An absent or silent review is not an approval, and a review without the evidence below is not meaningful.

## Evidence that must be placed in the PRs for the review to be meaningful
1. Exact heads of #226, #223, #225 and the commitment sha256 (the REPORTED value, supplied from outside the checkout).
2. The exact candidate manifest: `process/mvp-acceptance/candidate-identity.inputs.json` (tuple and composite block) and the hub tree ids.
3. Expectation hashes (`unchanged_files_sha256` in the battery) and the mandatory battery file.
4. Raw run output kept in the repo or attached to the PR: full console logs, `results.json`, `observations.json`, junit XML, collected-test lists, pytest exit files, Verifier reports, the ingress module dump, the gate verdict; a `SHA256SUMS` manifest over all of it (see `process/mvp-acceptance/manual-execution-runbook.proposed.md`).
5. Environment records and envelopes, or an explicit statement that none exists (no Yama host: the original profile stays INCOMPLETE).
6. The successor profile draft and the four-layer report (`report-template.proposed.md`), with the builder-side labels intact.
7. The PR comments listing known limits, failing or INCOMPLETE items, and the not-covered list.

## Record fields (filled per review)
| Field | Value |
|---|---|
| Reviewer identity | GitHub Copilot code review; model/session: |
| Source revisions reviewed (exact heads) | #226: ______ #223: ______ #225: ______ |
| Findings | |
| Operator disposition | (blank: for the operator) |
| Date and authorized actor | (blank) |

## Observed review activity (recorded by the builder; findings triaged on the PRs)
| PR | Reviewer identity | State | Commit reviewed |
|---|---|---|---|
| #226 | copilot-pull-request-reviewer[bot] | COMMENTED | 94fc06bd |
| #223 | copilot-pull-request-reviewer[bot] | COMMENTED | b3123aee |
| #225 | copilot-pull-request-reviewer[bot] | COMMENTED | e931f18c |

Material fixes were pushed afterwards and re-review was requested; the commits reviewed in any later review must be added to this table by the operator or the builder.

## Operator disposition entries (dated; recorded by the builder at the coordinator's instruction)

2026-10-24, operator statement in the coordinating session, verbatim: "there is no second llm for now. i grant approval."

Interpretation, stated as the coordinator's reading and no broader: the operator approves (a) adoption of the successor trusted-host distinct-UID profile scope (the approved wording quoted in `process/mvp-acceptance/trusted-host-successor-profile.proposed.md`), and (b) this reviewer designation record (GitHub Copilot code review, identity copilot-pull-request-reviewer[bot], review state COMMENTED; Qualification merges delegated to the coordinator Claude session under operator authority).

Not approved by that statement: adoption of the baseline record (`process/governance/qualification-baseline.proposed.md` stays PREPARED, NOT ADOPTED until #225 is merged and the final commitment and heads are fixed; the operator's adoption must reference exact digests), any acceptance, qualification, release or production decision.

Evidence review: no second LLM is available now, so the separate evidence review is NOT performed (pending). Every report must say: **independent evidence review: not performed (no reviewer available)**. It must not claim independent qualification or independent evidence adjudication. Copilot code review is a code review and is not an evidence review.
