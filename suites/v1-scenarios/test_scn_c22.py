"""Catalog scenario C22 - Equal conditions comparison (V1 stack vs a conventional control; executed against the frozen F5b reference).

SPDX-License-Identifier: Apache-2.0

Stimulus (catalog): freeze one request, policy, permissions, attack and initial state; run conventional controls and the governed
stack with independent resets. Required observation: report correctness, prohibited and duplicate effects, false blocks, latency,
recovery and human effort per arm; recovery is a separate trajectory.

OWNER DECISION D5 applies: the HARD GATES are zero unauthorized effects and zero excess duplicate effects (asserted on the V1 arm,
in every run). False blocks, latency and review burden are MEASURED AND REPORTED ONLY: no pass/fail threshold is applied to them,
and nothing here is a superiority claim.

THE CONVENTIONAL CONTROL (DEFINED HERE BEFORE ANY RUN; the catalog does not define it sufficiently, so this is the simplest honest
conventional control, recorded as an assumption in the report). ``ConventionalControl`` is a plain allow-list + approval check:
  * facts it holds (the same facts the V1 arm's policy/claims hold): allowed actors, principals, adapters, actions, a target prefix,
    allowed units, a maximum amount, a maximum number of effects in the store, and an approval registry
    {approval_id -> action_id, status (active/revoked), expires_at}.
  * check, at call time, against LIVE state: actor, principal, adapter, action and unit are allow-listed; the target starts with the
    prefix; amount <= maximum; effects == 1; the request's approval exists, is active, is unexpired and was granted for the SAME action;
    the number of effect rows already stored is below the maximum.
  * act: if every check passed, INSERT one row into a plain table (autoincrement key, no UNIQUE constraint) and return success.
  * deliberately NOT present (this is what "without the V1 binding/ledger" means): no operation/claim binding (the approval is not
    bound to the exact target, amount or payload, only to the action), no commitment over the request, no idempotency key or
    deduplication, no attempt/ledger records, and the check and the write are NOT one transaction (check-then-act).
  * client behaviour is part of the frozen conditions and identical for both arms: on an UNKNOWN outcome (lost acknowledgement) the
    client retries the same request once.
  * recovery (separate trajectory): the operator queries the store for a row carrying the request's approval id and resubmits only
    if none exists (one manual query); the V1 arm uses the reference's exact-original ``reconcile_claim``.
The conventional control is NOT a model of any particular product, of OPA/LangGraph-style applications (the hub battery's adapters
add idempotency, transactions and audit) or of what a well-engineered conventional system can do; results characterise exactly this
baseline against exactly this V1 route (route B, atomic-claim profile) and nothing more.

EQUAL CONDITIONS. One frozen plan (``PLAN``, digest recorded) lists the requests, approvals, caps, attack/fault steps and the oracle's
authorized-effect sets; both arms receive the identical plan, each case on its own freshly reset store per arm (independent resets),
and one independent read-only observer (same SQL over each arm's store) counts effects. Oracle per case: an observed effect row is
UNAUTHORIZED if its (target, amount, unit, payload) is not in the case's authorized set or if authorized rows exceed the case's
declared maximum; EXCESS DUPLICATE = rows of an authorized key beyond its allowed count; FALSE BLOCK = authorized effects that were
expected but did not occur. Every case runs twice per arm and the two normalised observations are compared (D3); latency is retained
separately and never compared.
"""
from __future__ import annotations

import dataclasses
import json
import sqlite3
import statistics
from datetime import timedelta
from pathlib import Path

import pytest

import _c_2c_helpers as C
import _d02_d05_d09_helpers as H
from _d02_d05_d09_helpers import no_network, pinned_reference  # noqa: F401  (fixtures)

pytestmark = pytest.mark.usefixtures('pinned_reference')

PREFIX = 'urn:cognous:synthetic-account:'
OTHER_ACTOR = 'urn:cognous:identity:not-allowlisted'
OTHER_ADAPTER = 'urn:cognous:adapter:not-allowlisted'
OUTSIDE_TARGET = 'urn:elsewhere:account:1'


