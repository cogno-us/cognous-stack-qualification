# cases-host.md - frozen case specification FC-H1, FC-H2, FC-H3a, FC-H3b (OCS-F3-Q240-BOUNDED-QUALIFICATION, host_profile_digest)

Author: Worker B, DRAFT PHASE (nothing executed; sources read, `py_compile` and `pytest --collect-only` only). Same session lineage as the lead: NOT independent; technical qualification evidence only.
Code under spec: `/tmp/claude-0/work/bq/harness/test_bq_host.py` (imports read-only `d1_lib.py` sha256 5ec947ba..., and `orig_harness.py`). Test names: `test_FC_H1`, `test_FC_H2`, `test_FC_H3a`, `test_FC_H3b`.
Subject: Control Plane 739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69 (pristine tree `/tmp/claude-0/work/src/cp-739efe7`, `PYTHONPATH=<cp>/src`); Registry pin a40fe755 (`OCS_REGISTRY_PIN_DIR`, `OCS_REQUIRE_REGISTRY_PIN=1`); Python 3.11.18; env as D-1 `run_d1.sh` (`D1_CP_ROOT`, `D1_EVIDENCE_DIR`, `F3_EVIDENCE_DIR`, `D1_LABEL`).
Source citations below are CP 739efe7 `src/agent_control_plane/...` read from the pristine tree.

## 0. Conventions (apply to all four cases)

- Instrument: complementary binding diff = leaf diff of the PERSISTED decision binding (read from the store the subject wrote) vs the binding a scratch LIVE world genuinely mints (`d1_lib.live_binding`, a real `decide` in a fresh scratch store, same fixtures and clock), split by `d1_lib.split_diff` into base diff (outside `runtime_authority.effective_configuration`) and ECB diff (inside). D-1 decision rule: "isolated end-to-end" iff base diff == [] and ECB diff == {ecb.digest, ecb.members.host_profile_digest}; otherwise "joint". The candidate's `configuration_binding_status` is evidence only (rows `E*`), never an oracle.
- Evidence rows (`$D1_EVIDENCE_DIR/d1_evidence.jsonl`, one row per assertion, every row has `case`, `assertion_id`, `check`, `expected`, `observed`, `result`):
  `PRECONDITION_PASS/FAIL` (id `*-P*`); `CHECK_PASS/FAIL` (gating, ids `*-C*` controls and `*-A*` assertions, `gating=true`); `OBSERVATION` (`gating=false`, ids `*-E*`, evidence-only, `result` MATCH/DIVERGE, never part of a verdict); `BLOCKED`; `CLASSIFICATION` (H3a, H3b; H1/H2 carry the classification inside observation rows `FC-H1-E04`, `FC-H2-E03`); one `PREFLIGHT` row per session.
- BLOCKED rule (frozen): any failing `P*` row, an unissuable control claim (FC-H1-P04), or any unhandled exception in a case body writes a `BLOCKED` row (raw exception type, text and traceback retained) and fails the test hard. A BLOCKED case is NOT interpreted and is corrected only by a versioned successor.
- A failing `C*`/`A*` row against the pristine subject is an ADVERSE FINDING retained as observed; it is never revised after the fact.
- Expected values are hard-coded literals in the code and listed below. The only computed oracles are the harness's own independent sha256 commitments (`own_commit`, same as D-1) used in preconditions, never to produce an expected value of an assertion from an observed one.
- Not done by any case: no guard disabled/patched/bypassed, no store write or graft, no private attribute read (only `configuration_binding_status`, `decide`, `execute`, `materialize_local_execution_claim`, constructors), no network, only the D-1 clock patch (`H.patch_clock`). Synthetic data only.
- Shared fixture facts: F5 world = `d1_lib.f5_world(t1, reg)` (Registry r08-v2 class-age selection for class `synthetic-irreversible`, host class irreversible, `max_status_age_seconds` = t1, no freshness, no policy_binding); action id `urn:cognous:action:refund-issue-routine-v1`; approval bound to the EFFECTIVE profile at mint (`f5_mint`), NOT re-issued unless a case says so.

