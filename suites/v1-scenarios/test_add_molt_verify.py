"""Addendum row ADD-MOLT-VERIFY - the four open verify items from the Moltbook addenda, probed at the frozen pins.

SPDX-License-Identifier: Apache-2.0

The addenda carried four claims taken from public replies or code reading and marked VERIFY / not independently confirmed:

  E3-verify  (GR-1654) "evidence freshness is settable per item but grant-status freshness is not" (default 60 s)
  E6-verify  (GR-1662) "test_substitution_prevents_effect compares adapter ID not code digest"
  A-E2-verify / I4-gap (GR-1679, GR-1540) "denied path writes nothing"
  H5-gap     (GR-1500, GR-1517) "effect path does not carry lineage generation"

Each is probed by executing the frozen F5b reference (Control Plane a34c3dc2, runtime e20f92e1, exchange 8be6c6b8); nothing is
read from replies. Results are asserted exactly as observed. Where the observed behaviour contradicts the addendum's requirement
(not merely its claim) the test FAILS and says why. No product code, pin, profile or default is changed; probes use test-time
object mutation only. Every case runs twice and is compared (D3).
"""
from __future__ import annotations

import ast
import dataclasses
import datetime as dt
import sqlite3
from pathlib import Path

import pytest

import _c_2a_helpers as C
import _d02_d05_d09_helpers as H
from _d02_d05_d09_helpers import no_network, pinned_reference  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures('pinned_reference')


def _age(ch, seconds):
    return (ch.NOW - dt.timedelta(seconds=seconds)).isoformat()


def _decide(work, mp, mutate):
    flow = C.flow_a_pre(work, mp, mutate)
    return flow, flow.d.result, sorted(flow.d.reasons or [])


# ------------------------------------------------------------------------------------------------
# E3-verify: per-item freshness
# ------------------------------------------------------------------------------------------------

def test_add_molt_verify_e3_grant_status_freshness_is_not_per_item(request, record_property, tmp_path):
    def trial(work, mp, checks):
        ref = H.reference()
        ch = ref.chain
        from agent_control_plane.bounded import GrantStatus
        n = {'i': 0}

        def run(mutate):
            n['i'] += 1
            d = work / f'c{n["i"]}'
            d.mkdir()
            return _decide(d, mp, mutate)[1:]

        def grant_age(sec, **grant_keys):
            def m(p, r, f, dest):
                next(iter(r.statuses.values())).observed_at = _age(ch, sec)
                r.contexts[ch.PROFILE]['grant'].update(grant_keys)
            return m
        out = {}
        out['grant_age_59s_default'] = run(grant_age(59))
        out['grant_age_61s_default'] = run(grant_age(61))
        checks.equal(out['grant_age_59s_default'], ('authorized', []), 'default bound: a 59 s old grant status is fresh')
        checks.equal(out['grant_age_61s_default'], ('hold', ['grant_status_stale_or_future']), 'default bound 60 s verified: a 61 s old grant status is stale')
        # per-item knobs on the grant item are ignored (30 s old status, 1 s "per-item" bound)
        for key in ('max_age_seconds', 'status_max_age_seconds', 'freshness_seconds'):
            result = run(grant_age(30, **{key: 1}))
            out[f'grant_item_key_{key}'] = result
            checks.expect('grant_status_stale_or_future' not in result[1], f'a per-item grant key {key!r} must not be honoured as a freshness bound (claim: not settable per item); observed {result}')
        fields = sorted(GrantStatus.model_fields)
        out['grant_status_fields'] = fields
        checks.expect(not any('age' in f or 'fresh' in f or 'ttl' in f for f in fields), f'GrantStatus carries no freshness field: {fields}')

        def set_status_attr(p, r, f, dest):
            try:
                next(iter(r.statuses.values())).max_age_seconds = 1
            except Exception as exc:  # pydantic rejects unknown fields
                out['status_object_attr'] = type(exc).__name__
        run(set_status_attr)
        checks.equal(out.get('status_object_attr'), 'ValueError', 'a GrantStatus record cannot be given a per-item freshness attribute')

        # evidence freshness IS per item (obligation max_age_seconds)
        def evidence(max_age, age):
            def m(p, r, f, dest):
                for ob in r.contexts[ch.PROFILE]['requirement']['evidence']:
                    ob['max_age_seconds'] = max_age
                for item in r.evidence.values():
                    item.observed_at = _age(ch, age)
                    ref.sign_evidence(item)
            return m
        out['evidence_bound10_age30'] = run(evidence(10, 30))
        out['evidence_bound60_age30'] = run(evidence(60, 30))
        checks.equal(out['evidence_bound10_age30'], ('hold', ['required_evidence_stale_or_future']), 'evidence freshness is settable per obligation: bound 10 s, age 30 s is stale')
        checks.equal(out['evidence_bound60_age30'], ('authorized', []), 'evidence bound 60 s, age 30 s is fresh')

        # nuance: the host-governed ACTION CLASS bound is honoured, but it is bound into the approval (catalogue digest)
        def klass(max_age, age):
            def m(p, r, f, dest):
                next(iter(r.statuses.values())).observed_at = _age(ch, age)
                prof = f.runtime_authority_profile
                prof.actions[p.action_id] = prof.actions[p.action_id].model_copy(update={'max_status_age_seconds': max_age})
            return m
        out['class_bound5_age30'] = run(klass(5, 30))
        out['class_bound120_age100'] = run(klass(120, 100))
        checks.expect('grant_status_stale_or_future' in out['class_bound5_age30'][1], 'class-level bound 5 s makes a 30 s old grant status stale')
        checks.expect('grant_status_stale_or_future' not in out['class_bound120_age100'][1], 'class-level bound 120 s keeps a 100 s old grant status fresh')
        checks.expect('runtime_authority_approval_mismatch' in out['class_bound5_age30'][1] and 'runtime_authority_approval_mismatch' in out['class_bound120_age100'][1],
                      'changing the class bound also invalidates the approval (catalogue digest is approval-bound): it is a host-governed, re-approval-required knob, not a per-item setting')
        out['finding'] = ('grant-status freshness: constructor default 60 s, or per ACTION CLASS (host-governed, approval-bound) under the runtime-authority profile; '
                          'NOT per grant item. evidence freshness: per obligation. The addendum claim is confirmed with the class-level nuance.')
        return {**out, 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'ADD-MOLT-VERIFY/E3', trial, expect_effects_gate=False)


