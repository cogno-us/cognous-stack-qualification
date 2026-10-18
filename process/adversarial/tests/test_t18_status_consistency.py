"""T18. Control-panel and results consistency checker (ideas I74, I70, tier 8).

SPDX-License-Identifier: Apache-2.0

Attacker: an editor of release summaries who changes a status in one copy without evidence.
Checker: process/adversarial/consistency_check.py (read-only). Copies compared: the reduced-scope requirements matrix (recounted
from its rows), its summary.json, the hub release-closeout control panel JSON (v1_validation) and Markdown prose, and the
failure register (vocabulary and referenced rows).
Invariant: the copies agree; a status changed in any one copy is flagged. Mutations are applied to in-memory copies only.

Does not prove: that the copies are right (they can agree on a wrong value); consistency of documents the checker does not read
(reports, known-limits prose, dashboard); the hub is frozen, so a real divergence is a coordinator follow-up, not an edit here.
"""
from __future__ import annotations

import copy
import importlib.util
import pathlib

import pytest

from conftest import ADV, observe, require

T = "T18"
DNP = "agreement is not correctness; documents outside the five read copies are not checked"


def _checker():
    spec = importlib.util.spec_from_file_location("adv_consistency_check", ADV / "consistency_check.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def sources():
    hub = require("hub")["hub"]
    mod = _checker()
    return mod, mod.load_sources(pathlib.Path(hub))


def test_positive_control_retained_copies_are_consistent(sources):
    mod, src = sources
    findings = mod.check(src)
    observe(T, "retained copies", "prevented" if not findings else "reproduced failure", does_not_prove=DNP,
            detail={"findings": findings})
    assert findings == [], findings


def _mutations(src):
    def matrix(s):
        row = next(r for r in s["matrix"]["requirements"] if r.get("mandatory") and r["status"] == "PASS")
        row["status"] = "FAIL"

    def summary(s):
        s["summary"]["requirement_status_counts"]["PASS"] += 1

    def summary_verdict(s):
        s["summary"]["full_catalog_status"]["unreduced_mandatory_verdict"] = "PASS"

    def panel(s):
        s["panel"]["v1_validation"]["mandatory_requirements"]["FAIL"] = 1

    def panel_verdict(s):
        s["panel"]["v1_validation"]["verdict_full_catalog"] = "PASS"

    def markdown(s):
        s["markdown"] = s["markdown"].replace("Full-catalog verdict: FAIL", "Full-catalog verdict: PASS")

    def markdown_counts(s):
        s["markdown"] = s["markdown"].replace("39 PASS, 2 FAIL, 29 INCONCLUSIVE, 5 NOT RUN", "41 PASS, 0 FAIL, 29 INCONCLUSIVE, 5 NOT RUN")

    def register(s):
        s["register"]["entries"][0]["status"] = "CLOSED"

    def register_verified(s):
        e = next(x for x in s["register"]["entries"] if x.get("status") == "VERIFIED")
        e.pop("verified_in", None)
    return {f.__name__: f for f in (matrix, summary, summary_verdict, panel, panel_verdict, markdown, markdown_counts, register,
                                     register_verified)}


def test_every_single_copy_mutation_is_flagged(sources):
    mod, src = sources
    missed = []
    for name, mutate in _mutations(src).items():
        s = copy.deepcopy(src)
        mutate(s)
        assert s != src, f"mutation {name} changed nothing; the fixture no longer matches the documents"
        if not mod.check(s):
            missed.append(name)
    observe(T, "single-copy status mutations", "detected only" if not missed else "reproduced failure", does_not_prove=DNP,
            detail={"mutations": sorted(_mutations(src)), "missed": missed})
    assert missed == [], missed
