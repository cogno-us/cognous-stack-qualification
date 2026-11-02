# RW-01-F4-PoC end-to-end qualification battery

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

## What is claimed (and what is not)
- Claim A only: a Registry selection signature, carried through the Control Plane run record, is admitted by an OPERATOR-SUPPLIED verifier
  (`RegistryEvidenceVerifierV2`) at decision time. Claim B (the Control Plane decision is authenticated) is NOT made: markers keep
  `registry_authenticated: False`, `registry_origin: registry_origin_unverified`, `control_plane_decision_authenticated: False`.
- Synthetic Ed25519 keys (`bytes(range(32))` seeds) demonstrate the mechanism only. No trust root, no real keys, no production, adoption, Q7 or release claim.
- Decision-time verification only; no revocation or time-travel guarantee beyond what the tests state.
- NF-2 (documented, tested): Replay cannot distinguish an injected stub verifier from the real adapter; the consumer must construct the verifier.
- Some rows pin stated NON-detections (N08, N22); those tests assert the limitation, they do not claim detection.

## Findings the battery reports (FAIL rows are results, not hidden)
- F-1 (FAIL, intentional): a REAL `GovernedAgeWorkflow` run record is refused by every Replay profile at structural validation
  (`typed refusal profile: resolution journal missing`) because the real F4 decision has no `check_events` journal and no runtime-authority/0.1
  binding members. The gap exists with the carriage flag off and with the pre-existing profile, so it is not caused by the PoC. The remaining N-rows
  therefore use a BRIDGED record: the real CP bytes with the journal/binding members that Replay requires added and re-sealed; the tests cross-check
  that Replay's digest function reproduces the real CP effective-configuration digest and that the real bytes are carried verbatim.
- F-3: `tests/test_f5_class_age_governance.py` holds a seventh `bounded.py` pin beyond the six of the frozen contract (needs ratification).

## Known limitations
- The bridged record is not a CP-produced run record (see F-1). N-rows on it prove Replay and Registry behaviour, not an end-to-end CP-to-Replay flow.
- N26 (downstream pins) is checked by subprocess probes against the pinned ODES, Evidence Pack and Exchange sources.
- Three CP test files assert the r08-v8 Registry pin (a40fe755) and run against it; the others run against Registry 6f600ab1.
- Hosted-run artifacts return HTTP 403 on download, so raw output is also committed here and posted as PR comments with a SHA-256 manifest.
