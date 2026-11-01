"""F3-A readjudication gap harness (qualifier-authored assertions). Criteria are those frozen in PROTOCOL-F3A-READJ-v1.md (sha256 in MANIFEST-freeze.txt).
Shared tooling (disclosed): fixture helpers are imported from the byte-verified original harness (orig_harness.py == test_f3a_independent.post-AMEND4.py).
Run: PYTHONPATH=<cp>/src READJ_CP_ROOT=<cp> OCS_REGISTRY_PIN_DIR=<pin> OCS_REQUIRE_REGISTRY_PIN=1 F3_EVIDENCE_DIR=<dir-for-helper-side-records>
     READJ_EVIDENCE_DIR=<dir> F3_OLD_SRC=<b7eb11a>/src python -m pytest -p no:cacheprovider test_readj_gaps.py
"""
from __future__ import annotations

import copy
import json
import os
import re
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, "/tmp/claude-0/work/orig")
import orig_harness as H  # noqa: E402

CODE = H.CODE
KEY = H.KEY
LEAVES = H.MEMBER_LEAVES
CLAIM_MSG = "authorization-critical inputs changed before claim issuance"
ALLOWED_JOURNAL_KEYS = {"resolution_checks", "input_time_floors"}


def _ev() -> Path:
    p = Path(os.environ["READJ_EVIDENCE_DIR"])
    p.mkdir(parents=True, exist_ok=True)
    return p / "readj_evidence.jsonl"


