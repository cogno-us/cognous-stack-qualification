"""Grant lifetime, expiry, revocation and rotation (routes A and B).

SPDX-License-Identifier: Apache-2.0

Cases (catalog ids): TC-D09-009, TC-D09-016, TC-L02-011, TC-L06-023, TC-L09-003, TC-L09-014.

Each test checks the part of its case that falls inside the declared scope: a grant is usable inside its validity window only,
its status is read at the decision and again at the destination commit, a rotated revision needs a fresh decision, and the
effect budget caps use. Route A is the effective-grant SQLite destination behind the pinned control-plane executor; route B is the
atomic-claim SQLite destination. Everything is synthetic: no network, no payment, no model call, no production effect.

Time semantics asserted here: a grant window is half-open (an instant equal to ``expires_at`` is outside, an instant equal to
``not_before`` is inside).

Not claimed by these tests: requesting, approving, issuing or extending an elevation; revocation in other systems; credential
issuance or refresh; rollback of applied effects; model-provider keys.
"""
from __future__ import annotations

import dataclasses
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

import _wiki_helpers as W
from _wiki_helpers import wiki_case

pytestmark = pytest.mark.usefixtures('pinned_reference')

US = timedelta(microseconds=1)


# ------------------------------------------------------------------------------------------------ local helpers
def _h():
    return W._h()


def _chain():
    return _h().reference().chain


def _c():
    _h()
    import _c_2a_helpers as C
    return C


def _rebind(r, proposal):
    """Independent approval of ``proposal`` (the approval is bound to the proposal commitment)."""
    ch = _chain()
    ctx = r.contexts[ch.PROFILE]
    ref = ctx['grant']['approval_refs'][0]
    r.approvals[ref] = r.approvals[ref].model_copy(update={'proposal_commitment': ch.commitment(proposal.model_dump(mode='json', exclude_none=False))})


def _with_budget(n, grant=None):
    """flow_a_pre mutation: effect budget ``n`` (manifest, requirement and grant agree) and optional grant member overrides."""
    ch = _chain()

    def mutate(p, r, f, dest):
        f.manifest['actions'][0]['effect_limits']['max_effects'] = n
        p = p.model_copy(update={'manifest_digest': ch.commitment(f.manifest)})
        ctx = r.contexts[ch.PROFILE]
        ctx['requirement']['permissions'][0]['max_effects'] = n
        ctx['grant']['permissions'][0]['max_effects'] = n
        for key, value in (grant or {}).items():
            ctx['grant'][key] = value.isoformat() if isinstance(value, datetime) else value
        _rebind(r, p)
        ch.bind_approval(r, f.runtime_authority_profile)
        return p
    return mutate


class SeqA:
    """Route A with an effect budget of ``budget``: each request is decided and executed on its own (approval per request)."""

    def __init__(self, work, monkeypatch, budget=1, grant=None):
        self.ch = _chain()
        self.flow = _c().flow_a_pre(work, monkeypatch, _with_budget(budget, grant))
        self.executor, self.env = _c().best_effort_executor(self.flow)
        self.executor.policy = dataclasses.replace(self.executor.policy, max_effects=budget)
        self.budget = budget
        self.last = (self.flow.p, self.flow.d, self.env)

    @property
    def dest(self):
        return self.flow.dest

    @property
    def resolver(self):
        return self.flow.r

    def request(self, i):
        """Request ``i`` (0 is the flow's own); returns (proposal, decision, envelope)."""
        if i == 0:
            self.last = (self.flow.p, self.flow.d, self.env)
            return self.last
        ch = self.ch
        p = self.flow.p.model_copy(update={'correlation_id': f'wp-a-call-{i}'})
        _rebind(self.flow.r, p)
        d = self.flow.f.decide(p, now=ch.NOW)
        op = dataclasses.replace(self.env.operation, proposal_commitment=ch.commitment(p.model_dump(mode='json')))
        env = dataclasses.replace(self.env, decision_id=d.decision_id, effect_id=d.effect_id, operation=op)
        self.last = (p, d, env)
        return self.last

    def run(self, request, now=None):
        p, d, env = request
        try:
            res = self.executor.execute(envelope=env, proposal=p, decision=d, now=now or self.ch.NOW)
            return res, None
        except Exception as exc:  # a rejection before dispatch
            return None, f'{type(exc).__name__}: {exc}'

    def effects(self):
        return W.destination_summary(self.flow)['effects']

    def journal(self):
        return self.flow.f.records.load()


def _refused(res, exc):
    """Rejected without a destination write: an exception, or a result that attempted nothing and is not executed."""
    return exc is not None or (res is not None and res.status in ('denied', 'failed') and not res.attempted)


def _executed(res, exc):
    return exc is None and res is not None and res.status == 'executed' and res.newly_executed


def _status(res, exc):
    return (res.status if res is not None else f'raised {exc}')


def _rotate(seq_or_flow, revision, *, expires_at=None):
    """Resolver and destination publish grant revision ``revision`` (the grant itself, its status, its approval and the
    destination authority row), as the trusted resolver would. The approval stays required and is bound to the new revision."""
    ch = _chain()
    flow = getattr(seq_or_flow, 'flow', seq_or_flow)
    r = flow.r
    ctx = r.contexts[ch.PROFILE]
    grant = ctx['grant']
    grant['revision'] = revision
    if expires_at is not None:
        grant['expires_at'] = expires_at.isoformat()
    next(iter(r.statuses.values())).revision = revision
    key = grant['approval_refs'][0]
    r.approvals[key] = r.approvals[key].model_copy(update={'grant_revision': revision})
    digest = flow.dest.set_effective_grant(principal=flow.p.principal, grant_id=grant['grant_id'], revision=revision,
                                           permissions=flow.p.requested_permissions)
    ctx['runtime_authority'].update(expected_effective_grant_digest=digest)
    ch.bind_approval(r, flow.c)


