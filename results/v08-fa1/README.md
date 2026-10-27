# V08 F-A1 qualification: local run record (candidate, non-authorizing)

Standing holds: V08: IMPLEMENTATION ACTIVE; QUALIFICATION NOT YET PASSED. Independent external Tier 1: NOT STARTED. V09: NOT AUTHORIZED. Ed25519: SECURITY-HELD.
Release: HOLD. Publication: HOLD. Production: HOLD. Nothing here claims clearance, certification or production readiness.

This directory is NEW and append-only. The historical V08 evidence (`results/v08-tier1/**`, PR #235, including the F-A1 BREACH evidence and
`test_au7_operation_substitution_bypasses_policy_containment_posthoc`) is not edited, not allow-listed and not reinterpreted.

## Exact heads under test
| Component | Head | Change |
|---|---|---|
| Registry | `1a4de32605519c505142b1ba3a57fa5b259b0b2c` | Amendment 4 adopted (contract and 30-case plan) |
| Control Plane | `0fd44d03d69aa49f8022472aedd0f8187a8e8ea9` | cognous-control-plane PR #86 (export from the persisted decision), unmerged |
| Runtime | `ad1805e22b1dee4f3201a228f85e1c4599bbebe5` | cognous-execution-runtime PR #149 (installer + guard + integration), unmerged |
| Harness | the commit recorded in `runs/run-001.json` (`f187dada…`) | `suites/tier1-v08-fa1/` |

## Local execution accounting (budget: 30 including reruns and parametrized runs)
- **30 counted executions, 0 reruns.** `ledger.jsonl` has 30 lines; `runs/run-001.json` is the only counted run.
- Verdicts: **HELD 28, CHARACTERIZED 1 (FA1-12, the documented propagation window), INCONCLUSIVE 1 (FA1-13)**. 29 cases passed, 1 failed.
- **FA1-13 is INCONCLUSIVE and stays so locally.** Its recorded facts are correct (`pending_blocked`, rows `[active]`, committed epoch 1, intent present, new effect HELD
  `pin_transition_pending`, recovery `complete`, then REFUSE `pin_status:revoked`), but the oracle's "no completion was logged while held" check matched the *earlier install's*
  `complete` log record (harness defect, not a product defect). It was the 30th execution, so it was NOT rerun locally. The oracle was corrected in a later commit and the
  corrected case runs in GitHub CI at the exact heads. The local record is not edited and INCONCLUSIVE is not read as PASS.
- Not counted, disclosed: seven throwaway exploratory scripts (not test cases, no verdicts recorded) checked fixture mechanics before the counted run (typed outcomes, a
  second-decision feasibility check, the two-user setup, the kill helper, anchor forgery construction). The Runtime-side builder tests (`tests/test_authorization_pin_*.py`,
  `tests/host_pin/**`) are component tests, not qualification executions.
- Environment: Linux, root, python 3.13.17, pydantic 2.14.1, real `useradd`/`setpriv`. CI uses the hash-locked python 3.12 / pydantic 2.12 set.

## Findings by theme
**E. F-A1, historical versus patched (FA1-01, 03, 04).** With a validly activated second operation `op-other`, a supplier rewrites `binding.operation` and every commitment the
claim verifies (`forged_claim_verifies: true`). The SAME claim in the SAME store: against a destination WITHOUT the pin option it **executes** (1 effect, 1 receipt: the historical breach
is reproduced); against the pin-required destination it is **REFUSED** `policy_identity_mismatch[pin_binding_mismatch:operation]` with 0 effects, 0 receipts, claim still `issued`. The Registry
guard was never asked about `op-other` (`check_effect_calls: []`). Recomputing every state commitment after altering `selection_epoch` changes nothing (`pin_binding_mismatch:selection_epoch`).

**F. Real OS isolation (FA1-05, FA1-06a).** Two real non-root identities (installer uid 30033, executor uid 30034). All 7 install/replace attempts and all 28 modify attempts by the
executor identity were denied by the OS (SQLite reports a read-only database), store/anchor/log/fence bytes and modes unchanged, no journal or sibling file created. The same
identity could read the pin through the guard's reader and take a shared flock on a read-only descriptor. FA1-06(b) (in-process): unexpected arguments raise `TypeError`, frozen
attributes raise `AttributeError`, a claim carrying a path member is rejected. In-process attribute freezing is defence in depth, not an isolation boundary.

