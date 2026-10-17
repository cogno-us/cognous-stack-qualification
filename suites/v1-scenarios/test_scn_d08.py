"""SCN-D08 Audit and export: planted defects must be detected; unknown/missing/refused states must survive export.

SPDX-License-Identifier: Apache-2.0

Stimulus (catalog D08): drop, reorder, duplicate or corrupt events and remove observations.
Required observation: the evaluator detects planted defects; Replay and Evidence Pack preserve unknown, missing and
refused states without promoting them to verified.

Method. The frozen F5b seven-component reference produces real artifacts (Control Plane journal, executor export,
Replay reconstruction bundle, Evidence Pack, ODES package). Each is written to a temp directory. Defects are planted
ONLY in deep copies re-read from those exported files; the pinned checkouts and the exported originals are verified
byte-unchanged. The evaluators are the reference's own consumers: Replay ``import_bounded_workflow``, Evidence Pack
import + ``validate_evidence_pack``/loader, ODES export + recipient evaluation. Clean controls must not alarm.
Each test executes the whole scenario twice (two independent producer runs, owner decision D3) and compares the
normalised verdicts. A planted defect that no evaluator flags is a real miss and FAILS the test (never skipped).
"""
from __future__ import annotations

import hashlib
import json

import pytest

import _d06_d07_d08_helpers as H
from _d06_d07_d08_helpers import pinned_reference  # noqa: F401  (module fixture: pin identity before/after)

FAMILIES = ('producer', 'bundle', 'pack', 'odes', 'odes_rehashed')
STIMULUS_CLASSES = ('drop', 'reorder', 'duplicate', 'corrupt', 'remove_observation')


@pytest.fixture(scope='module')
def runs(pinned_reference, tmp_path_factory):
    """Two independent producer runs of every case, plus proof that exported originals are never modified."""
    root = tmp_path_factory.mktemp('d08-exports')
    built = {(n, case): H.build_exports(case, root / f'run-{n}') for n in (1, 2) for case in H.D08_CASES}
    yield built
    for (n, case), ex in built.items():
        for name, expected in ex['sha256'].items():
            actual = hashlib.sha256((ex['dir'] / name).read_bytes()).hexdigest()
            assert actual == expected, f'exported original {n}/{case}/{name} was modified (defects must be planted in copies only)'


def _catalogue(ex, family):
    """(mutation, base object) pairs for a family, loaded as copies from the exported files."""
    if family == 'producer':
        base = {k: H.load_copy(ex, k) for k in ('journal', 'proposal', 'executor_export')}
        return H.producer_mutations(), base
    if family == 'bundle':
        base = H.load_copy(ex, 'bundle')
        return H.bundle_mutations(base), base
    if family == 'pack':
        base = H.load_copy(ex, 'pack')
        return H.pack_mutations(base), base
    base = H.load_copy(ex, 'odes')
    return H.odes_mutations(base, family == 'odes_rehashed'), base


def _evaluate(family, ex, planted):
    manifest = H.load_copy(ex, 'manifest')
    if family == 'producer':
        return H.summarise(H.evaluate_producer_exports(manifest, planted['journal'], planted['proposal'], planted['executor_export']))
    if family == 'bundle':
        return H.summarise(H.evaluate_bundle(manifest, planted))
    if family == 'pack':
        return H.summarise([H.eval_pack_artifact(planted)])
    return H.summarise([H.eval_odes_package(planted)])


def _run_family(ex, family):
    mutations, base = _catalogue(ex, family)
    table = {}
    for mid, klass, _target, fn in mutations:
        planted, changed = H.apply_mutation(base, fn, rehash=(family == 'odes_rehashed'))
        if not changed:
            table[mid] = {'class': klass, 'applicable': False}
            continue
        verdict = _evaluate(family, ex, planted)
        table[mid] = {'class': klass, 'applicable': True, 'detected': verdict['detected'], 'stage': verdict['first_detecting_stage'],
                      'how': verdict['verdict'], 'why': verdict['why']}
    return table


