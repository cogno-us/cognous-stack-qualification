"""OCS-F3-Q240-BOUNDED-QUALIFICATION, host-profile cases FC-H1, FC-H2, FC-H3a, FC-H3b (WORKER B draft; frozen by the lead before first execution).
Subject: Control Plane 739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69 (PYTHONPATH=<cp>/src), Registry pin a40fe755 (OCS_REGISTRY_PIN_DIR, OCS_REQUIRE_REGISTRY_PIN=1), Python 3.11.18.
Same session lineage as the lead builder: NOT organizationally independent; technical qualification evidence only. Governing spec: spec/cases-host.md (assertion inventory).
Modelled on the merged D-1 host tests Q3-H0/H1/H2 (test_d1.py) and the D-1 convention (PROTOCOL-D1-v1.md): complementary binding diff (persisted vs live scratch mint),
base diff / ECB diff split, soft assertions, every assertion recorded (pass AND fail), a failing check against a pristine subject is an ADVERSE FINDING and is never revised.

Rules honoured here: no subject-side guard is disabled, patched or bypassed; no store write or graft (only reads of the run.json the subject wrote, and subject-side `decide`/`execute`/
claim calls); supported public interfaces only (constructors, decide, execute, materialize_local_execution_claim, configuration_binding_status); the only monkeypatch is the
D-1 synthetic clock (H.patch_clock); synthetic data; no network. EXPECTED VALUES ARE HARD-CODED LITERALS; none is computed from an observed value (the only computed oracles are the
harness's own independent sha256 commitments `own_commit`, as in D-1).

Evidence rows (D1_EVIDENCE_DIR/d1_evidence.jsonl), per case, every one with assertion_id, expected, observed, result:
  PRECONDITION_PASS / PRECONDITION_FAIL   validity preconditions (any FAIL => BLOCKED row and the test fails hard: the case is NOT interpreted)
  CHECK_PASS / CHECK_FAIL                 gating assertions (control C*, assertions A*)
  OBSERVATION (gating=false)              evidence-only rows E* (candidate's own classifier, restoration control, raw bookkeeping counts); never gate a verdict
  BLOCKED                                 fixture could not be built / control could not be issued / unhandled exception; raw detail retained
"""
from __future__ import annotations

import base64
import functools
import hashlib
import importlib
import os
import platform
import sys
import traceback
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import d1_lib as L  # noqa: E402
from d1_lib import Check, rec  # noqa: E402

H = L.H
TENANT = H.TENANT

# ---- hard-coded literals (frozen expectations and fixture constants) ----
AID = "urn:cognous:action:refund-issue-routine-v1"          # tba.tenant_proposal().action_id (verified at runtime by precondition P*)
T2_ACTION = "urn:cognous:action:refund-issue-high-v1"       # second host action of the class-unreadable host profile (as the developer fixture)
CLS_REV, CLS_IRR = "synthetic-reversible", "synthetic-irreversible"
OP_U = "refund-issue-unreadable"
V5_DOMAIN = b"ocs-reg/r08-v5/selection\n"
EXEC_MSG = "authorization-critical inputs changed before effect"
CLAIM_MSG = "authorization-critical inputs changed before claim issuance"
VOC = "runtime-authority-reasons/0.1"
CODE = "authorization_binding_changed"
APPR = "runtime_authority_approval_mismatch"
BASE_APPROVAL_CAT = ["runtime_authority.approval_commitment", "runtime_authority.catalogue_digest"]
ECB_DIGEST = "runtime_authority.effective_configuration.digest"
ECB_HOST = "runtime_authority.effective_configuration.members.host_profile_digest"
ECB_EFF = "runtime_authority.effective_configuration.members.effective_profile_digest"
ECB_FAM0 = "runtime_authority.effective_configuration.members.families.0.effective_policy_digest"
BOOKKEEPING_KEYS = ["check_events", "input_time_floors", "resolution_checks"]


# ======================================================================================================================== fixtures / plumbing
@pytest.fixture(scope="session", autouse=True)
def _preflight():
    E = H.env()
    root = Path(E.acp.__file__).resolve().parents[2]
    want = Path(os.environ["D1_CP_ROOT"]).resolve()
    assert root == want, f"imported agent_control_plane from {root}, expected {want}"
    import pydantic
    pin = H.pin_state()
    assert pin["head"] == H.EXPECTED_REGISTRY_HEAD and pin["require"] == "1", pin
    rec("PREFLIGHT", "OBSERVATION", label=os.environ.get("D1_LABEL"), acp=str(E.acp.__file__), cp_root=str(root), python=platform.python_version(), pydantic=pydantic.VERSION, pin=pin,
        suite="test_bq_host")


