"""Catalog scenario C09 - Repeat delivery (executed against the frozen F5b bounded reference).

SPDX-License-Identifier: Apache-2.0

Stimulus (catalog): repeat an already delivered effect through the supported retry path. Required observation: no
excess committed effect; the attempt identity is distinct and linked to the original effect.

The supported retry path differs per route and each is exercised:
  A  re-present the same decision / a fresh decision for the same proposal / retry after a lost acknowledgement through
     ``PinnedControlPlaneExecutor.execute``; and, one layer lower, the runtime ``LocalDestinationExecutor`` retry with
     and without an explicit (re-used) attempt id.
  B  re-present the consumed claim (new attempt id each time) or a fresh claim for the same effect; and a retry after a
     lost acknowledgement.
  C  redeliver the same exchange message; deliver a NEW message carrying the same effect; ``resume_original_exchange``.
Identity evidence is read from the records the reference actually retains (destination attempts, Control Plane journal,
failure records). Where a refused repeat leaves a distinct, effect-linked record that carries no ``attempt_id`` (route B),
that is stated in the evidence (``attempt_identity_minted_for_repeat: false``) and not presented as an attempt identity.
Every case runs twice from fresh stores and the normalised observations are compared (owner decision D3). Hard gates
(D5): zero unauthorized effects and zero excess duplicate effects. A genuine violation FAILS.
"""
from __future__ import annotations

import dataclasses
from datetime import timedelta

import pytest

import _c_2a_helpers as C
import _d02_d05_d09_helpers as H
from _c_2a_helpers import no_network, pinned_reference  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures('pinned_reference')

REPEATS = 3


def test_scn_c09_source_identity_containment_and_initial_state(request, record_property, tmp_path):
    ref = H.reference()
    H.assert_pins_still_pristine()
    import engine, agent_control_plane
    from pathlib import Path
    assert Path(engine.__file__).resolve().is_relative_to(ref.paths['runtime'])
    assert Path(agent_control_plane.__file__).resolve().is_relative_to(ref.paths['control_plane'])

    def trial(work, mp, checks):
        (work / 'a').mkdir()
        (work / 'b').mkdir()
        a = H.db_summary(H.flow_a(work / 'a', mp).dest.path)
        b = H.db_summary(H.flow_b(work / 'b').dest.path)
        checks.equal((a['effects'], b['effects']), ([], []), 'initial destinations hold no effect')
        return {'initial_state_digest': H.digest({'a': a, 'b': b}), 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'C09', trial)


# ------------------------------------------------------------------------------------------------
# route A
# ------------------------------------------------------------------------------------------------

def _check_a_identity(checks, flow, original_attempt_id, repeat_ids, expected_repeats):
    cp = C.cp_attempt_summary(flow, with_ids=True)
    checks.equal(cp['effects_linked'], [flow.env.effect_id], 'every Control Plane attempt links to the one original effect id')
    checks.equal(cp['distinct_attempt_ids'], 1 + expected_repeats, 'the original and each repeat carry distinct attempt ids in the Control Plane journal')
    checks.expect(original_attempt_id not in repeat_ids and len(set(repeat_ids)) == len(repeat_ids), 'repeat attempt ids differ from the original and from each other')
    checks.expect(set(repeat_ids) <= set(cp['attempt_ids']), 'each repeat attempt id is retained in the journal')
    return cp


