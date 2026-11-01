"""Control plane probes (PROBE2_CONTROL_PLANE_DIR): what the recorder hands out is a copy, not the stored record.

A decision, a blocked action, a reliance record or a policy trace returned to the caller must not be the object the run record
is built from: changing the returned object must leave the run record as it was. The time grammar sites of this component are
in test_time_grammar_probes.py.
"""
import pytest

from conftest import checkout


@pytest.fixture(autouse=True)
def _pin():
    checkout("PROBE2_CONTROL_PLANE_DIR")


def recorder():
    from agent_control_plane.records import RunRecorder
    rec = RunRecorder()
    rec.start_run(task="Probe run", actor="agent-1", environment="test", allowed_tools=["crm_read"],
                  blocked_tools=["email_send"], policy_version="v1")
    return rec


def snapshot(rec):
    return rec.to_run_record().model_dump(mode="json")


def allowed(rec):
    action = rec.propose_action(tool_name="crm_read", action_type="read", target="customer:1")
    return action, rec.evaluate_action(action)


def blocked(rec):
    action = rec.propose_action(tool_name="email_send", action_type="external_send", target="a@example.invalid")
    return action, rec.evaluate_action(action)


# ---------------------------------------------------------------------------------------------------------- controls
def test_control_the_run_record_snapshot_is_independent_of_the_recorder():
    rec = recorder()
    allowed(rec)
    record = rec.to_run_record()
    before = snapshot(rec)
    record.decisions[0].reason = "changed after the snapshot"
    record.actions[0].target = "customer:2"
    assert snapshot(rec) == before


def test_control_the_proposal_returned_by_propose_action_is_a_copy():
    rec = recorder()
    action = rec.propose_action(tool_name="crm_read", action_type="read", target="customer:1")
    before = snapshot(rec)
    action.target = "customer:2"
    assert snapshot(rec) == before


def test_control_returned_objects_carry_the_recorded_content():
    rec = recorder()
    _, (decision, none) = allowed(rec)
    _, (denied, blocked_action) = blocked(rec)
    record = rec.to_run_record()
    assert none is None and denied.result == "block" and blocked_action is not None
    assert [d.model_dump() for d in record.decisions] == [decision.model_dump(), denied.model_dump()]
    assert [b.model_dump() for b in record.blocked_actions] == [blocked_action.model_dump()]


# ---------------------------------------------------------------------------------------------------------- probes
def test_probe_changing_a_returned_decision_does_not_change_the_run_record():
    rec = recorder()
    _, (decision, _) = allowed(rec)
    before = snapshot(rec)
    decision.result = "block"
    decision.reason = "changed after the decision"
    assert snapshot(rec) == before


def test_probe_changing_a_returned_blocked_action_does_not_change_the_run_record():
    rec = recorder()
    _, (_, blocked_action) = blocked(rec)
    before = snapshot(rec)
    blocked_action.reason = "changed after the block"
    assert snapshot(rec) == before


def test_probe_changing_a_returned_reliance_record_does_not_change_the_run_record():
    rec = recorder()
    action, _ = allowed(rec)
    reliance = rec.record_reliance(source_name="crm_read", source_type="tool", scope="customer fields",
                                   referenced_action_id=action.action_id)
    before = snapshot(rec)
    reliance.scope = "changed after the record"
    assert snapshot(rec) == before


def test_probe_changing_a_returned_policy_trace_does_not_change_the_run_record():
    rec = recorder()
    allowed(rec)
    before = snapshot(rec)
    rec.get_policy_traces()[0].final_result = "block"
    assert snapshot(rec) == before
