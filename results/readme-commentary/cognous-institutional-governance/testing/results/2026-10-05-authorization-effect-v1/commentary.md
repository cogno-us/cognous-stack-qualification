# Historical test-result commentary: cognous-institutional-governance

Public source: [`testing/results/2026-10-05-authorization-effect-v1/README.md`](https://github.com/cogno-us/cognous-institutional-governance/blob/614df9e0ca8c044725f7cca1d5149a49c2da4d91/testing/results/2026-10-05-authorization-effect-v1/README.md) at commit `614df9e0ca8c044725f7cca1d5149a49c2da4d91`, Git blob `125d347371ae8e45bc158139d78dbfe8af9f9398`.

Only test-result excerpts or bounded summaries are relocated here. Unrelated evaluator, security, license, release and implementation material stays at its source. These are historical statements, not a new test run, validation, current selection claim or deployment approval. Review the exact source for full context and applicable license/notice terms.

Move result narrative without changing fixtures, code, observations or integrity manifests.

## Recorded test commentary

**Executive summary:** twenty fixtures produced sixty deterministic observations.
Both guarded configurations satisfied all twenty authored oracles, including all
ten legitimate countercases. The authorization-only toy satisfied nine. This
shows local mechanics on supplied conditions, not institutional effectiveness.

**EXECUTED_SYNTHETIC — NOT_INDEPENDENTLY_REVIEWED.**

| Arm | Observations | Complete oracles satisfied | Primary variants satisfied | Positive variants satisfied |
|---|---:|---:|---:|---:|
| Authorization-only toy | 20 | 9 | 0 | 9 |
| Conventional guarded controls | 20 | 20 | 10 | 10 |
| Same controls plus Alvorada-inspired records | 20 | 20 | 10 | 10 |

```sh
python3 testing/harness/run_authorization_effect.py --output testing/runs/authorization-effect-repeat
python3 testing/harness/verify_authorization_effect.py
python3 -m unittest discover -s testing/harness -p 'test_authorization_effect.py' -q
```

One process, one database connection, invented grants and logical clocks control
all conditions and observations. A simulated separate verifier is not independent.
The observer API's lack of execution methods is not permission or process isolation.
There is no real remote state, concurrent executor, revocation service, hostile
input corpus, cryptographic verification, ODES conformance or full mediation.
