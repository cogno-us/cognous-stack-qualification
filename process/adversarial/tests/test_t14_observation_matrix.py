"""T14. Observation field matrix (ideas H55, H56, H58, tier 5).

SPDX-License-Identifier: Apache-2.0

Attacker: an executor or other party who writes the effect-side record (the destination ledger) or the observation times.
Invariant: a genuine run's evidence with one field changed (effect id, grant, target, amount, unit, payload, state), a matching
row written for an effect no decision authorised, or an acknowledgement with no ledger row, is never counted as verified
completion. 'Verified' here means: the independent verifier (cognous-verify, tier V4) refutes nothing and exits 0 or 3.
Substitute values come from the control plane's own second genuine fixture (the T2 refund) and from a second genuine run.

Does not prove: that the effect happened in the world; detection of a CONSISTENT rewrite of record and ledger (the verifier's
forgery bound); profile-on records (the verifier refuses them until J1, F-3); tenant substitution (the ledger row has no
tenant member, so it is not expressible at this layer).
"""
from __future__ import annotations

import copy
import json

import pytest

from _adv import bundle, flow, ledger_projection, refuted, verify
from conftest import observe, require

T = "T14"
DNP = "consistent rewrites pass by the verifier's forgery bound; profile-on records and tenant are out of reach here"


@pytest.fixture
def genuine(cprt, tmp_path, monkeypatch):
    vf = require("verifier")["verifier"]
    fl = flow(tmp_path / "one", monkeypatch)
    assert fl.run(fl.d1).status == "executed"
    b = bundle(fl, tmp_path / "bundle")
    ledger = ledger_projection(fl.dest.path)
    other = fl.tba.proposal("T2")
    return vf, fl, b, ledger, other


def _verified(code, report):
    return code in (0, 3) and not refuted(report)


def test_positive_control_unchanged_evidence_is_verified(genuine):
    vf, fl, b, ledger, _ = genuine
    code, report = verify(vf, b, ledger=ledger)
    assert _verified(code, report), report.get("summary")


def test_single_field_substitution_is_never_verified(genuine):
    vf, fl, b, ledger, other = genuine
    [eid] = ledger["effects"]
    subs = {
        "target": other.target,
        "amount": float(other.amount),
        "unit": "EUR",
        "payload": copy.deepcopy(other.payload),
        "state": "partial",
        "grant_id": "urn:cognous:grant:other",
        "effect_id": "sha256:" + "ab" * 32,
    }
    results = {}
    for name, value in subs.items():
        doc = copy.deepcopy(ledger)
        row = doc["effects"].pop(eid)
        row[name] = value
        key = value if name == "effect_id" else eid
        doc["effects"][key] = row
        if name == "grant_id":
            doc["grant_effect_counts"] = {value: 1}
        code, report = verify(vf, b, ledger=doc, name=f"sub-{name}")
        results[name] = {"verified": _verified(code, report), "refuted": sorted(refuted(report)), "exit": code}
    observe(T, "single ledger field substituted", "detected only" if not any(v["verified"] for v in results.values())
            else "reproduced failure", does_not_prove=DNP, detail=results)
    assert not [k for k, v in results.items() if v["verified"]], results


def test_unrelated_matching_row_is_not_verified(genuine, tmp_path, monkeypatch):
    """A second genuine run's row (another effect id, same grant shape) added to this run's ledger."""
    vf, fl, b, ledger, _ = genuine
    fl2 = flow(tmp_path / "two", monkeypatch)
    p2 = fl2.p.model_copy(deep=True)
    p2.correlation_id = "case-2"
    ref = fl2.r.contexts[fl2.PROFILE]["grant"]["approval_refs"][0]
    fl2.r.approvals[ref].proposal_commitment = fl2.cp.commitment(p2.model_dump(mode="json", exclude_none=False))
    fl2.tra.bind_approval(fl2.r, fl2.f.runtime_authority_profile or fl2.cfg)
    d2 = fl2.f.decide(p2, now=fl2.NOW)
    assert d2.result == "authorized" and d2.effect_id != fl.d1.effect_id, d2.reasons
    assert fl2.run(d2, p2).status == "executed"
    extra = ledger_projection(fl2.dest.path)["effects"][d2.effect_id]
    doc = copy.deepcopy(ledger)
    doc["effects"][d2.effect_id] = extra
    doc["grant_effect_counts"] = {k: v + 1 for k, v in doc["grant_effect_counts"].items()}
    code, report = verify(vf, b, ledger=doc, name="extra-row")
    hit = refuted(report)
    observe(T, "unrelated matching row added", "detected only" if hit else "reproduced failure", does_not_prove=DNP,
            detail=sorted(hit))
    assert not _verified(code, report)


def test_acknowledgement_without_ledger_row_is_not_verified(genuine):
    vf, fl, b, ledger, _ = genuine
    code, report = verify(vf, b, ledger={"effects": {}, "grant_effect_counts": {}}, name="ack-only")
    hit = refuted(report)
    observe(T, "acknowledged attempt, no ledger row", "detected only" if hit else "reproduced failure", does_not_prove=DNP,
            detail=sorted(hit))
    assert "v4.ledger.acknowledged-attempts-have-rows" in hit


def test_observation_time_moved_outside_the_interval_is_not_verified(genuine):
    """The accepted observation's time moved one day before the decision (interval leg)."""
    vf, fl, b, ledger, _ = genuine
    doc = json.loads((b / "run-record.json").read_text(encoding="utf-8"))
    assert doc["observations"], "the genuine run recorded no accepted observation"
    doc["observations"][-1]["observed_at"] = "2026-10-04T19:00:00+00:00"
    (b / "moved.json").write_text(json.dumps(doc), encoding="utf-8")
    code, report = verify(vf, b, ledger=ledger, record=b / "moved.json", name="moved")
    observe(T, "observation time outside the interval", "detected only" if not _verified(code, report) else "reproduced failure",
            does_not_prove=DNP, detail={"refuted": sorted(refuted(report)), "exit": code})
    assert not _verified(code, report)
