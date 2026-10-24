# Qualification reviewer designation record (DRAFT for operator approval)

Status: DRAFT prepared by the builder for the Cognous operator. Not approved, not effective until the operator fills the disposition below. Non-authorizing; release and production HOLD. This file does not concern issue #218 and nothing is posted there.

## Designation (proposed by the operator's decision of 2026-10-24)
| Field | Value |
|---|---|
| Reviewer | GitHub Copilot code review (a separate LLM, independent of the builder) |
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
