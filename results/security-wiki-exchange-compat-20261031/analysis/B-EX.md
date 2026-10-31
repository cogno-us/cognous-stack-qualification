# B-EX handoff: interface compatibility, Exchange 7f7569b0 vs current tuple (OCS-SECURITY-EXCHANGE-01)

Worker B. Read-only. Pristine checkouts untouched (verified no new __pycache__). Scratch: /tmp/claude-0/sec/scratch-B-EX/ (t1.py, t2.py, *.diff).
Labels: OBSERVED = file:line or command; INFERENCE = reasoned; UNAVAILABLE = cannot be established here.

## 0. Verdict (read first)

**The Exchange cannot interoperate with the current tuple by adding a pin profile alone. INCOMPATIBLE at the Replay and ODES revision gates.**

Replay 40012b8c, ODES 1a5e1d30 and Evidence Pack 7b9511f2 are themselves tied to a *different, earlier* Control Plane / Runtime pair than the target tuple. Their only Programme-2 generation is:
Control Plane **7a4bcd40** / Runtime **c5e97e87** / Replay 40012b8c / Manifest fa170815.
They do not name Control Plane **b19c47dd** or Runtime **f7a55e2a** anywhere (OBSERVED: `grep -rIn "b19c47dd\|f7a55e2a"` over control_plane, runtime, replay, evidence_pack, odes, manifest, exchange checkouts returns nothing).

