"""Worker A helper: a Control-Plane-WORKFLOW-issued claim aligned with a Runtime governed scope (V08 Tier 1, area `authority`).

Fixture mechanics only. Reused (imported, not re-implemented), as permitted after the inventory commit:
  * Runtime `test_registry_selection_authority` (v4): Registry record/statement builders, Ed25519 test keys, `Env`.
  * Control Plane `tests.v02_support.tenant_flow` / `tests.test_bounded_authorization`: a real BoundedAuthorizationWorkflow with a
    runtime-authority profile whose approvals commit to the approval-side policy-binding/0.1, and the synthetic tenant/institution/domain.
New here: the Registry scope and record payload are built FROM the Control Plane fixture's own tenant, institution, authority domain, action,
adapter and unit, so both sides are aligned; the claim is produced by `provision_local_execution_claim` / `materialize_local_execution_claim`
(never by the `commitment()` function over a hand-written claim). Forged claims in the attack cases are derived FROM a workflow-issued claim.
"""
from __future__ import annotations

import contextlib
import copy
import dataclasses
import sqlite3
import sys
from pathlib import Path

import test_registry_selection_authority as v4  # Runtime test module (Registry builders); path set by the shared conftest
from registry_successor import common as c
from registry_successor import v2_f1ab as f1ab
from registry_successor import verify as vfy
from registry_adapters import ed25519_verifier as ed
import r08_support as r
import s01_support as s

import os
_CP_ROOT = str(Path(os.environ["V08_COMPONENTS_DIR"]).resolve() / "control_plane")
if _CP_ROOT not in sys.path:
    sys.path.insert(0, _CP_ROOT)
from tests import v02_support as v02  # noqa: E402  (Control Plane test support)
from tests import test_bounded_authorization as cpt  # noqa: E402
import agent_control_plane.bounded as cp_bounded  # noqa: E402
import agent_control_plane.local_authority_effect as cp_effect  # noqa: E402
from agent_control_plane.bounded import commitment as cp_commitment  # noqa: E402

from engine.atomic_local_control_plane_executor import AtomicLocalControlPlaneExecutor  # noqa: E402
from engine.safe_executor import (EXECUTION_ENVELOPE_VERSION, ExecutionEnvelope, ExecutionOperation, LocalExecutionPolicy)  # noqa: E402

CP_NOW = cpt.NOW
TENANT, INSTITUTION, DOMAIN = cpt.TENANT, cpt.INSTITUTION, v02.DOMAIN
CONSUMER, OPERATION = v02.CONSUMER, v02.OPERATION
FIELDS = v4.FIELDS
WINDOW = {"valid_from": "2026-10-05T00:00:00Z", "valid_until": "2026-10-06T00:00:00Z"}


@contextlib.contextmanager
def cp_clock():
    """The Control Plane suite pins its synthetic clock with an autouse fixture; do the same for the duration of one case."""
    old = cp_bounded._now
    cp_bounded._now = lambda: CP_NOW
    try:
        yield
    finally:
        cp_bounded._now = old


def aligned_scope(**over):
    scope = dict(consumer_id=CONSUMER, tenant=TENANT, institution=INSTITUTION, authority_domain=DOMAIN, operation=OPERATION, family=f1ab.FAMILY_F1AB)
    scope.update(over)
    return scope


def needed_payload():
    """The five sets exactly covering the Control Plane fixture's proposal (so an EQUAL policy is the minimal policy that executes it)."""
    p = cpt.tenant_proposal()
    return {"allowed_actions": [p.action_id], "allowed_adapters": [p.adapter_id], "allowed_units": [p.unit],
            "allowed_institutions": [INSTITUTION], "allowed_authority_domains": [DOMAIN]}


