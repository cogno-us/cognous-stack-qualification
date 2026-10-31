"""NC4-03 frozen mutation set: loader, runner and the DETERMINISTIC verdict (host-independent by construction).

SPDX-License-Identifier: Apache-2.0

Pure function of (a) ``nc4_03_mutation_set.v1.json``, (b) the bytes of the pinned hub ``tools/mvp_ingress`` tree and (c) the predicate code in
``_kwflow.py`` on CPython 3.13. It reads no host property: no uid, no /proc, no sysctl, no socket, no network, no clock, no process environment (other than
the caller-supplied hub path). Every mutation is applied to a COPY of the tree in a temporary directory; the pinned checkout is never written.

Verdict vocabulary reuses ``verdict.py`` (PASS / FAIL / BLOCKED). The deterministic record is computed first, is canonical JSON with its own sha256, and is
never read or altered by the host-dependent subcases (``_nc4_03_host.py``); ``compose`` is the only place the two meet and it copies the deterministic block
verbatim. PROPOSED; Qualification owns and freezes the set and every verdict.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

import _kwflow
import verdict

HERE = pathlib.Path(__file__).resolve().parent
SET_PATH = HERE / "nc4_03_mutation_set.v1.json"
PASS, FAIL, BLOCKED = verdict.PASS, verdict.FAIL, verdict.BLOCKED
ITEM_FIELDS = ("input", "operation", "expected", "environment", "evidence_source", "predicate")
STEP_OPS = ("replace", "append", "create_file", "create_dir", "symlink", "delete")
INGRESS_REL = pathlib.Path("tools") / "mvp_ingress"


class SetError(Exception):
    pass


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def load_set(path: pathlib.Path = SET_PATH) -> dict:
    return json.loads(pathlib.Path(path).read_text())


def set_file_sha256(path: pathlib.Path = SET_PATH) -> str:
    return sha256_bytes(pathlib.Path(path).read_bytes())


def interpreter_ok() -> bool:
    return sys.implementation.name == "cpython" and sys.version_info[:2] == (3, 13)


# ---------------------------------------------------------------------------------------------------------------- structure validation
def validate_set(doc: dict) -> list[str]:
    """Return the list of structural problems (empty means every mutation and control is fully specified with the six required fields)."""
    problems = []
    if doc.get("schema") != "cognous.nc4-03-mutation-set/1":
        problems.append("schema")
    if doc.get("deterministic") is not True or doc.get("host_dependent") is not False:
        problems.append("set must declare deterministic:true, host_dependent:false")
    seen = set()
    fam_ids = {f["id"] for f in doc.get("families", [])}
    for kind in ("mutations", "controls"):
        for it in doc.get(kind, []):
            iid = it.get("id", "<no id>")
            if iid in seen:
                problems.append(f"{iid}: duplicate id")
            seen.add(iid)
            for f in ITEM_FIELDS:
                if not it.get(f):
                    problems.append(f"{iid}: missing or empty field {f!r}")
            if it.get("family") not in fam_ids:
                problems.append(f"{iid}: unknown family")
            env = it.get("environment") or {}
            if env.get("host_dependent") is not False or env.get("scan_mode") not in ("rebased", "pinned"):
                problems.append(f"{iid}: environment must declare host_dependent:false and a scan_mode")
            exp = it.get("expected") or {}
            if exp.get("outcome") not in ("REJECTED", "ACCEPTED"):
                problems.append(f"{iid}: expected.outcome")
            if (kind == "mutations") != (exp.get("outcome") == "REJECTED"):
                problems.append(f"{iid}: outcome does not match its kind")
            steps = (it.get("operation") or {}).get("steps") or []
            if not steps or any(s.get("op") not in STEP_OPS for s in steps):
                problems.append(f"{iid}: operation steps")
            for p in it.get("predicate") or []:
                if not {"obs", "op"} <= set(p):
                    problems.append(f"{iid}: malformed predicate item")
            for rule in exp.get("rules_all_of", []):
                if not any(p["obs"] == "violation_rules" and p["op"] == "contains" and p.get("value") == rule for p in it.get("predicate") or []):
                    problems.append(f"{iid}: expected rule {rule} is not enforced by the predicate")
    for fam in doc.get("families", []):
        ctl = [c for c in doc.get("controls", []) if c["family"] == fam["id"]]
        if not ctl:
            problems.append(f"family {fam['id']}: no negative control")
        if sorted(c["id"] for c in ctl) != sorted(fam["controls"]):
            problems.append(f"family {fam['id']}: control list mismatch")
        if sorted(m["id"] for m in doc["mutations"] if m["family"] == fam["id"]) != sorted(fam["mutations"]):
            problems.append(f"family {fam['id']}: mutation list mismatch")
    return problems


# ---------------------------------------------------------------------------------------------------------------- applying operations
def _apply_steps(root: pathlib.Path, steps: list) -> tuple[bool, str]:
    """Apply the steps to the COPY at ``root/tools/mvp_ingress``. Returns (applied, why-not). An anchor that does not occur exactly ``count`` times is NOT applied."""
    ing = root / INGRESS_REL
    for s in steps:
        op = s["op"]
        if op == "replace":
            f = ing / s["file"]
            text = f.read_text()
            if text.count(s["old"]) != s["count"]:
                return False, f"anchor occurs {text.count(s['old'])} times in {s['file']}, expected {s['count']}"
            f.write_text(text.replace(s["old"], s["new"]))
        elif op == "append":
            f = ing / s["file"]
            f.write_text(f.read_text() + s["text"])
        elif op == "create_file":
            (ing / s["path"]).write_text(s["text"])
        elif op == "create_dir":
            (ing / s["path"]).mkdir()
        elif op == "symlink":
            (ing / s["path"]).symlink_to(s["target"])
        elif op == "delete":
            (ing / s["path"]).unlink()
    return True, ""


def _rebased_scan(root: pathlib.Path) -> dict:
    """scan_dir with the pins and the recursive digest re-based onto the mutated copy, so only the source-aware rules decide (restored afterwards)."""
    saved_pins = {k: dict(v) for k, v in _kwflow.PINNED_SITES.items()}
    saved_tree = _kwflow.EXPECTED_TREE_SHA256
    try:
        _, tree = _kwflow.ingress_tree_manifest(sorted((root / INGRESS_REL).glob("*.py")))
        for r in _kwflow.PINNED_SITES.values():
            r["reviewed_ingress_tree_sha256"] = tree
        _kwflow.EXPECTED_TREE_SHA256 = _kwflow.tree_digest(_kwflow.tree_files(root))
        return _kwflow.scan_dir(root)
    finally:
        _kwflow.PINNED_SITES.clear()
        _kwflow.PINNED_SITES.update(saved_pins)
        _kwflow.EXPECTED_TREE_SHA256 = saved_tree


def summarize(scan: dict) -> dict:
    """Raw scan -> the small, stable observation record the predicates read (no interpreter patch version, no path, no clock)."""
    return {
        "violation_rules": sorted({v["rule"] for v in scan["violations"]}),
        "violation_count": len(scan["violations"]),
        "pins_unmatched_count": len(scan["pins_unmatched"]),
        "required_sites_missing": scan["required_sites_missing"],
        "pinned_sites_used_count": len(scan["pinned_sites_used"]),
        "ast_digest_python_match": scan["ast_digest_python_match"],
        "ingress_tree_sha256": scan["ingress_tree_sha256"],
        "recursive_tree_sha256": scan["recursive_tree_sha256"],
    }


def observe_tree(root: pathlib.Path, mode: str) -> dict:
    scan = _rebased_scan(root) if mode == "rebased" else _kwflow.scan_dir(root)
    return summarize(scan)


def holds(predicate: list, obs: dict) -> tuple[bool, list]:
    failed = [p for p in predicate if not verdict._check(obs, p)]
    return not failed, failed


def run_item(hub: pathlib.Path, item: dict, base_obs: dict) -> dict:
    """Apply one mutation or control to a fresh copy and evaluate its predicate. ``mutation_applied`` is true only if the operation applied AND changed the tree bytes
    (or, for a no-op control, was applied with identical result); an unapplied mutation can never count as rejected."""
    with tempfile.TemporaryDirectory(prefix="nc4-03-mut-") as tmp:
        root = pathlib.Path(tmp)
        shutil.copytree(pathlib.Path(hub) / INGRESS_REL, root / INGRESS_REL, symlinks=True)
        before = _kwflow.tree_digest(_kwflow.tree_files(root))
        applied, why = _apply_steps(root, item["operation"]["steps"])
        after = _kwflow.tree_digest(_kwflow.tree_files(root))
        obs = {"mutation_applied": applied, "tree_unchanged": before == after, "apply_error": why}
        # a mutation (expected REJECTED) must actually change the tree; a no-op control must leave it byte-identical where it says so
        if item["expected"]["outcome"] == "REJECTED" and before == after:
            obs["mutation_applied"] = False
            obs["apply_error"] = "mutation did not change the tree"
        if applied:
            obs.update(observe_tree(root, item["environment"]["scan_mode"]))
    ok, failed = holds(item["predicate"], obs)
    return {"id": item["id"], "family": item["family"], "expected_outcome": item["expected"]["outcome"], "predicate_holds": ok,
            "observed": {k: obs.get(k) for k in ("mutation_applied", "tree_unchanged", "apply_error", "violation_rules", "violation_count", "pins_unmatched_count",
                                                 "required_sites_missing", "pinned_sites_used_count")},
            "failed_predicates": failed}


def run_deterministic(hub_dir, set_path: pathlib.Path = SET_PATH) -> dict:
    """Compute the deterministic NC4-03 mutation-set record. Never raises for an input problem: returns BLOCKED / FAIL with the reason."""
    doc = load_set(set_path)
    rec = {"schema": "cognous.nc4-03-deterministic-record/1", "set_version": doc["version"], "set_file_sha256": set_file_sha256(set_path),
           "host_dependent": False, "interpreter_required": "CPython 3.13", "mutation_results": [], "control_results": [], "reasons": []}

    def done(status):
        rec["verdict"] = status
        rec["mutations_total"] = len(doc["mutations"])
        rec["mutations_rejected"] = sum(1 for r in rec["mutation_results"] if r["predicate_holds"])
        rec["mutations_not_rejected"] = sorted(r["id"] for r in rec["mutation_results"] if not r["predicate_holds"])
        rec["controls_total"] = len(doc["controls"])
        rec["controls_accepted"] = sum(1 for r in rec["control_results"] if r["predicate_holds"])
        rec["controls_falsely_rejected"] = sorted(r["id"] for r in rec["control_results"] if not r["predicate_holds"])
        rec["families"] = sorted(f["id"] for f in doc["families"])
        rec["record_sha256"] = sha256_bytes(canonical({k: v for k, v in rec.items() if k != "record_sha256"}).encode())
        return rec

    problems = validate_set(doc)
    if problems:
        rec["reasons"] = ["set structure: " + p for p in problems]
        return done(FAIL)
    if not interpreter_ok():
        rec["reasons"] = ["interpreter is not CPython 3.13: the ast_digest pins are honoured on 3.13 only, so the set cannot be judged here (BLOCKED, never PASS)"]
        return done(BLOCKED)
    if not hub_dir or not (pathlib.Path(hub_dir) / INGRESS_REL).is_dir():
        rec["reasons"] = ["pinned hub checkout (tools/mvp_ingress) not available"]
        return done(BLOCKED)
    hub = pathlib.Path(hub_dir)
    tgt = doc["target"]
    ing = hub / INGRESS_REL
    actual = {p.name: sha256_bytes(p.read_bytes()) for p in sorted(ing.iterdir()) if p.is_file()}
    base = observe_tree(hub, "pinned")
    rec["pinned_input"] = {"ingress_tree_sha256": base["ingress_tree_sha256"], "recursive_tree_sha256": base["recursive_tree_sha256"],
                           "matches_set_target": base["ingress_tree_sha256"] == tgt["ingress_py_tree_sha256"] and base["recursive_tree_sha256"] == tgt["recursive_tree_sha256"] and actual == tgt["file_sha256"]}
    if not rec["pinned_input"]["matches_set_target"]:
        rec["reasons"] = ["hub tools/mvp_ingress does not equal the set's frozen target bytes: this is not the candidate the set was frozen against"]
        return done(FAIL)
    for m in doc["mutations"]:
        rec["mutation_results"].append(run_item(hub, m, base))
    for c in doc["controls"]:
        rec["control_results"].append(run_item(hub, c, base))
    # false-pass guard: a control must never satisfy the rejection predicate of any mutation of its family
    guard = []
    for r in rec["control_results"]:
        for m in doc["mutations"]:
            if m["family"] != r["family"]:
                continue
            obs = {**r["observed"], "violation_rules": r["observed"]["violation_rules"] or []}
            if m["predicate"] and holds(m["predicate"], obs)[0]:
                guard.append([r["id"], m["id"]])
    rec["control_satisfies_rejection_predicate"] = guard
    status = PASS
    bad_m = [r["id"] for r in rec["mutation_results"] if not r["predicate_holds"]]
    bad_c = [r["id"] for r in rec["control_results"] if not r["predicate_holds"]]
    if bad_m:
        rec["reasons"].append(f"mutations not rejected as expected: {bad_m}")
        status = FAIL
    if bad_c:
        rec["reasons"].append(f"controls falsely rejected or not applied: {bad_c}")
        status = FAIL
    if guard:
        rec["reasons"].append(f"a control satisfies a rejection predicate (predicate could false-pass): {guard}")
        status = FAIL
    if status == PASS:
        rec["reasons"].append("every mutation rejected as expected, every control accepted, no control satisfies a rejection predicate")
    return done(status)


# ---------------------------------------------------------------------------------------------------------------- scenario observation for the oracle
def d1_simulate_ast_test(hub: pathlib.Path) -> dict:
    """Run D1's own simulate AST tests on a COPY of the hub tree (never in the pinned checkout)."""
    with tempfile.TemporaryDirectory(prefix="nc4-03-d1-") as tmp:
        dst = pathlib.Path(tmp) / "hub"
        dst.mkdir()
        for sub in ("tools", "tests"):
            if (hub / sub).exists():
                shutil.copytree(hub / sub, dst / sub, symlinks=True, ignore=shutil.ignore_patterns("__pycache__"))
        env = {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": str(dst), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0"}
        p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_mvp_ingress_boundary.py", "-k", "simulate"],
                           cwd=dst, env=env, capture_output=True, text=True, timeout=300)
        return {"exit_code": p.returncode, "tail": p.stdout[-300:]}