@pytest.fixture(autouse=True)
def _clock(monkeypatch):
    H.patch_clock(monkeypatch)


def own_commit(obj) -> str:
    """Independent re-computation of a profile commitment (sha256 over canonical JSON); not the candidate's profile_digest."""
    return "sha256:" + hashlib.sha256(H.canon(obj)).hexdigest()


class Cx:
    """Per-case recorder. P = precondition (failure => BLOCKED, case not interpreted); C/A = gating assertions; E = evidence-only observation (never gates)."""

    def __init__(self, case):
        self.case, self.chk, self.pre_fail = case, Check(case), []

    def P(self, pid, desc, expected, observed, **info):
        ok = observed == expected
        rec(self.case, "PRECONDITION_PASS" if ok else "PRECONDITION_FAIL", assertion_id=pid, check=f"{pid}:{desc}", expected=expected, observed=observed,
            result="PASS" if ok else "FAIL", **info)
        if not ok:
            self.pre_fail.append(pid)
        return ok

    def gate(self):
        if self.pre_fail:
            rec(self.case, "BLOCKED", phase="precondition", failed_preconditions=list(self.pre_fail),
                why="validity precondition not met; the case is BLOCKED and is not interpreted")
            pytest.fail(f"BLOCKED: {self.case}: preconditions failed {self.pre_fail}", pytrace=False)

    def A(self, aid, desc, expected, observed, **info):
        ok = observed == expected
        self.chk.ok(f"{aid}:{desc}", ok, assertion_id=aid, expected=expected, observed=observed, result="PASS" if ok else "FAIL", gating=True, **info)
        return ok

    def E(self, eid, desc, expected, observed, **info):
        self.chk.obs(f"{eid}:{desc}", assertion_id=eid, expected=expected, observed=observed, result="MATCH" if observed == expected else "DIVERGE", gating=False, **info)

    def O(self, oid, desc, **info):
        self.chk.obs(f"{oid}:{desc}", assertion_id=oid, gating=False, **info)

    def blocked(self, phase, **info):
        rec(self.case, "BLOCKED", phase=phase, **info)
        pytest.fail(f"BLOCKED: {self.case}: {phase}", pytrace=False)

    def done(self):
        self.chk.done()


def guarded(case):
    """Any unhandled exception inside a case body is recorded as BLOCKED (raw type/text/traceback retained) and fails the test hard; it is never a PASS and never swallowed."""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*a, **k):
            try:
                return fn(*a, **k)
            except AssertionError:
                raise
            except Exception as exc:  # noqa: BLE001  (pytest.fail/Failed is a BaseException and passes through)
                rec(case, "BLOCKED", phase="unhandled_exception", error=f"{type(exc).__name__}: {exc}"[:800], traceback=traceback.format_exc()[-3000:])
                pytest.fail(f"BLOCKED: {case}: unhandled {type(exc).__name__}", pytrace=False)
        return wrapper
    return deco


def run(flow, p, did):
    return H.jsonable(H.drive_execute(H.env(), flow, p, did))


def live_diff(E, w, mk_flow, tmp, name):
    """(base_diff, ecb_diff, live_result, live_reasons, live_binding): complementary diff of the PERSISTED binding of w.did vs the binding the LIVE world mints (scratch store)."""
    live, res_, rs = L.live_binding(E, mk_flow, w.p, Path(tmp) / name)
    if live is None:
        return None, None, res_, rs, None
    base, ecb = L.split_diff(L.binding_of(w.dir, w.did), live)
    return base, ecb, res_, rs, live


def classification(base, ecb, member_leaf):
    """D-1 decision rule: 'isolated end-to-end' iff base diff empty and the member diff is exactly {digest, member leaf}; else 'joint'."""
    want = sorted([ECB_DIGEST, "runtime_authority.effective_configuration.members." + member_leaf])
    return "isolated end-to-end" if base == [] and sorted(ecb or []) == want else "joint"


def exec_refusal_rows(cx, ids, out, codes):
    cx.A(ids[0], "raised_PermissionError", "PermissionError", out.get("raised"), detail=out)
    cx.A(ids[1], "exception_text_exact", EXEC_MSG, out.get("msg"))
    cx.A(ids[2], "exactly_one_new_durable_EffectTimeRefusal_with_exact_reasons", [sorted(codes)], out["new_refusal_reasons"])
    cx.A(ids[3], "refusal_reason_vocabulary", [VOC], out["new_refusal_vocab"])
    cx.A(ids[4], "no_attempt_row", 0, out["new_attempts"])
    cx.A(ids[5], "destination_never_called_and_unchanged", [0, True], [out["dest_calls"], out["dest_unchanged"]])


