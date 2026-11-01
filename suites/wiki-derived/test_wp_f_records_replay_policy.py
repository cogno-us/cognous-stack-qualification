"""Scenario-derived tests: records, replay, policy revision and pin and digest refusal (work package F).

SPDX-License-Identifier: Apache-2.0

Seven catalog cases, each checked for the part that falls inside the declared scope of the stack, against the pinned synthetic
reference (route A, see README.md; most tests read exported records and never touch a destination). Each case keeps a positive
control next to the refusals it checks.

Limits, asserted as limits and never as passes:

* a reconstruction carries a fresh bundle identifier and a generation time on every run; the rest of the bundle is identical
  (TC-D12-007);
* the replay importer reconstructs one proposal per bundle: a record store that holds decisions for several proposals is refused
  as a whole, so a run of several actions is reconstructed one action at a time (TC-L17-020);
* a changed policy version inside a retained decision is not refused by the importer: it shows up as a difference between two
  reconstructions (TC-D12-007);
* decision-time input content (the values the decision recorded about its inputs) is carried as recorded and is not re-verified at
  import (TC-D12-007);
* policy content is read as a digest and a revision row, not as rules, in the bounded decision path (TC-L05-028, TC-L08-036);
* a policy configuration member the model does not know is dropped on load (TC-L05-028);
* the component revision check of the importer compares exact strings from a fixed list; hash-checked installation of
  dependencies is not part of this suite (TC-L16-007, TC-L16-015).

Not claimed here: model version, prompts, sampling settings or retrieved content (none is recorded), re-execution, a custody log
of exports, a cross-system timeline, pivots or filters, clock correction, a policy console or diff view, package indexes and
look-alike package detection.
"""
from __future__ import annotations

import copy
import dataclasses
import hashlib
import importlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import importlib.util
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

import _wiki_helpers as W
from _wiki_helpers import wiki_case

pytestmark = pytest.mark.usefixtures('pinned_reference')

ROOT = W.ROOT
REVISER = 'synthetic-principal:reviser'
SIGNER = 'synthetic-principal:signer'
RUN_MEMBERS = ('bundle_id', 'generated_at')
CP_NOW = '2026-10-05T19:00:00+00:00'


# ------------------------------------------------------------------------------------------------ helpers
def _h():
    return W._h()


def _h2():
    """The bundle export helpers of suites/v1-scenarios (the same pinned reference)."""
    _h()
    return importlib.import_module('_d06_d07_d08_helpers')


def _chain():
    return _h2().reference().chain


def _c2a():
    _h()
    return importlib.import_module('_c_2a_helpers')


def _tb():
    _h()
    return importlib.import_module('tests.test_bounded_authorization')


def _tr():
    _h()
    return importlib.import_module('tests.test_runtime_authority')


def _rr():
    _h()
    return importlib.import_module('agent_control_plane.rule_revision')


def _importers():
    _h()
    return importlib.import_module('agent_replay_bundle.importers')


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(canon(value)).hexdigest()


def stable(bundle):
    """The bundle without the two members that are new on every reconstruction (identifier and generation time)."""
    return {k: v for k, v in bundle.items() if k not in RUN_MEMBERS}


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reconstruct(journal, proposal, export, *, revision=None):
    """Replay import of retained records (copies read from disk), as a JSON dict."""
    ch = _chain()
    return _importers().import_bounded_workflow(copy.deepcopy(journal), proposal=copy.deepcopy(proposal), moltbot_export=copy.deepcopy(export),
                                                control_plane_revision=ch.CONTROL_PLANE_RUNTIME_AUTHORITY_REVISION if revision is None else revision).model_dump(mode='json')


def refusal_of(fn):
    """The typed refusal text of a call that must raise the importer's contract error, else None."""
    try:
        fn()
    except _importers().ImportContractError as exc:
        return str(exc)
    return None


def complete(bundle):
    return bundle['status'] == 'reconstruction_complete' and all(r['complete'] for r in bundle['import_reports'])


def kinds(bundle):
    return [r['record_type'] for r in bundle['records']]


def records_of(bundle, kind):
    return [r for r in bundle['records'] if r['record_type'] == kind]


def bundle_diff(left, right):
    """Where two reconstructions differ, apart from the members that are new on every run: [(member, record id or index)]."""
    out = []
    for member in sorted(set(left) | set(right)):
        if member in RUN_MEMBERS or left.get(member) == right.get(member):
            continue
        if member in ('records', 'links', 'commitments') and isinstance(left.get(member), list) and isinstance(right.get(member), list):
            key = 'record_id' if member == 'records' else None
            a, b = left[member], right[member]
            if len(a) != len(b):
                out.append((member, 'length'))
                continue
            for i, (x, y) in enumerate(zip(a, b)):
                if x != y:
                    out.append((member, x[key] if key else i))
        else:
            out.append((member, None))
    return out


def walk(value, path=''):
    """(path, member name or None, string value or None) for every member and string of a JSON value."""
    if isinstance(value, dict):
        for k, v in value.items():
            yield f'{path}/{k}', k, None
            yield from walk(v, f'{path}/{k}')
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from walk(v, f'{path}/{i}')
    elif isinstance(value, str):
        yield path, None, value


UNRECORDED_WORDS = ('conversation', 'prompt', 'seed', 'temperature', 'sampling', 'retriev', 'chunk', 'transcript', 'llm', 'utterance')


def unrecorded_hits(value):
    """Members or strings that name a conversation, prompt, sampling setting or retrieved content (the `model_*` members of the
    semantics block and the `unavailable` machine-role values are checked separately)."""
    hits = []
    for path, key, text in walk(value):
        for word in UNRECORDED_WORDS:
            if (key and word in key.lower()) or (text and word in text.lower()):
                hits.append((word, path))
    return hits


# ------------------------------------------------------------------------------------------------ retained exports (five bundles)
FIVE = ('valid', 'lost_ack', 'race', 'revoked', 'unreadable')


@pytest.fixture(scope='module')
def five(pinned_reference, tmp_path_factory):
    """Five producer runs of the frozen harness (an applied effect, a lost acknowledgement, a commit-time race, a revoked grant and
    an unreadable status), each written to disk and read back."""
    H2 = _h2()
    root = tmp_path_factory.mktemp('wp-f-five')
    built = {case: H2.build_exports(case, root) for case in FIVE}
    yield built
    for case, ex in built.items():
        for name, expected in ex['sha256'].items():
            assert file_digest(ex['dir'] / name) == expected, f'exported original {case}/{name} was modified'


def load(ex, name):
    return _h2().load_copy(ex, name)


def retained(ex):
    return SimpleNamespace(**{n: load(ex, n) for n in ('journal', 'proposal', 'executor_export', 'bundle', 'manifest', 'pack', 'odes')})


# ================================================================================================ TC-D12-007
@wiki_case('TC-D12-007')
def test_wiki_d12_007_three_reconstructions_of_each_of_five_bundles_are_byte_identical(five):
    """Three reconstructions of each of five bundles are byte-identical apart from the identifier and generation time.

    Limit: the ODES package carries a top-level `created_at` with one-second resolution, taken from the wall clock by the
    pinned exporter (it accepts no clock input). It is set aside exactly as `bundle_id` and `generated_at` are, and the
    comparison covers every other member of the package, including its integrity digest.
    """
    for case in FIVE:
        r = retained(five[case])
        runs = [reconstruct(r.journal, r.proposal, r.executor_export) for _ in range(3)]
        assert all(complete(b) or case in ('race', 'revoked', 'unreadable', 'lost_ack') for b in runs), case
        digests = {sha(stable(b)) for b in runs}
        assert len(digests) == 1, (case, [bundle_diff(runs[0], b) for b in runs[1:]])
        assert canon(stable(runs[0])) == canon(stable(runs[1])) == canon(stable(runs[2]))
        # the reconstruction equals the bundle that was retained when the run was exported
        assert canon(stable(runs[0])) == canon(stable(r.bundle)), (case, bundle_diff(r.bundle, runs[0]))
        assert len(runs[0]['records']) > 0 and runs[0]['status'] == r.bundle['status']
        # limit: the identifier and generation time are new on every reconstruction
        assert len({b['bundle_id'] for b in runs}) == 3
        assert all(b['bundle_id'] != r.bundle['bundle_id'] for b in runs)
        # the consumers of the same bundle are deterministic too (Evidence Pack and ODES package)
        from agent_governance_evidence_pack.importer import import_manifest_reconstruction
        from odes import export_cognous_stack_package
        packs = {sha(import_manifest_reconstruction(r.manifest, runs[0]).model_dump(mode='json')) for _ in range(3)}
        packages = {sha({k: v for k, v in export_cognous_stack_package(r.manifest, runs[0]).items() if k != 'created_at'}) for _ in range(3)}
        assert len(packs) == 1 and len(packages) == 1, case
    assert {five[c]['status'] for c in FIVE} >= {'executed', 'denied'}  # the five bundles are not five copies of one outcome


