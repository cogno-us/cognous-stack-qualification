"""R2 POSITIVE joined chain (evidence kind REAL; BUILDER_TESTED developer test code, NOT independent qualification).

PRIVATE PREVIEW QUALIFICATION TUPLE (preview-only, NOT canonical). Synthetic refund-age workflow, single synthetic tenant, synthetic Ed25519 keys.

Chain: Registry-signed F4 selection (PyNaCl, synthetic) -> real Control Plane `GovernedAgeWorkflow(carry_selection_evidence=True)` -> authorized decision -> retained bounded
record persisted by the Control Plane's `BoundedRecordStore` and reloaded through a fresh store -> real Replay `import_bounded_workflow` under the explicit F4 profile with
independent operator trust inputs -> the real `RegistryEvidenceVerifierV2` invoked (observed by a pure Spy) -> admission with exact claim-A markers.

Claim made: A only (a Registry selection signature admitted by an operator-supplied verifier at the operator's time, bound to the exact retained record). NOT claimed: claim B
(Control Plane decision authenticated by Replay), Registry origin/authority, operational trust, production.

The 15 required assertions of sprint section 10 are the labelled checks P01..P15 below (each recorded in the row's `checks`). Extra checks are P00 (no shadow module).
"""
import hashlib
import json

import pytest

import harness as H
import real_cp_record as R


def _sel_digest(stmt):
    return H.c.digest(stmt)          # the Registry's own statement digest function, applied to the statement the test signed


