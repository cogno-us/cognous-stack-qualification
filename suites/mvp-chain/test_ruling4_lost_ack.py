"""Architect ruling 4: focused assertions on the lost-acknowledgement path of route B (proposed; Qualification owns the verdict).

SPDX-License-Identifier: Apache-2.0

Added to the existing mvp-chain battery as direct pytest assertions. It does NOT touch expectations v1-v3 or any scenario observation
that those expectations read: it drives its own disposable flow (``_chain.Ctx``, the same real Control Plane decision, real claim
provisioning, route B executor and synthetic SQLite destination) and asserts, after ``simulate='lost_ack'`` (fault injection by this
trusted harness):

  1. the first result is UNKNOWN, never acknowledged, and its recovery observation says retry_eligible is False;
  2. a second execute with the same claim is refused (a denied result with attempted False, or a raised refusal) and the claim is no longer usable;
  3. the destination holds exactly one committed effect, established by an independent read-only SQLite readback of the ``effects``
     table (not by any executor result);
  4. ``reconcile_claim`` resolves the uncertainty (applied, same effect id) without authorizing a duplicate (no new effect, still
     not retry eligible, claim stays consumed);
  5. the second result's default ``observed_state`` is NOT an authoritative observation: the second result carries no observation, and the
     authoritative readback and reconciliation show the effect whatever it says;
  6. a fresh operation identity without new authority (no new approval binding, no renewal, same grant cap) cannot re-issue the
     same business effect: whatever refuses it, no second effect is committed and no second execute reports ``executed``.

Every test fails when the components are not the pinned tuple (conftest); nothing skips and nothing is marked xfail.
"""
from __future__ import annotations

import copy
import pathlib
import tempfile

import pytest

import _chain
import _state


class LostAck:
    """Raw observations of one lost-acknowledgement flow. No verdict is computed here."""


@pytest.fixture(scope="module")
def lost_ack():
    if _state.ENV["problems"]:
        pytest.fail("mvp-chain cannot run against the components: " + "; ".join(_state.ENV["problems"]))
    from engine.safe_executor import snapshot_envelope
    work = pathlib.Path(tempfile.mkdtemp(prefix="mvp-ruling4-"))
    ctx = _chain.Ctx(work)
    obs = LostAck()
    try:
        flow, dest = ctx.flow, ctx.dest
        obs.expected_effect_id = flow.d1.effect_id
        claim = ctx.provision()
        obs.claim_id = claim.claim_id
        obs.claim_state_before = dest.claim_state(claim.claim_id)
        obs.first = ctx.execute(claim.claim_id, simulate="lost_ack")
        obs.first_observation = copy.deepcopy(obs.first.observation) if isinstance(obs.first.observation, dict) else {}
        obs.ids_after_first = ctx.effect_ids()
        obs.claim_state_after_first = dest.claim_state(claim.claim_id)
        step = _chain.attempt(lambda: ctx.execute(claim.claim_id))
        obs.second_raised = None if step["ok"] else step["error"]
        obs.second = step["value"] if step["ok"] else None
        obs.ids_after_second = ctx.effect_ids()
        recon = _chain.attempt(lambda: dest.reconcile_claim(claim.claim_id, snapshot_envelope(flow.envelope(flow.d1))))
        obs.reconcile_raised = None if recon["ok"] else recon["error"]
        obs.reconcile = recon["value"] if recon["ok"] else None
        obs.ids_after_reconcile = ctx.effect_ids()
        obs.claim_state_after_reconcile = dest.claim_state(claim.claim_id)
        # A fresh operation identity WITHOUT new authority: only the operation id in the authority context changes. The approval is not
        # re-bound, no renewal is recorded, the grant cap (one effect) is untouched. Nothing here may add authority.
        authority = flow.r.contexts[flow.PROFILE]["runtime_authority"]
        original_operation = authority["operation_id"]
        authority["operation_id"] = original_operation + "/fresh-identity-no-new-authority"
        obs.fresh = {"operation_id": authority["operation_id"], "original_operation_id": original_operation,
                     "decision": None, "decision_reasons": None, "decision_raised": None, "claim_issued": False,
                     "claim_raised": None, "execute_status": None, "execute_raised": None, "executed": False}
        d2 = _chain.attempt(lambda: flow.f.decide(flow.p, now=flow.NOW))
        if d2["ok"]:
            obs.fresh["decision"], obs.fresh["decision_reasons"] = d2["value"].result, list(d2["value"].reasons)
            if d2["value"].result == "authorized":
                c2 = _chain.attempt(lambda: ctx.provision(d2["value"]))
                obs.fresh["claim_issued"] = c2["ok"]
                obs.fresh["claim_raised"] = None if c2["ok"] else c2["error"]
                if c2["ok"]:
                    e2 = _chain.attempt(lambda: ctx.execute(c2["value"].claim_id, d2["value"]))
                    obs.fresh["execute_raised"] = None if e2["ok"] else e2["error"]
                    if e2["ok"]:
                        obs.fresh["execute_status"] = e2["value"].status
                        obs.fresh["executed"] = e2["value"].status == "executed"
        else:
            obs.fresh["decision_raised"] = d2["error"]
        obs.ids_final = ctx.effect_ids()
        yield obs
    finally:
        ctx.close()


