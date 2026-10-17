"""ASW core-12, family R (monitoring/response, wiki layer L17): R01 lost executor acknowledgement, R02 crash after
destination commit.

SPDX-License-Identifier: Apache-2.0

Crash model (stated plainly): route B uses a REAL child process killed with os._exit(77) at a named seam of the reference's
own transaction hook; routes A and C raise a BaseException (``CrashSignal``) at the seam and discard every in-memory
object, restarting from the durable files. This is not an operating-system or power-loss durability claim.

Executed against the frozen F5b-repaired seven-component bounded synthetic reference (see ``_asw_helpers``); every test
runs twice from fresh stores and the hard gate applies to every run. A genuine violation FAILS; nothing is loosened.
"""
from __future__ import annotations

import pytest

import _asw_helpers as A
import _d02_d05_d09_helpers as H
from _asw_helpers import C, no_network, pinned_reference  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures('pinned_reference')


def restart_a(flow):
    """New process: re-open the durable destination with new objects (the Control Plane journal is its own file)."""
    ch = H.reference().chain
    dest = ch.EffectiveGrantDestination(flow.work / 'sqlite')
    executor = ch.PinnedControlPlaneExecutor(workflow=flow.f, destination=dest, policy=flow.executor.policy, observation_clock=lambda: ch.NOW)
    return dest, executor


def unknown_recorded(cp):
    return any('unknown' in statuses for statuses in cp['per_attempt_statuses'])


# =====================================================================================================
# R01  Lost executor acknowledgement: retain unknown delivery; reconcile before retry
# =====================================================================================================

