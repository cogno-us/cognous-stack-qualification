# Decisions made while assembling the package

Where the drafts left a choice open, the conservative choice was made: no expected outcome was written or changed, no registered file, pin, profile, inventory row or workflow was touched, and the choice that keeps the comparison harder for the comparators or leaves a question visible was preferred. Each item says what was chosen, what the alternative was and how to reverse it. All are for owner review before the freeze amendment is applied.

## Decisions

**C-1. Mapping of TC-L02-011-S3 (exception to an approval step).**
The scenario asks whether an exception that bypasses an approval step is honoured while it is valid (call at 10 minutes of a 1-hour exception, no approval record, expected: accepted). The application recorded an exception only for the allow-list and for the elevation requirement, so the question could not be answered as asked.
Chosen: the application honours a live exception record for the same agent and target against the absence of an approval (rule `APPROVAL_PENDING`) and nothing else. A recorded rejection, timeout or self-approval is never waived, an exception for another agent or target does not apply, and at the expiry instant the hold applies again. The rule is written from the case text. The expected outcome and the steps of the scenario are unchanged. Tests: `tests/test_wiki_opa_app.py` (`test_exception_*`).
Alternative: declare S3 not expressible for both comparators (asked 85, not expressible 20), or leave the application as it was and let the scenario be answered as asked. Reverse: remove the line `not exception_ok` from the `APPROVAL_PENDING` rule and the three tests.

**C-2. Comparator tool count for TC-L06-011 (10 tools).**
The case names 10 tools (4 read, 3 write, 2 delete, 1 execute), 3 agents and 2 users; the declared world had 14 named tools with a different split, so five scenarios had been set aside as not expressible.
Chosen: the declared world carries the 10 gateway tools (`gw_read_1..4`, `gw_write_1..3`, `gw_delete_1..2`, `gw_exec_1`) and three agents (`gw-a1`, `gw-a2`, `gw-a3`). The rule of the case (reads for all, writes for `gw-a1`, deletes and execute denied) is carried by the per-agent allow-lists, the same mechanism as for every other agent; no new rule logic. Scenarios S1 to S5 are executable (24, 6, 12, 12 and 6 calls, every tool for every agent and for both users); their expected outcomes are the ones of the outcome file, unchanged. A static check in `validate_plan.py` confirms that each call expected to be accepted is permitted by the declared world; no scenario was scored. The plumbing of the new steps was checked on renamed twins (`harness/plumbing_twin.py`) with the verdicts discarded.
Alternative: keep S1 to S5 not expressible (asked 81, not expressible 24). Reverse: restore the five `ne(...)` declarations in `author_plan.py` and remove the gateway world from `wiki_config.py`.

**C-3. Declared-interface files.**
The source references of the draft (line numbers into the application source) had drifted after later edits; they are replaced by references that carry a marker text which the cited line must contain, and `tests/test_interface_declarations.py` checks every one. The status text no longer says draft: the files state what the applications read and offer and are not themselves declarations of asked, not expressible or not claimed. Added: the exception records (C-1), the gateway world (C-2), and the absence "several accepted effects with different payloads" (the oracle compares every effect payload with one expected payload). Every plan-authoring reclassification (C-5) now cites at least one item of the declared interface (amendment 79, draft).
Reverse: not applicable (corrections).

**C-4. Two sets of counts, and the paths.**
The outcome files (written from the case text before the comparator world existed) count asked 94, not expressible 11, not claimed 0, not asked 16 of 121 scenarios in 28 cases. The plan file, which adds the executable steps, counts asked 86, not expressible 19, not claimed 0, not asked 16: eight scenarios that the outcome files mark as asked could not be built in the declared world and are recorded in the plan file as not expressible, each with a reason, citations, an interface item and the unchanged expected outcome (list in `digests.json`, `wiki_plan.plan_authoring_reclassifications`). The draft of the freeze amendment for the plan file states 94 and 11; it needs to state the counts of the plan file (86 and 19) and name the eight, or the eight need to be made expressible first (C-5). Plan file path: `comparators/wiki/plans/wiki-subset-plan.json` (the draft names a `suites/` path). The outcome files are `comparators/wiki/expected-outcomes/outcomes-final.json` and `scenario-outcomes.json`.

**C-5. The eight plan-authoring reclassifications are left as authored.**
TC-D09-011-S4, TC-D13-003-S6, TC-L06-013-S4, TC-L06-014-S1, TC-L07-008-S1, TC-L07-008-S2, TC-L09-004-S5, TC-L09-019-S2. Six of them need a control or a world feature that the applications do not have (a delegation expiry, a budget-cap change, removal from an allow-list, a read-only token, a non-production destination, a request intent) and two need several accepted effects with different payloads, which the oracle cannot compare. Conservative choice: no application feature was added after the expected outcomes were written. Risk: not expressible declared because of a gap in the comparator world can look like hiding a failure (risk H-3 of the plan); the report prints the counts per configuration for that reason. Owner decision needed: accept as authored, or extend the world before the freeze (each extension is small, none changes an expected outcome).

**C-6. Location and wiring.**
The package lives in `comparators/` of the qualification repository. It is a Python package (`comparators.wiki.apps`, `comparators.wiki.harness`) that the tests import with the repository root on the path. It is not collected by `pytest.ini` (`testpaths = tests`), and no workflow, inventory row, pin or profile refers to it.

**C-7. Registered files are not copied.**
The package refers to the registered files in `suites/cognous-open-control-stack/` and checks their digests (`_base.py`, `digests.json`). The hub revision `8517818fbf817897aacfb6fe7898c22aea46fd95` is read from a checkout named by `SCN_HUB_DIR` (only `reference_profiles/`); its digests are recorded. The OPA binary is not stored; its digest is the one in `dependencies.json`.

**C-8. Cross-reference file.**
Regenerated by test name from the repository at the base commit (the earlier listing named an older commit and tests that were since renamed). Names only, no gate status, never added to a pass fraction.

**C-9. Neutral text.**
Internal labels in rulings and notes were replaced by plain statements of the same content (for example the two limits of the shared fixture); the outcomes, states and rulings of all 121 scenarios were compared with the earlier drafts at build time and are identical. This comparison cannot be repeated from the repository.

**C-10. Records held by the owner.**
The author's method note with the draft table and the checker's record are not in this repository and are not quoted; `owner-held-records.json` records their sha256 so that the freeze amendment can name them. Owner decision needed: keep them private and name only the digests, or publish a neutral version.

## Open items that need the owner or a later step

1. Cell aggregation, report generator, contract self-check and stub adapters of the Wiki-subset runner do not exist yet. The draft of the freeze amendment has placeholders for them; they cannot be filled from this package.
2. The declarations of not expressible and not claimed for the protected destination (amendment 76, citations required) are not authored; the plan file holds the scenarios that the comparators are asked and carries only the one citation already on record (amendment 39, TC-D13-003). The per-configuration counts for the destination column are therefore not available.
3. C-1, C-2, C-4, C-5 and C-10 above.
4. The freeze amendment must be updated for the paths, the counts (C-4) and the new digests in `DIGESTS.md`; any later change to a listed file changes its digest.