def _b(tmp_path, **kwargs):
    return W.route_b(tmp_path, **kwargs)


def _exb(flow, part, **kwargs):
    res, exc = W.execute_b(flow, part, **kwargs)
    return res, exc


def _bview(res, exc):
    return _h().atomic_view(res, exc)


def _b_refused(res, exc):
    return exc is not None or (res is not None and res.status == 'denied' and not res.attempted)


def _claim_window(part):
    return datetime.fromisoformat(part.claim.not_before), datetime.fromisoformat(part.claim.expires_at)


def _b_with_expiry(tmp_path, effect_nos=(1,), seconds=60):
    """Route B whose claims expire ``seconds`` after the destination clock's start (inside the evidence freshness window)."""
    ref = _h().reference()
    h = ref.atomic
    from engine.local_authority_effect import AtomicLocalControlPlaneExecutor
    clock = h.MutableClock(h.BASE)
    dest = _h().hooked_atomic_class()(tmp_path, clock=clock)
    dest.trace = []
    parts = []
    for n in effect_nos:
        env = _h().envelope_with_cap(h, n, len(effect_nos))
        claim = h.make_claim(env, claim_id=f'claim-{n}', budget_id='budget-main', max_effects=len(effect_nos),
                             expires_at=h.BASE + timedelta(seconds=seconds))
        dest.provision_claim(claim)
        parts.append(SimpleNamespace(n=n, env=env, claim=claim))
    policy = dataclasses.replace(h.policy(parts[0].env.operation), max_effects=len(effect_nos))
    executor = AtomicLocalControlPlaneExecutor(workflow=object(), destination=dest, policy=policy)
    return SimpleNamespace(dest=dest, executor=executor, policy=policy, parts=parts, clock=clock, helpers=h, work=tmp_path,
                           expires=h.BASE + timedelta(seconds=seconds))


def _grant_input(record):
    """The grant input that a decision or refusal record retains: (id, revision, status)."""
    rows = [i for i in record.resolution_inputs if i.input_type == 'grant']
    return [(i.input_id, i.observed.get('revision'), i.observed.get('status')) for i in rows]


def _attempt_errors(path):
    conn = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True, timeout=10)
    try:
        return [r[0] for r in conn.execute('SELECT error FROM attempt_events WHERE error IS NOT NULL ORDER BY event_id')]
    finally:
        conn.close()


GRANT_A = 'urn:cognous:grant:routine-1'


# ================================================================================================ TC-D09-009
@wiki_case('TC-D09-009')
def test_wiki_d09_009_effect_inside_grant_window_executes_and_after_window_close_is_refused(tmp_path, monkeypatch):
    (tmp_path / 'a').mkdir()
    (tmp_path / 'b').mkdir()
    ch = _chain()
    # route A: inside the window one effect; at the first instant after the window a second request is refused
    seq = SeqA(tmp_path / 'a', monkeypatch, budget=2)
    res, exc = seq.run(seq.request(0))
    assert _executed(res, exc), _status(res, exc)
    expires = datetime.fromisoformat(seq.resolver.contexts[ch.PROFILE]['grant']['expires_at'])
    res, exc = seq.run(seq.request(1), now=expires)
    assert _refused(res, exc), _status(res, exc)
    assert len(seq.effects()) == 1
    assert 'grant_outside_validity' in {r for x in seq.journal().refusals for r in x.reasons}
    # route B: the same on the atomic-claim destination
    fb = _b_with_expiry(tmp_path / 'b', effect_nos=(1, 2))
    res, exc = _exb(fb, fb.parts[0])
    assert _bview(res, exc)['status'] == 'executed'
    fb.clock.value = fb.expires
    res, exc = _exb(fb, fb.parts[1])
    assert _b_refused(res, exc), _bview(res, exc)
    assert 'execution claim outside validity interval' in _bview(res, exc)['error']
    assert len(W.destination_effects(fb)) == 1


@wiki_case('TC-D09-009')
def test_wiki_d09_009_task_longer_than_window_keeps_the_first_effect_and_refuses_the_next(tmp_path, monkeypatch):
    (tmp_path / 'a').mkdir()
    (tmp_path / 'b').mkdir()
    ch = _chain()
    seq = SeqA(tmp_path / 'a', monkeypatch, budget=3)
    res, exc = seq.run(seq.request(0))
    assert _executed(res, exc)
    before = seq.effects()
    assert [e['state'] for e in before] == ['applied']
    # the task runs past the window: the next effect is refused, the first one stays applied and is not reversed
    expires = datetime.fromisoformat(seq.resolver.contexts[ch.PROFILE]['grant']['expires_at'])
    for i, now in ((1, expires), (2, expires + timedelta(minutes=5))):
        res, exc = seq.run(seq.request(i), now=now)
        assert _refused(res, exc), _status(res, exc)
    assert seq.effects() == before
    # route B
    fb = _b_with_expiry(tmp_path / 'b', effect_nos=(1, 2, 3))
    res, exc = _exb(fb, fb.parts[0])
    assert _bview(res, exc)['status'] == 'executed'
    first = W.destination_effects(fb)
    for part, now in ((fb.parts[1], fb.expires), (fb.parts[2], fb.expires + timedelta(minutes=5))):
        fb.clock.value = now
        res, exc = _exb(fb, part)
        assert _b_refused(res, exc), _bview(res, exc)
    assert W.destination_effects(fb) == first and [e['state'] for e in first] == ['applied']