@wiki_case('TC-D12-007')
def test_wiki_d12_007_reconstruction_performs_no_destination_write_and_no_new_decision(tmp_path, monkeypatch):
    ch = _chain()
    flow = W.route_a(tmp_path, monkeypatch)
    res, exc = W.execute_a(flow)
    assert exc is None and res.status == 'executed'
    export = ch.export_execution_artifacts(flow.env, res, flow.dest, repository_revision=ch.MOLTBOT_RUNTIME_AUTHORITY_REVISION)
    store = flow.f.records
    watched = [Path(store.path)]  # the destination is a WAL database: its file bytes can change when an old connection closes, so it is
    #                               observed by content and by the count of connections opened
    keys = ('decisions', 'attempts', 'observations', 'reconciliations', 'refusals', 'check_events')
    before_summary = W.destination_summary(flow)
    before_rows = {k: len(getattr(store.load(), k)) for k in keys}
    before_files = [file_digest(p) for p in watched]
    decided, opened = [], []
    real_decide, real_connect = type(flow.f).decide, sqlite3.connect
    monkeypatch.setattr(type(flow.f), 'decide', lambda self, *a, **k: decided.append(1) or real_decide(self, *a, **k))
    monkeypatch.setattr(sqlite3, 'connect', lambda *a, **k: opened.append(a) or real_connect(*a, **k))
    raw = store.load().model_dump(mode='json')
    bundles = [ch.import_bounded_workflow(copy.deepcopy(raw), proposal=flow.p.model_dump(mode='json'), moltbot_export=copy.deepcopy(export),
                                          control_plane_revision=ch.CONTROL_PLANE_RUNTIME_AUTHORITY_REVISION).model_dump(mode='json') for _ in range(3)]
    from agent_governance_evidence_pack.importer import import_manifest_reconstruction
    from odes import export_cognous_stack_package
    import_manifest_reconstruction(flow.f.manifest, bundles[0])
    export_cognous_stack_package(flow.f.manifest, bundles[0])
    monkeypatch.undo()
    after_files = [file_digest(p) for p in watched]
    assert all(complete(b) for b in bundles)
    assert decided == [] and opened == []  # no decision taken and no database opened by any reconstruction step
    assert after_files == before_files  # the record store file is byte-identical
    assert W.destination_summary(flow) == before_summary
    assert {k: len(getattr(store.load(), k)) for k in keys} == before_rows
    # the bundle states what it did: nothing was executed or re-evaluated
    sem = bundles[0]['semantics']
    assert (sem['record_reconstruction'], sem['external_effect_execution'], sem['policy_reevaluation']) == (True, False, False)


@wiki_case('TC-D12-007')
def test_wiki_d12_007_changed_policy_or_manifest_input_is_reported_as_a_difference(five):
    r = retained(five['valid'])
    base = reconstruct(r.journal, r.proposal, r.executor_export)
    again = reconstruct(r.journal, r.proposal, r.executor_export)
    assert bundle_diff(base, again) == []  # control: unchanged input, no difference
    decision_record = records_of(base, 'runtime_decision')[0]['record_id']

    def changed(edit):
        j = copy.deepcopy(r.journal)
        edit(j['decisions'][0]['binding'])
        return reconstruct(j, r.proposal, r.executor_export)
    # a changed policy version, a changed policy reference and a changed role mapping are reconstructed as they were recorded and
    # shown as a difference in exactly the decision record; the importer does not refuse them (limit)
    pv = changed(lambda b: b['policy_versions'][0].update(version='9.9'))
    pr = changed(lambda b: b['policy_versions'][0].update(ref='urn:cognous:policy:other-policy'))
    rm = changed(lambda b: b.update(role_mapping_version='roles-v2'))
    for other in (pv, pr, rm):
        assert bundle_diff(base, other) == [('records', decision_record)]
    assert records_of(pv, 'runtime_decision')[0]['data']['binding']['policy_versions'][0]['version'] == '9.9'
    # a changed manifest is refused: by the importer when the decision binds another digest, by the Evidence Pack importer when the
    # supplied manifest is not the manifest the proposal names
    j = copy.deepcopy(r.journal)
    j['decisions'][0]['binding']['manifest_digest'] = 'sha256:' + '0' * 64
    assert 'manifest_digest conflicts with committed operation' in refusal_of(lambda: reconstruct(j, r.proposal, r.executor_export))
    p = copy.deepcopy(r.proposal)
    p['manifest_digest'] = 'sha256:' + '1' * 64
    assert 'proposal_commitment conflicts with committed operation' in refusal_of(lambda: reconstruct(r.journal, p, r.executor_export))
    H2 = _h2()
    assert H2.eval_pack_from_bundle(r.manifest, base)['verdict'] == 'accepted'  # control
    edited = copy.deepcopy(r.manifest)
    edited['actions'][0]['description'] = 'changed after the proposal was bound to the manifest digest'
    other_id = copy.deepcopy(r.manifest)
    other_id['manifest_id'] = 'urn:cognous:manifest:other'
    out = H2.eval_pack_from_bundle(edited, base)
    assert out['verdict'] == 'rejected' and 'does not match supplied Manifest digest' in out['why']
    assert (edited['manifest_id'], edited['manifest_version']) == (r.manifest['manifest_id'], r.manifest['manifest_version'])  # same label
    out = H2.eval_pack_from_bundle(other_id, base)
    assert out['verdict'] == 'rejected' and 'manifest_id does not match' in out['why']


@pytest.fixture(scope='module')
def valid_export(pinned_reference, tmp_path_factory):
    """One producer run of the frozen harness (an applied effect), written to disk and read back."""
    root = tmp_path_factory.mktemp('wp-f-valid')
    built = _h2().build_exports('valid', root)
    yield built
    for name, expected in built['sha256'].items():
        assert file_digest(built['dir'] / name) == expected, f'exported original valid/{name} was modified'


@wiki_case('TC-D12-007')
def test_wiki_d12_007_decision_time_input_content_is_carried_as_recorded_and_is_not_re_verified_at_import_known_limit(valid_export):
    """Limit: observation state is bound to the reconciliation records, the execution result, the destination rows and the
    reconstruction compare. Decision-time input content is carried as recorded and is not re-verified at import: a value edited in
    the retained decision is imported, and the reconstruction shows the edited text in the decision record only."""
    r = retained(valid_export)
    base = reconstruct(r.journal, r.proposal, r.executor_export)
    assert complete(base)  # control: the unedited records
    decision_record = records_of(base, 'runtime_decision')[0]['record_id']
    state_kinds = ('effect_observation', 'reconciliation', 'execution_result', 'destination_effect')
    assert all(records_of(base, kind) for kind in state_kinds)

    def edited(edit):
        j = copy.deepcopy(r.journal)
        edit(j['decisions'][0])
        return reconstruct(j, r.proposal, r.executor_export)

    def grant_input(decision):
        return next(x for x in decision['resolution_inputs'] if x['input_type'] == 'grant')
    in_binding = edited(lambda d: d['binding'].update(authority_context_status='edited decision-time text'))
    in_inputs = edited(lambda d: grant_input(d)['observed'].update(status='edited decision-time text'))
    for other in (in_binding, in_inputs):
        assert complete(other)  # imported, not refused
        assert bundle_diff(base, other) == [('records', decision_record)]  # only the decision record differs
        for kind in state_kinds:
            assert records_of(other, kind) == records_of(base, kind), kind  # the observation state is as it was
    assert records_of(in_binding, 'runtime_decision')[0]['data']['binding']['authority_context_status'] == 'edited decision-time text'
    assert grant_input(records_of(in_inputs, 'runtime_decision')[0]['data'])['observed']['status'] == 'edited decision-time text'


@wiki_case('TC-D12-007')
def test_wiki_d12_007_fidelity_statement_lists_what_is_not_reproduced(five):
    r = retained(five['valid'])
    bundle = reconstruct(r.journal, r.proposal, r.executor_export)
    sem = bundle['semantics']
    assert sem['record_reconstruction'] is True
    assert (sem['policy_reevaluation'], sem['model_reexecution'], sem['external_effect_execution'], sem['independent_effect_verification']) == \
        (False, False, False, False)
    assert sem['destination_observation'] == 'producer_reported'
    assert 'reconstructs recorded events only' in sem['notes'] and 'never renews permission or creates an effect' in sem['notes']
    # the Evidence Pack and the ODES package restate it
    pack_sem = r.pack['metadata']['traceable_import']['replay_semantics']
    assert pack_sem == sem or {k: pack_sem[k] for k in sem} == sem
    issues = {u['code'] for u in r.pack['metadata']['traceable_import']['unresolved_issues']}
    assert {'U_INDEPENDENT_VERIFICATION_UNAVAILABLE', 'U_HISTORICAL_AUTHORIZATION_NOT_CURRENT_PERMISSION'} <= issues
    assert any('renews no authorization' in line for line in r.odes['provenance']['limits'])
    assert any('no native fields' in line for line in r.odes['provenance']['unsupported_semantics'])
    # a model version is not recorded: the ODES record says so ('unavailable'), and nothing in the records names a model, prompt,
    # seed, sampling setting or retrieved content
    machine = r.odes['record']['machine_role']
    assert (machine['model_id'], machine['model_version']) == ('unavailable', 'unavailable')
    for name, value in (('bundle records', bundle['records']), ('journal', r.journal), ('executor export', r.executor_export),
                        ('manifest', r.manifest), ('proposal', r.proposal)):
        assert unrecorded_hits(value) == [], name
    assert not any('model' in k.lower() for _, k, _ in walk(bundle['records']) if k)