def exec_accept_rows(cx, ids, out):
    cx.A(ids[0], "executed_acknowledged_no_exception", ["acknowledged", None], [out.get("attempt_status"), out.get("raised")], detail=out)
    cx.A(ids[1], "no_refusal_row", [], out["new_refusal_reasons"])
    cx.A(ids[2], "destination_called_exactly_once", 1, out["dest_calls"])


def doc_delta(before, after):
    """(changed top-level keys, per-list-key length deltas) between two run.json documents (read-only snapshots)."""
    keys = sorted(set(before) | set(after))
    changed = [k for k in keys if before.get(k) != after.get(k)]
    deltas = {k: len(after.get(k) or []) - len(before.get(k) or []) for k in keys if isinstance(after.get(k, before.get(k)), list)}
    return changed, deltas


def claim_attempt(E, flow, w, store_dir, claim_id):
    """One call of the supported public claim interface; never raises. Returns a record of the call and of the store/destination before and after."""
    persisted = flow.records.decision(w.did)
    before, dest_before, calls_before = H.load_doc(store_dir), flow.destination.snapshot(), flow.destination.calls
    claim, exc = None, None
    try:
        claim = E.claim(flow, w.p, persisted, now=E.NOW, claim_id=claim_id)
    except Exception as e:  # noqa: BLE001  (recorded, classified by the caller)
        exc = e
    after, dest_after, calls_after = H.load_doc(store_dir), flow.destination.snapshot(), flow.destination.calls
    changed, deltas = doc_delta(before, after)
    return SimpleNamespace(claim=claim, exc=exc, persisted=persisted, before=before, after=after, changed=changed, deltas=deltas,
                           dest_unchanged=dest_before == dest_after, dest_calls=calls_after - calls_before)


# ---- F5 class-age world helpers come from d1_lib (f5_world, f5_flow, f5_mint, host_profile). Class-unreadable world helpers are new (below). ----
def host_unr(E, p, scoped_value):
    """HOST profile for the class-unreadable family: scoped action class T1 REVERSIBLE with on_unreadable=`scoped_value`; a second action, class T2 irreversible `refuse` (the shape of the
    developer fixture tests/test_f5_class_unreadable_governance.host_profile). Irreversible classes must already be `refuse` (host_class_defect), the D-1 class is therefore not reused."""
    actions = {p.action_id: E.ActionClass(class_id=CLS_REV, irreversible=False, max_status_age_seconds=60, on_unreadable=scoped_value),
               T2_ACTION: E.ActionClass(class_id=CLS_IRR, irreversible=True, max_status_age_seconds=120, on_unreadable="refuse")}
    return E.RuntimeAuthorityProfile(catalogue_version="synthetic-catalogue/1", actions=actions, producer_keys={"synthetic-validator": E.PUBLIC}, allow_synthetic_resolver=True)


def unr_material(E, classes: dict, *, consumer="consumer-test", op=OP_U):
    """Registry r08-v5 (family f5-action-class-unreadable-policy) selection: own construction following the Registry/developer builders; statement scope carries tenant/institution/domain."""
    v5f = importlib.import_module("registry_successor.v5_class_unreadable")
    payload = {v5f.F5U_FIELD: {k: classes[k] for k in sorted(classes)}}
    record = E.r.seal_record(dict(E.r.make_record(), contract_version="r08-v5", family=v5f.FAMILY_F5U, record_id="f5u-record", payload=payload))
    scope = {"tenant": TENANT, "institution": E.INSTITUTION, "authority_domain": E.AUTHORITY_DOMAIN}
    stmt = E.r.make_statement_v2(record, consumer_id=consumer, scope=scope, operation=op, effective=H.EFFECTIVE, issued_at="2026-10-01T00:00:00Z", family=v5f.FAMILY_F5U)
    sig = base64.b64encode(E.nb.crypto_sign(V5_DOMAIN + E.c.canonical_bytes(stmt), E.sk)[:64]).decode("ascii")
    selection = E.r.dumps(E.s.envelope(stmt, domain=V5_DOMAIN, contract="r08-v5", signature=sig, pub=E.pk))
    grant = E.v.AuthorityGrant(consumer, TENANT, E.INSTITUTION, E.AUTHORITY_DOMAIN, op)
    trust = E.v.TrustSnapshot("snap-test-1", 1, "2026-10-07T00:00:00Z", (E.v.IssuerEntry(E.s.KEY_ID, "issuer-test-1", "ed25519", E.pk, (grant,)),))
    return E.agegov.SelectionMaterial(E.r.dumps(record), selection, trust)


