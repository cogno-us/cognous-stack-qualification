"""Catalog scenario D02 - Binding substitution (executed against the frozen F5b bounded reference).

SPDX-License-Identifier: Apache-2.0

Stimulus (catalog): alter tenant, actor, adapter, target, payload or action version, each separately.
Required observation: each altered request is refused; no prohibited destination mutation; the refusal path
is observable. Forbidden: any effect outside current scoped authority.

Three supported routes are exercised (see test_scn_d09 for the route inventory):
  A  Control Plane revalidation + runtime PinnedControlPlaneExecutor + effective-grant destination
  B  atomic-claim profile (AtomicLocalControlPlaneExecutor), the route driven by tools/run_matched_refund.py
  C  governed-exchange ``run_exchange`` ingress (drives route A internally)
Every case runs twice from fresh stores and the two normalised observations are compared (owner decision D3).
A genuine violation FAILS; nothing here is xfail.
"""
from __future__ import annotations

import copy
from datetime import timedelta

import pytest

import _d02_d05_d09_helpers as H
from _reason_norm import exc_summary  # noqa: E402
from _d02_d05_d09_helpers import no_network, pinned_reference  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures('pinned_reference')

ACTOR2 = 'urn:cognous:identity:other'
ADAPTER2 = 'urn:cognous:adapter:other'
TARGET2 = 'urn:cognous:synthetic-account:customer-999'
PRINCIPAL2 = 'urn:cognous:principal:other'


def _reasons_text(summary):
    return ';'.join(f'{c}/{r}/{s}: {detail}' for c, r, s, detail in summary['failures'])


# ------------------------------------------------------------------------------------------------
# identity, containment, initial state (execution contract step 1)
# ------------------------------------------------------------------------------------------------

def test_scn_d02_source_identity_containment_and_initial_state(request, record_property, tmp_path):
    ref = H.reference()
    H.assert_pins_still_pristine()
    import engine, agent_control_plane
    from pathlib import Path
    assert Path(engine.__file__).resolve().is_relative_to(ref.paths['runtime'])
    assert Path(agent_control_plane.__file__).resolve().is_relative_to(ref.paths['control_plane'])

    def trial(work, mp, checks):
        flow = H.flow_a(work, mp, tenant='tenant-alpha')
        s = H.db_summary(flow.dest.path)
        checks.equal(s['effects'], [], 'initial destination holds no effect')
        checks.equal(s['attempts'], [], 'initial destination holds no attempt')
        return {'initial_state_digest': H.digest({k: v for k, v in s.items()}), 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'D02', trial)


# ------------------------------------------------------------------------------------------------
# positive controls: the harness really observes an authorized effect (so absence elsewhere is meaningful)
# ------------------------------------------------------------------------------------------------

def test_scn_d02_positive_control_route_a_exact_request_executes_once(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp, tenant='tenant-alpha')
        res, exc = H.execute_a(flow)
        view = H.result_view(res, exc)
        checks.equal(view.get('status'), 'executed', 'exact authorized request executes')
        s = H.db_summary(flow.dest.path)
        digest = H.snapshot_digest(flow.env)
        gate = H.effect_gate(s, authorized_effect_ids={flow.env.effect_id}, authorized_digests={digest})
        checks.equal(len(s['effects']), 1, 'exactly one durable effect')
        return {'result': view, 'effects': s['effects'], **gate}
    H.run_case(request, record_property, tmp_path, 'D02', trial)