def _signature(table):
    """Run-comparable form: identifiers stripped, detecting stage and verdict kept."""
    return {mid: (None if not row['applicable'] else (row['detected'], row['stage'], row['how'])) for mid, row in sorted(table.items())}


@pytest.mark.parametrize('case', H.D08_CASES)
@pytest.mark.parametrize('family', FAMILIES)
def test_scn_d08_planted_defects_detected(request, record_property, runs, family, case):
    t1 = _run_family(runs[(1, case)], family)
    t2 = _run_family(runs[(2, case)], family)
    comparison = H.compare_runs({'outcome': _signature(t1)}, {'outcome': _signature(t2)})
    applicable = {m: r for m, r in t1.items() if r['applicable']}
    missed = {m: r for m, r in applicable.items() if not r['detected']}
    by_class = {k: {'planted': sum(1 for r in applicable.values() if r['class'] == k),
                    'detected': sum(1 for r in applicable.values() if r['class'] == k and r['detected']),
                    'missed': sorted(m for m, r in missed.items() if r['class'] == k)} for k in STIMULUS_CLASSES}
    H.record(request, record_property, 'd08_planted_defects', {
        'scenario': 'D08', 'family': family, 'case': case, 'run_comparison': comparison,
        'run1': {'table': t1}, 'run2': {'table': t2},
        'planted': len(applicable), 'detected': len(applicable) - len(missed), 'missed': len(missed),
        'not_applicable_nothing_to_plant': sorted(m for m, r in t1.items() if not r['applicable']), 'by_class': by_class,
        'detection_means': 'any consumer stage rejecting (typed refusal/exception) or flagging (incomplete/invalid/new failing dimension)'})
    assert comparison['verdict'] == 'MATCH', comparison
    assert applicable, 'nothing could be planted for this family/case'
    assert not missed, ('UNDETECTED planted defects (' + str(len(missed)) + '/' + str(len(applicable)) + '): '
                        + '; '.join(f'{m} [{r["class"]}]' for m, r in sorted(missed.items())))


@pytest.mark.parametrize('case', H.D08_CASES)
def test_scn_d08_catalogue_covers_every_stimulus_class(runs, case):
    """Honest coverage: every stimulus class (drop/reorder/duplicate/corrupt/remove observations) was planted at least once per case."""
    ex = runs[(1, case)]
    planted = {k: 0 for k in STIMULUS_CLASSES}
    for family in FAMILIES:
        mutations, base = _catalogue(ex, family)
        for _mid, klass, _t, fn in mutations:
            _w, changed = H.apply_mutation(base, fn, rehash=(family == 'odes_rehashed'))
            planted[klass] += int(changed)
    # a refusal case has no observations or attempts to remove; the effect cases must cover all five classes
    required = STIMULUS_CLASSES if case in ('valid', 'lost_ack') else ('drop', 'reorder', 'duplicate', 'corrupt')
    assert all(planted[k] > 0 for k in required), planted


@pytest.mark.parametrize('case', H.D08_CASES)
def test_scn_d08_clean_controls_do_not_alarm(request, record_property, runs, case):
    """False-alarm control: unmodified exports are accepted by every evaluator, in both runs, with identical verdicts."""
    sigs = []
    for n in (1, 2):
        ex = runs[(n, case)]
        manifest = H.load_copy(ex, 'manifest')
        stages = H.evaluate_producer_exports(manifest, H.load_copy(ex, 'journal'), H.load_copy(ex, 'proposal'), H.load_copy(ex, 'executor_export'))
        stages += H.evaluate_bundle(manifest, H.load_copy(ex, 'bundle'))
        stages += [H.eval_pack_artifact(H.load_copy(ex, 'pack')), H.eval_odes_package(H.load_copy(ex, 'odes'))]
        assert all(s['verdict'] == 'accepted' for s in stages), stages
        sigs.append({'stages': [(s['stage'], s['verdict']) for s in stages], 'status': ex['status'], 'destination_effects': ex['destination_effects']})
    comparison = H.compare_runs({'outcome': sigs[0]}, {'outcome': sigs[1]})
    H.record(request, record_property, 'd08_clean_controls', {'scenario': 'D08', 'case': case, 'run_comparison': comparison, 'stages': sigs[0]})
    assert comparison['verdict'] == 'MATCH'


