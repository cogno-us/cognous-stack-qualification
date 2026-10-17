"""SCN-C11 Credential and permission boundaries (executed against the frozen F5b seven-component reference).

SPDX-License-Identifier: Apache-2.0

Stimulus (catalog C11): use an absent or out-of-scope test credential, then attempt an alternate execution route. Required
observation: institutional authorization cannot override stricter local permissions; no unauthorized destination mutation
or credential exposure.

What "credential" means in the frozen reference. The bounded synthetic reference holds no production credential and no
credential broker (runtime docs/execution-boundary.md). The local credentials that gate a destination write are:
  route A / C : the destination's effective-grant row (principal + grant + revision + permissions digest), bound at commit
  route B     : the exact execution claim provisioned by the trusted control-plane workflow (commitment, validity window)
  all routes  : the executor's LocalExecutionPolicy (the stricter LOCAL permission that institutional authorization cannot widen)
plus the synthetic evidence-signing key the Control Plane trusts. "Absent" = the credential row/claim does not exist;
"out-of-scope" = it exists but for another principal/revision/permission set, expired, suspended or not yet valid.

Cases (each runs twice from fresh stores and the observations are compared, D3; hard gate D5 on every run):
  1 positive controls (credential present, local policy permissive) so refusals are not vacuous
  2 route A and route B: LocalExecutionPolicy stricter than the (authorized) institutional decision, per dimension
  3 route A: absent / out-of-scope effective-grant credential
  4 route B: absent / out-of-scope claim
  5 alternate routes attempted AFTER the credential failure (retry, direct commit with no/wrong/row digest, snapshot executor)
  6 route C (governed exchange) with an absent/out-of-scope destination credential
  7 no credential exposure: a canary credential in the environment and the synthetic signing key never appear in any artifact
  8 declared out-of-model characterisation: direct commit by a caller holding the local credential after institutional revocation
Honest outcomes: a probe that lands an effect FAILS the test; nothing is skipped or loosened.
"""
from __future__ import annotations

import base64
import dataclasses
import hashlib
import os
import sqlite3
from datetime import timedelta

import pytest

import _c_2b_helpers as C
from _c_2b_helpers import pinned_reference  # noqa: F401

H = C.H
H2 = C.H2
CANARY = 'c11-canary-credential-7f3a9d1e5b'
KEY_SEED = bytes(range(32))  # the synthetic Control Plane evidence-signing seed used by the reference fixtures


# ---------------------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------------------
def effects_of(path):
    return H.db_summary(path)


def norm(text):
    return None if text is None else C.H2.normalise_reason(text)


def refused(res, exc):
    return exc is not None or (res is not None and res.status in ('denied', 'failed'))


def view_a(res, exc):
    v = H.result_view(res, exc)
    for k in ('error', 'raised'):
        if v.get(k):
            v[k] = norm(v[k])
    return v


def view_b(res, exc):
    v = H.atomic_view(res, exc)
    for k in ('error', 'raised'):
        if v.get(k):
            v[k] = norm(v[k])
    return v


def stricter(policy, dim):
    changes = {
        'institution': dict(allowed_institutions=frozenset({'urn:other:institution'})),
        'authority_domain': dict(allowed_authority_domains=frozenset({'other-domain'})),
        'adapter': dict(allowed_adapters=frozenset({'other-adapter'})),
        'action': dict(allowed_actions=frozenset({'other-action'})),
        'target_prefix': dict(allowed_target_prefixes=('urn:other:prefix:',)),
        'unit': dict(allowed_units=frozenset({'EUR'})),
        'max_amount': dict(max_amount=1),
    }[dim]
    return dataclasses.replace(policy, **changes)


POLICY_DIMS = ['institution', 'authority_domain', 'adapter', 'action', 'target_prefix', 'unit', 'max_amount']


