"""SCN-D06 Ingress pressure: flood the reference's real ingress surfaces and observe refusal, effects and cost.

SPDX-License-Identifier: Apache-2.0

Required observation (catalog D06): typed refusal/saturation behaviour with zero unauthorized and zero excess duplicate
effects; CPU, memory, concurrency, storage and latency are MEASURED and REPORTED ONLY (owner decision D5: no pass/fail
threshold on any measured number, no performance claim). Hard gates asserted here:

* zero unauthorized effects  - observed by an independent read-only process on the destination SQLite store;
* zero excess duplicate effects - at most one effect per valid effect identity under concurrent duplicate delivery;
* evidence obligations - the one valid flow still reconstructs in Replay and is accepted by Evidence Pack and ODES.

The frozen F5b reference is a library: it has no network listener, request limiter or queue, and no ``INGRESS_SATURATED``
refusal. The scenario therefore floods the surfaces that do exist (runtime admission budgets, Control Plane decisions,
exchange assessment, model validation, the generation fence) and lists the rest as uncovered in each evidence record.
Each test executes twice under unchanged conditions (owner decision D3) and compares the normalised outcomes.
"""
from __future__ import annotations

import sqlite3
import sys
import threading
import time
from pathlib import Path

import pytest

import _d06_d07_d08_helpers as H
from _d06_d07_d08_helpers import pinned_reference  # noqa: F401

UNCOVERED = {
    'INGRESS_SATURATED typed refusal': 'not exercisable: the reference has no ingress limiter, rate limit, queue or concurrency cap to saturate',
    'rate / queue / concurrency limiting': 'absent from the reference; only per-request structural budgets exist (exercised)',
    'bounded rejection history': 'admission_rejections_v1, failure records and the Control Plane journal grow without bound (measured as storage growth)',
    'network transport pressure': 'no listener in the reference; ingress is a function call, so connection floods are not applicable',
}
PER_CLASS = 60
WORKERS = 8


def _meter(label, root):
    return H.Meter(label, watch_dirs=[root])


