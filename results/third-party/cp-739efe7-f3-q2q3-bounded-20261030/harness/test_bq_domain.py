"""BOUNDED-v1 case N-CLAIM-JOINT (Worker D, authority-domain qualification): natural JOINT refusal on the CLAIM ISSUANCE leg for scope.authority_domain.

Subject: Control Plane 739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69, Registry pin a40fe755, Python 3.11.18. Same session lineage as the lead: NOT independent.
Governing spec: spec/cases-domain.md (this file implements its ASSERTION INVENTORY 1:1; every expected value below is a hard-coded literal, none is computed from an observation).

This is JOINT evidence. It does NOT establish independently isolated authority_domain evidence (the base binding differs in {manifest_digest, proposal_commitment} too).
Nothing here disables, patches, bypasses or grafts anything: supported public interfaces only (decide, GovernedAgeWorkflow restart over a COPY of a genuine store,
materialize_local_execution_claim, provision_local_execution_claim with a recording sink, verify_local_execution_claim). No direct store write. Synthetic data; no network.

Evidence rows: one row per assertion through d1_lib.rec (case/kind/t) with extra keys protocol, run, case_id, assertion_id, bq_kind, expected, observed, result.
A failing PRECONDITION (P*) or inline CONTROL (C01) is BLOCKED (case not interpreted); a failing assertion (A*) with all preconditions held is FAIL.
"""
from __future__ import annotations

import os
import platform
import shutil
import sys
import traceback
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import d1_lib as L  # noqa: E402

H = L.H
KEY = H.KEY
ECBP = "runtime_authority." + KEY
CASE = "N-CLAIM-JOINT"
PROTOCOL = os.environ.get("BQ_PROTOCOL", "OCS-F3-Q2Q3-BOUNDED-v1")

# ---------------------------------------------------------------------------------------------------------------- frozen expected literals
X_DOMAIN = "customer-refunds"
Y_DOMAIN = "other-domain"
MSG_CLAIM = "authorization-critical inputs changed before claim issuance"          # local_authority_effect.py:458 (generic; also used for base reasons)
BASE_EXP = ["manifest_digest", "proposal_commitment"]                                # as D-1 Q2-A1/A2(ii) observed
ECB_EXP = sorted([ECBP + ".digest", ECBP + ".members.scope.authority_domain"])      # exactly digest + the domain leaf
C1_REASONS = ["approval_operation_binding_mismatch", "manifest_digest_mismatch"]    # as D-1 Q2-A2(i) (bounded.py:2619, 2509-2510), sorted
CLAIM_PROFILE_V1 = "urn:cognous:profiles:local-authority-effect:0.1.0-proposed"     # local_authority_effect.py:31
CLAIM_CODE_NAME = "authorization_binding_changed"


# ---------------------------------------------------------------------------------------------------------------- fixtures
@pytest.fixture(scope="session", autouse=True)
def _bq_domain_preflight():
    E = H.env()
    root = Path(E.acp.__file__).resolve().parents[2]
    want = Path(os.environ.get("BQ_CP_ROOT") or os.environ["D1_CP_ROOT"]).resolve()
    assert root == want, f"imported agent_control_plane from {root}, expected {want}"
    import pydantic
    pin = H.pin_state()
    assert pin["head"] == H.EXPECTED_REGISTRY_HEAD and pin["require"] == "1", pin
    L.rec(CASE, "OBSERVATION", check="PREFLIGHT", protocol=PROTOCOL, run=_run(), acp=str(E.acp.__file__), cp_root=str(root), python=platform.python_version(),
          pydantic=pydantic.VERSION, pin=pin)


@pytest.fixture(autouse=True)
def _bq_domain_clock(monkeypatch):
    H.patch_clock(monkeypatch)


def _run():
    return os.environ.get("BQ_LABEL") or os.environ.get("D1_LABEL")


