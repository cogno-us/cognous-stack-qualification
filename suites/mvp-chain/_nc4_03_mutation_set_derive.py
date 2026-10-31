"""Derivation record of nc4_03_mutation_set.v1.json (authoring tool, NOT part of any verdict).

SPDX-License-Identifier: Apache-2.0

The frozen data file is the artifact; this script documents how it was produced from the existing supplementary self-test tables
(``test_kwflow.MUTANTS`` / ``test_kwflow.V5_MUTANTS``, the 183 ``supplementary_nc4_03_predicate`` battery entries) and from the tree
operations of ``test_kwflow``. It is read only by ``test_nc4_03_mutation_set.py::test_frozen_set_matches_its_derivation`` (anti-drift).
Run: ``MVP_HUB_DIR=<pinned hub> /usr/bin/python3.13 _nc4_03_mutation_set_derive.py > nc4_03_mutation_set.v1.json`` (prints the JSON).
PROPOSED; Qualification owns and freezes the set.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

SET_VERSION = "v1"
INGRESS = "tools/mvp_ingress"
STAMP = "benign-control"

# family GENERIC-FORWARD (added pre-freeze, QGATE-05 Reviewer finding F-05): the generic ** / keyword / positional-unpack rules of the predicate that the origin-rule families above do not
# exercise. Each label is a test_kwflow.MUTANTS entry that carries no explicit rule there (the rule is set here from the scan, rebased) or one of the EXTRA edits below.
# "UNRESOLVED" is not a rule id of _kwflow: it is the sentinel that names_of() returns for a callee that cannot be resolved statically (a call result, a dynamic getattr). The EXTRA
# edits drive the rules that fire ONLY through that sentinel (OPAQUE_POSITIONAL_UNPACK and ORIGIN_VIOLATION on an unresolved callee).
GENERIC_FAMILY = "GENERIC-FORWARD"
GENERIC_RULES = {
    "core: client simulate": "SIMULATE_NOT_CONSTANT_NONE",
    "core: **fields into execute": "NONLITERAL_KWARGS",
    "core: client kwargs into decide": "NONLITERAL_KWARGS",
    "core: update() with client fields": "NONLITERAL_KWARGS",
    "host: model_copy ** update from client": "MODEL_COPY_KWARGS_FORBIDDEN",
    "host: model_copy update from client mapping": "MODEL_COPY_UPDATE_NOT_FIXED",
    "core: comprehension over client fields into provision_claim": "COMPREHENSION_NOT_FIXED",
    "host: comprehension keys from non-literal iterable": "COMPREHENSION_NOT_FIXED",
    "core: import alias then client star-args": "OPAQUE_POSITIONAL_UNPACK",
}
_EXEC = "res = host.executor.execute(envelope=host.envelope(decision, proposal), claim_id=claim.claim_id, simulate=None)"
GENERIC_EXTRA = {  # label -> (file, old, new, rule)
    "U1 unresolved callee (call result) invoked with client star-args": ("core.py", _EXEC, 'make_runner(host)(*fields["a"])\n            ' + _EXEC, "OPAQUE_POSITIONAL_UNPACK"),
    "U2 unresolved callee (call result) with a client value for a six-field keyword": ("core.py", _EXEC, 'make_runner(host)(claim_id=fields["claim_id"])\n            ' + _EXEC, "ORIGIN_VIOLATION"),
    "U3 unresolved callee (dynamic getattr) with a client value for a six-field keyword": ("core.py", _EXEC, 'getattr(host.executor, fields["n"])(claim_id=fields["claim_id"])\n            ' + _EXEC, "ORIGIN_VIOLATION"),
}
# these edit INSIDE a pinned function, so the pinned AST digest legitimately no longer matches; only the source-aware rule must decide
GENERIC_DROP_PINS = {"host: model_copy update from client mapping", "host: comprehension keys from non-literal iterable"}
# family id -> (title, scan mode, [labels of test_kwflow.MUTANTS], [labels of test_kwflow.V5_MUTANTS])
FAMILIES = {
    "OR-FIELD": ("R1 origin rule: each of the six authority fields (claim_id, grant_id, grant_revision, effective_max_effects, authority_context_id, requested_permissions) "
                 "and the envelope caller must come from the trusted producer, never from a client value", "rebased",
                 ["core: CLIENT claim_id reaches execute (regression target)", "core: claim_id from client display", "core: claim name reassigned from client fields",
                  "host: client grant_id", "host: client grant_revision", "host: client effective_max_effects", "host: client authority_context_id",
                  "host: client requested_permissions", "core: envelope called with client-derived arguments"], []),
    "OR-BINDING": ("R1 origin rule, scoping and producer integrity: a producer or root name must be bound once, in the enclosing function, from the exact receiver of the real ingress "
                   "(F1 scope, F2 producer shadowing, F3 envelope escape, N5 host binding, import/match/except rebinding)", "rebased",
                   ["core: F1 claim bound in another function, used as parameter", "core: F1 claim rebound from client in another scope", "core: F2 module-level provision_claim shadow",
                    "core: F2 bare-name producer", "core: F2 producer on wrong receiver", "core: F2 decide shadowed by import", "core: F3 envelope alias",
                    "core: F3 envelope via getattr", "core: N5 host rebound from client fields", "core: N5 host as a parameter"],
                   ["E17 import-as rebinding of the claim name via match capture", "E17b import-as rebinding of the claim name", "E18 except-as rebinding of the claim name"]),
    "OR-LITERAL": ("v5 literal-only protected keywords: attempt_id, budget_id, expires_at, decision_input_commitment, decision_input_profile_version and now accept only constants "
                   "(now only host.now) at every protected call", "rebased",
                   [], ["E01 provision_claim budget_id from client", "E02 execute attempt_id from client", "E03 provision_claim expires_at from client",
                        "E04 provision_claim decision_input_commitment from client", "E04b provision_claim decision_input_profile_version from client", "E05 decide now from client",
                        "E16 dynamic callee with attempt_id", "E21 second execute call with attempt_id in a new method"]),
    "OR-OBJECT": ("v5 authority-object mutation and dynamic construction: no attribute store, setattr or object.__setattr__ on a non-self authority object, no model_validate / "
                  "__class__ proposal construction", "rebased",
                  [], ["E07 object.__setattr__ on claim", "E08 attribute store on decision.binding", "E09 setattr on proposal in _run", "E10 attribute store on p in build_proposal",
                       "E11 setattr on p in build_proposal", "E13 proposal built by model_validate", "E14 proposal built by __class__", "E19 helper function mutates the claim"]),
    "OR-FIXEDFORM": ("v5 fixed-form keys and positional values: RuntimeProposal keys in the fixed update display and positional values into ExecutionOperation / ExecutionEnvelope are constants "
                     "or trusted expressions only", "rebased",
                     [], ["E12 build_proposal update gains RuntimeProposal fields", "E12b build_proposal update gains tenant_id",
                          "E15 positional client value into ExecutionOperation in a new method", "E15b positional client value into ExecutionEnvelope"]),
    "GENERIC-FORWARD": ("v1 generic forwarding rules: a client-influenced simulate keyword, ** forwarding or dict update into a protected call, a ** into model_copy or a non-fixed update=, a dict "
                        "comprehension, an opaque positional * unpack, and a callee that cannot be resolved statically (call result, dynamic getattr) receiving client data", "rebased",
                        list(GENERIC_RULES) + list(GENERIC_EXTRA), []),
}
# family PIN: tree / pin integrity, evaluated WITHOUT rebasing (the fail-closed property is the thing under test)
PIN_FILES = ["__init__.py", "client.py", "core.py", "launch.py", "proposal.py", "server.py", "synthetic_host.py"]


# these edit INSIDE a pinned function (ExecutionOperation site in SyntheticHost.envelope), so the pinned AST digest legitimately no longer matches; the origin rule must still reject
DROP_PINS = lambda lab: lab.startswith("E15") or lab.startswith("host: client") or lab in GENERIC_DROP_PINS  # noqa: E731


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def build(hub: pathlib.Path) -> dict:
    import test_kwflow as T
    import _kwflow
    ing = hub / "tools" / "mvp_ingress"
    file_sha = {p.name: sha(p.read_bytes()) for p in sorted(ing.iterdir()) if p.is_file()}
    muts, controls, fams = [], [], []

    def rebased_predicate(rule, drop_pins=False):
        pred = [{"obs": "mutation_applied", "op": "true"}, {"obs": "violation_rules", "op": "contains", "value": rule}]
        if not drop_pins:
            pred.append({"obs": "pins_unmatched_count", "op": "eq", "value": 0})
        return pred

    env_rebased = {"interpreter": "CPython 3.13 (ast_digest pins are honoured on 3.13 only)", "host_dependent": False, "privileges": "none (no root, no uid change, no socket, no network, no /proc)",
                   "scan_mode": "rebased", "scan_mode_meaning": "pins and recursive digest re-based onto the mutated copy so ONLY the source-aware rule decides (a plain edit would otherwise be rejected merely by un-pinning)",
                   "input_copy": "temporary copy of MVP_HUB_DIR/tools/mvp_ingress; the pinned checkout is never written"}
    evidence = {"function": "suites/mvp-chain/_kwflow.py:scan_dir (predicate nc4-03.v5.strict-refinement-dataflow)", "derivation": "_nc4_03_mutations.observe_tree",
                "observations_used": ["violations[].rule", "pins_unmatched", "required_sites_missing", "pinned_sites_used"]}
    for fam, (title, mode, kw_labels, v5_labels) in FAMILIES.items():
        ids = []
        first_anchor = None
        for lab in kw_labels + v5_labels:
            if lab in GENERIC_EXTRA:
                src, (fname, old, new, *rule) = None, GENERIC_EXTRA[lab]
            else:
                src = T.MUTANTS if lab in T.MUTANTS else T.V5_MUTANTS
                fname, old, new, *rule = src[lab]
                if fam == GENERIC_FAMILY:
                    assert not rule, f"{lab}: carries its own rule in test_kwflow"
                    rule = [GENERIC_RULES[lab]]
            assert rule, f"{lab}: the frozen set needs an explicit rule"
            n = len(muts) + 1
            mid = f"M{n:03d}"
            ids.append(mid)
            first_anchor = first_anchor or (fname, old)
            muts.append({
                "id": mid, "family": fam, "title": lab,
                "input": {"tree": INGRESS, "files": {fname: file_sha[fname]}, "anchor": {"file": fname, "text": old, "occurrences": 1}},
                "operation": {"kind": "source_edit", "steps": [{"op": "replace", "file": fname, "old": old, "new": new, "count": 1}]},
                "expected": {"outcome": "REJECTED", "rules_all_of": [rule[0]], "pins_stay_matched": not DROP_PINS(lab)},
                "environment": dict(env_rebased), "evidence_source": dict(evidence),
                "predicate": rebased_predicate(rule[0], drop_pins=DROP_PINS(lab)),
                "provenance": {"supplementary_source": ("new in this set (not in a test_kwflow table); drives the UNRESOLVED-callee path" if src is None else
                                                        ("test_kwflow.MUTANTS" if src is T.MUTANTS else "test_kwflow.V5_MUTANTS") + f"[{lab!r}]"),
                               "supplementary_battery_entries": "KW-* (kind supplementary_nc4_03_predicate), unchanged and still collected"}})
        fname, old = first_anchor
        fams.append({"id": fam, "title": title, "scan_mode": mode, "mutations": ids, "controls": [f"C-{fam}-NOOP", f"C-{fam}-BENIGN"]})
        controls.append({
            "id": f"C-{fam}-NOOP", "family": fam, "title": "no-op mutation (replace the family's first anchor by itself): the predicate must NOT reject",
            "input": {"tree": INGRESS, "files": {fname: file_sha[fname]}, "anchor": {"file": fname, "text": old, "occurrences": 1}},
            "operation": {"kind": "source_edit", "steps": [{"op": "replace", "file": fname, "old": old, "new": old, "count": 1}]},
            "expected": {"outcome": "ACCEPTED", "rules_all_of": []}, "environment": dict(env_rebased), "evidence_source": dict(evidence),
            "predicate": [{"obs": "mutation_applied", "op": "true"}, {"obs": "violation_count", "op": "eq", "value": 0}, {"obs": "pins_unmatched_count", "op": "eq", "value": 0},
                          {"obs": "required_sites_missing", "op": "empty"}, {"obs": "pinned_sites_used_count", "op": "eq", "value": 3}]})
        controls.append({
            "id": f"C-{fam}-BENIGN", "family": fam, "title": "bytes-changing but AST-neutral edit (trailing comment on the family's target file): the predicate must NOT reject",
            "input": {"tree": INGRESS, "files": {fname: file_sha[fname]}, "anchor": {"file": fname, "text": None, "occurrences": None}},
            "operation": {"kind": "source_edit", "steps": [{"op": "append", "file": fname, "text": "\n# nc4-03 mutation-set control: comment only\n"}]},
            "expected": {"outcome": "ACCEPTED", "rules_all_of": []}, "environment": dict(env_rebased), "evidence_source": dict(evidence),
            "predicate": [{"obs": "mutation_applied", "op": "true"}, {"obs": "violation_count", "op": "eq", "value": 0}, {"obs": "pins_unmatched_count", "op": "eq", "value": 0},
                          {"obs": "required_sites_missing", "op": "empty"}, {"obs": "pinned_sites_used_count", "op": "eq", "value": 3}]})

    # ---- family PIN (pinned mode): fail-closed integrity of the reviewed tree and the three pin records
    env_pinned = dict(env_rebased, scan_mode="pinned", scan_mode_meaning="no re-basing: the reviewed tree digest and the three AST-digest pins are in force, so any byte or tree change must fail closed")
    pin_ids = []

    def add_pin(title, steps, files, pred, rules, prov, extra_expected=None):
        mid = f"M{len(muts) + 1:03d}"
        pin_ids.append(mid)
        fname = next(iter(files))
        muts.append({"id": mid, "family": "PIN", "title": title,
                     "input": {"tree": INGRESS, "files": {k: file_sha[k] for k in files}, "anchor": {"file": fname, "text": files[fname], "occurrences": 1 if files[fname] else None}},
                     "operation": {"kind": "tree_edit" if any(s["op"] in ("create_file", "create_dir", "symlink", "delete") for s in steps) else "source_edit", "steps": steps},
                     "expected": dict({"outcome": "REJECTED", "rules_all_of": rules}, **(extra_expected or {})), "environment": dict(env_pinned), "evidence_source": dict(evidence),
                     "predicate": pred, "provenance": {"supplementary_source": prov, "supplementary_battery_entries": "KW-* (kind supplementary_nc4_03_predicate), unchanged and still collected"}})

    for fname in PIN_FILES:
        add_pin(f"comment-only append to {fname} un-pins and fails closed", [{"op": "append", "file": fname, "text": "\n# comment-only edit\n"}], {fname: None},
                [{"obs": "mutation_applied", "op": "true"}, {"obs": "violation_rules", "op": "contains", "value": "INGRESS_TREE_DIGEST"},
                 {"obs": "pins_unmatched_count", "op": "eq", "value": 3}], ["INGRESS_TREE_DIGEST"], "test_kwflow::test_any_byte_change_including_a_comment_fails_closed")
    old = '"payload", "payload_commitment", "amount", "unit", "effects"'
    add_pin("semantic AST change inside a pinned site (14-name tuple reordered)", [{"op": "replace", "file": "synthetic_host.py", "old": old,
            "new": '"payload", "payload_commitment", "unit", "amount", "effects"', "count": 1}], {"synthetic_host.py": old},
            [{"obs": "mutation_applied", "op": "true"}, {"obs": "pins_unmatched_count", "op": "gte", "value": 1}, {"obs": "violation_count", "op": "gte", "value": 1}],
            [], "test_kwflow::test_semantic_ast_change_unpins")
    old = "institution_id=tba.INSTITUTION,"
    add_pin("pinned ExecutionOperation site changed (** names added)", [{"op": "replace", "file": "synthetic_host.py", "old": old, "new": old + " **names,", "count": 1}], {"synthetic_host.py": old},
            [{"obs": "mutation_applied", "op": "true"}, {"obs": "pins_unmatched_count", "op": "gte", "value": 1}, {"obs": "violation_count", "op": "gte", "value": 1}],
            [], "test_kwflow.MUTANTS['host: pinned ExecutionOperation site changed (un-pins)']")
    old = "host.executor.provision_claim("
    add_pin("required protected call site vanishes (provision_claim renamed)", [{"op": "replace", "file": "core.py", "old": old, "new": "host.executor.other_claim(", "count": 1}], {"core.py": old},
            [{"obs": "mutation_applied", "op": "true"}, {"obs": "required_sites_missing", "op": "contains", "value": ["core.py", "IngressCore._run", "provision_claim", 1]}],
            [], "test_kwflow::test_vanished_required_site_is_reported")
    for name, steps in (("package shadowing proposal.py", [{"op": "create_dir", "path": "proposal"}, {"op": "create_file", "path": "proposal/__init__.py", "text": "raise SystemExit('shadow')\n"}]),
                        ("extension module planted", [{"op": "create_file", "path": "proposal.cpython-313-x86_64-linux-gnu.so", "text": "\u007fELF"}]),
                        ("sitecustomize.py planted", [{"op": "create_file", "path": "sitecustomize.py", "text": ""}]),
                        ("symlink planted", [{"op": "symlink", "path": "link.py", "target": "core.py"}]),
                        ("BOUNDARY.md removed", [{"op": "delete", "path": "BOUNDARY.md"}])):
        add_pin(f"recursive tree check: {name}", steps, {"core.py": None},
                [{"obs": "mutation_applied", "op": "true"}, {"obs": "violation_rules", "op": "contains", "value": "INGRESS_TREE_FILE_LIST"},
                 {"obs": "violation_rules", "op": "contains", "value": "INGRESS_TREE_DIGEST"}], ["INGRESS_TREE_FILE_LIST", "INGRESS_TREE_DIGEST"],
                "test_kwflow::test_recursive_tree_rejects_extra_or_missing_entries")
    fams.append({"id": "PIN", "title": "Tree and pin integrity (fail closed): any byte change in a scanned file, a changed pinned site, a vanished required site, or any extra / missing / replaced entry in the "
                                      "recursive tree is rejected", "scan_mode": "pinned", "mutations": pin_ids, "controls": ["C-PIN-NOOP"]})
    pin_env_ctl = dict(env_pinned)
    controls.append({
        "id": "C-PIN-NOOP", "family": "PIN", "title": "no-op (identity replace, byte-identical copy) under pinned mode: the unmodified pinned tree must be ACCEPTED",
        "input": {"tree": INGRESS, "files": {"core.py": file_sha["core.py"]}, "anchor": {"file": "core.py", "text": "class IngressCore:", "occurrences": 1}},
        "operation": {"kind": "source_edit", "steps": [{"op": "replace", "file": "core.py", "old": "class IngressCore:", "new": "class IngressCore:", "count": 1}]},
        "expected": {"outcome": "ACCEPTED", "rules_all_of": []}, "environment": pin_env_ctl, "evidence_source": dict(evidence),
        "predicate": [{"obs": "mutation_applied", "op": "true"}, {"obs": "tree_unchanged", "op": "true"}, {"obs": "violation_count", "op": "eq", "value": 0},
                      {"obs": "pins_unmatched_count", "op": "eq", "value": 0}, {"obs": "required_sites_missing", "op": "empty"}, {"obs": "pinned_sites_used_count", "op": "eq", "value": 3}]})

    return {
        "schema": "cognous.nc4-03-mutation-set/1",
        "version": SET_VERSION,
        "status": "PROPOSED by Worker B2 (OCS-MVP-QGATE-05) for Qualification freeze; not frozen, not an acceptance. Qualification owns the set, the oracle and every verdict. A change is a NEW versioned file (v2), never an edit of v1.",
        "rulings": "Architect A3/A4 (issue #215 comment 6537418060): empty NC4-03 placeholder eliminated; explicit versioned mutation set; deterministic source/predicate mutations are mandatory; host-dependent predicates are separate subcases (nc4_03_host_subcases.v1.json) that cannot alter this set's verdict.",
        "deterministic": True,
        "host_dependent": False,
        "target": {
            "component": "hub (cogno-us/cognous-open-control-stack)", "pin_sha": _kwflow.HUB_REVISION, "tree": INGRESS,
            "ingress_py_tree_sha256": _kwflow.INGRESS_PY_TREE_SHA256, "recursive_tree_sha256": _kwflow.EXPECTED_TREE_SHA256,
            "file_sha256": file_sha, "interpreter": {"implementation": "CPython", "version_prefix": "3.13"},
            "input_note": "Verdicts are a pure function of these bytes and the predicate in _kwflow.py: a different tree or interpreter is not this candidate (FAIL / BLOCKED), never PASS."},
        "relation_to_supplementary_entries": (
            "The 183 `supplementary_nc4_03_predicate` battery entries (KW-001..KW-183 = every test of test_kwflow.py) remain, unchanged and still collected: they are the predicate's own self-tests "
            "(71 negative and 7 positive fixtures, baseline, pin records, 43 ingress mutants, 23 v5 evading mutants, tree and interpreter tests). This set does NOT re-implement or replace them. "
            "It selects, from the mutants those tables already contain (provenance field on each mutation), a FROZEN mandatory subset expressed as data with the six required fields, "
            "runs it through its own runner on a copy of the pinned hub tree, and adds per-family negative controls that the supplementary tables lack. "
            "The family GENERIC-FORWARD (added pre-freeze after the QGATE-05 pre-execution review, finding F-05) covers every rule of the predicate that the origin-rule families do not exercise "
            "(SIMULATE_NOT_CONSTANT_NONE, NONLITERAL_KWARGS, MODEL_COPY_KWARGS_FORBIDDEN, MODEL_COPY_UPDATE_NOT_FIXED, COMPREHENSION_NOT_FIXED, OPAQUE_POSITIONAL_UNPACK) plus three edits that reach the "
            "rules ORIGIN_VIOLATION and OPAQUE_POSITIONAL_UNPACK only through an UNRESOLVED callee (UNRESOLVED is the callee-resolution sentinel of _kwflow.names_of, not a rule id). "
            f"The {sum(1 for lab in T.MUTANTS if not any(f"MUTANTS[{lab!r}]" in m['provenance']['supplementary_source'] for m in muts))} MUTANTS not selected here (pinned-site un-pin variants, PROTECTED_CALLABLE_ESCAPES forms, etc.) and the fixture-level negatives stay supplementary only."),
        "verdict_rule": "PASS iff every mutation's predicate holds (REJECTED as expected), every control's predicate holds (ACCEPTED), no control satisfies its family's rejection predicate, and the pinned input digests match. "
                        "Anything else is FAIL; a non-3.13 interpreter or missing hub checkout is BLOCKED (never PASS). No host observation is read.",
        "families": fams,
        "mutations": muts,
        "controls": controls,
    }


if __name__ == "__main__":
    out = build(pathlib.Path(os.environ["MVP_HUB_DIR"]))
    sys.stdout.write(json.dumps(out, indent=1, sort_keys=False, ensure_ascii=True) + "\n")