@wiki_case('TC-D09-009')
def test_wiki_d09_009_missing_or_expired_approval_holds_without_effect(tmp_path, monkeypatch):
    """Approval has no validity date of its own: a missing approval, an approval whose status is not current (stale observation) and
    an approval that is not active each hold; nothing is dispatched."""
    ch = _chain()
    C = _c()
    cases = {}

    def missing(p, r, f, dest):
        r.approvals.clear()
        return p

    def stale(p, r, f, dest):
        a = r.approvals[next(iter(r.approvals))]
        a.observed_at = (ch.NOW - timedelta(hours=1)).isoformat()
        return p

    def inactive(p, r, f, dest):
        r.approvals[next(iter(r.approvals))].status = 'revoked'
        return p

    expected = {'missing': (missing, 'required_approval_missing'), 'stale': (stale, 'approval_status_stale_or_future'),
                'inactive': (inactive, 'approval_not_active')}
    for name, (mutate, reason) in expected.items():
        work = tmp_path / name
        work.mkdir()
        flow = C.flow_a_pre(work, monkeypatch, mutate)
        assert flow.d.result == 'hold' and flow.d.binding is None, (name, flow.d.result)
        assert reason in flow.d.reasons, (name, flow.d.reasons)
        executor, env = C.best_effort_executor(flow)
        try:
            res = executor.execute(envelope=env, proposal=flow.p, decision=flow.d, now=ch.NOW)
            exc = None
        except Exception as e:
            res, exc = None, repr(e)
        assert _refused(res, exc), (name, _status(res, exc))
        summary = W.destination_summary(flow)
        assert summary['effects'] == [], name
        cases[name] = summary['effects']
    # route B: an approval that is no longer active refuses the claim at the destination
    fb = _b(tmp_path / 'b')
    fb.dest.set_approval_status('urn:cognous:approval:atomic', status='revoked')
    res, exc = _exb(fb, fb.parts[0])
    assert _b_refused(res, exc), _bview(res, exc)
    assert 'approval state invalid' in _bview(res, exc)['error']
    assert W.destination_effects(fb) == []


@wiki_case('TC-D09-009')
def test_wiki_d09_009_decision_and_refusal_records_name_grant_id_and_revision(tmp_path, monkeypatch):
    (tmp_path / 'a').mkdir()
    ch = _chain()
    seq = SeqA(tmp_path / 'a', monkeypatch, budget=2)
    p, d, env = seq.request(0)
    assert d.binding.grant_id == GRANT_A and d.binding.grant_revision == '1'
    res, exc = seq.run((p, d, env))
    assert _executed(res, exc)
    expires = datetime.fromisoformat(seq.resolver.contexts[ch.PROFILE]['grant']['expires_at'])
    res, exc = seq.run(seq.request(1), now=expires)
    assert _refused(res, exc)
    record = seq.journal()
    assert [x.result for x in record.decisions] == ['authorized', 'authorized']
    assert all(x.binding.grant_id == GRANT_A and x.binding.grant_revision == '1' for x in record.decisions)
    refusal = record.refusals[-1]
    assert refusal.stage == 'effect_time_revalidation' and 'grant_outside_validity' in refusal.reasons
    assert _grant_input(refusal) == [(GRANT_A, '1', 'active')]
    # route B: the destination failure record carries the grant id and revision beside a typed reason
    fb = _b_with_expiry(tmp_path / 'b')
    fb.clock.value = fb.expires
    res, exc = _exb(fb, fb.parts[0])
    assert _b_refused(res, exc)
    failures = fb.dest.failure_history()
    assert len(failures) == 1
    assert (failures[0]['grant_id'], failures[0]['grant_revision']) == ('urn:cognous:grant:atomic', '1')
    assert (failures[0]['failure_class'], failures[0]['reason_code']) == ('authority_hold', 'current_authority_rejected')


# ================================================================================================ TC-D09-016
def _revocation_sequence_a(tmp_path, monkeypatch, status, calls=8, at=4):
    """Route A: ``calls`` requests in a row; the resolver withdraws the grant (``status``) before call ``at``.
    The decision of call ``at`` is taken before the withdrawal (a stale authorizing decision), later calls are decided afterwards."""
    seq = SeqA(tmp_path, monkeypatch, budget=calls)
    outcomes = []
    for i in range(calls):
        req = seq.request(i)
        if i == at:
            next(iter(seq.resolver.statuses.values())).status = status
        res, exc = seq.run(req)
        outcomes.append((i, req[1].result, _executed(res, exc), _refused(res, exc)))
    return seq, outcomes


@wiki_case('TC-D09-016')
def test_wiki_d09_016_repeated_calls_stop_at_the_first_check_after_revocation_route_a(tmp_path, monkeypatch):
    seq, outcomes = _revocation_sequence_a(tmp_path, monkeypatch, 'revoked')
    assert [o[2] for o in outcomes] == [True] * 4 + [False] * 4
    assert all(o[3] for o in outcomes[4:])
    assert len(seq.effects()) == 4
    # the call whose decision pre-dates the revocation is refused by the effect-time check, later decisions hold
    assert [o[1] for o in outcomes] == ['authorized'] * 5 + ['hold'] * 3
    record = seq.journal()
    assert [x.reasons for x in record.refusals] == [['grant_revoked']]
    assert [x.reasons for x in record.decisions[5:]] == [['grant_revoked']] * 3


