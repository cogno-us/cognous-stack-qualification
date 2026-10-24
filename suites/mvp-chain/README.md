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
tuple (the workflow reads it). Current proposed tuple (PROVISIONAL, UNQUALIFIED; see `process/mvp-chain/tuple-pin.proposed.json`, which is the single source): Control Plane `7a4bcd40`, Runtime `c5e97e87` (main after the merged Runtime F3, PR #144; pre-F3 `ec728da6`), Replay `40012b8c`, Evidence Pack `7b9511f2`, ODES `1a5e1d30`, Verifier `c0b8ba1f`, Action Manifest `fa170815`, hub `c897266b` (ingress and `tools/mvp_env_record/capture_env_record.py`). Replay, Pack and ODES are re-tied to Runtime `c5e97e87` at these pins.
To reproduce the earlier unpatched run: `MVP_CP_REVISION=0a41faa9...`, `MVP_REPLAY_REVISION=028f63d1...`, `MVP_PACK_REVISION=a3ebbb90...`.

**ODES is pin-checked but not exercised**: the chain never imports ODES (no schema validation or fixture of ODES runs here), so for ODES the "exact tuple"
is identity only. Replay and the Evidence Pack consume the evidence formats themselves.

The Evidence Pack trusts the Replay revision recorded by the *installed* `agent-replay-bundle` distribution. The suite creates no venv:
it writes a dist-info for the pinned Replay checkout (the `direct_url.json` an editable local install records) to a temporary directory
first on `sys.path`, then records the revision the Evidence Pack resolves and requires it to equal the pin.

## Observations versus verdicts

`_chain.py` only records raw observations (statuses, error types and codes, counts from an independent read-only SQLite connection,
hashes, Verifier exit codes and findings). `verdict.py` computes `PASS` / `FAIL` / `BLOCKED` / `NOT RUN` / `NOT APPLICABLE` as a pure function
of the observations and [`process/mvp-chain/expectations.proposed.v7.json`](../../process/mvp-chain/expectations.proposed.v7.json) (42 rows, 41 mandatory, including NC4-04 and NC7-01..03; the default of `conftest.py`; `MVP_EXPECTATIONS` selects another file such as v3 or v6). v7 is built on v6 (38 rows, 37 mandatory), which is the builder's composition of the v3 rows with the NC4-03 row of PR #222 and the NC2-06 row of PR #224 (kept here as composition provenance); v7 changes NC4-03 again and adds NC4-04 and NC7-01..03. All of these are proposals that Qualification owns and has not frozen.
`v1` and `v2` are kept unchanged (as are v4 and v5, the two single-row proposals). v6 differs from v3 only in NC4-03 (changed) and NC2-06 (added). v2 differed from v1 in `VER-03`; v3 differs from v2 in NC4-01..03 (rewired to the real ingress), NC2-02 and NC5-04 (tightened), and adds NC1-04, NC1-05 (revocation terminality) and KL-01 (known limitation); reasons are recorded inside v3. Expectations are never edited after a
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

## Required controls NC7-01..03 (expectations v7, PROPOSED)

Architect ruling Q2. Scenario `nc_authority_gates` (in `_chain.py`) drives the real route-B chain (Control Plane workflow, `AtomicLocalControlPlaneExecutor`, operation-identity atomic SQLite destination) and records raw observations; the rows in `process/mvp-chain/expectations.proposed.v7.json` compute their verdicts from them.

* NC7-01: unauthorized execution (forged claim id; a decision that is not `authorized`) is denied, not attempted, zero effects.
* NC7-02: stale or mismatched authority (expired claim, authority advanced after the claim, resolver revision changed before the claim, envelope amount or grant revision mismatch) is refused with zero effects.
* NC7-03: missing, invalid-state or expired evidence, and evidence missing at claim issuance, does not permit execution (zero effects).
* Every row also requires the control case to execute exactly one effect, so a refusal cannot pass because nothing works at all.

v7 is v6 plus these three rows (42 rows, 41 mandatory); v1-v3 and v6 are unchanged. Error strings are recorded but not pinned. Scope: the executor-level gates only; true OS-level process-kill recovery is UNQUALIFIED (synthetic fault injection only). Test inventory (260 battery entries) is not the number of unique governance claims (41 mandatory rows).

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

**Composition:** `process/mvp-chain/expectations.proposed.v6.json` is the builder's composition (a rows-from-two-branches merge, not a Qualification-composed or frozen oracle) of PR #222's NC4-03 row (`expectations.proposed.v4.json`) and this NC2-06 row (PR #224's `expectations.proposed.v5-ingress-ambiguity.json`) over v3, as a new proposed version (38 rows, 37 mandatory). This composition is provenance: the oracle in force, the default of `conftest.py` and of `process/mvp-acceptance/mandatory-battery.proposed.v1.json`, is `expectations.proposed.v7.json` (42 rows, 41 mandatory; v6 plus NC7-01..03, with NC4-03 changed and NC4-04 added), where NC2-06 is the oracle-row entry `test_mvp_chain.py::test_row[NC2-06]` (not a test of `test_ingress_ambiguity.py`); the six tests of `test_ingress_ambiguity.py` and every test of `test_kwflow.py` are listed there as supplementary entries (they are not oracle rows). v1-v5 are untouched. Proposal only; Qualification owns and freezes the oracle; non-authorizing; release stays HOLD.

## Known limits

- The destination ledger is the atomic `effects` table; there is no account balance adapter, so "matched" means amount `10.0 USD` on the Control Plane proposal.
- Evidence Pack tamper (NC5-03) drops a retained record from the pack's retained source; it is only exercised once Replay accepts the chain.
- NC4 needs root (to start the ingress and the client as other uids; the acceptance workflow creates the dedicated users `mvp-ingress`, `mvp-client` and group `mvp-ipc`, named by `MVP_INGRESS_USER`, `MVP_CLIENT_USER`, `MVP_IPC_GROUP`) and `kernel.yama.ptrace_scope >= 1`; the unprivileged runner path is BLOCKED by design. `MVP_INGRESS_PROFILE=developer-optout` is the explicit local escape (root ingress, mode 666, uid 65534, no environment record) and makes the acceptance verdict INCOMPLETE. `yama.ptrace_scope` is absent on the observed kernel and recorded as unavailable.
- Approval revocation terminality (NC1-04) was expected to FAIL at Runtime `ec728da6` (a revoked approval could be reactivated). It must not be softened. At Runtime `c5e97e87` (F3 PR #144) the expectation is unchanged; whether it passes is a Qualification result, not asserted here.
- Verifier run B uses a ledger derived by this harness; it is not a component artifact. Run A is the gated run.
- Single Linux host and a single process; no claim about concurrent writers, process kill or financial finality.

## NC4-03 predicate v5 (independent Q1 review; PROPOSED, builder-prepared)

Narrowly scoped source-aware additions to `_kwflow.py` (no taint-analysis subsystem, no ingress change, `tools/mvp_ingress` untouched):

1. literal-only protected keywords `attempt_id`, `budget_id`, `expires_at`, `decision_input_commitment`, `decision_input_profile_version`, `now` (only `now=host.now` is accepted) and the RuntimeProposal keys `evidence_refs`, `risk_metadata`, `run_id`, `expires_at`, `not_before`, `expected_side_effects`, `tenant_id`;
2. rule `AUTHORITY_OBJECT_MUTATION`: attribute stores, `setattr`, `object.__setattr__` on non-self objects (including in helper functions); `DYNAMIC_PROPOSAL_CONSTRUCTION` (`model_validate`, `model_construct`, `vars`) and `DYNAMIC_ATTRIBUTE_ACCESS` (`__class__`, `__dict__`);
3. rule `POSITIONAL_NON_LITERAL` for `ExecutionOperation`, `ExecutionEnvelope`, `execute`, `provision_claim`;
4. rebinding by import-as, match capture, except-as and def/class of the tracked names;
5. separate recursive tree check (`INGRESS_TREE_FILE_LIST`: exactly 8 regular files incl. `BOUNDARY.md`, no directory, symlink or extension module; `INGRESS_TREE_DIGEST`); the `*.py` digest `ea37100d...` that the pins bind is unchanged;
6. `ast_digest` pins carry `ast_digest_python` and are honoured on CPython 3.13 only (fail closed elsewhere), the observation records the interpreter;
7. pin prose: `request_id` flows via `correlation_id` into the proposal commitment and is not among the 14 names.

Every evading mutant of the review has a negative test (`test_v5_evading_mutant_is_rejected_by_its_source_aware_rule`, pins re-based so that only the new rule decides) and the unmodified ingress still passes. Not covered, not claimed: see `limitations.nc4_03_not_covered_not_claimed` in expectations v7.
