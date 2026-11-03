"""R2 joined-chain harness (qualification-side test code; BUILDER_TESTED developer evidence, NOT independent qualification).

PRIVATE PREVIEW QUALIFICATION TUPLE only (preview-only, NOT canonical, not component-lock). Synthetic only: single synthetic tenant, synthetic Ed25519 seeds, no network.

================================================================================ PUBLIC HELPER API (backward compatible; Worker B builds on it)
Environment
    SRC_DIR            env var: parent directory of the fetched subject sources (``control_plane/``, ``registry/``, ``replay/`` as named in r2_chain/sources.json "dir").
    R2_SOURCES_JSON    optional env override of the path of sources.json (default: r2_chain/sources.json). SHAs are only ever READ from it.
    R2_ROWS_JSONL      optional env var: path of the result-row JSONL the conftest recorder appends to (run_chain.py sets it).
    R2_OUT_DIR         optional env var: output directory for ``publish_artifact`` (run_chain.py sets it).

Pinned identity (read from sources.json, never duplicated)
    SOURCES, src(name) -> Path, git(name, *args) -> str          # `git --no-replace-objects -C <src dir> ...`
    CP_SHA, REGISTRY_SHA, REPLAY_SHA                             # exact pins; CP_PR_HEAD / REGISTRY_PR_HEAD are aliases kept for ported code
    assert_modules_from_pins()                                   # every imported subject module file lives under SRC_DIR (no local shadow module)

Registry side (synthetic signing; ported from rw01 harness, mechanism tests only)
    sign, record(status, approval), grant, trust(...), statement, envelope_text, Material, material(status, approval, *, rec, host_trust, sk, key_id, pub,
    stmt_over, ensure_ascii, signature, record_text), withdrawal_text(base)
    constants: PK SK OTHER_PK OTHER_SK KEY_ID OTHER_KEY_ID CONSUMER ACTION_ID OPERATION TENANT_ID INSTITUTION DOMAIN SCOPE STMT_SCOPE EFFECTIVE ISSUED
               HOST_AGES BOUND VERIFY_T NOW F4 SELECTOR (= F4 profile string) OLD_SELECTOR CUR_CP

Control Plane side (real GovernedAgeWorkflow(carry_selection_evidence=True), real BoundedRecordStore)
    produce_real(workdir=None, *, mat=None, carry=True, execute=False, tenant=None, operator=None) -> RealRecord     # lazy wrapper of real_cp_record.produce_real
    RealRecord: .path .written_bytes .retrieved_bytes .record(dict, retrieved run.json) .retrieved_model .proposal .material .decision_id .operator(OperatorInputs)
                .decision (record["decisions"][0]) .evidence (decision["selection_evidence"]) .destination_path .workdir
    default_operator_inputs(...) -> OperatorInputs         # operator-side trust inputs, independent of the record; .with_(**changes), .as_replay_trust(verifier)
    reload_record(rr) -> RealRecord-like dict {bytes, record}  # fresh BoundedRecordStore on the same path (the supported restart/reload path)
    variant_* producers of real_cp_record (forged signature, wrong context, no carry, wrong-tenant record, substituted pair, mutated effective policy)

Replay side
    import_f4(record, operator, *, proposal, verifier=None, selector=SELECTOR_F4, revision=None, pass_trust=True, **extra) -> (bundle, replay_trust_object)
        the SINGLE call into Replay import_bounded_workflow with the explicit F4 profile; verifier defaults to Spy() around the REAL RegistryEvidenceVerifierV2.
    refuse_import(record, operator, proposal, expected_code, *, verifier_calls=None, layers=None, spy=None, selector=SELECTOR_F4, **kw) -> RefusalResult
        asserts ImportContractError.code == expected_code (exact), no bundle returned, optional verifier call count and last-verdict layers; RECORDS the
        refusal (expected + observed typed code) for the result row. RefusalResult: .code .message .spy .calls .bundle(None)
    expect_refusal(expected_code, exc=Exception) -> context manager for any other typed refusal (CP / store / Replay); records expected and observed (.code attribute)
    Spy(inner=None, mutate=None)  # observation wrapper around the real adapter; .calls .requests .verdicts .last ; mutate(verdict, request) -> verdict for malformed-verdict negatives
    make_trust(...)               # raw RegistryEvidenceTrust (rw01 style); StubVerifier / stub_accepts_everything for NF-2 style cases
    assert_exact_claim_a_markers(bundle, ...)        # claim A markers exactly; no claim B key; registry_authenticated False

Tamper helpers (explicitly labelled TAMPERED; deep copies, genuine record untouched)
    tampered_copy_selection_text(rr, fn), tampered_copy_record_text(rr, fn), tamper_decision(rr_or_record, fn(decision_dict)), tamper_evidence(rr_or_record, fn(evidence_dict)),
    swap_evidence(record, other_evidence), reseal(cp, mutate)   # reseal: recompute effective_configuration digest only for fixture-style records
    jdump(x) canonical json text; sha256_text(text)

Recording (pytest hooks live in conftest.py)
    @pytest.mark.row("<row id>", "<case id / title>", kind="positive"|"negative"|"persistence"|"structure")
        one result row per marked test (per parametrization): {row_id, case_id, kind, label, expected_code, observed_code, refusals[], checks[], verifier_calls, nodeid, outcome}
        label: PASS | FAIL | REFUSED_AS_EXPECTED (test passed AND recorded >=1 refusal via refuse_import/expect_refusal) | NOT_RUN | NOT_APPLICABLE (skip reason starts with NOT_APPLICABLE)
    check(label, condition, detail="")   # explicit LABELLED assertion: recorded in the row's checks[] (PASS/FAIL) and raises AssertionError when false
    note(key, value)                     # attach a JSON-able detail to the current row
    publish_artifact(name, obj)          # write JSON evidence into R2_OUT_DIR (no-op when unset)
    emit_row(...)                        # explicit extra row (rarely needed)

Result labels used verbatim: PASS / FAIL / REFUSED_AS_EXPECTED / NOT_RUN / NOT_APPLICABLE. Claim A only; claim B is never asserted.
"""
from __future__ import annotations

