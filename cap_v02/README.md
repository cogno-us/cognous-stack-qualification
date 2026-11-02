# CAP v0.1 gate G2 - independent qualification tests

Independent tests of the Control Plane G2 head (`registry_authority_state`, profile `state.backend = "file-g2"`, store `ocs-cap-freshness-state/1`), written from the frozen contract
(cogno-us/cognous-open-control-stack#259, comment 6589180377, section 5, and the sprint brief), **not** from the implementer's tests (which were deliberately not read).

Real components: Control Plane `GovernedAgeWorkflow` built by the factory, Registry `verify_f4_selection_v2` (11 layers) with the exact `Ed25519Verifier` (PyNaCl), the unchanged Registry
conformance kit (`registry_conformance.highwater`), **a real persisted state file with its `.lock` sibling**, and **real separate Python processes** (`battery/child_worker.py`, `python -I`).
Keys are SYNTHETIC (mechanism only). Spies wrap the Registry core, the signature check and the state writer in place and delegate, to prove whether the verifier was reached, which layer
refused, and that no write happened on a refusal. On refusals the whole authorization directory (configuration, snapshot, store, ledger) is compared byte-for-byte before and after.

## Claim scope (read this first)

* **Synthetic restart-safe only.** A fresh process, given the same configuration and the persisted store, keeps the epoch / snapshot / revocation floors.
* **Operational trust is NOT established.** Operational mode still refuses `authority_config_unprovisioned`; nothing here tests or claims issuer identity, key custody, adoption or release.
* **Local-integrity limit.** The store digest detects accidental or partial damage. It does **not** detect a privileged actor who replaces the WHOLE store (or the directory) with an older valid
  copy, hand-creates an empty store, or deletes store and ledger and replays a still-valid bootstrap. G2.15 / G2.8.q / G2.13 pin these as *not detected*; an independently anchored monotonic
  store is G3 (`anchor_reference`). G3 is not tested.
* Other documented limits pinned as limits (not defects): config edit to `none-g1` without `expected_config_digest`; a revocation-only newer pin is not recorded until a selection is admitted;
  no clock high-water; stray `*.tmp` after a kill; 8 MiB store cap (fails closed, not exercised).

## Rows

| Row | File | What |
|---|---|---|
| S | battery/test_00_sources.py | pinned HEADs, modules imported from the pinned checkouts (also in a child process), locked PyNaCl, claim-scope labels, G1 label change finding |
| T | battery/test_01_tripwire.py | CP changed-file set vs merged G1 main 2ebc3e66 is exactly 6 files; bounded.py untouched; Registry/Replay clean at pins; SHA-256 manifest |
| G2.1 | battery/test_g2_01_state_and_freshness.py | valid selection persisted (envelope, digests, parent chain, one write), guard repeat, stored snapshot passed as last_accepted |
| G2.2 | same | legitimate renewal (signed supersedes incl. decision_ref), chains, gaps, renewed bound used by the real workflow, illegitimate advancement refused |
| G2.3 | same | lower / conflicting epoch refused by the state (Registry admitted it), via direct source and factory; snapshot min_epochs floor |
| G2.4 | same | snapshot rotation is not a reset; older snapshot refused against the stored one (also in a fresh process) |
| G2.5 | same | expired / not-yet-effective / revoked selection or key refused; persisted grow-only revocation; selection_conflict |
| G2.6 | battery/test_g2_02_restart.py | fresh-process restart demonstration (5 PIDs), parent sees only the file, snapshot floor survives |
| G2.7 | battery/test_g2_03_missing_corrupt.py | missing / deleted / garbage / bit-flipped / truncated / oversized / re-sealed-tampered / foreign store: typed, never recreated, verifier not reached |
| G2.8 | battery/test_g2_04_bootstrap.py | cold start: TTL, namespace, authority digest, mode, floor-seeding members, consumed, existing store, concurrent and crashed bootstrap |
| G2.9 | battery/test_g2_05_scope_tenant.py | another configuration (tenant, consumer, operation, ... ) over the same store refused `state_authority_mismatch`; independent authority_digest |
| G2.10 | battery/test_g2_06_downgrade_bypass_forgery.py | unknown/replaced backend, operational cannot open a transaction, none-g1 explicit and stateless, every path enforces, factory kwargs, host snapshot |
| G2.11 | same | untrusted evidence claiming epoch 99 cannot advance state (nine forgeries), no refusal ever calls the writer |
| G2.12 | same | review-fix behaviours: forged / unadmitted verdict cannot be committed, signing key recorded, lock identity, clock read after the lock |
| G2.13 | same | documented limits pinned as limits |
| G2.14 | battery/test_g2_07_atomicity_concurrency.py | 12-process races (exactly one variant wins), crash before replace, SIGKILLed lock holder, lock held (5 s default), write-failure injection, torn-read check |
| G2.15 | battery/test_g2_08_limit_and_g1_regression.py | HONEST LIMIT: whole-store rollback to an older valid copy NOT detected |
| G2.16 | same | G1 regression: unmodified cap_v01 N1-N4/P1 behavioural tests against the G2 head; none-g1 flows unchanged |

## G1 regression

`test_g1_battery_behavioural_tests_pass_on_the_g2_head` runs, as a separate pytest process from `cap_v01/`, `battery/test_n{1,2,3,4}_*.py` and `test_p1_positive.py` with `CAP_SRC_DIR`
pointing at the G2 checkouts (the G1 source/tripwire pin tests are excluded: they are pinned to the G1 PR head). `cap_v01/` is not edited or imported. The single G1 test that pins
the old docstring wording (`NO durable anti-rollback (G2)`) is run separately and is pinned to fail only on that wording (finding).

## Run

Needs `<CAP_SRC_DIR>/{control_plane,registry,replay}` at the SHAs of `sources.json` (control_plane with full history in the hosted run; `fetch_sources.sh <dir>` fetches them), PyNaCl,
pytest, pydantic. Re-pin the Control Plane head without editing files with `CAP_CP_SHA` (and `CAP_CP_BASE_SHA`).

    CAP_SRC_DIR=<dir> CAP_EVIDENCE_DIR=<evidence> python -m pytest -rA --junitxml=<evidence>/junit.xml   # from cap_v02/
    python junit_gate.py <evidence>/junit.xml --min-tests 250                                          # fail-closed gate (hosted workflow)

Evidence written under `$CAP_EVIDENCE_DIR`: `cp-changed-files.sha256`, `evidence-manifest.sha256`, `g2-evidence/*.json` (persisted state before/after, restart transcript, concurrency outcomes,
crash residue, refusal codes, limits), `g1-regression-*.{xml,txt}`.
