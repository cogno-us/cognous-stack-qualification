"""Shared bootstrap and harness for scenarios D02 (binding substitution), D05 (partial effect) and
D09 (bypass and interruption).

SPDX-License-Identifier: Apache-2.0

Everything here runs against the FROZEN F5b-repaired seven-component bounded synthetic reference. It never
changes product code, pins, profiles or defaults: the seven component checkouts are verified pristine at
their exact pinned commits before any of their code is imported and again at the end of each module. No
network, payment, model or production effect is used. Linux only (owner decision D2).

Reference layout (the same one ``tools/run_security_runtime.py --prepare-work`` builds)::

    $SCN_COMPONENTS_DIR/{control_plane,runtime,replay,evidence_pack,odes,exchange,manifest}

Optional: ``SCN_HUB_DIR`` = checkout of hub 8517818f (verified pristine when supplied),
``SCN_EVIDENCE_DIR`` = directory that receives one JSON evidence file per test.

Determinism (owner decision D3): every case is executed TWICE from fresh, identical work directories and the
two normalised observations are compared; both runs and the MATCH/MISMATCH assertion are recorded.
Hard gate (D5): zero unauthorized effects and zero excess duplicate effects in every run.
"""
from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import json
import os
import platform
import socket
import sqlite3
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.dont_write_bytecode = True  # a bytecode file inside a pinned checkout would make it non-pristine

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'suites'))
import _pins  # noqa: E402  (the one source of pinned identities: freeze manifest + refreeze overlay)
import _contract_matrix as _matrix  # noqa: E402  (compatibility gate for contract-governed boundaries; the pins stay the tested revisions)
from _reason_norm import exc_summary, normalise_reason  # noqa: E402,F401
PROFILE_PATH = _pins.PROFILE_PATH
from pristine_checkout import require_pristine  # noqa: E402

FROZEN_HUB = _pins.FROZEN_HUB
FROZEN_RUNTIME = _pins.FROZEN_RUNTIME
FROZEN_CONTROL_PLANE = _pins.FROZEN_CONTROL_PLANE
COMPONENT_NAMES = ('control_plane', 'runtime', 'replay', 'evidence_pack', 'odes', 'exchange', 'manifest')
SCENARIO_VERSION = '1.0.0'
_REF = None


def _git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True, timeout=60).strip()



def lost_ack_status():
    """Strict, per-runtime-row expectation of the first-delivery status after a lost acknowledgement.

    A runtime that declares ``execution-attempt-lifecycle`` conformance (the N-1 rule) reports ``reconciled`` once the destination
    is observed applied; an undeclared (older) runtime reports ``unknown``. One value per row, never "either".
    """
    declared = _matrix.declares(reference().paths['runtime'], 'execution-attempt-lifecycle')
    return 'reconciled' if declared else 'unknown'


