# Execution and evidence contract

This is a proposed test contract, not a new component runtime schema. Resolve actual producer interfaces and report missing mappings before implementing adapters. Use a versioned test sidecar for unsupported fields; never manufacture absent source evidence.

## Scenario preparation

Each executable variant must declare scenario ID and version, risk, capability, trust boundary, consequence, action profile, user turns, attack or fault placement, expected checkpoints, forbidden effects, final-state oracle, initial-state digest, cleanup, applicability and required evidence. The catalog is an initial specification; profile-specific fixtures, numerical thresholds and fault hooks remain to be implemented.

Start with one supported customer-service effect. Do not change selected component pins or production permissions as part of this test-only work. Optional memory, coordination, ODES or human-review cases require actual supported capabilities.

## Source and environment identity

Record hub SHA; every participating component repository and exact commit; harness and evaluator commits/versions; selected or candidate profile label and digest; fixtures and dependencies; model identifier and available provider revision; inference settings; prompt and tool-definition digests; and context/memory configuration. Record unavailable details explicitly. A seed does not guarantee reproducibility.

Run setup checks before each suite: dedicated destination, synthetic data, test identities, no production credentials or effects, and tested network/tool allow lists including attempted prohibited access. Reset database, queue, filesystem, cache, session and memory between independent trials and compare the declared initial digest. Deliberately preserve state inside a stateful sequence. Cleanup failures must be visible.

Use barriers and fault injection for race cases, not timing sleeps. Name the actual commit/linearization contract. Late cancellation does not reverse an irreversible commit. Restore tests must identify everything restored and everything remaining external; restoring an anchor with its protected database does not demonstrate rollback resistance.

D06 requires numerical CPU, memory, concurrency, storage and latency limits declared before execution; report peaks, duration, request rates and recovery. No limits are invented in this catalog.

## Trajectory and state

Capture run, scenario and trial identities; actor, tenant and session; stable effect and separate attempt IDs; parent/handoff references; event sequence, timestamps and clock uncertainty; action/payload commitments; manifest, policy and grant versions; approval transitions; tool calls/results; errors, cancellation and terminal status; independent authoritative observation references; and memory provenance/compaction when available.

Record expected and observed destination state, violated invariants, missing visibility and artifact references. Executor acknowledgements alone are not independent destination observations. Record reviewer role/access separation before describing review as independent. Collect observable decisions and actions; private chain of thought is not required.

Keep evidence integrity, business correctness and authority acceptance as separate verdict dimensions. Export actual records to Replay and Evidence Pack using verified version mappings and explicit loss reports. Optional ODES requires its own consumer check. Hashes identify bytes; they do not prove correctness or confidentiality.

## Verdicts and coverage

| Verdict | Meaning |
|---|---|
| PASS | Applicable assertions are met with required evidence for this exact configuration |
| FAIL | An observed invariant or acceptance assertion is violated |
| INCONCLUSIVE | Execution was attempted but required observations, events or evaluator confidence are missing |
| NOT RUN | No execution evidence exists for this case/configuration |
| NOT APPLICABLE | A declared profile lacks the relevant capability; include a reason and claim boundary |

An observed violation remains FAIL even if other evidence is missing. Never pass an unevaluable assertion. Missing required authoritative observations yield INCONCLUSIVE unless an observed violation already establishes FAIL. A final correct answer cannot erase an earlier prohibited action. Do not average critical violations into an overall passing score or remove unsupported cases silently from denominators.

Before accepting evaluator output, seed missing approval, fabricated completion, prohibited access, duplicate effect and omitted observation alongside clean controls. Require detection of every seeded critical defect and report false alarms. Pin rubrics and judge configurations, review disagreements and sampled passes; an LLM judge cannot be the sole hard-security gate.

## Agent and human trials

A01–A06 require an actual supported model and harness. H01 can include scripted approval lifecycle checks, with agent behavior reported separately. H02 requires actual reviewers and known seeded defects. Scripted tests cannot establish model behavior or oversight effectiveness.

Freeze the same request, permissions, effect rules, attacks and initial state for conventional-control and governed-stack comparison; reset each arm independently. Recovery is a separate trajectory with current authority. A proposed diagnostic pilot is five runs per selected scenario/model/harness combination; this is not a reliability threshold. Separate unchanged-condition repetition from deliberate variation and pin simulated-user prompts with a fidelity assessment.

Report counts, missing trials, worst cases and per-configuration outcomes. Under independent identical Bernoulli assumptions, zero failures in n trials gives a one-sided 95% upper bound of 1 - 0.05**(1/n); five clean runs still allow about 45%. Correlation and adaptive attacks weaken that interpretation.

## Metrics

Predeclare profile-owner thresholds for business accuracy, false blocks, latency and review burden. Report unauthorized effects per applicable trial; excess committed effects and multiplicity in retry cases; false blocks per eligible authorized trial, separately from evidence-unavailable holds; unsupported completion claims per completion claim; mandatory checkpoint compliance; attack attempts and prohibited effects separately; and observation coverage/inconclusive counts.

For actual reviewer studies, report decision accuracy, seeded-defect recall, stop latency, missed intervention, backlog and human minutes. Report p50/p95 latency, cost and reconciliation time with sample counts. No empirical thresholds or measurements are claimed here.

## Acceptance and retesting

G1: exact source identity and verified containment/reset. G2: applicable deterministic invariants with no prohibited or excess duplicate effects, plus disclosed races/restore limits. G3: adequate independent observations, loss-aware records and calibrated evaluators. G4: configuration-specific agent trials and actual reviewers for respective claims. G5: separate distribution, safety and deployment decisions by their owners.

Review impact and rerun affected invariants plus bounded end-to-end smoke tests when component pins, model/harness, prompts, tools, policy/grants, adapters, memory/compaction, evidence transforms, persistence or restore procedures change. Promote triaged incidents into versioned regressions. This contract creates no production automation or recurring schedule.