import base64
import contextlib
import copy
import dataclasses
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LANE = HERE.parent
SOURCES_JSON = Path(os.environ.get("R2_SOURCES_JSON") or (LANE / "sources.json"))
SOURCES = json.loads(SOURCES_JSON.read_text())["sources"]
if "SRC_DIR" not in os.environ:
    raise RuntimeError("SRC_DIR is not set: point it at the directory holding the fetched subject sources (see r2_chain/fetch_sources.sh)")
SRC_DIR = Path(os.environ["SRC_DIR"]).resolve()

CP_SHA = SOURCES["control_plane"]["sha"]
REGISTRY_SHA = SOURCES["registry"]["sha"]
REPLAY_SHA = SOURCES["replay"]["sha"]
CP_PR_HEAD, REGISTRY_PR_HEAD = CP_SHA, REGISTRY_SHA      # aliases of the ported rw01 code


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
SELECTOR_F4 = RE.REGISTRY_AUTHENTICATED_SELECTION_F4_PROFILE      # "registry-authenticated-selection-f4-governed/0.1"
F4_SELECTOR = SELECTOR_F4
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
VERIFY_T = NOW                                                            # the operator's explicit verification time (== the decision time of the synthetic CP clock)
SUCCESS_KEYS = RE.SUCCESS_MARKER_KEYS
CLAIMS_KEY = "registry_claims_asserted_by_verifier_verdict"
OLD_CLAIMS_KEY = "registry_verified_claims"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def jdump(x) -> str:
    return json.dumps(x, sort_keys=True)


def assert_modules_from_pins() -> dict:
    """No local shadow module: every loaded module of the three subject trees resolves to a file under SRC_DIR. Returns {top-level package: dir}."""
    found = {}
    for pkg, owner in (("agent_control_plane", "control_plane"), ("agent_replay_bundle", "replay"), ("registry_successor", "registry"),
                       ("registry_consumer", "registry"), ("registry_adapters", "registry")):
        mod = sys.modules[pkg]
        f = Path(mod.__file__).resolve()
        assert src(owner) in f.parents, "module %s resolves to %s, outside the pinned %s tree %s" % (pkg, f, owner, src(owner))
        found[pkg] = str(f.parent.relative_to(SRC_DIR))
    return found


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
class Source:
    """Callable selection source handed to GovernedAgeWorkflow; counts the calls (proves the Control Plane asked the Registry material)."""

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


# ------------------------------------------------------------------------------------------------------------------------------ fixture-style record helpers
def reseal(cp, mutate):
    """Mutate effective_configuration members and recompute Replay's own digest (fixture-style record only)."""
    cp = copy.deepcopy(cp)
    ec = cp["decisions"][0]["binding"]["runtime_authority"]["effective_configuration"]
    mutate(ec["members"])
    ec["digest"] = EC.digest_of(ec["version"], ec["members"])
    return cp


def row(cp):
    """The f4_ages family row of the record's effective_configuration."""
    return next(x for x in cp["decisions"][0]["binding"]["runtime_authority"]["effective_configuration"]["members"]["families"] if x["slot"] == "f4_ages")


# ------------------------------------------------------------------------------------------------------------------------------ Replay side (operator trust)
class Spy:
    """Observation wrapper around a verifier: records each request and verdict, delegates unchanged (NOT a stub). Replay cannot tell it from the wrapped adapter
    (known non-detection NF-2). `mutate(verdict_copy, request) -> verdict` lets a negative case return a malformed/forged verdict AFTER the real adapter ran."""

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
              last_accepted_snapshot=None, expected_host_ages=dict(HOST_AGES), control_plane_source_revision=CP_SHA, registry_source_revision=REGISTRY_SHA)
    kw.update(over)
    return RegistryEvidenceTrust(**kw)


