#!/usr/bin/env python3
"""Static validation of plans/wiki-subset-plan.json (no scenario is executed here).

Checks (all from reading the pinned runner and the comparator applications; nothing from any OCS test or result):
 1. runner schema: top-level keys read by run_comparative_governance.main, case keys read by run_case/evaluate, step actions and
    their keys, request fields (the eight), faults, clock steps;
 2. interface support: every control step and fault exists on BOTH comparator applications (class introspection when the apps import, plus the
    declared-interface JSON files); control arguments name things that exist in the declared world at that point of the steps;
 3. world fit: grants, targets, agents, users, delegation, hierarchy levels, claim keys, payload keys;
 4. bookkeeping: statuses vs execute count, accepted count vs expected_effects vs allowed_effect_ids, one expected_payload for all
    accepted calls, clock monotone within 100..999, no expected_reasons;
 5. outcomes unchanged: expected statuses and effects equal the values of expected-outcomes/outcomes-final.json for every executable scenario (and are carried for the
    non-executed author reclassifications); the 121 outcome scenario ids are each present once;
 6. an authoring lint on calls that are expected ACCEPTED (static preconditions from the declared world only: grant live at the
    clock, tool in the registry and on the allow-list, entitled user, schema, parameter limits, window and grant counters). It
    never evaluates an expectation against a configuration.
Exit status 0 only when every check passes. Prints counts per state and the sha256 of the plan.

Usage: python3 validate_plan.py [plan.json]   (needs SCN_HUB_DIR and the pinned dependencies to include the class-introspection checks)
"""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PKG = HERE.parent                      # comparators/wiki
PLAN = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else PKG / 'plans' / 'wiki-subset-plan.json'
sys.path.insert(0, str(PKG.parents[1]))
from comparators.wiki.apps import wiki_config as W  # noqa: E402  (declared world; imports only copy/unicodedata)

ERR, WARN, INFO = [], [], []
RUNNER_ACTIONS = {'execute', 'capture', 'alter_captured', 'submit', 'clock', 'parallel', 'crash_before_commit', 'crash_after_commit'}
REQUEST_FIELDS = {'grant', 'effect', 'generation', 'policy', 'target', 'payload', 'verifier_status', 'issuer_claims'}
BASE_CONTROLS = {'revoke', 'fence', 'rotate', 'reopen', 'break_audit', 'opa_down', 'opa_up', 'fail_open', 'fail_closed'}
VERB_ARITY = {'revoke_grant': (1, 1), 'stop': (1, 1), 'unstop': (1, 1), 'remove_user': (1, 1), 'revoke_delegation': (1, 1),
              'allow_tool': (2, 2), 'grant_exception': (3, 3), 'mutate_tool': (2, 2), 'reapprove_tool': (1, 1),
              'add_tool': (2, 3), 'pend_tool': (1, 1), 'change_agent': (2, 2), 'reapprove_agent': (1, 1),
              'approve': (2, 2), 'reject': (1, 1), 'timeout': (1, 1),
              'disallow_tool': (2, 2), 'set_budget': (3, 3), 'set_environment': (1, 1)}
CLAIM_KEYS = {'user', 'agent', 'environment', 'delegation_id', 'chain', 'task_expires_at', 'hierarchy', 'task_tools'}
PAYLOAD_KEYS_READ = {'recipient', 'path', 'amount', 'records', 'scope', 'resource', 'operation', 'user', 'claimed_user', 'on_behalf_of',
                     'data_owner', 'data_class'}
FAULTS = {None, 'missing_verifier', 'stale_verifier', 'forged_signature', 'wrong_actor'}


def err(sid, msg): ERR.append('%s: %s' % (sid, msg))


plan_bytes = PLAN.read_bytes()
plan = json.loads(plan_bytes)
outcomes = json.loads((PKG / 'expected-outcomes/outcomes-final.json').read_text())
K = {s['scenario']: s for s in outcomes['scenarios']}

# ---------------------------------------------------------------- 1. top-level runner schema
for key, typ in (('schema', str), ('repetitions', int), ('seeds', list), ('mutations', dict), ('not_run', dict), ('cases', list), ('profiles', list)):
    if not isinstance(plan.get(key), typ): err('plan', 'top-level key %s missing or not %s' % (key, typ.__name__))
