# V1 validation report: v1-2026-10-16-a

**This report does not declare a release.** No release, tag, announcement or message was made. Production remains NOT ESTABLISHED. V1 is an alpha candidate that was modified during validation.

## Verdicts, side by side

| | Reduced scope (D15) | Full catalog (before D15) |
|---|---|---|
| Selected-V1 verdict | **PASS** | **FAIL** |
| Basis | Verdict rule over the 39 mandatory rows that passed in final-linux-1 | The same rule over the 75 rows that were mandatory before D15 |
| Mandatory rows | 39 PASS, 0 FAIL, 0 INCONCLUSIVE, 0 NOT RUN | 39 PASS, 2 FAIL, 29 INCONCLUSIVE, 5 NOT RUN |
| All 131 catalog rows (real statuses) | 54 PASS, 3 FAIL, 34 INCONCLUSIVE, 20 NOT RUN, 20 NOT APPLICABLE | identical (no row status changed) |

**The reduced-scope PASS exists only because 36 mandatory rows were moved out of the claim after the result was seen.** The verdict rule was not changed. The full-catalog verdict is the honest measure of how much of the original claim passed: 39 of 75 mandatory rows (52 percent).

Authoritative run: Actions run [39032930011](https://github.com/cogno-us/cognous-stack-qualification/actions/runs/39032930011) (label final-linux-1, Linux only). Retained original evidence: `results/v1-validation/v1-2026-10-16-a/final-linux-1-39032930011/` (unaltered). Offline re-evaluation with the D15 requirements file, no new execution: `results/v1-validation/v1-2026-10-16-a/final-linux-1-39032930011-reduced-scope/`. Re-aggregating the original requirements file reproduced the retained matrix and summary exactly (apart from job-label prefixes), so the re-evaluation differs from the original only through D15.

Job-level result of the same run: 35 PASS, 1 FAIL (the scenarios job: 1084 cases, 4 failures, all SCN-C04), 2 NOT RUN (PRP and TFA, removed from the stack under D8). The scenarios job failure is still real. The reduced-scope verdict is computed over requirement rows, not jobs; the failing cases belong to a scope-reduced row.

## Scope reduction (D15)

Decision D15 (2026-10-17, after the final-linux-1 result; disclosed, not pre-registered), on the owner's direction: if remediation would take too long, reduce scope coverage so that everything claimed passes, and move failed and inconclusive rows to known limitations to be addressed after the ODES contract re-engineering.

- The V1 claim is narrowed to the 39 rows that passed. Each of the 36 other mandatory rows is `mandatory: false` with a `scope_reduction` record (decision D15, final status, category). No status, selector, adequacy declaration or result was changed or deleted.
- Moved rows by category: 1 failed, fix merged outside the pinned tuple (ER-03-1); 1 design limit (SCN-C04); 5 not run and unimplemented (SCN-C05, C15, C19, C20, C21); 29 inconclusive by declared partial coverage. Full list with reasons: [docs/v1-known-limits.md](../docs/v1-known-limits.md).
- ADD-AUTH-RA (FAIL, D10) was already non-mandatory and is not in the 36.
- Harness change, reporting only: `summary.json` and `summary.md` now carry a "Full-catalog status" block over all rows and a "Scope reduction" block listing every moved row. The verdict function is untouched. New tests: `tests/test_v1_scope_reduction.py`.
- Follow-up: ODES contract re-engineering (`docs/engineering/ODES-INTERCOMPONENT-CONTRACTS.md` in `cogno-us/open-decision-evidence-standard`, in progress by another worker). The moved rows are to be revisited after it.

## What was frozen and what changed

The original freeze ([freeze-manifest.json](../process/v1-validation/v1-2026-10-16-a/freeze-manifest.json)) fixed hub `8517818f`, qualification closeout `af9f5843`, runtime `e20f92e1`. It was never edited. Ten owner-authorised re-freeze steps ([refreeze-log.json](../process/v1-validation/v1-2026-10-16-a/refreeze-log.json)) moved component pins to merged remediation commits:

| Step | Component | From | To |
|---|---|---|---|
| RF-1 | the_index | d5e45d27 | d17b8ac2 |
| RF-2 | moltbot_safe (runtime) | e20f92e1 | 4a83b175 |
| RF-3 | replay_bundle | 79ba16d4 | 0cfe7a63 |
| RF-4 | odes | eb83220c | 4e6d1169 |
| RF-5 | governance_evidence_pack | 893aca8d | 683246e0 |
| RF-6 | gax_imx_transport | 8be6c6b8 | da953782 |
| RF-7 | replay_bundle | 0cfe7a63 | def0ee0f |
| RF-8 | odes | 4e6d1169 | 5675f1b9 |
| RF-9 | governance_evidence_pack | 683246e0 | 505a3590 |
| RF-10 | gax_imx_transport | da953782 | ec6ba5bd |

The re-freeze was stopped by the owner on 2026-10-17. The constitutional authority pin stays at `fb3d9793` by owner decision, so the F-15 fix (merged at cbc39e79) is not in the validated tuple. final-linux-1 is the single full run at the pins in force. Results at earlier pins are retained as history and are not relabelled.

## What the 39 passing rows cover

Evidence is from executed tests and probes at the pinned commits on Linux, Python 3.12 (3.11 also run for components). Counts are matched executed cases.

- **BitRep signing (5 rows):** invalid signatures and substituted issuers cannot be stored; malformed, tampered and replayed submissions rejected; rotation and revocation semantics; demonstration proofs cannot yield assurance; real signing round trips (ER-01-1 to ER-01-5).
- **The Index evidence store (6 rows):** public API cannot bypass accepted-object invariants; forged attestations rejected; supersession preserves history; status reproducible; duplicated evidence does not raise the independence score (ER-02-4b checks the independence count only, not `supporting_weight`; the supporting-weight inflation is F-19 and SCN-C04); detector calibration controls (ER-02-1, 02-2, 02-3, 02-4a, 02-4b, CTL-02). ER-02-2, ER-02-4a and ER-02-4b each rest on a single targeted probe case.
- **Constitutional governance (1 row):** independence mechanisms for review required (ER-03-2, one case).
- **Action manifest (3 rows):** unambiguous action resolution; unknown actions and version mismatches never default to permission; round-trip fixtures preserve obligations (ER-04-1 to 04-3).
- **Control plane (6 rows):** payload or adapter substitution fails; revoked or expired grants cannot authorise later effects; unknown delivery cannot trigger blind retry; exports carry attempt and outcome references; destination state asserted; residual check-to-commit races declared and tested (ER-05-1 to 05-6).
- **Runtime (4 rows):** supported tests execute against the real API; allowed operations change the destination and denied ones do not; path traversal, symlink, adapter bypass and credential misuse tests; stubs report not executed (ER-06-1 to 06-4).
- **Replay bundle (4 rows):** generated runs import without silent loss; invalid references and unsupported versions fail clearly; redacted and signed export semantics; incomplete delivery cannot become verified completion (ER-07-1 to 07-4).
- **Evidence pack (3 rows):** pack reconciles with underlying records; missing observations stay visible; approved review status cannot be manufactured from schema validity (ER-08-1 to 08-3).
- **ODES (3 rows):** mapped examples validate; negative vectors distinguish structural failure, verifier rejection and local reliance; effect and attempt extensions labelled proposed and separately versioned (ER-09-1 to 09-3).
- **Governed exchange transport (1 row):** generation fence, effect ownership, repaired chain (ER-IMX, 109 cases).
- **Shared requirement (1 row):** revocation, observation time, clock uncertainty, freshness and status propagation (SR-1, 68 cases).

## What is not claimed

- No release, no production claim, no performance claim (D5).
- Nothing about the 36 moved rows: scenario-catalog acceptance (only named synthetic assertions and partial coverage exist), the unimplemented scenarios, conventional-control comparison, provenance beyond a lexical screen, migration notes, tier delay limits, independence of copied evidence.
- Windows and macOS (Linux only, D2). Results from the earlier all-platform runs are retained and not claimed.
- Extension families (D4), governed memory (D6), PRP and TFA (D8), the deferred runtime-authority addendum (ADD-AUTH-RA, D10), the refund-intent profile with route A (D12).
- The 40 native runtime regressions from PR #29 were not re-executed from the overlay; the runtime's own suite and the 36-case native F5b suite pass.
- The Drive addenda folder could not be read; the matrix covers the attached recommendations document and repository matrices. The counterparty's material was read-only and not reconciled.

## Known limitations

See [docs/v1-known-limits.md](../docs/v1-known-limits.md). In summary: the 36 moved rows (grouped by category there), plus F-16, F-18 and the earlier deferrals. Statuses are unchanged. None of these is a pass.

## Zero-harm gate (D5)

D5 makes zero unauthorized effects and zero excess duplicate effects the only hard gate. Checked in the retained final-linux-1 scenario evidence (1105 evidence files, 1791 governed-arm gate records):

- **Governed arm: 0 unauthorized effects, 0 excess duplicate effects** in every gate record, with no network and no live effects (`live_effects: 0`, `paid_model_calls: 0`).
- The only non-zero governed-arm values are the five deliberately seeded defects in the SCN-C23 effect-oracle calibration test. The oracle detected all five (`missed: []`) and its clean control reported 0 and 0.
- The conventional-control arm (a plain allow-list check, report-only) shows 25 unauthorized and 15 excess duplicate effects across the SCN-C22 cases, which is the comparison the scenario exists to measure.
- The 4 failing cases (SCN-C04) concern evidence weighting, not effects.

**Gate result: PASS.** This is a check of the retained JSON by script, not a separate execution.

## Failures found and fixed

Register: [failure-register.json](../process/v1-validation/v1-2026-10-16-a/failure-register.json). VERIFIED means confirmed in the final-linux-1 JUnit or matrix. Most verifications are at test level: the matched scenario row stays INCONCLUSIVE because of declared partial coverage (D13/D15), so the defect is verified, not the row.

| ID | Finding | Status |
|---|---|---|
| F-01 | Index accepts unverifiable attestations | VERIFIED (ER-02-2 PASS; SCN-C03 87/87) |
| F-02 | Duplicated evidence counted as independent | REMEDIATION-PR (partly fixed; SCN-C04 FAIL) |
| F-03 | ODES export profiles not labelled proposed | VERIFIED (ER-09-3 PASS) |
| F-04 | Tenant id not compared on route A | VERIFIED (SCN-D02 58/58) |
| F-05 | One unauthorized hold blocks valid export | VERIFIED (SCN-D06 8/8) |
| F-06 | Planted-defect cases undetected by evaluators | VERIFIED (SCN-D08 32/32) |
| F-07 | Fails on macOS and Windows | WONTFIX-OWNER-DECISION (D2) |
| F-08 | Post-commit observation failure misreported | VERIFIED (SCN-C06 7/7) |
| F-09 | Narrowed local grant does not stop direct commit | VERIFIED (SCN-C11 55/55) |
| F-10 | Unknown export members silently dropped | VERIFIED (SCN-C12 57/57) |
| F-11 | Changed ODES bundle version not flagged | VERIFIED (SCN-C12 57/57) |
| F-12 | Seeded-defect misses in evaluators | VERIFIED (SCN-C23 12/12, all 5 seeds detected) |
| F-13 | Substituted replay bundle accepted | VERIFIED (ADD-ASW12 231 cases, 0 failures) |
| F-14 | Tenant substitution via ASW I01 | VERIFIED (SCN-D02, ASW I-series 27/27) |
| F-15 | Tier table declares no delay limit | REMEDIATION-PR (ER-03-1 FAIL; fix outside the pinned tuple) |
| F-16 | Six runtime-authority behaviours missing | WONTFIX-OWNER-DECISION (D10; ADD-AUTH-RA FAIL) |
| F-17 | Generation fence fails every commit | VERIFIED (ADD-MOLT-VERIFY PASS) |
| F-18 | Refund-intent profile cannot combine with route A | WONTFIX-OWNER-DECISION (D12; fails closed, documented) |
| F-19 | Copied evidence inflates supporting weight | WONTFIX-OWNER-DECISION (D14; SCN-C04 FAIL) |
| F-20 | Replay rejects unknown result with executed terminal | VERIFIED (SCN-C06 7/7) |
| F-21 | Replay requires a start row that reconciled attempts lack | VERIFIED (SCN-C09, D05, D06) |
| F-22 | Replay journal-order rule races | VERIFIED (SCN-D06 8/8) |
| F-23 | Two added skips made rows INCONCLUSIVE (test-only) | VERIFIED (ER-07-1, ER-07-2 PASS, 0 skips) |

17 VERIFIED, 3 failing and kept (F-02, F-15, F-19), 3 accepted or unchanged (F-07, F-16, F-18). Entries are never deleted.

## Process caveats

- **The scope was reduced after the results were seen.** D15 is disclosed, not pre-registered. The owner saw final-linux-1 before choosing it.
- The verdict rules are unchanged. The reduced-scope PASS follows only from moving rows out of the mandatory set.
- The V1 candidate was modified during validation: ten re-freeze steps changed component pins after the first run found defects. The verdict applies to the re-frozen tuple, not the original freeze.
- The constitutional authority pin was held back, so a merged fix for ER-03-1 is not in what was validated.
- V1 is alpha. Decisions D10 to D15 were made after results were known; D9 was decided after batch 1 and before batch 2. Earlier decisions: [preregistration.json](../process/v1-validation/v1-2026-10-16-a/preregistration.json).
- Several passing rows rest on few cases (ER-02-2, ER-02-4a, ER-02-4b, ER-03-2 on one case each). The adequacy declarations were fixed before the run.
- The scenarios job reports FAIL at job level because of the SCN-C04 cases.

## Next step

ODES contract re-engineering, then revisit the moved rows and the F-02, F-15 and F-19 limits at a new freeze. Until then V1 as validated is the 39 passing rows. This report does not declare a release.