def canon(payload):
    return json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def base_request(n, amount=50.0):
    """The approved request n (route-B fixture values); both arms derive every request from this one definition."""
    h = H.reference().atomic
    op = h.operation(effect_no=n)
    return {'n': n, 'actor': op.actor, 'principal': op.principal, 'action_id': op.action_id, 'adapter_id': op.adapter_id, 'target': op.target,
            'amount': float(amount), 'unit': op.unit, 'effects': 1, 'payload': dict(op.payload), 'approval_id': f'approval-{n}'}


def apply_overrides(req, overrides):
    out = {**req, 'payload': dict(req['payload'])}
    for k, v in overrides.items():
        if k == 'payload_reason':
            out['payload']['reason'] = v
        else:
            out[k] = v
    return out


def key_of(req):
    return (req['target'], float(req['amount']), req['unit'], canon(req['payload']))


# ----------------------------------------------------------------------------------------------
# the frozen plan
# ----------------------------------------------------------------------------------------------

def step(n, overrides=None, **extra):
    return {'op': 'submit', 'n': n, 'overrides': overrides or {}, **extra}


PLAN = [
    # id, kind, approved {n: amount}, cap, steps, authorized request numbers, expected effect count
    {'id': 'L1_permitted_exact', 'kind': 'legit', 'approved': {1: 50.0}, 'cap': 1, 'steps': [step(1)], 'authorized': [1], 'expected': 1},
    {'id': 'L2_permitted_two_distinct_within_budget', 'kind': 'legit', 'approved': {1: 50.0, 2: 50.0}, 'cap': 2, 'steps': [step(1), step(2)], 'authorized': [1, 2], 'expected': 2},
    {'id': 'L3_permitted_larger_amount_with_its_own_approval', 'kind': 'legit', 'approved': {3: 75.0}, 'cap': 1, 'steps': [step(3)], 'authorized': [3], 'expected': 1},
    {'id': 'L4_permitted_after_store_restart', 'kind': 'legit', 'approved': {1: 50.0, 2: 50.0}, 'cap': 2, 'steps': [step(1), {'op': 'restart'}, step(2)], 'authorized': [1, 2], 'expected': 2},
    {'id': 'A01_changed_target_within_prefix', 'kind': 'attack', 'approved': {1: 50.0}, 'cap': 1, 'steps': [step(1, {'target': PREFIX + 'customer-999'})], 'authorized': [], 'expected': 0},
    {'id': 'A02_changed_amount_within_cap', 'kind': 'attack', 'approved': {1: 50.0}, 'cap': 1, 'steps': [step(1, {'amount': 900.0})], 'authorized': [], 'expected': 0},
    {'id': 'A03_changed_payload', 'kind': 'attack', 'approved': {1: 50.0}, 'cap': 1, 'steps': [step(1, {'payload_reason': 'substituted'})], 'authorized': [], 'expected': 0},
    {'id': 'A04_actor_not_allowlisted', 'kind': 'attack', 'approved': {1: 50.0}, 'cap': 1, 'steps': [step(1, {'actor': OTHER_ACTOR})], 'authorized': [], 'expected': 0},
    {'id': 'A05_adapter_not_allowlisted', 'kind': 'attack', 'approved': {1: 50.0}, 'cap': 1, 'steps': [step(1, {'adapter_id': OTHER_ADAPTER})], 'authorized': [], 'expected': 0},
    {'id': 'A06_target_outside_prefix', 'kind': 'attack', 'approved': {1: 50.0}, 'cap': 1, 'steps': [step(1, {'target': OUTSIDE_TARGET})], 'authorized': [], 'expected': 0},
    {'id': 'A07_amount_over_policy_cap', 'kind': 'attack', 'approved': {1: 50.0}, 'cap': 1, 'steps': [step(1, {'amount': 1500.0})], 'authorized': [], 'expected': 0},
    {'id': 'A08_effects_two', 'kind': 'attack', 'approved': {1: 50.0}, 'cap': 1, 'steps': [step(1, {'effects': 2})], 'authorized': [], 'expected': 0},
    {'id': 'A09_approval_revoked_before_call', 'kind': 'attack', 'approved': {1: 50.0}, 'cap': 1, 'steps': [{'op': 'revoke_approval'}, step(1)], 'authorized': [], 'expected': 0},
    {'id': 'A10_approval_expired', 'kind': 'attack', 'approved': {1: 50.0}, 'cap': 1, 'steps': [{'op': 'advance_clock', 'hours': 2}, step(1)], 'authorized': [], 'expected': 0},
    {'id': 'A11_approval_revoked_between_check_and_write', 'kind': 'attack', 'approved': {1: 50.0}, 'cap': 1, 'steps': [step(1, between='revoke_approval')], 'authorized': [], 'expected': 0},
    {'id': 'A12_lost_ack_then_client_retry', 'kind': 'attack', 'approved': {1: 50.0}, 'cap': 2, 'steps': [step(1, lose_ack=True, retry_on_unknown=True)], 'authorized': [1], 'expected': 1},
    {'id': 'A13_duplicate_redelivery', 'kind': 'attack', 'approved': {1: 50.0}, 'cap': 2, 'steps': [step(1), step(1)], 'authorized': [1], 'expected': 1},
    {'id': 'A14_resubmission_after_store_restart', 'kind': 'attack', 'approved': {1: 50.0}, 'cap': 2, 'steps': [step(1), {'op': 'restart'}, step(1)], 'authorized': [1], 'expected': 1},
    {'id': 'A15_budget_exhaustion_sequential', 'kind': 'attack', 'approved': {1: 50.0, 2: 50.0, 3: 50.0}, 'cap': 2, 'steps': [step(1), step(2), step(3)], 'authorized': [1, 2, 3], 'expected': 2},
    {'id': 'A16_last_unit_taken_between_check_and_write', 'kind': 'attack', 'approved': {1: 50.0, 2: 50.0}, 'cap': 1, 'steps': [step(1, between='submit_other:2')], 'authorized': [1, 2], 'expected': 1},
]
PLAN_DIGEST = H.digest(PLAN)


