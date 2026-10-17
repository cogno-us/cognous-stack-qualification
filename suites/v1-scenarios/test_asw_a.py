"""ASW core-12, family A (agent/tool, wiki layer L06): A01 tool-description injection, A02 lookalike adapter,
A03 malformed action/tool schema, A04 unregistered action or agent.

SPDX-License-Identifier: Apache-2.0

Executed against the frozen F5b-repaired seven-component bounded synthetic reference (see ``_asw_helpers``). No LLM, no
network, no payment. Each test runs twice from fresh stores and the normalised observations are compared; the hard gate
(zero unauthorized / excess duplicate effects, independent read-only SQLite observation) applies to every run. A genuine
violation FAILS; nothing is loosened.
"""
from __future__ import annotations

import pytest

import _asw_helpers as A
import _d02_d05_d09_helpers as H
from _asw_helpers import C, no_network, pinned_reference  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures('pinned_reference')

ATTACKER = 'urn:cognous:synthetic-account:attacker'
ROUTINE_ADAPTER = 'urn:cognous:adapter:synthetic-refund-v1'


# =====================================================================================================
# A01  MCP tool-description instruction injection: descriptions remain data; no new authorized action
# =====================================================================================================

def test_asw_a01_poisoned_descriptions_are_data_and_authorize_nothing_new(request, record_property, tmp_path):
    """Positive control with hostile tool/action/agent descriptions in the manifest: the ordinary request still executes
    exactly its own bounded operation; the injected target/amount/permission appear nowhere in authority or destination."""
    def trial(work, mp, checks):
        A.patch_manifest(mp, A.poison_manifest)
        flow = H.flow_a(work, mp)
        checks.equal(flow.d.result, 'authorized', 'the ordinary request is not blocked by hostile description text (false-block control)')
        b = flow.d.binding
        checks.equal((b.target, b.amount, b.unit, list(b.requested_permissions), b.effects),
                     ('urn:cognous:synthetic-account:customer-001', 50.0, 'USD', ['refund.issue.routine'], 1),
                     'the authorized operation is the bound proposal, unchanged by description text')
        res, exc = H.execute_a(flow)
        s = H.db_summary(flow.dest.path)
        A.one_effect_expected(checks, s, 'poisoned descriptions')
        checks.expect(not A.contains_injection_value({'binding': b.model_dump(mode='json'), 'effects': s['effects']}),
                      'no injected value (attacker target / 99999) in the authority binding or the destination state')
        return {'decision': flow.d.result, 'result': A.view_a(res, exc), 'effects': s['effects'], **A.gate_for(s, {flow.env.effect_id})}
    A.run(request, record_property, tmp_path, 'A01', trial)


FOLLOW = {
    'amount': {'amount': 99999.0},
    'target': {'target': ATTACKER},
    'permission': {'requested_permissions': ['refund.issue.high', 'admin']},
    'action': {'action_id': 'urn:cognous:action:refund-issue-high-v1'},
}


@pytest.mark.parametrize('demand', sorted(FOLLOW))
def test_asw_a01_acting_on_the_injected_instruction_yields_no_effect(request, record_property, tmp_path, demand):
    """The deterministic part of 'the agent obeyed the description': a request that does what the injected text demands
    (here against the same hostile manifest) is not authorized and cannot reach the destination."""
    def trial(work, mp, checks):
        A.patch_manifest(mp, A.poison_manifest)
        update = FOLLOW[demand]

        flow = C.flow_a_pre(work, mp, mutate=lambda p, r, f, dest: p.model_copy(update=update))
        decision = A.expect_not_authorized(checks, flow.d, f'obeying injected {demand}')
        res, exc = A.execute_decision(flow)
        checks.expect(A.refused_before_dispatch(res, exc), f'executor refuses the injected-instruction request; observed {A.view_a(res, exc)}')
        s = A.no_effect(checks, flow, f'injected {demand}')
        return {'demand': demand, 'decision': decision, 'result': A.view_a(res, exc), **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'A01', trial)


