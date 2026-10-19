"""Shared helpers: implementation adapters, fixture loaders, expected-failure marks.

Standard library only. Nothing here changes a target checkout.
"""
import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from conftest import checkout

PENDING = "pending hardening"


def pending(*, raises=(AssertionError, pytest.fail.Exception), condition=True):
    """A strict expected failure: the probe states a property the pinned head does not yet hold.

    Only a failed assertion (or ``pytest.raises`` finding no exception) counts as the expected failure: an import error or any
    other exception in the probe is a real failure, so a renamed API cannot hide behind the mark."""
    return pytest.mark.xfail(condition, strict=True, raises=raises, reason=PENDING)


def known_limit(reason, *, raises=(AssertionError, pytest.fail.Exception), condition=True):
    """A strict expected failure that records a known limit of the component under test (see KNOWN_LIMITS.md): the probe
    states a property the pinned head does not hold, and ``reason`` names the limit in neutral words. Same strictness as
    ``pending``: only a failed assertion is the expected failure, and a probe that starts to pass fails the run."""
    return pytest.mark.xfail(condition, strict=True, raises=raises, reason=reason)


# ---------------------------------------------------------------------------- the two implementations of the rules
IMPLS = ("verifier", "odes")
IMPL_VAR = {"verifier": "PROBE2_VERIFIER_DIR", "odes": "PROBE2_ODES_DIR"}


def impl_params(*red, reason=None):
    """One parameter per implementation; those named in ``red`` are strict expected failures. ``reason`` (a string, or a
    mapping from implementation to string) records the known limit; without it the mark is the plain ``pending`` one."""
    def mark(impl):
        text = reason.get(impl) if isinstance(reason, dict) else reason
        return known_limit(text) if text else pending()
    return [pytest.param(i, id=i, marks=[mark(i)] if i in red else []) for i in IMPLS]


def root(var):
    return Path(checkout(var))


_CONTRACT_MODULES = {}


def odes_contract(name):
    """The reference validator module of one ODES contract, loaded by file path under a unique module name."""
    if name not in _CONTRACT_MODULES:
        path = root("PROBE2_ODES_DIR") / "contracts" / name / "validate.py"
        spec = importlib.util.spec_from_file_location("fix2_contract_" + name.replace("-", "_"), path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _CONTRACT_MODULES[name] = module
    return _CONTRACT_MODULES[name]


def odes_fixture(contract, name, kind="valid"):
    path = root("PROBE2_ODES_DIR") / "contracts" / contract / "fixtures" / kind / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))["document"]


def verifier_data(*parts):
    return root("PROBE2_VERIFIER_DIR") / "tests" / "data" / Path(*parts)


def verifier_fixture(kind, name, cls="valid"):
    return json.loads(verifier_data("odes-fixtures", kind, cls, f"{name}.json").read_text(encoding="utf-8"))["document"]


def real_run(name):
    return json.loads(verifier_data("real-runs", name, "bounded-run-record.json").read_text(encoding="utf-8"))


def refusal_codes(impl, doc, contract):
    """Stable codes with which ``impl`` refuses ``doc`` (empty: accepted). ``contract`` names the ODES contract."""
    if impl == "odes":
        return sorted({v.code for v in odes_contract(contract).validate(doc)})
    from cognous_verify import documents
    results = documents.verify_document(doc)
    assert not [r.check_id for r in results if r.error], "the verifier reported an internal error"
    return sorted({f.code for r in results if r.verdict == "refuted" for f in r.findings})


# ----------------------------------------------------------------------------------------- journal run record bases
def refusal_base(impl):
    """A run record whose decision was refused at effect time (one refusal row, no attempt)."""
    if impl == "odes":
        return copy.deepcopy(odes_fixture("control-plane-journal", "effect-time-refusal"))
    return real_run("journal-effect-time-refusal")


def applied_base(impl):
    """A run record whose decision was authorized and applied (attempts and observations present)."""
    if impl == "odes":
        return copy.deepcopy(odes_fixture("control-plane-journal", "normal-attempted-acknowledged-applied"))
    return real_run("journal-applied")


def closeout_base(impl):
    """A run record with a lost acknowledgement closed out by an accepted observation."""
    if impl == "odes":
        return copy.deepcopy(odes_fixture("control-plane-journal", "lost-ack-unknown-then-closeout"))
    return real_run("journal-lost-ack-closeout")


def effect_checks(doc):
    return [c for c in doc["resolution_checks"] if c["stage"] == "effect"]


def effect_events(doc):
    return [e for e in doc["check_events"] if e["stage"] == "effect"]