# ----------------------------------------------------------------------------------------------
# arms
# ----------------------------------------------------------------------------------------------

class ConventionalControl:
    """The conventional control exactly as defined in the module docstring (plain allow-list/approval check, check-then-act)."""
    name = 'conventional'

    def __init__(self, work, case, clock):
        self.path = Path(work) / 'conventional.sqlite3'
        self.clock = clock
        self.cap = case['cap']
        base = base_request(1)
        self.cfg = {'actors': {base['actor']}, 'principals': {base['principal']}, 'adapters': {base['adapter_id']}, 'actions': {base['action_id']},
                    'prefix': PREFIX, 'units': {'USD'}, 'max_amount': 1000.0}
        self.restart()
        with self.conn:
            self.conn.executescript('CREATE TABLE IF NOT EXISTS approvals(approval_id TEXT PRIMARY KEY, action_id TEXT, status TEXT, expires_at REAL);'
                                    'CREATE TABLE IF NOT EXISTS effects(row_id INTEGER PRIMARY KEY AUTOINCREMENT, approval_id TEXT, actor TEXT, target TEXT, amount REAL, unit TEXT, payload_json TEXT);')
            for n in case['approved']:
                b = base_request(n)
                self.conn.execute('INSERT INTO approvals VALUES(?,?,?,?)', (b['approval_id'], b['action_id'], 'active', (self.clock() + timedelta(hours=1)).timestamp()))

    def restart(self):
        self.conn = sqlite3.connect(self.path, timeout=10, isolation_level=None)

    def check(self, req):
        c = self.cfg
        if req['actor'] not in c['actors'] or req['principal'] not in c['principals']:
            return 'actor_or_principal_not_allowlisted'
        if req['adapter_id'] not in c['adapters'] or req['action_id'] not in c['actions']:
            return 'adapter_or_action_not_allowlisted'
        if not req['target'].startswith(c['prefix']):
            return 'target_outside_prefix'
        if req['unit'] not in c['units']:
            return 'unit_not_allowed'
        if req['amount'] > c['max_amount']:
            return 'amount_over_maximum'
        if req['effects'] != 1:
            return 'effects_not_one'
        row = self.conn.execute('SELECT action_id,status,expires_at FROM approvals WHERE approval_id=?', (req['approval_id'],)).fetchone()
        if row is None or row[1] != 'active' or row[2] <= self.clock().timestamp() or row[0] != req['action_id']:
            return 'approval_missing_revoked_expired_or_other_action'
        if self.conn.execute('SELECT COUNT(*) FROM effects').fetchone()[0] >= self.cap:
            return 'effect_budget_exhausted'
        return None

    def submit(self, req, *, between=None, lose_ack=False):
        reason = self.check(req)
        if reason:
            return {'status': 'denied', 'error': reason}
        if between:
            between()
        self.conn.execute('INSERT INTO effects(approval_id,actor,target,amount,unit,payload_json) VALUES(?,?,?,?,?,?)',
                          (req['approval_id'], req['actor'], req['target'], req['amount'], req['unit'], canon(req['payload'])))
        if lose_ack:
            return {'status': 'unknown', 'error': 'acknowledgement lost after write'}
        return {'status': 'executed', 'error': None}

    def revoke_approval(self, n=1):
        self.conn.execute('UPDATE approvals SET status=? WHERE approval_id=?', ('revoked', base_request(n)['approval_id']))

    def recover(self, req):
        """Operator recovery: one manual query by approval id; resubmit only if no row exists."""
        found = self.conn.execute('SELECT COUNT(*) FROM effects WHERE approval_id=?', (req['approval_id'],)).fetchone()[0]
        return {'manual_queries': 1, 'found_existing_effect': bool(found), 'resubmitted': False if found else True,
                'result': None if found else self.submit(req)}

    @property
    def effects_path(self):
        return self.path


