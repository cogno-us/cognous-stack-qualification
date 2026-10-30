"""D-2 harness (Archetype D worker, subordinate of the lead builder session; technical qualification result, NOT organizationally independent certification).

Covers (a) Q4b: component/classifier-level probes of authority_domain COMPARISON sensitivity (NOT end-to-end; the D-1 worker owns the end-to-end graft) and
(b) Q5: provision_local_execution_claim under D-06 binding drift on the governed 'pin' fixture (journal mode), compared row by row with
materialize_local_execution_claim for the same perturbation.
Q4 (persisted-content detection) re-executes the FROZEN readjudication file test_readj_gaps.py::test_G5a_persisted_member_content unmodified; it is not in this file.

Fixture helpers: orig_harness.py (byte-identical to the original F3-A post-AMEND4 harness, sha256 a5147412...), imported from this directory.
Instrument: store_effects() is copied verbatim from test_readj_gaps.py c682dd3a (AMEND-R3 semantics).
Expectations are written in PROTOCOL-D2-v1.md BEFORE any execution of this file. Selection of expectations per environment variant: env D2_VARIANT in {pristine, M06, M04}.
"""
from __future__ import annotations

import copy
import json
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import orig_harness as H  # noqa: E402

CODE = H.CODE
KEY = H.KEY
LEAVES = dict(H.MEMBER_LEAVES)
CLAIM_MSG = "authorization-critical inputs changed before claim issuance"
POLICY_PREFIX = "policy binding refused at claim issuance"
VARIANT = os.environ.get("D2_VARIANT", "pristine")


def _ev() -> Path:
    p = Path(os.environ["D2_EVIDENCE_DIR"])
    p.mkdir(parents=True, exist_ok=True)
    return p / "d2_evidence.jsonl"


