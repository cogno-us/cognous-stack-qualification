"""Addendum row ADD-C2C-BI - business-intent duplication negative control (different effect IDs, same refund intent).

SPDX-License-Identifier: Apache-2.0

Requirement (Stokes addendum 6 / 8 P0): the published claim is that effect-ID deduplication is NOT business-intent deduplication.
The matched-refund duplicate-redelivery case only covers the SAME effect ID. This module executes the missing control against the
frozen F5b reference: a second request with the SAME business content (same target, amount, unit, payload, reason) and a DIFFERENT
effect ID, independently approved, presented after the first has been applied.

Expected-by-publication outcomes asserted here (and what a deviation means):
  * default route A (C0) and optional atomic C1 route B: the second effect is NOT deduplicated by business intent. If the grant/budget
    admits it, it commits (a business-level duplicate). The control records ``business_intent_duplicates`` and
    ``residual_exposed = true``; it is never reported as prevention. Where the grant/budget admits only one effect, the second is
    refused by the BUDGET, which is recorded as a budget refusal, not intent protection.
  * a replay of the SAME effect ID adds nothing in every configuration (positive control that effect-ID dedup works).
  * opt-in refund-intent profile (synthetic-refund-intent/1) on the destination: the second effect with the same intent is held and
    never committed; a distinct intent is allowed. Positive control showing the negative control is not a harness artefact.
    This profile is exercised through the runtime's own legacy durable-destination fixtures (the same flow the runtime suite uses);
    it is NOT composable with the F5b effective-grant destination (route A), which fails closed - recorded as a separate test.

Hard gates: zero unauthorized effects (both effect IDs carry their own authorized decision) and zero excess duplicate effects per
effect ID. The business-level duplicate count is report-only. Every case runs twice and is compared (D3).
"""
from __future__ import annotations

import dataclasses
import os
import sqlite3
import sys
from pathlib import Path

import pytest

import _c_2a_helpers as C
import _d02_d05_d09_helpers as H
from _d02_d05_d09_helpers import no_network, pinned_reference  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures('pinned_reference')


def _business_rows(path):
    conn = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute('SELECT effect_id,target,amount,unit,payload_json,state FROM effects ORDER BY effect_id')]
    finally:
        conn.close()


def _attempt_errors(path):
    conn = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True, timeout=10)
    try:
        return [r[0] for r in conn.execute('SELECT error FROM attempt_events WHERE error IS NOT NULL ORDER BY event_id')]
    finally:
        conn.close()


def _business_duplicates(rows):
    groups = {}
    for r in rows:
        groups.setdefault((r['target'], r['amount'], r['unit'], r['payload_json']), set()).add(r['effect_id'])
    return sum(len(v) - 1 for v in groups.values())


def _raise_budget_and_rebind(ref, ch, max_effects):
    def mutate(p, r, f, dest):
        f.manifest['actions'][0]['effect_limits']['max_effects'] = max_effects
        p = p.model_copy(update={'manifest_digest': ch.commitment(f.manifest)})
        ctx = r.contexts[ch.PROFILE]
        ctx['requirement']['permissions'][0]['max_effects'] = max_effects
        ctx['grant']['permissions'][0]['max_effects'] = max_effects
        _rebind(r, ch, p)
        return p
    return mutate


def _rebind(r, ch, proposal):
    """Independent approval of ``proposal`` (the approval is bound to the proposal commitment)."""
    ctx = r.contexts[ch.PROFILE]
    approval_ref = ctx['grant']['approval_refs'][0]
    r.approvals[approval_ref] = r.approvals[approval_ref].model_copy(
        update={'proposal_commitment': ch.commitment(proposal.model_dump(mode='json', exclude_none=False))})


def _second_request(flow, ex, env, ch):
    """Same business content, different correlation -> a different, independently approved, effect ID."""
    p2 = flow.p.model_copy(update={'correlation_id': 'another-case-same-refund-intent'})
    _rebind(flow.r, ch, p2)
    d2 = flow.f.decide(p2, now=ch.NOW)
    op2 = dataclasses.replace(env.operation, proposal_commitment=ch.commitment(p2.model_dump(mode='json')))
    env2 = dataclasses.replace(env, decision_id=d2.decision_id, effect_id=d2.effect_id, operation=op2)
    return p2, d2, env2


