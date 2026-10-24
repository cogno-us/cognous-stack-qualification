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


def test_history_per_file_hashes_are_self_consistent_and_record_the_superseded_pre_launcher_tree():
    """The history file is a historical record of the PRE-launcher hub tree (digest ea37100d..., six *.py files): it is not rewritten, only checked for self-consistency."""
    hist = json.loads((pathlib.Path(__file__).resolve().parents[2] / "process" / "mvp-chain" / "history" / "nc4-03-v3-predicate-result.json").read_text())
    per_file = hist["scanned_files_sha256"]
    assert sorted(per_file) == ["__init__.py", "client.py", "core.py", "proposal.py", "server.py", "synthetic_host.py"]
    digest = hashlib.sha256("".join(f"{n}\0{per_file[n]}\n" for n in sorted(per_file, key=lambda x: x.encode())).encode()).hexdigest()
    assert digest == hist["ingress_tree_sha256"] == "ea37100d0827aea08c1c83303c911234e193854978d3313ae6d106688f2a9058"
    assert hist["ingress_tree_sha256"] != _kwflow.INGRESS_PY_TREE_SHA256


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


PINNED_SITES_ORIG = tuple(_kwflow.PINNED_SITES)  # keyed by site, not by line number (line numbers move with every hub edit)


def test_without_pins_the_baseline_fails(monkeypatch):
    monkeypatch.setattr(_kwflow, "PINNED_SITES", {})
    obs = _kwflow.scan_dir(BASE)
    assert {v["site"] for v in obs["violations"]} >= set(PINNED_SITES_ORIG)


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


# ---- v5: independent Q1 review of NC4-03 (12 evading mutants and their relatives), recursive tree, interpreter pin ---------------------------------------
PROV = "claim = host.executor.provision_claim(proposal=proposal, decision=decision, now=host.now)"
BP_RET = '''        return self.p0.model_copy(update={
            "target": "urn:cognous:synthetic-account:" + fields["customer_id"],
            "payload": payload, "payload_commitment": cp.commitment(payload),
            "amount": float(fields["amount"]), "unit": fields["unit"], "correlation_id": fields["request_id"]})'''
BP_TAIL = '"correlation_id": fields["request_id"]})'
ENV_RET = "        return ExecutionEnvelope(EXECUTION_ENVELOPE_VERSION, d.decision_id, d.effect_id, op)\n"


def _bp_update(extra):
    return ("synthetic_host.py", BP_RET, BP_RET.replace(BP_TAIL, '"correlation_id": fields["request_id"], ' + extra + "})"))


def _bp_post(post):
    head = BP_RET.replace("        return self.p0.model_copy(update={", "        p = self.p0.model_copy(update={").replace(BP_TAIL, BP_TAIL)
    return ("synthetic_host.py", BP_RET, head + "\n" + post + "        return p")


