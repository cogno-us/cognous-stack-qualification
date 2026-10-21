# V1 known limits

## D15: V1 claim narrowed to the passing rows

**V1 as validated = the 39 passing rows; the rest are known limitations pending ODES re-engineering.**

Decision D15 was made on 2026-10-17 after the final-linux-1 result (Actions run 39032930011). It is disclosed, not pre-registered: the scope was reduced after the results were seen. On the owner's direction, the V1 mandatory claim is narrowed to the 39 requirement rows that PASSED in final-linux-1. The 36 mandatory rows that did not pass (2 FAIL, 29 INCONCLUSIVE, 5 NOT RUN) are moved out of the mandatory claim and listed below as known limitations, to be addressed after the ODES contract re-engineering (`docs/engineering/ODES-INTERCOMPONENT-CONTRACTS.md` in `cogno-us/open-decision-evidence-standard`, in progress and not yet merged when this was written).

This is a scope reduction, not a relabelling. No requirement's status, selector, adequacy declaration or result was changed or deleted. Each moved row carries `mandatory: false` and a `scope_reduction` record (decision, final status, category) in `requirements.json`, and keeps its real status. The verdict rule is unchanged. The harness reports a full-catalog status block over all rows, so a moved row is never counted as PASS. The reduced-scope verdict is PASS; the same rule over the pre-reduction mandatory rows is FAIL. Neither is a release decision.

The 36 moved rows (re-evaluation: `results/v1-validation/v1-2026-10-16-a/final-linux-1-39032930011-reduced-scope/`):

### Failed: fix merged outside the pinned tuple (F-15, D11) (1 rows)

- **ER-03-1** (FAIL): probes-authority: no delay limit linked to any consequence tier (F-15); fix merged in institutional-governance (cbc39e79) but outside the pinned tuple (fb3d9793). Update 2026-10-17: the authority pin has since moved to cbc39e79 (RF-17, profile r4); this row is not re-run, so it keeps this recorded result until a controller run at the r4 pins.

### Failed: design limit accepted (F-19, D14) (1 rows)

- **SCN-C04** (FAIL): copied evidence still inflates supporting_weight (0.8 to 4.0 for five copies) at Index d17b8ac2; 4 of 10 cases fail (F-19, D14).

### Not run: unimplemented scenarios (D9) (5 rows)

- **SCN-C05** (NOT RUN): unimplemented (D9); no test exists; coverage mapping UNIMPLEMENTED.
- **SCN-C15** (NOT RUN): unimplemented (D9); no test exists; coverage mapping UNIMPLEMENTED.
- **SCN-C19** (NOT RUN): unimplemented (D9); no test exists; coverage mapping UNIMPLEMENTED.
- **SCN-C20** (NOT RUN): unimplemented (D9); no test exists; coverage mapping UNIMPLEMENTED.
- **SCN-C21** (NOT RUN): unimplemented (D9); no test exists; coverage mapping UNIMPLEMENTED.

### Inconclusive: partial coverage (D13) (29 rows)

- **ER-04-4** (INCONCLUSIVE): process check over the few schema-changing PRs in history; two had notes only outside the same PR (recorded as timing gaps).
- **SR-2** (INCONCLUSIVE): C22 equal-conditions comparison vs a harness-defined conventional control (catalog gives none); hard gates asserted on V1; false blocks, latency and review burden report-only per D5; only 4 permitted cases; human effort not measured.
- **SR-3** (INCONCLUSIVE): lexical screen of 12 pinned public repos only; optional components not scanned; not a semantic review of logic.
- **SCN-D01** (INCONCLUSIVE): named synthetic assertion only (matched refund battery); catalog mapping PARTIAL; not whole-catalog acceptance.
- **SCN-D02** (INCONCLUSIVE): no tenant concept on the exchange route; no OpenShell destination.
- **SCN-D03** (INCONCLUSIVE): named synthetic assertion only (matched refund battery); catalog mapping PARTIAL; not whole-catalog acceptance.
- **SCN-D04** (INCONCLUSIVE): named synthetic assertion only (matched refund battery); catalog mapping PARTIAL; not whole-catalog acceptance.
- **SCN-D05** (INCONCLUSIVE): reference has no native multi-part operation or explicit cancel call; parts composed from claims on a shared budget.
- **SCN-D06** (INCONCLUSIVE): reference has no ingress limiter, typed INGRESS_SATURATED refusal or listener; measurements report-only per D5.
- **SCN-D07** (INCONCLUSIVE): no external anchor exists; some restores re-admit effects after history erasure (recorded as limitations).
- **SCN-D08** (INCONCLUSIVE): covers planted defects in five artifact families, not every stimulus class beyond the catalogue.
- **SCN-D09** (INCONCLUSIVE): raw SQL by the database holder and OpenShell routes are out of model.
- **SCN-C01** (INCONCLUSIVE): tenant variants and OpenShell destination not covered.
- **SCN-C02** (INCONCLUSIVE): tenant variants and OpenShell destination not covered.
- **SCN-C03** (INCONCLUSIVE): run at re-frozen Index d17b8ac2 (RF-1); BitRep verification is not integrated into the Index route; all 87 scenario cases pass.
- **SCN-C06** (INCONCLUSIVE): observer independence beyond an in-process oracle not exercised.
- **SCN-C07** (INCONCLUSIVE): residual check-to-commit race recorded as evidence, not a failure (C0 default).
- **SCN-C08** (INCONCLUSIVE): no OS-level kill for routes A and C (BaseException crash model); power loss not claimed.
- **SCN-C09** (INCONCLUSIVE): tenant and OpenShell variants not covered.
- **SCN-C10** (INCONCLUSIVE): no OpenShell destination, container isolation or credential broker in the reference.
- **SCN-C11** (INCONCLUSIVE): no credential broker in the reference; local-credential holder bypass is characterised.
- **SCN-C12** (INCONCLUSIVE): recorded adequacy note: executor export silently dropped injected unknown members (F-10, since verified at test level in final-linux-1); coverage otherwise partial.
- **SCN-C13** (INCONCLUSIVE): HMAC and content digest only; no public-key signature path; absent/unavailable states not emitted by producers.
- **SCN-C14** (INCONCLUSIVE): ODES as an optional absent consumer not covered.
- **SCN-C16** (INCONCLUSIVE): no exchange-route budget case; no per-agent quotas or replenish API in the reference.
- **SCN-C17** (INCONCLUSIVE): authority writers have no compare-and-set (unsupported coordination); exchange route covers grant revision and policy version only.
- **SCN-C18** (INCONCLUSIVE): sub-delegation unsupported by the reference; exchange route not covered.
- **SCN-C22** (INCONCLUSIVE): conventional control defined by the harness (catalog gives none); only 4 permitted cases; human effort not measured; metrics report-only per D5.
- **SCN-C23** (INCONCLUSIVE): prohibited_access seeded only in producer artifacts.

