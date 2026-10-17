"""Catalog scenario C08 - Crash and restart (executed against the frozen F5b bounded reference).

SPDX-License-Identifier: Apache-2.0

Stimulus (catalog): crash at precommit, postcommit and prerecord checkpoints as separate variants; restart. Required
observation: reconcile authoritative state and stable effect identity; no unsupported completion or duplicate.

Checkpoint definitions used (each its own variant, per route, at the reference's real seams):
  precommit   the destination write transaction is open (or about to open) and has NOT committed;
  postcommit  the destination transaction has COMMITTED but the caller never saw the acknowledgement;
  prerecord   the effect is committed and acknowledged inside the executor but the NEXT durable record that would
              retain the outcome (Control Plane attempt update on route A; dispatch-checkpoint result on route C;
              the typed failure record on route B) is not written.
  (route C additionally: postrecord = the reference's own ``fault_after_dispatch`` seam, after the checkpoint result.)
How the process "dies":
  route B  a REAL child process is killed with ``os._exit(77)`` at the seam (``_c_2a_child.py``); the parent restarts by
           re-opening the SQLite file in a new executor (nothing in memory survives).
  route A/C  a ``BaseException`` (``CrashSignal``) is raised at the seam, which no ``except Exception`` in the reference
           can absorb, and every in-memory object of the crashed run (destination handle, executor) is discarded; the
           restart re-opens the durable files with new objects. This is a crash model at the Python level, not an
           operating-system kill and NOT a power-loss claim.
Every case runs twice from fresh stores and the normalised observations are compared (owner decision D3). Hard gates
(D5): zero unauthorized effects and zero excess duplicate effects. A genuine violation FAILS.
"""
from __future__ import annotations

import pytest

import _c_2a_helpers as C
import _d02_d05_d09_helpers as H
from _c_2a_helpers import CrashSignal, no_network, pinned_reference  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures('pinned_reference')


def test_scn_c08_source_identity_containment_and_initial_state(request, record_property, tmp_path):
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
        checks.equal(b['claims'], [('claim-1', 'issued')], 'route B claim starts issued')
        return {'initial_state_digest': H.digest({'a': a, 'b': b}), 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'C08', trial)


# ------------------------------------------------------------------------------------------------
# route A: Control Plane + runtime executor + effective-grant destination
# ------------------------------------------------------------------------------------------------

def _restart_a(flow):
    """New process: re-open the durable destination file with new objects; the Control Plane journal is its own file."""
    ch = H.reference().chain
    dest = ch.EffectiveGrantDestination(flow.work / 'sqlite')
    executor = ch.PinnedControlPlaneExecutor(workflow=flow.f, destination=dest, policy=flow.executor.policy, observation_clock=lambda: ch.NOW)
    return dest, executor


