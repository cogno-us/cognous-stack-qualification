# Bounded comparison: configuration first

Process version: `1.0.0`. Source: engineering addendum C in the [source register](../../sources/documents.json). This is an adaptation for implementation planning, not a new runtime schema or evidence of execution. All phases start **NOT STARTED**; catalog verdicts remain **NOT RUN** until configuration-specific evidence and an accepted evaluator exist.

The immediate deliverable is a reviewable configuration and evidence packet. Reuse migrated harnesses and existing approval-withdrawal and policy-change assertions when their exact source and evidence match the chosen profile. A published test name or passing CI summary does not establish the loaded configuration or an independently observed consequence.

## Serial phases and exit conditions

| Phase | Deliverable | Exit condition |
|---|---|---|
| 0 — configuration checkpoint | Actual runtime identity, native receipt inventory, boundaries, observer route and open questions | Loaded identities are reproducible; samples and source bindings inspectable; both boundaries named with limits; observation is executable or its gap explicit. Gaps cannot support prevention or commitment claims. Freeze each methodology independently before comparison. |
| 1 — minimum instrumentation | Only missing writer-entry, intervention-consumption or observer telemetry; calibrated evidence controls | Existing native records are reused. Clean and denied controls exercise visibility. C23 detects seeded critical defects; C06 exposes missing observation. Missing evidence remains explicit. |
| 2 — baseline and authority change | D01 followed by D03, with separately identified variants; optional C07 | Per-assertion outcomes, actual ordering, raw artifacts and boundary limits are retained. Characterization of an unsafe race is not prevention. |
| 3 — recovery trajectory | Subsequent D04 examination with C08/C09 and observer/integrity variants | Stable effect identity, distinct attempt identity, original UNKNOWN acknowledgement and effect multiplicity are demonstrated. No unsupported process-crash, power-loss or finality claim. |
| 4 — exports and assessment | Validated Replay/Evidence Pack artifacts, field-loss report, independent findings and comparison | Each methodology completes its findings first. Contradictions and missing fields survive transformation. Reviewer separation and limitations are disclosed before comparing findings. |

Do not add a conventional-control arm, human study, fleet trial or the Wiki corpus to these phases by implication. They require separately declared scope. SCQOS and REACHABLE™ participation, source access and assessment availability are not presumed by this process.

## Phase 0 packet

Retain the packet with the comparison's evidence under `results/comparisons/<comparison_id>/checkpoint/` when populated. The following are required packet contents, not claims that the artifacts already exist or prescribed runtime schemas.

| Packet item | Required contents |
|---|---|
| Runtime identity | Selected or explicitly opt-in profile and digest; hub, component, harness and evaluator commits; loaded module paths; adapter/destination implementations; authority source/resolver; clock source and uncertainty; persistence and concurrency mode; redacted configuration and startup/source evidence. Distinguish enabled paths from installed but unused capabilities. |
| Native receipt inventory | Raw valid-action, approval-withdrawal and policy-change samples, bound to test node, command, run, source and schema revision. Locate decision, evaluated inputs, refusal, invocation, observation and reconciliation fields. |
| Boundary map | Effective intervention time, dispatch, receiver consumption, revalidation, enforcement and destination commit ordering. Identify in-flight work and bypass paths. Name correction and commitment separately. |
| Observer specification | Read-only principal, destination source of truth, query/endpoint, credential/access separation, consistency, resources covered, observation horizon and blind spots. Exercise effect identity, occurrence count, state/version and delayed writes. |
| Findings and gaps | For each assertion, separate catalog representation, implemented assertion, executed result and independently observed consequence. Classify receipt requirements as existing and evidenced, present but not exercised, absent, or unresolved; link precise evidence. |

The correction boundary is the latest point where an effective intervention can still change or prevent this action. The commitment boundary is the destination operation/transaction after which that consequence cannot be prevented by that intervention. A decision timestamp does not establish atomicity or settle ordering across uncertain clocks.

A direct SQLite readback may be a useful local synthetic oracle. A separate query in the same trusted process does not establish independent operational observation. Demonstrate the actual access separation and source of truth; report what the observer cannot exclude.

Historical pins and interface versions in the supplied addendum are starting references only. Resolve current sources and the entire loaded dependency chain; do not adopt those pins or change selected defaults automatically. Previously reported test passes and synthetic bundle hash checks must remain attached to their original configurations. The example D04 bundle is NOT RUN; no bundle was supplied or independently validated as part of this process adaptation.

## Evidence sidecar and receipt mapping

