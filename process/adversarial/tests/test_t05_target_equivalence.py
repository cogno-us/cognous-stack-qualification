"""T05. Target equivalence and prefix semantics (idea A02, tier 2).

SPDX-License-Identifier: Apache-2.0

Attacker: a proposer choosing the target string.
Evaluators: the control plane's exact-membership target check (manifest allowed_targets and grant permission targets, in
bounded.py) and the runtime LocalExecutionPolicy, which matches allowed_target_prefixes. At the attacked revisions it used
str.startswith; at runtime 11de097c the default target_match is "segment" (a prefix matches only on a whole path segment, control
and format characters and dot-segments are refused), with "exact" available and "legacy-prefix" an explicit opt-in.
Invariant (plan): both evaluators agree on every near-equivalent spelling of the granted target; in the composed route a
near-equivalent target never produces an effect.

Does not prove: resolver-level aliasing (no V1 referent); targets outside the synthetic account namespace; the runtime policy is
a local restriction, not the authority boundary, so a disagreement matters only where the runtime is driven without the control
plane (see T01 for direct calls).
"""
from __future__ import annotations

import unicodedata

import pytest

from _adv import effect_ids, flow
from conftest import observe

T = "T05"
DNP = "synthetic account namespace only; runtime policy is a local restriction, not the authority boundary"
GRANTED = "urn:cognous:synthetic-account:customer-001"
VARIANTS = {
    "prefix_extension": GRANTED + "0",
    "prefix_extension_path": GRANTED + "/sub",
    "upper_case": GRANTED.upper(),
    "trailing_space": GRANTED + " ",
    "leading_space": " " + GRANTED,
    "nfd_text": unicodedata.normalize("NFD", GRANTED.replace("customer", "custómer")),
    "nfc_text": unicodedata.normalize("NFC", GRANTED.replace("customer", "custómer")),
    "zero_width": GRANTED[:-1] + "​" + GRANTED[-1],
    "separator": GRANTED.replace(":customer", "::customer"),
}


def _cp_decides(fl, target):
    p = fl.p.model_copy(deep=True)
    p.target = target
    return fl.f.decide(p, now=fl.NOW)


def _rt_allows(prefixes, target, fl, mode=None):
    import dataclasses
    from engine.safe_executor import LocalExecutionPolicy
    extra = {} if mode is None else {"target_match": mode}
    pol = dataclasses.replace(fl.policy, allowed_target_prefixes=prefixes, **extra)
    assert isinstance(pol, LocalExecutionPolicy)
    from _adv import snapshot
    p = fl.p.model_copy(deep=True)
    p.target = target
    snap = snapshot(fl.envelope(fl.d1, p))
    try:
        pol.check(snap.operation)
        return True
    except PermissionError:
        return False


def _table(fl, prefixes, mode=None):
    return {name: {"control_plane": _cp_decides(fl, t).result == "authorized", "runtime": _rt_allows(prefixes, t, fl, mode)}
            for name, t in VARIANTS.items()}


def test_positive_control_exact_target_allowed_by_both(cprt, tmp_path, monkeypatch):
    fl = flow(tmp_path, monkeypatch)
    assert fl.p.target == GRANTED
    assert _cp_decides(fl, GRANTED).result == "authorized"
    assert _rt_allows(("urn:cognous:synthetic-account:",), GRANTED, fl)
    assert _rt_allows((GRANTED,), GRANTED, fl)


def test_composed_route_never_commits_a_near_equivalent_target(cprt, tmp_path, monkeypatch):
    fl = flow(tmp_path, monkeypatch)
    for name, target in VARIANTS.items():
        d = _cp_decides(fl, target)
        assert d.result == "hold", (name, d.reasons)
    # the original decision executed with a substituted target is refused at effect time
    p = fl.p.model_copy(deep=True)
    p.target = VARIANTS["prefix_extension"]
    r = fl.run(fl.d1, p)
    assert r.status != "executed"
    assert effect_ids(fl.dest.path) == []
    observe(T, "composed route: near-equivalent targets", "prevented", does_not_prove=DNP, detail=sorted(VARIANTS))


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="evaluator differential recorded at the attacked revisions; see the batch README")
@pytest.mark.parametrize("config", ["namespace_prefix", "exact_target_as_prefix"])
def test_evaluators_agree_on_every_variant(cprt, tmp_path, monkeypatch, config):
    fl = flow(tmp_path, monkeypatch)
    prefixes = ("urn:cognous:synthetic-account:",) if config == "namespace_prefix" else (GRANTED,)
    table = _table(fl, prefixes)
    disagree = sorted(k for k, v in table.items() if v["control_plane"] != v["runtime"])
    observe(T, f"evaluator differential ({config})", "reproduced failure" if disagree else "prevented", does_not_prove=DNP,
            detail={"disagreements": disagree})
    assert disagree == []


def test_exact_mode_agrees_with_the_control_plane_on_every_variant(cprt, tmp_path, monkeypatch):
    """target_match="exact" with the granted target as the only entry: the runtime admits the granted target and refuses every
    near-equivalent spelling, the same set the control plane does not authorise (the invariant holds in this configuration)."""
    fl = flow(tmp_path, monkeypatch)
    assert _rt_allows((GRANTED,), GRANTED, fl, "exact")
    table = _table(fl, (GRANTED,), "exact")
    disagree = sorted(k for k, v in table.items() if v["control_plane"] != v["runtime"])
    observe(T, "evaluator agreement (exact mode)", "reproduced failure" if disagree else "prevented", does_not_prove=DNP,
            detail={"disagreements": disagree})
    assert disagree == []
