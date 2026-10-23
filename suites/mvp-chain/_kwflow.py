"""NC4-03 v4 source predicate: DATA-FLOW / CALL-BOUNDARY check of keyword forwarding into protected executor and claim APIs.

SPDX-License-Identifier: Apache-2.0

PROPOSED by the builder for Qualification review and freeze (not frozen, not an acceptance, production HOLD unchanged).
SOURCE-LEVEL ONLY: a static AST analysis; it is not an execution observation and says nothing about code outside the scanned files.

Protected property (unchanged from v3): no client-controlled ``simulate``, authority-writer capability, operation-identity override or
arbitrary keyword can reach a protected executor or claim API. v3 approximated this by forbidding every non-literal ``**`` in the
ingress source. v4 judges the CALL BOUNDARY instead: every call whose callee resolves to a protected API is examined, and the mapping
behind each ``**`` is given an abstract value:

  FIXED(keys)  the key set is statically known and every key is a string constant (dict display, comprehension over a literal name
               list, fixed ``.items()`` copy, ``dict(**fixed)``, ``|``, ``.update(fixed)``, constant-key subscript stores, ``{**fixed}``)
  OPAQUE       anything else: a parameter (including a lambda/proxy ``**k``), a call result, an unknown name, a comprehension over a
               non-literal iterable, a non-constant key, ``.update(opaque)``, ``dict(opaque)``, ``{**opaque}``, ``partial(..., **opaque)``

A protected call is REJECTED if: a ``**`` argument is OPAQUE; a FIXED mapping carries a prohibited key; a prohibited keyword is passed
explicitly with a non-literal value (``simulate`` must be exactly the constant None); or ``*args`` unpacks a non-literal sequence.
A FIXED mapping with only non-prohibited keys is ACCEPTED, as is a proxy whose target is not protected. Aliases (``f = obj.execute``),
``functools.partial`` and lambda proxies are resolved to their targets; a ``**`` OPAQUE into a callee that cannot be resolved is rejected.

Limits (recorded, not hidden): intraprocedural and flow-insensitive per scope (all assignments to a name are joined); no import
following; values under non-prohibited fixed keys are not taint-tracked (e.g. a client ``claim_id`` string); a dynamic ``getattr`` name
or ``exec``/``eval`` is treated as an unresolvable callee. Qualification must review these limits.
"""
from __future__ import annotations

import ast
import pathlib
import re

PREDICATE_ID = "nc4-03.v4.dataflow-callboundary"
PROTECTED_CALLEES = frozenset({
    "execute", "execute_claim_atomic", "provision_claim",  # executor / claim APIs named by the architect ruling
    "ExecutionOperation", "ExecutionEnvelope", "OperationIdentityProfile",  # operation-identity / authority-bearing constructors
    "AtomicLocalControlPlaneExecutor", "OperationIdentityAtomicAuthorityEffectDestination", "LocalExecutionPolicy",
})
PROHIBITED_KEY = re.compile(r"^(simulate|operation_id|operation_identity\w*|operation_override\w*|\w*writer\w*|set_(grant|approval|policy|evidence)_\w+|claim_writer\w*)$")
SIMULATE = "simulate"


class _Opaque:
    def __repr__(self):
        return "OPAQUE"


OPAQUE = _Opaque()


_EXPR = object()


class Fixed:
    """Fixed key set. ``vals`` maps key -> literal constant value, or _EXPR when the value is any other expression."""

    def __init__(self, keys, vals=None):
        self.keys = frozenset(keys)
        self.vals = {k: (vals or {}).get(k, _EXPR) for k in self.keys}

    def __repr__(self):
        return f"FIXED{sorted(self.keys)}"


def _const(node):
    return node.value if isinstance(node, ast.Constant) else _EXPR


def _same(a, b):
    return a is b or (a is not _EXPR and b is not _EXPR and type(a) is type(b) and a == b)


