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
tuple (the workflow reads it). Current proposed tuple: Control Plane `7a4bcd40` (main after the merged F3), Runtime `ec728da6`, Replay `ab421ad0`
(main after the merged Replay F3), Verifier `c0b8ba1f`, Action Manifest `fa170815`, hub `43c526eb` (ingress). **Evidence Pack and ODES are PENDING**
(null in the pin file, their re-pin PRs are not merged) and must be named by `MVP_PACK_REVISION` / `MVP_ODES_REVISION`; they are not guessed.
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
| unmediated path via the declared ingress | NC4-01..03, KL-01 | the real hub ingress (Unix socket), attacked as a dedicated client uid against a dedicated non-root ingress uid (developer opt-out: root ingress, uid 65534); see below |
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

## Ruling 4: lost acknowledgement (`test_ruling4_lost_ack.py`)

Six direct assertions added to the battery without touching expectations v1-v3 or any observation they read; the module drives its own flow
(`_chain.Ctx`) and fails, never skips, when the components are not the pinned tuple. After `simulate='lost_ack'`: the first result is
UNKNOWN, unacknowledged, `retry_eligible` False; a second execute with the same claim is denied (claim not usable, `attempted` False);
the destination holds exactly one committed effect by an independent read-only SQLite readback; `reconcile_claim` resolves it (applied, same
effect id, not retry eligible, nothing written); the second result's default `observed_state` `unknown` carries no observation and is
contradicted by the readback, so it is not an authoritative observation; and a fresh operation identity without new authority (no approval
re-binding, no renewal, same cap) commits no second effect and never reports `executed`.

## Ruling 5: supported-ingress ambiguous acknowledgement (`test_ingress_ambiguity.py`, row NC2-06, PROPOSED)

EVIDENCE LEVEL: SUPPORTED INGRESS. One valid proposal from the unprivileged client over the real hub ingress (`simulate=None`, request schema unchanged); the fault is owner-side only (`_ingress_fault_wrapper.py`, one Runtime post-commit seam). Row NC2-06 lives in `process/mvp-chain/expectations.proposed.v6.json` (the composed proposal: v3 rows byte-identical except NC4-03 from PR #222 and NC2-06 inserted after NC2-05; first proposed in PR #224's `expectations.proposed.v5-ingress-ambiguity.json`, byte-identical row). NC2-01..05 and ruling 4 remain EXECUTOR-LEVEL evidence (`simulate='lost_ack'`).

`MVP_FAULT_MODE` is a required, comma-separated token set for the wrapper (absent or unknown tokens: refuse to start). The product run uses `after_commit,bind_fresh`.

What the reuse part does and does not show:

- **Same bytes again** is refused `REPLAY` by the ingress request ledger. This is ingress-level evidence only; it never reaches the executor and says nothing about the destination.
- **A fresh request id with the same business content** is, without help, HELD at decide, because the synthetic approval binds exactly the request id `case-1`. A HELD request never reaches the executor, so that observation is not destination duplicate prevention. `bind_fresh` (owner side only, the wire is unchanged) builds the proposal with the approval-bound correlation id, so the fresh request is authorized, a second claim is provisioned, and the executor and `execute_claim_atomic` are called a second time. The row requires: executor calls 1 after the first request, 1 after the replay, 2 after the fresh request; the second result is `denied`, not attempted, not acknowledged, with `simulate` null; the fresh response is `refused` with `DUPLICATE_OPERATION` or `EXECUTION_DENIED`; the effect count stays 1; no new consumed claim exists. In the pinned tuple the second call is stopped inside the destination transaction by `authoritative effect budget exhausted` (the budget is checked before the operation-identity guard); the second claim remains `issued` and unconsumed. The operation-identity guard is not what stops it here.
- **Reconcile** runs on the FIRST claim only (`envelope.pickle` is written on the first executor call).

Negative controls (tests, each must FAIL NC2-06): hook disabled (`ack.hook_fired`); a wrapper forcing `simulate='lost_ack'` (the `simulate` is-null predicates); failure raised before the commit (`boundary.effect_count_after_first` and the ack/unknown predicates); a destination that allows a second commit (operation guard and record skipped and the budget un-spent from the second execute on; fails the second-request predicates; the second insert still collides on the deterministic effect id and ends `unknown` / `IntegrityError`, so the effect count stays 1); no `bind_fresh` (fails `reuse.executor_calls_after_fresh`).

**Composition:** `process/mvp-chain/expectations.proposed.v6.json` is the composition of PR #222's NC4-03 row (`expectations.proposed.v4.json`) and this NC2-06 row (PR #224's `expectations.proposed.v5-ingress-ambiguity.json`) over v3 as a new proposed version (38 rows, 37 mandatory). Select it with `MVP_EXPECTATIONS` until the suite default and the mandatory battery are moved by a separate, Qualification-owned change; v1-v5 are untouched. Proposal only; non-authorizing; release stays HOLD.

## Known limits

- The destination ledger is the atomic `effects` table; there is no account balance adapter, so "matched" means amount `10.0 USD` on the Control Plane proposal.
- Evidence Pack tamper (NC5-03) drops a retained record from the pack's retained source; it is only exercised once Replay accepts the chain.
- NC4 needs root (to start the ingress and the client as other uids; the acceptance workflow creates the dedicated users `mvp-ingress`, `mvp-client` and group `mvp-ipc`, named by `MVP_INGRESS_USER`, `MVP_CLIENT_USER`, `MVP_IPC_GROUP`) and `kernel.yama.ptrace_scope >= 1`; the unprivileged runner path is BLOCKED by design. `MVP_INGRESS_PROFILE=developer-optout` is the explicit local escape (root ingress, mode 666, uid 65534, no environment record) and makes the acceptance verdict INCOMPLETE. `yama.ptrace_scope` is absent on the observed kernel and recorded as unavailable.
- Approval revocation terminality (NC1-04) is expected to FAIL at the current tuple: the Runtime lets a revoked approval be reactivated. It must not be softened.
- Verifier run B uses a ledger derived by this harness; it is not a component artifact. Run A is the gated run.
- Single Linux host and a single process; no claim about concurrent writers, process kill or financial finality.