# ---------------------------------------------------------------------------------------------------------------- evidence instrument
class BQ:
    """One evidence row per assertion; expected is a literal supplied by the caller, result is observed == expected (plain equality)."""

    def __init__(self, test):
        self.test, self.fails, self.blocked = test, [], []

    def _row(self, aid, bq_kind, desc, expected, observed, ok, **info):
        L.rec(CASE, "CHECK_PASS" if ok else "CHECK_FAIL", check=aid, protocol=PROTOCOL, run=_run(), case_id=CASE, test=self.test, assertion_id=aid, bq_kind=bq_kind,
              desc=desc, expected=expected, observed=observed, result="PASS" if ok else "FAIL", **info)

    def pre(self, aid, desc, expected, observed, **info):
        ok = observed == expected
        self._row(f"{CASE}-{aid}", "PRECONDITION" if not aid.endswith("C01") else "CONTROL", desc, expected, observed, ok, **info)
        if not ok:
            self.blocked.append(aid)
        return ok

    def ok(self, aid, desc, expected, observed, **info):
        ok = observed == expected
        self._row(f"{CASE}-{aid}", "ASSERTION", desc, expected, observed, ok, **info)
        if not ok:
            self.fails.append(aid)
        return ok

    def obs(self, aid, desc, **info):
        L.rec(CASE, "OBSERVATION", check=f"{CASE}-{aid}", protocol=PROTOCOL, run=_run(), case_id=CASE, test=self.test, assertion_id=f"{CASE}-{aid}", bq_kind="OBSERVATION",
              desc=desc, result="n/a", **info)

    def snap(self, aid, desc, **info):
        L.rec(CASE, "SNAPSHOT", check=f"{CASE}-{aid}", protocol=PROTOCOL, run=_run(), case_id=CASE, test=self.test, assertion_id=f"{CASE}-{aid}", bq_kind="SNAPSHOT",
              desc=desc, result="n/a", **info)

    def exc(self, aid, exc, tb):
        L.rec(CASE, "EXCEPTION", check=f"{CASE}-{aid}", protocol=PROTOCOL, run=_run(), case_id=CASE, test=self.test, assertion_id=f"{CASE}-{aid}", bq_kind="EXCEPTION",
              exc_type=type(exc).__name__, exc_str=str(exc), traceback=tb, result="n/a")

    def gate(self):
        """BLOCKED: a validity precondition or inline control failed; the case is NOT interpreted and no outcome assertion is evaluated."""
        if self.blocked:
            L.rec(CASE, "BLOCKED", check=f"{CASE}-BLOCKED", protocol=PROTOCOL, run=_run(), case_id=CASE, test=self.test, failed_preconditions=list(self.blocked), result="BLOCKED")
            pytest.fail(f"{CASE}/{self.test}: BLOCKED, failed preconditions {self.blocked}", pytrace=False)

    def done(self):
        assert not self.fails, f"{CASE}/{self.test}: failed assertions {self.fails}"


# ---------------------------------------------------------------------------------------------------------------- helpers
def _commit(E, p):
    return E.B.commitment(p.model_dump(mode="json", exclude_none=False))


def _two_worlds(E, tmp, chk):
    """World X (customer-refunds) and world Y (other-domain), each genuinely minted. Records P01..P04; gates."""
    try:
        w1 = L.domain_world(E, tmp, "x", X_DOMAIN)
        f1, dec1 = L.domain_mint(E, w1)
        w2 = L.domain_world(E, tmp, "y", Y_DOMAIN)
        f2, dec2 = L.domain_mint(E, w2)
    except Exception as exc:  # fixture could not be built: BLOCKED, never interpreted
        chk.exc("P00", exc, traceback.format_exc())
        chk.pre("P00", "worlds X and Y construct and mint without raising", None, f"{type(exc).__name__}: {exc}"[:300])
        chk.gate()
        raise
    chk.pre("P01", "world X mints an authorized decision", {"result": "authorized", "reasons": []}, {"result": dec1.result, "reasons": list(dec1.reasons)})
    chk.pre("P02", "world Y mints an authorized decision for its own rebuilt proposal", {"result": "authorized", "reasons": []}, {"result": dec2.result, "reasons": list(dec2.reasons)})
    chk.pre("P03", "manifest authority_domain of X and Y", [X_DOMAIN, Y_DOMAIN],
            [w1.manifest["actions"][0]["authority_context"]["authority_domain"], w2.manifest["actions"][0]["authority_context"]["authority_domain"]])
    cx, cy = _commit(E, w1.p), _commit(E, w2.p)
    approvals_y = sorted({a.proposal_commitment for a in w2.res.approvals.values()})
    chk.pre("P04", "Y approvals are re-issued: every Y approval is bound to the Y proposal commitment, which differs from the X proposal commitment; Y proposal carries H(M_Y)",
            {"y_approvals_bound_to_Y_proposal": True, "X_and_Y_proposal_commitments_differ": True, "Y_manifest_digest_is_commitment_of_Y_manifest": True,
             "X_manifest_digest_differs_from_Y": True},
            {"y_approvals_bound_to_Y_proposal": approvals_y == [cy], "X_and_Y_proposal_commitments_differ": cx != cy,
             "Y_manifest_digest_is_commitment_of_Y_manifest": w2.p.manifest_digest == E.B.commitment(w2.manifest),
             "X_manifest_digest_differs_from_Y": w1.p.manifest_digest != w2.p.manifest_digest})
    chk.gate()
    return w1, f1, dec1, w2, f2, dec2


