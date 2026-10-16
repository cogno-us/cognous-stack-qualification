# Historical test-result commentary: cognous-institutional-governance

Public source: [`testing/README.md`](https://github.com/cogno-us/cognous-institutional-governance/blob/614df9e0ca8c044725f7cca1d5149a49c2da4d91/testing/README.md) at commit `614df9e0ca8c044725f7cca1d5149a49c2da4d91`, Git blob `aa60922a467e0f21d0ed5c7bc97bfde3ef021d4d`.

Only test-result excerpts or bounded summaries are relocated here. Unrelated evaluator, security, license, release and implementation material stays at its source. These are historical statements, not a new test run, validation, current selection claim or deployment approval. Review the exact source for full context and applicable license/notice terms.

Retain test design and local commands; move run outcomes and repository check history to the central test hub.

## Recorded test commentary

| Area | Contents | Status |
|---|---|---|
| [Battery](https://github.com/cogno-us/cognous-institutional-governance/blob/614df9e0ca8c044725f7cca1d5149a49c2da4d91/testing/README.md) | 40 incident-inspired and seven lifecycle exercises | 47 PROPOSED; full operational exercises unexecuted |
| [Protocol](https://github.com/cogno-us/cognous-institutional-governance/blob/614df9e0ca8c044725f7cca1d5149a49c2da4d91/testing/README.md) | Recommended program, comparison design, measures and status rules | Operational program pending |
| [Incident sources](https://github.com/cogno-us/cognous-institutional-governance/blob/614df9e0ca8c044725f7cca1d5149a49c2da4d91/testing/README.md) | News reporting, primary supplements and evidence qualifications | Reporting links checked; access limits recorded |
| [Harness design](https://github.com/cogno-us/cognous-institutional-governance/blob/614df9e0ca8c044725f7cca1d5149a49c2da4d91/testing/README.md) | Construction method, configurations, gates, oracles and limits | Deterministic reference adapter only |
| [Film-review adapter](https://github.com/cogno-us/cognous-institutional-governance/blob/614df9e0ca8c044725f7cca1d5149a49c2da4d91/testing/README.md) | 42 narrow subtests mapped to 21 FW/TB proposals; 126 observations | EXECUTED_SYNTHETIC; full exercises pending |
| [Fixtures](https://github.com/cogno-us/cognous-institutional-governance/blob/614df9e0ca8c044725f7cca1d5149a49c2da4d91/testing/README.md) | 24 fixed synthetic subtests and recovery data | Invented; no real participants or production data |
| [Results](https://github.com/cogno-us/cognous-institutional-governance/blob/614df9e0ca8c044725f7cca1d5149a49c2da4d91/testing/README.md) | Raw 72-run observations, interpretation and reproducibility evidence | EXECUTED_SYNTHETIC; not independently reviewed |
| [Execution template](https://github.com/cogno-us/cognous-institutional-governance/blob/614df9e0ca8c044725f7cca1d5149a49c2da4d91/testing/README.md) | Actual operational run record requirements | Template only |
| [Repository checks](https://github.com/cogno-us/cognous-institutional-governance/blob/614df9e0ca8c044725f7cca1d5149a49c2da4d91/testing/README.md) | Validator and existing invariant tests | Conformance checks, not efficacy evidence |

```sh
python3 testing/harness/run_authorization_effect.py --output testing/runs/authorization-effect-repeat
python3 testing/harness/verify_authorization_effect.py
python3 -m unittest discover -s testing/harness -p 'test_*.py' -q
```

The [modular-remediation check record](https://github.com/cogno-us/cognous-institutional-governance/blob/614df9e0ca8c044725f7cca1d5149a49c2da4d91/testing/README.md) documents current
conformance checks and explicit limits; it is not a module-efficacy result.

Against base `1ea31ee79f77f2e6b6c1124c93b52b55c0fbce3d`, Python 3.12.14:
the repository validator, 423 repository tests, eight harness tests and both
archived integrity/replay verifiers passed. All 1,433 relative Markdown file
destinations resolved (external URLs and fragment anchors not certified).
Whitespace, Markdown-only scope and bounded changed-document marker checks passed;
SR01–SR16 are distinct proposals. Original constitutional data, source-status
registers, code, fixtures and frozen results remain unchanged. These are repository
checks, **not execution of the sixteen stewardship scenarios**, source/legal
verification or evidence of institutional benefit.

Against public base `3d614fa71bfbabc689aebb44923a1dabaf825922` (local base
`bcf24236318607ff0bf7fae5e51871fecd82afe6`, identical tree
`592aea78c4edae58dc3c188197dc06dc7e70168b`), Python 3.12.14:
repository validator, 423 repository tests, eight harness tests and both archived
integrity/replay verifiers passed. The reference and film runners were also
executed afresh. Their per-case observations and summaries exactly reproduced
the existing [reference archive](https://github.com/cogno-us/cognous-institutional-governance/blob/614df9e0ca8c044725f7cca1d5149a49c2da4d91/testing/README.md) and
[film archive](https://github.com/cogno-us/cognous-institutional-governance/blob/614df9e0ca8c044725f7cca1d5149a49c2da4d91/testing/README.md).

| Existing synthetic adapter | Fresh observations | Conventional / Alvorada-inspired oracle satisfaction | Deliberately permissive toy arm |
|---|---|---|---|
| Reference | 72: 24 fixtures × three arms | 24/24 each | 3/24 |
| Film | 126: 42 fixtures × three arms | 42/42 each | 15/42 |

The equal guarded outcomes establish no incremental effect benefit. These runners
use deterministic supplied fixtures, not live models, institutional actors or the
new OECD scenarios. Fresh bundles record the local base and documentation-dirty
working tree in ignored `testing/runs/`; duplicate bundles are not new committed
archives. The unchanged archives remain the canonical raw evidence. To reproduce,
use **new, nonexistent** output directories:

```sh
python3 testing/harness/run_reference.py --output testing/runs/oecd-reference-repeat
python3 testing/harness/run_film_review.py --output testing/runs/oecd-film-repeat
python3 testing/harness/verify_snapshot.py
python3 testing/harness/verify_film_review.py
python3 tools/validate_bootstrap.py
python3 -m unittest discover -s tests -q
python3 -m unittest discover -s testing/harness -p 'test_*.py' -q
```

Against public base `7345eb2b591fcf41d44fa4845d3a42c267cb57dc` and identical-tree
local base `45e76097c83f5af3940e0718c90bfd673481f412`, Python 3.12.14:
423 repository tests and 22 harness tests passed (**445 total**, including fourteen
new boundary/mutation tests). The repository validator and all three archive
verifiers passed. The [new archive](https://github.com/cogno-us/cognous-institutional-governance/blob/614df9e0ca8c044725f7cca1d5149a49c2da4d91/testing/README.md)
records sixty new synthetic observations; both guarded configurations satisfied
20/20 fixture oracles and 10/10 positive variants, while the authorization-only toy
satisfied 9/20 complete oracles and 9/10 positives.

The documentation check resolved 1,555 relative file destinations and fragment
links in changed Markdown, twenty unique paired fixture IDs and bounded current
change markers. Whitespace and scope checks passed. New code/fixtures/archive are
isolated in testing; original constitutional data, source-status records, original
harnesses/fixtures and old archives are unchanged. No external-link availability,
exhaustive IP clearance, ODES conformance, real identity isolation, distributed
atomicity, operational efficacy or independent institutional review is certified.

```sh
python3 testing/harness/run_reference.py
python3 testing/harness/verify_snapshot.py
python3 tools/validate_bootstrap.py
python3 -m unittest discover -s tests -q
```

Both guarded configurations satisfied the same 24 predefined fixture outcomes; the deliberately permissive toy baseline satisfied three. Nineteen hazardous cases were blocked and all three legitimate allows were retained by both guarded configurations. Pending delivery and recovery behaved as specified. The Alvorada-inspired arm adds records but has identical effect controls. This establishes no incremental effect benefit, historical prevention or real-world efficacy. Record richness needs independent human evaluation.

[FW01–FW11](https://github.com/cogno-us/cognous-institutional-governance/blob/614df9e0ca8c044725f7cca1d5149a49c2da4d91/testing/README.md) add eleven proposed exercises for uncertainty, correlated evidence, purpose, metrics, harm, reconsideration, accountability and near misses. Together, the original frozen 47-case battery and this eleven-case supplement specify 58 proposed exercises. The 90 application exercises are separate. The full supplement remains unexecuted and is not covered by the original 24 fixtures or 72 observations; the original battery, harness and archives are preserved.

[TB01–TB10](https://github.com/cogno-us/cognous-institutional-governance/blob/614df9e0ca8c044725f7cca1d5149a49c2da4d91/testing/README.md) add ten proposed exercises on evidence omissions, observation conditions, contamination, incentives, synthetic reconstructions, access, reconsideration and correction effects. The original and film batteries contain **68 proposed exercises**: 47 original cases, 11 FW cases and 10 TB cases. The 90 application exercises remain separate. No full FW or TB operational exercise has been executed or reviewed. The original 24 fixtures and 72 observations cover neither supplement; the new film adapter supplies separately documented narrow synthetic coverage.

```sh
python3 testing/harness/run_film_review.py
python3 testing/harness/verify_film_review.py
```

The [2026-10-04 archive](https://github.com/cogno-us/cognous-institutional-governance/blob/614df9e0ca8c044725f7cca1d5149a49c2da4d91/testing/README.md) records 126 final film-adapter observations, a rerun of the original 72 observations, and current repository checks. Conventional and Alvorada-inspired controls have identical effects; no incremental institutional benefit is established.
