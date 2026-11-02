"""Shared harness of the RW-01-F4-PoC end-to-end battery (qualification-side test code; BUILDER_TESTED developer evidence, NOT independent qualification).

What this wires together, with the REAL components at the pinned SHAs of ../sources.json:
  * Registry (PR #86 head): real Ed25519 (PyNaCl) signing of SYNTHETIC selections (mechanism tests only; no trust root, no real key custody), the real
    `Ed25519Verifier`, and the real enforcing-consumer adapter `registry_consumer.evidence_verifier.RegistryEvidenceVerifierV2`;
  * Control Plane (PR #102 head): the real `GovernedAgeWorkflow(..., carry_selection_evidence=True)` producing a real authorized decision whose `selection_evidence`
    carries the exact signed bytes;
  * Replay (PR #84 head): the real `import_bounded_workflow` under the `registry-authenticated-selection/0.1` profile with operator-supplied independent trust inputs.

KNOWN INTEGRATION GAP (finding F-1, pinned by test_e2e_f1_*): a real `GovernedAgeWorkflow` run record is refused by EVERY Replay profile at structural validation
("resolution journal missing"), because Replay's current-generation validator requires a `check_events` journal and a `runtime-authority/0.1` binding that the F4 workflow
(which by contract refuses a `runtime_authority_profile`) never writes. The battery therefore also uses a clearly labelled BRIDGED record (`bridge()`): the REAL F4
`effective_configuration` record and the REAL carried `selection_evidence` of the real F4 decision, grafted verbatim onto the structurally valid current-generation run record
that Replay's own test fixture captured from a runtime-authority workflow. Every row says which of the two it used.

Signing helpers (`sign`, `record`, `trust`) follow tests/test_f4_age_governance.py of the Control Plane and tests/test_rw01_f4_verified_selection.py of the Registry.
"""
from __future__ import annotations

import base64
import copy
import dataclasses
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
POC = HERE.parent
SOURCES = json.loads((POC / "sources.json").read_text())["sources"]
SRC_DIR = Path(os.environ.get("RW01_SRC_DIR", "/dev/shm/rw01-src")).resolve()


def src(name: str) -> Path:
    return SRC_DIR / SOURCES[name]["dir"]


def git(name: str, *args: str) -> str:
    return subprocess.run(["git", "--no-replace-objects", "-C", str(src(name)), *args], capture_output=True, text=True, check=True).stdout.strip()


def bootstrap_paths() -> None:
    """Front of sys.path: CP root (its regular `tests` package), CP src, Replay src, Registry root + vendored engine baseline + Registry tests (flat helper modules)."""
    for entry in reversed([src("control_plane"), src("control_plane") / "src", src("replay") / "src", src("registry"),
                           src("registry") / "baseline" / "execution-runtime", src("registry") / "tests"]):
        if str(entry) not in sys.path:
            sys.path.insert(0, str(entry))


bootstrap_paths()

import nacl.bindings as nb  # noqa: E402
import pytest  # noqa: E402
import r08_support as r  # noqa: E402  (Registry test builders, reused)
import s01_support as s  # noqa: E402
from registry_adapters import ed25519_verifier as ev  # noqa: E402
from registry_consumer.evidence_verifier import RegistryEvidenceVerifierV2  # noqa: E402
from registry_successor import common as c  # noqa: E402
from registry_successor import v2_age_bounds as f4  # noqa: E402
from registry_successor import v2_policy_identity as pid  # noqa: E402
from registry_successor import v2_verified_selection as vs  # noqa: E402
from registry_successor import verify as v  # noqa: E402

import agent_control_plane.bounded as cp_bounded  # noqa: E402
import agent_control_plane.registry_f4_age_governance as cp_f4  # noqa: E402
from agent_control_plane.bounded import BoundedRecordStore, LocalRefundDestination, ObservationPolicy  # noqa: E402
from agent_control_plane.registry_f4_age_governance import GovernedAgeWorkflow, GovernedScope, SelectionMaterial  # noqa: E402
from tests.test_bounded_authorization import NOW, manifest, tenant_proposal, tenant_resolver_for, TENANT  # noqa: E402  (Control Plane test builders, reused)

from agent_replay_bundle import effective_configuration as EC  # noqa: E402
from agent_replay_bundle import importers as I  # noqa: E402
from agent_replay_bundle import registry_evidence as RE  # noqa: E402
from agent_replay_bundle.registry_evidence import (RegistryEvidenceTrust, RegistryExpectedContext, RegistryTrustSnapshotRef,  # noqa: E402
                                                   REGISTRY_AUTHENTICATED_SELECTION_PROFILE as SELECTOR)

