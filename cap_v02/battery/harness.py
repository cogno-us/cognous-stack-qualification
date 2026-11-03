"""Shared harness of the CAP v0.1 gate G2 qualification battery (independent test author; written from the FROZEN G2 CONTRACT, not from the implementer's tests).

Unit under test: `agent_control_plane.registry_authority_state` and the `state.backend = file-g2` path of `agent_control_plane.registry_authority_profile` at the Control Plane
G2 head (exact SHA in ../sources.json, re-pinnable through CAP_CP_SHA). Everything below the unit is REAL: the Control Plane `GovernedAgeWorkflow`, the Registry
`verify_f4_selection_v2` (all eleven layers) with the exact `Ed25519Verifier` and PyNaCl signatures, the Registry conformance kit `registry_conformance.highwater`, a REAL persisted state
FILE, and REAL separate Python processes (`child_worker.py`). Only the key material is SYNTHETIC (mechanism tests, no trust root, no custody).

This file is a COPY-and-adapt of the G1 harness idea (nothing is imported across qualification lanes).

Spies (`Spy`) wrap the Registry entry points in place and delegate unchanged; they record whether the verifier was REACHED and what it said. `WriteSpy` counts calls of the state
module's atomic writer (and delegates).
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
# the Control Plane pin is re-pinnable without editing files (a later G2 head, a later base)
if os.environ.get("CAP_CP_SHA"):
    SOURCES["control_plane"]["sha"] = os.environ["CAP_CP_SHA"]
if os.environ.get("CAP_CP_BASE_SHA"):
    SOURCES["control_plane_base"]["sha"] = os.environ["CAP_CP_BASE_SHA"]
_src_env = os.environ.get("CAP_SRC_DIR")
if not _src_env:
    raise RuntimeError("CAP_SRC_DIR must point at the directory holding the pinned checkouts (<CAP_SRC_DIR>/control_plane, registry, replay); see ../README.md")
SRC_DIR = Path(_src_env).resolve()
CHILD = HERE / "child_worker.py"
PY = sys.executable


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
from registry_conformance import highwater as kitmod  # noqa: E402  (the unchanged Registry conformance kit)
from registry_successor import common as c  # noqa: E402
from registry_successor import v2_age_bounds as f4  # noqa: E402
from registry_successor import v2_policy_identity as pid  # noqa: E402
from registry_successor import v2_verified_selection as vsel  # noqa: E402
from registry_successor import verify as v  # noqa: E402

import agent_control_plane.atomic_write as cp_atomic  # noqa: E402
import agent_control_plane.bounded as cp_bounded  # noqa: E402
import agent_control_plane.registry_f4_age_governance as cp_f4  # noqa: E402
import agent_control_plane.registry_authority_profile as AP  # noqa: E402  (UNIT UNDER TEST, profile side)
import agent_control_plane.registry_authority_state as ST  # noqa: E402  (UNIT UNDER TEST, state side)
from agent_control_plane.bounded import BoundedRecordStore, LocalRefundDestination, ObservationPolicy  # noqa: E402
from agent_control_plane.registry_f4_age_governance import GovernedScope, SelectionMaterial  # noqa: E402
from tests.test_bounded_authorization import NOW, manifest, tenant_proposal, tenant_resolver_for, TENANT  # noqa: E402  (Control Plane test builders, reused)

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
STMT_SCOPE = {"tenant": TENANT_ID, "institution": INSTITUTION, "authority_domain": DOMAIN}
EFFECTIVE = {"valid_from": "2026-10-01T00:00:00Z", "valid_until": "2026-10-06T00:00:00Z"}
EFFECTIVE_LONG = {"valid_from": "2026-10-01T00:00:00Z", "valid_until": "2026-10-20T00:00:00Z"}
ISSUED = "2026-10-01T00:00:00Z"
SELECTION_ID = "sel-test-1"
SELECTION_ID_B = "sel-test-2"
BOUND = (120, 90)
AS_OF = "2026-10-05T19:00:00Z"                                         # == NOW of the Control Plane test harness
SNAP_ID, SNAP_VERSION = "snap-cap-1", 1
SYNTH = "UNSELECTED-SYNTHETIC"
GRANT_ROW = [CONSUMER, TENANT_ID, INSTITUTION, DOMAIN, OPERATION]
NAMESPACE = "cap-qual-g2"
STATE_NAME = "freshness-state.json"
DECISION_REF = "decision-test-9"
EVIDENCE_DIR = Path(os.environ["CAP_EVIDENCE_DIR"]) if os.environ.get("CAP_EVIDENCE_DIR") else None


def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_tag(b: bytes) -> str:
    return "sha256:" + sha256_hex(b)


def evidence(name: str, obj) -> None:
    """Record a JSON evidence document under $CAP_EVIDENCE_DIR/g2-evidence/<name>.json (no-op when the variable is unset)."""
    if EVIDENCE_DIR is None:
        return
    d = EVIDENCE_DIR / "g2-evidence"
    d.mkdir(parents=True, exist_ok=True)
    (d / (name + ".json")).write_text(json.dumps(obj, sort_keys=True, indent=1, default=str) + "\n")


# ---------------------------------------------------------------------------------------------------------------------------------------------- snapshot document
def issuer_entry(key_id=KEY_ID, issuer_id=ISSUER_ID, pub=PK, grants=None):
    return {"alg": "ed25519", "authority": [list(g) for g in (grants if grants is not None else [GRANT_ROW])], "issuer_id": issuer_id, "key_id": key_id, "public_key": pub.hex()}


def snapshot_doc(**over):
    """Registry normalized snapshot document (the separate pinned trust document): public keys live HERE, never in the configuration."""
    doc = {"snapshot_id": SNAP_ID, "version": SNAP_VERSION, "valid_until": "2026-10-12T00:00:00Z", "issuers": [issuer_entry()],
           "min_epochs": [[SELECTION_ID, 1], [SELECTION_ID_B, 1]], "revoked_key_ids": [], "revoked_selections": []}
    doc.update(over)
    return doc


def fingerprint_of(doc) -> str:
    return pid.trust_snapshot_fingerprint(copy.deepcopy(doc))


def dump(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=1) + "\n").encode("utf-8")


# ---------------------------------------------------------------------------------------------------------------------------------------------- configuration
def base_config(doc=None, *, mode="synthetic", snapshot_ref="snapshot.json", backend="file-g2", namespace=NAMESPACE, state_ref=STATE_NAME, grant_row=None, profile_id="cap-profile-g2") -> dict:
    doc = doc if doc is not None else snapshot_doc()
    return {
        "version": "ocs-authority-profile/0.1", "id": profile_id, "mode": mode,
        "verifier": {"contract": "r08-v2", "family": "f4"},
        "trust_anchor": {"algorithm": "ed25519", "keys": [{"key_id": e["key_id"], "public_key_sha256": sha_tag(bytes.fromhex(e["public_key"]))} for e in doc["issuers"]]},
        "issuers": [{"issuer_id": e["issuer_id"], "key_id": e["key_id"],
                     "grants": [dict(zip(("consumer_id", "tenant", "institution", "authority_domain", "operation"), g)) for g in e["authority"]]} for e in doc["issuers"]],
        "expected_context": dict(zip(("consumer_id", "tenant", "institution", "authority_domain", "operation"), grant_row or GRANT_ROW)),
        "snapshot": {"source": {"kind": "file", "reference": snapshot_ref},
                     "expected": {"snapshot_id": doc["snapshot_id"], "version": doc["version"], "fingerprint": fingerprint_of(doc)}},
        "clock": {"kind": "fixed_instant", "as_of": AS_OF},
        "state": {"backend": backend, "namespace": namespace, "reference": state_ref, "anchor_reference": "anchor-ref-1"},
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
    boot_dir: Path

    @property
    def state_path(self) -> Path:
        return self.dir / self.config["state"]["reference"]

    @property
    def lock_path(self) -> Path:
        return Path(str(self.state_path) + ".lock")

    def rewrite_config(self, config=None, raw: bytes = None):
        data = raw if raw is not None else dump(config if config is not None else self.config)
        self.config_path.write_bytes(data)
        self.digest = sha_tag(data)
        return self.digest

    def load(self, mode="synthetic", digest="kit"):
        return AP.load_authority_profile(self.config_path, expected_mode=mode, expected_config_digest=self.digest if digest == "kit" else digest)

    def rotate(self, doc, *, edit=None):
        """Legitimate snapshot rotation: a NEW pinned snapshot document and a new snapshot.expected pin in the configuration (same anchor, issuers, grants)."""
        self.doc = doc
        self.snapshot_path.write_bytes(dump(doc))
        self.config["snapshot"]["expected"] = {"snapshot_id": doc["snapshot_id"], "version": doc["version"], "fingerprint": fingerprint_of(doc)}
        if edit:
            edit(self.config)
        return self.rewrite_config()

    def bootstrap_doc(self, **over) -> dict:
        profile = self.load()
        doc = {"schema": ST.BOOTSTRAP_SCHEMA, "bootstrap_id": "bootstrap-0001", "namespace": self.config["state"]["namespace"],
               "authority_digest": independent_authority_digest(self.config), "issued_for_mode": "synthetic",
               "issued_at": "2026-10-05T18:30:00Z", "not_after": "2026-10-05T19:30:00Z"}
        doc.update(over)
        return doc

    def write_bootstrap(self, doc=None, *, raw: bytes = None, name=None) -> Path:
        doc = doc if doc is not None else self.bootstrap_doc()
        self.boot_dir.mkdir(parents=True, exist_ok=True)
        import re as _re
        stem = name or _re.sub(r"[^A-Za-z0-9._-]", "_", str(doc.get("bootstrap_id", "x") if isinstance(doc, dict) else "x")) + ".json"
        p = self.boot_dir / stem
        p.write_bytes(raw if raw is not None else dump(doc))
        return p

    def bootstrap(self, **over) -> dict:
        """Owner-run cold start through the REAL bootstrap_state; returns the created envelope."""
        profile = self.load()
        path = self.write_bootstrap(self.bootstrap_doc(**over))
        return ST.bootstrap_state(profile, path, AP._now(profile))

    def store_bytes(self) -> bytes:
        return self.state_path.read_bytes()

    def store(self) -> dict:
        return json.loads(self.state_path.read_text())


def independent_authority_digest(config: dict) -> str:
    """The contract's authority_digest recomputed here: digest of the configuration WITHOUT snapshot.expected, snapshot.source and identities (Registry canonical digest)."""
    cfg = copy.deepcopy(config)
    cfg["snapshot"] = {}
    cfg.pop("identities", None)
    return c.digest(cfg)


