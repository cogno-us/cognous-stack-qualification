"""F-A1 qualification, in-process cases (plan docs/f-a1-authorization-pin/qualification-plan.md). 23 of the 30 counted executions.

Real components throughout: a Control Plane BoundedAuthorizationWorkflow decision, claims issued by `provision_local_execution_claim`, the Control Plane
export on the PERSISTED decision, the trusted installer writing the pin store/anchor/fences, and a Runtime destination built with the host-configured
`authorization_pin`. Where an input is synthetic (an unrelated decision, a terminal assessment, a pin recording a newer revision) the case says so in its
evidence. Same-identity, in-process cases do NOT demonstrate OS isolation; that is `test_fa1_os.py`.

HELD only with positive evidence (attack delivered and refused for the intended typed reason, or the legitimate path really executed).
"""
from __future__ import annotations

import copy
import datetime as dt
import json
import shutil
import sqlite3
import threading
import time

import pytest

import _fa1 as f
from _fa1 import Rig, judge, w
from engine import authorization_pin_format as fmt
from engine.authorization_pin import PinReader
from engine.local_authority_effect import AtomicAuthorityEffectDestination


@pytest.fixture(autouse=True)
def _cp_clock():
    with w.cp_clock():
        yield


def finish(ev, verdict, note=None, **observed):
    ev["observed"].update(observed)
    ev["verdict"] = verdict
    if note:
        ev["note"] = note
    assert verdict in ("HELD", "CHARACTERIZED"), (verdict, {k: observed[k] for k in list(observed)[:6]})


def second_operation(rig, wide2=None):
    """Activate a SECOND, valid operation `op-other` (wide record) in the same Registry scope, as the historical V08 AU-7 scenario did."""
    wide2 = wide2 or {k: sorted(v + [f"urn:cognous:op2:{k}"]) for k, v in w.needed_payload().items()}
    rec2 = w.v4.reg_record(payload=copy.deepcopy(wide2), record_id="f1ab-v08-record-op2")
    st2 = rig.env.statement(rec2, scope=rig.scope2, sid="sel-test-op2")
    rig.env.activate_stmt(st2, rec2, scope=rig.scope2)
    return wide2, rig.env.state(rig.scope2)


def receipts(rig):
    with sqlite3.connect(rig.dest.path) as conn:
        return [json.loads(r[0]) for r in conn.execute("SELECT receipt_json FROM authority_effect_receipts_v1")]


# ====================================================================================================================== FA1-01
def test_fa1_01_original_fa1_substitution_is_refused_and_the_historical_control_executes(tmp_path, ev):
    ev["scenario"] = "FA1-01"
    ev["expected"] = ("historical V08 AU-7 scenario: binding rewritten to another validly activated operation with every commitment recomputed. PATCHED: REFUSE "
                      "policy_identity_mismatch[pin_binding_mismatch:operation], 0 effects, 0 receipts. CONTROL (same claim, same store, destination WITHOUT the pin option) "
                      "executes: the attack is real and the pin is what stops it")
    rig = Rig(tmp_path, second_operation=True)
    wide2, state2 = second_operation(rig)
    installed = rig.install()
    honest = rig.iss.materialize(claim_id="honest-op")
    b2 = w.binding_for(rig.env, state2, rig.sets, scope=rig.scope2)
    raw = f.recompute_claim(w.forged_from(honest, claim_id="forged-op", binding_changes={k: b2[k] for k in b2 if k not in ("scope",)}))
    verifies = w.cp_effect.verify_local_execution_claim(raw)
    rig.dest.provision_claim(raw)
    res = rig.run("forged-op")
    patched_counts = rig.counts()
    verdict_p, typed = judge(res, patched_counts, "policy_identity_mismatch", "REFUSE", "pin_binding_mismatch:operation")
    control = w.executor(rig.env.dest, w.policy_from(rig.sets)).execute(envelope=rig.iss.envelope, claim_id="forged-op")
    control_counts = rig.counts()
    landed = control.status == "executed" and control_counts["effects"] == 1
    verdict = verdict_p if (verdict_p != "HELD" or landed) else "INCONCLUSIVE"
    finish(ev, verdict, pin_installed=installed.outcome, forged_binding_operation=raw["policy_binding"]["operation"], forged_claim_verifies=verifies,
           patched_status=res.status, patched_typed=typed, patched_counts=patched_counts, control_unpinned_status=control.status,
           control_unpinned_counts=control_counts, historical_breach_reproduced_without_pin=landed, chain=rig.iss.chain)


# ====================================================================================================================== FA1-02
def test_fa1_02_workflow_issued_claim_executes_and_the_receipt_carries_the_pin(tmp_path, ev):
    ev["scenario"] = "FA1-02"
    ev["expected"] = "real Control Plane decision, export, installer pin, workflow-issued claim: executes with 1 effect; the receipt records pin_epoch/pin_digest of the stored row"
    rig = Rig(tmp_path)
    installed = rig.install()
    cid = rig.claim()
    res = rig.run(cid)
    c = rig.counts()
    row = rig.rows()[0]
    rec = res.control_plane_evidence["authority_receipt"]["authorization_pin"]
    ok = (res.status == "executed" and c["effects"] == 1 and c["authority_effect_receipts_v1"] == 1 and rec["pin_epoch"] == 1
          and rec["pin_digest"] == row["pin_digest"] and installed.outcome == "installed" and receipts(rig)[0]["authorization_pin"] == rec)
    finish(ev, "HELD" if ok else "INCONCLUSIVE", status=res.status, counts=c, receipt_pin=rec, installed=installed.outcome, chain=rig.iss.chain)


