"""Self-tests of the NC4-03 v4 data-flow / call-boundary predicate (_kwflow.py): negative and positive fixtures plus a mutation check.

SPDX-License-Identifier: Apache-2.0

Fixtures are source text only; they are parsed, never imported or executed. Every negative fixture assembles ``**kwargs`` indirectly and
carries prohibited client input toward a protected API: each must be REJECTED with the declared rule. Every positive fixture is fixed
trusted forwarding and must be ACCEPTED. The mutation check injects a client-fed ``**`` into a copy of the pinned ingress source and
requires the predicate to fail, and requires the unmutated copy to pass. PROPOSED; Qualification owns and freezes the oracle.
"""
import hashlib
import json
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
    assert len(NEG) >= 71 and len(POS) >= 7


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
    assert obs["pin_records_incomplete"] == []
    for rec in obs["pin_records"].values():
        assert all(rec[f] for f in _kwflow.PIN_FIELDS) and rec["originating_hub_commit"] == _kwflow.HUB_REVISION


@pytest.mark.parametrize("field", _kwflow.PIN_FIELDS)
def test_pin_record_missing_field_fails(monkeypatch, field):
    pins = {k: {f: v for f, v in r.items() if f != field} for k, r in _kwflow.PINNED_SITES.items()}
    monkeypatch.setattr(_kwflow, "PINNED_SITES", pins)
    obs = _kwflow.scan_dir(BASE)
    assert obs["pin_records_incomplete"] and obs["violations"]


@pytest.mark.parametrize("rev", [None, "0" * 40, "43c526eb", "7b38ae62" + "0" * 32])
def test_pins_are_content_addressed_unrelated_hub_commit_still_passes(rev):
    obs = _kwflow.scan_dir(BASE, rev)  # hub revision is informational only
    assert obs["violations"] == [] and obs["pins_unmatched"] == [] and obs["pin_records_incomplete"] == []
    assert obs["ingress_tree_sha256"] in obs["reviewed_ingress_tree_sha256"]


def test_tree_digest_serialization_is_the_documented_one():
    files = sorted((BASE / "tools" / "mvp_ingress").glob("*.py"), key=lambda p: p.name.encode())
    manifest = "".join(f"{p.name}\0{hashlib.sha256(p.read_bytes()).hexdigest()}\n" for p in files).encode()
    assert _kwflow.scan_dir(BASE)["ingress_tree_sha256"] == hashlib.sha256(manifest).hexdigest()
    assert [n for n, _ in _kwflow.scan_dir(BASE)["ingress_tree_manifest"]] == _kwflow.EXPECTED_FILES


def test_history_per_file_hashes_are_consistent_with_the_tree_digest():
    hist = json.loads((pathlib.Path(__file__).resolve().parents[2] / "process" / "mvp-chain" / "history" / "nc4-03-v3-predicate-result.json").read_text())
    per_file = hist["scanned_files_sha256"]
    assert sorted(per_file) == _kwflow.EXPECTED_FILES
    digest = hashlib.sha256("".join(f"{n}\0{per_file[n]}\n" for n in sorted(per_file, key=lambda x: x.encode())).encode()).hexdigest()
    assert digest == hist["ingress_tree_sha256"] == _kwflow.scan_dir(BASE)["ingress_tree_sha256"]
    for p in (BASE / "tools" / "mvp_ingress").glob("*.py"):
        assert hashlib.sha256(p.read_bytes()).hexdigest() == per_file[p.name]


@pytest.mark.parametrize("fname", _kwflow.EXPECTED_FILES)
def test_any_byte_change_including_a_comment_fails_closed(tmp_path, fname):
    shutil.copytree(BASE / "tools" / "mvp_ingress", tmp_path / "tools" / "mvp_ingress")
    f = tmp_path / "tools" / "mvp_ingress" / fname
    f.write_text(f.read_text() + "\n# comment-only edit\n")
    base, obs = _kwflow.scan_dir(BASE), _kwflow.scan_dir(tmp_path)
    assert obs["ingress_tree_sha256"] != base["ingress_tree_sha256"]
    assert obs["ingress_tree_sha256"] not in obs["reviewed_ingress_tree_sha256"]
    assert obs["pins_unmatched"] and obs["violations"]
    # the AST digests of the pinned sites are unchanged: only the tree digest un-pins (fail closed until a new pin record is made)
    assert {v["ast_digest"] for v in obs["violations"] if v["site"] in _kwflow.PINNED_SITES} <= {r["ast_digest"] for r in _kwflow.PINNED_SITES.values()}


def _host_copy(tmp_path, edit):
    shutil.copytree(BASE / "tools" / "mvp_ingress", tmp_path / "tools" / "mvp_ingress")
    f = tmp_path / "tools" / "mvp_ingress" / "synthetic_host.py"
    f.write_text(edit(f.read_text()))
    return _kwflow.scan_dir(tmp_path)