if plan.get('seeds') != [1701, 1702]: err('plan', 'seeds must be [1701, 1702]')
if plan.get('repetitions') != 5: err('plan', 'repetitions must be 5')
if plan.get('mutations') != {}: err('plan', 'mutations must be empty (the registered ablations belong to the registered plans)')
if plan.get('schema') != 'cognous.comparative-governance-plan/1': err('plan', 'schema string differs from the registered plan format')
if 'expected_reasons' in json.dumps(plan['cases']): err('plan', 'expected_reasons must be omitted for every Wiki scenario')

# ---------------------------------------------------------------- 2. interface support
APPS = {}
try:
    import os
    from comparators.wiki.apps.wiki_opa_app import WikiOpaApp
    from comparators.wiki.apps.wiki_langgraph_app import WikiLangGraphOPA
    APPS = {'opa-transactional-application': WikiOpaApp, 'langgraph-opa-transactional-application': WikiLangGraphOPA}
    INFO.append('class introspection: both comparator applications imported')
except Exception as exc:  # no cryptography / langgraph in this interpreter
    WARN.append('class introspection skipped (%s); using the declared-interface JSON only' % type(exc).__name__)
DECL_OPA = json.loads((PKG / 'interface/declared-interface-opa-app.json').read_text())
DECL_LG = json.loads((PKG / 'interface/langgraph-opa-declared-interface.json').read_text())
declared_base = set(DECL_OPA['zero_argument_controls']['base']) | set(DECL_OPA['zero_argument_controls']['engine'])
declared_verbs = {v.split(':')[0] for v in DECL_OPA['zero_argument_controls']['verbs (grammar verb:arg:arg through __getattr__)']}
declared_faults = set(DECL_OPA['faults'])
if not BASE_CONTROLS <= declared_base: err('interface', 'base controls differ from declared: %s' % (BASE_CONTROLS - declared_base))
if set(VERB_ARITY) != declared_verbs: err('interface', 'verb list differs from the declared interface: %s' % (set(VERB_ARITY) ^ declared_verbs))
if FAULTS - {None} != declared_faults: err('interface', 'fault list differs from the declared interface')
for name, cls in APPS.items():
    for c in BASE_CONTROLS:
        if not callable(getattr(cls, c, None)): err('interface', '%s lacks control %s' % (name, c))
    for verb, (lo, hi) in VERB_ARITY.items():
        h = getattr(cls, '_verb_' + verb, None)
        if h is None: err('interface', '%s lacks verb %s' % (name, verb)); continue
        import inspect
        params = list(inspect.signature(h).parameters)[1:]
        required = sum(1 for p in inspect.signature(h).parameters.values() if p.default is inspect._empty) - 1
        if (required, len(params)) != (lo, hi): err('interface', '%s verb %s arity %s differs from %s' % (name, verb, (required, len(params)), (lo, hi)))

# ---------------------------------------------------------------- world model (declared, static)
def new_world():
    st = W.initial_state()
    return dict(tools={k: dict(trusted=v['trusted']) for k, v in st['tools'].items()},
                allow={a: list(r['allowed_targets']) for a, r in st['agents'].items()},
                exceptions={a: [] for a in st['agents']}, grants=st['grants'], users=st['users'], delegations=st['delegations'],
                hierarchy=st['budgets'], used={}, pend={}, environment=st['environment'])


NEEDS_APPROVAL = set(W.CONFIG['approval_required_targets'])


