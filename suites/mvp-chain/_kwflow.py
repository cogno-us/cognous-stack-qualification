"""NC4-03 v4 source predicate: a STRICT REFINEMENT of the v3 blanket ban on non-literal ** forwarding, with proven-fixed carve-outs.

SPDX-License-Identifier: Apache-2.0

PROPOSED by the builder for Qualification review and freeze (not frozen, not an acceptance, production HOLD unchanged).
SOURCE-LEVEL ONLY: a static AST analysis of tools/mvp_ingress; not an execution observation.

Base rule (kept from v3, tightened): any call, to ANY callee, whose keywords contain ``**<expr>`` is REJECTED unless ``<expr>`` is one of
the statically proven fixed forms below. A mapping held in a variable is therefore always OPAQUE (aliasing, passing to a call, mutation in a
nested scope or global, ``update()``, helpers: all rejected by construction). Carve-outs, each checked for prohibited keys:
  (a) an inline dict display with constant string keys (nested ``**`` only of another such display);
  (b) REMOVED (architect rulings #2): the former generic comprehension carve-out; the 14-name site is accepted only by exact pin. Formerly: an inline dict comprehension ``{k: getattr(obj, k) | <constant> for k in NAMES}`` where NAMES is an inline literal list/tuple of string
      constants, or a name bound exactly once in the file to one and loaded exactly once (the comprehension): never aliased, passed, mutated,
      or declared global/nonlocal;
  (c) a lambda proxy forwarding only its own ``*a, **k`` where the lambda is bound once to a local name that is only ever called directly
      (call sites are then judged by the same rules).
Prohibited keys inside a carved-out mapping (simulate, operation_id/operation_identity*, *writer*, set_*_*, grant_id, grant_revision,
effective_max_effects, authority_context_id, actor, principal, claim_id, idempotency_key) are allowed only with a literal constant value
(simulate: exactly None).
Further rules: explicit ``simulate=`` must be the constant None on any call; explicit operation-identity/writer/set_* keywords with a
non-literal value are rejected on protected callees; non-literal ``*args`` into a protected or unresolvable callee, or into any call that
receives a protected callable, is rejected; a protected callable referenced anywhere except as the direct callee of a call (alias, argument to
run/submit/starmap/partial, ``.__call__``) is rejected; ``model_copy(update=...)`` must be a carved-out display. Import aliases are bound.
Pinned reviewed sites: a violation whose exact call source hash is pinned in PINNED_SITES is reported separately (``pinned_sites_used``)
and is NOT a violation; a changed site un-pins itself and fails. Pins are a recorded exception and need Qualification/operator adoption.

Out of scope (limits, not hidden): setattr/__dict__.update, positional client values, values under non-prohibited fixed keys (not
taint-tracked), values inside constants-only forms, anything outside the scanned files, imports are not followed.
"""
from __future__ import annotations

import ast
import hashlib
import pathlib
import re

PREDICATE_ID = "nc4-03.v4.strict-refinement-dataflow"
PROTECTED_CALLS = frozenset({"execute", "execute_claim_atomic", "provision_claim", "decide", "bind_approval"})
PROTECTED_CTORS = frozenset({"ExecutionOperation", "ExecutionEnvelope", "OperationIdentityProfile", "AtomicLocalControlPlaneExecutor",
                             "OperationIdentityAtomicAuthorityEffectDestination", "LocalExecutionPolicy"})
PROTECTED = PROTECTED_CALLS | PROTECTED_CTORS | {"model_copy"}
BASE_PROHIBITED = re.compile(r"^(simulate|operation_id|operation_identity\w*|operation_override\w*|\w*writer\w*|set_(grant|approval|policy|evidence)_\w+)$")
MAPPING_PROHIBITED = re.compile(BASE_PROHIBITED.pattern[:-2] + r"|grant_id|grant_revision|effective_max_effects|authority_context_id|actor|principal|claim_id|idempotency_key"
                              r"|manifest_id|manifest_version|manifest_digest|action_id|adapter_id|requirement_id|authority_context_ref|requested_permissions|effects)$")
