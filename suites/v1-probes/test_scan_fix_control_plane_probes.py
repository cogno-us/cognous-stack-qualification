"""Control plane probes for the evidence-check hardening of the final pin round (qualification first).

Each probe states one property the control plane must keep after the external scan review, without using any new
API where an old one can express it: a writer must never produce a file the strict readers refuse, a refused write
must leave the existing record readable, and a redacted export must not carry a re-derivable fingerprint. They are
red at control plane 3cd17ead by design and green at the final pin (6093aca7). Run against PROBE_CONTROL_PLANE_DIR.
"""
from pathlib import Path

import pytest

from conftest import pin_dir

BAD = [
    pytest.param("lone\ud800surrogate", id="lone-surrogate"),
    pytest.param(float("nan"), id="nan"),
    pytest.param(float("inf"), id="infinity"),
]


@pytest.fixture(autouse=True)
def _pin():
    pin_dir("PROBE_CONTROL_PLANE_DIR")


def _recorder(task="Probe run", payload=None):
    from agent_control_plane.records import RunRecorder
    recorder = RunRecorder()
    recorder.start_run(task=task, actor="a", environment="test", allowed_tools=["crm_read"], blocked_tools=[],
                       policy_version="v1")
    kwargs = {"payload": payload} if payload else {}
    action = recorder.propose_action(tool_name="crm_read", action_type="read", target="customer:1", **kwargs)
    recorder.evaluate_action(action)
    recorder.complete_run("done")
    return recorder


@pytest.mark.parametrize("bad", BAD)
def test_probe_record_store_is_never_made_unreadable_by_a_write(tmp_path, bad):
    """A write of text or numbers the strict reader refuses is itself refused: the store stays readable afterwards."""
    from agent_control_plane.bounded import BoundedRecordStore
    path = tmp_path / "store" / "records.json"
    store = BoundedRecordStore(path, "run-1")
    with store._transaction():
        document = store._read_document()
        document["decisions"] = [{"note": bad}]
        try:
            store._write(document)
        except ValueError:
            pass
    reopened = BoundedRecordStore(path, "run-1")
    with reopened._transaction():
        assert reopened._read_document()["run_id"] == "run-1"


def test_probe_file_adapter_refused_save_leaves_the_existing_record_intact(tmp_path):
    from agent_control_plane.persistence import FileSystemPersistenceAdapter
    record = _recorder().to_run_record()
    adapter = FileSystemPersistenceAdapter(tmp_path)
    path = Path(adapter.save_run_record(record))
    before = path.read_bytes()
    bad = record.model_copy(update={"task": "lone\ud800surrogate"})
    try:
        adapter.save_run_record(bad)
    except (ValueError, FileExistsError):
        pass
    assert path.read_bytes() == before


def test_probe_export_json_writes_only_what_the_strict_readers_accept(tmp_path):
    out = tmp_path / "run.json"
    _recorder(payload={"amount": float("inf"), "n": float("nan")}).export_json(out)
    text = out.read_bytes()
    assert b"Infinity" not in text and b"NaN" not in text


def test_probe_redacted_export_does_not_keep_a_rederivable_fingerprint():
    from agent_control_plane.redaction import RedactionConfig, redact_run_record
    record = _recorder().to_run_record()
    assert record.decisions[0].deterministic_fingerprint
    redacted = redact_run_record(record, RedactionConfig(redact_targets=True))
    assert all(d.deterministic_fingerprint == "" for d in redacted.decisions)
    assert all(t.deterministic_fingerprint == "" for t in redacted.policy_traces)


def test_probe_legacy_recorder_refuses_a_different_proposal_under_a_recorded_action_id():
    from agent_control_plane.records import RunRecorder
    recorder = RunRecorder()
    recorder.start_run(task="t", actor="a", environment="test", allowed_tools=["crm_read", "email_send"], blocked_tools=[],
                       policy_version="v1")
    action = recorder.propose_action(tool_name="email_send", action_type="external_send", target="prod-db")
    other = action.model_copy(update={"tool_name": "crm_read", "action_type": "read", "target": "readme"})
    with pytest.raises(ValueError):
        recorder.evaluate_action(other)
    assert recorder.to_run_record().decisions == []
