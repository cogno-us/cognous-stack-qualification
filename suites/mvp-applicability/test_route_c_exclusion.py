"""Route C (Exchange) is EXCLUDED and NOT INVOKED in the MVP candidate: verified, not merely omitted (Architect ruling 5, proposed).

SPDX-License-Identifier: Apache-2.0

AP-01..AP-05 here; AP-06 is the session-end module scan of exchange_exclusion_plugin.py, judged by the gate. These tests assert the
declared exclusion against the candidate identity, the resolved tuple, the pinned ingress source and the real ingress parser. They say
nothing about Exchange's own correctness, and they do not touch the Exchange defect register.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import re
from pathlib import Path

import pytest

EXCHANGE_REPO = "cogno-us/cognous-governed-exchange"


def _banned(mapping):
    return re.compile(mapping["banned_exchange_name_pattern"]), tuple(mapping["banned_exchange_module_roots"])


def test_ap01_mapping_declares_route_c_excluded_and_not_invoked_distinct_from_a_skip(mapping, identity_file):
    route_c = mapping["routes"]["route_c"]
    assert route_c["mvp_status"] == "EXCLUDED and NOT INVOKED"
    assert "NOT APPLICABLE by exclusion" in route_c["applicability"] and "distinct from a skip" in route_c["applicability"]
    assert mapping["routes"]["route_b"]["mvp_status"] == "IN SCOPE and INVOKED"
    assert "unchanged raw history" in route_c["defect_register_note"]
    ap_ids = [v["id"] for v in route_c["verified_by"]]
    assert ap_ids == ["AP-01", "AP-02", "AP-03", "AP-04", "AP-05", "AP-06"]
    identity = json.loads(identity_file.read_text())
    assert not [n for n, c in identity["components"].items() if c["repository"] == EXCHANGE_REPO or "exchange" in n.lower()]
    assert identity["excluded_components"]["exchange"]["repository"] == EXCHANGE_REPO


def test_ap02_resolved_tuple_has_no_exchange_component(pin_file):
    pins = json.loads(pin_file.read_text())["components"]
    assert pins, "empty tuple"
    offenders = [n for n, c in pins.items() if c.get("repository") == EXCHANGE_REPO or "exchange" in n.lower() or "gax" in n.lower()]
    assert offenders == [], offenders


def _string_constants_outside_docstrings(tree):
    doc_nodes = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                doc_nodes.add(id(first.value))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in doc_nodes:
            yield node.lineno, node.value


def scan_source(text: str, name_pattern, module_roots) -> dict:
    tree = ast.parse(text)
    hits = {"imports": [], "dynamic_imports": [], "strings": []}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in module_roots or name_pattern.search(alias.name):
                    hits["imports"].append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.split(".")[0] in module_roots or name_pattern.search(mod) or any(name_pattern.search(a.name) for a in node.names):
                hits["imports"].append((node.lineno, mod))
        elif isinstance(node, ast.Call):
            callee = ast.unparse(node.func)
            if callee in ("__import__", "eval", "exec", "compile") or callee.startswith("importlib"):
                hits["dynamic_imports"].append((node.lineno, callee))
    for line, value in _string_constants_outside_docstrings(tree):
        if name_pattern.search(value):
            hits["strings"].append((line, value[:80]))
    return hits


def test_ap03_pinned_ingress_source_has_no_route_c_entry_point(mapping, hub_ingress_dir):
    pattern, roots = _banned(mapping)
    files = sorted(hub_ingress_dir.glob("*.py"))
    assert {f.name for f in files} >= {"core.py", "proposal.py", "server.py", "client.py", "synthetic_host.py"}, [f.name for f in files]
    problems = {}
    for f in files:
        hits = scan_source(f.read_text(), pattern, roots)
        if any(hits.values()):
            problems[f.name] = hits
    assert problems == {}, problems


def test_ap03_scanner_detects_what_it_claims_to_detect(mapping):
    pattern, roots = _banned(mapping)
    bad = "import experiments.odex_gax_imx_reference.gax_ref\nfrom x import y\nimportlib = None\nz = __import__('q')\nroute = 'exchange gax'\n"
    hits = scan_source(bad, pattern, roots)
    assert hits["imports"] and hits["dynamic_imports"] and hits["strings"]
    clean = '"""docstring may say Exchange"""\nimport json\n\ndef f():\n    """route C is excluded"""\n    return json.dumps({})\n'
    assert not any(scan_source(clean, pattern, roots).values())


def _load_parser(hub_ingress_dir):
    spec = importlib.util.spec_from_file_location("mvp_ingress_proposal_ap04", hub_ingress_dir / "proposal.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ap04_ingress_parser_is_closed_and_refuses_every_route_c_selector(mapping, hub_ingress_dir):
    parser = _load_parser(hub_ingress_dir)
    assert list(parser.MEMBERS) == mapping["expected_ingress_member_vocabulary"], parser.MEMBERS
    refusals = []
    for body in mapping["route_c_probe_bodies"]:
        with pytest.raises(parser.Refusal) as caught:
            parser.parse(json.dumps(body).encode())
        refusals.append(caught.value.code)
    assert refusals == ["UNKNOWN_MEMBER"] * len(mapping["route_c_probe_bodies"]), refusals
    control = {k: v for k, v in mapping["route_c_probe_bodies"][0].items() if k in parser.MEMBERS}
    assert parser.parse(json.dumps(control).encode())["request_id"] == "ap-probe-1"  # the same body without the selector is accepted


def test_ap05_historical_files_are_byte_identical_to_the_recorded_hashes(mapping, repo_root):
    recorded = mapping["historical_files_unchanged"]["files"]
    assert set(recorded) >= {"suites/v1-scenarios/test_scn_d09.py", "process/mvp-chain/expectations.proposed.v3.json"}
    changed = {}
    for rel, digest in recorded.items():
        actual = hashlib.sha256((repo_root / rel).read_bytes()).hexdigest()
        if actual != digest:
            changed[rel] = {"recorded": digest, "actual": actual}
    assert changed == {}, changed