@wiki_case('TC-D09-016')
def test_wiki_d09_016_repeated_calls_stop_at_the_first_check_after_revocation_route_b(tmp_path):
    flow = _b(tmp_path, effect_nos=tuple(range(1, 9)))
    outcomes = []
    for i, part in enumerate(flow.parts):
        if i == 4:
            flow.dest.set_grant_status(part.claim.grant_id, status='revoked')
        res, exc = _exb(flow, part)
        outcomes.append(_bview(res, exc))
    assert [o['status'] for o in outcomes] == ['executed'] * 4 + ['denied'] * 4
    assert all(o['attempted'] is False and o['error'] == 'authoritative grant state invalid' for o in outcomes[4:])
    summary = W.destination_summary(flow)
    assert len(summary['effects']) == 4
    assert summary['claims'] == [(f'claim-{n}', 'consumed') for n in range(1, 5)] + [(f'claim-{n}', 'issued') for n in range(5, 9)]


@wiki_case('TC-D09-016')
def test_wiki_d09_016_suspension_and_revocation_both_take_effect_on_the_next_call(tmp_path, monkeypatch):
    for status in ('suspended', 'revoked'):
        a = tmp_path / f'a-{status}'
        a.mkdir()
        seq, outcomes = _revocation_sequence_a(a, monkeypatch, status, calls=4, at=2)
        assert [o[2] for o in outcomes] == [True, True, False, False], status
        assert len(seq.effects()) == 2, status
        assert [x.reasons for x in seq.journal().refusals] == [[f'grant_{status}']], status
        b = tmp_path / f'b-{status}'
        b.mkdir()
        flow = _b(b, effect_nos=(1, 2, 3, 4))
        results = []
        for i, part in enumerate(flow.parts):
            if i == 2:
                flow.dest.set_grant_status(part.claim.grant_id, status=status)
            res, exc = _exb(flow, part)
            results.append(_bview(res, exc)['status'])
        assert results == ['executed', 'executed', 'denied', 'denied'], status
        assert len(W.destination_effects(flow)) == 2, status


@wiki_case('TC-D09-016')
def test_wiki_d09_016_every_refused_call_after_revocation_is_retained_with_grant_id_and_typed_reason(tmp_path, monkeypatch):
    (tmp_path / 'a').mkdir()
    seq, outcomes = _revocation_sequence_a(tmp_path / 'a', monkeypatch, 'revoked')
    record = seq.journal()
    refused_ids = []
    for x in record.refusals:
        assert x.reasons == ['grant_revoked']
        assert _grant_input(x) == [(GRANT_A, '1', 'revoked')]
        refused_ids.append(x.decision_id)
    for x in record.decisions[5:]:
        assert x.result == 'hold' and x.reasons == ['grant_revoked']
        assert _grant_input(x) == [(GRANT_A, '1', 'revoked')]
    # four refused calls in all: one refusal at effect time and three held decisions; the destination retains one failure each
    assert len(refused_ids) + len(record.decisions[5:]) == 4
    failures = W.destination_summary(seq.flow)['failures']
    assert len(failures) == 4 and {f[0] for f in failures} == {'authority_hold'} and {f[1] for f in failures} == {'admission_rejected'}
    # route B
    (tmp_path / 'b').mkdir()
    flow = _b(tmp_path / 'b', effect_nos=(1, 2, 3, 4, 5, 6))
    for i, part in enumerate(flow.parts):
        if i == 3:
            flow.dest.set_grant_status(part.claim.grant_id, status='revoked')
        _exb(flow, part)
    history = flow.dest.failure_history()
    assert len(history) == 3
    assert [(f['decision_id'], f['grant_id']) for f in history] == [(f'decision-{n}', 'urn:cognous:grant:atomic') for n in (4, 5, 6)]
    assert {(f['failure_class'], f['reason_code'], f['stage']) for f in history} == {('authority_hold', 'current_authority_rejected', 'pre_dispatch')}


# ================================================================================================ TC-L02-011
@wiki_case('TC-L02-011')
def test_wiki_l02_011_grant_allows_before_expiry_and_refuses_after_with_an_injected_clock(tmp_path, monkeypatch):
    (tmp_path / 'a').mkdir()
    (tmp_path / 'b').mkdir()
    ch = _chain()
    now = ch.NOW
    # route A: the grant expires one microsecond after the injected instant, then at it
    inside = SeqA(tmp_path / 'a', monkeypatch, budget=1, grant={'expires_at': now + US})
    assert inside.flow.d.result == 'authorized'
    res, exc = inside.run(inside.request(0), now=now)
    assert _executed(res, exc), _status(res, exc)
    (tmp_path / 'a2').mkdir()
    at_expiry = SeqA(tmp_path / 'a2', monkeypatch, budget=1, grant={'expires_at': now})
    assert at_expiry.flow.d.result == 'hold' and 'grant_outside_validity' in at_expiry.flow.d.reasons
    res, exc = at_expiry.run(at_expiry.request(0), now=now)
    assert _refused(res, exc)
    assert at_expiry.effects() == []
    # route B: the injected destination clock decides
    fb = _b_with_expiry(tmp_path / 'b', effect_nos=(1, 2))
    fb.clock.value = fb.expires - US
    res, exc = _exb(fb, fb.parts[0])
    assert _bview(res, exc)['status'] == 'executed'
    fb.clock.value = fb.expires
    res, exc = _exb(fb, fb.parts[1])
    assert _b_refused(res, exc) and 'outside validity interval' in _bview(res, exc)['error']
    assert len(W.destination_effects(fb)) == 1


