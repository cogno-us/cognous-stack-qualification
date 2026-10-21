"""Shared builder for aggregate tests: writes a collected-artifacts directory and runs cmd_aggregate on it (no real components)."""
import argparse
import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path
from xml.sax.saxutils import quoteattr

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import v1_validation as v  # noqa: E402

VID = 'v1-2026-10-16-t'
GOOD_FREEZE = {'status': 'PASS', 'validation_id': VID, 'components': {'alpha': {}}, 'components_expected': ['alpha']}


def junit_xml(cases):
    """cases: (classname, name, kind) with kind passed|failed|skipped."""
    out = ['<?xml version="1.0"?><testsuites><testsuite>']
    for cn, n, kind in cases:
        inner = {'passed': '', 'failed': '<failure message="boom"/>', 'skipped': '<skipped message="s"/>'}[kind]
        out.append(f'<testcase classname={quoteattr(cn)} name={quoteattr(n)}>{inner}</testcase>')
    out.append('</testsuite></testsuites>')
    return ''.join(out)


def job(component, status='PASS', cases=(), os_='ubuntu-latest', python='3.12', dirname=None, extra=None):
    return {'dir': dirname or f'v1v-comp-{component}', 'result': dict({'component': component, 'status': status, 'os': os_, 'python': python,
                                                                        'attempts': [{'outcome': status}]}, **(extra or {})), 'cases': list(cases)}


def aggregate(jobs, requirements=None, freeze=GOOD_FREEZE, plan=None, declared_twin=None, vid=VID, env=None):
    """Run cmd_aggregate; returns (summary dict, td-independent). plan: list of plan include entries (None: no plan record)."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        inp = td / 'in'
        inp.mkdir()
        if freeze is not None:
            (inp / 'v1v-freeze').mkdir()
            (inp / 'v1v-freeze' / 'freeze-verification.json').write_text(json.dumps(freeze))
        if plan is not None:
            (inp / 'v1v-plan').mkdir()
            (inp / 'v1v-plan' / 'plan.json').write_text(json.dumps({'include': plan}))
        for j in jobs:
            d = inp / j['dir']
            d.mkdir()
            (d / 'result.json').write_text(json.dumps(j['result']))
            if j['cases']:
                (d / 'junit-attempt1.xml').write_text(junit_xml(j['cases']))
        req = None
        if requirements is not None:
            req = str(td / 'req.json')
            Path(req).write_text(json.dumps({'requirements': requirements}))
        ns = argparse.Namespace(inputs=str(inp), out=str(td / 'out'), validation_id=vid, requirements=req,
                                declared_twin=declared_twin, declared_set=None, require_committed_twin=False)
        with contextlib.redirect_stdout(io.StringIO()):
            v.cmd_aggregate(ns)
        return json.loads((td / 'out' / 'summary.json').read_text())


def plan_entry(component, group='components_subject', os_='ubuntu-latest', python='3.12', **kw):
    return dict({'component': component, 'group': group, 'os': os_, 'python': python}, **kw)


def selector_row(rid, component, rx, minimum=1, mandatory=True):
    return {'id': rid, 'kind': 'tests', 'mandatory': mandatory, 'selectors': [{'component': component, 're': rx, 'min': minimum}]}
