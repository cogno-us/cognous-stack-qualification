"""Catalog scenario C18 - Bounded delegation (executed against the frozen F5b bounded reference).

SPDX-License-Identifier: Apache-2.0

Stimulus (catalog): delegate within scope, then exceed action, tenant, time or resource limits separately.
Required observation: only supported bounded delegation can proceed; a handoff cannot create new authority.

DECLARED DELEGATION CONTRACT (derived from the reference, not invented):
  * The reference has NO sub-delegation primitive. Its supported bounded delegation is the handoff of a trusted-host-issued,
    operation-bound capability to another agent:
      - route B (atomic claim profile): a ``LocalExecutionClaim`` bound to actor, principal, institution/domain, action,
        adapter, target, payload commitment, amount, unit, effect count, tenant, validity interval and one budget; the
        delegate presents (claim_id, envelope) through its own executor/destination handle;
      - route A (Control Plane): a grant whose ``permissions`` bound action, targets, data scopes, max_amount, unit and
        max_effects, whose validity window bounds time, and whose tenant binds the tenant.
  * A grant that names a parent (``delegation.parent_grant_id``) is NOT a supported delegation: the Control Plane holds it
    with ``delegation_profile_unsupported`` (the reference states that no ancestor revocation walk or shared ancestor
    budget exists) and ``delegation_chain_missing``; an identity whose ``delegation_valid`` is false is held with
    ``identity_or_delegation_invalid``.
  * A handoff may carry the capability only unchanged; every exceeded limit is refused, and no refusal consumes the capability.
Each limit class (action, tenant, time, resource) and each handoff attack is exercised separately. Every case runs twice from
fresh stores and the two normalised observations are compared (owner decision D3). Hard gate (D5): zero unauthorized effects
and zero excess duplicate effects.
"""
from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta

import pytest

import _c_2c_helpers as C
import _d02_d05_d09_helpers as H
from _reason_norm import exc_summary  # noqa: E402
from _d02_d05_d09_helpers import no_network, pinned_reference  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures('pinned_reference')

OTHER_ACTOR = 'urn:cognous:identity:delegate-other'
OTHER_PRINCIPAL = 'urn:cognous:principal:delegate-other'
OTHER_ADAPTER = 'urn:cognous:adapter:other'
OTHER_TARGET = 'urn:cognous:synthetic-account:customer-999'
OUTSIDE_TARGET = 'urn:elsewhere:account:1'


def delegate_executor(flow, policy=None):
    """The delegate agent: its own destination handle (sharing the store and the trusted clock) and its own executor."""
    dest = type(flow.dest)(flow.work, clock=flow.clock)
    return type(flow.executor)(workflow=object(), destination=dest, policy=policy or flow.policy)


def fully_widened(policy, op):
    """A local policy that would admit the altered operation on every dimension, so the CLAIM is the only refusing control."""
    p = H.widened_policy(policy, op)
    return dataclasses.replace(p, allowed_units=p.allowed_units | {op.unit}, max_amount=max(p.max_amount, float(op.amount)) + 1,
                               allowed_target_prefixes=tuple(p.allowed_target_prefixes) + (op.target,), max_effects=max(p.max_effects, int(op.effects), int(op.effective_max_effects)))


def part_of(env, claim):
    return type('P', (), {'env': env, 'claim': claim})()


def test_scn_c18_source_identity_containment_and_initial_state(request, record_property, tmp_path):
    ref = H.reference()
    H.assert_pins_still_pristine()
    import agent_control_plane, engine
    from pathlib import Path
    assert Path(engine.__file__).resolve().is_relative_to(ref.paths['runtime'])
    assert Path(agent_control_plane.__file__).resolve().is_relative_to(ref.paths['control_plane'])

    def trial(work, mp, checks):
        (work / 'a').mkdir()
        (work / 'b').mkdir()
        b = H.flow_b(work / 'b', tenant='tenant-alpha')
        a = H.flow_a(work / 'a', mp, tenant='tenant-alpha')
        sb, sa = H.db_summary(b.dest.path), H.db_summary(a.dest.path)
        checks.equal(sb['effects'], [], 'route B initial destination holds no effect')
        checks.equal(sa['effects'], [], 'route A initial destination holds no effect')
        checks.equal(sb['claims'], [('claim-tenant-1', 'issued')], 'the delegated claim starts issued')
        return {'initial_state_digest': H.digest({'a': sa, 'b': sb}), 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'C18', trial)


