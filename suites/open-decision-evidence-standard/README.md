# open-decision-evidence-standard cross component suite

Original source: [exact snapshot](https://github.com/cogno-us/open-decision-evidence-standard/tree/25c7ad608c2e6fd9f450e075db6bbf3ee4091a49). Implementation and component-local tests remain in the owning repository.

Use the reusable workflows listed below through GitHub Actions. Each source caller supplies its exact component commit and the immutable qualification commit. The assembly tool restores only these relocated test/harness paths in a disposable source checkout, preserving relative imports without vendoring runtime packages. Source changes after inventory are rejected rather than silently overwritten.

Licenses: see the retained LICENSE and NOTICE files in this directory and [the repository notices](../../THIRD_PARTY_NOTICES.md). No source license is replaced by relocation. Historical test outcomes remain tied to their original commits; no successful outcome is inferred from a move.

## Workflows

- [open-decision-evidence-standard--merged-producers.yml](../../.github/workflows/open-decision-evidence-standard--merged-producers.yml)
- [open-decision-evidence-standard--tests.yml](../../.github/workflows/open-decision-evidence-standard--tests.yml)
- [open-decision-evidence-standard--typed-refusal.yml](../../.github/workflows/open-decision-evidence-standard--typed-refusal.yml)

## Source map

| Original path | Canonical file | License |
|---|---|---|
| [.github/workflows/merged-producers.yml](https://github.com/cogno-us/open-decision-evidence-standard/blob/25c7ad608c2e6fd9f450e075db6bbf3ee4091a49/.github/workflows/merged-producers.yml) | [.github/workflows/merged-producers.yml](.github/workflows/merged-producers.yml) | Apache-2.0 |
| [.github/workflows/tests.yml](https://github.com/cogno-us/open-decision-evidence-standard/blob/25c7ad608c2e6fd9f450e075db6bbf3ee4091a49/.github/workflows/tests.yml) | [.github/workflows/tests.yml](.github/workflows/tests.yml) | Apache-2.0 |
| [.github/workflows/typed-refusal.yml](https://github.com/cogno-us/open-decision-evidence-standard/blob/25c7ad608c2e6fd9f450e075db6bbf3ee4091a49/.github/workflows/typed-refusal.yml) | [.github/workflows/typed-refusal.yml](.github/workflows/typed-refusal.yml) | Apache-2.0 |
| [qualification/refusal_sources.py](https://github.com/cogno-us/open-decision-evidence-standard/blob/25c7ad608c2e6fd9f450e075db6bbf3ee4091a49/qualification/refusal_sources.py) | [qualification/refusal_sources.py](qualification/refusal_sources.py) | Apache-2.0 |
| [qualification/test_merged_producer.py](https://github.com/cogno-us/open-decision-evidence-standard/blob/25c7ad608c2e6fd9f450e075db6bbf3ee4091a49/qualification/test_merged_producer.py) | [qualification/test_merged_producer.py](qualification/test_merged_producer.py) | Apache-2.0 |
| [qualification/test_refusal_profile.py](https://github.com/cogno-us/open-decision-evidence-standard/blob/25c7ad608c2e6fd9f450e075db6bbf3ee4091a49/qualification/test_refusal_profile.py) | [qualification/test_refusal_profile.py](qualification/test_refusal_profile.py) | Apache-2.0 |
| [scripts/qualify_merged_producer.py](https://github.com/cogno-us/open-decision-evidence-standard/blob/25c7ad608c2e6fd9f450e075db6bbf3ee4091a49/scripts/qualify_merged_producer.py) | [scripts/qualify_merged_producer.py](scripts/qualify_merged_producer.py) | Apache-2.0 |
| [scripts/qualify_producer_v2.py](https://github.com/cogno-us/open-decision-evidence-standard/blob/25c7ad608c2e6fd9f450e075db6bbf3ee4091a49/scripts/qualify_producer_v2.py) | [scripts/qualify_producer_v2.py](scripts/qualify_producer_v2.py) | Apache-2.0 |
| [tests/test_accepted_replay_profile.py](https://github.com/cogno-us/open-decision-evidence-standard/blob/25c7ad608c2e6fd9f450e075db6bbf3ee4091a49/tests/test_accepted_replay_profile.py) | [tests/test_accepted_replay_profile.py](tests/test_accepted_replay_profile.py) | Apache-2.0 |
| [tests/test_odes_stack_export.py](https://github.com/cogno-us/open-decision-evidence-standard/blob/25c7ad608c2e6fd9f450e075db6bbf3ee4091a49/tests/test_odes_stack_export.py) | [tests/test_odes_stack_export.py](tests/test_odes_stack_export.py) | Apache-2.0 |
| [tests/test_producer_v2.py](https://github.com/cogno-us/open-decision-evidence-standard/blob/25c7ad608c2e6fd9f450e075db6bbf3ee4091a49/tests/test_producer_v2.py) | [tests/test_producer_v2.py](tests/test_producer_v2.py) | Apache-2.0 |