def test_first_result_is_unknown_never_acknowledged_and_not_retry_eligible(lost_ack):
    first = lost_ack.first
    assert first.status == "unknown", first.status
    assert first.acknowledged is False
    assert lost_ack.first_observation.get("retry_eligible") is False, lost_ack.first_observation


def test_second_execute_with_the_same_claim_is_refused_claim_not_usable_not_attempted(lost_ack):
    if lost_ack.second is None:  # a refusal raised instead of returned: it must be a real exception, and nothing may have been committed
        assert lost_ack.second_raised and lost_ack.second_raised.get("type"), lost_ack.second_raised
    else:
        second = lost_ack.second
        assert second.status == "denied", second.status
        assert second.attempted is False
        assert second.acknowledged is False
    assert lost_ack.claim_state_after_first != "issued", lost_ack.claim_state_after_first  # the claim is no longer usable
    assert lost_ack.ids_after_second == lost_ack.ids_after_first


def test_destination_has_exactly_one_committed_effect_by_authoritative_readback(lost_ack):
    # independent read-only SQLite connection over the effects table: not an executor result, not an observation field
    assert lost_ack.ids_after_first == [lost_ack.expected_effect_id], lost_ack.ids_after_first
    assert lost_ack.ids_after_second == [lost_ack.expected_effect_id]
    assert lost_ack.ids_after_reconcile == [lost_ack.expected_effect_id]
    assert lost_ack.ids_final == [lost_ack.expected_effect_id]


def test_reconcile_resolves_the_uncertainty_without_authorizing_a_duplicate(lost_ack):
    assert lost_ack.reconcile_raised is None, lost_ack.reconcile_raised
    recon = lost_ack.reconcile
    assert isinstance(recon, dict), type(recon)
    state = recon.get("state") or recon.get("status")
    assert state in ("applied", "reconciled"), recon
    assert recon.get("effect_id") == lost_ack.expected_effect_id
    assert recon.get("retry_eligible") is False, recon
    assert lost_ack.claim_state_after_reconcile == "consumed"
    assert lost_ack.ids_after_reconcile == lost_ack.ids_after_first  # reconciliation wrote nothing


def test_second_result_default_unknown_observed_state_is_not_an_authoritative_observation(lost_ack):
    second = lost_ack.second
    if second is not None:
        # a refused result carries no destination observation: whatever its default observed_state says is not evidence about the effect
        assert not second.observation, second.observation
    # the authoritative sources (independent readback, reconciliation) show the effect, whatever the second result's observed_state says
    assert len(lost_ack.ids_after_second) == 1
    assert (lost_ack.reconcile.get("state") or lost_ack.reconcile.get("status")) in ("applied", "reconciled")


def test_fresh_operation_identity_without_new_authority_cannot_reissue_the_same_effect(lost_ack):
    fresh = lost_ack.fresh
    detail = repr(fresh)
    # refused at a specific stage, with a recorded reason: not merely "something raised"
    decision_refused = fresh["decision"] in ("hold", "refused", "denied") or (fresh["decision"] is not None and fresh["decision"] != "authorized")
    if decision_refused:
        assert fresh["decision_reasons"], detail
    elif fresh["decision_raised"] is not None:
        assert fresh["decision_raised"].get("type") and (fresh["decision_raised"].get("code") or fresh["decision_raised"].get("message")), detail
    elif fresh["claim_raised"] is not None:
        assert fresh["claim_raised"].get("type") and (fresh["claim_raised"].get("code") or fresh["claim_raised"].get("message")), detail
    else:
        assert fresh["execute_status"] == "denied" or fresh["execute_raised"] is not None, detail
    assert fresh["executed"] is False, detail
    assert fresh["execute_status"] != "executed", detail
    assert lost_ack.ids_final == [lost_ack.expected_effect_id], detail  # still exactly the one original effect
    assert lost_ack.ids_final == lost_ack.ids_after_reconcile, detail
