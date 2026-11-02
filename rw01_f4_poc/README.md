# RW-01-F4-PoC end-to-end qualification battery

> **OPERATIONAL TRUST NOT ESTABLISHED / PRODUCTION ADOPTION NOT AUTHORIZED.** This is developer/qualification evidence of CLAIM A only (a Registry selection
> signature admitted by an operator-supplied verifier, synthetic keys, decision time). Claim B (Control Plane decision authenticated) and Registry origin are NOT
> established. The hosted check now FAILS if any test fails or any required row (N01-N28, F-1, F1-A..F1-G, F1-BRIDGED, PF, S) is not PASS; there is no tolerated FAIL row.
>
> **F-1 recovery.** The former intentional F-1 FAIL (a real `GovernedAgeWorkflow` record refused at structural validation, "resolution journal missing") is replaced by the
> passing REAL integration rows **F1-A .. F1-G** in `battery/test_f1_integrated_rows.py`: a genuine persisted and retrieved CP record imports into the real Replay
> (`6651abef`, merged PR #84, tree identical to former PR head `ca94d6a8`; explicit selector `registry-authenticated-selection-f4-governed/0.1`) with the real `RegistryEvidenceVerifierV2` and operator-supplied trust, with no
> grafting, no re-sealing and no edit of the retrieved record; each negative is paired with the control positive. The old BRIDGED rows remain COMPONENT evidence only.
> Limits are listed under "Known limitations". Builder-tested developer evidence, not independent qualification.

Register: cogno-us/cognous-open-control-stack#259 (RW-01), parent #254. Constitution pin 1c2e920f4e58e07a52e8e2408a506cf7dbc1292b.
Gate 0: https://github.com/cogno-us/cognous-open-control-stack/issues/259#issuecomment-6577903097

This directory adds an additive, read-only battery that drives the REAL pinned Registry (PR #86), Control Plane (PR #102) and Replay (PR #84)
code together, and checks rows N01-N28 at the real boundary (typed refusal code, refusing layer, no admitted marker or bundle). Nothing here
modifies any existing file or any other repository.

## Layout
- `sources.json` - the ONE manifest of every pinned source (repo, 40-hex SHA, tree). Nothing else in this directory restates a SHA, except named
  historical constants that the tests deliberately compare against (e.g. the old `bounded.py` hash).
- `fetch_sources.sh <dest>` - fetches each source by exact SHA (`git fetch --depth 1 <sha>`) and verifies HEAD and tree.
- `run_battery.py --src <dest> --out <dir>` - runs the suites as separate `pytest -rA --junitxml` processes, then writes `SUMMARY.md`,
  `summary.json`, `rows.json` (N-row to nodeid to boundary mapping), `environment.json` and `SHA256SUMS`.
- `battery/` - the tests (`test_00_sources`, `test_e2e_rows`, `test_e2e_rows_b`, `test_compat_rows`, `test_cp_protected_files`, `test_downstream_n26`)
  and `harness.py`. `evidence/` - committed raw outputs of the local run and the PR-comment manifest.

Run locally: `bash fetch_sources.sh /dev/shm/src && python run_battery.py --src /dev/shm/src --out /dev/shm/out`
(needs hash-locked PyNaCl, pydantic, pytest, jsonschema; see the workflow). CI: `.github/workflows/rw01-f4-poc-e2e.yml`.

## REAL versus BRIDGED evidence (73 of 153 battery tests still run on the bridged record; the integrated CP-to-Replay rows are F1-A..F1-G)
Evidence kinds (the `evidence` field in `rows.json` of a run): REAL 50, BRIDGED 73 (+1 BRIDGED,SUBPROCESS), SUBPROCESS 9, STATIC 20 (153 battery tests).
- What is REAL in every BRIDGED test: the Registry signature verification (real PyNaCl Ed25519, synthetic keys), the real `RegistryEvidenceVerifierV2`
  adapter, the bytes the real Control Plane `GovernedAgeWorkflow` carries as selection evidence, and the real CP `effective_configuration`
  (Replay's own digest function reproduces the real CP digest).
- What is BRIDGED: the surrounding run-record members (e.g. the resolution journal / `check_events` and runtime-authority binding members) that Replay's
  structural validation requires and the real F4 decision does not produce. They are grafted from Replay's own fixture and the record is re-sealed.
  BRIDGED tests therefore prove Registry, adapter and Replay behaviour on real carried bytes, NOT an end-to-end CP -> Replay flow.
- N19 does NOT traverse Replay with the real adapter: a non-ASCII statement tenant breaks the fixture bridge. N19 is REAL at the CP -> real-adapter
  boundary (carriage, positive in both text encodings, and the ensure_ascii=False negative). Replay-side and adapter/core coverage of non-ASCII is in
  the Registry PR #86 adapter/core tests (`registry_pr` suite).

| row | tests by evidence kind |
|---|---|
| N01 | 1 BRIDGED, 1 REAL |
| N02 | 2 BRIDGED, 1 REAL |
| N03 | 1 BRIDGED |
| N04 | 1 BRIDGED |
| N05 | 2 BRIDGED |
| N06 | 4 BRIDGED |
| N07 | 6 BRIDGED |
| N08 | 4 BRIDGED |
| N09 | 3 BRIDGED |
| N10 | 4 BRIDGED |
| N11 | 21 BRIDGED |
| N12 | 1 BRIDGED |
| N13 | 1 BRIDGED, 1 REAL |
| N14 | 2 BRIDGED |
| N15 | 2 BRIDGED |
| N16 | 2 BRIDGED, 1 REAL |
| N17 | 1 BRIDGED |
| N18 | 1 BRIDGED |
| N19 | 3 REAL |
| N20 | 5 BRIDGED |
| N21 | 1 BRIDGED |
| N22 | 2 BRIDGED |
| N23 | 1 SUBPROCESS |
| N24 | 1 SUBPROCESS |
| N25 | 3 SUBPROCESS |
| N26 | 1 BRIDGED,SUBPROCESS, 4 SUBPROCESS |
| N27 | 5 BRIDGED |
| N28 | 1 BRIDGED |
| F-1 | 20 REAL |
| F1-A | 2 REAL |
| F1-B | 1 REAL |
| F1-BRIDGED | 1 REAL |
| F1-C | 7 REAL |
| F1-D | 2 REAL |
| F1-E | 2 REAL |
| F1-F | 1 REAL |
| F1-G | 7 REAL |
| PF | 7 STATIC |
| S | 13 STATIC |

## Unrelated, pre-existing repository failure
The repository's own `Catalog validation` workflow fails on this PR AND on a rerun of main at c9004a6d
(`tests/test_mvp_acceptance_gate.py`, planted-pyc test: `AttributeError: module 'importlib._bootstrap_external' has no attribute '_RAW_MAGIC_NUMBER'`,
newer Python 3.13.x on the runner). Environmental, unrelated to this change; main's runs from earlier on 2026-11-02 passed.

## What is claimed (and what is not)
- Claim A only: a Registry selection signature, carried through the Control Plane run record, is admitted by an OPERATOR-SUPPLIED verifier
  (`RegistryEvidenceVerifierV2`) at decision time. Claim B (the Control Plane decision is authenticated) is NOT made: markers keep
  `registry_authenticated: False`, `registry_origin: registry_origin_unverified`, `control_plane_decision_authenticated: False`.
- Synthetic Ed25519 keys (`bytes(range(32))` seeds) demonstrate the mechanism only. No trust root, no real keys, no production, adoption, Q7 or release claim.
- Decision-time verification only; no revocation or time-travel guarantee beyond what the tests state.
- NF-2 (documented, tested): Replay cannot distinguish an injected stub verifier from the real adapter; the consumer must construct the verifier.
- Some rows pin stated NON-detections (N08, N22); those tests assert the limitation, they do not claim detection.

## Findings the battery reports (FAIL rows are results, not hidden)
- F-1 (RESOLVED for the explicit F4 path; was an intentional FAIL): a REAL `GovernedAgeWorkflow` run record is still refused by every PRE-EXISTING Replay profile at
  structural validation (`typed refusal profile: resolution journal missing`) because the real F4 decision has no `check_events` journal and no runtime-authority/0.1
  binding members; the remaining F-1 rows pin exactly that (old selectors never import it). It is imported only through the new explicit selector
  `registry-authenticated-selection-f4-governed/0.1` (Replay 6651abef = merged PR #84; tree identical to former head ca94d6a8), rows F1-A..F1-G. The N01-N28 rows still use a BRIDGED record (the real CP bytes with the
  journal/binding members that the old profiles require added and re-sealed); they are component evidence, not CP-to-Replay integration.
- F-3: `tests/test_f5_class_age_governance.py` holds a seventh `bounded.py` pin beyond the six of the frozen contract (needs ratification).

## Known limitations
- The bridged record is not a CP-produced run record (see F-1). N-rows on it prove Replay and Registry behaviour, not an end-to-end CP-to-Replay flow; the integrated
  flow is F1-A..F1-G only.
- F1-D(ii) limit: the selection signature binds no run id or decision id. Evidence of a second genuine CP run with byte-identical signed material is indistinguishable
  and is admitted (asserted, not hidden); evidence with a different signed bound or another tenant is refused (effective-digest cross-check / real adapter).
- Replay's operator trust object has no "expected effective-policy digest" field: the operator supplies host ages and Replay compares the verdict's digest with the record's
  `f4_ages` row (row F1-E). The Replay F4 shape check is closed-absence only (journal and runtime-authority members must be absent); the CP decision fields remain unsigned
  (claim B not made); `reverify_retained_registry_evidence` does not support the F4 selector; the verifier cannot be distinguished from a stub by Replay (NF-2).
- Hosted pins: Replay `6651abef` (merged PR #84; tree identical to former head `ca94d6a8`), Control Plane `8b97d32f` (merged PR #102; tree identical to former head `cf7f5268` = 6648ae2c + CI-only commit; the protected-file crosswalk row PF adds the one workflow file
  `.github/workflows/tests.yml` to the changed set), Registry `7de0ec9f` (merged PR #86; tree identical to former head `52ff5f7d`). Pin change only: the source trees are unchanged.
- N26 (downstream pins) is checked by subprocess probes against the pinned ODES, Evidence Pack and Exchange sources.
- Three CP test files assert the r08-v8 Registry pin (a40fe755) and run against it; the others run against Registry 6f600ab1.
- Hosted-run artifacts return HTTP 403 on download, so raw output is also committed here and posted as PR comments with a SHA-256 manifest.