ImportContractError = I.ImportContractError
CUR_CP = I.CONTROL_PLANE_CUR_REVISION
OLD_SELECTOR = EC.REGISTRY_GOVERNED_PROFILE
F4 = f4.FAMILY_F4
PK, SK = nb.crypto_sign_seed_keypair(bytes(range(32)))              # SYNTHETIC seed: mechanism test only
OTHER_PK, OTHER_SK = nb.crypto_sign_seed_keypair(bytes(range(1, 33)))  # SYNTHETIC seed: mechanism test only
KEY_ID, OTHER_KEY_ID = s.KEY_ID, "key-test-2"
CONSUMER = "consumer-test"
_action = manifest()["actions"][0]
ACTION_ID = _action["action_id"]
INSTITUTION = _action["authority_context"]["institution_id"]
DOMAIN = _action["authority_context"]["authority_domain"]
TENANT_ID = TENANT.lower()
OPERATION = "refund-issue-routine"
SCOPE = GovernedScope(CONSUMER, TENANT_ID, ACTION_ID, OPERATION)
STMT_SCOPE = {"tenant": TENANT_ID, "institution": INSTITUTION, "authority_domain": DOMAIN}
EFFECTIVE = {"valid_from": "2026-10-01T00:00:00Z", "valid_until": "2026-10-06T00:00:00Z"}
ISSUED = "2026-10-01T00:00:00Z"
HOST_AGES = {"status_max_age_seconds": 60, "approval_max_age_seconds": 60}   # the Control Plane host default AND the operator's independent expectation
BOUND = (120, 90)                                                         # the signed Registry bound: effective = per-scalar min(host, bound) = (60, 60)
REPLAY_FIXTURE = src("replay") / "tests" / "fixtures" / "registry_governed_effective_configuration" / "governed_executed"
CP_PR_HEAD = SOURCES["control_plane"]["sha"]
REGISTRY_PR_HEAD = SOURCES["registry"]["sha"]
VERIFY_T = NOW                                                            # the operator's explicit verification time (== the decision time of the synthetic CP clock)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ------------------------------------------------------------------------------------------------------------------------------ Registry side (synthetic)
def sign(stmt, sk=None, domain=None):
    return base64.b64encode(nb.crypto_sign((domain or s.V2_DOMAIN) + c.canonical_bytes(stmt), sk or SK)[:64]).decode("ascii")


def record(status=BOUND[0], approval=BOUND[1], **over):
    body = dict(r.make_record(), contract_version="r08-v2", family=F4, record_id="f4-age-record",
                payload={"status_max_age_seconds": status, "approval_max_age_seconds": approval})
    body.update(over)
    return r.seal_record(body)


def grant(**over):
    kw = dict(consumer=CONSUMER, tenant=TENANT_ID, institution=INSTITUTION, domain=DOMAIN, operation=OPERATION)
    kw.update(over)
    return v.AuthorityGrant(kw["consumer"], kw["tenant"], kw["institution"], kw["domain"], kw["operation"])


def trust(*, version=1, valid_until="2026-10-07T00:00:00Z", issuers=None, **kw):
    """A Registry TrustSnapshot (synthetic). Default: one issuer (KEY_ID/PK) authorised for exactly the derived scope."""
    issuers = issuers if issuers is not None else (v.IssuerEntry(KEY_ID, "issuer-test-1", "ed25519", PK, (grant(),)),)
    return v.TrustSnapshot("snap-test-1", version, valid_until, tuple(issuers), **kw)


def statement(rec, **over):
    kw = dict(family=rec.get("family", F4), consumer_id=CONSUMER, scope=dict(STMT_SCOPE), operation=OPERATION, effective=dict(EFFECTIVE), issued_at=ISSUED)
    kw.update(over)
    return r.make_statement_v2(rec, **kw)


def envelope_text(stmt, *, sk=None, key_id=KEY_ID, pub=PK, signature=None, ensure_ascii=True):
    env = s.envelope(stmt, signature=signature if signature is not None else sign(stmt, sk), pub=pub, key_id=key_id)
    return json.dumps(env, sort_keys=True, ensure_ascii=ensure_ascii)


@dataclasses.dataclass
class Material:
    record_text: str
    selection_text: str
    host_trust: object
    rec: dict
    stmt: dict

    def selection_material(self) -> SelectionMaterial:
        return SelectionMaterial(self.record_text, self.selection_text, self.host_trust)