# ====================================================================================================================== FA1-03
def test_fa1_03_cross_operation_selection_never_consults_the_other_operations_registry_row(tmp_path, ev, monkeypatch):
    ev["scenario"] = "FA1-03"
    ev["expected"] = ("two activated operations; pin for A; the claim names B with B's own (wide) effective-policy digest and the executor runs B's wide policy: REFUSE at the "
                      "pin; the Registry guard is never asked about B")
    rig = Rig(tmp_path, second_operation=True)
    wide2, state2 = second_operation(rig)
    rig.install()
    sel_cls = type(rig.dest._selection())
    calls = []
    original = sel_cls.check_effect

    def spy(self, *a, **k):
        calls.append({"args": [repr(x)[:80] for x in a], "kwargs": {n: repr(v)[:120] for n, v in k.items()}})
        return original(self, *a, **k)
    monkeypatch.setattr(sel_cls, "check_effect", spy)
    honest = rig.iss.materialize(claim_id="honest-op")
    b2 = w.binding_for(rig.env, state2, wide2, scope=rig.scope2)
    raw = f.recompute_claim(w.forged_from(honest, claim_id="forged-b", binding_changes={k: b2[k] for k in b2 if k not in ("scope",)}))
    rig.dest.provision_claim(raw)
    res = rig.run("forged-b", policy=w.policy_from(wide2))
    v, typed = judge(res, rig.counts(), "policy_identity_mismatch", "REFUSE", "pin_binding_mismatch:*")
    consulted_b = [c for c in calls if "op-other" in json.dumps(c)]
    finish(ev, v if (v != "HELD" or not consulted_b) else "BREACH", typed=typed, counts=rig.counts(), check_effect_calls=calls, registry_row_of_b_consulted=bool(consulted_b),
           forged_operation=raw["policy_binding"]["operation"], pin_operation=rig.assessment()["payload"]["operation"])


# ====================================================================================================================== FA1-04
def test_fa1_04_recomputed_commitments_never_change_the_outcome(tmp_path, ev):
    ev["scenario"] = "FA1-04"
    ev["expected"] = ("the supplier alters a binding member and recomputes approval/policy/evidence/authority-state and claim commitments (the claim verifies): REFUSE "
                      "policy_identity_mismatch[pin_binding_mismatch:*]; recomputation changes nothing")
    rig = Rig(tmp_path)
    rig.install()
    honest = rig.iss.materialize(claim_id="honest-c")
    raw = f.recompute_claim(w.forged_from(honest, claim_id="recomputed", binding_changes={"selection_epoch": rig.state.selection_epoch + 1}))
    verifies = w.cp_effect.verify_local_execution_claim(raw)
    rig.dest.provision_claim(raw)
    res = rig.run("recomputed")
    v, typed = judge(res, rig.counts(), "policy_identity_mismatch", "REFUSE", "pin_binding_mismatch:*")
    finish(ev, v if verifies else "INCONCLUSIVE", forged_claim_verifies=verifies, typed=typed, counts=rig.counts(), changed_member="policy_binding.selection_epoch",
           operation_commitment_unchanged=raw["operation_commitment"] == honest.operation_commitment)


# ====================================================================================================================== FA1-07
def test_fa1_07_missing_pin_is_refused_with_no_fallback(tmp_path, ev):
    ev["scenario"] = "FA1-07"
    ev["expected"] = ("verified store, no row for the decision. (a) no per-decision fence exists (the installer creates it with the pin): HOLD verifier_unavailable"
                      "[pin_fence_unavailable] per Amendment 4 6.1; (b) a fence exists but there is no row: REFUSE policy_identity_mismatch[pin_absent]. 0 effects, no fallback")
    rig = Rig(tmp_path)
    cid = rig.claim()
    ra = rig.run(cid)
    va, ta = judge(ra, rig.counts(), "verifier_unavailable", "HOLD", "pin_fence_unavailable")
    fence = f.fence_of(rig)
    fence.parent.mkdir(parents=True, exist_ok=True)
    fence.touch()                                                       # harness acts as the installer identity to reach the "fence present, row absent" state
    rb = rig.run(cid)
    vb, tb = judge(rb, rig.counts(), "policy_identity_mismatch", "REFUSE", "pin_absent")
    finish(ev, f.verdict_of(va, vb), no_fence=ta, fence_without_row=tb, counts=rig.counts(),
           note="The plan text expected pin_absent for the no-fence state; the adopted contract (6.1) makes an absent fence a HOLD. Both are fail-closed with 0 effects.")


# ====================================================================================================================== FA1-08
def test_fa1_08_stale_grant_revision_is_refused_by_the_pin(tmp_path, ev):
    ev["scenario"] = "FA1-08"
    ev["expected"] = ("a pin that records a different grant_revision than the (honest, workflow-issued) claim: REFUSE policy_identity_mismatch[pin_lineage_mismatch:grant_revision]. "
                      "INPUT IS SYNTHETIC: the pin's payload is the real export with grant_revision replaced; forging the claim instead is stopped earlier by the existing "
                      "approval-state validation (observed in the qualification exploration), so that route cannot reach the pin")
    rig = Rig(tmp_path)
    assessment = rig.assessment()
    assessment["payload"] = {**assessment["payload"], "grant_revision": "rev-2-newer"}
    installed = rig.installer.apply_assessment(assessment)
    cid = rig.claim()
    res = rig.run(cid)
    v, typed = judge(res, rig.counts(), "policy_identity_mismatch", "REFUSE", "pin_lineage_mismatch:grant_revision")
    finish(ev, v, installed=installed.outcome, typed=typed, counts=rig.counts(), claim_grant_revision=rig.iss.decision.binding.grant_revision)


