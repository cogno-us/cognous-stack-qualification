"""V08 Tier 1, area `authority` (Worker A, fresh AI session, same organization; independent test DESIGN, not independent external qualification).

Oracles were committed in results/v08-tier1/authority/INVENTORY.md (commit 89621468) before any execution. The verdict is the finding:
HELD only with positive evidence (attack delivered and refused for the intended typed reason, or the legitimate path really executed).

Fixture mechanics reused by import (see _wf.py docstring): Runtime `test_registry_selection_authority` (Registry builders, Env), Control Plane
`tests.v02_support.tenant_flow` (real BoundedAuthorizationWorkflow + runtime-authority approvals committing to the policy binding). Assertions
and attacks are this file's own.
"""
from __future__ import annotations

import copy

import pytest

import _wf as w
from registry_successor import v2_f1ab as f1ab  # noqa: F401

pytestmark = []


@pytest.fixture(autouse=True)
def _cp_clock():
    with w.cp_clock():
        yield


# ------------------------------------------------------------------------------------------------------------------ shared steps
def governed(tmp_path, *, payload=None, policy_sets=None, scope=None, generation=None):
    """Runtime governed store with one activated selection aligned to the Control Plane fixture, and one workflow decision committed to it."""
    env = w.AEnv(tmp_path / "rt", scope=scope, payload=payload).boot()
    rec = env.record()
    stmt = env.statement(rec)
    env.activate_stmt(stmt, rec)
    state = env.state()
    sets = policy_sets or w.needed_payload()
    binding = w.binding_for(env, state, sets)
    iss = w.Issued(tmp_path / "cp", binding, generation=generation or state.policy_generation)
    return env, rec, stmt, state, sets, binding, iss


def stage_ok(ev, name, **facts):
    ev["observed"].setdefault("steps", {})[name] = facts


def judge_refusal(res, c, code, cls, cause=None):
    """HELD only when: no effect/attempt/receipt/budget use, every claim still `issued`, status denied and the typed triple is exactly the intended one."""
    typed = w.refusal_of(res)
    if c["effects"] or c["attempts"] or c["authority_effect_receipts_v1"] or c["budget_used"] or res.status == "executed" or res.attempted:
        return "BREACH", typed
    states_ok = all(v == "issued" for v in c["claim_states"].values())
    if res.status == "denied" and typed and typed["code"] == code and typed["refusal_class"] == cls and (cause is None or typed["cause"] == cause) and states_ok:
        return "HELD", typed
    return "INCONCLUSIVE", typed


def aggregate(verdicts):
    if "BREACH" in verdicts:
        return "BREACH"
    if all(v == "HELD" for v in verdicts):
        return "HELD"
    if "BLOCKED" in verdicts:
        return "BLOCKED"
    return "INCONCLUSIVE"


# ====================================================================================================================== AU-1 (mandatory)
def test_au1_workflow_issued_claim_equal_policy_executes(tmp_path, ev):
    """AU-1 (mandatory) + AU-2 equal. Real workflow issuance through provision_local_execution_claim, then the Runtime destination/executor."""
    ev["scenario"] = "AU-1"
    ev["expected"] = ("successor-profile claim ISSUED BY agent_control_plane provision_local_execution_claim (policy_binding given, aligned tenant/institution/"
                      "authority_domain with the Runtime governed scope) is provisioned by destination.provision_claim and executes: status executed, "
                      "1 effect/1 attempt/1 receipt, claim consumed, budget 1, receipt selection_guard binding_verified with the live activation_ref")
    env, rec, stmt, state, sets, binding, iss = governed(tmp_path)
    ev["observed"].update(workflow_issued=False, scope={"tenant": w.TENANT, "institution": w.INSTITUTION, "authority_domain": w.DOMAIN})
    assert iss.decision.result == "authorized", iss.decision.reasons
    claim = iss.provision(env.dest, claim_id="claim-au1")
    ev["observed"].update(
        workflow_issued=True, call_chain=iss.chain + ["engine.local_authority_effect.AtomicAuthorityEffectDestination.provision_claim (the provision callback)",
                                                         "engine.atomic_local_control_plane_executor.AtomicLocalControlPlaneExecutor.execute -> execute_claim_atomic"],
        claim_profile=claim.profile, claim_type=type(claim).__name__, claim_has_binding=claim.policy_binding is not None,
        claim_scope_matches_binding=(claim.tenant_id, claim.institution_id, claim.authority_domain) == tuple(claim.policy_binding["scope"][k] for k in ("tenant", "institution", "authority_domain")),
        verify_local_execution_claim=w.cp_effect.verify_local_execution_claim(claim),
        decision_id=iss.decision.decision_id, hand_built_claim=False, commitment_function_called_by_test_on_a_claim=False)
    res = w.executor(env.dest, w.policy_from(sets)).execute(envelope=iss.envelope, claim_id="claim-au1")
    c = w.counts(env.dest)
    guard = w.receipt_guard(env.dest)
    ev["observed"].update(status=res.status, error=res.error, counts=c, selection_guard=guard, activation_ref=state.activation_ref)
    ok = (claim.profile == w.cp_effect.LOCAL_AUTHORITY_EFFECT_PROFILE_V2 and claim.policy_binding is not None and res.status == "executed"
          and (c["effects"], c["attempts"], c["authority_effect_receipts_v1"], c["budget_used"]) == (1, 1, 1, 1) and c["claim_states"] == {"claim-au1": "consumed"}
          and len(guard) == 1 and guard[0]["result"] == "binding_verified" and guard[0]["applied"] is True and guard[0]["activation_ref"] == state.activation_ref)
    ev["verdict"] = "HELD" if ok else ("BREACH" if c["effects"] > 1 else "INCONCLUSIVE")
    ev["note"] = "actual workflow issuance exercised end to end with aligned synthetic fixtures; no hand-built claim"
    assert ok