V5_MUTANTS = {
    "E01 provision_claim budget_id from client": ("core.py", PROV, PROV[:-1] + ", budget_id=fields['customer_id'])", "PROHIBITED_KEYWORD_NON_LITERAL"),
    "E02 execute attempt_id from client": ("core.py", "claim_id=claim.claim_id, simulate=None)", "claim_id=claim.claim_id, simulate=None, attempt_id=fields['request_id'])", "PROHIBITED_KEYWORD_NON_LITERAL"),
    "E03 provision_claim expires_at from client": ("core.py", PROV, PROV[:-1] + ", expires_at=fields['refund_reason'])", "PROHIBITED_KEYWORD_NON_LITERAL"),
    "E04 provision_claim decision_input_commitment from client": ("core.py", PROV, PROV[:-1] + ", decision_input_commitment=fields['request_id'])", "PROHIBITED_KEYWORD_NON_LITERAL"),
    "E04b provision_claim decision_input_profile_version from client": ("core.py", PROV, PROV[:-1] + ", decision_input_profile_version=fields['request_id'])", "PROHIBITED_KEYWORD_NON_LITERAL"),
    "E05 decide now from client": ("core.py", "host.workflow.decide(proposal, now=host.now)", "host.workflow.decide(proposal, now=fields['amount'])", "PROHIBITED_KEYWORD_NON_LITERAL"),
    "E07 object.__setattr__ on claim": ("core.py", "res = host.executor.execute(", "object.__setattr__(claim, 'claim_id', fields['request_id'])\n            res = host.executor.execute(", "AUTHORITY_OBJECT_MUTATION"),
    "E08 attribute store on decision.binding": ("core.py", PROV, "decision.binding.grant_id = fields['request_id']\n            " + PROV, "AUTHORITY_OBJECT_MUTATION"),
    "E09 setattr on proposal in _run": ("core.py", PROV, "setattr(proposal, 'authority_context_ref', fields['customer_id'])\n            " + PROV, "AUTHORITY_OBJECT_MUTATION"),
    "E10 attribute store on p in build_proposal": _bp_post("        p.authority_context_ref = fields['customer_id']\n") + ("AUTHORITY_OBJECT_MUTATION",),
    "E11 setattr on p in build_proposal": _bp_post("        setattr(p, 'requested_permissions', [fields['refund_reason']])\n") + ("AUTHORITY_OBJECT_MUTATION",),
    "E12 build_proposal update gains RuntimeProposal fields": _bp_update('"risk_metadata": {"r": fields["refund_reason"]}, "evidence_refs": [fields["request_id"]], "run_id": fields["request_id"], '
                                                                        '"expires_at": fields["refund_reason"], "not_before": fields["refund_reason"], "expected_side_effects": [fields["refund_reason"]]') + ("PROHIBITED_KEY_IN_FIXED_FORM",),
    "E12b build_proposal update gains tenant_id": _bp_update('"tenant_id": fields["customer_id"]') + ("PROHIBITED_KEY_IN_FIXED_FORM",),
    "E13 proposal built by model_validate": ("synthetic_host.py", BP_RET, '        return type(self.p0).model_validate({**self.p0.model_dump(), "actor": fields["customer_id"]})', "DYNAMIC_PROPOSAL_CONSTRUCTION"),
    "E14 proposal built by __class__": ("synthetic_host.py", BP_RET, '        d = self.p0.model_dump()\n        return self.p0.__class__(**d)', "DYNAMIC_ATTRIBUTE_ACCESS"),
    "E15 positional client value into ExecutionOperation in a new method": ("synthetic_host.py", ENV_RET,
        ENV_RET + "\n    def envelope2(self, d, p, fields):\n        op = ExecutionOperation(p.actor, p.principal, 'i', fields['customer_id'])\n        return op\n", "POSITIONAL_NON_LITERAL"),
    "E15b positional client value into ExecutionEnvelope": ("synthetic_host.py", ENV_RET, "        return ExecutionEnvelope(EXECUTION_ENVELOPE_VERSION, d.decision_id, p.payload['x'], op)\n", "POSITIONAL_NON_LITERAL"),
    "E16 dynamic callee with attempt_id": ("core.py", "res = host.executor.execute(", "res = getattr(host.executor, 'exe' + 'cute')(attempt_id=fields['request_id'], ", "PROHIBITED_KEYWORD_NON_LITERAL"),
    "E17 import-as rebinding of the claim name via match capture": ("core.py", "res = host.executor.execute(",
        "from types import SimpleNamespace as claim_ns\n            match claim_ns(claim_id=fields['request_id']):\n                case claim_ns(claim_id=_) as claim:\n                    pass\n            res = host.executor.execute(", "ORIGIN_VIOLATION"),
    "E17b import-as rebinding of the claim name": ("core.py", "res = host.executor.execute(", "from types import SimpleNamespace as claim\n            res = host.executor.execute(", "ORIGIN_VIOLATION"),
    "E18 except-as rebinding of the claim name": ("core.py", "res = host.executor.execute(",
        "try:\n                raise ValueError(fields['request_id'])\n            except ValueError as claim:\n                pass\n            res = host.executor.execute(", "ORIGIN_VIOLATION"),
    "E19 helper function mutates the claim": ("core.py", "class IngressCore:", "def _poke(o, v):\n    object.__setattr__(o, 'claim_id', v)\n\n\nclass IngressCore:", "AUTHORITY_OBJECT_MUTATION"),
    "E21 second execute call with attempt_id in a new method": ("core.py", "    def _run(self, fields, request_id) -> dict:",
        "    def _alt(self, host, fields, claim, env):\n        return host.executor.execute(envelope=env, claim_id=claim.claim_id, attempt_id=fields['request_id'])\n\n    def _run(self, fields, request_id) -> dict:", "PROHIBITED_KEYWORD_NON_LITERAL"),
}


