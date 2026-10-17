"""SCN-C12 Producer / consumer compatibility (executed against the frozen F5b seven-component reference).

SPDX-License-Identifier: Apache-2.0

Stimulus (catalog C12): import ACTUAL pinned Control Plane + executor outputs into Replay and Evidence Pack (and the ODES
consumer that reads their product); vary schema versions and break references. Required observation: supported records
preserve identifiers and outcomes; invalid references and unsupported versions fail explicitly; field loss is reported.

Producers: the frozen F5b Control Plane (a34c3dc2) journal + the executor producer export (runtime 4a83b175) for nine real
runs (valid, lost_ack, race, unreadable, revoked, purpose_closed, purpose_reopened, tampered_evidence, input_dropped), written
to disk and re-read. Consumers: Replay ``import_bounded_workflow`` (def0ee0f), Evidence Pack importer/validator (505a3590)
and the ODES exporter/recipient evaluator (5675f1b9). Defects are planted ONLY in deep copies re-read from the exported files;
the pinned checkouts and the exported originals are verified byte-unchanged. Each case runs twice (two independent producer
runs, D3) and the normalised observations are compared.

Honest outcomes: a version or reference variant that no consumer rejects/flags, and an injected field that is neither
rejected, reported nor preserved, FAIL the test (never skipped).
"""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

import _c_2b_helpers as C
from _c_2b_helpers import pinned_reference  # noqa: F401  (module fixture: pin identity before/after)

H2 = C.H2
CASES = ('valid', 'lost_ack', 'race', 'unreadable', 'revoked', 'purpose_closed', 'purpose_reopened', 'tampered_evidence', 'input_dropped')


@pytest.fixture(scope='module')
def runs(pinned_reference, tmp_path_factory):
    root = tmp_path_factory.mktemp('c12-exports')
    built = {(n, case): H2.build_exports(case, root / f'run-{n}') for n in (1, 2) for case in CASES}
    yield built
    for (n, case), ex in built.items():
        for name, expected in ex['sha256'].items():
            assert hashlib.sha256((ex['dir'] / name).read_bytes()).hexdigest() == expected, f'exported original {n}/{case}/{name} was modified'


def loaded(ex):
    return {k: H2.load_copy(ex, k) for k in ex['objects_on_disk']}


def cp_revision():
    return C.reference().chain.CONTROL_PLANE_RUNTIME_AUTHORITY_REVISION


def replay_import(journal, proposal, export, rev=None):
    from agent_replay_bundle.importers import import_bounded_workflow
    try:
        bundle = import_bounded_workflow(journal, proposal=proposal, moltbot_export=export, control_plane_revision=rev or cp_revision())
    except Exception as exc:
        return None, {'stage': 'replay_import', 'verdict': 'rejected', 'why': type(exc).__name__ + ': ' + H2.normalise_reason(exc)}
    flags = H2._flag_replay(bundle)
    return bundle, {'stage': 'replay_import', 'verdict': 'flagged' if flags else 'accepted', 'why': ','.join(flags)}


def odes_layers(package, policy=None):
    """Recipient layers as {name: status}; the policy supports the F5b profile so a clean package reaches its real verdicts."""
    from odes import evaluate_recipient_package
    pol = {'supported_profiles': ['odes_cognous_stack_export_0_2'], **(policy or {})}
    try:
        res = evaluate_recipient_package(package, pol)
    except Exception as exc:
        return {'raised': type(exc).__name__ + ': ' + H2.normalise_reason(exc)}
    return {k: v['status'] for k, v in res.items() if isinstance(v, dict) and 'status' in v}


def records(bundle, kind):
    return [r for r in bundle['records'] if r['record_type'] == kind]


# ------------------------------------------------------------------------------------------------
# 1. identifiers and outcomes survive producer -> Replay -> Evidence Pack -> ODES
# ------------------------------------------------------------------------------------------------
LIFECYCLE = {  # case -> (executor status, ack, destination_observed, attempted) for the four cases whose end state is fixed by the reference
    'valid': ('executed', 'received', 'applied', 'yes'), 'lost_ack': ('unknown', 'unknown', 'applied', 'yes'),
    'revoked': ('denied', 'not_applicable', 'unknown', 'no'), 'unreadable': ('denied', 'not_applicable', 'unknown', 'no')}