# ------------------------------------------------------------------------------------------------
# E6-verify: adapter identity vs code digest
# ------------------------------------------------------------------------------------------------

def _adapter_fields(ref):
    import dataclasses as dc
    from engine.safe_executor import ExecutionEnvelope, ExecutionOperation, LocalExecutionPolicy, FrozenEnvelope
    found = {}
    for cls in (ExecutionOperation, ExecutionEnvelope, LocalExecutionPolicy, FrozenEnvelope):
        names = [f.name for f in dc.fields(cls)] if dc.is_dataclass(cls) else []
        found[cls.__name__] = sorted(n for n in names if 'adapter' in n.lower() or 'digest' in n.lower() or 'impl' in n.lower())
    from agent_control_plane.bounded import AuthorizationBinding, RuntimeDecision
    for cls in (AuthorizationBinding, RuntimeDecision):
        found[cls.__name__] = sorted(n for n in cls.model_fields if 'adapter' in n.lower() or 'digest' in n.lower() or 'impl' in n.lower())
    return found


def test_add_molt_verify_e6_adapter_binding_is_id_string_not_code_digest(request, record_property, tmp_path):
    def trial(work, mp, checks):
        ref = H.reference()
        ch = ref.chain
        # (1) the referenced upstream test compares only an adapter id string (AST of the pinned test source)
        src = (ref.paths['control_plane'] / 'tests/test_bounded_authorization.py').read_text()
        fn = next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == 'test_substitution_prevents_effect')
        text = ast.get_source_segment(src, fn)
        checks.expect('adapter_id = "urn:cognous:adapter:other"' in text and 'digest' not in text.split('adapter')[1][:80].lower(),
                      'pinned test_substitution_prevents_effect varies the adapter by id string only')
        # (2) no field of the binding / envelope / policy carries an adapter implementation digest
        fields = _adapter_fields(ref)
        implementation_fields = [(c, f) for c, names in fields.items() for f in names if 'adapter' in f.lower() and any(k in f.lower() for k in ('digest', 'hash', 'revision', 'image', 'impl'))]
        checks.equal(implementation_fields, [], 'no adapter implementation digest/hash/revision field exists in the binding, envelope or policy')
        adapter_named = sorted({f for names in fields.values() for f in names if 'adapter' in f.lower()})
        checks.expect(set(adapter_named) <= {'adapter_id', 'allowed_adapters'}, f'the only adapter-identifying fields are the id and the allow-list: {adapter_named}')
        # (3) executed: changing the adapter id string is refused; the same id with a DIFFERENT implementation is accepted
        (work / 'a').mkdir()
        (work / 'b').mkdir()
        flow = H.flow_a(work / 'a', mp)
        res, exc = H.execute_a(flow, envelope=H.alter_envelope(flow.env, adapter_id='urn:cognous:adapter:other'))
        view = H.result_view(res, exc)
        checks.equal((view.get('status'), len(H.db_summary(flow.dest.path)['effects'])), ('denied', 0), 'a different adapter id string is refused and writes no effect')
        flow2 = H.flow_a(work / 'b', mp)
        base = type(flow2.dest)
        marker = []

        class AlternativeImplementation(base):  # same adapter id, different code
            def commit(self, snapshot, **kwargs):
                marker.append('alternative-implementation-ran')
                return super().commit(snapshot, **kwargs)
        alt_dest = AlternativeImplementation(flow2.dest.root)
        executor = ch.PinnedControlPlaneExecutor(workflow=flow2.f, destination=alt_dest, policy=flow2.executor.policy, observation_clock=lambda: ch.NOW)
        flow2.f.destination = alt_dest
        res2 = executor.execute(envelope=flow2.env, proposal=flow2.p, decision=flow2.d, now=ch.NOW)
        rows = H.db_summary(alt_dest.path)['effects']
        checks.equal((res2.status, marker, len(rows)), ('executed', ['alternative-implementation-ran'], 1),
                     'same adapter id + different implementation class is accepted and executes (only the id string is bound)')
        gate = H.effect_gate(H.db_summary(alt_dest.path), authorized_effect_ids={flow2.env.effect_id}, authorized_digests={H.snapshot_digest(flow2.env)})
        return {'adapter_fields': fields, 'changed_id': view, 'same_id_different_implementation': {'status': res2.status, 'marker': marker, 'effects': len(rows)},
                'finding': 'adapter_id string equality is the only binding at the pin; code equivalence is not established (proposed E6 adapter_digest binding is absent). '
                           'This matches the stated V1 position (no universal attestation; adapter_id is the supported binding). Not a defect against that position.', **gate}
    H.run_case(request, record_property, tmp_path, 'ADD-MOLT-VERIFY/E6', trial)


