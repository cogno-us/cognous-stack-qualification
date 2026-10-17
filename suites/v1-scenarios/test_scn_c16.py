"""Catalog scenario C16 - Shared budget exhaustion (executed against the frozen F5b bounded reference).

SPDX-License-Identifier: Apache-2.0

Stimulus (catalog): exhaust the declared shared budget before another agent attempts an effect.
Required observation: no effect exceeding the budget under the declared coordination contract; unsupported
coordination is reported.

DECLARED COORDINATION CONTRACT (derived from the reference, not invented):
  * Shared budget = one ``effect_budgets_v1`` row (budget_id, max_effects, used_effects) in the authoritative
    destination store of the atomic-claim profile (route B). Any number of claims (one per agent/effect) may name
    the same budget_id provided they carry the same max_effects.
  * Consumption is atomic with the effect insert and the claim consumption inside one BEGIN IMMEDIATE transaction;
    the budget is re-read after the lock is held, so concurrent agents (threads, processes, separate handles) are
    serialised by the store.
  * A claim naming an existing budget with a different max_effects is refused at provisioning and at execution.
  * Route A (Control Plane + PinnedControlPlaneExecutor + effective-grant destination) has a per-GRANT cap
    (``effective_max_effects`` bound by the decision and enforced by the destination as a cumulative effect count).
NOT part of the contract and therefore REPORTED AS UNSUPPORTED (never inferred): per-agent quotas or sub-budgets,
budget replenishment/raise by an API, agent identity inside the budget record, leases/queues between agents, and
coordination of one budget across separate destination stores. See ``test_scn_c16_unsupported_coordination_is_reported``.

Every case runs twice from fresh stores and the two normalised observations are compared (owner decision D3).
Race cases compare outcome-class counts (which agent wins a race is scheduling-dependent and not contractual).
Hard gate (D5): zero unauthorized effects (including any effect beyond the budget) and zero excess duplicate effects.
"""
from __future__ import annotations

import dataclasses
import sqlite3

import pytest

import _c_2c_helpers as C
import _d02_d05_d09_helpers as H
from _d02_d05_d09_helpers import no_network, pinned_reference  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures('pinned_reference')


def _ids(flow):
    return {p.env.effect_id for p in flow.parts}


def test_scn_c16_source_identity_containment_and_initial_state(request, record_property, tmp_path):
    ref = H.reference()
    H.assert_pins_still_pristine()
    import engine
    from pathlib import Path
    assert Path(engine.__file__).resolve().is_relative_to(ref.paths['runtime'])
    assert ref.profile['components']['runtime']['revision'] == H.FROZEN_RUNTIME

    def trial(work, mp, checks):
        (work / 'b').mkdir()
        (work / 'a').mkdir()
        b = H.db_summary(H.flow_b(work / 'b', effect_nos=(1, 2, 3), budget_max=2).dest.path)
        a = H.db_summary(H.flow_a(work / 'a', mp).dest.path)
        checks.equal(b['effects'], [], 'route B initial destination holds no effect')
        checks.equal(b['budgets'], [('budget-main', 2, 0)], 'declared shared budget starts unused')
        checks.equal(b['claims'], [('claim-1', 'issued'), ('claim-2', 'issued'), ('claim-3', 'issued')], 'every agent claim starts issued')
        checks.equal(a['effects'], [], 'route A initial destination holds no effect')
        return {'initial_state_digest': H.digest({'a': a, 'b': b}), 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'C16', trial)


def test_scn_c16_positive_control_agents_within_budget_each_execute_once(request, record_property, tmp_path):
    """The harness really observes consumption: two agents inside a budget of 3 both execute and consume exactly their share."""
    def trial(work, mp, checks):
        flow = H.flow_b(work, effect_nos=(1, 2), budget_max=3)
        views = [H.atomic_view(*H.execute_b(flow, p)) for p in flow.parts]
        s = H.db_summary(flow.dest.path)
        checks.equal([v['status'] for v in views], ['executed', 'executed'], 'agents within the budget execute')
        checks.equal(s['budgets'], [('budget-main', 3, 2)], 'budget consumption equals the number of effects')
        checks.equal(len(s['effects']), 2, 'two durable effects')
        gate = C.gate_with_budget(s, _ids(flow), 3)
        return {'views': views, 'effects': s['effects'], 'budgets': s['budgets'], 'claims': s['claims'], **gate}
    H.run_case(request, record_property, tmp_path, 'C16', trial)