# ================================================================================================ rule revision flows
def digest_of(label):
    return _chain().commitment({'synthetic-policy-content': label})


def revision(rid, to, frm=None, *, signer=SIGNER, supersedes=None):
    ba, ra, rr = _tb(), _tr(), _rr()
    return rr.RuleRevision(revision_id=rid, rule_kind='policy', rule_ref=ba.POLICY_REF, from_digest=frm, to_digest=to, reviser=REVISER,
                           signer=signer, authority_ref='synthetic-authority:1', reason='synthetic', supersedes=supersedes,
                           recorded_at=ra.NOW.isoformat())


def rule_flow(tmp_path, monkeypatch, content='v1'):
    """Bounded workflow with the opt-in rule revision profile: the resolver reports the digest of the policy it runs."""
    ba, ra, rr = _tb(), _tr(), _rr()
    bounded = importlib.import_module('agent_control_plane.bounded')
    monkeypatch.setattr(bounded, '_now', lambda: ra.NOW)
    p, r, f, c = ra.setup_flow(tmp_path)
    f.rule_revision_profile = rr.RuleRevisionProfile(signers=[SIGNER])
    r.policies[ba.POLICY_REF].digest = digest_of(content)
    return p, r, f


def adopt(f, rid, to_label, from_label=None, **kw):
    return _rr().append_rule_revision(f.records, f.rule_revision_profile,
                                      revision(rid, digest_of(to_label), digest_of(from_label) if from_label else None, **kw))


def observe(r, label):
    r.policies[_tb().POLICY_REF].digest = digest_of(label)


def decide(f, p):
    return f.decide(p, now=_tr().NOW)


def rule_of(decision):
    return decision.rule_identity['rules'][_tb().POLICY_REF]


def adopted(f):
    """The digest the revision rows currently adopt for the policy (None when nothing counts)."""
    rr = _rr()
    return rr.adopted_digest(f.rule_revision_profile, f.records.load().rule_revisions, _tb().POLICY_REF)


def rows(f):
    return [x.model_dump(mode='json') for x in f.records.load().rule_revisions]


POLICY_JSON = {'policy_version': 'refund-policy-1', 'allowed_tools': ['refund_tool', 'lookup_tool'], 'blocked_tools': ['export_tool'],
               'authority_required': {'write': ['write']}, 'default_action': 'escalate'}


def policy_file(tmp_path, name, content):
    path = tmp_path / name
    path.write_bytes(canon(content))
    return path


def policy_config(path):
    _h()
    return importlib.import_module('agent_control_plane.policy_config').load_policy_config(path)


def gate_decision(config, tool, *, action_type='read'):
    _h()
    models = importlib.import_module('agent_control_plane.models')
    gate = importlib.import_module('agent_control_plane.policy_gate').PolicyGate()
    frame = importlib.import_module('agent_control_plane.policy_config').frame_from_policy_config(config, task='synthetic', actor='synthetic-actor',
                                                                                                  environment='test')
    action = models.ActionProposal(action_id='action-1', run_id='run-1', tool_name=tool, action_type=action_type, target='synthetic://target',
                                   proposed_at=CP_NOW)
    return gate.evaluate(action, frame, [], now=CP_NOW)


def config_digest(config):
    return _chain().commitment(config.model_dump(mode='json'))


# ================================================================================================ TC-L05-028
@wiki_case('TC-L05-028')
def test_wiki_l05_028_policy_config_round_trip_is_byte_stable(tmp_path):
    path = policy_file(tmp_path, 'policy-1.json', POLICY_JSON)
    config = policy_config(path)
    stored = canon(config.model_dump(mode='json'))
    assert stored == path.read_bytes()  # the stored form is the canonical form of the loaded policy
    second = policy_file(tmp_path, 'policy-2.json', json.loads(stored))
    config_2 = policy_config(second)
    assert canon(config_2.model_dump(mode='json')) == stored and second.read_bytes() == path.read_bytes()
    assert config_digest(config_2) == config_digest(config) and config_2 == config
    # members in another order give the same policy and the same digest
    reordered = tmp_path / 'policy-reordered.json'
    reordered.write_text(json.dumps(dict(reversed(list(POLICY_JSON.items()))), indent=2))
    assert config_digest(policy_config(reordered)) == config_digest(config)
    # a repeated member name is refused, never read as its last value
    twice = tmp_path / 'policy-twice.json'
    twice.write_text('{"policy_version": "a", "policy_version": "b", "allowed_tools": [], "blocked_tools": []}')
    with pytest.raises(ValueError, match='Failed to parse policy config JSON'):
        policy_config(twice)
    # limit: a member the policy model does not know is dropped on load, so the round trip is stable only for known members
    extra = policy_file(tmp_path, 'policy-extra.json', {**POLICY_JSON, 'unmodelled_member': 'x'})
    kept = canon(policy_config(extra).model_dump(mode='json'))
    assert kept == stored and kept != extra.read_bytes()
    # a policy with a missing required member is refused
    missing = policy_file(tmp_path, 'policy-missing.json', {'allowed_tools': []})
    with pytest.raises(ValueError, match='Invalid policy config'):
        policy_config(missing)


@wiki_case('TC-L05-028')
def test_wiki_l05_028_changed_rule_has_a_new_digest_and_changes_the_decision_only_after_a_signed_revision(tmp_path, monkeypatch):
    v1 = policy_config(policy_file(tmp_path, 'v1.json', POLICY_JSON))
    v2 = policy_config(policy_file(tmp_path, 'v2.json', {**POLICY_JSON, 'policy_version': 'refund-policy-2', 'allowed_tools': ['lookup_tool'],
                                                          'blocked_tools': ['export_tool', 'refund_tool']}))
    d1, d2 = config_digest(v1), config_digest(v2)
    assert d1 != d2
    assert gate_decision(v1, 'refund_tool').result == 'allow' and gate_decision(v2, 'refund_tool').result == 'block'
    # the bounded decision path pins the policy by digest: the digest of the stored configuration is what the resolver reports
    p, r, f = rule_flow(tmp_path / 'flow', monkeypatch)
    ba = _tb()
    r.policies[ba.POLICY_REF].digest = d1
    _rr().append_rule_revision(f.records, f.rule_revision_profile, revision('r1', d1))
    first = decide(f, p)
    assert first.result == 'authorized' and rule_of(first)['state'] == 'adopted' and rule_of(first)['digest'] == d1
    r.policies[ba.POLICY_REF].digest = d2  # the changed rule is in force at the resolver, no revision row yet
    unsigned = decide(f, p)
    assert unsigned.result == 'hold' and 'policy_status_unknown' in unsigned.reasons
    assert rule_of(unsigned)['digest'] == d2 and 'digest_mismatch_with_adopted' in rule_of(unsigned)['findings'] and adopted(f) == d1
    _rr().append_rule_revision(f.records, f.rule_revision_profile, revision('r2', d2, d1))
    signed = decide(f, p)
    assert signed.result == 'authorized' and rule_of(signed)['state'] == 'adopted' and rule_of(signed)['digest'] == d2
    assert [x.result for x in (first, unsigned, signed)] == ['authorized', 'hold', 'authorized']


@wiki_case('TC-L05-028')
def test_wiki_l05_028_revision_rows_list_prior_and_current_digest_in_order(tmp_path, monkeypatch):
    p, r, f = rule_flow(tmp_path, monkeypatch)
    adopt(f, 'r1', 'v1')
    adopt(f, 'r2', 'v2', 'v1')
    adopt(f, 'r3', 'v3', 'v2')
    listed = rows(f)
    assert [x['revision_id'] for x in listed] == ['r1', 'r2', 'r3']
    assert [(x['from_digest'], x['to_digest']) for x in listed] == [(None, digest_of('v1')), (digest_of('v1'), digest_of('v2')),
                                                                    (digest_of('v2'), digest_of('v3'))]
    assert all(listed[i]['from_digest'] == listed[i - 1]['to_digest'] for i in (1, 2))  # each row names the prior digest
    assert [x['signer'] for x in listed] == [SIGNER] * 3 and all(x['reviser'] != x['signer'] for x in listed)
    assert [x['recorded_at'] for x in listed] == sorted(x['recorded_at'] for x in listed)
    # a row that does not follow from the adopted digest is refused and retained as a refusal, not as a row
    with pytest.raises(_rr().RuleRevisionRefused) as refused:
        adopt(f, 'r4', 'v4', 'v1')
    assert 'rule_revision_from_digest_mismatch' in refused.value.reasons
    doc = f.records.load()
    assert [x.revision_id for x in doc.rule_revisions] == ['r1', 'r2', 'r3'] and len(doc.rule_revision_refusals) == 1
    assert doc.rule_revision_refusals[0].revision['revision_id'] == 'r4'
    observe(r, 'v3')
    d = decide(f, p)
    assert d.result == 'authorized' and adopted(f) == digest_of('v3') == rule_of(d)['digest']