def material(status=BOUND[0], approval=BOUND[1], *, rec=None, host_trust=None, sk=None, key_id=KEY_ID, pub=PK, stmt_over=None, ensure_ascii=True, signature=None, record_text=None):
    rec = rec if rec is not None else record(status, approval)
    stmt = statement(rec, **(stmt_over or {}))
    return Material(record_text if record_text is not None else r.dumps(rec), envelope_text(stmt, sk=sk, key_id=key_id, pub=pub, ensure_ascii=ensure_ascii, signature=signature),
                    host_trust if host_trust is not None else trust(), rec, stmt)


def withdrawal_text(base: Material) -> str:
    wd = s.withdraw_statement(base.stmt)
    return envelope_text(wd)


# ------------------------------------------------------------------------------------------------------------------------------ Control Plane side (real)
@dataclasses.dataclass
class Produced:
    run: dict            # raw run.json of the real Control Plane store
    proposal: dict
    decision: object
    material: Material
    flow: object
    tmp: Path


class Source:
    def __init__(self, mat):
        self.mat, self.calls = mat, 0

    def __call__(self):
        self.calls += 1
        return self.mat.selection_material() if isinstance(self.mat, Material) else self.mat


def build_flow(tmp: Path, mat, *, carry=None, host=None, tenant=None, **kw):
    p = tenant_proposal(tenant) if tenant else tenant_proposal()
    kw.setdefault("resolver", tenant_resolver_for(p, tenant_id=tenant) if tenant else tenant_resolver_for(p))
    if tenant:
        kw.setdefault("scope", GovernedScope(CONSUMER, tenant, ACTION_ID, OPERATION))
    if carry is not None:
        kw["carry_selection_evidence"] = carry
    if host:
        kw.update(host)
    return GovernedAgeWorkflow(scope=kw.pop("scope", SCOPE), selection_source=Source(mat), verifier=kw.pop("verifier", ev.Ed25519Verifier()), allow_test_time=True,
                               construction_time=NOW, manifest=manifest(), destination=LocalRefundDestination(tmp / "destination.json"),
                               records=BoundedRecordStore(tmp / "run.json", "run-1"), observation_policy=ObservationPolicy(max_age_seconds=300, clock_tolerance_seconds=5), **kw)


def produce(tmp: Path, mat: Material, *, carry=True, execute=True, host=None, tenant=None) -> Produced:
    """Real Control Plane F4 workflow: construct (Registry verifies), decide (authorized), optionally execute. Returns the raw store."""
    p = tenant_proposal(tenant) if tenant else tenant_proposal()
    flow = build_flow(tmp, mat, carry=carry, host=host, tenant=tenant)
    d = flow.decide(p, now=NOW)
    assert d.result == "authorized", d.reasons
    if execute:
        flow.execute(p, flow.records.decision(d.decision_id), adapter_id=p.adapter_id, now=NOW)
    return Produced(json.loads((tmp / "run.json").read_text()), json.loads(p.model_dump_json()), d, mat, flow, tmp)


def real_decision(pr: Produced) -> dict:
    return pr.run["decisions"][0]


# ------------------------------------------------------------------------------------------------------------------------------ the BRIDGED record (see module docstring)
def fixture_record():
    cp = json.loads((REPLAY_FIXTURE / "control_plane_run.json").read_text())
    return cp, json.loads((REPLAY_FIXTURE / "proposal.json").read_text())


def bridge(pr: Produced, *, evidence=True):
    """Replay-valid current-generation run record whose effective_configuration and selection_evidence are the REAL ones of the real F4 decision (verbatim)."""
    cp, proposal = fixture_record()
    real = real_decision(pr)
    tenant = real["binding"]["tenant_id"]       # identical to the fixture's unless the row uses another tenant (N19); then both fixture fields follow the REAL decision
    cp["decisions"][0]["binding"]["tenant_id"] = tenant
    proposal["tenant_id"] = tenant
    cp["decisions"][0]["binding"]["runtime_authority"]["effective_configuration"] = copy.deepcopy(real["binding"]["runtime_authority"]["effective_configuration"])
    cp["decisions"][0].pop("selection_evidence", None)
    if evidence:
        assert "selection_evidence" in real, "the real Control Plane decision carries no selection_evidence"
        cp["decisions"][0]["selection_evidence"] = copy.deepcopy(real["selection_evidence"])
    return cp, proposal


def reseal(cp, mutate):
    """Mutate effective_configuration members and recompute Replay's own digest so the structural check cannot be the thing that refuses."""
    cp = copy.deepcopy(cp)
    ec = cp["decisions"][0]["binding"]["runtime_authority"]["effective_configuration"]
    mutate(ec["members"])
    ec["digest"] = EC.digest_of(ec["version"], ec["members"])
    return cp


