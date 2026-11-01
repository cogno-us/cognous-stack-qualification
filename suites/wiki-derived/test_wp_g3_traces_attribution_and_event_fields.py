"""Scenario-derived tests: replayable traces, identity attribution and event fields (work package G3).

SPDX-License-Identifier: Apache-2.0

Three catalog cases classified APPLICABLE, each checked for the part inside the declared scope of the stack against the pinned
synthetic reference (retained producer runs of route A, written to files and read back).

* TC-L06-028, action logging and replayable traces (scope: effect lineage only, no model turns): each run is reconstructed from
  its exported records alone and compared with the script of the run.
* TC-L09-025, identity audit trail (scope: who, what and on whose behalf as recorded in the decision, the binding and the replay
  bundle): ten actions from ten retained runs, each checked for the user, agent, tool, resource, decision, time and authority.
* TC-L17-002, event schema and field completeness (scope: the journal and ODES schema only; no SIEM source): the fields of the
  case list are mapped onto the members the records carry, across more than 100 retained events of more than 10 record types.

Existing coverage that these tests build on (not copied): the producer, bundle, pack and package evaluators and planted-defect
catalogues of ``suites/v1-scenarios/_d06_d07_d08_helpers.py``, the retained-record checks of ``test_scn_c12.py`` and the version
checks of ``suites/v1-probes/test_odes_probes.py``.

Limits, asserted as limits and never as passes:

* the case wants sensitive values masked: the destination state, with the synthetic payload of the refund, is written in clear to
  the journal (observations and reconciliations), the executor export, the bundle, the Evidence Pack and the ODES package; the
  Replay redaction can replace the records that carry it, but the copy kept in the bundle metadata stays, and a redacted derivative
  is refused by the pack and package importers (TC-L06-028, TC-L17-002);
* one bundle holds one proposal, so a run of parallel tool calls is not a single trace; a retry shows as two attempt records of one
  effect (TC-L06-028);
* the clocks of the journal and of the executor are independent and the bundle states no order between records of different
  ledgers; the order inside a ledger is the order of the rows (TC-L06-028, TC-L09-025);
* of the fourteen fields of the case list, four are not carried by any record: device, model (ODES says ``unavailable``), severity
  and, outside the tenant-aware flow, tenant (TC-L17-002). With those four counted as applicable the carried share is 10 of 14;
  whether they are applicable to this stack is a decision for the owner, not for the test;
* a decision that is held carries no binding, so for a held decision the user, agent, tool and resource are read from the
  proposal record that is retained next to it (TC-L09-025);
* the on-whose-behalf chain stops at the principal, the grant and the mandate: no delegation chain is carried (delegation is refused
  wholesale in this release) (TC-L09-025).

Not claimed here: SIEM sources, a search interface, a time zone other than UTC, model turns, device identity or alerting.
"""
from __future__ import annotations

import copy
import json
import re

import pytest

import _wiki_helpers as W
import _wp_g_common as G
from _wiki_helpers import wiki_case

pytestmark = pytest.mark.usefixtures('pinned_reference')

NINE = ('valid', 'lost_ack', 'race', 'revoked', 'unreadable', 'purpose_closed', 'purpose_reopened', 'tampered_evidence', 'input_dropped')
UTC = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(\+00:00|Z)$')
REQUIRED = ('time', 'tenant', 'user', 'device', 'agent', 'model', 'tool', 'resource', 'policy', 'decision', 'severity', 'session identifier',
            'correlation identifier', 'source layer')


@pytest.fixture(scope='module')
def four(pinned_reference, tmp_path_factory):
    built = G.build_four(tmp_path_factory.mktemp('wp-g3-four'))
    yield built
    G.check_exports_unchanged(built)


@pytest.fixture(scope='module')
def ten(pinned_reference, tmp_path_factory):
    """Ten retained runs: the nine outcomes of the frozen harness and a second applied run."""
    H2 = G.h2()
    root = tmp_path_factory.mktemp('wp-g3-ten')
    built = [(case, H2.build_exports(case, root / f'run-{i}')) for i, case in enumerate(NINE + ('valid',))]
    yield built
    for i, (case, ex) in enumerate(built):
        for name, expected in ex['sha256'].items():
            assert G.file_digest(ex['dir'] / name) == expected, f'exported original {i}/{case}/{name} was modified'


