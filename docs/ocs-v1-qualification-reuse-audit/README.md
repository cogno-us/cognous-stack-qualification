# OCS V1 qualification reuse and duplication audit

**Status: documentation-only analysis for OCS Architect review. Non-authorizing. DRAFT. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.**

Question: can OCS Registry V1 be qualified with the infrastructure that already exists in this repository, and what, if anything, is genuinely missing? The comparison is by capability, not by product-specific oracle. `cognous-issbench-v2` was read as a read-only reference.

This package does not implement any change, add or edit a test, expectation, fixture, workflow, schema or result, create a status, re-score a scenario, depend on another repository, or modify an implementation repository. It does not qualify anything. Builder-side inspection only: **Tier 1 NOT QUALIFIED.** No independent qualification lead is designated (GAP-G4-13), and nothing here is a verdict.

## Deliverables

| # | Deliverable | File |
|---|---|---|
| 1 | Existing OCS capabilities | [01-existing-ocs-capabilities.md](01-existing-ocs-capabilities.md) |
| 2 | Relevant ISSBench mechanisms | [02-issbench-mechanisms.md](02-issbench-mechanisms.md) |
| 3 | Reuse and duplication matrix | [03-reuse-and-duplication-matrix.md](03-reuse-and-duplication-matrix.md) |
| 4 | Genuine OCS V1 qualification gaps | [04-genuine-qualification-gaps.md](04-genuine-qualification-gaps.md) |
| 5 | Minimum necessary new test infrastructure | [05-minimum-new-infrastructure.md](05-minimum-new-infrastructure.md) |
| 6 | Recommended ownership and integration | [06-ownership-and-integration.md](06-ownership-and-integration.md) |
| 7 | Estimated engineering effort avoided | [07-engineering-effort-avoided.md](07-engineering-effort-avoided.md) |
| 8 | Proposed bounded implementation PRs | [08-proposed-bounded-prs.md](08-proposed-bounded-prs.md) |
| | Sources, pins, limits, corrections | [09-source-and-evidence-manifest.md](09-source-and-evidence-manifest.md) |

Data: [`data/capability-matrix.csv`](data/capability-matrix.csv) and `.json` (44 capabilities, each in exactly one of the five classes), [`data/gate-coverage.csv`](data/gate-coverage.csv) and `.json` (QG-01..QG-14). [`method/validate_audit.py`](method/validate_audit.py) checks the data is closed-vocabulary and self-consistent; it is not repository tooling and is wired to no workflow.

## Headline findings

1. **No new qualification system is needed.** 14 of 44 capabilities are REUSE UNCHANGED and 3 are EXTEND EXISTING. Most of what the V1 profile needs for evidence records, immutable writes, freeze and pin handling, versioned expectations, failure and limit registers, refusal templates, Route B atomic fixtures and revocation oracles already exists here, with the gaps in doc 04 (no QG-nn table, no registry-subject workflow, nothing written for QG-05, 07, 14). **REASONED INFERENCE** over matrix rows Q01 to Q31 (most rows are SOURCE FACT; Q19 and Q30 are REASONED INFERENCE; Q20 is UNVERIFIED).
2. **No ISSBench code should be reused or referenced.** The two repositories have no coupling today, in either direction, and no byte-identical file. ISSBench's own documents state that it keeps its own oracle custody and that OCS owners keep generic execution, replay, packaging and verifier services. What ISSBench offers is method: freeze before execution, additive successors, distinct BLOCKED, and a few property checklists. This repository already does all of these. **SOURCE FACT**
3. **The fourteen gates are not defined in this repository.** `QG-01..QG-14` live in the merged P1 plan in `cognous-ocs-registry` (`docs/p1-extraction-plan/data/qualification-gate-matrix.json`). `grep QG-[0-9]` finds nothing here. QG-02 is INACTIVE there (`max_amount` deferred). Other "gate" names in this repository (OCS-1/2/3, MVP G-00..G-15, V1-M/R/C) are different things. **SOURCE FACT**
4. **Qualification-side coverage by existing tests, by gate:** 10 PARTIAL, 3 NONE (QG-05, QG-07, QG-14), 1 INACTIVE (QG-02). No gate is covered in full, and PARTIAL means adjacent reusable tests exist, not that any gate has passed. Existing tests are mostly authority-level and Control Plane-level: they exercise revocation, expiry, atomicity and refusal evidence, not registry-sourced policy at the effect boundary. **REASONED INFERENCE** (reading, no suites run)
5. **The genuine gaps are few and specific.** Nothing builds a policy from a registry record, no selection-level test exists in this repository, no claim carries an effective-policy identity, approval-age behaviour has no test, and no test separates pre-construction deny-all from a `LocalExecutionPolicy.check` denial. Most are also blocked because there is nothing to execute until the planned registry consumer and claim-carried binding exist. **SOURCE FACT** (doc 04)
6. **Minimum new infrastructure is one data file, one validator and one workflow (plus an optional suite skeleton and import map)**, plus new test files that import existing helpers. No new schema, record kind, status, collector, fixture library or dashboard. The allowlist in `tools/qualification_results.py` does not need to change if the registry-subject workflow lives in this repository. **REASONED INFERENCE** (doc 05)
7. **Effort avoided is estimated at about 41 to 74 engineer-days** against about 5 to 9.5 for the proposed PRs (builder-side, excluding independent oracle authoring that is needed either way). These are estimates with stated assumptions, not measurements. **REASONED INFERENCE** (doc 07)
8. **Duplication exists but is not a V1 blocker.** Seven consolidation candidates, none proposed for V1: five coexisting status vocabularies, a byte-identical `_index_signing.py` pair, reimplemented canonical-JSON and digest helpers whose flags differ, and near-identical workflow boilerplate. Consolidating any of them touches existing tests, so it is deferred. **SOURCE FACT**