class V1Arm:
    """The governed stack: route B (atomic claim profile) - one trusted-host-issued claim per approved request."""
    name = 'v1'

    def __init__(self, work, case, clock):
        h = H.reference().atomic
        self.h = h
        self.clock = clock
        self.work = Path(work)
        self.cls = H.hooked_atomic_class()
        self.dest = self.cls(self.work, clock=clock)
        self.dest.trace = []
        self.claims = {}
        self.base_env = {}
        for n, amount in case['approved'].items():
            env = h.envelope(effect_no=n)
            env = dataclasses.replace(env, operation=dataclasses.replace(env.operation, amount=float(amount)))
            claim = h.make_claim(env, claim_id=f'claim-{n}', budget_id='budget-main', max_effects=case['cap'])
            self.dest.provision_claim(claim)
            self.claims[n], self.base_env[n] = claim, env
        first = next(iter(self.base_env.values()))
        self.policy = dataclasses.replace(h.policy(first.operation), max_effects=max(1, case['cap']))
        self._executor()

    def _executor(self):
        from engine.local_authority_effect import AtomicLocalControlPlaneExecutor
        self.executor = AtomicLocalControlPlaneExecutor(workflow=object(), destination=self.dest, policy=self.policy)

    def restart(self):
        self.dest = self.cls(self.work, clock=self.clock)
        self.dest.trace = []
        self._executor()

    def envelope(self, req):
        env = self.base_env[req['n']]
        op = dataclasses.replace(env.operation, actor=req['actor'], principal=req['principal'], adapter_id=req['adapter_id'], target=req['target'], amount=req['amount'],
                                 unit=req['unit'], effects=req['effects'])
        if req['payload'] != env.operation.payload:
            from engine.safe_executor import commitment
            op = dataclasses.replace(op, payload=req['payload'], payload_commitment=commitment(req['payload']))
        return dataclasses.replace(env, operation=op)

    def submit(self, req, *, between=None, lose_ack=False):
        env = self.envelope(req)
        self.dest.stage_hook = None
        if between:
            def hook(stage, between=between):
                if stage == 'before_begin':
                    self.dest.stage_hook = None   # the interleaved agent runs once, outside the hook
                    between()
            self.dest.stage_hook = hook
        try:
            res = self.executor.execute(envelope=env, claim_id=self.claims[req['n']].claim_id, simulate='lost_ack' if lose_ack else None)
            return {'status': res.status, 'error': res.error}
        except Exception as exc:
            return {'status': 'denied', 'error': f'{type(exc).__name__}: {exc}'}
        finally:
            self.dest.stage_hook = None

    def revoke_approval(self, n=1):
        self.dest.set_approval_status(self.h.APPROVAL, status='revoked')

    def recover(self, req):
        env = self.base_env[req['n']]
        rec = self.dest.reconcile_claim(self.claims[req['n']].claim_id, H.snapshot_env(env))
        return {'reconcile_calls': 1, 'status': rec['status'], 'retry_eligible': rec['retry_eligible'], 'resubmitted': False}

    @property
    def effects_path(self):
        return self.dest.path


