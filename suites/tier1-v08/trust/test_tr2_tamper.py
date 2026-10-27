"""TR-2/TR-3 replay-log, hash-chain and pinned-row tampering observed at the effect boundary (C04-C07). Worker C.
Adversary model: write access to the destination SQLite file (triggers dropped where they block), the host anchor file untouched unless stated.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import hashlib
import json
import sqlite3

import _tr
from _tr import PAIR, log_entry, put_entry, sa, tamper_probe, v4


def _control(tmp_path):
    C = _tr.newgov(tmp_path, "ctl")
    e, c = C.claim()
    res, info = _tr.attempt(C, e, c)
    return {**info, "counts": list(C.counts()), "ok": res.status == "executed" and C.counts() == (1, 1, 1, 1)}


def _setup(tmp_path):
    G = _tr.newgov(tmp_path, "a")
    env, cid = G.claim()
    pristine = tmp_path / "pristine.sqlite3"
    _tr.save(G, pristine)
    return G, env, cid, pristine


def test_c04_log_entry_edits_break_the_chain_and_fail_closed(tmp_path, ev):
    ev["scenario"] = "TR-2"
    ev["expected"] = ("Each log edit (field edit; edit plus per-entry rehash; full re-chain of the suffix with the tables patched to match; "
                      "non-canonical text; unparseable text) makes the store unknown, and the effect is refused store_unknown / HOLD with zero "
                      "effects, attempts, receipts, budget use and the claim unconsumed; an untampered twin executes. Causes expected: "
                      "entry_hash_mismatch, prev_entry_hash_mismatch, anchor_hash_mismatch (full re-chain). Escape of a non-typed exception for the "
                      "last two is recorded as a finding, not a pass.")
    _tr.sub(ev, "positive_control_untampered_twin_executes", lambda: _control(tmp_path))
    G, env, cid, pristine = _setup(tmp_path)

    def edit():
        e = log_entry(G, 2)
        e["recorded_at"] = "2026-10-25T11:00:00.000000Z"
        put_entry(G, 2, e, rehash=False)

    def rehash():
        e = log_entry(G, 2)
        e["recorded_at"] = "2026-10-25T11:00:00.000000Z"
        put_entry(G, 2, e, rehash=True)

    def rechain():
        e2 = log_entry(G, 2)
        e2["recorded_at"] = "2026-10-25T11:00:00.000000Z"
        h2 = put_entry(G, 2, e2, rehash=True)
        e3 = log_entry(G, 3)
        e3["prev_entry_hash"] = h2
        h3 = put_entry(G, 3, e3, rehash=True)
        G.e.sql("UPDATE selection_activation_v1 SET activation_ref=?", (h3,))  # patch the one table value derived from the entry hash

    def noncanonical():
        e = log_entry(G, 2)
        G.e.sql("UPDATE selection_log_v1 SET entry_json=? WHERE activation_sequence=2", (json.dumps(e, indent=1),))

    def garbage():
        G.e.sql("UPDATE selection_log_v1 SET entry_json=? WHERE activation_sequence=2", ("{not json",))

    for name, fn, cause in (("field_edit_hash_untouched", edit, "entry_hash_mismatch"), ("edit_plus_entry_rehash", rehash, "prev_entry_hash_mismatch"),
                            ("full_rechain_of_suffix_tables_patched", rechain, "anchor_hash_mismatch"),
                            ("noncanonical_entry_text", noncanonical, "entry_not_canonical"), ("unparseable_entry_text", garbage, "entry_unparseable")):
        def run(fn=fn, cause=cause):
            out = tamper_probe(G, env, cid, pristine, fn)
            out["cause_as_predicted"] = cause in str(out.get("verify_cause"))
            return out
        _tr.sub(ev, name, run)
    _tr.verdict(ev, allow=("HELD", "CHARACTERIZED"))


def test_c05_deleted_reordered_duplicated_and_truncated_log_fail_closed(tmp_path, ev):
    ev["scenario"] = "TR-2"
    ev["expected"] = ("Deleting a middle entry (with and without renumbering), deleting the head, truncating the log together with every table row "
                      "derived from it, swapping two sequence numbers, and appending a forged-but-validly-hashed duplicate of the activation all make "
                      "the store unknown; the effect is refused store_unknown / HOLD, zero effects, claim unconsumed. A byte-exact duplicate row "
                      "cannot even be inserted (UNIQUE entry_hash).")
    _tr.sub(ev, "positive_control_untampered_twin_executes", lambda: _control(tmp_path))
    G, env, cid, pristine = _setup(tmp_path)

    def del_mid():
        G.e.sql("DELETE FROM selection_log_v1 WHERE activation_sequence=2")

    def del_mid_renumber():
        G.e.sql("DELETE FROM selection_log_v1 WHERE activation_sequence=2")
        G.e.sql("UPDATE selection_log_v1 SET activation_sequence=2 WHERE activation_sequence=3")

    def del_head():
        G.e.sql("DELETE FROM selection_log_v1 WHERE activation_sequence=3")

    def truncate_consistent():
        G.e.sql("DELETE FROM selection_log_v1 WHERE activation_sequence=3")
        for t in ("selection_activation_v1", "selection_lineage_v1", "selection_generation_v1", "selection_scope_required_v1"):
            G.e.sql(f"DELETE FROM {t}")
        G.e.sql("DELETE FROM selection_highwater_v1 WHERE hw_kind='scope'")

    def reorder():
        G.e.sql("UPDATE selection_log_v1 SET activation_sequence=100 WHERE activation_sequence=2")
        G.e.sql("UPDATE selection_log_v1 SET activation_sequence=2 WHERE activation_sequence=3")
        G.e.sql("UPDATE selection_log_v1 SET activation_sequence=3 WHERE activation_sequence=100")

    def dup_forged():
        e = log_entry(G, 3)
        h3 = G.e.sql("SELECT entry_hash FROM selection_log_v1 WHERE activation_sequence=3")[0][0]
        e["activation_sequence"], e["prev_entry_hash"] = 4, h3
        G.e.sql("INSERT INTO selection_log_v1(activation_sequence, entry_hash, entry_json) VALUES(4,?,?)",
                (sa.entry_hash_of(e), sa.canonical_bytes(e).decode("ascii")))

    for name, fn in (("delete_middle_entry", del_mid), ("delete_middle_and_renumber", del_mid_renumber), ("delete_head_entry", del_head),
                     ("truncate_log_and_all_derived_rows", truncate_consistent), ("swap_two_sequence_numbers", reorder),
                     ("append_forged_valid_hash_duplicate_activation", dup_forged)):
        _tr.sub(ev, name, lambda fn=fn: tamper_probe(G, env, cid, pristine, fn))

    def dup_exact():
        _tr.restore(G, pristine)
        G.e.drop_guards()
        row = G.e.sql("SELECT entry_hash, entry_json FROM selection_log_v1 WHERE activation_sequence=3")[0]
        try:
            G.e.sql("INSERT INTO selection_log_v1(activation_sequence, entry_hash, entry_json) VALUES(4,?,?)", (row[0], row[1]))
            return {"inserted": True, "ok": False}
        except sqlite3.IntegrityError as exc:
            return {"integrity_error": str(exc)[:120], "store": G.e.verify().state, "ok": G.e.verify().state == "known"}
    _tr.sub(ev, "byte_exact_duplicate_row_rejected_by_unique_hash", dup_exact)
    _tr.verdict(ev)


def _row(G):
    r = G.e.sql("SELECT statement_json, record_json FROM selection_activation_v1")[0]
    return json.loads(r[0]), json.loads(r[1])


def _canon(o) -> str:
    return sa.canonical_bytes(o).decode("ascii")


def test_c06_pinned_row_and_identity_substitution_in_the_activation_table(tmp_path, ev):
    ev["scenario"] = "TR-3"
    ev["expected"] = ("Rows the chain pins only indirectly (statement_json via selection_digest, record_json via the statement's record pin) and the "
                      "identity columns cannot be substituted: widening the record payload (digest untouched; digest columns recomputed to match), "
                      "non-canonical or duplicate-key or valid_until-extended statement text, and swapped selection_id / record_digest / "
                      "selection_digest / participation columns each make the store unknown; the effect is refused store_unknown / HOLD with zero "
                      "effects and the claim unconsumed. Any variant that lets the effect commit is a BREACH.")
    _tr.sub(ev, "positive_control_untampered_twin_executes", lambda: _control(tmp_path))
    G, env, cid, pristine = _setup(tmp_path)

    def widen_record():
        _, rec = _row(G)
        rec["payload"]["allowed_actions"] = sorted(rec["payload"]["allowed_actions"] + ["act-pay"])
        G.e.sql("UPDATE selection_activation_v1 SET record_json=?", (_canon(rec),))

    def widen_record_and_recompute_digests():
        _, rec = _row(G)
        rec["payload"]["allowed_actions"] = sorted(rec["payload"]["allowed_actions"] + ["act-pay"])
        body = {k: v for k, v in rec.items() if k != "record_digest"}
        new = "sha256:" + hashlib.sha256(sa.canonical_bytes(body)).hexdigest()
        rec["record_digest"] = new
        pol = v4.ident.effective_policy_digest(v4.f1ab.FAMILY_F1AB, {k: sorted(rec["payload"][k]) for k in sa.sa_fields()})
        G.e.sql("UPDATE selection_activation_v1 SET record_json=?, record_digest=?, record_policy_digest=?", (_canon(rec), new, pol))

    def stmt_noncanonical():
        st, _ = _row(G)
        G.e.sql("UPDATE selection_activation_v1 SET statement_json=?", (json.dumps(st, indent=1),))

    def stmt_duplicate_key():
        st, _ = _row(G)
        G.e.sql("UPDATE selection_activation_v1 SET statement_json=?", ('{"epoch":999,' + _canon(st)[1:],))

    def stmt_extend_validity():
        st, _ = _row(G)
        st["effective"]["valid_until"] = "2099-01-01T00:00:00Z"
        G.e.sql("UPDATE selection_activation_v1 SET statement_json=?, valid_until=?", (_canon(st), "2099-01-01T00:00:00Z"))

    cols = {
        "swap_selection_id": "UPDATE selection_activation_v1 SET selection_id='sel-evil'",
        "swap_record_digest": "UPDATE selection_activation_v1 SET record_digest='sha256:" + "9" * 64 + "'",
        "swap_selection_digest": "UPDATE selection_activation_v1 SET selection_digest='sha256:" + "8" * 64 + "'",
        "swap_participation_to_optional": "UPDATE selection_activation_v1 SET participation='optional'",
        "swap_scope_json_operation": "UPDATE selection_activation_v1 SET scope_json=replace(scope_json,'op-test','op-evil')",
    }
    for name, fn in (("widen_record_payload_digest_untouched", widen_record),
                     ("widen_record_payload_all_digest_columns_recomputed", widen_record_and_recompute_digests),
                     ("statement_text_noncanonical", stmt_noncanonical), ("statement_text_duplicate_key", stmt_duplicate_key),
                     ("statement_valid_until_extended_with_column", stmt_extend_validity)):
        _tr.sub(ev, name, lambda fn=fn: tamper_probe(G, env, cid, pristine, fn))
    for name, sql in cols.items():
        _tr.sub(ev, name, lambda sql=sql: tamper_probe(G, env, cid, pristine, lambda: G.e.sql(sql)))
    _tr.verdict(ev, allow=("HELD", "CHARACTERIZED"))


def test_c07_table_level_unrevocation_of_a_revoked_selection_is_detected(tmp_path, ev):
    ev["scenario"] = "TR-2"
    ev["expected"] = ("Once a snapshot revoked the selection the effect is refused selection_revoked (control). Flipping activation_state back to "
                      "active, deleting the revoked-pair row, rolling policy_generation back, or all three, makes the store unknown and the effect "
                      "is refused store_unknown / HOLD; the claim bound to the revoked selection never executes (0 effects).")
    G = _tr.newgov(tmp_path, "a")
    env, cid = G.claim()
    G.e.sync(2, revoked_selections=PAIR)

    def control():
        res, info = _tr.attempt(G, env, cid)
        return {**info, "ok": _tr.refused_as(res, G, cid, {"selection_revoked"}, "REFUSE"), "breach": G.counts()[0] > 0}
    _tr.sub(ev, "control_revocation_is_live", control)
    pristine = tmp_path / "pristine.sqlite3"
    _tr.save(G, pristine)

    def flip():
        G.e.sql("UPDATE selection_activation_v1 SET activation_state='active', transition_ref=NULL")

    def del_pair():
        G.e.sql("DELETE FROM selection_revoked_v1")

    def all_three():
        G.e.sql("UPDATE selection_activation_v1 SET activation_state='active', transition_ref=NULL, policy_generation=1")
        G.e.sql("DELETE FROM selection_revoked_v1")
        G.e.sql("UPDATE selection_generation_v1 SET policy_generation=1")

    for name, fn in (("flip_state_to_active", flip), ("delete_revoked_pair_row", del_pair), ("flip_delete_and_roll_generation_back", all_three)):
        _tr.sub(ev, name, lambda fn=fn: tamper_probe(G, env, cid, pristine, fn))
    _tr.verdict(ev)
