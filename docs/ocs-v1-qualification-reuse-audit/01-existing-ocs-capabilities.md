# 01 Existing OCS capabilities

**Status: documentation-only analysis. Non-authorizing. Draft for Architect review. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.**

Nothing here authorizes a migration, approves a pin, selects or activates a record, or changes a qualification verdict. Implementation is not authorized. Labels: **SOURCE FACT** (read in the file), **REASONED INFERENCE**, **UNVERIFIED**. Nothing was executed; all test status is as recorded in the repository.

Each capability below has a row in [data/capability-matrix.csv](data/capability-matrix.csv) (IDs Q01 to Q31) and a class in [03](03-reuse-and-duplication-matrix.md).

## 1. What the repository is, for V1 purposes

It holds no registry code. It holds the qualification corpus (696 canonical scenarios, 162 suite-local claims), suites relocated from the owner repositories, an evidence and freeze toolchain, and a set of proposed MVP-chain oracles. It checks owner repositories out at pinned commits and overlays suites onto them. **SOURCE FACT**

The registry is not a subject yet. `cognous-ocs-registry` appears in no workflow, tool, test or suite here; it appears only in `docs/registry-v1-scope-assessment/`. **SOURCE FACT**

## 2. Capabilities by V1 scope item

### Five Runtime allowlists (F1a: actions, adapters, units; F1b: institutions, authority domains)

- `suites/v1-scenarios/test_scn_c11.py` varies one policy dimension at a time (`POLICY_DIMS`: institution, authority_domain, adapter, action, target_prefix, unit, max_amount). It swaps in a stricter policy and asserts refusal, zero destination effects and no recorded attempt, on Route A and Route B, with positive controls and a determinism rerun. All five in-scope allowlists are covered as refusal oracles. **SOURCE FACT**
- `suites/v1-probes/test_runtime_probes.py` repeats this at the executor level without the Control Plane, including a control that the in-scope operation executes. **SOURCE FACT**
- Not covered: values arriving from a registry record, superset and narrowing cases (the oracles only swap to a disjoint set), the empty-set case per allowlist, and the pre-construction deny-all path. **SOURCE FACT**

### Three Control Plane freshness bounds (status age, approval age, per-class status age)

- Pattern covered: `test_add_molt_verify.py` E3 (59 s authorized, 61 s `grant_status_stale_or_future`; per-item keys ignored), class bounds 5 s and 120 s, `operation-identity/test_freshness_profile.py` (stalled check refused, outage extension to 200 s with a signer), purpose-cache inclusive edge. **SOURCE FACT**
- Notable constraint found in E3: changing the class bound also yields `runtime_authority_approval_mismatch`, because the catalogue digest is approval-bound. A registry change to this value forces re-approval. **SOURCE FACT**
- Not covered: approval-age behaviour. `approval_max_age_seconds` appears in exactly one place, `process/adversarial/tests/test_t15_profile_forwarding.py:52`, as a constructor parameter checked for forwarding completeness. It is not exercised for freshness. **SOURCE FACT**

### Atomic Route B

- `test_local_authority_effect.py` and `test_worker21_atomic_authority_effect.py` cover invalidation before the transaction, expiry evaluated after the lock wait, claim, budget and effect committing together, process termination at transaction boundaries, concurrent same-claim and competing effects. Reusable harness pieces: `MutableClock`, `BarrierDestinationMixin`, `setup_case`, `setup_atomic`. **SOURCE FACT**
- They assert the authority boundary, not registry policy at it. The local policy check runs before the destination transaction (shown by C11 Route B and `test_w2_refusal_history.py`); no test asserts its placement or races a policy change against the transaction. This is GAP-G3-02 and R10 Options A/B/C are unimplemented. **SOURCE FACT**
- Route C is marked EXCLUDED / NOT INVOKED in `suites/mvp-applicability`, and `suites/mvp-d2-route-b` is not wired to CI. Both are usable as Route-B-only controls. **SOURCE FACT**

### Claim-carried effective-policy identity

- The Route B claim fixture carries `policy_versions`, `policy_state`, `policy_state_commitment` and `claim_commitment`. Tests refuse a changed policy-state version (`test_local_authority_effect.py`), a superseded policy state (`test_scn_c07.py`), a substituted binding including a widened policy (`test_scn_d02.py`), and an unadopted policy digest (`operation-identity/test_adapter_forwarding.py`). **SOURCE FACT**
- These bind Control Plane policy. No claim field or test carries the effective `LocalExecutionPolicy` or a registry record, selection epoch or activation identity. **SOURCE FACT**