def context(**over):
    kw = dict(consumer_id=CONSUMER, tenant=TENANT_ID, institution=INSTITUTION, authority_domain=DOMAIN, operation=OPERATION)
    kw.update(over)
    return RegistryExpectedContext(**kw)


def assert_exact_claim_a_markers(bundle, *, issuer="issuer-test-1", epoch=1, selection_id="sel-test-1", time_mode="as_of_historical", profile=None):
    """Exactly the current Replay claim-A contract; returns the single registry_evidence entry. No claim B / origin / authority marker may exist."""
    m = bundle.metadata
    assert m["registry_authenticated"] is False
    assert m["registry_origin"] == "registry_origin_unverified"
    assert m["control_plane_decision_authenticated"] is False
    assert m["control_plane_profile"] == (SELECTOR_F4 if profile is None else profile)
    assert m["registry_selection_verification"] == RE.MARKER_SELECTION_VERIFICATION
    assert m["registry_selection_admitted_by_injected_verifier"] is True
    assert m["registry_authentication_claim"] == "A_selection_signature_per_injected_verifier"
    assert m["registry_trust_snapshot_attestation"] == "operator_supplied_unattested"
    assert m["registry_verified_scope"] == "decision_time_only" and m["registry_verified_time_mode"] == time_mode
    assert m[CLAIMS_KEY] == RE.MARKER_CLAIMS_ASSERTED_BY_VERIFIER_VERDICT and OLD_CLAIMS_KEY not in m and OLD_CLAIMS_KEY not in SUCCESS_KEYS and m["registry_not_verified"] == RE.MARKER_NOT_VERIFIED
    assert m["registry_declared_source_revisions"] == {"control_plane": CP_SHA, "registry": REGISTRY_SHA, "attestation": "operator_declared_unattested"}
    assert m["claim_scope_note"] == RE.CLAIM_SCOPE_NOTE
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


# ------------------------------------------------------------------------------------------------------------------------------ recording context (see conftest.py)
class _Ctx:
    def __init__(self, nodeid: str):
        self.nodeid = nodeid
        self.checks: list = []
        self.refusals: list = []
        self.notes: dict = {}
        self.verifier_calls = None


_CTX: "_Ctx | None" = None


def _ctx() -> _Ctx:
    global _CTX
    if _CTX is None:
        _CTX = _Ctx("<no-test>")
    return _CTX


def check(label: str, condition, detail: str = "") -> None:
    """Explicit labelled assertion: recorded (PASS/FAIL) in the current row's `checks`, raises AssertionError when false."""
    ok = bool(condition)
    _ctx().checks.append({"check": label, "result": "PASS" if ok else "FAIL", "detail": str(detail)[:500]})
    assert ok, "%s %s" % (label, detail)


def note(key: str, value) -> None:
    _ctx().notes[key] = value


def publish_artifact(name: str, obj) -> "Path | None":
    out = os.environ.get("R2_OUT_DIR")
    if not out:
        return None
    p = Path(out)
    p.mkdir(parents=True, exist_ok=True)
    (p / name).write_text(json.dumps(obj, indent=1, sort_keys=True) + "\n")
    return p / name


def _record_refusal(expected, observed, **extra) -> None:
    _ctx().refusals.append(dict(expected_code=expected, observed_code=observed, **extra))


# ------------------------------------------------------------------------------------------------------------------------------ real producer / replay (lazy; real_cp_record imports this module)
def produce_real(*a, **kw):
    import real_cp_record as R
    return R.produce_real(*a, **kw)


def default_operator_inputs(*a, **kw):
    import real_cp_record as R
    return R.default_operator_inputs(*a, **kw)


def reload_record(rr):
    import real_cp_record as R
    return R.reload_record(rr)


def import_f4(record, operator, *, proposal, verifier=None, selector=None, revision=None, pass_trust: bool = True, **extra):
    """The SINGLE call into Replay `import_bounded_workflow` with the explicit F4 profile. Returns (bundle, replay_trust_object|None). Raises ImportContractError unchanged."""
    import real_cp_record as R
    return R.import_through_replay_f4_with_trust(record, operator, proposal=proposal, verifier=verifier, selector=selector or SELECTOR_F4, revision=revision, pass_trust=pass_trust, **extra)


@dataclasses.dataclass
class RefusalResult:
    code: str
    message: str
    spy: "Spy | None"
    calls: "int | None"
    bundle: None = None