# explicit keywords: BASE plus the names the real ingress never passes explicitly with a non-literal value (it passes claim_id, grant_id, grant_revision,
# effective_max_effects, authority_context_id, requested_permissions explicitly on trusted call sites, so those stay mapping-only; disclosed in the proposal)
EXPLICIT_PROHIBITED = re.compile(BASE_PROHIBITED.pattern[:-2] + r"|actor|principal|idempotency_key|manifest_id|manifest_version|manifest_digest|action_id|adapter_id"
                                 r"|requirement_id|authority_context_ref|effects)$")
SQLITE_RECEIVERS = frozenset({"c"})

PRODUCER_RECEIVER = {"decide": "host.workflow", "provision_claim": "host.executor", "build_proposal": "host"}
ESCAPE_NAMES = PROTECTED_CALLS | {"envelope"}
SIX = frozenset({"claim_id", "grant_id", "grant_revision", "effective_max_effects", "authority_context_id", "requested_permissions"})
HUB_REVISION = "43c526eb1c8df9f07942ac36a6b2d11e14775bd1"
PIN_FIELDS = ("source_revision", "ast_digest", "trusted_input_origin", "protected_destination")
# Exact reviewed sites, keyed "file:qualname:callee#ordinal". ast_digest = sha256 over ast.dump (no line/col, so comments/blank lines/formatting are
# irrelevant) of the call node plus its whole enclosing function; any semantic AST change invalidates the pin. A pin with a missing or empty
# field makes the predicate fail (pin_records_incomplete).
PINNED_SITES = {
    "synthetic_host.py:SyntheticHost.__init__:original#1": {
        "source_revision": HUB_REVISION, "ast_digest": "6e674d7b5d28e15ec8e0e4fc67305b7b24f747ffeb707ff61cb40d79806456ae",
        "trusted_input_origin": "lambda *a, **k proxy installed on the Control Plane test fixture tra.proposal during trusted-host setup (setup_flow, fixed synthetic authority); no ingress request value is a parameter of it",
        "protected_destination": "original = tra.proposal (Control Plane fixture proposal template); not an executor/claim API"},
    "synthetic_host.py:SyntheticHost.__init__:model_copy#1": {
        "source_revision": HUB_REVISION, "ast_digest": "894a4c5b60e1e98d252d85c62f64422d5ace664c4c64a23800936f160596fbbb",
        "trusted_input_origin": "OperationIdentityProfile(resolver_id=RESOLVER_ID, resolver_version=RESOLVER_VERSION): module constants of the trusted host",
        "protected_destination": "cfg.model_copy(update=...) -> runtime-authority profile consumed by the workflow and AtomicLocalControlPlaneExecutor (operation_identity)"},
    "synthetic_host.py:SyntheticHost.envelope:ExecutionOperation#1": {
        "source_revision": HUB_REVISION, "ast_digest": "c2774557d47fc58ad136542c5bfbeeb0c7311c4bdfc0e119d83effd11c3093ca",
        "trusted_input_origin": "attributes of the template proposal p0 (via build_proposal: only customer_id, refund_reason, amount, unit, request_id come from the client under non-prohibited keys), fixed 14 field names",
        "protected_destination": "ExecutionOperation(...) constructor feeding ExecutionEnvelope for AtomicLocalControlPlaneExecutor.execute"},
}
REQUIRED_SITES = [  # exact-site pin of the real protected calls the oracle must see (file, qualname, callee, ordinal)
    ("core.py", "IngressCore._run", "decide", 1), ("core.py", "IngressCore._run", "provision_claim", 1), ("core.py", "IngressCore._run", "execute", 1),
    ("synthetic_host.py", "SyntheticHost.__init__", "bind_approval", 1),
    ("synthetic_host.py", "SyntheticHost.__init__", "OperationIdentityProfile", 1),
    ("synthetic_host.py", "SyntheticHost.__init__", "OperationIdentityAtomicAuthorityEffectDestination", 1),
    ("synthetic_host.py", "SyntheticHost.__init__", "LocalExecutionPolicy", 1),
    ("synthetic_host.py", "SyntheticHost.__init__", "AtomicLocalControlPlaneExecutor", 1),
    ("synthetic_host.py", "SyntheticHost.envelope", "ExecutionOperation", 1), ("synthetic_host.py", "SyntheticHost.envelope", "ExecutionEnvelope", 1)]
