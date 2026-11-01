"""Probe harness for the evidence-check hardening round (probes first).

One env var per target checkout, set to the repository root of that checkout (read only: no probe writes inside it). A test
module whose env var is unset is not collected, so a missing checkout yields no result rather than a pass. Probes that
span two checkouts (the journal and lifecycle rules exist in both the reference validators and the independent verifier)
take one parameter per implementation and skip an implementation whose checkout is not given.

Every probe marked ``xfail(strict=True)`` states a property the target must hold and does not hold at the pinned head
named in the README; the mark is removed when the matching change lands (a strict xfail that starts passing fails the run,
which is the signal to remove it). Every unmarked probe is a valid control and passes at the pinned head.
"""
import os
import sys

import pytest

# module file -> env vars naming the checkouts it needs (all must be set for the module to be collected, except the
# modules listed in ANY_OF, which are collected when at least one is set)
MODULE_ENV = {
    "test_journal_rules_probes.py": ("PROBE2_VERIFIER_DIR", "PROBE2_ODES_DIR"),
    "test_verifier_probes.py": ("PROBE2_VERIFIER_DIR",),
    "test_odes_probes.py": ("PROBE2_ODES_DIR",),
    "test_time_grammar_probes.py": ("PROBE2_ODES_DIR", "PROBE2_REPLAY_DIR", "PROBE2_VERIFIER_DIR", "PROBE2_CONTROL_PLANE_DIR"),
    "test_replay_probes.py": ("PROBE2_REPLAY_DIR",),
    "test_control_plane_probes.py": ("PROBE2_CONTROL_PLANE_DIR",),
    "test_manifest_probes.py": ("PROBE2_MANIFEST_DIR",),
    "test_runtime_probes.py": ("PROBE2_RUNTIME_DIR", "PROBE2_CONTROL_PLANE_DIR"),
    "test_ergonomics_probes.py": ("PROBE2_ERGONOMICS_DIR",),
    "test_pack_probes.py": ("PROBE2_PACK_DIR",),
    "test_exchange_probes.py": ("PROBE2_EXCHANGE_DIR",),
}
ANY_OF = {"test_journal_rules_probes.py", "test_time_grammar_probes.py"}


def _wanted(module, names):
    present = [bool(os.environ.get(n)) for n in names]
    return any(present) if module in ANY_OF else all(present)


collect_ignore = [m for m, names in MODULE_ENV.items() if not _wanted(m, names)]

# Directories put on sys.path (source layouts first). The verifier, ODES validators and the runtime are used from their
# checkouts; contract validators are loaded by file path (see _support.py) because every contract names its file validate.py.
SYSPATH = {
    "PROBE2_VERIFIER_DIR": ("src",),
    "PROBE2_ODES_DIR": ("src",),
    "PROBE2_REPLAY_DIR": ("src",),
    "PROBE2_CONTROL_PLANE_DIR": ("src",),
    "PROBE2_MANIFEST_DIR": ("src",),
    "PROBE2_ERGONOMICS_DIR": ("src",),
    "PROBE2_PACK_DIR": ("src",),
    "PROBE2_RUNTIME_DIR": ("",),
    "PROBE2_EXCHANGE_DIR": ("",),
}
for _var, _subs in SYSPATH.items():
    _d = os.environ.get(_var)
    if _d:
        for _sub in reversed(_subs):
            _p = os.path.join(_d, _sub) if _sub else _d
            if os.path.isdir(_p) and _p not in sys.path:
                sys.path.insert(0, _p)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def checkout(var):
    d = os.environ.get(var)
    if not d:
        pytest.skip(f"{var} is not set")
    return d