def reference():
    """Verify the pins, put the reference on sys.path and load the frozen chain harness (idempotent)."""
    global _REF
    if _REF is not None:
        return _REF
    base = os.environ.get('SCN_COMPONENTS_DIR')
    if not base:
        pytest.fail('SCN_COMPONENTS_DIR is not set; the scenarios cannot run against the pinned reference '
                    '(layout: tools/run_security_runtime.py --prepare-work)')
    base = Path(base).resolve()
    profile = json.loads(PROFILE_PATH.read_text())
    assert profile['components']['runtime']['revision'] == FROZEN_RUNTIME
    assert profile['components']['control_plane']['revision'] == FROZEN_CONTROL_PLANE
    # Compatibility gate: the contract-version matrix for components on a declared-contract boundary (their sha pin is the
    # recorded *tested revision*), the sha pin for every other component. Every checkout must be pristine either way.
    gates, matrix_rows = _matrix.admit_components(base, profile['components'], COMPONENT_NAMES, require_pristine,
                                                  lambda p: _git(p, 'rev-parse', 'HEAD'))
    paths, pins = {}, {}
    for name in COMPONENT_NAMES:
        spec = profile['components'][name]
        path = base / name
        paths[name] = path
        pins[name] = {'repository': spec['repository'], 'commit': gates[name]['revision'], 'tree': _git(path, 'rev-parse', 'HEAD^{tree}'),
                      'gate': gates[name]['gate'], 'tested_revision': gates[name]['tested_revision'],
                      'tested_revision_match': gates[name]['tested_revision_match']}
    hub = os.environ.get('SCN_HUB_DIR')
    hub_identity = None
    if hub:
        require_pristine(hub, FROZEN_HUB, 'hub')
        hub_identity = {'repository': 'cogno-us/cognous-open-control-stack', 'commit': FROZEN_HUB, 'verified_in_this_run': True}
    env = os.environ
    env['COGNOUS_SECURITY_RUNTIME_GENERATION'] = profile.get('suite_generation', 'f5b')  # the profile selects the generation (f5b through r2, p4 from r3)
    env['GAX_RUNTIME_COMPATIBILITY_PROFILE'] = profile['exchange_compatibility_profile']
    env['MOLTBOT_SAFE_CONTROL_PLANE_ROOT'] = str(paths['control_plane'])
    env['MOLTBOT_SAFE_ROOT'] = str(paths['runtime'])
    env['UPSTREAM_MANIFEST_EXAMPLE'] = str(paths['manifest'] / 'examples/refund_integration_v1_1.manifest.json')
    order = [paths['control_plane'], paths['control_plane'] / 'src', paths['runtime'], paths['replay'] / 'src',
             paths['evidence_pack'] / 'src', paths['odes'] / 'src', paths['exchange']]
    for entry in reversed(order):
        sys.path.insert(0, str(entry))
    # The qualification repository has its own ``tests`` directory; the control-plane fixtures need theirs.
    loaded = sys.modules.get('tests')
    if loaded is not None and not str(getattr(loaded, '__file__', '') or '').startswith(str(paths['control_plane'])):
        for key in [k for k in sys.modules if k == 'tests' or k.startswith('tests.')]:
            del sys.modules[key]
    spec = importlib.util.spec_from_file_location('scn_d02_d05_d09_chain', ROOT / 'suites/security-runtime/test_security_runtime_chain.py')
    chain = importlib.util.module_from_spec(spec)
    sys.modules['scn_d02_d05_d09_chain'] = chain
    spec.loader.exec_module(chain)  # the frozen harness: integrated(), produce(), exchange_setup()
    atomic_spec = importlib.util.spec_from_file_location(
        'scn_d02_d05_d09_atomic', ROOT / 'suites/cognous-execution-runtime/tests/test_local_authority_effect.py')
    atomic = importlib.util.module_from_spec(atomic_spec)
    sys.modules['scn_d02_d05_d09_atomic'] = atomic
    atomic_spec.loader.exec_module(atomic)  # the frozen atomic-claim fixtures (claims, policy, tenant claims)
    from tests.test_runtime_authority import sign_evidence
    from tests.test_bounded_authorization import POLICY_REF
    ref = SimpleNamespace(paths=paths, pins=pins, matrix_rows=matrix_rows, hub=hub_identity, profile=profile, chain=chain, atomic=atomic,
                          base=base, sign_evidence=sign_evidence, POLICY_REF=POLICY_REF)
    _REF = ref
    return ref


def assert_pins_still_pristine():
    ref = reference()
    for name, path in ref.paths.items():
        require_pristine(path, ref.pins[name]['commit'], name)
    if ref.hub:
        require_pristine(os.environ['SCN_HUB_DIR'], FROZEN_HUB, 'hub')