def rec(case, kind, **f):
    with open(_ev(), "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"case": case, "kind": kind, "t": round(time.time(), 3), **f}, sort_keys=True, default=str) + "\n")


class Check:
    def __init__(self, case):
        self.case, self.fails = case, []

    def ok(self, name, cond, **info):
        rec(self.case, "CHECK_PASS" if cond else "CHECK_FAIL", check=name, **info)
        if not cond:
            self.fails.append(name)
        return bool(cond)

    def obs(self, name, **info):
        rec(self.case, "OBSERVATION", check=name, **info)

    def done(self):
        assert not self.fails, f"{self.case}: failed {self.fails}"


@pytest.fixture(scope="session", autouse=True)
def _preflight():
    E = H.env()
    root = Path(E.acp.__file__).resolve().parents[2]
    want = Path(os.environ["READJ_CP_ROOT"]).resolve()
    assert root == want, f"imported agent_control_plane from {root}, expected {want}"
    import platform, pydantic
    pin = H.pin_state()
    assert pin["head"] == H.EXPECTED_REGISTRY_HEAD and pin["require"] == "1", pin
    rec("PREFLIGHT", "OBSERVATION", acp=str(E.acp.__file__), cp_root=str(root), python=platform.python_version(), pydantic=pydantic.VERSION, pin=pin)


@pytest.fixture(autouse=True)
def _clock(monkeypatch):
    H.patch_clock(monkeypatch)


def doc(d):
    return json.loads((Path(d) / "run.json").read_text())


def diff_keys(b, a):
    return sorted(k for k in set(b) | set(a) if b.get(k) != a.get(k))


def store_effects(b, a):
    """Instrument: classify store changes. unexpected = any top-level key other than the journaling keys that changed."""
    changed = diff_keys(b, a)
    new_checks = a.get("resolution_checks", [])[len(b.get("resolution_checks", [])):]
    new_events = a.get("check_events", [])[len(b.get("check_events", [])):]
    return {"changed_keys": changed, "check_events_delta": len(new_events), "check_event_phases": [e.get("phase") for e in new_events],
            "strict_unexpected_keys": [k for k in changed if k not in ALLOWED_JOURNAL_KEYS],
            "unexpected": [k for k in ("decisions", "attempts", "observations", "reconciliations") if b.get(k) != a.get(k)],
            "new_refusals": [r.get("reasons") for r in a.get("refusals", [])[len(b.get("refusals", [])):]] if isinstance(a.get("refusals"), list) else None,
            "new_attempts": len(a.get("attempts", [])) - len(b.get("attempts", [])),
            "resolution_checks_delta": len(new_checks), "resolution_check_stages": [c.get("stage") for c in new_checks]}


def pin_call(E, flow, fx, did, store_dir):
    persisted = flow.records.decision(did)
    b, dest_b = doc(store_dir), flow.destination.snapshot()
    calls_b = flow.destination.calls
    out = {"raised": None, "msg": None, "state": None, "payload": "unset", "terminal_status": None, "reason": None}
    try:
        r = E.assess(flow, fx.p, persisted, now=E.NOW, host_policy_binding=fx.binding)
        out.update(state=r["state"], payload=r["payload"], terminal_status=r.get("terminal_status"), reason=r["reason"])
    except Exception as exc:
        out.update(raised=type(exc).__name__, msg=str(exc)[:240])
    a = doc(store_dir)
    out["effects"] = store_effects(b, a)
    out["dest_calls"] = flow.destination.calls - calls_b
    out["dest_unchanged"] = flow.destination.snapshot() == dest_b
    return out


def judge_pin_succ(chk, label, out):
    ef = out["effects"]
    chk.ok(f"{label}:P1_no_exception", out["raised"] is None, detail=out.get("msg"))
    chk.ok(f"{label}:P2_state_unknown", out["state"] == "unknown", state=out["state"])
    chk.ok(f"{label}:P3_payload_none_terminal_none", out["payload"] is None and out["terminal_status"] is None)
    chk.ok(f"{label}:P4_reason_nonempty_text", isinstance(out["reason"], str) and bool(out["reason"]), reason=out["reason"])
    chk.ok(f"{label}:P5_no_new_effect_time_refusal", ef["new_refusals"] == [] and "refusals" not in ef["changed_keys"], new_refusals=ef["new_refusals"])
    chk.ok(f"{label}:P6_no_authorization_state_write", ef["unexpected"] == [] and ef["new_attempts"] == 0, changed=ef["changed_keys"])
    chk.ok(f"{label}:P7_destination_untouched", out["dest_calls"] == 0 and out["dest_unchanged"])
    chk.ok(f"{label}:P8_one_claim_stage_resolution_check", ef["resolution_checks_delta"] == 1 and ef["resolution_check_stages"] == ["claim"],
           delta=ef["resolution_checks_delta"], stages=ef["resolution_check_stages"])


def literal_flags(chk, label, out):
    # reading (i) flags recorded for scoring (not asserted here: they are scored by the scorer from raw records)
    names = CODE in (out.get("reason") or "") or CODE in (out.get("msg") or "")
    durable = out["effects"]["new_refusals"] == [[CODE]]
    chk.obs(f"{label}:literal_flags", reason_names_code=names, durable_effect_time_refusal=durable, state=out["state"], payload_is_none=out["payload"] is None,
            dest_untouched=out["dest_calls"] == 0 and out["dest_unchanged"])


@pytest.mark.parametrize("leaf_id,leaf", LEAVES, ids=[x[0] for x in LEAVES])
def test_G1_pin_export_mismatch(tmp_path, leaf_id, leaf):
    E = H.env()
    chk = Check(f"G1_pin[{leaf_id}]")
    c = H.with_pristine(H.new_case(tmp_path, "pin"))
    ctl = pin_call(E, H.restart(c), c.fx, c.did, c.dir)
    chk.ok("control_unperturbed_active_with_payload", ctl["state"] == "active" and isinstance(ctl["payload"], dict), state=ctl["state"])
    H.put_text(c.dir, c.pristine)
    original = H.member_of(c.dir, c.did)
    H.edit(c.dir, c.did, lambda ra, item: ra.__setitem__(KEY, H.perturb_member(original, leaf)))
    chk.ok("perturbed_member_differs", H.member_of(c.dir, c.did)["digest"] != original["digest"])
    out = pin_call(E, H.restart(c), c.fx, c.did, c.dir)
    rec(chk.case, "RAW", out=H.jsonable(out))
    judge_pin_succ(chk, leaf_id, out)
    literal_flags(chk, leaf_id, out)
    chk.done()


def test_G1_instrument_detects_refusal_write(tmp_path):
    """Instrument validity: the store-diff instrument must see the durable EffectTimeRefusal that the EXECUTE path writes."""
    E = H.env()
    chk = Check("G1_instrument_validity")
    c = H.with_pristine(H.new_case(tmp_path, "pin"))
    original = H.member_of(c.dir, c.did)
    H.edit(c.dir, c.did, lambda ra, item: ra.__setitem__(KEY, H.perturb_member(original, ("f4_scalars", "status_max_age_seconds"))))
    flow = H.restart(c)
    b = doc(c.dir)
    ex = H.drive_execute(E, flow, c.fx.p, c.did)
    ef = store_effects(b, doc(c.dir))
    chk.ok("execute_refused", ex.get("raised") == "PermissionError")
    chk.ok("instrument_sees_new_refusal", ef["new_refusals"] == [[CODE]] and "refusals" in ef["changed_keys"], effects=ef)
    chk.done()


def claim_call(E, flow, fx, did, store_dir):
    persisted = flow.records.decision(did)
    b, dest_b, calls_b = doc(store_dir), flow.destination.snapshot(), flow.destination.calls
    out = {"outcome": None, "exc": None, "msg": None}
    try:
        res = E.claim(flow, fx.p, persisted, now=E.NOW, claim_id="readj-claim", policy_binding=fx.binding,
                      expected_consumer_id=fx.binding["consumer_id"], expected_operation=fx.binding["operation"])
        out["outcome"] = "claimed"
        out["claim_type"] = type(res).__name__
    except Exception as exc:
        out.update(outcome="refused", exc=type(exc).__name__, msg=str(exc)[:240])
    out["effects"] = store_effects(b, doc(store_dir))
    out["dest_calls"] = flow.destination.calls - calls_b
    out["dest_unchanged"] = flow.destination.snapshot() == dest_b
    return out


@pytest.mark.parametrize("leaf_id,leaf", LEAVES, ids=[x[0] for x in LEAVES])
def test_G2_claim_issuance_mismatch(tmp_path, leaf_id, leaf):
    E = H.env()
    chk = Check(f"G2_claim[{leaf_id}]")
    c = H.with_pristine(H.new_case(tmp_path, "pin"))
    ctl = claim_call(E, H.restart(c), c.fx, c.did, c.dir)
    chk.ok("control_unperturbed_claim_issued", ctl["outcome"] == "claimed", detail=ctl.get("msg"))
    H.put_text(c.dir, c.pristine)
    original = H.member_of(c.dir, c.did)
    H.edit(c.dir, c.did, lambda ra, item: ra.__setitem__(KEY, H.perturb_member(original, leaf)))
    out = claim_call(E, H.restart(c), c.fx, c.did, c.dir)
    rec(chk.case, "RAW", out=H.jsonable(out))
    ef = out["effects"]
    chk.ok("C1_permission_error_no_claim", out["outcome"] == "refused" and out["exc"] == "PermissionError", exc=out["exc"], msg=out["msg"])
    chk.obs("C2_message_matches_documented_text", match=out["msg"] == CLAIM_MSG, msg=out["msg"])
    chk.ok("C3_no_new_effect_time_refusal", ef["new_refusals"] == [] and "refusals" not in ef["changed_keys"], new_refusals=ef["new_refusals"])
    chk.ok("C4_no_authorization_state_write", ef["unexpected"] == [] and ef["new_attempts"] == 0, changed=ef["changed_keys"])
    chk.ok("C5_destination_untouched", out["dest_calls"] == 0 and out["dest_unchanged"])
    chk.ok("C6_journal_delta_le1_claim_stage", ef["resolution_checks_delta"] <= 1 and set(ef["resolution_check_stages"]) <= {"claim"}, delta=ef["resolution_checks_delta"],
           stages=ef["resolution_check_stages"])
    chk.obs("literal_flags", token_in_message=CODE in (out["msg"] or ""), durable_refusal=ef["new_refusals"] == [[CODE]])
    chk.done()


def test_G3_A06_legacy_pin_cutoff0_idx0(tmp_path):
    E = H.env()
    old = os.environ["F3_OLD_SRC"]
    chk = Check("G3_A06_pin_cutoff0_idx0")
    base = Path(tmp_path) / "legacy_pin"
    ids = []
    for i in range(2):
        o = H.run_worker("decide", "pin", base / "store", base / f"gen{i}", {}, old_src=old)
        chk.ok("legacy_generator_ran_under_baseline_binary", not o.get("worker_error") and str(o.get("acp", "")).startswith(old), acp=o.get("acp"))
        if o.get("worker_error") or o.get("result") != "authorized":
            rec(chk.case, "RAW", worker=H.jsonable(o))
            break
        ids.append(o["decision_id"])
    chk.ok("two_legacy_decisions", len(ids) == 2)
    if len(ids) != 2:
        chk.done()
        return
    store = base / "store"
    pristine = H.raw_text(store)
    chk.ok("store_has_no_member", all(KEY not in ((x["binding"] or {}).get("runtime_authority") or {}) for x in doc(store)["decisions"] if x.get("binding")))
    fx = H.make_fixture(E, "pin", base / "fxwork")
    flow = H.construct(E, "pin", fx, store, {"cutoff": 1})
    ctl = pin_call(E, flow, fx, ids[0], store)
    chk.ok("control_cutoff1_idx0_active", ctl["state"] == "active" and isinstance(ctl["payload"], dict), state=ctl["state"])
    H.put_text(store, pristine)
    H.reset_dest(store)
    flow = H.construct(E, "pin", fx, store, {"cutoff": 0})
    out = pin_call(E, flow, fx, ids[0], store)
    rec(chk.case, "RAW", out=H.jsonable(out))
    judge_pin_succ(chk, "pin:cutoff0_idx0", out)
    literal_flags(chk, "pin:cutoff0_idx0", out)
    chk.done()


def _cp_root():
    return Path(os.environ["READJ_CP_ROOT"]).resolve()


def test_G4_documentation_limits_S_DOC():
    chk = Check("G4_S_DOC")
    root = _cp_root()
    docp = root / "docs" / "effective-configuration-binding.md"
    text = docp.read_text(encoding="utf-8")
    low = text.lower()
    chk.ok("D1a_unsigned_store", "unsigned" in low)
    chk.ok("D1b_no_anti_rollback_guarantee", "no anti-rollback guarantee" in low)
    chk.ok("D1c_cutoff_no_durable_provenance", "no durable provenance" in low and "legacy_cutoff" in low)
    chk.ok("D1d_mixed_fleet", "mixed fleet" in low or "mixed-fleet" in low)
    masked = [(n, l.strip()[:300]) for n, l in enumerate(text.splitlines(), 1) if "masked" in l.lower() or ("stricter" in l.lower() and "host" in l.lower())]
    chk.ok("D2_masked_host_change_limitation_stated", any("masked" in l.lower() for _, l in masked) and any("stricter" in l.lower() for _, l in masked), lines=masked)
    aff = re.compile(r"(prevent|protect|guarantee|defen[cd]|ensure|resist)", re.I)
    neg = re.compile(r"\b(no|not|never|without|cannot|does not|do not|isn't|nor|neither|absent|held|separate held item)\b", re.I)
    affirmative = []
    for rel in ("docs/effective-configuration-binding.md", "docs/final3-consumers.md", "docs/d07-purpose-observation-anchor-correction.md", "src/agent_control_plane/effective_configuration_binding.py",
                "src/agent_control_plane/registry_governed_lifecycle.py"):
        p = root / rel
        if not p.is_file():
            continue
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"roll(ed)?[- ]?back", line, re.I):
                is_aff = bool(aff.search(line)) and not neg.search(line)
                rec(chk.case, "OBSERVATION", check="rollback_line", file=rel, line=n, text=line.strip()[:300], looks_affirmative=is_aff)
                if is_aff:
                    affirmative.append((rel, n))
    chk.ok("D3_no_line_affirms_rollback_protection", affirmative == [], lines=affirmative)
    pin_lines = [(n, l.strip()[:400]) for n, l in enumerate(text.splitlines(), 1) if re.search(r"pin[- ]export|claim issuance", l, re.I)]
    chk.obs("D4_pin_export_claim_lines", lines=pin_lines)
    chk.ok("D4a_doc_states_pin_export_not_active_no_payload", any(re.search(r"not\s+`?active`?", l) and "payload" in l.lower() for _, l in pin_lines))
    chk.ok("D4b_doc_states_no_effect_time_refusal_on_pin_export_claim", any(re.search(r"no\s+`?EffectTimeRefusal`?", l) for _, l in pin_lines))
    bad = [(n, l) for n, l in pin_lines if re.search(r"durable\s+`?EffectTimeRefusal`?", l) and not re.search(r"\b(no|not|never|without)\b", l, re.I) and re.search(r"pin[- ]export", l, re.I)]
    chk.ok("D4c_no_line_attributes_durable_refusal_to_pin_export", bad == [], lines=bad)
    stale = {"final3-consumers.md section 6 (D-07 status)": None}
    chk.obs("D5_docs_changed_vs_739efe7_listed_in_manifest", note="see git diff stat in raw results")
    chk.done()


