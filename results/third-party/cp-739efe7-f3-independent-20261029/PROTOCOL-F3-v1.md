# OCS-F3-INDEPENDENT-20261029 — Frozen qualification protocol v1

Role: independent_qualification_owner · Archetype D · Subject risk T3 · Boundary T4 (focused, not the full final campaign)
Status at freeze: **no candidate test has been executed** by this qualification (CA04). Builder suites, CI and builder mutation results are developer evidence only.
Authority note (CA23): this outcome is an independent qualification result produced by an AI session. It is not a competent human certification and does not certify production readiness. See §9.

## 1. Subjects (frozen; never switched)
| Subject | Exact identity |
|---|---|
| Control Plane main (F3-A + F3-B candidate) | `739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69` (merge of #97) |
| F3-B predecessor (characterization) | CP #94 head `061a986563768f2f8f9f6c0861647a3c5b1935be` |
| Pre-change baseline (legacy binary, byte-identity) | CP `b7eb11aaeed9c766ecaae7d22955093f7f7cd1aa` |
| Registry main | `2815643c3e15fbc6aadadbf88dc7596f10120992`; r08-v8 integration `188e90efc02e857928e857998231473c3f235b16` |
| Registry working pin for r08-v8 suites | `a40fe755e2384a99c37016fa9ad59396f1835900` (verified: non-doc tree identical to Registry main; ancestor of main) |
| Oracle docs | Registry main `docs/family-migration/final-three/{02,03,04}`; handoff #79 head `430fbbca68a565bb95d2d5187e2646caa7e912e8` (non-authorizing) |
| Governance text | constitution `dcdbe3b76843d672ca3cfb1f000124ecd78ed03c`; normative files byte-identical to `230c0af` (checked); OCS project adoption (`1c2e920…`) is NOT changed by this work |
Evidence produced at feature heads (`5ffd0ae`, `4adb84b`, `b8fbe95`, `a1de48c`, `55488d2`) is not transferred. Python 3.11.18 (CI matrix 3.11/3.12; 3.12 not run — stated limitation).

## 2. Verdict rule
- Every case carries a tag: **CONTRACT** (traceable to Registry 02/03 text or the assignment's A/B coverage list) or **PROPOSAL** (qualifier-added, not a pre-existing obligation) or **OBSERVATION** (recorded, never scored).
- **PASS**: every CONTRACT case PASS, none BLOCKED, no unresolved CONTRACT deviation.
- **FAIL**: any CONTRACT case FAIL with a source-backed requirement; the original counterexample is preserved.
- **BLOCKED**: a prerequisite prevents any CONTRACT case; name prerequisite and authority.
- PROPOSAL/OBSERVATION failures are reported verbatim as adverse observations and do not by themselves decide a verdict. A partial pass is not acceptance.
- A deviation may be re-classified only by written interpretation from the Architect (competent authority); this qualification will not relax a CONTRACT criterion after seeing results.

## 3. Rulings made BEFORE execution (resolving worker questions)
| Id | Ruling |
|---|---|
| R1 | Doc 03 is the frozen minimum ("add, never drop"). Literal 03 wording is the oracle. |
| R2 | **Pin-export refusal** (03 L23). Two criteria, both CONTRACT: (a) a perturbed member ⇒ state ≠ active and payload None; (b) literal 03 "refuse with `authorization_binding_changed` and a durable `EffectTimeRefusal`" evaluated for **execute** (rebuild/restart or persisted-side drift) — CONTRACT. For pin-export, (b) is evaluated literally and tagged CONTRACT-LITERAL: if pin-export writes no durable row/code token, that is recorded as a deviation (DEV-PE-1) with severity assessed on whether the refusal itself holds. Not downgraded after results. In-process post-construction edits yielding adapter refusals `scalars_modified` / `configuration_binding_invalid` are strictly-more-refusal variants: criterion = refused, destination untouched; code recorded as OBSERVATION. |
| R3 | **Claim path in scope** (assignment A8): pin-export claim assessment AND `materialize_local_execution_claim`/`provision_local_execution_claim` are CONTRACT. |
| R4 | **Stricter-than-contract behaviors** (cutoff > decision count refused at construction; scalars must be ints 0..2^31-1; `scalars_modified` guard): treated as documented explicit rules satisfying 03 L25; tested on both sides; recorded OBSERVATION as stricter than 02 §5; never a fail. |
| R5 | **Documented limits are not violations**: unsigned store; no anti-rollback; `legacy_cutoff` host-supplied; mixed-fleet legacy writers; stripped member below cutoff accepted as legacy (A16 below-cutoff sub-case expected ACCEPTED); host change fully masked by stricter Registry value (A02_masked) = OBSERVATION. Any claim of anti-rollback or malicious-store integrity in code/docs ⇒ FAIL (A24). |
| R6 | Same-scope/same-configuration replay of a member is accepted by design (member is configuration-bound, not decision-bound); foreign scope MUST refuse (CONTRACT). |
| R7 | Duplicate JSON keys: fail-closed by exception with destination untouched satisfies refusal; a readable-store refusal row is not required (impossible). Which behavior occurred is recorded. |
| R8 | Pin-export fixtures can declare only the F4 family; unreachable family rows on the pin path are OBSERVATION (structural), not FAIL; family perturbation on the execute path is CONTRACT. |
| R9 | **Zero-window**: injected-clock oracle is CONTRACT: for remaining window w = bound − age, dispatch iff stall ≤ w (strict `>`); candidate permissions ⊆ predecessor permissions; deadline_new ≤ deadline_old. The real-monotonic behavior at w = 0 (authorized but never dispatchable; builder admits it) is OBSERVATION OBS-ZERO-WINDOW, reported to the Architect, not scored. Windows of 1–9 s use injected clocks. |
| R10 | **Extensions** (03 F3-B E3): reading (a) — anchored cached bound is the recorded bound and never exceeds the signed extension; extensions never applied to live purpose/identity/mandate. Interaction of an extension with a PolicyBinding-narrowed ceiling and the missing-reversibility-profile irreversible-class extension are pre-existing, outside the D-07 hunk: OBSERVATION / PROPOSAL. |
| R11 | Builder fixtures are claims. Legacy store and D-07 predecessor outcomes are regenerated independently (baseline `b7eb11a`, predecessor `061a986`); disagreement with builder fixtures is an adverse finding. |
| R12 | Builder repository helpers (foundation test fixtures, Registry builders) may be imported where no public constructor exists; this reuse is a stated independence limitation. No D-06/D-07 builder test or fixture is imported. |
| R13 | DEF-OBS-TOL-OVERFLOW-1 out of scope: no case uses `ObservationPolicy.clock_tolerance_seconds` ≥ 10**12. |
| R14 | Tier vocabulary: this protocol uses TESTING_POLICY.md T0–T4 at `dcdbe3b`. "Final independent Tier 1" in the assignment means the OCS-project final campaign: DEFERRED, NOT WAIVED. |
| R15 | Per-suite Registry pins: independent harnesses run with `OCS_REGISTRY_PIN_DIR=run/reg-v8`, `OCS_REQUIRE_REGISTRY_PIN=1`. Builder suites are run only as labeled developer corroboration, using the pin each suite hard-codes (a40fe755 for `test_final3_*` and D-06 files; 6f600ab/6c3e5e4/943ab18 etc. per D report); the 41 baseline failures are retained, and a differing count in this environment (pytest-asyncio present) is recorded, not hidden. |

## 4. Amendment discipline (CA04/CA06)
First-run outputs of every harness are retained. A harness/fixture defect (cannot construct a baseline) may be fixed only via a logged amendment `AMEND-n` stating the defect, the diff, and confirming that the expectation text and pass criteria are unchanged; the re-run is a new run, the first run is kept. An expectation or criterion is never edited after observing a candidate result. B-oracle errors surfaced at the predecessor run (Q7 caveat) are corrected by amendment and logged.

## 5. Case registry and mapping
Assignment items → harness cases (all CONTRACT unless noted). Harness files are frozen by sha256 in `MANIFEST-freeze.txt`.
**F3-A** (`work/A/test_f3a_independent.py`): A1 same-config/restart → A01, A20; A2 changed config refuses → A02, A18, A19(execute); A3 F4 scalars → A19 (f4 members); A4 ObservationPolicy → A19 (observation members); A5 family identity/contract/digest → A19 (family members, execute); A6 missing/unknown version → A03, A04, A13, A15; A7 legacy → A05, A06, A07, A16; A8 claim & execution paths → A19 (pin-export), A19_claim, A17_claim, A10; A9 wrong scope → A14 (foreign scope); A10 stored binding ≠ authorization → A08, A23. Adversarial: A11, A12, A13, A14, A15, A16, A17, A18. Fault: A21, A22. Compat: A09. Limits: A24, A02_masked (OBSERVATION).
**F3-B** (`work/B/test_f3b_independent.py`): B1 purpose boundary → B13 (+B01); B2 cached boundary → B12, B13 (cached); B3 delayed dispatch in former window → B11, B01; B4 after expiry → B03; B5 without PolicyBinding → B01, B11, B16; B6 with PolicyBinding → B09, B16; B7 grant-status → B04, B21; B8 identity/mandate → B05, B06, B21; B9 reversible/irreversible → B02, B07; B10 no external effect after refusal → B17. Additional CONTRACT: B08, B10 (source delta = removed gate), B14 (≥500-input seeded grid, predecessor vs candidate), B15, B18, B19, B20 (live/identity/mandate/cached); B20 binding+extension sub-case = OBSERVATION.
**Compat/baseline** (`work/C/compat_probe.py`, run with `--src` for `b7eb11a` and `739efe7`; compare): catalogue_digest, approval_commitment, RuntimeAuthorityProfile dump, schema sha256, reason vocabulary, EffectivePolicySnapshot.identity_digest, protected-file hashes. CONTRACT (03 F3-A E5, F3-B E5/E7).
**Mutation adequacy** (PROPOSAL; scratch copies only, `work/C/mutants/*.diff`): each applied mutant must be killed by the independent harness to count the harness as non-vacuous; survivors are reported, they do not change the subject verdict.
**Developer corroboration** (labeled, not evidence of qualification): builder suites at their hard-coded pins.

## 6. Environment and commands
`PYTHONDONTWRITEBYTECODE=1 …/venv311/bin/python -m pytest -p no:cacheprovider -q <harness>` with `F3_EVIDENCE_DIR`, `OCS_REGISTRY_PIN_DIR`, `OCS_REQUIRE_REGISTRY_PIN=1`, `F3_OLD_SRC` (b7eb11a src), `F3B_SUBJECT_SRC` (predecessor first, then main), `F3B_PRED_SRC`. No network, no paid calls, injected clocks, no sleeping. Pristine checkouts are never modified; verified clean before and after (`git status`, tree hash).

## 7. Out of scope / holds (unchanged)
Registry #58/#59 HELD; CP #87 HELD; constructor tolerance NOT AUTHORIZED; Ed25519 #26/#34 HELD; V09 SEPARATE; final independent Tier 1 DEFERRED, NOT WAIVED; publication/release/production HOLD; DEF-OBS-TOL-OVERFLOW-1 open. No R1 refactoring. No merges.

## 8. Known limitations at freeze
Python 3.12 not exercised; two-process/restart monotonic guard not testable cross-process; oracle derived from AI-authored docs (git shows all authors as "Claude"); reuse of builder foundation helpers (R12); GitHub PR API unavailable (identities verified through git refs); #94 PR body UNVERIFIED offline.

## 9. Reviewer provenance (CA23)
Qualifier: Claude (model `claude-sonnet-5-5`) in a fresh session, operating under the project owner's GitHub identity (`titanicprime`). Four read-only inspection workers (A source/contract F3-A, B source/contract F3-B, C oracle/coverage crosswalk, D source identity/custody) are subagents of this session; they hold no verdict authority. Independence limits: the oracle docs, the implementation and this qualification were all produced by AI sessions; git authorship cannot show a separation between oracle author and builder. This session did not write or edit implementation code. Competent certification and integration decisions remain with the human Architect.