def story(bundle):
    """What the exported records alone say happened, step by step."""
    steps = []
    for r in bundle['records']:
        kind, d = r['record_type'], r['data']
        if kind == 'runtime_proposal':
            steps.append(('proposal', d['action_id'], d['target']))
        elif kind == 'runtime_decision':
            steps.append(('decision', d['result'], tuple(d['reasons'])))
        elif kind == 'control_plane_attempt_transition':
            steps.append(('attempt', d['status']))
        elif kind == 'effect_observation':
            steps.append(('observation', d['state']))
        elif kind == 'reconciliation':
            steps.append(('reconciliation', d['result']))
        elif kind == 'effect_time_refusal':
            steps.append(('refusal', d['stage'], tuple(d['reasons'])))
        elif kind == 'execution_result':
            steps.append(('result', d['status']))
        elif kind == 'destination_effect':
            steps.append(('effect', d['state']))
    return steps


def script(case, lost_ack_status):
    """The expected steps of a run, written from the behaviour of the frozen harness and not read from its records."""
    proposal = ('proposal', 'urn:cognous:action:refund-issue-routine-v1', 'urn:cognous:synthetic-account:customer-001')
    decision = ('decision', 'authorized', ())
    return {
        'valid': [proposal, decision, ('attempt', 'attempted'), ('attempt', 'acknowledged'), ('observation', 'absent'), ('observation', 'applied'),
                  ('reconciliation', 'observed_absent'), ('reconciliation', 'applied'), ('result', 'executed'), ('effect', 'applied')],
        'lost_ack': [proposal, decision, ('attempt', 'attempted'), ('attempt', 'unknown'), ('observation', 'absent'), ('observation', 'applied'),
                     ('reconciliation', 'observed_absent'), ('reconciliation', 'applied'), ('result', lost_ack_status), ('effect', 'applied')],
        'revoked': [proposal, decision, ('refusal', 'effect_time_revalidation', ('grant_revoked',)), ('result', 'denied')],
        'unreadable': [proposal, decision, ('refusal', 'effect_time_revalidation', ('status_unreadable',)), ('result', 'denied')],
    }[case]


# ================================================================================================ TC-L06-028
@wiki_case('TC-L06-028')
def test_wiki_l06_028_each_run_is_reconstructed_from_the_exported_records_alone_and_matches_the_script(four):
    lost = G.h2().lost_ack_status()
    total = matched = 0
    for case, ex in four.items():
        bundle = G.load(ex, 'bundle')
        wanted, got = script(case, lost), story(bundle)
        # the destination effects the script lists are the ones the destination holds; the test does not read the destination
        assert got == wanted, (case, got)
        total += len(wanted)
        matched += sum(1 for a, b in zip(wanted, got) if a == b)
        # every record is a reconstructable step: it names its type, its identifiers and its place in the sequence
        assert all(r['record_type'] and r['record_id'] and r['identifiers'] is not None for r in bundle['records'])
        # the records of the Control Plane name the run; the records of the executor and the destination name the effect and the decision
        assert all(r['identifiers'].get('run_id') == bundle['run_id'] for r in bundle['records'] if r['record_type'] in ('runtime_decision', 'runtime_proposal'))
        assert [r['source_sequence'] for r in bundle['records']] == list(range(len(bundle['records'])))
    assert total == 28 and matched == total


@wiki_case('TC-L06-028')
def test_wiki_l06_028_the_blocked_action_and_the_approval_are_visible_in_the_records(four):
    refused = G.load(four['revoked'], 'bundle')
    refusal = G.records_of(refused, 'effect_time_refusal')[0]['data']
    assert refusal['stage'] == 'effect_time_revalidation' and set(refusal['reasons']) == {'grant_revoked'}
    assert refusal['effect_id'] == G.records_of(refused, 'runtime_decision')[0]['data']['effect_id']  # the blocked action is the decided one
    assert G.records_of(refused, 'execution_result')[0]['data']['status'] == 'denied' and not G.records_of(refused, 'destination_effect')
    for case, ex in four.items():
        decision = G.records_of(G.load(ex, 'bundle'), 'runtime_decision')[0]['data']
        approvals = [i for i in decision['resolution_inputs'] if i['input_type'] == 'approval']
        assert len(approvals) == 1 and approvals[0]['observed']['status'] == 'active'  # the approval the decision relied on
        assert decision['binding']['runtime_authority']['approval_commitment'].startswith('sha256:'), case
    # the blocked action is also named in the ODES package and in the pack
    facts = G.load(four['revoked'], 'odes')['provenance']['execution_facts']
    assert len(facts['effect_time_refusal']) == 1 and 'grant_revoked' in json.dumps(facts['effect_time_refusal'])
    assert G.load(four['revoked'], 'pack')['metadata']['traceable_import']['refusal_vocabulary_summary']['total_refusals'] == 1


