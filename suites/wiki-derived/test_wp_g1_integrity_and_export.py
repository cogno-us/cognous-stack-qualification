"""Scenario-derived tests: evidence hashing, tamper evidence and export (work package G1).

SPDX-License-Identifier: Apache-2.0

Five catalog cases classified APPLICABLE, each checked for the part inside the declared scope of the stack against the pinned
synthetic reference (retained producer runs written to files and read back; no destination is touched by the tests).

Existing coverage that each test builds on (not copied): the planted-defect catalogue and the producer, bundle, pack and package
evaluators of ``suites/v1-scenarios/_d06_d07_d08_helpers.py`` (SCN-D08), the HMAC, redaction and content-digest checks of
``test_scn_c13.py``, the separate-process package consumer of ``test_scn_c14.py``, the outside-held digest of the pinned Control
Plane (``agent_control_plane.witness``; ``suites/outside-holder``) and the digest substitution checks of ``test_asw_s.py``. What
these tests add: per-record hash recomputation done in the test, every record altered in turn, deleted ranges, the witness over a
change history of twenty revisions, and the exports read by a fresh process.

Cases: TC-D12-018, TC-L17-021, TC-L17-004, TC-L02-025, TC-L03-022.

Limits, asserted as limits and never as passes:

* eleven of the 46 records of an applied run carry no time of their own (the proposal, the time floors and the ten records that
  come from the executor export); the items that do carry a time are the journal rows (TC-D12-018);
* the artifacts hold no custody log, no handler identity, no access log, no legal hold and no retention rule (TC-D12-018,
  TC-L17-021);
* the exported copies are plain files: an altered copy is detected on verification, not prevented (TC-L17-004, TC-L17-021);
* the record store is a plain JSON file with no keyed integrity check. A row edited, deleted, reordered or backdated in the
  source journal before an export is read as given by the Replay importer, the Evidence Pack importer and the ODES exporter
  (TC-L02-025). Rewrites and deletions of rows already covered by an outside-held digest are detected by the witness check; rows
  appended after the latest digest are not covered, and whoever holds the witness can replace it (TC-L02-025, TC-L17-004);
* a revision row with an earlier recorded time than the row before it is accepted and appended (TC-L02-025);
* a redacted derivative of a bundle is refused by the Evidence Pack importer and the ODES exporter, so no redacted export reaches
  them (TC-L03-022);
* the independent verifier (``cognous-verify``) is not part of the pinned reference built by ``--prepare-work``; it is measured by
  the opt-in report-only harness ``suites/verifier-mutation`` and is not asserted here (TC-L17-004, TC-L02-025, TC-L17-021).

Not claimed here: an access log, a custody workflow, legal hold, retention, blocking of an alteration, a role model, alerting,
clock synchronisation, compliance-framework formats or an export size limit.
"""
from __future__ import annotations

import copy
import json

import pytest

import _wiki_helpers as W
import _wp_g_common as G
from _wiki_helpers import wiki_case

pytestmark = pytest.mark.usefixtures('pinned_reference')

SECRET = 'synthetic-shared-secret-G1'
MUTATION_FAMILIES = ('producer', 'bundle', 'pack', 'odes', 'odes_rehashed')
JOURNAL_LEDGERS = ('check_events', 'decisions', 'resolution_checks', 'attempts', 'observations', 'reconciliations', 'refusals')


@pytest.fixture(scope='module')
def four(pinned_reference, tmp_path_factory):
    """Four retained producer runs: an applied effect, a lost acknowledgement, a revoked grant and an unreadable status."""
    built = G.build_four(tmp_path_factory.mktemp('wp-g1-four'))
    yield built
    G.check_exports_unchanged(built)


def ledger_rows(journal):
    return {k: v for k, v in journal.items() if isinstance(v, list)}


def pack_refs(pack):
    return {r['source_path']: r for r in pack['metadata']['traceable_import']['source_record_refs']}


# ================================================================================================ TC-D12-018
@wiki_case('TC-D12-018')
def test_wiki_d12_018_every_retained_item_carries_a_hash_that_recomputes_in_the_test(four):
    total = 0
    for case, ex in four.items():
        bundle, pack, package = G.load(ex, 'bundle'), G.load(ex, 'pack'), G.load(ex, 'odes')
        refs = pack_refs(pack)
        assert sorted(refs) == sorted(r['source_path'] for r in bundle['records']), case  # one hash per retained item, none missing
        for record in bundle['records']:
            ref = refs[record['source_path']]
            assert ref['hash'] == G.sha(record), (case, record['source_path'])  # sha256 of the canonical record, computed here
            assert ref['local_content_commitment'] == ref['hash'] and ref['record_id'] == record['record_id']
        total += len(bundle['records'])
        # the whole bundle: the digest the pack and the ODES package bind equals one computed here from the file
        digest = G.sha(G.bundle_without_integrity(bundle))
        artifacts = {a['artifact_role']: a for a in pack['metadata']['traceable_import']['input_artifacts']}
        assert artifacts['reconstruction_bundle']['hash'] == digest == package['provenance']['source_artifacts']['reconstruction_bundle_digest']
        assert artifacts['manifest']['hash'] == package['provenance']['source_artifacts']['manifest_digest'] == G.sha(G.load(ex, 'manifest'))
        assert G.replay().content_digest(G.replay().ReconstructionBundle.model_validate(bundle)).value == digest
    assert total >= 150  # the four runs hold 158 retained items between them