class AEnv(v4.Env):
    """The Runtime governed store (v4.Env) with the Registry scope, trust grant and clock aligned with the Control Plane fixture."""

    def __init__(self, tmp_path, *, scope=None, payload=None):
        Path(tmp_path).mkdir(parents=True, exist_ok=True)
        super().__init__(tmp_path)
        self.now = CP_NOW
        self.scope = scope or aligned_scope()
        self.payload = payload or needed_payload()
        sc = self.scope
        self.ctx = c.ExpectedContext(sc["consumer_id"], sc["tenant"], sc["institution"], sc["authority_domain"], sc["operation"])
        self.grants = [vfy.AuthorityGrant(sc["consumer_id"], sc["tenant"], sc["institution"], sc["authority_domain"], sc["operation"])]

    def add_scope(self, scope):
        """Authorise the (single, test) issuer for one more governed scope, e.g. a second operation. Call before boot()."""
        self.grants.append(vfy.AuthorityGrant(scope["consumer_id"], scope["tenant"], scope["institution"], scope["authority_domain"], scope["operation"]))

    def mk_trust(self, version=1, valid_until="2026-10-27T00:00:00Z", **kw):
        return vfy.TrustSnapshot("snap-test-1", version, valid_until,
                                 (vfy.IssuerEntry(s.KEY_ID, "issuer-test-1", "ed25519", v4.PK, tuple(self.grants)),), **kw)

    def boot(self, version=1, **tkw):
        self.dest.sync_selection("baseline", determination_ref=v4.DET)
        self.trust = self.mk_trust(version, **tkw)
        self.dest.sync_selection("snapshot", trust=self.trust)
        return self

    def sync(self, version, **tkw):
        t = self.mk_trust(version, **tkw)
        res = self.dest.sync_selection("snapshot", trust=t)
        self.trust = t
        return res

    def record(self, **over):
        over.setdefault("payload", copy.deepcopy(self.payload))
        return v4.reg_record(**over)

    def statement(self, rec, scope=None, **over):
        sc = scope or self.scope
        base = dict(consumer_id=sc["consumer_id"], scope={"tenant": sc["tenant"], "institution": sc["institution"], "authority_domain": sc["authority_domain"]},
                    operation=sc["operation"], effective=dict(WINDOW), issued_at="2026-10-04T00:00:00Z")
        base.update(over)
        return v4.select_stmt(rec, **base)

    def ctx_of(self, sc):
        return c.ExpectedContext(sc["consumer_id"], sc["tenant"], sc["institution"], sc["authority_domain"], sc["operation"])

    def activate_stmt(self, stmt, rec, scope=None):
        return self.dest.activate_selection(record_text=r.dumps(rec), selection_text=v4.text(stmt),
                                            context=self.ctx_of(scope) if scope else self.ctx, trust=self.trust,
                                            verifier=ed.Ed25519Verifier())

    def withdraw_stmt(self, stmt):
        return self.dest.withdraw_selection(selection_text=v4.text(stmt), context=self.ctx, trust=self.trust, verifier=ed.Ed25519Verifier())

    def state(self, gs=None):
        return self.dest.read_selection_state(gs or self.scope)


def policy_from(sets, **over):
    base = {k: frozenset(sets[k]) for k in FIELDS}
    base.update(over)
    return LocalExecutionPolicy(allowed_target_prefixes=("urn:cognous:synthetic-account:",), max_amount=1000.0, max_effects=2, **base)


def binding_for(env: AEnv, state, policy_sets, scope=None) -> dict:
    sc = scope or env.scope
    return {"binding_profile": "ocs-policy-binding/1", "record_id": state.record_id, "record_version": state.record_version,
            "record_digest": state.record_digest, "selection_id": state.selection_id, "selection_epoch": state.selection_epoch,
            "selection_digest": state.selection_digest, "family": sc["family"], "consumer_id": sc["consumer_id"],
            "scope": {"tenant": sc["tenant"], "institution": sc["institution"], "authority_domain": sc["authority_domain"]},
            "operation": sc["operation"],
            "effective_policy_digest": v4.ident.effective_policy_digest(f1ab.FAMILY_F1AB, {k: sorted(policy_sets[k]) for k in FIELDS}),
            "activation_ref": state.activation_ref, "trust_snapshot_version": state.trust_snapshot_version,
            "trust_snapshot_fingerprint": state.trust_snapshot_fingerprint}


