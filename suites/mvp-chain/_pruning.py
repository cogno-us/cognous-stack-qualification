"""A2 scenario ``nc_ledger_pruning``: operation-ledger PRUNING on route B (proposed; Qualification owns the verdict).

SPDX-License-Identifier: Apache-2.0

Documented limitation (Control Plane 7a4bcd40 ``docs/bounded_authorization_effect.md`` "Approval, payload policy and the operation
ledger: stated limits", pinned for the Control Plane's own workflow destination by ``tests/test_known_limits.py::
test_removed_operation_rows_let_a_revision_2_decision_authorize_but_the_destination_refuses_known_limit``):

  The operation-identity ledger has NO retention rule. If its rows (``operations`` in the run record) are removed, a revision-2
  decision that would hold as ``operation_renewal_unrecorded`` is ``authorized``; the destination still refuses the second effect
  (``operation_already_committed``). A retention rule is a freeze item.

What this scenario exercises, on the exact pinned tuple and on ROUTE B (the Control Plane test does not touch route B), reusing
``_chain.Ctx`` (real decision, real claim provisioning, ``AtomicLocalControlPlaneExecutor`` on the atomic operation-identity
destination, independent read-only SQLite readback):

  1. one effect committed for an operation id (revision 1);
  2. the issuer publishes revision 2 WITHOUT recording the renewal. CONTROL arm (ledger intact): the Control Plane decision is
     ``hold`` / ``operation_renewal_unrecorded`` (so the harness can tell the two states apart);
  3. PRUNED arm: the ``operations`` rows are removed from the Control Plane run record (exactly the operation the disclosed test uses);
     the same revision-2 decision is now ``authorized`` with no reasons: THIS IS THE DOCUMENTED LIMIT, recorded and NOT judged here;
  4. a claim for the new decision is provisioned and executed through route B. The destination's own ledger
     (``operation_effects_v1``, a separate store that pruning of the run record does not touch) refuses it: a RETURNED denied result
     ``operation_already_committed``, no new effect, the new claim stays ``issued``.

Not claimed (the pinned code provides no more): the Control Plane does not detect the pruning or refuse the decision; there is no
retention rule; if the DESTINATION ledger were also lost (see the ``prune_destination`` negative control) nothing in the pinned code
prevents a second effect. The protection that exists is the destination-side operation guard only. The pinned Verifier statement
("rejects the pruned record") is recorded as an informational observation, not as a predicate of the mandatory row.

Raw observations only; no verdict is computed here.
"""
from __future__ import annotations

import json
import pathlib
import sqlite3

import _chain
import _state

OPERATION = "op-order-100/refund-1"


def _renew_authority(ctx, *, record_renewal: bool) -> None:
    """Revision-2 renewal of the same operation (source: ``_chain.nc_duplicate`` second block / suites/operation-identity ``_renew``).

    ``record_renewal=False`` publishes revision 2 and re-binds a new approval WITHOUT writing the renewal row to the ledger."""
    flow, dest = ctx.flow, ctx.dest
    flow.publish_revision("2")
    c = flow.r.contexts[flow.tba.PROFILE]
    grant = c["grant"]
    old = grant["approval_refs"][0]
    new = old.rsplit("-", 1)[0] + "-2"
    approval = flow.r.approvals[old].model_copy(deep=True)
    approval.approval_ref = new
    flow.r.approvals[new] = approval
    grant["approval_refs"] = [new]
    ra = c["runtime_authority"]
    for item in ra["required_inputs"]:
        if item["input_id"] == old:
            item["input_id"] = new
    ra["required_inputs"] = sorted(ra["required_inputs"], key=lambda x: (x["input_type"], x["input_id"]))
    ra["required_inputs_digest"] = flow.cp.commitment(ra["required_inputs"])
    flow.tra.bind_approval(flow.r, flow.f.runtime_authority_profile or flow.cfg)
    if record_renewal:
        flow.f.record_renewal(flow.OPERATION_ID, to_revision="2", written_by=flow.ISSUER, now=flow.NOW)
    dest.set_grant_status(flow.d1.binding.grant_id, status="active", revision="2")


def _ro(ctx):
    return sqlite3.connect(pathlib.Path(ctx.dest.path).resolve().as_uri() + "?mode=ro", uri=True, timeout=10)


def _destination_operation_rows(ctx) -> int:
    conn = _ro(ctx)
    try:
        return conn.execute("SELECT COUNT(*) FROM operation_effects_v1").fetchone()[0]
    finally:
        conn.close()


