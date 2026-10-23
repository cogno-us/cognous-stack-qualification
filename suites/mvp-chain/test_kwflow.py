"""Self-tests of the NC4-03 v4 data-flow / call-boundary predicate (_kwflow.py): negative and positive fixtures plus a mutation check.

SPDX-License-Identifier: Apache-2.0

Fixtures are source text only; they are parsed, never imported or executed. Every negative fixture assembles ``**kwargs`` indirectly and
carries prohibited client input toward a protected API: each must be REJECTED with the declared rule. Every positive fixture is fixed
trusted forwarding and must be ACCEPTED. The mutation check injects a client-fed ``**`` into a copy of the pinned ingress source and
requires the predicate to fail, and requires the unmutated copy to pass. PROPOSED; Qualification owns and freezes the oracle.
"""
import pathlib
import re
import shutil

import pytest

import _kwflow

FIX = pathlib.Path(__file__).parent / "kwflow_fixtures"
NEG = sorted((FIX / "negative").glob("*.py"))
POS = sorted((FIX / "positive").glob("*.py"))
BASE = FIX / "baseline"


@pytest.fixture(autouse=True)
def _components_present():
    """Pure source analysis: overrides the suite's component-wiring autouse fixture (no component checkout is needed or touched)."""


def _expected_rule(path):
    return re.match(r"# EXPECT-RULE: (\w+)", path.read_text()).group(1)


def test_fixture_inventory():
    assert len(NEG) >= 16 and len(POS) >= 8


@pytest.mark.parametrize("path", NEG, ids=lambda p: p.stem)
def test_negative_fixture_is_rejected(path):
    findings, _ = _kwflow.scan_source(path.read_text(), path.name)
    assert findings, f"{path.name}: client-fed keyword assembly was ACCEPTED"
    assert _expected_rule(path) in {f["rule"] for f in findings}, (path.name, findings)


@pytest.mark.parametrize("path", POS, ids=lambda p: p.stem)
def test_positive_fixture_is_accepted(path):
    findings, _ = _kwflow.scan_source(path.read_text(), path.name)
    assert findings == [], findings


def test_baseline_ingress_snapshot_is_accepted_and_examined():
    obs = _kwflow.scan_dir(BASE)
    assert obs["violations"] == []
    assert obs["protected_calls_examined_count"] >= 10
    # the two forwardings the v3 predicate rejected are present, observed and judged fixed/non-protected
    fwd = [(e["file"], e["line"]) for e in obs["calls_examined"] if e["forwards"]]
    assert ("synthetic_host.py", 39) in fwd and ("synthetic_host.py", 72) in fwd


MUTANTS = {
    "core: **fields into execute": ("core.py", "claim_id=claim.claim_id, simulate=None)", "claim_id=claim.claim_id, simulate=None, **fields)"),
    "core: client simulate": ("core.py", "claim_id=claim.claim_id, simulate=None)", 'claim_id=claim.claim_id, simulate=fields.get("simulate"))'),
    "core: comprehension over client fields into provision_claim": ("core.py", "provision_claim(proposal=proposal, decision=decision, now=host.now)",
                                                                  "provision_claim(proposal=proposal, decision=decision, now=host.now, **{k: v for k, v in fields.items()})"),
    "core: update() with client fields then execute": ("core.py", "res = host.executor.execute(envelope=host.envelope(decision, proposal), claim_id=claim.claim_id, simulate=None)",
                                                       "kw = {\"claim_id\": claim.claim_id}\n            kw.update(fields)\n            res = host.executor.execute(envelope=host.envelope(decision, proposal), **kw)"),
    "core: functools.partial with client fields": ("core.py", "res = host.executor.execute(envelope=host.envelope(decision, proposal), claim_id=claim.claim_id, simulate=None)",
                                                   "import functools\n            run = functools.partial(host.executor.execute, **fields)\n            res = run(envelope=host.envelope(decision, proposal))"),
    "core: lambda proxy fed by client fields": ("core.py", "res = host.executor.execute(envelope=host.envelope(decision, proposal), claim_id=claim.claim_id, simulate=None)",
                                                "run = lambda **k: host.executor.execute(**k)\n            res = run(envelope=host.envelope(decision, proposal), **fields)"),
    "host: op construction keys from non-literal iterable": ("synthetic_host.py", "for k in names}", "for k in p.model_dump()}"),
    "host: names list gains simulate": ("synthetic_host.py", "op = ExecutionOperation(", "names.append(\"simulate\")\n        op = ExecutionOperation("),
}


@pytest.mark.parametrize("label", sorted(MUTANTS))
def test_mutant_ingress_fails(label, tmp_path):
    dst = tmp_path / "tools" / "mvp_ingress"
    shutil.copytree(BASE / "tools" / "mvp_ingress", dst)
    fname, old, new = MUTANTS[label]
    text = (dst / fname).read_text()
    assert text.count(old) == 1, "mutation anchor not found exactly once"
    (dst / fname).write_text(text.replace(old, new))
    obs = _kwflow.scan_dir(tmp_path)
    assert obs["violations"], f"mutant ACCEPTED: {label}"
