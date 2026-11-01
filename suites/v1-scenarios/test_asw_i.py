"""ASW core-12, family I (identity, wiki layer L09): I01 cross-tenant substitution, I02 expired grant at use time,
I03 revocation between plan and execution.

SPDX-License-Identifier: Apache-2.0

Executed against the frozen F5b-repaired seven-component bounded synthetic reference (see ``_asw_helpers``). No LLM, no
network, no payment. Each test runs twice from fresh stores; the hard gate (zero unauthorized / excess duplicate effects,
independent read-only SQLite observation) applies to every run. A genuine violation FAILS; nothing is loosened.

I01 route A, envelope-level tenant substitution: the reference runtime executor does not compare the envelope tenant_id
(registered defect F-04, cogno-us/cognous-execution-runtime#95); those variants are expected to FAIL here and are NOT
skipped or xfailed.
"""
from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta

import pytest

import _asw_helpers as A
import _d02_d05_d09_helpers as H
from _asw_helpers import C, no_network, pinned_reference  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures('pinned_reference')

TENANT = 'tenant-alpha'
OTHER = 'tenant-beta'
OTHER_ACCOUNT = 'urn:cognous:synthetic-account:customer-002'


# =====================================================================================================
# I01  Cross-tenant subject or target substitution: reject tenant mismatch
# =====================================================================================================

def test_asw_i01_positive_control_route_a_tenant_request_executes_once(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp, tenant=TENANT)
        checks.equal(type(flow.d.binding).__name__, 'TenantAuthorizationBinding', 'the decision carries a tenant binding')
        res, exc = H.execute_a(flow)
        checks.equal(A.view_a(res, exc).get('status'), 'executed', 'the matching tenant executes')
        s = H.db_summary(flow.dest.path)
        A.one_effect_expected(checks, s, 'tenant alpha')
        return {'result': A.view_a(res, exc), 'effects': s['effects'], **A.gate_for(s, {flow.env.effect_id})}
    A.run(request, record_property, tmp_path, 'I01', trial)


def test_asw_i01_positive_control_route_b_tenant_claim_executes_once(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_b(work, tenant=TENANT)
        part = flow.parts[0]
        res, exc = H.execute_b(flow, part)
        checks.equal(A.view_b(res, exc).get('status'), 'executed', 'the matching tenant claim executes')
        s = H.db_summary(flow.dest.path)
        checks.equal(len(s['effects']), 1, 'one effect')
        return {'result': A.view_b(res, exc), 'effects': s['effects'], 'claims': s['claims'], **A.gate_for(s, {part.env.effect_id})}
    A.run(request, record_property, tmp_path, 'I01', trial)


PROPOSAL_SUBSTITUTIONS = {
    'subject_tenant_other': lambda p: {'tenant_id': OTHER},
    'target_other_tenant_account': lambda p: {'target': OTHER_ACCOUNT},
}


@pytest.mark.parametrize('substitution', sorted(PROPOSAL_SUBSTITUTIONS))
def test_asw_i01_route_a_proposal_substitution_is_not_authorized(request, record_property, tmp_path, substitution):
    """Decision level: tenant-alpha authority cannot authorize a proposal for another tenant or another tenant's account."""
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp, tenant=TENANT)
        p2 = flow.p.model_copy(update=PROPOSAL_SUBSTITUTIONS[substitution](flow.p))
        d2 = flow.f.decide(p2, now=H.reference().chain.NOW)
        decision = A.expect_not_authorized(checks, d2, substitution)
        env = flow.env
        if substitution == 'target_other_tenant_account':
            env = H.alter_envelope(env, target=OTHER_ACCOUNT)
        res, exc = H.execute_a(flow, envelope=env, proposal=p2)
        checks.expect(A.refused_before_dispatch(res, exc), f'the original decision cannot carry the substituted proposal; observed {A.view_a(res, exc)}')
        s = A.no_effect(checks, flow, substitution)
        return {'substitution': substitution, 'decision': decision, 'result': A.view_a(res, exc), **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'I01', trial)