def rec(case, kind, **f):
    with open(_ev(), "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"case": case, "kind": kind, "variant": VARIANT, "t": round(time.time(), 3), **f}, sort_keys=True, default=str) + "\n")


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
    import hashlib
    import platform
    import pydantic
    E = H.env()
    root = Path(E.acp.__file__).resolve().parents[2]
    want = Path(os.environ["D2_CP_ROOT"]).resolve()
    assert root == want, f"imported agent_control_plane from {root}, expected {want}"
    pin = H.pin_state()
    assert pin["head"] == H.EXPECTED_REGISTRY_HEAD and pin["require"] == "1", pin
    from agent_control_plane import effective_configuration_binding as ecb, local_authority_effect as lae
    sha = {Path(m.__file__).name: hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest() for m in (ecb, lae)}
    rec("PREFLIGHT", "OBSERVATION", acp=str(E.acp.__file__), cp_root=str(root), python=platform.python_version(), pydantic=pydantic.VERSION, pin=pin, source_sha256=sha)


@pytest.fixture(autouse=True)
def _clock(monkeypatch):
    H.patch_clock(monkeypatch)


# ---------------------------------------------------------------------------------------------------------------- instruments
def doc(d):
    return json.loads((Path(d) / "run.json").read_text())


def diff_keys(b, a):
    return sorted(k for k in set(b) | set(a) if b.get(k) != a.get(k))


ALLOWED_JOURNAL_KEYS = {"resolution_checks", "input_time_floors"}


def store_effects(b, a):  # verbatim from test_readj_gaps.py c682dd3a (AMEND-R3 semantics)
    changed = diff_keys(b, a)
    new_checks = a.get("resolution_checks", [])[len(b.get("resolution_checks", [])):]
    new_events = a.get("check_events", [])[len(b.get("check_events", [])):]
    return {"changed_keys": changed, "check_events_delta": len(new_events), "check_event_phases": [e.get("phase") for e in new_events],
            "strict_unexpected_keys": [k for k in changed if k not in ALLOWED_JOURNAL_KEYS],
            "unexpected": [k for k in ("decisions", "attempts", "observations", "reconciliations") if b.get(k) != a.get(k)],
            "new_refusals": [r.get("reasons") for r in a.get("refusals", [])[len(b.get("refusals", [])):]] if isinstance(a.get("refusals"), list) else None,
            "new_attempts": len(a.get("attempts", [])) - len(b.get("attempts", [])),
            "resolution_checks_delta": len(new_checks), "resolution_check_stages": [c.get("stage") for c in new_checks]}


class Spy:
    def __init__(self):
        self.calls = []

    def __call__(self, claim):
        self.calls.append(claim)


def _lae():
    from agent_control_plane import local_authority_effect as lae
    return lae


def claim_row(E, c, flow, mode, spy=None):
    """One claim attempt over the CURRENT store; mode in {materialize, provision}. Returns a JSON-able dict of the observed outcome and store effects."""
    lae = _lae()
    persisted = flow.records.decision(c.did)
    try:
        status = flow.configuration_binding_status(persisted)  # candidate classifier: EVIDENCE ONLY (read-only, writes nothing)
    except Exception as exc:
        status = f"raised:{type(exc).__name__}"
    b, dest_b, calls_b = doc(c.dir), flow.destination.snapshot(), flow.destination.calls
    out = {"mode": mode, "candidate_status": status, "outcome": None, "exc": None, "msg": None, "spy_calls": None, "spy_arg_is_result": None, "verify": None}
    kw = dict(now=E.NOW, claim_id="d2-claim", policy_binding=c.fx.binding, expected_consumer_id=c.fx.binding["consumer_id"], expected_operation=c.fx.binding["operation"])
    res = None
    try:
        if mode == "materialize":
            res = lae.materialize_local_execution_claim(flow, c.fx.p, persisted, **kw)
        else:
            res = lae.provision_local_execution_claim(flow, c.fx.p, persisted, provision=spy, **kw)
        out.update(outcome="claimed", claim_type=type(res).__name__)
    except Exception as exc:
        out.update(outcome="refused", exc=type(exc).__name__, msg=str(exc)[:240])
    if spy is not None:
        out["spy_calls"] = len(spy.calls)
        out["spy_arg_is_result"] = bool(res is not None and len(spy.calls) == 1 and spy.calls[0] is res)
    if res is not None:
        try:
            out["verify"] = bool(lae.verify_local_execution_claim(res))
        except Exception as exc:
            out["verify"] = f"raised:{type(exc).__name__}"
    out["effects"] = store_effects(b, doc(c.dir))
    out["dest_calls"] = flow.destination.calls - calls_b
    out["dest_unchanged"] = flow.destination.snapshot() == dest_b
    out["_claim"] = res
    return out


def public(out):
    return {k: v for k, v in out.items() if k != "_claim"}


def both_modes(E, c, perturbed_text, cfg=None):
    """Run materialize then provision over the SAME perturbed store text (store and destination restored between the two)."""
    rows = {}
    for mode in ("materialize", "provision"):
        H.put_text(c.dir, perturbed_text)
        H.reset_dest(c.dir)
        flow = H.restart(c, cfg)
        spy = Spy() if mode == "provision" else None
        rows[mode] = claim_row(E, c, flow, mode, spy)
    return rows["materialize"], rows["provision"]


def judge_refusal(chk, label, mat, prov):
    for who, r in (("provision", prov), ("materialize_ref", mat)):
        ef = r["effects"]
        chk.ok(f"{label}:{who}:R1_PermissionError_no_claim", r["outcome"] == "refused" and r["exc"] == "PermissionError", exc=r["exc"], msg=r["msg"])
        chk.ok(f"{label}:{who}:R2_documented_message", r["msg"] == CLAIM_MSG or (r["msg"] or "").startswith(POLICY_PREFIX), msg=r["msg"])
        chk.ok(f"{label}:{who}:R4_no_new_effect_time_refusal", ef["new_refusals"] == [] and "refusals" not in ef["changed_keys"], new_refusals=ef["new_refusals"])
        chk.ok(f"{label}:{who}:R5_no_authorization_state_write_no_attempt", ef["unexpected"] == [] and ef["new_attempts"] == 0, changed=ef["changed_keys"])
        chk.ok(f"{label}:{who}:R6_destination_untouched", r["dest_calls"] == 0 and r["dest_unchanged"])
        chk.ok(f"{label}:{who}:R7_journal_delta_le1_claim_stage", ef["resolution_checks_delta"] <= 1 and set(ef["resolution_check_stages"]) <= {"claim"},
               delta=ef["resolution_checks_delta"], stages=ef["resolution_check_stages"])
    chk.ok(f"{label}:R3_provision_spy_not_called", prov["spy_calls"] == 0, spy_calls=prov["spy_calls"])
    chk.ok(f"{label}:R8_provision_equals_materialize_type_message_effects",
           prov["exc"] == mat["exc"] and prov["msg"] == mat["msg"] and prov["outcome"] == mat["outcome"] and prov["effects"] == mat["effects"]
           and prov["dest_calls"] == mat["dest_calls"] and prov["dest_unchanged"] == mat["dest_unchanged"],
           prov_exc=prov["exc"], mat_exc=mat["exc"], prov_msg=prov["msg"], mat_msg=mat["msg"], prov_effects=prov["effects"], mat_effects=mat["effects"])
    chk.obs(f"{label}:candidate_status_vs_prediction", prov_status=prov["candidate_status"], mat_status=mat["candidate_status"])
    chk.obs(f"{label}:literal_flags", token_in_message=CODE in (prov["msg"] or ""), durable_refusal=prov["effects"]["new_refusals"] == [[CODE]])


def judge_accept(chk, label, mat, prov):
    for who, r in (("provision", prov), ("materialize_ref", mat)):
        ef = r["effects"]
        chk.ok(f"{label}:{who}:A1_claim_issued", r["outcome"] == "claimed", exc=r["exc"], msg=r["msg"])
        chk.ok(f"{label}:{who}:A4_no_new_effect_time_refusal_no_attempt", ef["new_refusals"] == [] and ef["new_attempts"] == 0 and "refusals" not in ef["changed_keys"])
        chk.ok(f"{label}:{who}:A5_no_authorization_state_write", ef["unexpected"] == [], changed=ef["changed_keys"])
        chk.ok(f"{label}:{who}:A6_destination_untouched", r["dest_calls"] == 0 and r["dest_unchanged"])
        chk.ok(f"{label}:{who}:A7_one_claim_stage_check", ef["resolution_checks_delta"] == 1 and ef["resolution_check_stages"] == ["claim"], delta=ef["resolution_checks_delta"],
               stages=ef["resolution_check_stages"])
    chk.ok(f"{label}:A2_spy_called_exactly_once_with_returned_claim", prov["spy_calls"] == 1 and prov["spy_arg_is_result"] is True, spy_calls=prov["spy_calls"], is_result=prov["spy_arg_is_result"])
    chk.ok(f"{label}:A3_verify_local_execution_claim_true", prov["verify"] is True, verify=prov["verify"])
    chk.ok(f"{label}:A8_provision_equals_materialize_outcome_effects", prov["outcome"] == mat["outcome"] and prov["effects"] == mat["effects"] and prov["claim_type"] == mat.get("claim_type"),
           prov_effects=prov["effects"], mat_effects=mat["effects"])
    try:
        same = prov["_claim"] == mat["_claim"]
    except Exception as exc:
        same = f"raised:{type(exc).__name__}"
    chk.obs(f"{label}:claim_objects_equal", equal=same)
    chk.obs(f"{label}:candidate_status_vs_prediction", prov_status=prov["candidate_status"], mat_status=mat["candidate_status"])


def pin_case(tmp_path, name="s"):
    c = H.with_pristine(H.new_case(tmp_path, "pin", name=name))
    return c


def perturbed(c, edit_fn):
    H.put_text(c.dir, c.pristine)
    H.edit(c.dir, c.did, edit_fn)
    return H.raw_text(c.dir)


# ---------------------------------------------------------------------------------------------------------------- Q5
def test_Q5_P0_control_unperturbed(tmp_path):
    E = H.env()
    chk = Check("Q5_P0_control")
    c = pin_case(tmp_path)
    chk.obs("python_member_status", status=c.flow.configuration_binding_status(c.flow.records.decision(c.did)))
    mat, prov = both_modes(E, c, c.pristine)
    rec(chk.case, "RAW", materialize=public(mat), provision=public(prov))
    judge_accept(chk, "control", mat, prov)
    chk.done()


Q5_MISMATCH = [("P1_f4_scalars.status_max_age_seconds", ("f4_scalars", "status_max_age_seconds")),
               ("P2_scope.authority_domain", ("scope", "authority_domain")),
               ("P3_families.0.effective_policy_digest", ("families", 0, "effective_policy_digest")),
               ("P4_host_profile_digest", ("host_profile_digest",)),
               ("P5_effective_profile_digest", ("effective_profile_digest",))]


@pytest.mark.parametrize("row_id,leaf", Q5_MISMATCH, ids=[x[0] for x in Q5_MISMATCH])
def test_Q5_mismatch_leaf(tmp_path, row_id, leaf):
    E = H.env()
    chk = Check(f"Q5_{row_id}")
    c = pin_case(tmp_path)
    original = H.member_of(c.dir, c.did)
    text = perturbed(c, lambda ra, item: ra.__setitem__(KEY, H.perturb_member(original, leaf)))
    chk.ok("perturbed_member_differs_and_self_consistent",
           H.member_of(c.dir, c.did)["digest"] != original["digest"] and H.my_digest(H.member_of(c.dir, c.did)["members"]) == H.member_of(c.dir, c.did)["digest"])
    mat, prov = both_modes(E, c, text)
    rec(chk.case, "RAW", materialize=public(mat), provision=public(prov))
    judge_refusal(chk, row_id, mat, prov)
    chk.done()


Q5_OTHER = [
    ("P6_stripped_member_cutoff0", lambda ra, item: H.strip_member(ra, item), None),
    ("P7_invalid_members_changed_old_digest", lambda ra, item: ra[KEY]["members"]["f4_scalars"].__setitem__("status_max_age_seconds", 31), None),
    ("P8_invalid_digest_truncated", lambda ra, item: ra[KEY].__setitem__("digest", ra[KEY]["digest"][:-2]), None),
    ("P9_unknown_version_resealed", lambda ra, item: (ra[KEY].__setitem__("version", "effective-configuration-binding/0.2"), H.reseal(ra[KEY])), None),
]


@pytest.mark.parametrize("row_id,fn,cfg", Q5_OTHER, ids=[x[0] for x in Q5_OTHER])
def test_Q5_stripped_invalid_unknown(tmp_path, row_id, fn, cfg):
    E = H.env()
    chk = Check(f"Q5_{row_id}")
    c = pin_case(tmp_path)
    text = perturbed(c, fn)
    mat, prov = both_modes(E, c, text, cfg)
    rec(chk.case, "RAW", materialize=public(mat), provision=public(prov))
    judge_refusal(chk, row_id, mat, prov)
    chk.done()


def test_Q5_L1_legacy_accepted_cutoff1_idx0_stripped(tmp_path):
    E = H.env()
    chk = Check("Q5_L1_legacy_cutoff1_idx0_stripped")
    c = pin_case(tmp_path)
    text = perturbed(c, lambda ra, item: H.strip_member(ra, item))
    chk.ok("single_decision_idx0", len(doc(c.dir)["decisions"]) == 1)
    mat, prov = both_modes(E, c, text, {"cutoff": 1})
    rec(chk.case, "RAW", materialize=public(mat), provision=public(prov))
    judge_accept(chk, "L1", mat, prov)
    chk.ok("L1:status_legacy_prediction", prov["candidate_status"] == "legacy", status=prov["candidate_status"])
    chk.done()


def test_Q5_L2_legacy_generated_by_prior_binary_cutoff1_idx0(tmp_path):
    E = H.env()
    old = os.environ["F3_OLD_SRC"]
    chk = Check("Q5_L2_legacy_generated_cutoff1_idx0")
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
    chk.ok("store_has_no_member", all(KEY not in ((x["binding"] or {}).get("runtime_authority") or {}) for x in doc(store)["decisions"] if x.get("binding")))
    fx = H.make_fixture(E, "pin", base / "fxwork")
    c = SimpleNamespace(E=E, kind="pin", dir=store, fx=fx, did=ids[0], cfg={"cutoff": 1})
    text = H.raw_text(store)
    mat, prov = both_modes(E, c, text, {"cutoff": 1})
    rec(chk.case, "RAW", materialize=public(mat), provision=public(prov))
    judge_accept(chk, "L2", mat, prov)
    chk.done()


NONCALLABLES = [("none", None), ("int", 5), ("str", "x"), ("object", object())]


def _typeerror_rows(chk, c, label, text):
    lae = _lae()
    E = c.E
    for nid, nc in NONCALLABLES:
        H.put_text(c.dir, text)
        H.reset_dest(c.dir)
        flow = H.restart(c)
        persisted = flow.records.decision(c.did)
        before_text, dest_b, calls_b = H.raw_text(c.dir), flow.destination.snapshot(), flow.destination.calls
        exc = msg = None
        res = None
        try:
            res = lae.provision_local_execution_claim(flow, c.fx.p, persisted, provision=nc, now=E.NOW, claim_id="d2-claim", policy_binding=c.fx.binding,
                                                      expected_consumer_id=c.fx.binding["consumer_id"], expected_operation=c.fx.binding["operation"])
        except Exception as e:
            exc, msg = type(e).__name__, str(e)
        chk.ok(f"{label}:{nid}:T1_TypeError_provision_must_be_callable", exc == "TypeError" and msg == "provision must be callable" and res is None, exc=exc, msg=msg)
        chk.ok(f"{label}:{nid}:T2_store_byte_identical_before_any_write", H.raw_text(c.dir) == before_text)
        chk.ok(f"{label}:{nid}:T3_destination_untouched", flow.destination.calls == calls_b and flow.destination.snapshot() == dest_b)


def test_Q5_T1_noncallable_provision_typeerror_before_write_unperturbed(tmp_path):
    chk = Check("Q5_T1_noncallable_unperturbed")
    c = pin_case(tmp_path)
    _typeerror_rows(chk, c, "T1", c.pristine)
    chk.done()


def test_Q5_T2_noncallable_provision_typeerror_ordering_perturbed(tmp_path):
    chk = Check("Q5_T2_noncallable_perturbed_store")
    c = pin_case(tmp_path)
    original = H.member_of(c.dir, c.did)
    text = perturbed(c, lambda ra, item: ra.__setitem__(KEY, H.perturb_member(original, ("f4_scalars", "status_max_age_seconds"))))
    _typeerror_rows(chk, c, "T2", text)
    chk.done()


# ---------------------------------------------------------------------------------------------------------------- Q4b (component / classifier level)
def _ecb():
    from agent_control_plane import effective_configuration_binding as ecb
    return ecb


def _leaf_diff(a, b, prefix=()):
    """Paths at which two JSON-like structures differ (leaf level)."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            out += _leaf_diff(a.get(k), b.get(k), prefix + (k,)) if (k in a and k in b) else [".".join(map(str, prefix + (k,)))]
        return out
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out += _leaf_diff(x, y, prefix + (i,))
        return out
    return [] if a == b else [".".join(map(str, prefix))]


@pytest.mark.parametrize("kind", ["pin", "f4"])
def test_Q4b_B1_persisted_authority_domain_edit_classified_mismatch_via_public_status(tmp_path, kind):
    """COMPONENT/CLASSIFIER level (public configuration_binding_status), persisted-side edit only; labelled so; not an end-to-end or live-side-world result."""
    chk = Check(f"Q4b_B1_{kind}")
    c = H.with_pristine(H.new_case(tmp_path, kind))
    persisted = c.flow.records.decision(c.did)
    chk.ok("control_status_bound", c.flow.configuration_binding_status(persisted) == "bound", status=c.flow.configuration_binding_status(persisted))
    original = H.member_of(c.dir, c.did)
    new_member = H.perturb_member(original, ("scope", "authority_domain"))
    H.edit(c.dir, c.did, lambda ra, item: ra.__setitem__(KEY, new_member))
    diff = _leaf_diff(original["members"], H.member_of(c.dir, c.did)["members"])
    chk.ok("member_diff_exactly_scope_authority_domain", diff == ["scope.authority_domain"], diff=diff)
    chk.ok("edited_member_self_consistent_digest", H.my_digest(H.member_of(c.dir, c.did)["members"]) == H.member_of(c.dir, c.did)["digest"])
    flow = H.restart(c)
    st = flow.configuration_binding_status(flow.records.decision(c.did))
    chk.ok("edited_status_mismatch", st == "mismatch", status=st)
    chk.done()


def test_Q4b_B2_classify_live_vs_persisted_domain_pure(tmp_path):
    """COMPONENT level: ecb.classify with persisted/live members equal in everything except scope.authority_domain, both directions, with the domain value edited directly
    (does not go through scope_identity)."""
    chk = Check("Q4b_B2_classify_pure")
    ecb = _ecb()
    c = H.new_case(tmp_path, "f4")
    m = H.member_of(c.dir, c.did)
    same = ecb.mint(copy.deepcopy(m["members"]))
    other_members = copy.deepcopy(m["members"])
    other_members["scope"]["authority_domain"] = other_members["scope"]["authority_domain"] + "-other"
    other = ecb.mint(other_members)
    chk.ok("mint_of_persisted_members_equals_persisted_record", same == m, same_digest=same["digest"], persisted_digest=m["digest"])
    chk.ok("live_domains_differ_only_in_domain", _leaf_diff(same["members"], other["members"]) == ["scope.authority_domain"], diff=_leaf_diff(same["members"], other["members"]))
    kw = dict(index=0, cutoff=0, decision_count=1)
    chk.ok("equal_members_bound", ecb.classify({KEY: copy.deepcopy(m)}, same, **kw) == "bound")
    chk.ok("live_domain_differs_mismatch", ecb.classify({KEY: copy.deepcopy(m)}, other, **kw) == "mismatch")
    chk.ok("persisted_domain_differs_mismatch", ecb.classify({KEY: copy.deepcopy(other)}, same, **kw) == "mismatch")
    chk.done()


def test_Q4b_B3_scope_identity_derivation_blindness_demonstration(tmp_path):
    """COMPONENT level, variant-keyed. scope_identity is the ONE derivation feeding both the minted and the live member. Pristine: two different domains give different members and
    classify mismatch. M06: the derivation is constant, so a domain change is invisible to the comparison (classify bound)."""
    chk = Check("Q4b_B3_derivation")
    ecb = _ecb()
    c = H.new_case(tmp_path, "f4")
    m = H.member_of(c.dir, c.did)
    s = m["members"]["scope"]
    ids = {d: ecb.scope_identity(s["consumer_id"], s["tenant_id"], s["action_id"], s["institution_id"], d) for d in ("domain-one", "domain-two")}

    def member_with(scope):
        mem = copy.deepcopy(m["members"])
        mem["scope"] = scope
        return ecb.mint(mem)
    a, b = member_with(ids["domain-one"]), member_with(ids["domain-two"])
    status = ecb.classify({KEY: copy.deepcopy(a)}, b, index=0, cutoff=0, decision_count=1)
    rec(chk.case, "RAW", scope_one=ids["domain-one"], scope_two=ids["domain-two"], status=status)
    if VARIANT == "M06":
        chk.ok("M06_scope_identity_ignores_domain", ids["domain-one"] == ids["domain-two"])
        chk.ok("M06_classify_blind_to_derivation_level_domain_change_bound", status == "bound", status=status)
    else:
        chk.ok("pristine_scope_identity_distinguishes_domains", ids["domain-one"] != ids["domain-two"])
        chk.ok("pristine_classify_mismatch", status == "mismatch", status=status)
    chk.done()
