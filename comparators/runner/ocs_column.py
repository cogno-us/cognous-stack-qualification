"""The protected-destination column of the Wiki-subset comparison.

Decision D1 (amendment 76): the registered OCS reference configuration for the Wiki subset is the hub's protected
destination, scored by the same oracle as the two comparator applications. This module holds

  1. the declared interface of the protected destination (what a request can carry, which operations and controls exist),
     each item with a marker text that the cited source line must contain (checked by the tests);
  2. the step rules: a scenario step is applied to the destination exactly when this declared interface can express it;
  3. the rule-based declaration of one scenario as ASKED, NOT-EXPRESSIBLE or NOT-CLAIMED, with citations;
  4. the adapter class (a subclass of the registered Cognous adapter) that applies the expressible steps.

Nothing here reads a result, an expected outcome or the behaviour of any configuration. The declaration of a scenario depends
on its steps and on the sentences cited, never on its expected statuses. The destination is not changed and no check is
added to it.
"""
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
CMP = HERE.parent
REPO = CMP.parent

OCS_PROFILE = 'cognous-protected-destination'
HUB_REPO = 'cogno-us/cognous-open-control-stack'
HUB_REVISION = '8517818fbf817897aacfb6fe7898c22aea46fd95'
HUB_FILE = 'reference_profiles/protected_destination.py'
HUB_FILE_SHA256 = '5947adbe1a8c75ed20ddea911b42a75ce75bfa6442e3afe97ed1fb7546d62bc9'
ADAPTERS_FILE = 'suites/cognous-open-control-stack/benchmarks/governance/adapters.py'
APPLICABILITY_FILE = 'scenarios/ai-security-wiki/applicability.json'
APPLICABILITY_VERSION = '1.0.0'
APPLICABILITY_CATALOG_COMMIT = '1a0c72de4752a1c6932172e5e7dbf14f755799c8'

REQUEST_FIELDS = ('grant', 'effect', 'generation', 'policy', 'target', 'payload', 'verifier_status', 'issuer_claims')
KNOWN_FAULTS = (None, 'missing_verifier', 'stale_verifier', 'forged_signature', 'wrong_actor')
# The registered fixture provisions one grant that pins this target; the Wiki-world grants are provisioned the same way.
PINNED_TARGET = 'sink'
PINNED_POLICY = 'policy1'
# One grant of the registered fixture has this principal; the destination keeps its grant view per principal.
FIXTURE_PRINCIPAL = 'agent'

STATUS_ASKED = 'ASKED'
STATUS_NE = 'NOT-EXPRESSIBLE'
STATUS_NC = 'NOT-CLAIMED'

