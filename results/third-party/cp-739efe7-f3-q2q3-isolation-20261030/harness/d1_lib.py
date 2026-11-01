"""D-1 (Q2/Q3 isolation) fixture and instrument library. Archetype D, subordinate worker of the lead builder session (NOT organizationally independent).

New code (own): F5 class-age Registry material, host profile builder, prepared F5 world, domain-retargeted F4 world, binding leaf diff, graft helper, evidence writer.
Shared tooling (disclosed): fixture helpers are imported from the byte-verified original qualifier harness (orig_harness.py == test_f3a_independent.post-AMEND4.py).
Nothing here disables, patches or bypasses a guard of the subject. The only store-level manipulation is the GRAFT write (unsigned store, documented limit).
"""
from __future__ import annotations

import base64
import copy
import json
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import orig_harness as H  # noqa: E402

KEY, CODE, TENANT = H.KEY, H.CODE, H.TENANT
D1_DOMAIN_DEFAULT = "customer-refunds"   # the literal in tests/test_bounded_authorization.py resolver fixtures
OP_C = "refund-issue-routine"            # Registry operation id used by the builder's F5 tests (a mapping choice of the host)
OP_F = H.OP_F
CLASS_T1 = "synthetic-irreversible"


# ------------------------------------------------------------------------------------------------------------------ evidence writer
def evfile() -> Path:
    p = Path(os.environ["D1_EVIDENCE_DIR"])
    p.mkdir(parents=True, exist_ok=True)
    return p / "d1_evidence.jsonl"


