# Pre-registration: publication criteria and comparator subset

**Status.** Pre-registration. It is merged before any controller run and before any comparator run. Its registration time is the merge time that the repository host records for the commit that adds this file; no time is written in the file, so it cannot be backdated. Items marked PROPOSED need the owner's confirmation, recorded as an amendment, before the first run. Machine-readable twin: [`process/release-gate/preregistration.json`](../../process/release-gate/preregistration.json), checked against this page and against the repository by `tests/test_release_gate_preregistration.py`.

**Scope.** Bounded synthetic profile only. The comparator applications (the OPA application and the LangGraph plus OPA application) are configured by Cognous, not vendor implementations. This is not independent certification and not production readiness; operational trust stays on HOLD. Linux only.

## 1. Purpose

This page sets, in advance, how the release test results of the Open Control Stack (OCS) will be judged and what the comparison with the two comparator applications may and may not contain. It sets: the publication criteria; the meaning of the words used to report a result; the rules for declaring a known limit or a reclassification before a run; the exact comparator subset; the scoring rule; how a comparator that cannot express a case is reported; the known limits declared for the run; the reporting format; the order of runs; and who may change this page afterwards (nobody; see section 11).

Nothing here is derived from a result. No result of the qualification controller, of any release-gate run or of any comparator configuration was consulted or used. Every inclusion in the comparator subset is written from the text of the case and from the description of the configurations, not from how any configuration behaved. This page is not a verdict, a score or a coverage claim.

## 2. The publication criteria

These are the criteria as the owner agreed them on 18 October 2026.

- **PC-1.** OCS passes 100% of its applicable suites in all three categories: synthetic individual-component tests (gate OCS-1), synthetic cross-component tests (gate OCS-2), and Wiki-derived tests split into individual-component (W-I) and cross-component (W-X) cases (gate OCS-3).
- **PC-2.** Passing means green with no unexplained skips and no unexplained xfails.
- **PC-3.** Known-limit tests are listed separately from ordinary passes.
- **PC-4.** A failing applicable test blocks publication until it is fixed or reclassified. The reclassification and its reason are recorded before the result is seen.
- **PC-5.** The comparators (the OPA transactional application and the LangGraph plus OPA application) run only on the 19 corner scenarios, the 24 baseline scenarios and a Wiki subset pre-registered per case, with identical scoring for OCS and for each comparator.
- **PC-6.** All results are reported honestly, including cases where a comparator passes and OCS does not.
- **PC-7.** The scope text is unchanged: Bounded synthetic profile only. The comparator applications (the OPA application and the LangGraph plus OPA application) are configured by Cognous, not vendor implementations. This is not independent certification and not production readiness; operational trust stays on HOLD. Linux only.
- **PC-8.** A statement that one configuration scores higher is made only where both configurations were run.

The release test inventory ([`docs/test-inventory.md`](../test-inventory.md), twin [`process/release-gate/inventory.json`](../../process/release-gate/inventory.json)) lists the suites in each category. The comparison is a separate observation and never replaces the OCS gate: OCS passes its release gate when OCS-1, OCS-2 and OCS-3 are 100% under PC-1 to PC-4; the comparison then reports what identical scoring showed on three declared sets.

## 3. Definitions

Each term below has one meaning in every report of the gate.

- **pass.** A test that ran in the documented environment and ended in the outcome "passed", with no skip and no expected failure involved. For a comparison, a trial passes when the oracle in the Scoring section reports it; a case passes for a configuration when every one of its trials passes.
- **fail.** An applicable test that errors, fails, or is a strict expected failure that unexpectedly passes; a comparison case in which at least one trial does not pass the oracle. A failing applicable test stays in the denominator and blocks publication under PC-4.
- **known limit.** A stated boundary of the stack: something it does not check, record or guarantee, which the documentation says. A known-limit test passes by showing the limit as it is; the negative fact is the assertion. It is reported in the PASSING-AS-KNOWN-LIMIT column, listed apart from ordinary passes, and never counted as an ordinary pass. A strict expected failure counts as a known limit only if it is declared in this document (or in an appended amendment) before the run that could show its result.
- **not claimed.** A statement that the stack makes no claim about something a case asks for. The part of a case that is claimed is tested and counts; the part that is not claimed is stated in the case's not_claimed sentence in applicability.json and is not scored. In a comparison, a configuration for which a case asks for something that configuration does not claim is reported as not claimed, which is neither a pass nor a fail.
- **not applicable.** A capability the stack does not have or that the owner scoped out, decided from the declared scope and never from results. It is listed with a one-line reason and is outside the denominator. In applicability.json these are the cases classed NOT_APPLICABLE.
- **skipped.** A test that did not run: a skip mark, an in-body skip, an unset environment variable that excludes a module from collection, or a missing checkout. A skip is allowed only if inventory.json lists it with a reason and the environment it needs; a skip that is not listed fails the gate. A skip is never a pass, and a module that was not collected gives no result, which is reported as no result.
- **xfail.** An expected-failure mark. Every xfail in a gate suite must be strict. A strict xfail that fails as asserted is a known limit only if declared before the run; an undeclared xfail is an unexplained xfail and fails the gate; a strict xfail that passes is a failure.
- **not expressible.** A recorded outcome for a comparator configuration, not a pass and not a fail: the case asks a question that the configuration, as configured by Cognous, has no way to be asked or to answer. It is declared per case and per configuration before any run, with a reason from the case text and the configuration's declared interface. See the section on not-expressible cases. (PROPOSED for owner review; the pilot specification has no such outcome.)
- **could not check.** A recorded outcome when a harness, adapter or trial could not complete (a crash, a timeout or an unparseable reply). It is never a pass; the reason text is kept. (PROPOSED for owner review; taken from the three-valued verdict rule of the pilot specification and applied to the comparison harness.)

## 4. How a known limit or a reclassification is declared before a run

- **DR-1.** A known-limit declaration names the exact test id (module, function and parameter), states the limit in one neutral sentence, and is recorded in this document or in an appended amendment before the run that could show the result. The time of recording is the time the repository host records for the change that adds it.
- **DR-2.** A declaration made after a result was seen has no effect on that result. The result stays as observed, the failed attempt stays in the retained evidence, and a failing applicable test still blocks publication.
- **DR-3.** A reclassification (known limit, not applicable, or a test that lags its component) is made only by the owner or by an owner-approved delegate, with the test id, the date and the reason in writing. It takes effect only for runs that start after it was recorded. A reclassification recorded after an earlier run showed the failure is reported as such, with the earlier run named.
- **DR-4.** A known-limit test is never changed to make it pass. Its assertions, fixtures and expected values stay as they are; a test that is replaced keeps the old id as a retired row with the failure text that retired it.
- **DR-5.** Not applicable is decided from the declared scope, not from a result. An applicable case or test stays in the denominator even if it fails.
- **DR-6.** A skip is declared only by inventory.json (reason and environment). A skip not listed there fails the gate. This document declares no skips.
- **DR-7.** A strict expected failure that is not declared as a known limit is an unexplained xfail and fails the gate. A strict expected failure that passes fails the run; its mark is then removed in a later change and the probe counts as an ordinary test from the next run.
- **DR-8.** A declaration is made for one named test or one named requirement selector. A declaration for a group, a directory or a pattern is not valid.
- **DR-9.** Anything not declared here or by amendment before a run is treated as undeclared: a test in the known-limit class that is not on a list is reported in the ordinary passing column if it passes, and a failure of it blocks publication.

## 5. The comparator subset

Comparators run only on three sets (PC-5). The configurations are synthetic, local, with no model, cloud, payment or human reviewer: the OCS reference (the optional protected destination), the OPA transactional application (an OPA policy plus application controls written by the benchmark authors), and the LangGraph plus OPA application (a LangGraph graph with a checkpoint and interrupt in front of the same OPA application). The two comparators are configured by Cognous and are not vendor implementations. The application controls in them are application responsibilities, not guarantees of OPA or LangGraph.

The plans carry their own caveats, which stay with every report: the corner plan states that it is an exploratory extension authored after inspection of the baseline code and is not blinded, and both plans state that no independent review took place. The plan files, the policy file and the scoring function are pinned by digest in the JSON twin; a change to any of them before the run is an amendment.

### 5.1 Corner scenarios (19)

Source: [`corner-plan.json`](../../suites/cognous-open-control-stack/benchmarks/governance/corner-plan.json), seeds 1701 and 1702, 5 repetitions per seed.

| # | Scenario id |
|---|---|
| 1 | `permitted` |
| 2 | `revoked_before_effect` |
| 3 | `changed_target` |
| 4 | `missing_verifier` |
| 5 | `budget_exhaustion` |
| 6 | `verifier_wrong_command` |
| 7 | `verifier_wrong_digest` |
| 8 | `verifier_inactive` |
| 9 | `verifier_wrong_generation` |
| 10 | `verifier_future` |
| 11 | `verifier_expiry_boundary` |
| 12 | `payload_changed_after_verification` |
| 13 | `payload_changed_without_resigning` |
| 14 | `unknown_argument` |
| 15 | `empty_effect_identifier` |
| 16 | `unknown_body_field` |
| 17 | `unknown_verifier_field` |
| 18 | `wrong_operation` |
| 19 | `exact_command_replay` |

