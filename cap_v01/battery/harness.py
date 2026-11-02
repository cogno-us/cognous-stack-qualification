"""Shared harness of the CAP v0.1 gate G1 qualification battery (independent test author; written from the FROZEN CONTRACT, not from the implementer's tests).

Unit under test: `agent_control_plane.registry_authority_profile` at the Control Plane G1 head (exact SHA in ../sources.json). Everything below the unit is REAL:
the Control Plane `GovernedAgeWorkflow`, the Registry `verify_f4_selection_v2` (all eleven layers) with the exact `Ed25519Verifier` and PyNaCl signatures, and (P1) Replay's
`registry-authenticated-selection/0.1` import. Only the key material is SYNTHETIC (mechanism tests, no trust root, no custody). NO durable anti-rollback (G2) is tested here.

Spies (`Spy`) wrap the Registry entry points in place and delegate unchanged; they record whether the verifier was REACHED and what it said.
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
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = HERE.parent
SPEC = json.loads((KIT / "sources.json").read_text())
SOURCES = SPEC["sources"]
_src_env = os.environ.get("CAP_SRC_DIR")
if not _src_env:
    raise RuntimeError("CAP_SRC_DIR must point at the directory holding the pinned checkouts (<CAP_SRC_DIR>/control_plane, registry, replay); see ../README.md")
SRC_DIR = Path(_src_env).resolve()


def src(name: str) -> Path:
    return SRC_DIR / SOURCES[name]["dir"]


def git(name: str, *args: str) -> str:
    return subprocess.run(["git", "--no-replace-objects", "-C", str(src(name)), *args], capture_output=True, text=True, check=True).stdout.strip()


def bootstrap_paths() -> None:
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
from registry_successor import v2_verified_selection as vsel  # noqa: E402
from registry_successor import verify as v  # noqa: E402

import agent_control_plane.bounded as cp_bounded  # noqa: E402
import agent_control_plane.registry_f4_age_governance as cp_f4  # noqa: E402
import agent_control_plane.registry_authority_profile as AP  # noqa: E402  (UNIT UNDER TEST)
from agent_control_plane.bounded import BoundedRecordStore, LocalRefundDestination, ObservationPolicy  # noqa: E402
from agent_control_plane.registry_f4_age_governance import GovernedScope, SelectionMaterial  # noqa: E402
from tests.test_bounded_authorization import NOW, manifest, tenant_proposal, tenant_resolver_for, TENANT  # noqa: E402  (Control Plane test builders, reused)

from agent_replay_bundle import effective_configuration as EC  # noqa: E402
from agent_replay_bundle import importers as I  # noqa: E402
from agent_replay_bundle import registry_evidence as RE  # noqa: E402
from agent_replay_bundle.registry_evidence import (RegistryEvidenceTrust, RegistryExpectedContext, RegistryTrustSnapshotRef,  # noqa: E402
                                                   REGISTRY_AUTHENTICATED_SELECTION_PROFILE as SELECTOR)

# ---------------------------------------------------------------------------------------------------------------------------------------------- constants (SYNTHETIC)
F4 = f4.FAMILY_F4
PK, SK = nb.crypto_sign_seed_keypair(bytes(range(32)))                 # SYNTHETIC seeds: mechanism tests only
ATT_PK, ATT_SK = nb.crypto_sign_seed_keypair(bytes(range(77, 109)))    # the attacker's own keypair
KEY_ID = s.KEY_ID
ISSUER_ID = "issuer-test-1"
CONSUMER = "consumer-test"
_action = manifest()["actions"][0]
ACTION_ID = _action["action_id"]
INSTITUTION = _action["authority_context"]["institution_id"]
DOMAIN = _action["authority_context"]["authority_domain"]
TENANT_ID = TENANT.lower()
OPERATION = "refund-issue-routine"
SCOPE = GovernedScope(CONSUMER, TENANT_ID, ACTION_ID, OPERATION)
CONTEXT = {"consumer_id": CONSUMER, "tenant_id": TENANT_ID, "institution": INSTITUTION, "authority_domain": DOMAIN, "operation": OPERATION}
STMT_SCOPE = {"tenant": TENANT_ID, "institution": INSTITUTION, "authority_domain": DOMAIN}
EFFECTIVE = {"valid_from": "2026-10-01T00:00:00Z", "valid_until": "2026-10-06T00:00:00Z"}
ISSUED = "2026-10-01T00:00:00Z"
SELECTION_ID = "sel-test-1"
BOUND = (120, 90)                                                      # signed bound; host default (60, 60) => effective = per-scalar min = (60, 60)
HOST_AGES = {"status_max_age_seconds": 60, "approval_max_age_seconds": 60}
AS_OF = "2026-10-05T19:00:00Z"                                         # == NOW of the Control Plane test harness
SNAP_ID, SNAP_VERSION = "snap-cap-1", 1
SYNTH = "UNSELECTED-SYNTHETIC"
GRANT_ROW = [CONSUMER, TENANT_ID, INSTITUTION, DOMAIN, OPERATION]
PROFILE_SHA_PREFIX = "sha256:"


def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_tag(b: bytes) -> str:
    return "sha256:" + sha256_hex(b)


# ---------------------------------------------------------------------------------------------------------------------------------------------- snapshot document
def issuer_entry(key_id=KEY_ID, issuer_id=ISSUER_ID, pub=PK, grants=None):
    return {"alg": "ed25519", "authority": [list(g) for g in (grants if grants is not None else [GRANT_ROW])], "issuer_id": issuer_id, "key_id": key_id, "public_key": pub.hex()}


def snapshot_doc(**over):
    """Registry normalized snapshot document (the separate pinned trust document): public keys live HERE, never in the configuration."""
    doc = {"snapshot_id": SNAP_ID, "version": SNAP_VERSION, "valid_until": "2026-10-07T00:00:00Z", "issuers": [issuer_entry()],
           "min_epochs": [[SELECTION_ID, 1]], "revoked_key_ids": [], "revoked_selections": []}
    doc.update(over)
    return doc


def fingerprint_of(doc) -> str:
    return pid.trust_snapshot_fingerprint(copy.deepcopy(doc))


def trust_object(doc=None):
    """The Registry `TrustSnapshot` object equal to `doc` (what a HOST would hand over as its own snapshot)."""
    n = pid.normalize_snapshot(copy.deepcopy(doc if doc is not None else snapshot_doc()))
    return v.TrustSnapshot(n["snapshot_id"], n["version"], n["valid_until"],
                           tuple(v.IssuerEntry(e["key_id"], e["issuer_id"], e["alg"], bytes.fromhex(e["public_key"]), tuple(v.AuthorityGrant(*g) for g in e["authority"]))
                                 for e in n["issuers"]),
                           frozenset(n["revoked_key_ids"]), frozenset((p[0], p[1]) for p in n["revoked_selections"]), tuple((p[0], p[1]) for p in n["min_epochs"]))


def dump(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=1) + "\n").encode("utf-8")


# ---------------------------------------------------------------------------------------------------------------------------------------------- configuration
def base_config(doc=None, *, mode="synthetic", snapshot_ref="snapshot.json") -> dict:
    doc = doc if doc is not None else snapshot_doc()
    return {
        "version": "ocs-authority-profile/0.1", "id": "cap-profile-1", "mode": mode,
        "verifier": {"contract": "r08-v2", "family": "f4"},
        "trust_anchor": {"algorithm": "ed25519", "keys": [{"key_id": e["key_id"], "public_key_sha256": sha_tag(bytes.fromhex(e["public_key"]))} for e in doc["issuers"]]},
        "issuers": [{"issuer_id": e["issuer_id"], "key_id": e["key_id"],
                     "grants": [dict(zip(("consumer_id", "tenant", "institution", "authority_domain", "operation"), g)) for g in e["authority"]]} for e in doc["issuers"]],
        "expected_context": dict(zip(("consumer_id", "tenant", "institution", "authority_domain", "operation"), GRANT_ROW)),
        "snapshot": {"source": {"kind": "file", "reference": snapshot_ref},
                     "expected": {"snapshot_id": doc["snapshot_id"], "version": doc["version"], "fingerprint": fingerprint_of(doc)}},
        "clock": {"kind": "fixed_instant", "as_of": AS_OF},
        "state": {"backend": "none-g1", "namespace": "cap-qual", "reference": "state-ref-1", "anchor_reference": "anchor-ref-1"},
        "identities": {"snapshot_publisher_ref": SYNTH, "enforcing_operator_ref": SYNTH, "state_admin_ref": SYNTH},
    }


@dataclasses.dataclass
class Kit:
    dir: Path
    config_path: Path
    snapshot_path: Path
    doc: dict
    config: dict
    digest: str

    def rewrite_config(self, config=None, raw: bytes = None):
        data = raw if raw is not None else dump(config if config is not None else self.config)
        self.config_path.write_bytes(data)
        self.digest = sha_tag(data)
        return self.digest

    def load(self, mode="synthetic", digest=None):
        return AP.load_authority_profile(self.config_path, expected_mode=mode, expected_config_digest=digest)


def make_kit(tmp: Path, *, doc=None, config_edit=None, mode="synthetic", snapshot_name="snapshot.json") -> Kit:
    """Write <tmp>/auth/{authority.json, snapshot.json}. `config_edit(config_dict)` mutates the configuration before it is written."""
    d = tmp / "auth"
    d.mkdir(parents=True, exist_ok=True)
    doc = doc if doc is not None else snapshot_doc()
    cfg = base_config(doc, mode=mode, snapshot_ref=snapshot_name)
    if config_edit:
        config_edit(cfg)
    (d / snapshot_name).write_bytes(dump(doc))
    k = Kit(d, d / "authority.json", d / snapshot_name, doc, cfg, "")
    k.rewrite_config()
    return k


# ---------------------------------------------------------------------------------------------------------------------------------------------- signed material
def sign(stmt, sk=None, domain=None):
    return base64.b64encode(nb.crypto_sign((domain or s.V2_DOMAIN) + c.canonical_bytes(stmt), sk or SK)[:64]).decode("ascii")


def record(status=BOUND[0], approval=BOUND[1], **over):
    body = dict(r.make_record(), contract_version="r08-v2", family=F4, record_id="f4-age-record",
                payload={"status_max_age_seconds": status, "approval_max_age_seconds": approval})
    body.update(over)
    return r.seal_record(body)


def statement(rec, **over):
    kw = dict(family=rec.get("family", F4), consumer_id=CONSUMER, scope=dict(STMT_SCOPE), operation=OPERATION, effective=dict(EFFECTIVE), issued_at=ISSUED)
    kw.update(over)
    return r.make_statement_v2(rec, **kw)


def envelope_text(stmt, *, sk=None, key_id=KEY_ID, pub=PK):
    return json.dumps(s.envelope(stmt, signature=sign(stmt, sk), pub=pub, key_id=key_id), sort_keys=True, ensure_ascii=True)


@dataclasses.dataclass
class Material:
    record_text: str
    selection_text: str
    host_trust: object

    def selection_material(self) -> SelectionMaterial:
        return SelectionMaterial(self.record_text, self.selection_text, self.host_trust)


def material(*, host_trust=None, sk=None, key_id=KEY_ID, pub=PK, stmt_over=None, rec=None) -> Material:
    rec = rec if rec is not None else record()
    stmt = statement(rec, **(stmt_over or {}))
    return Material(r.dumps(rec), envelope_text(stmt, sk=sk, key_id=key_id, pub=pub), host_trust if host_trust is not None else trust_object())


class Source:
    """The HOST's selection source (counts its own reads)."""

    def __init__(self, mat):
        self.mat, self.calls = mat, 0

    def __call__(self):
        self.calls += 1
        return self.mat.selection_material() if isinstance(self.mat, Material) else self.mat