def unr_world(E, tmp, name, *, host_value, registry_value="refuse"):
    """Fresh class-unreadable world: HOST T1 on_unreadable=host_value, Registry value for T1 = registry_value. Returns SimpleNamespace(p,res,host,src,dir)."""
    d = Path(tmp) / name
    d.mkdir(parents=True, exist_ok=True)
    p = E.tba.tenant_proposal()
    res = E.tba.tenant_resolver_for(p)
    host = host_unr(E, p, host_value)
    L.prepare_runtime_authority(E, res, p, d / "_work", host)
    src = H.Src(unr_material(E, {CLS_REV: registry_value}))
    return SimpleNamespace(E=E, p=p, res=res, host=host, src=src, dir=d)


def unr_flow(E, w, store_dir=None, *, host=None, rebind=False):
    scope = E.GovernedScope("consumer-test", TENANT, w.p.action_id, OP_U)
    flow = E.ugov.GovernedClassUnreadableWorkflow(scope=scope, selection_source=w.src, verifier=E.ev.Ed25519Verifier(),
                                                  runtime_authority_profile=host if host is not None else w.host, construction_time=E.NOW,
                                                  **L.f5_base_kwargs(E, store_dir or w.dir, w.res))
    if rebind:
        E.bind_approval(w.res, flow.runtime_authority_profile)  # supported host duty: approvals are issued against the FINAL profile
    return flow


def unr_mint(E, w):
    flow = unr_flow(E, w, rebind=True)
    dec = flow.decide(w.p, now=E.NOW)
    w.did = dec.decision_id
    return flow, dec