@pytest.mark.parametrize('checkpoint', ['precommit', 'postcommit', 'prerecord'])
def test_scn_c08_route_a_crash_then_restart_reconciles_without_duplicate(request, record_property, tmp_path, checkpoint):
    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = H.flow_a(work, mp)
        effect_id = flow.env.effect_id
        crashed_at = []
        if checkpoint == 'precommit':
            def hook(conn, snapshot):
                crashed_at.append('inside_open_write_transaction_before_effect_insert')
                raise CrashSignal('precommit')
            flow.dest._check_commit_profile = hook
        elif checkpoint == 'postcommit':
            original = flow.dest.commit

            def commit_then_die(snapshot, **kwargs):
                original(snapshot, **kwargs)
                crashed_at.append('after_durable_commit_before_acknowledgement')
                raise CrashSignal('postcommit')
            flow.dest.commit = commit_then_die
        else:
            records = flow.f.records
            calls = []
            original_append = records.append_attempt

            def append_then_die(value):
                calls.append(value.status)
                if len(calls) == 2:
                    crashed_at.append('after_acknowledged_commit_before_control_plane_attempt_update')
                    raise CrashSignal('prerecord')
                return original_append(value)
            records.append_attempt = append_then_die
        crashed = False
        try:
            H.execute_a(flow)
        except CrashSignal:
            crashed = True
        checks.equal(crashed, True, f'the {checkpoint} seam fired (the crash was delivered)')
        if checkpoint == 'prerecord':
            del flow.f.records.__dict__['append_attempt']
        at_crash = H.db_summary(flow.dest.path)
        cp_at_crash = flow.f.records.load()
        expected_rows = 0 if checkpoint == 'precommit' else 1
        checks.equal(len(at_crash['effects']), expected_rows, f'oracle at the crash: {expected_rows} durable effect(s)')
        # ---- restart: nothing in memory survives
        dest2, executor2 = _restart_a(flow)
        flow.dest, flow.executor = dest2, executor2
        rec = executor2.reconcile(flow.env, now=ch.NOW)
        rec_view = C.reconciliation_view(rec)
        res, exc = H.execute_a(flow)
        retry = H.result_view(res, exc)
        final = H.db_summary(dest2.path)
        if checkpoint == 'precommit':
            checks.equal(rec_view['result'], 'observed_absent', 'restart reconciliation observes the absence of the effect')
            checks.equal(rec_view['retry_eligible'], False, 'absence never makes the effect retry-eligible')
            checks.equal((retry.get('status'), retry.get('newly_executed')), ('denied', False), 'no blind retry after an unresolved prior attempt')
            checks.equal(final['effects'], [], 'no effect is invented or duplicated')
        else:
            checks.equal((rec_view['result'], rec_view['observation_accepted'], rec_view['retry_eligible']), ('applied', True, False), 'restart reconciliation establishes the committed effect')
            checks.equal((retry.get('status'), retry.get('newly_executed')), ('reconciled', False), 're-execution reconciles the existing effect, executing nothing new')
            checks.equal(final['effects'], at_crash['effects'], 'effect rows byte-identical across the restart (stable identity, no duplicate)')
            checks.equal(final['effects'][0]['effect_id'], effect_id, 'effect identity is the original one')
            checks.equal(final['effects'][0]['state'], 'applied', 'the committed effect is applied')
        cp_final = C.cp_attempt_summary(flow)
        gate = H.effect_gate(final, authorized_effect_ids={effect_id}, authorized_digests={H.snapshot_digest(flow.env)})
        return {'checkpoint': checkpoint, 'crash_seam': crashed_at, 'at_crash': {'effects': at_crash['effects'], 'local_attempts': [a['events'] for a in at_crash['attempts']],
                                                                              'cp_attempts': [a.status for a in cp_at_crash.attempts]},
                'restart_reconcile': rec_view, 'restart_re_execution': retry, 'effects': final['effects'], 'local_attempts': [a['events'] for a in final['attempts']],
                'cp_attempts_final': cp_final, 'trajectory_after': H.trajectory_a(flow, flow.env, res) if res is not None else {}, **gate}
    H.run_case(request, record_property, tmp_path, 'C08', trial)


# ------------------------------------------------------------------------------------------------
# route B: real process kill
# ------------------------------------------------------------------------------------------------

B_SEAMS = {
    'precommit-after-begin': ('after_begin', None),
    'precommit-after-effect-insert': ('after_effect_insert_before_commit', None),
    'postcommit': ('after_commit', None),
    'prerecord-failure-record-lost': ('before_failure_record', 'lost_ack'),
}