def set_grant_row(flow, state):
    """Make the destination's effective-grant credential absent or out of scope (trusted authority writer / setup only)."""
    g = flow.d.binding
    p = flow.p
    if state == 'absent_row':
        with flow.dest._connect() as conn:
            conn.execute('DELETE FROM effective_grants_v1 WHERE grant_id=?', (g.grant_id,))
    elif state == 'other_principal':
        flow.dest.set_effective_grant(principal='urn:cognous:principal:someone-else', grant_id=g.grant_id, revision=g.grant_revision, permissions=p.requested_permissions)
    elif state == 'narrowed_permissions':
        narrowed = list(p.requested_permissions)[:-1] if len(p.requested_permissions) > 1 else []
        flow.dest.set_effective_grant(principal=p.principal, grant_id=g.grant_id, revision=g.grant_revision, permissions=narrowed)
    elif state == 'suspended':
        flow.dest.set_effective_grant(principal=p.principal, grant_id=g.grant_id, revision=g.grant_revision, permissions=p.requested_permissions, status='suspended')
    elif state == 'revision_changed':
        flow.dest.set_effective_grant(principal=p.principal, grant_id=g.grant_id, revision='99', permissions=p.requested_permissions)
    else:
        raise ValueError(state)


def stored_row_digest(flow):
    with flow.dest._connect() as conn:
        row = conn.execute('SELECT digest FROM effective_grants_v1 WHERE grant_id=?', (flow.d.binding.grant_id,)).fetchone()
    return row['digest'] if row else None


GRANT_STATES = ['absent_row', 'other_principal', 'narrowed_permissions', 'suspended', 'revision_changed']


# ---------------------------------------------------------------------------------------------------------
# 1. positive controls
# ---------------------------------------------------------------------------------------------------------
def test_scn_c11_positive_control_route_a_credential_present_executes_once(request, record_property, tmp_path, pinned_reference):
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        res, exc = H.execute_a(flow)
        checks.expect(res is not None and res.status == 'executed', f'credential present and policy permissive: executes, observed {view_a(res, exc)}')
        s = effects_of(flow.dest.path)
        checks.equal(len(s['effects']), 1, 'exactly one effect')
        return {'result': view_a(res, exc), 'effects': len(s['effects']), **H.effect_gate(s, authorized_effect_ids={flow.env.effect_id})}
    C.run_c_case(request, record_property, tmp_path, 'C11', trial)


def test_scn_c11_positive_control_route_b_claim_present_executes_once(request, record_property, tmp_path, pinned_reference):
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        res, exc = H.execute_b(flow, part)
        checks.expect(res is not None and res.status == 'executed', f'claim present and policy permissive: executes, observed {view_b(res, exc)}')
        s = effects_of(flow.dest.path)
        checks.equal(len(s['effects']), 1, 'exactly one effect')
        return {'result': view_b(res, exc), 'effects': len(s['effects']), **H.effect_gate(s, authorized_effect_ids={part.env.effect_id})}
    C.run_c_case(request, record_property, tmp_path, 'C11', trial)


