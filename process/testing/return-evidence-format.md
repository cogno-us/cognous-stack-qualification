# Reciprocal evidence package for Jerry

Status: **REQUIRED AT THE NEXT APPLICABLE BOUNDED COMPARISON EXPORT; NOT YET GENERATED**.

## Native local export tooling

`tools/run_serial_qualification.py` now retains consistent standalone SQLite snapshots and native requests/readbacks for each diagnostic trial. On pristine exact-source checkouts, execute the frozen local battery, then package it with:

```bash
PYTHONDONTWRITEBYTECODE=1 python tools/run_serial_qualification.py --hub /path/to/hub --output /path/to/new-native-run > /path/to/serial-command.log 2>&1
PYTHONDONTWRITEBYTECODE=1 python tools/export_exchange.py --run /path/to/new-native-run --hub /path/to/hub --log /path/to/serial-command.log --output /path/to/new-exchange-package
python /path/to/new-exchange-package/verify_export.py /path/to/new-exchange-package
```

Output and logs must be outside the pristine source checkouts. The exporter preserves native records; it does not implement missing Replay/Evidence Pack adapters or convert duplicate admission into writer-free reconciliation. This fixture inserts a synthetic payload rather than executing the external sample's monetary refund. The package discloses that asymmetry and does not claim matched-request interoperability. Generating a local review package does not transmit it.

The owner requested that Cognous return results in a portable format comparable to Jerry's supplied local synthetic D04 sample. Generate and verify this package when the Cognous test is ready to execute and its actual records are available. Do not manufacture a matching outcome, relabel prior trials or rerun paid agent campaigns to populate it. This requirement does not start a test, send a message or assert interoperability acceptance.

## Package layout

| Path | Contents |
|---|---|
| `README_FOR_JERRY.md` | Exact scenario/configuration, what actually ran, reproduction and verification commands, scoped findings, prerequisites and limitations. Distinguish producer-reported test results from recipient-reproduced checks. |
| `manifest.json` | Package/format version, architecture, scenario/version, variant, comparison/run/trial IDs; exact component, harness and evaluator identities; profile/configuration digest; observation times and clock domains; separate execution, interoperability and authority-authenticity dispositions; artifact byte lengths and SHA-256 values. |
| `fixture.json` | Synthetic initial state, resource identity, exact proposed action/payload, stable effect identity, authority assumptions, fault plan, clocks, reset configuration and expected assertions. Keep simulated time separate from wall time. |
| `transport.json` | Separate attempt IDs, writer/dispatch events and their evidence references, original acknowledgement, retry/reconciliation outcome and current-authority checks. Preserve UNKNOWN as a historical fact. |
| `post_commit_readback.json` | For D04, the actual post-commit/pre-retry snapshot and observation metadata. For another scenario, mark this item NOT APPLICABLE with a reason rather than inventing a commit. |
| `observation.json` | Raw destination readback, resource/state/version, exact effect occurrence count, attempt and authorization records when exposed, observer route/access separation, consistency, horizon and blind spots. |
| `native/` | Actual Cognous producer records, Replay bundle and Evidence Pack, with their native schemas/versions and validator output. Do not manufacture a SCQOS receipt or a substitute authorization token. |
| `destination/` | Disposable synthetic destination snapshot, such as a standalone SQLite database, when export is permitted and reproducible. Otherwise include a reason, exact readback query/output and the resulting verification limit. |
| `test-results.xml` | Results from the actual invocation, linked to test node IDs, command, source revision, run/trial and retained log. Do not count a JUnit summary as a recipient rerun of its tests. |
| `CROSSWALK.md` | Native artifact and field locations for each shared requirement, including differences, unavailable fields, transformations and information loss. Keep original enums and separate verdict dimensions. |
| `verify_export.py` | Independently implemented, inspectable portable verifier; standard library only where feasible. It verifies the package without executing the effect, contacting production, acquiring credentials or writing to the supplied destination. Document checks it cannot perform. |
| `evidence/` | Raw command logs, fault-injection/order evidence, writer-entry records, observer query/access evidence, source/configuration identities, native validator outputs and canonical commitment preimages/projections as applicable. Include fixture versus live-evaluation labels. |

The layout mirrors the evidence categories of the received sample, not its private implementation or exact outcome. Keep absence, redaction and unsupported mappings explicit. The recipient's filenames must not dictate Cognous runtime semantics.

## Integrity and reproducibility

1. Hash **every distributed payload file**, including README, crosswalk, verifier, test XML and raw logs. List file lengths, relative paths and SHA-256 values in `manifest.json`. Exclude the manifest itself to avoid a circular self-hash; publish the final archive digest separately. Keep any actual signature and signer verification separate from unkeyed hashing.
2. Freeze the archive after verification. Do not silently change files after hashing. Reject duplicate or unsafe paths, unexpected unlisted payloads, invalid JSON and commitment mismatches. Explicitly identify missing artifacts instead of omitting them from the evidence obligations.
3. Define the exact canonicalization algorithm and committed JSON projection for every payload, effect, authority and state digest. Retain its preimage or disclose why it cannot be reproduced. A balance/version digest may legitimately exclude resource identity; bind that identity explicitly elsewhere and document the projection.
4. For SQLite, export a consistent standalone snapshot with any required WAL changes incorporated; verify `PRAGMA integrity_check` and inspect through a read-only connection. Record how the snapshot was taken. A later recipient readback verifies the exported snapshot, not the original execution history or an external operational trust domain.
5. Pin runnable test sources, native schemas and semantic validators by repository URL/path/commit, with dependency versions and commands. Where sources cannot be shared, distinguish reported results from recipient-reproducible assertions and state the restriction.
6. Correlate fixture, proposal, authority consumption, original attempt, retry attempt, readbacks, native receipts and destination state. Check exact effect multiplicity and state transition. Preserve differences between invocation telemetry, database records and independently witnessed actions.
7. Run the verifier from a clean recipient-style copy. Record its actual output and source digest. Exercise a file-tampering control and a semantically contradictory snapshot control. Use explicit failure handling so optimized Python cannot disable required validation. A self-consistent manifest or receipt is not issuer authentication or proof of legitimate authority.

## Scope and comparison rules

Prepare D01/D03 first under the [bounded process](bounded-comparison.md); package D04 as a separate recovery trajectory when it is run. A prior external D04 sample does not advance the Cognous scenario verdict or satisfy its configuration checkpoint. Retain exact-version differences between illustrative examples and actual fixtures.

Keep these findings separate: package byte integrity, native schema/semantic validity, test execution, destination-state consistency, authority authenticity, observer independence and cross-system reconstruction. A local same-host readback is useful evidence with a declared trust boundary, not an independent external witness. A fixture PERMIT or invariant vector stays a fixture regardless of a native verification label.

Before the package is marked ready for return, confirm rights to each included byte, preserve original notices and exclude secrets, customer data, proprietary mechanisms and unauthorized third-party source. The supplied external bundle is review input; it is not imported into the public repository or automatically licensed by this process. Implement the Cognous verifier and export tooling independently unless reuse permission is established.

At phase 4, record the package identity, digest, verification outcome, retained location, missing checks and **READY TO SHARE** or **NOT READY** with reasons. Generation/readiness is distinct from sending: obtain an explicit instruction identifying the recipient/channel before transmission. Do not infer release, production or institutional authority from package acceptance.