@wiki_case('TC-L06-028')
def test_wiki_l06_028_timestamps_and_order_inside_each_ledger_known_cross_ledger_limit(four):
    for case, ex in four.items():
        journal = G.load(ex, 'journal')
        for name, rows in journal.items():
            if not isinstance(rows, list):
                continue
            stamps = [r.get('recorded_at') or r.get('decided_at') or r.get('started_at') or r.get('evaluated_at') or r.get('reconciled_at') for r in rows]
            assert all(s is None or UTC.match(s) for s in stamps), (case, name)
            known = [s for s in stamps if s]
            assert known == sorted(known), (case, name)  # the order of the rows is the order of the times
    # limit: the records of different ledgers are not ordered by their clocks, and the pack says so
    pack = G.load(four['lost_ack'], 'pack')['metadata']['traceable_import']
    assert any('Independent clocks do not establish ordering' in line for line in pack['derived_counts']['counting_rules'])
    history = next(iter(pack['lifecycle_summary']['effect_observation_history'].values()))
    assert history['cross_sequence_order'] == 'not_established' and history['freshness_at_import'] == 'not_evaluated'
    # a retry is visible as two attempt records of one effect (lost acknowledgement), not as one step
    lost = G.load(four['lost_ack'], 'journal')
    assert [a['status'] for a in lost['attempts']] == ['attempted', 'unknown'] and len({a['effect_id'] for a in lost['attempts']}) == 1
    # limit: one bundle holds one proposal, so parallel tool calls are not one trace
    assert len(G.records_of(G.load(four['valid'], 'bundle'), 'runtime_proposal')) == 1


@wiki_case('TC-L06-028')
def test_wiki_l06_028_the_payload_is_not_masked_in_the_logs_and_redaction_does_not_reach_the_metadata_copy_known_limit(four):
    R = G.replay()
    from agent_governance_evidence_pack.importer import import_manifest_reconstruction
    ex = four['valid']
    marker = 'duplicate'  # the refund reason of the synthetic payload
    for name in ('journal', 'proposal', 'executor_export', 'bundle', 'pack', 'odes'):
        assert marker in json.dumps(G.load(ex, name)), name  # written in clear in each retained form
    assert marker in json.dumps(G.load(ex, 'journal')['observations'])  # the Control Plane log itself holds the destination state
    assert G.load(ex, 'journal')['decisions'][0]['binding']['payload_commitment'].startswith('sha256:')  # the decision holds a commitment only
    assert marker not in json.dumps(G.load(ex, 'manifest'))
    bundle = R.ReconstructionBundle.model_validate(G.load(ex, 'bundle'))
    carrying = {r.source_path for r in bundle.records if marker in json.dumps(r.model_dump(mode='json'))}
    assert carrying == {'attempts[1]', 'moltbot.control_plane_attempts[0]', 'moltbot.control_plane_evidence', 'moltbot.effects[0]', 'moltbot.execution_envelope',
                        'moltbot.execution_result', 'moltbot.observations[0]', 'observations[1]', 'proposal', 'reconciliations[1]'}
    derivative = R.redact_reconstruction_bundle(bundle, redact_paths=carrying)
    dumped = derivative.model_dump(mode='json')
    assert derivative.status == 'redacted' and all(marker not in json.dumps(r) for r in dumped['records'])  # the records are masked
    assert [m for m, v in dumped.items() if marker in json.dumps(v)] == ['metadata']  # limit: the copy in the bundle metadata is not
    # limit: the derivative is refused by the pack importer, so no masked pack is made from it
    with pytest.raises(Exception):
        import_manifest_reconstruction(G.load(ex, 'manifest'), dumped)


