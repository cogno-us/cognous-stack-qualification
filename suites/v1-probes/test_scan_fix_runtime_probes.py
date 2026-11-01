"""Runtime probes for the profile-composition and amount-exactness hardening of the final pin round (qualification first).

The atomic route and the effective-grant profile must never share one database (both creation orders), and an amount the
runtime cannot compare exactly must be refused at the envelope rather than admitted and compared in binary64. They are red at
runtime 11de097c by design and green at the final pin (62a5cc15). Run against PROBE_RUNTIME_DIR.
"""
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from conftest import pin_dir

NOW = datetime(2026, 10, 9, 18, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def _pin():
    pin_dir("PROBE_RUNTIME_DIR")


def test_probe_atomic_route_refuses_a_database_that_holds_an_effective_grant_profile(tmp_path):
    from engine.effective_grant import EffectiveGrantDestination
    from engine.local_authority_effect import AtomicAuthorityEffectDestination
    EffectiveGrantDestination(tmp_path)
    with pytest.raises(PermissionError):
        AtomicAuthorityEffectDestination(tmp_path, clock=lambda: NOW)


def test_probe_effective_grant_profile_refuses_a_database_that_holds_the_atomic_route(tmp_path):
    from engine.effective_grant import EffectiveGrantDestination
    from engine.local_authority_effect import AtomicAuthorityEffectDestination
    AtomicAuthorityEffectDestination(tmp_path, clock=lambda: NOW)
    with pytest.raises(PermissionError):
        EffectiveGrantDestination(tmp_path)


@pytest.mark.parametrize("amount", [2 ** 53 + 1, 10 ** 30, True])
def test_probe_an_amount_that_cannot_be_compared_exactly_is_refused(amount):
    from test_runtime_probes import op_and_policy, snap
    op, _ = op_and_policy()
    with pytest.raises(ValueError):
        snap(replace(op, amount=amount))


def test_probe_amount_comparison_is_exact_not_binary64():
    from engine.safe_executor import exact_amount_equal
    assert exact_amount_equal(50, 50.0)
    assert not exact_amount_equal(2 ** 53 + 1, float(2 ** 53))
    assert not exact_amount_equal(1000.0000000000001, 1000.0)


def test_probe_an_effective_grant_id_cannot_be_rebound_to_another_principal(tmp_path):
    from engine.effective_grant import EffectiveGrantDestination
    dest = EffectiveGrantDestination(tmp_path)
    dest.set_effective_grant(principal="urn:cognous:principal:one", grant_id="urn:cognous:grant:g", revision="1", permissions=["p"])
    with pytest.raises(PermissionError):
        dest.set_effective_grant(principal="urn:cognous:principal:two", grant_id="urn:cognous:grant:g", revision="2", permissions=["p"])