def row(cp):
    return next(x for x in cp["decisions"][0]["binding"]["runtime_authority"]["effective_configuration"]["members"]["families"] if x["slot"] == "f4_ages")


# ------------------------------------------------------------------------------------------------------------------------------ Replay side (operator trust)
class Spy:
    """Observation wrapper around a verifier: records each request and verdict, delegates unchanged. It is NOT a stub: it forwards to the object it wraps.
    Replay cannot tell it from the wrapped adapter (known non-detection NF-2)."""

    def __init__(self, inner=None, mutate=None):
        if inner is None:
            ad = ev.Ed25519Verifier()
            inner = RegistryEvidenceVerifierV2(ad, ad.key_admission)
        self.inner, self.mutate = inner, mutate
        self.requests: list = []
        self.verdicts: list = []

    @property
    def calls(self) -> int:
        return len(self.requests)

    def verify_selection_evidence(self, request):
        self.requests.append(request)
        verdict = self.inner.verify_selection_evidence(request)
        if self.mutate is not None:
            verdict = self.mutate(copy.deepcopy(verdict), request)
        self.verdicts.append(verdict)
        return verdict

    @property
    def last(self):
        return self.verdicts[-1]


def make_trust(*, verifier=None, snapshot=None, **over):
    kw = dict(verifier=verifier if verifier is not None else Spy(), trust_snapshot=snapshot if snapshot is not None else trust(),
              trust_snapshot_ref=RegistryTrustSnapshotRef(snapshot_id="snap-test-1", version=1),
              expected_context=RegistryExpectedContext(consumer_id=CONSUMER, tenant=TENANT_ID, institution=INSTITUTION, authority_domain=DOMAIN, operation=OPERATION),
              expected_action_id=ACTION_ID, expected_operation_id=OPERATION, verification_time=VERIFY_T, time_mode="as_of", min_trust_snapshot_version=1,
              last_accepted_snapshot=None, expected_host_ages=dict(HOST_AGES), control_plane_source_revision=CP_PR_HEAD, registry_source_revision=REGISTRY_PR_HEAD)
    kw.update(over)
    return RegistryEvidenceTrust(**kw)


def context(**over):
    kw = dict(consumer_id=CONSUMER, tenant=TENANT_ID, institution=INSTITUTION, authority_domain=DOMAIN, operation=OPERATION)
    kw.update(over)
    return RegistryExpectedContext(**kw)


def do_import(cp, proposal, trust_obj=None, *, selector=SELECTOR, revision=CUR_CP, export=None, **kw):
    if trust_obj is not None or "registry_evidence_trust" in kw:
        kw.setdefault("registry_evidence_trust", trust_obj)
    return I.import_bounded_workflow(copy.deepcopy(cp), proposal=copy.deepcopy(proposal), moltbot_export=export, control_plane_revision=revision,
                                     control_plane_profile=selector, **kw)


def refused(cp, proposal, trust_obj, code, *, reached_verifier=None, layer=None, adapter_code=None, **kw):
    """Run the import expecting the SPECIFIC typed refusal `code`. Asserts: it raised ImportContractError(code); no bundle came back (the call never returned);
    whether the real Registry adapter was reached (`reached_verifier`) and, if so, which Registry layer refused (`layer`) with which Registry code (`adapter_code`)."""
    bundle = None
    with pytest.raises(ImportContractError) as exc:
        bundle = do_import(cp, proposal, trust_obj, **kw)
    assert bundle is None
    assert exc.value.code == code, (exc.value.code, str(exc.value))
    spy = getattr(trust_obj, "verifier", None)
    if isinstance(spy, Spy):
        if reached_verifier is not None:
            assert (spy.calls > 0) is reached_verifier, "verifier calls: %d" % spy.calls
        if layer is not None:
            assert spy.last["layers"][layer] == "refuse", spy.last["layers"]
        if adapter_code is not None:
            assert spy.last["ok"] is False and spy.last["code"] == adapter_code, spy.last
    leaked = ("SNAPSHOT", "signature", "-----")  # nothing of the opaque trust snapshot or the verifier's text reaches the exception
    assert not any(tok in str(exc.value) for tok in leaked[:1])
    return exc.value


def admitted(cp, proposal, trust_obj=None, **kw):
    trust_obj = trust_obj if trust_obj is not None else make_trust()
    bundle = do_import(cp, proposal, trust_obj, **kw)
    return bundle, trust_obj


SUCCESS_KEYS = RE.SUCCESS_MARKER_KEYS
# Review-fix pin: the marker that lists what the verifier's verdict ASSERTED is `registry_claims_asserted_by_verifier_verdict`; the old key `registry_verified_claims` must be absent.
CLAIMS_KEY = "registry_claims_asserted_by_verifier_verdict"
OLD_CLAIMS_KEY = "registry_verified_claims"