@wiki_case('TC-L06-028')
def test_wiki_l06_028_the_logs_are_tamper_evident_and_hold_no_model_turn(four):
    H2 = G.h2()
    R = G.replay()
    for case, ex in four.items():
        manifest = G.load(ex, 'manifest')
        base = {k: G.load(ex, k) for k in ('journal', 'proposal', 'executor_export')}
        missed = []
        for mid, _klass, _t, fn in H2.producer_mutations():
            planted, changed = H2.apply_mutation(base, fn)
            if changed and not H2.summarise(H2.evaluate_producer_exports(manifest, planted['journal'], planted['proposal'], planted['executor_export']))['detected']:
                missed.append(mid)
        assert missed == [], (case, missed)
        bundle = G.load(ex, 'bundle')
        assert R.content_digest(R.ReconstructionBundle.model_validate(bundle)).value == G.sha(G.bundle_without_integrity(bundle))
        # effect lineage only: the bundle states that it reconstructs recorded events, and no record names a model turn
        sem = bundle['semantics']
        assert (sem['model_reexecution'], sem['policy_reevaluation'], sem['external_effect_execution']) == (False, False, False)
        names = {str(k).lower() for r in bundle['records'] for _, k in _keys(r['data'])}
        assert not [n for n in names if any(w in n for w in ('prompt', 'completion', 'conversation', 'utterance', 'llm', 'model'))], case