### Authenticated selection and activation

- None in this repository. The nearest material is signed policy-revision supersession in `suites/wiki-derived/test_wp_d_manifest_change_control.py` and `test_wp_f_records_replay_policy.py` (L08-036). `suites/cognous-evidence-registry/chain/` has supersession and withdrawal for an on-chain claim registry, which is a different system and is not coverage. **SOURCE FACT**
- Registry-side behaviour is tested only by builder tests in `cognous-ocs-registry` (`test_r08_*`, `test_s05_equivalence.py`), which use a `FakeVerifier`. They are BUILDER_TESTED, not qualification evidence. **SOURCE FACT** (per the P1 plan)

### Revocation, expiry and rollback

- Authority level, well covered: `process/mvp-chain/expectations.proposed.v7.json` NC1-01 to NC1-05 (revoked before effect, approval withdrawn, revoked then reactivated stays refused), NC7-02/03 (expired claim, missing evidence); `process/adversarial` T07 (terminal revocation profile), T08 (revocation at each point of the commit sequence), T09 (expiry equality at T-1 µs, T and T+1 µs in three timestamp spellings); `suites/wiki-derived/test_wp_a_grant_lifecycle.py` (calls stop at first check after revocation; 60 effects then revoke). **SOURCE FACT** Several of these are builder proposals awaiting review.
- Rollback is characterized, not refused: T10 shows an atomic store rollback is undetected without an external anchor and asserts no REFUSE. `suites/outside-holder/test_witness_digest.py` rejects a shrunk or rewritten witness ledger against a held digest. **SOURCE FACT**
- Selection-level revocation, expiry, stale epoch and restore fence: none. **SOURCE FACT**

### Durable negative evidence

- `suites/_refusal_template.py` and `docs/refusal-test-template.md` define five legs: (a) no ledger row for the effect id, read through an independent read-only connection; (b) a refusal row naming the failed check and expected and observed input versions; (c) a positive control at the same enforcement point and policy version; (d) mutation, with the refusal writer disabled leg (b) must fail while the effect is still blocked; (e) provenance. **SOURCE FACT**
- `test_refusal_evidence.py` reconstructs every typed source field and rejects eleven substitution or loss mutations; `test_wp_c_budget_stop_recovery.py` D12-021 keeps sixty refusals durable across restart. Refusal rows are `hold`, never `deny`. **SOURCE FACT**
- A refusal never means expired, revoked or inactive: `classify_holders` returns `witnessed_refusals` and `unenumerated_authority_needing_containment`. **SOURCE FACT**
- Not covered: registry-code carriage as structured evidence, deny-all distinct from a policy-check denial, and a mutation proving a decision does not depend on message text. The mvp-chain README states error strings are recorded but not pinned. **SOURCE FACT**

## 3. Evidence, custody and reporting

| Mechanism | Where | Property that matters for V1 |
|---|---|---|
| Immutable writer | `tools/qualification_results.py:147-159` | Content-addressed path, open mode `'x'`; a path with different bytes raises "Evidence path collision". The dashboard re-hashes every file. This is the only place immutability is enforced in code |
| Run manifest | `schemas/run-manifest-v1.schema.json` | Telemetry only: `scenario_results` forced `[]`, observed state null, all three verdict dimensions forced `NOT ASSESSED`, release and production authorization forced false |
| Bounded trajectory v2 | `schemas/trajectory-evidence-v2.schema.json`, `tools/trajectory_contract.py` | Plan hash, per-file shas, per-case verdict from the existing set, `verdict_scope` fixed to "named local variant only" |
| V1 validation controller | `tools/v1_validation.py`, `requirements.json` (131 rows, 39 mandatory) | `PASS` only with adequate executed evidence; zero matches, a short `min` or a skip gives INCONCLUSIVE; selected verdict is PASS, FAIL or INCOMPLETE |
| Freeze and pins | `suites/_pins.py`, `freeze-manifest.json` (never edited), `refreeze-log.json` | Overlay entries, original pins never relabelled; a mismatched `from_sha` raises |
| Pre-registration | `process/release-gate/preregistration.json` | 127 append-only amendments; an amendment never turns a failed test into a known limit for the run in which it failed |
| Failure register, declared limits | `schemas/failure-register.schema.json`, `tools/declared_limits.py` | Re-statused, never deleted |
| Retention | `docs/qualification-dashboard-guide.md` | Compact manifests in Git; larger logs in expiring artifacts. A hash or URL does not preserve bytes |