@pytest.fixture(scope='module')
def pinned_reference():
    """Module fixture: pins verified pristine before use and again after the module's tests."""
    ref = reference()
    yield ref
    assert_pins_still_pristine()


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Containment: attempted IP network access is refused and counted; the count must stay zero."""
    attempts = []
    real_connect = socket.socket.connect

    def refuse(self, address):
        if self.family in (socket.AF_INET, socket.AF_INET6):
            attempts.append(repr(address))
            raise PermissionError('network access is prohibited in the synthetic scenario harness')
        return real_connect(self, address)
    monkeypatch.setattr(socket.socket, 'connect', refuse)
    yield attempts
    assert attempts == [], f'prohibited network access attempted: {attempts}'


# ----------------------------------------------------------------------------------------------
# determinism and evidence
# ----------------------------------------------------------------------------------------------

def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False, default=str).encode()


def digest(value) -> str:
    return 'sha256:' + hashlib.sha256(canonical(value)).hexdigest()


class Checks:
    """Soft assertions: every violated expectation is recorded, so a real violation is reported (FAIL), never hidden."""

    def __init__(self):
        self.violations = []

    def expect(self, condition, message):
        if not condition:
            self.violations.append(message)
        return bool(condition)

    def equal(self, actual, expected, message):
        return self.expect(actual == expected, f'{message}: expected {expected!r}, observed {actual!r}')


def environment_identity():
    ref = reference()
    return {'scenario_version': SCENARIO_VERSION, 'python': sys.version.split()[0], 'platform': platform.platform(),
            'sqlite': sqlite3.sqlite_version, 'components': ref.pins, 'contract_matrix': ref.matrix_rows,
            'hub': ref.hub or {'repository': 'cogno-us/cognous-open-control-stack', 'commit': FROZEN_HUB, 'verified_in_this_run': False},
            'frozen_pins_asserted': {'hub': FROZEN_HUB, 'runtime': FROZEN_RUNTIME, 'control_plane': FROZEN_CONTROL_PLANE},
            'profile': _pins.PROFILE_RELPATH, 'network': 'none', 'paid_model_calls': 0, 'live_effects': 0}


def run_case(request, record_property, tmp_path, scenario, trial, *, expect_effects_gate=True):
    """Execute ``trial(workdir, monkeypatch)`` twice from fresh work directories, compare, record, assert.

    A trial returns an ``observed`` dict containing ``unauthorized_effects`` and ``excess_duplicate_effects``
    (hard gate, D5) and records its own expectations through ``Checks``.
    """
    reference()
    runs = []
    for n in (1, 2):
        work = tmp_path / f'run-{n}'
        work.mkdir()
        checks = Checks()
        mp = pytest.MonkeyPatch()
        try:
            observed = trial(work, mp, checks)
        except Exception as exc:  # harness error is reported as a violation, never as a pass
            observed = {'harness_exception': f'{type(exc).__name__}: {exc}'}
            checks.violations.append(f'harness exception (INCONCLUSIVE, not a pass): {type(exc).__name__}: {exc}')
        finally:
            mp.undo()
        if expect_effects_gate and 'harness_exception' not in observed:
            checks.equal(observed.get('unauthorized_effects'), 0, 'hard gate: unauthorized effects')
            checks.equal(observed.get('excess_duplicate_effects'), 0, 'hard gate: excess duplicate effects')
        runs.append({'run': n, 'observed': observed, 'violations': list(checks.violations)})
    d1, d2 = digest(runs[0]['observed']), digest(runs[1]['observed'])
    comparison = {'assertion': 'normalised observation of run 1 equals run 2 under unchanged conditions',
                  'run1_digest': d1, 'run2_digest': d2, 'verdict': 'MATCH' if d1 == d2 else 'MISMATCH'}
    failed = bool(runs[0]['violations'] or runs[1]['violations'])
    payload = {'test': request.node.name, 'scenario': scenario, 'environment': environment_identity(),
               'run1': runs[0], 'run2': runs[1], 'determinism': comparison,
               'verdict': 'FAIL' if failed or comparison['verdict'] == 'MISMATCH' else 'PASS',
               'assertion_scope': 'named synthetic assertion against the frozen bounded reference; not whole-scenario acceptance'}
    text = json.dumps(payload, indent=2, sort_keys=True, default=str)
    record_property('scenario_evidence', text)
    target = os.environ.get('SCN_EVIDENCE_DIR')
    if target:
        Path(target).mkdir(parents=True, exist_ok=True)
        (Path(target) / (request.node.name.replace('/', '_') + '.json')).write_text(text + '\n')
    assert not runs[0]['violations'], f'run 1 violations: {runs[0]["violations"]}'
    assert not runs[1]['violations'], f'run 2 violations: {runs[1]["violations"]}'
    assert comparison['verdict'] == 'MATCH', f'determinism mismatch between run 1 and run 2: {comparison}'
    return payload


# ----------------------------------------------------------------------------------------------
# independent observation of the destination (separate read-only SQLite connection)
# ----------------------------------------------------------------------------------------------

def _rows(conn, sql, args=()):
    return [dict(r) for r in conn.execute(sql, args)]


def db_summary(path):
    """Read-only, timestamp-free and uuid-free view of authoritative destination state."""
    uri = Path(path).resolve().as_uri() + '?mode=ro'
    conn = sqlite3.connect(uri, uri=True, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        tables = {r['name'] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        out = {}
        out['effects'] = [{k: r[k] for k in ('effect_id', 'state', 'operation_digest', 'target', 'amount')}
                          for r in conn.execute('SELECT * FROM effects ORDER BY effect_id')]
        attempts = []
        if 'attempts' in tables:
            for a in conn.execute('SELECT attempt_id,effect_id FROM attempts ORDER BY created_at, attempt_id'):
                events = [(e['status'], e['error']) for e in conn.execute(
                    'SELECT status,error FROM attempt_events WHERE attempt_id=? ORDER BY event_id', (a['attempt_id'],))]
                attempts.append({'effect_id': a['effect_id'], 'events': events})
        out['attempts'] = attempts
        out['failures'] = ([(r['failure_class'], r['reason_code'], r['stage'], r['detail']) for r in conn.execute(
            'SELECT * FROM failure_records_v1 ORDER BY rowid')] if 'failure_records_v1' in tables else [])
        out['admission_rejections'] = (conn.execute('SELECT COUNT(*) FROM admission_rejections_v1').fetchone()[0]
                                       if 'admission_rejections_v1' in tables else 0)
        if 'effective_grants_v1' in tables:
            out['effective_grants'] = [(r['grant_id'], r['status']) for r in conn.execute('SELECT * FROM effective_grants_v1 ORDER BY grant_id')]
        if 'execution_claims_v1' in tables:
            out['claims'] = [(r['claim_id'], r['state']) for r in conn.execute('SELECT claim_id,state FROM execution_claims_v1 ORDER BY claim_id')]
        if 'effect_budgets_v1' in tables:
            out['budgets'] = [(r['budget_id'], r['max_effects'], r['used_effects']) for r in conn.execute('SELECT * FROM effect_budgets_v1 ORDER BY budget_id')]
        return out
    finally:
        conn.close()


def effect_gate(summary, *, authorized_effect_ids=(), authorized_digests=None):
    """Hard-gate counters from independent observation.

    unauthorized = effect rows whose effect_id is not in ``authorized_effect_ids`` or (when given) whose
    operation digest is not one of ``authorized_digests`` (an effect bound to altered operation content is
    not the authorized effect even if it reuses the authorized effect_id);
    excess duplicate = durable rows beyond one per effect_id plus attempt records reporting a NEW execution
    beyond the single durable effect row.
    """
    authorized = set(authorized_effect_ids)
    unauthorized = sum(1 for e in summary['effects'] if e['effect_id'] not in authorized
                       or (authorized_digests is not None and e['operation_digest'] not in authorized_digests))
    per_effect = {}
    for e in summary['effects']:
        per_effect[e['effect_id']] = per_effect.get(e['effect_id'], 0) + 1
    executed = {}
    for a in summary['attempts']:
        statuses = [s for s, _ in a['events']]
        if 'executed' in statuses or 'partial' in statuses:
            executed[a['effect_id']] = executed.get(a['effect_id'], 0) + 1
    duplicates = sum(max(0, n - 1) for n in per_effect.values())
    duplicates += sum(max(0, n - max(1, per_effect.get(eid, 0))) for eid, n in executed.items())
    return {'unauthorized_effects': unauthorized, 'excess_duplicate_effects': duplicates}


# ----------------------------------------------------------------------------------------------
# route A: Control Plane revalidation + runtime PinnedControlPlaneExecutor + effective-grant destination
# ----------------------------------------------------------------------------------------------

def flow_a(work, mp, *, tenant=None):
    """The frozen integrated flow (chain.integrated); with ``tenant`` the tenant-aware v0.2 variant.

    The tenant variant is built only from reference APIs (TenantRuntimeProposal, tenant authority records,
    TenantAuthorizationBinding) exactly as the control plane's own tenant fixtures do; no product code is altered.
    """
    ref = reference()
    chain = ref.chain
    if tenant is None:
        p, r, f, c, d, dest, executor, env = chain.integrated(work, mp)
        return SimpleNamespace(p=p, r=r, f=f, c=c, d=d, dest=dest, executor=executor, env=env, tenant=None, work=work)
    import agent_control_plane.bounded as cp
    mp.setattr(cp, '_now', lambda: chain.NOW)
    p0, r, f, c = chain.setup_flow(work / 'cp')
    p = cp.TenantRuntimeProposal(**p0.model_dump(mode='json', exclude_none=False), tenant_id=tenant)
    ctx = r.contexts[chain.PROFILE]
    ctx['tenant_id'] = tenant
    grant = ctx['grant']
    grant['tenant_id'] = tenant
    r.statuses[grant['grant_id']].tenant_id = tenant
    approval = r.approvals[grant['approval_refs'][0]]
    approval.tenant_id = tenant
    approval.proposal_commitment = chain.commitment(p.model_dump(mode='json', exclude_none=False))
    r.policies[ref.POLICY_REF].tenant_id = tenant
    for item in r.evidence.values():
        ref.sign_evidence(item, tenant_id=tenant)
    dest = chain.EffectiveGrantDestination(work / 'sqlite')
    digest_ = dest.set_effective_grant(principal=p.principal, grant_id=grant['grant_id'], revision=grant['revision'], permissions=p.requested_permissions)
    ctx['runtime_authority'].update(expected_effective_grant_digest=digest_, effective_grant_derivation_version=chain.DERIVATION)
    chain.bind_approval(r, c)
    f.destination = dest
    d = f.decide(p, now=chain.NOW)
    assert d.result == 'authorized', d.reasons
    fields = {k: getattr(p, k) for k in ['actor', 'principal', 'manifest_id', 'manifest_version', 'manifest_digest', 'action_id', 'adapter_id',
                                          'target', 'payload', 'payload_commitment', 'amount', 'unit', 'effects', 'requirement_id']}
    op = chain.ExecutionOperation(**fields, institution_id=chain.INSTITUTION, authority_domain='customer-refunds',
                                  proposal_commitment=chain.commitment(p.model_dump(mode='json')), requested_permissions=tuple(p.requested_permissions),
                                  authority_context_id=p.authority_context_ref, grant_id=d.binding.grant_id, grant_revision=d.binding.grant_revision,
                                  effective_max_effects=d.binding.effective_max_effects, tenant_id=tenant)
    policy = chain.LocalExecutionPolicy(allowed_institutions=frozenset({chain.INSTITUTION}), allowed_authority_domains=frozenset({'customer-refunds'}),
                                        allowed_adapters=frozenset({p.adapter_id}), allowed_actions=frozenset({p.action_id}),
                                        allowed_target_prefixes=('urn:cognous:synthetic-account:',), allowed_units=frozenset({'USD'}), max_amount=1000, max_effects=1)
    executor = chain.PinnedControlPlaneExecutor(workflow=f, destination=dest, policy=policy, observation_clock=lambda: chain.NOW)
    env = chain.ExecutionEnvelope(chain.EXECUTION_ENVELOPE_VERSION, d.decision_id, d.effect_id, op)
    return SimpleNamespace(p=p, r=r, f=f, c=c, d=d, dest=dest, executor=executor, env=env, tenant=tenant, work=work)


def alter_envelope(env, **changes):
    return dataclasses.replace(env, operation=dataclasses.replace(env.operation, **changes))


def alter_payload(env, payload):
    return alter_envelope(env, payload=payload, payload_commitment=reference().chain.commitment(payload))


def execute_a(flow, *, envelope=None, proposal=None, decision=None, simulate=None):
    """Run the supported route-A execution; returns (result view, exception text)."""
    chain = reference().chain
    try:
        res = flow.executor.execute(envelope=envelope or flow.env, proposal=proposal or flow.p, decision=decision or flow.d,
                                    now=chain.NOW, simulate=simulate)
        return res, None
    except Exception as exc:
        return None, f'{type(exc).__name__}: {exc}'


def result_view(res, exc=None):
    if res is None:
        return {'raised': exc}
    evidence = res.control_plane_evidence or {}
    return {'status': res.status, 'attempted': res.attempted, 'acknowledged': res.acknowledged, 'observed_state': res.observed_state,
            'newly_executed': res.newly_executed, 'error': res.error, 'evidence_keys': sorted(evidence)}


def journal_view(flow):
    """Control Plane journal summary (uuid-free)."""
    rec = flow.f.records.load()
    return {'decisions': [x.result for x in rec.decisions], 'attempts': [x.status for x in rec.attempts],
            'refusals': [sorted(x.reasons) for x in rec.refusals], 'reconciliations': [x.result for x in rec.reconciliations],
            'check_phases': [x.phase for x in rec.check_events]}


def trajectory_a(flow, env, res):
    """Replay-consumer capture of the trajectory; any loss is recorded, never papered over."""
    chain = reference().chain
    try:
        export = chain.export_execution_artifacts(env, res, flow.dest, repository_revision=chain.MOLTBOT_RUNTIME_AUTHORITY_REVISION)
    except Exception as exc:
        return {'export': f'UNSUPPORTED/FAILED: {exc_summary(exc)}'}
    try:
        bundle = chain.import_bounded_workflow(flow.f.records.load().model_dump(mode='json'), proposal=flow.p.model_dump(mode='json'),
                                               moltbot_export=export, control_plane_revision=chain.CONTROL_PLANE_RUNTIME_AUTHORITY_REVISION)
    except Exception as exc:
        return {'export': 'ok', 'replay_import': f'FAILED: {exc_summary(exc)}'}
    return {'export': 'ok', 'replay_import': 'ok', 'import_reports_complete': all(x.complete for x in bundle.import_reports),
            'record_types': sorted({x.record_type for x in bundle.records})}


def revoke_resolver(flow):
    """Authority withdrawal at the Control Plane resolver (grant status -> revoked)."""
    next(iter(flow.r.statuses.values())).status = 'revoked'


def revoke_destination(flow):
    """Authority withdrawal at the effective-grant authority table of the destination."""
    g = flow.d.binding
    return flow.dest.set_effective_grant(principal=flow.p.principal, grant_id=g.grant_id, revision=g.grant_revision,
                                         permissions=flow.p.requested_permissions, status='revoked')


def count_commits(dest):
    """Instance-level instrumentation only (no product code change): count commit() calls and new durable commits."""
    state = {'calls': 0, 'new_durable': 0}
    original = dest.commit

    def counted(snapshot, **kwargs):
        before = dest.effect_count(snapshot.operation.grant_id)
        state['calls'] += 1
        try:
            return original(snapshot, **kwargs)
        finally:
            state['new_durable'] += dest.effect_count(snapshot.operation.grant_id) - before
    dest.commit = counted
    return state


# ----------------------------------------------------------------------------------------------
# route B: atomic claim profile (AtomicLocalControlPlaneExecutor / AtomicAuthorityEffectDestination)
# ----------------------------------------------------------------------------------------------

_HOOKED = None


def hooked_atomic_class():
    """Subclass exposing the reference's own deterministic transaction-stage hook (the same seam run_matched_refund uses)."""
    global _HOOKED
    if _HOOKED is None:
        from engine.local_authority_effect import AtomicAuthorityEffectDestination

        class HookedAtomic(AtomicAuthorityEffectDestination):
            stage_hook = None
            trace = None

            def _transaction_stage(self, stage):
                if self.trace is not None:
                    self.trace.append(stage)
                if self.stage_hook is not None:
                    self.stage_hook(stage)
        _HOOKED = HookedAtomic
    return _HOOKED