# ================================================================================================ TC-L08-036
@wiki_case('TC-L08-036')
def test_wiki_l08_036_rule_change_from_allow_to_block_applies_at_the_next_decision(tmp_path, monkeypatch):
    path = policy_file(tmp_path, 'live.json', POLICY_JSON)
    first = gate_decision(policy_config(path), 'refund_tool')
    assert first.result == 'allow'
    path.write_bytes(canon({**POLICY_JSON, 'policy_version': 'refund-policy-2', 'allowed_tools': ['lookup_tool'],
                            'blocked_tools': ['export_tool', 'refund_tool']}))  # the stored rule changes; nothing is restarted
    second = gate_decision(policy_config(path), 'refund_tool')
    assert second.result == 'block' and second.policy_name == 'blocked_tool_policy'
    assert second.deterministic_fingerprint != first.deterministic_fingerprint and second.decision_id != first.decision_id
    assert gate_decision(policy_config(path), 'lookup_tool').result == 'allow'  # the rest of the policy is unchanged
    # bounded decision path: a policy retired at the resolver applies at the very next decision and nothing reaches the destination
    p, r, f = rule_flow(tmp_path / 'flow', monkeypatch)
    adopt(f, 'r1', 'v1')
    assert decide(f, p).result == 'authorized'
    r.policies[_tb().POLICY_REF].status = 'superseded'
    held = decide(f, p)
    assert held.result == 'hold' and 'policy_superseded' in held.reasons and held.binding is None
    assert f.destination.snapshot()['effects'] == {}


@wiki_case('TC-L08-036')
def test_wiki_l08_036_rollback_by_a_new_signed_revision_restores_prior_behaviour(tmp_path, monkeypatch):
    p, r, f = rule_flow(tmp_path, monkeypatch)
    adopt(f, 'r1', 'v1')
    a = decide(f, p)
    observe(r, 'v2')
    assert decide(f, p).result == 'hold'  # v2 is not adopted yet
    adopt(f, 'r2', 'v2', 'v1')
    b = decide(f, p)
    assert b.result == 'authorized' and rule_of(b)['digest'] == digest_of('v2')
    before = rows(f)
    adopt(f, 'r3', 'v1', 'v2')  # rollback: a new signed revision back to the first digest
    observe(r, 'v1')
    c = decide(f, p)
    assert (a.result, a.reasons) == (c.result, c.reasons) == ('authorized', [])
    assert rule_of(a) == rule_of(c) and rule_of(c)['state'] == 'adopted' and rule_of(c)['digest'] == digest_of('v1')
    assert rows(f)[:2] == before and len(rows(f)) == 3  # nothing was edited: the rollback is a third row
    assert rows(f)[2]['from_digest'] == digest_of('v2') and rows(f)[2]['to_digest'] == digest_of('v1')
    # the same holds for a stored policy configuration: restoring the first content restores the first decision exactly
    v1 = policy_file(tmp_path, 'cfg.json', POLICY_JSON)
    first = gate_decision(policy_config(v1), 'refund_tool')
    v1.write_bytes(canon({**POLICY_JSON, 'allowed_tools': [], 'blocked_tools': ['refund_tool']}))
    assert gate_decision(policy_config(v1), 'refund_tool').result == 'block'
    v1.write_bytes(canon(POLICY_JSON))
    restored = gate_decision(policy_config(v1), 'refund_tool')
    assert (restored.result, restored.policy_name, restored.deterministic_fingerprint) == (first.result, first.policy_name, first.deterministic_fingerprint)


@wiki_case('TC-L08-036')
def test_wiki_l08_036_unsigned_or_self_signed_revision_is_refused_and_the_prior_policy_stays_in_force(tmp_path, monkeypatch):
    rr = _rr()
    p, r, f = rule_flow(tmp_path, monkeypatch)
    adopt(f, 'r1', 'v1')
    assert decide(f, p).result == 'authorized'
    # unsigned: retained, never counts
    adopt(f, 'r-unsigned', 'v2', 'v1', signer=None)
    # self-signed and a signer outside the configured set: refused and retained as refusals
    with pytest.raises(rr.RuleRevisionRefused) as self_signed:
        adopt(f, 'r-self', 'v2', 'v1', signer=REVISER)
    with pytest.raises(rr.RuleRevisionRefused) as outsider:
        adopt(f, 'r-outsider', 'v2', 'v1', signer='synthetic-principal:not-configured')
    assert 'self_signed_revision_row' in self_signed.value.reasons and 'signer_not_configured' in outsider.value.reasons
    doc = f.records.load()
    assert [x.revision_id for x in doc.rule_revisions] == ['r1', 'r-unsigned']
    assert [x.revision['revision_id'] for x in doc.rule_revision_refusals] == ['r-self', 'r-outsider']
    # the prior policy is still the adopted one: v1 passes, v2 holds
    d1 = decide(f, p)
    assert d1.result == 'authorized' and adopted(f) == digest_of('v1') == rule_of(d1)['digest']
    observe(r, 'v2')
    d2 = decide(f, p)
    assert d2.result == 'hold' and 'policy_status_unknown' in d2.reasons and adopted(f) == digest_of('v1')
    assert 'unsigned_revision_row' in rule_of(d2)['findings']
    assert f.destination.snapshot()['effects'] == {}
    # control: an independent configured signer is accepted and changes the outcome
    adopt(f, 'r2', 'v2', 'v1')
    assert decide(f, p).result == 'authorized'


@wiki_case('TC-L08-036')
def test_wiki_l08_036_change_record_lists_each_version_in_order(tmp_path, monkeypatch):
    p, r, f = rule_flow(tmp_path, monkeypatch)
    decisions = []
    adopt(f, 'r1', 'v1')
    decisions.append(decide(f, p))
    adopt(f, 'r2', 'v2', 'v1')
    observe(r, 'v2')
    decisions.append(decide(f, p))
    adopt(f, 'r3', 'v1', 'v2')
    observe(r, 'v1')
    decisions.append(decide(f, p))
    listed = rows(f)
    assert [x['revision_id'] for x in listed] == ['r1', 'r2', 'r3']
    assert [x['to_digest'] for x in listed] == [digest_of('v1'), digest_of('v2'), digest_of('v1')]
    assert [x['from_digest'] for x in listed] == [None, digest_of('v1'), digest_of('v2')]
    # the decision rows name the digest that was in force at each decision, in the same order
    stored = f.records.load().decisions
    assert [x.decision_id for x in stored] == [d.decision_id for d in decisions]
    assert [x.rule_identity['rules'][_tb().POLICY_REF]['digest'] for x in stored] == [digest_of('v1'), digest_of('v2'), digest_of('v1')]
    assert [x.result for x in stored] == ['authorized'] * 3


# ================================================================================================ TC-L16-007 and TC-L16-015
def accepted_revision():
    return _chain().CONTROL_PLANE_RUNTIME_AUTHORITY_REVISION


def floating_forms(revision):
    return {'zeros': '0' * 40, 'one_character_changed': revision[:-1] + ('0' if revision[-1] != '0' else '1'), 'abbreviated': revision[:12],
            'upper_case': revision.upper(), 'branch_name': 'main', 'head_name': 'HEAD', 'padded': revision + ' ', 'empty': ''}


@wiki_case('TC-L16-007')
@pytest.mark.parametrize('form', sorted(floating_forms('a' * 40)))
def test_wiki_l16_007_component_revision_outside_the_accepted_list_is_refused_by_the_importer(five, form):
    r = retained(five['valid'])
    revision = floating_forms(accepted_revision())[form]
    assert revision != accepted_revision()
    assert refusal_of(lambda: reconstruct(r.journal, r.proposal, r.executor_export, revision=revision)) == 'unsupported Control Plane revision'
    # the executor side: a producer repository revision outside the accepted set is refused as well
    export = copy.deepcopy(r.executor_export)
    export['repository']['revision'] = revision or '0' * 40
    text = refusal_of(lambda: reconstruct(r.journal, r.proposal, export))
    assert text is not None and 'repository revision' in text, text
    # control: the accepted revision is not refused
    assert complete(reconstruct(r.journal, r.proposal, r.executor_export, revision=accepted_revision()))