# ====================================================================================================================== FA1-09
def test_fa1_09_superseded_pin_is_refused_after_the_full_fenced_protocol(tmp_path, ev):
    ev["scenario"] = "FA1-09"
    ev["expected"] = "terminal `superseded` committed through intent, exclusive fence, row commit and anchor completion; the claim is REFUSED pin_status:superseded. INPUT: synthetic terminal assessment"
    rig = Rig(tmp_path)
    rig.install()
    cid = rig.claim()
    done = rig.installer.apply_assessment(Rig.terminal_assessment(rig.decision_id, "superseded"))
    anchor = fmt.anchor_decode(rig.icfg.anchor_path.read_bytes())
    res = rig.run(cid)
    v, typed = judge(res, rig.counts(), "policy_identity_mismatch", "REFUSE", "pin_status:superseded")
    ok = done.outcome == "complete" and anchor["intent"] is None and anchor["committed_epoch"] == 2 and [r["status"] for r in rig.rows()] == ["active", "superseded"]
    finish(ev, v if ok else "INCONCLUSIVE", install_result=done.outcome, anchor_committed_epoch=anchor["committed_epoch"], typed=typed, counts=rig.counts(),
           statuses=[r["status"] for r in rig.rows()])


# ====================================================================================================================== FA1-10
def test_fa1_10_revocation_committed_before_the_effect_refuses_it(tmp_path, ev):
    ev["scenario"] = "FA1-10"
    ev["expected"] = ("claim issued, grant then revoked in the Control Plane: the REAL export reports terminal/revoked, the installer commits it; the effect is REFUSED "
                      "pin_status:revoked with 0 effects; the Control Plane also refuses to issue a new claim")
    rig = Rig(tmp_path)
    rig.install()
    cid = rig.claim()
    rig.revoke_in_control_plane()
    a = rig.assessment()
    done = rig.installer.apply_assessment(a)
    res = rig.run(cid)
    v, typed = judge(res, rig.counts(), "policy_identity_mismatch", "REFUSE", "pin_status:revoked")
    try:
        rig.claim(claim_id="late")
        late = "ISSUED"
    except PermissionError as exc:
        late = f"PermissionError: {str(exc)[:100]}"
    ok = a["state"] == "terminal" and a["terminal_status"] == "revoked" and done.outcome == "complete" and late.startswith("PermissionError")
    finish(ev, v if ok else "INCONCLUSIVE", export_state=a["state"], export_reason=a["reason"], install_result=done.outcome, typed=typed, counts=rig.counts(), late_claim=late)


# ====================================================================================================================== FA1-11
class Hold(AtomicAuthorityEffectDestination):
    """Parks the FIRST guarded transaction (shared fence held, pin step already passed) so a revocation can be attempted against a real in-flight effect."""
    entered = threading.Event()
    release = threading.Event()
    _lock = threading.Lock()
    parked = False

    def _transaction_stage(self, stage):
        cls = type(self)
        if stage == "after_selection_guard":
            with cls._lock:
                first, cls.parked = not cls.parked, True
            if first:
                cls.entered.set()
                assert cls.release.wait(20)


def test_fa1_11_revocation_serializes_with_effects_in_flight(tmp_path, ev):
    ev["scenario"] = "FA1-11"
    ev["expected"] = ("three effects of the decision in flight (one parked after its pin step, two holding the shared fence): the revocation stays pending, no terminal row, "
                      "no unfenced commit; the parked effect commits with pin_epoch 1; the others are HELD by the pending intent; after they leave the terminal row commits "
                      "(epoch 2 > every receipt epoch) and a later claim is REFUSED pin_status:revoked")
    Hold.entered, Hold.release, Hold.parked = threading.Event(), threading.Event(), False
    rig = Rig(tmp_path, dest_cls=Hold, installer_deadline=0.3, deadline=5.0)
    rig.install()
    cids = [rig.claim() for _ in range(4)]
    rig.revoke_in_control_plane()
    a = rig.assessment()
    out = {}

    def go(cid):
        out[cid] = rig.run(cid)
    t1 = threading.Thread(target=go, args=(cids[0],))
    t1.start()
    assert Hold.entered.wait(15), "the first guarded transaction never reached its parked stage"
    others = [threading.Thread(target=go, args=(c,)) for c in cids[1:3]]
    for t in others:
        t.start()
    time.sleep(0.4)                                                    # the two others now hold the shared fence and wait for the effect database
    pending_result = rig.installer.apply_assessment(a)
    mid = {"statuses": [r["status"] for r in rig.rows()], "pending": rig.installer.pending() is not None,
           "anchor_committed": fmt.anchor_decode(rig.icfg.anchor_path.read_bytes())["committed_epoch"]}
    Hold.release.set()
    for t in [t1, *others]:
        t.join(30)
    done = rig.installer.reconcile()
    after = [r["status"] for r in rig.rows()]
    last = rig.run(cids[3])
    c = rig.counts()
    zero = {"effects": 0, "attempts": 0, "authority_effect_receipts_v1": 0, "budget_used": 0}
    v_last, typed_last = judge(last, zero, "policy_identity_mismatch", "REFUSE", "pin_status:revoked")
    epochs = [r["authorization_pin"]["pin_epoch"] for r in receipts(rig)]
    term_epoch = rig.rows()[-1]["pin_epoch"]
    held_ok = [out[c_].status for c_ in cids[1:3]]
    ok = (pending_result.outcome == "pending_blocked" and mid["statuses"] == ["active"] and mid["pending"] and mid["anchor_committed"] == 1
          and out[cids[0]].status == "executed" and all(s != "executed" for s in held_ok) and after == ["active", "revoked"] and epochs == [1]
          and term_epoch > max(epochs) and any(r.outcome == "complete" for r in done) and v_last == "HELD" and c["effects"] == 1)
    # the parked effect committed BEFORE the revocation became effective; nothing committed with the previous pin afterwards
    finish(ev, "HELD" if ok else "INCONCLUSIVE", installer_while_in_flight=pending_result.outcome, mid=mid, statuses_after=after, receipt_pin_epochs=epochs,
           terminal_epoch=term_epoch, in_flight_results={f"claim-{i + 1}": out[c_].status for i, c_ in enumerate(cids[:3])}, later_claim_typed=typed_last, counts=c,
           reconcile=[r.outcome for r in done])


