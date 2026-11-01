"""T19. Rule-revision downgrade (ideas A05, F46, tier 2; leg of chain CH5).

SPDX-License-Identifier: Apache-2.0

Attacker: a policy editor presenting an older (previously adopted, since superseded) or never-adopted policy digest.
Setup: control plane rule-revision/0.1 on the host workflow (configured signer set), policy P1 adopted, then P2 adopted
advancing the chain from P1 (signed by an independent configured signer). The policy status the resolver serves carries the digest.
Route: decision by the control plane; effect through the runtime PinnedControlPlaneExecutor (whose per-call workflow view must
carry the rule-revision profile, R1 finding 1, see T15) into the SQLite destination, read independently.
Invariant: a superseded digest is not accepted as current, and an unadopted digest is refused, at decision time and at effect
time.

Does not prove: tamper evidence of the revision rows (the record store is a plain file; trust moves to the revision signer;
signer names are asserted, not authenticated); manifest signatures (do not exist); the institutional-governance repository's
own adoption flow (SCN-C20 unimplemented).
"""
from __future__ import annotations

import pytest

from _adv import effect_ids, flow
from conftest import observe

T = "T19"
DNP = "revision rows are not tamper-evident; signer names are asserted; no manifest signatures exist"
REVISER, SIGNER = "synthetic-principal:reviser", "synthetic-principal:signer"


def _digest(label):
    from agent_control_plane.bounded import commitment
    return commitment({"synthetic-policy-content": label})


def _setup(tmp_path, mp):
    import agent_control_plane.rule_revision as rr
    fl = flow(tmp_path, mp)
    fl.f.rule_revision_profile = rr.RuleRevisionProfile(signers=[SIGNER])
    ref = fl.tba.POLICY_REF

    def rev(rid, to, frm=None, supersedes=None):
        return rr.RuleRevision(revision_id=rid, rule_kind="policy", rule_ref=ref, from_digest=frm, to_digest=to, reviser=REVISER,
                               signer=SIGNER, authority_ref="synthetic-authority:1", reason="synthetic", supersedes=supersedes,
                               recorded_at=fl.NOW.isoformat())
    rr.append_rule_revision(fl.f.records, fl.f.rule_revision_profile, rev("r1", _digest("P1")))
    rr.append_rule_revision(fl.f.records, fl.f.rule_revision_profile, rev("r2", _digest("P2"), frm=_digest("P1")))
    return fl, ref


def _present(fl, ref, label):
    fl.r.policies[ref].digest = _digest(label)


def test_positive_control_current_digest_accepted(cprt, tmp_path, monkeypatch):
    fl, ref = _setup(tmp_path, monkeypatch)
    _present(fl, ref, "P2")
    d = fl.f.decide(fl.p, now=fl.NOW)
    assert d.result == "authorized", d.reasons
    assert fl.run(d).status == "executed" and effect_ids(fl.dest.path) == [d.effect_id]


@pytest.mark.parametrize("label", ["P1", "never-adopted"])
def test_downgraded_digest_refused_at_decision(cprt, tmp_path, monkeypatch, label):
    fl, ref = _setup(tmp_path, monkeypatch)
    _present(fl, ref, label)
    d = fl.f.decide(fl.p, now=fl.NOW)
    observe(T, f"decision with {label} digest", "prevented" if d.result == "hold" else "reproduced failure", does_not_prove=DNP,
            detail={"result": d.result, "reasons": list(d.reasons)})
    assert d.result == "hold" and "policy_status_unknown" in d.reasons, d.reasons


@pytest.mark.parametrize("label", ["P1", "never-adopted"])
def test_downgraded_digest_refused_at_effect_through_runtime_adapter(cprt, tmp_path, monkeypatch, label):
    fl, ref = _setup(tmp_path, monkeypatch)
    _present(fl, ref, "P2")
    d = fl.f.decide(fl.p, now=fl.NOW)
    assert d.result == "authorized", d.reasons
    _present(fl, ref, label)  # the editor swaps the served policy back between decision and effect
    r = fl.run(d)
    landed = bool(effect_ids(fl.dest.path))
    observe(T, f"effect with {label} digest after a P2 decision", "prevented" if not landed else "reproduced failure",
            does_not_prove=DNP, detail={"status": r.status, "error": r.error})
    assert r.status == "denied" and not landed, (r.status, r.error)
