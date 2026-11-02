# OCS-254-R1C targeted qualification - run record (developer observation on CANDIDATE heads)

Not Q7, not independent qualification, not certification; no release or production hold changes (CA16: no claim promotion). Remediation record: Issue #256.
Replay trusted match = CALLER-TRUSTED CONFIGURATION MATCH only, never Registry authentication. Structural-only mode remains UNQUALIFIED (leg E asserts the marker).

- Qualification PR (draft): https://github.com/cogno-us/cognous-stack-qualification/pull/262 ; code head 98bd74a58b3f350d41cc84f0cbf0d88015bdb8a3 (base main 7fc2fe602f460d0d4e01d6c3839d61e448a9010b)
- Run: https://github.com/cogno-us/cognous-stack-qualification/actions/runs/41390031155 (attempt 1, conclusion success), job 125099166146
- Artifact security-r1c-targeted-41390031155-1, GitHub-reported digest sha256:f34228e8799f8fecb4c69adeb79959ab493bf7a8c44cc6cbd79fd046d0ab6c46 (308201 bytes; not downloadable by the builder)
- r1c/tuple.json sha256 cc54da6aed97edb3966ccb7844c4065fd79698da666fe11cf7c4c782a192031d
- Annotations: check-run-annotations-job-125099166146.txt in this directory (the readable surface; per-test CSVs for legs A, B, H are only in the artifact).
- Checks on the code head: 9/9 completed success (r1c-targeted, validate x2, validate-and-build, CodeQL, 4 Analyze).

## Tuple (exact SHAs, HEAD and tree verified by the runner)
| component | commit | tree | label |
|---|---|---|---|
| Replay | 6f45e288ae37ec7e7712f9296760927d2d843bba | b2932497304ad589b1085d8b586ddc1fc1a2c583 | main merge (#82) |
| Exchange | 8fa8d3e77c4b24fefddb333795f9b6d3457dc556 | c73d2d5b43c6864dda99746c1978aa6f244ea788 | main merge (#64) |
| ODES | fe3c1416bca0c1ea1091f08ba570ecfc68e3bb2f | e6ed482de7e9a1eabc3f17641180764803bcbe0b | CANDIDATE PR #143 head, not a merge SHA |
| Evidence Pack | c461ae8c99ac96112f812cc4a9a3412fe136aed2 | 65181250a18b52d1e96b60d29c25527b4ff596f3 | CANDIDATE PR #66 head, not a merge SHA |
| Control Plane | b19c47ddd020409d24e52e70b11359c46265edbb | 039219b5aba7a157fff79781c716067fad7ed985 | parity leg only (fetched in CI with the default token; repo is public) |
| Replay P2 | 40012b8c174c6f25685bd5d9bc93ff46cc9a5842 | b68151a2f957a468d398a4bcb4b3936217eb449d | prerequisite of the Pack historical tests only |
Rebinding to the actual ODES/Pack merge SHAs is required after the operator merges them: edit r1c/tuple.json and re-run (not done here).

## Verdicts (from the job annotations)
| leg | what | PASS | FAIL | BLOCKED | skips |
|---|---|---|---|---|---|
| A1 | ODES current-generation e2e vs Replay 6f45e288 (180 tests + pin-constant check) | 181 | 0 | 0 | 0 |
| A2 | Pack current-generation e2e vs Replay 6f45e288 (148 + pin check) | 149 | 0 | 0 | 0 |
| B1 | ODES historical files (3 files) | 122 | 0 | 0 | 0 |
| B2 | Pack historical files (7 files, P2 Replay on path) | 172 | 0 | 0 | 0 |
| C1/C2 | new negative tests: ODES superseded d395e37c refused; Pack pinned gate refuses [d395e37c] | 1+1 | 0 | 0 | 0 |
| D | Replay tests/test_registry_governed_expected_configuration_digest.py | 71 | 0 | 0 | 0 |
| E | structural-only marker, no authenticated label | 1 | 0 | 0 | 0 |
| F | Exchange 35 replace-ref tests | 35 | 0 | 0 | 0 |
| G | Exchange source-identity/dirty-source refusal tests (13 functions) | 91 | 0 | 0 | 0 |
| H1 | ODES full suite (CI configuration) | 3266 | 0 | 0 | 8 SKIP_DOCUMENTED |
| H2 | Pack full suite minus test_cli | 427 | 0 | 0 | 82 SKIP_COVERED |
| P | CP b19c47dd vs Replay 6f45e288 FAMILY_TABLE parity | 3 | 0 | 0 | 0 |

Mutations (6/6 MUTATION_DETECTED; the required tests passed on the fixed tree and all failed on the mutant):
C-M1 ODES pin reverted to d395e37c (2 required, 0 other failing); C-M2 Pack pin reverted (1 required, 12 other failing); D-M1 expected-digest comparison bypassed (R1-N02, R1-N04; 10 other failing);
E-M1 structural marker replaced; F-M1 --no-replace-objects removed (7 other failing); P-M1 Replay FAMILY_TABLE class_age r08-v2 -> r08-v3 (2 of 3 parity tests fail).

## Limitations and disclosures
- Candidate heads only; results do not bind to ODES/Pack merge commits. Not a Q7 or release statement.
- Skips are not PASS: H1 has 8 SKIP_DOCUMENTED (1 needs rfc8785, not in the hash lock; 7 need the accepted Replay *installed*). Run locally (not in CI) against base ODES 77fd7a1c with Replay d395e37c installed, 4 of those 7 FAIL identically (Replay "unknown result cannot carry a validated applied/partial observation"), so this is pre-existing and not caused by 6f45e288; it means ODES example-package semantic tests have no executed coverage in CI at either Replay.
- H2 82 skips are the Pack current-generation e2e nodes, SKIP_COVERED by leg A2 (same node PASSed). Pack tests/test_cli.py (13 tests need an installed agep entry point) is excluded from H2 and not executed.
- Pack A2 needs full Replay history (superseded-head checkout tests); the Replay fetch for the tuple is by exact SHA with full reachable history, HEAD+tree verified.
- Leg C covers only the new negative tests plus the pin reverts; D relies on Replay's own PINNED vectors whose independence is asserted by the test author, not verified here. Parity covers one deterministic vector, not Registry-derived family digests.
- Annotation noise: on a green job, H1/H2 also carry ::error annotations that list skip rows (verdicts SKIP_*), not failures; the gate step passed.
- Per-test CSVs for A, B, H are artifact-only; annotations list every row only for legs of 100 rows or fewer (others: summary plus non-PASS rows).
- Existing workflows, PR #260, results/security-wiki-s3-20261031, results/security-wiki-r1b-20261101 and r1b/ were not touched.
