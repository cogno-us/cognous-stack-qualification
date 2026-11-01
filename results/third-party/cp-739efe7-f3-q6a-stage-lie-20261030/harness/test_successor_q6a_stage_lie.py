"""Q6-A-S1-stage-lie-plain-journal: SUCCESSOR case (separately named; NOT the original test).

Reuses, BY IMPORT (no copy), the helpers/fixture of the ORIGINAL tests/test_claim_journal_stage.py at CP 739efe7:
  flow (fixture, params 'journal' and 'journal+operation-identity'), _claim, _verify, _refutations.
Asserts ONLY the stage-lie half of test_negative_incorrect_journal_linkage_is_detected. NO check-id linkage assertion.
Subordinate of the lead builder session; not independent.
"""
from __future__ import annotations

import copy

from tests.test_claim_journal_stage import _claim, _refutations, _verify, flow  # noqa: F401  (flow = fixture)


def test_stage_lie_is_refuted(flow, record_property):
    """Mutation: every check_events entry with stage == 'claim' gets stage = 'decision'. Original half-2 assertion verbatim:
    any(c.verdict == 'refuted' for c in _verify(bad2).checks)."""
    _, rec = _claim(flow)
    bad2 = copy.deepcopy(rec)
    n = 0
    for e in bad2["check_events"]:
        if e["stage"] == "claim":
            e["stage"] = "decision"
            n += 1
    assert n >= 1, "precondition: the record must contain claim-stage check_events to rewrite"
    record_property("rewritten_rows", n)
    ev = _verify(bad2)
    record_property("refutations", repr(sorted(_refutations(ev))))
    record_property("overall", ev.overall)
    assert any(c.verdict == "refuted" for c in ev.checks)


def test_unmutated_record_has_no_stage_binding_refutation(flow, record_property):
    """NEGATIVE control: the unmutated record yields no refuted finding with code journal_stage_binding."""
    _, rec = _claim(flow)
    ev = _verify(rec)
    record_property("refutations", repr(sorted(_refutations(ev))))
    record_property("overall", ev.overall)
    assert not ev.crashed
    assert not any(code == "journal_stage_binding" for _cid, code in _refutations(ev))