def check_control(sid, name, world):
    if name in BASE_CONTROLS: return
    if ':' not in name: err(sid, 'control %r is neither a base control nor a verb:arg form' % name); return
    verb, *a = name.split(':')
    if verb not in VERB_ARITY: err(sid, 'unknown verb %r' % verb); return
    lo, hi = VERB_ARITY[verb]
    if not lo <= len(a) <= hi: err(sid, 'verb %s takes %d..%d arguments, got %d' % (verb, lo, hi, len(a))); return
    if verb in ('stop', 'unstop', 'change_agent', 'reapprove_agent') and a[0] not in world['allow']: err(sid, 'unknown agent %s' % a[0])
    if verb == 'allow_tool':
        if a[0] not in world['allow']: err(sid, 'unknown agent %s' % a[0])
        elif a[1] not in world['tools']: err(sid, 'allow_tool: tool %s not in the registry at this point' % a[1])
        else: world['allow'][a[0]].append(a[1])
    if verb == 'grant_exception':
        if a[0] not in world['allow']: err(sid, 'unknown agent %s' % a[0])
        if not a[2].isdigit(): err(sid, 'ttl must be an integer')
        else: world['exceptions'][a[0]].append((a[1], world['clock'] + int(a[2])))
    if verb == 'disallow_tool':
        if a[0] not in world['allow']: err(sid, 'unknown agent %s' % a[0])
        elif a[1] not in world['allow'][a[0]]: err(sid, 'disallow_tool: %s is not on the allow-list of %s at this point' % (a[1], a[0]))
        else: world['allow'][a[0]] = [t for t in world['allow'][a[0]] if t != a[1]]
    if verb == 'set_budget':
        rec = world['hierarchy'].get(a[0], {}).get(a[1])
        if rec is None: err(sid, 'set_budget: unknown budget %s/%s' % (a[0], a[1]))
        elif not a[2].isdigit(): err(sid, 'set_budget: cap must be a non-negative integer')
        else: rec['cap'] = int(a[2])
    if verb == 'set_environment':
        if a[0] not in ('prod', 'non-prod'): err(sid, 'set_environment: unknown environment %s' % a[0])
        else: world['environment'] = a[0]
    if verb == 'revoke_grant':
        if a[0] not in world['grants']: err(sid, 'unknown grant %s' % a[0])
        else: world['grants'][a[0]]['revoked'] = True
    if verb == 'revoke_delegation':
        if a[0] not in world['delegations']: err(sid, 'unknown delegation %s' % a[0])
        else: world['delegations'][a[0]]['revoked'] = True
    if verb == 'remove_user' and a[0] not in world['users']: err(sid, 'unknown user %s' % a[0])
    if verb in ('mutate_tool', 'reapprove_tool', 'pend_tool'):
        if a[0] not in world['tools']: err(sid, '%s: tool %s not in the registry' % (verb, a[0]))
        if verb == 'mutate_tool':
            if a[1] not in ('description', 'new_parameter', 'rename', 'scope'): err(sid, 'unknown tool field %s' % a[1])
            world['tools'][a[0]]['mutated'] = True
        if verb in ('reapprove_tool',): world['tools'][a[0]].pop('mutated', None); world['tools'][a[0]].pop('pending', None)
        if verb == 'pend_tool': world['tools'][a[0]]['pending'] = True
    if verb == 'change_agent':
        if a[1] not in ('model', 'prompt', 'tool', 'data_scope', 'owner'): err(sid, 'unknown agent component %s' % a[1])
        elif a[1] in W.MATERIAL_AGENT_COMPONENTS: world.setdefault('pending_agent', set()).add(a[0])
    if verb == 'reapprove_agent': world.setdefault('pending_agent', set()).discard(a[0])
    if verb == 'add_tool':
        name, key = a[1], (a[1] if a[1] not in world['tools'] else a[0] + '/' + a[1])
        world['tools'][key] = dict(trusted=len(a) > 2 and a[2] == 'trusted')
    if verb in ('approve', 'reject', 'timeout'):
        eff = a[0]
        if eff not in world['pend']: err(sid, '%s:%s without a pending hold recorded earlier in the steps' % (verb, eff))
        else:
            world['pend'].pop(eff)
            if verb == 'approve': world.setdefault('approved', set()).add(eff)


# ---------------------------------------------------------------- 3/4/6. per-case checks
def norm(n): return W.normalise_name(n)


