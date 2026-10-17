"""SCN-C04 Evidence supersession and dependence (executed against The Index @ d5e45d27 (old pin) or the re-frozen d17b8ac2).

SPDX-License-Identifier: Apache-2.0

Stimulus (catalog C04): supersede an accepted claim and supply multiple copies of dependent evidence. Required observation:
history survives; current status recomputes from pinned inputs; copied evidence is not counted as independent corroboration.

Two Index surfaces exist at the pin and are exercised separately:

  Python API (app/)  - claims are immutable once accepted (no supersession route exists); evidence links are scored by
        EvidenceService.compute_epistemic_status. The copied-evidence cases are EXPECTED TO FAIL at the old pin
        (defect #24: it counts duplicated evidence as independent). A FAIL there is the correct honest result.
        Links are posted through _index_signing.LinkSigner: unsigned at a service that does not require attestation (old pin),
        validly signed (test-time Ed25519 issuers in a trust snapshot, profile index.link.v1) at the re-frozen Index, so the
        links are genuinely STORED and the scores genuinely computed; a link that is not stored fails the case (no skip).
  Chain profile      - the Solidity lifecycle contract on a disposable loopback Ganache chain: supersession, history,
        reconstruction from logs and the treatment of copied evidence (copies stay visible; the contract computes no score).

Sub-case NOT covered (and why): superseding a claim *through the Python API* and recomputing its status afterwards - the API
exposes no supersession route (its claim model is immutable; the inventory of OpenAPI paths is recorded in the evidence). The
chain supersession and the API scoring are separate, unconnected subsystems at this pin.
Cases skip with the reason when SCN_INDEX_DIR / SCN_INDEX_CHAIN_DIR are unset.
"""
from __future__ import annotations

from pathlib import Path

import pytest

import _c_2b_helpers as C
import _index_signing as S
from _c_2b_helpers import no_network  # noqa: F401  (autouse fixture)

HERE = Path(__file__).resolve().parent
CLAIM = {'canonical_text': 'C04 claim alpha', 'semantic_representation': {'subject': 'a', 'predicate': 'b'}, 'domains': ['c04'], 'created_by': 'c04_user'}
FIELDS = ('status', 'supporting_weight', 'contradicting_weight', 'independence_score', 'robustness_score')


@pytest.fixture(scope='module')
def index_pin():
    pin, sha = S.resolve_index_pin(C)
    yield pin
    C.require_pristine(pin, sha, 'The Index')


@pytest.fixture(scope='module')
def chain_dir(index_pin):
    import os
    value = os.environ.get('SCN_INDEX_CHAIN_DIR')
    if not value:
        pytest.skip('SCN_INDEX_CHAIN_DIR is not set: a node_modules-bearing copy of the pinned Index chain/ was not provided '
                    '(CI must run `npm ci --ignore-scripts` in a copy of chain/); not a pass.')
    C.verify_chain_copy(index_pin, value)
    return Path(value)


def evidence(source='doi:10.1234/same-source', **meta):
    return {'type': 'experiment', 'source_identifier': source,
            'metadata': {'methodology': 'double-blind RCT', 'sample_size': 1000, 'uncertainty': 0.05, **meta}, 'submitted_by': 'c04_user'}


def fresh(pin, work, mp):
    """A fresh Index client (fresh in-memory services) and its link signer (services are process-global: use before building the next)."""
    client = C.index_client(pin)
    return client, S.LinkSigner(client, work, mp.setenv)


def status(client, claim_id):
    s = client.get(f'/api/v1/evidence/epistemic-status/{claim_id}').json()
    return {k: s[k] for k in FIELDS}


def build(client, signer, items):
    """Create a claim and link each (evidence body, attestor, reused evidence id) item; every link must be STORED (200/201)."""
    claim = client.post('/api/v1/claims/', json=CLAIM).json()
    for body, attestor, reuse in items:
        ev = reuse if reuse else client.post('/api/v1/evidence/', json=body).json()['id']
        signer.store_link(claim['id'], ev, attestor)
    assert len(signer.stored_links(claim['id'])) == len(items), 'every link must be stored for the status to be a real measurement'
    return claim['id'], status(client, claim['id'])


