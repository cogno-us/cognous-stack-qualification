"""D-1 feasibility PROBE (exploratory; NOT evidence of PASS). Prints JSON lines. Run via run_probe.sh."""
import json, sys, tempfile, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pytest
import d1_lib as L
H = L.H
E = H.env()
mp = pytest.MonkeyPatch(); H.patch_clock(mp)
tmp = Path(tempfile.mkdtemp(prefix="d1probe-"))
def P(tag, **kw): print("PROBE " + tag + " " + json.dumps(kw, sort_keys=True, default=str), flush=True)
def drive(flow, p, did): return H.jsonable(H.drive_execute(E, flow, p, did))

which = sys.argv[1:] or ["f5", "dom"]
if "f5" in which:
    # P-F5-1: mint under H1 (t1=60, R=10); restart identical -> execute
    for label, t1b in (("control_t60", 60), ("masked_t61", 61)):
        try:
            w = L.f5_world(E, tmp, "f5_" + label, t1=60, reg=10)
            flow, dec = L.f5_mint(E, w)
            P("f5.mint." + label, result=dec.result, reasons=list(dec.reasons), did=dec.decision_id)
            ra = flow.runtime_authority_profile
            m = H.member_of(w.dir, w.did)["members"]
            P("f5.member." + label, host=m["host_profile_digest"], eff=m["effective_profile_digest"], fam=m["families"], scope=m["scope"],
              host_age=w.host.actions[w.p.action_id].max_status_age_seconds, eff_age=ra.actions[w.p.action_id].max_status_age_seconds)
            host2 = L.host_profile(E, w.p, t1b)
            flow2 = L.f5_flow(E, w, host=host2)  # same store, same Registry, same approval (NOT re-bound)
            out = drive(flow2, w.p, w.did)
            P("f5.exec." + label, **out)
            P("f5.eff_commit_equal." + label, same=(E.B.commitment(flow.runtime_authority_profile.model_dump(mode="json")) == E.B.commitment(flow2.runtime_authority_profile.model_dump(mode="json"))))
        except Exception as exc:
            P("f5.EXC." + label, err=f"{type(exc).__name__}: {exc}"[:600], tb=traceback.format_exc()[-1500:])
if "dom" in which:
    try:
        w1 = L.domain_world(E, tmp, "d1", "customer-refunds")
        f1, dec1 = L.domain_mint(E, w1)
        P("dom.mint.d1", result=dec1.result, reasons=list(dec1.reasons))
        w2 = L.domain_world(E, tmp, "d2", "other-domain")
        f2, dec2 = L.domain_mint(E, w2)
        P("dom.mint.d2", result=dec2.result, reasons=list(dec2.reasons))
        m1, m2 = H.member_of(w1.dir, w1.did), H.member_of(w2.dir, w2.did)
        P("dom.members", d1=m1["members"]["scope"], d2=m2["members"]["scope"], member_diff=sorted(L.leaf_diff(m1["members"], m2["members"])))
        b1, b2 = L.binding_of(w1.dir, w1.did), L.binding_of(w2.dir, w2.did)
        P("dom.bindingdiff.d1_vs_d2", base=L.split_diff(b1, b2)[0], ecb=L.split_diff(b1, b2)[1])
        P("dom.status", d1_on_flow2=f2.configuration_binding_status(f1.records.decision(w1.did)), d2_on_flow2=f2.configuration_binding_status(f2.records.decision(w2.did)))
        # natural routes over the d1 store
        # (i) original A25(a)-like: rebuild d1 store with the d2 manifest/resolver/registry, execute P1
        import shutil
        ni = Path(tmp) / "nat_i"; shutil.copytree(w1.dir, ni)
        fl = L.construct_domain(E, w2, ni)
        P("dom.nat_i.P1_in_d2world", **drive(fl, w1.p, w1.did))
        # (ii) execute P2 against D1 in d2 world
        ni2 = Path(tmp) / "nat_ii"; shutil.copytree(w1.dir, ni2)
        fl = L.construct_domain(E, w2, ni2)
        P("dom.nat_ii.P2_vs_D1", **drive(fl, w2.p, w1.did))
        # graft
        g = Path(tmp) / "graft"; shutil.copytree(w2.dir, g)
        L.graft(w1.dir, w1.did, g, w2.did)
        fl = L.construct_domain(E, w2, g)
        P("dom.graft.status", status=fl.configuration_binding_status(fl.records.decision(w2.did)))
        P("dom.graft.exec", **drive(fl, w2.p, w2.did))
        bg = L.binding_of(g, w2.did)
        live, res_, rs = L.live_binding(E, lambda sd: L.construct_domain(E, w2, sd), w2.p, Path(tmp) / "scratch_live")
        P("dom.graft.bindingdiff_vs_live", result=res_, reasons=rs, split=L.split_diff(bg, live))
        # d2 control executes
        c = Path(tmp) / "ctl2"; shutil.copytree(w2.dir, c)
        P("dom.ctl.d2_exec", **drive(L.construct_domain(E, w2, c), w2.p, w2.did))
    except Exception as exc:
        P("dom.EXC", err=f"{type(exc).__name__}: {exc}"[:800], tb=traceback.format_exc()[-2500:])

if "eff" in which:
    for label, rebind in (("E1_no_reissue", False), ("E2_reissued", True)):
        try:
            w = L.f5_world(E, tmp, "f5_" + label, t1=60, reg=10)
            flow, dec = L.f5_mint(E, w)
            src2 = H.Src(L.f5_material(E, {L.CLASS_T1: 20}))
            flow2 = L.f5_flow(E, w, src=src2, rebind=rebind)
            P("eff.eff_commit." + label, orig=E.B.commitment(flow.runtime_authority_profile.model_dump(mode="json")), new=E.B.commitment(flow2.runtime_authority_profile.model_dump(mode="json")))
            out = drive(flow2, w.p, w.did)
            P("eff.exec." + label, **out)
            if rebind:
                bp = L.binding_of(w.dir, w.did)
                live, r_, rs = L.live_binding(E, lambda sd: L.f5_flow(E, w, sd, src=src2), w.p, Path(tmp) / ("scratch_" + label))
                P("eff.bindingdiff." + label, result=r_, split=L.split_diff(bp, live))
        except Exception as exc:
            P("eff.EXC." + label, err=f"{type(exc).__name__}: {exc}"[:600], tb=traceback.format_exc()[-1500:])
    try:
        w = L.f5_world(E, tmp, "f5_H1diff", t1=60, reg=10)
        flow, dec = L.f5_mint(E, w)
        host2 = L.host_profile(E, w.p, 61)
        flow2 = L.f5_flow(E, w, host=host2)
        bp = L.binding_of(w.dir, w.did)
        live, r_, rs = L.live_binding(E, lambda sd: L.f5_flow(E, w, sd, host=host2), w.p, Path(tmp) / "scratch_H1")
        P("h1.bindingdiff", result=r_, split=L.split_diff(bp, live))
    except Exception as exc:
        P("h1.EXC", err=f"{type(exc).__name__}: {exc}"[:600], tb=traceback.format_exc()[-1500:])
P("done", tmp=str(tmp))
