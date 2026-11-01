"""L5 probe scenarios (addendum 101726_B, L5/N4): revocation propagation across enumerated authority holders.

SPDX-License-Identifier: Apache-2.0

Scenarios: ``probe_routed_and_self_credentialed_holders``, ``probe_without_control_is_inconclusive``, plus the opt-in profile
behaviour that gives the probe its consequence: classes flagged ``requires_revocation_assurance`` hold until a holder inventory
exists (control plane ``RuntimeAuthorityProfile.holder_inventory``).

PROVENANCE of "expected today" (template leg e), per test:

* ``probe_routed_and_self_credentialed_holders``  RUN. The probe uses only code on control plane main fd0d5e0 and runtime main
  6bfb77ee (default path, no profile) and passes on pristine checkouts of them: the routed holder gets one refusal row; the
  self-credentialed holder's effect lands in the destination with no refusal row and no control-plane record (one unrecorded
  outcome). Reading the code (101726_B, L5) predicted this; the run confirmed it. The self-credentialed holder is MODELLED as a
  direct insert into the destination's ``effects`` table, which is what holding a destination credential permits.
* ``probe_without_control_is_inconclusive``  RUN, same pristine checkouts.
* ``requires_revocation_assurance_*``  new opt-in behaviour: no expected-today value; fails on those mains by design (the field
  and the inventory are absent). The default-path companion (``flag_unset_default_path_unchanged``) is RUN and passes today.

What these prove: a probe that has a positive control attributes a refusal to the revocation and reports, per enumerated holder,
a witnessed refusal or ``coverage_unknown`` (never "expired"); a self-credentialed holder is surfaced as unenumerated authority
needing containment; a probe without a valid control claims nothing. What they do NOT prove: anything about a holder nobody
enumerated (the inventory is the control), that a self-credentialed holder's authority was revoked (it was not), or that holders
other than the two modelled behave alike.
"""
from __future__ import annotations

import json

import pytest

import _refusal_template as T
import _holder_probe as P
from _oi_flow import Flow

PRINCIPAL = "urn:cognous:principal:refund-service"
ROUTED, SELF = P.HOLDERS[0]["holder_id"], P.HOLDERS[1]["holder_id"]


def record(record_property, name, result):
    record_property("principal", PRINCIPAL)
    record_property(name, json.dumps(result, indent=2, sort_keys=True, default=str))


def test_probe_routed_and_self_credentialed_holders(tmp_path, record_property):
    """Template legs a-e for the routed holder (run_refusal_scenario), then the two-holder probe and its classification."""
    templated = T.run_refusal_scenario(P.ProbeAdapter(), P.SPEC, tmp_path / "template", pytest.MonkeyPatch)
    assert templated.legs_passed == T.LEGS and templated.mutation["detected"] and templated.mutation["effect_still_blocked"]

    result = P.run_holder_probe(tmp_path / "probe")
    record(record_property, "l5_probe", result)
    assert result["verdict"] == "conclusive" and result["control"]["reached_destination_once"] is True
    by_holder = {h["holder_id"]: h for h in result["holders"]}
    assert by_holder[ROUTED]["outcome"] == "refused" and by_holder[ROUTED]["ledger_rows"] == 0 and by_holder[ROUTED]["refusal_ids"]
    assert by_holder[SELF]["outcome"] == "effect_landed_unrecorded" and by_holder[SELF]["ledger_rows"] == 1 and not by_holder[SELF]["refusal_ids"]
    # one refusal, one unrecorded outcome
    assert [h["holder_id"] for h in result["witnessed_refusals"]] == [ROUTED]
    assert [h["holder_id"] for h in result["unenumerated_authority_needing_containment"]] == [SELF]
    unknown = result["unenumerated_authority_needing_containment"][0]
    assert unknown["classification"] == T.CLASSIFICATION_UNKNOWN == "coverage_unknown"
    for word in ("expired", "revoked", "lapsed", "inactive"):
        assert word not in json.dumps(unknown).lower().replace("authority_change", ""), word   # never labelled as having ended


