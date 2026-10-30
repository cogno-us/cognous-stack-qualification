"""D-1 frozen cases (Q2/Q3 isolation) for Control Plane 739efe7. Governing document: PROTOCOL-D1-v1.md (its sha256 is recorded in PROTOCOL-D1-v1.sha256 and FREEZE-TIME.txt).
Archetype D, subordinate worker of the lead builder session: technical qualification result, NOT organizationally independent certification.
Run via run_d1.sh <label> <cp-root>. Every check is recorded (pass AND fail) in d1_evidence.jsonl; a failing check against a pristine subject is an ADVERSE FINDING
(prediction wrong or defect), never revised after the fact. Under a scratch mutant a failing check is a KILL signal.
"""
from __future__ import annotations

import hashlib
import os
import platform
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import d1_lib as L  # noqa: E402
from d1_lib import Check, rec  # noqa: E402

H = L.H
KEY = H.KEY
ECBP = "runtime_authority." + KEY
CT = L.CLASS_T1


@pytest.fixture(scope="session", autouse=True)
def _preflight():
    E = H.env()
    root = Path(E.acp.__file__).resolve().parents[2]
    want = Path(os.environ["D1_CP_ROOT"]).resolve()
    assert root == want, f"imported agent_control_plane from {root}, expected {want}"
    import pydantic
    pin = H.pin_state()
    assert pin["head"] == H.EXPECTED_REGISTRY_HEAD and pin["require"] == "1", pin
    rec("PREFLIGHT", "OBSERVATION", label=os.environ.get("D1_LABEL"), acp=str(E.acp.__file__), cp_root=str(root), python=platform.python_version(),
        pydantic=pydantic.VERSION, pin=pin)


@pytest.fixture(autouse=True)
def _clock(monkeypatch):
    H.patch_clock(monkeypatch)


def own_commit(obj) -> str:
    """Independent re-computation of the profile commitment (sha256 over canonical JSON); not the candidate's profile_digest."""
    return "sha256:" + hashlib.sha256(H.canon(obj)).hexdigest()


def claim_for(base, ecb, member: str) -> str:
    """Decision rule (PROTOCOL section 5): 'isolated end-to-end' iff the base-binding diff is empty and the member diff is exactly the member leaf plus its digest."""
    return "isolated end-to-end" if base == [] and sorted(ecb) == sorted([f"{ECBP}.digest", f"{ECBP}.members.{member}"]) else "joint"


def run(flow, p, did):
    return H.jsonable(H.drive_execute(H.env(), flow, p, did))


def refused_with(chk, label, out, codes, vocab=None):
    chk.ok(f"{label}:PermissionError", out.get("raised") == "PermissionError", detail=out)
    chk.ok(f"{label}:one_durable_refusal_exact_reasons", out["new_refusal_reasons"] == [sorted(codes)], observed=out["new_refusal_reasons"], expected=[sorted(codes)])
    if vocab is not None:
        chk.ok(f"{label}:vocabulary", out["new_refusal_vocab"] == [vocab], observed=out["new_refusal_vocab"])
    chk.ok(f"{label}:no_attempt", out["new_attempts"] == 0)
    chk.ok(f"{label}:destination_never_called_unchanged", out["dest_calls"] == 0 and out["dest_unchanged"])


def accepted(chk, label, out):
    chk.ok(f"{label}:acknowledged", out.get("raised") is None and out.get("attempt_status") == "acknowledged", detail=out)
    chk.ok(f"{label}:no_refusal_row", out["new_refusal_reasons"] == [])
    chk.ok(f"{label}:destination_called_exactly_once", out["dest_calls"] == 1)
    chk.ok(f"{label}:binding_status_bound(evidence-only classifier)", out.get("binding_status") == "bound", observed=out.get("binding_status"))


def f5_live_diff(E, w, mk_flow, tmp, name):
    live, res_, rs = L.live_binding(E, mk_flow, w.p, Path(tmp) / name)
    persisted = L.binding_of(w.dir, w.did)
    return (None, None, res_, rs) if live is None else (*L.split_diff(persisted, live), res_, rs)


# ======================================================================================================================== Q3
def test_Q3_H0_control(tmp_path):
    E, chk = H.env(), Check("Q3-H0")
    w = L.f5_world(E, tmp_path, "h0", t1=60, reg=10)
    flow, dec = L.f5_mint(E, w)
    chk.ok("minted_authorized", dec.result == "authorized", reasons=list(dec.reasons))
    flow2 = L.f5_flow(E, w)  # restart, identical host
    base, ecb, r_, rs = f5_live_diff(E, w, lambda sd: L.f5_flow(E, w, sd), tmp_path, "h0live")
    chk.ok("live_world_mints_authorized", r_ == "authorized", reasons=rs)
    chk.ok("binding_diff_empty", base == [] and ecb == [], base=base, ecb=ecb)
    out = run(flow2, w.p, w.did)
    accepted(chk, "H0", out)
    chk.done()


