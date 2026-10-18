"""Shared additions for catalog scenarios C01, C02, C06, C07, C08 and C09 (batch 2a).

SPDX-License-Identifier: Apache-2.0

This module only ADDS harness code on top of ``_d02_d05_d09_helpers`` (imported, never modified). Everything
runs against the FROZEN F5b-repaired seven-component bounded synthetic reference; no product code, pin,
profile or default is changed (instance-level and test-time monkeypatching only, undone after every trial).
No network, payment, model or production effect is used. Linux only (owner decision D2).

Routes (same inventory as batch 1, see ``test_scn_d09``):
  A  Control Plane revalidation + runtime PinnedControlPlaneExecutor + effective-grant destination
  B  atomic-claim profile (AtomicLocalControlPlaneExecutor / AtomicAuthorityEffectDestination)
  C  governed-exchange ``run_exchange`` ingress (drives route A internally)
"""
from __future__ import annotations

import dataclasses
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import _d02_d05_d09_helpers as H
from _d02_d05_d09_helpers import no_network, pinned_reference  # noqa: F401  (re-exported fixtures)

HERE = Path(__file__).resolve().parent


class CrashSignal(BaseException):
    """Simulated process death. BaseException so no ``except Exception`` in the reference can absorb it."""


# ----------------------------------------------------------------------------------------------
# route A with the decision exposed to a pre-decision mutation (needed when the decision itself must be refused)
# ----------------------------------------------------------------------------------------------

def flow_a_pre(work, mp, mutate=None):
    """Same construction as ``chain.integrated`` but ``mutate(p, r, f, dest)`` may alter authority BEFORE the decision.

    Returns a flow whose decision may be non-authorized; ``p`` is the (possibly altered) proposal.
    """
    ref = H.reference()
    ch = ref.chain
    import agent_control_plane.bounded as cp
    mp.setattr(cp, '_now', lambda: ch.NOW)
    p, r, f, c = ch.setup_flow(work / 'cp')
    dest = ch.EffectiveGrantDestination(work / 'sqlite')
    grant = r.contexts[ch.PROFILE]['grant']
    digest_ = dest.set_effective_grant(principal=p.principal, grant_id=grant['grant_id'], revision=grant['revision'], permissions=p.requested_permissions)
    r.contexts[ch.PROFILE]['runtime_authority'].update(expected_effective_grant_digest=digest_, effective_grant_derivation_version=ch.DERIVATION)
    ch.bind_approval(r, c)
    f.destination = dest
    if mutate is not None:
        p = mutate(p, r, f, dest) or p
    d = f.decide(p, now=ch.NOW)
    return SimpleNamespace(p=p, r=r, f=f, c=c, d=d, dest=dest, work=work, grant=grant)


def best_effort_executor(flow):
    """Executor and envelope an unprivileged caller would assemble for ``flow`` even though the decision may be a hold.

    The envelope reuses the grant the proposal's authority context names (or a placeholder when none exists), the
    decision's own identifiers, and a local policy that admits exactly this request, so that the Control Plane /
    destination controls are the only refusing layers.
    """
    ch = H.reference().chain
    p = flow.p
    grant = (flow.r.contexts.get(ch.PROFILE) or {}).get('grant') or {'grant_id': 'urn:cognous:grant:absent', 'revision': '1'}
    fields = {k: getattr(p, k) for k in ['actor', 'principal', 'manifest_id', 'manifest_version', 'manifest_digest', 'action_id', 'adapter_id',
                                          'target', 'payload', 'payload_commitment', 'amount', 'unit', 'effects', 'requirement_id']}
    binding = flow.d.binding
    op = ch.ExecutionOperation(**fields, institution_id=ch.INSTITUTION, authority_domain='customer-refunds',
                               proposal_commitment=ch.commitment(p.model_dump(mode='json')), requested_permissions=tuple(p.requested_permissions),
                               authority_context_id=p.authority_context_ref,
                               grant_id=binding.grant_id if binding else grant['grant_id'],
                               grant_revision=binding.grant_revision if binding else grant['revision'],
                               effective_max_effects=binding.effective_max_effects if binding else 1)
    policy = ch.LocalExecutionPolicy(allowed_institutions=frozenset({ch.INSTITUTION}), allowed_authority_domains=frozenset({'customer-refunds'}),
                                     allowed_adapters=frozenset({p.adapter_id}), allowed_actions=frozenset({p.action_id}),
                                     allowed_target_prefixes=('urn:cognous:synthetic-account:',), allowed_units=frozenset({'USD'}),
                                     max_amount=1000, max_effects=1)
    executor = ch.PinnedControlPlaneExecutor(workflow=flow.f, destination=flow.dest, policy=policy, observation_clock=lambda: ch.NOW)
    env = ch.ExecutionEnvelope(ch.EXECUTION_ENVELOPE_VERSION, flow.d.decision_id, flow.d.effect_id or 'effect-absent', op)
    return executor, env


def decision_view(flow):
    return {'result': flow.d.result, 'reasons': sorted(flow.d.reasons or []), 'has_binding': flow.d.binding is not None}


def journal_decisions(flow):
    """Retained Control Plane decisions with their reasons (uuid-free)."""
    rec = flow.f.records.load()
    return [{'result': x.result, 'reasons': sorted(x.reasons or [])} for x in rec.decisions]


def journal_refusal_reasons(flow):
    rec = flow.f.records.load()
    return [sorted(x.reasons) for x in rec.refusals]