# ====================================================================================================================== AU-2 narrower
def test_au2_workflow_issued_strictly_narrower_policy_executes(tmp_path, ev):
    ev["scenario"] = "AU-2"
    ev["expected"] = ("record payload strictly wider than the executor policy in ALL five sets; workflow-issued claim whose binding effective_policy_digest is the "
                      "NARROWER digest executes: 1/1/1; receipt effective_policy_digest == narrower digest != record digest")
    wide = {k: sorted(v + [f"urn:cognous:extra:{k}"]) for k, v in w.needed_payload().items()}
    env, rec, stmt, state, sets, binding, iss = governed(tmp_path, payload=wide, policy_sets=w.needed_payload())
    strictly = all(set(sets[k]) < set(wide[k]) for k in w.FIELDS)
    claim = iss.provision(env.dest, claim_id="claim-au2")
    res = w.executor(env.dest, w.policy_from(sets)).execute(envelope=iss.envelope, claim_id="claim-au2")
    c, guard = w.counts(env.dest), w.receipt_guard(env.dest)
    ev["observed"].update(workflow_issued=True, call_chain=iss.chain, strictly_narrower_in_all_five_sets=strictly, status=res.status, counts=c,
                          record_policy_digest=state.effective_policy_digest, binding_digest=binding["effective_policy_digest"], selection_guard=guard)
    ok = (strictly and res.status == "executed" and (c["effects"], c["attempts"], c["authority_effect_receipts_v1"]) == (1, 1, 1)
          and guard[0]["effective_policy_digest"] == binding["effective_policy_digest"] != state.effective_policy_digest)
    ev["verdict"] = "HELD" if ok else "INCONCLUSIVE"
    assert ok


# ====================================================================================================================== AU-1 companion: CP refuses to issue
def test_au1_control_plane_refuses_binding_the_approval_did_not_commit_to(tmp_path, ev):
    ev["scenario"] = "AU-1"
    ev["expected"] = ("real provision_local_execution_claim raises PermissionError 'policy binding refused at claim issuance' for a binding whose activation_ref "
                      "or record identity differs from what the approvals committed; the destination holds 0 claims and 0 effects; the honest binding still issues")
    env, rec, stmt, state, sets, binding, iss = governed(tmp_path)
    probes = {}
    verdicts = []
    for name, bad in (("activation_ref_not_committed", dict(binding, activation_ref="sha256:" + "9" * 64)),
                      ("record_id_changes_binding_digest", dict(binding, record_id="f1ab-uncommitted-record"))):
        try:
            iss.provision(env.dest, claim_id="claim-bad-" + name, binding=bad)
            probes[name] = {"issued": True}
            verdicts.append("BREACH")
        except PermissionError as exc:
            msg = str(exc)
            probes[name] = {"raised": type(exc).__name__, "message": msg, "claims_in_destination": w.counts(env.dest)["execution_claims_v1"]}
            verdicts.append("HELD" if "policy binding refused at claim issuance" in msg and w.counts(env.dest)["execution_claims_v1"] == 0 else "INCONCLUSIVE")
        except Exception as exc:  # a different failure is not the intended refusal
            probes[name] = {"raised": type(exc).__name__, "message": str(exc)[:200]}
            verdicts.append("INCONCLUSIVE")
    claim = iss.provision(env.dest, claim_id="claim-honest")
    probes["honest_control_issues"] = {"claim_profile": claim.profile, "claims_in_destination": w.counts(env.dest)["execution_claims_v1"]}
    verdicts.append("HELD" if w.counts(env.dest)["execution_claims_v1"] == 1 else "INCONCLUSIVE")
    ev["observed"].update(workflow_issued=True, probes=probes, counts=w.counts(env.dest))
    ev["verdict"] = aggregate(verdicts)
    assert ev["verdict"] == "HELD", probes


