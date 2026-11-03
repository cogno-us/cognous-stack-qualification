"""R2 REAL-record producer for the joined chain (BUILDER_TESTED developer test code, NOT independent qualification). Ported from rw01_f4_poc/battery/real_cp_record.py to the FINAL pins.

Produces, with NO bridging, grafting, re-sealing or hand-editing, a genuine Control Plane F4 run record:
  1. a real `GovernedAgeWorkflow(..., carry_selection_evidence=True)` over the pinned Control Plane, SYNTHETIC Ed25519 keys signing the Registry selection (the real
     `Ed25519Verifier` verifies at construction/decision inside the Control Plane);
  2. `decide()` (and optionally `execute()`) persist through the Control Plane's OWN `BoundedRecordStore` (atomic replace of run.json);
  3. the record is RETRIEVED through a FRESH `BoundedRecordStore` on the same path (`reload_record`) - never reconstructed;
  4. the operator-side trust inputs a later Replay admission needs are INDEPENDENT objects (`OperatorInputs`): nothing in them is read from the record.
Negative variants re-run the real producer with a different CAUSE (variant_*). Explicit edits of signed bytes live in harness.tamper_* (deep copies).
Paths and pins follow harness.py (SRC_DIR + r2_chain/sources.json).
"""
from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

import harness as H
from harness import F4, ev, pid, vs

REGISTRY_REQUEST_CONTRACT = "registry-evidence-verification-request/0.1"   # == Replay registry_evidence.REQUEST_CONTRACT (asserted in the test file)
CTX_FIELDS = ("consumer_id", "tenant", "institution", "authority_domain", "operation")


# ------------------------------------------------------------------------------------------------------------------------------ operator-side inputs
@dataclasses.dataclass(frozen=True)
class OperatorInputs:
    """Everything the operator supplies INDEPENDENTLY of the record (trust snapshot, expected context, time/mode, floors, required family, host ages, expected ids, expected digest)."""
    trust_snapshot: Any
    snapshot_ref: tuple                  # (snapshot_id, version)
    expected_context: dict               # consumer_id, tenant, institution, authority_domain, operation
    expected_action_id: str
    expected_operation_id: str
    verification_time: Any               # datetime (tz-aware)
    time_mode: str                       # "as_of"
    min_trust_snapshot_version: int
    last_accepted_snapshot: Any          # None
    required_families: frozenset         # {"f4"}
    expected_host_ages: dict
    expected_effective_policy_digest: str   # operator-computed: sha(min(host ages, signed bound)) with Registry's own policy-identity function (independent of the record)
    control_plane_source_revision: str
    registry_source_revision: str

    def expected_effective_values(self) -> dict:
        return {k: min(self.expected_host_ages[k], H.BOUND[i]) for i, k in enumerate(("status_max_age_seconds", "approval_max_age_seconds"))}

    def with_(self, **over) -> "OperatorInputs":
        return dataclasses.replace(self, **over)

    def request_for(self, evidence: dict) -> dict:
        """The plain verification request for a carried `selection_evidence` (same shape as Replay registry_evidence.build_request; Replay's builder is not used here)."""
        t = self.trust_snapshot
        return {
            "contract": REGISTRY_REQUEST_CONTRACT, "family": evidence["family"], "registry_contract": evidence["contract_version"],
            "selection_text": evidence["selection_text"], "record_text": evidence["record_text"],
            "expected_context": dict(self.expected_context), "expected_operation_id": self.expected_operation_id, "trust_snapshot": t,
            "verification_time": self.verification_time, "verification_time_utc": self.verification_time.isoformat().replace("+00:00", "Z"),
            "min_trust_snapshot_version": self.min_trust_snapshot_version,
            "last_accepted_snapshot": None if self.last_accepted_snapshot is None else list(self.last_accepted_snapshot),
            "host_policy": {k: self.expected_host_ages[k] for k in ("status_max_age_seconds", "approval_max_age_seconds")},
        }

    def as_replay_trust(self, verifier=None):
        """The Replay-side `RegistryEvidenceTrust` object built from these inputs (only for the later Replay call; the real adapter is the default verifier)."""
        return H.make_trust(
            verifier=verifier, snapshot=self.trust_snapshot,
            trust_snapshot_ref=H.RegistryTrustSnapshotRef(snapshot_id=self.snapshot_ref[0], version=self.snapshot_ref[1]),
            expected_context=H.RegistryExpectedContext(**self.expected_context), expected_action_id=self.expected_action_id,
            expected_operation_id=self.expected_operation_id, verification_time=self.verification_time, time_mode=self.time_mode,
            min_trust_snapshot_version=self.min_trust_snapshot_version, last_accepted_snapshot=self.last_accepted_snapshot,
            expected_host_ages=dict(self.expected_host_ages), required_families=self.required_families,
            control_plane_source_revision=H.CP_SHA, registry_source_revision=H.REGISTRY_SHA)


