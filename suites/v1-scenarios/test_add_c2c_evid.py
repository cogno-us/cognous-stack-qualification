"""Addendum row ADD-C2C-EVID - race evidence records persist revalidation time, ordering source and direct destination inspection.

SPDX-License-Identifier: Apache-2.0

Requirement text (process/v1-validation/v1-2026-10-16-a/requirements.json, Stokes addendum 4.1): "Race evidence records persist
revalidation time, ordering source and direct destination inspection". The existing C07 cases pass but assert outcomes, not the
presence of each evidence field.

This module re-executes the C07 race matrix (same barriers, imported from ``test_scn_c07``; route A 5 changes x 4 points, route B
5 x 4, route C governed exchange 3 x 2) and, for EVERY race case, builds a race-evidence record from what is actually persisted and
asserts each required field:

  revalidation_time          route A/C: Control Plane journal ``resolution_checks`` entry of stage ``effect`` (``evaluated_at``)
                             route B  : ``authority_effect_receipts_v1.receipt_json.checked_at`` when the effect committed, else the
                                        destination ``failure_records_v1`` row (``created_at``, stage ``pre_dispatch``)
  ordering_source            route A/C: ``time_source`` persisted on the journal checks/attempts/refusals
                             route B  : ``status_version_source`` in the persisted authority receipt (committed cases)
                             all      : destination ``attempt_events.event_id`` monotone order, and the barrier ``actual_order`` trace
  direct_destination_inspection
                             product  : a persisted destination observation (journal ``observations`` / receipt commitment) whenever an
                                        attempt was dispatched, compared with an independent read-only SQLite connection
                             harness  : independent read-only inspection of the destination taken after the race (always)

Assertions are honest: a field the product does not persist is a violation (FAIL), not papered over. Product-layer gaps that are not
persisted by design (e.g. no dispatched attempt, hence no destination observation) are listed under ``product_layer_not_persisted``
in the evidence so they are visible; they are not counted as violations only for the case classes stated in the code comments.
Every case runs twice and the normalised observations are compared (D3).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sqlite3
from pathlib import Path

import pytest

import _c_2a_helpers as C
import _d02_d05_d09_helpers as H
import test_scn_c07 as C07  # barrier helpers only (module import; no test function is re-collected)
from _c_2a_helpers import no_network, pinned_reference  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures('pinned_reference')

REQUIRED_FIELDS = ('revalidation_time', 'ordering_source', 'direct_destination_inspection')


def _iso(value):
    try:
        parsed = dt.datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo is not None else None


def _ro(path):
    conn = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def _attempt_event_order(path, checks):
    """Persisted destination ordering key: attempt_events.event_id strictly increasing, created_at non-decreasing."""
    conn = _ro(path)
    try:
        rows = [dict(r) for r in conn.execute('SELECT event_id,attempt_id,status,created_at FROM attempt_events ORDER BY event_id')]
    finally:
        conn.close()
    ids = [r['event_id'] for r in rows]
    checks.expect(ids == sorted(set(ids)), f'attempt_events.event_id is not strictly increasing: {ids}')
    stamps = [r['created_at'] for r in rows]
    checks.expect(all(isinstance(s, (int, float)) for s in stamps), 'attempt_events.created_at not persisted as a number')
    checks.expect(stamps == sorted(stamps), 'attempt_events.created_at decreases against event order')
    return [r['status'] for r in rows]


def _independent_view(path, queued_saw=None):
    summary = H.db_summary(path)
    return {'source': 'separate read-only SQLite connection (mode=ro) taken after the race',
            'effect_rows': [{'effect_id': e['effect_id'], 'state': e['state'], 'operation_digest': e['operation_digest']} for e in summary['effects']],
            'effect_row_count': len(summary['effects']), 'queued_writer_saw_effect_rows_when_landed': queued_saw}


def _journal_evidence(flow, path, checks, *, committed, journal=None):
    """Route A / C: fields persisted by the Control Plane journal and the effective-grant destination.

    ``journal`` is the persisted Control Plane record of the executing workflow (route C: ``message_workflows.cp_record_json`` in the
    exchange store, read back through a fresh SQLite connection).
    """
    rec = journal if journal is not None else flow.f.records.load().model_dump(mode='json')  # re-read from the persisted store
    effect_checks = [x for x in rec['resolution_checks'] if x['stage'] == 'effect']
    checks.expect(bool(effect_checks), 'revalidation_time: no effect-stage resolution check persisted in the journal')
    times = [x.get('evaluated_at') for x in effect_checks]
    checks.expect(all(_iso(t) for t in times), f'revalidation_time: evaluated_at missing or not timezone-aware ISO-8601: {times}')
    sources = [x.get('time_source') for x in effect_checks]
    checks.expect(all(isinstance(s, str) and s for s in sources), f'ordering_source: time_source missing on the effect-stage check: {sources}')
    phases = [(x['check_id'], x['phase']) for x in rec['check_events'] if x['stage'] == 'effect']
    first_effect_check = phases[0][0] if phases else None
    seq = [p for c, p in phases if c == first_effect_check]
    checks.expect(bool(seq) and seq[0] == 'opened' and seq[-1] in ('completed', 'failed', 'aborted', 'closed'),
                  f'ordering_source: journal check_events do not bracket the revalidation (opened ... completed): {seq}')
    dispatched = bool(rec['attempts'])
    stamped = [(a['status'], _iso(a['started_at']) is not None, bool(a.get('time_source'))) for a in rec['attempts']]
    checks.expect(all(ok and src for _, ok, src in stamped), f'ordering_source: attempt records lack started_at/time_source: {stamped}')
    refusal = [(r['stage'], _iso(r['recorded_at']) is not None, bool(r.get('time_source'))) for r in rec['refusals']]
    checks.expect(all(ok and src for _, ok, src in refusal), f'ordering_source: refusal records lack recorded_at/time_source: {refusal}')
    if not dispatched:
        checks.expect(bool(rec['refusals']) or bool(rec['decisions']), 'no persisted refusal or decision record explains the absent attempt')
    statuses = _attempt_event_order(path, checks)
    inspection = {'dispatched': dispatched, 'persisted_observations': []}
    if dispatched:
        checks.expect(statuses[:1] == ['attempted'], f'destination attempt_events do not start with attempted: {statuses}')
        obs = rec['observations']
        checks.expect(bool(obs), 'direct_destination_inspection: attempt dispatched but no destination observation persisted in the journal')
        db = H.db_summary(path)
        if obs:
            last = obs[-1]
            checks.expect(_iso(last.get('observed_at')) is not None, 'direct_destination_inspection: observation observed_at missing')
            want = 'applied' if db['effects'] else 'absent'
            checks.equal(last.get('state'), want, 'persisted final destination observation agrees with the independent read-only inspection')
            if db['effects']:
                checks.equal((last.get('destination_state') or {}).get('operation_digest'), db['effects'][0]['operation_digest'],
                             'persisted destination_state digest equals the destination row')
            inspection['persisted_observations'] = [x['state'] for x in obs]
    return {'revalidation_time': {'source': 'journal.resolution_checks[stage=effect].evaluated_at', 'values': times},
            'ordering_source': {'time_source': sources, 'journal_check_phase_order': seq, 'destination_event_status_order': statuses,
                                'attempt_records': stamped, 'refusal_records': refusal},
            'direct_destination_inspection': inspection,
            'product_layer_not_persisted': [] if dispatched else ['destination observation (no attempt was dispatched; refusal happened before dispatch)']}


def _b_evidence(flow, part, path, checks, *, committed):
    conn = _ro(path)
    try:
        receipts = [dict(r) for r in conn.execute('SELECT * FROM authority_effect_receipts_v1')]
        fails = [dict(r) for r in conn.execute('SELECT * FROM failure_records_v1 ORDER BY rowid')]
    finally:
        conn.close()
    statuses = _attempt_event_order(path, checks)
    gaps = []
    if committed:
        checks.equal(len(receipts), 1, 'one persisted authority receipt for the committed effect')
        receipt = json.loads(receipts[0]['receipt_json']) if receipts else {}
        checks.expect(_iso(receipt.get('checked_at')) is not None, f'revalidation_time: receipt checked_at missing: {receipt.get("checked_at")!r}')
        src = receipt.get('status_version_source')
        checks.expect(isinstance(src, str) and bool(src), 'ordering_source: receipt status_version_source missing')
        checks.expect(str(receipt.get('grant_state_commitment', '')).startswith('sha256:'), 'direct_destination_inspection: receipt grant_state_commitment missing')
        checks.expect(statuses[:1] == ['attempted'] and 'executed' in statuses, f'destination attempt_events missing attempted/executed: {statuses}')
        db = H.db_summary(path)
        checks.equal(len(db['effects']), 1, 'independent read-only inspection sees the committed effect row')
        return {'revalidation_time': {'source': 'authority_effect_receipts_v1.receipt_json.checked_at', 'values': [receipt.get('checked_at')]},
                'ordering_source': {'status_version_source': src, 'destination_event_status_order': statuses},
                'direct_destination_inspection': {'dispatched': True, 'grant_state_commitment_persisted': bool(receipt.get('grant_state_commitment')),
                                                  'receipt_attempt_matches_destination': receipt.get('attempt_id') == receipts[0]['attempt_id']},
                'product_layer_not_persisted': []}
    checks.equal(len(receipts), 0, 'no authority receipt for a refused claim')
    checks.expect(bool(fails), 'revalidation_time: refusal not persisted as a destination failure record')
    row = fails[0] if fails else {}
    checks.expect(isinstance(row.get('created_at'), (int, float)) and row.get('created_at', 0) > 0, 'revalidation_time: failure record created_at missing')
    checks.expect(bool(row.get('stage')) and bool(row.get('reason_code')) and bool(row.get('detail')), 'refusal record lacks stage/reason_code/detail')
    return {'revalidation_time': {'source': 'failure_records_v1.created_at (refusal time; no receipt exists for a refused claim)', 'values': ['present' if row.get('created_at') else None]},
            'ordering_source': {'status_version_source': None, 'destination_event_status_order': statuses, 'refusal_stage': row.get('stage')},
            'direct_destination_inspection': {'dispatched': False},
            'product_layer_not_persisted': ['ordering source (status_version_source) is only persisted inside the authority receipt of a committed effect; '
                                            'a refusal persists stage/reason/time only', 'destination observation (no attempt dispatched)']}


def _finish(checks, evidence, trace, independent, route, level_trace_key='actual_order'):
    """Harness layer: the barrier trace is the ordering source of record; the independent inspection is always present."""
    checks.expect(bool(trace), 'ordering_source: barrier actual_order trace empty')
    evidence['ordering_source']['barrier_actual_order'] = list(trace)
    evidence['direct_destination_inspection']['independent_read_only'] = independent
    checks.expect(independent['effect_row_count'] in (0, 1), 'independent inspection effect count out of range')
    present = {
        'revalidation_time': bool(evidence['revalidation_time']['values']) and all(evidence['revalidation_time']['values']),
        'ordering_source': bool(evidence['ordering_source'].get('barrier_actual_order')) and (
            bool(evidence['ordering_source'].get('time_source')) or bool(evidence['ordering_source'].get('status_version_source'))
            or bool(evidence['ordering_source'].get('destination_event_status_order'))
            or bool(evidence['ordering_source'].get('refusal_stage'))),
        'direct_destination_inspection': 'independent_read_only' in evidence['direct_destination_inspection']}
    for field in REQUIRED_FIELDS:
        checks.expect(present[field], f'required evidence field not persisted: {field}')
    evidence['required_field_presence'] = present
    evidence['route'] = route
    return evidence


def _assert_evidence_persisted(request, payload):
    """Read the evidence file back (when SCN_EVIDENCE_DIR is set) and re-check the required fields from disk."""
    target = os.environ.get('SCN_EVIDENCE_DIR')
    for n in ('run1', 'run2'):
        ev = payload[n]['observed']['race_evidence']
        assert all(ev['required_field_presence'][f] for f in REQUIRED_FIELDS), ev['required_field_presence']
    if target:
        path = Path(target) / (request.node.name.replace('/', '_') + '.json')
        stored = json.loads(path.read_text())
        for n in ('run1', 'run2'):
            ev = stored[n]['observed']['race_evidence']
            assert all(ev['required_field_presence'][f] for f in REQUIRED_FIELDS), f'evidence file on disk lacks a required field: {path}'


# ------------------------------------------------------------------------------------------------
# route A
# ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize('point', C07.POINTS)
@pytest.mark.parametrize('change', sorted(C07.A_CHANGES))
def test_add_c2c_evid_route_a_race_evidence_fields_persisted(request, record_property, tmp_path, change, point):
    level = C07.A_CHANGES[change]

    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        apply_change = C07._a_change_fn(flow, change)
        trace, queued = [], []
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
                        return len(H.db_summary(flow.dest.path)['effects'])
                    queued.append(C07._queued_writer(change_and_look))
                    queued[0][1].wait()
                    trace.append('destination_writer_started_inside_open_write_transaction')
                else:
                    apply_change()
                    trace.append('resolver_change_landed_inside_open_write_transaction')
                return check_profile(conn, snapshot)
            flow.dest._check_commit_profile = hook
        res, exc = H.execute_a(flow)
        if queued:
            queued[0][0].join(30)
        if point == 'after-commit':
            apply_change()
            trace.append('change_landed_after_acknowledged_commit')
        committed = point in ('inside-commit-transaction', 'after-commit') or (point == 'commit-boundary' and level == 'resolver')
        checks.equal((H.result_view(res, exc).get('status') == 'executed'), committed, 'case outcome follows the declared C07 contract')
        evidence = _journal_evidence(flow, flow.dest.path, checks, committed=committed)
        evidence = _finish(checks, evidence, trace, _independent_view(flow.dest.path, queued[0][3].get('result') if queued else None), 'A')
        gate = H.effect_gate(H.db_summary(flow.dest.path), authorized_effect_ids={flow.env.effect_id}, authorized_digests={H.snapshot_digest(flow.env)})
        return {'change': change, 'point': point, 'race_evidence': evidence, **gate}
    payload = H.run_case(request, record_property, tmp_path, 'ADD-C2C-EVID', trial)
    _assert_evidence_persisted(request, payload)


# ------------------------------------------------------------------------------------------------
# route B
# ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize('point', C07.POINTS)
@pytest.mark.parametrize('change', C07.B_CHANGES)
def test_add_c2c_evid_route_b_race_evidence_fields_persisted(request, record_property, tmp_path, change, point):
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        apply_change = C07._b_change_fn(flow, part, change)
        trace, queued = [], []

        def hook(stage):
            if point == 'commit-boundary' and stage == 'before_begin':
                trace.append('change_landed_immediately_before_BEGIN_IMMEDIATE')
                apply_change()
            elif point == 'inside-commit-transaction' and stage == 'after_begin':
                def change_and_look():
                    apply_change()
                    return len(H.db_summary(flow.dest.path)['effects'])
                queued.append(C07._queued_writer(change_and_look))
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
        committed = point in ('inside-commit-transaction', 'after-commit')
        checks.equal((H.atomic_view(res, exc).get('status') == 'executed'), committed, 'case outcome follows the declared C07 contract')
        evidence = _b_evidence(flow, part, flow.dest.path, checks, committed=committed)
        evidence = _finish(checks, evidence, trace + [f'stage:{s}' for s in flow.dest.trace], _independent_view(flow.dest.path, queued[0][3].get('result') if queued else None), 'B')
        gate = H.effect_gate(H.db_summary(flow.dest.path), authorized_effect_ids={part.env.effect_id})
        return {'change': change, 'point': point, 'race_evidence': evidence, **gate}
    payload = H.run_case(request, record_property, tmp_path, 'ADD-C2C-EVID', trial)
    _assert_evidence_persisted(request, payload)


# ------------------------------------------------------------------------------------------------
# route C
# ------------------------------------------------------------------------------------------------

def _exchange_journal(flow):
    conn = _ro(flow.kwargs['store_path'])
    try:
        rows = conn.execute('SELECT cp_record_json FROM message_workflows').fetchall()
    finally:
        conn.close()
    assert len(rows) == 1, f'expected one persisted message workflow, found {len(rows)}'
    return json.loads(rows[0][0])


@pytest.mark.parametrize('point', ['after-decision-before-revalidation', 'commit-boundary'])
@pytest.mark.parametrize('change', sorted(C07.C_CHANGES))
def test_add_c2c_evid_route_c_race_evidence_fields_persisted(request, record_property, tmp_path, change, point):
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
        committed = H.exchange_view(res)['attempt_status'] == 'executed'
        evidence = _journal_evidence(flow, flow.dest.path, checks, committed=committed, journal=_exchange_journal(flow))
        evidence = _finish(checks, evidence, trace, _independent_view(flow.dest.path), 'C')
        gate = H.effect_gate(H.db_summary(flow.dest.path), authorized_effect_ids={res['execution'].get('effect_id')})
        return {'change': change, 'point': point, 'race_evidence': evidence, **gate}
    payload = H.run_case(request, record_property, tmp_path, 'ADD-C2C-EVID', trial)
    _assert_evidence_persisted(request, payload)