# ======================================================================================================================== FC-H1
@guarded("FC-H1")
def test_FC_H1(tmp_path):
    """FC-H1: host_profile_digest on the CLAIM ISSUANCE leg, F5 class-age masked-host world (host age 60 -> 61 masked by Registry 10; approval NOT re-issued)."""
    E, cx = H.env(), Cx("FC-H1")
    from agent_control_plane.local_authority_effect import verify_local_execution_claim

    # ---- control world: unperturbed; a valid control claim must issue first (else BLOCKED, raw recorded) ----
    wc = L.f5_world(E, tmp_path, "h1c", t1=60, reg=10)
    fc1, dc = L.f5_mint(E, wc)
    cx.P("FC-H1-P01", "control_world_minted_authorized", "authorized", dc.result, reasons=list(dc.reasons))
    cx.P("FC-H1-P02", "proposal_action_id_is_the_frozen_literal", AID, wc.p.action_id)
    cx.gate()
    flow_c = L.f5_flow(E, wc)  # restart, identical host, same approval
    cbase, cecb, cres, crs, _ = live_diff(E, wc, lambda sd: L.f5_flow(E, wc, sd), tmp_path, "h1c_live")
    cx.P("FC-H1-P03", "control_live_world_mints_authorized", "authorized", cres, reasons=crs)
    cx.gate()
    cc = claim_attempt(E, flow_c, wc, wc.dir, "bq-fc-h1-control")
    if cc.exc is not None or cc.claim is None:
        cx.P("FC-H1-P04", "control_claim_issued_on_this_world", "issued", f"refused:{type(cc.exc).__name__}:{cc.exc}"[:300], raw_exception_type=type(cc.exc).__name__,
             raw_exception_text=str(cc.exc)[:500])
        cx.gate()
    cx.P("FC-H1-P04", "control_claim_issued_on_this_world", "issued", "issued")
    cx.A("FC-H1-C01", "control_live_binding_diff_base_empty", [], cbase)
    cx.A("FC-H1-C02", "control_live_binding_diff_ecb_empty", [], cecb)
    cx.A("FC-H1-C03", "control_claim_verifies", True, verify_local_execution_claim(cc.claim))
    cx.A("FC-H1-C04", "control_claim_bound_to_the_minted_decision", [wc.did, "bq-fc-h1-control"], [cc.claim.decision_id, cc.claim.claim_id])
    cx.A("FC-H1-C05", "control_claim_not_authorizing_by_possession", False, cc.claim.authorizing_by_possession)
    cx.A("FC-H1-C06", "control_exactly_one_claim_and_no_execution_side_effect", [1, 0, True], [1, cc.dest_calls, cc.dest_unchanged])
    cx.A("FC-H1-C07", "control_claim_wrote_no_refusal_attempt_or_decision_row", {"refusals": 0, "attempts": 0, "decisions": 0},
         {k: cc.deltas.get(k, 0) for k in ("refusals", "attempts", "decisions")})
    cx.E("FC-H1-E01", "control_classifier_bound(evidence-only)", "bound", flow_c.configuration_binding_status(flow_c.records.decision(wc.did)))
    cx.O("FC-H1-E02", "control_claim_type_and_bookkeeping(raw)", claim_type=type(cc.claim).__name__, deltas=cc.deltas, changed_keys=cc.changed)

    # ---- perturbed world: F5 class-age masked-host H1 world; host age 60 -> 61, Registry 10, approval NOT re-issued ----
    wp = L.f5_world(E, tmp_path, "h1p", t1=60, reg=10)
    flow1, dp = L.f5_mint(E, wp)
    cx.P("FC-H1-P05", "perturbed_world_minted_authorized", "authorized", dp.result, reasons=list(dp.reasons))
    cx.gate()
    host2 = L.host_profile(E, wp.p, 61)
    hd1, hd2 = wp.host.model_dump(mode="json"), host2.model_dump(mode="json")
    flow2 = L.f5_flow(E, wp, host=host2)  # restart over the same store, host edited, same Registry, approval NOT re-bound
    e1, e2 = flow1.runtime_authority_profile.model_dump(mode="json"), flow2.runtime_authority_profile.model_dump(mode="json")
    cx.P("FC-H1-P06", "host_class_ages_60_and_61", [60, 61], [hd1["actions"][AID]["max_status_age_seconds"], hd2["actions"][AID]["max_status_age_seconds"]])
    cx.P("FC-H1-P07", "host_profiles_differ_in_exactly_the_class_age_leaf", [f"actions.{AID}.max_status_age_seconds"], sorted(L.leaf_diff(hd1, hd2)))
    cx.P("FC-H1-P08", "effective_profile_dumps_equal(masked)", True, e1 == e2)
    cx.P("FC-H1-P09", "effective_profile_independent_commitments_equal", True, own_commit(e1) == own_commit(e2))
    cx.P("FC-H1-P10", "host_profile_independent_commitments_differ", True, own_commit(hd1) != own_commit(hd2))
    cx.P("FC-H1-P11", "effective_class_age_is_the_registry_value_in_both", [10, 10], [e1["actions"][AID]["max_status_age_seconds"], e2["actions"][AID]["max_status_age_seconds"]])
    base, ecb, lres, lrs, live = live_diff(E, wp, lambda sd: L.f5_flow(E, wp, sd, host=host2), tmp_path, "h1p_live")
    cx.P("FC-H1-P12", "live_world_with_edited_host_mints_authorized", "authorized", lres, reasons=lrs)
    cx.gate()
    ra_p, ra_l = L.binding_of(wp.dir, wp.did)["runtime_authority"], live["runtime_authority"]
    cx.P("FC-H1-P13", "catalogue_digest_and_effective_profile_digest_equal_across_worlds",
         [True, True, True],
         [ra_p["catalogue_digest"] == ra_l["catalogue_digest"], ra_p["effective_configuration"]["members"]["effective_profile_digest"] == ra_l["effective_configuration"]["members"]["effective_profile_digest"],
          ra_p["catalogue_digest"] == own_commit(e1)])
    cx.gate()

    # ---- the case: claim issuance on the rebuilt, host-edited workflow ----
    cl = claim_attempt(E, flow2, wp, wp.dir, "bq-fc-h1-perturbed")
    exc_type = None if cl.exc is None else type(cl.exc).__name__
    exc_text = None if cl.exc is None else str(cl.exc)
    cx.A("FC-H1-A01", "base_binding_diff_empty", [], base)
    cx.A("FC-H1-A02", "ecb_diff_exactly_digest_and_host_profile_digest", sorted([ECB_DIGEST, ECB_HOST]), sorted(ecb or []))
    cx.A("FC-H1-A03", "claim_issuance_raised_exactly_PermissionError", "PermissionError", exc_type, exact_type_is_PermissionError=(cl.exc is not None and type(cl.exc) is PermissionError))
    cx.A("FC-H1-A04", "no_claim_emitted", True, cl.claim is None)
    cx.A("FC-H1-A05", "exception_text_exact_claim_issuance_text", CLAIM_MSG, exc_text)
    cx.A("FC-H1-A06", "claim_path_does_not_name_authorization_binding_changed", False, CODE in (exc_text or ""))
    cx.A("FC-H1-A07", "no_durable_EffectTimeRefusal_or_refusal_write", 0, cl.deltas.get("refusals", 0))
    cx.A("FC-H1-A08", "no_attempt_row", 0, cl.deltas.get("attempts", 0))
    cx.A("FC-H1-A09", "no_decision_observation_reconciliation_or_closeout_rows", {"decisions": 0, "observations": 0, "reconciliations": 0, "closeouts": 0},
         {k: cl.deltas.get(k, 0) for k in ("decisions", "observations", "reconciliations", "closeouts")})
    cx.A("FC-H1-A10", "destination_never_called_and_unchanged", [0, True], [cl.dest_calls, cl.dest_unchanged])
    cx.A("FC-H1-A11", "store_changes_confined_to_claim_stage_bookkeeping_keys", [], sorted(set(cl.changed) - set(BOOKKEEPING_KEYS)))
    cx.A("FC-H1-A12", "exactly_one_new_resolution_check_row", 1, cl.deltas.get("resolution_checks", 0))
    new_rc = (cl.after.get("resolution_checks") or [])[len(cl.before.get("resolution_checks") or []):]
    cx.A("FC-H1-A13", "new_resolution_check_is_stage_claim_with_no_reasons", [["claim", []]], [[r.get("stage"), r.get("reasons")] for r in new_rc])
    cx.A("FC-H1-A14", "persisted_decision_unchanged_after_refusal", True, flow2.records.decision(wp.did) == cl.persisted)
    cx.E("FC-H1-E03", "classifier_mismatch(evidence-only)", "mismatch", flow2.configuration_binding_status(cl.persisted))
    cx.O("FC-H1-E04", "perturbed_bookkeeping_and_classification(raw)", deltas=cl.deltas, changed_keys=cl.changed, claim=classification(base, ecb, "host_profile_digest"),
         base_diff=base, ecb_diff=ecb)
    # restoration control (evidence-only): restoring the original host over the SAME store can still issue a claim, so the refusal above is attributable to the host edit, not to store state
    flow_r = L.f5_flow(E, wp)
    cr = claim_attempt(E, flow_r, wp, wp.dir, "bq-fc-h1-restore")
    cx.E("FC-H1-E05", "restoration_control_same_store_original_host_issues_claim(evidence-only)", "issued", "issued" if (cr.exc is None and cr.claim is not None) else f"refused:{type(cr.exc).__name__}:{cr.exc}"[:200])
    cx.done()


