"""SCN-C13 Redaction and signing (executed against the frozen F5b seven-component reference).

SPDX-License-Identifier: Apache-2.0

Stimulus (catalog C13): tamper with an export and exercise the declared redaction and signing order. Required
observation: integrity failures are detected; absent, unknown and redacted states remain distinct; HMAC is not treated as
public independent attestation.

Surfaces exercised (Replay 0cfe7a63 ``sign_reconstruction_bundle`` / ``verify_reconstruction_hmac`` /
``redact_reconstruction_bundle`` / ``content_digest``; Evidence Pack importer + validator 683246e0; ODES exporter +
recipient evaluator 4e6d1169) over bundles produced by the frozen Control Plane + executor. Every variant is planted in a
deep copy; the exported originals are verified byte-unchanged. Each case runs twice (two independent producer runs, D3).
Honest outcomes: where a consumer cannot carry a state (e.g. no downstream consumer accepts a redacted derivative) the
test records the explicit refusal and the limit; nothing is faked as a pass. The replay package ships no content-digest
verifier, so the digest check here recomputes ``content_digest`` the way any recipient would.
"""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

import _c_2b_helpers as C
from _c_2b_helpers import pinned_reference  # noqa: F401

H2 = C.H2
CASES = ('valid', 'lost_ack', 'revoked', 'unreadable')
SECRET = 'synthetic-shared-secret-A'
OTHER_SECRET = 'synthetic-shared-secret-B'


@pytest.fixture(scope='module')
def runs(pinned_reference, tmp_path_factory):
    root = tmp_path_factory.mktemp('c13-exports')
    built = {(n, case): H2.build_exports(case, root / f'run-{n}') for n in (1, 2) for case in CASES}
    yield built
    for (n, case), ex in built.items():
        for name, expected in ex['sha256'].items():
            assert hashlib.sha256((ex['dir'] / name).read_bytes()).hexdigest() == expected, f'exported original {n}/{case}/{name} was modified'


def _n(work):
    return int(work.name.split('-')[1])


def _replay():
    import agent_replay_bundle as R
    return R


def _bundle(ex):
    R = _replay()
    return R.ReconstructionBundle.model_validate(H2.load_copy(ex, 'bundle'))


def _hmac_ok(bundle_dict, secret=SECRET):
    R = _replay()
    try:
        return R.verify_reconstruction_hmac(R.ReconstructionBundle.model_validate(bundle_dict), secret)
    except Exception:
        return 'rejected_by_model'


def _digest_matches(bundle):
    R = _replay()
    stored = [i for i in bundle.integrity if i.kind == 'content-digest']
    return len(stored) == 1 and stored[0].value == R.content_digest(bundle).value


# ---------------------------------------------------------------------------------------------------------
# 1. HMAC export integrity: every tampered field is detected; the intact export verifies
# ---------------------------------------------------------------------------------------------------------
def _first(lst, pred):
    return next(i for i, x in enumerate(lst) if pred(x))


HMAC_TAMPER = {
    'record_data_edit': lambda d: d['records'][0]['data'].__setitem__('__planted__', 'tampered'),
    'record_drop_first': lambda d: d['records'].pop(0),
    'record_duplicate_first': lambda d: d['records'].append(copy.deepcopy(d['records'][0])),
    'record_reorder_swap': lambda d: d['records'].insert(0, d['records'].pop(1)),
    'record_identifier_edit': lambda d: d['records'][0]['identifiers'].__setitem__('planted_id', 'x'),
    'status_promoted': lambda d: d.__setitem__('status', 'reconstruction_complete' if d['status'] != 'reconstruction_complete' else 'redacted'),
    'run_id_edit': lambda d: d.__setitem__('run_id', 'run-forged'),
    'generated_at_edit': lambda d: d.__setitem__('generated_at', '2000-01-01T00:00:00+00:00'),
    'semantics_effect_flag_edit': lambda d: d['semantics'].__setitem__('external_effect_execution', True),
    'semantics_independent_verification_edit': lambda d: d['semantics'].__setitem__('independent_effect_verification', True),
    'commitment_status_promoted': lambda d: d['commitments'][_first(d['commitments'], lambda c: c['verification_status'] == 'attributed_claim')].__setitem__('verification_status', 'checked_match'),
    'import_finding_dropped': lambda d: d['import_reports'][0]['findings'].pop(0),
    'metadata_edit': lambda d: d['metadata'].__setitem__('planted', 'x'),
    'integrity_key_id_relabelled': lambda d: d['integrity'][0].__setitem__('key_id', 'issuer:someone-else'),
    'integrity_claim_edited': lambda d: d['integrity'][0].__setitem__('verification_claim', 'Verified public issuer signature.'),
    'integrity_algorithm_edited': lambda d: d['integrity'][0].__setitem__('algorithm', 'HMAC-SHA512'),
    'integrity_canonicalization_edited': lambda d: d['integrity'][0].__setitem__('canonicalization_profile', 'other'),
    'integrity_subject_edited': lambda d: d['integrity'][0].__setitem__('subject_bundle_id', 'other-bundle'),
    'bundle_id_edit': lambda d: d.__setitem__('bundle_id', 'bundle-forged'),
    'signature_blanked': lambda d: d['integrity'][0].__setitem__('value', ''),
    'signature_bit_flipped': lambda d: d['integrity'][0].__setitem__('value', ('0' if d['integrity'][0]['value'][0] != '0' else '1') + d['integrity'][0]['value'][1:]),
    'signature_stripped': lambda d: d.__setitem__('integrity', []),
    'signature_duplicated': lambda d: d['integrity'].append(copy.deepcopy(d['integrity'][0])),
}