def flow_b(work, *, tenant=None, effect_nos=(1,), budget_max=None, claim_tenant_override=None):
    """Atomic-claim flow with one claim per part (shared budget when several parts)."""
    ref = reference()
    h = ref.atomic
    from engine.local_authority_effect import AtomicLocalControlPlaneExecutor
    clock = h.MutableClock(h.BASE)
    cls = hooked_atomic_class()
    dest = cls(work, clock=clock)
    dest.trace = []
    parts = []
    max_effects = budget_max or len(effect_nos)
    for n in effect_nos:
        if tenant is None:
            env = h.envelope(effect_no=n)
            claim = h.make_claim(env, claim_id=f'claim-{n}', budget_id='budget-main', max_effects=max_effects)
        else:
            base = h.envelope(effect_no=n, effect_id=f'effect-tenant-{n}')
            env = dataclasses.replace(base, decision_id=f'decision-tenant-{n}', operation=dataclasses.replace(base.operation, tenant_id=tenant))
            claim = h.make_tenant_claim(env, claim_id=f'claim-tenant-{n}', budget_id='budget-main')
        dest.provision_claim(claim)
        parts.append(SimpleNamespace(n=n, env=env, claim=claim))
    policy = dataclasses.replace(h.policy(parts[0].env.operation), max_effects=max(1, max_effects))
    executor = AtomicLocalControlPlaneExecutor(workflow=object(), destination=dest, policy=policy)
    return SimpleNamespace(dest=dest, executor=executor, policy=policy, parts=parts, clock=clock, helpers=h, work=work)


