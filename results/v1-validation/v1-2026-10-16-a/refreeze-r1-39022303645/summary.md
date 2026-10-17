## V1 validation v1-2026-10-16-a

Freeze: **PASS** · Verdict: **FAIL** (requirement matrix)

| Status | Jobs |
|---|---|
| PASS | 14 |
| FAIL | 1 |
| INCONCLUSIVE | 43 |
| NOT RUN | 0 |
| NOT APPLICABLE | 0 |

| Component | OS | Python | Status | Testcases/fail/err/skip | Reason |
|---|---|---|---|---|---|
| hub-tests | ubuntu-latest | 3.12 | PASS | 653/0/0/0 |  |
| qual-tooling | ubuntu-latest | 3.12 | PASS | 131/0/0/0 |  |
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
| control_plane | ubuntu-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| control_plane | ubuntu-latest | 3.11 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| control_plane | windows-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| control_plane | macos-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| moltbot_safe | ubuntu-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| moltbot_safe | ubuntu-latest | 3.11 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| moltbot_safe | windows-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| moltbot_safe | macos-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| replay_bundle | ubuntu-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| replay_bundle | ubuntu-latest | 3.11 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| replay_bundle | windows-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| replay_bundle | macos-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| governance_evidence_pack | ubuntu-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| governance_evidence_pack | ubuntu-latest | 3.11 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| governance_evidence_pack | windows-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| governance_evidence_pack | macos-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| odes | ubuntu-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| odes | ubuntu-latest | 3.11 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| odes | windows-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| odes | macos-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| gax_imx_transport | ubuntu-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| gax_imx_transport | ubuntu-latest | 3.11 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| gax_imx_transport | windows-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| gax_imx_transport | macos-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| action_manifest | ubuntu-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| action_manifest | ubuntu-latest | 3.11 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| action_manifest | windows-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| action_manifest | macos-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| bitrep | ubuntu-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| bitrep | ubuntu-latest | 3.11 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| bitrep | windows-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| bitrep | macos-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| the_index | ubuntu-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| the_index | ubuntu-latest | 3.11 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| the_index | windows-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| the_index | macos-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| constitutional_authority | ubuntu-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| constitutional_authority | ubuntu-latest | 3.11 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| constitutional_authority | windows-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| constitutional_authority | macos-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| prp | ubuntu-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| research_intelligence | ubuntu-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
| tfa | ubuntu-latest | 3.12 | INCONCLUSIVE | -/-/-/- | expected job produced no result (setup failure, cancelled or unavailable runner) |
