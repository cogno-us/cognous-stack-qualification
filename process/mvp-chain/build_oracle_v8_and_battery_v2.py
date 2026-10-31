#!/usr/bin/env python3
"""Authoring record and checker for oracle v8 and battery v2 (OCS-MVP-QGATE-05 assembly). SPDX-License-Identifier: Apache-2.0

Builds process/mvp-chain/expectations.proposed.v8.json from the byte-identical v7 file plus the worker fragments (suites/mvp-chain/v8_rows_b1.fragment.json,
nc4_03_oracle_v8_fragment.proposed.json) and process/mvp-acceptance/mandatory-battery.proposed.v2.json from battery v1 plus the fragments. Nothing here edits
v1..v7: they are only read. Every statement about what changed is computed from the files, never typed. `--check` rebuilds both documents in memory and fails
unless the committed files are byte-identical to the rebuild; it also re-proves the no-weakening claims. Stdlib only, no network.

Usage: python3 build_oracle_v8_and_battery_v2.py --repo-root <tree> [--write | --check]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

V7_SHA = "0dc17a1984e1c3c153f3cb6e3f7fdd4dad87cdc4414728a20df0f8174e402f6b"
V1_BATTERY_SHA = "a520e9e92534f196a48d4229d984231abbb71c23dfe63b573d919d2285bcdb16"
DISPOSITION = "https://github.com/cogno-us/cognous-open-control-stack/issues/215#issuecomment-6537418060"
ORACLE_V7 = "process/mvp-chain/expectations.proposed.v7.json"
ORACLE_V8 = "process/mvp-chain/expectations.proposed.v8.json"
BATTERY_V1 = "process/mvp-acceptance/mandatory-battery.proposed.v1.json"
BATTERY_V2 = "process/mvp-acceptance/mandatory-battery.proposed.v2.json"
FR_B1 = "suites/mvp-chain/v8_rows_b1.fragment.json"
FR_B2_ORACLE = "suites/mvp-chain/nc4_03_oracle_v8_fragment.proposed.json"
FR_B2_BATTERY = "suites/mvp-chain/nc4_03_battery_v2_fragment.proposed.json"
BATTERY_V2_NAME = "process/mvp-acceptance/mandatory-battery.proposed.v2.json"
OLD_PREFIX, NEW_PREFIX = "nc_unmediated.source_level.", "nc4_03_det.source_level."
TEST_FILES = {"kill": "suites/mvp-chain/test_process_kill_a1.py", "prune": "suites/mvp-chain/test_ledger_pruning_a2.py"}
NEW_INVOCATION_PATHS = ["suites/mvp-chain/test_process_kill_a1.py", "suites/mvp-chain/test_ledger_pruning_a2.py",
                        "suites/mvp-chain/test_nc4_03_mutation_set.py", "suites/mvp-chain/test_nc4_03_host_subcases.py"]


def sha(path_or_bytes) -> str:
    data = path_or_bytes if isinstance(path_or_bytes, bytes) else Path(path_or_bytes).read_bytes()
    return hashlib.sha256(data).hexdigest()


def dump(doc) -> bytes:
    return (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def load(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def counts_of(rows: list[dict]) -> dict:
    mand = [r for r in rows if r.get("mandatory")]
    nc = [r for r in mand if r["id"].startswith("NC")]
    groups = Counter(re.match(r"NC(\d+)", r["id"]).group(1) for r in nc)
    return {"oracle_rows": len(rows), "mandatory_rows": len(mand), "non_mandatory_rows": len(rows) - len(mand), "mandatory_nc_rows": len(nc),
            "negative_groups": len(groups), "mandatory_nc_rows_per_group": {f"NC{k}": groups[k] for k in sorted(groups, key=int)}}


def build_oracle(repo: Path) -> tuple[dict, dict]:
    v7_bytes = (repo / ORACLE_V7).read_bytes()
    if sha(v7_bytes) != V7_SHA:
        raise SystemExit(f"oracle v7 is not byte-identical to the frozen proposal (sha256 {sha(v7_bytes)})")
    v7 = json.loads(v7_bytes)
    b1, b2 = load(repo / FR_B1), load(repo / FR_B2_ORACLE)
    b1_rows = {r["id"]: r for r in b1["rows"]}
    b2_rows = {r["id"]: r for r in b2["rows"]}
    order = []
    for r in v7["rows"]:
        if r["id"] == "NC4-03":
            order += [b2_rows["NC4-03"]] + [b2_rows[i] for i in ("NC4-03a", "NC4-03b", "NC4-03c", "NC4-03d")]
        else:
            order.append(r)
        if r["id"] == "NC2-06":
            order.append(b1_rows["NC2-07"])
        if r["id"] == "NC3-03":
            order.append(b1_rows["NC3-04"])
    rows = order
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate row id"
    v7_by = {r["id"]: r for r in v7["rows"]}
    v8_by = {r["id"]: r for r in rows}
    identical = [i for i in v7_by if v8_by.get(i) == v7_by[i]]
    changed = [i for i in v7_by if i in v8_by and v8_by[i] != v7_by[i]]
    dropped = [i for i in v7_by if i not in v8_by]
    added = [i for i in v8_by if i not in v7_by]
    assert not dropped, dropped
    assert changed == ["NC4-03"], changed
    # no placeholder rows, no empty predicate lists
    for r in rows:
        assert r.get("all") or r.get("any_of"), f"{r['id']}: row without predicates"
        assert "placeholder" not in json.dumps(r).lower() or r["id"] == "NC4-03", f"{r['id']}: placeholder text"
    c7, c8 = counts_of(v7["rows"]), counts_of(rows)
    new_limits = dict(v7["limitations"])
    new_limits["os_level_process_kill"] = (
        "QUALIFIED FOR PROCESS DEATH (SIGKILL) AT THREE SEAMS ONLY, by the mandatory row NC2-07 (architect ruling A1, replacing the v7 wording 'UNQUALIFIED'): a real "
        "subprocess is killed with SIGKILL by the harness at each of three deterministic seams of the pinned route B executor (after_begin; after_effect_insert_before_commit, "
        "inside the open write transaction; after_commit, no acknowledgement can reach the caller), and an independent fresh process observes the persisted state. The row "
        "records the pinned code's own contract: before COMMIT nothing is durable and the claim is still issued (nothing recovers automatically; a new presentation executes "
        "exactly once); after COMMIT exactly one durable effect, consumed claim, reconcile reports applied, re-presentation is denied. The claim must not promise recovery of "
        "the lost acknowledgement or automatic retry. The synthetic fault injection used by NC2-01..06, ruling 4 and NC6-02/03 stays supplementary and does not support any "
        "wording about recovery after actual process death. STILL UNQUALIFIED: power loss, OS crash, filesystem fault, kill during claim provisioning, kill of the Control "
        "Plane process, kill during Replay/Evidence Pack/Verifier steps.")
    new_limits["nc4_03_not_covered_not_claimed"] = v7["limitations"]["nc4_03_not_covered_not_claimed"] + (
        " v8 addendum (architect A3/A4, D3): items (2) and (3) above are no longer wholly uncovered by the oracle: the host-dependent subcases NC4-03a (Yama), NC4-03b (uid "
        "separation), NC4-03c (IPC directory 2751, socket 0660) and NC4-03d (peer-UID allowlist) are separately identified mandatory rows on the ratified bounded profile; "
        "they are BLOCKED, never PASS, without that profile, and never alter the deterministic NC4-03 verdict. Items (1), (4) and (5) are unchanged and still NOT claimed.")
    new_limits["ledger_pruning_documented_limitation"] = (
        "NC3-04 (architect ruling A2) preserves the documented limitation instead of closing it: the Control Plane has no retention rule and neither detects nor prevents "
        "pruning of its operation ledger (a pruned ledger makes the decision for a renewed revision 'authorized' where the intact ledger holds it; recorded, not judged). The "
        "ONLY barrier shown is the destination-side operation guard, which refuses the second effect (operation_already_committed). If the destination ledger is also lost "
        "nothing in the pinned code prevents a second effect (observed in a negative control of the supplementary test, not a row predicate). The row is not NC3-03 by "
        "substitution.")
    new_limits["ipc_profile_2751_bounded_synthetic_only"] = (
        "Architect ruling D3: IPC directory mode 2751, socket 0660 and the peer-UID allowlist are the BOUNDED SYNTHETIC qualification configuration only, not a production "
        "adoption. Accepted residual: an outsider can stat a known socket name; no directory listing, connect or state-content disclosure is authorized or claimed. The "
        "original 2750 evidence stays preserved. If later evidence contradicts this confinement the test profile reverts to 2750 and the socket-level outsider control is "
        "BLOCKED.")
    new_limits["composed_chain_claim_wording_q14"] = (
        "Architect ruling Q14 (equivalence accepted for this MVP): the permitted claim is 'The frozen pinned classes compose end-to-end in the qualification harness, while "
        "the trusted ingress boundary is separately exercised on the real socket under the same frozen candidate.' PROHIBITED: 'A live socket request produced the "
        "reconstructed Replay, Evidence Pack, and Verifier evidence.' No row of this oracle observes a live socket request producing Replay, Evidence Pack or Verifier "
        "evidence, and none may be cited for it. No live-ingress capture seam exists or is required.")
    reasons = {
        "NC2-07": f"Architect disposition {DISPOSITION}, A1: a REAL OS-level process kill is a MANDATORY row; synthetic fault injection stays supplementary and must not support wording that promises recovery after actual process death. New row; predicates are observations of a real SIGKILL (returncode -9, process gone) and of the persisted destination state read by a fresh process, per the pinned executor contract (Runtime c5e97e87). Source: suites/mvp-chain/v8_rows_b1.fragment.json (worker B1).",
        "NC3-04": f"Architect disposition {DISPOSITION}, A2: a DEDICATED mandatory oracle row for operation-ledger pruning, not NC3-03 by substitution, existing harness machinery reused (_chain.Ctx), documented pruning limitation preserved and not overclaimed. New row. Source: suites/mvp-chain/v8_rows_b1.fragment.json (worker B1).",
        "NC4-03": f"Architect disposition {DISPOSITION}, A3/A4: the empty NC4-03 placeholder is eliminated and a frozen, deterministic, versioned mutation set (nc4_03_mutation_set.v1: 57 mutations, 11 negative controls; each with exact input, operation, expected rejection, environment, evidence source and deterministic verdict predicate) becomes part of the row. CHANGED row: all 12 v7 predicates are retained with identical operators and values (only the observation prefix {OLD_PREFIX} -> {NEW_PREFIX}, so that a blocked host scenario can no longer make the deterministic verdict ambiguous, A4), 10 predicates are added. Nothing is weakened.",
        "NC4-03a..d": f"Architect disposition {DISPOSITION}, A3/A4 with D3: host-dependent predicates (Yama, uid separation, IPC 2751/0660 profile, peer-UID allowlist) are explicit, separately identified mandatory subcases on the ratified bounded 2751 profile, run on a separate scenario (nc4_03_host); BLOCKED, never PASS, when the profile is unavailable; they cannot change the deterministic NC4-03 verdict. New rows.",
        "Q14": f"Architect disposition {DISPOSITION}, Q14: no oracle row is added or changed for it by design (no live-ingress capture seam; no production interface change). It governs claim wording only and is recorded in limitations.composed_chain_claim_wording_q14. The existing chain rows (CHAIN-*, VER-*) remain the in-process exact-pin composed chain; NC4-01..04 and NC2-06 remain the separate real-socket ingress controls; both are bound to the same frozen tuple and commitment.",
        "D3": f"Architect disposition {DISPOSITION}, D3: recorded in limitations.ipc_profile_2751_bounded_synthetic_only and enforced in the NC4-03c row and the environment profile v2; no production adoption.",
        "A5": "Not asserted by this file: whether NC4-03d satisfies a separate A5 'non-allowlisted group member' row is the Qualification Owner's call (worker B2 handoff).",
    }
    true_diff = {
        "vs": "expectations.proposed.v7.json",
        "v7_sha256": V7_SHA,
        "rows_v7": c7["oracle_rows"], "rows_v8": c8["oracle_rows"],
        "rows_added": added,
        "rows_changed": changed,
        "rows_removed": dropped,
        "rows_byte_identical_to_v7": identical,
        "row_count_byte_identical_to_v7": len(identical),
        "non_row_fields_changed": ["status", "supersedes", "inventory_vs_claims", "limitations.os_level_process_kill", "limitations.nc4_03_not_covered_not_claimed"],
        "non_row_fields_added": ["limitations.ledger_pruning_documented_limitation", "limitations.ipc_profile_2751_bounded_synthetic_only",
                                 "limitations.composed_chain_claim_wording_q14", "limitations.changelog_2026_10_31_qgate05"],
        "non_row_fields_unchanged": "schema, statuses, semantics, operators and every other limitations entry (incl. result_layers and changelog_2026_10_24_review_fixes) are identical to v7",
        "nc4_03_v7_predicates_retained": 12, "nc4_03_predicates_added": len(v8_by["NC4-03"]["all"]) - 12,
        "counts_v7": c7, "counts_v8": c8,
    }
    changelog = {
        "note": "Changes made by the QGATE-05 metadata repair, after the architect disposition. Additions and replacement of one stale limitation text only; no retained row was loosened and no historical result was rewritten. v1..v7 are untouched.",
        "disposition": DISPOSITION,
        "v7_wording_correction": "v7's own status text and its supersedes.unchanged_rows field say v7 is v6 byte-identical plus NC7-01..03. That is inaccurate, and v7 itself is not edited (its hash is pinned): relative to v6, v7 ADDED NC4-04 and NC7-01..03 and CHANGED NC4-03 (launch.py added to files_scanned; ingress_tree_sha256 ea37100d -> 0c0e2cf6), so v7 has 42 rows, not 41. This v8 text states the true diff against v7 (supersedes.true_diff_vs_v7), computed by script from the files.",
        "nc4_03_row_change": f"NC4-03 is the only v7 row that is not byte-identical in v8. All 12 v7 predicates are present with identical op/value; their observation names differ only by the prefix {OLD_PREFIX} -> {NEW_PREFIX}. The v7 title is extended (not shortened) by the mutation-set sentence.",
        "reasons_per_row": reasons,
    }
    status = (f"PROPOSED oracle v8 (builder proposal for the MVP battery) for Qualification's independent review, acceptance and freeze. v8 = v7 ({V7_SHA}, byte-identical, unedited) "
              f"with: {len(added)} NEW rows ({', '.join(added)}); 1 CHANGED row ({', '.join(changed)}: all 12 v7 predicates retained, 10 predicates added, observation prefix moved to the deterministic "
              f"scenario nc4_03_det); {len(identical)} of v7's {c7['oracle_rows']} rows byte-identical; 0 rows removed; two limitation texts replaced and four limitation entries added (see supersedes.true_diff_vs_v7). "
              f"Rows: {c8['oracle_rows']} ({c8['mandatory_rows']} mandatory, KL-01 non-mandatory). It implements architect disposition {DISPOSITION} (A1, A2, A3/A4, D3, Q14). "
              "NOT frozen; builder-prepared, Qualification owns every verdict; non-authorizing; release and production stay HOLD. Never edit after seeing results: a change is a new file with a recorded reason. "
              "(v7's description 'v6 byte-identical plus NC7-01..03' was inaccurate; see changelog_2026_10_31_qgate05.v7_wording_correction.)")
    v8 = {"schema": v7["schema"], "statuses": v7["statuses"], "semantics": v7["semantics"], "operators": v7["operators"], "status": status,
          "supersedes": {"file": "expectations.proposed.v7.json", "v7_sha256": V7_SHA,
                         "composition": {"base": f"expectations.proposed.v7.json ({c7['oracle_rows']} rows, {c7['mandatory_rows']} mandatory)",
                                         "added": added, "changed": changed,
                                         "row_count": f"{c8['oracle_rows']} rows, {c8['mandatory_rows']} mandatory (KL-01 remains non-mandatory); v8 = v7 + {', '.join(added)}; {', '.join(changed)} changed"},
                         "reasons": reasons,
                         "unchanged_rows": f"{len(identical)} rows of v7 are byte-identical in v8: {', '.join(identical)}. The only v7 row that differs is NC4-03 (retained predicates + additions); no v7 row was removed.",
                         "true_diff_vs_v7": true_diff},
          "rows": rows, "limitations": new_limits,
          "inventory_vs_claims": {
              "unique_governance_claims": f"mandatory oracle rows: {c8['mandatory_rows']} in v8 ({c7['mandatory_rows']} in v7). Each row is one claim.",
              "test_inventory": "the acceptance battery lists more test entries than claims: supplementary entries (KW-001..183 and NM-001..122 substantiate NC4-03 and NC4-03a..d; KILL-01..18 substantiate NC2-07; PRUNE-01..08 substantiate NC3-04; AMB-01..06 substantiate NC2-06; the route-B mediation entries map existing mvp-d2-route-b tests) are inventory, not additional claims. Inventory counts must not be cited as governance coverage; battery v2 states its own entry counts."},
          }
    for k in ("changelog_2026_10_24_review_fixes", "result_layers"):
        assert k in v7["limitations"], k  # they live inside limitations in v7 and are carried over unchanged
    v8["limitations"]["changelog_2026_10_31_qgate05"] = changelog
    changed_keys = [k for k in v7["limitations"] if v8["limitations"][k] != v7["limitations"][k]]
    added_keys = [k for k in v8["limitations"] if k not in v7["limitations"]]
    assert sorted(changed_keys) == ["nc4_03_not_covered_not_claimed", "os_level_process_kill"], changed_keys
    assert sorted(added_keys) == sorted(k.split(".", 1)[1] for k in true_diff["non_row_fields_added"]), added_keys
    for k in ("schema", "statuses", "semantics", "operators"):
        assert v8[k] == v7[k]
    proofs = {"v7_rows_identical": identical, "changed": changed, "added": added, "counts_v7": c7, "counts_v8": c8}
    return v8, proofs


def prove_no_weakening(repo: Path, v8: dict) -> list[str]:
    """Raise AssertionError on any weakening; return human-readable proof lines."""
    v7 = load(repo / ORACLE_V7)
    v7_by = {r["id"]: r for r in v7["rows"]}
    v8_by = {r["id"]: r for r in v8["rows"]}
    out = []
    n = 0
    for i, r in v7_by.items():
        if i == "NC4-03":
            continue
        assert json.dumps(v8_by[i], sort_keys=True) == json.dumps(r, sort_keys=True), f"retained row {i} differs"
        n += 1
    out.append(f"{n} retained v7 rows (all but NC4-03) are byte-identical (canonical JSON) in v8")
    old, new = v7_by["NC4-03"], v8_by["NC4-03"]
    assert old["mandatory"] is True and new["mandatory"] is True
    assert set(old) == set(new) == {"id", "mandatory", "title", "scenario", "all"}, "NC4-03 gained blocked_if/not_applicable_if (would weaken)"
    body = old["title"].split(": ", 1)[1]  # the v7 title after its "SOURCE-LEVEL assertion only (...)" lead-in
    assert body in new["title"], "the v7 title text is not retained in the v8 NC4-03 title"
    new_preds = [json.dumps(p, sort_keys=True) for p in new["all"]]
    for p in old["all"]:
        q = dict(p)
        if q["obs"].startswith(OLD_PREFIX):
            q["obs"] = NEW_PREFIX + q["obs"][len(OLD_PREFIX):]
        assert json.dumps(q, sort_keys=True) in new_preds, f"NC4-03 v7 predicate lost or weakened: {p}"
    out.append(f"NC4-03: all {len(old['all'])} v7 predicates retained with identical op/value (obs prefix {OLD_PREFIX} -> {NEW_PREFIX} only); {len(new['all']) - len(old['all'])} predicates added; no blocked_if/not_applicable_if; mandatory stays true")
    for r in v8["rows"]:
        assert r["mandatory"] is True or r["id"] == "KL-01", r["id"]
        assert r.get("all"), f"{r['id']}: no predicates"
    out.append("every v8 row except KL-01 is mandatory and has a non-empty predicate list; no placeholder rows")
    return out


def build_battery(repo: Path, v8_bytes: bytes, node_names: dict[str, list[str]], oracle_proofs: dict) -> dict:
    v1_bytes = (repo / BATTERY_V1).read_bytes()
    if sha(v1_bytes) != V1_BATTERY_SHA:
        raise SystemExit("battery v1 is not byte-identical to the proposal")
    v1 = json.loads(v1_bytes)
    b2 = load(repo / FR_B2_BATTERY)
    v8 = json.loads(v8_bytes)
    mandatory_ids = [r["id"] for r in v8["rows"] if r["mandatory"]]
    tests = list(v1["tests"])
    existing = {t["id"] for t in tests}
    # oracle rows: one entry per mandatory v8 row, in oracle order
    oracle_entries = {t["row"]: t for t in tests if t["kind"] == "oracle_row"}
    new_oracle = []
    for rid in ("NC2-07", "NC3-04", "NC4-03a", "NC4-03b", "NC4-03c", "NC4-03d"):
        e = {"id": rid, "kind": "oracle_row", "invocation": "mvp-chain", "file": "suites/mvp-chain/test_mvp_chain.py", "test": f"test_row[{rid}]", "row": rid}
        new_oracle.append(e)
    b2_oracle = {t["row"]: t for t in b2["tests_added"] if t["kind"] == "oracle_row"}
    for e in new_oracle:
        if e["row"] in b2_oracle:
            assert b2_oracle[e["row"]] == e, e
    order = []
    inserted = {"NC2-06": ["NC2-07"], "NC3-03": ["NC3-04"], "NC4-03": ["NC4-03a", "NC4-03b", "NC4-03c", "NC4-03d"]}
    for t in tests:
        order.append(t)
        if t["kind"] == "oracle_row" and t["row"] in inserted:
            order += [e for e in new_oracle if e["row"] in inserted[t["row"]]]
    tests = order
    kill = [{"id": f"KILL-{i + 1:02d}", "kind": "supplementary_nc2_07_process_kill", "invocation": "mvp-chain", "file": TEST_FILES["kill"], "test": n}
            for i, n in enumerate(node_names["kill"])]
    prune = [{"id": f"PRUNE-{i + 1:02d}", "kind": "supplementary_nc3_04_ledger_pruning", "invocation": "mvp-chain", "file": TEST_FILES["prune"], "test": n}
             for i, n in enumerate(node_names["prune"])]
    nm_frag = [t for t in b2["tests_added"] if t["kind"].startswith("supplementary_")]
    nm_names = {(t["file"], t["test"]) for t in nm_frag}
    live = {("suites/mvp-chain/test_nc4_03_mutation_set.py", n) for n in node_names["mut"]} | {("suites/mvp-chain/test_nc4_03_host_subcases.py", n) for n in node_names["host"]}
    assert nm_names == live, f"B2 battery fragment entries differ from the collected tests: {sorted(nm_names ^ live)[:5]}"
    tests += kill + prune + nm_frag
    ids = [t["id"] for t in tests]
    assert len(ids) == len(set(ids)), "duplicate battery id"
    keys = [(t["file"], t["test"]) for t in tests]
    assert len(keys) == len(set(keys)), "duplicate battery test"
    assert [t["row"] for t in tests if t["kind"] == "oracle_row"] and set(t["row"] for t in tests if t["kind"] == "oracle_row") == set(mandatory_ids), "battery oracle_row entries != mandatory v8 rows"
    inv = json.loads(json.dumps(v1["invocations"]))
    paths = inv["mvp-chain"]["paths"]
    for p in NEW_INVOCATION_PATHS:
        if p not in paths:
            paths.append(p)
    kinds = Counter(t["kind"] for t in tests)
    unchanged = dict(v1["oracle"]["unchanged_files_sha256"])
    unchanged[ORACLE_V8] = sha(v8_bytes)
    c8 = oracle_proofs["counts_v8"]
    battery = {
        "schema": v1["schema"],
        "status": (f"PROPOSED battery v2 for Qualification freeze (Architect ruling 7); supersedes mandatory-battery.proposed.v1.json (sha256 {V1_BATTERY_SHA}, unedited). Not frozen, not selected, not an acceptance. "
                   f"v2 = v1 with: the oracle in force moved from v7 to v8; {len(new_oracle)} oracle_row entries added (NC2-07, NC3-04, NC4-03a..d); {len(kill)} supplementary NC2-07 entries, {len(prune)} supplementary NC3-04 entries and "
                   f"{len(nm_frag)} supplementary NC4-03 mutation-set/host-subcase entries added; the four new test modules appended to the mvp-chain invocation; pending_rows emptied (the NC4-03 placeholder is removed). "
                   "Qualification owns this list, the oracle and every verdict; the builder proposes."),
        "supersedes": {"file": "mandatory-battery.proposed.v1.json", "v1_sha256": V1_BATTERY_SHA,
                       "reason": f"Architect disposition {DISPOSITION}: A1 (real kill row), A2 (pruning row), A3/A4 (NC4-03 mutation set; no placeholder), Q14 (wording only)."},
        "rule": v1["rule"], "verdict_precedence": v1["verdict_precedence"],
        "oracle": {"expectations_in_force": ORACLE_V8, "expectations_in_force_sha256": sha(v8_bytes), "unchanged_files_sha256": unchanged,
                   "note": "v8 is listed with its sha256 together with the earlier files; the gate refuses a different hash for any of them. v7 stays byte-identical and listed. " + v1["oracle"]["note"]},
        "invocations": inv, "declared_not_applicable": v1["declared_not_applicable"], "excluded_components_not_in_battery": v1["excluded_components_not_in_battery"],
        "tests": tests, "non_mandatory_tests": v1["non_mandatory_tests"], "pending_rows": [],
        "supplementary_entries": {
            "note": v1["supplementary_entries"]["note"] + (
                " v2 adds: supplementary_nc2_07_process_kill (KILL-01..18, suites/mvp-chain/test_process_kill_a1.py: the real SIGKILL harness checks, per-seam predicates and five negative controls); "
                "supplementary_nc3_04_ledger_pruning (PRUNE-01..08, test_ledger_pruning_a2.py); supplementary_nc4_03_mutation_set (NM-001..114, test_nc4_03_mutation_set.py: one test per frozen mutation or control plus structure checks) and "
                "supplementary_nc4_03_host_subcases (NM-115..122, test_nc4_03_host_subcases.py). The 183 KW entries still self-test the NC4-03 predicate and are not replaced."),
            "counts": dict(sorted(kinds.items())),
        },
        "inventory_vs_claims": {
            "statement": ("The inventory is not coverage. The battery lists %d mandatory entries; only the %d oracle_row entries are governance claims (one per mandatory oracle row of v8). "
                          "The other %d entries are supplementary tests: they substantiate, self-test or add negative controls to a claim, and do not add claims. Passing them does not widen what any row proves." %
                          (len(tests), kinds["oracle_row"], len(tests) - kinds["oracle_row"])),
            "unique_governance_claims": c8["mandatory_rows"],
            "non_mandatory_tests": len(v1["non_mandatory_tests"]),
        },
        "counts": {"oracle_rows": c8["oracle_rows"], "mandatory_rows": c8["mandatory_rows"], "non_mandatory_oracle_rows": c8["non_mandatory_rows"],
                   "mandatory_nc_rows": c8["mandatory_nc_rows"], "negative_groups": c8["negative_groups"], "mandatory_nc_rows_per_group": c8["mandatory_nc_rows_per_group"],
                   "battery_entries": len(tests), "battery_entries_by_kind": dict(sorted(kinds.items())), "unique_claims": c8["mandatory_rows"],
                   "non_mandatory_tests": len(v1["non_mandatory_tests"]), "pending_rows": 0, "pytest_nodes_new_modules": {k: len(v) for k, v in node_names.items()}},
    }
    return battery


def node_names_from_collection(text: str) -> dict[str, list[str]]:
    out = {"kill": [], "prune": [], "mut": [], "host": []}
    key = {"test_process_kill_a1.py": "kill", "test_ledger_pruning_a2.py": "prune", "test_nc4_03_mutation_set.py": "mut", "test_nc4_03_host_subcases.py": "host"}
    for line in text.splitlines():
        m = re.match(r"suites/mvp-chain/(test_\w+\.py)::(.+)$", line.strip())
        if m and m.group(1) in key:
            out[key[m.group(1)]].append(m.group(2))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--collection", help="file with `pytest --collect-only -q` output of the four new test modules (required for --write)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    ap.add_argument("--report", help="write a JSON report of the proofs and counts here")
    a = ap.parse_args()
    repo = Path(a.repo_root)
    v8, proofs = build_oracle(repo)
    lines = prove_no_weakening(repo, v8)
    v8_bytes = dump(v8)
    if a.check or not a.collection:
        old = load(repo / BATTERY_V2)
        nodes = {"kill": [], "prune": [], "mut": [], "host": []}
        for t in old["tests"]:
            for k, f in (("kill", "test_process_kill_a1.py"), ("prune", "test_ledger_pruning_a2.py"), ("mut", "test_nc4_03_mutation_set.py"), ("host", "test_nc4_03_host_subcases.py")):
                if t["file"].endswith(f):
                    nodes[k].append(t["test"])
        # order inside the new modules is the collection order (supplementary NM entries keep the fragment order)
        nodes["mut"] = [t["test"] for t in old["tests"] if t["file"].endswith("test_nc4_03_mutation_set.py")]
        nodes["host"] = [t["test"] for t in old["tests"] if t["file"].endswith("test_nc4_03_host_subcases.py")]
    else:
        nodes = node_names_from_collection(Path(a.collection).read_text())
    battery = build_battery(repo, v8_bytes, nodes, proofs)
    b_bytes = dump(battery)
    if a.write:
        (repo / ORACLE_V8).write_bytes(v8_bytes)
        (repo / BATTERY_V2).write_bytes(b_bytes)
    else:
        ok = (repo / ORACLE_V8).read_bytes() == v8_bytes and (repo / BATTERY_V2).read_bytes() == b_bytes
        print("CHECK", "OK" if ok else "FAIL", "(committed v8/v2 are byte-identical to the rebuild)" if ok else "(committed v8/v2 differ from the rebuild)")
        if not ok:
            return 1
    if sha(repo / ORACLE_V7) != V7_SHA or sha(repo / BATTERY_V1) != V1_BATTERY_SHA:
        print("v7 or battery v1 changed", file=sys.stderr)
        return 2
    report = {"oracle_v8_sha256": sha(v8_bytes), "battery_v2_sha256": sha(b_bytes), "oracle_v7_sha256": sha(repo / ORACLE_V7), "battery_v1_sha256": sha(repo / BATTERY_V1),
              "no_weakening_proofs": lines, "counts": battery["counts"], "true_diff_vs_v7": v8["supersedes"]["true_diff_vs_v7"]}
    print(json.dumps({k: report[k] for k in ("oracle_v8_sha256", "battery_v2_sha256", "oracle_v7_sha256", "battery_v1_sha256", "no_weakening_proofs", "counts")}, indent=1))
    if a.report:
        Path(a.report).write_text(json.dumps(report, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
