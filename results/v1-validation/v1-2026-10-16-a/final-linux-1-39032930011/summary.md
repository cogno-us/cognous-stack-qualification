## V1 validation v1-2026-10-16-a

Freeze: **PASS** · Verdict: **FAIL** (requirement matrix)

| Status | Jobs |
|---|---|
| PASS | 35 |
| FAIL | 1 |
| INCONCLUSIVE | 0 |
| NOT RUN | 2 |
| NOT APPLICABLE | 0 |

| Component | OS | Python | Status | Testcases/fail/err/skip | Reason |
|---|---|---|---|---|---|
| action_manifest | ubuntu-latest | 3.11.17 | PASS | 146/0/0/0 |  |
| action_manifest | ubuntu-latest | 3.12.15 | PASS | 146/0/0/0 |  |
| bitrep | ubuntu-latest | 3.11.17 | PASS | 81/0/0/0 |  |
| bitrep | ubuntu-latest | 3.12.15 | PASS | 81/0/0/0 |  |
| constitutional_authority | ubuntu-latest | 3.11.17 | PASS | 446/0/0/0 |  |
| constitutional_authority | ubuntu-latest | 3.12.15 | PASS | 446/0/0/0 |  |
| control_plane | ubuntu-latest | 3.11.17 | PASS | 320/0/0/1 |  |
| control_plane | ubuntu-latest | 3.12.15 | PASS | 320/0/0/1 |  |
| gax_imx_transport | ubuntu-latest | 3.11.17 | PASS | 109/0/0/0 |  |
| gax_imx_transport | ubuntu-latest | 3.12.15 | PASS | 109/0/0/0 |  |
| governance_evidence_pack | ubuntu-latest | 3.11.17 | PASS | 155/0/0/0 |  |
| governance_evidence_pack | ubuntu-latest | 3.12.15 | PASS | 155/0/0/0 |  |
| moltbot_safe | ubuntu-latest | 3.11.17 | PASS | 194/0/0/0 |  |
| moltbot_safe | ubuntu-latest | 3.12.15 | PASS | 194/0/0/0 |  |
| odes | ubuntu-latest | 3.11.17 | PASS | 91/0/0/0 |  |
| odes | ubuntu-latest | 3.12.15 | PASS | 91/0/0/0 |  |
| prp | ubuntu-latest | 3.12.15 | NOT RUN | -/-/-/- | no test_*.py discovered in this component at the pinned commit |
| replay_bundle | ubuntu-latest | 3.11.17 | PASS | 240/0/0/0 |  |
| replay_bundle | ubuntu-latest | 3.12.15 | PASS | 240/0/0/0 |  |
| research_intelligence | ubuntu-latest | 3.12.15 | PASS | 13/0/0/0 |  |
| tfa | ubuntu-latest | 3.12.15 | NOT RUN | -/-/-/- | no test_*.py discovered in this component at the pinned commit |
| the_index | ubuntu-latest | 3.11.17 | PASS | 121/0/0/0 |  |
| the_index | ubuntu-latest | 3.12.15 | PASS | 121/0/0/0 |  |
| hub-tests | ubuntu-latest | 3.12 | PASS | 653/0/0/0 |  |
| qual-tooling | ubuntu-latest | 3.12 | PASS | 133/0/0/0 |  |
| matched-refund-rerun | ubuntu-latest | 3.12 | PASS | 20/0/0/0 |  |
| native-f5b-suite | ubuntu-latest | 3.12 | PASS | 36/0/0/0 |  |
| probes-action-manifest | ubuntu-latest | 3.12.15 | PASS | 3/0/0/0 | probe harness executed; individual probe outcomes are in junit.xml |
| probes-authority | ubuntu-latest | 3.12.15 | PASS | 23/1/0/0 | probe harness executed; individual probe outcomes are in junit.xml |
| probes-bitrep | ubuntu-latest | 3.12.15 | PASS | 9/0/0/0 | probe harness executed; individual probe outcomes are in junit.xml |
| probes-control-plane | ubuntu-latest | 3.12.15 | PASS | 61/6/0/0 | probe harness executed; individual probe outcomes are in junit.xml |
| probes-evidence-pack | ubuntu-latest | 3.12.15 | PASS | 12/0/0/0 | probe harness executed; individual probe outcomes are in junit.xml |
| probes-index | ubuntu-latest | 3.12.15 | PASS | 35/0/0/0 | probe harness executed; individual probe outcomes are in junit.xml |
| probes-moltbot-safe | ubuntu-latest | 3.12.15 | PASS | 22/0/0/0 | probe harness executed; individual probe outcomes are in junit.xml |
| probes-odes | ubuntu-latest | 3.12.15 | PASS | 13/0/0/0 | probe harness executed; individual probe outcomes are in junit.xml |
| probes-replay-bundle | ubuntu-latest | 3.12.15 | PASS | 10/0/0/0 | probe harness executed; individual probe outcomes are in junit.xml |
| provenance-scan | ubuntu-latest | 3.12.15 | PASS | 4/0/0/0 | probe harness executed; individual probe outcomes are in junit.xml |
| scenarios | ubuntu-latest | 3.12 | FAIL | -/-/-/- |  |
