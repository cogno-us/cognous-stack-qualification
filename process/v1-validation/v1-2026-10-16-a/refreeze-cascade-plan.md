# V1 re-freeze cascade plan (v1-2026-10-16-a)

Status: DRAFT, read-only analysis. No PR merged, no component repo pushed, no pin edited. Date 2026-10-17.
Basis: component repos at the F5b pins (checkouts identical to the freeze-manifest shas), qualification `main` d1f5ba2, hub profile read at 8517818f, open PR heads fetched via REST.
Short names: RT runtime e20f92e1, CP control plane a34c3dc2, RP replay 79ba16d4, PK evidence pack 893aca8d, OD odes eb83220c, EX exchange 8be6c6b8, MF manifest 2c36bcd0. Primed names (RT') are the post-merge shas.

## 0. Findings in brief

1. **No cycle.** Hard-coded identities form a DAG (section 3). RT, CP, MF hard-code nothing; RP hard-codes {RT,CP,MF}; OD and PK hard-code {RT,CP,MF,RP}; EX hard-codes all six. Only the qualification repo hard-codes EX.
2. **Tree-hash identity is not supported by any component.** Every check is `git rev-parse HEAD` against a literal (EX `_git_source_identity`) or a string-equality accept-list (RP/OD/PK). The qualification harness records `HEAD^{tree}` (`run_security_runtime.py:65`, `v1_validation.py:163`) but gates on the commit. Adding tree identity means new verification code in four repos, so it is not recommended; sequence the merges.
3. **Minimum: 4 sequential component layers + 1 qualification PR + 1 full controller run = 6 rounds** (7 if the retained-evidence bootstrap in 4.3 is not fixed first). 3 of the 4 layers need a repin fix-up. 13 remediation PRs, 4 mechanical repin commits.
4. A merge commit's sha is unknown until merge, so each layer needs a repin after its predecessors merged. Intermediate states are not runnable: the chain refuses mixed generations by design (OD `common.py:62-65`), so RF entries cannot be qualified one at a time.
5. Component PR CI cannot catch a wrong repin literal: component `tests.yml` calls qualification reusable workflows at 39f03843/b3942698 that check out peers at pre-F5b shas (e.g. `cognous-governed-exchange--tests.yml:63-88`). Only qualification runs exercise the F5b tuple. Rehearse first (section 6).
6. Six open docs-only "stack-component-cleanup" PRs (runtime #94, exchange #29, odes #40, replay #32, pack #33, **control-plane #36**) each move their repo sha. CP #36 would invalidate the CP pin in six hard-coders plus qualification. Hold #36; fold the others into their layer or defer.

## 1. Where pinned identities are hard-coded

### 1a. Component repos at their current pins (line numbers at the pin)

| Repo | File:line | Constant / content | Identities | Role |
|---|---|---|---|---|
| exchange | experiments/odex_gax_imx_reference/gax_ref_runtime.py:68-76 | `CP_REVISION` .71, `MOLTBOT_REVISION` .72, `MANIFEST_REVISION` .73, `REPLAY_REVISION` .74, `ODES_REVISION` .75, `EVIDENCE_PACK_REVISION` .76 | CP RT MF RP OD PK | Gate: `_verify_refusal_profile_sources` :238-242 compares `git rev-parse HEAD` of each loaded checkout; manifest :279-285. Also stamped into exports :390, :405 |
| exchange | tests/test_exchange_input_and_source_repairs.py:330-335 | literal copy of the six constants | same six | Test equality |
| exchange | docs/security-runtime-f5b-profile-20261016.md:7-12; CHANGELOG.md:44 | pin table | six | Narrative (add a note, do not rewrite history) |
| replay | src/agent_replay_bundle/importers.py:61-65 | `CONTROL_PLANE_F5B_REVISION` .61, `MOLTBOT_F5B_REVISION` .62, `MANIFEST_F5B_REVISION` .63, `BOUNDED_F5B_PROFILE` .64 (`@a34c3dc2`), `MOLTBOT_F5B_PROFILE` .65 (`...-2.0.0@e20f92e1`, 8-char RT label) | CP RT MF | Gate: producer `repository_revision == MOLTBOT_F5B_REVISION` :344-346 else "unsupported Moltbot producer repository revision"; maps :67-77, :397, :711 |
| replay | docs/security-runtime-f5b-profile-20261016.md:3 | pin text | CP RT | Narrative |
| odes | src/odes/common.py:62-77 | `F5B_REVISIONS` :68-71 {manifest, replay, control_plane, moltbot_safe}; `SECURITY_RUNTIME_GENERATIONS` :73-74 keyed by CP sha | MF RP CP RT | Gate: exporter.py:158,534,609 and recipient_validator.py:86 select the exact tuple |
| odes | tests/test_security_cloud_regressions.py:198-201 | literal `F5B_REVISIONS` assertion | MF RP CP RT | Test equality |
| odes | docs/security-runtime-f5b-profile-20261016.md:3 | pin text | CP RT RP MF | Narrative |
| evidence_pack | src/agent_governance_evidence_pack/importer.py:80-83 | `F5B_REVISIONS` {manifest, replay, control_plane, moltbot_safe}; :86-87; :193-208 | MF RP CP RT | Gate: :204-206 requires Replay's `*_F5B_REVISION` constants (imported :200) to equal these, else "source mapping contradicts Evidence Pack contract" (RP and PK must carry the same RT literal) |
| evidence_pack | tests/test_f5b_generation.py:19-22, :36, :89, :106-107 | literal `F5B` dict; label `control-plane-security-runtime@a34c3dc2`; parametrize ids with 8-char CP/RT/MF prefixes | MF RP CP RT | Test equality |
| evidence_pack | CHANGELOG.md:5; docs/security-runtime-f5b-profile-20261016.md:3 | pin text | CP RT RP MF | Narrative |
| runtime, control_plane, action_manifest | none | no pinned peer identity | none | Sinks |
| hub 8517818f (frozen) | profiles/security-runtime-f5b-candidate-20261016.json:11-35; docs/releases/f3r-qualification-receipt-20261016.md:11-17; docs/releases/security-review-freeze-f5b-20261016/verification.json:5-29; docs/release-status.md:66 | all seven | all | Leave unchanged: a hub edit moves `FROZEN_HUB` (workflow x5, two helpers). The r1 profile lives in the qualification repo only |

No open PR diff touches these lines (pack #34 adds one `a34c3dc2` profile label in a new test; CP is unchanged).

### 1b. Qualification repo (outside results/)

| File:line | Content | Identities |
|---|---|---|
| .github/workflows/v1-validation.yml:240 / 241 / 242 / 243 / 244 / 246 | probe matrix `sha:` for RT / RP / PK / OD / CP / MF (EX has no probe row; Index :238 is RF-1) | RT RP PK OD (CP, MF unchanged) |
| .github/workflows/v1-validation.yml:386, :392 | matched-refund job `ref:` RT, CP | RT (CP unchanged) |
| .github/workflows/v1-validation.yml:136, :137, :332 | `--profile process/security-runtime-f5b-20261016.json` (scenario components come from the profile) | all seven, indirect |
| .github/workflows/v1-validation.yml:42, :69, :281 | `plan`, `freeze-verify`, `probe-suite --pins-manifest` read the ORIGINAL freeze-manifest; the `components` job runs each component's own suite at manifest shas (3 OS) | all seven, indirect |
| .github/workflows/security-runtime-f5b-qualification.yml:5, :39, :40 | original profile path; `tests/test_security_runtime_profiles.py:60` asserts exactly 2 occurrences, so leave unedited | indirect |
| process/security-runtime-f5b-20261016.json:18,22,26,30,34,38,42 | `components.*.revision` CP RT RP PK OD EX MF (sha256 a710b8c0 is pinned in the manifest) | all seven |
| process/v1-validation/v1-2026-10-16-a/freeze-manifest.json:34,58,64,70,76,82,88,94 (+ `qualification_file_hashes` :52) | `sha` entries | all seven. ORIGINAL, never edited |
| process/v1-validation/v1-2026-10-16-a/acceptance-map-03.json:6 | `control_plane@a34c3dc2...` | CP (unchanged) |
| suites/v1-scenarios/_d02_d05_d09_helpers.py:43, :47-49, :70-71 | profile path; `FROZEN_HUB/RUNTIME/CONTROL_PLANE` asserted against the profile | RT (CP, hub unchanged) |
| suites/v1-scenarios/_d06_d07_d08_helpers.py:39, :43-45, :73-74 | same | RT |
| suites/v1-scenarios/test_scn_c14.py:39-40 (used :121-124) | `PINS` {control_plane, moltbot_safe, replay} vs ODES package provenance | RT RP |
| suites/v1-scenarios/test_add_test_g1.py:82, :84-91, :109-170 | freeze runtime sha == `H.FROZEN_RUNTIME`; loaded pins == manifest (:84-88) and == profile (:89-91); retained junit evidence pins == loaded pins (:166-168, `pins_bad`) | all seven |
| suites/v1-scenarios/test_asw_s.py:78-79, :137 | profile RT/CP equal `H.FROZEN_*`; subprocess `--profile ...-20261016.json` | RT |
| suites/v1-probes/test_provenance_probes.py:62-69, :129-139 | expected pins built from the manifest (12 repos) | all seven |
| tools/v1_validation.py:62-73, :146-153, :158-167 | `plan`, profile-equals-manifest, fetch each manifest sha. No refreeze overlay exists (RF-1 changed only workflow lines) | all seven |
| tests/test_security_runtime_profiles.py:10, :37, :60 | asserts the original profile and workflow | leave unchanged |
| docstrings: suites/v1-probes/test_replay_probes.py:3; v1-scenarios/test_add_molt_verify.py:12; test_scn_c10.py:9; c12:9-12; c13:9-11; c14:9-10 | 8-char prefixes | cosmetic |
| results/** (3,496 files in results/v1-validation; results/security-runtime-f5b-20261016/*; reports/*) | retained evidence at the old pins | historical, never edited |

## 2. What each open PR invalidates

Every merge changes its repo's sha. Conflicts: the four runtime PRs and the four ODES PRs merge pairwise and sequentially without conflict (checked with `git merge-tree` and a scratch merge); replay #33/#34 and exchange #31/#32 conflict only in CHANGELOG.md. "More coming" are already open: replay #34 (F-10 unknown members), exchange #32 (F-17 generation fence).

| Repo / PRs | Sha invalidated | Repin required in | 8-char label |
|---|---|---|---|
| runtime #100 (F-04), #101 (F-08), #102 (F-09), #103 (docs, F-17/F-18 note) | RT e20f92e1 | RP importers.py:62; OD common.py:71 (+test :201); PK importer.py:83 (+test :22); EX gax_ref_runtime.py:72 (+test :331); qualification workflow :240 :386, profile :22, helpers, c14:39, g1, asw_s | RP `MOLTBOT_F5B_PROFILE` :65 |
| replay #33 (F-06/F-12), #34 (F-10) | RP 79ba16d4 | OD common.py:69 (+test :199); PK importer.py:81 (+test :20); EX gax_ref_runtime.py:74 (+test :333); qualification workflow :241, profile :26, c14:40 | none |
| odes #44 (F-03 docs), #45 (F-05), #46 (F-11), #47 (F-06/F-12) | OD eb83220c | EX gax_ref_runtime.py:75 (+test :334); qualification workflow :243, profile :34 | none |
| evidence pack #34 (F-06/F-12) | PK 893aca8d | EX gax_ref_runtime.py:76 (+test :335); qualification workflow :242, profile :30 | none |
| exchange #31 (F-13), #32 (F-17) | EX 8be6c6b8 | qualification profile :38 only | none |
| F-18 refund-intent (no PR yet) | RT or EX, wherever it lands | add to that layer | |

Behaviour (not identity) that changes qualification expectations: OD #46 requires bundle_version 0.2.0; EX #31 refuses a mismatched `evidence_refs` digest (ASW S02, 29 tests); RP #33 and PK #34 refuse the planted F-06/F-12 defects (D08, C23); OD #45 changes D06 export. Failure-register statuses move only after the r1 run.

## 3. Dependency order and cycle analysis

```
CP, MF (no PR)            unchanged sinks
RT (#100-#103) -> RP (#33,#34) -> OD (#44-#47) --\
                              \-> PK (#34) --------> EX (#31,#32) -> qualification r1
```
Edges "X hard-codes Y": RP->RT; OD->RT,RP; PK->RT,RP (and asserts RP's runtime constant equals its own); EX->RT,RP,OD,PK; qualification->all. Code imports agree (runtime imports control plane; odes and pack import replay; exchange imports replay, odes, pack). **No pair hard-codes each other.** Cycle-like couplings, both acyclic: (a) PK/RP lockstep on the RT literal (importer.py:204-206); (b) EX's strict check rejects any non-pinned OD, so EX must be last.

Cycle-breaking rule: none needed. The repo-native rule ("add alongside, not instead of", OD `common.py:62-64`) cannot apply to a runtime-only change, because generations are keyed by the CP sha and CP does not change. Decision D1 for the owner: replace the F5b literals in place (retained evidence is verified at the old pins only, consistent with the refreeze-log policy) instead of carrying two RT values per generation (new code in three repos). Recommended: in place; keep the exchange profile name `security-runtime-f5b-20261016` and give the r1 qualification profile its own `profile_id`.

Merge and repin order (a layer is a set of PRs that do not hard-code each other; merge them back to back with nothing else landing, then record main's head):

| Round | Merge | Repin commit pushed on the layer's first PR (shas known from earlier rounds) |
|---|---|---|
| L1 | RT #100, #101, #102, #103 (any order) -> RT' | none (RT hard-codes no peer) |
| L2 | RP #33, #34 -> RP' | RP importers.py:62 and label :65 to RT' |
| L3 (parallel) | OD #44-#47 -> OD'; PK #34 -> PK' | OD common.py:69,71 + test; PK importer.py:81,83 + tests (RP', RT'; same RT literal as RP) |
| L4 | EX #31, #32 -> EX' | EX gax_ref_runtime.py:72,74,75,76 + tests :331,333,334,335 (RT', RP', OD', PK') |
| Q | qualification PR (section 4), then one full controller run | five new shas |

Fix-up rounds: **3** (RP; OD+PK; EX). A fix-up cannot be precomputed because GitHub merge, squash and rebase commits are new objects. Only a fast-forward push of the exact verified head would make a sha known in advance and collapse the cascade to 2 rounds; that needs direct pushes to component main (protection bypass), an owner decision not assumed here.

## 4. Qualification files per re-freeze step

Policy (refreeze-log.json): one owner-authorised entry per component pin; originals never edited. Five entries: RF-2 RT, RF-3 RP, RF-4 OD, RF-5 PK, RF-6 EX (RF-1 Index is applied). Each needs owner authorisation (RF-1 precedent: explicit "yes"). They are applied together in one PR because mixed generations are refused.

### 4.1 Step 0, prepare now (no new shas; can merge before the cascade)
- `tools/v1_validation.py`: add `--refreeze-log` overlay (`from_sha -> to_sha`) to `plan`, `freeze-verify`, `probe-suite --pins-manifest`; `freeze-verify` also checks each `to_sha` belongs to the same repository and that the r1 profile equals manifest plus overlay. Original-manifest checks keep passing.
- `.github/workflows/v1-validation.yml` :42, :69, :281: pass `--refreeze-log`.
- `suites/v1-scenarios/_d02_d05_d09_helpers.py`, `_d06_d07_d08_helpers.py`, `test_add_test_g1.py`, `test_asw_s.py`, `test_scn_c14.py`: replace pin literals and the profile path with one new module `suites/v1-scenarios/_pins.py` that reads the profile named by env `V1_PROFILE` (default: the original). Later steps become data edits.
- `suites/v1-probes/test_provenance_probes.py:62-69`: build `expected_pins` through the overlay.
- `suites/v1-scenarios/test_add_test_g1.py:109-170`: retained-junit rule (4.3).
- New `tests/test_refreeze_overlay.py`. Do not edit `tests/test_security_runtime_profiles.py`.

### 4.2 Step Q, after L4 (one PR)
Common to all entries: new `process/security-runtime-f5b-20261016-r1.json` (copy of the original; `predecessor_profile` = the original, `refreeze_ids` RF-2..RF-6, five new `revision`s, CP and MF unchanged, `selected`, `reference_release_authorized`, `production_deployment_authorized` all false); `process/v1-validation/v1-2026-10-16-a/refreeze-log.json` (append RF-2..RF-6 with from/to, PR list, behaviour_changes, historical results at from_sha, status); `.github/workflows/v1-validation.yml` :136, :137, :332 (`--profile ...-r1.json`; `V1_PROFILE` env for the scenarios job).

| Entry | Additional qualification edits |
|---|---|
| RF-2 RT -> RT' | workflow :240, :386 |
| RF-3 RP -> RP' | workflow :241 |
| RF-4 OD -> OD' | workflow :243 |
| RF-5 PK -> PK' | workflow :242 |
| RF-6 EX -> EX' | none (EX enters only through the profile) |

If Step 0 was skipped, also edit: `_d02_d05_d09_helpers.py:43,48`, `_d06_d07_d08_helpers.py:39,44`, `test_scn_c14.py:39-40`, `test_add_test_g1.py:82,89`, `test_asw_s.py:137`. Never edited: freeze-manifest.json, process/security-runtime-f5b-20261016.json, hub files, `security-runtime-f5b-qualification.yml`, `tests/test_security_runtime_profiles.py`, anything under results/ (the r1 run adds a new `results/v1-validation/v1-2026-10-16-a/<run>/` directory). Optional later: docstring prefixes, failure-register.json statuses, requirements.json, report text.

### 4.3 Retained-evidence bootstrap (test_add_test_g1)
`_latest_retained_junit` selects the newest retained run, whose evidence carries the old pins, so `pins_bad` fails against r1 pins until an r1 run is retained, which needs a passing run first. Fix in Step 0: compare retained evidence with the pin set in force for that run (via the refreeze-log) or take the newest retained run at the current pins and list older runs as historical. Otherwise add one retention PR and one re-run (round 7).

## 5. Risks

1. Merge method and branch protection are unknown. If "up to date before merge" is required, each same-repo PR needs its own rebase and CI. Mitigation: merge a layer as one integration PR (merges are conflict-free) or use a merge queue.
2. Intervening merges: docs PRs #94, #29, #40, #32, #33 and above all CP #36 reopen the cascade. Freeze main of all seven repos for the window.
3. A wrong 40-hex literal passes component CI (finding 5). After each layer, `git grep` the previous sha in that repo (expect only history lines) and rehearse (section 6).
4. PK/RP lockstep on the RT literal: updating one without the other fails PK at import.
5. Verdict scope: a verdict applies only after a full controller run at the new pins; intermediate runs are partial evidence. The hub profile keeps the old pins and still labels F5b nonselected; r1 diverges from it by design (record in the refreeze-log).
6. Tags: `public-reference-f5b-20261016` stays on the old shas (freeze-verify checks the RT tag against the original manifest). New `-r1` tags are an owner decision.
7. Behaviour changes in section 2 (OD #46, EX #31) can turn retained expectations red; record as findings, never relabel.
8. F-18 is open; if it lands in RT or EX, repeat the affected layers.

## 6. Estimate and rehearsal

- Rounds (merge + CI): L1 1, L2 1, L3 1 (OD and PK parallel), L4 1, Q 1, controller run 1 = **6 typical** (7 with 4.3). Worst case if every same-repo PR needs its own rebase and CI: L1 4, L2 2, L3 4, L4 2, Q, run = 14.
- Counts: 13 remediation PRs, 1 qualification PR, 4 repin commits, 0 new component PRs.
- Rehearsal before L1: in scratch clones merge the PRs, make local merge commits, rewrite the literals from the 1a/1b line list into a throwaway r1 profile, serve the clones as `file://` remotes and run `tools/run_security_runtime.py --profile <r1> --prepare-work`. This proves the edit set is complete without overriding any identity check; the real rounds then only substitute shas. Nothing is pushed to component repos.
