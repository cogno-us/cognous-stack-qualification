# Original-evidence applicability crosswalk (CA07)
Original run: A-main4 (hub bundle `F3-qualification-evidence-ed31764.tar.gz`, sha256 1d07a704…); row numbers are 1-based lines of `runs/A-main4/f3a_evidence.jsonl`. Facts verified by this session or its read-only worker (report in `workers/evidence.md`).
| Fact | Result |
|---|---|
| Executed Control Plane tree | 1e7a7555eb3a956fcd2db21d3eb944169d0f7783 == git tree of 739efe7 (verified) |
| Bundle / protocol / verdict hashes | match recorded (SHA256SUMS OK) |
| MANIFEST-final / MANIFEST-freeze | 168/168 and 40/40 OK |
| Module/schema hashes in C-compat probes | tie to git blobs at 739efe7 and b7eb11a |
| Harness AMEND chain | reproduces harness-final byte-for-byte (sha256 a5147412…, identical to copy used as shared fixture library here) |
| 8616d5f vs 739efe7 | one src file, docstring only; AST equal excluding the module docstring; other trees identical |
| Environment | original: Python 3.11.18, pydantic 2.14.2, PyNaCl 1.6.2, pytest 9.2.0 (partly after-the-fact); this session identical; Registry pin a40fe755 |
| Provenance weaknesses (disclosed) | tree id recorded only pre-run; run header lacks pytest/pydantic/PyNaCl versions; PIN_DURABLE_REFUSAL_REQUIRED not logged (inferred default 1); no executed-harness hash at run time |
| Case | Rows | Decision | Why |
|---|---|---|---|
| A19 execute (22 members) | 520-798 (132 checks) | REUSE | execute path source identical; also instrument-validity control in G1 |
| A19 pin-export (22) | 526-805 | REUSE for (i); GAP for (ii) | raw rows lack store diff / journal capture; G1 added |
| A06 pin sub-case | 221-224 | REUSE for (i); GAP for (ii) | no raw outcome row; G3 added |
| A19 claim | 806-814 (3/22) | GAP | G2 added |
| A09 + C-compat | 235-264 | REUSE at 739efe7; G6 delta at 8616d5f | one module hash changed (docstring) |
| A24 | 863-879 | NOT REUSED | docs changed; rerun at 8616d5f |
| All other CHECK_PASS cases, F3-B | — | NOT RERUN | source/contract/behavior unchanged; F3-B not reopened |
