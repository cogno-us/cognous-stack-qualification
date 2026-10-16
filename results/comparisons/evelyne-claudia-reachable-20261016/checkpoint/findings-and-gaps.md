# Phase 0 findings and gaps

## Findings

1. The frozen F5b candidate profile (`process/security-runtime-f5b-20261016.json`,
   SHA-256 `a710b8c0eb4a6dba1f0770a957212b32a34fb8042e1d3726ef24a2b1db249ddd`) is
   `selected=false`, non-authorizing, and pins all seven components at the revisions
   named by the coordinator. It is reproducible via `tools/run_security_runtime.py`.
2. D01 (`valid`), D03 (`revoked`), and C07 (`race`) are already implemented as
   parameterized cases in `suites/security-runtime/test_security_runtime_chain.py`
   via the `produce()` fixture. Each case produces the four native artifacts
   (`proposal.json`, `executor.json`, `reconstruction.json`,
   `destination-observation.json`) plus pytest `junit.xml` and `report.json` from
   the runner.
3. Correction and commitment boundaries are separately named for each scenario in
   `boundary-map.md`. The C07 characterization confirms the existing C0 residual-race
   limit; it is not qualified distributed atomicity and will be reported as such.
4. The observer is an in-process SQLite readback (`EffectiveGrantDestination.observe`).
   This is a local synthetic oracle; the bounded-comparison process already requires
   that limit to be declared, and `observer-spec.md` declares it.
5. Evelyne-Claudia's five receipt categories are already covered natively with two
   explicit exceptions:
   - 1.c "Revocation receipt with issuing authority" — the frozen reference uses an
     in-memory status mutation. Native refusal reason `grant_revoked` carries the
     effect; the issuer signature does not exist in this profile. This is a declared
     F5b limitation ("Missing signature verification remains missing"), not an
     adapter we can fairly add.
   - 5.d "REACHABLE verdict" — Cognous should not produce these. They are REACHABLE's
     to assign. The package records their absence as intentional per "correspondence
     permits comparison; it does not transfer proof".
6. No required-receipt gap is covered neither by native producers nor by the
   available observer. Phase 1 does not need new instrumentation; it only
   re-serializes native data into category-aligned JSON files behind declared trust
   labels.

## Open questions for the owner's go/no-go

- Q1. Proceed to Phases 2–4 with D01 (`valid`), D03 (`revoked`), and C07 (`race`)
  only, as named by Evelyne-Claudia and already parameterized by the suite?
- Q2. Report 1.c (issuer-side revocation receipt) and 5.d (REACHABLE verdict) as
  honest limitations in `README_FOR_EVELYNE_CLAUDIA.md` and
  `CROSSWALK_REACHABLE.md`, rather than fabricating adapters?
- Q3. Package layout: use Evelyne-Claudia's five categories as the primary table of
  contents in `README_FOR_EVELYNE_CLAUDIA.md`, with the return-evidence-format
  layout (manifest/fixture/transport/observation/native/destination/test-results/
  evidence) as the on-disk structure under each category?
- Q4. D03 variant selection: run only `revoked` as the primary D03 variant for this
  round (what Evelyne-Claudia specifically asked about — authority remains current
  at consequential commitment)? "Approval withdrawal", "policy-version change", and
  "evidence expiry" would be separate runs if ever requested.
- Q5. Diagnostic repetitions: the bounded process asks for two unchanged-condition
  diagnostic repetitions per included variant. We will run each of D01/D03/C07
  twice. Trial IDs will be distinct; no reliability estimate will be claimed.

## Explicit non-questions

- The package will not advance `selected`, release, or production fields.
- The package will not be sent anywhere. "Ready to share" is distinct from "sent";
  transmission requires separate explicit instruction identifying recipient and
  channel.
- The package will not import Jerry's bundle or any ChatGPT output.
- The package will not claim interoperability acceptance or any REACHABLE verdict.

## Phase 0 verdict

Phase 0 is COMPLETE with no un-coverable required-receipt gap. The owner can
authorize Phases 1-4 or request narrowing before execution.
