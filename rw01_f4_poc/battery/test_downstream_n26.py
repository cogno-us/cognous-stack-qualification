"""N26: ODES d461f0ba, Evidence Pack 39fecb00 and Exchange 37f72b69 AS THEY EXIST (unmodified) against the PoC tuple. Downstream code is only called, never edited.

What is shown (each statement is an assertion below):
  (a) a CP record carrying selection_evidence fails PLAIN Replay import (PR head) with undeclared_member (E-3), so no plain re-import can reproduce it;
  (b) the authenticated-profile bundle is refused by ODES and by the Evidence Pack. With the PoC Replay installed both refuse on the exact Replay revision (fail-closed pin);
      with the accepted Replay 6f45e288 installed both refuse on content (same refusal as for the pre-existing Registry-governed profile bundle: runtime authority fields
      unsupported / producer profile identity contradiction);
  (c) INERT PASS (documented, not a defect of this PoC): a plain bundle into which selection_evidence is injected after the fact is accepted by ODES and the Pack when the
      ACCEPTED Replay 6f45e288 is installed - the signed blob is then carried, digested and never verified downstream;
  (d) Exchange's strict source-identity check (profile security-runtime-current-20261031-r3) refuses the PoC Control Plane head.
"""
import copy
import json
import subprocess
import sys

import pytest

import harness as H

pytestmark = [pytest.mark.evidence("SUBPROCESS")]
MANIFEST = H.src("control_plane") / "tests" / "fixtures" / "refund_integration_v1_1.manifest.json"
ODES_MANIFEST = H.src("odes") / "tests" / "data" / "current_generation" / "manifest.json"


def probe(script, *args):
    res = subprocess.run([sys.executable, str(H.HERE / script), *map(str, args)], capture_output=True, text=True, timeout=900)
    assert res.returncode == 0, res.stderr[-1500:]
    return res.stdout


@pytest.fixture(scope="module")
def bundles(tmp_path_factory):
    from unittest import mock
    d = tmp_path_factory.mktemp("n26")
    with mock.patch.object(H.cp_bounded, "_now", lambda: H.NOW), mock.patch.object(H.cp_f4, "_now", lambda: H.NOW):
        pr = H.produce(d / "w", H.material())
    cp, proposal = H.bridge(pr)
    auth, _ = H.admitted(cp, proposal)
    cp0, p0 = H.bridge(pr, evidence=False)
    governed = H.do_import(cp0, p0, selector=H.OLD_SELECTOR)
    control = json.loads(probe("probe_downstream.py", "make-control", H.src("replay_base") / "src", H.src("odes")))
    injected = copy.deepcopy(control)
    for r_ in injected["records"]:
        if r_["record_type"] == "runtime_decision" and r_["data"].get("result") == "authorized":
            r_["data"]["selection_evidence"] = cp["decisions"][0]["selection_evidence"]
    paths = {}
    for name, obj in (("auth", json.loads(auth.model_dump_json())), ("governed", json.loads(governed.model_dump_json())), ("control", control), ("injected", injected)):
        paths[name] = d / (name + ".json")
        paths[name].write_text(json.dumps(obj))
    return paths, cp, proposal


def run(kind, replay, path, manifest):
    root = H.src("odes") if kind == "odes" else H.src("evidence_pack")
    return json.loads(probe("probe_downstream.py", kind, H.src(replay) / "src", root, path, manifest))


@pytest.mark.row("N26", "(a) a CP record with selection_evidence fails PLAIN Replay import with undeclared_member (exact), under the plain selector and the old governed selector, with and without expected digest; every older revision also refuses")
@pytest.mark.evidence("BRIDGED")
def test_n26_a_record_with_selection_evidence_fails_plain_replay_import(bundles):
    _, cp, proposal = bundles
    for kw in ({}, {"control_plane_profile": H.OLD_SELECTOR}, {"control_plane_profile": H.OLD_SELECTOR, "expected_effective_configuration_digest": cp["decisions"][0]["binding"]["runtime_authority"]["effective_configuration"]["digest"]}):
        bundle = None
        with pytest.raises(H.ImportContractError) as exc:
            bundle = H.I.import_bounded_workflow(copy.deepcopy(cp), proposal=copy.deepcopy(proposal), control_plane_revision=H.CUR_CP, **kw)
        assert bundle is None and exc.value.code == "undeclared_member", (kw, exc.value.code)
    revisions = sorted(getattr(H.I, n) for n in dir(H.I) if n.startswith("CONTROL_PLANE") and n.endswith("REVISION"))
    for rev in revisions:
        with pytest.raises(H.ImportContractError):
            H.I.import_bounded_workflow(copy.deepcopy(cp), proposal=copy.deepcopy(proposal), control_plane_revision=rev)