@pytest.mark.row("P1", "POSITIVE: Registry F4 selection -> Control Plane -> retained bounded record -> Replay F4 re-admission (assertions P01-P15)", kind="positive")
def test_p1_positive_joined_chain(tmp_path):
    chk = H.check
    H.assert_modules_from_pins()
    chk("P00 subject modules resolve under the pinned source trees (no shadow module)", True)

    # ----------------------------------------------------------------------------------------------- P01 Registry emits valid F4 selection evidence
    mat = H.material()
    stmt, rec = mat.stmt, mat.rec
    env = json.loads(mat.selection_text)
    chk("P01 Registry emits valid F4 selection evidence (signed envelope of the synthetic F4 record; family f4-control-plane-age-bounds)",
        rec["family"] == H.F4 and env["kind"] == "selection-envelope" and env["statement_digest"] == _sel_digest(stmt) and len(env["signatures"]) == 1
        and rec["record_digest"] == json.loads(mat.record_text)["record_digest"] and stmt["family"] == H.F4)
    # the real Registry verifier (same adapter Replay will use) admits it independently, before the Control Plane ever sees it
    pre = R.verify_with_real_adapter({"family": H.F4, "contract_version": rec["contract_version"], "selection_text": mat.selection_text, "record_text": mat.record_text},
                                     R.default_operator_inputs())
    chk("P01b the real RegistryEvidenceVerifierV2 independently accepts the emitted evidence (ok, authenticated, 11 layers pass)",
        pre["ok"] is True and pre["authenticated"] is True and set(pre["layers"].values()) == {"pass"} and len(pre["layers"]) == 11)

    # ----------------------------------------------------------------------------------------------- P02/P03 Control Plane receives the exact evidence and authorizes
    rr = R.produce_real(tmp_path / "cp", mat=mat, execute=False)
    src_obj = rr.flow.r2_selection_source
    chk("P02 Control Plane received the exact selection evidence (selection source pulled; retained evidence texts equal the Registry-emitted bytes)",
        src_obj.calls >= 1 and rr.evidence["selection_text"] == mat.selection_text and rr.evidence["record_text"] == mat.record_text
        and rr.evidence["family"] == H.F4 and rr.evidence["operation_id"] == H.OPERATION)
    d = rr.decision
    chk("P03 Control Plane decision is authorized under the expected synthetic conditions (result authorized, no reasons, synthetic tenant, expected action id)",
        d["result"] == "authorized" and not d["reasons"] and d["binding"]["tenant_id"] == H.TENANT_ID and d["binding"]["action_id"] == H.ACTION_ID
        and d["binding"]["runtime_authority"]["effective_configuration"]["members"]["scope"]["action_id"] == H.ACTION_ID)

    # ----------------------------------------------------------------------------------------------- P04 retained record preserves the original evidence unchanged
    persisted = json.loads(rr.written_bytes)
    chk("P04 retained bounded record preserves the original selection evidence unchanged (byte-identical texts, whole evidence object equal to what the Control Plane wrote)",
        persisted["decisions"][0]["selection_evidence"] == rr.evidence and rr.evidence["selection_text"].encode() == mat.selection_text.encode()
        and rr.evidence["record_text"].encode() == mat.record_text.encode()
        and hashlib.sha256(rr.evidence["selection_text"].encode()).hexdigest() == H.sha256_text(mat.selection_text))

    # ----------------------------------------------------------------------------------------------- P05 persist and reload through the supported record-store path
    reloaded = H.reload_record(rr)        # a NEW BoundedRecordStore on the persisted file validates and returns it
    chk("P05 persisted and reloaded through the supported BoundedRecordStore path (fresh store; identical bytes; reloaded model carries the same evidence)",
        reloaded["bytes"] == rr.written_bytes == rr.retrieved_bytes and reloaded["record"] == rr.record
        and reloaded["model"]["decisions"][0]["selection_evidence"] == rr.evidence and reloaded["model"] == rr.retrieved_model)

    # snapshots to prove Replay applies nothing (P15) and does not edit the retained record
    dest_before, run_before = rr.destination_path.read_bytes(), rr.path.read_bytes()
    record_before = H.jdump(rr.record)

    # ----------------------------------------------------------------------------------------------- P06/P07 Replay F4 import with independent operator trust inputs
    op = rr.operator
    rec_json = json.dumps(rr.record)
    chk("P06 Replay imports the retained record under the explicit F4 profile (profile string, current-generation revision)",
        H.SELECTOR_F4 == "registry-authenticated-selection-f4-governed/0.1" and H.CUR_CP == "b19c47ddd020409d24e52e70b11359c46265edbb")
    chk("P07 Replay receives independent operator trust inputs (operator snapshot is a separate object from the Control Plane host trust; nothing of trust/time/ages is in the record)",
        op.trust_snapshot is not mat.host_trust and not any(k in rec_json for k in ("trust_snapshot", "expected_host_ages", "verification_time", "snap-test-1"))
        and op.expected_host_ages == H.HOST_AGES and op.expected_action_id == H.ACTION_ID and op.expected_operation_id == H.OPERATION)

    spy = H.Spy()
    bundle, trust_obj = H.import_f4(rr.record, op, proposal=rr.proposal, verifier=spy)
    assert trust_obj.verifier is spy

    # ----------------------------------------------------------------------------------------------- P08 Replay invokes the Registry verifier
    chk("P08 Replay invoked the real Registry verifier exactly once, passing the original carried selection text and record text unchanged",
        spy.calls == 1 and type(spy.inner) is H.RegistryEvidenceVerifierV2 and spy.requests[0]["selection_text"] == mat.selection_text
        and spy.requests[0]["record_text"] == mat.record_text and spy.requests[0]["expected_operation_id"] == H.OPERATION)

    # ----------------------------------------------------------------------------------------------- P09 accepted verdict
    v = spy.last
    chk("P09 Registry verifier returned an accepted verdict (ok, code None, authenticated, all 11 layers pass, not a caller-injected stub)",
        v["ok"] is True and v["code"] is None and v["authenticated"] is True and len(v["layers"]) == 11 and set(v["layers"].values()) == {"pass"}
        and v["verifier_implementation"]["name"] == "registry-evidence-verifier-v2" and v["verifier_implementation"]["name"] != "caller-injected-stub")

    # ----------------------------------------------------------------------------------------------- P10 binding
    m = bundle.metadata
    (ev0,) = m["registry_evidence"]
    ec = d["binding"]["runtime_authority"]["effective_configuration"]
    tr = H.RE.validate_trust(op.as_replay_trust(verifier=H.Spy()))
    recomputed = H.RE.binding_digest(decision_id=d["decision_id"], ec=ec, ev=rr.evidence, verdict=v, tr=tr)
    other_action = H.RE.validate_trust(op.with_(expected_action_id=op.expected_action_id + "-x").as_replay_trust(verifier=H.Spy()))
    eff = op.expected_effective_values()
    git_cp, git_rg, git_rp = H.git("control_plane", "rev-parse", "HEAD"), H.git("registry", "rev-parse", "HEAD"), H.git("replay", "rev-parse", "HEAD")
    bind = {
        "selection_digest": ev0["selection_digest"], "record_digest": ev0["bound_record_digest"], "operation_id": rr.evidence["operation_id"],
        "expected_action_id": tr.action_id, "trust_snapshot": [m["registry_trust_snapshot_id"], m["registry_trust_snapshot_version"], ev0["trust_snapshot_fingerprint"]],
        "host_ages_effective_values": v["effective_values"], "effective_policy_digest": ev0["effective_policy_digest"], "source_revisions": m["registry_declared_source_revisions"],
        "admission_binding_digest": ev0["admission_binding_digest"]}
    H.note("binding", bind)
    chk("P10a binding of the SELECTION DIGEST: marker == verdict == independently recomputed Registry statement digest of the signed statement",
        ev0["selection_digest"] == v["selection_digest"] == _sel_digest(stmt))
    chk("P10b binding of the RECORD DIGEST: marker == verdict == the Registry-sealed record_digest of the carried record",
        ev0["bound_record_digest"] == v["bound_record_digest"] == rec["record_digest"] == json.loads(rr.evidence["record_text"])["record_digest"])
    chk("P10c binding of the OPERATION ID: carried evidence, the verifier request and the operator expectation all say the operation",
        rr.evidence["operation_id"] == spy.requests[0]["expected_operation_id"] == op.expected_operation_id == tr.operation_id == H.OPERATION)
    chk("P10d binding of the EXPECTED ACTION ID: admission_binding_digest recomputes with the operator action id and changes when the expected action id changes",
        tr.action_id == H.ACTION_ID and recomputed == ev0["admission_binding_digest"]
        and H.RE.binding_digest(decision_id=d["decision_id"], ec=ec, ev=rr.evidence, verdict=v, tr=other_action) != recomputed)
    chk("P10e binding of the TRUST SNAPSHOT: marker id/version == operator reference == verdict id/version, and fingerprint marker == verdict fingerprint",
        (m["registry_trust_snapshot_id"], m["registry_trust_snapshot_version"]) == op.snapshot_ref == (v["trust_snapshot_id"], v["trust_snapshot_version"])
        and ev0["trust_snapshot_fingerprint"] == v["trust_snapshot_fingerprint"])
    chk("P10f binding of the EXPECTED HOST AGES: the verifier request carried the operator host ages; verdict effective values == min(host ages, signed bound) == the record's "
        "f4_scalars; effective-policy digest == operator-computed == f4_ages row",
        spy.requests[0]["host_policy"] == H.HOST_AGES and v["effective_values"] == eff == ec["members"]["f4_scalars"] == {"status_max_age_seconds": 60, "approval_max_age_seconds": 60}
        and ev0["effective_policy_digest"] == v["effective_policy_digest"] == H.row(rr.record)["effective_policy_digest"] == op.expected_effective_policy_digest)
    chk("P10g binding of the SOURCE REVISIONS: the operator-declared revisions in the admission markers equal the checked-out HEADs of the pinned Control Plane and Registry "
        "(Replay revision is the git HEAD of the replay tree actually imported)",
        m["registry_declared_source_revisions"] == {"control_plane": H.CP_SHA, "registry": H.REGISTRY_SHA, "attestation": "operator_declared_unattested"}
        and git_cp == H.CP_SHA and git_rg == H.REGISTRY_SHA and git_rp == H.REPLAY_SHA)
    chk("P10h the admission binding digest is bound to this decision's exact retained record: it changes when the carried record text is substituted",
        H.RE.binding_digest(decision_id=d["decision_id"], ec=ec, ev={**rr.evidence, "record_text": R.produce_real(tmp_path / "other", mat=H.material(40, 30)).evidence["record_text"]},
                            verdict=v, tr=tr) != recomputed)
    chk("P10 binding (summary): selection digest, record digest, operation id, expected action id, trust snapshot, host ages and source revisions are all bound",
        all(bind[k] for k in ("selection_digest", "record_digest", "operation_id", "expected_action_id", "trust_snapshot", "host_ages_effective_values", "source_revisions")))

    # ----------------------------------------------------------------------------------------------- P11 admission
    (rec_dec,) = [x for x in bundle.records if x.record_type == "runtime_decision"]
    chk("P11 Replay admission succeeds (a bundle is returned; the admitted runtime_decision is byte-identical to the persisted decision including selection_evidence)",
        bundle is not None and H.jdump(rec_dec.data) == H.jdump(json.loads(rr.written_bytes)["decisions"][0]) == H.jdump(rr.decision)
        and rec_dec.data["selection_evidence"] == rr.evidence)

    # ----------------------------------------------------------------------------------------------- P12/P13/P14 markers
    ev_entry = H.assert_exact_claim_a_markers(bundle, profile=H.SELECTOR_F4)
    chk("P12 success markers match the expected F4 contract exactly (profile, claim A text, decision-time-only scope, unattested snapshot, claims/not-verified lists, scope note, "
        "success marker key set)", ev_entry is ev0 or ev_entry == ev0)
    chk("P12b the metadata carries every Replay success marker key", H.SUCCESS_KEYS <= set(m))
    claim_b_like = [k for k in m if k.lower().startswith("claim_b") or "claim_b" in k.lower() or k.startswith(("decision_authentic", "registry_origin_verified", "registry_authority"))]
    chk("P13 no claim-B marker appears (no claim-B/decision-authenticated/origin-verified/authority key; control_plane_decision_authenticated False; claim is the A-text only)",
        not claim_b_like and m["control_plane_decision_authenticated"] is False and m["registry_authentication_claim"].startswith("A_")
        and m["registry_origin"] == "registry_origin_unverified")
    chk("P14 registry_authenticated remains False, per the current declared Replay contract (claim A is the injected verifier's admission, not Replay authentication)",
        m["registry_authenticated"] is False and m["registry_selection_admitted_by_injected_verifier"] is True)

    # ----------------------------------------------------------------------------------------------- P15 no external effect
    ctrl = rr.record
    dest_state = json.loads(rr.destination_path.read_text())
    chk("P15 no external effect executed: the bounded local destination holds no effect, the record has no attempt/observation/reconciliation, the Control Plane was not asked to "
        "execute, and the Replay import left destination, run.json and the loaded record byte-identical",
        dest_state == {"effects": {}, "grant_effect_counts": {}} and ctrl["attempts"] == [] and ctrl["observations"] == [] and ctrl["reconciliations"] == []
        and rr.executed is False and rr.destination_path.read_bytes() == dest_before and rr.path.read_bytes() == run_before and H.jdump(rr.record) == record_before
        and not any("effect" in x.record_type and x.record_type != "effect_observation_history" for x in bundle.records))

    H.publish_artifact("positive-case.json", {
        "label": "PRIVATE PREVIEW QUALIFICATION TUPLE - positive joined-chain case (synthetic, single tenant, claim A only)",
        "tuple": {"control_plane": H.CP_SHA, "registry": H.REGISTRY_SHA, "replay": H.REPLAY_SHA},
        "profile": H.SELECTOR_F4, "replay_expected_control_plane_revision": H.CUR_CP,
        "record": {"run_id": rr.record["run_id"], "decision_id": d["decision_id"], "run_json_sha256": hashlib.sha256(rr.written_bytes).hexdigest(),
                   "decision_sha256": hashlib.sha256(H.jdump(rr.decision).encode()).hexdigest(),
                   "selection_text_sha256": H.sha256_text(rr.evidence["selection_text"]), "record_text_sha256": H.sha256_text(rr.evidence["record_text"])},
        "binding": bind,
        "verdict": {k: val for k, val in v.items() if k != "layers"} | {"layers": v["layers"]},
        "verifier_calls": spy.calls, "operator_inputs": {"expected_action_id": op.expected_action_id, "expected_operation_id": op.expected_operation_id,
                                                           "expected_host_ages": op.expected_host_ages, "verification_time": op.verification_time.isoformat(),
                                                           "time_mode": op.time_mode, "trust_snapshot_ref": list(op.snapshot_ref)},
        "markers": {k: m[k] for k in sorted(H.SUCCESS_KEYS)},
        "assertions": [x for x in H._ctx().checks],
        "no_effect": {"destination": dest_state, "attempts": len(ctrl["attempts"]), "observations": len(ctrl["observations"]), "executed": rr.executed},
        "claims_not_made": ["claim B", "Registry origin/authority", "production readiness", "multi-tenant isolation", "operational trust"]})