# ----------------------------------------------------------------------------------------------------------------------
# 1. Declared interface of the protected destination. `file` is relative to the hub checkout (hub:) or to the repository
#    root (repo:); `marker` is a text that the file must contain.
# ----------------------------------------------------------------------------------------------------------------------
INTERFACE = {
    'DEST-EXEC-ARGS': dict(
        description='The execute operation takes exactly eight argument fields: grant, effect, generation, policy, target, payload, '
                    'verifier_status, issuer_claims. Any other field is refused.',
        file='hub:' + HUB_FILE, marker="exact(a,'grant effect generation policy target payload verifier_status issuer_claims')"),
    'DEST-GRANT-FIELDS': dict(
        description='A grant record has exactly these fields: id, scope, generation, principal, policy, target, credential_version, '
                    'dependency_version, modes, max_effects, expires_at. There is no field for an agent, a user, a set of tools, an '
                    'approval, a window, a parent or a budget level other than max_effects.',
        file='hub:' + HUB_FILE,
        marker="exact(a,'id scope generation principal policy target credential_version dependency_version modes max_effects expires_at')"),
    'DEST-TARGET-PIN': dict(
        description='A grant pins exactly one target and one policy; a request whose target or policy differs from the grant is refused '
                    'by the hard pin.',
        file='hub:' + HUB_FILE, marker="require(a['policy']==g['policy'] and a['target']==g['target'],'HARD_PIN_CHANGED')"),
    'DEST-OPERATIONS': dict(
        description='The destination accepts a closed list of operations: fence, destination_grants, provision, revoke, execute, '
                    'ingress_recover. There is no operation for stopping an agent, recording a delegation, an exception, an approval '
                    'or a tool, or for changing a policy engine.',
        file='hub:' + HUB_FILE, marker="require(operation in ('fence','destination_grants','provision','revoke','execute','ingress_recover'),'UNKNOWN_OPERATION')"),
    'DEST-REVOKE': dict(
        description='The revoke operation takes one field, grant, and closes that grant.',
        file='hub:' + HUB_FILE, marker="exact(a,'grant');g=self.get(c,'grant',a['grant']);g['revoked']=True"),
    'DEST-CLAIMS-DIGEST': dict(
        description='issuer_claims is carried and bound into the request, but the destination only records its digest in the '
                    'resolution input; no decision reads a claim.',
        file='hub:' + HUB_FILE, marker="'issuer_context_digest':digest(a['issuer_claims'])"),
    'DEST-PAYLOAD-OPAQUE': dict(
        description='payload is bound by the request digest and stored as canonical text; the destination does not read inside it.',
        file='hub:' + HUB_FILE, marker="canonical(a['payload'])"),
    'DEST-BUDGET': dict(
        description='One budget level per grant: max_effects counts the effects of that grant.',
        file='hub:' + HUB_FILE, marker="g['consumed']<g['max_effects']"),
    'DEST-EXPIRY': dict(
        description='A grant expires at expires_at, read from the host clock; the expiry instant is outside the grant.',
        file='hub:' + HUB_FILE, marker="require(self.now()<g['expires_at'],'CREDENTIAL_EXPIRED')"),
    'DEST-CLOCK': dict(
        description='The destination reads a host clock that the harness sets; a scenario clock step sets it.',
        file='hub:' + HUB_FILE, marker='self.clock = clock'),
    'DEST-INGRESS': dict(
        description='A fixed admission budget of 128 attempts per interval of 60 clock units applies to every command, including the '
                    'commands that provision grants.',
        file='hub:' + HUB_FILE, marker='ATTEMPTS_PER_INTERVAL = 128'),
    'DEST-REOPEN': dict(
        description='The registered adapter reopens the destination from the persisted file.',
        file='repo:' + ADAPTERS_FILE, marker='def reopen(self): self.runtime = ProtectedDestination(self.path'),
    'DEST-CONTROLS': dict(
        description='The registered adapter offers the zero-argument controls revoke (the default grant), fence, rotate, reopen and '
                    'break_audit.',
        file='repo:' + ADAPTERS_FILE, marker='def revoke(self): self.control('),
    'DEST-FAULTS': dict(
        description='The registered request builder offers the faults missing_verifier, stale_verifier, forged_signature and wrong_actor.',
        file='repo:' + ADAPTERS_FILE, marker="if fault == 'forged_signature'"),
}

# Controls that the destination interface can express, with the interface item that carries each.
EXPRESSIBLE_ZERO_ARG = {
    'revoke': 'DEST-CONTROLS', 'fence': 'DEST-CONTROLS', 'rotate': 'DEST-CONTROLS', 'reopen': 'DEST-REOPEN',
    'break_audit': 'DEST-CONTROLS',
}
# Runner-level actions that act on the signed request and the clock, as for the registered sets.
EXPRESSIBLE_RUNNER_ACTIONS = ('execute', 'capture', 'alter_captured', 'submit', 'clock', 'parallel',
                              'crash_before_commit', 'crash_after_commit')
