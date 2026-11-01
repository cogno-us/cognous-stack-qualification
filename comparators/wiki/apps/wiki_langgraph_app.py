"""Wiki-subset comparator: LangGraph plus OPA transactional application (WP-C2).

Configured by Cognous, not a vendor implementation. Not independent certification, not production
readiness. Bounded synthetic profile only. Linux only.

Topology is the same as the registered `LangGraphOPA` (approval node using `interrupt`, then an effect
node, SQLite checkpointer, `thread_id` = command id) with these differences, each stated here so a
checker can compare them with the plan (scoring interface, comparator rules, graph-variant rule):

1. The effect node calls the Wiki OPA application's `apply` by an explicit reference to the base class
   it was built over (`self._base_cls.apply(self, request)`), never through `super()` bound to another
   class. A different base class therefore changes the effect node (test:
   `test_effect_node_calls_the_configured_base`).
2. A rejected or timed-out approval is a recorded denial (status denied, non-empty reason, durable
   event in the destination file), not an exception that would crash the harness.
3. Approval hold is an adapter state, entered by the zero-argument step method `require_approval` and
   left by `release_approval`. While held, `apply` stops at the interrupt, records a durable denial
   `APPROVAL_PENDING` and keeps the request pending; `approve`, `reject` and `timeout` (zero-argument
   step methods) resume every pending thread. Outside hold the behaviour equals the registered
   configuration: interrupt, then immediate resume with approval.

Nothing here reads a plan, a case or any OCS output. No policy logic lives in this file: the decision
is the Wiki OPA application's. This file only adds the graph, the hold and the recorded denial.
"""
from contextlib import closing
import json
import sqlite3
from typing import TypedDict

from ..harness import _base

_base.setup_paths()  # pinned hub helpers (reference_profiles); idempotent, same call the OPA application makes
from reference_profiles.assurance_runtime import digest  # noqa: E402
from reference_profiles.trust_evidence import verify  # noqa: E402

PROFILE_ID = 'langgraph-opa-transactional-application'  # the registered profile id of the graph configuration

APPROVED, REJECTED, TIMEOUT = 'approved', 'rejected', 'timeout'
# Reason names are the Wiki OPA application's own (comparators/wiki/apps/wiki_opa_app.py REASON_ORDER), so a denial
# recorded by this layer and one decided by the application share one vocabulary.
REASON_PENDING = 'APPROVAL_PENDING'
REASON_BY_DECISION = {REJECTED: 'APPROVAL_REJECTED', TIMEOUT: 'APPROVAL_TIMED_OUT'}

# Members the runner (and the plan steps) use; every base class must provide them
# (comparator-plan.md section 2). `record_denial` is optional (see `_deny`).
REQUIRED_METHODS = ('apply', 'request', 'snapshot', 'revoke', 'fence', 'rotate', 'reopen', 'break_audit')
REQUIRED_INSTANCE_ATTRIBUTES = ('now', 'serial', 'keys', 'registry', 'root', 'path')

# Control-removal ablations of this layer only (never of the base application's rules).
GRAPH_MUTATIONS = (
    'graph_bypass_graph',       # base apply called directly: no interrupt, no hold
    'graph_skip_hold',          # hold state ignored: request goes straight through
    'graph_reject_as_approve',  # a rejection is treated as approval
    'graph_timeout_as_approve',  # a timeout is treated as approval
)


def denial_event(command, request_digest, reason, at, authenticated):
    """The events(body) JSON of a denial recorded outside the base `apply`; same keys, in the same order, as
    the Wiki OPA application writes for a denied execute (threshold_alert, hold, policy_skipped, reasons)."""
    return dict(operation='execute', command=command, request_digest=request_digest, status='denied',
                reason=reason, at=at, command_authenticated=authenticated, threshold_alert=False,
                hold=reason == REASON_PENDING, policy_skipped=False, reasons=[reason])


class GraphState(TypedDict, total=False):
    request: dict
    decision: str
    result: dict


def check_base_contract(base_cls):
    """Raise TypeError when `base_cls` lacks a member the scoring interface needs."""
    missing = [m for m in REQUIRED_METHODS if not callable(getattr(base_cls, m, None))]
    if missing:
        raise TypeError('base application lacks members: ' + ', '.join(missing))


