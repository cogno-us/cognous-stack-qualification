# FXE-JOINT: effective-profile digest JOINT transition (freshness-extension route), EXECUTE leg: draft case specification

Status: DRAFT by Worker C (same session lineage as the lead; NOT independent). Written from source reading only; nothing was executed (no case, no probe, no pytest run; only `py_compile` to a scratch path and `pytest --collect-only`, which imports and runs no test body). Not an acceptance claim. The lead freezes (hashes) `harness/test_bq_eff.py` and this file before first execution; invalid fixtures after the freeze are retained as BLOCKED/FAIL and corrected only by a versioned successor (protocol section 14).

Instrument: `/tmp/claude-0/work/bq/harness/test_bq_eff.py` (imports, read-only, `d1_lib.py` sha256 `5ec947ba...` and `orig_harness.py` sha256 `a5147412...`; both verified unchanged at the end of the draft).
Subject: CP `739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69`; Registry pin `a40fe755e2384a99c37016fa9ad59396f1835900`; Python 3.11.18; `GovernedClassAgeWorkflow` (dedicated class-age workflow, no activation ledger).
Static sources: `/tmp/claude-0/work/f252/worker-c.md` section 10 (FXE-JOINT, CE4), merged dossier section 7, protocol skeleton section 15 item 7.

## 0. Mandatory scope statement (to be carried verbatim into README.md and limitations.md)

FXE-JOINT is JOINT evidence. It is NOT independently isolated `effective_profile_digest` evidence and must never be labelled so. By `02` section 4 line 48 (`effective_profile_digest` equals `catalogue_digest` for profile-bearing workflows, else null) and by construction (one `_resolve` call derives both from the one object `self.runtime_authority_profile`; the approval commitment preimage contains the profile dump), the base pair `{approval_commitment, catalogue_digest}` always moves together with the effective member. The case narrows the ECB diff to exactly `{digest, members.effective_profile_digest}` (no `families.*` leaf, no `host_profile_digest` leaf) and nothing more. The case decision rule `claim_for(...)` is expected to return `"joint"`; a result `"isolated end-to-end"` would itself be an adverse finding (impossible by I1-I4 of worker-c section 3).

What FXE-JOINT does NOT prove:
1. Live derivation sensitivity of the effective digest alone (nothing varies `effective_profile_digest` with `catalogue_digest` and `approval_commitment` held fixed; by contract that state does not exist on a live path).
2. Pin-export behaviour (profile-bearing governed workflows refuse the `policy_binding` pin-export requires; no pin-export leg exists here; do not add one).
3. Claim / provision / materialize behaviour (no claim leg).
4. That a mutant of the live derivation (for example live effective := host digest at `registry_f5_class_age_governance.py:260`) would be caught: no mutant is run in this protocol (section 13), and by source reading such a mutant is outcome-equivalent on this case (the base pair still refuses).
5. Behaviour on class-unreadable, joint, composed, revocation, irreversibility or anchor workflows; F4-dedicated (null/null) workflows; other revisions (`8616d5f`, `main`), Registry main, Python 3.12.
6. Persisted-side comparison sensitivity of the effective member (that is A19/G1/G2/P5 evidence, not rerun here).
7. That record 12 item 2 is discharged, or that "two independent fixtures" is satisfied (reading R1/R2 UNVERIFIED).
8. That a re-issued approval is a production-grade control: it uses the supported host duty `bind_approval`, in the harness resolver.

## 1. Fixture (frozen values)

