"""Reasons 0.3 successor assertion at Control Plane fff27ebf, kept SEPARATE from the historical 164-code assertion.

REASONS_CP_DIR  a pristine, full-history checkout of cogno-us/cognous-control-plane at the pinned revision.
Every test FAILS (never skips) when the variable is unset, the checkout is not at the pin, or it is not pristine.

Historical assertion (unchanged elsewhere): suites/v1-probes/test_rule_revision_probes.py asserts 164 codes on the 0.2 file at Control Plane
0a41faa9. This suite asserts the SAME 0.2 file still has 164 codes (frozen) AND asserts the 172-code 0.3 file separately. Substituting either
version for the other fails (negative controls below). Builder-authored; not a Qualification verdict. Not independently reviewed.
SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

CP_SHA = "fff27ebf356007e1eb3bb24198efc7e3e3f0c5eb"
BASE_SHA = "7a4bcd40b3b49e61ff3c294dcca53b52f460b22c"      # first parent: the pre-R6 Control Plane
PIN_RECORD = Path(__file__).resolve().parents[2] / "process" / "registry-v1" / "reasons-successor-pin.proposed.v1.json"
V01, V02, V03 = "runtime-authority-reasons/0.1", "runtime-authority-reasons/0.2", "runtime-authority-reasons/0.3"
FILES = {V01: "schemas/runtime_authority_reasons_0_1.json", V02: "schemas/runtime_authority_reasons_0_2.json",
         V03: "schemas/runtime_authority_reasons_0_3.json"}
BLOB = {V01: "a21aa9b350c75b3d2f7cd325a8f7b43656e73b26", V02: "a46ef35e7ece5c3a16e50d174000c49e3632eb12",
        V03: "b3b822874b7288fdaa015c9cdac960f39d6594bc"}
SHA256 = {V01: "fbc4df2e02457e294ca1f819d0e507c4452e46691e4f139a66be48967c2096c0",
          V02: "c7678fa766f4d67d71ad9533672afdc87b3765ac1d336acae26504fc74ce3be6",
          V03: "58b29ef74b9bd49d3eae7278d8cce73c7cbc6a1095a07f7b9fa44f48a7b8c07f"}
ADDED_IN_0_3 = ["approval_commitment_version_unsupported", "approval_policy_generation_missing", "approval_policy_generation_invalid",
                "approval_policy_generation_mismatch", "approval_policy_activation_mismatch", "freshness_ceiling_exceeded",
                "freshness_ceiling_unanchored", "policy_binding_invalid"]


def _git(*args):
    return subprocess.run(["git", "-C", os.environ["REASONS_CP_DIR"], *args], check=True, capture_output=True, text=True, timeout=60).stdout.strip()


def _blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def _load(label):
    raw = (Path(os.environ["REASONS_CP_DIR"]) / FILES[label]).read_bytes()
    return json.loads(raw), raw


def _kinds(doc):
    kinds = [v["reason_kind"] for v in doc["codes"].values()]
    return len(kinds), kinds.count("typed_only"), kinds.count("recomputable")


def historical_164_problems(doc, raw, check_bytes=True):
    """The historical assertion: the frozen 0.2 registry. Returns a list of problems (empty = holds)."""
    problems = []
    if doc.get("version") != V02:
        problems.append(f"version {doc.get('version')!r} != {V02}")
    if _kinds(doc) != (164, 163, 1):
        problems.append(f"kinds {_kinds(doc)} != (164, 163, 1)")
    if check_bytes and (_blob(raw) != BLOB[V02] or hashlib.sha256(raw).hexdigest() != SHA256[V02]):
        problems.append("bytes are not the frozen 0.2 file")
    return problems


def successor_172_problems(doc, raw, frozen_doc, check_bytes=True):
    """The successor assertion: the immutable 0.3 registry (the 164 entries of 0.2 unchanged and in order, plus eight)."""
    problems = []
    if doc.get("version") != V03:
        problems.append(f"version {doc.get('version')!r} != {V03}")
    if _kinds(doc) != (172, 171, 1):
        problems.append(f"kinds {_kinds(doc)} != (172, 171, 1)")
    codes, old = list(doc["codes"]), list(frozen_doc["codes"])
    if codes[:len(old)] != old or any(doc["codes"][c] != frozen_doc["codes"][c] for c in old):
        problems.append("the 164 entries of 0.2 are not unchanged and in order")
    if codes[len(old):] != ADDED_IN_0_3:
        problems.append("the eight added codes are not exactly the pinned names in order")
    for c in ADDED_IN_0_3:
        entry = doc["codes"].get(c)
        if not entry or entry.get("reason_kind") != "typed_only":
            problems.append(f"{c} is not typed_only")
    if check_bytes and (_blob(raw) != BLOB[V03] or hashlib.sha256(raw).hexdigest() != SHA256[V03]):
        problems.append("bytes are not the pinned 0.3 file")
    return problems


_MISSING = not os.environ.get("REASONS_CP_DIR")


@pytest.fixture(scope="module")
def cp():
    assert not _MISSING, "REASONS_CP_DIR is not set (this suite fails rather than skips)"
    head, dirty = _git("rev-parse", "HEAD"), _git("status", "--porcelain")
    assert head == CP_SHA, f"Control Plane HEAD {head} != pin {CP_SHA}"
    assert not dirty, "Control Plane checkout is not pristine"
    assert not _git("status", "--porcelain", "--ignored"), "Control Plane checkout has ignored/untracked files"
    return {label: _load(label) for label in FILES}


def test_pin_record_matches_the_constants_in_this_suite():
    rec = json.loads(PIN_RECORD.read_text(encoding="utf-8"))
    assert rec["control_plane"]["sha"] == CP_SHA and rec["control_plane"]["first_parent"] == BASE_SHA
    for label in FILES:
        r = rec["registries"][label]
        assert (r["file"], r["git_blob"], r["sha256"]) == (FILES[label], BLOB[label], SHA256[label])
    assert rec["registries"][V02]["codes"] == 164 and rec["registries"][V03]["codes"] == 172 and rec["added_in_0_3"] == ADDED_IN_0_3
    assert (rec["registries"][V02]["typed_only"], rec["registries"][V02]["recomputable"]) == (163, 1)
    assert (rec["registries"][V03]["typed_only"], rec["registries"][V03]["recomputable"]) == (171, 1)
    assert rec["registries"][V02]["frozen"] is True and rec["registries"][V03]["immutable_successor_of"] == V02
    assert "0a41faa972699f7ec3063967a14cd9bdd3e67d27" in rec["control_plane"]["historical_pins_not_replaced"]


def test_the_checkout_is_the_pinned_revision_and_a_merge_of_the_pre_r6_main(cp):
    parents = _git("rev-list", "--parents", "-n", "1", CP_SHA).split()[1:]
    assert parents[0] == BASE_SHA, parents


def test_historical_164_assertion_still_holds_on_the_frozen_0_2_registry(cp):
    assert historical_164_problems(*cp[V02]) == []


def test_historical_0_1_registry_is_unchanged(cp):
    doc, raw = cp[V01]
    assert _kinds(doc) == (121, 120, 1) and _blob(raw) == BLOB[V01] and hashlib.sha256(raw).hexdigest() == SHA256[V01]


def test_frozen_0_2_is_byte_identical_to_the_pre_r6_main(cp):
    for label in (V01, V02):
        assert _git("rev-parse", f"{BASE_SHA}:{FILES[label]}") == BLOB[label] == _git("rev-parse", f"{CP_SHA}:{FILES[label]}")
    _git("cat-file", "-e", f"{BASE_SHA}^{{commit}}")                    # the base commit is present (full history)
    absent = subprocess.run(["git", "-C", os.environ["REASONS_CP_DIR"], "cat-file", "-e", f"{BASE_SHA}:{FILES[V03]}"], capture_output=True)
    assert absent.returncode != 0                                       # 0.3 did not exist before R6


def test_successor_172_assertion_holds_on_the_immutable_0_3_registry(cp):
    assert successor_172_problems(*cp[V03], cp[V02][0]) == []


# ---------------------------------------------------------------- substitution negatives: neither version can stand in for the other
def test_substituting_0_3_for_the_historical_164_assertion_fails(cp):
    problems = historical_164_problems(*cp[V03])
    assert problems and any("164" in p for p in problems) and any("frozen 0.2" in p for p in problems)


def test_substituting_0_2_for_the_successor_172_assertion_fails(cp):
    problems = successor_172_problems(*cp[V02], cp[V02][0])
    assert problems and any("172" in p for p in problems) and any("pinned 0.3" in p for p in problems)


def test_substituting_0_1_for_either_assertion_fails(cp):
    assert historical_164_problems(*cp[V01]) and successor_172_problems(*cp[V01], cp[V02][0])


def _mutated(doc, how):
    """Returns (document, bytes) for a tampered copy; the bytes are re-serialised so a doc-level edit also changes the pinned digests."""
    d = copy.deepcopy(doc)
    codes = d["codes"]
    if how == "drop_one":
        del codes[next(iter(codes))]
    elif how == "append_code":
        codes["zz_extra_code"] = {"reason_kind": "typed_only", "description": "x"}
    elif how == "reorder_added":
        keys = list(codes)
        keys[-1], keys[-2] = keys[-2], keys[-1]
        d["codes"] = {k: codes[k] for k in keys}
    elif how == "edit_old_entry":
        codes[next(iter(codes))]["description"] += " changed"
    elif how == "relabel_version":
        d["version"] = V03 if doc.get("version") == V02 else V02
    elif how == "added_recomputable":
        codes[ADDED_IN_0_3[0]]["reason_kind"] = "recomputable"
    return d, (json.dumps(d, indent=2) + "\n").encode()


EXPECT_172 = {"drop_one": "kinds", "append_code": "kinds", "reorder_added": "eight added codes", "edit_old_entry": "unchanged and in order",
              "relabel_version": "version", "added_recomputable": "kinds"}
EXPECT_164 = {"drop_one": "kinds", "append_code": "kinds", "edit_old_entry": None, "relabel_version": "version"}


@pytest.mark.parametrize("how", sorted(EXPECT_172))
def test_a_tampered_successor_registry_fails_the_172_assertion_structurally(cp, how):
    """Digest checks are OFF here, so only the structural checks can catch the tamper; the specific defect must be named."""
    mutated, raw = _mutated(cp[V03][0], how)
    problems = successor_172_problems(mutated, raw, cp[V02][0], check_bytes=False)
    assert any(EXPECT_172[how] in p for p in problems), (how, problems)
    assert successor_172_problems(mutated, raw, cp[V02][0]), how           # and the digest check also rejects it


@pytest.mark.parametrize("how", sorted(EXPECT_164))
def test_a_tampered_historical_registry_fails_the_164_assertion(cp, how):
    mutated, raw = _mutated(cp[V02][0], how)
    if EXPECT_164[how]:
        assert any(EXPECT_164[how] in p for p in historical_164_problems(mutated, raw, check_bytes=False)), how
    assert historical_164_problems(mutated, raw), how                       # edit_old_entry is caught by the pinned digests alone