class _GraphLayer:
    _base_cls = None  # set by the factory; read-only afterwards

    def __init__(self, root, opa, mutation=None):
        self._graph_mutation = None
        base_mutation = mutation
        if isinstance(mutation, str):
            # One graph ablation may be combined with base control families ("graph_x+family+family").
            parts = mutation.split('+')
            graph = [x for x in parts if x.startswith('graph_')]
            if len(graph) > 1:
                raise ValueError('at most one graph mutation')
            if graph:
                if graph[0] not in GRAPH_MUTATIONS:
                    raise ValueError('unknown graph mutation: ' + graph[0])
                self._graph_mutation = graph[0]
                rest = [x for x in parts if not x.startswith('graph_')]
                base_mutation = '+'.join(rest) if rest else None
        self._base_cls.__init__(self, root, opa, base_mutation)
        self._hold = False
        self.last_resolutions = []
        with closing(sqlite3.connect(self.root / 'approvals.sqlite', timeout=10)) as c, c:
            c.execute('CREATE TABLE IF NOT EXISTS pending(seq INTEGER PRIMARY KEY, thread TEXT UNIQUE, request TEXT)')

    # ---- zero-argument step methods ---------------------------------------------------------
    def require_approval(self): self._hold = True
    def release_approval(self): self._hold = False
    def approve(self): self._resolve(APPROVED)
    def reject(self): self._resolve(REJECTED)
    def timeout(self): self._resolve(TIMEOUT)

    # ---- pending store (separate file, so the destination file and crash coupling are untouched)
    def _pending_connection(self):
        return closing(sqlite3.connect(self.root / 'approvals.sqlite', timeout=10))

    def pending_threads(self):
        with self._pending_connection() as c:
            return [r[0] for r in c.execute('SELECT thread FROM pending ORDER BY seq')]

    def _add_pending(self, thread, request):
        with self._pending_connection() as c, c:
            c.execute('INSERT INTO pending(thread,request) VALUES(?,?)', (thread, json.dumps(request)))

    def _drop_pending(self, thread):
        with self._pending_connection() as c, c:
            c.execute('DELETE FROM pending WHERE thread=?', (thread,))

    # ---- recorded denial ---------------------------------------------------------------------
    def _deny(self, request, reason):
        hook = getattr(self._base_cls, 'record_denial', None)
        if hook is not None:
            hook(self, request, reason)
        else:
            self._record_denial_direct(request, reason)
        return {'status': 'denied', 'reason': reason, 'result': {'duplicate': False}}

    def _record_denial_direct(self, request, reason):
        """Fallback when the base has no `record_denial`: one event row, same shape the Wiki OPA
        application writes for a denial (`events(seq, body)`, see `denial_event`), in its own writer transaction. An
        audit-storage abort surfaces as sqlite3.IntegrityError and is never swallowed."""
        body = request['body']
        try:
            if request['issuer'] != 'broker' or request['kind'] != 'destination-command':
                raise ValueError('SIGNER_SCOPE')
            verify(request, self.registry, at=body['at'], now=self.now)
            authenticated = True
        except (ValueError, KeyError, TypeError):
            authenticated = False
        event = denial_event(body['id'], digest(request), reason, self.now, authenticated)
        with closing(sqlite3.connect(self.path, timeout=10)) as c, c:
            c.execute('BEGIN IMMEDIATE')
            c.execute('INSERT INTO events(body) VALUES(?)', (json.dumps(event),))

    # ---- graph -------------------------------------------------------------------------------
    def _run(self, make_input, thread):
        from langgraph.graph import StateGraph, START, END
        from langgraph.types import interrupt
        from langgraph.checkpoint.sqlite import SqliteSaver
        layer = self
        mutation = self._graph_mutation

        def approval(state):
            decision = interrupt({'request_digest': digest(state['request'])})
            if decision is True:
                decision = APPROVED
            if decision not in (APPROVED, REJECTED, TIMEOUT):
                raise ValueError('unknown approval decision')
            if mutation == 'graph_reject_as_approve' and decision == REJECTED: decision = APPROVED
            if mutation == 'graph_timeout_as_approve' and decision == TIMEOUT: decision = APPROVED
            return {'decision': decision}

        def effect(state):
            return {'result': layer._base_cls.apply(layer, state['request'])}

        def deny(state):
            return {'result': layer._deny(state['request'], REASON_BY_DECISION[state['decision']])}

        def route(state):
            return 'effect' if state['decision'] == APPROVED else 'deny'

        builder = StateGraph(GraphState)
        builder.add_node('approval', approval); builder.add_node('effect', effect); builder.add_node('deny', deny)
        builder.add_edge(START, 'approval')
        builder.add_conditional_edges('approval', route, {'effect': 'effect', 'deny': 'deny'})
        builder.add_edge('effect', END); builder.add_edge('deny', END)
        with SqliteSaver.from_conn_string(str(self.root / 'checkpoints.sqlite')) as saver:
            graph = builder.compile(checkpointer=saver)
            return make_input(graph, {'configurable': {'thread_id': thread}})

    def apply(self, request):
        from langgraph.types import Command
        thread = request['body']['id']
        if self._graph_mutation == 'graph_bypass_graph':
            return self._base_cls.apply(self, request)
        hold = self._hold and self._graph_mutation != 'graph_skip_hold'
        if hold and thread in self.pending_threads():
            return self._deny(request, REASON_PENDING)

        def first(graph, config):
            pending = graph.invoke({'request': request}, config)
            if not pending.get('__interrupt__'):
                raise RuntimeError('expected durable approval interrupt')
            if hold:
                return None
            return graph.invoke(Command(resume=APPROVED), config)['result']
        result = self._run(first, thread)
        if result is not None:
            return result
        self._add_pending(thread, request)
        try:
            return self._deny(request, REASON_PENDING)
        except BaseException:
            self._drop_pending(thread)
            raise

    def _resolve(self, decision):
        from langgraph.types import Command
        with self._pending_connection() as c:
            rows = c.execute('SELECT thread FROM pending ORDER BY seq').fetchall()
        results = []
        for (thread,) in rows:
            results.append(self._run(lambda g, cfg: g.invoke(Command(resume=decision), cfg)['result'], thread))
            self._drop_pending(thread)
        self.last_resolutions = results


def make_wiki_langgraph_app(base_cls, name='WikiLangGraphOPA'):
    """Return the graph configuration built over `base_cls` (the Wiki OPA application)."""
    check_base_contract(base_cls)
    return type(name, (_GraphLayer, base_cls), {'_base_cls': base_cls, '__doc__': __doc__,
                                                'profile_id': PROFILE_ID})


def __getattr__(name):
    """`WikiLangGraphOPA` is the graph over the real Wiki OPA application (`WikiOpaApp`, same package).

    Resolved lazily so that the factory can be used and tested over a synthetic base without starting
    the policy engine wiring."""
    if name == 'WikiLangGraphOPA':
        from .wiki_opa_app import WikiOpaApp
        cls = make_wiki_langgraph_app(WikiOpaApp)
        globals()[name] = cls
        return cls
    raise AttributeError(name)