@wiki_case('TC-L02-011')
def test_wiki_l02_011_decision_taken_before_expiry_is_refused_at_commit_after_expiry(tmp_path, monkeypatch):
    (tmp_path / 'a').mkdir()
    (tmp_path / 'b').mkdir()
    ch = _chain()
    seq = SeqA(tmp_path / 'a', monkeypatch)
    assert seq.flow.d.result == 'authorized'
    expires = datetime.fromisoformat(seq.resolver.contexts[ch.PROFILE]['grant']['expires_at'])
    res, exc = seq.run(seq.request(0), now=expires + timedelta(seconds=1))
    assert _refused(res, exc), _status(res, exc)
    assert seq.effects() == []
    # route B, at the commit boundary: the clock passes the expiry after the caller's checks and before the write transaction
    fb = _b_with_expiry(tmp_path / 'b')

    def hook(stage):
        if stage == 'before_begin':
            fb.clock.value = fb.expires

    fb.dest.stage_hook = hook
    res, exc = _exb(fb, fb.parts[0])
    assert _b_refused(res, exc), _bview(res, exc)
    assert 'outside validity interval' in _bview(res, exc)['error']
    assert fb.dest.trace == ['before_begin', 'after_begin']
    summary = W.destination_summary(fb)
    assert summary['effects'] == [] and summary['claims'] == [('claim-1', 'issued')]


@wiki_case('TC-L02-011')
def test_wiki_l02_011_extended_grant_revision_needs_a_fresh_decision_and_approval_stays_required(tmp_path, monkeypatch):
    (tmp_path / 'a').mkdir()
    (tmp_path / 'b').mkdir()
    ch = _chain()
    seq = SeqA(tmp_path / 'a', monkeypatch)
    old_p, old_d, old_env = seq.request(0)
    assert old_d.binding.grant_revision == '1'
    # the resolver publishes revision 2 with a later expiry; the approval still names revision 1
    ctx = seq.resolver.contexts[ch.PROFILE]
    ctx['grant']['revision'] = '2'
    ctx['grant']['expires_at'] = (ch.NOW + timedelta(hours=3)).isoformat()
    next(iter(seq.resolver.statuses.values())).revision = '2'
    res, exc = seq.run((old_p, old_d, old_env))
    assert _refused(res, exc), 'a decision taken on revision 1 does not carry over to revision 2'
    held = seq.flow.f.decide(old_p, now=ch.NOW)
    assert held.result == 'hold' and 'approval_grant_binding_mismatch' in held.reasons
    assert seq.effects() == []
    # a fresh approval for revision 2 (and the matching destination row) is needed before a fresh decision authorizes
    _rotate(seq, '2', expires_at=ch.NOW + timedelta(hours=3))
    fresh = seq.flow.f.decide(old_p, now=ch.NOW)
    assert fresh.result == 'authorized' and fresh.binding.grant_revision == '2'
    flow2 = SimpleNamespace(p=old_p, r=seq.flow.r, f=seq.flow.f, d=fresh, dest=seq.dest, c=seq.flow.c)
    ex2, env2 = _c().best_effort_executor(flow2)
    res = ex2.execute(envelope=env2, proposal=old_p, decision=fresh, now=ch.NOW)
    assert res.status == 'executed' and res.newly_executed and len(seq.effects()) == 1
    # route B: a claim for the extended revision is not provisioned against the authoritative state of the prior revision
    fb = _b(tmp_path / 'b')
    h = fb.helpers
    env2b = h.envelope(effect_no=2, effect_id='effect-rev2')
    env2b = dataclasses.replace(env2b, operation=dataclasses.replace(env2b.operation, grant_revision='2'))
    claim2 = h.make_claim(env2b, claim_id='claim-rev2', budget_id='budget-main', max_effects=1,
                          expires_at=h.BASE + timedelta(hours=3))
    with pytest.raises(Exception, match='existing authoritative grant state rejects claim provisioning'):
        fb.dest.provision_claim(claim2)
    assert W.destination_summary(fb)['claims'] == [('claim-1', 'issued')]


@wiki_case('TC-L02-011')
def test_wiki_l02_011_expiry_refusal_is_retained_with_its_reason(tmp_path, monkeypatch):
    (tmp_path / 'a').mkdir()
    (tmp_path / 'b').mkdir()
    ch = _chain()
    seq = SeqA(tmp_path / 'a', monkeypatch)
    expires = datetime.fromisoformat(seq.resolver.contexts[ch.PROFILE]['grant']['expires_at'])
    res, exc = seq.run(seq.request(0), now=expires)
    assert _refused(res, exc)
    record = seq.journal()
    assert len(record.refusals) == 1
    assert record.refusals[0].stage == 'effect_time_revalidation' and 'grant_outside_validity' in record.refusals[0].reasons
    # a decision taken after the expiry is retained as a hold with the same typed reason
    held = seq.flow.f.decide(seq.flow.p, now=expires)
    assert held.result == 'hold' and 'grant_outside_validity' in held.reasons
    assert 'grant_outside_validity' in seq.journal().decisions[-1].reasons
    failures = W.destination_summary(seq.flow)['failures']
    assert [(f[0], f[1]) for f in failures] == [('authority_hold', 'admission_rejected')]
    # route B
    fb = _b_with_expiry(tmp_path / 'b')
    fb.clock.value = fb.expires
    res, exc = _exb(fb, fb.parts[0])
    assert _b_refused(res, exc)
    failures = fb.dest.failure_history()
    assert len(failures) == 1
    assert failures[0]['reason_code'] == 'current_authority_rejected' and failures[0]['detail'] == 'execution claim outside validity interval'


# ================================================================================================ TC-L06-023
SIXTY = 60


