# V07 requalification: F-01 remediation verification

Builder identity: the same builder that wrote the F-01 remediation and the original V07 harness. **This is not an independent-party attestation.** Historical results are preserved unchanged: `../FINDINGS.md`, `../local-runs/` (A08 BREACH at Runtime `4199a6c7`, Registry `943ab183`), `../historical_findings.json`. Plan, new cases and regression selection were committed before any execution at the patched pins (`../INVENTORY.md`, Addendum B, commit `3d71e7ee`).

## Pins (verified before use)
| Component | Pin | Verification |
|---|---|---|
| Registry (with r08-v2 Amendment 3) | `a1169a05afb917862f4a0f5865e278f4168ed171` | on `main`; contains PR #45 head `153a8f0f`; descends from `943ab183`; diff from it is docs plus one pin test, no code |
| Runtime (with F-01 remediation) | `ac247dafbce3aacde37695575d457cf958b22560` | on `main`; contains PR #148 head `fa1eec61`; diff from `4199a6c7` is exactly `engine/registry_selection_authority.py`, `engine/local_authority_effect.py`, `engine/atomic_local_control_plane_executor.py` and `tests/test_f01_policy_containment.py`; `safe_executor.py` untouched |
| Control Plane V02 | `1bee3696ee6cd8037d142cdbcdb6020e052b0480` | unchanged |
| Older Control Plane fixture | `e66e5f163c5d5c112ff345a2f332b4c3893ee183` | unchanged |
| Qualification V06 baseline | `ae12221831bc39beea6dbf0ae7fda726baeecf1f` | ancestor of this branch (checked by the suite) |

