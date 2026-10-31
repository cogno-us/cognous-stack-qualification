"""Builds the oracle-v8 and battery-v2 FRAGMENTS for NC4-03 (authoring tool; the JSON files are the artifacts).

SPDX-License-Identifier: Apache-2.0
Run: ``MVP_HUB_DIR=<hub> /usr/bin/python3.13 _nc4_03_v8_fragment_derive.py oracle > nc4_03_oracle_v8_fragment.proposed.json`` (battery: argument ``battery``, needs the collected node ids on stdin as JSON).
"""
import copy
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _nc4_03_mutations as M  # noqa: E402

V7 = json.loads((HERE.parents[1] / "process" / "mvp-chain" / "expectations.proposed.v7.json").read_text())
OLD, NEW = "nc_unmediated.source_level.", "nc4_03_det.source_level."
HOSTS = {"NC4-03a": ("Yama", "kernel.yama.ptrace_scope >= 1 on the execution host (absent or 0: profile unsupported, BLOCKED)"),
         "NC4-03b": ("uid separation", "dedicated non-root ingress uid, a distinct unprivileged client uid and outsider uid 65533, distinct primary groups, no capabilities"),
         "NC4-03c": ("IPC 2751 socket profile", "IPC directory 2751 / socket 0660 / dedicated group: the outsider can only stat the known socket name (accepted residual) and cannot list or connect; the group-member client connects"),
         "NC4-03d": ("peer-UID allowlist", "pinned server.serve against a stub core: the allowlisted client is served, a non-allowlisted socket-group member gets PEER_NOT_ALLOWED, an empty allowlist is refused")}


def oracle_fragment():
    doc = M.load_set()
    v7 = next(r for r in V7["rows"] if r["id"] == "NC4-03")
    row = copy.deepcopy(v7)
    row["scenario"] = "nc4_03_det"
    row["title"] = ("DETERMINISTIC SOURCE-LEVEL assertion (host-independent; not an execution observation): " + v7["title"].split("SOURCE-LEVEL assertion only (not an execution observation): ", 1)[1]
                    + "; AND the frozen versioned mutation set nc4_03_mutation_set.v1 (57 mutations in 6 families, each with exact input, operation, expected rejection, environment, evidence source and predicate) "
                      "is rejected as expected on a copy of the pinned hub source while its 11 negative controls (no-op and benign edits) are accepted and satisfy no rejection predicate. "
                      "Host-dependent subcases are the separate rows NC4-03a..d and cannot alter this verdict")
    row["all"] = [dict(p, obs=p["obs"].replace(OLD, NEW, 1)) for p in v7["all"]]
    ms = "nc4_03_det.mutation_set."
    row["all"] += [
        {"obs": ms + "set_version", "op": "eq", "value": doc["version"]},
        {"obs": ms + "set_file_sha256", "op": "eq", "value": M.set_file_sha256()},
        {"obs": ms + "verdict", "op": "eq", "value": "PASS"},
        {"obs": ms + "mutations_total", "op": "eq", "value": len(doc["mutations"])},
        {"obs": ms + "mutations_rejected", "op": "eq", "value": len(doc["mutations"])},
        {"obs": ms + "mutations_not_rejected", "op": "empty"},
        {"obs": ms + "controls_total", "op": "eq", "value": len(doc["controls"])},
        {"obs": ms + "controls_accepted", "op": "eq", "value": len(doc["controls"])},
        {"obs": ms + "controls_falsely_rejected", "op": "empty"},
        {"obs": "nc4_03_det.mutation_set_control_guard", "op": "empty"},
    ]
    rows = [row]
    for sid, (name, what) in HOSTS.items():
        rows.append({"id": sid, "mandatory": True, "scenario": "nc4_03_host",
                     "title": f"HOST-DEPENDENT subcase of NC4-03 ({name}), executed on the ratified bounded 2751 test profile (D3; not production): {what}. BLOCKED when the profile is unavailable; "
                              "never changes, converts or obscures the deterministic NC4-03 verdict",
                     "blocked_if": [{"obs": f"nc4_03_host.{sid}.status", "op": "eq", "value": "BLOCKED"}],
                     "all": [{"obs": f"nc4_03_host.{sid}.status", "op": "eq", "value": "PASS"}]})
    return {
        "schema": "cognous.mvp-chain-expectations-fragment/1",
        "status": "PROPOSED fragment for oracle v8 (Worker B2, OCS-MVP-QGATE-05). Not a complete oracle: apply on top of expectations.proposed.v7.json (byte-identical elsewhere; v7 is never edited). Qualification owns and freezes v8.",
        "reasons": {"NC4-03": "Architect A3/A4: the empty NC4-03 placeholder is eliminated. The row keeps every v7 predicate unchanged (only the observation prefix moves from nc_unmediated.source_level to nc4_03_det.source_level, so a blocked host "
                              "scenario no longer blocks it, per A4) and ADDS the frozen mutation-set predicates. Nothing is weakened.",
                    "NC4-03a..d": "Architect A3/A4 + D3: host-dependent predicates become separately identified mandatory rows on a separate scenario, BLOCKED (never PASS/FAIL-converted) without the ratified profile."},
        "requires_harness": ["scenario nc4_03_det: _nc4_03_mutations.scenario_observation(hub_dir, hub_head)", "scenario nc4_03_host: _nc4_03_host.scenario_observation(hub_dir)"],
        "counts": {"v7_rows": 42, "v7_mandatory": 41, "rows_added": 4, "rows_changed": 1, "v8_rows_from_this_fragment_alone": 46, "v8_mandatory_from_this_fragment_alone": 45},
        "rows": rows}