### 5.2 Baseline scenarios (24)

Source: [`plan.json`](../../suites/cognous-open-control-stack/benchmarks/governance/plan.json), seeds 1701 and 1702, 10 repetitions per seed.

| # | Scenario id |
|---|---|
| 1 | `permitted` |
| 2 | `missing_grant` |
| 3 | `revoked_before_effect` |
| 4 | `expiry_boundary` |
| 5 | `stale_generation` |
| 6 | `unissued_generation` |
| 7 | `changed_policy` |
| 8 | `changed_target` |
| 9 | `missing_verifier` |
| 10 | `stale_verifier` |
| 11 | `forged_signature` |
| 12 | `direct_agent` |
| 13 | `hard_pin_rotation` |
| 14 | `lost_ack_restart` |
| 15 | `conflicting_redelivery` |
| 16 | `budget_exhaustion` |
| 17 | `revocation_after_commit_read_receipt` |
| 18 | `revocation_after_commit_new_effect` |
| 19 | `audit_write_failure` |
| 20 | `concurrent_last_budget` |
| 21 | `stale_signed_request` |
| 22 | `captured_request_then_revocation` |
| 23 | `crash_before_commit` |
| 24 | `crash_after_commit` |

### 5.3 Wiki subset

The pool is the 65 AI Security Wiki cases that `applicability.json` (version 1.0.0, catalog commit `1a0c72de`) classes APPLICABLE or PARTLY_COVERED. That classification was made from the declared scope of OCS before any result was consulted. A comparator can be asked only a question it can express, so each case is judged on two points, both from the case text:

- **R1.** The case's own pass statement is an allow, refuse or hold on an action, or an effect count at a destination.
- **R2.** A generic authorization or policy engine, together with application controls of the kind both comparator applications already have (a writer transaction, state, a signature check, effect-identity idempotency, a durable audit record), could in principle be configured to express it without a component the comparators lack (an identity provider, a gateway, a log store, a replay tool, monitoring or a directory).

A case that meets both is included. A case that fails either is excluded, with the reason. The column "Generic engine could express" says yes, partly or no for R2 alone. For a partly case, the reason names the part that is asked. Case titles are not repeated here; the ids resolve in `catalog.json`.

The subset is 28 included cases and 37 excluded cases. Inclusion settles the case, not its translation into a scenario; the translation is a later plan file (PR-6) that may not change the inclusion. Excluded cases stay in the OCS gate under OCS-3 where applicable; excluding a case from the comparison says nothing about OCS on it.

#### Included (28)

| Case | Class | Split | Components | Generic engine could express | Reason (from the case text) |
|---|---|---|---|---|---|
| `TC-D09-009` | PARTLY_COVERED | cross-component | control-plane, execution-runtime | partly | Asks that elevated access exists only inside a 15-minute window and that expired access is refused; a time-window check on a grant is a standard policy input. Asked: effect inside the window, refusal after it. Approval modes and slow-approval timing are not asked. |
| `TC-D09-011` | PARTLY_COVERED | individual-component | control-plane | partly | Asks that an action outside a delegation's scope is blocked and that a revoked delegation stops working; scope and revocation are data a policy rule can read. Asked: in-scope and out-of-scope actions, effect after revocation. Export completeness is not asked. |
| `TC-D13-003` | PARTLY_COVERED | cross-component | execution-runtime, control-plane | yes | Asks that each level of nested budgets stops at its own limit while sibling levels continue; per-level counters held by the application can express it. Included as written; the owner decision on whether OCS claims this case is open (see Decisions still open). |
| `TC-L02-011` | PARTLY_COVERED | cross-component | control-plane, execution-runtime | yes | Asks that an exception that opened a control stops working at expiry; an expiry time on an exception record is a standard policy input. |
| `TC-L05-013` | APPLICABLE | cross-component | control-plane, execution-runtime | partly | Asks that when the protection component is stopped the application behaves as configured (fail open or fail closed); a configuration can express the fail-closed mode. Asked: effect count while the check component is unavailable. Alerting and mode switching are not asked. |
| `TC-L05-022` | APPLICABLE | cross-component | action-manifest, control-plane | yes | Asks that function-call arguments violating a schema or policy are blocked and valid calls pass; schema and argument rules are the core use of a policy engine. |
| `TC-L06-008` | PARTLY_COVERED | cross-component | action-manifest, control-plane | partly | Asks that a tool definition changed after approval is blocked until re-approval; a digest of the approved definition compared at call time can express it. Asked: call with a changed definition. Detection interval is not asked. |
| `TC-L06-009` | PARTLY_COVERED | cross-component | action-manifest, execution-runtime | partly | Asks that identical, case-varied, look-alike and prefix-removed tool names do not reach the trusted tool's authority; exact-match allow-listing by tool identity can express the refusal. Asked: call naming each variant. Server attribution display is not asked. |
| `TC-L06-011` | PARTLY_COVERED | cross-component | action-manifest, execution-runtime | yes | Asks that every combination of agent, user and tool matches a per-tool allow or deny matrix; an allow/deny table keyed by agent, user and tool is a direct policy expression. |
| `TC-L06-013` | APPLICABLE | cross-component | action-manifest, control-plane, execution-runtime | yes | Asks that each agent can call only the tools on its own allow-list and that out-of-list calls are blocked; a per-agent allow-list is a direct policy expression. |
| `TC-L06-014` | APPLICABLE | cross-component | action-manifest, control-plane, execution-runtime | yes | Asks that tool calls violating parameter rules (recipient domain, amount limit, path, record count) are blocked and compliant calls pass; parameter-level rules are a direct policy expression. |
| `TC-L06-015` | APPLICABLE | cross-component | control-plane, execution-runtime | partly | Asks that risky actions are held for approval and that rejected or timed-out actions do not run; a hold-until-approved step can express it. Asked: effect count after approve, reject and timeout. Approver context display is not asked. |
| `TC-L06-016` | PARTLY_COVERED | cross-component | execution-runtime, control-plane | partly | Asks that one large action split into many small ones is treated as one aggregate and that repeated identical requests do not multiply effects; an aggregate counter and an effect identity can express both. Wording and visual-distinction items are not asked. |
| `TC-L06-017` | PARTLY_COVERED | individual-component | control-plane | yes | Asks that a sub-agent never holds more than its parent and that chain depth is limited; a subset check and a depth bound on a delegation chain can be expressed as rules. |
| `TC-L06-019` | PARTLY_COVERED | cross-component | control-plane, execution-runtime | yes | Asks that a standard user is denied privileged actions even when the agent's own reach is wider; a rule comparing the requesting user's entitlement with the action can express it. |
| `TC-L06-022` | PARTLY_COVERED | individual-component | execution-runtime | partly | Asks that no new action runs after a stop is triggered for one agent while other agents continue and the stopped state persists; a persistent stop flag read at decision time can express it. In-flight call documentation is not asked. |
| `TC-L06-023` | PARTLY_COVERED | cross-component | control-plane, execution-runtime | partly | Asks that revoked credentials are unusable and that the list of actions taken is complete; revocation state and an audit log can express both. Rollback support is not asked. |
| `TC-L06-024` | PARTLY_COVERED | individual-component | execution-runtime | partly | Asks that per-window caps on updates, sends and deletes are enforced exactly and reset on schedule; counters with a time window held by the application can express it. Alert at 80 percent is not asked. |
| `TC-L06-034` | PARTLY_COVERED | cross-component | action-manifest, control-plane | partly | Asks that a change to model, prompt, tool, data scope or owner after approval restricts the agent until re-approval; a digest of the approved configuration compared at call time can express it. Asked: call after each change. Classification of which changes are material is not asked. |
| `TC-L06-039` | APPLICABLE | cross-component | governed-exchange, control-plane, execution-runtime | partly | Asks that a request from a low-privilege agent is authorised against both the calling agent and the originating user; a rule over caller, user and action can express it. Asked at the request level; the message transport between agents is not asked. |
| `TC-L07-008` | PARTLY_COVERED | cross-component | control-plane, execution-runtime | partly | Asks that a tool call that the user's request did not warrant is stopped before the action runs while legitimate calls pass; an allow-list at the destination can express the refusal. Asked: effect count for unwarranted calls. Detection of the text that prompted the call is not asked. |
| `TC-L09-003` | PARTLY_COVERED | cross-component | control-plane, execution-runtime | partly | Asks that expired, wrong-audience and over-scope tokens are rejected; expiry, audience and scope are standard token claims a rule can check. Flagging of static long-lived keys is not asked. |
| `TC-L09-004` | APPLICABLE | cross-component | control-plane, execution-runtime | yes | Asks that calls outside a token's scope (tickets versus payroll and files) are rejected; a scope check is a direct policy expression. |
| `TC-L09-006` | PARTLY_COVERED | cross-component | control-plane, execution-runtime | partly | Asks that downstream calls carry the end user's identity and that substitution is rejected; a rule comparing the presented identity with the authenticated one can express the rejection. Downstream recording of identity is not asked. |
| `TC-L09-007` | PARTLY_COVERED | cross-component | control-plane, execution-runtime | partly | Asks that attempts to use tools that edit roles, read credentials or create agents are blocked; an allow-list can express the block. Identification of the escalation paths is not asked. |
| `TC-L09-014` | PARTLY_COVERED | cross-component | control-plane, execution-runtime | partly | Asks that expired keys are rejected and revocation is immediate; expiry and revocation state are inputs a rule can check. Rotation window and usage reminders are not asked. |
| `TC-L09-018` | PARTLY_COVERED | cross-component | control-plane, execution-runtime | partly | Asks that identity claimed in text, headers or fields is rejected and identity is taken from the authenticated source; a rule that reads only the authenticated principal can express it. The result depends on how the application supplies the authenticated principal, which is part of the configuration. |
| `TC-L09-019` | PARTLY_COVERED | cross-component | control-plane, execution-runtime | yes | Asks that a token or agent from a non-production environment is blocked at a production-like destination; an environment or audience claim check is a direct policy expression. |