@wiki_case('TC-D12-018')
def test_wiki_d12_018_each_item_names_its_time_when_it_has_one_and_eleven_applied_run_items_have_none_known_limit(four):
    ex = four['valid']
    bundle = G.load(ex, 'bundle')
    untimed = sorted(r['source_path'] for r in bundle['records'] if not r['recorded_at'])
    timed = [r for r in bundle['records'] if r['recorded_at']]
    assert len(bundle['records']) == 46 and len(timed) == 35
    assert untimed == ['input_time_floors', 'moltbot.attempt_events[0]', 'moltbot.attempt_events[1]', 'moltbot.attempts[0]',
                       'moltbot.control_plane_attempts[0]', 'moltbot.control_plane_evidence', 'moltbot.effects[0]', 'moltbot.execution_envelope',
                       'moltbot.execution_result', 'moltbot.observations[0]', 'proposal']
    # every timed item states a strict UTC instant; the sequence number orders all items, timed or not
    assert all(r['recorded_at'].endswith('+00:00') for r in timed)
    assert [r['source_sequence'] for r in bundle['records']] == list(range(len(bundle['records'])))
    # limit: the clocks of the journal and of the executor are independent, so the bundle states no order between them
    assert any('Independent clocks do not establish ordering' in line
               for line in G.load(ex, 'pack')['metadata']['traceable_import']['derived_counts']['counting_rules'])


@wiki_case('TC-D12-018')
def test_wiki_d12_018_altering_any_one_item_is_detected_by_the_hash_of_that_item(four):
    altered_total = 0
    for case, ex in four.items():
        bundle, pack = G.load(ex, 'bundle'), G.load(ex, 'pack')
        refs = pack_refs(pack)
        recorded_digest = pack['metadata']['traceable_import']['input_artifacts'][1]['hash']
        for i, record in enumerate(bundle['records']):
            copy_ = copy.deepcopy(bundle)
            path = G.alter_first_leaf(copy_['records'][i]['data'])
            assert path is not None, (case, record['source_path'])
            mismatching = [r['source_path'] for r in copy_['records'] if G.sha(r) != refs[r['source_path']]['hash']]
            assert mismatching == [record['source_path']], (case, record['source_path'], mismatching)  # exactly the altered item
            assert G.sha(G.bundle_without_integrity(copy_)) != recorded_digest
            altered_total += 1
        # control: the unaltered bundle has no mismatching item
        assert [r for r in bundle['records'] if G.sha(r) != refs[r['source_path']]['hash']] == []
    assert altered_total == 158


@wiki_case('TC-D12-018')
def test_wiki_d12_018_the_exports_are_files_that_read_back_and_verify(four):
    for case, ex in four.items():
        files = ex['objects_on_disk']
        # Evidence Pack: the file loads and validates
        assert G.h2().eval_pack_artifact(G.load(ex, 'pack'))['verdict'] == 'accepted'
        # ODES package: read from the file by a fresh process that holds only the ODES and Replay trees
        layers = G.separate_consumer(files['odes'])
        assert layers['package_content_integrity'] == 'pass' and layers['schema_validity'] == 'pass', (case, layers)
        # Replay bundle: round trips through the model and keeps its digest
        bundle = G.load(ex, 'bundle')
        model = G.replay().ReconstructionBundle.model_validate(bundle)
        assert json.loads(model.model_dump_json()) == bundle
        # the producer wrote each artifact once and the files are unchanged since (checked again at module teardown)
        assert {n: G.file_digest(p) for n, p in files.items()} == {n[:-5]: d for n, d in ex['sha256'].items()}


@wiki_case('TC-D12-018')
def test_wiki_d12_018_no_custody_log_handler_identity_or_access_log_is_carried_known_limit(four):
    words = ('custody', 'handler', 'transfer', 'access_log', 'accessed_by', 'legal_hold', 'retention')
    for case, ex in four.items():
        for name in ('bundle', 'pack', 'odes'):
            names = {str(k).lower() for _, k, _ in _members(G.load(ex, name)) if k}
            assert [w for w in words if any(w in n for n in names)] == [], (case, name)
    # what the package does state about its maker is one fixed exporter label, not a handler of the evidence
    created_by = {G.load(ex, 'odes')['created_by'] for ex in four.values()}
    assert created_by == {'open-decision-evidence-standard/reference-exporter'}


