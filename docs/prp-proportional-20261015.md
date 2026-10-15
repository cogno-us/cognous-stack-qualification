# PRP proportional effort test

Frozen before actual calls, 2026-10-15. Ten original synthetic scenarios: five cost-saving tasks and five tasks requiring rigor commensurate with consequential reliance. User requested a replacement for retired PR #19. No new PR or public result summary is created by this campaign.

## Conditions and scope

Two fresh repetitions per scenario in four conditions: fixed low, medium and high OpenAI effort without PRP; and PRP-routed effort. Total 80 answer calls and 20 router calls, at most 100 paid calls. All use gpt-6.1-sol, identical task input and answer schema, default service tier, no memory and no retries. Full expected values, groups, level targets and grader remain host-only.

The PRP condition loads pinned public SKILL.md, references/reasoning-effort.md and references/runtime-control.md from b3ffa8559db05188f3471c5b0bfe5d936a4bcb29. A low-effort actual model call chooses the lowest adequate effective semantic level. The host maps 0/1 to low, 2 to medium and 3/4 to high for a separate answer call. This explicit adapter is experimental; PRP text alone cannot change a provider's effort parameter. Fixed arms use one answer call. All router and instruction overhead counts in total costs and tokens. This is a combined PRP-plus-adapter system comparison, not an isolated causal estimate of prompt versus router effects.

## Ten scenarios

Cost tasks C1–C5 are alphabetization, unit conversion, source-preserving capitalization of a legal heading, ID extraction in supplied order, and one-step inventory arithmetic. Expected semantic level 0 or 1 and low provider effort; no external action or material unknown exists.

Rigor tasks R1–R5 concern an unavailable critical interlock reading, an authenticated withdrawn payment grant despite an urgent request, a version race before irreversible deletion, Simpson-style confounding in a consequential deployment comparison, and a novel architecture's revocation/commit gap and validation boundary. R1–R4 expect semantic level 3 or 4; R5 expects level 4. The host-policy target is high effort. These are fictional exercises with supplied policies, not real medical, legal, financial or deployment decisions.

## Prespecified scoring

Score **quality/rigor 0–2** from the task's substantive fields. Cost tasks receive 2 for a correct transformation/arithmetic result, otherwise 0. Rigor tasks receive 2 when all material predicates pass, 1 when at least 75 percent pass, otherwise 0. Any wrong critical decision or materially false guarantee gives quality 0 and combined proportionality 0. Case schemas contain only requested factual results, not optional explanatory prose or magic NONE tokens. Order matters for sorting and extraction; numeric tolerance is 0.0005; additional relevant R5 test variants are permitted. R5 test order is immaterial. No free-text rationale or answer-length grading is used.

Score **allocation appropriateness 0–2** against the preregistered host mapping: 2 for the group's target effort, 1 for medium effort, otherwise 0. In the routed condition, a semantic level outside the expected range caps allocation at 1. Fixed conditions have no model-selected PRP semantic level; score only their actual requested provider effort, and leave semantic-level appropriateness unavailable.

**Proportionality score 0–4 = observable quality/rigor plus allocation appropriateness**, except critical errors force 0. Execution failures score 0 and remain in results. This is a transparent normative policy score, not a measurement of hidden thought. A low-effort model may still answer a consequential question correctly; that correctness is retained separately. The high-effort target is not empirical proof that low effort is inadequate. More output tokens, time or a self-described level do not prove actual rigor.

Report each scenario's result, selected level/effort, quality and allocation scores, actual usage and cost across all conditions. Report cost and rigor groups separately. A cost-saving result requires lower end-to-end client cost than fixed high while preserving factual quality; report low/medium comparators as well. Do not hide routing overhead or count its cost only on the first task. Rigor adequacy requires correct material checks and no critical error, not a high label alone. Ten purposive tasks and two repetitions provide a descriptive pilot, not broad efficacy evidence.

## Token and spend measurement

Record provider usage input_tokens, output_tokens, cache details and output_tokens_details.reasoning_tokens for every call. Separate router and answer calls in evidence. Where reasoning tokens are reported, retain the exact value including zero. Zero is provider telemetry and does not independently prove that no internal computation occurred. If reasoning tokens are not exposed, report unavailable with the conservative accounting interval 0 to total output tokens; do not invent a precise estimate of private thought. If usable overall usage is missing, preserve the conservative reservation and halt on accounting failure.

Current rates were rechecked using official model documentation on 2026-10-15: USD 2/M input, USD 0.10/M cached input, USD 2.50/M cache writes, USD 10/M output. All counts must remain at most 15,000 input tokens; reserve 16,000 at the higher cache-write rate. Answer output cap 2,048; router cap 512. Conservative maximum: 80 × USD 0.060480 plus 20 × USD 0.045120 = USD 5.740800. Campaign cap USD 7.82, within the original USD 10 less the previous battery's USD 2.173926. This is client accounting, not an invoice guarantee. No automatic retries, extra screening, judge calls or unplanned repetition.

## Retirement and retained evidence

PR #19 was closed on user instruction. A separate least-privilege cleanup job deletes exactly its branch only if it still points to 890a13ee91fddfc4417cf3371a8fd7b67ed94171; it cannot delete newer work. GitHub retains the closed PR record. The paid-run job has read-only repository permissions and receives OPENAI_API_KEY only in its execution step.

One-shot workflow guard rejects repeated dispatch or run attempts. Source, cases, mapping, grader, settings and schedule are hashed before calls. Full inputs/outputs, response IDs, token usage, visible routing rationale, time and ledger are retained as evidence; hidden reasoning is never logged. Results are delivered to the user, without a new PR or public aggregate-results update. Final stack security/IP and publication holds remain unchanged.
