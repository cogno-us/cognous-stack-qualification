"""Scenario-derived tests: an evidence pack on demand and the state at decision time (work package G2).

SPDX-License-Identifier: Apache-2.0

Two catalog cases classified APPLICABLE that needed new implementation of the test (no existing test covers them), checked for the
part inside the declared scope of the stack against the pinned synthetic reference.

* TC-L02-016, audit readiness: an evidence pack is generated on demand from the retained records of a run, timed, checked against
  what the manifest declares, shown to list what it does not establish, exported and verified. Scope: one pack per retained run;
  compliance-framework packs are not claimed.
* TC-D12-004, state at incident time: a change history of six changes (role mapping twice, grant status label, evidence state,
  and policy content changed and rolled back through signed revisions) is applied between decisions of one record store;
  the state of every component that shaped a decision is read from the retained decision record alone and compared with the
  change record, for the incident time and for earlier times. Scope: the policy, grant, manifest and decision inputs at decision
  time only; the model, prompts and retrieval state are not recorded.

Limits, asserted as limits and never as passes:

* the pack importer takes a manifest and one bundle and has no framework, period or sampling input; a period is a selection of
  retained runs made by the caller (TC-L02-016);
* the pack lists what it does not establish (six of nine evidence levels are unavailable or not established by import) and does
  not redact: the synthetic identifiers of the run stay in the retained records, and a redacted derivative is refused by the importer
  (TC-L02-016);
* no model identifier, model version, prompt, sampling setting, guardrail setting, retrieval setting or feature flag is recorded in
  any retained record (TC-D12-004);
* the platform sees a change only through the inputs its resolver reports: the state of a model, a prompt, a provider-side update
  or a change made outside the platform is not part of any decision record (TC-D12-004);
* a policy version edited inside a retained decision is read as given by the Replay importer; the retained decisions are
  tamper-evident through the outside-held digest (witness) and through the digest of an exported copy, not through the importer
  (TC-D12-004).

Not claimed here: a point-in-time query interface (the state at a time is derived by the test from the ordered records), model or
prompt versioning, a change-management system, framework mappings, redaction of exports, or a pack covering several runs.
"""
from __future__ import annotations

import copy
import inspect
import json
import time
from datetime import timedelta

import pytest

import _wiki_helpers as W
import _wp_g_common as G
from _wiki_helpers import wiki_case

pytestmark = pytest.mark.usefixtures('pinned_reference')

GENERATION_BUDGET_SECONDS = 120  # the case allows one hour; the test holds the generation to two minutes
UNAVAILABLE = {'unavailable', 'not_established_by_import', 'not_evaluated_during_import'}


@pytest.fixture(scope='module')
def four(pinned_reference, tmp_path_factory):
    built = G.build_four(tmp_path_factory.mktemp('wp-g2-four'))
    yield built
    G.check_exports_unchanged(built)


def import_pack(manifest, bundle):
    from agent_governance_evidence_pack.importer import import_manifest_reconstruction
    return import_manifest_reconstruction(manifest, bundle)


# ================================================================================================ TC-L02-016
@wiki_case('TC-L02-016')
def test_wiki_l02_016_a_pack_is_generated_on_demand_for_each_retained_run_in_the_budget_and_validates(four):
    from agent_governance_evidence_pack import validate_evidence_pack
    for case, ex in four.items():
        manifest, bundle = G.load(ex, 'manifest'), G.load(ex, 'bundle')
        started = time.perf_counter()
        pack = import_pack(manifest, bundle)
        report = validate_evidence_pack(pack)
        took = time.perf_counter() - started
        assert took < GENERATION_BUDGET_SECONDS, (case, took)
        assert report.valid and not [i for i in report.issues if str(i.severity).endswith('error')], case
        data = pack.model_dump(mode='json')
        assert data == G.load(ex, 'pack')  # the pack on demand is the pack the run exported: generation is repeatable
        assert data['validation_summary']['valid_bundle_count'] == 1 and data['validation_summary']['error_count'] == 0
        assert data['replay_bundles'][0]['run_id'] == bundle['run_id'] and data['replay_bundles'][0]['validation_status'] == 'semantically_valid'