def _doc_deltas(before, after):
    keys = set(before) | set(after)
    out = {}
    for k in sorted(keys):
        b, a = before.get(k), after.get(k)
        if isinstance(a, list) or isinstance(b, list):
            out[k] = len(a or []) - len(b or [])
    return out


def _nonzero(d):
    return {k: v for k, v in d.items() if v != 0}


def _claim_summary(c):
    if c is None:
        return None
    return {"type": type(c).__name__, "claim_id": c.claim_id, "decision_id": c.decision_id, "effect_id": c.effect_id, "authority_domain": c.authority_domain,
            "institution_id": c.institution_id, "manifest_digest": c.manifest_digest, "tenant_id": getattr(c, "tenant_id", None), "profile": c.profile,
            "operation_commitment": c.operation_commitment, "claim_commitment": c.claim_commitment}


def run_leg(E, route, flow, p, did, claim_id, store_dir, chk, label):
    """ONE claim-issuance call through a supported public interface over the store in `store_dir`. route: 'materialize' | 'provision' (recording sink).
    Returns the observed leg record. Writes only what the production claim path writes."""
    from agent_control_plane import local_authority_effect as LAE
    persisted = flow.records.decision(did)
    before_doc, before = H.load_doc(store_dir), H.snap_state(flow, did)
    sink = []
    claim, exc, tb = None, None, None
    try:
        if route == "provision":
            claim = LAE.provision_local_execution_claim(flow, p, persisted, provision=sink.append, now=E.NOW, claim_id=claim_id)
        else:
            claim = LAE.materialize_local_execution_claim(flow, p, persisted, now=E.NOW, claim_id=claim_id)
    except Exception as e:  # classified by the caller
        exc, tb = e, traceback.format_exc()
        chk.exc(f"{label}.exc", e, tb)
    after_doc, after = H.load_doc(store_dir), H.snap_state(flow, did)
    deltas = _doc_deltas(before_doc, after_doc)
    new_checks = after_doc.get("resolution_checks", [])[len(before_doc.get("resolution_checks", [])):]
    verified = None
    if claim is not None:
        try:
            verified = bool(LAE.verify_local_execution_claim(claim))
        except Exception:
            verified = False
    leg = SimpleNamespace(route=route, claim=claim, exc=exc, exc_type=(type(exc).__name__ if exc is not None else None), exc_str=(str(exc) if exc is not None else None),
                          sink=sink, deltas=deltas, nonzero=_nonzero(deltas), new_checks=new_checks, before_doc=before_doc, after_doc=after_doc,
                          calls=after["calls"] - before["calls"], dest_unchanged=after["dest"] == before["dest"], verified=verified,
                          decisions_equal=before_doc.get("decisions") == after_doc.get("decisions"), keys_equal=set(before_doc) == set(after_doc),
                          floors_equal=before_doc.get("input_time_floors") == after_doc.get("input_time_floors"))
    chk.snap(f"{label}.leg", f"claim leg {label} via {route}: store deltas, new ResolutionCheck rows, destination, sink", route=route, claim=_claim_summary(claim), verified=verified,
             exc_type=leg.exc_type, exc_str=leg.exc_str, store_deltas=deltas, new_resolution_checks=[{"stage": c["stage"], "reasons": c["reasons"]} for c in new_checks],
             dest_calls_delta=leg.calls, dest_unchanged=leg.dest_unchanged, sink_calls=len(sink), decisions_equal=leg.decisions_equal, top_level_keys_equal=leg.keys_equal,
             input_time_floors_equal=leg.floors_equal, count_before={k: len(v) for k, v in before_doc.items() if isinstance(v, list)},
             count_after={k: len(v) for k, v in after_doc.items() if isinstance(v, list)})
    return leg