#### Excluded (37)

| Case | Class | Split | Components | Generic engine could express | Reason (from the case text) |
|---|---|---|---|---|---|
| `TC-D09-004` | PARTLY_COVERED | individual-component | control-plane | no | Asks for agreement with a reviewer on risk tiers for 15 agents and flags for agents short of tier controls; no action at a destination is observed. |
| `TC-D09-016` | PARTLY_COVERED | cross-component | control-plane, execution-runtime | no | Asks for revocation to take effect within 5 minutes in four separate systems (identity provider, cloud, SaaS, gateway); the comparators have one destination and none of those systems. |
| `TC-D12-004` | APPLICABLE | cross-component | control-plane, replay-bundle, evidence-pack | no | Asks for a point-in-time snapshot of model, prompt, tools and policy that is exportable and tamper-evident; a records property, no decision or effect is observed. |
| `TC-D12-007` | PARTLY_COVERED | cross-component | replay-bundle, control-plane | no | Asks for replay of recorded incidents with a fidelity report; a records and reconstruction property, no decision or effect is observed. |
| `TC-D12-018` | APPLICABLE | cross-component | replay-bundle, evidence-pack, verifier | no | Asks that evidence items are hashed with a custody trail and that an altered item is detected; a records property, no decision or effect is observed. |
| `TC-D12-021` | PARTLY_COVERED | cross-component | control-plane, replay-bundle, execution-runtime | no | Asks that near-misses are captured, clustered and reviewed weekly with improvements; a review process, no decision or effect is observed. |
| `TC-L02-002` | PARTLY_COVERED | individual-component | control-plane | no | Asks that policy statements are mapped to enforcing controls and evidence; a documentation mapping, no decision or effect is observed. |
| `TC-L02-016` | APPLICABLE | cross-component | evidence-pack, replay-bundle | no | Asks that an evidence pack for a chosen framework is produced on demand; a reporting property, no decision or effect is observed. |
| `TC-L02-025` | APPLICABLE | cross-component | control-plane, verifier | no | Asks for change history and tamper evidence on governance records edited by three roles; a records property, no decision or effect is observed. |
| `TC-L03-022` | APPLICABLE | cross-component | replay-bundle, evidence-pack, odes | no | Asks that evidence exports in each offered format are complete and carry integrity proof; a reporting property, no decision or effect is observed. |
| `TC-L05-012` | PARTLY_COVERED | individual-component | execution-runtime | no | Asks that a coverage report correctly shows which of four applications have protection deployed; an inventory report, no decision or effect is observed. |
| `TC-L05-028` | PARTLY_COVERED | individual-component | control-plane | partly | Asks that an application policy can be exported, edited, re-imported and shown in a version history; policy-as-code is expressible, but the observed object is a policy round trip, not an action at a destination. |
| `TC-L06-003` | PARTLY_COVERED | cross-component | governed-exchange, execution-runtime | no | Asks that agents run on workstations and in personal accounts are discovered; endpoint and traffic discovery, not an action at a destination. |
| `TC-L06-007` | PARTLY_COVERED | cross-component | action-manifest, control-plane | no | Asks that hidden instructions in tool descriptions, parameter text and zero-width characters are detected before the model sees them; content inspection of metadata, not an authorization decision. |
| `TC-L06-018` | APPLICABLE | individual-component | governed-exchange | partly | Asks that forged, modified and replayed messages between two agents are rejected; signature and replay checks are expressible, but the observed object is an agent-to-agent message channel, which the comparators do not have. |
| `TC-L06-020` | PARTLY_COVERED | cross-component | governed-exchange, control-plane, execution-runtime | no | Asks that hostile content in a three-agent chain is stopped at an inter-agent boundary and the hop is recorded; needs an agent chain and a boundary the comparators do not have. |
| `TC-L06-026` | PARTLY_COVERED | individual-component | execution-runtime | partly | Asks that file paths and network destinations outside an allow-list are blocked on an endpoint or container; allow-lists are expressible, but the observed object is endpoint and network behaviour, not an action at the synthetic destination. |
| `TC-L06-028` | APPLICABLE | cross-component | control-plane, replay-bundle, verifier | no | Asks that a 15-step task is reconstructable from logs with masking and tamper evidence; a records property, no decision or effect is observed. |
| `TC-L06-038` | PARTLY_COVERED | individual-component | governed-exchange | partly | Asks that links outside a declared agent-to-agent trust map are flagged and map changes carry an approver; a map is expressible as data, but the observed object is an inter-agent call graph, which the comparators do not have. |
| `TC-L06-040` | APPLICABLE | individual-component | governed-exchange | partly | Asks that agent-to-agent messages are checked against a published schema, including oversized and extra-field messages; schema checks are expressible, but the observed object is a message channel between agents, which the comparators do not have. |
| `TC-L06-041` | PARTLY_COVERED | individual-component | governed-exchange | no | Asks that a client agent never routes to rogue entries in an agent directory; needs a directory and discovery step the comparators do not have. |
| `TC-L06-045` | APPLICABLE | cross-component | governed-exchange, control-plane, replay-bundle | no | Asks that user requests are reconstructed across four agents from one identifier; a cross-agent log correlation property, no decision or effect is observed. |
| `TC-L07-009` | PARTLY_COVERED | cross-component | governed-exchange, control-plane, execution-runtime | no | Asks that hidden instructions in web pages are neutralised or flagged and the content origin is recorded; content inspection of fetched pages, not an authorization decision. |
| `TC-L07-012` | PARTLY_COVERED | cross-component | governed-exchange, control-plane, execution-runtime | no | Asks that instruction text in retrieved knowledge documents is neutralised or flagged and the chunk quarantined; content inspection of a retrieval store, not an authorization decision. |
| `TC-L07-013` | PARTLY_COVERED | cross-component | governed-exchange, control-plane, execution-runtime | no | Asks that instruction text inside tool responses is neutralised and tool-result inspection is confirmed or its absence documented; content inspection of tool output, not an authorization decision. |
| `TC-L08-033` | PARTLY_COVERED | individual-component | execution-runtime | no | Asks that blocked content stays blocked at up to twice the expected peak load with timed recovery; a load and timing measurement, and wall times are descriptive only in the comparison. |
| `TC-L08-036` | PARTLY_COVERED | individual-component | control-plane | partly | Asks that a rule change takes effect on every component within a stated time and can be rolled back; rule change is expressible, but the pass statement is propagation time across components, and the comparators are single-process. |
| `TC-L09-025` | APPLICABLE | cross-component | control-plane, replay-bundle | no | Asks that nine of ten actions across four systems are fully attributable with integrity protection; a records property, no decision or effect is observed. |
| `TC-L15-019` | PARTLY_COVERED | cross-component | execution-runtime, control-plane | no | Asks that a model, vector store, prompts and policies are restored within recovery targets, with encrypted backups and regional limits; needs components and properties the comparators do not have. |
| `TC-L16-007` | PARTLY_COVERED | individual-component | replay-bundle | no | Asks that a public package with an internal package's name is never selected by a build; a build and package-index property with no destination action. |
| `TC-L16-015` | PARTLY_COVERED | individual-component | replay-bundle | no | Asks that a tampered SDK release is blocked and floating versions are reported; a package-index and version-pinning property with no destination action. |
| `TC-L17-002` | APPLICABLE | cross-component | odes, control-plane | no | Asks that events carry required fields with consistent names and time format; an event-schema property, no decision or effect is observed. |
| `TC-L17-004` | APPLICABLE | cross-component | control-plane, verifier, replay-bundle, evidence-pack | no | Asks that log edits and deletions by administrators are blocked or detected and exports are signed; a log-integrity property, no decision or effect is observed. |
| `TC-L17-020` | PARTLY_COVERED | cross-component | replay-bundle, control-plane | no | Asks that scripted conversations and tool calls are reconstructed from platform records; a records and reconstruction property, no decision or effect is observed. |
| `TC-L17-021` | APPLICABLE | cross-component | replay-bundle, evidence-pack, verifier | no | Asks that preserved records are immune to deletion and altered copies fail verification; a records property, no decision or effect is observed. |
| `TC-L17-022` | PARTLY_COVERED | cross-component | control-plane, verifier | no | Asks that 40 events across users, agents and tools are placed in the right order with pivots and export; a timeline reconstruction property, no decision or effect is observed. |
| `TC-L17-028` | PARTLY_COVERED | cross-component | execution-runtime, control-plane | no | Asks that six induced failures of the platform itself (agent offline, node down, ingestion stopped and similar) are alerted within 10 minutes; monitoring and alert routing, not an action at a destination. |