@wiki_case('TC-L02-016')
def test_wiki_l02_016_the_pack_names_every_declared_action_and_tool_and_every_retained_record(four):
    for case, ex in four.items():
        manifest, bundle, pack = G.load(ex, 'manifest'), G.load(ex, 'bundle'), G.load(ex, 'pack')
        declared = [a['action_name'] for a in manifest['actions']] + [t['tool_name'] if 'tool_name' in t else t['name'] for t in manifest['tools']]
        listed = [a['action_name'] for a in pack['action_inventory']] + [t['tool_name'] for t in pack['tool_inventory']]
        covered = [x for x in declared if x in listed]
        assert len(declared) == 3 and len(covered) / len(declared) >= 0.9 and sorted(listed) == sorted(declared), (case, declared, listed)
        refs = {r['source_path'] for r in pack['metadata']['traceable_import']['source_record_refs']}
        assert refs == {r['source_path'] for r in bundle['records']}  # evidence for each retained record, none left out
        # the requirement the executed or refused decision relied on is the one the manifest declares for the action
        binding = G.load(ex, 'journal')['decisions'][0]['binding']
        assert binding['action_id'] in [a['action_id'] for a in manifest['actions']] and binding['manifest_digest'] == G.sha(manifest)
        assert {a['artifact_role']: a['hash'] for a in pack['metadata']['traceable_import']['input_artifacts']}['manifest'] == binding['manifest_digest']


@wiki_case('TC-L02-016')
def test_wiki_l02_016_the_pack_states_what_it_does_not_establish(four):
    for case, ex in four.items():
        pack = G.load(ex, 'pack')
        ti = pack['metadata']['traceable_import']
        levels = {name: row['status'] for name, row in ti['control_evidence_levels'].items()}
        assert levels['declared'] == 'present' and levels['semantic_validation_performed_during_import'] == 'validated_complete'
        missing = sorted(name for name, status in levels.items() if status in UNAVAILABLE)
        assert missing == ['attributable_test_run_evidence', 'implemented', 'independently_audited', 'operationally_observed',
                           'source_asserted_runtime_evidence', 'tested', 'tested_in_this_repository'], (case, missing)  # each is listed, with its meaning
        assert all(ti['control_evidence_levels'][name]['meaning'] for name in missing)
        codes = {u['code'] for u in ti['unresolved_issues']}
        assert {'U_INDEPENDENT_VERIFICATION_UNAVAILABLE', 'U_OPERATIONAL_EFFECTIVENESS_NOT_MEASURED'} <= codes
        # the controls of the pack are 'planned' unless the import itself performed the check; nothing is promoted to implemented
        statuses = {c['control_name']: c['control_status'] for c in pack['policy_controls']}
        assert statuses['Replay semantic import validation'] == 'implemented' and statuses['Independent operational verification'] == 'planned'
        assert pack['review_status'] == 'draft' and pack['review_records'] == [] and pack['risk_register'] == []
    # the observation that is missing in a run is shown as unavailable, never as success
    assert G.load(four['unreadable'], 'pack')['metadata']['traceable_import']['lifecycle_summary']['destination_observed'] == 'unknown'
    assert G.load(four['valid'], 'pack')['metadata']['traceable_import']['lifecycle_summary']['destination_observed'] == 'applied'
    assert any('Missing observations are unavailable' in line
               for line in G.load(four['valid'], 'pack')['metadata']['traceable_import']['derived_counts']['counting_rules'])


@wiki_case('TC-L02-016')
def test_wiki_l02_016_the_exported_pack_is_a_file_that_loads_and_an_altered_copy_is_flagged(four, tmp_path):
    H2 = G.h2()
    for case, ex in four.items():
        pack = G.load(ex, 'pack')
        path = tmp_path / f'{case}-pack.json'
        path.write_text(json.dumps(pack))
        assert H2.eval_pack_artifact(json.loads(path.read_text()))['verdict'] == 'accepted'
        base = G.load(ex, 'pack')
        missed, planted = [], 0
        for mid, _klass, _target, fn in H2.pack_mutations(base):
            altered, changed = H2.apply_mutation(base, fn)
            if not changed:
                continue
            planted += 1
            if H2.eval_pack_artifact(altered)['verdict'] not in ('flagged', 'rejected'):
                missed.append(mid)
        assert planted >= 25 and missed == [], (case, planted, missed)
        # the pack binds the exact sources by digest: an edited manifest or bundle is refused at generation
        edited = copy.deepcopy(G.load(ex, 'manifest'))
        edited['actions'][0]['description'] = 'changed after the proposal was bound to the manifest digest'
        with pytest.raises(Exception, match='does not match supplied Manifest digest'):
            import_pack(edited, G.load(ex, 'bundle'))