def envelope_for(p, d) -> ExecutionEnvelope:
    """Host glue only: the Runtime envelope for the persisted Control Plane decision (all values from the proposal and the decision binding)."""
    b = d.binding
    op = ExecutionOperation(
        actor=p.actor, principal=p.principal, institution_id=INSTITUTION, authority_domain=DOMAIN, manifest_id=p.manifest_id,
        manifest_version=p.manifest_version, manifest_digest=p.manifest_digest, proposal_commitment=b.proposal_commitment, action_id=p.action_id,
        adapter_id=p.adapter_id, target=p.target, payload=copy.deepcopy(p.payload), payload_commitment=p.payload_commitment,
        requested_permissions=tuple(p.requested_permissions), amount=p.amount, unit=p.unit, effects=p.effects,
        authority_context_id=p.authority_context_ref, requirement_id=b.requirement_id, grant_id=b.grant_id, grant_revision=b.grant_revision,
        effective_max_effects=b.effective_max_effects, tenant_id=b.tenant_id)
    return ExecutionEnvelope(EXECUTION_ENVELOPE_VERSION, d.decision_id, d.effect_id, op)


class Issued:
    """One real workflow decision for a given approval-side binding, plus helpers to issue/provision/execute through the real functions."""

    def __init__(self, tmp_path, binding, *, generation=1):
        self.p, self.resolver, self.workflow, self.decision, self.profile = v02.tenant_flow(tmp_path, binding, generation=generation)
        self.binding = binding
        self.chain = ["v02_support.tenant_flow -> BoundedAuthorizationWorkflow.decide (authorized)"]
        self.envelope = envelope_for(self.p, self.decision)

    def materialize(self, *, claim_id, binding="own", budget_id=None, **kw):
        b = self.binding if binding == "own" else binding
        self.chain.append("agent_control_plane.local_authority_effect.materialize_local_execution_claim(policy_binding=...)")
        return cp_effect.materialize_local_execution_claim(
            self.workflow, self.p, self.decision, now=CP_NOW, claim_id=claim_id, budget_id=budget_id or f"budget-{claim_id}",
            **({"policy_binding": b, "expected_consumer_id": CONSUMER, "expected_operation": OPERATION} if b is not None else {}), **kw)

    def provision(self, dest, *, claim_id, binding="own", budget_id=None, **kw):
        b = self.binding if binding == "own" else binding
        self.chain.append("agent_control_plane.local_authority_effect.provision_local_execution_claim(provision=destination.provision_claim, policy_binding=...)")
        return cp_effect.provision_local_execution_claim(
            self.workflow, self.p, self.decision, provision=dest.provision_claim, now=CP_NOW, claim_id=claim_id,
            budget_id=budget_id or f"budget-{claim_id}",
            **({"policy_binding": b, "expected_consumer_id": CONSUMER, "expected_operation": OPERATION} if b is not None else {}), **kw)


def forged_from(claim, *, claim_id=None, binding_changes=None, top_changes=None, scope_changes=None) -> dict:
    """A colluding claim supplier: take a WORKFLOW-ISSUED claim, alter members, and recompute claim_commitment so the claim verifies."""
    raw = claim.model_dump(mode="json", exclude_none=False)
    raw.pop("claim_commitment")
    if claim_id:
        raw["claim_id"] = claim_id
        raw["budget_id"] = f"budget-{claim_id}"
    pb = copy.deepcopy(raw["policy_binding"]) if raw.get("policy_binding") is not None else None
    if pb is not None:
        pb.update(binding_changes or {})
        if scope_changes:
            pb["scope"] = {**pb["scope"], **scope_changes}
        raw["policy_binding"] = pb
    raw.update(top_changes or {})
    raw["claim_commitment"] = cp_commitment(raw)
    return raw


def executor(dest, policy):
    return AtomicLocalControlPlaneExecutor(workflow=None, destination=dest, policy=policy)


def counts(dest) -> dict:
    with sqlite3.connect(dest.path) as conn:
        out = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ("effects", "attempts", "authority_effect_receipts_v1", "execution_claims_v1")}
        out["budget_used"] = conn.execute("SELECT COALESCE(SUM(used_effects),0) FROM effect_budgets_v1").fetchone()[0]
        out["claim_states"] = dict(conn.execute("SELECT claim_id, state FROM execution_claims_v1").fetchall())
        return out


def refusal_of(result):
    return (result.control_plane_evidence or {}).get("selection_refusal")


def receipt_guard(dest):
    import json
    with sqlite3.connect(dest.path) as conn:
        rows = conn.execute("SELECT receipt_json FROM authority_effect_receipts_v1").fetchall()
    return [json.loads(x[0]).get("selection_guard") for x in rows]