## 1. Exact reason / message strings frozen (derived from source)

| Where | String | Source |
|---|---|---|
| Execute, durable `EffectTimeRefusal.reasons` for any base-silent binding difference | `["authorization_binding_changed"]` | `bounded.py:1690-1693` (set only when no other reason exists) |
| Execute, refusal vocabulary | `runtime-authority-reasons/0.1` | `bounded.py:1707`, `vocabulary_for` |
| Execute, exception text | `authorization-critical inputs changed before effect` | `bounded.py:1711` |
| Execute, H3a guard-first reason | `["runtime_authority_approval_mismatch"]` (D-1 Q3-E1 literal) | `runtime_authority.py:332-335` |
| Claim issuance, exception text (FC-H1) | `authorization-critical inputs changed before claim issuance` (type exactly `PermissionError`) | `local_authority_effect.py:455-458` |
| Claim issuance, durable refusal | NONE. The claim path does NOT name `authorization_binding_changed` anywhere: no `EffectTimeRefusal`, no reason code in the exception text. The lifecycle `_resolve` (`registry_governed_lifecycle.py:271-285`) returns no reasons on a member mismatch (the code is only added when the stamped extension equals the persisted one, `:278`), so the only artefact of the refusal is one `ResolutionCheck` (stage `claim`, reasons `[]`) plus check events, written by `_record_check` (`local_authority_effect.py:451`, `bounded.py:1327`, `record_resolution_check` `:624-660`) before the raise | as listed |

Frozen reading: the claim leg refuses through the generic base comparison `current != decision.binding`; the attribution to `host_profile_digest` rests on the complementary diff (rows `FC-H1-A01/A02`), not on any reason string.

## 2. FC-H1 - host_profile_digest, CLAIM ISSUANCE leg, F5 class-age masked-host world

**Purpose.** Show on the D-1 H1 world (host class age 60 -> 61, masked by Registry 10, approval not re-issued) that a rebuilt workflow whose ONLY live difference is the host profile refuses to issue a local execution claim for the previously authorized decision, with the base binding unchanged and the ECB diff exactly {digest, host_profile_digest}, and that an unperturbed world issues exactly one claim.

**Validity preconditions (any failure => BLOCKED, not interpreted).**
P01 control world minted `authorized`; P02 `p.action_id == urn:cognous:action:refund-issue-routine-v1`; P03 control live world mints `authorized`; **P04 the control claim is issued on this world (frozen rule: if the control claim cannot be issued the case is BLOCKED, raw exception type/text recorded; the control is never weakened)**; P05 perturbed world minted `authorized`; P06 host class ages `[60, 61]`; P07 host dumps differ in exactly `actions.urn:cognous:action:refund-issue-routine-v1.max_status_age_seconds`; P08 effective profile dumps equal; P09 independent commitments of the effective dumps equal; P10 independent commitments of the host dumps differ; P11 effective class age `[10, 10]`; P12 live world with the edited host mints `authorized`; P13 `catalogue_digest` equal across (persisted vs live), `effective_profile_digest` equal across, persisted `catalogue_digest` == `own_commit(effective dump)` (all `[true, true, true]`).

**Steps.**
1. Control world `h1c`: `f5_world(60,10)`, `f5_mint`; restart identical host (`f5_flow`); live-world diff (scratch); ONE call `materialize_local_execution_claim(flow, p, persisted_decision, now=NOW, claim_id="bq-fc-h1-control")` (supported public interface, no `policy_binding`, no `expected_*`); store snapshot before/after.
2. Perturbed world `h1p`: `f5_world(60,10)`, `f5_mint`; build host2 (age 61); rebuild the workflow over the same store with host2, approval NOT re-bound; independent preconditions; live-world diff (scratch) BEFORE touching the store.
3. ONE call `materialize_local_execution_claim(flow2, p, persisted_decision, now=NOW, claim_id="bq-fc-h1-perturbed")` with store snapshots (`run.json` read, never written by the harness) and destination snapshot before/after.
4. Evidence-only restoration control: rebuild with the original host over the same store and issue `bq-fc-h1-restore`.