@wiki_case('TC-L02-016')
def test_wiki_l02_016_no_framework_or_period_input_and_no_redaction_known_limit(four):
    from agent_governance_evidence_pack.importer import import_manifest_reconstruction
    names = list(inspect.signature(import_manifest_reconstruction).parameters)
    assert names == ['manifest', 'reconstruction_bundle', 'title', 'generated_at']  # one manifest, one bundle: no framework, period or sample
    # a period is the caller's selection of retained runs, one pack each; the packs of different runs differ in their run
    packs = {case: G.load(ex, 'pack') for case, ex in four.items()}
    assert len({p['replay_bundles'][0]['bundle_id'] for p in packs.values()}) == 4 and len({p['pack_id'] for p in packs.values()}) == 4
    assert all(len(p['replay_bundles']) == 1 for p in packs.values())
    # limit: the pack does not redact; the synthetic identifiers stay in the retained records and no redaction export is made
    for case, pack in packs.items():
        text = json.dumps(pack)
        assert 'customer-001' in text and pack['redaction_exports'] == [], case
        assert pack['metadata']['traceable_import']['redaction_state'] == {'derivation': None, 'redacted': False, 'source': 'unverified_source_claim'}
    # a redacted derivative of the bundle is refused by the importer, so a redacted pack cannot be made from it
    R = G.replay()
    ex = four['valid']
    derivative = R.redact_reconstruction_bundle(R.ReconstructionBundle.model_validate(G.load(ex, 'bundle')), redact_paths={'proposal'})
    with pytest.raises(Exception):
        import_pack(G.load(ex, 'manifest'), derivative.model_dump(mode='json'))


# ================================================================================================ TC-D12-004


class History:
    """One record store, six changes made between decisions, and the change record kept by the test."""

    def __init__(self, tmp_path, monkeypatch):
        self.ba, self.ra = G.tb(), G.tr()
        self.p, self.r, self.f = G.rule_flow(tmp_path, monkeypatch)
        self.t0 = self.ra.NOW
        self.inst = next(iter(self.r.role_mappings))
        self.grant_id = next(iter(self.r.statuses))
        self.changes = []   # (time, component, new value)
        self.decisions = []  # (time, decision)
        self.state = {'policy_digest': G.digest_of('v1'), 'role_mapping': ('roles-v1', self.r.role_mappings[self.inst].digest),
                      'grant_label': 'status-v1', 'optional_evidence': 'unknown', 'authority_context': 'proposed_pending_governor_review',
                      'refund_evidence': 'current'}
        G.adopt(self.f, 'r1', 'v1')

    def at(self, seconds):
        return self.t0 + timedelta(seconds=seconds)

    def decide(self, seconds):
        d = self.f.decide(self.p, now=self.at(seconds))
        assert d.result == 'authorized', (seconds, d.reasons)
        self.decisions.append((seconds, d))
        return d

    def change(self, seconds, component, value):
        self.changes.append((seconds, component, value))
        self.state[component] = value
        return seconds

    def expected_after(self, seconds):
        """The change record read at ``seconds``: the state after every change made up to and including that time."""
        state = {'policy_digest': G.digest_of('v1'), 'role_mapping': ('roles-v1', self.changes_initial_digest), 'grant_label': 'status-v1',
                 'optional_evidence': 'unknown', 'authority_context': 'proposed_pending_governor_review', 'refund_evidence': 'current'}
        for t, component, value in self.changes:
            if t <= seconds:
                state[component] = value
        return state

    def run(self):
        self.changes_initial_digest = self.r.role_mappings[self.inst].digest
        self.decide(0)
        self.set_role_mapping(8, 'roles-v2')
        self.decide(10)
        self.r.statuses[self.grant_id].version = 'status-v2'
        self.change(16, 'grant_label', 'status-v2')
        self.decide(18)
        G.adopt(self.f, 'r2', 'v2', 'v1')
        G.observe(self.r, 'v2')
        self.change(24, 'policy_digest', G.digest_of('v2'))
        self.decide(26)
        self.r.evidence['urn:cognous:evidence:optional-context'].state = 'current'
        self.change(32, 'optional_evidence', 'current')
        self.decide(34)
        G.adopt(self.f, 'r3', 'v1', 'v2')  # a rollback is a new signed revision back to the first digest
        G.observe(self.r, 'v1')
        self.change(40, 'policy_digest', G.digest_of('v1'))
        self.decide(42)
        self.set_role_mapping(48, 'roles-v3')
        self.decide(50)
        return self

    def set_role_mapping(self, seconds, version):
        rm = self.r.role_mappings[self.inst]
        rm.version = version
        rm.digest = G.chain().commitment({'institution_id': self.inst, 'version': version, 'aliases': rm.aliases})
        self.change(seconds, 'role_mapping', (version, rm.digest))


