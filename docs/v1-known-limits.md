# V1 known limits

## D15: V1 claim narrowed to the passing rows

**V1 as validated = the 39 passing rows; the rest are known limitations pending ODES re-engineering.**

Decision D15 was made on 2026-10-17 after the final-linux-1 result (Actions run 39032930011). It is disclosed, not pre-registered: the scope was reduced after the results were seen. On the owner's direction, the V1 mandatory claim is narrowed to the 39 requirement rows that PASSED in final-linux-1. The 36 mandatory rows that did not pass (2 FAIL, 29 INCONCLUSIVE, 5 NOT RUN) are moved out of the mandatory claim and listed below as known limitations, to be addressed after the ODES contract re-engineering (`docs/engineering/ODES-INTERCOMPONENT-CONTRACTS.md` in `cogno-us/open-decision-evidence-standard`, in progress and not yet merged when this was written).

This is a scope reduction, not a relabelling. No requirement's status, selector, adequacy declaration or result was changed or deleted. Each moved row carries `mandatory: false` and a `scope_reduction` record (decision, final status, category) in `requirements.json`, and keeps its real status. The verdict rule is unchanged. The harness reports a full-catalog status block over all rows, so a moved row is never counted as PASS. The reduced-scope verdict is PASS; the same rule over the pre-reduction mandatory rows is FAIL. Neither is a release decision.

The 36 moved rows (re-evaluation: `results/v1-validation/v1-2026-10-16-a/final-linux-1-39032930011-reduced-scope/`):

### Failed: fix merged outside the pinned tuple (F-15, D11) (1 rows)

- **ER-03-1** (FAIL): probes-authority: no delay limit linked to any consequence tier (F-15); fix merged in institutional-governance (cbc39e79) but outside the pinned tuple (fb3d9793).

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

- **F-15, tier delay limit (ER-03-1, D11).** The tier table declares no delay limit. A fix is open as cogno-us/cognous-institutional-governance#51, with limit values pending owner confirmation. Until it is confirmed and re-pinned, treat this as open.

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

The runtime's atomic local executor (route B) returns status `unknown` with a recovery observation after a post-commit failure. Replay at the validated pin rejects that export on its public import path. The fix for F-20 to F-22 covered route C only. Qualification scenario SCN-C06 route B passes because it never exports into Replay, so that pass does not show Replay can consume route B. This is outside the reduced V1 claim. Update 2026-10-17: fixed in Replay (cognous-replay-bundle #37, main 287a2b6b) and covered by ODES contract fixtures (open-decision-evidence-standard #52). It is not re-pinned, so the validated pin still rejects route B, and the SCN-C06 route-B round-trip scenario will be added with the end-of-alpha pin refresh. Status FIXED-UNVERIFIED.

## Evidence pack cannot re-validate route-B bundles (F-25, found 2026-10-17)

Replay now imports the real route-B post-commit exports (F-24) and retains the recovery report as `executor_recovery_report`. The evidence pack at its pinned revision does not map that record type back when it re-validates a retained Replay bundle, so it rejects all three captured route-B bundles. Outside the reduced V1 claim. Status OPEN; proposed for the decoupling plan's P3 phase.
