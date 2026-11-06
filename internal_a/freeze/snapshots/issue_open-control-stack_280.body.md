## Open interoperability defect: digest basis differs

**Status:** OPEN; builder-reproduced, not resolved. Source: https://github.com/cogno-us/cognous-stack-orchestrator/issues/138#issuecomment-6660750456

Action Manifest revision `fa170815ef96a54c233d0dd9da821b60debabf8b` hashes the parsed model with optional defaults filled. Control Plane revision `484fdbd297235dd24148ddb0703f2055a31eabff` hashes a raw parsed dictionary. For valid manifests omitting optional fields, these representations yield different digest values. A proposal digest accepted by Action Manifest then fails Control Plane with `manifest_digest_mismatch`, and the reverse digest fails Action Manifest.

**Decision:** C1 is development-frozen only for one fully populated Manifest 1.1 fixture and requires preflight digest equality. General interoperability is not accepted. No silent reserialization or fallback inside orchestrator.

**Remediation (separate authorization required):** Native component owners specify and approve one canonical digest basis, exact version/scope, preservation requirements and regression oracles. Demonstrate agreement for populated and omitted-optional-field cases, negative tests for unknown fields/tampering, and faithful retention of existing refusal semantics. No unrelated contract changes.

**Not authorized by this issue:** Implementation, merge, paid/external effects or release. Technical reviewer was same builder lineage, not independent qualification.

Links: [Hub contract ledger #273](https://github.com/cogno-us/cognous-open-control-stack/issues/273), [Orchestrator C1 #138](https://github.com/cogno-us/cognous-stack-orchestrator/issues/138), [Program #142](https://github.com/cogno-us/cognous-stack-orchestrator/issues/142).