def state_of(decision):
    """The state of every component that shaped one retained decision, read from the decision record alone."""
    inputs = {}
    for item in decision['resolution_inputs']:
        inputs.setdefault(item['input_type'], {})[item['input_id']] = item['observed']
    only = lambda kind: next(iter(inputs[kind].values()))
    return {'policy_digest': only('policy').get('digest'), 'policy_version': only('policy')['version'],
            'role_mapping': (only('role_mapping')['version'], only('role_mapping')['digest']),
            'grant_label': only('grant')['version'], 'grant_revision': only('grant')['revision'], 'grant_status': only('grant')['status'],
            'authority_context': only('authority_context')['interface_status'], 'schema_version': only('authority_context')['schema_version'],
            'optional_evidence': inputs['evidence']['urn:cognous:evidence:optional-context']['state'],
            'refund_evidence': inputs['evidence']['urn:cognous:evidence:refund-entitlement']['state'],
            'manifest': (next(iter(inputs['manifest'])), next(i['record_commitment'] for i in decision['resolution_inputs'] if i['input_type'] == 'manifest')),
            'rule_state': decision['rule_identity']['rules'][G.tb().POLICY_REF]['state'] if decision.get('rule_identity') else None}


def decisions_of(history):
    doc = history.f.records.load().model_dump(mode='json')
    return doc['decisions']


def state_at(history, seconds):
    """The retained decision in force at ``seconds``: the last decision recorded at or before that time (None before the first)."""
    cutoff = history.at(seconds).isoformat()
    chosen = None
    for row in decisions_of(history):
        if row['decided_at'] <= cutoff:
            chosen = row
    return None if chosen is None else state_of(chosen)


@pytest.fixture
def history(tmp_path, monkeypatch):
    return History(tmp_path, monkeypatch).run()


@wiki_case('TC-D12-004')
def test_wiki_d12_004_the_state_at_every_decision_time_equals_the_change_record(history):
    rows = decisions_of(history)
    assert len(rows) == 7 and len(history.changes) == 6
    for seconds, _ in history.decisions:
        got, want = state_at(history, seconds), history.expected_after(seconds)
        for component in want:
            assert got[component] == want[component], (seconds, component)
    # every component class that shaped the decision is present in the retained record: completeness
    for row in rows:
        kinds = {i['input_type'] for i in row['resolution_inputs']}
        assert kinds == {'approval', 'authority_context', 'conflict', 'evidence', 'grant', 'identity', 'mandate', 'manifest', 'policy', 'role_mapping'}
        b = row['binding']
        assert b['manifest_digest'] and b['grant_id'] and b['grant_revision'] and b['policy_versions'] and b['role_mapping_digest']
        assert b['catalogue_digest' if 'catalogue_digest' in b else 'runtime_authority']  # the runtime authority block is bound
    # the state changed once per change and not otherwise: seven decisions, states that differ exactly where a change was made
    states = [state_of(r) for r in rows]
    differing = [sorted(k for k in states[i] if states[i][k] != states[i - 1][k]) for i in range(1, len(states))]
    assert differing == [['role_mapping'], ['grant_label'], ['policy_digest'], ['optional_evidence'], ['policy_digest'], ['role_mapping']]