# ------------------------------------------------------------------------------------------------
# within scope: the delegate proceeds (positive controls)
# ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize('tenant', [None, 'tenant-alpha'])
def test_scn_c18_positive_control_route_b_delegate_within_scope_executes_once(request, record_property, tmp_path, tenant):
    def trial(work, mp, checks):
        flow = H.flow_b(work, tenant=tenant)
        part = flow.parts[0]
        delegate = delegate_executor(flow)
        view = H.atomic_view(*H.execute_b(flow, part, executor=delegate))
        again = H.atomic_view(*H.execute_b(flow, part, executor=delegate))
        s = H.db_summary(flow.dest.path)
        checks.equal(view['status'], 'executed', 'the delegate executes the exact capability it was handed')
        checks.equal(again['status'], 'denied', 'the capability cannot be used twice')
        checks.equal(len(s['effects']), 1, 'exactly one effect')
        gate = H.effect_gate(s, authorized_effect_ids={part.env.effect_id})
        return {'tenant': tenant, 'delegate': view, 'second_use': again, 'effects': s['effects'], 'claims': s['claims'], **gate}
    H.run_case(request, record_property, tmp_path, 'C18', trial)


def test_scn_c18_positive_control_route_a_grant_within_scope_executes_once(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp, tenant='tenant-alpha')
        res, exc = H.execute_a(flow)
        view = H.result_view(res, exc)
        s = H.db_summary(flow.dest.path)
        checks.equal(view.get('status'), 'executed', 'a request inside the grant scope executes')
        checks.equal(len(s['effects']), 1, 'exactly one effect')
        gate = H.effect_gate(s, authorized_effect_ids={flow.env.effect_id}, authorized_digests={H.snapshot_digest(flow.env)})
        return {'result': view, 'effects': s['effects'], 'journal': H.journal_view(flow), **gate}
    H.run_case(request, record_property, tmp_path, 'C18', trial)


# ------------------------------------------------------------------------------------------------
# route B: exceed each limit separately (claim binding must refuse even when local policy would admit the value)
# ------------------------------------------------------------------------------------------------

def _alter(dim, env):
    ch = H.reference().chain
    op = env.operation
    payload = {**op.payload, 'reason': 'exceeded'}
    return {
        'action:action_id': lambda: H.alter_envelope(env, action_id=op.action_id + ':v2'),
        'action:adapter_id': lambda: H.alter_envelope(env, adapter_id=OTHER_ADAPTER),
        'tenant:substituted': lambda: H.alter_envelope(env, tenant_id='tenant-beta'),
        'tenant:removed': lambda: H.alter_envelope(env, tenant_id=None),
        'tenant:added': lambda: H.alter_envelope(env, tenant_id='tenant-beta'),
        'resource:amount_plus_one': lambda: H.alter_envelope(env, amount=op.amount + 1),
        'resource:amount_far_beyond': lambda: H.alter_envelope(env, amount=999.0),
        'resource:effects_two': lambda: H.alter_envelope(env, effects=2),
        'resource:unit': lambda: H.alter_envelope(env, unit='EUR'),
        'resource:target_other_account': lambda: H.alter_envelope(env, target=OTHER_TARGET),
        'resource:target_outside_prefix': lambda: H.alter_envelope(env, target=OUTSIDE_TARGET),
        'resource:payload': lambda: H.alter_payload(env, payload),
        'handoff:actor': lambda: H.alter_envelope(env, actor=OTHER_ACTOR),
        'handoff:principal': lambda: H.alter_envelope(env, principal=OTHER_PRINCIPAL),
    }[dim]()


B_DIMS = ['action:action_id', 'action:adapter_id', 'tenant:substituted', 'tenant:removed', 'tenant:added', 'resource:amount_plus_one', 'resource:amount_far_beyond',
          'resource:effects_two', 'resource:unit', 'resource:target_other_account', 'resource:target_outside_prefix', 'resource:payload', 'handoff:actor', 'handoff:principal']