def observe(path):
    """The independent observer: the same read-only SQL over each arm's store."""
    conn = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True, timeout=10)
    try:
        return [(r[0], float(r[1]), r[2], r[3]) for r in conn.execute('SELECT target,amount,unit,payload_json FROM effects ORDER BY rowid')]
    finally:
        conn.close()


def score(case, rows):
    authorized = {}
    for n in case['authorized']:
        authorized[key_of(base_request(n, case['approved'][n]))] = authorized.get(key_of(base_request(n, case['approved'][n])), 0) + 1
    cap = case['cap']
    seen = {}
    unauthorized = duplicates = 0
    valid_rows = 0
    for r in rows:
        if r not in authorized:
            unauthorized += 1
            continue
        seen[r] = seen.get(r, 0) + 1
        if seen[r] > authorized[r]:
            duplicates += 1
        else:
            valid_rows += 1
    unauthorized += max(0, valid_rows - cap)            # authorized rows beyond the declared maximum are prohibited
    valid_rows = min(valid_rows, cap)
    false_blocks = max(0, case['expected'] - valid_rows)
    return {'effects': len(rows), 'unauthorized_effects': unauthorized, 'excess_duplicate_effects': duplicates, 'false_blocks': false_blocks,
            'correct': unauthorized == 0 and duplicates == 0 and false_blocks == 0}


def run_arm(arm_cls, case, work, clock, watch):
    arm = arm_cls(work, case, clock)
    base = case['approved']
    results = []
    for st in case['steps']:
        if st['op'] == 'restart':
            arm.restart()
        elif st['op'] == 'revoke_approval':
            arm.revoke_approval()
        elif st['op'] == 'advance_clock':
            clock.value = clock.value + timedelta(hours=st['hours'])
        else:
            req = apply_overrides(base_request(st['n'], base[st['n']]), st['overrides'])
            between = None
            if st.get('between') == 'revoke_approval':
                between = arm.revoke_approval
            elif st.get('between', '').startswith('submit_other:'):
                other = apply_overrides(base_request(int(st['between'].split(':')[1]), base[int(st['between'].split(':')[1])]), {})
                between = lambda other=other: results.append({'interleaved': True, **watch.time(f'{arm.name}.submit', arm.submit, other)})
            out = watch.time(f'{arm.name}.submit', arm.submit, req, between=between, lose_ack=st.get('lose_ack', False))
            results.append(out)
            if out['status'] == 'unknown' and st.get('retry_on_unknown'):
                results.append({'retry': True, **watch.time(f'{arm.name}.submit', arm.submit, req)})   # frozen client behaviour: one retry
    rows = observe(arm.effects_path)
    denied = sum(1 for r in results if r['status'] in ('denied', 'unknown'))
    return arm, results, rows, denied


class Clock:
    def __init__(self, value):
        self.value = value

    def __call__(self):
        return self.value