## Constraint check

| Requirement | Result |
|---|---|
| Preserve the 696-scenario inventory | Re-counted at 696 rows (NO_TEST 602, NOT_RUN 67, PASS_RECORDED 23, KNOWN_LIMIT_ASSERTED 4); no row touched |
| Preserve all historical evidence statuses | None edited or re-scored |
| Do not duplicate existing fixtures | Every proposed test reuses an existing helper (doc 05) |
| Do not invent qualification statuses | None proposed; no status is stored in the data files; `method/validate_audit.py` checks only the audit's own class, label and coverage vocabularies. A status check against the repository's closed sets does not exist yet (it is part of the proposed N1, doc 05) |
| Do not rewrite existing test expectations | None touched |
| Do not recreate ISSBench infrastructure | Nothing ported; see doc 02 |
| No cross-repository dependencies | None under Reading A; the proposed registry-subject workflow (N2 / QPR-2) would violate the rule under Reading B, so it waits for the Architect's reading (doc 06 section 3) |
| Do not modify implementation repositories | None modified |
| QG-02 remains INACTIVE | Reported inactive throughout; never counted as PASS |
| No independent Tier 1 claim | None made |

Source pins and limitations: [09](09-source-and-evidence-manifest.md). Base: `cognous-stack-qualification` main `be1994a961e4e40612d999972ede6547a3729887`.

## Testing cadence

The Architect notice of 2026-10-25 directs adoption of the Constitution's [Risk-Based Testing addendum](https://github.com/cogno-us/cognous-engineering-constitution/blob/main/addenda/RISK_BASED_TESTING.md) (constitution PR #4; read at `main` `a4dd11115e47e27e8f0731a622fe950f7fbf2fc2`). It applies here as follows. The addendum is interpretive guidance; it does not confer adoption, and adoption is the Architect's decision under `ADOPTION.md`.

- **This PR is documentation only.** It ran no qualification battery and needs only the repository's existing CI. Status: analysis for review, not independently qualified. Tier 1 NOT QUALIFIED; PREPARE-only until an independent lead is designated.
- **Reuse over a new framework** is the audit's finding (doc 03) and matches the addendum's anti-pattern "a second verifier, runner, dashboard or evidence platform absent a demonstrated gap".
- **Proposed PRs QPR-1 to QPR-3** (doc 08) are Level 1/Level 2 work: build and unit-check the table, workflow and skeleton; do not run the full 696-scenario battery per PR. They touch no effect boundary.
- **High-risk exception.** Test content for selection and activation, claim-carried identity, revocation, expiry and rollback, atomic Route B and negative-evidence custody (gates QG-03, 04, 06, 08, 09, 10, 11, 13 and similar) is in the addendum's escalation class. Those cases need their negative, adversarial and recovery controls before merge, not only at the milestone. That is the independent oracle author's work and is not proposed here.
- **Level 3** (freeze, full applicable battery, independent oracles) stays a milestone activity and needs the designated independent lead (GAP-G4-13).
- **Reported conflict, stricter requirement kept.** The addendum reports "PASS / FAIL / BLOCKED / NOT EXECUTED". This repository's closed result vocabulary is PASS / FAIL / INCONCLUSIVE / NOT RUN / NOT APPLICABLE, with BLOCKED only in the mvp-chain verdict. This audit invents no mapping and adds no status; it keeps the existing sets. How BLOCKED and NOT EXECUTED relate to INCONCLUSIVE and NOT RUN is a question for the Architect.
- **Coverage words.** `PARTIAL`, `NONE` and `INACTIVE` in `data/gate-coverage.*` mean only that adjacent tests are listed by the merged plan or exist in this repository. They are not result statuses. `PARTIAL` is weak for QG-04 and QG-06, whose listed tests are NOT RUN or cannot detect the relevant toggle (doc 04, G-H); read those as close to `NONE`.
