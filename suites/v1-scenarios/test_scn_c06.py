"""Catalog scenario C06 - Authoritative observer unavailable (executed against the frozen F5b bounded reference).

SPDX-License-Identifier: Apache-2.0

Stimulus (catalog): remove the independent observation after an execution acknowledgement. Required observation:
delivery remains unresolved; no verified completion or blind retry.

Method. The destination's read path (``observe`` / ``observe_bound`` / ``reconcile_claim``) is the observer. A barrier
flag is raised exactly when the destination's commit returns (the acknowledgement point) and from then on every
observation either raises ``ConnectionError`` (unavailable) or is served with a stale timestamp. Instance-level
patching only; the reference's product code is untouched. A separate read-only SQLite connection is the test oracle
(an in-process oracle, NOT an independent operational observer). After the assertions the observer is restored so that
the resolution path (effect-free reconcile) is also shown.

Sub-cases: route A (observer unavailable; observation stale; lost acknowledgement AND observer unavailable), route B
(independent observer unavailable after a lost acknowledgement; post-commit observation read fails inside the atomic
executor), route C (governed exchange: original run, redelivery, resume under observer outage and after restoration).
Every case runs twice from fresh stores and the normalised observations are compared (owner decision D3).
Hard gates (D5): zero unauthorized effects and zero excess duplicate effects. A genuine violation FAILS.
"""
from __future__ import annotations

import dataclasses
from datetime import timedelta

import pytest

import _c_2a_helpers as C
import _d02_d05_d09_helpers as H
from _c_2a_helpers import no_network, pinned_reference  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures('pinned_reference')


def test_scn_c06_source_identity_containment_and_initial_state(request, record_property, tmp_path):
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
    H.run_case(request, record_property, tmp_path, 'C06', trial)


class Observer:
    """Barrier-controlled observer outage installed on a destination instance (no product code change)."""

    def __init__(self, dest, mode='unavailable'):
        self.dest = dest
        self.mode = mode
        self.down = False
        self.reads_refused = 0
        orig_commit, orig_observe, orig_bound = dest.commit, dest.observe, dest.observe_bound

        def commit(snapshot, **kwargs):
            try:
                return orig_commit(snapshot, **kwargs)
            finally:
                self.down = True  # the acknowledgement point has been passed (returned or lost): the observer goes away

        def observe(effect_id):
            if self.down and self.mode == 'unavailable':
                self.reads_refused += 1
                raise ConnectionError('authoritative observer unavailable')
            return orig_observe(effect_id)

        def observe_bound(snapshot):
            if self.down and self.mode == 'unavailable':
                self.reads_refused += 1
                raise ConnectionError('authoritative observer unavailable')
            return orig_bound(snapshot)
        dest.commit, dest.observe, dest.observe_bound = commit, observe, observe_bound

    def restore(self):
        self.down = False


