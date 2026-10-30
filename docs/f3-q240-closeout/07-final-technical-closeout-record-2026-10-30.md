# 07 F3 final technical closeout record (OCS-F3-Q240-FINAL-CLOSURE), 2026-10-30

Append-only successor note to the Q1-Q8 package (#243). It does not rewrite earlier documents or evidence. Lifecycle language: **technical qualification by the lead builder session and its subordinate agents is complete as far as the evidence allows; no independent acceptance, no competent certification, no merge into main-branch custody has occurred.**

## 1. Frozen executable subject
Control Plane `739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69` (tree `1e7a7555eb3a956fcd2db21d3eb944169d0f7783`, src `d248bde4…`). Live heads at writing: Registry `6b96a9a6`, Control Plane `b19c47dd` (later; not the subject), hub `b7d81311`. Execution pin: Registry r08-v8 `a40fe755` (and `943ab18` for one named successor case).

## 2. Governing contract and successor interpretation
Frozen contract and oracle: Registry docs 02 section 4 and 03 (execute AND pin-export refuse with `authorization_binding_changed` and a durable `EffectTimeRefusal`). Successor interpretation OCS-F3A-DEV-PE-1-INTERPRETATION/1.0: doc 06 and record 11 (builder-prepared, unsigned, human adoption pending). Constitutional baseline `1c2e920`; `dcdbe3b` prospective only; draft adoption instrument inactive.

## 3. Original F3-A FAIL (permanently preserved)
DEV-PE-1: 23 failed assertions (22 pin-export members plus A06 sub-case) under the frozen literal oracle. Original evidence: `results/third-party/cp-739efe7-f3-independent-20261029/`. Not rewritten.

## 4. Successor F3-A technical assessment
Readjudication (PR #242, producer = lead builder session): technical assessment under both readings, not independent qualification. Unmerged.

## 5. F3-B
Scoped technical PASS (original record); not reopened.

## 6. Q1-Q8 dispositions
| Q | Status | Evidence | Scope established | Remaining | Criterion met? | Certification still required? |
|---|---|---|---|---|---|---|
| Q1 | OPEN | #242 `2246a61c`; read-only cross-check at PR head | Original bytes (tree `9004b517` = commit `44ce26eb`) verified at PR head | merge + fresh-checkout `sha256sum -c` at merge commit; blocked by authorization control | No | n/a |
| Q2 | OPEN, contract AMBIGUOUS | #244 `d76b20f3` | MECHANISM EVIDENCE ESTABLISHED (graft, execute only). NATURAL END-TO-END ISOLATION NOT ESTABLISHED (structurally unavailable) | Architect ruling on whether this satisfies the acceptance boundary (analysis: frozen text does not require it; records 12-14 place it in the boundary) | Undetermined | Yes |
| Q3 | OPEN, contract AMBIGUOUS | #244 | host_profile_digest: F5 masked-host execute isolation (one workflow, execute leg). effective_profile_digest: decomposed only | same; pin-export legs and other workflows not covered | Undetermined | Yes |
| Q4 | OPEN pending custody | #245 `1321e2ee` | M06 kill reproduced: persisted-content detection by the harness. NOT live authority-domain comparison sensitivity (Q2 limit preserved) | #245 merge + custody check | Technically yes; closure gated on custody | Yes |
| Q5 | OPEN pending custody | #245 | `provision_local_execution_claim` 14/14 on Python 3.11 and 3.12, governed D-06 journal path, real spy | non-journal branch, raising provision, live-side drift untested; #245 custody | Technically yes; closure gated on custody | Yes |
| Q6 | OPEN pending custody; technical criterion met on evidence | #245, #246 `b206de18`, #247 `7898f319` | Gap A: linkage half NOT APPLICABLE (contract), stage-lie half executed 4/4 on 3.11 and 3.12, original 13 pass / 1 skip preserved. Gap B: passes only as a modified copy; original test still skips (hard-coded path). Gap C: original file 95/95 at its own pin `943ab18` | custody of #245-#247; Architect confirmation of the Q6-A applicability determination | Technically yes; closure gated on custody and confirmation | Yes |
| Q7 | Recorded; independence NOT ESTABLISHED | this record | See sections 9 and 10 | Architect/operator designation; competent certifier | No | Yes |
| Q8 | Separate governance matter | #243 `05` | Baseline `1c2e920` preserved; draft inactive | Architect adoption decision | n/a | n/a |

## 7. Evidence custody verification
Pre-merge read-only cross-check of #242 passed (47 OK, 0 failed; manifest, protocol hash `04f4f950…`, scope, tree identity). **Post-merge verification not performed: no PR is merged.** No evidence is claimed to be in main-branch custody. #243-#247 CI green and clean at heads recorded on issue #240; #244-#247 carry same-session read-only review addenda (stage-lie case: lead-builder checks only).

## 8. Remaining technical coverage limitations
A25(a): graft-only, execute leg only, outside the documented threat model (unsigned store write); no pin-export leg. A25(e): effective_profile_digest decomposed only; host digest one workflow. M06: harness-level detection only; mutants D06-M06/D1-M14 alter live derivation only. Q5: non-journal branch, raising provision, live-side drift. Q6: Verifier sha `39d46b49` unpinned (Control Plane pins none; CI does not install it); format-module test passed only as a modified copy; plain-journal check-id linkage not required by contract and unasserted (a zeroed id yields "abstain"). Python limited to 3.11.18 and 3.12.3. Builder CI logs not inspected.

## 9. Independent-authority limitations
All execution, review and custody work was done by subordinate agents of one session that also produced the readjudication; this is the same lineage as the evidence. ADOPTION.md: independence "cannot be inferred from a second automated process alone". No designation of an independent qualification owner and no competent certification authority exist; none is invented. These are reserved gates, not engineering failures. Distinct stages: technical qualification completed (this record, bounded); independent technical acceptance NOT ESTABLISHED; competent certification NOT ESTABLISHED; final Tier 1 DEFERRED, NOT WAIVED; production release HOLD.

## 10. Holds
Registry #58/#59, Control Plane #87, Ed25519 #26/#34 HELD; V09 SEPARATE; constructor tolerance NOT AUTHORIZED; publication/release/production HOLD; DEF-OBS-TOL-OVERFLOW-1 OPEN, SEPARATE; R1 DEFERRED.

Contract determinations behind Q2/Q3 and Q6-A: `contract-determinations/` (read-only analyses by subordinate agents of the lead builder session; not independent).