EXPECTED_FILES = ["__init__.py", "client.py", "core.py", "proposal.py", "server.py", "synthetic_host.py"]


def _is_const_str(n):
    return isinstance(n, ast.Constant) and isinstance(n.value, str)


def _lit_names(n):
    if isinstance(n, (ast.List, ast.Tuple)) and n.elts and all(_is_const_str(e) for e in n.elts):
        return [e.value for e in n.elts]
    return None


def _literal_ok(key, value):
    """A prohibited key may only carry a literal constant (simulate: exactly None)."""
    return isinstance(value, ast.Constant) and (value.value is None if key == "simulate" else True)


class Analyzer:
    def __init__(self, source, filename, hub_revision=None):
        self.hub_revision = hub_revision
        self.src, self.filename = source, filename
        self.tree = ast.parse(source)
        self.findings, self.pinned, self.examined, self.sites = [], [], [], []
        self.alias, self.assign = {}, {}
        self.loads, self.stores, self.escapes = {}, {}, set()
        self.parent, self._memo = {}, {}
        self._index()

    # ---- indexing -------------------------------------------------------------
    def _index(self):
        for n in ast.walk(self.tree):
            for c in ast.iter_child_nodes(n):
                self.parent[c] = n
            if isinstance(n, ast.Import):
                for a in n.names:
                    if a.asname:
                        self.alias[a.asname] = a.name.split(".")[-1]
            elif isinstance(n, ast.ImportFrom):
                for a in n.names:
                    if a.asname:
                        self.alias[a.asname] = a.name
            elif isinstance(n, ast.Name):
                (self.loads if isinstance(n.ctx, ast.Load) else self.stores).setdefault(n.id, []).append(n)
            elif isinstance(n, (ast.Global, ast.Nonlocal)):
                self.escapes.update(n.names)
            elif isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Name):
                        self.assign.setdefault(t.id, []).append(n.value)
                    elif isinstance(t, ast.Attribute):
                        self.assign.setdefault("." + t.attr, []).append(n.value)
            elif isinstance(n, (ast.AugAssign, ast.AnnAssign, ast.NamedExpr)) and isinstance(getattr(n, "target", None), ast.Name):
                self.assign.setdefault(n.target.id, []).append(getattr(n, "value", None))

    def names_of(self, e, depth=0):
        """Possible final callee names of an expression; 'UNRESOLVED' when it cannot be determined statically."""
        if depth > 6 or e is None:
            return {"UNRESOLVED"}
        if isinstance(e, ast.Attribute):
            return {e.attr}
        if isinstance(e, ast.Name):
            if e.id in self._memo:
                return self._memo[e.id]
            self._memo[e.id] = {e.id}  # cycle guard
            out = {e.id, self.alias.get(e.id, e.id)}
            for v in self.assign.get(e.id, []):
                if isinstance(v, (ast.Name, ast.Attribute, ast.Lambda, ast.Call, ast.IfExp)):
                    out |= self.names_of(v, depth + 1)
            self._memo[e.id] = out
            return out
        if isinstance(e, ast.IfExp):
            return self.names_of(e.body, depth + 1) | self.names_of(e.orelse, depth + 1)
        if isinstance(e, ast.Lambda):
            out = set()
            for c in ast.walk(e.body):
                if isinstance(c, ast.Call):
                    out |= self.names_of(c.func, depth + 1)
            return out
        if isinstance(e, ast.Call):
            f = e.func
            fname = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else None
            fname = self.alias.get(fname, fname)
            if fname == "getattr" and len(e.args) >= 2:
                return {e.args[1].value} if _is_const_str(e.args[1]) else {"UNRESOLVED"}
            if fname == "partial" and e.args:
                return self.names_of(e.args[0], depth + 1)
            return {"UNRESOLVED"}
        return {"UNRESOLVED"}

    # ---- helpers ----------------------------------------------------------------
    def qualname(self, n):
        parts, p = [], self.parent.get(n)
        while p is not None:
            if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                parts.append(p.name)
            p = self.parent.get(p)
        return ".".join(reversed(parts)) or "<module>"

    def _once_literal(self, name_node):
        """NAMES bound exactly once in the file to a literal string list/tuple and loaded exactly once (this use)."""
        i = name_node.id
        vals = self.assign.get(i, [])
        return (len(vals) == 1 and _lit_names(vals[0]) is not None and len(self.stores.get(i, [])) == 1 and len(self.loads.get(i, [])) == 1
                and i not in self.escapes and _lit_names(vals[0]))

    def check_mapping(self, node, lam):
        """Return [(rule, detail)] for the expression used as a ** mapping / update= display; [] means a proven fixed form."""
        if isinstance(node, ast.Dict):
            bad = []
            for k, v in zip(node.keys, node.values):
                if k is None:
                    bad += self.check_mapping(v, lam) if isinstance(v, ast.Dict) else [("NONLITERAL_KWARGS", f"{{**{ast.unparse(v)[:50]}}}")]
                elif not _is_const_str(k):
                    bad.append(("NONLITERAL_KWARGS", "dict display with non-constant key " + ast.unparse(k)[:40]))
                elif k.value in SIX:
                    if not self.origin_ok(k.value, v):
                        bad.append(("ORIGIN_VIOLATION", f"{k.value} value {ast.unparse(v)[:50]} has no trusted origin"))
                elif MAPPING_PROHIBITED.match(k.value) and not _literal_ok(k.value, v):
                    bad.append(("PROHIBITED_KEY_IN_FIXED_FORM", f"key {k.value!r} with non-literal value {ast.unparse(v)[:40]}"))
            return bad
        if isinstance(node, ast.DictComp):  # the generic carve-out was removed (architect rulings #2): values of an arbitrary obj are not proven trusted
            return [("COMPREHENSION_NOT_FIXED", "dict comprehension is not an accepted ** form (only an exactly pinned reviewed site)")]
        if isinstance(node, ast.Name) and lam is not None and node.id in lam:
            return []  # (c) the proxy's own *a/**k, closed lambda
        return [("NONLITERAL_KWARGS", f"**{ast.unparse(node)[:60]} is not a proven fixed form")]

    # ---- R1 origin rule (bounded, source-aware; not a taint framework) -----------------
    def _enclosing_func(self, node):
        p = self.parent.get(node)
        while p is not None and not isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef)):
            p = self.parent.get(p)
        return p

    @staticmethod
    def _arg_names(fn):
        a = fn.args
        return {x.arg for x in a.posonlyargs + a.args + a.kwonlyargs} | {x.arg for x in (a.vararg, a.kwarg) if x}

    def _is_producer(self, call, producers):
        """Producer = a METHOD call on the known receiver chain exactly as in the real ingress (host.workflow.decide, host.executor.provision_claim,
        host.build_proposal); a bare/local/aliased name never qualifies."""
        f = call.func if isinstance(call, ast.Call) else None
        return (isinstance(f, ast.Attribute) and f.attr in producers and ast.unparse(f.value) == PRODUCER_RECEIVER[f.attr])

    def _bound_only_from(self, use, ident, producers):
        """Scoped single-binding test: within the enclosing function of `use`, `ident` is not a parameter (of it or of an intervening lambda), is bound
        in no other scope, is not global/nonlocal, and every binding is a plain `ident = <producer call>`."""
        fn = self._enclosing_func(use)
        if ident in self.escapes or (fn is not None and ident in self._arg_names(fn)):
            return False
        p = self.parent.get(use)
        while p is not None and p is not fn:
            if isinstance(p, ast.Lambda) and ident in self._arg_names(p):
                return False
            p = self.parent.get(p)
        stores = self.stores.get(ident, [])
        if not stores or any(self._enclosing_func(st) is not fn for st in stores):
            return False
        assigns = [self.parent.get(st) for st in stores]
        return all(isinstance(x, ast.Assign) and len(x.targets) == 1 and x.targets[0] in stores and self._is_producer(x.value, producers) for x in assigns)

    def _root_ok(self, node, producers, params):
        """Name bound (scoped, single) only from a producer, or a parameter named in `params` of a function called `envelope`
        (whose every caller is separately required to pass producer-bound arguments)."""
        if not isinstance(node, ast.Name):
            return False
        if self._bound_only_from(node, node.id, producers):
            return True
        fn = self._enclosing_func(node)
        return bool(fn and fn.name == "envelope" and node.id in params and node.id not in self.stores and node.id in self._arg_names(fn))

    def origin_ok(self, field, v):
        if isinstance(v, ast.Constant):
            return True
        if field == "requested_permissions" and isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == "tuple" and len(v.args) == 1 and not v.keywords:
            v = v.args[0]
        if not isinstance(v, ast.Attribute):
            return False
        if field == "claim_id":  # the governed claim returned by the trusted provision path
            return v.attr == "claim_id" and self._root_ok(v.value, {"provision_claim"}, ())
        if field in ("grant_id", "grant_revision", "effective_max_effects"):  # authoritative decision binding
            return (v.attr == field and isinstance(v.value, ast.Attribute) and v.value.attr == "binding"
                    and self._root_ok(v.value.value, {"decide"}, {"d", "decision"}))
        if field == "authority_context_id":  # the selected trusted authority context carried by the template-derived proposal
            return v.attr in ("authority_context_ref", "authority_context_id") and self._root_ok(v.value, {"build_proposal"}, {"p", "proposal"})
        return v.attr == "requested_permissions" and self._root_ok(v.value, {"build_proposal"}, {"p", "proposal"})  # derived from the authorized operation

    def check_envelope_caller(self, node, ordinal):
        if isinstance(node.func, ast.Attribute) and node.func.attr == "envelope":
            a = node.args
            if not (len(a) >= 2 and isinstance(a[0], ast.Name) and self._bound_only_from(node, a[0].id, {"decide"})
                    and isinstance(a[1], ast.Name) and self._bound_only_from(node, a[1].id, {"build_proposal"})):
                self.record(node, "ORIGIN_CALLER_UNTRUSTED", "envelope(decision, proposal) must receive names bound only from host.workflow.decide() / host.build_proposal() in this scope", "envelope", ordinal)

    def closed_lambda_params(self, lam):
        """(c): lambda bound once to a name that is only ever called directly -> its own *a/**k names, else empty set."""
        p = self.parent.get(lam)
        if not (isinstance(p, ast.Assign) and len(p.targets) == 1 and isinstance(p.targets[0], ast.Name)):
            return set()
        n = p.targets[0].id
        if len(self.stores.get(n, [])) != 1 or n in self.escapes:
            return set()
        for use in self.loads.get(n, []):
            par = self.parent.get(use)
            if not (isinstance(par, ast.Call) and par.func is use):
                return set()
        return {x.arg for x in (lam.args.vararg, lam.args.kwarg) if x}

    def record(self, node, rule, detail, callee, ordinal):
        scope, p = node, self.parent.get(node)
        while p is not None and not isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef)):
            p = self.parent.get(p)
        scope = p or self.tree  # the pin covers the whole enclosing function, so a change anywhere in it un-pins the site
        digest = hashlib.sha256((ast.dump(node) + "\n--\n" + ast.dump(scope)).encode()).hexdigest()
        pid = f"{self.filename}:{self.qualname(node)}:{callee}#{ordinal}"
        f = {"file": self.filename, "line": node.lineno, "rule": rule, "callee": callee, "detail": detail, "source": ast.unparse(node)[:160],
             "site": pid, "ast_digest": digest}
        rec = PINNED_SITES.get(pid)
        pin = pid if (rec and rec.get("ast_digest") == digest and all(rec.get(k) for k in PIN_FIELDS)
                      and self.hub_revision and rec["source_revision"] == self.hub_revision) else None
        (self.pinned if pin else self.findings).append({**f, "pinned": pin} if pin else f)

    # ---- the check --------------------------------------------------------------
    def run(self):
        counts = {}
        for n in ast.walk(self.tree):
            if isinstance(n, ast.Call):
                self.check_call(n, counts)
                if isinstance(n.func, ast.Call) and (self.names_of(n.func) & ESCAPE_NAMES):  # getattr(host, "execute"/"envelope")(...)
                    self.record(n, "PROTECTED_CALLABLE_ESCAPES", "protected callable obtained through getattr", sorted(self.names_of(n.func) & ESCAPE_NAMES)[0], 0)
            elif isinstance(n, (ast.Attribute, ast.Name)) and isinstance(n.ctx, ast.Load):
                par = self.parent.get(n)
                names = self.names_of(n)
                hit = names & PROTECTED_CALLS
                if "envelope" in names and (isinstance(n, ast.Attribute) and n.attr == "envelope" or isinstance(n, ast.Name) and n.id != "envelope"):
                    hit = hit | {"envelope"}
                if hit and not (isinstance(par, ast.Call) and par.func is n):
                    self.record(n, "PROTECTED_CALLABLE_ESCAPES", "protected callable referenced as a value, not called directly", sorted(hit)[0], 0)
            self._shadow(n)
        return self

    def _shadow(self, n):
        bound = []
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not isinstance(self.parent.get(n), ast.ClassDef):
            bound = [n.name]
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            bound = [a.asname or a.name.split(".")[0] for a in n.names]
        elif isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            bound = [n.id]
        for b in bound:
            if b in set(PRODUCER_RECEIVER) | {"envelope"} | PROTECTED_CALLS:
                self.record(n, "PRODUCER_SHADOWED", f"local/module binding of the protected/producer name {b!r}", b, 0)

    def check_call(self, node, counts):
        f = node.func
        names = self.names_of(f)
        callee = (sorted(names & PROTECTED) or [self.alias.get(f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "<expr>"),
                                                                f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "<expr>"))])[0]
        is_partial = callee == "partial" or (isinstance(f, ast.Name) and self.alias.get(f.id) == "partial")
        protected = bool(names & PROTECTED)
        recv_sqlite = isinstance(f, ast.Attribute) and f.attr == "execute" and isinstance(f.value, ast.Name) and f.value.id in SQLITE_RECEIVERS
        counts[(self.qualname(node), callee)] = ordinal = counts.get((self.qualname(node), callee), 0) + 1
        receives_protected = any(self.names_of(v) & PROTECTED_CALLS for v in list(node.args) + [k.value for k in node.keywords]
                                 if isinstance(v, (ast.Name, ast.Attribute)))
        lam, par = None, self.parent.get(node)
        while par is not None and lam is None:
            if isinstance(par, ast.Lambda):
                lam = self.closed_lambda_params(par) or None
            par = self.parent.get(par)
        real = protected and not recv_sqlite and callee in (PROTECTED_CALLS | PROTECTED_CTORS)
        if real:
            self.sites.append({"file": self.filename, "qualname": self.qualname(node), "callee": callee, "ordinal": ordinal, "line": node.lineno})
        forwards = []
        self.check_envelope_caller(node, ordinal)
        for kw in node.keywords:
            if kw.arg is None and callee == "model_copy":
                self.record(node, "MODEL_COPY_KWARGS_FORBIDDEN", "any ** into model_copy is rejected; update= must be an explicit keyword", callee, ordinal)
                continue
            if kw.arg is None:
                bad = self.check_mapping(kw.value, lam)
                forwards.append({"mapping": ast.unparse(kw.value)[:80], "fixed_form": not bad})
                for rule, d in bad:
                    self.record(node, rule, d, callee, ordinal)
            elif kw.arg == "simulate" and not _literal_ok("simulate", kw.value):
                self.record(node, "SIMULATE_NOT_CONSTANT_NONE", "simulate=" + ast.unparse(kw.value)[:50], callee, ordinal)
            elif kw.arg in SIX and (protected or is_partial or "UNRESOLVED" in names):
                if not self.origin_ok(kw.arg, kw.value):
                    self.record(node, "ORIGIN_VIOLATION", f"{kw.arg}={ast.unparse(kw.value)[:60]} has no trusted origin", callee, ordinal)
            elif (protected or is_partial or "UNRESOLVED" in names) and EXPLICIT_PROHIBITED.match(kw.arg) and not _literal_ok(kw.arg, kw.value):
                self.record(node, "PROHIBITED_KEYWORD_NON_LITERAL", f"{kw.arg}={ast.unparse(kw.value)[:50]}", callee, ordinal)
            elif kw.arg == "update" and callee == "model_copy":
                for rule, d in self.check_mapping(kw.value, None):
                    self.record(node, "MODEL_COPY_UPDATE_NOT_FIXED" if rule == "NONLITERAL_KWARGS" else rule, d, callee, ordinal)
        for a in node.args:
            if isinstance(a, ast.Starred) and (protected or "UNRESOLVED" in names or receives_protected):
                own = lam and isinstance(a.value, ast.Name) and a.value.id in lam
                if not own and not isinstance(a.value, (ast.Tuple, ast.List)):
                    self.record(node, "OPAQUE_POSITIONAL_UNPACK", f"*{ast.unparse(a.value)[:50]} into protected/unresolved/protected-callable-receiving call", callee, ordinal)
        if forwards or real:
            self.examined.append({"file": self.filename, "line": node.lineno, "callee": callee, "protected": real, "forwards": forwards})


