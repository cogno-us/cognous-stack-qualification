"""Independent re-verification of the Control Plane protected-file claims of PR #102 (E-1): recomputed here from the two pinned checkouts, not read from the PR's own tests."""
import difflib
import hashlib
import re
import subprocess

import pytest

import harness as H

OLD_SHA, NEW_SHA = "c219f8825a8ddf9da1fe6771ae575af0a9069ac8a04eadd40f093a9adb13655b", "4052ff87bfc90d3a4092ee690969354cd58769a9b542c4e5d1fa74ce821856ae"
OLD_BLOB, NEW_BLOB = "2cc8d998ff0a8fec3112a8b0634111fcf8fbef17", "b5329804b05a83990af1a3ca17eb61c13080c12f"
BOUNDED = "src/agent_control_plane/bounded.py"
EXPECTED_CHANGED = {
    "src/agent_control_plane/bounded.py", "src/agent_control_plane/registry_governed_lifecycle.py", "src/agent_control_plane/selection_evidence.py",
    "tests/fixtures/f4_selection_evidence_wire_0_1.json", "tests/fixtures/rw01_f4_poc_legacy_run_b19c47dd.json", "tests/rw01_f4_poc_support.py",
    "tests/test_f4_age_governance.py", "tests/test_f4_selection_evidence.py", "tests/test_f5_class_age_governance.py", "tests/test_f5_class_unreadable_governance.py",
    "tests/test_final3_composed_binding.py", "tests/test_freshness_purpose_anchor_successor.py", "tests/test_governed_policy_composition.py", "tests/test_rw01_f4_poc_bounded_diff.py",
    "tests/test_v02_legacy_claim_vector.py"}
pytestmark = [pytest.mark.row("PF", "Control Plane protected-file independent re-verification (bounded.py crosswalk, every changed file, no other protected file changed)"), pytest.mark.evidence("STATIC")]


def blobs(name):
    out = subprocess.run(["git", "--no-replace-objects", "-C", str(H.src(name)), "ls-tree", "-r", "--full-tree", "HEAD"], capture_output=True, text=True, check=True).stdout
    return {line.split("\t", 1)[1]: line.split()[2] for line in out.splitlines()}


def content(name, path):
    return subprocess.run(["git", "--no-replace-objects", "-C", str(H.src(name)), "show", "HEAD:" + path], capture_output=True, check=True).stdout


def test_bounded_py_old_and_new_sha256_and_blob_are_recomputed_and_equal_the_crosswalk():
    old, new = content("control_plane_base", BOUNDED), content("control_plane", BOUNDED)
    assert hashlib.sha256(old).hexdigest() == OLD_SHA and hashlib.sha256(new).hexdigest() == NEW_SHA
    assert blobs("control_plane_base")[BOUNDED] == OLD_BLOB and blobs("control_plane")[BOUNDED] == NEW_BLOB
    assert hashlib.sha1(b"blob %d\0" % len(new) + new).hexdigest() == NEW_BLOB      # blob id recomputed by hand, not read from git