EXPECTED_STATES = {
    # case: (executor status, destination effects, acknowledgement, destination_observed, attempted, refusal code)
    'valid': ('executed', 1, 'received', 'applied', 'yes', None),
    'lost_ack': ('unknown', 1, 'unknown', 'applied', 'yes', None),
    'revoked': ('denied', 0, 'not_applicable', 'unknown', 'no', 'grant_revoked'),
    'unreadable': ('denied', 0, 'not_applicable', 'unknown', 'no', 'status_unreadable'),
}


@pytest.mark.parametrize('case', H.D08_CASES)
def test_scn_d08_unknown_missing_refused_states_preserved_not_verified(request, record_property, runs, case):
    """Replay, Evidence Pack and ODES keep unknown/missing/refused as such and never claim independent verification."""
    observed = []
    for n in (1, 2):
        ex = runs[(n, case)]
        status, effects, ack, destination, attempted, refusal = EXPECTED_STATES[case]
        bundle, pack, odes = H.load_copy(ex, 'bundle'), H.load_copy(ex, 'pack'), H.load_copy(ex, 'odes')
        ti = pack['metadata']['traceable_import']
        life = ti['lifecycle_summary']
        facts = odes['provenance']['execution_facts']
        # independent observation of the destination, not the executor's say-so
        assert ex['status'] == status and ex['destination_effects'] == effects
        # Replay bundle: producer-reported only, never independently verified
        assert bundle['semantics']['independent_effect_verification'] is False
        assert bundle['semantics']['destination_observation'] == 'producer_reported'
        assert bundle['semantics']['external_effect_execution'] is False and bundle['semantics']['policy_reevaluation'] is False
        # Evidence Pack lifecycle: exact states retained, nothing promoted to verified
        assert life['acknowledgement'] == ack and life['destination_observed'] == destination and life['execution_attempted'] == attempted
        assert life['independent_verification'] == 'unavailable' and life['retry_permission'] == 'not_established'
        assert ti['replay_semantics']['independent_effect_verification'] is False
        assert {u['code'] for u in ti['unresolved_issues']} >= {'U_INDEPENDENT_VERIFICATION_UNAVAILABLE'}
        # ODES: same facts, same non-promotion
        assert facts['acknowledgement_summary'] == ack and facts['destination_observed'] == destination
        assert facts['independent_delivery_verification'] == 'unavailable' and facts['retry_permission'] == 'not_established'
        if case == 'lost_ack':
            findings = [fi for r in bundle['import_reports'] for fi in r['findings']]
            assert any(fi['code'] == 'M002' and fi['value_state'] == 'unknown' for fi in findings), 'unknown value state lost'
            result = [r for r in bundle['records'] if r['record_type'] == 'execution_result'][0]['data']
            assert result['status'] == 'unknown' and result['acknowledged'] is False
        if refusal:
            assert ti['refusal_vocabulary_summary']['total_refusals'] == 1
            assert [s['code'] for s in ti['refusal_vocabulary_summary']['series']] == [refusal]
            assert len(facts['effect_time_refusal']) == 1 and not facts['destination_effects']
            assert refusal in json.dumps(facts['effect_time_refusal'])
        observed.append({'case': case, 'ack': life['acknowledgement'], 'destination_observed': life['destination_observed'],
                         'attempted': life['execution_attempted'], 'independent_verification': life['independent_verification'],
                         'refusals': ti['refusal_vocabulary_summary']['total_refusals']})
    comparison = H.compare_runs({'outcome': observed[0]}, {'outcome': observed[1]})
    H.record(request, record_property, 'd08_state_preservation', {'scenario': 'D08', 'case': case, 'run_comparison': comparison, 'observed': observed[0]})
    assert comparison['verdict'] == 'MATCH'