# ------------------------------------------------------------------------------------------------
# route A
# ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize('variant', ['observer-unavailable', 'observation-stale', 'lost-ack-and-observer-unavailable'])
def test_scn_c06_route_a_observer_removed_after_ack_leaves_delivery_unresolved(request, record_property, tmp_path, variant):
    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = H.flow_a(work, mp)
        commits = H.count_commits(flow.dest)
        if variant == 'observation-stale':
            observer = Observer(flow.dest, mode='stale')
            # after the acknowledgement point the observer answers, but with a timestamp older than the observation policy allows
            flow.executor.observation_clock = lambda: ch.NOW - timedelta(seconds=flow.f.observation_policy.max_age_seconds + 3600) if observer.down else ch.NOW
        else:
            observer = Observer(flow.dest)
        res, exc = H.execute_a(flow, simulate='lost_ack' if variant.startswith('lost-ack') else None)
        first = H.result_view(res, exc)
        rec = flow.f.records.load()
        s1 = H.db_summary(flow.dest.path)
        checks.equal(first.get('status'), 'unknown', 'delivery is reported unresolved (unknown), not executed/reconciled')
        checks.equal(first.get('observed_state'), 'unknown', 'no destination state is claimed')
        checks.equal([o.state for o in rec.observations], ['absent'], 'only the pre-dispatch absence observation is accepted; nothing after the acknowledgement is recorded as verified')
        checks.expect(rec.reconciliations and rec.reconciliations[-1].result == 'hold' and not rec.reconciliations[-1].observation_accepted,
                      'the last reconciliation is HOLD with the observation not accepted')
        checks.equal(len(s1['effects']), 1, 'the oracle shows the acknowledged effect really committed once')
        # blind retries while the observer is still away: the same decision, then a fresh decision for the same proposal
        again, e2 = H.execute_a(flow)
        d2 = flow.f.decide(flow.p, now=ch.NOW)
        env2 = dataclasses.replace(flow.env, decision_id=d2.decision_id)
        fresh, e3 = H.execute_a(flow, envelope=env2, decision=d2)
        for label, res_, exc_ in (('same decision', again, e2), ('fresh decision', fresh, e3)):
            view = H.result_view(res_, exc_)
            checks.equal((view.get('status'), view.get('newly_executed')), ('denied', False), f'{label}: no blind retry while the observer is unavailable')
        rec_down = flow.executor.reconcile(flow.env, now=ch.NOW)
        checks.equal((rec_down.result, rec_down.retry_eligible, rec_down.observation_accepted), ('hold', False, False), 'effect-free reconcile stays HOLD and never makes the effect retry-eligible')
        s2 = H.db_summary(flow.dest.path)
        checks.equal(s2['effects'], s1['effects'], 'effect rows unchanged by every retry')
        checks.equal(commits['new_durable'], 1, 'exactly one durable commit across execution and all retries')
        # resolution after the observer is restored
        observer.restore()
        rec_up = flow.executor.reconcile(flow.env, now=ch.NOW)
        checks.equal((rec_up.result, rec_up.observation_accepted, rec_up.retry_eligible), ('applied', True, False), 'after restoration the effect is reconciled as applied')
        final_res, e4 = H.execute_a(flow)
        final_view = H.result_view(final_res, e4)
        checks.equal((final_view.get('status'), final_view.get('newly_executed')), ('reconciled', False), 're-execution after restoration reconciles the existing effect')
        final = H.db_summary(flow.dest.path)
        checks.equal(final['effects'], s1['effects'], 'effect rows unchanged after restoration')
        checks.equal(commits['new_durable'], 1, 'still exactly one durable commit')
        gate = H.effect_gate(final, authorized_effect_ids={flow.env.effect_id}, authorized_digests={H.snapshot_digest(flow.env)})
        return {'variant': variant, 'first': first, 'reads_refused': observer.reads_refused > 0, 'cp_attempts': C.cp_attempt_summary(flow)['statuses'],
                'retry_same_decision': H.result_view(again, e2), 'retry_fresh_decision': H.result_view(fresh, e3),
                'reconcile_while_down': C.reconciliation_view(rec_down), 'reconcile_after_restore': C.reconciliation_view(rec_up),
                're_execution_after_restore': final_view, 'effects': final['effects'], 'commit_instrumentation': commits, **gate}
    H.run_case(request, record_property, tmp_path, 'C06', trial)


# ------------------------------------------------------------------------------------------------
# route B
# ------------------------------------------------------------------------------------------------