# ====================================================================================================================== FA1-12
def test_fa1_12_revocation_propagation_delay_is_characterized(tmp_path, ev):
    ev["scenario"] = "FA1-12"
    ev["expected"] = ("the Control Plane has revoked but the installer has not started: the effect still passes under the old pin (CHARACTERIZED, documented limit, Amendment 4 "
                      "section 12); from the first read after the installer's work the next claim is REFUSED pin_status:revoked")
    rig = Rig(tmp_path)
    rig.install()
    c1, c2 = rig.claim(), rig.claim()
    rig.revoke_in_control_plane()
    a = rig.assessment()
    window = rig.run(c1)                                                # installer not yet started for this revocation
    window_counts = rig.counts()
    done = rig.installer.apply_assessment(a)
    res = rig.run(c2)
    zero = {"effects": 0, "attempts": 0, "authority_effect_receipts_v1": 0, "budget_used": 0}
    v, typed = judge(res, zero, "policy_identity_mismatch", "REFUSE", "pin_status:revoked")
    ok = (a["state"] == "terminal" and window.status == "executed" and window_counts["effects"] == 1 and done.outcome == "complete" and v == "HELD"
          and rig.counts()["effects"] == 1)
    finish(ev, "CHARACTERIZED" if ok else "INCONCLUSIVE", note="propagation window: an effect admitted before the installer acts is not stopped by the pin",
           export_state=a["state"], effect_in_window=window.status, effects_in_window=window_counts["effects"], install_result=done.outcome, after_installer_typed=typed)


# ====================================================================================================================== FA1-13
def test_fa1_13_unavailable_fence_holder_keeps_the_transition_pending_and_holds_new_effects(tmp_path, ev):
    ev["scenario"] = "FA1-13"
    ev["expected"] = ("a REAL separate process holds the shared fence and never releases it: the revocation stays pending_blocked (no terminal row, committed epoch unchanged, "
                      "intent preserved, no completion reported); new effects for the decision are HELD pin_transition_pending; after the holder exits, recovery completes it "
                      "through the exclusive fence and the next attempt is REFUSED pin_status:revoked")
    rig = Rig(tmp_path, installer_deadline=0.3)
    rig.install()
    cid = rig.claim()
    rig.revoke_in_control_plane()
    a = rig.assessment()
    with f.holder(f.fence_of(rig), "sh"):
        blocked = rig.installer.apply_assessment(a)
        mid_rows = [r["status"] for r in rig.rows()]
        anchor = fmt.anchor_decode(rig.icfg.anchor_path.read_bytes())
        held = rig.run(cid)
        log = rig.installer.read_log()
        # only a TERMINAL completion for this decision counts (the earlier install of the pin also logs outcome "complete")
        completed_logged = any(e.get("action") == "terminal" and e.get("outcome") == "complete" and e.get("decision_id") == rig.decision_id for e in log)
    vh, typed = judge(held, rig.counts(), "store_unknown", "HOLD", "pin_transition_pending")
    done = rig.installer.reconcile()
    res = rig.run(cid)
    vr, typed_after = judge(res, rig.counts(), "policy_identity_mismatch", "REFUSE", "pin_status:revoked")
    ok = (blocked.outcome == "pending_blocked" and mid_rows == ["active"] and anchor["committed_epoch"] == 1 and anchor["intent"] is not None and not completed_logged
          and any(r.outcome == "complete" for r in done) and [r["status"] for r in rig.rows()] == ["active", "revoked"])
    finish(ev, f.verdict_of(vh, vr) if ok else "INCONCLUSIVE", blocked=blocked.outcome, rows_while_held=mid_rows, anchor_while_held={"committed_epoch": anchor["committed_epoch"],
           "intent": anchor["intent"] is not None}, new_effect_typed=typed, completion_logged_while_held=completed_logged, recovery=[r.outcome for r in done],
           after_recovery_typed=typed_after, counts=rig.counts())