@wiki_case('TC-L16-007')
def test_wiki_l16_007_same_label_different_content_artifact_is_refused_by_digest(five):
    r = retained(five['valid'])
    H2 = _h2()
    base = reconstruct(r.journal, r.proposal, r.executor_export)
    # executor export: version labels, producer profile and repository revision stay, the operation content changes
    labels = (r.executor_export['execution_envelope']['version'], r.executor_export['producer_profile'], r.executor_export['repository'])
    for path, value in (('target', 'urn:cognous:synthetic-account:customer-099'), ('amount', 51.0), ('payload_commitment', 'sha256:' + '2' * 64)):
        export = copy.deepcopy(r.executor_export)
        export['execution_envelope']['operation'][path] = value
        assert (export['execution_envelope']['version'], export['producer_profile'], export['repository']) == labels
        assert refusal_of(lambda: reconstruct(r.journal, r.proposal, export)) is not None, path
    # manifest: the label (identifier and version) stays, the content changes; the digest in the proposal no longer matches
    edited = copy.deepcopy(r.manifest)
    edited['tools'][0]['description'] = 'Same label, different content.'
    assert (edited['manifest_id'], edited['manifest_version']) == (r.manifest['manifest_id'], r.manifest['manifest_version'])
    out = H2.eval_pack_from_bundle(edited, base)
    assert out['verdict'] == 'rejected' and 'does not match supplied Manifest digest' in out['why']
    # control: the unchanged artifacts are accepted
    assert complete(base) and H2.eval_pack_from_bundle(r.manifest, base)['verdict'] == 'accepted'


@wiki_case('TC-L16-007')
def test_wiki_l16_007_pinned_revision_is_accepted_as_the_positive_control(five):
    r = retained(five['valid'])
    H2 = _h2()
    ref = H2.reference()
    bundle = reconstruct(r.journal, r.proposal, r.executor_export, revision=accepted_revision())
    assert complete(bundle) and bundle['metadata']['control_plane_revision'] == accepted_revision()
    stages = H2.evaluate_producer_exports(r.manifest, r.journal, r.proposal, r.executor_export)
    assert [s['verdict'] for s in stages] == ['accepted'] * 3
    assert ref.pins['control_plane']['commit'] == ref.profile['components']['control_plane']['revision']
    assert ref.pins['runtime']['commit'] == ref.profile['components']['runtime']['revision']


def altered(value, path, new):
    out = copy.deepcopy(value)
    node = out
    keys = path.strip('/').split('/')
    for k in keys[:-1]:
        node = node[int(k)] if isinstance(node, list) else node[k]
    last = int(keys[-1]) if isinstance(node, list) else keys[-1]
    node[last] = new
    return out


def bundle_digest(bundle):
    """The content digest the Replay component computes for a reconstruction bundle (integrity members excluded)."""
    _h()
    replay = importlib.import_module('agent_replay_bundle')
    return replay.content_digest(replay.ReconstructionBundle.model_validate(bundle)).value


def set_member(value, path, new):
    """A copy of ``value`` with the member at the slash path replaced (list positions are numbers)."""
    out = copy.deepcopy(value)
    node = out
    keys = path.strip('/').split('/')
    for k in keys[:-1]:
        node = node[int(k)] if isinstance(node, list) else node[k]
    node[int(keys[-1]) if isinstance(node, list) else keys[-1]] = new
    return out


def record_member(bundle, kind, path, new):
    """A copy of the bundle with a member inside the data of the first record of ``kind`` replaced."""
    out = copy.deepcopy(bundle)
    record = records_of(out, kind)[0]
    record['data'] = set_member(record['data'], path, new)
    return out


EXPORT_PATHS = {'envelope_amount': ('/execution_envelope/operation/amount', 51.0), 'effect_amount': ('/effects/0/amount', 51.0),
                'effect_target': ('/effects/0/target', 'urn:cognous:synthetic-account:customer-099')}
BUNDLE_PATHS = {'decision_amount': ('runtime_decision', 'binding/amount', 51.0), 'effect_amount': ('destination_effect', 'amount', 51.0),
                'result_status': ('execution_result', 'status', 'failed')}


# ================================================================================================ TC-L16-015
@wiki_case('TC-L16-015')
@pytest.mark.parametrize('artifact', ['executor_export', 'evidence_pack', 'bundle'])
def test_wiki_l16_015_tampered_artifact_with_an_unchanged_version_label_is_refused_by_digest(five, artifact):
    r = retained(five['valid'])
    H2 = _h2()
    base = reconstruct(r.journal, r.proposal, r.executor_export)
    if artifact == 'executor_export':
        labels = (r.executor_export['execution_envelope']['version'], r.executor_export['producer_profile'], r.executor_export['repository'])
        for name, (path, value) in EXPORT_PATHS.items():
            export = set_member(r.executor_export, path, value)
            assert (export['execution_envelope']['version'], export['producer_profile'], export['repository']) == labels, name
            assert refusal_of(lambda: reconstruct(r.journal, r.proposal, export)) is not None, name
    elif artifact == 'evidence_pack':
        assert H2.eval_pack_artifact(r.pack)['verdict'] == 'accepted'  # control
        for name, (kind, path, value) in BUNDLE_PATHS.items():
            pack = copy.deepcopy(r.pack)
            inner = pack['metadata']['traceable_import']['retained_sources']['reconstruction_bundle']
            pack['metadata']['traceable_import']['retained_sources']['reconstruction_bundle'] = record_member(inner, kind, path, value)
            assert pack['pack_version'] == r.pack['pack_version'] and pack['pack_id'] == r.pack['pack_id'], name
            assert H2.eval_pack_artifact(pack)['verdict'] != 'accepted', name
        count = set_member(r.pack, 'metadata/traceable_import/derived_counts/decision_count', 9)
        assert H2.eval_pack_artifact(count)['verdict'] != 'accepted'
    else:
        stored = bundle_digest(base)
        for name, (kind, path, value) in BUNDLE_PATHS.items():
            tampered = record_member(base, kind, path, value)
            assert (tampered['bundle_version'], tampered['bundle_id']) == (base['bundle_version'], base['bundle_id']), name  # same label
            assert bundle_digest(tampered) != stored, name  # the recorded digest no longer matches
            stages = H2.evaluate_bundle(r.manifest, tampered)
            assert [s['verdict'] for s in stages] == ['rejected', 'rejected'], (name, stages)  # the consumers refuse it as well
        assert bundle_digest(copy.deepcopy(base)) == stored  # control: an identical copy has the same digest


def mini_repos(root, names):
    """One tiny local git repository per component name, each with one commit; returns {name: head sha}. No network is used."""
    git_id = ['-c', 'user.name=wp-f', '-c', 'user.email=wp-f@example.invalid', '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null']
    heads = {}
    for name in names:
        path = root / name
        path.mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', str(path)], check=True, timeout=60)
        (path / 'file.txt').write_text(name + '\n')
        subprocess.run(['git', '-C', str(path), 'add', 'file.txt'], check=True, timeout=60)
        subprocess.run(['git', '-C', str(path), *git_id, 'commit', '-q', '-m', 'one'], check=True, timeout=60)
        subprocess.run(['git', '-C', str(path), 'tag', 'v1'], check=True, timeout=60)
        heads[name] = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True, timeout=60).strip()
    return heads


def run_selection(tmp_path, tag, revisions, heads_root):
    """Run a byte-identical copy of the qualification runner against local components whose pinned revisions are ``revisions``.
    The profile sits in a throw-away tree because the runner reads only profiles inside its own tree."""
    tree = tmp_path / f'tree-{tag}'
    (tree / 'tools').mkdir(parents=True)
    (tree / 'process').mkdir()
    runner = tree / 'tools/run_security_runtime.py'
    shutil.copyfile(ROOT / 'tools/run_security_runtime.py', runner)
    assert file_digest(runner) == file_digest(ROOT / 'tools/run_security_runtime.py')
    profile = {'components': {n: {'repository': f'cogno-us/synthetic-{n}', 'revision': rev} for n, rev in revisions.items()},
               'selected': False, 'reference_release_authorized': False, 'production_deployment_authorized': False, 'phase': 'full'}
    (tree / 'process/profile.json').write_text(json.dumps(profile))
    out = tree / 'out'
    proc = subprocess.run([sys.executable, '-I', str(runner), '--profile', 'process/profile.json', '--components', str(heads_root), '--out', str(out)],
                          cwd=str(tree), env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), capture_output=True, text=True, timeout=120)
    return proc, out