def _row_state(leg):
    if len(leg.new_checks) != 1:
        return {"n_new": len(leg.new_checks)}
    c = leg.new_checks[0]
    return {"n_new": 1, "stage": c["stage"], "reasons": list(c["reasons"])}


def _copy(src, dst):
    shutil.copytree(src, dst)
    return dst


def claim_for(base, ecb):
    return "isolated end-to-end" if base == [] and sorted(ecb) == ECB_EXP else "joint"


def _issued_expectation_checks(chk, E, w, leg, aid_prefix, claim_id, sink_expected, domain):
    """Shared control assertions (an unperturbed claim issues exactly one claim)."""
    c = leg.claim
    chk.ok(f"{aid_prefix}A01", "unperturbed claim is issued (a claim object is returned, no exception)", {"claim_type": "TenantLocalExecutionClaim", "raised": None},
           {"claim_type": type(c).__name__ if c is not None else None, "raised": leg.exc_type}, exc=leg.exc_str)
    chk.ok(f"{aid_prefix}A02", "verify_local_execution_claim(claim) is True", True, leg.verified)
    chk.ok(f"{aid_prefix}A03", "claim binds the minted decision, the host domain, the manifest digest, the tenant, the claim id and the v0.1 profile",
           {"decision_id": w.did, "authority_domain": domain, "manifest_digest": w.p.manifest_digest, "tenant_id": H.TENANT, "claim_id": claim_id, "profile": CLAIM_PROFILE_V1},
           None if c is None else {"decision_id": c.decision_id, "authority_domain": c.authority_domain, "manifest_digest": c.manifest_digest, "tenant_id": getattr(c, "tenant_id", None),
                                   "claim_id": c.claim_id, "profile": c.profile})
    chk.ok(f"{aid_prefix}A04", "exactly one new ResolutionCheck row, stage claim, reasons [] (claim path wrote its pre-existing journal row; no base reason)",
           {"n_new": 1, "stage": "claim", "reasons": []}, _row_state(leg))
    chk.ok(f"{aid_prefix}A05", "no other store collection changed (no refusal, attempt, decision, observation, reconciliation, new ledger)", {"resolution_checks": 1}, leg.nonzero)
    chk.ok(f"{aid_prefix}A06", "persisted decisions section byte-equal before and after", True, leg.decisions_equal)
    chk.ok(f"{aid_prefix}A07", "destination never called and unchanged (claim issuance does not effect)", {"calls": 0, "unchanged": True}, {"calls": leg.calls, "unchanged": leg.dest_unchanged})
    chk.ok(f"{aid_prefix}A08", "sink called exactly as expected (materialize: no sink; provision: once, with the very claim returned)",
           sink_expected, {"calls": len(leg.sink), "is_returned_claim": (leg.sink == [c]) if leg.sink else None} if leg.route == "provision" else {"calls": 0, "is_returned_claim": None})