def test_Q3_H1_masked_host_edit_end_to_end(tmp_path):
    E, chk = H.env(), Check("Q3-H1")
    w = L.f5_world(E, tmp_path, "h1", t1=60, reg=10)
    flow1, dec = L.f5_mint(E, w)
    chk.ok("minted_authorized", dec.result == "authorized", reasons=list(dec.reasons))
    host2 = L.host_profile(E, w.p, 61)
    aid = w.p.action_id
    hd1, hd2 = w.host.model_dump(mode="json"), host2.model_dump(mode="json")
    chk.ok("host_profiles_differ_in_exactly_the_class_age", L.leaf_diff(hd1, hd2) == {f"actions.{aid}.max_status_age_seconds"}, diff=sorted(L.leaf_diff(hd1, hd2)))
    flow2 = L.f5_flow(E, w, host=host2)  # restart, host edited 60->61, same Registry, same approval (NOT re-bound)
    e1, e2 = flow1.runtime_authority_profile.model_dump(mode="json"), flow2.runtime_authority_profile.model_dump(mode="json")
    chk.ok("effective_profile_dumps_equal_masked", e1 == e2)
    chk.ok("effective_profile_independent_commitments_equal", own_commit(e1) == own_commit(e2))
    chk.ok("host_profile_independent_commitments_differ", own_commit(hd1) != own_commit(hd2))
    chk.ok("effective_class_age_is_registry_value", e1["actions"][aid]["max_status_age_seconds"] == 10 and e2["actions"][aid]["max_status_age_seconds"] == 10)
    base, ecb, r_, rs = f5_live_diff(E, w, lambda sd: L.f5_flow(E, w, sd, host=host2), tmp_path, "h1live")
    chk.ok("live_world_mints_authorized", r_ == "authorized", reasons=rs)
    claim = claim_for(base, ecb, "host_profile_digest")
    rec("Q3-H1", "CLASSIFICATION", claim=claim, base_diff=base, ecb_diff=ecb)
    chk.ok("binding_diff_base_empty", base == [], base=base)
    chk.ok("binding_diff_member_exactly_host_leaf_plus_digest", sorted(ecb or []) == sorted([f"{ECBP}.digest", f"{ECBP}.members.host_profile_digest"]), ecb=ecb)
    out = run(flow2, w.p, w.did)
    refused_with(chk, "H1", out, ["authorization_binding_changed"], "runtime-authority-reasons/0.1")
    chk.ok("binding_status_mismatch(evidence-only classifier)", out.get("binding_status") == "mismatch", observed=out.get("binding_status"))
    chk.ok("claim_is_isolated_end_to_end", claim == "isolated end-to-end", claim=claim)
    chk.done()


def test_Q3_H2_component(tmp_path):
    E, chk = H.env(), Check("Q3-H2")
    wa = L.f5_world(E, tmp_path, "h2a", t1=60, reg=10)
    fa, da = L.f5_mint(E, wa)
    wb = L.f5_world(E, tmp_path, "h2b", t1=61, reg=10)
    fb, db = L.f5_mint(E, wb)
    chk.ok("both_minted", da.result == "authorized" and db.result == "authorized")
    ma, mb = H.member_of(wa.dir, wa.did), H.member_of(wb.dir, wb.did)
    ra = H.dec_item(H.load_doc(wa.dir), wa.did)["binding"]["runtime_authority"]
    exp_host_a, exp_host_b = own_commit(wa.host.model_dump(mode="json")), own_commit(wb.host.model_dump(mode="json"))
    exp_eff = own_commit(fa.runtime_authority_profile.model_dump(mode="json"))
    chk.ok("host_digest_A_equals_independent_commitment", ma["members"]["host_profile_digest"] == exp_host_a)
    chk.ok("host_digest_B_equals_independent_commitment", mb["members"]["host_profile_digest"] == exp_host_b)
    chk.ok("effective_digest_A_equals_independent_commitment", ma["members"]["effective_profile_digest"] == exp_eff)
    chk.ok("effective_digest_B_equals_independent_commitment", mb["members"]["effective_profile_digest"] == exp_eff)
    chk.ok("effective_digest_equals_persisted_catalogue_digest", ma["members"]["effective_profile_digest"] == ra["catalogue_digest"], catalogue=ra["catalogue_digest"])
    chk.ok("host_differs_from_effective", ma["members"]["host_profile_digest"] != ma["members"]["effective_profile_digest"])
    chk.ok("member_diff_A_vs_B_exactly_host_leaf_and_digest", L.leaf_diff(ma, mb) == {"digest", "members.host_profile_digest"}, diff=sorted(L.leaf_diff(ma, mb)))
    chk.ok("digest_A_recomputed_independently", H.my_digest(ma["members"], ma["version"]) == ma["digest"])
    chk.ok("digest_B_recomputed_independently", H.my_digest(mb["members"], mb["version"]) == mb["digest"])
    # candidate classifier on a world-B workflow over each store (evidence only, never the oracle)
    fb_over_a = L.f5_flow(E, wa, host=wb.host)
    chk.ok("classifier_A_decision_under_host_B_is_mismatch(evidence-only)", fb_over_a.configuration_binding_status(fb_over_a.records.decision(wa.did)) == "mismatch")
    fa_over_a = L.f5_flow(E, wa)
    chk.ok("classifier_A_decision_under_host_A_is_bound(evidence-only)", fa_over_a.configuration_binding_status(fa_over_a.records.decision(wa.did)) == "bound")
    chk.done()


