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
Update: decided in favour of extending the world (C-11 to C-17): a gap in the comparator world is not a reason to declare a scenario not expressible, because that would look like hiding a result. The eight are executable.

Update (C-11 to C-17): the eight were made executable by extending the declared world; the plan file now counts asked 94, not expressible 11, not claimed 0, not asked 16, equal to the outcome files, and no scenario is set aside by plan authoring. The sentence above about the draft of the freeze amendment is superseded: it states 94 and 11.

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

## Extensions of the declared world (the eight scenarios of C-5)

Rule for every item below: the extension is what a plain transactional application with an OPA decision point, and the same application with an interrupt and resume graph in front of it, would have for the control that the scenario text names. It is added once, to the one application that both configurations share, so both get the same world. No extension reads a plan, a case or any result; no scenario was run against an expected outcome to shape it; the plumbing of the eight new step lists was checked on renamed twins (`harness/plumbing_twin.py`) with the verdicts discarded. Every expected status and effect count is the value of the outcome files, unchanged. Each extension has tests in `tests/test_world_extensions.py` that also show what it must not change, and an item under `world_extensions` in `wiki/interface/declared-interface-opa-app.json`.

**C-11. A second delegation record that cannot expire before the check (TC-D09-011-S4).**
The scenario revokes a delegation and checks an in-scope action at revocation + 600 units (clock 700). The only delegation record (`deleg-1`) expires at clock 200, so a denial at 700 could not be attributed to the revocation.
Chosen: `deleg-2`, the same scope as `deleg-1` (user-a, read_file, data class public) with expiry 10000, the same expiry the per-agent grants carry. `deleg-1` and its scenarios are untouched. No new rule: the delegation rules already read the record.
Alternative: a control that sets the expiry of a delegation record, or keeping S4 not expressible. Reverse: remove the `deleg-2` entry from `initial_state` in `wiki_config.py`, the scenario steps in `author_plan.py` and the tests of C-11.

**C-12. Budget cap change control (TC-D13-003-S6).**
The scenario raises the key budget from 3 to 5 after it was exhausted and checks one effect at +6 minutes. No control wrote a budget cap.
Chosen: the control `set_budget:<level>:<id>:<cap>` writes the cap of one existing budget record and keeps its usage counter; the rule `BUDGET_LEVEL_EXHAUSTED` reads the record as before. An unknown level or id raises KeyError, a cap that is not a non-negative integer raises ValueError, never a silent no-op.
Alternative: a world with a second key budget of cap 5 (does not carry the change of a cap, which is what the scenario asks), or not expressible. Reverse: remove `_verb_set_budget`, its entry in the declared interface and in `VERB_ARITY` of `validate_plan.py`, the scenario and the tests.

**C-13. Allow-list removal control (TC-L06-013-S4).**
The scenario removes one tool from one agent and checks the immediate effect. The controls only added to an allow-list (`allow_tool`).
Chosen: the control `disallow_tool:<agent>:<tool>` is the inverse of `allow_tool`: the tool leaves the agent's allow-list and its read class. A tool that is not on the list raises KeyError. A live exception record is a separate record and is not touched (tested). No new rule.
Alternative: not expressible. Reverse: remove `_verb_disallow_tool`, its declared-interface and `VERB_ARITY` entries, the scenario and the tests.

**C-14. A token with the read scope only (TC-L09-004-S5).**
Every declared grant carried both token scopes, so a write with a read-only token could not be formed.
Chosen: one more grant, `grant-agent-ro`, for the agent "agent" with the token scope `read:tickets` only (same environment and validity as the per-agent grants). It is an ordinary grant in every other respect (revocation, budget, expiry). The rule `SCOPE_NOT_GRANTED` reads the scopes of the grant as before.
Alternative: a control that narrows the scopes of a grant, or not expressible. Reverse: remove the `grant-agent-ro` line in `initial_state`, the scenario and the tests.