def _rebased_scan(root):
    """Scan with the pins and the recursive digest re-based onto the mutated tree: only the source-aware rules decide (a plain edit would otherwise fail by un-pinning)."""
    saved_pins = {k: dict(v) for k, v in _kwflow.PINNED_SITES.items()}
    saved_tree = _kwflow.EXPECTED_TREE_SHA256
    try:
        _, tree = _kwflow.ingress_tree_manifest(sorted((root / "tools" / "mvp_ingress").glob("*.py")))
        for r in _kwflow.PINNED_SITES.values():
            r["reviewed_ingress_tree_sha256"] = tree
        _kwflow.EXPECTED_TREE_SHA256 = _kwflow.tree_digest(_kwflow.tree_files(root))
        return _kwflow.scan_dir(root)
    finally:
        _kwflow.PINNED_SITES.clear()
        _kwflow.PINNED_SITES.update(saved_pins)
        _kwflow.EXPECTED_TREE_SHA256 = saved_tree


def test_unmutated_ingress_still_passes_when_rebased_control(tmp_path):
    shutil.copytree(BASE / "tools" / "mvp_ingress", tmp_path / "tools" / "mvp_ingress")
    obs = _rebased_scan(tmp_path)
    assert obs["violations"] == [] and obs["pins_unmatched"] == [] and obs["required_sites_missing"] == []
    assert len(obs["pinned_sites_used"]) == 3


@pytest.mark.parametrize("label", sorted(V5_MUTANTS))
def test_v5_evading_mutant_is_rejected_by_its_source_aware_rule(label, tmp_path):
    dst = tmp_path / "tools" / "mvp_ingress"
    shutil.copytree(BASE / "tools" / "mvp_ingress", dst)
    fname, old, new, rule = V5_MUTANTS[label]
    text = (dst / fname).read_text()
    assert text.count(old) == 1, "mutation anchor not found exactly once"
    (dst / fname).write_text(text.replace(old, new))
    obs = _rebased_scan(tmp_path)
    assert rule in {v["rule"] for v in obs["violations"]}, (label, [v["rule"] for v in obs["violations"]])
    assert obs["pins_unmatched"] == [] or label.startswith("E15"), "the pinned sites must stay matched: the rule itself must reject the mutant"


def test_real_hub_tree_is_unchanged_and_has_exactly_the_expected_files():
    obs = _kwflow.scan_dir(BASE)
    assert [r for r, k in obs["recursive_tree_files"]] == _kwflow.EXPECTED_TREE_FILES and all(k == "file" for _, k in obs["recursive_tree_files"])
    assert len(_kwflow.EXPECTED_TREE_FILES) == 8 and obs["recursive_tree_sha256"] == _kwflow.EXPECTED_TREE_SHA256
    assert obs["ingress_tree_sha256"] == _kwflow.INGRESS_PY_TREE_SHA256  # the *.py digest the pins bind is unchanged


def _tree_copy(tmp_path):
    shutil.copytree(BASE / "tools" / "mvp_ingress", tmp_path / "tools" / "mvp_ingress")
    return tmp_path / "tools" / "mvp_ingress"