def make_kit(tmp: Path, *, doc=None, config_edit=None, mode="synthetic", snapshot_name="snapshot.json", bootstrap=True, **cfg_kw) -> Kit:
    """Write <tmp>/auth/{authority.json, snapshot.json}; with bootstrap=True (default) the store is created by a REAL authorized bootstrap (generation 0, EMPTY kit state)."""
    d = tmp / "auth"
    d.mkdir(parents=True, exist_ok=True)
    doc = doc if doc is not None else snapshot_doc()
    cfg = base_config(doc, mode=mode, snapshot_ref=snapshot_name, **cfg_kw)
    if config_edit:
        config_edit(cfg)
    (d / snapshot_name).write_bytes(dump(doc))
    k = Kit(d, d / "authority.json", d / snapshot_name, doc, cfg, "", tmp / "boot")
    k.rewrite_config()
    if bootstrap:
        k.bootstrap()
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
class Sel:
    """One signed selection (record + envelope) and the statement it carries."""
    record_text: str
    selection_text: str
    stmt: dict

    @property
    def epoch(self) -> int:
        return self.stmt["epoch"]

    @property
    def digest(self) -> str:
        return c.digest(self.stmt)

    def supersedes_ref(self, decision_ref=DECISION_REF) -> dict:
        """The signed `supersedes` block a successor must carry to name THIS selection exactly (Registry requires decision_ref)."""
        return {"selection_id": self.stmt["selection_id"], "epoch": self.stmt["epoch"], "statement_digest": self.digest, "decision_ref": decision_ref}


