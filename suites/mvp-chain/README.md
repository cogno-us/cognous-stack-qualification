# mvp-chain suite (proposed)

Exact-candidate harness for the bounded OCS MVP chain: matched `$10` synthetic refund, Linux single host, Control Plane decision,
operation identity (journal mode), the real claim-provisioning API, route B `AtomicLocalControlPlaneExecutor`, a synthetic SQLite
destination, Replay and Evidence Pack reconstruction, and the pinned Verifier run in parallel over the raw Control Plane record.
It is **proposed**: Qualification owns the oracle and every verdict. Nothing here is an acceptance, a release decision or a
production claim; production HOLD is unchanged.

## What runs

| Step | Real call |
|---|---|
| decide + admit | `BoundedAuthorizationWorkflow.decide` with `OperationIdentityProfile` (the operation is admitted at decide) |
| claim | `AtomicLocalControlPlaneExecutor.provision_claim` -> `agent_control_plane.local_authority_effect.provision_local_execution_claim` |
| effect | `AtomicLocalControlPlaneExecutor(operation_identity=True).execute` on `OperationIdentityAtomicAuthorityEffectDestination` |
| export | `engine.producer_contract.export_execution_artifacts` |
| Replay | `agent_replay_bundle.importers.import_bounded_workflow` (Control Plane revision `CONTROL_PLANE_P2_REVISION`) |
| Evidence Pack | `import_manifest_reconstruction` + `validate_evidence_pack` |
| Verifier | pinned `cognous_verify.cli.main` in a subprocess: run A (record + proposal + manifest), run B (A + a harness-derived ledger from the SQLite `effects` table); exit codes, report bytes and hashes retained |

Fixtures are the Control Plane component's own `tests` package (as `suites/operation-identity` and `suites/runtime-authority` do) with
the proposal amount set to `10.0`. The destination is the atomic destination's `effects` table; no account-balance adapter is attached.

## Pins and refusal

Component checkouts are explicit environment paths: `MVP_CP_DIR`, `MVP_RUNTIME_DIR`, `MVP_REPLAY_DIR`, `MVP_PACK_DIR`, `MVP_ODES_DIR`,
`MVP_VERIFIER_DIR`, `MVP_MANIFEST_DIR`. Expected shas are in [`process/mvp-chain/tuple-pin.proposed.json`](../../process/mvp-chain/tuple-pin.proposed.json)
(proposed for Qualification's freeze; `MVP_PIN_FILE` selects another). Every test fails (nothing skips) when a variable is unset, a
HEAD differs from its pin, a checkout is not pristine (`tools/pristine_checkout.py`), pydantic is below 2.12, or a component module
is imported from outside its pinned tree.

The Control Plane revision is a run parameter: `MVP_CP_REVISION=<40-hex>` replaces the pin file's Control Plane sha for that run and the
override is recorded in `results.json`. Run unpatched with no override at `0a41faa9`; run a patched candidate by checking it out and
naming its sha.

The Evidence Pack trusts the Replay revision recorded by the *installed* `agent-replay-bundle` distribution. The suite creates no venv:
it writes a dist-info for the pinned Replay checkout (the `direct_url.json` an editable local install records) to a temporary directory
first on `sys.path`, then records the revision the Evidence Pack resolves and requires it to equal the pin.

## Observations versus verdicts

`_chain.py` only records raw observations (statuses, error types and codes, counts from an independent read-only SQLite connection,
hashes, Verifier exit codes and findings). `verdict.py` computes `PASS` / `FAIL` / `BLOCKED` / `NOT RUN` / `NOT APPLICABLE` as a pure function
of the observations and [`process/mvp-chain/expectations.proposed.v2.json`](../../process/mvp-chain/expectations.proposed.v2.json) (34 rows).
`v1` is kept unchanged: v2 differs in one row (`VER-03`), for the reason recorded inside v2. Expectations are never edited after a
result is seen; a change is a new file with a recorded reason. A row fails its pytest test unless `PASS` or `NOT APPLICABLE`: there is no
xfail, skip or relabelling. Differential rows (tampering, custody) are `BLOCKED` when the untampered control is not accepted, because
a refusal then cannot be attributed to the tamper.

Outputs (`MVP_RESULTS_DIR`, default a temp dir): `observations.json`, `results.json` (statuses, counts, expectations hash and git blob id,
tuple heads, override, `acceptance_declared: false`) and `artifacts/` (CP run record, proposal, export, bundle, pack, destination copy, every
Verifier report).

## Six negative controls

| Control | Rows | Exercised by |
|---|---|---|
| revocation, incl. approval withdrawal before effect | NC1-01..03 | grant revoked / approval withdrawn in the destination after claim issuance; resolver revoked before claim |
| ambiguous commit incl. lost acknowledgement | NC2-01..05 | `simulate='lost_ack'` (fault injection by this trusted harness, not the ingress), retry of the claim, `reconcile_claim`, reconcile route unavailable, export and Replay of the unknown outcome |
| duplicate effect | NC3-01..03 | consumed claim replayed, second claim for one decision, cap-2 renewal with the same operation id |
| unmediated path via the declared ingress | NC4-01..03 | **pluggable hook, see below** |
| evidence tampering | NC5-01..05 | substituted journal commitment, export naming another effect, Evidence Pack retained source, Verifier on an altered decision, destination row edited after the fact |
| custody failure | NC6-01..04 | journal events omitted, store directory absent at effect time, authority store unreadable at claim, export withheld |

### Ingress hook (Worker D1 supplies the ingress)

Set `MVP_INGRESS_MODULE` (and optionally `MVP_INGRESS_PATH`) to an importable module exposing `qualification_probe(context) -> dict`
(`context` = `control_plane_dir`, `runtime_dir`, `work_dir`) returning `attempted_surfaces`, `reached_surfaces` (must be empty),
`fixed_simulate` (`None`), `operation_identity_source` (`"persisted_decision"`) and free-form `details`. NC4-02 requires the attempted
surfaces to include `provision_claim`, `execute_claim_atomic`, `simulate`, `set_grant_status`, `set_approval_status`,
`raw_sql_destination_write`. With the module absent or without the function the scenario is `BLOCKED` and the three rows fail closed.
The contract is a proposal for D1 and Qualification to settle. The scenario also records, as information only (no row), which excluded
surfaces are reachable by direct in-process use of the components (the trusted-host limitation the ingress must exclude).

## Run

```bash
export MVP_CP_DIR=... MVP_RUNTIME_DIR=... MVP_REPLAY_DIR=... MVP_PACK_DIR=... MVP_ODES_DIR=... MVP_VERIFIER_DIR=... MVP_MANIFEST_DIR=...
MVP_RESULTS_DIR=out PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider suites/mvp-chain
```

## Known limits

- The destination ledger is the atomic `effects` table; there is no account balance adapter, so "matched" means amount `10.0 USD` on the Control Plane proposal.
- Evidence Pack tamper (NC5-03) drops a retained record from the pack's retained source; its effectiveness is only observable once Replay accepts the chain.
- Verifier run B uses a ledger derived by this harness; it is not a component artifact. Run A is the gated run.
- Single Linux host and a single process; no claim about concurrent writers, process kill or financial finality.