# ====================================================================================================================== main
def test_N_CLAIM_JOINT_main(tmp_path):
    """Decide/mint under X; rebuild a valid Y workflow (manifest Y, Registry signed for Y, resolver/records Y, proposal P_Y with H(M_Y), approvals re-issued for P_Y) over a COPY
    of the genuine X store; issue a claim for P_Y against the persisted decision D_X. Frozen: PermissionError(MSG_CLAIM), no claim, no refusal write, sink never called,
    destination untouched, base diff exactly {manifest_digest, proposal_commitment}, ECB diff exactly {digest, members.scope.authority_domain}, classification 'joint'."""
    E, chk = H.env(), BQ("main")
    w1, f1, dec1, w2, f2, dec2 = _two_worlds(E, tmp_path, chk)

    # P05: the Y world is a valid, genuinely-minting world for P_Y; its minted binding is the live binding of the complementary diff
    live, res_, rs = L.live_binding(E, lambda sd: L.construct_domain(E, w2, sd), w2.p, tmp_path / "live_y")
    chk.pre("P05", "genuine decide of P_Y in world Y (scratch store) is authorized with no reasons", {"result": "authorized", "reasons": []}, {"result": res_, "reasons": list(rs)})
    chk.gate()
    persisted_b = L.binding_of(w1.dir, w1.did)
    base, ecb = L.split_diff(persisted_b, live)
    claim_label = claim_for(base, ecb)
    chk.snap("S01", "complementary binding diff, persisted D_X vs live binding minted for P_Y in world Y", base_diff=base, ecb_diff=ecb, classification=claim_label)

    # C01 (inline control, BLOCKED if it fails): the UNPERTURBED X world issues exactly one claim through the provision interface over a copy of the same genuine store
    dctl = _copy(w1.dir, tmp_path / "ctl_x")
    leg_c = run_leg(E, "provision", L.construct_domain(E, w1, dctl), w1.p, w1.did, "bq-claim-main-ctl", dctl, chk, "C01")
    chk.pre("C01", "inline control: unperturbed X-world claim issues exactly one claim (provision sink called once with it, verified)",
            {"issued": True, "sink_calls": 1, "verified": True}, {"issued": leg_c.claim is not None, "sink_calls": len(leg_c.sink), "verified": leg_c.verified}, exc=leg_c.exc_str)
    chk.gate()

    # the claim leg under test (route 1: materialize_local_execution_claim)
    dm = _copy(w1.dir, tmp_path / "claim_main")
    flow_y = L.construct_domain(E, w2, dm)
    persisted = flow_y.records.decision(w1.did)
    chk.pre("P06", "the persisted X decision is readable by the Y workflow's store reader and authorized",
            {"found": True, "result": "authorized"}, {"found": persisted is not None, "result": getattr(persisted, "result", None)})
    chk.gate()
    leg = run_leg(E, "materialize", flow_y, w2.p, w1.did, "bq-claim-main-m", dm, chk, "main-m")
    chk.pre("P07", "the claim path reached the live-binding comparison: the claim ResolutionCheck row records NO base reason (stage claim, reasons [])",
            {"n_new": 1, "stage": "claim", "reasons": []}, _row_state(leg))
    chk.gate()

    # route 2: provision_local_execution_claim with a recording sink, over a second copy (separate, no reuse of the first store)
    dp = _copy(w1.dir, tmp_path / "claim_main_prov")
    leg_p = run_leg(E, "provision", L.construct_domain(E, w2, dp), w2.p, w1.did, "bq-claim-main-p", dp, chk, "main-p")
    chk.pre("P08", "route 2: the claim ResolutionCheck row records NO base reason either",
            {"n_new": 1, "stage": "claim", "reasons": []}, _row_state(leg_p))
    chk.gate()

    # ---- outcome assertions, route 1 (materialize)
    chk.ok("A01", "claim leg raised exactly PermissionError (not a subclass such as RegistrySelectionRefused, not another type)", "PermissionError", leg.exc_type)
    chk.ok("A02", "refusal message is exactly the generic claim-issuance message", MSG_CLAIM, leg.exc_str)
    chk.ok("A03", "no claim object was emitted", False, leg.claim is not None)
    chk.ok("A04", "no durable EffectTimeRefusal or other refusal written (refusals delta 0)", 0, leg.deltas.get("refusals", 0))
    chk.ok("A05", "the ONLY store collection that changed is resolution_checks (+1); no attempt, decision, observation, reconciliation, closeout or new ledger row",
           {"resolution_checks": 1}, leg.nonzero)
    chk.ok("A06", "persisted decisions section byte-equal before and after (no decision rewritten, no authorization widened)", True, leg.decisions_equal)
    chk.ok("A07", "store top-level key set unchanged (no new ledger or check_events section)", True, leg.keys_equal)
    chk.ok("A08", "destination apply never called and destination state unchanged", {"calls": 0, "unchanged": True}, {"calls": leg.calls, "unchanged": leg.dest_unchanged})
    chk.ok("A09", "no machine-readable binding-change token on the claim path: not in the exception text and not in the claim ResolutionCheck reasons",
           {"in_exception_text": False, "in_check_reasons": False},
           {"in_exception_text": CLAIM_CODE_NAME in (leg.exc_str or ""), "in_check_reasons": any(CLAIM_CODE_NAME in c["reasons"] for c in leg.new_checks)})
    # ---- complementary diff (joint evidence)
    chk.ok("A10", "base binding diff (persisted D_X vs live P_Y in world Y) is exactly {manifest_digest, proposal_commitment}", BASE_EXP, base)
    chk.ok("A11", "ECB diff is exactly {effective_configuration.digest, effective_configuration.members.scope.authority_domain}", ECB_EXP, sorted(ecb))
    chk.ok("A12", "ECB diff contains the scope.authority_domain leaf", True, (ECBP + ".members.scope.authority_domain") in ecb)
    chk.ok("A13", "classification by the decision rule (base [] and ECB exactly digest+leaf => isolated) is JOINT", "joint", claim_label)
    pm, lm = persisted_b["runtime_authority"][KEY], live["runtime_authority"][KEY]
    chk.ok("A14", "persisted ECB domain leaf is X and live ECB domain leaf is Y", [X_DOMAIN, Y_DOMAIN], [pm["members"]["scope"]["authority_domain"], lm["members"]["scope"]["authority_domain"]])
    chk.ok("A15", "both ECB digests equal the independent recomputation (H.my_digest over version and members)", {"persisted": True, "live": True},
           {"persisted": H.my_digest(pm["members"], pm["version"]) == pm["digest"], "live": H.my_digest(lm["members"], lm["version"]) == lm["digest"]})
    # ---- route 2 (provision with sink)
    chk.ok("A20", "route 2: PermissionError with the generic claim message", ["PermissionError", MSG_CLAIM], [leg_p.exc_type, leg_p.exc_str])
    chk.ok("A21", "route 2: provision sink never called and no claim returned", {"sink_calls": 0, "claim_returned": False}, {"sink_calls": len(leg_p.sink), "claim_returned": leg_p.claim is not None})
    chk.ok("A22", "route 2: only resolution_checks (+1) changed; refusals delta 0; decisions byte-equal", {"nonzero": {"resolution_checks": 1}, "refusals": 0, "decisions_equal": True},
           {"nonzero": leg_p.nonzero, "refusals": leg_p.deltas.get("refusals", 0), "decisions_equal": leg_p.decisions_equal})
    chk.ok("A23", "route 2: destination never called and unchanged", {"calls": 0, "unchanged": True}, {"calls": leg_p.calls, "unchanged": leg_p.dest_unchanged})
    # evidence-only (never scored): candidate's own read-only classifier on the Y workflow over the X decision, and the input-time-floor movement
    try:
        chk.obs("O01", "candidate classifier configuration_binding_status(D_X) in the Y workflow (evidence only, not an oracle)", observed=flow_y.configuration_binding_status(persisted))
    except Exception as exc:
        chk.obs("O01", "classifier raised (evidence only)", observed=f"raised:{type(exc).__name__}")
    chk.obs("O02", "input_time_floors unchanged by the claim leg (evidence only)", observed={"materialize": leg.floors_equal, "provision": leg_p.floors_equal})
    chk.done()