**Assertion inventory (expected values hard-coded).**

| id | statement | expected |
|---|---|---|
| FC-H1-C01 | control live binding diff, base | `[]` |
| FC-H1-C02 | control live binding diff, ECB | `[]` |
| FC-H1-C03 | `verify_local_execution_claim(control claim)` | `True` |
| FC-H1-C04 | `[claim.decision_id, claim.claim_id]` | `[<minted decision id>, "bq-fc-h1-control"]` |
| FC-H1-C05 | `claim.authorizing_by_possession` | `False` |
| FC-H1-C06 | `[claims issued, destination calls, destination snapshot unchanged]` | `[1, 0, True]` |
| FC-H1-C07 | control claim new rows `refusals/attempts/decisions` | `{"refusals":0,"attempts":0,"decisions":0}` |
| FC-H1-A01 | perturbed base binding diff | `[]` |
| FC-H1-A02 | perturbed ECB diff (sorted) | `["runtime_authority.effective_configuration.digest", "runtime_authority.effective_configuration.members.host_profile_digest"]` |
| FC-H1-A03 | exception type raised by claim issuance | `"PermissionError"` (row also records `type(exc) is PermissionError`) |
| FC-H1-A04 | claim object returned is None (no claim emitted) | `True` |
| FC-H1-A05 | exception text | `"authorization-critical inputs changed before claim issuance"` |
| FC-H1-A06 | text contains `authorization_binding_changed` | `False` |
| FC-H1-A07 | new durable refusal rows (`refusals` delta) | `0` |
| FC-H1-A08 | new attempt rows | `0` |
| FC-H1-A09 | `decisions/observations/reconciliations/closeouts` deltas | all `0` |
| FC-H1-A10 | `[destination calls, destination snapshot unchanged]` | `[0, True]` |
| FC-H1-A11 | top-level `run.json` keys that changed, minus `{check_events, input_time_floors, resolution_checks}` | `[]` |
| FC-H1-A12 | `resolution_checks` delta | `1` |
| FC-H1-A13 | `[stage, reasons]` of the new resolution check | `[["claim", []]]` |
| FC-H1-A14 | persisted decision after the refusal equals the decision before | `True` |

Evidence-only (never gating): E01 control classifier `bound`; E02 raw control claim type and bookkeeping; E03 perturbed classifier `mismatch`; E04 raw bookkeeping, base/ECB diffs and classification string; E05 restoration control issues a claim on the same store with the original host (`issued`).

**Failure conditions.** Any `C*/A*` row FAIL; any `P*` FAIL or unhandled exception => BLOCKED (not a FAIL of the subject). A02 failing with a non-empty base diff means the world is not isolating (label joint, stop). A12/A13 are source-derived (medium-high confidence: `_record_check` runs before the raise) and are bookkeeping facts, not the member claim; a failure of A12/A13 alone does not by itself contradict A01-A11 but is retained as observed.

**What it does / does not establish (six dimensions).**
- functional correctness: control world issues exactly one valid claim (C01-C07) on the F5 world. Does not establish claim content correctness beyond `verify_local_execution_claim` and decision binding.
- member sensitivity: with A01/A02/A03-A10 passing, the claim comparison refuses on a diff confined to `host_profile_digest` (and the derived ECB `digest`) on the LIVE side. Not shown: sensitivity of the comparison to other members on this leg (not in scope).
- guard-order evidence: claim path runs `_resolve(stage="claim")` (base guards incl. approval guard, then ECB) before the generic comparison; base reasons empty and base diff empty places the refusal at the ECB step. The claim path does not run `_gl_revalidate`/selection re-verification (`local_authority_effect.py:442-458`); that is source reading, not shown by a row.
- end-to-end refusal: yes for the claim leg (no claim object, no durable refusal by design); NOT an execute-leg or pin-export statement.
- independent isolation: NO. Same session lineage as the lead, same fixture family and helper library as D-1, n=1 world, one workflow family; an independent owner is not established.
- contract coverage: touches only the claim leg for host_profile_digest on class-age. Does not cover `provision_local_execution_claim`, `policy_binding` claim variants, other workflow families, pin-export, other members.