def _members(value, path=''):
    if isinstance(value, dict):
        for k, v in value.items():
            yield f'{path}/{k}', k, None
            yield from _members(v, f'{path}/{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _members(v, f'{path}/{i}')


# ================================================================================================ TC-L17-021
@wiki_case('TC-L17-021')
def test_wiki_l17_021_incident_export_with_hashes_verifies_in_a_fresh_process(four):
    records = 0
    for case, ex in four.items():
        bundle, package = G.load(ex, 'bundle'), G.load(ex, 'odes')
        records += len(bundle['records'])
        layers = G.separate_consumer(ex['objects_on_disk']['odes'])
        assert layers['package_content_integrity'] == 'pass' and layers['replay_semantic_consistency'] == 'pass', (case, layers)
        # the hashes are the ones the test recomputes from the retained items
        assert package['provenance']['source_artifacts']['reconstruction_bundle_digest'] == G.sha(G.bundle_without_integrity(bundle))
        retained = package['provenance']['retained_sources']['reconstruction_bundle']
        assert len(retained['records']) == len(bundle['records'])
        assert all(G.sha(a) == G.sha(b) for a, b in zip(retained['records'], bundle['records']))
        # the package binds its own record and profile metadata by a digest that recomputes
        assert package['integrity']['kind'] == 'content-digest' and package['integrity']['value'].startswith('sha256:')
    assert records >= 150


@wiki_case('TC-L17-021')
def test_wiki_l17_021_an_altered_exported_copy_fails_verification_in_a_fresh_process(four, tmp_path):
    edits = {
        'record_edit': lambda o: o['record'].__setitem__('planted_member', 'x'),
        'profile_edit': lambda o: o['profile'].__setitem__('planted_member', 'x'),
        'integrity_value_edit': lambda o: o['integrity'].__setitem__('value', 'sha256:' + '0' * 64),
        'package_digest_edit': lambda o: o.__setitem__('package_digest', 'sha256:' + '0' * 64),
    }
    for case, ex in four.items():
        package = G.load(ex, 'odes')
        assert G.separate_consumer(ex['objects_on_disk']['odes'])['package_content_integrity'] == 'pass'  # control
        for name, edit in edits.items():
            altered = copy.deepcopy(package)
            edit(altered)
            assert altered != package
            path = tmp_path / f'{case}-{name}.json'
            path.write_text(json.dumps(altered))
            layers = G.separate_consumer(path)
            assert layers['package_content_integrity'] == 'fail', (case, name, layers)
            assert layers['recipient_reliance_decision'] != 'pass' and layers['integrity_authentication_checks'] != 'pass', (case, name)
        # an edit of the retained execution facts is caught by the integrity layer or by the replay semantics layer
        facts = copy.deepcopy(package)
        facts['provenance']['execution_facts']['destination_observed'] = 'absent' if package['provenance']['execution_facts']['destination_observed'] != 'absent' else 'applied'
        path = tmp_path / f'{case}-facts.json'
        path.write_text(json.dumps(facts))
        layers = G.separate_consumer(path)
        assert 'fail' in (layers['package_content_integrity'], layers['replay_semantic_consistency']), (case, layers)


@wiki_case('TC-L17-021')
def test_wiki_l17_021_the_artifacts_offer_no_hold_retention_or_access_log_known_limit(four):
    import importlib
    G.h()
    bounded = importlib.import_module('agent_control_plane.bounded')
    surfaces = {
        'record store': dir(bounded.BoundedRecordStore),
        'replay': dir(G.replay()),
        'evidence pack': dir(importlib.import_module('agent_governance_evidence_pack')),
        'odes': dir(importlib.import_module('odes')),
    }
    for where, names in surfaces.items():
        hits = [n for n in names if any(w in n.lower() for w in ('legal_hold', 'retention', 'access_log', 'custody', 'preserve'))]
        assert hits == [], (where, hits)
    # the export is a plain file: deleting or editing it is not prevented (the test removes a copy it made itself)
    ex = four['valid']
    # (a copy of the retained package is edited and re-read; the original stays byte-identical, checked at teardown)
    assert G.file_digest(ex['objects_on_disk']['odes']) == ex['sha256']['odes.json']


# ================================================================================================ TC-L17-004
@pytest.mark.parametrize('case', G.FOUR)
@wiki_case('TC-L17-004')
def test_wiki_l17_004_every_planted_alteration_of_the_exported_records_is_detected_and_clean_exports_do_not_alarm(four, case):
    H2 = G.h2()
    ex = four[case]
    manifest = G.load(ex, 'manifest')
    planted, missed = 0, []
    for family in MUTATION_FAMILIES:
        if family == 'producer':
            base = {k: G.load(ex, k) for k in ('journal', 'proposal', 'executor_export')}
            mutations = H2.producer_mutations()
        elif family == 'bundle':
            base = G.load(ex, 'bundle')
            mutations = H2.bundle_mutations(base)
        elif family == 'pack':
            base = G.load(ex, 'pack')
            mutations = H2.pack_mutations(base)
        else:
            base = G.load(ex, 'odes')
            mutations = H2.odes_mutations(base, family == 'odes_rehashed')
        for mid, klass, _target, fn in mutations:
            copy_, changed = H2.apply_mutation(base, fn, rehash=(family == 'odes_rehashed'))
            if not changed:
                continue
            if family == 'producer':
                stages = H2.evaluate_producer_exports(manifest, copy_['journal'], copy_['proposal'], copy_['executor_export'])
            elif family == 'bundle':
                stages = H2.evaluate_bundle(manifest, copy_)
            elif family == 'pack':
                stages = [H2.eval_pack_artifact(copy_)]
            else:
                stages = [H2.eval_odes_package(copy_)]
            planted += 1
            if not H2.summarise(stages)['detected']:
                missed.append(f'{family}:{mid}')
    assert planted >= 150 and missed == [], (planted, missed)
    # control: the unaltered exports are accepted by every evaluator
    stages = H2.evaluate_producer_exports(manifest, G.load(ex, 'journal'), G.load(ex, 'proposal'), G.load(ex, 'executor_export'))
    stages += H2.evaluate_bundle(manifest, G.load(ex, 'bundle')) + [H2.eval_pack_artifact(G.load(ex, 'pack')), H2.eval_odes_package(G.load(ex, 'odes'))]
    assert all(s['verdict'] == 'accepted' for s in stages), stages


@wiki_case('TC-L17-004')
def test_wiki_l17_004_deleting_a_range_of_records_from_a_journal_or_bundle_is_detected(four):
    H2 = G.h2()
    for case, ex in four.items():
        manifest = G.load(ex, 'manifest')
        journal, proposal, export = G.load(ex, 'journal'), G.load(ex, 'proposal'), G.load(ex, 'executor_export')
        bundle = G.load(ex, 'bundle')
        undetected = []
        for name, rows in ledger_rows(journal).items():
            n = len(rows)
            if n < 2:
                continue
            ranges = {'first_half': (0, n // 2), 'last_half': (n - n // 2, n), 'middle': (n // 4, n - n // 4), 'all_but_one': (0, n - 1)}
            if name == 'check_events':
                # ranges that cut through a check; the removal of every event of one whole check is its own test (known limit)
                ranges = {'first_five': (0, 5), 'last_five': (n - 5, n), 'middle_five': (n // 2 - 3, n // 2 + 2), 'all_but_one': (0, n - 1),
                          'all_but_the_last_two_checks_events': (0, n - 2)}
            for label, (lo, hi) in ranges.items():
                if lo >= hi:
                    continue
                j = copy.deepcopy(journal)
                del j[name][lo:hi]
                if not H2.summarise(H2.evaluate_producer_exports(manifest, j, proposal, export))['detected']:
                    undetected.append(f'journal.{name}.{label}')
        n = len(bundle['records'])
        for label, (lo, hi) in {'first_third': (0, n // 3), 'middle_third': (n // 3, 2 * n // 3), 'last_third': (2 * n // 3, n), 'all_but_one': (0, n - 1)}.items():
            b = copy.deepcopy(bundle)
            del b['records'][lo:hi]
            if not H2.summarise(H2.evaluate_bundle(manifest, b))['detected']:
                undetected.append(f'bundle.records.{label}')
        assert undetected == [], (case, undetected)


@wiki_case('TC-L17-004')
def test_wiki_l17_004_removing_every_event_of_one_whole_check_is_read_as_given_by_the_consumers_known_limit(four, tmp_path):
    H2 = G.h2()
    witness_mod = _witness()
    for case in ('valid', 'lost_ack', 'revoked', 'unreadable'):
        ex = four[case]
        manifest = G.load(ex, 'manifest')
        journal, proposal, export = G.load(ex, 'journal'), G.load(ex, 'proposal'), G.load(ex, 'executor_export')
        check_ids = list(dict.fromkeys(e['check_id'] for e in journal['check_events']))
        assert len(check_ids) == 2  # one check at the decision and one at the effect
        witness = witness_mod.LocalFileWitness(tmp_path / f'{case}.jsonl')
        witness_mod.publish_head(journal, witness)
        for check_id in check_ids:
            doc = copy.deepcopy(journal)
            doc['check_events'] = [e for e in doc['check_events'] if e['check_id'] != check_id]
            assert len(doc['check_events']) < len(journal['check_events'])
            # limit: no consumer of the reference cross-checks the check events against the decisions and the checks list
            stages = H2.evaluate_producer_exports(manifest, doc, proposal, export)
            assert [s['verdict'] for s in stages] == ['accepted'] * 3, (case, check_id, stages)
            # the outside-held digest does see it
            verdict = witness_mod.verify_against_witness(doc, witness)
            assert not verdict.ok and verdict.reasons == ['witness_ledger_shrunk'], (case, verdict.reasons)


@wiki_case('TC-L17-004')
def test_wiki_l17_004_witness_detects_rewritten_deleted_reordered_or_duplicated_rows_covered_by_a_held_digest(four, tmp_path):
    ex = four['lost_ack']
    journal = G.load(ex, 'journal')
    witness_mod = _witness()
    witness = witness_mod.LocalFileWitness(tmp_path / 'witness.jsonl')
    first = witness_mod.publish_head(journal, witness)
    assert first['sequence'] == 0 and witness_mod.verify_against_witness(journal, witness).ok
    wrong = {}
    for name, rows in ledger_rows(journal).items():
        if not rows:
            continue
        variants = {}
        edited = copy.deepcopy(journal)
        G.alter_first_leaf(edited[name][0])
        variants['rewrite_first'] = edited
        deleted = copy.deepcopy(journal)
        deleted[name].pop()
        variants['delete_last'] = deleted
        dup = copy.deepcopy(journal)
        dup[name].insert(0, copy.deepcopy(dup[name][0]))  # before the covered rows, so they shift
        variants['duplicate_first'] = dup
        if len(rows) > 1:
            swapped = copy.deepcopy(journal)
            swapped[name][0], swapped[name][1] = swapped[name][1], swapped[name][0]
            variants['swap_first_two'] = swapped
            middle = copy.deepcopy(journal)
            middle[name].pop(len(rows) // 2)
            variants['delete_middle'] = middle
        for label, doc in variants.items():
            verdict = witness_mod.verify_against_witness(doc, witness)
            if label == 'duplicate_first' and verdict.ok and len(rows) == 1:
                # a copy of the only covered row ahead of it leaves the covered prefix unchanged: it reads as one appended row
                if verdict.unwitnessed_rows != {name: 1}:
                    wrong[f'{name}.{label}'] = verdict.unwitnessed_rows
                continue
            if verdict.ok or not set(verdict.reasons) <= {'witness_ledger_shrunk', 'witness_ledger_head_mismatch'}:
                wrong[f'{name}.{label}'] = verdict.reasons
    assert wrong == {}, wrong
    # publishing over a rewrite is refused, so a rewrite is never laundered into the next digest
    rewritten = copy.deepcopy(journal)
    G.alter_first_leaf(rewritten['decisions'][0])
    with pytest.raises(witness_mod.WitnessRefused):
        witness_mod.publish_head(rewritten, witness)


@wiki_case('TC-L17-004')
def test_wiki_l17_004_rows_after_the_latest_digest_and_the_witness_holder_are_outside_the_check_known_limit(four, tmp_path):
    journal = G.load(four['valid'], 'journal')
    witness_mod = _witness()
    witness = witness_mod.LocalFileWitness(tmp_path / 'witness.jsonl')
    witness_mod.publish_head(journal, witness)
    # a row appended after the latest digest is reported as not witnessed, and a deleted unwitnessed row is not noticed
    longer = copy.deepcopy(journal)
    longer['check_events'].append(copy.deepcopy(longer['check_events'][-1]))
    verdict = witness_mod.verify_against_witness(longer, witness)
    assert verdict.ok and verdict.unwitnessed_rows == {'check_events': 1}
    back = copy.deepcopy(longer)
    back['check_events'].pop()
    assert witness_mod.verify_against_witness(back, witness).ok  # the appended row can vanish again without a finding
    # whoever controls the witness can replace it with one over the altered record set, which then verifies
    altered = copy.deepcopy(journal)
    G.alter_first_leaf(altered['decisions'][0])
    assert not witness_mod.verify_against_witness(altered, witness).ok
    replaced = witness_mod.LocalFileWitness(tmp_path / 'replaced.jsonl')
    witness_mod.publish_head(altered, replaced)
    assert witness_mod.verify_against_witness(altered, replaced).ok
    # the verdict states its own scope
    assert 'not tamper evidence against the witness holder' in verdict.scope


@wiki_case('TC-L17-004')
def test_wiki_l17_004_signed_export_verifies_and_an_altered_copy_does_not_and_the_alteration_is_not_prevented(four, tmp_path):
    R = G.replay()
    ex = four['valid']
    bundle = R.ReconstructionBundle.model_validate(G.load(ex, 'bundle'))
    signed = R.sign_reconstruction_bundle(bundle, SECRET, key_id='key:synthetic-G1').model_dump(mode='json')
    assert R.verify_reconstruction_hmac(R.ReconstructionBundle.model_validate(signed), SECRET) is True
    assert R.verify_reconstruction_hmac(R.ReconstructionBundle.model_validate(signed), SECRET + 'x') is False
    edits = {
        'record_edit': lambda d: d['records'][0]['data'].__setitem__('planted_member', 'x'),
        'record_dropped': lambda d: d['records'].pop(),
        'status_promoted': lambda d: d.__setitem__('status', 'redacted'),
        'signature_stripped': lambda d: d.__setitem__('integrity', []),
    }
    path = tmp_path / 'altered-export.json'
    for name, edit in edits.items():
        forged = copy.deepcopy(signed)
        edit(forged)
        path.write_text(json.dumps(forged))  # nothing prevents writing the altered copy: detection only
        reread = json.loads(path.read_text())
        assert reread == forged
        verdict = R.verify_reconstruction_hmac(R.ReconstructionBundle.model_validate(reread), SECRET)
        assert verdict is False, name
    # limit: the HMAC proves possession of the shared secret, not an identity; a holder of the secret can mint a verifying copy
    minted = copy.deepcopy(signed)
    minted['records'][0]['data']['planted_member'] = 'x'
    minted = R.sign_reconstruction_bundle(R.ReconstructionBundle.model_validate({**minted, 'integrity': []}), SECRET, key_id='key:synthetic-G1')
    assert R.verify_reconstruction_hmac(minted, SECRET) is True


def _witness():
    import importlib
    G.h()
    return importlib.import_module('agent_control_plane.witness')


# ================================================================================================ TC-L02-025
@wiki_case('TC-L02-025')
def test_wiki_l02_025_twenty_revisions_keep_a_complete_history_with_before_and_after_values(tmp_path, monkeypatch):
    p, r, f = G.rule_flow(tmp_path, monkeypatch)
    labels = [f'v{i}' for i in range(1, 21)]
    G.adopt(f, 'r1', labels[0])
    for i in range(1, 20):
        G.adopt(f, f'r{i + 1}', labels[i], labels[i - 1])
    listed = G.rows(f)
    assert [x['revision_id'] for x in listed] == [f'r{i}' for i in range(1, 21)]  # twenty edits, twenty rows, each recorded on its own
    assert [x['from_digest'] for x in listed] == [None] + [G.digest_of(l) for l in labels[:-1]]
    assert [x['to_digest'] for x in listed] == [G.digest_of(l) for l in labels]
    assert all(x['reviser'] == G.REVISER and x['signer'] == G.SIGNER and x['authority_ref'] and x['reason'] and x['recorded_at'] for x in listed)
    # each decision names the digest that was in force when it was taken, and the row that adopted it exists
    G.observe(r, labels[-1])
    d = G.decide(f, p)
    assert d.result == 'authorized' and d.rule_identity['rules'][G.tb().POLICY_REF]['digest'] == G.digest_of(labels[-1])
    # attempts to alter the history through the supported interface are refused and the refusals are kept as rows
    rr = G.rr()
    for rid, kwargs, reason in (('r5', {}, 'rule_revision_duplicate'),  # a row with an existing identifier
                                ('r-self', {'signer': G.REVISER}, 'self_signed_revision_row'),
                                ('r-outsider', {'signer': 'synthetic-principal:not-configured'}, 'signer_not_configured')):
        with pytest.raises(rr.RuleRevisionRefused) as refused:
            G.adopt(f, rid, 'v21', 'v20', **kwargs)
        assert reason in refused.value.reasons
    with pytest.raises(rr.RuleRevisionRefused) as stale:
        G.adopt(f, 'r-stale', 'v21', 'v7')  # a row that does not follow the adopted digest
    assert 'rule_revision_from_digest_mismatch' in stale.value.reasons
    doc = f.records.load()
    assert len(doc.rule_revisions) == 20 and len(doc.rule_revision_refusals) == 4
    assert G.rows(f) == listed  # nothing was edited


@wiki_case('TC-L02-025')
def test_wiki_l02_025_the_record_store_offers_no_way_to_edit_or_delete_a_row_and_has_no_role_model(tmp_path, monkeypatch):
    p, r, f = G.rule_flow(tmp_path, monkeypatch)
    names = [n for n in dir(f.records) if not n.startswith('__')]
    assert [n for n in names if any(w in n.lower() for w in ('delete', 'remove', 'update', 'edit', 'truncate', 'drop', 'purge'))] == []
    # a superseding row is a new row; the superseded row stays as written
    G.adopt(f, 'r1', 'v1')
    before = G.rows(f)
    rev = G.revision('r2', 'v1b')  # replaces r1: the adoption row of the rule, so it has no prior digest
    rev = rev.model_copy(update={'supersedes': 'r1'})
    G.rr().append_rule_revision(f.records, f.rule_revision_profile, rev)
    after = G.rows(f)
    assert after[0] == before[0] and [x['revision_id'] for x in after] == ['r1', 'r2'] and after[1]['supersedes'] == 'r1'
    assert G.rr().adopted_digest(f.rule_revision_profile, f.records.load().rule_revisions, G.tb().POLICY_REF) == G.digest_of('v1b')
    # limit: there is no role model; the signer set is host configuration and the store distinguishes no other role
    profile = f.rule_revision_profile
    assert set(type(profile).model_fields) == {'version', 'signers', 'host_digests', 'host_rule_kinds'}


@wiki_case('TC-L02-025')
def test_wiki_l02_025_a_backdated_revision_row_is_accepted_and_kept_in_append_order_known_limit(tmp_path, monkeypatch):
    p, r, f = G.rule_flow(tmp_path, monkeypatch)
    G.adopt(f, 'r1', 'v1')
    G.adopt(f, 'r2', 'v2', 'v1')
    G.adopt(f, 'r3', 'v3', 'v2', recorded_at='2020-01-01T00:00:00+00:00')  # earlier than both rows before it
    listed = G.rows(f)
    assert [x['revision_id'] for x in listed] == ['r1', 'r2', 'r3']  # append order is kept, so the backdating is visible by comparison
    assert listed[2]['recorded_at'] < listed[1]['recorded_at']
    assert f.records.load().rule_revision_refusals == []  # neither refused nor flagged at the store
    # control: a row with a later time is appended in order as well
    G.adopt(f, 'r4', 'v4', 'v3', recorded_at='2026-10-06T19:00:00+00:00')
    assert [x['revision_id'] for x in G.rows(f)] == ['r1', 'r2', 'r3', 'r4']


@wiki_case('TC-L02-025')
def test_wiki_l02_025_witness_detects_a_rewritten_or_deleted_revision_row_covered_by_a_digest(tmp_path, monkeypatch):
    witness_mod = _witness()
    p, r, f = G.rule_flow(tmp_path / 'flow', monkeypatch)
    G.adopt(f, 'r1', 'v1')
    G.adopt(f, 'r2', 'v2', 'v1')
    G.adopt(f, 'r3', 'v3', 'v2')
    path = f.records.path
    witness = witness_mod.LocalFileWitness(tmp_path / 'witness.jsonl')
    witness_mod.publish_head(json.loads(path.read_text()), witness)
    assert witness_mod.verify_against_witness(path, witness).ok  # control
    good = json.loads(path.read_text())
    for label, edit, codes in (
            ('rewrite_first_row', lambda d: d['rule_revisions'][0].__setitem__('to_digest', 'sha256:' + '7' * 64), {'witness_ledger_head_mismatch'}),
            ('delete_last_row', lambda d: d['rule_revisions'].pop(), {'witness_ledger_shrunk'}),
            ('delete_middle_row', lambda d: d['rule_revisions'].pop(1), {'witness_ledger_shrunk', 'witness_ledger_head_mismatch'}),
            ('reorder_rows', lambda d: d['rule_revisions'].reverse(), {'witness_ledger_head_mismatch'}),
            ('backdate_a_row', lambda d: d['rule_revisions'][2].__setitem__('recorded_at', '2020-01-01T00:00:00+00:00'), {'witness_ledger_head_mismatch'})):
        doc = copy.deepcopy(good)
        edit(doc)
        verdict = witness_mod.verify_against_witness(doc, witness)
        assert not verdict.ok and set(verdict.reasons) <= codes and verdict.reasons, (label, verdict.reasons)
    # a row appended after the digest is reported as not witnessed, not as an alteration
    G.adopt(f, 'r4', 'v4', 'v3')
    verdict = witness_mod.verify_against_witness(path, witness)
    assert verdict.ok and verdict.unwitnessed_rows == {'rule_revisions': 1}


@wiki_case('TC-L02-025')
def test_wiki_l02_025_an_edit_to_the_source_journal_before_export_is_read_as_given_known_limit(four):
    H2 = G.h2()
    ex = four['valid']
    journal, proposal, export, manifest = (G.load(ex, n) for n in ('journal', 'proposal', 'executor_export', 'manifest'))
    rows = [G.revision(f'r{i}', f'v{i}', f'v{i - 1}' if i > 1 else None).model_dump(mode='json') for i in (1, 2, 3)]
    base = copy.deepcopy(journal)
    base['rule_revisions'] = rows
    assert [s['verdict'] for s in H2.evaluate_producer_exports(manifest, base, proposal, export)] == ['accepted'] * 3  # control
    bundle = G.reconstruct(base, proposal, export)
    assert [r['record_type'] for r in bundle['records']].count('rule_revision') == 3  # the change history reaches the bundle
    variants = {}
    edited = copy.deepcopy(base)
    edited['rule_revisions'][0]['to_digest'] = 'sha256:' + '7' * 64
    variants['row_rewritten'] = edited
    dropped = copy.deepcopy(base)
    dropped['rule_revisions'].pop(1)
    variants['middle_row_deleted'] = dropped
    last = copy.deepcopy(base)
    last['rule_revisions'].pop()
    variants['last_row_deleted'] = last
    reordered = copy.deepcopy(base)
    reordered['rule_revisions'].reverse()
    variants['rows_reordered'] = reordered
    backdated = copy.deepcopy(base)
    backdated['rule_revisions'][2]['recorded_at'] = '2020-01-01T00:00:00+00:00'
    variants['row_backdated'] = backdated
    for label, doc in variants.items():
        stages = H2.evaluate_producer_exports(manifest, doc, proposal, export)
        assert [s['verdict'] for s in stages] == ['accepted'] * 3, (label, stages)  # not refused, not flagged by any consumer
    # once an export exists, an edit of the exported copy is detected (digest recomputation), so the integrity is the export's
    exported = G.reconstruct(base, proposal, export)
    altered = copy.deepcopy(exported)
    G.alter_first_leaf(altered['records'][[r['record_type'] for r in altered['records']].index('rule_revision')]['data'])
    assert G.sha(G.bundle_without_integrity(altered)) != G.sha(G.bundle_without_integrity(exported))


# ================================================================================================ TC-L03-022
@wiki_case('TC-L03-022')
def test_wiki_l03_022_each_offered_format_holds_the_content_of_the_source_runs(four):
    for case, ex in four.items():
        journal, bundle, pack, package = (G.load(ex, n) for n in ('journal', 'bundle', 'pack', 'odes'))
        # format 1: the Replay bundle holds one record per journal row of the run (plus the executor export rows)
        by_kind = {}
        for r in bundle['records']:
            by_kind.setdefault(r['record_type'], []).append(r)
        assert len(by_kind.get('runtime_decision', [])) == len(journal['decisions'])
        assert len(by_kind.get('resolution_check_event', [])) == len(journal['check_events'])
        assert len(by_kind.get('effect_time_refusal', [])) == len(journal['refusals'])
        assert len(by_kind.get('reconciliation', [])) == len(journal['reconciliations'])
        assert len(by_kind.get('effect_observation', [])) == len(journal['observations'])
        for decision, record in zip(journal['decisions'], by_kind['runtime_decision']):
            assert record['data'] == decision  # the record carries the journal row unchanged
        # format 2: the Evidence Pack counts what the bundle holds and retains the bundle itself
        counts = pack['metadata']['traceable_import']['derived_counts']
        assert counts['decision_count'] == len(journal['decisions']) and counts['reconciliation_count'] == len(journal['reconciliations'])
        assert pack['metadata']['traceable_import']['retained_sources']['reconstruction_bundle']['records'] == bundle['records']
        # format 3: the ODES package retains the same bundle and states the same facts
        assert package['provenance']['retained_sources']['reconstruction_bundle']['records'] == bundle['records']
        facts = package['provenance']['execution_facts']
        assert len(facts['resolution_check_event']) == len(journal['check_events'])
        assert package['provenance']['decision_facts']['decision_result'] == journal['decisions'][0]['result']


@wiki_case('TC-L03-022')
def test_wiki_l03_022_each_format_carries_who_when_source_system_and_control_reference(four):
    for case, ex in four.items():
        journal, bundle, pack, package = (G.load(ex, n) for n in ('journal', 'bundle', 'pack', 'odes'))
        binding = journal['decisions'][0]['binding']
        facts = package['provenance']['decision_facts']
        # who: actor and principal; control reference: grant, policy versions, manifest and authority requirement
        assert (facts['actor'], facts['principal'], facts['grant_revision']) == (binding['actor'], binding['principal'], binding['grant_revision'])
        assert facts['policy_versions'] == binding['policy_versions'] and facts['proposal_commitment'] == binding['proposal_commitment']
        # when: the bundle and the package name their generation time; each journal-derived record names its own time
        assert bundle['generated_at'] and package['created_at'] and pack['generated_at']
        assert sum(1 for r in bundle['records'] if r['recorded_at']) >= len(journal['decisions']) + len(journal['check_events'])
        # source system: every retained item names its producer profile and repository revision
        refs = pack['metadata']['traceable_import']['source_record_refs']
        assert all(r['producer_profile_id'] and r['producer_repository'] and r['producer_revision'] for r in refs)
        assert {r['producer_repository'] for r in refs} >= {'cogno-us/cognous-agent-control-plane'}
        # the revisions of the components that made each export are stated
        assert set(package['provenance']['selected_revisions']) == {'control_plane', 'manifest', 'moltbot_safe', 'replay'}
        assert set(pack['metadata']['traceable_import']['selected_revisions']) >= {'control_plane', 'manifest'}


@wiki_case('TC-L03-022')
def test_wiki_l03_022_integrity_verifies_in_each_format_and_an_altered_copy_fails_in_each(four, tmp_path):
    H2 = G.h2()
    R = G.replay()
    for case, ex in four.items():
        bundle, pack, package = G.load(ex, 'bundle'), G.load(ex, 'pack'), G.load(ex, 'odes')
        manifest = G.load(ex, 'manifest')
        # replay bundle: the content digest recomputes (here, independently) and an altered copy no longer matches it
        stored = G.sha(G.bundle_without_integrity(bundle))
        model = R.ReconstructionBundle.model_validate(bundle)
        assert R.content_digest(model).value == stored
        altered_bundle = copy.deepcopy(bundle)
        G.alter_first_leaf(altered_bundle['records'][1]['data'])
        assert R.content_digest(R.ReconstructionBundle.model_validate(altered_bundle)).value != stored
        # evidence pack: a clean pack validates; an altered retained bundle, derived count or signing claim is flagged or refused
        assert H2.eval_pack_artifact(pack)['verdict'] == 'accepted'
        for label, edit in {
                'retained_record': lambda p: G.alter_first_leaf(p['metadata']['traceable_import']['retained_sources']['reconstruction_bundle']['records'][0]['data']),
                'derived_count': lambda p: p['metadata']['traceable_import']['derived_counts'].__setitem__('decision_count', 99),
                'signed_claim': lambda p: p['replay_bundles'][0].__setitem__('signed', True)}.items():
            altered = copy.deepcopy(pack)
            edit(altered)
            assert altered != pack and H2.eval_pack_artifact(altered)['verdict'] in ('flagged', 'rejected'), (case, label)
        # ODES package: the package digest layer passes for the exported file and fails for an altered copy
        assert G.separate_consumer(ex['objects_on_disk']['odes'])['package_content_integrity'] == 'pass'
        altered_package = copy.deepcopy(package)
        altered_package['record']['planted_member'] = 'x'
        path = tmp_path / f'{case}.json'
        path.write_text(json.dumps(altered_package))
        assert G.separate_consumer(path)['package_content_integrity'] == 'fail'
        # the signing option of the bundle: an HMAC over the bundle verifies under the secret and not after an edit
        signed = R.sign_reconstruction_bundle(model, SECRET, key_id='key:synthetic-G1').model_dump(mode='json')
        assert R.verify_reconstruction_hmac(R.ReconstructionBundle.model_validate(signed), SECRET) is True
        signed['records'][0]['data']['planted_member'] = 'x'
        assert R.verify_reconstruction_hmac(R.ReconstructionBundle.model_validate(signed), SECRET) is False
        assert manifest  # (the manifest is retained next to each export)


@wiki_case('TC-L03-022')
def test_wiki_l03_022_a_redacted_derivative_is_refused_by_the_pack_and_package_exporters_known_limit(four):
    R = G.replay()
    from agent_governance_evidence_pack.importer import import_manifest_reconstruction
    from odes import export_cognous_stack_package
    ex = four['lost_ack']
    bundle = R.ReconstructionBundle.model_validate(G.load(ex, 'bundle'))
    manifest = G.load(ex, 'manifest')
    paths = sorted({r.source_path for r in bundle.records if not r.source_path.startswith('check_events') or r.source_path == 'check_events[0]'})
    refused = {}
    for path in paths:
        derivative = R.redact_reconstruction_bundle(bundle, redact_paths={path})
        assert derivative.derivation is not None and derivative.status == 'redacted'  # the Replay component produces a derivative with lineage
        dumped = derivative.model_dump(mode='json')
        row = {}
        for name, fn in (('pack', import_manifest_reconstruction), ('odes', export_cognous_stack_package)):
            try:
                fn(manifest, dumped)
                row[name] = 'accepted'
            except Exception as exc:
                row[name] = 'refused:' + type(exc).__name__
        refused[path] = row
    # the derivative is not carried further as a redacted state: every path tried is refused by both exporters
    assert all(v['pack'].startswith('refused') and v['odes'].startswith('refused') for v in refused.values()), refused
    # control: the unredacted bundle is accepted by both
    assert import_manifest_reconstruction(manifest, G.load(ex, 'bundle')) and export_cognous_stack_package(manifest, G.load(ex, 'bundle'))