**G. Revocation, pending intent and recovery (FA1-09 to 22).**
- FA1-10: a real Control Plane revocation exports `terminal/revoked`; the committed terminal row refuses the effect (`pin_status:revoked`); the Control Plane also refuses new claims.
- FA1-11: with three effects in flight the revocation stayed `pending_blocked` (rows `[active]`, committed epoch 1); the parked effect committed with `pin_epoch` 1 and the others were HELD;
  the terminal row then committed at epoch 2 (> every receipt epoch) and a later claim was refused.
- FA1-12: the propagation window is **CHARACTERIZED**: an effect admitted before the installer acts passes under the old pin (documented limit, Amendment 4 section 12).
- FA1-13/14: a real process holding the shared fence keeps the transition pending with no unfenced commit; covered-decision claims are HELD every time; three unrelated decisions keep executing;
  completion followed the holder's exit in 4 ms, with no reliance on flock fairness. (FA1-14 unrelated decisions are synthetic by construction.)
- FA1-16/17/18: restoring an older store with the anchor intact, an anchor ahead of the store, a different head digest and an invalid intent relation HOLD (`pin_anchor_inconsistent`; for the
  invalid-intent variant the covered decision reports `pin_transition_pending` from the lock-free barrier and an unrelated decision `pin_anchor_inconsistent`); a missing anchor HOLDs
  every decision (`pin_anchor_unavailable`) and the installer refuses to write; restoring the anchor restores admission.
