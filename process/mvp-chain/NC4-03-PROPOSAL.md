# NC4-03 proposal (revision 3): v4 corrected per Architect rulings #2

Status: PROPOSED by the builder. Non-authorizing. Production HOLD unchanged. Not frozen, not an acceptance.
**The protected guarantee is unchanged.** Qualification must independently approve this corrected predicate before freezing it; the builder only proposes. v1-v3 are untouched.

## Why NC4-03 failed under v3
v3 forbade every non-literal `**` forwarding in `tools/mvp_ingress`; `synthetic_host.py` line 39 (lambda proxy to a Control Plane test fixture) and line 72
(`ExecutionOperation(**{k: getattr(p, k) for k in names})`) tripped it. Raw v3 result: `process/mvp-chain/history/nc4-03-v3-predicate-result.json`.

## v4 rule (suites/mvp-chain/_kwflow.py)
- Blanket ban kept: `**<expr>` to ANY callee is rejected unless `<expr>` is (a) an inline dict display with constant string keys, or (c) a closed lambda proxy
  (bound once to a local name only ever called directly). A mapping in a variable is always opaque.
- **Removed (rulings #2 item 2):** the generic comprehension carve-out. No dict comprehension is accepted generically.
- Prohibited keys inside a fixed form (simulate, operation_id/operation_identity*, *writer*, set_*_*, actor, principal, idempotency_key, manifest_*, action_id, adapter_id,
  requirement_id, authority_context_ref, effects) need a literal value (simulate: None). Explicit `simulate=` must be None on any call. Any `**` into `model_copy` is rejected;
  `update=` must be a fixed display. Non-literal `*args` into protected/unresolvable/protected-callable-receiving calls and protected-callable escape are rejected.
- **R1 origin rule (item 3), bounded and source-aware, not a taint framework**, at protected calls, both as explicit keywords and as keys of a fixed display / `model_copy(update=)`:
  `claim_id` must be `<name>.claim_id` where `<name>` is bound only from `provision_claim(...)`; `grant_id`/`grant_revision`/`effective_max_effects` must be
  `<d>.binding.<field>` with `<d>` bound only from `decide(...)` (or the `d`/`decision` parameter of a function named `envelope`); `authority_context_id` must be
  `<p>.authority_context_ref|authority_context_id` and `requested_permissions` `[tuple(]<p>.requested_permissions[)]` with `<p>` bound only from `build_proposal(...)` (or the
  `p`/`proposal` parameter of `envelope`); a literal constant is accepted. Every call `X.envelope(a, b)` must pass `a` bound only from `decide()` and `b` only from `build_proposal()`.
  Anything else (including a client field, a request attribute, or a name reassigned from other data) is `ORIGIN_VIOLATION` / `ORIGIN_CALLER_UNTRUSTED`.
- The oracle row also requires all 6 files of tools/mvp_ingress scanned, the 10 real protected call sites seen by exact (file, function, callee, ordinal), count >= 8, sqlite receiver `c` excluded.

## Pins (item 1)
Exactly three reviewed sites in `synthetic_host.py` are accepted by pin: the `original(*a, **k)` lambda proxy, `model_copy(update={"operation_identity": OperationIdentityProfile(<constants>)})`
and the 14-name `ExecutionOperation(**{...comprehension...})`. Each pin record states `source_revision` (hub 43c526eb1c8df9f07942ac36a6b2d11e14775bd1), `ast_digest`
(sha256 over `ast.dump` of the call and its whole enclosing function; comments, blank lines and formatting are irrelevant, docstrings and every semantic change are not),
`trusted_input_origin` and `protected_destination`. The predicate FAILS if any field is missing or empty (`pin_records_incomplete`), or if the AST digest differs (`pins_unmatched` and the
underlying violations reappear). Qualification must independently establish the stated provenance of these three sites.

## What remains relaxed versus v3 (precisely)
1. The three pinned sites above (v3 failed on two of them; the model_copy site was not reached by v3 at all).
2. A closed lambda proxy forwarding its own `*a, **k` (v3 rejected it); none exists in the real ingress.
Nothing else is relaxed: the generic comprehension exception is gone, and v4 additionally rejects everything above that v3 did not. Without the pins v4 FAILS on the real source (verified).
NC4-02 remains the execution evidence; this predicate is source-level only.

## Limits (out of scope)
setattr, `__dict__.update`, positional client values, values under non-prohibited fixed keys (not taint-tracked, e.g. a client `customer_id`), imports not followed, dynamic code,
parameters named `d`/`p` of `envelope` are trusted only through the caller rule within the scanned files. The origin rule checks the shape of the source expression and
single-assignment binding, not full data flow.

## Evidence
`suites/mvp-chain/test_kwflow.py`: 57 negative fixtures (each REJECTED with the declared rule, including client claim_id and the other five fields by keyword and display, generic comprehension
over an arbitrary obj, untrusted `envelope` callers), 7 positive, baseline = all of tools/mvp_ingress at 43c526eb (accepted only via complete pins; no-pins control FAILS),
pin-field-missing tests (4), comment-only edit does not un-pin, semantic edit un-pins, sqlite exclusion, vanished-site detection, and 33 mutants of the ingress copy each failing, including the
regression target `claim_id=fields["claim_id"]` at execute in `core._run` (rejected as ORIGIN_VIOLATION) and one mutant per remaining origin field.