# ------------------------------------------------------------------------------------------------
# Python API: copied / dependent evidence must not read as independent corroboration (#24, expected FAIL)
# ------------------------------------------------------------------------------------------------
COPY_VARIANTS = ['five_copies_of_one_source_distinct_metadata', 'five_exact_duplicate_submissions', 'five_copies_attested_by_five_attestors',
                 'one_evidence_record_linked_five_times']


def _copies(client, signer, variant):
    n = 5
    if variant == 'five_copies_of_one_source_distinct_metadata':
        return build(client, signer, [(evidence(copy=i), 'c04_attestor', None) for i in range(n)])
    if variant == 'five_exact_duplicate_submissions':
        return build(client, signer, [(evidence(), 'c04_attestor', None) for _ in range(n)])
    if variant == 'five_copies_attested_by_five_attestors':
        return build(client, signer, [(evidence(copy=i), f'attestor_{i}', None) for i in range(n)])
    claim = client.post('/api/v1/claims/', json=CLAIM).json()
    ev = client.post('/api/v1/evidence/', json=evidence()).json()['id']
    for i in range(n):
        signer.store_link(claim['id'], ev, f'attestor_{i}')
    assert len(signer.stored_links(claim['id'])) == n
    return claim['id'], status(client, claim['id'])


@pytest.mark.parametrize('variant', COPY_VARIANTS)
def test_scn_c04_index_api_copied_evidence_is_not_counted_as_independent_corroboration(request, record_property, tmp_path, index_pin, variant):
    """EXPECTED TO FAIL at the old pin (defect #24). Links are stored (signed where required), so the scores are real measurements."""
    def trial(work, mp, checks):
        one_id, one = build(*fresh(index_pin, work, mp), [(evidence(), 'c04_attestor', None)])
        many_id, many = _copies(*fresh(index_pin, work, mp), variant)
        checks.expect(many['independence_score'] <= one['independence_score'],
                      f'{variant}: independence_score for 5 copies of ONE source is {many["independence_score"]} > {one["independence_score"]} for a single copy')
        checks.expect(many['supporting_weight'] <= one['supporting_weight'],
                      f'{variant}: supporting_weight for 5 copies is {many["supporting_weight"]} > {one["supporting_weight"]} for a single copy (copies added corroborating weight)')
        checks.equal(many['status'], one['status'], f'{variant}: copies alone must not change the claim status')
        return {'variant': variant, 'single_copy': one, 'five_copies': many, 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    C.run_c_case(request, record_property, tmp_path, 'C04', trial, gate=False,
                 extra={'surface': 'The Index API EvidenceService.compute_epistemic_status', 'pin': S.env_pin_sha(), 'known_defect': '#24',
                        'expected_at_frozen_pin': 'FAIL (a FAIL is the correct honest result)',
                        'formula_observed': 'independence_score = min(distinct evidence ids / 5, 1); supporting_weight sums quality*strength per LINK; the service has no source-identity or copy detection'})


def test_scn_c04_index_api_independent_sources_control(request, record_property, tmp_path, index_pin):
    """Detector control: five genuinely different sources do raise the metrics (so the copy cases above are not vacuous)."""
    def trial(work, mp, checks):
        _, one = build(*fresh(index_pin, work, mp), [(evidence('doi:10.1/source-0'), 'c04_attestor', None)])
        _, five = build(*fresh(index_pin, work, mp), [(evidence(f'doi:10.1/source-{i}'), 'c04_attestor', None) for i in range(5)])
        checks.expect(five['independence_score'] > one['independence_score'], 'independent sources raise independence_score')
        checks.expect(five['supporting_weight'] > one['supporting_weight'], 'independent sources raise supporting_weight')
        return {'one_source': one, 'five_sources': five}
    C.run_c_case(request, record_property, tmp_path, 'C04', trial, gate=False, extra={'surface': 'The Index API (control)'})


# ------------------------------------------------------------------------------------------------
# Python API: history survives; status recomputes from its inputs
# ------------------------------------------------------------------------------------------------

def test_scn_c04_index_api_status_recomputes_deterministically_from_pinned_inputs(request, record_property, tmp_path, index_pin):
    def trial(work, mp, checks):
        def run(order, extend=False):
            client, signer = fresh(index_pin, work, mp)  # services are process-global: each run gets a fresh set, used before the next is built
            claim = client.post('/api/v1/claims/', json=CLAIM).json()
            cid = claim['id']
            evs = [client.post('/api/v1/evidence/', json=evidence(f'doi:10.1/s{i}', copy=i)).json()['id'] for i in range(3)]
            rel = ['supports', 'supports', 'contradicts']
            for i in order:
                signer.store_link(cid, evs[i], f'a{i}', rel[i])
            first, second = status(client, cid), status(client, cid)
            out = {'first': first, 'second': second}
            if extend:
                before = [l['id'] for l in client.get(f'/api/v1/evidence/links/claim/{cid}').json()]
                extra_ev = client.post('/api/v1/evidence/', json=evidence('doi:10.1/s9')).json()['id']
                signer.store_link(cid, extra_ev, 'a9', 'contradicts')
                out.update(after=status(client, cid), links_before=before,
                           links_after=[l['id'] for l in client.get(f'/api/v1/evidence/links/claim/{cid}').json()])
            return out
        a = run([0, 1, 2], extend=True)
        b = run([2, 1, 0])
        a1, a2, b1, after = a['first'], a['second'], b['first'], a['after']
        checks.equal(a1, a2, 'repeated reads of the same inputs give the same status')
        checks.equal(a1, b1, 'status does not depend on insertion order (recomputed from the set of inputs)')
        checks.expect(after['contradicting_weight'] > a1['contradicting_weight'], 'a later contradicting input is reflected on recomputation')
        checks.equal(a['links_after'][:len(a['links_before'])], a['links_before'], 'earlier links survive (history is append-only here)')
        before_links, after_links = a['links_before'], a['links_after']
        return {'status_initial': a1, 'status_reordered': b1, 'status_after_new_input': after, 'links_before': len(before_links), 'links_after': len(after_links)}
    C.run_c_case(request, record_property, tmp_path, 'C04', trial, gate=False, extra={'surface': 'The Index API status recomputation'})


def test_scn_c04_index_api_accepted_claim_history_survives_rewrite_and_delete(request, record_property, tmp_path, index_pin):
    def trial(work, mp, checks):
        client, signer = fresh(index_pin, work, mp)
        claim = client.post('/api/v1/claims/', json=CLAIM).json()
        cid = claim['id']
        ev = client.post('/api/v1/evidence/', json=evidence()).json()['id']
        signer.store_link(cid, ev, 'a0')
        put = client.put(f'/api/v1/claims/{cid}', json={'canonical_text': 'rewritten as a "supersession"'})
        delete = client.delete(f'/api/v1/claims/{cid}')
        kept = client.get(f'/api/v1/claims/{cid}').json()
        links = client.get(f'/api/v1/evidence/links/claim/{cid}').json()
        checks.equal((put.status_code, delete.status_code), (409, 409), 'accepted claim cannot be rewritten or deleted')
        checks.equal(kept['canonical_text'], CLAIM['canonical_text'], 'original claim text survives')
        checks.equal(len(links), 1, 'links survive')
        paths = sorted(client.get('/openapi.json').json()['paths'])
        return {'put': put.status_code, 'delete': delete.status_code, 'claim_text_unchanged': kept['canonical_text'] == CLAIM['canonical_text'],
                'links': len(links), 'openapi_paths': paths, 'api_has_supersession_route': any('supersed' in p.lower() for p in paths)}
    C.run_c_case(request, record_property, tmp_path, 'C04', trial, gate=False,
                 extra={'surface': 'The Index API claims', 'not_covered': 'supersession through the API (no such route; see module docstring)'})


# ------------------------------------------------------------------------------------------------
# Chain profile: supersession preserves history; reconstruction from logs; copies stay visible
# ------------------------------------------------------------------------------------------------
DRIVER = HERE / '_c_index_chain_driver.mjs'


def test_scn_c04_index_chain_supersession_preserves_history_and_is_author_only_and_terminal(request, record_property, tmp_path, chain_dir):
    def trial(work, mp, checks):
        obs = C.run_node_driver(DRIVER, chain_dir, work)
        s = obs['supersession']
        for key in ('third_party_supersede_refused', 'unrelated_successor_refused', 'self_successor_refused', 'empty_reason_refused',
                    'supersede_by_author_accepted', 'withdraw_after_supersede_refused', 'supersede_twice_refused',
                    'later_criticism_of_superseded_claim_recorded'):
            checks.equal(s[key], True, key)
        checks.equal(s['original'], {'content_preserved': True, 'lifecycle': 3, 'successor_is_revision': True, 'author_preserved': True}, 'original claim preserved and marked superseded')
        checks.equal(s['revision'], {'content_preserved': True, 'lifecycle': 1, 'parent_is_original': True}, 'revision linked to the original')
        return {'supersession': s}
    C.run_c_case(request, record_property, tmp_path, 'C04', trial, gate=False,
                 extra={'surface': 'Index chain contract (loopback Ganache)', 'pin': S.env_pin_sha()})


def test_scn_c04_index_chain_status_recomputes_from_logs_and_history_is_ordered(request, record_property, tmp_path, chain_dir):
    def trial(work, mp, checks):
        r = C.run_node_driver(DRIVER, chain_dir, work)['reconstruction']
        checks.equal(r['from_logs_equals_direct_reads'], True, 'state rebuilt from logs equals direct contract reads')
        checks.equal(r['two_independent_readers_agree'], True, 'two independent readers rebuild identical state')
        checks.equal(r['history_has_registered_before_lifecycle_change'], True, 'history order preserved')
        checks.equal(r['original_content_reconstructed'], True, 'superseded claim content reconstructed from logs')
        checks.equal(r['evidence_on_original_after_supersession'], 2, 'earlier and later criticism both survive supersession')
        checks.equal(r['reconstructed_lifecycles']['v1']['lifecycle'], 3, 'lifecycle reconstructed as superseded')
        return {'reconstruction': r}
    C.run_c_case(request, record_property, tmp_path, 'C04', trial, gate=False,
                 extra={'surface': 'Index chain reconstruct.mjs', 'pin': S.env_pin_sha(),
                        'finality_note': 'provisional on a single development node; not consensus finality'})


def test_scn_c04_index_chain_copied_evidence_is_visible_and_never_merged_or_scored_as_independent(request, record_property, tmp_path, chain_dir):
    def trial(work, mp, checks):
        cp = C.run_node_driver(DRIVER, chain_dir, work)['copied_evidence']
        checks.equal(cp['exact_duplicate_refused'], True, 'exact duplicate evidence is rejected')
        checks.equal(cp['copies_are_visible_not_merged'], True, 'semantic copies remain visible as separate records')
        checks.equal(cp['records_sharing_the_original_content_commitment'], 4, 'all four copies expose the same content commitment (dependence is detectable)')
        checks.equal(cp['distinct_content_commitments'], 2, 'distinct content commitments: the original and the independent measurement')
        checks.equal(cp['contract_computes_no_corroboration_or_independence_value'], True, 'the contract computes no corroboration/independence value that copies could inflate')
        return {'copied_evidence': cp, 'harness_derived_view': 'distinct content commitments counted by the harness from reconstructed records; the product defines no such view'}
    C.run_c_case(request, record_property, tmp_path, 'C04', trial, gate=False,
                 extra={'surface': 'Index chain contract', 'pin': S.env_pin_sha(),
                        'limit': 'the chain slice does not itself decide independence; a consumer must derive it from the exposed commitments'})
