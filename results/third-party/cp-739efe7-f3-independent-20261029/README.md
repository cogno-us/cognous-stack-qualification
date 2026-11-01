# Third-party session record: independent F3-A / F3-B qualification of Control Plane `739efe7`

**Status: PROPOSED (this PR is open and unmerged).** Custody is not established until this directory is merged to `main` and verified from a fresh clone with `sha256sum -c SHA256SUMS`. Nothing here is a hub run, a Tier 1 verdict, an independent certification, a release authorization or a production authorization. Holds unchanged: publication, release and production HOLD; final independent Tier 1 DEFERRED, NOT WAIVED.

This record is retained exactly as produced. Nothing in the bundle, the protocol or the verdict was edited for filing. Corrections or successor evidence must be new directories that reference this one.

## Subject (exact identities)
| Item | Identity |
|---|---|
| Control Plane (candidate under test) | `cogno-us/cognous-control-plane` `739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69`; `src` tree `d248bde478ae3f2ce050db4637f0c1203066e906`; `schemas` tree `2e927251a664de16fef10b8295758e34bd947488` |
| Registry | `cogno-us/cognous-ocs-registry` `2815643c3e15fbc6aadadbf88dc7596f10120992` (working pin `a40fe755e2384a99c37016fa9ad59396f1835900`) |
| Work package | OCS-F3-INDEPENDENT-20261029 (Archetype D, independent qualification) |
| Frozen protocol | `PROTOCOL-F3-v1.md`, sha256 `e799b1083743526648a0c1c23d2c1455c0533ac843d88f3fe977dfd6a3850135`, frozen in evidence commit `e08b5c2` before any candidate execution |
| Evidence bundle | `F3-qualification-evidence-ed31764.tar.gz`, sha256 `1d07a70439625de3b3e85e0ea3c088a43f14bc237649487d22d85da51a174fc5` (12,816,115 bytes, 5,792 entries) |
| Evidence commit | `ed31764` of the qualifier's local evidence repository (not published as a git object anywhere; the bundle carries it as `F3-evidence.bundle`) |
| Verdict report | `verdict.md` (original name `VERDICTS-F3-20261029.md`), sha256 `57546d2b3fd390d905a731ee7904660fa06f42128aaeae68593a0677a8342cb1` |

## Original verdicts (preserved)
* **F3-A: FAIL, DEV-PE-1 (CONTRACT-LITERAL).** 74 passed, 23 failed in the final run. The 23 failed assertions are 22 x `test_A19_pin_export_refuses_per_perturbed_member[<member>-pin-export]` and 1 x `test_A06_frozen_legacy_store_cutoff_semantics`, sub-case `pin:cutoff0_idx0`. Each fails `reason_names_code` and `durable_effect_time_refusal`; everything else in those cases passed. The execute path was solid.
* **F3-B: PASS, scoped.** 21 passed, 1 failed as run (B11, one `attempt_statuses` sub-expectation adjudicated as harness over-specification and not edited); declared scope limits apply. See `verdict.md`.
* Raw observations, harness versions, amendment history (AMEND-n), mutation runs and manifests are inside the bundle (`MANIFEST-final.txt`, 168 lines, verified 168/168 at filing preparation). First-run outputs are preserved; amendments are logged, never overwritten.

## Qualifier identity and independence limits
Produced by a Claude Code session (model family Claude) acting as `independent_qualification_owner` under the Architect's assignment. Session: https://claude.ai/code/session_01VFvQdmswQGR49FcW7guMvk. Independence is **not evidenced** by this record: git authorship cannot distinguish builder and qualifier (all are "Claude"), no competent designation record is filed here, and this same session later acted for the implementation owner on the DEV-PE-1 remediation (it is therefore ineligible to readjudicate F3-A). This hub's own protocol treats a Tier 1 verdict as requiring a designated lead (`docs/registry-v1-qualification-preparation/06-evidence-capture-and-custody-protocol.md`); this record is not one. Treat it as a prior independent-session record, non-suite, unverified by the hub.

## Successor interpretation (separate from this evidence)
The Architect-approved successor clarification OCS-F3A-DEV-PE-1-INTERPRETATION/1.0 is proposed in Registry PR #80 (https://github.com/cogno-us/cognous-ocs-registry/pull/80), adopted in principle (decision D1) pending the Architect's post-review confirmation. It does not amend the frozen oracle or protocol and does not convert the FAIL into a PASS. **No successor qualification evidence exists yet.** A fresh independent qualifier has not been appointed; any readjudication must be filed as new evidence in its own directory and must not alter this one.

## Limits
Bounded synthetic profile; not Tier 1; no paid or external execution; A25(a) authority-domain and A25(e) host/effective-profile-digest members were not isolable; mutant D06-M06 survived; pin-export can declare the F4 family only; DEF-OBS-TOL-OVERFLOW-1 is open and separate. Full statement in `verdict.md`.

## Files
See `manifest.json` and `SHA256SUMS` (written last; this README is not listed, following `results/comparisons/g2-r10-20261020/`).