So a profile pinning CP=b19c47dd / MOLTBOT=f7a55e2a (as the lead's draft at gax_ref_runtime.py:98-110 does) would pass `_verify_refusal_profile_sources` (identity of the five modules) but then every flow that reaches `import_replay_bundle` is refused by Replay with `unsupported Control Plane revision`. A Runtime export stamped f7a55e2a is also refused by Replay (`unsupported Moltbot producer repository revision`). ODES then cannot select a generation for b19c47dd.

I make no recommendation that weakens any check. Presenting the real options factually:
- (a) Replay/ODES/Pack (owners) add an exact b19c47dd/f7a55e2a generation: outside this task's authorization (Replay/ODES/Pack behaviour must not change).
- (b) The Exchange profile selects the tuple the current Replay/ODES/Pack actually accept (CP 7a4bcd40, Runtime c5e97e87). That is not the target tuple, and Runtime c5e97e87 is not in the pristine Runtime checkout (UNAVAILABLE), so the pristine Runtime f7a55e2a would fail the source-identity check for it. This changes the tuple under test; needs the lead/architect decision.
- (c) Passing the label 7a4bcd40/c5e97e87 to Replay while the loaded code is b19c47dd/f7a55e2a would be a false provenance label. The Exchange source check does not measure what is stamped into `control_plane_revision` / `repository_revision` (comment at gax_ref_runtime.py:44-46 says these are labels). I flag this as an identity falsification, not an option.

## 1. Method and what could be diffed
- Historical p2 pins: /home/claude/scn-components (all five present at CP 0a41faa9, Runtime ec728da6, Replay 028f63d1, Pack a3ebbb90, ODES e86a25a1; OBSERVED `git rev-parse HEAD`).
- Current: /home/claude/cs-components (CP b19c47dd not shallow; Runtime, Replay, Pack, ODES are SHALLOW clones: `git rev-parse --is-shallow-repository` = true). Old SHAs are absent from those clones (`git cat-file -t` fatal for ec728da6, 028f63d1, a3ebbb90, e86a25a1), so `git diff old new` is UNAVAILABLE for Runtime/Replay/Pack/ODES. I substituted a file-level `diff -rq` / `diff -u` between the two worktrees (scn-components vs cs-components, excluding .git, tests). That is a diff of the two exact trees, equivalent for these purposes.
- Control Plane: real `git diff 0a41faa9 b19c47dd` (full history, 7a4bcd40 is an ancestor of b19c47dd: `merge-base --is-ancestor` exit 0; 74 commits between 0a41faa9 and HEAD).
- Runtime c5e97e87 and Control Plane 7a4bcd40 are the pins the *current* Replay/ODES/Pack name. CP 7a4bcd40 is diffable; Runtime c5e97e87 is not present in any local clone (searched all /home/claude repos), so Runtime c5e97e87 -> f7a55e2a is UNAVAILABLE. Runtime ec728da6 -> f7a55e2a is available (file level).

## 2. Per-area results

### 2.1 Authority envelopes (runtime_authority_profile, bounded workflow)
Exchange call: `cp.BoundedAuthorizationWorkflow(manifest, resolver, destination, records, observation_policy, runtime_authority_profile=..., allow_test_time=...)`, `workflow.decide(proposal, now=)`, `BoundedRecordStore`, `LocalRefundDestination` (gax_ref_runtime.py:955-960, `_workflow_options` 124-134).
- `agent_control_plane/bounded.py` is NOT among the files changed 0a41faa9 -> b19c47dd (OBSERVED `git diff --name-only 0a41faa9 HEAD -- src`: 15 files, none is bounded.py/models.py/records.py). Constructor, `decide`, record store: **VERIFIED-COMPATIBLE (unchanged)**.
- `runtime_authority.py` changed additively (OBSERVED diff): new `VOCABULARY_VERSION_0_3`, `policy_binding: PolicyBinding | None = Field(default=None, exclude_if=None)`; `approval_commitment` is byte-identical when `profile.policy_binding is None` ("legacy: byte-identical to before"); extra extension members `approval_commitment_version/policy_generation/policy_activation_ref` only when `binding is not None`; one `min` added to the dispatch deadline collector for the purpose anchor (R6/D-07) that "can only add a min". **VERIFIED-COMPATIBLE for a profile without policy_binding** (code shown); behaviour change of the D-07 deadline anchor is not exercised by interface shape: UNPROVEN dynamically.
- If the Wiki harness profile sets `policy_binding`, the decision `binding.runtime_authority` gains members Replay does not accept (see 2.7): INCOMPATIBLE for that case. I did not find policy_binding use in the Wiki helper I sampled (wt-wiki/suites/v1-scenarios/_c_2a_helpers.py); the full harness profile construction was not traced: UNPROVEN.

### 2.2 Source identity (modules named in `_verify_refusal_profile_sources`, gax_ref_runtime.py:340-415)
Five modules: `agent_control_plane.bounded` (CP_REVISION), `engine.producer_contract` (MOLTBOT_REVISION), `agent_replay_bundle.importers` (REPLAY), `odes.exporter` (ODES), `agent_governance_evidence_pack.importer` (PACK); plus Manifest via UPSTREAM_MANIFEST_EXAMPLE (line 391-404).
- The check compares `git rev-parse HEAD` of each package's checkout to the constant. With the current heads in the constants it is a pure identity check; no interface dependence. **VERIFIED-COMPATIBLE as a mechanism**; I did not run it end to end (needs the lead's env; INFERENCE that it passes for pristine clean checkouts, UNPROVEN until run).
- Pack is source-verified only; the Exchange never imports or calls anything from it (OBSERVED: the only occurrence in experiments/ is the dict key at line 355). So Pack interface drift cannot break the Exchange; Pack's P2 tuple (importer.py P2_REVISIONS = 7a4bcd40/c5e97e87/40012b8c/fa170815) still does not name the target CP/Runtime.
- Cross-component consistency, not Exchange-local: Replay, ODES and Pack each embed an exact tuple that is not the target tuple (see 2.6).

### 2.3 Operation identity
Exchange builds `ExecutionOperation(... proposal_commitment=commitment(...), grant_id, grant_revision, effective_max_effects ...)` and `ExecutionEnvelope(producer.EXECUTION_ENVELOPE_VERSION, decision_id, effect_id, operation)` (gax_ref_runtime.py:613-647).
- Runtime `engine/producer_contract.py` and `engine/safe_executor.py` are byte-identical between ec728da6 and f7a55e2a (OBSERVED `diff -q`); `EXECUTOR_PRODUCER_PROFILE_ID/VERSION` still `urn:cognous:profiles:moltbot-safe-executor-producer` / `2.0.0` (producer_contract.py:23-24), matching Exchange constants (gax_ref_runtime.py:39-40). **VERIFIED-COMPATIBLE vs the historical p2 Runtime.** Runtime c5e97e87 -> f7a55e2a: UNAVAILABLE (INFERENCE: c5e97e87 is ec728da6 plus F3 terminal approval revocation per the Replay comment; Exchange-called files appear unchanged).
- Control Plane `operation_identity.py` unchanged (not in diff list). Verified-compatible.

