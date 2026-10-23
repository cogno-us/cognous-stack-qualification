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
Strictly stronger than v3 in all but one respect: v3 allowed any dict display as a `**` and any value of any key; v4 rejects everything v3 rejected, plus non-constant-key
displays, prohibited keys with non-literal values, protected-callable escape and star-args. The ONE remaining relaxation: three trusted-host sites are accepted by EXACT PIN
(hash of the call and its whole enclosing function, so any edit un-pins them), because the generic rules cannot prove them:
1. `synthetic_host.py` `original(*a, **k)` lambda proxy (exposed through attribute assignment, so (c) cannot show it closed; target is the non-protected fixture `tra.proposal`);
2. `model_copy(update={"operation_identity": OperationIdentityProfile(<constants>)})` (prohibited key, non-literal but trusted-host constant value);
3. `ExecutionOperation(**{k: getattr(p, k) for k in names})`: fixed names include `actor` and `principal`, taken from the template proposal `p0`, not from the client.
Without these pins v4 FAILS on the real source (verified), exactly as v3 does. The pins are a recorded exception: **they are a weakening versus v3's blanket ban only in that these
three reviewed sites are exempt, and they require Qualification/operator adoption before NC4-03 can PASS.** If adoption is declined, the alternative is to refactor the three sites in the hub.
The guarantee (no client-controlled simulate/authority-writer/operation-identity override/arbitrary keyword reaches a protected API) is otherwise unchanged; NC4-02 remains the execution evidence.

## Out of scope / limits
setattr, `__dict__.update`, positional client values, values under non-prohibited fixed keys (not taint-tracked, e.g. a client `customer_id`), anything outside the scanned files,
imports not followed, dynamic code (`exec`/`eval`). Static, source-level only.

## Evidence
`suites/mvp-chain/test_kwflow.py`: 37 negative fixtures (all REJECTED with the declared rule), 8 positive (ACCEPTED), baseline = all of tools/mvp_ingress at 43c526eb (accepted only via pins),
a no-pins control (fails), sqlite exclusion, vanished-site detection, and 19 mutants of the ingress copy (each fails): `**fields`, client simulate, comprehension, update(), partial, lambda proxy,
import alias + star-args, alias/poison/closure mutation, `run(execute, **fields)`, `pool.submit`, `starmap`, `__call__`, `decide(**fields)`, non-literal comprehension, names list gaining `simulate`,
model_copy update from client, and a change inside a pinned function (un-pins). Pinned-source verdict: v3 FAIL, v4 PASS (with pins).
