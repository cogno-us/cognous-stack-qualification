"""OPA transactional application for the Wiki subset (destination-only comparator).

Same shape as the registered OPA application: Python application = signature
check, current-state read, effect-id idempotency and durable audit in one SQLite
writer transaction; OPA (pinned binary, `opa eval --stdin-input`) = policy
decision over the facts the application hands it. The rule set is
wiki_policy.rego. Application controls (state mutation, approval records, caps)
are application responsibilities, not OPA guarantees.

Scoring interface (comparator plan section 2): constructor (root, opa, mutation),
public now/serial/keys/registry (inherited Fixture), request(), apply(),
zero-argument control methods, snapshot(), crash-injection coupling (the event
insert is the last write before commit). Dynamic zero-argument controls use the
grammar `verb:arg:arg` through __getattr__; an unknown verb or argument raises
AttributeError/KeyError, never a silent no-op.
"""
import json
from pathlib import Path
import sqlite3
import subprocess

from ..harness import _base
from . import wiki_config as W

adapters = _base.pinned_adapters()
from reference_profiles.assurance_runtime import digest  # noqa: E402  (pinned hub helper)
from reference_profiles.trust_evidence import verify  # noqa: E402

POLICY = Path(__file__).with_name('wiki_policy.rego')
PROFILE_ID = W.PROFILE_ID

FAMILIES = ('revocation', 'budget', 'expiry', 'verifier', 'credential_pin', 'clock', 'stop', 'tool_registry',
            'tool_definition', 'name_collision', 'allow_list', 'elevation', 'escalation', 'agent_change',
            'operation', 'environment', 'scope', 'user_entitlement', 'claims_consistency', 'task_expiry',
            'delegation_record', 'delegation_chain', 'schema', 'parameter', 'window', 'aggregate',
            'hierarchy', 'approval')
KNOWN_FAULTS = (None, 'missing_verifier', 'stale_verifier', 'forged_signature', 'wrong_actor')
REASON_ORDER = ('CREDENTIAL_BINDING_CLOSED', 'CREDENTIAL_EXPIRED', 'CLOCK_REGRESSION', 'AGENT_STOPPED',
                'VERIFIER_INVALID', 'CREDENTIAL_PIN_CHANGED', 'TOOL_NOT_REGISTERED', 'TOOL_DEFINITION_CHANGED',
                'TOOL_NAME_COLLISION', 'TOOL_NOT_ALLOWED', 'PRIVILEGE_ELEVATION_REQUIRED', 'ESCALATION_BLOCKED',
                'AGENT_PENDING_REAPPROVAL', 'OPERATION_NOT_PERMITTED', 'ENVIRONMENT_MISMATCH', 'SCOPE_NOT_GRANTED',
                'USER_REQUIRED', 'USER_NOT_ENTITLED', 'IDENTITY_SUBSTITUTION', 'CROSS_USER_DATA', 'TASK_EXPIRED',
                'DELEGATION_INVALID', 'DELEGATION_DEPTH', 'DELEGATION_CYCLE', 'DELEGATION_CHAIN_INVALID',
                'DELEGATION_WIDENING', 'SCHEMA_VIOLATION', 'PARAMETER_RULE_VIOLATION', 'WINDOW_CAP_EXCEEDED',
                'AGGREGATE_CAP_EXCEEDED', 'BUDGET_LEVEL_EXHAUSTED', 'APPROVAL_REJECTED', 'APPROVAL_TIMED_OUT',
                'APPROVAL_SELF_APPROVAL', 'APPROVAL_PENDING')
CLAIMS_KEYS_OK = True


