# Internal Milestone A — Q-A evaluator and freeze-preparation package (DRAFT)

**Status: DRAFT / UNFROZEN. Internal nonproduction preparation. Nothing here qualifies, certifies, releases or authorizes anything. The actual C1–C4 subject has NOT been assessed; no subject component was imported or executed to produce this package.**

Canonical protocol and decisions: [QR#271](https://github.com/cogno-us/cognous-stack-qualification/issues/271) · Architect decision [comment 6676452107](https://github.com/cogno-us/cognous-stack-qualification/issues/271#issuecomment-6676452107) · program [Hub#267](https://github.com/cogno-us/cognous-open-control-stack/issues/267) · internal acceptance [Hub#276](https://github.com/cogno-us/cognous-open-control-stack/issues/276) · formal qualification, still deferred and BLOCKED [Hub#279](https://github.com/cogno-us/cognous-open-control-stack/issues/279).

Ceiling if every gate is later met: **INTERNALLY ACCEPTED (NONPRODUCTION)**, only after an actually executed assessment and a separate Architect acceptance decision. This is not independent qualification: the oracle author, evaluator and preparation owner share builder lineage (see `freeze/roles.json`). Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`; project-local adoption **UNVERIFIED**.

## What this is

A small, stdlib-only, read-only **verdict engine** (`ia_eval/`) that judges an *observation bundle* (raw native outputs plus a hash index) against a **source-derived oracle** (`oracle/oracle.v1.json`). It does not run the subject. A future one-shot local run would produce the bundle; this package decides what that bundle means.

| Path | Purpose |
|---|---|
| `ia_eval/` | evaluator: `engine` (verdicts), `predicates` (strict operators), `oracle` (strict loader/validator), `guard` (no-effect event check), `identity` (pure-Python hashing), `freeze` (manifest/root), `cli` |
| `oracle/oracle.v1.json` | the oracle: 22 mandatory cases (PRE/CTL/RI/OBS), 2 INFO, 1 NA, exclusions; every observation carries a native `file:line` or an explicit limit/literal source |
| `docs/battery.md` | generated reading of the oracle: case table, source references, exclusions, coverage of the Architect's list |
| `tests/` | stub-only self-tests (EST-01…12), kill matrix, security regressions; `stubs.py` synthesises bundles from the oracle |
| `freeze/` | contract-comment snapshots (exact bytes), custody inventory, source/blob hashes, environment identity, L1–L27, roles, `freeze-manifest.json` (root commitment) |
| `results/selftest/` | raw self-test and kill-matrix output (outside the frozen file scope; hashed in the freeze meta) |

## Verdicts (docs/execution-contract.md vocabulary, persisted)

`PASS` · `FAIL` · `INCONCLUSIVE` · `NOT RUN` · `NOT APPLICABLE`. There is **no persisted BLOCKED**: a missing precondition is `NOT RUN` + `blocked_reason`; attempted-but-unevaluable is `INCONCLUSIVE` + `reason`. An observed violation stays `FAIL` even if other evidence is missing. Any mandatory `FAIL`, `INCONCLUSIVE` or `NOT RUN` prevents overall `PASS`; an empty or zero-executed run is never `PASS`. Oracle/bundle/freeze drift, unexpected case ids, out-of-scope driver events and evaluator errors all fail closed.

* **PRE / CTL / RI** gate the Q-A claim (`claim_basis`).
* **OBS** (QA-09, QA-11, QA-17, QA-26, QA-OBS-EXACT) pins what the pinned subject *does*, e.g. "Replay accepts a held record whose tenant was swapped". A match is reported as `OBSERVED_AS_FROZEN` with `security_property_validated=false`; a deviation is `FAIL` (frozen-subject drift or oracle error — never re-baselined silently). OBS results are excluded from the claim gate and are never worded as a security PASS.
* **INFO** (N3-GATE, QA-21) stays `NOT RUN`; **NA** (QA-14) is `NOT APPLICABLE` with a source-backed reason. Neither is mandatory.

## Observation bundle contract (what a future driver must produce)

`bundle.json` (`ia-observation-bundle/1`): `raw_index` {relpath → sha256}, `cases` {id → `{executed, boundaries, adverse_notes}`}, `driver_events`, and (ignored, listed only) `orchestrator_status`. A boundary is `{outcome, entrypoint, raw | exception_raw, inputs}`: a returned native value is serialised into a hash-indexed raw JSON file; a native refusal is a raw JSON `{"type","message"}`. **The outcome is derived from hash-verified evidence kind, never from the label.** Orchestrator labels (`REFUSED_NATIVE`, `chain_verdict`, `all_ok`, `retains_upstream_refusal`, …) are rejected as pointer segments at oracle load (L25). `bundle.json` must be hashed by someone other than the driver and that hash supplied to `evaluate`.

## Run (evaluator only; no subject)

```bash
cd internal_a
PYTHONDONTWRITEBYTECODE=1 python3 -I -B -m pytest -p no:cacheprovider tests          # stub-only self-tests
python3 -I -B tests/selftest_matrix.py results/selftest                                 # kill matrix + raw results
python3 -I -B run_ia.py freeze-verify --freeze-root <root>                             # file-set equals manifest
python3 -I -B run_ia.py evaluate --oracle oracle/oracle.v1.json --expect-oracle-sha256 <h> \
    --bundle <dir> --expect-bundle-sha256 <h> --freeze-root <root> --out <new-report.json>   # exit 0 only on PASS
```

Always `-I -B`; `freeze-verify` also fails if any `.pyc` exists.

## Residual trust and known gaps (honest)

1. **No native-calling driver is included.** The evaluator never imports a component. The future one-shot local runner (D6) must still be demonstrated to be repeatable, to reach the pinned native components rather than developer status fields, and to retain complete raw output. Until then execution is not authorized and the readiness is for the *freeze*, not for running.
2. The driver is trusted for **call fidelity**, **completeness of `driver_events`** and the `executed` flag; hashes prove only that a bundle is consistent with its own index. The evaluator cannot detect a lying driver.
3. QA-22 needs a clean git checkout of Replay (a `git archive` extract has no VCS revision, so the Pack refuses even the control). QA-S1/S2 trust the driver's raw `git rev-parse` capture and evaluator hashing of files on disk.
3b. Identity captures (QA-S1/S2/S3/QA-E1) should be produced with `python3 -I -B run_ia.py collect-identity` by the evaluator owner on the extracted trees, not by the driver; QA-09 recomputes the raw-dict commitment itself (`commitment_of`), but `am_digest` and every other native output are driver-reported serialisations of native objects.
4. Oracle `source` annotations are documentation: the engine does not verify them against the repositories; integrity rests on the pinned oracle hash. Observations marked `INFERRED` in `source.confidence` have an expectation not fully traced in source and are the first suspects if a future run deviates.
5. Hash commitments are self-computed. GitHub comments are mutable and not an independent anchor (Architect D8); the root commitment must additionally be retained **outside the builder's workspace**.
6. Original C1–C4 evidence is **not in independent custody** (`freeze/custody-inventory.json`): artifacts expire from 2027-02-03.
7. Q-B, Q-C, Q-D are out of scope. Hub #280 remains OPEN. L1–L27 (`freeze/limits-L1-L27.json`), the provisional unqualified Pack↔Replay development pin (L16), held-record non-binding (L22) and the original negative findings remain intact.

## Unsupported claims (must not be inferred from this package or any future PASS of it)

Independent qualification or certification; production readiness or authorization; actual destination execution; absence of effect beyond decide()-only observation; authentic authority, freshness, custody or signature; general Manifest/Control Plane interoperability (Hub #280); tenant/proposal/action binding of held records; complete reconstruction; qualification of the provisional Pack↔Replay profile; constitutional adoption; Milestone B / Hub #279.

## Evidence-retention specification (for the future run)

Retain, hashed and listed in the evidence record: the frozen package and root commitment; oracle JSON; evaluator source; the exact bundle (`bundle.json` + every raw file, original bytes, including all adverse evidence and exceptions); the evaluator report; driver transcript; environment identity (OS image, Python build, pip/git versions, installed distributions); the extracted-source identity records; and the self-test results. Reports are written create-only. Nothing is rerun to replace original bytes. Copies belong in access-controlled write-once storage outside the author-controlled GitHub account (D7); none is established here.

## Freeze order (not executed here)

1. Reviewed package merged/approved → 2. `freeze-build` (root commitment; meta lists every input hash incl. self-test results) → 3. commitment posted in the tracker **and** retained outside the builder workspace → 4. Architect's separate freeze approval → 5. separate one-shot execution authorization. Any post-commit alteration blocks the candidate pending a separately approved successor freeze; the predecessor is preserved.