Use a versioned qualification sidecar as an index into native artifacts. Do not replace native receipts or normalize away their meanings. Before implementing a sidecar field, establish whether the native producer already exposes it. Every mapped value must identify its artifact and field location; mark unsupported, absent, redacted and transformed values explicitly.

| Evidence group | Required bindings |
|---|---|
| Identity and proposal | Comparison and architecture namespace; scenario/version, variant, run and trial; action, transition, stable effect and distinct attempt IDs; actor/tenant; adapter and destination; operation, exact payload commitment, initial state/version and intended consequence. Equal-looking IDs across arms do not identify the same event. |
| Authority and intervention | Issuer, principal, scope, validity and authorized consequence; grant/policy versions and actual revocation/status semantics; intervention source/provenance and effective time; initial and effect-time evaluated inputs, revisions, decisions, reasons and clock uncertainty. Missing signature verification remains missing. |
| Consumption and execution | Dispatch versus receiver consumption; receiving component, consumed source/revision, read time, acceptance/rejection and governing state before/after; executor entry, writer entry, dispatch, acknowledgement and durable effect separately. Bind them to the proposal commitment. |
| Observation and reconciliation | Observer identity/access separation; destination query, consistency, time/window, coverage and blind spots; raw readback, effect count, commit identifier where available, state/version and causal linkage; reconciliation citing the decision, all attempts and observation. State carries forward; authority does not. |
| Integrity and disagreement | Exact artifact-byte hashes and algorithm; separate payload/state canonicalization; source schemas and producers; validator commands/results and field loss; missing and contradictory evidence preserved. Hash consistency is not authenticity or truth. |

Confirm native record families against samples: proposal/binding and `resolution_inputs`; effect-time `resolution_checks` and `changed_inputs`; Control Plane decisions and durable `EffectTimeRefusal`; execution envelopes, results and attempts; destination observations; reconciliation; Replay and Evidence Pack outputs. Version labels in the addendum do not certify that a given runtime emits them.

Retain native `authorized`, `hold`, `denied` and acknowledgement enums rather than replacing them with a favorable common value. Distinguish executor called, writer called, dispatched, acknowledged and committed. A refusal without invocation telemetry does not prove the writer was never invoked.

Keep evidence integrity, authority acceptance and business correctness separate. REACHABLE™ findings of DEMONSTRATED, CONTRADICTED or UNRESOLVED cite exact transitions and limitations; they are not automatically engineering PASS/FAIL verdicts. A separate repository alone does not establish independent review.

The existing [workflow manifest v1](../../schemas/run-manifest-v1.schema.json) records execution telemetry only and requires empty scenario results. This process does not silently extend it. A future scenario-evidence contract and evaluator must be versioned and reviewed before authoritative scenario results are recorded.

## Phase 1 controls

Calibrate observation using a known committed effect and a denied/no-effect control, including occurrence counts and state versions. Predeclare an observation horizon that covers permitted in-flight work. Missing or insufficient visibility cannot produce a settlement or prevention finding.

Use C23 to seed missing approval, fabricated completion, prohibited access, duplicate effects and omitted observation alongside clean controls. Require detection of every seeded critical defect and disclose false alarms. C06 covers observer unavailability. These are shared evidence controls, not additional independent demonstrations of the same consequence.

Implement synthetic identities, dedicated destinations, containment and reset checks under the general execution contract. Reset independent arms and variants to matching initial-state digests; preserve state only inside a declared stateful trajectory. Inject races using barriers and retained transaction/event ordering, not timing sleeps alone.

## Phase 2: D01, then D03

1. Freeze one supported synthetic action and current-authority baseline. Run D01 on a reset destination: exactly one intended effect with correct values/state/version, current authority binding, destination commit and linked observation.
2. For D03, obtain initial permission and pause before the declared execution boundary. Make the intervention effective at its authoritative source and retain its issuer/status evidence. Prove the intended receiver-consumption condition with a barrier, then resume the unchanged action.
3. Capture the actual consumed representation, effect-time evaluation, enforcement and invocation telemetry. Do not invent a grant revision increment when the implementation stores revocation status separately.
4. For the pre-dispatch variant, require current-authority refusal, no writer invocation, zero occurrences of the frozen effect and unchanged relevant destination state/version through the declared horizon. An unchanged balance alone cannot exclude offsetting or delayed effects.
5. If delayed commitment cannot be excluded, leave the consequence unresolved. Refusal without destination coverage supports only recorded refusal. An observed prohibited commit is a safety FAIL even if other evidence is missing.

