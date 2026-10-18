"""T06. Adapter identity versus implementation (idea A03, tier 2).

SPDX-License-Identifier: Apache-2.0

Attacker: a party who replaces the implementation behind an unchanged adapter id (here: the destination implementation the
runtime adapter writes through), so that the effect it writes differs from the approved one (amount x10).
Invariant (plan): the swap is detected after the fact by the ledger, or the gap is recorded as accepted limit E6. The expected
classification is 'detected only' (never 'prevented': nothing binds an adapter id to its code; adapter attestation is absent).
Detection path: the independent verifier (tier V4) over the control plane record and a projection of the destination rows.

Does not prove: prevention (needs adapter attestation, absent); detection by anything other than the verifier's V4 ledger
checks; a lookalike that also rewrites the ledger consistently (the verifier's forgery bound says a consistent rewrite passes).
"""
from __future__ import annotations

from _adv import bundle, effect_ids, flow, ledger_projection, refuted, rows, verify
from conftest import observe, require

T = "T06"
DNP = "prevention needs adapter attestation (absent, E6); a consistent ledger rewrite is outside the verifier's reach"


def _lookalike(path, fl):
    """Same adapter id, same class surface; the commit writes ten times the approved amount after the honest write."""
    from engine.safe_executor import DurableRefundDestination

    class Lookalike(DurableRefundDestination):
        def commit(self, snapshot, **kw):
            out = super().commit(snapshot, **kw)
            with self._connect() as conn:
                conn.execute("UPDATE effects SET amount = amount * 10 WHERE effect_id = ?", (snapshot.effect_id,))
            return out

    return Lookalike(path)


def test_registered_implementation_yields_a_consistent_ledger(cprt, tmp_path, monkeypatch):
    vf = require("verifier")["verifier"]
    fl = flow(tmp_path, monkeypatch)
    assert fl.run(fl.d1).status == "executed"
    code, report = verify(vf, bundle(fl, tmp_path / "b"), ledger=ledger_projection(fl.dest.path))
    assert refuted(report) == set(), report.get("summary")
    assert code in (0, 3)


def test_lookalike_implementation_is_detected_only(cprt, tmp_path, monkeypatch):
    vf = require("verifier")["verifier"]
    fl = flow(tmp_path, monkeypatch, dest_factory=_lookalike)
    r = fl.run(fl.d1)
    assert effect_ids(fl.dest.path) == [fl.d1.effect_id]
    [row] = rows(fl.dest.path, "effects")
    assert row["amount"] == 10 * fl.p.amount, "the lookalike did not change the effect; the test is not exercising the swap"
    # The control plane accepted the run (nothing on the effect path compares the written amount).
    record = fl.f.records.load()
    assert r.status == "executed" and record.attempts[-1].status == "acknowledged"
    code, report = verify(vf, bundle(fl, tmp_path / "b"), ledger=ledger_projection(fl.dest.path))
    hit = refuted(report)
    observe(T, "lookalike implementation behind the registered adapter id", "detected only" if hit else "reproduced failure",
            does_not_prove=DNP, detail={"refuted_checks": sorted(hit), "verifier_exit": code})
    assert "v4.ledger.row-matches-binding" in hit, report.get("summary")
    assert code not in (0, 3)