def run_case_both_arms(case, work, watch):
    """Independent resets: each arm gets its own fresh directory and its own clock; identical frozen case."""
    h = H.reference().atomic
    out = {}
    for arm_cls in (V1Arm, ConventionalControl):
        d = Path(work) / arm_cls.name
        d.mkdir()
        clock = Clock(h.BASE)
        if arm_cls is ConventionalControl:
            pass
        _arm, results, rows, denied = run_arm(arm_cls, case, d, clock, watch)
        s = score(case, rows)
        out[arm_cls.name] = {'step_results': [{k: v for k, v in r.items()} for r in results], 'observed_rows': len(rows), **s, 'denied_or_unknown_responses': denied,
                             'approvals_required': len(case['approved']), 'claims_issued': len(case['approved']) if arm_cls is V1Arm else 0}
    return out


@pytest.fixture
def watch():
    return C.Stopwatch()


# ----------------------------------------------------------------------------------------------
# tests
# ----------------------------------------------------------------------------------------------

def test_scn_c22_frozen_plan_conventional_control_definition_and_independent_resets(request, record_property, tmp_path):
    """The plan is frozen (stable digest), the conventional control is the one defined in this module, and each arm starts from a
    fresh, independent, empty store for every case."""
    ref = H.reference()
    H.assert_pins_still_pristine()
    assert PLAN_DIGEST == H.digest(json.loads(json.dumps(PLAN))), 'the frozen plan must be plain data with a stable digest'
    assert len({c['id'] for c in PLAN}) == len(PLAN)

    def trial(work, mp, checks):
        h = ref.atomic
        paths = []
        for case in PLAN:
            for arm_cls in (V1Arm, ConventionalControl):
                d = Path(work) / case['id'] / arm_cls.name
                d.mkdir(parents=True)
                arm = arm_cls(d, case, Clock(h.BASE))
                checks.equal(observe(arm.effects_path), [], f'{case["id"]}/{arm_cls.name}: initial store holds no effect')
                paths.append(str(arm.effects_path.relative_to(work)))
        checks.equal(len(paths), len(set(paths)), 'every (case, arm) store is a distinct path (independent resets)')
        checks.equal(base_request(1)['payload'] and H.snapshot_env(H.reference().atomic.envelope(effect_no=1)).operation.payload_json == canon(base_request(1)['payload']), True,
                     'the oracle\'s canonical payload equals the V1 destination\'s stored payload encoding')
        return {'plan_digest': PLAN_DIGEST, 'cases': [c['id'] for c in PLAN], 'unauthorized_effects': 0, 'excess_duplicate_effects': 0}
    H.run_case(request, record_property, tmp_path, 'C22', trial)
    C.write_report(request, record_property, 'conventional_control_definition', {
        'scenario': 'C22', 'plan_digest': PLAN_DIGEST, 'plan': PLAN, 'conventional_control': (__doc__ or '').split('THE CONVENTIONAL CONTROL')[1].split('EQUAL CONDITIONS.')[0].strip(),
        'assumption': 'catalog does not define the conventional control; this is the simplest honest allow-list/approval check without binding or ledger'})


@pytest.mark.parametrize('case_id', ['L1_permitted_exact', 'L2_permitted_two_distinct_within_budget'])
def test_scn_c22_positive_control_both_arms_execute_the_permitted_request(request, record_property, tmp_path, watch, case_id):
    """Harness validity: BOTH arms must perform the permitted effect(s) exactly, or the comparison would be meaningless."""
    case = next(c for c in PLAN if c['id'] == case_id)

    def trial(work, mp, checks):
        out = run_case_both_arms(case, work, watch)
        for arm in ('v1', 'conventional'):
            checks.equal((out[arm]['effects'], out[arm]['false_blocks'], out[arm]['unauthorized_effects']), (case['expected'], 0, 0), f'{arm}: permitted effect(s) performed exactly')
        return {'case': case_id, 'arms': out, 'unauthorized_effects': out['v1']['unauthorized_effects'], 'excess_duplicate_effects': out['v1']['excess_duplicate_effects']}
    H.run_case(request, record_property, tmp_path, 'C22', trial)


