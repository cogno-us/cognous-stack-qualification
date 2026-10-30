# 02 Evidence applicability crosswalk and coverage plan

Method: for each obligation, what existing evidence exists, its class (BUILDER_TESTED / TECHNICAL_ASSESSMENT / INDEPENDENT), and whether it applies under CA07 (exact source, configuration, protocol). Existing evidence is not rerun where applicable. Nothing here transfers a pass across revisions.

Evidence classes: **Builder CI** = developer evidence. **Readjudication (PR #242)** = technical assessment by an AI session that is also the coordinator; not independent. **Original F3 (hub)** = AI-session qualification, preserved, FAIL under the literal oracle.

## Q1 Successor evidence custody
Applicable evidence: PR #242 (tree id `9004b517…` equals commit `44ce26eb`). Gap: merge plus independent fresh-clone checksum verification. No further execution needed.

## Q2 / Q3 (static analysis of 739efe7; nothing executed)
Why the original paths could not isolate the members:
- `scope.authority_domain` is a pure function of the manifest action's `authority_context`; the manifest digest is itself a base-binding member, so any supported way to change the live domain also changes `manifest_digest` and `proposal_commitment`, and the guards `authority_domain_mismatch` and `manifest_digest_mismatch` fire first. Natural isolation: structurally impossible.
- `effective_profile_digest` is the same digest function over the same held object as the persisted `catalogue_digest`, and `approval_commitment` covers the same profile; a natural live change trips `runtime_authority_approval_mismatch` or moves `catalogue_digest` first. Not isolable end-to-end; joint only.
- `host_profile_digest`: on the pin-export fixture (F4-only family) the effective profile equals the host profile (G5a: both equal `catalogue_digest`), so masking was impossible there. On an F5 class-age workflow `compose_profile` overwrites the host class age with the Registry-narrowed value, so a masked host edit keeps the effective profile, `catalogue_digest` and `approval_commitment` unchanged while `host_profile_digest` changes. The candidate's own documentation (section 10, masked-host bullet) says a host profile edit is refused even if the final profile is identical. Predicted reachable; unexecuted.

Evidence decomposition required (no end-to-end claim from component evidence):
| Layer | Q2 authority_domain | Q3a host_profile_digest | Q3b effective_profile_digest |
|---|---|---|---|
| Component equality | two real worlds d1/d2; member diff exactly `{scope.authority_domain}` | member equals independent commitment of host dump; host != effective on F5 | member equals independent commitment of held dump equals `catalogue_digest` |
| End-to-end refusal | natural: joint (`authority_domain_mismatch` + `manifest_digest_mismatch`); consistent-world: `authorization_binding_changed` with base-diff including `manifest_digest`; GRAFT: single `authorization_binding_changed`, base-diff empty | masked-host rebuild: durable `authorization_binding_changed` only, complementary diff exactly the member and digest | without re-issue: `runtime_authority_approval_mismatch` only; with re-issue: `authorization_binding_changed` with diff including `catalogue_digest`, `approval_commitment` (joint) |
| Reachability / guard order | file:line guard-order table and dependency chain | same | same |

GRAFT = a genuine member minted by production code in another domain's world is written into a genuine decision (unsigned store, a documented limit); no guard disabled. It isolates comparison plus live derivation, not natural reachability, and must carry that label.

Eight cases plus a mandatory feasibility probe are in `assignments/D-1-q2q3-isolation.json`. Allowed claims: "isolated end-to-end" only if the complementary diff is empty; otherwise "joint".

## Q4 D06-M06
Verified by the coordinator from recorded files (not rerun): the mutant diff (sha256 `3c381f7c…`) changes one line in `scope_identity()`; applied copy differs from `git archive 739efe7` in that line only; `raw/M06-mutant` shows `1 failed, 47 deselected` with exactly three failing persisted-content checks (`scope_equals_independent_expectation`, `scope_authority_domain_equals_manifest_domain`, `f4_scope_authority_domain`; persisted `constant-domain` versus expected `customer-refunds`) while the four digest checks pass; unmutated 739efe7 and 8616d5f pass the same test. G5a was pre-declared in the frozen protocol as informing the coverage limitation only. The harness hash is bridged only by AMEND-R3.
Not established: that the binding comparison itself is sensitive to `authority_domain` (the same function feeds both minted and live sides, so the comparison cannot differ under M06). The original M06 SURVIVED record stands. Independence of the kill: same session wrote the test after survival was known. Also note the 739efe7 readjudication run is 1 failed / 47 passed (G4 documentation), not all green.
Residual: independent re-execution on a pristine copy (assignment D-2).

## Q5 `provision_local_execution_claim`
Path: `provision_local_execution_claim` = callable check (TypeError first) then the same `_materialize_under_handoff` body as `materialize_local_execution_claim`; `provision(claim)` is called only after every D-06 check passes, under the lock. Existing coverage: the shared body is exercised through `materialize` (22 leaf perturbations x 2 revisions in the readjudication; mutant D06-M04 killed). Not exercised: provision plus a governed D-06 member (refuse or accept), the sink-not-called-on-binding-refusal property, TypeError ordering with a governed workflow. Builder tests that call provision use non-governed workflows. A non-journal (F4-only governed) claim branch uses plain equality without classification and is unexercised; noted for the Architect.
Minimum independent coverage: control, 4+ mismatch leaves, stripped/invalid/unknown-version member, legacy-accepted case at cutoff 1, TypeError-before-write; expectations: PermissionError, spy not called, no new EffectTimeRefusal, store effects equal to materialize.

## Q6 Python 3.12
Static facts at 739efe7: `requires-python >= 3.11`; `tests.yml` matrix 3.11 and 3.12 running the full suite and the Registry-pinned gated suites (including the FINAL3 gate at the same Registry pin a40fe755, minimum count 858) on both. Not skip-gated: the D-06 builder files (`test_effective_configuration_binding*.py`, `test_authorization_pin_export.py`, `test_claim_journal_stage.py`, `test_v02_claim_policy_binding.py`); they run only in the bare `pytest` step where governed ones report NOT RUN without the Registry pin. Recorded CI: public commit page shows `test (3.12)` succeeded (run 40913412623, Oct 29, 4m47s); step output and counts were not readable by this session, so the FINAL3 gate result is unconfirmed. Independent runs: all on 3.11.18; "Python 3.12 not run" appears in the original and readjudication records.
Applicability: CI may supply builder-class 3.12 coverage of gated suites; it does not cover the independent harnesses or the ungated D-06 files. Existing exact-source CI does not satisfy an independent 3.12 obligation.
Minimum: one Archetype D 3.12 run of the frozen harnesses plus the ungated D-06 files with a no-skip assertion; baselines 47/1 and 73/23 on 3.11.
