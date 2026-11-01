"""T15. Profile-flag forwarding completeness (ideas D32, A05, tier 6; regression guard for R1 finding 1).

SPDX-License-Identifier: Apache-2.0

Attacker: a misconfiguration or an older caller: a profile set on the host control plane workflow that the runtime adapter
drops when it builds its per-call workflow view, so the effect-time check runs without it.
Method: the runtime PinnedControlPlaneExecutor builds a fresh workflow view per call from the host workflow. The host workflow's
class is swapped for a recording subclass (no behaviour change), every combination of rule-revision, freshness, operation
identity and holder inventory is configured on the host, timing settings are set to non-default values, and every constructor
parameter of BoundedAuthorizationWorkflow (generated from its signature, so a new parameter forces a new case) is compared
between host and view.
Invariant: every setting is forwarded, or construction fails; none is silently dropped. The two parameters that are replaced by
design (destination -> the adapter, records -> the reconciliation capture over the same store) are listed.

Does not prove: enforcement of each profile at effect time (each profile's own suite covers that; here only forwarding);
the witness profile, which is not a workflow setting (a separate publish/verify step); route C.
"""
from __future__ import annotations

import inspect
import itertools

import pytest

from _adv import flow
from conftest import observe

T = "T15"
DNP = "forwarding only (enforcement is covered by each profile's own suite); witness is not a workflow setting; route C not run"
REPLACED_BY_DESIGN = {"destination": "the per-request runtime adapter", "records": "a capture wrapper over the same record store"}
FLAGS = ("rule_revision", "freshness", "operation_identity", "holder_inventory")


def _configure(fl, flags):
    from agent_control_plane.holder_inventory import AuthorityHolder, HolderInventory
    from agent_control_plane.rule_revision import RuleRevisionProfile
    updates = {}
    if "freshness" in flags:
        from agent_control_plane.freshness import FreshnessProfile
        updates["freshness"] = FreshnessProfile()
    if "operation_identity" in flags:
        from agent_control_plane.operation_identity import OperationIdentityProfile
        updates["operation_identity"] = OperationIdentityProfile(resolver_id="synthetic-resolver", resolver_version="1")
    if "holder_inventory" in flags:
        updates["holder_inventory"] = HolderInventory(
            inventory_id="inv-1", recorded_by="urn:cognous:principal:inventory-owner", recorded_at=fl.NOW.isoformat(),
            holders=[AuthorityHolder(holder_id="h-routed", kind="routed", enforcement_point="control plane effect check")])
    if updates:
        fl.f.runtime_authority_profile = fl.cfg.model_copy(update=updates).snapshot()
    if "rule_revision" in flags:
        fl.f.rule_revision_profile = RuleRevisionProfile(signers=["urn:cognous:principal:policy-signer"])
    for name in ("status_max_age_seconds", "identity_max_age_seconds", "mandate_max_age_seconds", "approval_max_age_seconds"):
        setattr(fl.f, name, 59)
    fl.f.clock_tolerance_seconds = 4


def _views(fl):
    host_cls = fl.f.__class__
    seen = []

    class Recording(host_cls):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            seen.append(self)
    fl.f.__class__ = Recording
    try:
        fl.run(fl.d1)
    finally:
        fl.f.__class__ = host_cls
    return seen


COMBOS = [c for n in range(len(FLAGS) + 1) for c in itertools.combinations(FLAGS, n)]


@pytest.mark.parametrize("flags", COMBOS, ids=["+".join(c) or "none" for c in COMBOS])
def test_every_workflow_setting_reaches_the_effect_time_view(cprt, tmp_path, monkeypatch, flags):
    from agent_control_plane.bounded import BoundedAuthorizationWorkflow
    fl = flow(tmp_path, monkeypatch)
    _configure(fl, set(flags))
    views = _views(fl)
    assert len(views) == 1, "the adapter did not build exactly one per-call workflow view"
    view = views[0]
    params = [p for p in inspect.signature(BoundedAuthorizationWorkflow.__init__).parameters if p != "self"]
    dropped = {}
    for name in params:
        if name in REPLACED_BY_DESIGN:
            continue
        host_value, view_value = getattr(fl.f, name), getattr(view, name)
        if host_value != view_value:
            dropped[name] = {"host": repr(host_value)[:80], "view": repr(view_value)[:80]}
    observe(T, f"forwarding with {'+'.join(flags) or 'no profile'}", "prevented" if not dropped else "reproduced failure",
            does_not_prove=DNP, detail={"dropped": dropped, "replaced_by_design": REPLACED_BY_DESIGN})
    assert dropped == {}, dropped
    assert view.records is not fl.f.records  # replaced by design (listed above)


def test_positive_control_all_flags_on_view_carries_every_profile(cprt, tmp_path, monkeypatch):
    fl = flow(tmp_path, monkeypatch)
    _configure(fl, set(FLAGS))
    [view] = _views(fl)
    profile = view.runtime_authority_profile
    assert profile.freshness is not None and profile.operation_identity is not None and profile.holder_inventory is not None
    assert view.rule_revision_profile is not None
