# 02 Canonical scenario crosswalk

The crosswalk is machine-readable: [data/canonical-scenario-crosswalk.csv](data/canonical-scenario-crosswalk.csv) (and the identical [JSON](data/canonical-scenario-crosswalk.json)). It does not duplicate the scenario catalog: it references each scenario by its source ID and adds the registry-scope columns. Non-authorizing; nothing here alters `scenarios/catalog.json`, `coverage-map.json` or any verdict.

## Rows

**696 rows, one per distinct canonical scenario**: 40 Cognous catalog scenarios (D01-D09, A01-A06, H01-H02, C01-C23) and 656 AI Security Wiki cases (`TC-*` IDs from `applicability.json`: 20 APPLICABLE, 45 PARTLY_COVERED, 591 NOT_APPLICABLE). Source IDs and order are preserved. The 591 NOT_APPLICABLE cases are retained with their recorded reason (`exclusion_impact`), `registry_family = NONE`, and priority `OUT_OF_SCOPE`; unmapped mechanisms in the in-scope set are explicit `UNMAPPED` rows with the reason in `exclusion_impact`, not dropped.

A separate supplement, [data/suite-local-claims-supplement.csv](data/suite-local-claims-supplement.csv), lists **162 suite-local claims** (`SL:<suite>:<slug>`) from suites whose protections are not catalog scenarios (security-runtime, operation-identity, v1-probes, fix2-probes, mvp-chain, mvp-d09, mvp-d2-route-b, outside-holder, governed-exchange, verifier-mutation and relocated component suites). They are grouped claims, not test functions and not scenarios, are counted separately, and are never added to the 696.

## Columns (the 21 required, in order)

| Column | Content | Source / label |
|---|---|---|
| `scenario_id` | Source ID, verbatim | catalog / applicability |
| `scenario_source` | `cognous scenarios/catalog.json v1.0.0` or the Wiki file + anchor at commit `1a0c72de` | source |
| `scenario_title` | Source title | source |
| `applicability` | Wiki: `APPLICABLE / PARTLY_COVERED / NOT_APPLICABLE` as recorded; catalog: `APPLICABLE_DECLARED_PROFILE / CONDITIONAL / UNKNOWN` from the catalog's own applicability text | source; Lane B |
| `customer_security_outcome` | `PRIMARY|SECONDARY` from the 12-category taxonomy (plus `OTHER_OR_OUT_OF_SCOPE`) | Lane E, REASONED INFERENCE |
| `test_ids` | `;`-joined: `suite-path::symbol` (catalog) or test function names (Wiki). Parametrised tests appear once. | source (validated) |
| `test_suite` | Owning suite(s) | source |
| `component_route` | `CROSS_COMPONENT_INTEGRATION / BOTH / COMPONENT_LOCAL / UNKNOWN` (Wiki in-scope rows: the route description recorded by Lane A, for example "route A ..."; empty for NOT_APPLICABLE) | Lane C (catalog), Lane A (Wiki) |
| `source_commit` | Qualification `998d39c5` (+ Wiki `1a0c72de`; + Control Plane `7a4bcd40` / Runtime `c5e97e87` where enforcement source was read) | [07](07-source-and-evidence-manifest.md) |
| `enforcement_component`, `enforcement_function` | Component and `path:line` at the pinned head, or "repo not cloned" | SOURCE FACT where cited; UNVERIFIED otherwise |
| `existing_protection` | `ENFORCED_AND_EVIDENCED / IMPLEMENTED_NOT_QUALIFIED / PARTIALLY_ENFORCED / KNOWN_GAP / NOT_APPLICABLE / UNKNOWN` | REASONED INFERENCE |
| `existing_configuration_mechanism` | How an operator sets the value today (constructor, profile, manifest, resolver data, none) | SOURCE FACT |
| `registry_family` | `F1a ... F11`, `NONE`, `UNMAPPED` (comma-joined) | REASONED INFERENCE against the R07 taxonomy |
| `registry_dependency` | `REQUIRED / BENEFICIAL / UNNECESSARY / UNKNOWN`: whether the scenario's **required observation** depends on a registry-supplied value. `UNNECESSARY` means no governable value exists for the scenario, or a value exists but the outcome does not depend on it; it never says central governance has no value (see "Three questions" below) | REASONED INFERENCE |
| `exclusion_impact` | Governance capability lost by excluding the mapped family (central change control not gained, not enforcement lost); begins with `OBSERVATION=FIXED_CODE_INVARIANT` or `CONFIGURABLE_VALUE` for catalog rows | REASONED INFERENCE |
| `evidence_status` | `PASS_RECORDED / FAIL_RECORDED / BLOCKED / NOT_RUN / KNOWN_LIMIT_ASSERTED / COLLECTED_ONLY / NO_TEST / UNKNOWN` | recorded artifacts (Lane F) |
| `qualification_status` | What the controller artifacts say, quoted, never upgraded; always "not independently qualified" | SOURCE FACT |
| `known_limitations` | Known-limit tests and reasons; known-limit assertions are not protection | SOURCE FACT |
| `priority` | `P1-P4`, `OUT_OF_SCOPE` (rule in [04](04-prioritization-analysis.md) section 7) | REASONED INFERENCE |
| `priority_rationale` | One sentence generated from the rule | REASONED INFERENCE |

Severity (1-5) used by the priority rule is in [data/lane-E-outcomes.jsonl](data/lane-E-outcomes.jsonl).

## Three questions (derived view)

One column cannot carry three different questions, so [data/three-question-view.csv](data/three-question-view.csv) / [json](data/three-question-view.json) (built by `method/build_three_question_view.py`, read-only on the crosswalk, 696 rows) separates them: **A** does existing OCS code enforce the protection (`existing_protection`, `evidence_status` copied verbatim); **B** would central registry management improve governance of it (`q_b_governance_benefit`); **C** is registry management necessary for the V1 capability (`q_c_v1_necessity_basis`, `smallest_covering_profile`). No scenario is re-rated and `registry_dependency` keeps its meaning. Explanation and counts: [01 section 1a](01-executive-assessment.md).

## Rules enforced in the data and checked by [validation](07-source-and-evidence-manifest.md)

- NOT RUN is never recorded as PASS; all 656 Wiki rows are NOT RUN.
- `PASS_RECORDED` means named executed cases only. No canonical row is `ENFORCED_AND_EVIDENCED`.
- A passing known-limit test is `KNOWN_LIMIT_ASSERTED` and `KNOWN_GAP` evidence, never protection.
- Registry coverage is not security protection: a scenario can be `UNNECESSARY` for the registry while `IMPLEMENTED_NOT_QUALIFIED`, and `BENEFICIAL` while `KNOWN_GAP`.
- Every test ID resolves to a file and function in this repository; every coverage-map entry is preserved.