DECISION_WORDS = {'authorized': 'authorized', 'hold': 'held', 'denied': 'denied'}


def _preservation(ex, checks):
    o = loaded(ex)
    j, export, bundle, pack, odes = o['journal'], o['executor_export'], o['bundle'], o['pack'], o['odes']
    truth = {'decision_ids': sorted(d['decision_id'] for d in j['decisions']), 'effect_ids': sorted({d['effect_id'] for d in j['decisions']}),
             'results': sorted(d['result'] for d in j['decisions']), 'refusal_reasons': sorted(r for x in j['refusals'] for r in x['reasons']),
             'exec_status': export['execution_result']['status'], 'exec_attempt': export['execution_result']['attempt_id'],
             'executor_attempts': sorted(a['attempt_id'] for a in export['attempts']),
             'cp_attempts': sorted({a['attempt_id'] for a in j['attempts']}), 'destination_effects': ex['destination_effects']}
    ids = lambda kind, key: sorted({r['identifiers'][key] for r in records(bundle, kind) if key in r['identifiers']})  # noqa: E731
    checks.equal(ids('runtime_decision', 'decision_id'), truth['decision_ids'], 'Replay keeps every Control Plane decision id')
    checks.equal(ids('runtime_decision', 'effect_id'), truth['effect_ids'], 'Replay keeps every effect id')
    checks.equal(ids('execution_envelope', 'decision_id'), [export['execution_envelope']['decision_id']], 'Replay keeps the executor envelope decision id')
    checks.equal(sorted(r['data']['status'] for r in records(bundle, 'execution_result')), [truth['exec_status']], 'Replay keeps the executor outcome')
    checks.equal(ids('execution_result', 'attempt_id'), [truth['exec_attempt']] if truth['exec_attempt'] else [], 'Replay keeps the executor attempt id')
    checks.equal(ids('destination_attempt', 'attempt_id'), truth['executor_attempts'], 'Replay keeps every executor attempt id')
    checks.equal(ids('control_plane_attempt_transition', 'attempt_id'), truth['cp_attempts'], 'Replay keeps every Control Plane attempt id')
    checks.equal(len(records(bundle, 'destination_effect')), truth['destination_effects'], 'Replay keeps the durable destination effect count (independently observed)')
    checks.equal(sorted(r for x in records(bundle, 'effect_time_refusal') for r in x['data']['reasons']), truth['refusal_reasons'], 'Replay keeps refusal reasons')
    ti = pack['metadata']['traceable_import']
    dc = ti['derived_counts']
    checks.equal(dc['decision_count'], len(truth['decision_ids']), 'Evidence Pack decision count')
    checks.equal(dc['authorization_granted_count'], sum(1 for r in truth['results'] if r == 'authorized'), 'Evidence Pack authorization count')
    checks.equal(dc['destination_effect_count'], truth['destination_effects'], 'Evidence Pack destination effect count')
    checks.equal(ti['refusal_vocabulary_summary']['total_refusals'], len(j['refusals']), 'Evidence Pack refusal count')
    life = ti['lifecycle_summary']
    facts = odes['provenance']['execution_facts']
    dfacts = odes['provenance']['decision_facts']
    checks.equal(odes['record']['decision_id'] in truth['decision_ids'], True, 'ODES record carries a Control Plane decision id')
    checks.equal(dfacts['decision_result'], DECISION_WORDS.get(truth['results'][0], truth['results'][0]), 'ODES decision result')
    checks.equal(len(facts['destination_effects']), truth['destination_effects'], 'ODES destination effects')
    checks.equal((facts['acknowledgement_summary'], facts['destination_observed']), (life['acknowledgement'], life['destination_observed']), 'ODES and Pack agree on acknowledgement/observation')
    checks.equal(facts['independent_delivery_verification'], 'unavailable', 'no consumer promotes producer evidence to independent verification')
    if ex['status'] and (ex['dir'].name in LIFECYCLE):
        status, ack, observed, attempted = LIFECYCLE[ex['dir'].name]
        if ex['dir'].name == 'lost_ack':
            status = H2.lost_ack_status()
        checks.equal((truth['exec_status'], life['acknowledgement'], life['destination_observed'], life['execution_attempted']), (status, ack, observed, attempted), 'declared end state of the case')
    return {'decisions': len(truth['decision_ids']), 'authorization': truth['results'], 'exec_status': truth['exec_status'], 'destination_effects': truth['destination_effects'],
            'refusals': truth['refusal_reasons'], 'attempts': {'executor': len(truth['executor_attempts']), 'control_plane': len(truth['cp_attempts'])},
            'pack': {'decision_count': dc['decision_count'], 'granted': dc['authorization_granted_count'], 'ack': life['acknowledgement'],
                     'destination_observed': life['destination_observed'], 'attempted': life['execution_attempted']},
            'odes': {'decision_result': dfacts['decision_result'], 'ack': facts['acknowledgement_summary'], 'observed': facts['destination_observed']},
            'consumers_reported_complete': all(r['complete'] for r in bundle['import_reports'])}


