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
`MVP_VERIFIER_DIR`, `MVP_MANIFEST_DIR`, `MVP_HUB_DIR` (the hub checkout holding the trusted-host ingress `tools/mvp_ingress`, now a pinned tuple member). Expected shas are in [`process/mvp-chain/tuple-pin.proposed.json`](../../process/mvp-chain/tuple-pin.proposed.json)
(proposed for Qualification's freeze; `MVP_PIN_FILE` selects another). Every test fails (nothing skips) when a variable is unset, a
HEAD differs from its pin, a checkout is not pristine (`tools/pristine_checkout.py`), pydantic is below 2.12, or a component module
is imported from outside its pinned tree.

Every component revision is a run parameter: `MVP_<NAME>_REVISION=<40-hex>` (`MVP_CP_`, `_RUNTIME_`, `_REPLAY_`, `_PACK_`, `_ODES_`, `_VERIFIER_`, `_MANIFEST_`, `_HUB_`)
replaces that component's pin-file sha for the run and is recorded under `overrides` in `results.json`. The pin file is the single source of the
tuple (the workflow reads it). Current proposed tuple: Control Plane `7a4bcd40` (main after the merged F3), Runtime `c5e97e87` (main after the merged Runtime F3, PR #144; pre-F3 `ec728da6`), Replay `ab421ad0`
(main after the merged Replay F3), Verifier `c0b8ba1f`, Action Manifest `fa170815`, hub `43c526eb` (ingress). **Evidence Pack and ODES**
were PENDING and are now named in the pin file: Pack `79ae34d9`, ODES `eae95dd3`. Replay, Pack and ODES Programme 2 profiles still name Runtime `ec728da6`; that is an open F3 candidate, not changed here.
To reproduce the earlier unpatched run: `MVP_CP_REVISION=0a41faa9...`, `MVP_REPLAY_REVISION=028f63d1...`, `MVP_PACK_REVISION=a3ebbb90...`.

**ODES is pin-checked but not exercised**: the chain never imports ODES (no schema validation or fixture of ODES runs here), so for ODES the "exact tuple"
is identity only. Replay and the Evidence Pack consume the evidence formats themselves.

The Evidence Pack trusts the Replay revision recorded by the *installed* `agent-replay-bundle` distribution. The suite creates no venv:
it writes a dist-info for the pinned Replay checkout (the `direct_url.json` an editable local install records) to a temporary directory
first on `sys.path`, then records the revision the Evidence Pack resolves and requires it to equal the pin.

## Observations versus verdicts

`_chain.py` only records raw observations (statuses, error types and codes, counts from an independent read-only SQLite connection,
hashes, Verifier exit codes and findings). `verdict.py` computes `PASS` / `FAIL` / `BLOCKED` / `NOT RUN` / `NOT APPLICABLE` as a pure function
of the observations and [`process/mvp-chain/expectations.proposed.v3.json`](../../process/mvp-chain/expectations.proposed.v3.json) (37 rows).
`v1` and `v2` are kept unchanged. v2 differed from v1 in `VER-03`; v3 differs from v2 in NC4-01..03 (rewired to the real ingress), NC2-02 and NC5-04 (tightened), and adds NC1-04, NC1-05 (revocation terminality) and KL-01 (known limitation); reasons are recorded inside v3. Expectations are never edited after a
result is seen; a change is a new file with a recorded reason. A row fails its pytest test unless `PASS` or `NOT APPLICABLE`: there is no
xfail, skip or relabelling. Differential rows (tampering, custody) are `BLOCKED` when the untampered control is not accepted, because
a refusal then cannot be attributed to the tamper.

Outputs (`MVP_RESULTS_DIR`, default a temp dir): `observations.json`, `results.json` (statuses, counts, expectations hash and git blob id,
tuple heads, override, `acceptance_declared: false`) and `artifacts/` (CP run record, proposal, export, bundle, pack, destination copy, every
Verifier report).

## Six negative controls

| Control | Rows | Exercised by |
|---|---|---|
| revocation, incl. approval withdrawal before effect | NC1-01..05 | grant revoked / approval withdrawn in the destination after claim issuance; resolver revoked before claim |
| ambiguous commit incl. lost acknowledgement | NC2-01..05 | `simulate='lost_ack'` (fault injection by this trusted harness, not the ingress), retry of the claim, `reconcile_claim`, reconcile route unavailable, export and Replay of the unknown outcome |
| duplicate effect | NC3-01..03 | consumed claim replayed, second claim for one decision, cap-2 renewal with the same operation id |
| unmediated path via the declared ingress | NC4-01..03, KL-01 | the real hub ingress (Unix socket), attacked as uid 65534; see below |
| evidence tampering | NC5-01..05 | substituted journal commitment, export naming another effect, Evidence Pack retained source, Verifier on an altered decision, destination row edited after the fact |
| custody failure | NC6-01..04 | journal events omitted, store directory absent at effect time, authority store unreadable at claim, export withheld |

### NC4: the real ingress (hub `tools/mvp_ingress`)

The earlier in-process hook (`qualification_probe`) is removed: it matched neither the delivered ingress (a Unix-socket server) nor the required
independence, and a self-reported probe could pass without any ingress. `_ingress.py` now starts `python -m tools.mvp_ingress.server` from the pinned hub
checkout on a fresh state directory (parent-chain rules of `BOUNDARY.md`: root-owned, non-writable ancestors), then, **as uid 65534 with no groups**
(root plus `setuid`, as D1's tests do), sends D1's adversarial inputs (reused as data, 232 bodies: simulate values, forbidden member names, hand-built claim,
authority-writer and claim-method names, malformed/oversized/duplicate/non-object inputs) through the declared client, and attempts direct open, sqlite write,
rename, chmod, `/proc/<pid>/mem` and `kill` against the state tree. `reached_surfaces` is computed from **owner-side observations**: content hashes of every
destination and authority table and the ingress ledger before and after the attack phase, state-tree stat, client uid and groups; ingress responses are recorded only.
Then one legitimate proposal is sent twice (expected: one effect, one consumed claim, then `REPLAY`). If the environment cannot run the client as a distinct
unprivileged uid (not root) the scenario is **BLOCKED with that reason, never PASS**. The workflow therefore runs the suite under `sudo`.
`simulate=None` and the operation-identity source are only **source-level assertions** (NC4-03: AST scan of the pinned hub source plus D1's own AST tests), labelled as such.
KL-01 records, as a known limitation and not a defect pass, that the trusted ingress process imports the Control Plane component's `tests` package (synthetic resolver
fixture) in-process; it is not client reachable and is not production authority. Only the tested configuration is observed (single host, uid 65534, kernel
and capabilities recorded); nothing here covers code running as the ingress uid or root.

## Run

```bash
export MVP_CP_DIR=... MVP_RUNTIME_DIR=... MVP_REPLAY_DIR=... MVP_PACK_DIR=... MVP_ODES_DIR=... MVP_VERIFIER_DIR=... MVP_MANIFEST_DIR=...
MVP_RESULTS_DIR=out PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider suites/mvp-chain
```

## Known limits

- The destination ledger is the atomic `effects` table; there is no account balance adapter, so "matched" means amount `10.0 USD` on the Control Plane proposal.
- Evidence Pack tamper (NC5-03) drops a retained record from the pack's retained source; it is only exercised once Replay accepts the chain.
- NC4 needs root (to drop to uid 65534); the unprivileged runner path is BLOCKED by design. `yama.ptrace_scope` is absent on the observed kernel and recorded as unavailable.
- Approval revocation terminality (NC1-04) was expected to FAIL at Runtime `ec728da6` (a revoked approval could be reactivated). It must not be softened. At Runtime `c5e97e87` (F3 PR #144) the expectation is unchanged; whether it passes is a Qualification result, not asserted here.
- Verifier run B uses a ledger derived by this harness; it is not a component artifact. Run A is the gated run.
- Single Linux host and a single process; no claim about concurrent writers, process kill or financial finality.
