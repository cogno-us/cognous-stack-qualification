# Verifier mutation harness (design stage S5, family T)

Opt-in, report-only measurement of the independent verifier (`cogno-us/cognous-open-control-stack-verifier`, command `cognous-verify`) against damaged traces. Design: `docs/engineering/INDEPENDENT-VERIFIER-DESIGN.md` in `cogno-us/open-decision-evidence-standard` (sections 4.1 to 4.5). Report shape: the ODES `verification-report` draft (`mutation_report`), vendored unmodified in `contract/verification-report` (see its `CONTRACT.json`).

It selects no component, changes no scenario verdict, profile or pin, runs no qualification controller and no `tools/v1_validation.py` mode, and is not a required check. Standard library only. Family S (control-removal) counts are context only and are never produced here; `--family-s FILE` can carry them, with their own denominators.

## Pieces

| File | Role |
|---|---|
| `corpus/clean/` | frozen snapshot of 18 clean traces from the real control plane: 10 from its own test helpers (fixed clock, journal and default modes) and 8 from `acp run` (2 declared examples, 6 seeded variants). 12 authorized, 6 held. Manifest records the control plane revision, reason registry digest and every file digest |
| `verifier_mutation/operators.py` | 77 deterministic, seeded operator variants over the traces, each tagged with one design category (34 categories; `Q` is reported as n/a, `L1` is the S6 join step and has no trace operator) |
| `operators.json` | the frozen operator set: catalogue, seed, draws, intended codes and the digests of the implementation files. `operator-set --check` and a test fail when it differs from the code; `report` refuses to run unless it matches. Commit it before any verifier run |
| `seed-map.json` | which category each ODES invalid fixture seeds; unmapped fixtures are counted as unclassified, never dropped |
| `verifier_mutation/runner.py` | runs the verifier as an external process per trace; reads its stdout as an ODES report, validates it, derives reject / abstain / accept; crash, time-out, non-JSON and refused reports are `error`, never detection |
| `verifier_mutation/report.py` | tallies and emits the mutation report; validated with the ODES validator before it is written |
| `stubs/stub_verifier.py` | stub verifiers that prove the harness (accept all, reject all, abstain, crash, garbage, invalid, slow, partial). Not verifiers |
| `tests/test_verifier_mutation_harness.py` | the proof (runs in the default catalog-validation job; no verifier needed) |

## Run

```
# harness proof with stubs (default CI does this)
python -m unittest tests.test_verifier_mutation_harness

# measurement (workflow verifier-mutation-report.yml does the same; dispatch only)
PYTHONPATH=suites/verifier-mutation python -m verifier_mutation report \
  --odes <ODES checkout> --out mutation-report.json --jobs 4 \
  --verifier-cmd 'cognous-verify {run_record} [--proposal {proposal_export}] [--manifest {manifest}] [--ledger {destination_ledger}] --json'
```

A `[...]` group in the command is passed only when the trace has that file; seed documents carry a run record only. `--strict` exits 3 when a harness flag is raised; by default a flag is an advisory in the report and the run exits 0.

Regenerate the clean corpus (opt-in; needs the control plane virtualenv with `cryptography`): `python -m verifier_mutation capture --control-plane <checkout>`. Capture is not byte-repeatable (the stack mints identifiers), so the corpus digest, not the script, identifies the corpus.

## Counting rules

- Corpora are never pooled: `t-seed-odes` (ODES fixtures, regression only: `k` of `n` seeds refused with the intended code, no detection, no metric impact), `t-generated` (operator mutants of the clean traces: detection with any code and with the intended code, false acceptance, abstain, error on separate lines, metric impact conditioned on false acceptance), and per clean corpus the clean-trace false rejection. Per-scenario tables repeat the generated rows over each scenario's own slots (one trace per scenario here).
- A slot is one (trace, operator variant, draw). `n_na`: precondition not met. `n_noop`: files identical to the clean trace (a structural operator also when canonically equal). Identical mutants of one trace and operator are dropped and counted in the harness extension. `n_eff = n_gen - n_noop - n_na`. Verdicts sum to `n_eff`.
- Divergence from the design text: noop is decided on files, not on a lenient re-parse, because a duplicate member or `NaN` reads as the clean document under Python's parser yet is the damage being measured.
- Clean false rejection per category counts the clean traces on which that category's operators produced an effective mutant; benign (B) counts benign mutants. For the ODES valid fixtures the row covers the valid fixtures of the contracts that category's seeds come from, so rows repeat the same fixtures.
- Metric impact measures are derived by this harness from the files (the verifier does not expose them); unavailable (counted aside) for an accepted mutant Python cannot parse.
- Intended codes are frozen with the operator set. A different but correct verifier code counts in `any_code` only. Working names are used where no ODES contract or verifier code existed when the set was frozen.
- J3 is realized as completed-to-interrupted or completed-event-dropped: no real clean trace holds an interrupted check to rewrite.
- Expected-accept categories (B, F, R6) are reported with the same columns; an accept there is the expected outcome, not a failure.
- Held-out: the operator set and seed are fixed in this repository before the verifier is run; the clean bases are the same scenario family the verifier's own tests use, so only the mutants are held out.
- Flags (`no_detection_anywhere`, `accepts_every_mutant`, `abstains_on_every_mutant`, `rejects_every_clean_trace`, `rejects_every_valid_seed`, `errors_present`) say the verifier is not measuring anything. They gate nothing.

Nothing here claims a decision is correct or that the verifier is correct; figures are counts over the stated corpora and say nothing outside them.
