"""T04. Every-field post-approval mutation completeness (ideas A01, A02, A04, A07, tier 2).

SPDX-License-Identifier: Apache-2.0

Attacker: a holder of the approved envelope (and, in the second matrix, of the proposal) between decision and effect.
Invariant: mutating any single member after approval either is refused with no destination row, or is LISTED below as unbound
with its reason. The member lists are generated from the models (runtime ExecutionOperation / ExecutionEnvelope dataclass
fields, control plane RuntimeProposal model fields), so a member added later forces a new case: it is neither refused nor
listed, and the test fails.

Does not prove: adapter-internal behaviour (T06); route C (governed exchange, not in the attacked set); nested payload keys
beyond one injected key; members whose mutation the model itself rejects before any executor runs are counted as refused.
"""
from __future__ import annotations

import dataclasses

import pytest

from _adv import atomic, effect_ids, flow
from conftest import observe

T = "T04"
DNP = "adapter internals (T06) and route C are not covered; one injected payload key per case"

UNBOUND = {
    "A": {"attempt_id": "caller-chosen attempt label by design; it names the attempt, not the effect"},
    "B": {
        "attempt_id": "caller-chosen attempt label by design",
        "proposal_commitment": "the atomic claim checks operation_commitment, which does not include proposal_commitment; "
                               "effect content (target, amount, unit, payload) is still the claimed one",
        "effective_max_effects": "the shared budget is taken from the claim, not the envelope; effect content unchanged",
    },
}
PROPOSAL_UNBOUND: dict[str, str] = {}


def _mutate(value, name):
    if name == "payload":
        return {**value, "x-injected": 1}
    if name == "requested_permissions":
        return type(value)(list(value) + ["refund.issue.high"])
    if isinstance(value, bool):
        return not value
    if isinstance(value, int):
        return value + 1
    if isinstance(value, float):
        return value + 1.0
    if value is None:
        return "tenant-x"
    if isinstance(value, dict):
        return {**value, "x-injected": 1}
    if isinstance(value, list):
        return value + ["x-injected"]
    return value + "-x"


def _envelope_members():
    from engine.safe_executor import ExecutionEnvelope, ExecutionOperation
    return ([("operation", f.name) for f in dataclasses.fields(ExecutionOperation)]
            + [("envelope", f.name) for f in dataclasses.fields(ExecutionEnvelope) if f.name not in ("operation", "version")])


def _mutated_envelope(env, where, name):
    if where == "envelope":
        return dataclasses.replace(env, **{name: (getattr(env, name) or "attempt") + "-x"})
    return dataclasses.replace(env, operation=dataclasses.replace(env.operation, **{name: _mutate(getattr(env.operation, name), name)}))


@pytest.mark.parametrize("route", ["A", "B"])
def test_envelope_member_mutation(cprt, tmp_path, monkeypatch, route):
    members = _envelope_members()
    assert len([m for m in members if m[0] == "operation"]) == 23, "ExecutionOperation member count changed: review this test"
    written, outcome = [], {}
    for where, name in members:
        work = tmp_path / f"{where}-{name}"
        fl = flow(work, monkeypatch)
        env = _mutated_envelope(fl.envelope(fl.d1), where, name)
        if route == "A":
            path = fl.dest.path
            call = lambda: fl.executor.execute(envelope=env, proposal=fl.p, decision=fl.d1, now=fl.NOW)  # noqa: E731
        else:
            dest, ex = atomic(fl, work)
            claim = ex.provision_claim(proposal=fl.p, decision=fl.d1, now=fl.NOW)
            path = dest.path
            call = lambda: ex.execute(envelope=env, claim_id=claim.claim_id)  # noqa: E731
        try:
            outcome[name] = call().status
        except (ValueError, TypeError, PermissionError) as exc:
            outcome[name] = "rejected:" + type(exc).__name__
        if effect_ids(path):
            written.append(name)
    assert sorted(written) == sorted(UNBOUND[route]), {"written": written, "listed": sorted(UNBOUND[route]), "outcome": outcome}
    observe(T, f"route {route}: single envelope member mutated after approval", "prevented", does_not_prove=DNP,
            detail={"refused": sorted(set(outcome) - set(written)), "unbound_listed": UNBOUND[route]})


def test_proposal_member_mutation_route_a(cprt, tmp_path, monkeypatch):
    """The attacker changes the proposal and rebuilds a consistent envelope (fresh proposal commitment); the decision is unchanged."""
    from agent_control_plane.bounded import RuntimeProposal, commitment
    written, outcome = [], {}
    for name in RuntimeProposal.model_fields:
        fl = flow(tmp_path / name, monkeypatch)
        p = fl.p.model_copy(deep=True)
        setattr(p, name, _mutate(getattr(p, name), name))
        if name == "payload":
            p.payload_commitment = commitment(p.payload)
        try:
            outcome[name] = fl.run(fl.d1, p).status
        except (ValueError, TypeError, PermissionError) as exc:
            outcome[name] = "rejected:" + type(exc).__name__
        if effect_ids(fl.dest.path):
            written.append(name)
    assert sorted(written) == sorted(PROPOSAL_UNBOUND), outcome
    assert "run_id" in outcome and "correlation_id" in outcome
    observe(T, "route A: single proposal member mutated, envelope rebuilt", "prevented", does_not_prove=DNP,
            detail={"members": len(outcome), "outcome": outcome})


def test_positive_control_unmutated_executes_once(cprt, tmp_path, monkeypatch):
    fl = flow(tmp_path / "a", monkeypatch)
    assert fl.run(fl.d1).status == "executed" and effect_ids(fl.dest.path) == [fl.d1.effect_id]
    fl = flow(tmp_path / "b", monkeypatch)
    dest, ex = atomic(fl, tmp_path / "b")
    claim = ex.provision_claim(proposal=fl.p, decision=fl.d1, now=fl.NOW)
    assert ex.execute(envelope=fl.envelope(fl.d1), claim_id=claim.claim_id).status == "executed"
    assert effect_ids(dest.path) == [fl.d1.effect_id]