@wiki_case('TC-L16-015')
def test_wiki_l16_015_floating_unpinned_component_selection_is_refused_by_the_component_lock_check(tmp_path):
    names = ('control_plane', 'runtime', 'replay', 'evidence_pack', 'odes', 'exchange', 'manifest')
    heads = mini_repos(tmp_path / 'components', names)
    # control: every component pinned to its exact revision passes the check (the run then starts and stops for lack of a suite)
    proc, out = run_selection(tmp_path, 'exact', dict(heads), tmp_path / 'components')
    assert 'Dirty or mismatched source' not in proc.stderr and out.exists()
    # a floating selection of one component (branch, tag, HEAD, abbreviated or upper-case revision) is refused before anything runs
    head = heads['manifest']
    floating = {'branch': 'main', 'tag': 'v1', 'head': 'HEAD', 'abbreviated': head[:12], 'upper_case': head.upper(), 'empty': ''}
    for tag, selector in floating.items():
        proc, out = run_selection(tmp_path, tag, {**heads, 'manifest': selector}, tmp_path / 'components')
        assert proc.returncode != 0, tag
        assert 'Dirty or mismatched source: manifest' in proc.stderr, (tag, proc.stderr[-300:])
        assert not out.exists(), tag
    # the pin resolution of the harness refuses evidence pins that match no frozen generation, a floating pin included
    spec = importlib.util.spec_from_file_location('wp_f_pins', ROOT / 'suites/_pins.py')
    pins = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pins)
    label, index = pins.classify_generation([pins.PROFILE_PINS], pins.GENERATIONS)
    assert label is not None and index is not None  # the pinned set classifies as one frozen generation
    for selector in ('main', 'HEAD', pins.PROFILE_PINS['runtime'][:12]):
        with pytest.raises(pins.RefreezeError, match='match no frozen generation'):
            pins.classify_generation([{**pins.PROFILE_PINS, 'runtime': selector}], pins.GENERATIONS)


@wiki_case('TC-L16-015')
def test_wiki_l16_015_pinned_artifact_is_accepted_as_the_positive_control(five):
    r = retained(five['valid'])
    H2 = _h2()
    ref = H2.reference()
    bundle = reconstruct(r.journal, r.proposal, r.executor_export)
    assert complete(bundle)
    assert [s['verdict'] for s in H2.evaluate_producer_exports(r.manifest, r.journal, r.proposal, r.executor_export)] == ['accepted'] * 3
    assert [s['verdict'] for s in H2.evaluate_bundle(r.manifest, bundle)] == ['accepted'] * 2
    assert H2.eval_pack_artifact(r.pack)['verdict'] == 'accepted' and H2.eval_odes_package(r.odes)['verdict'] == 'accepted'
    assert bundle_digest(bundle) == bundle_digest(copy.deepcopy(bundle))
    for name, pin in ref.pins.items():  # the checkouts that produced these artifacts are the pinned revisions and nothing extra
        assert H2.require_pristine(ref.paths[name], pin['commit'], name) == pin['commit']


# ================================================================================================ runs for TC-L17-020
RUNS = 3
CALLS_PER_RUN = 3  # two effects and one refused action


def _with_budget(n):
    """flow_a_pre mutation: effect budget ``n`` (manifest, requirement and grant agree)."""
    ch = _chain()

    def mutate(p, r, f, dest):
        f.manifest['actions'][0]['effect_limits']['max_effects'] = n
        p = p.model_copy(update={'manifest_digest': ch.commitment(f.manifest)})
        ctx = r.contexts[ch.PROFILE]
        ctx['requirement']['permissions'][0]['max_effects'] = n
        ctx['grant']['permissions'][0]['max_effects'] = n
        _rebind(r, p)
        ch.bind_approval(r, f.runtime_authority_profile)
        return p
    return mutate


def _rebind(r, proposal):
    """Independent approval of ``proposal`` (the approval is bound to the proposal commitment)."""
    ch = _chain()
    ref = r.contexts[ch.PROFILE]['grant']['approval_refs'][0]
    r.approvals[ref] = r.approvals[ref].model_copy(update={'proposal_commitment': ch.commitment(proposal.model_dump(mode='json', exclude_none=False))})


class Run:
    """One run on route A: its own record store and destination; each call is decided and executed on its own."""

    def __init__(self, work, label, mp, budget=3):
        self.ch, self.label = _chain(), label
        self.flow = _c2a().flow_a_pre(work, mp, _with_budget(budget))
        self.executor, self.env = _c2a().best_effort_executor(self.flow)
        self.executor.policy = dataclasses.replace(self.executor.policy, max_effects=budget)
        self.calls = []

    def request(self, i):
        if i == 0:
            return self.flow.p, self.flow.d, self.env
        p = self.flow.p.model_copy(update={'correlation_id': f'wp-f-{self.label}-call-{i}'})
        _rebind(self.flow.r, p)
        d = self.flow.f.decide(p, now=self.ch.NOW)
        op = dataclasses.replace(self.env.operation, proposal_commitment=self.ch.commitment(p.model_dump(mode='json')))
        return p, d, dataclasses.replace(self.env, decision_id=d.decision_id, effect_id=d.effect_id, operation=op)

    def execute(self, request):
        p, d, env = request
        res = self.executor.execute(envelope=env, proposal=p, decision=d, now=self.ch.NOW)
        self.calls.append((p, d, env, res))
        return res


def slice_journal(journal, decision):
    """The rows of one proposal from a record store that holds several: the importer reconstructs one proposal at a time. Journal
    and resolution-check identifiers are separate producer identifiers, so the checks are taken by completion order."""
    commitment = decision['operation_horizon']['proposal_commitment']
    out = copy.deepcopy(journal)
    out['decisions'] = [d for d in journal['decisions'] if d['decision_id'] == decision['decision_id']]
    for member in ('attempts', 'observations', 'reconciliations', 'refusals'):
        out[member] = [x for x in journal[member] if x.get('effect_id') == decision['effect_id']]
    out['check_events'] = [e for e in journal['check_events'] if e['proposal_commitment'] == commitment]
    checks, rank = [], 0
    for event in journal['check_events']:
        if event['phase'] == 'completed':
            if event['proposal_commitment'] == commitment:
                checks.append(journal['resolution_checks'][rank])
            rank += 1
    out['resolution_checks'] = checks
    return out


@pytest.fixture(scope='module')
def three_runs(pinned_reference, tmp_path_factory):
    """Three runs of two executed effects and one refused action each, exported and reconstructed one action at a time."""
    ch = _chain()
    root = tmp_path_factory.mktemp('wp-f-runs')
    mp = pytest.MonkeyPatch()
    runs = []
    try:
        for k in range(RUNS):
            work = root / f'run-{k}'
            work.mkdir()
            run = Run(work, f'run{k}', mp)
            for i in (0, 1):
                assert run.execute(run.request(i)).status == 'executed'
            stale = run.request(2)  # decided while the grant is active
            next(iter(run.flow.r.statuses.values())).status = 'revoked'  # the resolver revokes it before the third effect
            assert run.execute(stale).status == 'denied'
            journal = run.flow.f.records.load().model_dump(mode='json')
            actions = []
            for p, d, env, res in run.calls:
                decision = next(x for x in journal['decisions'] if x['decision_id'] == d.decision_id)
                export = ch.export_execution_artifacts(env, res, run.flow.dest, repository_revision=ch.MOLTBOT_RUNTIME_AUTHORITY_REVISION)
                proposal = p.model_dump(mode='json')
                sliced = slice_journal(journal, decision)
                actions.append(SimpleNamespace(proposal=proposal, decision=decision, export=export, journal=sliced,
                                               bundle=reconstruct(sliced, proposal, export), status=res.status))
            runs.append(SimpleNamespace(run=run, journal=journal, actions=actions, effects=W.destination_summary(run.flow)['effects']))
        yield runs
    finally:
        mp.undo()


# ================================================================================================ TC-L17-020
@wiki_case('TC-L17-020')
def test_wiki_l17_020_three_runs_with_two_effects_and_one_refused_action_each_reconstruct_completely_and_in_order(three_runs):
    assert len(three_runs) == RUNS
    for k, run in enumerate(three_runs):
        assert [a.status for a in run.actions] == ['executed', 'executed', 'denied']
        # the retained record store holds the three actions in the order they were taken
        decisions = run.journal['decisions']
        assert [d['decision_id'] for d in decisions] == [a.decision['decision_id'] for a in run.actions]
        effect_ids = [a.decision['effect_id'] for a in run.actions]
        assert len(set(effect_ids)) == 3
        assert [x['effect_id'] for x in run.journal['attempts']] == [effect_ids[0]] * 2 + [effect_ids[1]] * 2
        assert [x['effect_id'] for x in run.journal['refusals']] == [effect_ids[2]]
        assert sorted(e['effect_id'] for e in run.effects) == sorted(effect_ids[:2])  # the destination itself holds exactly the two effects
        for i, action in enumerate(run.actions):
            b = action.bundle
            assert complete(b), (k, i)
            assert [r['source_sequence'] for r in b['records']] == list(range(len(b['records'])))  # sequence is the order of the records
            assert kinds(b)[:2] == ['runtime_proposal', 'runtime_decision']
            assert records_of(b, 'runtime_decision')[0]['data'] == action.decision
            if i < 2:
                assert records_of(b, 'execution_result')[0]['data']['status'] == 'executed'
                assert len(records_of(b, 'destination_effect')) == 1 and len(records_of(b, 'control_plane_attempt_transition')) == 2
                assert [r['data'] for r in records_of(b, 'control_plane_attempt_transition')] == [x for x in run.journal['attempts'] if x['effect_id'] == effect_ids[i]]
                assert records_of(b, 'destination_effect')[0]['data']['effect_id'] == effect_ids[i]
            else:
                assert records_of(b, 'execution_result')[0]['data']['status'] == 'denied'
                refusal = records_of(b, 'effect_time_refusal')
                assert len(refusal) == 1 and refusal[0]['data'] == run.journal['refusals'][0] and refusal[0]['data']['reasons'] == ['grant_revoked']
                assert records_of(b, 'destination_effect') == [] and records_of(b, 'control_plane_attempt_transition') == []
    # limit: the record store of a run is refused as a whole, because a reconstruction covers one proposal
    run = three_runs[0]
    text = refusal_of(lambda: reconstruct(run.journal, run.actions[0].proposal, run.actions[0].export))
    assert text is not None and 'conflicts with committed operation' in text


