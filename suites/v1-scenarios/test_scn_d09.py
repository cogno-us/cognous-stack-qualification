"""Catalog scenario D09 - Bypass and interruption (executed against the frozen F5b bounded reference).

SPDX-License-Identifier: Apache-2.0

Stimulus (catalog): call alternate routes; cancel before commit; race cancellation with commit. Required
observation: inventory and test all supported routes; state matches the documented commit ordering; do not claim
reversal after an irreversible commit.

"Cancellation" - the frozen bounded reference has no executor-level cancel call outside the optional OpenShell
destination (needs a Docker gateway and pinned CLI; not exercisable here, see report). The supported analogue
exercised here is WITHDRAWAL OF AUTHORITY (grant revocation at the resolver, the effective-grant table, or the
atomic authority tables) placed at every distinguishable point of the commit ordering, using the reference's own
deterministic seams and event barriers (no timing sleeps):
    before execution | at the commit boundary (immediately before the transaction) |
    inside the commit transaction (a concurrent canceller blocks on the write lock) |
    after durable commit but before acknowledgement (lost ack) | after acknowledgement.
Documented commit ordering exercised: authority is evaluated inside the destination's BEGIN IMMEDIATE transaction; the
effect is linearised at COMMIT; a cancellation that lands first prevents the effect, one that lands after leaves the
committed effect in place (no reversal is offered or claimed).
Every case runs twice from fresh stores and the two normalised observations are compared (owner decision D3).
"""
from __future__ import annotations

import dataclasses
import re
import threading
from pathlib import Path

import pytest

import _d02_d05_d09_helpers as H
from _reason_norm import exc_summary, normalise_reason  # noqa: E402
from _d02_d05_d09_helpers import no_network, pinned_reference  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures('pinned_reference')

REVERSAL_WORDS = re.compile(r'revers|rolled.?back|rollback|revert|undone|undo|compensat|cancelled|canceled', re.I)

# --- supported mutation routes of the bounded reference: declared inventory ----------------------------------------------
# id -> (what, exercised?, reason when not exercised)
ROUTES = {
    'cp-pinned-executor': ('Control Plane revalidation + PinnedControlPlaneExecutor + EffectiveGrantDestination (route A)', True, None),
    'atomic-claim-executor': ('AtomicLocalControlPlaneExecutor + AtomicAuthorityEffectDestination claims (route B, run_matched_refund route)', True, None),
    'exchange-run_exchange': ('governed-exchange run_exchange ingress; drives route A internally (route C)', True, None),
    'control-plane-local-destination': ('BoundedAuthorizationWorkflow.execute against the Control Plane LocalRefundDestination (no runtime executor)', True, None),
    'direct-commit-bypass': ('direct DurableRefundDestination.commit / LocalDestinationExecutor.execute_snapshot / adapter.apply on an effective-grant destination', True, None),
    'legacy-write-on-atomic-profile': ('legacy DurableRefundDestination write path on an atomic-claim database', True, None),
    'legacy-write-on-intent-profile': ('legacy DurableRefundDestination write path on an intent-registry database', True, None),
    'legacy-agent-engine': ('legacy AgentEngine.execute_action shell (declared to perform no side effect)', True, None),
    'openshell-destination': ('OpenShellRefundDestination (sandbox destination, request_cancel)', False,
                              'requires a pinned OpenShell 0.1.2 gateway, Docker and an immutable OCI image; outside the bounded Linux synthetic reference'),
    'legacy-cli': ('cli/moltbot_safe_cli.py', False, 'legacy CLI; statically asserted below to reference no destination/executor route'),
    'raw-sql-by-database-holder': ('direct SQL by a holder of the SQLite file', False,
                                   'declared out of model: SQLite does not separate the file holder from the authority writer (trusted-host boundary documented by the reference)'),
}
TESTED_ROUTE_IDS = ['cp-pinned-executor', 'atomic-claim-executor', 'exchange-run_exchange', 'control-plane-local-destination',
                    'direct-commit-bypass', 'legacy-write-on-atomic-profile', 'legacy-write-on-intent-profile', 'legacy-agent-engine']