def lint_accepted(sid, world, args, now):
    """Static preconditions of a call expected ACCEPTED, from the declared world only."""
    g = world['grants'].get(args['grant']); tg = args['target']; p = args['payload']; cl = args.get('issuer_claims') or {}
    if g is None: err(sid, 'accepted call on unknown grant'); return
    ag = g['agent']
    if g.get('revoked'): err(sid, 'lint: accepted call on a revoked grant %s' % args['grant'])
    if now >= g['expires_at']: err(sid, 'lint: grant %s expired at %d, call at %d' % (args['grant'], g['expires_at'], now))
    if g['consumed'] + world['used'].get(args['grant'], 0) >= g['max_effects']: err(sid, 'lint: grant budget exhausted')
    if tg not in world['tools']: err(sid, 'lint: accepted call to unregistered tool %r' % tg); return
    t = world['tools'][tg]
    if t.get('mutated') or t.get('pending'): err(sid, 'lint: accepted call to a tool whose definition is changed or pending')
    peers = [k for k in world['tools'] if k != tg and norm(k.split('/')[-1]) == norm(tg.split('/')[-1])]
    if peers and not t['trusted']: err(sid, 'lint: accepted call to a colliding tool')
    exc = any(e[0] == tg and now < e[1] for e in world['exceptions'][ag])
    if tg not in world['allow'][ag] and not exc: err(sid, 'lint: target %s not on the allow-list of %s' % (tg, ag))
    if tg in W.CONFIG['privileged_targets'] and not exc: err(sid, 'lint: privileged target without exception')
    if tg in W.CONFIG['never_via_agent']: err(sid, 'lint: accepted call to a never-via-agent target')
    if ag in world.get('pending_agent', set()) and tg not in [x for x in world['allow'][ag] if x in ('read_file', 'list_tickets', 'sink')]:
        err(sid, 'lint: agent pending re-approval and target outside the read class')
    if tg in NEEDS_APPROVAL and args['effect'] not in world.get('approved', set()): err(sid, 'lint: accepted call on an approval-gated target without an approval record')  # overridden for the exception scenarios below
    if tg in W.CONFIG['user_required_targets'] and 'user' not in cl: err(sid, 'lint: user required')
    if 'user' in cl:
        u = world['users'].get(cl['user'])
        if u is None or not u['active'] or tg not in u['allowed_targets']: err(sid, 'lint: user not entitled')
        if isinstance(p, dict):
            for k in W.CONFIG['identity_payload_keys']:
                if k in p and p[k] != cl['user']: err(sid, 'lint: identity key differs from claims.user')
            if 'data_owner' in p and p['data_owner'] != cl['user']: err(sid, 'lint: data_owner differs')
    if 'agent' in cl and cl['agent'] != ag: err(sid, 'lint: claims.agent differs from the grant agent')
    if g['environment'] != world['environment']: err(sid, 'lint: grant environment differs from the destination')
    if cl.get('environment', world['environment']) != world['environment']: err(sid, 'lint: claims.environment differs from the destination')
    if 'task_tools' in cl and tg not in cl['task_tools']: err(sid, 'lint: target not among claims.task_tools')
    if 'delegation_id' in cl:
        d = world['delegations'].get(cl['delegation_id'])
        if d is None or d['revoked'] or now >= d['expires_at'] or d['user'] != cl.get('user') or tg not in d['targets'] \
                or (isinstance(p, dict) and 'data_class' in p and p['data_class'] not in d['data_classes']): err(sid, 'lint: delegation does not cover the call')
    for i, a in enumerate(cl.get('chain', [])):
        if a not in world['allow'] or tg not in world['allow'][a]: err(sid, 'lint: chain member %s does not hold %s' % (a, tg))
    if cl.get('chain') and (len(cl['chain']) > W.CONFIG['max_delegation_depth'] or cl['chain'][-1] != ag): err(sid, 'lint: chain invalid')
    if isinstance(p, dict):
        sch = W.CONFIG['schemas'].get(tg)
        if sch:
            allowed = set(sch['required']) | set(sch['optional']) | {'scope', 'resource', 'operation', 'user', 'claimed_user', 'on_behalf_of', 'data_owner', 'data_class'}
            if not set(p) <= allowed or not set(sch['required']) <= set(p): err(sid, 'lint: payload violates the closed schema of %s' % tg)
            for k, typ in {**sch['required'], **sch['optional']}.items():
                if k in p and {'string': str, 'number': (int, float)}[typ] is not None and not isinstance(p[k], {'string': str, 'number': (int, float)}[typ]): err(sid, 'lint: type of %s' % k)
        if 'recipient' in p and p['recipient'].split('@')[-1] not in W.CONFIG['allowed_domains']: err(sid, 'lint: recipient domain')
        if 'path' in p and (not any(p['path'].startswith(x) for x in W.CONFIG['allowed_path_prefixes']) or '..' in p['path']): err(sid, 'lint: path')
        if 'amount' in p and not (0 < p['amount'] <= W.CONFIG['amount_limit']): err(sid, 'lint: amount')
        if 'records' in p and not (1 <= p['records'] <= W.CONFIG['max_records']): err(sid, 'lint: records')
        if 'scope' in p and p['scope'] not in g['scopes']: err(sid, 'lint: scope not on the grant')
        if 'resource' in p and ('scope' not in p or p['scope'].split(':')[1] != p['resource']): err(sid, 'lint: resource/scope')
        if 'operation' in p and p['operation'] not in W.agent_record(ag)['operations']: err(sid, 'lint: operation')
    elif tg in W.CONFIG['schemas']: err(sid, 'lint: non-object payload on a schema tool')
    spec = W.CONFIG['windows'].get(tg)
    if spec:
        used = world['used'].get(ag + '|' + tg, 0)
        if used >= spec['cap']: err(sid, 'lint: window cap reached')
        world['used'][ag + '|' + tg] = used + 1
    for lv, ident in (cl.get('hierarchy') or {}).items():
        rec = world['hierarchy'].get(lv, {}).get(ident)
        if rec is None: err(sid, 'lint: unknown hierarchy %s/%s' % (lv, ident)); continue
        k2 = 'h|%s|%s' % (lv, ident)
        if world['used'].get(k2, 0) >= rec['cap']: err(sid, 'lint: hierarchy budget reached')
        world['used'][k2] = world['used'].get(k2, 0) + 1
    world['used'][args['grant']] = world['used'].get(args['grant'], 0) + 1