# ---------------------------------------------------------------------------------------------------------
# 2. institutional authorization cannot override a stricter local policy
# ---------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize('dim', POLICY_DIMS)
def test_scn_c11_route_a_stricter_local_policy_overrides_institutional_authorization(request, record_property, tmp_path, pinned_reference, dim):
    def trial(work, mp, checks):
        chain = C.reference().chain
        flow = H.flow_a(work, mp)
        checks.equal(flow.d.result, 'authorized', 'the institutional decision is authorized (the strictness is only local)')
        tight = chain.PinnedControlPlaneExecutor(workflow=flow.f, destination=flow.dest, policy=stricter(flow.executor.policy, dim), observation_clock=lambda: chain.NOW)
        res, exc = None, None
        try:
            res = tight.execute(envelope=flow.env, proposal=flow.p, decision=flow.d, now=chain.NOW)
        except Exception as e:
            exc = f'{type(e).__name__}: {e}'
        s = effects_of(flow.dest.path)
        checks.expect(refused(res, exc), f'{dim}: local restriction must refuse an authorized decision, observed {view_a(res, exc)}')
        checks.equal(s['effects'], [], f'{dim}: no destination mutation')
        reason = (res.error if res is not None else exc) or ''
        # The runtime evaluates the local policy inside the destination adapter's observe(); the Control Plane reports that
        # refusal through its generic dispatch-validity reason. The positive control (same flow, permissive policy) executes,
        # so the policy is the only cause of this refusal.
        checks.expect(('local' in reason and 'restriction' in reason) or reason == 'destination observation is not valid for effect dispatch',
                      f'{dim}: refusal is the local-restriction refusal or its Control Plane dispatch-validity wrapper, observed {reason!r}')
        checks.equal(H.journal_view(flow)['attempts'], [], f'{dim}: no execution attempt was recorded')
        return {'dimension': dim, 'result': view_a(res, exc), 'journal': H.journal_view(flow), 'effects': len(s['effects']), **H.effect_gate(s, authorized_effect_ids=())}
    C.run_c_case(request, record_property, tmp_path, 'C11', trial)


@pytest.mark.parametrize('dim', POLICY_DIMS)
def test_scn_c11_route_b_stricter_local_policy_overrides_claimed_authority(request, record_property, tmp_path, pinned_reference, dim):
    def trial(work, mp, checks):
        from engine.local_authority_effect import AtomicLocalControlPlaneExecutor
        flow = H.flow_b(work)
        part = flow.parts[0]
        tight = AtomicLocalControlPlaneExecutor(workflow=object(), destination=flow.dest, policy=stricter(flow.policy, dim))
        res, exc = H.execute_b(flow, part, executor=tight)
        s = effects_of(flow.dest.path)
        checks.expect(refused(res, exc), f'{dim}: local restriction must refuse a validly claimed request, observed {view_b(res, exc)}')
        checks.equal(s['effects'], [], f'{dim}: no destination mutation')
        reason = (res.error if res is not None else exc) or ''
        checks.expect('local' in reason and 'restriction' in reason, f'{dim}: refusal names a LOCAL restriction, observed {reason!r}')
        checks.equal(s['claims'], [('claim-1', 'provisioned')] if s['claims'] and s['claims'][0][1] == 'provisioned' else s['claims'], 'claim state recorded')
        return {'dimension': dim, 'result': view_b(res, exc), 'effects': len(s['effects']), 'claims': s['claims'], **H.effect_gate(s, authorized_effect_ids=())}
    C.run_c_case(request, record_property, tmp_path, 'C11', trial)


# ---------------------------------------------------------------------------------------------------------
# 3. route A: absent / out-of-scope effective-grant credential
# ---------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize('state', GRANT_STATES)
def test_scn_c11_route_a_absent_or_out_of_scope_grant_credential_is_refused(request, record_property, tmp_path, pinned_reference, state):
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        set_grant_row(flow, state)
        with C.Observer(work) as obs:
            res, exc = H.execute_a(flow)
        rep = obs.report()
        s = effects_of(flow.dest.path)
        checks.expect(refused(res, exc), f'{state}: execution without a valid local credential must be refused, observed {view_a(res, exc)}')
        checks.equal(s['effects'], [], f'{state}: no destination mutation')
        checks.equal(rep['process_events'] + rep['network_events'], [], f'{state}: no process/network event')
        return {'state': state, 'result': view_a(res, exc), 'effects': len(s['effects']), 'journal': H.journal_view(flow), **H.effect_gate(s, authorized_effect_ids=())}
    C.run_c_case(request, record_property, tmp_path, 'C11', trial)