# ------------------------------------------------------------------ a. runtime admission flood
def _admission(root, monkeypatch):
    root.mkdir()
    w = H.ChainWorld(root, monkeypatch)
    cases = H.malformed_envelope_cases(w.env)
    tasks = [(klass, (lambda e=env: H.raw_execute(w, e))) for _ in range(PER_CLASS) for klass, env, _x in cases]
    expected = {k: x for k, _e, x in cases}
    phases = {}
    with _meter('admission_flood', root) as seq:
        out_seq = H.run_pool(tasks[: len(tasks) // 2], 1, seq)
    with _meter('admission_flood_concurrent', root) as par:
        out_par = H.run_pool(tasks[len(tasks) // 2:], WORKERS, par)
    outcomes = out_seq + out_par
    obs = H.observe_destination(w.dest.path)
    post = H.capture(lambda: H.raw_execute(w).status)
    obs_after = H.observe_destination(w.dest.path)
    typed = {}
    for klass, o in outcomes:
        typed.setdefault(klass, set()).add((o.get('raised'), o.get('message'), expected[klass] in o.get('message', '')))
    return {'outcome': {'by_class': {k: sorted(map(list, v)) for k, v in sorted(typed.items())}, 'n': len(outcomes),
                        'effects_after_flood': obs['effects'], 'rejection_rows': obs['admission_rejections'],
                        'post_flood_valid': post, 'effects_after_valid': len(obs_after['effects'])},
            'metrics': {'sequential_phase': seq.report(), 'concurrent_phase': par.report()}}


def test_scn_d06_malformed_runtime_admission_flood(request, record_property, pinned_reference, tmp_path, monkeypatch):
    r1, r2 = _admission(tmp_path / 'run-1', monkeypatch), _admission(tmp_path / 'run-2', monkeypatch)
    cmp_ = H.compare_runs(r1, r2)
    out = r1['outcome']
    H.record(request, record_property, 'd06_admission_flood', {
        'scenario': 'D06', 'surface': 'runtime admission budgets (SafeExecutor.execute)', 'run_comparison': cmp_, 'run1': r1, 'run2': r2,
        'uncovered_subcases': UNCOVERED, 'measurement_policy': 'report-only, no thresholds (owner decision D5)'})
    assert cmp_['verdict'] == 'MATCH', cmp_
    for klass, rows in out['by_class'].items():
        assert all(r[0] == 'ValueError' and r[2] is True for r in rows), (klass, rows)  # typed, budget-specific refusal
    assert out['effects_after_flood'] == [], 'unauthorized effect from malformed ingress'
    assert out['rejection_rows'] == [[out['n']]], 'every refusal is recorded (and the history is unbounded, see storage growth)'
    assert out['post_flood_valid']['returned'] == 'executed' and out['effects_after_valid'] == 1


# ------------------------------------------------------------------ b. model-boundary flood
def _model_flood(root, monkeypatch):
    root.mkdir()
    w = H.ChainWorld(root, monkeypatch)
    cases = H.malformed_proposal_cases()
    before = (w.journal_counts(), w.f.records.path.read_bytes() if w.f.records.path.exists() else b'')
    tasks = [(klass, (lambda kw=kw: type(w.p)(**kw))) for _ in range(PER_CLASS // 2) for klass, kw in cases]
    with _meter('model_boundary_flood', root) as m:
        outcomes = H.run_pool(tasks, WORKERS, m)
    after = (w.journal_counts(), w.f.records.path.read_bytes() if w.f.records.path.exists() else b'')
    obs = H.observe_destination(w.dest.path)
    by = {}
    for klass, o in outcomes:
        by.setdefault(klass, set()).add(o.get('raised', 'ACCEPTED'))
    return {'outcome': {'by_class': {k: sorted(v) for k, v in sorted(by.items())}, 'journal_unchanged': before == after, 'effects': obs['effects']},
            'metrics': m.report()}


def test_scn_d06_malformed_proposal_model_boundary_flood(request, record_property, pinned_reference, tmp_path, monkeypatch):
    r1, r2 = _model_flood(tmp_path / 'run-1', monkeypatch), _model_flood(tmp_path / 'run-2', monkeypatch)
    cmp_ = H.compare_runs(r1, r2)
    H.record(request, record_property, 'd06_model_flood', {'scenario': 'D06', 'surface': 'Control Plane proposal model validation', 'run_comparison': cmp_,
                                                          'run1': r1, 'run2': r2, 'uncovered_subcases': UNCOVERED})
    assert cmp_['verdict'] == 'MATCH', cmp_
    assert all(v == ['ValidationError'] for v in r1['outcome']['by_class'].values()), r1['outcome']['by_class']
    assert r1['outcome']['journal_unchanged'] and r1['outcome']['effects'] == []


# ------------------------------------------------------------------ c. unauthenticated Control Plane decisions
N_UNAUTH = 3


def _unauth(root, monkeypatch):
    root.mkdir()
    w = H.ChainWorld(root, monkeypatch)
    rows, held = {}, []
    tasks = []
    for i in range(N_UNAUTH):
        for klass, mut, _x in H.UNAUTH_PROPOSALS:
            tasks.append((klass, (lambda m=mut, i=i, k=klass: _decide(w, m(i), k, held))))
    with _meter('unauthenticated_control_plane_flood', root) as m:
        outcomes = H.run_pool(tasks, 1, m)
    for klass, o in outcomes:
        rows.setdefault(klass, set()).add(repr(o))
    reasons_ok = {klass: all(expected in held_reasons for held_reasons in [h['reasons'] for h in held if h['klass'] == klass]) for klass, _m, expected in H.UNAUTH_PROPOSALS}
    # a held decision is presented to the executor: effect-time refusal, no effect
    denied = []
    for h in held[: len(H.UNAUTH_PROPOSALS)]:
        denied.append(H.capture(lambda h=h: w.executor.execute(envelope=w.env, proposal=h['proposal'], decision=h['decision'], now=w.now).status))
    obs = H.observe_destination(w.dest.path)
    valid = H.capture(lambda: H.raw_execute(w))
    status = valid.get('returned') and valid['returned'].status
    t_ev = time.perf_counter()
    evidence = H.chain_evidence(w, valid['returned']) if valid.get('returned') else None
    t_ev = time.perf_counter() - t_ev
    obs2 = H.observe_destination(w.dest.path)
    return {'outcome': {'results': {k: sorted(v) for k, v in sorted(rows.items())}, 'reasons_contain_expected_code': reasons_ok, 'executor_with_held_decision': denied,
                        'effects_before_valid': obs['effects'], 'valid_status': status, 'effects_after_valid': len(obs2['effects']),
                        'evidence_stages': [(a, b) for a, b, _c in evidence or []]},
            'metrics': {'flood': m.report(), 'evidence_pipeline_seconds_after_flood': round(t_ev, 3), 'evidence_stage_reasons': [(a, b, c) for a, b, c in evidence or []], 'journal_decisions': w.journal_counts()['decisions'], 'journal_bytes': w.f.records.path.stat().st_size}}


def _decide(w, update, klass, held):
    proposal = w.p.model_copy(update=update)
    dec = w.f.decide(proposal, now=w.now)
    held.append({'klass': klass, 'reasons': list(dec.reasons), 'decision': dec, 'proposal': proposal})
    return {'result': str(dec.result), 'blocking_reason_count': len(dec.reasons)}


def test_scn_d06_unauthenticated_control_plane_flood(request, record_property, pinned_reference, tmp_path, monkeypatch):
    r1, r2 = _unauth(tmp_path / 'run-1', monkeypatch), _unauth(tmp_path / 'run-2', monkeypatch)
    cmp_ = H.compare_runs(r1, r2)
    out = r1['outcome']
    H.record(request, record_property, 'd06_unauthenticated_decisions', {'scenario': 'D06', 'surface': 'Control Plane decide + executor effect-time check',
                                                                         'run_comparison': cmp_, 'run1': r1, 'run2': r2, 'uncovered_subcases': UNCOVERED})
    assert cmp_['verdict'] == 'MATCH', cmp_
    assert all(out['reasons_contain_expected_code'].values()), out['reasons_contain_expected_code']
    assert all(set(v) and 'hold' in ''.join(v).lower() or 'deny' in ''.join(v).lower() or 'refus' in ''.join(v).lower() for v in out['results'].values()), out['results']
    assert out['effects_before_valid'] == [], 'unauthorized effect from an unauthenticated decision flood'
    assert out['valid_status'] == 'executed' and out['effects_after_valid'] == 1
    assert dict(out['evidence_stages']).get('replay_import') == 'accepted', out['evidence_stages']  # Replay still reconstructs; see the export test for Pack/ODES


# ------------------------------------------------------------------ d. unauthenticated exchange flood
def _exchange_flood(root, monkeypatch):
    root.mkdir()
    x = H.ExchangeWorld(root, monkeypatch)
    files_before = sorted(p.name for p in x.root.rglob('*') if p.is_file())
    typed = x.typed_attack_messages()
    tasks = [(k, (lambda b=b, i=i: x.deliver(b(i))[0])) for i in range(40) for k, b, _c in typed]
    with _meter('exchange_flood', root) as m:
        outcomes = H.run_pool(tasks, WORKERS, m)
    expected = {k: c for k, _b, c in typed}
    by = {}
    for klass, o in outcomes:
        r = o.get('returned')
        by.setdefault(klass, set()).add(repr((r['handling'], expected[klass] in r['errors'], r['attempted'])) if r else repr((o['raised'], o['message'])))
    confusion = x.type_confusion_messages()
    conf_tasks = [(k, (lambda b=b, i=i: x.deliver(b(i))[0])) for i in range(5) for k, b in confusion]
    with _meter('exchange_type_confusion', root) as mc:
        conf_out = H.run_pool(conf_tasks, 1, mc)
    obs = H.observe_destination(x.dest.path)
    before_valid = x.dest.effect_count(x.grant_id)
    valid, _ = x.deliver(x.message)
    obs2 = H.observe_destination(x.dest.path)
    confusion_kinds = {}
    for klass, o in conf_out:
        confusion_kinds.setdefault(klass, set()).add(o.get('raised') or o['returned']['handling'])
    return {'outcome': {'typed_by_class': {k: sorted(v) for k, v in sorted(by.items())}, 'effects_after_attacks': obs['effects'], 'effect_count_before_valid': before_valid,
                        'valid': valid, 'effects_after_valid': len(obs2['effects']),
                        'type_confusion_by_class': {k: sorted(v) for k, v in sorted(confusion_kinds.items())},
                        'files_created_by_attacks': sorted(set(files_before) ^ set(p.name for p in x.root.rglob('*') if p.is_file()) - {'exchange.sqlite'}) and None},
            'metrics': {'typed_flood': m.report(), 'type_confusion': mc.report()}}


def test_scn_d06_unauthenticated_exchange_flood(request, record_property, pinned_reference, tmp_path, monkeypatch):
    r1, r2 = _exchange_flood(tmp_path / 'run-1', monkeypatch), _exchange_flood(tmp_path / 'run-2', monkeypatch)
    cmp_ = H.compare_runs(r1, r2)
    out = r1['outcome']
    untyped = {k: v for k, v in out['type_confusion_by_class'].items() if any(x in ('TypeError', 'AttributeError', 'ValueError') for x in v)}
    H.record(request, record_property, 'd06_exchange_flood', {
        'scenario': 'D06', 'surface': 'exchange GAX assessment + run_exchange', 'run_comparison': cmp_, 'run1': r1, 'run2': r2, 'uncovered_subcases': UNCOVERED,
        'defect_observed_untyped_refusals_on_wrong_json_types': untyped,
        'note': 'wrong-typed fields surface as raw Python exceptions, not typed GAX refusals; no effect occurs (hard gate asserted)'})
    assert cmp_['verdict'] == 'MATCH', cmp_
    for klass, rows in out['typed_by_class'].items():
        assert len(rows) == 1 and rows[0].endswith('True, False)'), (klass, rows)  # typed error code present, no attempt
    assert out['effects_after_attacks'] == [] and out['effect_count_before_valid'] == 0, 'unauthorized effect from an unauthenticated exchange flood'
    assert out['effects_after_valid'] == 1, out['valid']


# ------------------------------------------------------------------ e. valid traffic under a mixed concurrent flood
def _mixed(root, monkeypatch):
    root.mkdir()
    base_root = root / 'baseline'
    base_root.mkdir()
    base = H.ChainWorld(base_root, monkeypatch)
    with _meter('baseline_valid_request', base_root) as mb:
        b = H.run_pool([('valid', lambda: H.raw_execute(base))], 1, mb)
    pressure_root = root / 'pressure'
    pressure_root.mkdir()
    w = H.ChainWorld(pressure_root, monkeypatch)
    cases = H.malformed_envelope_cases(w.env)
    flood = [(k, (lambda e=e: H.raw_execute(w, e))) for _ in range(20) for k, e, _x in cases]
    flood += [(k, (lambda m=m, i=i: w.f.decide(w.p.model_copy(update=m(i)), now=w.now))) for i in range(6) for k, m, _x in H.UNAUTH_PROPOSALS]
    valid_outcomes = []
    gate = threading.Barrier(2)

    def valid_traffic():
        gate.wait()
        valid_outcomes.append(H.capture(lambda: H.raw_execute(w).status))

    with _meter('valid_request_under_flood', pressure_root) as mp_:
        t = threading.Thread(target=valid_traffic)
        t.start()
        gate.wait()
        flood_out = H.run_pool(flood, WORKERS, mp_)
        t.join()
    obs = H.observe_destination(w.dest.path)
    retry = None
    if len(obs['effects']) == 0:
        retry = H.capture(lambda: H.raw_execute(w).status)  # availability is report-only; the effect gate is not
        obs = H.observe_destination(w.dest.path)
    result = H.capture(lambda: H.raw_execute(w))  # redelivery after the flood
    evidence = H.chain_evidence(w, result['returned']) if result.get('returned') else None
    obs_final = H.observe_destination(w.dest.path)
    effect_ids = {e[0] for e in obs_final['effects']}
    return {'outcome': {'effects_final': len(obs_final['effects']), 'distinct_effect_ids': len(effect_ids),
                        'effect_targets_and_grants': sorted({(e[1], e[2]) for e in obs_final['effects']}),
                        'redelivery_after_flood': (result.get('returned') and (result['returned'].status, result['returned'].newly_executed)) or result,
                        'evidence_stages': [(a, v) for a, v, _c in evidence or []]},
            'report_only': {'valid_completed_during_flood': valid_outcomes[0], 'needed_retry_after_flood': retry,
                            'flood_outcome_kinds': H.kinds([(k, o) for k, o in flood_out if isinstance(o, dict)])},
            'metrics': {'baseline': mb.report(), 'under_flood': mp_.report()}}


def test_scn_d06_valid_request_under_mixed_flood_keeps_effect_and_evidence_gates(request, record_property, pinned_reference, tmp_path, monkeypatch):
    r1, r2 = _mixed(tmp_path / 'run-1', monkeypatch), _mixed(tmp_path / 'run-2', monkeypatch)
    cmp_ = H.compare_runs(r1, r2)
    out = r1['outcome']
    H.record(request, record_property, 'd06_mixed_flood', {
        'scenario': 'D06', 'surface': 'valid flow concurrent with malformed-envelope and unauthenticated-decision flood', 'run_comparison': cmp_,
        'run1': r1, 'run2': r2, 'uncovered_subcases': UNCOVERED, 'measurement_policy': 'report-only, no thresholds (owner decision D5)',
        'hard_gates': {'unauthorized_effects': 'effects whose grant/target differ from the single authorized flow', 'excess_duplicate_effects': 'effects beyond one per effect id'}})
    assert cmp_['verdict'] == 'MATCH', cmp_
    assert out['effects_final'] == 1 and out['distinct_effect_ids'] == 1, 'excess duplicate or unauthorized effect under pressure'
    assert len(out['effect_targets_and_grants']) == 1
    assert out['redelivery_after_flood'] == ('executed', False) or out['redelivery_after_flood'][1] is False, out['redelivery_after_flood']
    assert dict(out['evidence_stages']).get('replay_import') == 'accepted', ('Replay evidence broken by the flood', out['evidence_stages'])


# ------------------------------------------------------------------ f. concurrent duplicate valid deliveries
K = 8


def _duplicates(root, monkeypatch):
    root.mkdir()
    w = H.ChainWorld(root, monkeypatch)
    gate = threading.Barrier(K)

    def deliver():
        gate.wait()
        return (lambda r: (r.status, r.newly_executed))(H.raw_execute(w))
    with _meter('chain_duplicate_deliveries', root) as mc:
        out = H.run_pool([('dup', deliver)] * K, K, mc)
    obs = H.observe_destination(w.dest.path)
    sequential = H.capture(lambda: (lambda r: (r.status, r.newly_executed))(H.raw_execute(w)))
    chain = {'effects': len(obs['effects']), 'newly_executed_claims': sum(1 for _k, o in out if o.get('returned') and o['returned'][1]),
             'attempts_table': obs['attempts'], 'sequential_redelivery': sequential, 'kinds': H.kinds(out)}
    # exchange flow
    xr = root / 'exchange'
    xr.mkdir()
    x = H.ExchangeWorld(xr, monkeypatch)
    gate2 = threading.Barrier(K)

    def xdeliver():
        gate2.wait()
        return (lambda o: (o['handling'], o['newly_executed']))(x.deliver(x.message)[0])
    with _meter('exchange_duplicate_deliveries', xr) as mx:
        xout = H.run_pool([('dup', xdeliver)] * K, K, mx)
    xobs = H.observe_destination(x.dest.path)
    xseq = H.capture(lambda: (lambda o: (o['handling'], o['newly_executed'], o['attempt_status']))(x.deliver(x.message)[0]))
    exch = {'effects': len(xobs['effects']), 'newly_executed_claims': sum(1 for _k, o in xout if o.get('returned') and o['returned'][1]),
            'sequential_redelivery': xseq, 'kinds': H.kinds(xout)}
    return {'outcome': {'chain_effects': chain['effects'], 'chain_new_claims': chain['newly_executed_claims'], 'chain_sequential': chain['sequential_redelivery'],
                        'exchange_effects': exch['effects'], 'exchange_new_claims': exch['newly_executed_claims'], 'exchange_sequential': exch['sequential_redelivery']},
            'report_only': {'chain': chain, 'exchange': exch}, 'metrics': {'chain': mc.report(), 'exchange': mx.report()}}


def test_scn_d06_concurrent_duplicate_deliveries_at_most_one_effect(request, record_property, pinned_reference, tmp_path, monkeypatch):
    r1, r2 = _duplicates(tmp_path / 'run-1', monkeypatch), _duplicates(tmp_path / 'run-2', monkeypatch)
    cmp_ = H.compare_runs(r1, r2)
    out = r1['outcome']
    H.record(request, record_property, 'd06_duplicates', {'scenario': 'D06', 'surface': f'{K} simultaneous deliveries of one valid operation (chain and exchange)',
                                                         'run_comparison': cmp_, 'run1': r1, 'run2': r2, 'uncovered_subcases': UNCOVERED,
                                                         'note': 'raw per-thread outcome kinds are report-only (race timing); the effect count is the gate'})
    assert cmp_['verdict'] == 'MATCH', cmp_
    assert out['chain_effects'] == 1 and out['chain_new_claims'] == 1, 'excess duplicate effect on the chain flow'
    assert out['exchange_effects'] == 1 and out['exchange_new_claims'] <= 1, 'excess duplicate effect on the exchange flow'


# ------------------------------------------------------------------ g. generation-fence refusal saturation
STALE = 300


def _fence(root):
    root.mkdir()
    from experiments.odex_gax_imx_reference.generation_fence import GenerationFenceClaim, GenerationFenceRefusal, LineageGenerationFence
    path = root / 'lineage.sqlite'
    with sqlite3.connect(path, isolation_level=None) as c:
        c.execute('CREATE TABLE heads(conversation_id TEXT PRIMARY KEY, packet_id TEXT NOT NULL, packet_digest TEXT NOT NULL, state_version INTEGER NOT NULL)')
        c.execute("INSERT INTO heads VALUES('conv-1','p','d',4)")
    fence = LineageGenerationFence(path)

    class Dest:
        def __init__(self):
            self.effects = []
            self.lock = threading.Lock()

        def commit(self, snapshot, *, simulate=None):
            with self.lock:
                self.effects.append(snapshot.effect_id)
            return {'status': 'applied'}

    class Snap:
        def __init__(self, e):
            self.effect_id = e
    dest = Dest()

    def stale(i):
        try:
            fence.wrap_destination(dest, GenerationFenceClaim('conv-1', f'e{i}', 3)).commit(Snap(f'e{i}'))
            return 'committed'
        except GenerationFenceRefusal as exc:
            return 'refused:' + H.normalise_reason(exc)
    with _meter('generation_fence_refusal_flood', root) as m:
        out = H.run_pool([('stale', (lambda i=i: stale(i))) for i in range(STALE)], WORKERS, m)
    counters = fence.counters('conv-1')
    rows = len(fence.refusals('conv-1'))
    stale_effects = len(dest.effects)
    current = fence.wrap_destination(dest, GenerationFenceClaim('conv-1', 'good', 4)).commit(Snap('good'))
    return {'outcome': {'results': sorted({str(o.get('returned') or o) for _k, o in out}), 'total': counters['total_refusals'], 'persisted_rows': rows,
                        'persisted_counter': counters['persisted_refusals'], 'suppressed': counters['suppressed_refusals'], 'stale_effects': stale_effects,
                        'current_claim': current, 'effects_final': list(dest.effects)},
            'metrics': m.report()}


def test_scn_d06_generation_fence_refusal_flood_is_bounded(request, record_property, pinned_reference, tmp_path):
    sys.path.insert(0, str(pinned_reference.paths['exchange']))
    r1, r2 = _fence(tmp_path / 'run-1'), _fence(tmp_path / 'run-2')
    cmp_ = H.compare_runs(r1, r2)
    out = r1['outcome']
    H.record(request, record_property, 'd06_generation_fence', {'scenario': 'D06', 'surface': 'LineageGenerationFence stale-claim flood (typed refusal, bounded evidence)',
                                                               'run_comparison': cmp_, 'run1': r1, 'run2': r2, 'uncovered_subcases': UNCOVERED})
    assert cmp_['verdict'] == 'MATCH', cmp_
    assert out['results'] == ['refused:superseded_lineage_generation']
    assert out['stale_effects'] == 0
    assert out['total'] == STALE and out['persisted_rows'] == out['persisted_counter'] == 64 and out['suppressed'] == STALE - 64
    assert out['effects_final'] == ['good']


# ------------------------------------------------------------------ h. evidence survives unauthorized ingress
def _evidence_after_noise(root, monkeypatch, holds):
    root.mkdir()
    w = H.ChainWorld(root, monkeypatch)
    for i in range(holds):
        w.f.decide(w.p.model_copy(update={'actor': f'intruder-{i}'}), now=w.now)
    result = H.raw_execute(w)
    stages = H.chain_evidence(w, result)
    return {'outcome': {'holds_before_valid': holds, 'effects': w.effects(), 'stages': [(a, b, H.normalise_reason(c)) for a, b, c in stages]}}


def test_scn_d06_valid_flow_export_survives_unauthorized_hold(request, record_property, pinned_reference, tmp_path, monkeypatch):
    """One unauthenticated, held proposal sharing the journal must not stop the valid flow's evidence export.

    Hard-gate side (effects) holds. Evidence side is asserted honestly: if ODES refuses to export the valid flow because of the
    unrelated held decision, that is a real ingress-pressure finding and this test FAILS (it is not skipped or weakened).
    """
    control1, control2 = _evidence_after_noise(tmp_path / 'c1', monkeypatch, 0), _evidence_after_noise(tmp_path / 'c2', monkeypatch, 0)
    noisy1, noisy2 = _evidence_after_noise(tmp_path / 'n1', monkeypatch, 1), _evidence_after_noise(tmp_path / 'n2', monkeypatch, 1)
    cmp_control, cmp_noisy = H.compare_runs(control1, control2), H.compare_runs(noisy1, noisy2)
    H.record(request, record_property, 'd06_evidence_after_noise', {'scenario': 'D06', 'control_no_noise': {'run1': control1, 'run2': control2, 'run_comparison': cmp_control},
                                                                   'one_unauthorized_hold': {'run1': noisy1, 'run2': noisy2, 'run_comparison': cmp_noisy},
                                                                   'uncovered_subcases': UNCOVERED})
    assert cmp_control['verdict'] == cmp_noisy['verdict'] == 'MATCH'
    assert all(v == 'accepted' for _s, v, _w in control1['outcome']['stages']), control1  # the control must be clean
    assert noisy1['outcome']['effects'] == 1  # effect gate holds
    assert all(v == 'accepted' for _s, v, _w in noisy1['outcome']['stages']), ('evidence for the valid flow blocked by one unauthorized hold', noisy1['outcome']['stages'])
