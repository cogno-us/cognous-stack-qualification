# V1 known limits

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