# ====================================================================================================================== FA1-14
def test_fa1_14_pending_revocation_holds_only_the_covered_decision_and_completes_without_flock_fairness(tmp_path, ev):
    ev["scenario"] = "FA1-14"
    ev["expected"] = ("a stream of new claims for the covered decision is HELD every time while a revocation is pending; three UNRELATED decisions keep being admitted and "
                      "execute without touching the covered fence; once the pre-intent holder leaves, the revocation completes at once (no reliance on flock fairness). "
                      "UNRELATED decisions are synthetic by construction (the fixture cannot mint a second decision with another effect_id)")
    rig = Rig(tmp_path, installer_deadline=0.3, deadline=2.0)
    rig.install()
    others = [f.unrelated(rig, n) for n in (2, 3, 4)]
    for u in others:
        assert rig.installer.apply_assessment(u.assessment).outcome == "installed"
        rig.dest.provision_claim(u.claim)
    covered = [rig.claim() for _ in range(3)]
    rig.revoke_in_control_plane()
    a = rig.assessment()
    held_results, unrelated_results = [], []
    with f.holder(f.fence_of(rig), "sh"):
        blocked = rig.installer.apply_assessment(a)
        stop = threading.Event()

        def stream():
            while not stop.is_set():
                for cid in covered:
                    held_results.append(judge(rig.run(cid), {"effects": 0, "attempts": 0, "authority_effect_receipts_v1": 0, "budget_used": 0}, "store_unknown", "HOLD",
                                              "pin_transition_pending")[0])
                time.sleep(0.01)
        t = threading.Thread(target=stream)
        t.start()
        for u in others:
            r = w.executor(rig.dest, w.policy_from(rig.sets)).execute(envelope=u.envelope, claim_id=u.claim_id)
            unrelated_results.append(r.status)
        stop.set()
        t.join(30)
    t0 = time.monotonic()
    done = rig.installer.reconcile()
    took = time.monotonic() - t0
    res = rig.run(covered[0])
    v, typed = judge(res, {"effects": 0, "attempts": 0, "authority_effect_receipts_v1": 0, "budget_used": 0}, "policy_identity_mismatch", "REFUSE", "pin_status:revoked")
    ok = (blocked.outcome == "pending_blocked" and held_results and all(x == "HELD" for x in held_results) and unrelated_results == ["executed"] * 3
          and any(r.outcome == "complete" for r in done) and took < 1.0 and v == "HELD" and rig.counts()["effects"] == 3)
    finish(ev, "HELD" if ok else "INCONCLUSIVE", blocked=blocked.outcome, covered_attempts=len(held_results), covered_all_held=all(x == "HELD" for x in held_results),
           unrelated_statuses=unrelated_results, completion_seconds_after_holder_exit=round(took, 3), after_typed=typed, effects=rig.counts()["effects"])


# ====================================================================================================================== FA1-15
def test_fa1_15_stale_authorization_replay_is_refused_by_runtime_and_installer(tmp_path, ev):
    ev["scenario"] = "FA1-15"
    ev["expected"] = "claim for a terminal decision: Runtime REFUSE pin_status:revoked; the installer refuses (and logs) an attempt to re-activate the terminal decision; no new row"
    rig = Rig(tmp_path)
    active_assessment = rig.assessment()
    rig.installer.apply_assessment(active_assessment)
    cid = rig.claim()
    rig.revoke_in_control_plane()
    rig.installer.apply_assessment(rig.assessment())
    res = rig.run(cid)
    v, typed = judge(res, rig.counts(), "policy_identity_mismatch", "REFUSE", "pin_status:revoked")
    replay = rig.installer.apply_assessment(active_assessment)
    log = rig.installer.read_log()
    logged = [e for e in log if e.get("outcome") == "refused" and e.get("decision_id") == rig.decision_id]
    statuses = [r["status"] for r in rig.rows()]
    ok = replay.outcome == "refused" and bool(logged) and statuses == ["active", "revoked"]
    finish(ev, v if ok else "INCONCLUSIVE", runtime_typed=typed, installer_replay=replay.outcome, installer_detail=replay.detail, refusal_logged=bool(logged), statuses=statuses)


# ====================================================================================================================== FA1-16
def test_fa1_16_restoring_an_older_pin_store_is_held(tmp_path, ev):
    ev["scenario"] = "FA1-16"
    ev["expected"] = "pin store restored to the earlier ACTIVE state with the anchor intact: HOLD [pin_anchor_inconsistent]; the earlier active pin is not honoured; 0 effects"
    rig = Rig(tmp_path)
    rig.install()
    cid = rig.claim()
    backup = tmp_path / "store.backup"
    shutil.copyfile(rig.icfg.pin_store_path, backup)
    rig.revoke_in_control_plane()
    done = rig.installer.apply_assessment(rig.assessment())
    shutil.copyfile(backup, rig.icfg.pin_store_path)                     # rollback of the store only
    res = rig.run(cid)
    v, typed = judge(res, rig.counts(), "store_unknown", "HOLD", "pin_anchor_inconsistent",
                     alt=[("verifier_unavailable", "HOLD", "pin_anchor_inconsistent")])
    finish(ev, v if done.outcome == "complete" else "INCONCLUSIVE", terminal_install=done.outcome, typed=typed, counts=rig.counts(),
           note="A CONSISTENT restore of store and anchor together is undetectable (Amendment 4 section 7): recorded as CHARACTERIZED by analysis, not as a pass")


