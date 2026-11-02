# CAP v0.1 gate G1 - independent qualification tests

Independent tests (negatives N1-N4, positive P1, source/tripwire rows S and T) for the merged Control Plane G1 commit
`registry_authority_profile` (`ocs-authority-profile/0.1`), written from the frozen contract
(cogno-us/cognous-open-control-stack#259, comment 6589180377), not from the implementer's tests.

Real components: Control Plane `GovernedAgeWorkflow` built by the factory, Registry `verify_f4_selection_v2` (11 layers) with the exact `Ed25519Verifier` (PyNaCl),
Replay `registry-authenticated-selection/0.1` import (P1). Keys are SYNTHETIC (mechanism only). Spies wrap the Registry core and the signature check in place and delegate,
to prove whether the verifier was reached. On refusals the configuration, snapshot, destination and run store are compared byte-for-byte before and after.

Claim scope: claim A only. NO durable anti-rollback (G2): nothing here tests or claims cross-process rollback protection. Not an operational-trust claim.

| Row | File | What |
|---|---|---|
| S | battery/test_00_sources.py | pinned HEADs, modules imported from the pinned checkouts, locked PyNaCl, G2/claim labels |
| T | battery/test_01_tripwire.py | CP changed-file set is exactly 6 files vs base 8b97d32f; bounded.py untouched; Registry/Replay clean at pins; SHA-256 manifest |
| N1 | battery/test_n1_forged_authority.py | attacker/host snapshot, altered pinned file, extra issuer/grant, forged signature, decision-time tamper, no cache |
| N2 | battery/test_n2_scope_authority.py | scope/consumer/tenant/operation mismatch, ungranted issuer, wildcard, revoked, expired |
| N3 | battery/test_n3_mode_config.py | mode mismatch both ways, omitted mode, operational always unprovisioned, secret material, closed schema, digest, version |
| N4 | battery/test_n4_verifier_epoch.py | None/subclass/stub verifier, injected kwargs, unimportable Registry, missing epoch floor |
| P1 | battery/test_p1_positive.py | factory flow authorizes, 4 reads, 11 layers, fingerprint == pin, Replay trust kwargs + real Replay import |

## Run
Needs `<CAP_SRC_DIR>/{control_plane,registry,replay}` at the SHAs of `sources.json` (control_plane with full history; `fetch_sources.sh <dir>` fetches them) and PyNaCl, pytest,
pydantic installed (PyNaCl from the Registry hash-locked `requirements-ed25519.lock.txt`).

    CAP_SRC_DIR=<dir> python -m pytest -rA            # from cap_v01/
    python junit_gate.py junit.xml --min-tests 254    # fail-closed gate (hosted workflow)
