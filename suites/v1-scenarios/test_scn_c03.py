"""SCN-C03 Forged and replayed attestation (executed against BitRep @ 5b5077da, The Index @ d5e45d27 and the frozen F5b reference).

SPDX-License-Identifier: Apache-2.0

Stimulus (catalog C03): tampered bytes, substituted issuer, unknown or revoked key and prohibited replay, each as a
separate variant. Required observation: rejected evidence never becomes accepted support or execution authority; record
the temporal key semantics.

Surfaces (each variant is exercised independently, each case executes twice and is compared):

  BitRep verifier (library and the pinned /verify + /attest admission router)  - variants rejected, never stored;
  BitRep temporal key semantics (boundary matrix)                              - recorded and asserted;
  The Index Python API link route                                              - the pinned component accepts a link whose
        attestor identity is unverifiable (defect #23). These cases are EXPECTED TO FAIL at the frozen pin: a FAIL is the
        correct honest result and is never converted to a pass or skipped;
  The Index chain-side adapter (chain/python/bitrep_adapter.py)                - the profile route that does verify;
  The Index chain contract                                                     - stores a statement commitment only;
  Control Plane runtime evidence (route A, hard gate)                          - forged/replayed producer evidence never
        becomes execution authority: zero effects.

BitRep/Index cases are skipped with the reason when SCN_BITREP_DIR / SCN_INDEX_DIR / SCN_INDEX_CHAIN_DIR are unset.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import _c_2b_helpers as C
from _c_2b_helpers import no_network, pinned_reference  # noqa: F401  (fixtures)

HERE = Path(__file__).resolve().parent


@pytest.fixture(scope='module')
def br():
    pin = C.external_pin('SCN_BITREP_DIR', C.FROZEN_BITREP, 'BitRep')
    yield C.bitrep(pin)
    C.require_pristine(pin, C.FROZEN_BITREP, 'BitRep')


@pytest.fixture(scope='module')
def index_pin():
    pin = C.external_pin('SCN_INDEX_DIR', C.FROZEN_INDEX, 'The Index')
    yield pin
    C.require_pristine(pin, C.FROZEN_INDEX, 'The Index')


@pytest.fixture(scope='module')
def chain_dir(index_pin):
    import os
    value = os.environ.get('SCN_INDEX_CHAIN_DIR')
    if not value:
        pytest.skip('SCN_INDEX_CHAIN_DIR is not set: a node_modules-bearing copy of the pinned Index chain/ was not provided '
                    '(CI must run `npm ci --ignore-scripts` in a copy of chain/); not a pass.')
    C.verify_chain_copy(index_pin, value)
    return Path(value)


# ------------------------------------------------------------------------------------------------
# BitRep: tampered bytes / substituted issuer / unknown or revoked key  (each variant independent)
# ------------------------------------------------------------------------------------------------
MALLORY = C.key_record('issuer:mallory', 'key:1', C.SEED_M)


def _tamper(field, value):
    def build(br_):
        env = C.signed_envelope(br_)
        env['statement'][field] = value
        return env, C.trust_doc(), C.NOW
    return build


def _alter_env(fn, doc=None, now=C.NOW):
    def build(br_):
        env = C.signed_envelope(br_)
        fn(br_, env)
        return env, (doc() if callable(doc) else doc) or C.trust_doc(), now
    return build


def _signed_by(seed, doc, **over):
    def build(br_):
        return C.signed_envelope(br_, seed, **over), doc() if callable(doc) else doc, C.NOW
    return build


VARIANTS = {
    # ---- tampered bytes
    'tamper_subject': ('tampered_bytes', _tamper('subject', 'claim:43'), 'invalid_signature'),
    'tamper_content_digest': ('tampered_bytes', _tamper('content_digest', C.content_digest(b'other bytes')), 'invalid_signature'),
    'tamper_expiry_extended': ('tampered_bytes', _tamper('expires_at', C.NOW + 10_000), 'invalid_signature'),
    'tamper_attestation_id': ('tampered_bytes', _tamper('attestation_id', 'att-999'), 'invalid_signature'),
    'tamper_statement_type': ('tampered_bytes', _tamper('statement_type', 'retracts'), 'invalid_signature'),
    'signature_one_bit_flipped': ('tampered_bytes', _alter_env(lambda b, e: e.update(signature=C.flip_bit(e['signature']))), 'invalid_signature'),
    'signature_zeroed': ('tampered_bytes', _alter_env(lambda b, e: e.update(signature=__import__('base64').b64encode(bytes(64)).decode())), 'invalid_signature'),
    'signature_noncanonical_encoding': ('tampered_bytes', _alter_env(lambda b, e: e.update(signature='A' * 88)), 'malformed_signature'),
    'signature_of_another_statement': ('tampered_bytes', _alter_env(lambda b, e: e.update(signature=C.signed_envelope(b, attestation_id='att-other')['signature'])), 'invalid_signature'),
    'unsupported_protocol_version': ('tampered_bytes', _signed_by(C.SEED_A, C.trust_doc, protocol_version='bitrep-attestation/2'), 'unsupported_version'),
    'unsupported_algorithm': ('tampered_bytes', _signed_by(C.SEED_A, C.trust_doc, algorithm='RS256'), 'unsupported_algorithm'),
    # ---- substituted issuer
    'issuer_unregistered_attacker_with_own_key': ('substituted_issuer', _signed_by(C.SEED_M, C.trust_doc, issuer='issuer:mallory'), 'unknown_key'),
    'issuer_claims_alice_but_attacker_signs': ('substituted_issuer', _signed_by(C.SEED_M, C.trust_doc), 'invalid_signature'),
    'issuer_key_id_cross_binding': ('substituted_issuer', _signed_by(C.SEED_M, lambda: C.trust_doc([C.key_record(), C.key_record('issuer:mallory', 'key:m', C.SEED_M)]), key_id='key:m'), 'unknown_key'),
    'issuer_edited_after_signing_to_other_registered_issuer': ('substituted_issuer', _alter_env(
        lambda b, e: e['statement'].update(issuer='issuer:bob'), doc=lambda: C.trust_doc([C.key_record(), C.key_record('issuer:bob', 'key:1', C.SEED_B)])), 'invalid_signature'),
    # ---- unknown or revoked key
    'key_unknown_id': ('unknown_or_revoked_key', _signed_by(C.SEED_A, C.trust_doc, key_id='key:unknown'), 'unknown_key'),
    'key_revoked_in_force': ('unknown_or_revoked_key', _signed_by(C.SEED_A, lambda: C.trust_doc([C.key_record(revoked_at=C.NOW - 30)])), 'key_revoked'),
    'key_revoked_at_evaluation_instant': ('unknown_or_revoked_key', _signed_by(C.SEED_A, lambda: C.trust_doc([C.key_record(revoked_at=C.NOW)])), 'key_revoked'),
    'key_revoked_before_issuance_backdated_statement': ('unknown_or_revoked_key', _signed_by(C.SEED_A, lambda: C.trust_doc([C.key_record(revoked_at=C.NOW - 200)])), 'key_revoked'),
    'key_expired': ('unknown_or_revoked_key', _signed_by(C.SEED_A, lambda: C.trust_doc([C.key_record(valid_until=C.NOW)])), 'key_expired'),
    'key_not_yet_valid': ('unknown_or_revoked_key', _signed_by(C.SEED_A, lambda: C.trust_doc([C.key_record(valid_from=C.NOW + 1)])), 'key_not_yet_valid'),
    'issuance_outside_key_validity': ('unknown_or_revoked_key', _signed_by(C.SEED_A, lambda: C.trust_doc([C.key_record(valid_from=C.NOW - 5)])), 'issuance_outside_key_validity'),
    'retired_key_after_rotation': ('unknown_or_revoked_key', _signed_by(C.SEED_A, lambda: C.trust_doc([
        C.key_record('issuer:alice', 'key:1', C.SEED_A, valid_until=C.NOW - 1), C.key_record('issuer:alice', 'key:2', C.SEED_B, valid_from=C.NOW - 20)])), 'key_expired'),
}


def _no_domain(br_):
    return C.signed_envelope(br_, C.SEED_A, domain_separated=False), C.trust_doc(), C.NOW


VARIANTS['signature_without_domain_separation'] = ('tampered_bytes', _no_domain, 'invalid_signature')


@pytest.mark.parametrize('variant', sorted(VARIANTS))
def test_scn_c03_bitrep_rejects_forged_attestation_variant(request, record_property, tmp_path, br, variant):
    klass, build, expected_reason = VARIANTS[variant]

    def trial(work, mp, checks):
        # detector calibration: an untampered statement under the unmodified snapshot IS verified (the rejection below is not vacuous)
        control = C.verify_dict(br, C.signed_envelope(br), C.trust_doc())
        checks.equal((control['outcome'], control['reason'], control['assurance']), ('verified', 'ok', 'issuer_signature_only'), 'positive control')
        env, doc, now = build(br)
        lib = C.verify_dict(br, env, doc, now)
        checks.equal((lib['outcome'], lib['reason'], lib['assurance']), ('rejected', expected_reason, 'none'), f'{variant}: library verdict')
        http = C.BitRepHttp(br, doc, now)
        verify = C.http_view(http.post('/verify', env))
        attest = C.http_view(http.post('/attest', env))
        checks.equal(verify['status'], 200, 'POST /verify is a well-formed request with a rejected result')
        checks.equal(verify['reason'], expected_reason, 'POST /verify reports the rejection reason')
        checks.equal(attest['status'], 422, 'POST /attest refuses admission')
        checks.equal(attest['reason'], expected_reason, 'POST /attest reports the rejection reason')
        stored = http.stored()
        checks.equal(stored, [], 'rejected evidence is never written to accepted storage')
        return {'variant': variant, 'class': klass, 'control': control, 'library': lib, 'http_verify': verify, 'http_attest': attest,
                'accepted_records': len(stored)}
    C.run_c_case(request, record_property, tmp_path, 'C03', trial, gate=False,
                 extra={'surface': 'BitRep verifier + /verify + /attest', 'pin': C.FROZEN_BITREP})


WIRE_VARIANTS = ['extra_statement_member', 'duplicate_statement_member', 'non_json_constant', 'oversized_body', 'missing_signature', 'coercible_integer_type']


def _wire_body(br_, variant):
    env = C.signed_envelope(br_)
    if variant == 'extra_statement_member':
        env['statement']['unsigned_extra'] = 'x'
        return json.dumps(env).encode(), 422, 'malformed_input'
    if variant == 'duplicate_statement_member':
        raw = json.dumps(env).replace('"subject": "claim:42"', '"subject": "claim:42", "subject": "claim:43"').encode()
        return raw, 422, 'malformed_input'
    if variant == 'non_json_constant':
        raw = json.dumps(env).replace(str(C.NOW + 100), 'NaN').encode()
        return raw, 422, 'malformed_input'
    if variant == 'oversized_body':
        env['padding'] = 'x' * 17000
        return json.dumps(env).encode(), 413, 'input_too_large'
    if variant == 'missing_signature':
        del env['signature']
        return json.dumps(env).encode(), 422, 'malformed_input'
    env['statement']['issued_at'] = str(env['statement']['issued_at'])
    return json.dumps(env).encode(), 422, 'malformed_input'


@pytest.mark.parametrize('variant', WIRE_VARIANTS)
def test_scn_c03_bitrep_rejects_malformed_wire_forgery_before_verification(request, record_property, tmp_path, br, variant):
    def trial(work, mp, checks):
        raw, status, reason = _wire_body(br, variant)
        http = C.BitRepHttp(br, C.trust_doc())
        verify = C.http_view(http.post('/verify', raw))
        attest = C.http_view(http.post('/attest', raw))
        checks.equal((verify['status'], verify['reason']), (status, reason), 'POST /verify wire rejection')
        checks.equal((attest['status'], attest['reason']), (status, reason), 'POST /attest wire rejection')
        checks.equal(http.stored(), [], 'wire-rejected evidence is never stored')
        return {'variant': variant, 'http_verify': verify, 'http_attest': attest, 'accepted_records': len(http.stored())}
    C.run_c_case(request, record_property, tmp_path, 'C03', trial, gate=False, extra={'surface': 'BitRep wire boundary', 'pin': C.FROZEN_BITREP})


# ------------------------------------------------------------------------------------------------
# BitRep: prohibited replay (stateful, through the pinned admission router)
# ------------------------------------------------------------------------------------------------
REPLAYS = ['resubmit_identical_statement', 'same_issuer_and_id_different_statement', 'replay_after_attestation_expiry',
           'replay_after_key_revocation', 'replay_into_other_audience', 'replay_with_stale_trust_snapshot',
           'replay_before_not_before', 'tampered_retry_of_accepted_statement']


def _replay(br_, name, checks):
    env = C.signed_envelope(br_)
    http = C.BitRepHttp(br_, C.trust_doc())
    first = C.http_view(http.post('/attest', env))
    checks.equal((first['status'], first['admission']), (201, 'accepted'), 'baseline admission of the genuine statement')
    digest = http.stored()[0][2]
    out = {'first': first}
    if name == 'resubmit_identical_statement':
        again = C.http_view(http.post('/attest', env))
        out['replay'] = again
        # documented semantics: an attestation is evidence ingestion, NOT a one-time action-authorization token
        checks.equal((again['status'], again['admission']), (200, 'duplicate'), 'identical replay is an idempotent duplicate')
        checks.equal(len(http.stored()), 1, 'exactly one stored record after replay')
    elif name == 'same_issuer_and_id_different_statement':
        other = C.signed_envelope(br_, subject='claim:99')
        r = C.http_view(http.post('/attest', other))
        out['replay'] = r
        checks.equal((r['status'], r['reason']), (409, 'attestation_id_conflict'), 'validly signed conflicting statement under a used id')
        checks.equal(len(http.stored()), 1, 'conflicting replay writes nothing')
    elif name == 'replay_after_attestation_expiry':
        http.state['now'] = C.NOW + 100
        r = C.http_view(http.post('/attest', env))
        out['replay'] = r
        checks.equal((r['status'], r['reason']), (422, 'attestation_expired'), 'expired statement is rejected even though previously admitted')
        got = http.client.get(f'/attestations/{digest}').json()
        out['stored_record_now'] = {'at_acceptance': got['verification_at_acceptance']['outcome'], 'current': got['verification']['outcome'],
                                    'current_reason': got['verification']['reason']}
        checks.equal((got['verification_at_acceptance']['outcome'], got['verification']['outcome']), ('verified', 'rejected'),
                     'history retained as an unsigned acceptance record; current verification is re-evaluated')
    elif name == 'replay_after_key_revocation':
        http.state['doc'] = C.trust_doc([C.key_record(revoked_at=C.NOW + 5)])
        http.state['now'] = C.NOW + 5
        r = C.http_view(http.post('/attest', env))
        out['replay'] = r
        checks.equal((r['status'], r['reason']), (422, 'key_revoked'), 'revoked-key retry rejected despite prior admission')
        got = http.client.get(f'/attestations/{digest}').json()
        out['stored_record_now'] = {'current': got['verification']['outcome'], 'current_reason': got['verification']['reason']}
        checks.equal(got['verification']['outcome'], 'rejected', 'stored record no longer reads as current assurance')
    elif name == 'replay_into_other_audience':
        other = C.BitRepHttp(br_, C.trust_doc(audience='index:other-deployment'))
        r = C.http_view(other.post('/attest', env))
        out['replay'] = r
        checks.equal((r['status'], r['reason']), (422, 'audience_mismatch'), 'statement bound to another audience is refused')
        checks.equal(other.stored(), [], 'nothing stored in the other deployment')
    elif name == 'replay_with_stale_trust_snapshot':
        http.state['now'] = C.NOW + 1000  # snapshot valid_until is exclusive
        r = C.http_view(http.post('/attest', env))
        out['replay'] = r
        checks.equal(r['status'], 503, 'expired trust snapshot fails closed')
        checks.equal(r['reason'], 'trust_unavailable', 'fail-closed reason')
    elif name == 'replay_before_not_before':
        early = C.BitRepHttp(br_, C.trust_doc(), now=C.NOW - 20)
        r = C.http_view(early.post('/attest', env))
        out['replay'] = r
        checks.equal((r['status'], r['reason']), (422, 'not_yet_valid'), 'statement presented before its not_before')
        checks.equal(early.stored(), [], 'nothing stored')
    else:  # tampered_retry_of_accepted_statement
        forged = copy.deepcopy(env)
        forged['statement']['subject'] = 'claim:43'
        r = C.http_view(http.post('/attest', forged))
        out['replay'] = r
        checks.equal((r['status'], r['reason']), (422, 'invalid_signature'), 'tampered retry rejected')
        checks.equal(len(http.stored()), 1, 'accepted record unchanged by the forged retry')
    out['stored_after'] = len(http.stored())
    return out


@pytest.mark.parametrize('name', REPLAYS)
def test_scn_c03_bitrep_prohibited_replay_variant(request, record_property, tmp_path, br, name):
    def trial(work, mp, checks):
        return {'variant': name, **_replay(br, name, checks)}
    C.run_c_case(request, record_property, tmp_path, 'C03', trial, gate=False,
                 extra={'surface': 'BitRep /attest replay semantics', 'pin': C.FROZEN_BITREP,
                        'note': 'identical replay is an idempotent duplicate by contract (not a one-time token); prohibited replays are the others'})


# ------------------------------------------------------------------------------------------------
# BitRep: temporal key semantics (recorded boundary matrix)
# ------------------------------------------------------------------------------------------------

def _matrix(br_):
    rows = []

    def row(label, env, doc, now, expected):
        got = C.verify_dict(br_, env, doc, now)
        rows.append({'label': label, 'now_offset': now - C.NOW, 'outcome': got['outcome'], 'reason': got['reason'], 'expected': expected})
    base = C.signed_envelope(br_, issued_at=C.NOW - 50, not_before=C.NOW - 50)
    row('key revoked one second in the future (not yet in force)', base, C.trust_doc([C.key_record(revoked_at=C.NOW + 1)]), C.NOW, ['verified', 'ok'])
    row('revoked_at == now (inclusive)', base, C.trust_doc([C.key_record(revoked_at=C.NOW)]), C.NOW, ['rejected', 'key_revoked'])
    row('revoked_at in the past, statement issued earlier (no grandfathering, not backdatable)', base, C.trust_doc([C.key_record(revoked_at=C.NOW - 30)]), C.NOW, ['rejected', 'key_revoked'])
    env = C.signed_envelope(br_)
    row('key valid_until == now (half-open: expired)', env, C.trust_doc([C.key_record(valid_until=C.NOW)]), C.NOW, ['rejected', 'key_expired'])
    row('key valid_until == now+1 (still valid)', env, C.trust_doc([C.key_record(valid_until=C.NOW + 1)]), C.NOW, ['verified', 'ok'])
    row('key valid_from == now+1 (not yet valid)', env, C.trust_doc([C.key_record(valid_from=C.NOW + 1)]), C.NOW, ['rejected', 'key_not_yet_valid'])
    row('key valid_from == now (inclusive start; issuance precedes it)', env, C.trust_doc([C.key_record(valid_from=C.NOW)]), C.NOW, ['rejected', 'issuance_outside_key_validity'])
    row('statement expires_at - 1 (still valid; no skew allowance)', env, C.trust_doc(), C.NOW + 99, ['verified', 'ok'])
    row('statement expires_at == now (half-open: expired)', env, C.trust_doc(), C.NOW + 100, ['rejected', 'attestation_expired'])
    future = C.signed_envelope(br_, issued_at=C.NOW + 1, not_before=C.NOW + 1, expires_at=C.NOW + 100)
    row('issued one second after now (no clock-skew allowance)', future, C.trust_doc(), C.NOW, ['rejected', 'not_yet_valid'])
    old = C.signed_envelope(br_, issued_at=C.NOW - 50, not_before=C.NOW - 50)
    rotation = C.trust_doc([C.key_record('issuer:alice', 'key:1', C.SEED_A, valid_from=C.NOW - 100, valid_until=C.NOW - 10),
                            C.key_record('issuer:alice', 'key:2', C.SEED_B, valid_from=C.NOW - 20)])
    row('rotation: statement valid at issuance, old key retired at evaluation', old, rotation, C.NOW, ['rejected', 'key_expired'])
    row('rotation: new key signs for a time before its validity', C.signed_envelope(br_, C.SEED_B, key_id='key:2', issued_at=C.NOW - 50, not_before=C.NOW - 50), rotation, C.NOW, ['rejected', 'issuance_outside_key_validity'])
    row('rotation: new key, current statement', C.signed_envelope(br_, C.SEED_B, key_id='key:2'), rotation, C.NOW, ['verified', 'ok'])
    row('rotation: retired key signature presented under the new key id', C.signed_envelope(br_, C.SEED_A, key_id='key:2'), rotation, C.NOW, ['rejected', 'invalid_signature'])
    row('trust snapshot published_at == now (inclusive)', env, C.trust_doc(published_at=C.NOW), C.NOW, ['verified', 'ok'])
    row('trust snapshot published in the future (fails closed)', env, C.trust_doc(published_at=C.NOW + 1), C.NOW, ['unavailable', 'trust_unavailable'])
    row('trust snapshot valid_until == now (exclusive; fails closed)', env, C.trust_doc(valid_until=C.NOW), C.NOW, ['unavailable', 'trust_unavailable'])
    return rows


def test_scn_c03_bitrep_temporal_key_semantics_are_as_documented(request, record_property, tmp_path, br):
    def trial(work, mp, checks):
        rows = _matrix(br)
        for r in rows:
            checks.equal([r['outcome'], r['reason']], r['expected'], r['label'])
        contract = (C.Path(br.pin) / 'docs' / 'VERIFICATION_CONTRACT_V1.md').read_text(encoding='utf-8')
        flat = ' '.join(contract.split())
        for phrase in ('[valid_from, valid_until)', 'strictly before `expires_at`', 'There is no clock-skew allowance',
                       'Once `now >= revoked_at`', 'including statements issued before revocation',
                       'The server\'s current time must be in `[published_at, valid_until)`',
                       'Historical verification is **not supported**'):
            checks.expect(phrase in flat, f'contract documents: {phrase}')
        return {'temporal_key_semantics': rows,
                'declared': {'key_interval': '[valid_from, valid_until) at both issuance and evaluation', 'revocation': 'now >= revoked_at rejects every signature of the key, including earlier statements',
                             'statement': 'issued_at/not_before <= now < expires_at, no skew', 'snapshot': '[published_at, valid_until) else fail closed',
                             'historical_as_of_verification': 'not supported (acceptance record is unsigned history, not a signing-time proof)'}}
    C.run_c_case(request, record_property, tmp_path, 'C03', trial, gate=False, extra={'surface': 'BitRep temporal key semantics', 'pin': C.FROZEN_BITREP})


# ------------------------------------------------------------------------------------------------
# The Index Python API: unverifiable attestor identity accepted as support (defect #23 at the frozen pin)
# ------------------------------------------------------------------------------------------------
CLAIM = {'canonical_text': 'C03 claim alpha', 'semantic_representation': {'subject': 'a', 'predicate': 'b'}, 'domains': ['c03'], 'created_by': 'c03_user'}
EVIDENCE = {'type': 'experiment', 'source_identifier': 'doi:10.1234/c03-source',
            'metadata': {'methodology': 'double-blind RCT', 'sample_size': 1000, 'uncertainty': 0.05}, 'submitted_by': 'c03_user'}
FORGED_IDENTITIES = {
    'unregistered_forged_identity': 'forged-attestor-absent-from-every-registry',
    'substituted_issuer_identity': 'issuer:mallory',
    'identity_of_unknown_key': 'issuer:alice#key:unknown',
    'identity_of_revoked_key': 'issuer:alice#key:1(revoked)',
}


def _link_attempt(client, attested_by):
    claim = client.post('/api/v1/claims/', json=CLAIM).json()
    ev = client.post('/api/v1/evidence/', json=EVIDENCE).json()
    r = client.post('/api/v1/evidence/links', json={'claim_id': claim['id'], 'evidence_id': ev['id'], 'relation_type': 'supports',
                                                    'strength': 1.0, 'attested_by': attested_by})
    status = client.get(f'/api/v1/evidence/epistemic-status/{claim["id"]}').json()
    return r.status_code, status


@pytest.mark.parametrize('variant', sorted(FORGED_IDENTITIES))
def test_scn_c03_index_api_unverifiable_attestation_never_becomes_accepted_support(request, record_property, tmp_path, index_pin, variant):
    """EXPECTED TO FAIL at the frozen pin (defect #23): the link route stores any non-empty attested_by string."""
    def trial(work, mp, checks):
        client = C.index_client(index_pin)
        code, status = _link_attempt(client, FORGED_IDENTITIES[variant])
        stored = 200 <= code < 300
        checks.expect(not stored, f'link with unverifiable attestor {variant!r} was ACCEPTED (HTTP {code}); rejected evidence became accepted support')
        checks.equal(status.get('supporting_weight'), 0, f'supporting weight after the forged link: {status.get("supporting_weight")}')
        return {'variant': variant, 'link_http_status': code, 'link_stored': stored, 'supporting_weight': status.get('supporting_weight'),
                'status': status.get('status'), 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    C.run_c_case(request, record_property, tmp_path, 'C03', trial, gate=False,
                 extra={'surface': 'The Index API POST /api/v1/evidence/links', 'pin': C.FROZEN_INDEX, 'known_defect': '#23',
                        'expected_at_frozen_pin': 'FAIL (a FAIL is the correct honest result)',
                        'note': 'the link model has no field for a BitRep envelope; the route performs no verification'})


def test_scn_c03_index_api_detector_calibration_controls(request, record_property, tmp_path):
    """The detector used above flags an accept-all stub and clears a reject-all stub (a pass/fail there is not vacuous)."""
    def trial(work, mp, checks):
        from fastapi import FastAPI, HTTPException
        from fastapi.testclient import TestClient

        def stub(accept):
            app = FastAPI()

            @app.post('/api/v1/claims/')
            def claim():
                return {'id': 'c1'}

            @app.post('/api/v1/evidence/')
            def ev():
                return {'id': 'e1'}

            @app.post('/api/v1/evidence/links', status_code=201)
            def link():
                if not accept:
                    raise HTTPException(status_code=403, detail='unverified attestation')
                return {'id': 'l1'}

            @app.get('/api/v1/evidence/epistemic-status/{cid}')
            def status(cid: str):
                return {'supporting_weight': 1.0 if accept else 0, 'status': 'x'}
            return TestClient(app)
        a, _ = _link_attempt(stub(True), 'forged')
        b, _ = _link_attempt(stub(False), 'forged')
        checks.expect(200 <= a < 300, 'accept-all stub is flagged as accepting')
        checks.expect(not 200 <= b < 300, 'reject-all stub is cleared')
        return {'accept_all_http': a, 'reject_all_http': b}
    C.run_c_case(request, record_property, tmp_path, 'C03', trial, gate=False, extra={'surface': 'detector calibration'})


# ------------------------------------------------------------------------------------------------
# The Index chain-side adapter (the profile route that verifies) - variants never verify
# ------------------------------------------------------------------------------------------------
ADAPTER_VARIANTS = ['altered_content_bytes', 'missing_content', 'subject_replayed_from_other_claim', 'audience_replayed_to_other_deployment',
                    'statement_digest_mismatch', 'untrusted_snapshot_digest', 'unsigned_result_presented_as_envelope', 'duplicate_json_member',
                    'tampered_signature', 'revoked_key', 'unknown_key', 'expired_statement', 'oversized_envelope']


def _adapter_case(br_, ad, variant):
    content = b'synthetic supporting evidence'
    chain_subject = 'index:eip155:31337:0x5fbdb2315678afecb367f032d93f642f64180aa3:v1:claim:ab12'
    chain_audience = 'index:eip155:31337:0x5fbdb2315678afecb367f032d93f642f64180aa3:v1'
    over = dict(subject=chain_subject, audience=chain_audience, statement_type='index-support/1', content_digest=C.content_digest(content))
    env = C.signed_envelope(br_, **over)
    doc = C.trust_doc(audience=chain_audience)
    att = br_.AttestationEnvelope.model_validate(env)
    reg = br_.TrustRegistry.model_validate(doc)
    expected = {'subject': chain_subject, 'statement_type': 'index-support/1', 'audience': chain_audience,
                'content_digest': C.content_digest(content), 'statement_digest': br_.statement_digest(att.statement)}
    args = dict(raw=json.dumps(env).encode(), content=content, expected=expected, registry=reg,
                trusted_snapshot_digest=reg.fingerprint(), now=C.NOW)
    if variant == 'altered_content_bytes':
        args['content'] = b'altered'
    elif variant == 'missing_content':
        args['content'] = None
    elif variant == 'subject_replayed_from_other_claim':
        args['expected'] = {**expected, 'subject': chain_subject.replace('ab12', 'cd34')}
    elif variant == 'audience_replayed_to_other_deployment':
        args['expected'] = {**expected, 'audience': 'index:eip155:1:0xabc:v1'}
    elif variant == 'statement_digest_mismatch':
        args['expected'] = {**expected, 'statement_digest': 'sha256:' + '0' * 64}
    elif variant == 'untrusted_snapshot_digest':
        args['trusted_snapshot_digest'] = 'sha256:' + '0' * 64
    elif variant == 'unsigned_result_presented_as_envelope':
        args['raw'] = json.dumps({'result_version': 'bitrep-verification/1', 'outcome': 'verified', 'reason': 'ok'}).encode()
    elif variant == 'duplicate_json_member':
        args['raw'] = b'{"statement":{},"statement":{}}'
    elif variant == 'tampered_signature':
        bad = copy.deepcopy(env)
        bad['signature'] = C.flip_bit(bad['signature'])
        args['raw'] = json.dumps(bad).encode()
    elif variant == 'revoked_key':
        reg2 = br_.TrustRegistry.model_validate(C.trust_doc([C.key_record(revoked_at=C.NOW)], audience=chain_audience))
        args.update(registry=reg2, trusted_snapshot_digest=reg2.fingerprint())
    elif variant == 'unknown_key':
        reg2 = br_.TrustRegistry.model_validate(C.trust_doc([C.key_record(key_id='key:other')], audience=chain_audience))
        args.update(registry=reg2, trusted_snapshot_digest=reg2.fingerprint())
    elif variant == 'expired_statement':
        args['now'] = C.NOW + 100
    elif variant == 'oversized_envelope':
        args['raw'] = b' ' * 20000 + json.dumps(env).encode()
    try:
        result = ad.evaluate(**args)
        return {'verified': result['outcome'] == 'verified', 'outcome': result['outcome'], 'reason': result['reason']}
    except Exception as exc:
        return {'verified': False, 'outcome': 'refused', 'reason': C.exc_text(exc)}


def test_scn_c03_index_chain_adapter_positive_control(request, record_property, tmp_path, br, index_pin):
    def trial(work, mp, checks):
        ad = C.index_adapter(index_pin, br.pin)
        got = _adapter_case(br, ad, 'control')
        checks.expect(got['verified'], f'untampered envelope with correct bindings verifies (detector not vacuous): {got}')
        return {'control': got}
    C.run_c_case(request, record_property, tmp_path, 'C03', trial, gate=False, extra={'surface': 'Index chain adapter (BitRep delegated)'})


@pytest.mark.parametrize('variant', ADAPTER_VARIANTS)
def test_scn_c03_index_chain_adapter_never_verifies_forged_or_replayed_attestation(request, record_property, tmp_path, br, index_pin, variant):
    def trial(work, mp, checks):
        ad = C.index_adapter(index_pin, br.pin)
        got = _adapter_case(br, ad, variant)
        checks.expect(not got['verified'], f'{variant}: forged/replayed attestation was VERIFIED by the Index adapter: {got}')
        return {'variant': variant, 'result': {'outcome': got['outcome'], 'reason': C.H2.normalise_reason(got['reason'])}}
    C.run_c_case(request, record_property, tmp_path, 'C03', trial, gate=False, extra={'surface': 'Index chain adapter (BitRep delegated)', 'pin': C.FROZEN_INDEX})


# ------------------------------------------------------------------------------------------------
# The Index chain contract: a statement commitment is stored, never a verified flag
# ------------------------------------------------------------------------------------------------

def test_scn_c03_index_chain_statement_commitment_carries_no_verification(request, record_property, tmp_path, chain_dir):
    driver = HERE / '_c_index_chain_driver.mjs'

    def trial(work, mp, checks):
        obs = C.run_node_driver(driver, chain_dir, work)
        s = obs['statement_commitment']
        checks.equal(sorted(s['evidence_record_fields']), ['claim', 'content', 'manifest', 'relation', 'statement', 'submitter'],
                     'the reconstructed evidence record has no verification/verified/assurance field')
        checks.equal(s['forged_statement_commitment_stored'], True, 'observation: an unverified (forged) statement commitment can be recorded (documented as an unverified commitment)')
        checks.equal(s['verified_flag_present'], False, 'no caller-supplied verified flag can be stored')
        checks.equal(s['reconstructed_statement_equals_commitment'], True, 'the stored value is exactly the commitment')
        return {'statement_commitment': s}
    C.run_c_case(request, record_property, tmp_path, 'C03', trial, gate=False,
                 extra={'surface': 'Index chain contract (disposable loopback Ganache chain)', 'pin': C.FROZEN_INDEX,
                        'interpretation': 'chain inclusion is not BitRep verification; a verifier must use the adapter above'})


# ------------------------------------------------------------------------------------------------
# Control Plane runtime evidence: forged or replayed producer evidence never becomes execution authority (hard gate)
# ------------------------------------------------------------------------------------------------
CP_VARIANTS = {
    # variant: (class, expected refusal reason)
    'tampered_validator_value': ('tampered_bytes', 'evidence_signature_invalid'),
    'signature_one_bit_flipped': ('tampered_bytes', 'evidence_signature_invalid'),
    'signature_truncated': ('tampered_bytes', 'evidence_signature_invalid'),
    'unsigned_record': ('tampered_bytes', 'evidence_unsigned'),
    'record_shape_tampered': ('tampered_bytes', 'evidence_record_invalid'),
    'producer_id_substituted': ('substituted_issuer', 'evidence_producer_untrusted'),
    'attacker_signs_as_trusted_producer': ('substituted_issuer', 'evidence_signature_invalid'),
    'criterion_names_unknown_producer': ('unknown_key', 'evidence_producer_untrusted'),
    'trusted_key_withdrawn_from_profile': ('unknown_or_revoked_key', 'evidence_producer_untrusted'),
    'version_unsupported_but_validly_signed': ('tampered_bytes', 'evidence_record_version_unsupported'),
    'replay_for_other_tenant': ('replay', 'evidence_subject_mismatch'),
    'replay_for_other_obligation': ('replay', 'evidence_subject_mismatch'),
    'replay_with_other_observation_time': ('replay', 'evidence_subject_mismatch'),
    'replay_for_other_institution': ('replay', 'evidence_subject_mismatch'),
}


def _forge(flow, variant):
    """Apply one forgery to the (single) required evidence record of an already-authorized route-A flow."""
    ch = C.reference().chain
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    status = next(iter(flow.r.evidence.values()))
    envelope = status.validation_record
    if variant == 'tampered_validator_value':
        envelope['statement']['values']['validated_count'] = 999
    elif variant == 'signature_one_bit_flipped':
        raw = bytearray(bytes.fromhex(envelope['signature']))
        raw[0] ^= 1
        envelope['signature'] = raw.hex()
    elif variant == 'signature_truncated':
        envelope['signature'] = envelope['signature'][:-2]
    elif variant == 'unsigned_record':
        status.validation_record = None
    elif variant == 'record_shape_tampered':
        envelope['statement']['unsigned_extra'] = 1
    elif variant == 'producer_id_substituted':
        envelope['statement']['producer_id'] = 'agent'
    elif variant == 'attacker_signs_as_trusted_producer':
        from agent_control_plane.bounded import _canonical_bytes
        attacker = Ed25519PrivateKey.from_private_bytes(bytes(range(7, 39)))
        envelope['signature'] = attacker.sign(_canonical_bytes(envelope['statement'])).hex()
    elif variant == 'criterion_names_unknown_producer':
        crit = next(iter(flow.r.contexts[ch.PROFILE]['runtime_authority']['evidence_criteria'].values()))
        crit['producer_id'] = 'producer-absent-from-trust-profile'
        ch.bind_approval(flow.r, flow.c)
    elif variant == 'trusted_key_withdrawn_from_profile':
        # the only revocation the Control Plane models: the operator removes the key from the trusted profile (a profile
        # change, re-bound into the approval commitment so that the key withdrawal is the only refusing control)
        flow.f.runtime_authority_profile = flow.f.runtime_authority_profile.model_copy(update={'producer_keys': {}})
        ch.bind_approval(flow.r, flow.f.runtime_authority_profile)
    elif variant == 'version_unsupported_but_validly_signed':
        from agent_control_plane.bounded import _canonical_bytes
        from tests.test_runtime_authority import KEY
        envelope['statement']['version'] = 'validation-record/9.9'
        envelope['signature'] = KEY.sign(_canonical_bytes(envelope['statement'])).hex()
    elif variant == 'replay_for_other_tenant':
        C.H1.reference().sign_evidence(status, tenant_id='another-tenant')  # signed for a different tenant than the context's
    elif variant == 'replay_for_other_obligation':
        status.obligation_id = status.obligation_id + ':other'
    elif variant == 'replay_with_other_observation_time':
        status.observed_at = '2026-01-01T00:00:00+00:00'
    elif variant == 'replay_for_other_institution':
        envelope['statement']['institution_id'] = 'institution-other'
        from agent_control_plane.bounded import _canonical_bytes
        from tests.test_runtime_authority import KEY
        envelope['signature'] = KEY.sign(_canonical_bytes(envelope['statement'])).hex()
    else:
        raise AssertionError(variant)


def _refusal_reasons(flow):
    return sorted({r for x in flow.f.records.load().refusals for r in x.reasons})


@pytest.mark.parametrize('variant', sorted(CP_VARIANTS))
def test_scn_c03_control_plane_forged_evidence_never_becomes_execution_authority(request, record_property, tmp_path, pinned_reference, variant):
    klass, reason = CP_VARIANTS[variant]

    def trial(work, mp, checks):
        flow = C.H.flow_a(work, mp)
        _forge(flow, variant)
        res, exc = C.H.execute_a(flow)
        view = C.H.result_view(res, exc)
        summary = C.H.db_summary(flow.dest.path)
        reasons = _refusal_reasons(flow)
        checks.expect(res is not None and res.status == 'denied' and not res.attempted, f'{variant}: forged evidence must be refused at effect time; observed {view}')
        checks.expect(reason in reasons, f'{variant}: expected refusal reason {reason}; recorded {reasons}')
        checks.equal(summary['effects'], [], 'no destination mutation from forged evidence')
        checks.equal(summary['attempts'], [], 'no dispatch attempt for refused evidence')
        return {'variant': variant, 'class': klass, 'result': view, 'refusal_reasons': reasons, 'effects': summary['effects'],
                **C.H.effect_gate(summary)}
    C.run_c_case(request, record_property, tmp_path, 'C03', trial,
                 extra={'surface': 'Control Plane validate_evidence (Ed25519 producer keys, route A)',
                        'temporal_key_semantics': 'NONE: producer_keys is a static host-configured map; there is no key validity interval, expiry or revocation field in RuntimeAuthorityProfile. Withdrawal of a key is a profile change that must be re-approved (profile is bound into the approval commitment).'})


def test_scn_c03_control_plane_valid_evidence_control_authorizes_exactly_once(request, record_property, tmp_path, pinned_reference):
    def trial(work, mp, checks):
        flow = C.H.flow_a(work, mp)
        res, exc = C.H.execute_a(flow)
        summary = C.H.db_summary(flow.dest.path)
        checks.expect(res is not None and res.status == 'executed', f'untampered evidence authorizes the supported route: {C.H.result_view(res, exc)}')
        checks.equal(len(summary['effects']), 1, 'exactly one effect for the genuine evidence (detector is not vacuous)')
        return {'result': C.H.result_view(res, exc), **C.H.effect_gate(summary, authorized_effect_ids={flow.env.effect_id})}
    C.run_c_case(request, record_property, tmp_path, 'C03', trial, extra={'surface': 'Control Plane + runtime route A (positive control)'})


def test_scn_c03_control_plane_replayed_accepted_authorization_executes_once(request, record_property, tmp_path, pinned_reference):
    """Prohibited replay of an already-consumed authorization: later presentations never add an effect."""
    def trial(work, mp, checks):
        flow = C.H.flow_a(work, mp)
        views = []
        for _ in range(3):
            res, exc = C.H.execute_a(flow)
            views.append(C.H.result_view(res, exc))
        summary = C.H.db_summary(flow.dest.path)
        checks.equal(views[0].get('newly_executed'), True, 'first presentation executes')
        checks.equal([v.get('newly_executed') for v in views[1:]], [False, False], 'replays never newly execute')
        checks.equal(len(summary['effects']), 1, 'exactly one durable effect after three presentations')
        return {'views': views, 'effects': summary['effects'], **C.H.effect_gate(summary, authorized_effect_ids={flow.env.effect_id})}
    C.run_c_case(request, record_property, tmp_path, 'C03', trial, extra={'surface': 'route A replay of an accepted authorization'})