# ====================================================================================================================== AU-3 five-set widening
def test_au3_five_set_widening_under_claim_supplier_collusion(tmp_path, ev):
    ev["scenario"] = "AU-3"
    ev["expected"] = ("for EACH of the five sets independently: a claim derived from the workflow-issued claim with a widened effective_policy_digest and a RECOMPUTED "
                      "claim_commitment is provisioned (verifies) but execution with the widened executor policy is denied: code policy_identity_mismatch, class REFUSE, "
                      "cause policy_not_subset:<that set>; 0 effects/attempts/receipts, budget 0, claim still issued")
    subs = {}
    verdicts = []
    for field in w.FIELDS:
        sub = tmp_path / field
        sub.mkdir()
        env, rec, stmt, state, sets, binding, iss = governed(sub)
        honest = iss.materialize(claim_id=f"honest-{field}")  # real workflow issuance (not provisioned: the supplier replaces it)
        widened = copy.deepcopy(sets)
        widened[field] = widened[field] + [f"urn:cognous:widen:{field}"]
        wdig = w.v4.ident.effective_policy_digest(f1ab.FAMILY_F1AB, {k: sorted(widened[k]) for k in w.FIELDS})
        forged = w.forged_from(honest, claim_id=f"forged-{field}", binding_changes={"effective_policy_digest": wdig})
        entry = {"honest_claim_workflow_issued": True, "honest_digest": binding["effective_policy_digest"], "widened_digest": wdig,
                 "commitment_recomputed": forged["claim_commitment"] != honest.claim_commitment,
                 "forged_verifies": w.cp_effect.verify_local_execution_claim(forged)}
        try:
            env.dest.provision_claim(forged)
            entry["provisioned"] = True
        except Exception as exc:
            entry.update(provisioned=False, provision_error=f"{type(exc).__name__}: {str(exc)[:160]}")
            subs[field] = entry
            verdicts.append("INCONCLUSIVE")  # the attack was not delivered
            continue
        res = w.executor(env.dest, w.policy_from(widened)).execute(envelope=iss.envelope, claim_id=f"forged-{field}")
        c = w.counts(env.dest)
        v, typed = judge_refusal(res, c, "policy_identity_mismatch", "REFUSE", f"policy_not_subset:{field}")
        entry.update(status=res.status, typed=typed, counts=c, verdict=v)
        subs[field] = entry
        verdicts.append(v)
    ev["observed"].update(workflow_issued=True, subprobes=subs)
    ev["verdict"] = aggregate(verdicts)
    ev["note"] = "five sub-probes (one per set), each in a fresh governed store"
    assert ev["verdict"] == "HELD", subs


# ====================================================================================================================== AU-4 stale activation
def test_au4_stale_activation_refuses_and_new_activation_executes(tmp_path, ev):
    ev["scenario"] = "AU-4"
    ev["expected"] = ("claim issued under activation 1, selection re-activated at epoch 2 (new activation_ref, generation 2): the old claim is denied "
                      "selection_epoch_stale / REFUSE_STALE with cause stale_policy_generation, 0 effects; a claim issued by the workflow against the NEW activation executes 1/1/1")
    env, rec, stmt, state1, sets, binding1, iss1 = governed(tmp_path)
    iss1.provision(env.dest, claim_id="claim-old")
    stmt2 = env.statement(rec, epoch=2, supersedes=w.v4.sup(stmt))
    env.activate_stmt(stmt2, rec)
    state2 = env.state()
    ev["observed"].update(activation_ref_1=state1.activation_ref, activation_ref_2=state2.activation_ref, generation_1=state1.policy_generation,
                          generation_2=state2.policy_generation, epoch_2=state2.selection_epoch)
    res_old = w.executor(env.dest, w.policy_from(sets)).execute(envelope=iss1.envelope, claim_id="claim-old")
    c_old = w.counts(env.dest)
    v_old, typed_old = judge_refusal(res_old, c_old, "selection_epoch_stale", "REFUSE_STALE", "stale_policy_generation")
    ev["observed"].update(old_claim=dict(status=res_old.status, typed=typed_old, counts=c_old, verdict=v_old))
    binding2 = w.binding_for(env, state2, sets)
    (tmp_path / "cp2").mkdir()
    iss2 = w.Issued(tmp_path / "cp2", binding2, generation=state2.policy_generation)
    iss2.provision(env.dest, claim_id="claim-new")
    res_new = w.executor(env.dest, w.policy_from(sets)).execute(envelope=iss2.envelope, claim_id="claim-new")
    c_new = w.counts(env.dest)
    guard = w.receipt_guard(env.dest)
    ev["observed"].update(workflow_issued=True, new_claim=dict(status=res_new.status, counts=c_new, selection_guard=guard))
    new_ok = (res_new.status == "executed" and (c_new["effects"], c_new["attempts"], c_new["authority_effect_receipts_v1"]) == (1, 1, 1)
              and c_new["claim_states"] == {"claim-old": "issued", "claim-new": "consumed"} and guard[0]["activation_ref"] == state2.activation_ref)
    ev["verdict"] = "BREACH" if v_old == "BREACH" else ("HELD" if v_old == "HELD" and new_ok else "INCONCLUSIVE")
    assert ev["verdict"] == "HELD"