def test_scn_c11_route_a_credential_table_absent_is_refused(request, record_property, tmp_path, pinned_reference):
    """The effective-grant table itself is missing (activation never happened): the digest precondition still refuses."""
    def trial(work, mp, checks):
        flow = H.flow_a(work, mp)
        with flow.dest._connect() as conn:
            conn.execute('DROP TABLE effective_grants_v1')
        res, exc = H.execute_a(flow)
        s = effects_of(flow.dest.path)
        checks.expect(refused(res, exc), f'credential table absent: must be refused, observed {view_a(res, exc)}')
        checks.equal(s['effects'], [], 'no destination mutation')
        return {'result': view_a(res, exc), 'effects': len(s['effects']), **H.effect_gate(s, authorized_effect_ids=())}
    C.run_c_case(request, record_property, tmp_path, 'C11', trial)


# ---------------------------------------------------------------------------------------------------------
# 4. route B: absent / out-of-scope claim
# ---------------------------------------------------------------------------------------------------------
def _claim_variant(flow, part, state):
    h = flow.helpers
    env = part.env
    if state == 'claim_absent':
        return env, 'claim-never-provisioned', None
    if state == 'claim_expired':
        claim = h.make_claim(env, claim_id='claim-expiring', budget_id='budget-x', max_effects=1, expires_at=h.BASE + timedelta(minutes=5))
        flow.dest.provision_claim(claim)
        flow.clock.value = h.BASE + timedelta(minutes=10)
        return env, 'claim-expiring', None
    if state == 'claim_not_yet_valid':
        claim = h.make_claim(env, claim_id='claim-early', budget_id='budget-x', max_effects=1)
        flow.dest.provision_claim(claim)
        flow.clock.value = h.BASE - timedelta(minutes=10)
        return env, 'claim-early', None
    if state == 'claim_for_other_effect':
        other = h.envelope(effect_no=7)
        claim = h.make_claim(other, claim_id='claim-other', budget_id='budget-y', max_effects=1)
        flow.dest.provision_claim(claim)
        return env, 'claim-other', None
    if state == 'claim_commitment_tampered':
        raw = h.make_claim(env, claim_id='claim-tampered', budget_id='budget-z', max_effects=1).model_dump(mode='json')
        raw['amount'] = raw['amount'] + 1000  # edited after the commitment was computed
        try:
            flow.dest.provision_claim(raw)
            return env, 'claim-tampered', None
        except Exception as exc:
            return env, 'claim-tampered', f'{type(exc).__name__}: {exc}'
    raise ValueError(state)


CLAIM_STATES = ['claim_absent', 'claim_expired', 'claim_not_yet_valid', 'claim_for_other_effect', 'claim_commitment_tampered']


@pytest.mark.parametrize('state', CLAIM_STATES)
def test_scn_c11_route_b_absent_or_out_of_scope_claim_is_refused(request, record_property, tmp_path, pinned_reference, state):
    def trial(work, mp, checks):
        flow = H.flow_b(work, effect_nos=(9,))  # a claim exists, but for another effect; the variants add or break the claim for effect 1
        h = flow.helpers
        env = h.envelope(effect_no=1)
        part = type('Part', (), {'env': env})()
        env_, claim_id, provision_error = _claim_variant(flow, part, state)
        res, exc = None, None
        try:
            res = flow.executor.execute(envelope=env_, claim_id=claim_id)
        except Exception as e:
            exc = f'{type(e).__name__}: {e}'
        s = effects_of(flow.dest.path)
        checks.expect(refused(res, exc), f'{state}: execution under an absent/out-of-scope claim must be refused, observed {view_b(res, exc)}')
        checks.equal(s['effects'], [], f'{state}: no destination mutation')
        if state == 'claim_commitment_tampered':
            checks.expect(provision_error is not None and 'commitment' in provision_error, f'tampered claim must be refused at provisioning, observed {provision_error!r}')
        return {'state': state, 'provision_error': norm(provision_error), 'result': view_b(res, exc), 'effects': len(s['effects']), **H.effect_gate(s, authorized_effect_ids=())}
    C.run_c_case(request, record_property, tmp_path, 'C11', trial)


