# 06 Recommended ownership and integration

**Status: documentation-only analysis. Non-authorizing. Draft for Architect review. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.**

Nothing here authorizes a migration, approves a pin, selects or activates a record, or changes a qualification verdict. Implementation is not authorized. Roles follow the Constitution (CA04, CA08, CA20, CA23) and the P1 plan; they are recommendations for the Architect, not designations. Assigning a title does not manufacture independence.

## 1. Ownership

| Asset | Recommended owner | Why |
|---|---|---|
| Registry code, builder tests, `FakeVerifier`, the gate-matrix source of record | Registry builder (`cognous-ocs-registry`) | Source of the subject; its tests stay `BUILDER_TESTED` |
| Runtime narrowing adapter, Control Plane age-bound and claim-carried changes | Runtime and Control Plane component owners | Each owns its enforcement files; Runtime `engine/safe_executor.py` is never modified |
| Gate-binding table (N1), registry-subject workflow (N2), suite directory and import map (N3) | **This repository's owner** | They are qualification infrastructure and must stay out of implementation repositories |
| Oracle expectations for QG-01..QG-14 | **Independent oracle author**, blind to the candidate | Constitution CA04: expectations are recorded before candidate acceptance and are not fitted to behaviour. Must not have authored or reviewed `registry_successor`, `s05_oracle.py` or the R08 tests, nor read them before freeze |
| Execution at exact pins and the verdict | **Independent qualification lead**, **not designated** | GAP-G4-13. Not the builder, Architect, Copilot or a dependent worker |
| Evidence review | A party separate from author, builder and runner, else recorded "not performed" | Operator statement: "no second llm for now" |
| Final adjudication | Operator | Per the status record |
| Known-limit declarations (11 Runtime tests) | Runtime owner | GAP-G4-07; before the exact-pin run |
| ISSBench | ISSBench owner; **no OCS role** | Its own documents keep oracle custody there and disclaim OCS infrastructure |

Until a lead is designated, every S5 output reads "builder-side inspection; Tier 1 not qualified" and counts toward neither V1-M8, CA04 nor CA23. If none is designated by S5 exit the candidate reads "OCS-only V1: NOT INDEPENDENTLY QUALIFIED". This package does not soften that wording.

## 2. Integration with what exists

1. **Pins.** All subject revisions are workflow inputs. Evidence records both git identities, as the delegated workflows already do (`install_suite.py` writes the relocation artifact). Nothing is pinned by branch name.
2. **Order.** N1 before any implementation result is shown to the oracle author (EXT-S5-1). Expectations and the spec digest are frozen in a dated commit before execution; amendments are dated and never made to obtain a pass. A mismatch against a resolved expectation is FAIL; an unresolved mapping is BLOCKED.
3. **Existing workflows.** Dispatch the existing delegated workflows against a registry-bearing candidate SHA where they already fit (`cognous-execution-runtime--worker21-authority-effect`, `--durable-refusal`, `--python-safety`, the OCS `accepted-authority-effect`, `paired-request-enforcement`, `release-integrity`, and the `recovery-inspection` and `typed-refusal` families for negative evidence). No edit is needed. Their baseline pins differ per workflow and are unmanaged across the 49 files; only `v1-validation` has a test tying its literals to a manifest.
4. **Results.** New results go in a new folder with the existing layout (REPORT, `SHA256SUMS`, raw logs, junit, collected-test lists). Failures, skips, XFAIL and NOT RUN are retained. Nothing under `results/` is edited; corrections are linked successors. Note immutability outside `results/workflows` is convention, not enforced.
5. **Reporting.** Keep qualification status beside evidence status. Report QG-02 as inactive. Do not aggregate native, integrated and live results into one number.
6. **Gate vocabulary.** Always write `QG-nn` in full when meaning the plan's gates. "Gate" alone is ambiguous here (OCS-1/2/3, V1-M/R/C, MVP G-00..G-15).

## 3. One interpretation question for the Architect

The requirement "do not introduce cross-repository dependencies" can be read two ways.

- **Reading A (recommended).** It bars code, package or tooling dependencies between repositories, and any dependence on ISSBench. Checking a *subject under test* out at a pinned revision, as this repository already does for seven owner repositories through the delegated workflows (and for the Control Plane in the MVP chain), is the qualification model, not a dependency. On this reading N2 checking out `cognous-ocs-registry` at an input revision is allowed; N1 and N3 import nothing from outside this repository.
- **Reading B.** It also bars checking out the registry repository at all. The P1 plan's host driver and `p1-config-extraction` workflow could then not run, and the gates could only be exercised through a copy of the registry placed here, which would be a worse duplication.

Nothing in this package introduces either kind of dependency on ISSBench, under either reading. I recommend Reading A and ask for confirmation before N2 is built. This is the only point in the package that needs an Architect decision; it is not a material change to OCS architecture or product scope. **REASONED INFERENCE**

## 4. Consolidation, if ever wanted

Not for V1. If the Architect later wants it: put the machine-readable gate table in one place (N1 already does), publish a mapping table before touching the five status vocabularies, and treat `_index_signing.py` and the canonical-JSON copies as an intra-repository clean-up with a digest-equivalence check per call site. Any cross-repository sharing would need its own decision.
