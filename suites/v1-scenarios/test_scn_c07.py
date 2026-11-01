"""Catalog scenario C07 - Concurrent authority change (executed against the frozen F5b bounded reference).

SPDX-License-Identifier: Apache-2.0

Stimulus (catalog): race a grant or policy change against the actual destination commit using barriers. Required
observation: record the actual order against the declared linearization contract; expose rather than conceal any
residual race.

Declared linearization contract of the reference (from the reference's own comments/tests, quoted in the evidence):
  * Route B (atomic-claim profile): grant, approval, policy and evidence state live in the destination database and are
    evaluated INSIDE the destination's ``BEGIN IMMEDIATE`` transaction ("same write transaction: no authority writer can
    interleave"); the effect is linearised at COMMIT. A change that lands first prevents the effect; a change that lands
    after the commit leaves it in place.
  * Route A (Control Plane + runtime executor + effective-grant destination): only the DESTINATION effective-grant row
    (grant id/revision/status/permissions, compared as a digest) is checked inside the commit transaction. Resolver-side
    authority (grant status, policy status read through the Control Plane resolver) is read ONCE at effect-time
    revalidation ("no authority-context or grant reread occurs after validation") and is NOT atomic with the commit.
    A resolver-side change that lands between revalidation and commit is therefore a RESIDUAL RACE by design: the effect
    commits. Such a case asserts the by-contract outcome AND records ``residual_race.exposed = true`` in the evidence;
    it is never reported as prevention.
Barriers (no sleeps): the change is applied at an exact seam - before execution; at the commit boundary (after
revalidation, immediately before the destination transaction); inside the commit transaction (a destination-side writer
is started from inside the open write transaction and must queue on the write lock; a resolver-side change is applied
while the transaction is open); after the commit. For queued destination writers the evidence records how many effect
rows were visible at the moment the change landed (1 = the commit linearised first).

Every case runs twice from fresh stores and the normalised observations are compared (owner decision D3). Hard gates (D5):
zero unauthorized effects (an effect is authorized when its revalidation/transaction read precedes the change) and zero
excess duplicate effects. The report-only metric ``effects_committed_after_change_landed`` is recorded separately.
"""
from __future__ import annotations

import threading

import pytest

import _c_2a_helpers as C
import _d02_d05_d09_helpers as H
from _c_2a_helpers import no_network, pinned_reference  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures('pinned_reference')

CONTRACT_A = ('destination effective-grant row checked inside the commit transaction; resolver-side grant/policy read once at '
              'effect-time revalidation and not atomic with the commit (residual race by design)')
CONTRACT_B = 'grant, approval, policy and evidence rows evaluated inside BEGIN IMMEDIATE; effect linearised at COMMIT'
POINTS = ['before-execution', 'commit-boundary', 'inside-commit-transaction', 'after-commit']


