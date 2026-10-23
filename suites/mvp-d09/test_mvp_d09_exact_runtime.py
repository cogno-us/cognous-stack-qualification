"""D09 supplement for the exact MVP candidate (Runtime ec728da6, Control Plane 0a41faa9): route B + operation identity.

SPDX-License-Identifier: Apache-2.0

Lives in suites/mvp-d09/, deliberately outside suites/v1-scenarios and with no ``test_scn_d09`` in its name, so the frozen V1 SCN-D09
selector (min 32) still matches exactly the original cases. Companion to ``test_scn_d09.py`` (which is unchanged: historical expectations stay intact). Architect MVP2 rulings Q13/Q14:
  Q13  D09 evidence produced at Runtime 4a83b175 does not transfer; the controls are re-executed here and in test_scn_d09.py at the
       exact runtime / Control Plane pair selected by the r13 profile.
  Q14  every inventory failure affecting a supported or potentially reachable effect surface is blocking until corrected or
       conclusively classified; no call site is deleted and no missing-path finding is suppressed.

Two parts.
  1. Static inventory, widened beyond the CALL_PATTERNS of test_scn_d09.py: (a) the exact set of source files that write the
     ``effects`` table (the sink), and (b) every call-site file of the effect entry points, including the Control Plane
     ``workflow.execute`` ingress that the original patterns do not look for. Each file carries a classification.
  2. Negative controls on the MVP route (route B ``AtomicLocalControlPlaneExecutor(operation_identity=True)`` over
     ``OperationIdentityAtomicAuthorityEffectDestination``, real Control Plane decision): direct commit bypass, legacy write path
     refusal through the atomic-profile marker, and the legacy AgentEngine. The tests record observations; Qualification owns verdicts.
"""
from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

import pytest

_SUITES = Path(__file__).resolve().parents[1]
for _p in (_SUITES / 'operation-identity', _SUITES / 'v1-scenarios'):  # helpers and the original declared inventory live there
    sys.path.insert(0, str(_p))
import _d02_d05_d09_helpers as H  # noqa: E402
from _reason_norm import exc_summary  # noqa: E402
from _d02_d05_d09_helpers import no_network, pinned_reference  # noqa: F401,E402  (fixtures)
import test_scn_d09 as D09  # noqa: E402  (the original declared inventory, imported so it is extended and never copied)

pytestmark = pytest.mark.usefixtures('pinned_reference')

OP = 'op-order-100/refund-1'

# Expected identities of the MVP tuple (asserted, not inherited from the selected profile). The Control Plane may be either
# revision of the MVP tuple: 0a41faa9 (hub lock) or 7a4bcd40 (F3-repaired candidate); the runtime must be ec728da6.
EXPECTED_RUNTIME = 'ec728da6dc301a664b331ac8986afd6e850a1273'
ALLOWED_CONTROL_PLANE = ('0a41faa972699f7ec3063967a14cd9bdd3e67d27', '7a4bcd40b3b49e61ff3c294dcca53b52f460b22c')


@pytest.fixture(autouse=True)
def _tuple_is_the_mvp_tuple():
    ref = H.reference()
    rt, cp = ref.pins['runtime']['commit'], ref.pins['control_plane']['commit']
    assert rt == EXPECTED_RUNTIME, f'runtime {rt} is not the MVP runtime {EXPECTED_RUNTIME}'
    assert cp in ALLOWED_CONTROL_PLANE, f'control plane {cp} is not an MVP tuple revision {ALLOWED_CONTROL_PLANE}'

# --- (a) the sink: the only statements that write the effects table at the exact runtime -------------------------------------
EFFECT_WRITE = re.compile(r'\b(?:INSERT(?:\s+OR\s+\w+)?\s+INTO|UPDATE|DELETE\s+FROM)\s+effects\b', re.I)
EXPECTED_EFFECT_WRITERS = {
    'runtime/engine/safe_executor.py': 'DurableRefundDestination.commit (legacy/adapter route; refused on an atomic-profile database by the marker check)',
    'runtime/engine/local_authority_effect.py': 'AtomicAuthorityEffectDestination.execute_claim_atomic (route B; consumes a claim inside BEGIN IMMEDIATE)',
}