@wiki_case('TC-D12-004')
def test_wiki_d12_004_an_earlier_time_is_answered_with_the_state_of_that_time_and_a_time_before_any_record_with_none(history):
    at = lambda s: state_at(history, s)
    assert at(-1) is None  # nothing is recorded before the first decision
    first, after_c1, mid, after_c5, last = at(0), at(12), at(30), at(45), at(60)
    assert first['role_mapping'][0] == 'roles-v1' and after_c1['role_mapping'][0] == 'roles-v2'
    assert first['grant_label'] == after_c1['grant_label'] == 'status-v1'  # the grant label changed later, at 16
    assert mid['grant_label'] == 'status-v2' and mid['policy_digest'] == G.digest_of('v2') and mid['optional_evidence'] == 'unknown'
    assert after_c5['policy_digest'] == first['policy_digest'] == G.digest_of('v1') and after_c5['optional_evidence'] == 'current'
    assert last['role_mapping'][0] == 'roles-v3' and last['policy_digest'] == G.digest_of('v1')
    # a query between two decisions gives the earlier decision, and the same query twice gives the same answer
    assert at(21) == at(18) and at(0) == at(5) and at(5) != at(12) and at(30) == at(30)
    assert all(at(12)[k] == v for k, v in history.expected_after(12).items())


@wiki_case('TC-D12-004')
def test_wiki_d12_004_the_retained_decision_states_the_policy_grant_and_manifest_of_the_incident(history):
    incident = decisions_of(history)[5]  # the decision taken at 42 s, after five changes
    state = state_of(incident)
    assert state['policy_digest'] == G.digest_of('v1') and state['rule_state'] == 'adopted'  # rolled back at 40 s
    assert state['grant_label'] == 'status-v2' and state['grant_revision'] == '1' and state['grant_status'] == 'active'
    assert state['role_mapping'][0] == 'roles-v2' and state['optional_evidence'] == 'current'
    manifest = history.f.manifest
    assert state['manifest'] == (manifest['manifest_id'], G.sha(manifest)) and incident['binding']['manifest_version'] == manifest['manifest_version']
    assert incident['binding']['policy_versions'] == [{'ref': G.tb().POLICY_REF, 'version': '1.0'}]
    # the change record (revision rows) lists the policy change with its prior and new digest, in order
    rows = G.rows(history.f)
    assert [(x['from_digest'], x['to_digest']) for x in rows] == [(None, G.digest_of('v1')), (G.digest_of('v1'), G.digest_of('v2')),
                                                                  (G.digest_of('v2'), G.digest_of('v1'))]
    # a change the platform does not accept is held and the held decision still retains the state it saw
    history.r.contexts[history.ba.PROFILE]['interface_status'] = 'active'
    held = history.f.decide(history.p, now=history.at(52))
    assert held.result == 'hold' and 'authority_context_status_mismatch' in held.reasons
    held_row = decisions_of(history)[-1]
    assert held_row['result'] == 'hold' and state_of(held_row)['authority_context'] == 'active'
    assert state_of(held_row)['policy_digest'] == G.digest_of('v1')


@wiki_case('TC-D12-004')
def test_wiki_d12_004_the_snapshot_is_tamper_evident_through_the_witness_and_an_exported_copy(history, tmp_path):
    import importlib
    witness_mod = importlib.import_module('agent_control_plane.witness')
    path = history.f.records.path
    witness = witness_mod.LocalFileWitness(tmp_path / 'witness.jsonl')
    witness_mod.publish_head(json.loads(path.read_text()), witness)
    assert witness_mod.verify_against_witness(path, witness).ok  # control
    good = json.loads(path.read_text())
    # rewrite the recorded role mapping version of an earlier decision, or its policy digest, or drop the decision: all are seen
    for label, edit in (
            ('role_mapping_version', lambda d: next(i for i in d['decisions'][1]['resolution_inputs'] if i['input_type'] == 'role_mapping')['observed'].__setitem__('version', 'roles-v1')),
            ('policy_digest', lambda d: next(i for i in d['decisions'][3]['resolution_inputs'] if i['input_type'] == 'policy')['observed'].__setitem__('digest', G.digest_of('v1'))),
            ('decision_dropped', lambda d: d['decisions'].pop(2)),
            ('revision_row_dropped', lambda d: d['rule_revisions'].pop())):
        doc = copy.deepcopy(good)
        edit(doc)
        assert doc != good
        assert not witness_mod.verify_against_witness(doc, witness).ok, label
    # the digest of an exported copy of the decision record also fails after an edit
    row = good['decisions'][5]
    exported = G.sha(row)
    altered = copy.deepcopy(row)
    next(i for i in altered['resolution_inputs'] if i['input_type'] == 'authority_context')['observed']['interface_status'] = 'active'
    assert G.sha(altered) != exported