def run(work, *, prune_cp: bool = True, prune_destination: bool = False, verifier: bool = True, retain: bool = True) -> dict:
    """One flow. ``retain=False`` writes no result artifact (negative controls must never overwrite the mandatory run's artifacts). ``prune_cp=False`` and ``prune_destination=True`` are NEGATIVE-CONTROL variants (a mutation of the scenario), never the mandatory arm."""
    work = pathlib.Path(work)
    ctx = _chain.Ctx(work / "pruning", wide=True)  # wide: the cumulative cap allows a second effect, so only operation identity can prevent it
    obs: dict = {"variant": {"prune_cp": prune_cp, "prune_destination": prune_destination}}
    try:
        flow, dest = ctx.flow, ctx.dest
        flow.OPERATION_ID = OPERATION
        original_effect = flow.d1.effect_id
        claim1 = ctx.provision()
        first = ctx.execute(claim1.claim_id)
        obs["first"] = {**_chain.result_obs(first), "operation_id": OPERATION, "expected_effect_id": original_effect,
                        "effect_ids": ctx.effect_ids(), "effect_count": ctx.count(), "destination_operation_rows": _destination_operation_rows(ctx)}

        # revision 2 published by the issuer, renewal NOT recorded
        _renew_authority(ctx, record_renewal=False)
        path = work / "pruning" / "cp" / "run.json"
        obs["control"] = {}
        intact = flow.f.decide(flow.p, now=flow.NOW)
        document = json.loads(path.read_text(encoding="utf-8"))
        obs["control"] = {"ledger_rows": len(document.get("operations", [])), "decision_result": intact.result, "decision_reasons": list(intact.reasons),
                          "run_json_sha256": _chain.sha256_bytes(path.read_bytes())}
        if retain:
            _chain.retain("nc_ledger_pruning/cp-run-record.intact.json", path.read_bytes())

        pruned = {"prune_cp": prune_cp, "rows_before": len(document.get("operations", [])), "rows_removed": 0, "rows_after": None}
        if prune_cp:
            document["operations"] = []
            path.write_text(json.dumps(document), encoding="utf-8")  # the disclosed test's exact operation
            pruned["rows_removed"] = pruned["rows_before"]
        pruned["rows_after"] = len(json.loads(path.read_text(encoding="utf-8")).get("operations", []))
        pruned["run_json_sha256_pruned"] = _chain.sha256_bytes(path.read_bytes())
        if retain:
            _chain.retain("nc_ledger_pruning/cp-run-record.pruned.json", path.read_bytes())
        if prune_destination:  # negative-control mutation of the DESTINATION ledger (a disposable store)
            conn = sqlite3.connect(str(dest.path), timeout=10)
            try:
                conn.execute("DELETE FROM operation_effects_v1")
                conn.commit()
            finally:
                conn.close()
        pruned["destination_operation_rows_before_second"] = _destination_operation_rows(ctx)

        d2 = flow.f.decide(flow.p, now=flow.NOW)
        pruned["cp_decision_result"], pruned["cp_decision_reasons"] = d2.result, list(d2.reasons)
        pruned["cp_decision_authorized_on_pruned_record"] = d2.result == "authorized"
        pruned["second_effect_id_differs_from_first"] = d2.effect_id != original_effect
        pruned["claim_issued"], pruned["second_execute"] = False, None
        if d2.result == "authorized":
            claim2 = _chain.attempt(lambda: ctx.provision(d2), _chain.REFUSALS_AUTHORITY)
            if claim2["ok"]:
                pruned["claim_issued"] = True
                second = _chain.attempt(lambda: ctx.execute(claim2["value"].claim_id, d2), _chain.NO_EXCEPTION)
                if second["ok"]:
                    pruned["second_execute"] = {**_chain.result_obs(second["value"]), "raised": False}
                else:  # a raised exception is NOT a documented refusal here: recorded as such, the predicate on .status/.error then fails
                    pruned["second_execute"] = {"status": None, "error": None, "raised": True, "exception": _chain.err_of(second)}
                pruned["claim_state_after_second"] = dest.claim_state(claim2["value"].claim_id)
            else:
                pruned["claim_provision_error"] = _chain.err_of(claim2)
        pruned["effect_ids_after"] = ctx.effect_ids()
        pruned["effect_count"] = ctx.count()
        pruned["only_original_effect"] = pruned["effect_ids_after"] == [original_effect]
        pruned["destination_operation_rows_after"] = _destination_operation_rows(ctx)
        obs["pruned"] = pruned
        if retain:
            import shutil
            _chain.retain("nc_ledger_pruning/cp-run-record.after-second-decision.json", path.read_bytes())
            shutil.copy(dest.path, _state.results_dir() / "artifacts" / "nc_ledger_pruning" / "destination.final.sqlite")
        if verifier and retain:  # informational only (CP document: "the independent verifier rejects the pruned record"); NOT part of the row predicate
            out = _state.results_dir() / "artifacts" / "nc_ledger_pruning" / "verifier"
            v = _chain.run_verifier("pruned", out, record_bytes=path.read_bytes(), proposal=ctx.proposal_json(), manifest=flow.f.manifest)
            obs["verifier_informational"] = {k: v.get(k) for k in ("exit_code", "overall", "refuted_check_ids", "could_not_check_check_ids", "finding_codes", "report_sha256", "module_path_under_pin")}
    finally:
        ctx.close()
    return obs


@_chain.scenario("nc_ledger_pruning")
def nc_ledger_pruning(work):
    """A2 mandatory scenario: the documented pruning limit on route B (control arm + pruned arm)."""
    return run(work)