@pytest.mark.parametrize('policy_mode', ['narrow-policy', 'fully-widened-policy'])
@pytest.mark.parametrize('dim', B_DIMS)
def test_scn_c18_route_b_delegate_exceeding_a_limit_is_refused_without_consuming_the_capability(request, record_property, tmp_path, dim, policy_mode):
    def trial(work, mp, checks):
        tenant = 'tenant-alpha' if dim in ('tenant:substituted', 'tenant:removed') else None
        flow = H.flow_b(work, tenant=tenant)
        part = flow.parts[0]
        altered = _alter(dim, part.env)
        policy = flow.policy if policy_mode == 'narrow-policy' else fully_widened(flow.policy, altered.operation)
        delegate = delegate_executor(flow, policy)
        view = H.atomic_view(*H.execute_b(flow, part, envelope=altered, executor=delegate))
        s = H.db_summary(flow.dest.path)
        refused = view.get('status') == 'denied' and not view.get('attempted') or 'raised' in view
        checks.expect(refused, f'{dim} ({policy_mode}): exceeding the delegated limit must be refused; observed {view}')
        checks.equal(s['effects'], [], f'{dim}: no destination mutation')
        checks.equal(s['attempts'], [], f'{dim}: no dispatch attempt')
        checks.equal(C.claim_state(s, part.claim.claim_id), 'issued', f'{dim}: the refusal must not consume the delegated capability')
        checks.equal(s['budgets'], [('budget-main', 1, 0)], f'{dim}: no budget consumed')
        # the capability is unharmed: the delegate can still use it within scope afterwards
        ok = H.atomic_view(*H.execute_b(flow, part, executor=delegate_executor(flow)))
        checks.equal(ok['status'], 'executed', f'{dim}: the unchanged capability still works within scope after the refusal')
        final = H.db_summary(flow.dest.path)
        gate = H.effect_gate(final, authorized_effect_ids={part.env.effect_id}, authorized_digests={H.snapshot_digest(part.env)})
        return {'dimension': dim, 'policy_mode': policy_mode, 'exceeded': view, 'then_within_scope': ok['status'], 'refusal': ';'.join(f'{c}/{r}/{st}' for c, r, st, _d in s['failures']),
                'effects_after': final['effects'], **gate}
    H.run_case(request, record_property, tmp_path, 'C18', trial)


@pytest.mark.parametrize('moment', ['before_not_before', 'at_not_before', 'one_microsecond_before_expiry', 'at_expiry', 'after_expiry'])
def test_scn_c18_route_b_time_limit_of_the_delegation(request, record_property, tmp_path, moment):
    """Time limit: the claim is valid on [not_before, expires_at). Inside the window the delegate proceeds; outside it is refused."""
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        nb = datetime.fromisoformat(part.claim.not_before)
        exp = datetime.fromisoformat(part.claim.expires_at)
        at = {'before_not_before': nb - timedelta(microseconds=1), 'at_not_before': nb, 'one_microsecond_before_expiry': exp - timedelta(microseconds=1),
              'at_expiry': exp, 'after_expiry': exp + timedelta(hours=1)}[moment]
        inside = moment in ('at_not_before', 'one_microsecond_before_expiry')
        flow.clock.value = at
        # keep the other time-dependent input (evidence freshness) current at ``at`` so only the delegation window can decide
        flow.dest.set_evidence_state(flow.helpers.EVIDENCE, state='current', observed_at=(at - timedelta(seconds=1)).isoformat())
        view = H.atomic_view(*H.execute_b(flow, part, executor=delegate_executor(flow)))
        s = H.db_summary(flow.dest.path)
        if inside:
            checks.equal(view['status'], 'executed', f'{moment}: inside the delegated window the delegate proceeds; observed {view}')
            checks.equal(len(s['effects']), 1, f'{moment}: exactly one effect')
        else:
            checks.equal(view['status'], 'denied', f'{moment}: outside the delegated window the delegate is refused')
            checks.expect('validity interval' in (view['error'] or ''), f'{moment}: refusal names the validity interval; observed {view["error"]}')
            checks.equal(s['effects'], [], f'{moment}: no effect outside the window')
            checks.equal(C.claim_state(s, part.claim.claim_id), 'issued', f'{moment}: refusal does not consume the capability')
        gate = H.effect_gate(s, authorized_effect_ids={part.env.effect_id})
        return {'moment': moment, 'inside_window': inside, 'view': view, 'effects': s['effects'], 'claims': s['claims'], **gate}
    H.run_case(request, record_property, tmp_path, 'C18', trial)