def test_scn_c07_source_identity_containment_and_initial_state(request, record_property, tmp_path):
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
        checks.equal(a.get('effective_grants'), [('urn:cognous:grant:routine-1', 'active')], 'route A destination grant starts active')
        return {'initial_state_digest': H.digest({'a': a, 'b': b}), 'declared_linearization': {'route_a': CONTRACT_A, 'route_b': CONTRACT_B},
                'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'C07', trial)


def _queued_writer(fn):
    """Start ``fn`` on its own thread from inside an open write transaction; returns (thread, started, errors, landed)."""
    started = threading.Event()
    errors, landed = [], {}

    def run():
        started.set()
        try:
            landed['result'] = fn()
        except Exception as exc:  # pragma: no cover - surfaced through the observation
            errors.append(f'{type(exc).__name__}: {exc}')
    thread = threading.Thread(target=run)
    thread.start()
    return thread, started, errors, landed


# ------------------------------------------------------------------------------------------------
# route A
# ------------------------------------------------------------------------------------------------

A_CHANGES = {
    'dest-grant-revoked': 'destination',
    'dest-grant-revision-bumped': 'destination',
    'dest-grant-permissions-changed': 'destination',
    'resolver-grant-revoked': 'resolver',
    'resolver-policy-superseded': 'resolver',
}


def _a_change_fn(flow, change):
    ref = H.reference()
    p, g = flow.p, flow.d.binding
    if change == 'dest-grant-revoked':
        return lambda: H.revoke_destination(flow)
    if change == 'dest-grant-revision-bumped':
        return lambda: flow.dest.set_effective_grant(principal=p.principal, grant_id=g.grant_id, revision='2', permissions=p.requested_permissions)
    if change == 'dest-grant-permissions-changed':
        return lambda: flow.dest.set_effective_grant(principal=p.principal, grant_id=g.grant_id, revision=g.grant_revision, permissions=list(p.requested_permissions) + ['admin'])
    if change == 'resolver-grant-revoked':
        return lambda: H.revoke_resolver(flow)
    return lambda: setattr(flow.r.policies[ref.POLICY_REF], 'status', 'superseded')


@pytest.mark.parametrize('point', POINTS)
@pytest.mark.parametrize('change', sorted(A_CHANGES))
def test_scn_c07_route_a_authority_change_ordering_against_destination_commit(request, record_property, tmp_path, change, point):
    level = A_CHANGES[change]

    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        commits = H.count_commits(flow.dest)
        apply_change = _a_change_fn(flow, change)
        trace, queued = [], []

        def landed_view():
            return len(H.db_summary(flow.dest.path)['effects'])
        if point == 'before-execution':
            apply_change()
            trace.append('change_landed_before_execution')
        elif point == 'commit-boundary':
            original = flow.dest.commit

            def change_then_commit(snapshot, **kwargs):
                trace.append('revalidation_done_change_lands_before_commit_transaction')
                apply_change()
                return original(snapshot, **kwargs)
            flow.dest.commit = change_then_commit
        elif point == 'inside-commit-transaction':
            check_profile = flow.dest._check_commit_profile

            def hook(conn, snapshot):
                if level == 'destination':
                    def change_and_look():
                        apply_change()
                        return landed_view()
                    queued.append(_queued_writer(change_and_look))
                    queued[0][1].wait()  # barrier: the writer is racing while the write transaction is open
                    trace.append('destination_writer_started_inside_open_write_transaction')
                else:
                    apply_change()
                    trace.append('resolver_change_landed_inside_open_write_transaction')
                return check_profile(conn, snapshot)
            flow.dest._check_commit_profile = hook
        res, exc = H.execute_a(flow)
        if queued:
            queued[0][0].join(30)
            checks.equal(queued[0][2], [], 'queued destination writer completed without error')
        view = H.result_view(res, exc)
        if point == 'after-commit':
            apply_change()
            trace.append('change_landed_after_acknowledged_commit')
        after = H.db_summary(flow.dest.path)
        again, e2 = H.execute_a(flow)
        post = H.result_view(again, e2)
        final = H.db_summary(flow.dest.path)

        committed_by_contract = point in ('inside-commit-transaction', 'after-commit') or (point == 'commit-boundary' and level == 'resolver')
        if committed_by_contract:
            checks.equal(view.get('status'), 'executed', f'by the declared contract the effect linearises before this change ({point}, {change})')
            checks.equal(len(after['effects']), 1, 'exactly one durable effect')
            checks.equal(after['effects'][0]['state'], 'applied', 'the committed effect stays applied (not reversed)')
            checks.equal(commits['new_durable'], 1, 'exactly one durable commit')
        else:
            checks.expect(view.get('status') in ('denied', 'failed'), f'the change that landed first prevents the effect; observed {view}')
            checks.equal(after['effects'], [], 'no effect after a change that landed before the commit')
            checks.equal(commits['new_durable'], 0, 'no durable commit')
            if point == 'commit-boundary':
                checks.equal(view.get('error'), 'effective_grant_changed_at_commit', 'destination refuses the commit because the effective grant changed')
        if queued and queued[0][3].get('result') is not None:
            checks.equal(queued[0][3]['result'], 1, 'the queued destination writer landed only after the commit (the commit linearised first)')
        checks.equal(post.get('newly_executed'), False, 'a re-presentation after the change dispatches nothing new')
        checks.equal(final['effects'], after['effects'], 'later re-presentation leaves effect rows byte-identical')
        residual = (point == 'commit-boundary' and level == 'resolver')
        effects_after_change = len(after['effects']) if (committed_by_contract and point != 'after-commit') else 0
        gate = H.effect_gate(final, authorized_effect_ids={flow.env.effect_id}, authorized_digests={H.snapshot_digest(flow.env)})
        return {'change': change, 'level': level, 'point': point, 'declared_linearization': CONTRACT_A, 'actual_order': trace, 'result': view,
                'queued_writer_saw_effect_rows_when_landed': queued[0][3].get('result') if queued else None, 'effects': after['effects'],
                'effective_grants': final.get('effective_grants'), 'commit_instrumentation': commits, 're_presentation': post, 'journal': H.journal_view(flow),
                'residual_race': {'exposed': residual, 'description': ('resolver-side change landed after revalidation and before the destination commit; '
                                                                       'the effect committed because the destination cannot see resolver state') if residual else None},
                'effects_committed_after_change_landed': effects_after_change if residual else 0, **gate}
    H.run_case(request, record_property, tmp_path, 'C07', trial)


# ------------------------------------------------------------------------------------------------
# route B
# ------------------------------------------------------------------------------------------------

B_CHANGES = ['grant-revoked', 'grant-revision-bumped', 'policy-superseded', 'approval-revoked', 'evidence-stale']


def _b_change_fn(flow, part, change):
    d, claim = flow.dest, part.claim
    return {
        'grant-revoked': lambda: d.set_grant_status(claim.grant_id, status='revoked'),
        'grant-revision-bumped': lambda: d.set_grant_status(claim.grant_id, status='active', revision='2'),
        'policy-superseded': lambda: d.set_policy_state(claim.policy_state[0].ref, status='superseded'),
        'approval-revoked': lambda: d.set_approval_status(claim.approval_state[0].approval_ref, status='revoked'),
        'evidence-stale': lambda: d.set_evidence_state(claim.evidence_state[0].obligation_id, state='stale'),
    }[change]


@pytest.mark.parametrize('point', POINTS)
@pytest.mark.parametrize('change', B_CHANGES)
def test_scn_c07_route_b_authority_change_ordering_against_atomic_commit(request, record_property, tmp_path, change, point):
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        apply_change = _b_change_fn(flow, part, change)
        trace, queued = [], []

        def hook(stage):
            if point == 'commit-boundary' and stage == 'before_begin':
                trace.append('change_landed_immediately_before_BEGIN_IMMEDIATE')
                apply_change()
            elif point == 'inside-commit-transaction' and stage == 'after_begin':
                def change_and_look():
                    apply_change()
                    return len(H.db_summary(flow.dest.path)['effects'])
                queued.append(_queued_writer(change_and_look))
                queued[0][1].wait()
                trace.append('authority_writer_started_inside_open_write_transaction')
            elif point == 'after-commit' and stage == 'after_commit':
                apply_change()
                trace.append('change_landed_after_COMMIT')
        flow.dest.stage_hook = hook
        if point == 'before-execution':
            apply_change()
            trace.append('change_landed_before_execution')
        res, exc = H.execute_b(flow, part)
        if queued:
            queued[0][0].join(30)
            checks.equal(queued[0][2], [], 'queued authority writer completed without error')
        view = H.atomic_view(res, exc)
        after = H.db_summary(flow.dest.path)
        again, e2 = H.execute_b(flow, part)
        final = H.db_summary(flow.dest.path)
        committed_by_contract = point in ('inside-commit-transaction', 'after-commit')
        if committed_by_contract:
            checks.equal(view.get('status'), 'executed', f'the effect linearises at COMMIT before this change ({point}, {change})')
            checks.equal(len(after['effects']), 1, 'exactly one durable effect')
            checks.equal(after['effects'][0]['state'], 'applied', 'the committed effect stays applied (not reversed)')
            checks.equal([c for c in after['claims'] if c[0] == 'claim-1'], [('claim-1', 'consumed')], 'claim consumed by the commit')
            checks.equal(flow.dest.trace.count('after_commit'), 1, 'exactly one commit transaction')
        else:
            checks.equal(view.get('status'), 'denied', 'the change that landed first prevents the effect')
            checks.equal(after['effects'], [], 'no effect after a change that landed before the transaction')
            checks.equal([c for c in after['claims'] if c[0] == 'claim-1'], [('claim-1', 'issued')], 'the refused claim is not consumed')
            checks.expect(bool(after['failures']), 'refusal observable in destination failure records')
        if queued:
            checks.equal(queued[0][3].get('result'), 1, 'the queued authority writer landed only after the commit (the commit linearised first)')
        checks.equal(H.atomic_view(again, e2).get('newly_executed'), False, 'a re-presentation after the change dispatches nothing new')
        checks.equal(final['effects'], after['effects'], 'later re-presentation leaves effect rows byte-identical')
        gate = H.effect_gate(final, authorized_effect_ids={part.env.effect_id})
        return {'change': change, 'point': point, 'declared_linearization': CONTRACT_B, 'actual_order': trace, 'stage_trace': list(flow.dest.trace), 'result': view,
                'queued_writer_saw_effect_rows_when_landed': queued[0][3].get('result') if queued else None, 'effects': after['effects'], 'claims': final['claims'],
                'budgets': final['budgets'], 'destination_failures': final['failures'], 're_presentation': H.atomic_view(again, e2),
                'residual_race': {'exposed': False, 'description': None}, 'effects_committed_after_change_landed': 0, **gate}
    H.run_case(request, record_property, tmp_path, 'C07', trial)


# ------------------------------------------------------------------------------------------------
# route C: governed exchange (barriers: after the decision; at the destination commit boundary)
# ------------------------------------------------------------------------------------------------

C_CHANGES = {'resolver-grant-revoked': 'resolver', 'resolver-policy-superseded': 'resolver', 'dest-grant-revoked': 'destination'}


@pytest.mark.parametrize('point', ['after-decision-before-revalidation', 'commit-boundary'])
@pytest.mark.parametrize('change', sorted(C_CHANGES))
def test_scn_c07_route_c_exchange_authority_change_ordering(request, record_property, tmp_path, change, point):
    level = C_CHANGES[change]

    def trial(work, mp, checks):
        ref = H.reference()
        flow = H.flow_c(work, mp)
        g = flow.d.binding
        trace = []

        def apply_change():
            if change == 'resolver-grant-revoked':
                next(iter(flow.r.statuses.values())).status = 'revoked'
            elif change == 'resolver-policy-superseded':
                flow.r.policies[ref.POLICY_REF].status = 'superseded'
            else:
                flow.dest.set_effective_grant(principal=flow.p.principal, grant_id=g.grant_id, revision=g.grant_revision,
                                              permissions=flow.p.requested_permissions, status='revoked')
        extra = {}
        if point == 'after-decision-before-revalidation':
            def mutate(resolver):
                trace.append('change_landed_after_decision_before_effect_revalidation')
                apply_change()
            extra['mutate_resolver_after_decision'] = mutate
        else:
            original = flow.dest.commit

            def change_then_commit(snapshot, **kwargs):
                trace.append('revalidation_done_change_lands_before_commit_transaction')
                apply_change()
                return original(snapshot, **kwargs)
            flow.dest.commit = change_then_commit
        res = H.exchange_run(flow, **extra)
        view = H.exchange_view(res)
        after = H.db_summary(flow.dest.path)
        residual = (point == 'commit-boundary' and level == 'resolver')
        if residual:
            checks.equal(view['attempt_status'], 'executed', 'by the declared contract a resolver-side change after revalidation does not stop the commit')
            checks.equal(len(after['effects']), 1, 'the effect committed (residual race exposed)')
        else:
            checks.expect(view['attempt_status'] in ('denied', 'failed', 'hold'), f'the change that landed first prevents the effect; observed {view}')
            checks.equal(after['effects'], [], 'no effect after a change that landed before the commit')
        gate = H.effect_gate(after, authorized_effect_ids={res['execution'].get('effect_id')})
        return {'change': change, 'level': level, 'point': point, 'declared_linearization': CONTRACT_A, 'actual_order': trace, 'view': view,
                'effects': after['effects'], 'residual_race': {'exposed': residual, 'description': 'exchange drives route A; resolver state is not rechecked inside the destination transaction' if residual else None},
                'effects_committed_after_change_landed': len(after['effects']) if residual else 0, **gate}
    H.run_case(request, record_property, tmp_path, 'C07', trial)