# ---------------------------------------------------------------------------------------------------------------------------------------------- spies (delegate unchanged)
class Spy:
    """Installed by the `spy` fixture: wraps `verify_f4_selection_v2` and the exact `Ed25519Verifier._check` IN PLACE, records and delegates. `reached` is True iff the Registry
    verifier core was entered; `crypto` counts real Ed25519 checks of a SELECTION signature (the constructor self-test is not counted); `verifier_types` records the exact type of the verifier object the unit handed to the core."""

    def __init__(self):
        self.calls, self.verdicts, self.verifier_types, self.crypto = [], [], [], 0

    @property
    def reached(self) -> bool:
        return bool(self.calls)

    @property
    def n(self) -> int:
        return len(self.calls)

    def reset(self):
        self.calls.clear(); self.verdicts.clear(); self.verifier_types.clear(); self.crypto = 0


@pytest.fixture
def spy(monkeypatch):
    sp = Spy()
    real_core = vsel.verify_f4_selection_v2
    real_check = ev.Ed25519Verifier._check

    def core(selection_text, record_text, context, trust, verifier, now, **kw):
        sp.calls.append((selection_text, record_text, context, trust, now, kw))
        sp.verifier_types.append(type(verifier))
        out = real_core(selection_text, record_text, context, trust, verifier, now, **kw)
        sp.verdicts.append(out)
        return out

    def check(self, public_key, message, signature):
        if bytes(message).startswith(s.V2_DOMAIN):   # the verifier's constructor self-test also calls _check; only a check of a SELECTION signature counts
            sp.crypto += 1
        return real_check(self, public_key, message, signature)

    monkeypatch.setattr(vsel, "verify_f4_selection_v2", core)
    monkeypatch.setattr(ev.Ed25519Verifier, "_check", check)
    return sp