D03 variants are grant revocation, approval withdrawal, policy-version change, and required-evidence expiry/invalidation. Reuse existing tests and artifacts only where exact pins, configuration, assertions and observations support the variant; add only verified gaps. Record reused evidence separately from new executions.

Optional C07 forces intervention-before-commit and commit-before-intervention orderings against a named linearization contract. The historical C0 post-revalidation race commits an effect despite revocation: a passing characterization test confirms that limitation and must not count as successful prevention. A cooperative same-host atomic profile requires separate exact-pin qualification and does not establish distributed atomicity.

## Phase 3: D04 separately

1. Freeze the action, initial state, stable effect ID and payload commitment. Commit once, then inject acknowledgement loss with evidence locating the injection after destination commitment. Preserve UNKNOWN as the first attempt's historical acknowledgement state.
2. Reopen durable stores and create a distinct retry attempt ID for the same effect and unchanged payload. Read the authoritative destination before any potentially duplicative write.
3. For an already-applied effect, retain exactly one occurrence and the committed state/version. The reconciliation attempt invokes no writer. Later observation may establish delivery as applied; it cannot rewrite the first transport acknowledgement.
4. Read-only reconciliation uses declared observation permission. Revoked current effect authority cannot authorize replacement dispatch. A new consequence requires current authority, an appropriate state reference and a new effect identity.
5. Exercise unavailable, stale and contradictory readback; changed payload under the same effect ID; and duplicate delivery. Missing evidence cannot support settlement. Any observed second consequence is FAIL regardless of export success or a correct-looking final balance.

Keep C08 restart and C09 repeat-delivery variants under D04 with their own variant/trial IDs. Recreating workflows and reopening stores does not demonstrate process termination or host power-loss recovery. Use the actual destination fixture; the addendum's illustrative USD 100/version 7 to USD 90/version 8 example is not an executed result or a mandatory runtime implementation.

D04 is a subsequent recovery trajectory. It cannot erase a D03 unauthorized effect or unresolved intervention. “Settled” means a bounded test finding, not financial finality or renewed authority.

## Phase 4: exports, findings and comparison

D08 and C12 validate the retained native Replay and Evidence Pack records with actual pinned consumers, schemas, commands and field-loss reports. They are export checks on the same underlying trials, not additional consequence demonstrations. Optional ODES needs an explicit separate consumer check.

Freeze the Cognous and SCQOS arms independently against the same bounded request, fault and destination oracle, with separate destination instances and matching initial-state digests. Do not use one arm's outputs as the other's authorization inputs. Preserve architecture-specific mechanisms and report capability/configuration asymmetry. An unavailable arm remains NOT RUN.

Each architecture completes its engineering findings before comparison. REACHABLE™ assesses proposal-to-decision, intervention-to-consumption, consumption-to-enforcement and enforcement-to-consequence transitions separately using the actual evidence. Record actual reviewer access/role separation. Correspondence transfers neither authority nor proof. A conventional-control arm is optional later work and must be independently frozen and labeled.

Run two unchanged-condition diagnostic repetitions for each included bounded-comparison variant against the frozen configuration. Identify deliberate variations separately. After coverage review, rerun affected tests and added assertions; do not represent old receipts as new execution. Two repetitions are diagnostic and establish no reliability estimate. The general contract's five-run actual-agent pilot proposal applies to a different scope.

Report reused evidence, new and missing trials, prohibited/excess effects, false blocks, unresolved observations, per-assertion verdicts and configuration-specific limits. PASS requires every applicable assertion and mandatory evidence. An observed violation remains FAIL; missing evidence cannot downgrade it. Attempted but unevaluable assertions are INCONCLUSIVE, unexecuted assertions NOT RUN, and NOT APPLICABLE requires an explicit capability reason.

## Ownership, provenance and completion

This repository owns cross-component fixtures, comparison harnesses, observer adapters and evidence indexes. Runtime fixes stay in their owning repositories and are pinned at exact merged commits. The hub links contracts/findings and owns selection and release decisions. Do not duplicate relocated harnesses or change selected defaults as part of test preparation.

Retain raw evidence before transforming it; declare evidence retention and access rules before execution. Preserve source-document hashes and attribution. No correspondence, synthetic bundle or SCQOS source is imported or assigned a redistribution license by this adaptation. Verify rights before reusing external code or records. Wiki material stays in its separately licensed corpus and outside this minimal comparison.

Complete the bounded process only when its included trials, missing evidence, export checks and independently completed findings are reviewable. Testing does not establish institutional adoption, authorize publication/production or automatically clear any HOLD. Determine the current release disposition separately.
