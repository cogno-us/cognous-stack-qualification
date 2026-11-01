"""Authorization pin export (Registry r08-v2 Amendment 4 section 3.2). Synthetic fixtures; builder-authored, not independent qualification.

Every refusal test asserts the refusal itself (PermissionError, or a non-active result with no payload), never only the absence of success.
"""
import copy
import importlib.util
import inspect
import json
import sys
from pathlib import Path

import pytest

import agent_control_plane.authorization_pin_export as export
from agent_control_plane.authorization_pin_export import PAYLOAD_MEMBERS, PIN_EXPORT_PROFILE, assess_authorization_pin
from agent_control_plane.bounded import BoundedRecordStore, commitment
from agent_control_plane.policy_binding import PolicyBinding
from tests import v02_support as v02
from tests.test_bounded_authorization import NOW, PROFILE, TENANT  # noqa: F401  (NOW pinned by the autouse clock below)
from tests.test_bounded_authorization import _fixed_synthetic_clock  # noqa: F401  (autouse fixture)

FORMAT_PATH = Path(__import__("os").environ["Q6_FORMAT_MODULE_PATH"])


def flow(tmp_path, binding=None, **kw):
    binding = binding or v02.canonical_binding()
    p, r, f, d, cfg = v02.tenant_flow(tmp_path, binding, **kw)
    return p, r, f, d, cfg, binding


def active(f, p, d, binding, **kw):
    return assess_authorization_pin(f, p, d, now=NOW, host_policy_binding=binding, **kw)



def test_payload_passes_the_runtime_format_module_when_available(tmp_path):
    if not FORMAT_PATH.exists():
        pytest.skip("Runtime format module not present in this environment (INCONCLUSIVE, not a pass)")
    spec = importlib.util.spec_from_file_location("pin_format_for_test", FORMAT_PATH)
    fmt = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = fmt
    try:
        spec.loader.exec_module(fmt)
    finally:
        sys.modules.pop(spec.name, None)
    p, r, f, d, cfg, b = flow(tmp_path)
    assert fmt.payload_defect(active(f, p, d, b)["payload"]) is None
    assert tuple(fmt.PAYLOAD_MEMBERS) == PAYLOAD_MEMBERS