The suite fails, never skips, when a checkout is missing or off its pin. The original V06 workflow still runs at the V05 pins (passed on this branch's CI), which keeps the historical baseline.

## What changed in the harness (no component source touched)
Pins of the V07 suite and workflow; A12 to A18 added; accepted-breach list emptied (A08 is **not** allowlisted); `historical_findings.json` holds the F-01 history and is not read by the gate; the gate additionally requires A08 HELD with typed `policy_identity_mismatch` and zero effects, attempts and receipts, and requires A12 to A18 to be present; the V06 conftest accepts an optional `V06_PIN_OVERRIDES` (unset in the V06 workflow, no assertion touched) so the unchanged V06 cases run at the patched pins; the V07 workflow runs the Runtime's V05 effect-guard module and F-01 module, and the V06 suite at the patched pins, failing on any skip or failure.

## Local executions (budget 50; 36 used)
| Run | Scope | Count | Result |
|---|---|---|---|
| `local-runs/run5-f01-cases` | A08 (original attack, unchanged body) + A12 to A16 (one F1a set widened each) + A17 (strictly narrower) + A18 (equal) | 8 | 8 PASS / 0 FAIL / 0 SKIP; verdicts 8 HELD |
| `local-runs/run6-v05-regression.junit.xml` | V05 module at the patched Runtime: S-01, S-04, B-03, B-04, C-01, E-01, L-03, X-01 | 8 | 8 PASS |
| `local-runs/run7-v06-at-patched-pins` | V06 unchanged: A01, P04, S01, B01, B02, R01, S03, G02, G04, L01, L03, D04 | 12 | 12 PASS / 0 SKIP |
| `local-runs/run8-v07-concurrency-corruption-replay` | V07: C01, C02, C05, C06, C07, D02, T03, I04 | 8 | 8 PASS; verdicts 8 HELD |
No local rerun was needed. No failed attack was discarded.

## A08: historical versus patched
| | Runtime `4199a6c7` (historical, `run1`, `run4`) | Runtime `ac247daf` (patched, `run5`) |
|---|---|---|
| Verdict | **BREACH** | **HELD** |
| Status | `executed` | `denied`, `attempted: false` |
| Typed refusal | none | `policy_identity_mismatch`, cause `policy_not_subset:allowed_actions`, class REFUSE |
| Effects / attempts / receipts / budget | 1 / 1 / 1 / 1 | 0 / 0 / 0 / 0 |
| Fallback authorization | n/a | none (refused; no caller-policy fallback) |
The attack is the same: a claim with correct identity members, a recomputed commitment and the digest of a wider policy; an executor given that policy; a record that allows only `act-list`. The gate was run on the historical results and rejects them (A08 BREACH, A08 not HELD, cases A12 to A18 missing); on the patched results it passes.

## Five-set containment (A12 to A16, independent of the Runtime's own tests)
Each case widens exactly one set with the claim supplier carrying the matching digest and a recomputed commitment: `allowed_actions` HELD, `allowed_adapters` HELD, `allowed_units` HELD, `allowed_institutions` HELD, `allowed_authority_domains` HELD. Every one: denied, typed `policy_identity_mismatch`, zero effects, attempts, receipts and budget. Over-enforcement check: A17 (strict subset in all five sets) and A18 (equal) each executed with one effect and one receipt.

## Regressions
Directly affected capabilities, locally (selected) and in CI (whole modules):
- Valid narrowed and equal policy: A17, A18, V06 A01 and P04. Stale generation: V05 S-04, V06 S01. Withdrawal and revocation: V05 S-01, V06 B01, B02, V07 C07. Racing authority writer: V05 C-01, V06 R01, V07 C01 (below), C02. Substituted or invalid binding: V05 B-03, B-04, V06 S03. Corrupt authenticated store: V05 X-01, V06 G02, V07 D02. Evidence-write failure: V05 E-01, V06 G04. Required-scope legacy bypass refused: V05 L-03, V06 L01. Permitted legacy: V06 L03. Control Plane successor profile: V06 D04, V07 I04.
- Authority transition ordering, V07 C01 at the patched pins: 51 effects committed then 109 refusals; first refusal at stream index 51; the highest guard log head recorded on an effect (3) is below the withdrawal sequence (4). C02: two processes, one claim, one `executed`, one `denied`, one effect. C05 and C06: probes exit 9 at the stage; no effect before commit, no duplicate after commit.

## GitHub CI at head `63430e51` (all 14 checks success)
Run https://github.com/cogno-us/cognous-stack-qualification/actions/runs/40490458320. From the annotations of the adversarial job (logs and artifacts are not downloadable through this environment's proxy):
- V07 suite at the patched pins: 46 executed, 46 PASS, 0 FAIL, 0 SKIP, 0 BLOCKED; verdicts 42 HELD, 4 CHARACTERIZED (A09, D01, D08, I01), **0 BREACH**.
- Runtime V05 effect-guard module plus the Runtime F-01 module at the patched Runtime: 65 tests, 0 failures, 0 errors, 0 skipped.
- Unchanged V06 suite re-pointed at the patched Registry and Runtime: 33 executed, 33 PASS, 0 FAIL, 0 SKIP.
- The original V06 workflow (V05 pins) and the Worker21 successor and legacy lanes also passed.
The CI result for the final docs-only head is reported in the PR closeout comment.

## History preserved
C05 and C06 BREACH verdicts in the first CI run were a harness defect (probe could not import `agent_control_plane`); the record and repair are in `../FINDINGS.md`, Addendum B and C, and are unchanged. C02 evidence (exit status, stdout and stderr captured; INCONCLUSIVE on missing output) is unchanged and HELD again here.

## Residual risks and unqualified boundaries
- Same-builder requalification: no independent third-party attestation.
- The guard trusts the executor to report the five sets of the policy it evaluates (the same trust as the digest it already supplied). A compromised executor process is outside the guard.
- A09 (LOW): `max_amount` and target prefixes remain caller-owned and outside the F1AB payload; still CHARACTERIZED.
- D08 (LOW, qualification gap): stored `claim_json` is not authenticated at lock time; direct database write access; still CHARACTERIZED in CI. Its patched-pins observation was not re-examined locally.
- D01: a consistent rollback of database plus anchor remains undetectable by design (ADR 3.6).
- I01: the Runtime wrapper `worker21-authority-effect.yml` still calls the reusable workflow at `1c1755ff`; a Runtime-repository change.
- Coverage gap A: no claim issued by the Control Plane workflow was carried through the Runtime guard.
- Not assessed: Ed25519 soundness (SECURITY-HELD), anchor custody, Registry-to-Control-Plane publication, production deployment. Release, Publication and Production remain on HOLD; V08 to V09 are not authorized.

## Disposition
All eight PASS conditions are met: A08 reproduced and HELD at the patched Runtime; all five F1a dimensions refuse widening; narrowed and equal policies execute; no V05 or V06 regression demonstrated; no new HIGH or CRITICAL finding; required CI passes; history preserved; residual limits disclosed. **PASS (same-builder), with the residual limits above.** F-01 is closed only to the extent of this evidence.