def test_Q3_E1_effective_no_reissue(tmp_path):
    E, chk = H.env(), Check("Q3-E1")
    w = L.f5_world(E, tmp_path, "e1", t1=60, reg=10)
    flow1, dec = L.f5_mint(E, w)
    chk.ok("minted_authorized", dec.result == "authorized")
    src2 = H.Src(L.f5_material(E, {CT: 20}))
    flow2 = L.f5_flow(E, w, src=src2, rebind=False)
    e1, e2 = flow1.runtime_authority_profile.model_dump(mode="json"), flow2.runtime_authority_profile.model_dump(mode="json")
    chk.ok("effective_profiles_differ", own_commit(e1) != own_commit(e2))
    out = run(flow2, w.p, w.did)
    refused_with(chk, "E1", out, ["runtime_authority_approval_mismatch"], "runtime-authority-reasons/0.1")
    chk.ok("binding_changed_code_not_emitted(ECB not consulted)", ["authorization_binding_changed"] not in out["new_refusal_reasons"])
    rec("Q3-E1", "CLASSIFICATION", claim="guard-first (approval); member not isolated", observed=out["new_refusal_reasons"])
    chk.done()


def test_Q3_E2_effective_reissued_joint(tmp_path):
    E, chk = H.env(), Check("Q3-E2")
    w = L.f5_world(E, tmp_path, "e2", t1=60, reg=10)
    flow1, dec = L.f5_mint(E, w)
    chk.ok("minted_authorized", dec.result == "authorized")
    src2 = H.Src(L.f5_material(E, {CT: 20}))
    flow2 = L.f5_flow(E, w, src=src2, rebind=True)  # approval re-issued against the NEW effective profile
    base, ecb, r_, rs = f5_live_diff(E, w, lambda sd: L.f5_flow(E, w, sd, src=src2), tmp_path, "e2live")
    chk.ok("live_world_mints_authorized", r_ == "authorized", reasons=rs)
    claim = claim_for(base, ecb, "effective_profile_digest")
    rec("Q3-E2", "CLASSIFICATION", claim=claim, base_diff=base, ecb_diff=ecb)
    chk.ok("base_diff_is_approval_commitment_and_catalogue_digest", sorted(base or []) == ["runtime_authority.approval_commitment", "runtime_authority.catalogue_digest"], base=base)
    chk.ok("ecb_diff_is_digest_effective_member_and_family_digest",
           sorted(ecb or []) == sorted([f"{ECBP}.digest", f"{ECBP}.members.effective_profile_digest", f"{ECBP}.members.families.0.effective_policy_digest"]), ecb=ecb)
    chk.ok("claim_is_joint_not_isolated", claim == "joint", claim=claim)
    out = run(flow2, w.p, w.did)
    refused_with(chk, "E2", out, ["authorization_binding_changed"], "runtime-authority-reasons/0.1")
    chk.done()


# ======================================================================================================================== Q2
def _two_worlds(E, tmp):
    w1 = L.domain_world(E, tmp, "d1", "customer-refunds")
    f1, dec1 = L.domain_mint(E, w1)
    w2 = L.domain_world(E, tmp, "d2", "other-domain")
    f2, dec2 = L.domain_mint(E, w2)
    return w1, f1, dec1, w2, f2, dec2