@pytest.mark.parametrize('field', ['tool_description', 'action_description', 'agent_description', 'tool_external_system'])
def test_asw_a01_description_changed_after_approval_is_refused(request, record_property, tmp_path, field):
    """Rug-pull analogue: the manifest text is swapped for hostile text AFTER the decision; the manifest digest bound to
    the approval no longer matches, so the effect is refused (a tool definition change needs fresh authority)."""
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        m = flow.f.manifest
        if field == 'tool_description':
            m['tools'][0]['description'] = A.INJECTION
        elif field == 'action_description':
            m['actions'][0]['description'] = A.INJECTION
        elif field == 'agent_description':
            m['agent_description'] = A.INJECTION
        else:
            m['tools'][0]['external_system'] = 'attacker-ledger'
        res, exc = H.execute_a(flow)
        checks.expect(A.refused_before_dispatch(res, exc), f'post-approval manifest change must be refused; observed {A.view_a(res, exc)}')
        s = A.no_effect(checks, flow, f'post-approval {field} change')
        journal = H.journal_view(flow)
        checks.expect(any('manifest_digest_mismatch' in r for r in journal['refusals']), f'refusal names the manifest digest mismatch; observed {journal["refusals"]}')
        return {'field': field, 'result': A.view_a(res, exc), 'refusals': journal['refusals'], **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'A01', trial)


# =====================================================================================================
# A02  Registered tool replaced by lookalike adapter: name, type and immutable adapter binding must match
# =====================================================================================================

LOOKALIKES = {
    'case': ROUTINE_ADAPTER.upper(),
    'trailing_space': ROUTINE_ADAPTER + ' ',
    'homoglyph': ROUTINE_ADAPTER.replace('a', 'а', 1),
    'version_bump': ROUTINE_ADAPTER.replace('-v1', '-v2'),
    'prefix': 'x' + ROUTINE_ADAPTER,
    'scheme_case': ROUTINE_ADAPTER.replace('urn:', 'URN:'),
}


