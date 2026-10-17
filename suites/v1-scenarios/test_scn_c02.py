"""Catalog scenario C02 - Unknown action and manifest mismatch (executed against the frozen F5b bounded reference).

SPDX-License-Identifier: Apache-2.0

Stimulus (catalog): submit an unknown action, then a mismatched manifest version or digest. Required observation:
neither request defaults to permission; the destination remains unchanged.

Sub-cases, each executed independently AND once as the ordered sequence the catalog states:
  * unknown action (an action id the Manifest does not declare);
  * manifest version mismatch; manifest digest mismatch; (additionally) manifest id mismatch.
Layers exercised:
  A  decision-level  : the altered proposal is submitted to the Control Plane for a decision (then the caller tries to
                       execute with the best envelope it can assemble);
  A  execution-level : the altered proposal AND a consistent altered envelope are presented against the ORIGINAL
                       authorized decision, with the local policy widened so that the Control Plane binding is the
                       refusing control;
  B  atomic claim    : the altered envelope is presented with the issued claim (narrow and widened local policy);
  C  governed exchange: the altered proposal is carried in an exchange bundle.
Every case runs twice from fresh stores and the normalised observations are compared (owner decision D3).
Hard gates (D5): zero unauthorized effects and zero excess duplicate effects. Nothing here is xfail.
"""
from __future__ import annotations

import copy
from datetime import timedelta

import pytest

import _c_2a_helpers as C
import _d02_d05_d09_helpers as H
from _c_2a_helpers import no_network, pinned_reference  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures('pinned_reference')

UNKNOWN_ACTION = 'urn:cognous:action:unknown-v1'
DIGEST_ZERO = 'sha256:' + '0' * 64
VARIANTS = ['unknown-action', 'manifest-version-mismatch', 'manifest-digest-mismatch', 'manifest-id-mismatch']


def _updates(variant):
    return {'unknown-action': {'action_id': UNKNOWN_ACTION}, 'manifest-version-mismatch': {'manifest_version': '9.9'},
            'manifest-digest-mismatch': {'manifest_digest': DIGEST_ZERO}, 'manifest-id-mismatch': {'manifest_id': 'urn:cognous:manifest:other'}}[variant]


def _failures(summary):
    return ';'.join(f'{c}/{r}/{s}: {d}' for c, r, s, d in summary['failures'])


def test_scn_c02_source_identity_containment_and_initial_state(request, record_property, tmp_path):
    ref = H.reference()
    H.assert_pins_still_pristine()
    import engine, agent_control_plane
    from pathlib import Path
    assert Path(engine.__file__).resolve().is_relative_to(ref.paths['runtime'])
    assert Path(agent_control_plane.__file__).resolve().is_relative_to(ref.paths['control_plane'])

    def trial(work, mp, checks):
        a = H.db_summary(C.flow_a_pre(work, mp).dest.path)
        checks.equal((a['effects'], a['attempts']), ([], []), 'initial destination holds no effect or attempt')
        return {'initial_state_digest': H.digest(a), 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'C02', trial)