def test_asw_i01_route_a_tenant_less_proposal_cannot_use_tenant_authority(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp, tenant=TENANT)
        raw = flow.p.model_dump(mode='json')
        raw.pop('tenant_id')
        p2 = type(flow.p).__mro__[1](**raw)  # the tenant-less RuntimeProposal base class
        d2 = flow.f.decide(p2, now=H.reference().chain.NOW)
        decision = A.expect_not_authorized(checks, d2, 'tenant-less proposal')
        checks.expect('tenant_proposal_required' in decision['reasons'], f'decision names tenant_proposal_required; observed {decision["reasons"]}')
        res, exc = H.execute_a(flow, proposal=p2)
        checks.expect(A.refused_before_dispatch(res, exc), f'refused; observed {A.view_a(res, exc)}')
        s = A.no_effect(checks, flow, 'tenant-less proposal')
        return {'decision': decision, 'result': A.view_a(res, exc), **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'I01', trial)


@pytest.mark.parametrize('variant', ['tenant_substituted', 'tenant_removed', 'tenant_added'])
def test_asw_i01_route_a_envelope_tenant_substitution_is_refused(request, record_property, tmp_path, variant):
    """Execution-envelope level (decision and proposal untouched). Registered defect F-04 makes these FAIL on the pinned runtime."""
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp, tenant=None if variant == 'tenant_added' else TENANT)
        env = H.alter_envelope(flow.env, tenant_id=None if variant == 'tenant_removed' else OTHER)
        res, exc = H.execute_a(flow, envelope=env)
        checks.expect(A.refused_before_dispatch(res, exc), f'{variant} envelope must be refused; observed {A.view_a(res, exc)}')
        s = A.no_effect(checks, flow, variant)
        return {'variant': variant, 'result': A.view_a(res, exc), 'effects': s['effects'], 'failure_records': A.reasons_text(s),
                'known_defect': 'F-04 cogno-us/cognous-execution-runtime#95', **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'I01', trial)


@pytest.mark.parametrize('variant', ['tenant_substituted', 'tenant_removed'])
def test_asw_i01_route_b_claim_rejects_tenant_mismatch(request, record_property, tmp_path, variant):
    def trial(work, mp, checks):
        flow = H.flow_b(work, tenant=TENANT)
        part = flow.parts[0]
        env = H.alter_envelope(part.env, tenant_id=None if variant == 'tenant_removed' else OTHER)
        res, exc = H.execute_b(flow, part, envelope=env)
        checks.expect(A.refused_before_dispatch(res, exc), f'{variant} must be refused; observed {A.view_b(res, exc)}')
        s = H.db_summary(flow.dest.path)
        checks.equal((s['effects'], s['claims']), ([], [('claim-tenant-1', 'issued')]), 'no effect; the claim is untouched')
        return {'variant': variant, 'result': A.view_b(res, exc), 'failures': A.reasons_text(s), **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'I01', trial)


def test_asw_i01_route_b_other_tenants_claim_cannot_carry_this_tenants_envelope(request, record_property, tmp_path):
    """A destination provisioned for tenant-beta only: tenant-alpha's envelope presented under beta's claim id is refused."""
    def trial(work, mp, checks):
        (work / 'alpha').mkdir()
        (work / 'beta').mkdir()
        alpha = H.flow_b(work / 'alpha', tenant=TENANT)
        beta = H.flow_b(work / 'beta', tenant=OTHER)
        a_env = alpha.parts[0].env
        b_part = beta.parts[0]
        res, exc = H.execute_b(beta, b_part, envelope=a_env)
        checks.expect(A.refused_before_dispatch(res, exc), f'alpha envelope under beta claim must be refused; observed {A.view_b(res, exc)}')
        s = H.db_summary(beta.dest.path)
        checks.equal((s['effects'], s['claims']), ([], [('claim-tenant-1', 'issued')]), 'beta destination untouched')
        return {'result': A.view_b(res, exc), 'failures': A.reasons_text(s), **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'I01', trial)


# =====================================================================================================
# I02  Expired grant at use time: deny later effect
# =====================================================================================================

def test_asw_i02_positive_control_unexpired_grant_executes_once_on_both_routes(request, record_property, tmp_path):
    def trial(work, mp, checks):
        (work / 'a').mkdir()
        (work / 'b').mkdir()
        fa = H.flow_a(work / 'a', mp)
        ra, ea = H.execute_a(fa)
        fb = H.flow_b(work / 'b')
        rb, eb = H.execute_b(fb, fb.parts[0])
        checks.equal((A.view_a(ra, ea).get('status'), A.view_b(rb, eb).get('status')), ('executed', 'executed'), 'both routes execute inside the validity window')
        sa, sb = H.db_summary(fa.dest.path), H.db_summary(fb.dest.path)
        checks.equal((len(sa['effects']), len(sb['effects'])), (1, 1), 'one effect each')
        return {'a': A.view_a(ra, ea), 'b': A.view_b(rb, eb), **A.gate_for({'effects': sa['effects'] + sb['effects'], 'attempts': []},
                                                                           {fa.env.effect_id, fb.parts[0].env.effect_id})}
    A.run(request, record_property, tmp_path, 'I02', trial)