@wiki_case('TC-L17-020')
def test_wiki_l17_020_reconstruction_carries_manifest_policy_and_grant_versions_and_decisions(three_runs):
    ba = _tb()
    for run in three_runs:
        for i, action in enumerate(run.actions):
            b = action.bundle
            proposal = records_of(b, 'runtime_proposal')[0]['data']
            decision = records_of(b, 'runtime_decision')[0]['data']
            binding = decision['binding']
            assert decision['result'] == 'authorized' and decision['reasons'] == []
            assert (proposal['manifest_id'], proposal['manifest_version'], proposal['manifest_digest']) == \
                (binding['manifest_id'], binding['manifest_version'], binding['manifest_digest'])
            assert binding['manifest_version'] == '1.1'
            assert binding['policy_versions'] == [{'ref': ba.POLICY_REF, 'version': ba.POLICY_VERSION}]
            assert (binding['grant_id'], binding['grant_revision']) == (run.run.flow.d.binding.grant_id, run.run.flow.d.binding.grant_revision)
            assert binding['role_mapping_version'] == 'roles-v1' and binding['effective_max_effects'] == 3
            # the inputs the decision read are retained with their types
            checks = records_of(b, 'resolution_check')
            assert checks and {'manifest', 'policy', 'grant', 'approval'} <= {x['input_type'] for c in checks for x in c['data']['inputs']}
            if i == 2:  # the refused action keeps the decision that authorized it and a refusal that names the grant and the reason
                refusal = records_of(b, 'effect_time_refusal')[0]['data']
                assert refusal['stage'] == 'effect_time_revalidation' and refusal['reasons'] == ['grant_revoked']
                assert refusal['decision_id'] == decision['decision_id'] and refusal['effect_id'] == decision['effect_id']
                assert {'grant', 'policy', 'manifest'} <= {x['input_type'] for x in refusal['resolution_inputs']}


@wiki_case('TC-L17-020')
def test_wiki_l17_020_exported_bundle_digest_verifies_and_an_altered_copy_fails(three_runs, tmp_path):
    H2 = _h2()
    replay = importlib.import_module('agent_replay_bundle')
    manifest = three_runs[0].run.flow.f.manifest
    for k, run in enumerate(three_runs):
        for i, action in enumerate(run.actions):
            bundle = copy.deepcopy(action.bundle)
            bundle['integrity'] = [replay.content_digest(replay.ReconstructionBundle.model_validate(bundle)).model_dump(mode='json')]
            path = tmp_path / f'export-{k}-{i}.json'  # the exported file, read back
            path.write_text(json.dumps(bundle, indent=2, sort_keys=True))
            exported = json.loads(path.read_text())
            stored = exported['integrity'][0]
            assert stored['kind'] == 'content-digest' and stored['subject_bundle_id'] == exported['bundle_id']
            assert bundle_digest(exported) == stored['value']  # the digest verifies
            kind, member, value = ('runtime_decision', 'binding/amount', 51.0) if i < 2 else ('runtime_decision', 'binding/target', 'urn:x')
            altered = record_member(exported, kind, member, value)
            assert altered['integrity'] == exported['integrity'] and altered['bundle_id'] == exported['bundle_id']
            assert bundle_digest(altered) != stored['value']  # the altered copy fails
            assert bundle_digest(set_member(exported, 'run_id', 'run-other')) != stored['value']
            assert [s['verdict'] for s in H2.evaluate_bundle(manifest, exported)] == ['accepted'] * 2
            assert [s['verdict'] for s in H2.evaluate_bundle(manifest, altered)] == ['rejected'] * 2
    # the package that carries the bundle fails its own content digest when a member is altered after export
    from odes import export_cognous_stack_package
    package = export_cognous_stack_package(manifest, three_runs[0].actions[0].bundle)
    assert H2.eval_odes_package(package)['verdict'] == 'accepted'
    edited = set_member(package, 'provenance/retained_sources/reconstruction_bundle/run_id', 'run-other')
    assert H2.eval_odes_package(edited)['verdict'] != 'accepted'


@wiki_case('TC-L17-020')
def test_wiki_l17_020_conversation_turns_are_absent_and_declared_absent(three_runs):
    H2 = _h2()
    ref = H2.reference()
    from odes import export_cognous_stack_package
    manifest = three_runs[0].run.flow.f.manifest
    for run in three_runs:
        assert unrecorded_hits(run.journal) == []
        for action in run.actions:
            b = action.bundle
            assert unrecorded_hits(b['records']) == [] and unrecorded_hits(action.export) == []
            assert not any('model' in k.lower() for _, k, _ in walk(b['records']) if k)
            sem = b['semantics']
            assert (sem['record_reconstruction'], sem['model_reexecution'], sem['policy_reevaluation'], sem['external_effect_execution']) == (True, False, False, False)
            assert 'reconstructs recorded events only' in sem['notes']
    package = export_cognous_stack_package(manifest, three_runs[0].actions[0].bundle)
    machine = package['record']['machine_role']
    assert (machine['model_id'], machine['model_version']) == ('unavailable', 'unavailable')
    assert any('renews no authorization' in line for line in package['provenance']['limits'])
    # the statement that no model is rerun and no conversation is recorded is in the component's own documentation
    doc = (ref.paths['replay'] / 'docs/reconstruction_import.md').read_text(encoding='utf-8')
    assert 'does **not**' in doc and 'rerun a model' in doc and 'reevaluate policy' in doc


# ================================================================================================ TC-L17-022
REFUND_ADAPTER = 'urn:cognous:adapter:synthetic-refund-v1'
PRINCIPALS = ('urn:cognous:principal:timeline-a', 'urn:cognous:principal:timeline-b')
ACTORS = ('urn:cognous:identity:timeline-agent-1', 'urn:cognous:identity:timeline-agent-2', 'urn:cognous:identity:timeline-agent-3')
ADAPTERS = ('urn:cognous:adapter:timeline-1', 'urn:cognous:adapter:timeline-2', 'urn:cognous:adapter:timeline-3', 'urn:cognous:adapter:timeline-4')
TIMELINE_RUNS = ((0, 0, 0), (0, 1, 1), (1, 2, 2), (1, 0, 3))  # (principal, actor, adapter): every value is used, each run applies one effect
LIFECYCLE = {'runtime_decision': 1, 'control_plane_attempt_transition': 2, 'effect_observation': 2, 'reconciliation': 2,
             'destination_attempt_event': 2, 'destination_effect': 1}  # ten recorded events per applied effect


def with_identity(mp, principal, actor, adapter):
    """The control-plane fixtures with another principal, acting identity and adapter (the declared manifest and the proposal agree)."""
    tb, ra = _tb(), _tr()
    original_manifest, original_proposal = tb.manifest, tb.proposal
    mp.setattr(tb, 'PRINCIPAL', principal)
    mp.setattr(tb, 'ACTOR', actor)

    def manifest():
        return json.loads(json.dumps(original_manifest()).replace(REFUND_ADAPTER, adapter))

    def proposal(*a, **k):
        return original_proposal(*a, **k).model_copy(update={'adapter_id': adapter})
    for module in (tb, ra):
        mp.setattr(module, 'manifest', manifest)
        mp.setattr(module, 'proposal', proposal)


def source_row(path, journal, export):
    """The retained row a record's ``source_path`` names (``decisions[0]``, ``moltbot.effects[0]``, ...)."""
    import re
    m = re.fullmatch(r'(moltbot\.)?(\w+)\[(\d+)\]', path)
    assert m, path
    return (export if m.group(1) else journal)[m.group(2)][int(m.group(3))]


