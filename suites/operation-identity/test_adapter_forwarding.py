"""F1 (R1 finding 1): the runtime adapter hands the control plane's rule-revision profile to its per-call workflow view
whenever the host configured one, not only when freshness/0.1 is on.

SPDX-License-Identifier: Apache-2.0

Scenario: only rule-revision/0.1 is configured (no freshness). The policy digest is adopted at decision time; the policy content
is then edited under the same version before the effect. The control plane's own workflow refuses the effect
(`policy_status_unknown`, "authorization-critical inputs changed before effect"). The runtime executor builds a fresh workflow
view per call; a view without the profile executes the effect (R1 repro: `view execute: acknowledged`).
Opt-in behaviour: fails on runtime main 6bfb77ee by design (the adapter forwards the profile only with freshness).
"""
from __future__ import annotations

import pytest

from _oi_flow import Flow


def _adopt_policy(flow):
    import agent_control_plane.bounded as cp
    from agent_control_plane.rule_revision import RuleRevision, RuleRevisionProfile, append_rule_revision
    ref = flow.tba.POLICY_REF
    digest = cp.commitment({"policy": "v1"})
    flow.r.policies[ref].digest = digest
    flow.f.rule_revision_profile = RuleRevisionProfile(signers=["urn:cognous:principal:rule-signer"])
    append_rule_revision(flow.f.records, flow.f.rule_revision_profile, RuleRevision(
        revision_id="adopt-1", rule_kind="policy", rule_ref=ref, to_digest=digest, reviser="urn:cognous:principal:reviser",
        signer="urn:cognous:principal:rule-signer", reason="adopt fixture policy", recorded_at=flow.NOW.isoformat()))
    flow.policy_ref = ref


def test_unadopted_policy_digest_is_refused_at_effect_time_through_the_runtime_adapter(tmp_path):
    mp = pytest.MonkeyPatch()
    try:
        flow = Flow(tmp_path / "edited", mp, identity=False, wide=False, setup=_adopt_policy)
        assert flow.f.runtime_authority_profile.freshness is None  # the point: no freshness profile
        import agent_control_plane.bounded as cp
        flow.r.policies[flow.policy_ref].digest = cp.commitment({"policy": "edited"})  # same version, unadopted content
        # the control plane's own workflow refuses (the control)
        with pytest.raises(PermissionError, match="authorization-critical inputs changed"):
            flow.f.execute(flow.p, flow.d1, adapter_id=flow.p.adapter_id, now=flow.NOW)
        # and so must the runtime route, which builds its own workflow view
        result = flow.run(flow.d1)
        assert result.status == "denied", result.error
        assert flow.ledger_effect_ids() == []
    finally:
        mp.undo()


def test_adopted_policy_digest_still_executes_through_the_runtime_adapter(tmp_path):
    """Control: the same configuration with the adopted content executes, so the refusal above is the digest and not the setup."""
    mp = pytest.MonkeyPatch()
    try:
        flow = Flow(tmp_path / "adopted", mp, identity=False, wide=False, setup=_adopt_policy)
        result = flow.run(flow.d1)
        assert result.status == "executed", result.error
        assert len(flow.ledger_effect_ids()) == 1
    finally:
        mp.undo()