@pytest.mark.row("N26", "(b) ODES: the authenticated-profile bundle is REFUSED - on the exact Replay revision when the PoC Replay is installed, on content when the accepted Replay 6f45e288 is installed; the plain control bundle is accepted by ODES with the accepted Replay")
def test_n26_odes_refuses_the_authenticated_bundle(bundles):
    paths, _, _ = bundles
    ctrl = run("odes", "replay_base", paths["control"], ODES_MANIFEST)
    assert ctrl["result"] == "accepted"                                              # harness control: ODES + accepted Replay works on a plain bundle
    poc = run("odes", "replay", paths["auth"], MANIFEST)
    assert poc["result"] == "refused" and poc["type"] == "ReplayRevisionUnsupportedError" and "is not an accepted Replay revision" in poc["message"]
    assert run("odes", "replay", paths["control"], ODES_MANIFEST)["type"] == "ReplayRevisionUnsupportedError"   # even the plain control is refused with the PoC Replay: exact-version pin
    accepted = run("odes", "replay_base", paths["auth"], MANIFEST)
    assert accepted["result"] == "refused" and accepted["type"] == "ExportError" and "runtime authority fields unsupported" in accepted["message"]
    gov = run("odes", "replay_base", paths["governed"], MANIFEST)
    assert (gov["type"], gov["message"]) == (accepted["type"], accepted["message"])   # identical to the pre-existing governed-profile bundle: nothing new is admitted


@pytest.mark.row("N26", "(b) Evidence Pack: the authenticated-profile bundle is REFUSED with the PoC Replay and with the accepted Replay (producer profile identity contradicts the accepted mapping); plain control accepted with the accepted Replay")
def test_n26_pack_refuses_the_authenticated_bundle(bundles):
    paths, _, _ = bundles
    assert run("pack", "replay_base", paths["control"], ODES_MANIFEST)["result"] == "accepted"
    for replay in ("replay", "replay_base"):
        res = run("pack", replay, paths["auth"], MANIFEST)
        assert res["result"] == "refused" and res["type"] == "ImportContractError" and "producer profile identity contradicts accepted Replay revision/profile mapping" in res["message"], (replay, res)
    assert "is not the pinned revision 6f45e288" in run("pack", "replay", paths["control"], ODES_MANIFEST)["message"]    # the exact-version pin, on the plain control
    gov = run("pack", "replay_base", paths["governed"], MANIFEST)
    assert gov["message"] == run("pack", "replay_base", paths["auth"], MANIFEST)["message"]


@pytest.mark.row("N26", "(c) INERT PASS, reported precisely: a plain bundle with selection_evidence injected post hoc is ACCEPTED by ODES and the Pack under the ACCEPTED Replay (signed blob carried and digested, never verified downstream); refused on the exact Replay revision under the PoC Replay")
def test_n26_injected_selection_evidence_passes_inertly_downstream_only_under_the_accepted_replay(bundles):
    paths, _, _ = bundles
    assert run("odes", "replay_base", paths["injected"], ODES_MANIFEST)["result"] == "accepted"
    assert run("pack", "replay_base", paths["injected"], ODES_MANIFEST)["result"] == "accepted"
    assert run("odes", "replay", paths["injected"], ODES_MANIFEST)["type"] == "ReplayRevisionUnsupportedError"
    assert run("pack", "replay", paths["injected"], ODES_MANIFEST)["type"] == "ImportContractError"
    # and the same bundle is NOT a valid plain Replay input at the PoC head: the evidence is rejected there
    control = json.loads(paths["injected"].read_text())
    assert any(r_["data"].get("selection_evidence") for r_ in control["records"] if r_["record_type"] == "runtime_decision")


@pytest.mark.row("N26", "(d) Exchange r3 strict source-identity check refuses the PoC Control Plane head (candidate source identity mismatch: agent_control_plane.bounded); the base CP passes that first check and stops later at a source (engine.producer_contract) this battery does not pin")
def test_n26_exchange_refuses_the_poc_control_plane_head():
    out = {}
    for name in ("control_plane", "control_plane_base"):
        out[name] = json.loads(probe("probe_exchange.py", H.src("exchange"), H.src(name), H.src("replay") / "src"))
    assert out["control_plane"]["strict_profile"] is True and out["control_plane"]["pins"]["CP_REVISION"] == "b19c47ddd020409d24e52e70b11359c46265edbb"
    assert out["control_plane"]["pins"]["REPLAY_REVISION"] == "6f45e288ae37ec7e7712f9296760927d2d843bba"
    assert out["control_plane"]["result"] == "RuntimeError: candidate source identity mismatch: agent_control_plane.bounded"
    assert out["control_plane_base"]["result"] == "RuntimeError: candidate source identity mismatch: engine.producer_contract"