# ====================================================================================================================== FA1-17
def test_fa1_17_external_anchor_mismatch_holds_every_decision(tmp_path, ev):
    ev["scenario"] = "FA1-17"
    ev["expected"] = ("(a) anchor ahead of the store, (b) head digest different at the same epoch, (c) intent in an invalid relation (not committed+1): each HOLDs the covered AND an "
                      "unrelated decision with [pin_anchor_inconsistent] (for (c) the covered decision may instead report [pin_transition_pending] from the lock-free barrier); 0 effects")
    rig = Rig(tmp_path)
    rig.install()
    u = f.unrelated(rig, 2)
    rig.installer.apply_assessment(u.assessment)
    rig.dest.provision_claim(u.claim)
    cid = rig.claim()
    original = rig.icfg.anchor_path.read_bytes()
    base = fmt.anchor_decode(original)

    def anchor(**over):
        spec = dict(pin_store_id=base["pin_store_id"], committed_epoch=base["committed_epoch"], committed_head_digest=base["committed_head_digest"], intent=None,
                    anchored_at=base["anchored_at"])
        spec.update(over)
        return fmt.anchor_encode(fmt.make_anchor(**spec))
    variants = {"a_anchor_ahead": anchor(committed_epoch=base["committed_epoch"] + 3),
                "b_head_digest_differs": anchor(committed_head_digest="sha256:" + "9" * 64),
                "c_intent_invalid_relation": anchor(intent=fmt.make_intent(epoch=base["committed_epoch"] + 5, decision_id=rig.decision_id, action="terminal",
                                                                          status="revoked", provenance_ref="qualification"))}
    verdicts, seen = [], {}
    for name, payload in variants.items():
        rig.icfg.anchor_path.write_bytes(payload)
        r1 = rig.run(cid)
        r2 = w.executor(rig.dest, w.policy_from(rig.sets)).execute(envelope=u.envelope, claim_id=u.claim_id)
        z = {"effects": 0, "attempts": 0, "authority_effect_receipts_v1": 0, "budget_used": 0}
        alt = [("verifier_unavailable", "HOLD", "pin_anchor_inconsistent")]
        # a terminal intent that names the covered decision trips the lock-free pending barrier before the full anchor verification: still a HOLD, 0 effects
        alt_covered = alt + ([("store_unknown", "HOLD", "pin_transition_pending")] if name.startswith("c_") else [])
        v1, t1 = judge(r1, z, "store_unknown", "HOLD", "pin_anchor_inconsistent", alt=alt_covered)
        v2, t2 = judge(r2, z, "store_unknown", "HOLD", "pin_anchor_inconsistent", alt=alt)
        verdicts += [v1, v2]
        seen[name] = {"covered": t1, "unrelated": t2}
    rig.icfg.anchor_path.write_bytes(original)
    finish(ev, f.verdict_of(*verdicts) if rig.counts()["effects"] == 0 else "BREACH", variants=seen, counts=rig.counts())


# ====================================================================================================================== FA1-18
def test_fa1_18_unavailable_anchor_holds_every_decision_and_stops_the_installer(tmp_path, ev):
    ev["scenario"] = "FA1-18"
    ev["expected"] = "anchor removed: HOLD [pin_anchor_unavailable] for every decision; the installer refuses to write; nothing changes; restoring the anchor restores admission"
    rig = Rig(tmp_path)
    rig.install()
    cid = rig.claim()
    u = f.unrelated(rig, 2)
    rows_before = f.sql(rig.icfg.pin_store_path, "SELECT COUNT(*) FROM authorization_pin_v1")[0][0]
    aside = rig.icfg.anchor_path.with_suffix(".aside")
    rig.icfg.anchor_path.rename(aside)
    res = rig.run(cid)
    z = {"effects": 0, "attempts": 0, "authority_effect_receipts_v1": 0, "budget_used": 0}
    v, typed = judge(res, z, "store_unknown", "HOLD", "pin_anchor_unavailable", alt=[("verifier_unavailable", "HOLD", "pin_anchor_unavailable")])
    refused = rig.installer.apply_assessment(u.assessment)
    rows_mid = f.sql(rig.icfg.pin_store_path, "SELECT COUNT(*) FROM authorization_pin_v1")[0][0]
    aside.rename(rig.icfg.anchor_path)
    after = rig.run(cid)
    ok = refused.outcome == "refused" and rows_before == rows_mid and after.status == "executed"
    finish(ev, v if ok else "INCONCLUSIVE", typed=typed, installer_with_missing_anchor=refused.outcome, installer_detail=refused.detail, rows_before=rows_before,
           rows_while_missing=rows_mid, status_after_restore=after.status)


# ====================================================================================================================== FA1-23
def test_fa1_23_original_f01_widening_still_refuses_beneath_a_valid_pin(tmp_path, ev):
    ev["scenario"] = "FA1-23"
    ev["expected"] = ("the pin and the claim agree (the approval-side binding names the wide policy digest) but the activated Registry record is narrower and the executor runs the "
                      "wide policy: the pin step PASSES and F-01 containment REFUSES policy_identity_mismatch[policy_not_subset:allowed_actions]; 0 effects")
    wide = {k: list(v) for k, v in w.needed_payload().items()}
    wide["allowed_actions"] = wide["allowed_actions"] + ["act-extra"]
    rig = Rig(tmp_path, policy_sets=wide)
    rig.install()
    cid = rig.claim()
    res = rig.run(cid, policy=w.policy_from(wide))
    v, typed = judge(res, rig.counts(), "policy_identity_mismatch", "REFUSE", "policy_not_subset:allowed_actions")
    finish(ev, v, typed=typed, counts=rig.counts(), pin_passed=typed is not None and not typed["cause"].startswith("pin_"))


# ====================================================================================================================== FA1-24
def test_fa1_24_a_second_f01_set_is_contained_beneath_the_pin(tmp_path, ev):
    ev["scenario"] = "FA1-24"
    ev["expected"] = "same arrangement widening allowed_units: REFUSE policy_identity_mismatch[policy_not_subset:allowed_units]; the other three sets run in the Runtime F-01 CI suite"
    wide = {k: list(v) for k, v in w.needed_payload().items()}
    wide["allowed_units"] = wide["allowed_units"] + ["unit-extra"]
    rig = Rig(tmp_path, policy_sets=wide)
    rig.install()
    cid = rig.claim()
    res = rig.run(cid, policy=w.policy_from(wide))
    v, typed = judge(res, rig.counts(), "policy_identity_mismatch", "REFUSE", "policy_not_subset:allowed_units")
    finish(ev, v, typed=typed, counts=rig.counts())


