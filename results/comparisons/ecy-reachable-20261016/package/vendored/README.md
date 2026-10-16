# Vendored consumer constants

The three files in this directory are verbatim copies of the pinned-revision
source files that define the F5b and security-generation consumer constants.
Their SHA-256 values are listed in `../manifest.json#vendored_consumer_sources`.
The verifier `../verify_f5b_enforcement.py` loads these files directly (no
network, no imports from other installed packages) and runs the pairing-
enforcement check against each trial's `native/consumers/odes-package.json`.

| File | Source repository (frozen revision) | Source path |
|---|---|---|
| `odes_common.py` | cogno-us/open-decision-evidence-standard @ eb83220c82f942e429a5e3ef5f677fdd5057ef84 | `src/odes/common.py` |
| `ep_importer.py` | cogno-us/cognous-governance-evidence-pack @ 893aca8dfb27ba5c5f3e833f2d29210ca7fc92e3 | `src/agent_governance_evidence_pack/importer.py` |
| `replay_importers.py` | cogno-us/cognous-replay-bundle @ 79ba16d48b9be1e059b3045989c7df960c3df1c2 | `src/agent_replay_bundle/importers.py` |

Why vendor instead of pip-install: the verifier must be standalone and
recipient-verifiable; vendoring the exact bytes (hash-recorded) proves that the
"F5b pairing is enforced by consumer code" claim is grounded in the real
consumer sources, not in a boolean the producer wrote into
`f5b-enforcement.json`.
