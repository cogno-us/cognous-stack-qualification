"""The protected-destination column: step rules, declarations, citations and the adapter's mechanics."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from comparators.runner import ocs_column as O

REPO = Path(__file__).resolve().parents[3]


def case(sid, steps, wiki_case='TC-X-000', **kw):
    return dict(id=sid, wiki_case_id=wiki_case, steps=steps, outcome_inputs='inputs of ' + sid, expected_statuses=['accepted'], **kw)


def ex(target='sink', **extra):
    args = dict(grant='grant-agent', effect='e1', payload='synthetic', target=target)
    args.update(extra)
    return dict(action='execute', args=args)


# ---------------------------------------------------------------- interface items and sources
def test_every_marker_is_in_its_source_file():
    for item_id, item in O.INTERFACE.items():
        path, text = O.interface_item_source(item_id)
        assert item['marker'] in text, (item_id, path)


def test_the_hub_file_is_the_one_named_in_the_declarations():
    import hashlib
    assert hashlib.sha256((Path(os.environ['SCN_HUB_DIR']) / O.HUB_FILE).read_bytes()).hexdigest() == O.HUB_FILE_SHA256


def test_the_request_fields_are_the_eight_of_the_execute_operation():
    path, text = O.interface_item_source('DEST-EXEC-ARGS')
    assert "'" + ' '.join(O.REQUEST_FIELDS) + "'" in text


def test_every_control_of_the_comparator_interface_is_classified():
    """No control verb or zero-argument control of the comparator applications is left without a statement about the destination."""
    decl = json.loads((REPO / 'comparators/wiki/interface/declared-interface-opa-app.json').read_text())
    controls = decl['zero_argument_controls']
    zero = set(controls['base']) | set(controls['engine'])
    verbs = {v.split(':')[0] for v in controls['verbs (grammar verb:arg:arg through __getattr__)']}
    classified = set(O.EXPRESSIBLE_ZERO_ARG) | set(O.NOT_EXPRESSIBLE_CONTROLS) | set(O.EXPRESSIBLE_VERBS)
    assert (zero | verbs) <= classified, sorted((zero | verbs) - classified)
    assert not set(O.EXPRESSIBLE_ZERO_ARG) & set(O.NOT_EXPRESSIBLE_CONTROLS)


def test_every_not_expressible_control_cites_existing_interface_items():
    for verb, (code, reason, items) in O.NOT_EXPRESSIBLE_CONTROLS.items():
        assert code.startswith('NE-') and reason and items
        assert all(i in O.INTERFACE for i in items), verb


# ---------------------------------------------------------------- step rules
GRANTS = {'grant', 'grant-agent', 'grant-support'}


def test_expressible_steps():
    for step in (ex(), dict(action='clock', now=300), dict(action='reopen'), dict(action='revoke'), dict(action='break_audit'),
                 dict(action='revoke_grant:grant-support'), dict(action='capture', args={})):
        assert O.classify_step(0, step, GRANTS) is None, step


def test_a_call_to_another_target_has_no_counterpart():
    b = O.classify_step(3, ex('read_file'), GRANTS)
    assert b['code'] == 'NE-TOOL-SET' and b['step'] == 3 and b['target'] == 'read_file'
    assert 'DEST-TARGET-PIN' in b['interface_items']
    assert O.classify_step(0, ex(''), GRANTS)['code'] == 'NE-TOOL-SET'


def test_a_field_outside_the_eight_and_an_unknown_fault_have_no_counterpart():
    assert O.classify_step(0, ex(tenant='t1'), GRANTS)['code'] == 'NE-FIELD'
    step = ex()
    step['fault'] = 'unknown_fault'
    assert O.classify_step(0, step, GRANTS)['code'] == 'NE-FAULT'
    step['fault'] = 'stale_verifier'
    assert O.classify_step(0, step, GRANTS) is None


def test_controls_without_a_counterpart_are_blocked_with_their_own_code():
    for verb in O.NOT_EXPRESSIBLE_CONTROLS:
        action = verb if verb in ('opa_down', 'opa_up', 'fail_open', 'fail_closed') else verb + ':a:b'
        b = O.classify_step(0, dict(action=action), GRANTS)
        assert b and b['code'] == O.NOT_EXPRESSIBLE_CONTROLS[verb][0], verb


def test_revoke_grant_needs_a_grant_of_the_declared_world_and_an_unknown_control_is_blocked():
    assert O.classify_step(0, dict(action='revoke_grant:missing'), GRANTS)['code'] == 'NE-GRANT'
    assert O.classify_step(0, dict(action='no_such_control:x'), GRANTS)['code'] == 'NE-CONTROL'
    assert O.classify_step(0, dict(action='no_such_zero'), GRANTS)['code'] == 'NE-CONTROL'


# ---------------------------------------------------------------- declarations
def test_a_scenario_with_a_blocked_step_is_not_expressible_whatever_else_it_holds():
    r = O.declare(case('S1', [dict(action='stop:support'), ex()], 'TC-D13-003'), grant_ids=GRANTS)
    assert r['status'] == O.STATUS_NE and r['run_anyway'] is False
    assert r['blocking_steps'][0]['action'] == 'stop:support'
    kinds = {c['kind'] for c in r['citations']}
    assert {'interface', 'case_text', 'amendment', 'rule'} <= kinds


def test_the_calls_to_other_targets_are_named_once_in_the_reason():
    r = O.declare(case('S1', [ex('a_tool'), ex('b_tool'), ex('a_tool')]), grant_ids=GRANTS)
    assert r['reason'].count('allow-list') == 1 and "'a_tool'" in r['reason'] and "'b_tool'" in r['reason']


def test_budget_hierarchy_case_is_not_claimed_by_amendment_39_and_is_run():
    r = O.declare(case('S1', [ex(issuer_claims={'hierarchy': {'org': 'org-1'}})], 'TC-D13-003'), grant_ids=GRANTS)
    assert r['status'] == O.STATUS_NC and r['run_anyway'] is True and r['reason_code'] == 'NC-AMENDMENT-39'
    assert any(c['kind'] == 'amendment' and c['ref'] == '39' for c in r['citations'])


def test_claims_with_a_published_sentence_are_not_claimed_and_without_one_the_scenario_is_asked():
    app = {'cases': [{'id': 'TC-A-1', 'not_claimed': 'a sentence that was published before the plan'}, {'id': 'TC-A-2', 'not_claimed': None}]}
    steps = [ex(issuer_claims={'user': 'u'})]
    with_sentence = O.declare(case('S1', steps, 'TC-A-1'), app, GRANTS)
    assert with_sentence['status'] == O.STATUS_NC and with_sentence['run_anyway']
    assert any(c['kind'] == 'not_claimed_sentence' and c['sentence'] == 'a sentence that was published before the plan' for c in with_sentence['citations'])
    void = O.declare(case('S2', steps, 'TC-A-2'), app, GRANTS)
    assert void['status'] == O.STATUS_ASKED and void['reason_code'] == 'ASK-VOID-NC' and not void['run_anyway']


def test_payload_content_counts_as_content_the_destination_does_not_read():
    app = {'cases': [{'id': 'TC-A-1', 'not_claimed': 'sentence'}]}
    assert O.declare(case('S1', [ex(payload={'k': 'v'})], 'TC-A-1'), app, GRANTS)['status'] == O.STATUS_NC
    assert O.declare(case('S2', [ex()], 'TC-A-1'), app, GRANTS)['status'] == O.STATUS_ASKED


def test_a_plain_call_sequence_with_the_expressible_controls_is_asked():
    r = O.declare(case('S1', [ex(), dict(action='revoke_grant:grant-agent'), dict(action='clock', now=161), ex()]), grant_ids=GRANTS)
    assert r['status'] == O.STATUS_ASKED and r['reason_code'] == 'ASK'


def test_a_declaration_does_not_depend_on_the_expected_outcome(plan):
    app = O.load_applicability()
    for c in plan['cases']:
        flipped = copy.deepcopy(c)
        flipped['expected_statuses'] = ['denied' if s == 'accepted' else 'accepted' for s in c['expected_statuses']]
        flipped['expected_effects'] = c['expected_effects'] + 1
        flipped['expected_payload'] = 'other'
        assert O.declare(c, app) == O.declare(flipped, app), c['id']


def test_the_scenario_digest_follows_the_steps_and_the_id_only():
    c = case('S1', [ex()])
    d = O.scenario_digest(c)
    assert O.scenario_digest(dict(c, expected_statuses=['denied'])) == d
    assert O.scenario_digest(case('S1', [ex(), ex()])) != d
    assert O.scenario_digest(case('S2', [ex()])) != d


# ---------------------------------------------------------------- the committed declarations
def test_the_committed_declarations_are_current_and_complete(plan, decl):
    assert O.check_declarations(plan, decl) == []
    assert [r['scenario'] for r in decl['records']] == [c['id'] for c in plan['cases']]
    c = decl['counts']
    assert c['ASKED'] + c['NOT-EXPRESSIBLE'] + c['NOT-CLAIMED'] == len(plan['cases']) == c['executable_scenarios']
    for case_id, row in c['per_case'].items():
        assert row['ASKED'] + row['NOT-EXPRESSIBLE'] + row['NOT-CLAIMED'] <= row['of']


def test_the_declarations_file_can_be_regenerated_without_change():
    r = subprocess.run([sys.executable, '-I', str(REPO / 'comparators/runner/declare_ocs_column.py'), '--check'], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_every_not_claimed_record_cites_a_published_sentence_or_amendment_39(decl):
    app = {row['id']: row.get('not_claimed') for row in O.load_applicability()['cases']}
    for r in decl['records']:
        if r['status'] != O.STATUS_NC:
            continue
        assert r['run_anyway'] is True
        sentences = [c for c in r['citations'] if c['kind'] == 'not_claimed_sentence']
        a39 = [c for c in r['citations'] if c['kind'] == 'amendment' and c['ref'] == '39']
        assert (sentences and sentences[0]['sentence'] == app[r['case']]) or (a39 and r['case'] == 'TC-D13-003'), r['scenario']
        assert not r.get('blocking_steps')


def test_every_not_expressible_record_names_a_blocking_step_an_interface_item_and_the_case_sentence(decl):
    for r in decl['records']:
        if r['status'] != O.STATUS_NE:
            continue
        assert r['blocking_steps'] and r['interface_items'] and r['scenario_inputs']
        assert all(i in decl['interface_items'] for i in r['interface_items'])
        assert any(c['kind'] == 'case_text' and c['sentence'] == r['scenario_inputs'] for c in r['citations'])
        assert any(c['kind'] == 'amendment' and c['ref'] == '76' for c in r['citations'])


def test_the_asked_records_have_nothing_that_cannot_be_applied(decl):
    for r in decl['records']:
        if r['status'] == O.STATUS_ASKED:
            assert not r.get('blocking_steps') and r['run_anyway'] is False


def test_the_amendment_numbered_79_is_cited_as_the_draft_rule_and_not_as_the_registered_text(decl):
    text = decl['amendments_and_rules_cited']['79-draft']
    assert 'not yet been appended' in text and 'not the amendment that carries that number' in text


# ---------------------------------------------------------------- tampering is caught
def test_a_stale_missing_or_uncited_declaration_is_reported(plan, decl):
    def errors(d):
        return O.check_declarations(plan, d, require_sources=False)
    d = copy.deepcopy(decl)
    d['records'].pop(0)
    assert any('no declaration' in e for e in errors(d))
    d = copy.deepcopy(decl)
    d['records'][0]['scenario_sha256'] = '0' * 64
    assert any('changed after it was declared' in e for e in errors(d))
    d = copy.deepcopy(decl)
    nc = next(r for r in d['records'] if r['status'] == O.STATUS_NC)
    nc['citations'] = [c for c in nc['citations'] if c['kind'] not in ('not_claimed_sentence', 'amendment')]
    assert errors(d)
    d = copy.deepcopy(decl)
    asked = next(r for r in d['records'] if r['status'] == O.STATUS_ASKED)
    asked['status'] = O.STATUS_NE
    assert errors(d)
    d = copy.deepcopy(decl)
    d['records'].append(dict(d['records'][0]))
    assert any('twice' in e for e in errors(d))


def test_a_plan_that_gains_a_scenario_needs_new_declarations(plan, decl):
    bigger = copy.deepcopy(plan)
    extra = copy.deepcopy(bigger['cases'][0])
    extra['id'] = 'TC-NEW-000-S1'
    bigger['cases'].append(extra)
    assert any('TC-NEW-000-S1' in e and 'no declaration' in e for e in O.check_declarations(bigger, decl, require_sources=False))


# ---------------------------------------------------------------- the adapter (mechanics only)
@pytest.fixture(scope='module')
def adapter_class():
    return O.build_adapter_class()


def test_the_adapter_provisions_the_grants_of_the_declared_world_like_the_registered_fixture(adapter_class, tmp_path):
    from comparators.wiki.apps import wiki_config as W
    a = adapter_class(tmp_path / 'a', '/unused', None)
    assert a.world_grants == set(W.initial_state()['grants'])
    events = a.snapshot()['events']
    assert len(events) == 3 + (len(a.world_grants) - 1)  # fence, destination grants, the registered grant, one per other grant
    assert all(e['status'] == 'accepted' and e['command_authenticated'] for e in events)


def test_the_adapter_applies_a_call_to_a_provisioned_grant(adapter_class, tmp_path):
    a = adapter_class(tmp_path / 'a', '/unused', None)
    out = a.apply(a.request(dict(grant='grant-support', effect='mechanics-1')))
    assert out['status'] == 'accepted'
    assert [e['id'] for e in a.snapshot()['effects']] == ['mechanics-1']


def test_the_adapter_never_ignores_a_step_it_cannot_apply(adapter_class, tmp_path):
    a = adapter_class(tmp_path / 'a', '/unused', None)
    with pytest.raises(KeyError):
        getattr(a, 'revoke_grant:no-such-grant')()
    for verb in ('stop:support', 'allow_tool:agent:read_file', 'approve:effect:approver-1', 'unknown:x'):
        with pytest.raises(AttributeError):
            getattr(a, verb)
    with pytest.raises(AttributeError):
        a.opa_down
    with pytest.raises(ValueError):
        a.request(None, 'no-such-fault')
    with pytest.raises(ValueError):
        a.request(dict(tenant='t1'))
    with pytest.raises(ValueError):
        adapter_class(tmp_path / 'b', '/unused', 'some-family')


def test_revoke_grant_closes_only_the_named_grant(adapter_class, tmp_path):
    a = adapter_class(tmp_path / 'a', '/unused', None)
    getattr(a, 'revoke_grant:grant-support')()
    assert a.apply(a.request(dict(grant='grant-support', effect='m1')))['status'] == 'denied'
    assert a.apply(a.request(dict(grant='grant-finance', effect='m2')))['status'] == 'accepted'