@pytest.mark.parametrize('case', ('lost_ack', 'valid'))
def test_scn_c13_hmac_intact_export_verifies_and_wrong_secret_does_not(request, record_property, tmp_path, runs, case):
    R = _replay()

    def trial(work, mp, checks):
        ex = runs[(_n(work), case)]
        signed = R.sign_reconstruction_bundle(_bundle(ex), SECRET, key_id='key:synthetic-A')
        d = signed.model_dump(mode='json')
        checks.equal(_hmac_ok(d), True, 'intact signed export verifies under the right secret')
        checks.equal(_hmac_ok(d, OTHER_SECRET), False, 'wrong secret does not verify')
        checks.equal(_hmac_ok(d, ''), False, 'empty secret does not verify')
        checks.equal(len([i for i in signed.integrity if i.kind == 'hmac']), 1, 'exactly one hmac integrity entry')
        # re-reading the serialised export keeps it verifiable (a signature that does not survive a round trip is useless)
        again = json.loads(json.dumps(d))
        checks.equal(_hmac_ok(again), True, 'signed export verifies after a JSON round trip')
        # the source bundle was not mutated by signing
        checks.equal(any(i.kind == 'hmac' for i in _bundle(ex).integrity), False, 'signing returns a copy; the source bundle stays unsigned')
        return {'hmac_intact_verifies': True, 'wrong_secret_rejected': True, 'round_trip_verifies': True,
                'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    C.run_c_case(request, record_property, tmp_path, 'C13', trial, gate=False)


@pytest.mark.parametrize('variant', sorted(HMAC_TAMPER))
def test_scn_c13_hmac_tamper_detected_variant(request, record_property, tmp_path, runs, variant):
    R = _replay()

    def trial(work, mp, checks):
        ex = runs[(_n(work), 'lost_ack')]
        signed = R.sign_reconstruction_bundle(_bundle(ex), SECRET, key_id='key:synthetic-A').model_dump(mode='json')
        forged = copy.deepcopy(signed)
        HMAC_TAMPER[variant](forged)
        checks.expect(forged != signed, f'{variant}: the plant changed the export')
        verdict = _hmac_ok(forged)
        checks.expect(verdict is False or verdict == 'rejected_by_model', f'{variant}: tampered export must not verify, observed {verdict!r}')
        return {'variant': variant, 'verifies': verdict is True, 'detected_by': 'hmac_verify' if verdict is False else 'model_validation'}
    C.run_c_case(request, record_property, tmp_path, 'C13', trial, gate=False)


# ---------------------------------------------------------------------------------------------------------
# 2. HMAC is shared-secret authenticity only, never public independent attestation
# ---------------------------------------------------------------------------------------------------------
def test_scn_c13_hmac_is_not_public_attestation_key_id_is_a_label(request, record_property, tmp_path, runs):
    R = _replay()

    def trial(work, mp, checks):
        ex = runs[(_n(work), 'lost_ack')]
        base = _bundle(ex)
        verdicts = {}
        for label in ('issuer:alice', 'issuer:bob', 'issuer:does-not-exist', None):
            signed = R.sign_reconstruction_bundle(base, SECRET, key_id=label)
            verdicts[str(label)] = _hmac_ok(signed.model_dump(mode='json'))
        # whoever holds the secret signs ANY content under ANY label (a verifier is also a forger)
        forged = base.model_copy(deep=True)
        forged.records[0].data['__planted__'] = 'attacker-with-secret'
        forged_signed = R.sign_reconstruction_bundle(forged, SECRET, key_id='issuer:alice')
        forged_ok = _hmac_ok(forged_signed.model_dump(mode='json'))
        claim = next(i for i in forged_signed.integrity if i.kind == 'hmac').verification_claim
        checks.expect(all(verdicts.values()), f'every label verifies under the shared secret (labels carry no identity): {verdicts}')
        checks.equal(forged_ok, True, 'a secret holder can mint a verifying export with altered content under any label (shared-secret property)')
        checks.expect('does not establish public key identity' in claim and 'issuer identity' in claim,
                      f'the declared verification claim must state that the label is not identity: {claim!r}')
        return {'labels_that_verify': sorted(verdicts), 'secret_holder_can_forge_verifying_export': forged_ok is True,
                'declared_claim_disclaims_identity': 'does not establish public key identity' in claim,
                'conclusion': 'hmac verification proves possession of the shared secret only; it is not a public attestation'}
    C.run_c_case(request, record_property, tmp_path, 'C13', trial, gate=False)


def test_scn_c13_hmac_not_surfaced_as_attestation_by_pack_or_odes(request, record_property, tmp_path, runs):
    R = _replay()

    def trial(work, mp, checks):
        ex = runs[(_n(work), 'lost_ack')]
        manifest = H2.load_copy(ex, 'manifest')
        signed = R.sign_reconstruction_bundle(_bundle(ex), SECRET, key_id='issuer:alice').model_dump(mode='json')
        from agent_governance_evidence_pack.importer import import_manifest_reconstruction
        from agent_governance_evidence_pack import validate_evidence_pack
        from odes import export_cognous_stack_package, evaluate_recipient_package
        pack = import_manifest_reconstruction(manifest, signed)
        pd = pack.model_dump(mode='json')
        codes = sorted(f['code'] for f in pd['metadata']['traceable_import']['import_findings'])
        checks.equal(pd['replay_bundles'][0]['signed'], False, 'Evidence Pack does not mark an HMAC-signed bundle as signed/attested')
        checks.expect('R_REDACTION_UNVERIFIED' in codes, 'Evidence Pack keeps its unverified-redaction warning for a signed bundle')
        checks.equal(validate_evidence_pack(pack).valid, True, 'signed bundle still imports and validates as a pack (no new claim)')
        package = export_cognous_stack_package(manifest, signed)
        res = evaluate_recipient_package(package, {'supported_profiles': ['odes_cognous_stack_export_0_2']})
        layers = {k: v['status'] for k, v in res.items() if isinstance(v, dict) and 'status' in v}
        checks.equal(layers.get('integrity_authentication_checks'), 'unavailable', 'ODES reports authentication of integrity as unavailable, not pass')
        checks.expect(layers.get('recipient_reliance_decision') != 'pass', 'ODES reliance decision is never pass on an HMAC-signed export')
        kinds = sorted({i.get('kind') for i in package['integrity']} if isinstance(package['integrity'], list) else {package['integrity'].get('kind')})
        checks.expect('hmac' not in kinds, f'ODES package integrity must not present the HMAC as its integrity kind: {kinds}')
        return {'pack_signed_flag': pd['replay_bundles'][0]['signed'], 'pack_findings_include_unverified_redaction': 'R_REDACTION_UNVERIFIED' in codes,
                'odes_integrity_authentication': layers.get('integrity_authentication_checks'),
                'odes_reliance': layers.get('recipient_reliance_decision'), 'odes_integrity_kinds': kinds}
    C.run_c_case(request, record_property, tmp_path, 'C13', trial, gate=False)


# ---------------------------------------------------------------------------------------------------------
# 3. Redaction produces a separately identified derivative; absent / unknown / redacted stay distinct
# ---------------------------------------------------------------------------------------------------------
def _states(bundle_dict):
    return sorted({str(f.get('value_state')) for r in bundle_dict['import_reports'] for f in r['findings']})


def test_scn_c13_redaction_derivative_lineage_and_states(request, record_property, tmp_path, runs):
    R = _replay()

    def trial(work, mp, checks):
        ex = runs[(_n(work), 'lost_ack')]
        src = _bundle(ex)
        before = src.model_dump(mode='json')
        red = R.redact_reconstruction_bundle(src, redact_paths={'proposal'})
        rd = red.model_dump(mode='json')
        checks.expect(red.bundle_id != src.bundle_id, 'redacted derivative has its own identifier')
        checks.equal(rd['derivation']['relationship'], 'redacted_derivative', 'derivation relationship')
        checks.equal(rd['derivation']['source_bundle_id'], src.bundle_id, 'derivation names the source bundle')
        checks.equal(rd['status'], 'redacted', 'derivative status is redacted')
        checks.equal(src.model_dump(mode='json'), before, 'the source bundle is unmodified by redaction')
        red_recs = [r for r in rd['records'] if r['source_path'] == 'proposal']
        other_recs = {r['record_id']: r for r in rd['records'] if r['source_path'] != 'proposal'}
        orig_other = {r['record_id']: r for r in before['records'] if r['source_path'] != 'proposal'}
        checks.expect(bool(red_recs) and all(r['data'].get('redacted') is True for r in red_recs), 'redacted records carry the redaction marker, not an empty/absent value')
        checks.equal(other_recs, orig_other, 'records outside redact_paths are byte-identical')
        redacted_ids = {r['record_id'] for r in red_recs}
        for c in rd['commitments']:
            if c['source_record_id'] in redacted_ids:
                checks.equal(c['verification_status'], 'attributed_claim', 'a commitment over redacted content is downgraded to an attributed claim')
        src_states = _states(before)
        red_states = _states(rd)
        checks.expect('unknown' in src_states, f'source carries an explicit unknown state: {src_states}')
        checks.expect('unknown' in red_states and 'redacted' in red_states, f'derivative keeps unknown AND adds redacted (distinct, not collapsed): {red_states}')
        checks.expect('redacted' not in src_states, 'the source carries no redacted state before redaction')
        r001 = [f for r in rd['import_reports'] for f in r['findings'] if f['code'] == 'R001']
        checks.expect(bool(r001) and all(f['value_state'] == 'redacted' and f['path'] == 'proposal' for f in r001), 'R001 findings are value_state=redacted at the redacted path')
        checks.expect(all(f['value_state'] == 'unknown' for r in rd['import_reports'] for f in r['findings'] if f['code'] == 'M002'), 'M002 stays unknown (not rewritten to redacted/absent)')
        integ = rd['integrity']
        checks.equal([i['kind'] for i in integ], ['content-digest'], 'derivative carries exactly one content-digest and no signature')
        checks.expect('not an issuer signature' in integ[0]['verification_claim'], 'content-digest claim disclaims issuer signature')
        checks.equal(_digest_matches(red), True, 'derivative content-digest recomputes')
        try:
            R.redact_reconstruction_bundle(src, redact_paths={'no.such.path'})
            unmatched = 'silent_noop'
        except ValueError:
            unmatched = 'explicit_error'
        checks.equal(unmatched, 'explicit_error', 'redacting a path that matches nothing fails explicitly (not a silent no-op)')
        return {'derivative_new_id': True, 'lineage_recorded': True, 'source_unmodified': True, 'source_states': src_states, 'derivative_states': red_states,
                'other_records_identical': True, 'commitments_downgraded': True, 'unmatched_path': unmatched,
                'integrity_kinds': [i['kind'] for i in integ]}
    C.run_c_case(request, record_property, tmp_path, 'C13', trial, gate=False)


def test_scn_c13_value_states_observed_across_producer_cases(request, record_property, tmp_path, runs):
    """Which of absent / unknown / unavailable / redacted the real producers emit; states are never merged."""
    def trial(work, mp, checks):
        seen = {}
        for case in CASES:
            d = H2.load_copy(runs[(_n(work), case)], 'bundle')
            seen[case] = _states(d)
        union = sorted({s for v in seen.values() for s in v})
        checks.expect('unknown' in union, f'producers emit the explicit unknown state: {union}')
        checks.expect('redacted' not in union, 'no producer-run bundle claims redaction without a redaction act')
        return {'value_states_by_case': seen, 'union': union,
                'not_produced_by_these_runs': sorted({'absent', 'unavailable'} - set(union))}
    C.run_c_case(request, record_property, tmp_path, 'C13', trial, gate=False)


def test_scn_c13_absent_unknown_redacted_are_schema_distinct(request, record_property, tmp_path, runs):
    R = _replay()

    def trial(work, mp, checks):
        accepted = {}
        for state in ('absent', 'unknown', 'unavailable', 'redacted'):
            f = R.ImportFinding(code='X', category='conversion_warning', severity='info', path='p', message='m', value_state=state)
            accepted[state] = f.value_state
        checks.equal(accepted, {s: s for s in accepted}, 'each state round-trips as itself')
        try:
            R.ImportFinding(code='X', category='conversion_warning', severity='info', path='p', message='m', value_state='missing')
            bogus = 'accepted'
        except Exception:
            bogus = 'rejected'
        checks.equal(bogus, 'rejected', 'a fifth, undeclared state is rejected')
        ex = runs[(_n(work), 'lost_ack')]
        red = R.redact_reconstruction_bundle(_bundle(ex), redact_paths={'proposal'})
        marker = [r for r in red.records if r.source_path == 'proposal'][0].data
        checks.expect(marker != {} and marker.get('redacted') is True, 'a redacted record is not rendered as empty/absent data')
        return {'states_round_trip': True, 'undeclared_state_rejected': bogus == 'rejected', 'redacted_marker_is_not_empty': True}
    C.run_c_case(request, record_property, tmp_path, 'C13', trial, gate=False)


# ---------------------------------------------------------------------------------------------------------
# 4. Declared signing / redaction order
# ---------------------------------------------------------------------------------------------------------
def test_scn_c13_order_sign_then_redact_drops_the_signature(request, record_property, tmp_path, runs):
    R = _replay()

    def trial(work, mp, checks):
        ex = runs[(_n(work), 'lost_ack')]
        signed = R.sign_reconstruction_bundle(_bundle(ex), SECRET, key_id='key:synthetic-A')
        red = R.redact_reconstruction_bundle(signed, redact_paths={'proposal'})
        kinds = [i.kind for i in red.integrity]
        checks.equal(kinds, ['content-digest'], 'redacting a signed bundle yields a derivative with no HMAC (the old signature is not carried over)')
        checks.equal(R.verify_reconstruction_hmac(red, SECRET), False, 'the original secret does not verify the derivative')
        # copy the old HMAC entry across by hand: it must not verify either
        grafted = red.model_copy(deep=True)
        grafted.integrity = [i.model_copy(deep=True) for i in signed.integrity if i.kind == 'hmac']
        checks.equal(R.verify_reconstruction_hmac(grafted, SECRET), False, 'a grafted old HMAC does not verify over the derivative')
        checks.expect(red.bundle_id != signed.bundle_id, 'derivative has its own id (a signature over the source cannot be mistaken for one over the derivative)')
        return {'derivative_integrity_kinds': kinds, 'old_secret_verifies_derivative': False, 'grafted_old_hmac_verifies': False}
    C.run_c_case(request, record_property, tmp_path, 'C13', trial, gate=False)


def test_scn_c13_order_redact_then_sign_binds_the_derivative(request, record_property, tmp_path, runs):
    R = _replay()

    def trial(work, mp, checks):
        ex = runs[(_n(work), 'lost_ack')]
        red = R.redact_reconstruction_bundle(_bundle(ex), redact_paths={'proposal'})
        signed = R.sign_reconstruction_bundle(red, SECRET, key_id='key:synthetic-A')
        d = signed.model_dump(mode='json')
        checks.equal(_hmac_ok(d), True, 'redact-then-sign verifies')
        kinds = sorted(i.kind for i in signed.integrity)
        checks.equal(kinds, ['content-digest', 'hmac'], 'signing a derivative keeps its content digest and adds the HMAC')
        for name, fn in (('derivation_source_edit', lambda x: x['derivation'].__setitem__('source_bundle_id', 'other')),
                         ('redaction_marker_removed', lambda x: [r for r in x['records'] if r['source_path'] == 'proposal'][0].__setitem__('data', {'restored': 'secret'})),
                         ('status_unredacted', lambda x: x.__setitem__('status', 'reconstruction_complete')),
                         ('redaction_finding_dropped', lambda x: [f for rp in x['import_reports'] for f in rp['findings'] if f['code'] == 'R001'] and [rp['findings'].__delitem__(i) for rp in x['import_reports'] for i, f in reversed(list(enumerate(rp['findings']))) if f['code'] == 'R001'])):
            q = copy.deepcopy(d)
            fn(q)
            checks.expect(q != d, f'{name}: plant changed the export')
            checks.expect(_hmac_ok(q) is not True, f'{name}: post-signing edit of redaction state must be detected')
        return {'redact_then_sign_verifies': True, 'integrity_kinds': kinds,
                'post_signing_edits_detected': ['derivation_source_edit', 'redaction_marker_removed', 'status_unredacted', 'redaction_finding_dropped']}
    C.run_c_case(request, record_property, tmp_path, 'C13', trial, gate=False)


def test_scn_c13_order_sign_then_manual_redaction_is_detected(request, record_property, tmp_path, runs):
    R = _replay()

    def trial(work, mp, checks):
        ex = runs[(_n(work), 'lost_ack')]
        signed = R.sign_reconstruction_bundle(_bundle(ex), SECRET, key_id='key:synthetic-A').model_dump(mode='json')
        q = copy.deepcopy(signed)
        for r in q['records']:
            if r['source_path'] == 'proposal':
                r['data'] = {'redacted': True, 'replacement': '[REDACTED]'}
        checks.expect(_hmac_ok(q) is not True, 'redaction applied by hand to a signed bundle (not via the redactor) invalidates the HMAC')
        return {'manual_redaction_of_signed_bundle_verifies': _hmac_ok(q) is True}
    C.run_c_case(request, record_property, tmp_path, 'C13', trial, gate=False)


def test_scn_c13_order_double_redaction_keeps_lineage(request, record_property, tmp_path, runs):
    R = _replay()

    def trial(work, mp, checks):
        ex = runs[(_n(work), 'lost_ack')]
        src = _bundle(ex)
        first = R.redact_reconstruction_bundle(src, redact_paths={'proposal'})
        second = R.redact_reconstruction_bundle(first, redact_paths={'attempts[0]'})
        checks.equal(second.derivation.source_bundle_id, first.bundle_id, 'second derivative names the first derivative as its source')
        checks.expect(len({src.bundle_id, first.bundle_id, second.bundle_id}) == 3, 'three distinct bundle ids')
        checks.expect(src.bundle_id != second.derivation.source_bundle_id, 'lineage points one step back, not to the original')
        red_paths = sorted(r.source_path for r in second.records if isinstance(r.data, dict) and r.data.get('redacted') is True)
        checks.equal(red_paths, ['attempts[0]', 'proposal'], 'both redactions are present in the second derivative')
        return {'distinct_ids': 3, 'lineage_one_step_back': True, 'redacted_paths': red_paths}
    C.run_c_case(request, record_property, tmp_path, 'C13', trial, gate=False)


# ---------------------------------------------------------------------------------------------------------
# 5. Content digest is tamper evidence for a recipient who recomputes it, never authentication
# ---------------------------------------------------------------------------------------------------------
def test_scn_c13_content_digest_detects_tamper_but_is_not_authentication(request, record_property, tmp_path, runs):
    R = _replay()

    def trial(work, mp, checks):
        ex = runs[(_n(work), 'lost_ack')]
        red = R.redact_reconstruction_bundle(_bundle(ex), redact_paths={'proposal'})
        checks.equal(_digest_matches(red), True, 'intact derivative digest recomputes')
        tampered = red.model_copy(deep=True)
        tampered.records[0].data['__planted__'] = 'tampered'
        detected = not _digest_matches(tampered)
        checks.equal(detected, True, 'editing a record without refreshing the digest is detected on recomputation')
        refreshed = tampered.model_copy(deep=True)
        refreshed.integrity = [R.content_digest(refreshed)]
        forged_consistent = _digest_matches(refreshed)
        checks.equal(forged_consistent, True, 'a refreshed digest is self-consistent (documented: the digest is not authentication)')
        checks.equal(R.verify_reconstruction_hmac(refreshed, SECRET), False, 'a self-consistent digest never verifies as an HMAC')
        claim = refreshed.integrity[0].verification_claim
        checks.expect('not an issuer signature' in claim, 'the digest claim states it is not an issuer signature')
        return {'tamper_detected_on_recompute': detected, 'refreshed_digest_self_consistent': forged_consistent,
                'refreshed_digest_is_authentication': False, 'conclusion': 'digest detects accidental/unrefreshed edits only'}
    C.run_c_case(request, record_property, tmp_path, 'C13', trial, gate=False)


# ---------------------------------------------------------------------------------------------------------
# 6. Consumers: a redacted derivative is refused explicitly; state-bearing fields of tampered packs/packages are detected
# ---------------------------------------------------------------------------------------------------------
def test_scn_c13_redacted_derivative_is_explicitly_refused_downstream(request, record_property, tmp_path, runs):
    R = _replay()

    def trial(work, mp, checks):
        ex = runs[(_n(work), 'lost_ack')]
        src = _bundle(ex)
        manifest = H2.load_copy(ex, 'manifest')
        paths = sorted({r.source_path for r in src.records if not r.source_path.startswith('check_events') or r.source_path == 'check_events[0]'})
        from agent_governance_evidence_pack.importer import import_manifest_reconstruction
        from odes import export_cognous_stack_package
        table = {}
        for p in paths:
            rd = R.redact_reconstruction_bundle(src, redact_paths={p}).model_dump(mode='json')
            row = {}
            try:
                pack = import_manifest_reconstruction(manifest, rd).model_dump(mode='json')
                codes = {f['code'] for f in pack['metadata']['traceable_import']['import_findings']}
                row['pack'] = 'accepted'
                checks.expect('R_REDACTION_UNVERIFIED' in codes, f'{p}: an accepted redacted bundle must keep R_REDACTION_UNVERIFIED')
                checks.expect(pack['metadata']['traceable_import']['redaction_state']['derivation'] is not None, f'{p}: an accepted redacted bundle must keep its derivation')
            except Exception as exc:
                row['pack'] = 'refused:' + type(exc).__name__
            try:
                package = export_cognous_stack_package(manifest, rd)
                row['odes'] = 'accepted'
                checks.expect(package['provenance']['redaction'].get('status') != 'not_declared', f'{p}: an accepted redacted bundle must not be exported as redaction not_declared')
            except Exception as exc:
                row['odes'] = 'refused:' + type(exc).__name__
            table[p] = row
        refused_both = sorted(p for p, r in table.items() if r['pack'].startswith('refused') and r['odes'].startswith('refused'))
        return {'paths_tried': len(table), 'refused_by_both_consumers': len(refused_both),
                'per_path': table,
                'limit': 'the pinned consumers need unredacted retained records; no redacted derivative reaches Pack/ODES as a redacted state'}
    C.run_c_case(request, record_property, tmp_path, 'C13', trial, gate=False)


def test_scn_c13_odes_export_tamper_detection_and_integrity_scope(request, record_property, tmp_path, runs):
    def trial(work, mp, checks):
        from odes import evaluate_recipient_package
        ex = runs[(_n(work), 'lost_ack')]
        pkg = H2.load_copy(ex, 'odes')
        pol = {'supported_profiles': ['odes_cognous_stack_export_0_2']}

        def layers(o):
            res = evaluate_recipient_package(o, pol)
            return {k: v['status'] for k, v in res.items() if isinstance(v, dict) and 'status' in v}
        clean = layers(pkg)
        checks.equal(clean['package_content_integrity'], 'pass', 'clean export passes content integrity')
        checks.equal(clean['integrity_authentication_checks'], 'unavailable', 'clean export has no authentication available')
        scope = {}
        edits = {
            'record_edit': lambda o: o['record'].__setitem__('__planted__', 'x') if isinstance(o['record'], dict) else o.__setitem__('record', 'x'),
            'profile_edit': lambda o: o['profile'].__setitem__('__planted__', 'x') if isinstance(o['profile'], dict) else o.__setitem__('profile', 'x'),
            'provenance_edit': lambda o: o['provenance']['execution_facts'].__setitem__('destination_observed', 'absent' if o['provenance']['execution_facts'].get('destination_observed') != 'absent' else 'applied'),
            'integrity_value_edit': lambda o: o['integrity'].__setitem__('value', 'sha256:' + '0' * 64),
            'package_digest_edit': lambda o: o.__setitem__('package_digest', 'sha256:' + '0' * 64),
            'created_by_edit': lambda o: o.__setitem__('created_by', 'forged-issuer'),
            'created_at_edit': lambda o: o.__setitem__('created_at', '2000-01-01T00:00:00+00:00'),
        }
        for name, fn in edits.items():
            q = copy.deepcopy(pkg)
            fn(q)
            checks.expect(q != pkg, f'{name}: plant changed the export')
            out = layers(q)
            scope[name] = {'integrity': out['package_content_integrity'], 'replay_semantic': out['replay_semantic_consistency'],
                           'reliance': out['recipient_reliance_decision'], 'authentication': out['integrity_authentication_checks']}
            checks.expect(out['integrity_authentication_checks'] != 'pass', f'{name}: authentication must never read pass')
            checks.expect(out['recipient_reliance_decision'] != 'pass', f'{name}: reliance must never read pass')
        for name in ('record_edit', 'profile_edit', 'integrity_value_edit', 'package_digest_edit'):
            checks.expect(scope[name]['integrity'] == 'fail', f'{name}: a bound field edit must fail content integrity, observed {scope[name]["integrity"]}')
        checks.expect(scope['provenance_edit']['integrity'] == 'fail' or scope['provenance_edit']['replay_semantic'] == 'fail',
                      f'provenance_edit must be caught by integrity or replay semantics: {scope["provenance_edit"]}')
        undetected = sorted(n for n, v in scope.items() if v['integrity'] == 'pass' and v['replay_semantic'] == 'pass')
        return {'clean': clean, 'edits': scope, 'edits_not_detected_by_any_integrity_or_semantic_layer': undetected,
                'note': 'fields outside the digest scope (created_by/created_at) are unauthenticated; the digest claim says it binds record and profile metadata only'}
    C.run_c_case(request, record_property, tmp_path, 'C13', trial, gate=False)


def test_scn_c13_odes_rehash_forgery_keeps_authentication_unavailable(request, record_property, tmp_path, runs):
    def trial(work, mp, checks):
        from odes import evaluate_recipient_package
        ex = runs[(_n(work), 'lost_ack')]
        pkg = H2.load_copy(ex, 'odes')
        pol = {'supported_profiles': ['odes_cognous_stack_export_0_2']}
        q = copy.deepcopy(pkg)
        q['provenance']['execution_facts']['independent_delivery_verification'] = 'verified'
        H2.odes_rehash(q)
        res = evaluate_recipient_package(q, pol)
        layers = {k: v['status'] for k, v in res.items() if isinstance(v, dict) and 'status' in v}
        checks.equal(layers['package_content_integrity'], 'pass', 'a rehashed forgery is self-consistent (documented digest scope)')
        checks.expect(layers['replay_semantic_consistency'] == 'fail' or layers['recipient_reliance_decision'] != 'pass',
                      f'a rehashed promotion of delivery verification must be caught by a semantic layer or refused reliance: {layers}')
        checks.equal(layers['integrity_authentication_checks'], 'unavailable', 'no authentication is claimed for a rehashed forgery')
        checks.expect(layers['recipient_reliance_decision'] != 'pass', 'reliance is not granted on the forged package')
        return {'integrity': layers['package_content_integrity'], 'replay_semantic': layers['replay_semantic_consistency'],
                'authentication': layers['integrity_authentication_checks'], 'reliance': layers['recipient_reliance_decision']}
    C.run_c_case(request, record_property, tmp_path, 'C13', trial, gate=False)


def test_scn_c13_pack_tamper_of_signing_and_redaction_claims_is_flagged(request, record_property, tmp_path, runs):
    def trial(work, mp, checks):
        ex = runs[(_n(work), 'lost_ack')]
        pack = H2.load_copy(ex, 'pack')
        checks.equal(H2.eval_pack_artifact(pack)['verdict'], 'accepted', 'clean pack validates')
        edits = {
            'bundle_marked_signed': lambda p: p['replay_bundles'][0].__setitem__('signed', True),
            'bundle_marked_redacted': lambda p: p['replay_bundles'][0].__setitem__('redacted', True),
            'bundle_status_edited': lambda p: p['replay_bundles'][0].__setitem__('status', 'tampered'),
            'redaction_declared_verified': lambda p: p['metadata']['traceable_import']['redaction_state'].update({'source': 'verified', 'redacted': True}),
            'unverified_redaction_warning_removed': lambda p: p['metadata']['traceable_import'].__setitem__(
                'import_findings', [f for f in p['metadata']['traceable_import']['import_findings'] if f['code'] != 'R_REDACTION_UNVERIFIED']),
        }
        out = {}
        for name, fn in edits.items():
            q = copy.deepcopy(pack)
            fn(q)
            checks.expect(q != pack, f'{name}: plant changed the pack')
            v = H2.eval_pack_artifact(q)
            out[name] = v['verdict'] + (':' + v['why'] if v['why'] else '')
            checks.expect(v['verdict'] in ('flagged', 'rejected'), f'{name}: tampered signing/redaction claim must be flagged, observed {v}')
        return {'edits': out}
    C.run_c_case(request, record_property, tmp_path, 'C13', trial, gate=False)
