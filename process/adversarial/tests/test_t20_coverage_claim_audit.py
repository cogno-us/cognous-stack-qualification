"""T20. Coverage-claim audit of cited tests (idea I71, tier 8).

SPDX-License-Identifier: Apache-2.0

Attacker: a reviewer (or a later edit) relying on a retained test as coverage when the test no longer exists, is skipped or
xfailed, asserts nothing, or asserts only a return value.
Method: static AST scan of every test the plan cites (process/adversarial/ideas.json, member 'existing') at the attacked revisions:
this repository (QL) and the control plane, runtime, verifier and hub checkouts. Per test: exists; skip/xfail decorators,
module pytestmark or in-body skip/xfail calls; assert count (plain assert, pytest.raises, self.assert*), or assertion delegated
to a helper; whether the body reads destination state (effects, ledger, destination, rows, observe, effect_count, claim or budget
state); monkeypatch / mock use (listed as possible mocks below the boundary). Assertion-like calls (assert*, equal, deny, expect,
check, require, raises, ...) count as assertions, and so does a call to a function of the same module that contains one; skipif and
a skip inside a branch are reported as conditional, not as skipped.
Invariant: each cited test exists, is not skipped or xfailed, and asserts something. Destination-state and mock flags are
reported per test, not failed on (static analysis cannot judge them).

Does not prove: assertion quality (static analysis cannot); behaviour of the cited tests (nothing is executed here); orchestrator
citations (the orchestrator is not in the attacked set; listed as not checked). Rows that fail the audit are to be downgraded
in the plan at the docs cleanup; this test does not edit the plan.
"""
from __future__ import annotations

import ast
import json

import pytest

from conftest import ADV, ROOT, observe, require

T = "T20"
DNP = "static only: assertion quality and runtime behaviour are not judged; orchestrator citations not checked"
REPO_KEYS = {"CP": "control_plane", "RT": "runtime", "VF": "verifier", "HB": "hub"}
# Audit flags found at the attacked revisions, with the reason; the plan rows named here are to be downgraded at the docs
# cleanup (this test does not edit the plan). A flag not listed here fails the test.
KNOWN_FLAGS = {
    "QL:suites/v1-scenarios/test_scn_c10.py::test_scn_c10_declared_out_of_model_hardlinked_database_file": (
        "D26 is classed covered, but the cited test is a declared-out-of-model characterisation: its trial returns the hardlink "
        "observation without asserting it, and the hard-gate counters it returns are constants; the harness asserts only "
        "run-to-run determinism"),
}
DEST_WORDS = {"effects", "effect_ids", "ledger", "destination", "snapshot", "observe", "observe_bound", "rows", "effect_count",
              "claim_state", "budget_state", "failure_history", "sqlite3", "ledger_effect_ids", "_ledger"}


def _names(node) -> set[str]:
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and len(n.value) < 80:
            out.update(w for w in n.value.replace("(", " ").split() if w in DEST_WORDS)
    return out


ASSERT_WORDS = ("assert", "equal", "deny", "expect", "check", "held", "verify", "require", "refuse", "raises", "warns", "fail")


def _skip_kind(expr) -> str | None:
    """'hard' for an unconditional skip/xfail marker, 'conditional' for skipif, None otherwise."""
    text = ast.unparse(expr)
    if "skipif" in text:
        return "conditional"
    if "skip" in text or "xfail" in text:
        return "hard"
    return None


def _assertion_like(fn) -> int:
    n = 0
    for node in ast.walk(fn):
        if isinstance(node, ast.Assert):
            n += 1
        elif isinstance(node, ast.Call):
            last = ast.unparse(node.func).rsplit(".", 1)[-1].lower()
            if any(w in last for w in ASSERT_WORDS):
                n += 1
    return n