# ====================================================================================================================== AU-5 withdrawal
def test_au5_withdrawal_between_issuance_and_effect_refuses(tmp_path, ev):
    ev["scenario"] = "AU-5"
    ev["expected"] = "workflow-issued claim, then an authenticated withdrawal: denied selection_withdrawn / REFUSE (not HOLD), 0 effects/attempts/receipts, claim issued"
    env, rec, stmt, state, sets, binding, iss = governed(tmp_path)
    iss.provision(env.dest, claim_id="claim-wd")
    wres = env.withdraw_stmt(w.v4.withdraw_stmt(stmt, 2))
    state_after = env.state()
    res = w.executor(env.dest, w.policy_from(sets)).execute(envelope=iss.envelope, claim_id="claim-wd")
    c = w.counts(env.dest)
    v, typed = judge_refusal(res, c, "selection_withdrawn", "REFUSE")
    ev["observed"].update(workflow_issued=True, withdraw_transition=wres.entry_type, state_after_withdrawal=state_after.status, status=res.status, typed=typed, counts=c)
    ev["verdict"] = v if state_after.status == "withdrawn" else "INCONCLUSIVE"
    assert ev["verdict"] == "HELD"


# ====================================================================================================================== AU-5 revocation
def test_au5_selection_pair_and_issuer_key_revocation_refuse_with_distinct_codes(tmp_path, ev):
    ev["scenario"] = "AU-5"
    ev["expected"] = ("fresh store each: (a) snapshot revokes the (selection_id, epoch) pair -> denied selection_revoked; (b) snapshot revokes the issuer key -> denied "
                      "issuer_key_revoked (distinct code); both REFUSE; 0 effects; claim issued")
    subs, verdicts = {}, []
    for name, kw, code in (("pair", {"revoked_selections": frozenset({("sel-test-1", 1)})}, "selection_revoked"),
                           ("issuer_key", {"revoked_key_ids": frozenset({"key-test-1"})}, "issuer_key_revoked")):
        sub = tmp_path / name
        sub.mkdir()
        env, rec, stmt, state, sets, binding, iss = governed(sub)
        iss.provision(env.dest, claim_id=f"claim-{name}")
        env.sync(2, **kw)
        st_after = env.state()
        res = w.executor(env.dest, w.policy_from(sets)).execute(envelope=iss.envelope, claim_id=f"claim-{name}")
        c = w.counts(env.dest)
        v, typed = judge_refusal(res, c, code, "REFUSE")
        if st_after.status != "revoked":
            v = "INCONCLUSIVE" if v == "HELD" else v
        subs[name] = dict(state_after=st_after.status, status=res.status, typed=typed, counts=c, verdict=v)
        verdicts.append(v)
    ev["observed"].update(workflow_issued=True, subprobes=subs)
    ev["verdict"] = aggregate(verdicts)
    assert ev["verdict"] == "HELD", subs


