"""TR-1 trust snapshot validity, expiry and high-water (C01-C03). Worker C. Fixture mechanics reused from the Runtime's `Gov`/`Env` helpers
(see `_tr.py`); attacks and oracles written independently from the Runtime source and ADR EXT-S4-0 3.6/7.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import _tr
from _tr import PAIR, sa, v4


def test_c01_expired_snapshot_blocks_the_effect_not_just_the_writer(tmp_path, ev):
    ev["scenario"] = "TR-1"
    ev["expected"] = ("Same store, same claim: with the trusted clock at or after the accepted snapshot's valid_until the effect is refused "
                      "trust_snapshot_expired / HOLD with zero effects and the claim unconsumed; one second before valid_until the SAME claim executes "
                      "(1 effect, 1 receipt) so the refusal is attributable to the snapshot clock alone.")
    until = "2026-10-25T18:00:00Z"
    G = _tr.newgov(tmp_path, "a", snapshot_until=until)
    env, cid = G.claim()
    t0 = G.e.now

    def late():
        G.e.now = t0.replace(hour=20)
        res, info = _tr.attempt(G, env, cid)
        return {**info, "ok": _tr.refused_as(res, G, cid, {"trust_snapshot_expired"}, "HOLD"), "breach": G.counts()[0] > 0, "counts": list(G.counts())}

    def boundary():
        G.e.now = t0.replace(hour=18)  # exactly valid_until: the interval is half-open
        res, info = _tr.attempt(G, env, cid)
        return {**info, "ok": _tr.refused_as(res, G, cid, {"trust_snapshot_expired"}, "HOLD"), "breach": G.counts()[0] > 0, "counts": list(G.counts())}

    def before():
        G.e.now = t0.replace(hour=17, minute=59, second=59)
        res, info = _tr.attempt(G, env, cid)
        return {**info, "ok": res.status == "executed" and G.counts() == (1, 1, 1, 1), "counts": list(G.counts())}

    _tr.sub(ev, "refused_after_valid_until", late)
    _tr.sub(ev, "refused_at_exact_valid_until", boundary)
    _tr.sub(ev, "same_claim_executes_one_second_before", before)
    _tr.verdict(ev)


def test_c02_older_equal_expired_and_lowered_floor_snapshots_are_refused_and_change_nothing(tmp_path, ev):
    ev["scenario"] = "TR-1"
    ev["expected"] = ("After snapshot v3 is accepted: v2, v1, same-version/different-fingerprint and an already-expired v9 are refused typed "
                      "(trust_snapshot_version_stale REFUSE_STALE / trust_snapshot_expired) and every table, the anchor and the log head stay "
                      "byte-identical; identical redelivery of v3 is accepted without a log entry. After an external floor of 4 is set, lowering it is "
                      "refused (external_floor_lowered) and a claim bound to snapshot v1 is refused at the effect boundary trust_snapshot_version_stale "
                      "REFUSE_STALE with zero effects, while an untouched twin store (no floor) executes the same kind of claim.")
    G = _tr.newgov(tmp_path, "a")
    env, cid = G.claim()  # bound to snapshot v1
    G.e.sync(3)
    base = _tr.fingerprint_state(G)

    def refuse(label, trust_obj, code, cls, **kw):
        def run():
            got = _tr.sync_try(G, trust_obj, **kw)
            same = _tr.fingerprint_state(G) == base
            return {"refusal": got, "unchanged": same, "store": G.e.verify().state,
                    "ok": bool(got and got["code"] == code and (cls is None or got["refusal_class"] == cls) and same and G.e.verify().state == "known")}
        _tr.sub(ev, label, run)

    refuse("older_v2", v4.trust(2), "trust_snapshot_version_stale", "REFUSE_STALE")
    refuse("older_v1", v4.trust(1), "trust_snapshot_version_stale", "REFUSE_STALE")
    refuse("same_version_other_fingerprint", v4.trust(3, revoked_key_ids=frozenset({"key-other-9"})), "trust_snapshot_version_stale", "REFUSE_STALE")
    refuse("already_expired_v9", v4.trust(9, valid_until="2026-10-25T11:00:00Z"), "trust_snapshot_expired", None)

    def redelivery():
        res = G.dest.sync_selection("snapshot", trust=v4.trust(3))
        return {"entry_hashes": list(res.entry_hashes), "unchanged": _tr.fingerprint_state(G) == base,
                "ok": res.entry_hashes == () and _tr.fingerprint_state(G) == base}
    _tr.sub(ev, "identical_redelivery_accepted_without_entry", redelivery)

    def floor():
        G.dest.sync_selection("snapshot", trust=v4.trust(4), min_trust_snapshot_version=4)
        lowered = _tr.sync_try(G, v4.trust(5), min_trust_snapshot_version=2)
        res, info = _tr.attempt(G, env, cid)
        return {"lowering": lowered, **info, "counts": list(G.counts()), "breach": G.counts()[0] > 0,
                "ok": bool(lowered and lowered["code"] == "trust_snapshot_invalid" and lowered["cause"] == "external_floor_lowered"
                           and _tr.refused_as(res, G, cid, {"trust_snapshot_version_stale"}, "REFUSE_STALE"))}
    _tr.sub(ev, "external_floor_not_lowerable_and_old_claim_stale_at_effect", floor)

    def twin():
        T = _tr.newgov(tmp_path, "twin")
        e2, c2 = T.claim()
        T.e.sync(3)
        T.e.sync(4)  # no external floor
        res, info = _tr.attempt(T, e2, c2)
        return {**info, "counts": list(T.counts()), "ok": res.status == "executed" and T.counts() == (1, 1, 1, 1), "informational": False}
    _tr.sub(ev, "twin_without_floor_executes_v1_claim", twin)
    _tr.verdict(ev)


def test_c03_unrevocation_attempts_are_refused_and_revoked_authority_stays_dead(tmp_path, ev):
    ev["scenario"] = "TR-1"
    ev["expected"] = ("After a snapshot revokes (sel-test-1, epoch 1) the effect is refused selection_revoked; a newer snapshot that omits the revoked "
                      "pair, the revoked issuer key or lowers/omits a min-epoch floor is refused trust_snapshot_invalid (revocation_omitted / "
                      "min_epoch_floor_lowered) with all tables and the anchor unchanged; re-activating the revoked pair is refused; the claim bound to "
                      "the revoked selection never executes (0 effects, claim unconsumed).")
    G = _tr.newgov(tmp_path, "a")
    env, cid = G.claim()
    G.e.sync(2, revoked_selections=PAIR)

    def control():
        res, info = _tr.attempt(G, env, cid)
        return {**info, "ok": _tr.refused_as(res, G, cid, {"selection_revoked"}, "REFUSE"), "breach": G.counts()[0] > 0}
    _tr.sub(ev, "revocation_is_live_at_effect_boundary", control)

    base = _tr.fingerprint_state(G)

    def omit_pair():
        got = _tr.sync_try(G, v4.trust(3))
        return {"refusal": got, "unchanged": _tr.fingerprint_state(G) == base,
                "ok": bool(got and got["code"] == "trust_snapshot_invalid" and got["cause"] == "revocation_omitted" and _tr.fingerprint_state(G) == base)}
    _tr.sub(ev, "newer_snapshot_omitting_revoked_pair", omit_pair)

    keys = frozenset({"key-test-1"})
    G.e.sync(3, revoked_selections=PAIR, revoked_key_ids=keys)  # legitimate: adds the key revocation

    def omit_key():
        b = _tr.fingerprint_state(G)
        got = _tr.sync_try(G, v4.trust(4, revoked_selections=PAIR))
        return {"refusal": got, "unchanged": _tr.fingerprint_state(G) == b,
                "ok": bool(got and got["code"] == "trust_snapshot_invalid" and got["cause"] == "revocation_omitted" and _tr.fingerprint_state(G) == b)}
    _tr.sub(ev, "newer_snapshot_omitting_revoked_issuer_key", omit_key)

    G.e.sync(4, revoked_selections=PAIR, revoked_key_ids=keys, min_epochs=(("sel-x", 5),))

    def lower_floor():
        b = _tr.fingerprint_state(G)
        lowered = _tr.sync_try(G, v4.trust(5, revoked_selections=PAIR, revoked_key_ids=keys, min_epochs=(("sel-x", 2),)))
        omitted = _tr.sync_try(G, v4.trust(5, revoked_selections=PAIR, revoked_key_ids=keys, min_epochs=()))
        good = all(x and x["code"] == "trust_snapshot_invalid" and x["cause"] == "min_epoch_floor_lowered" for x in (lowered, omitted))
        return {"lowered": lowered, "omitted": omitted, "unchanged": _tr.fingerprint_state(G) == b, "ok": bool(good and _tr.fingerprint_state(G) == b)}
    _tr.sub(ev, "min_epoch_floor_lowered_or_omitted", lower_floor)

    def reactivate():
        b = _tr.fingerprint_state(G)
        try:
            G.e.activate(G.stmt)
            return {"activated": True, "breach": True, "ok": False}
        except sa.SelectionRefusal as exc:
            return {"refusal": {"code": exc.code, "class": exc.refusal_class, "cause": exc.cause}, "unchanged": _tr.fingerprint_state(G) == b,
                    "ok": exc.code in ("selection_revoked", "issuer_key_revoked") and _tr.fingerprint_state(G) == b}
    _tr.sub(ev, "reactivate_revoked_pair", reactivate)

    def final():
        res, info = _tr.attempt(G, env, cid)
        return {**info, "counts": list(G.counts()), "breach": G.counts()[0] > 0,
                "ok": _tr.refused_as(res, G, cid, {"selection_revoked", "issuer_key_revoked"}, "REFUSE")}
    _tr.sub(ev, "revoked_claim_still_refused_after_all_attempts", final)
    _tr.verdict(ev)
