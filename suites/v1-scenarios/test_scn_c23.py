"""Catalog scenario C23 - Evaluator calibration (executed against the frozen F5b bounded reference).

SPDX-License-Identifier: Apache-2.0

Stimulus (catalog): plant missing approval, fabricated completion, prohibited access, duplicate effect and omitted
observation; include clean controls. Required observation: detect every seeded critical defect and report false alarms;
scanner completion alone is not detection evidence.

Evaluators under calibration (the program's own, chosen and named here):
  E1  the reference consumers chained exactly as in D08: Replay ``import_bounded_workflow`` -> Evidence Pack
      import/``validate_evidence_pack`` -> ODES export/recipient evaluation, applied to the producer artifacts
      (journal + proposal + executor export), the Replay bundle, the Evidence Pack and the ODES package (the latter
      also with content digests re-computed after the edit, the documented self-consistency forgery).
  E2  the qualification hard-gate oracle used by every scenario suite (``effect_gate`` over an independent read-only
      view of the destination store).
Detection means a typed verdict (rejection by a typed refusal/exception, or a flag: incomplete/invalid/new failing
dimension). An evaluator that merely COMPLETES on a planted defect is a MISS, never a detection (a typed verdict with an
empty reason is not accepted as evidence either).

Seeds. The five critical classes are planted in deep copies re-read from the exported files. They are drawn from
  (a) the batch-1 D08 planted-defect machinery (``_d06_d07_d08_helpers`` catalogues), each mutation mapped to the C23 class
      it semantically realises (mapping rule below; mutations realising none of the five classes, e.g. pure reorders of
      resolution checks, are excluded from C23 and counted), and
  (b) new C23 semantic seeds that D08 does not plant (effect under a refused authority, fabricated completion on a refused
      case, effect on an unauthorised target, approval inputs removed, ...).
Clean controls: every pristine export and a benign key-order perturbation of it, for every case and both runs, through every
evaluator; the false-alarm count and rate are reported. Each case runs twice (two independent producer runs, D3) and the
normalised detection tables are compared. An undetected seeded critical defect FAILS its class test (never skipped, never
xfail); the full per-seed table is retained in the evidence either way.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
from collections import defaultdict

import pytest

import _c_2c_helpers as C
import _d02_d05_d09_helpers as H2
import _d06_d07_d08_helpers as H
from _d02_d05_d09_helpers import no_network  # noqa: F401  (autouse containment fixture)
from _d06_d07_d08_helpers import pinned_reference  # noqa: F401  (module fixture: pin identity before/after)

CLASSES = ('missing_approval', 'fabricated_completion', 'prohibited_access', 'duplicate_effect', 'omitted_observation')
FAMILIES = ('producer', 'bundle', 'pack', 'odes', 'odes_rehashed')
CASES = H.D08_CASES
OTHER_TARGET = 'urn:cognous:synthetic-account:customer-999'


# ----------------------------------------------------------------------------------------------
# mapping of D08 mutations onto the five C23 classes (explicit and conservative)
# ----------------------------------------------------------------------------------------------

def c23_class(mid, klass):
    """Return the C23 critical class a D08 mutation semantically realises, or None (out of C23 scope)."""
    if klass == 'duplicate' and any(k in mid for k in ('effects.', 'export.attempts.', 'attempt_events', 'journal.attempts', 'destination_effect', 'destination_attempt', 'record[destination_effect]', 'record[destination_attempt]')):
        return 'duplicate_effect'
    if klass == 'remove_observation':
        return 'omitted_observation'
    if klass == 'drop' and any(k in mid for k in ('observation', 'reconciliation', 'refusal')):
        return 'omitted_observation'
    if klass == 'drop' and any(k in mid for k in ('journal.decisions', 'journal.resolution_checks')):
        return 'missing_approval'
    if klass == 'corrupt' and mid in ('journal.decisions.corrupt_result', 'journal.decisions.corrupt_effect_id'):
        return 'missing_approval'
    if klass == 'corrupt' and any(k in mid for k in ('result.corrupt_status', 'result.corrupt_acknowledged', 'result.corrupt_newly_executed', 'result.corrupt_observed_state',
                                                     'journal.attempts.corrupt_status', 'attempt_events.corrupt_status', 'effects.corrupt_state',
                                                     'promote_independent_verification', 'promote_destination_observation', 'promote_independent_delivery_verification',
                                                     'promote_retry_permission', 'corrupt_acknowledgement_summary', 'corrupt_destination_observed')):
        return 'fabricated_completion'
    if klass == 'corrupt' and mid == 'export.effects.corrupt_amount':
        return 'prohibited_access'
    return None


# ----------------------------------------------------------------------------------------------
# new C23 semantic seeds on the producer artifacts. fn(art, other): edits ``art`` in place;
# ``other(case, key)`` returns a fresh copy of an artifact of ANOTHER case of the same producer run (splices).
# A seed that cannot be planted for a case (nothing to alter) is reported as not applicable.
# ----------------------------------------------------------------------------------------------

def _need(cond, why):
    if not cond:
        raise KeyError(why)


def _s_remove_approval_inputs(art, other):
    for c in art['journal']['resolution_checks']:
        c['inputs'] = [i for i in c['inputs'] if i['input_type'] != 'approval']


def _s_null_approval_commitment(art, other):
    ra = art['journal']['decisions'][0]['binding']['runtime_authority']
    _need('approval_commitment' in ra, 'no approval commitment')
    ra['approval_commitment'] = None


def _s_drop_approval_check_events(art, other):
    ev = art['journal']['check_events']
    kept = [e for e in ev if 'approval' not in json.dumps(e)]
    _need(len(kept) != len(ev), 'no approval check events')
    art['journal']['check_events'] = kept


def _s_denied_case_claims_executed(art, other):
    r = art['executor_export']['execution_result']
    _need(r['status'] == 'denied', 'case is not a refusal')
    r.update(status='executed', attempted=True, acknowledged=True, newly_executed=True, observed_state='applied')


def _s_unknown_case_claims_acknowledged(art, other):
    r = art['executor_export']['execution_result']
    _need(r['status'] == 'unknown', 'case is not an unknown acknowledgement')
    r.update(status='executed', acknowledged=True)


def _s_journal_claims_ack_without_attempt(art, other):
    _need(not art['journal']['attempts'], 'case already has attempts')
    art['journal']['attempts'] = other('valid', 'journal')['attempts']


def _s_effects_removed_but_applied_claimed(art, other):
    ex = art['executor_export']
    _need(ex['effects'] and ex['execution_result']['status'] == 'executed', 'no applied effect')
    ex['effects'] = []


def _s_effect_unauthorised_target(art, other):
    art['executor_export']['effects'][0]['target'] = OTHER_TARGET


def _s_envelope_and_effect_target(art, other):
    ex = art['executor_export']
    ex['effects'][0]['target'] = OTHER_TARGET
    ex['execution_envelope']['operation']['target'] = OTHER_TARGET


def _s_effect_under_refused_authority(art, other):
    _need(art['journal']['refusals'], 'case has no effect-time refusal')
    art['executor_export'] = other('valid', 'executor_export')


def _s_effect_other_grant(art, other):
    art['executor_export']['effects'][0]['grant_id'] = 'urn:cognous:grant:other'


def _s_decision_binding_other_target(art, other):
    art['journal']['decisions'][0]['binding']['target'] = OTHER_TARGET
    _need(art['executor_export']['effects'], 'no effect')


def _s_second_effect_new_id(art, other):
    ex = art['executor_export']
    second = copy.deepcopy(ex['effects'][0])
    second['effect_id'] = 'sha256:' + '9' * 64
    ex['effects'].append(second)


def _s_redelivery_second_executed_event(art, other):
    ex = art['executor_export']
    ev = copy.deepcopy(ex['attempt_events'][-1])
    ev['attempt_id'] = 'attempt-redelivery'
    ex['attempt_events'].append(ev)
    att = copy.deepcopy(ex['attempts'][0])
    att['attempt_id'] = 'attempt-redelivery'
    ex['attempts'].append(att)


def _s_all_observations_removed(art, other):
    art['journal']['observations'] = []
    art['journal']['reconciliations'] = []
    ex = art['executor_export']
    _need(ex['observations'] or ex['execution_result'].get('observation'), 'no observation present')
    ex['observations'] = []
    ex['execution_result']['observation'] = None


NEW_SEEDS = [
    ('c23.missing_approval.approval_inputs_removed_from_resolution_checks', 'missing_approval', _s_remove_approval_inputs),
    ('c23.missing_approval.approval_commitment_nulled_in_decision_binding', 'missing_approval', _s_null_approval_commitment),
    ('c23.missing_approval.approval_check_events_dropped', 'missing_approval', _s_drop_approval_check_events),
    ('c23.fabricated_completion.refused_case_claims_executed_and_acknowledged', 'fabricated_completion', _s_denied_case_claims_executed),
    ('c23.fabricated_completion.unknown_ack_case_claims_acknowledged', 'fabricated_completion', _s_unknown_case_claims_acknowledged),
    ('c23.fabricated_completion.journal_claims_dispatch_and_ack_without_attempt', 'fabricated_completion', _s_journal_claims_ack_without_attempt),
    ('c23.fabricated_completion.effects_removed_but_executed_claimed', 'fabricated_completion', _s_effects_removed_but_applied_claimed),
    ('c23.prohibited_access.effect_on_unauthorised_target', 'prohibited_access', _s_effect_unauthorised_target),
    ('c23.prohibited_access.envelope_and_effect_on_unauthorised_target', 'prohibited_access', _s_envelope_and_effect_target),
    ('c23.prohibited_access.effect_recorded_under_refused_authority', 'prohibited_access', _s_effect_under_refused_authority),
    ('c23.prohibited_access.effect_under_other_grant', 'prohibited_access', _s_effect_other_grant),
    ('c23.prohibited_access.decision_binds_other_target_than_effect', 'prohibited_access', _s_decision_binding_other_target),
    ('c23.duplicate_effect.second_effect_new_id_same_operation', 'duplicate_effect', _s_second_effect_new_id),
    ('c23.duplicate_effect.redelivery_second_executed_attempt', 'duplicate_effect', _s_redelivery_second_executed_event),
    ('c23.omitted_observation.every_observation_and_reconciliation_removed', 'omitted_observation', _s_all_observations_removed),
]


# ----------------------------------------------------------------------------------------------
# machinery
# ----------------------------------------------------------------------------------------------

def _base_for(family, ex):
    if family == 'producer':
        return {k: H.load_copy(ex, k) for k in ('journal', 'proposal', 'executor_export')}
    key = {'bundle': 'bundle', 'pack': 'pack', 'odes': 'odes', 'odes_rehashed': 'odes'}[family]
    return H.load_copy(ex, key)


def _catalogue(family, base):
    if family == 'producer':
        return H.producer_mutations()
    if family == 'bundle':
        return H.bundle_mutations(base)
    if family == 'pack':
        return H.pack_mutations(base)
    return H.odes_mutations(base, family == 'odes_rehashed')


def _evaluate(family, ex, planted):
    manifest = H.load_copy(ex, 'manifest')
    if family == 'producer':
        return H.summarise(H.evaluate_producer_exports(manifest, planted['journal'], planted['proposal'], planted['executor_export']))
    if family == 'bundle':
        return H.summarise(H.evaluate_bundle(manifest, planted))
    if family == 'pack':
        return H.summarise([H.eval_pack_artifact(planted)])
    return H.summarise([H.eval_odes_package(planted)])


def _row(sid, cls, family, case, source, applicable, verdict=None):
    r = {'seed': sid, 'class': cls, 'family': family, 'case': case, 'source': source, 'applicable': applicable}
    if verdict is not None:
        r.update(detected=bool(verdict['detected'] and verdict['why'] != ''), stage=verdict['first_detecting_stage'], how=verdict['verdict'], why=verdict['why'],
                 completed_without_detection=not verdict['detected'])
        if verdict['detected'] and not verdict['why']:
            r['note'] = 'typed verdict without a stated reason is not accepted as detection evidence'
    return r


def calibrate(runs, n):
    """Plant every mapped D08 mutation and every new C23 seed for every case of producer run ``n`` and evaluate."""
    table = []
    excluded = defaultdict(int)
    for case in CASES:
        ex = runs[(n, case)]
        other = lambda c, key, n=n: H.load_copy(runs[(n, c)], key)
        for family in FAMILIES:
            base = _base_for(family, ex)
            for mid, klass, _t, fn in _catalogue(family, base):
                cls = c23_class(mid, klass)
                if cls is None:
                    excluded[family] += 1
                    continue
                planted, changed = H.apply_mutation(base, fn, rehash=(family == 'odes_rehashed'))
                table.append(_row(mid, cls, family, case, 'D08-machinery', changed, _evaluate(family, ex, planted) if changed else None))
        base = _base_for('producer', ex)
        for sid, cls, fn in NEW_SEEDS:
            planted = copy.deepcopy(base)
            try:
                fn(planted, other)
            except (KeyError, IndexError, TypeError):
                table.append(_row(sid, cls, 'producer', case, 'C23-new', False))
                continue
            changed = planted != base
            table.append(_row(sid, cls, 'producer', case, 'C23-new', changed, _evaluate('producer', ex, planted) if changed else None))
    return table, dict(excluded)


def reverse_keys(obj):
    """Benign, semantics-preserving perturbation: JSON object key order reversed at every level."""
    if isinstance(obj, dict):
        return {k: reverse_keys(obj[k]) for k in reversed(list(obj))}
    if isinstance(obj, list):
        return [reverse_keys(x) for x in obj]
    return obj


def clean_evaluations(runs, n):
    """Every evaluator over every clean artifact (pristine and key-order-perturbed). Returns one row per evaluation."""
    rows = []
    for case in CASES:
        ex = runs[(n, case)]
        manifest = H.load_copy(ex, 'manifest')
        for variant, f in (('pristine', lambda o: o), ('key_order_reversed', reverse_keys)):
            journal, proposal, export = (f(H.load_copy(ex, k)) for k in ('journal', 'proposal', 'executor_export'))
            stages = H.evaluate_producer_exports(manifest, journal, proposal, export)
            rows.append(('producer_pipeline', variant, case, H.summarise(stages)))
            rows.append(('bundle_pipeline', variant, case, H.summarise(H.evaluate_bundle(manifest, f(H.load_copy(ex, 'bundle'))))))
            rows.append(('evidence_pack', variant, case, H.summarise([H.eval_pack_artifact(f(H.load_copy(ex, 'pack')))])))
            rows.append(('odes_package', variant, case, H.summarise([H.eval_odes_package(f(H.load_copy(ex, 'odes')))])))
    return [{'evaluator': e, 'variant': v, 'case': c, 'flagged': s['detected'], 'why': s['why']} for e, v, c, s in rows]


def signature(table):
    return sorted((r['class'], r['family'], r['case'], r['seed'], None if not r['applicable'] else (r['detected'], r['stage'], r['how'])) for r in table)


@pytest.fixture(scope='module')
def runs(pinned_reference, tmp_path_factory):
    """Two independent producer runs of every case; exported originals are proven unmodified at teardown."""
    root = tmp_path_factory.mktemp('c23-exports')
    built = {(n, case): H.build_exports(case, root / f'run-{n}') for n in (1, 2) for case in CASES}
    yield built
    for (n, case), ex in built.items():
        for name, expected in ex['sha256'].items():
            assert hashlib.sha256((ex['dir'] / name).read_bytes()).hexdigest() == expected, f'exported original {n}/{case}/{name} was modified'


@pytest.fixture(scope='module')
def calibration(runs):
    tables = {}
    excluded = None
    for n in (1, 2):
        tables[n], excluded = calibrate(runs, n)
    clean = {n: clean_evaluations(runs, n) for n in (1, 2)}
    return {'tables': tables, 'excluded': excluded, 'clean': clean}


def _summary(table, cls=None):
    rows = [r for r in table if r['applicable'] and (cls is None or r['class'] == cls)]
    missed = [r for r in rows if not r['detected']]
    by_family = {f: {'planted': sum(1 for r in rows if r['family'] == f), 'detected': sum(1 for r in rows if r['family'] == f and r['detected'])} for f in FAMILIES}
    return {'planted': len(rows), 'detected': len(rows) - len(missed), 'missed': len(missed),
            'detection_rate': round((len(rows) - len(missed)) / len(rows), 4) if rows else None, 'by_family': by_family,
            'missed_seeds': sorted(f"{r['family']}/{r['case']}/{r['seed']}" for r in missed)}


# ----------------------------------------------------------------------------------------------
# tests
# ----------------------------------------------------------------------------------------------

def test_scn_c23_source_identity_and_containment(request, record_property, runs):
    ref = H.reference()
    H.assert_pins_still_pristine()
    assert ref.profile['components']['runtime']['revision'] == H.FROZEN_RUNTIME
    assert ref.profile['components']['control_plane']['revision'] == H.FROZEN_CONTROL_PLANE
    for n in (1, 2):
        for case in CASES:
            ex = runs[(n, case)]
            assert ex['status'] == {'valid': 'executed', 'lost_ack': 'unknown', 'revoked': 'denied', 'unreadable': 'denied'}[case]
    H.record(request, record_property, 'c23_identity', {'scenario': 'C23', 'pins': ref.pins, 'cases': list(CASES),
                                                          'statuses': {c: runs[(1, c)]['status'] for c in CASES}, 'network': 'none'})


@pytest.mark.parametrize('cls', CLASSES)
def test_scn_c23_seeded_critical_defects_detected_by_class(request, record_property, calibration, cls):
    t1, t2 = calibration['tables'][1], calibration['tables'][2]
    s1 = _summary(t1, cls)
    comparison = H.compare_runs({'outcome': signature([r for r in t1 if r['class'] == cls])}, {'outcome': signature([r for r in t2 if r['class'] == cls])})
    rows = [r for r in t1 if r['class'] == cls]
    H.record(request, record_property, 'c23_class_detection', {
        'scenario': 'C23', 'class': cls, 'run_comparison': comparison, 'summary_run1': s1, 'summary_run2': _summary(t2, cls),
        'evaluators': {'E1': 'Replay -> Evidence Pack -> ODES consumers (D08 chain)'},
        'not_applicable_nothing_to_plant': sorted({f"{r['family']}/{r['case']}/{r['seed']}" for r in rows if not r['applicable']}),
        'table_run1': rows, 'table_run2': [r for r in t2 if r['class'] == cls],
        'detection_means': 'typed rejection or flag with a stated reason; an evaluator that completes without flagging is a miss'})
    assert comparison['verdict'] == 'MATCH', comparison
    assert s1['planted'] > 0, f'no {cls} defect could be planted'
    assert all(r['stage'] and r['how'] in ('rejected', 'flagged') for r in rows if r['applicable'] and r['detected']), 'a detection without a typed verdict was counted'
    assert not s1['missed'], (f"UNDETECTED seeded critical defects of class {cls}: {s1['missed']}/{s1['planted']} "
                              f"(detected {s1['detected']}): " + '; '.join(s1['missed_seeds'][:40]) + (' ...' if len(s1['missed_seeds']) > 40 else ''))


def test_scn_c23_every_class_planted_for_every_case_where_applicable(request, record_property, calibration):
    """Honest coverage: which classes could be planted in which cases (a refusal case has no completion/observation to remove)."""
    t = calibration['tables'][1]
    cover = {cls: {case: sum(1 for r in t if r['applicable'] and r['class'] == cls and r['case'] == case) for case in CASES} for cls in CLASSES}
    H.record(request, record_property, 'c23_coverage', {'scenario': 'C23', 'planted_by_class_and_case': cover,
                                                         'excluded_out_of_c23_scope_by_family': calibration['excluded'],
                                                         'seed_sources': {'D08-machinery': sum(1 for r in t if r['applicable'] and r['source'] == 'D08-machinery'),
                                                                          'C23-new': sum(1 for r in t if r['applicable'] and r['source'] == 'C23-new')}})
    for cls in CLASSES:
        assert cover[cls]['valid'] > 0 and cover[cls]['lost_ack'] > 0, f'{cls} not planted in an effect case: {cover[cls]}'
    assert cover['missing_approval']['revoked'] > 0 and cover['prohibited_access']['revoked'] > 0, 'refusal cases must carry planted defects too'


def test_scn_c23_clean_controls_report_false_alarm_rate(request, record_property, calibration):
    c1, c2 = calibration['clean'][1], calibration['clean'][2]
    comparison = H.compare_runs({'outcome': [(r['evaluator'], r['variant'], r['case'], r['flagged']) for r in c1]},
                                {'outcome': [(r['evaluator'], r['variant'], r['case'], r['flagged']) for r in c2]})
    flagged = [r for r in c1 if r['flagged']]
    per_eval = {e: {'clean_evaluations': sum(1 for r in c1 if r['evaluator'] == e), 'false_alarms': sum(1 for r in c1 if r['evaluator'] == e and r['flagged'])}
                for e in sorted({r['evaluator'] for r in c1})}
    H.record(request, record_property, 'c23_false_alarms', {
        'scenario': 'C23', 'run_comparison': comparison, 'clean_evaluations': len(c1), 'false_alarms': len(flagged),
        'false_positive_rate': round(len(flagged) / len(c1), 4), 'per_evaluator': per_eval,
        'false_alarm_rows': flagged, 'clean_variants': ['pristine export', 'JSON key order reversed at every level (semantics-preserving)'],
        'cases': list(CASES), 'run2_false_alarms': sum(1 for r in c2 if r['flagged'])})
    assert comparison['verdict'] == 'MATCH', comparison
    assert not flagged, f'FALSE ALARMS on clean controls ({len(flagged)}/{len(c1)}): {flagged}'


def test_scn_c23_overall_detection_and_false_alarm_report(request, record_property, calibration):
    """Retains the whole calibration table. Reports; the per-class tests carry the pass/fail assertions."""
    t = calibration['tables'][1]
    c = calibration['clean'][1]
    overall = _summary(t)
    per_class = {cls: _summary(t, cls) for cls in CLASSES}
    H.record(request, record_property, 'c23_overall', {
        'scenario': 'C23', 'overall': overall, 'by_class': per_class,
        'false_alarms': {'clean_evaluations': len(c), 'false_alarms': sum(1 for r in c if r['flagged']), 'rate': round(sum(1 for r in c if r['flagged']) / len(c), 4)},
        'excluded_out_of_c23_scope_by_family': calibration['excluded'],
        'completion_is_not_detection': 'rows with completed_without_detection=true ran every stage and were accepted; they are counted as misses',
        'table_run1': t})
    assert overall['planted'] > 0


def test_scn_c23_evaluators_are_alive_sentinels(request, record_property, runs):
    """Sentinels prove the evaluators can both flag and accept: a known-detectable planted commitment corruption must be detected,
    and its unmodified twin must be accepted, in both runs (a dead evaluator would pass or fail everything)."""
    out = []
    for n in (1, 2):
        ex = runs[(n, 'valid')]
        manifest = H.load_copy(ex, 'manifest')
        j, p, x = (H.load_copy(ex, k) for k in ('journal', 'proposal', 'executor_export'))
        clean = H.summarise(H.evaluate_producer_exports(manifest, j, p, x))
        j['check_events'][6]['proposal_commitment'] = 'sha256:' + '1' * 64
        planted = H.summarise(H.evaluate_producer_exports(manifest, j, p, x))
        out.append({'clean_detected': clean['detected'], 'planted_detected': planted['detected'], 'planted_stage': planted['first_detecting_stage']})
        assert not clean['detected'] and planted['detected'] and planted['why'], out[-1]
    comparison = H.compare_runs({'outcome': out[0]}, {'outcome': out[1]})
    H.record(request, record_property, 'c23_sentinels', {'scenario': 'C23', 'run_comparison': comparison, 'observed': out[0]})
    assert comparison['verdict'] == 'MATCH'


# ----------------------------------------------------------------------------------------------
# E2: the qualification hard-gate oracle (effect_gate) over independent destination observation
# ----------------------------------------------------------------------------------------------

def _e2_world(work):
    flow = H2.flow_b(work, effect_nos=(1,))
    part = flow.parts[0]
    res, exc = H2.execute_b(flow, part)
    assert res is not None and res.status == 'executed', (res, exc)
    return flow, part


def _db(flow):
    return sqlite3.connect(flow.dest.path)


def _e2_seeds():
    """(id, class, mutator(conn, part), expects_detection_by_effect_gate)."""
    def unapproved_row(conn, part):
        conn.execute("INSERT INTO effects(effect_id,operation_digest,grant_id,target,amount,unit,payload_json,state) VALUES(?,?,?,?,?,?,?,?)",
                     ('effect-ghost', 'sha256:' + 'a' * 64, 'urn:cognous:grant:ghost', OTHER_TARGET, 50.0, 'USD', '{}', 'applied'))

    def other_target_row_under_authorised_grant(conn, part):
        conn.execute("INSERT INTO effects(effect_id,operation_digest,grant_id,target,amount,unit,payload_json,state) "
                     "SELECT 'effect-other-target','sha256:' || ?,grant_id,?,amount,unit,payload_json,state FROM effects WHERE effect_id=?",
                     ('b' * 64, OTHER_TARGET, part.env.effect_id))

    def second_effect_same_operation(conn, part):
        conn.execute("INSERT INTO effects(effect_id,operation_digest,grant_id,target,amount,unit,payload_json,state) "
                     "SELECT 'effect-replay',operation_digest,grant_id,target,amount,unit,payload_json,state FROM effects WHERE effect_id=?", (part.env.effect_id,))

    def duplicate_executed_attempt(conn, part):
        for i in (1, 2):
            conn.execute('INSERT INTO attempts(attempt_id,effect_id,decision_id,operation_digest,created_at) VALUES(?,?,?,?,?)',
                         (f'attempt-dup-{i}', part.env.effect_id, part.env.decision_id, 'sha256:x', 10.0 + i))
            conn.execute('INSERT INTO attempt_events(attempt_id,status,error,created_at) VALUES(?,?,?,?)', (f'attempt-dup-{i}', 'executed', None, 10.0 + i))

    def altered_operation_digest(conn, part):
        conn.execute('UPDATE effects SET operation_digest=? WHERE effect_id=?', ('sha256:' + '0' * 64, part.env.effect_id))

    return [('unapproved_effect_row_for_unknown_effect_id', 'missing_approval', unapproved_row),
            ('effect_on_unauthorised_target_under_the_authorised_grant', 'prohibited_access', other_target_row_under_authorised_grant),
            ('second_effect_row_replaying_the_authorised_operation', 'duplicate_effect', second_effect_same_operation),
            ('two_executed_attempts_for_one_effect', 'duplicate_effect', duplicate_executed_attempt),
            ('authorised_effect_id_bound_to_altered_operation_digest', 'prohibited_access', altered_operation_digest)]


def test_scn_c23_effect_oracle_detects_seeded_effect_state_defects_and_passes_clean(request, record_property, tmp_path):
    """E2 calibration: ``effect_gate`` must flag each effect-state seed (a non-zero hard-gate counter) and report zero on the clean store."""
    def once(work):
        rows = []
        flow, part = _e2_world(work / 'clean')
        s = H2.db_summary(flow.dest.path)
        clean = H2.effect_gate(s, authorized_effect_ids={part.env.effect_id}, authorized_digests={H2.snapshot_digest(part.env)})
        for sid, cls, mutate in _e2_seeds():
            (work / sid).mkdir()
            f, p = _e2_world(work / sid)
            with _db(f) as conn:
                mutate(conn, p)
            gate = H2.effect_gate(H2.db_summary(f.dest.path), authorized_effect_ids={p.env.effect_id}, authorized_digests={H2.snapshot_digest(p.env)})
            rows.append({'seed': sid, 'class': cls, 'gate': gate, 'detected': (gate['unauthorized_effects'] + gate['excess_duplicate_effects']) > 0})
        return {'clean': clean, 'seeds': rows}
    runs_ = []
    for n in (1, 2):
        (tmp_path / f'run-{n}').mkdir()
        runs_.append(once(tmp_path / f'run-{n}'))
    comparison = H.compare_runs({'outcome': runs_[0]}, {'outcome': runs_[1]})
    missed = [r['seed'] for r in runs_[0]['seeds'] if not r['detected']]
    H.record(request, record_property, 'c23_effect_oracle', {'scenario': 'C23', 'evaluator': 'E2 effect_gate', 'run_comparison': comparison,
                                                              'clean_control_gate': runs_[0]['clean'], 'seeds': runs_[0]['seeds'], 'missed': missed})
    assert comparison['verdict'] == 'MATCH', comparison
    assert runs_[0]['clean'] == {'unauthorized_effects': 0, 'excess_duplicate_effects': 0}, f"false alarm on the clean store: {runs_[0]['clean']}"
    assert not missed, f'E2 missed seeded effect-state defects: {missed}'


def test_scn_c23_effect_oracle_scope_boundary_effect_without_consumed_claim(request, record_property, tmp_path):
    """REPORT-ONLY scope probe (no pass/fail on E2 here): a seeded 'missing approval' where the effect id/digest are authorised but the
    authorising claim was never consumed. ``effect_gate`` takes no claim input, so it cannot flag this; the scenario suites assert claim
    state separately through ``db_summary``. The probe records both the E2 verdict and the claim-aware cross-check verdict."""
    (tmp_path / 'w').mkdir()
    flow, part = _e2_world(tmp_path / 'w')
    with _db(flow) as conn:
        conn.execute("UPDATE execution_claims_v1 SET state='issued' WHERE claim_id=?", (part.claim.claim_id,))
    s = H2.db_summary(flow.dest.path)
    gate = H2.effect_gate(s, authorized_effect_ids={part.env.effect_id}, authorized_digests={H2.snapshot_digest(part.env)})
    cross_check = [e['effect_id'] for e in s['effects'] if C.claim_state(s, part.claim.claim_id) != 'consumed']
    C.write_report(request, record_property, 'effect_gate_scope_boundary', {
        'scenario': 'C23', 'seed': 'effect row present while its authorising claim is not consumed',
        'effect_gate_verdict': gate, 'effect_gate_detects': (gate['unauthorized_effects'] + gate['excess_duplicate_effects']) > 0,
        'claim_aware_cross_check_flags_effects': cross_check,
        'finding': 'effect_gate alone does not evaluate claim consumption; use of effect_gate as the sole oracle would miss this seed'})
    assert cross_check == [part.env.effect_id], 'the claim-aware cross-check must flag the seeded defect'
