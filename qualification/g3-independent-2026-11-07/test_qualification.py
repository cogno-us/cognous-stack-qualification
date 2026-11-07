"""The five frozen G3 qualification cases; no additional cases are permitted."""
from harness import case_q1, case_q2, case_q3, case_q4, case_q5


def test_q1_source_integrity():
    assert case_q1()["oracle_satisfied"]


def test_q2_effect_integrity():
    assert case_q2()["oracle_satisfied"]


def test_q3_authority_refusal():
    assert case_q3()["oracle_satisfied"]


def test_q4_concurrency_and_disposal():
    assert case_q4()["oracle_satisfied"]


def test_q5_failure_unknown():
    assert case_q5()["oracle_satisfied"]
