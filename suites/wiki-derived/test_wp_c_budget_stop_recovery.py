"""Scenario-derived tests: budgets, stop, approval binding, restore and failure behaviour (work package C).

SPDX-License-Identifier: Apache-2.0

Six catalog cases, each checked for the part that falls inside the declared scope of the stack, against the pinned synthetic
reference (routes A and B, see README.md). Each case keeps a positive control that must still pass next to the refusals it
checks.

Covered here: durable typed refusal records (TC-D12-021), approval binding, repeated-request identity and the shared effect budget
(TC-L06-016), stopping the next effect of one grant holder (TC-L06-022), the cumulative effect cap per budget identifier
(TC-L06-024), restore of the stack's own state (TC-L15-019) and fail-closed behaviour when an input is unavailable (TC-L17-028).
Budgets of independent identifiers stay independent; a nested budget hierarchy is not part of this suite.

Limits, asserted as limits and never as passes:

* budgets count effects per budget identifier; there is no time window, no reset and no alert, and no aggregate amount over several
  effects (TC-L06-016, TC-L06-024);
* the local stop journal holds what the host controller records; it does not authenticate who asked (TC-L06-022);
* restoring an older backup of the stack's state re-admits effects that were consumed after it was taken, because nothing outside
  the local files anchors that history (TC-L15-019);
* a refusal on the exchange route before acceptance is not durable; TC-D12-021 is checked on route A only.

Not claimed here: clustering or review of refusals, how approvals are presented to a human, approver workload, a fleet or
all-path stop, a health model or alert routing, backup or restore of anything outside the local SQLite files.

Run time: route A keeps its records in one JSON file that is rewritten for every record, so the cost of a route A test grows with
the number of records. The volume tests therefore spread their requests over several short, independent runs.
"""
from __future__ import annotations

import dataclasses
import importlib
import json
import re
import shutil
import sqlite3
import time
from pathlib import Path

import pytest

import _wiki_helpers as W
from _wiki_helpers import wiki_case

pytestmark = pytest.mark.usefixtures('pinned_reference')

REASON_CODE = re.compile(r'^[a-z][a-z0-9_]*$')
ROUTINE = 'refund.issue.routine'
BOUNDED_TARGET = 'urn:cognous:synthetic-account:customer-001'


# ------------------------------------------------------------------------------------------------ shared helpers
def _h():
    return W._h()


def _chain():
    return _h().reference().chain


def _c2a():
    _h()
    return importlib.import_module('_c_2a_helpers')


def revoke_resolver(flow):
    next(iter(flow.r.statuses.values())).status = 'revoked'


def revoke_destination(flow):
    b = flow.d.binding
    return flow.dest.set_effective_grant(principal=flow.p.principal, grant_id=b.grant_id, revision=b.grant_revision,
                                         permissions=flow.p.requested_permissions, status='revoked')


def rebind_approval(flow, proposal):
    """The approval is bound to the exact proposal: re-approve ``proposal`` (independent approval of one operation)."""
    ch = _chain()
    ref = flow.r.contexts[ch.PROFILE]['grant']['approval_refs'][0]
    flow.r.approvals[ref] = flow.r.approvals[ref].model_copy(
        update={'proposal_commitment': ch.commitment(proposal.model_dump(mode='json', exclude_none=False))})


def request_a(flow, label, **update):
    """A further, separately approved request on route A: (proposal, decision, envelope). Different ``label`` gives a different
    correlation, hence a different decision and effect identifier."""
    ch = _chain()
    p2 = flow.p.model_copy(update={'correlation_id': f'request-{label}', **update})
    rebind_approval(flow, p2)
    d2 = flow.f.decide(p2, now=ch.NOW)
    op = dataclasses.replace(flow.env.operation, proposal_commitment=ch.commitment(p2.model_dump(mode='json')),
                             **{k: v for k, v in update.items() if k in ('amount', 'target')})
    env2 = dataclasses.replace(flow.env, decision_id=d2.decision_id, effect_id=d2.effect_id, operation=op)
    return p2, d2, env2


def run_a(flow, proposal, decision, envelope, **kwargs):
    ch = _chain()
    try:
        return flow.executor.execute(envelope=envelope, proposal=proposal, decision=decision, now=ch.NOW, **kwargs), None
    except Exception as exc:  # a raised refusal is a refusal before dispatch
        return None, f'{type(exc).__name__}: {exc}'


def executed(res):
    return res is not None and res.status == 'executed' and res.attempted and res.observed_state == 'applied'


def journal(flow):
    return flow.f.records.load()


def counts(flow):
    rec = journal(flow)
    return {k: len(getattr(rec, k)) for k in ('decisions', 'refusals', 'attempts', 'closeouts')}


def failures(flow):
    return W.destination_summary(flow)['failures']


def assert_typed_reasons(reasons):
    assert reasons and all(REASON_CODE.match(code) for code in reasons), reasons


def part_b(h, n, cap, *, budget_id, claim_id=None, grant=None, extra_env=None):
    """One route B part (envelope and provisioned-able claim) for effect number ``n`` under ``budget_id`` with limit ``cap``."""
    kwargs = {'grant': grant} if grant else {}
    base = h.envelope(effect_no=n, **kwargs)
    env = dataclasses.replace(base, operation=dataclasses.replace(base.operation, effective_max_effects=int(cap)))
    claim = h.make_claim(env, claim_id=claim_id or f'claim-{budget_id}-{n}', budget_id=budget_id, max_effects=cap)
    return type('Part', (), {'n': n, 'env': env, 'claim': claim})()


def executor_b(flow, *, max_effects):
    from engine.local_authority_effect import AtomicLocalControlPlaneExecutor
    policy = dataclasses.replace(flow.policy, max_effects=max(1, max_effects))
    return AtomicLocalControlPlaneExecutor(workflow=object(), destination=flow.dest, policy=policy)


def sqlite_backup(source, target):
    """Consistent SQLite backup (no live callers while it runs)."""
    with sqlite3.connect(source) as src, sqlite3.connect(target) as dst:
        src.backup(dst)


def sqlite_rows(path, tables=None):
    """Whole-table state of a SQLite file through a read-only connection."""
    with sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True) as db:
        names = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        out = {}
        for name in names:
            if tables is not None and name not in tables:
                continue
            quoted = '"' + name.replace('"', '""') + '"'
            out[name] = [list(r) for r in db.execute('SELECT * FROM ' + quoted + ' ORDER BY rowid')]
    return out


# ================================================================================================ TC-D12-021
def refused_by_withdrawal(work, monkeypatch, requests):
    """Route A: ``requests`` separately approved requests are decided (authorized), then the grant is withdrawn at the resolver and
    every request is presented for execution. Returns the flow and the (proposal, decision, envelope) triples."""
    flow = W.route_a(work, monkeypatch)
    items = [(flow.p, flow.d, flow.env)]
    for k in range(1, requests):
        proposal, decision, env = request_a(flow, f'near-miss-{k}')
        assert decision.result == 'authorized', decision.reasons
        items.append((proposal, decision, env))
    revoke_resolver(flow)
    return flow, items


@wiki_case('TC-D12-021')
def test_wiki_d12_021_sixty_refused_requests_each_leave_a_durable_typed_refusal_record(tmp_path, monkeypatch):
    """Sixty refused requests, in twelve independent runs of five (route A keeps its records in one file that is rewritten for every
    record, so one run of sixty would take minutes). Every refused request leaves its own control-plane refusal record with typed
    reasons and its own destination failure record; no request leaves an effect."""
    seen_effects, refusal_total, failure_total = set(), 0, 0
    for run in range(12):
        work = tmp_path / f'run-{run:02d}'
        work.mkdir()
        flow, items = refused_by_withdrawal(work, monkeypatch, 5)
        for proposal, decision, env in items:
            res, exc = run_a(flow, proposal, decision, env)
            assert exc is not None or (res.status == 'denied' and not res.attempted), (res, exc)
        rec = journal(flow)
        assert len(rec.decisions) == 5 and len(rec.refusals) == 5, counts(flow)
        refusals = {r.effect_id: r for r in rec.refusals}
        assert set(refusals) == {d.effect_id for _, d, _ in items}, 'one refusal record per refused request, each under its own effect identity'
        for r in rec.refusals:
            assert r.stage == 'effect_time_revalidation' and 'grant_revoked' in r.reasons
            assert_typed_reasons(r.reasons)
            assert r.decision_id in {d.decision_id for _, d, _ in items} and r.refusal_id
        assert len({r.refusal_id for r in rec.refusals}) == 5
        stored = W.destination_summary(flow)
        assert len(stored['failures']) == 5 and {f[:3] for f in stored['failures']} == {('authority_hold', 'admission_rejected', 'pre_dispatch')}
        assert stored['effects'] == [] and stored['attempts'] == []
        seen_effects |= {(run, effect_id) for effect_id in refusals}
        refusal_total += len(rec.refusals)
        failure_total += len(stored['failures'])
    assert (refusal_total, failure_total, len(seen_effects)) == (60, 60, 60)
    # positive control: the same construction without the withdrawal executes
    (tmp_path / 'control').mkdir()
    control = W.route_a(tmp_path / 'control', monkeypatch)
    res, exc = run_a(control, control.p, control.d, control.env)
    assert exc is None and executed(res) and journal(control).refusals == []


