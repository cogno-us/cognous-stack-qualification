# PRP K6 actual OpenAI evaluation — 2026-10-15

All 18 fresh-context agent trials completed, using 36 actual OpenAI Responses calls to `gpt-6.1-sol`. The provider returned that exact model ID and the default service tier on every call. No retries or incomplete trials occurred.

| Measure | Baseline | PRP |
|---|---:|---:|
| Fresh-context trials | 9 | 9 |
| Null + discriminating paired passes | 3/3 | 3/3 |
| Preregistered perturbation direction passes | 3/3 | 3/3 |
| Input tokens (all calls) | 7,101 | 172,989 |
| Output tokens, including reasoning | 1,745 | 1,852 |
| Estimated API spend, USD | 0.031652 | 0.364498 |
| Sum of provider request latency, seconds | 55.646 | 60.528 |

Total estimated spend was **USD 0.396150**, below the USD 3 cap. Every reservation settled. Estimates use the campaign's recorded rates and do not guarantee the provider invoice. Latency is descriptive for this sequential small run; it is not a controlled throughput benchmark.

Both conditions returned posterior [0.5, 0.5] and `gather` on every null case, posterior [0.9, 0.1] and `act_h0` on every discriminating case, and posterior [0.8, 0.2] and `gather` on every weaker-signal case. The paired scorer reports zero regret for both twins in all repetitions. The preregistered perturbation score checks direction only; its action and posterior magnitude are visible observations, not additional preregistered endpoints.

**Interpretation:** this synthetic case showed no measured PRP improvement over baseline. Baseline already achieved the maximum score. PRP consumed more input tokens and cost more in this setup, where the entire public skill and three references were loaded for each PRP conversation. Three repetitions of a single simple author-model case cannot establish general efficacy, equivalence, or harm. Harder, preregistered cases would be needed to discriminate performance.

## Reproducibility and evidence

- [Actual workflow run](https://github.com/cogno-us/cognous-stack-qualification/actions/runs/38821181897), success.
- Runner/config commit: `5b86c028fafa7853c3820c2084ceb0dc7f03fb6d`.
- PRP source pin: `b3ffa8559db05188f3471c5b0bfe5d936a4bcb29`.
- [Original evidence artifact](https://github.com/cogno-us/cognous-stack-qualification/actions/runs/38821181897/artifacts/12013745469), includes SQLite ledger; retained for 90 days.
- Artifact ZIP SHA-256: `d5b642dcfc3572cc97641df610cf22abc549bb9217d94144ceb2a7f62ec628ea`.
- `manifest.json` records all 36 unique response IDs, actual model identities, usage, request latency, visible messages, tool arguments/results, decisions, source hashes, exact schedule, scores, and execution bounds.
- Instructions, tools, author-model case, config and verified summary are retained alongside this receipt. The fixture's historical `execution_status: unexecuted` describes its original offline provenance; the actual run status is `COMPLETE` in the manifest.
- Independent local verification matched all PRP source hashes and the runner hash, checked all response identities/tool sequences, recomputed every score using the pinned scorer, and reconciled estimated spend to USD 0.396150.
- Five offline tool-loop/accounting controls passed locally and on the hosted runner. A separate constructed-output integration check exercised six scorer pairs and six perturbations without model calls.

Each trial used a new in-memory conversation, identical model/settings/tools/task inputs, medium reasoning, maximum 1,536 output tokens per call, and at most three calls. Condition and observation order were counterbalanced. The baseline instruction explicitly requested Bayesian updating and minimum permitted expected loss; no expected answers or grading annotations were supplied to either agent condition. Only the PRP condition received protocol text. Finer immutable model revision, temperature and seed were unavailable. Hidden reasoning was never logged.

Final integration/security review holds remain deferred and unchanged.