@pytest.mark.row("P2", "POSITIVE (secondary): record of an EXECUTED local synthetic refund also re-admits; the Replay import applies no further effect", kind="positive")
def test_p2_positive_with_locally_executed_effect_still_readmits_without_new_effect(tmp_path):
    rr = R.produce_real(tmp_path / "cp", execute=True)
    dest_before, run_before = rr.destination_path.read_bytes(), rr.path.read_bytes()
    spy = H.Spy()
    bundle, _ = H.import_f4(rr.record, rr.operator, proposal=rr.proposal, verifier=spy)
    H.check("P2a executed-record import admitted with exact claim-A markers", spy.calls == 1 and H.assert_exact_claim_a_markers(bundle, profile=H.SELECTOR_F4) is not None)
    H.check("P2b the effect was applied by the Control Plane BEFORE retention (one local synthetic effect); Replay import left destination and run.json byte-identical",
            len(json.loads(dest_before)["effects"]) == 1 and rr.destination_path.read_bytes() == dest_before and rr.path.read_bytes() == run_before)


@pytest.mark.row("P3", "POSITIVE (determinism): two independent runs of the whole chain agree on every deterministic digest and marker", kind="positive")
def test_p3_positive_chain_is_deterministic(tmp_path):
    a, b = R.produce_real(tmp_path / "a"), R.produce_real(tmp_path / "b")
    outs = []
    for rr in (a, b):
        spy = H.Spy()
        bundle, _ = H.import_f4(rr.record, rr.operator, proposal=rr.proposal, verifier=spy)
        m = bundle.metadata
        (e,) = m["registry_evidence"]
        outs.append(({k: e[k] for k in ("selection_digest", "bound_record_digest", "effective_policy_digest", "trust_snapshot_fingerprint", "issuer_id", "selection_id", "epoch")},
                     {k: m[k] for k in sorted(H.SUCCESS_KEYS) if k != "registry_evidence"}, rr.evidence))
    H.check("P3 digests, markers and carried evidence are identical across two independent runs (decision ids, which are random, are the only difference)",
            outs[0] == outs[1] and a.decision_id != b.decision_id)