def test_scn_c18_route_b_resource_limit_second_effect_under_the_same_capability_is_refused(request, record_property, tmp_path):
    """Resource limit (effect count): one capability authorises one effect. A delegate who presents a SECOND effect under it
    (new effect id/decision and operation) is refused, and so is a replay of the first."""
    def trial(work, mp, checks):
        flow = H.flow_b(work, effect_nos=(1, 2), budget_max=2)
        p1, p2 = flow.parts
        delegate = delegate_executor(flow)
        first = H.atomic_view(*H.execute_b(flow, p1, executor=delegate))
        second = H.atomic_view(*H.execute_b(flow, p1, envelope=p2.env, executor=delegate))   # claim 1, effect 2's operation
        replay = H.atomic_view(*H.execute_b(flow, p1, executor=delegate))
        s = H.db_summary(flow.dest.path)
        checks.equal(first['status'], 'executed', 'the first effect executes')
        checks.equal(second['status'], 'denied', 'a second effect cannot ride on the first capability')
        checks.expect(any(k in (second['error'] or '') for k in ('operation mismatch', 'not usable')), f'refusal is a typed claim refusal: {second["error"]}')
        checks.equal(replay['status'], 'denied', 'the consumed capability is not replayable')
        checks.equal(len(s['effects']), 1, 'exactly one effect')
        gate = H.effect_gate(s, authorized_effect_ids={p1.env.effect_id}, authorized_digests={H.snapshot_digest(p1.env)})
        return {'first': first, 'second': second, 'replay': replay, 'effects': s['effects'], 'claims': s['claims'], **gate}
    H.run_case(request, record_property, tmp_path, 'C18', trial)


# ------------------------------------------------------------------------------------------------
# handoff cannot create new authority
# ------------------------------------------------------------------------------------------------

def test_scn_c18_route_b_handoff_chain_a_to_b_to_c_yields_one_effect(request, record_property, tmp_path):
    """The capability is handed A -> B -> C (each with its own executor/destination handle). Only the first use takes effect;
    handing it on never multiplies authority."""
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        views = [H.atomic_view(*H.execute_b(flow, part, executor=delegate_executor(flow))) for _ in range(3)]
        s = H.db_summary(flow.dest.path)
        checks.equal([v['status'] for v in views], ['executed', 'denied', 'denied'], 'only the first holder of the capability takes effect')
        checks.equal(len(s['effects']), 1, 'exactly one effect across the chain')
        checks.equal(s['budgets'], [('budget-main', 1, 1)], 'budget used once')
        return {'views': views, 'effects': s['effects'], 'claims': s['claims'], **H.effect_gate(s, authorized_effect_ids={part.env.effect_id})}
    H.run_case(request, record_property, tmp_path, 'C18', trial)