def default_operator_inputs(*, snapshot=None, tenant=None, host_ages=None, action_id=None, operation=None, context_over=None) -> OperatorInputs:
    ages = dict(host_ages or H.HOST_AGES)
    eff = {k: min(ages[k], H.BOUND[i]) for i, k in enumerate(("status_max_age_seconds", "approval_max_age_seconds"))}
    ctx = dict(consumer_id=H.CONSUMER, tenant=tenant or H.TENANT_ID, institution=H.INSTITUTION, authority_domain=H.DOMAIN, operation=operation or H.OPERATION)
    ctx.update(context_over or {})
    snap = snapshot if snapshot is not None else H.trust()
    return OperatorInputs(
        trust_snapshot=snap, snapshot_ref=(snap.snapshot_id, snap.version), expected_context=ctx, expected_action_id=action_id or H.ACTION_ID,
        expected_operation_id=operation or H.OPERATION, verification_time=H.VERIFY_T, time_mode="as_of", min_trust_snapshot_version=1, last_accepted_snapshot=None,
        required_families=frozenset({"f4"}), expected_host_ages=ages, expected_effective_policy_digest=pid.effective_policy_digest(F4, eff),
        control_plane_source_revision=H.CP_SHA, registry_source_revision=H.REGISTRY_SHA)


# ------------------------------------------------------------------------------------------------------------------------------ the real record
@dataclasses.dataclass
class RealRecord:
    """A genuine CP-produced, persisted and retrieved F4 run record (`record` is the retrieved run.json document; nothing was edited)."""
    path: Path
    written_bytes: bytes            # run.json bytes immediately after the last Control Plane write
    retrieved_bytes: bytes          # bytes of run.json read again through a FRESH BoundedRecordStore (CP's own load path validates them)
    record: dict                    # json.loads(retrieved_bytes): the run record handed to Replay
    retrieved_model: dict           # BoundedRunRecord from the fresh store, model_dump(mode="json") (CP's own retrieval path)
    proposal: dict
    material: Any                   # harness.Material: the signed Registry selection that governed the decision
    decision_id: str
    operator: OperatorInputs
    workdir: Path = None
    flow: Any = None                # the Control Plane workflow object (selection_source call counter: flow.selection_source.calls)
    executed: bool = False
    kind: str = "REAL"

    @property
    def decision(self) -> dict:
        return self.record["decisions"][0]

    @property
    def evidence(self) -> dict:
        return self.decision["selection_evidence"]

    @property
    def destination_path(self) -> Path:
        return self.workdir / "destination.json"


def produce_real(workdir: Path | None = None, *, mat: "H.Material | None" = None, carry: bool = True, execute: bool = False, tenant: str | None = None,
                 operator: OperatorInputs | None = None) -> RealRecord:
    """Run the real Control Plane F4 workflow (decide; execute only when asked), persist through BoundedRecordStore, retrieve through a fresh BoundedRecordStore.
    `execute=False` (default for R2): the decision is authorized and retained, NO effect is applied to the bounded local destination."""
    workdir = Path(workdir) if workdir is not None else Path(tempfile.mkdtemp(prefix="r2chain-"))
    workdir.mkdir(parents=True, exist_ok=True)
    mat = mat if mat is not None else H.material()
    p = H.tenant_proposal(tenant) if tenant else H.tenant_proposal()
    flow = H.build_flow(workdir, mat, carry=carry, tenant=tenant)
    d = flow.decide(p, now=H.NOW)                       # real decide(): CP appends to run.json via BoundedRecordStore._append/_write
    assert d.result == "authorized", d.reasons
    if execute:
        flow.execute(p, flow.records.decision(d.decision_id), adapter_id=p.adapter_id, now=H.NOW)
    path = workdir / "run.json"
    written = path.read_bytes()
    out = _retrieve(path)
    return RealRecord(path, written, out["bytes"], json.loads(out["bytes"]), out["model"], json.loads(p.model_dump_json()), mat, d.decision_id,
                      operator if operator is not None else default_operator_inputs(tenant=tenant), workdir, flow, bool(execute))


