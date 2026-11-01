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

Route-B round trip (P4 of the decoupling plan, cognous-control-plane#38; verifies F-24, F-25 and F-28). The cases of
``test_scn_c06_route_b_round_trip`` take a REAL route-B export (``AtomicLocalControlPlaneExecutor`` over the atomic
claim destination, the real Control Plane journal and decision of the integrated flow) through the whole downstream
chain: ``export_execution_artifacts`` -> Replay ``import_bounded_workflow`` -> evidence pack
``import_manifest_reconstruction`` (which re-runs Replay's validator over the retained records) -> pack validation.
Four cases: a normal executed effect, the post-commit observation read failing (recovery status applied), a lost
acknowledgement with reconciliation down (recovery status unknown), and an effect-free reconcile of a consumed claim.
Each case also plants a defect into the retained bundle and requires the pack re-validation to refuse it, so a pass
cannot come from a validator that never ran. Replay step B negative controls on the real export: observation {} and a recovery
report mirrored in ``observations`` (the retired legacy layout) are refused with schema_violation.
"""
from __future__ import annotations

import dataclasses
import json
from datetime import timedelta

import pytest

import _c_2a_helpers as C
import _d02_d05_d09_helpers as H
from _reason_norm import exc_summary  # noqa: E402
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
            down_resume = {'raised': exc_summary(exc)}
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


# ------------------------------------------------------------------------------------------------
# route B round trip: real route-B export -> Replay import -> evidence pack re-validation
# ------------------------------------------------------------------------------------------------

ROUTE_B_VARIANTS = ['executed', 'observe_bound_fail', 'lost_ack_recon_down', 'reconcile_only']


def _route_b_flow(work, mp, variant):
    """Real route-B execution of the exact envelope the real Control Plane decided (route A is built only for its journal)."""
    ref = H.reference()
    (work / 'a').mkdir()
    (work / 'b').mkdir()
    fa = H.flow_a(work / 'a', mp)
    h = ref.atomic
    from engine.local_authority_effect import AtomicLocalControlPlaneExecutor
    dest = H.hooked_atomic_class()(work / 'b', clock=h.MutableClock(h.BASE))
    dest.trace = []
    dest.provision_claim(h.make_claim(fa.env, claim_id='claim-1', budget_id='budget-main', max_effects=1))
    executor = AtomicLocalControlPlaneExecutor(workflow=object(), destination=dest, policy=fa.executor.policy)
    state, simulate = {'down': False}, None
    if variant in ('observe_bound_fail', 'lost_ack_recon_down'):
        dest.stage_hook = lambda stage: state.__setitem__('down', True) if stage == 'after_commit' else None
    if variant == 'observe_bound_fail':
        original = dest.observe_bound

        def observe_bound(snapshot):
            if state['down']:
                raise ConnectionError('authoritative observer unavailable')
            return original(snapshot)
        dest.observe_bound = observe_bound
    elif variant == 'lost_ack_recon_down':
        original_reconcile = dest.reconcile_claim

        def reconcile_claim(claim_id, snapshot):
            if state['down']:
                raise ConnectionError('authoritative observer unavailable')
            return original_reconcile(claim_id, snapshot)
        dest.reconcile_claim = reconcile_claim
        simulate = 'lost_ack'
    if variant == 'reconcile_only':
        executor.execute(envelope=fa.env, claim_id='claim-1')
        res = executor.reconcile(claim_id='claim-1', envelope=fa.env)
    else:
        res = executor.execute(envelope=fa.env, claim_id='claim-1', simulate=simulate)
    return fa, dest, res


@pytest.mark.parametrize('variant', ROUTE_B_VARIANTS)
def test_scn_c06_route_b_round_trip(request, record_property, tmp_path, variant):
    def trial(work, mp, checks):
        ref = H.reference()
        ch = ref.chain
        fa, dest, res = _route_b_flow(work, mp, variant)
        summary = H.db_summary(dest.path)
        checks.equal(len(summary['effects']), 1, 'the oracle shows exactly one committed effect')
        # 1. the real route-B export
        export = ch.export_execution_artifacts(fa.env, res, dest, repository_revision=ch.MOLTBOT_RUNTIME_AUTHORITY_REVISION)
        report = res.observation if isinstance(res.observation, dict) and res.observation and 'state' not in res.observation else None
        checks.expect(all('state' in row for row in export['observations']),
                      'export layout: observations carry validated observations only (rows with a state)')
        checks.equal(export.get('recovery_observations', []), [report] if report else [],
                     'export layout: recovery_observations carries the destination recovery report, and only that')
        if variant == 'executed':
            checks.equal((res.status, res.attempted, res.acknowledged, res.newly_executed), ('executed', True, True, True), 'normal route-B execution reports executed')
        elif variant == 'reconcile_only':
            checks.equal((res.status, res.attempted, res.newly_executed), ('observed', False, False), 'effect-free reconcile reports observed and claims no attempt')
        else:
            checks.equal((res.status, res.attempted, res.acknowledged), ('unknown', True, False), 'a post-commit failure is reported unresolved, not denied')
            checks.expect(report is not None and report.get('retry_eligible') is False, 'the recovery report is typed and never makes the effect retry-eligible')
            checks.equal(report.get('status') if report else None, 'applied' if variant == 'observe_bound_fail' else 'unknown',
                         'recovery report status follows what the reconciliation could establish')
        # 2. Replay import of the real export together with the real Control Plane journal
        raw = fa.f.records.load().model_dump(mode='json')
        proposal = fa.p.model_dump(mode='json')
        bundle = ref_import(raw, proposal, export)
        dump = bundle.model_dump(mode='json')
        record_types = sorted({r['record_type'] for r in dump['records']})
        checks.equal(dump['status'], 'reconstruction_complete', 'Replay reconstructs the bundle completely')
        checks.expect(all(r['complete'] for r in dump['import_reports']), 'every Replay import report is complete')
        checks.equal('executor_recovery_report' in record_types, report is not None, 'a recovery report is retained as a report record, only when the result carries one')
        # 3. evidence pack: re-validation of the retained bundle (re-runs Replay's validator over the retained records)
        from agent_governance_evidence_pack import import_manifest_reconstruction, validate_evidence_pack
        from agent_governance_evidence_pack.importer import ImportContractError as PackRefusal
        pack = import_manifest_reconstruction(fa.f.manifest, dump)
        validation = pack.metadata['traceable_import']['replay_semantic_validation']
        checks.equal(validation.get('status'), 'validated_complete', 'the evidence pack re-validates the retained bundle with Replay')
        checks.expect(validate_evidence_pack(pack).valid, 'the evidence pack validates')
        # 4. non-vacuity: a planted defect in the retained bundle is refused by the same re-validation
        tampered = json.loads(json.dumps(dump))
        target = next(r for r in tampered['records'] if r['record_type'] == ('executor_recovery_report' if report else 'execution_result'))
        if report:
            target['data']['status'] = 'hold' if target['data']['status'] != 'hold' else 'applied'
        else:
            target['data']['observed_state'] = 'partial' if target['data'].get('observed_state') != 'partial' else 'applied'
        try:
            import_manifest_reconstruction(fa.f.manifest, tampered)
            refused = False
        except PackRefusal:
            refused = True
        checks.expect(refused, 'a planted change to a retained record is refused by the pack re-validation')
        # 5. step-B negative controls on the real export: the retired shapes are refused with the contract code
        from agent_replay_bundle.importers import ImportContractError as ReplayRefusal
        retired = {'empty_observation_object': lambda x: x['execution_result'].__setitem__('observation', {})}
        if report:
            def legacy_layout(x):
                x.pop('recovery_observations', None)
                x['observations'] = [json.loads(json.dumps(report))]
            retired['legacy_layout_report_in_observations'] = legacy_layout
        refusals = {}
        for name, mutate in retired.items():
            probe = json.loads(json.dumps(export, default=str))
            mutate(probe)
            try:
                ref_import(raw, proposal, probe)
                refusals[name] = None
            except ReplayRefusal as exc:
                refusals[name] = exc.code
        checks.equal(refusals, {name: 'schema_violation' for name in retired}, 'Replay refuses the retired export shapes with schema_violation')
        gate = H.effect_gate(summary, authorized_effect_ids={fa.env.effect_id})
        return {'variant': variant, 'result': H.atomic_view(res), 'recovery_report_status': report.get('status') if report else None,
                'export_layout': {'observations': len(export['observations']), 'recovery_observations': len(export.get('recovery_observations', []))},
                'replay_status': dump['status'], 'replay_record_types': record_types, 'pack_replay_validation': validation.get('status'),
                'pack_valid': True, 'tamper_refused': refused, 'retired_shapes_refused': refusals, 'contract_matrix': {r['boundary']: r['status'] for r in ref.matrix_rows},
                'oracle_effects': len(summary['effects']), **gate}
    H.run_case(request, record_property, tmp_path, 'C06', trial)


def ref_import(raw, proposal, export):
    """Replay's public bounded-workflow import at the generation the profile pins (revision constants come from Replay itself)."""
    ch = H.reference().chain
    from agent_replay_bundle.importers import import_bounded_workflow
    return import_bounded_workflow(raw, proposal=proposal, moltbot_export=export,
                                   control_plane_revision=ch.CONTROL_PLANE_RUNTIME_AUTHORITY_REVISION)