@wiki_case('TC-D12-021')
def test_wiki_d12_021_refusal_at_the_commit_boundary_after_an_authorizing_decision_is_retained_and_distinct(tmp_path, monkeypatch):
    """An authorizing decision, then the authority is withdrawn at the destination only. The control plane still sees it as
    current; the destination refuses inside the commit. The refusal is retained as a failed attempt with its own reason code,
    which tells it apart from a refusal at the effect-time revalidation."""
    (tmp_path / 'boundary').mkdir()
    flow = W.route_a(tmp_path / 'boundary', monkeypatch)
    assert flow.d.result == 'authorized'
    revoke_destination(flow)
    res, exc = run_a(flow, flow.p, flow.d, flow.env)
    assert exc is None and (res.status, res.attempted, res.acknowledged, res.error) == ('failed', True, False, 'effective_grant_changed_at_commit')
    assert REASON_CODE.match(res.error)
    rec = journal(flow)
    assert [d.result for d in rec.decisions] == ['authorized'] and rec.refusals == []
    assert [a.status for a in rec.attempts] == ['attempted', 'failed'] and rec.attempts[-1].error == 'effective_grant_changed_at_commit'
    assert len({a.attempt_id for a in rec.attempts}) == 1 and rec.attempts[0].effect_id == flow.d.effect_id
    stored = W.destination_summary(flow)
    assert stored['effects'] == [] and [a['events'] for a in stored['attempts']] == [[('attempted', None), ('failed', 'effective_grant_changed_at_commit')]]
    # the refusal at the effect-time revalidation looks different: a refusal record, no attempt
    (tmp_path / 'revalidation').mkdir()
    other = W.route_a(tmp_path / 'revalidation', monkeypatch)
    revoke_resolver(other)
    res2, exc2 = run_a(other, other.p, other.d, other.env)
    assert exc2 is None and (res2.status, res2.attempted) == ('denied', False)
    rec2 = journal(other)
    assert len(rec2.refusals) == 1 and rec2.attempts == [] and rec2.refusals[0].stage == 'effect_time_revalidation'
    assert W.destination_summary(other)['attempts'] == []
    # the two retained shapes differ by record type and by reason
    assert rec.refusals == [] and rec2.attempts == []
    assert res.error not in rec2.refusals[0].reasons


@wiki_case('TC-D12-021')
def test_wiki_d12_021_refusals_survive_restart_and_appear_in_the_replay_reconstruction(tmp_path, monkeypatch):
    ch = _chain()
    flow = W.route_a(tmp_path, monkeypatch)
    revoke_resolver(flow)
    for _ in range(3):
        res, exc = run_a(flow, flow.p, flow.d, flow.env)
        assert exc is None and res.status == 'denied'
    before = journal(flow)
    ids = [r.refusal_id for r in before.refusals]
    assert len(ids) == 3 and len(set(ids)) == 3
    failure_ids = sorted(f['failure_id'] for f in flow.dest.failure_history(flow.env.effect_id))
    assert len(failure_ids) == 3
    # restart: new record store and destination objects over the same files
    store = type(flow.f.records)(flow.f.records.path, flow.f.records.run_id)
    after = store.load()
    assert [r.refusal_id for r in after.refusals] == ids
    assert [r.model_dump(mode='json') for r in after.refusals] == [r.model_dump(mode='json') for r in before.refusals]
    reopened = ch.EffectiveGrantDestination(flow.work / 'sqlite')
    assert sorted(f['failure_id'] for f in reopened.failure_history(flow.env.effect_id)) == failure_ids
    # the replay reconstruction carries every refusal, with its typed reasons, from the retained records
    exported = ch.export_execution_artifacts(flow.env, res, reopened, repository_revision=ch.MOLTBOT_RUNTIME_AUTHORITY_REVISION)
    bundle = ch.import_bounded_workflow(after.model_dump(mode='json'), proposal=flow.p.model_dump(mode='json'), moltbot_export=exported,
                                        control_plane_revision=ch.CONTROL_PLANE_RUNTIME_AUTHORITY_REVISION)
    assert bundle.status == 'reconstruction_complete' and all(r.complete for r in bundle.import_reports)
    kept = [r for r in bundle.records if r.record_type == 'effect_time_refusal']
    assert len(kept) == 3
    assert sorted(r.data['reasons'] for r in kept) == sorted(r.reasons for r in after.refusals)
    assert all('grant_revoked' in r.data['reasons'] for r in kept)


@wiki_case('TC-D12-021')
def test_wiki_d12_021_repeated_refusals_from_one_actor_are_each_retained(tmp_path, monkeypatch):
    flow = W.route_a(tmp_path, monkeypatch)
    actor = flow.d.binding.actor
    revoke_resolver(flow)
    for _ in range(8):
        res, exc = run_a(flow, flow.p, flow.d, flow.env)
        assert exc is None and (res.status, res.attempted) == ('denied', False)
    rec = journal(flow)
    assert len(rec.refusals) == 8 and len({r.refusal_id for r in rec.refusals}) == 8, 'a repeated refusal is not collapsed into an earlier one'
    assert {r.decision_id for r in rec.refusals} == {flow.d.decision_id} and {r.effect_id for r in rec.refusals} == {flow.d.effect_id}
    assert [d.binding.actor for d in rec.decisions] == [actor], 'the refusals trace to the one decision that names the actor'
    assert [r.recorded_at for r in rec.refusals] == sorted(r.recorded_at for r in rec.refusals)
    history = flow.dest.failure_history(flow.env.effect_id)
    assert len(history) == 8 and len({f['failure_id'] for f in history}) == 8
    assert {f['failure_class'] for f in history} == {'authority_hold'}
    assert W.destination_effects(flow) == []


# ================================================================================================ TC-L06-024
def capped_flow_a(work, monkeypatch, cap):
    """Route A flow whose manifest, requirement and grant allow ``cap`` effects (the approval is re-bound to the proposal)."""
    ch, C = _chain(), _c2a()

    def mutate(p, r, f, dest):
        f.manifest['actions'][0]['effect_limits']['max_effects'] = cap
        p = p.model_copy(update={'manifest_digest': ch.commitment(f.manifest)})
        ctx = r.contexts[ch.PROFILE]
        ctx['requirement']['permissions'][0]['max_effects'] = cap
        ctx['grant']['permissions'][0]['max_effects'] = cap
        ref = ctx['grant']['approval_refs'][0]
        r.approvals[ref] = r.approvals[ref].model_copy(update={'proposal_commitment': ch.commitment(p.model_dump(mode='json', exclude_none=False))})
        return p
    flow = C.flow_a_pre(work, monkeypatch, mutate)
    assert flow.d.result == 'authorized', flow.d.reasons
    executor, env = C.best_effort_executor(flow)
    executor.policy = dataclasses.replace(executor.policy, max_effects=cap)
    flow.executor, flow.env = executor, env
    return flow


@wiki_case('TC-L06-024')
def test_wiki_l06_024_cap_of_twenty_is_exact_under_one_hundred_attempts_route_a(tmp_path, monkeypatch):
    """Route A: the cap is a cumulative effect count per grant, enforced by the destination inside the commit. One hundred
    attempts against a cap of twenty leave exactly twenty effects; every later attempt is refused with the exhausted-cap reason.
    The destination takes the cap from the envelope it is given, so the hundred attempts present the decision-bound cap; the
    executor route is checked with the same behaviour on a small cap in the second part."""
    from engine.safe_executor import snapshot_envelope
    ch = _chain()
    (tmp_path / 'raw').mkdir()
    flow = W.route_a(tmp_path / 'raw', monkeypatch)
    digest = flow.r.contexts[ch.PROFILE]['runtime_authority']['expected_effective_grant_digest']
    accepted, refused = 0, []
    for n in range(1, 101):
        op = dataclasses.replace(flow.env.operation, target=f'urn:cognous:synthetic-account:customer-{n:03d}', effective_max_effects=20)
        env = ch.ExecutionEnvelope(flow.env.version, f'decision-cap-{n:03d}', f'effect-cap-{n:03d}', op)
        try:
            flow.dest.commit(snapshot_envelope(env), expected_effective_grant_digest=digest, effective_grant_derivation_version=ch.DERIVATION)
            accepted += 1
        except Exception as exc:
            refused.append(f'{type(exc).__name__}: {exc}')
    assert accepted == 20 and len(refused) == 80, (accepted, len(refused))
    assert all(text.endswith('local cumulative max_effects exhausted') for text in refused), set(refused)
    assert len(W.destination_effects(flow)) == 20
    assert flow.dest.effect_count(flow.d.binding.grant_id) == 20
    # the attempts after the cap leave no effect row: the twenty rows are the first twenty attempts
    assert [row['effect_id'] for row in W.destination_effects(flow)] == [f'effect-cap-{n:03d}' for n in range(1, 21)]

    # the same cumulative behaviour through the control-plane executor, on a cap of three with five separately approved requests
    (tmp_path / 'executor').mkdir()
    capped = capped_flow_a(tmp_path / 'executor', monkeypatch, 3)
    first, exc = run_a(capped, capped.p, capped.d, capped.env)
    assert exc is None and executed(first)
    outcomes = ['executed']
    for label in range(1, 5):
        p, d, env = request_a(capped, f'cap-{label}')
        assert d.result == 'authorized', d.reasons
        res, exc = run_a(capped, p, d, env)
        outcomes.append('executed' if executed(res) else 'refused')
    assert outcomes == ['executed'] * 3 + ['refused'] * 2, outcomes
    assert len(W.destination_effects(capped)) == 3
    assert any('local cumulative max_effects exhausted' in event[1] for a in W.destination_summary(capped)['attempts'] for event in a['events'] if event[1]), \
        W.destination_summary(capped)['attempts']