def _retrieve(path: Path) -> dict:
    fresh = H.BoundedRecordStore(path, "run-1")          # CP's own retrieval path (validates the document, same lock) - a "restart": a new store object, nothing cached
    model = fresh.load().model_dump(mode="json")
    return {"bytes": path.read_bytes(), "model": model, "record": json.loads(path.read_bytes())}


def reload_record(rr: RealRecord) -> dict:
    """Simulated restart/reload: a NEW BoundedRecordStore on the persisted file; returns {bytes, model, record}. Raises the store's own refusal if the file is not a valid record."""
    return _retrieve(rr.path)


# ------------------------------------------------------------------------------------------------------------------------------ honest NEGATIVE variants (re-run the real producer with a different cause)
def variant_forged_signature(workdir=None) -> RealRecord:
    """Selection signed with the WRONG key (the trust snapshot admits only the genuine key). The Control Plane's own construction-time Registry check would refuse it, so the
    producer is given a host trust that ADMITS the wrong key (host side), while the operator's independent snapshot admits only the genuine one."""
    wrong_pub = H.OTHER_PK
    host_trust = H.trust(issuers=(vs_issuer(H.KEY_ID, wrong_pub),))
    mat = H.material(sk=H.OTHER_SK, pub=wrong_pub, host_trust=host_trust)
    return produce_real(workdir, mat=mat, operator=default_operator_inputs())       # operator snapshot: genuine key only


def vs_issuer(key_id, pub):
    return H.v.IssuerEntry(key_id, "issuer-test-1", "ed25519", pub, (H.grant(),))


def variant_wrong_context(kind: str, workdir=None) -> RealRecord:
    """Genuine record; the OPERATOR expects a different tenant / scope member / action / operation. kind in tenant|institution|domain|consumer|operation|action."""
    base = produce_real(workdir)
    if kind == "action":
        op = base.operator.with_(expected_action_id=base.operator.expected_action_id + "-other")
    elif kind == "operation":
        op = base.operator.with_(expected_operation_id="refund-issue-other", expected_context={**base.operator.expected_context, "operation": "refund-issue-other"})
    else:
        key = {"tenant": "tenant", "institution": "institution", "domain": "authority_domain", "consumer": "consumer_id"}[kind]
        op = base.operator.with_(expected_context={**base.operator.expected_context, key: base.operator.expected_context[key] + "-other"})
    return dataclasses.replace(base, operator=op)


def variant_substituted(workdir=None) -> tuple:
    """Two GENUINE records (different signed bounds). Returns (record_a, record_b); a substitution presents b's evidence where a's operator inputs / digest were expected."""
    a = produce_real(workdir)
    b = produce_real(mat=H.material(40, 30))       # genuine, different signed bound -> effective 40/30 (not 60/60)
    return a, b


def variant_mutated_effective_policy(workdir=None, host_ages=None) -> RealRecord:
    """Genuine record; the operator's independent host-age expectation (hence expected effective policy digest) differs from what the record's decision used."""
    ages = host_ages or {"status_max_age_seconds": 30, "approval_max_age_seconds": 30}
    return dataclasses.replace(produce_real(workdir), operator=default_operator_inputs(host_ages=ages))


def variant_no_carry(workdir=None) -> RealRecord:
    """Real producer with carry_selection_evidence=False: the persisted decision has no selection_evidence (missing evidence)."""
    return produce_real(workdir, carry=False)