def test_scn_c09_route_a_same_decision_repeats_add_no_effect_and_have_distinct_linked_attempts(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        commits = H.count_commits(flow.dest)
        first, e1 = H.execute_a(flow)
        checks.equal(H.result_view(first, e1).get('status'), 'executed', 'original delivery executes')
        s1 = H.db_summary(flow.dest.path)
        repeats = []
        for _ in range(REPEATS):
            res, exc = H.execute_a(flow)
            repeats.append(res)
            view = H.result_view(res, exc)
            checks.equal((view.get('status'), view.get('newly_executed'), view.get('observed_state')), ('reconciled', False, 'applied'), 'repeat reconciles the existing effect and executes nothing new')
        final = H.db_summary(flow.dest.path)
        checks.equal(final['effects'], s1['effects'], 'effect rows byte-identical after every repeat (no excess committed effect)')
        checks.equal(commits, {'calls': 1, 'new_durable': 1}, 'the destination commit ran exactly once')
        cp = _check_a_identity(checks, flow, first.attempt_id, [r.attempt_id for r in repeats], REPEATS)
        local = C.attempt_summary(flow.dest.path)
        checks.equal(local['count'], 1, 'the destination recorded exactly one dispatch attempt (repeats were not re-dispatched)')
        gate = H.effect_gate(final, authorized_effect_ids={flow.env.effect_id}, authorized_digests={H.snapshot_digest(flow.env)})
        return {'original': H.result_view(first, e1), 'repeats': [H.result_view(r, None) for r in repeats], 'control_plane_attempts': {k: v for k, v in cp.items() if k != 'attempt_ids'},
                'destination_attempts': local, 'effects': final['effects'], 'commit_instrumentation': commits, **gate}
    H.run_case(request, record_property, tmp_path, 'C09', trial)


def test_scn_c09_route_a_fresh_decision_for_same_proposal_binds_same_effect_without_new_effect(request, record_property, tmp_path):
    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = H.flow_a(work, mp)
        commits = H.count_commits(flow.dest)
        first, e1 = H.execute_a(flow)
        d2 = flow.f.decide(flow.p, now=ch.NOW)
        env2 = dataclasses.replace(flow.env, decision_id=d2.decision_id)
        res, exc = H.execute_a(flow, envelope=env2, decision=d2)
        view = H.result_view(res, exc)
        checks.equal(d2.effect_id, flow.env.effect_id, 'the fresh decision binds the SAME stable effect identity')
        checks.equal((view.get('status'), view.get('newly_executed')), ('reconciled', False), 'repeat through a fresh decision reconciles and executes nothing new')
        final = H.db_summary(flow.dest.path)
        checks.equal(len(final['effects']), 1, 'one effect only')
        checks.equal(commits['new_durable'], 1, 'one durable commit')
        cp = _check_a_identity(checks, flow, first.attempt_id, [res.attempt_id], 1)
        gate = H.effect_gate(final, authorized_effect_ids={flow.env.effect_id}, authorized_digests={H.snapshot_digest(flow.env)})
        return {'original': H.result_view(first, e1), 'repeat': view, 'control_plane_attempts': {k: v for k, v in cp.items() if k != 'attempt_ids'}, 'effects': final['effects'], **gate}
    H.run_case(request, record_property, tmp_path, 'C09', trial)


def test_scn_c09_route_a_retry_after_lost_acknowledgement_does_not_double_commit(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        commits = H.count_commits(flow.dest)
        first, e1 = H.execute_a(flow, simulate='lost_ack')
        checks.equal(H.result_view(first, e1).get('status'), 'unknown', 'the original delivery is reported unknown (lost acknowledgement)')
        s1 = H.db_summary(flow.dest.path)
        checks.equal(len(s1['effects']), 1, 'the effect committed despite the lost acknowledgement')
        res, exc = H.execute_a(flow)
        view = H.result_view(res, exc)
        checks.equal((view.get('status'), view.get('newly_executed')), ('reconciled', False), 'the retry reconciles the committed effect and does not commit again')
        final = H.db_summary(flow.dest.path)
        checks.equal(final['effects'], s1['effects'], 'effect rows byte-identical after the retry')
        checks.equal(commits['new_durable'], 1, 'one durable commit')
        cp = _check_a_identity(checks, flow, first.attempt_id, [res.attempt_id], 1)
        gate = H.effect_gate(final, authorized_effect_ids={flow.env.effect_id}, authorized_digests={H.snapshot_digest(flow.env)})
        return {'original': H.result_view(first, e1), 'retry': view, 'control_plane_attempts': {k: v for k, v in cp.items() if k != 'attempt_ids'}, 'effects': final['effects'], **gate}
    H.run_case(request, record_property, tmp_path, 'C09', trial)


@pytest.mark.parametrize('explicit_attempt_id', [False, True])
def test_scn_c09_route_a_runtime_local_executor_retry_has_distinct_attempt_linked_to_effect(request, record_property, tmp_path, explicit_attempt_id):
    def trial(work, mp, checks):
        from engine.safe_executor import LocalDestinationExecutor
        flow = H.flow_a(work, mp)
        env = dataclasses.replace(flow.env, attempt_id='attempt-original') if explicit_attempt_id else flow.env
        first, e1 = H.execute_a(flow, envelope=env)
        checks.equal(H.result_view(first, e1).get('status'), 'executed', 'original delivery executes')
        s1 = H.db_summary(flow.dest.path)
        local = LocalDestinationExecutor(flow.dest, flow.executor.policy)
        res = local.execute_snapshot(H.snapshot_env(env))  # the runtime-level retry; same requested attempt id when explicit
        view = H.result_view(res)
        final = H.db_summary(flow.dest.path)
        summary = C.attempt_summary(flow.dest.path)
        checks.equal(len(final['effects']), 1, 'no excess committed effect')
        checks.equal(final['effects'], s1['effects'], 'effect rows byte-identical after the retry')
        checks.equal(view.get('newly_executed'), False, 'the retry executes nothing new')
        checks.equal(summary['count'], 2, 'the retry has its own attempt record')
        checks.equal(summary['distinct_attempt_ids'], True, 'attempt ids are distinct')
        checks.equal(summary['effects_linked'], [flow.env.effect_id], 'both attempts link to the original effect id')
        if explicit_attempt_id:
            checks.equal(view.get('status'), 'denied', 're-using an explicit attempt id is refused')
            checks.equal(summary['attempts'][0]['events'], [('attempted', None), ('executed', None)], 'the ORIGINAL attempt history is preserved, not overwritten')
            checks.equal(summary['attempts'][1]['events'][-1][0], 'denied', 'the conflicting retry is retained under a fresh attempt id as denied')
        else:
            checks.equal(view.get('status'), 'reconciled', 'the retry reconciles the existing effect')
        gate = H.effect_gate(final, authorized_effect_ids={flow.env.effect_id}, authorized_digests={H.snapshot_digest(flow.env)})
        return {'explicit_attempt_id': explicit_attempt_id, 'retry': view, 'destination_attempts': summary, 'effects': final['effects'], **gate}
    H.run_case(request, record_property, tmp_path, 'C09', trial)


# ------------------------------------------------------------------------------------------------
# route B
# ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize('first_outcome', ['acknowledged', 'lost-acknowledgement'])
def test_scn_c09_route_b_repeats_of_consumed_claim_are_refused_without_new_effect(request, record_property, tmp_path, first_outcome):
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        first, e1 = H.execute_b(flow, part, simulate='lost_ack' if first_outcome == 'lost-acknowledgement' else None)
        s1 = H.db_summary(flow.dest.path)
        checks.equal(len(s1['effects']), 1, 'the original delivery committed once')
        repeats = []
        for n in range(REPEATS):
            try:
                res, exc = flow.executor.execute(envelope=part.env, claim_id=part.claim.claim_id, attempt_id=f'retry-{n + 1}'), None
            except Exception as e:  # pragma: no cover - surfaced via observation
                res, exc = None, f'{type(e).__name__}: {e}'
            repeats.append(H.atomic_view(res, exc))
            checks.equal((repeats[-1].get('status'), repeats[-1].get('newly_executed')), ('denied', False), f'repeat {n + 1}: the consumed claim cannot deliver again')
        final = H.db_summary(flow.dest.path)
        checks.equal(final['effects'], s1['effects'], 'effect rows byte-identical after every repeat (no excess committed effect)')
        checks.equal(final['claims'], [('claim-1', 'consumed')], 'claim stays consumed')
        checks.equal(final['budgets'], [('budget-main', 1, 1)], 'budget used exactly once')
        checks.equal(flow.dest.trace.count('after_commit'), 1, 'exactly one commit transaction')
        attempts = C.attempt_summary(flow.dest.path)
        checks.equal((attempts['count'], attempts['effects_linked']), (1, [part.env.effect_id]), 'one attempt record, linked to the original effect id')
        new_failures = [f for f in flow.dest.failure_history() if f['reason_code'] == 'current_authority_rejected']
        checks.equal(len(new_failures), REPEATS, 'each refused repeat leaves its own retained failure record')
        checks.equal({f['effect_id'] for f in new_failures}, {part.env.effect_id}, 'each refusal record links to the original effect id')
        checks.equal(len({f['failure_id'] for f in new_failures}), REPEATS, 'the refusal records are distinct')
        gate = H.effect_gate(final, authorized_effect_ids={part.env.effect_id})
        return {'first_outcome': first_outcome, 'original': H.atomic_view(first, e1), 'repeats': repeats, 'effects': final['effects'], 'claims': final['claims'], 'budgets': final['budgets'],
                'destination_attempts': attempts, 'refusal_records': len(new_failures),
                'attempt_identity_minted_for_repeat': False, 'repeat_identity_evidence': 'distinct failure record linked by effect_id; no attempt_id is minted for a refused repeat', **gate}
    H.run_case(request, record_property, tmp_path, 'C09', trial)


def test_scn_c09_route_b_fresh_claim_for_delivered_effect_does_not_commit_again(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        first, e1 = H.execute_b(flow, part)
        s1 = H.db_summary(flow.dest.path)
        fresh = flow.helpers.make_claim(part.env, claim_id='claim-fresh', budget_id='budget-main', max_effects=1)
        flow.dest.provision_claim(fresh)
        try:
            res, exc = flow.executor.execute(envelope=part.env, claim_id='claim-fresh', attempt_id='retry-fresh'), None
        except Exception as e:  # pragma: no cover - surfaced via observation
            res, exc = None, f'{type(e).__name__}: {e}'
        view = H.atomic_view(res, exc)
        final = H.db_summary(flow.dest.path)
        checks.equal((view.get('status'), view.get('newly_executed')), ('denied', False), 'a second claim for the same effect cannot deliver it again')
        checks.equal(final['effects'], s1['effects'], 'effect rows byte-identical')
        checks.equal(flow.dest.trace.count('after_commit'), 1, 'exactly one commit transaction')
        checks.equal(C.attempt_summary(flow.dest.path)['count'], 1, 'no second dispatch attempt exists')
        return {'original': H.atomic_view(first, e1), 'fresh_claim_retry': view, 'effects': final['effects'], 'claims': final['claims'], 'budgets': final['budgets'],
                'destination_failures': final['failures'], **H.effect_gate(final, authorized_effect_ids={part.env.effect_id})}
    H.run_case(request, record_property, tmp_path, 'C09', trial)


# ------------------------------------------------------------------------------------------------
# route C
# ------------------------------------------------------------------------------------------------

def test_scn_c09_route_c_same_message_redelivery_adds_no_effect(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_c(work, mp)
        first = H.exchange_run(flow)
        v1 = H.exchange_view(first)
        s1 = H.db_summary(flow.dest.path)
        checks.equal(v1['attempt_status'], 'executed', 'original delivery executes')
        views = []
        for _ in range(REPEATS):
            v = H.exchange_view(H.exchange_run(flow))
            views.append(v)
            checks.equal((v['attempted'], bool(v['newly_executed']), v['attempt_status']), (False, False, 'reconciled'), 'redelivery dispatches nothing and reconciles the retained outcome')
        final = H.db_summary(flow.dest.path)
        checks.equal(final['effects'], s1['effects'], 'effect rows byte-identical after every redelivery')
        attempts = C.exchange_attempts(flow)
        checks.equal(attempts['effects_linked'], [first['execution']['effect_id']], 'every retained attempt links to the original effect id')
        checks.equal(C.attempt_summary(flow.dest.path)['count'], 1, 'the destination recorded exactly one dispatch attempt')
        gate = H.effect_gate(final, authorized_effect_ids={first['execution']['effect_id']})
        return {'original': v1, 'redeliveries': views, 'control_plane_attempts': attempts, 'effects': final['effects'], 'note': 'a same-message redelivery is answered from the retained workflow; it mints no new attempt', **gate}
    H.run_case(request, record_property, tmp_path, 'C09', trial)


def test_scn_c09_route_c_new_message_for_same_effect_is_held_not_executed(request, record_property, tmp_path):
    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = H.flow_c(work, mp)
        first = H.exchange_run(flow)
        s1 = H.db_summary(flow.dest.path)
        second_msg = flow.gax.make_message(flow.bundle, message_id='second-owner', created_at=ch.NOW.isoformat(), expires_at=(ch.NOW + timedelta(hours=1)).isoformat())
        second = flow.gax.run_exchange(second_msg, flow.bundle, flow.registry, flow.dest, **flow.kwargs)
        ex = second['execution']
        checks.equal((ex.get('attempted'), bool(ex.get('newly_executed')), ex.get('attempt_status')), (False, False, 'hold'), 'a different message for the same effect is held, not executed')
        checks.equal(ex.get('reason'), 'effect_owned_by_another_message', 'the hold names the ownership barrier')
        checks.equal(ex.get('effect_id'), first['execution']['effect_id'], 'the held request is linked to the original effect id')
        checks.equal(ex.get('retry_eligible'), False, 'the hold is not retry-eligible')
        checks.equal(ex.get('recovery_route'), 'resume_original_exchange', 'the supported recovery route is named')
        final = H.db_summary(flow.dest.path)
        checks.equal(final['effects'], s1['effects'], 'effect rows byte-identical')
        return {'original': H.exchange_view(first), 'second_message': {k: ex.get(k) for k in ('attempted', 'newly_executed', 'attempt_status', 'reason', 'retry_eligible', 'recovery_route')},
                'effects': final['effects'], **H.effect_gate(final, authorized_effect_ids={first['execution']['effect_id']})}
    H.run_case(request, record_property, tmp_path, 'C09', trial)


def test_scn_c09_route_c_resume_original_exchange_mints_distinct_linked_attempt_without_new_effect(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_c(work, mp)
        first = H.exchange_run(flow, lose_ack=True)
        v1 = H.exchange_view(first)
        checks.equal(v1['attempt_status'], 'unknown', 'the original delivery is unknown (lost acknowledgement)')
        s1 = H.db_summary(flow.dest.path)
        before = C.exchange_attempts(flow, with_ids=True)
        resumed = H.exchange_resume(flow)
        v2 = H.exchange_view(resumed)
        after = C.exchange_attempts(flow, with_ids=True)
        checks.equal((v2['attempted'], bool(v2['newly_executed']), v2['attempt_status']), (False, False, 'reconciled'), 'resume reconciles the committed effect without dispatch')
        final = H.db_summary(flow.dest.path)
        checks.equal(final['effects'], s1['effects'], 'effect rows byte-identical after the resume')
        new_ids = [i for i in after['attempt_ids'] if i not in before['attempt_ids']]
        checks.equal(len(new_ids), 1, 'the resume recorded exactly one NEW attempt with its own id')
        checks.equal(after['effects_linked'], [first['execution']['effect_id']], 'original and resume attempts all link to the original effect id')
        checks.equal(C.attempt_summary(flow.dest.path)['count'], 1, 'the destination recorded exactly one dispatch attempt (resume did not dispatch)')
        gate = H.effect_gate(final, authorized_effect_ids={first['execution']['effect_id']})
        public = lambda s: {k: v for k, v in s.items() if k != 'attempt_ids'}
        return {'original': v1, 'resume': v2, 'attempts_before_resume': public(before), 'attempts_after_resume': public(after), 'effects': final['effects'], **gate}
    H.run_case(request, record_property, tmp_path, 'C09', trial)
