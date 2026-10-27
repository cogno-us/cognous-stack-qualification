# V07 findings and disposition

Bounded adversarial assessment of the V06 baseline at the frozen pins (Registry `943ab183`, Control Plane V02 `1bee3696`, Runtime V05 `4199a6c7`, Qualification V06 `ae122218`; older Control Plane fixture `e66e5f16`). Synthetic local SQLite only. **Assessor = the builder identity that wrote the Runtime V05 guard and the V06 harness; this is not an independent-party review.** Ed25519 is SECURITY-HELD and not assessed. Threat model and the predeclared inventory: `THREAT_MODEL.md`, `INVENTORY.md` (committed at `b1c6644e`, before any attack was run; Addendum A was added after the first wave and before its two cases ran).

## Execution record (local; budget 50)
| Run | Cases | Result |
|---|---|---|
| 1 (commit `591ee470`) | 37 | 37 harness PASS: 32 HELD, 1 BREACH, 4 CHARACTERIZED (`local-runs/run1-first-wave`) |
| 2 | A11, I05 | A11 HELD; I05 recorded HELD but its stderr showed a missing test dependency (`cryptography`), i.e. an environment error, not a security result — **I05 run 2 is withdrawn** (`local-runs/run2-addendum`, kept) |
| 3 | I05 | HELD with a real outcome (`local-runs/run3-i05-rerun`) |
| **Total** | **40 executions** | no case skipped; no failed attack discarded |

Effective result per case: 39 distinct cases — HELD 34, BREACH 1 (A08), CHARACTERIZED 4 (A09, D01, D08, I01), INCONCLUSIVE 0. The CI run re-executes all 39 at the frozen pins (not counted against the local budget).

## Findings
### F-01 HIGH (Architect classification, PR #234 review; assessor originally MEDIUM) — Registry policy narrowing is not verified by the Runtime at effect time (case A08, D08)
- **Component/commit:** Runtime V05 `4199a6c7`, `engine/registry_selection_authority.py::check_effect`; contract r08-v2 §7.4 item 3.
- **Invariant:** "The Registry policy can reduce caller permissions but cannot expand them" (V06 acceptance 5; mission P0 "unauthorized policy expansion").
- **Preconditions:** a claim supplier that can call the trusted-host `provision_claim` with a claim the Control Plane would not issue: all identity members correct (record triple, activation_ref, epoch, snapshot), `effective_policy_digest` set to the digest of a WIDER policy, commitment recomputed; the executor is then given that wider policy.
- **Reproduction:** `suites/security-v07/test_adversarial.py::test_a08_...` (Registry payload allows only `act-list`; claim and executor policy carry `act-list, act-extra`; envelope action `act-extra`).
- **Expected vs observed:** expected refusal; observed `executed`, one effect committed (`local-runs/run1-first-wave/results.json`, case A08). The guard compares the claim-carried digest only with the digest of the executor's own policy; it never compares the executor policy with the activated record's payload, which it holds (`selection_activation_v1.record_json`).
- **Demonstrated, and NOT demonstrated (both retained):** a Runtime policy-narrowing bypass under a compromised or mis-composed claim supplier **WAS demonstrated** (A08, reproduced a second time in the closeout, `local-runs/run4-closeout`). Compromise of the normal Control Plane issuance workflow **was NOT demonstrated**: I04 showed the Control Plane refusing an unapproved binding. An ordinary external caller cannot exploit this without the claim-supplier capability. No claim issued by the Control Plane workflow was carried through the Runtime guard (coverage gap A).
- **Classification:** HIGH for independent Runtime policy enforcement, per the Architect review (comment 6438515324). It is not downgraded because the frozen contract permits the behaviour; contract conformance explains the finding, it does not remove the missing control. The assessor's original MEDIUM reasoning is retained below, superseded.
- **Original assessor reasoning (superseded):** contract §7.4 item 3 states in terms that `effective_policy_digest` "is not compared to durable state ... narrowing itself is enforced by the evaluator on the policy the executor was given", so the behaviour conforms to the frozen contract; the Control Plane refuses an unapproved binding at issuance (case I04, HELD); and an honest flow cannot widen (executor policy digest must equal the issuer-composed `min(record, caller)` digest, so its five sets are within the record). Exploitation needs a claim supplier outside the honest Control Plane.
- **Escalation condition (original; now resolved by the Architect as HIGH):** if the Architect treats the Runtime as an enforcement point for Registry narrowing independent of the claim supplier (the V06 acceptance wording could be read that way), this is HIGH and the disposition becomes BLOCK.
- **Consequence:** an effect outside the active Registry policy can commit when claim issuance is compromised or mis-composed; the Registry restriction is only as strong as the issuer.
- **Owner / remediation:** `cogno-us/cognous-execution-runtime` (guard), dependent on a contract amendment to r08-v2 §7.4 (effective-policy narrowing semantics, item 3): refuse when any of the five executor policy sets is not a subset of the activated record's payload sets (local rows only; no new authority source).

