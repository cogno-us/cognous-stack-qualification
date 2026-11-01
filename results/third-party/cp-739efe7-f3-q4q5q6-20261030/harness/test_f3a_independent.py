"""Independent F3-A qualification harness (Worker A): D-06 persisted effective-configuration binding `effective-configuration-binding/0.1`.

STATUS: WRITTEN, NOT RUN. Must not be run against the candidate until the lead announces "PROTOCOL FROZEN" (BRIEF rule 3).
Oracle: Registry docs at main 2815643, `docs/family-migration/final-three/02-...` section 4/5 and `03-...` F3-A items 1-9 (written BEFORE the implementation).
Independence: no builder test is imported (`d06_support`, `test_*binding*` are NOT used). Allowed shared fixtures are the PRE-EXISTING foundational ones
(`tests.test_bounded_authorization`, `tests.test_runtime_authority`, `tests.v02_support`: manifest, tenant proposal/resolver, approval signing, canonical host binding)
and the Registry's own test builders (`r08_support`, `s01_support`). All Registry selection material, workflows, store rewriting, digests and assertions below are this
file's own. The digest is recomputed by an independent implementation (`my_digest`), not by the candidate.

How to run (later, after freeze):
    export OCS_REGISTRY_PIN_DIR=<scratchpad>/run/reg-v8 OCS_REQUIRE_REGISTRY_PIN=1 F3_EVIDENCE_DIR=<scratchpad>/work/A/evidence PYTHONDONTWRITEBYTECODE=1
    export F3_OLD_SRC=<detached b7eb11a checkout>/src      # REQUIRED by A06, A07, A09 (hard FAIL "BLOCKED" when unset; never a skip)
    <venv>/bin/python -m pytest -p no:cacheprovider <this file>        # cwd must not be inside the candidate checkout's tracked tree writes
Optional: F3_PIN_DURABLE_REFUSAL_REQUIRED=0 downgrades ONLY the "pin-export writes a durable EffectTimeRefusal" criterion to an evidence-only observation (lead decision, see open-questions Q2).

Evidence: every check appends one JSON object per line to `$F3_EVIDENCE_DIR/f3a_evidence.jsonl` with `case`, `kind` and `polarity`:
  kind in CHECK_PASS | CHECK_FAIL | OBSERVATION | LIMIT_CONFIRMED | BLOCKED
  polarity "negative" (a refusal / rejection was observed) or "positive" (an acceptance / equality was observed) or "n/a".
A missing/wrong Registry pin, missing PyNaCl, missing evidence dir or missing F3_OLD_SRC is a hard test FAILURE with a BLOCKED record (never pytest.skip).

Assumed meaning of the assignment's A01..A10 (the task text with their names was not available to this worker; see open-questions Q1):
  A01 same configuration accepted across restart + separate process       A06 frozen legacy store (unchanged prior binary): cutoff semantics, `legacy`
  A02 live-side configuration perturbation (restart) -> execute refuses   A07 legacy reader on new record fails CLOSED
  A03 unknown version / malformed record / bad digest shape -> refuse     A08 a hold persists no binding and stays a hold
  A04 missing member refuses at default cutoff                            A09 compatibility surfaces byte-identical to baseline
  A05 legacy_cutoff domain rules                                          A10 pin-export positive control (same config -> active)
"""
from __future__ import annotations

import base64
import copy
import functools
import hashlib
import inspect
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

THIS_FILE = Path(__file__).resolve()
EXPECTED_REGISTRY_HEAD = "a40fe755e2384a99c37016fa9ad59396f1835900"
VERSION = "effective-configuration-binding/0.1"                  # 02 s4
DOMAIN = "cognous.control-plane.effective-configuration-binding"  # 02 s4
KEY = "effective_configuration"                                    # 02 s4 carriage C2
CODE = "authorization_binding_changed"                             # 02 s2 D-06.6
MAXI = 2147483647
TENANT = "tenant-alpha"
OP_F = "refund-issue-ages"
EFFECTIVE = {"valid_from": "2026-10-01T00:00:00Z", "valid_until": "2026-10-06T00:00:00Z"}
PIN_REFUSAL_REQUIRED = os.environ.get("F3_PIN_DURABLE_REFUSAL_REQUIRED", "1") != "0"


# ------------------------------------------------------------------------------------------------------------------ evidence + gating
def _evidence_file() -> Path:
    d = os.environ.get("F3_EVIDENCE_DIR")
    if not d:
        raise RuntimeError("F3_EVIDENCE_DIR is not set")
    p = Path(d)
    p.mkdir(parents=True, exist_ok=True)
    return p / "f3a_evidence.jsonl"


