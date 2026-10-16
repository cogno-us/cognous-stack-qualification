# Native receipt inventory

Evelyne-Claudia's five receipt categories (verbatim headings from her 11:10 AM
message) mapped to native producer records in the frozen F5b reference. "Native"
means produced by the pinned components without any added adapter. "Added" means
re-serialization of native fields into a package-level JSON file under the
return-evidence-format schema; no new facts are invented.

Legend:
- E = exists and evidenced by the current suite
- P = present but not currently exercised by the chosen scenarios
- A = absent in the frozen reference (no adapter, no observer)
- T = transformation / re-serialization only (no new facts)

| # | Her sub-item | Native producer / record | Status |
|---|---|---|---|
| **1. Test and authority records** |
| 1.a | Scenario ID, run ID, action ID, timestamps, test configuration, frozen software/policy versions | `tools/run_security_runtime.py` writes `report.json` with pins, tree hashes, exchange profile, generation; pytest `junit.xml` carries test node IDs; `proposal.json` carries `action_id`. | E |
| 1.b | Original authority grant: issuer, principal, scope, validity period, grant revision | `grant` dict on `resolver.contexts[PROFILE]['grant']` with `grant_id`, `revision`, `principal`, `permissions`; `effective_grant_derivation_version`. **Issuer field is a synthetic constant**; validity period is implicit in `NOW`. | E (with limit) |
| 1.c | Revocation receipt: grant ID, issuing authority, effective time, new revision, provenance | The D03 case mutates `status.status='revoked'` directly on an in-memory status object. There is **no signed revocation receipt and no issuing-authority attestation**. `grant_revoked` reason is recorded in refusals. | **A (known limit)** |
| **2. Decision and intervention receipts** |
| 2.a | Action proposal + initial policy decision | `proposal.json` (`p.model_dump`); `d` from `f.decide()` with `decision_id`, `result`, `binding`, `reasons`; stored in `f.records`. | E |
| 2.b | Evidence of which authority revision was evaluated | `d.binding.grant_revision`, `resolution_check_event` phase=`input` records the revision read, `expected_effective_grant_digest`. | E |
| 2.c | Revocation or correction event | For D03: the status mutation is the correction event; refusal path then records `grant_revoked`. There is no separate revocation-event JSON produced by the runtime — the refusal is the only durable artifact. | E (with limit) |
| 2.d | Effect-time authority revalidation | `resolution_check_event` records at effect time; `EffectTimeRefusal` on `f.records.load().refusals`; executor refuses with `result.status='denied'`. | E |
| 2.e | Enforcement result (allowed/blocked/escalated) | `result.status` (`authorized` / `denied` / `unknown`); `result.attempted`; `control_plane_evidence['refusal']`. "Escalated" is not a native enum. | E |
| 2.f | Whether the execution adapter was actually invoked | `result.attempted` (bool); `export['execution_result']`; writer-side effect occurs only on `dest.commit`. | E |
| **3. Consumption and state-change evidence** |
| 3.a | Receiving component accepted / consumed intervention | `resolution_check_event` phase=`input` has `read_time`, `source_revision`, `consumed`; refusal reasons reflect which input triggered the refusal. | E |
| 3.b | Governing-state snapshots before and after correction | `destination-observation.json` snapshot; `EffectiveGrantDestination` state table carries `effective_grant_digest` before and after; `dest.observe()` state is `absent` for denied cases. | E |
| 3.c | Whether the intended action was committed, prevented, delayed, unresolved | `dest.effect_count(grant_id)` (0/1); `dest.observe(effect_id)['state']` (`absent`/`applied`); `result.status`. | E |
| 3.d | Authoritative destination observation with coverage and limitations | `destination-observation.json`. Coverage: single local SQLite; limitation: in-process observer (see `observer-spec.md`). | E |
| **4. Consequence evidence** |
| 4.a | Independently inspectable observation of what happened next | The SQLite file can be exported as a disposable snapshot (Phase 4), observed outside the test process via a read-only connection. In-run: in-process only. | T (export permits later inspection) |
| 4.b | Correlation between original action, intervention, resulting effect | Stable `effect_id` propagates through `d`, `env`, `result`, bundle, dest; `proposal_commitment` ties envelope to proposal; `check_events` link to refusals. | E |
| 4.c | Preservation of missing, contradictory, inconclusive evidence | Replay bundle `import_reports` carry completeness flags; `metadata['executor_failure_reference_verification']='source_asserted_not_independently_verified'`. | E |
| **5. Evidence integrity and review** |
| 5.a | Stable event IDs and links between records | `decision_id`, `effect_id`, `grant_id`, `attempt_id` thread through records. | E |
| 5.b | Source provenance, artifact hashes, schema versions | `report.json` from `run_security_runtime.py` records tree hashes and pins; evidence pack records transformation version; replay bundle records revisions. | E |
| 5.c | Replay bundle, validation results, evidence pack | `import_bounded_workflow` output; `validate_evidence_pack`; `render_traceable_markdown`; ODES `export_cognous_stack_package`. | E |
| 5.d | A separate REACHABLE™ assessment identifying DEMONSTRATED / CONTRADICTED / UNRESOLVED transitions | **Not produced by Cognous**; this is REACHABLE's independent assessment. The package will contain an empty REACHABLE-verdict column with the explicit note that the three labels are REACHABLE's to assign. | **A (intentionally — correspondence does not transfer proof)** |

## Summary of gaps

Only two cells above are **A** (absent):

1. **1.c revocation receipt as signed issuer attestation** — the frozen reference uses
   an in-memory status mutation. The native refusal reason `grant_revoked` carries the
   fact that revocation was effective but not an issuer signature. This is a declared
   limitation of the F5b candidate profile (see profile `limitations[3]`:
   "Missing signature verification remains missing") and is also stated in the bounded
   process doc. It is NOT a gap we can fairly close by adding a Cognous-side adapter;
   closing it requires an upstream issuer PKI, which is out of scope.
2. **5.d REACHABLE verdict column** — Cognous should not produce REACHABLE verdicts;
   doing so would violate "correspondence permits comparison; it does not transfer
   proof". This is correct absence, not a gap.

## Phase 1 instrumentation decision

Given the inventory above, no new telemetry is required. The run can proceed with:

- The native producer records already generated by the F5b suite;
- One package-level `observer.json` per scenario (status T — re-serialization of
  `destination-observation.json` and `effect_count` behind the declared
  local-synthetic-oracle label);
- The explicit disclosure of 1.c and 5.d in `README_FOR_EVELYNE_CLAUDIA.md` and in
  `CROSSWALK_REACHABLE.md`.

## Honesty check (does Phase 0 reveal a blocker?)

The two **A** cells are both already known and declared by the frozen reference and by
the bounded-comparison process. Neither is "we would need to add something that
doesn't exist and pretend it does to meet her 5 categories". Both can be reported as
honest limitations in the package. There is **no required-receipt gap covered neither
by native producers nor by the available observer**.