@pytest.mark.parametrize('case', CASES)
def test_scn_c12_supported_records_preserve_identifiers_and_outcomes(request, record_property, runs, tmp_path, case):
    def trial_for(n):
        def trial(work, mp, checks):
            return _preservation(runs[(n, case)], checks)
        return trial
    # the two independent producer runs are the two executions (D3); both are checked and compared
    observed = []
    violations = []
    for n in (1, 2):
        checks = C.Checks()
        observed.append(_preservation(runs[(n, case)], checks))
        violations.append(list(checks.violations))
    comparison = H2.compare_runs({'outcome': observed[0]}, {'outcome': observed[1]})
    H2.record(request, record_property, 'c12_preservation', {
        'scenario': 'C12', 'case': case, 'run_comparison': comparison, 'run1': {'observed': observed[0], 'violations': violations[0]},
        'run2': {'observed': observed[1], 'violations': violations[1]}, 'verdict': 'FAIL' if violations[0] or violations[1] or comparison['verdict'] != 'MATCH' else 'PASS',
        'hard_gate_applied': False, 'note': 'consumers only; the producers ran the hard-gated D5 flows in batch 1'})
    assert not violations[0] and not violations[1], violations
    assert comparison['verdict'] == 'MATCH', comparison


# ------------------------------------------------------------------------------------------------
# 2. unsupported versions fail explicitly
# ------------------------------------------------------------------------------------------------
HISTORICAL_CP = '248d899634d9db3518e831bc7ab568a48733f825'  # an exact, supported-for-OTHER-generations Control Plane pin

VERSION_VARIANTS = {
    # id: (stage, description)
    'replay_control_plane_revision_unknown': ('replay_import', 'Control Plane revision that matches no supported profile'),
    'replay_control_plane_revision_other_generation': ('replay_import', 'valid supported revision of another generation against this generation\'s export'),
    'replay_executor_envelope_version': ('replay_import', 'executor ExecutionEnvelope version 9.9.9'),
    'replay_executor_profile_id': ('replay_import', 'unknown executor producer profile id'),
    'replay_executor_profile_version': ('replay_import', 'executor producer profile version 1.0.0 (not the 2.0.0 contract)'),
    'replay_executor_repository_revision': ('replay_import', 'executor producer repository revision outside the supported set'),
    'pack_bundle_version': ('pack_import', 'Reconstruction Bundle version 0.3.0'),
    'pack_manifest_version': ('pack_import', 'Action Manifest version 2.0'),
    'odes_manifest_version': ('odes_export', 'Action Manifest version 2.0'),
    'odes_bundle_version': ('odes_export', 'Reconstruction Bundle version 0.3.0'),
    'odes_package_version': ('odes_recipient', 'ODES package_version 9.9.9'),
    'odes_package_type': ('odes_recipient', 'unknown ODES package_type'),
    'odes_implementation_profile_version': ('odes_recipient', 'ODES implementation_profile_version of another generation'),
    'odes_implementation_profile': ('odes_recipient', 'unknown ODES implementation_profile'),
    'odes_schema_version': ('odes_recipient', 'ODES record schema_version 9.9'),
    'odes_pinned_replay_revision': ('odes_recipient', 'ODES provenance pins a different Replay revision'),
    'odes_pinned_control_plane_revision': ('odes_recipient', 'ODES provenance pins a different Control Plane revision'),
}