# call sites that can mutate a destination, discovered statically below and required to match this table exactly
EXPECTED_CALL_SITES = {
    'runtime/engine/safe_executor.py': 'LocalDestinationExecutor.execute_snapshot -> destination.commit',
    'runtime/engine/control_plane_adapter.py': 'ControlPlaneRefundDestinationAdapter.apply -> execute_snapshot',
    'runtime/engine/atomic_local_control_plane_executor.py': 'AtomicLocalControlPlaneExecutor.execute -> execute_claim_atomic',
    'runtime/engine/refund_intent.py': 'IntentRefundDestination.commit -> super().commit',
    'runtime/engine/openshell_worker.py': 'sandbox worker destination.commit (OpenShell route)',
    'control_plane/src/agent_control_plane/bounded.py': 'BoundedAuthorizationWorkflow.execute -> destination.apply',
}
CALL_PATTERNS = [r'(?:destination|super\(\))\.commit\(', r'\bexecute_claim_atomic\(', r'\bexecute_snapshot\(', r'destination\.apply\(']


def discover_call_sites(paths):
    found = {}
    for rel in ('runtime/engine', 'control_plane/src/agent_control_plane'):
        for py in sorted((paths['runtime'].parent / rel).glob('*.py')):
            lines = [line for line in py.read_text().splitlines() if not line.lstrip().startswith(('def ', '#'))]  # call sites, not definitions
            hits = [pat for pat in CALL_PATTERNS if re.search(pat, '\n'.join(lines))]
            if hits:
                found[f'{rel}/{py.name}'] = hits
    return found


def scan_for_reversal(value, path='$'):
    """Return JSON paths of string values that CLAIM a reversal/rollback/cancellation outcome."""
    hits = []
    if isinstance(value, dict):
        for k, v in value.items():
            hits += scan_for_reversal(v, f'{path}.{k}')
    elif isinstance(value, (list, tuple)):
        for i, v in enumerate(value):
            hits += scan_for_reversal(v, f'{path}[{i}]')
    elif isinstance(value, str) and REVERSAL_WORDS.search(value):
        hits.append(f'{path}={value!r}')
    return hits


def test_scn_d09_source_identity_containment_and_initial_state(request, record_property, tmp_path):
    ref = H.reference()
    H.assert_pins_still_pristine()
    import engine
    assert Path(engine.__file__).resolve().is_relative_to(ref.paths['runtime'])

    def trial(work, mp, checks):
        (work / 'a').mkdir()
        (work / 'b').mkdir()
        a = H.db_summary(H.flow_a(work / 'a', mp).dest.path)
        b = H.db_summary(H.flow_b(work / 'b').dest.path)
        checks.equal((a['effects'], b['effects']), ([], []), 'initial destinations hold no effect')
        return {'initial_state_digest': H.digest({'a': a, 'b': b}), 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'D09', trial)


# ------------------------------------------------------------------------------------------------
# route inventory
# ------------------------------------------------------------------------------------------------

def test_scn_d09_route_inventory_is_complete_and_classified(request, record_property, tmp_path):
    ref = H.reference()

    def trial(work, mp, checks):
        found = discover_call_sites(ref.paths)
        undeclared = sorted(set(found) - set(EXPECTED_CALL_SITES))
        vanished = sorted(set(EXPECTED_CALL_SITES) - set(found))
        checks.equal(undeclared, [], 'every destination-mutating call site is declared in the inventory (an undeclared one is a new route)')
        checks.equal(vanished, [], 'every declared call site still exists at the pin')
        exercised = sorted(r for r, (_, ex, _) in ROUTES.items() if ex)
        checks.equal(exercised, sorted(TESTED_ROUTE_IDS), 'routes marked exercised are exactly the routes this module tests')
        cli_text = (ref.paths['runtime'] / 'cli/moltbot_safe_cli.py').read_text()
        checks.expect(not re.search(r'safe_executor|DurableRefundDestination|control_plane_adapter|local_authority_effect|refund_intent|openshell', cli_text),
                      'legacy CLI references no destination or executor route')
        return {'declared_routes': {r: {'what': w, 'exercised': ex, 'not_exercised_reason': why} for r, (w, ex, why) in ROUTES.items()},
                'discovered_call_sites': found, 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'D09', trial)