# ------------------------------------------------------------------------------------------------
# denied path
# ------------------------------------------------------------------------------------------------

def _persisted_a(flow):
    rec = flow.f.records.load()
    s = H.db_summary(flow.dest.path)
    conn = sqlite3.connect(flow.dest.path.resolve().as_uri() + '?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    try:
        failures = [dict(r) for r in conn.execute('SELECT * FROM failure_records_v1 ORDER BY rowid')]
    finally:
        conn.close()
    return rec, s, failures


DENIALS = {
    'effect-time-revalidation-grant-revoked': ('resolver', None),
    'envelope-adapter-substituted': ('envelope', {'adapter_id': 'urn:cognous:adapter:other'}),
    'envelope-target-substituted': ('envelope', {'target': 'urn:cognous:synthetic-account:attacker'}),
    'envelope-amount-altered': ('envelope', {'amount': 999999.0}),
    'envelope-unit-altered': ('envelope', {'unit': 'EUR'}),
}


@pytest.mark.parametrize('case', sorted(DENIALS))
def test_add_molt_verify_denied_path_route_a_persists_refusal_and_executes_nothing(request, record_property, tmp_path, case):
    kind, change = DENIALS[case]

    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        if kind == 'resolver':
            H.revoke_resolver(flow)
            res, exc = H.execute_a(flow)
        else:
            res, exc = H.execute_a(flow, envelope=H.alter_envelope(flow.env, **change))
        view = H.result_view(res, exc)
        rec, s, failures = _persisted_a(flow)
        checks.equal((view.get('status'), view.get('attempted'), view.get('newly_executed')), ('denied', False, False), 'the request is denied and nothing is attempted')
        checks.equal((len(s['effects']), len(s['attempts']), len(rec.attempts)), (0, 0, 0), 'denied path executes nothing: no effect row, no destination attempt, no journal attempt')
        # Addendum A-E2.1/A-E2.2: the refusal is durably recorded with effect id, failed check and input versions
        checks.expect(len(failures) == 1, f'exactly one durable destination failure record for the denial; observed {len(failures)}')
        row = failures[0] if failures else {}
        for column in ('failure_id', 'decision_id', 'effect_id', 'proposal_commitment', 'manifest_digest', 'grant_id', 'grant_revision', 'failure_class', 'reason_code', 'stage', 'detail', 'created_at'):
            checks.expect(row.get(column) not in (None, ''), f'durable failure record lacks {column}')
        checks.equal(row.get('effect_id'), flow.env.effect_id, 'failure record names the effect id of the denied request')
        journal_refusals = [{'stage': x.stage, 'reasons': sorted(x.reasons), 'changed_inputs': len(x.changed_inputs)} for x in rec.refusals]
        if kind == 'resolver':
            checks.equal([x['reasons'] for x in journal_refusals], [['grant_revoked']], 'the Control Plane journal persists the effect-time refusal with its reason')
            checks.expect(all(x['changed_inputs'] >= 1 for x in journal_refusals), 'journal refusal carries the changed input versions')
        else:
            checks.equal(journal_refusals, [], 'envelope-level denials are NOT in the Control Plane journal (only the destination failure record exists)')
        gate = H.effect_gate(s, authorized_effect_ids={flow.env.effect_id})
        return {'case': case, 'view': view, 'journal_refusals': journal_refusals, 'destination_failure_record': {k: (v if k in ('failure_class', 'reason_code', 'stage', 'detail') else bool(v))
                                                                                                                    for k, v in row.items() if k != 'created_at'},
                'proposal_stored_in_full': False, **gate,
                'finding': 'the denied path writes a destination failure record (and a journal refusal for effect-time revalidation) but never an effect or attempt'}
    H.run_case(request, record_property, tmp_path, 'ADD-MOLT-VERIFY/denied-path', trial)


def test_add_molt_verify_denied_path_decision_time_hold_is_persisted_without_effect(request, record_property, tmp_path):
    def trial(work, mp, checks):
        def revoke(p, r, f, dest):
            next(iter(r.statuses.values())).status = 'revoked'
        flow, result, reasons = _decide(work, mp, revoke)
        rec, s, failures = _persisted_a(flow)
        checks.equal(result, 'hold', 'revoked grant at decision time -> hold')
        checks.expect('grant_revoked' in reasons, f'hold reasons name the revocation: {reasons}')
        checks.equal([(x.result, sorted(x.reasons)) for x in rec.decisions], [('hold', reasons)], 'the held decision and its reasons are persisted in the journal')
        checks.expect(len(rec.resolution_checks) >= 1 and len(rec.check_events) >= 1, 'the decision-time resolution inputs are persisted')
        checks.equal((len(s['effects']), len(s['attempts']), len(rec.attempts)), (0, 0, 0), 'a hold executes nothing')
        held = rec.decisions[0].model_dump(mode='json')
        return {'decision': result, 'reasons': reasons, 'resolution_checks_persisted': len(rec.resolution_checks), 'decision_binding_present': held.get('binding') is not None,
                'unauthorized_effects': 0, 'excess_duplicate_effects': 0,
                'finding': 'held decisions are persisted with reasons and resolution inputs; whether the authorization binding is stored for held decisions is recorded, not asserted (E2.2 is a proposal)'}
    H.run_case(request, record_property, tmp_path, 'ADD-MOLT-VERIFY/denied-path', trial)


def test_add_molt_verify_denied_path_route_b_persists_refusal_and_executes_nothing(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        flow.dest.set_grant_status(part.claim.grant_id, status='revoked')
        res, exc = H.execute_b(flow, part)
        view = H.atomic_view(res, exc)
        s = H.db_summary(flow.dest.path)
        failures = flow.dest.failure_history()
        checks.equal((view.get('status'), view.get('attempted')), ('denied', False), 'revoked grant -> denied before dispatch')
        checks.equal((len(s['effects']), len(s['attempts'])), (0, 0), 'nothing executed and no attempt row')
        checks.equal([c for c in s['claims'] if c[0] == 'claim-1'], [('claim-1', 'issued')], 'the claim is not consumed')
        checks.equal(len(failures), 1, 'one durable failure record')
        row = failures[0] if failures else {}
        for column in ('failure_id', 'decision_id', 'effect_id', 'grant_id', 'grant_revision', 'failure_class', 'reason_code', 'stage', 'detail'):
            checks.expect(row.get(column) not in (None, ''), f'durable failure record lacks {column}')
        gate = H.effect_gate(s, authorized_effect_ids={part.env.effect_id})
        return {'view': view, 'failure': {k: row.get(k) for k in ('failure_class', 'reason_code', 'stage', 'detail')}, **gate}
    H.run_case(request, record_property, tmp_path, 'ADD-MOLT-VERIFY/denied-path', trial)


# ------------------------------------------------------------------------------------------------
# H5: lineage generation on the effect path
# ------------------------------------------------------------------------------------------------

def _set_head(path, conversation_id, generation):
    with sqlite3.connect(path, timeout=10, isolation_level=None) as conn:
        conn.execute('BEGIN IMMEDIATE')
        conn.execute('CREATE TABLE IF NOT EXISTS heads(conversation_id TEXT PRIMARY KEY, packet_id TEXT NOT NULL, packet_digest TEXT NOT NULL, state_version INTEGER NOT NULL)')
        conn.execute('INSERT OR REPLACE INTO heads VALUES(?,?,?,?)', (conversation_id, f'packet-v{generation}', f'digest-v{generation}', generation))
        conn.execute('COMMIT')


def test_add_molt_verify_h5_default_effect_path_carries_no_lineage_generation(request, record_property, tmp_path):
    def trial(work, mp, checks):
        ref = H.reference()
        from experiments.odex_gax_imx_reference import gax_ref_runtime as gax
        flow = H.flow_c(work, mp)
        store_path = flow.kwargs['store_path']
        gax.TransactionalExchangeStore(store_path)
        conversation = flow.message['conversation_id']
        _set_head(store_path, conversation, 7)  # the authoritative accepted lineage head has advanced far beyond any generation of this request
        res = H.exchange_run(flow)
        view = H.exchange_view(res)
        rows = H.db_summary(flow.dest.path)['effects']
        checks.equal((view['attempt_status'], len(rows)), ('executed', 1), 'default: the effect commits regardless of the lineage head (no generation is carried on the effect path)')
        # no lineage/generation column in the destination or the effect-bearing objects
        conn = sqlite3.connect(flow.dest.path.resolve().as_uri() + '?mode=ro', uri=True)
        try:
            cols = sorted({f'{t}.{c[1]}' for (t,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table'") for c in conn.execute(f'PRAGMA table_info({t})')
                           if any(k in c[1].lower() for k in ('lineage', 'generation', 'state_version', 'head'))})
        finally:
            conn.close()
        checks.equal(cols, [], 'no lineage/generation/head column in the destination database')
        from engine.safe_executor import ExecutionOperation, ExecutionEnvelope
        names = [f.name for cls in (ExecutionOperation, ExecutionEnvelope) for f in dataclasses.fields(cls)]
        checks.equal([n for n in names if any(k in n.lower() for k in ('lineage', 'generation', 'state_version', 'head'))], [], 'ExecutionOperation/ExecutionEnvelope carry no lineage generation')
        gate = H.effect_gate(H.db_summary(flow.dest.path), authorized_effect_ids={res['execution'].get('effect_id')})
        return {'view': view, 'effects': len(rows), 'lineage_columns': cols, 'authoritative_head_generation': 7,
                'finding': 'by default the effect path neither carries nor re-checks a lineage generation (claim confirmed at the pin); a generation fence exists only as an opt-in parameter', **gate}
    H.run_case(request, record_property, tmp_path, 'ADD-MOLT-VERIFY/H5', trial)


def test_add_molt_verify_h5_optional_fence_in_isolation_refuses_superseded_and_persists_refusal(request, record_property, tmp_path):
    def trial(work, mp, checks):
        H.reference()
        from experiments.odex_gax_imx_reference.generation_fence import GenerationFenceClaim, GenerationFenceRefusal, LineageGenerationFence
        from types import SimpleNamespace
        path = work / 'exchange.sqlite'
        _set_head(path, 'conv-1', 4)
        committed = []

        class Destination:
            def commit(self, snapshot, *, simulate=None):
                committed.append(snapshot.effect_id)
                return {'status': 'applied'}
        fence = LineageGenerationFence(path)
        snap = SimpleNamespace(effect_id='effect-1', payload={'raw': 'secret'})
        with pytest.raises(GenerationFenceRefusal, match='superseded_lineage_generation'):
            fence.commit_if_current(Destination(), snap, GenerationFenceClaim('conv-1', 'effect-1', 3))
        checks.equal(committed, [], 'a superseded generation commits nothing')
        refusals = fence.refusals('conv-1')
        checks.equal([(r['expected_generation'], r['authoritative_generation'], r['reason']) for r in refusals], [(3, 4, 'superseded_lineage_generation')], 'the refusal is persisted before returning')
        checks.expect('secret' not in repr(refusals), 'persisted refusal carries no payload')
        fence.commit_if_current(Destination(), snap, GenerationFenceClaim('conv-1', 'effect-1', 4))
        checks.equal(committed, ['effect-1'], 'the current generation commits')
        restarted = LineageGenerationFence(path)
        counters = restarted.counters('conv-1')
        checks.equal((counters or {}).get('total_refusals'), 1, 'the refusal counter survives a restart (H5.3 restart behaviour)')
        return {'refusals': [(r['expected_generation'], r['authoritative_generation'], r['reason']) for r in refusals], 'counter_after_restart': (counters or {}).get('total_refusals'),
                'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'ADD-MOLT-VERIFY/H5', trial)


@pytest.mark.parametrize('claimed', ['current-generation-4', 'superseded-generation-3'])
def test_add_molt_verify_h5_optional_fence_on_f5b_route_effect_path(request, record_property, tmp_path, claimed):
    """The fence is wired into run_exchange (generation_fence=, lineage_generation=). Executed against the F5b route:

    * a CURRENT-generation effect must commit and a SUPERSEDED one must be refused with a persisted refusal (addendum H5.3).
    Observed (see the evidence): both fail closed with the same TypeError because the fence wrapper does not accept the F5b
    effective-grant commit keyword, so the current generation cannot commit and no refusal row is persisted. The assertions
    state the required behaviour and therefore FAIL; this is a reported composition defect, not a harness problem.
    """
    def trial(work, mp, checks):
        H.reference()
        from experiments.odex_gax_imx_reference import gax_ref_runtime as gax
        from experiments.odex_gax_imx_reference.generation_fence import LineageGenerationFence
        flow = H.flow_c(work, mp)
        store_path = flow.kwargs['store_path']
        gax.TransactionalExchangeStore(store_path)
        conversation = flow.message['conversation_id']
        _set_head(store_path, conversation, 4)
        fence = LineageGenerationFence(store_path)
        generation = 4 if claimed.endswith('4') else 3
        res = H.exchange_run(flow, generation_fence=fence, lineage_generation=generation)
        view = H.exchange_view(res)
        rows = H.db_summary(flow.dest.path)
        conn = sqlite3.connect(flow.dest.path.resolve().as_uri() + '?mode=ro', uri=True)
        try:
            attempt_errors = [r[0] for r in conn.execute('SELECT error FROM attempt_events WHERE error IS NOT NULL')]
        finally:
            conn.close()
        refusals = fence.refusals(conversation)
        if generation == 4:
            checks.equal((view['attempt_status'], len(rows['effects'])), ('executed', 1), f'current generation must commit through the fence; destination attempt errors: {attempt_errors}')
        else:
            checks.equal(len(rows['effects']), 0, 'superseded generation must not commit')
            checks.equal([(r['expected_generation'], r['authoritative_generation'], r['reason']) for r in refusals], [(3, 4, 'superseded_lineage_generation')],
                         f'superseded generation must leave a persisted fence refusal; destination attempt errors: {attempt_errors}')
        gate = H.effect_gate(rows, authorized_effect_ids={res['execution'].get('effect_id')})
        return {'claimed_generation': generation, 'authoritative_generation': 4, 'view': view, 'effects': len(rows['effects']), 'fence_refusals': len(refusals),
                'destination_attempt_errors': attempt_errors, **gate}
    H.run_case(request, record_property, tmp_path, 'ADD-MOLT-VERIFY/H5', trial)