**Evidence rows written.** `PREFLIGHT`; `FC-H1` rows `FC-H1-P01..P13`, `C01..C07`, `A01..A14`, `E01..E05` (E05 expected `issued`); `BLOCKED` only on failure. Note: classification string (`isolated end-to-end` / `joint`) is in row `FC-H1-E04`.

## 3. FC-H2 - second masked-host workflow, EXECUTE (GovernedClassUnreadableWorkflow)

**Purpose.** Repeat the D-1 H1 pattern on a different workflow family, hook and Registry family: class-unreadable (Registry r08-v5 `f5-action-class-unreadable-policy`, hook `registry_f5_class_unreadable_governance.py:336`, masking `compose_unreadable` `:146-151`), where a host `on_unreadable` edit is masked by a Registry narrowing, and show the refusal and the diff attribution.

**Fixture.** Host profile (shape of the developer fixture): scoped action class `synthetic-reversible` (`irreversible=False`, `max_status_age_seconds=60`, `on_unreadable` = world value), a second action `urn:cognous:action:refund-issue-high-v1` class `synthetic-irreversible` (`irreversible=True`, `on_unreadable="refuse"`; the irreversible class is already `refuse`, so `host_class_defect` does not reject it; the D-1 class is NOT reused). Registry r08-v5 selection names class `synthetic-reversible` -> `refuse` (operation `refund-issue-unreadable`, scope tenant/institution/domain of the manifest). Mint under host `bounded_tolerance` (effective `refuse`), approval bound to the effective profile; rebuild with host `refuse` (effective `refuse`, identical), approval NOT re-issued.

**Validity preconditions (any failure => BLOCKED; if the edit is not masked the case is BLOCKED, not interpreted).**
P01 control world minted `authorized`; P02 action id literal; P03 control live world mints `authorized`; P04 perturbed world minted `authorized`; P05 scoped class irreversible `[false, false]` in host1/host2; P06 host scoped `on_unreadable` `["bounded_tolerance", "refuse"]`; P07 host dumps differ in exactly `actions.urn:cognous:action:refund-issue-routine-v1.on_unreadable`; **P08 effective profile dumps equal across worlds; P09 their independent commitments equal; P10 host independent commitments differ; P11 effective scoped `on_unreadable` `["refuse","refuse"]`; P12 live world with edited host mints `authorized`; P13 `catalogue_digest`, `members.effective_profile_digest`, `members.families.0.effective_policy_digest` all equal between persisted and live, and persisted `catalogue_digest == own_commit(effective dump)` (`[true,true,true,true]`)**; P14 family rows in both are exactly `["class_unreadable"]`. P08/P09/P11/P13 are the "effective profile and catalogue digests equal across worlds" validity precondition: if the edit is not masked the case is BLOCKED.

**Steps.** (1) Control world `h2c`: mint, identical restart, live diff, execute the original decision. (2) Perturbed world `h2p`: mint (host `bounded_tolerance`); rebuild over the same store with host `refuse`, approval NOT re-bound; live diff before execution; execute the original decision once via `H.drive_execute`.

**Assertion inventory.**

| id | statement | expected |
|---|---|---|
| FC-H2-C01 | control live diff base | `[]` |
| FC-H2-C02 | control live diff ECB | `[]` |
| FC-H2-C03 | control `[attempt status, exception]` | `["acknowledged", null]` |
| FC-H2-C04 | control new refusal rows | `[]` |
| FC-H2-C05 | control destination calls | `1` (unperturbed executes exactly once) |
| FC-H2-A01 | perturbed base binding diff | `[]` |
| FC-H2-A02 | perturbed ECB diff (sorted) | `["runtime_authority.effective_configuration.digest", "runtime_authority.effective_configuration.members.host_profile_digest"]` |
| FC-H2-A03 | exception type | `"PermissionError"` |
| FC-H2-A04 | exception text | `"authorization-critical inputs changed before effect"` |
| FC-H2-A05 | new durable refusals' reasons (exactly one new row) | `[["authorization_binding_changed"]]` |
| FC-H2-A06 | new refusal vocabulary | `["runtime-authority-reasons/0.1"]` |
| FC-H2-A07 | new attempt rows | `0` |
| FC-H2-A08 | `[destination calls, destination snapshot unchanged]` | `[0, true]` |

