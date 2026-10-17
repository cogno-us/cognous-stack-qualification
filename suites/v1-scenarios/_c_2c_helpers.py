"""Shared helpers for catalog scenarios C16 (shared budget), C17 (stale shared state), C18 (bounded delegation),
C22 (equal-conditions comparison) and C23 (evaluator calibration).

SPDX-License-Identifier: Apache-2.0

Nothing here changes product code, pins, profiles or defaults. It only imports the batch-1 helpers
(``_d02_d05_d09_helpers`` / ``_d06_d07_d08_helpers``) and adds read-only observation, report-only evidence and a
small multi-agent race harness. The frozen F5b seven-component reference is built and verified pristine by the
batch-1 ``reference()`` (``SCN_COMPONENTS_DIR``); Linux only (owner decision D2); no network/payment/model/production effect.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import _d02_d05_d09_helpers as H

AUTHORITY_TABLES = ('authority_grants_v1', 'authority_approvals_v1', 'authority_policies_v1', 'authority_evidence_v1')


def write_report(request, record_property, label, payload):
    """Report-only / supplementary evidence next to the per-test evidence JSON (never compared, never thresholded)."""
    payload = {'test': request.node.name, 'environment': H.environment_identity(), 'report_only': True, **payload}
    text = json.dumps(payload, indent=2, sort_keys=True, default=str)
    record_property(label, text)
    target = os.environ.get('SCN_EVIDENCE_DIR')
    if target:
        Path(target).mkdir(parents=True, exist_ok=True)
        (Path(target) / (request.node.name.replace('/', '_') + f'__{label}.json')).write_text(text + '\n')
    return payload


def authority_rows(path):
    """Read-only dump of the authoritative (shared, mutable) authority tables of an atomic destination."""
    uri = Path(path).resolve().as_uri() + '?mode=ro'
    conn = sqlite3.connect(uri, uri=True, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        out = {}
        names = {r['name'] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for t in AUTHORITY_TABLES:
            if t in names:
                out[t] = [dict(r) for r in conn.execute(f'SELECT * FROM {t} ORDER BY 1')]
        return out
    finally:
        conn.close()


def table_columns(path, table):
    uri = Path(path).resolve().as_uri() + '?mode=ro'
    conn = sqlite3.connect(uri, uri=True, timeout=10)
    try:
        return [r[1] for r in conn.execute(f'PRAGMA table_info({table})')]
    finally:
        conn.close()


def claim_state(summary, claim_id):
    return next((s for c, s in summary.get('claims', []) if c == claim_id), None)


def budget_overrun(summary, budget_id, limit):
    """Effects beyond the declared budget (counted as unauthorized effects: no effect may exceed the budget)."""
    used = next((u for b, _m, u in summary.get('budgets', []) if b == budget_id), 0)
    return max(0, len(summary['effects']) - limit), used


def gate_with_budget(summary, authorized_effect_ids, limit, budget_id='budget-main'):
    gate = H.effect_gate(summary, authorized_effect_ids=authorized_effect_ids)
    over, _used = budget_overrun(summary, budget_id, limit)
    gate['unauthorized_effects'] += over
    return gate


# ----------------------------------------------------------------------------------------------
# multi-agent race harness (route B): every agent opens ITS OWN destination handle / executor on the shared store
# ----------------------------------------------------------------------------------------------

def _agent_executor(work, policy, base_iso):
    from engine.local_authority_effect import AtomicAuthorityEffectDestination, AtomicLocalControlPlaneExecutor
    base = datetime.fromisoformat(base_iso)
    dest = AtomicAuthorityEffectDestination(work, clock=lambda: base)
    return AtomicLocalControlPlaneExecutor(workflow=object(), destination=dest, policy=policy)


def _run_one(executor, env, claim_id):
    try:
        res = executor.execute(envelope=env, claim_id=claim_id)
        return {'status': res.status, 'error': res.error, 'newly_executed': res.newly_executed}
    except Exception as exc:  # recorded, never swallowed silently
        return {'status': 'raised', 'error': f'{type(exc).__name__}: {exc}', 'newly_executed': False}


def race_threads(flow, parts):
    """All agents (threads, separate destination handles / SQLite connections) start behind one barrier."""
    barrier = threading.Barrier(len(parts))
    out = [None] * len(parts)

    def agent(i, part):
        ex = _agent_executor(flow.work, flow.policy, flow.helpers.BASE.isoformat())
        barrier.wait(timeout=30)
        out[i] = _run_one(ex, part.env, part.claim.claim_id)
    threads = [threading.Thread(target=agent, args=(i, p)) for i, p in enumerate(parts)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(60)
    assert all(o is not None for o in out), 'an agent thread did not finish'
    return out


def _process_agent(work, env, claim_id, policy, base_iso, start, queue, index):
    ex = _agent_executor(work, policy, base_iso)
    start.wait(30)
    queue.put((index, _run_one(ex, env, claim_id)))


def race_processes(flow, parts):
    """All agents (separate spawned OS processes) start behind one event; results are collected by agent index."""
    import multiprocessing as mp
    ctx = mp.get_context('spawn')
    start, queue = ctx.Event(), ctx.Queue()
    procs = [ctx.Process(target=_process_agent, args=(str(flow.work), p.env, p.claim.claim_id, flow.policy, flow.helpers.BASE.isoformat(), start, queue, i))
             for i, p in enumerate(parts)]
    for p in procs:
        p.start()
    start.set()
    got = {}
    for _ in procs:
        i, r = queue.get(timeout=60)
        got[i] = r
    for p in procs:
        p.join(30)
        assert p.exitcode == 0, f'agent process exit code {p.exitcode}'
    return [got[i] for i in range(len(parts))]


def normalise_race(results):
    """Which agent wins a race is scheduling-dependent and not part of the contract: compare counts and reason classes."""
    def klass(r):
        if r['status'] == 'executed':
            return 'executed'
        err = (r['error'] or '')
        if 'budget exhausted' in err:
            return 'denied:budget_exhausted'
        return f"{r['status']}:{err[:80]}"
    kinds = sorted(klass(r) for r in results)
    return {'agents': len(results), 'outcome_classes': {k: kinds.count(k) for k in sorted(set(kinds))}}


# ----------------------------------------------------------------------------------------------
# timing (report-only)
# ----------------------------------------------------------------------------------------------

class Stopwatch:
    def __init__(self):
        self.samples = {}

    def time(self, label, fn, *a, **k):
        t = time.perf_counter()
        try:
            return fn(*a, **k)
        finally:
            self.samples.setdefault(label, []).append(time.perf_counter() - t)

    def summary(self):
        import statistics
        return {k: {'n': len(v), 'median_ms': round(statistics.median(v) * 1000, 3), 'max_ms': round(max(v) * 1000, 3)}
                for k, v in sorted(self.samples.items())}


def utc(dt):
    return dt.astimezone(timezone.utc).isoformat()