@pytest.mark.parametrize('budget', [1, 2, 3])
def test_scn_c16_route_b_exhausted_budget_blocks_every_later_agent(request, record_property, tmp_path, budget):
    def trial(work, mp, checks):
        later = 2  # two further agents attempt after exhaustion
        flow = H.flow_b(work, effect_nos=tuple(range(1, budget + later + 1)), budget_max=budget)
        views = {}
        for p in flow.parts:
            views[p.n] = H.atomic_view(*H.execute_b(flow, p))
        s = H.db_summary(flow.dest.path)
        for n in range(1, budget + 1):
            checks.equal(views[n]['status'], 'executed', f'agent {n} inside the budget executes')
        for n in range(budget + 1, budget + later + 1):
            checks.equal(views[n]['status'], 'denied', f'agent {n} after exhaustion is denied')
            checks.expect('budget exhausted' in (views[n]['error'] or ''), f'agent {n} refusal names the exhausted budget: {views[n]["error"]}')
            checks.equal(C.claim_state(s, f'claim-{n}'), 'issued', f'denied agent {n} claim is not consumed')
        checks.equal(len(s['effects']), budget, 'exactly the budgeted number of durable effects exist')
        checks.equal(s['budgets'], [('budget-main', budget, budget)], 'budget fully and exactly used')
        checks.equal(flow.dest.trace.count('after_commit'), budget, 'exactly the budgeted number of committed transactions')
        checks.equal(len(s['attempts']), budget, 'denied agents leave no attempt record (no dispatch)')
        checks.expect(bool(s['failures']), 'denials are observable in the destination failure records')
        gate = C.gate_with_budget(s, _ids(flow), budget)
        return {'budget': budget, 'views': views, 'effects': s['effects'], 'claims': s['claims'], 'budgets': s['budgets'],
                'failures': [f'{c}/{r}/{st}' for c, r, st, _d in s['failures']], **gate}
    H.run_case(request, record_property, tmp_path, 'C16', trial)


