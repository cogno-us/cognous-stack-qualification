## V1 validation v1-2026-10-16-a

Freeze: **PASS** · Verdict: **INCOMPLETE** (no requirement matrix supplied: aggregation refuses to promote)

| Status | Jobs |
|---|---|
| PASS | 33 |
| FAIL | 1 |
| INCONCLUSIVE | 0 |
| NOT RUN | 2 |
| NOT APPLICABLE | 0 |

| Component | OS | Python | Status | Testcases/fail/err/skip | Reason |
|---|---|---|---|---|---|
| action_manifest | macos-latest | 3.12.10 | PASS | 146/0/0/0 |  |
| action_manifest | ubuntu-latest | 3.11.17 | PASS | 146/0/0/0 |  |
| action_manifest | ubuntu-latest | 3.12.15 | PASS | 146/0/0/0 |  |
| bitrep | macos-latest | 3.12.10 | PASS | 81/0/0/0 |  |
| bitrep | ubuntu-latest | 3.11.17 | PASS | 81/0/0/0 |  |
| bitrep | ubuntu-latest | 3.12.15 | PASS | 81/0/0/0 |  |
| constitutional_authority | macos-latest | 3.12.10 | PASS | 446/0/0/1 |  |
| constitutional_authority | ubuntu-latest | 3.11.17 | PASS | 446/0/0/1 |  |
| constitutional_authority | ubuntu-latest | 3.12.15 | PASS | 446/0/0/1 |  |
| control_plane | macos-latest | 3.12.10 | FAIL | 320/188/0/1 | test failures/errors |
| control_plane | ubuntu-latest | 3.11.17 | PASS | 320/0/0/1 |  |
| control_plane | ubuntu-latest | 3.12.15 | PASS | 320/0/0/1 |  |
| gax_imx_transport | macos-latest | 3.12.10 | PASS | 102/0/0/0 |  |
| gax_imx_transport | ubuntu-latest | 3.11.17 | PASS | 102/0/0/0 |  |
| gax_imx_transport | ubuntu-latest | 3.12.15 | PASS | 102/0/0/0 |  |
| governance_evidence_pack | macos-latest | 3.12.10 | PASS | 150/0/0/0 |  |
| governance_evidence_pack | ubuntu-latest | 3.11.17 | PASS | 150/0/0/0 |  |
| governance_evidence_pack | ubuntu-latest | 3.12.15 | PASS | 150/0/0/0 |  |
| moltbot_safe | macos-latest | 3.12.10 | PASS | 174/0/0/0 |  |
| moltbot_safe | ubuntu-latest | 3.11.17 | PASS | 174/0/0/0 |  |
| moltbot_safe | ubuntu-latest | 3.12.15 | PASS | 174/0/0/0 |  |
| odes | macos-latest | 3.12.10 | PASS | 78/0/0/0 |  |
| odes | ubuntu-latest | 3.11.17 | PASS | 78/0/0/0 |  |
| odes | ubuntu-latest | 3.12.15 | PASS | 78/0/0/0 |  |
| prp | ubuntu-latest | 3.12.15 | NOT RUN | -/-/-/- | no test_*.py discovered in this component at the pinned commit |
| replay_bundle | macos-latest | 3.12.10 | PASS | 204/0/0/0 |  |
| replay_bundle | ubuntu-latest | 3.11.17 | PASS | 204/0/0/0 |  |
| replay_bundle | ubuntu-latest | 3.12.15 | PASS | 204/0/0/0 |  |
| research_intelligence | ubuntu-latest | 3.12.15 | PASS | 13/0/0/0 |  |
| tfa | ubuntu-latest | 3.12.15 | NOT RUN | -/-/-/- | no test_*.py discovered in this component at the pinned commit |
| the_index | macos-latest | 3.12.10 | PASS | 85/0/0/0 |  |
| the_index | ubuntu-latest | 3.11.17 | PASS | 85/0/0/0 |  |
| the_index | ubuntu-latest | 3.12.15 | PASS | 85/0/0/0 |  |
| hub-tests | ubuntu-latest | 3.12 | PASS | 653/0/0/0 |  |
| qual-tooling | ubuntu-latest | 3.12 | PASS | 114/0/0/0 |  |
| native-f5b-suite | ubuntu-latest | 3.12 | PASS | 36/0/0/0 |  |