def test_Q2_A1_component(tmp_path):
    E, chk = H.env(), Check("Q2-A1")
    w1, f1, dec1, w2, f2, dec2 = _two_worlds(E, tmp_path)
    chk.ok("both_worlds_mint_authorized", dec1.result == "authorized" and dec2.result == "authorized", r1=list(dec1.reasons), r2=list(dec2.reasons))
    m1, m2 = H.member_of(w1.dir, w1.did), H.member_of(w2.dir, w2.did)
    exp1 = w1.manifest["actions"][0]["authority_context"]["authority_domain"]
    exp2 = w2.manifest["actions"][0]["authority_context"]["authority_domain"]
    chk.ok("worlds_have_distinct_manifest_domains", exp1 == "customer-refunds" and exp2 == "other-domain" and exp1 != exp2)
    chk.ok("member_d1_equals_manifest_domain", m1["members"]["scope"]["authority_domain"] == exp1, observed=m1["members"]["scope"]["authority_domain"])
    chk.ok("member_d2_equals_manifest_domain", m2["members"]["scope"]["authority_domain"] == exp2, observed=m2["members"]["scope"]["authority_domain"])
    chk.ok("member_diff_exactly_domain_leaf_and_digest", L.leaf_diff(m1, m2) == {"digest", "members.scope.authority_domain"}, diff=sorted(L.leaf_diff(m1, m2)))
    chk.ok("digest_d1_recomputed_independently", H.my_digest(m1["members"], m1["version"]) == m1["digest"])
    chk.ok("digest_d2_recomputed_independently", H.my_digest(m2["members"], m2["version"]) == m2["digest"])
    b1, b2 = L.binding_of(w1.dir, w1.did), L.binding_of(w2.dir, w2.did)
    base, ecb = L.split_diff(b1, b2)
    chk.ok("worlds_base_binding_diff_is_manifest_digest_and_proposal_commitment(dependency shown)", base == ["manifest_digest", "proposal_commitment"], base=base, ecb=ecb)
    chk.ok("classifier_D1_on_d2_workflow_is_mismatch(evidence-only)", f2.configuration_binding_status(f1.records.decision(w1.did)) == "mismatch")
    chk.ok("classifier_D2_on_d2_workflow_is_bound(evidence-only)", f2.configuration_binding_status(f2.records.decision(w2.did)) == "bound")
    chk.done()


def test_Q2_A2_natural_joint(tmp_path):
    E, chk = H.env(), Check("Q2-A2")
    w1, f1, dec1, w2, f2, dec2 = _two_worlds(E, tmp_path)
    # (i) un-rebuilt proposal P1 in a consistent d2 world, over a copy of the d1 store
    si = tmp_path / "nat_i"
    shutil.copytree(w1.dir, si)
    out_i = run(L.construct_domain(E, w2, si), w1.p, w1.did)
    refused_with(chk, "A2i[P1 in d2 world]", out_i, ["approval_operation_binding_mismatch", "manifest_digest_mismatch"])
    chk.ok("A2i:binding_changed_code_not_emitted(ECB not consulted)", ["authorization_binding_changed"] not in out_i["new_refusal_reasons"])
    # (ii) rebuilt consistent proposal P2 against D1 in the d2 world
    sii = tmp_path / "nat_ii"
    shutil.copytree(w1.dir, sii)
    out_ii = run(L.construct_domain(E, w2, sii), w2.p, w1.did)
    live, r_, rs = L.live_binding(E, lambda sd: L.construct_domain(E, w2, sd), w2.p, tmp_path / "nat_ii_live")
    base, ecb = L.split_diff(L.binding_of(w1.dir, w1.did), live)
    claim = claim_for(base, ecb, "scope.authority_domain")
    rec("Q2-A2", "CLASSIFICATION", claim=claim, route="P2 vs D1 in consistent d2 world", base_diff=base, ecb_diff=ecb)
    chk.ok("A2ii:base_diff_is_manifest_digest_and_proposal_commitment", base == ["manifest_digest", "proposal_commitment"], base=base)
    chk.ok("A2ii:ecb_diff_is_domain_leaf_and_digest", sorted(ecb) == sorted([f"{ECBP}.digest", f"{ECBP}.members.scope.authority_domain"]), ecb=ecb)
    chk.ok("A2ii:claim_is_joint", claim == "joint", claim=claim)
    refused_with(chk, "A2ii[P2 vs D1 in d2 world]", out_ii, ["authorization_binding_changed"])
    # (iii) the original A25(a) route (manifest domain edited + Registry re-signed, original resolver and proposal), reproduced with the original fixtures
    ctl = H.new_case(tmp_path, "f4", name="orig_route")
    try:
        flow = H.restart(ctl, {"domain": "other-domain"})
        out_iii = run(flow, ctl.fx.p, ctl.did)
        refused_with(chk, "A2iii[original A25(a) route]", out_iii, ["authority_domain_mismatch", "manifest_digest_mismatch"])
        chk.ok("A2iii:binding_changed_code_not_emitted", ["authorization_binding_changed"] not in out_iii["new_refusal_reasons"])
    except Exception as exc:
        chk.ok("A2iii:constructed", False, error=f"{type(exc).__name__}: {exc}"[:300])
    chk.done()


