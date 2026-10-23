# NC4-03 proposal (revision 2): v4 as a strict refinement of v3

Status: PROPOSED by the builder. Non-authorizing. Production HOLD unchanged. Not frozen, not an acceptance.
Qualification owns the oracle and must independently review and freeze (or reject) this; the builder only proposes.
Revision 2 answers the independent review (CHANGES REQUIRED: revision 1 was weaker than v3).

## Why NC4-03 failed under v3
v3 forbade every non-literal `**` forwarding in `tools/mvp_ingress`. Two sites tripped it, neither forwarding a client value:
`synthetic_host.py:39` (lambda proxy to the Control Plane test fixture) and `:72` (`ExecutionOperation(**{k: getattr(p, k) for k in names})`, fixed names).
The v3 result is kept as raw history: `process/mvp-chain/history/nc4-03-v3-predicate-result.json` (v3 file untouched).

## v4 rule (suites/mvp-chain/_kwflow.py)
Base rule kept from v3 and tightened: any call to ANY callee with `**<expr>` is REJECTED unless `<expr>` is a statically proven fixed form:
(a) inline dict display with constant string keys (nested `**` only of such a display); (b) inline dict comprehension `{k: getattr(obj, k) | constant for k in NAMES}`
over an inline literal string tuple/list, or a name bound once and loaded once in the file (never aliased, passed, mutated, global/nonlocal); (c) lambda proxy bound
once to a name that is only called directly. A mapping in a variable is always OPAQUE. Prohibited keys (simulate, operation_id/operation_identity*, *writer*, set_*_*,
grant_id, grant_revision, effective_max_effects, authority_context_id, actor, principal, claim_id, idempotency_key) inside a fixed form need a literal value (simulate: None).
Also: import aliases bound; explicit `simulate=` must be None on any call; non-literal `*args` into a protected, unresolvable or protected-callable-receiving call is rejected;
a protected callable used as a value (alias, argument to run/submit/starmap/partial, `.__call__`) is rejected; protected set extended with `decide`, `bind_approval`,
`model_copy(update=)` (must be a fixed display). The oracle row also requires: all 6 files of tools/mvp_ingress scanned; the 10 real protected call sites seen by exact
(file, function, callee, ordinal) pin, count >= 8, sqlite receiver `c` excluded; no unmatched pins.

## Strictness relative to v3 (honest accounting)
v4 rejects everything v3 rejected, plus non-constant-key displays, prohibited keys with non-literal values, any `**` into `model_copy`, protected-callable escape and star-args.
Prohibited keys (mapping forms, `model_copy(update=)`): the list above plus manifest_id, manifest_version, manifest_digest, action_id, adapter_id, requirement_id,
authority_context_ref, requested_permissions, effects. Explicit keywords use the same list except claim_id, grant_id, grant_revision, effective_max_effects,
authority_context_id and requested_permissions, which the real trusted call sites pass explicitly with non-literal values (residual difference, disclosed).

**Residual relaxations versus v3 (two, both requiring explicit operator adoption):**
1. **Comprehension carve-out.** `{k: getattr(obj, k) for k in <literal tuple/list of non-prohibited string names>}` is accepted for ANY `obj` (v3 forbade every non-literal `**`).
   The keys are fixed and non-prohibited, but the values are whatever `obj` holds; they are not taint-tracked.
2. **Three exact-hash pinned sites in `synthetic_host.py`**, accepted only because the generic rules cannot prove them:
   - the lambda proxy `original(*a, **k)` (exposed through attribute assignment; target is the non-protected fixture `tra.proposal`);
   - `model_copy(update={"operation_identity": OperationIdentityProfile(<constants>)})` (prohibited key, trusted-host constant value);
   - `ExecutionOperation(**{k: getattr(p, k) for k in names})`, whose names include prohibited keys (actor, principal, manifest_*, action_id, adapter_id, requirement_id, effects)
     taken from the template proposal `p0`, not from the client.
   The pin is a hash over the normalised AST (`ast.unparse`) of the call and its whole enclosing function: comment-only, blank-line and formatting edits do NOT un-pin;
   any semantic edit inside that function does. Without the pins v4 FAILS on the real source (verified), as v3 does.

**Adopting v4 therefore needs explicit operator adoption of (1) the comprehension carve-out and (2) the three pinned sites, OR a refactor of those hub sites instead.**
The guarantee (no client-controlled simulate/authority-writer/operation-identity override/arbitrary keyword reaches a protected API) is otherwise unchanged; NC4-02 remains the execution evidence.

## Out of scope / limits
setattr, `__dict__.update`, positional client values, values under non-prohibited fixed keys (not taint-tracked, e.g. a client `customer_id`), anything outside the scanned files,
imports not followed, dynamic code (`exec`/`eval`). Static, source-level only.

## Evidence
`suites/mvp-chain/test_kwflow.py`: 44 negative fixtures (all REJECTED with the declared rule), 8 positive (ACCEPTED), baseline = all of tools/mvp_ingress at 43c526eb (accepted only via pins),
a no-pins control (fails), sqlite exclusion, vanished-site detection, and 24 mutants of the ingress copy (each fails): `**fields`, client simulate, comprehension, update(), partial, lambda proxy,
import alias + star-args, alias/poison/closure mutation, `run(execute, **fields)`, `pool.submit`, `starmap`, `__call__`, `decide(**fields)`, non-literal comprehension, names list gaining `simulate`,
model_copy update from client, and a change inside a pinned function (un-pins). Pinned-source verdict: v3 FAIL, v4 PASS (with pins).