@wiki_case('TC-D12-004')
def test_wiki_d12_004_the_exported_run_carries_the_decision_time_state_for_the_case_file(four):
    for case, ex in four.items():
        journal, bundle, pack, package = (G.load(ex, n) for n in ('journal', 'bundle', 'pack', 'odes'))
        decision = journal['decisions'][0]
        state = state_of({**decision, 'rule_identity': None})
        record = G.records_of(bundle, 'runtime_decision')[0]['data']
        assert state_of({**record, 'rule_identity': None}) == state  # the bundle carries the state of the decision unchanged
        facts = package['provenance']['decision_facts']
        assert facts['policy_versions'] == decision['binding']['policy_versions'] and facts['grant_revision'] == decision['binding']['grant_revision']
        retained = G.records_of(package['provenance']['retained_sources']['reconstruction_bundle'], 'runtime_decision')[0]['data']
        assert state_of({**retained, 'rule_identity': None}) == state
        assert state['manifest'][1] == package['provenance']['source_artifacts']['manifest_digest'] == G.sha(G.load(ex, 'manifest'))
        assert pack['metadata']['traceable_import']['selected_revisions']['manifest'] == package['provenance']['selected_revisions']['manifest']
    # the exported files are the case-file export: they read back and verify
    assert G.separate_consumer(four['valid']['objects_on_disk']['odes'])['package_content_integrity'] == 'pass'


@wiki_case('TC-D12-004')
def test_wiki_d12_004_model_prompt_guardrail_retrieval_and_feature_flag_are_not_recorded_known_limit(four, history):
    words = ('model', 'prompt', 'temperature', 'sampling', 'guardrail', 'retriev', 'index_version', 'feature_flag', 'system_message')
    surfaces = {'decision rows': decisions_of(history), 'journal': G.load(four['valid'], 'journal'), 'bundle records': G.load(four['valid'], 'bundle')['records'],
                'executor export': G.load(four['valid'], 'executor_export'), 'manifest': G.load(four['valid'], 'manifest')}
    for where, value in surfaces.items():
        hits = sorted({str(k) for _, k, _ in _members(value) if k and any(w in str(k).lower() for w in words)})
        assert hits == [], (where, hits)
    # the ODES record states that the machine role has no model identifier or version
    machine = G.load(four['valid'], 'odes')['record']['machine_role']
    assert (machine['model_id'], machine['model_version']) == ('unavailable', 'unavailable')
    # a change to the role mapping that is not reported with a new digest is held (the mapping no longer matches its digest), and the
    # held decision is retained with what it saw: an unreported change is refused, not recorded as unchanged
    history.r.role_mappings[history.inst].aliases['unreported-alias'] = ['urn:cognous:role:unreported']
    held = history.f.decide(history.p, now=history.at(54))
    assert held.result == 'hold' and 'role_mapping_invalid' in held.reasons
    assert decisions_of(history)[-1]['result'] == 'hold'
    # the retained decision is read as given by the importer: a policy version edited inside it is not refused (limit)
    ex = four['valid']
    journal = G.load(ex, 'journal')
    journal['decisions'][0]['binding']['policy_versions'][0]['version'] = '9.9'
    bundle = G.reconstruct(journal, G.load(ex, 'proposal'), G.load(ex, 'executor_export'))
    assert G.records_of(bundle, 'runtime_decision')[0]['data']['binding']['policy_versions'][0]['version'] == '9.9'


def _members(value, path=''):
    if isinstance(value, dict):
        for k, v in value.items():
            yield f'{path}/{k}', k, None
            yield from _members(v, f'{path}/{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _members(v, f'{path}/{i}')