def test_G5a_persisted_member_content(tmp_path):
    E = H.env()
    chk = Check("G5a_persisted_member_content")
    c = H.new_case(tmp_path, "pin")
    m = H.member_of(c.dir, c.did)["members"]
    ra = H.dec_item(doc(c.dir), c.did)["binding"]["runtime_authority"]
    exp_scope = {"consumer_id": "consumer-test", "tenant_id": H.TENANT, "action_id": E.ACTION_ID, "institution_id": E.INSTITUTION, "authority_domain": E.AUTHORITY_DOMAIN}
    chk.ok("scope_equals_independent_expectation", m["scope"] == exp_scope, persisted=m["scope"], expected=exp_scope)
    chk.ok("scope_authority_domain_equals_manifest_domain", m["scope"]["authority_domain"] == E.AUTHORITY_DOMAIN, persisted=m["scope"]["authority_domain"])
    cat = E.B.commitment(c.fx.cfg.model_dump(mode="json"))
    chk.ok("catalogue_digest_recomputed", ra.get("catalogue_digest") == cat)
    chk.ok("host_profile_digest_equals_catalogue_digest", m["host_profile_digest"] == cat, persisted=m["host_profile_digest"], expected=cat)
    chk.ok("effective_profile_digest_equals_catalogue_digest", m["effective_profile_digest"] == cat, persisted=m["effective_profile_digest"], expected=cat)
    f = H.new_case(tmp_path, "f4", name="f4case")
    mf = H.member_of(f.dir, f.did)["members"]
    chk.ok("f4_scope_authority_domain", mf["scope"]["authority_domain"] == E.AUTHORITY_DOMAIN)
    chk.ok("f4_profile_digests_null", mf["host_profile_digest"] is None and mf["effective_profile_digest"] is None, host=mf["host_profile_digest"], eff=mf["effective_profile_digest"])
    chk.done()