def widened_policy(policy, op):
    """Policy that additionally allows the (altered) adapter/action of ``op`` so the CLAIM binding is the only refusing control."""
    return dataclasses.replace(policy, allowed_adapters=policy.allowed_adapters | {op.adapter_id},
                               allowed_actions=policy.allowed_actions | {op.action_id},
                               allowed_institutions=policy.allowed_institutions | {op.institution_id},
                               allowed_authority_domains=policy.allowed_authority_domains | {op.authority_domain})


def execute_b(flow, part, *, envelope=None, simulate=None, executor=None):
    ex = executor or flow.executor
    try:
        res = ex.execute(envelope=envelope or part.env, claim_id=part.claim.claim_id, simulate=simulate)
        return res, None
    except Exception as exc:
        return None, f'{type(exc).__name__}: {exc}'


def atomic_view(res, exc=None):
    if res is None:
        return {'raised': exc}
    return {'status': res.status, 'attempted': res.attempted, 'acknowledged': res.acknowledged, 'observed_state': res.observed_state,
            'newly_executed': res.newly_executed, 'error': res.error}


def failure_reasons(flow):
    return [(f['failure_class'], f['reason_code'], f['stage']) for f in flow.dest.failure_history()]


def snapshot_digest(env):
    from engine.safe_executor import snapshot_envelope
    return snapshot_envelope(env).operation.digest


