# 06 Final custody and disposition (OCS-F3-EVIDENCE-CUSTODY-DISPOSITION), 2026-10-30

Append-only report under issue #249 (execution plan); per-Q tracking stays in #240. Documentation only; no evidence, protocol or earlier record is rewritten.

**Lineage and limits.** Custody checks and the Q4-Q6 applicability review were done by read-only agents of the same session lineage that produced the evidence. This is reproducible technical verification, **not organizationally independent certification**. No reviewer, independent owner or certifier is invented.

## 1. Hub main and merge identities
Qualification hub `main` at start of verification: `247d46ceacc159f298eed7bb6a3584343279d7f0` (fresh checkout, clean). All seven merge commits are ancestors of it (verified):

| PR | Merge commit | Content |
|---|---|---|
| #242 | `2b15604b5667b416aca8b29c1d000ce08ec71c9e` | Successor F3-A readjudication |
| #243 | `15bc49c212a2020c6145b6d1c28c69b55b4eae4b` | Q1-Q8 plan and assignments |
| #244 | `d744ecbc1101968e615b1bec7e26778ce88d595c` | D-1 A25(a)/A25(e) |
| #245 | `8de7143237e97cf4575b305aaeb6cf587c17cb84` | D-2 M06, provision, Python 3.12 |
| #246 | `7ddf917ccc743166d3f4f0d5bfeda4af7188a0f4` | Q6 successor |
| #247 | `247d46ceacc159f298eed7bb6a3584343279d7f0` | Q6-A stage-lie and applicability |
| #248 | `61877e172d8ce0bfc8a9b045aa22493e64e2944d` | Final technical closeout analysis |

