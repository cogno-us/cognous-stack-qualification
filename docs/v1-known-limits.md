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
- **F-19, copied evidence in the Index (SCN-C04, ER-02-4b, D14).** The Index counts copied evidence as extra supporting weight because it has no independence mechanism, so copies can raise support. This is also stated in `BITREP_LINK_ATTESTATION.md`.

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

Two gap fixes closed the 12 full-phase chain cases that did not pass at the r5 pins. The pins moved again (refreeze entries RF-23 and RF-24, profile `process/security-runtime-f5b-20261016-r6.json`, suite generation `p2`): ODES 0663d5a2 to 81979784 (ODES #97 adds the P2 compatibility tuple, so the exporter accepts the Programme 2 producers) and exchange 914db78d to 7172dde6 (exchange #37 adds the compatibility profile `security-runtime-p2-20261018`; the exchange head was d8d44c1 after the bytecode cleanup #36 and before #37). The control plane 3cd17ead, runtime 11de097c, Replay 46e8bd7c, evidence pack 4fbbd344, the action manifest and the constitutional authority are unchanged from r5. The `p2` branch of the chain suite's ODES generation helper now selects the P2 tuple; no probe assertion was changed.

- No qualification-controller run has been made at the r6 pins; every earlier verdict is historical and is not transferred. The FIXED-UNVERIFIED rows stay FIXED-UNVERIFIED.
- The full-phase cases of the security-runtime chain suite were run locally and read-only at the `p2` generation with the r6 pins (result recorded in the pull request that introduced r6). This is not a controller run and carries no verdict.
- The exchange profile `security-runtime-p4-20261017` still refuses the Programme 2 producers (identity mismatch), as intended: the compatibility names are exact per generation.