def sel(epoch=1, *, selection_id=SELECTION_ID, prev: "Sel" = None, supersedes="auto", status=BOUND[0], approval=BOUND[1], effective=None, sk=None, key_id=KEY_ID, pub=PK,
        stmt_over=None, rec=None, decision_ref=DECISION_REF) -> Sel:
    """A signed epoch-`epoch` selection. A successor names `prev` in a signed `supersedes` (with decision_ref) unless supersedes=None / an explicit dict is passed."""
    rec = rec if rec is not None else record(status, approval)
    over = {"selection_id": selection_id, "epoch": epoch}
    if effective is not None:
        over["effective"] = dict(effective)
    if supersedes == "auto":
        over["supersedes"] = prev.supersedes_ref(decision_ref) if prev is not None else None
    else:
        over["supersedes"] = supersedes
    over.update(stmt_over or {})
    stmt = statement(rec, **over)
    return Sel(r.dumps(rec), envelope_text(stmt, sk=sk, key_id=key_id, pub=pub), stmt)


class Source:
    """The HOST's selection source (counts its own reads). `trust` is the pinned snapshot object (the wrapper requires host trust == the pin)."""

    def __init__(self, selection: Sel, trust):
        self.sel, self.trust, self.calls = selection, trust, 0

    def __call__(self):
        self.calls += 1
        return SelectionMaterial(self.sel.record_text, self.sel.selection_text, self.trust)