def assert_exact_claim_a_markers(bundle, *, issuer="issuer-test-1", epoch=1, selection_id="sel-test-1", time_mode="as_of_historical"):
    m = bundle.metadata
    assert m["registry_authenticated"] is False
    assert m["registry_origin"] == "registry_origin_unverified"
    assert m["control_plane_decision_authenticated"] is False
    assert m["control_plane_profile"] == SELECTOR
    assert m["registry_selection_verification"] == RE.MARKER_SELECTION_VERIFICATION
    assert m["registry_selection_admitted_by_injected_verifier"] is True
    assert m["registry_authentication_claim"] == "A_selection_signature_per_injected_verifier"
    assert m["registry_trust_snapshot_attestation"] == "operator_supplied_unattested"
    assert m["registry_verified_scope"] == "decision_time_only" and m["registry_verified_time_mode"] == time_mode
    assert m[CLAIMS_KEY] == RE.MARKER_CLAIMS_ASSERTED_BY_VERIFIER_VERDICT and OLD_CLAIMS_KEY not in m and OLD_CLAIMS_KEY not in SUCCESS_KEYS and m["registry_not_verified"] == RE.MARKER_NOT_VERIFIED
    assert m["registry_declared_source_revisions"] == {"control_plane": CP_PR_HEAD, "registry": REGISTRY_PR_HEAD, "attestation": "operator_declared_unattested"}
    assert m["claim_scope_note"] == RE.CLAIM_SCOPE_NOTE
    # claim A only: no marker anywhere says the Control Plane DECISION, the Registry ORIGIN or the Registry AUTHORITY is established
    for key, value in m.items():
        if "decision_authenticated" in key or key in ("registry_authenticated",):
            assert value is False, key
    assert not [k for k in m if k.startswith(("claim_b", "decision_authentic", "registry_origin_verified", "registry_authority"))]
    (ev0,) = m["registry_evidence"]
    assert (ev0["issuer_id"], ev0["epoch"], ev0["selection_id"], ev0["family"]) == (issuer, epoch, selection_id, F4)
    return ev0


def stub_accepts_everything(request):
    """A caller-injected STUB verifier (NF-2 demonstration only): checks nothing, returns a self-consistent ok verdict by echoing the request."""
    t = request["trust_snapshot"]
    eff = {k: min(request["host_policy"][k], BOUND[i]) for i, k in enumerate(("status_max_age_seconds", "approval_max_age_seconds"))}
    digest = pid.effective_policy_digest(F4, eff)
    return {"contract": "registry-evidence-verdict/0.1", "ok": True, "code": None, "authenticated": True, "layers": {n: "pass" for n in v.LAYERS_V2}, "family": request["family"],
            "registry_contract": request["registry_contract"], "selection_text_sha256": sha256_text(request["selection_text"]), "record_text_sha256": sha256_text(request["record_text"]),
            "verification_time_utc": request["verification_time_utc"], "trust_snapshot_id": t.snapshot_id, "trust_snapshot_version": t.version,
            "trust_snapshot_fingerprint": "sha256:" + "0" * 64,
            "floors_applied": {"min_trust_snapshot_version": True, "last_accepted_snapshot": request["last_accepted_snapshot"] is not None}, "epoch_floor_applied": False,
            "issuer_id": "issuer-STUB", "selection_id": "sel-STUB", "epoch": 1, "selection_digest": "sha256:" + "1" * 64, "bound_record_digest": "sha256:" + "2" * 64,
            "effective_policy_digest": digest, "effective_values": dict(eff), "verifier_implementation": {"name": "caller-injected-stub", "registry_revision": "none"}}


class StubVerifier:
    """NOT the Registry adapter. Accepts anything (see stub_accepts_everything)."""

    def __init__(self):
        self.calls = 0

    def verify_selection_evidence(self, request):
        self.calls += 1
        return stub_accepts_everything(request)


def make_trust_unvalidated(**over):
    """A trust object built without __post_init__ (as a hostile caller could); Replay re-validates at import."""
    t = make_trust()
    for k, val in over.items():
        object.__setattr__(t, k, val)
    return t


def fixture_request(cp, proposal):
    """The exact request Replay would send for the (possibly tampered) record, built with Replay's own builder (for asserting the real adapter's verdict code)."""
    tr = RE.validate_trust(make_trust())
    d = cp["decisions"][0]
    return RE.build_request(d["selection_evidence"], tr, dict(HOST_AGES))
