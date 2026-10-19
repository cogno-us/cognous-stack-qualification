"""SCN-C14 Optional ODES consumer (executed against the frozen F5b seven-component reference).

SPDX-License-Identifier: Apache-2.0

Stimulus (catalog C14): export the supported optional ODES mapping and read it with a separate compatible consumer.
Required observation: declared versions validate; lineage and uncertainty survive; envelope validity does not grant
authority or prove delivery.

The ODES package is exported (odes 5675f1b9 ``export_cognous_stack_package``) from the real Replay bundle of four real
producer runs (frozen Control Plane a34c3dc2 + executor 4a83b175; valid, lost_ack, revoked, unreadable), written to disk,
and then read by a SEPARATE consumer: a fresh Python process whose import path holds only the ODES and Replay source trees
(no Control Plane, executor, Evidence Pack, hub or exchange code) reading the exported file. The in-process recipient
evaluator is also exercised for the policy and forgery variants. Each case runs twice (two independent producer runs, D3).
The producer directory (journal + SQLite destination) is snapshotted byte for byte around every read: a read must create
no effect and renew no authorization.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

import _c_2b_helpers as C
from _c_2b_helpers import pinned_reference  # noqa: F401
import _pins  # noqa: E402  (suites/ is on sys.path via the shared helpers)

H2 = C.H2
CASES = ('valid', 'lost_ack', 'revoked', 'unreadable')
PROFILE_ID = 'odes_cognous_stack_export_0_2'
POLICY = {'supported_profiles': [PROFILE_ID]}
EXPECTED_EFFECTS = {'valid': 1, 'lost_ack': 1, 'revoked': 0, 'unreadable': 0}
# end state fixed by the frozen reference (same ground truth as C12): case -> (acknowledgement_summary, destination_observed)
TRUTH = {'valid': ('received', 'applied'), 'lost_ack': ('unknown', 'applied'), 'revoked': ('not_applicable', 'unknown'),
         'unreadable': ('not_applicable', 'unknown')}
PINS = dict(_pins.C14_PINS)

SEPARATE_CONSUMER = r'''
import json, os, sys
import odes.recipient_validator as _rv
COMPONENT_ROOTS = ('odes', 'agent_replay_bundle', 'agent_governance_evidence_pack', 'moltbot_safe',
                   'cognous_control_plane', 'agent_governance_control_plane', 'tests', 'gax_imx', 'exchange')
WORKER_LOG = sys.argv[3]
# The recipient evaluator (ODES 39a3c6ce, #117) runs the Replay semantic check in a forked worker, so the
# Replay tree is imported in the worker and not in this process. The worker's own import set is recorded before it sends its
# result (the parent kills a live worker as soon as it has the result), so "loaded" below is the union of both processes.
_orig_worker = _rv._worker
def _recording_worker(fn, conn):
    def run():
        try:
            return fn()
        finally:
            with open(WORKER_LOG, 'a') as handle:
                handle.write(json.dumps(sorted({m.split('.')[0] for m in sys.modules} & set(COMPONENT_ROOTS))) + '\n')
    return _orig_worker(run, conn)
_rv._worker = _recording_worker
from odes import evaluate_recipient_package
pkg = json.load(open(sys.argv[1]))
policy = json.loads(sys.argv[2])
res = evaluate_recipient_package(pkg, policy)
loaded = {m.split('.')[0] for m in sys.modules} & set(COMPONENT_ROOTS)
worker = [json.loads(line) for line in open(WORKER_LOG).read().splitlines()] if os.path.exists(WORKER_LOG) else []
for roots in worker:
    loaded |= set(roots)
print(json.dumps({'layers': {k: v['status'] for k, v in res.items() if isinstance(v, dict) and 'status' in v},
                  'reasons': {k: v['reasons'] for k, v in res.items() if isinstance(v, dict) and 'reasons' in v},
                  'semantic_workers': len(worker),
                  'loaded_component_roots': sorted(loaded)},
                 sort_keys=True))
'''


@pytest.fixture(scope='module')
def runs(pinned_reference, tmp_path_factory):
    root = tmp_path_factory.mktemp('c14-exports')
    built = {(n, case): H2.build_exports(case, root / f'run-{n}') for n in (1, 2) for case in CASES}
    yield built
    for (n, case), ex in built.items():
        for name, expected in ex['sha256'].items():
            assert hashlib.sha256((ex['dir'] / name).read_bytes()).hexdigest() == expected, f'exported original {n}/{case}/{name} was modified'


def _n(work):
    return int(work.name.split('-')[1])


def separate_consumer(path, policy, only=('odes',)):
    ref = C.reference()
    roots = {'odes': ref.paths['odes'] / 'src', 'replay': ref.paths['replay'] / 'src'}
    env = {k: v for k, v in os.environ.items() if k not in ('PYTHONPATH',)}
    env['PYTHONPATH'] = os.pathsep.join(str(roots[k]) for k in ('odes', 'replay') if k in only or k == 'odes' and False) if False else \
        os.pathsep.join(str(roots[k]) for k in (('odes', 'replay') if 'replay' in only else ('odes',)))
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    with tempfile.TemporaryDirectory() as scratch:
        out = subprocess.run([sys.executable, '-s', '-c', SEPARATE_CONSUMER, str(path), json.dumps(policy), os.path.join(scratch, 'worker-roots.jsonl')],
                             env=env, capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        raise RuntimeError(f'separate consumer failed: {out.stderr[-400:]}')
    return json.loads(out.stdout)


def in_process(package, policy=None):
    from odes import evaluate_recipient_package
    res = evaluate_recipient_package(package, policy or POLICY)
    return {k: v['status'] for k, v in res.items() if isinstance(v, dict) and 'status' in v}


def _effects(ex):
    return H2.sqlite_rows if False else ex['destination_effects']


def _gate(case, ex):
    effects = ex['destination_effects']
    return {'unauthorized_effects': effects if EXPECTED_EFFECTS[case] == 0 else 0,
            'excess_duplicate_effects': max(0, effects - 1)}


# ---------------------------------------------------------------------------------------------------------
# 1. Declared versions validate in a separate consumer; the read creates no effect
# ---------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize('case', CASES)
def test_scn_c14_declared_versions_validate_in_separate_consumer(request, record_property, tmp_path, runs, case):
    def trial(work, mp, checks):
        ex = runs[(_n(work), case)]
        pkg = H2.load_copy(ex, 'odes')
        before = C.tree_snapshot(ex['dir'] / 'producer')
        out = separate_consumer(ex['objects_on_disk']['odes'], POLICY, only=('odes', 'replay'))
        layers = out['layers']
        for layer in ('schema_validity', 'replay_semantic_consistency', 'declared_profile_conformance', 'package_content_integrity'):
            checks.equal(layers.get(layer), 'pass', f'separate consumer: {layer}')
        checks.equal(layers, in_process(pkg), 'separate consumer and in-process evaluator agree layer for layer')
        checks.equal(pkg['package_type'], 'odes_decision_evidence_export_package', 'package_type')
        checks.equal(pkg['package_version'], '0.1.0', 'package_version')
        prof = pkg['profile']
        checks.equal(prof['implementation_profile'], PROFILE_ID, 'declared implementation profile')
        checks.equal(prof['schema_name'] + '/' + prof['schema_version'], 'pder-v0.1/0.1', 'declared record schema')
        checks.equal(pkg['record']['verification']['conformance_profile'], PROFILE_ID, 'record and package declare the same profile')
        sel = pkg['provenance']['selected_revisions']
        for name, sha in PINS.items():
            checks.equal(sel.get(name), sha, f'selected revision {name} is the frozen pin')
        checks.equal(pkg['provenance']['pinned_revisions'], sel, 'pinned and selected revisions agree')
        checks.equal(pkg['provenance']['supported_revisions']['control_plane'], [PINS['control_plane']], 'supported Control Plane revisions')
        loaded = out['loaded_component_roots']
        checks.equal(loaded, ['agent_replay_bundle', 'odes'], 'separate consumer (this process and its semantic worker) loaded only the ODES and Replay trees (no producer code)')
        checks.equal(out['semantic_workers'], 1, 'the Replay semantic check ran in exactly one worker of the separate consumer')
        checks.equal(C.tree_snapshot(ex['dir'] / 'producer'), before, 'reading the package left the producer tree (journal + destination) byte-identical')
        return {'case': case, 'layers': layers, 'declared': {'package_type': pkg['package_type'], 'package_version': pkg['package_version'], 'profile': PROFILE_ID},
                'selected_revisions_are_frozen_pins': True, 'loaded_component_roots': loaded, 'producer_tree_unchanged': True, **_gate(case, ex)}
    C.run_c_case(request, record_property, tmp_path, 'C14', trial)


def test_scn_c14_separate_consumer_without_replay_fails_closed(request, record_property, tmp_path, runs):
    def trial(work, mp, checks):
        ex = runs[(_n(work), 'lost_ack')]
        out = separate_consumer(ex['objects_on_disk']['odes'], POLICY, only=('odes',))
        # ODES #113 (ad80fd7c): an absent Replay distribution is a dependency gap, classed 'unavailable' (not a contradiction in the package,
        # so not 'fail'; never 'pass'); it still blocks reliance. docs/recipient-validation.md, "Replay check separates three situations".
        checks.equal(out['layers']['replay_semantic_consistency'], 'unavailable', 'a consumer that lacks the pinned Replay validator reports the semantic layer unavailable, never pass')
        checks.expect(any('Replay validator is unavailable' in r and 'cognous-agent-replay-bundle' in r for r in out['reasons']['replay_semantic_consistency']), 'the reason names the missing validator')
        checks.equal(out['layers']['recipient_reliance_decision'], 'fail', 'reliance is refused (not pass, not informational) without the semantic layer')
        checks.equal(out['layers']['package_content_integrity'], 'pass', 'the independent layers still evaluate')
        return {'layers': out['layers'], 'reason': out['reasons']['replay_semantic_consistency']}
    C.run_c_case(request, record_property, tmp_path, 'C14', trial, gate=False)


# ---------------------------------------------------------------------------------------------------------
# 2. Version / profile variants fail explicitly
# ---------------------------------------------------------------------------------------------------------
VERSION_VARIANTS = {
    'package_type_unknown': (lambda p: p.__setitem__('package_type', 'odes_other_package'), 'schema_validity', 'not_evaluated'),
    'package_version_unsupported': (lambda p: p.__setitem__('package_version', '9.9.9'), None, None),
    'profile_unsupported': (lambda p: p['profile'].__setitem__('implementation_profile', 'odes_cognous_stack_export_9_9'), 'declared_profile_conformance', 'fail'),
    'profile_version_unsupported': (lambda p: p['profile'].__setitem__('implementation_profile_version', 'odes-cognous-stack-export-9.9.9'), None, None),
    'record_profile_mismatch': (lambda p: p['record']['verification'].__setitem__('conformance_profile', 'odes_other_profile'), 'declared_profile_conformance', 'fail'),
    'schema_version_unsupported': (lambda p: p['profile'].__setitem__('schema_version', '9.9'), None, None),
    'selected_control_plane_revision_unknown': (lambda p: p['provenance']['selected_revisions'].__setitem__('control_plane', 'f' * 40), None, None),
    'replay_required_revision_changed': (lambda p: p['provenance']['replay_validation'].__setitem__('required_revision', 'e' * 40), None, None),
}


@pytest.mark.parametrize('variant', sorted(VERSION_VARIANTS))
def test_scn_c14_version_variant_is_flagged_not_validated(request, record_property, tmp_path, runs, variant):
    fn, layer, status = VERSION_VARIANTS[variant]

    def trial(work, mp, checks):
        ex = runs[(_n(work), 'lost_ack')]
        base = H2.load_copy(ex, 'odes')
        for rehash in (False, True):
            q = copy.deepcopy(base)
            fn(q)
            checks.expect(q != base, f'{variant}: plant changed the package')
            if rehash:
                H2.odes_rehash(q)
            try:
                layers = in_process(q)
            except Exception as exc:
                layers = {'raised': type(exc).__name__}
            flagged = layers.get('raised') is not None or any(v not in ('pass', 'unavailable') for k, v in layers.items() if k not in ('consumption_conditions',)) \
                or layers.get('recipient_reliance_decision') != 'pass'
            non_pass_core = [k for k in ('schema_validity', 'replay_semantic_consistency', 'declared_profile_conformance', 'package_content_integrity')
                             if layers.get(k) not in (None, 'pass')]
            checks.expect(bool(non_pass_core) or layers.get('raised') is not None or layers.get('schema_validity') == 'not_evaluated',
                          f'{variant} (rehash={rehash}): an unsupported version/profile/revision must fail a core layer, observed {layers}')
            checks.expect(layers.get('recipient_reliance_decision', 'fail') != 'pass', f'{variant}: reliance must not pass')
            if layer and not rehash:
                checks.equal(layers.get(layer), status, f'{variant}: {layer}')
        q = copy.deepcopy(base)
        fn(q)
        out = in_process(q)
        return {'variant': variant, 'layers_without_rehash': out}
    C.run_c_case(request, record_property, tmp_path, 'C14', trial, gate=False)


def test_scn_c14_recipient_policy_not_supporting_the_profile_is_refused(request, record_property, tmp_path, runs):
    def trial(work, mp, checks):
        ex = runs[(_n(work), 'lost_ack')]
        pkg = H2.load_copy(ex, 'odes')
        layers = in_process(pkg, {'supported_profiles': ['odes_some_other_profile']})
        checks.expect(layers['declared_profile_conformance'] in ('fail', 'unsupported'), f'a recipient that does not support the declared profile does not pass profile conformance: {layers["declared_profile_conformance"]}')
        checks.expect(layers['recipient_reliance_decision'] != 'pass', 'no reliance when the profile is unsupported')
        return {'layers': layers}
    C.run_c_case(request, record_property, tmp_path, 'C14', trial, gate=False)


# ---------------------------------------------------------------------------------------------------------
# 3. Lineage and uncertainty survive
# ---------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize('case', CASES)
def test_scn_c14_lineage_survives_export(request, record_property, tmp_path, runs, case):
    def trial(work, mp, checks):
        from odes.common import sha256 as odes_sha256
        ex = runs[(_n(work), case)]
        pkg, journal, bundle, manifest = (H2.load_copy(ex, k) for k in ('odes', 'journal', 'bundle', 'manifest'))
        prov = pkg['provenance']
        src = prov['source_artifacts']
        checks.equal(src['reconstruction_bundle_id'], bundle['bundle_id'], 'package names the Replay bundle it was exported from')
        checks.equal(src['reconstruction_bundle_digest'], odes_sha256(bundle), 'package bundle digest recomputes from the retained bundle')
        checks.equal(src['manifest_digest'], odes_sha256(manifest), 'package manifest digest recomputes from the manifest')
        checks.equal(prov['retained_sources']['reconstruction_bundle'], bundle, 'retained bundle in the package equals the exported Replay bundle')
        decision = journal['decisions'][0]
        facts = prov['decision_facts']
        checks.equal(facts['proposal_commitment'], decision['binding']['proposal_commitment'], 'proposal commitment survives')
        checks.equal(facts['decision_result'], decision['result'], 'decision result survives')
        checks.equal(facts['grant_revision'], str(decision['binding']['grant_revision']), 'grant revision survives')
        checks.equal(pkg['record']['decision_id'], decision['decision_id'], 'decision id survives into the ODES record')
        refs = prov['source_record_refs']
        retained_ids = {r['record_id'] for r in bundle['records']}
        ref_ids = {r.get('record_id') for r in refs if isinstance(r, dict)}
        checks.expect(bool(refs) and ref_ids <= retained_ids and len(ref_ids) > 0, 'every source record ref points at a retained Replay record')
        ef = prov['execution_facts']
        checks.equal(len(ef['destination_effects']), ex['destination_effects'], 'destination effect count survives')
        checks.equal(ef['reconstruction_status'], bundle['status'], 'Replay reconstruction status survives')
        ns = ef['attempt_namespaces']
        ns_counts = {k: len(v) for k, v in sorted(ns.items())}
        checks.equal(sorted(ns), ['control_plane', 'executor'], 'Control Plane and executor attempt namespaces are carried as two namespaces')
        checks.expect(not set(ns['control_plane']) & set(ns['executor']), 'the two attempt namespaces share no identifier (no equivalence inferred)')
        checks.equal(ns_counts, {'control_plane': EXPECTED_EFFECTS[case], 'executor': EXPECTED_EFFECTS[case]}, 'attempt identifiers present exactly where an attempt happened')
        checks.equal(prov['replay_validation']['status'], bundle['status'], 'Replay validation status survives')
        src_findings = sorted((f['code'], f['value_state']) for r in bundle['import_reports'] for f in r['findings'])
        pkg_findings = sorted((f['code'], f['value_state']) for f in prov['replay_validation']['findings'])
        checks.equal(pkg_findings, src_findings, 'Replay import findings (codes and value states) survive intact')
        checks.expect(any('effect_id' in s for s in prov['unsupported_semantics']), 'fields pder-v0.1 cannot carry are declared, not invented')
        return {'case': case, 'bundle_id_bound': True, 'bundle_digest_recomputes': True, 'manifest_digest_recomputes': True, 'retained_bundle_equal': True,
                'decision_facts_equal_journal': True, 'record_refs_resolve': len(ref_ids), 'findings': [list(x) for x in src_findings],
                'attempt_namespace_counts': ns_counts, **_gate(case, ex)}
    C.run_c_case(request, record_property, tmp_path, 'C14', trial)


@pytest.mark.parametrize('case', CASES)
def test_scn_c14_uncertainty_survives_export(request, record_property, tmp_path, runs, case):
    def trial(work, mp, checks):
        ex = runs[(_n(work), case)]
        pkg = H2.load_copy(ex, 'odes')
        ef = pkg['provenance']['execution_facts']
        ack, dest = TRUTH[case]
        checks.equal(ef['acknowledgement_summary'], ack, 'acknowledgement state is the producer state (not upgraded or erased)')
        checks.equal(ef['destination_observed'], dest, 'destination observation state is the producer state')
        checks.equal(ef['independent_delivery_verification'], 'unavailable', 'independent delivery verification is unavailable, not verified and not absent')
        checks.equal(ef['retry_permission'], 'not_established', 'retry permission is not established')
        checks.expect('not a fresh query' in ef['destination_observation_scope'], 'destination observation scope states it is not a fresh query')
        checks.equal(ef['historical_local_observation'], False, 'no historical local observation is claimed')
        checks.equal(pkg['provenance']['decision_facts']['human_disposition_source'], 'unavailable', 'human disposition is unavailable, not asserted')
        findings = {(f['code'], f['value_state']) for f in pkg['provenance']['replay_validation']['findings']}
        if case == 'lost_ack':
            checks.expect(('M002', 'unknown') in findings, 'the lost-ack attempt-correlation uncertainty survives as value_state unknown')
        else:
            checks.expect(not any(v == 'unknown' for _, v in findings), 'no unknown state is invented where the producer reported none')
        checks.expect(any('unknown decision_timestamp' in s for s in pkg['provenance']['unsupported_semantics']), 'unknown-timestamp limitation is declared')
        checks.expect(any('do not authenticate the issuer' in s for s in pkg['provenance']['limits']), 'the digest limitation is declared')
        checks.expect(any('renews no authorization' in s for s in pkg['provenance']['limits']), 'the no-renewed-authorization limitation is declared')
        checks.equal(pkg['provenance']['redaction'], {'derivation': None, 'status': 'not_declared'}, 'redaction is explicitly not_declared (not redacted, not absent)')
        return {'case': case, 'acknowledgement': ef['acknowledgement_summary'], 'destination_observed': ef['destination_observed'],
                'independent_delivery_verification': ef['independent_delivery_verification'], 'retry_permission': ef['retry_permission'],
                'findings': sorted(list(x) for x in findings), 'redaction': pkg['provenance']['redaction'], **_gate(case, ex)}
    C.run_c_case(request, record_property, tmp_path, 'C14', trial)


# ---------------------------------------------------------------------------------------------------------
# 4. Envelope validity neither grants authority nor proves delivery
# ---------------------------------------------------------------------------------------------------------
def _best_policy(pkg):
    """The most permissive recipient policy the validator supports short of fabricating external authority evidence."""
    return {'supported_profiles': [PROFILE_ID], 'trusted_digests': [pkg['package_digest']], 'allow_unauthenticated_informational_inspection': True,
            'now': '2030-01-01T00:00:00Z', 'relying_party': 'urn:synthetic:recipient', 'purpose': 'audit'}


@pytest.mark.parametrize('case', CASES)
def test_scn_c14_valid_envelope_grants_no_authority_and_proves_no_delivery(request, record_property, tmp_path, runs, case):
    def trial(work, mp, checks):
        ex = runs[(_n(work), case)]
        pkg = H2.load_copy(ex, 'odes')
        before = C.tree_snapshot(ex['dir'] / 'producer')
        table = {}
        for name, policy in (('empty', POLICY), ('digest_trusted_informational', _best_policy(pkg))):
            layers = in_process(pkg, policy)
            table[name] = layers
            checks.equal(layers['schema_validity'], 'pass', f'{name}: the envelope is valid')
            checks.equal(layers['package_content_integrity'] in ('pass', 'unavailable'), True, f'{name}: integrity evaluated')
            checks.equal(layers['integrity_authentication_checks'], 'unavailable', f'{name}: a content digest is never issuer authentication')
            checks.equal(layers['historical_authority_assertions'], 'unavailable', f'{name}: no historical authority without external status evidence')
            checks.expect(layers['authority_status_and_freshness'] != 'pass', f'{name}: no present authority/freshness')
            checks.expect(layers['recipient_reliance_decision'] in ('fail', 'informational_only'), f'{name}: reliance never pass, observed {layers["recipient_reliance_decision"]}')
        checks.expect(table['digest_trusted_informational']['recipient_reliance_decision'] != 'pass', 'even a digest-trusting, informational policy yields no reliance')
        ef = pkg['provenance']['execution_facts']
        checks.equal(ef['independent_delivery_verification'], 'unavailable', 'delivery is not independently verified by the envelope')
        if case in ('valid', 'lost_ack'):
            checks.equal(ef['destination_observed'], 'applied', 'destination state is the producer observation')
        else:
            checks.expect(ef['destination_observed'] != 'applied', 'no delivery is claimed where the effect was refused')
        checks.equal(C.tree_snapshot(ex['dir'] / 'producer'), before, 'evaluation created no effect and renewed no authorization (producer tree identical)')
        return {'case': case, 'policies': table, 'independent_delivery_verification': ef['independent_delivery_verification'],
                'destination_observed': ef['destination_observed'], 'producer_tree_unchanged': True, **_gate(case, ex)}
    C.run_c_case(request, record_property, tmp_path, 'C14', trial)


def test_scn_c14_forged_authority_or_delivery_claims_are_not_validated(request, record_property, tmp_path, runs):
    """Self-consistent (rehashed) forgeries promoting authority or delivery in the envelope."""
    FORGERIES = {
        'delivery_verified': lambda p: p['provenance']['execution_facts'].__setitem__('independent_delivery_verification', 'verified'),
        'retry_permitted': lambda p: p['provenance']['execution_facts'].__setitem__('retry_permission', 'permitted'),
        'destination_applied_on_refused_case': lambda p: p['provenance']['execution_facts'].__setitem__('destination_observed', 'applied'),
        'ack_received_on_lost_ack': lambda p: p['provenance']['execution_facts'].__setitem__('acknowledgement_summary', 'received'),
        'decision_result_authorized_to_denied_label': lambda p: p['provenance']['decision_facts'].__setitem__('decision_result', 'denied'),
        'record_authority_valid_at_decision_false': lambda p: p['record']['authority'].__setitem__('authority_valid_at_decision', False),
        'record_status_freshness_current': lambda p: p['record']['status'].__setitem__('freshness', 'current'),
    }

    def trial(work, mp, checks):
        out = {}
        for case in ('lost_ack', 'revoked'):
            base = H2.load_copy(runs[(_n(work), case)], 'odes')
            for name, fn in FORGERIES.items():
                q = copy.deepcopy(base)
                try:
                    fn(q)
                except KeyError:
                    out[f'{case}/{name}'] = 'not_applicable'
                    continue
                if q == base:
                    out[f'{case}/{name}'] = 'no_change'
                    continue
                H2.odes_rehash(q)
                try:
                    layers = in_process(q, _best_policy(q))
                except Exception as exc:
                    layers = {'raised': type(exc).__name__}
                out[f'{case}/{name}'] = layers if 'raised' in layers else {k: layers[k] for k in ('replay_semantic_consistency', 'package_content_integrity', 'integrity_authentication_checks', 'recipient_reliance_decision')}
                checks.expect('raised' in layers or layers['recipient_reliance_decision'] != 'pass', f'{case}/{name}: reliance must not pass on a forged envelope')
                checks.expect('raised' in layers or layers['integrity_authentication_checks'] != 'pass', f'{case}/{name}: authentication must not pass')
                # the forgery must be caught by a semantic layer (the digest is self-consistent after rehash)
                caught = 'raised' in layers or layers['replay_semantic_consistency'] != 'pass'
                checks.expect(caught, f'{case}/{name}: a rehashed envelope claim contradicting the retained Replay evidence must fail replay semantic consistency, observed {layers}')
        applicable = {k: v for k, v in out.items() if v not in ('not_applicable', 'no_change')}
        return {'forgeries': out, 'applicable': len(applicable)}
    C.run_c_case(request, record_property, tmp_path, 'C14', trial, gate=False)


class _FdEvents:
    """Event sink of a forked worker: one JSON line per event through an fd opened before the fork (os.write raises no audit event)."""
    def __init__(self, fd):
        self.fd = fd

    def append(self, event):
        os.write(self.fd, (json.dumps(list(event)) + '\n').encode())


class _ObserverWithWorkers(C.Observer):
    """C.Observer plus the events of forked children (the ODES semantic worker): the audit hook is inherited across fork but its
    in-memory list is not shared, so each child redirects its events to a file the parent reads back as ``child_events``."""
    _fork_hook_registered = False

    def __enter__(self):
        self._dir = tempfile.TemporaryDirectory()
        self._path = os.path.join(self._dir.name, 'child-events.jsonl')
        self._fd = os.open(self._path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        if not _ObserverWithWorkers._fork_hook_registered:
            os.register_at_fork(after_in_child=_ObserverWithWorkers._in_child)
            _ObserverWithWorkers._fork_hook_registered = True
        return super().__enter__()

    def __exit__(self, *exc):
        super().__exit__(*exc)
        os.close(self._fd)
        return False

    @staticmethod
    def _in_child():
        obs = C.Observer._current
        if isinstance(obs, _ObserverWithWorkers):
            child = _ObserverWithWorkers.__new__(_ObserverWithWorkers)
            child.boundary, child.events = obs.boundary, _FdEvents(obs._fd)
            C.Observer._current = child
            fd = obs._fd

            def full_argv(event, args):  # the base observer truncates rendered arguments; the exact argv is needed to classify a spawn
                if event == 'subprocess.Popen' and C.Observer._current is child:
                    os.write(fd, (json.dumps(['popen-argv', [str(a) for a in args[1]]]) + '\n').encode())
            sys.addaudithook(full_argv)

    @property
    def child_events(self):
        with open(self._path) as handle:
            return [tuple(json.loads(line)) for line in handle.read().splitlines()]

    def __del__(self):
        try:
            self._dir.cleanup()
        except Exception:
            pass


def test_scn_c14_read_cannot_be_used_to_reach_the_destination(request, record_property, tmp_path, runs):
    """A reader observes no process/network/destination-write activity from the evaluator."""
    def trial(work, mp, checks):
        ex = runs[(_n(work), 'valid')]
        pkg = H2.load_copy(ex, 'odes')
        boundary = ex['dir'] / 'producer'
        before = C.tree_snapshot(boundary)
        with _ObserverWithWorkers(boundary) as obs:
            in_process(pkg, _best_policy(pkg))
        rep = obs.report()
        # ODES #117 (39a3c6ce): the Replay semantic check runs in one forked worker (a deadline needs a killable process). That fork is the
        # only process event allowed; no exec, subprocess, shell or spawn, and the worker's own events are observed too (see _ChildLog).
        checks.equal(rep['process_events'], ['os.fork'], 'evaluator spawned no process other than the one documented semantic worker (fork only)')
        checks.equal(sum(1 for e in obs.events if e[0] == 'os.fork'), 1, 'exactly one fork')
        # The worker (odes.common.installed_replay_revision and installed_replay_checkout_dirty, ODES #100 and #110: 10dfd70d, 08ac0ead) asks git which commit the
        # imported Replay comes from: `git -C <dir of the Replay checkout> rev-parse HEAD` and `git -C <dir> status --porcelain
        # --untracked-files=no`. Those two read-only calls against the Replay tree are the only spawn allowed; any other process, any git
        # call elsewhere (the producer tree, the destination) or any other git verb is a finding.
        replay_tree = C.reference().paths['replay'].resolve()
        argvs = [e[1] for e in obs.child_events if e[0] == 'popen-argv']
        allowed = ([['git', '-C', None, 'rev-parse', 'HEAD'], ['git', '-C', None, 'status', '--porcelain', '--untracked-files=no']])
        unexpected = [a for a in argvs if not (len(a) >= 5 and a[:2] == ['git', '-C'] and Path(a[2]).resolve().is_relative_to(replay_tree)
                                                and [a[0], a[1], None, *a[3:]] in allowed)]
        checks.equal(unexpected, [], 'the semantic worker spawned only read-only git queries about the Replay checkout')
        checks.equal(sorted({e[0] for e in obs.child_events if e[0] in ('os.system', 'os.exec', 'os.posix_spawn', 'os.fork', 'os.forkpty')}), [],
                     'the semantic worker started no shell, exec, spawn or further fork')
        checks.equal(sum(1 for e in obs.child_events if e[0] == 'subprocess.Popen'), len(argvs), 'every worker subprocess was classified by its exact argv')
        checks.equal(sorted({e[0] for e in obs.child_events if e[0].startswith('socket.')}), [], 'the semantic worker opened no network connection')
        checks.equal([e for e in obs.child_events if e[0] == 'sqlite3.connect'], [], 'the semantic worker opened no SQLite database')
        checks.equal([e for e in obs.child_events if e[0] == 'open-write'], [], 'the semantic worker opened no file for writing')
        checks.equal(rep['network_events'], [], 'evaluator opened no network connection')
        checks.equal([e for e in obs.events if e[0] == 'sqlite3.connect'], [], 'evaluator opened no SQLite database')
        checks.equal(rep['write_class_events'], 0, 'evaluator issued no write-class filesystem event')
        checks.equal(C.tree_snapshot(boundary), before, 'producer tree byte-identical')
        return {'process_events': rep['process_events'], 'network_events': rep['network_events'], 'write_class_events': rep['write_class_events'],
                'sqlite_opened': False, 'producer_tree_unchanged': True, **_gate('valid', ex)}
    C.run_c_case(request, record_property, tmp_path, 'C14', trial)