# ====================================================================================================================== controls
def test_N_CLAIM_JOINT_C0(tmp_path):
    """C0: the unperturbed X world issues exactly one claim per call (both interfaces); the live X world mints a binding identical to the persisted one (base [] and ECB [])."""
    E, chk = H.env(), BQ("C0")
    w1 = L.domain_world(E, tmp_path, "x", X_DOMAIN)
    f1, dec1 = L.domain_mint(E, w1)
    chk.pre("C0-P01", "world X mints an authorized decision", {"result": "authorized", "reasons": []}, {"result": dec1.result, "reasons": list(dec1.reasons)})
    chk.gate()
    live, res_, rs = L.live_binding(E, lambda sd: L.construct_domain(E, w1, sd), w1.p, tmp_path / "live_x")
    chk.pre("C0-P02", "genuine decide of P_X in world X (scratch) is authorized", {"result": "authorized", "reasons": []}, {"result": res_, "reasons": list(rs)})
    chk.gate()
    base, ecb = L.split_diff(L.binding_of(w1.dir, w1.did), live)
    chk.snap("C0-S01", "complementary diff persisted D_X vs live X", base_diff=base, ecb_diff=ecb)
    dm = _copy(w1.dir, tmp_path / "c0_m")
    leg_m = run_leg(E, "materialize", L.construct_domain(E, w1, dm), w1.p, w1.did, "bq-claim-C0-m", dm, chk, "C0-m")
    dp = _copy(w1.dir, tmp_path / "c0_p")
    leg_p = run_leg(E, "provision", L.construct_domain(E, w1, dp), w1.p, w1.did, "bq-claim-C0-p", dp, chk, "C0-p")
    chk.ok("C0-A00", "live X binding equals persisted: base diff [] and ECB diff []", {"base": [], "ecb": []}, {"base": base, "ecb": ecb})
    _issued_expectation_checks(chk, E, w1, leg_m, "C0-m-", "bq-claim-C0-m", {"calls": 0, "is_returned_claim": None}, X_DOMAIN)
    _issued_expectation_checks(chk, E, w1, leg_p, "C0-p-", "bq-claim-C0-p", {"calls": 1, "is_returned_claim": True}, X_DOMAIN)
    chk.done()