def variant_wrong_tenant_record(workdir=None) -> RealRecord:
    """Genuine record produced for ANOTHER tenant end to end (real producer, other scope); operator inputs still expect the default tenant."""
    other = "tenant-other"
    snap = H.trust(issuers=(H.v.IssuerEntry(H.KEY_ID, "issuer-test-1", "ed25519", H.PK, (H.grant(tenant=other),)),))
    mat = H.material(stmt_over={"scope": {**H.STMT_SCOPE, "tenant": other}}, host_trust=snap)
    return produce_real(workdir, mat=mat, tenant=other, operator=default_operator_inputs())


# ------------------------------------------------------------------------------------------------------------------------------ TAMPERED copies (explicit; genuine record untouched)
def tampered_copy_selection_text(rr: RealRecord, mutate) -> dict:
    """TAMPERED: deep copy of the retrieved record with its carried selection_text changed by `mutate(str)->str`. Never use as a genuine record."""
    rec = copy.deepcopy(rr.record)
    rec["decisions"][0]["selection_evidence"]["selection_text"] = mutate(rec["decisions"][0]["selection_evidence"]["selection_text"])
    return rec


def tampered_copy_record_text(rr: RealRecord, mutate) -> dict:
    """TAMPERED: deep copy with the carried record_text changed."""
    rec = copy.deepcopy(rr.record)
    rec["decisions"][0]["selection_evidence"]["record_text"] = mutate(rec["decisions"][0]["selection_evidence"]["record_text"])
    return rec


# ------------------------------------------------------------------------------------------------------------------------------ the real adapter
def real_adapter():
    adapter = ev.Ed25519Verifier()
    return H.RegistryEvidenceVerifierV2(adapter, adapter.key_admission)


def verify_with_real_adapter(evidence: dict, operator: OperatorInputs) -> dict:
    """Send the carried evidence + operator inputs to the REAL RegistryEvidenceVerifierV2; return its verdict dict."""
    return real_adapter().verify_selection_evidence(operator.request_for(evidence))


# ------------------------------------------------------------------------------------------------------------------------------ the single Replay call
F4_SELECTOR = H.RE.REGISTRY_AUTHENTICATED_SELECTION_F4_PROFILE   # "registry-authenticated-selection-f4-governed/0.1" (Replay 6651abef, tree identical to former head ca94d6a8), imported from the pinned Replay


def import_through_replay_f4(record: dict, trust: OperatorInputs, *, proposal: dict, verifier=None, selector=F4_SELECTOR, revision=None, pass_trust: bool = True, **extra):
    """The SINGLE call into the REAL Replay `import_bounded_workflow` with the explicit F4 structural selector.

    `record` is the persisted/retrieved CP run record (deep-copied here; never edited), `proposal` the CP-produced proposal. The trust object is built ONLY from `trust`
    (operator inputs: trust snapshot, expected context/action/operation, time, host ages, floors, source revisions) via `OperatorInputs.as_replay_trust`; NOTHING from the
    record is used as trust. `verifier` defaults to a `harness.Spy` (a pure observation wrapper) around the REAL `RegistryEvidenceVerifierV2` adapter; tests read
    `trust_obj.verifier` back from the return value of `import_through_replay_f4_with_trust`. No grafting, no re-sealing, no journal inference.
    """
    return import_through_replay_f4_with_trust(record, trust, proposal=proposal, verifier=verifier, selector=selector, revision=revision, pass_trust=pass_trust, **extra)[0]


def import_through_replay_f4_with_trust(record: dict, trust: OperatorInputs, *, proposal: dict, verifier=None, selector=F4_SELECTOR, revision=None, pass_trust: bool = True, **extra):
    """Same call; returns (bundle, replay_trust_object_or_None). Raises Replay's ImportContractError unchanged on refusal."""
    trust_obj = trust.as_replay_trust(verifier=verifier if verifier is not None else H.Spy()) if pass_trust else None
    kw = dict(extra)
    if trust_obj is not None:
        kw["registry_evidence_trust"] = trust_obj
    bundle = H.I.import_bounded_workflow(copy.deepcopy(record), proposal=copy.deepcopy(proposal), control_plane_revision=revision or H.CUR_CP, control_plane_profile=selector, **kw)
    return bundle, trust_obj
