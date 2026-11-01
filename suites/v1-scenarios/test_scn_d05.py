"""Catalog scenario D05 - Partial effect (executed against the frozen F5b bounded reference).

SPDX-License-Identifier: Apache-2.0

Stimulus (catalog): interrupt a supported multi-part operation. Required observation: delivered and undelivered
parts remain distinguishable; recovery respects current authority and does not redeliver completed parts.

What the reference supports (and therefore what is exercised):
  * a single effect can end in the durable destination state ``partial`` (distinct from ``absent`` and ``applied``);
  * recovery (re-execution, fresh decision, effect-free reconcile, ``resume_original_exchange``) never re-dispatches
    an effect that already has a durable row, and is gated by current authority;
  * the atomic-claim profile supports a shared N-effect budget; a multi-part operation is composed by the harness
    from N independently claimed parts (the reference has NO native multi-part operation, part-level progress record
    or resume protocol - see the report: sub-case "per-part progress / completing the remainder of a partial effect"
    is not exercisable and is deliberately omitted rather than faked).
Every case runs twice from fresh stores and the two normalised observations are compared (owner decision D3).
"""
from __future__ import annotations

import dataclasses

import pytest

import _d02_d05_d09_helpers as H
from _d02_d05_d09_helpers import no_network, pinned_reference  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures('pinned_reference')


def test_scn_d05_source_identity_containment_and_initial_state(request, record_property, tmp_path):
    ref = H.reference()
    H.assert_pins_still_pristine()
    import engine
    from pathlib import Path
    assert Path(engine.__file__).resolve().is_relative_to(ref.paths['runtime'])

    def trial(work, mp, checks):
        (work / 'a').mkdir()
        (work / 'b').mkdir()
        a = H.db_summary(H.flow_a(work / 'a', mp).dest.path)
        b = H.db_summary(H.flow_b(work / 'b', effect_nos=(1, 2, 3)).dest.path)
        checks.equal(a['effects'], [], 'route A initial destination holds no effect')
        checks.equal(b['effects'], [], 'route B initial destination holds no effect')
        checks.equal(b['claims'], [('claim-1', 'issued'), ('claim-2', 'issued'), ('claim-3', 'issued')], 'every part starts undelivered (claim issued)')
        return {'initial_state_digest': H.digest({'a': a, 'b': b}), 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'D05', trial)


# ------------------------------------------------------------------------------------------------
# route A: Control Plane + runtime executor
# ------------------------------------------------------------------------------------------------

def test_scn_d05_route_a_partial_state_is_distinguishable_from_absent_and_applied(request, record_property, tmp_path):
    def trial(work, mp, checks):
        views = {}
        for label, simulate, execute in (('absent', None, False), ('partial', 'partial', True), ('applied', None, True)):
            (work / label).mkdir()
            flow = H.flow_a(work / label, mp)
            res = exc = None
            if execute:
                res, exc = H.execute_a(flow, simulate=simulate)
            s = H.db_summary(flow.dest.path)
            views[label] = {'destination_state': flow.dest.observe(flow.env.effect_id)['state'], 'effect_rows': [e['state'] for e in s['effects']],
                            'result': H.result_view(res, exc) if execute else None, 'journal': H.journal_view(flow),
                            'attempt_events': [a['events'] for a in s['attempts']],
                            'gate': H.effect_gate(s, authorized_effect_ids={flow.env.effect_id}, authorized_digests={H.snapshot_digest(flow.env)})}
        states = {k: v['destination_state'] for k, v in views.items()}
        checks.equal(states, {'absent': 'absent', 'partial': 'partial', 'applied': 'applied'}, 'destination states are mutually distinguishable')
        checks.equal(views['partial']['result']['status'], 'partial', 'executor result reports partial, not executed')
        checks.equal(views['applied']['result']['status'], 'executed', 'executor result reports executed for the whole effect')
        checks.expect(views['partial']['journal']['attempts'][-1:] == ['partial'] and views['applied']['journal']['attempts'][-1:] == ['acknowledged'],
                      f'Control Plane journal keeps partial and acknowledged attempts distinct: {views["partial"]["journal"]["attempts"]} vs {views["applied"]["journal"]["attempts"]}')
        checks.expect(views['partial']['result']['observed_state'] == 'partial', 'partial result is not promoted to applied')
        gate = {k: sum(v['gate'][k] for v in views.values()) for k in ('unauthorized_effects', 'excess_duplicate_effects')}
        return {'views': views, 'trajectory_partial': None, **gate}
    H.run_case(request, record_property, tmp_path, 'D05', trial)