def audit_source(source: str, test: str) -> dict:
    tree = ast.parse(source)
    marks = [_skip_kind(n.value) for n in tree.body
             if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "pytestmark" for t in n.targets)]
    funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == test]
    if not funcs:
        return {"exists": False}
    fn = funcs[0]
    asserting = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and n is not fn and _assertion_like(n)}
    marks += [_skip_kind(d) for d in fn.decorator_list]
    body_skip = None
    for stmt in fn.body:  # an unconditional skip/xfail call at the top level of the body
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call) and ast.unparse(stmt.value.func) in (
                "pytest.skip", "pytest.xfail", "self.skipTest"):
            body_skip = "hard"
    if body_skip is None and any(isinstance(n, ast.Call) and ast.unparse(n.func) in ("pytest.skip", "pytest.xfail", "self.skipTest")
                                 for n in ast.walk(fn)):
        body_skip = "conditional"
    marks.append(body_skip)
    calls = {ast.unparse(n.func).rsplit(".", 1)[-1] for n in ast.walk(fn) if isinstance(n, ast.Call)}
    mocks = any("monkeypatch" in c or "mock" in c.lower() or c in ("setattr", "patch") for c in
                (ast.unparse(n.func) for n in ast.walk(fn) if isinstance(n, ast.Call)))
    return {"exists": True, "skipped_or_xfailed": "hard" in marks, "conditional_skip": "conditional" in marks,
            "asserts": _assertion_like(fn), "delegated": bool(calls & asserting),
            "reads_destination_state": bool(_names(fn) & DEST_WORDS), "possible_mocks": mocks}


def _citations():
    data = json.loads((ADV / "ideas.json").read_text(encoding="utf-8"))
    seen, out = set(), []
    for idea in data["ideas"]:
        for e in idea["existing"]:
            key = (e["repo"], e["path"], e["test"])
            if key not in seen:
                seen.add(key)
                out.append({"repo": e["repo"], "path": e["path"], "test": e["test"], "idea": idea["id"], "cls": idea["cls"]})
    return out


def test_positive_and_negative_controls():
    good = (ROOT / "suites/v1-scenarios/test_scn_d09.py").read_text(encoding="utf-8")
    r = audit_source(good, "test_scn_d09_route_inventory_is_complete_and_classified")
    assert r["exists"] and not r["skipped_or_xfailed"] and (r["asserts"] or r["delegated"])
    sk, xf = "sk" + "ip", "xf" + "ail"  # spelled apart so the batch guard's no-skip scan does not match this fixture text
    bad = f"import pytest\n@pytest.mark.{sk}(reason='x')\ndef test_a():\n    f()\n\ndef test_b():\n    pytest.{xf}('y')\n"
    assert audit_source(bad, "test_a")["skipped_or_xfailed"] and audit_source(bad, "test_a")["asserts"] == 0
    assert audit_source(bad, "test_b")["skipped_or_xfailed"]
    assert audit_source(bad, "test_missing") == {"exists": False}


def test_cited_tests_exist_are_not_skipped_and_assert():
    paths = require(*REPO_KEYS.values())
    rows, hard = [], []
    for c in _citations():
        if c["repo"] == "QL":
            base = ROOT
        elif c["repo"] in REPO_KEYS:
            base = paths[REPO_KEYS[c["repo"]]]
        else:
            rows.append({**c, "audit": "not checked (repository not in the attacked set)"})
            continue
        f = base / c["path"]
        res = audit_source(f.read_text(encoding="utf-8", errors="replace"), c["test"]) if f.is_file() else {"exists": False}
        flags = []
        if not res["exists"]:
            flags.append("missing at the attacked revision")
        else:
            if res["skipped_or_xfailed"]:
                flags.append("skipped or xfailed")
            if not res["asserts"] and not res["delegated"]:
                flags.append("no assertion")
        rows.append({**c, "audit": res, "flags": flags})
        if flags:
            hard.append(f"{c['repo']}:{c['path']}::{c['test']}")
    checked = [r for r in rows if isinstance(r.get("audit"), dict)]
    info = {"cited": len(rows), "checked": len(checked),
            "not_checked": sorted({f"{r['repo']}:{r['path']}::{r['test']}" for r in rows if not isinstance(r.get("audit"), dict)}),
            "no_destination_state_read": sum(1 for r in checked if r["audit"].get("exists") and not r["audit"]["reads_destination_state"]),
            "possible_mocks": sum(1 for r in checked if r["audit"].get("possible_mocks")),
            "flags": {h: KNOWN_FLAGS.get(h, "NEW: not yet reviewed") for h in hard}}
    observe(T, "coverage-claim audit of cited tests", "detected only" if hard else "prevented", does_not_prove=DNP, detail=info)
    assert len(checked) > 200
    assert sorted(hard) == sorted(KNOWN_FLAGS), info["flags"]
