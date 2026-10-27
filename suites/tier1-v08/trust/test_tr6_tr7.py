"""TR-6 provenance/evidence integrity (C12) and TR-7 re-examination of the documented V07 LOW findings (C13). Worker C.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import _tr
from _tr import REPO, v4

import os

COMP = Path(os.environ["V08_COMPONENTS_DIR"]).resolve()


def _attest_paths(obj, prefix=""):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            here = f"{prefix}.{k}" if prefix else str(k)
            if "attest" in str(k).lower() or "certif" in str(k).lower() or "independent" in str(k).lower():
                out.append((here, v))
            out.extend(_attest_paths(v, here))
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            out.extend(_attest_paths(v, f"{prefix}[{i}]"))
    return out


def test_c12_guard_evidence_equals_durable_state_and_claims_no_attestation(tmp_path, ev):
    ev["scenario"] = "TR-6"
    ev["expected"] = ("For an executed effect the retained guard evidence equals durable state field by field (activation_ref, policy_generation, "
                      "selection id/epoch, trust snapshot version and fingerprint, log head sequence and hash == store head == host anchor head, "
                      "effective policy digest), the stored receipt row equals the returned receipt, independent_attestation is False, and the only "
                      "attestation/certification/independence-named members anywhere in the receipt or result evidence are independent_attestation=False.")
    G = _tr.newgov(tmp_path, "a")
    env, cid = G.claim()
    res, info = _tr.attempt(G, env, cid)
    st = G.state()
    anchor = json.loads(G.e.anchor.read_text())["anchor"]
    head = G.e.head()
    rc = (res.control_plane_evidence or {}).get("authority_receipt") or {}
    guard = rc.get("selection_guard") or {}
    stored = json.loads(G.receipt())

    def compare():
        checks = {
            "executed": res.status == "executed",
            "guard_present_and_binding_verified": guard.get("result") == "binding_verified" and guard.get("applied") is True,
            "activation_ref": guard.get("activation_ref") == st.activation_ref,
            "policy_generation": guard.get("policy_generation") == st.policy_generation,
            "selection_id": guard.get("selection_id") == st.selection_id,
            "selection_epoch": guard.get("selection_epoch") == st.selection_epoch,
            "participation": guard.get("participation") == st.participation,
            "scope_required": guard.get("scope_required") == st.scope_required,
            "trust_snapshot_version": guard.get("trust_snapshot_version") == st.trust_snapshot_version,
            "trust_snapshot_fingerprint": guard.get("trust_snapshot_fingerprint") == st.trust_snapshot_fingerprint,
            "effective_policy_digest": guard.get("effective_policy_digest") == v4.effective_digest(),
            "log_head_sequence_vs_store": guard.get("log_head_sequence") == head[0] == st.log_head_sequence,
            "log_head_hash_vs_store": guard.get("log_head_hash") == head[1] == st.log_head_hash,
            "log_head_vs_host_anchor": (guard.get("log_head_sequence"), guard.get("log_head_hash")) == (anchor["head_sequence"], anchor["head_entry_hash"]),
            "receipt_row_equals_returned_receipt": stored == rc,
            "independent_attestation_is_false": guard.get("independent_attestation") is False,
            "store_known_after": G.e.verify().state == "known",
            "single_effect_single_receipt": G.counts() == (1, 1, 1, 1),
        }
        return {"checks": checks, "ok": all(checks.values())}
    _tr.sub(ev, "guard_evidence_equals_durable_state", compare)

    def attestation_scan():
        found = _attest_paths({"receipt": rc, "control_plane_evidence": res.control_plane_evidence})
        blob = json.dumps({"receipt": rc, "evidence": res.control_plane_evidence}, default=str).lower()
        words = [w for w in ("attested by", "certified", "independently verified", "independently qualified", "production ready", "security cleared")
                 if w in blob]
        only_false = all(v is False for _, v in found) and {p.split(".")[-1] for p, _ in found} <= {"independent_attestation"}
        return {"members_named_attest_certif_independent": [[p, v] for p, v in found], "claim_phrases_present": words,
                "ok": bool(only_false and not words and found)}
    _tr.sub(ev, "no_attestation_claim_beyond_explicit_false", attestation_scan)

    def refusal_evidence():
        R = _tr.newgov(tmp_path, "r")
        env2, cid2 = R.claim()
        R.e.sync(2, revoked_selections=_tr.PAIR)
        res2, info2 = _tr.attempt(R, env2, cid2)
        t = info2["typed"] or {}
        blob = json.dumps(res2.control_plane_evidence, default=str).lower()
        return {"typed": t, "ok": bool(res2.status == "denied" and set(t) == {"code", "refusal_class", "cause"} and "attest" not in blob)}
    _tr.sub(ev, "refusal_evidence_is_typed_data_without_attestation_language", refusal_evidence)
    _tr.verdict(ev)


def _git(repo, *args):
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return p.returncode, p.stdout.strip()


def test_c13_tr7_reexamination_of_v07_low_findings(tmp_path, ev):
    ev["scenario"] = "TR-7"
    ev["expected"] = ("Characterization (no pass is claimed): (a) amount ceiling and target prefixes are owned by the caller's executor policy and are "
                      "NOT part of the Registry payload, so a caller policy wider than anything the Registry bound still executes while a narrower one "
                      "denies locally; (b) the lock-time path does not re-verify claim_commitment: a claim_json edited after provisioning (without "
                      "recomputing the commitment) is honoured; (d) the Runtime wrapper workflow pins are recorded with their relation to the "
                      "qualified revision. (c) consistent DB+anchor rollback is case C10. Any probe where the recorded behavior is tighter than "
                      "the documented finding is reported as such.")
    wide = _tr.g.effect_policy

    def amount():
        G = _tr.newgov(tmp_path, "amt")
        env, cid = G.claim(amount=5_000_000.0)
        narrow_res, narrow = _tr.attempt(G, env, cid, wide(max_amount=1000.0))
        denied_locally = narrow_res.status == "denied" and narrow["failure_class"] == "policy_denial" and G.counts() == (0, 0, 0, 0)
        wide_res, wideinfo = _tr.attempt(G, env, cid, wide(max_amount=1e9))
        payload_keys = sorted(json.loads(G.e.sql("SELECT record_json FROM selection_activation_v1")[0][0])["payload"])
        return {"narrow_policy": narrow, "wide_policy": wideinfo, "registry_payload_members": payload_keys, "counts": list(G.counts()),
                "caller_owned": bool(denied_locally and wide_res.status == "executed" and G.counts()[0] == 1 and "max_amount" not in payload_keys),
                "informational": True}
    amt = _tr.sub(ev, "A09_amount_ceiling_is_caller_owned", amount)

    def target():
        G = _tr.newgov(tmp_path, "tgt")
        env, cid = G.claim(target="urn:other:system:9")
        narrow_res, narrow = _tr.attempt(G, env, cid, wide())
        denied_locally = narrow_res.status == "denied" and narrow["failure_class"] == "policy_denial" and G.counts() == (0, 0, 0, 0)
        wide_res, wideinfo = _tr.attempt(G, env, cid, wide(allowed_target_prefixes=("urn:other:",)))
        return {"narrow_policy": narrow, "wide_policy": wideinfo, "counts": list(G.counts()),
                "caller_owned": bool(denied_locally and wide_res.status == "executed" and G.counts()[0] == 1), "informational": True}
    tgt = _tr.sub(ev, "A09_target_prefix_is_caller_owned", target)

    def claim_json_edit():
        G = _tr.newgov(tmp_path, "cj")
        stale = _tr.g.binding_of(G.state(), activation_ref="sha256:" + "a" * 64)
        env, cid = G.claim(binding=stale)
        control_res, control = _tr.attempt(G, env, cid)
        control_ok = _tr.refused_as(control_res, G, cid, {"policy_identity_mismatch"}, "REFUSE")
        pristine = tmp_path / "cj_pristine.sqlite3"
        _tr.save(G, pristine)
        row = G.e.sql("SELECT claim_json, claim_commitment FROM execution_claims_v1 WHERE claim_id=?", (cid,))[0]
        raw = json.loads(row[0])
        raw["policy_binding"]["activation_ref"] = G.state().activation_ref  # now matches durable state; claim_commitment NOT recomputed
        G.e.sql("UPDATE execution_claims_v1 SET claim_json=? WHERE claim_id=?", (json.dumps(raw, sort_keys=True, separators=(",", ":")), cid))
        edited_res, edited = _tr.attempt(G, env, cid)
        committed = G.counts()[0]
        cb = {"stale_binding_control": control, "control_refused_policy_identity_mismatch": control_ok, "edited_commitment_unchanged": True,
              "edited_outcome": edited, "counts_after_edit": list(G.counts())}
        # variant 2: edit a member the lock-time comparisons ignore (source label), commitment not recomputed
        _tr.restore(G, pristine)
        raw2 = json.loads(row[0])
        raw2["policy_binding"]["activation_ref"] = G.state().activation_ref
        raw2["source"] = "attacker_supplied_source"
        G.e.sql("UPDATE execution_claims_v1 SET claim_json=? WHERE claim_id=?", (json.dumps(raw2, sort_keys=True, separators=(",", ":")), cid))
        res3, info3 = _tr.attempt(G, env, cid)
        cb.update(ignored_member_outcome=info3, counts_after_ignored_member_edit=list(G.counts()))
        cb["edited_claim_refused"] = edited_res.status != "executed"
        cb["informational"] = True
        cb["control_ok"] = control_ok
        cb["edited_executed"] = committed == 1
        return cb
    cj = _tr.sub(ev, "D08_claim_json_edited_without_recomputing_commitment", claim_json_edit)

    def workflow_pin():
        wf = COMP / "runtime" / ".github" / "workflows"
        pins = {}
        for f in sorted(wf.glob("*.yml")):
            for m in re.finditer(r"uses:\s*cogno-us/cognous-stack-qualification/\S+@([0-9a-f]{40})", f.read_text()):
                pins.setdefault(m.group(1), []).append(f.name)
        v07 = "90e0e56e69448eadb43ea3df2017be189e09e3bb"
        head = _git(REPO, "rev-parse", "HEAD")[1]
        rows = []
        for sha, files in pins.items():
            exists = _git(REPO, "cat-file", "-e", sha + "^{commit}")[0] == 0
            anc = _git(REPO, "merge-base", "--is-ancestor", sha, v07)[0] == 0 if exists else None
            rows.append({"pin": sha, "workflows": files, "commit_known_in_this_repo": exists, "is_ancestor_of_v07_pin": anc,
                         "equals_v07_pin": sha == v07, "equals_this_checkout_head": sha == head})
        return {"pins": rows, "distinct_pins": len(pins), "qualified_revision_v07": v07, "this_checkout_head": head,
                "any_pin_equals_qualified_revision": any(r["equals_v07_pin"] or r["equals_this_checkout_head"] for r in rows),
                "informational": True}
    wfp = _tr.sub(ev, "I01_runtime_wrapper_workflow_pin", workflow_pin)

    harness = [k for k, v in ev["observed"]["probes"].items() if "harness_error" in v]
    if harness:
        ev["verdict"], ev["note"] = "INCONCLUSIVE", f"harness error in {harness}"
    else:
        lines = []
        lines.append("A09: amount ceiling caller-owned=%s; target prefix caller-owned=%s (Registry payload members: %s)" % (
            amt.get("caller_owned"), tgt.get("caller_owned"), amt.get("registry_payload_members")))
        lines.append("D08: control refused stale binding=%s; claim_json edited without recomputing claim_commitment %s at lock time" % (
            cj.get("control_ok"), "EXECUTED (commitment not re-verified)" if cj.get("edited_executed") else "was refused"))
        lines.append("I01: %d distinct wrapper pin(s); any equals the qualified revision: %s" % (wfp.get("distinct_pins", 0), wfp.get("any_pin_equals_qualified_revision")))
        ev["verdict"] = "CHARACTERIZED"
        ev["note"] = " | ".join(lines) + ". Limitations are characterized, not passed."
    assert ev["verdict"] == "CHARACTERIZED", (ev["verdict"], ev["note"])
