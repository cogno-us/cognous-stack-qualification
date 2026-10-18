"""T11. C3 chain per configuration (ideas C22, C17, C20, tier 4; compound chain CH3).

SPDX-License-Identifier: Apache-2.0

Attacker: a retrying client whose first request lost its acknowledgement and who re-plans (new effect id, here through a grant
renewal) while the first request may still land.
Chain: r1 dispatched, acknowledgement lost (the delayed-commit destination holds it in flight, or the commit is durable and only
the ack is lost); r2 re-planned under a new effect id and executed; r1 lands late or is retried. Per-grant cap 2, so only an
operation-level control can stop the second business effect.
Invariant (plan): count business-level effects per configuration from destination rows; default configurations may duplicate
(known, F-5 / F-18) and are recorded, not hidden; opt-in configurations must not.

Does not prove: logical-intent prevention beyond the synthetic refund-intent registry; route C (exchange) and the atomic route
(F-5 there is covered by suites/operation-identity); a re-plan that changes business content (that is a new business request).
"""
from __future__ import annotations

from _adv import effect_ids, flow, rows, snapshot, twice
from conftest import observe

T = "T11"
DNP = "synthetic intent registry only; route C and the atomic route not run here"


def _chain_delayed(fl):
    fl.dest.defer_next_commit()
    r1 = fl.run(fl.d1)
    _, r2 = fl.renew_and_commit_r2()
    try:
        fl.dest.land()
        late = "landed"
    except PermissionError as exc:
        late = "refused:" + str(exc)
    return {"r1": r1.status, "r2": r2.status, "late_r1": late, "effects": len(effect_ids(fl.dest.path))}


def test_default_configuration_duplicates_known(cprt, tmp_path, monkeypatch):
    out = twice(tmp_path, lambda w, mp: _chain_delayed(flow(w, mp, identity=False, wide=True)))  # two fresh stores, equal
    observe(T, "C3 chain, default configuration", "reproduced failure" if out["effects"] > 1 else "prevented", does_not_prove=DNP,
            detail={**out, "known": "F-5 / F-18: default routes do not prevent a business-level duplicate"})
    assert out["effects"] == 2, out  # characterised known limitation


def test_operation_identity_configuration_single_effect(cprt, tmp_path, monkeypatch):
    out = twice(tmp_path, lambda w, mp: _chain_delayed(flow(w, mp, identity=True, wide=True)))
    observe(T, "C3 chain, operation-identity/0.1", "prevented" if out["effects"] == 1 else "reproduced failure",
            does_not_prove=DNP, detail=out)
    assert out["effects"] == 1, out


def test_refund_intent_configuration_single_effect(cprt, tmp_path, monkeypatch):
    from engine.refund_intent import RefundIntent, RefundIntentRegistry
    from engine.safe_executor import DurableRefundDestination
    fl = flow(tmp_path, monkeypatch, identity=False, wide=True, dest_factory=lambda path, f: DurableRefundDestination(path))
    intent = RefundIntent(institution_id=fl.tba.INSTITUTION, authority_domain="customer-refunds",
                          customer_id=fl.p.payload["customer_id"], request_id="request-1")
    registry = RefundIntentRegistry(fl.dest)
    registry.provision(intent, snapshot(fl.envelope(fl.d1)))

    def run(d):
        return fl.executor.execute(envelope=fl.envelope(d), proposal=fl.p, decision=d, now=fl.NOW, refund_intent=intent,
                                   **({"simulate": "lost_ack"} if d is fl.d1 else {}))
    r1 = run(fl.d1)
    fl.publish_revision("2")
    d2 = fl.f.decide(fl.p, now=fl.NOW)
    assert d2.result == "authorized" and d2.effect_id != fl.d1.effect_id
    r2 = run(d2)
    retry = fl.executor.execute(envelope=fl.envelope(fl.d1), proposal=fl.p, decision=fl.d1, now=fl.NOW, refund_intent=intent)
    reasons = [r["error"] for r in rows(fl.dest.path, "attempt_events") if r["status"] in ("failed", "denied") and r["error"]]
    out = {"r1": r1.status, "r2": r2.status, "destination_reasons": reasons, "retry_r1": retry.status,
           "effects": len(effect_ids(fl.dest.path))}
    observe(T, "C3 chain, refund intent", "prevented" if out["effects"] == 1 else "reproduced failure", does_not_prove=DNP,
            detail=out)
    assert out["effects"] == 1 and any("intent" in x for x in reasons), out  # refused by the intent registry, not by something else


def test_positive_control_single_submission_one_effect(cprt, tmp_path, monkeypatch):
    for identity in (False, True):
        fl = flow(tmp_path / str(identity), monkeypatch, identity=identity, wide=True)
        assert fl.run(fl.d1).status == "executed"
        assert effect_ids(fl.dest.path) == [fl.d1.effect_id]
