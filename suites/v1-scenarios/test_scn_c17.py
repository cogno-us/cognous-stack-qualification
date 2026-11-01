"""Catalog scenario C17 - Stale shared state (executed against the frozen F5b bounded reference).

SPDX-License-Identifier: Apache-2.0

Stimulus (catalog): execute using a stale shared-state version after another agent updates it.
Required observation: reject or reconcile according to the declared concurrency contract; no silently lost update or
expanded authority.

DECLARED CONCURRENCY CONTRACT (derived from the reference, not invented): FAIL-CLOSED REJECTION, not reconciliation.
  * The shared mutable state is the authoritative authority state: grant (status, revision), approvals, policies (version,
    status), evidence (state, age) in the atomic destination store (route B); the grant status/revision/approval/policy/
    evidence inputs at the Control Plane resolver and the effective-grant row at the destination (route A).
  * A claim (route B) or decision (route A) captures the versions seen when it was issued. At execution the versions are
    re-read under the destination's write lock (route B: BEGIN IMMEDIATE; route A: the effect transaction) and any
    difference refuses the effect. There is no merge or reconcile path for a stale claim/decision: the supported way
    forward is a fresh claim/decision for the CURRENT versions.
  * The executor never writes authority state; a stale caller cannot overwrite or revive a newer version (claim
    provisioning refuses to disagree with existing authoritative rows).
NOT part of the contract (reported, never inferred): general multi-agent shared-document concurrency, compare-and-set on the
trusted authority writers (no version check; only a revoked grant revision is final) and reconciliation of a stale claim. See
``test_scn_c17_unsupported_concurrency_is_reported``.

Every case runs twice from fresh stores and the two normalised observations are compared (owner decision D3).
Hard gate (D5): zero unauthorized effects and zero excess duplicate effects.
"""
from __future__ import annotations

import dataclasses
import threading
from datetime import timedelta

import pytest

import _c_2c_helpers as C
import _d02_d05_d09_helpers as H
from _d02_d05_d09_helpers import no_network, pinned_reference  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures('pinned_reference')


def effective_grant_rows(path):
    import sqlite3
    from pathlib import Path
    conn = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute('SELECT * FROM effective_grants_v1 ORDER BY grant_id')]
    finally:
        conn.close()


def _plain(flow):
    """A second agent's handle on the same store (plain class, no test hook)."""
    return type(flow.dest).__bases__[0](flow.work, clock=flow.clock)


def test_scn_c17_source_identity_containment_and_initial_state(request, record_property, tmp_path):
    ref = H.reference()
    H.assert_pins_still_pristine()
    import engine
    from pathlib import Path
    assert Path(engine.__file__).resolve().is_relative_to(ref.paths['runtime'])

    def trial(work, mp, checks):
        (work / 'a').mkdir()
        (work / 'b').mkdir()
        b = H.flow_b(work / 'b')
        a = H.flow_a(work / 'a', mp)
        sb, sa = H.db_summary(b.dest.path), H.db_summary(a.dest.path)
        checks.equal(sb['effects'], [], 'route B initial destination holds no effect')
        checks.equal(sa['effects'], [], 'route A initial destination holds no effect')
        auth = C.authority_rows(b.dest.path)
        checks.equal({t: [r.get('status', r.get('state')) for r in rows] for t, rows in auth.items()},
                     {'authority_grants_v1': ['active'], 'authority_approvals_v1': ['active'], 'authority_policies_v1': ['active'], 'authority_evidence_v1': ['current']},
                     'authoritative shared state starts current')
        return {'initial_state_digest': H.digest({'a': sa, 'b': sb, 'auth': auth}), 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'C17', trial)