def scan_source(source, filename="<src>"):
    a = Analyzer(source, filename).run()
    return a.findings, a.examined


def scan_dir(hub, hub_revision=None):
    """Observation record for NC4-03 v4 (source-level). Keys are the ones expectations v4 reads."""
    files = sorted((pathlib.Path(hub) / "tools" / "mvp_ingress").glob("*.py"))
    findings, pinned, examined, sites = [], [], [], []
    for f in files:
        a = Analyzer(f.read_text(), f.name, hub_revision).run()
        findings += a.findings
        pinned += a.pinned
        examined += a.examined
        sites += a.sites
    have = {(s["file"], s["qualname"], s["callee"], s["ordinal"]) for s in sites}
    used = {p["pinned"] for p in pinned}
    return {"predicate": PREDICATE_ID, "scanned_hub_revision": hub_revision,
            "hub_revision_verified": bool(hub_revision and re.fullmatch(r"[0-9a-f]{40}", hub_revision)),
            "pin_source_revision_mismatch": sorted(k for k, r in PINNED_SITES.items() if r.get("source_revision") != hub_revision),
            "files_scanned": [f.name for f in files],
            "violations": findings, "simulate_violations": [x for x in findings if x["rule"] == "SIMULATE_NOT_CONSTANT_NONE"],
            "client_fed_kwargs_to_protected": [x for x in findings if x["rule"] != "SIMULATE_NOT_CONSTANT_NONE"],
            "required_sites_missing": [list(s) for s in REQUIRED_SITES if s not in have],
            "real_protected_calls_count": len(sites), "real_protected_calls": sites,
            "pinned_sites_used": sorted(used), "pins_unmatched": sorted(k for k in PINNED_SITES if k not in used),
            "pin_records_incomplete": sorted(k for k, r in PINNED_SITES.items() if any(not r.get(f) for f in PIN_FIELDS)
                                             or not re.fullmatch(r"[0-9a-f]{64}", str(r.get("ast_digest", "")))),
            "pin_records": {k: v for k, v in PINNED_SITES.items() if k in used},
            "calls_examined": examined,
            "scope": "source-level static analysis; see _kwflow.py module docstring for limits"}