# ---------------------------------------------------------------------------------------------------------------------------------------------- Control Plane flow through the factory
def flow_kwargs(tmp: Path, proposal=None):
    p = proposal if proposal is not None else tenant_proposal()
    return p, dict(manifest=manifest(), destination=LocalRefundDestination(tmp / "destination.json"), records=BoundedRecordStore(tmp / "run.json", "run-1"),
                   observation_policy=ObservationPolicy(max_age_seconds=300, clock_tolerance_seconds=5), resolver=tenant_resolver_for(p))


def build(tmp: Path, kit: Kit, mat, *, mode="synthetic", digest="kit", scope=None, host_source=None, prepared=None, **extra):
    """Factory under test. `digest='kit'` supplies the kit's real configuration digest as the owner process argument. `prepared` = (proposal, kwargs) from `flow_kwargs`
    (so a caller can create the Control Plane stores BEFORE taking a before-snapshot)."""
    profile = kit.load(mode=mode, digest=kit.digest if digest == "kit" else digest)
    p, kw = prepared if prepared is not None else flow_kwargs(tmp)
    kw.update(extra)
    src_ = host_source if host_source is not None else Source(mat)
    flow = AP.governed_age_workflow(profile, host_source=src_, scope=scope or SCOPE, expected_mode=mode, expected_config_digest=kit.digest if digest == "kit" else digest, **kw)
    return flow, p, src_, profile