def scenario_observation(hub_dir, hub_head=None) -> dict:
    """The observation record of scenario ``nc4_03_det`` (see the v8 fragment): v7's source-level predicates' observations (same names, same values, now host-independent)
    plus the mutation-set record. Computed with no host input."""
    det = run_deterministic(hub_dir)
    obs = {"scope": "SOURCE-LEVEL deterministic assertions over the pinned hub source (AST predicate, frozen mutation set, D1 AST tests); NOT execution observations and NOT host evidence",
           "deterministic_record": det, "mutation_set": {k: det[k] for k in ("set_version", "set_file_sha256", "verdict", "mutations_total", "mutations_rejected", "mutations_not_rejected",
                                                                       "controls_total", "controls_accepted", "controls_falsely_rejected", "record_sha256")},
           "mutation_set_control_guard": det.get("control_satisfies_rejection_predicate", ["<not computed>"])}
    if det["verdict"] == BLOCKED:
        return {"status": "blocked", "blocked_reason": "; ".join(det["reasons"]), **obs}
    hub = pathlib.Path(hub_dir)
    import _ingress  # lazy: only for the v3 simulate-keyword AST helper that v7 NC4-03 already used
    src = {"kwflow": _kwflow.scan_dir(hub, hub_head)}
    src.update(_ingress.ast_simulate_scan(hub))
    d1 = d1_simulate_ast_test(hub)
    src["d1_ast_test_exit_code"], src["d1_ast_test_tail"] = d1["exit_code"], d1["tail"]
    return {"status": "ran", **obs, "source_level": src}


# ---------------------------------------------------------------------------------------------------------------- composition with host subcases
def compose(deterministic: dict, host: dict) -> dict:
    """Meet point of the two independent computations. The deterministic block is copied verbatim (checked by sha) and the NC4-03 verdict IS the deterministic
    verdict. The host block is reported beside it under its own statuses; it is never read to decide the deterministic verdict, and a host exception, BLOCKED or FAIL
    cannot convert a deterministic PASS or FAIL."""
    det_sha = sha256_bytes(canonical(deterministic).encode())
    out = {"nc4_03_deterministic": deterministic, "nc4_03_deterministic_sha256": det_sha, "nc4_03_row_verdict": deterministic["verdict"],
           "host_dependent_subcases": host, "host_subcase_statuses": {h["id"]: h["status"] for h in host.get("subcases", [])},
           "separation": "the row verdict above is the deterministic verdict only; host subcase statuses are separate rows and never change it"}
    assert sha256_bytes(canonical(out["nc4_03_deterministic"]).encode()) == det_sha
    return out