# ====================================================================================================================== FA1-25
def test_fa1_25_valid_narrower_policy_executes_under_the_pin(tmp_path, ev):
    ev["scenario"] = "FA1-25"
    ev["expected"] = "activated record WIDER than the executor policy; valid pin; the narrower policy executes (1 effect)"
    needed = w.needed_payload()
    wide_record = {k: sorted(v + [f"extra-{k}"]) for k, v in needed.items()}
    rig = Rig(tmp_path, payload=wide_record, policy_sets=needed)
    rig.install()
    cid = rig.claim()
    res = rig.run(cid, policy=w.policy_from(needed))
    c = rig.counts()
    finish(ev, "HELD" if (res.status == "executed" and c["effects"] == 1) else "INCONCLUSIVE", status=res.status, counts=c)


# ====================================================================================================================== FA1-26
def test_fa1_26_transaction_critical_evidence_failure_commits_nothing_and_releases_the_fence(tmp_path, ev):
    ev["scenario"] = "FA1-26"
    ev["expected"] = "the receipt/evidence insert fails: 0 committed effects/attempts/receipts/budget, the claim stays issued, and the shared fence is released"
    rig = Rig(tmp_path)
    rig.install()
    cid = rig.claim()
    conn = sqlite3.connect(rig.dest.path)
    conn.execute("CREATE TRIGGER fa1_evidence_fail BEFORE INSERT ON authority_effect_receipts_v1 BEGIN SELECT RAISE(ABORT, 'fa1 injected evidence failure'); END")
    conn.commit()
    conn.close()
    res = rig.run(cid)
    c = rig.counts()
    released = f.fence_free(f.fence_of(rig))
    ok = (res.status != "executed" and c["effects"] == 0 and c["attempts"] == 0 and c["authority_effect_receipts_v1"] == 0 and c["budget_used"] == 0
          and set(c["claim_states"].values()) == {"issued"} and released)
    finish(ev, "HELD" if ok else "BREACH" if c["effects"] else "INCONCLUSIVE", status=res.status, error=res.error, counts=c, fence_released=released)


# ====================================================================================================================== FA1-27
def test_fa1_27_required_scope_legacy_claim_without_a_binding_is_refused(tmp_path, ev):
    ev["scenario"] = "FA1-27"
    ev["expected"] = "a workflow-issued claim WITHOUT a policy binding on a pin-required destination: REFUSE policy_identity_mismatch[pin_required_binding_absent]; no legacy fallback; 0 effects"
    rig = Rig(tmp_path)
    rig.install()
    cid = rig.claim(binding=None)
    res = rig.run(cid)
    v, typed = judge(res, rig.counts(), "policy_identity_mismatch", "REFUSE", "pin_required_binding_absent")
    finish(ev, v, typed=typed, counts=rig.counts(), claim_has_binding=False)


# ====================================================================================================================== FA1-28
def test_fa1_28_supplier_seeded_first_writer_rows_confer_no_authority(tmp_path, ev):
    ev["scenario"] = "FA1-28"
    ev["expected"] = ("the supplier seeds a claim FIRST (a different grant, every commitment recomputed, envelope consistent): it is REFUSED with 0 effects, and the honest claim still "
                      "executes; the seeded rows confer no authority. The refusing control is recorded (existing approval-state validation or the pin lineage check)")
    rig = Rig(tmp_path)
    rig.install()
    raw, env = f.consistent_forgery(rig, "seeded", op_changes={"grant_id": "urn:cognous:grant:seeded"},
                                    top_changes={"grant_id": "urn:cognous:grant:seeded", "budget_id": "budget-seeded"})
    verifies = w.cp_effect.verify_local_execution_claim(raw)
    provision_error = None
    try:
        rig.dest.provision_claim(raw)
        seeded = w.executor(rig.dest, w.policy_from(rig.sets)).execute(envelope=env, claim_id="seeded")
    except Exception as exc:                                              # noqa: BLE001
        seeded, provision_error = None, f"{type(exc).__name__}: {str(exc)[:160]}"
    mid = rig.counts()
    seeded_refused = (seeded is None) or (seeded.status != "executed" and not seeded.attempted)
    cid = rig.claim()
    honest = rig.run(cid)
    c = rig.counts()
    ok = verifies and seeded_refused and mid["effects"] == 0 and honest.status == "executed" and c["effects"] == 1
    finish(ev, "HELD" if ok else "BREACH" if mid["effects"] else "INCONCLUSIVE", seeded_claim_verifies=verifies, seeded_provision_error=provision_error,
           seeded_status=None if seeded is None else seeded.status, seeded_error=None if seeded is None else seeded.error, seeded_typed=None if seeded is None else w.refusal_of(seeded),
           effects_after_seeded=mid["effects"], honest_status=honest.status, final_counts=c)