def refuse_import(record, operator, proposal, expected_code, *, verifier_calls=None, layers=None, spy=None, selector=None, pass_trust: bool = True, verifier=None, **kw) -> RefusalResult:
    """Run the F4 import expecting the SPECIFIC typed refusal `expected_code` (exact string; None means "any typed code is recorded but not compared" - avoid).

    Asserts: ImportContractError raised; the call returned no bundle (so no admission/success marker exists); optional `verifier_calls` (how often the real Registry adapter
    was reached) and `layers` ({layer: "refuse"|"pass"...} of the adapter's last verdict); the exception text leaks nothing of the opaque trust snapshot.
    The refusal (expected + observed code) is recorded for the result row BEFORE the assertions run, so a mismatch is reported as FAIL with both codes."""
    if verifier is None and pass_trust:
        verifier = spy if spy is not None else Spy()
    spy = verifier if isinstance(verifier, Spy) else None
    out = None
    try:
        out = import_f4(record, operator, proposal=proposal, verifier=verifier, selector=selector, pass_trust=pass_trust, **kw)
    except ImportContractError as e:
        code = e.code
        _record_refusal(expected_code, code, verifier_calls=None if spy is None else spy.calls, message=str(e)[:200])
        _ctx().verifier_calls = None if spy is None else spy.calls
        assert expected_code is None or code == expected_code, (code, str(e))
        if spy is not None and verifier_calls is not None:
            assert spy.calls == verifier_calls, "verifier calls: %d (want %d)" % (spy.calls, verifier_calls)
        if spy is not None and layers:
            for layer, value in layers.items():
                assert spy.last["layers"][layer] == value, spy.last["layers"]
        assert "SNAPSHOT" not in str(e)
        return RefusalResult(code, str(e), spy, None if spy is None else spy.calls)
    _record_refusal(expected_code, None, message="NOT REFUSED: import returned a bundle")
    raise AssertionError("expected refusal %r but the import returned a bundle (%r)" % (expected_code, getattr(out[0], "metadata", {}).get("control_plane_profile")))


@contextlib.contextmanager
def expect_refusal(expected_code, exc=Exception):
    """Context manager for any typed refusal outside the Replay import call (Control Plane, record store, persistence reload ...). The exception's `.code` (else
    its first `.reasons` / class name) is the observed typed code. Records expected + observed; fails when nothing is raised or the code differs."""
    box = type("Box", (), {"code": None, "exception": None})()
    try:
        yield box
    except exc as e:
        observed = getattr(e, "code", None) or (list(getattr(e, "reasons", []) or [None])[0]) or type(e).__name__
        box.code, box.exception = observed, e
        _record_refusal(expected_code, observed, message=str(e)[:200])
        assert expected_code is None or observed == expected_code, (observed, str(e))
        return
    _record_refusal(expected_code, None, message="NOT REFUSED")
    raise AssertionError("expected refusal %r but nothing was raised" % (expected_code,))


# ------------------------------------------------------------------------------------------------------------------------------ TAMPER helpers (deep copies; genuine untouched)
def _rec(x):
    return x.record if hasattr(x, "record") and not isinstance(x, dict) else x


def tamper_decision(x, fn) -> dict:
    """TAMPERED: deep copy of the record with fn(decision_dict) applied to decisions[0] (fn may mutate in place or return a replacement)."""
    rec = copy.deepcopy(_rec(x))
    out = fn(rec["decisions"][0])
    if out is not None:
        rec["decisions"][0] = out
    return rec


def tamper_evidence(x, fn) -> dict:
    """TAMPERED: deep copy with fn(selection_evidence_dict) applied (in place or returning a replacement)."""
    def _f(d):
        res = fn(d["selection_evidence"])
        if res is not None:
            d["selection_evidence"] = res
    return tamper_decision(x, _f)


def tampered_copy_selection_text(x, mutate) -> dict:
    return tamper_evidence(x, lambda e: e.__setitem__("selection_text", mutate(e["selection_text"])))


def tampered_copy_record_text(x, mutate) -> dict:
    return tamper_evidence(x, lambda e: e.__setitem__("record_text", mutate(e["record_text"])))


def swap_evidence(record_, other_evidence) -> dict:
    """SWAPPED: deep copy of the record whose selection_evidence is replaced by (a deep copy of) another run's genuine evidence."""
    return tamper_evidence(record_, lambda e: copy.deepcopy(other_evidence))


# ------------------------------------------------------------------------------------------------------------------------------ emit explicit rows
_EXTRA_ROWS: list = []


def emit_row(row_id, case_id, label, *, expected_code=None, observed_code=None, kind="negative", detail=None) -> None:
    """Explicit extra row (normally rows come from @pytest.mark.row)."""
    _EXTRA_ROWS.append(dict(row_id=row_id, case_id=case_id, kind=kind, label=label, expected_code=expected_code, observed_code=observed_code, detail=detail, nodeid=_ctx().nodeid))