# ------------------------------------------------------------------------------------------------
# supported routes: authorized request effects exactly once; withdrawn authority yields no effect
# ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize('route', ['cp-pinned-executor', 'atomic-claim-executor', 'exchange-run_exchange', 'control-plane-local-destination'])
@pytest.mark.parametrize('authority', ['current', 'withdrawn-before-execution'])
def test_scn_d09_supported_route_effect_follows_current_authority(request, record_property, tmp_path, route, authority):
    def trial(work, mp, checks):
        withdrawn = authority != 'current'
        if route == 'cp-pinned-executor':
            flow = H.flow_a(work, mp)
            if withdrawn:
                H.revoke_resolver(flow)
            res, exc = H.execute_a(flow)
            view = H.result_view(res, exc)
            authorized = {flow.env.effect_id}
            summary = H.db_summary(flow.dest.path)
            checks.equal(view.get('status'), 'denied' if withdrawn else 'executed', 'executor outcome')
        elif route == 'atomic-claim-executor':
            flow = H.flow_b(work)
            part = flow.parts[0]
            if withdrawn:
                flow.dest.set_grant_status(part.claim.grant_id, status='revoked')
            res, exc = H.execute_b(flow, part)
            view = H.atomic_view(res, exc)
            authorized = {part.env.effect_id}
            summary = H.db_summary(flow.dest.path)
            checks.equal(view.get('status'), 'denied' if withdrawn else 'executed', 'executor outcome')
        elif route == 'exchange-run_exchange':
            flow = H.flow_c(work, mp)
            extra = {'mutate_resolver_after_decision': lambda resolver: setattr(next(iter(resolver.statuses.values())), 'status', 'revoked')} if withdrawn else {}
            res = H.exchange_run(flow, **extra)
            view = H.exchange_view(res)
            authorized = {res['execution'].get('effect_id')}
            summary = H.db_summary(flow.dest.path)
            checks.equal(view['attempt_status'], 'denied' if withdrawn else 'executed', 'exchange outcome')
        else:
            ch = H.reference().chain
            p, r, f, c = ch.setup_flow(work)  # the Control Plane's own LocalRefundDestination (JSON), no runtime executor
            mp.setattr(__import__('agent_control_plane.bounded', fromlist=['x']), '_now', lambda: ch.NOW)
            d = f.decide(p, now=ch.NOW)
            checks.equal(d.result, 'authorized', 'decision authorized')
            if withdrawn:
                next(iter(r.statuses.values())).status = 'revoked'
            try:
                attempt, observation = f.execute(p, d, adapter_id=p.adapter_id, now=ch.NOW)
                view = {'attempt': attempt.status, 'observation': observation.state if observation else None}
            except PermissionError as exc:
                view = {'raised': 'PermissionError: ' + normalise_reason(exc)}
            effects = f.destination.snapshot()['effects']
            summary = {'effects': [{'effect_id': k, 'state': v.get('state'), 'operation_digest': None, 'target': v.get('target'), 'amount': v.get('amount')} for k, v in effects.items()],
                       'attempts': [], 'failures': []}
            authorized = {d.effect_id}
            checks.equal(view.get('attempt', 'refused'), 'refused' if withdrawn else 'acknowledged', 'workflow outcome')
        count = len(summary['effects'])
        checks.equal(count, 0 if withdrawn else 1, 'durable effect count follows current authority')
        gate = H.effect_gate(summary, authorized_effect_ids=authorized)
        return {'route': route, 'authority': authority, 'view': view, 'effects': summary['effects'], **gate}
    H.run_case(request, record_property, tmp_path, 'D09', trial)


# ------------------------------------------------------------------------------------------------
# alternate routes that skip the supported admission path must not mutate the destination
# ------------------------------------------------------------------------------------------------