@wiki_case('TC-L06-024')
def test_wiki_l06_024_cap_of_twenty_is_exact_under_one_hundred_attempts_route_b(tmp_path):
    """Route B: one shared budget row (limit, used) in the destination; claims name it. One hundred claims against a limit of
    twenty give twenty effects, eighty refusals that name the exhausted budget, and eighty claims that are not consumed."""
    flow = W.route_b(tmp_path, effect_nos=tuple(range(1, 101)), budget_max=20)
    assert flow.dest.budget_state('budget-main') == {'max_effects': 20, 'used_effects': 0}
    statuses, errors = [], []
    for part in flow.parts:
        res, exc = W.execute_b(flow, part)
        assert exc is None, exc
        statuses.append(res.status)
        errors.append(res.error or '')
    assert statuses.count('executed') == 20 and statuses.count('denied') == 80, (statuses.count('executed'), statuses.count('denied'))
    assert statuses[:20] == ['executed'] * 20 and statuses[20:] == ['denied'] * 80
    assert all('budget exhausted' in text for text in errors[20:]), set(errors[20:])
    summary = W.destination_summary(flow)
    assert len(summary['effects']) == 20 and len(summary['attempts']) == 20
    assert summary['budgets'] == [('budget-main', 20, 20)]
    assert [state for _, state in summary['claims']].count('consumed') == 20 and [state for _, state in summary['claims']].count('issued') == 80
    assert flow.dest.trace.count('after_commit') == 20
    # a refused attempt is retained as a typed failure record
    assert len(summary['failures']) == 80 and {f[:3] for f in summary['failures']} == {('authority_hold', 'current_authority_rejected', 'pre_dispatch')}
    # a repeat of the whole series changes nothing
    for part in flow.parts:
        res, _ = W.execute_b(flow, part)
        assert res is None or not res.newly_executed
    assert W.destination_summary(flow)['effects'] == summary['effects']
    assert flow.dest.budget_state('budget-main') == {'max_effects': 20, 'used_effects': 20}


@wiki_case('TC-L06-024')
def test_wiki_l06_024_three_budgets_for_three_action_classes_are_independent(tmp_path):
    """Three budget identifiers (one per action class, chosen by the host) with their own limits. Exhausting one never touches
    another, and each stops at its own limit. The identifiers are host names: the stack does not derive an action class."""
    flow = W.route_b(tmp_path, effect_nos=(1,), budget_max=2)
    h, dest = flow.helpers, flow.dest
    plan = {'budget-refund': 2, 'budget-credit': 3, 'budget-adjustment': 1}
    parts, n = {}, 100
    for budget_id, cap in plan.items():
        parts[budget_id] = []
        for _ in range(cap + 2):  # two attempts beyond the limit for every budget
            n += 1
            part = part_b(h, n, cap, budget_id=budget_id, claim_id=f'claim-{n}')
            dest.provision_claim(part.claim)
            parts[budget_id].append(part)
    executor = executor_b(flow, max_effects=3)

    def attempt(part):
        res, exc = W.execute_b(flow, part, executor=executor)
        assert exc is None, exc
        return res.status

    # exhaust the first budget completely, then show the others are untouched
    first = [attempt(p) for p in parts['budget-refund']]
    assert first == ['executed', 'executed', 'denied', 'denied']
    assert dest.budget_state('budget-refund') == {'max_effects': 2, 'used_effects': 2}
    assert dest.budget_state('budget-credit') == {'max_effects': 3, 'used_effects': 0}
    assert dest.budget_state('budget-adjustment') == {'max_effects': 1, 'used_effects': 0}
    second = [attempt(p) for p in parts['budget-credit']]
    third = [attempt(p) for p in parts['budget-adjustment']]
    assert second == ['executed'] * 3 + ['denied'] * 2
    assert third == ['executed', 'denied', 'denied']
    summary = W.destination_summary(flow)
    assert sorted(summary['budgets']) == [('budget-adjustment', 1, 1), ('budget-credit', 3, 3), ('budget-main', 2, 0), ('budget-refund', 2, 2)]
    assert len(summary['effects']) == 2 + 3 + 1
    # an attempt on the exhausted budget stays refused although the others still had room earlier
    again = W.execute_b(flow, parts['budget-refund'][2], executor=executor)[0]
    assert again.status == 'denied' and 'budget exhausted' in (again.error or '')
    assert len(W.destination_summary(flow)['effects']) == 6


@wiki_case('TC-L06-024')
def test_wiki_l06_024_budget_state_reports_used_and_maximum_for_each_budget(tmp_path, monkeypatch):
    """The maximum and the used count of a budget are readable at any time, count only effects, and do not move on refusals. There
    is no window, reset or alert member in the budget record (limit asserted as a limit)."""
    flow = W.route_b(tmp_path, effect_nos=(1,), budget_max=3)
    h, dest = flow.helpers, flow.dest
    extra = [part_b(h, 200 + i, 3, budget_id='budget-main', claim_id=f'claim-extra-{i}') for i in range(3)]
    for part in extra:
        dest.provision_claim(part.claim)
    other = [part_b(h, 300 + i, 1, budget_id='budget-other', claim_id=f'claim-other-{i}') for i in range(2)]
    for part in other:
        dest.provision_claim(part.claim)
    executor = executor_b(flow, max_effects=3)
    assert dest.budget_state('budget-main') == {'max_effects': 3, 'used_effects': 0}
    assert dest.budget_state('budget-other') == {'max_effects': 1, 'used_effects': 0}
    assert dest.budget_state('budget-unknown') is None  # an unknown identifier is reported absent, not as an empty budget
    seen = []
    for part in [flow.parts[0], *extra]:
        res, _ = W.execute_b(flow, part, executor=executor)
        seen.append((res.status, dest.budget_state('budget-main')['used_effects']))
    assert seen == [('executed', 1), ('executed', 2), ('executed', 3), ('denied', 3)]
    # the other budget is not moved by them; a refused attempt does not move its own
    assert dest.budget_state('budget-other') == {'max_effects': 1, 'used_effects': 0}
    assert [W.execute_b(flow, p, executor=executor)[0].status for p in other] == ['executed', 'denied']
    assert dest.budget_state('budget-other') == {'max_effects': 1, 'used_effects': 1}
    # the record carries only an identifier, a limit and a usage count: no window, reset time or alert member
    with sqlite3.connect(Path(dest.path)) as db:
        columns = [row[1] for row in db.execute('PRAGMA table_info(effect_budgets_v1)')]
    assert columns == ['budget_id', 'max_effects', 'used_effects']
    assert [name for name in dir(type(dest)) if 'budget' in name.lower() and not name.startswith('_')] == ['budget_state']
    # route A: the cap of the grant is readable from the decision binding, and the used count from the destination
    (tmp_path / 'a').mkdir()
    flow_a = capped_flow_a(tmp_path / 'a', monkeypatch, 3)
    grant_id = flow_a.d.binding.grant_id
    assert flow_a.d.binding.effective_max_effects == 3 and flow_a.dest.effect_count(grant_id) == 0
    res, exc = run_a(flow_a, flow_a.p, flow_a.d, flow_a.env)
    assert exc is None and executed(res)
    assert flow_a.dest.effect_count(grant_id) == 1 and flow_a.d.binding.effective_max_effects == 3


# ================================================================================================ TC-L06-016
def envelope_for(flow, decision, proposal, **op_changes):
    """The envelope an unprivileged caller would build for ``decision`` even if it is a hold (the executor is then the only
    refusing layer)."""
    ch = _chain()
    op = dataclasses.replace(flow.env.operation, proposal_commitment=ch.commitment(proposal.model_dump(mode='json')), **op_changes)
    return dataclasses.replace(flow.env, decision_id=decision.decision_id, effect_id=decision.effect_id or 'effect-absent', operation=op)


HIGH_RISK = {'amount': 100.0}  # the highest amount the grant allows; the same scope as the routine requests, so only the approval differs