# ====================================================================================================================== AU-6 legacy
def test_au6_required_scope_binding_less_claim_refused_and_ungoverned_legacy_still_works(tmp_path, ev):
    ev["scenario"] = "AU-6"
    ev["expected"] = ("(a) REQUIRED activation for the claim's scope: a legacy-profile binding-less claim issued by the real workflow is denied selection_missing / REFUSE "
                      "cause scope_required_without_binding, 0 effects; a legacy-profile claim cannot carry a binding. (b) activation only for a DIFFERENT institution: the same "
                      "binding-less legacy claim executes 1/1/1 with guard result fallback_caller_policy, applied False, reason never_activated")
    from tests import v02_support as v02
    verdicts, subs = [], {}
    # (a) required scope, binding-less claim
    a = tmp_path / "a"
    a.mkdir()
    env_a = w.AEnv(a / "rt").boot()
    rec = env_a.record()
    env_a.activate_stmt(env_a.statement(rec), rec)
    p, r_, f, d, cfg = v02.tenant_flow(a / "cp", None, profile_binding=None)
    legacy = w.cp_effect.provision_local_execution_claim(f, p, d, provision=env_a.dest.provision_claim, now=w.CP_NOW, claim_id="legacy-a", budget_id="budget-legacy-a")
    envelope = w.envelope_for(p, d)
    raw = legacy.model_dump(mode="json", exclude_none=False)
    raw["policy_binding"] = w.binding_for(env_a, env_a.state(), w.needed_payload())
    try:
        w.cp_effect.TenantLocalExecutionClaim.model_validate(raw)
        carry = "legacy profile accepted a policy_binding member"
        carry_ok = False
    except Exception as exc:
        carry, carry_ok = f"{type(exc).__name__}: {str(exc)[:140]}", True
    res_a = w.executor(env_a.dest, w.policy_from(w.needed_payload())).execute(envelope=envelope, claim_id="legacy-a")
    c_a = w.counts(env_a.dest)
    v_a, typed_a = judge_refusal(res_a, c_a, "selection_missing", "REFUSE", "scope_required_without_binding")
    if not carry_ok:
        v_a = "BREACH" if v_a == "BREACH" else "INCONCLUSIVE"
    subs["required_scope_legacy_claim"] = dict(claim_profile=legacy.profile, legacy_claim_carries_no_binding=legacy.policy_binding is None, binding_on_legacy_profile=carry,
                                               status=res_a.status, typed=typed_a, counts=c_a, scope_required=env_a.state().scope_required, verdict=v_a)
    verdicts.append(v_a)
    # (b) permitted ungoverned legacy: the only activation is for another institution
    b = tmp_path / "b"
    b.mkdir()
    other_inst = "urn:cognous:institution:other-unit"
    scope_b = w.aligned_scope(institution=other_inst)
    pay_b = dict(w.needed_payload(), allowed_institutions=[other_inst])
    env_b = w.AEnv(b / "rt", scope=scope_b, payload=pay_b).boot()
    rec_b = env_b.record()
    env_b.activate_stmt(env_b.statement(rec_b), rec_b)
    p2, r2, f2, d2, cfg2 = v02.tenant_flow(b / "cp", None, profile_binding=None)
    w.cp_effect.provision_local_execution_claim(f2, p2, d2, provision=env_b.dest.provision_claim, now=w.CP_NOW, claim_id="legacy-b", budget_id="budget-legacy-b")
    res_b = w.executor(env_b.dest, w.policy_from(w.needed_payload())).execute(envelope=w.envelope_for(p2, d2), claim_id="legacy-b")
    c_b, guard_b = w.counts(env_b.dest), w.receipt_guard(env_b.dest)
    ok_b = (res_b.status == "executed" and (c_b["effects"], c_b["attempts"], c_b["authority_effect_receipts_v1"]) == (1, 1, 1) and guard_b
            and guard_b[0].get("result") == "fallback_caller_policy" and guard_b[0].get("applied") is False and guard_b[0].get("fallback_reason") == "never_activated")
    subs["ungoverned_legacy_claim"] = dict(status=res_b.status, counts=c_b, selection_guard=guard_b, verdict="HELD" if ok_b else "INCONCLUSIVE")
    verdicts.append("HELD" if ok_b else "INCONCLUSIVE")
    ev["observed"].update(workflow_issued=True, subprobes=subs)
    ev["verdict"] = aggregate(verdicts)
    assert ev["verdict"] == "HELD", subs