@pytest.mark.parametrize('checkpoint', sorted(B_SEAMS))
def test_scn_c08_route_b_real_process_kill_then_restart_reconciles_without_duplicate(request, record_property, tmp_path, checkpoint):
    seam, simulate = B_SEAMS[checkpoint]

    def trial(work, mp, checks):
        H.flow_b(work)  # creates and provisions the atomic-claim destination, then the objects are dropped
        code, output = C.run_child_that_dies(work, seam, simulate=simulate)
        checks.equal(code, 77, f'the child process was killed (os._exit) at seam {seam}: {output!r}')
        restarted = C.reopen_b(work)
        part = restarted.parts[0]
        at_crash = H.db_summary(restarted.dest.path)
        committed = checkpoint in ('postcommit', 'prerecord-failure-record-lost')
        checks.equal(len(at_crash['effects']), 1 if committed else 0, f'oracle after the kill: {"committed" if committed else "rolled back"}')
        checks.equal(at_crash['claims'], [('claim-1', 'consumed' if committed else 'issued')], 'claim state after the kill')
        checks.equal(at_crash['attempts'] if not committed else len(at_crash['attempts']), [] if not committed else 1, 'attempt rows after the kill (rolled back with the transaction, or committed with it)')
        reconciled = restarted.dest.reconcile_claim(part.claim.claim_id, H.snapshot_env(part.env))
        rec_view = {k: reconciled.get(k) for k in ('status', 'retry_eligible', 'claim_state', 'reason')}
        res, exc = H.execute_b(restarted, part)
        again = H.atomic_view(res, exc)
        final = H.db_summary(restarted.dest.path)
        receipt_attempts = [a for a in C.attempt_rows(restarted.dest.path)]
        if committed:
            checks.equal((rec_view['status'], rec_view['retry_eligible']), ('applied', False), 'restart reconciliation establishes the committed effect')
            checks.equal((again.get('status'), again.get('newly_executed')), ('denied', False), 're-presenting the consumed claim executes nothing')
            checks.equal(final['effects'], at_crash['effects'], 'effect rows byte-identical across the restart')
            checks.equal(final['claims'], [('claim-1', 'consumed')], 'claim stays consumed')
            checks.equal(len(receipt_attempts), 1, 'exactly one attempt record links the effect')
            checks.equal(restarted.dest.authority_receipt(receipt_attempts[0]['attempt_id']) is not None, True, 'the atomic commit receipt was retained')
            if checkpoint == 'prerecord-failure-record-lost':
                checks.equal(at_crash['failures'], [], 'documented loss: at the kill the typed acknowledgement-unavailable failure record was never written (authoritative attempt events and receipt remain)')
        else:
            checks.equal((rec_view['status'], rec_view['retry_eligible']), ('hold', False), 'restart reconciliation reports no durable effect and no retry eligibility by itself')
            checks.equal(rec_view['reason'], 'no_durable_effect_for_claim', 'reconciliation names the absence')
            checks.equal(again.get('status'), 'executed', 'the still-issued claim delivers the effect exactly once after restart')
            checks.equal(len(final['effects']), 1, 'exactly one effect after restart')
            checks.equal(final['effects'][0]['effect_id'], part.env.effect_id, 'effect identity is the original one')
            checks.equal(final['claims'], [('claim-1', 'consumed')], 'claim consumed by the single delivery')
        gate = H.effect_gate(final, authorized_effect_ids={part.env.effect_id})
        return {'checkpoint': checkpoint, 'seam': seam, 'killed': code == 77, 'at_kill': {'effects': at_crash['effects'], 'claims': at_crash['claims'], 'attempts': at_crash['attempts']},
                'restart_reconcile': rec_view, 're_execution': again, 'effects': final['effects'], 'claims': final['claims'], 'budgets': final['budgets'],
                'failure_records': final['failures'], 'attempt_summary': C.attempt_summary(restarted.dest.path)['attempts'], **gate}
    H.run_case(request, record_property, tmp_path, 'C08', trial)