# --- (b) entry points: original patterns plus the Control Plane workflow ingress ------------------------------------------------
WIDER_PATTERNS = D09.CALL_PATTERNS + [r'\bworkflow\.execute\(']
NEW_CALL_SITES = {
    'control_plane/src/agent_control_plane/cli_run.py': (
        '`acp run` (console script agent_control_plane.cli:main) -> run_command -> BoundedAuthorizationWorkflow.execute -> '
        'LocalRefundDestination (a local destination.json file in the output directory). Mediated by the workflow decision and grant '
        'revalidation (route "control-plane-local-destination"); it does not touch the route B SQLite destination. NOT declared '
        'excluded (invocation is covered by the D2 branch test test_REFUSED_acp_run*, which together with this declaration closes the item): whether an ordinary client can invoke it is a trusted-host ingress question for the integration profile.'),
}


def _scan(root, rels, patterns):
    found = {}
    for rel in rels:
        for py in sorted((root / rel).glob('*.py')):
            lines = [line for line in py.read_text().splitlines() if not line.lstrip().startswith(('def ', '#'))]
            hits = [p for p in patterns if re.search(p, '\n'.join(lines))]
            if hits:
                found[f'{rel}/{py.name}'] = hits
    return found


def test_d09_mvp_effect_sink_is_exactly_two_writers(request, record_property, tmp_path):
    ref = H.reference()

    def trial(work, mp, checks):
        base = ref.paths['runtime'].parent
        writers = {}
        for rel in ('runtime/engine', 'runtime/examples', 'control_plane/src/agent_control_plane'):
            for py in sorted((base / rel).rglob('*.py')):
                if EFFECT_WRITE.search(py.read_text()):
                    writers[f'{rel}/{py.relative_to(base / rel).as_posix()}'] = True
        checks.equal(sorted(writers), sorted(EXPECTED_EFFECT_WRITERS), 'files that write the effects table are exactly the two declared sinks')
        return {'effect_writers': sorted(writers), 'declared': EXPECTED_EFFECT_WRITERS, 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'D09', trial)


