# Lane C notes: cross-component and MVP scenarios (read-only, analysis only)

Outputs: `C-routes.jsonl` (40 rows), `C-suitelocal-rows.jsonl` (109 rows), this file.

## Method
- Revisions read (SOURCE FACT): Control Plane `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c`; Runtime `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f`; Qualification `998d39c5`; hub `/home/claude/cogno-us/cognous-open-control-stack` at `51c579a3` (present locally; the MVP tuple pins hub `c897266b`, which is not checked out); registry docs main `783ff59f`; registry clone `376e34b0`.
- Task 1: component route came from the V1 driver docstrings (`suites/v1-scenarios/test_scn_*.py`), `scenarios/coverage-map.json`, and `tools/run_matched_refund.py` (D01, D03, D04). Rule: CROSS if the observation needs two or more real components and no single-component driver exists; COMPONENT_LOCAL if the driver loads one component; BOTH if drivers exist at both levels; UNKNOWN if no driver exists (UNIMPLEMENTED, DEFERRED, or agent/human trials).
- Task 2: one row per distinct claim, grouped across parametrised tests. Oracle rows of `process/mvp-chain/expectations.proposed.v7.json` map to mvp-chain rows. Relocated suites are grouped coarsely (by claim cluster or by file); see Limitations.
- Task 3: grep for any consumer of the registry (`registry_consumer`, `apply_registry_overlay`) in Control Plane, Runtime and hub; read enforcement code at the cited lines.
- Tags embedded in `known_limitations`: `outcome:<CATEGORY>` and `gap:Gx`. `registry_family` is a list. UNMAPPED reasons are in `exclusion_impact`. Enforcement function paths are relative to the Control Plane (`cognous-control-plane/src/agent_control_plane/`) or Runtime (`cognous-execution-runtime/`) clone.

## Integration vs local (40 catalog scenarios, distinct ids)
| Route | Count | Scenario ids |
|---|---|---|
| CROSS_COMPONENT_INTEGRATION | 7 | D01, D07, D08, C12, C14, C22, C23 |
| BOTH | 16 | D02, D03, D04, D05, D06, D09, C01, C02, C03, C06, C07, C08, C09, C11, C13, C18 |
| COMPONENT_LOCAL | 4 | C04 (Index/evidence registry only), C10, C16, C17 |
| UNKNOWN (no driver) | 13 | A01-A06, H01, H02, C05, C15, C19, C20, C21 |

REASONED INFERENCE: BOTH means a component-level driver can exercise the claim, but the end-to-end claim still needs the assembled stack. Counting a scenario as "covered" by a component-local driver does not show the integration claim. Every coverage-map mapping is NOT RUN (SOURCE FACT: `scenarios/coverage-map.json`).

## Suite status classes (SOURCE FACT unless stated)
- CI-wired as dispatch/call only (no push/PR trigger): all delegated relocated-suite workflows (`cognous-*--*.yml`, `open-decision-*`), outside-holder-profile, operation-identity-profile, verifier-mutation-report, mvp-acceptance.yml, mvp-chain.yml. Only `catalog-validation.yml` runs on push/PR. No dispatched run of the MVP workflows exists in the corpus.
- Local-builder-only (no workflow): mvp-d09, mvp-d2-route-b.
- Synthetic-only: the MVP chain and ingress use a synthetic SQLite `OperationIdentityAtomicAuthorityEffectDestination` and `allow_synthetic_resolver=True` fixtures (Control Plane `tests/test_runtime_authority.py:24-50`; hub `tools/mvp_ingress/synthetic_host.py:117-143`). No real customer system, tenant or payment rail is involved.
- Inventory states: X-06 operation-identity PASS (50), X-07 outside-holder PASS (17 at main; inventory state only), X-08 verifier-mutation NOT_RUN_HERE, X-09 relocated overlays ENV (5,763 collected). The inventory page is "an inventory, not a result".

## G3 candidates (registry policy would need to bind to an enforcement boundary)
Finding that frames all of them (SOURCE FACT): there is no consumption path from the registry to any enforcement boundary today. `registry_consumer/consumer.py:270` `apply_registry_overlay` (effective = caller intersect registry, for allowed_actions/adapters/units only) has no caller in Control Plane, Runtime or hub (grep, three repos), and `s04-implementation.md` section 8 says nothing calls it. The Qualification repo has no reference to the OCS Registry (grep). It is an optional overlay profile; making participation mandatory would be a different, unauthorized profile.