# Controls with arguments (verb:arg:arg). Only revoke_grant has a counterpart: the revoke operation of one grant.
EXPRESSIBLE_VERBS = {'revoke_grant': 'DEST-REVOKE'}
# Controls that have no counterpart, each with the absence that is cited.
NOT_EXPRESSIBLE_CONTROLS = {
    'stop': ('NE-AGENT', 'stopping one agent: the destination has no agent object and no stop operation; a grant can be revoked but '
                         'the control names an agent', ['DEST-OPERATIONS', 'DEST-GRANT-FIELDS']),
    'unstop': ('NE-AGENT', 'resuming one agent: the destination has no agent object and no stop operation',
               ['DEST-OPERATIONS', 'DEST-GRANT-FIELDS']),
    'remove_user': ('NE-USER', 'deactivating a user: the destination has no user object', ['DEST-OPERATIONS', 'DEST-GRANT-FIELDS']),
    'revoke_delegation': ('NE-DELEGATION', 'revoking a delegation record: the destination has no delegation record and a grant has no '
                                           'parent field', ['DEST-OPERATIONS', 'DEST-GRANT-FIELDS']),
    'allow_tool': ('NE-TOOL-SET', 'adding a tool to an agent allow-list: a grant pins one target and the destination has no allow-list',
                   ['DEST-TARGET-PIN', 'DEST-GRANT-FIELDS']),
    'grant_exception': ('NE-EXCEPTION', 'recording a time-bound exception: the destination has no exception record',
                        ['DEST-OPERATIONS', 'DEST-GRANT-FIELDS']),
    'mutate_tool': ('NE-TOOL-DEFINITION', 'changing a tool definition: the destination has no tool registry or definition',
                    ['DEST-OPERATIONS', 'DEST-GRANT-FIELDS']),
    'reapprove_tool': ('NE-TOOL-DEFINITION', 'approving a tool definition again: the destination has no tool registry or approval state',
                       ['DEST-OPERATIONS', 'DEST-GRANT-FIELDS']),
    'add_tool': ('NE-TOOL-DEFINITION', 'registering a tool: the destination has no tool registry', ['DEST-OPERATIONS', 'DEST-GRANT-FIELDS']),
    'pend_tool': ('NE-TOOL-DEFINITION', 'holding a tool as not yet approved: the destination has no tool registry or approval state',
                  ['DEST-OPERATIONS', 'DEST-GRANT-FIELDS']),
    'change_agent': ('NE-AGENT', 'changing an agent component: the destination has no agent object',
                     ['DEST-OPERATIONS', 'DEST-GRANT-FIELDS']),
    'reapprove_agent': ('NE-AGENT', 'approving an agent change: the destination has no agent object or approval state',
                        ['DEST-OPERATIONS', 'DEST-GRANT-FIELDS']),
    'approve': ('NE-APPROVAL', 'recording an approval: the destination has no approval record or hold state',
                ['DEST-OPERATIONS', 'DEST-GRANT-FIELDS']),
    'reject': ('NE-APPROVAL', 'recording a rejection: the destination has no approval record or hold state',
               ['DEST-OPERATIONS', 'DEST-GRANT-FIELDS']),
    'timeout': ('NE-APPROVAL', 'recording an approval timeout: the destination has no approval record or hold state',
                ['DEST-OPERATIONS', 'DEST-GRANT-FIELDS']),
    'opa_down': ('NE-ENGINE', 'stopping a policy engine: the destination has no separate policy engine; its checks are fixed in the '
                              'execute operation', ['DEST-OPERATIONS']),
    'opa_up': ('NE-ENGINE', 'starting a policy engine: the destination has no separate policy engine', ['DEST-OPERATIONS']),
    'fail_open': ('NE-ENGINE', 'switching a failure mode: the destination has no failure mode to switch', ['DEST-OPERATIONS']),
    'fail_closed': ('NE-ENGINE', 'switching a failure mode: the destination has no failure mode to switch', ['DEST-OPERATIONS']),
}


def interface_item_source(item_id, hub_dir=None):
    """Return (path, text) of the source file of an interface item."""
    kind, _, rel = INTERFACE[item_id]['file'].partition(':')
    if kind == 'hub':
        base = Path(hub_dir or os.environ['SCN_HUB_DIR'])
    else:
        base = REPO
    path = base / rel
    return path, path.read_text()


# ----------------------------------------------------------------------------------------------------------------------
# 2. Step rules
# ----------------------------------------------------------------------------------------------------------------------
def _world_grant_ids():
    from comparators.wiki.apps import wiki_config as W
    return set(W.initial_state()['grants'])