def battery_fragment(nodes):
    """nodes: {"mutation_set": [node ids of test_nc4_03_mutation_set.py], "host": [node ids of test_nc4_03_host_subcases.py]} (names after the file::)."""
    tests = [{"id": sid, "kind": "oracle_row", "invocation": "mvp-chain", "file": "suites/mvp-chain/test_mvp_chain.py", "test": f"test_row[{sid}]", "row": sid} for sid in HOSTS]
    n = 0
    for fname, key, kind in (("test_nc4_03_mutation_set.py", "mutation_set", "supplementary_nc4_03_mutation_set"), ("test_nc4_03_host_subcases.py", "host", "supplementary_nc4_03_host_subcases")):
        for node in nodes[key]:
            n += 1
            tests.append({"id": f"NM-{n:03d}", "kind": kind, "invocation": "mvp-chain", "file": f"suites/mvp-chain/{fname}", "test": node})
    return {
        "schema": "cognous.mvp-mandatory-battery-fragment/1",
        "status": "PROPOSED fragment for battery v2 (Worker B2). Apply on top of mandatory-battery.proposed.v1.json (v1 is never edited).",
        "pending_rows": [],
        "remove": "pending_rows[0] (placeholder NC4-03-origin-rule-negative-mutations, rows: []) is deleted; battery v2 carries pending_rows: [] (G-14 passes: no placeholder remains)",
        "oracle": {"expectations_in_force": "process/mvp-chain/expectations.proposed.v8.json (NC4-03 changed, NC4-03a..d added, per nc4_03_oracle_v8_fragment.proposed.json)"},
        "invocations_mvp_chain_paths_add": ["suites/mvp-chain/test_nc4_03_mutation_set.py", "suites/mvp-chain/test_nc4_03_host_subcases.py"],
        "unchanged": "the 183 supplementary_nc4_03_predicate entries KW-001..KW-183 (test_kwflow.py) and NC4-03's oracle_row entry test_row[NC4-03] stay as in v1",
        "tests_added": tests,
        "counts": {"oracle_row_entries_added": len(HOSTS), "supplementary_entries_added": len(tests) - len(HOSTS), "tests_added_total": len(tests), "pending_rows_before": 1, "pending_rows_after": 0}}


if __name__ == "__main__":
    if sys.argv[1] == "oracle":
        print(json.dumps(oracle_fragment(), indent=1))
    else:
        print(json.dumps(battery_fragment(json.load(sys.stdin)), indent=1))