- FA1-19 to 22 (real SIGKILL): A (before the intent) leaves no barrier and the restarted installer re-derives the transition; B/D/F/H (intent durable) HOLD the covered decision for the whole
  interval while an unrelated decision executes and the restarted installer completes it; C (hot journal) HOLDs `pin_store_unreadable` until recovery rolls the junk back (0 junk rows) with no
  fabricated commit; E (row committed, anchor pending) HOLDs the decision (`pin_transition_pending`, stricter than the section 7 table's "accept") and reconcile completes the anchor; a
  chain-valid row that does not match the intent makes reconcile refuse and every decision HOLD (`pin_anchor_inconsistent`). The append-only triggers had to be dropped by the harness (as the
  store owner) to simulate that corruption.

**F-01 and regressions (FA1-23 to 27).** With the pin and the claim in agreement and the activated record narrower, the pin step passes and F-01 containment refuses
`policy_not_subset:allowed_actions` and `:allowed_units`; a narrower executor policy executes; an injected evidence failure commits nothing and releases the fence; a claim without a binding is
refused `pin_required_binding_absent`.

## Deviations from the plan text (stated, not hidden)
- FA1-07: the plan expects `pin_absent` for "no row". Under the adopted contract (6.1) an absent per-decision fence is a HOLD `pin_fence_unavailable`; `pin_absent` is reached only when a fence exists without a row. Both were exercised.
- FA1-08: the pin is a real export with `grant_revision` replaced (synthetic input). Forging the claim instead (FA1-28 style) is refused earlier by the existing approval-state validation, so that route cannot reach the pin.
- FA1-28: the seeded claim was refused by the existing approval-state validation (`authoritative approval state invalid`), not by the pin; the honest claim still executed.
- FA1-09 uses a synthetic terminal assessment (`superseded`); FA1-10/12/13/19 to 22 use the real Control Plane revocation export.
- FA1-22: see above (HOLD in state E rather than "accept; the terminal row refuses").

## Retained qualification gaps (not closed by this run)
- External anchor custody cannot be demonstrated by code in this environment; a CONSISTENT restore of the pin store and the anchor together is undetectable (CHARACTERIZED by analysis, Amendment 4 section 7).
- Anti-rollback is therefore unsupported until an operator demonstrates anchor custody outside the pin store's restore domain.
- The two-identity cases show what OS permissions do on this host; a production deployment's identities, mounts and mode bits are not demonstrated here.
- `reconcile()` completes a recorded terminal intent without re-contacting the Control Plane (can only remove authority).
- Profile rotation leaves the old pin `active`; the existing Registry selection guard (not the pin) refuses the stale activation.
- Independent external Tier 1 has not started; this suite was designed and run by the Lead Builder session of the same organization.

## CI
GitHub CI at the exact heads is carried by `.github/workflows/tier1-v08-fa1.yml` (runs the full 30 cases as root, then `suites/tier1-v08-fa1/gate.py`). CI references are appended below as they complete.

## CI note 1 (appended, head e5770b1b, GitHub Actions run 40537445066)

The first CI run at e5770b1b reported 28 of 30 cases passing and failed only FA1-05 and FA1-06a (real two-identity OS cases; verdict NONE, `pins.sqlite3` never created). Cause: an ordinary harness/CI defect, not a product result. The installer child script was launched as the throwaway installer user from the runner workspace under the runner's home directory, which that user cannot traverse, so no store was written and no isolation claim was evaluated. Both cases remain unresolved (INCONCLUSIVE) until a CI run at the repaired harness shows them executing. Repair: the child is staged next to the pinned components under /opt (`V08_FA1_CHILD`). No product code, pinned head, allowlist or acceptance criterion changed. The 30 local executions are not rerun.

## CI note 2 (appended): CI evidence for the first successful run, distinct from the local record above

The local record above is unchanged and is NOT rewritten as 30 PASS: 30 counted local executions, 28 HELD, 1 CHARACTERIZED (FA1-12), 1 INCONCLUSIVE (FA1-13, an oracle defect). `results.json` and `runs/run-001.json` remain that local record (harness commit f187dada, pins registry 1a4de326 / control plane 0fd44d03 / runtime ad1805e2).

CI evidence is separate and was produced by corrected harness code, not by the local run:

- Run 40537952077 (https://github.com/cogno-us/cognous-stack-qualification/actions/runs/40537952077), Qualification PR #236 head 1a9b6a93, pins registry 1a4de326 / control plane 0fd44d03 / runtime ad1805e2: the F-A1 job executed all 30 cases as root with real throwaway identities and the gate passed (it fails on any failure, skip, BREACH, INCONCLUSIVE, BLOCKED, or executed != 30). Evidence artifact `v08-fa1-evidence` (junit and per-case JSON) is attached to that run; GitHub artifacts expire, so the run URL and this note are the retained pointer.
- Run 40537445066 (head e5770b1b) is the original failed CI gate for this suite: FA1-05 and FA1-06a failed because the OS-identity child script was under the runner home, which the throwaway users could not traverse (harness defect, repaired in 1a9b6a93; no product code, pin or acceptance criterion changed). It is retained as the original failed gate.
- The corrected FA1-13 oracle (match `action=="terminal"`, `outcome=="complete"`, same decision id) passed in CI; locally FA1-13 stays INCONCLUSIVE because the local budget was spent.

## Lineage and pin update (appended)

- Successor to PR #236 (stacked on #235). This branch is based on `main` and carries only the F-A1 suite, its results and its workflow. The historical V08 assessment (#235, head `7b72de9ac7e4898c0f9bdad3e9b337775cc9c543`: the F-A1 BREACH (`test_au7`) and its original failed gate) is preserved there, unmerged and unedited; it is referenced here by immutable commit, not copied.
- The one historical helper this suite reuses (`suites/tier1-v08/authority/_wf.py` at 7b72de9) is vendored byte-for-byte as `suites/tier1-v08-fa1/_historical/_wf.py` (sha256 a36dc8f81f4789cc795abf43f8f510acc68eac5acfee07806c7a0e237c60d2a7, enforced by the suite's environment gate in place of the previous ancestor check; it fails, never skips, on mismatch).
- Pins advanced for the final heads: control plane `d66ae07fa240510efdcc11ed4b3e1189dcefc822` (merge commit of #86; its tree equals that of the former pin 0fd44d03, an ancestor); runtime `3873a61b5dd1ca2f8102d355888e59b5cd5a5456` (#149 head: code tree identical to the former pin ad1805e2 plus the docs-only F3 record). Registry stays `1a4de326`. No moving branch references.
- CI at these pins is the revalidation. The 30 local executions are not rerun, no gate was weakened, and F-A1 is not allowlisted.