## Characterized behaviour (not findings)
- **A09 (LOW / hardening):** `max_amount` and target prefixes are outside the F1AB payload and remain caller-owned; with the five Registry sets unchanged, an amount above the default cap executed. Contractual, but a "narrowed" selection does not bound them.
- **D08 (LOW / QUALIFICATION GAP):** `execution_claims_v1.claim_json` is not authenticated at lock time; editing it in place (no commitment recompute) changed the effective digest and an effect committed. Requires write access to the database file, which also permits direct effect rows; the selection tables, by contrast, are hash-chained and anchored. Same condition as F-01 but via storage.
- **D01 (disclosed limit):** a consistent rollback of the database AND the host-held anchor resurrected a withdrawn selection (effect committed). ADR 3.6 discloses this as undetectable; the anchor custodian is operator-gated. Not a new vulnerability; stays an unqualified boundary.
- **I01 (coverage gap C):** the Runtime wrapper `worker21-authority-effect.yml` still calls the reusable workflow at `1c1755ff…`, older than the V06-qualified revision. A change belongs to the Runtime repository.

## Coverage gaps / unqualified boundaries
- Coverage gap A: only one Control Plane issuance probe (I04) exists; no claim issued by the Control Plane workflow was carried through the Runtime guard (fixtures use different scopes).
- Coverage gap B: the in-process stage-hook race of V06 was supplemented by one OS-process race (C01: 50 effects then 110 refusals, every effect's guard head below the withdrawal sequence) and a two-process double-claim (C02); one timing-dependent run each, not exhaustive.
- Coverage gap D: I03 refused because its hand-built binding was invalid, so it does not isolate pydantic 2.11 behaviour (weak evidence). I05 shows Control Plane V02 *issuance* works and still refuses a tampered binding under pydantic 2.11.9; Runtime-side verification of successor claims under 2.11.9 remains untested.
- Not assessed: Ed25519 soundness, anchor custody, Registry→Control Plane publication, production deployment, independent human review.

## Case results (HELD = attack failed)
A01 A02 A03 A04 A05 A06 A07 A10 A11 HELD; **A08 BREACH (F-01)**; A09 CHARACTERIZED; C01–C07 HELD (C01 overlapped the race: executed 50 / denied 110); D02–D07 HELD; D01, D08 CHARACTERIZED; T01–T08 HELD; I02 I03 I04 I05 HELD; I01 CHARACTERIZED.

## Disposition
**BLOCKED.** One HIGH finding (F-01, Runtime narrowing bypass under a compromised or mis-composed claim supplier; normal Control Plane issuance compromise not demonstrated). No CRITICAL finding. The earlier "PASS with one MEDIUM finding" disposition is superseded by the Architect's HIGH classification. The V07 gate never accepts a HIGH finding, so the adversarial CI job is expected to report the A08 BREACH as unaccepted until the Runtime is remediated and requalified; that is the truthful state, not a harness fault. Results are reproducible at the pins. Standing holds unchanged: V08–V09 not authorized; Ed25519 SECURITY-HELD; Tier 1 not started; Release / Publication / Production HOLD.

## Addendum B: CI run at `9151ae02` failed on a harness defect (not a component finding)

The first CI run of this suite (head `9151ae02`) failed. The cause was in the harness, not in the components. The subprocess probes (C02, C05, C06) were launched with a `PYTHONPATH` that omitted the pinned Control Plane `src/`. On my workstation that package was importable from the environment, which hid the defect. In the hash-locked CI environment it was not, so the probe processes exited 1 before reaching their stage.

Observed in CI, from the gate annotations of that run:
- C02: `IndexError` (the probe printed no result line), recorded FAILED.
- C05 and C06: recorded `BREACH`. These were false results. A crash probe that never reached its stage was being read as a durability failure.

Repairs (harness only, no component touched):
- The probe `PYTHONPATH` now includes the pinned Control Plane `src/`, after any caller-chosen older copy.
- C05 and C06 now record INCONCLUSIVE, never BREACH, when the crash probe does not exit 9 at the stage. A harness fault can no longer be reported as a breach.
- The gate now emits `::error` annotations for failed cases and for a missing results file, so a CI failure is readable without downloading job logs.

Re-check in a clean hash-locked venv (Python 3.13 locally; CI uses 3.12) with the pydantic 2.11.9 venv for I03 and I05: I01, I02, I03 and I05 passed with unchanged verdicts, and after the repair C02, C05 and C06 are all HELD (exit code 9 observed at both crash stages).

Execution accounting: 40 local executions before CI, 4 environment checks (I01, I02, I03, I05), and 3 post-repair checks (C02, C05, C06) plus 3 pre-repair reproductions of the CI failure (C02, C05, C06), which gives the 50-execution ceiling. The earlier local verdicts for C02, C05 and C06 (HELD) were obtained with the probe path working and stand. The pre-repair CI verdicts are retained here as invalid harness results, not as findings.

## Addendum C: reconciliation of the CI discrepancy (closeout, Architect review of `9151ae02`)

**The three CI BREACH verdicts were A08, C05 and C06.** The review's other counts reconcile: 39 executed = 31 HELD + 4 CHARACTERIZED + 3 BREACH + 1 without verdict (C02 FAILED, no verdict recorded).

| Case | CI at `9151ae02` / `aaa45adc` | Local (retained) | Class | Cause |
|---|---|---|---|---|
| A08 | BREACH | BREACH (run1; closeout rerun BREACH) | **Demonstrated security violation** (F-01) | see F-01 |
| C05 | BREACH (`exit_code` 1, not 9) | HELD (exit 9, claim `issued`, retry executed, 1 effect) | **Harness/environment defect** | crash probe died on import before reaching its stage |
| C06 | BREACH (`exit_code` 1, not 9) | HELD (exit 9, 1 effect committed, replay denied) | **Harness/environment defect** | same |
| C02 | FAILED, `IndexError` | HELD (one executed, one denied, 1 effect) | **Harness/environment defect** | same: probes printed no result line |

**Local/CI discrepancy.** Subprocess probes were launched with `PYTHONPATH` = Runtime tests + Runtime only. The Runtime test module they import calls `pytest.importorskip("agent_control_plane.local_authority_effect")`. On the assessor's workstation `agent_control_plane` was importable from the Python environment, so the probes worked. In the hash-locked CI environment it is not installed (the pinned Control Plane is only on `sys.path` of the pytest process, by `conftest.py`), so `importorskip` raised `Skipped` inside the probe, which exited 1 with no result line. This was reproduced in a clean hash-locked venv before any repair (C02 IndexError; C05 and C06 BREACH with exit 1), which is the evidence for the cause. C05 and C06 were wrongly read as durability breaches because the verdict logic treated "exit code is not 9" as BREACH.

**Preserved results.** The CI verdicts above are kept as recorded; they were not reclassified to HELD. The raw artifact of run 40482037092 (head `9151ae02`) cannot be downloaded through this environment's proxy, so the per-case CI outcomes come from the gate annotations of run 40483061382 (head `aaa45adc`, which carries the same harness defect): C06 and C05 BREACH not accepted, harness FAILED 1, C02 IndexError. The first CI run is https://github.com/cogno-us/cognous-stack-qualification/actions/runs/40482037092. The local-run raw files are unchanged.

**Repairs (harness only; no component source, pin, expected outcome, acceptance criterion or CI check changed or weakened).**
1. Probe `PYTHONPATH` now includes the pinned Control Plane `src/` (commit `d66e3a1b`). With this, CI at `d66e3a1b` ran all 39 cases with C02, C05 and C06 HELD.
2. C05 and C06 record INCONCLUSIVE, not BREACH, when the crash probe does not exit 9 (commit `d66e3a1b`).
3. C02 (this closeout): captures each subprocess's exit status, stdout tail and stderr tail into the evidence; if a racing process printed no result line the verdict is INCONCLUSIVE, never an IndexError; the original criterion (exactly one effect for the one claim, `effects == 1`) is unchanged. Corrected C02 evidence: `local-runs/run4-closeout/results.json` (both exit 0; one `executed`, one `denied`; counts 1/1/1/1). The INCONCLUSIVE branch itself was not exercised by a deliberate fault (not run; budget).
4. The gate emits annotations for failed cases (commit `aaa45adc`).

**Closeout executions (budget 8): 2.** C02 corrected: HELD. A08 reproducibility: BREACH again (status `executed`, one effect, registry payload allowed only `act-list`, claim and executor carried `act-extra`). 0 FAIL. Local executions in total: 50 (original budget, fully used) plus 2 of the 8 additional ones authorized for this closeout.

## Unqualified boundaries (final)
Ed25519 soundness (SECURITY-HELD); anchor custody; Registry-to-Control-Plane publication; production deployment; independent human review (assessor is the builder identity); no Control-Plane-issued claim was carried through the Runtime guard; Runtime-side verification of successor claims under pydantic 2.11.9; the `claim_json` lock-time authentication gap (D08); the F1AB caller-owned dimensions (A09).