## 6. Scoring: identical for OCS and for each comparator

**Source of the rule.** The scoring function is `evaluate` in [`run_comparative_governance.py`](../../suites/cognous-open-control-stack/tools/run_comparative_governance.py). The same code path scores every configuration; its source digest is in the JSON twin. A trial passes when all of these hold:

- decision conformance: the sequence of statuses equals the expected statuses
- destination conformance: the effect count equals the expected count, every effect id is allowed, and every payload equals the expected payload
- reason conformance: where the plan lists expected reason codes for the configuration, the reasons equal them
- durable denial coverage: every denied call has a matching durable denial event with the request digest, a reason and an integer time

A case passes for a configuration when every one of its trials passes (trials are the repetitions over the two seeds). The counts reported with each set are: trials passed, unexpected effects, missing effects, false allows, false blocks, denied calls, durably recorded denials. Wall times are descriptive only. There is no aggregate score across sets and no ranking. An expected outcome comes from the case's own pass statement, never from what a configuration did. An observed mismatch stays a recorded mismatch.

**What the pilot specification provides.** The comparator pilot specification (PREP-8) is a three-valued interoperability protocol (accept, refuse, could_not_check). This page takes from it: the case list and verdict vocabulary are recorded in writing before the first run; unknown never becomes accept; every refusal and every could-not-check is kept with its reason; results are published side by side with scope and limits; neither side edits the other's column; a disputed result is published with the dispute; the harness, cases and pinned revision set are published together.

**What it lacks, proposed here.** The pilot specification has no per-case pass or fail rule (it reports agreement with an expected verdict and says disagreement is a finding, not a score), no outcome for a question a configuration cannot be asked, no rule for repeated trials and seeds, no source label for expected outcomes written from case text, and no rule for a comparator reported again with an added check. This page supplies the first by taking the oracle above and the trial rule from the plans. It proposes the rest:

- **PR-1.** The outcome not expressible and the rules for declaring and reporting it (the pilot specification has none).
- **PR-2.** The outcome could not check applied to the comparison harness, taken from the pilot specification's three-valued verdict rule.
- **PR-3.** For Wiki-subset scenarios, expected outcomes are written from the case text by two reviewers other than the author of the OCS code; a case on which the two disagree leaves the comparison and stays in W-I or W-X.
- **PR-4.** A second row for a comparator with an equivalent check added after a failure, reported separately and labelled as configured by Cognous after the failure was seen. Both rows are published.
- **PR-5.** Wiki-subset scenarios use the same seeds and repetitions as the corner plan (seeds 1701 and 1702, five repetitions).
- **PR-6.** The per-case, per-configuration translation of each included Wiki case (inputs, expected statuses, effects and reasons) and any per-configuration not-expressible declaration go in a plan file committed and digested before the first run of any Wiki-subset scenario.
- **PR-7.** The comparison runs only after the three OCS gates are green and never in place of them.

## 7. Cases a comparator cannot express

Not expressible is a recorded outcome. It is not a pass for the comparator and not a fail for it, and it is never counted in a pass fraction. It is reported as follows (PROPOSED, PR-1):

- It is declared per case and per configuration before the first run, in the plan file of PR-6, with a reason taken from the case text and the configuration's declared interface (for example, an input the configuration's request format has no field for). A declaration made after a run has no effect on that run.
- A configuration that is asked a question it can express and does not pass it is a fail, even if the plan authors had not written the check. The report may say so in words; the cell stays fail. A comparator reported again with a check added after the failure is a separate, labelled row (PR-4).
- A not-expressible cell shows the reason text. The per-set counts show pass, fail, not expressible, not claimed and could not check as separate numbers, so that a reader sees how many cases a configuration was asked and how many it could not be asked.
- Not expressible says what the configured application can be asked. It does not say what OPA or LangGraph could do in other hands, and the report states that.
- The same applies to OCS in the form not claimed: a case or part of a case that OCS does not claim is reported as not claimed, never as a pass.

## 8. Known limits declared for the run

These declarations are made before any run (DR-1). They follow the rules of section 4. Declaring a limit does not turn it into a pass: each is listed apart, with its limit, in the PASSING-AS-KNOWN-LIMIT column or, for the authority-ra probes, in the block described in RP-3.

### 8.1 fix2-probes: the seven known limits that remain

`suites/fix2-probes/KNOWN_LIMITS.md` lists 22 probes kept as strict expected failures. Fifteen of them are the attempt-identity probes that ODES #127 closed in the lifecycle validator; their marks are pending removal after the pin round, so they are **not** declared here (OD-7). The other seven are declared:

| Test id (relative to the suite directory) | Suite | Limit declared |
|---|---|---|
| `test_journal_rules_probes.py::test_probe_a_reconciliation_dated_before_its_attempt_is_refused[verifier]` | X-02 | known limit: does not compare a reconciliation stamp with the start of the attempt it rests on |
| `test_journal_rules_probes.py::test_probe_a_reconciliation_dated_before_its_attempt_is_refused[odes]` | X-02 | known limit: orders stamps within one clock domain only; a service stamp is not compared with the attempt start (evaluation time) |
| `test_journal_rules_probes.py::test_probe_a_closeout_dated_before_its_attempt_is_refused[odes]` | X-02 | known limit: orders stamps within one clock domain only; a service stamp is not compared with the attempt start (evaluation time) |
| `test_runtime_probes.py::test_failure_after_commit_reports_unknown[runtime-error]` | X-02 | known limit: reports status unknown, retry not eligible, with observed_state applied (recovery observation); the probe expects observed_state unknown. The coordinator's recorded decision is to revise this probe's expected observed state at the pin round; any such revision before the run is recorded as an amendment, not as an edit. |
| `test_runtime_probes.py::test_failure_after_commit_reports_unknown[os-error]` | X-02 | known limit: reports status unknown, retry not eligible, with observed_state applied (recovery observation); the probe expects observed_state unknown. The coordinator's recorded decision is to revise this probe's expected observed state at the pin round; any such revision before the run is recorded as an amendment, not as an edit. |
| `test_verifier_probes.py::test_probe_a_binding_member_changed_alone_is_refused_against_the_captured_inputs[journal-applied-effective_max_effects]` | X-02 | known limit: this member is checked against the proposal export and destination ledger only, not against the captured inputs. A follow-up on captured-input binding is open; if it changes this limit before the run, an amendment records it. |
| `test_verifier_probes.py::test_probe_a_binding_member_changed_alone_is_refused_against_the_captured_inputs[journal-applied-requirement_id]` | X-02 | known limit: this member is checked against the proposal export and destination ledger only, not against the captured inputs. A follow-up on captured-input binding is open; if it changes this limit before the run, an amendment records it. |

The 15 not declared:

- `test_journal_rules_probes.py::test_probe_every_contradictory_combination_for_a_status_is_refused[odes-failed]`
- `test_journal_rules_probes.py::test_probe_every_contradictory_combination_for_a_status_is_refused[odes-partial]`
- `test_journal_rules_probes.py::test_probe_every_contradictory_combination_for_a_status_is_refused[odes-unknown]`
- `test_journal_rules_probes.py::test_probe_every_contradictory_combination_for_a_status_is_refused[odes-executed]`
- `test_journal_rules_probes.py::test_probe_every_contradictory_combination_for_a_status_is_refused[odes-reconciled]`
- `test_journal_rules_probes.py::test_probe_a_null_attempt_id_on_an_attempt_claiming_status_is_refused[failed-odes]`
- `test_journal_rules_probes.py::test_probe_a_null_attempt_id_on_an_attempt_claiming_status_is_refused[partial-odes]`
- `test_journal_rules_probes.py::test_probe_a_null_attempt_id_on_an_attempt_claiming_status_is_refused[unknown-odes]`
- `test_journal_rules_probes.py::test_probe_a_null_attempt_id_on_an_attempt_claiming_status_is_refused[executed-odes]`
- `test_journal_rules_probes.py::test_probe_a_null_attempt_id_on_an_attempt_claiming_status_is_refused[reconciled-odes]`
- `test_journal_rules_probes.py::test_probe_a_result_naming_no_attempt_row_is_refused[failed-odes]`
- `test_journal_rules_probes.py::test_probe_a_result_naming_no_attempt_row_is_refused[partial-odes]`
- `test_journal_rules_probes.py::test_probe_a_result_naming_no_attempt_row_is_refused[unknown-odes]`
- `test_journal_rules_probes.py::test_probe_a_result_naming_no_attempt_row_is_refused[executed-odes]`
- `test_journal_rules_probes.py::test_probe_a_result_naming_no_attempt_row_is_refused[reconciled-odes]`

