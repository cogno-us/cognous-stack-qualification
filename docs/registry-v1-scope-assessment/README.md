# OCS Registry V1 scope assessment

**Status: documentation-only analysis for OCS Architect review. Non-authorizing. DRAFT. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.**

Question: using the **existing** Cognous qualification corpus (the AI Security Wiki cases, the V1 scenario catalog and batteries, the security-runtime and MVP suites), which OCS Registry rule families are necessary, valuable, redundant or deferrable for a V1 release profile?

It does not create a scenario catalog or a qualification framework, move or rewrite any suite, change any expectation or verdict, authorize or perform any migration, approve a pin, select or activate any record, or modify the registry plan (plan v1.3, draft; this package changes no plan version). The Architect's R07 rulings are treated as design guidance, not implementation authority. Decisions D1, D5, D6 and D12 and the 32 UNRESOLVED S02 rows are referenced as open and are not resolved here.

## Deliverables

Nine deliverables, in file order (the numbering of the files is the order of the table):

| # | Deliverable | File |
|---|---|---|
| 1 | Executive assessment | [01-executive-assessment.md](01-executive-assessment.md) |
| 2 | Canonical scenario crosswalk (696 rows, 21 columns) and three-question view | [02-canonical-scenario-crosswalk.md](02-canonical-scenario-crosswalk.md); [data/canonical-scenario-crosswalk.csv](data/canonical-scenario-crosswalk.csv) / [json](data/canonical-scenario-crosswalk.json); [data/three-question-view.csv](data/three-question-view.csv); 162 suite-local claims in [data/suite-local-claims-supplement.csv](data/suite-local-claims-supplement.csv) |
| 3 | Family coverage matrix (and Profiles A-D, F7) | [03-family-coverage-matrix.md](03-family-coverage-matrix.md) |
| 4 | Prioritization analysis with sensitivity | [04-prioritization-analysis.md](04-prioritization-analysis.md) |
| 5 | Gap register G1-G4 (33 gaps) | [05-gap-register.md](05-gap-register.md) / [data/gap-register.csv](data/gap-register.csv) |
| 6 | Proposed V1 acceptance matrix | [06-v1-acceptance-matrix.md](06-v1-acceptance-matrix.md) / [data/v1-acceptance-matrix.csv](data/v1-acceptance-matrix.csv) |
| 7 | Source and evidence manifest | [07-source-and-evidence-manifest.md](07-source-and-evidence-manifest.md) |
| 8 | Model A versus Model B comparison and V1 boundary recommendation | [08-model-a-b-comparison.md](08-model-a-b-comparison.md) |
| 9 | Configuration-extraction handoff (planning manifest for P1) | [09-configuration-extraction-handoff.md](09-configuration-extraction-handoff.md) / [data/configuration-extraction-manifest.jsonl](data/configuration-extraction-manifest.jsonl) / [csv](data/configuration-extraction-manifest.csv) |

Supporting: [appendix/](appendix/) holds the six lane reports (A Wiki, B V1/security-runtime, C cross-component/MVP, D family source analysis, E outcome classification, F evidence audit) and the per-owner extraction-manifest rows and notes (`lane-P1-*`). [method/](method/) holds the stdlib-only analysis scripts (not repository tooling, not wired to any workflow). [data/validation-report.json](data/validation-report.json) is the output of `method/validate_crosswalk.py`.

## Headline findings

1. Across 696 canonical scenarios and 162 suite-local claims, **no scenario makes registry-managed configuration REQUIRED**; 17 in-scope canonical rows are BENEFICIAL, 24 UNKNOWN, 64 UNNECESSARY (REASONED INFERENCE). V1 value is governed change control of values the components already enforce.
2. **No path from registry to enforcement exists today** (`apply_registry_overlay` has no caller; the `LocalExecutionPolicy` check runs outside the atomic transaction). R09 and R10 decide V1 more than the family list does.
3. **Recommended V1:** F1a + F1b mandatory; F1c, F4, F5 conditional on named rulings (D6; D4/D1; W8-014); F6, F1d, F7, F3, F9, F10, F11 deferred; F8 is not a policy family. Profiles C and D add nothing a decision-free profile can use.
4. **Nothing is qualified:** no scenario-level PASS in any controller run; no recorded evidence at Control Plane `7a4bcd40` / Runtime `c5e97e87`; all 656 Wiki cases NOT RUN; no independent qualification owner (D13).
5. Existing enforcement defects and known limits stay with their owners (G1); the register separates them from registry gaps (G2, G3) and evidence gaps (G4).

Source pins and limitations: [07](07-source-and-evidence-manifest.md). Base: `cognous-stack-qualification` main `998d39c5ba1c9d537be8289f7658f2e9cde6cbba`.
