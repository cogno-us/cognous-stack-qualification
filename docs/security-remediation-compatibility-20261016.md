# Security remediation compatibility correction

The owner authorized fixing failing PRs and merging those that pass. These corrections preserve the security behavior proposed by runtime #90, Evidence Pack #28 and ODES #35; they do not weaken validation to reproduce historical permissive behavior.

- Runtime: the argv/stdin contract test now intercepts the bounded subprocess helper instead of an unused subprocess.run call. Runtime production code still enforces shell=False, output limits, deadline and process-group cleanup. The temporary binary is never executed by this contract mock.
- Evidence Pack: source-declared redaction stays false/unverified, while declared derivation remains preserved. No sensitive-content-removal assurance is inferred.
- ODES: synthetic recipient policies and status assertions bind exact issuer identities. Unchanged historical producers lack explicit use restrictions, so their packages must fail consumption and recipient acceptance even when current status matches. CLI refusals must return nonzero. Unsupported redacted derivation remains rejected. Checked-in producer packages and Evidence Pack renderings are regenerated in the owning repair PRs from unchanged retained sources, preserving unknown restrictions and unverified redaction. Historical permissive bytes remain in Git history; they are not silently accepted.
- Canonical migration records retain original source hashes and license notices, with modification notices and new destination hashes. Reusable workflow default source revisions identify the tested repair proposals, not selected-stack revisions.

## Local verification

Isolated checkouts of exact PR heads were overlaid with this changed canonical suite. All historical producer dependencies retain the immutable revisions from the respective reusable workflows.

| Source | Exact proposed revision | Result |
|---|---|---|
| Runtime | 95b938c6d71129ce52f8bd7a10f9b9565aa7dc8c | 381 passed, 57 existing skips |
| Evidence Pack | 201e5b5c0e173b0645622ef294f7b41dc40e87e4 | 183 passed, 27 existing skips |
| ODES | cb1898f2514d02e5a824607db3e0b941774cdd39 | 124 passed |
| ODES merged producers | same ODES head, separately pinned merged producers | 56 passed |

The runtime local command matches the hosted safety lane's exclusion of test_refusal_capture.py, which has its own workflow. These tests do not establish native-platform qualification, operational observer independence, or final integrated selected-stack security. No paid trials ran. Selected hub pins, package hashes and publication/production HOLD remain unchanged by this suite correction. Any repaired release package must be rebuilt and reconciled after integration.

Additional controls verify that recomputing all public hashes cannot promote missing source restrictions to permission. All 93 qualification tooling tests and dashboard regeneration checks pass locally. Evidence Pack accepted-generation checks also pass (43 tests) after its five JSON/Markdown fixture pairs are regenerated.