def test_scn_c06_route_b_independent_observer_unavailable_after_lost_ack_gives_no_completion_and_no_retry(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        snapshot = H.snapshot_env(part.env)
        state = {'down': False}
        original_reconcile = flow.dest.reconcile_claim

        def hook(stage):
            if stage == 'after_commit':
                state['down'] = True  # acknowledgement point reached; the independent read path goes away
        flow.dest.stage_hook = hook

        def reconcile(claim_id, snap):
            if state['down']:
                raise ConnectionError('authoritative observer unavailable')
            return original_reconcile(claim_id, snap)
        flow.dest.reconcile_claim = reconcile
        res, exc = H.execute_b(flow, part, simulate='lost_ack')
        first = H.atomic_view(res, exc)
        s1 = H.db_summary(flow.dest.path)
        checks.expect(res is None or res.status not in ('executed', 'reconciled', 'applied'), f'no completion is claimed while the observer is away; observed {first}')
        checks.equal(len(s1['effects']), 1, 'the oracle shows the atomic commit happened once')
        checks.equal(s1['claims'], [('claim-1', 'consumed')], 'the claim is consumed by the commit')
        again, e2 = H.execute_b(flow, part)
        checks.equal((H.atomic_view(again, e2).get('status'), H.atomic_view(again, e2).get('newly_executed')), ('denied', False), 'no blind retry: the consumed claim cannot be re-presented')
        fresh = flow.helpers.make_claim(part.env, claim_id='claim-fresh', budget_id='budget-main', max_effects=1)
        flow.dest.provision_claim(fresh)
        try:
            res3, e3 = flow.executor.execute(envelope=part.env, claim_id='claim-fresh'), None
        except Exception as exc3:
            res3, e3 = None, f'{type(exc3).__name__}: {exc3}'
        checks.expect(res3 is None or res3.status == 'denied', f'a fresh claim for the same effect does not redeliver; observed {H.atomic_view(res3, e3)}')
        s2 = H.db_summary(flow.dest.path)
        checks.equal(s2['effects'], s1['effects'], 'effect rows unchanged by retries')
        checks.equal(flow.dest.trace.count('after_commit'), 1, 'exactly one committed transaction')
        state['down'] = False
        recovered = flow.dest.reconcile_claim(part.claim.claim_id, snapshot)
        checks.equal((recovered['status'], recovered['retry_eligible']), ('applied', False), 'after restoration reconciliation reports the committed effect')
        gate = H.effect_gate(s2, authorized_effect_ids={part.env.effect_id})
        return {'first': first, 'retry_same_claim': H.atomic_view(again, e2), 'fresh_claim': H.atomic_view(res3, e3), 'effects': s2['effects'], 'claims': s2['claims'],
                'reconcile_after_restore': {k: recovered.get(k) for k in ('status', 'retry_eligible', 'claim_state')}, **gate}
    H.run_case(request, record_property, tmp_path, 'C06', trial)


def test_scn_c06_route_b_post_commit_observation_failure_is_reported_unresolved_not_denied(request, record_property, tmp_path):
    """Observation read inside the atomic executor fails right after COMMIT.

    Required: delivery remains unresolved (an `unknown`-style outcome). The reference's observed behaviour is recorded in
    the evidence file; a result that denies/not-attempts an effect that is durably committed is a violation.
    """
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        state = {'down': False}
        flow.dest.stage_hook = lambda stage: state.__setitem__('down', True) if stage == 'after_commit' else None
        original = flow.dest.observe_bound

        def observe_bound(snapshot):
            if state['down']:
                raise ConnectionError('authoritative observer unavailable')
            return original(snapshot)
        flow.dest.observe_bound = observe_bound
        res, exc = H.execute_b(flow, part)
        view = H.atomic_view(res, exc)
        s1 = H.db_summary(flow.dest.path)
        checks.equal(len(s1['effects']), 1, 'the oracle shows the effect is durably committed')
        checks.expect(res is not None and res.status not in ('executed', 'reconciled', 'applied'), f'no verified completion is claimed; observed {view}')
        checks.expect(res is not None and res.status == 'unknown' and res.attempted is True,
                      f'delivery must be reported unresolved (status unknown, attempted) for a durably committed effect; observed {view} with failure records {s1["failures"]}')
        again, e2 = H.execute_b(flow, part)
        checks.equal(H.atomic_view(again, e2).get('newly_executed'), False, 'no blind retry')
        s2 = H.db_summary(flow.dest.path)
        checks.equal(s2['effects'], s1['effects'], 'effect rows unchanged by retry')
        return {'first': view, 'failure_records': s1['failures'], 'effects': s2['effects'], 'claims': s2['claims'], **H.effect_gate(s2, authorized_effect_ids={part.env.effect_id})}
    H.run_case(request, record_property, tmp_path, 'C06', trial)


# ------------------------------------------------------------------------------------------------
# route C
# ------------------------------------------------------------------------------------------------

def test_scn_c06_route_c_exchange_observer_outage_keeps_delivery_unresolved_until_restored(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_c(work, mp)
        observer = Observer(flow.dest)
        first = H.exchange_run(flow)
        v1 = H.exchange_view(first)
        s1 = H.db_summary(flow.dest.path)
        checks.equal(v1['attempt_status'], 'unknown', 'exchange reports the delivery as unknown')
        checks.equal((v1['unresolved_delivery'], v1['pending_effects']), (True, 1), 'the successor packet keeps the delivery unresolved and the effect pending')
        checks.equal(v1['destination_observed'], 'unknown', 'no destination state is claimed')
        checks.equal(len(s1['effects']), 1, 'the oracle shows the effect committed once')
        redelivery = H.exchange_view(H.exchange_run(flow))
        checks.equal((redelivery['attempted'], redelivery['newly_executed']), (False, False), 'redelivering the message dispatches nothing')
        checks.equal(redelivery['unresolved_delivery'], True, 'redelivery does not resolve the delivery')
        down_resume = None
        try:
            r = H.exchange_view(H.exchange_resume(flow))
            down_resume = {'returned': r}
            checks.expect(r['attempt_status'] not in ('executed', 'reconciled') and r['newly_executed'] is False, f'resume under outage must not claim completion; observed {r}')
        except Exception as exc:
            down_resume = {'raised': f'{type(exc).__name__}: {str(exc)[:160]}'}
        s2 = H.db_summary(flow.dest.path)
        checks.equal(s2['effects'], s1['effects'], 'effect rows unchanged under outage')
        observer.restore()
        resumed = H.exchange_view(H.exchange_resume(flow))
        checks.equal((resumed['attempt_status'], resumed['destination_observed'], resumed['newly_executed']), ('reconciled', 'applied', False), 'after restoration the original effect is reconciled')
        checks.equal(resumed['unresolved_delivery'], False, 'the delivery is resolved only after an accepted observation')
        final = H.db_summary(flow.dest.path)
        checks.equal(final['effects'], s1['effects'], 'effect rows unchanged after restoration')
        return {'first': v1, 'redelivery': redelivery, 'resume_while_down': down_resume, 'resume_after_restore': resumed, 'effects': final['effects'],
                **H.effect_gate(final, authorized_effect_ids={first['execution'].get('effect_id')})}
    H.run_case(request, record_property, tmp_path, 'C06', trial)
