# Third-party session record: independent F3-A READJUDICATION of Control Plane `739efe7` (successor `8616d5f`)

**Status: PROPOSED (new, append-only evidence directory).** Custody is not established until this directory is merged to `main` and verified from a fresh clone with `sha256sum -c SHA256SUMS`. It does NOT overwrite or edit `results/third-party/cp-739efe7-f3-independent-20261029/`, which remains the predecessor record (F3-A FAIL — DEV-PE-1; F3-B scoped PASS) exactly as filed.

**This is NOT:** a Tier 1 result, a hub run, a human certification, a release/production authorization, or a merge approval. Verdict dimensions integrity/business: NOT ASSESSED.

## Result in one line
F3-A under the original literal oracle (doc 03 L23): **FAIL (unchanged)**. Under the Architect-approved successor interpretation (doc 06): **technical PASS, scoped and CONDITIONAL** on the Architect's recorded confirmation of doc 06 (not found in any bound source). Formal independent acceptance: **BLOCKED**. No implementation defect found. See `verdict.md`.

## Contents
`verdict.md` (verdicts under both readings, cases, adverse findings, limits) · `PROTOCOL-F3A-READJ-v1.md` + `PROTOCOL-F3A-READJ-v1.sha256` (frozen 2026-10-30T02:21:56Z, before new execution) · `MANIFEST-freeze.txt` · `manifest.json` (source and contract identities) · `CROSSWALK-original-evidence-applicability.md` · `raw/` (all runs, including aborted attempts) · `amendments/` (AMEND-R1..R3) · `scoring/` · `harness/` (gap harness, runner, scorers; fixtures are imported from the original harness, see below) · `workers/` (reports of three read-only inspection workers; model output, no verdict authority) · `SHA256SUMS` (written last).

## Subjects
Control Plane `739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69` and `8616d5f64a901b8f858359809193961a1124b5f6`; Registry oracle `2815643c3e15fbc6aadadbf88dc7596f10120992`, successor `6bf83dd0e564951cb221c58cf9a4032f8db93e5c`, handoff/head `517062529f0507be81a8ac5e457a009db98f8d90`, pin `a40fe755e2384a99c37016fa9ad59396f1835900`; constitution `dcdbe3b76843d672ca3cfb1f000124ecd78ed03c`; original evidence hub `0d90e355238ca28549eed443efd4242c11de7f8a` / `2f3dcd55ff2b6345d774f8868fa83d62e1bc2f3e`.

## Independence provenance and limits (CA04, CA23)
Producer: a fresh Claude Code session, session https://claude.ai/code/session_01VFvQdn8XjieqzRUfpEtpgy, configured model claude-sonnet-5-5 (the serving model may differ). Distinct from the original qualifier session (session_01VFvQdmswQGR49FcW7guMvk; different scratchpad) and, per the bound records, from the remediation and integration-builder sessions; it started with no conversation memory of them. Limits: **no competent designation record** of this session as independent owner exists in the bound sources; same model family and AI authorship of the oracle, implementation and original qualification (git authors are all "Claude"); this session has access to shared project memory but did not read the project's builder handoff documents; the gap harness imports fixture helpers from the original qualifier's harness (shared tooling) while the assertions, instruments, claim driver, documentation checks and verdict logic are this session's own; three read-only workers assisted inspection. A second automated process does not establish independence (ADOPTION.md). Therefore formal independent acceptance/certification is BLOCKED pending human designation.

## Holds (unchanged)
Registry #58/#59 HELD; Control Plane #87 HELD; constructor tolerance NOT AUTHORIZED; Ed25519 #26/#34 HELD; V09 SEPARATE; final Tier 1 DEFERRED, NOT WAIVED; publication/release/production HOLD; DEF-OBS-TOL-OVERFLOW-1 OPEN; R1 refactoring DEFERRED. Not merged by this session; no custody is claimed.