def test_N_CLAIM_JOINT_C1(tmp_path):
    """C1: world Y with the X proposal P_X (the Y approvals are bound to P_Y, not P_X; P_X carries H(M_X)): refused GUARD-FIRST by base reasons recorded in the claim
    ResolutionCheck row. The ECB comparison is never consulted (governed _resolve returns the base reasons unchanged, registry_governed_lifecycle.py:267-268)."""
    E, chk = H.env(), BQ("C1")
    w1, f1, dec1, w2, f2, dec2 = _two_worlds(E, tmp_path, chk)
    d = _copy(w1.dir, tmp_path / "c1")
    flow_y = L.construct_domain(E, w2, d)
    persisted = flow_y.records.decision(w1.did)
    chk.pre("C1-P05", "the persisted X decision is readable by the Y workflow and authorized", {"found": True, "result": "authorized"},
            {"found": persisted is not None, "result": getattr(persisted, "result", None)})
    chk.gate()
    leg = run_leg(E, "materialize", flow_y, w1.p, w1.did, "bq-claim-C1", d, chk, "C1")
    try:  # evidence-only probe: what a genuine decide says about P_X in world Y (scratch store); never scored
        lv, r_, rs = L.live_binding(E, lambda sd: L.construct_domain(E, w2, sd), w1.p, tmp_path / "c1_live_px")
        chk.obs("C1-O01", "genuine decide of P_X in world Y (evidence only)", binding_minted=lv is not None, result=r_, reasons=list(rs))
    except Exception as exc:
        chk.obs("C1-O01", "decide probe raised (evidence only)", error=f"{type(exc).__name__}: {exc}"[:300])
    chk.ok("C1-A01", "PermissionError exactly, generic claim message", ["PermissionError", MSG_CLAIM], [leg.exc_type, leg.exc_str])
    chk.ok("C1-A02", "no claim emitted", False, leg.claim is not None)
    row = leg.new_checks[0] if len(leg.new_checks) == 1 else None
    chk.ok("C1-A03", "one new claim ResolutionCheck row whose reasons are exactly the base reasons [approval_operation_binding_mismatch, manifest_digest_mismatch]",
           {"n_new": 1, "stage": "claim", "reasons": C1_REASONS}, {"n_new": len(leg.new_checks), "stage": row["stage"] if row else None, "reasons": list(row["reasons"]) if row else None})
    chk.ok("C1-A04", "guard-first: neither authority_domain_mismatch (resolver and manifest agree on Y) nor the binding-change token is among the reasons",
           {"authority_domain_mismatch": False, CLAIM_CODE_NAME: False}, {"authority_domain_mismatch": bool(row and "authority_domain_mismatch" in row["reasons"]),
                                                                          CLAIM_CODE_NAME: bool(row and CLAIM_CODE_NAME in row["reasons"])})
    chk.ok("C1-A05", "no refusal row written; only resolution_checks (+1) changed; decisions byte-equal", {"nonzero": {"resolution_checks": 1}, "refusals": 0, "decisions_equal": True},
           {"nonzero": leg.nonzero, "refusals": leg.deltas.get("refusals", 0), "decisions_equal": leg.decisions_equal})
    chk.ok("C1-A06", "destination never called and unchanged", {"calls": 0, "unchanged": True}, {"calls": leg.calls, "unchanged": leg.dest_unchanged})
    chk.done()