def _apply_version(variant, o):
    j, p, e, manifest, bundle, odes = (copy.deepcopy(o[k]) for k in ('journal', 'proposal', 'executor_export', 'manifest', 'bundle', 'odes'))
    if variant == 'replay_control_plane_revision_unknown':
        return replay_import(j, p, e, rev='0' * 40)[1]
    if variant == 'replay_control_plane_revision_other_generation':
        return replay_import(j, p, e, rev=HISTORICAL_CP)[1]
    if variant == 'replay_executor_envelope_version':
        e['execution_envelope']['version'] = '9.9.9'
    elif variant == 'replay_executor_profile_id':
        e['producer_profile']['profile_id'] = 'urn:other:producer'
    elif variant == 'replay_executor_profile_version':
        e['producer_profile']['profile_version'] = '1.0.0'
    elif variant == 'replay_executor_repository_revision':
        e['repository']['revision'] = '0' * 40
    elif variant == 'pack_bundle_version':
        bundle['bundle_version'] = '0.3.0'
        return H2.eval_pack_from_bundle(manifest, bundle)
    elif variant in ('pack_manifest_version', 'odes_manifest_version'):
        for k in ('manifest_version', 'version', 'schema_version'):
            if k in manifest:
                manifest[k] = '2.0'
        return H2.eval_pack_from_bundle(manifest, bundle) if variant == 'pack_manifest_version' else H2.eval_odes_from_bundle(manifest, bundle)
    elif variant == 'odes_bundle_version':
        bundle['bundle_version'] = '0.3.0'
        return H2.eval_odes_from_bundle(manifest, bundle)
    if variant.startswith('replay_'):
        return replay_import(j, p, e)[1]
    # ODES package variants are judged by the recipient layers
    if variant == 'odes_package_version':
        odes['package_version'] = '9.9.9'
    elif variant == 'odes_package_type':
        odes['package_type'] = 'other_package'
    elif variant == 'odes_implementation_profile_version':
        odes['profile']['implementation_profile_version'] = 'odes-cognous-stack-export-0.2.3-security-runtime-candidate'
    elif variant == 'odes_implementation_profile':
        odes['profile']['implementation_profile'] = 'odes_other_profile'
    elif variant == 'odes_schema_version':
        odes['record']['schema_version'] = '9.9'
    elif variant == 'odes_pinned_replay_revision':
        odes['provenance']['pinned_revisions']['replay'] = '0' * 40
    elif variant == 'odes_pinned_control_plane_revision':
        odes['provenance']['pinned_revisions']['control_plane'] = '0' * 40
    layers = odes_layers(odes)
    bad = sorted(k for k, v in layers.items() if k != 'raised' and k not in ('recipient_reliance_decision',) and v in ('fail', 'unsupported', 'not_evaluated'))
    baseline_bad = {'consumption_conditions'}  # fails on every clean export under an empty recipient policy
    flagged = sorted(set(bad) - baseline_bad)
    return {'stage': 'odes_recipient', 'verdict': 'rejected' if 'raised' in layers else ('flagged' if flagged else 'accepted'),
            'why': layers.get('raised') or ','.join(flagged), 'layers': layers}