@pytest.fixture(scope='module')
def sixty_effects(tmp_path_factory):
    """Route A: sixty effects under one grant, then the resolver revokes it and four more calls are made."""
    work = tmp_path_factory.mktemp('sixty')
    mp = pytest.MonkeyPatch()
    try:
        seq = SeqA(work, mp, budget=SIXTY + 4)
        before = []
        for i in range(SIXTY):
            res, exc = seq.run(seq.request(i))
            before.append(_executed(res, exc))
        applied = seq.effects()
        stale = seq.request(SIXTY)  # decided while the grant is still active
        next(iter(seq.resolver.statuses.values())).status = 'revoked'
        after = []
        for k in range(4):
            req = stale if k == 0 else seq.request(SIXTY + k)  # each later request is decided after the revocation
            res, exc = seq.run(req)
            after.append((req[1].result, _refused(res, exc), _executed(res, exc)))
        yield SimpleNamespace(seq=seq, before=before, applied=applied, after=after)
    finally:
        mp.undo()


@wiki_case('TC-L06-023')
def test_wiki_l06_023_sixty_effects_then_revocation_refuses_the_sixty_first_and_every_later_effect(sixty_effects):
    s = sixty_effects
    assert s.before == [True] * SIXTY
    assert len(s.applied) == SIXTY
    assert s.after == [('authorized', True, False), ('hold', True, False), ('hold', True, False), ('hold', True, False)]
    assert len(s.seq.effects()) == SIXTY
    assert [x.reasons for x in s.seq.journal().refusals] == [['grant_revoked']]


@wiki_case('TC-L06-023')
def test_wiki_l06_023_effect_list_from_the_run_record_matches_the_destination_rows_sixty_of_sixty(sixty_effects):
    s = sixty_effects
    record = s.seq.journal()
    acknowledged = {a.effect_id for a in record.attempts if a.status == 'acknowledged'}
    attempted = [a.effect_id for a in record.attempts if a.status == 'attempted']
    destination = {e['effect_id'] for e in s.seq.effects()}
    assert len(acknowledged) == SIXTY and len(attempted) == SIXTY and len(set(attempted)) == SIXTY
    assert acknowledged == destination
    # the run record lists no effect that the destination does not hold, and the destination holds none that the record omits
    assert {a.effect_id for a in record.attempts} == destination


@wiki_case('TC-L06-023')
def test_wiki_l06_023_no_rollback_is_offered_and_applied_effects_remain(sixty_effects):
    s = sixty_effects
    assert [e['state'] for e in s.seq.effects()] == ['applied'] * SIXTY
    assert s.seq.effects() == s.applied  # byte-identical after the revocation and the refused calls
    names = [n for obj in (s.seq.dest, s.seq.executor, s.seq.flow.f) for n in dir(obj) if not n.startswith('_')]
    assert [n for n in names if any(w in n.lower() for w in ('rollback', 'undo', 'compensat', 'reverse'))] == []


# ================================================================================================ TC-L09-003
@wiki_case('TC-L09-003')
def test_wiki_l09_003_expired_grant_is_refused_at_use(tmp_path, monkeypatch):
    (tmp_path / 'a').mkdir()
    (tmp_path / 'b').mkdir()
    ch = _chain()
    for label, grant in (('before-now', {'expires_at': ch.NOW - timedelta(seconds=1)}), ('equal-now', {'expires_at': ch.NOW})):
        work = tmp_path / f'a-{label}'
        work.mkdir()
        seq = SeqA(work, monkeypatch, grant=grant)
        assert seq.flow.d.result == 'hold' and 'grant_outside_validity' in seq.flow.d.reasons, label
        res, exc = seq.run(seq.request(0))
        assert _refused(res, exc), label
        assert seq.effects() == [], label
    # use time after the expiry of an authorizing decision
    seq = SeqA(tmp_path / 'a', monkeypatch)
    res, exc = seq.run(seq.request(0), now=ch.NOW + timedelta(hours=2))
    assert _refused(res, exc) and seq.effects() == []
    # route B
    fb = _b_with_expiry(tmp_path / 'b')
    fb.clock.value = fb.expires + timedelta(hours=1)
    res, exc = _exb(fb, fb.parts[0])
    assert _b_refused(res, exc) and W.destination_effects(fb) == []


@wiki_case('TC-L09-003')
def test_wiki_l09_003_grant_for_another_tenant_or_adapter_is_refused(tmp_path, monkeypatch):
    for n in ('tenant', 'adapter', 'b'):
        (tmp_path / n).mkdir()
    ch = _chain()
    other_adapter = 'urn:cognous:adapter:other'
    # another tenant: the proposal names a tenant the grant was not issued to; the envelope names another tenant
    flow = W.route_a(tmp_path / 'tenant', monkeypatch, tenant='tenant-alpha')
    p2 = flow.p.model_copy(update={'tenant_id': 'tenant-beta'})
    d2 = flow.f.decide(p2, now=ch.NOW)
    assert d2.result != 'authorized' and d2.binding is None
    assert 'grant_tenant_mismatch' in d2.reasons
    env2 = _h().alter_envelope(flow.env, tenant_id='tenant-beta')
    res, exc = W.execute_a(flow, envelope=env2)
    assert _refused(res, exc), _status(res, exc)
    assert W.destination_effects(flow) == []
    # another adapter: a proposal for another adapter is not authorized; the envelope naming another adapter is refused
    flow = W.route_a(tmp_path / 'adapter', monkeypatch)
    p3 = flow.p.model_copy(update={'adapter_id': other_adapter})
    d3 = flow.f.decide(p3, now=ch.NOW)
    assert d3.result != 'authorized' and 'adapter_mismatch' in d3.reasons
    env3 = _h().alter_envelope(flow.env, adapter_id=other_adapter)
    res, exc = W.execute_a(flow, envelope=env3)
    assert _refused(res, exc), _status(res, exc)
    assert W.destination_effects(flow) == []
    # route B: a claim issued for one tenant does not carry the envelope of another tenant or another adapter
    fb = _b(tmp_path / 'b', tenant='tenant-alpha')
    part = fb.parts[0]
    res, exc = _exb(fb, part, envelope=_h().alter_envelope(part.env, tenant_id='tenant-beta'))
    assert _b_refused(res, exc), _bview(res, exc)
    res, exc = _exb(fb, part, envelope=_h().alter_envelope(part.env, adapter_id=other_adapter))
    assert _b_refused(res, exc), _bview(res, exc)
    summary = W.destination_summary(fb)
    assert summary['effects'] == [] and summary['claims'] == [('claim-tenant-1', 'issued')]