def test_scn_d02_positive_control_route_b_exact_claim_executes_once(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        res, exc = H.execute_b(flow, part)
        view = H.atomic_view(res, exc)
        checks.equal(view.get('status'), 'executed', 'exact claimed request executes')
        s = H.db_summary(flow.dest.path)
        gate = H.effect_gate(s, authorized_effect_ids={part.env.effect_id})
        checks.equal(s['claims'], [('claim-1', 'consumed')], 'claim consumed exactly once')
        return {'result': view, 'effects': s['effects'], 'claims': s['claims'], **gate}
    H.run_case(request, record_property, tmp_path, 'D02', trial)


# ------------------------------------------------------------------------------------------------
# route A: envelope altered after authorization (decision/proposal unchanged)
# ------------------------------------------------------------------------------------------------

def _env_alterations(flow):
    ch = H.reference().chain
    p = flow.p
    return {
        'tenant_substituted': H.alter_envelope(flow.env, tenant_id='tenant-beta'),
        'tenant_removed': H.alter_envelope(flow.env, tenant_id=None),
        'tenant_added': H.alter_envelope(flow.env, tenant_id='tenant-beta'),
        'actor': H.alter_envelope(flow.env, actor=ACTOR2),
        'principal': H.alter_envelope(flow.env, principal=PRINCIPAL2),
        'adapter': H.alter_envelope(flow.env, adapter_id=ADAPTER2),
        'target': H.alter_envelope(flow.env, target=TARGET2),
        'payload': H.alter_payload(flow.env, {**p.payload, 'refund_reason': 'substituted'}),
        'payload_commitment_stale': H.alter_envelope(flow.env, payload_commitment=ch.commitment({'stale': True})),
        'action_version': H.alter_envelope(flow.env, action_id=p.action_id.replace('-v1', '-v2')),
        'manifest_version': H.alter_envelope(flow.env, manifest_version='9.9'),
        'manifest_digest': H.alter_envelope(flow.env, manifest_digest='sha256:' + '0' * 64),
    }


@pytest.mark.parametrize('dimension', ['tenant_substituted', 'tenant_removed', 'tenant_added', 'actor', 'principal', 'adapter', 'target', 'payload',
                                       'payload_commitment_stale', 'action_version', 'manifest_version', 'manifest_digest'])
def test_scn_d02_route_a_envelope_substitution_is_refused(request, record_property, tmp_path, dimension):
    def trial(work, mp, checks):
        # tenant_added: a tenant claim is attached to a request whose authority is NOT tenant-scoped
        flow = H.flow_a(work, mp, tenant=None if dimension == 'tenant_added' else 'tenant-alpha')
        before = H.db_summary(flow.dest.path)
        altered = _env_alterations(flow)[dimension]
        res, exc = H.execute_a(flow, envelope=altered)
        view = H.result_view(res, exc)
        after = H.db_summary(flow.dest.path)
        refused = (res is not None and res.status == 'denied' and not res.attempted) or (res is None and after['admission_rejections'] > before['admission_rejections'])
        checks.expect(refused, f'altered {dimension} request must be refused; observed {view}')
        checks.equal(after['effects'], [], f'no destination mutation after altered {dimension}')
        checks.equal(after['attempts'], [], 'no dispatch attempt recorded for a refused request')
        observable = bool(after['failures']) or after['admission_rejections'] > 0
        checks.expect(observable, 'refusal path must be observable in the destination failure/rejection records')
        gate = H.effect_gate(after)
        trajectory = H.trajectory_a(flow, altered, res) if res is not None else {'export': 'n/a: request rejected before an execution result existed'}
        return {'dimension': dimension, 'layer': 'envelope-only', 'result': view, 'refusal_records': _reasons_text(after),
                'admission_rejections': after['admission_rejections'], 'effects': after['effects'], 'journal': H.journal_view(flow),
                'trajectory': trajectory, **gate}
    H.run_case(request, record_property, tmp_path, 'D02', trial)


# ------------------------------------------------------------------------------------------------
# route A: proposal altered (only the proposal, or proposal and envelope consistently) against the original decision
# ------------------------------------------------------------------------------------------------

def _proposal_updates(flow):
    ch = H.reference().chain
    p = flow.p
    payload = {**p.payload, 'refund_reason': 'substituted'}
    return {
        'tenant': {'tenant_id': 'tenant-beta'},
        'actor': {'actor': ACTOR2},
        'adapter': {'adapter_id': ADAPTER2},
        'target': {'target': TARGET2},
        'payload': {'payload': payload, 'payload_commitment': ch.commitment(payload)},
        'action_version': {'action_id': p.action_id.replace('-v1', '-v2')},
        'manifest_version': {'manifest_version': '9.9'},
    }


def _consistent_envelope(flow, p2):
    ch = H.reference().chain
    fields = {k: getattr(p2, k) for k in ('actor', 'principal', 'manifest_version', 'manifest_digest', 'action_id', 'adapter_id', 'target',
                                           'payload', 'payload_commitment')}
    return H.alter_envelope(flow.env, **fields, tenant_id=getattr(p2, 'tenant_id', None),
                            proposal_commitment=ch.commitment(p2.model_dump(mode='json')))


@pytest.mark.parametrize('layer', ['proposal-only', 'proposal-and-envelope'])
@pytest.mark.parametrize('dimension', ['tenant', 'actor', 'adapter', 'target', 'payload', 'action_version', 'manifest_version'])
def test_scn_d02_route_a_proposal_substitution_cannot_reuse_authorization(request, record_property, tmp_path, dimension, layer):
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp, tenant='tenant-alpha')
        p2 = flow.p.model_copy(update=_proposal_updates(flow)[dimension])
        env2 = flow.env if layer == 'proposal-only' else _consistent_envelope(flow, p2)
        if layer == 'proposal-and-envelope':  # let the local policy admit the altered values so the Control Plane binding is the refusing control
            flow.executor.policy = H.widened_policy(flow.executor.policy, env2.operation)
        before = H.db_summary(flow.dest.path)
        res, exc = H.execute_a(flow, envelope=env2, proposal=p2)
        view = H.result_view(res, exc)
        after = H.db_summary(flow.dest.path)
        refused = (res is not None and res.status == 'denied' and not res.attempted)
        checks.expect(refused, f'altered {dimension} ({layer}) must be refused; observed {view}')
        checks.equal(after['effects'], [], f'no destination mutation after altered {dimension} ({layer})')
        checks.equal(after['attempts'], [], 'no dispatch attempt recorded for a refused request')
        journal = H.journal_view(flow)
        observable = bool(after['failures']) or bool(journal['refusals'])
        checks.expect(observable, 'refusal path must be observable (destination failure record or Control Plane refusal)')
        gate = H.effect_gate(after)
        return {'dimension': dimension, 'layer': layer, 'result': view, 'refusal_records': _reasons_text(after), 'journal': journal,
                'effects': after['effects'], 'trajectory': H.trajectory_a(flow, env2, res) if res is not None else {}, **gate}
    H.run_case(request, record_property, tmp_path, 'D02', trial)