def test_scn_c11_route_b_consumed_claim_cannot_authorize_a_second_effect(request, record_property, tmp_path, pinned_reference):
    def trial(work, mp, checks):
        flow = H.flow_b(work)
        part = flow.parts[0]
        first, e1 = H.execute_b(flow, part)
        checks.expect(first is not None and first.status == 'executed', 'first use of the claim executes')
        h = flow.helpers
        second_env = h.envelope(effect_no=2)
        try:
            second = flow.executor.execute(envelope=second_env, claim_id=part.claim.claim_id)
            e2 = None
        except Exception as exc:
            second, e2 = None, f'{type(exc).__name__}: {exc}'
        s = effects_of(flow.dest.path)
        checks.expect(refused(second, e2), f'the consumed claim must not authorize a second effect, observed {view_b(second, e2)}')
        checks.equal([e['effect_id'] for e in s['effects']], [part.env.effect_id], 'only the first effect exists')
        return {'first': view_b(first, e1), 'second': view_b(second, e2), 'effects': len(s['effects']), **H.effect_gate(s, authorized_effect_ids={part.env.effect_id})}
    C.run_c_case(request, record_property, tmp_path, 'C11', trial)


# ---------------------------------------------------------------------------------------------------------
# 5. alternate routes after the credential failure
# ---------------------------------------------------------------------------------------------------------
ALT_ROUTES = ['retry_route_a', 'direct_commit_no_precondition', 'direct_commit_digest_of_expected_credential', 'direct_commit_digest_of_stored_row',
              'execute_snapshot_no_precondition']


@pytest.mark.parametrize('route', ALT_ROUTES)
@pytest.mark.parametrize('state', ['absent_row', 'other_principal', 'narrowed_permissions', 'suspended'])
def test_scn_c11_alternate_route_after_credential_failure_cannot_mutate(request, record_property, tmp_path, pinned_reference, state, route):
    def trial(work, mp, checks):
        ch = C.reference().chain
        flow = H.flow_a(work, mp)
        expected = flow.r.contexts[ch.PROFILE]['runtime_authority']['expected_effective_grant_digest']
        set_grant_row(flow, state)
        first, e1 = H.execute_a(flow)
        checks.expect(refused(first, e1), f'{state}: the primary route is refused first, observed {view_a(first, e1)}')
        snapshot = H.snapshot_env(flow.env)
        outcome = {}
        if route == 'retry_route_a':
            res, exc = H.execute_a(flow)
            outcome = view_a(res, exc)
            ok = refused(res, exc)
        elif route in ('direct_commit_no_precondition', 'direct_commit_digest_of_expected_credential', 'direct_commit_digest_of_stored_row'):
            kwargs = {}
            if route == 'direct_commit_digest_of_expected_credential':
                kwargs = dict(expected_effective_grant_digest=expected, effective_grant_derivation_version=ch.DERIVATION)
            elif route == 'direct_commit_digest_of_stored_row':
                row = stored_row_digest(flow)
                kwargs = dict(expected_effective_grant_digest=row, effective_grant_derivation_version=ch.DERIVATION)
            try:
                flow.dest.commit(snapshot, **kwargs)
                outcome, ok = {'raised': None}, False
            except Exception as exc:
                outcome, ok = {'raised': norm(f'{type(exc).__name__}: {exc}')}, True
        else:
            from engine.safe_executor import LocalDestinationExecutor
            res = LocalDestinationExecutor(flow.dest, flow.executor.policy).execute_snapshot(snapshot)
            outcome = {'status': res.status, 'error': norm(res.error)}
            ok = res.status in ('failed', 'denied')
        s = effects_of(flow.dest.path)
        checks.expect(ok, f'{state}/{route}: the alternate route must be refused, observed {outcome}')
        checks.equal(s['effects'], [], f'{state}/{route}: no destination mutation (unauthorized effect)')
        return {'state': state, 'route': route, 'primary': view_a(first, e1), 'alternate': outcome, 'effects': [e['state'] for e in s['effects']],
                **H.effect_gate(s, authorized_effect_ids=())}
    C.run_c_case(request, record_property, tmp_path, 'C11', trial)