@wiki_case('TC-L09-003')
def test_wiki_l09_003_request_beyond_the_grants_permissions_is_refused_at_decision_and_at_commit(tmp_path, monkeypatch):
    for n in ('decision', 'commit', 'b'):
        (tmp_path / n).mkdir()
    ch = _chain()
    widened = ['refund.issue.routine', 'refund.issue.high']

    def widen(p, r, f, dest):
        return p.model_copy(update={'requested_permissions': widened})

    flow = _c().flow_a_pre(tmp_path / 'decision', monkeypatch, widen)
    assert flow.d.result == 'hold' and flow.d.binding is None
    assert 'grant_scope_mismatch' in flow.d.reasons
    executor, env = _c().best_effort_executor(flow)
    try:
        res, exc = executor.execute(envelope=env, proposal=flow.p, decision=flow.d, now=ch.NOW), None
    except Exception as e:
        res, exc = None, repr(e)
    assert _refused(res, exc) and W.destination_effects(flow) == []
    # at commit: the destination's own authority row no longer covers the request
    flow = W.route_a(tmp_path / 'commit', monkeypatch)
    g = flow.d.binding
    flow.dest.set_effective_grant(principal=flow.p.principal, grant_id=g.grant_id, revision=g.grant_revision, permissions=['refund.issue.other'])
    res, exc = W.execute_a(flow)
    assert res is not None and res.status == 'failed' and not res.acknowledged
    assert res.error == 'effective_grant_changed_at_commit'
    assert W.destination_effects(flow) == []
    # route B: the claim binds the permission set; a wider request is refused
    fb = _b(tmp_path / 'b')
    part = fb.parts[0]
    wide = _h().alter_envelope(part.env, requested_permissions=('refund.issue', 'refund.admin'))
    res, exc = _exb(fb, part, envelope=wide)
    assert _b_refused(res, exc), _bview(res, exc)
    assert W.destination_summary(fb)['effects'] == []


@wiki_case('TC-L09-003')
def test_wiki_l09_003_deadline_and_window_boundaries_follow_the_documented_time_semantics(tmp_path, monkeypatch):
    """Validity windows are half-open: ``not_before`` is inside, ``expires_at`` is outside (decision 34-A, 35-B)."""
    ch = _chain()
    now = ch.NOW
    grid = {
        'expires_at one microsecond after the use time': ({'expires_at': now + US}, True),
        'expires_at equal to the use time': ({'expires_at': now}, False),
        'expires_at one microsecond before the use time': ({'expires_at': now - US}, False),
        'not_before equal to the use time': ({'not_before': now}, True),
        'not_before one microsecond after the use time': ({'not_before': now + US}, False),
    }
    for i, (label, (grant, inside)) in enumerate(grid.items()):
        work = tmp_path / f'a{i}'
        work.mkdir()
        seq = SeqA(work, monkeypatch, grant=grant)
        res, exc = seq.run(seq.request(0), now=now)
        if inside:
            assert seq.flow.d.result == 'authorized' and _executed(res, exc), label
            assert len(seq.effects()) == 1, label
        else:
            assert seq.flow.d.result == 'hold' and 'grant_outside_validity' in seq.flow.d.reasons, label
            assert _refused(res, exc) and seq.effects() == [], label
    # route B: the claim window is half-open at the end and refuses before its start
    (tmp_path / 'b').mkdir()
    fb = _b_with_expiry(tmp_path / 'b', effect_nos=(1, 2, 3), seconds=60)
    not_before, expires = _claim_window(fb.parts[0])
    fb.clock.value = expires - US
    assert _bview(*_exb(fb, fb.parts[0]))['status'] == 'executed'
    fb.clock.value = expires
    res, exc = _exb(fb, fb.parts[1])
    assert _b_refused(res, exc) and 'outside validity interval' in _bview(res, exc)['error']
    fb.clock.value = not_before - US
    res, exc = _exb(fb, fb.parts[2])
    assert _b_refused(res, exc) and 'outside validity interval' in _bview(res, exc)['error']
    assert len(W.destination_effects(fb)) == 1


