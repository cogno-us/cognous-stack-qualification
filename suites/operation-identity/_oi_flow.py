"""Composed control-plane + runtime flow for the operation-identity scenarios (synthetic, no network effects).

SPDX-License-Identifier: Apache-2.0

Route: control plane BoundedAuthorizationWorkflow -> runtime PinnedControlPlaneExecutor -> SQLite destination.
The control plane fixtures are the component's own (`tests.test_runtime_authority.setup_flow`), as in suites/runtime-authority.

MINIMAL IN-TEST DELAYED-COMMIT DESTINATION. ``DelayedMixin`` below is a stand-in for the CI destination delayed-commit mode
that stream N3 owns (addendum 101726_B, decision 4). It has no in-flight or committed-but-invisible state: it runs a one-shot
hook at a named point of the first attempt (``observe``: after the check, before dispatch; ``commit``: inside the destination,
before the commit lands) or defers the first commit and loses its acknowledgement (``defer``), and lands it on ``land()``.
Replace it with the N3 destination when that exists.
"""
from __future__ import annotations

import pathlib
import sqlite3

OPERATION = "op-order-100/refund-1"
RESOLVER_ID, RESOLVER_VERSION = "synthetic-resolver", "1"
EXPECTED_TODAY_RUN = ("run", "control plane main 5f5ae03f and runtime main 10a11d03, pristine checkouts, this suite with identity=False")


class DelayedMixin:
    """MINIMAL IN-TEST delayed-commit behaviour (see module docstring)."""

    def _delayed_init(self):
        self.hooks, self.deferred, self.defer_next = {}, None, False

    def _fire(self, name):
        hook = self.hooks.pop(name, None)
        if hook is not None:
            hook()

    def observe_bound(self, snapshot):
        self._fire("observe")
        return super().observe_bound(snapshot)

    def commit(self, snapshot, **kwargs):
        self._fire("commit")
        if self.defer_next:
            self.defer_next = False
            self.deferred = (snapshot, kwargs)
            raise TimeoutError("synthetic acknowledgement lost; commit has not landed yet")
        return super().commit(snapshot, **kwargs)

    def land(self):
        """The deferred first commit finally lands (the provider processed it late)."""
        snapshot, kwargs = self.deferred
        self.deferred = None
        return super().commit(snapshot, **kwargs)


def destination(path, *, identity, effective_grant=False):
    if identity and effective_grant:
        from engine.operation_identity_destination import OperationIdentityEffectiveGrantDestination as Base
    elif identity:
        from engine.operation_identity_destination import OperationIdentityDestination as Base
    else:
        from engine.safe_executor import DurableRefundDestination as Base

    class Delayed(DelayedMixin, Base):
        def __init__(self, root):
            Base.__init__(self, root)
            self._delayed_init()
    return Delayed(path)