# ======================================================================================================================== FC-H2
@guarded("FC-H2")
def test_FC_H2(tmp_path):
    """FC-H2: second masked-host workflow, EXECUTE. GovernedClassUnreadableWorkflow, REVERSIBLE host class T1, host on_unreadable `bounded_tolerance` -> `refuse` masked by the Registry r08-v5
    value `refuse` (compose_unreadable overwrites every action's on_unreadable with the effective map); approval NOT re-issued."""
    E, cx = H.env(), Cx("FC-H2")

    # ---- control world: unperturbed executes exactly once ----
    wc = unr_world(E, tmp_path, "h2c", host_value="bounded_tolerance")
    fc1, dc = unr_mint(E, wc)
    cx.P("FC-H2-P01", "control_world_minted_authorized", "authorized", dc.result, reasons=list(dc.reasons))
    cx.P("FC-H2-P02", "proposal_action_id_is_the_frozen_literal", AID, wc.p.action_id)
    cx.gate()
    flow_c = unr_flow(E, wc)  # restart, identical host
    cbase, cecb, cres, crs, _ = live_diff(E, wc, lambda sd: unr_flow(E, wc, sd), tmp_path, "h2c_live")
    cx.P("FC-H2-P03", "control_live_world_mints_authorized", "authorized", cres, reasons=crs)
    cx.gate()
    cx.A("FC-H2-C01", "control_live_binding_diff_base_empty", [], cbase)
    cx.A("FC-H2-C02", "control_live_binding_diff_ecb_empty", [], cecb)
    out_c = run(flow_c, wc.p, wc.did)
    exec_accept_rows(cx, ["FC-H2-C03", "FC-H2-C04", "FC-H2-C05"], out_c)
    cx.E("FC-H2-E01", "control_classifier_bound(evidence-only)", "bound", out_c.get("binding_status"))

    # ---- perturbed world: host T1 on_unreadable bounded_tolerance (mint) -> refuse (rebuilt), Registry `refuse`, approval NOT re-issued ----
    wp = unr_world(E, tmp_path, "h2p", host_value="bounded_tolerance")
    flow1, dp = unr_mint(E, wp)
    cx.P("FC-H2-P04", "perturbed_world_minted_authorized", "authorized", dp.result, reasons=list(dp.reasons))
    cx.gate()
    host2 = host_unr(E, wp.p, "refuse")
    hd1, hd2 = wp.host.model_dump(mode="json"), host2.model_dump(mode="json")
    flow2 = unr_flow(E, wp, host=host2)  # restart over the same store, host edited, same Registry material, approval NOT re-bound
    e1, e2 = flow1.runtime_authority_profile.model_dump(mode="json"), flow2.runtime_authority_profile.model_dump(mode="json")
    cx.P("FC-H2-P05", "host_scoped_class_is_reversible_in_both", [False, False], [hd1["actions"][AID]["irreversible"], hd2["actions"][AID]["irreversible"]])
    cx.P("FC-H2-P06", "host_scoped_on_unreadable_values", ["bounded_tolerance", "refuse"], [hd1["actions"][AID]["on_unreadable"], hd2["actions"][AID]["on_unreadable"]])
    cx.P("FC-H2-P07", "host_profiles_differ_in_exactly_the_scoped_on_unreadable_leaf", [f"actions.{AID}.on_unreadable"], sorted(L.leaf_diff(hd1, hd2)))
    cx.P("FC-H2-P08", "effective_profile_dumps_equal(masked)", True, e1 == e2)
    cx.P("FC-H2-P09", "effective_profile_independent_commitments_equal", True, own_commit(e1) == own_commit(e2))
    cx.P("FC-H2-P10", "host_profile_independent_commitments_differ", True, own_commit(hd1) != own_commit(hd2))
    cx.P("FC-H2-P11", "effective_scoped_on_unreadable_is_the_registry_value_in_both", ["refuse", "refuse"], [e1["actions"][AID]["on_unreadable"], e2["actions"][AID]["on_unreadable"]])
    base, ecb, lres, lrs, live = live_diff(E, wp, lambda sd: unr_flow(E, wp, sd, host=host2), tmp_path, "h2p_live")
    cx.P("FC-H2-P12", "live_world_with_edited_host_mints_authorized", "authorized", lres, reasons=lrs)
    cx.gate()
    ra_p, ra_l = L.binding_of(wp.dir, wp.did)["runtime_authority"], live["runtime_authority"]
    mp, ml = ra_p["effective_configuration"]["members"], ra_l["effective_configuration"]["members"]
    cx.P("FC-H2-P13", "catalogue_digest_effective_profile_digest_and_family_digest_equal_across_worlds",
         [True, True, True, True],
         [ra_p["catalogue_digest"] == ra_l["catalogue_digest"], mp["effective_profile_digest"] == ml["effective_profile_digest"],
          mp["families"][0]["effective_policy_digest"] == ml["families"][0]["effective_policy_digest"], ra_p["catalogue_digest"] == own_commit(e1)])
    cx.P("FC-H2-P14", "family_row_is_class_unreadable_only", [["class_unreadable"], ["class_unreadable"]], [[r["slot"] for r in mp["families"]], [r["slot"] for r in ml["families"]]])
    cx.gate()

    # ---- the case: execute the original decision on the host-edited workflow ----
    cx.A("FC-H2-A01", "base_binding_diff_empty", [], base)
    cx.A("FC-H2-A02", "ecb_diff_exactly_digest_and_host_profile_digest", sorted([ECB_DIGEST, ECB_HOST]), sorted(ecb or []))
    out = run(flow2, wp.p, wp.did)
    exec_refusal_rows(cx, ["FC-H2-A03", "FC-H2-A04", "FC-H2-A05", "FC-H2-A06", "FC-H2-A07", "FC-H2-A08"], out, [CODE])
    cx.E("FC-H2-E02", "classifier_mismatch(evidence-only)", "mismatch", out.get("binding_status"))
    cx.O("FC-H2-E03", "classification(raw)", claim=classification(base, ecb, "host_profile_digest"), base_diff=base, ecb_diff=ecb)
    cx.done()