@wiki_case('TC-L06-016')
def test_wiki_l06_016_fifty_approved_low_risk_operations_do_not_carry_to_one_high_risk_operation(tmp_path, monkeypatch):
    """An approval is bound to one proposal commitment. Fifty separately approved low-risk operations leave the approval store
    holding the approval of the last of them; none of that approves a different, high-risk operation of the same grant."""
    flow = W.route_a(tmp_path, monkeypatch)
    ch = _chain()
    decisions = []
    for k in range(1, 51):
        proposal, decision, _ = request_a(flow, f'low-{k:02d}', amount=float(k % 9 + 1))
        assert decision.result == 'authorized' and decision.binding is not None, (k, decision.reasons)
        decisions.append(decision)
    assert len({d.effect_id for d in decisions}) == 50, 'each approved operation has its own identity'
    assert W.destination_effects(flow) == []
    # the high-risk operation is asked for while the approval in force is the one of the fiftieth low-risk operation
    high = flow.p.model_copy(update={'correlation_id': 'request-high', **HIGH_RISK})
    decision = flow.f.decide(high, now=ch.NOW)
    assert decision.result != 'authorized' and decision.binding is None
    assert decision.reasons == ['approval_operation_binding_mismatch'], decision.reasons
    retained = journal(flow).decisions[-1]
    assert retained.decision_id == decision.decision_id and retained.result == 'hold' and retained.reasons == decision.reasons
    # nothing reaches the destination for it: the executor refuses before dispatch and the refusal is retained
    res, exc = run_a(flow, high, decision, envelope_for(flow, decision, high, **HIGH_RISK))
    assert exc is not None or (res.status == 'denied' and not res.attempted), (res, exc)
    assert W.destination_effects(flow) == []
    # positive control: the same operation with its own approval is authorized and executes once
    rebind_approval(flow, high)
    approved = flow.f.decide(high, now=ch.NOW)
    assert approved.result == 'authorized' and approved.binding is not None, approved.reasons
    res, exc = run_a(flow, high, approved, envelope_for(flow, approved, high, **HIGH_RISK))
    assert exc is None and executed(res)
    rows = W.destination_effects(flow)
    assert len(rows) == 1 and rows[0]['amount'] == 100.0 and rows[0]['state'] == 'applied'


@wiki_case('TC-L06-016')
def test_wiki_l06_016_ten_split_effects_stop_at_the_shared_effect_budget(tmp_path):
    """Route B: ten effects split from one intent share one budget identifier with a limit of five. The sixth and later are
    refused. Amounts are not aggregated: the budget record holds a count and a limit, never an amount (limit)."""
    flow = W.route_b(tmp_path, effect_nos=tuple(range(1, 11)), budget_max=5)
    results = [W.execute_b(flow, part) for part in flow.parts]
    assert all(exc is None for _, exc in results)
    statuses = [res.status for res, _ in results]
    assert statuses == ['executed'] * 5 + ['denied'] * 5, statuses
    assert all('budget exhausted' in (res.error or '') for res, _ in results[5:])
    summary = W.destination_summary(flow)
    assert len(summary['effects']) == 5 and summary['budgets'] == [('budget-main', 5, 5)]
    assert [s for _, s in summary['claims']].count('issued') == 5
    # known limit: the stack counts effects, it does not add up amounts
    assert sum(row['amount'] for row in summary['effects']) == 250.0
    with sqlite3.connect(Path(flow.dest.path)) as db:
        assert [row[1] for row in db.execute('PRAGMA table_info(effect_budgets_v1)')] == ['budget_id', 'max_effects', 'used_effects']
    # positive control: a split of the same size inside the limit is carried out completely
    (tmp_path / 'inside').mkdir()
    inside = W.route_b(tmp_path / 'inside', effect_nos=tuple(range(1, 6)), budget_max=5)
    assert [W.execute_b(inside, part)[0].status for part in inside.parts] == ['executed'] * 5
    assert W.destination_summary(inside)['budgets'] == [('budget-main', 5, 5)]


@wiki_case('TC-L06-016')
def test_wiki_l06_016_repeated_identical_requests_yield_one_effect(tmp_path, monkeypatch):
    """The same request gives the same operation identity. Presented ten times it executes once on route A and once on route B;
    the repeats are reported as already applied, not executed again."""
    ch = _chain()
    (tmp_path / 'a').mkdir()
    flow = W.route_a(tmp_path / 'a', monkeypatch)
    again = flow.f.decide(flow.p, now=ch.NOW)
    assert again.result == 'authorized' and again.effect_id == flow.d.effect_id, 'the same proposal has the same effect identity'
    outcomes = []
    for _ in range(10):
        res, exc = run_a(flow, flow.p, flow.d, flow.env)
        assert exc is None, exc
        outcomes.append((res.status, res.newly_executed))
    assert outcomes == [('executed', True)] + [('reconciled', False)] * 9, outcomes
    rows = W.destination_effects(flow)
    assert len(rows) == 1 and rows[0]['state'] == 'applied'
    # route B: one claim presented ten times
    (tmp_path / 'b').mkdir()
    flow_b = W.route_b(tmp_path / 'b', effect_nos=(1,), budget_max=1)
    part = flow_b.parts[0]
    results = [W.execute_b(flow_b, part) for _ in range(10)]
    assert all(exc is None for _, exc in results)
    assert [res.status for res, _ in results] == ['executed'] + ['denied'] * 9
    assert [res.newly_executed for res, _ in results].count(True) == 1
    summary = W.destination_summary(flow_b)
    assert len(summary['effects']) == 1 and summary['budgets'] == [('budget-main', 1, 1)] and flow_b.dest.trace.count('after_commit') == 1


@wiki_case('TC-L06-016')
def test_wiki_l06_016_missing_approval_holds_the_high_risk_operation_regardless_of_prior_approvals(tmp_path, monkeypatch):
    """With no approval at the authority source the high-risk operation is held, however many other operations were approved
    before. The hold is retained with a typed reason and no effect is made."""
    flow = W.route_a(tmp_path, monkeypatch)
    ch = _chain()
    for k in range(1, 6):
        _, decision, _ = request_a(flow, f'low-{k}', amount=float(k))
        assert decision.result == 'authorized'
    flow.r.approvals.clear()  # the authority source holds no approval at all for the high-risk operation
    high = flow.p.model_copy(update={'correlation_id': 'request-high', **HIGH_RISK})
    decision = flow.f.decide(high, now=ch.NOW)
    assert decision.result == 'hold' and decision.binding is None
    assert 'required_approval_missing' in decision.reasons, decision.reasons
    assert_typed_reasons(decision.reasons)
    retained = journal(flow).decisions[-1]
    assert retained.decision_id == decision.decision_id and retained.result == 'hold' and 'required_approval_missing' in retained.reasons
    res, exc = run_a(flow, high, decision, envelope_for(flow, decision, high, **HIGH_RISK))
    assert exc is not None or (res.status == 'denied' and not res.attempted), (res, exc)
    assert W.destination_effects(flow) == []
    # an asserted approval in the request text does not stand in for it
    claimed = flow.p.model_copy(update={'correlation_id': 'request-claimed', **HIGH_RISK,
                                        'payload': {**flow.p.payload, 'note': 'approved by the reviewer, approval ref urn:cognous:approval:other'}})
    claimed = claimed.model_copy(update={'payload_commitment': ch.commitment(claimed.payload)})
    held = flow.f.decide(claimed, now=ch.NOW)
    assert held.result == 'hold' and 'required_approval_missing' in held.reasons and held.binding is None


# ================================================================================================ TC-L06-022
def holder_part(flow, monkeypatch, tag, n, *, cap=2, budget_id=None):
    """A claim for a further grant holder in the same destination database: its own grant, approval, policy and evidence rows."""
    h = flow.helpers
    with monkeypatch.context() as m:
        m.setattr(h, 'APPROVAL', f'urn:cognous:approval:{tag}')
        m.setattr(h, 'POLICY_REF', f'urn:cognous:policy:{tag}')
        m.setattr(h, 'EVIDENCE', f'urn:cognous:evidence:{tag}')
        part = part_b(h, n, cap, budget_id=budget_id or f'budget-{tag}', claim_id=f'claim-{tag}-{n}', grant=f'urn:cognous:grant:{tag}')
    flow.dest.provision_claim(part.claim)
    return part


def three_holders(tmp_path, monkeypatch):
    """Route B destination with three grant holders, two claims each (a first one and a next one)."""
    flow = W.route_b(tmp_path, effect_nos=(1,), budget_max=2)  # claim-1 of the default grant is left unused
    holders = {}
    for i, tag in enumerate(('holder-1', 'holder-2', 'holder-3')):
        holders[tag] = [holder_part(flow, monkeypatch, tag, 10 * (i + 1) + k) for k in range(2)]
    return flow, holders, executor_b(flow, max_effects=2)


def grant_of(part):
    return part.claim.grant_id