### 8.2 authority-ra probes (requirement ADD-AUTH-RA)

Six probes in `suites/v1-probes/test_authority_ra_probes.py` are strict expected failures recorded as registered findings (spec gap) in `suites/v1-probes/KNOWN_LIMITS.md`. They belong to the requirement ADD-AUTH-RA, whose selector is the component `probes-control-plane` with the pattern `probe_addauthra_`. The JUnit report records a strict expected failure as skipped, so the requirement is computed as inconclusive. The six probes are declared known limits before the run, reported apart from passes and never counted as a pass.

| Test id (relative to the suite directory) | Suite | Limit declared |
|---|---|---|
| `test_authority_ra_probes.py::test_probe_addauthra_opened_event_binds_the_component_version` | X-01 | known limit (registered finding, spec gap): the event does not name the control plane component version |
| `test_authority_ra_probes.py::test_probe_addauthra_resolution_result_records_observation_time_and_age` | X-01 | known limit (registered finding, spec gap): no explicit age value is stored (observation and evaluation times only) |
| `test_authority_ra_probes.py::test_probe_addauthra_evidence_refusal_records_the_criterion_reference` | X-01 | known limit (registered finding, spec gap): the evidence refusal row carries no criterion reference |
| `test_authority_ra_probes.py::test_probe_addauthra_registry_declares_applicable_reopen_predicates` | X-01 | known limit (registered finding, spec gap): the registry declares no reopen predicates per code |
| `test_authority_ra_probes.py::test_probe_addauthra_refusal_trend_report_names_unmapped_codes` | X-01 | known limit (registered finding, spec gap): the report does not name unmapped codes |
| `test_authority_ra_probes.py::test_probe_addauthra_freshness_is_verified_before_the_criterion_is_evaluated` | X-01 | known limit (registered finding, spec gap): the strict order is not observed (both reasons are reported together) |

### 8.3 Wiki-derived known-limit tests

Seven tests in `suites/wiki-derived` carry the suffix or infix `known_limit` and assert a limit as the negative fact. They are declared:

| Test id (relative to the suite directory) | Suite | Limit declared |
|---|---|---|
| `test_wp_b_identity_scope.py::test_wiki_l09_018_host_asserted_authenticated_flag_is_a_known_limit` | W-X | known limit: The authenticated flag on the identity input is taken as asserted by the host and the record of that input carries no provenance for it; the stack authenticates nothing itself |
| `test_wp_b_identity_scope.py::test_wiki_l09_019_shared_engine_database_evidence_status_is_not_tenant_scoped_known_limit` | W-X | known limit: Evidence status is stored once per obligation in the engine database with no tenant; tenants that share one engine database share the status. Separate environments need separate engine databases |
| `test_wp_c_budget_stop_recovery.py::test_wiki_l15_019_restore_of_an_older_backup_readmits_later_effects_known_limit` | W-X | known limit: State lives in local files with no anchor outside them; a consistent restore of an older backup admits again the effects consumed after it was taken |
| `test_wp_d_manifest_change_control.py::test_wiki_l06_009_a_decision_alone_does_not_refuse_two_tools_of_one_name_known_limit` | W-X | known limit: The decision binds the first declared tool of a name and does not run the manifest validator; the manifest validator and the executor allow-list refuse it later. A revision of this test is queued for the pin round; any revision before the run is recorded as an amendment |
| `test_wp_d_manifest_change_control.py::test_wiki_l06_034_a_grant_edited_in_place_without_a_new_revision_is_read_as_current_known_limit` | W-X | known limit: Revision numbers are the resolver's to assign; a permission edited in place under the same revision is read as the current grant |
| `test_wp_e_exchange_injection.py::test_wiki_l06_020_known_limit_the_hop_where_content_was_stopped_is_not_recorded` | W-X | known limit: A refusal before acceptance is returned and not durably recorded; nothing records at which hop the content was stopped |
| `test_wp_e_exchange_injection.py::test_wiki_l06_038_known_limit_a_registry_holds_one_recipient_and_refusals_are_not_stored` | W-I | known limit: A registry holds one recipient and a sender set and no stored trust map; refusals before acceptance are not stored and a refused message does not reserve its identifier |

## 9. Reporting format

- **RP-1.** Gate table: for every suite and test group, three columns, PASSING, PASSING-AS-KNOWN-LIMIT and SKIPPED-WITH-REASON, plus FAILING and NO RESULT where they occur. Counts per column are given as numbers, not as a single percentage.
- **RP-2.** Known limits are listed apart from ordinary passes, each with its test id, the limit as declared here and a pointer to the sentence in the guarantees and limits documentation that states it.
- **RP-3.** The requirement ADD-AUTH-RA (selector probe_addauthra_) is reported in its own block next to its six declared known-limit probes. The six are shown as known limits, never as passes, and the requirement keeps the status the controller computes for it.
- **RP-4.** Comparison tables, one per set (corner, baseline, Wiki subset): one row per case, one column per configuration (OCS, the OPA application, the LangGraph plus OPA application), each cell one of pass, fail, not expressible, not claimed or could not check, with the per-case trial counts and the reason text of every refusal. There is no aggregate score across sets and no ranking.
- **RP-5.** Per set, the counts the oracle already reports: trials passed, unexpected effects, missing effects, false allows, false blocks, denied calls and durably recorded denials. Wall times are descriptive only.
- **RP-6.** A block titled "cases where a comparator passes and OCS does not" is always present. If there are none it says none. Each such case carries the same weight and the same prominence as any other row.
- **RP-7.** A comparative statement (scores higher, passes more) appears only for a set on which both configurations were run, and names the set.
- **RP-8.** The scope text of PC-7 appears unchanged on every gate report and every comparison report, together with the caveats of the plans: the corner plan was authored after inspection of the baseline code and is not blinded, and both plans had no independent review; the shared Cognous wire and signature helpers feed all three configurations.
- **RP-9.** Each report records the candidate id, the commit and sha256 of each plan file, the oracle digest, the candidate manifest digest, the commit of this pre-registration and the list of amendments in force.
- **RP-10.** A result that a party disputes is published together with the dispute. Neither side edits the other's column.

## 10. Order of runs

- **RO-1.** This pre-registration is merged. Its registration time is the merge time recorded by the repository host. No controller run and no comparator run starts before it.
- **RO-2.** The owner reviews the items marked PROPOSED and the entries under Decisions still open. Each confirmation or change is an appended amendment. No run starts while a PROPOSED item that the run depends on is unconfirmed.
- **RO-3.** Known-limit and reclassification declarations for the run are complete (DR-1 to DR-9), and the Wiki-subset plan file (PR-6) is committed, before the candidate manifest run starts.
- **RO-4.** One candidate manifest names the exact revisions to be run. Any change of a pin, a component revision, an inventory row or a reclassification starts a new candidate id.
- **RO-5.** Gate OCS-1 (Category 1), then OCS-2 (Category 2), then OCS-3 (Category 3, W-I and W-X), in the order of the inventory page.
- **RO-6.** The comparison runs on the three declared sets (PC-5) after the gates are green (PR-7), in this order: corner scenarios, baseline scenarios, Wiki subset. Each set is reported as its own table.
- **RO-7.** The qualification controller and aggregate run last, by the coordinator, after the owner's go.
- **RO-8.** Every run, including a failed attempt and a rerun, is retained and reported. Retained results are not edited.

Items RO-2 and RO-6 depend on PROPOSED items (PR-7 for the order of the comparison). The invariant that does not depend on any proposal: this page is merged before any run.

## 11. Who may change this page after a run

Nobody edits this document or its JSON twin after the registration commit. A change is an amendment appended below, with a UTC timestamp and a reason; the earlier text stays as it was. An amendment never changes the meaning of a rule for a run that has already started, never removes a case from a comparison after a run began (a withdrawn case stays in the report with its result), and never turns a failed test into a known limit for the run in which it failed. The JSON twin carries the same amendments in its amendments array, in the same order.

## 12. Decisions still open

The items below could not be settled from the sources and are not guessed.

