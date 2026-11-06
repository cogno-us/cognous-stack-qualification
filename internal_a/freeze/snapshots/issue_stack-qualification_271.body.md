# R4 / Q-A — Independent qualification protocol PROPOSAL: four-component vertical slice (Action Manifest → Control Plane → Replay Bundle → Governance Evidence Pack)

**Status: PROPOSED / UNFROZEN. Qualification-readiness decision package for Architect review. This is NOT a qualification, NOT a certification, NOT a release and NOT an acceptance. No qualification case has been executed. No workflow was created or dispatched. No PR. No component, pin, contract or developer evidence was modified.**

Prepared by the builder-lineage session (Claude, working for the Architect). **Builder lineage is not independence.** Everything below is *preparation material* that an independent qualification owner must adopt or rebuild before it can carry independent standing (Hub #259: "the independent Qualification Owner should rebuild the oracle before any re-run").

Cross-references: program [ORCH#142](https://github.com/cogno-us/cognous-stack-orchestrator/issues/142) · C4 tracker [ORCH#141](https://github.com/cogno-us/cognous-stack-orchestrator/issues/141) · Hub ledger [Hub#273](https://github.com/cogno-us/cognous-open-control-stack/issues/273) · controlling plan [Hub#267](https://github.com/cogno-us/cognous-open-control-stack/issues/267) (R4) · acceptance checkpoints Hub#276 (Milestone A, internal) and Hub#279 (Milestone B, formal, DEFERRED) · digest defect [Hub#280](https://github.com/cogno-us/cognous-open-control-stack/issues/280) (OPEN, not touched).
Companion comments on this issue: **(2) oracle + case battery + adversarial matrix**, **(3) evidence/custody specification + independence + reviewer verdict**.

Governance: Engineering Constitution reference revision `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`; **project-local adoption UNVERIFIED** (Hub#273 c6674059997 §19; Hub#267; Hub#276/#279; ORCH#141/#142). EP1–EP7 and CA01/03/04/18/21/23 applied as planning discipline only; no binding adoption is asserted.

---

## 0. Headline decision

| Gate | State |
|---|---|
| Protocol content (subject, oracle spec, battery, evidence design) | **PROPOSED — ready for Architect review** |
| Subject freeze (exact pins/hashes below) | **PROPOSED, source-verified 2026-11-06; not yet frozen by an authority** |
| Independent oracle owner | **MISSING — BLOCKED** |
| Independent qualification owner / executor | **MISSING — BLOCKED** |
| Qualification execution | **BLOCKED** (no independent owner; no frozen protocol; adoption UNVERIFIED) |
| Recommendation | **BLOCKED for qualification execution. READY_FOR_FREEZE-REVIEW only as a PROPOSED protocol; it cannot become an *independent* freeze until the Architect designates the owners in §10.** |

What a Q-A result could lawfully be called with *today's* authorities: at most **builder-lineage evidence, Architect-reviewed, INTERNAL NONPRODUCTION** (Hub#276 Milestone A ceiling: "INTERNALLY ACCEPTED (NONPRODUCTION)"). It could not be called *independently qualified*.

---

## 1. Qualification authority — what source actually says

| Question | Finding (source) |
|---|---|
| Canonical program | Hub#267 (R0–R5 reset). R4 = "Fresh minimal current qualification… Owner: independent qualification owner, separate from implementation writers… oracle independently owned" (Hub#267 body). Slice program ORCH#142. Hub#267 c6651707342 splits **Milestone A** (Hub#276: Architect-accepted internal nonproduction baseline) from **Milestone B** (Hub#279: formal independent qualification, DEFERRED). |
| Existing tracker in this repo | **None suitable.** QR open **issues** are only #240 (F3-only) and #53 (V1 findings); #235, #233, #224, #222 and #198 are open PRs; closed #218 is generic. This issue is the single new tracker. |
| Adopted policies | **UNVERIFIED for this slice.** Contradictory repo text: QR#249/#252 and a Hub role README call `1c2e920f` "adopted"; Hub#267/#273/#276/#279 and ORCH#141/#142 say UNVERIFIED. QR `docs/ocs-v1-qualification-reuse-audit/10` adopts only a Risk-Based Testing Addendum, only for the Registry V1 program. `TESTING_POLICY.md` **does not exist at `1c2e920f`** (404); it was added on main 2026-10-29. Tier taxonomy therefore used as planning vocabulary only. |
| Independent qualification owner | **MISSING.** Hub#267 c6648970937; Hub#259 c6650970539 ("no Qualification Owner or Adversarial Evidence Reviewer designated"). Role packets (Hub `docs/mvp-recovery/qgate-02/role-assignments`) "NOT YET INSTANTIATED" and concern MVP Q-GATE-02, not P1. QR `process/mvp-acceptance/owner-designation-request.proposed.md` is an unposted DRAFT; `process/qualification-owner.md` does not exist. |
| Independent oracle owner | **MISSING.** C4 contract (Hub#273 c6674059997 §8/§19): oracle is "builder-adjacent… oracle owner must be named at freeze (CA04)"; the freeze A1–A9 (c6674176671) names none. |
| Acceptance authority | Founder/Architect (login `titanicprime`) — decision and merge authority; "Architect reserves final acceptance/formal qualification/release" (Hub#267 c6650689271, Hub#276). The same login authored PR #149, dispatched the run, merged and wrote the closeouts. A8 (c6674176671) records component-owner acknowledgements as **temporary self-designations, not independent owner authority and "not an invented signature"**. |
| Reviewers observed | Copilot review bot (COMMENTED only) and same-lineage Claude workers = "builder-side inspection" (QR designation record: "never… independent; do not count toward CA04/CA23"). PR #149 shows 0 reviews / 0 comments on GitHub. |
| Freeze rules in QR | Exact 40-hex pins fetched by SHA with HEAD+tree verified, pristine checkout; oracle frozen in a dated commit before execution; amendments never to obtain a pass; candidate-commitment sha256 supplied from outside the checkout else INCOMPLETE; zero unexplained skips; results append-only. **Gaps:** QR has no CODEOWNERS and no classic branch protection (an active ruleset `main-protect` blocks deletion/force-push and requires a PR with 0 approvals), so "frozen on main" is not enforced by an independent reviewer; QR holds **no pin file or oracle for this tuple**; the C4 oracle lives in the orchestrator and is frozen only by an Architect comment. |
| Completed relevant qualification | **None for this tuple.** C1–C4 are hosted developer validation only. Prior QR work (S3, R1C-final, rw01, r2_chain, cap_v01/02, MVP chain, F3) used other tuples and was developer/builder-side or never dispatched; none transfers. |

### Distinction ladder (this slice, 2026-11-06)

| Level | Holder today | State |
|---|---|---|
| Development evidence | ORCH builder lineage | EXISTS (C1–C4 hosted runs) |
| Independent inspection | none independent (same-lineage reviewers; Architect re-hash of own artifact) | builder-side only |
| Independent qualification | nobody designated | **MISSING** |
| Competent certification | none | MISSING |
| Internal acceptance (Hub#276 Milestone A) | Architect | authority exists; no decision recorded |
| Product release / production | Architect/operator reserved | HOLD |

### Verdict-vocabulary conflict (needs a decision, D5)
QR has six coexisting vocabularies. `docs/execution-contract.md` uses PASS/FAIL/INCONCLUSIVE/NOT RUN/NOT APPLICABLE; Architect ruling D2 (reuse-audit 10/11) keeps the closed set and persists "BLOCKED" as *a reason, not a status*. The assignment requires PASS/FAIL/BLOCKED/NOT_EXECUTED/NOT_APPLICABLE. **Proposal:** use the assignment's five values in the qualification record; persist BLOCKED as `NOT RUN + reason` when interoperating with legacy QR tooling. The location of the reason field is UNVERIFIED; decision required.

---

## 2. A — Proposed exact Q-A subject (PROPOSED; verified from source 2026-11-06)

| Component | Commit | Git tree |
|---|---|---|
| Orchestrator (merge of PR #149, merged 2026-11-06T02:39:45Z) | `1504cf409fa352305d3fced589a0ad9e166819ec` | `4ac4e026648c2adda9836e366ffce9ca3d142da8` |
| Action Manifest | `fa170815ef96a54c233d0dd9da821b60debabf8b` | `3b0e3772e944aa668c8f4b879588c7cc3e2c32be` |
| Control Plane | `484fdbd297235dd24148ddb0703f2055a31eabff` | `c182939882103015f12c5360fccf377c54e2c4f9` |
| Replay Bundle | `93a76e281fcae6a65d2cd1d35376f87442dafb95` | `aca6e6b8bdd33d51db3b34bc0c75eff93b9ff88f` |
| Governance Evidence Pack | `065150852cc2a8abeb748777bb69d72ccd0e03d8` | `fe428a89da2e74346648cdfe014462ddc8624c77` |
| Qualification repo (protocol host) | `8e5e4ac31cae3300694bcaa3bfa67205e204813c` (#269; single-commit history; confirmed = `main`) | `079405d59804e5972489cc8b79a704ded2c5e634` |

Each of the five subject SHAs was confirmed as `origin/main` head **as of fetch/check time 2026-11-06** (local fetch + `gh api commits/main`); the freeze step must re-check. The PR head `8228df9a…` has the **same tree** `4ac4e026…` as the merge `1504cf4`; `git diff 8228df9 1504cf4` is empty. The subject is the merge commit, because that is what the hosted run executed (run 42152466722, attempt 1, `head_sha` = `1504cf40…`). Cross-ties in source: Replay `importers.py:118` names CP `484fdbd2`; Pack `importer.py:123` `CP2_REPLAY_PIN` = `93a76e28`, labelled **"PROVISIONAL DEVELOPMENT PIN, UNQUALIFIED, non-authorizing"** (`importer.py:110-128`).

**Identities.** Manifest file sha256 `789ad39596b9e1ef84a726a671883e1cb6b83343da3a31db0a1120906d68c074` (`refund-integration-pilot-v1` v1.1, blob `8f5c0788…`); AM canonical digest `sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac`; proposal fixture sha256 `1033c73e7dbe677cc71520711d3aaacb182952e5c12c8eaa489f24be0014cfe2` (no `proposal_id` field; identity = commitment `sha256:becaea3f10b5edf56ea181e0cd62793ebe8262238f948fb72dc5c0389c7f8c53`, tenant `tenant-alpha`). POS `effect_id` `sha256:4e5844d6…ecde8`; HOLD `effect_id` `sha256:d0e4afe0…18465` (differs by verdict, L23). These literals were read from sources/artifacts and independently re-observed by Worker C offline; they are not yet re-derived by a qualification-owned evaluator.

**Native entrypoints (as called by the harness; verified in source).** AM `load_manifest_json`, `validate_manifest`, `manifest_digest`, `RuntimeActionProposalV12.model_validate`, `proposal_digest`, `proposal_mismatches`. CP `BoundedAuthorizationWorkflow(...).decide(TenantRuntimeProposal, now=2026-10-05T19:00Z)`, generation `bounded-authorization-effect/0.3-strict-tenant`, `RuntimeAuthorityProfile(catalogue_version "synthetic-catalogue/1")`, `allow_synthetic_resolver=True`, plus unshipped CP **test helpers** `sign_evidence`/`bind_approval` and private `bounded._canonical_bytes` (blob-checked). Replay `import_bounded_workflow(record, proposal=, control_plane_revision=)`; bundle_version 0.2.0. Pack `import_manifest_reconstruction(manifest, bundle)` → `validate_evidence_pack` → `dump_evidence_pack`. All four: Python ≥3.11, Apache-2.0; CP needs pydantic ≥2.12, cryptography ≥43.

**Effective configuration.** C4 = CP **profile-enabled** configuration (L21); C1 ran the same workflow without a `RuntimeAuthorityProfile` (`real_c1.py:257-262`), so C1 records are not the C4 source records.

**Harness/oracle files (sha256 @ `1504cf4`; subjects of evaluation, never oracle sources):** `real_c4.py` `3843b6e7a7ee…284d`; `c4_producer.py` `7d833ab22f88…2971`; `c4_hosted_check.py` `d681662f7968…95ef`; `real_c3.py` `c92883af328f…c31b`; `c2_producer.py` `7c4f2595d793…a895`; `test_real_c4.py` `34faa8fe3d92…9fe9`; `test_real_c4_integrity.py` `07cf8cc437ae…6f0e` (full 64-hex values retained in builder scratch notes and must be re-captured by the qualification owner at freeze).

**Workflow/environment.** `.github/workflows/manual-contract-edge.yml` job `c4-real-edge` (lines 1214-1424; file sha256 `e17b5a1d26c7a019d38d2c5b8aecddc4be3dda3810f8125b5ccee4281f2f1cb3`, blob `905562b1…`); `permissions: contents: read`; manual dispatch from `refs/heads/main` only; actions SHA-pinned (checkout `11d5960a…`, setup-python `a26af69b…`, upload-artifact `ea165f8d…`); deps `pip install --require-hashes --only-binary=:all:` from `.github/locks/cryptography-pydantic-pytest-513753.txt` (sha256 `33a9e3605c5188a78c816fefd20938a8bf0299fc0fb8eda8e224f126409bde2b`; pydantic 2.14.1, cryptography 50.0.2, pytest 8.4.2, pydantic-core 2.50.1). Hosted observation: runner image ubuntu26 `20261101.186.1`, Python 3.13.18, pip 26.2.2, git 2.56.0.

**Floating items that defeat an exact freeze (must be recorded as environment identity or pinned by the owner, never silently accepted):** `runs-on: ubuntu-latest` (image floated); Python pinned to minor `'3.13'` only; pip/git unpinned; run-time network fetch of the four sources (content-pinned by tree check) and PyPI wheels (hash-locked); integrity tests require full orchestrator history (`aff43bdd`, `fce552de`); per-run values (`decision_id`, `bundle_id`, `generated_at`, `pack_id`, record/bundle/pack hashes) are **non-golden**; **the C1–C4 contracts are mutable GitHub comments** (Hub#273; the C4 contract comment is still headed "PROPOSED / NOT FROZEN"; the freeze is the separate A1–A9 comment). Comment body sha256 at inspection: C4 contract 6674059997 `405e2568…8f7e`, Architect freeze A1–A9 6674176671 `ed045086…86df`, C4 closeout 6675593994 `f27d577e…53aa5`, C3 contract 6671327666 `a0b2e8df…ca4e8`, C3 freeze 6671384213 `d56e5479…6e38`, C2 freeze 6665625039 `e44a6690…761`, C1 freeze 6660913875 `72faf87b…6cb`. Edit history was not inspected. **A freeze must therefore snapshot the comment bytes into the evidence record.**

**Full L1–L27** (verbatim at `real_c3.py:71-92` for L1–L19 and `real_c4.py:82-94` for L20–L27) remain applicable and are carried into the evidence record verbatim; Q-A cannot eliminate any of them. The provisional, unqualified Pack↔Replay profile (L16) is retained.

---

## 3. K — Reconstruction of developer evidence (what was independently re-derived, and what was not)

Recomputed from retained originals by an inspecting worker (GET-only; nothing rerun, nothing republished):

* C4 run 42152466722: attempt 1, `workflow_dispatch`, `head_sha` = merge commit; only job `c4-real-edge` (127678700422) ran, 22 steps success; c1/c2/c3/mock jobs skipped. Artifact 13472981580 digest `sha256:81ad900b767df6358f7919278207db3dbee4ad4e6633169f7938b07c07543786` equals sha256 of the downloaded zip. **26/26 indexed file hashes recomputed and match**; `evidence-manifest.json` (`73c4fc7c…539d`) is the self-excluded index. 126 tests (33 + 93) appear in the job log and `tests.json` — **not re-executed**. 481 oracle checks come from the orchestrator-owned checker re-reading its own output — **self-referential, not independent**.
* Verdict vector (`boundary-verdicts.json`): P1 → AM ACCEPTED / CP ACCEPTED(authorized) / Replay ACCEPTED (partial) / Pack ACCEPTED (valid) / chain ACCEPTED. N1-HOLD → CP REFUSED_NATIVE (native `hold`, `grant_revoked`, binding null) / Replay ACCEPTED (retains refusal) / Pack ACCEPTED (valid, 7 warnings) / chain `REFUSED_NATIVE@control_plane`. N2-FLIP → Pack REFUSED_NATIVE only (AM/CP/Replay NOT_EXECUTED, derived from N1 bundle). N3-GATE NOT EXECUTED.
* No-effect claim: both destination dumps are `{"effects":{},"grant_effect_counts":{}}` (sha256 `6ab0f91d…`), decide()-only. This is "synthetic SQLite destination observed empty by the harness" (L4, L25), not independent observation.
* **C1/C2 are weaker:** C1 artifacts have no per-file hash index; C2's closeout "12/12" and "132 checks" could not be reproduced from the retained manifest. C3 17/17 and 356 checks verified (self-referential). `/home/user/c3-evidence` is a **local re-run** (pydantic 2.13.5, different bundle hash), **not** original hosted C3 evidence, and must never be cited as such.
* **Artifacts expire** (C1 2027-02-03, C2 2027-02-03, C3 2027-02-04, C4 2027-02-04T02:46:44Z). Custody action required before then (see comment 3).

**Insufficient to support anything stronger than DEVELOPER-TESTED:** every PASS is an orchestrator-owned frozen-literal comparison; one actor authored, dispatched, merged and closed out; PR #149 has no recorded review; fixtures are a single hand-authored proposal and synthetic test-only authority (public Ed25519 seed `bytes(range(32))`, L2); the revoked grant is a synthetic input (L26); hashes are self-attested with no external trust anchor.

---

## 4. Corrections to the assignment's stated expectations (source-derived; must be frozen into the oracle)

1. **HOLD Replay findings are `{B005, B004}`** (observed order B005 then B004): B004 whenever `moltbot_export is None` (`importers.py:1210-1215`), B005 when a proposal is supplied and no decision carries a binding (`importers.py:1078-1084`). Positive case is exactly `[B004]`. ✔ consistent with the assignment.
2. **Pack counters are case-specific, not "zero everywhere".** POS: `authorization_granted_count=1`, `authorization_held_count=0`. HOLD: granted 0, held 1, lifecycle `held`. The six *attempt/effect* counts (control_plane_attempt, executor_attempt, attempt_transition_record, destination_effect, effect_observation, reconciliation) are 0 in both.
3. **Replay does *not* refuse a held→authorized flip.** Replay imports the flipped record as partial; only the Pack refuses ("decision … is authorized but has no binding", `importer.py:1059-1061`). N2 is a structural Pack refusal, not a Replay tamper-refusal.
4. **`deny` is never assigned by `decide()` on this path**; `hold` is the only refusal-like native result. No component emits the word "REFUSED"; `REFUSED_NATIVE`, `ACCEPTED`, `NOT_ATTEMPTED`, `retains_upstream_refusal`, `carried_authorization_state` and the chain verdict are **orchestrator labels (L25)**.
5. **A Pack `valid=True` on HOLD is native acceptance of evidence import — not acceptance, authorization or execution of the refused action.** The qualification record must say so literally.
6. **Hub#280** invalidates generalisation: AM `manifest_digest` hashes the parsed model with defaults filled (`binding.py:31`); CP (`bounded.py:2678`) and Pack hash the raw dict. All three agree **only for the fully populated fixture** (sha256 `789ad395…`); omitting `agent_description`, `owner`, `environment`, `default_action` or `metadata` makes AM ≠ CP = Pack (verified offline). Affected: O-AM2, O-CP2/3, O-PK2, O-E3, N3-GATE. Q-A claims are confined to the populated fixture.
7. "One run identity" (ORCH#141) is natively unsatisfiable; `run-1` is a literal (L24); Architect A6 reinterprets it.
8. C4 is decide()-only: no Runtime, Replay partial even on P1, AM→CP is an orchestrator gate plus byte pass-through (L20, A1), not a native data flow.

---

## 5. Q-A … Q-D scopes (distinct; a PASS in one is never a PASS in another)

| Profile | Scope | Status |
|---|---|---|
| **Q-A** | Frozen-fixture, source-pinned, decision-only four-component composition (this protocol) | plausible bounded candidate; **execution BLOCKED** (owners) |
| **Q-B** | General Manifest/Control Plane interoperability | Constrained by Hub#280 (OPEN); Q-A only *demonstrates* the divergence (case QA-09); no Q-B claim |
| **Q-C** | Authenticated, independently verifiable evidence provenance | Not attemptable: signed=false, no custody/freshness, synthetic public key (L2, L7–L10); needs additional evidence and possibly engineering authorization |
| **Q-D** | Real external-effect governance | Out of scope: no executor/destination; needs additional authorization |

**Q-A supportable claim (if and only if every mandatory required-invariant (RI) case, every precondition case and both controls are PASS under an independent owner; observe-only/limitation cases are tallied separately and never count toward this claim):** *bounded, source-linked composition of the four pinned components for one hand-authored synthetic fixture, evaluated against a pre-frozen oracle: POS yields a native `authorized` decision carried as a historical record through partial Replay and a valid Pack; the synthetic revoked-grant scenario yields native `hold`/`grant_revoked`, retained at each downstream boundary, with decide()-only zero attempts/effects.* **Unsupported claims:** production authorization, destination execution, absence of effect beyond decide()-only observation, authentic authority, freshness, custody, general Manifest/CP interoperability, tenant/proposal binding of held records, complete reconstruction, any qualification of the provisional Pack↔Replay profile, constitutional adoption.

---

## 6. L — Recommendation and required Architect decisions

**BLOCKED for qualification execution** (missing independent qualification owner and oracle owner; adoption UNVERIFIED; no frozen protocol). The protocol content is proposed; a separate read-only **builder-lineage** review was performed and its findings resolved or recorded (verdict and findings in comment 3). That review is not independent qualification and Worker F is not an independent authority. The package is ready for Architect *review*.

Decisions required before any execution:

| # | Decision |
|---|---|
| D1 | Designate (named, evidenced, recorded) an **independent Qualification Owner** and an **independent Oracle Owner**, separate from builder lineage and from the dispatching/merging identity — or explicitly choose a *labelled non-independent* internal Milestone-A route (Hub#276) with ceiling "INTERNALLY ACCEPTED (NONPRODUCTION)". Do not rename roles to satisfy independence (ADOPTION.md). |
| D2 | Designate who may declare PASS and who adjudicates (acceptance authority) and an **Adversarial Evidence Reviewer** distinct from the evaluator. |
| D3 | Constitution/testing-policy adoption for this slice: record an actual adoption instrument, or confirm it stays UNVERIFIED and the tiering is planning vocabulary only. |
| D4 | Approve or amend the Q-A subject pins (§2) and the snapshot rule for the mutable Hub contract comments; authorize snapshotting them into the evidence record. |
| D5 | Rule on the verdict-vocabulary mapping (§1). |
| D6 | Rule on execution venue: (a) one manual GitHub-hosted job in this repo (requires a new qualification workflow — **not created now**; needs separate authorization and a separately authorized dispatch) or (b) owner-controlled local deterministic run with retained transcript. |
| D7 | Authorize custody: copying the original C1–C4 artifact zips + job logs to write-once storage outside the author's account before 2027-02-03, with a hash recorded by a non-author. |
| D8 | Decide the freeze-protection mechanism for QR (CODEOWNERS/branch protection or an out-of-band commitment sha256 posted by a non-builder). |
| D9 | Decide whether N3-GATE (mutated byte unspecified) and QA-21 (native outcome not yet derived; demoted to informational) stay informational. |
| D10 | Hub#280 remains a separate owner-decision item; confirm Q-A proceeds with the populated fixture only, and that Q-B is not claimed. |
| D11 | Confirm the cap: one bounded execution, deterministic synthetic fixtures, **no paid calls, no external effects**. |

---

## 7. Execution design (NOT to be run in this assignment)

```
G0 Independent protocol freeze   (owner adopts/rebuilds; protocol sha256 + comment snapshots posted by non-builder)
 → G1 Exact subject/config freeze (re-verify §2 pins/trees/blobs/lock; record image+interpreter identity)
 → G2 Independent oracle freeze   (single canonical oracle JSON, sha256 posted BEFORE any run; evaluator source hash; corpus hash)
 → G3 Evaluator self-tests (EST-01…12) on stubs — evaluator must kill all wrong variants; failure = BLOCKED, no subject run
 → G4 Qualification-owner authorization (named, dated, scope = Q-A only, no-effects, no-paid)
 → G5 ONE bounded execution (single shot; defect log; no oracle edits; late edit ⇒ new oracle version, old results retained)
 → G6 Independent results + adverse-evidence review (reviewer ≠ evaluator)
 → G7 Competent acceptance decision (authority per D1/D2; Q-A scope only)
```

Resources (estimates, not measurements): zero paid calls; one deterministic offline Python job (32 cases = 6 preconditions + 2 controls + 24 adversarial, plus 12 self-tests; native calls on small JSON; expected tens of minutes including source checkout and hash-locked install); no network beyond source checkout and PyPI wheels; no secrets; `contents: read`. Retention: original zips/logs per D7.

**Existing infrastructure reused (CA01):** `tools/pristine_checkout.py` and the `r2_chain`/`cap_v02` `fetch_sources.sh` pin-and-verify pattern; `cap_v0{1,2}/junit_gate.py` zero-case/skip gating; `tools/mvp_acceptance_gate.py` commitment/run-id binding/skip rule; `suites/_refusal_template.py`; `schemas/run-manifest-v1.schema.json`, `failure-register.schema.json`; `tests/test_e10_zero_case_rows.py`, `tests/test_job_skip_gate.py`; SHA256SUMS conventions; the orchestrator's **existing hash-locked dependency file** (reused to keep environment identity). **New (after authorization only):** one evaluator-owned runner that calls native functions directly — required because the developer harness hash-pins its inputs and accepts only three cases (`c4_p1_authorized_chain`, `c4_n1_hold_revoked_grant`, `c4_n2_flip_hold_to_authorized`), so mutated inputs never reach native logic. Not reused: the legacy 255-row/62-entry matrices and the 49 delegated workflows; `real_c4.py`/`c4_hosted_check.py` expectations.

**Risk tier.** Treated as **T4 acceptance milestone with T3 authority/security coverage** per the assignment; tier taxonomy is **planning vocabulary only**, policy adoption UNVERIFIED (D3). Risk-based, not count-based: the battery covers distinct weaknesses, not volume.


---
_Generated by [Claude Code](https://claude.ai/code)_