def test_probe_without_control_is_inconclusive(tmp_path, record_property):
    """No positive control, or a control that did not reach the destination under the same call: the verdict is inconclusive, the
    refusal is not attributed to the revocation, and every holder stays coverage_unknown."""
    omitted = P.run_holder_probe(tmp_path / "omitted", with_control=False)
    broken = P.run_holder_probe(tmp_path / "broken", break_control=True)
    record(record_property, "l5_probe_no_control", omitted)
    record(record_property, "l5_probe_broken_control", broken)
    for label, result in (("omitted", omitted), ("broken", broken)):
        assert result["verdict"] == "inconclusive" and result["inconclusive_reasons"], label
        assert result["witnessed_refusals"] == [], label
        assert {h["holder_id"] for h in result["unenumerated_authority_needing_containment"]} == {ROUTED, SELF}, label
        assert {h["classification"] for h in result["unenumerated_authority_needing_containment"]} == {"coverage_unknown"}, label
    assert omitted["control"]["ran"] is False and "no positive control was run" in omitted["inconclusive_reasons"]
    assert broken["control"]["ran"] is True and broken["control"]["reached_destination_once"] is False
    # the raw outcome is still reported: the routed holder was refused, but that is not claimed as witnessed revocation
    assert {h["holder_id"]: h["outcome"] for h in broken["holders"]}[ROUTED] == "refused"


def test_probe_with_refusal_writer_disabled_fails_the_probe(tmp_path):
    """Mutation check on the probe itself: with the refusal writer disabled the routed holder produces no evidence row, so the probe
    cannot call the refusal witnessed (inconclusive, not a pass)."""
    class Muted(P.ProbeAdapter):
        def apply_change(self, flow):
            super().apply_change(flow)
            self.disable_refusal_writer(flow)
    result = P.run_holder_probe(tmp_path / "muted", adapter=Muted())
    assert result["verdict"] == "inconclusive" and result["witnessed_refusals"] == []
    assert {h["holder_id"]: h["outcome"] for h in result["holders"]}[ROUTED] == "no_outcome"


# ---------------------------------------------------------------------------------------------------- profile (new)
def flagged(inventory):
    """Flow setup: flag every action class ``requires_revocation_assurance`` and (optionally) configure a holder inventory."""
    def setup(flow):
        from agent_control_plane.holder_inventory import AuthorityHolder, HolderInventory
        actions = {k: v.model_copy(update={"requires_revocation_assurance": True}) for k, v in flow.cfg.actions.items()}
        updates = {"actions": actions}
        if inventory:
            updates["holder_inventory"] = HolderInventory(
                inventory_id="inventory-1", recorded_by="urn:cognous:principal:inventory-owner", recorded_at=flow.NOW.isoformat(),
                holders=[AuthorityHolder(holder_id=h["holder_id"], kind=h["kind"], enforcement_point=h["enforcement_point"]) for h in P.HOLDERS])
        flow.cfg = flow.cfg.model_copy(update=updates)
        flow.tra.bind_approval(flow.r, flow.cfg)
        flow.f.runtime_authority_profile = flow.cfg.snapshot()
    return setup


def test_requires_revocation_assurance_class_holds_until_inventory_exists(tmp_path):
    """Positive control: with an inventory the flagged class is authorised. Remove the inventory (same call, same flagged class)
    and the decision is a hold naming ``holder_inventory_missing``; an inventory that enumerates no holder does not count."""
    mp = pytest.MonkeyPatch()
    try:
        flow = Flow(tmp_path, mp, identity=False, setup=flagged(inventory=True))     # authorised (asserted by Flow)
        assert flow.d1.result == "authorized"
        from agent_control_plane.holder_inventory import HolderInventory
        for inventory in (None, HolderInventory(inventory_id="empty", recorded_by="urn:x", recorded_at=flow.NOW.isoformat(), holders=[])):
            cfg = flow.cfg.model_copy(update={"holder_inventory": inventory})
            flow.tra.bind_approval(flow.r, cfg)
            flow.f.runtime_authority_profile = cfg.snapshot()
            decision = flow.f.decide(flow.p, now=flow.NOW)
            assert decision.result == "hold" and "holder_inventory_missing" in decision.reasons
    finally:
        mp.undo()


def test_requires_revocation_assurance_hold_reaches_no_destination(tmp_path):
    mp = pytest.MonkeyPatch()
    try:
        flow = Flow(tmp_path, mp, identity=False, setup=flagged(inventory=True))
        cfg = flow.cfg.model_copy(update={"holder_inventory": None})
        flow.tra.bind_approval(flow.r, cfg)
        flow.f.runtime_authority_profile = cfg.snapshot()
        held = flow.f.decide(flow.p, now=flow.NOW)
        assert held.result == "hold"
        assert flow.ledger_effect_ids() == []
    finally:
        mp.undo()


def test_flag_unset_default_path_unchanged(tmp_path):
    """RUN today: with the flag and the inventory unset nothing about the profile or the decision changes."""
    mp = pytest.MonkeyPatch()
    try:
        flow = Flow(tmp_path, mp, identity=False)
        dumped = json.dumps(flow.cfg.model_dump(mode="json"))
        assert "requires_revocation_assurance" not in dumped and "holder_inventory" not in dumped
        assert flow.d1.result == "authorized"
    finally:
        mp.undo()
