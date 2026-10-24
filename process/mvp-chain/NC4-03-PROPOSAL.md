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
Exactly three reviewed sites in `synthetic_host.py` are accepted by pin (see content-addressing below): the `original(*a, **k)` lambda proxy, `model_copy(update={"operation_identity": OperationIdentityProfile(<constants>)})`
and the 14-name `ExecutionOperation(**{...comprehension...})`. Each pin record states `reviewed_ingress_tree_sha256`, informational `originating_hub_commit` (43c526eb1c8df9f07942ac36a6b2d11e14775bd1), `ast_digest`
(sha256 over `ast.dump` of the call and its whole enclosing function; comments, blank lines and formatting are irrelevant, docstrings and every semantic change are not),
`trusted_input_origin` and `protected_destination`. The predicate FAILS if any required field is missing or empty (`pin_records_incomplete`), if the AST digest differs, or if the ingress tree digest differs from the reviewed one (`pins_unmatched` and the
underlying violations reappear). Qualification must independently establish the stated provenance of these three sites.

## What remains relaxed versus v3 (precisely)
1. The three pinned sites above (v3 failed on two of them; the model_copy site was not reached by v3 at all).
2. A closed lambda proxy forwarding its own `*a, **k` (v3 rejected it); none exists in the real ingress.
Nothing else is relaxed: the generic comprehension exception is gone, and v4 additionally rejects everything above that v3 did not. Without the pins v4 FAILS on the real source (verified).
NC4-02 remains the execution evidence; this predicate is source-level only.

## Hardening in revision 4 (re-review F1-F3)
- Origin bindings are scoped to the enclosing function: a root name that is a parameter of that scope, is bound in any other scope, is global/nonlocal, or is shadowed by an
  intervening lambda parameter is rejected; only plain `name = <producer call>` bindings count.
- Producers must be method calls on the exact receivers of the real ingress (`host.workflow.decide`, `host.executor.provision_claim`, `host.build_proposal`); a bare, local,
  imported or differently-received name never qualifies, and any module-level/local def, import or assignment binding `decide`, `provision_claim`, `build_proposal`, `execute`, `envelope`,
  ... is rejected (`PRODUCER_SHADOWED`; class-body methods are exempt).
- `envelope` is treated like a protected callable: alias, value use and `getattr(host, "envelope")` are rejected; the direct-call caller rule is unchanged.
- **Pins are content-addressed (revision 5).** `scan_dir` computes `ingress_tree_sha256` = sha256 of the UTF-8 concatenation, over `tools/mvp_ingress/*.py` sorted by file name, of
  `<name>\0<sha256 hex of the file bytes>\n`. Each pin record carries `reviewed_ingress_tree_sha256`; a pin is honoured only when its `ast_digest` matches AND the scanned tree digest equals the reviewed
  digest. The originating hub commit (43c526eb) is informational only: an unrelated hub commit with byte-identical ingress files still PASSES, so moving the tuple hub sha needs no re-pin. Any byte change in
  any ingress file, including a comment-only edit, changes the tree digest and fails closed until Qualification makes a new pin record (intended; the pinned sites' `ast_digest` is unchanged by a comment).
  The oracle gates `ingress_tree_sha256` equal to the reviewed digest and `pin_records_incomplete` empty; `hub_revision_verified` and `pin_source_revision_mismatch` are informational output only.
  The six per-file sha256 values in `history/nc4-03-v3-predicate-result.json` are tested to reproduce the digest.
- N5: `host` must be bound exactly once in the enclosing function as `host = self._host` and must not be a parameter, for any producer call; the real ingress still passes with the same three pins.

## Limits (out of scope)
Class limits of the origin rule, stated plainly: it is name-based (producers and roots are identified by names and receiver text, not by resolved objects), it checks the shape of the source
expression plus scoped single assignment (not full data flow, not object identity), and it does not see positional client values.
setattr, `__dict__.update`, positional client values, values under non-prohibited fixed keys (not taint-tracked, e.g. a client `customer_id`), imports not followed, dynamic code,
parameters named `d`/`p` of `envelope` are trusted only through the caller rule within the scanned files. The origin rule checks the shape of the source expression and
single-assignment binding, not full data flow.

## Evidence
`suites/mvp-chain/test_kwflow.py`: 71 negative fixtures (each REJECTED with the declared rule, including client claim_id and the other five fields by keyword and display, generic comprehension
over an arbitrary obj, untrusted `envelope` callers), 7 positive, baseline = all of tools/mvp_ingress at 43c526eb (accepted only via complete pins; no-pins control FAILS),
pin-field-missing tests (4), comment-only edit does not un-pin, semantic edit un-pins, sqlite exclusion, vanished-site detection, and 43 mutants of the ingress copy each failing, including the
regression target `claim_id=fields["claim_id"]` at execute in `core._run` (rejected as ORIGIN_VIOLATION) and one mutant per remaining origin field.

## NC4-03 predicate v5 (independent Q1 review; PROPOSED, builder-prepared)

Narrowly scoped source-aware additions to `_kwflow.py` (no taint-analysis subsystem, no ingress change, `tools/mvp_ingress` untouched):

1. literal-only protected keywords `attempt_id`, `budget_id`, `expires_at`, `decision_input_commitment`, `decision_input_profile_version`, `now` (only `now=host.now` is accepted) and the RuntimeProposal keys `evidence_refs`, `risk_metadata`, `run_id`, `expires_at`, `not_before`, `expected_side_effects`, `tenant_id`;
2. rule `AUTHORITY_OBJECT_MUTATION`: attribute stores, `setattr`, `object.__setattr__` on non-self objects (including in helper functions); `DYNAMIC_PROPOSAL_CONSTRUCTION` (`model_validate`, `model_construct`, `vars`) and `DYNAMIC_ATTRIBUTE_ACCESS` (`__class__`, `__dict__`);
3. rule `POSITIONAL_NON_LITERAL` for `ExecutionOperation`, `ExecutionEnvelope`, `execute`, `provision_claim`;
4. rebinding by import-as, match capture, except-as and def/class of the tracked names;
5. separate recursive tree check (`INGRESS_TREE_FILE_LIST`: exactly 7 regular files incl. `BOUNDARY.md`, no directory, symlink or extension module; `INGRESS_TREE_DIGEST`); the `*.py` digest `ea37100d...` that the pins bind is unchanged;
6. `ast_digest` pins carry `ast_digest_python` and are honoured on CPython 3.13 only (fail closed elsewhere), the observation records the interpreter;
7. pin prose: `request_id` flows via `correlation_id` into the proposal commitment and is not among the 14 names.

Every evading mutant of the review has a negative test (`test_v5_evading_mutant_is_rejected_by_its_source_aware_rule`, pins re-based so that only the new rule decides) and the unmodified ingress still passes. Not covered, not claimed: see `limitations.nc4_03_not_covered_not_claimed` in expectations v7.