| Item | Value | Source of the value |
|---|---|---|
| Workflow | `GovernedClassAgeWorkflow`, scope (`consumer-test`, `tenant-alpha`, tenant proposal action, operation `refund-issue-routine`) | D-1 `d1_lib.construct_f5` |
| Host profile | one class `synthetic-irreversible` (T1), `irreversible=True`, `max_status_age_seconds=60`, `on_unreadable=refuse`, `producer_keys`, `allow_synthetic_resolver=True`, `freshness=FreshnessProfile(max_age_extension_seconds=100)` (other FreshnessProfile fields default; no `anchor_deadline_to_inputs`), no `policy_binding` | `test_bq_eff.fx_host` (own), modelled on `d1_lib.host_profile` plus developer test `test_f5_class_age_governance.py::host_profile(freshness=...)` |
| SA | Registry F5 record `{T1: 70}`, effective T1 = min(60, 70) = 60, room = 70 - 60 = 10, composed extension limit = min(100, 10) = 10 | `compose_profile` `registry_f5_class_age_governance.py:117-127`, `derive_effective` `:169-172` |
| SB | Registry F5 record `{T1: 90}`, effective T1 = 60, room 30, composed limit = min(100, 30) = 30 | same |
| SA' (C2) | `{T1: 70}`, record text byte-identical to SA, selection re-signed with `selection_id="sel-test-2"`, `epoch=2` | `test_bq_eff.fx_material` (own copy of `d1_lib.f5_material` with the two overrides); developer test l05 pattern |
| SC (C3) | `{T1: 50}`, effective T1 = 50, room = max(0, 50 - 50) = 0, composed limit = 0 | same functions |
| Registry validity | an r08-v2 F5 value above the host is accepted and composes by `min`: Registry `compose_f5` at pin: `eff = min(base[k], reg[k])` with a `widens_host` note only (`registry_successor/v2_age_bounds.py:219-227`); CP `derive_effective` refuses only `effective > host` (impossible by `min`) | read at pin `a40fe755` |
| Clock | `H.patch_clock` (D-1; the only patch): `bounded._now` and the governed modules' `_now` fixed at `tba.NOW` (2026-10-05T19:00Z); the Registry effective window is 2026-10-01..2026-10-06 | D-1 |
| Resolver/destination | tenant resolver from `tba.tenant_resolver_for`, approvals via `bind_approval` (supported host duty), `CountingDestination` in-process stub; no network | D-1 |

Persisted vs live: persisted decision minted by workflow over SA in store directory S; the live world is a second workflow over SB over the SAME store S for execute, and the live binding for the complementary diff is minted by a third workflow over SB in a scratch store (the D-1 `live_binding` method; it uses the same resolver, same clock, same approval state).