@wiki_case('TC-L06-022')
def test_wiki_l06_022_suspended_grant_refuses_the_next_effect_of_one_holder_while_a_second_holder_executes(tmp_path, monkeypatch):
    flow, holders, executor = three_holders(tmp_path, monkeypatch)
    dest = flow.dest

    def attempt(part):
        res, exc = W.execute_b(flow, part, executor=executor)
        assert exc is None, exc
        return res

    # before the stop every holder's first effect passes
    first = {tag: attempt(parts[0]) for tag, parts in holders.items()}
    assert {tag: res.status for tag, res in first.items()} == {tag: 'executed' for tag in holders}
    assert len(W.destination_effects(flow)) == 3
    # stop holder 1 by suspending its grant: its next effect is refused; the second and third holders still execute
    dest.set_grant_status(grant_of(holders['holder-1'][0]), status='suspended')
    refused = attempt(holders['holder-1'][1])
    assert refused.status == 'denied' and not refused.attempted and 'authoritative grant state invalid' in (refused.error or '')
    assert dest.claim_state(holders['holder-1'][1].claim.claim_id) == 'issued', 'the refused claim is not consumed'
    assert attempt(holders['holder-2'][1]).status == 'executed'
    assert attempt(holders['holder-3'][1]).status == 'executed'
    summary = W.destination_summary(flow)
    assert len(summary['effects']) == 5
    assert {e['effect_id'] for e in summary['effects']} == {p.env.effect_id for tag, parts in holders.items() for p in parts if tag != 'holder-1' or p is parts[0]}
    # the refusal is retained as a typed failure record
    assert [f[:3] for f in summary['failures']] == [('authority_hold', 'current_authority_rejected', 'pre_dispatch')]
    # a suspension is reversible: the same holder executes again once the grant is active, which shows the stop was the cause
    dest.set_grant_status(grant_of(holders['holder-1'][0]), status='active')
    assert attempt(holders['holder-1'][1]).status == 'executed'
    # a revocation is final for that grant revision: it refuses the next effect and cannot be undone by a later status write
    (tmp_path / 'revoked').mkdir()
    flow2, holders2, executor2 = three_holders(tmp_path / 'revoked', monkeypatch)
    assert W.execute_b(flow2, holders2['holder-2'][0], executor=executor2)[0].status == 'executed'
    flow2.dest.set_grant_status(grant_of(holders2['holder-2'][0]), status='revoked')
    res = W.execute_b(flow2, holders2['holder-2'][1], executor=executor2)[0]
    assert res.status == 'denied' and not res.attempted
    with pytest.raises(PermissionError):
        flow2.dest.set_grant_status(grant_of(holders2['holder-2'][0]), status='active')
    assert W.execute_b(flow2, holders2['holder-1'][0], executor=executor2)[0].status == 'executed'
    assert W.execute_b(flow2, holders2['holder-3'][0], executor=executor2)[0].status == 'executed'


@wiki_case('TC-L06-022')
def test_wiki_l06_022_suspension_persists_across_restart(tmp_path, monkeypatch):
    # route B: the grant row is in the destination database
    (tmp_path / 'b').mkdir()
    flow, holders, executor = three_holders(tmp_path / 'b', monkeypatch)
    flow.dest.set_grant_status(grant_of(holders['holder-1'][0]), status='suspended')
    reopened = type(flow.dest)(flow.work, clock=flow.clock)
    fresh = type(executor)(workflow=object(), destination=reopened, policy=executor.policy)
    flow.dest = reopened
    res = W.execute_b(flow, holders['holder-1'][0], executor=fresh)[0]
    assert res.status == 'denied' and not res.attempted and 'authoritative grant state invalid' in (res.error or '')
    assert reopened.claim_state(holders['holder-1'][0].claim.claim_id) == 'issued'
    assert W.execute_b(flow, holders['holder-2'][0], executor=fresh)[0].status == 'executed'
    # route A: the effective grant row is in the destination database; the executor and destination are rebuilt from the file
    (tmp_path / 'a').mkdir()
    ch = _chain()
    flow_a = W.route_a(tmp_path / 'a', monkeypatch)
    b = flow_a.d.binding
    flow_a.dest.set_effective_grant(principal=flow_a.p.principal, grant_id=b.grant_id, revision=b.grant_revision,
                                    permissions=flow_a.p.requested_permissions, status='suspended')
    dest2 = ch.EffectiveGrantDestination(flow_a.work / 'sqlite')
    flow_a.dest = dest2
    flow_a.executor = ch.PinnedControlPlaneExecutor(workflow=flow_a.f, destination=dest2, policy=flow_a.executor.policy, observation_clock=lambda: ch.NOW)
    res, exc = run_a(flow_a, flow_a.p, flow_a.d, flow_a.env)
    assert exc is not None or (res.status in ('denied', 'failed') and not res.acknowledged), (res, exc)
    assert W.destination_effects(flow_a) == []
    assert [status for _, status in W.destination_summary(flow_a)['effective_grants']] == ['suspended']


@wiki_case('TC-L06-022')
def test_wiki_l06_022_stop_journal_retains_requester_and_reason_in_order(tmp_path, monkeypatch):
    """The local stop journal holds what the controlling process records at each step, ordered by sequence. The journal is a
    record of observations: it does not check who the requester is, and it is not a mechanism that stops anything."""
    from engine.c8_source_evidence import LocalStopJournal, STOP_KINDS
    flow, holders, executor = three_holders(tmp_path, monkeypatch)
    dest = flow.dest
    stopped, other = holders['holder-1'], holders['holder-2']
    assert W.execute_b(flow, stopped[0], executor=executor)[0].status == 'executed'
    journal_path = tmp_path / 'stop-journal.sqlite'
    j = LocalStopJournal(journal_path)
    life, effect = 'stop-holder-1', stopped[1].env.effect_id
    requester, reason = 'urn:cognous:principal:operations-lead', 'synthetic_incident_drill'

    j.record(event_id='e1', sequence=1, lifecycle_id=life, effect_id=effect, kind='stop_requested',
             observation={'requester': requester, 'reason': reason, 'grant_id': grant_of(stopped[0])})
    dest.set_grant_status(grant_of(stopped[0]), status='suspended')
    with sqlite3.connect(Path(dest.path)) as db:
        status = db.execute('SELECT status FROM authority_grants_v1 WHERE grant_id=?', (grant_of(stopped[0]),)).fetchone()[0]
    j.record(event_id='e2', sequence=2, lifecycle_id=life, effect_id=effect, kind='stop_acknowledged',
             observation={'grant_status': status})
    refused = W.execute_b(flow, stopped[1], executor=executor)[0]
    j.record(event_id='e3', sequence=3, lifecycle_id=life, effect_id=effect, kind='dispatch_closed',
             observation={'next_effect_status': refused.status, 'attempted': refused.attempted})
    before = W.destination_effects(flow)
    j.record(event_id='e4', sequence=4, lifecycle_id=life, effect_id=effect, kind='quiescence_observed',
             observation={'effect_rows_unchanged': W.destination_effects(flow) == before})
    # a second, unrelated lifecycle interleaved in time does not mix into the first
    j.record(event_id='x1', sequence=5, lifecycle_id='stop-other', effect_id=other[0].env.effect_id, kind='stop_requested',
             observation={'requester': 'urn:cognous:principal:someone-else', 'reason': 'other_reason'})
    from engine.safe_executor import snapshot_envelope
    recon = dest.reconcile_claim(stopped[0].claim.claim_id, snapshot_envelope(stopped[0].env))
    j.record(event_id='e5', sequence=6, lifecycle_id=life, effect_id=effect, kind='destination_reconciled',
             observation={'status': recon['status'], 'retry_eligible': recon['retry_eligible']})

    exported = LocalStopJournal(journal_path).export(life)  # read back through a new handle on the file
    events = exported['events']
    assert [e['kind'] for e in events] == list(STOP_KINDS)
    assert [e['sequence'] for e in events] == [1, 2, 3, 4, 6]
    assert events[0]['observation'] == {'requester': requester, 'reason': reason, 'grant_id': grant_of(stopped[0])}
    assert events[1]['observation'] == {'grant_status': 'suspended'}
    assert events[2]['observation'] == {'next_effect_status': 'denied', 'attempted': False}
    assert events[3]['observation'] == {'effect_rows_unchanged': True}
    assert events[4]['observation'] == {'status': 'applied', 'retry_eligible': False}
    assert exported['provenance'] == 'explicit_local_controller_observations_only'
    assert LocalStopJournal(journal_path).export('stop-other')['events'][0]['observation']['reason'] == 'other_reason'
    # the order is the sequence: a repeated sequence or event identifier is refused, an unknown kind is refused
    with pytest.raises(sqlite3.IntegrityError):
        j.record(event_id='e6', sequence=3, lifecycle_id=life, effect_id=effect, kind='dispatch_closed', observation={})
    with pytest.raises(sqlite3.IntegrityError):
        j.record(event_id='e1', sequence=9, lifecycle_id=life, effect_id=effect, kind='dispatch_closed', observation={})
    with pytest.raises(ValueError):
        j.record(event_id='e7', sequence=10, lifecycle_id=life, effect_id=effect, kind='fleet_stopped', observation={})
    assert len(LocalStopJournal(journal_path).export(life)['events']) == 5
    # known limit: the journal accepts any requester value; it does not authenticate it
    j.record(event_id='e8', sequence=11, lifecycle_id='stop-unchecked', effect_id=effect, kind='stop_requested',
             observation={'requester': 'anyone-at-all', 'reason': 'unverified'})
    assert LocalStopJournal(journal_path).export('stop-unchecked')['events'][0]['observation']['requester'] == 'anyone-at-all'


