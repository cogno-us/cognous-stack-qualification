# cognous-governed-exchange cross component suite

Original source: [exact snapshot](https://github.com/cogno-us/cognous-governed-exchange/tree/9de2d438ed03531bb960c896f541a6a2da1b2315). Implementation and component-local tests remain in the owning repository.

Use the reusable workflows listed below through GitHub Actions. Each source caller supplies its exact component commit and the immutable qualification commit. The assembly tool restores only these relocated test/harness paths in a disposable source checkout, preserving relative imports without vendoring runtime packages. Source changes after inventory are rejected rather than silently overwritten.

Licenses: see the retained LICENSE and NOTICE files in this directory and [the repository notices](../../THIRD_PARTY_NOTICES.md). No source license is replaced by relocation. Historical test outcomes remain tied to their original commits; no successful outcome is inferred from a move.

## Workflows

- [cognous-governed-exchange--merged-consumer-chain.yml](../../.github/workflows/cognous-governed-exchange--merged-consumer-chain.yml)
- [cognous-governed-exchange--tests.yml](../../.github/workflows/cognous-governed-exchange--tests.yml)
- [cognous-governed-exchange--typed-refusal.yml](../../.github/workflows/cognous-governed-exchange--typed-refusal.yml)

## Source map

| Original path | Canonical file | License |
|---|---|---|
| [.github/workflows/merged-consumer-chain.yml](https://github.com/cogno-us/cognous-governed-exchange/blob/9de2d438ed03531bb960c896f541a6a2da1b2315/.github/workflows/merged-consumer-chain.yml) | [.github/workflows/merged-consumer-chain.yml](.github/workflows/merged-consumer-chain.yml) | Apache-2.0 |
| [.github/workflows/tests.yml](https://github.com/cogno-us/cognous-governed-exchange/blob/9de2d438ed03531bb960c896f541a6a2da1b2315/.github/workflows/tests.yml) | [.github/workflows/tests.yml](.github/workflows/tests.yml) | Apache-2.0 |
| [.github/workflows/typed-refusal.yml](https://github.com/cogno-us/cognous-governed-exchange/blob/9de2d438ed03531bb960c896f541a6a2da1b2315/.github/workflows/typed-refusal.yml) | [.github/workflows/typed-refusal.yml](.github/workflows/typed-refusal.yml) | Apache-2.0 |
| [candidate_qualification/conftest.py](https://github.com/cogno-us/cognous-governed-exchange/blob/9de2d438ed03531bb960c896f541a6a2da1b2315/candidate_qualification/conftest.py) | [candidate_qualification/conftest.py](candidate_qualification/conftest.py) | Apache-2.0 |
| [candidate_qualification/test_typed_refusal_profile.py](https://github.com/cogno-us/cognous-governed-exchange/blob/9de2d438ed03531bb960c896f541a6a2da1b2315/candidate_qualification/test_typed_refusal_profile.py) | [candidate_qualification/test_typed_refusal_profile.py](candidate_qualification/test_typed_refusal_profile.py) | Apache-2.0 |
| [qualification/conftest.py](https://github.com/cogno-us/cognous-governed-exchange/blob/9de2d438ed03531bb960c896f541a6a2da1b2315/qualification/conftest.py) | [qualification/conftest.py](qualification/conftest.py) | Apache-2.0 |
| [qualification/test_merged_artifacts.py](https://github.com/cogno-us/cognous-governed-exchange/blob/9de2d438ed03531bb960c896f541a6a2da1b2315/qualification/test_merged_artifacts.py) | [qualification/test_merged_artifacts.py](qualification/test_merged_artifacts.py) | Apache-2.0 |
| [qualification/test_merged_store.py](https://github.com/cogno-us/cognous-governed-exchange/blob/9de2d438ed03531bb960c896f541a6a2da1b2315/qualification/test_merged_store.py) | [qualification/test_merged_store.py](qualification/test_merged_store.py) | Apache-2.0 |
| [tests/test_control_plane_store_adoption.py](https://github.com/cogno-us/cognous-governed-exchange/blob/9de2d438ed03531bb960c896f541a6a2da1b2315/tests/test_control_plane_store_adoption.py) | [tests/test_control_plane_store_adoption.py](tests/test_control_plane_store_adoption.py) | Apache-2.0 |
| [tests/test_gax_imx_redelivery.py](https://github.com/cogno-us/cognous-governed-exchange/blob/9de2d438ed03531bb960c896f541a6a2da1b2315/tests/test_gax_imx_redelivery.py) | [tests/test_gax_imx_redelivery.py](tests/test_gax_imx_redelivery.py) | Apache-2.0 |
| [tests/test_gax_imx_reference.py](https://github.com/cogno-us/cognous-governed-exchange/blob/9de2d438ed03531bb960c896f541a6a2da1b2315/tests/test_gax_imx_reference.py) | [tests/test_gax_imx_reference.py](tests/test_gax_imx_reference.py) | Apache-2.0 |
| [tests/test_gax_public_runtime_artifacts.py](https://github.com/cogno-us/cognous-governed-exchange/blob/9de2d438ed03531bb960c896f541a6a2da1b2315/tests/test_gax_public_runtime_artifacts.py) | [tests/test_gax_public_runtime_artifacts.py](tests/test_gax_public_runtime_artifacts.py) | Apache-2.0 |
| [tests/test_governed_message_transport_integration.py](https://github.com/cogno-us/cognous-governed-exchange/blob/9de2d438ed03531bb960c896f541a6a2da1b2315/tests/test_governed_message_transport_integration.py) | [tests/test_governed_message_transport_integration.py](tests/test_governed_message_transport_integration.py) | Apache-2.0 |
| [tests/test_observation_repair.py](https://github.com/cogno-us/cognous-governed-exchange/blob/9de2d438ed03531bb960c896f541a6a2da1b2315/tests/test_observation_repair.py) | [tests/test_observation_repair.py](tests/test_observation_repair.py) | Apache-2.0 |
| [tests/test_recovery_export_separation.py](https://github.com/cogno-us/cognous-governed-exchange/blob/9de2d438ed03531bb960c896f541a6a2da1b2315/tests/test_recovery_export_separation.py) | [tests/test_recovery_export_separation.py](tests/test_recovery_export_separation.py) | Apache-2.0 |