@pytest.mark.parametrize('variant', sorted(VERSION_VARIANTS))
def test_scn_c12_unsupported_version_fails_explicitly(request, record_property, runs, tmp_path, variant):
    def observe(n):
        o = loaded(runs[(n, 'valid')])
        v = _apply_version(variant, o)
        return {'stage': v['stage'], 'verdict': v['verdict'], 'why': H2.normalise_reason(v['why'])}
    a, b = observe(1), observe(2)
    comparison = H2.compare_runs({'outcome': a}, {'outcome': b})
    H2.record(request, record_property, 'c12_versions', {'scenario': 'C12', 'variant': variant, 'description': VERSION_VARIANTS[variant][1],
                                                         'run_comparison': comparison, 'run1': a, 'run2': b, 'hard_gate_applied': False,
                                                         'verdict': 'FAIL' if a['verdict'] == 'accepted' or comparison['verdict'] != 'MATCH' else 'PASS'})
    assert a['verdict'] != 'accepted', f'unsupported version silently accepted: {variant}: {a}'
    assert comparison['verdict'] == 'MATCH', comparison


def test_scn_c12_clean_controls_are_accepted_by_every_consumer(request, record_property, runs, tmp_path):
    """Detector control: the unmodified exports pass every consumer, so the rejections above are caused by the planted variant."""
    sigs = []
    for n in (1, 2):
        o = loaded(runs[(n, 'valid')])
        stages = H2.evaluate_producer_exports(o['manifest'], o['journal'], o['proposal'], o['executor_export'])
        stages += [H2.eval_pack_artifact(o['pack']), H2.eval_odes_package(o['odes'])]
        layers = odes_layers(o['odes'])
        sigs.append({'stages': [(s['stage'], s['verdict']) for s in stages], 'odes_layers': layers})
        assert all(s['verdict'] == 'accepted' for s in stages), stages
        assert layers['declared_profile_conformance'] == 'pass' and layers['package_content_integrity'] == 'pass' and layers['schema_validity'] == 'pass', layers
    comparison = H2.compare_runs({'outcome': sigs[0]}, {'outcome': sigs[1]})
    H2.record(request, record_property, 'c12_controls', {'scenario': 'C12', 'run_comparison': comparison, 'observed': sigs[0], 'hard_gate_applied': False})
    assert comparison['verdict'] == 'MATCH'


# ------------------------------------------------------------------------------------------------
# 3. broken references fail explicitly
# ------------------------------------------------------------------------------------------------

def _journal(fn):
    return lambda j, p, e, b, pk, od: fn(j)


def _export(fn):
    return lambda j, p, e, b, pk, od: fn(e)


def _bundle(fn):
    return lambda j, p, e, b, pk, od: fn(b)


def _first(items, pred=lambda x: True):
    return next(x for x in items if pred(x))


def _drop_cp_decision(j):
    j['decisions'].clear()


def _attempt_dangling(j):
    j['attempts'][0]['decision_id'] = 'absent-decision'


def _recon_dangling(j):
    j['reconciliations'][0]['effect_id'] = 'sha256:' + '0' * 64


def _observation_dangling(j):
    j['observations'][0]['effect_id'] = 'sha256:' + '0' * 64


def _refusal_dangling(j):
    j['refusals'][0]['effect_id'] = 'sha256:' + '0' * 64


def _check_event_dangling(j):
    next(x for x in j['check_events'] if x.get('decision_id'))['decision_id'] = 'absent-decision'


def _envelope_decision(e):
    e['execution_envelope']['decision_id'] = 'absent-decision'


def _result_effect(e):
    e['execution_result']['effect_id'] = 'sha256:' + '0' * 64


def _attempt_identity(e):
    e['attempt_identity'] = {'namespace': 'executor', 'attempt_id': 'absent-attempt'} if isinstance(e['attempt_identity'], dict) else 'absent-attempt'


def _effect_row_dangling(e):
    e['effects'][0]['effect_id'] = 'sha256:' + '0' * 64


def _attempt_event_dangling(e):
    e['attempt_events'][0]['attempt_id'] = 'absent-attempt'


def _link_target_missing(b):
    b['links'][0]['to_record_id'] = 'absent-record'