@wiki_case('TC-L06-022')
def test_wiki_l06_022_call_already_committed_is_reported_applied_and_not_rolled_back(tmp_path, monkeypatch):
    from engine.safe_executor import snapshot_envelope
    # route B: the acknowledgement of the first call is lost, the grant is stopped afterwards
    (tmp_path / 'b').mkdir()
    flow, holders, executor = three_holders(tmp_path / 'b', monkeypatch)
    dest, part = flow.dest, holders['holder-1'][0]
    first = W.execute_b(flow, part, executor=executor, simulate='lost_ack')[0]
    assert first.status == 'unknown' and first.attempted and not first.acknowledged and first.observed_state == 'applied'
    committed = W.destination_effects(flow)
    assert len(committed) == 1 and committed[0]['effect_id'] == part.env.effect_id
    dest.set_grant_status(grant_of(part), status='suspended')
    recon = dest.reconcile_claim(part.claim.claim_id, snapshot_envelope(part.env))
    assert (recon['status'], recon['retry_eligible']) == ('applied', False), recon
    assert dest.claim_state(part.claim.claim_id) == 'consumed'
    retry = W.execute_b(flow, part, executor=executor)[0]
    assert retry.status == 'denied' and not retry.newly_executed
    assert W.destination_effects(flow) == committed, 'the stop did not remove or change the committed effect'
    states = {e['state'] for e in W.destination_effects(flow)} | {state for _, state in W.destination_summary(flow)['claims']}
    assert not any(word in state for state in states for word in ('rolled', 'reverted', 'cancel', 'undone')), states
    # route A: executed, then the grant is revoked at the destination; the historical observation still reports applied
    (tmp_path / 'a').mkdir()
    flow_a = W.route_a(tmp_path / 'a', monkeypatch)
    res, exc = run_a(flow_a, flow_a.p, flow_a.d, flow_a.env)
    assert exc is None and executed(res)
    before = W.destination_effects(flow_a)
    revoke_resolver(flow_a)
    revoke_destination(flow_a)
    again, exc = run_a(flow_a, flow_a.p, flow_a.d, flow_a.env)
    assert exc is not None or (again.status == 'denied' and not again.newly_executed), (again, exc)
    historical = flow_a.executor.observe_historical(flow_a.env)
    assert historical.observed_state == 'applied'
    assert W.destination_effects(flow_a) == before and before[0]['state'] == 'applied'


# ================================================================================================ TC-L15-019
AUTHORITY_TABLES = ('authority_grants_v1', 'authority_approvals_v1', 'authority_policies_v1', 'authority_evidence_v1',
                    'execution_claims_v1', 'effect_budgets_v1')
EFFECT_TABLES = ('effects', 'attempts', 'attempt_events', 'authority_effect_receipts_v1', 'failure_records_v1')


def reopen_b(flow, *, max_effects):
    """New destination and executor objects over the same database file (a restarted process)."""
    flow.dest = type(flow.dest)(flow.work, clock=flow.clock)
    flow.dest.trace = []
    return executor_b(flow, max_effects=max_effects)


def wipe_database(path):
    """Loss of the database: the file and its journal files are gone."""
    for suffix in ('', '-wal', '-shm', '-journal'):
        Path(str(path) + suffix).unlink(missing_ok=True)


def restore_tables(snapshot, live, tables):
    """Replace only ``tables`` of ``live`` with their rows from ``snapshot`` (a table the snapshot lacks becomes empty)."""
    with sqlite3.connect(live) as db:
        db.execute('ATTACH DATABASE ? AS snap', (str(snapshot),))
        for table in tables:
            db.execute(f'DELETE FROM main."{table}"')
            if db.execute('SELECT 1 FROM snap.sqlite_master WHERE type = ? AND name = ?', ('table', table)).fetchone():
                db.execute(f'INSERT INTO main."{table}" SELECT * FROM snap."{table}"')
        db.commit()
        db.execute('DETACH DATABASE snap')


class Witness:
    """What really committed, recorded outside the restore set: every executor result that reports a new execution. A test
    observer only; it is not an input of any admission and not an anchor."""

    def __init__(self):
        self.commits = []

    def run(self, call):
        res, exc = call()
        if res is not None and res.newly_executed:
            self.commits.append(res.effect_id)
        return res, exc


class ChainState:
    """Route A state in the three places a host keeps it: resolver statuses, control-plane journal file, destination database."""

    def __init__(self, tmp_path, monkeypatch):
        self.flow = W.route_a(tmp_path, monkeypatch)
        self.witness = Witness()
        self.root = tmp_path

    def execute(self, **kwargs):
        f = self.flow
        return self.witness.run(lambda: run_a(f, f.p, f.d, f.env, **kwargs))

    def authority_snapshot(self):
        import copy
        return {'statuses': copy.deepcopy(self.flow.r.statuses), 'journal': self.flow.f.records.path.read_bytes()}

    def authority_restore(self, snap):
        import copy
        self.flow.r.statuses.clear()
        self.flow.r.statuses.update(copy.deepcopy(snap['statuses']))
        self.flow.f.records.path.write_bytes(snap['journal'])

    def destination_snapshot(self, name):
        snap = self.root / name
        sqlite_backup(self.flow.dest.path, snap)
        return snap

    def destination_restore(self, snap):
        sqlite_backup(snap, self.flow.dest.path)

    def effects(self):
        return len(W.destination_effects(self.flow))


@wiki_case('TC-L15-019')
def test_wiki_l15_019_restore_of_authority_and_destination_files_preserves_grants_budgets_claims_and_effects(tmp_path, monkeypatch):
    # route B: authority state, claims, budgets and effects share one database file
    (tmp_path / 'b').mkdir()
    flow = W.route_b(tmp_path / 'b', effect_nos=(1, 2, 3, 4), budget_max=3)
    assert [W.execute_b(flow, p)[0].status for p in flow.parts[:2]] == ['executed', 'executed']
    before = sqlite_rows(flow.dest.path)
    assert before['effects'] and before['execution_claims_v1'] and before['effect_budgets_v1'] and before['authority_grants_v1']
    backup = tmp_path / 'b-backup.sqlite'
    sqlite_backup(flow.dest.path, backup)
    wipe_database(flow.dest.path)
    assert not flow.dest.path.exists()
    sqlite_backup(backup, flow.dest.path)
    executor = reopen_b(flow, max_effects=3)
    after = sqlite_rows(flow.dest.path)
    assert after == before, [t for t in before if after.get(t) != before[t]]
    assert flow.dest.budget_state('budget-main') == {'max_effects': 3, 'used_effects': 2}
    assert [flow.dest.claim_state(p.claim.claim_id) for p in flow.parts] == ['consumed', 'consumed', 'issued', 'issued']
    # the restored store keeps working exactly where it stopped: one unit of budget is left
    assert [W.execute_b(flow, p, executor=executor)[0].status for p in flow.parts[2:]] == ['executed', 'denied']
    assert flow.dest.budget_state('budget-main') == {'max_effects': 3, 'used_effects': 3}
    assert len(W.destination_effects(flow)) == 3

    # route A: resolver statuses and control-plane journal on one side, destination database on the other
    (tmp_path / 'a').mkdir()
    world = ChainState(tmp_path / 'a', monkeypatch)
    res, exc = world.execute()
    assert exc is None and executed(res)
    rows_before = sqlite_rows(world.flow.dest.path)
    authority, destination = world.authority_snapshot(), world.destination_snapshot('destination-backup.sqlite')
    journal_before = world.flow.f.records.path.read_bytes()
    wipe_database(world.flow.dest.path)
    world.flow.f.records.path.write_bytes(b'')
    world.authority_restore(authority)
    sqlite_backup(destination, world.flow.dest.path)
    assert world.flow.f.records.path.read_bytes() == journal_before
    assert sqlite_rows(world.flow.dest.path) == rows_before
    assert world.flow.dest.effect_count(world.flow.d.binding.grant_id) == 1
    assert [status for _, status in W.destination_summary(world.flow)['effective_grants']] == ['active']
    assert [d.result for d in journal(world.flow).decisions] == ['authorized']
    # the effect is reported as already applied after the restore, and none is added
    again, exc = world.execute()
    assert exc is None and (again.status, again.newly_executed) == ('reconciled', False)
    assert world.effects() == 1 and world.witness.commits == [world.flow.d.effect_id]


@wiki_case('TC-L15-019')
def test_wiki_l15_019_consumed_claim_stays_consumed_and_the_retry_is_refused_after_restore(tmp_path, monkeypatch):
    (tmp_path / 'b').mkdir()
    flow = W.route_b(tmp_path / 'b', effect_nos=(1, 2), budget_max=2)
    witness = Witness()
    first = W.execute_b(flow, flow.parts[0])[0]
    assert first.status == 'executed'
    witness.commits.append(first.effect_id)
    backup = tmp_path / 'after-first.sqlite'
    sqlite_backup(flow.dest.path, backup)
    # more work after the backup, then a loss and a restore from that backup
    second = W.execute_b(flow, flow.parts[1])[0]
    assert second.status == 'executed'
    wipe_database(flow.dest.path)
    sqlite_backup(backup, flow.dest.path)
    executor = reopen_b(flow, max_effects=2)
    assert flow.dest.claim_state(flow.parts[0].claim.claim_id) == 'consumed'
    state_before = sqlite_rows(flow.dest.path)
    retry = W.execute_b(flow, flow.parts[0], executor=executor)[0]
    assert retry.status == 'denied' and not retry.attempted and not retry.newly_executed
    assert 'execution claim is not usable' in (retry.error or ''), retry.error
    assert sqlite_rows(flow.dest.path)['effects'] == state_before['effects'] and len(state_before['effects']) == 1
    assert flow.dest.budget_state('budget-main') == {'max_effects': 2, 'used_effects': 1}
    # recovery of the consumed claim reports the committed effect and no retry eligibility
    from engine.safe_executor import snapshot_envelope
    recon = flow.dest.reconcile_claim(flow.parts[0].claim.claim_id, snapshot_envelope(flow.parts[0].env))
    assert (recon['status'], recon['retry_eligible']) == ('applied', False)
    assert [failure[:3] for failure in W.destination_summary(flow)['failures']][-1] == ('authority_hold', 'current_authority_rejected', 'pre_dispatch')

    # route A: after a restore of every part from the state taken after the effect, the retry is reported as applied
    (tmp_path / 'a').mkdir()
    world = ChainState(tmp_path / 'a', monkeypatch)
    assert executed(world.execute()[0])
    authority, destination = world.authority_snapshot(), world.destination_snapshot('after-effect.sqlite')
    world.authority_restore(authority)
    world.destination_restore(destination)
    retry, exc = world.execute()
    assert exc is None and (retry.status, retry.newly_executed) == ('reconciled', False)
    assert world.effects() == 1 and world.witness.commits == [world.flow.d.effect_id]