Each merge adds only files inside its own PR directory (48, 53, 137, 90, 33 files; 9 and 3 documentation files for #243 and #248); no other path changed.

## 2. Frozen executable subject
Control Plane `739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69` (tree `1e7a7555eb3a956fcd2db21d3eb944169d0f7783`, src `d248bde478ae3f2ce050db4637f0c1203066e906`). Later heads (Control Plane `b19c47dd`, Registry `6b96a9a6`) are not the subject. Engineering closeout: Registry record 14.

## 3. Evidence custody verification (fresh checkout at `247d46ce`)
| Package | Source SHA | Protocol SHA-256 | Files | Checksum | Manifest | Custody |
|---|---|---|---|---|---|---|
| #242 `cp-739efe7-f3a-readjudication-20261030` | `739efe7d…`, `8616d5f6…`; Registry pin `a40fe755…` | `04f4f950f526d6e98f056f5635bb7a1acad1d3332f46c3ec1b0897150a169ad6` | 48 | 47 OK, 0 failed | 46 entries, complete | **PASS** (tree `9004b517b381e5bc57bf7079f11d73c20e4d64ed` = producer commit `44ce26eb`); presentation notes in section 4 |
| #244 `cp-739efe7-f3-q2q3-isolation-20261030` | `739efe7d…`; pin `a40fe755…` | `cb2d3ade429e8c881288f681f490c23bc7875014916c581325c840ee2d5af6af` | 53 | 52 OK, 0 failed | 51, complete | **PASS**; Python 3.11.18 only; graft/decomposed limits |
| #245 `cp-739efe7-f3-q4q5q6-20261030` | `739efe7d…`; pins `a40fe755…`, supplementary `943ab183…` | `fb31437768888e7847628ea05ef4c8365eef5a7836a4b859f74088ea2e781e8a` | 137 | 136 OK, 0 failed | 135, complete | **PASS**; builder D-06 gate recorded NOT MET as run |
| #246 `cp-739efe7-f3-q6-successor-20261030` | `739efe7d…`; Registry `943ab183…` (case C); Verifier `39d46b49…` | `25b076db6a2220926af76314ceb7415e7358e59a2a42bb5c9fb1f07ca796ea30` | 90 | 89 OK, 0 failed | 88, complete | **PASS**; Verifier unpinned; Q6-A frozen expectation not met (13/14) |
| #247 `cp-739efe7-f3-q6a-stage-lie-20261030` | `739efe7d…`; Verifier `39d46b49…` | `04ff5530c81ababce363512691ca9dc16b02dd803d069982bb8bccbb2fcc2000` | 33 | 32 OK, 0 failed | 31, complete | **PASS**; Verifier unpinned |
| #243 / #248 (documents) | refs verified present: Registry `6b96a9a6`, CP `b19c47dd`/`739efe7d`, constitution `dcdbe3b`/`1c2e920` | n/a | 9 / 3 | merged blobs equal PR-head blobs (12/12); 3 assignment JSONs validate against the schema | n/a | **PASS** (existence of referenced SHAs checked, not the truth of each claim) |

Predecessor `results/third-party/cp-739efe7-f3-independent-20261029/`: tree `a8e2ff2f5205c0d6334f90112b666de672924ed2` unchanged from `b7d81311` through `247d46ce` (empty diff). Original bundle sha256 `1d07a704…74fc5` and verdict sha256 `57546d2b…2cb1` recompute and match. Original verdict still shows DEV-PE-1 and the 23 failed assertions. No failed checksum; no BLOCKED package.

## 4. Custody note: presentation discrepancies (not rewritten)
- #242 README says `amendments/` holds AMEND-R1..R3; AMEND-R1.md holds R1 and R2, AMEND-R3 is its own file. Cosmetic.
- #242 `MANIFEST-freeze.txt` lists two unlabelled hashes each for the gap harness and runner (pre/post amendment, each matches a committed file) and non-repo-relative paths. Cosmetic.
- #242 `verdict.md` omits the pytest counts (they are in raw logs: 739efe7 "1 failed, 47 passed", 8616d5f "48 passed", M06 mutant "1 failed, 47 deselected"). Cosmetic.
- **Not cosmetic for reproducibility:** `compat_probe.py` (hash `b0845b2c…` in MANIFEST-freeze) is not committed in #242; its outputs are retained in `raw/G6-compat`, but the probe cannot be re-run or hash-checked from #242 alone.
- #246 verdict wording "only FORMAT_PATH changed": the successor is a one-test extract; FORMAT_PATH is the only change inside the retained function body; other tests and the `refused` helper are omitted (diff retained).
- #247 contract analysis cites test params at line 56 (actual 50) and skip at 153 (actual 154); sidecar block approximate (`if profile_on` at ~606). The conclusions are unaffected.
- #245: `post-run-integrity.txt` states "identical to pre-run: NO", superseded by two addenda (YES); tree ids equal.

## 5. Original F3-A FAIL (permanently preserved)
Original F3-A under the frozen literal oracle: **FAIL, DEV-PE-1, 23 failed assertions** (22 pin-export members plus A06 cutoff0 case). Unchanged.

## 6. Successor F3-A scoped technical outcome
Conditional scoped technical assessment (successor interpretation OCS-F3A-DEV-PE-1-INTERPRETATION/1.0, builder-prepared, human adoption of record 11 pending). Not independent acceptance.

## 7. F3-B
Scoped technical PASS; not reopened.

## 8. Q1-Q8 dispositions
| Q | Disposition | Basis and scope |
|---|---|---|
| Q1 | **CLOSED** (custody) | #242 merged at `2b15604b`; fresh-checkout `sha256sum -c` 47 OK, manifest, protocol hash and tree identity PASS. Reproducible custody verification only. |
| Q2 | **OPEN** | Graft-only mechanism evidence (execute leg). Natural end-to-end isolation NOT established. Contract AMBIGUOUS on sufficiency (analysis in `contract-determinations/`). Narrow Architect decision below. |
| Q3 | **OPEN** | host_profile_digest isolated on the F5 masked-host execute route only; effective_profile_digest decomposed only. Contract does not expressly accept decomposition; no retroactive criteria change. |
| Q4 | **CLOSED** (bounded) | Merged #245 custody PASS. M06 persisted-content mutant kill reproduced on a pristine copy (three checks fail, four digest checks pass). Does NOT establish live authority_domain comparison sensitivity (that stays under Q2). |
| Q5 | **CLOSED** (scoped) | Merged #245 custody PASS. `provision_local_execution_claim` governed D-06 journal path: 14/14 on Python 3.11.18 and 3.12.3 with a real spy; refusal rows leave the spy uncalled. Untested: non-journal F4-only branch, raising provision, lock-held sink, live-side drift. No production-wide inference. |
| Q6 | **CLOSED** (scoped, as defined by the Architect) | Merged #245-#247 custody PASS. Original 13 pass / 1 skip preserved; plain-journal check-ID linkage NOT APPLICABLE without operation identity (Architect-accepted, with the source citations); stage-lie successor 4 pass / 0 skip on each interpreter; original `test_v02_claim_policy_binding.py` 95/95 at its own pin `943ab18` (original 6 failures at `a40fe755` remain visible in #245); format-module test passes only as a path-parameterized one-test copy (bounded evidence, not repair; original still skips). Limits: Verifier `39d46b49` unpinned (Control Plane pins none; CI does not install it); freshness-only route untested; 3.11/3.12 equality covers cases run only. |
| Q7 | **Recorded; reserved gate** | AI-session authorship and same-lineage review recorded. Independent acceptance and competent certification NOT ESTABLISHED. |
| Q8 | **Separate governance matter** | Baseline `1c2e920` preserved; later adoption draft inactive. Did not block custody. |

## 9. Remaining A25 coverage limitations
A25(a): graft-only, execute leg, outside the documented threat model (unsigned-store write); no pin-export leg; mutants alter live derivation only. A25(e): effective_profile_digest decomposed (guard-first / joint); host digest verified on one workflow only; no unmasked negative control; policy-composition and class-unreadable workflows not covered. Python 3.11.18 / 3.12.3 only.

## 10. Independence and certification limits
Same-lineage agents only; ADOPTION.md: independence "cannot be inferred from a second automated process alone". No independent qualification owner or competent certification authority exists. Distinct and unmet: independent technical acceptance; competent certification.

## 11. Holds
Final independent Tier 1 DEFERRED, NOT WAIVED. Publication/release/production HOLD. Registry #58/#59, Control Plane #87, Ed25519 #26/#34 HELD; V09 SEPARATE; constructor tolerance NOT AUTHORIZED; DEF-OBS-TOL-OVERFLOW-1 OPEN, SEPARATE; R1 DEFERRED.

## 12. Links
Plan: https://github.com/cogno-us/cognous-stack-qualification/issues/249 . Tracker: https://github.com/cogno-us/cognous-stack-qualification/issues/240 . Original FAIL: `results/third-party/cp-739efe7-f3-independent-20261029/`.

## Narrow Architect decision outstanding
Do graft-only authority_domain mechanism evidence (Q2) and decomposed/F5-only digest evidence (Q3) satisfy the F3-A acceptance boundary (records 12-14 place A25(a)/(e) in it; the frozen text does not require natural isolation)? Until ruled, Q2 and Q3 stay OPEN.