def test_scn_c17_positive_control_unchanged_versions_execute_once(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        view = H.atomic_view(*H.execute_b(flow, part))
        s = H.db_summary(flow.dest.path)
        checks.equal(view['status'], 'executed', 'a claim whose versions are still current executes')
        checks.equal(len(s['effects']), 1, 'exactly one effect')
        gate = H.effect_gate(s, authorized_effect_ids={part.env.effect_id})
        return {'view': view, 'effects': s['effects'], 'claims': s['claims'], **gate}
    H.run_case(request, record_property, tmp_path, 'C17', trial)


# ------------------------------------------------------------------------------------------------
# route B: another agent updates the shared authority state; the stale claim is then presented
# ------------------------------------------------------------------------------------------------

B_UPDATES = {
    # id: (update(flow, part), expected refusal text)
    'grant_revision_bumped_by_other_agent': (lambda f, p: f.dest.set_grant_status(p.claim.grant_id, status='active', revision='2'), 'authoritative grant state invalid'),
    'grant_revoked_by_other_agent': (lambda f, p: f.dest.set_grant_status(p.claim.grant_id, status='revoked'), 'authoritative grant state invalid'),
    'grant_suspended_by_other_agent': (lambda f, p: f.dest.set_grant_status(p.claim.grant_id, status='suspended'), 'authoritative grant state invalid'),
    'approval_withdrawn_by_other_agent': (lambda f, p: f.dest.set_approval_status(f.helpers.APPROVAL, status='revoked'), 'authoritative approval state invalid'),
    'policy_version_changed_by_other_agent': (lambda f, p: f.dest.set_policy_state(f.helpers.POLICY_REF, version='2'), 'authoritative policy state invalid'),
    'policy_superseded_by_other_agent': (lambda f, p: f.dest.set_policy_state(f.helpers.POLICY_REF, status='superseded'), 'authoritative policy state invalid'),
    'evidence_marked_stale_by_other_agent': (lambda f, p: f.dest.set_evidence_state(f.helpers.EVIDENCE, state='stale'), 'authoritative evidence state invalid'),
    'evidence_removed_by_other_agent': (lambda f, p: f.dest.remove_authoritative_state('evidence', f.helpers.EVIDENCE), 'authoritative evidence state unavailable'),
    'grant_removed_by_other_agent': (lambda f, p: f.dest.remove_authoritative_state('grant', p.claim.grant_id), 'authoritative grant state unavailable'),
}


@pytest.mark.parametrize('update', sorted(B_UPDATES))
def test_scn_c17_route_b_stale_claim_is_rejected_after_another_agent_updates_shared_state(request, record_property, tmp_path, update):
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        apply, needle = B_UPDATES[update]
        apply(flow, part)
        after_update = C.authority_rows(flow.dest.path)
        res, exc = H.execute_b(flow, part)
        view = H.atomic_view(res, exc)
        s = H.db_summary(flow.dest.path)
        checks.equal(view['status'], 'denied', f'{update}: the stale claim is rejected')
        checks.expect(needle in (view['error'] or ''), f'{update}: refusal names the changed state ({needle}); observed {view["error"]}')
        checks.equal(s['effects'], [], f'{update}: no effect from stale state')
        checks.equal(C.claim_state(s, part.claim.claim_id), 'issued', f'{update}: the stale claim is not consumed')
        checks.equal(s['budgets'], [('budget-main', 1, 0)], f'{update}: no budget consumed')
        checks.equal(C.authority_rows(flow.dest.path), after_update, f'{update}: the stale attempt did not overwrite the other agent\'s update (no lost update)')
        checks.expect(bool(s['failures']), f'{update}: rejection observable in destination failure records')
        gate = H.effect_gate(s, authorized_effect_ids=set())
        return {'update': update, 'view': view, 'claims': s['claims'], 'authority_after_update': after_update, 'failures': [f'{c}/{r}/{st}' for c, r, st, _d in s['failures']], **gate}
    H.run_case(request, record_property, tmp_path, 'C17', trial)


def test_scn_c17_route_b_evidence_aged_past_its_freshness_is_rejected(request, record_property, tmp_path):
    """Staleness by time rather than by another agent's write: required evidence older than max_age is refused."""
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        flow.clock.value = flow.helpers.BASE + timedelta(seconds=301)
        view = H.atomic_view(*H.execute_b(flow, part))
        s = H.db_summary(flow.dest.path)
        checks.equal(view['status'], 'denied', 'aged evidence is refused')
        checks.expect('evidence expired' in (view['error'] or ''), f'refusal names the expiry: {view["error"]}')
        checks.equal(s['effects'], [], 'no effect')
        return {'view': view, 'claims': s['claims'], **H.effect_gate(s, authorized_effect_ids=set())}
    H.run_case(request, record_property, tmp_path, 'C17', trial)


def test_scn_c17_route_b_reissue_at_new_revision_requires_authority_rebinding_not_provisioning(request, record_property, tmp_path):
    """There is no merge/reconcile for a stale claim. Re-issuing one for the NEW grant revision through claim provisioning is refused
    because the existing approval is bound to the old revision: provisioning cannot widen or carry authority across versions."""
    def trial(work, mp, checks):
        flow = H.flow_b(work, effect_nos=(1,))
        part = flow.parts[0]
        flow.dest.set_grant_status(part.claim.grant_id, status='active', revision='2')
        stale = H.atomic_view(*H.execute_b(flow, part))
        rows = C.authority_rows(flow.dest.path)
        op2 = dataclasses.replace(part.env.operation, grant_revision='2')
        env2 = dataclasses.replace(part.env, operation=op2, decision_id='decision-1-rev2')
        claim2 = flow.helpers.make_claim(env2, claim_id='claim-1-rev2', budget_id='budget-main', max_effects=1)
        outcome = 'PROVISIONED'
        try:
            flow.dest.provision_claim(claim2)
        except Exception as exc:
            outcome = f'{type(exc).__name__}: {exc}'
        s = H.db_summary(flow.dest.path)
        checks.equal(stale['status'], 'denied', 'the stale claim is rejected')
        checks.expect('existing authoritative approval state rejects claim provisioning' in outcome, f'provisioning a rev-2 claim against rev-1 approval must be refused; observed {outcome}')
        checks.equal(C.authority_rows(flow.dest.path), rows, 'authority state unchanged by the refused re-issuance')
        checks.equal(s['effects'], [], 'no effect')
        return {'stale': stale, 'reissue_attempt': outcome, 'claims': s['claims'], **H.effect_gate(s, authorized_effect_ids=set())}
    H.run_case(request, record_property, tmp_path, 'C17', trial)


def test_scn_c17_route_b_trusted_refresh_of_stale_evidence_lets_the_same_claim_proceed_exactly_once(request, record_property, tmp_path):
    """The supported recovery for time/evidence staleness is a refresh by the trusted authority writer, after which the SAME claim
    (same budget, same effect) executes exactly once; the earlier refusal must not have consumed anything."""
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        flow.dest.set_evidence_state(flow.helpers.EVIDENCE, state='stale')
        stale = H.atomic_view(*H.execute_b(flow, part))
        flow.dest.set_evidence_state(flow.helpers.EVIDENCE, state='current')
        fresh = H.atomic_view(*H.execute_b(flow, part))
        again = H.atomic_view(*H.execute_b(flow, part))
        s = H.db_summary(flow.dest.path)
        checks.equal(stale['status'], 'denied', 'stale evidence refuses the claim')
        checks.equal(fresh['status'], 'executed', 'after the trusted refresh the same claim executes')
        checks.equal(again['status'], 'denied', 'the executed claim cannot execute twice')
        checks.equal(len(s['effects']), 1, 'exactly one effect')
        gate = H.effect_gate(s, authorized_effect_ids={part.env.effect_id})
        return {'stale': stale, 'after_refresh': fresh, 'again': again, 'effects': s['effects'], 'claims': s['claims'], 'budgets': s['budgets'], **gate}
    H.run_case(request, record_property, tmp_path, 'C17', trial)


STALE_PROVISIONING = {
    'revoked_grant': (lambda f, p: f.dest.set_grant_status(p.claim.grant_id, status='revoked'), 'existing authoritative grant state rejects claim provisioning'),
    'bumped_grant_revision': (lambda f, p: f.dest.set_grant_status(p.claim.grant_id, status='active', revision='2'), 'existing authoritative grant state rejects claim provisioning'),
    'withdrawn_approval': (lambda f, p: f.dest.set_approval_status(f.helpers.APPROVAL, status='revoked'), 'existing authoritative approval state rejects claim provisioning'),
    'changed_policy_version': (lambda f, p: f.dest.set_policy_state(f.helpers.POLICY_REF, version='2'), 'existing authoritative policy state rejects claim provisioning'),
    'stale_evidence': (lambda f, p: f.dest.set_evidence_state(f.helpers.EVIDENCE, state='stale'), 'existing authoritative evidence state rejects claim provisioning'),
}


@pytest.mark.parametrize('update', sorted(STALE_PROVISIONING))
def test_scn_c17_route_b_stale_provisioning_cannot_overwrite_or_revive_newer_state(request, record_property, tmp_path, update):
    """A stale agent re-issuing a claim built from the OLD versions must not overwrite the newer shared state (no lost update)
    and must not revive revoked/superseded authority (no expanded authority)."""
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        apply, needle = STALE_PROVISIONING[update]
        apply(flow, part)
        newer = C.authority_rows(flow.dest.path)
        env2 = flow.helpers.envelope(effect_no=2)
        stale_claim = flow.helpers.make_claim(env2, claim_id='claim-stale', budget_id='budget-main', max_effects=1)
        outcome = 'PROVISIONED'
        try:
            flow.dest.provision_claim(stale_claim)
        except Exception as exc:
            outcome = f'{type(exc).__name__}: {exc}'
        s = H.db_summary(flow.dest.path)
        checks.expect(needle in outcome, f'{update}: stale provisioning must be refused ({needle}); observed {outcome}')
        checks.equal(C.authority_rows(flow.dest.path), newer, f'{update}: the newer shared state is unchanged by the stale provisioning')
        checks.equal(C.claim_state(s, 'claim-stale'), None, f'{update}: the stale claim was not recorded')
        # and the original claim still cannot execute
        view = H.atomic_view(*H.execute_b(flow, part))
        checks.equal(view['status'], 'denied', f'{update}: the original claim remains refused')
        checks.equal(len(H.db_summary(flow.dest.path)['effects']), 0, f'{update}: no effect')
        return {'update': update, 'provisioning': outcome, 'authority_rows': newer, 'original_claim_attempt': view, 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'C17', trial)


def test_scn_c17_route_b_update_after_commit_preserves_history_and_blocks_more(request, record_property, tmp_path):
    """Ordering: execution first, other agent's update second. The committed effect is retained (history is not rewritten),
    and no further effect can follow the update."""
    def trial(work, mp, checks):
        flow = H.flow_b(work, effect_nos=(1, 2), budget_max=2)
        p1, p2 = flow.parts
        first = H.atomic_view(*H.execute_b(flow, p1))
        before = H.db_summary(flow.dest.path)
        flow.dest.set_grant_status(p1.claim.grant_id, status='revoked')
        second = H.atomic_view(*H.execute_b(flow, p2))
        s = H.db_summary(flow.dest.path)
        checks.equal(first['status'], 'executed', 'effect before the update executes')
        checks.equal(second['status'], 'denied', 'effect after the update is refused')
        checks.equal(s['effects'], before['effects'], 'the committed effect is unchanged by the later update')
        checks.equal(C.claim_state(s, 'claim-1'), 'consumed', 'consumed claim stays consumed')
        checks.equal(C.claim_state(s, 'claim-2'), 'issued', 'refused claim stays issued')
        gate = H.effect_gate(s, authorized_effect_ids={p1.env.effect_id})
        return {'first': first, 'second': second, 'effects': s['effects'], 'claims': s['claims'], 'budgets': s['budgets'], **gate}
    H.run_case(request, record_property, tmp_path, 'C17', trial)


def test_scn_c17_route_b_update_between_executor_checks_and_transaction_is_rejected(request, record_property, tmp_path):
    """Interleaving: another agent (separate handle) changes the policy version AFTER the executor has validated its inputs
    and BEFORE the write transaction begins (the reference's own deterministic stage hook). The version is re-read under the lock."""
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        other = _plain(flow)
        fired = []

        def hook(stage):
            if stage == 'before_begin' and not fired:
                fired.append(stage)
                other.set_policy_state(flow.helpers.POLICY_REF, version='2')
        flow.dest.stage_hook = hook
        view = H.atomic_view(*H.execute_b(flow, part))
        s = H.db_summary(flow.dest.path)
        checks.equal(fired, ['before_begin'], 'the interleaved update ran at the intended stage')
        checks.equal(view['status'], 'denied', 'the claim validated earlier is refused once the shared version changed')
        checks.expect('policy state invalid' in (view['error'] or ''), f'refusal names the changed policy: {view["error"]}')
        checks.equal(s['effects'], [], 'no effect')
        checks.equal(C.authority_rows(flow.dest.path)['authority_policies_v1'][0]['version'], '2', 'the other agent\'s update survives')
        return {'view': view, 'stage_trace': flow.dest.trace, 'policy_rows': C.authority_rows(flow.dest.path)['authority_policies_v1'], **H.effect_gate(s, authorized_effect_ids=set())}
    H.run_case(request, record_property, tmp_path, 'C17', trial)


def test_scn_c17_route_b_concurrent_update_during_commit_is_serialised_not_lost(request, record_property, tmp_path):
    """Interleaving: another agent's revocation is issued while the effect transaction holds the write lock. The store must
    serialise: the in-flight effect (authorised under the version it read) commits, the update is then applied (not lost), and
    nothing further can execute."""
    def trial(work, mp, checks):
        flow = H.flow_b(work, effect_nos=(1, 2), budget_max=2)
        p1, p2 = flow.parts
        other = _plain(flow)
        outcome = {}

        def writer():
            try:
                other.set_grant_status(p1.claim.grant_id, status='revoked')
                outcome['writer'] = 'applied'
            except Exception as exc:
                outcome['writer'] = f'{type(exc).__name__}: {exc}'
        threads = []

        def hook(stage):
            if stage == 'after_effect_insert_before_commit' and not threads:
                t = threading.Thread(target=writer)
                threads.append(t)
                t.start()
        flow.dest.stage_hook = hook
        first = H.atomic_view(*H.execute_b(flow, p1))
        for t in threads:
            t.join(30)
        flow.dest.stage_hook = None
        second = H.atomic_view(*H.execute_b(flow, p2))
        s = H.db_summary(flow.dest.path)
        grant_status = C.authority_rows(flow.dest.path)['authority_grants_v1'][0]['status']
        checks.equal(first['status'], 'executed', 'the in-flight effect, authorised under the version it read, commits')
        checks.equal(outcome.get('writer'), 'applied', f'the concurrent update is applied after the commit, not lost or errored: {outcome}')
        checks.equal(grant_status, 'revoked', 'final shared state reflects the other agent\'s update')
        checks.equal(second['status'], 'denied', 'nothing further executes after the update')
        checks.equal(len(s['effects']), 1, 'exactly one effect')
        gate = H.effect_gate(s, authorized_effect_ids={p1.env.effect_id})
        return {'first': first, 'writer': outcome.get('writer'), 'final_grant_status': grant_status, 'second': second, 'effects': s['effects'], 'claims': s['claims'], **gate}
    H.run_case(request, record_property, tmp_path, 'C17', trial)


# ------------------------------------------------------------------------------------------------
# route A: Control Plane revalidation + runtime executor + effective-grant destination
# ------------------------------------------------------------------------------------------------

def _res_grant_revision(f):
    next(iter(f.r.statuses.values())).revision = '2'


def _res_grant_revoked(f):
    H.revoke_resolver(f)


def _res_policy_version(f):
    f.r.policies[H.reference().POLICY_REF].version = '2'


def _res_approval_withdrawn(f):
    for a in f.r.approvals.values():
        a.status = 'revoked'


def _res_evidence_aged(f):
    for ev in f.r.evidence.values():
        ev.observed_at = (H.reference().chain.NOW - timedelta(minutes=30)).isoformat()


def _dest_revision(f):
    g = f.d.binding
    f.dest.set_effective_grant(principal=f.p.principal, grant_id=g.grant_id, revision='2', permissions=f.p.requested_permissions)


def _dest_permissions_narrowed(f):
    g = f.d.binding
    f.dest.set_effective_grant(principal=f.p.principal, grant_id=g.grant_id, revision=g.grant_revision, permissions=['refund.other'])


def _dest_revoked(f):
    H.revoke_destination(f)


A_UPDATES = {'resolver_grant_revision_changed': _res_grant_revision, 'resolver_grant_revoked': _res_grant_revoked, 'resolver_policy_version_changed': _res_policy_version,
             'resolver_approval_withdrawn': _res_approval_withdrawn, 'resolver_evidence_aged': _res_evidence_aged,
             'destination_effective_grant_revision_changed': _dest_revision, 'destination_effective_grant_permissions_narrowed': _dest_permissions_narrowed,
             'destination_effective_grant_revoked': _dest_revoked}


@pytest.mark.parametrize('update', sorted(A_UPDATES))
def test_scn_c17_route_a_stale_decision_is_rejected_and_cannot_be_refreshed_into_authority(request, record_property, tmp_path, update):
    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = H.flow_a(work, mp)
        A_UPDATES[update](flow)
        effective_before = effective_grant_rows(flow.dest.path)
        res, exc = H.execute_a(flow)
        view = H.result_view(res, exc)
        s = H.db_summary(flow.dest.path)
        refused = res is not None and res.status in ('denied', 'failed') and not newly(res)
        checks.expect(refused, f'{update}: the stale decision is refused; observed {view}')
        checks.equal(s['effects'], [], f'{update}: no effect from stale state')
        checks.equal(effective_grant_rows(flow.dest.path), effective_before, f'{update}: the stale attempt did not overwrite the destination authority row (no lost update)')
        # the same proposal presented for a FRESH decision must not become authorised by the stale one
        fresh = flow.f.decide(flow.p, now=ch.NOW)
        if update.startswith('resolver_'):
            checks.expect(fresh.result != 'authorized', f'{update}: a fresh decision reads the current state and does not authorise; observed {fresh.result} {fresh.reasons}')
        else:
            # destination-side drift is caught at commit; the Control Plane decision may still be authorised, but the destination refuses again
            res2, exc2 = H.execute_a(flow)
            checks.expect(res2 is not None and res2.status in ('denied', 'failed') and not newly(res2), f'{update}: re-presenting remains refused; observed {H.result_view(res2, exc2)}')
        s2 = H.db_summary(flow.dest.path)
        checks.equal(s2['effects'], [], f'{update}: still no effect after the second look')
        gate = H.effect_gate(s2, authorized_effect_ids=set())
        return {'update': update, 'result': view, 'fresh_decision': {'result': fresh.result, 'reasons': sorted(fresh.reasons)}, 'journal': H.journal_view(flow),
                'destination_failures': [f'{c}/{r}/{st}' for c, r, st, _d in s2['failures']], 'effective_grant_after': effective_before, **gate}
    H.run_case(request, record_property, tmp_path, 'C17', trial)


def newly(res):
    return bool(res.newly_executed)


def test_scn_c17_route_a_update_between_executor_validation_and_commit_is_rejected(request, record_property, tmp_path):
    """Interleaving: another agent widens the effective grant (revision 2 plus an admin permission) after the executor validated
    and immediately before the destination commit (the reference's own race instrumentation). The commit re-reads under its lock."""
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        g = flow.d.binding
        original = flow.dest.commit
        fired = []

        def race(snapshot, **kwargs):
            fired.append(True)
            flow.dest.set_effective_grant(principal=flow.p.principal, grant_id=g.grant_id, revision='2', permissions=flow.p.requested_permissions + ['admin'])
            return original(snapshot, **kwargs)
        flow.dest.commit = race
        res, exc = H.execute_a(flow)
        view = H.result_view(res, exc)
        s = H.db_summary(flow.dest.path)
        checks.equal(fired, [True], 'the interleaved update ran immediately before the commit')
        checks.expect(res is not None and res.status in ('denied', 'failed') and not res.newly_executed, f'the commit is refused after the interleaved update; observed {view}')
        checks.equal(s['effects'], [], 'no effect')
        rows = effective_grant_rows(flow.dest.path)
        checks.equal(len(rows), 1, 'the other agent\'s effective-grant row survives')
        return {'result': view, 'effective_grant_status': [r['status'] for r in rows], 'destination_failures': [f'{c}/{r}/{st}' for c, r, st, _d in s['failures']], **H.effect_gate(s, authorized_effect_ids=set())}
    H.run_case(request, record_property, tmp_path, 'C17', trial)


@pytest.mark.parametrize('update', ['grant-revision-changed', 'policy-version-changed'])
def test_scn_c17_route_c_exchange_with_stale_authority_state_is_refused(request, record_property, tmp_path, update):
    def trial(work, mp, checks):
        flow = H.flow_c(work, mp)
        if update == 'grant-revision-changed':
            next(iter(flow.r.statuses.values())).revision = '2'
        else:
            flow.r.policies[H.reference().POLICY_REF].version = '2'
        res = H.exchange_run(flow)
        view = H.exchange_view(res)
        s = H.db_summary(flow.dest.path)
        checks.equal(view['attempted'], False, 'the exchange dispatches nothing on stale authority state')
        checks.expect(view['attempt_status'] in ('hold', 'denied', None) or view['authority_stage'] in ('hold', 'denied'), f'refusal/hold is observable: {view}')
        checks.equal(s['effects'], [], 'no effect')
        return {'update': update, 'view': view, **H.effect_gate(s, authorized_effect_ids=set())}
    H.run_case(request, record_property, tmp_path, 'C17', trial)


def test_scn_c17_unsupported_concurrency_is_reported(request, record_property, tmp_path):
    """REPORT: probe the concurrency capabilities the catalog implies and record which are not supported. Nothing is inferred.

    Changed after the runtime made a revoked grant revision final (runtime 11de097c): the stale-writer probe used to observe that a
    writer holding a stale view could set a revoked grant back to active at the same revision. It now asserts the stricter
    outcome: that write is refused (PermissionError) and the grant stays revoked. The probe id is unchanged; the missing
    compare-and-set on the authority writers (and the other three probes) are reported as before."""
    import inspect

    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        cls = type(flow.dest).__bases__[0]
        writers = ['set_grant_status', 'set_approval_status', 'set_policy_state', 'set_evidence_state', 'remove_authoritative_state']
        cas_params = {w: [p for p in inspect.signature(getattr(cls, w)).parameters if any(k in p for k in ('expected', 'if_version', 'if_revision', 'etag', 'cas'))] for w in writers}
        # observation: authority writers are unconditional (last writer wins); a stale writer can silently revert a newer update
        flow.dest.set_grant_status(part.claim.grant_id, status='revoked')                 # agent A revokes
        try:
            flow.dest.set_grant_status(part.claim.grant_id, status='active', revision='1')    # agent B, holding a stale view, writes back 'active'
            stale_write = 'accepted'
        except PermissionError:
            stale_write = 'refused'
        checks.equal(stale_write, 'refused', 'a revoked grant revision is final: the stale write back to active is refused')
        reverted = C.authority_rows(flow.dest.path)['authority_grants_v1'][0]['status']
        # a claim can only be reconciled by exact original recovery, never against a changed version
        recon_api = [n for n in dir(cls) if 'reconcile' in n.lower()]
        probes = {
            'compare_and_set_on_authority_writers': {'supported': any(cas_params.values()), 'version_parameters_found': cas_params},
            'stale_writer_cannot_revert_newer_update': {'supported': reverted != 'active',
                                                       'observed': f'after agent A revoked and a stale agent B wrote status=active, that write was {stale_write} and the grant status is {reverted!r}: a revoked revision is final on the trusted authority writer'},
            'reconcile_or_merge_of_stale_claim': {'supported': False, 'public_reconcile_methods': recon_api,
                                                  'observed': 'only exact-original effect recovery (reconcile_claim); no merge/rebase of a stale claim onto a newer version'},
            'general_multi_agent_shared_state_versioning': {'supported': False, 'observed': 'no shared-document or generic versioned-state object exists in the reference; shared state is the fixed authority tables'},
        }
        checks.expect(recon_api == ['reconcile_claim'], f'only exact-original recovery exists: {recon_api}')
        return {'probes': probes, 'unsupported': sorted(k for k, v in probes.items() if not v['supported'])}
    payload = H.run_case(request, record_property, tmp_path, 'C17', trial, expect_effects_gate=False)
    C.write_report(request, record_property, 'unsupported_concurrency', {'scenario': 'C17', 'unsupported': payload['run1']['observed']['unsupported'],
                                                                         'probes': payload['run1']['observed']['probes']})