@pytest.mark.parametrize('mode', ['use_time_after_expiry', 'resolver_expiry_before_use', 'resolver_expiry_equal_to_use_time'])
def test_asw_i02_route_a_expired_grant_at_use_time_is_denied(request, record_property, tmp_path, mode):
    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = H.flow_a(work, mp)
        if mode == 'use_time_after_expiry':
            res, exc = None, None
            try:
                res = flow.executor.execute(envelope=flow.env, proposal=flow.p, decision=flow.d, now=ch.NOW + timedelta(hours=2))
            except Exception as e:
                exc = f'{type(e).__name__}: {e}'
        else:
            grant = flow.r.contexts[ch.PROFILE]['grant']
            grant['expires_at'] = (ch.NOW - timedelta(seconds=1) if mode == 'resolver_expiry_before_use' else ch.NOW).isoformat()
            res, exc = H.execute_a(flow)
        checks.expect(A.refused_before_dispatch(res, exc), f'expired grant ({mode}) must be denied; observed {A.view_a(res, exc)}')
        s = A.no_effect(checks, flow, f'expired grant {mode}')
        refusals = H.journal_view(flow)['refusals']
        checks.expect(any(r for r in refusals), f'the denial is retained in the Control Plane journal; observed {refusals}')
        return {'mode': mode, 'result': A.view_a(res, exc), 'refusals': refusals, **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'I02', trial)


def test_asw_i02_route_a_fresh_decision_after_expiry_is_not_authorized(request, record_property, tmp_path):
    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = H.flow_a(work, mp)
        later = flow.f.decide(flow.p, now=ch.NOW + timedelta(hours=2))
        decision = A.expect_not_authorized(checks, later, 'decision after grant expiry')
        s = A.no_effect(checks, flow, 'decision after expiry')
        return {'decision': decision, **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'I02', trial)


@pytest.mark.parametrize('mode', ['after_expiry', 'at_expiry', 'before_not_before'])
def test_asw_i02_route_b_claim_outside_validity_interval_is_denied(request, record_property, tmp_path, mode):
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        expires, not_before = datetime.fromisoformat(part.claim.expires_at), datetime.fromisoformat(part.claim.not_before)
        flow.clock.value = {'after_expiry': expires + timedelta(microseconds=1), 'at_expiry': expires, 'before_not_before': not_before - timedelta(seconds=1)}[mode]
        res, exc = H.execute_b(flow, part)
        checks.expect(A.refused_before_dispatch(res, exc), f'claim outside validity ({mode}) must be denied; observed {A.view_b(res, exc)}')
        s = H.db_summary(flow.dest.path)
        checks.equal((s['effects'], s['claims']), ([], [('claim-1', 'issued')]), 'no effect; the claim is not consumed')
        return {'mode': mode, 'result': A.view_b(res, exc), 'failures': A.reasons_text(s), **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'I02', trial)


def test_asw_i02_route_c_exchange_evaluated_after_grant_expiry_does_not_execute(request, record_property, tmp_path):
    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = H.flow_c(work, mp)
        msg = flow.gax.make_message(flow.bundle, created_at=ch.NOW.isoformat(), expires_at=(ch.NOW + timedelta(hours=24)).isoformat())
        res = flow.gax.run_exchange(msg, flow.bundle, flow.registry, flow.dest, **{**flow.kwargs, 'evaluation_time': (ch.NOW + timedelta(hours=2)).isoformat()})
        ex = res.get('execution') or {}
        checks.equal((bool(ex.get('attempted')), ex.get('attempt_status')), (False, 'hold'), 'the exchange holds without dispatch after the grant expired')
        s = A.no_effect(checks, flow, 'exchange after expiry')
        return {'execution': {k: ex.get(k) for k in ('attempted', 'attempt_status', 'newly_executed')}, **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'I02', trial)


# =====================================================================================================
# I03  Revocation between plan and execution: revalidate before the protected boundary
# =====================================================================================================