Immutability elsewhere under `results/` is convention: no test or check forbids editing `results/v1-validation`, `serial`, `verifier-mutation` or `security-*`, and I found no verifier for their `SHA256SUMS*` files. **SOURCE FACT**

## 4. Status vocabulary (closed; no value is added here)

| Set | Values | Defined at |
|---|---|---|
| Case verdicts | PASS, FAIL, INCONCLUSIVE, NOT RUN, NOT APPLICABLE (`NOT EVALUATED` for human oversight) | `docs/execution-contract.md:31-37` |
| Workflow outcomes | PASS, FAIL, RUNNING, CANCELLED, INCONCLUSIVE, NOT RUN | `tools/qualification_results.py:13` |
| MVP-chain verdicts | PASS, FAIL, BLOCKED, NOT RUN, NOT APPLICABLE | `suites/mvp-chain/verdict.py:11` |
| Selected V1 verdict | PASS, FAIL, INCOMPLETE | `tools/v1_validation.py` (`verdict`) |
| MVP gate verdicts | ACCEPT, REJECT, INCOMPLETE (INCOMPLETE > REJECT > ACCEPT; `authorizes: false`) | `tools/mvp_acceptance_gate.py` |
| Crosswalk evidence_status | PASS_RECORDED, FAIL_RECORDED, BLOCKED, NOT_RUN, KNOWN_LIMIT_ASSERTED, COLLECTED_ONLY, NO_TEST, UNKNOWN | `method/validate_crosswalk.py:33-35` |
| Crosswalk existing_protection | ENFORCED_AND_EVIDENCED, IMPLEMENTED_NOT_QUALIFIED, PARTIALLY_ENFORCED, KNOWN_GAP, NOT_APPLICABLE, UNKNOWN | same |

`PASS_RECORDED` means a historical, developer-run, named case at the g8-r10 controller pins. It is not a PASS and does not transfer to Control Plane `7a4bcd40` or Runtime `c5e97e87`. The P1 plan also uses `BUILDER_TESTED`, an evidence label for registry-repository tests, which is not a verdict in this repository. **SOURCE FACT**

## 5. CI and test harness

- 70 workflows, about 7.5k lines; all use SHA-pinned actions and `contents: read`. 49 are delegated owner-repository suites (`<repo>--<name>.yml`): dispatch or call, inputs `source_revision` and `qualification_revision`, two checkouts, `tools/install_suite.py` overlaying relocated tests, hash-pinned dependency locks, and a mandatory `relocation-*` identity artifact. **SOURCE FACT**
- Templates for exact-revision composition: `operation-identity-profile.yml` and `outside-holder-profile.yml` (`workflow_call`, `control_plane_revision` and `runtime_revision` inputs). Controllers: `v1-validation.yml` (plan, freeze, aggregate), `mvp-acceptance.yml` (resolve, verify-checkouts, commit, gate). **SOURCE FACT**
- Only `catalog-validation.yml` and `qualification-dashboard.yml` run on every pull request; neither reads a docs directory listing. Nothing automatically gates a registry change, because all delegated workflows are dispatch or call only. **SOURCE FACT**
- Environment hazards that affect reuse: many suites hard-fail on unset checkout variables (`MVP_*_DIR`, `ADV_*_DIR`, `ARB_REFUSAL_*`); Runtime CI skips atomic tests when `agent_control_plane` is not on the path; `mvp-d2-route-b` and `mvp-d09` need pydantic 2.12 or later, but two of the locks pin 2.11.9; some `operation-identity` tests are designed to fail on specific pins. **SOURCE FACT**

## 6. Stale or contradictory repository statements (reported, not edited)

- `README.md` says 18 suite directories in one place and 20 in another; `suites/` holds 20. **SOURCE FACT**
- `README.md` says wiki-derived has 290 collected tests; `docs/test-inventory.md` rows W-I 64 and W-X 217 sum to 281. Unreconciled. **SOURCE FACT**
- The README quick start says the unit suite runs 413 tests; a local run of `python3 -m unittest discover -s tests` at this head ran 780 (OK, 3 skipped). The inventory's "main bf865632" measurement point is also not this head; the README itself tags these as pin-round-stale. **SOURCE FACT**
- `scenarios/catalog.json` records all 40 catalog rows as NOT RUN, while the crosswalk shows 27 as INCONCLUSIVE in controller g8-r10. The README explains this, but a reader taking statuses from `catalog.json` is misled. **SOURCE FACT**
- "Gate" means three different things here (OCS-1/2/3, V1-M/R/C, MVP G-00..G-15) and a fourth in the P1 plan (QG-01..14). **SOURCE FACT**