| Candidate | What the boundary enforces | Where selected policy would be consumed | Consumption path today | Catalog scenarios |
|---|---|---|---|---|
| F1a-F1d LocalExecutionPolicy | Allowed actions/adapters/units/institutions/domains/targets and amount/effect ceilings, via `LocalExecutionPolicy.check` (Runtime `engine/safe_executor.py:359,410`) | Constructor of `LocalExecutionPolicy` passed to `AtomicLocalControlPlaneExecutor` (`engine/atomic_local_control_plane_executor.py:14`) | None. Values are host literals: hub `synthetic_host.py:126-130` (max_amount=1000, max_effects=1), `suites/operation-identity/_oi_flow.py:93` | D02, C01, C02, C11, C18 |
| The same, at the transaction boundary | The policy check runs OUTSIDE the transaction (`atomic_local_control_plane_executor.py:69`; transaction opens at `local_authority_effect.py:798`); `_validate_claim_state` (`:675`) checks grant, approval, policy-state and evidence ROWS but not the policy sets | R10 Options A (re-evaluate in-transaction) or B (bind an immutable evaluation/selection identity, revalidate at commit); C (clamp claim expiry) is a stopgap | All UNIMPLEMENTED; each needs a successor local-authority-effect profile in both repos (R10 feasibility doc). Route A cannot be closed. Everything UNQUALIFIED | D02, C11 |
| F5 ActionClass / RuntimeAuthorityProfile | Decision-time authority declarations, including `max_status_age_seconds` (`runtime_authority.py:87`), `requires_revocation_assurance` (`:91`, hold at `:356`) | Profile passed at workflow construction (`bounded.py:1261`; hub `synthetic_host.py:120-124`) | None; fixture data. Decision-time only | D07, C01, C14 |
| F4 freshness bounds | Spans Control Plane constructor arguments (`ObservationPolicy` `bounded.py:411`, observation_policy_missing hold `:1858,:1901`) and Runtime evidence-row `max_age_seconds`. Source comment at `bounded.py:1782-1784` says the window is narrowed, not closed | Both ends; cross-component | None. D1 is OPEN | D03 (stale evidence), C07 |
| F7 dedupe/replay window | Selected route B destination has no TTL (`operation_identity_destination.py:43-49`); F7 not engaged. D12 OPEN | n/a | n/a | D04, C09 |
| F6 agent permission allow-list | `PermissionSystem` is used only by the legacy AgentEngine, which executes nothing (`engine/engine.py:39`) | none effect-bearing | No effect-bearing consumer. D5 OPEN | A-series (UNKNOWN) |
| F3 size/depth/timeout budgets | Admission limits 1 MiB, depth 32, 10000 nodes (`safe_executor.py:147`) | module constants | None | C10, C16 |

REASONED INFERENCE: nothing in the corpus makes registry-managed configuration REQUIRED. All policy values are host literals or test fixtures. REQUIRED would arise only if a release profile mandated registry participation. Beyond that, F1a-F1d, F4 and F5 are BENEFICIAL (central governance of host literals) and carry G2 and G3 gaps.

Open items touching these rows, not resolved here: D1, D5, D6, D12 and the 32 UNRESOLVED S02 rows. Hub ingress rows are UNMAPPED because S02 covers only Runtime and Control Plane.

## MVP suite status caveats
- All MVP expectations are PROPOSED (Qualification owns the oracle `expectations.proposed.v7.json`: 42 rows, 41 mandatory, KL-01 non-mandatory; not frozen). Evidence status for mvp-chain, mvp-d09, mvp-d2-route-b and mvp-applicability is NOT_RUN. Nothing is recorded as passed.
- The 260-entry mandatory battery inventory is not 260 claims: the 41 mandatory oracle rows are the distinct governance claims; kwflow (183 tests) substantiates NC4-03, AMB-01..06 substantiates NC2-06, and 16 route-B mediation entries come from mvp-d2-route-b.
- mvp-d09 is pinned to pre-F3 Runtime `ec728da6`; it does not describe `c5e97e87` (README pin note).
- Stale documentation: `suites/README.md` says one mvp-d2-route-b test fails by design (approval revocation is reversible). The suite README says the reversible-characterisation test was retired at `c5e97e87`; `local_authority_effect.py:540-544` makes approval revocation terminal at `c5e97e87`. Whether the terminal test passes is a Qualification result: UNVERIFIED.
- Five `test_REACHABLE_*` tests pass when a hole exists (forged claim, caller-chosen operation id, caller-controlled simulate, public authority writers, raw SQL). They are KNOWN_GAP evidence, not protection. Mitigation is the ingress boundary (NC4), not a registry parameter.
- No MVP oracle row exercises a LocalExecutionPolicy denial (grep). Policy denial is covered only by the relocated `test_w2_refusal_history.py::test_atomic_policy_denial_has_durable_typed_failure_record` (adapter dimension) and by v1-scenarios `test_scn_c11`.
- Verifier mutation: retained run-5 (`results/verifier-mutation/run-5-0a43a7f0/`) used verifier `0a43a7f0`, not the tuple verifier `c0b8ba1f`; intended codes were frozen post-hoc after run 1; X1 108/109, H4 229/230; B/F/R6 are expected-accept classes.
- Naming collision: `cognous-evidence-registry` is the BitRep/Index attestation trust registry, not the OCS Registry. Its rows are UNMAPPED. The hub's `ocs-registry-record/0` is a separate scanner-record profile.

## Limitations
- Cloned nothing; no suites run. Evidence statuses come from inventory text, workflow metadata, retained result files and source reads only.
- Not cloned, so unread: Replay, Evidence Pack, ODES, Exchange, Verifier, BitRep source. Their enforcement functions read "repo not cloned"; relocated test copies were read by name and docstring, so those rows are REASONED INFERENCE or UNVERIFIED.
- Relocated suites are grouped coarsely (hub and Runtime relocated rows are partly grouped by file, with wildcard test ids in a few rows). The row count (109) is claim clusters, not an exhaustive per-claim enumeration; hub paired-request, worker21 and Runtime atomic rows are the finest-grained.
- Hub read at `51c579a3`, not the tuple pin `c897266b`. Control Plane `7a4bcd40` and Runtime `c5e97e87` match the heads; older builder statements cite other revisions (CP `fd0d5e0`, `0a41faa9`, Runtime `ec728da6`, `6bfb77ee`).
- Per-scenario protection analysis is Lane B's; route classification here rests on driver docstrings, not on running the drivers.
- The enumerated rows contain no customer, healthcare or financial validation claims; none are made.