def pinned_trust(kit: Kit):
    return AP.load_pinned_trust(kit.load())[0]


def admit(kit: Kit, selection: Sel, *, profile=None, trust=None):
    """Direct PinnedSelectionSource call (the real wrapper, exact Ed25519Verifier). Returns (material, source)."""
    profile = profile if profile is not None else kit.load()
    host = Source(selection, trust if trust is not None else pinned_trust(kit))
    w = AP.PinnedSelectionSource(profile, host, ev.Ed25519Verifier(), expected_mode="synthetic", expected_config_digest=kit.digest)
    return w(), host


def later(profile, as_of: str):
    """The same loader-validated profile with the fixed instant moved (time passes); authority_digest is unaffected (it is computed from profile.config)."""
    return dataclasses.replace(profile, as_of=as_of)


# ---------------------------------------------------------------------------------------------------------------------------------------------- spies (delegate unchanged)
class Spy:
    """Installed by the `spy` fixture: wraps `verify_f4_selection_v2` and the exact `Ed25519Verifier._check` IN PLACE, records and delegates."""

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


class WriteSpy:
    """Counts calls of the state module's atomic writer (delegates unchanged)."""

    def __init__(self):
        self.calls = []

    @property
    def n(self) -> int:
        return len(self.calls)


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
        if bytes(message).startswith(s.V2_DOMAIN):
            sp.crypto += 1
        return real_check(self, public_key, message, signature)

    monkeypatch.setattr(vsel, "verify_f4_selection_v2", core)
    monkeypatch.setattr(ev.Ed25519Verifier, "_check", check)
    return sp


@pytest.fixture
def wspy(monkeypatch):
    ws = WriteSpy()
    real = ST.write_bytes_atomic

    def wrapped(path, data, *, overwrite=True):
        ws.calls.append((str(path), len(data), overwrite))
        return real(path, data, overwrite=overwrite)

    monkeypatch.setattr(ST, "write_bytes_atomic", wrapped)
    return ws


# ---------------------------------------------------------------------------------------------------------------------------------------------- Control Plane flow through the factory
def flow_kwargs(tmp: Path, proposal=None):
    p = proposal if proposal is not None else tenant_proposal()
    return p, dict(manifest=manifest(), destination=LocalRefundDestination(tmp / "destination.json"), records=BoundedRecordStore(tmp / "run.json", "run-1"),
                   observation_policy=ObservationPolicy(max_age_seconds=300, clock_tolerance_seconds=5), resolver=tenant_resolver_for(p))


def build(tmp: Path, kit: Kit, selection: Sel, *, digest="kit", scope=None, prepared=None, profile=None, **extra):
    """Factory under test (file-g2 profile)."""
    profile = profile if profile is not None else kit.load(digest=digest)
    p, kw = prepared if prepared is not None else flow_kwargs(tmp)
    kw.update(extra)
    host = Source(selection, pinned_trust(kit))
    flow = AP.governed_age_workflow(profile, host_source=host, scope=scope or SCOPE, expected_mode="synthetic", expected_config_digest=kit.digest if digest == "kit" else digest, **kw)
    return flow, p, host, profile


def tree(root: Path) -> dict:
    """path -> sha256 of EVERY file under root (and a marker for directories), for before/after equality."""
    out = {}
    for p in sorted(root.rglob("*")):
        rel = str(p.relative_to(root))
        out[rel] = sha256_hex(p.read_bytes()) if p.is_file() else "<dir>"
    return out


def expect_refusal(code, fn, *a, registry_code=None, **kw):
    with pytest.raises(AP.AuthorityProfileRefusal) as exc:
        fn(*a, **kw)
    assert exc.value.code == code, (exc.value.code, exc.value.detail)
    assert exc.value.refusal.code == code
    if registry_code is not None:
        assert exc.value.refusal.registry_code == registry_code, exc.value.refusal
    return exc.value