- **OD-1.** Owner confirmation of the known-limit declarations. The criteria require a strict expected failure to be reclassified by the owner before the run. This document records the declarations on the coordinator's instruction; the owner confirms or changes them by amendment before the first run.
- **OD-2.** Owner confirmation of each item marked PROPOSED (PR-1 to PR-7).
- **OD-3.** TC-D13-003 (nested budget hierarchy). It is included in the subset as written. Whether OCS claims this case is an open owner decision; if the owner treats it as not claimed, OCS is reported as not claimed for it and the comparator results are shown without a comparative statement.
- **OD-4.** Who writes and reviews the expected outcomes of the Wiki-subset scenarios (PR-3). No reviewers are named here, and independence from the authors cannot be established from inside the repository.
- **OD-5.** Known limits and skips of Category 1 suites are not declared here. The inventory rows C1-03, C1-05, C1-05a, C1-09 and C1-15 carry known-limit counts, and the rows C1-02 (22), C1-03 (1) and C1-05 (12) carry skips outside the declared list. Until they are declared by amendment before the run, they are unexplained under PC-2.
- **OD-6.** Limit-asserting tests in suites/wiki-derived that do not carry the suffix known_limit in their name, and every test added to that suite by work still in progress, are not declared. They are reported as ordinary passes unless an amendment declares them before the run.
- **OD-7.** The 15 attempt-identity probes in fix2-probes are not declared as known limits. Their cause is closed in ODES and their marks are to be removed after the pin round. If a mark is still present at the run, a strict unexpected pass fails the run (DR-7).
- **OD-8.** Whether the owner accepts publication while ADD-AUTH-RA is inconclusive in the controller's output. The six probes are declared known limits and reported apart (RP-3); an earlier owner decision on these six concerned the earlier validation round, and whether it carries over to this gate is not stated.
- **OD-9.** Earlier retained observations of the corner and baseline plans may exist. This document uses none of them. Whether they are cited beside the release-gate comparison or superseded by it is open.
- **OD-10.** The owner-approved delegate for reclassification (DR-3) is not named.
- **OD-11.** The inclusion table depends on applicability.json version 1.0.0 at catalog commit 1a0c72de. A change to that file before the run needs an amendment that restates the affected rows.

## Amendments (appended only)

None recorded at registration.

Form of an amendment: a heading `### Amendment N (YYYY-MM-DDTHH:MM:SSZ)` (UTC), then the text of the amendment and its reason, and the person or delegate who made it. In the JSON twin the same amendment is an object with `timestamp`, `action` (one of add_known_limit, withdraw_known_limit, confirm_proposed, other), `id` (for the first two), `text`, `reason` and `by`.

### Amendment 1 (2026-10-19T11:18:16Z)

