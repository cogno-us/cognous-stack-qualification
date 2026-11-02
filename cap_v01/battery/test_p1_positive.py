"""P1: the positive path. The factory-built flow authorizes with a synthetic profile; the host source is read 4 times for construction + decide + execute (1 + 1 + 2), every read
passes through the pinned wrapper and the REAL verifier (all eleven layers, exact Ed25519Verifier, epoch floor applied, real signature checks); the verdict fingerprint equals the
pin; the pinned file is re-read on every call; the Replay trust inputs come from replay_trust_kwargs and a real Replay import admits the real decision; no state is persisted by the
unit (G1 keeps none: no durable anti-rollback, G2)."""
import json
from pathlib import Path

import pytest

import harness as H
from harness import AP, Source, build, make_kit, material, snapshot_doc, snapshot_files, spy  # noqa: F401


def run_flow(tmp_path, kit, spy, **extra):
    mat = material()
    flow, p, src, profile = build(tmp_path, kit, mat, **extra)
    d = flow.decide(p, now=H.NOW)
    assert d.result == "authorized", d.reasons
    ex = flow.execute(p, flow.records.decision(d.decision_id), adapter_id=p.adapter_id, now=H.NOW)
    return flow, p, src, profile, d, ex


@pytest.mark.row("P1.a", "factory flow with a synthetic profile AUTHORIZES and EXECUTES; marked synthetic, wrapper installed")
def test_factory_flow_authorizes_and_executes(tmp_path, spy):
    kit = make_kit(tmp_path)
    flow, p, src, profile, d, ex = run_flow(tmp_path, kit, spy)
    assert d.result == "authorized" and not d.reasons
    assert flow.cap_authority_mode == "synthetic" and flow.cap_authority_id == "cap-profile-1"
    assert type(flow.cap_selection_source) is AP.PinnedSelectionSource and flow.cap_selection_source.last_refusal is None
    dest = json.loads((tmp_path / "destination.json").read_text())
    assert dest, "the refund effect must have been written by the real destination"
    assert flow.status_max_age_seconds == 60 and flow.approval_max_age_seconds == 60   # per-scalar min(host 60, signed bound 120/90)


@pytest.mark.row("P1.b", "4 source reads for construction + decide + execute (1 + 1 + 2): the host source, the wrapper and the Registry core all see exactly 4, in step")
def test_four_reads_through_the_wrapper_and_the_real_verifier(tmp_path, spy):
    kit = make_kit(tmp_path)
    mat = material()
    flow, p, src, _ = build(tmp_path, kit, mat)
    wrapper = flow.cap_selection_source
    assert (src.calls, wrapper.reads, spy.n) == (1, 1, 1)
    d = flow.decide(p, now=H.NOW)
    assert (src.calls, wrapper.reads, spy.n) == (2, 2, 2)
    flow.execute(p, flow.records.decision(d.decision_id), adapter_id=p.adapter_id, now=H.NOW)
    assert (src.calls, wrapper.reads) == (4, 4)
    # the Registry core ran once per read of the wrapper (Control Plane internal re-reads may add verifier runs but never fewer)
    assert spy.n == 4


@pytest.mark.row("P1.c", "every verification runs ALL ELEVEN layers to pass with the exact Ed25519Verifier, applies the epoch floor, and does real Ed25519 signature checks")
def test_every_read_is_a_full_real_verification(tmp_path, spy):
    kit = make_kit(tmp_path)
    run_flow(tmp_path, kit, spy)
    assert spy.n == 4 and spy.crypto >= spy.n
    assert set(spy.verifier_types) == {H.ev.Ed25519Verifier}
    for verdict in spy.verdicts:
        names = [k for k, _ in verdict.layers]
        assert names == list(H.vsel._LAYERS) and len(names) == 11
        assert all(x == "pass" for _, x in verdict.layers)
        assert verdict.admitted is True and verdict.code is None and verdict.epoch_floor_applied is True
        assert verdict.trust_snapshot_fingerprint == kit.config["snapshot"]["expected"]["fingerprint"]