**C-15. Environment of the destination (TC-L09-019-S2).**
The destination environment was fixed to prod, so a prod token at a non-prod destination could not be formed.
Chosen: the control `set_environment:<prod|non-prod>` sets the environment of the destination (default prod). The rule `ENVIRONMENT_MISMATCH` compares it with the grant and with the environment claim as before. Any other value raises KeyError.
Alternative: a second destination file configured as non-prod (a different harness shape; the runner drives one destination per case), or not expressible. Reverse: remove `_verb_set_environment`, its declared-interface and `VERB_ARITY` entries, the scenario and the tests.

**C-16. The tools that the user's request requires (TC-L07-008-S1 and S2).**
The pass statement separates a call that the user's request warrants from a call to a tool that the agent and the user both hold but the request does not need. The request had no field or claim for the user's request.
Chosen: the issuer claim `task_tools` (a list of tool names: the tools that the request requires, as stated by the issuer, in the same place as the existing task claim `task_expires_at`). A call to a tool outside the list is denied (`TASK_TOOL_NOT_WARRANTED`, control family `task_scope`, which has a control-removal probe). An empty list means that the request needs no tool; no claim means no task limit (as for every other optional claim); a value that is not a list of strings is `CLAIMS_INVALID`. An exception record does not warrant a tool. S1 carries the empty list, S2 the list of the one tool of each call. The rule is written from the scenario text; it contains nothing aimed at one application or at one outcome. The request still has the eight fields of the registered interface; the claim travels in `issuer_claims`, which the protected destination never reads (stated in the declared interface).
Alternative: a payload key for the request text (needs text understanding, which a rule engine does not have), or not expressible. Reverse: remove the rule `TASK_TOOL_NOT_WARRANTED` from `wiki_policy.rego`, the family `task_scope`, the reason name, the claim check in `claims_well_formed`, the scenarios and the tests.

**C-17. One parameter envelope for the four mock tools (TC-L06-014-S1 and TC-L07-008-S2).**
Both scenarios have several accepted effects on different tools. The scoring function compares the payload of every effect with one expected payload, and the tools had closed schemas with different required keys, so no payload satisfied two of them.
Chosen: send_email, transfer_test_funds, read_file and update_records share one parameter envelope (recipient, body, amount, account, path, records). Each tool requires its own parameter; the other keys of the envelope are optional for it and are checked by type and by the parameter rules when present (those rules already apply to every tool by key). A key outside the envelope is still an unknown argument, a missing own parameter, a wrong type, an out-of-policy value and a non-object payload are still denied (tests for all four tools). The four calls of each scenario carry one payload that is compliant for every key of the envelope. Tools without a schema (delete_record, list_tickets, sink and the rest) are unchanged. This change is the most open to the objection that it makes the schemas more permissive; it admits a sibling key only, applies to both configurations, and the scenarios L05-022-S2 and L06-014-S2 to S4 and S6, whose denials do not depend on a sibling key, are unchanged in their steps.
Alternative: keep both not expressible with the reason that the oracle compares every effect with one payload (asked 92, not expressible 13), or a ledger that stores a normalised effect record instead of the payload (changes the destination's recorded effect, which the registered adapters do not do). Reverse: restore the four schema entries of the previous `CONFIG` (`send_email` required recipient optional body; `transfer_test_funds` required amount optional account; `read_file` required path; `update_records` required records), remove `tool_schema` and `ENVELOPE_PARAMS`, the two scenarios and the tests.

## Open items that need the owner or a later step

1. Cell aggregation, report generator, contract self-check and stub adapters of the Wiki-subset runner do not exist yet. The draft of the freeze amendment has placeholders for them; they cannot be filled from this package.
2. The declarations of not expressible and not claimed for the protected destination (amendment 76, citations required) are not authored; the plan file holds the scenarios that the comparators are asked and carries only the one citation already on record (amendment 39, TC-D13-003). The per-configuration counts for the destination column are therefore not available.
3. C-1, C-2, C-4, C-5, C-10 and C-11 to C-17 above.
4. The freeze amendment must be updated for the paths, the counts (94 and 11 after C-11 to C-17) and the new digests in `DIGESTS.md`; any later change to a listed file changes its digest.