@pytest.mark.parametrize('case_id', [c['id'] for c in PLAN])
def test_scn_c22_equal_conditions_case(request, record_property, tmp_path, watch, case_id):
    """One frozen case, both arms, independent resets. Hard gates are asserted on the V1 arm; every other number is reported only."""
    case = next(c for c in PLAN if c['id'] == case_id)
    latencies = []

    def trial(work, mp, checks):
        local_watch = C.Stopwatch()
        out = run_case_both_arms(case, work, local_watch)
        latencies.append(local_watch.summary())
        return {'case': case_id, 'kind': case['kind'], 'plan_digest': PLAN_DIGEST, 'arms': out,
                # hard gates (D5) are asserted on the V1 arm only; the conventional arm's counts are reported
                'unauthorized_effects': out['v1']['unauthorized_effects'], 'excess_duplicate_effects': out['v1']['excess_duplicate_effects']}
    payload = H.run_case(request, record_property, tmp_path, 'C22', trial)
    arms = payload['run1']['observed']['arms']
    C.write_report(request, record_property, 'measurements', {
        'scenario': 'C22', 'case': case_id, 'thresholds_applied': None,
        'per_arm': {a: {k: arms[a][k] for k in ('effects', 'unauthorized_effects', 'excess_duplicate_effects', 'false_blocks', 'correct', 'denied_or_unknown_responses', 'approvals_required', 'claims_issued')} for a in arms},
        'latency_ms_run1_and_run2': latencies, 'latency_note': 'wall time per submit on one host; not compared between runs, not a ranking, includes no human time'})


def test_scn_c22_summary_report_only_measurements(request, record_property, tmp_path):
    """Whole frozen plan twice per arm; per-arm totals and latency percentiles. REPORT ONLY: the sole assertions are the V1 hard gates,
    run-to-run determinism of the normalised outcomes, and that both arms ran the identical plan."""
    def once(work):
        watch = C.Stopwatch()
        rows = {}
        for case in PLAN:
            (Path(work) / case['id']).mkdir()
            rows[case['id']] = run_case_both_arms(case, Path(work) / case['id'], watch)
        samples = watch.samples
        return rows, samples

    runs = []
    for n in (1, 2):
        d = tmp_path / f'run-{n}'
        d.mkdir()
        runs.append(once(d))
    norm = [{cid: {a: {k: v for k, v in arm.items()} for a, arm in arms.items()} for cid, arms in r[0].items()} for r in runs]
    comparison = {'run1_digest': H.digest(norm[0]), 'run2_digest': H.digest(norm[1]), 'verdict': 'MATCH' if H.digest(norm[0]) == H.digest(norm[1]) else 'MISMATCH'}
    totals = {}
    for arm in ('v1', 'conventional'):
        rows = [norm[0][c['id']][arm] for c in PLAN]
        permitted = [norm[0][c['id']][arm] for c in PLAN if c['kind'] == 'legit']
        samples = [x for r in runs for k, v in r[1].items() if k.startswith(arm + '.') for x in v]
        samples.sort()

        def pick(q, s=samples):
            return round(s[min(len(s) - 1, int(q * len(s)))] * 1000, 3) if s else None
        totals[arm] = {
            'cases': len(rows), 'cases_correct': sum(1 for r in rows if r['correct']), 'unauthorized_effects': sum(r['unauthorized_effects'] for r in rows),
            'excess_duplicate_effects': sum(r['excess_duplicate_effects'] for r in rows), 'false_blocks_total': sum(r['false_blocks'] for r in rows),
            'false_blocks_on_permitted_cases': sum(r['false_blocks'] for r in permitted), 'permitted_cases': len(permitted),
            'denied_or_unknown_responses': sum(r['denied_or_unknown_responses'] for r in rows), 'approvals_required': sum(r['approvals_required'] for r in rows),
            'claims_issued': sum(r['claims_issued'] for r in rows),
            'latency_ms': {'n': len(samples), 'median': round(statistics.median(samples) * 1000, 3) if samples else None, 'p95': pick(0.95), 'max': round(samples[-1] * 1000, 3) if samples else None}}
    per_case = {c['id']: {a: {k: norm[0][c['id']][a][k] for k in ('effects', 'unauthorized_effects', 'excess_duplicate_effects', 'false_blocks', 'correct')} for a in ('v1', 'conventional')} for c in PLAN}
    C.write_report(request, record_property, 'summary', {
        'scenario': 'C22', 'plan_digest': PLAN_DIGEST, 'run_comparison': comparison, 'thresholds_applied': None, 'owner_decision': 'D5: false blocks, latency, review burden reported only',
        'totals_per_arm': totals, 'per_case': per_case,
        'human_effort': 'NOT MEASURED: these deterministic batteries involve no human participant; approvals_required, claims_issued and denied_or_unknown_responses are artifact counts, not effort',
        'conventional_control_scope': 'a plain allow-list/approval check without binding, ledger, idempotency or atomic check-and-write; not a model of any product',
        'latency_note': 'wall time per submit on one host (V1 includes SQLite transaction and claim validation); not an intrinsic speed comparison'})
    assert comparison['verdict'] == 'MATCH', comparison
    assert totals['v1']['unauthorized_effects'] == 0, f'HARD GATE: V1 unauthorized effects {totals["v1"]["unauthorized_effects"]}'
    assert totals['v1']['excess_duplicate_effects'] == 0, f'HARD GATE: V1 excess duplicate effects {totals["v1"]["excess_duplicate_effects"]}'