Evidence-only: E01 control classifier `bound`; E02 perturbed classifier `mismatch`; E03 raw classification string and diffs (the prediction is `isolated end-to-end`, not asserted as a row).

**Failure conditions.** Any `C*/A*` FAIL; the host edit EXECUTING (acknowledged, 1 destination call) is the kill-signal for a host-digest-from-effective defect in this hook; P-failure or exception => BLOCKED.

**What it does / does not establish.**
- functional correctness: a second workflow family mints, executes once (C03-C05) and exposes the same member contract.
- member sensitivity: with A01-A08 passing the live execute comparison refuses on a diff confined to `host_profile_digest` in the class-unreadable hook. No scratch mutant is run here, so sensitivity to a defect in the hook (`:336`) is inferred from the live refusal only, not demonstrated by a kill.
- guard-order evidence: base diff empty and base reasons absent show no earlier guard fired; the approval guard did not trip because the effective profile is identical. Not shown for any other member.
- end-to-end refusal: yes on execute for this family.
- independent isolation: NO (same lineage; same fixture library; n=1 world for this family).
- contract coverage: class-unreadable dedicated, execute leg, host_profile_digest only. Does not cover the joint class-unreadable+class-age workflow, composed policy workflow, claim leg, pin-export, freshness-extension, other members.

**Evidence rows written.** `FC-H2-P01..P14`, `C01..C05`, `A01..A08`, `E01..E03`; `BLOCKED` only on failure.

## 4. FC-H3 - unmasked-host contrast control (BOUNDED; NEVER ISOLATING)

Statement for both sub-cases: **FC-H3 does NOT isolate `host_profile_digest`.** The edit is unmasked by construction (host 60 -> 5 under Registry 10, effective min(5,10) = 5), so the effective profile, `catalogue_digest`, `approval_commitment` and the class-age family digest change together with the host digest. Its only purpose is to distinguish mechanism behavior: unmasked host drift is refused through other members first (H3a) or jointly (H3b). It must not be cited as evidence for the host member's isolation and must not be combined with FC-H1/FC-H2 into an isolation claim.

Shared preconditions (helper; ids `FC-H3a-P01..P07` and `FC-H3b-P01..P07`; any failure => BLOCKED): P01 minted `authorized`; P02 action id literal; P03 host class ages `[60, 5]`; P04 host dumps differ in exactly `actions.urn:cognous:action:refund-issue-routine-v1.max_status_age_seconds`; **P05 effective class age `[10, 5]` (the edit is NOT masked; if the effective value does not change the case is BLOCKED)**; P06 effective independent commitments differ; P07 host independent commitments differ. H3b adds P08 live world after approval re-issue mints `authorized`.

### FC-H3a - approval NOT re-issued (guard-first)
Steps: mint (host 60, Registry 10, approval bound to effective {10}); rebuild with host age 5 over the same store, approval NOT re-bound; execute the original decision.

| id | statement | expected |
|---|---|---|
| FC-H3a-A01 | exception type | `"PermissionError"` |
| FC-H3a-A02 | exception text | `"authorization-critical inputs changed before effect"` |
| FC-H3a-A03 | new durable refusal reasons | `[["runtime_authority_approval_mismatch"]]` |
| FC-H3a-A04 | vocabulary | `["runtime-authority-reasons/0.1"]` |
| FC-H3a-A05 | new attempts | `0` |
| FC-H3a-A06 | `[destination calls, unchanged]` | `[0, true]` |
| FC-H3a-A07 | `authorization_binding_changed` present in any new refusal | `False` |

Evidence-only: E01 classifier `mismatch` (it says nothing about guard order). `CLASSIFICATION` row: "guard-first (approval); host_profile_digest NOT isolated; the ECB was not the refusing comparison". "ECB not consulted" is an inference from guard order (approval guard `runtime_authority.py:332-335` runs inside the base `_resolve`, before the lifecycle ECB step, `registry_governed_lifecycle.py:266-268`); the row asserts only that the ECB code is absent.