def refused_admit(kit: Kit, selection: Sel, code, spy=None, *, reached=None, registry_code=None, profile=None, trust=None, watch=None):
    """The wrapper must refuse `code` and NOT change ANY file under `watch` (default: the whole kit dir: config, snapshot, store, lock...). `reached` asserts whether the Registry core ran."""
    watch = watch if watch is not None else kit.dir
    before = tree(watch)
    err = expect_refusal(code, admit, kit, selection, registry_code=registry_code, profile=profile, trust=trust)
    after = tree(watch)
    # the lock file is a legitimate by-product of opening the lock; the STORE and everything else must be byte-identical
    drop = {kit.lock_path.name}
    assert {k: x for k, x in after.items() if k not in drop} == {k: x for k, x in before.items() if k not in drop}
    if spy is not None and reached is not None:
        assert spy.reached is reached, spy.n
        if not reached:
            assert spy.crypto == 0
    return err


# ---------------------------------------------------------------------------------------------------------------------------------------------- real child processes
def child_env() -> dict:
    env = dict(os.environ)
    env["CAP_SRC_DIR"] = str(SRC_DIR)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("PYTHONPATH", None)
    return env


def child_args(op: str, **kw) -> list:
    return [PY, "-I", str(CHILD), json.dumps(dict(op=op, **kw))]


def run_child(op: str, timeout=60, **kw) -> dict:
    """Run `child_worker.py` as a REAL separate Python process; returns {'returncode', 'out' (parsed last JSON line or None), 'stdout', 'stderr', 'pid'}."""
    p = subprocess.run(child_args(op, **kw), capture_output=True, text=True, timeout=timeout, env=child_env())
    return _result(p)


def _result(p) -> dict:
    out = None
    for line in reversed((p.stdout or "").splitlines()):
        try:
            out = json.loads(line)
            break
        except ValueError:
            continue
    return {"returncode": p.returncode, "out": out, "stdout": p.stdout, "stderr": p.stderr}


def popen_child(op: str, **kw) -> subprocess.Popen:
    return subprocess.Popen(child_args(op, **kw), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=child_env())


def child_admit(kit: Kit, selection: Sel, *, as_of=None, **kw) -> dict:
    return run_child("admit", config=str(kit.config_path), digest=kit.digest, record=selection.record_text, selection=selection.selection_text, as_of=as_of, **kw)


def child_read(kit: Kit) -> dict:
    return run_child("read", config=str(kit.config_path), digest=kit.digest)


# ---------------------------------------------------------------------------------------------------------------------------------------------- assurance labels (H1)
LABELS_DRAFT: dict = {}   # filled by test_g2_09 from the LOADED profile; conftest writes it with the final battery result


def assurance_labels(profile, *, digest_supplied: bool, battery_result: str) -> dict:
    """Machine-readable assurance labels for the lane's evidence. Derived from the loaded profile, never constants for its inputs. Refuses to label a non-synthetic profile as
    synthetic-verified. Says plainly what is NOT claimed. There is no provider concept: `derived_inputs` only reports what the loaded profile declares."""
    if profile.mode != "synthetic":
        raise ValueError("assurance labels are defined for synthetic-verified profiles only")
    return {
        "schema": "cap-assurance-labels/1", "lane": "cap-v02-g2", "label": "NON-PRODUCTION", "mode": "synthetic-verified",
        "claim": "A mechanism, synthetic keys", "authenticated_authority": False, "operational_trust": False,
        "not_claimed": ["B: Control Plane decision authenticated", "operational trust", "production adoption", "independently anchored anti-rollback (G3)"],
        "derived_inputs": {"profile_mode": profile.mode, "state_backend": profile.state_backend, "clock_kind": profile.clock_kind,
                           "snapshot_source_kind": profile.config["snapshot"]["source"]["kind"], "expected_config_digest_supplied": bool(digest_supplied)},
        "sources": {"qualification": os.environ.get("CAP_QUAL_SHA", "unset"), "control_plane": SOURCES["control_plane"]["sha"],
                    "registry": SOURCES["registry"]["sha"], "replay": SOURCES["replay"]["sha"]},
        "battery_result": battery_result,
    }