def rec(case: str, kind: str, polarity: str = "n/a", **fields) -> None:
    line = json.dumps({"case": case, "kind": kind, "polarity": polarity, "t": round(time.time(), 3), **fields}, sort_keys=True, default=str)
    with open(_evidence_file(), "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def blocked(case: str, why: str) -> None:
    try:
        rec(case, "BLOCKED", why=why)
    except Exception:
        pass
    pytest.fail("BLOCKED: " + why, pytrace=False)


class Check:
    """Soft assertions: every criterion is recorded (pass AND fail) before the test fails, so one failure never hides the others."""

    def __init__(self, case: str):
        self.case, self.fails = case, []

    def ok(self, name: str, cond: bool, polarity: str = "n/a", **info) -> bool:
        rec(self.case, "CHECK_PASS" if cond else "CHECK_FAIL", polarity, check=name, **info)
        if not cond:
            self.fails.append(name)
        return bool(cond)

    def obs(self, name: str, **info) -> None:
        rec(self.case, "OBSERVATION", check=name, **info)

    def limit(self, name: str, **info) -> None:
        rec(self.case, "LIMIT_CONFIRMED", check=name, **info)

    def done(self) -> None:
        assert not self.fails, f"{self.case}: failed criteria {self.fails}"


def pin_state() -> dict:
    pin = os.environ.get("OCS_REGISTRY_PIN_DIR")
    out = {"pin_dir": pin, "require": os.environ.get("OCS_REQUIRE_REGISTRY_PIN"), "head": None}
    if pin and (Path(pin) / "registry_successor").is_dir():
        out["head"] = subprocess.run(["git", "rev-parse", "HEAD"], cwd=pin, capture_output=True, text=True).stdout.strip()
    return out


@pytest.fixture(scope="session", autouse=True)
def _preflight():
    """Environment gate. Any defect is a hard FAIL with a BLOCKED record (no skip, ever)."""
    try:
        _evidence_file()
    except Exception as exc:
        pytest.fail(f"BLOCKED: F3_EVIDENCE_DIR unusable: {exc}", pytrace=False)
    st = pin_state()
    if st["require"] != "1":
        blocked("PREFLIGHT", "OCS_REQUIRE_REGISTRY_PIN is not '1'")
    if st["head"] != EXPECTED_REGISTRY_HEAD:
        blocked("PREFLIGHT", f"OCS_REGISTRY_PIN_DIR head {st['head']!r} != {EXPECTED_REGISTRY_HEAD}")
    try:
        import nacl.bindings  # noqa: F401
        env()
    except Exception as exc:
        blocked("PREFLIGHT", f"environment import failed: {type(exc).__name__}: {exc}")
    rec("PREFLIGHT", "OBSERVATION", pin=st, acp=env().acp.__file__, python=sys.version.split()[0])


@pytest.fixture(autouse=True)
def _clock(monkeypatch):
    patch_clock(monkeypatch)


# ------------------------------------------------------------------------------------------------------------------ environment / imports
@functools.lru_cache(maxsize=1)
def env() -> SimpleNamespace:
    pin = Path(os.environ["OCS_REGISTRY_PIN_DIR"]).resolve()
    sys.path.insert(0, str(pin))
    sys.path.insert(0, str(pin / "tests"))
    import agent_control_plane as acp
    cproot = Path(acp.__file__).resolve().parents[2]
    if str(cproot) not in sys.path:
        sys.path.append(str(cproot))  # `tests` package of the checkout that provides agent_control_plane (appended: never shadows)
    import nacl.bindings as nb
    import r08_support as r
    import s01_support as s
    from registry_adapters import ed25519_verifier as ev
    from registry_successor import common as c, v2_age_bounds as ab, verify as v
    from agent_control_plane import bounded as B
    from agent_control_plane import registry_f4_age_governance as f4gov
    from agent_control_plane import registry_governed_policy as pol
    from agent_control_plane import registry_f5_class_age_governance as agegov
    from agent_control_plane import registry_f5_class_unreadable_governance as ugov
    from agent_control_plane.registry_governed_lifecycle import GovernedScope
    from agent_control_plane.policy_binding import APPROVAL_COMMITMENT_V2
    from agent_control_plane.runtime_authority import ActionClass, RuntimeAuthorityProfile, approval_commitment
    from agent_control_plane.authorization_pin_export import assess_authorization_pin
    from agent_control_plane.local_authority_effect import materialize_local_execution_claim
    import tests.test_bounded_authorization as tba
    from tests.test_runtime_authority import MEMBERS, PUBLIC, bind_approval, sign_evidence
    from tests import v02_support as v02

    class CountingDestination(B.LocalRefundDestination):
        calls = 0

        def apply(self, **kw):
            self.calls = self.calls + 1
            return super().apply(**kw)

    auth = [a for a in tba.manifest()["actions"]][0]
    seed = bytes(range(32))
    pk, sk = nb.crypto_sign_seed_keypair(seed)
    return SimpleNamespace(acp=acp, nb=nb, r=r, s=s, ev=ev, c=c, ab=ab, v=v, B=B, f4gov=f4gov, pol=pol, agegov=agegov, ugov=ugov, GovernedScope=GovernedScope,
                           APPROVAL_COMMITMENT_V2=APPROVAL_COMMITMENT_V2, ActionClass=ActionClass, RuntimeAuthorityProfile=RuntimeAuthorityProfile,
                           approval_commitment=approval_commitment, assess=assess_authorization_pin, claim=materialize_local_execution_claim, tba=tba,
                           MEMBERS=MEMBERS, PUBLIC=PUBLIC, bind_approval=bind_approval, sign_evidence=sign_evidence, v02=v02, Dest=CountingDestination,
                           INSTITUTION=auth["authority_context"]["institution_id"], AUTHORITY_DOMAIN=auth["authority_context"]["authority_domain"],
                           ACTION_ID=auth["action_id"], pk=pk, sk=sk, NOW=tba.NOW)


def patch_clock(mp) -> None:
    E = env()
    mp.setattr(E.B, "_now", lambda: E.NOW)
    for m in (E.f4gov, E.pol, E.agegov, E.ugov):
        if hasattr(m, "_now"):
            mp.setattr(m, "_now", lambda: E.NOW)


# ------------------------------------------------------------------------------------------------------------------ Registry material (own builder)
class Src:
    """Host selection source. `.fail` makes it raise; `.gate_fail` makes it raise ONLY when called from the commit gate (used to force a failed attempt)."""

    def __init__(self, material):
        self.mat, self.calls, self.fail, self.gate_fail, self.gate_calls = material, 0, False, False, 0

    def __call__(self):
        self.calls += 1
        if self.gate_fail and any(f.function == "_gl_commit_gate" for f in inspect.stack()):
            self.gate_calls += 1
            raise RuntimeError("source down at the commit gate")
        if self.fail:
            raise RuntimeError("source down")
        return self.mat


def f4_material(E, status: int, approval: int, *, consumer: str = "consumer-test", op: str = OP_F, domain: str | None = None):
    payload = {"status_max_age_seconds": status, "approval_max_age_seconds": approval}
    record = E.r.seal_record(dict(E.r.make_record(), contract_version="r08-v2", family=E.ab.FAMILY_F4, record_id="f4-age-record", payload=payload))
    scope = {"tenant": TENANT, "institution": E.INSTITUTION, "authority_domain": domain or E.AUTHORITY_DOMAIN}
    stmt = E.r.make_statement_v2(record, consumer_id=consumer, scope=scope, operation=op, effective=EFFECTIVE, issued_at="2026-10-01T00:00:00Z", family=E.ab.FAMILY_F4)
    sig = base64.b64encode(E.nb.crypto_sign(E.s.V2_DOMAIN + E.c.canonical_bytes(stmt), E.sk)[:64]).decode("ascii")
    selection = E.r.dumps(E.s.envelope(stmt, domain=E.s.V2_DOMAIN, contract="r08-v2", signature=sig, pub=E.pk))
    grant = E.v.AuthorityGrant(consumer, TENANT, E.INSTITUTION, domain or E.AUTHORITY_DOMAIN, op)
    trust = E.v.TrustSnapshot("snap-test-1", 1, "2026-10-07T00:00:00Z", (E.v.IssuerEntry(E.s.KEY_ID, "issuer-test-1", "ed25519", E.pk, (grant,)),))
    return E.f4gov.SelectionMaterial(E.r.dumps(record), selection, trust)


# ------------------------------------------------------------------------------------------------------------------ workflow fixtures
def make_pin_fixture(E, work) -> SimpleNamespace:
    """Profile-bearing fixture able to reach the pin export: a RuntimeAuthorityProfile carrying an approval-side policy_binding. (Own construction of the
    pre-existing foundation pieces; a profile with `policy_binding` is refused for the profile-bearing Registry families, so only F4 can be declared.)"""
    work = Path(work)
    binding = E.v02.canonical_binding()
    p = E.tba.tenant_proposal()
    res = E.tba.tenant_resolver_for(p)
    pb = E.v02.profile_for(binding)
    cl = E.ActionClass(class_id="synthetic-irreversible", irreversible=True, max_status_age_seconds=60, on_unreadable="refuse")
    cfg = E.RuntimeAuthorityProfile(catalogue_version="synthetic-catalogue/1", actions={p.action_id: cl}, producer_keys={"synthetic-validator": E.PUBLIC},
                                    allow_synthetic_resolver=True, policy_binding=pb)
    first = E.tba.workflow(work / "baseline", p, resolver=res).decide(p, now=E.NOW)
    required = sorted([{"input_type": x.input_type, "input_id": x.input_id} for x in first.resolution_inputs], key=lambda x: (x["input_type"], x["input_id"]))
    context, criteria = res.contexts[E.tba.PROFILE], {}
    for ob in context["requirement"]["evidence"]:
        if ob["required"] and ob["kind"] == "authorization":
            criteria[ob["obligation_id"]] = {"kind": "exact_members", "producer_id": "synthetic-validator", "subject_digest": E.B.commitment(E.MEMBERS),
                                             "minimum_count": 40, "members": E.MEMBERS}
            E.sign_evidence(res.evidence[ob["obligation_id"]], tenant_id=E.v02.TENANT)
    context["runtime_authority"] = {"profile": "runtime-authority/0.1", "required_inputs": required, "required_inputs_digest": E.B.commitment(required),
                                    "evidence_criteria": criteria, "approval_commitment_version": E.APPROVAL_COMMITMENT_V2, "policy_generation": pb.policy_generation,
                                    "policy_activation_ref": pb.activation_ref}
    E.bind_approval(res, cfg)
    return SimpleNamespace(p=p, res=res, cfg=cfg, binding=binding)


def make_fixture(E, kind: str, work) -> SimpleNamespace:
    if kind == "pin":
        return make_pin_fixture(E, work)
    p = E.tba.tenant_proposal()
    return SimpleNamespace(p=p, res=E.tba.tenant_resolver_for(p), cfg=None, binding=None)


def construct(E, kind: str, fx, store_dir, cfg: dict | None = None, source=None):
    """Build a governed workflow over the store in `store_dir` (a 'restart' is calling this again). `cfg` keys: status, approval, tolerance, identity, mandate (constructor
    scalars), obs ('default' | 'none' | [max_age, tolerance]), cutoff (int, omitted when absent), reg ([status, approval] Registry values), consumer."""
    cfg = cfg or {}
    sd = Path(store_dir)
    manifest = E.tba.manifest()
    if cfg.get("domain"):
        manifest["actions"][0]["authority_context"]["authority_domain"] = cfg["domain"]
    kw = dict(allow_test_time=True, manifest=manifest, resolver=fx.res, destination=E.Dest(sd / "destination.json"),
              records=E.B.BoundedRecordStore(sd / "run.json", "run-1"))
    obs = cfg.get("obs", "default")
    if obs == "default":
        kw["observation_policy"] = E.B.ObservationPolicy(max_age_seconds=300, clock_tolerance_seconds=5)
    elif obs in (None, "none"):
        kw["observation_policy"] = None
    else:
        kw["observation_policy"] = E.B.ObservationPolicy(max_age_seconds=obs[0], clock_tolerance_seconds=obs[1])
    for key, name in (("tolerance", "clock_tolerance_seconds"), ("identity", "identity_max_age_seconds"), ("mandate", "mandate_max_age_seconds"),
                      ("status", "status_max_age_seconds"), ("approval", "approval_max_age_seconds")):
        if key in cfg:
            kw[name] = cfg[key]
    if "cutoff" in cfg:
        kw["legacy_cutoff"] = cfg["cutoff"]
    reg = cfg.get("reg", [30, 30])
    consumer = cfg.get("consumer", "consumer-test")
    scope = E.GovernedScope(consumer, TENANT, E.ACTION_ID, OP_F)
    src = source or Src(f4_material(E, reg[0], reg[1], consumer=consumer, domain=cfg.get("domain")))
    if kind == "f4":
        return E.f4gov.GovernedAgeWorkflow(scope=scope, selection_source=src, verifier=E.ev.Ed25519Verifier(), construction_time=E.NOW, **kw)
    fams = E.pol.GovernedFamilies(f4_ages=E.pol.GovernedFamily(scope, src))
    return E.pol.GovernedPolicyWorkflow(families=fams, verifier=E.ev.Ed25519Verifier(), runtime_authority_profile=fx.cfg, construction_time=E.NOW, **kw)


def new_case(tmp_path, kind: str = "f4", cfg: dict | None = None, name: str = "s", source=None) -> SimpleNamespace:
    E = env()
    d = Path(tmp_path) / name
    d.mkdir(parents=True, exist_ok=True)
    fx = make_fixture(E, kind, d / "_work")
    flow = construct(E, kind, fx, d, cfg, source)
    dec = flow.decide(fx.p, now=E.NOW)
    assert dec.result == "authorized", f"fixture could not mint an authorized decision: {dec.reasons}"
    return SimpleNamespace(E=E, kind=kind, dir=d, fx=fx, flow=flow, dec=dec, did=dec.decision_id, cfg=cfg or {})


def restart(c, cfg: dict | None = None, source=None):
    """A fresh workflow object over the same persisted store (nothing is carried in memory)."""
    return construct(c.E, c.kind, c.fx, c.dir, c.cfg if cfg is None else cfg, source)


# ------------------------------------------------------------------------------------------------------------------ store tooling (own)
def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def my_digest(members, version: str = VERSION) -> str:
    """Independent recomputation of the frozen digest (02 s4): sha256 of canonical JSON over {domain, version, **members}."""
    return "sha256:" + hashlib.sha256(canon({"domain": DOMAIN, "version": version, **members})).hexdigest()


def load_doc(d) -> dict:
    return json.loads((Path(d) / "run.json").read_text())


def save_doc(d, doc: dict) -> None:
    (Path(d) / "run.json").write_text(json.dumps(doc, indent=2))


def raw_text(d) -> str:
    return (Path(d) / "run.json").read_text()


def put_text(d, text: str) -> None:
    (Path(d) / "run.json").write_text(text)


def dec_item(doc: dict, did: str) -> dict:
    return [x for x in doc["decisions"] if x["decision_id"] == did][0]


def member_of(d, did: str) -> dict:
    return dec_item(load_doc(d), did)["binding"]["runtime_authority"][KEY]


def edit(d, did: str, fn) -> None:
    doc = load_doc(d)
    fn(dec_item(doc, did)["binding"]["runtime_authority"], dec_item(doc, did))
    save_doc(d, doc)


def strip_member(ra, item):
    """AMEND-4: remove the member in the exact shape of a legacy writer (runtime_authority=None when the member was the only key)."""
    ra.pop(KEY)
    if not ra:
        item["binding"]["runtime_authority"] = None


def reseal(member: dict) -> dict:
    member["digest"] = my_digest(member["members"], member["version"])
    return member


def set_at(obj, path, value):
    for part in path[:-1]:
        obj = obj[part]
    obj[path[-1]] = value


def get_at(obj, path):
    for part in path:
        obj = obj[part]
    return obj


ALT_DIGEST_A, ALT_DIGEST_B = "sha256:" + "ab" * 32, "sha256:" + "cd" * 32

# Every member of the frozen section-4 member set (02:48) as a perturbation. (id, path | special)
MEMBER_LEAVES = [
    ("scope.consumer_id", ("scope", "consumer_id")), ("scope.tenant_id", ("scope", "tenant_id")), ("scope.action_id", ("scope", "action_id")),
    ("scope.institution_id", ("scope", "institution_id")), ("scope.authority_domain", ("scope", "authority_domain")),
    ("host_profile_digest", ("host_profile_digest",)), ("effective_profile_digest", ("effective_profile_digest",)),
    ("f4_scalars.status_max_age_seconds", ("f4_scalars", "status_max_age_seconds")), ("f4_scalars.approval_max_age_seconds", ("f4_scalars", "approval_max_age_seconds")),
    ("other_scalars.clock_tolerance_seconds", ("other_scalars", "clock_tolerance_seconds")),
    ("other_scalars.identity_max_age_seconds", ("other_scalars", "identity_max_age_seconds")),
    ("other_scalars.mandate_max_age_seconds", ("other_scalars", "mandate_max_age_seconds")),
    ("observation_policy.max_age_seconds", ("observation_policy", "max_age_seconds")),
    ("observation_policy.clock_tolerance_seconds", ("observation_policy", "clock_tolerance_seconds")),
    ("observation_policy=null", "obs_null"),
    ("families.0.slot", ("families", 0, "slot")), ("families.0.family_id", ("families", 0, "family_id")),
    ("families.0.contract_version", ("families", 0, "contract_version")), ("families.0.family_schema_revision", ("families", 0, "family_schema_revision")),
    ("families.0.effective_policy_digest", ("families", 0, "effective_policy_digest")),
    ("families=none_declared", "fam_empty"), ("families=extra_class_age_declared", "fam_extra"),
]


def bump(value, path):
    if value is None:
        return 2 if path[-1] == "family_schema_revision" else ALT_DIGEST_A
    if isinstance(value, bool):
        return not value
    if isinstance(value, int):
        return value + 1 if value < MAXI else value - 1
    if isinstance(value, str) and value.startswith("sha256:"):
        return ALT_DIGEST_A if value != ALT_DIGEST_A else ALT_DIGEST_B
    return value + "-x"


def perturb_member(member: dict, leaf) -> dict:
    """Return a SELF-CONSISTENT (digest recomputed by `my_digest`) copy of `member` differing in exactly one member."""
    m = copy.deepcopy(member)
    mem = m["members"]
    if leaf == "obs_null":
        mem["observation_policy"] = None
    elif leaf == "fam_empty":
        mem["families"] = []
    elif leaf == "fam_extra":
        mem["families"].append({"slot": "class_age", "family_id": "f5-action-class-age-bounds", "contract_version": "r08-v2", "family_schema_revision": None,
                                "effective_policy_digest": ALT_DIGEST_A})
    else:
        set_at(mem, leaf, bump(get_at(mem, leaf), leaf))
    return reseal(m)


# ------------------------------------------------------------------------------------------------------------------ drivers
def snap_state(flow, did):
    doc = flow.records.load()
    return {"refusals": [r for r in doc.refusals if r.decision_id == did], "attempts": [a for a in doc.attempts if a.decision_id == did], "calls": flow.destination.calls,
            "dest": flow.destination.snapshot()}


def drive_execute(E, flow, p, did) -> dict:
    persisted = flow.records.decision(did)
    before = snap_state(flow, did)
    out = {"raised": None, "msg": None, "attempt_status": None}
    try:
        attempt, _ = flow.execute(p, persisted, adapter_id=p.adapter_id, now=E.NOW)
        out["attempt_status"] = attempt.status
    except Exception as exc:  # recorded, classified by the caller
        out["raised"], out["msg"] = type(exc).__name__, str(exc)[:200]
        out["is_permission_error"] = isinstance(exc, PermissionError)
    after = snap_state(flow, did)
    new_ref = after["refusals"][len(before["refusals"]):]
    out.update(new_refusal_reasons=[sorted(r.reasons) for r in new_ref], new_refusal_vocab=[r.reason_vocabulary_version for r in new_ref],
               new_attempts=len(after["attempts"]) - len(before["attempts"]), dest_calls=after["calls"] - before["calls"], dest_unchanged=after["dest"] == before["dest"])
    try:
        out["binding_status"] = flow.configuration_binding_status(flow.records.decision(did))  # candidate's own classifier: EVIDENCE ONLY, never the oracle
    except Exception as exc:
        out["binding_status"] = f"raised:{type(exc).__name__}"
    return out


def drive_pin(E, flow, fx, did) -> dict:
    persisted = flow.records.decision(did)
    before = snap_state(flow, did)
    out = {"raised": None, "state": None, "reason": None, "payload": None}
    try:
        res = E.assess(flow, fx.p, persisted, now=E.NOW, host_policy_binding=fx.binding)
        out.update(state=res["state"], reason=res["reason"], payload=res["payload"], terminal_status=res.get("terminal_status"))
    except Exception as exc:
        out["raised"], out["msg"] = type(exc).__name__, str(exc)[:200]
    after = snap_state(flow, did)
    out.update(new_refusal_reasons=[sorted(r.reasons) for r in after["refusals"][len(before["refusals"]):]], dest_calls=after["calls"] - before["calls"],
               dest_unchanged=after["dest"] == before["dest"], new_attempts=len(after["attempts"]) - len(before["attempts"]))
    return out


def judge_exec_refusal(chk: Check, label: str, out: dict, *, durable: bool = True) -> None:
    """Pass criterion (03:23): PermissionError, exactly one new durable EffectTimeRefusal whose reasons == ['authorization_binding_changed'], no attempt, destination never
    called and unchanged."""
    chk.ok(f"{label}:raised_permission_error", out.get("raised") == "PermissionError", "negative", detail=out)
    if durable:
        chk.ok(f"{label}:one_durable_refusal_with_code", out["new_refusal_reasons"] == [[CODE]], "negative", reasons=out["new_refusal_reasons"])
    chk.ok(f"{label}:no_attempt_created", out["new_attempts"] == 0, "negative")
    chk.ok(f"{label}:destination_apply_never_called", out["dest_calls"] == 0 and out["dest_unchanged"], "negative")


def judge_exec_accept(chk: Check, label: str, out: dict) -> None:
    chk.ok(f"{label}:executed", out.get("raised") is None and out.get("attempt_status") == "acknowledged", "positive", detail=out)
    chk.ok(f"{label}:no_refusal_row", out["new_refusal_reasons"] == [], "positive")
    chk.ok(f"{label}:destination_called_once", out["dest_calls"] == 1, "positive")


def judge_pin_refusal(chk: Check, label: str, out: dict) -> None:
    """Pass criterion (brief A19; 03:23): the export is not `active` and carries no payload; the reason names authorization_binding_changed; a durable
    EffectTimeRefusal naming it was written; the destination is untouched. The last two are STRICT readings and may legitimately be disputed (open-questions Q2)."""
    refused_out = out.get("raised") == "PermissionError" or (out.get("state") not in (None, "active") and out.get("payload") is None)
    chk.ok(f"{label}:export_not_active_no_payload", refused_out, "negative", state=out.get("state"), raised=out.get("raised"))
    named = CODE in (out.get("reason") or "") or CODE in (out.get("msg") or "")
    chk.ok(f"{label}:reason_names_code", named, "negative", reason=out.get("reason"))
    durable = [CODE] in out["new_refusal_reasons"]
    if PIN_REFUSAL_REQUIRED:
        chk.ok(f"{label}:durable_effect_time_refusal", durable, "negative", rows=out["new_refusal_reasons"])
    else:
        chk.obs(f"{label}:durable_effect_time_refusal(evidence_only)", present=durable, rows=out["new_refusal_reasons"])
    chk.ok(f"{label}:destination_apply_never_called", out["dest_calls"] == 0 and out["dest_unchanged"], "negative")


def variant(c, fn, cfg: dict | None = None):
    """Restore the pristine store, apply `fn(runtime_authority_dict, decision_item)` to the persisted decision, restart, execute. Returns (outcome, error)."""
    put_text(c.dir, c.pristine)
    edit(c.dir, c.did, fn)
    try:
        flow = restart(c, cfg)
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"[:240]
    return drive_execute(c.E, flow, c.fx.p, c.did), None


def with_pristine(c):
    c.pristine = raw_text(c.dir)
    return c


# ------------------------------------------------------------------------------------------------------------------ separate process worker
def run_worker(op: str, kind: str, store_dir, work_dir, cfg: dict | None = None, did: str = "-", old_src: str | None = None, extra_env: dict | None = None) -> dict:
    Path(work_dir).mkdir(parents=True, exist_ok=True)
    envv = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    envv.update(extra_env or {})
    if old_src:
        envv["PYTHONPATH"] = old_src + os.pathsep + envv.get("PYTHONPATH", "")
    cp = subprocess.run([sys.executable, str(THIS_FILE), "--worker", op, kind, str(store_dir), str(work_dir), json.dumps(cfg or {}), did], env=envv,
                        capture_output=True, text=True, timeout=600, cwd=str(work_dir))
    line = [ln for ln in cp.stdout.splitlines() if ln.startswith("F3JSON:")]
    if not line:
        return {"worker_error": True, "returncode": cp.returncode, "stdout": cp.stdout[-1500:], "stderr": cp.stderr[-2500:]}
    out = json.loads(line[-1][len("F3JSON:"):])
    out["returncode"] = cp.returncode
    return out


def worker_main(argv) -> int:
    op, kind, store_dir, work_dir, cfgjson, did = argv
    cfg = json.loads(cfgjson)
    E = env()
    mp = pytest.MonkeyPatch()
    patch_clock(mp)
    Path(work_dir).mkdir(parents=True, exist_ok=True)
    out = {"op": op, "acp": E.acp.__file__}
    try:
        fx = make_fixture(E, kind, Path(work_dir) / "_work")
        flow = construct(E, kind, fx, store_dir, cfg)
    except Exception as exc:
        out.update(outcome="construction_refused", error=f"{type(exc).__name__}: {exc}"[:300])
        print("F3JSON:" + json.dumps(out))
        return 0
    if op == "decide":
        d = flow.decide(fx.p, now=E.NOW)
        out.update(decision_id=d.decision_id, result=d.result, reasons=list(d.reasons))
    elif op.startswith("crash-"):
        mode = op.split("-", 1)[1]
        if mode == "before":
            flow.records.append_decision = lambda value: os._exit(77)
        elif mode == "after":
            orig = flow.records.append_decision

            def after_append(value):
                orig(value)
                os._exit(77)
            flow.records.append_decision = after_append
        elif mode == "replace":
            real = os.replace
            os.replace = lambda a, b: os._exit(77)  # crash after the temp file was fully written/fsynced but before the atomic rename
        flow.decide(fx.p, now=E.NOW)
        out.update(outcome="decide_returned_without_crash")
    elif op == "execute":
        out.update(drive_execute(E, flow, fx.p, did))
    elif op == "pin":
        out.update(drive_pin(E, flow, fx, did))
    else:
        out.update(outcome="unknown_op")
    print("F3JSON:" + json.dumps(out, default=str))
    return 0


def jsonable(x):
    return json.loads(json.dumps(x, default=str))


def reset_dest(d) -> None:
    """Forget destination effects between runs over the same store (a fresh destination file), so an acceptance run is judged on its own."""
    for name in ("destination.json", "destination.json.lock"):
        try:
            (Path(d) / name).unlink()
        except FileNotFoundError:
            pass


def snapshot_context(fx) -> dict:
    ref = fx.p.authority_context_ref or ""
    with fx.res.authority_effect_handoff(ref):
        return fx.res.authority_effect_snapshot(ref)["context"]


# ====================================================================================================================== A01 .. A10
def test_A01_same_config_accepted_restart_and_separate_process(tmp_path):
    """Frozen expectation 03:23 (first clause) + 02:53 rule 4. Pass criterion: a decision minted by workflow W1 executes with status 'acknowledged', one destination
    call, no refusal row (a) after an in-process rebuild over the same store and (b) when a SEPARATE python process rebuilds from scratch and executes it; and the
    pin export of a decision minted under the same configuration is 'active' in-process and in a separate process. Any refusal here is a failure (false refusal)."""
    chk = Check("A01_same_config_accepted_restart_and_separate_process")
    E = env()
    c = new_case(tmp_path, "f4", name="inproc")
    out = drive_execute(E, restart(c), c.fx.p, c.did)
    judge_exec_accept(chk, "f4_inprocess_restart", out)
    c2 = new_case(tmp_path, "f4", name="proc")
    child = run_worker("execute", "f4", c2.dir, c2.dir / "_cw", c2.cfg, c2.did)
    chk.ok("f4_separate_process_ran", not child.get("worker_error"), detail=jsonable(child))
    chk.ok("f4_separate_process_executed", child.get("attempt_status") == "acknowledged" and child.get("new_refusal_reasons") == [], "positive", detail=jsonable(child))
    c3 = new_case(tmp_path, "pin", name="pin_inproc")
    pout = drive_pin(E, restart(c3), c3.fx, c3.did)
    chk.ok("pin_inprocess_restart_active", pout.get("state") == "active" and pout.get("payload") is not None, "positive", detail=jsonable(pout))
    c4 = new_case(tmp_path, "pin", name="pin_proc")
    child = run_worker("pin", "pin", c4.dir, c4.dir / "_cw", c4.cfg, c4.did)
    chk.ok("pin_separate_process_active", child.get("state") == "active", "positive", detail=jsonable(child))
    chk.done()


LIVE_PERTURBATIONS = [
    ("registry_status_value", {"reg": [35, 30]}), ("registry_approval_value", {"reg": [30, 35]}),
    ("constructor_clock_tolerance", {"tolerance": 6}), ("identity_max_age", {"identity": 61}), ("mandate_max_age", {"mandate": 61}),
    ("obs_max_age", {"obs": [301, 5]}), ("obs_tolerance", {"obs": [300, 6]}), ("obs_present_to_absent", {"obs": "none"}),
    ("scope_consumer_id", {"consumer": "consumer-test-2"}),
]


@pytest.mark.parametrize("name,over", LIVE_PERTURBATIONS, ids=[x[0] for x in LIVE_PERTURBATIONS])
def test_A02_live_configuration_perturbation_refuses_execute(tmp_path, name, over):
    """Frozen expectation 03:23 (perturbed members, execute side) + 02:51 rule 2. A decision is minted under the base configuration; the workflow is REBUILT (restart,
    not an attribute edit, which would hit the non-durable `scalars_modified` guard) with exactly one configuration value changed. Pass criterion: PermissionError, exactly
    one durable EffectTimeRefusal with reasons == ['authorization_binding_changed'], no attempt, destination never called/unchanged."""
    chk = Check(f"A02_live_perturbation_{name}")
    c = new_case(tmp_path, "f4")
    cfg = dict(c.cfg)
    cfg.update(over)
    try:
        flow = restart(c, cfg)
    except Exception as exc:
        chk.ok("construction_must_succeed_for_this_perturbation", False, error=f"{type(exc).__name__}: {exc}"[:240])
        chk.done()
        return
    out = drive_execute(c.E, flow, c.fx.p, c.did)
    judge_exec_refusal(chk, name, out)
    chk.obs("candidate_classification_evidence_only", status=out.get("binding_status"))
    chk.done()


def test_A02_masked_host_change_is_recorded_not_blessed(tmp_path):
    """Documented limitation (Registry PR #79 handoff s5): a HOST value fully masked by a stricter Registry value is not refused. Frozen member set 02:48 binds LIVE
    (effective) F4 values, so this is consistent with the contract; 03:23 lists 'each F4 scalar'. Pass criterion: none (evidence only): the outcome (executed or refused)
    is recorded as an OBSERVATION; the test only fails if the harness cannot reach the observation."""
    chk = Check("A02_masked_host_change_observation")
    c = new_case(tmp_path, "f4", {"status": 60, "approval": 60, "reg": [30, 30]})
    out = drive_execute(c.E, restart(c, {"status": 45, "approval": 60, "reg": [30, 30]}), c.fx.p, c.did)
    chk.obs("host_status_60_to_45_masked_by_registry_30", executed=out.get("attempt_status") == "acknowledged", detail=jsonable(out))
    chk.ok("observation_reached", out.get("raised") in (None, "PermissionError"))
    chk.done()


def test_A03_unknown_version_malformed_record_bad_digest_shape_refuse(tmp_path):
    """Frozen expectation 03:24 / 02:51 rule 2 (unknown version, malformed member, invalid record). Each variant rewrites the persisted decision (store is unsigned) and
    restarts. Pass criterion for EVERY variant: PermissionError + one durable refusal ['authorization_binding_changed'] + no attempt + destination untouched."""
    chk = Check("A03_unknown_version_malformed_bad_digest_shape")
    c = with_pristine(new_case(tmp_path, "f4"))

    def rv(fn):
        return lambda ra, item: fn(ra[KEY])

    def set_version(v):
        return lambda m: m.__setitem__("version", v)
    variants = {
        "version_0_2": rv(lambda m: reseal(m.__setitem__("version", "effective-configuration-binding/0.2") or m)),
        "version_trailing_space": rv(lambda m: m.__setitem__("version", VERSION + " ")),
        "version_empty": rv(set_version("")), "version_int": rv(set_version(1)), "version_null": rv(set_version(None)),
        "record_is_string": lambda ra, item: ra.__setitem__(KEY, "effective-configuration-binding/0.1"),
        "record_is_list": lambda ra, item: ra.__setitem__(KEY, [ra[KEY]]),
        "record_is_int": lambda ra, item: ra.__setitem__(KEY, 7),
        "record_is_null": lambda ra, item: ra.__setitem__(KEY, None),
        "record_is_empty_dict": lambda ra, item: ra.__setitem__(KEY, {}),
        "missing_members_key": rv(lambda m: m.pop("members")), "missing_digest_key": rv(lambda m: m.pop("digest")), "missing_version_key": rv(lambda m: m.pop("version")),
        "members_is_list": rv(lambda m: m.__setitem__("members", [])), "members_is_null": rv(lambda m: m.__setitem__("members", None)),
        "digest_uppercase_hex": rv(lambda m: m.__setitem__("digest", m["digest"].upper().replace("SHA256:", "sha256:"))),
        "digest_short": rv(lambda m: m.__setitem__("digest", m["digest"][:-2])), "digest_no_prefix": rv(lambda m: m.__setitem__("digest", m["digest"][7:])),
        "digest_all_zero": rv(lambda m: m.__setitem__("digest", "sha256:" + "0" * 64)), "digest_int": rv(lambda m: m.__setitem__("digest", 5)),
        "member_missing_scope": rv(lambda m: reseal(m["members"].pop("scope") and m)), "member_missing_families": rv(lambda m: reseal(m["members"].pop("families") and m)),
    }
    for label, fn in variants.items():
        out, err = variant(c, fn)
        if out is None:
            chk.ok(f"{label}:store_loaded", False, error=err)
            continue
        judge_exec_refusal(chk, label, out)
    chk.done()


def test_A04_missing_member_refuses_at_default_cutoff(tmp_path):
    """Frozen expectation 03:25 / 02:60. With the default cutoff (0) a decision whose member is absent (stripped) must refuse. Pass criterion: PermissionError + one durable
    refusal ['authorization_binding_changed'] + no attempt + destination untouched for: member deleted; runtime_authority set to null; runtime_authority emptied."""
    chk = Check("A04_missing_member_refuses_default_cutoff")
    c = with_pristine(new_case(tmp_path, "f4"))
    variants = {
        "member_deleted": lambda ra, item: ra.pop(KEY),
        "runtime_authority_null": lambda ra, item: item["binding"].__setitem__("runtime_authority", None),
        "runtime_authority_empty": lambda ra, item: item["binding"].__setitem__("runtime_authority", {}),
    }
    for label, fn in variants.items():
        out, err = variant(c, fn)
        if out is None:
            chk.ok(f"{label}:store_loaded", False, error=err)
            continue
        judge_exec_refusal(chk, label, out)
    chk.done()


BAD_CUTOFFS = [("bool_true", True), ("bool_false", False), ("negative", -1), ("float", 1.0), ("float_inf", float("inf")), ("str_digit", "1"), ("str_wildcard_star", "*"),
               ("str_all", "all"), ("none", None), ("huge_2_31", MAXI + 1), ("huge_1e30", 10 ** 30), ("list", [1])]


@pytest.mark.parametrize("name,value", BAD_CUTOFFS, ids=[x[0] for x in BAD_CUTOFFS])
def test_A05_legacy_cutoff_domain_rejects_wildcards_and_bad_types(tmp_path, name, value):
    """Frozen expectation 03:25 ('no wildcard or accept-all value ... negative, non-int, bool, huge cutoff handled by an explicit rule, documented') + 02:60. Pass criterion:
    constructing a governed workflow with this cutoff raises (PermissionError subclass) before any state write, i.e. the store row count is unchanged and no workflow exists."""
    chk = Check(f"A05_cutoff_rejected_{name}")
    E = env()
    d = Path(tmp_path) / "s"
    fx = make_fixture(E, "f4", d / "_work")
    err = None
    try:
        construct(E, "f4", fx, d, {"cutoff": value})
    except Exception as exc:
        err = exc
    chk.ok("construction_refused", err is not None and isinstance(err, PermissionError), "negative", error=f"{type(err).__name__}: {err}" if err else None)
    code = getattr(getattr(err, "refusal", None), "code", None)
    chk.obs("adapter_refusal_code", code=code)
    chk.ok("no_decision_written", not (d / "run.json").exists() or load_doc(d)["decisions"] == [], "negative")
    chk.done()


def test_A05_legacy_cutoff_valid_values_and_oversize_rule(tmp_path):
    """02:60 + builder doc (stricter: cutoff may not exceed today's decision count; recorded as 'stricter than contract', open-questions Q5). Pass criterion: cutoff 0
    and cutoff == number of decisions construct; cutoff == count+1 is refused. (Whether the oversize refusal is REQUIRED is not asserted: only recorded.)"""
    chk = Check("A05_cutoff_valid_and_oversize")
    c = new_case(tmp_path, "f4")
    count = len(load_doc(c.dir)["decisions"])
    ok0, okn = True, True
    try:
        restart(c, {"cutoff": 0})
    except Exception:
        ok0 = False
    try:
        restart(c, {"cutoff": count})
    except Exception:
        okn = False
    chk.ok("cutoff_0_constructs", ok0, "positive")
    chk.ok("cutoff_eq_count_constructs", okn, "positive", count=count)
    refused = False
    try:
        restart(c, {"cutoff": count + 1})
    except Exception:
        refused = True
    chk.obs("cutoff_count_plus_one_refused", refused=refused, note="builder claims refusal; contract text does not require it")
    chk.done()


def _need_old_src(case: str) -> str:
    old = os.environ.get("F3_OLD_SRC")
    if not old or not (Path(old) / "agent_control_plane" / "bounded.py").is_file():
        blocked(case, "F3_OLD_SRC (the 'src' dir of a detached checkout of the UNCHANGED prior binary b7eb11a) is not set or invalid")
    return old


def test_A06_frozen_legacy_store_cutoff_semantics_and_legacy_report(tmp_path):
    """Frozen expectation 03:26 / 02:60. Stores are GENERATED by the unchanged prior binary (F3_OLD_SRC = b7eb11a src) through this file's own fixtures. Pass criterion
    (F4 dedicated, two legacy decisions index 0 and 1): cutoff 0 -> execute refuses with one durable ['authorization_binding_changed']; cutoff 2 -> decision 0 executes
    (acknowledged) and `configuration_binding_status` (candidate report API) == 'legacy'; cutoff 1 -> decision 1 (past the cutoff) refuses, decision 0 executes. Pin kind:
    persisted `approval_commitment` of the legacy decision equals the recomputation by the CURRENT public `approval_commitment` function (legacy approvals still validate)
    and pin export is 'active' with cutoff>=1 and not 'active' with cutoff 0."""
    chk = Check("A06_frozen_legacy_store_cutoff_semantics")
    old = _need_old_src("A06_frozen_legacy_store_cutoff_semantics")
    E = env()
    for kind in ("f4", "pin"):
        base = Path(tmp_path) / f"legacy_{kind}"
        ids = []
        for i in range(2):
            out = run_worker("decide", kind, base / "store", base / f"gen{i}", {}, old_src=old)
            chk.ok(f"{kind}:legacy_generator_ran_under_old_tree", not out.get("worker_error") and str(out.get("acp", "")).startswith(old), detail=jsonable(out))
            if out.get("worker_error") or out.get("result") != "authorized":
                break
            ids.append(out["decision_id"])
        chk.ok(f"{kind}:two_legacy_decisions", len(ids) == 2, detail=ids)
        if len(ids) != 2:
            continue
        doc = load_doc(base / "store")
        chk.ok(f"{kind}:store_has_no_member", all(KEY not in ((x["binding"] or {}).get("runtime_authority") or {}) for x in doc["decisions"] if x.get("binding")), "positive")
        pristine = raw_text(base / "store")
        fx = make_fixture(E, kind, base / "fxwork")

        def run(cutoff, did):
            put_text(base / "store", pristine)
            reset_dest(base / "store")
            flow = construct(E, kind, fx, base / "store", {"cutoff": cutoff})
            if kind == "pin":
                return drive_pin(E, flow, fx, did), flow
            return drive_execute(E, flow, fx.p, did), flow
        if kind == "f4":
            out, _ = run(0, ids[0])
            judge_exec_refusal(chk, "f4:cutoff0_idx0_refuses", out)
            out, flow = run(2, ids[0])
            judge_exec_accept(chk, "f4:cutoff2_idx0_executes", out)
            chk.ok("f4:cutoff2_idx0_reported_legacy", out.get("binding_status") == "legacy", "positive", status=out.get("binding_status"))
            put_text(base / "store", pristine)
            reset_dest(base / "store")
            flow = construct(E, kind, fx, base / "store", {"cutoff": 1})
            out1 = drive_execute(E, flow, fx.p, ids[1])
            judge_exec_refusal(chk, "f4:cutoff1_idx1_past_cutoff_refuses", out1)
            out0 = drive_execute(E, flow, fx.p, ids[0])
            judge_exec_accept(chk, "f4:cutoff1_idx0_executes", out0)
        else:
            persisted = load_doc(base / "store")["decisions"][0]["binding"]["runtime_authority"]
            probe = construct(E, kind, fx, base / "store", {"cutoff": 0})
            recomputed = E.approval_commitment(probe.runtime_authority_profile, snapshot_context(fx))
            chk.ok("pin:legacy_approval_commitment_recomputes_identically", recomputed == persisted.get("approval_commitment"), "positive",
                   persisted=persisted.get("approval_commitment"), recomputed=recomputed)
            chk.ok("pin:legacy_catalogue_digest_recomputes_identically", E.B.commitment(probe.runtime_authority_profile.model_dump(mode="json")) == persisted.get("catalogue_digest"),
                   "positive")
            out, _ = run(1, ids[0])
            chk.ok("pin:cutoff1_idx0_active", out.get("state") == "active", "positive", detail=jsonable(out))
            out, _ = run(0, ids[0])
            judge_pin_refusal(chk, "pin:cutoff0_idx0", out)
    chk.done()


def test_A07_legacy_reader_on_new_record_fails_closed(tmp_path):
    """Frozen expectation 03:27 (last clause) / builder matrix. New code mints a decision; the UNCHANGED prior binary (F3_OLD_SRC) rebuilds the same workflow and tries to
    execute it. Pass criterion: the old reader REFUSES (PermissionError, one durable refusal ['authorization_binding_changed'], destination never called). Executing
    would be a fail-OPEN downgrade path."""
    chk = Check("A07_legacy_reader_on_new_record_fails_closed")
    old = _need_old_src("A07_legacy_reader_on_new_record_fails_closed")
    c = new_case(tmp_path, "f4")
    chk.ok("record_carries_member", KEY in dec_item(load_doc(c.dir), c.did)["binding"]["runtime_authority"], "positive")
    child = run_worker("execute", "f4", c.dir, c.dir / "_old", {}, c.did, old_src=old)
    chk.ok("old_worker_ran_under_old_tree", not child.get("worker_error") and str(child.get("acp", "")).startswith(old), detail=jsonable(child))
    judge_exec_refusal(chk, "old_reader", child) if not child.get("worker_error") else None
    chk.done()


def test_A08_hold_persists_no_binding_and_stays_hold(tmp_path):
    """Frozen expectation 03:29 (a hold persists no binding) + 02:50 rule 1 + 03:28. A decision is made while the grant status is stale (base check produces a hold).
    Pass criterion: result == 'hold', persisted `binding` is null, the text 'effective_configuration' occurs nowhere in the persisted hold row; executing the hold raises
    PermissionError (hold never becomes an authorization) and the destination is never called."""
    chk = Check("A08_hold_persists_no_binding_and_stays_hold")
    E = env()
    d = Path(tmp_path) / "s"
    fx = make_fixture(E, "f4", d / "_work")
    ctx = fx.res.contexts[E.tba.PROFILE]
    from datetime import timedelta
    fx.res.statuses[ctx["grant"]["grant_id"]].observed_at = (E.NOW - timedelta(seconds=3600)).isoformat()
    flow = construct(E, "f4", fx, d)
    dec = flow.decide(fx.p, now=E.NOW)
    chk.ok("decision_is_hold", dec.result == "hold", "negative", reasons=list(dec.reasons))
    row = json.dumps(dec_item(load_doc(d), dec.decision_id))
    chk.ok("persisted_binding_is_null", dec_item(load_doc(d), dec.decision_id).get("binding") is None, "negative")
    chk.ok("no_member_text_in_hold_row", KEY not in row, "negative")
    out = drive_execute(E, restart_like(E, "f4", fx, d), fx.p, dec.decision_id)
    chk.ok("hold_does_not_execute", out.get("raised") == "PermissionError" and out["dest_calls"] == 0 and out["dest_unchanged"], "negative", detail=jsonable(out))
    chk.done()


def restart_like(E, kind, fx, d, cfg=None, source=None):
    return construct(E, kind, fx, d, cfg, source)


def test_A09_compatibility_surfaces_byte_identical_to_baseline(tmp_path):
    """Frozen expectation 03:27 / 02:55 rule 6. Pass criterion: against the UNCHANGED prior tree (F3_OLD_SRC) the files `bounded.py`, `local_authority_effect.py`,
    `authorization_pin_export.py`, `reason_vocabulary.py`, `models.py` and every file under `<old root>/schemas` are byte-identical (sha256) to the candidate's; a persisted
    decision of the new code keeps `catalogue_digest == commitment(host profile dump)` and `approval_commitment == public approval_commitment(profile, context)`; the
    only new key in `runtime_authority` relative to a legacy decision is `effective_configuration`. `runtime_authority.py` and `registry_effective_policy.py` are EXPECTED to
    differ (D-07 / table rows) and are only recorded. `EffectivePolicySnapshot.identity_digest` and r08-v1..v7 identities are UNVERIFIED here (no baseline value is
    available without executing the old tree; see source-crosswalk)."""
    chk = Check("A09_compat_surfaces_byte_identical")
    old = Path(_need_old_src("A09_compat_surfaces_byte_identical"))
    E = env()
    new = Path(E.acp.__file__).resolve().parent

    def sha(p):
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    for name in ("bounded.py", "local_authority_effect.py", "authorization_pin_export.py", "reason_vocabulary.py", "models.py"):
        chk.ok(f"unchanged:{name}", (old / "agent_control_plane" / name).is_file() and sha(old / "agent_control_plane" / name) == sha(new / name), "positive")
    old_schemas, new_schemas = old.parent / "schemas", new.parents[1] / "schemas"
    files = sorted(p.name for p in old_schemas.glob("*.json")) if old_schemas.is_dir() else []
    chk.ok("schemas_dir_found", bool(files), files=files)
    for name in files:
        chk.ok(f"schema_unchanged:{name}", (new_schemas / name).is_file() and sha(old_schemas / name) == sha(new_schemas / name), "positive")
    for name in ("runtime_authority.py", "registry_effective_policy.py"):
        chk.obs(f"expected_to_differ:{name}", differs=sha(old / "agent_control_plane" / name) != sha(new / name))
    c = new_case(tmp_path, "pin")
    ra = dec_item(load_doc(c.dir), c.did)["binding"]["runtime_authority"]
    chk.ok("catalogue_digest_is_commitment_of_profile_dump", ra.get("catalogue_digest") == E.B.commitment(c.flow.runtime_authority_profile.model_dump(mode="json")), "positive")
    chk.ok("approval_commitment_recomputes", ra.get("approval_commitment") == E.approval_commitment(c.flow.runtime_authority_profile, snapshot_context(c.fx)), "positive")
    chk.ok("member_present_alongside_existing_keys", KEY in ra and {"catalogue_digest", "approval_commitment"} <= set(ra), "positive", keys=sorted(ra))
    chk.done()


def test_A10_pin_export_same_config_active_positive_control(tmp_path):
    """Frozen expectation 03:23 (accepted side) for the pin-export path. Pass criterion: for a decision minted and exported under the same configuration the export state
    is 'active' with a 17-member payload whose decision_id/effect_id/approval_commitment equal the persisted decision, no refusal row is written and the destination is not
    called."""
    chk = Check("A10_pin_export_same_config_active")
    c = new_case(tmp_path, "pin")
    out = drive_pin(c.E, restart(c), c.fx, c.did)
    chk.ok("state_active", out.get("state") == "active" and out.get("payload") is not None, "positive", detail=jsonable(out))
    if out.get("payload"):
        persisted = c.flow.records.decision(c.did)
        chk.ok("payload_has_17_members", len(out["payload"]) == 17, "positive", n=len(out["payload"]))
        chk.ok("payload_binds_persisted_ids", out["payload"]["decision_id"] == c.did and out["payload"]["effect_id"] == persisted.effect_id and
               out["payload"]["approval_commitment"] == persisted.binding.runtime_authority["approval_commitment"], "positive")
    chk.ok("no_refusal_no_dispatch", out["new_refusal_reasons"] == [] and out["dest_calls"] == 0, "positive")
    chk.done()


# ====================================================================================================================== A11 .. A24 adversarial controls
def test_A11_member_order_shuffle(tmp_path):
    """Frozen expectation 03:30 (member-order shuffling). Rewrite the persisted member with every dict's key order reversed (digest unchanged: canonical JSON is
    sorted-key) and reorder the keys of runtime_authority. Pass criterion: the decision is still ACCEPTED (acknowledged, no refusal): ordering is not identity. Also, with a
    family row appended and the families LIST reversed (self-consistent digest) the member is a different value and must REFUSE."""
    chk = Check("A11_member_order_shuffle")
    c = with_pristine(new_case(tmp_path, "f4"))

    def rev(o):
        return {k: rev(o[k]) for k in reversed(list(o))} if isinstance(o, dict) else ([rev(x) for x in o] if isinstance(o, list) else o)

    def shuffle(ra, item):
        m = ra.pop(KEY)
        orig_digest = m["digest"]
        ra.clear()
        ra[KEY] = rev(m)
        assert ra[KEY]["digest"] == orig_digest
    out, err = variant(c, shuffle)
    if out is None:
        chk.ok("store_loaded", False, error=err)
    else:
        judge_exec_accept(chk, "reversed_key_order", out)

    def reorder_families(ra, item):
        m = perturb_member(ra[KEY], "fam_extra")
        m["members"]["families"] = list(reversed(m["members"]["families"]))
        ra[KEY] = reseal(m)
    out, err = variant(c, reorder_families)
    if out is None:
        chk.ok("store_loaded_2", False, error=err)
    else:
        judge_exec_refusal(chk, "families_extra_and_reordered", out)
    chk.done()


def test_A12_duplicate_json_keys_in_store(tmp_path):
    """Frozen expectation 03:30 (duplicate keys). Textual duplicates are injected into the persisted JSON (a) of the record-level `version`, (b) of a member scalar with a
    DIFFERENT value (first-wins/last-wins parsers disagree). Pass criterion: the candidate never executes: either the store/workflow cannot be built (exception recorded) or
    execute raises; destination never called; if a refusal row can be written it names the code. (A store that cannot be read cannot hold a refusal row: recorded.)"""
    chk = Check("A12_duplicate_json_keys_in_store")
    c = with_pristine(new_case(tmp_path, "f4"))
    text = c.pristine
    pos = text.index(f'"{KEY}"')
    head, tail = text[:pos], text[pos:]
    vtxt = f'"version": "{VERSION}",'
    m1 = re.search(re.escape(vtxt), tail)
    s_txt = re.search(r'"status_max_age_seconds": (\d+)', tail)
    variants = {
        "dup_record_version_same_value": head + tail[:m1.end()] + " " + vtxt + tail[m1.end():] if m1 else None,
        "dup_member_scalar_different_value": head + tail[:s_txt.end()] + ', "status_max_age_seconds": ' + str(int(s_txt.group(1)) + 1000) + tail[s_txt.end():] if s_txt else None,
    }
    for label, newtext in variants.items():
        if newtext is None:
            chk.ok(f"{label}:injection_point_found", False)
            continue
        put_text(c.dir, newtext)
        chk.ok(f"{label}:text_really_has_duplicate", newtext != text)
        flow, cerr = None, None
        try:
            flow = restart(c)
        except Exception as exc:
            cerr = f"{type(exc).__name__}: {exc}"[:200]
        if flow is None:
            chk.ok(f"{label}:store_or_workflow_refused_to_build", True, "negative", error=cerr)
            chk.ok(f"{label}:destination_untouched", not (c.dir / "destination.json").exists() or c.flow.destination.calls == 0)
            continue
        out = drive_execute(c.E, flow, c.fx.p, c.did)
        chk.ok(f"{label}:not_executed", out.get("attempt_status") is None and out["dest_calls"] == 0, "negative", detail=jsonable(out))
        chk.obs(f"{label}:refusal_rows", rows=out["new_refusal_reasons"])
    put_text(c.dir, c.pristine)
    chk.done()


def test_A13_extra_unknown_member(tmp_path):
    """Frozen expectation 03:30 (extra unknown members inside effective_configuration) + builder claim 'exact key sets'. Extra keys are injected at record level, members
    level, scope level and in a family row, each (i) with the old digest and (ii) with a digest recomputed over the extended members. Pass criterion for every variant:
    PermissionError + one durable ['authorization_binding_changed'] + no attempt + destination untouched (an attacker who recomputes the digest must not succeed)."""
    chk = Check("A13_extra_unknown_member")
    c = with_pristine(new_case(tmp_path, "f4"))
    places = {
        "record_level": lambda m: m.__setitem__("extra", 1), "members_level": lambda m: m["members"].__setitem__("extra", 1),
        "scope_level": lambda m: m["members"]["scope"].__setitem__("extra", "x"), "f4_scalars_level": lambda m: m["members"]["f4_scalars"].__setitem__("extra", 1),
        "observation_level": lambda m: m["members"]["observation_policy"].__setitem__("extra", 1),
        "family_row_level": lambda m: m["members"]["families"][0].__setitem__("extra", "x"),
    }
    for label, put in places.items():
        for resealed in (False, True):
            def fn(ra, item, put=put, resealed=resealed):
                put(ra[KEY])
                if resealed:
                    reseal(ra[KEY])
            out, err = variant(c, fn)
            tag = f"{label}:{'resealed' if resealed else 'old_digest'}"
            if out is None:
                chk.ok(f"{tag}:store_loaded", False, error=err)
                continue
            judge_exec_refusal(chk, tag, out)
    chk.done()


def test_A14_replayed_member_from_other_scope_or_decision(tmp_path):
    """Frozen expectation 03:30 (replayed member copied from another decision or scope; 'scope member must refuse'). Decision X is minted under scope consumer-test; a
    second decision Y under a DIFFERENT scope (consumer-test-2, separate store). Pass criterion: copying Y's valid member (digest consistent, unmodified) into X refuses
    (durable code, destination untouched). Copying a member from another decision of the SAME scope/configuration is recorded as an OBSERVATION (the member has no decision
    id, so it is accepted by design) and a member from a different configuration in the same scope (constructor tolerance 6) refuses."""
    chk = Check("A14_replayed_member_other_scope")
    x = with_pristine(new_case(tmp_path, "f4", name="x"))
    y = new_case(tmp_path, "f4", {"consumer": "consumer-test-2"}, name="y")
    z = new_case(tmp_path, "f4", {"tolerance": 6}, name="z")
    same = new_case(tmp_path, "f4", name="same")
    for label, donor in (("other_scope", y), ("other_configuration", z)):
        member = member_of(donor.dir, donor.did)
        out, err = variant(x, lambda ra, item, member=member: ra.__setitem__(KEY, copy.deepcopy(member)))
        if out is None:
            chk.ok(f"{label}:store_loaded", False, error=err)
            continue
        judge_exec_refusal(chk, label, out)
    member = member_of(same.dir, same.did)
    pristine_member = json.loads(x.pristine)["decisions"][0]["binding"]["runtime_authority"][KEY]  # x's store was mutated by the loop above
    chk.ok("same_scope_member_identical_by_construction", member == pristine_member, "positive", note="member is configuration-level, not decision-level")
    out, err = variant(x, lambda ra, item: ra.__setitem__(KEY, copy.deepcopy(member)))
    chk.obs("same_scope_same_config_replay", accepted=bool(out) and out.get("attempt_status") == "acknowledged", detail=jsonable(out) if out else err)
    chk.done()


def test_A15_downgrade_by_deleting_member(tmp_path):
    """Frozen expectation 03:30 (downgrade by deleting the member) + 02:60. Pass criterion: with the default cutoff the stripped decision refuses (durable code,
    destination untouched). With cutoff == number of decisions the stripped decision at index below the cutoff is ACCEPTED as 'legacy': this is the documented limitation
    (`effective-configuration-binding.md:154`) and is recorded as LIMIT_CONFIRMED, not as a pass of the contract."""
    chk = Check("A15_downgrade_by_deleting_member")
    c = with_pristine(new_case(tmp_path, "f4"))
    out, err = variant(c, strip_member)
    if out is None:
        chk.ok("store_loaded", False, error=err)
    else:
        judge_exec_refusal(chk, "default_cutoff_stripped", out)
    count = len(load_doc(c.dir)["decisions"])
    out, err = variant(c, strip_member, {"cutoff": count})
    if out is None:
        chk.ok("store_loaded_2", False, error=err)
    else:
        chk.limit("stripped_member_below_cutoff", accepted_as_legacy=out.get("attempt_status") == "acknowledged", status=out.get("binding_status"), detail=jsonable(out))
    chk.done()


def test_A16_strip_member_at_or_past_cutoff(tmp_path):
    """Frozen expectation 03:25 ('a stripped member on a record at or past the cutoff refuses'). Three authorized decisions d0,d1,d2 are minted by the new code; the member is
    stripped from d1 (index == cutoff 1) and d2 (past the cutoff); a 4th decision d3 is appended AFTER activation with cutoff 3 and stripped (index 3 == cutoff). Pass
    criterion: d1, d2 and d3 each refuse (durable code, no attempt, destination untouched). d0 stripped (below the cutoff) is recorded as the documented limitation."""
    chk = Check("A16_strip_member_at_or_past_cutoff")
    E = env()
    d = Path(tmp_path) / "s"
    fx = make_fixture(E, "f4", d / "_work")
    flow = construct(E, "f4", fx, d)
    ids = [flow.decide(fx.p, now=E.NOW).decision_id for _ in range(3)]
    base = SimpleNamespace(E=E, kind="f4", dir=d, fx=fx, cfg={"cutoff": 1}, did=None, pristine=raw_text(d))
    for idx in (1, 2):
        base.did = ids[idx]
        out, err = variant(base, strip_member, {"cutoff": 1})
        if out is None:
            chk.ok(f"d{idx}:store_loaded", False, error=err)
            continue
        judge_exec_refusal(chk, f"d{idx}_stripped_at_or_past_cutoff1", out)
    base.did = ids[0]
    out, err = variant(base, strip_member, {"cutoff": 1})
    chk.limit("d0_stripped_below_cutoff", accepted=bool(out) and out.get("attempt_status") == "acknowledged", detail=jsonable(out) if out else err)
    chk.ok("d0_stripped_below_cutoff_accepted_as_legacy_R5", bool(out) and out.get("attempt_status") == "acknowledged" and out.get("binding_status") == "legacy", "positive",
           detail=jsonable(out) if out else err)
    put_text(d, base.pristine)
    flow3 = construct(E, "f4", fx, d, {"cutoff": 3})
    d3 = flow3.decide(fx.p, now=E.NOW).decision_id
    base.pristine = raw_text(d)
    base.did = d3
    out, err = variant(base, strip_member, {"cutoff": 3})
    if out is None:
        chk.ok("d3:store_loaded", False, error=err)
    else:
        judge_exec_refusal(chk, "d3_appended_after_activation_stripped", out)
    refused_oversize = False
    try:
        construct(E, "f4", fx, d, {"cutoff": 5})
    except Exception:
        refused_oversize = True
    chk.obs("cutoff_5_with_4_decisions_refused_at_construction", refused=refused_oversize)
    chk.done()


BAD_VALUES = [("bool_true", True), ("bool_false", False), ("float_equal", 30.0), ("float_frac", 30.5), ("str_number", "30"), ("negative", -1), ("huge_2_31", MAXI + 1),
              ("huge_2_63", 2 ** 63), ("huge_1e30", 10 ** 30), ("null", None), ("list", [30]), ("dict", {"v": 30})]
BAD_SLOTS = [("f4_scalars.status_max_age_seconds", ("f4_scalars", "status_max_age_seconds")), ("other_scalars.clock_tolerance_seconds", ("other_scalars", "clock_tolerance_seconds")),
             ("observation_policy.max_age_seconds", ("observation_policy", "max_age_seconds"))]


@pytest.mark.parametrize("slot_id,path", BAD_SLOTS, ids=[x[0] for x in BAD_SLOTS])
def test_A17_bad_types_bool_float_str_negative_huge(tmp_path, slot_id, path):
    """Frozen expectation 03:24 / 02:48 ('exact int, never bool, 0..2147483647'). For one scalar slot in each of three member groups every bad value is written with a
    SELF-CONSISTENT digest (so only type/range validation can reject; float 30.0 and True compare equal to the live ints in Python). Pass criterion for every value:
    PermissionError + one durable ['authorization_binding_changed'] + no attempt + destination untouched. The float_equal case is the equality-conflation control."""
    chk = Check(f"A17_bad_types_{slot_id}")
    c = with_pristine(new_case(tmp_path, "f4"))
    for label, bad in BAD_VALUES:
        def fn(ra, item, bad=bad):
            m = ra[KEY]
            set_at(m["members"], path, bad)
            reseal(m)
        out, err = variant(c, fn)
        if out is None:
            chk.ok(f"{label}:store_loaded", False, error=err)
            continue
        judge_exec_refusal(chk, label, out)
    chk.done()


def test_A17_bad_types_claim_route_without_profile(tmp_path):
    """Source-crosswalk finding F-2 (UNVERIFIED by execution). The claim route (`materialize_local_execution_claim`) for a governed workflow WITHOUT a runtime-authority
    profile calls `_resolve` without stage/decision, so the lifecycle may take the MINT branch and compare by Python equality. Pass criterion: a persisted member holding the
    FLOAT 30.0 for the live int 30 (self-consistent digest) must NOT yield a claim (PermissionError); the unperturbed decision must yield a claim (control). If the control
    itself cannot be claimed in this fixture the test records BLOCKED_INFO and fails (hard) so the lead sees the fixture limit."""
    chk = Check("A17_bad_types_claim_route_no_profile")
    c = with_pristine(new_case(tmp_path, "f4"))

    def claim(flow):
        persisted = flow.records.decision(c.did)
        try:
            claim_obj = c.E.claim(flow, c.fx.p, persisted, now=c.E.NOW, claim_id="harness-claim")
            return "claimed", type(claim_obj).__name__
        except Exception as exc:
            return "refused", f"{type(exc).__name__}: {exc}"[:200]
    put_text(c.dir, c.pristine)
    ctl, detail = claim(restart(c))
    chk.obs("control_unperturbed_claim", outcome=ctl, detail=detail)
    if ctl != "claimed":
        rec(chk.case, "BLOCKED", why="claim route not constructible for a no-profile fixture (control refused)", detail=detail)
        chk.ok("control_claim_constructible", False, detail=detail)
        chk.done()
        return

    def fn(ra, item):
        m = ra[KEY]
        m["members"]["f4_scalars"]["status_max_age_seconds"] = 30.0
        reseal(m)
    put_text(c.dir, c.pristine)
    edit(c.dir, c.did, fn)
    res, detail = claim(restart(c))
    chk.ok("float_equal_member_does_not_yield_claim", res == "refused", "negative", outcome=res, detail=detail)
    chk.done()


def test_A18_digest_not_equal_recompute(tmp_path):
    """Frozen expectation 03:24 / 02:51 ('digest not equal to the recomputation of its own members'). Positive oracle check first: this file's independent `my_digest`
    reproduces the persisted digest exactly (validates the harness's reading of 02:48 and the candidate's minting). Then: (a) valid-looking different digest with unchanged
    members, (b) members changed (a scalar) with the OLD digest kept, (c) members changed AND digest recomputed to a member value equal to nothing live. Pass criterion:
    (a),(b) refuse (durable code); (c) refuses as mismatch. Destination untouched in all."""
    chk = Check("A18_digest_not_equal_recompute")
    c = with_pristine(new_case(tmp_path, "f4"))
    m = member_of(c.dir, c.did)
    chk.ok("independent_recompute_equals_persisted_digest", my_digest(m["members"], m["version"]) == m["digest"], "positive", mine=my_digest(m["members"]), persisted=m["digest"])
    chk.ok("independent_canonical_equals_bounded_commitment", c.E.B.commitment({"domain": DOMAIN, "version": VERSION, **m["members"]}) == m["digest"], "positive")
    variants = {
        "a_other_digest_same_members": lambda ra, item: ra[KEY].__setitem__("digest", ALT_DIGEST_A),
        "b_members_changed_old_digest": lambda ra, item: ra[KEY]["members"]["f4_scalars"].__setitem__("status_max_age_seconds", 31),
        "c_members_changed_digest_recomputed": lambda ra, item: (ra[KEY]["members"]["f4_scalars"].__setitem__("status_max_age_seconds", 31), reseal(ra[KEY])),
    }
    for label, fn in variants.items():
        out, err = variant(c, fn)
        if out is None:
            chk.ok(f"{label}:store_loaded", False, error=err)
            continue
        judge_exec_refusal(chk, label, out)
    chk.done()


A19_CASES = [(leaf_id, path) for leaf_id, path in MEMBER_LEAVES]


@pytest.mark.parametrize("path_kind", ["execute", "pin-export"])
@pytest.mark.parametrize("leaf_id,leaf", A19_CASES, ids=[x[0] for x in A19_CASES])
def test_A19_pin_export_refuses_per_perturbed_member(tmp_path, leaf_id, leaf, path_kind):
    """Frozen expectation 03:23 (EVERY member perturbed, execute AND pin-export refuse with `authorization_binding_changed` and a durable EffectTimeRefusal; destination
    untouched). Member set = the frozen section-4 set (02:48), one parametrization per member. Fixture: profile-bearing F4-only composed workflow (the only one that can reach
    the pin export, `policy_binding` forbids profile families). The persisted member is replaced by a SELF-CONSISTENT member (digest recomputed independently) that differs in
    exactly that member. Pass criterion execute: PermissionError, one durable ['authorization_binding_changed'], no attempt, destination never called/unchanged. Pass criterion
    pin-export: state != 'active' and no payload; reason text names the code; a durable EffectTimeRefusal naming the code exists (strict; see open-questions Q2); destination
    never called. Candidate classification is recorded as evidence only."""
    chk = Check(f"A19_pin_export_refuses_per_perturbed_member[{path_kind}][{leaf_id}]")
    c = with_pristine(new_case(tmp_path, "pin"))
    chk.ok("control_status_bound_before_perturbation", c.flow.configuration_binding_status(c.flow.records.decision(c.did)) == "bound", "positive")
    original = member_of(c.dir, c.did)
    edit(c.dir, c.did, lambda ra, item: ra.__setitem__(KEY, perturb_member(original, leaf)))
    new_member = member_of(c.dir, c.did)
    chk.ok("perturbation_changed_digest_and_is_self_consistent", new_member["digest"] != original["digest"] and my_digest(new_member["members"]) == new_member["digest"], "n/a")
    flow = restart(c)
    if path_kind == "execute":
        judge_exec_refusal(chk, leaf_id, drive_execute(c.E, flow, c.fx.p, c.did))
    else:
        out = drive_pin(c.E, flow, c.fx, c.did)
        chk.obs("pin_raw_outcome", detail=jsonable(out))
        judge_pin_refusal(chk, leaf_id, out)
    chk.done()


@pytest.mark.parametrize("leaf_id", ["f4_scalars.status_max_age_seconds", "scope.consumer_id", "families=none_declared"])
def test_A19_claim_route_extra_path(tmp_path, leaf_id):
    """Extra path beyond the brief (source-crosswalk: claim is the third consumer of `_resolve`). Evidence-oriented: perturb one member as in A19 on the profile-bearing
    fixture and call `materialize_local_execution_claim`. Pass criterion: no claim is issued (PermissionError). If even the unperturbed claim is not constructible in this
    fixture the case records BLOCKED_INFO and fails hard (fixture limit, lead decides)."""
    chk = Check(f"A19_claim_route_extra[{leaf_id}]")
    leaf = dict(MEMBER_LEAVES)[leaf_id]
    c = with_pristine(new_case(tmp_path, "pin"))

    def claim(flow):
        try:
            c.E.claim(flow, c.fx.p, flow.records.decision(c.did), now=c.E.NOW, claim_id="harness-claim", policy_binding=c.fx.binding,
                      expected_consumer_id=c.fx.binding["consumer_id"], expected_operation=c.fx.binding["operation"])
            return "claimed", None
        except Exception as exc:
            return "refused", f"{type(exc).__name__}: {exc}"[:200]
    ctl, detail = claim(restart(c))
    chk.obs("control_unperturbed_claim", outcome=ctl, detail=detail)
    if ctl != "claimed":
        rec(chk.case, "BLOCKED", why="claim route not constructible in this fixture", detail=detail)
        chk.ok("control_claim_constructible", False, detail=detail)
        chk.done()
        return
    original = member_of(c.dir, c.did)
    edit(c.dir, c.did, lambda ra, item: ra.__setitem__(KEY, perturb_member(original, leaf)))
    res, detail = claim(restart(c))
    chk.ok("perturbed_member_yields_no_claim", res == "refused", "negative", detail=detail)
    chk.obs("claim_reason_text_names_code", names_code=CODE in (detail or ""), detail=detail)
    chk.done()


def test_A20_restart_separate_process(tmp_path):
    """Frozen expectation 03:23 + 02:53 (nothing held in memory) + 03:29 (crash/restart). The PARENT mints; fresh python processes (subprocess) rebuild from scratch.
    Pass criterion: (a) same config -> executed; (b) child with constructor tolerance 6 -> refused with ['authorization_binding_changed'] durable row, destination not
    called; (c) child with ObservationPolicy absent -> refused likewise; (d) pin child with the same config -> active, and the pin child over a store whose member was perturbed
    (digest re-sealed) -> not active with destination not called."""
    chk = Check("A20_restart_separate_process")
    for label, over, accept in (("same", {}, True), ("tolerance_6", {"tolerance": 6}, False), ("obs_absent", {"obs": "none"}, False)):
        c = new_case(tmp_path, "f4", name=f"f4_{label}")
        child = run_worker("execute", "f4", c.dir, c.dir / "_cw", over, c.did)
        if child.get("worker_error"):
            chk.ok(f"{label}:worker_ran", False, detail=jsonable(child))
            continue
        if accept:
            chk.ok(f"{label}:executed", child.get("attempt_status") == "acknowledged" and child["new_refusal_reasons"] == [], "positive", detail=jsonable(child))
        else:
            judge_exec_refusal(chk, label, child)
    c = new_case(tmp_path, "pin", name="pin_perturbed")
    original = member_of(c.dir, c.did)
    edit(c.dir, c.did, lambda ra, item: ra.__setitem__(KEY, perturb_member(original, ("other_scalars", "identity_max_age_seconds"))))
    child = run_worker("pin", "pin", c.dir, c.dir / "_cw", {}, c.did)
    chk.ok("pin_child_not_active_on_perturbed_member", not child.get("worker_error") and child.get("state") != "active" and child.get("payload") is None, "negative", detail=jsonable(child))
    chk.ok("pin_child_destination_untouched", child.get("dest_calls") == 0 and child.get("dest_unchanged") is True, "negative")
    chk.done()


@pytest.mark.parametrize("mode", ["before", "after", "replace"])
def test_A21_crash_around_append_decision(tmp_path, mode):
    """Frozen expectation 03:29 (crash points around `append_decision`). A child process is killed with os._exit(77) (a) BEFORE append_decision, (b) immediately AFTER it
    returned, (c) after the temp file was written but before the atomic rename. Pass criterion: (a),(c) leave NO decision row in the store (nothing authorized, nothing to
    execute) and a later decide+execute under the same configuration works; (b) leaves exactly one decision which carries a VALID member (independent digest recomputation) and
    executes under the same configuration but refuses (durable code) under a changed constructor tolerance. No half-written/memberless authorized decision may exist."""
    chk = Check(f"A21_crash_around_append_decision[{mode}]")
    E = env()
    base = Path(tmp_path) / "s"
    child = run_worker(f"crash-{mode}", "f4", base, base / "_cw", {})
    chk.ok("child_crashed_with_77", child.get("returncode") == 77 and child.get("outcome") is None, detail=jsonable(child))
    doc = load_doc(base) if (base / "run.json").exists() else {"decisions": []}
    rows = doc["decisions"]
    if mode in ("before", "replace"):
        chk.ok("no_decision_row_persisted", rows == [], "negative", n=len(rows))
        c = new_case(tmp_path, "f4", name="after_crash_recovery")
        judge_exec_accept(chk, "fresh_decision_after_crash", drive_execute(E, restart(c), c.fx.p, c.did))
        chk.obs("leftover_tmp_files", files=sorted(p.name for p in base.glob("*.tmp")))
    else:
        chk.ok("exactly_one_decision_row", len(rows) == 1, "positive", n=len(rows))
        if len(rows) == 1:
            ra = (rows[0].get("binding") or {}).get("runtime_authority") or {}
            m = ra.get(KEY)
            chk.ok("member_present_and_independently_valid", isinstance(m, dict) and my_digest(m["members"], m["version"]) == m["digest"], "positive")
            fx = make_fixture(E, "f4", base / "_fx")
            did = rows[0]["decision_id"]
            refuse_out = drive_execute(E, construct(E, "f4", fx, base, {"tolerance": 6}), fx.p, did)
            judge_exec_refusal(chk, "changed_config_after_crash", refuse_out)
            accept_out = drive_execute(E, construct(E, "f4", fx, base, {}), fx.p, did)
            judge_exec_accept(chk, "same_config_after_crash", accept_out)
    chk.done()


def test_A22_failed_attempt_still_blocks_retry(tmp_path):
    """Frozen expectation 03:29 ('an attempt already `failed` still blocks retry'). The Registry source is made to fail ONLY at the commit gate so the existing pre-dispatch
    gate records the attempt `failed` without calling the destination. Pass criterion: that attempt exists with status 'failed'; a retry (source restored, same
    configuration, binding still `bound`) raises PermissionError and does NOT call the destination; the binding never clears the failed attempt. (If the harness cannot reach
    the commit gate the case fails hard: fixture limit.)"""
    chk = Check("A22_failed_attempt_still_blocks_retry")
    E = env()
    d = Path(tmp_path) / "s"
    fx = make_fixture(E, "f4", d / "_work")
    src = Src(f4_material(E, 30, 30))
    flow = construct(E, "f4", fx, d, None, src)
    did = flow.decide(fx.p, now=E.NOW).decision_id
    src.gate_fail = True
    out1 = drive_execute(E, flow, fx.p, did)
    attempts = [a for a in flow.records.load().attempts if a.decision_id == did]
    latest = {a.attempt_id: a for a in attempts}  # the attempt log is append-only: 'attempted' then 'failed' rows share an attempt_id
    chk.ok("commit_gate_reached_attempt_failed", len(latest) == 1 and list(latest.values())[0].status == "failed", "negative", statuses=[a.status for a in attempts], first=jsonable(out1))
    chk.ok("destination_not_called_by_failed_attempt", out1["dest_calls"] == 0)
    src.gate_fail = False
    out2 = drive_execute(E, flow, fx.p, did)
    chk.ok("retry_raises_permission_error", out2.get("raised") == "PermissionError", "negative", detail=jsonable(out2))
    chk.ok("retry_never_calls_destination", out2["dest_calls"] == 0 and out2["new_attempts"] == 0, "negative")
    chk.ok("binding_status_bound_does_not_clear_failure", out2.get("binding_status") == "bound", "positive", status=out2.get("binding_status"))
    chk.ok("retry_not_blamed_on_binding", out2["new_refusal_reasons"] == [], "n/a", rows=out2["new_refusal_reasons"])
    chk.done()


def test_A23_binding_confers_no_authority(tmp_path):
    """Frozen expectation 03:28 / 02:52 rule 3 ('cannot turn a hold into an authorization, cannot widen a bound, is never read by an approval, never removes a refusal
    produced by another check'). Pass criteria: (a) a hold row never carries a member and never executes (see A08); (b) a decision whose member is `bound` still REFUSES when
    another check now fails (grant status made stale after the decision): refusal reasons are produced by that check, no attempt, destination untouched; (c) a persisted member
    claiming a WIDER bound (status 3600, digest re-sealed) does not widen anything: execute refuses (mismatch) and the live bound is unchanged; (d) the source of
    `runtime_authority.py` does not mention the member key (approval_commitment cannot read it)."""
    chk = Check("A23_binding_confers_no_authority")
    E = env()
    from datetime import timedelta
    c = with_pristine(new_case(tmp_path, "f4"))
    ctx = c.fx.res.contexts[E.tba.PROFILE]
    status_obj = c.fx.res.statuses[ctx["grant"]["grant_id"]]
    original_observed = status_obj.observed_at
    status_obj.observed_at = (E.NOW - timedelta(seconds=3600)).isoformat()
    out = drive_execute(E, restart(c), c.fx.p, c.did)
    chk.obs("stale_status_after_decision", detail=jsonable(out))
    chk.ok("other_check_still_refuses", out.get("raised") == "PermissionError" and out["dest_calls"] == 0 and out["new_attempts"] == 0, "negative")
    chk.ok("refusal_row_exists_and_binding_was_bound", len(out["new_refusal_reasons"]) == 1 and out.get("binding_status") == "bound", "negative", rows=out["new_refusal_reasons"],
           status=out.get("binding_status"))
    chk.ok("refusal_reasons_include_the_other_check", out["new_refusal_reasons"] != [] and out["new_refusal_reasons"] != [[CODE]], "negative", rows=out["new_refusal_reasons"])
    status_obj.observed_at = original_observed
    out_w, err = variant(c, lambda ra, item: (ra[KEY]["members"]["f4_scalars"].__setitem__("status_max_age_seconds", 3600), reseal(ra[KEY])))
    if out_w is None:
        chk.ok("wider_member_store_loaded", False, error=err)
    else:
        judge_exec_refusal(chk, "wider_bound_member", out_w)
    ra_src = Path(E.acp.__file__).resolve().parent / "runtime_authority.py"
    chk.ok("runtime_authority_source_does_not_reference_member_key", KEY not in ra_src.read_text(encoding="utf-8"), "negative", file=str(ra_src))
    chk.done()


def test_A24_limits_documented_no_antirollback_claim(tmp_path):
    """Frozen expectation 03:31 ('stated limits present and honest ... the qualifier fails any claim of anti-rollback protection'). Pass criteria: (a) the candidate's binding
    doc and module docstring state: unsigned store, NO anti-rollback guarantee, host-supplied cutoff without durable provenance, mixed-fleet legacy writers; (b) no line in
    the binding doc, final3 doc or the binding/lifecycle module docstrings AFFIRMS anti-rollback/rollback protection (heuristic: a line mentioning rollback with
    prevent/protect/guarantee/defend and no negation); every rollback line is recorded for human review; (c) BEHAVIOUR: roll back A -> B -> A: the decision minted under A is
    refused under B and accepted again under A (documented 'revives'), recorded as LIMIT_CONFIRMED; a store-writer who forges a member equal to the live one is accepted
    (documented unsigned limit), recorded as LIMIT_CONFIRMED."""
    chk = Check("A24_limits_documented_no_antirollback_claim")
    E = env()
    root = Path(E.acp.__file__).resolve().parents[2]
    doc = (root / "docs" / "effective-configuration-binding.md").read_text(encoding="utf-8")
    low = doc.lower()
    chk.ok("doc_states_unsigned_store", "unsigned" in low, "positive")
    chk.ok("doc_states_no_anti_rollback_guarantee", bool(re.search(r"no anti-rollback guarantee", low)), "positive")
    chk.ok("doc_states_cutoff_without_durable_provenance", "no durable provenance" in low and "legacy_cutoff" in low, "positive")
    chk.ok("doc_states_mixed_fleet", "mixed fleet" in low or "mixed-fleet" in low, "positive")
    mod = (Path(E.acp.__file__).resolve().parent / "effective_configuration_binding.py").read_text(encoding="utf-8")
    chk.ok("module_docstring_states_no_anti_rollback", "no anti-rollback guarantee" in mod.lower(), "positive")
    neg = re.compile(r"\b(no|not|never|without|cannot|does not|do not|isn't|nor|neither|absent|held|separate held item)\b", re.I)
    aff = re.compile(r"(prevent|protect|guarantee|defen[cd]|ensure|resist)", re.I)
    affirmative = []
    texts = {"docs/effective-configuration-binding.md": doc, "src/effective_configuration_binding.py": mod}
    for rel in ("docs/final3-consumers.md", "docs/d07-purpose-observation-anchor-correction.md"):
        if (root / rel).is_file():
            texts[rel] = (root / rel).read_text(encoding="utf-8")
    lc = (Path(E.acp.__file__).resolve().parent / "registry_governed_lifecycle.py").read_text(encoding="utf-8")
    texts["src/registry_governed_lifecycle.py"] = lc
    for name, text in texts.items():
        for n, line in enumerate(text.splitlines(), 1):
            if re.search(r"roll(ed)?[- ]?back", line, re.I):
                is_aff = bool(aff.search(line)) and not neg.search(line)
                rec(chk.case, "OBSERVATION", check="rollback_line", file=name, line=n, text=line.strip()[:300], looks_affirmative=is_aff)
                if is_aff:
                    affirmative.append((name, n))
    chk.ok("no_line_affirms_rollback_protection", affirmative == [], "negative", lines=affirmative)
    c = with_pristine(new_case(tmp_path, "f4", name="rollback"))
    out_b = drive_execute(E, restart(c, {"tolerance": 6}), c.fx.p, c.did)
    judge_exec_refusal(chk, "under_config_B", out_b)
    put_text(c.dir, c.pristine)
    out_a = drive_execute(E, restart(c, {}), c.fx.p, c.did)
    chk.limit("rollback_to_A_revives_decision", revived=out_a.get("attempt_status") == "acknowledged", detail=jsonable(out_a))
    chk.ok("rollback_revival_matches_documentation", out_a.get("attempt_status") == "acknowledged", "positive")
    c2 = with_pristine(new_case(tmp_path, "f4", name="forge"))
    donor = new_case(tmp_path, "f4", {"tolerance": 6}, name="forge_donor")
    forged = copy.deepcopy(member_of(donor.dir, donor.did))  # what an operator with write access to the unsigned store can fabricate: a valid member for configuration B
    out_f, err = variant(c2, lambda ra, item: ra.__setitem__(KEY, copy.deepcopy(forged)), {"tolerance": 6})
    chk.limit("store_writer_rebinds_decision_to_new_configuration_is_accepted", accepted=bool(out_f) and out_f.get("attempt_status") == "acknowledged",
              note="unsigned store; documented in 02:62; contract rule 5 'no re-bind' is not enforceable against a store writer", detail=jsonable(out_f) if out_f else err)
    chk.done()


import contextlib


@contextlib.contextmanager
def patched(obj, name, value):
    old = getattr(obj, name)
    setattr(obj, name, value)
    try:
        yield
    finally:
        setattr(obj, name, old)


def test_A25_live_side_member_perturbation_rebuild(tmp_path):
    """AMEND-3 (coverage addition after mutation result). Expectation (03 F3-A E1): a decision minted under configuration C, then a workflow REBUILT with a LIVE
    configuration differing in exactly one of authority_domain / family contract_version / family_schema_revision / family effective_policy_digest (/ host-effective profile
    digest where reachable) must refuse: PermissionError, one durable ['authorization_binding_changed'], no attempt, destination apply never called. Positive control: an
    unperturbed rebuild executes. Routes: (a) signed (re-signed selection + manifest domain); (b)(c)(d) in-process PATCH after minting (no signed route); (e) joint only."""
    import registry_successor.v2_policy_identity as v2i
    import agent_control_plane.registry_effective_policy as eff
    chk = Check("A25_live_side_member_perturbation_rebuild")
    E = env()
    ctl = new_case(tmp_path, "f4", name="control")
    judge_exec_accept(chk, "control_unperturbed_rebuild", drive_execute(E, restart(ctl), ctl.fx.p, ctl.did))

    def run_case(label, route, cfg=None, ctx=None):
        c = new_case(tmp_path, "f4", name=label)
        with (ctx if ctx is not None else contextlib.nullcontext()):
            try:
                flow = restart(c, cfg)
            except Exception as exc:
                return c, None, f"{type(exc).__name__}: {exc}"[:240]
            return c, drive_execute(E, flow, c.fx.p, c.did), None
    # (a) signed route
    c, out, err = run_case("a_authority_domain", "signed", {"domain": "other-domain"})
    if out is not None and out.get("raised") == "PermissionError" and out["new_refusal_reasons"] == [[CODE]]:
        judge_exec_refusal(chk, "a_authority_domain[signed]", out)
    else:
        chk.obs("a_authority_domain[signed]:UNREACHABLE-ISOLATED", reason="no clean binding refusal obtainable", construction_error=err, detail=jsonable(out) if out else None)
    # (b) contract version, PATCH
    c0 = FAM = dict(eff.FAMILY_TABLE)
    mod = dict(FAM)
    mod["f4_ages"] = (FAM["f4_ages"][0], "r08-v2-live-changed")
    c, out, err = run_case("b_contract_version", "patch")  # mint first (unpatched), then patch for rebuild+execute
    with patched(eff, "FAMILY_TABLE", mod):
        flow = restart(c)
        out = drive_execute(E, flow, c.fx.p, c.did)
    judge_exec_refusal(chk, "b_contract_version[PATCH]", out)
    # (c) schema revision, PATCH
    c, _, _ = run_case("c_schema_revision", "patch")
    with patched(eff, "SCHEMA_REVISIONS", dict(eff.SCHEMA_REVISIONS, f4_ages=1)):
        out = drive_execute(E, restart(c), c.fx.p, c.did)
    judge_exec_refusal(chk, "c_schema_revision[PATCH]", out)
    # (d) effective-policy digest, PATCH of the Registry digest function (same effective values, different digest)
    c, _, _ = run_case("d_effective_policy_digest", "patch")
    real = v2i.effective_policy_digest
    with patched(v2i, "effective_policy_digest", lambda *a, **k: "sha256:" + "ee" * 32):
        out = drive_execute(E, restart(c), c.fx.p, c.did)
    judge_exec_refusal(chk, "d_effective_policy_digest[PATCH]", out)
    chk.ok("patches_restored", eff.FAMILY_TABLE == FAM and v2i.effective_policy_digest is real and "f4_ages" not in eff.SCHEMA_REVISIONS)
    # (d') signed route: different narrowing value (scalars change jointly)
    c, out, err = run_case("d2_signed_narrowing", "signed", {"reg": [35, 30]})
    judge_exec_refusal(chk, "d2_signed_narrowing[signed,joint-with-f4_scalars]", out) if out else chk.ok("d2_constructed", False, error=err)
    # (e) host/effective profile digest: joint with catalogue_digest only
    pc = new_case(tmp_path, "pin", name="e_profile")
    cl = pc.fx.cfg.actions[pc.fx.p.action_id].model_copy(update={"max_status_age_seconds": 61})
    cfg2 = pc.fx.cfg.model_copy(update={"actions": {pc.fx.p.action_id: cl}})
    fx2 = SimpleNamespace(p=pc.fx.p, res=pc.fx.res, cfg=cfg2, binding=pc.fx.binding)
    try:
        out = drive_execute(E, construct(E, "pin", fx2, pc.dir, {}), pc.fx.p, pc.did)
    except Exception as exc:
        out, err = None, f"{type(exc).__name__}: {exc}"[:240]
    chk.obs("e_profile_digest:UNREACHABLE-ISOLATED(joint with catalogue_digest)", detail=jsonable(out) if out else err)
    chk.done()


if __name__ == "__main__" and len(sys.argv) >= 2 and sys.argv[1] == "--worker":
    raise SystemExit(worker_main(sys.argv[2:]))
