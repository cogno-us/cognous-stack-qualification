# cognous-replay-bundle cross component suite

Original source: [exact snapshot](https://github.com/cogno-us/cognous-replay-bundle/tree/83fbaf2a0f6f071aca1ea0af859eb8fc6385c26a). Implementation and component-local tests remain in the owning repository.

Use the reusable workflows listed below through GitHub Actions. Each source caller supplies its exact component commit and the immutable qualification commit. The assembly tool restores only these relocated test/harness paths in a disposable source checkout, preserving relative imports without vendoring runtime packages. Source changes after inventory are rejected rather than silently overwritten.

Licenses: see the retained LICENSE and NOTICE files in this directory and [the repository notices](../../THIRD_PARTY_NOTICES.md). No source license is replaced by relocation. Historical test outcomes remain tied to their original commits; no successful outcome is inferred from a move.

## Workflows

- [cognous-replay-bundle--merged-producer.yml](../../.github/workflows/cognous-replay-bundle--merged-producer.yml)
- [cognous-replay-bundle--recovery-inspection.yml](../../.github/workflows/cognous-replay-bundle--recovery-inspection.yml)
- [cognous-replay-bundle--tests.yml](../../.github/workflows/cognous-replay-bundle--tests.yml)
- [cognous-replay-bundle--typed-refusal.yml](../../.github/workflows/cognous-replay-bundle--typed-refusal.yml)

## Source map

| Original path | Canonical file | License |
|---|---|---|
| [.github/workflows/merged-producer.yml](https://github.com/cogno-us/cognous-replay-bundle/blob/83fbaf2a0f6f071aca1ea0af859eb8fc6385c26a/.github/workflows/merged-producer.yml) | [.github/workflows/merged-producer.yml](.github/workflows/merged-producer.yml) | Apache-2.0 |
| [.github/workflows/recovery-inspection.yml](https://github.com/cogno-us/cognous-replay-bundle/blob/83fbaf2a0f6f071aca1ea0af859eb8fc6385c26a/.github/workflows/recovery-inspection.yml) | [.github/workflows/recovery-inspection.yml](.github/workflows/recovery-inspection.yml) | Apache-2.0 |
| [.github/workflows/tests.yml](https://github.com/cogno-us/cognous-replay-bundle/blob/83fbaf2a0f6f071aca1ea0af859eb8fc6385c26a/.github/workflows/tests.yml) | [.github/workflows/tests.yml](.github/workflows/tests.yml) | Apache-2.0 |
| [.github/workflows/typed-refusal.yml](https://github.com/cogno-us/cognous-replay-bundle/blob/83fbaf2a0f6f071aca1ea0af859eb8fc6385c26a/.github/workflows/typed-refusal.yml) | [.github/workflows/typed-refusal.yml](.github/workflows/typed-refusal.yml) | Apache-2.0 |
| [qualification/test_merged_producer.py](https://github.com/cogno-us/cognous-replay-bundle/blob/83fbaf2a0f6f071aca1ea0af859eb8fc6385c26a/qualification/test_merged_producer.py) | [qualification/test_merged_producer.py](qualification/test_merged_producer.py) | Apache-2.0 |
| [scripts/generate_producer_v2_examples.py](https://github.com/cogno-us/cognous-replay-bundle/blob/83fbaf2a0f6f071aca1ea0af859eb8fc6385c26a/scripts/generate_producer_v2_examples.py) | [scripts/generate_producer_v2_examples.py](scripts/generate_producer_v2_examples.py) | Apache-2.0 |
| [scripts/generate_reconstruction_examples.py](https://github.com/cogno-us/cognous-replay-bundle/blob/83fbaf2a0f6f071aca1ea0af859eb8fc6385c26a/scripts/generate_reconstruction_examples.py) | [scripts/generate_reconstruction_examples.py](scripts/generate_reconstruction_examples.py) | Apache-2.0 |
| [tests/recovery_inspection_checks.py](https://github.com/cogno-us/cognous-replay-bundle/blob/83fbaf2a0f6f071aca1ea0af859eb8fc6385c26a/tests/recovery_inspection_checks.py) | [tests/recovery_inspection_checks.py](tests/recovery_inspection_checks.py) | Apache-2.0 |
| [tests/test_pinned_integration.py](https://github.com/cogno-us/cognous-replay-bundle/blob/83fbaf2a0f6f071aca1ea0af859eb8fc6385c26a/tests/test_pinned_integration.py) | [tests/test_pinned_integration.py](tests/test_pinned_integration.py) | Apache-2.0 |
| [tests/test_producer_v2.py](https://github.com/cogno-us/cognous-replay-bundle/blob/83fbaf2a0f6f071aca1ea0af859eb8fc6385c26a/tests/test_producer_v2.py) | [tests/test_producer_v2.py](tests/test_producer_v2.py) | Apache-2.0 |
| [tests/test_producer_v2_persistence.py](https://github.com/cogno-us/cognous-replay-bundle/blob/83fbaf2a0f6f071aca1ea0af859eb8fc6385c26a/tests/test_producer_v2_persistence.py) | [tests/test_producer_v2_persistence.py](tests/test_producer_v2_persistence.py) | Apache-2.0 |
| [tests/test_refusal_evidence.py](https://github.com/cogno-us/cognous-replay-bundle/blob/83fbaf2a0f6f071aca1ea0af859eb8fc6385c26a/tests/test_refusal_evidence.py) | [tests/test_refusal_evidence.py](tests/test_refusal_evidence.py) | Apache-2.0 |