@pytest.mark.row("P1.d", "the verdict fingerprint equals the pin, and the pin equals an INDEPENDENT recomputation (sha256 over the Registry canonical bytes of the normalized snapshot)")
def test_fingerprint_equals_the_pin_and_an_independent_recomputation(tmp_path, spy):
    import hashlib
    kit = make_kit(tmp_path)
    flow, p, src, profile = build(tmp_path, kit, material())
    independent = "sha256:" + hashlib.sha256(H.c.canonical_bytes(H.pid.normalize_snapshot(json.loads(kit.snapshot_path.read_text())))).hexdigest()
    assert profile.pin_fingerprint == independent == kit.config["snapshot"]["expected"]["fingerprint"]
    assert spy.verdicts[0].trust_snapshot_fingerprint == independent
    assert H.pid.trust_snapshot_fingerprint_from_verified(flow.cap_selection_source().trust) == independent


@pytest.mark.row("P1.e", "the wrapper returns FRESH material carrying the pinned snapshot, not the host's object; host material is otherwise passed through unchanged")
def test_wrapper_returns_the_pinned_snapshot_not_the_hosts_object(tmp_path, spy):
    kit = make_kit(tmp_path)
    mat = material()
    flow, p, src, _ = build(tmp_path, kit, mat)
    got = flow.cap_selection_source()
    assert got is not mat.selection_material() and got.trust is not mat.host_trust
    assert (got.record_text, got.selection_text) == (mat.record_text, mat.selection_text)
    assert H.pid.trust_snapshot_fingerprint_from_verified(got.trust) == profile_pin(kit)
    assert flow.cap_selection_source() .trust is not got.trust   # not cached: a fresh object per call


def profile_pin(kit):
    return kit.config["snapshot"]["expected"]["fingerprint"]


@pytest.mark.row("P1.f", "the pinned snapshot file is RE-READ on every call (no cache): the file is read once per wrapper call")
def test_pinned_file_is_read_on_every_call(tmp_path, spy, monkeypatch):
    kit = make_kit(tmp_path)
    flow, p, src, _ = build(tmp_path, kit, material())
    target = str(kit.snapshot_path)
    seen = []
    import builtins
    real = builtins.open

    def counting(file, *a, **k):
        if isinstance(file, (str, Path)) and str(file) == target:
            seen.append(1)
        return real(file, *a, **k)

    monkeypatch.setattr(builtins, "open", counting)
    wrapper = flow.cap_selection_source
    for _ in range(3):
        wrapper()
    assert len(seen) == 3


@pytest.mark.row("P1.g", "a host snapshot EQUAL to the pin is accepted (and ignored); owner digest is optional in synthetic mode and equally accepted")
def test_synthetic_without_owner_digest_and_equal_host_snapshot(tmp_path, spy):
    kit = make_kit(tmp_path)
    flow, p, src, _ = build(tmp_path, kit, material(), digest=None)
    assert flow.decide(p, now=H.NOW).result == "authorized"


@pytest.mark.row("P1.h", "Replay trust inputs come from replay_trust_kwargs (derived from the configuration and the pinned snapshot ONLY): pin, ref, context, version floor, verification time")
def test_replay_trust_kwargs_are_derived_from_the_pin(tmp_path, spy):
    kit = make_kit(tmp_path)
    flow, p, src, profile = build(tmp_path, kit, material())
    kw = AP.replay_trust_kwargs(profile)
    assert kw["trust_snapshot_fingerprint"] == profile_pin(kit)
    assert H.pid.trust_snapshot_fingerprint_from_verified(kw["trust_snapshot"]) == profile_pin(kit)
    assert kw["trust_snapshot_ref"] == (H.SNAP_ID, H.SNAP_VERSION) and kw["min_trust_snapshot_version"] == H.SNAP_VERSION and kw["last_accepted_snapshot"] is None
    assert kw["expected_context"] == {"consumer_id": H.CONSUMER, "tenant": H.TENANT_ID, "institution": H.INSTITUTION, "authority_domain": H.DOMAIN, "operation": H.OPERATION}
    assert kw["time_mode"] == "as_of" and kw["verification_time"] == H.NOW


@pytest.mark.row("P1.i", "replay_trust_kwargs re-reads and re-checks the pin: a tampered pinned file refuses (snapshot_pin_mismatch) and yields NO kwargs")
def test_replay_trust_kwargs_refuses_a_tampered_pinned_file(tmp_path, spy):
    kit = make_kit(tmp_path)
    profile = kit.load()
    kit.snapshot_path.write_bytes(H.dump(snapshot_doc(version=2)))
    got = None
    with pytest.raises(AP.AuthorityProfileRefusal) as exc:
        got = AP.replay_trust_kwargs(profile)
    assert got is None and exc.value.code == "snapshot_pin_mismatch"