# ------------------------------------------------------------------------------------------------
# route B: atomic claim profile
# ------------------------------------------------------------------------------------------------

B_DIMENSIONS = ['tenant_substituted', 'tenant_removed', 'tenant_added', 'actor', 'principal', 'adapter', 'target', 'payload',
                'action_version', 'manifest_version', 'manifest_digest']


def _b_alteration(dimension, env):
    ch = H.reference().chain
    payload = {**env.operation.payload, 'reason': 'substituted'}
    return {
        'tenant_substituted': lambda: H.alter_envelope(env, tenant_id='tenant-beta'),
        'tenant_removed': lambda: H.alter_envelope(env, tenant_id=None),
        'tenant_added': lambda: H.alter_envelope(env, tenant_id='tenant-beta'),
        'actor': lambda: H.alter_envelope(env, actor=ACTOR2),
        'principal': lambda: H.alter_envelope(env, principal=PRINCIPAL2),
        'adapter': lambda: H.alter_envelope(env, adapter_id=ADAPTER2),
        'target': lambda: H.alter_envelope(env, target=TARGET2),
        'payload': lambda: H.alter_payload(env, payload),
        'action_version': lambda: H.alter_envelope(env, action_id=env.operation.action_id + ':v2'),
        'manifest_version': lambda: H.alter_envelope(env, manifest_version='9.9'),
        'manifest_digest': lambda: H.alter_envelope(env, manifest_digest='sha256:' + '0' * 64),
    }[dimension]()


