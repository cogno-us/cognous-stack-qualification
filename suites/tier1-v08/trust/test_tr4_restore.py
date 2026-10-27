"""TR-4 restore and anchor consistency at the effect boundary (C08-C10). Worker C.
ADR EXT-S4-0 3.6: an older database than the anchor is unknown; a store ahead of a stale anchor with an unbroken chain is accepted; a consistent
restore of database AND anchor is the DISCLOSED limit (undetectable by construction) and is recorded as CHARACTERIZED, never as a pass.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import json

import _tr
from _tr import PAIR, tamper_probe, v4


def test_c08_restoring_an_older_database_never_resurrects_revoked_authority(tmp_path, ev):
    ev["scenario"] = "TR-4"
    ev["expected"] = ("A claim whose selection was revoked after a database copy was taken: control refuses selection_revoked. After the OLDER copy "
                      "is restored while the host anchor stays current, verify() is unknown with cause anchor_ahead, the effect is refused "
                      "store_unknown / HOLD with zero effects and the claim unconsumed, writers and readers also HOLD, and the refused attempts do "
                      "not move the anchor.")
    G = _tr.newgov(tmp_path, "a")
    env, cid = G.claim()
    old = tmp_path / "old.sqlite3"
    _tr.save(G, old)
    G.e.sync(2, revoked_selections=PAIR)

    def control():
        res, info = _tr.attempt(G, env, cid)
        return {**info, "ok": _tr.refused_as(res, G, cid, {"selection_revoked"}, "REFUSE"), "breach": G.counts()[0] > 0}
    _tr.sub(ev, "control_revocation_is_live_before_restore", control)
    anchor_before = G.e.anchor.read_text()

    def restore_old():
        _tr.restore(G, old)
        st = G.e.verify()
        res, info = _tr.attempt(G, env, cid)
        typed_hold = _tr.refused_as(res, G, cid, {"store_unknown"}, "HOLD")
        return {"verify_state": st.state, "verify_cause": st.cause, **info, "counts": list(G.counts()), "breach": G.counts()[0] > 0,
                "ok": bool(st.state == "unknown" and str(st.cause).startswith("anchor_ahead") and typed_hold)}
    _tr.sub(ev, "older_db_with_current_anchor_effect_hold", restore_old)

    def writers_and_readers():
        w = _tr.sync_try(G, v4.trust(3, revoked_selections=PAIR))
        try:
            G.e.state()
            r = None
        except _tr.sa.SelectionRefusal as exc:
            r = {"code": exc.code, "refusal_class": exc.refusal_class, "cause": exc.cause}
        return {"writer": w, "reader": r, "anchor_unchanged": G.e.anchor.read_text() == anchor_before,
                "ok": bool(w and w["code"] == "store_unknown" and w["refusal_class"] == "HOLD" and r and r["code"] == "store_unknown"
                           and G.e.anchor.read_text() == anchor_before)}
    _tr.sub(ev, "writers_readers_hold_and_anchor_not_moved", writers_and_readers)
    _tr.verdict(ev)


def test_c09_anchor_absent_altered_foreign_or_ahead_fails_closed(tmp_path, ev):
    ev["scenario"] = "TR-4"
    ev["expected"] = ("For a healthy known store and a good claim, each anchor condition (absent, digest altered, head hash altered, garbage, empty, "
                      "foreign store, head ahead, replayed digest wrong, evidence head ahead, floor higher than store, wrong version, extra member) makes "
                      "the store unknown and the effect is refused store_unknown / HOLD with zero effects and the claim unconsumed; with the genuine "
                      "anchor restored the SAME claim executes (1 effect, 1 receipt).")
    G = _tr.newgov(tmp_path, "a")
    env, cid = G.claim()
    pristine = tmp_path / "pristine.sqlite3"
    _tr.save(G, pristine)
    a0 = G.e.anchor.read_text()
    B = _tr.newgov(tmp_path, "b")
    foreign = B.e.anchor.read_text()
    p = G.e.anchor

    def altered_digest():
        d = json.loads(a0)
        d["anchor_digest"] = "sha256:" + "0" * 64
        p.write_text(json.dumps(d))

    muts = {
        "anchor_absent": p.unlink,
        "anchor_digest_altered": altered_digest,
        "anchor_head_hash_altered": lambda: G.e.rewrite_anchor(head_entry_hash="sha256:" + "7" * 64),
        "anchor_garbage": lambda: p.write_text("{not json"),
        "anchor_empty": lambda: p.write_text(""),
        "anchor_of_another_store": lambda: p.write_text(foreign),
        "anchor_head_ahead_of_store": lambda: G.e.rewrite_anchor(head_sequence=4),
        "anchor_replayed_digest_wrong": lambda: G.e.rewrite_anchor(lineage_digest="sha256:" + "6" * 64),
        "anchor_evidence_head_ahead": lambda: G.e.rewrite_anchor(evidence_head_sequence=5),
        "anchor_floor_above_store": lambda: G.e.rewrite_anchor(floor_min_trust_snapshot_version=9),
        "anchor_wrong_version": lambda: G.e.rewrite_anchor(anchor_version="ocs-s4/store-anchor/9"),
        "anchor_extra_member": lambda: G.e.rewrite_anchor(extra="x"),
    }
    for name, fn in muts.items():
        _tr.sub(ev, name, lambda fn=fn: tamper_probe(G, env, cid, pristine, fn, anchor_text=a0))

    def positive():
        _tr.restore(G, pristine)
        p.write_text(a0)
        res, info = _tr.attempt(G, env, cid)
        return {**info, "counts": list(G.counts()), "ok": res.status == "executed" and G.counts() == (1, 1, 1, 1)}
    _tr.sub(ev, "genuine_anchor_same_claim_executes", positive)
    _tr.verdict(ev)


def test_c10_consistent_restore_of_database_and_anchor_is_the_disclosed_limit(tmp_path, ev):
    ev["scenario"] = "TR-4"
    ev["expected"] = ("Disclosed limit (ADR 3.6): restoring database AND anchor together to a point before a revocation is undetectable by "
                      "construction. Expected observation: the store verifies known and the effect against the formerly revoked selection COMMITS. "
                      "That is recorded CHARACTERIZED (not a pass, not a defect against the documented contract). Also observed: a stale anchor "
                      "over the current (revoked) database is accepted (store ahead of anchor, chain unbroken) and does NOT weaken the revocation.")
    G = _tr.newgov(tmp_path, "a")
    env, cid = G.claim()
    old = tmp_path / "old.sqlite3"
    _tr.save(G, old)
    a0 = G.e.anchor.read_text()
    G.e.sync(2, revoked_selections=PAIR)
    a1 = G.e.anchor.read_text()

    def control():
        res, info = _tr.attempt(G, env, cid)
        return {**info, "ok": _tr.refused_as(res, G, cid, {"selection_revoked"}, "REFUSE"), "breach": G.counts()[0] > 0}
    _tr.sub(ev, "control_revocation_is_live", control)

    def stale_anchor():
        G.e.anchor.write_text(a0)
        st = G.e.verify()
        res, info = _tr.attempt(G, env, cid)
        G.e.anchor.write_text(a1)
        return {"verify_state": st.state, "verify_cause": st.cause, **info, "counts": list(G.counts()), "breach": G.counts()[0] > 0,
                "ok": bool(_tr.refused_as(res, G, cid, {"selection_revoked", "store_unknown"}))}
    _tr.sub(ev, "stale_anchor_over_current_db_revocation_still_enforced", stale_anchor)

    consistent: dict = {}

    def consistent_restore():
        _tr.restore(G, old)
        G.e.anchor.write_text(a0)
        st = G.e.verify()
        res, info = _tr.attempt(G, env, cid)
        consistent.update(verify_state=st.state, executed=res.status == "executed", counts=list(G.counts()))
        return {"verify_state": st.state, "verify_cause": st.cause, **info, "counts": list(G.counts()), "informational": True}
    _tr.sub(ev, "consistent_db_and_anchor_restore_before_revocation", consistent_restore)

    probes = ev["observed"]["probes"]
    if any(v.get("breach") for k, v in probes.items() if k != "consistent_db_and_anchor_restore_before_revocation"):
        ev["verdict"], ev["note"] = "BREACH", "revocation not enforced while the database was current"
    elif "harness_error" in probes["consistent_db_and_anchor_restore_before_revocation"] or not probes["control_revocation_is_live"].get("ok"):
        ev["verdict"], ev["note"] = "INCONCLUSIVE", "the restore scenario was not exercised"
    elif consistent.get("executed") and consistent.get("verify_state") == "known" and consistent["counts"][0] == 1:
        ev["verdict"] = "CHARACTERIZED"
        ev["note"] = ("ADR EXT-S4-0 3.6 disclosed limit reproduced: a consistent restore of database and anchor to a point before the revocation is "
                      "undetectable and the formerly revoked selection's effect committed (1 effect). Mitigation is operator custody and anchor cadence "
                      "(out of scope for the synthetic host-file anchor). This is NOT a pass.")
    else:
        ev["verdict"], ev["note"] = "HELD", "consistent restore was refused or detected (tighter than the documented limit); see probes"
    assert ev["verdict"] in ("CHARACTERIZED", "HELD"), (ev["verdict"], ev["note"])
