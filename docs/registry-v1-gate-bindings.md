# OCS Registry V1 gate bindings (QPR-1)

**Status: PROPOSED, UNADOPTED preparation record. Documentation and validation only. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD. INDEPENDENT QUALIFICATION: NOT STARTED. Tier 1 NOT QUALIFIED. QG-02 INACTIVE.**

QPR-1 is the bounded prerequisite for EXT-S5-1 (gate catalogue and predeclaration) in the registry P1 plan. It is not a new sprint, framework or release gate. S5 stays PREPARE-only until G-6. It follows the Architect rulings recorded in [the reuse audit](ocs-v1-qualification-reuse-audit/10-architect-dispositions-and-adoption-record.md).

## What it adds

| File | Purpose |
|---|---|
| `process/registry-v1/gate-bindings.proposed.v1.json` | One row per gate QG-01..QG-14 from the merged plan matrix (registry `d2c472e4`, matrix sha-256 `e81b5fad…04bd`). Each row binds the plan's scenario ids, existing test references, sprint, mode, known gaps, the count of predeclared new test items and the digest of the plan row |
| `process/registry-v1/validate_gate_bindings.py` | Rejects a missing or inconsistent binding. Run `python3 -I process/registry-v1/validate_gate_bindings.py`; add `--matrix <copy of the plan matrix>` to check for drift (it checks the stored row digest and re-derives every copied binding field from the source row) |
| `tests/test_gate_bindings.py` | 31 focused unit tests, positive and negative. They execute no qualification scenario |

## What it does and does not do

- Every active gate has a binding; QG-02 is `INACTIVE_MAX_AMOUNT_DEFERRED`, not mandatory and excluded from the active count of 13.
- Scenario ids resolve against the existing inventory (`canonical-scenario-crosswalk.json`, `scenarios/catalog.json`). Plan annotations such as `C20 (NO_TEST)` are split into the id and an annotation. QG-14 binds all canonical scenarios and lists none.
- Source and contract references are explicit (repository, revision, path, role), including the pinned Constitution and the adopted testing addendum.
- It stores **no** execution result, status or verdict: any `status`, `result`, `verdict` or similar key is rejected, as are qualification-claim phrases. `qualified` must be `false`.
- It does **not** copy the plan's predeclared new test items (the independent oracle author's work under EXT-S5-1), edit any oracle expectation, fixture, scenario row, workflow or historical result, or import anything from another repository.

## Reuse versus new

Reused: `validate_requirements` in `tools/v1_validation.py` (the existing requirement-row model: unique ids, row structure), the existing scenario inventory, and the plan matrix as data. New: the binding table, one validator of about 150 lines, and the tests. Gate rows use the existing row shape with `kind: "gap"` (no executable test exists yet) and `mandatory` true or false; the binding fields are extra keys, which the row model ignores.

## Findings from the discovery work

1. **`validate_requirements` runs without a frozen V1 implementation candidate.** The function is pure (it reads only its argument). Importing `tools/v1_validation.py` reads the repository's committed freeze manifest and refreeze log, but needs no component checkout or candidate. Confirmed by running it on the real 131-row file and on synthetic rows.
2. **Blocker or reason fields.** There is no dedicated blocker-reason field in the result records. Existing free-text fields next to a status: `reason` (job, probe, computed requirement rows and mvp-chain verdict rows), `not_applicable_reason` (required for NOT APPLICABLE, `v1_validation.py:733`), `adequacy_note`, `classification`, `detail`, and `limitations` on telemetry records. Only mvp-chain has `blocked_reason`, copied into `reason` for BLOCKED. Per ruling D2, a blocker is recorded as the existing applicable status plus `reason`. Nothing is added here. If a dedicated field is ever wanted, the smallest compatible extension is a `blocked_reason` string on result rows, modelled on mvp-chain; it is **not** proposed or implemented.
3. **New files under `tools/` or `suites/` break the MVP acceptance commitment.** The candidate commitment pins every file directly in `tools/` and `suites/`, and two tests in `tests/test_mvp_acceptance_gate.py` fail when one is added. Fixing that means a new versioned candidate, so the validator lives beside the table instead. Future qualification tooling for this program should do the same unless a new candidate is intended.

## Known gaps and limitations

- Existing-test references listed by the plan for the **registry builder** (26 of 74) are recorded with their repository-relative path but are **not checked** here; this repository does not read the registry. They remain builder-side evidence only.
- Of the 74 plan references, 47 name a path in this repository and are checked for existence (four of them are row groups in `process/`, checked at file or directory level), 26 are registry-builder tests (not checked), and one is descriptive with no path (`v1-probes and fix2-probes KNOWN_GAP rows (not protection)`), kept verbatim.
- References resolve to files, not to individual tests; a renamed test inside an existing file is not detected.
- `known_gaps` text is the audit's adjacent-test note per gate, not a coverage claim. Gates QG-05, 07 and 14 have no adjacent tests; QG-04 and QG-06 have only weak ones.
- The plan's sandbox paths (`/home/claude/cognous-ocs-registry/…`) are normalised to relative registry paths.
- Prose-only identifiers in the plan (for example `NC1-01..05`, `GAP-G4-05`) are not scenario ids and are not resolved.
- The optional `--matrix` check needs a copy of the plan matrix supplied as data; it is not wired to any workflow.
- Nothing here qualifies OCS V1. Passing this validator or CI is not independent qualification.