# ------------------------------------------------------------------------------------------------
# default route A (C0)
# ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize('budget', [3, 1])
def test_add_c2c_bi_route_a_different_effect_id_same_business_request(request, record_property, tmp_path, budget):
    def trial(work, mp, checks):
        ref = H.reference()
        ch = ref.chain
        flow = C.flow_a_pre(work, mp, _raise_budget_and_rebind(ref, ch, budget))
        checks.equal(flow.d.result, 'authorized', 'E1 decision authorized')
        ex, env = C.best_effort_executor(flow)
        ex.policy = dataclasses.replace(ex.policy, max_effects=budget)
        r1 = ex.execute(envelope=env, proposal=flow.p, decision=flow.d, now=ch.NOW)
        checks.equal((r1.status, r1.newly_executed), ('executed', True), 'E1 executes')
        again = ex.execute(envelope=env, proposal=flow.p, decision=flow.d, now=ch.NOW)
        rows1 = _business_rows(flow.dest.path)
        checks.equal((again.newly_executed, len(rows1)), (False, 1), 'control: replay of the SAME effect id adds nothing (effect-id dedup works)')
        p2, d2, env2 = _second_request(flow, ex, env, ch)
        checks.equal(d2.result, 'authorized', 'E2 is independently authorized')
        checks.expect(d2.effect_id != flow.d.effect_id, 'E2 carries a DIFFERENT effect id')
        r2 = ex.execute(envelope=env2, proposal=p2, decision=d2, now=ch.NOW)
        rows = _business_rows(flow.dest.path)
        dup = _business_duplicates(rows)
        residual = dup > 0
        if budget >= 2:
            checks.equal((r2.status, r2.newly_executed, len(rows)), ('executed', True, 2),
                         'published behaviour: effect-ID dedup is not business-intent dedup, the second effect commits')
            checks.equal(dup, 1, 'both effects carry identical business content')
        else:
            checks.expect(not r2.newly_executed and len(rows) == 1, f'with a one-effect budget the second effect is refused; observed {H.result_view(r2)}')
            checks.equal(dup, 0, 'no business duplicate when the budget refuses the second effect')
            errors = _attempt_errors(flow.dest.path)
            checks.expect('local cumulative max_effects exhausted' in errors,
                          f'destination attempt_events persist the budget exhaustion as the refusal cause (not intent); observed {errors}')
        summary = H.db_summary(flow.dest.path)
        gate = H.effect_gate(summary, authorized_effect_ids={flow.d.effect_id, d2.effect_id})
        return {'route': 'A', 'budget': budget, 'first': H.result_view(r1), 'second': H.result_view(r2), 'second_refusal_class': None if r2.newly_executed else 'destination cumulative max_effects exhausted (not intent)',
                'distinct_effect_ids': d2.effect_id != flow.d.effect_id, 'effects': [{k: v for k, v in x.items() if k != 'effect_id'} for x in rows],
                'effect_count': len(rows), 'business_intent_duplicates': dup,
                'residual_exposed': residual, 'residual_description': 'effect-ID deduplication does not equal business-intent deduplication; the profile does not claim otherwise' if residual else None, **gate}
    H.run_case(request, record_property, tmp_path, 'ADD-C2C-BI', trial)


# ------------------------------------------------------------------------------------------------
# optional atomic C1 route B
# ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize('budget', [2, 1])
def test_add_c2c_bi_route_b_different_effect_id_same_business_request(request, record_property, tmp_path, budget):
    def trial(work, mp, checks):
        ref = H.reference()
        h = ref.atomic
        from engine.local_authority_effect import AtomicLocalControlPlaneExecutor
        clock = h.MutableClock(h.BASE)
        dest = H.hooked_atomic_class()(work, clock=clock)
        dest.trace = []
        env1 = h.envelope(effect_no=1)
        env2 = dataclasses.replace(h.envelope(effect_no=1, effect_id='effect-1-second-id'), decision_id='decision-1-second-id')
        checks.equal(env1.operation, env2.operation, 'both envelopes carry the identical business operation')
        checks.expect(env1.effect_id != env2.effect_id, 'effect ids differ')
        claims = [h.make_claim(env1, claim_id='claim-a', budget_id='budget-main', max_effects=budget),
                  h.make_claim(env2, claim_id='claim-b', budget_id='budget-main', max_effects=budget)]
        for c in claims:
            dest.provision_claim(c)
        policy = dataclasses.replace(h.policy(env1.operation), max_effects=budget)
        ex = AtomicLocalControlPlaneExecutor(workflow=object(), destination=dest, policy=policy)
        parts = [SimpleNamespace_(env=env1, claim=claims[0]), SimpleNamespace_(env=env2, claim=claims[1])]
        r1, e1 = H.execute_b(SimpleNamespace_(executor=ex), parts[0])
        checks.equal(H.atomic_view(r1, e1).get('status'), 'executed', 'E1 executes')
        rr, er = H.execute_b(SimpleNamespace_(executor=ex), parts[0])
        rows1 = _business_rows(dest.path)
        checks.equal(len(rows1), 1, 'control: replay of the SAME effect/claim adds nothing')
        r2, e2 = H.execute_b(SimpleNamespace_(executor=ex), parts[1])
        rows = _business_rows(dest.path)
        dup = _business_duplicates(rows)
        v2 = H.atomic_view(r2, e2)
        if budget >= 2:
            checks.equal((v2.get('status'), len(rows)), ('executed', 2), 'published behaviour: C1 orders authority/effect, it does not deduplicate by business intent')
            checks.equal(dup, 1, 'both effects carry identical business content')
        else:
            checks.expect(v2.get('status') != 'executed' and len(rows) == 1, f'budget 1 refuses the second effect; observed {v2}')
            checks.equal(dup, 0, 'no business duplicate when the shared budget refuses the second effect')
        final = H.db_summary(dest.path)
        gate = H.effect_gate(final, authorized_effect_ids={env1.effect_id, env2.effect_id})
        return {'route': 'B', 'budget': budget, 'second': v2, 'second_refusal_class': None if v2.get('status') == 'executed' else 'shared budget exhausted (not intent)',
                'effect_count': len(rows), 'business_intent_duplicates': dup, 'budgets': final.get('budgets'), 'destination_failures': final['failures'],
                'residual_exposed': dup > 0, 'residual_description': 'C1 does not deduplicate by business intent' if dup else None, **gate}
    H.run_case(request, record_property, tmp_path, 'ADD-C2C-BI', trial)


