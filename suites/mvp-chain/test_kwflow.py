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
    assert len(NEG) >= 36 and len(POS) >= 8


@pytest.mark.parametrize("path", NEG, ids=lambda p: p.stem)
def test_negative_fixture_is_rejected(path):
    findings, _ = _kwflow.scan_source(path.read_text(), path.name)
    assert findings, f"{path.name}: client-fed keyword assembly was ACCEPTED"
    assert _expected_rule(path) in {f["rule"] for f in findings}, (path.name, findings)


@pytest.mark.parametrize("path", POS, ids=lambda p: p.stem)
def test_positive_fixture_is_accepted(path):
    findings, _ = _kwflow.scan_source(path.read_text(), path.name)
    assert findings == [], findings


def test_baseline_covers_all_of_ingress_and_is_accepted_only_via_pins():
    obs = _kwflow.scan_dir(BASE)
    assert obs["files_scanned"] == _kwflow.EXPECTED_FILES
    assert obs["violations"] == [] and obs["required_sites_missing"] == [] and obs["pins_unmatched"] == []
    assert obs["real_protected_calls_count"] >= 8
    assert sorted(obs["pinned_sites_used"]) == sorted(_kwflow.PINNED_SITES)


def test_without_pins_the_baseline_fails(monkeypatch):
    monkeypatch.setattr(_kwflow, "PINNED_SITES", {})
    obs = _kwflow.scan_dir(BASE)
    assert {v["line"] for v in obs["violations"]} >= {39, 44, 72}


def test_sqlite_receiver_not_counted_as_protected():
    findings, ex = _kwflow.scan_source("def f(c):\n    c.execute('x')\n")
    assert findings == [] and not [e for e in ex if e["protected"]]


def test_vanished_required_site_is_reported(tmp_path):
    shutil.copytree(BASE / "tools" / "mvp_ingress", tmp_path / "tools" / "mvp_ingress")
    core = tmp_path / "tools" / "mvp_ingress" / "core.py"
    core.write_text(core.read_text().replace("host.executor.provision_claim(", "host.executor.other_claim("))
    assert ["core.py", "IngressCore._run", "provision_claim", 1] in _kwflow.scan_dir(tmp_path)["required_sites_missing"]


EXEC = "res = host.executor.execute(envelope=host.envelope(decision, proposal), claim_id=claim.claim_id, simulate=None)"
MUTANTS = {
    "core: **fields into execute": ("core.py", "claim_id=claim.claim_id, simulate=None)", "claim_id=claim.claim_id, simulate=None, **fields)"),
    "core: client simulate": ("core.py", "claim_id=claim.claim_id, simulate=None)", 'claim_id=claim.claim_id, simulate=fields.get("simulate"))'),
    "core: comprehension over client fields into provision_claim": ("core.py", "provision_claim(proposal=proposal, decision=decision, now=host.now)",
                                                                  "provision_claim(proposal=proposal, decision=decision, now=host.now, **{k: v for k, v in fields.items()})"),
    "core: update() with client fields": ("core.py", EXEC, "kw = {\"claim_id\": claim.claim_id}\n            kw.update(fields)\n            res = host.executor.execute(envelope=host.envelope(decision, proposal), **kw)"),
    "core: functools.partial with client fields": ("core.py", EXEC, "import functools\n            run = functools.partial(host.executor.execute, **fields)\n            res = run(envelope=host.envelope(decision, proposal))"),
    "core: lambda proxy fed by client fields": ("core.py", EXEC, "run = lambda **k: host.executor.execute(**k)\n            res = run(envelope=host.envelope(decision, proposal), **fields)"),
    "core: import alias then client star-args": ("core.py", EXEC, "from engine.x import execute as go\n            res = go(*fields[\"a\"])"),
    "core: helper mutation via alias": ("core.py", EXEC, "kw = {\"claim_id\": claim.claim_id}\n            al = kw\n            al.update(fields)\n            res = host.executor.execute(envelope=host.envelope(decision, proposal), **kw)"),
    "core: helper mutation via poison call": ("core.py", EXEC, "kw = {\"claim_id\": claim.claim_id}\n            poison(kw, fields)\n            res = host.executor.execute(envelope=host.envelope(decision, proposal), **kw)"),
    "core: closure mutation": ("core.py", EXEC, "kw = {\"claim_id\": claim.claim_id}\n            def later():\n                kw.update(fields)\n            later()\n            res = host.executor.execute(envelope=host.envelope(decision, proposal), **kw)"),
    "core: ** into non-protected helper receiving execute": ("core.py", EXEC, "res = run(host.executor.execute, envelope=host.envelope(decision, proposal), **fields)"),
    "core: pool.submit(execute)": ("core.py", EXEC, "res = pool.submit(host.executor.execute, envelope=host.envelope(decision, proposal)).result()"),
    "core: starmap(execute)": ("core.py", EXEC, "res = list(itertools.starmap(host.executor.execute, fields[\"rows\"]))"),
    "core: __call__": ("core.py", EXEC, "res = host.executor.execute.__call__(envelope=host.envelope(decision, proposal), **fields)"),
    "core: client kwargs into decide": ("core.py", "host.workflow.decide(proposal, now=host.now)", "host.workflow.decide(proposal, now=host.now, **fields)"),
    "host: comprehension keys from non-literal iterable": ("synthetic_host.py", "for k in names}", "for k in p.model_dump()}"),
    "host: names list gains simulate": ("synthetic_host.py", "op = ExecutionOperation(", "names.append(\"simulate\")\n        op = ExecutionOperation("),
    "host: model_copy update from client mapping": ("synthetic_host.py", "tra.proposal = lambda *a, **k: original(*a, **k).model_copy(update={\"amount\": APPROVED_AMOUNT})",
                                                    "tra.proposal = lambda *a, **k: original(*a, **k).model_copy(update=a[0])"),
    "host: pinned ExecutionOperation site changed (un-pins)": ("synthetic_host.py", "institution_id=tba.INSTITUTION,", "institution_id=tba.INSTITUTION, **names,"),
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
    assert obs["violations"] or obs["pins_unmatched"], f"mutant ACCEPTED: {label}"