def reconciliation_view(rec):
    return {'result': rec.result, 'retry_eligible': rec.retry_eligible, 'observation_accepted': rec.observation_accepted, 'reasons': sorted(rec.reasons or [])}


# ----------------------------------------------------------------------------------------------
# attempt identity linkage (uuid-free labels, read-only SQLite observation)
# ----------------------------------------------------------------------------------------------

def attempt_rows(path):
    """Destination attempts in creation order: distinct ids are labelled a1, a2 ... and linked to their effect id."""
    uri = Path(path).resolve().as_uri() + '?mode=ro'
    conn = sqlite3.connect(uri, uri=True, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in conn.execute('SELECT attempt_id,effect_id,decision_id FROM attempts ORDER BY created_at, rowid')]
        out = []
        for i, row in enumerate(rows, 1):
            events = [(e['status'], e['error']) for e in conn.execute('SELECT status,error FROM attempt_events WHERE attempt_id=? ORDER BY event_id', (row['attempt_id'],))]
            out.append({'label': f'a{i}', 'attempt_id': row['attempt_id'], 'effect_id': row['effect_id'], 'events': events})
        return out
    finally:
        conn.close()


def attempt_summary(path):
    rows = attempt_rows(path)
    ids = [r['attempt_id'] for r in rows]
    return {'count': len(rows), 'distinct_attempt_ids': len(set(ids)) == len(ids), 'effects_linked': sorted({r['effect_id'] for r in rows}),
            'attempts': [{'label': r['label'], 'events': r['events']} for r in rows]}


def _group_attempts(items, with_ids=False):
    """Control Plane journal appends a record per STATE of an attempt (same attempt_id): group them, uuid-free."""
    order, statuses, effects = [], {}, set()
    for attempt_id, status, effect_id in items:
        if attempt_id not in statuses:
            order.append(attempt_id)
            statuses[attempt_id] = []
        statuses[attempt_id].append(status)
        effects.add(effect_id)
    return {'records': len(items), 'distinct_attempt_ids': len(order), 'effects_linked': sorted(effects),
            'per_attempt_statuses': [statuses[a] for a in order], **({'attempt_ids': order} if with_ids else {})}


def cp_attempt_summary(flow, with_ids=False):
    rec = flow.f.records.load()
    out = _group_attempts([(a.attempt_id, a.status, a.effect_id) for a in rec.attempts], with_ids)
    out['statuses'] = [a.status for a in rec.attempts]
    return out


def exchange_attempts(flow, with_ids=False):
    """Attempts retained in the exchange's Control Plane journal files, grouped by attempt id."""
    import json
    items = []
    for path in sorted(Path(flow.work).glob('control-plane-*.json')):
        for a in json.loads(path.read_text()).get('attempts', []):
            items.append((a['attempt_id'], a['status'], a['effect_id']))
    return _group_attempts(items, with_ids)


# ----------------------------------------------------------------------------------------------
# route B re-open (restart) without re-provisioning, and a real child process that dies at a named seam
# ----------------------------------------------------------------------------------------------

def reopen_b(work, effect_nos=(1,)):
    """Open an EXISTING atomic-claim destination in a new executor (what a restarted process does).

    The envelope/claim/policy objects are rebuilt from the same deterministic fixture constructors flow_b uses;
    nothing is provisioned again.
    """
    ref = H.reference()
    h = ref.atomic
    from engine.local_authority_effect import AtomicLocalControlPlaneExecutor
    clock = h.MutableClock(h.BASE)
    dest = H.hooked_atomic_class()(work, clock=clock)
    dest.trace = []
    parts = []
    for n in effect_nos:
        env = H.envelope_with_cap(h, n, len(effect_nos))
        claim = h.make_claim(env, claim_id=f'claim-{n}', budget_id='budget-main', max_effects=len(effect_nos))
        parts.append(SimpleNamespace(n=n, env=env, claim=claim))
    policy = dataclasses.replace(h.policy(parts[0].env.operation), max_effects=max(1, len(effect_nos)))
    executor = AtomicLocalControlPlaneExecutor(workflow=object(), destination=dest, policy=policy)
    return SimpleNamespace(dest=dest, executor=executor, policy=policy, parts=parts, clock=clock, helpers=h, work=work)


def run_child_that_dies(work, seam, *, simulate=None):
    """Run ``_c_2a_child.py`` in a separate Python process that calls ``os._exit(77)`` at ``seam`` (a real process kill).

    Returns (exit_code, stdout). Exit code 77 means the kill was delivered at the seam; 0 means the seam never fired.
    """
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    argv = [sys.executable, '-I', str(HERE / '_c_2a_child.py'), str(work), seam, simulate or '-']
    proc = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=300)
    return proc.returncode, (proc.stdout + proc.stderr)[-400:]


# ----------------------------------------------------------------------------------------------
# route C: retained Control Plane journal of the exchange's own decision (read-only)
# ----------------------------------------------------------------------------------------------

def exchange_journal(flow):
    """Decisions/refusals/attempts retained in the exchange's Control Plane journal files (uuid-free)."""
    import json
    out = []
    for path in sorted(Path(flow.work).glob('control-plane-*.json')):
        data = json.loads(path.read_text())
        out.append({'decisions': [{'result': x['result'], 'reasons': sorted(x.get('reasons') or [])} for x in data.get('decisions', [])],
                    'refusals': [sorted(x.get('reasons') or []) for x in data.get('refusals', [])],
                    'attempts': [x['status'] for x in data.get('attempts', [])],
                    'reconciliations': [x['result'] for x in data.get('reconciliations', [])]})
    return out