def test_semantic_ast_change_unpins(tmp_path):
    obs = _host_copy(tmp_path, lambda t: t.replace('"payload", "payload_commitment", "amount", "unit", "effects"', '"payload", "payload_commitment", "unit", "amount", "effects"'))
    assert obs["pins_unmatched"] and obs["violations"]


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
    "host: model_copy ** update from client": ("synthetic_host.py", "return self.p0.model_copy(update={", "return self.p0.model_copy(**{\"fields\": fields}, update={"),
    "host: build_proposal update gains client manifest_digest": ("synthetic_host.py", '"amount": float(fields["amount"]),', '"amount": float(fields["amount"]), "manifest_digest": fields["d"],'),
    "host: build_proposal update gains client effects": ("synthetic_host.py", '"amount": float(fields["amount"]),', '"amount": float(fields["amount"]), "effects": fields["e"],'),
    "core: explicit client action_id into execute": ("core.py", "claim_id=claim.claim_id, simulate=None)", 'claim_id=claim.claim_id, simulate=None, action_id=fields["a"])'),
    "core: display with client requested_permissions": ("core.py", "claim_id=claim.claim_id, simulate=None)", 'claim_id=claim.claim_id, simulate=None, **{"requested_permissions": fields["p"]})'),
    "core: CLIENT claim_id reaches execute (regression target)": ("core.py", "claim_id=claim.claim_id, simulate=None)", 'claim_id=fields["claim_id"], simulate=None)', "ORIGIN_VIOLATION"),
    "core: claim_id from client display": ("core.py", "claim_id=claim.claim_id, simulate=None)", 'simulate=None, **{"claim_id": fields["claim_id"]})', "ORIGIN_VIOLATION"),
    "core: claim name reassigned from client fields": ("core.py", "res = host.executor.execute(", "claim = fields\n            res = host.executor.execute(", "ORIGIN_VIOLATION"),
    "host: client grant_id": ("synthetic_host.py", "grant_id=d.binding.grant_id", 'grant_id=p.payload["g"]', "ORIGIN_VIOLATION"),
    "host: client grant_revision": ("synthetic_host.py", "grant_revision=d.binding.grant_revision", 'grant_revision=p.payload["r"]', "ORIGIN_VIOLATION"),
    "host: client effective_max_effects": ("synthetic_host.py", "effective_max_effects=d.binding.effective_max_effects", 'effective_max_effects=p.payload["m"]', "ORIGIN_VIOLATION"),
    "host: client authority_context_id": ("synthetic_host.py", "authority_context_id=p.authority_context_ref", 'authority_context_id=p.payload["c"]', "ORIGIN_VIOLATION"),
    "host: client requested_permissions": ("synthetic_host.py", "requested_permissions=tuple(p.requested_permissions)", 'requested_permissions=tuple(p.payload["perm"])', "ORIGIN_VIOLATION"),
    "core: envelope called with client-derived arguments": ("core.py", "host.envelope(decision, proposal)", 'host.envelope(fields, proposal)', "ORIGIN_CALLER_UNTRUSTED"),
    "core: F1 claim bound in another function, used as parameter": ("core.py", "class IngressCore:", "def _a(host):\n    claim = host.executor.provision_claim(1)\n\n\ndef _h(host, claim):\n    return host.executor.execute(claim_id=claim.claim_id)\n\n\nclass IngressCore:", "ORIGIN_VIOLATION"),
    "core: F1 claim rebound from client in another scope": ("core.py", "class IngressCore:", "def _h(host, fields):\n    claim = fields\n    return claim\n\n\nclass IngressCore:", "ORIGIN_VIOLATION"),
    "core: F2 module-level provision_claim shadow": ("core.py", "class IngressCore:", "def provision_claim(x):\n    return x\n\n\nclass IngressCore:", "PRODUCER_SHADOWED"),
    "core: F2 bare-name producer": ("core.py", "host.executor.provision_claim(proposal=proposal", "provision_claim(proposal=proposal", "ORIGIN_VIOLATION"),
    "core: F2 producer on wrong receiver": ("core.py", "host.executor.provision_claim(proposal=proposal", "host.workflow.provision_claim(proposal=proposal", "ORIGIN_VIOLATION"),
    "core: F2 decide shadowed by import": ("core.py", "class IngressCore:", "from helpers import decide\n\n\nclass IngressCore:", "PRODUCER_SHADOWED"),
    "core: F3 envelope alias": ("core.py", EXEC, "e = host.envelope\n            res = host.executor.execute(envelope=e(decision, proposal), claim_id=claim.claim_id, simulate=None)", "PROTECTED_CALLABLE_ESCAPES"),
    "core: F3 envelope via getattr": ("core.py", EXEC, "res = host.executor.execute(envelope=getattr(host, \"envelope\")(decision, proposal), claim_id=claim.claim_id, simulate=None)", "PROTECTED_CALLABLE_ESCAPES"),
    "core: N5 host rebound from client fields": ("core.py", "        host = self._host\n        # Stage 1", "        host = fields\n        # Stage 1", "ORIGIN_VIOLATION"),
    "core: N5 host as a parameter": ("core.py", "def _run(self, fields, request_id) -> dict:\n        host = self._host", "def _run(self, fields, request_id, host) -> dict:", "ORIGIN_VIOLATION"),
    "host: pinned ExecutionOperation site changed (un-pins)": ("synthetic_host.py", "institution_id=tba.INSTITUTION,", "institution_id=tba.INSTITUTION, **names,"),
}


@pytest.mark.parametrize("label", sorted(MUTANTS))
def test_mutant_ingress_fails(label, tmp_path):
    dst = tmp_path / "tools" / "mvp_ingress"
    shutil.copytree(BASE / "tools" / "mvp_ingress", dst)
    fname, old, new, *rule = MUTANTS[label]
    text = (dst / fname).read_text()
    assert text.count(old) == 1, "mutation anchor not found exactly once"
    (dst / fname).write_text(text.replace(old, new))
    obs = _kwflow.scan_dir(tmp_path)
    assert obs["violations"] or obs["pins_unmatched"], f"mutant ACCEPTED: {label}"
    if rule:
        assert rule[0] in {v["rule"] for v in obs["violations"]}, (label, [v["rule"] for v in obs["violations"]])
