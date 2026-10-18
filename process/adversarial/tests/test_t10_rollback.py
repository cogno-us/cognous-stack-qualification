"""T10. Rollback of programme-2 state (idea B14, tier 3).

SPDX-License-Identifier: Apache-2.0

Attacker: an operator restoring a store from an earlier copy (SQLite online backup of the destination; file copy of the control
plane record store).
Invariant (plan): after restoring an older copy, a spent budget unit, operation key or witnessed record row is still enforced, or
its loss is detected by a digest held elsewhere; undetected loss is recorded, not hidden.
Per store, the classification extends SCN-D07 (INCONCLUSIVE, no external anchor) rather than replacing it.

Does not prove: prevention (needs an external anchor, absent); the freshness floors (input_time_floors are a mutable dictionary
the witness does not cover by design) are not exercised; a witness held by the store writer gives no evidence (module scope).
"""
from __future__ import annotations

import json
import shutil
import sqlite3

from _adv import atomic, effect_ids, flow
from conftest import observe

T = "T10"
DNP = "no external anchor exists; freshness floors not exercised; a local-file witness is a test aid"


def _backup(src_path, dst_path):
    src, dst = sqlite3.connect(src_path), sqlite3.connect(dst_path)
    try:
        src.backup(dst)
    finally:
        src.close()
        dst.close()


def test_positive_control_no_restore_budget_refuses_second_spend(cprt, tmp_path, monkeypatch):
    fl = flow(tmp_path, monkeypatch)
    dest, ex = atomic(fl, tmp_path)
    claim = ex.provision_claim(proposal=fl.p, decision=fl.d1, now=fl.NOW)
    assert ex.execute(envelope=fl.envelope(fl.d1), claim_id=claim.claim_id).status == "executed"
    assert ex.execute(envelope=fl.envelope(fl.d1), claim_id=claim.claim_id).status == "denied"
    assert effect_ids(dest.path) == [fl.d1.effect_id]


def test_atomic_budget_and_claim_rollback_is_undetected(cprt, tmp_path, monkeypatch):
    """Known limit (SCN-D07): restoring the pre-spend destination re-issues the claim and the budget unit; the effect re-commits."""
    fl = flow(tmp_path, monkeypatch)
    dest, ex = atomic(fl, tmp_path)
    claim = ex.provision_claim(proposal=fl.p, decision=fl.d1, now=fl.NOW)
    _backup(dest.path, tmp_path / "pre-spend.sqlite3")
    first = ex.execute(envelope=fl.envelope(fl.d1), claim_id=claim.claim_id)
    _backup(tmp_path / "pre-spend.sqlite3", dest.path)
    assert dest.claim_state(claim.claim_id) == "issued" and dest.budget_state(f"grant:{fl.d1.binding.grant_id}")["used_effects"] == 0
    second = ex.execute(envelope=fl.envelope(fl.d1), claim_id=claim.claim_id)
    commits = [r.status for r in (first, second)].count("executed")
    observe(T, "atomic destination restored before the spend", "reproduced failure" if commits == 2 else "prevented",
            does_not_prove=DNP, detail={"commits_acknowledged": commits, "rows_now": len(effect_ids(dest.path)),
                                        "known": "SCN-D07, no external anchor"})
    assert commits == 2 and effect_ids(dest.path) == [fl.d1.effect_id]  # characterised: two commits acknowledged, one row left


def test_operation_key_rollback_of_destination_only_is_undetected(cprt, tmp_path, monkeypatch):
    """Identity profile on (no dedupe profile): restore only the destination (its operation-key table) and renew.

    Characterised known limit (SCN-D07): the operation key is enforced at the destination only, so the renewed effect lands and
    nothing in the control plane record refuses it. The dedupe-ttl/0.1 profile's own-ledger refusal is not exercised here."""
    fl = flow(tmp_path, monkeypatch, identity=True, wide=True)
    _backup(fl.dest.path, tmp_path / "pre.sqlite3")
    assert fl.run(fl.d1).status == "executed"
    _backup(tmp_path / "pre.sqlite3", fl.dest.path)
    assert effect_ids(fl.dest.path) == []
    fl.publish_revision("2")
    fl.f.record_renewal("op-order-100/refund-1", to_revision="2", written_by=fl.ISSUER, now=fl.NOW)
    d2 = fl.f.decide(fl.p, now=fl.NOW)
    landed = False
    if d2.result == "authorized":
        r2 = fl.run(d2)
        landed = r2.status == "executed"
    observe(T, "destination operation-key table restored, control-plane record kept", "reproduced failure" if landed else "prevented",
            does_not_prove=DNP + "; dedupe-ttl/0.1 (control-plane-side ledger refusal) not exercised",
            detail={"decision": d2.result, "reasons": list(d2.reasons), "known": "SCN-D07, no external anchor"})
    assert landed and len(effect_ids(fl.dest.path)) == 1  # characterised: the restored key table let the renewal commit


def test_operation_key_rollback_of_both_stores_is_detected_only_with_a_witness(cprt, tmp_path, monkeypatch):
    """Restore the destination AND the control plane record: nothing in either store remembers; a witness digest held elsewhere does."""
    import agent_control_plane.witness as W
    fl = flow(tmp_path, monkeypatch, identity=True, wide=True)
    _backup(fl.dest.path, tmp_path / "pre.sqlite3")
    shutil.copyfile(fl.f.records.path, tmp_path / "pre-record.json")
    assert fl.run(fl.d1).status == "executed"
    witness = W.LocalFileWitness(tmp_path / "elsewhere" / "witness.jsonl")
    W.publish_head(json.loads(fl.f.records.path.read_text(encoding="utf-8")), witness)
    _backup(tmp_path / "pre.sqlite3", fl.dest.path)
    shutil.copyfile(tmp_path / "pre-record.json", fl.f.records.path)
    fl.publish_revision("2")
    fl.f.record_renewal("op-order-100/refund-1", to_revision="2", written_by=fl.ISSUER, now=fl.NOW)
    d2 = fl.f.decide(fl.p, now=fl.NOW)
    r2 = fl.run(d2) if d2.result == "authorized" else None
    verdict = W.verify_against_witness(json.loads(fl.f.records.path.read_text(encoding="utf-8")), witness)
    second = r2 is not None and r2.status == "executed"
    observe(T, "both stores restored; witness held elsewhere", "detected only" if (second and not verdict.ok) else
            ("prevented" if not second else "reproduced failure"), does_not_prove=DNP,
            detail={"second_commit": second, "witness_ok": verdict.ok, "witness_reasons": list(verdict.reasons)})
    assert not verdict.ok, "the witness did not see the rollback"
    assert set(verdict.reasons) & {W.CODE_SHRUNK, W.CODE_HEAD_MISMATCH}


def test_record_rollback_without_a_witness_is_invisible_to_the_record_store(cprt, tmp_path, monkeypatch):
    fl = flow(tmp_path, monkeypatch)
    shutil.copyfile(fl.f.records.path, tmp_path / "pre-record.json")
    assert fl.run(fl.d1).status == "executed"
    shutil.copyfile(tmp_path / "pre-record.json", fl.f.records.path)
    record = fl.f.records.load()  # loads without complaint: nothing in the store itself records its own history
    assert record.attempts == []
    observe(T, "record store restored, no witness", "reproduced failure", does_not_prove=DNP,
            detail="known: the record store has no keyed integrity; the witness profile is the opt-in control")