BYPASS_VARIANTS = ['commit-without-precondition', 'commit-with-stale-digest', 'commit-with-correct-digest-after-revocation',
                   'execute_snapshot-without-precondition', 'adapter-apply-without-precondition']


@pytest.mark.parametrize('variant', BYPASS_VARIANTS)
def test_scn_d09_direct_bypass_of_executor_route_is_refused_by_destination(request, record_property, tmp_path, variant):
    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = H.flow_a(work, mp)
        snapshot = H.snapshot_env(flow.env)
        grant = flow.d.binding
        current_digest = flow.r.contexts[ch.PROFILE]['runtime_authority']['expected_effective_grant_digest']
        outcome = {}
        if variant == 'commit-without-precondition':
            try:
                flow.dest.commit(snapshot)
                outcome = {'raised': None}
            except Exception as exc:
                outcome = {'raised': exc_summary(exc)}
        elif variant == 'commit-with-stale-digest':
            H.revoke_destination(flow)
            flow.dest.set_effective_grant(principal=flow.p.principal, grant_id=grant.grant_id, revision='2', permissions=flow.p.requested_permissions)
            try:
                flow.dest.commit(snapshot, expected_effective_grant_digest=current_digest, effective_grant_derivation_version=ch.DERIVATION)
                outcome = {'raised': None}
            except Exception as exc:
                outcome = {'raised': exc_summary(exc)}
        elif variant == 'commit-with-correct-digest-after-revocation':
            revoked_digest = H.revoke_destination(flow)
            try:
                flow.dest.commit(snapshot, expected_effective_grant_digest=revoked_digest, effective_grant_derivation_version=ch.DERIVATION)
                outcome = {'raised': None}
            except Exception as exc:
                outcome = {'raised': exc_summary(exc)}
        elif variant == 'execute_snapshot-without-precondition':
            local = ch.LocalDestinationExecutor if hasattr(ch, 'LocalDestinationExecutor') else __import__('engine.safe_executor', fromlist=['x']).LocalDestinationExecutor
            res = local(flow.dest, flow.executor.policy).execute_snapshot(snapshot)
            outcome = {'status': res.status, 'error': res.error}
        else:
            from engine.control_plane_adapter import ControlPlaneRefundDestinationAdapter
            op = flow.env.operation
            adapter = ControlPlaneRefundDestinationAdapter(snapshot=snapshot, destination=flow.dest, policy=flow.executor.policy,
                                                           trusted_institution_id=op.institution_id, trusted_authority_domain=op.authority_domain,
                                                           observation_clock=lambda: ch.NOW)
            try:
                adapter.apply(effect_id=snapshot.effect_id, grant_id=op.grant_id, max_effects=op.effective_max_effects, target=op.target,
                              amount=op.amount, unit=op.unit, payload=op.payload)
                outcome = {'raised': None}
            except Exception as exc:
                outcome = {'raised': exc_summary(exc)}
        after = H.db_summary(flow.dest.path)
        checks.equal(after['effects'], [], f'bypass variant {variant} must not mutate the destination; observed {outcome}')
        refused = outcome.get('raised') not in (None, '') if 'raised' in outcome else outcome.get('status') in ('failed', 'denied')
        checks.expect(refused, f'bypass variant {variant} must be refused; observed {outcome}')
        return {'variant': variant, 'outcome': outcome, 'effects': after['effects'], 'failures': after['failures'], **H.effect_gate(after)}
    H.run_case(request, record_property, tmp_path, 'D09', trial)


