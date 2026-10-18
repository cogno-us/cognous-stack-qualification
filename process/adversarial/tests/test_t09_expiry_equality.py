"""T09. Expiry equality and offset across evaluators (idea B13, tier 3).

SPDX-License-Identifier: Apache-2.0

Attacker: a proposer (or record producer) choosing timestamps and UTC-offset spellings near an expiry instant T.
Evaluators: the control plane decision clock (grant validity window, bounded.py), the runtime atomic destination's trusted clock
(claim and grant validity, local_authority_effect.py), and the ODES recipient validator's consumption-window check.
Invariant: at T-1us, T and T+1us, with the same instant spelled 'Z', '+00:00' and '+01:00', every evaluator gives the same
accept/expire answer for the same instant.

Does not prove: real clock skew between hosts; the three evaluators check different objects (a grant window, a claim window, a
record's consumption window) that the plan treats as one 'expires at T' semantics, so a difference shows inconsistent boundary
semantics, not that one object is accepted by another evaluator. The ODES check is called through its module-level helper
(_evaluate_authority_and_freshness), not a full recipient package.
"""
from __future__ import annotations

from datetime import timedelta, timezone

import pytest

from _adv import atomic, effect_ids, flow
from conftest import observe, require

T = "T09"
DNP = "different objects per evaluator (grant, claim, record window); no real clock skew"
OFFSETS = ("Z", "+00:00", "+01:00")
DELTAS = (-1, 0, 1)


def _spell(instant, offset):
    if offset == "+01:00":
        return instant.astimezone(timezone(timedelta(hours=1))).isoformat()
    base = instant.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    return base + ("Z" if offset == "Z" else "+00:00")


def _cp_table(fl, mp, T0):
    out = {}
    g = fl.r.contexts[fl.PROFILE]["grant"]
    for off in OFFSETS:
        g["expires_at"] = _spell(T0, off)
        fl.tra.bind_approval(fl.r, fl.cfg)
        for d in DELTAS:
            t = T0 + timedelta(microseconds=d)
            mp.setattr(fl.cp, "_now", lambda t=t: t)
            out[(off, d)] = fl.f.decide(fl.p, now=t).result == "authorized"
    return out


def _atomic_table(tmp_path, mp, T0):
    out = {}
    for off in OFFSETS:
        for d in DELTAS:
            work = tmp_path / f"atomic-{off.replace(':', '')}-{d}"
            fl = flow(work, mp)
            clock = {"now": fl.NOW}
            dest, ex = atomic(fl, work, clock=lambda: clock["now"])
            claim = ex.provision_claim(proposal=fl.p, decision=fl.d1, now=fl.NOW, expires_at=_spell(T0, off))
            clock["now"] = T0 + timedelta(microseconds=d)
            r = ex.execute(envelope=fl.envelope(fl.d1), claim_id=claim.claim_id)
            out[(off, d)] = r.status == "executed" and bool(effect_ids(dest.path))
    return out


def _odes_table(T0):
    from odes.recipient_validator import _evaluate_authority_and_freshness
    out = {}
    for off in OFFSETS:
        for d in DELTAS:
            now = (T0 + timedelta(microseconds=d)).isoformat()
            res = _evaluate_authority_and_freshness({"consumption_conditions": {"expires_at": _spell(T0, off)}}, {}, now, {})
            out[(off, d)] = not any("expired" in r for r in res["reasons"])
    return out


def test_positive_control_mid_validity_accepted_by_all(cprt, tmp_path, monkeypatch):
    import sys
    sys.path.insert(0, str(require("odes")["odes"] / "src"))
    fl = flow(tmp_path / "cp", monkeypatch)
    T0 = fl.NOW + timedelta(seconds=30)
    assert fl.f.decide(fl.p, now=fl.NOW).result == "authorized"
    from odes.recipient_validator import _evaluate_authority_and_freshness
    res = _evaluate_authority_and_freshness({"consumption_conditions": {"expires_at": _spell(T0, "Z")}}, {}, fl.NOW.isoformat(), {})
    assert not any("expired" in r for r in res["reasons"])


def test_control_plane_and_atomic_destination_agree_at_the_boundary(cprt, tmp_path, monkeypatch):
    fl = flow(tmp_path / "cp", monkeypatch)
    T0 = fl.NOW + timedelta(seconds=30)
    cp = _cp_table(fl, monkeypatch, T0)
    at = _atomic_table(tmp_path, monkeypatch, T0)
    expected = {(off, d): d < 0 for off in OFFSETS for d in DELTAS}  # half-open: valid iff now < expires_at
    observe(T, "control plane vs atomic destination at T", "prevented" if cp == at == expected else "reproduced failure",
            does_not_prove=DNP, detail={"control_plane": {str(k): v for k, v in cp.items()},
                                        "atomic": {str(k): v for k, v in at.items()}})
    assert cp == expected and at == expected


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="boundary differential recorded at the attacked revisions; see the batch README")
def test_odes_recipient_window_agrees_at_the_boundary(cprt, tmp_path, monkeypatch):
    import sys
    sys.path.insert(0, str(require("odes")["odes"] / "src"))
    fl = flow(tmp_path / "cp", monkeypatch)
    T0 = fl.NOW + timedelta(seconds=30)
    od = _odes_table(T0)
    expected = {(off, d): d < 0 for off in OFFSETS for d in DELTAS}
    diff = sorted(str(k) for k in expected if od[k] != expected[k])
    observe(T, "ODES recipient consumption window vs control plane at T", "reproduced failure" if diff else "prevented",
            does_not_prove=DNP, detail={"differs_at": diff})
    assert od == expected
