# Registry import probe (REGISTRY-PROBE-S3) - verdicts. Governing: Constitution @1c2e920f; Issue #254. Narrow CP-to-Replay IMPORT result only; NOT Registry enforcement qualification.
Probe commit 877bc005 (probe file unedited). Tuple: CP b19c47dd, Replay d395e37c (E1), Registry 6b96a9a6 (tuple) / a40fe755 (bytes exercised; code-equal outside docs/+README.md, 62 doc paths differ). Synthetic keys, patched clock, one scenario.
| Check | Verdict |
|---|---|
| exact source identity / module origins | PASS (all modules loaded from the pristine checkouts; Registry bytes = a40fe755, not 6b96a9a6) |
| CP Registry-governed decision + execute | PASS (authorized, bound, acknowledged/applied) |
| Replay E1 import of real CP record | PASS_IMPORT (retains digest, family rows, CUR label; import report complete=False, finding B004; Replay marker internal_consistency_only_registry_source_revision_unverified) |
| missing member / plain-profile member / tampered digest / catalogue tie | REFUSED_AS_EXPECTED (Replay, typed refusals) |
| substituted configuration (age61, family dropped) | REFUSED_AS_EXPECTED CP-side at execute (authorization_binding_changed); Replay retains refusal record: RETENTION_ONLY |
| resealed substitution at Replay | NON_DETECTION_RECORDED (Replay ACCEPTED) |
| revoked / withdrawn / expired selection | REFUSED_AS_EXPECTED CP-side only; at Replay NOT_APPLICABLE (no selection state) |
| forged signature | REFUSED_AS_EXPECTED CP-builder-side (synthetic keys); at Replay NOT_APPLICABLE (no signature carried) |
| decision lineage (ids, action, tenant) | PASS |
| source lineage (Registry SHA/selection/signature/trust) | NOT_APPLICABLE / UNAVAILABLE |
| governed Runtime export | BLOCKED(PinnedControlPlaneExecutor.execute rebuilds workflow via workflow.__class__(...), cannot construct GovernedPolicyWorkflow; no production interface; not repaired, not fabricated) |
| Pack/ODES | NOT_RUN |
Non-claims: source authenticity; signature/trust; live configuration selection; runtime enforcement; decision/execution configuration consistency; independent verifier acceptance; qualification (NONE); claims_made = [].