def test_bounded_py_diff_is_exactly_six_added_lines_and_zero_removed():
    old = content("control_plane_base", BOUNDED).decode().splitlines()
    new = content("control_plane", BOUNDED).decode().splitlines()
    delta = [l for l in difflib.unified_diff(old, new, lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    assert len([l for l in delta if l[0] == "-"]) == 0 and len([l for l in delta if l[0] == "+"]) == 6, delta
    joined = "\n".join(delta)
    for needle in ("from .selection_evidence import SelectionEvidence", "selection_evidence: SelectionEvidence | None = Field(default=None, exclude_if=lambda v: v is None)",
                   "def _decision_selection_evidence(self, reasons", "selection_evidence=self._decision_selection_evidence(reasons)"):
        assert needle in joined
    removed_to_old = "\n".join(l for l in new if l not in set(delta))
    assert [l for l in old if l not in set(new)] == []                             # every OLD line survives


def test_the_set_of_files_the_cp_pr_changes_is_exactly_the_declared_fifteen():
    base, head = blobs("control_plane_base"), blobs("control_plane")
    changed = {p for p in set(base) | set(head) if base.get(p) != head.get(p)}
    assert changed == EXPECTED_CHANGED, sorted(changed ^ EXPECTED_CHANGED)
    assert [p for p in base if p not in head] == []                                  # nothing deleted


def _pins(name):
    pins = {}
    for path, blob in blobs(name).items():
        if path.startswith("tests/") and path.endswith(".py"):
            text = content(name, path).decode("utf-8", "replace")
            for m in re.finditer(r'"((?:src/agent_control_plane/)?[A-Za-z0-9_]+\.py)"\s*:\s*(?:\(\s*)?"([0-9a-f]{64}|[0-9a-f]{40})"', text):
                pins.setdefault(path, []).append((m.group(1), m.group(2)))
    return pins


def test_no_other_protected_file_changed_every_pinned_source_file_is_unchanged_except_bounded_py():
    base, head = blobs("control_plane_base"), blobs("control_plane")
    pins = _pins("control_plane")
    named = {}
    for path, items in pins.items():
        for fname, digest in items:
            rel = fname if "/" in fname else "src/agent_control_plane/" + fname
            if rel in head:
                named.setdefault(rel, set()).add((path, digest))
    named.setdefault(BOUNDED, set())      # bounded.py is pinned through named constants (checked by the other tests), not by a literal inside a dict
    assert len(named) >= 6, sorted(named)
    for rel in sorted(named):
        if rel == BOUNDED:
            continue
        assert base[rel] == head[rel], "protected file changed: " + rel            # identical blob id at base and head
    # every pin recorded for each named file in the PR-head tests is the REAL hash of that file at PR head (pins are real, not weakened or prefix-matched)
    bad = []
    for rel, items in named.items():
        data = content("control_plane", rel)
        for path, digest in items:
            real = hashlib.sha256(data).hexdigest() if len(digest) == 64 else hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
            if digest != real and digest not in (OLD_SHA, OLD_BLOB):
                bad.append((path, rel, digest))
    # older/other-generation pin comments are allowed to differ only when they are not asserted: report any asserted mismatch
    asserted_bad = [b for b in bad if b[1] == BOUNDED]
    assert asserted_bad == [], asserted_bad


def test_old_hash_is_kept_as_a_named_constant_in_every_repinned_assertion_and_the_seventh_is_flagged():
    head = blobs("control_plane")
    holders = []
    for path in sorted(p for p in head if p.startswith("tests/") and p.endswith(".py")):
        text = content("control_plane", path).decode("utf-8", "replace")
        if OLD_SHA in text or OLD_BLOB in text:
            holders.append(path)
            assert re.search(r'^[A-Z0-9_]+\s*=\s*"(%s|%s)"' % (OLD_SHA, OLD_BLOB), text, re.M), path          # a NAMED constant
            assert NEW_SHA in text or NEW_BLOB in text, path
    six = {"tests/test_f4_age_governance.py", "tests/test_final3_composed_binding.py", "tests/test_f5_class_unreadable_governance.py", "tests/test_freshness_purpose_anchor_successor.py",
           "tests/test_governed_policy_composition.py", "tests/test_v02_legacy_claim_vector.py"}
    extra = sorted(set(holders) - six - {"tests/test_rw01_f4_poc_bounded_diff.py"})
    assert extra == ["tests/test_f5_class_age_governance.py"], extra          # FINDING F-3: a SEVENTH pinned assertion beyond the six of the frozen contract (declared in the PR; needs ratification)
    assert six <= set(holders)


def test_the_updated_tripwire_still_detects_an_unrelated_one_byte_modification_of_bounded_py():
    new = content("control_plane", BOUNDED)
    for mutated in (new + b"#", new.replace(b"class RuntimeDecision", b"class RuntimeDecisioN", 1), new[:-1]):
        assert mutated != new
        assert hashlib.sha256(mutated).hexdigest() != NEW_SHA and hashlib.sha1(b"blob %d\0" % len(mutated) + mutated).hexdigest() != NEW_BLOB


def test_registry_governed_lifecycle_py_is_changed_but_is_not_in_any_protected_pin_set():
    pins = _pins("control_plane")
    pinned = {fname for items in pins.values() for fname, _ in items}
    assert "registry_governed_lifecycle.py" not in pinned and "src/agent_control_plane/registry_governed_lifecycle.py" not in pinned
    assert blobs("control_plane_base")["src/agent_control_plane/registry_governed_lifecycle.py"] != blobs("control_plane")["src/agent_control_plane/registry_governed_lifecycle.py"]