ADD-AUTH-RA (F-16, D10) is also a failing row, but it was already non-mandatory before D15 and is not listed above.

Earlier content of this page follows unchanged.

---

This page lists what the V1 claim does not cover. Every item below is a limit of what V1 claims. None of them is a pass, and none of them changes a requirement status, selector or verdict rule. The decisions are recorded in `process/v1-validation/v1-2026-10-16-a/preregistration.json` (D4 to D14) and the failures in `failure-register.json`.

Decisions D10 to D14 were made on 2026-10-17, after the refreeze-r1b result. They are disclosed, not pre-registered.

## Failures accepted as known limits

- **F-16, runtime-authority addendum (ADD-AUTH-RA, D10).** Six behaviours in the addendum text are not implemented: component version binding, age, criterion reference, freshness ordering, reopen predicates and unmapped-code trend. They are deferred beyond V1. The row stays FAIL.
- **F-18, refund-intent profile (ADD-C2C-BI, D12).** The opt-in refund-intent profile cannot be combined with route A. This exact combination fails closed against the F5b effective-grant destination, so it refuses rather than acting. It is documented as unsupported and the runtime is not changed.
- **F-19, copied evidence in the Index (SCN-C04, ER-02-4b, D14).** The Index counts copied evidence as extra supporting weight because it has no independence mechanism, so copies can raise support. Probe ER-02-4b checks the independence count only (duplicated evidence does not raise it); it does not check `supporting_weight`, which is what SCN-C04 fails on, so a passing ER-02-4b does not contradict this limit. This is also stated in `BITREP_LINK_ATTESTATION.md`.

## Failure with a fix pending

- **F-15, tier delay limit (ER-03-1, D11).** The tier table declared no delay limit at the original pin. The fix is merged as cogno-us/cognous-institutional-governance#51 (main cbc39e79) and the authority pin now points at it (refreeze entry RF-17, profile `process/security-runtime-f5b-20261016-r4.json`; the probe revisions that came with the bump are in `docs/authority-probe-rebaseline.md`). The authority probes pass 23 of 23 locally at cbc39e79, but no controller run has executed at the r4 pins, so ER-03-1 keeps its recorded FAIL in the retained final-linux-1 results. Status FIXED-UNVERIFIED; a controller run at the r4 pins is what can verify it.

## Rows with partial coverage (D13)

These 29 rows were declared adequacy "partial" before the run. The V1 claim is narrower than full catalog coverage, and their statuses are unchanged:

ER-04-4, SR-2, SR-3, SCN-D02, SCN-D05, SCN-D06, SCN-D07, SCN-D08, SCN-D09, SCN-C01, SCN-C02, SCN-C03, SCN-C04, SCN-C06, SCN-C07, SCN-C08, SCN-C09, SCN-C10, SCN-C11, SCN-C12, SCN-C13, SCN-C14, SCN-C16, SCN-C17, SCN-C18, SCN-C22, SCN-C23, ADD-C2C-EVID, ADD-ASW12.

The reason for each row is in the `adequacy_note` field of `requirements.json`.

## Catalog scenarios not implemented (D9)

C05, C15, C19, C20, C21 and A01 are unimplemented. No test exists for them. They stay NOT RUN and are not marked NOT APPLICABLE. Mandatory ones keep the verdict from reaching PASS.

## Earlier deferrals and removals

- **Extension families (D4) and governed memory (D6)** are outside the V1 claim.
- **PRP and TFA (D8)** were removed from the stack. ER-11 and ER-13 are NOT APPLICABLE citing D8.

D4: no extension families in V1, all eight deferred. D6: governed memory is out of V1, and its addenda rows are NOT APPLICABLE citing D6.

## Route B export is not accepted by Replay (F-24, found 2026-10-17)

The runtime's atomic local executor (route B) returns status `unknown` with a recovery observation after a post-commit failure. Replay at the validated pin rejects that export on its public import path. The fix for F-20 to F-22 covered route C only. Qualification scenario SCN-C06 route B passes because it never exports into Replay, so that pass does not show Replay can consume route B. This is outside the reduced V1 claim. Update 2026-10-17: fixed in Replay (cognous-replay-bundle #37, main 287a2b6b) and covered by ODES contract fixtures (open-decision-evidence-standard #52). The P4 pin advance moved the pins to Replay 9aab3f6c and the SCN-C06 route-B round-trip scenario was added (see Update P4 below). Status FIXED-UNVERIFIED.

## Evidence pack cannot re-validate route-B bundles (F-25, found 2026-10-17)

