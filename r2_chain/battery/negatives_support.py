"""Shared helpers of the R2 negative-path rows (Worker B; BUILDER_TESTED developer test code, NOT independent qualification). Uses ONLY the public harness API.

Every negative is paired, in the SAME test, with a CONTROL POSITIVE that imports the genuine retained record with the same operator inputs (so a refusal cannot be a broken
fixture), and every refusal asserts the exact typed code, the verifier call count and (where the Registry adapter was reached) the refusing layer; refuse_import asserts that
no bundle (hence no admission/success marker) was returned.
"""
from __future__ import annotations

import copy
import dataclasses
import json

import pytest

import harness as H
import real_cp_record as R

UNV = "registry_evidence_unverified:"
ALL_PASS = {"pass"}


def control(rr, *, operator=None):
    """CONTROL POSITIVE: the genuine retained record imports under the explicit F4 profile; 11 layers pass; exact claim-A markers; one verifier call."""
    spy = H.Spy()
    bundle, _ = H.import_f4(rr.record, operator or rr.operator, proposal=rr.proposal, verifier=spy)
    H.assert_exact_claim_a_markers(bundle, profile=H.SELECTOR_F4)
    H.check("CONTROL genuine record admitted (1 verifier call, 11 layers pass, claim-A markers exact)",
            spy.calls == 1 and spy.last["ok"] is True and set(spy.last["layers"].values()) == ALL_PASS and len(spy.last["layers"]) == 11)
    return bundle


class Cases:
    """Collects the sub-cases of one row (expected vs observed code, layer, verifier calls) into the row notes; also guards that the genuine record is never edited."""

    def __init__(self, rr):
        self.rr, self.before, self.rows = rr, H.jdump(rr.record), []

    def refuse(self, name, record, code, *, operator=None, proposal=None, calls=None, layers=None, spy=None, message_has=None, **kw):
        res = H.refuse_import(record, operator or self.rr.operator, proposal or self.rr.proposal, code, verifier_calls=calls, layers=layers, spy=spy, **kw)
        if message_has:
            H.check("%s: refusal text mentions %r" % (name, message_has), message_has in res.message, res.message)
        self.rows.append(dict(case=name, expected=code, observed=res.code, verifier_calls=res.calls,
                              layers_refused=None if res.spy is None or not res.spy.verdicts or not isinstance(res.spy.last, dict) or "layers" not in res.spy.last
                              else sorted(k for k, v in res.spy.last["layers"].items() if v == "refuse")))
        return res

    def done(self):
        H.note("cases", self.rows)
        H.check("genuine retained record untouched by all tampered copies", H.jdump(self.rr.record) == self.before)
        H.check("every sub-case refused with its exact expected code", all(c["expected"] == c["observed"] for c in self.rows), self.rows)


def trust_with(rr, spy=None, **over):
    """A Replay trust object = the operator's inputs with some RegistryEvidenceTrust fields replaced (e.g. source revisions, snapshot ref). Pass to import via
    `registry_evidence_trust=` and `pass_trust=False`."""
    spy = spy or H.Spy()
    return dataclasses.replace(rr.operator.as_replay_trust(verifier=spy), **over), spy


def other_genuine(**kw):
    return R.produce_real(**kw)