class SimpleNamespace_:
    def __init__(self, **kw):
        self.__dict__.update(kw)


# ------------------------------------------------------------------------------------------------
# opt-in refund-intent profile (positive control) and its non-composition with route A
# ------------------------------------------------------------------------------------------------

def _runtime_intent_fixtures(mp, ref):
    mp.setenv('MOLTBOT_SAFE_MANIFEST_FIXTURE', str(ref.paths['control_plane'] / 'tests/fixtures/refund_integration_v1_1.manifest.json'))
    tests_dir = str(H.ROOT / 'suites/cognous-execution-runtime/tests')
    if tests_dir not in sys.path:
        sys.path.append(tests_dir)
    import agent_control_plane.bounded as cp
    mp.setattr(cp, '_now', lambda: ref.chain.NOW)
    import test_refund_intent as T  # the runtime's own fixtures (module import; no test function re-collected)
    return T


@pytest.mark.parametrize('same_intent', [True, False])
def test_add_c2c_bi_opt_in_refund_intent_profile_positive_control(request, record_property, tmp_path, same_intent):
    def trial(work, mp, checks):
        ref = H.reference()
        T = _runtime_intent_fixtures(mp, ref)
        from engine.safe_executor import snapshot_envelope
        h, p, resolver, workflow, d, executor, intent, registry, authorize = T.integrated_profile(work)
        d1, first = authorize(p)
        registry.provision(intent, snapshot_envelope(first))
        r1 = executor.execute(envelope=first, proposal=p, decision=d1, now=h.NOW, refund_intent=intent)
        checks.expect(r1.newly_executed, 'E1 executes under the profile')
        p2 = p.model_copy(update={'correlation_id': 'another-case'})
        d2, second = authorize(p2)
        checks.expect(d2.effect_id != d1.effect_id, 'E2 carries a different effect id')
        chosen = intent if same_intent else dataclasses.replace(intent, request_id='distinct-domain-request')
        if not same_intent:
            registry.provision(chosen, snapshot_envelope(second))
        r2 = executor.execute(envelope=second, proposal=p2, decision=d2, now=h.NOW, refund_intent=chosen)
        count = d.effect_count(first.operation.grant_id)
        if same_intent:
            checks.expect(not r2.newly_executed, 'same refund intent with a different effect id is held, not executed')
            checks.equal(count, 1, 'exactly one durable effect for the one refund intent')
            checks.equal(d.observe(second.effect_id)['state'], 'absent', 'E2 is absent at the destination')
            checks.expect(r2.control_plane_evidence['reconciliation']['retry_eligible'] is False, 'absence does not make E2 retry-eligible')
        else:
            checks.expect(r2.newly_executed, 'a distinct intent is allowed')
            checks.equal(count, 2, 'two effects for two distinct intents')
        return {'same_intent': same_intent, 'second': {'status': r2.status, 'newly_executed': r2.newly_executed, 'error': (r2.error or '')[:80]},
                'effect_count': count, 'unauthorized_effects': 0, 'excess_duplicate_effects': 0 if count == (1 if same_intent else 2) else 1}
    H.run_case(request, record_property, tmp_path, 'ADD-C2C-BI', trial)


def test_add_c2c_bi_refund_intent_profile_is_not_composable_with_route_a_and_fails_closed(request, record_property, tmp_path):
    """Finding recorded as an assertion: the optional intent profile cannot be combined with the F5b effective-grant destination."""
    def trial(work, mp, checks):
        ref = H.reference()
        ch = ref.chain
        flow = C.flow_a_pre(work, mp, _raise_budget_and_rebind(ref, ch, 3))
        ex, env = C.best_effort_executor(flow)
        ex.policy = dataclasses.replace(ex.policy, max_effects=3)
        from engine.refund_intent import RefundIntent, RefundIntentRegistry
        from engine.safe_executor import snapshot_envelope
        registry = RefundIntentRegistry(flow.dest)
        op = env.operation
        intent = RefundIntent(op.institution_id, op.authority_domain, flow.p.payload['customer_id'], 'domain-request-1')
        registry.provision(intent, snapshot_envelope(env))
        res = ex.execute(envelope=env, proposal=flow.p, decision=flow.d, now=ch.NOW, refund_intent=intent)
        rows = _business_rows(flow.dest.path)
        checks.equal((res.status, res.newly_executed, len(rows)), ('denied', False, 0), 'combination fails closed with no effect')
        return {'result': H.result_view(res), 'effects': len(rows),
                'note': 'intent profile + effective-grant destination => denied; the opt-in intent control is unavailable on the F5b route A flow',
                'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'ADD-C2C-BI', trial)