### 2.4 Claim / approval semantics
- The Exchange does not use Control Plane claims (route B: `local_authority_effect`, `authorization_pin`, `registry_*`, atomic executor). OBSERVED grep of experiments/ finds no use. The Control Plane changes there (claim profile V2, `policy_binding` member, claim-journal stage, pin export) and Runtime `atomic_local_control_plane_executor.py` / `local_authority_effect.py` changes (selection_refusal in denied evidence, authorization_pin option) are **not on the Exchange call path**: VERIFIED-COMPATIBLE by non-use. Note Replay does not accept the new `selection_refusal` evidence member (OBSERVED: no occurrence in replay/src), so if a deployment used the atomic executor with a SelectionRefusal, Replay import would refuse it; the Exchange uses `PinnedControlPlaneExecutor` instead.
- Approval commitment: unchanged for profiles without policy_binding (2.1).

### 2.5 Execution result structures / evidence representations
- Exchange reads `result.status/attempted/newly_executed/observed_state/effect_id/decision_id/attempt_id/acknowledged/observation/control_plane_evidence` and exports via `producer.export_execution_artifacts(request, result, destination, repository_revision=MOLTBOT_REVISION, source_asserted_provenance=...)` (lines 508-529, 820-842). producer_contract unchanged vs ec728da6: **VERIFIED-COMPATIBLE** on the producing side.
- Replay change (current vs old pin, OBSERVED diff importers.py): adds `RUNTIME_FAILURE_CLASSES` and `_denial_failure_class_admitted`; permits `failure_class` on denied, not-attempted route-B evidence (only with `failure_record_id`, only security-generation). Additive; Exchange does not emit it. **VERIFIED-COMPATIBLE (additive)**.
- ODES change vs old pin (common.py only): constants. exporter.py unchanged. `export_cognous_stack_package` / `evaluate_recipient_package` signatures used at gax_ref_runtime.py:538-560 unchanged. **VERIFIED-COMPATIBLE for the interface**, but see 2.6 for the revision gate.

### 2.6 Replay import requirements and revision gates — INCOMPATIBLE
1. `import_bounded_workflow(..., control_plane_revision=CP_REVISION)` (gax_ref_runtime.py:530) requires `control_plane_revision in {CONTROL_PLANE_REVISION, *CONTROL_PLANE_SUPPORTED_V2_REVISIONS}` (replay/src/agent_replay_bundle/importers.py:682-683). The accepted P2 revision is `CONTROL_PLANE_P2_REVISION = 7a4bcd40...` (importers.py:~88). OBSERVED run (scratch t1.py, python3 -I, bytecode disabled):
   - b19c47dd -> `ImportContractError: unsupported Control Plane revision`
   - 0a41faa9 (the historical p2 CP) -> `unsupported Control Plane revision` (so the existing p2 profile also cannot run against the current Replay/ODES; retained-evidence reproduction needs the historical checkouts)
   - 7a4bcd40 -> passes the gate (then fails later on my intentionally empty record).
   This applies even to denial-only flows: `_pipeline` calls it with `moltbot=None` (lines 528-530, 669-683 of the Exchange), so every path that builds artifacts is affected, not only executed ones.
2. With a Runtime export, `_moltbot_contract` requires `repository.revision == MOLTBOT_P2_REVISION (c5e97e87)` for the P2 pairing and `control_plane_revision in compatible_control_plane_revisions == [7a4bcd40]` (importers.py:596-598, 703-706). A Runtime export stamped f7a55e2a is refused: `unsupported Moltbot producer repository revision` (importers.py:609-610). Exchange stamps `repository_revision=MOLTBOT_REVISION` (gax_ref_runtime.py:515).
3. ODES: `export_cognous_stack_package` selects the generation from the bundle's `metadata.control_plane_revision` and requires it in `ALL_V2_CONTROL_PLANE_REVISIONS` (exporter.py:592-599, 637-652). OBSERVED (scratch t2.py): b19c47dd not in `ALL_V2_CONTROL_PLANE_REVISIONS` nor `SECURITY_RUNTIME_CP_REVISIONS`; `accepted_replay_revisions(b19c47dd)` is empty; 7a4bcd40 maps to Replay 40012b8c. Replay 40012b8c itself is an accepted Replay revision.
4. Evidence Pack importer: `P2_REVISIONS` = 7a4bcd40/c5e97e87/40012b8c/fa170815 only (importer.py:~96-100, 106). Not called by the Exchange; informational for downstream Wiki Pack tests.
5. Replay comments mark the generation "PROVISIONAL DEVELOPMENT PIN, UNQUALIFIED" (importers.py comment at the P2 constants).