- **Action.** other
- **Text.** Delegate for declarations (settles OD-10). The coordinator is the owner-approved delegate under DR-3 for known-limit declarations and for reclassifications recorded before a run. Any reclassification made after a result has been seen is made by the owner only, and is reported as such with the run it follows.
- **Reason.** OD-10 named no delegate; the declarations below need one. Recorded before any run.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 2 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g1_integrity_and_export.py::test_wiki_d12_018_each_item_names_its_time_when_it_has_one_and_eleven_applied_run_items_have_none_known_limit`
- **Text.** Suite W-X, case `TC-D12-018`. Known limit: Not every item of the exported records carries a time; an item without one is ordered by its sequence number only, and the clocks of the journal and of the executor are independent, so no order between them is stated.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 3 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g1_integrity_and_export.py::test_wiki_d12_018_no_custody_log_handler_identity_or_access_log_is_carried_known_limit`
- **Text.** Suite W-X, case `TC-D12-018`. Known limit: The package names one fixed exporter label as its maker and carries no custody log, no handler identity and no access log.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 4 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g1_integrity_and_export.py::test_wiki_l17_021_the_artifacts_offer_no_hold_retention_or_access_log_known_limit`
- **Text.** Suite W-X, case `TC-L17-021`. Known limit: The artifacts are plain files with no legal hold, retention rule or access log, and nothing prevents deletion of a copy; an altered copy is detected by verification.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 5 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g1_integrity_and_export.py::test_wiki_l17_004_removing_every_event_of_one_whole_check_is_read_as_given_by_the_consumers_known_limit`
- **Text.** Suite W-X, case `TC-L17-004`. Known limit: The consumers do not cross-check the check events against the decision and check lists, so completeness of a record is shown only by a digest held outside it.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 6 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g1_integrity_and_export.py::test_wiki_l17_004_rows_after_the_latest_digest_and_the_witness_holder_are_outside_the_check_known_limit`
- **Text.** Suite W-X, case `TC-L17-004`. Known limit: A row added after the latest witness digest is reported as not witnessed, and the check covers what the witness covers; the party that holds the witness is outside the check.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 7 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g1_integrity_and_export.py::test_wiki_l02_025_a_backdated_revision_row_is_accepted_and_kept_in_append_order_known_limit`
- **Text.** Suite W-X, case `TC-L02-025`. Known limit: Revision rows are kept in append order and their stated times are not verified against that order.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 8 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g1_integrity_and_export.py::test_wiki_l02_025_an_edit_to_the_source_journal_before_export_is_read_as_given_known_limit`
- **Text.** Suite W-X, case `TC-L02-025`. Known limit: A source journal edited before it is exported is read as given; integrity is that of the export from the moment it exists.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 9 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g1_integrity_and_export.py::test_wiki_l03_022_a_redacted_derivative_is_refused_by_the_pack_and_package_exporters_known_limit`
- **Text.** Suite W-X, case `TC-L03-022`. Known limit: A redacted derivative of a bundle is refused by the pack and package exporters, so no redacted pack or package is offered.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 10 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g2_pack_on_demand_and_decision_state.py::test_wiki_l02_016_no_framework_or_period_input_and_no_redaction_known_limit`
- **Text.** Suite W-X, case `TC-L02-016`. Known limit: The pack takes no compliance framework or reporting period as input and does not redact; a period is the caller's selection of retained runs, one pack per run.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 11 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g2_pack_on_demand_and_decision_state.py::test_wiki_d12_004_model_prompt_guardrail_retrieval_and_feature_flag_are_not_recorded_known_limit`
- **Text.** Suite W-X, case `TC-D12-004`. Known limit: The model, prompt, guardrail, retrieval source and feature-flag state of an agent are not recorded; the record states that the machine role has no model identifier or version.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 12 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g3_traces_attribution_and_event_fields.py::test_wiki_l06_028_the_payload_is_not_masked_in_the_logs_and_redaction_does_not_reach_the_metadata_copy_known_limit`
- **Text.** Suite W-X, case `TC-L06-028`. Known limit: Payload values are carried as recorded and are not masked in the logs; the redaction options of the bundle do not reach its metadata copy, and the pack and package exporters refuse redacted derivatives.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 13 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g3_traces_attribution_and_event_fields.py::test_wiki_l09_025_a_held_decision_has_no_binding_so_its_attribution_comes_from_the_proposal_known_limit`
- **Text.** Suite W-X, case `TC-L09-025`. Known limit: A held decision names the identity it resolved but carries no principal, tool, resource or grant revision of its own; attribution of a held request comes from its proposal.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 14 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g3_traces_attribution_and_event_fields.py::test_wiki_l17_002_the_required_field_list_is_mapped_ten_of_fourteen_carried_and_four_not_carried_known_limit`
- **Text.** Suite W-X, case `TC-L17-002`. Known limit: Of the fourteen fields the case lists, ten are carried by the records; tenant, device, model and severity are not carried.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 15 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g3_traces_attribution_and_event_fields.py::test_wiki_l17_002_the_schema_is_documented_with_versions_and_sensitive_values_are_not_masked_known_limit`
- **Text.** Suite W-X, case `TC-L17-002`. Known limit: The record schema is documented with versions; sensitive values such as the payload are written as recorded and are not masked.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 16 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g4_tool_call_and_approval_controls.py::test_wiki_l06_014_payload_values_and_zero_amount_are_not_policy_checked_known_limit`
- **Text.** Suite W-X, case `TC-L06-014`. Known limit: The payload policy checks member names; the type and size of a value, its consistency with the target and a lower bound on the amount are not part of the policy.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 17 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g4_tool_call_and_approval_controls.py::test_wiki_l06_015_every_outcome_is_retained_with_the_approval_state_read_and_no_rejection_record_exists_known_limit`
- **Text.** Suite W-X, case `TC-L06-015`. Known limit: An approval has the states active, revoked and unknown; a refusal by the approver and a request nobody answered are not told apart by a rejection record.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 18 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g4_tool_call_and_approval_controls.py::test_wiki_l05_013_there_is_no_configurable_fail_open_mode_known_limit`
- **Text.** Suite W-X, case `TC-L05-013`. Known limit: The stack has a fail-closed branch only; there is no configurable fail-open mode.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 19 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g5_exchange_messages_and_correlation.py::test_wiki_l06_018_a_forged_message_claiming_a_registered_agent_is_accepted_when_consistent_known_limit`
- **Text.** Suite W-I, case `TC-L06-018`. Known limit: Sender authentication by signature or mutual authentication is not part of the exchange route; the message digest binds content, not origin, and a message consistent with its digest is read as given.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 20 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g5_exchange_messages_and_correlation.py::test_wiki_l06_018_refusals_before_acceptance_are_returned_and_not_stored_known_limit`
- **Text.** Suite W-I, case `TC-L06-018`. Known limit: A refusal before acceptance is returned to the caller and is not durably stored.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 21 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g5_exchange_messages_and_correlation.py::test_wiki_l06_040_the_schema_check_does_not_reject_extra_members_content_types_or_size_known_limit`
- **Text.** Suite W-I, case `TC-L06-040`. Known limit: The schema check of the exchange route does not reject extra members, content types or message size; such messages are accepted as data.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 22 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g5_exchange_messages_and_correlation.py::test_wiki_l06_040_every_rejection_carries_a_typed_reason_code_and_none_is_stored_known_limit`
- **Text.** Suite W-I, case `TC-L06-040`. Known limit: Every rejection carries a typed reason code and no rejection is durably stored.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 23 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g5_exchange_messages_and_correlation.py::test_wiki_l06_039_the_sender_label_is_not_bound_to_the_actor_so_a_listed_low_trust_sender_has_the_rights_of_the_named_actor_known_limit`
- **Text.** Suite W-X, case `TC-L06-039`. Known limit: The sender label is checked against a list of trusted senders and is not bound to the actor named in the request; the request is judged on the rights of the named actor.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 24 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g5_exchange_messages_and_correlation.py::test_wiki_l06_039_a_held_request_is_retained_with_the_proposal_of_the_actor_and_the_user_and_not_the_sender_known_limit`
- **Text.** Suite W-X, case `TC-L06-039`. Known limit: A held request is retained with the proposal of the actor and the user and not with the sender.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 25 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g5_exchange_messages_and_correlation.py::test_wiki_l06_045_the_hop_names_the_actor_the_user_the_payload_commitment_and_the_decision_but_not_the_caller_and_callee_known_limit`
- **Text.** Suite W-X, case `TC-L06-045`. Known limit: The retained hop names the actor, the user, the payload commitment and the decision, and does not name a caller agent and a callee agent.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 26 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g5_exchange_messages_and_correlation.py::test_wiki_l06_045_the_correlation_identifier_is_not_a_member_of_the_message_known_limit`
- **Text.** Suite W-X, case `TC-L06-045`. Known limit: The correlation identifier is not a member of the message; a search by conversation identifier finds the message, the workflow row and the successor packet, and no decision, effect or bundle record.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 27 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g6_partly_covered_fragments.py::test_wiki_l06_003_the_registry_is_a_set_of_names_and_not_an_inventory_known_limit`
- **Text.** Suite W-X, case `TC-L06-003`. Known limit: The registry that refuses undeclared parties is a set of names; it records no discovery, no state of an agent and no history of a refusal.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 28 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `suites/wiki-derived/test_wp_g6_partly_covered_fragments.py::test_wiki_l06_026_the_confinement_covers_the_database_path_only_known_limit`
- **Text.** Suite W-I, case `TC-L06-026`. Known limit: The confinement check covers the destination database path only; file reads and network destinations of an agent are not restricted, and the host configures the root.
- **Reason.** Recorded before the controller run so that the assertion of this limit is reported in the PASSING-AS-KNOWN-LIMIT column and never as an ordinary pass (DR-1, DR-8, OD-6). The test asserts the stated limit as the negative fact and is not changed to produce a pass (DR-4). No result of the controller or of any release-gate run had been seen when this was recorded.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 29 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `cogno-us/open-decision-evidence-standard:tests/test_restriction_semantics.py::test_control_legacy_export_is_digest_identical_to_the_retained_example`
- **Text.** Suite C1-01 (open-decision-evidence-standard, pinned revision of the release candidate). Known limit, declared as a test that ends in failure: with the Replay bundle installed at the accepted revision, Replay does not import the retained producer-v2 examples `lost_ack` and `prior_absence` that this test uses, with the reason that an unknown result cannot carry a validated applied or partial observation. The retained examples, the export path and the test are unchanged. Without the accepted Replay revision the test is skipped, with the reason listed in inventory row C1-01.
- **Reason.** The four failures were seen while moving the Programme 2 tuple (ODES decision 41) and are not caused by it; they are skipped in the component's own CI, where Replay is not installed. This is a test that ends in failure and not a strict expected failure, so it is reported in its own list of declared known limits that end in failure, apart from the passes and apart from the strict expected failures, and never as a pass (PC-3, PC-4). Whether the retained examples or the export path should change is left to a later planned change and is not made before the run. Recorded before the controller run; no result of it had been seen.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 30 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `cogno-us/open-decision-evidence-standard:tests/test_restriction_semantics.py::test_explicit_export_end_to_end`
- **Text.** Suite C1-01 (open-decision-evidence-standard, pinned revision of the release candidate). Known limit, declared as a test that ends in failure: with the Replay bundle installed at the accepted revision, Replay does not import the retained producer-v2 examples `lost_ack` and `prior_absence` that this test uses, with the reason that an unknown result cannot carry a validated applied or partial observation. The retained examples, the export path and the test are unchanged. Without the accepted Replay revision the test is skipped, with the reason listed in inventory row C1-01.
- **Reason.** The four failures were seen while moving the Programme 2 tuple (ODES decision 41) and are not caused by it; they are skipped in the component's own CI, where Replay is not installed. This is a test that ends in failure and not a strict expected failure, so it is reported in its own list of declared known limits that end in failure, apart from the passes and apart from the strict expected failures, and never as a pass (PC-3, PC-4). Whether the retained examples or the export path should change is left to a later planned change and is not made before the run. Recorded before the controller run; no result of it had been seen.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 31 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `cogno-us/open-decision-evidence-standard:tests/test_result_classification.py::test_control_producer_v2_examples_pass_the_semantic_layer[lost_ack.package.json]`
- **Text.** Suite C1-01 (open-decision-evidence-standard, pinned revision of the release candidate). Known limit, declared as a test that ends in failure: with the Replay bundle installed at the accepted revision, Replay does not import the retained producer-v2 examples `lost_ack` and `prior_absence` that this test uses, with the reason that an unknown result cannot carry a validated applied or partial observation. The retained examples, the export path and the test are unchanged. Without the accepted Replay revision the test is skipped, with the reason listed in inventory row C1-01.
- **Reason.** The four failures were seen while moving the Programme 2 tuple (ODES decision 41) and are not caused by it; they are skipped in the component's own CI, where Replay is not installed. This is a test that ends in failure and not a strict expected failure, so it is reported in its own list of declared known limits that end in failure, apart from the passes and apart from the strict expected failures, and never as a pass (PC-3, PC-4). Whether the retained examples or the export path should change is left to a later planned change and is not made before the run. Recorded before the controller run; no result of it had been seen.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 32 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `cogno-us/open-decision-evidence-standard:tests/test_result_classification.py::test_control_producer_v2_examples_pass_the_semantic_layer[prior_absence.package.json]`
- **Text.** Suite C1-01 (open-decision-evidence-standard, pinned revision of the release candidate). Known limit, declared as a test that ends in failure: with the Replay bundle installed at the accepted revision, Replay does not import the retained producer-v2 examples `lost_ack` and `prior_absence` that this test uses, with the reason that an unknown result cannot carry a validated applied or partial observation. The retained examples, the export path and the test are unchanged. Without the accepted Replay revision the test is skipped, with the reason listed in inventory row C1-01.
- **Reason.** The four failures were seen while moving the Programme 2 tuple (ODES decision 41) and are not caused by it; they are skipped in the component's own CI, where Replay is not installed. This is a test that ends in failure and not a strict expected failure, so it is reported in its own list of declared known limits that end in failure, apart from the passes and apart from the strict expected failures, and never as a pass (PC-3, PC-4). Whether the retained examples or the export path should change is left to a later planned change and is not made before the run. Recorded before the controller run; no result of it had been seen.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 33 (2026-10-19T11:18:16Z)

- **Action.** add_known_limit
- **Id.** `ADD-AUTH-RA`
- **Text.** Requirement ADD-AUTH-RA (selector: component `probes-control-plane`, pattern `probe_addauthra_`). Known limit: if the controller computes this requirement as inconclusive because its six declared probes are strict expected failures (a strict expected failure is recorded as skipped in the JUnit report), the requirement is listed as a known limit, reported in its own block (RP-3) next to the six declared probes. The status the controller computes is reported unchanged and is never reported as a pass. This declaration does not cover any other status of the requirement: a failure, an error or an unexpected pass of one of the probes is reported as computed and DR-7 applies.
- **Reason.** Settles OD-8 as the owner decided on 19 October 2026: when ADD-AUTH-RA is inconclusive at the gate it is listed as a known limit. Declared before the run, for one named requirement selector (DR-8), and not reclassified after any result (DR-2, DR-3).
- **By.** the owner's decision of 19 October 2026, recorded by the coordinator

### Amendment 34 (2026-10-19T11:18:16Z)