# ====================================================================================================================== FA1-29
def test_fa1_29_installer_preconditions_install_no_pin_for_unsupported_authority(tmp_path, ev):
    ev["scenario"] = "FA1-29"
    ev["expected"] = ("an expired grant, a host binding that no longer matches the committed catalogue, an unknown decision and a non-active/unknown assessment each produce NO pin; "
                      "the Control Plane export raises, and the installer refuses and LOGS what reaches it")
    rig = Rig(tmp_path)
    iss = rig.iss

    def attempt(label, fn):
        try:
            out = fn()
            return label, f"returned state={out.get('state')} payload={'present' if out.get('payload') else 'none'}"
        except (PermissionError, ValueError) as exc:
            return label, f"{type(exc).__name__}: {str(exc)[:110]}"
    far = w.CP_NOW + dt.timedelta(days=3650)
    mismatched = copy.deepcopy(iss.binding)
    mismatched["record_version"] = mismatched["record_version"] + 1
    probes = dict([
        attempt("expired_grant", lambda: f.cp_export.assess_authorization_pin(iss.workflow, iss.p, iss.decision, now=far, host_policy_binding=iss.binding)),
        attempt("catalogue_or_binding_mismatch", lambda: f.cp_export.assess_authorization_pin(iss.workflow, iss.p, iss.decision, now=w.CP_NOW, host_policy_binding=mismatched)),
        attempt("unknown_decision", lambda: f.cp_export.assess_authorization_pin(iss.workflow, iss.p, iss.decision.model_copy(update={"decision_id": "never-persisted"}),
                                                                                  now=w.CP_NOW, host_policy_binding=iss.binding)),
    ])
    export_refused = all(v.startswith(("PermissionError", "ValueError")) or "payload=none" in v for v in probes.values())
    unknown = rig.installer.apply_assessment({"profile": f.EXPORT_PROFILE, "decision_id": rig.decision_id, "state": "unknown", "payload": None, "terminal_status": None,
                                              "reason": "persisted authority could not be confirmed"})
    garbage = rig.installer.apply_assessment({"profile": "other/1", "decision_id": "x", "state": "active"})
    rows = f.sql(rig.icfg.pin_store_path, "SELECT COUNT(*) FROM authorization_pin_v1")[0][0]
    logged = [e for e in rig.installer.read_log() if e.get("outcome") == "refused"]
    ok = export_refused and unknown.outcome == "refused" and garbage.outcome == "refused" and rows == 0 and len(logged) >= 2
    finish(ev, "HELD" if ok else "INCONCLUSIVE", control_plane_export=probes, installer_unknown_state=unknown.outcome, installer_garbage=garbage.outcome, pin_rows=rows,
           refusals_logged=len(logged))


# ====================================================================================================================== FA1-06b
def test_fa1_06b_pin_paths_and_options_are_host_only(tmp_path, ev):
    ev["scenario"] = "FA1-06"
    ev["expected"] = ("(b) a caller cannot redirect the pin store, anchor or fence through executor/destination arguments, attributes or a claim member: unexpected arguments raise "
                      "TypeError, the frozen configuration attributes raise AttributeError, and a claim carrying a path member is rejected or ignored with the host-configured paths "
                      "unchanged. In-process attribute freezing is defence in depth, NOT an isolation boundary")
    rig = Rig(tmp_path)
    rig.install()
    cid = rig.claim()
    before = (str(rig.dest._authorization_pin_config.pin_store_path), str(rig.dest._authorization_pin_config.anchor_path), str(rig.dest._authorization_pin_config.fence_dir))
    other = rig.gcfg.__class__(pin_store_path=tmp_path / "evil.sqlite3", fence_dir=tmp_path / "evil-fences", anchor_path=tmp_path / "evil.anchor", pin_store_id="evil")
    results = {}

    def probe(name, fn):
        try:
            fn()
            results[name] = "ALLOWED"
        except Exception as exc:                                          # noqa: BLE001
            results[name] = type(exc).__name__
    probe("executor_execute_kwarg", lambda: w.executor(rig.dest, w.policy_from(rig.sets)).execute(envelope=rig.iss.envelope, claim_id=cid, authorization_pin=other))
    probe("execute_claim_atomic_kwarg", lambda: rig.dest.execute_claim_atomic(cid, rig.iss.envelope, authorization_pin=other))
    probe("rebind_config_attribute", lambda: setattr(rig.dest, "_authorization_pin_config", other))
    probe("rebind_reader_attribute", lambda: setattr(rig.dest, "_pin_reader", None))
    probe("disable_required_property", lambda: setattr(rig.dest, "authorization_pin_required", False))
    honest = rig.iss.materialize(claim_id="with-path-member")
    raw = f.recompute_claim({**honest.model_dump(mode="json", exclude_none=False), "pin_store_path": str(tmp_path / "evil.sqlite3"), "claim_commitment": ""})
    try:
        rig.dest.provision_claim(raw)
        results["claim_with_path_member"] = "ACCEPTED_AND_IGNORED"
    except Exception as exc:                                              # noqa: BLE001
        results["claim_with_path_member"] = f"rejected:{type(exc).__name__}"
    after = (str(rig.dest._authorization_pin_config.pin_store_path), str(rig.dest._authorization_pin_config.anchor_path), str(rig.dest._authorization_pin_config.fence_dir))
    still_governed = rig.run(cid)
    ok = (results["executor_execute_kwarg"] == "TypeError" and results["execute_claim_atomic_kwarg"] == "TypeError"
          and results["rebind_config_attribute"] == "AttributeError" and results["rebind_reader_attribute"] == "AttributeError"
          and results["disable_required_property"] == "AttributeError" and results["claim_with_path_member"] != "ALLOWED" and before == after
          and still_governed.status == "executed" and still_governed.control_plane_evidence["authority_receipt"]["authorization_pin"]["pin_epoch"] == 1)
    finish(ev, "HELD" if ok else "INCONCLUSIVE", attempts=results, config_unchanged=before == after, governed_execution_after_attempts=still_governed.status)