@pytest.mark.row("P1.j", "REAL Replay import (registry-authenticated-selection/0.1) of the real factory decision using ONLY the replay_trust_kwargs inputs admits; the real adapter was reached; markers carry the pinned fingerprint; check_replay_markers is True")
def test_replay_import_with_the_kwargs_admits_and_markers_match_the_pin(tmp_path, spy):
    kit = make_kit(tmp_path)
    flow, p, src, profile, d, ex = run_flow(tmp_path, kit, spy, carry_selection_evidence=True)
    run = json.loads((tmp_path / "run.json").read_text())
    cp, proposal = H.bridge_record(run)
    vs = H.VerifierSpy()
    trust = H.replay_trust(AP.replay_trust_kwargs(profile), vs)
    bundle = H.I.import_bounded_workflow(cp, proposal=proposal, moltbot_export=None, control_plane_revision=H.I.CONTROL_PLANE_CUR_REVISION, control_plane_profile=H.SELECTOR,
                                         registry_evidence_trust=trust)
    assert len(vs.requests) == 1 and vs.verdicts[-1]["ok"] is True
    m = bundle.metadata
    assert m["registry_selection_admitted_by_injected_verifier"] is True and m["registry_authenticated"] is False and m["control_plane_decision_authenticated"] is False
    (row,) = m["registry_evidence"]
    assert row["trust_snapshot_fingerprint"] == profile_pin(kit) and row["epoch_floor_applied"] is True
    assert AP.check_replay_markers(profile, m) is True and AP.check_replay_markers(profile, m["registry_evidence"]) is True


@pytest.mark.row("P1.k", "check_replay_markers is strict: empty, missing, a foreign fingerprint in ANY row, or non-mapping rows are False")
def test_check_replay_markers_is_strict(tmp_path, spy):
    kit = make_kit(tmp_path)
    profile = kit.load()
    good = {"trust_snapshot_fingerprint": profile_pin(kit)}
    bad = {"trust_snapshot_fingerprint": "sha256:" + "0" * 64}
    assert AP.check_replay_markers(profile, [good]) is True
    assert AP.check_replay_markers(profile, [good, good]) is True
    for rows in ([], None, {}, {"registry_evidence": []}, [bad], [good, bad], [bad, good], ["x"], [{}], {"registry_evidence": [good, bad]}, (good,), "sha256", 7):
        assert AP.check_replay_markers(profile, rows) is False, rows


@pytest.mark.row("P1.l", "NO state persistence in G1: the configuration and snapshot are byte-identical after construct/decide/execute/replay_trust_kwargs; the only files are the Control Plane's own two stores and their locks")
def test_unit_persists_no_state(tmp_path, spy, monkeypatch):
    kit = make_kit(tmp_path)
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    auth_before = snapshot_files(kit.dir)
    flow, p, src, profile, d, ex = run_flow(tmp_path, kit, spy)
    AP.replay_trust_kwargs(profile)
    assert snapshot_files(kit.dir) == auth_before
    assert sorted(snapshot_files(tmp_path)) == sorted(["auth", "auth/authority.json", "auth/snapshot.json", "cwd", "destination.json", "destination.json.lock", "run.json", "run.json.lock"])
    assert list(cwd.iterdir()) == []


@pytest.mark.row("P1.m", "no cross-process anti-rollback is claimed: the module and the evidence say so (G2); a fresh wrapper over the same pin has no memory of an earlier acceptance (read count restarts at 0)")
def test_a_new_wrapper_has_no_memory_of_earlier_acceptance(tmp_path, spy):
    kit = make_kit(tmp_path)
    flow, p, src, profile = build(tmp_path, kit, material())
    flow.cap_selection_source()
    fresh = AP.PinnedSelectionSource(profile, Source(material()), H.ev.Ed25519Verifier(), expected_mode="synthetic")
    assert fresh.reads == 0 and fresh.last_refusal is None
    assert fresh().record_text
    assert "NO durable anti-rollback (G2)" in AP.__doc__