Replay now imports the real route-B post-commit exports (F-24) and retains the recovery report as `executor_recovery_report`. The evidence pack at its pinned revision does not map that record type back when it re-validates a retained Replay bundle, so it rejects all three captured route-B bundles. Outside the reduced V1 claim. Status FIXED-UNVERIFIED (fixed in evidence pack #36, route-B tests run since P4).

## Lifecycle contract conformance divergences (F-26 runtime, F-27 Replay, found 2026-10-17)

The P2 conformance suites for the execution-attempt lifecycle contract (0.1.0-draft) found five runtime divergences (F-26, including the OpenShell `unknown`-with-validated-observation path, N-1) and twelve Replay divergences (F-27). The control plane conforms in every case it exercised. Each divergence was pinned as a strict expected failure in the component's own test; none was fixed at the time (they are fixed since, see the updates below), and none is part of the reduced V1 claim. They are handled in the decoupling plan (cogno-us/cognous-control-plane#38), P3.


### Update 2026-10-17 (P3)

F-25, F-26 and F-27 are fixed at component level and unverified at row level (pins unchanged): evidence pack #36, runtime #106, Replay #40. Remaining: Replay step B (legacy layout refusal and RP-6), the route C contract gap, and the pin refresh, all later in the decoupling plan. No verdict changed.

### Update 2026-10-17 (P4)

The pins moved to the P4 generation (refreeze entries RF-11..RF-16, profile `process/security-runtime-f5b-20261016-r3.json`): Control Plane 26a7e659, runtime 3024ef6e, Replay 9aab3f6c, evidence pack 54df6984, ODES c5f4e2d0, exchange 914db78d. For the boundaries governed by the execution-attempt lifecycle contract (runtime to Replay, Control Plane to Replay) compatibility is now gated by a contract-version matrix instead of sha equality: each component declares the contract it conforms to and the sha stays as the recorded tested revision (`docs/contract-matrix.md`). The other components keep the sha pin until a contract covers their boundary. The matrix proves the paper trail only; behaviour is shown by the component conformance suites and the scenarios.

- F-24, F-25, F-26, F-27 and the new F-28 are fixed and carry P4 verification evidence but stay FIXED-UNVERIFIED: no controller run has executed at the r3 pins (P4 does not run it); the P5 full run is what can verify them. No requirement verdict changed.
- F-28: Replay refused a normal executed route-B export (control_plane_evidence carried the local authority receipt). Fixed in Replay step B (cognous-replay-bundle #43) with identity binding checks.
- SCN-C06 now includes a route-B round trip (real AtomicLocalControlPlaneExecutor export, Replay import, evidence pack re-validation) for the executed case and the three recovery variants. The row stays partial (INCONCLUSIVE): the round trip is a named synthetic assertion, not whole-scenario acceptance.
- Replay step B refuses the legacy recovery layout, `observation: {}` and unknown with a validated applied/partial observation. Historical executors that predate the lifecycle contract still export those shapes; the Replay cross-component suites assert the refusal per row (stack-qualification #87, #88), and the typed-refusal suite normalises `{}` to null only after asserting the refusal. The validated-unknown Replay fixture still waits for a Control Plane that emits an unknown observation.
- Remaining for P5: remove the hard peer pins (component tables and the pin-only gates), vendor contracts for the pack, ODES and exchange boundaries, and run the full qualification at the r3 pins. The route C contract gap and the choice of unknown with a null observation after a timeout still await owner decisions.

### Update 2026-10-18 (Programme 2 pin batch)

The pins moved to the Programme 2 generation (refreeze entries RF-18..RF-22, profile `process/security-runtime-f5b-20261016-r5.json`, suite generation `p2`): Control Plane 3cd17ead, runtime 11de097c, Replay 46e8bd7c, evidence pack 4fbbd344, ODES 0663d5a2; exchange 914db78d, the action manifest and the constitutional authority are unchanged from r4. The contract-version matrix evaluates both boundaries as conforming at the new revisions (the vendored lifecycle contract declarations are unchanged). The independent verifier reference for the mutation harness is f99a6543.

- No qualification-controller run has been made at the r5 pins; every earlier verdict is historical and is not transferred. The FIXED-UNVERIFIED rows stay FIXED-UNVERIFIED.
- The bounded Replay-phase cases of the security-runtime chain suite run at the `p2` generation (24 of 24 pass locally). The ODES export cases (7) and the exchange reference-runtime cases (5) of the full phase do not pass at `p2` yet: the ODES exporter and the exchange reference runtime carry revision tuples for the earlier generations only. A tuple for the Programme 2 producers is needed in ODES and in the exchange (a new exchange compatibility profile) before the full phase can pass; the probes were not changed to hide this.
- The retained verifier-mutation corpus (run 5) stays at verifier 0a43a7f0 and is historical.


### Update 2026-10-18 (Programme 2 re-pin r6)

Three gap fixes closed the 12 full-phase chain cases that did not pass at the r5 pins. The pins moved again (refreeze entries RF-23 and RF-24, profile `process/security-runtime-f5b-20261016-r6.json`, suite generation `p2`): ODES 0663d5a2 to 81979784 (ODES #97 adds the P2 compatibility tuple, so the exporter accepts the Programme 2 producers) and exchange 914db78d to ba9fa160 (exchange #37 adds the compatibility profile `security-runtime-p2-20261018` and #38 corrects its ODES pin to 81979784; the exchange head was d8d44c1 after the bytecode cleanup #36 and before #37). The control plane 3cd17ead, runtime 11de097c, Replay 46e8bd7c, evidence pack 4fbbd344, the action manifest and the constitutional authority are unchanged from r5. The `p2` branch of the chain suite's ODES generation helper now selects the P2 tuple; no probe assertion was changed.

- No qualification-controller run has been made at the r6 pins; every earlier verdict is historical and is not transferred. The FIXED-UNVERIFIED rows stay FIXED-UNVERIFIED.
- The full-phase cases of the security-runtime chain suite were run locally and read-only at the `p2` generation with the r6 pins (result recorded in the pull request that introduced r6). This is not a controller run and carries no verdict.
- The exchange profile `security-runtime-p4-20261017` still refuses the Programme 2 producers (identity mismatch), as intended: the compatibility names are exact per generation.

### Update 2026-10-18 (Programme 2 consistency fixes)

A read-only consistency check at the final pins (no controller run) found qualification files that still described the earlier generation. They are corrected here; no verdict was changed and no assertion was relaxed.

- The controller workflow's `V1_PROFILE` pointed at the r4 profile while the refreeze overlay selects r6. It now names r6, and a unit test asserts that the workflow value equals the profile the overlay selects.
- The control-plane probe that checks the registry-0.2 code kinds expects exactly 158 codes (it expected 157).
- **Owner review item: shared-budget claims with a differing value are now refused.** The atomic route binds the claim's `max_effects` to the envelope's `effective_max_effects` (runtime 11de097c). A shared-budget claim whose budget limit differs from the envelope's cap is refused with `execution claim operation mismatch: effective_max_effects`; before, a shared budget of N could be spent by envelopes that each carried a cap of 1. The coordinator kept the binding strict. The scenario helpers (C16, C17, C18, C22, D05 and the C2C bi-directional cases) now build the envelope with the same cap as the claim, so the budget flow is what is tested. Whether a shared budget should be allowed to differ from each envelope's cap is for the owner to decide at the end review.
- SCN-D07 restore boundary, three characterisations changed because the runtime improved: the refusal by effect uniqueness reports the exception class only (`IntegrityError`, no SQL text; the test now pins the exact string), and restoring the authority tables to a pre-revocation snapshot no longer reopens a revoked grant (the replay is refused with `authoritative grant state invalid`; the case was renamed `c1_authority_tables_alone_after_revoke_refused_revocation_is_final`). The retained controller results keep the old case name. Precisely what that restore covers: `C1_AUTHORITY_TABLES` is grants, approvals, policies, evidence, claims and budgets; it does not include the revocation table `authority_grant_revocations_v1`, which the runtime keeps separately, so that case restores the authority tables while the revocation memory stays in place. A restore that rolls the revocation table back as well reopens the grant (see the next update section and the case `c1_authority_tables_and_revocations_after_revoke_reopens`).
- Two tripwires were extended without loosening them. SCN-D07's anchor scan classifies one use of the word in the control plane's new `freshness.py` (a deadline "anchored" at the opening of the check, not a restore anchor) by exact file and exact line text, so any other occurrence still fails. SCN-D09's call-site inventory declares the opt-in `dedupe_destination.py` and `delayed_commit_destination.py` wrappers (each calls the same destination commit path through `super().commit` and is reached only through the executor).
- The batch-1 adversarial components file now names the revisions of the Programme 2 mains (verifier f99a6543, Replay 46e8bd7c, evidence pack 4fbbd344, ODES 81979784); batch 1 does not feed any verdict.
- Not changed: the ODES probe that needs `P4_PROFILE_VERSION` and `P2_PROFILE_VERSION` named in an ODES document (an ODES documentation fix), the Q3 registry fallback, and the orchestrator overlay tests. The four SCN-C04 Index-copy failures are the known baseline.


### Update 2026-10-18 (Programme 2 re-pin r7)

Two further pins moved (refreeze entries RF-25 and RF-26, profile `process/security-runtime-f5b-20261016-r7.json`, suite generation `p2`): ODES 81979784 to e2cbc0dc and exchange ba9fa160 to 06f58c32. ODES #98 is documentation only: it adds `docs/security-runtime-p4-p2-profiles.md`, which names the P4 and P2 profile versions as non-selected candidates so that the probe er093 (every extension version is documented and labelled proposed) passes; no source, schema, validator or fixture changed. Exchange #39 moves the ODES pin of the compatibility profile `security-runtime-p2-20261018` to e2cbc0dc, because the exchange strict source check compares each checkout's Git HEAD to the pinned string exactly, so a docs-only change still needs the pin. The control plane 3cd17ead, runtime 11de097c, Replay 46e8bd7c, evidence pack 4fbbd344, the action manifest and the constitutional authority are unchanged from r6. The controller profile named by `V1_PROFILE` in `v1-validation.yml` is r7 (a unit test asserts it equals the profile `select_profile` picks).

- No qualification-controller run has been made at the r7 pins; every earlier verdict is historical and is not transferred. The FIXED-UNVERIFIED rows stay FIXED-UNVERIFIED.
- The full-phase cases of the security-runtime chain suite were run locally and read-only at the `p2` generation with the r7 pins (result recorded in the pull request that introduced r7). This is not a controller run and carries no verdict.

### Update 2026-10-18 (Programme 2 consistency review cleanup)

An independent static review at the final pins found text and test gaps. They are corrected here; no verdict was changed, no assertion was relaxed and no pin or profile moved.

- **New observed limit (SCN-D07).** The runtime keeps revocations of destination grants in its own table, `authority_grant_revocations_v1`, created at the first revocation. The case `c1_authority_tables_and_revocations_after_revoke_reopens` restores the authority tables and that table (absent from a pre-revocation snapshot, so restored to empty) to the pre-revocation snapshot: the replay executes and one effect is admitted. Local-only persistence has no external anchor for the revocation, the same family as the other ACCEPTED_REPLAY rows. The earlier case that restores the authority tables alone is unchanged and stays refused.
- **Contract content under one draft label.** The ODES contracts `execution-attempt-lifecycle` and `verification-report` have different content under the same `0.1.0-draft` label: the contract matrix gates on the content at ODES a9db024c and the control plane, runtime and Replay vendor that copy, while ODES e2cbc0dc carries the hardened README, schema and validator (decision 32) and the verifier vendors the hardened schema. For example, a sha256 digest with a trailing newline passes the older copy and fails the hardened one. The matrix rule that a draft version string alone is not enough therefore does not see this divergence; the earlier sentence that the vendored declarations are "unchanged" refers to the declared contract versions, not to the content of the files. Accepted until the first contract freeze, when all components and the verifier are re-vendored to one content. Owner review item.
- **Mutation catalogue 3.2, H4.** `H4.destination-row-dropped-uncorroborated` was reclassified from expected reject to an expected-accept known-limit control (qualification #111, verifier `docs/tiers.md`): it is excluded from the missed-detection and false-acceptance counts and is not a detection claim. The H8 absent-file runs are input-error controls (#110). Both are disclosed in the catalogue and the verifier's tier documentation.
- **Corrections to earlier entries (the entries themselves are not edited).** RF-22's `docs/ODES-TIME-SEMANTICS.md` is at `docs/engineering/ODES-TIME-SEMANTICS.md` in the ODES repository. Its recipient-expiry wording "inclusive of the boundary instant" is wrong: validity windows are half-open, an instant equal to `expires_at` is expired (decision 34-A, 35-B); deadlines are the inclusive ones. RF-24's `historical_results_at_from_sha` names a run range (final-38962759690 and later runs through refreeze-r1b-39025887085) where RF-18..RF-23, RF-25 and RF-26 use the plain wording; the meaning is the same: results at the earlier pins are historical and are not transferred, and no run exists at the new pins. RF-24 also names ODES 81979784 in the exchange profile, which exchange #39 later moved to e2cbc0dc (RF-26). The `process/v1-validation/v1-2026-10-16-a/failure-register.json` policy "Frozen pins are not moved" and its VERIFIED statuses refer to the pins of the retained run final-linux-1; the pins have since moved through the refreeze overlay (see the failure-register notes).
- **Package versions are not contract versions.** `pyproject.toml` versions (verifier 0.1.0, Replay and ODES 0.2.0) are package or format numbers. The contract versions are the `0.1.0-draft` strings in the contract files; every contract is still draft and none is frozen.
- **Test changes.** The Q3 fallback to the 0.1 reason registry in `suites/v1-probes/test_authority_ra_probes.py` is removed (the probes read the 0.2 registry directly; a checkout without it fails), and stale 157-code comments now say 158. Adversarial batch 1 gained a T05 exact-mode agreement case (132 passed, 4 xfailed at the final revisions).
- No qualification-controller run has been made; every earlier verdict is historical and is not transferred.


### Update 2026-10-18 (Programme 2 re-pin r8)

Two further pins moved (refreeze entries RF-27 and RF-28, profile `process/security-runtime-f5b-20261016-r8.json`, suite generation `p2`): ODES e2cbc0dc to cdf704c8 and exchange 06f58c32 to 8721e8d3. ODES #99 is documentation only: it corrects the lifecycle and verification-report README wording, the destination-ledger and effect-reversibility README fixture counts, the time-semantics conformance rows (re-read against control plane 3cd17ead and runtime 11de097c) and records decision 36 (the same-label content divergence described above); no source, schema, validator or fixture changed. Exchange #40 moves the ODES pin of the compatibility profile `security-runtime-p2-20261018` to cdf704c8, for the same reason as exchange #39: the strict source check compares each checkout's Git HEAD to the pinned string exactly, so a docs-only change still needs the pin. The control plane 3cd17ead, runtime 11de097c, Replay 46e8bd7c, evidence pack 4fbbd344, the action manifest and the constitutional authority are unchanged from r7. The controller profile named by `V1_PROFILE` in `v1-validation.yml` is r8 (a unit test asserts it equals the profile `select_profile` picks).

- No qualification-controller run has been made at the r8 pins; every earlier verdict is historical and is not transferred. The FIXED-UNVERIFIED rows stay FIXED-UNVERIFIED.
- The full-phase cases of the security-runtime chain suite were run locally and read-only at the `p2` generation with the r8 pins (result recorded in the pull request that introduced r8). This is not a controller run and carries no verdict.
- Adversarial batch 1 was last run at ODES e2cbc0dc; `components.json` names cdf704c8, which differs by documentation only, and batch 1 was not re-run for it.

### Update 2026-10-18 (workflow and tooling hardening)

Workflow inputs are validated and passed through the environment, the aggregator reads plan, freeze and result records only from fixed artifact locations and rejects duplicates, Actions are pinned by commit SHA, pilot installs are hash-locked, and the Wiki importer has byte caps (details and residuals in `security-residuals-20261016.md`). Open limits: the `python:3.12-slim` base image is not digest-pinned (registry unreachable when this was written); the owner has configured the reviewer-gated environment `provider-keys` (provider keys stored there as environment secrets) and the branch `evaluation/prp-openai-20261015` is already deleted; the repo-level copies of the keys remain until the owner removes them after this change is on `main`. No pin, profile or refreeze value changed and no controller run was made, so earlier verdicts remain historical.

### Update 2026-10-19 (Programme 2 re-pin r9, hardening probe suite)

The local hardening probe suite `suites/fix2-probes` was re-measured at the main heads of the nine components (ODES 4bf12128, verifier dc09a98f, Replay 2a7963b1, control plane 2bac7875, action manifest ff549082, runtime c4a05883, ergonomics e996a53f, evidence pack 80e24650, exchange bf314f38), on Python 3.13 and 3.14 with the same result. The suite is run locally and is not part of any qualification run, so this carries no controller verdict. No assertion, fixture or expected value was changed.

- Result: 207 passed, 6 expected failures, 0 reported failures (the previous measurement was 191 passed, 22 expected failures). With `--runxfail` the same 6 probes are the only failures.
- 16 probes that were strict expected failures now pass, and their marks are removed so that they run as controls: the 15 ODES attempt-identity probes (the execution-attempt-lifecycle reference validator now refuses a result that claims an attempt and names no registered attempt row, for each of the five statuses, in all three probe families) and the verifier probe for a change to the binding member `requirement_id` alone against the captured inputs. Before the marks were removed, a run of the unchanged suite reported exactly these 16 as unexpected passes.
- Still kept as known limits (6, listed in `suites/fix2-probes/KNOWN_LIMITS.md`): the three clock-domain order probes (a service stamp of a reconciliation or closeout is not compared with the attempt start, for the verifier reconciliation row and the two ODES rows); the two runtime probes (after a failure that follows the effect commit the executor reports status `unknown`, retry not eligible, with observed state `applied`; the probe expects `unknown`); and the verifier binding probe for `effective_max_effects` (checked against the proposal export and destination ledger only, not against the captured inputs).
- The four retained-example cases of the ODES test suite that fail with Replay installed (ODES issue #131) are not part of this suite and are unchanged.

### Update 2026-10-19 (Programme 2 re-pin r10, runtime fix)

Five further pins moved (refreeze entries RF-37 to RF-41, profile `process/security-runtime-f5b-20261016-r10.json`, suite generation `p2`): runtime c4a05883 to 6b16962d, Replay 2a7963b1 to 6a6a4774, evidence pack 80e24650 to fd030615, ODES 4bf12128 to 2893d935 and exchange bf314f38 to fdc2a410. The runtime change repairs the export of a grant that changes at commit time (`effective_grant_changed_at_commit`); Replay, the evidence pack, ODES and the exchange compatibility profile `security-runtime-p2-20261018` then name the new runtime revision, so the producer tuple moves together (a bundle of the previous P2 tuple is no longer accepted as P2 by those four). The control plane 2bac7875, the action manifest ff549082, the constitutional authority 0124adcd and the verifier dc09a98f are unchanged from r9. The controller profile named by `V1_PROFILE` in `v1-validation.yml` is r10 (a unit test asserts it equals the profile `select_profile` picks).

- No qualification-controller run has been made at the r10 pins; every earlier verdict is historical and is not transferred. The FIXED-UNVERIFIED rows stay FIXED-UNVERIFIED.
- The declared-limit lists and measured counts of the suites that use the commit-time-race export were taken at the r9 pins and are not re-measured by this change.
- The README table of the hardening probe suite `suites/fix2-probes` still names the r9 heads; the suite was not re-measured at the r10 pins and carries no controller verdict.
- Adversarial batch 1 (`process/adversarial/components.json`) still names the r9 revisions of the runtime, Replay, evidence pack and ODES as a record of the 2026-10-19 run; batch 1 was not re-run for r10.

### Update 2026-10-19 (representative reference run at the Programme 2 profile)

At the compatibility profile `security-runtime-p2-20261018` the representative reference run is a declared known limit. `tools/reference_release.py` sets `GAX_RUNTIME_COMPATIBILITY_PROFILE` from the hub lock. The exchange (fdc2a410) function `_workflow_options` in `gax_ref_runtime.py` requires a trusted `runtime_authority_profile` under every `security-runtime-*` profile, and `AcceptedGaxRecipientAdapter.handle` calls `run_exchange` without one. This is the exchange's own documented limitation (`experiments/governed_message_transport/profile.md`, F5b).

- The representative step of `reference-release` and the authority batch (and its aggregate) of the `full-candidate-release` matrix are expected to fail at this profile. No component change is made.
- The earlier profile `merged-producers-v1` is not a substitute: its older pins make the retained bundle reconstruction partial.
- The result is not claimed as a pass. It is listed here, separately from the passing suites.
- Decision: owner, 19 October 2026 (declare as known limit, no component change).
- No qualification-controller run has been made for this entry, and the pins are unchanged from r10.


### Update 2026-10-20 (Programme 2 r10 tuple: measured state)

This entry records what was measured at the r10 pins (profile `process/security-runtime-f5b-20261016-r10.json`: runtime 6b16962d, Replay 6a6a4774, evidence pack fd030615, ODES 2893d935, exchange fdc2a410, control plane 2bac7875, action manifest ff549082, constitutional authority 0124adcd, verifier dc09a98f). It adds to the entries above and does not rewrite them. Where the entry of 2026-10-19 (r10, runtime fix) says that the declared-limit lists and the counts of the suites that use the commit-time-race export were taken at r9 and not re-measured, the measurements below replace those counts for the suites named here. No status of an earlier finding is changed by this entry, and no assertion, fixture or expected value was changed to obtain a count.

**Declared set.** The declared set in force is derived from the committed twin (`tools/declared_limits.py`): 76 entries (75 tests and 1 requirement), `declared_set_sha256` `1ba741d7e71a7c3fb49c6bbc995b41503608e5232cb1cee93c0684563e19c087`. A direct measurement of 19 October used a set of 72 entries (hash `bde46adc...`); the four entries added since are the four SCN-C04 copy cases of `suites/v1-scenarios` (amendments 85 to 88).

| Where the entries live | Entries | Collected by the controller |
|---|---:|---|
| control plane tests | 11 | yes |
| Replay tests | 5 | yes |
| ODES tests | 4 | yes |
| `suites/v1-probes` (control plane probes) | 6 | yes |
| `suites/v1-scenarios` (SCN-C04 copy cases) | 4 | yes |
| `suites/wiki-derived` | 35 | no |
| `suites/fix2-probes` | 6 | no |
| `process/adversarial/tests` | 4 | no |
| requirement `ADD-AUTH-RA` | 1 | not a test |

**Controller run at the r10 pins.** Run 39349033320 (label `g2-r10`, harness revision cbe7ba03; results retained under `results/v1-validation/v1-2026-10-16-a/g2-r10-39349033320`). The job table has 33 PASS, 3 FAIL, 2 NOT RUN and 0 INCONCLUSIVE jobs. Freeze check PASS. The requirement matrix for the selected V1 scope reports 39 mandatory rows PASS and 0 others; the full-catalog block reports 56 PASS, 0 FAIL, 35 INCONCLUSIVE, 20 NOT RUN and 20 NOT APPLICABLE rows, and the verdict rule applied to the rows that were mandatory before the D15 scope reduction reports INCOMPLETE. None of the 36 moved rows is counted as PASS. None of this is a release decision.

- The 3 FAIL jobs are exactly the declared failing tests: ODES on Python 3.11 and 3.12 (3071 test cases, 4 failures, 1 skip; the four declared ODES retained-example tests) and the scenarios job (1093 test cases, 4 failures; the four declared SCN-C04 copy cases). No undeclared test failed in either job.
- The declared control plane tests (11) ended as asserted on both Python versions. The 5 declared Replay tests and the 6 declared control plane probes are recorded as skipped (strict expected failures).
- The 2 NOT RUN jobs are the optional components that have no tests at the pinned commit.
- Other job counts (test cases, failures, errors, skipped): control plane 952/0/0/1, runtime 512/0/0/0, Replay 1183/0/0/17, evidence pack 366/0/0/0, exchange 311/0/0/0, action manifest 245/0/0/0, BitRep 81/0/0/0, Index 121/0/0/0, constitutional authority 491/0/0/0, optional research component 13/0/0/0, hub tests 653/0/0/0, qualification tooling 416/0/0/1, native-f5b suite 36/0/0/0, matched-refund rerun 20/0/0/0 (20 of 20 trials PASS).
- One skipped test in the qualification tooling job (416 test cases, 1 skipped) was not declared by exact test id and reason before the run. It changes no row and no verdict. It is reported openly here and is not declared after the result. At the next candidate it is either declared beforehand or its cause is removed.

**First attempt and artifact split.** The first dispatch (run 39345693648) completed all jobs and then stopped at the aggregate step, which refused a control record found in a nested location (`v1v-harness-hub/hub-tests/result.json`). The rule that refuses nested control records had been added earlier and the workflow had not been adapted to it. That attempt is retained as an aborted attempt (RO-8) and no result of it is used. A second dispatch (run 39348963707) was made before the fix was merged and was cancelled. The fix (#182) uploads the qualification tooling tests and the hub tests as two separate artifacts (`v1v-qual-tooling` and `v1v-hub-tests`) instead of one nested artifact; it changes no test, selector or verdict rule. The retained run above is the next dispatch with the same label, made after #182 was merged, and its results were retained by #183.

**Suites outside the controller, measured by direct runs on 19 and 20 October at the same pins** (no test was changed, selected or deselected; these runs carry no controller verdict):

- `suites/wiki-derived`: 290 collected, 285 passed, 5 failed, 0 errors, 0 skipped. The split is W-I 64 collected (63 passed, 1 failed), W-X 217 collected (213 passed, 4 failed) and 9 infrastructure tests (9 passed). Of the 35 declared tests of this suite, 34 end as asserted and 1 fails because its component has changed since the limit was declared. Each failing test failed again on a single re-run and in a second environment; each is reported as FAILING (NON-GATING) under amendments 78 and 79, and none was classified as a major defect. The five are tests whose expectations lag an intended change of their component; one of them is the test withdrawn by amendment 65.
- `suites/fix2-probes`: 213 collected, 207 passed, 6 expected failures, 0 failed; the six are the six declared entries. The README of the suite still names the r9 heads.
- `process/adversarial/tests`: 136 collected, 132 passed, 4 expected failures, 0 failed, run with `ADV_ALLOW_REVISION_DRIFT=1` because `process/adversarial/components.json` still names the r9 revisions of the runtime, Replay, evidence pack and ODES. The four expected failures are the four declared entries.
- `suites/v1-scenarios`: the controller job above (1093 cases, 4 failures, all declared) is the recorded result. A direct local run on 19 October, made before declared entries existed for this suite, recorded 23 failures in the same 1093 cases (the four SCN-C04 cases plus 19 others, some reported as harness exceptions of that local environment). The difference is the nineteen test expectations updated for intended component behaviour (qualification pull request 176) and the declaration of the four SCN-C04 cases (amendments 85 to 88).

The bounded comparison of the same candidate is recorded in `reports/comparison-g2-r10-2026-10-20.md`, with its retained output in `results/comparisons/g2-r10-20261020/`. It uses a different harness, does not change any count above and is not a release decision.

**Still open.** The refreeze log status text and the inventory pair are not changed by this entry. The representative reference run remains a declared known limit (entry of 2026-10-19). The README of `suites/fix2-probes` and `process/adversarial/components.json` still name r9 revisions and are not edited here.


### Update 2026-10-21 (candidate g5-r10: registry d25afe60 and attestation 981036c3)

This entry adds to the entries above and does not rewrite them. The registry (`the_index`) and the attestation component (`bitrep`) were moved to the revisions the hub component lock lists (RF-42 to RF-44; the registry at `d25afe601454d60c561a4726e31c31d1ec40d99b` pins attestation `981036c315856c71207984797b0c4e48d3b3921d`). The seven components of the r10 profile keep their revisions.

**Runs.** g4-r10 (run 39522462997) stopped at the install step of the scenarios job (INCONCLUSIVE, no scenario result). g4-r10b (run 39524389031) ran the scenarios; 14 SCN-C03 cases were INCONCLUSIVE on the harness exception `BitRep checkout must be clean and pinned`, because the registry at 704f55ea accepts only the previous attestation revision. Neither run qualified the two revisions. **g5-r10** (run 39531760987, results retained at qualification merge commit `0e4a29ac`) is the controller run at the tuple above: 40 of 40 workflow jobs succeeded; 33 PASS, 3 FAIL, 0 INCONCLUSIVE, 2 NOT RUN; freeze PASS; selected verdict PASS.

- The 3 FAIL jobs are the declared failing tests: ODES on Python 3.11 and 3.12 (3071 cases, 4 failures, 1 skip) and the scenarios job (1093 cases, 3 failures: the three SCN-C04 copy cases of amendments 85 to 87). No undeclared test failed.
- The 14 SCN-C03 cases that were inconclusive in g4-r10b ran and passed.
- `one_evidence_record_linked_five_times` (SCN-C04) passed, as declared before the run by amendments 104 and 108. The SCN-C04 row stays INCONCLUSIVE and is not mandatory. Amendment 109 withdraws the declaration of amendment 88 for this case by the owner's decision, citing the run; the declared set is 75 entries (74 tests and 1 requirement), `declared_set_sha256` `51bb22945a8a5e525f689fc9a2053f150127aab0cc32b95fd26442eeba69e5d7`. The run itself used the set of 76 entries (`1ba741d7...`).
- The registry change that counts a repeated link of one evidence record once is the behaviour behind the pass. The other three copy cases still show copied evidence raising supporting weight (F-19, D14).

Scope: bounded synthetic profile only. This is not independent certification and not production readiness; operational trust, publication and production stay on HOLD. The hub component lock lists the registry at a revision that this run did not probe until the lock is updated.


### Update 2026-10-21 (candidate g6-r10: constitutional authority d4462697, profile r11)

This entry adds to the entries above and does not rewrite them. An independent static review of the lock revision of the institutional-governance repository (0124adcd) reported two false accepts of the synthetic authority-lineage validator, a non-authorizing evidence profile that nothing else in the stack consumes: a delegation under a parent edge that forbids redelegation (or whose remaining depth does not decrease below its parent's) was accepted, and a bundle with more than one origin for one authority was accepted. Both were reproduced locally and fixed in institutional-governance #60 (merge commit `d4462697197d6eb4e76bbfc3d712c8c1dab27884`), with negative cases and valid controls; the lineage fixture, schema and ten qualification cases are unchanged. Neither was a declared known limit.

The refreeze entry RF-45 moves the constitutional authority to that commit and the profile `process/security-runtime-f5b-20261016-r11.json` is r10 with only that pin changed. The controller run g5-r10 (entry of 2026-10-21 above) was made at the earlier authority revision and is not transferred. The candidate g6-r10 is the run at the new tuple; its expected state is recorded before the run in the pre-registration (amendment 112). No run of g6-r10 had been made when this entry was written.

Scope: bounded synthetic profile only. This is not independent certification and not production readiness; operational trust, publication and production stay on HOLD.


### Update 2026-10-21 (verdict machinery: independent review findings E-1 to E-11)

This entry adds to the entries above and does not rewrite them. An independent review of the controller (`tools/v1_validation.py` and `.github/workflows/v1-validation.yml`) found that the machinery which decides the selected-V1 verdict could report PASS when it should not. The declared known limits, the requirement rows and the declared scope are unchanged; the verdict rule is stricter in the following ways, each with a test in `tests/test_e*.py`.

- E-1: an expected job that is FAIL, INCONCLUSIVE or missing stops the verdict being PASS unless every failed case of its JUnit report is a declared known limit of that component (FAIL gives FAIL, the others INCOMPLETE). A NOT RUN job blocks unless the plan marks its component optional. Jobs behind a non-mandatory job row (qualification tooling, matched-refund rerun) remain scope-reduced. The blocking jobs are named in `verdict_note` and `blocking_jobs`.
- E-2: a freeze-verification record without `components_expected`, or whose `components` differ from it, or with a failed check under a PASS status, is a freeze problem (INCOMPLETE). The retained g6-r10 record has 0 components and no `components_expected`; re-aggregated by this controller its verdict is INCOMPLETE, not PASS. The retained results are not edited; the earlier PASS is the result of the controller that produced it.
- E-3: the freeze profile checks run both ways: the profile lists components, every pinned subject component appears at the manifest-plus-overlay revision, and a `constitutional_authority` section equals the pinned authority.
- E-4: `check-workflow-pins` (run by the plan job) fails when a pinned-repository sha literal of the workflow differs from the pin in force.
- E-8: the native-f5b job record is FAIL when the audit or repetition step failed, and SC-NATIVE-F5B is PASS only for a record whose `audit_outcome` is `success`.
- E-10: a `tests` row with zero executed cases is INCONCLUSIVE; rows without selectors or with a selector minimum below 1 are refused.
- E-5, E-7, E-7b, E-11: a refreeze status note that says the entry is reverted, withdrawn or not applied is not applied; duplicate entry ids and a missing `validation_id` are refused; a failed pinned-sibling install stays visible in the job record; a job that passed only on its retry is reported (`flaky_or_setup_jobs`, not blocking); job and freeze records are checked against the validation id, the workflow run and the plan pins.

Not changed here: E-6, E-12 and E-13 of the review remain open and are not claimed as fixed. Scope: bounded synthetic profile only. This is not independent certification and not production readiness; operational trust, publication and production stay on HOLD.


### Update 2026-10-21 (candidate g7-r10: refreeze to the scan 3 and 4 mains, profile r12)

This entry adds to the entries above and does not rewrite them. After the independent scans 3 and 4 the fixes were merged in the authority, the control plane, the action manifest, the runtime, the exchange, Replay, the evidence pack, ODES and the registry. The refreeze entries RF-46 to RF-54 move those pins in the log and in the controller workflow, and the profile `process/security-runtime-f5b-20261016-r12.json` lists the seven component pins and the constitutional authority at the new revisions. The attestation pin (981036c3) and the hub identity of the freeze manifest are unchanged; the hub component lock moves after the run, not in this change. The controller runs g2-r10 to g6-r10 were made at earlier revisions and are not transferred to the new tuple.

- The status of RF-45 is restated. The run g6-r10 probed it, but its PASS is the result of the controller that produced it and reads INCOMPLETE when the retained record is re-aggregated by the hardened controller (E-2), so the entry is not marked qualified. No run at the hardened controller has qualified any pin yet; the candidate g7-r10 is the first run that can.
- The contract matrix reference for `execution-attempt-lifecycle` 0.1.0-draft moves to ODES 59ca4c79. The content hashes were compared first: the lifecycle files at ODES dc5cf19d and the vendored copies of the control plane, the runtime and Replay are identical, so the move records the content the producers vendor. Measured locally against the built components: both lifecycle boundaries conform.
- The control plane reason registry has 163 codes; the probe expectation moves from 158 to 163 with it. The ODES label list of codes added in 0.2 has 42 entries (163 less 121).
- Expected change of status, declared before the run (amendment 116): the three declared SCN-C04 copy cases of amendments 85 to 87 passed in a local execution against the registry at RF-54, which weights a claim by distinct normalised source. If they pass in the controller they are unexpected passes of declared strict expected failures and the row reads FAIL until the owner withdraws the declarations by an amendment that cites the run. The copy-evidence limit F-19 is not described as closed by this entry; the controller run decides.
- Local executions of the component suites and the native cases at the new pins are measurements made outside the controller. They are not results of any controller run and do not qualify any pin.

Scope: bounded synthetic profile only. This is not independent certification and not production readiness; operational trust, publication and production stay on HOLD.