EXCEPTION_SCENARIOS = {'TC-L02-011-S3'}   # asks whether an exception record opens an approval-gated target: the approval lint is waived on purpose
seen_ids = []
executable = []
for case in plan['cases']:
    sid = case.get('id'); seen_ids.append(sid); executable.append(sid)
    for key in ('id', 'steps', 'expected_statuses', 'expected_effects', 'allowed_effect_ids', 'expected_payload'):
        if key not in case: err(sid, 'missing runner key %s' % key)
    if not (isinstance(case['steps'], list) and case['steps']): err(sid, 'steps must be a non-empty list'); continue
    if case['expected_effects'] != len(case['allowed_effect_ids']): err(sid, 'expected_effects != len(allowed_effect_ids)')
    world = new_world(); world['clock'] = 100; now = 100
    statuses, accepted = [], []
    for st in case['steps']:
        act = st.get('action')
        if not isinstance(act, str): err(sid, 'step without action'); continue
        extra = set(st) - {'action', 'args', 'fault', 'now'}
        if extra: err(sid, 'step keys not read by the runner: %s' % extra)
        if act == 'clock':
            if not isinstance(st.get('now'), int): err(sid, 'clock step needs an int now'); continue
            if st['now'] < now: err(sid, 'clock moves backwards')
            if not 100 <= st['now'] <= 999: err(sid, 'clock reading %s outside the usable 100..999' % st['now'])
            now = world['clock'] = st['now']
        elif act == 'execute':
            args = st.get('args') or {}
            if set(args) - REQUEST_FIELDS: err(sid, 'request fields outside the eight: %s' % (set(args) - REQUEST_FIELDS))
            if st.get('fault') not in FAULTS: err(sid, 'unknown fault %r' % st.get('fault'))
            full = dict(grant='grant', effect='effect', generation=7, policy='policy1', target='sink', payload='synthetic', issuer_claims={})
            full.update(args)
            if full['grant'] not in world['grants']: err(sid, 'unknown grant %s' % full['grant'])
            claims = full['issuer_claims']
            if not isinstance(claims, dict) or set(claims) - CLAIM_KEYS: err(sid, 'claims keys outside the declared set')
            if isinstance(full['payload'], dict):
                unknown = set(full['payload']) - PAYLOAD_KEYS_READ
                if unknown: INFO.append('%s: free-text payload keys (not read by any rule): %s' % (sid, sorted(unknown)))
            if full['target'] in NEEDS_APPROVAL: world['pend'].setdefault(full['effect'], True)
            statuses.append(None); accepted.append((full, now))
        elif act in RUNNER_ACTIONS:
            err(sid, 'runner action %s is not used by Wiki steps' % act)
        else:
            check_control(sid, act, world)
            if act.startswith(('approve:', 'reject:', 'timeout:')): pass
    # replay for statuses: recompute expected from outcomes and lint accepted calls in order
    k = K.get(sid)
    if k is None: err(sid, 'not an outcome-file scenario'); continue
    if k['state'] != 'ASKED': err(sid, 'executable entry for a scenario that the outcome files do not mark ASKED')
    if case['expected_statuses'] != k['expected_statuses']: err(sid, 'expected_statuses differ from the outcome files')
    if case['expected_effects'] != k['expected_effects']: err(sid, 'expected_effects differ from the outcome files')
    if len(accepted) != len(case['expected_statuses']): err(sid, 'execute count %d != expected_statuses %d' % (len(accepted), len(case['expected_statuses'])))
    if set(case['expected_statuses']) - {'accepted', 'denied'}: err(sid, 'status vocabulary')
    ok_calls = [c for c, s in zip(accepted, case['expected_statuses']) if s == 'accepted']
    if len(ok_calls) != case['expected_effects']: err(sid, 'accepted statuses != expected_effects')
    ids = [c[0]['effect'] for c in ok_calls]
    if ids != case['allowed_effect_ids']: err(sid, 'allowed_effect_ids must equal the effect ids of the expected-accepted calls, in order')
    if len(set(ids)) != len(ids): err(sid, 'duplicate effect ids among accepted calls')
    for c in ok_calls:
        if c[0]['payload'] != case['expected_payload']: err(sid, 'an accepted call payload differs from expected_payload')
    # second pass: static lint of accepted calls with the world as of that call
    world = new_world(); world['clock'] = 100; now = 100; idx = 0; pend_seen = {}
    for st in case['steps']:
        act = st['action']
        if act == 'clock': now = world['clock'] = st['now']
        elif act == 'execute':
            full = dict(grant='grant', effect='effect', target='sink', payload='synthetic', issuer_claims={}); full.update(st.get('args') or {})
            if case['expected_statuses'][idx] == 'accepted':
                before = len(ERR); lint_accepted(sid, world, full, now)
                if sid in EXCEPTION_SCENARIOS:  # waive only the approval-gated line
                    ERR[:] = [e for e in ERR if not (e.startswith(sid) and 'approval-gated target without an approval record' in e)]
            else:
                if full['target'] in NEEDS_APPROVAL and full['effect'] not in world['pend']: world['pend'][full['effect']] = True
            idx += 1
        elif act not in RUNNER_ACTIONS: check_control(sid + '#lint', act, world)

