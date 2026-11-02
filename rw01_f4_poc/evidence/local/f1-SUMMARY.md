# RW-01-F4-PoC battery summary

| suite | collected | passed | failed | errors | skipped |
|---|---|---|---|---|---|
| battery | 153 | 153 | 0 | 0 | 0 |
| registry_pr | 533 | 533 | 0 | 0 | 0 |
| replay_pr | 730 | 730 | 0 | 0 | 0 |
| replay_f4 | 1276 | 1275 | 0 | 0 | 1 |
| cp_pr | 83 | 83 | 0 | 0 | 0 |
| cp_repinned_6f600ab1 | 385 | 385 | 0 | 0 | 0 |
| cp_repinned_v8 | 305 | 305 | 0 | 0 | 0 |

| row | result | tests |
|---|---|---|
| N01 | PASS | 2 (2 pass, 0 fail) |
| N02 | PASS | 3 (3 pass, 0 fail) |
| N03 | PASS | 1 (1 pass, 0 fail) |
| N04 | PASS | 1 (1 pass, 0 fail) |
| N05 | PASS | 2 (2 pass, 0 fail) |
| N06 | PASS | 4 (4 pass, 0 fail) |
| N07 | PASS | 6 (6 pass, 0 fail) |
| N08 | PASS | 4 (4 pass, 0 fail) |
| N09 | PASS | 3 (3 pass, 0 fail) |
| N10 | PASS | 4 (4 pass, 0 fail) |
| N11 | PASS | 21 (21 pass, 0 fail) |
| N12 | PASS | 1 (1 pass, 0 fail) |
| N13 | PASS | 2 (2 pass, 0 fail) |
| N14 | PASS | 2 (2 pass, 0 fail) |
| N15 | PASS | 2 (2 pass, 0 fail) |
| N16 | PASS | 3 (3 pass, 0 fail) |
| N17 | PASS | 1 (1 pass, 0 fail) |
| N18 | PASS | 1 (1 pass, 0 fail) |
| N19 | PASS | 3 (3 pass, 0 fail) |
| N20 | PASS | 5 (5 pass, 0 fail) |
| N21 | PASS | 1 (1 pass, 0 fail) |
| N22 | PASS | 2 (2 pass, 0 fail) |
| N23 | PASS | 1 (1 pass, 0 fail) |
| N24 | PASS | 1 (1 pass, 0 fail) |
| N25 | PASS | 3 (3 pass, 0 fail) |
| N26 | PASS | 5 (5 pass, 0 fail) |
| N27 | PASS | 5 (5 pass, 0 fail) |
| N28 | PASS | 1 (1 pass, 0 fail) |
| F-1 | PASS | 20 (20 pass, 0 fail) |
| F1-A | PASS | 2 (2 pass, 0 fail) |
| F1-B | PASS | 1 (1 pass, 0 fail) |
| F1-BRIDGED | PASS | 1 (1 pass, 0 fail) |
| F1-C | PASS | 7 (7 pass, 0 fail) |
| F1-D | PASS | 2 (2 pass, 0 fail) |
| F1-E | PASS | 2 (2 pass, 0 fail) |
| F1-F | PASS | 1 (1 pass, 0 fail) |
| F1-G | PASS | 7 (7 pass, 0 fail) |
| PF | PASS | 7 (7 pass, 0 fail) |
| S | PASS | 13 (13 pass, 0 fail) |

REQUIRED ROWS: 39 required, 0 not PASS/missing
RESULT: PASS

## Re-pin supersession (closeout, 2026-11-02)
These f1-* files supersede the previous set (manifest f1-SHA256SUMS, sha256 b4b1b294f5588d96b71deeea834be1d2f33858559d97d62ec9a7b0e2c9b1fe84) ONLY because the source identities changed: Registry, Control Plane and Replay are now the merged squash commits
7de0ec9f8471c7a2ff630eb4035fa24d60b5e2eb / 8b97d32ff9a5aee640e61704637ff60dc57a84d9 / 6651abef2dfc0960b09907ed268db45e809ee814 (PRs #86 / #102 / #84). Their git trees
(6866eda49094a514cb4682da5670f9d9191868d5 / c8fa80276af211077ff8c84d34e5d1015200423b / 6f1153ce5f58749c6a9f1c96b7ad31dc92c32dde) are IDENTICAL to the former PR heads
52ff5f7d / cf7f5268 / ca94d6a8. No battery test logic changed (only source pins and comment text); per-suite and per-row counts are identical to the previous run.
Toolchain note: this run used the repository's hash-locked venv (pytest 8.3.5, cryptography 50.0.0, PyNaCl 1.6.2, pydantic 2.13.5, Python 3.13.18); the previous run used pytest 9.1.1 / cryptography 50.0.1. Results are unaffected.
Regressions: H = Replay F4 regression set (f1-regression-H-replay.raw.txt: 1275 passed, 1 skipped); I = Control Plane F4 tests against Registry pin 6f600ab1 (f1-regression-I-cp-f4.raw.txt: 267 passed).

## Closeout confirmations (all from the PASS rows above)
- Genuine CP-produced GovernedAgeWorkflow record (carry_selection_evidence=True, persisted and retrieved) imports into Replay under the F4 selector without grafting, re-sealing or inferred journal entries: F1-A (2/2 PASS; trust comes from the operator, never the record), with the F-1 producer tests (20/20 PASS).
- The REAL Registry RegistryEvidenceVerifierV2 (real adapter, not a stub) verifies the original signed selection evidence, and all eleven verifier layers pass on the genuine record: F1-A (2/2 PASS).
- Effective-policy binding matches on the positive path (F1-A) and a mismatching operator host-age expectation is refused registry_evidence_effective_digest_mismatch: F1-E (2/2 PASS).
- Essential negatives pass: F1-B forged signature (1), F1-C wrong scope (7 tests incl. other tenant / operator context), F1-D substituted record (2), F1-E (2), F1-F missing evidence (1), F1-G downgrade / closed absence (7) = 20 tests, all PASS.
- Markers: registry_authenticated False, claim A only, no authenticated-origin or production claim. OPERATIONAL TRUST NOT ESTABLISHED / PRODUCTION ADOPTION NOT AUTHORIZED.
- F1-BRIDGED remains BRIDGED (1/1 PASS); N01-N28 rows still use the BRIDGED record and are not integration evidence.