@wiki_case('TC-L15-019')
def test_wiki_l15_019_destination_restored_without_authority_state_refuses_or_holds(tmp_path, monkeypatch):
    # route B: the effect tables go back to an older state while the authority tables (claim consumed) stay: fail closed
    (tmp_path / 'b1').mkdir()
    flow = W.route_b(tmp_path / 'b1', effect_nos=(1,), budget_max=1)
    old = tmp_path / 'before-effect.sqlite'
    sqlite_backup(flow.dest.path, old)
    assert W.execute_b(flow, flow.parts[0])[0].status == 'executed'
    restore_tables(old, flow.dest.path, EFFECT_TABLES)
    executor = reopen_b(flow, max_effects=1)
    assert W.destination_effects(flow) == [], 'the effect rows are gone with their tables'
    res = W.execute_b(flow, flow.parts[0], executor=executor)[0]
    assert res.status == 'denied' and not res.attempted and 'execution claim is not usable' in (res.error or '')
    assert W.destination_effects(flow) == [], 'nothing is admitted from the half-restored state'
    assert flow.dest.claim_state(flow.parts[0].claim.claim_id) == 'consumed'

    # route B: the authority tables go back to an older state while the effects stay: refused by effect uniqueness
    (tmp_path / 'b2').mkdir()
    flow2 = W.route_b(tmp_path / 'b2', effect_nos=(1,), budget_max=1)
    old2 = tmp_path / 'before-effect-2.sqlite'
    sqlite_backup(flow2.dest.path, old2)
    assert W.execute_b(flow2, flow2.parts[0])[0].status == 'executed'
    committed = W.destination_effects(flow2)
    restore_tables(old2, flow2.dest.path, AUTHORITY_TABLES)
    executor2 = reopen_b(flow2, max_effects=1)
    assert flow2.dest.claim_state(flow2.parts[0].claim.claim_id) == 'issued'
    res2 = W.execute_b(flow2, flow2.parts[0], executor=executor2)[0]
    assert res2.status == 'denied' and not res2.newly_executed
    assert W.destination_effects(flow2) == committed and len(committed) == 1

    # route A: destination restored to a state in which the grant was still active while the resolver kept the revocation
    (tmp_path / 'a1').mkdir()
    world = ChainState(tmp_path / 'a1', monkeypatch)
    snap = world.destination_snapshot('active-grant.sqlite')
    revoke_resolver(world.flow)
    revoke_destination(world.flow)
    assert world.execute()[0].status == 'denied'
    world.destination_restore(snap)
    res, exc = world.execute()
    assert exc is None and (res.status, res.error) == ('denied', 'authorization-critical inputs changed before effect'), (res, exc)
    assert world.effects() == 0 and world.witness.commits == []

    # route A: resolver statuses and journal restored to an older state while the destination keeps the revoked grant
    (tmp_path / 'a2').mkdir()
    world2 = ChainState(tmp_path / 'a2', monkeypatch)
    older = world2.authority_snapshot()
    revoke_resolver(world2.flow)
    revoke_destination(world2.flow)
    assert world2.execute()[0].status == 'denied'
    world2.authority_restore(older)
    res, exc = world2.execute()
    assert exc is None and (res.status, res.error) == ('failed', 'effective_grant_changed_at_commit'), (res, exc)
    assert world2.effects() == 0 and world2.witness.commits == []


@wiki_case('TC-L15-019')
def test_wiki_l15_019_restore_of_an_older_backup_readmits_later_effects_known_limit(tmp_path, monkeypatch):
    """Known limit, asserted as a limit and not as a pass: the state lives in local files with no anchor outside them, so a
    consistent restore of an OLDER backup returns claims and budgets to the state of that day, and effects consumed after it was
    taken are admitted again. The witness below is a test observer outside the restore set; the stack never consults it."""
    (tmp_path / 'b').mkdir()
    flow = W.route_b(tmp_path / 'b', effect_nos=(1, 2, 3, 4), budget_max=2)
    witness = Witness()
    older = tmp_path / 'older.sqlite'
    sqlite_backup(flow.dest.path, older)
    for part in flow.parts[:3]:
        res = W.execute_b(flow, part)[0]
        if res.newly_executed:
            witness.commits.append(res.effect_id)
    assert flow.dest.budget_state('budget-main') == {'max_effects': 2, 'used_effects': 2}
    assert len(witness.commits) == 2
    # restore of the older backup: the budget and the claims are those of the earlier day
    wipe_database(flow.dest.path)
    sqlite_backup(older, flow.dest.path)
    executor = reopen_b(flow, max_effects=2)
    assert flow.dest.budget_state('budget-main') == {'max_effects': 2, 'used_effects': 0}
    assert W.destination_effects(flow) == []
    for part in flow.parts:
        res = W.execute_b(flow, part, executor=executor)[0]
        if res.newly_executed:
            witness.commits.append(res.effect_id)
    # the first two effects were committed a second time, and in total twice the budget limit was spent
    assert len(witness.commits) == 4 and len(set(witness.commits)) == 2
    assert witness.commits.count(flow.parts[0].env.effect_id) == 2
    assert len(witness.commits) > 2, 'more effects were committed over the life of the system than the limit of its budget'
    assert flow.dest.budget_state('budget-main') == {'max_effects': 2, 'used_effects': 2}

    # route A: authority and destination both restored to a state before the effect: the same effect commits again
    (tmp_path / 'a').mkdir()
    world = ChainState(tmp_path / 'a', monkeypatch)
    authority, destination = world.authority_snapshot(), world.destination_snapshot('older-destination.sqlite')
    assert executed(world.execute()[0])
    world.authority_restore(authority)
    world.destination_restore(destination)
    assert world.effects() == 0
    res, exc = world.execute()
    assert exc is None and (res.status, res.newly_executed) == ('executed', True)
    assert world.witness.commits == [world.flow.d.effect_id] * 2, 'one effect identity, committed twice over the life of the system'
    assert world.effects() == 1


# ================================================================================================ TC-L17-028
def _unavailable(*args, **kwargs):
    raise ConnectionError('input unavailable')


def _unreadable(*args, **kwargs):
    raise sqlite3.OperationalError('unable to open database file')


class FailureWorld:
    """One request on route A or B and one modelled failure of an input it depends on. ``inject`` makes the input unavailable,
    ``restore`` brings it back."""

    def __init__(self, label, tmp_path, monkeypatch):
        self.label = label
        self.route = ROUTE_OF[label]
        tmp_path.mkdir(exist_ok=True)
        if self.route == 'A':
            self.flow = W.route_a(tmp_path, monkeypatch)
            assert self.flow.d.result == 'authorized'
        else:
            self.flow = W.route_b(tmp_path, effect_nos=(1,), budget_max=1)
            self.part = self.flow.parts[0]
        self.saved = None

    # ---- the request
    def execute(self):
        f = self.flow
        if self.route == 'A':
            return run_a(f, f.p, f.d, f.env)
        return W.execute_b(f, self.part)

    def effects(self):
        return len(W.destination_effects(self.flow))

    # ---- the six failures
    def inject(self):
        f = self.flow
        if self.label == 'resolver_unavailable':
            self.saved = f.r.authority_context
            f.r.authority_context = _unavailable
        elif self.label == 'grant_row_missing':
            with sqlite3.connect(Path(f.dest.path)) as db:
                db.execute('DELETE FROM effective_grants_v1')
        elif self.label == 'permission_set_unavailable':
            with sqlite3.connect(Path(f.dest.path)) as db:
                db.execute('UPDATE effective_grants_v1 SET permissions_json=NULL')
        elif self.label == 'budget_row_unavailable':
            with sqlite3.connect(Path(f.dest.path)) as db:
                self.saved = db.execute('SELECT * FROM effect_budgets_v1').fetchall()
                db.execute('DELETE FROM effect_budgets_v1')
        elif self.label == 'evidence_status_unavailable':
            f.dest.set_evidence_state('urn:cognous:evidence:atomic', state='unknown')
        elif self.label == 'destination_unreadable':
            f.dest._connect = _unreadable

    def restore(self):
        f = self.flow
        if self.label == 'resolver_unavailable':
            f.r.authority_context = self.saved
        elif self.label in ('grant_row_missing', 'permission_set_unavailable'):
            b = f.d.binding
            f.dest.set_effective_grant(principal=f.p.principal, grant_id=b.grant_id, revision=b.grant_revision, permissions=f.p.requested_permissions)
        elif self.label == 'budget_row_unavailable':
            with sqlite3.connect(Path(f.dest.path)) as db:
                db.executemany('INSERT INTO effect_budgets_v1 VALUES (?,?,?)', self.saved)
        elif self.label == 'evidence_status_unavailable':
            f.dest.set_evidence_state('urn:cognous:evidence:atomic', state='current')
        elif self.label == 'destination_unreadable':
            del f.dest._connect