# ---------------------------------------------------------------- 5. coverage and states
by_state = {'ASKED': 0, 'NOT-EXPRESSIBLE': 0, 'NOT-CLAIMED': 0, 'UNASKED': 0}
ne_ids = []
for x in plan['non_executed']:
    sid = x['id']; seen_ids.append(sid)
    if x['state'] not in ('NOT-EXPRESSIBLE', 'UNASKED'): err(sid, 'non-executed entry with state %s' % x['state'])
    if not x.get('citations'): err(sid, 'non-executed entry without citations')
    if not x.get('reason'): err(sid, 'non-executed entry without reason')
    if x['state'] == 'UNASKED' and K[sid]['state'] != 'UNASKED': err(sid, 'state differs from the outcome files')
    if x['state'] == 'NOT-EXPRESSIBLE' and K[sid]['state'] == 'ASKED':
        if x.get('outcome_expected_statuses') != K[sid]['expected_statuses'] or x.get('outcome_expected_effects') != K[sid]['expected_effects']:
            err(sid, 'author-reclassified scenario does not carry the outcome-file expected outcome unchanged')
    by_state[x['state']] += 1
by_state['ASKED'] = len(plan['cases'])
if sorted(seen_ids) != sorted(K): err('plan', 'scenario ids differ from the 121 outcome-file ids (missing %s, extra %s)' % (sorted(set(K) - set(seen_ids)), sorted(set(seen_ids) - set(K))))
if len(seen_ids) != len(set(seen_ids)): err('plan', 'duplicate scenario ids')
outcome_asked = sum(1 for s in K.values() if s['state'] == 'ASKED')
author_ne = [x['id'] for x in plan['non_executed'] if K[x['id']]['state'] == 'ASKED']
if by_state['ASKED'] + len(author_ne) != outcome_asked: err('plan', 'executable + author-reclassified != outcome-file ASKED (%d)' % outcome_asked)
if plan['counts_per_state'] != by_state: err('plan', 'counts_per_state in the file differ from the recount %s' % by_state)

sha = hashlib.sha256(plan_bytes).hexdigest()
print('plan:', PLAN)
print('sha256:', sha)
print('outcomes-final.json sha256:', hashlib.sha256((PKG / 'expected-outcomes/outcomes-final.json').read_bytes()).hexdigest())
print('counts per state (final):', json.dumps(by_state))
print('outcome-file counts per state:', json.dumps(outcomes['counts_per_state']))
print('plan-authoring reclassifications (asked in the outcome files, not expressible in the comparator world): %d %s' % (len(author_ne), author_ne))
print('executable scenarios: %d; execute steps in total: %d' % (len(plan['cases']), sum(1 for c in plan['cases'] for s in c['steps'] if s['action'] == 'execute')))
for line in INFO[:3]: print('info:', line)
for w in WARN: print('warn:', w)
print('errors: %d' % len(ERR))
for e in ERR[:80]: print('  ERROR', e)
sys.exit(1 if ERR else 0)