def classify_step(index, step, grant_ids=None):
    """Return None when the destination interface can express the step, else a blocking record."""
    grant_ids = _world_grant_ids() if grant_ids is None else grant_ids
    action = step['action']
    if action == 'execute':
        args = step.get('args') or {}
        extra = sorted(set(args) - set(REQUEST_FIELDS))
        if extra:
            return dict(step=index, action=action, code='NE-FIELD',
                        reason='the request carries field(s) %s that the execute operation does not take' % ', '.join(extra),
                        interface_items=['DEST-EXEC-ARGS'])
        if step.get('fault') not in KNOWN_FAULTS:
            return dict(step=index, action=action, code='NE-FAULT', reason='fault %r is not offered by the request builder' % step.get('fault'),
                        interface_items=['DEST-FAULTS'])
        target = args.get('target', PINNED_TARGET)
        if target != PINNED_TARGET:
            return dict(step=index, action=action, code='NE-TOOL-SET', target=target,
                        reason='a grant of the destination pins exactly one target (%r) and the destination has no allow-list, so the per-agent set '
                               'of tools that the scenario asks about cannot be expressed' % PINNED_TARGET,
                        interface_items=['DEST-TARGET-PIN', 'DEST-GRANT-FIELDS'])
        return None
    if action in EXPRESSIBLE_RUNNER_ACTIONS:
        return None
    if ':' not in action:
        if action in EXPRESSIBLE_ZERO_ARG:
            return None
        if action in NOT_EXPRESSIBLE_CONTROLS:
            code, reason, items = NOT_EXPRESSIBLE_CONTROLS[action]
            return dict(step=index, action=action, code=code, reason=reason, interface_items=list(items))
        return dict(step=index, action=action, code='NE-CONTROL', reason='control %r is not in the declared control list' % action,
                    interface_items=['DEST-OPERATIONS', 'DEST-CONTROLS'])
    verb, *args = action.split(':')
    if verb in EXPRESSIBLE_VERBS:
        if len(args) == 1 and args[0] in grant_ids:
            return None
        return dict(step=index, action=action, code='NE-GRANT', reason='%s names a grant that the declared world does not hold' % verb,
                    interface_items=[EXPRESSIBLE_VERBS[verb]])
    if verb in NOT_EXPRESSIBLE_CONTROLS:
        code, reason, items = NOT_EXPRESSIBLE_CONTROLS[verb]
        return dict(step=index, action=action, code=code, reason=reason, interface_items=list(items))
    return dict(step=index, action=action, code='NE-CONTROL', reason='control verb %r is not in the declared control list' % verb,
                interface_items=['DEST-OPERATIONS', 'DEST-CONTROLS'])


