# Contract-version matrix

Alpha decoupling, phase P4 of cogno-us/cognous-control-plane#38. Status: alpha; the execution-attempt lifecycle contract is a
draft (`0.1.0-draft`), is not frozen, and no release is declared.

## What changed

Until P4 a component entered a qualification run only if its checkout equalled a pinned sha (`require_pristine`). Pins therefore
doubled as the compatibility gate. For a boundary that is governed by an ODES contract the gate is now a **contract-version
matrix**; the shas stay as the recorded **tested revision**.

| | Before | Now (matrix-governed components) |
|---|---|---|
| Admission gate | checkout HEAD equals the pinned sha | the component's vendored `CONTRACT.json` conforms to the boundary |
| Pinned sha | the gate | recorded evidence: the revision that was tested, reported with `tested_revision_match` |
| Checkout state | must be pristine | must be pristine (unchanged) |

Components that carry no contract declaration, or that sit on no matrix boundary, keep the sha pin as their gate. The matrix says
which they are (`sha_pin_gate` in the matrix file).

## Files

- `process/v1-validation/v1-2026-10-16-a/contract-matrix.json`: contracts and versions known to the matrix (with the reference file
  digests of each version), the boundaries (`producer`, `consumer`, minimum conformance level per side) and the `sha_pin_gate`
  list.
- `suites/_contract_matrix.py`: the evaluation (stdlib only); used by the scenario helpers (`reference()`), the chain suite and
  the CLI.
- `tools/contract_matrix.py check --components DIR [--matrix FILE] [--json]`: print the matrix verdict for a components directory.
- `tests/test_contract_matrix.py`: unit tests of the rules below.
- Scenario evidence: `environment_identity()` includes `contract_matrix` (one row per boundary) and every `pins[name]` carries
  `gate`, `tested_revision` and `tested_revision_match`.

## Declaration

A component declares conformance by vendoring the contract with ODES `contracts/tools/vendor_contract.py`, which writes
`tests/contracts/<contract>/CONTRACT.json` (contract, version, odes commit, role, level, per-file sha256). Roles are `producer` and
`consumer`; levels are `S` (structure), `L` (structure and lifecycle rules) and `P` (structure, rules and a real producer run).

## Rules (per boundary)

1. Both sides declare the boundary's contract in their role, at a version the matrix knows.
2. Each side's level is at or above the boundary minimum.
3. While the contract is a draft, producer and consumer versions must be identical (no compatibility between drafts is assumed).
4. A declaration must carry the reference file digests of that version. The same `0.1.0-draft` string covered different content
   between ODES d1e17fa1 and a9db024c, so the version string alone is not accepted.
5. The vendored copy must be free of drift (files match the digests in its own `CONTRACT.json`).
6. Verdicts per component: `conforms`, `nonconforming` (refused: the run fails), `undeclared` (falls back to the sha pin).

A matrix row proves the paper trail only. Behaviour is shown by the producer and consumer conformance suites in the component
repositories and by the scenarios.

## Version-aware expectations

Where behaviour differs between contract versions the suites state one strict expectation per row, never "either". Example (N-1
rule of the lifecycle contract): a runtime that declares the lifecycle contract reports a lost acknowledgement that is then
observed applied as `reconciled` (observed partial: `partial`); an undeclared runtime reports `unknown`. The helper
`lost_ack_status()` in the scenario helpers and `_lifecycle_declared()` in the migrated runtime tests and the chain suite read the
declaration, so both rows stay strictly asserted.

## Removing pins at end-of-alpha (P5)

1. Freeze (or version-bump) the contract in ODES, with the owner's decision. Update the matrix `versions` digests and, if wanted,
   allow compatible version pairs in rule 3.
2. Move each remaining `sha_pin_gate` component onto a boundary: vendor the contract it implements, add the boundary row.
3. For every matrix-governed component, stop treating the profile sha as a requirement: delete the `require_pristine` fallback for
   it in `admit_components` and keep `tested_revision` as report-only evidence (it already is).
4. Remove the hard-coded peer revision tables in the components (Replay `importers.py`, pack `importer.py`, ODES `common.py`,
   exchange `gax_ref_runtime.py`) once their consumers check the declared contract instead of revision constants. This is a
   component change and needs its own PR per component; until then the tables stay and a new generation is added beside the old.
5. Run the full qualification (not the controller from this phase) and record the matrix rows in the run evidence.
