"""Test-only stand-in for the Wiki OPA application (no policy engine, no registered scenario).

It has the scoring-interface members of comparator-plan.md section 2 and a trivial one-effect
budget, so that the graph layer can be tested without running any real configuration.
"""
import json
from pathlib import Path
import sqlite3
from contextlib import closing
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from reference_profiles.assurance_runtime import digest
from reference_profiles.trust_evidence import signed, verify


class SyntheticBase:
    max_effects = 1

    def __init__(self, root, opa, mutation=None):
        self.root = Path(root); self.root.mkdir(parents=True)
        self.path = self.root / 'destination.sqlite'; self.opa = opa
        self.now = 100; self.serial = 0; self.mutation = mutation
        self.keys = {p: Ed25519PrivateKey.generate() for p in ('admin', 'broker', 'verifier', 'agent')}
        self.registry = {p: {'public_key': k.public_key().public_bytes_raw().hex(),
                             'not_before': 0, 'expires_at': 1000, 'revoked_at': None}
                         for p, k in self.keys.items()}
        with closing(sqlite3.connect(self.path)) as c, c:
            c.executescript('CREATE TABLE state(body TEXT); CREATE TABLE effects(id TEXT PRIMARY KEY,request TEXT,payload TEXT);'
                            'CREATE TABLE events(seq INTEGER PRIMARY KEY,body TEXT);')
            c.execute('INSERT INTO state VALUES(?)', (json.dumps(dict(revoked=False, consumed=0)),))

    def request(self, changes=None, fault=None):
        if fault is not None:
            raise ValueError('unknown fault ' + str(fault))
        self.serial += 1
        args = dict(grant='grant', effect='effect', payload='synthetic-graph')
        args.update(changes or {})
        return signed(self.keys['broker'], 'broker', 'destination-command',
                      dict(id='graph-command-' + str(self.serial), operation='execute', at=self.now, arguments=args))

    def snapshot(self):
        with closing(sqlite3.connect(f'file:{self.path}?mode=ro', uri=True)) as c:
            effects = [dict(id=r[0], request=r[1], payload=r[2]) for r in c.execute('SELECT id,request,payload FROM effects ORDER BY id')]
            events = [json.loads(r[0]) for r in c.execute('SELECT body FROM events ORDER BY seq')]
        return {'effects': effects, 'events': events}

    def _change(self, **changes):
        with closing(sqlite3.connect(self.path, timeout=10)) as c, c:
            c.execute('BEGIN IMMEDIATE')
            state = json.loads(c.execute('SELECT body FROM state').fetchone()[0]); state.update(changes)
            c.execute('UPDATE state SET body=?', (json.dumps(state),))

    def revoke(self): self._change(revoked=True)
    def fence(self): pass
    def rotate(self): pass
    def reopen(self): pass

    def break_audit(self):
        with closing(sqlite3.connect(self.path)) as c, c:
            c.execute("CREATE TRIGGER fail_audit BEFORE INSERT ON events BEGIN SELECT RAISE(ABORT,'synthetic audit outage'); END")

    def apply(self, request):
        with closing(sqlite3.connect(self.path, timeout=10)) as c, c:
            c.execute('BEGIN IMMEDIATE')
            state = json.loads(c.execute('SELECT body FROM state').fetchone()[0])
            body = request['body']; args = body['arguments']; reason = None
            try:
                verify(request, self.registry, at=body['at'], now=self.now)
            except ValueError:
                reason = 'AUTHENTICATION_DENIED'
            if reason is None and (state['revoked'] or state['consumed'] >= self.max_effects):
                reason = 'POLICY_DENIED'
            if reason is None:
                c.execute('INSERT INTO effects VALUES(?,?,?)', (args['effect'], digest(args),
                          json.dumps(args['payload'], separators=(',', ':'), sort_keys=True)))
                state['consumed'] += 1
                c.execute('UPDATE state SET body=?', (json.dumps(state),))
            status = 'denied' if reason else 'accepted'
            c.execute('INSERT INTO events(body) VALUES(?)', (json.dumps(dict(operation='execute', command=body['id'],
                request_digest=digest(request), status=status, reason=reason, at=self.now,
                command_authenticated=reason != 'AUTHENTICATION_DENIED')),))
            return {'status': status, 'reason': reason, 'result': {'duplicate': False}}


class SyntheticBaseWithHook(SyntheticBase):
    """Same, plus the optional `record_denial` hook (the preferred path for the graph layer)."""
    hook_calls = 0

    def record_denial(self, request, reason):
        SyntheticBaseWithHook.hook_calls += 1
        body = request['body']
        with closing(sqlite3.connect(self.path, timeout=10)) as c, c:
            c.execute('BEGIN IMMEDIATE')
            c.execute('INSERT INTO events(body) VALUES(?)', (json.dumps(dict(operation='execute', command=body['id'],
                request_digest=digest(request), status='denied', reason=reason, at=self.now, command_authenticated=True)),))