# ====================================================================================================================== AU-7 issuance and scope-member substitution
def test_au7_scope_member_substitution_and_issuance_expectations(tmp_path, ev):
    ev["scenario"] = "AU-7"
    ev["expected"] = ("(a) issuance with a host-expected consumer or operation different from the binding's: PermissionError, no claim; (b) tenant / institution / "
                      "authority_domain substituted in the binding ALONE (commitment recomputed): claim model refuses at provisioning, 0 claims; (c) institution substituted "
                      "CONSISTENTLY in claim and binding (recomputed): not executed, 0 effects, denied by an operation/scope mismatch")
    env, rec, stmt, state, sets, binding, iss = governed(tmp_path)
    subs, verdicts = {}, []
    # (a) CP issuance
    for name, kw in (("expected_operation_differs", dict(expected_operation="op-other")), ("expected_consumer_differs", dict(expected_consumer_id="consumer-other"))):
        args = dict(expected_consumer_id=w.CONSUMER, expected_operation=w.OPERATION)
        args.update(kw)
        try:
            w.cp_effect.provision_local_execution_claim(iss.workflow, iss.p, iss.decision, provision=env.dest.provision_claim, now=w.CP_NOW,
                                                         claim_id="x-" + name, policy_binding=binding, **args)
            subs[name] = {"issued": True}
            verdicts.append("BREACH")
        except PermissionError as exc:
            ok = "consumer or operation does not match" in str(exc) and w.counts(env.dest)["execution_claims_v1"] == 0
            subs[name] = {"raised": "PermissionError", "message": str(exc), "verdict": "HELD" if ok else "INCONCLUSIVE"}
            verdicts.append("HELD" if ok else "INCONCLUSIVE")
    honest = iss.materialize(claim_id="honest-au7")
    # (b) binding-only substitutions
    for dim, other in (("tenant", "tenant-beta"), ("institution", "urn:cognous:institution:other-unit"), ("authority_domain", "other-domain")):
        forged = w.forged_from(honest, claim_id=f"forged-{dim}", scope_changes={dim: other})
        try:
            env.dest.provision_claim(forged)
            subs[f"binding_only_{dim}"] = {"provisioned": True}
            verdicts.append("INCONCLUSIVE")  # reached the destination: judged by execution below
            res = w.executor(env.dest, w.policy_from(sets)).execute(envelope=iss.envelope, claim_id=f"forged-{dim}")
            c = w.counts(env.dest)
            subs[f"binding_only_{dim}"].update(status=res.status, counts=c)
            if c["effects"]:
                verdicts[-1] = "BREACH"
        except Exception as exc:
            msg = f"{type(exc).__name__}: {str(exc)[:200]}"
            ok = "inconsistent with the claim profile or the claim scope" in str(exc) and w.counts(env.dest)["execution_claims_v1"] == 0
            subs[f"binding_only_{dim}"] = {"refused_at": "provision_claim (claim model)", "error": msg, "verdict": "HELD" if ok else "INCONCLUSIVE"}
            verdicts.append("HELD" if ok else "INCONCLUSIVE")
    # (c) consistent institution substitution in claim and binding
    other = "urn:cognous:institution:other-unit"
    forged = w.forged_from(honest, claim_id="forged-consistent", scope_changes={"institution": other}, top_changes={"institution_id": other})
    entry = {"forged_verifies": w.cp_effect.verify_local_execution_claim(forged)}
    try:
        env.dest.provision_claim(forged)
        entry["provisioned"] = True
        res = w.executor(env.dest, w.policy_from(sets)).execute(envelope=iss.envelope, claim_id="forged-consistent")
        c = w.counts(env.dest)
        entry.update(status=res.status, error=res.error, typed=w.refusal_of(res), counts=c)
        if c["effects"] or res.status == "executed":
            entry["verdict"] = "BREACH"
        elif res.status == "denied" and "operation mismatch" in (res.error or ""):
            entry["verdict"] = "HELD"
        else:
            entry["verdict"] = "INCONCLUSIVE"
    except Exception as exc:
        entry.update(provisioned=False, error=f"{type(exc).__name__}: {str(exc)[:200]}", verdict="INCONCLUSIVE")
    subs["consistent_institution_substitution"] = entry
    verdicts.append(entry["verdict"])
    ev["observed"].update(workflow_issued=True, subprobes=subs, final_counts=w.counts(env.dest))
    ev["verdict"] = aggregate(verdicts)
    assert ev["verdict"] == "HELD", subs