def test_scn_c18_route_b_handoff_with_another_agents_capability_or_operation_is_refused(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_b(work, effect_nos=(1, 2), budget_max=2)
        p1, p2 = flow.parts
        delegate = delegate_executor(flow)
        claim1_env2 = H.atomic_view(*H.execute_b(flow, p1, envelope=p2.env, executor=delegate))
        claim2_env1 = H.atomic_view(*H.execute_b(flow, p2, envelope=p1.env, executor=delegate))
        s = H.db_summary(flow.dest.path)
        checks.equal(claim1_env2['status'], 'denied', 'delegate A cannot use its capability for delegate B\'s operation')
        checks.equal(claim2_env1['status'], 'denied', 'delegate B cannot use its capability for delegate A\'s operation')
        checks.equal(s['effects'], [], 'no effect')
        checks.equal(s['claims'], [('claim-1', 'issued'), ('claim-2', 'issued')], 'neither capability consumed')
        return {'claim1_with_env2': claim1_env2, 'claim2_with_env1': claim2_env1, 'claims': s['claims'], **H.effect_gate(s, authorized_effect_ids=set())}
    H.run_case(request, record_property, tmp_path, 'C18', trial)


def test_scn_c18_route_b_reminted_copy_of_a_consumed_capability_cannot_add_an_effect(request, record_property, tmp_path):
    """A delegate with provisioning access mints a second claim (new claim id, same operation) after the first was consumed,
    on a budget that would otherwise allow a second effect. No second effect may result."""
    def trial(work, mp, checks):
        flow = H.flow_b(work, effect_nos=(1,), budget_max=2)
        part = flow.parts[0]
        first = H.atomic_view(*H.execute_b(flow, part))
        before = H.db_summary(flow.dest.path)
        copy = flow.helpers.make_claim(part.env, claim_id='claim-copy', budget_id='budget-main', max_effects=2)
        flow.dest.provision_claim(copy)
        second = H.atomic_view(*H.execute_b(flow, part_of(part.env, copy)))
        s = H.db_summary(flow.dest.path)
        checks.equal(first['status'], 'executed', 'the original capability executes')
        checks.equal(second['status'], 'denied', 'the re-minted copy does not execute')
        checks.equal(s['effects'], before['effects'], 'no effect is added by the copy')
        checks.equal(s['budgets'], before['budgets'], 'no budget is consumed by the copy')
        checks.equal(C.claim_state(s, 'claim-copy'), 'issued', 'the refused copy is not consumed')
        gate = H.effect_gate(s, authorized_effect_ids={part.env.effect_id})
        return {'first': first, 'copy_attempt': second, 'effects': s['effects'], 'claims': s['claims'], 'budgets': s['budgets'],
                'refusal_kind': 'untyped integrity error (UNIQUE constraint on effects.effect_id)' if 'UNIQUE' in (second['error'] or '') else 'typed refusal', **gate}
    H.run_case(request, record_property, tmp_path, 'C18', trial)


def test_scn_c18_route_b_handoff_cannot_extend_a_grant_by_provisioning_a_broader_claim(request, record_property, tmp_path):
    """A delegate with provisioning access tries to widen authority through a new claim on the existing grant: a different
    revision/institution/status than the authoritative grant row is refused, and the grant row is left unchanged."""
    def trial(work, mp, checks):
        flow = H.flow_b(work, effect_nos=(1,))
        part = flow.parts[0]
        h = flow.helpers
        rows = C.authority_rows(flow.dest.path)
        attempts = {}
        variants = {
            'other_revision': dataclasses.replace(h.envelope(effect_no=2), operation=dataclasses.replace(h.envelope(effect_no=2).operation, grant_revision='9')),
            'other_domain': dataclasses.replace(h.envelope(effect_no=3), operation=dataclasses.replace(h.envelope(effect_no=3).operation, authority_domain='other-domain')),
            'other_institution': dataclasses.replace(h.envelope(effect_no=4), operation=dataclasses.replace(h.envelope(effect_no=4).operation, institution_id='urn:cognous:institution:other')),
        }
        for label, env in variants.items():
            claim = h.make_claim(env, claim_id=f'claim-wide-{label}', budget_id='budget-main', max_effects=1)
            try:
                flow.dest.provision_claim(claim)
                attempts[label] = 'PROVISIONED'
            except Exception as exc:
                attempts[label] = f'{type(exc).__name__}: {exc}'
        s = H.db_summary(flow.dest.path)
        for label, outcome in attempts.items():
            checks.expect('rejects claim provisioning' in outcome, f'{label}: a claim disagreeing with the authoritative grant must be refused; observed {outcome}')
        checks.equal(C.authority_rows(flow.dest.path), rows, 'authority state is unchanged by the refused claims')
        checks.equal(s['effects'], [], 'no effect')
        return {'attempts': attempts, 'claims': s['claims'], **H.effect_gate(s, authorized_effect_ids=set())}
    H.run_case(request, record_property, tmp_path, 'C18', trial)


# ------------------------------------------------------------------------------------------------
# route A: the Control Plane's delegation / scope model
# ------------------------------------------------------------------------------------------------

def _rebind(flow, p2):
    ch = H.reference().chain
    for a in flow.r.approvals.values():
        a.proposal_commitment = ch.commitment(p2.model_dump(mode='json', exclude_none=False))
    ch.bind_approval(flow.r, flow.c)


def _consistent_env(flow, p2):
    ch = H.reference().chain
    fields = {k: getattr(p2, k) for k in ('actor', 'principal', 'manifest_version', 'manifest_digest', 'action_id', 'adapter_id', 'target', 'payload', 'payload_commitment', 'amount', 'unit', 'effects')}
    return H.alter_envelope(flow.env, **fields, tenant_id=getattr(p2, 'tenant_id', None), proposal_commitment=ch.commitment(p2.model_dump(mode='json')))


A_CASES = {
    # id: (proposal update, tenant flow, now shift, expected reason in the held decision)
    'action:permission_widened': ({'requested_permissions': ['refund.issue.routine', 'refund.issue.admin']}, None, None, 'grant_scope_mismatch'),
    'action:unknown_action': ({'action_id': 'urn:cognous:action:refund-issue-high-v1'}, None, None, 'action_class_unknown'),
    'tenant:substituted': ({'tenant_id': 'tenant-beta'}, 'tenant-alpha', None, 'grant_tenant_mismatch'),
    'time:before_window': ({}, None, timedelta(hours=-2), 'grant_outside_validity'),
    'time:at_expiry': ({}, None, timedelta(hours=1), 'grant_outside_validity'),
    'time:after_window': ({}, None, timedelta(hours=2), 'grant_outside_validity'),
    'resource:amount_just_above_max': ({'amount': 100.01}, None, None, 'amount_exceeded'),
    'resource:amount_far_beyond': ({'amount': 999.0}, None, None, 'amount_exceeded'),
    'resource:unit': ({'unit': 'EUR'}, None, None, 'amount_unit_mismatch'),
    'resource:effects_two': ({'effects': 2}, None, None, 'effect_count_exceeded'),
    'resource:target_other_account': ({'target': 'urn:cognous:synthetic-account:customer-002'}, None, None, 'target_out_of_scope'),
    'handoff:actor': ({'actor': OTHER_ACTOR}, None, None, 'proposal_identity_binding_mismatch'),
}


@pytest.mark.parametrize('case', sorted(A_CASES))
def test_scn_c18_route_a_exceeding_a_grant_limit_is_held_and_cannot_execute(request, record_property, tmp_path, case):
    """The approval is re-bound to the altered proposal so the grant scope, window and tenant are the only refusing controls."""
    update, tenant, shift, reason = A_CASES[case]

    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = H.flow_a(work, mp, tenant=tenant)
        p2 = flow.p.model_copy(update=update) if update else flow.p
        _rebind(flow, p2)
        now = ch.NOW + shift if shift is not None else ch.NOW
        try:
            d2 = flow.f.decide(p2, now=now)
            outcome = {'result': d2.result, 'reasons': sorted(d2.reasons)}
        except Exception as exc:
            d2, outcome = None, {'raised': exc_summary(exc)}
        checks.expect(d2 is not None and d2.result != 'authorized', f'{case}: the delegated limit exceeded must not be authorised; observed {outcome}')
        checks.expect(d2 is not None and reason in d2.reasons, f'{case}: the held decision names {reason}; observed {outcome}')
        # presenting the held decision with a consistent envelope (and a policy that admits the values) must still not execute
        res_view = None
        if d2 is not None:
            env2 = _consistent_env(flow, p2)
            flow.executor.policy = fully_widened(flow.executor.policy, env2.operation)
            res, exc = H.execute_a(flow, envelope=env2, proposal=p2, decision=d2)
            res_view = H.result_view(res, exc)
            checks.expect(res is None or (res.status in ('denied', 'failed') and not res.attempted), f'{case}: the held decision cannot be executed; observed {res_view}')
        s = H.db_summary(flow.dest.path)
        checks.equal(s['effects'], [], f'{case}: no effect')
        gate = H.effect_gate(s, authorized_effect_ids=set())
        return {'case': case, 'decision': outcome, 'execution_of_held_decision': res_view, 'journal': H.journal_view(flow), **gate}
    H.run_case(request, record_property, tmp_path, 'C18', trial)


@pytest.mark.parametrize('boundary', ['amount_exactly_at_max', 'one_second_before_expiry'])
def test_scn_c18_route_a_grant_boundaries_inside_the_limit_are_authorised(request, record_property, tmp_path, boundary):
    """The limits are limits, not walls: exactly AT the grant maximum amount is still within scope; and just before the window closes
    the grant-validity check does not fire (other freshness inputs are reported, not asserted)."""
    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = H.flow_a(work, mp)
        if boundary == 'amount_exactly_at_max':
            p2 = flow.p.model_copy(update={'amount': 100.0})
            _rebind(flow, p2)
            d2 = flow.f.decide(p2, now=ch.NOW)
            checks.equal(d2.result, 'authorized', f'amount exactly at max_amount is within scope; observed {d2.result} {d2.reasons}')
            return {'boundary': boundary, 'decision': {'result': d2.result, 'reasons': sorted(d2.reasons)}, 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
        d2 = flow.f.decide(flow.p, now=ch.NOW + timedelta(hours=1) - timedelta(seconds=1))
        checks.expect('grant_outside_validity' not in d2.reasons, f'one second before expiry the grant window must not refuse; observed {d2.reasons}')
        return {'boundary': boundary, 'decision': {'result': d2.result, 'reasons': sorted(d2.reasons)}, 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'C18', trial)


@pytest.mark.parametrize('variant', ['parent_grant_named', 'parent_grant_named_with_identity_chain', 'identity_delegation_invalid'])
def test_scn_c18_route_a_unsupported_or_invalid_delegation_is_held_and_cannot_execute(request, record_property, tmp_path, variant):
    """Only supported bounded delegation proceeds: a grant naming a parent is held as an unsupported profile, an invalid
    delegation is held, and neither can reach the destination even if its held decision is presented to the executor."""
    expected = {'parent_grant_named': {'delegation_profile_unsupported', 'delegation_chain_missing'},
                'parent_grant_named_with_identity_chain': {'delegation_profile_unsupported'},
                'identity_delegation_invalid': {'identity_or_delegation_invalid'}}[variant]

    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = H.flow_a(work, mp)
        if variant.startswith('parent_grant'):
            flow.r.contexts[ch.PROFILE]['grant']['delegation']['parent_grant_id'] = 'urn:cognous:grant:parent'
        if variant == 'parent_grant_named_with_identity_chain':
            flow.r.identities[flow.p.actor].chain = ['urn:cognous:grant:parent']
        if variant == 'identity_delegation_invalid':
            flow.r.identities[flow.p.actor].delegation_valid = False
        d2 = flow.f.decide(flow.p, now=ch.NOW)
        checks.expect(d2.result != 'authorized', f'{variant}: must not be authorised; observed {d2.result}')
        checks.expect(expected <= set(d2.reasons), f'{variant}: held for {sorted(expected)}; observed {sorted(d2.reasons)}')
        res, exc = H.execute_a(flow, decision=d2)
        view = H.result_view(res, exc)
        checks.expect(res is None or (res.status in ('denied', 'failed') and not res.attempted), f'{variant}: the held decision cannot be executed; observed {view}')
        s = H.db_summary(flow.dest.path)
        checks.equal(s['effects'], [], f'{variant}: no effect')
        return {'variant': variant, 'decision': {'result': d2.result, 'reasons': sorted(d2.reasons)}, 'execution_of_held_decision': view, **H.effect_gate(s, authorized_effect_ids=set())}
    H.run_case(request, record_property, tmp_path, 'C18', trial)


def test_scn_c18_unsupported_delegation_is_reported(request, record_property, tmp_path):
    """REPORT: which delegation capabilities the reference does not support (observed, not inferred)."""
    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = H.flow_a(work, mp)
        flow.r.contexts[ch.PROFILE]['grant']['delegation'].update(parent_grant_id='urn:cognous:grant:parent', may_delegate=True, remaining_depth=3)
        d2 = flow.f.decide(flow.p, now=ch.NOW)
        from engine import local_authority_effect as lae
        names = sorted(n for n in dir(lae.AtomicAuthorityEffectDestination) if not n.startswith('_'))
        sub_api = [n for n in names if 'delegat' in n.lower() or 'handoff' in n.lower() or 'subgrant' in n.lower()]
        probes = {
            'sub_delegation_chain_with_parent_grant': {'supported': d2.result == 'authorized', 'observed': f'decision {d2.result}: {sorted(d2.reasons)}'},
            'ancestor_revocation_walk': {'supported': False, 'observed': 'delegation_profile_unsupported is raised for any parent_grant_id; the reference states no ancestor revocation walk exists'},
            'shared_ancestor_budget': {'supported': False, 'observed': 'same reason; per-grant caps only (see C16)'},
            'executor_side_delegation_api': {'supported': bool(sub_api), 'public_methods_matching': sub_api},
            'delegation_depth_enforcement': {'supported': False, 'observed': 'may_delegate/remaining_depth are carried in the grant but no sub-grant is ever created or consumed'},
        }
        checks.expect(d2.result != 'authorized', 'a delegated grant must not be authorised')
        return {'probes': probes, 'unsupported': sorted(k for k, v in probes.items() if not v['supported'])}
    payload = H.run_case(request, record_property, tmp_path, 'C18', trial, expect_effects_gate=False)
    C.write_report(request, record_property, 'unsupported_delegation', {'scenario': 'C18', 'unsupported': payload['run1']['observed']['unsupported'], 'probes': payload['run1']['observed']['probes']})