def scenario_digest(case):
    """sha256 of the parts of a plan scenario that a declaration depends on (steps and the identity of the scenario)."""
    body = json.dumps({'id': case['id'], 'steps': case['steps']}, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(body.encode()).hexdigest()


def carries_unread_content(case):
    """True when a call carries claims or payload content, which the destination records but never reads (DEST-CLAIMS-DIGEST,
    DEST-PAYLOAD-OPAQUE). The scenario's own question is then carried in a field that has no meaning at the destination."""
    for step in case['steps']:
        if step['action'] != 'execute':
            continue
        args = step.get('args') or {}
        if args.get('issuer_claims'):
            return True
        if args.get('payload', 'synthetic') != 'synthetic':
            return True
    return False


# ----------------------------------------------------------------------------------------------------------------------
# 3. Declaration of one scenario
# ----------------------------------------------------------------------------------------------------------------------
AMENDMENTS = {
    '39': 'Amendment 39 (registered): TC-D13-003 (nested budget hierarchy) is not claimed by OCS (OD-3); it stays in the subset, OCS is '
          'reported as not claimed for it, and the comparator results are shown without a comparative statement.',
    '74': 'Amendment 74 (registered): outcomes are declared per scenario (asked k of n); a scenario that can technically be run but is '
          'declared not claimed is still run, its observation is retained and printed apart, and is never counted in a pass fraction.',
    '75': 'Amendment 75 (registered): expected outcomes of the Wiki subset are written from the case text by one author and checked by one checker.',
    '76': 'Amendment 76 (registered): the Wiki comparison scores the protected destination and the two comparator applications with the same '
          'oracle; a scenario that asks for something the destination does not claim or cannot be asked carries not claimed or not '
          'expressible, with a citation; each such cell carries a separate cross-reference column labelled `different harness, not scored by '
          'this oracle`.',
    '79-draft': 'Interface declarations and the rule for not expressible and not claimed (restating PR-1 for the Wiki subset): a declaration '
                'of not expressible cites an item of the configuration\'s declared interface and the sentence of the case that needs it; a '
                'declaration of not claimed cites a sentence published before the plan file (for the protected destination a not-claimed '
                'sentence of the applicability file at its pinned revision, or an amendment such as 39); a declaration without a citation is '
                'void and the scenario is asked. This is amendment 79 of the draft batch that has not yet been appended; it is not the '
                'amendment that carries that number in the pre-registration page today, and its number is assigned when it is appended.',
    'PR-1': 'PR-1 and section 7 of the pre-registration (registered text): the outcome not expressible and the rules for declaring and '
            'reporting it.',
}


def load_applicability():
    return json.loads((REPO / APPLICABILITY_FILE).read_text())


def applicability_sentence(case_id, applicability=None):
    applicability = applicability or load_applicability()
    for row in applicability['cases']:
        if row['id'] == case_id:
            return row.get('not_claimed')
    return None


def merged_reason(blocking):
    """One text for all blocking steps: the calls to other targets are named once, every other reason appears once."""
    targets = list(dict.fromkeys(b['target'] for b in blocking if 'target' in b))
    parts = []
    for b in blocking:
        text = b['reason']
        if 'target' in b:
            text = 'the call(s) name target(s) %s; %s' % (', '.join(repr(t) for t in targets), text)
        if text not in parts:
            parts.append(text)
    return '; '.join(parts)


def declare(case, applicability=None, grant_ids=None):
    """Declaration record of one executable plan scenario for the protected destination."""
    wiki_case = case['wiki_case_id']
    blocking = [b for i, s in enumerate(case['steps']) if (b := classify_step(i, s, grant_ids))]
    record = dict(scenario=case['id'], case=wiki_case, configuration=OCS_PROFILE, scenario_sha256=scenario_digest(case),
                  scenario_inputs=case.get('outcome_inputs'), steps=len(case['steps']),
                  executes=sum(1 for s in case['steps'] if s['action'] == 'execute'))
    if blocking:
        items = []
        for b in blocking:
            for it in b['interface_items']:
                if it not in items:
                    items.append(it)
        first = blocking[0]
        record.update(status=STATUS_NE, run_anyway=False, reason_code=first['code'],
                      reason=merged_reason(blocking),
                      interface_items=items, blocking_steps=[dict(step=b['step'], action=b['action'], code=b['code']) for b in blocking],
                      citations=_citations(items, case, ['76', '79-draft', 'PR-1']))
        return record
    sentence = applicability_sentence(wiki_case, applicability)
    if wiki_case == 'TC-D13-003':
        record.update(status=STATUS_NC, run_anyway=True, reason_code='NC-AMENDMENT-39',
                      reason='all steps can be applied, but the hierarchy levels of the scenario are named only in issuer_claims, which the '
                             'destination records as a digest and never reads, and OCS does not claim a nested budget hierarchy (amendment 39); '
                             'the scenario is run and its observation is retained apart from the scored results',
                      interface_items=['DEST-CLAIMS-DIGEST', 'DEST-BUDGET'],
                      citations=_citations(['DEST-CLAIMS-DIGEST', 'DEST-BUDGET'], case, ['39', '74', '76', '79-draft'], sentence=sentence))
        return record
    if carries_unread_content(case):
        if sentence:
            record.update(status=STATUS_NC, run_anyway=True, reason_code='NC-CASE-SENTENCE',
                          reason='all steps can be applied, but the question of the scenario is carried in issuer_claims or in payload content, '
                                 'which the destination records and never reads, and the not-claimed sentence of the case (cited) states what '
                                 'OCS does not claim; the scenario is run and its observation is retained apart from the scored results',
                          interface_items=['DEST-CLAIMS-DIGEST', 'DEST-PAYLOAD-OPAQUE'],
                          citations=_citations(['DEST-CLAIMS-DIGEST', 'DEST-PAYLOAD-OPAQUE'], case, ['74', '76', '79-draft'], sentence=sentence))
            return record
        record.update(status=STATUS_ASKED, run_anyway=False, reason_code='ASK-VOID-NC',
                      reason='the question is carried in a field the destination does not read, but no not-claimed sentence is published for the '
                             'case, so a declaration of not claimed would be void and the scenario is asked',
                      interface_items=['DEST-CLAIMS-DIGEST', 'DEST-PAYLOAD-OPAQUE'], citations=_citations(['DEST-CLAIMS-DIGEST'], case, ['79-draft']))
        return record
    record.update(status=STATUS_ASKED, run_anyway=False, reason_code='ASK',
                  reason='every step can be applied through the eight request fields and the destination controls, and no field carries content '
                         'that the destination does not read',
                  interface_items=['DEST-EXEC-ARGS'], citations=_citations(['DEST-EXEC-ARGS'], case, []))
    return record


def _citations(items, case, amendment_keys, sentence=None):
    out = []
    for it in items:
        out.append(dict(kind='interface', item=it, source=INTERFACE[it]['file'], marker=INTERFACE[it]['marker']))
    out.append(dict(kind='case_text', source='comparators/wiki/plans/wiki-subset-plan.json', scenario=case['id'],
                    sentence=case.get('outcome_inputs'),
                    page='scenarios/ai-security-wiki/pages (case %s)' % case['wiki_case_id']))
    if sentence:
        out.append(dict(kind='not_claimed_sentence', source=APPLICABILITY_FILE, applicability_version=APPLICABILITY_VERSION,
                        catalog_commit=APPLICABILITY_CATALOG_COMMIT, case=case['wiki_case_id'], sentence=sentence))
    for key in amendment_keys:
        out.append(dict(kind='amendment' if key not in ('PR-1',) else 'rule', ref=key, text=AMENDMENTS[key]))
    return out


# ----------------------------------------------------------------------------------------------------------------------
# 4. The adapter
# ----------------------------------------------------------------------------------------------------------------------
def build_adapter_class():
    """Subclass of the registered Cognous adapter for the Wiki world. Needs the pinned trees (SCN_HUB_DIR)."""
    from comparators.wiki.harness import _base
    adapters = _base.pinned_adapters()
    from comparators.wiki.apps import wiki_config as W

    class OcsWikiDestination(adapters.Cognous):
        """The protected destination with the grants of the declared Wiki world provisioned as the registered fixture provisions its
        grant: one hard-pinned target and policy, the lifetime and the effect count of the world's grant record, the fixture principal.
        Steps are applied only where the destination interface can express them; any other step raises (never a silent no-op)."""
        profile_id = OCS_PROFILE

        def __init__(self, root, opa, mutation=None):
            if mutation is not None:
                raise ValueError('the destination column has no control-removal families')
            super().__init__(root, opa, mutation)
            world = W.initial_state()['grants']
            default = world['grant']
            assert default['max_effects'] == 1 and default['expires_at'] == 200  # the grant the registered fixture provisions
            self.world_grants = {'grant'}
            for gid in sorted(world):
                if gid == 'grant':
                    continue
                rec = world[gid]
                self.control('provision', id=gid, scope='tenant', generation=7, principal=FIXTURE_PRINCIPAL, policy=PINNED_POLICY,
                             target=PINNED_TARGET, credential_version='v1', dependency_version='d1', modes={},
                             max_effects=rec['max_effects'], expires_at=rec['expires_at'])
                self.world_grants.add(gid)

        def request(self, changes=None, fault=None):
            if fault not in KNOWN_FAULTS:
                raise ValueError('unknown fault: ' + str(fault))
            extra = sorted(set(changes or {}) - set(REQUEST_FIELDS))
            if extra:
                raise ValueError('request field(s) outside the eight of the execute operation: ' + ', '.join(extra))
            return super().request(changes, fault)

        def __getattr__(self, name):
            if name.startswith('_') or ':' not in name:
                raise AttributeError(name)
            verb, *args = name.split(':')
            if verb == 'revoke_grant' and len(args) == 1:
                grant = args[0]
                if grant not in self.__dict__.get('world_grants', ()):
                    raise KeyError('grant not in the declared world: ' + grant)
                return lambda: self.control('revoke', grant=grant)
            raise AttributeError('control verb has no counterpart at the protected destination: ' + verb)

    return OcsWikiDestination


# ----------------------------------------------------------------------------------------------------------------------
# 5. Checks of a declarations file against the plan file and the cited sources
# ----------------------------------------------------------------------------------------------------------------------
def check_declarations(plan, decl, applicability=None, hub_dir=None, require_sources=True):
    """Errors (a list of text) of a declarations file against the plan file: coverage, scenario digests, agreement with the rules, citations."""
    errors = []
    applicability = applicability or load_applicability()
    if decl.get('schema') != 'cognous.ocs-column-declarations/1' or decl.get('configuration') != OCS_PROFILE:
        errors.append('declarations file: wrong schema or configuration')
    records = decl.get('records', [])
    ids = [r['scenario'] for r in records]
    if len(ids) != len(set(ids)):
        errors.append('declarations file: a scenario is declared twice')
    cases = {c['id']: c for c in plan['cases']}
    for sid in cases:
        if sid not in ids:
            errors.append('%s: executable scenario of the plan has no declaration (generate the declarations again and review them)' % sid)
    for sid in ids:
        if sid not in cases:
            errors.append('%s: declared but not an executable scenario of the plan' % sid)
    sentences = {row['id']: row.get('not_claimed') for row in applicability['cases']}
    for r in records:
        case = cases.get(r['scenario'])
        if case is None:
            continue
        if r['scenario_sha256'] != scenario_digest(case):
            errors.append('%s: the scenario changed after it was declared' % r['scenario'])
            continue
        if r != declare(case, applicability):
            errors.append('%s: the record differs from the declaration that the rules produce' % r['scenario'])
        status = r['status']
        if status not in (STATUS_ASKED, STATUS_NE, STATUS_NC):
            errors.append('%s: unknown status %r' % (r['scenario'], status))
        if r.get('run_anyway') != (status == STATUS_NC):
            errors.append('%s: run_anyway must be true exactly for not claimed' % r['scenario'])
        kinds = [c['kind'] for c in r['citations']]
        for c in r['citations']:
            if c['kind'] == 'interface' and c['item'] not in INTERFACE:
                errors.append('%s: cites an interface item that does not exist: %s' % (r['scenario'], c['item']))
        if status == STATUS_NE:
            if 'interface' not in kinds or 'case_text' not in kinds:
                errors.append('%s: not expressible needs an interface item and the sentence of the case' % r['scenario'])
            if not r.get('blocking_steps'):
                errors.append('%s: not expressible without a blocking step' % r['scenario'])
        if status == STATUS_NC:
            cited_ok = False
            for c in r['citations']:
                if c['kind'] == 'not_claimed_sentence' and c['sentence'] and c['sentence'] == sentences.get(c['case']):
                    cited_ok = True
                if c['kind'] == 'amendment' and c['ref'] == '39' and r['case'] == 'TC-D13-003':
                    cited_ok = True
            if not cited_ok:
                errors.append('%s: not claimed without a published sentence or amendment 39 (a declaration without a citation is void)' % r['scenario'])
            if r.get('blocking_steps'):
                errors.append('%s: not claimed with a step that cannot be applied' % r['scenario'])
        if status == STATUS_ASKED and r.get('blocking_steps'):
            errors.append('%s: asked with a step that cannot be applied' % r['scenario'])
        entry = (case.get('per_configuration') or {}).get(OCS_PROFILE)
        if isinstance(entry, str) and entry.upper().startswith(STATUS_NC) and status != STATUS_NC:
            errors.append('%s: the plan file says not claimed for the destination, the declaration says %s' % (r['scenario'], status))
    if require_sources:
        try:
            for item_id, item in INTERFACE.items():
                path, text = interface_item_source(item_id, hub_dir)
                if item['marker'] not in text:
                    errors.append('interface item %s: the marker text is not in %s' % (item_id, path.name))
            hub_file = Path(hub_dir or os.environ['SCN_HUB_DIR']) / HUB_FILE
            if hashlib.sha256(hub_file.read_bytes()).hexdigest() != HUB_FILE_SHA256:
                errors.append('the hub file differs from the digest named in the declarations')
        except KeyError:
            errors.append('SCN_HUB_DIR is not set: the cited hub source cannot be checked')
        except OSError as exc:
            errors.append('cited source not readable: %s' % exc)
    return errors