def _commitment_source_missing(b):
    b['commitments'][0]['source_record_id'] = 'absent-record'


def _duplicate_record_id(b):
    b['records'].append(copy.deepcopy(b['records'][0]))


def _link_from_missing(b):
    b['links'][0]['from_record_id'] = 'absent-record'


def _drop_referenced_record(b):
    target = b['links'][0]['to_record_id']
    b['records'] = [r for r in b['records'] if r['record_id'] != target]


REF_VARIANTS = {
    # id: (case, layer, mutate)
    'cp_decision_dropped_but_attempts_remain': ('valid', 'producer', _journal(_drop_cp_decision)),
    'cp_attempt_references_absent_decision': ('valid', 'producer', _journal(_attempt_dangling)),
    'cp_reconciliation_references_absent_effect': ('valid', 'producer', _journal(_recon_dangling)),
    'cp_observation_references_absent_effect': ('valid', 'producer', _journal(_observation_dangling)),
    'cp_refusal_references_absent_effect': ('revoked', 'producer', _journal(_refusal_dangling)),
    'cp_check_event_references_absent_decision': ('valid', 'producer', _journal(_check_event_dangling)),
    'executor_envelope_references_absent_decision': ('valid', 'producer', _export(_envelope_decision)),
    'executor_result_references_absent_effect': ('valid', 'producer', _export(_result_effect)),
    'executor_attempt_identity_references_absent_attempt': ('valid', 'producer', _export(_attempt_identity)),
    'executor_effect_row_references_absent_effect': ('valid', 'producer', _export(_effect_row_dangling)),
    'executor_attempt_event_references_absent_attempt': ('valid', 'producer', _export(_attempt_event_dangling)),
    'bundle_link_to_absent_record': ('valid', 'bundle', _bundle(_link_target_missing)),
    'bundle_link_from_absent_record': ('valid', 'bundle', _bundle(_link_from_missing)),
    'bundle_commitment_names_absent_source_record': ('valid', 'bundle', _bundle(_commitment_source_missing)),
    'bundle_duplicate_record_id': ('valid', 'bundle', _bundle(_duplicate_record_id)),
    'bundle_referenced_record_removed': ('valid', 'bundle', _bundle(_drop_referenced_record)),
}


@pytest.mark.parametrize('variant', sorted(REF_VARIANTS))
def test_scn_c12_broken_reference_fails_explicitly(request, record_property, runs, tmp_path, variant):
    case, layer, mutate = REF_VARIANTS[variant]

    def observe(n):
        o = loaded(runs[(n, case)])
        j, p, e, b, pk, od = (copy.deepcopy(o[k]) for k in ('journal', 'proposal', 'executor_export', 'bundle', 'pack', 'odes'))
        before = json.dumps([j, e, b], sort_keys=True)
        try:
            mutate(j, p, e, b, pk, od)
        except (KeyError, IndexError, StopIteration, TypeError) as exc:
            return {'not_applicable': f'{type(exc).__name__}'}
        if before == json.dumps([j, e, b], sort_keys=True):
            return {'not_applicable': 'mutation changed nothing'}
        stages = (H2.evaluate_producer_exports(o['manifest'], j, p, e) if layer == 'producer' else H2.evaluate_bundle(o['manifest'], b))
        s = H2.summarise(stages)
        return {'layer': layer, 'detected': s['detected'], 'first_detecting_stage': s['first_detecting_stage'], 'verdict': s['verdict'], 'why': s['why']}
    a, b2 = observe(1), observe(2)
    comparison = H2.compare_runs({'outcome': a}, {'outcome': b2})
    H2.record(request, record_property, 'c12_references', {'scenario': 'C12', 'variant': variant, 'case': case, 'run_comparison': comparison, 'run1': a, 'run2': b2,
                                                           'hard_gate_applied': False,
                                                           'verdict': 'FAIL' if not a.get('detected') or comparison['verdict'] != 'MATCH' else 'PASS'})
    assert 'not_applicable' not in a, f'variant could not be planted: {a}'
    assert a['detected'], f'broken reference NOT detected by any consumer: {variant}: {a}'
    assert comparison['verdict'] == 'MATCH', comparison