# ------------------------------------------------------------------------------------------------
# route C: governed exchange
# ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize('checkpoint', ['precommit', 'postcommit', 'prerecord', 'postrecord'])
def test_scn_c08_route_c_exchange_crash_then_restart_never_redispatches(request, record_property, tmp_path, checkpoint):
    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = H.flow_c(work, mp)
        effect_id = flow.d.effect_id
        seam = []
        extra = {}
        if checkpoint == 'precommit':
            def commit_dies(snapshot, **kwargs):
                seam.append('before_destination_transaction')
                raise CrashSignal('precommit')
            flow.dest.commit = commit_dies
        elif checkpoint == 'postcommit':
            original = flow.dest.commit

            def commit_then_die(snapshot, **kwargs):
                original(snapshot, **kwargs)
                seam.append('after_durable_commit_before_acknowledgement')
                raise CrashSignal('postcommit')
            flow.dest.commit = commit_then_die
        elif checkpoint == 'prerecord':
            store_cls = flow.gax.TransactionalExchangeStore
            original_record = store_cls.record_dispatch_checkpoint
            calls = []

            def record_then_die(self, message, payload):
                calls.append(payload.get('status'))
                if len(calls) == 2:
                    seam.append('after_executor_returned_before_dispatch_checkpoint_result')
                    raise CrashSignal('prerecord')
                return original_record(self, message, payload)
            mp.setattr(store_cls, 'record_dispatch_checkpoint', record_then_die)
        else:
            extra['fault_after_dispatch'] = True
            seam.append('reference_fault_after_dispatch_after_checkpoint_result')
        crashed = False
        first = None
        try:
            first = H.exchange_run(flow, **extra)
        except CrashSignal:
            crashed = True
        if checkpoint != 'postrecord':
            checks.equal(crashed, True, f'the {checkpoint} seam fired (the crash was delivered)')
        else:
            checks.equal((crashed, first['execution'].get('attempt_status')), (False, 'interrupted_after_dispatch'), 'the reference fault seam fired')
        at_crash = H.db_summary(flow.dest.path)
        expected_rows = 0 if checkpoint == 'precommit' else 1
        checks.equal(len(at_crash['effects']), expected_rows, f'oracle at the crash: {expected_rows} durable effect(s)')
        # ---- restart: new destination handle, same durable files; the message is delivered again
        if checkpoint == 'prerecord':
            mp.setattr(store_cls, 'record_dispatch_checkpoint', original_record)  # the crashed process is gone
        dest2 = ch.EffectiveGrantDestination(work / 'target' / 'sqlite')
        flow.dest = dest2
        flow.kwargs = dict(flow.kwargs)
        redelivery = H.exchange_run(flow, **{})
        v = H.exchange_view(redelivery)
        redelivery_view = {**v, 'reason': redelivery['execution'].get('reason')}
        after_redelivery = H.db_summary(dest2.path)
        resume = None
        try:
            r = H.exchange_resume(flow)
            resume = {'returned': H.exchange_view(r)}
        except Exception as exc:
            resume = {'raised': f'{type(exc).__name__}: {str(exc)[:160]}'}
        final = H.db_summary(dest2.path)
        checks.equal((v['attempted'], bool(v['newly_executed'])), (False, False), 'redelivery after the crash dispatches nothing')
        checks.equal(final['effects'], at_crash['effects'], 'effect rows byte-identical across the restart and every recovery attempt (no duplicate)')
        if expected_rows:
            checks.equal(final['effects'][0]['effect_id'], effect_id, 'effect identity is the original one')
        checks.expect(redelivery_view['attempt_status'] != 'executed', f'redelivery never reports a fresh execution; observed {redelivery_view}')
        if checkpoint == 'postrecord':
            checks.equal((v['attempt_status'], v['destination_observed']), ('reconciled', 'applied'), 'with the checkpoint result retained the redelivery reconciles the committed effect')
        else:
            checks.equal(redelivery_view['attempt_status'], 'hold', 'without a retained dispatch result the exchange holds rather than guess')
        gate = H.effect_gate(final, authorized_effect_ids={effect_id})
        return {'checkpoint': checkpoint, 'crash_seam': seam, 'at_crash_effects': at_crash['effects'], 'at_crash_local_attempts': [a['events'] for a in at_crash['attempts']],
                'redelivery': redelivery_view, 'resume_original_exchange': resume, 'effects': final['effects'],
                'recovery_note': 'hold = fail-closed: the reference exposes no automatic reconciliation of an exchange whose dispatch checkpoint lacks the executor result' if checkpoint != 'postrecord' else None,
                **gate}
    H.run_case(request, record_property, tmp_path, 'C08', trial)