def test_d09_mvp_entry_point_inventory_including_control_plane_cli(request, record_property, tmp_path):
    ref = H.reference()

    def trial(work, mp, checks):
        base = ref.paths['runtime'].parent
        found = _scan(base, ('runtime/engine', 'control_plane/src/agent_control_plane'), WIDER_PATTERNS)
        declared = {**D09.EXPECTED_CALL_SITES, **NEW_CALL_SITES}
        checks.equal(sorted(set(found) - set(declared)), [], 'every effect entry-point file (widened patterns) is declared and classified')
        checks.equal(sorted(set(declared) - set(found)), [], 'every declared entry-point file still exists at the pins')
        runtime = ref.paths['runtime']
        checks.equal((runtime / 'cli').exists(), False, 'no cli/ directory at the runtime pin (legacy CLI removed; nothing to inventory)')
        checks.equal([n for n in ('pyproject.toml', 'setup.py', 'setup.cfg') if (runtime / n).exists()], [],
                     'runtime declares no installable package entry point or console script')
        checks.equal(sorted(p.name for p in (runtime / 'engine').glob('__main__.py')), [], 'engine is not runnable with -m')
        cp_scripts = re.findall(r'^\w[\w-]*\s*=\s*"agent_control_plane\.[^"]+"', (ref.paths['control_plane'] / 'pyproject.toml').read_text(), re.M)
        return {'discovered': found, 'newly_declared': sorted(NEW_CALL_SITES), 'control_plane_console_scripts': cp_scripts,
                'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'D09', trial)


# ------------------------------------------------------------------------------------------------
# route B + operation identity: composed flow over a real Control Plane decision
# ------------------------------------------------------------------------------------------------

def _flow_b_oi(work, mp):
    ref = H.reference()
    from _oi_flow import Flow
    from engine.atomic_local_control_plane_executor import AtomicLocalControlPlaneExecutor
    from engine.operation_identity_atomic_destination import OperationIdentityAtomicAuthorityEffectDestination as Dest
    from engine.safe_executor import snapshot_envelope
    flow = Flow(work, mp, identity=True, wide=False)
    dest = Dest(work / 'atomic', clock=lambda: flow.NOW)
    executor = AtomicLocalControlPlaneExecutor(workflow=flow.f, destination=dest, policy=flow.policy, operation_identity=True)
    claim = executor.provision_claim(proposal=flow.p, decision=flow.d1, now=flow.NOW)
    env = flow.envelope(flow.d1)
    return flow, dest, executor, claim, env, snapshot_envelope(env), ref


def _state(dest):
    summary = H.db_summary(dest.path)
    conn = sqlite3.connect(Path(dest.path).resolve().as_uri() + '?mode=ro', uri=True)
    try:
        summary['operation_effects'] = [tuple(r) for r in conn.execute('SELECT principal_id,authority_domain,operation_id,effect_id FROM operation_effects_v1')]
    finally:
        conn.close()
    return summary


def test_d09_mvp_route_b_supported_path_control(request, record_property, tmp_path):
    """Positive control: the supported route B + operation identity path commits exactly one effect (the flow under test is live)."""
    def trial(work, mp, checks):
        flow, dest, executor, claim, env, snap, _ = _flow_b_oi(work, mp)
        res = executor.execute(envelope=env, claim_id=claim.claim_id)
        after = _state(dest)
        checks.equal((res.status, res.acknowledged), ('executed', True), 'supported route B execution')
        checks.equal([e['effect_id'] for e in after['effects']], [env.effect_id], 'exactly one durable effect')
        checks.equal(after['operation_effects'], [(env.operation.principal, 'customer-refunds', OP, env.effect_id)], 'operation row names the effect')
        return {'status': res.status, 'effects': after['effects'], 'operation_effects': after['operation_effects'], **H.effect_gate(after, authorized_effect_ids={env.effect_id})}
    H.run_case(request, record_property, tmp_path, 'D09', trial)


@pytest.mark.parametrize('variant', ['commit-no-kwargs', 'commit-with-operation-id', 'commit-with-simulate', 'local-executor-execute_snapshot',
                                     'control-plane-adapter-apply'])
def test_d09_mvp_route_b_direct_commit_bypass_is_refused(request, record_property, tmp_path, variant):
    """Direct commit on the route B destination (claim provisioned, never executed) must not create an effect or consume the claim."""
    def trial(work, mp, checks):
        flow, dest, executor, claim, env, snap, ref = _flow_b_oi(work, mp)
        before = _state(dest)
        outcome = {}
        try:
            if variant == 'commit-no-kwargs':
                dest.commit(snap)
            elif variant == 'commit-with-operation-id':
                dest.commit(snap, operation_id=OP)
            elif variant == 'commit-with-simulate':
                dest.commit(snap, simulate='crash_after_commit')
            elif variant == 'local-executor-execute_snapshot':
                from engine.safe_executor import LocalDestinationExecutor
                res = LocalDestinationExecutor(dest, flow.policy).execute_snapshot(snap)
                outcome = {'status': res.status, 'error': res.error}
            else:
                from engine.control_plane_adapter import ControlPlaneRefundDestinationAdapter
                op = env.operation
                adapter = ControlPlaneRefundDestinationAdapter(snapshot=snap, destination=dest, policy=flow.policy,
                                                               trusted_institution_id=op.institution_id, trusted_authority_domain=op.authority_domain,
                                                               observation_clock=lambda: flow.NOW)
                adapter.apply(effect_id=snap.effect_id, grant_id=op.grant_id, max_effects=op.effective_max_effects, target=op.target,
                              amount=op.amount, unit=op.unit, payload=op.payload)
            outcome = outcome or {'raised': None}
        except Exception as exc:
            outcome = {'raised': exc_summary(exc)}
        after = _state(dest)
        checks.equal(after['effects'], [], f'bypass {variant} must not create an effect; observed {outcome}')
        checks.equal([c[1] for c in after.get('claims', [])], ['issued'], 'claim is not consumed by the bypass')
        checks.equal(after.get('claims'), before.get('claims'), 'claim rows identical before and after the bypass')
        checks.equal(after['operation_effects'], [], 'no operation row recorded by the bypass')
        refused = (outcome.get('raised') not in (None, '')) if 'raised' in outcome else outcome.get('status') in ('failed', 'denied')
        checks.expect(refused, f'bypass {variant} must be refused; observed {outcome}')
        return {'variant': variant, 'outcome': outcome, 'claim_states': [c[1] for c in after.get('claims', [])], 'effects': after['effects'], **H.effect_gate(after)}
    H.run_case(request, record_property, tmp_path, 'D09', trial)


@pytest.mark.parametrize('variant', ['legacy-commit', 'legacy-commit-with-operation-id', 'legacy-executor'])
def test_d09_mvp_route_b_legacy_write_path_refused_by_atomic_marker(request, record_property, tmp_path, variant):
    """The legacy DurableRefundDestination opened on the route B database is refused by the atomic marker (safe_executor commit)."""
    def trial(work, mp, checks):
        from engine.safe_executor import DurableRefundDestination, LocalDestinationExecutor
        flow, dest, executor, claim, env, snap, ref = _flow_b_oi(work, mp)
        src = (ref.paths['runtime'] / 'engine/safe_executor.py').read_text()
        checks.expect("authority_effect_profile_v1" in src and 'requires atomic claim execution' in src,
                      'source read: safe_executor.py carries the atomic-marker refusal at the pin')
        legacy = DurableRefundDestination(work / 'atomic')
        outcome = {}
        try:
            if variant == 'legacy-commit':
                legacy.commit(snap)
            elif variant == 'legacy-commit-with-operation-id':
                legacy.commit(snap, operation_id=OP)
            else:
                res = LocalDestinationExecutor(legacy, flow.policy).execute_snapshot(snap)
                outcome = {'status': res.status, 'error': res.error}
            outcome = outcome or {'raised': None}
        except Exception as exc:
            outcome = {'raised': exc_summary(exc)}
        after = _state(dest)
        text = outcome.get('raised') or outcome.get('error') or ''
        checks.expect('requires atomic claim execution' in str(text), f'refusal names the atomic marker; observed {outcome}')
        checks.equal(after['effects'], [], 'no effect through the legacy path')
        checks.equal(after['operation_effects'], [], 'no operation row through the legacy path')
        checks.equal([c[1] for c in after.get('claims', [])], ['issued'], 'claim untouched')
        return {'variant': variant, 'outcome': outcome, 'claim_states': [c[1] for c in after.get('claims', [])], 'effects': after['effects'], **H.effect_gate(after)}
    H.run_case(request, record_property, tmp_path, 'D09', trial)


def test_d09_mvp_route_b_agent_engine_performs_no_effect(request, record_property, tmp_path):
    """The legacy AgentEngine, pointed at the route B state directory, reports no execution and leaves the database unchanged."""
    def trial(work, mp, checks):
        import json
        from engine.engine import AgentEngine
        flow, dest, executor, claim, env, snap, ref = _flow_b_oi(work, mp)
        before = _state(dest)
        perms = work / 'permissions.json'
        perms.write_text(json.dumps({'agent1': ['write']}))
        engine = AgentEngine(str(work / 'atomic'), str(perms), str(work / 'audit.log'))
        res = engine.execute_action('agent1', {'type': 'write', 'target': 'x', 'params': {}})
        after = _state(dest)
        checks.equal((res['status'], res['executed']), ('unsupported', False), 'AgentEngine reports no execution')
        checks.equal(after, before, 'route B database unchanged by AgentEngine')
        return {'status': res['status'], 'executed': res['executed'], 'effects': after['effects'], **H.effect_gate(after)}
    H.run_case(request, record_property, tmp_path, 'D09', trial)