def test_asw_r01_positive_control_acknowledged_delivery_is_not_unknown(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        res, exc = H.execute_a(flow)
        v = A.view_a(res, exc)
        checks.equal((v.get('status'), v.get('acknowledged')), ('executed', True), 'an acknowledged delivery is reported executed, not unknown')
        s = H.db_summary(flow.dest.path)
        A.one_effect_expected(checks, s, 'acknowledged delivery')
        return {'result': v, 'effects': s['effects'], **A.gate_for(s, {flow.env.effect_id})}
    A.run(request, record_property, tmp_path, 'R01', trial)


def test_asw_r01_route_a_lost_ack_is_retained_unknown_and_reconciled_before_any_retry(request, record_property, tmp_path):
    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = H.flow_a(work, mp)
        commits = H.count_commits(flow.dest)
        first, e1 = H.execute_a(flow, simulate='lost_ack')
        v1 = A.view_a(first, e1)
        checks.equal((v1.get('status'), v1.get('acknowledged')), ('unknown', False), 'a lost acknowledgement is reported unknown, never success')
        checks.equal(v1.get('newly_executed'), False, 'the caller is not told the effect was newly executed')
        cp1 = C.cp_attempt_summary(flow)
        checks.expect(unknown_recorded(cp1), f'the Control Plane retains the unknown attempt state; observed {cp1["per_attempt_statuses"]}')
        s1 = H.db_summary(flow.dest.path)
        checks.equal(len(s1['effects']), 1, 'the effect did commit although the acknowledgement was lost (absence is not inferred from a missing ack)')
        rec = flow.executor.reconcile(flow.env, now=ch.NOW)
        rv = C.reconciliation_view(rec)
        checks.equal((rv['result'], rv['observation_accepted'], rv['retry_eligible']), ('applied', True, False), 'reconciliation observes the committed effect and grants no retry eligibility')
        res, exc = H.execute_a(flow)
        v2 = A.view_a(res, exc)
        checks.equal((v2.get('status'), v2.get('newly_executed')), ('reconciled', False), 'the retry reconciles the committed effect and executes nothing new')
        final = H.db_summary(flow.dest.path)
        checks.equal(final['effects'], s1['effects'], 'effect rows byte-identical after reconcile and retry')
        checks.equal(commits['new_durable'], 1, 'exactly one durable commit')
        return {'first': v1, 'cp_attempts': {k: v for k, v in cp1.items() if k != 'attempt_ids'}, 'reconcile': rv, 'retry': v2, 'effects': final['effects'],
                **A.gate_for(final, {flow.env.effect_id})}
    A.run(request, record_property, tmp_path, 'R01', trial)


def test_asw_r01_route_a_unknown_delivery_without_durable_effect_is_not_inferred_as_no_effect(request, record_property, tmp_path):
    """No acknowledgement AND no committed effect (process dies inside the open write transaction). The absence observed at
    restart does not make a blind retry eligible: the unresolved attempt must be reconciled first."""
    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = H.flow_a(work, mp)

        def hook(conn, snapshot):
            raise C.CrashSignal('inside-open-transaction')
        flow.dest._check_commit_profile = hook
        crashed = False
        try:
            H.execute_a(flow)
        except C.CrashSignal:
            crashed = True
        checks.equal(crashed, True, 'the crash was delivered inside the open write transaction')
        at_crash = H.db_summary(flow.dest.path)
        checks.equal(at_crash['effects'], [], 'nothing committed')
        dest2, executor2 = restart_a(flow)
        flow.dest, flow.executor = dest2, executor2
        rec = executor2.reconcile(flow.env, now=ch.NOW)
        rv = C.reconciliation_view(rec)
        checks.equal((rv['result'], rv['retry_eligible']), ('observed_absent', False), 'absence is observed but retry is NOT thereby eligible')
        res, exc = H.execute_a(flow)
        v = A.view_a(res, exc)
        checks.equal((v.get('status'), v.get('newly_executed')), ('denied', False), 'no blind retry after an unresolved prior attempt')
        final = H.db_summary(dest2.path)
        checks.equal(final['effects'], [], 'no effect is invented')
        return {'reconcile': rv, 'retry': v, **A.gate_for(final)}
    A.run(request, record_property, tmp_path, 'R01', trial)


def test_asw_r01_route_b_lost_ack_keeps_the_claim_consumed_and_retry_is_refused(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        first, e1 = H.execute_b(flow, part, simulate='lost_ack')
        v1 = A.view_b(first, e1)
        checks.equal((v1.get('status'), v1.get('acknowledged')), ('unknown', False), 'a lost acknowledgement is reported unknown, never success')
        s1 = H.db_summary(flow.dest.path)
        checks.equal((len(s1['effects']), s1['claims']), (1, [('claim-1', 'consumed')]), 'the effect committed and the claim is consumed')
        checks.expect(bool(s1['failures']),
                      f'the unknown delivery is retained as a typed failure record; observed {s1["failures"]}')
        reconciled = flow.dest.reconcile_claim(part.claim.claim_id, H.snapshot_env(part.env))
        rv = {k: reconciled.get(k) for k in ('status', 'retry_eligible', 'claim_state')}
        checks.equal((rv['status'], rv['retry_eligible']), ('applied', False), 'reconciliation establishes the committed effect; no retry eligibility')
        res, exc = H.execute_b(flow, part)
        v2 = A.view_b(res, exc)
        checks.equal((v2.get('status'), v2.get('newly_executed')), ('denied', False), 'the retry cannot deliver again')
        final = H.db_summary(flow.dest.path)
        checks.equal(final['effects'], s1['effects'], 'effect rows byte-identical after the retry')
        checks.equal(flow.dest.trace.count('after_commit'), 1, 'exactly one commit transaction')
        return {'first': v1, 'reconcile': rv, 'retry': v2, 'effects': final['effects'], 'claims': final['claims'], 'failures': [(f[0], f[1], f[2]) for f in final['failures']],
                **A.gate_for(final, {part.env.effect_id})}
    A.run(request, record_property, tmp_path, 'R01', trial)


def test_asw_r01_route_c_lost_ack_redelivery_does_not_dispatch_again(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_c(work, mp)
        first = H.exchange_run(flow, lose_ack=True)
        v1 = H.exchange_view(first)
        checks.equal(v1['attempt_status'], 'unknown', 'the exchange reports the lost acknowledgement as unknown')
        s1 = H.db_summary(flow.dest.path)
        checks.equal(len(s1['effects']), 1, 'the effect committed')
        second = H.exchange_run(flow)
        v2 = H.exchange_view(second)
        checks.equal((v2['attempted'], bool(v2['newly_executed'])), (False, False), 'redelivery dispatches nothing')
        checks.equal(v2['destination_observed'], 'applied', 'the committed effect is observed at the destination')
        final = H.db_summary(flow.dest.path)
        checks.equal(final['effects'], s1['effects'], 'effect rows byte-identical')
        checks.equal(C.attempt_summary(flow.dest.path)['count'], 1, 'one destination dispatch attempt only')
        return {'first': v1, 'redelivery': v2, 'effects': final['effects'], **A.gate_for(final, {first['execution'].get('effect_id')})}
    A.run(request, record_property, tmp_path, 'R01', trial)


# =====================================================================================================
# R02  Crash after destination commit: no blind duplicate effect after restart
# =====================================================================================================

@pytest.mark.parametrize('checkpoint', ['postcommit', 'prerecord'])
def test_asw_r02_route_a_crash_after_commit_then_restart_adds_no_duplicate(request, record_property, tmp_path, checkpoint):
    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = H.flow_a(work, mp)
        effect_id = flow.env.effect_id
        if checkpoint == 'postcommit':
            original = flow.dest.commit

            def commit_then_die(snapshot, **kwargs):
                original(snapshot, **kwargs)
                raise C.CrashSignal('after-durable-commit-before-acknowledgement')
            flow.dest.commit = commit_then_die
        else:
            records = flow.f.records
            calls = []
            original_append = records.append_attempt

            def append_then_die(value):
                calls.append(value.status)
                if len(calls) == 2:
                    raise C.CrashSignal('after-acknowledged-commit-before-control-plane-update')
                return original_append(value)
            records.append_attempt = append_then_die
        crashed = False
        try:
            H.execute_a(flow)
        except C.CrashSignal:
            crashed = True
        checks.equal(crashed, True, f'the {checkpoint} crash was delivered')
        at_crash = H.db_summary(flow.dest.path)
        checks.equal(len(at_crash['effects']), 1, 'the effect is durably committed at the crash')
        if checkpoint == 'prerecord':
            del flow.f.records.__dict__['append_attempt']
        dest2, executor2 = restart_a(flow)
        flow.dest, flow.executor = dest2, executor2
        commits = H.count_commits(dest2)
        rec = executor2.reconcile(flow.env, now=ch.NOW)
        rv = C.reconciliation_view(rec)
        checks.equal((rv['result'], rv['observation_accepted'], rv['retry_eligible']), ('applied', True, False), 'restart reconciliation establishes the committed effect; no retry eligibility')
        res, exc = H.execute_a(flow)
        v = A.view_a(res, exc)
        checks.equal((v.get('status'), v.get('newly_executed')), ('reconciled', False), 're-execution after restart reconciles, executing nothing new')
        final = H.db_summary(dest2.path)
        checks.equal(final['effects'], at_crash['effects'], 'effect rows byte-identical across the restart (stable effect identity, no duplicate)')
        checks.equal(commits['new_durable'], 0, 'no new durable commit after the restart')
        return {'checkpoint': checkpoint, 'reconcile': rv, 're_execution': v, 'effects': final['effects'], **A.gate_for(final, {effect_id})}
    A.run(request, record_property, tmp_path, 'R02', trial)


@pytest.mark.parametrize('seam,simulate', [('after_commit', None), ('before_failure_record', 'lost_ack')], ids=['kill_after_commit', 'kill_after_commit_before_failure_record'])
def test_asw_r02_route_b_real_process_kill_after_commit_then_restart_adds_no_duplicate(request, record_property, tmp_path, seam, simulate):
    def trial(work, mp, checks):
        H.flow_b(work)  # provisions the claim; the objects are then dropped
        code, output = C.run_child_that_dies(work, seam, simulate=simulate)
        checks.equal(code, 77, f'the child process was killed (os._exit) at seam {seam}: {output!r}')
        restarted = C.reopen_b(work)
        part = restarted.parts[0]
        at_kill = H.db_summary(restarted.dest.path)
        checks.equal((len(at_kill['effects']), at_kill['claims']), (1, [('claim-1', 'consumed')]), 'the effect is durably committed and the claim consumed at the kill')
        reconciled = restarted.dest.reconcile_claim(part.claim.claim_id, H.snapshot_env(part.env))
        rv = {k: reconciled.get(k) for k in ('status', 'retry_eligible')}
        checks.equal((rv['status'], rv['retry_eligible']), ('applied', False), 'restart reconciliation establishes the committed effect; no retry eligibility')
        res, exc = H.execute_b(restarted, part)
        v = A.view_b(res, exc)
        checks.equal((v.get('status'), v.get('newly_executed')), ('denied', False), 're-presenting the consumed claim executes nothing')
        final = H.db_summary(restarted.dest.path)
        checks.equal(final['effects'], at_kill['effects'], 'effect rows byte-identical across the restart')
        checks.equal(C.attempt_summary(restarted.dest.path)['count'], 1, 'exactly one attempt record links the effect')
        return {'seam': seam, 'killed': code == 77, 'reconcile': rv, 're_execution': v, 'effects': final['effects'], 'claims': final['claims'], **A.gate_for(final, {part.env.effect_id})}
    A.run(request, record_property, tmp_path, 'R02', trial)


def test_asw_r02_route_c_crash_after_commit_then_redelivery_never_redispatches(request, record_property, tmp_path):
    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = H.flow_c(work, mp)
        effect_id = flow.d.effect_id
        original = flow.dest.commit

        def commit_then_die(snapshot, **kwargs):
            original(snapshot, **kwargs)
            raise C.CrashSignal('after-durable-commit-before-acknowledgement')
        flow.dest.commit = commit_then_die
        crashed = False
        try:
            H.exchange_run(flow)
        except C.CrashSignal:
            crashed = True
        checks.equal(crashed, True, 'the crash was delivered after the destination commit')
        at_crash = H.db_summary(flow.dest.path)
        checks.equal(len(at_crash['effects']), 1, 'the effect is durably committed')
        flow.dest = ch.EffectiveGrantDestination(work / 'target' / 'sqlite')
        redelivery = H.exchange_run(flow)
        v = H.exchange_view(redelivery)
        checks.equal((v['attempted'], bool(v['newly_executed'])), (False, False), 'redelivery after the crash dispatches nothing')
        checks.expect(v['attempt_status'] != 'executed', f'redelivery never reports a fresh execution; observed {v}')
        final = H.db_summary(flow.dest.path)
        checks.equal(final['effects'], at_crash['effects'], 'effect rows byte-identical across the restart (no duplicate)')
        return {'redelivery': v, 'effects': final['effects'], **A.gate_for(final, {effect_id})}
    A.run(request, record_property, tmp_path, 'R02', trial)