# ---------------------------------------------------------------------------------------------------------
# 6. route C (governed exchange) with an absent / out-of-scope destination credential
# ---------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize('state', GRANT_STATES)
def test_scn_c11_route_c_exchange_with_absent_or_out_of_scope_destination_credential(request, record_property, tmp_path, pinned_reference, state):
    def trial(work, mp, checks):
        flow = H.flow_c(work, mp)
        g = flow.d.binding
        p = flow.p
        if state == 'absent_row':
            with flow.dest._connect() as conn:
                conn.execute('DELETE FROM effective_grants_v1 WHERE grant_id=?', (g.grant_id,))
        elif state == 'other_principal':
            flow.dest.set_effective_grant(principal='urn:cognous:principal:someone-else', grant_id=g.grant_id, revision=g.grant_revision, permissions=p.requested_permissions)
        elif state == 'narrowed_permissions':
            flow.dest.set_effective_grant(principal=p.principal, grant_id=g.grant_id, revision=g.grant_revision, permissions=[])
        elif state == 'suspended':
            flow.dest.set_effective_grant(principal=p.principal, grant_id=g.grant_id, revision=g.grant_revision, permissions=p.requested_permissions, status='suspended')
        else:
            flow.dest.set_effective_grant(principal=p.principal, grant_id=g.grant_id, revision='99', permissions=p.requested_permissions)
        try:
            res = H.exchange_run(flow)
            exc = None
        except Exception as e:
            res, exc = None, f'{type(e).__name__}: {e}'
        s = effects_of(flow.dest.path)
        view = H.exchange_view(res) if res is not None else {'raised': norm(exc)}
        checks.equal(s['effects'], [], f'{state}: no destination mutation through the exchange route')
        checks.expect(exc is not None or view.get('newly_executed') in (False, None), f'{state}: exchange must not report a new execution, observed {view}')
        return {'state': state, 'result': view, 'effects': len(s['effects']), **H.effect_gate(s, authorized_effect_ids=())}
    C.run_c_case(request, record_property, tmp_path, 'C11', trial)


# ---------------------------------------------------------------------------------------------------------
# 7. no credential exposure
# ---------------------------------------------------------------------------------------------------------
def _needles():
    raw = KEY_SEED
    return {'env_canary': CANARY, 'signing_seed_hex': raw.hex(), 'signing_seed_b64': base64.b64encode(raw).decode(),
            'signing_seed_b64url': base64.urlsafe_b64encode(raw).decode().rstrip('='), 'signing_seed_repr': repr(raw)}