def _keys(value, path=''):
    if isinstance(value, dict):
        for k, v in value.items():
            yield path, k
            yield from _keys(v, f'{path}/{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _keys(v, f'{path}/{i}')


# ================================================================================================ TC-L09-025
def attribution(bundle):
    """Who, what and on whose behalf for one action, read from the retained records of its bundle alone."""
    proposal = G.records_of(bundle, 'runtime_proposal')[0]['data']
    decision = G.records_of(bundle, 'runtime_decision')[0]['data']
    binding = decision['binding']
    inputs = {i['input_type']: i for i in decision['resolution_inputs']}
    refusal = G.records_of(bundle, 'effect_time_refusal')
    return {
        'user': binding['principal'], 'agent': binding['actor'], 'tool': binding['adapter_id'], 'action': binding['action_id'],
        'resource': binding['target'], 'decision': decision['result'], 'time': decision['decided_at'],
        'authority': binding['grant_id'], 'authority_revision': binding['grant_revision'], 'mandate': inputs['mandate']['input_id'],
        'approval': inputs['approval']['input_id'], 'identity': inputs['identity']['input_id'],
        'outcome': (refusal[0]['data']['reasons'] if refusal else G.records_of(bundle, 'execution_result')[0]['data']['status']),
        'proposal_actor': proposal['actor'], 'proposal_principal': proposal['principal'], 'proposal_target': proposal['target'],
    }


@wiki_case('TC-L09-025')
def test_wiki_l09_025_each_of_ten_actions_is_attributable_to_user_agent_tool_resource_decision_and_time(ten):
    attributable = 0
    for i, (case, ex) in enumerate(ten):
        row = attribution(G.load(ex, 'bundle'))
        complete = all(row[k] for k in ('user', 'agent', 'tool', 'resource', 'decision', 'time', 'authority', 'mandate', 'approval', 'identity', 'outcome'))
        # the decision and the proposal agree on who acted, for whom and on what
        assert (row['user'], row['agent'], row['resource']) == (row['proposal_principal'], row['proposal_actor'], row['proposal_target']), (i, case)
        assert row['user'] == 'urn:cognous:principal:refund-service' and row['agent'] == 'urn:cognous:identity:refund-agent-1'
        assert row['identity'] == row['agent'] and row['tool'] == 'urn:cognous:adapter:synthetic-refund-v1'
        attributable += int(complete)
    assert len(ten) == 10 and attributable >= 9 and attributable == 10


@wiki_case('TC-L09-025')
def test_wiki_l09_025_the_chain_is_reconstructed_across_the_four_systems_by_shared_identifiers(ten):
    for i, (case, ex) in enumerate(ten):
        bundle = G.load(ex, 'bundle')
        decision = G.records_of(bundle, 'runtime_decision')[0]
        effect_id = decision['identifiers']['effect_id']
        ids = {rec['record_type']: rec['identifiers'] for rec in bundle['records']}
        # system 1, the Control Plane journal: the decision and its checks name the effect and the decision
        assert decision['identifiers']['decision_id'] == decision['data']['decision_id']
        # system 2, the executor: its envelope names the same decision and effect
        envelope = G.records_of(bundle, 'execution_envelope')[0]['data']
        assert envelope['decision_id'] == decision['data']['decision_id'] and envelope['effect_id'] == effect_id, (i, case)
        assert envelope['operation']['principal'] == decision['data']['binding']['principal'] and envelope['operation']['actor'] == decision['data']['binding']['actor']
        # system 3, the destination: an applied effect names the same effect and the same operation target
        for effect in G.records_of(bundle, 'destination_effect'):
            assert effect['data']['effect_id'] == effect_id and effect['data']['target'] == decision['data']['binding']['target'], (i, case)
        # system 4, the replay bundle: explicit links tie executor attempts to Control Plane attempts
        links = bundle['links']
        assert all(link['link_type'] == 'explicit' for link in links)
        ids_known = {r['record_id'] for r in bundle['records']}
        attempted = bool(G.records_of(bundle, 'moltbot_attributed_control_plane_attempt'))  # a run refused before any attempt has no link to make
        assert bool(links) == attempted and all(l['from_record_id'] in ids_known and l['to_record_id'] in ids_known for l in links), (i, case)
        assert any(l['establishes_identity_equivalence'] for l in links) == attempted, (i, case)  # at least the attributed attempt is the Control Plane attempt
        assert {l['from_record_id'] for l in links} >= {r['record_id'] for r in G.records_of(bundle, 'moltbot_attributed_control_plane_attempt')}, (i, case)
        assert 'run_id' in next(iter(ids.values()))
    # the chain stops at the principal, the grant and the mandate: no delegation chain member is carried (limit)
    row = attribution(G.load(ten[0][1], 'bundle'))
    assert row['authority'] == 'urn:cognous:grant:routine-1' and row['mandate'] == 'urn:cognous:issuance:1'
    members = {str(k).lower() for r in G.load(ten[0][1], 'bundle')['records'] for _, k in _keys(r['data'])}
    assert not [m for m in members if 'delegat' in m and m != 'delegation_valid'], members


@wiki_case('TC-L09-025')
def test_wiki_l09_025_the_attribution_survives_into_the_pack_and_the_package_and_is_integrity_protected(ten):
    H2 = G.h2()
    for i, (case, ex) in enumerate(ten):
        bundle, package, pack = G.load(ex, 'bundle'), G.load(ex, 'odes'), G.load(ex, 'pack')
        row = attribution(bundle)
        facts = package['provenance']['decision_facts']
        assert (facts['actor'], facts['principal'], facts['decision_result']) == (row['agent'], row['user'], row['decision']), (i, case)
        assert package['record']['authority']['authority_basis'] == row['authority'] and package['record']['decision_timestamp'] == row['time']
        assert pack['replay_bundles'][0]['run_id'] == bundle['run_id']
        # integrity: the pack and the package of each run verify, and the bundle digest recomputes
        assert H2.eval_pack_artifact(pack)['verdict'] == 'accepted' and G.odes_layers(package)['package_content_integrity'] == 'pass'
        assert G.load(ex, 'pack')['metadata']['traceable_import']['input_artifacts'][1]['hash'] == G.sha(G.bundle_without_integrity(bundle))
    # altering the user, agent or decision of the retained decision record changes its hash and is detected on verification
    _, ex = ten[0]
    pack_hashes = {r['source_path']: r['hash'] for r in G.load(ex, 'pack')['metadata']['traceable_import']['source_record_refs']}
    for member in ('principal', 'actor', 'target'):
        bundle = G.load(ex, 'bundle')
        record = G.records_of(bundle, 'runtime_decision')[0]
        record['data']['binding'][member] += '~altered'
        assert G.sha(record) != pack_hashes[record['source_path']], member
        assert H2.summarise(H2.evaluate_bundle(G.load(ex, 'manifest'), bundle))['detected'], member


@wiki_case('TC-L09-025')
def test_wiki_l09_025_a_held_decision_has_no_binding_so_its_attribution_comes_from_the_proposal_known_limit(tmp_path, monkeypatch):
    p, r, f = G.rule_flow(tmp_path, monkeypatch)
    G.adopt(f, 'r1', 'v1')
    G.observe(r, 'v2')  # a policy that is not adopted: the decision is held
    held = G.decide(f, p)
    assert held.result == 'hold' and held.binding is None
    row = f.records.load().model_dump(mode='json')['decisions'][-1]
    # the held row names the identity it resolved, but carries no principal, tool, resource or grant revision of its own
    assert any(i['input_type'] == 'identity' and i['input_id'] == p.actor for i in row['resolution_inputs'])
    assert row['binding'] is None
    # the proposal is the record that carries them
    assert (p.principal, p.actor, p.target, p.adapter_id) == ('urn:cognous:principal:refund-service', 'urn:cognous:identity:refund-agent-1',
                                                             'urn:cognous:synthetic-account:customer-001', 'urn:cognous:adapter:synthetic-refund-v1')


# ================================================================================================ TC-L17-002
def field_map(bundle):
    """Which of the fourteen required fields are carried by the retained records of one action, and in which member."""
    proposal = G.records_of(bundle, 'runtime_proposal')[0]
    decision = G.records_of(bundle, 'runtime_decision')[0]
    b = decision['data']['binding']
    carried = {
        'time': 'recorded_at' if decision['recorded_at'] else None,
        'user': 'binding.principal' if b.get('principal') else None,
        'agent': 'binding.actor' if b.get('actor') else None,
        'tool': 'binding.adapter_id' if b.get('adapter_id') else None,
        'resource': 'binding.target' if b.get('target') else None,
        'policy': 'binding.policy_versions' if b.get('policy_versions') else None,
        'decision': 'result' if decision['data'].get('result') else None,
        'session identifier': 'identifiers.run_id' if decision['identifiers'].get('run_id') else None,
        'correlation identifier': 'proposal.correlation_id' if proposal['data'].get('correlation_id') else None,
        'source layer': 'producer_profile_id' if decision.get('producer_profile_id') else None,
        'tenant': 'binding.tenant_id' if b.get('tenant_id') else None,
        'device': next((k for k in b if 'device' in k or 'host' in k), None),
        'model': next((k for k in b if 'model' in k), None),
        'severity': next((k for k in decision['data'] if 'severity' in k), None),
    }
    return {k: v for k, v in carried.items()}


@wiki_case('TC-L17-002')
def test_wiki_l17_002_more_than_one_hundred_events_of_more_than_ten_types_carry_the_envelope_fields(ten):
    events, types = 0, set()
    for _, ex in ten:
        bundle = G.load(ex, 'bundle')
        for r in bundle['records']:
            events += 1
            types.add(r['record_type'])
            # every event of every type names its type, producer, evidence class, session and place; the time member is always present
            assert set(r) == {'data', 'evidence_class', 'identifiers', 'producer_profile_id', 'record_id', 'record_type', 'recorded_at', 'source_path', 'source_sequence'}
            assert r['producer_profile_id'] and r['evidence_class'] and r['identifiers'] is not None and r['record_id'].count(':') >= 1
            assert r['identifiers'].get('run_id') or r['identifiers'].get('effect_id') or r['record_type'] in ('executor_control_plane_evidence',)
    assert events >= 100 and len(types) >= 10, (events, sorted(types))


@wiki_case('TC-L17-002')
def test_wiki_l17_002_the_required_field_list_is_mapped_ten_of_fourteen_carried_and_four_not_carried_known_limit(ten):
    maps = [field_map(G.load(ex, 'bundle')) for _, ex in ten]
    assert all(m == maps[0] for m in maps)  # the same members in every run, whatever the outcome
    carried = sorted(k for k, v in maps[0].items() if v)
    missing = sorted(k for k, v in maps[0].items() if not v)
    assert set(carried) | set(missing) == set(REQUIRED)
    assert missing == ['device', 'model', 'severity', 'tenant'] and len(carried) == 10  # 10 of 14 fields
    assert maps[0]['correlation identifier'] == 'proposal.correlation_id' and maps[0]['session identifier'] == 'identifiers.run_id'
    # model: not carried by the journal, and stated as unavailable by the ODES record (distinct from absent)
    odes = G.load(ten[0][1], 'odes')['record']['machine_role']
    assert (odes['model_id'], odes['model_version']) == ('unavailable', 'unavailable')
    # severity: findings of the import carry a severity, the decision does not
    findings = [fi for r in G.load(ten[0][1], 'bundle')['import_reports'] for fi in r['findings']]
    assert findings and all(fi['severity'] in ('info', 'warning', 'error') for fi in findings)


@wiki_case('TC-L17-002')
def test_wiki_l17_002_the_tenant_field_is_carried_in_the_tenant_aware_flow_only(tmp_path, monkeypatch):
    flow = W.route_a(tmp_path, monkeypatch, tenant='tenant-alpha')
    assert flow.d.result == 'authorized'
    row = flow.f.records.load().model_dump(mode='json')['decisions'][0]['binding']
    assert row['tenant_id'] == 'tenant-alpha'
    assert not G.records_of(G.load(G.build_four.__globals__['h2']().build_exports('valid', tmp_path / 'default'), 'bundle'), 'runtime_decision')[0]['data']['binding'].get('tenant_id')


@wiki_case('TC-L17-002')
def test_wiki_l17_002_names_are_consistent_across_event_types_and_runs_and_all_times_are_utc(ten):
    by_type = {}
    for _, ex in ten:
        bundle = G.load(ex, 'bundle')
        for r in bundle['records']:
            by_type.setdefault(r['record_type'], []).append(set(r['data']))
            if r['recorded_at']:
                assert UTC.match(r['recorded_at']), r['source_path']
    # one member set per event type, whatever the run (the only exceptions are optional members of the same type)
    for kind, sets in by_type.items():
        if kind == 'executor_control_plane_evidence':
            continue  # its members depend on the outcome by design (attempt, refusal, reconciliation, failure); checked below
        common = set.intersection(*sets)
        extra = set.union(*sets) - common
        assert common and len(extra) <= 3, (kind, sorted(extra))
    assert set().union(*by_type['executor_control_plane_evidence']) <= {'attempt', 'failure_record_id', 'reconciliation', 'refusal'}
    # the same concept has the same name in the decision, the refusal and the ODES package
    shared = {'decision_id', 'effect_id', 'reasons', 'resolution_inputs', 'reason_vocabulary_version'}
    first = G.load(ten[3][1], 'bundle')  # a revoked run holds both a decision and a refusal
    assert shared <= set(G.records_of(first, 'runtime_decision')[0]['data']) and shared - {'result'} <= set(G.records_of(first, 'effect_time_refusal')[0]['data']) | {'decision_id'}
    for _, ex in ten:
        package = G.load(ex, 'odes')
        assert UTC.match(package['created_at']) and UTC.match(package['record']['decision_timestamp'])


@wiki_case('TC-L17-002')
def test_wiki_l17_002_the_schema_is_documented_with_versions_and_sensitive_values_are_not_masked_known_limit(four):
    ex = four['valid']
    bundle, package, pack, journal = G.load(ex, 'bundle'), G.load(ex, 'odes'), G.load(ex, 'pack'), G.load(ex, 'journal')
    assert bundle['bundle_version'] == '0.2.0' and pack['pack_version'] == '0.2.0' and package['package_version'] == '0.1.0'
    assert package['profile']['schema_name'] == 'pder-v0.1' and package['profile']['implementation_profile'] == 'odes_cognous_stack_export_0_2'
    assert journal['decisions'][0]['reason_vocabulary_version'] == 'runtime-authority-reasons/0.1'
    assert pack['metadata']['traceable_import']['transformation_version'].startswith('agep-manifest-reconstruction-import/')
    # a change of the schema version is refused or flagged by the consumers (the version variants of SCN-C12 and SCN-C14 are the control);
    # here: an unsupported package version is not validated
    altered = copy.deepcopy(package)
    altered['package_version'] = '9.9.9'
    assert G.odes_layers(altered)['schema_validity'] != 'pass' or G.odes_layers(altered)['declared_profile_conformance'] != 'pass'
    # limit: the payload of the synthetic refund is written in clear (see TC-L06-028); the decision holds a commitment only
    assert 'duplicate' in json.dumps(journal['observations']) and journal['decisions'][0]['binding']['payload_commitment'].startswith('sha256:')
