"""L5 revocation-propagation probe over enumerated authority holders, built on the N4 refusal-test template.

SPDX-License-Identifier: Apache-2.0

``run_holder_probe`` revokes one grant at the control-plane resolver, then has every enumerated holder attempt the effect with
the credential it actually holds:

* a ``routed`` holder goes through the control plane's effect-time check and the runtime executor (a refusal row is expected);
* a ``self_credentialed`` holder writes to the destination with its own credential and never reaches the control plane
  (nothing records the outcome; the destination, which knows nothing of the revocation, accepts it).

The probe follows the template's legs for the routed holder (a negative, b refusal row, c positive control bound to the policy
version observed at the enforcement point) and classifies every holder with the template's ``classify_holders``. Without a
positive control that reached the destination the verdict is ``inconclusive``: a refusal alone cannot be attributed to the
revocation (it could be an unrelated error), so no holder is reported as witnessed.

The result dict is the proposed ``probe_result`` shape (see the PR body); it is a test-side record, not a contract.
Limits: only enumerated holders are probed. A holder nobody listed stays invisible, so the inventory is the control.
"""
from __future__ import annotations

import pathlib
import sqlite3

import pytest

import _refusal_template as T
from _oi_flow import Flow

REVOCATION = "grant status -> revoked at the control-plane resolver"
SELF_EFFECT = "urn:cognous:effect:self-credentialed-holder-1"


class ProbeAdapter(T.Adapter):
    """Template adapter over the operation-identity flow, default path (no profile), grant revoked at the resolver."""

    def build(self, work, mp):
        return Flow(work, mp, identity=False)

    def apply_change(self, flow):
        next(iter(flow.r.statuses.values())).status = "revoked"

    def execute(self, flow):
        return flow.run(flow.d1)

    def effect_id(self, flow):
        return flow.d1.effect_id

    def ledger_effect_ids(self, flow):
        return flow.ledger_effect_ids()

    def refusal_rows(self, flow):
        return [r.model_dump(mode="json") for r in flow.record().refusals]

    def disable_refusal_writer(self, flow):
        flow.f.records.append_refusal = lambda value: None  # instance level; the refusal still blocks the effect

    def policy_versions_observed_at_enforcement(self, flow, stage):
        wanted = "effect" if stage in (None, "effect_time_revalidation") else stage
        out: dict[str, str] = {}
        for check in [c for c in flow.record().resolution_checks if c.stage == wanted][-1:]:
            for item in check.inputs:
                if item.input_type == "policy" and (item.observed or {}).get("version") is not None:
                    out[item.input_id] = str(item.observed["version"])
        return out


def self_credentialed_write(flow, effect_id: str) -> None:
    """The holder holds a credential for the destination itself: it inserts its own effect row, bypassing the control plane."""
    conn = sqlite3.connect(pathlib.Path(flow.dest.path), timeout=10, isolation_level=None)
    try:
        conn.execute("INSERT INTO effects(effect_id,operation_digest,grant_id,target,amount,unit,payload_json,state) "
                     "VALUES(?,?,?,?,?,?,?,?)", (effect_id, "self-credentialed", flow.d1.binding.grant_id, flow.p.target, 1.0, "USD", "{}", "applied"))
    finally:
        conn.close()


SPEC = T.RefusalSpec(
    name="revocation_reaches_routed_holder", reasons=("grant_revoked",), changed_inputs=(T.ChangedInput("grant", "urn:cognous:grant:routine-1"),),
    provenance=T.Provenance("run", "control plane main fd0d5e0 and runtime main 6bfb77ee, pristine checkouts, this probe on the default path "
                                   "(no profile): one refusal (routed holder) and one unrecorded outcome (self-credentialed holder)"),
    revocation=True)

HOLDERS = [
    {"holder_id": "urn:cognous:holder:refund-service", "kind": "routed", "enforcement_point": "control-plane effect-time check"},
    {"holder_id": "urn:cognous:holder:legacy-batch-job", "kind": "self_credentialed", "enforcement_point": "destination credential (none)"},
]


def run_holder_probe(work: pathlib.Path, *, holders=HOLDERS, with_control: bool = True, break_control: bool = False,
                     adapter: ProbeAdapter | None = None) -> dict:
    adapter = adapter or ProbeAdapter()
    mps: list[pytest.MonkeyPatch] = []

    def fresh(label: str):
        path = work / label
        path.mkdir(parents=True, exist_ok=False)
        mp = pytest.MonkeyPatch()
        mps.append(mp)
        return adapter.build(path, mp)

    try:
        flow = fresh("probed")
        adapter.apply_change(flow)
        attempts = []
        for holder in holders:
            if holder["kind"] == "routed":
                effect_id = adapter.effect_id(flow)
                adapter.execute(flow)
            else:
                effect_id = SELF_EFFECT
                self_credentialed_write(flow, effect_id)
            attempts.append({**holder, "attempted_effect_id": effect_id, "effect_ids": [effect_id]})
        ledger = adapter.ledger_effect_ids(flow)
        rows = adapter.refusal_rows(flow)
        routed = next((h for h in attempts if h["kind"] == "routed"), None)

        inconclusive: list[str] = []
        control: dict = {"ran": with_control}
        if routed is not None:
            try:
                T.check_negative(adapter, flow, routed["attempted_effect_id"])           # leg (a)
                refusal = T.check_refusal_row(adapter, flow, routed["attempted_effect_id"], SPEC)  # leg (b)
            except T.RefusalTemplateFailure as failure:
                inconclusive.append(f"routed holder leg ({failure.leg}) failed: {failure.detail}")
                refusal = None
            if not with_control:
                inconclusive.append("no positive control was run")
            elif refusal is not None:
                control_flow = fresh("control")
                if break_control:
                    control_flow.r.identity_status = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("unrelated resolver failure"))
                adapter.execute(control_flow)
                try:
                    control.update(T.check_control(adapter, control_flow, routed["attempted_effect_id"], SPEC, refusal))   # leg (c)
                    control["reached_destination_once"] = True
                except T.RefusalTemplateFailure as failure:
                    control.update(reached_destination_once=False, failure=failure.detail)
                    inconclusive.append(f"positive control did not reach the destination under the same call: {failure.detail}")
        verdict = "inconclusive" if inconclusive else "conclusive"
        # Unattributable refusals are never counted: without a valid control every holder stays coverage_unknown.
        classification = T.classify_holders(attempts, [] if inconclusive else rows)
        outcomes = []
        for h in attempts:
            refused = any(r.get("effect_id") == h["attempted_effect_id"] for r in rows)
            landed = h["attempted_effect_id"] in ledger
            outcomes.append({"holder_id": h["holder_id"], "kind": h["kind"], "enforcement_point": h["enforcement_point"],
                             "attempted_effect_id": h["attempted_effect_id"],
                             "outcome": "refused" if refused and not landed else ("effect_landed_unrecorded" if landed and not refused else "no_outcome"),
                             "ledger_rows": ledger.count(h["attempted_effect_id"]),
                             "refusal_ids": [r["refusal_id"] for r in rows if r.get("effect_id") == h["attempted_effect_id"]]})
        return {"scenario": "revocation_propagation", "authority_change": REVOCATION, "verdict": verdict,
                "inconclusive_reasons": inconclusive, "control": control, "holders": outcomes, **classification,
                "provenance": {"kind": SPEC.provenance.kind, "source": SPEC.provenance.source}}
    finally:
        for mp in mps:
            mp.undo()