def test_N_CLAIM_JOINT_C2(tmp_path):
    """C2: neutral rebuild. A second, independently built world with the SAME domain X (new manifest/resolver/Registry material objects, identical content) over a copy of the
    X store issues a claim: the write/rebuild path is neutral and the only semantic change in main is the domain."""
    E, chk = H.env(), BQ("C2")
    w1 = L.domain_world(E, tmp_path, "x", X_DOMAIN)
    f1, dec1 = L.domain_mint(E, w1)
    wb = L.domain_world(E, tmp_path, "xb", X_DOMAIN)
    chk.pre("C2-P01", "world X mints an authorized decision", {"result": "authorized", "reasons": []}, {"result": dec1.result, "reasons": list(dec1.reasons)})
    chk.pre("C2-P02", "the rebuild is neutral: same domain, same proposal commitment, same manifest commitment, distinct objects",
            {"same_domain": True, "same_proposal_commitment": True, "same_manifest_commitment": True, "distinct_resolver_objects": True},
            {"same_domain": wb.manifest["actions"][0]["authority_context"]["authority_domain"] == w1.manifest["actions"][0]["authority_context"]["authority_domain"] == X_DOMAIN,
             "same_proposal_commitment": _commit(E, wb.p) == _commit(E, w1.p), "same_manifest_commitment": E.B.commitment(wb.manifest) == E.B.commitment(w1.manifest),
             "distinct_resolver_objects": wb.res is not w1.res})
    chk.gate()
    live, res_, rs = L.live_binding(E, lambda sd: L.construct_domain(E, wb, sd), wb.p, tmp_path / "live_xb")
    chk.pre("C2-P03", "genuine decide in the rebuilt X world (scratch) is authorized", {"result": "authorized", "reasons": []}, {"result": res_, "reasons": list(rs)})
    chk.gate()
    base, ecb = L.split_diff(L.binding_of(w1.dir, w1.did), live)
    chk.snap("C2-S01", "complementary diff persisted D_X vs live neutral rebuild", base_diff=base, ecb_diff=ecb)
    d = _copy(w1.dir, tmp_path / "c2")
    leg = run_leg(E, "materialize", L.construct_domain(E, wb, d), wb.p, w1.did, "bq-claim-C2", d, chk, "C2")
    chk.ok("C2-A00", "neutral rebuild: base diff [] and ECB diff []", {"base": [], "ecb": []}, {"base": base, "ecb": ecb})
    _issued_expectation_checks(chk, E, w1, leg, "C2-", "bq-claim-C2", {"calls": 0, "is_returned_claim": None}, X_DOMAIN)
    chk.done()


def test_N_CLAIM_JOINT_CY(tmp_path):
    """SUPPLEMENTARY control (not a precondition of main; its result never changes the interpretation of main): world Y claims for its OWN decision over a copy of Y's own
    store. Shows the Y fixture supports the claim interface at all. A failure here is recorded as a FAIL of this supplementary test only."""
    E, chk = H.env(), BQ("CY")
    w1, f1, dec1, w2, f2, dec2 = _two_worlds(E, tmp_path, chk)
    d = _copy(w2.dir, tmp_path / "cy")
    leg = run_leg(E, "materialize", L.construct_domain(E, w2, d), w2.p, w2.did, "bq-claim-CY", d, chk, "CY")
    _issued_expectation_checks(chk, E, w2, leg, "CY-", "bq-claim-CY", {"calls": 0, "is_returned_claim": None}, Y_DOMAIN)
    chk.done()