# ======================================================================================================================== FC-H3 (contrast control; NEVER isolating)
def _h3_world(E, cx, tmp_path, name, rebind):
    """F5 class-age world, host age 60 at mint, Registry 10 (effective 10); rebuilt with host age 5 (effective min(5,10)=5: NOT masked). rebind=True re-issues the approval against the new effective profile."""
    w = L.f5_world(E, tmp_path, name, t1=60, reg=10)
    flow1, dec = L.f5_mint(E, w)
    cx.P(f"{cx.case}-P01", "minted_authorized", "authorized", dec.result, reasons=list(dec.reasons))
    cx.gate()
    host2 = L.host_profile(E, w.p, 5)
    hd1, hd2 = w.host.model_dump(mode="json"), host2.model_dump(mode="json")
    flow2 = L.f5_flow(E, w, host=host2, rebind=rebind)
    e1, e2 = flow1.runtime_authority_profile.model_dump(mode="json"), flow2.runtime_authority_profile.model_dump(mode="json")
    cx.P(f"{cx.case}-P02", "proposal_action_id_is_the_frozen_literal", AID, w.p.action_id)
    cx.P(f"{cx.case}-P03", "host_class_ages_60_and_5", [60, 5], [hd1["actions"][AID]["max_status_age_seconds"], hd2["actions"][AID]["max_status_age_seconds"]])
    cx.P(f"{cx.case}-P04", "host_profiles_differ_in_exactly_the_class_age_leaf", [f"actions.{AID}.max_status_age_seconds"], sorted(L.leaf_diff(hd1, hd2)))
    cx.P(f"{cx.case}-P05", "effective_class_age_changes_NOT_masked", [10, 5], [e1["actions"][AID]["max_status_age_seconds"], e2["actions"][AID]["max_status_age_seconds"]])
    cx.P(f"{cx.case}-P06", "effective_profile_independent_commitments_differ", True, own_commit(e1) != own_commit(e2))
    cx.P(f"{cx.case}-P07", "host_profile_independent_commitments_differ", True, own_commit(hd1) != own_commit(hd2))
    cx.gate()
    return w, host2, flow2