### 2.7 Typed-refusal importer: accepted runtime_authority member set vs what CP now emits
Replay `refusal_evidence.validate_run` (refusal_evidence.py:~352-362):
- `binding.runtime_authority` must have `profile == 'runtime-authority/0.1'` and its key set must equal exactly `{profile, approval_commitment, required_inputs_digest, catalogue_digest, expected_effective_grant_digest, effective_grant_derivation_version}` plus `{operation_id, operation_issuer}` when present and `profiles=True`. Anything else: `runtime authority fields unsupported` (code `undeclared_member`).
- Accepted decision vocabulary labels: `runtime-authority-reasons/0.1`, `/0.2` only (with profiles); 0.3 is not accepted (lines 92-143, 355).
Current Control Plane emits, OBSERVED in source:
- `binding.runtime_authority["effective_configuration"]` (`effective_configuration_binding.py:34 KEY`, registry_governed_policy.py module docstring lines 27-30): emitted by every authorized decision of the **registry-governed workflow** (D-06). Not accepted by Replay: **INCOMPATIBLE for any run produced through `registry_governed_policy` workflows.** The Exchange uses plain `BoundedAuthorizationWorkflow` (no registry_* import), so this member is not emitted on the Exchange path: VERIFIED by non-use, UNPROVEN if the Wiki harness injects a governed workflow.
- `approval_commitment_version`, `policy_generation`, `policy_activation_ref` (runtime_authority.py validate_extensions) when `profile.policy_binding` is set: not accepted by Replay (INCOMPATIBLE if configured); and the label `runtime-authority-reasons/0.3` when any of the eight policy-binding codes is raised: not accepted by Replay.
- Default path (no policy_binding, plain bounded workflow): the emitted member set equals the old set (code-shown additive-only changes). **VERIFIED-COMPATIBLE by code reading; dynamic emission not exercised.**
Note this member-set mismatch is *behind* the revision gate in 2.6 (the gate fails first for b19c47dd).

### 2.8 Refusal behaviour
- Exchange-side refusal logic (message assessment, `candidate source identity mismatch` RuntimeError) is local and unchanged by the new tuple.
- Control Plane `reason_vocabulary.py` / bounded.py refusal paths unchanged (not in diff list). Replay additive failure_class (2.5). **VERIFIED-COMPATIBLE** for unchanged paths; reason-code semantics of the new D-07 anchor deadline: UNPROVEN.