class Flow:
    """One disposable flow. ``d1`` is the revision-1 decision; r1 is its execution."""

    def __init__(self, work, mp, *, identity=True, wide=True, effective_grant=False, live_observation_clock=False):
        import agent_control_plane.bounded as cp
        import tests.test_bounded_authorization as tba
        import tests.test_runtime_authority as tra
        from engine.control_plane_adapter import PinnedControlPlaneExecutor
        from engine.safe_executor import LocalExecutionPolicy
        self.cp, self.tba, self.tra, self.mp, self.work, self.identity = cp, tba, tra, mp, pathlib.Path(work), identity
        self.NOW, self.PROFILE, self.ISSUER = tba.NOW, tba.PROFILE, tba.ISSUER
        mp.setattr(cp, "_now", lambda: self.NOW)
        if wide:  # let the cumulative cap allow a second effect, so only identity can prevent it
            original = tba.manifest

            def wide_manifest():
                m = original()
                for action in m["actions"]:
                    action["effect_limits"]["max_effects"] = 2
                return m
            mp.setattr(tba, "manifest", wide_manifest)
            mp.setattr(tra, "manifest", wide_manifest)
        self.p, self.r, self.f, self.cfg = tra.setup_flow(self.work / "cp")
        if wide:
            ctx = self.r.contexts[self.PROFILE]
            ctx["requirement"]["permissions"][0]["max_effects"] = 2
            ctx["grant"]["permissions"][0]["max_effects"] = 2
        if identity:
            from agent_control_plane.operation_identity import OperationIdentityProfile
            self.cfg = self.cfg.model_copy(update={"operation_identity": OperationIdentityProfile(
                resolver_id=RESOLVER_ID, resolver_version=RESOLVER_VERSION)})
            self.r.contexts[self.PROFILE]["runtime_authority"]["operation_id"] = OPERATION
            tra.bind_approval(self.r, self.cfg)
            self.f.runtime_authority_profile = self.cfg.snapshot()
        self.dest = destination(self.work / "sqlite", identity=identity, effective_grant=effective_grant)
        self.digest = None
        if effective_grant:  # bind the effective-grant digest in the issuer-approved extension (opt-in, already supported)
            from engine.effective_grant import DERIVATION
            grant = self.r.contexts[self.PROFILE]["grant"]
            self.digest = self.dest.set_effective_grant(principal=self.p.principal, grant_id=grant["grant_id"],
                                                        revision=grant["revision"], permissions=self.p.requested_permissions)
            self.r.contexts[self.PROFILE]["runtime_authority"].update(expected_effective_grant_digest=self.digest,
                                                                      effective_grant_derivation_version=DERIVATION)
            tra.bind_approval(self.r, self.f.runtime_authority_profile or self.cfg)
        self.policy = LocalExecutionPolicy(
            allowed_institutions=frozenset({tba.INSTITUTION}), allowed_authority_domains=frozenset({"customer-refunds"}),
            allowed_adapters=frozenset({self.p.adapter_id}), allowed_actions=frozenset({self.p.action_id}),
            allowed_target_prefixes=("urn:cognous:synthetic-account:",), allowed_units=frozenset({"USD"}),
            max_amount=1000, max_effects=2)
        # The destination observation is stamped by the party being checked, not by the service clock: by default it stays
        # at the initial time when advance_clock() moves the service clock. ``live_observation_clock`` makes it follow.
        self.obs_now, self.live_observation_clock = self.NOW, live_observation_clock
        self.executor = PinnedControlPlaneExecutor(workflow=self.f, destination=self.dest, policy=self.policy,
                                                   observation_clock=lambda: self.NOW if self.live_observation_clock else self.obs_now)
        self.d1 = self.f.decide(self.p, now=self.NOW)
        assert self.d1.result == "authorized", self.d1.reasons
        self.r2 = None  # (decision, result) of the renewed execution, once it ran

    # -- control-plane side ---------------------------------------------------------------------------------
    def envelope(self, d):
        from engine.safe_executor import EXECUTION_ENVELOPE_VERSION, ExecutionEnvelope, ExecutionOperation
        p = self.p
        fields = {k: getattr(p, k) for k in ["actor", "principal", "manifest_id", "manifest_version", "manifest_digest", "action_id",
                                             "adapter_id", "target", "payload", "payload_commitment", "amount", "unit", "effects",
                                             "requirement_id"]}
        op = ExecutionOperation(**fields, institution_id=self.tba.INSTITUTION, authority_domain="customer-refunds",
                                proposal_commitment=self.cp.commitment(p.model_dump(mode="json")),
                                requested_permissions=tuple(p.requested_permissions), authority_context_id=p.authority_context_ref,
                                grant_id=d.binding.grant_id, grant_revision=d.binding.grant_revision,
                                effective_max_effects=d.binding.effective_max_effects)
        return ExecutionEnvelope(EXECUTION_ENVELOPE_VERSION, d.decision_id, d.effect_id, op)

    def run(self, d):
        return self.executor.execute(envelope=self.envelope(d), proposal=self.p, decision=d, now=self.NOW)

    def publish_revision(self, revision):
        """The authority side publishes a new revision of the same grant (a renewal candidate)."""
        ctx = self.r.contexts[self.PROFILE]
        ctx["grant"]["revision"] = revision
        for status in self.r.statuses.values():
            status.revision = revision
        for approval in self.r.approvals.values():
            approval.grant_revision = revision
        self.tra.bind_approval(self.r, self.f.runtime_authority_profile or self.cfg)

    def advance_clock(self, seconds):
        """Advance the service clock and the evaluation time, and refresh every input the resolver serves."""
        from datetime import timedelta
        new = self.NOW + timedelta(seconds=seconds)
        self.NOW = new
        self.mp.setattr(self.cp, "_now", lambda: new)
        r = self.r
        for collection in (r.statuses, r.identities, r.mandates, r.approvals, r.policies, r.conflicts, r.evidence):
            for item in collection.values():
                item.observed_at = new.isoformat()
        for status in r.evidence.values():
            self.tra.sign_evidence(status)  # the signed statement carries observed_at

    def renewed_effect_id(self, revision="2"):
        """The effect id the proposal gets under ``revision`` (computed, no decision taken)."""
        cp = self.cp
        return cp.commitment({"proposal": cp.commitment(self.p.model_dump(mode="json", exclude_none=False)),
                              "grant_id": self.d1.binding.grant_id, "grant_revision": revision})

    def renew_and_commit_r2(self):
        """Issuer renewal to revision 2, then the second execution to completion (r2)."""
        self.publish_revision("2")
        if self.identity:
            self.f.record_renewal(OPERATION, to_revision="2", written_by=self.ISSUER, now=self.NOW)
        d2 = self.f.decide(self.p, now=self.NOW)
        assert d2.result == "authorized", d2.reasons
        self.r2 = (d2, self.run(d2))
        return self.r2

    # -- independent reads ------------------------------------------------------------------------------------
    def ledger_effect_ids(self):
        uri = pathlib.Path(self.dest.path).resolve().as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=10)
        try:
            return [row[0] for row in conn.execute("SELECT effect_id FROM effects ORDER BY effect_id")]
        finally:
            conn.close()

    def record(self):
        return self.f.records.load()

    def latest_attempts(self):
        out = {}
        for item in self.record().attempts:
            out[item.attempt_id] = item
        return list(out.values())