def snapshot_files(root: Path) -> dict:
    """path -> sha256 of EVERY file under root (and a marker for directories), for before/after equality on refusal."""
    out = {}
    for p in sorted(root.rglob("*")):
        rel = str(p.relative_to(root))
        out[rel] = sha256_hex(p.read_bytes()) if p.is_file() else "<dir>"
    return out


def expect_refusal(code, fn, *a, **kw):
    with pytest.raises(AP.AuthorityProfileRefusal) as exc:
        fn(*a, **kw)
    assert exc.value.code == code, (exc.value.code, exc.value.detail)
    assert exc.value.refusal.code == code
    return exc.value


# ---------------------------------------------------------------------------------------------------------------------------------------------- Replay side (P1)
REPLAY_FIXTURE = src("replay") / "tests" / "fixtures" / "registry_governed_effective_configuration" / "governed_executed"
CP_HEAD = SOURCES["control_plane"]["sha"]
REGISTRY_PIN = SOURCES["registry"]["sha"]


class VerifierSpy:
    """Delegating observation wrapper around the real Replay-side Registry adapter (RegistryEvidenceVerifierV2): records every request/verdict, changes nothing."""

    def __init__(self):
        ad = ev.Ed25519Verifier()
        self.inner = RegistryEvidenceVerifierV2(ad, ad.key_admission)
        self.requests, self.verdicts = [], []

    def verify_selection_evidence(self, request):
        self.requests.append(request)
        out = self.inner.verify_selection_evidence(request)
        self.verdicts.append(out)
        return out