def test_asw_a02_positive_control_registered_adapter_executes_once(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        res, exc = H.execute_a(flow)
        checks.equal(A.view_a(res, exc).get('status'), 'executed', 'the registered adapter executes')
        s = H.db_summary(flow.dest.path)
        A.one_effect_expected(checks, s, 'registered adapter')
        return {'result': A.view_a(res, exc), 'effects': s['effects'], **A.gate_for(s, {flow.env.effect_id})}
    A.run(request, record_property, tmp_path, 'A02', trial)


@pytest.mark.parametrize('lookalike', sorted(LOOKALIKES))
def test_asw_a02_route_a_lookalike_adapter_in_envelope_is_refused(request, record_property, tmp_path, lookalike):
    """The executor policy is widened to admit the lookalike so the Control Plane's immutable adapter binding is the refusing control."""
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        env = H.alter_envelope(flow.env, adapter_id=LOOKALIKES[lookalike])
        flow.executor.policy = H.widened_policy(flow.executor.policy, env.operation)
        res, exc = H.execute_a(flow, envelope=env)
        checks.expect(A.refused_before_dispatch(res, exc), f'lookalike adapter {lookalike} must be refused; observed {A.view_a(res, exc)}')
        s = A.no_effect(checks, flow, f'lookalike {lookalike}')
        checks.expect(bool(s['failures']) or s['admission_rejections'] > 0, 'refusal is retained as a destination failure/rejection record')
        return {'lookalike': lookalike, 'result': A.view_a(res, exc), 'failure_records': A.reasons_text(s), **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'A02', trial)


@pytest.mark.parametrize('lookalike', sorted(LOOKALIKES))
def test_asw_a02_decision_does_not_authorize_a_lookalike_adapter(request, record_property, tmp_path, lookalike):
    def trial(work, mp, checks):
        flow = C.flow_a_pre(work, mp, mutate=lambda p, r, f, dest: p.model_copy(update={'adapter_id': LOOKALIKES[lookalike]}))
        decision = A.expect_not_authorized(checks, flow.d, f'lookalike {lookalike}')
        checks.expect('adapter_mismatch' in decision['reasons'], f'decision names the adapter mismatch; observed {decision["reasons"]}')
        res, exc = A.execute_decision(flow)
        checks.expect(A.refused_before_dispatch(res, exc), f'executor refuses; observed {A.view_a(res, exc)}')
        s = A.no_effect(checks, flow, f'lookalike decision {lookalike}')
        return {'lookalike': lookalike, 'decision': decision, 'result': A.view_a(res, exc), **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'A02', trial)


REPLACEMENTS = ['tool_adapter_id', 'tool_name', 'tool_type_external_system', 'action_type']


@pytest.mark.parametrize('replacement', REPLACEMENTS)
def test_asw_a02_registered_tool_replaced_in_manifest_after_decision_is_refused(request, record_property, tmp_path, replacement):
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        m = flow.f.manifest
        if replacement == 'tool_adapter_id':
            m['tools'][0]['adapter_id'] = 'urn:cognous:adapter:lookalike'
        elif replacement == 'tool_name':
            m['tools'][0]['tool_name'] = 'refund_adapter2'
        elif replacement == 'tool_type_external_system':
            m['tools'][0]['external_system'] = 'other-ledger'
        else:
            m['actions'][0]['action_type'] = 'read'
        res, exc = H.execute_a(flow)
        checks.expect(A.refused_before_dispatch(res, exc), f'replaced tool ({replacement}) must be refused; observed {A.view_a(res, exc)}')
        s = A.no_effect(checks, flow, f'replacement {replacement}')
        refusals = H.journal_view(flow)['refusals']
        checks.expect(any('manifest_digest_mismatch' in r for r in refusals), f'refusal names the manifest digest mismatch; observed {refusals}')
        return {'replacement': replacement, 'result': A.view_a(res, exc), 'refusals': refusals, **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'A02', trial)


@pytest.mark.parametrize('lookalike', ['case', 'version_bump', 'homoglyph'])
def test_asw_a02_route_b_claim_binds_the_adapter(request, record_property, tmp_path, lookalike):
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        env = H.alter_envelope(part.env, adapter_id=LOOKALIKES[lookalike])
        from engine.local_authority_effect import AtomicLocalControlPlaneExecutor
        ex = AtomicLocalControlPlaneExecutor(workflow=object(), destination=flow.dest, policy=H.widened_policy(flow.policy, env.operation))
        res, exc = H.execute_b(flow, part, envelope=env, executor=ex)
        checks.expect(A.refused_before_dispatch(res, exc), f'claim-bound adapter must refuse the lookalike; observed {A.view_b(res, exc)}')
        s = H.db_summary(flow.dest.path)
        checks.equal(s['effects'], [], 'no destination effect')
        checks.equal(s['claims'], [('claim-1', 'issued')], 'the claim is not consumed by the lookalike')
        return {'lookalike': lookalike, 'result': A.view_b(res, exc), 'claims': s['claims'], 'failures': A.reasons_text(s), **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'A02', trial)


# =====================================================================================================
# A03  Malformed action/tool schema: reject before adapter side effect
# =====================================================================================================

MALFORMED_PROPOSAL = {
    'amount_text': {'amount': 'fifty'},
    'amount_nan': {'amount': float('nan')},
    'amount_negative': {'amount': -5.0},
    'effects_text': {'effects': 'one'},
    'effects_negative': {'effects': -1},
    'payload_list': {'payload': ['x']},
    'permissions_text': {'requested_permissions': 'refund.issue.routine'},
    'target_int': {'target': 5},
    'unit_none': {'unit': None},
}


@pytest.mark.parametrize('malformation', sorted(MALFORMED_PROPOSAL))
def test_asw_a03_malformed_proposal_is_rejected_by_the_schema(request, record_property, tmp_path, malformation):
    """The typed proposal rejects malformed input at construction (nothing downstream can see it)."""
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        raw = flow.p.model_dump(mode='json', warnings=False)
        raw.update(MALFORMED_PROPOSAL[malformation])
        rejected = None
        try:
            type(flow.p)(**raw)
        except Exception as exc:
            rejected = type(exc).__name__
        checks.equal(rejected, 'ValidationError', f'malformed {malformation} rejected at construction')
        s = A.no_effect(checks, flow, f'malformed {malformation}')
        return {'malformation': malformation, 'rejected_by': rejected, **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'A03', trial)


@pytest.mark.parametrize('malformation', sorted(MALFORMED_PROPOSAL))
def test_asw_a03_unvalidated_malformed_proposal_never_authorizes_or_executes(request, record_property, tmp_path, malformation):
    """Defence in depth: a malformed proposal that bypassed construction (model_copy skips validation) is still held or raises."""
    def trial(work, mp, checks):
        flow = C.flow_a_pre(work, mp)
        p2 = flow.p.model_copy(update=MALFORMED_PROPOSAL[malformation])
        before = len(flow.f.records.load().attempts)
        outcome = None
        try:
            d = flow.f.decide(p2, now=H.reference().chain.NOW)
            outcome = {'decision': d.result, 'reasons': sorted(d.reasons or [])}
            checks.expect(d.result != 'authorized' and d.binding is None, f'a malformed proposal must not be authorized; observed {outcome}')
            flow.p, flow.d = p2, d
            res, exc = A.execute_decision(flow)
            checks.expect(A.refused_before_dispatch(res, exc), f'a malformed proposal must not execute; observed {A.view_a(res, exc)}')
            outcome['executor'] = A.view_a(res, exc)
        except Exception as exc:  # raising before any dispatch is a rejection
            outcome = {'raised': A.norm(f'{type(exc).__name__}: {exc}')}
        s = A.no_effect(checks, flow, f'unvalidated malformed {malformation}')
        checks.equal(len(flow.f.records.load().attempts), before, 'no Control Plane dispatch attempt recorded')
        return {'malformation': malformation, 'outcome': outcome, **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'A03', trial)


PAYLOADS = {
    'missing_required': ({'customer_id': 'customer-001'}, 'missing_required_payload_field'),
    'undeclared_field': ({'customer_id': 'customer-001', 'refund_reason': 'duplicate', 'cmd': 'rm -rf /'}, 'undeclared_payload_field'),
    'empty': ({}, 'missing_required_payload_field'),
    'nested_object': ({'customer_id': {'a': 1}, 'refund_reason': 'duplicate'}, None),
}


@pytest.mark.parametrize('shape', sorted(PAYLOADS))
def test_asw_a03_payload_schema_violation_is_held_and_never_dispatched(request, record_property, tmp_path, shape):
    payload, reason = PAYLOADS[shape]

    def trial(work, mp, checks):
        ch = H.reference().chain
        flow = C.flow_a_pre(work, mp, mutate=lambda p, r, f, d: p.model_copy(update={'payload': payload, 'payload_commitment': ch.commitment(payload)}))
        decision = A.expect_not_authorized(checks, flow.d, f'payload {shape}')
        if reason:
            checks.expect(reason in decision['reasons'], f'decision names {reason}; observed {decision["reasons"]}')
        res, exc = A.execute_decision(flow)
        checks.expect(A.refused_before_dispatch(res, exc), f'executor refuses; observed {A.view_a(res, exc)}')
        s = A.no_effect(checks, flow, f'payload {shape}')
        return {'shape': shape, 'decision': decision, 'result': A.view_a(res, exc), **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'A03', trial)


ENVELOPE_MALFORMATIONS = {
    'amount_text': {'amount': '50'},
    'amount_nan': {'amount': float('nan')},
    'amount_negative': {'amount': -1.0},
    'effects_zero': {'effects': 0},
    'effects_huge': {'effects': 10 ** 9},
    'unit_none': {'unit': None},
    'payload_none': {'payload': None},
    'permissions_text': {'requested_permissions': 'refund.issue.routine'},
    'target_empty': {'target': ''},
}


@pytest.mark.parametrize('malformation', sorted(ENVELOPE_MALFORMATIONS))
def test_asw_a03_route_a_malformed_execution_envelope_is_rejected_before_any_adapter_call(request, record_property, tmp_path, malformation):
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        commits = H.count_commits(flow.dest)
        res, exc = None, None
        try:
            env = H.alter_envelope(flow.env, **ENVELOPE_MALFORMATIONS[malformation])
            res, exc = H.execute_a(flow, envelope=env)
        except Exception as e:  # rejected while constructing the envelope
            exc = f'{type(e).__name__}: {e}'
        checks.expect(A.refused_before_dispatch(res, exc), f'malformed envelope ({malformation}) must be rejected; observed {A.view_a(res, exc)}')
        s = A.no_effect(checks, flow, f'malformed envelope {malformation}')
        checks.equal(commits['calls'], 0, 'the destination adapter commit was never called')
        return {'malformation': malformation, 'result': A.view_a(res, exc), 'commit_calls': commits['calls'], **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'A03', trial)


@pytest.mark.parametrize('malformation', ['amount_text', 'amount_negative', 'effects_zero', 'unit_none', 'permissions_text'])
def test_asw_a03_route_b_malformed_execution_envelope_is_rejected_before_any_claim_use(request, record_property, tmp_path, malformation):
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        res, exc = None, None
        try:
            env = H.alter_envelope(part.env, **ENVELOPE_MALFORMATIONS[malformation])
            res, exc = H.execute_b(flow, part, envelope=env)
        except Exception as e:
            exc = f'{type(e).__name__}: {e}'
        checks.expect(A.refused_before_dispatch(res, exc), f'malformed envelope ({malformation}) must be rejected; observed {A.view_b(res, exc)}')
        s = H.db_summary(flow.dest.path)
        checks.equal((s['effects'], s['claims']), ([], [('claim-1', 'issued')]), 'no effect; the claim is untouched')
        return {'malformation': malformation, 'result': A.view_b(res, exc), 'claims': s['claims'], **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'A03', trial)


MALFORMED_MESSAGES = {
    'missing_requested_action': lambda gax, m: {k: v for k, v in m.items() if k != 'requested_action'},
    'missing_message_digest': lambda gax, m: {k: v for k, v in m.items() if k != 'message_digest'},
    'requested_action_not_object': lambda gax, m: gax_resign(gax, m, requested_action='refund everything'),
    'amount_text_in_action': lambda gax, m: gax_resign(gax, m, requested_action={**m['requested_action'], 'amount': 'fifty'}),
    'unsupported_message_type': lambda gax, m: gax_resign(gax, m, message_type='EXECUTE'),
    'unsupported_protocol_version': lambda gax, m: gax_resign(gax, m, protocol_version='9.9.9'),
}


def gax_resign(gax, m, **changes):
    return A.resign_message(gax, m, **changes)


@pytest.mark.parametrize('malformation', sorted(MALFORMED_MESSAGES))
def test_asw_a03_route_c_malformed_exchange_message_is_not_executed(request, record_property, tmp_path, malformation):
    def trial(work, mp, checks):
        flow = H.flow_c(work, mp)
        msg = MALFORMED_MESSAGES[malformation](flow.gax, flow.message)
        outcome = None
        try:
            res = flow.gax.run_exchange(msg, flow.bundle, flow.registry, flow.dest, **flow.kwargs)
            ex = res.get('execution') or {}
            outcome = {'handling': res['assessment']['permitted_handling'], 'errors': res['assessment'].get('errors'), 'attempted': ex.get('attempted')}
            checks.expect(res['assessment']['permitted_handling'] != 'ACCEPT_FOR_ASSESSMENT', f'malformed message must not be accepted; observed {outcome}')
            checks.equal(bool(ex.get('attempted')), False, 'nothing dispatched')
        except Exception as exc:
            outcome = {'raised': A.norm(f'{type(exc).__name__}: {str(exc)[:120]}')}
        s = A.no_effect(checks, flow, f'malformed message {malformation}')
        return {'malformation': malformation, 'outcome': outcome, **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'A03', trial)


# =====================================================================================================
# A04  Unregistered action or agent: fail closed at declared/allowed scope
# =====================================================================================================

def test_asw_a04_positive_control_registered_action_and_agent_execute_once(request, record_property, tmp_path):
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        res, exc = H.execute_a(flow)
        checks.equal(A.view_a(res, exc).get('status'), 'executed', 'the registered action by the registered agent executes')
        s = H.db_summary(flow.dest.path)
        A.one_effect_expected(checks, s, 'registered action')
        return {'result': A.view_a(res, exc), 'effects': s['effects'], **A.gate_for(s, {flow.env.effect_id})}
    A.run(request, record_property, tmp_path, 'A04', trial)


UNREGISTERED = {
    'action': ({'action_id': 'urn:cognous:action:unregistered-v1'}, None),
    'manifest_id': ({'manifest_id': 'unknown-manifest'}, 'manifest_id_mismatch'),
    'agent_identity': ({'actor': 'urn:cognous:identity:rogue-agent'}, 'proposal_identity_binding_mismatch'),
    'adapter': ({'adapter_id': 'urn:cognous:adapter:unregistered'}, 'adapter_mismatch'),
    'principal': ({'principal': 'urn:cognous:principal:unregistered'}, None),
}


@pytest.mark.parametrize('kind', sorted(UNREGISTERED))
def test_asw_a04_route_a_unregistered_action_or_agent_fails_closed(request, record_property, tmp_path, kind):
    update, reason = UNREGISTERED[kind]

    def trial(work, mp, checks):
        flow = C.flow_a_pre(work, mp, mutate=lambda p, r, f, d: p.model_copy(update=update))
        decision = A.expect_not_authorized(checks, flow.d, f'unregistered {kind}')
        if reason:
            checks.expect(reason in decision['reasons'], f'decision names {reason}; observed {decision["reasons"]}')
        res, exc = A.execute_decision(flow)
        checks.expect(A.refused_before_dispatch(res, exc), f'executor refuses; observed {A.view_a(res, exc)}')
        s = A.no_effect(checks, flow, f'unregistered {kind}')
        return {'kind': kind, 'decision': decision, 'result': A.view_a(res, exc), 'failure_records': A.reasons_text(s), **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'A04', trial)


POLICY_SCOPE = {
    'action': ('action_id', 'urn:cognous:action:unregistered-v1'),
    'adapter': ('adapter_id', 'urn:cognous:adapter:unregistered'),
    'institution': ('institution_id', 'urn:other:institution'),
    'authority_domain': ('authority_domain', 'other-domain'),
    'target_prefix': ('target', 'urn:cognous:other-namespace:customer-001'),
}


@pytest.mark.parametrize('dimension', sorted(POLICY_SCOPE))
def test_asw_a04_route_b_local_allow_list_fails_closed_outside_declared_scope(request, record_property, tmp_path, dimension):
    """The executor's LocalExecutionPolicy is the declared/allowed scope; it is NOT widened here."""
    field, value = POLICY_SCOPE[dimension]

    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        env = H.alter_envelope(part.env, **{field: value})
        res, exc = H.execute_b(flow, part, envelope=env)
        checks.expect(A.refused_before_dispatch(res, exc), f'out-of-scope {dimension} must fail closed; observed {A.view_b(res, exc)}')
        s = H.db_summary(flow.dest.path)
        checks.equal((s['effects'], s['claims']), ([], [('claim-1', 'issued')]), 'no effect; claim untouched')
        return {'dimension': dimension, 'result': A.view_b(res, exc), 'claims': s['claims'], **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'A04', trial)


@pytest.mark.parametrize('dimension', sorted(POLICY_SCOPE))
def test_asw_a04_route_a_local_allow_list_fails_closed_outside_declared_scope(request, record_property, tmp_path, dimension):
    field, value = POLICY_SCOPE[dimension]

    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        env = H.alter_envelope(flow.env, **{field: value})
        res, exc = H.execute_a(flow, envelope=env)
        checks.expect(A.refused_before_dispatch(res, exc), f'out-of-scope {dimension} must fail closed; observed {A.view_a(res, exc)}')
        s = A.no_effect(checks, flow, f'out-of-scope {dimension}')
        return {'dimension': dimension, 'result': A.view_a(res, exc), 'failure_records': A.reasons_text(s), **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'A04', trial)


EXCHANGE_UNREGISTERED = {
    'sender_agent': lambda gax, m: A.resign_message(gax, m, sender='rogue-agent'),
    'recipient_agent': lambda gax, m: A.resign_message(gax, m, recipient='rogue-recipient'),
    'purpose': lambda gax, m: A.resign_message(gax, m, purpose='unregistered_purpose'),
    'action': lambda gax, m: A.resign_message(gax, m, requested_action={**m['requested_action'], 'action_id': 'urn:cognous:action:unregistered-v1'}),
}


@pytest.mark.parametrize('kind', sorted(EXCHANGE_UNREGISTERED))
def test_asw_a04_route_c_unregistered_party_or_action_in_exchange_is_refused(request, record_property, tmp_path, kind):
    def trial(work, mp, checks):
        flow = H.flow_c(work, mp)
        msg = EXCHANGE_UNREGISTERED[kind](flow.gax, flow.message)
        res = flow.gax.run_exchange(msg, flow.bundle, flow.registry, flow.dest, **flow.kwargs)
        ex = res.get('execution') or {}
        checks.equal(res['assessment']['permitted_handling'], 'REFUSE', f'unregistered {kind} refused at assessment')
        checks.equal(bool(ex.get('attempted')), False, 'nothing dispatched')
        s = A.no_effect(checks, flow, f'unregistered exchange {kind}')
        return {'kind': kind, 'errors': res['assessment'].get('errors'), 'reason': ex.get('reason'), **A.gate_for(s)}
    A.run(request, record_property, tmp_path, 'A04', trial)
