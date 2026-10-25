# 10 Architect dispositions and constitutional adoption record

**Status: documentation-only. Non-authorizing for release. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.** Not independent qualification; Tier 1 NOT QUALIFIED; PREPARE-only until an independent Tier 1 lead is designated.

This file records the OCS Architect's rulings on PR #229, received 2026-10-25 ("PR #229 — Architect rulings, closeout and next work authorization"). It records them; it does not extend them. Where this file and the ruling text differ, the ruling governs.

## 1. Assessment

The Architect accepted the qualification reuse assessment. Adopted conclusion: do not build a new qualification framework; extend existing OCS Stack Qualification infrastructure; ISSBench contributes methodology and conventions, not a mandatory implementation dependency; domain-specific oracles stay separate; cross-repository infrastructure consolidation is deferred. The engineering-effort figures in doc 07 are planning estimates, not measured results. The 44 capability classifications and the reuse matrix are unchanged by this closeout.

## 2. Dispositions

| ID | Question (doc) | Ruling | Effect on this package |
|---|---|---|---|
| D1 | Cross-repository subject checkout (doc 06 section 3) | **Reading A, permitted.** OCS Stack Qualification may check out `cognous-ocs-registry` as a subject under test, subject to the conditions below. A pinned checkout is not an architectural dependency between the two qualification systems. QPR-2 is architecturally permitted and **not authorized** for implementation in this batch | Doc 06 and 08 open questions are answered. QPR-2 stays deferred |
| D2 | Result status vocabulary (doc 01 section 4, README) | **Preserve the existing closed vocabulary.** No new persisted status value. Documentation crosswalk only, no schema migration | Crosswalk in [11](11-status-vocabulary-crosswalk.md) |
| D3 | Constitutional adoption (doc 09 section 1) | **Adopt the merged Risk-Based Testing Addendum for the OCS Registry V1 program** as an additional interpretive testing policy. The existing pinned baseline stays binding | Recorded in section 3 below |
| D4 | First implementation PR | **QPR-1 authorized** after PR #229 is closed out. QPR-2 and QPR-3 deferred. QPR-4 not authorized | Doc 08 status notes below |

### D1 conditions on any future subject checkout

Exact immutable commit SHA; read-only checkout; no untrusted workflow execution; no write credentials to the subject repository; no implicit checkout of a moving `main`; no production secrets; no registry source modification; no dependency on ISSBench; the subject commit is stated explicitly in qualification evidence.

### Status of the proposed PRs after the rulings

| PR | Status |
|---|---|
| QPR-1 gate-binding table and validator | AUTHORIZED, to start only after PR #229 is closed out; stop at a reviewed draft; not auto-merged |
| QPR-2 registry-subject profile workflow | Permitted in principle by D1; NOT authorized in this batch |
| QPR-3 suite skeleton and import map | Deferred |
| QPR-4 capture allowlist option | Not authorized |

## 3. Constitutional adoption record

| Item | Record |
|---|---|
| Existing pinned baseline (unchanged, still binding) | `cogno-us/cognous-engineering-constitution` at `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`, read as `ENGINEERING_CONSTITUTION.md` and `ADOPTION.md`. The pin is not replaced |
| Later revision containing the addendum | Same repository, `main` at `a4dd11115e47e27e8f0731a622fe950f7fbf2fc2` (commit "Use generic Governed Cognition Runtime (GCR) terminology in testing addendum"), verified by fetch on 2026-10-25. The notice cites merged constitution PR #4 |
| Addendum path | `addenda/RISK_BASED_TESTING.md` |
| Adoption decision | The OCS Architect's ruling D3 above, dated 2026-10-25, scoped to the OCS Registry V1 program |
| Publication versus adoption | Publication or possession of a revision does not establish adoption (`ADOPTION.md`). Only the Architect's ruling D3 adopts the addendum, and only for this program. Nothing here says any other repository or program has adopted the later revision |
| Articles | The 23 constitutional articles are unchanged. The addendum is interpretive guidance, not a new article |
| Conflicts | If a stricter existing requirement conflicts with the addendum, the stricter rule is kept. The one conflict found (BLOCKED / NOT EXECUTED wording) is resolved by D2 and [11](11-status-vocabulary-crosswalk.md) |
| Not resolved | A different revision, `6f7f2731`, is called provisional guidance in the project status record. Whether it is adopted is still UNVERIFIED and is not decided here |

## 4. Limits

This closeout changes only documentation under `docs/ocs-v1-qualification-reuse-audit/`. No historical test result, expectation, fixture, workflow, status or scenario was edited. Copilot review and passing CI are technical review, not independent qualification.