def rec(case, kind, **f):
    with open(evfile(), "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"case": case, "kind": kind, "t": round(time.time(), 3), **f}, sort_keys=True, default=str) + "\n")


class Check:
    """Soft assertions; every criterion is recorded (pass AND fail)."""

    def __init__(self, case):
        self.case, self.fails = case, []

    def ok(self, name, cond, **info):
        rec(self.case, "CHECK_PASS" if cond else "CHECK_FAIL", check=name, **info)
        if not cond:
            self.fails.append(name)
        return bool(cond)

    def obs(self, name, **info):
        rec(self.case, "OBSERVATION", check=name, **info)

    def done(self):
        assert not self.fails, f"{self.case}: failed {self.fails}"


# ------------------------------------------------------------------------------------------------------------------ diff / store helpers
def leaf_diff(a, b, prefix=""):
    """Set of dotted leaf paths whose values differ between two JSON-like structures (lists compared index-wise, length difference reported as path[len])."""
    out = set()
    if isinstance(a, dict) and isinstance(b, dict):
        for k in set(a) | set(b):
            if k not in a or k not in b:
                out.add(f"{prefix}{k}")
            else:
                out |= leaf_diff(a[k], b[k], f"{prefix}{k}.")
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.add(f"{prefix}[len]")
        for i, (x, y) in enumerate(zip(a, b)):
            out |= leaf_diff(x, y, f"{prefix}{i}.")
    elif a != b:
        out.add(prefix[:-1] if prefix.endswith(".") else prefix)
    return out


def binding_of(d, did):
    """Persisted binding (JSON) of decision `did` as stored in the run.json of store dir `d`."""
    return copy.deepcopy(H.dec_item(H.load_doc(d), did)["binding"])


def live_binding(E, mk_flow, p, scratch_dir):
    """Binding that the LIVE world mints for proposal `p` (a genuine decide in a scratch store, same fixtures, same clock). Returns (binding json, decision result, reasons)."""
    Path(scratch_dir).mkdir(parents=True, exist_ok=True)
    flow = mk_flow(scratch_dir)
    dec = flow.decide(p, now=E.NOW)
    if dec.result != "authorized":
        return None, dec.result, list(dec.reasons)
    return binding_of(scratch_dir, dec.decision_id), dec.result, list(dec.reasons)


def split_diff(persisted_binding, live_binding_json):
    """Return (base_diff, ecb_diff): leaf paths differing outside / inside runtime_authority.effective_configuration."""
    full = leaf_diff(persisted_binding, live_binding_json)
    ecbp = f"runtime_authority.{KEY}"
    ecb = {x for x in full if x == ecbp or x.startswith(ecbp + ".")}
    return sorted(full - ecb), sorted(ecb)


# ------------------------------------------------------------------------------------------------------------------ F5 class-age fixtures (NEW code)
def f5_material(E, classes: dict, *, consumer="consumer-test", op=OP_C, domain=None):
    """Registry F5 class-age selection (r08-v2): own construction following the shape of the Registry's test builders; statement scope carries the authority_domain."""
    dom = domain or E.AUTHORITY_DOMAIN
    payload = {E.ab.F5_FIELD: {k: classes[k] for k in sorted(classes)}}
    record = E.r.seal_record(dict(E.r.make_record(), contract_version="r08-v2", family=E.ab.FAMILY_F5, record_id="f5-age-record", payload=payload))
    scope = {"tenant": TENANT, "institution": E.INSTITUTION, "authority_domain": dom}
    stmt = E.r.make_statement_v2(record, consumer_id=consumer, scope=scope, operation=op, effective=H.EFFECTIVE, issued_at="2026-10-01T00:00:00Z", family=E.ab.FAMILY_F5)
    sig = base64.b64encode(E.nb.crypto_sign(E.s.V2_DOMAIN + E.c.canonical_bytes(stmt), E.sk)[:64]).decode("ascii")
    selection = E.r.dumps(E.s.envelope(stmt, domain=E.s.V2_DOMAIN, contract="r08-v2", signature=sig, pub=E.pk))
    grant = E.v.AuthorityGrant(consumer, TENANT, E.INSTITUTION, dom, op)
    trust = E.v.TrustSnapshot("snap-test-1", 1, "2026-10-07T00:00:00Z", (E.v.IssuerEntry(E.s.KEY_ID, "issuer-test-1", "ed25519", E.pk, (grant,)),))
    return E.agegov.SelectionMaterial(E.r.dumps(record), selection, trust)


def host_profile(E, p, t1):
    """HOST profile: one irreversible class T1 for the scoped action, status age t1; no freshness, no policy_binding."""
    cl = E.ActionClass(class_id=CLASS_T1, irreversible=True, max_status_age_seconds=t1)
    return E.RuntimeAuthorityProfile(catalogue_version="synthetic-catalogue/1", actions={p.action_id: cl}, producer_keys={"synthetic-validator": E.PUBLIC},
                                     allow_synthetic_resolver=True)


def prepare_runtime_authority(E, res, p, work, host_cfg):
    """Build the resolver's runtime_authority context exactly as the foundational tests/test_runtime_authority.setup_flow does (own re-statement), tenant-aware."""
    base = E.tba.workflow(Path(work) / "baseline", p, resolver=res).decide(p, now=E.NOW)
    required = sorted([{"input_type": x.input_type, "input_id": x.input_id} for x in base.resolution_inputs], key=lambda x: (x["input_type"], x["input_id"]))
    context, criteria = res.contexts[E.tba.PROFILE], {}
    for ob in context["requirement"]["evidence"]:
        if ob["required"] and ob["kind"] == "authorization":
            criteria[ob["obligation_id"]] = {"kind": "exact_members", "producer_id": "synthetic-validator", "subject_digest": E.B.commitment(E.MEMBERS),
                                             "minimum_count": 40, "members": E.MEMBERS}
            E.sign_evidence(res.evidence[ob["obligation_id"]], tenant_id=TENANT)
    context["runtime_authority"] = {"profile": "runtime-authority/0.1", "required_inputs": required, "required_inputs_digest": E.B.commitment(required),
                                    "evidence_criteria": criteria}


def f5_base_kwargs(E, sd, res, manifest=None):
    return dict(allow_test_time=True, manifest=manifest or E.tba.manifest(), resolver=res, destination=E.Dest(Path(sd) / "destination.json"),
                records=E.B.BoundedRecordStore(Path(sd) / "run.json", "run-1"), observation_policy=E.B.ObservationPolicy(max_age_seconds=300, clock_tolerance_seconds=5))


def construct_f5(E, p, res, host, store_dir, src, *, consumer="consumer-test", op=OP_C):
    scope = E.GovernedScope(consumer, TENANT, p.action_id, op)
    return E.agegov.GovernedClassAgeWorkflow(scope=scope, selection_source=src, verifier=E.ev.Ed25519Verifier(), runtime_authority_profile=host,
                                             construction_time=E.NOW, **f5_base_kwargs(E, store_dir, res))


def f5_world(E, tmp, name, *, t1, reg):
    """Fresh F5 world: host H(t1), Registry selection value `reg` for class T1. Returns SimpleNamespace(p,res,host,src,dir,reg)."""
    d = Path(tmp) / name
    d.mkdir(parents=True, exist_ok=True)
    p = E.tba.tenant_proposal()
    res = E.tba.tenant_resolver_for(p)
    host = host_profile(E, p, t1)
    prepare_runtime_authority(E, res, p, d / "_work", host)
    src = H.Src(f5_material(E, {CLASS_T1: reg}))
    return SimpleNamespace(E=E, p=p, res=res, host=host, src=src, dir=d, reg=reg, t1=t1)


def f5_flow(E, w, store_dir=None, *, host=None, src=None, rebind=False):
    flow = construct_f5(E, w.p, w.res, host if host is not None else w.host, store_dir or w.dir, src if src is not None else w.src)
    if rebind:
        E.bind_approval(w.res, flow.runtime_authority_profile)  # a supported host duty: approvals are issued against the FINAL profile
    return flow


def f5_mint(E, w):
    """Mint under the world's host/Registry values; approvals bound to the effective profile; returns (flow, decision)."""
    flow = f5_flow(E, w, rebind=True)
    dec = flow.decide(w.p, now=E.NOW)
    w.did = dec.decision_id
    return flow, dec


# ------------------------------------------------------------------------------------------------------------------ domain-retargeted F4 world (NEW code, Q2)
def retarget(obj, old, new):
    """Deep replace of the authority-domain string in a resolver fixture (dicts/lists/str-valued attributes of pydantic models). Synthetic trusted-source data only."""
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if v == old:
                obj[k] = new
            else:
                retarget(v, old, new)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if v == old:
                obj[i] = new
            else:
                retarget(v, old, new)
    elif hasattr(obj, "model_fields"):
        for name in type(obj).model_fields:
            v = getattr(obj, name, None)
            if v == old:
                setattr(obj, name, new)
            elif isinstance(v, (dict, list)) or hasattr(v, "model_fields"):
                retarget(v, old, new)


def domain_world(E, tmp, name, domain):
    """F4 world whose HOST MANIFEST action authority_context.authority_domain == domain, with a self-consistent proposal (manifest_digest), resolver (all domain
    fields), and Registry selection re-signed for the domain. Returns SimpleNamespace(p,res,manifest,src,dir,domain)."""
    d = Path(tmp) / name
    d.mkdir(parents=True, exist_ok=True)
    m = E.tba.manifest()
    m["actions"][0]["authority_context"]["authority_domain"] = domain
    p0 = E.tba.tenant_proposal()
    p = type(p0)(**{**p0.model_dump(mode="json", exclude_none=False), "manifest_digest": E.B.commitment(m)})
    res = E.tba.tenant_resolver_for(p)
    if domain != D1_DOMAIN_DEFAULT:
        retarget(res.contexts, D1_DOMAIN_DEFAULT, domain)
        for attr in ("statuses", "identities", "mandates", "approvals", "policies", "conflicts", "role_mappings", "evidence"):
            retarget(getattr(res, attr, {}), D1_DOMAIN_DEFAULT, domain)
    src = H.Src(H.f4_material(E, 30, 30, domain=domain))
    return SimpleNamespace(E=E, p=p, res=res, manifest=m, src=src, dir=d, domain=domain)


def construct_domain(E, w, store_dir=None, *, src=None, manifest=None, res=None):
    sd = Path(store_dir or w.dir)
    kw = f5_base_kwargs(E, sd, res or w.res, manifest or w.manifest)
    scope = E.GovernedScope("consumer-test", TENANT, E.ACTION_ID, OP_F)
    return E.f4gov.GovernedAgeWorkflow(scope=scope, selection_source=src or w.src, verifier=E.ev.Ed25519Verifier(), construction_time=E.NOW, **kw)


def domain_mint(E, w):
    flow = construct_domain(E, w)
    dec = flow.decide(w.p, now=E.NOW)
    w.did = dec.decision_id
    return flow, dec


def graft(donor_dir, donor_did, host_dir, host_did):
    """GRAFT (unsigned-store write, documented limit): copy the donor decision's effective_configuration member VERBATIM into the host decision. No field is edited, no reseal."""
    donor = copy.deepcopy(H.member_of(donor_dir, donor_did))
    doc = H.load_doc(host_dir)
    item = H.dec_item(doc, host_did)
    item["binding"]["runtime_authority"][KEY] = donor
    H.save_doc(host_dir, doc)
    return donor