def test_scn_d09_exchange_ingress_without_trusted_configuration_fails_closed(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_c(work, mp)
        kwargs = dict(flow.kwargs)
        del kwargs['runtime_authority_profile']
        try:
            flow.gax.run_exchange(flow.message, flow.bundle, flow.registry, flow.dest, **kwargs)
            raised = None
        except ValueError as exc:
            raised = str(exc)
        no_resolver = dict(flow.kwargs)
        no_resolver['resolver'] = None
        res = flow.gax.run_exchange(flow.message, flow.bundle, flow.registry, flow.dest, **no_resolver)
        after = H.db_summary(flow.dest.path)
        checks.expect(bool(raised) and 'requires trusted' in raised, f'missing runtime authority profile is refused: {raised}')
        checks.equal(res['execution'].get('reason'), 'trusted_resolver_required', 'missing resolver fails closed')
        checks.equal(after['effects'], [], 'no destination mutation through the unconfigured ingress')
        return {'missing_profile': None if raised is None else normalise_reason(raised), 'missing_resolver': H.exchange_view(res), 'effects': after['effects'], **H.effect_gate(after)}
    H.run_case(request, record_property, tmp_path, 'D09', trial)


def test_scn_d09_legacy_write_path_on_atomic_profile_database_is_refused(request, record_property, tmp_path):
    def trial(work, mp, checks):
        from engine.safe_executor import DurableRefundDestination, LocalDestinationExecutor
        flow = H.flow_b(work)
        snapshot = H.snapshot_env(flow.parts[0].env)
        legacy = DurableRefundDestination(work)
        try:
            legacy.commit(snapshot)
            direct = None
        except Exception as exc:
            direct = exc_summary(exc)
        res = LocalDestinationExecutor(legacy, flow.policy).execute_snapshot(snapshot)
        after = H.db_summary(flow.dest.path)
        checks.expect(bool(direct) and 'requires atomic claim execution' in direct, f'direct legacy commit refused: {direct}')
        checks.equal(res.status, 'failed', 'legacy executor refused')
        checks.equal(after['effects'], [], 'no destination mutation through the legacy path')
        checks.equal(after['claims'], [('claim-1', 'issued')], 'authority claim untouched')
        return {'direct_commit': direct, 'legacy_executor': {'status': res.status, 'error': res.error}, 'effects': after['effects'], **H.effect_gate(after)}
    H.run_case(request, record_property, tmp_path, 'D09', trial)


def test_scn_d09_legacy_write_path_on_intent_profile_database_is_refused(request, record_property, tmp_path):
    def trial(work, mp, checks):
        from engine.safe_executor import DurableRefundDestination, LocalDestinationExecutor
        from engine.refund_intent import RefundIntentRegistry
        flow = H.flow_a(work, mp)
        # a fresh destination that opts into the intent profile (activation requires an empty destination)
        destination = DurableRefundDestination(work / 'intent-state')
        RefundIntentRegistry(destination)
        snapshot = H.snapshot_env(flow.env)
        try:
            destination.commit(snapshot)
            direct = None
        except Exception as exc:
            direct = exc_summary(exc)
        res = LocalDestinationExecutor(destination, flow.executor.policy).execute_snapshot(snapshot)
        after = H.db_summary(destination.path)
        checks.expect(bool(direct) and 'requires bound dispatch' in direct, f'direct legacy commit refused: {direct}')
        checks.equal(res.status, 'failed', 'legacy executor refused')
        checks.equal(after['effects'], [], 'no destination mutation through the legacy path')
        return {'direct_commit': direct, 'legacy_executor': {'status': res.status, 'error': res.error}, 'effects': after['effects'], **H.effect_gate(after)}
    H.run_case(request, record_property, tmp_path, 'D09', trial)


def test_scn_d09_legacy_agent_engine_performs_no_side_effect(request, record_property, tmp_path):
    def trial(work, mp, checks):
        import json
        from engine.engine import AgentEngine
        perms = work / 'permissions.json'
        perms.write_text(json.dumps({'agent1': ['write']}))
        engine = AgentEngine(str(work / 'sandbox'), str(perms), str(work / 'audit.log'))
        res = engine.execute_action('agent1', {'type': 'write', 'target': 'x', 'params': {}})
        try:
            engine.execute_action('agent2', {'type': 'write'})
            denied = None
        except PermissionError as exc:
            denied = str(exc)
        files = sorted(p.name for p in (work / 'sandbox').rglob('*') if p.is_file())
        checks.equal((res['status'], res['executed']), ('unsupported', False), 'even a permitted legacy action reports no execution')
        checks.expect(bool(denied), 'unpermitted legacy action is refused')
        checks.equal(files, [], 'legacy engine writes nothing to its sandbox')
        return {'permitted': {'status': res['status'], 'executed': res['executed']}, 'unpermitted': None if denied is None else normalise_reason(denied), 'sandbox_files': files,
                'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'D09', trial)


# ------------------------------------------------------------------------------------------------
# cancellation (authority withdrawal) placed at each point of the commit ordering
# ------------------------------------------------------------------------------------------------

def _start_canceller(fn):
    """Start a concurrent canceller and return (thread, started-event). It blocks on the SQLite write lock."""
    started = threading.Event()
    errors = []

    def run():
        started.set()
        try:
            fn()
        except Exception as exc:  # pragma: no cover - surfaced through the observation
            errors.append(exc_summary(exc))
    thread = threading.Thread(target=run)
    thread.start()
    return thread, started, errors


def _effective_status(summary):
    return [s for _, s in summary.get('effective_grants', [])]


@pytest.mark.parametrize('point', ['before-execution', 'commit-boundary', 'inside-commit-transaction', 'after-durable-commit-lost-ack', 'after-acknowledgement'])
def test_scn_d09_route_a_cancellation_ordering(request, record_property, tmp_path, point):
    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = H.flow_a(work, mp)
        commits = H.count_commits(flow.dest)
        trace = []
        canceller = None
        if point == 'before-execution':
            H.revoke_resolver(flow)
        elif point == 'commit-boundary':
            original = flow.dest.commit

            def cancel_then_commit(snapshot, **kwargs):
                trace.append('cancel_landed_before_commit_transaction')
                H.revoke_destination(flow)
                return original(snapshot, **kwargs)
            flow.dest.commit = cancel_then_commit
        elif point == 'inside-commit-transaction':
            check_profile = flow.dest._check_commit_profile

            def hook(conn, snapshot):
                nonlocal canceller
                canceller = _start_canceller(lambda: H.revoke_destination(flow))
                canceller[1].wait()  # barrier: the canceller is racing while the write transaction is open
                trace.append('canceller_started_inside_write_transaction')
                return check_profile(conn, snapshot)
            flow.dest._check_commit_profile = hook
        res, exc = H.execute_a(flow, simulate='lost_ack' if point == 'after-durable-commit-lost-ack' else None)
        if canceller:
            canceller[0].join(30)
            checks.equal(canceller[2], [], 'concurrent canceller completed without error')
        view = H.result_view(res, exc)
        s_commit = H.db_summary(flow.dest.path)
        post = {}
        if point in ('after-durable-commit-lost-ack', 'after-acknowledgement'):
            H.revoke_resolver(flow)
            H.revoke_destination(flow)
            recovery, exc2 = H.execute_a(flow)
            post['re_execution'] = H.result_view(recovery, exc2)
            post['reconcile'] = (lambda r: {'result': r.result, 'retry_eligible': r.retry_eligible})(flow.executor.reconcile(flow.env, now=ch.NOW)) if point == 'after-durable-commit-lost-ack' else None
            post['historical'] = (lambda r: {'status': r.status, 'observed_state': r.observed_state})(flow.executor.observe_historical(flow.env))
        final = H.db_summary(flow.dest.path)
        committed_before_cancel = point in ('inside-commit-transaction', 'after-durable-commit-lost-ack', 'after-acknowledgement')
        if point in ('before-execution', 'commit-boundary'):
            checks.equal(final['effects'], [], f'cancellation at {point} prevents the effect')
            checks.expect(view.get('status') in ('denied', 'failed'), f'cancelled request is refused/failed; observed {view}')
            checks.equal(commits['new_durable'], 0, 'no durable commit happened')
            if point == 'commit-boundary':
                checks.equal(view.get('error'), 'effective_grant_changed_at_commit', 'refusal reason names the commit-time authority change')
            checks.expect(bool(final['failures']) or bool(H.journal_view(flow)['refusals']) or view.get('status') == 'failed', 'refusal path observable')
        else:
            checks.equal(len(final['effects']), 1, f'cancellation at {point} cannot remove or duplicate the committed effect')
            checks.equal(final['effects'][0]['state'], 'applied', 'the committed effect stays applied (no reversal)')
            checks.equal(commits['new_durable'], 1, 'exactly one durable commit')
            checks.equal(final['effects'], s_commit['effects'], 'later cancellation leaves the committed effect byte-identical')
            checks.expect('revoked' in _effective_status(final), 'the cancellation itself was recorded after the commit')
        if post:
            checks.equal(post['re_execution'].get('status'), 'denied', 'a re-execution after withdrawal is refused')
            checks.equal(post['re_execution'].get('newly_executed'), False, 'nothing re-executed')
            checks.equal(post['historical']['observed_state'], 'applied', 'historical observation still reports the committed effect')
        if point == 'after-durable-commit-lost-ack':
            checks.equal(view.get('status'), 'unknown', 'a lost acknowledgement is reported as unknown, not as success or failure')
            checks.equal(post['reconcile']['result'], 'applied', 'reconciliation establishes the committed effect')
        claims = scan_for_reversal({'view': view, 'post': post, 'journal': H.journal_view(flow), 'states': [e['state'] for e in final['effects']]})
        checks.equal(claims, [], 'no result, journal or state claims a reversal/rollback/cancellation outcome')
        gate = H.effect_gate(final, authorized_effect_ids={flow.env.effect_id}, authorized_digests={H.snapshot_digest(flow.env)})
        return {'point': point, 'ordering': trace, 'committed_before_cancel': committed_before_cancel, 'result': view, 'post': post,
                'effects': final['effects'], 'effective_grants': final.get('effective_grants'), 'commit_instrumentation': commits,
                'journal': H.journal_view(flow), 'destination_failures': final['failures'], **gate}
    H.run_case(request, record_property, tmp_path, 'D09', trial)


@pytest.mark.parametrize('point', ['before-execution', 'commit-boundary', 'inside-commit-transaction', 'after-durable-commit-lost-ack', 'after-acknowledgement'])
def test_scn_d09_route_b_cancellation_ordering(request, record_property, tmp_path, point):
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        grant = part.claim.grant_id
        canceller = None

        def hook(stage):
            nonlocal canceller
            if point == 'commit-boundary' and stage == 'before_begin':
                flow.dest.set_grant_status(grant, status='revoked')
            elif point == 'inside-commit-transaction' and stage == 'after_begin':
                canceller = _start_canceller(lambda: flow.dest.set_grant_status(grant, status='revoked'))
                canceller[1].wait()
        flow.dest.stage_hook = hook
        if point == 'before-execution':
            flow.dest.set_grant_status(grant, status='revoked')
        res, exc = H.execute_b(flow, part, simulate='lost_ack' if point == 'after-durable-commit-lost-ack' else None)
        if canceller:
            canceller[0].join(30)
            checks.equal(canceller[2], [], 'concurrent canceller completed without error')
        view = H.atomic_view(res, exc)
        post = {}
        if point in ('after-durable-commit-lost-ack', 'after-acknowledgement'):
            flow.dest.set_grant_status(grant, status='revoked')
            again, e2 = H.execute_b(flow, part)
            post['re_execution'] = H.atomic_view(again, e2)
            post['reconcile'] = {k: v for k, v in flow.dest.reconcile_claim(part.claim.claim_id, H.snapshot_env(part.env)).items() if k in ('status', 'retry_eligible', 'claim_state')}
        final = H.db_summary(flow.dest.path)
        claim = [c for c in final['claims'] if c[0] == part.claim.claim_id]
        if point in ('before-execution', 'commit-boundary'):
            checks.equal(final['effects'], [], f'cancellation at {point} prevents the effect')
            checks.equal(view.get('status'), 'denied', 'cancelled request is refused')
            checks.equal(claim, [(part.claim.claim_id, 'issued')], 'the refused claim is not consumed')
            checks.equal(flow.dest.trace.count('after_commit'), 0, 'no commit transaction completed')
            checks.expect(bool(final['failures']), 'refusal path observable in destination failure records')
        else:
            checks.equal(len(final['effects']), 1, f'cancellation at {point} cannot remove or duplicate the committed effect')
            checks.equal(final['effects'][0]['state'], 'applied', 'the committed effect stays applied (no reversal)')
            checks.equal(claim, [(part.claim.claim_id, 'consumed')], 'the claim stays consumed by the commit')
            checks.equal(flow.dest.trace.count('after_commit'), 1, 'exactly one commit transaction')
            checks.equal(flow.dest.claim_state(part.claim.claim_id), 'consumed', 'claim consumed')
            grant_rows = flow.dest._connect().execute('SELECT status FROM authority_grants_v1 WHERE grant_id=?', (grant,)).fetchone()[0]
            checks.equal(grant_rows, 'revoked', 'the cancellation itself landed after the commit')
        if point == 'after-durable-commit-lost-ack':
            checks.equal(view.get('status'), 'unknown', 'a lost acknowledgement is reported as unknown')
        if post:
            checks.equal(post['re_execution'].get('status'), 'denied', 'a re-execution after withdrawal is refused')
            checks.equal(post['reconcile'].get('status'), 'applied', 'reconciliation reports the committed effect')
            checks.equal(post['reconcile'].get('retry_eligible'), False, 'reconciliation never makes the committed effect retry-eligible')
        claims = scan_for_reversal({'view': view, 'post': post, 'states': [e['state'] for e in final['effects']]})
        checks.equal(claims, [], 'no result or state claims a reversal/rollback/cancellation outcome')
        gate = H.effect_gate(final, authorized_effect_ids={part.env.effect_id})
        return {'point': point, 'stage_trace': list(flow.dest.trace), 'result': view, 'post': post, 'effects': final['effects'], 'claims': final['claims'],
                'budgets': final['budgets'], 'destination_failures': final['failures'], **gate}
    H.run_case(request, record_property, tmp_path, 'D09', trial)


@pytest.mark.parametrize('point', ['before-commit', 'after-durable-commit-lost-ack', 'after-acknowledgement'])
def test_scn_d09_route_c_exchange_cancellation_ordering(request, record_property, tmp_path, point):
    def trial(work, mp, checks):
        flow = H.flow_c(work, mp)
        post = {}
        if point == 'before-commit':
            first = H.exchange_run(flow, mutate_resolver_after_decision=lambda r: setattr(next(iter(r.statuses.values())), 'status', 'revoked'))
        else:
            first = H.exchange_run(flow, lose_ack=(point == 'after-durable-commit-lost-ack'))
            H.revoke_resolver(flow)
            post['redelivery'] = H.exchange_view(H.exchange_run(flow, lose_ack=False))
            post['recovery'] = H.exchange_view(H.exchange_resume(flow))
        view = H.exchange_view(first)
        final = H.db_summary(flow.dest.path)
        if point == 'before-commit':
            checks.equal(view['attempt_status'], 'denied', 'cancelled exchange is denied')
            checks.equal(final['effects'], [], 'no effect after cancellation before commit')
        else:
            checks.equal(len(final['effects']), 1, 'the committed effect is neither removed nor duplicated by later cancellation')
            checks.equal(final['effects'][0]['state'], 'applied', 'the committed effect stays applied (no reversal)')
            checks.equal(view['attempt_status'], 'unknown' if point == 'after-durable-commit-lost-ack' else 'executed', 'first-run outcome')
            checks.equal(post['redelivery']['attempted'], False, 'redelivery after cancellation dispatches nothing')
            checks.equal(post['recovery']['newly_executed'], False, 'recovery after cancellation executes nothing')
        claims = scan_for_reversal({'view': view, 'post': post, 'states': [e['state'] for e in final['effects']]})
        checks.equal(claims, [], 'no result or state claims a reversal/rollback/cancellation outcome')
        gate = H.effect_gate(final, authorized_effect_ids={first['execution'].get('effect_id')})
        return {'point': point, 'result': view, 'post': post, 'effects': final['effects'], **gate}
    H.run_case(request, record_property, tmp_path, 'D09', trial)