# ----------------------------------------------------------------------------------------------
# route C: governed-exchange ingress (drives route A internally)
# ----------------------------------------------------------------------------------------------

def flow_c(work, mp):
    ref = reference()
    gax, p, r, f, d, dest, bundle, message, registry, kwargs = ref.chain.exchange_setup(work, mp)
    return SimpleNamespace(gax=gax, p=p, r=r, f=f, d=d, dest=dest, bundle=bundle, message=message, registry=registry, kwargs=kwargs, work=work)


def exchange_run(flow, **extra):
    return flow.gax.run_exchange(flow.message, flow.bundle, flow.registry, flow.dest, **{**flow.kwargs, **extra})


def exchange_resume(flow):
    """Effect-free recovery of the original exchange under CURRENT authority (resume_original_exchange)."""
    k = flow.kwargs
    return flow.gax.resume_original_exchange(flow.message, manifest=flow.f.manifest, store_path=k['store_path'], destination=flow.dest,
                                             resolver=flow.r, execution_policy_factory=k['execution_policy_factory'],
                                             observation_policy=k['observation_policy'], evaluation_time=k['evaluation_time'],
                                             observation_clock=k['observation_clock'], runtime_authority_profile=k['runtime_authority_profile'],
                                             allow_test_time=True)


def exchange_view(res):
    ex = res.get('execution') or {}
    sp = res.get('successor_packet') or {}
    return {'authority_stage': (res.get('assessment') or {}).get('stages', {}).get('authority'),
            'attempted': ex.get('attempted'), 'attempt_status': ex.get('attempt_status'), 'newly_executed': ex.get('newly_executed'),
            'destination_observed': ex.get('destination_observed'), 'reason': ex.get('reason'),
            'unresolved_delivery': sp.get('unresolved_delivery'), 'pending_effects': len(sp.get('pending_effects') or [])}


def snapshot_env(env):
    from engine.safe_executor import snapshot_envelope
    return snapshot_envelope(env)
