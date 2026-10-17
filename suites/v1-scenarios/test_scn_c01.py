"""Catalog scenario C01 - Missing grant (executed against the frozen F5b bounded reference).

SPDX-License-Identifier: Apache-2.0

Stimulus (catalog): attempt the bounded action without a grant. Required observation: refuse execution; the
authoritative destination is unchanged; refusal evidence is retained. Forbidden: effects outside declared authority.

"Without a grant" has distinct meanings in the reference, each exercised independently (the execution contract
requires each stimulus variant to run on its own):
  A  decision-level   : the Control Plane resolver cannot establish any grant (status absent / unknown, issued grant
                        absent from or null in the authority context, authority context absent). The decision is a HOLD
                        with no binding; the caller then tries to execute anyway with the best envelope it can assemble.
  A  effect-time      : the grant disappears from the resolver between decision and execution.
  A  destination      : the destination's effective-grant authority row is absent at commit.
  B  atomic claim     : the authoritative grant row is absent, its status is unknown, or no claim was ever provisioned.
  C  governed exchange: resolver has no grant (before the run, after the decision) or the context has no issued grant.
Every case runs twice from fresh stores and the normalised observations are compared (owner decision D3).
Hard gates (D5): zero unauthorized effects and zero excess duplicate effects. Nothing here is xfail.
"""
from __future__ import annotations

import sqlite3

import pytest

import _c_2a_helpers as C
import _d02_d05_d09_helpers as H
from _c_2a_helpers import no_network, pinned_reference  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures('pinned_reference')


def _failures(summary):
    return ';'.join(f'{c}/{r}/{s}: {d}' for c, r, s, d in summary['failures'])


def test_scn_c01_source_identity_containment_and_initial_state(request, record_property, tmp_path):
    ref = H.reference()
    H.assert_pins_still_pristine()
    import engine, agent_control_plane
    from pathlib import Path
    assert Path(engine.__file__).resolve().is_relative_to(ref.paths['runtime'])
    assert Path(agent_control_plane.__file__).resolve().is_relative_to(ref.paths['control_plane'])

    def trial(work, mp, checks):
        (work / 'a').mkdir()
        (work / 'b').mkdir()
        a = H.db_summary(C.flow_a_pre(work / 'a', mp).dest.path)
        b = H.db_summary(H.flow_b(work / 'b').dest.path)
        checks.equal((a['effects'], a['attempts']), ([], []), 'route A initial destination holds no effect or attempt')
        checks.equal((b['effects'], b['attempts']), ([], []), 'route B initial destination holds no effect or attempt')
        checks.equal(b['claims'], [('claim-1', 'issued')], 'route B claim starts issued')
        return {'initial_state_digest': H.digest({'a': a, 'b': b}), 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'C01', trial)


# ------------------------------------------------------------------------------------------------
# positive controls: with a grant the same harness really observes the effect
# ------------------------------------------------------------------------------------------------