def test_scn_c12_odes_retained_source_reference_removal_is_detected(request, record_property, runs, tmp_path):
    """ODES package whose provenance references a retained record that is no longer in its retained bundle."""
    def observe(n):
        o = loaded(runs[(n, 'valid')])
        od = copy.deepcopy(o['odes'])
        retained = od['provenance']['retained_sources']['reconstruction_bundle']
        target = od['provenance']['source_record_refs'][0]['record_id']
        retained['records'] = [r for r in retained['records'] if r['record_id'] != target]
        layers = odes_layers(H2.odes_rehash(od))  # digests recomputed so integrity cannot be the detecting layer
        return {'layers': layers, 'semantic': layers.get('replay_semantic_consistency'), 'reliance': layers.get('recipient_reliance_decision')}
    a, b = observe(1), observe(2)
    comparison = H2.compare_runs({'outcome': a}, {'outcome': b})
    H2.record(request, record_property, 'c12_odes_retained', {'scenario': 'C12', 'run_comparison': comparison, 'run1': a, 'run2': b, 'hard_gate_applied': False})
    assert a['semantic'] == 'fail' and a['reliance'] != 'pass', a
    assert comparison['verdict'] == 'MATCH'


# ------------------------------------------------------------------------------------------------
# 4. field loss is reported (never silent)
# ------------------------------------------------------------------------------------------------
MARKER = 'zz_unknown_member_c12'
FIELD_VARIANTS = {
    # id: (layer, plant(j, p, e, b))
    'journal_top_level_member': ('producer', lambda j, p, e, b: j.update({MARKER: 'x'})),
    'journal_decision_member': ('producer', lambda j, p, e, b: j['decisions'][0].update({MARKER: 'x'})),
    'journal_attempt_member': ('producer', lambda j, p, e, b: j['attempts'][0].update({MARKER: 'x'})),
    'executor_export_top_level_member': ('producer', lambda j, p, e, b: e.update({MARKER: 'x'})),
    'executor_result_member': ('producer', lambda j, p, e, b: e['execution_result'].update({MARKER: 'x'})),
    'executor_repository_member': ('producer', lambda j, p, e, b: e['repository'].update({MARKER: 'x'})),
    'executor_producer_profile_member': ('producer', lambda j, p, e, b: e['producer_profile'].update({MARKER: 'x'})),
    'executor_effect_row_member': ('producer', lambda j, p, e, b: e['effects'][0].update({MARKER: 'x'})),
    'bundle_top_level_member': ('bundle', lambda j, p, e, b: b.update({MARKER: 'x'})),
    'bundle_record_data_member': ('bundle', lambda j, p, e, b: b['records'][0]['data'].update({MARKER: 'x'})),
}


def _fate(layer, planted, o):
    """Where did the planted unknown member end up? One of rejected / reported / preserved / SILENTLY_LOST."""
    j, p, e, b = planted
    manifest = o['manifest']
    if layer == 'producer':
        bundle, verdict = replay_import(j, p, e)
        if bundle is None:
            return {'fate': 'rejected', 'where': 'replay_import', 'why': verdict['why']}
        bdict = bundle.model_dump(mode='json')
    else:
        bdict = b
    findings = [f for r in bdict['import_reports'] for f in r['findings']]
    base_findings = [f for r in o['bundle']['import_reports'] for f in r['findings']]
    new_findings = [f for f in findings if f not in base_findings]
    reported_marker = [f['code'] for f in new_findings if MARKER in json.dumps(f)]
    incomplete = (bdict['status'] != 'reconstruction_complete') or not all(r['complete'] for r in bdict['import_reports'])
    downstream = {'bundle': MARKER in json.dumps(bdict)}
    try:
        from agent_governance_evidence_pack.importer import import_manifest_reconstruction
        downstream['pack'] = MARKER in json.dumps(import_manifest_reconstruction(manifest, bdict).model_dump(mode='json'))
    except Exception as exc:
        return {'fate': 'rejected', 'where': 'pack_import', 'why': type(exc).__name__}
    try:
        from odes import export_cognous_stack_package
        downstream['odes'] = MARKER in json.dumps(export_cognous_stack_package(manifest, bdict))
    except Exception as exc:
        return {'fate': 'rejected', 'where': 'odes_export', 'why': type(exc).__name__}
    if reported_marker or (incomplete and layer == 'producer' and not downstream['bundle']):
        return {'fate': 'reported', 'finding_codes': reported_marker, 'incomplete': incomplete, 'downstream': downstream}
    if all(downstream.values()):
        return {'fate': 'preserved', 'downstream': downstream}
    if incomplete:
        return {'fate': 'reported', 'finding_codes': [], 'incomplete': True, 'downstream': downstream}
    return {'fate': 'SILENTLY_LOST', 'downstream': downstream}