Selection / record identity (answer to the lead's source question): SA and SB share `selection_id` `sel-test-1`, epoch 1, issuer, consumer, scope, operation, validity window and trust snapshot; they differ in record content (`payload.class_status_max_age_seconds` 70 vs 90), hence `record_digest`, record text and the signature over the statement. None of this enters the persisted decision binding (the binding carries only digests: `catalogue_digest`, `approval_commitment`, the ECB member digests) or the ECB members (`families[].effective_policy_digest` covers `{family, contract_version, effective map}` only; `v2_policy_identity.preimage_from_inputs` takes `{family, contract_version, effective}`). The case therefore does not rely on any selection-identity difference; the harness records both record digests as an OBSERVATION.

## 2. Predicted values (derivation, frozen before execution)

- Effective profile dump under SA = host dump with `actions.<aid>.max_status_age_seconds = 60` (unchanged) and `freshness.max_age_extension_seconds = 10`. Under SB: same with `30`. Dumps differ in exactly one leaf: `freshness.max_age_extension_seconds`.
- `catalogue_digest` (base) = commitment of the held effective profile dump (`runtime_authority.py:475`); ECB `effective_profile_digest` = `profile_digest(held)` = the same commitment (`registry_f5_class_age_governance.py:260`). `host_profile_digest` = commitment of the HOST dump (limit 100), identical in SA and SB.
- `approval_commitment` preimage contains the profile dump (`runtime_authority.py:236-242`), so it differs between the SA-bound and SB-bound approvals.
- `families.0.effective_policy_digest` covers only `{T1: 60}`: equal in SA and SB. `scope`, `f4_scalars`, `other_scalars`, `observation_policy`: equal.
- Base diff (persisted SA binding vs live SB binding): exactly `{runtime_authority.approval_commitment, runtime_authority.catalogue_digest}`.
- ECB diff: exactly `{effective_configuration.digest, effective_configuration.members.effective_profile_digest}` (prefix `runtime_authority.`).
- Execute (SB workflow, approval re-issued): guard order `_gl_reverify` passes (rebuilt workflow derives its own held state), approval matches the live profile, base reasons empty, ECB classification `mismatch`, `current != persisted.binding` at `bounded.py:1690` -> `PermissionError("authorization-critical inputs changed before effect")`, one durable `EffectTimeRefusal` with `reasons == ["authorization_binding_changed"]` (vocabulary `runtime-authority-reasons/0.1` since the code is not in `CODES_ADDED_IN_0_2`), no attempt row, destination untouched.
- No age-extension row is recorded anywhere in the case (`age_extensions` stays 0): the extension limit is configuration, not an extension use.

## 3. Reason strings and exception text frozen

- `authorization_binding_changed` (main, C3)
- `runtime_authority_approval_mismatch` (C1, alone)
- Exception type `PermissionError`, text exactly `authorization-critical inputs changed before effect` (main, C1, C3 where asserted)
- Reason vocabulary `runtime-authority-reasons/0.1`
- Candidate classifier (evidence only) values: `mismatch` (main), `bound` (C0, C2)

## 4. Evidence rows

Every assertion emits exactly one row in `$BQ_EVIDENCE_DIR/bq_evidence.jsonl` (protocol section 16 schema: `protocol, run, case_id=FXE-JOINT, assertion_id, kind, expected, observed, result, t_start, t_end, t`, plus `test`), and one D-1-style mirror row (`CHECK_PASS` / `CHECK_FAIL` / `BLOCKED` / `NOT_EXECUTED`, with `check`, `expected`, `observed`) via `d1_lib.rec` in `$D1_EVIDENCE_DIR/d1_evidence.jsonl` (case `FXE-JOINT/<test>`). `result` is `PASS`/`FAIL` for assertions and controls, `PASS`/`BLOCKED` for preconditions, `NOT EXECUTED` for planned ids not reached after an abort or BLOCKED gate. Additional rows per leg: SNAPSHOT (`journal_before`, `journal_after`: counts of decisions, refusals, attempts, age extensions; refusal rows with reasons and vocabulary; destination call count and snapshot), OBSERVATION (`fixture_material`, `complementary_diff` with full leaf sets, persisted and live ECB members, digests and independent recomputations, `execute_outcome`), EXCEPTION (the raised `PermissionError` with full text and traceback). Assertion ids: `FXE-JOINT-A01..A32` (main), `FXE-JOINT-C0-A01..A08`, `FXE-JOINT-C1-A01..A08`, `FXE-JOINT-C2-A01..A07`, `FXE-JOINT-C3-A01..A10`; preconditions `FXE-JOINT-P01..P12` and `FXE-JOINT-C<k>-P<nn>`.

Expected values are hard-coded literals except one disclosed class, marked ORACLE below: digest expectations are `own_commit(expected_dump)` where `expected_dump` is built by the harness from the HOST dump plus two literal integers (age, extension limit) and canonicalised by the harness's own `H.canon` (sha256 over sorted-key, compact, non-ASCII JSON; byte-compatible with `bounded._canonical_bytes`, re-implemented in `orig_harness.canon`). Nothing is computed from the product's observed digest. Equality assertions (`A05`, `A11`) compare two observed values with expected literal `True` (these express the contract equality `eff == catalogue_digest`).

## 5. Six dimensions (protocol section 11) for FXE-JOINT, per leg

| Leg | 1 Functional | 2 Member sensitivity | 3 Guard order | 4 End-to-end refusal | 5 Independent isolation | 6 Contract coverage |
|---|---|---|---|---|---|---|
| main | CAN (A01-A13: persisted and live eff digest equal the independent commitment of the harness-built expected profile; eff == catalogue_digest) | PARTIAL, JOINT (A14-A23: base diff exactly the pair, ECB diff exactly `{digest, effective_profile_digest}`; CANNOT show the member alone) | CANNOT (main alone does not show which guard fired first; C1 does) | CAN (A24-A32: durable refusal after the approval re-issue; joint) | CANNOT: JOINT evidence, NO independent isolation | CAN: execute leg, class-age dedicated workflow, freshness-extension route only |
| C0 | CAN (control executes once; empty diff; digest recomputes) | NOT APPLICABLE | NOT APPLICABLE | NOT APPLICABLE (acceptance control) | NOT APPLICABLE | validity control only |
| C1 | NOT APPLICABLE | NOT APPLICABLE (member not reached) | CAN: approval guard fires first, ECB not consulted (code absent) | CAN only to its boundary (refused before the ECB; says nothing about the member) | NOT APPLICABLE | execute leg guard-first |
| C2 | CAN (neutral rotation does not refuse) | NOT APPLICABLE (shows a non-member change is not sensitive) | NOT APPLICABLE | NOT APPLICABLE | NOT APPLICABLE | validity control: SA vs SB difference is not a selection-identity artefact |
| C3 | CAN (SC dump equals the harness prediction) | PARTIAL, JOINT (diff widens by exactly `families.0.effective_policy_digest`: the leaf is observable) | NOT APPLICABLE | CAN (joint) | CANNOT | execute leg, effective-map route |

## 6. Case FXE-JOINT-main: `test_FXE_JOINT_main`

Purpose: execute-leg fail-closed behaviour on a JOINT transition of the effective profile whose ECB diff is exactly `{digest, effective_profile_digest}` (the narrowest joint reachable on a supported live path).

### 6.1 Exact steps
1. World: tenant proposal/resolver, HOST profile (T1 age 60, FreshnessProfile limit 100), runtime-authority context prepared as D-1 (`prepare_runtime_authority`). Registry source SA (`{T1: 70}`).
2. P01: construct `fa` = `GovernedClassAgeWorkflow` over SA, store S; approval bound to `fa`'s effective profile (`bind_approval`). P02/P03: `fa.decide(...)` -> must return `authorized` (persisted decision, ECB member minted).
3. P04: construct `fb` over SB (`{T1: 90}`), same store S, approval RE-ISSUED to `fb`'s effective profile (`bind_approval`).
4. Preconditions P05-P10 (fixture material, identity maps, family digest equality, profile dump diff, commitment inequality).
5. P11/P12: a third workflow over SB in a scratch store mints a decision (`authorized`); its binding is the live binding for the complementary diff.
6. Gate (any failed precondition -> BLOCKED, case not interpreted).
7. Compute base diff / ECB diff of persisted SA binding vs live SB binding (harness-side), assertions A01-A23.
8. Execute: `fb.execute(proposal, persisted_decision, adapter_id, now=NOW)`; record journal before/after, exception, outcome; assertions A24-A32.

### 6.2 Validity preconditions (BLOCKED if they fail; never interpreted)
| Id | Precondition | Expected |
|---|---|---|
| P01 | `fa` constructed over SA (host limit 100) without Registry/construction refusal | `constructed` |
| P02 | `fa.decide` completes without raising | `completed` |
| P03 | SA decision result | `authorized` |
| P04 | `fb` constructed over SB; the Registry/adapter accepts a record value (90) above the host (60) (developer test x02 implies yes; UNVERIFIED at pin `a40fe755`) | `constructed` |
| P05 | parsed record class maps: SA `{T1:70}`, SB `{T1:90}` | `{"A":{T1:70},"B":{T1:90}}` |
| P06 | `registry_f5_policy_identity["effective"]`: both `{T1:60}` (effective profile values equal) | `{"A":{T1:60},"B":{T1:60}}` |
| P07 | identity `host` ages both `{T1:60}` | same shape |
| P08 | `effective_policy_digest` of the two flows equal | `True` |
| P09 | held effective profile dump leaf diff A vs B | `["freshness.max_age_extension_seconds"]` exactly |
| P10 | `own_commit(dump_A) != own_commit(dump_B)` (catalogue_digest differs) | `True` |
| P11 | live scratch mint completes without raising | `completed` |
| P12 | live SB mint result | `authorized` |

### 6.3 Assertion inventory

Legend for "does NOT establish": see section 0 for the global NOT list (never an isolation, never pin-export/claim, never live derivation sensitivity alone, no mutant). Dimensions: F functional, M member sensitivity, G guard order, E end-to-end refusal, I independent isolation, K contract coverage. "Eviden" rows: the assertion's own row plus the case-level SNAPSHOT/OBSERVATION/EXCEPTION rows of 6.4.

| Id | Expected (hard-coded) | Fails when | Establishes | Does NOT establish | Dimensions |
|---|---|---|---|---|---|
| A01 | held profile dump of `fa` == harness-built dump (host dump with age 60, limit 10) | the product composes anything other than limit 10 (including the host dump changed elsewhere) | F: the composition formula `min(host limit, room)` at SA, no other profile change; ORACLE-free (literal-built dump) | that the derivation is exercised by anything but these two points | F |
| A02 | held profile dump of `fb` == harness-built dump (age 60, limit 30) | limit != 30 or any other leaf differs | F: second profile point distinct from A01 (defeats a constant); the freshness-extension route is real | live effect on `effective_profile_digest` alone | F |
| A03 | persisted base `catalogue_digest` (SA) == `own_commit(exp_A)` | digest differs | F: base digest equals an independent commitment | member sensitivity | F |
| A04 | persisted ECB `members.effective_profile_digest` (SA) == `own_commit(exp_A)` (ORACLE: independent recomputation over literal-built dump) | member value differs | F: the minted member equals the independent commitment of the effective profile (not host, not null) | variation by itself (A10 gives the second point) | F |
| A05 | persisted eff == persisted `catalogue_digest` (observed equality; expected `True`) | members differ | the `02` line 48 equality on a profile-bearing workflow (supports why isolation is impossible) | that the equality is checked at runtime (it is not) | F, K |
| A06 | persisted ECB `host_profile_digest` == `own_commit(host dump)` (ORACLE) | differs | F: host member is the HOST profile (limit 100), not the effective | independent isolation of the host member | F |
| A07 | host digest != effective digest (`True`) | equal | the fixture separates host from effective (limit 100 vs 10) | masked-host limit | F |
| A08 | persisted ECB `digest` == `H.my_digest(members, version)` (independent re-implementation) | mismatch | F: the member's own digest recomputes | nothing about the live comparison | F |
| A09 | live (SB) base `catalogue_digest` == `own_commit(exp_B)` (ORACLE) | differs | F: live base digest equals independent commitment, second point | independence from the approval | F |
| A10 | live ECB eff (SB) == `own_commit(exp_B)` (ORACLE) | differs | F: live member tracks the profile at the second point; with A04 it shows the member is not a constant and not the host digest (host is constant 100) | live derivation sensitivity ALONE (no run holds catalogue/approval fixed) | F, M(partial) |
| A11 | live eff == live `catalogue_digest` (`True`) | differ | the equality holds live too | runtime check of the equality | F, K |
| A12 | live ECB `digest` == `H.my_digest` | mismatch | live member digest recomputes | - | F |
| A13 | live ECB `host_profile_digest` == `own_commit(host dump)` (ORACLE) | differs | the host member is unchanged between worlds (the diff cannot be a host effect) | - | F, M |
| A14 | base diff == `["runtime_authority.approval_commitment","runtime_authority.catalogue_digest"]` | any other leaf, or a leaf missing (for example empty: the premise "base moves" is false) | M(joint): base pair moves, nothing else in the base binding (no manifest/proposal/grant leaf) | that the pair is the cause of the refusal (see A22) | M |
| A15 | ECB diff == `{runtime_authority.effective_configuration.digest, ...members.effective_profile_digest}` exactly | any other leaf (for example `families.0...` or `host_profile_digest`), or a leaf missing | M(joint): the ECB leaf set is exactly two (the case's narrowing; CE4 confirmed) | independence (A14 shows the base pair moved too) | M |
| A16 | `members.families` equal persisted vs live | differs | the family digest leaf is NOT in the diff (the CE4 claim; contradicts D-1 reviewer F2 "always moves families.0") | other families | M |
| A17 | `members.host_profile_digest` equal | differs | host leaf not in the diff | - | M |
| A18 | `members.scope` equal | differs | scope unchanged | - | M |
| A19 | `members.f4_scalars` equal | differs | scalars unchanged | - | M |
| A20 | `members.other_scalars` equal | differs | scalars unchanged | - | M |
| A21 | `members.observation_policy` equal | differs | observation policy unchanged | - | M |
| A22 | `claim_for(base, ecb, "effective_profile_digest")` == `"joint"` | returns `"isolated end-to-end"` (base empty would be required: contradicts I1-I4: adverse finding) | the case is recorded as JOINT by the frozen decision rule | any isolation claim; the rule is a classification, not a proof | M, I |
| A23 | `members.families` has exactly one row, slot `class_age` | different count/slot | the dedicated F5 workflow's family structure (so `families.0` in C3 is the class-age row) | - | K |
| A24 | `execute` raised `PermissionError` (exact type name) | no exception, or another type (for example a Registry refusal type) | E: fail closed (exception) | durable row (A26) | E |
| A25 | exception text == `authorization-critical inputs changed before effect` | differs | E: the frozen text from `bounded.py` | member attribution | E |
| A26 | new durable refusal rows == `[["authorization_binding_changed"]]` (exactly one row, exactly one reason) | extra/missing row or reason (for example `runtime_authority_approval_mismatch` also present: approval re-issue failed) | E: durable `EffectTimeRefusal` with the contract code, only that code | attribution to the effective member (the code is generic: `current != persisted.binding`); attribution is only by A14/A15 | E, G(partial: approval guard passed) |
| A27 | refusal `reason_vocabulary_version` rows == `["runtime-authority-reasons/0.1"]` | differs | vocabulary label as D-1 | - | E |
| A28 | new attempt rows 0 and total attempts after == 0 | any attempt row | E: no attempt created | - | E |
| A29 | destination calls 0 and destination snapshot unchanged | any call or change | E: destination untouched | - | E |
| A30 | journal counts: decisions [1,1], refusals [0,1], age_extensions [0,0] | any other count | E: exactly one new durable refusal, no other store growth in these collections, no age-extension row involved | other collections (check events, resolution checks are expected to grow and are not asserted) | E |
| A31 | persisted decision binding identical before and after the leg | changed | the refusal did not rewrite the decision | tamper evidence (unsigned store) | E |
| A32 | candidate classifier `configuration_binding_status` == `mismatch` (EVIDENCE ONLY, never the oracle) | other value | corroboration that the stored member differs from the live member | independent oracle | M (evidence-only) |

### 6.4 Case-level rows (not assertions)
`SNP-journal_before`, `SNP-journal_after`, `OBS-fixture_material` (both record texts' digests, same selection id/epoch), `OBS-complementary_diff` (full leaf sets, persisted and live ECB members, `own_commit` of expected dumps), `OBS-execute_outcome`, `EXC-execute` (type, text, traceback), plus the D-1 PREFLIGHT row. A leg without all of them cannot be scored PASS (protocol section 16).

### 6.5 Predicted outcome and claim permitted if all pass
Predicted: all preconditions hold; A01-A32 PASS. Claim permitted: "On CP 739efe7 / Registry pin a40fe755 / Python 3.11.18, `GovernedClassAgeWorkflow` with a host outage-extension limit of 100 and class age 60: a decision minted under Registry selection `{T1:70}` is refused at execute under a rebuilt workflow over `{T1:90}` with the approval re-issued (`PermissionError`, one durable `EffectTimeRefusal [authorization_binding_changed]`, no attempt, destination untouched). The complementary diff is base `{approval_commitment, catalogue_digest}`, ECB `{digest, effective_profile_digest}`. JOINT with `catalogue_digest` and `approval_commitment`; not independently isolated. Bounded technical record, same-lineage, not acceptance."

## 7. Control C0: `test_FXE_JOINT_C0` (SA unchanged executes exactly once)

Steps: world SA; `fa` constructed (approval bound), decided (`authorized`); restart workflow `f0` over the same SA material, same host, same store, approval untouched; live scratch mint under SA; complementary diff; `f0.execute`.
Preconditions: P01 `fa` constructed; P02 decide completes; P03 `authorized`; P04 `f0` constructed; P05 scratch mint completes; P06 scratch mint `authorized`.
| Id | Expected | Fails when | Establishes | Does NOT establish |
|---|---|---|---|---|
| C0-A01 | base diff `[]` | any leaf | the instrument reports no difference when none exists (no spurious base leaf from freshness stamps) | sensitivity |
| C0-A02 | ECB diff `[]` | any leaf | same for the ECB (checks that freshness fields do not leak into the ECB) | sensitivity |
| C0-A03 | `raised` None and `attempt_status` `acknowledged` | exception or other status | functional: the freshness-enabled fixture executes end to end (precondition for interpreting main) | - |
| C0-A04 | new refusal rows `[]` | any row | no spurious refusal | - |
| C0-A05 | destination calls == 1 | 0 or more than 1 | exactly one destination call | - |
| C0-A06 | classifier `bound` (evidence only) | other | corroboration | oracle |
| C0-A07 | persisted ECB eff == `own_commit(exp_A)` (ORACLE) | differs | second independent confirmation of A04 in a fresh world | - |
| C0-A08 | persisted `catalogue_digest` == `own_commit(exp_A)` (ORACLE) | differs | same for the base digest | - |
Dimensions: F only. If C0 fails the case is not interpretable (the lead scores main BLOCKED per protocol section 10 "control did not hold"; the harness itself scores the failing control rows FAIL, not BLOCKED, because C0 is a separate test; the lead applies the BLOCKED reading).

## 8. Control C1: `test_FXE_JOINT_C1` (approval NOT re-issued: guard first)

Steps: world SA decided; `fb` over SB constructed with `rebind=False` (approval still bound to the SA profile); `fb.execute`.
Preconditions: P01 `fa` constructed; P02 decide completes; P03 `authorized`; P04 `fb` constructed (Registry accepts 90 > 60); P05 profile dump leaf diff A vs B == `["freshness.max_age_extension_seconds"]`.
| Id | Expected | Fails when | Establishes | Does NOT establish |
|---|---|---|---|---|
| C1-A01 | `PermissionError` | other | fails closed | - |
| C1-A02 | text `authorization-critical inputs changed before effect` | differs | same raise site as main | - |
| C1-A03 | new refusal rows `[["runtime_authority_approval_mismatch"]]` exactly | extra reason (for example `authorization_binding_changed`) or other | G: the base approval guard refuses first and alone | behaviour of the ECB member |
| C1-A04 | `authorization_binding_changed` absent from every new refusal | present | G: the ECB comparison did not add its code (not consulted) | proof the ECB was not evaluated internally (inferred from the code's absence, as D-1 Q3-E1) |
| C1-A05 | vocabulary `["runtime-authority-reasons/0.1"]` | differs | label | - |
| C1-A06 | new attempts 0, total attempts 0 | any | no attempt | - |
| C1-A07 | destination calls 0, unchanged | any | destination untouched | - |
| C1-A08 | journal decisions [1,1], refusals [0,1] | other | exactly one durable refusal | - |
Dimensions: G CAN, E CAN only to the guard boundary; M and I NOT APPLICABLE. This is guard-first evidence; it says nothing about the later effective-member comparison.

## 9. Control C2: `test_FXE_JOINT_C2` (neutral re-signed SA')

Steps: world SA decided; SA' = same record content re-signed under `selection_id sel-test-2`, `epoch 2`; workflow over SA' constructed (approval untouched, profile identical so commitment unchanged); scratch mint under SA'; complementary diff; execute.
Preconditions: P01 record texts equal, selection texts differ, ids `[sel-test-1, sel-test-2]`, epochs `[1,2]`; P02 `fa` constructed; P03 decide completes; P04 `authorized`; P05 SA' workflow constructed (Registry accepts the re-signed selection; UNVERIFIED at pin `a40fe755`, developer test l05 on pin `6f600ab1`); P06 held profile dump equal to SA's; P07 scratch mint completes; P08 `authorized`.
| Id | Expected | Fails when | Establishes | Does NOT establish |
|---|---|---|---|---|
| C2-A01 | base diff `[]` | any | rotation does not move the base binding | - |
| C2-A02 | ECB diff `[]` | any | rotation does not move the ECB (selection identity is not a member) | - |
| C2-A03 | executes `acknowledged`, no exception | other | rotation alone does not refuse | - |
| C2-A04 | new refusal rows `[]` | any | no refusal | - |
| C2-A05 | destination calls == 1 | other | - | - |
| C2-A06 | classifier `bound` (evidence only) | other | - | oracle |
| C2-A07 | identity `effective_policy_digest` equal SA vs SA' | differs | same effective policy identity | - |
Dimensions: F (control). Purpose: the SA vs SB difference in main is a record-CONTENT difference (raw value), not a selection-identity artefact.

## 10. Control C3: `test_FXE_JOINT_C3` (effective-map change widens the diff)

Steps: world SA decided; `fc` over SC (`{T1:50}`) constructed with the approval re-issued; scratch mint under SC; complementary diff; execute.
Preconditions: P01 `fa` constructed; P02 decide completes; P03 `authorized`; P04 `fc` constructed; P05 scratch mint completes; P06 `authorized`.
Derived exact diff (frozen): base `{runtime_authority.approval_commitment, runtime_authority.catalogue_digest}`; ECB `{digest, members.effective_profile_digest, members.families.0.effective_policy_digest}`. The profile dump differs from SA in `actions.<aid>.max_status_age_seconds` (50 vs 60) and `freshness.max_age_extension_seconds` (0 vs 10); `host_profile_digest` and the other members unchanged. This is the same ECB leaf set D-1 Q3-E2 observed (age 20, no freshness), so C3 doubles as a cross-check that adding the host freshness profile does not change the families leaf behaviour.
| Id | Expected | Fails when | Establishes | Does NOT establish |
|---|---|---|---|---|
| C3-A01 | held SC dump == harness-built dump (age 50, limit 0) | differs | F: formula at a third point incl. the `max(0, ...)` floor | - |
| C3-A02 | identity effective `{T1:50}` | differs | - | - |
| C3-A03 | base diff == base pair | other | joint base pair | - |
| C3-A04 | ECB diff == three leaves above | other | M(joint): the families leaf is observable and is what the main case removes | independent isolation |
| C3-A05 | `host_profile_digest` equal | differs | host leaf absent | - |
| C3-A06 | `claim_for(...)` == `joint` | other | classification | - |
| C3-A07 | `PermissionError` | other | E | - |
| C3-A08 | new refusal rows `[["authorization_binding_changed"]]` | other | E: durable refusal | attribution (generic code) |
| C3-A09 | new attempts 0 and total 0 | any | no attempt | - |
| C3-A10 | destination calls 0, unchanged | any | untouched | - |
Dimensions: M partial/joint, E CAN (joint), I CANNOT.

## 11. Failure conditions at case level (protocol section 12)
FAIL (case interpretable): any assertion A01-A32 failing; refusal reasons/exception differ from section 3; the destination is called; an attempt row appears; the base diff is not exactly the pair; the ECB diff is not exactly two leaves (or a families/host leaf appears: then the CE4 premise is falsified and that is the finding); `claim_for` returns `isolated end-to-end` (adverse; contradicts I1-I4); a control (C0..C3) assertion fails while its preconditions held.
BLOCKED (case not interpreted): any `P` precondition fails, in particular the Registry/adapter refuses a record value above the host (P04) or the extension limit is not composed as predicted so the dumps do not differ exactly in `freshness.max_age_extension_seconds` (P09), or construction/decide raises. The harness records a `BLOCKED` row, a `GATE` row, and `NOT EXECUTED` rows for the unreached ids, then stops the leg.
Never revised after the fact; correction only by a versioned successor.

## 12. Source uncertainties that could invalidate the fixture (UNVERIFIED, flagged)
1. U-A: a freshness-enabled GOVERNED workflow decides and executes on the tenant fixtures under `H.patch_clock`. Source support: `tests/test_final3_composed_binding.py::test_e01` (freshness profile, decide `authorized`, execute `acknowledged`) and `test_freshness.py` (non-governed). No developer test combines `GovernedClassAgeWorkflow` with a freshness profile through decide+execute (the F5 tests with freshness stop at profile checks and `selection_changed`). Mitigation: C0 (SA unchanged) is the control; its failure makes the case BLOCKED.
2. U-B: the pinned Registry `a40fe755` accepts r08-v2 record values above the host and a re-signed SA' (`epoch 2`). Source read: `compose_f5` `min` composition at the pin; developer tests g02/x02/l05 are on pin `6f600ab1`, not `a40fe755`.
3. U-C: `FreshnessProfile` in the host does not by itself add base-binding leaves (the binding carries `runtime_authority = extension` built from `profile`/`context` only; no freshness-derived member read in `_resolve`'s binding construction at `bounded.py:2560-2640`). C0-A01/A02 detect a spurious leaf.
4. U-D: the class age bound in decisions with freshness is `_class_age_bound` over zero extension rows (bound = 60); status ages in the tenant fixture equal NOW, so the status check passes. No extension row is recorded; A30 asserts `age_extensions` stays 0.
5. U-E: the refusal vocabulary label is `0.1` (code not in `CODES_ADDED_IN_0_2`); D-1 observed the same label for the same code without freshness; the label depends only on the reasons list.
6. U-F: a restart workflow over the same store with the same Registry material and approval executes (C0); same pattern as D-1 Q3-H0.
7. U-G: `age_extensions` attribute exists on the loaded run record (read via `getattr` with default 0; if absent, A30's age-extension component passes vacuously, which weakens only that sub-claim).
8. U-H: the candidate classifier values (`mismatch`, `bound`) are evidence only; a deviation there would FAIL A32/C0-A06/C2-A06 without implying a product defect in the refusal path.
9. U-I: the fresh-clock caveat: under freshness the dispatch gate compares the patched `_now` to a deadline computed from the same patched clock and also a real monotonic elapsed time (`bounded.py:1410-1432`); acceptable only if the control executes within the 60 s bound of real time (a slow runner could produce `check_expired_before_dispatch` in C0/C2, which the assertions would record as FAIL, not BLOCKED).
10. U-J: `bind_approval` mutates the shared resolver approvals; each test has its own world, so ordering across tests is irrelevant; inside main, the SA mint happens before the SB re-issue (by construction of the steps).
11. Same-lineage and non-blind: predictions informed by the dossier and D-1 (protocol section 2).

## 13. Exclusions honoured
No guard disabled, patched or bypassed; the only patch is the fixed synthetic clock of D-1; no store write, graft, reseal or forged member; no seam patch; approval re-issue only through `bind_approval`; no network; synthetic data; no pin-export or claim leg; no mutant.