def test_scn_c02_positive_control_exact_manifest_executes_once(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        res, exc = H.execute_a(flow)
        view = H.result_view(res, exc)
        checks.equal(view.get('status'), 'executed', 'the declared action under the exact manifest executes')
        s = H.db_summary(flow.dest.path)
        checks.equal(len(s['effects']), 1, 'exactly one durable effect')
        return {'result': view, 'effects': s['effects'],
                **H.effect_gate(s, authorized_effect_ids={flow.env.effect_id}, authorized_digests={H.snapshot_digest(flow.env)})}
    H.run_case(request, record_property, tmp_path, 'C02', trial)


# ------------------------------------------------------------------------------------------------
# route A, decision-level, each variant independently
# ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize('variant', VARIANTS)
def test_scn_c02_route_a_decision_does_not_default_to_permission(request, record_property, tmp_path, variant):
    def trial(work, mp, checks):
        flow = C.flow_a_pre(work, mp, lambda p, r, f, dest: p.model_copy(update=_updates(variant)))
        decision = C.decision_view(flow)
        checks.equal(decision['result'], 'hold', f'{variant} is not authorized')
        checks.equal(decision['has_binding'], False, 'no authorization binding is minted')
        checks.expect(bool(decision['reasons']), 'the hold carries explicit reasons')
        flow.executor, flow.env = C.best_effort_executor(flow)
        res, exc = H.execute_a(flow)
        view = H.result_view(res, exc)
        after = H.db_summary(flow.dest.path)
        checks.expect(res is not None and res.status == 'denied' and not res.attempted, f'execution is refused; observed {view}')
        checks.equal(after['effects'], [], 'destination unchanged')
        checks.equal(after['attempts'], [], 'no dispatch attempt recorded')
        journal = C.journal_decisions(flow)
        checks.expect(any(d['result'] == 'hold' for d in journal), f'the hold is retained in the Control Plane journal: {journal}')
        return {'variant': variant, 'decision': decision, 'result': view, 'journal_decisions': journal, 'destination_failures': _failures(after),
                'effects': after['effects'], **H.effect_gate(after)}
    H.run_case(request, record_property, tmp_path, 'C02', trial)


def test_scn_c02_route_a_ordered_sequence_unknown_action_then_manifest_version_then_digest(request, record_property, tmp_path):
    """The catalog stimulus as one ordered sequence on a single destination; the destination never changes between steps."""
    def trial(work, mp, checks):
        flow = C.flow_a_pre(work, mp)
        original_p = flow.p
        original_ex, original_env = C.best_effort_executor(flow)
        checks.equal(flow.d.result, 'authorized', 'the genuine request is authorized')
        flow.executor, flow.env = original_ex, original_env
        steps = []
        for variant in ('unknown-action', 'manifest-version-mismatch', 'manifest-digest-mismatch'):
            ch = H.reference().chain
            p2 = original_p.model_copy(update=_updates(variant))
            d2 = flow.f.decide(p2, now=ch.NOW)
            sub = C.SimpleNamespace(**{**flow.__dict__, 'p': p2, 'd': d2})
            executor, env = C.best_effort_executor(sub)
            sub.executor, sub.env = executor, env
            res, exc = H.execute_a(sub)
            after = H.db_summary(flow.dest.path)
            checks.equal(d2.result, 'hold', f'{variant}: not authorized')
            checks.expect(res is not None and res.status == 'denied' and not res.attempted, f'{variant}: execution refused; observed {H.result_view(res, exc)}')
            checks.equal((after['effects'], after['attempts']), ([], []), f'{variant}: destination unchanged after this step')
            steps.append({'variant': variant, 'decision': {'result': d2.result, 'reasons': sorted(d2.reasons or [])}, 'result': H.result_view(res, exc),
                          'effects_after': after['effects']})
        # the genuine request is still authorized exactly once afterwards: refusals left no residue that blocks or permits anything
        res, exc = H.execute_a(flow)  # original authorized decision and envelope, untouched by the refused steps
        final = H.db_summary(flow.dest.path)
        checks.equal(H.result_view(res, exc).get('status'), 'executed', 'the genuine request still executes afterwards')
        checks.equal(len(final['effects']), 1, 'exactly one effect, only for the genuine request')
        return {'steps': steps, 'genuine_after': H.result_view(res, exc), 'effects': final['effects'],
                **H.effect_gate(final, authorized_effect_ids={flow.env.effect_id}, authorized_digests={H.snapshot_digest(flow.env)})}
    H.run_case(request, record_property, tmp_path, 'C02', trial)


# ------------------------------------------------------------------------------------------------
# route A, execution-level: altered proposal + consistent altered envelope against the ORIGINAL decision
# ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize('variant', VARIANTS)
def test_scn_c02_route_a_execution_with_altered_manifest_binding_cannot_reuse_authorization(request, record_property, tmp_path, variant):
    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = H.flow_a(work, mp)
        p2 = flow.p.model_copy(update=_updates(variant))
        fields = {k: getattr(p2, k) for k in ('actor', 'principal', 'manifest_id', 'manifest_version', 'manifest_digest', 'action_id', 'adapter_id', 'target',
                                               'payload', 'payload_commitment')}
        env2 = H.alter_envelope(flow.env, **fields, proposal_commitment=ch.commitment(p2.model_dump(mode='json')))
        flow.executor.policy = H.widened_policy(flow.executor.policy, env2.operation)
        res, exc = H.execute_a(flow, envelope=env2, proposal=p2)
        view = H.result_view(res, exc)
        after = H.db_summary(flow.dest.path)
        checks.expect(res is not None and res.status == 'denied' and not res.attempted, f'altered {variant} must be refused; observed {view}')
        checks.equal(after['effects'], [], 'destination unchanged')
        checks.equal(after['attempts'], [], 'no dispatch attempt recorded')
        journal = H.journal_view(flow)
        checks.expect(bool(after['failures']) or bool(journal['refusals']), 'refusal observable (destination failure record or Control Plane refusal)')
        return {'variant': variant, 'result': view, 'journal': journal, 'destination_failures': _failures(after), 'effects': after['effects'], **H.effect_gate(after)}
    H.run_case(request, record_property, tmp_path, 'C02', trial)


# ------------------------------------------------------------------------------------------------
# route B: atomic claim profile
# ------------------------------------------------------------------------------------------------

def _b_env(variant, env):
    upd = _updates(variant)
    return H.alter_envelope(env, **upd)


@pytest.mark.parametrize('policy_mode', ['narrow-policy', 'widened-policy'])
@pytest.mark.parametrize('variant', VARIANTS)
def test_scn_c02_route_b_claim_refuses_unknown_action_and_manifest_mismatch(request, record_property, tmp_path, variant, policy_mode):
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        altered = _b_env(variant, part.env)
        executor = flow.executor
        if policy_mode == 'widened-policy':
            executor = type(flow.executor)(workflow=object(), destination=flow.dest, policy=H.widened_policy(flow.policy, altered.operation))
        res, exc = H.execute_b(flow, part, envelope=altered, executor=executor)
        view = H.atomic_view(res, exc)
        after = H.db_summary(flow.dest.path)
        checks.expect(res is not None and res.status == 'denied' and not res.attempted, f'altered {variant} must be refused; observed {view}')
        checks.equal(after['effects'], [], 'destination unchanged')
        checks.equal(after['attempts'], [], 'no attempt recorded')
        checks.equal(after['claims'], [('claim-1', 'issued')], 'the refusal does not consume the claim')
        checks.expect(bool(after['failures']), 'refusal observable in destination failure records')
        return {'variant': variant, 'policy_mode': policy_mode, 'result': view, 'destination_failures': _failures(after), 'claims': after['claims'],
                'effects': after['effects'], **H.effect_gate(after)}
    H.run_case(request, record_property, tmp_path, 'C02', trial)


# ------------------------------------------------------------------------------------------------
# route C: governed-exchange ingress
# ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize('variant', ['unknown-action', 'manifest-version-mismatch', 'manifest-digest-mismatch'])
def test_scn_c02_route_c_exchange_does_not_default_to_permission(request, record_property, tmp_path, variant):
    def trial(work, mp, checks):
        ref = H.reference()
        flow = H.flow_c(work, mp)
        bundle = copy.deepcopy(flow.bundle)
        next(x for x in bundle['records'] if x['record_type'] == 'runtime_proposal')['data'].update(_updates(variant))
        refusal = result = None
        try:
            msg = flow.gax.make_message(bundle, created_at=ref.chain.NOW.isoformat(), expires_at=(ref.chain.NOW + timedelta(hours=1)).isoformat())
            result = flow.gax.run_exchange(msg, bundle, flow.registry, flow.dest, **flow.kwargs)
        except Exception as exc:
            refusal = f'{type(exc).__name__}: {str(exc)[:200]}'
        after = H.db_summary(flow.dest.path)
        if result is not None:
            view = H.exchange_view(result)
            checks.expect(view['attempted'] is False and view['attempt_status'] in ('hold', 'denied', None), f'exchange refuses or holds; observed {view}')
        else:
            view = None
            checks.expect(bool(refusal), 'a refusal must be a typed, observable error')
        checks.equal(after['effects'], [], 'destination unchanged')
        return {'variant': variant, 'refusal': refusal, 'view': view, 'retained_control_plane_journal': C.exchange_journal(flow), 'effects': after['effects'],
                **H.effect_gate(after)}
    H.run_case(request, record_property, tmp_path, 'C02', trial)