@pytest.mark.parametrize('variant', sorted(FIELD_VARIANTS))
def test_scn_c12_unknown_member_is_rejected_reported_or_preserved_never_silently_lost(request, record_property, runs, tmp_path, variant):
    layer, plant = FIELD_VARIANTS[variant]

    def observe(n):
        o = loaded(runs[(n, 'valid')])
        planted = tuple(copy.deepcopy(o[k]) for k in ('journal', 'proposal', 'executor_export', 'bundle'))
        plant(*planted)
        return _fate(layer, planted, o)
    a, b = observe(1), observe(2)
    comparison = H2.compare_runs({'outcome': a}, {'outcome': b})
    H2.record(request, record_property, 'c12_field_loss', {'scenario': 'C12', 'variant': variant, 'layer': layer, 'run_comparison': comparison, 'run1': a, 'run2': b,
                                                           'hard_gate_applied': False,
                                                           'verdict': 'FAIL' if a['fate'] == 'SILENTLY_LOST' or comparison['verdict'] != 'MATCH' else 'PASS'})
    assert a['fate'] != 'SILENTLY_LOST', f'field loss NOT reported: an unknown member planted in {variant} vanished from every consumer with the import reported complete: {a}'
    assert comparison['verdict'] == 'MATCH', comparison


@pytest.mark.parametrize('case', ('valid', 'lost_ack', 'revoked'))
def test_scn_c12_known_conversion_losses_and_unsupported_semantics_are_enumerated(request, record_property, runs, tmp_path, case):
    """Replay import warnings reach the Evidence Pack as conversion losses; ODES states what pder-v0.1 cannot carry."""
    def observe(n):
        o = loaded(runs[(n, case)])
        reports = [f['code'] for r in o['bundle']['import_reports'] for f in r['findings']]
        losses = o['pack']['metadata']['traceable_import']['conversion_losses']
        unresolved = [u['code'] for u in o['pack']['metadata']['traceable_import']['unresolved_issues']]
        unsupported = o['odes']['provenance']['unsupported_semantics']
        return {'replay_finding_codes': sorted(reports), 'pack_loss_codes': sorted(x['code'] for x in losses), 'pack_unresolved': sorted(unresolved),
                'odes_unsupported_semantics': len(unsupported), 'odes_limits': len(o['odes']['provenance']['limits'])}
    a, b = observe(1), observe(2)
    comparison = H2.compare_runs({'outcome': a}, {'outcome': b})
    violations = []
    if sorted(a['replay_finding_codes']) != a['pack_loss_codes']:
        violations.append(f'Replay findings {a["replay_finding_codes"]} are not carried into Evidence Pack conversion losses {a["pack_loss_codes"]}')
    if not a['odes_unsupported_semantics'] or not a['odes_limits']:
        violations.append('ODES package states no unsupported semantics / limits')
    H2.record(request, record_property, 'c12_losses', {'scenario': 'C12', 'case': case, 'run_comparison': comparison, 'run1': a, 'run2': b, 'violations': violations,
                                                       'hard_gate_applied': False})
    assert not violations, violations
    assert comparison['verdict'] == 'MATCH'
