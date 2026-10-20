"""Three stub adapters for the contract self-check. They implement the scoring interface (comparator plan, section 2) and nothing else: they
are not configurations of the comparison and make no decision of their own.

  accept  accepts every call and records one effect per distinct effect id with the submitted payload
  deny    denies every call and records a durable denial event for it
  echo    returns, call by call, the expected statuses of the case it is built for and records exactly the expected effects (a correct fixture)

The stubs inherit the registered Fixture (keys, clock, request signing, snapshot) so that requests are byte-identical to those of every
configuration. Built by a factory because the registered adapters module is available only after the pinned trees are on the path.
"""
import json
import sqlite3

from comparators.wiki.harness import _base


def build_stubs():
    adapters = _base.pinned_adapters()
    from reference_profiles.assurance_runtime import digest

    def canonical(value):
        return json.dumps(value, separators=(',', ':'), sort_keys=True)

    class _Stub(adapters.Fixture):
        def __init__(self, root, opa, mutation=None):
            super().__init__(root, opa, mutation)
            with sqlite3.connect(self.path) as c:
                c.executescript('CREATE TABLE effects(id TEXT PRIMARY KEY,request TEXT,payload TEXT); CREATE TABLE events(seq INTEGER PRIMARY KEY,body TEXT);')
            self.calls = 0

        def reopen(self): pass
        def revoke(self): pass
        def fence(self): pass
        def rotate(self): pass
        def opa_down(self): pass
        def opa_up(self): pass
        def fail_open(self): pass
        def fail_closed(self): pass

        def __getattr__(self, name):
            if name.startswith('_') or ':' not in name:
                raise AttributeError(name)
            return lambda: None  # a control with arguments: a stub has no state to change

        def _record(self, request, status, reason, payload=None):
            body = request['body']
            args = body['arguments']
            with sqlite3.connect(self.path, timeout=10) as c:
                if status == 'accepted':
                    c.execute('INSERT OR IGNORE INTO effects VALUES(?,?,?)',
                              (args['effect'], digest({k: v for k, v in args.items() if k not in ('verifier_status', 'issuer_claims')}),
                               canonical(args['payload'] if payload is None else payload)))
                c.execute('INSERT INTO events(body) VALUES(?)', (json.dumps(dict(
                    operation='execute', command=body['id'], request_digest=digest(request), status=status, reason=reason, at=self.now,
                    command_authenticated=True)),))
            return {'status': status, 'reason': reason, 'result': {'duplicate': False}}

    class AcceptStub(_Stub):
        def apply(self, request):
            return self._record(request, 'accepted', None)

    class DenyStub(_Stub):
        def apply(self, request):
            return self._record(request, 'denied', 'STUB_DENIED')

    def echo_for(case):
        class EchoStub(_Stub):
            script = list(case['expected_statuses'])
            payload = case['expected_payload']

            def apply(self, request):
                status = self.script[self.calls]
                self.calls += 1
                return self._record(request, status, None if status == 'accepted' else 'STUB_ECHO',
                                    self.payload if status == 'accepted' else None)
        return EchoStub

    return dict(accept=AcceptStub, deny=DenyStub, echo_for=echo_for)