# ================================================================================================ TC-L09-014
@wiki_case('TC-L09-014')
def test_wiki_l09_014_rotated_grant_revision_refuses_a_decision_taken_on_the_prior_revision_at_commit(tmp_path, monkeypatch):
    for n in ('a', 'a-commit', 'b', 'b-commit'):
        (tmp_path / n).mkdir()
    # route A, rotation before use: the control-plane revalidation refuses the decision of revision 1
    seq = SeqA(tmp_path / 'a', monkeypatch)
    req = seq.request(0)
    assert req[1].binding.grant_revision == '1'
    _rotate(seq, '2')
    res, exc = seq.run(req)
    assert _refused(res, exc), _status(res, exc)
    assert [x.reasons for x in seq.journal().refusals] == [['authorization_binding_changed']]
    assert seq.effects() == []
    # route A, rotation landing at the commit boundary: the destination refuses
    flow = W.route_a(tmp_path / 'a-commit', monkeypatch)
    g = flow.d.binding
    original = flow.dest.commit

    def rotate_then_commit(snapshot, **kwargs):
        flow.dest.set_effective_grant(principal=flow.p.principal, grant_id=g.grant_id, revision='2', permissions=flow.p.requested_permissions)
        return original(snapshot, **kwargs)

    flow.dest.commit = rotate_then_commit
    res, exc = W.execute_a(flow)
    assert res is not None and res.status == 'failed' and res.error == 'effective_grant_changed_at_commit'
    assert W.destination_effects(flow) == []
    # route B: a claim issued for revision 1 is refused once revision 2 is active, before and at the commit boundary
    fb = _b(tmp_path / 'b')
    part = fb.parts[0]
    fb.dest.set_grant_status(part.claim.grant_id, status='active', revision='2')
    res, exc = _exb(fb, part)
    assert _b_refused(res, exc) and _bview(res, exc)['error'] == 'authoritative grant state invalid'
    fb2 = _b(tmp_path / 'b-commit')
    part2 = fb2.parts[0]

    def hook(stage):
        if stage == 'before_begin':
            fb2.dest.set_grant_status(part2.claim.grant_id, status='active', revision='2')

    fb2.dest.stage_hook = hook
    res, exc = _exb(fb2, part2)
    assert _b_refused(res, exc)
    assert fb2.dest.trace == ['before_begin', 'after_begin']
    assert W.destination_effects(fb) == [] and W.destination_effects(fb2) == []


@wiki_case('TC-L09-014')
def test_wiki_l09_014_decisions_taken_after_rotation_execute_once(tmp_path, monkeypatch):
    ch = _chain()
    seq = SeqA(tmp_path, monkeypatch, budget=3)
    res, exc = seq.run(seq.request(0))
    assert _executed(res, exc)
    _rotate(seq, '2')
    p = seq.flow.p.model_copy(update={'correlation_id': 'wp-a-after-rotation'})
    _rebind(seq.flow.r, p)
    d = seq.flow.f.decide(p, now=ch.NOW)
    assert d.result == 'authorized' and d.binding.grant_revision == '2'
    flow2 = SimpleNamespace(p=p, r=seq.flow.r, f=seq.flow.f, d=d, dest=seq.dest, c=seq.flow.c)
    executor, env = _c().best_effort_executor(flow2)
    executor.policy = dataclasses.replace(executor.policy, max_effects=3)
    first = executor.execute(envelope=env, proposal=p, decision=d, now=ch.NOW)
    assert first.status == 'executed' and first.newly_executed
    again = executor.execute(envelope=env, proposal=p, decision=d, now=ch.NOW)
    assert not again.newly_executed
    effects = seq.effects()
    assert len(effects) == 2 and [e['state'] for e in effects] == ['applied', 'applied']
    assert W.destination_summary(seq.flow)['effective_grants'] == [(GRANT_A, 'active')]


@wiki_case('TC-L09-014')
def test_wiki_l09_014_revoked_grant_is_refused_immediately_and_expired_grant_after_its_deadline(tmp_path, monkeypatch):
    for n in ('rev', 'exp', 'b-rev', 'b-exp'):
        (tmp_path / n).mkdir()
    ch = _chain()
    seq = SeqA(tmp_path / 'rev', monkeypatch)
    req = seq.request(0)
    next(iter(seq.resolver.statuses.values())).status = 'revoked'
    res, exc = seq.run(req)
    assert _refused(res, exc) and seq.effects() == []
    assert [x.reasons for x in seq.journal().refusals] == [['grant_revoked']]
    seq = SeqA(tmp_path / 'exp', monkeypatch, budget=2)
    expires = datetime.fromisoformat(seq.resolver.contexts[ch.PROFILE]['grant']['expires_at'])
    # before the deadline the effect executes; at the deadline instant (expires_at) the next request is refused
    res, exc = seq.run(seq.request(0), now=ch.NOW)
    assert _executed(res, exc)
    res, exc = seq.run(seq.request(1), now=expires)
    assert _refused(res, exc)
    assert len(seq.effects()) == 1
    # route B
    fb = _b(tmp_path / 'b-rev')
    fb.dest.set_grant_status(fb.parts[0].claim.grant_id, status='revoked')
    res, exc = _exb(fb, fb.parts[0])
    assert _b_refused(res, exc) and _bview(res, exc)['error'] == 'authoritative grant state invalid'
    fx = _b_with_expiry(tmp_path / 'b-exp', effect_nos=(1, 2))
    fx.clock.value = fx.expires - US
    assert _bview(*_exb(fx, fx.parts[0]))['status'] == 'executed'
    fx.clock.value = fx.expires
    res, exc = _exb(fx, fx.parts[1])
    assert _b_refused(res, exc)
    assert len(W.destination_effects(fx)) == 1


@wiki_case('TC-L09-014')
def test_wiki_l09_014_effect_budget_acts_as_the_usage_cap(tmp_path, monkeypatch):
    (tmp_path / 'a').mkdir()
    (tmp_path / 'b').mkdir()
    seq = SeqA(tmp_path / 'a', monkeypatch, budget=2)
    results = [seq.run(seq.request(i)) for i in range(3)]
    assert [_executed(*r) for r in results] == [True, True, False]
    assert len(seq.effects()) == 2
    assert 'local cumulative max_effects exhausted' in _attempt_errors(seq.dest.path)
    # route B: the budget row reports used and maximum
    fb = _b(tmp_path / 'b', effect_nos=(1, 2, 3), budget_max=2)
    views = [_bview(*_exb(fb, part)) for part in fb.parts]
    assert [v['status'] for v in views] == ['executed', 'executed', 'denied']
    assert views[2]['error'] == 'authoritative effect budget exhausted'
    assert fb.dest.budget_state('budget-main') == {'max_effects': 2, 'used_effects': 2}
    assert len(W.destination_effects(fb)) == 2
