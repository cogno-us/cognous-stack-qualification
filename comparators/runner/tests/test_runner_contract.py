"""The contract self-check runs clean on the plan file, and each of its checks can fail."""
import json

from comparators.runner import contract_check


def test_the_contract_self_check_passes(capsys):
    assert contract_check.main([]) == 0
    assert ' 0 problem(s)' in capsys.readouterr().out


def test_the_self_check_fails_on_declarations_that_do_not_cover_the_plan(tmp_path, capsys):
    decl = json.loads(contract_check.DECL.read_text())
    decl['records'] = decl['records'][1:]
    f = tmp_path / 'd.json'
    f.write_text(json.dumps(decl))
    assert contract_check.main(['--declarations', str(f)]) == 1
    assert 'FAIL' in capsys.readouterr().out


def test_the_predicted_verdict_of_a_stub_is_derived_from_the_case_alone():
    case = dict(steps=[dict(action='execute', args=dict(effect='e1'))], expected_statuses=['denied'], expected_effects=0,
                allowed_effect_ids=[], expected_payload='synthetic')
    assert contract_check.predicted(case, 'deny') is True and contract_check.predicted(case, 'accept') is False
    assert contract_check.predicted(case, 'echo') is True