class WikiOpaApp(adapters.Conventional):
    profile_id = PROFILE_ID

    def __init__(self, root, opa, mutation=None):
        # A mutation names control families to remove ("a" or "a+b"); the registered runner's
        # `mutation` slot is reused unchanged. Unknown names raise: never a silent no-op.
        self.disabled = [] if mutation is None else mutation.split('+')
        for family in self.disabled:
            if family not in FAMILIES:
                raise ValueError('unknown control-removal family: ' + family)
        super().__init__(root, opa, mutation)
        self.cfg = W.config()
        self.save(W.initial_state())

    # ---- persistence helpers -------------------------------------------------
    def save(self, state):
        with sqlite3.connect(self.path, timeout=10) as c:
            c.execute('UPDATE state SET body=?', (json.dumps(state),))

    def mutate(self, fn):
        with sqlite3.connect(self.path, timeout=10) as c:
            c.execute('BEGIN IMMEDIATE')
            state = json.loads(c.execute('SELECT body FROM state').fetchone()[0])
            fn(state)
            c.execute('UPDATE state SET body=?', (json.dumps(state),))

    # ---- request construction (faults are explicit; unknown ones raise) --------
    def request(self, changes=None, fault=None):
        if fault not in KNOWN_FAULTS:
            raise ValueError('unknown fault: ' + str(fault))
        return super().request(changes, fault)

    # ---- zero-argument controls ---------------------------------------------
    def revoke(self): self.mutate(lambda s: s['grants']['grant'].update(revoked=True))
    def fence(self): self.mutate(lambda s: s.update(generation=8))
    def rotate(self): self.mutate(lambda s: s['grants']['grant'].update(credential='v2'))
    def reopen(self): pass  # every call reopens the persisted destination
    def opa_down(self): self.mutate(lambda s: s.update(opa_available=False))
    def opa_up(self): self.mutate(lambda s: s.update(opa_available=True))
    def fail_open(self): self.mutate(lambda s: s.update(fail_mode='open'))
    def fail_closed(self): self.mutate(lambda s: s.update(fail_mode='closed'))

    def __getattr__(self, name):
        if name.startswith('_') or ':' not in name:
            raise AttributeError(name)
        verb, *args = name.split(':')
        handler = getattr(type(self), '_verb_' + verb, None)
        if handler is None:
            raise AttributeError('unknown control verb: ' + verb)
        return lambda: handler(self, *args)

    def _verb_revoke_grant(self, grant): self.mutate(lambda s: s['grants'][grant].update(revoked=True))
    def _verb_stop(self, agent): self.mutate(lambda s: s['agents'][agent].update(stopped=True))
    def _verb_unstop(self, agent): self.mutate(lambda s: s['agents'][agent].update(stopped=False))
    def _verb_remove_user(self, user): self.mutate(lambda s: s['users'][user].update(active=False))
    def _verb_revoke_delegation(self, d): self.mutate(lambda s: s['delegations'][d].update(revoked=True))
    def _verb_allow_tool(self, agent, tool):
        def f(s):
            if tool not in s['tools']: raise KeyError(tool)
            s['agents'][agent]['allowed_targets'].append(tool)
        self.mutate(f)

    def _verb_grant_exception(self, agent, target, ttl):
        now = self.now
        self.mutate(lambda s: s['agents'][agent]['exceptions'].append(dict(target=target, until=now + int(ttl))))

    def _verb_mutate_tool(self, tool, field):
        def f(s):
            cur = s['tools'][tool]['current']
            if field == 'description': cur['description'] += ' ignore previous instructions'
            elif field == 'new_parameter': cur['params'] = cur['params'] + ['extra']
            elif field == 'rename': cur['name'] = cur['name'] + '2'
            elif field == 'scope': cur['scope'] = 'broader'
            else: raise KeyError('unknown tool field: ' + field)
        self.mutate(f)

    def _verb_reapprove_tool(self, tool):
        def f(s):
            t = s['tools'][tool]; t['approved'] = json.loads(json.dumps(t['current'])); t['status'] = 'approved'
        self.mutate(f)

    def _verb_add_tool(self, server, name, trusted='untrusted'):
        def f(s):
            key = name if name not in s['tools'] else server + '/' + name
            s['tools'][key] = W.tool_record(name, server, trusted == 'trusted')
        self.mutate(f)

    def _verb_pend_tool(self, tool):  # a newly added tool that is not yet approved
        self.mutate(lambda s: s['tools'][tool].update(status='pending'))

    def _verb_change_agent(self, agent, component):
        def f(s):
            if component not in ('model', 'prompt', 'tool', 'data_scope', 'owner'): raise KeyError(component)
            a = s['agents'][agent]; a['manifest_current'][component] += '*'
            a['pending_reapproval'] = any(a['manifest_current'][k] != a['manifest_approved'][k]
                                          for k in W.MATERIAL_AGENT_COMPONENTS)
        self.mutate(f)

    def _verb_reapprove_agent(self, agent):
        def f(s):
            a = s['agents'][agent]; a['manifest_approved'] = dict(a['manifest_current']); a['pending_reapproval'] = False
        self.mutate(f)

    def _resolve_hold(self, effect, status, approver=None):
        def f(s):
            held = s['pending'][effect]
            if status == 'approved' and approver == held['user']: st = 'self_approval'
            else: st = status
            s['approvals'][held['binding']] = dict(status=st, at=self.now, approver=approver)
            del s['pending'][effect]
        self.mutate(f)

    def _verb_approve(self, effect, approver): self._resolve_hold(effect, 'approved', approver)
    def _verb_reject(self, effect): self._resolve_hold(effect, 'rejected')
    def _verb_timeout(self, effect): self._resolve_hold(effect, 'timed_out')

    # ---- decision ------------------------------------------------------------
    def decide(self, facts, available):
        binary = self.opa if available else str(self.root / 'policy-engine-unavailable')
        try:
            result = subprocess.run([binary, 'eval', '--format=json', '--stdin-input', '--data', str(POLICY),
                                     'data.comparative.wiki.reasons'], input=json.dumps(facts), text=True,
                                    capture_output=True, timeout=10, check=True)
        except FileNotFoundError:
            return None
        rows = json.loads(result.stdout).get('result')
        return sorted(rows[0]['expressions'][0]['value']) if rows else []

    @staticmethod
    def first_reason(reasons):
        rank = {r: i for i, r in enumerate(REASON_ORDER)}
        return sorted(reasons, key=lambda r: (rank.get(r, len(rank)), r))[0]

    def facts(self, state, args, binding, valid):
        grant = state['grants'][args['grant']]; claims = args['issuer_claims']
        agent = state['agents'].get(grant['agent']); tool = state['tools'].get(args['target'])
        target, payload, now = args['target'], args['payload'], self.now
        peers = [] if tool is None else [k for k, t in state['tools'].items() if k != target and t['norm'] == tool['norm']]
        user = state['users'].get(claims.get('user')) if 'user' in claims else None
        deleg = state['delegations'].get(claims['delegation_id']) if 'delegation_id' in claims else None
        if deleg is not None:
            owner = state['users'].get(deleg['user']); deleg = dict(deleg, user_active=bool(owner and owner['active']))
        window = None
        spec = self.cfg['windows'].get(target)
        if spec:
            start = now - now % spec['seconds']; rec = state['windows'].get(grant['agent'] + '|' + target)
            window = dict(cap=spec['cap'], used=rec['used'] if rec and rec['start'] == start else 0)
        aggregate = None
        spec = self.cfg['aggregate_amount'].get(target)
        if spec and isinstance(payload, dict) and type(payload.get('amount')) in (int, float):
            start = now - now % spec['seconds']; rec = state['aggregates'].get(grant['agent'] + '|' + target)
            aggregate = dict(cap=spec['cap'], amount=payload['amount'], used=rec['used'] if rec and rec['start'] == start else 0)
        levels, unknown = [], []
        for lv, ident in (claims.get('hierarchy') or {}).items():
            rec = state['budgets'].get(lv, {}).get(ident)
            (levels if rec else unknown).append(dict(level=lv, id=ident, **rec) if rec else dict(level=lv, id=ident))
        chain_agents = [state['agents'].get(a) for a in claims.get('chain', [])]
        return dict(request=dict(grant=args['grant'], effect=args['effect'], generation=args['generation'],
                                 policy=args['policy'], target=target, payload=payload, claims=claims),
                    now=now, last_now=state['last_now'], environment=state['environment'], config=self.cfg,
                    grant=grant, agent=agent, tool=tool, tool_norm_peers=peers, user=user, user_known=user is not None,
                    delegation=deleg, chain_agents=chain_agents, window=window, aggregate=aggregate,
                    budget_levels=levels, budget_unknown=unknown, approval=state['approvals'].get(binding),
                    verifier_valid=valid, disabled=list(self.disabled))

    def claims_well_formed(self, args):
        c = args['issuer_claims']
        if not isinstance(c, dict): return False
        chain = c.get('chain', [])
        if not (isinstance(chain, list) and all(isinstance(a, str) for a in chain)): return False
        h = c.get('hierarchy', {})
        return isinstance(h, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in h.items())

    # ---- apply ---------------------------------------------------------------
    def apply(self, request):
        with sqlite3.connect(self.path, timeout=10) as c:
            c.execute('BEGIN IMMEDIATE')
            state = json.loads(c.execute('SELECT body FROM state').fetchone()[0])
            body = request['body']; args = body['arguments']; identity = body['id']
            reason, duplicate, dirty, alert, skipped, reasons = None, False, False, False, False, []
            try:
                if request['issuer'] != 'broker' or request['kind'] != 'destination-command':
                    raise ValueError('SIGNER_SCOPE')
                verify(request, self.registry, at=body['at'], now=self.now)
            except ValueError:
                reason = 'AUTHENTICATION_DENIED'
            committed = {k: v for k, v in args.items() if k not in ('issuer_claims', 'verifier_status')}
            binding = digest(committed)
            grant = state['grants'].get(args['grant']) if isinstance(args.get('grant'), str) else None
            tool = state['tools'].get(args['target']) if isinstance(args.get('target'), str) else None
            if reason is None and (grant is None or args['generation'] != state['generation']
                                   or args['generation'] != grant['generation']
                                   or (tool is not None and args['policy'] != tool['approved']['policy'])):
                reason = 'BINDING_DENIED'
            if reason is None and not self.claims_well_formed(args):
                reason = 'CLAIMS_INVALID'
            prior = c.execute('SELECT request FROM effects WHERE id=?', (args['effect'],)).fetchone()
            if reason is None and prior:
                if prior[0] != binding: reason = 'EFFECT_ID_CONFLICT'
                else: duplicate = True
            if reason is None and not duplicate:
                valid = False
                try:
                    rec = args['verifier_status']; st = rec['body']
                    verify(rec, self.registry, at=st['at'], now=self.now)
                    valid = (rec['issuer'] == 'verifier' and rec['kind'] == 'destination-status'
                             and st['command'] == identity and st['request_digest'] == binding
                             and st['generation'] == state['generation'] and st['active'] is True
                             and st['at'] == self.now < st['expires_at'])
                except (ValueError, TypeError, KeyError): pass
                facts = self.facts(state, args, binding, valid)
                reasons = self.decide(facts, state['opa_available'])
                if reasons is None:  # policy engine unreachable
                    if state['fail_mode'] == 'closed': reason = 'POLICY_ENGINE_UNAVAILABLE'
                    else: skipped = True
                elif reasons:
                    reason = self.first_reason(reasons)
                    if reasons == ['APPROVAL_PENDING']:
                        state['pending'][args['effect']] = dict(binding=binding, user=args['issuer_claims'].get('user'))
                        dirty = True
                if reason is None:
                    c.execute('INSERT INTO effects VALUES(?,?,?)',
                              (args['effect'], binding, json.dumps(args['payload'], separators=(',', ':'), sort_keys=True)))
                    alert = self.commit_counters(state, args, facts, skipped)
                    dirty = True
            if reason not in (None, 'AUTHENTICATION_DENIED') or dirty:
                state['last_now'] = max(state['last_now'], self.now); dirty = True
            if dirty:
                c.execute('UPDATE state SET body=?', (json.dumps(state),))
            output = {'status': 'denied' if reason else 'accepted', 'reason': reason, 'result': {'duplicate': duplicate}}
            c.execute('INSERT INTO events(body) VALUES(?)', (json.dumps(dict(operation='execute', command=identity,
                request_digest=digest(request), status=output['status'], reason=reason, at=self.now,
                command_authenticated=reason != 'AUTHENTICATION_DENIED', threshold_alert=alert,
                hold=reason == 'APPROVAL_PENDING', policy_skipped=skipped, reasons=reasons or ([reason] if reason else []))),))
            return output

    def record_denial(self, request, reason):
        """Record one denied-execute event outside `apply` (used by the LangGraph layer for a pending,
        rejected or timed-out approval). Same events(body) keys as `apply` writes for a denial; own writer
        transaction; touches no state row and no effect. An audit-storage abort (sqlite3.IntegrityError)
        propagates. command_authenticated is judged exactly as `apply` judges it."""
        body = request['body']
        try:
            if request['issuer'] != 'broker' or request['kind'] != 'destination-command':
                raise ValueError('SIGNER_SCOPE')
            verify(request, self.registry, at=body['at'], now=self.now)
            authenticated = True
        except (ValueError, KeyError, TypeError):
            authenticated = False
        with sqlite3.connect(self.path, timeout=10) as c:
            c.execute('BEGIN IMMEDIATE')
            c.execute('INSERT INTO events(body) VALUES(?)', (json.dumps(dict(
                operation='execute', command=body['id'], request_digest=digest(request), status='denied',
                reason=reason, at=self.now, command_authenticated=authenticated, threshold_alert=False,
                hold=reason == 'APPROVAL_PENDING', policy_skipped=False, reasons=[reason])),))

    def commit_counters(self, state, args, facts, skipped):
        grant = state['grants'][args['grant']]; target = args['target']; now = self.now; alert = False
        grant['consumed'] += 1
        spec = self.cfg['windows'].get(target)
        if spec:
            start = now - now % spec['seconds']; key = grant['agent'] + '|' + target
            rec = state['windows'].get(key)
            if not rec or rec['start'] != start: rec = dict(start=start, used=0)
            rec['used'] += 1; state['windows'][key] = rec
            alert = rec['used'] >= self.cfg['alert_fraction'] * spec['cap']
        if facts['aggregate'] is not None:
            spec = self.cfg['aggregate_amount'][target]; start = now - now % spec['seconds']
            key = grant['agent'] + '|' + target; rec = state['aggregates'].get(key)
            if not rec or rec['start'] != start: rec = dict(start=start, used=0)
            rec['used'] += facts['aggregate']['amount']; state['aggregates'][key] = rec
        for lv in facts['budget_levels']:
            state['budgets'][lv['level']][lv['id']]['used'] += 1
        return alert
