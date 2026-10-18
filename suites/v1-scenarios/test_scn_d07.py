"""SCN-D07 Restore boundary: restore authority state alone, then full destination state.

SPDX-License-Identifier: Apache-2.0

Required observation (catalog D07): show accepted replays or refusal under each restoration; distinguish local
persistence from an external anchor guarantee.

Two frozen profiles of the F5b reference are exercised, each in a fresh directory, each scenario executed twice under
unchanged conditions (owner decision D3) with the normalised outcomes compared:

* chain  - Control Plane + runtime + EffectiveGrantDestination (the supported F5b integration). Authority side =
           resolver statuses + Control Plane journal file; destination side = the whole SQLite store.
* c1     - the atomic claim profile the matched-refund job drives. Authority state (grants, approvals, policies, evidence,
           claims, budgets) and effect state share one SQLite file, so 'authority alone' is a table-granular restore.

An append-only witness OUTSIDE the restore set records every effect row that really appears (read-only diff, independent
of executor acknowledgements). It is a test observer: never consulted by admission and NOT an external anchor.

Assertions state what the reference actually does. Where a restore re-admits an effect after history was erased, the
test records that outcome as a LIMITATION (rollback resistance is not provided and not claimed) rather than a pass of
rollback safety; the evidence file carries ``external_anchor_guarantee: NOT PROVIDED`` for every case.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

import _d06_d07_d08_helpers as H
from _d06_d07_d08_helpers import pinned_reference  # noqa: F401

BOUNDARY = {'external_anchor_guarantee': 'NOT PROVIDED',
            'local_persistence': 'outcome depends on which local records survive the restore; the reference has no external restore anchor',
            'witness': 'test observer outside the restore set; never an admission input; not an anchor'}


def _step(world, label, result=None, c1=False):
    state = world.state() if c1 else {'effects': world.effects(), 'journal': world.journal_counts()}
    row = {'step': label, 'state': state, 'witness_commits': world.witness.commits()}
    if result is not None:
        row['result'] = result
    return row


# ---------------------------------------------------------------- chain scenarios (each returns the ordered steps)
def chain_authority_only_destination_revoked(w):
    a0 = w.authority_snapshot()
    w.revoke_resolver(); w.revoke_destination()
    steps = [_step(w, 'baseline_after_revocation', w.execute())]
    w.authority_restore(a0)
    steps.append(_step(w, 'replay_after_authority_only_restore', w.execute()))
    return steps


def chain_authority_only_resolver_only_revocation(w):
    a0 = w.authority_snapshot()
    w.revoke_resolver()
    steps = [_step(w, 'baseline_after_revocation', w.execute())]
    w.authority_restore(a0)
    steps.append(_step(w, 'replay_after_authority_only_restore', w.execute()))
    return steps


def chain_authority_only_after_consume(w):
    a0 = w.authority_snapshot()
    steps = [_step(w, 'first_execution', w.execute())]
    w.authority_restore(a0)
    steps.append(_step(w, 'replay_after_authority_only_restore', w.execute()))
    return steps


def chain_destination_full_authority_survives(w):
    d0 = w.destination_snapshot('d0.sqlite')
    w.revoke_resolver(); w.revoke_destination()
    steps = [_step(w, 'baseline_after_revocation', w.execute())]
    w.destination_restore(d0)
    steps.append(_step(w, 'replay_after_destination_full_restore', w.execute()))
    return steps


def chain_both_restored_before_revoke(w):
    a0, d0 = w.authority_snapshot(), w.destination_snapshot('d0.sqlite')
    w.revoke_resolver(); w.revoke_destination()
    steps = [_step(w, 'baseline_after_revocation', w.execute())]
    w.authority_restore(a0); w.destination_restore(d0)
    steps.append(_step(w, 'replay_after_both_restored', w.execute()))
    return steps


def chain_destination_only_before_consume_lost_ack(w):
    d0 = w.destination_snapshot('d0.sqlite')
    steps = [_step(w, 'first_execution_lost_ack', w.execute('lost_ack'))]
    w.destination_restore(d0)
    steps.append(_step(w, 'after_destination_full_restore'))
    steps.append(_step(w, 'replay_after_destination_full_restore', w.execute()))
    return steps


def chain_both_restored_before_consume_lost_ack(w):
    a0, d0 = w.authority_snapshot(), w.destination_snapshot('d0.sqlite')
    steps = [_step(w, 'first_execution_lost_ack', w.execute('lost_ack'))]
    w.destination_restore(d0); w.authority_restore(a0)
    steps.append(_step(w, 'after_both_restored'))
    steps.append(_step(w, 'replay_after_both_restored', w.execute()))
    return steps


def chain_destination_full_after_consume(w):
    steps = [_step(w, 'first_execution', w.execute())]
    d1 = w.destination_snapshot('d1.sqlite')
    steps.append(_step(w, 'duplicate_delivery', w.execute()))
    w.destination_restore(d1)
    steps.append(_step(w, 'replay_after_destination_full_restore', w.execute()))
    return steps


# ---------------------------------------------------------------- c1 scenarios
def c1_authority_tables_after_consume(w):
    s0 = w.snapshot('s0.sqlite')
    steps = [_step(w, 'first_execution', w.execute(), c1=True)]
    w.restore_tables(s0, H.C1_AUTHORITY_TABLES)
    steps.append(_step(w, 'replay_after_authority_tables_restore', w.execute(), c1=True))
    return steps


def c1_authority_tables_after_revoke(w):
    s0 = w.snapshot('s0.sqlite')
    w.revoke()
    steps = [_step(w, 'baseline_after_revocation', w.execute(), c1=True)]
    w.restore_tables(s0, H.C1_AUTHORITY_TABLES)
    steps.append(_step(w, 'replay_after_authority_tables_restore', w.execute(), c1=True))
    return steps


def c1_authority_tables_after_lost_ack(w):
    s0 = w.snapshot('s0.sqlite')
    steps = [_step(w, 'first_execution_lost_ack', w.execute('lost_ack'), c1=True)]
    w.restore_tables(s0, H.C1_AUTHORITY_TABLES)
    steps.append(_step(w, 'replay_after_authority_tables_restore', w.execute(), c1=True))
    return steps


def c1_full_before_consume(w):
    s0 = w.snapshot('s0.sqlite')
    steps = [_step(w, 'first_execution', w.execute(), c1=True)]
    w.restore_full(s0)
    steps.append(_step(w, 'after_full_restore', c1=True))
    steps.append(_step(w, 'replay_after_full_restore', w.execute(), c1=True))
    steps.append(_step(w, 'third_delivery', w.execute(), c1=True))
    return steps


def c1_full_after_consume(w):
    steps = [_step(w, 'first_execution', w.execute(), c1=True)]
    s1 = w.snapshot('s1.sqlite')
    w.restore_full(s1)
    steps.append(_step(w, 'replay_after_full_restore', w.execute(), c1=True))
    return steps


def c1_full_before_revoke(w):
    s0 = w.snapshot('s0.sqlite')
    w.revoke()
    steps = [_step(w, 'baseline_after_revocation', w.execute(), c1=True)]
    w.restore_full(s0)
    steps.append(_step(w, 'replay_after_full_restore', w.execute(), c1=True))
    return steps


def c1_destination_effect_tables_after_consume(w):
    s0 = w.snapshot('s0.sqlite')
    steps = [_step(w, 'first_execution', w.execute(), c1=True)]
    w.restore_tables(s0, H.C1_DESTINATION_TABLES)
    steps.append(_step(w, 'after_effect_tables_restore', c1=True))
    steps.append(_step(w, 'replay_after_effect_tables_restore', w.execute(), c1=True))
    return steps


# Uses of the word "anchor" in the reference code that are not a restore/anchor concept. Programme 2 (control plane 3cd17ead) added
# freshness.py, whose limits docstring says the deadline is "anchored" at the opening of the check (a time reference, not an external
# restore anchor and not an input to admission). Keyed by (path under the components directory, exact stripped line).
NON_RESTORE_ANCHOR_USES = {
    ('control_plane/src/agent_control_plane/freshness.py',
     '* The deadline is anchored at the opening of the check, not at the status\'s own timestamp. A status that was already close to the'),
}

# name: (kind, scenario, restored, remaining_external, expectation)
# expectation: replay step label, status, error substring, newly_executed, final effects, total witnessed commits
S = lambda **k: k
SCENARIOS = {
    'chain_authority_only_destination_revocation_holds': ('chain', chain_authority_only_destination_revoked,
        'resolver statuses + Control Plane journal', 'destination store (effective grant revoked, effects, failure records)',
        S(step='replay_after_authority_only_restore', status='failed', error='effective_grant_changed_at_commit', newly=False, effects=0, witness=0)),
    'chain_authority_only_resolver_only_revocation_reopens': ('chain', chain_authority_only_resolver_only_revocation,
        'resolver statuses + Control Plane journal', 'destination store (never told of the revocation)',
        S(step='replay_after_authority_only_restore', status='executed', error=None, newly=True, effects=1, witness=1)),
    'chain_authority_only_after_consume_reconciles': ('chain', chain_authority_only_after_consume,
        'resolver statuses + Control Plane journal (pre-execution)', 'destination store (effect committed)',
        S(step='replay_after_authority_only_restore', status='reconciled', error=None, newly=False, effects=1, witness=1)),
    'chain_destination_full_restore_authority_survives': ('chain', chain_destination_full_authority_survives,
        'complete destination store (effective grant active again)', 'resolver statuses + Control Plane journal (still revoked)',
        S(step='replay_after_destination_full_restore', status='denied', error='authorization-critical inputs changed before effect', newly=False, effects=0, witness=0)),
    'chain_both_restored_before_revoke_accepts': ('chain', chain_both_restored_before_revoke,
        'resolver statuses + journal AND complete destination store', 'nothing local; no external anchor exists',
        S(step='replay_after_both_restored', status='executed', error=None, newly=True, effects=1, witness=1)),
    'chain_destination_only_before_consume_lost_ack_journal_blocks': ('chain', chain_destination_only_before_consume_lost_ack,
        'complete destination store (pre-execution)', 'Control Plane journal (retains the unknown attempt)',
        S(step='replay_after_destination_full_restore', status='denied', error='observed absence does not establish retry eligibility', newly=False, effects=0, witness=1)),
    'chain_both_restored_before_consume_lost_ack_accepts_replay': ('chain', chain_both_restored_before_consume_lost_ack,
        'resolver statuses + journal AND complete destination store (pre-execution)', 'nothing local; no external anchor exists',
        S(step='replay_after_both_restored', status='executed', error=None, newly=True, effects=1, witness=2)),
    'chain_destination_full_restore_after_consume_reconciles': ('chain', chain_destination_full_after_consume,
        'complete destination store (post-commit)', 'Control Plane journal',
        S(step='replay_after_destination_full_restore', status='reconciled', error=None, newly=False, effects=1, witness=1)),
    # Programme 2 (runtime 11de097c): the executor records the exception CLASS only in attempt events, so the refusal by effect
    # uniqueness now reads exactly 'IntegrityError' (it used to carry the SQL message text); exact_error pins that there is no message text.
    'c1_authority_tables_alone_after_consume_refused_by_effect_uniqueness': ('c1', c1_authority_tables_after_consume,
        'authority tables (grants/approvals/policies/evidence/claims/budgets) from pre-execution snapshot', 'effects, attempts, receipts tables',
        S(step='replay_after_authority_tables_restore', status='denied', error='IntegrityError', exact_error=True, newly=False, effects=1, witness=1)),
    # Programme 2 (runtime 11de097c, atomic-route destination grants are revoked-final): restoring the authority tables to the pre-revocation
    # snapshot no longer reopens the revoked grant; the replay is refused (this case was 'c1_authority_tables_alone_after_revoke_reopens').
    'c1_authority_tables_alone_after_revoke_refused_revocation_is_final': ('c1', c1_authority_tables_after_revoke,
        'authority tables from pre-revocation snapshot', 'effects, attempts, receipts tables (none yet); destination grant row stays revoked',
        S(step='replay_after_authority_tables_restore', status='denied', error='authoritative grant state invalid', exact_error=True, newly=False, effects=0, witness=0)),
    'c1_authority_tables_alone_after_lost_ack_refused_by_effect_uniqueness': ('c1', c1_authority_tables_after_lost_ack,
        'authority tables from pre-execution snapshot', 'effects, attempts, receipts tables (effect committed, ack lost)',
        S(step='replay_after_authority_tables_restore', status='denied', error='IntegrityError', exact_error=True, newly=False, effects=1, witness=1)),
    'c1_full_restore_before_consume_accepts_replay': ('c1', c1_full_before_consume,
        'complete store (pre-execution)', 'nothing local; no external anchor exists',
        S(step='replay_after_full_restore', status='executed', error=None, newly=True, effects=1, witness=2)),
    'c1_full_restore_after_consume_refused': ('c1', c1_full_after_consume,
        'complete store (post-commit)', 'nothing local',
        S(step='replay_after_full_restore', status='denied', error='execution claim is not usable', newly=False, effects=1, witness=1)),
    'c1_full_restore_before_revoke_accepts': ('c1', c1_full_before_revoke,
        'complete store (pre-revocation)', 'nothing local; no external anchor exists',
        S(step='replay_after_full_restore', status='executed', error=None, newly=True, effects=1, witness=1)),
    'c1_effect_tables_alone_after_consume_fail_closed_effect_lost': ('c1', c1_destination_effect_tables_after_consume,
        'effects/attempts/receipts/failure tables (pre-execution)', 'authority tables (claim stays consumed)',
        S(step='replay_after_effect_tables_restore', status='denied', error='execution claim is not usable', newly=False, effects=0, witness=1)),
}


def _classify(steps, replay_label):
    replay = next(s for s in steps if s['step'] == replay_label)
    index = steps.index(replay)
    before = steps[index - 1]['witness_commits'] if index else 0
    added = replay['witness_commits'] - before
    status = replay['result']['status']
    if added:
        excess = replay['witness_commits'] - 1
        return 'ACCEPTED_REPLAY' + (f' (LIMITATION: {excess} excess historical commit(s) of the same effect)' if excess > 0 else ' (LIMITATION: authority re-opened by restore)')
    if status == 'reconciled':
        return 'RECONCILED_NO_NEW_EFFECT'
    return 'REFUSED'


def _world(kind, root, monkeypatch):
    return H.ChainWorld(root, monkeypatch) if kind == 'chain' else H.C1World(root)


def _run(name, root, monkeypatch):
    kind, scenario, *_ = SCENARIOS[name]
    root.mkdir()
    world = _world(kind, root, monkeypatch)
    steps = scenario(world)
    return {'steps': steps}


def _outcome(steps):
    """Run-comparable form: no timestamps/identifiers (results are already normalised)."""
    return [{'step': s['step'], 'state': s['state'], 'witness_commits': s['witness_commits'],
             'result': s.get('result') and {k: v for k, v in s['result'].items()}} for s in steps]


@pytest.mark.parametrize('name', sorted(SCENARIOS))
def test_scn_d07_restore_boundary(request, record_property, pinned_reference, tmp_path, monkeypatch, name):
    kind, _scenario, restored, remaining, expect = SCENARIOS[name]
    run1 = _run(name, tmp_path / 'run-1', monkeypatch)
    run2 = _run(name, tmp_path / 'run-2', monkeypatch)
    comparison = H.compare_runs({'outcome': _outcome(run1['steps'])}, {'outcome': _outcome(run2['steps'])})
    steps = run1['steps']
    replay = next(s for s in steps if s['step'] == expect['step'])
    classification = _classify(steps, expect['step'])
    effect_state = replay['state']['effects']
    H.record(request, record_property, 'd07_restore_boundary', {
        'scenario': 'D07', 'profile': kind, 'case': name, 'restore_scope': {'restored': restored, 'remaining_not_restored': remaining},
        'classification': classification, 'boundary': BOUNDARY, 'run_comparison': comparison,
        'run1_steps': steps, 'run2_steps': run2['steps'],
        'effect_admitted_after_restore': classification.startswith('ACCEPTED_REPLAY'),
        'note': 'ACCEPTED_REPLAY rows are observed limitations of local-only persistence, not rollback-safety acceptance'})
    assert comparison['verdict'] == 'MATCH', comparison
    result = replay['result']
    assert result['status'] == expect['status'], (name, result)
    assert bool(result['newly_executed']) is expect['newly'], (name, result)
    if expect['error']:
        assert expect['error'] in (result['error'] or ''), (name, result)
        if expect.get('exact_error'):
            assert result['error'] == expect['error'], (name, result)
    assert effect_state == expect['effects'], (name, replay['state'])
    assert replay['witness_commits'] == expect['witness'], (name, 'witnessed commits', replay['witness_commits'])


def test_scn_d07_external_anchor_absent_and_witness_not_consulted(request, record_property, pinned_reference, tmp_path, monkeypatch):
    """Local persistence is not an external anchor: no anchor concept exists in the code, and removing or forging the
    outside witness changes no admission outcome (the witness is not an input)."""
    ref = pinned_reference
    offenders = []
    classified = []
    for sub in ('control_plane/src', 'runtime/engine', 'exchange/experiments'):
        for path in (ref.paths[sub.split('/')[0]] / sub.split('/', 1)[1]).rglob('*.py'):
            for no, line in enumerate(path.read_text().splitlines(), 1):
                if re.search(r'anchor', line, re.I) and 'path.anchor' not in line:
                    rel = path.relative_to(ref.base).as_posix()
                    # a use of the word that is NOT a restore/anchor concept is classified by its exact file and exact line text
                    # (never by line number or pattern), so any other occurrence still fails the tripwire
                    if (rel, line.strip()) in NON_RESTORE_ANCHOR_USES:
                        classified.append(f'{rel}:{no}')
                    else:
                        offenders.append(f'{rel}:{no}')
    assert not offenders, f'a restore/anchor concept appears in reference code, re-characterise D07: {offenders}'

    def replay_outcome(variant):
        root = tmp_path / variant
        root.mkdir()
        w = H.ChainWorld(root, monkeypatch)
        a0, d0 = w.authority_snapshot(), w.destination_snapshot('d0.sqlite')
        w.execute('lost_ack')
        w.destination_restore(d0); w.authority_restore(a0)
        if variant == 'witness_removed':
            w.witness.path.unlink()
            w.witness.entries.clear()
        elif variant == 'witness_forged':
            w.witness.path.write_text('{"synthetic_commit_observed": "FORGED-REVOKE-EVERYTHING"}\n' * 5)
        res = w.execute()
        return {'status': res['status'], 'newly_executed': res['newly_executed'], 'effects': w.effects()}
    outcomes = {v: replay_outcome(v) for v in ('witness_present', 'witness_removed', 'witness_forged')}
    hub_text = None
    hub = os.environ.get('SCN_HUB_DIR')
    if hub:
        import json
        risks = json.loads((Path(hub) / 'residual-risks.json').read_text())['items']
        hub_text = next(r for r in risks if r['id'] == 'R-REVIEW-OPERATIONS')
        assert 'do not prevent full destination rollback' in hub_text['description']
    H.record(request, record_property, 'd07_anchor_boundary', {
        'scenario': 'D07', 'boundary': BOUNDARY, 'anchor_concept_in_reference_code': offenders,
        'anchor_word_uses_classified_as_not_a_restore_anchor': classified, 'replay_outcome_by_witness_variant': outcomes,
        'hub_declared_residual_risk': hub_text or 'SCN_HUB_DIR not supplied; declared residual not re-read in this run'})
    assert outcomes['witness_present'] == outcomes['witness_removed'] == outcomes['witness_forged']