def _join(a, b):
    if a is None:
        return b
    if b is None:
        return a
    if isinstance(a, Fixed) and isinstance(b, Fixed):
        vals = {}
        for k in a.keys | b.keys:
            if k in a.vals and k in b.vals:
                vals[k] = a.vals[k] if _same(a.vals[k], b.vals[k]) else _EXPR
            else:
                vals[k] = a.vals.get(k, b.vals.get(k, _EXPR))
        return Fixed(a.keys | b.keys, vals)
    return OPAQUE


def _safe_literal(key, value):
    """A prohibited keyword is tolerated only as a literal constant (simulate: exactly None); anything else may be client-fed."""
    return value is not _EXPR and (value is None if key == "simulate" else True)


def _str_consts(node):
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)) and all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in node.elts):
        return [e.value for e in node.elts]
    return None


class _Scope:
    def __init__(self, parent, params=()):
        self.parent, self.assigns, self.params = parent, {}, set(params)
        self.mut = {}  # name -> list of ("update"/"store", node)

    def lookup_assigns(self, name):
        s = self
        while s is not None:
            if name in s.params:
                return "param"
            if name in s.assigns:
                return s.assigns[name]
            s = s.parent
        return None


class Analyzer:
    def __init__(self, tree, filename):
        self.filename, self.tree = filename, tree
        self.findings, self.examined = [], []
        self.fn_scopes = {}

    # ---- scope construction -------------------------------------------------
    def _collect(self, body_nodes, scope):
        """Record every assignment of a name in this scope (flow-insensitive), without descending into nested function scopes."""
        stack = list(body_nodes)
        while stack:
            n = stack.pop()
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                continue
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    self._bind(t, n.value, scope)
            elif isinstance(n, ast.AnnAssign) and n.value is not None:
                self._bind(n.target, n.value, scope)
            elif isinstance(n, ast.AugAssign):
                self._bind(n.target, ast.BinOp(left=n.target, op=n.op, right=n.value), scope)
            elif isinstance(n, (ast.For, ast.AsyncFor, ast.With, ast.AsyncWith, ast.NamedExpr)):
                for t in ([n.target] if hasattr(n, "target") else [i.optional_vars for i in getattr(n, "items", []) if i.optional_vars]):
                    self._bind(t, None, scope)
            stack.extend(ast.iter_child_nodes(n))
        for n in ast.walk(ast.Module(body=list(body_nodes), type_ignores=[])):
            pass

    def _bind(self, target, value, scope):
        if isinstance(target, ast.Name):
            scope.assigns.setdefault(target.id, []).append(value)
        elif isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
            scope.mut.setdefault(target.value.id, []).append(("store", target))
        elif isinstance(target, (ast.Tuple, ast.List)):
            for e in target.elts:
                self._bind(e, None, scope)
        elif isinstance(target, ast.Attribute):
            pass

    def _scope_mutations(self, body_nodes, scope):
        stack = list(body_nodes)
        while stack:
            n = stack.pop()
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                continue
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) \
                    and n.func.attr in ("update", "setdefault", "append", "extend", "insert", "add", "__setitem__", "__ior__"):
                kind = n.func.attr if n.func.attr in ("update", "setdefault") else "seqmut"
                scope.mut.setdefault(n.func.value.id, []).append((kind, n))
            stack.extend(ast.iter_child_nodes(n))

    # ---- abstract evaluation ------------------------------------------------
    def mapping(self, node, scope, seen=()):
        """Abstract value of an expression used as a ``**`` mapping."""
        if isinstance(node, ast.Dict):
            keys, vals = set(), {}
            for k, v in zip(node.keys, node.values):
                if k is None:  # {**x}
                    m = self.mapping(v, scope, seen)
                    if not isinstance(m, Fixed):
                        return OPAQUE
                    keys |= m.keys
                    vals.update(m.vals)
                elif isinstance(k, ast.Constant) and isinstance(k.value, str):
                    keys.add(k.value)
                    vals[k.value] = _const(v)
                else:
                    return OPAQUE
            return Fixed(keys, vals)
        if isinstance(node, ast.DictComp):
            return self._dictcomp(node, scope, seen)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            a, b = self.mapping(node.left, scope, seen), self.mapping(node.right, scope, seen)
            return Fixed(a.keys | b.keys, {**a.vals, **b.vals}) if isinstance(a, Fixed) and isinstance(b, Fixed) else OPAQUE
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id == "dict":
                keys, vals = set(), {}
                if len(node.args) > 1:
                    return OPAQUE
                if node.args:
                    m = self.mapping(node.args[0], scope, seen)
                    if not isinstance(m, Fixed):
                        return OPAQUE
                    keys |= m.keys
                    vals.update(m.vals)
                for kw in node.keywords:
                    if kw.arg is None:
                        m = self.mapping(kw.value, scope, seen)
                        if not isinstance(m, Fixed):
                            return OPAQUE
                        keys |= m.keys
                        vals.update(m.vals)
                    else:
                        keys.add(kw.arg)
                        vals[kw.arg] = _const(kw.value)
                return Fixed(keys, vals)
            if isinstance(f, ast.Attribute) and f.attr == "copy" and not node.args:
                return self.mapping(f.value, scope, seen)
            return OPAQUE
        if isinstance(node, ast.Name):
            if node.id in seen:
                return None  # cyclic join neutral element
            res = scope.lookup_assigns(node.id)
            if res is None or res == "param":
                return OPAQUE
            sc, s = None, scope
            while s is not None and node.id not in s.assigns and node.id not in s.params:
                s = s.parent
            acc = None
            for v in res:
                if v is None:
                    return OPAQUE
                acc = _join(acc, self.mapping(v, s, seen + (node.id,)))
                if acc is OPAQUE:
                    return OPAQUE
            for kind, mnode in (s.mut.get(node.id, []) if s else []):
                if kind == "store":
                    sl = mnode.slice
                    if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                        acc = _join(acc, Fixed({sl.value}, {sl.value: _EXPR}))
                    else:
                        return OPAQUE
                elif kind == "seqmut":
                    return OPAQUE  # in-place mutation by a method that is not modelled for a mapping
                elif kind == "update":
                    keys, vals = set(), {}
                    for a in mnode.args:
                        m = self.mapping(a, scope, seen + (node.id,))
                        if not isinstance(m, Fixed):
                            return OPAQUE
                        keys |= m.keys
                        vals.update(m.vals)
                    for kw in mnode.keywords:
                        if kw.arg is None:
                            m = self.mapping(kw.value, scope, seen + (node.id,))
                            if not isinstance(m, Fixed):
                                return OPAQUE
                            keys |= m.keys
                            vals.update(m.vals)
                        else:
                            keys.add(kw.arg)
                            vals[kw.arg] = _const(kw.value)
                    acc = _join(acc, Fixed(keys, vals))
                else:  # setdefault(k, v)
                    a0 = mnode.args[0] if mnode.args else None
                    if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
                        acc = _join(acc, Fixed({a0.value}, {a0.value: _EXPR}))
                    else:
                        return OPAQUE
            return acc if acc is not None else OPAQUE
        return OPAQUE

    def _seq_keys(self, node, scope, seen=()):
        """String constants of a literal list/tuple/set, resolved through names."""
        c = _str_consts(node)
        if c is not None:
            return c
        if isinstance(node, ast.Name) and node.id not in seen:
            res = scope.lookup_assigns(node.id)
            if res is None or res == "param" or len(res) != 1 or res[0] is None:
                return None
            s = scope
            while s is not None and node.id not in s.assigns:
                s = s.parent
            if s is not None and s.mut.get(node.id):
                return None
            return self._seq_keys(res[0], s, seen + (node.id,))
        return None

    def _dictcomp(self, node, scope, seen):
        if len(node.generators) != 1 or node.generators[0].is_async:
            return OPAQUE
        g = node.generators[0]
        inner = _Scope(scope)
        key = node.key
        if isinstance(g.target, ast.Name) and isinstance(key, ast.Name) and key.id == g.target.id:
            consts = self._seq_keys(g.iter, scope)
            if consts is not None:
                return Fixed(consts)
        if isinstance(g.target, ast.Tuple) and len(g.target.elts) == 2 and isinstance(g.target.elts[0], ast.Name) \
                and isinstance(key, ast.Name) and key.id == g.target.elts[0].id and isinstance(g.iter, ast.Call) \
                and isinstance(g.iter.func, ast.Attribute) and g.iter.func.attr == "items" and not g.iter.args:
            return self.mapping(g.iter.func.value, scope, seen)
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            return Fixed({key.value})
        return OPAQUE

    # ---- callee resolution --------------------------------------------------
    def _name_of(self, func):
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            return func.attr
        return None

    def resolve(self, func, scope, depth=0):
        """Return (callee_name or None if unresolvable, extra_kwargs list[(kind,node)], proxy_node or None)."""
        if depth > 6:
            return None, [], None
        if isinstance(func, ast.Attribute):
            return func.attr, [], None
        if isinstance(func, ast.Call) and isinstance(func.func, ast.Name) and func.func.id == "getattr" and len(func.args) >= 2:
            a = func.args[1]
            return (a.value, [], None) if isinstance(a, ast.Constant) and isinstance(a.value, str) else (None, [], None)
        if isinstance(func, ast.Name):
            res = scope.lookup_assigns(func.id)
            if res is None or res == "param":
                return func.id, [], None  # imported / global name: judged by its own name
            if len(res) == 1 and res[0] is not None:
                v = res[0]
                if isinstance(v, ast.Lambda):
                    return "<lambda>", [], v
                if isinstance(v, (ast.Name, ast.Attribute)):
                    return self.resolve(v, scope, depth + 1)
                if isinstance(v, ast.Call) and self._name_of(v.func) == "partial" and v.args:
                    t, ex, px = self.resolve(v.args[0], scope, depth + 1)
                    return t, ex + [("partial", v)], px
                if isinstance(v, ast.Call):
                    return self.resolve(v.func, scope, depth + 1) if self._name_of(v.func) == "getattr" else (None, [], None)
            return (None, [], None)
        return None, [], None

    # ---- the check ----------------------------------------------------------
    def add(self, node, rule, detail, callee):
        self.findings.append({"file": self.filename, "line": node.lineno, "rule": rule, "callee": callee, "detail": detail,
                              "source": ast.unparse(node)[:160]})

    def check_call(self, node, scope):
        callee, extras, proxy = self.resolve(node.func, scope)
        is_partial = self._name_of(node.func) == "partial" and node.args
        if is_partial:  # partial(target, ...): examine the bound arguments against the target
            callee, _, _ = self.resolve(node.args[0], scope)
            args, kws = node.args[1:], node.keywords
        else:
            args, kws = node.args, node.keywords
            for kind, pnode in extras:  # calling a partial variable: the bound arguments plus this call's own
                args = list(pnode.args[1:]) + list(args)
                kws = list(pnode.keywords) + list(kws)
        protected = callee in PROTECTED_CALLEES
        unresolved = callee is None
        has_dstar = any(k.arg is None for k in kws) or any(isinstance(a, ast.Starred) for a in args)
        if not (protected or (unresolved and has_dstar) or any(k.arg and PROHIBITED_KEY.match(k.arg) for k in kws)):
            if has_dstar:  # transparency: record non-protected forwarding (e.g. a proxy to a fixture) without judging it
                self.examined.append({"file": self.filename, "line": node.lineno, "callee": callee or "<unresolved>", "protected": False,
                                      "forwards": [{"mapping": ast.unparse(k.value)[:80], "abstract": repr(self.mapping(k.value, scope))}
                                                   for k in kws if k.arg is None]})
            return
        rec = {"file": self.filename, "line": node.lineno, "callee": callee or "<unresolved>", "protected": protected}
        forwards = []
        for a in args:
            if isinstance(a, ast.Starred):
                c = self._seq_keys(a.value, scope)
                if (protected or unresolved) and c is None and not isinstance(a.value, (ast.Tuple, ast.List)):
                    self.add(node, "OPAQUE_POSITIONAL_UNPACK", f"*{ast.unparse(a.value)[:60]} is not a literal sequence", rec["callee"])
        for kw in kws:
            if kw.arg is None:
                m = self.mapping(kw.value, scope)
                forwards.append({"mapping": ast.unparse(kw.value)[:80], "abstract": repr(m)})
                if protected or unresolved:
                    if not isinstance(m, Fixed):
                        self.add(node, "OPAQUE_KWARGS_TO_PROTECTED" if protected else "OPAQUE_KWARGS_TO_UNRESOLVED",
                                 f"**{ast.unparse(kw.value)[:60]} is not a statically fixed key set", rec["callee"])
                    else:
                        bad = sorted(k for k in m.keys if PROHIBITED_KEY.match(k) and not _safe_literal(k, m.vals[k]))
                        if bad:
                            self.add(node, "PROHIBITED_KEY_IN_FIXED_MAPPING", f"fixed mapping carries prohibited key(s) {bad}", rec["callee"])
            elif PROHIBITED_KEY.match(kw.arg):
                ok = isinstance(kw.value, ast.Constant) and (kw.value.value is None if kw.arg == SIMULATE else True)
                if kw.arg == SIMULATE and not ok:
                    self.add(node, "SIMULATE_NOT_CONSTANT_NONE", f"simulate={ast.unparse(kw.value)[:60]}", rec["callee"])
                elif kw.arg != SIMULATE and not ok and (protected or unresolved):
                    self.add(node, "PROHIBITED_KEYWORD_NON_LITERAL", f"{kw.arg}={ast.unparse(kw.value)[:60]}", rec["callee"])
        rec["forwards"] = forwards
        if protected or forwards:
            self.examined.append(rec)

    def run(self):
        mod = _Scope(None)
        self._collect(self.tree.body, mod)
        self._scope_mutations(self.tree.body, mod)
        self._walk(self.tree.body, mod)
        return self

    def _walk(self, nodes, scope):
        for n in nodes:
            self._visit(n, scope)

    def _visit(self, n, scope):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            a = n.args
            params = [x.arg for x in a.posonlyargs + a.args + a.kwonlyargs] + ([a.vararg.arg] if a.vararg else []) + ([a.kwarg.arg] if a.kwarg else [])
            inner = _Scope(scope, params)
            body = n.body if isinstance(n.body, list) else [n.body]
            self._collect(body, inner)
            self._scope_mutations(body, inner)
            for d in (a.defaults + a.kw_defaults):
                if d is not None:
                    self._visit(d, scope)
            self._walk(body, inner)
            return
        if isinstance(n, ast.ClassDef):
            inner = _Scope(scope)
            self._collect(n.body, inner)
            self._scope_mutations(n.body, inner)
            self._walk(n.body, inner)
            return
        if isinstance(n, ast.Call):
            self.check_call(n, scope)
        for c in ast.iter_child_nodes(n):
            self._visit(c, scope)


def scan_source(source, filename="<src>"):
    a = Analyzer(ast.parse(source), filename).run()
    return a.findings, a.examined


def scan_dir(hub):
    """Observation record for NC4-03 v4 (source-level). Keys are the ones expectations v4 reads."""
    files = sorted((pathlib.Path(hub) / "tools" / "mvp_ingress").glob("*.py"))
    findings, examined = [], []
    for f in files:
        fi, ex = scan_source(f.read_text(), f.name)
        findings += fi
        examined += ex
    sim = [x for x in findings if x["rule"] == "SIMULATE_NOT_CONSTANT_NONE"]
    return {"predicate": PREDICATE_ID, "files_scanned": [f.name for f in files],
            "protected_callees": sorted(PROTECTED_CALLEES), "calls_examined": examined,
            "violations": findings, "client_fed_kwargs_to_protected": [x for x in findings if x["rule"] != "SIMULATE_NOT_CONSTANT_NONE"],
            "simulate_violations": sim, "protected_calls_examined_count": sum(1 for e in examined if e["protected"]),
            "scope": "source-level static analysis; see _kwflow.py module docstring for limits"}