def test_scn_c01_positive_control_route_a_with_grant_executes_once(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        res, exc = H.execute_a(flow)
        view = H.result_view(res, exc)
        checks.equal(view.get('status'), 'executed', 'request with a grant executes')
        s = H.db_summary(flow.dest.path)
        checks.equal(len(s['effects']), 1, 'exactly one durable effect')
        return {'result': view, 'effects': s['effects'],
                **H.effect_gate(s, authorized_effect_ids={flow.env.effect_id}, authorized_digests={H.snapshot_digest(flow.env)})}
    H.run_case(request, record_property, tmp_path, 'C01', trial)


def test_scn_c01_positive_control_route_b_with_grant_executes_once(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        res, exc = H.execute_b(flow, part)
        view = H.atomic_view(res, exc)
        checks.equal(view.get('status'), 'executed', 'claimed request with a grant executes')
        s = H.db_summary(flow.dest.path)
        checks.equal(s['claims'], [('claim-1', 'consumed')], 'claim consumed once')
        return {'result': view, 'effects': s['effects'], **H.effect_gate(s, authorized_effect_ids={part.env.effect_id})}
    H.run_case(request, record_property, tmp_path, 'C01', trial)


# ------------------------------------------------------------------------------------------------
# route A, decision-level: no grant can be established at decision time
# ------------------------------------------------------------------------------------------------

def _no_status(p, r, f, dest):
    r.statuses.clear()


def _issued_grant_null(p, r, f, dest):
    r.contexts[H.reference().chain.PROFILE]['grant'] = None


def _issued_grant_deleted(p, r, f, dest):
    del r.contexts[H.reference().chain.PROFILE]['grant']


def _status_unknown(p, r, f, dest):
    next(iter(r.statuses.values())).status = 'unknown'


def _no_context(p, r, f, dest):
    r.contexts.clear()


A_DECISION_VARIANTS = {
    'grant-status-absent': (_no_status, {'status_unreadable'}),
    'issued-grant-null-in-context': (_issued_grant_null, {'issued_grant_missing'}),
    'issued-grant-key-absent-in-context': (_issued_grant_deleted, {'issued_grant_missing'}),
    'grant-status-unknown': (_status_unknown, {'grant_unknown'}),
    'authority-context-absent': (_no_context, {'authority_context_missing'}),
}


@pytest.mark.parametrize('variant', sorted(A_DECISION_VARIANTS))
def test_scn_c01_route_a_decision_without_grant_is_held_and_execution_is_refused(request, record_property, tmp_path, variant):
    mutate, expected_reasons = A_DECISION_VARIANTS[variant]

    def trial(work, mp, checks):
        flow = C.flow_a_pre(work, mp, mutate)
        decision = C.decision_view(flow)
        checks.equal(decision['result'], 'hold', 'a request without a grant is not authorized')
        checks.equal(decision['has_binding'], False, 'no authorization binding is minted without a grant')
        checks.expect(expected_reasons <= set(decision['reasons']), f'decision reasons name the missing grant: {decision["reasons"]}')
        flow.executor, flow.env = C.best_effort_executor(flow)
        before = H.db_summary(flow.dest.path)
        res, exc = H.execute_a(flow)
        view = H.result_view(res, exc)
        after = H.db_summary(flow.dest.path)
        checks.expect(res is not None and res.status == 'denied' and not res.attempted, f'execution is refused before dispatch; observed {view}')
        checks.equal(after['effects'], before['effects'], 'authoritative destination unchanged (effects)')
        checks.equal(after['attempts'], [], 'no dispatch attempt recorded')
        journal = C.journal_decisions(flow)
        checks.expect(any(d['result'] == 'hold' and expected_reasons <= set(d['reasons']) for d in journal),
                      f'refusal evidence retained in the Control Plane journal: {journal}')
        checks.expect(bool(after['failures']), 'refusal evidence retained in the destination failure records')
        return {'variant': variant, 'decision': decision, 'result': view, 'journal_decisions': journal, 'destination_failures': _failures(after),
                'effects': after['effects'], **H.effect_gate(after)}
    H.run_case(request, record_property, tmp_path, 'C01', trial)


# ------------------------------------------------------------------------------------------------
# route A, effect time: the grant is gone between decision and execution
# ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize('variant', ['grant-status-removed-after-decision', 'issued-grant-removed-after-decision', 'grant-status-unknown-after-decision'])
def test_scn_c01_route_a_grant_missing_at_effect_time_is_refused_with_retained_refusal(request, record_property, tmp_path, variant):
    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = H.flow_a(work, mp)
        if variant == 'grant-status-removed-after-decision':
            flow.r.statuses.clear()
        elif variant == 'issued-grant-removed-after-decision':
            flow.r.contexts[ch.PROFILE]['grant'] = None
        else:
            next(iter(flow.r.statuses.values())).status = 'unknown'
        res, exc = H.execute_a(flow)
        view = H.result_view(res, exc)
        after = H.db_summary(flow.dest.path)
        checks.expect(res is not None and res.status == 'denied' and not res.attempted, f'execution is refused; observed {view}')
        checks.equal(after['effects'], [], 'authoritative destination unchanged')
        checks.equal(after['attempts'], [], 'no dispatch attempt recorded')
        refusals = C.journal_refusal_reasons(flow)
        checks.expect(bool(refusals) and bool(after['failures']), f'refusal retained in journal and destination; journal refusals {refusals}')
        return {'variant': variant, 'result': view, 'journal_refusals': refusals, 'destination_failures': _failures(after), 'effects': after['effects'],
                'trajectory': H.trajectory_a(flow, flow.env, res) if res is not None else {}, **H.effect_gate(after)}
    H.run_case(request, record_property, tmp_path, 'C01', trial)


# ------------------------------------------------------------------------------------------------
# route A, destination: the destination's own effective-grant authority row is absent at commit
# ------------------------------------------------------------------------------------------------

def test_scn_c01_route_a_destination_effective_grant_absent_is_refused_at_commit(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)  # the Control Plane still sees an active grant; only the destination authority row is gone
        conn = sqlite3.connect(flow.dest.path)
        conn.execute('DELETE FROM effective_grants_v1')
        conn.commit()
        conn.close()
        commits = H.count_commits(flow.dest)
        res, exc = H.execute_a(flow)
        view = H.result_view(res, exc)
        after = H.db_summary(flow.dest.path)
        checks.expect(res is not None and res.status == 'failed' and res.error == 'effective_grant_changed_at_commit', f'commit is refused for the missing grant; observed {view}')
        checks.equal(after['effects'], [], 'authoritative destination unchanged')
        checks.equal(commits['new_durable'], 0, 'no durable commit')
        events = [a['events'] for a in after['attempts']]
        checks.expect(bool(events) and events[-1][-1][0] == 'failed', f'refusal evidence retained in the attempt history: {events}')
        return {'result': view, 'attempt_events': events, 'commit_instrumentation': commits, 'effects': after['effects'], **H.effect_gate(after)}
    H.run_case(request, record_property, tmp_path, 'C01', trial)


# ------------------------------------------------------------------------------------------------
# route B: atomic-claim profile
# ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize('variant', ['grant-row-absent', 'grant-status-unknown', 'claim-never-provisioned'])
def test_scn_c01_route_b_without_authoritative_grant_is_refused_and_claim_untouched(request, record_property, tmp_path, variant):
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        claim_id = part.claim.claim_id
        if variant == 'grant-row-absent':
            flow.dest.remove_authoritative_state('grant', part.claim.grant_id)
        elif variant == 'grant-status-unknown':
            flow.dest.set_grant_status(part.claim.grant_id, status='unknown')
        else:
            claim_id = 'claim-never-provisioned'
        res, exc = H.execute_b(flow, part) if variant != 'claim-never-provisioned' else (None, None)
        if variant == 'claim-never-provisioned':
            try:
                res, exc = flow.executor.execute(envelope=part.env, claim_id=claim_id), None
            except Exception as e:  # pragma: no cover - surfaced via observation
                res, exc = None, f'{type(e).__name__}: {e}'
        view = H.atomic_view(res, exc)
        after = H.db_summary(flow.dest.path)
        checks.expect(res is not None and res.status == 'denied' and not res.attempted, f'execution is refused before any effect; observed {view}')
        checks.equal(after['effects'], [], 'authoritative destination unchanged')
        checks.equal(after['attempts'], [], 'no attempt recorded')
        checks.equal([c for c in after['claims'] if c[0] == 'claim-1'], [('claim-1', 'issued')], 'the issued claim is not consumed by a refusal')
        checks.equal(after['budgets'], [('budget-main', 1, 0)], 'budget unused')
        checks.expect(bool(after['failures']), 'refusal evidence retained in the destination failure records')
        return {'variant': variant, 'result': view, 'destination_failures': _failures(after), 'claims': after['claims'], 'budgets': after['budgets'],
                'effects': after['effects'], **H.effect_gate(after)}
    H.run_case(request, record_property, tmp_path, 'C01', trial)


# ------------------------------------------------------------------------------------------------
# route C: governed-exchange ingress
# ------------------------------------------------------------------------------------------------

def _exchange_case(request, record_property, tmp_path, variant):
    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = H.flow_c(work, mp)
        extra = {}
        if variant == 'resolver-grant-status-absent':
            flow.r.statuses.clear()
        elif variant == 'issued-grant-null-in-context':
            flow.r.contexts[ch.PROFILE]['grant'] = None
        else:
            extra = {'mutate_resolver_after_decision': lambda resolver: resolver.statuses.clear()}
        res = H.exchange_run(flow, **extra)
        view = H.exchange_view(res)
        after = H.db_summary(flow.dest.path)
        expected = 'denied' if variant == 'resolver-grant-absent-after-decision' else 'hold'
        checks.equal(view['attempt_status'], expected, 'exchange refuses to execute without a grant')
        checks.equal(view['attempted'], False, 'nothing dispatched')
        checks.equal(view['newly_executed'], False, 'nothing executed')
        checks.equal(after['effects'], [], 'authoritative destination unchanged')
        journal = C.exchange_journal(flow)
        retained = bool(journal) and (any(d['result'] == 'hold' for j in journal for d in j['decisions']) or any(j['refusals'] for j in journal))
        checks.expect(retained, f'refusal evidence retained in the exchange Control Plane journal: {journal}')
        return {'variant': variant, 'view': view, 'journal': journal, 'effects': after['effects'], **H.effect_gate(after)}
    H.run_case(request, record_property, tmp_path, 'C01', trial)


@pytest.mark.parametrize('variant', ['resolver-grant-status-absent', 'issued-grant-null-in-context', 'resolver-grant-absent-after-decision'])
def test_scn_c01_route_c_exchange_without_grant_is_refused(request, record_property, tmp_path, variant):
    _exchange_case(request, record_property, tmp_path, variant)
