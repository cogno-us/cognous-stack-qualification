# cognous-governance-evidence-pack cross component suite

Original source: [exact snapshot](https://github.com/cogno-us/cognous-governance-evidence-pack/tree/1e789c7d67a897097445faef1813fb0cd22d55e5). Implementation and component-local tests remain in the owning repository.

Use the reusable workflows listed below through GitHub Actions. Each source caller supplies its exact component commit and the immutable qualification commit. The assembly tool restores only these relocated test/harness paths in a disposable source checkout, preserving relative imports without vendoring runtime packages. Source changes after inventory are rejected rather than silently overwritten.

Licenses: see the retained LICENSE and NOTICE files in this directory and [the repository notices](../../THIRD_PARTY_NOTICES.md). No source license is replaced by relocation. Historical test outcomes remain tied to their original commits; no successful outcome is inferred from a move.

## Workflows

- [cognous-governance-evidence-pack--merged-producers.yml](../../.github/workflows/cognous-governance-evidence-pack--merged-producers.yml)
- [cognous-governance-evidence-pack--recovery-inspection.yml](../../.github/workflows/cognous-governance-evidence-pack--recovery-inspection.yml)
- [cognous-governance-evidence-pack--tests.yml](../../.github/workflows/cognous-governance-evidence-pack--tests.yml)
- [cognous-governance-evidence-pack--typed-refusal.yml](../../.github/workflows/cognous-governance-evidence-pack--typed-refusal.yml)
- [cognous-governance-evidence-pack--w3-actual-producer.yml](../../.github/workflows/cognous-governance-evidence-pack--w3-actual-producer.yml)
- [cognous-governance-evidence-pack--w3-c8-actual.yml](../../.github/workflows/cognous-governance-evidence-pack--w3-c8-actual.yml)
- [cognous-governance-evidence-pack--w3-composed.yml](../../.github/workflows/cognous-governance-evidence-pack--w3-composed.yml)

## Source map

| Original path | Canonical file | License |
|---|---|---|
| [.github/workflows/merged-producers.yml](https://github.com/cogno-us/cognous-governance-evidence-pack/blob/1e789c7d67a897097445faef1813fb0cd22d55e5/.github/workflows/merged-producers.yml) | [.github/workflows/merged-producers.yml](.github/workflows/merged-producers.yml) | Apache-2.0 |
| [.github/workflows/recovery-inspection.yml](https://github.com/cogno-us/cognous-governance-evidence-pack/blob/1e789c7d67a897097445faef1813fb0cd22d55e5/.github/workflows/recovery-inspection.yml) | [.github/workflows/recovery-inspection.yml](.github/workflows/recovery-inspection.yml) | Apache-2.0 |
| [.github/workflows/tests.yml](https://github.com/cogno-us/cognous-governance-evidence-pack/blob/1e789c7d67a897097445faef1813fb0cd22d55e5/.github/workflows/tests.yml) | [.github/workflows/tests.yml](.github/workflows/tests.yml) | Apache-2.0 |
| [.github/workflows/typed-refusal.yml](https://github.com/cogno-us/cognous-governance-evidence-pack/blob/1e789c7d67a897097445faef1813fb0cd22d55e5/.github/workflows/typed-refusal.yml) | [.github/workflows/typed-refusal.yml](.github/workflows/typed-refusal.yml) | Apache-2.0 |
| [.github/workflows/w3-actual-producer.yml](https://github.com/cogno-us/cognous-governance-evidence-pack/blob/1e789c7d67a897097445faef1813fb0cd22d55e5/.github/workflows/w3-actual-producer.yml) | [.github/workflows/w3-actual-producer.yml](.github/workflows/w3-actual-producer.yml) | Apache-2.0 |
| [.github/workflows/w3-c8-actual.yml](https://github.com/cogno-us/cognous-governance-evidence-pack/blob/1e789c7d67a897097445faef1813fb0cd22d55e5/.github/workflows/w3-c8-actual.yml) | [.github/workflows/w3-c8-actual.yml](.github/workflows/w3-c8-actual.yml) | Apache-2.0 |
| [.github/workflows/w3-composed.yml](https://github.com/cogno-us/cognous-governance-evidence-pack/blob/1e789c7d67a897097445faef1813fb0cd22d55e5/.github/workflows/w3-composed.yml) | [.github/workflows/w3-composed.yml](.github/workflows/w3-composed.yml) | Apache-2.0 |
| [qualification/refusal_sources.py](https://github.com/cogno-us/cognous-governance-evidence-pack/blob/1e789c7d67a897097445faef1813fb0cd22d55e5/qualification/refusal_sources.py) | [qualification/refusal_sources.py](qualification/refusal_sources.py) | Apache-2.0 |
| [qualification/test_merged_producer.py](https://github.com/cogno-us/cognous-governance-evidence-pack/blob/1e789c7d67a897097445faef1813fb0cd22d55e5/qualification/test_merged_producer.py) | [qualification/test_merged_producer.py](qualification/test_merged_producer.py) | Apache-2.0 |
| [qualification/test_refusal_profile.py](https://github.com/cogno-us/cognous-governance-evidence-pack/blob/1e789c7d67a897097445faef1813fb0cd22d55e5/qualification/test_refusal_profile.py) | [qualification/test_refusal_profile.py](qualification/test_refusal_profile.py) | Apache-2.0 |
| [scripts/qualify_control_plane_store_compatibility.py](https://github.com/cogno-us/cognous-governance-evidence-pack/blob/1e789c7d67a897097445faef1813fb0cd22d55e5/scripts/qualify_control_plane_store_compatibility.py) | [scripts/qualify_control_plane_store_compatibility.py](scripts/qualify_control_plane_store_compatibility.py) | Apache-2.0 |
| [scripts/qualify_merged_producer.py](https://github.com/cogno-us/cognous-governance-evidence-pack/blob/1e789c7d67a897097445faef1813fb0cd22d55e5/scripts/qualify_merged_producer.py) | [scripts/qualify_merged_producer.py](scripts/qualify_merged_producer.py) | Apache-2.0 |
| [scripts/qualify_producer_v2.py](https://github.com/cogno-us/cognous-governance-evidence-pack/blob/1e789c7d67a897097445faef1813fb0cd22d55e5/scripts/qualify_producer_v2.py) | [scripts/qualify_producer_v2.py](scripts/qualify_producer_v2.py) | Apache-2.0 |
| [scripts/w3_c8_actual_source.py](https://github.com/cogno-us/cognous-governance-evidence-pack/blob/1e789c7d67a897097445faef1813fb0cd22d55e5/scripts/w3_c8_actual_source.py) | [scripts/w3_c8_actual_source.py](scripts/w3_c8_actual_source.py) | Apache-2.0 |
| [scripts/w3_capture_accepted_producer.py](https://github.com/cogno-us/cognous-governance-evidence-pack/blob/1e789c7d67a897097445faef1813fb0cd22d55e5/scripts/w3_capture_accepted_producer.py) | [scripts/w3_capture_accepted_producer.py](scripts/w3_capture_accepted_producer.py) | Apache-2.0 |
| [tests/recovery_inspection_checks.py](https://github.com/cogno-us/cognous-governance-evidence-pack/blob/1e789c7d67a897097445faef1813fb0cd22d55e5/tests/recovery_inspection_checks.py) | [tests/recovery_inspection_checks.py](tests/recovery_inspection_checks.py) | Apache-2.0 |
| [tests/test_accepted_executor_profile.py](https://github.com/cogno-us/cognous-governance-evidence-pack/blob/1e789c7d67a897097445faef1813fb0cd22d55e5/tests/test_accepted_executor_profile.py) | [tests/test_accepted_executor_profile.py](tests/test_accepted_executor_profile.py) | Apache-2.0 |
| [tests/test_control_plane_store_compatibility.py](https://github.com/cogno-us/cognous-governance-evidence-pack/blob/1e789c7d67a897097445faef1813fb0cd22d55e5/tests/test_control_plane_store_compatibility.py) | [tests/test_control_plane_store_compatibility.py](tests/test_control_plane_store_compatibility.py) | Apache-2.0 |
| [tests/test_importer.py](https://github.com/cogno-us/cognous-governance-evidence-pack/blob/1e789c7d67a897097445faef1813fb0cd22d55e5/tests/test_importer.py) | [tests/test_importer.py](tests/test_importer.py) | Apache-2.0 |
| [tests/test_producer_v2.py](https://github.com/cogno-us/cognous-governance-evidence-pack/blob/1e789c7d67a897097445faef1813fb0cd22d55e5/tests/test_producer_v2.py) | [tests/test_producer_v2.py](tests/test_producer_v2.py) | Apache-2.0 |
| [tests/test_w3_composed_candidate.py](https://github.com/cogno-us/cognous-governance-evidence-pack/blob/1e789c7d67a897097445faef1813fb0cd22d55e5/tests/test_w3_composed_candidate.py) | [tests/test_w3_composed_candidate.py](tests/test_w3_composed_candidate.py) | Apache-2.0 |