@pytest.mark.parametrize('policy_mode', ['narrow-policy', 'widened-policy'])
@pytest.mark.parametrize('dimension', B_DIMENSIONS)
def test_scn_d02_route_b_claim_binding_substitution_is_refused_without_consuming_authority(request, record_property, tmp_path, dimension, policy_mode):
    def trial(work, mp, checks):
        tenant = 'tenant-alpha' if dimension in ('tenant_substituted', 'tenant_removed') else None
        flow = H.flow_b(work, tenant=tenant)
        part = flow.parts[0]
        altered = _b_alteration(dimension, part.env)
        executor = flow.executor
        if policy_mode == 'widened-policy':  # the claim binding must refuse even when local policy would admit the altered value
            import dataclasses
            policy = H.widened_policy(flow.policy, altered.operation)
            executor = type(flow.executor)(workflow=object(), destination=flow.dest, policy=policy)
        res, exc = H.execute_b(flow, part, envelope=altered, executor=executor)
        view = H.atomic_view(res, exc)
        after = H.db_summary(flow.dest.path)
        checks.expect(res is not None and res.status == 'denied' and not res.attempted, f'altered {dimension} must be refused; observed {view}')
        checks.equal(after['effects'], [], f'no destination mutation after altered {dimension}')
        checks.equal(after['attempts'], [], 'no attempt recorded for a refused request')
        claim_id = part.claim.claim_id
        checks.equal([c for c in after['claims'] if c[0] == claim_id], [(claim_id, 'issued')], 'refusal must not consume the claim')
        checks.expect(bool(after['failures']), 'refusal path must be observable in destination failure records')
        gate = H.effect_gate(after)
        return {'dimension': dimension, 'policy_mode': policy_mode, 'result': view, 'refusal_records': _reasons_text(after), 'claims': after['claims'],
                'budgets': after['budgets'], 'effects': after['effects'], **gate}
    H.run_case(request, record_property, tmp_path, 'D02', trial)


# ------------------------------------------------------------------------------------------------
# route C: governed-exchange ingress. The exchange reference has no tenant concept (tenant cases: see report).
# ------------------------------------------------------------------------------------------------

C_DIMENSIONS = ['actor', 'principal', 'target', 'adapter_id', 'payload', 'action_id', 'manifest_version']


def _alter_bundle(bundle, dimension):
    b = copy.deepcopy(bundle)
    proposal = next(x for x in b['records'] if x['record_type'] == 'runtime_proposal')['data']
    if dimension == 'payload':
        proposal['payload'] = {**proposal['payload'], 'refund_reason': 'substituted'}
    elif dimension == 'action_id':
        proposal['action_id'] = proposal['action_id'].replace('-v1', '-v2')
    elif dimension == 'manifest_version':
        proposal['manifest_version'] = '9.9'
    else:
        proposal[dimension] = {'actor': ACTOR2, 'principal': PRINCIPAL2, 'target': TARGET2, 'adapter_id': ADAPTER2}[dimension]
    return b


@pytest.mark.parametrize('dimension', C_DIMENSIONS)
def test_scn_d02_route_c_exchange_substitution_is_refused(request, record_property, tmp_path, dimension):
    def trial(work, mp, checks):
        ref = H.reference()
        gax, p, r, f, d, dest, bundle, message, registry, kwargs = ref.chain.exchange_setup(work, mp)
        altered = _alter_bundle(bundle, dimension)
        refusal = None
        result = None
        try:
            msg = gax.make_message(altered, created_at=ref.chain.NOW.isoformat(), expires_at=(ref.chain.NOW + timedelta(hours=1)).isoformat())
            result = gax.run_exchange(msg, altered, registry, dest, **kwargs)
        except Exception as exc:
            refusal = exc_summary(exc)
        after = H.db_summary(dest.path)
        if result is not None:
            ex = result['execution']
            checks.expect(ex.get('attempted') is False and ex.get('attempt_status') in ('hold', 'denied', None),
                          f'altered {dimension} must be refused or held by the exchange route; observed {ex.get("attempt_status")}')
            checks.expect(result['assessment']['stages'].get('authority') in ('hold', 'denied') or ex.get('reason'), 'refusal stage must be observable in the assessment')
            checks.expect(result.get('successor_packet') is not None, 'successor packet must retain the refusal')
            refusal = f'authority={result["assessment"]["stages"].get("authority")} attempt_status={ex.get("attempt_status")} reason={ex.get("reason")}'
        else:
            checks.expect(bool(refusal), 'refusal must be a typed, observable error')
        checks.equal(after['effects'], [], f'no destination mutation after altered {dimension} through the exchange')
        return {'dimension': dimension, 'refusal_path': refusal, 'effects': after['effects'], **H.effect_gate(after)}
    H.run_case(request, record_property, tmp_path, 'D02', trial)