def test_Q2_A3_graft(tmp_path):
    E, chk = H.env(), Check("Q2-A3")
    w1, f1, dec1, w2, f2, dec2 = _two_worlds(E, tmp_path)
    chk.ok("both_worlds_mint_authorized", dec1.result == "authorized" and dec2.result == "authorized")
    pristine = tmp_path / "d2_pristine_copy"
    shutil.copytree(w2.dir, pristine)
    # control: the untouched d2 decision executes (same world, store layout, proposal and destination)
    ctl = tmp_path / "d2_control"
    shutil.copytree(w2.dir, ctl)
    accepted(chk, "A3c-d2-control", run(L.construct_domain(E, w2, ctl), w2.p, w2.did))
    # write-path neutrality control: graft the member of an independent, identical-domain d2 world (no semantic change)
    w2b = L.domain_world(E, tmp_path, "d2b", "other-domain")
    L.domain_mint(E, w2b)
    neu = tmp_path / "d2_neutral_graft"
    shutil.copytree(w2.dir, neu)
    L.graft(w2b.dir, w2b.did, neu, w2.did)
    accepted(chk, "A3n-neutral-graft", run(L.construct_domain(E, w2, neu), w2.p, w2.did))
    # GRAFT: donor member from d1 into the d2 decision
    g = tmp_path / "d2_graft"
    shutil.copytree(w2.dir, g)
    donor = L.graft(w1.dir, w1.did, g, w2.did)
    gm = H.member_of(g, w2.did)
    chk.ok("grafted_member_is_donor_verbatim", gm == donor == H.member_of(w1.dir, w1.did))
    chk.ok("grafted_member_digest_self_consistent", H.my_digest(gm["members"], gm["version"]) == gm["digest"])
    chk.ok("grafted_member_domain_is_d1", gm["members"]["scope"]["authority_domain"] == "customer-refunds")
    chk.ok("store_diff_vs_pristine_is_only_the_member", all(x.startswith("decisions.") and f"binding.runtime_authority.{KEY}" in x for x in L.leaf_diff(H.load_doc(pristine), H.load_doc(g))),
           diff=sorted(L.leaf_diff(H.load_doc(pristine), H.load_doc(g))))
    fg = L.construct_domain(E, w2, g)  # restart world d2 over the grafted store (admission via the production constructor and store reader)
    chk.ok("grafted_decision_reloads_via_store_reader", fg.records.decision(w2.did) is not None)
    chk.ok("classifier_on_grafted_is_mismatch_not_invalid(evidence-only)", fg.configuration_binding_status(fg.records.decision(w2.did)) == "mismatch")
    live, r_, rs = L.live_binding(E, lambda sd: L.construct_domain(E, w2, sd), w2.p, tmp_path / "graft_live")
    chk.ok("live_world_mints_authorized", r_ == "authorized", reasons=rs)
    base, ecb = L.split_diff(L.binding_of(g, w2.did), live)
    claim = claim_for(base, ecb, "scope.authority_domain")
    rec("Q2-A3", "CLASSIFICATION", claim=claim, label="GRAFT: isolated by store-level construction (unsigned store); not a natural-reachability claim", base_diff=base, ecb_diff=ecb)
    chk.ok("base_binding_diff_empty", base == [], base=base)
    chk.ok("member_diff_exactly_domain_leaf_plus_digest", sorted(ecb) == sorted([f"{ECBP}.digest", f"{ECBP}.members.scope.authority_domain"]), ecb=ecb)
    out = run(fg, w2.p, w2.did)
    refused_with(chk, "A3-graft", out, ["authorization_binding_changed"])
    chk.ok("binding_status_mismatch(evidence-only)", out.get("binding_status") == "mismatch")
    chk.ok("claim_is_isolated_end_to_end_by_graft", claim == "isolated end-to-end", claim=claim)
    chk.done()