def bridge_record(run: dict):
    """Replay-valid current-generation run record whose effective_configuration and selection_evidence are the REAL ones of the real decision made through the factory (verbatim).
    (Known integration gap F-1 of the F4 PoC: a raw F4 run record is not accepted by Replay's structural validator; the same labelled bridge as the PoC is used.)"""
    cp = json.loads((REPLAY_FIXTURE / "control_plane_run.json").read_text())
    proposal = json.loads((REPLAY_FIXTURE / "proposal.json").read_text())
    real = run["decisions"][0]
    tenant = real["binding"]["tenant_id"]
    cp["decisions"][0]["binding"]["tenant_id"] = tenant
    proposal["tenant_id"] = tenant
    cp["decisions"][0]["binding"]["runtime_authority"]["effective_configuration"] = copy.deepcopy(real["binding"]["runtime_authority"]["effective_configuration"])
    cp["decisions"][0]["selection_evidence"] = copy.deepcopy(real["selection_evidence"])
    return cp, proposal


def replay_trust(kwargs: dict, verifier) -> RegistryEvidenceTrust:
    """RegistryEvidenceTrust from EXACTLY the operator inputs of `replay_trust_kwargs` plus the operator's own verifier, ids, host ages and revisions."""
    kw = dict(kwargs)
    kw.pop("trust_snapshot_fingerprint")  # not a RegistryEvidenceTrust field: the pin the operator compares the marker against
    snap_id, snap_ver = kw.pop("trust_snapshot_ref")
    ctx = kw.pop("expected_context")
    return RegistryEvidenceTrust(verifier=verifier, trust_snapshot_ref=RegistryTrustSnapshotRef(snapshot_id=snap_id, version=snap_ver),
                                 expected_context=RegistryExpectedContext(**ctx), expected_action_id=ACTION_ID, expected_operation_id=OPERATION,
                                 expected_host_ages=dict(HOST_AGES), control_plane_source_revision=CP_HEAD, registry_source_revision=REGISTRY_PIN, **kw)


# ---------------------------------------------------------------------------------------------------------------------------------------------- refusal assertions
def refused_build(tmp: Path, kit: Kit, mat, code, spy, *, reached: bool, registry_code=None, **kw):
    """Factory must refuse `code`; no workflow object exists; NO file under tmp changed (config, snapshot, destination and run store byte-identical; no decision recorded);
    the Registry verifier core was (reached=True) or was NOT (reached=False) entered; on `reached=False` no Ed25519 signature check ran either."""
    prepared = flow_kwargs(tmp)       # the harness creates the (empty) Control Plane stores first; the snapshot is taken AFTER, so only the unit's effects can differ
    before = snapshot_files(tmp)
    run_before = json.loads((tmp / "run.json").read_text())
    flow = None
    with pytest.raises(AP.AuthorityProfileRefusal) as exc:
        flow = build(tmp, kit, mat, prepared=prepared, **kw)
    assert flow is None
    assert exc.value.code == code, (exc.value.code, exc.value.detail)
    assert exc.value.refusal.code == code
    if registry_code is not None:
        assert exc.value.refusal.registry_code == registry_code, exc.value.refusal
    assert snapshot_files(tmp) == before
    assert json.loads((tmp / "run.json").read_text()) == run_before and not run_before.get("decisions")
    assert spy.reached is reached, spy.n
    if not reached:
        assert spy.crypto == 0
    return exc.value


def layers_of(verdict) -> dict:
    return dict(verdict.layers)