@pytest.mark.parametrize("name,write", [
    ("package shadowing proposal.py", lambda d: ((d / "proposal").mkdir(), (d / "proposal" / "__init__.py").write_text("raise SystemExit('shadow')\n"))),
    ("non-py file", lambda d: (d / "ignored.txt").write_text("x")),
    ("extension module", lambda d: (d / "proposal.cpython-313-x86_64-linux-gnu.so").write_bytes(b"\x7fELF")),
    ("sitecustomize", lambda d: (d / "sitecustomize.py").write_text("")),
    ("subpackage", lambda d: ((d / "sub").mkdir(), (d / "sub" / "__init__.py").write_text(""))),
    ("empty directory", lambda d: (d / "emptydir").mkdir()),
    ("symlink", lambda d: (d / "link.py").symlink_to("core.py")),
    ("removed file", lambda d: (d / "BOUNDARY.md").unlink()),
], ids=["package-shadowing-proposal", "non-py-file", "extension-module", "sitecustomize", "subpackage", "empty-directory", "symlink", "removed-file"])
def test_recursive_tree_rejects_extra_or_missing_entries(tmp_path, name, write):
    d = _tree_copy(tmp_path)
    write(d)
    obs = _kwflow.scan_dir(tmp_path)
    assert "INGRESS_TREE_FILE_LIST" in {v["rule"] for v in obs["violations"]}, name
    assert "INGRESS_TREE_DIGEST" in {v["rule"] for v in obs["violations"]}, name


def test_a_non_py_content_change_fails_the_recursive_digest_but_not_the_py_digest(tmp_path):
    d = _tree_copy(tmp_path)
    (d / "BOUNDARY.md").write_text((d / "BOUNDARY.md").read_text() + "\nedit\n")
    obs = _kwflow.scan_dir(tmp_path)
    assert obs["ingress_tree_sha256"] == _kwflow.INGRESS_PY_TREE_SHA256
    assert [v["rule"] for v in obs["violations"]] == ["INGRESS_TREE_DIGEST"]


def test_ast_digest_pins_fail_closed_except_on_the_recorded_interpreter(monkeypatch):
    assert all(r["ast_digest_python"] == "3.13" for r in _kwflow.PINNED_SITES.values())
    monkeypatch.setattr(_kwflow, "PIN_PYTHON", "3.12")  # emulates running anywhere but the recorded interpreter
    obs = _kwflow.scan_dir(BASE)
    assert obs["ast_digest_python_match"] is False and obs["violations"] and obs["pinned_sites_used"] == []
    assert obs["python_version"].count(".") == 2 and obs["ast_digest_python_required"] == "3.12"


def test_pin_prose_states_that_request_id_flows_via_correlation_id():
    text = _kwflow.PINNED_SITES["synthetic_host.py:SyntheticHost.envelope:ExecutionOperation#1"]["trusted_input_origin"]
    assert "correlation_id" in text and "NOT among the 14 names" in text


def test_launcher_isolation_helper_flags_the_shadowable_launch():
    assert _kwflow.launcher_isolated(["python", "-m", "tools.mvp_ingress.server"]) is False  # cwd-first sys.path: shadowable
    assert _kwflow.launcher_isolated(["python", "-P", "-m", "tools.mvp_ingress.server"]) is True
    assert _kwflow.launcher_isolated(["python", "-I", "-m", "tools.mvp_ingress.server"]) is True


def test_single_update_point_for_the_ingress_digest():
    assert {r["reviewed_ingress_tree_sha256"] for r in _kwflow.PINNED_SITES.values()} == {_kwflow.INGRESS_PY_TREE_SHA256}


# ---- interpreter-pinned assertions (architect Round 5): ast_digest pins are honoured on CPython 3.13 only. On any other interpreter (the supplementary Python 3.12
# workflow mvp-chain.yml) these assertions are SKIPPED with an explicit reason, never silently passed; a skipped instance in the authoritative 3.13 run would be
# INCOMPLETE at the gate, and a passing supplementary run is not qualification of the 3.13 profile. The source predicates are not redesigned for 3.12.
requires_313 = pytest.mark.skipif(_kwflow.pin_python() is None, reason="ast_digest pins are honoured on CPython 3.13 only; this interpreter is supplementary")
for _name in ("test_baseline_covers_all_of_ingress_and_is_accepted_only_via_pins", "test_pins_are_content_addressed_unrelated_hub_commit_still_passes",
              "test_any_byte_change_including_a_comment_fails_closed", "test_unmutated_ingress_still_passes_when_rebased_control",
              "test_a_non_py_content_change_fails_the_recursive_digest_but_not_the_py_digest", "test_ast_digest_pins_fail_closed_except_on_the_recorded_interpreter",
              "test_v5_evading_mutant_is_rejected_by_its_source_aware_rule"):
    globals()[_name] = requires_313(globals()[_name])
