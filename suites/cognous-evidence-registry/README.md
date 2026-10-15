# Evidence registry and BitRep qualification

These two test drivers are copied byte-for-byte from [cogno-us/cognous-evidence-registry](https://github.com/cogno-us/cognous-evidence-registry/tree/650903fd6db1d68810dd377ba09e801a76682935) at `650903fd6db1d68810dd377ba09e801a76682935`. The adapter, EVM contract, clients and application-local tests remain in their owning repository.

The [reusable chain workflow](../../.github/workflows/cognous-evidence-registry--chain-qualification.yml) assembles the drivers into an exact registry checkout, uses pinned BitRep `5b5077dafde232a7801cb425c4efddcffb468723`, the existing npm lock and synthetic disposable loopback EVM targets. It does not use public RPC, funds or production keys.

License: retained [Apache-2.0](LICENSE). Source provenance, original paths and hashes are in the [migration manifest](../../migrations/cross-component-2026-10-15.json).

- [chain/python/test_bitrep.py](chain/python/test_bitrep.py) — [source](https://github.com/cogno-us/cognous-evidence-registry/blob/650903fd6db1d68810dd377ba09e801a76682935/chain/python/test_bitrep.py)
- [chain/test/protocol.test.mjs](chain/test/protocol.test.mjs) — [source](https://github.com/cogno-us/cognous-evidence-registry/blob/650903fd6db1d68810dd377ba09e801a76682935/chain/test/protocol.test.mjs)