@pytest.fixture(scope='module')
def timeline(pinned_reference, tmp_path_factory):
    """Four runs, each with its own principal, acting identity and adapter, each applying one effect; every run is exported."""
    root = tmp_path_factory.mktemp('wp-f-timeline')
    ch = _chain()
    runs = []
    for n, (pi, ai, di) in enumerate(TIMELINE_RUNS):
        mp = pytest.MonkeyPatch()
        try:
            with_identity(mp, PRINCIPALS[pi], ACTORS[ai], ADAPTERS[di])
            p, r, f, d, dest, result, export, bundle = ch.produce(root / f'run-{n}', mp, 'valid')
            assert result.status == 'executed' and d.binding.principal == PRINCIPALS[pi] and d.binding.adapter_id == ADAPTERS[di]
            journal = f.records.load().model_dump(mode='json')
            proposal = p.model_dump(mode='json')
            runs.append(SimpleNamespace(n=n, identity=(PRINCIPALS[pi], ACTORS[ai], ADAPTERS[di]), journal=journal, proposal=proposal, export=export,
                                        effect_ids={'decision_id': d.decision_id, 'effect_id': d.effect_id}, bundle=reconstruct(journal, proposal, export)))
        finally:
            mp.undo()
    return runs


def events_of(bundle):
    return [r for r in bundle['records'] if r['record_type'] in LIFECYCLE]


@wiki_case('TC-L17-022')
def test_wiki_l17_022_forty_events_from_two_principals_three_actors_and_four_adapters_keep_order_and_identifiers(timeline):
    corpus = []
    for run in timeline:
        events = events_of(run.bundle)
        assert complete(run.bundle)
        counts = {k: sum(1 for e in events if e['record_type'] == k) for k in LIFECYCLE}
        assert counts == LIFECYCLE and len(events) == 10, (run.n, counts)
        assert [e['source_sequence'] for e in events] == sorted(e['source_sequence'] for e in events)  # order is the record sequence
        assert len({e['record_id'] for e in events}) == 10
        for e in events:
            row = source_row(e['source_path'], run.journal, run.export)
            if e['record_type'] != 'effect_observation':
                assert e['data'] == row, (run.n, e['source_path'])
            for key in ('decision_id', 'effect_id', 'attempt_id'):
                if key in row:  # an identifier the retained row carries is kept as it was; the others are lineage added by the importer
                    assert e['identifiers'][key] == row[key], (run.n, e['source_path'], key)
                else:
                    assert e['identifiers'].get(key) in (None, run.effect_ids.get(key)), (run.n, e['source_path'], key)
            corpus.append((run.n, e))
        binding = events[0]['data']['binding']
        assert (binding['principal'], binding['actor'], binding['adapter_id']) == run.identity  # identities as recorded
    assert len(corpus) == 40
    assert len({(n, e['record_id']) for n, e in corpus}) == 40  # no event is lost or repeated across the corpus
    assert [(n, e['source_sequence']) for n, e in corpus] == sorted((n, e['source_sequence']) for n, e in corpus)
    decisions = [e['data']['binding'] for _, e in corpus if e['record_type'] == 'runtime_decision']
    assert len({b['principal'] for b in decisions}) == 2 and len({b['actor'] for b in decisions}) == 3 and len({b['adapter_id'] for b in decisions}) == 4
    assert len({e['identifiers']['effect_id'] for _, e in corpus if 'effect_id' in e['identifiers']}) == 4


DUPLICATES = {  # name: (edit of the journal and the executor export, text of the typed refusal)
    'journal_decision_repeated': (lambda j, e: j['decisions'].append(copy.deepcopy(j['decisions'][0])), 'multiple authorization bindings'),
    'journal_attempt_repeated': (lambda j, e: j['attempts'].append(copy.deepcopy(j['attempts'][0])), 'lifecycle repeats a record'),
    'journal_check_opening_repeated': (lambda j, e: j['check_events'].append(copy.deepcopy(j['check_events'][0])), 'duplicate journal opening'),
    'journal_resolution_check_repeated': (lambda j, e: j['resolution_checks'].append(copy.deepcopy(j['resolution_checks'][0])), 'duplicate/empty resolution check id'),
    'executor_attempt_repeated': (lambda j, e: e['attempts'].append(copy.deepcopy(e['attempts'][0])), 'duplicate executor attempt row'),
    'executor_attempt_event_repeated': (lambda j, e: e['attempt_events'].append(copy.deepcopy(e['attempt_events'][0])), 'repeated or out of order'),
    'executor_effect_repeated': (lambda j, e: e['effects'].append(copy.deepcopy(e['effects'][0])), 'duplicate destination effect row'),
}
OUT_OF_SEQUENCE = {
    'journal_attempts_swapped': (lambda j, e: j['attempts'].reverse(), 'lacks its attempted start record'),
    'journal_check_events_swapped': (lambda j, e: j['check_events'].__setitem__(slice(0, 2), j['check_events'][1::-1]), 'missing opening or already closed'),
    'journal_resolution_checks_swapped': (lambda j, e: j['resolution_checks'].reverse(), 'out of journal order'),
    'executor_attempt_events_swapped': (lambda j, e: e['attempt_events'].reverse(), 'repeated or out of order'),
}


@wiki_case('TC-L17-022')
def test_wiki_l17_022_duplicate_event_is_detected_and_an_out_of_sequence_event_is_reported(timeline):
    run = timeline[0]
    assert complete(reconstruct(run.journal, run.proposal, run.export))  # control: the retained records reconstruct completely
    for table in (DUPLICATES, OUT_OF_SEQUENCE):
        for name, (edit, expected) in table.items():
            j, e = copy.deepcopy(run.journal), copy.deepcopy(run.export)
            edit(j, e)
            assert (j, e) != (run.journal, run.export), name
            text = refusal_of(lambda: reconstruct(j, run.proposal, e))
            assert text is not None and expected in text, (name, text)  # a typed refusal that names the defect, never a silent import
    # the same holds one layer up: a record repeated in a bundle is refused by the consumers
    H2 = _h2()
    repeated = copy.deepcopy(run.bundle)
    repeated['records'].append(copy.deepcopy(repeated['records'][0]))
    assert H2.eval_pack_from_bundle(timeline_manifest(run), repeated)['verdict'] == 'rejected'
    assert H2.eval_pack_from_bundle(timeline_manifest(run), run.bundle)['verdict'] == 'accepted'  # control


def timeline_manifest(run):
    """The declared manifest of a timeline run (its adapter is the one in the run's decision binding)."""
    tb = _tb()
    return json.loads(json.dumps(tb.manifest()).replace(REFUND_ADAPTER, run.identity[2]))


def shifted(text, minutes):
    return (datetime.fromisoformat(text) + timedelta(minutes=minutes)).isoformat()


@wiki_case('TC-L17-022')
def test_wiki_l17_022_timestamps_two_minutes_apart_do_not_reorder_events_ordered_by_sequence(timeline):
    run = timeline[0]
    base = run.bundle
    assert complete(base)
    # control-plane timestamps two minutes apart, forward and backward in turn: the events keep the order of the retained rows
    j = copy.deepcopy(run.journal)
    for i, event in enumerate(j['check_events']):
        event['recorded_at'] = shifted(event['recorded_at'], 2 if i % 2 else -2)
    skewed = reconstruct(j, run.proposal, run.export)
    assert complete(skewed) and kinds(skewed) == kinds(base)
    assert [r['record_id'] for r in skewed['records']] == [r['record_id'] for r in base['records']]
    assert [r['source_sequence'] for r in skewed['records']] == list(range(len(skewed['records'])))
    assert [r['data']['recorded_at'] for r in records_of(skewed, 'resolution_check_event')] != sorted(r['data']['recorded_at'] for r in records_of(skewed, 'resolution_check_event'))
    # a decision and its attempts stamped two minutes apart in either direction are not reordered either
    j = copy.deepcopy(run.journal)
    j['decisions'][0]['decided_at'] = shifted(j['decisions'][0]['decided_at'], 2)
    later = reconstruct(j, run.proposal, run.export)
    assert kinds(later) == kinds(base) and [r['record_id'] for r in later['records']] == [r['record_id'] for r in base['records']]
    # executor attempt events two minutes apart, in order: accepted, same order
    e = copy.deepcopy(run.export)
    for i, event in enumerate(e['attempt_events']):
        event['created_at'] = event['created_at'] + 120 * i
    spaced = reconstruct(run.journal, run.proposal, e)
    assert complete(spaced) and kinds(spaced) == kinds(base)
    assert [r['data']['event_id'] for r in records_of(spaced, 'destination_attempt_event')] == [x['event_id'] for x in e['attempt_events']]
    # executor attempt events whose clock runs backwards by two minutes: reported as out of order, not re-sorted
    e = copy.deepcopy(run.export)
    for i, event in enumerate(e['attempt_events']):
        event['created_at'] = event['created_at'] - 120 * i
    text = refusal_of(lambda: reconstruct(run.journal, run.proposal, e))
    assert text is not None and 'created_at is missing or out of order' in text
    # the sequence of the retained rows is what the reconstruction follows: the same rows in the same order give the same events
    again = reconstruct(run.journal, run.proposal, run.export)
    assert canon(stable(again)) == canon(stable(base))