ROUTE_OF = {'resolver_unavailable': 'A', 'grant_row_missing': 'A', 'permission_set_unavailable': 'A',
            'budget_row_unavailable': 'B', 'evidence_status_unavailable': 'B', 'destination_unreadable': 'A'}
FAILURES = list(ROUTE_OF)
# the request is refused before any attempt is recorded (True) or fails inside the commit after an attempt was recorded (False)
BEFORE_ATTEMPT = {'resolver_unavailable': True, 'grant_row_missing': False, 'permission_set_unavailable': False,
                  'budget_row_unavailable': True, 'evidence_status_unavailable': True, 'destination_unreadable': True}


def view(res, exc):
    if res is None:
        return {'raised': exc.split(':')[0]}
    return {'status': res.status, 'attempted': res.attempted, 'newly_executed': res.newly_executed, 'error': res.error}


@wiki_case('TC-L17-028')
@pytest.mark.parametrize('label', FAILURES)
def test_wiki_l17_028_six_modelled_failures_each_refuse_or_hold_and_none_authorizes(tmp_path, monkeypatch, label):
    # positive control on the same construction: without the failure the request executes
    control = FailureWorld(label, tmp_path / 'control', monkeypatch)
    res, exc = control.execute()
    assert exc is None and res.status == 'executed' and control.effects() == 1
    world = FailureWorld(label, tmp_path / 'failure', monkeypatch)
    world.inject()
    res, exc = world.execute()
    out = view(res, exc)
    assert out.get('status') != 'executed' and not out.get('newly_executed'), out
    assert out.get('status') in (None, 'denied', 'failed'), out
    assert not (res is not None and res.acknowledged), out
    assert world.effects() == 0, 'no effect is made while the input is unavailable'
    if world.route == 'B':
        assert world.flow.dest.claim_state(world.part.claim.claim_id) == 'issued', 'the claim is not consumed'
    if label == 'resolver_unavailable':
        # a new decision while the resolver is away is a hold, not an authorization
        again = world.flow.f.decide(world.flow.p, now=_chain().NOW)
        assert again.result == 'hold' and again.binding is None and again.reasons == ['status_unreadable'], (again.result, again.reasons)
    if label == 'destination_unreadable':
        assert exc is not None and 'OperationalError' in exc, 'an unreadable destination raises: nothing is reported as done'


@wiki_case('TC-L17-028')
@pytest.mark.parametrize('label', FAILURES)
def test_wiki_l17_028_after_the_input_returns_the_same_request_executes_once(tmp_path, monkeypatch, label):
    world = FailureWorld(label, tmp_path, monkeypatch)
    world.inject()
    first, exc = world.execute()
    assert world.effects() == 0
    world.restore()
    second, exc2 = world.execute()
    if BEFORE_ATTEMPT[label]:
        assert exc2 is None and second.status == 'executed' and second.newly_executed, view(second, exc2)
        assert world.effects() == 1
        # a repeat adds nothing
        third, exc3 = world.execute()
        assert third is not None and not third.newly_executed
        assert world.effects() == 1
        return
    # Known limit, asserted as a limit: a failure inside the commit leaves a recorded attempt. The input is back, but the same
    # request is still refused: absence of the effect does not make a retry of that attempt eligible. A new, separately
    # approved request (new correlation, hence a new effect identity) executes once.
    assert exc2 is None and second.status == 'denied' and not second.newly_executed
    assert 'observed absence does not establish retry eligibility after a prior attempt' in (second.error or ''), second.error
    assert world.effects() == 0
    recon = world.flow.executor.reconcile(world.flow.env, now=_chain().NOW)
    assert (recon.result, recon.retry_eligible) == ('observed_absent', False)
    p2, d2, env2 = request_a(world.flow, 'after-return')
    assert d2.result == 'authorized' and d2.effect_id != world.flow.d.effect_id
    res3, exc3 = run_a(world.flow, p2, d2, env2)
    assert exc3 is None and executed(res3)
    assert world.effects() == 1


@wiki_case('TC-L17-028')
def test_wiki_l17_028_error_after_commit_is_reported_unknown_not_denied(tmp_path, monkeypatch):
    # route B: the read of the destination right after COMMIT fails
    (tmp_path / 'b').mkdir()
    flow = W.route_b(tmp_path / 'b', effect_nos=(1,), budget_max=1)
    part = flow.parts[0]
    state = {'down': False}
    flow.dest.stage_hook = lambda stage: state.__setitem__('down', True) if stage == 'after_commit' else None
    original = flow.dest.observe_bound

    def observe_bound(snapshot):
        if state['down']:
            raise ConnectionError('observer unavailable')
        return original(snapshot)
    flow.dest.observe_bound = observe_bound
    res, exc = W.execute_b(flow, part)
    assert exc is None and (res.status, res.attempted, res.acknowledged) == ('unknown', True, False), view(res, exc)
    assert len(W.destination_effects(flow)) == 1 and flow.dest.claim_state(part.claim.claim_id) == 'consumed'
    again, _ = W.execute_b(flow, part)
    assert not again.newly_executed and len(W.destination_effects(flow)) == 1

    # route A: the acknowledgement is lost and the observer is away from the point of the commit on
    (tmp_path / 'a').mkdir()
    fa = W.route_a(tmp_path / 'a', monkeypatch)
    observer = {'down': False}
    commit, observe, observe_bound = fa.dest.commit, fa.dest.observe, fa.dest.observe_bound

    def commit_then_away(snapshot, **kwargs):
        try:
            return commit(snapshot, **kwargs)
        finally:
            observer['down'] = True

    def guarded(read):
        def call(arg):
            if observer['down']:
                raise ConnectionError('observer unavailable')
            return read(arg)
        return call
    fa.dest.commit, fa.dest.observe, fa.dest.observe_bound = commit_then_away, guarded(observe), guarded(observe_bound)
    res, exc = W.execute_a(fa, simulate='lost_ack')
    assert exc is None and (res.status, res.attempted, res.acknowledged, res.observed_state) == ('unknown', True, False, 'unknown'), view(res, exc)
    assert len(W.destination_effects(fa)) == 1
    retry, exc = W.execute_a(fa)
    assert exc is None and retry.status == 'denied' and not retry.newly_executed and len(W.destination_effects(fa)) == 1
    # a lost acknowledgement with a working observer is never reported as a denial either
    (tmp_path / 'c').mkdir()
    fc = W.route_a(tmp_path / 'c', monkeypatch)
    res, exc = W.execute_a(fc, simulate='lost_ack')
    assert exc is None and res.status == _h().lost_ack_status() and res.status != 'denied' and not res.acknowledged


@wiki_case('TC-L17-028')
@pytest.mark.parametrize('label', FAILURES)
def test_wiki_l17_028_failure_records_state_refuse_or_hold_as_the_resulting_protection(tmp_path, monkeypatch, label):
    world = FailureWorld(label, tmp_path, monkeypatch)
    world.inject()
    res, exc = world.execute()
    f = world.flow
    summary = None if label == 'destination_unreadable' else W.destination_summary(f)
    if label == 'resolver_unavailable':
        f.f.decide(f.p, now=_chain().NOW)
        rec = journal(f)
        assert [d.result for d in rec.decisions] == ['authorized', 'hold'] and rec.decisions[-1].reasons == ['status_unreadable']
        assert len(rec.refusals) == 1 and rec.refusals[0].stage == 'effect_time_revalidation'
        assert_typed_reasons(rec.refusals[0].reasons)
        assert [fr[:3] for fr in summary['failures']] == [('authority_hold', 'admission_rejected', 'pre_dispatch')]
    elif label in ('grant_row_missing', 'permission_set_unavailable'):
        code = {'grant_row_missing': 'effective_grant_changed_at_commit', 'permission_set_unavailable': 'effective_grant_permissions_unavailable'}[label]
        assert [a['events'] for a in summary['attempts']] == [[('attempted', None), ('failed', code)]]
        assert summary['effects'] == []
    elif label in ('budget_row_unavailable', 'evidence_status_unavailable'):
        detail = {'budget_row_unavailable': 'authoritative effect budget unavailable', 'evidence_status_unavailable': 'authoritative evidence state invalid'}[label]
        assert [fr for fr in summary['failures']] == [('authority_hold', 'current_authority_rejected', 'pre_dispatch', detail)]
        assert summary['attempts'] == [] and summary['effects'] == []
    else:
        # negative fact, kept: with the destination unreadable nothing can be written to it, and the control-plane journal holds
        # only the earlier authorized decision; the failure is visible to the caller as an exception, not as a retained record
        assert exc is not None and 'OperationalError' in exc
        rec = journal(f)
        assert [d.result for d in rec.decisions] == ['authorized'] and rec.refusals == [] and rec.attempts == []
        del f.dest._connect
        assert W.destination_summary(f)['failures'] == [] and W.destination_effects(f) == []
    # in every case no retained record says the request was authorized for effect or executed
    if world.route == 'A':
        rec = journal(f)
        assert all(a.status != 'executed' for a in rec.attempts)
    states = [] if summary is None else [e['state'] for e in summary['effects']]
    assert states == []
