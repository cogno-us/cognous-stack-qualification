"""Observer only (no assertion/behavior change): per test, counts Exchange _verify_refusal_profile_sources executions that ended by raising (refused source identity).
Uses sys.settrace with a local tracer on that single function; nothing is caught, altered or suppressed."""
import json, os, sys
_state = {"calls": 0, "raised": 0}
_out = os.environ["OBS_OUT"]
_rec = {}

def _local(frame, event, arg):
    if event == "exception":
        _state["raised"] += 1  # counts the exception event in this frame (propagating or caught inside)
    return _local

def _glob(frame, event, arg):
    if event == "call" and frame.f_code.co_name == "_verify_refusal_profile_sources":
        _state["calls"] += 1
        return _local
    return None

def pytest_runtest_call(item):
    _state["calls"] = 0; _state["raised"] = 0
    sys.settrace(_glob)

def pytest_runtest_teardown(item):
    sys.settrace(None)
    _rec[item.nodeid] = dict(_state)

def pytest_sessionfinish(session):
    json.dump(_rec, open(_out, "w"))