def test_au7_operation_member_substitution_to_another_activated_operation(tmp_path, ev):
    """The Runtime guard builds the governed scope from the binding alone; the envelope carries no operation member. Observed, not presumed."""
    ev["scenario"] = "AU-7"
    ev["expected"] = ("colluding supplier rewrites binding.operation (and the matching selection/record/activation members) to ANOTHER validly activated operation of the same "
                      "tenant/institution/domain/consumer. Contract 7.4 does not require an effect-time comparison with the envelope action: if it executes this is CHARACTERIZED "
                      "(issuance-time expected_operation is the only check); if refused, HELD with the typed reason")
    op2 = "op-other"
    scope2 = w.aligned_scope(operation=op2)
    wide2 = {k: sorted(v + [f"urn:cognous:op2:{k}"]) for k, v in w.needed_payload().items()}
    env = w.AEnv(tmp_path / "rt")
    env.add_scope(scope2)
    env.boot()
    rec1 = env.record()
    st1 = env.statement(rec1)
    env.activate_stmt(st1, rec1)
    rec2 = w.v4.reg_record(payload=copy.deepcopy(wide2), record_id="f1ab-v08-record-op2")
    st2 = env.statement(rec2, scope=scope2, sid="sel-test-op2")
    env.activate_stmt(st2, rec2, scope=scope2)
    state1, state2 = env.state(), env.state(scope2)
    sets = w.needed_payload()
    binding = w.binding_for(env, state1, sets)
    iss = w.Issued(tmp_path / "cp", binding, generation=state1.policy_generation)
    honest = iss.materialize(claim_id="honest-op")
    b2 = w.binding_for(env, state2, sets, scope=scope2)
    forged = w.forged_from(honest, claim_id="forged-op", binding_changes={k: b2[k] for k in b2 if k not in ("scope",)})
    entry = {"binding_operation_before": binding["operation"], "binding_operation_forged": forged["policy_binding"]["operation"],
             "forged_verifies": w.cp_effect.verify_local_execution_claim(forged),
             "activations": {"op_transfer": state1.activation_ref, "op_other": state2.activation_ref}}
    env.dest.provision_claim(forged)
    res = w.executor(env.dest, w.policy_from(sets)).execute(envelope=iss.envelope, claim_id="forged-op")
    c, guard = w.counts(env.dest), w.receipt_guard(env.dest)
    entry.update(status=res.status, typed=w.refusal_of(res), counts=c, selection_guard=guard)
    ev["observed"].update(workflow_issued=True, probe=entry)
    if res.status == "executed" and c["effects"] == 1 and guard and guard[0].get("activation_ref") == state2.activation_ref:
        ev["verdict"] = "CHARACTERIZED"
        ev["note"] = ("A supplier-forged claim naming a different, validly activated operation executed against THAT operation's activation; the envelope has no operation member "
                      "so the Runtime cannot compare it. Operation binding rests on the issuance-time expected_operation check (case AU-7 test 1(a)) and the approval-side binding.")
    elif res.status == "denied" and w.refusal_of(res) and not c["effects"]:
        ev["verdict"] = "HELD"
    else:
        ev["verdict"] = "INCONCLUSIVE"
    assert ev["verdict"] in ("HELD", "CHARACTERIZED")


# ====================================================================================================================== AU-8 record / selection identity
def test_au8_record_and_selection_identity_substitution(tmp_path, ev):
    ev["scenario"] = "AU-8"
    ev["expected"] = ("each alteration of the binding by a colluding supplier (commitment recomputed) is denied with the typed code of check_effect order, 0 effects: record_id / "
                      "record_version / record_digest -> record_identity_mismatch; selection_digest -> policy_identity_mismatch[selection_digest]; selection_epoch -> "
                      "policy_identity_mismatch[selection_epoch]; selection_id -> selection_conflict[lineage_binding]; then the unaltered workflow claim executes 1/1/1")
    env, rec, stmt, state, sets, binding, iss = governed(tmp_path)
    honest = iss.materialize(claim_id="honest-au8")
    alterations = [
        ("record_id", {"record_id": "f1ab-other-record"}, "record_identity_mismatch", None),
        ("record_version", {"record_version": state.record_version + 1}, "record_identity_mismatch", None),
        ("record_digest", {"record_digest": "sha256:" + "a" * 64}, "record_identity_mismatch", None),
        ("selection_digest", {"selection_digest": "sha256:" + "b" * 64}, "policy_identity_mismatch", "selection_digest"),
        ("selection_epoch", {"selection_epoch": state.selection_epoch + 1}, "policy_identity_mismatch", "selection_epoch"),
        ("selection_id", {"selection_id": "sel-substituted"}, "selection_conflict", "lineage_binding"),
    ]
    subs, verdicts = {}, []
    for name, change, code, cause in alterations:
        cid = f"forged-{name}"
        forged = w.forged_from(honest, claim_id=cid, binding_changes=change)
        try:
            env.dest.provision_claim(forged)
        except Exception as exc:
            subs[name] = {"provisioned": False, "error": f"{type(exc).__name__}: {str(exc)[:160]}", "verdict": "INCONCLUSIVE"}
            verdicts.append("INCONCLUSIVE")
            continue
        res = w.executor(env.dest, w.policy_from(sets)).execute(envelope=iss.envelope, claim_id=cid)
        c = w.counts(env.dest)
        v, typed = judge_refusal(res, c, code, "REFUSE", cause)
        subs[name] = {"status": res.status, "typed": typed, "counts_effects_attempts_receipts_budget": (c["effects"], c["attempts"], c["authority_effect_receipts_v1"], c["budget_used"]), "verdict": v}
        verdicts.append(v)
    env.dest.provision_claim(honest)
    res = w.executor(env.dest, w.policy_from(sets)).execute(envelope=iss.envelope, claim_id="honest-au8")
    c = w.counts(env.dest)
    ctrl = res.status == "executed" and (c["effects"], c["attempts"], c["authority_effect_receipts_v1"], c["budget_used"]) == (1, 1, 1, 1)
    subs["unaltered_control"] = {"status": res.status, "counts": c, "verdict": "HELD" if ctrl else "INCONCLUSIVE"}
    verdicts.append("HELD" if ctrl else "INCONCLUSIVE")
    ev["observed"].update(workflow_issued=True, subprobes=subs)
    ev["verdict"] = aggregate(verdicts)
    assert ev["verdict"] == "HELD", subs