- **Action.** other
- **Text.** Reclassification of `TC-L06-040` from APPLICABLE to PARTLY_COVERED (suite W-I). Claimed and tested (counts): messages whose identity, recipient, time, message-type or reference members are missing, of the wrong type or not trusted are refused with a typed reason code before any handler runs. Not claimed (not scored): validation of extra members, of free-text or list content and of message size, and detection of an instruction embedded in free text; the stack makes no content-detection claim, and a message cannot authorize an effect by itself. Basis: The case expects at least 11 of 12 invalid messages rejected, and its invalid set is 4 messages with extra fields, 3 with wrong types, 3 oversized and 2 with an embedded instruction. Extra members, size and free-text content are outside the declared checks of the exchange route, so at most the 3 wrong-type messages are within what the stack claims; the expected detection cannot be met in full by design.
- **Reason.** Decided from the text of the case and from the declared design of the stack, as recorded in the decision register of 19 October 2026, before any result of the controller or of any release-gate run was seen; no result was used (PC-4, DR-3, DR-5). The case stays in scope and in the denominator for its claimed part; it is not moved to NOT_APPLICABLE. The tests that assert the not-claimed parts as limits are declared as known limits in this record and are not changed. The case stays in the comparator table with its inclusion unchanged (R1 and R2 were judged from the case text); only the class column of its row is restated here (OD-11). applicability.json is not edited by this amendment.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 35 (2026-10-19T11:18:16Z)

- **Action.** other
- **Text.** Reclassification of `TC-L06-039` from APPLICABLE to PARTLY_COVERED (suite W-X). Claimed and tested (counts): requests are judged on the rights of the named actor and the originating user through the trusted resolver, and in-scope and out-of-scope requests are allowed and refused or held accordingly; an unlisted sender is refused. Not claimed (not scored): binding of the sender label to the calling agent, and a denial record that names both agent identities. Basis: Procedure step 5 asks that each decision uses the rights of the caller and step 6 that each denial is logged with both agent identities. The exchange route checks a sender label against a trusted-sender list and does not bind it to the actor, and refusals on that route are returned and not durably stored, so neither expectation is part of the declared design; the scope note of the case already limits it to a subset with fixture identities.
- **Reason.** Decided from the text of the case and from the declared design of the stack, as recorded in the decision register of 19 October 2026, before any result of the controller or of any release-gate run was seen; no result was used (PC-4, DR-3, DR-5). The case stays in scope and in the denominator for its claimed part; it is not moved to NOT_APPLICABLE. The tests that assert the not-claimed parts as limits are declared as known limits in this record and are not changed. The case stays in the comparator table with its inclusion unchanged (R1 and R2 were judged from the case text); only the class column of its row is restated here (OD-11). applicability.json is not edited by this amendment.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 36 (2026-10-19T11:18:16Z)

- **Action.** other
- **Text.** Reclassification of `TC-L06-018` from APPLICABLE to PARTLY_COVERED (suite W-I). Claimed and tested (counts): a modified message (digest mismatch) is refused, and a replayed or redelivered message does not produce a second effect. Not claimed (not scored): authentication of the sending agent by signature or mutual authentication, and a durable record of refusals. Basis: The case expects forged messages rejected or flagged and asks whether message signing or mutual authentication is available (procedure step 6). The exchange route defines neither: its message digest binds content, not origin, as the guarantees and limits page states. The forged-message expectation cannot be met in full by design.
- **Reason.** Decided from the text of the case and from the declared design of the stack, as recorded in the decision register of 19 October 2026, before any result of the controller or of any release-gate run was seen; no result was used (PC-4, DR-3, DR-5). The case stays in scope and in the denominator for its claimed part; it is not moved to NOT_APPLICABLE. The tests that assert the not-claimed parts as limits are declared as known limits in this record and are not changed. The case stays in the comparator table with its inclusion unchanged (R1 and R2 were judged from the case text); only the class column of its row is restated here (OD-11). applicability.json is not edited by this amendment.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 37 (2026-10-19T11:18:16Z)

- **Action.** other
- **Text.** Reclassification of `TC-L17-002` from APPLICABLE to PARTLY_COVERED (suite W-X). Claimed and tested (counts): presence, naming and time format of the fields that the record contracts define (the ODES package and the control-plane journal), and a documented schema with versions. Not claimed (not scored): the case's full required-field list (tenant, device, model and severity are not fields of these records), masking of sensitive values, and events from SIEM or third-party sources. Basis: The case lists fourteen required fields and expects at least 95 percent present and sensitive values masked. The record contracts define ten of the fourteen and write values as recorded, so the expected detection cannot be met in full by design; the scope note of the case already limits it to the ODES and journal schema.
- **Reason.** Decided from the text of the case and from the declared design of the stack, as recorded in the decision register of 19 October 2026, before any result of the controller or of any release-gate run was seen; no result was used (PC-4, DR-3, DR-5). The case stays in scope and in the denominator for its claimed part; it is not moved to NOT_APPLICABLE. The tests that assert the not-claimed parts as limits are declared as known limits in this record and are not changed. The case stays in the comparator table with its inclusion unchanged (R1 and R2 were judged from the case text); only the class column of its row is restated here (OD-11). applicability.json is not edited by this amendment.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 38 (2026-10-19T11:18:16Z)

- **Action.** other
- **Text.** Confirmation of the known-limit declarations (OD-1). The declarations of section 8 and the declarations appended above are confirmed by the coordinator as owner-approved delegate. The owner's review remains open as a record item and does not gate the run.
- **Reason.** OD-1 asked for confirmation before the first run; the register records the coordinator's decision as taken under the owner's delegation, for review at the end.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 39 (2026-10-19T11:18:16Z)

- **Action.** other
- **Text.** TC-D13-003 (nested budget hierarchy) is not claimed by OCS (OD-3). It stays in the comparator subset as written; OCS is reported as not claimed for it, the per-budget cap and sibling-independence tests stay as ordinary tests, and the comparator results for it are shown without a comparative statement.
- **Reason.** The owner decided on 18 October 2026 that this case is not claimed; the parent-budget design is a later-release item.
- **By.** the owner's decision of 18 October 2026, recorded by the coordinator

### Amendment 40 (2026-10-19T11:18:16Z)

- **Action.** other
- **Text.** Limit-asserting tests in suites/wiki-derived (OD-6). The known-limit tests named in section 8.3 and in the declarations appended above are declared. No other test in the suite is declared: a test that states a limit in a comment inside otherwise ordinary assertions is an ordinary test, and its failure blocks publication.
- **Reason.** Section 4 (DR-8, DR-9): a declaration names one test; anything not declared is undeclared.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 41 (2026-10-19T11:18:16Z)

- **Action.** other
- **Text.** The fifteen attempt-identity probes of fix2-probes stay not declared (OD-7). Removal of their strict expected-failure marks needs no withdrawal, because they were never declared; a mark still present at the run that unexpectedly passes fails the run (DR-7).
- **Reason.** Confirms OD-7 as registered; it is recorded here so that the removal of the marks after the pin round is not read as a change of a declaration.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 42 (2026-10-19T11:18:16Z)

- **Action.** other
- **Text.** Earlier retained observations of the corner and baseline plans are superseded by the release-gate comparison and are not cited beside it (OD-9).
- **Reason.** OD-9 asked whether earlier observations are cited or superseded; the comparison of this gate runs under this pre-registration only.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 43 (2026-10-19T11:18:16Z)

- **Action.** other
- **Text.** applicability.json stays at version 1.0.0 at catalog commit 1a0c72de (OD-11). The class of four cases (TC-L06-040, TC-L06-039, TC-L06-018, TC-L17-002) is restated by the reclassification amendments of this record; the effective class for the gate is the class of the file with those amendments applied.
- **Reason.** OD-11 requires an amendment that restates affected rows before the file is changed; the file is not changed here.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 44 (2026-10-19T12:18:05Z)

- **Action.** withdraw_known_limit
- **Id.** `test_verifier_probes.py::test_probe_a_binding_member_changed_alone_is_refused_against_the_captured_inputs[journal-applied-requirement_id]`
- **Text.** Withdrawal of the declaration for the verifier probe on the member `requirement_id`. The verifier now compares `binding.requirement_id` with the input id of every successful conflict read, so the limit as declared (checked against the proposal export and the destination ledger only) no longer describes the component. The strict expected-failure mark and the row in suites/fix2-probes/KNOWN_LIMITS.md are removed in the same change as this amendment; from the next run the probe is an ordinary test. The declaration for `effective_max_effects` is unchanged.
- **Reason.** The verifier change is merged (verifier #32). The declaration of 8.1 anticipated this case (a follow-up on captured-input binding was open). The withdrawal is recorded before the mark is removed (DR-3, DR-7) and before the run; the probe is not changed.
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)

### Amendment 45 (2026-10-19T12:18:05Z)

- **Action.** other
- **Text.** The strict expected-failure marks of the fifteen attempt-identity probes (listed as not declared in 8.1) are removed once the pin round moves the ODES pin to the revision that refuses a result naming no registered attempt. They were never declared, so no withdrawal applies; from the next run the fifteen are ordinary tests.
- **Reason.** ODES #127 is merged. Recorded so that the removal is visible in the record before the run (OD-7).
- **By.** the coordinator, owner-approved delegate for declarations (decision OD-10)