def test_scn_c22_recovery_is_a_separate_trajectory(request, record_property, tmp_path):
    """Recovery after a lost acknowledgement, run as its own trajectory on freshly reset stores (not mixed into the main metrics).
    V1: effect-free ``reconcile_claim``; conventional: the operator's one manual query. Hard gate on V1; the conventional arm is reported."""
    case = next(c for c in PLAN if c['id'] == 'A12_lost_ack_then_client_retry')

    def trial(work, mp, checks):
        h = H.reference().atomic
        out = {}
        for arm_cls in (V1Arm, ConventionalControl):
            d = Path(work) / arm_cls.name
            d.mkdir()
            clock = Clock(h.BASE)
            arm = arm_cls(d, case, clock)
            req = base_request(1, 50.0)
            first = arm.submit(req, lose_ack=True)              # trajectory 1: the interrupted effect (no client retry here)
            after_interrupt = observe(arm.effects_path)
            arm.restart()
            recovery = arm.recover(req)                          # trajectory 2: recovery under current authority
            after_recovery = observe(arm.effects_path)
            s = score({**case, 'steps': []}, after_recovery)
            out[arm_cls.name] = {'interrupted_outcome': first['status'], 'effects_after_interruption': len(after_interrupt), 'recovery': recovery,
                                 'effects_after_recovery': len(after_recovery), **{k: s[k] for k in ('unauthorized_effects', 'excess_duplicate_effects', 'false_blocks')}}
        for name in ('v1', 'conventional'):
            checks.equal(out[name]['interrupted_outcome'], 'unknown', f'{name}: the acknowledgement was lost')
            checks.equal(out[name]['effects_after_interruption'], 1, f'{name}: the effect is durable despite the lost acknowledgement')
        checks.equal(out['v1']['effects_after_recovery'], 1, 'V1 recovery leaves exactly one effect')
        checks.equal((out['v1']['recovery']['status'], out['v1']['recovery']['retry_eligible']), ('applied', False), 'V1 recovery reports applied and not retry-eligible')
        return {'arms': out, 'unauthorized_effects': out['v1']['unauthorized_effects'], 'excess_duplicate_effects': out['v1']['excess_duplicate_effects']}
    payload = H.run_case(request, record_property, tmp_path, 'C22', trial)
    C.write_report(request, record_property, 'recovery', {'scenario': 'C22', 'trajectory': 'recovery (separate from the main comparison)',
                                                          'per_arm': payload['run1']['observed']['arms'], 'thresholds_applied': None})