@pytest.mark.parametrize('withdrawal', ['revoked', 'suspended'])
def test_asw_i03_route_a_resolver_withdrawal_after_decision_is_revalidated_before_effect(request, record_property, tmp_path, withdrawal):
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        checks.equal(flow.d.result, 'authorized', 'the plan (decision) was authorized')
        next(iter(flow.r.statuses.values())).status = withdrawal
        res, exc = H.execute_a(flow)
        checks.expect(A.refused_before_dispatch(res, exc), f'{withdrawal} between plan and execution must be refused; observed {A.view_a(res, exc)}')
        s = A.no_effect(checks, flow, withdrawal)
        journal = H.journal_view(flow)
        checks.expect(any(f'grant_{withdrawal}' in r for r in journal['refusals']), f'the effect-time revalidation names grant_{withdrawal}; observed {journal["refusals"]}')
        checks.expect(journal['check_phases'].count('opened') >= 2, 'a second authority check was opened at effect time (revalidation, not reuse of the plan-time answer)')
        return {'withdrawal': withdrawal, 'result': A.view_a(res, exc), 'refusals': journal['refusals'], 'checks_opened': journal['check_phases'].count('opened'), **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'I03', trial)


def test_asw_i03_route_a_destination_authority_revoked_after_revalidation_is_refused_at_commit(request, record_property, tmp_path):
    """Revocation lands AFTER the Control Plane revalidation and before the destination commit: the destination's own
    authority check inside the commit transaction refuses it (no effect row)."""
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        H.revoke_destination(flow)
        res, exc = H.execute_a(flow)
        checks.expect(res is not None and res.status in ('failed', 'denied') and not res.acknowledged,
                      f'destination-side revocation must refuse the commit; observed {A.view_a(res, exc)}')
        s = H.db_summary(flow.dest.path)
        checks.equal(s['effects'], [], 'no destination effect')
        return {'result': A.view_a(res, exc), 'attempts': [a['events'] for a in s['attempts']], **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'I03', trial)


@pytest.mark.parametrize('withdrawal', ['revoked', 'suspended'])
def test_asw_i03_route_b_authority_withdrawal_after_provisioning_is_revalidated(request, record_property, tmp_path, withdrawal):
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        flow.dest.set_grant_status(part.claim.grant_id, status=withdrawal)
        res, exc = H.execute_b(flow, part)
        checks.expect(A.refused_before_dispatch(res, exc), f'{withdrawal} after the claim was issued must be refused; observed {A.view_b(res, exc)}')
        s = H.db_summary(flow.dest.path)
        checks.equal((s['effects'], s['claims']), ([], [('claim-1', 'issued')]), 'no effect; the claim is not consumed')
        return {'withdrawal': withdrawal, 'result': A.view_b(res, exc), 'failures': A.reasons_text(s), **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'I03', trial)


def test_asw_i03_route_b_revocation_at_the_commit_boundary_is_seen_inside_the_transaction(request, record_property, tmp_path):
    """The reference's own deterministic stage hook: revoke at 'before_begin' (after the caller's checks, before the write
    transaction opens); authority is re-read inside BEGIN IMMEDIATE and the effect is refused."""
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]

        def hook(stage):
            if stage == 'before_begin':
                flow.dest.set_grant_status(part.claim.grant_id, status='revoked')
        flow.dest.stage_hook = hook
        res, exc = H.execute_b(flow, part)
        checks.expect(A.refused_before_dispatch(res, exc), f'revocation at the commit boundary must be refused; observed {A.view_b(res, exc)}')
        s = H.db_summary(flow.dest.path)
        checks.equal((s['effects'], s['claims']), ([], [('claim-1', 'issued')]), 'no effect; claim not consumed')
        checks.equal(flow.dest.trace, ['before_begin', 'after_begin'], 'authority was evaluated after the write transaction opened')
        return {'result': A.view_b(res, exc), 'trace': flow.dest.trace, **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'I03', trial)


def test_asw_i03_route_c_exchange_authority_revoked_after_decision_is_refused(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_c(work, mp)
        res = H.exchange_run(flow, mutate_resolver_after_decision=lambda r: setattr(next(iter(r.statuses.values())), 'status', 'revoked'))
        view = H.exchange_view(res)
        checks.equal((view['attempted'], view['attempt_status']), (False, 'denied'), 'the exchange re-validates and denies without dispatch')
        s = A.no_effect(checks, flow, 'exchange revoked')
        return {'view': view, **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'I03', trial)