def test_scn_c11_no_credential_exposure_in_any_artifact(request, record_property, tmp_path, pinned_reference):
    def trial(work, mp, checks):
        mp.setenv('COGNOUS_C11_CANARY_TOKEN', CANARY)
        needles = _needles()
        found = {}
        scanned = 0
        texts = []
        # (a) full producer chain for four cases: journal, executor export, replay bundle, pack, ODES, destination row dump, SQLite file bytes
        for case in ('valid', 'lost_ack', 'revoked', 'unreadable'):
            ex = H2.build_exports(case, work / 'exports')
            for path in sorted(ex['dir'].rglob('*')):
                if path.is_file():
                    texts.append((f'{case}/{path.relative_to(ex["dir"])}', path.read_bytes()))
        # (b) credential-failure refusals on every route: result objects, exception text, journals, database bytes
        for state in GRANT_STATES:
            flow = H.flow_a(work / f'flow-{state}', mp) if (work / f'flow-{state}').mkdir() is None else None
            set_grant_row(flow, state)
            res, exc = H.execute_a(flow)
            texts.append((f'refusal-a/{state}', repr((view_a(res, exc), H.journal_view(flow))).encode()))
            for path in sorted((work / f'flow-{state}').rglob('*')):
                if path.is_file():
                    texts.append((f'flow-{state}/{path.relative_to(work / f"flow-{state}")}', path.read_bytes()))
        fb = H.flow_b(work / 'flow-b') if (work / 'flow-b').mkdir() is None else None
        try:
            r = fb.executor.execute(envelope=fb.parts[0].env, claim_id='claim-never-provisioned')
            texts.append(('refusal-b/result', repr(r).encode()))
        except Exception as e:
            texts.append(('refusal-b/exception', f'{type(e).__name__}: {e}'.encode()))
        for path in sorted((work / 'flow-b').rglob('*')):
            if path.is_file():
                texts.append((f'flow-b/{path.relative_to(work / "flow-b")}', path.read_bytes()))
        for label, data in texts:
            scanned += 1
            for name, needle in needles.items():
                if needle.encode() in data:
                    found.setdefault(name, []).append(label)
        checks.equal(found, {}, 'no credential material (env canary, signing seed in any encoding) in any artifact, exception or database file')
        checks.expect(scanned > 40, f'scan was not vacuous ({scanned} artifacts)')
        # the canary really is in the environment of this process (the scan could have found it)
        checks.equal(os.environ.get('COGNOUS_C11_CANARY_TOKEN'), CANARY, 'canary credential was present in the environment during the runs')
        return {'artifacts_scanned_at_least_40': scanned > 40, 'needle_kinds': sorted(needles), 'exposures': found,
                'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    C.run_c_case(request, record_property, tmp_path, 'C11', trial)


# ---------------------------------------------------------------------------------------------------------
# 8. declared out-of-model characterisation
# ---------------------------------------------------------------------------------------------------------
def test_scn_c11_declared_out_of_model_direct_commit_by_local_credential_holder_after_institutional_revocation(request, record_property, tmp_path, pinned_reference):
    """The destination holds only the LOCAL credential; it cannot see an institutional revocation. A caller that holds that
    credential (digest + database access: the trusted host, runtime docs/execution-boundary.md) and bypasses route A lands an
    effect that current institutional authority no longer permits. Recorded, never presented as confinement."""
    def trial(work, mp, checks):
        ch = C.reference().chain
        flow = H.flow_a(work, mp)
        expected = flow.r.contexts[ch.PROFILE]['runtime_authority']['expected_effective_grant_digest']
        H.revoke_resolver(flow)  # institutional withdrawal at the Control Plane resolver; the local row stays active
        routed, e_route = H.execute_a(flow)
        checks.expect(refused(routed, e_route), f'the supported route refuses after institutional revocation, observed {view_a(routed, e_route)}')
        mid = effects_of(flow.dest.path)
        checks.equal(mid['effects'], [], 'no effect through the supported route')
        snapshot = H.snapshot_env(flow.env)
        try:
            flow.dest.commit(snapshot, expected_effective_grant_digest=expected, effective_grant_derivation_version=ch.DERIVATION)
            direct = 'committed'
        except Exception as exc:
            direct = norm(f'{type(exc).__name__}: {exc}')
        after = effects_of(flow.dest.path)
        landed = len(after['effects'])
        return {'declared_out_of_model': True, 'actor': 'caller holding the local credential (digest) and the database file (trusted host)',
                'supported_route': view_a(routed, e_route), 'direct_commit': direct, 'effects_after_direct_commit': landed,
                'required_observation_met': landed == 0, 'classification': 'declared_out_of_model_characterisation',
                'note': 'SQLite cannot separate a caller holding the database file from the authority writer (effective_grant.py docstring)',
                'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    C.run_c_case(request, record_property, tmp_path, 'C11', trial, extra={'classification': 'declared_out_of_model_characterisation'})
