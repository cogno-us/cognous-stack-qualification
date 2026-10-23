# NC4-03 proposal: data-flow / call-boundary source predicate (v4)

Status: PROPOSED by the builder. Non-authorizing. Production HOLD unchanged. Not frozen, not an acceptance.
Qualification owns the oracle and must independently review and freeze (or reject) this; the builder only proposes.

## Why
NC4-03 (v3, merged main 4298247e) FAILS because its source predicate forbids every non-literal `**` forwarding in `tools/mvp_ingress`.
Two sites trip it, and neither forwards a client value:
- `synthetic_host.py:39` `lambda *a, **k: original(*a, **k)`: proxy to the Control Plane test fixture `tra.proposal` (not a protected API).
- `synthetic_host.py:72` `ExecutionOperation(**{k: getattr(p, k) for k in names})`: `names` is a fixed literal list of 14 field names.
The v3 result is preserved unedited in meaning as raw history: `process/mvp-chain/history/nc4-03-v3-predicate-result.json`.

## What changes
Only the implementation-level predicate, per the Architect ruling (data-flow / call-boundary, not a blanket dict-comprehension exception):
- `suites/mvp-chain/_kwflow.py` examines every call whose callee resolves (through aliases, `functools.partial`, lambda proxies) to a protected API
  (`execute`, `provision_claim`, `execute_claim_atomic`, and the ingress equivalents: `ExecutionOperation`, `ExecutionEnvelope`, `OperationIdentityProfile`,
  `AtomicLocalControlPlaneExecutor`, `OperationIdentityAtomicAuthorityEffectDestination`, `LocalExecutionPolicy`).
- A `**` mapping is FIXED (statically known string-constant key set) or OPAQUE. OPAQUE into a protected or unresolvable callee is REJECTED. A FIXED mapping
  is REJECTED if it carries a prohibited key (`simulate`, `operation_id`/`operation_identity*`, `*writer*`, `set_{grant,approval,policy,evidence}_*`) whose value
  is not a literal constant (`simulate` must be exactly None). Non-literal `*args` into a protected call is REJECTED. Fixed trusted forwarding is ACCEPTED.
- `expectations.proposed.v4.json` is a new file; only the NC4-03 row differs from v3 (v1, v2, v3 untouched). `conftest.py` still defaults to v3;
  v4 is selected by `MVP_EXPECTATIONS` until Qualification adopts it. `_ingress.py` additionally records `source_level.kwflow` and keeps all v3 observation keys.

## Evidence
- 18 negative fixtures (indirect assembly via comprehension, proxy/lambda, intermediate dict, `update()`, `functools.partial`, alias, dynamic getattr,
  dict union, subscript store, helper proxy, `*args`, plus explicit client `simulate`, authority-writer key, operation-identity override): all REJECTED.
- 9 positive fixtures (fixed dict display, literal-name comprehension, fixed proxy to a non-protected fixture, fixed update/store, fixed partial, constant
  `operation_identity=True`, fixed `.items()` copy, `dict(fixed, ...)`): all ACCEPTED.
- Baseline ingress snapshot (byte-identical to hub 43c526eb `tools/mvp_ingress`) is ACCEPTED, 13 protected-name calls examined, lines 39 and 72 observed and judged.
- Mutation check: 8 client-fed mutants of the ingress copy (`**fields` into execute, client `simulate`, comprehension over client fields, `update(fields)`,
  partial, lambda proxy, non-literal comprehension iterable, names list gaining `simulate`) all FAIL the new predicate. On the pinned source: v3 verdict FAIL, v4 PASS.

## Does the guarantee change? No.
The protected property is unchanged: no client-controlled `simulate`, authority-writer capability, operation-identity override or arbitrary keyword reaches a protected
executor or claim API. v3 over-approximated it syntactically; v4 states it at the call boundary. No expectation was loosened to obtain a PASS: the v4 predicate rejects every
indirect client-fed construction in the fixtures and mutants. Residual limits, for Qualification to weigh (if it judges any of them a guarantee change it should stop for
operator adoption): static, intraprocedural and flow-insensitive; no import following; values under non-prohibited fixed keys are not taint-tracked (e.g. a client `claim_id`);
opaque `**` into a NON-protected, resolvable callee is permitted (v3 forbade it); the sqlite `c.execute` calls match the protected name `execute` (harmless: no `**`).
This is a source-level assertion, not an execution observation; NC4-02 remains the execution evidence.
