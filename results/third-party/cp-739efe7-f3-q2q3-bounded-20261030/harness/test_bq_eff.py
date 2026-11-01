"""OCS-F3-Q2Q3-BOUNDED-v1, case FXE-JOINT (effective-profile digest JOINT transition, freshness-extension route, EXECUTE leg) for Control Plane 739efe7.

DRAFT-PHASE FILE (Worker C, same session lineage as the lead: NOT independent). Written from source reading only; NOT executed by its author. The lead freezes (hashes) this file
before the first execution. An invalid fixture after the freeze is retained as BLOCKED/FAIL and corrected only by a versioned successor (protocol section 14).

Specification: /tmp/claude-0/work/bq/spec/cases-eff.md (assertion inventory, expected values, what each assertion does and does NOT establish).
THIS IS JOINT EVIDENCE. It is NOT independently isolated `effective_profile_digest` evidence: by `02` section 4 line 48 (`effective_profile_digest` equals `catalogue_digest` for
profile-bearing workflows) and construction, the base pair {approval_commitment, catalogue_digest} always moves with it. The case narrows the ECB diff to exactly
{digest, members.effective_profile_digest} (no families.* leaf, no host leaf) and nothing more.

Tests (one pytest function each; C-controls are separate tests):
    test_FXE_JOINT_main   decide under SA, rebuild under SB, re-issue approval, execute
    test_FXE_JOINT_C0     SA unchanged: executes exactly once, empty complementary diff
    test_FXE_JOINT_C1     SB rebuild, approval NOT re-issued: [runtime_authority_approval_mismatch] only (guard first, ECB not consulted)
    test_FXE_JOINT_C2     neutral re-signed SA' (same record content, new selection id/epoch): executes
    test_FXE_JOINT_C3     SC (Registry value 50 < host 60: the EFFECTIVE map changes): ECB diff widens to include the families leaf

Fixture: GovernedClassAgeWorkflow, one class T1 (host status age 60) and a HOST FreshnessProfile(max_age_extension_seconds=100).
    SA = Registry {T1: 70}  -> effective T1 60, composed extension limit min(100, 70-60) = 10
    SB = Registry {T1: 90}  -> effective T1 60, composed extension limit min(100, 90-60) = 30
    SC = Registry {T1: 50}  -> effective T1 50, composed extension limit min(100, max(0, 50-50)) = 0
Nothing here disables, patches or bypasses a guard; no store write, no graft, no reseal; only the public workflow interfaces, `bind_approval` (the supported host duty) and the
fixed synthetic clock patch of D-1. Evidence rows: one JSON object per assertion in $BQ_EVIDENCE_DIR/bq_evidence.jsonl (protocol section 16 schema), and the D-1 style
CHECK_PASS/CHECK_FAIL mirror via d1_lib.rec in $D1_EVIDENCE_DIR/d1_evidence.jsonl. Expected values are hard-coded literals, with ONE disclosed exception class: digest
expectations are the harness's own recomputation (`own_commit`) over a profile dump that the harness builds from the HOST dump plus literals (never from the observed value).
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
import platform
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import d1_lib as L  # noqa: E402

H = L.H
KEY = H.KEY
ECBP = "runtime_authority." + KEY
CT = L.CLASS_T1
CASE = "FXE-JOINT"
PROTOCOL = os.environ.get("BQ_PROTOCOL", "OCS-F3-Q2Q3-BOUNDED-v1")

# ------------------------------------------------------------------------------------------------------------------ frozen fixture constants
HOST_T1 = 60            # host class status age for T1
HOST_EXT_LIMIT = 100    # host FreshnessProfile.max_age_extension_seconds
REG_SA, REG_SB, REG_SC = 70, 90, 50
BIND_CHANGED = "authorization_binding_changed"
APPROVAL_MISMATCH = "runtime_authority_approval_mismatch"
VOCAB = "runtime-authority-reasons/0.1"
EXC_TEXT = "authorization-critical inputs changed before effect"
BASE_PAIR = ["runtime_authority.approval_commitment", "runtime_authority.catalogue_digest"]
ECB_TWO = sorted([f"{ECBP}.digest", f"{ECBP}.members.effective_profile_digest"])
ECB_THREE = sorted([f"{ECBP}.digest", f"{ECBP}.members.effective_profile_digest", f"{ECBP}.members.families.0.effective_policy_digest"])

MAIN_PRE = [f"P{i:02d}" for i in range(1, 13)]
MAIN_A = [f"A{i:02d}" for i in range(1, 33)]
C0_PRE = ["P01", "P02", "P03", "P04", "P05", "P06"]
C0_A = [f"A{i:02d}" for i in range(1, 9)]
C1_PRE = ["P01", "P02", "P03", "P04", "P05"]
C1_A = [f"A{i:02d}" for i in range(1, 9)]
C2_PRE = [f"P{i:02d}" for i in range(1, 9)]
C2_A = [f"A{i:02d}" for i in range(1, 8)]
C3_PRE = ["P01", "P02", "P03", "P04", "P05", "P06"]
C3_A = [f"A{i:02d}" for i in range(1, 11)]


# ------------------------------------------------------------------------------------------------------------------ evidence rows (protocol section 16 schema)
def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _j(x):
    """JSON-normalised copy (tuples become lists, unknown types become str) so that expected and observed compare as stored."""
    return json.loads(json.dumps(x, default=str, sort_keys=True))


def _bq_file() -> Path:
    d = os.environ.get("BQ_EVIDENCE_DIR") or os.environ["D1_EVIDENCE_DIR"]
    p = Path(d)
    p.mkdir(parents=True, exist_ok=True)
    return p / "bq_evidence.jsonl"


def _write(row: dict) -> None:
    now = time.time()
    row = {"protocol": PROTOCOL, "run": os.environ.get("BQ_LABEL") or os.environ.get("D1_LABEL"), "case_id": CASE, "t": round(now, 3), "t_start": _utc(), "t_end": _utc(), **row}
    with open(_bq_file(), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True, default=str, ensure_ascii=False) + "\n")


_D1KIND = {"PASS": "CHECK_PASS", "FAIL": "CHECK_FAIL", "BLOCKED": "BLOCKED", "NOT EXECUTED": "NOT_EXECUTED", "n/a": "OBSERVATION"}


class Leg:
    """One pytest function's evidence recorder. Soft assertions (every criterion recorded, pass AND fail). Preconditions that fail make the leg BLOCKED (not interpreted);
    assertions that fail after the gate are adverse findings (FAIL). Unreached planned ids are recorded NOT EXECUTED on any abort."""

    def __init__(self, test: str, prefix: str, pre_ids, a_ids, kind: str):
        self.test, self.px, self.kind = test, f"{CASE}-{prefix}", kind
        self.pre_ids, self.a_ids = list(pre_ids), list(a_ids)
        self.seen, self.pre_fail, self.fails, self.blocked = set(), [], [], False

    # -- low level
    def _emit(self, sid, kind, expected, observed, result, **extra):
        self.seen.add(sid)
        _write({"test": self.test, "assertion_id": sid, "kind": kind, "expected": _j(expected), "observed": _j(observed), "result": result, **{k: _j(v) for k, v in extra.items()}})
        L.rec(f"{CASE}/{self.test}", _D1KIND.get(result, "OBSERVATION"), check=sid, expected=_j(expected), observed=_j(observed), result=result)

    def __enter__(self):
        return self

    def __exit__(self, et, ev, tb):
        if et is not None:
            if not self.blocked:
                try:
                    _write({"test": self.test, "assertion_id": f"{self.px}EXC", "kind": "EXCEPTION", "expected": None, "observed": {"type": et.__name__, "str": str(ev)[:2000]},
                            "result": "n/a", "trace": "".join(traceback.format_exception(et, ev, tb))[-6000:]})
                except Exception:
                    pass
            for sid in self.pre_ids:
                if self.px + sid not in self.seen:
                    self._emit(self.px + sid, "PRECONDITION", "not reached", "not reached", "NOT EXECUTED", why="aborted: " + et.__name__)
            for sid in self.a_ids:
                if self.px + sid not in self.seen:
                    self._emit(self.px + sid, self.kind, "not reached", "not reached", "NOT EXECUTED", why="aborted: " + et.__name__)
            return False
        missing = [s for s in self.a_ids if self.px + s not in self.seen]
        for sid in missing:
            self._emit(self.px + sid, self.kind, "not reached", "not reached", "NOT EXECUTED", why="planned assertion was not executed")
        assert not self.fails, f"{self.test}: failed {self.fails}"
        assert not missing, f"{self.test}: not executed {missing}"
        return False

    # -- preconditions (BLOCKED when they fail; never interpreted)
    def pre(self, sid, expected, observed, **info):
        ok = _j(observed) == _j(expected)
        self._emit(self.px + sid, "PRECONDITION", expected, observed, "PASS" if ok else "BLOCKED", **info)
        if not ok:
            self.pre_fail.append(self.px + sid)
        return ok

    def guarded(self, sid, fn, expected="completed"):
        """Run `fn` as a precondition step. Any exception (Registry refusal, construction refusal, instrument error) makes the leg BLOCKED immediately."""
        try:
            val = fn()
        except Exception as exc:
            self._emit(self.px + sid, "PRECONDITION", expected, f"{type(exc).__name__}: {str(exc)[:500]}", "BLOCKED", trace=traceback.format_exc()[-4000:])
            self.pre_fail.append(self.px + sid)
            self.gate()
            raise  # unreachable (gate fails); kept for safety
        self._emit(self.px + sid, "PRECONDITION", expected, "completed" if expected == "completed" else expected, "PASS")
        return val

    def gate(self):
        if self.pre_fail:
            self.blocked = True
            _write({"test": self.test, "assertion_id": f"{self.px}GATE", "kind": "OBSERVATION", "expected": "all validity preconditions hold", "observed": {"failed": self.pre_fail},
                    "result": "BLOCKED"})
            pytest.fail("BLOCKED: validity precondition(s) failed, the case is not interpreted: " + ",".join(self.pre_fail), pytrace=False)

    # -- assertions / controls
    def a(self, sid, expected, observed, **info):
        ok = _j(observed) == _j(expected)
        self._emit(self.px + sid, self.kind, expected, observed, "PASS" if ok else "FAIL", **info)
        if not ok:
            self.fails.append(self.px + sid)
        return ok

    # -- observations / snapshots / exceptions
    def obs(self, name, observed, kind="OBSERVATION"):
        _write({"test": self.test, "assertion_id": f"{self.px}{ {'OBSERVATION': 'OBS', 'SNAPSHOT': 'SNP'}.get(kind, kind[:3]) }-{name}", "kind": kind, "expected": None, "observed": _j(observed), "result": "n/a"})

    def exc(self, name, out):
        _write({"test": self.test, "assertion_id": f"{self.px}EXC-{name}", "kind": "EXCEPTION", "expected": None,
                "observed": {"raised": out.get("raised"), "str": out.get("msg"), "is_permission_error": out.get("is_permission_error")}, "result": "n/a", "trace": out.get("trace")})


# ------------------------------------------------------------------------------------------------------------------ session fixtures
@pytest.fixture(scope="session", autouse=True)
def _bq_eff_preflight():
    E = H.env()
    root = Path(E.acp.__file__).resolve().parents[2]
    want = Path(os.environ.get("BQ_CP_ROOT") or os.environ["D1_CP_ROOT"]).resolve()
    assert root == want, f"imported agent_control_plane from {root}, expected {want}"
    import pydantic
    pin = H.pin_state()
    assert pin["head"] == H.EXPECTED_REGISTRY_HEAD and pin["require"] == "1", pin
    L.rec("PREFLIGHT", "OBSERVATION", label=os.environ.get("BQ_LABEL") or os.environ.get("D1_LABEL"), fixture_case=CASE, acp=str(E.acp.__file__), cp_root=str(root),
          python=platform.python_version(), pydantic=pydantic.VERSION, pin=pin)


@pytest.fixture(autouse=True)
def _bq_eff_clock(monkeypatch):
    H.patch_clock(monkeypatch)  # the fixed synthetic clock of D-1; the only patch


# ------------------------------------------------------------------------------------------------------------------ independent oracle helpers
def own_commit(obj) -> str:
    """Independent re-computation of the profile commitment (sha256 over canonical JSON; same canonical form as bounded.commitment, re-implemented in orig_harness.canon)."""
    return "sha256:" + hashlib.sha256(H.canon(obj)).hexdigest()


def expected_eff_dump(host_dump: dict, action_id: str, *, age: int, limit: int) -> dict:
    """The EFFECTIVE profile dump the harness predicts, built from the HOST dump plus two literals; independent of `compose_profile`."""
    d = copy.deepcopy(host_dump)
    d["actions"][action_id]["max_status_age_seconds"] = age
    d["freshness"]["max_age_extension_seconds"] = limit
    return d


def claim_for(base, ecb, member: str) -> str:
    """D-1 decision rule (PROTOCOL-D1 section 5): 'isolated end-to-end' iff the base diff is empty and the member diff is exactly the member leaf plus its digest."""
    return "isolated end-to-end" if base == [] and sorted(ecb) == sorted([f"{ECBP}.digest", f"{ECBP}.members.{member}"]) else "joint"


# ------------------------------------------------------------------------------------------------------------------ fixture builders (own code)
def fx_host(E, p):
    """HOST profile: one irreversible class T1 (status age 60) for the scoped action, plus a host outage-extension limit of 100 (FreshnessProfile). No policy_binding."""
    from agent_control_plane.freshness import FreshnessProfile
    cl = E.ActionClass(class_id=CT, irreversible=True, max_status_age_seconds=HOST_T1)
    return E.RuntimeAuthorityProfile(catalogue_version="synthetic-catalogue/1", actions={p.action_id: cl}, producer_keys={"synthetic-validator": E.PUBLIC},
                                     allow_synthetic_resolver=True, freshness=FreshnessProfile(max_age_extension_seconds=HOST_EXT_LIMIT))


def fx_material(E, classes: dict, *, selection_id=None, epoch=None):
    """Registry F5 class-age selection (r08-v2). Same construction as d1_lib.f5_material, plus optional selection_id/epoch overrides (for the neutral re-signed SA')."""
    payload = {E.ab.F5_FIELD: {k: classes[k] for k in sorted(classes)}}
    record = E.r.seal_record(dict(E.r.make_record(), contract_version="r08-v2", family=E.ab.FAMILY_F5, record_id="f5-age-record", payload=payload))
    scope = {"tenant": H.TENANT, "institution": E.INSTITUTION, "authority_domain": E.AUTHORITY_DOMAIN}
    over = {}
    if selection_id is not None:
        over["selection_id"] = selection_id
    if epoch is not None:
        over["epoch"] = epoch
    stmt = E.r.make_statement_v2(record, consumer_id="consumer-test", scope=scope, operation=L.OP_C, effective=H.EFFECTIVE, issued_at="2026-10-01T00:00:00Z",
                                 family=E.ab.FAMILY_F5, **over)
    sig = base64.b64encode(E.nb.crypto_sign(E.s.V2_DOMAIN + E.c.canonical_bytes(stmt), E.sk)[:64]).decode("ascii")
    selection = E.r.dumps(E.s.envelope(stmt, domain=E.s.V2_DOMAIN, contract="r08-v2", signature=sig, pub=E.pk))
    grant = E.v.AuthorityGrant("consumer-test", H.TENANT, E.INSTITUTION, E.AUTHORITY_DOMAIN, L.OP_C)
    trust = E.v.TrustSnapshot("snap-test-1", 1, "2026-10-07T00:00:00Z", (E.v.IssuerEntry(E.s.KEY_ID, "issuer-test-1", "ed25519", E.pk, (grant,)),))
    return E.agegov.SelectionMaterial(E.r.dumps(record), selection, trust)


def fx_world(E, tmp, name, *, reg):
    """Fresh F5 world with the HOST freshness limit: host T1 age 60, extension limit 100, Registry selection value `reg` for T1. Shape identical to d1_lib.f5_world."""
    d = Path(tmp) / name
    d.mkdir(parents=True, exist_ok=True)
    p = E.tba.tenant_proposal()
    res = E.tba.tenant_resolver_for(p)
    host = fx_host(E, p)
    L.prepare_runtime_authority(E, res, p, d / "_work", host)
    src = H.Src(fx_material(E, {CT: reg}))
    return SimpleNamespace(E=E, p=p, res=res, host=host, src=src, dir=d, reg=reg, t1=HOST_T1)


def journal(flow) -> dict:
    doc = flow.records.load()
    ext = getattr(doc, "age_extensions", None)
    return {"decisions": len(doc.decisions), "refusals": len(doc.refusals), "attempts": len(doc.attempts), "age_extensions": 0 if ext is None else len(ext),
            "refusal_rows": [{"decision_id": r.decision_id, "reasons": sorted(r.reasons), "vocab": r.reason_vocabulary_version} for r in doc.refusals],
            "dest_calls": flow.destination.calls, "dest": H.jsonable(flow.destination.snapshot())}


def drive(E, flow, p, did) -> dict:
    """Same observations as orig_harness.drive_execute, plus the full exception text and traceback (protocol section 16 (d))."""
    persisted = flow.records.decision(did)
    before = H.snap_state(flow, did)
    out = {"raised": None, "msg": None, "trace": None, "attempt_status": None}
    try:
        attempt, _ = flow.execute(p, persisted, adapter_id=p.adapter_id, now=E.NOW)
        out["attempt_status"] = attempt.status
    except Exception as exc:  # recorded and judged by the caller
        out.update(raised=type(exc).__name__, msg=str(exc), trace=traceback.format_exc()[-6000:], is_permission_error=isinstance(exc, PermissionError))
    after = H.snap_state(flow, did)
    new_ref = after["refusals"][len(before["refusals"]):]
    out.update(new_refusal_reasons=[sorted(r.reasons) for r in new_ref], new_refusal_vocab=[r.reason_vocabulary_version for r in new_ref],
               new_attempts=len(after["attempts"]) - len(before["attempts"]), dest_calls=after["calls"] - before["calls"], dest_unchanged=after["dest"] == before["dest"])
    try:
        out["binding_status"] = flow.configuration_binding_status(flow.records.decision(did))  # candidate's classifier: EVIDENCE ONLY, never the oracle
    except Exception as exc:
        out["binding_status"] = f"raised:{type(exc).__name__}"
    return H.jsonable(out)


def parse_material(mat) -> dict:
    rec_ = json.loads(mat.record_text)
    sel = json.loads(mat.selection_text)
    return {"class_map": rec_["payload"]["class_status_max_age_seconds"], "record_digest": rec_.get("record_digest"), "selection_id": sel["statement"]["selection_id"],
            "epoch": sel["statement"]["epoch"], "record_text_sha256": hashlib.sha256(mat.record_text.encode()).hexdigest(),
            "selection_text_sha256": hashlib.sha256(mat.selection_text.encode()).hexdigest()}


def _unchanged(pm: dict, lm: dict, leaf: str) -> bool:
    return pm["members"][leaf] == lm["members"][leaf]


# ======================================================================================================================== MAIN
def test_FXE_JOINT_main(tmp_path):
    """Decide/mint under SA {T1:70}; rebuild under SB {T1:90}; re-issue the approval to the SB profile; execute. Expected: PermissionError, exactly one new durable
    EffectTimeRefusal [authorization_binding_changed], no attempt row, destination untouched; base diff exactly {approval_commitment, catalogue_digest}; ECB diff exactly
    {digest, members.effective_profile_digest}. JOINT evidence: never an isolation claim."""
    E = H.env()
    leg = Leg("test_FXE_JOINT_main", "", MAIN_PRE, MAIN_A, "ASSERTION")
    with leg:
        w = fx_world(E, tmp_path, "main", reg=REG_SA)
        aid = w.p.action_id
        host_dump = w.host.model_dump(mode="json")
        srcB = H.Src(fx_material(E, {CT: REG_SB}))
        # ---- validity preconditions (BLOCKED, never interpreted)
        fa = leg.guarded("P01", lambda: L.f5_flow(E, w, rebind=True), "constructed")  # SA world: Registry value 70 above host 60 accepted; approval bound to the SA profile
        deca = leg.guarded("P02", lambda: fa.decide(w.p, now=E.NOW))
        leg.pre("P03", "authorized", deca.result, reasons=list(deca.reasons))
        w.did = deca.decision_id
        fb = leg.guarded("P04", lambda: L.f5_flow(E, w, src=srcB, rebind=True), "constructed")  # SB world: value 90 above host accepted; approval RE-ISSUED to the SB profile
        mats = {"A": parse_material(w.src.mat), "B": parse_material(srcB.mat)}
        leg.pre("P05", {"A": {CT: 70}, "B": {CT: 90}}, {"A": mats["A"]["class_map"], "B": mats["B"]["class_map"]})
        ia, ib = fa.registry_f5_policy_identity, fb.registry_f5_policy_identity
        leg.pre("P06", {"A": {CT: 60}, "B": {CT: 60}}, {"A": ia["effective"], "B": ib["effective"]})
        leg.pre("P07", {"A": {CT: 60}, "B": {CT: 60}}, {"A": ia["host"], "B": ib["host"]})
        leg.pre("P08", True, ia["effective_policy_digest"] == ib["effective_policy_digest"], family_digest_A=ia["effective_policy_digest"], family_digest_B=ib["effective_policy_digest"])
        dump_a, dump_b = fa.runtime_authority_profile.model_dump(mode="json"), fb.runtime_authority_profile.model_dump(mode="json")
        leg.pre("P09", ["freshness.max_age_extension_seconds"], sorted(L.leaf_diff(dump_a, dump_b)))
        leg.pre("P10", True, own_commit(dump_a) != own_commit(dump_b), commit_A=own_commit(dump_a), commit_B=own_commit(dump_b))
        live, r_, rs = leg.guarded("P11", lambda: L.live_binding(E, lambda sd: L.f5_flow(E, w, sd, src=srcB), w.p, Path(tmp_path) / "main_live"))
        leg.pre("P12", "authorized", r_, reasons=rs)  # the SB world genuinely mints (so a complementary diff exists)
        leg.gate()
        # ---- persisted (SA) vs live (SB) complementary diff, harness-side
        pers = L.binding_of(w.dir, w.did)
        base, ecb = L.split_diff(pers, live)
        pm, lm = pers["runtime_authority"][KEY], live["runtime_authority"][KEY]
        exp_a = expected_eff_dump(host_dump, aid, age=60, limit=10)
        exp_b = expected_eff_dump(host_dump, aid, age=60, limit=30)
        claim = claim_for(base, ecb, "effective_profile_digest")
        leg.obs("fixture_material", {"A": mats["A"], "B": mats["B"], "note": "same selection_id/epoch, different record content and record_digest"})
        leg.obs("complementary_diff", {"base_diff": base, "ecb_diff": ecb, "claim": claim, "persisted_member": pm, "live_member": lm,
                                       "persisted_catalogue_digest": pers["runtime_authority"]["catalogue_digest"], "live_catalogue_digest": live["runtime_authority"]["catalogue_digest"],
                                       "own_commit_exp_A": own_commit(exp_a), "own_commit_exp_B": own_commit(exp_b), "own_commit_host": own_commit(host_dump)})
        # ---- derivation / functional (persisted SA member, live SB member)
        leg.a("A01", exp_a, dump_a)
        leg.a("A02", exp_b, dump_b)
        leg.a("A03", own_commit(exp_a), pers["runtime_authority"]["catalogue_digest"])
        leg.a("A04", own_commit(exp_a), pm["members"]["effective_profile_digest"])
        leg.a("A05", True, pm["members"]["effective_profile_digest"] == pers["runtime_authority"]["catalogue_digest"])
        leg.a("A06", own_commit(host_dump), pm["members"]["host_profile_digest"])
        leg.a("A07", True, pm["members"]["host_profile_digest"] != pm["members"]["effective_profile_digest"])
        leg.a("A08", True, H.my_digest(pm["members"], pm["version"]) == pm["digest"])
        leg.a("A09", own_commit(exp_b), live["runtime_authority"]["catalogue_digest"])
        leg.a("A10", own_commit(exp_b), lm["members"]["effective_profile_digest"])
        leg.a("A11", True, lm["members"]["effective_profile_digest"] == live["runtime_authority"]["catalogue_digest"])
        leg.a("A12", True, H.my_digest(lm["members"], lm["version"]) == lm["digest"])
        leg.a("A13", own_commit(host_dump), lm["members"]["host_profile_digest"])
        # ---- complementary diff (joint attribution)
        leg.a("A14", BASE_PAIR, base)
        leg.a("A15", ECB_TWO, sorted(ecb))
        leg.a("A16", True, _unchanged(pm, lm, "families"))
        leg.a("A17", True, _unchanged(pm, lm, "host_profile_digest"))
        leg.a("A18", True, _unchanged(pm, lm, "scope"))
        leg.a("A19", True, _unchanged(pm, lm, "f4_scalars"))
        leg.a("A20", True, _unchanged(pm, lm, "other_scalars"))
        leg.a("A21", True, _unchanged(pm, lm, "observation_policy"))
        leg.a("A22", "joint", claim)
        leg.a("A23", {"slot": "class_age", "n": 1}, {"slot": pm["members"]["families"][0]["slot"] if pm["members"]["families"] else None, "n": len(pm["members"]["families"])})
        # ---- execute leg (rebuilt SB workflow, approval re-issued, same store)
        jb, bind_before = journal(fb), L.binding_of(w.dir, w.did)
        leg.obs("journal_before", jb, "SNAPSHOT")
        out = drive(E, fb, w.p, w.did)
        ja, bind_after = journal(fb), L.binding_of(w.dir, w.did)
        leg.obs("journal_after", ja, "SNAPSHOT")
        leg.exc("execute", out)
        leg.obs("execute_outcome", out)
        leg.a("A24", "PermissionError", out.get("raised"))
        leg.a("A25", EXC_TEXT, out.get("msg"))
        leg.a("A26", [[BIND_CHANGED]], out["new_refusal_reasons"])
        leg.a("A27", [VOCAB], out["new_refusal_vocab"])
        leg.a("A28", {"new_attempts": 0, "total_attempts_after": 0}, {"new_attempts": out["new_attempts"], "total_attempts_after": ja["attempts"]})
        leg.a("A29", {"dest_calls": 0, "dest_unchanged": True}, {"dest_calls": out["dest_calls"], "dest_unchanged": out["dest_unchanged"]})
        leg.a("A30", {"decisions": [1, 1], "refusals": [0, 1], "age_extensions": [0, 0]},
              {"decisions": [jb["decisions"], ja["decisions"]], "refusals": [jb["refusals"], ja["refusals"]], "age_extensions": [jb["age_extensions"], ja["age_extensions"]]})
        leg.a("A31", True, bind_before == bind_after)
        leg.a("A32", "mismatch", out.get("binding_status"))  # candidate classifier: evidence only


# ======================================================================================================================== C0
def test_FXE_JOINT_C0(tmp_path):
    """Control C0: SA unchanged (restart over the same store, same Registry material, same host, same approval) executes exactly once; complementary diff empty."""
    E = H.env()
    leg = Leg("test_FXE_JOINT_C0", "C0-", C0_PRE, C0_A, "CONTROL")
    with leg:
        w = fx_world(E, tmp_path, "c0", reg=REG_SA)
        host_dump = w.host.model_dump(mode="json")
        fa = leg.guarded("P01", lambda: L.f5_flow(E, w, rebind=True), "constructed")
        deca = leg.guarded("P02", lambda: fa.decide(w.p, now=E.NOW))
        leg.pre("P03", "authorized", deca.result, reasons=list(deca.reasons))
        w.did = deca.decision_id
        f0 = leg.guarded("P04", lambda: L.f5_flow(E, w), "constructed")  # restart: same SA material, approval NOT touched (unchanged profile, unchanged commitment)
        live, r_, rs = leg.guarded("P05", lambda: L.live_binding(E, lambda sd: L.f5_flow(E, w, sd), w.p, Path(tmp_path) / "c0_live"))
        leg.pre("P06", "authorized", r_, reasons=rs)
        leg.gate()
        pers = L.binding_of(w.dir, w.did)
        base, ecb = L.split_diff(pers, live)
        exp_a = expected_eff_dump(host_dump, w.p.action_id, age=60, limit=10)
        leg.obs("complementary_diff", {"base_diff": base, "ecb_diff": ecb})
        jb = journal(f0)
        leg.obs("journal_before", jb, "SNAPSHOT")
        out = drive(E, f0, w.p, w.did)
        leg.obs("journal_after", journal(f0), "SNAPSHOT")
        leg.exc("execute", out)
        leg.obs("execute_outcome", out)
        leg.a("A01", [], base)
        leg.a("A02", [], ecb)
        leg.a("A03", {"raised": None, "attempt_status": "acknowledged"}, {"raised": out.get("raised"), "attempt_status": out.get("attempt_status")})
        leg.a("A04", [], out["new_refusal_reasons"])
        leg.a("A05", 1, out["dest_calls"])
        leg.a("A06", "bound", out.get("binding_status"))  # candidate classifier: evidence only
        leg.a("A07", own_commit(exp_a), pers["runtime_authority"][KEY]["members"]["effective_profile_digest"])
        leg.a("A08", own_commit(exp_a), pers["runtime_authority"]["catalogue_digest"])


# ======================================================================================================================== C1
def test_FXE_JOINT_C1(tmp_path):
    """Control C1 (guard order): the SB workflow is rebuilt but the approval is NOT re-issued: the base approval guard refuses first with [runtime_authority_approval_mismatch]
    only; `authorization_binding_changed` does not appear (the ECB comparison is not consulted)."""
    E = H.env()
    leg = Leg("test_FXE_JOINT_C1", "C1-", C1_PRE, C1_A, "CONTROL")
    with leg:
        w = fx_world(E, tmp_path, "c1", reg=REG_SA)
        srcB = H.Src(fx_material(E, {CT: REG_SB}))
        fa = leg.guarded("P01", lambda: L.f5_flow(E, w, rebind=True), "constructed")
        deca = leg.guarded("P02", lambda: fa.decide(w.p, now=E.NOW))
        leg.pre("P03", "authorized", deca.result, reasons=list(deca.reasons))
        w.did = deca.decision_id
        fb = leg.guarded("P04", lambda: L.f5_flow(E, w, src=srcB, rebind=False), "constructed")  # approval NOT re-issued
        dump_a, dump_b = fa.runtime_authority_profile.model_dump(mode="json"), fb.runtime_authority_profile.model_dump(mode="json")
        leg.pre("P05", ["freshness.max_age_extension_seconds"], sorted(L.leaf_diff(dump_a, dump_b)))
        leg.gate()
        jb = journal(fb)
        leg.obs("journal_before", jb, "SNAPSHOT")
        out = drive(E, fb, w.p, w.did)
        ja = journal(fb)
        leg.obs("journal_after", ja, "SNAPSHOT")
        leg.exc("execute", out)
        leg.obs("execute_outcome", out)
        L.rec("FXE-JOINT-C1", "CLASSIFICATION", claim="guard-first (approval); effective member not isolated, ECB comparison not consulted", observed=out["new_refusal_reasons"])
        leg.a("A01", "PermissionError", out.get("raised"))
        leg.a("A02", EXC_TEXT, out.get("msg"))
        leg.a("A03", [[APPROVAL_MISMATCH]], out["new_refusal_reasons"])
        leg.a("A04", False, any(BIND_CHANGED in r for r in out["new_refusal_reasons"]))
        leg.a("A05", [VOCAB], out["new_refusal_vocab"])
        leg.a("A06", {"new_attempts": 0, "total_attempts_after": 0}, {"new_attempts": out["new_attempts"], "total_attempts_after": ja["attempts"]})
        leg.a("A07", {"dest_calls": 0, "dest_unchanged": True}, {"dest_calls": out["dest_calls"], "dest_unchanged": out["dest_unchanged"]})
        leg.a("A08", {"decisions": [1, 1], "refusals": [0, 1]}, {"decisions": [jb["decisions"], ja["decisions"]], "refusals": [jb["refusals"], ja["refusals"]]})


# ======================================================================================================================== C2
def test_FXE_JOINT_C2(tmp_path):
    """Control C2 (neutral rotation): SA' is a re-signed selection with the SAME record content (same class map, same record text) but a new selection id and epoch. A workflow
    rebuilt over SA' with the unchanged approval executes: selection rotation alone does not refuse; the complementary diff is empty."""
    E = H.env()
    leg = Leg("test_FXE_JOINT_C2", "C2-", C2_PRE, C2_A, "CONTROL")
    with leg:
        w = fx_world(E, tmp_path, "c2", reg=REG_SA)
        srcA2 = H.Src(fx_material(E, {CT: REG_SA}, selection_id="sel-test-2", epoch=2))
        mA, mA2 = parse_material(w.src.mat), parse_material(srcA2.mat)
        leg.pre("P01", {"record_text_equal": True, "selection_text_equal": False, "selection_id": ["sel-test-1", "sel-test-2"], "epoch": [1, 2]},
                {"record_text_equal": w.src.mat.record_text == srcA2.mat.record_text, "selection_text_equal": w.src.mat.selection_text == srcA2.mat.selection_text,
                 "selection_id": [mA["selection_id"], mA2["selection_id"]], "epoch": [mA["epoch"], mA2["epoch"]]})
        fa = leg.guarded("P02", lambda: L.f5_flow(E, w, rebind=True), "constructed")
        deca = leg.guarded("P03", lambda: fa.decide(w.p, now=E.NOW))
        leg.pre("P04", "authorized", deca.result, reasons=list(deca.reasons))
        w.did = deca.decision_id
        f2 = leg.guarded("P05", lambda: L.f5_flow(E, w, src=srcA2, rebind=False), "constructed")  # Registry accepts the re-signed SA'; approval NOT touched
        leg.pre("P06", True, f2.runtime_authority_profile.model_dump(mode="json") == fa.runtime_authority_profile.model_dump(mode="json"))
        live, r_, rs = leg.guarded("P07", lambda: L.live_binding(E, lambda sd: L.f5_flow(E, w, sd, src=srcA2), w.p, Path(tmp_path) / "c2_live"))
        leg.pre("P08", "authorized", r_, reasons=rs)
        leg.gate()
        pers = L.binding_of(w.dir, w.did)
        base, ecb = L.split_diff(pers, live)
        leg.obs("complementary_diff", {"base_diff": base, "ecb_diff": ecb, "live_result": r_, "live_reasons": rs, "material": {"A": mA, "A2": mA2}})
        jb = journal(f2)
        leg.obs("journal_before", jb, "SNAPSHOT")
        out = drive(E, f2, w.p, w.did)
        leg.obs("journal_after", journal(f2), "SNAPSHOT")
        leg.exc("execute", out)
        leg.obs("execute_outcome", out)
        leg.a("A01", [], base)
        leg.a("A02", [], ecb)
        leg.a("A03", {"raised": None, "attempt_status": "acknowledged"}, {"raised": out.get("raised"), "attempt_status": out.get("attempt_status")})
        leg.a("A04", [], out["new_refusal_reasons"])
        leg.a("A05", 1, out["dest_calls"])
        leg.a("A06", "bound", out.get("binding_status"))  # candidate classifier: evidence only
        leg.a("A07", True, f2.registry_f5_policy_identity["effective_policy_digest"] == fa.registry_f5_policy_identity["effective_policy_digest"])


# ======================================================================================================================== C3
def test_FXE_JOINT_C3(tmp_path):
    """Control C3 (leaf observable): SC {T1:50} changes the EFFECTIVE map (50 < host 60). The complementary diff then ALSO contains families.0.effective_policy_digest. Same base
    pair. Execute with the approval re-issued refuses [authorization_binding_changed]."""
    E = H.env()
    leg = Leg("test_FXE_JOINT_C3", "C3-", C3_PRE, C3_A, "CONTROL")
    with leg:
        w = fx_world(E, tmp_path, "c3", reg=REG_SA)
        aid = w.p.action_id
        host_dump = w.host.model_dump(mode="json")
        srcC = H.Src(fx_material(E, {CT: REG_SC}))
        fa = leg.guarded("P01", lambda: L.f5_flow(E, w, rebind=True), "constructed")
        deca = leg.guarded("P02", lambda: fa.decide(w.p, now=E.NOW))
        leg.pre("P03", "authorized", deca.result, reasons=list(deca.reasons))
        w.did = deca.decision_id
        fc = leg.guarded("P04", lambda: L.f5_flow(E, w, src=srcC, rebind=True), "constructed")  # approval re-issued to the SC profile
        live, r_, rs = leg.guarded("P05", lambda: L.live_binding(E, lambda sd: L.f5_flow(E, w, sd, src=srcC), w.p, Path(tmp_path) / "c3_live"))
        leg.pre("P06", "authorized", r_, reasons=rs)
        leg.gate()
        pers = L.binding_of(w.dir, w.did)
        base, ecb = L.split_diff(pers, live)
        pm, lm = pers["runtime_authority"][KEY], live["runtime_authority"][KEY]
        claim = claim_for(base, ecb, "effective_profile_digest")
        exp_c = expected_eff_dump(host_dump, aid, age=50, limit=0)
        leg.obs("complementary_diff", {"base_diff": base, "ecb_diff": ecb, "claim": claim, "persisted_member": pm, "live_member": lm, "own_commit_exp_C": own_commit(exp_c)})
        jb = journal(fc)
        leg.obs("journal_before", jb, "SNAPSHOT")
        out = drive(E, fc, w.p, w.did)
        ja = journal(fc)
        leg.obs("journal_after", ja, "SNAPSHOT")
        leg.exc("execute", out)
        leg.obs("execute_outcome", out)
        leg.a("A01", exp_c, fc.runtime_authority_profile.model_dump(mode="json"))
        leg.a("A02", {CT: 50}, fc.registry_f5_policy_identity["effective"])
        leg.a("A03", BASE_PAIR, base)
        leg.a("A04", ECB_THREE, sorted(ecb))
        leg.a("A05", True, _unchanged(pm, lm, "host_profile_digest"))
        leg.a("A06", "joint", claim)
        leg.a("A07", "PermissionError", out.get("raised"))
        leg.a("A08", [[BIND_CHANGED]], out["new_refusal_reasons"])
        leg.a("A09", {"new_attempts": 0, "total_attempts_after": 0}, {"new_attempts": out["new_attempts"], "total_attempts_after": ja["attempts"]})
        leg.a("A10", {"dest_calls": 0, "dest_unchanged": True}, {"dest_calls": out["dest_calls"], "dest_unchanged": out["dest_unchanged"]})