## 3. Exchange embeddings tied to the historical tuple (everything a new profile also needs)
All in /home/claude/cognous-governed-exchange (read at the lead's working state, which already contains a draft `security-runtime-current-20261031` at gax_ref_runtime.py:98-117 and CURRENT pins in the tests at tests/test_exchange_input_and_source_repairs.py:459-470):
1. gax_ref_runtime.py:32-38 default constants (persistence-v1 historical, unchanged); 50-110 per-profile elif blocks, each setting CP/MOLTBOT/MANIFEST/REPLAY/ODES/EVIDENCE_PACK (the five plus Manifest; `ALVORADA_REVISION` line 38 is never overridden and not verified anywhere).
2. Line 115 `SECURITY_RUNTIME_PROFILES` frozenset (profile-name list; drives `_workflow_options` requirement for trusted `runtime_authority_profile`, line 126) and line 117 `STRICT_SOURCE_PROFILES` (drives `_verify_refusal_profile_sources`, line 433).
3. Line 111 `elif RUNTIME_COMPATIBILITY_PROFILE != "persistence-v1": raise` (unknown profile names fail at import).
4. `MOLTBOT_PRODUCER_PROFILE_ID/VERSION` (39-40) and `GAX_ARTIFACT_EXPORT_PROFILE/VERSION` (41-42): shared across profiles; not revision-tied; unchanged.
5. Revision constants flow into outputs as *labels* (not measured): `repository_revision=MOLTBOT_REVISION` at line 515 and `control_plane_revision=CP_REVISION` at line 530. These are the values Replay/ODES gate on (2.6).
6. Manifest: `MANIFEST_REVISION` compared at lines 391-404 against `UPSTREAM_MANIFEST_EXAMPLE`'s repo HEAD (fa170815 = same as P2; Manifest checkout unchanged).
7. tests/test_exchange_input_and_source_repairs.py: parametrised `STRICT_SOURCE_PROFILES` fixture (line 168); dicts F5B/P4/P2/typed-refusal/candidate pins at 327-366; profile table 373; CURRENT pins 459-470 and the assertions at 478-499, 531-533, 550-556 (per-constant mismatch refusals); a profile-selector test at 387-407; line 588 uses F5B manifest.
8. Docs/README embed profile lists and hashes: README.md:22, 68, 72, 167; docs/security-runtime-profile-20261016.md, docs/security-runtime-f5b-profile-20261016.md (tuple table lines 7-12, line 20, 22); docs/merged-consumer-chain.md:7; docs/typed-refusal-profile.md; experiments/governed_message_transport/profile.md:43 (limitation text naming security-runtime profiles); CHANGELOG.md (a dated entry per re-tie, the latest 22 Oct 2026 for 0a41faa9/ec728da6).
9. CI: .github/workflows/{tests,typed-refusal,merged-consumer-chain,generation-fence}.yml contain no matches for the historical SHAs or profile names (OBSERVED grep).
10. No hash of the tuple is embedded in produced artifacts other than the two labels in item 5 and the stored `producer_profile`/`repository` dicts that come from the Runtime export (so a retained export records f7a55e2a; Replay must accept it).

## 4. Summary table
| Area | Result |
|---|---|
| Authority envelopes (bounded.py, workflow API) | VERIFIED-COMPATIBLE (unchanged); policy_binding-off path additive |
| Source identity mechanism | VERIFIED-COMPATIBLE as mechanism; end-to-end pass UNPROVEN (not run) |
| Operation identity / producer contract | VERIFIED-COMPATIBLE vs ec728da6 (identical files); c5e97e87->f7a55e2a UNAVAILABLE |
| Claim / approval | VERIFIED by non-use (route B not used); approval commitment unchanged without policy_binding |
| Execution result / evidence structures | VERIFIED-COMPATIBLE (additive failure_class) |
| Replay `control_plane_revision` gate (importers.py:682) | **INCOMPATIBLE** for b19c47dd |
| Replay Runtime-export revision gate (importers.py:596-610) | **INCOMPATIBLE** for f7a55e2a |
| ODES generation selection (exporter.py:592-599, common.py) | **INCOMPATIBLE** for b19c47dd |
| Pack P2 tuple | Does not name target CP/Runtime; Exchange never calls Pack (informational) |
| Replay runtime_authority member set vs `effective_configuration`, policy_binding members, vocab 0.3 | INCOMPATIBLE if emitted; not emitted on plain bounded path (UNPROVEN dynamically) |
| Refusal behaviour | VERIFIED where unchanged; D-07 deadline anchor UNPROVEN |

## 5. Open items for the lead (not decided here)
- Whether the intended tuple is the target (b19c47dd/f7a55e2a) or the Replay/ODES/Pack-accepted pair (7a4bcd40/c5e97e87). The 41-test claim "an Exchange profile alone clears it" is not supported by this analysis; the BLOCKED tests that reach `_pipeline` will fail at Replay even with the profile added.
- Which of the 41 tests stop before `_pipeline` (pure message-assessment refusals) cannot be determined statically here; those may pass with a profile alone: UNPROVEN.
- Runtime c5e97e87 is absent from every local clone; obtaining it is needed for any decision on option (b) and for diffing c5e97e87 -> f7a55e2a.
- Memory facts used: none.