@guarded("FC-H3a")
def test_FC_H3a(tmp_path):
    """FC-H3a (contrast; does NOT isolate host_profile_digest): unmasked host edit 60 -> 5 under Registry 10, approval NOT re-issued. Expected guard-first: only runtime_authority_approval_mismatch."""
    E, cx = H.env(), Cx("FC-H3a")
    w, host2, flow2 = _h3_world(E, cx, tmp_path, "h3a", rebind=False)
    out = run(flow2, w.p, w.did)
    exec_refusal_rows(cx, ["FC-H3a-A01", "FC-H3a-A02", "FC-H3a-A03", "FC-H3a-A04", "FC-H3a-A05", "FC-H3a-A06"], out, [APPR])
    cx.A("FC-H3a-A07", "authorization_binding_changed_absent_from_every_new_refusal", False, any(CODE in r for r in out["new_refusal_reasons"]))
    cx.E("FC-H3a-E01", "classifier_mismatch(evidence-only; says nothing about guard order)", "mismatch", out.get("binding_status"))
    rec("FC-H3a", "CLASSIFICATION", claim="guard-first (approval); host_profile_digest NOT isolated; the ECB was not the refusing comparison", observed=out["new_refusal_reasons"])
    cx.done()


@guarded("FC-H3b")
def test_FC_H3b(tmp_path):
    """FC-H3b (contrast; does NOT isolate host_profile_digest): unmasked host edit 60 -> 5 under Registry 10, approval re-issued against the new effective profile. Expected JOINT."""
    E, cx = H.env(), Cx("FC-H3b")
    w, host2, flow2 = _h3_world(E, cx, tmp_path, "h3b", rebind=True)
    base, ecb, lres, lrs, live = live_diff(E, w, lambda sd: L.f5_flow(E, w, sd, host=host2), tmp_path, "h3b_live")
    cx.P("FC-H3b-P08", "live_world_after_approval_reissue_mints_authorized", "authorized", lres, reasons=lrs)
    cx.gate()
    cls = classification(base, ecb, "host_profile_digest")
    cx.A("FC-H3b-A01", "base_binding_diff_is_approval_commitment_and_catalogue_digest", BASE_APPROVAL_CAT, sorted(base or []))
    cx.A("FC-H3b-A02", "ecb_diff_is_digest_host_effective_and_family_digest", sorted([ECB_DIGEST, ECB_HOST, ECB_EFF, ECB_FAM0]), sorted(ecb or []))
    cx.A("FC-H3b-A03", "classification_is_joint_not_isolated", "joint", cls)
    out = run(flow2, w.p, w.did)
    exec_refusal_rows(cx, ["FC-H3b-A04", "FC-H3b-A05", "FC-H3b-A06", "FC-H3b-A07", "FC-H3b-A08", "FC-H3b-A09"], out, [CODE])
    cx.E("FC-H3b-E01", "classifier_mismatch(evidence-only)", "mismatch", out.get("binding_status"))
    rec("FC-H3b", "CLASSIFICATION", claim=cls, base_diff=base, ecb_diff=ecb, label="contrast control: refusal is JOINT; host_profile_digest is not isolated by this case")
    cx.done()