def test_scn_d05_route_a_recovery_under_current_authority_never_redelivers_and_never_promotes_partial(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        commits = H.count_commits(flow.dest)
        first, e1 = H.execute_a(flow, simulate='partial')
        s1 = H.db_summary(flow.dest.path)
        # recovery 1: the same decision is presented again
        again, e2 = H.execute_a(flow)
        s2 = H.db_summary(flow.dest.path)
        # recovery 2: a FRESH decision under current authority for the same proposal
        d2 = flow.f.decide(flow.p, now=H.reference().chain.NOW)
        env2 = dataclasses.replace(flow.env, decision_id=d2.decision_id)
        fresh, e3 = H.execute_a(flow, envelope=env2, decision=d2)
        s3 = H.db_summary(flow.dest.path)
        # recovery 3: effect-free reconciliation
        rec = flow.executor.reconcile(flow.env, now=H.reference().chain.NOW)
        s4 = H.db_summary(flow.dest.path)
        checks.equal(H.result_view(first, e1).get('status'), 'partial', 'first execution reports partial')
        checks.equal(d2.effect_id, flow.env.effect_id, 'fresh decision binds the same effect identity')
        for label, res, exc in (('re-presented decision', again, e2), ('fresh decision', fresh, e3)):
            view = H.result_view(res, exc)
            checks.equal(view.get('status'), 'partial', f'{label}: recovery reports the existing partial effect')
            checks.equal(view.get('newly_executed'), False, f'{label}: nothing newly executed')
        checks.equal(commits, {'calls': 1, 'new_durable': 1}, 'the destination commit ran exactly once across execution and all recoveries')
        checks.equal([s['effects'] for s in (s2, s3, s4)], [s1['effects']] * 3, 'durable effect rows are byte-identical after each recovery')
        checks.equal(s4['effects'][0]['state'], 'partial', 'recovery never promotes partial to applied')
        checks.equal(rec.retry_eligible, False, 'reconcile never makes the partial effect retry-eligible')
        gate = H.effect_gate(s4, authorized_effect_ids={flow.env.effect_id}, authorized_digests={H.snapshot_digest(flow.env)})
        return {'first': H.result_view(first, e1), 're_presented': H.result_view(again, e2), 'fresh_decision': H.result_view(fresh, e3),
                'reconcile': {'result': rec.result, 'retry_eligible': rec.retry_eligible, 'accepted': rec.observation_accepted, 'reasons': rec.reasons},
                'commit_instrumentation': commits, 'effects_after': s4['effects'], 'journal': H.journal_view(flow),
                'trajectory': H.trajectory_a(flow, flow.env, first), **gate}
    H.run_case(request, record_property, tmp_path, 'D05', trial)


@pytest.mark.parametrize('withdrawal', ['resolver-grant-revoked', 'destination-effective-grant-revoked'])
def test_scn_d05_route_a_recovery_after_authority_withdrawal_adds_no_effect(request, record_property, tmp_path, withdrawal):
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        commits = H.count_commits(flow.dest)
        first, e1 = H.execute_a(flow, simulate='partial')
        s1 = H.db_summary(flow.dest.path)
        if withdrawal == 'resolver-grant-revoked':
            H.revoke_resolver(flow)
        else:
            H.revoke_destination(flow)
        res, exc = H.execute_a(flow)
        s2 = H.db_summary(flow.dest.path)
        view = H.result_view(res, exc)
        historical = flow.executor.observe_historical(flow.env)  # observation without renewing authority
        checks.equal((historical.status, historical.observed_state), ('observed', 'partial'),
                     'the partial effect stays observable (distinguishable) after authority is withdrawn')
        if withdrawal == 'resolver-grant-revoked':
            checks.equal(view.get('status'), 'denied', 'recovery is refused by current (withdrawn) authority')
            checks.expect(bool(H.journal_view(flow)['refusals']), 'the refusal is recorded in the Control Plane journal')
        checks.equal(view.get('newly_executed'), False, 'nothing newly executed after withdrawal')
        checks.equal(commits, {'calls': 1, 'new_durable': 1}, 'no second commit after withdrawal')
        checks.equal(s2['effects'], s1['effects'], 'the partial effect row is unchanged by recovery after withdrawal')
        checks.equal(s2['effects'][0]['state'], 'partial', 'the partial effect remains distinguishable (not rolled back, not completed)')
        gate = H.effect_gate(s2, authorized_effect_ids={flow.env.effect_id}, authorized_digests={H.snapshot_digest(flow.env)})
        return {'withdrawal': withdrawal, 'first': H.result_view(first, e1), 'recovery': view, 'historical_observation': historical.observed_state, 'commit_instrumentation': commits,
                'effects_after': s2['effects'], 'journal': H.journal_view(flow), 'destination_failures': s2['failures'], **gate}
    H.run_case(request, record_property, tmp_path, 'D05', trial)


# ------------------------------------------------------------------------------------------------
# route B: atomic claims; multi-part operation composed from N claimed parts on one shared budget
# ------------------------------------------------------------------------------------------------

def test_scn_d05_route_b_partial_claim_is_consumed_and_recovery_never_redelivers(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        first, e1 = H.execute_b(flow, part, simulate='partial')
        s1 = H.db_summary(flow.dest.path)
        recovered = flow.dest.reconcile_claim(part.claim.claim_id, H.snapshot_env(part.env))
        reopened = type(flow.dest)(flow.work, clock=flow.clock)
        recovered_after_restart = reopened.reconcile_claim(part.claim.claim_id, H.snapshot_env(part.env))
        again, e2 = H.execute_b(flow, part)
        # fresh authority for the SAME effect: a second claim is provisioned, but the completed part must not be redelivered
        fresh = flow.helpers.make_claim(part.env, claim_id='claim-fresh', budget_id='budget-main', max_effects=1)
        flow.dest.provision_claim(fresh)
        try:
            res3 = flow.executor.execute(envelope=part.env, claim_id='claim-fresh')
            e3 = None
        except Exception as exc:
            res3, e3 = None, f'{type(exc).__name__}: {exc}'
        s2 = H.db_summary(flow.dest.path)
        checks.equal(H.atomic_view(first, e1).get('status'), 'partial', 'executor reports partial')
        checks.equal(s1['effects'][0]['state'], 'partial', 'durable effect state is partial')
        checks.equal(s1['claims'], [('claim-1', 'consumed')], 'the claim is consumed by the partial delivery')
        checks.equal((recovered['status'], recovered['retry_eligible']), ('partial', False), 'reconcile reports partial and not retry-eligible')
        checks.equal((recovered_after_restart['status'], recovered_after_restart['retry_eligible']), ('partial', False), 'same after restart')
        checks.equal(H.atomic_view(again, e2).get('status'), 'denied', 're-presenting the consumed claim is refused')
        checks.expect(res3 is not None and res3.status == 'denied', f'a fresh claim for the same effect must not redeliver; observed {H.atomic_view(res3, e3)}')
        checks.equal(s2['effects'], s1['effects'], 'durable effect rows unchanged by every recovery attempt')
        checks.equal(flow.dest.trace.count('after_commit'), 1, 'exactly one committed transaction')
        gate = H.effect_gate(s2, authorized_effect_ids={part.env.effect_id})
        return {'first': H.atomic_view(first, e1), 'reconcile': {k: recovered.get(k) for k in ('status', 'retry_eligible', 'claim_state')},
                'reconcile_after_restart': {k: recovered_after_restart.get(k) for k in ('status', 'retry_eligible', 'claim_state')},
                're_presented': H.atomic_view(again, e2), 'fresh_claim': H.atomic_view(res3, e3), 'effects_after': s2['effects'], 'claims': s2['claims'],
                'budgets': s2['budgets'], 'commit_stage_count': flow.dest.trace.count('after_commit'), **gate}
    H.run_case(request, record_property, tmp_path, 'D05', trial)


@pytest.mark.parametrize('resume', ['authority-intact', 'authority-withdrawn'])
def test_scn_d05_route_b_multi_part_interruption_keeps_delivered_and_undelivered_distinct(request, record_property, tmp_path, resume):
    def trial(work, mp, checks):
        flow = H.flow_b(work, effect_nos=(1, 2, 3))
        p1, p2, p3 = flow.parts
        r1, e1 = H.execute_b(flow, p1)                       # part 1 delivered
        r2, e2 = H.execute_b(flow, p2, simulate='partial')    # part 2 interrupted mid-delivery; part 3 never started
        interrupted = H.db_summary(flow.dest.path)
        ids = {p.env.effect_id: p.n for p in flow.parts}
        states = {ids[e['effect_id']]: e['state'] for e in interrupted['effects']}
        checks.equal(states, {1: 'applied', 2: 'partial'}, 'delivered and partially delivered parts are distinguishable by durable state')
        checks.equal(interrupted['claims'], [('claim-1', 'consumed'), ('claim-2', 'consumed'), ('claim-3', 'issued')], 'the undelivered part is distinguishable (claim still issued)')
        checks.equal(interrupted['budgets'], [('budget-main', 3, 2)], 'budget accounts for exactly the two touched parts')
        if resume == 'authority-withdrawn':
            flow.dest.set_grant_status(p3.claim.grant_id, status='revoked')
        # recovery: every part is presented again, in order, with the claim it was issued
        recovered = {}
        for part in (p1, p2, p3):
            res, exc = H.execute_b(flow, part)
            recovered[part.n] = H.atomic_view(res, exc)
        final = H.db_summary(flow.dest.path)
        checks.equal(recovered[1].get('status'), 'denied', 'completed part 1 is not redelivered')
        checks.equal(recovered[2].get('status'), 'denied', 'partially delivered part 2 is not redelivered')
        if resume == 'authority-intact':
            checks.equal(recovered[3].get('status'), 'executed', 'the undelivered part is delivered under current authority')
            checks.equal({ids[e['effect_id']]: e['state'] for e in final['effects']}, {1: 'applied', 2: 'partial', 3: 'applied'},
                         'recovery delivers only the undelivered part; part 2 stays partial')
            checks.equal(final['budgets'], [('budget-main', 3, 3)], 'budget fully used exactly once per part')
            checks.equal(flow.dest.trace.count('after_commit'), 3, 'three committed transactions in total (no redelivery)')
        else:
            checks.equal(recovered[3].get('status'), 'denied', 'withdrawn authority refuses the undelivered part')
            checks.equal({ids[e['effect_id']]: e['state'] for e in final['effects']}, {1: 'applied', 2: 'partial'}, 'no effect is added after withdrawal')
            checks.equal(final['claims'][2], ('claim-3', 'issued'), 'the undelivered part stays distinguishable after withdrawal')
            checks.equal(flow.dest.trace.count('after_commit'), 2, 'two committed transactions in total')
        gate = H.effect_gate(final, authorized_effect_ids={p.env.effect_id for p in flow.parts})
        return {'resume': resume, 'first_two_parts': [H.atomic_view(r1, e1), H.atomic_view(r2, e2)], 'interrupted_state': interrupted['effects'],
                'interrupted_claims': interrupted['claims'], 'recovery': recovered, 'final_effects': final['effects'], 'final_claims': final['claims'],
                'final_budgets': final['budgets'], 'commit_stage_count': flow.dest.trace.count('after_commit'), **gate}
    H.run_case(request, record_property, tmp_path, 'D05', trial)


# ------------------------------------------------------------------------------------------------
# route C: governed-exchange ingress
# ------------------------------------------------------------------------------------------------

def test_scn_d05_route_c_exchange_reports_unresolved_partial_delivery_distinct_from_success(request, record_property, tmp_path):
    def trial(work, mp, checks):
        out = {}
        for label, extra in (('success', {}), ('partial', {'partial_delivery': True})):
            (work / label).mkdir()
            flow = H.flow_c(work / label, mp)
            res = H.exchange_run(flow, **extra)
            s = H.db_summary(flow.dest.path)
            out[label] = {'view': H.exchange_view(res), 'effects': [e['state'] for e in s['effects']], 'gate': H.effect_gate(s, authorized_effect_ids={res['execution'].get('effect_id')})}
        checks.equal(out['success']['view']['unresolved_delivery'], False, 'complete delivery has no unresolved successor state')
        checks.equal(out['partial']['view']['unresolved_delivery'], True, 'partial delivery is reported as unresolved')
        checks.equal(out['partial']['view']['pending_effects'], 1, 'the interrupted effect is listed as pending')
        checks.equal((out['partial']['effects'], out['success']['effects']), (['partial'], ['applied']), 'destination states differ')
        gate = {k: sum(v['gate'][k] for v in out.values()) for k in ('unauthorized_effects', 'excess_duplicate_effects')}
        return {'runs': out, **gate}
    H.run_case(request, record_property, tmp_path, 'D05', trial)


@pytest.mark.parametrize('interruption', ['partial-delivery', 'partial-delivery-then-crash-before-persistence'])
def test_scn_d05_route_c_exchange_recovery_under_current_authority_does_not_redeliver(request, record_property, tmp_path, interruption):
    def trial(work, mp, checks):
        flow = H.flow_c(work, mp)
        first = H.exchange_run(flow, partial_delivery=True, fault_after_dispatch=(interruption != 'partial-delivery'))
        s1 = H.db_summary(flow.dest.path)
        recovery = H.exchange_resume(flow)
        s2 = H.db_summary(flow.dest.path)
        view = H.exchange_view(recovery)
        checks.equal(len(s1['effects']), 1, 'one durable (partial) effect exists after the interruption')
        checks.equal(s1['effects'][0]['state'], 'partial', 'the interrupted effect is partial')
        checks.equal(view['attempted'], False, 'recovery performs no dispatch')
        checks.equal(view['newly_executed'], False, 'recovery executes nothing new')
        checks.equal(view['attempt_status'], 'partial', 'recovery reports the existing partial effect')
        checks.equal(view['unresolved_delivery'], True, 'the successor packet keeps the delivery unresolved')
        checks.equal(s2['effects'], s1['effects'], 'durable effect rows unchanged by recovery')
        redelivery = None
        if interruption == 'partial-delivery':
            redelivery = H.exchange_view(H.exchange_run(flow, partial_delivery=True))
            checks.equal(redelivery['attempted'], False, 'redelivering the same message dispatches nothing')
        s3 = H.db_summary(flow.dest.path)
        checks.equal(s3['effects'], s1['effects'], 'durable effect rows unchanged after redelivery as well')
        gate = H.effect_gate(s3, authorized_effect_ids={recovery['execution'].get('effect_id')})
        return {'interruption': interruption, 'first': H.exchange_view(first), 'recovery': view, 'redelivery': redelivery, 'effects_after': s3['effects'], **gate}
    H.run_case(request, record_property, tmp_path, 'D05', trial)


def test_scn_d05_route_c_exchange_recovery_after_authority_withdrawal_is_denied_without_redelivery(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_c(work, mp)
        first = H.exchange_run(flow, partial_delivery=True)
        s1 = H.db_summary(flow.dest.path)
        H.revoke_resolver(flow)
        recovery = H.exchange_resume(flow)
        s2 = H.db_summary(flow.dest.path)
        view = H.exchange_view(recovery)
        checks.equal(view['attempt_status'], 'denied', 'recovery under withdrawn authority is denied')
        checks.equal(view['newly_executed'], False, 'nothing executed')
        checks.equal(s2['effects'], s1['effects'], 'the original partial effect is unchanged (not reversed, not completed)')
        checks.equal(s2['effects'][0]['state'], 'partial', 'partial remains distinguishable')
        checks.equal(view['unresolved_delivery'], True, 'the delivery stays unresolved after the denied recovery')
        gate = H.effect_gate(s2, authorized_effect_ids={first['execution'].get('effect_id')})
        return {'first': H.exchange_view(first), 'recovery': view, 'effects_after': s2['effects'], **gate}
    H.run_case(request, record_property, tmp_path, 'D05', trial)