def test_au7_operation_substitution_bypasses_policy_containment_posthoc(tmp_path, ev):
    """POST-HOC probe (added after the CHARACTERIZED result of the previous test; not in the committed inventory, disclosed in FINDINGS).

    Same store with two validly activated operations: op-transfer (narrow record) and op-other (wide record). The executor policy is the WIDE sets.
    Control: an honest binding naming op-transfer with the wide digest must be refused policy_not_subset (F-01 containment works for the true operation).
    Probe: the same wide policy with the binding rewritten to op-other (colluding supplier, commitment recomputed) -> secure oracle: refused."""
    ev["scenario"] = "AU-7"
    ev["expected"] = ("control (binding names op-transfer, executor policy wider than op-transfer's record): denied policy_identity_mismatch[policy_not_subset:<set>], 0 effects. "
                      "probe (binding rewritten to the other activated operation whose record contains the wide policy): secure oracle is a refusal; executing it means a "
                      "colluding supplier selected which activated record bounds the policy")
    op2 = "op-other"
    scope2 = w.aligned_scope(operation=op2)
    wide2 = {k: sorted(v + [f"urn:cognous:op2:{k}"]) for k, v in w.needed_payload().items()}
    env = w.AEnv(tmp_path / "rt")
    env.add_scope(scope2)
    env.boot()
    rec1 = env.record()
    env.activate_stmt(env.statement(rec1), rec1)
    rec2 = w.v4.reg_record(payload=copy.deepcopy(wide2), record_id="f1ab-v08-record-op2")
    env.activate_stmt(env.statement(rec2, scope=scope2, sid="sel-test-op2"), rec2, scope=scope2)
    state1, state2 = env.state(), env.state(scope2)
    needed = w.needed_payload()
    iss = w.Issued(tmp_path / "cp", w.binding_for(env, state1, needed), generation=state1.policy_generation)
    honest = iss.materialize(claim_id="honest-w")
    wdig = w.v4.ident.effective_policy_digest(f1ab.FAMILY_F1AB, {k: sorted(wide2[k]) for k in w.FIELDS})
    control = w.forged_from(honest, claim_id="control-wide-op-transfer", binding_changes={"effective_policy_digest": wdig})
    env.dest.provision_claim(control)
    res_c = w.executor(env.dest, w.policy_from(wide2)).execute(envelope=iss.envelope, claim_id="control-wide-op-transfer")
    c_c = w.counts(env.dest)
    v_c, typed_c = judge_refusal(res_c, c_c, "policy_identity_mismatch", "REFUSE")
    control_ok = v_c == "HELD" and typed_c["cause"].startswith("policy_not_subset:")
    b2 = w.binding_for(env, state2, needed, scope=scope2)
    changes = {k: b2[k] for k in b2 if k != "scope"}
    changes["effective_policy_digest"] = wdig
    probe = w.forged_from(honest, claim_id="probe-wide-op-other", binding_changes=changes)
    env.dest.provision_claim(probe)
    res_p = w.executor(env.dest, w.policy_from(wide2)).execute(envelope=iss.envelope, claim_id="probe-wide-op-other")
    c_p, guard = w.counts(env.dest), w.receipt_guard(env.dest)
    ev["observed"].update(workflow_issued=True, control=dict(status=res_c.status, typed=typed_c, counts=c_c, verdict=v_c),
                          probe=dict(status=res_p.status, typed=w.refusal_of(res_p), counts=c_p, selection_guard=guard,
                                     executor_policy_wider_than_op_transfer_record=any(set(wide2[k]) > set(needed[k]) for k in w.FIELDS),
                                     reproduction="forge from workflow claim: binding.operation/selection/record/activation members of op-other + effective_policy_digest of wide sets; recompute claim_commitment"))
    if not control_ok:
        ev["verdict"] = "INCONCLUSIVE"
    elif res_p.status == "executed" and c_p["effects"] == 1:
        ev["verdict"] = "BREACH"
        ev["note"] = ("Policy containment (F-01) is bypassed by operation substitution: with the control refused for op-transfer, the same wide executor policy committed an effect once the "
                      "binding named another activated operation (op-other) of the same tenant/institution/domain/consumer. Owner: Runtime registry_selection_authority.check_effect "
                      "(no operation comparison; the envelope has no operation member) / r08-v2 contract. The committed effect is the workflow-authorized operation itself.")
    elif res_p.status == "denied" and not c_p["effects"]:
        ev["verdict"] = "HELD"
    else:
        ev["verdict"] = "INCONCLUSIVE"
    assert ev["verdict"] == "HELD", ev["observed"]