def test_scn_c16_route_b_exhaustion_persists_across_restart_and_fresh_claims(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_b(work, effect_nos=(1, 2, 3), budget_max=2)
        H.execute_b(flow, flow.parts[0])
        H.execute_b(flow, flow.parts[1])
        before = H.db_summary(flow.dest.path)
        # restart: a new destination object over the same store, a new executor, and the third agent attempts
        reopened = type(flow.dest)(flow.work, clock=flow.clock)
        executor = type(flow.executor)(workflow=object(), destination=reopened, policy=flow.policy)
        after_restart = H.atomic_view(*H.execute_b(flow, flow.parts[2], executor=executor))
        # fresh authority for a 4th agent naming the same budget with the same declared limit: provisioning is allowed, execution is not
        env4 = flow.helpers.envelope(effect_no=4)
        claim4 = flow.helpers.make_claim(env4, claim_id='claim-4', budget_id='budget-main', max_effects=2)
        reopened.provision_claim(claim4)
        fourth = H.atomic_view(*H.execute_b(flow, type('P', (), {'env': env4, 'claim': claim4})(), executor=executor))
        # consumed claims: re-presenting them adds no effect and no budget use
        again = [H.atomic_view(*H.execute_b(flow, p, executor=executor)) for p in flow.parts[:2]]
        recon = reopened.reconcile_claim('claim-1', H.snapshot_env(flow.parts[0].env))
        final = H.db_summary(flow.dest.path)
        checks.equal(after_restart['status'], 'denied', 'third agent is denied after restart')
        checks.expect('budget exhausted' in (after_restart['error'] or ''), 'restart refusal names the exhausted budget')
        checks.equal(fourth['status'], 'denied', 'a fresh claim on the exhausted budget cannot execute')
        checks.expect('budget exhausted' in (fourth['error'] or ''), 'fresh-claim refusal names the exhausted budget')
        checks.equal([v['status'] for v in again], ['denied', 'denied'], 'consumed claims cannot be replayed')
        checks.equal((recon['status'], recon['retry_eligible']), ('applied', False), 'recovery of a consumed claim reports applied and not retry-eligible')
        checks.equal(final['effects'], before['effects'], 'no effect added by any post-exhaustion attempt')
        checks.equal(final['budgets'], [('budget-main', 2, 2)], 'budget state is unchanged')
        gate = C.gate_with_budget(final, _ids(flow), 2)
        return {'after_restart': after_restart, 'fourth_fresh_claim': fourth, 'replays': again, 'effects': final['effects'], 'budgets': final['budgets'],
                'claims': final['claims'], **gate}
    H.run_case(request, record_property, tmp_path, 'C16', trial)


def test_scn_c16_route_b_partial_and_unknown_ack_effects_still_consume_budget(request, record_property, tmp_path):
    """A partial effect and an effect whose acknowledgement was lost each consume a budget unit: later agents cannot spend it twice."""
    def trial(work, mp, checks):
        flow = H.flow_b(work, effect_nos=(1, 2, 3), budget_max=2)
        first = H.atomic_view(*H.execute_b(flow, flow.parts[0], simulate='partial'))
        second = H.atomic_view(*H.execute_b(flow, flow.parts[1], simulate='lost_ack'))
        third = H.atomic_view(*H.execute_b(flow, flow.parts[2]))
        s = H.db_summary(flow.dest.path)
        checks.equal(first['status'], 'partial', 'first agent reports partial')
        checks.equal(second['status'], 'unknown', 'second agent reports unknown acknowledgement')
        checks.equal(third['status'], 'denied', 'third agent is denied: the budget is spent')
        checks.expect('budget exhausted' in (third['error'] or ''), 'third refusal names the exhausted budget')
        checks.equal(sorted(e['state'] for e in s['effects']), ['applied', 'partial'], 'durable states retained distinctly (partial, applied)')
        checks.equal(s['budgets'], [('budget-main', 2, 2)], 'both uncertain effects consumed their unit')
        gate = C.gate_with_budget(s, _ids(flow), 2)
        return {'views': [first, second, third], 'effects': s['effects'], 'budgets': s['budgets'], 'claims': s['claims'], **gate}
    H.run_case(request, record_property, tmp_path, 'C16', trial)


def test_scn_c16_route_b_refused_attempts_do_not_consume_budget(request, record_property, tmp_path):
    """Refusals (substitution, validity window) leave the budget untouched, so exhaustion happens only at the declared limit."""
    def trial(work, mp, checks):
        flow = H.flow_b(work, effect_nos=(1, 2), budget_max=2)
        p1 = flow.parts[0]
        altered = H.alter_envelope(p1.env, target='urn:cognous:synthetic-account:customer-999')
        refused = [H.atomic_view(*H.execute_b(flow, p1, envelope=altered))]
        flow.clock.value = flow.helpers.BASE + flow.helpers.timedelta(hours=3)
        refused.append(H.atomic_view(*H.execute_b(flow, p1)))
        flow.clock.value = flow.helpers.BASE
        mid = H.db_summary(flow.dest.path)
        checks.equal([r['status'] for r in refused], ['denied', 'denied'], 'both refused attempts are denied')
        checks.equal(mid['budgets'], [('budget-main', 2, 0)], 'refused attempts consume no budget')
        checks.equal(mid['effects'], [], 'refused attempts leave no effect')
        done = [H.atomic_view(*H.execute_b(flow, p)) for p in flow.parts]
        s = H.db_summary(flow.dest.path)
        checks.equal([d['status'] for d in done], ['executed', 'executed'], 'the full declared budget is still available after refusals')
        checks.equal(s['budgets'], [('budget-main', 2, 2)], 'budget exhausted exactly at the declared limit')
        gate = C.gate_with_budget(s, _ids(flow), 2)
        return {'refused': refused, 'done': done, 'budget_after_refusals': mid['budgets'], 'budgets': s['budgets'], 'effects': s['effects'], **gate}
    H.run_case(request, record_property, tmp_path, 'C16', trial)


def test_scn_c16_route_b_budget_cannot_be_inflated_or_reset_by_another_agent(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_b(work, effect_nos=(1,), budget_max=2)
        h = flow.helpers
        executed = [H.atomic_view(*H.execute_b(flow, flow.parts[0]))]
        attempts = {}
        for label, limit in (('inflated_limit', 5), ('reduced_limit', 1)):
            env = h.envelope(effect_no=10 + limit)
            claim = h.make_claim(env, claim_id=f'claim-{label}', budget_id='budget-main', max_effects=limit)
            try:
                flow.dest.provision_claim(claim)
                attempts[label] = 'PROVISIONED'
            except Exception as exc:
                attempts[label] = f'{type(exc).__name__}: {exc}'
        dup_claim = h.make_claim(flow.parts[0].env, claim_id='claim-1', budget_id='budget-main', max_effects=2)
        try:
            flow.dest.provision_claim(dup_claim)
            attempts['reprovision_same_claim_id'] = 'PROVISIONED'
        except Exception as exc:
            attempts['reprovision_same_claim_id'] = f'{type(exc).__name__}: {exc}'
        s = H.db_summary(flow.dest.path)
        for label in ('inflated_limit', 'reduced_limit'):
            checks.expect('shared budget limit mismatch' in attempts[label], f'{label}: provisioning a claim with another limit must be refused; observed {attempts[label]}')
        checks.expect('already provisioned' in attempts['reprovision_same_claim_id'], f'claim identity cannot be re-provisioned; observed {attempts["reprovision_same_claim_id"]}')
        checks.equal(s['budgets'], [('budget-main', 2, 1)], 'budget limit and usage are unchanged by the attempts')
        # the budget can still be spent exactly to its limit by a legitimate second agent and not beyond
        env2 = h.envelope(effect_no=2)
        claim2 = h.make_claim(env2, claim_id='claim-2', budget_id='budget-main', max_effects=2)
        flow.dest.provision_claim(claim2)
        second = H.atomic_view(*H.execute_b(flow, type('P', (), {'env': env2, 'claim': claim2})()))
        env3 = h.envelope(effect_no=3)
        claim3 = h.make_claim(env3, claim_id='claim-3', budget_id='budget-main', max_effects=2)
        flow.dest.provision_claim(claim3)
        third = H.atomic_view(*H.execute_b(flow, type('P', (), {'env': env3, 'claim': claim3})()))
        final = H.db_summary(flow.dest.path)
        checks.equal((second['status'], third['status']), ('executed', 'denied'), 'second agent spends the last unit; third is denied')
        checks.equal(final['budgets'], [('budget-main', 2, 2)], 'budget ends exactly at its declared limit')
        gate = C.gate_with_budget(final, {flow.parts[0].env.effect_id, env2.effect_id}, 2)
        return {'executed_first': executed, 'provisioning_attempts': attempts, 'second': second, 'third': third, 'budgets': final['budgets'],
                'effects': final['effects'], **gate}
    H.run_case(request, record_property, tmp_path, 'C16', trial)


def test_scn_c16_route_b_distinct_budgets_are_independent_declared_boundary(request, record_property, tmp_path):
    """Characterises the declared boundary: coordination exists only among claims naming the SAME budget_id.
    A claim issued by the trusted host against a different budget_id is a different authority, not a bypass.
    Each budget must still hold its own limit exactly."""
    def trial(work, mp, checks):
        flow = H.flow_b(work, effect_nos=(1,), budget_max=1)
        h = flow.helpers
        a = H.atomic_view(*H.execute_b(flow, flow.parts[0]))
        env2 = h.envelope(effect_no=2)
        claim2 = h.make_claim(env2, claim_id='claim-own-budget', budget_id='budget-other', max_effects=1)
        flow.dest.provision_claim(claim2)
        part2 = type('P', (), {'env': env2, 'claim': claim2})()
        b = H.atomic_view(*H.execute_b(flow, part2))
        env3 = h.envelope(effect_no=3)
        claim3 = h.make_claim(env3, claim_id='claim-own-budget-2', budget_id='budget-other', max_effects=1)
        flow.dest.provision_claim(claim3)
        c = H.atomic_view(*H.execute_b(flow, type('P', (), {'env': env3, 'claim': claim3})()))
        s = H.db_summary(flow.dest.path)
        checks.equal((a['status'], b['status'], c['status']), ('executed', 'executed', 'denied'), 'each budget holds its own limit')
        checks.equal(sorted(s['budgets']), [('budget-main', 1, 1), ('budget-other', 1, 1)], 'budgets are accounted independently')
        gate = H.effect_gate(s, authorized_effect_ids={flow.parts[0].env.effect_id, env2.effect_id})
        return {'views': [a, b, c], 'budgets': sorted(s['budgets']), 'effects': s['effects'], **gate}
    H.run_case(request, record_property, tmp_path, 'C16', trial)


@pytest.mark.parametrize('agents,budget', [(2, 1), (6, 3), (8, 1), (8, 7)])
def test_scn_c16_route_b_concurrent_agents_never_exceed_budget_threads(request, record_property, tmp_path, agents, budget):
    def trial(work, mp, checks):
        flow = H.flow_b(work, effect_nos=tuple(range(1, agents + 1)), budget_max=budget)
        results = C.race_threads(flow, flow.parts)
        s = H.db_summary(flow.dest.path)
        norm = C.normalise_race(results)
        checks.equal(norm['outcome_classes'].get('executed', 0), budget, 'exactly the budgeted number of agents win')
        checks.equal(norm['outcome_classes'].get('denied:budget_exhausted', 0), agents - budget, 'every other agent is refused for the exhausted budget')
        checks.equal(len(s['effects']), budget, 'durable effects equal the budget, never more')
        checks.equal(s['budgets'], [('budget-main', budget, budget)], 'budget accounting is exact under contention')
        checks.equal(sum(1 for _, st in s['claims'] if st == 'consumed'), budget, 'exactly the winners consumed their claims')
        gate = C.gate_with_budget(s, _ids(flow), budget)
        return {'race': norm, 'effects_count': len(s['effects']), 'budgets': s['budgets'], 'consumed_claims': sum(1 for _, st in s['claims'] if st == 'consumed'), **gate}
    H.run_case(request, record_property, tmp_path, 'C16', trial)


@pytest.mark.parametrize('agents,budget', [(4, 2)])
def test_scn_c16_route_b_concurrent_agents_never_exceed_budget_processes(request, record_property, tmp_path, agents, budget):
    def trial(work, mp, checks):
        flow = H.flow_b(work, effect_nos=tuple(range(1, agents + 1)), budget_max=budget)
        results = C.race_processes(flow, flow.parts)
        s = H.db_summary(flow.dest.path)
        norm = C.normalise_race(results)
        checks.equal(norm['outcome_classes'].get('executed', 0), budget, 'exactly the budgeted number of processes win')
        checks.equal(norm['outcome_classes'].get('denied:budget_exhausted', 0), agents - budget, 'every other process is refused for the exhausted budget')
        checks.equal(len(s['effects']), budget, 'durable effects equal the budget, never more')
        checks.equal(s['budgets'], [('budget-main', budget, budget)], 'budget accounting is exact across processes')
        gate = C.gate_with_budget(s, _ids(flow), budget)
        return {'race': norm, 'effects_count': len(s['effects']), 'budgets': s['budgets'], **gate}
    H.run_case(request, record_property, tmp_path, 'C16', trial)


def test_scn_c16_route_a_grant_cap_exhausted_blocks_a_second_agent(request, record_property, tmp_path):
    """Route A: the per-grant cap (1) is spent by agent 1; a second agent cannot obtain or execute another effect."""
    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = H.flow_a(work, mp)
        first, e1 = H.execute_a(flow)
        s1 = H.db_summary(flow.dest.path)
        # agent 2a: a different proposal under the same grant/approval -> no authorization decision
        p2 = flow.p.model_copy(update={'target': 'urn:cognous:synthetic-account:customer-002'})
        d2 = flow.f.decide(p2, now=ch.NOW)
        # agent 2b: the same decision/envelope presented again (no new effect)
        again, e2 = H.execute_a(flow)
        # agent 2c: inflates the effect cap in its envelope
        inflated, e3 = H.execute_a(flow, envelope=H.alter_envelope(flow.env, effective_max_effects=5))
        s2 = H.db_summary(flow.dest.path)
        checks.equal(H.result_view(first, e1).get('status'), 'executed', 'agent 1 executes inside the grant cap')
        checks.expect(d2.result != 'authorized', f'a second effect is not authorized under the spent single-effect approval: {d2.result} {d2.reasons}')
        checks.equal(H.result_view(again, e2).get('newly_executed'), False, 'a re-presented decision executes nothing new')
        v3 = H.result_view(inflated, e3)
        checks.expect(v3.get('status') == 'denied' and not v3.get('attempted'), f'an envelope that inflates the effect cap is refused: {v3}')
        checks.equal(s2['effects'], s1['effects'], 'no effect is added by any later agent')
        checks.equal(len(s2['effects']), 1, 'exactly one effect (the grant cap) exists')
        gate = H.effect_gate(s2, authorized_effect_ids={flow.env.effect_id}, authorized_digests={H.snapshot_digest(flow.env)})
        return {'first': H.result_view(first, e1), 'second_proposal_decision': {'result': d2.result, 'reasons': sorted(d2.reasons)},
                're_presented': H.result_view(again, e2), 'inflated_cap': v3, 'effects': s2['effects'], 'journal': H.journal_view(flow), **gate}
    H.run_case(request, record_property, tmp_path, 'C16', trial)


def test_scn_c16_route_a_destination_cap_is_caller_supplied_boundary_observation(request, record_property, tmp_path):
    """Boundary characterization (recorded, not a pass/fail claim about the supported route): below the executor, the route-A
    destination enforces ``op.effective_max_effects`` taken from the CALLER's envelope. A caller with raw destination access
    (outside the supported executor route) can therefore spend more than the decision-bound cap. The supported executor refuses
    this (see the preceding test); the destination alone does not. The observation is retained verbatim in the evidence."""
    from engine.safe_executor import snapshot_envelope

    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = H.flow_a(work, mp)
        H.execute_a(flow)
        digest = flow.r.contexts[ch.PROFILE]['runtime_authority']['expected_effective_grant_digest']
        outcome = {}
        for cap in (1, 2):
            op = dataclasses.replace(flow.env.operation, target=f'urn:cognous:synthetic-account:customer-00{cap + 1}', effective_max_effects=cap)
            env = ch.ExecutionEnvelope(flow.env.version, f'decision-raw-{cap}', f'effect-raw-{cap}', op)
            try:
                flow.dest.commit(snapshot_envelope(env), expected_effective_grant_digest=digest, effective_grant_derivation_version=ch.DERIVATION)
                outcome[f'raw_commit_with_declared_cap_{cap}'] = 'ACCEPTED'
            except Exception as exc:
                outcome[f'raw_commit_with_declared_cap_{cap}'] = f'{type(exc).__name__}: {exc}'
        s = H.db_summary(flow.dest.path)
        checks.expect(outcome['raw_commit_with_declared_cap_1'].endswith('local cumulative max_effects exhausted'),
                      f'a raw commit that honours the decision-bound cap is refused: {outcome}')
        return {'observation': outcome, 'effects_after': len(s['effects']),
                'effects_beyond_decision_bound_cap_via_raw_destination': max(0, len(s['effects']) - 1),
                'declared_boundary': 'destination trusts caller-supplied effective_max_effects; only the executor compares it with the decision binding'}
    H.run_case(request, record_property, tmp_path, 'C16', trial, expect_effects_gate=False)


def test_scn_c16_unsupported_coordination_is_reported(request, record_property, tmp_path):
    """Probe every coordination capability the catalog implies and REPORT which are unsupported. Nothing is inferred."""
    def trial(work, mp, checks):
        (work / 'one').mkdir()
        (work / 'two').mkdir()
        f1 = H.flow_b(work / 'one', effect_nos=(1,), budget_max=1)
        f2 = H.flow_b(work / 'two', effect_nos=(1,), budget_max=1)
        cls = type(f1.dest)
        public = sorted(n for n in dir(cls) if not n.startswith('_'))
        budget_api = [n for n in public if 'budget' in n.lower()]
        columns = C.table_columns(f1.dest.path, 'effect_budgets_v1')
        H.execute_b(f1, f1.parts[0])
        H.execute_b(f2, f2.parts[0])
        total = len(H.db_summary(f1.dest.path)['effects']) + len(H.db_summary(f2.dest.path)['effects'])
        probes = {
            'per_agent_quota_or_subbudget': {'supported': any(c in columns for c in ('agent', 'actor', 'principal', 'agent_id')), 'budget_columns': columns},
            'budget_replenish_or_raise_api': {'supported': any(n for n in budget_api if n != 'budget_state'), 'public_budget_methods': budget_api},
            'agent_identity_in_budget_record': {'supported': 'actor' in columns or 'principal' in columns},
            'cross_store_shared_budget': {'supported': total <= 1,
                                          'observed': f'two independent destination stores both named budget-main (limit 1): {total} effects in total'},
            'agent_leases_or_queues': {'supported': any(('lease' in n.lower() or 'queue' in n.lower() or 'reserve' in n.lower()) for n in public)},
            'budget_at_control_plane_decision_level_route_a': {'supported': False,
                                                              'observed': 'route A cap is per grant (effective_max_effects) enforced at the destination; no cross-grant budget object exists'},
        }
        # contract assertions: what IS supported must be exactly what the reference declares (a change would be news, not a pass)
        checks.equal(columns, ['budget_id', 'max_effects', 'used_effects'], 'shared budget record holds only id, limit and usage')
        checks.equal(budget_api, ['budget_state'], 'the only public budget API is read-only')
        return {'probes': probes, 'unsupported': sorted(k for k, v in probes.items() if not v['supported'])}
    payload = H.run_case(request, record_property, tmp_path, 'C16', trial, expect_effects_gate=False)
    C.write_report(request, record_property, 'unsupported_coordination', {'scenario': 'C16', 'unsupported': payload['run1']['observed']['unsupported'],
                                                                           'probes': payload['run1']['observed']['probes']})