### FC-H3b - approval re-issued against the new effective profile (joint)
Steps: mint (host 60); rebuild with host age 5 and `bind_approval` against the new effective profile; live-world diff (scratch) after the re-issue; execute the original decision.

| id | statement | expected |
|---|---|---|
| FC-H3b-A01 | base binding diff (sorted) | `["runtime_authority.approval_commitment", "runtime_authority.catalogue_digest"]` |
| FC-H3b-A02 | ECB diff (sorted) | `["runtime_authority.effective_configuration.digest", "runtime_authority.effective_configuration.members.effective_profile_digest", "runtime_authority.effective_configuration.members.families.0.effective_policy_digest", "runtime_authority.effective_configuration.members.host_profile_digest"]` |
| FC-H3b-A03 | classification by the D-1 rule | `"joint"` |
| FC-H3b-A04 | exception type | `"PermissionError"` |
| FC-H3b-A05 | exception text | `"authorization-critical inputs changed before effect"` |
| FC-H3b-A06 | new durable refusal reasons | `[["authorization_binding_changed"]]` |
| FC-H3b-A07 | vocabulary | `["runtime-authority-reasons/0.1"]` |
| FC-H3b-A08 | new attempts | `0` |
| FC-H3b-A09 | `[destination calls, unchanged]` | `[0, true]` |

Evidence-only: E01 classifier `mismatch`. `CLASSIFICATION` row: claim string, base diff, ECB diff. Derivation of A01/A02 (from source, same machinery as D-1 Q3-E2): the effective map {T1:10} -> {T1:5} changes the effective profile (hence `catalogue_digest` and `approval_commitment`, `runtime_authority.py:332`, `:473-475`), `effective_profile_digest` and the Registry family digest (`registry_f5_class_age_governance.py:180`, `:260`), and the host profile changes `host_profile_digest`; nothing else is expected to move (D-1 E2 base diff had exactly these two base leaves). If A01/A02 differ by a leaf the exact diff is retained as observed.

**Failure conditions (H3a/H3b).** Any `A*` FAIL; P-failure/exception => BLOCKED. Results of H3a/H3b are descriptive of mechanism ordering only.

**What FC-H3a/H3b do / do not establish.**
- functional correctness: the F5 class-age world refuses unmasked host drift; says nothing about control correctness beyond what FC-H1/FC-H2 controls show.
- member sensitivity: NOT for `host_profile_digest` (H3a: refusal occurs before the ECB; H3b: several members and base leaves move at once).
- guard-order evidence: H3a shows the approval guard precedes the ECB for host-driven effective changes (same pattern as D-1 Q3-E1); H3b shows the joint refusal after re-issue (D-1 Q3-E2 pattern).
- end-to-end refusal: yes (two refusals), joint/guard-first only.
- independent isolation: none; NEVER isolating.
- contract coverage: contrast for the masked-host fixtures only; documents that the masking is the isolation device and that an unmasked edit is refused via other members.

**Evidence rows written.** `FC-H3a-P01..P07`, `A01..A07`, `E01`, `CLASSIFICATION`; `FC-H3b-P01..P08`, `A01..A09`, `E01`, `CLASSIFICATION`.

## 5. Cross-case scope statement for the report

The four cases together would extend D-1 Q3-H1 (execute, class-age, n=1) by: one claim-leg case (FC-H1), one second-family execute case (FC-H2), and a non-isolating contrast (FC-H3). They remain same-lineage, same-subject, same-pin, Python 3.11.18 only, synthetic fixtures; no pin-export case (not reachable for profile-bearing families, `policy_binding_unsupported` constructor refusals); no result transfers to 8616d5f, main or Python 3.12. The masked-host limit text (CP docs at 8616d5f only; absent at 739efe7) concerns F4 scalars and ObservationPolicy values; the cases here are host PROFILE edits and are consistent with, not tests of, that limit.
