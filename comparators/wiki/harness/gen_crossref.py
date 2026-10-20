#!/usr/bin/env python3
"""Mechanical listing: for each included Wiki case id, the test files and test function names whose source mentions the id.
Names only; no test body is read into the output and no result is read. Usage: gen_crossref.py <qualification checkout> <commit> <ids.json> <out.json>"""
import ast, json, re, sys
from pathlib import Path
root, commit, ids_path, out = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
ids = json.load(open(ids_path))
res = {i: [] for i in ids}
for f in sorted((root / 'suites/wiki-derived').glob('test_*.py')):
    src = f.read_text(); lines = src.splitlines(); tree = ast.parse(src)
    spans = []
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith('test_'):
            start = min([n.lineno] + [d.lineno for d in n.decorator_list]); spans.append((start, n.end_lineno, n.name))
        elif isinstance(n, ast.ClassDef):
            for m in n.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name.startswith('test_'):
                    start = min([m.lineno] + [d.lineno for d in m.decorator_list]); spans.append((start, m.end_lineno, n.name + '::' + m.name))
    inside = set()
    for a, b, _ in spans: inside.update(range(a, b + 1))
    for cid in ids:
        tests = set(); module = False
        for i, t in enumerate(lines, 1):
            if cid in t:
                hit = [nm for a, b, nm in spans if a <= i <= b]
                if hit: tests.update(hit)
                else: module = True
        if tests or module:
            res[cid].append({'file': 'suites/wiki-derived/' + f.name, 'tests': (['(module-level)'] if module else []) + sorted(tests)})
note = ("Mechanical listing of test names whose source mentions the case id in qualification main %s. Different harness, not scored by this oracle; never added to a pass fraction. "
        "gate_status is filled from the OCS-3 gate report at report time, not here. (module-level) means the id appears outside a test function (a table or docstring); the mapping is confirmed when the report is made." % commit[:8])
json.dump({'note': note, 'source_commit': commit, 'cases': res}, open(out, 'w'), indent=1); open(out, 'a').write('\n')
print({k: sum(len(x['tests']) for x in v) for k, v in res.items()})
